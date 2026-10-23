"""Loop B de «sobre la aurora»: cada instrumento y cada gesto de imagen, probado por separado
en una demo corta que pasa por la rejilla de verdad, y medido.

    python aurora/demos.py           # todas
    python aurora/demos.py d06 d07   # algunas
"""
import json, math, subprocess, sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from motor import (M, E, S, N, H, T, F, SR_OUT, rng, Pista, sintetizar, leer, euclides,
                   arena, entropia, negativo, peine, ruido, afinar, dicho, f0)
import instrumentos as I

AQUI = Path(__file__).parent
R = AQUI.parent / 'render' / 'aurora-demos'; R.mkdir(parents=True, exist_ok=True)
DEMOS = AQUI / 'demos'; DEMOS.mkdir(exist_ok=True)
t16 = T / 16
q = lambda b, pos: b * T + pos * t16                # MIDI: cuadrado
LAM = I.acorde(0, True); LA = I.acorde(0, False)
MED = {}


def render(nombre, ZL, ZR, sr=None, filas=None):
    esc = sintetizar(ZL, ZR, R / f'{nombre}.wav', sr, filas)
    return leer(R / f'{nombre}.wav', esc)


def guardar(nombre, y, lufs=-16):
    crudo = R / f'{nombre}-crudo.wav'
    wavfile.write(crudo, SR_OUT, (y / (np.abs(y).max() + 1e-12) * 0.8).astype(np.float32))
    fin = R / f'{nombre}.final.wav'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(crudo), '-af',
                    f'loudnorm=I={lufs}:TP=-1.5:LRA=11,aresample={SR_OUT}', '-c:a', 'pcm_s16le', str(fin)], check=True)
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(fin), '-c:a', 'aac', '-b:a', '192k',
                    str(DEMOS / f'{nombre}.m4a')], check=True)
    print('  ', nombre, 'lista')


def groove(P, compases, acordes, kal=True):
    """Un compás tipo de la pieza: piano en golpes sincopados, fretless, MIDI E(5,16), ostinato de 7."""
    ost = [0, 7, 10, 14, 15, 14, 7]                    # grados (semitonos sobre la raíz) del ostinato de 7
    for b in range(compases):
        bajo, voces = acordes[b % len(acordes)]
        for pos, du, v in ((0, 3, .8), (3, 2, .55), (7, 4, .7), (11, 2, .5)):
            for i, n in enumerate(voces): E.piano(P, n, q(b, pos) + 0.006 * i, v, du * t16, pan=-.3 + .15 * i)
        for pos, du in ((0, 6), (6, 2), (10, 5)): E.fretless(P, bajo + (12 if pos == 6 else 0), q(b, pos), du * t16, .8)
        for pos in euclides(5, 16, 2): E.bombo(P, q(b, pos), .9)
        for pos in (4, 14): E.clap(P, q(b, pos), .8)
        for pos in euclides(9, 16): E.hat(P, q(b, pos), .45)
        if kal:
            for k in range(16):
                i = b * 16 + k
                I.kalimba(P, bajo + 24 + ost[i % 7], q(b, k), .5 + .3 * (i % 7 == 0), pan=.5)


# ─────────────────────────── demos ───────────────────────────
def d01():
    """señal: estática de radio + la telemetría de la sonda deletreando 'vida' en bits ASCII + crujidos."""
    P = Pista('d01', 3)
    I.estatica(P, [0, 1, 2], [1.0, 0.8, 0.5])
    I.telemetria(P, 0.25, 'vida')
    I.chisporroteo(P, 0, 2 * T)
    return P


def d02():
    """ostinato de 7 contra 4/4: se realinea cada 7 compases (aquí 4)."""
    P = Pista('d02', 5)
    groove(P, 4, [LAM, LA, I.acorde(9, True), I.acorde(2, False)])
    return P


def d03():
    """órgano cósmico y coro que dice la «a»: Lam9 → La maj9 (un paso P del laberinto: se mueve sólo la tercera)."""
    P = Pista('d03', 3)
    env_a = I.vocal('a')
    for b, (bajo, voces) in enumerate((LAM, LA)):
        for n in [bajo] + voces: I.organo(P, n, b * T, T * .95, .9)
        I.coro(P, [v + 12 for v in voces[:3]], b * T + .05, T * .9, .9, env_a)
    return P


def d04():
    """la narradora canta (Sabina con TD-PSOLA): «perdimos contacto con el último robot que mandamos»."""
    P = Pista('d04', 3)
    notas = [76, 72, 69, 71, 72, 74, 72, 71, 76, 74, 72, 69, 67, 69, 72, 71, 69]
    pos = [1, 3, 4, 6, 7, 8, 10, 11, 12, 14, 15, 17, 19, 20, 22, 23, 24]
    dur = [2, 1, 2, 1, 1, 2, 1, 1, 2, 1, 2, 2, 1, 2, 1, 1, 6]
    MED['d04_cantante'] = inf = I.cantar(P, 'perdimos contacto con el último robot que mandamos', notas, pos, dur, 0.0)
    for b, (bajo, voces) in enumerate((LAM, LA, LAM)):
        for k in range(0, 16, 2): I.kalimba(P, voces[k // 2 % 4] + 12, q(b, k), .35, pan=.4)
        E.fretless(P, bajo, q(b, 0), T * .9, .6)
    return P


def d05():
    """el robot (Zira) deletrea v-i-d-a-e-n-o-t-r-o en E(11,32) con saltos de Dolphy y dice «planeta»."""
    P = Pista('d05', 3)
    letras = ['uve', 'i', 'de', 'a', 'e', 'ene', 'o', 'te', 'erre', 'o', 'planeta']
    _, voces = LAM
    alturas = [voces[0] + 12, voces[3] - 12, voces[2] + 12, voces[1], voces[3] + 12, voces[0], voces[2] - 12,
               voces[3] + 12, voces[1] - 12, voces[0] + 12, voces[1]]
    pos = euclides(11, 32)
    MED['d05_robot'] = []
    for s, n, p in zip(letras, alturas, pos):
        y = afinar(s, n, 'zira', largo=(8 if s == 'planeta' else 2.2) * t16)
        P.muestra(y, q(0, p), .9, pan=(n - 64) / 20)
        MED['d05_robot'].append({'txt': s, 'nota': n, 'mide_st': round(12 * math.log2(f0(y) / M.hz(n)), 2)})
    E.fretless(P, LAM[0], 0, 2 * T, .6)
    return P


def d06():
    """arena: el mismo groove, cada compás más generaciones de JPEG (0, 2, 6, 14), calidad 85."""
    P = Pista('d06', 5); groove(P, 4, [LAM])
    ZL, ZR = P.escribir()
    gens = [0, 2, 6, 14]
    ZL2, ZR2 = arena(ZL, [0, 1, 2, 3], gens), arena(ZR, [0, 1, 2, 3], gens)
    MED['d06_arena_dB_error'] = [round(float(20 * np.log10(np.linalg.norm(ZL2[c] - ZL[c]) / np.linalg.norm(ZL[c]) + 1e-12)), 1)
                                 for c in range(4)]
    return ZL2, ZR2


def d07():
    """entropía: misma magnitud, fase cada vez más al azar (0, .35, .7, 1)."""
    P = Pista('d07', 5); groove(P, 4, [LAM])
    ZL, ZR = P.escribir()
    eps = [0, .35, .7, 1]
    return entropia(ZL, [0, 1, 2, 3], eps), entropia(ZR, [0, 1, 2, 3], eps, semilla=8)


def d08():
    """helecho: cada punto del IFS de Barnsley es una campanita en Mi♭maj9 (el acorde del callejón
    donde muere); crece 3 compases, deja de brotar y se apaga en el cuarto."""
    P = Pista('d08', 6)
    eb = [51, 55, 58, 62, 65]                              # Mi♭ Sol Si♭ Re Fa
    notas = sorted(n + 12 * o for n in eb for o in range(1, 4))
    MED['d08_eventos'] = len(I.helecho(P, 0.0, 4, notas))
    bajo, voces = I.acorde(6, False)                       # Mi♭ mayor, el callejón
    for n in [bajo] + voces: I.organo(P, n, 0, 3 * T, .45)
    return P


def d09():
    """voz en negativo: Zira dice «el tono de voz magnético»; el segundo compás es el mismo
    compás con magnitud = techo − voz (el silencio con forma de voz)."""
    P = Pista('d09', 3)
    for b in (0, 1):
        x, _ = dicho('el tono de voz magnético', 'zira')
        P.muestra(x[:int(T * .95 * S)], b * T + .05, 1.0)
    ZL, ZR = P.escribir()
    ZL2, ZR2 = negativo(ZL, [1]), negativo(ZR, [1])
    k0, k1 = int(180 / F), int(6000 / F)
    a = np.convolve(np.abs(ZL[1]), np.ones(40) / 40, 'same')[k0:k1]
    b = np.abs(ZL2[1])[k0:k1]
    MED['d09_correlacion_voz_vs_negativo'] = round(float(np.corrcoef(a, b)[0, 1]), 3)
    return ZL2, ZR2


def d10():
    """incorporar el ruido al sistema: ruido de banda que el peine de Lam9 va volviendo acorde."""
    bajo, voces = LAM
    w = peine([bajo] + voces + [v + 12 for v in voces])
    z = ruido()
    ZL = np.zeros((5, H), complex); ZR = np.zeros((5, H), complex)
    alfa = [0, .4, .8, 1, 1]
    MED['d10_energia_en_el_peine'] = []
    for c, al in enumerate(alfa):
        filtro = (1 - al) + al * w * 6
        col = z * filtro
        ZL[c] = col; ZR[c] = col * np.exp(1j * .7)
        e = np.abs(col) ** 2
        MED['d10_energia_en_el_peine'].append(round(float((e * (w > .2)).sum() / e.sum()), 3))
    ZL[4] *= np.linspace(1, 1, H) * .0; ZR[4] *= 0
    return ZL, ZR


def d11():
    """prolación: el mismo groove de 2 compases leído a la vez a 1×, 3/2× y 2× (tónica, quinta, octava)."""
    P = Pista('d11', 2); groove(P, 2, [LAM, LA], kal=False)
    ZL, ZR = P.escribir()
    return ('prolacion', ZL, ZR)


# ───────────── loop B.2: la paleta oscura (Canek: «no jazz-pop de boutique») ─────────────
LAMo = I.acorde_oscuro(0, True); LAo = I.acorde_oscuro(0, False)
OST7 = [0, 1, 7, 0, 13, 7, 6]                         # raíz, ♭2, quinta, raíz, ♭9, quinta, tritono


def groove_oscuro(P, compases, acordes, piano=True):
    for b in range(compases):
        bajo, voces = acordes[b % len(acordes)]
        if piano:
            for pos, du, v in ((0, 6, .55), (7, 5, .4)):
                for i, n in enumerate(voces): E.piano(P, n, q(b, pos) + 0.012 * i, v, du * t16, pan=-.3 + .2 * i)
        for pos, du in ((0, 7), (10, 5)): E.sub808(P, bajo, q(b, pos), du * t16, .45)
        for pos in euclides(5, 16, 2): I.subbombo(P, q(b, pos), .55)
        I.placa(P, q(b, 12), .8)
        if b % 2: I.placa(P, q(b, 6), .35, pan=-.4)
        for pos in euclides(7, 16, 1): I.polvo(P, q(b, pos), .4)
        for k in range(16):
            i = b * 16 + k
            I.preparado(P, bajo + 12 + OST7[i % 7], q(b, k), .55 + .35 * (i % 7 == 0), pan=.35)


def o02():
    """ostinato de 7, oscuro: piano preparado grave (raíz, ♭2, quinta, ♭9, tritono), sub-bombo,
    placa de metal, hats de polvo; acordes con raíz-quinta y un grano de segunda menor."""
    P = Pista('o02', 5)
    groove_oscuro(P, 4, [LAMo, LAo, I.acorde_oscuro(9, True), I.acorde_oscuro(2, False)])
    return P


def o03():
    """órgano y coro, oscuros: Lam y La (paso P) en la voicing nueva, coro de la «a» grave."""
    P = Pista('o03', 3)
    env_a = I.vocal('a')
    for b, (bajo, voces) in enumerate((LAMo, LAo)):
        for n in [bajo] + voces: I.organo(P, n, b * T, T * .95, .8)
        I.coro(P, voces[:3], b * T + .05, T * .9, .8, env_a)
    return P


VOZ_MEL = dict(notas=[64, 64, 62, 60, 60, 58, 57, 57, 64, 65, 64, 62, 60, 58, 57, 58, 57],
               pos=[1, 3, 4, 6, 7, 8, 10, 12, 16, 18, 19, 20, 22, 24, 25, 27, 28],
               dur=[2, 1, 2, 1, 1, 2, 2, 3, 2, 1, 1, 2, 2, 1, 2, 1, 8])


def o04():
    """la narradora, mejor: más grave y como canto (medios tonos, frigio), y Zira cantando la
    misma línea una octava abajo, casi en susurro: la voz magnética pegada a la humana."""
    P = Pista('o04', 4)
    txt = 'perdimos contacto con el último robot que mandamos'
    MED['o04_sabina'] = I.cantar_con(P, txt, VOZ_MEL['notas'], VOZ_MEL['pos'], VOZ_MEL['dur'], 0.0, 'sabina', g=1.0)
    MED['o04_zira'] = I.cantar_con(P, txt, VOZ_MEL['notas'], VOZ_MEL['pos'], VOZ_MEL['dur'], 0.0, 'zira', g=.32,
                                   transporte=-12)
    for b, (bajo, voces) in enumerate((LAMo, LAMo, LAo)):
        E.sub808(P, bajo, q(b, 0), T * .95, .5)
        for i, n in enumerate(voces): I.organo(P, n, q(b, 0), T * .95, .35)
    return P


def o08():
    """helecho oscuro: el mismo IFS escribiendo, ahora en vidrio frotado una octava abajo, 170
    notas, sobre Mi♭ con su ♭6 (Do♭): crece, deja de brotar y se apaga."""
    P = Pista('o08', 6)
    eb = [51, 55, 58, 59, 62]                              # Mi♭ Sol Si♭ Do♭ Re
    notas = sorted(n + 12 * o for n in eb for o in range(0, 3))
    MED['o08_eventos'] = len(I.helecho_oscuro(P, 0.0, 4, notas))
    bajo, voces = I.acorde_oscuro(6, False)
    for n in [bajo] + voces: I.organo(P, n, 0, 3 * T, .35)
    return P


def o12():
    """el tono de la canción: groove oscuro + la narradora con su voz magnética + el robot deletreando."""
    P = Pista('o12', 5)
    groove_oscuro(P, 4, [LAMo, LAo, I.acorde_oscuro(9, True), I.acorde_oscuro(2, False)])
    txt = 'perdimos contacto con el último robot que mandamos'
    I.cantar_con(P, txt, VOZ_MEL['notas'], VOZ_MEL['pos'], VOZ_MEL['dur'], 0.0, 'sabina', g=1.2)
    I.cantar_con(P, txt, VOZ_MEL['notas'], VOZ_MEL['pos'], VOZ_MEL['dur'], 0.0, 'zira', g=.38, transporte=-12)
    letras = ['uve', 'i', 'de', 'a', 'e', 'ene', 'o', 'te', 'erre', 'o', 'planeta']
    _, voces = LAMo
    alt = [voces[0] + 24, voces[3] + 12, voces[2] + 12, voces[1] + 12, voces[3] + 24, voces[0] + 12, voces[2],
           voces[3] + 24, voces[1], voces[0] + 24, voces[1] + 12]
    for s, n, p in zip(letras, alt, euclides(11, 32)):
        I.robot(P, s, n, q(2, p), (8 if s == 'planeta' else 2.2) * t16, g=.8, pan=(n - 64) / 24)
    return P


# ───────────── loop E: la pared espectral ─────────────
def e01():
    """pared espectral sola: cuatro pasos del laberinto (Lam, La, Fa#m, Re) como espectros de su
    fundamental virtual, en oleadas sincopadas (0 y 7 dieciseisavos)."""
    P = Pista('e01', 5)
    MED['e01_parciales'] = []
    for b, (r, m) in enumerate(((0, True), (0, False), (9, True), (5, False))):
        for pos, du, v in ((0, 6.5, 1.0), (7, 8.5, .7)):
            MED['e01_parciales'].append(I.pared_espectral(P, r, m, q(b, pos), du * t16, v, semilla=b * 10 + pos))
    return P


def e02():
    """la misma pared con la banda oscura (sin piano), y en los últimos dos compases la serie se
    estira (0.004, 0.009): la pared se vuelve metálica, inarmónica."""
    P = Pista('e02', 5)
    pasos = ((0, True), (0, False), (9, True), (5, False))
    for b, (r, m) in enumerate(pasos):
        ac = I.acorde_oscuro(r, m)
        groove_oscuro(P, 1, [ac], piano=False) if False else None
        bajo, voces = ac
        for pos, du in ((0, 7), (10, 5)): E.sub808(P, bajo, q(b, pos), du * t16, .45)
        for pos in euclides(5, 16, 2): I.subbombo(P, q(b, pos), .55)
        I.placa(P, q(b, 12), .8)
        for pos in euclides(7, 16, 1): I.polvo(P, q(b, pos), .4)
        for k in range(16):
            i = b * 16 + k
            I.preparado(P, bajo + 12 + OST7[i % 7], q(b, k), .55 + .35 * (i % 7 == 0), pan=.35)
        est = [0, 0, .004, .009][b]
        for pos, du, v in ((0, 6.5, 1.0), (7, 8.5, .7)):
            I.pared_espectral(P, r, m, q(b, pos), du * t16, v * 1.3, estira=est, semilla=b * 10 + pos)
    return P


TODAS = ['d01', 'd02', 'd03', 'd04', 'd05', 'd06', 'd07', 'd08', 'd09', 'd10', 'd11']
OSCURAS = ['o02', 'o03', 'o04', 'o08', 'o12']
ESPECTRAL = ['e01', 'e02']
TITULO = {k: ' '.join(globals()[k].__doc__.split()) for k in TODAS + OSCURAS + ESPECTRAL}


def correr(nombre):
    res = globals()[nombre]()
    if isinstance(res, Pista):
        ZL, ZR = res.escribir(); y = render(nombre, ZL, ZR)
    elif isinstance(res[0], str) and res[0] == 'prolacion':
        _, ZL, ZR = res
        largo = int(round(2 * T * SR_OUT))
        capas = []
        for k, (sr, pan) in enumerate(((S, 0), (S * 3 // 2, -.6), (2 * S, .6))):
            z = render(f'{nombre}-{k}', ZL, ZR, sr=sr)
            z = np.concatenate([z] * 3)[:largo]
            gL, gR = M.paneo(pan)
            capas.append(np.stack([z[:, 0] * gL * 1.4, z[:, 1] * gR * 1.4], 1) if k else z)
        y = sum(capas)
        # medir: el pico del espectro de cada lectura (la quinta y la octava son exactas: 3/2 y 2)
        picos = []
        for k in range(3):
            z = leer(R / f'{nombre}-{k}.wav'); Z = np.abs(np.fft.rfft(z[:, 0])); fr = np.fft.rfftfreq(len(z), 1 / SR_OUT)
            m = (fr > 60) & (fr < 400); picos.append(float(fr[m][np.argmax(Z[m])]))
        MED['d11_picos_Hz'] = [round(p, 2) for p in picos]
        MED['d11_razones'] = [round(p / picos[0], 4) for p in picos]
    else:
        ZL, ZR = res; y = render(nombre, ZL, ZR)
    if nombre == 'd07':   # medir: el espectro largo no cambia, el factor de cresta sí (las notas se vuelven ruido)
        cr = []
        for b in range(4):
            s = y[int(b * T * SR_OUT):int((b + 1) * T * SR_OUT), 0]
            cr.append(round(float(np.abs(s).max() / s.std()), 2))
        MED['d07_factor_de_cresta'] = cr
    guardar(nombre, y)


if __name__ == '__main__':
    pedidas = sys.argv[1:] or TODAS
    for n in pedidas:
        correr(n)
        viejo = json.load(open(DEMOS / 'medidas.json', encoding='utf-8')) if (DEMOS / 'medidas.json').exists() else {}
        viejo.update(MED)
        json.dump(viejo, open(DEMOS / 'medidas.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=str)
    print(json.dumps(MED, ensure_ascii=False, default=str)[:3000])
