"""Loop B de «la máquina del tiempo»: los instrumentos con su textura, cada uno por la rejilla y medido.
Donde sirve, la demo pone primero el sonido CRUDO (como entraban en las piezas anteriores) y después
el mismo con sus seis capas (TEXTURAS.md).

    python maquina/demos.py            # todas
    python maquina/demos.py t02 t07    # algunas
Los WAV quedan en render/maquina-demos/ (borradores de trabajo); las entregas las arma proceso_texturas.py.
"""
import json, math, subprocess, sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfiltfilt
import nave as V

AQUI = Path(__file__).parent
R = AQUI.parent / 'render' / 'maquina-demos'; R.mkdir(parents=True, exist_ok=True)
MEDIDAS = R / 'medidas.json'
MED = json.load(open(MEDIDAS, encoding='utf-8')) if MEDIDAS.exists() else {}
T, S, SR = V.T, V.S, V.SR_OUT
L = lambda c: int(round(c * T * SR))
LISTA = []


def demo(f):
    LISTA.append(f.__name__); return f


# ───────────── utilidades ─────────────
def sint(nombre, ZL, ZR):
    wav = R / f'{nombre}.wav'
    esc = V.PM.sintetizar(ZL, ZR, wav, sr=S)
    return V.PM.leer(wav, esc)


def zp(P):
    return P.escribir()


class PistaD(V.Pista):
    """Una pista que puede escribirse corrida medio compás (off = T/2): para la versión sin raya."""
    def __init__(self, nombre, C, off=0.0):
        super().__init__(nombre, C + (1 if off else 0)); self.off = off

    def muestra(self, w, t0, g=1.0, pan=0.0):
        super().muestra(w, t0 - self.off, g, pan)


def pista(nombre, C, off=0.0):
    return PistaD(nombre, C, off)


SIGNO = (-1.0) ** np.arange(V.H)


def portadora_off(C, plan, off):
    """La portadora corrida medio compás: la columna j cubre [j+½, j+1½) con el plan de j;
    correr T/2 una fila con k ciclos por columna es multiplicarla por (-1)^k."""
    ZL, ZR = V.portadora(C, plan)
    return (ZL * SIGNO, ZR * SIGNO) if off else (ZL, ZR)


def liso(nombre, hacer, C, borde=.035):
    """Sin clics en la raya: hacer(off) → (ZL, ZR). Se sintetiza a off=0 y a off=T/2; cerca de cada
    raya (±borde s, coseno) se usa la versión corrida, que ahí no tiene raya."""
    a = sint(nombre + '-a', *hacer(0.0))
    b = sint(nombre + '-b', *hacer(T / 2))
    n = L(C); a = largo(a, n)
    b = largo(np.concatenate([np.zeros((L(.5), 2)), b]), n)
    t = np.arange(n) / SR; d = np.abs(t - np.round(t / T) * T)
    w = np.where(d < borde, .5 + .5 * np.cos(np.pi * d / borde), 0); w[t < T / 2] = 0
    return a * (1 - w[:, None]) + b * w[:, None]


def meter(P, y, t0, g=1.0, pan=0.0):
    """Mono o estéreo (2, n) a S dentro de la pista."""
    if np.ndim(y) == 2:
        P.muestra(y[0], t0, g, -1); P.muestra(y[1], t0, g, 1)
    else:
        P.muestra(y, t0, g, pan)


def largo(x, n):
    return x[:n] if len(x) >= n else np.concatenate([x, np.zeros((n - len(x), 2))])


def mezclar(stems, n, cola=2.6, afinado=.6, semilla=0):
    """stems: [(estéreo 48k, plano, ganancia)] → seco + sala afinada (la sala recibe los envíos)."""
    seco = np.zeros((n, 2)); envio = np.zeros((n, 2))
    for x, plano, g in stems:
        x = largo(x, n); m = np.abs(x).max(1); viva = m > m.max() * 1e-3
        x = x / (np.sqrt((x[viva] ** 2).mean()) + 1e-12) * .1          # cada stem a RMS 0.1: la ganancia es nivel real
        s, e = V.en_plano(x * g, plano, semilla=semilla)
        seco += s; envio += e
    return seco + .55 * V.sala_afinada(envio, cola, afinado, semilla)


def guardar(nombre, y, titulo, lufs=-16):
    crudo = R / f'{nombre}-mezcla.wav'
    wavfile.write(crudo, SR, (y / (np.abs(y).max() + 1e-12) * .8).astype(np.float32))
    fin = R / f'{nombre}.final.wav'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(crudo), '-af',
                    f'loudnorm=I={lufs}:TP=-1.5:LRA=11,aresample={SR}', '-c:a', 'pcm_s16le', str(fin)], check=True)
    MED.setdefault(nombre, {})['titulo'] = titulo
    json.dump(MED, open(MEDIDAS, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('  ', nombre, 'lista', flush=True)


def respira(b, per, fase, lo, hi):
    return lo + (hi - lo) * (.5 + .5 * math.sin(2 * math.pi * b / per + fase))


def plan_profundo(b0=0, enfoque=(.62, 1.0)):
    """El groove profundo: patrón B, el enfoque respira por banda (cada banda con su retraso: Crisis),
    swing que respira, halo de Scelsi, timbre que gira."""
    lo, hi = enfoque
    def plan(b):
        bb = b + b0
        return {'groove': 1, 'mezcla': 1,
                'coher': {'bajo': respira(bb, 5, 0, lo + .15, hi), 'medio': respira(bb, 7, 2, lo, hi),
                          'alto': respira(bb, 3, 4, lo - .1, hi)},
                'swing': round(respira(bb, 8, 1, .06, .14), 2), 'halo': .6, 'timbre': .7}
    return plan


def bajo_entre(compases, b0=0, desde_c=0):
    """El bajo elástico toca ENTRE los golpes del bajo de la portadora (patrón B: 0 2 5 8 9 12 15)."""
    fr = [(3, 45, 42, .05, .75), (6, 40, None, 0, .6), (7, 42.69, 40, .04, .7), (10, 33, 36, .09, .9),
          (13, 45, 40, .03, .6), (14, 43, None, 0, .5)]
    notas = []
    for b in range(desde_c, compases):
        for pos, midi, desde, glis, vel in fr:
            if b % 2 and pos == 10: midi, desde = 31.69, 33          # cada dos compases, el Sol 7/4 grave
            notas.append((V.q(b + b0, pos), T / 16 * (1.6 if pos in (7, 10) else 1.1), midi, desde, glis, vel))
    return notas


def bandas_medidas(x, inicio_c, fin_c):
    m = x.mean(1)[L(inicio_c):L(fin_c)]
    out = {}
    for n_, lo, hi in (('sub', 20, 80), ('bajo', 80, 250), ('medio', 250, 2000), ('pres', 2000, 6000), ('aire', 6000, 20000)):
        sos = butter(4, [lo, hi], 'bandpass', fs=SR, output='sos') if hi < SR / 2 else butter(4, lo, 'highpass', fs=SR, output='sos')
        out[n_] = round(20 * math.log10(sosfiltfilt(sos, m).std() / (m.std() + 1e-12) + 1e-12), 1)
    return out


def clics(x, compases):
    """¿Hay clic en la raya del compás? Energía arriba de 9 kHz en ±3 ms de cada raya contra la mediana."""
    m = x.mean(1); h = sosfiltfilt(butter(4, 9000, 'highpass', fs=SR, output='sos'), m) ** 2
    w = int(.003 * SR); base = (m ** 2).mean() + 1e-15            # contra la energía de toda la señal
    picos = [h[max(0, L(c) - w):L(c) + w].mean() / base for c in range(1, compases)]
    return round(10 * math.log10(max(picos) + 1e-12), 1)


def fraccion_la(x, t0, t1):
    """Qué fracción de la energía (150-4000 Hz) cae a ±4 Hz de un parcial de La: 1 = es portadora."""
    m = x.mean(1)[int(t0 * SR):int(t1 * SR)]
    X = np.abs(np.fft.rfft(m * np.hanning(len(m)))) ** 2; f = np.fft.rfftfreq(len(m), 1 / SR)
    sel = (f > 150) & (f < 4000); d = np.abs(f - np.round(f / V.LA) * V.LA)
    return round(float(X[sel & (d < 4)].sum() / (X[sel].sum() + 1e-12)), 3)


def clics_raya(x, compases):
    """Clic en la raya: energía arriba de 9 kHz en ±3 ms de cada raya contra la MEDIANA de esa misma
    energía en todo el audio (lo que sobresale). Se reporta el peor."""
    h = sosfiltfilt(butter(4, 9000, 'highpass', fs=SR, output='sos'), x.mean(1)) ** 2
    w = int(.003 * SR); e = np.convolve(h, np.ones(2 * w) / (2 * w), 'same'); base = np.median(e) + 1e-20
    return round(10 * math.log10(max(e[L(c)] for c in range(1, compases)) / base), 1)


def cama_(nombre, C, pl):
    return liso(nombre, lambda off: portadora_off(C, pl, off), C)


def centroide(x, c0, c1):
    m = x.mean(1)[L(c0):L(c1)]; X = np.abs(np.fft.rfft(m)); f = np.fft.rfftfreq(len(m), 1 / SR)
    return int((X * f).sum() / (X.sum() + 1e-12))


def modulacion(x, c0, c1):
    """Energía de la envolvente entre 2 y 8 Hz (ritmo silábico): sube cuando el ruido se vuelve voz."""
    m = x.mean(1)[L(c0):L(c1)]
    e = np.abs(sosfiltfilt(butter(2, [300, 3500], 'bandpass', fs=SR, output='sos'), m))
    e = sosfiltfilt(butter(2, 30, 'lowpass', fs=SR, output='sos'), e)[::100]
    E = np.abs(np.fft.rfft(e - e.mean())) ** 2; f = np.fft.rfftfreq(len(e), 100 / SR)
    return round(float(E[(f > 2) & (f < 8)].sum() / (E[(f > .3)].sum() + 1e-12)), 3)


def planitud(x, c0, c1):
    """Planitud espectral 300-4000 Hz (media geométrica / aritmética): 1 = ruido, cerca de 0 = tono."""
    m = x.mean(1)[L(c0):L(c1)]
    X = np.abs(np.fft.rfft(m * np.hanning(len(m)))) ** 2 + 1e-20; f = np.fft.rfftfreq(len(m), 1 / SR)
    X = X[(f > 300) & (f < 4000)]
    return round(float(np.exp(np.log(X).mean()) / X.mean()), 3)


# ───────────── las demos ─────────────
@demo
def t01():
    """El groove profundo: la nota sola (2 compases) y luego patrón B con el enfoque respirando por banda,
    swing por fase, sub en La0, halo de Scelsi, la chispa (ruido afinado) y el bajo elástico entre los golpes."""
    C = 10
    plan = plan_profundo()
    pl = lambda b: {'groove': 0, 'halo': .6, 'timbre': .7} if b < 2 else {**plan(b), 'groove': float(V.suave((b - 1.5) / 1.5))}
    por = cama_('t01-portadora', C, pl)
    P = pista('bajo', C); meter(P, V.bajo_elastico(bajo_entre(C, desde_c=4), C * T), 0, .55)
    bajo = sint('t01-bajo', *zp(P))
    Pc = pista('chispa', C); meter(Pc, V.chispa(C, lambda b: pl(b) if b >= 2 else {'groove': 0}), 0)
    ch = sint('t01-chispa', *zp(Pc))
    n = L(C)
    y = mezclar([(por, 'medio', 1.0), (bajo, 'cerca', .9), (ch, 'medio', .4)], n, cola=2.2, afinado=.7)
    sin_arreglo = sint('t01-portadora-a', *V.portadora(C, pl))
    MED['t01'] = {'bandas_groove': bandas_medidas(y, 5, 10),
                  'clic_raya_sobre_mediana_dB': {'antes (una sola versión)': clics_raya(sin_arreglo, C),
                                                 'liso (versión corrida en la raya)': clics_raya(por, C)}}
    guardar('t01', y, 'groove profundo: patrón B, enfoque que respira, swing por fase, sub, halo, chispa, bajo elástico')


FRASE_NAVE = 'aquí la nave. todos los sistemas responden.'


@demo
def t02():
    """La voz de la nave: CRUDA (como en las piezas anteriores: la cantante seca encima) y luego con
    textura (aire encasillado, doble hecho de portadora, plano medio, sala afinada, eco envejecido)."""
    C = 9
    cama = cama_('t02-cama', C, lambda b: {**plan_profundo(enfoque=(.5, .85))(b), 'groove': .55})
    P = pista('voz-cruda', C); V.cantar_nave(P, FRASE_NAVE, V.q(0), 3, semilla=11)
    cruda = sint('t02-cruda', *zp(P))
    Pv = pista('voz', C); V.cantar_nave(Pv, FRASE_NAVE, V.q(4, 2), 3, semilla=11)
    voz = sint('t02-voz', *zp(Pv))
    v_s = V.PM.a_sr(voz.mean(1), SR, S)
    Pa = pista('aire', C); meter(Pa, V.aire(v_s, .5, 3) - v_s, 0)
    Pc = pista('doble', C); meter(Pc, V.voz_portadora(v_s, semilla=4), 0)
    aire_ = sint('t02-aire', *zp(Pa)); doble = sint('t02-doble', *zp(Pc))

    def eco_(off):                                                     # su eco: una negra, una vez por el medio
        Pe = pista('eco', C, off); meter(Pe, v_s, T / 4); ZL, ZR = zp(Pe)
        return V.envejecer(ZL, 1, 5), V.envejecer(ZR, 1, 6)
    eco = liso('t02-eco', eco_, C)
    n = L(C)
    seca = largo(cruda, n) * (np.arange(n) < L(4))[:, None]
    y = mezclar([(cama, 'medio', .55), (voz, 'medio', 1.0), (aire_, 'medio', .22), (doble, 'medio', .5),
                 (eco, 'lejos', .45)], n, cola=2.4, afinado=.65)
    y = y + seca / (np.sqrt((seca[seca != 0] ** 2).mean()) + 1e-12) * .1
    MED['t02'] = {'aire_6k_cruda_vs_textura_dB': [bandas_medidas(y, 0, 3.5)['aire'], bandas_medidas(y, 4.5, 8)['aire']],
                  'fraccion_en_La_cruda_vs_textura': [fraccion_la(y, .1, 3.5 * T), fraccion_la(y, 4.5 * T, 8 * T)]}
    guardar('t02', y, 'la voz de la nave: cruda (compases 1-4) y con textura (5-9)')


RESP = 'los escuchamos, nave. no te apagues.'


@demo
def t03():
    """La Tierra: CRUDA (una Zira seca), luego el coro en el cuarto de control (cerca) y luego la misma
    respuesta cuando llega tarde: lejos y envejecida tres veces (como volverá en IV)."""
    C = 9
    cama = cama_('t03-cama', C, lambda b: {'groove': .3, 'halo': .7, 'timbre': .6, 'mezcla': 1,
                                           'coher': {'bajo': .6, 'medio': .4, 'alto': .3}})
    P = pista('cruda', C); meter(P, V.palabra(RESP, 0, 'zira'), V.q(0, 4)); cruda = sint('t03-cruda', *zp(P))
    Pc = pista('coro', C); meter(Pc, V.tierra(RESP, 2), V.q(3, 4)); coro = sint('t03-coro', *zp(Pc))

    def vieja_(off):
        Pv = pista('vieja', C, off); meter(Pv, V.tierra(RESP, 2), V.q(6, 2)); ZL, ZR = zp(Pv)
        return V.envejecer(ZL, 3, 7), V.envejecer(ZR, 3, 8)
    vieja = liso('t03-vieja', vieja_, C)
    n = L(C)
    cr = largo(cruda, n)
    y = mezclar([(cama, 'medio', .5), (coro, 'cerca', 1.0), (vieja, 'lejos', 1.6)], n, cola=1.6, afinado=.5)
    y = y + cr / (np.sqrt((cr[cr != 0] ** 2).mean()) + 1e-12) * .1
    MED['t03'] = {'centroide_Hz_coro_vs_vieja': [centroide(y, 3.2, 5.5), centroide(y, 6.2, 8.8)]}
    guardar('t03', y, 'la Tierra: Zira cruda, el coro en el cuarto de control, y la misma respuesta llegando tarde')


@demo
def t04():
    """El estribillo y su eco que envejece: «que estoy aquí» tres veces; cada una vuelve un compás tarde,
    pasada una vez más por el medio. El groove pierde enfoque."""
    C = 10
    cama = cama_('t04-cama', C, lambda b: plan_profundo(enfoque=(.35 - .03 * b, .95 - .05 * b))(b))
    voces, ecos = [], []
    for i in range(3):
        P = pista(f'v{i}', C); V.cantar_nave(P, 'que estoy aquí,', V.q(1 + 2 * i), 1.6, semilla=40 + i, desde=62 - 2 * i)
        voces.append(sint(f't04-v{i}', *zp(P)))
        w = V.PM.a_sr(voces[-1].mean(1), SR, S)
        for k in range(1, 4 - i if i < 2 else 3):
            def eco_(off, w=w, k=k, i=i):
                Pe = pista('e', C, off); meter(Pe, w, k * T); ZL, ZR = zp(Pe)
                return V.envejecer(ZL, k + i, 10 * i + k), V.envejecer(ZR, k + i, 10 * i + k + 50)
            ecos.append((liso(f't04-e{i}{k}', eco_, C), k + i))
    n = L(C)
    st = [(cama, 'medio', .6)] + [(v, 'medio', 1.0) for v in voces] + [(e, 'lejos', .75 / (1 + .25 * g)) for e, g in ecos]
    y = mezclar(st, n, cola=3.0, afinado=.7)
    MED['t04'] = {'centroide_Hz_por_edad_del_eco': {f'eco {j} (edad {g})': centroide(e, 0, C) for j, (e, g) in enumerate(ecos)}}
    guardar('t04', y, 'el estribillo «que estoy aquí» y su eco que envejece')


TELE = ['transmisión', 'cero', 'cero', 'cuatro', 'distancia', 'cinco', 'unidades', 'astronómicas',
        'retraso', 'de la señal', 'cuarenta', 'y un', 'minutos']


@demo
def t05():
    """La telemetría: cada palabra en un golpe del patrón del bajo, por teléfono y con un códec leve; la
    segunda vez más degradada (se caen palabras y pasa dos veces por el medio)."""
    C = 8
    cama = cama_('t05-cama', C, plan_profundo())
    golpes = [0, 2, 5, 8, 9, 12, 15]
    slots = [(b, p) for b in range(4) for p in golpes]

    def tele(off, segunda):
        P = pista('t', C, off); rng = np.random.default_rng(3)
        for i, w in enumerate(TELE):
            b, p = slots[i * 2]; cae = rng.random() <= .3
            if not segunda: meter(P, V.palabra(w, 5), V.q(b, p), 1.0, (-.3 if i % 2 else .3))
            elif not cae: meter(P, V.palabra(w, 5), V.q(b + 4, p), 1.0, (-.3 if i % 2 else .3))
        Z = zp(P); g = 2 if segunda else 1
        return V.telefono(V.envejecer(Z[0], g, 1 + 2 * g), 1), V.telefono(V.envejecer(Z[1], g, 2 + 2 * g), 1)
    t1 = liso('t05-t1', lambda off: tele(off, False), C); t2 = liso('t05-t2', lambda off: tele(off, True), C)
    n = L(C)
    y = mezclar([(cama, 'medio', .7), (t1, 'telefono', 1.0), (t2, 'telefono', 1.0)], n, cola=1.8, afinado=.6)
    MED['t05'] = {'centroide_Hz_1a_vs_2a': [centroide(y, 0, 4), centroide(y, 4, 8)]}
    guardar('t05', y, 'la telemetría como instrumento rítmico, por teléfono; la segunda vez más gastada')


@demo
def t06():
    """El morse que olvidó lo que quería decir: los parciales 16, 19 y 24 de la portadora en morse
    («tierra regreso ustedes»); el código se olvida hasta ser ritmo y fundirse con el brillo."""
    C = 8
    cama = cama_('t06-cama', C, lambda b: {**plan_profundo()(b), 'groove': .6 + .05 * b})
    m = V.morse('tierra regreso ustedes', lambda u: float(V.suave((u - .2) / .7)), semilla=6)
    P = pista('morse', C); meter(P, m, V.q(0, 4), 1.0, .5)
    mo = sint('t06-morse', *zp(P))
    n = L(C)
    y = mezclar([(cama, 'medio', .8), (mo, 'lejos', .9)], n, cola=2.8, afinado=.8)
    MED['t06'] = {'fraccion_en_La': fraccion_la(y, 0, C * T)}
    guardar('t06', y, 'el morse que olvidó lo que quería decir (hecho de la portadora)')


@demo
def t07():
    """La frontera: «creo que aquí empieza a terminarse mi idioma». La voz se vuelve portadora (el
    vocoder de parciales de La toma su lugar), el groove pierde el tiempo y «regreso» se congela."""
    C = 10
    plan = plan_profundo()
    cama = cama_('t07-cama', C, lambda b: {**plan(b), 'coher': {k: max(.05, v * (1 - b / 9)) for k, v in plan(b)['coher'].items()}})

    def v_(off):
        P = pista('v', C, off)
        V.cantar_nave(P, 'digo regreso', V.q(0, 2), 1.5, semilla=21)
        V.cantar_nave(P, 'creo que aquí empieza a terminarse mi idioma.', V.q(4), 4.5, semilla=22, desde=60)
        Z = zp(P); c = 0 if off else 1                 # «regreso» cae en el compás 2: columna 1, o 0 si va corrida
        return V.congelar(Z[0], c, c + 3, .75, 1), V.congelar(Z[1], c, c + 3, .75, 2)
    v = liso('t07-v', v_, C)
    vs = V.PM.a_sr(v.mean(1), SR, S)
    u = V.suave(np.clip((np.arange(len(vs)) / S - 4.5 * T) / (4.5 * T), 0, 1))
    Pv, Pc = pista('voz', C), pista('por', C)
    meter(Pv, V.aire(vs, .3, 2) * (1 - u), 0); meter(Pc, V.voz_portadora(vs, semilla=9) * (.35 + .9 * u), 0)
    voz = sint('t07-voz', *zp(Pv)); por = sint('t07-por', *zp(Pc))
    n = L(C)
    y = mezclar([(cama, 'medio', .7), (voz, 'medio', 1.0), (por, 'medio', .9)], n, cola=3.2, afinado=.75)
    rel = lambda a, b: round(20 * math.log10(largo(por, n)[L(a):L(b)].std() * .9 / (largo(voz, n)[L(a):L(b)].std() + 1e-12)), 1)
    MED['t07'] = {'portadora_sobre_voz_dB_inicio_vs_final': [rel(4, 5.5), rel(7.5, 9)]}
    guardar('t07', y, 'la frontera: la voz se vuelve portadora; «regreso» queda flotando')


@demo
def t08():
    """El vacío funky y lo que vuelve: dos compases sin tiempo, un compás de nada absoluta, la Tierra
    desde lejos y el groove que regresa por el teléfono y se enfoca (el gesto de los últimos 7 s)."""
    C = 9

    def plan(b):
        if b == 2: return {'mute': True}
        if b < 2: return {**plan_profundo()(b), 'coher': {'bajo': .15, 'medio': .1, 'alto': .05}, 'mezcla': 0}
        e = float(V.suave((b - 4) / 3.5))
        return {**plan_profundo()(b), 'coher': {k: .3 + .7 * e * (.9 if k == 'alto' else 1) for k in ('bajo', 'medio', 'alto')}}
    tel = np.array([0, 0, 0, 1, 1, .8, .45, .15, 0, 0])

    def cama_off(off):
        ZL, ZR = portadora_off(C, plan, off)
        tt = tel[:C] if not off else ((tel[:-1] + tel[1:]) / 2)[:C]
        return V.telefono(ZL, tt), V.telefono(ZR, tt)
    cama = liso('t08-cama', cama_off, C)

    def ti_(off):
        P = pista('tierra', C, off); meter(P, V.tierra('háblanos aunque se te acabe. inventa. te vamos a entender igual.', 5), V.q(3, 1))
        Zt = zp(P); return V.envejecer(Zt[0], 2, 3), V.envejecer(Zt[1], 2, 4)
    ti = liso('t08-tierra', ti_, C)
    n = L(C)
    y = mezclar([(cama, 'medio', 1.0), (ti, 'lejos', 1.4)], n, cola=2.6, afinado=.7)
    y[L(2):L(3)] = 0                                                   # nada: tampoco la cola de la sala
    MED['t08'] = {'centroide_Hz_regreso_vs_enfocado': [centroide(y, 3, 4.5), centroide(y, 7, 9)]}
    guardar('t08', y, 'el vacío funky: un compás de nada, y lo que vuelve por el teléfono')


GLIFOS = ['▓▓▓▓  ▓▓  ▓▓▓▓▓▓▓ ', '▓▓  ▓▓▓▓▓▓  ▓▓  ', '▓▓▓▓▓▓▓▓▓▓  ▓   ', '▓▓▓▓  ▓▓▓▓▓▓    ',
          '▓▓▓▓▓▓▓▓▓▓▓▓    ', '▓▓  ▓▓▓▓  ▓▓▓▓▓▓']


@demo
def t09():
    """El ruido afinado: los renglones ▓ del poema como ritmo (cada ▓ un dieciseisavo); los dientes del
    peine se abren renglón a renglón (de casi-nota a soplo) y de adentro salen «ruido», «y», «entropía»."""
    C = 7
    cama = cama_('t09-cama', C, lambda b: {**plan_profundo(enfoque=(.3, .7))(b), 'groove': .5})
    P = pista('ruido', C)
    for r, renglon in enumerate(GLIFOS):
        nz = V.ruido_afinado(int(T * S), 2.5 * 1.6 ** r, 100 + r)
        env = np.zeros(int(T * S)); k = int(.003 * S)
        for i, ch in enumerate(renglon[:16]):
            if ch == '▓':
                a = int(i * T / 16 * S); z = int((i + 1) * T / 16 * S)
                e = np.ones(z - a); e[:k] = np.linspace(0, 1, k); e[-k:] = np.linspace(1, 0, k)
                env[a:z] = e * (1 if (i == 0 or renglon[i - 1] != '▓') else .78)
        meter(P, nz * env, V.q(r), .9, (-.5 if r % 2 else .5))
    ru = sint('t09-ruido', *zp(P))
    anchos = [40, 120, 25, 120, 12, 80, 4, 4]

    def pal_(off):
        Pw = pista('palabras', C, off)
        for w, b in (('ruido', 1), ('y', 3), ('entropía', 5)): meter(Pw, V.palabra(w, -2), V.q(b, 6))
        Zw = zp(Pw); a = anchos if not off else [(x + y_) / 2 for x, y_ in zip(anchos, anchos[1:])]
        return V.desenfocar(Zw[0], a, 1), V.desenfocar(Zw[1], a, 2)
    pal = liso('t09-palabras', pal_, C)
    n = L(C)
    y = mezclar([(cama, 'medio', .6), (ru, 'medio', .55), (pal, 'medio', 1.0)], n, cola=2.6, afinado=.8)
    MED['t09'] = {'fraccion_en_La_renglon1_vs_6': [fraccion_la(ru, 0, T), fraccion_la(ru, 5 * T, 6 * T)]}
    guardar('t09', y, 'el ruido afinado: los renglones ▓ como ritmo, de casi-nota a soplo')


@demo
def t10():
    """El epílogo: la portadora sola con su latido y el ⌖ (parciales 23, 29, 31); la Tierra cerca e
    íntima; y la nave que sale del ruido sin tiempo hasta llegar limpia en «aquí»."""
    C = 10

    def plan(b):
        p = {'groove': 0, 'halo': .5, 'timbre': .4, 'latido': 1.0}
        if b in (1, 2): p['extra'] = {23: .05 * (1 if b == 1 else .5), 29: .04, 31: .035}
        return p
    cama = cama_('t10-cama', C, plan)
    P = pista('tierra', C); meter(P, V.tierra('el ruido que ahora nos llega de allá resulta que era, todo este tiempo, alguien', 9), V.q(1))
    ti = sint('t10-tierra', *zp(P))
    coh = np.array([0, 0, 0, 0, 0, .05, .3, .7, 1, 1, 1.]); anchos = np.array([0, 0, 0, 0, 0, 150, 60, 15, 0, 0, 0.])

    def na_(off):
        Pn = pista('nave', C, off); V.cantar_nave(Pn, 'diciendo que estaba aquí.', V.q(5), 3.5, semilla=33, desde=57)
        Zn = zp(Pn); k = Zn[0].shape[0]
        c = coh[:k] if not off else np.r_[(coh[:-1] + coh[1:]) / 2, 1][:k]
        a = anchos[:k] if not off else np.r_[(anchos[:-1] + anchos[1:]) / 2, 0][:k]
        return [V.quitar_tiempo(V.desenfocar(z, a, s), c, s + 1) for s, z in ((1, Zn[0]), (3, Zn[1]))]
    na = liso('t10-nave', na_, C)
    n = L(C)
    y = mezclar([(cama, 'medio', .9), (ti, 'cerca', 1.0), (na, 'medio', 1.15)], n, cola=3.4, afinado=.8)
    MED['t10'] = {'planitud_por_compas_6_a_9 (1 = ruido, 0 = tono)': [planitud(na, c, c + 1) for c in range(5, 9)]}
    guardar('t10', y, 'el epílogo: la portadora con su latido, la Tierra cerca, y la voz que sale del ruido')


if __name__ == '__main__':
    pedidas = sys.argv[1:] or LISTA
    for nm in pedidas:
        print(nm, globals()[nm].__doc__.split('\n')[0], flush=True)
        globals()[nm]()
    json.dump(MED, open(MEDIDAS, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in MED.items() if k in pedidas}, ensure_ascii=False, indent=1))
