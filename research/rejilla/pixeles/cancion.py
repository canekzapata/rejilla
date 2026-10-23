"""Rejilla 05 · «los pixeles y la luna» (poema de Canek Zapata, *poemas del espacio*) — loop C.

Todo es 5:4. Cada sección se escribe en Mi y suena transportada por LECTURA (reloj móvil):
  intro, verso 1, pre, coro 1 ............ Mi        (1)
  verso 2, coro 2 ........................ Sol#      (5/4, compensado: mismo tempo)
  puente ................................. Do grave  (el coro leído a 4/5 sin compensar: lento)
  coro final ............................. Do        (25/16)
  outro .................................. Mi −41 ¢  (125/64: tres terceras no cierran la octava)
Canek sobre las demos: «la parte más bella es puente y paro de cinta» → las MODULACIONES son
cinta: el último compás se vuelve a leer más rápido (o más lento), versiones tejidas, hasta caer
en la tonalidad nueva. Del puente al coro final la cinta acelera casi una octava: el despegue de
«los astronautas». Al final, un paro de cinta largo. Y el tornasol («se siente poco») pasa a lo
que tiene espectro continuo: una pared de ruido afinada al acorde y los hats del pre.

La voz y la batería NO se transportan con la cinta: la voz se canta con PSOLA a la altura exacta
de cada tercera justa (en cents) y la batería conserva su peso; sólo en el puente y en las
transiciones todo se lee junto.

    python pixeles/cancion.py            # ~30 min
    python pixeles/cancion.py --letra    # ver dónde cae la letra
    python pixeles/cancion.py --mezcla   # sólo la mezcla
"""
import hashlib, json, math, subprocess, sys, zlib
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from motor import M, S0, T0, N, H, SR_OUT, rng, Pista, reloj, q, sintetizar, leer, tornasol, arena, cinta
import instrumentos as I

AQUI = Path(__file__).parent
R = AQUI.parent / 'render' / 'pixeles'; R.mkdir(parents=True, exist_ok=True)
TAG = 's5454'
mel_rng = np.random.default_rng(5454)
F0 = S0 / N


def suave(u):
    u = np.clip(u, 0, 1); return u * u * u * (u * (6 * u - 15) + 10)


def a_largo(x, n):
    return x[:n] if len(x) >= n else np.concatenate([x, np.zeros((n - len(x),) + x.shape[1:])])


def recorrido(vs, u):
    k = len(vs); i = np.clip(np.floor(u).astype(int), 0, k - 2); f = np.clip(u - i, 0, 1)
    out = np.zeros_like(vs[0])
    for j in range(k):
        w = np.where(i == j, np.cos(f * np.pi / 2), 0) + np.where(i + 1 == j, np.sin(f * np.pi / 2), 0)
        out += w[:, None] * vs[j]
    return out


# ───────────── la forma ─────────────
# (nombre, reloj r (transporte por lectura), lectura (1 = compensada; 4/5 = lenta), compases, armonía, oct)
SECC = [
    ('intro', 1, 1, 4, 'verso', 0),
    ('verso 1', 1, 1, 8, 'verso', 0),
    ('pre', 1, 1, 4, 'pre', 0),
    ('coro 1', 1, 1, 8, 'coro', 0),
    ('verso 2', 5 / 4, 1, 8, 'verso', 0),
    ('coro 2', 5 / 4, 1, 8, 'coro', 0),
    ('puente', 1, 4 / 5, 8, 'coro', 0),          # el coro leído lento: suena Do grave, 78 bpm
    ('coro final', 25 / 16, 1, 8, 'coro', -12),  # Do; escrito una octava abajo para no adelgazar
    ('outro', 125 / 64, 1, 4, 'final', -12),     # Mi, 41 cents abajo
]
# las cintas: (después de qué sección, de qué lectura a qué lectura relativa, compases que dura)
CINTAS = {'coro 1': (1, 5 / 4, 1.0), 'coro 2': (1, 4 / 5, 1.0), 'puente': (1, (25 / 16) / (4 / 5), 2.0),
          'coro final': (1, (125 / 64) / (25 / 16), 1.0)}
PARO = (1, .42, 5.0)                             # el paro de cinta final: de 1 a .42 en 5 compases
PARO_GANANCIA = 3.2                              # medido: al frenar se hunde al sub; sin esto quedaba a −38 dB

LETRA = {
    'verso 1': ['la imagen en los monitores está compuesta de luz', 'millones de pequeños emisores que la irradian'],
    'pre': ['pequeños puntos que no pueden imitar', 'el baile de los colores en el tornasol', 'de un charco con aceite'],
    'coro 1': ['los pixeles no tienen sombra', 'no reflejan luz', 'ni tienen textura', 'los pixeles no tienen sombra'],
    'verso 2': ['los pixeles son ceros y unos', 'que indican de qué color', 'verás la luz en el monitor'],
    'coro 2': ['los pixeles no tienen sombra', 'no reflejan luz', 'ni tienen textura', 'los pixeles no tienen sombra'],
    'puente': ['son tan fríos', 'que no me extraña'],
    'coro final': ['que los hayan traído', 'los astronautas desde la luna', 'los pixeles no tienen sombra', 'desde la luna'],
    'outro': ['desde la luna'],
}
ENTRADA = {'verso 1': (1, 3), 'pre': (0, 2), 'coro 1': (0, 4), 'verso 2': (1, 3), 'coro 2': (0, 4),
           'puente': (1, 10), 'coro final': (0, 3), 'outro': (0, 2)}
# el gancho: siempre la misma melodía (Sol# en Mi → Sol natural en Do menor: el roce fantasmal)
GANCHO = ([59, 64, 63, 64, 67, 67, 63, 60, 60], [1, 3, 4, 6, 17, 19, 20, 22, 24], [2, 1, 2, 3, 2, 1, 2, 2, 6])

ARM = {
    'verso': [(52, (64, 68, 71)), (52, (60, 64, 67)), (52, (63, 68, 72)), (52, (60, 64, 67))],
    'pre': [(47, (64, 68, 71)), (47, (63, 66, 71)), (47, (60, 64, 67)), (47, (63, 66, 71))],
    'coro': [(52, False), (48, True), (56, False), (52, True), (48, False), (56, True), (52, False), (48, True)],
    'final': [(52, False)] * 8,
}


def tonos_del_compas(arm, b):
    """Clases de altura (en Mi escrito) del compás b de una armonía."""
    x = ARM[arm][b % len(ARM[arm])]
    if arm in ('verso', 'pre'):
        bajo, tri = x; return sorted({n % 12 for n in tri} | {bajo % 12}), bajo % 12
    raiz, menor = x
    return sorted({raiz % 12, (raiz + (3 if menor else 4)) % 12, (raiz + 7) % 12}), raiz % 12


def melodia(sec, arm, linea, inicio16, prev, centro=62):
    """Ritmo por acentos y alturas por contorno + acorde (como en «sobre la aurora»), en Mi escrito."""
    sil, _ = I.silabear(linea)
    tonicas, k = set(), 0
    for p in linea.replace(',', ' ').split():
        ss = I.SIL.silabea(p); t = I.SIL.tonica(p)
        if t is not None: tonicas.add(k + t)
        k += len(ss)
    forma = mel_rng.choice(['arco', 'baja', 'sube', 'ola'])
    cont = lambda u: {'arco': 5 * math.sin(math.pi * u), 'baja': 4 - 8 * u, 'sube': -3 + 7 * u, 'ola': 4 * math.sin(2 * math.pi * u)}[forma]
    notas, pos, dur, t = [], [], [], 0
    n = len(sil)
    for i in range(n):
        ton = i in tonicas
        if ton and i and mel_rng.uniform() < .35: t += 1
        d = 4 if i == n - 1 else (2 if ton else 1)
        pcs, raiz = tonos_del_compas(arm, (inicio16 + t) // 16)
        obj = .3 * prev + .7 * (centro + cont(i / max(1, n - 1)))
        cand = [m for m in range(55, 71) if m % 12 in pcs]
        if i == n - 1: cand = [m for m in range(55, 71) if m % 12 in (raiz, (raiz + 7) % 12)]
        elif not ton: cand += [m + 1 for m in cand if m + 1 < 71]
        def costo(c):
            rep = 2.5 if len(notas) >= 2 and notas[-1] == notas[-2] == c else 0
            return abs(c - obj) + rep + (0 if ton else max(0, abs(c - prev) - 3) * .8) + mel_rng.uniform(0, .9)
        m = min(cand, key=costo)
        notas.append(m); pos.append(t); dur.append(d); prev = m; t += d
    return notas, pos, dur, t, prev


def colocar_letra():
    """{sección: [(línea, inicio16 relativo a la sección, notas en Mi escrito, pos, dur)]}"""
    out, prev = {}, 62
    for sec, r, lec, nc, arm, oct_ in SECC:
        if sec not in LETRA: continue
        ent, aire = ENTRADA[sec]; cur = ent * 16 + 1; out[sec] = []
        for ln in LETRA[sec]:
            if ln == 'los pixeles no tienen sombra':
                notas, pos, dur = GANCHO; largo = pos[-1] + dur[-1]
            else:
                notas, pos, dur, largo, prev = melodia(sec, arm, ln, cur, prev)
            out[sec].append((ln, cur, list(notas), list(pos), list(dur)))
            cur += largo + aire
            if cur % 2 == 0: cur += 1
        if cur > nc * 16 + 4: print(f'  ¡ojo! {sec}: la letra se pasa {cur - nc * 16} dieciseisavos')
    return out


# ───────────── escribir una sección ─────────────
CINCO = [0, 3.2, 6.4, 9.6, 12.8]


def escribir_seccion(sec, r, lec, nc, arm, oct_, letra):
    """Devuelve {grupo: Pista}. tonal y chops con el reloj r; kit y voz con el reloj 1 (no se
    transportan). En el puente todo va en una sola imagen (todo se lee lento junto)."""
    C = nc + 1
    junta = (sec == 'puente')
    with reloj(r):
        Pt, Pc = Pista('tonal', C), Pista('chops', C)
    with reloj(1):
        Pk, Pv = Pista('kit', C), Pista('voz', C)
    if junta: Pk = Pv = Pt
    for b in range(nc):
        x = ARM[arm][b % len(ARM[arm])]
        with reloj(r):
            if arm in ('verso', 'pre'):
                bajo, tri = x
                for i, n in enumerate(tri): I.rhodes(Pt, n - 12 + oct_, q(b, 0) + .012 * i, .7, M.T * .95, pan=-.3 + .3 * i)
                if sec != 'intro' or b >= 2:
                    for k, pos in enumerate(CINCO):
                        pop = k in (1, 3)
                        I.bajo_dedos(Pt, bajo + oct_ + (12 if pop else 0), q(b, pos), M.T / 16 * (2.2 if pop else 2.8),
                                     .9 if k == 0 else .75, pop=pop)
                if sec != 'intro':
                    for pos in (2, 6, 9, 14): I.guitarra_cortada(Pt, [n + oct_ for n in tri], q(b, pos), .8 if pos != 9 else .55)
            elif arm == 'coro':
                raiz, menor = x
                I.pared_espectral(Pt, raiz + 12 + oct_, menor, q(b, 0), M.T * .98, 1.2, semilla=zlib.crc32(f"{sec}|{b}".encode()) % 997)
                for pos in range(0, 16, 2):
                    I.bajo_dedos(Pt, (raiz - 12 if raiz - 12 >= 36 else raiz) + oct_, q(b, pos), M.T / 16 * 1.6, .8)
                if sec == 'coro final':
                    for pos, du in ((3, 2), (11, 3)):
                        for n in (raiz, raiz + (3 if menor else 4), raiz + 7):
                            I.rhodes(Pt, n + oct_, q(b, pos), .55, du * M.T / 16, pan=.3)
            else:   # final: Mi, vuelto a tocar cada compás (medido: tocado una sola vez se apagaba a la mitad
                    # y dejaba 3 s de silencio antes del paro de cinta)
                v = 1.0 - .12 * b
                I.pared_espectral(Pt, 64 + oct_, False, q(b, 0), M.T * .98, v, semilla=77 + b)
                for i, n in enumerate((52, 59, 64, 68, 71)): I.rhodes(Pt, n + oct_, q(b, 0) + .01 * i, .62 * v, M.T * .95)
            # los ceros y unos de «luna» en los coros (Zira, con el reloj: suben con la cinta)
            if arm == 'coro' and b % 4 == 2 and sec != 'puente':
                I.ceros_y_unos(Pc, 'luna', q(b, 0), alto=76 + oct_ // 2, bajo=71 + oct_ // 2, g=.32)
        # la batería, con el reloj de lectura (no sube con la cinta)
        with reloj(1 if not junta else 1):
            kit = sec not in ('intro', 'outro') or (sec == 'intro' and b >= 2) or (sec == 'outro' and b < 2)
            if kit:
                if arm == 'coro':
                    for pos in (0, 6, 8, 11): I.bombo80(Pk, q(b, pos), .95)
                    for pos in (4, 12): I.caja80(Pk, q(b, pos), .9)
                    for pos in range(0, 16, 2): I.hat80(Pk, q(b, pos), .5)
                elif sec == 'intro':
                    for pos in range(16): I.hat80(Pk, q(b, pos), .35 if pos % 2 == 0 else .18)
                else:
                    for pos in (0, 7, 10): I.bombo80(Pk, q(b, pos), .9)
                    for pos in (4, 12): I.caja80(Pk, q(b, pos), .8)
                    for pos in range(16): I.hat80(Pk, q(b, pos), .55 if pos % 2 == 0 else .3)
                    if sec == 'pre' and b == 3:
                        for i in range(8): I.caja80(Pk, q(b, 8 + i), .25 + .08 * i)
    # la voz: en Mi escrito + los cents de la tercera justa de esta sección, en su registro
    informe = []
    trans = 12 * math.log2(r) - 12 * round(math.log2(r))
    for ln, cur, notas, pos, dur in letra.get(sec, []):
        with reloj(1):
            t0 = cur * M.T / 16
            if junta:
                informe += I.cantar(Pv, ln, notas, pos, dur, t0, g=1.25)
                I.cantar(Pv, ln, notas, pos, dur, t0, voz='zira', g=.4, transporte=-12)
            else:
                informe += I.cantar(Pv, ln, [n + trans for n in notas], pos, dur, t0, g=1.25)
                if sec.startswith('coro'):
                    I.cantar(Pv, ln, [n + trans for n in notas], pos, dur, t0, voz='zira', g=.42, transporte=-12)
    grupos = {'tonal': Pt} if junta else {'tonal': Pt, 'chops': Pc, 'kit': Pk, 'voz': Pv}
    return grupos, informe


# el tornasol, donde se oye: pared de ruido afinada al acorde (intro, pre) y hats del pre
TAUS = [0.3, 0.6, 1.0, 1.6, 2.5, 3.8]


def aceite(nc, arm, ganancia=2.2e-3):
    """Ruido con fase fija por fila × peine de armónicos del acorde de cada compás: espectro continuo
    donde la interferencia sí dibuja bandas."""
    k = np.arange(H); f = k * F0
    base = np.random.default_rng(31).uniform(-np.pi, np.pi, H)
    ZL = np.zeros((nc + 1, H), complex); ZR = np.zeros_like(ZL)
    for b in range(nc):
        pcs, raiz = tonos_del_compas(arm, b)
        w = np.zeros(H)
        for pc in pcs:
            for o in range(2, 7):
                fc = 440 * 2 ** ((pc + 12 * o - 9 - 48) / 12)
                for h in (1, 2, 3):
                    w += 1 / h / (1 + ((f - h * fc) / 6) ** 2)
        mag = ganancia * (.15 + w / w.max()) * (f > 80) / (1 + (f / 2500) ** 2)
        ZL[b] = mag * np.exp(1j * base); ZR[b] = mag * np.exp(1j * (base + .8))
    return ZL, ZR


def tornasol_tejido(ZL, ZR, nombre, sr, n_out, periodo_compases=2.0):
    """Versiones con distintos grosores de aceite, tejidas por una curva que sube y baja."""
    cols = list(range(ZL.shape[0])); vs = []
    for k, tau in enumerate(TAUS):
        esc = sintetizar(tornasol(ZL, cols, tau, .95), tornasol(ZR, cols, tau * 1.09, .95), R / f'{nombre}-tau{k}.wav', sr)
        vs.append(a_largo(leer(R / f'{nombre}-tau{k}.wav', esc), n_out))
    t = np.arange(n_out) / SR_OUT / T0
    u = (len(TAUS) - 1) * (.5 - .5 * np.cos(2 * np.pi * t / (2 * periodo_compases)))
    return recorrido(vs, u)


def cinta_tejida(Zs, nombre, sr_base, k0, k1, n_out, pasos=6):
    """La cinta que cambia de velocidad: el último compás (ZL, ZR) leído de k0 a k1 veces la lectura
    base, en `pasos` versiones; cada versión se repite (la cinta sigue girando) y se tejen."""
    vs = []
    for j, k in enumerate(np.geomspace(k0, k1, pasos)):
        suma = None
        for g, (zl, zr) in Zs.items():
            esc = sintetizar(zl, zr, R / f'{nombre}-{g}-{j}.wav', sr=sr_base * k)
            y = leer(R / f'{nombre}-{g}-{j}.wav', esc)
            y = np.concatenate([y] * (int(n_out / max(1, len(y))) + 2))[:n_out]
            suma = y if suma is None else suma + y
        vs.append(suma)
    t = np.arange(n_out) / n_out
    return recorrido(vs, (pasos - 1) * suave(t))


# ───────────── la canción ─────────────
GRUPOS = ['tonal', 'chops', 'kit', 'voz', 'aceite']


def main():
    letra = colocar_letra()
    linea = {g: [] for g in GRUPOS}                       # (inicio en muestras, audio)
    t_cursor = 0; marcas, informe_total = [], []
    for sec, r, lec, nc, arm, oct_ in SECC:
        print(f'— {sec} (reloj {r:.4f}, lectura {lec})', flush=True)
        grupos, informe = escribir_seccion(sec, r, lec, nc, arm, oct_, letra)
        informe_total += [dict(s, seccion=sec) for s in informe]
        dur_sec = int(round(nc * T0 / lec * SR_OUT))
        marcas.append((sec, t_cursor / SR_OUT))
        ultimos = {}
        for g, P in grupos.items():
            ZL, ZR = P.escribir()
            if sec == 'pre' and g == 'kit':               # el jet del aceite en los hats del pre
                y = tornasol_tejido(ZL, ZR, f'{sec}-kit', S0 * lec, len(ZL) * int(T0 * SR_OUT) + 1000, 1.0)
            else:
                esc = sintetizar(ZL, ZR, R / f'{sec}-{g}.wav', S0 * lec); y = leer(R / f'{sec}-{g}.wav', esc)
            linea[g].append((t_cursor, y))
            ultimos[g] = (np.ascontiguousarray(ZL[nc - 1:nc]), np.ascontiguousarray(ZR[nc - 1:nc]))
        if sec in ('intro', 'pre'):
            zl, zr = aceite(nc, arm)
            linea['aceite'].append((t_cursor, tornasol_tejido(zl, zr, f'{sec}-aceite', S0, dur_sec + int(T0 * SR_OUT))))
        t_cursor += dur_sec
        if sec in CINTAS:                                   # la cinta que acelera o frena hacia lo que sigue
            k0, k1, comp = CINTAS[sec]
            n = int(round(comp * T0 * SR_OUT))
            zs = {g: z for g, z in ultimos.items() if g in ('tonal', 'kit', 'chops')}
            y = cinta_tejida(zs, f'cinta-{sec}', S0 * lec, k0, k1, n)
            y *= np.concatenate([np.ones(n - int(.15 * SR_OUT)), np.linspace(1, .6, int(.15 * SR_OUT))])[:, None]
            linea['tonal'].append((t_cursor, y)); marcas.append((f'cinta {sec}', t_cursor / SR_OUT))
            t_cursor += n
    # el paro de cinta final: los dos últimos compases del outro leídos cada vez más lento
    sec, r, lec, nc, arm, oct_ = SECC[-1]
    grupos, _ = escribir_seccion('outro-paro', r, 1, 2, 'final', 0, {})     # registro medio: al frenar no se hunde
    zs = {}
    for g in ('tonal',):
        ZL, ZR = grupos[g].escribir(); zs[g] = (np.ascontiguousarray(ZL[:2]), np.ascontiguousarray(ZR[:2]))
    k0, k1, comp = PARO
    n = int(round(comp * T0 * SR_OUT))
    y = cinta_tejida(zs, 'paro', S0, k0, k1, n, pasos=7)
    tt = np.arange(n) / n
    y *= PARO_GANANCIA * (1 - suave((tt - .55) / .45))[:, None]
    linea['tonal'].append((t_cursor - int(.5 * T0 * SR_OUT), y)); marcas.append(('paro de cinta', t_cursor / SR_OUT))
    total = t_cursor + n + int(SR_OUT)

    piezas = {}
    for g in GRUPOS:
        for k, (t0, y) in enumerate(linea[g]):
            ruta = R / 'piezas' / f'{g}-{k:02d}.npy'; ruta.parent.mkdir(exist_ok=True); np.save(ruta, y.astype(np.float32))
            piezas.setdefault(g, []).append([t0, str(ruta.name)])
    json.dump({'piezas': piezas, 'total': total}, open(R / 'piezas.json', 'w'))
    for g in GRUPOS:
        out = np.zeros((total, 2))
        for t0, y in linea[g]:
            e = min(total, t0 + len(y)); out[t0:e] += y[:e - t0]
        wavfile.write(R / f'tl-{g}.wav', SR_OUT, out.astype(np.float32))
    json.dump({'marcas': marcas, 'informe': informe_total, 'letra': letra}, open(R / 'partitura.json', 'w', encoding='utf-8'),
              ensure_ascii=False, default=str)
    errs = [abs(s['error_st']) for s in informe_total if s['error_st'] is not None]
    print(f'sílabas {len(informe_total)}, error mediano {np.median(errs):.2f} st, >0.5: {sum(e > .5 for e in errs)}')
    mezclar()


GANANCIA = {'tonal': 1.0, 'chops': 1.0, 'kit': 1.0, 'voz': 1.0, 'aceite': 1.0}


def mezclar():
    """Voz arriba; los coros secos (el pixel), los versos con cuarto y cinta (lo tejido)."""
    marcas = json.load(open(R / 'partitura.json', encoding='utf-8'))['marcas']
    g = GANANCIA
    sr = SR_OUT
    pistas = {n: wavfile.read(R / f'tl-{n}.wav')[1].astype(float) * g[n] for n in GRUPOS}
    total = len(pistas['tonal'])
    # envío a la reverb: 1 en lo tejido (intro, versos, pre, puente, outro), .12 en los coros (el pixel)
    envio = np.ones(total)
    for (sec, t0), (_, t1) in zip(marcas, marcas[1:] + [('fin', total / sr)]):
        if sec.startswith('coro'): envio[int(t0 * sr):int(t1 * sr)] = .12
    envio = np.convolve(envio, np.ones(int(.8 * sr)) / int(.8 * sr), 'same')
    # cinta (wow y flutter) en lo tonal fuera de los coros
    tonal = pistas['tonal']
    # lo que se lee lento baja el bajo y el bombo al sub (medido: −1.5 a −2.5 dB del total): se recorta ahí
    lento = np.zeros(total)
    for (sec, t0), (_, t1) in zip(marcas, marcas[1:] + [('fin', total / sr)]):
        if sec == 'puente' or sec.startswith('cinta') or sec == 'paro de cinta': lento[int(t0 * sr):int(t1 * sr)] = 1
    lento = np.convolve(lento, np.ones(int(1.2 * sr)) / int(1.2 * sr), 'same')
    from scipy.signal import butter, sosfiltfilt
    sin_sub = sosfiltfilt(butter(2, 85, 'highpass', fs=sr, output='sos'), tonal, axis=0)
    tonal = tonal * (1 - .6 * lento[:, None]) + sin_sub * (.6 * lento[:, None])
    con_cinta = cinta(tonal)
    tonal = tonal * (1 - envio[:, None] * .8) + con_cinta * (envio[:, None] * .8)
    musica = tonal + pistas['chops'] + pistas['aceite']
    wavfile.write(R / 'mx-musica.wav', sr, musica.astype(np.float32))
    wavfile.write(R / 'mx-envio.wav', sr, ((musica + pistas['voz']) * envio[:, None]).astype(np.float32))
    wavfile.write(R / 'mx-kit.wav', sr, pistas['kit'].astype(np.float32))
    wavfile.write(R / 'mx-voz.wav', sr, pistas['voz'].astype(np.float32))
    grafo = ';'.join([
        "[2]asplit=2[k][kc]",
        "[0][kc]sidechaincompress=threshold=0.05:ratio=2.5:attack=6:release=180:makeup=1[mu]",
        "[3]highpass=f=110,equalizer=f=2800:t=o:w=1.4:g=3[vo]",
        "aevalsrc=d=3.2:s=48000:exprs='(random(0)*2-1)*exp(-t*1.6)|(random(1)*2-1)*exp(-t*1.6)',lowpass=f=5000,highpass=f=200[ir]",
        "[1][ir]afir=dry=0:wet=1[rev]",
        "[mu][vo][k][rev]amix=inputs=4:weights=1 1 1 0.22:normalize=0,highpass=f=26,"
        "acompressor=threshold=0.2:ratio=2.2:attack=15:release=200:makeup=1,"
        "loudnorm=I=-14:TP=-1.2:LRA=10,aresample=48000[out]",
    ])
    final = R / f'los-pixeles-y-la-luna-{TAG}.wav'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(R / 'mx-musica.wav'), '-i', str(R / 'mx-envio.wav'),
                    '-i', str(R / 'mx-kit.wav'), '-i', str(R / 'mx-voz.wav'), '-filter_complex', grafo, '-map', '[out]',
                    '-c:a', 'pcm_s16le', str(final)], check=True)
    m4a = AQUI / f'los-pixeles-y-la-luna-{TAG}.m4a'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(final), '-c:a', 'aac', '-b:a', '224k', str(m4a)], check=True)
    r_ = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(final), '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                        capture_output=True, text=True).stderr
    tail = r_[r_.rfind('Summary:'):]
    val = lambda key: float(tail.split(key)[1].split()[0])
    med = {'I_LUFS': val('I:'), 'LRA': val('LRA:'), 'pico_dBTP': val('Peak:'), 'duracion_s': round(total / sr, 2),
           'sha256_m4a': hashlib.sha256(m4a.read_bytes()).hexdigest()}
    print(med); json.dump(med, open(AQUI / f'medidas-cancion-{TAG}.json', 'w'), indent=1)


def armar():
    """Volver a sumar las pistas desde las piezas guardadas (sin sintetizar)."""
    pz = json.load(open(R / 'piezas.json')); total = pz['total']
    for g in GRUPOS:
        out = np.zeros((total, 2))
        for t0, nombre in pz['piezas'].get(g, []):
            y = np.load(R / 'piezas' / nombre); e = min(total, t0 + len(y)); out[t0:e] += y[:e - t0]
        wavfile.write(R / f'tl-{g}.wav', SR_OUT, out.astype(np.float32))


def rehacer_final():
    """Rehacer sólo el outro y el paro de cinta, reemplazando sus piezas guardadas."""
    pz = json.load(open(R / 'piezas.json')); part = json.load(open(R / 'partitura.json', encoding='utf-8'))
    mk = {s: t for s, t in part['marcas']}
    t_outro = int(round(mk['outro'] * SR_OUT)); t_paro = int(round(mk['paro de cinta'] * SR_OUT))
    sec, r, lec, nc, arm, oct_ = SECC[-1]
    grupos, _ = escribir_seccion(sec, r, lec, nc, arm, oct_, part['letra'])
    for g, P in grupos.items():
        ZL, ZR = P.escribir(); esc = sintetizar(ZL, ZR, R / f'{sec}-{g}.wav', S0 * lec)
        for t0, nombre in pz['piezas'][g]:
            if t0 == t_outro: np.save(R / 'piezas' / nombre, leer(R / f'{sec}-{g}.wav', esc).astype(np.float32))
    grupos, _ = escribir_seccion('outro-paro', r, 1, 2, 'final', 0, {})
    ZL, ZR = grupos['tonal'].escribir(); zs = {'tonal': (np.ascontiguousarray(ZL[:2]), np.ascontiguousarray(ZR[:2]))}
    k0, k1, comp = PARO; n = int(round(comp * T0 * SR_OUT))
    y = cinta_tejida(zs, 'paro', S0, k0, k1, n, pasos=7)
    tt = np.arange(n) / n; y *= PARO_GANANCIA * (1 - suave((tt - .55) / .45))[:, None]
    for t0, nombre in pz['piezas']['tonal']:
        if t0 == t_paro - int(.5 * T0 * SR_OUT): np.save(R / 'piezas' / nombre, y.astype(np.float32))
    armar(); mezclar()


if __name__ == '__main__':
    if '--mezcla' in sys.argv: mezclar()
    elif '--final' in sys.argv: rehacer_final()
    elif '--letra' in sys.argv:
        for sec, ls in colocar_letra().items():
            for ln, cur, notas, pos, dur in ls: print(f'{sec:11s} c{cur // 16}.{cur % 16:<2d} {ln:48s} {notas}')
    else: main()
