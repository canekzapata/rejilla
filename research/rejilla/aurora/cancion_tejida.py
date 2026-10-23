"""Rejilla 04 · «sobre la aurora» — loop D: tejer.

Canek sobre el loop C: «todavía parecen muy bruscos los cambios, como si cambiaras de A a B y no
en una gradiente tejiendo el sonido»; y en entropía y confundo «el ruido blanco no está
encasillado como instrumento, sino sólo es una capa abstracta completa».

Por qué pasaba: en la rejilla un gesto cambia por columna y una columna es un compás, así que
la arena, la entropía y el negativo subían en escalones de 2.3 s, y caían sobre la pista entera.

Aquí:
1. La imagen base va LIMPIA. Cada gesto se renderiza en VERSIONES paralelas (sólo las columnas
   de su sección) y se cruzan con curvas continuas, muestra por muestra (potencia constante).
   Cada instrumento tiene su propia curva y su propio retraso: se tejen, no cambian juntos.
2. RUIDO ENCASILLADO: la versión ruidosa de cada instrumento recibe la envolvente de ese mismo
   instrumento limpio. El ruido del piano preparado toca su ritmo de 7; el del órgano respira
   con sus acordes.
3. El negativo de la voz vive sólo dentro de las frases y en la banda de los formantes, y la
   voz entra y sale de él en una ola lenta.
4. Entradas y regresos con crescendo; la prolación entra y sale en rampa; el ruido del final
   se vuelve acorde con una curva continua.

La composición es la misma del loop C (mismas semillas, mismas notas). Salida nueva, no pisa la C.

    python aurora/cancion_tejida.py            # ~25 min
    python aurora/cancion_tejida.py --tejer    # rehace sólo el tejido y la mezcla (las versiones ya están)
"""
import json, math, sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
import cancion as K
from motor import M, S, T, SR_OUT, sintetizar, leer, arena, entropia, negativo, peine, ruido

AQUI = Path(__file__).parent
R2 = AQUI.parent / 'render' / 'aurora-tejida'; R2.mkdir(parents=True, exist_ok=True)
TAG = 's1015-tejida'
COLS = K.COLS
L = lambda c: int(round(c * T * SR_OUT))               # compases → muestras de salida
NOMBRES = K.NOMBRES
BANDA = ['bombo', 'bateria', 'bajo', 'ostinato', 'armonia', 'helecho', 'robot']
VOCES = ['voz', 'magnetica']


# ───────────── versiones (cada una: sólo las columnas de su sección) ─────────────
def versiones(n, ZL, ZR):
    """{(sección, nombre_versión): (ZL_sub, ZR_sub)}"""
    out = {}
    sub = lambda Z, cols: np.ascontiguousarray(Z[cols[0]:cols[-1] + 1])
    t = COLS['tormenta']; idx = list(range(len(t)))
    if n not in ('radio', 'ruido'):
        g_med, g_max = (1, 6) if n in VOCES else (3, 14)
        for nom, g in (('arena-media', g_med), ('arena-max', g_max)):
            out[('tormenta', nom)] = (arena(sub(ZL, t), idx, [g] * len(t)), arena(sub(ZR, t), idx, [g] * len(t)))
    e = COLS['entropía']; idx = list(range(len(e)))
    if n not in ('radio', 'ruido'):
        espejo = n in ('ostinato', 'armonia')
        zl, zr = sub(ZL, e), sub(ZR, e)
        if espejo:
            zl, zr = np.conj(zl), np.conj(zr)
            out[('entropía', 'espejo')] = (zl.copy(), zr.copy())
        top = .5 if n in VOCES else 1.0
        for nom, ep in (('ruido-medio', .5 * top), ('ruido-pleno', top)):
            out[('entropía', nom)] = (entropia(zl, idx, [ep] * len(e), 7), entropia(zr, idx, [ep] * len(e), 8))
    c = COLS['confundo']; idx = list(range(len(c)))
    if n in ('ostinato', 'armonia'):
        out[('confundo', 'espejo')] = (np.conj(sub(ZL, c)), np.conj(sub(ZR, c)))
    if n in VOCES:
        out[('confundo', 'negativo')] = (negativo(sub(ZL, c), idx, lo=250, hi=3500, igualar=.35),
                                         negativo(sub(ZR, c), idx, lo=250, hi=3500, igualar=.35))
    if n == 'ruido':
        s = COLS['sistema']
        bajo, voces = K.ACORDE[s[0]]
        w = peine([bajo, bajo + 12] + voces + [v + 12 for v in voces])
        z = ruido(semilla=23) * 2e-3
        zl = np.tile(z, (len(s), 1)); zr = zl * np.exp(1j * .9)
        out[('sistema', 'ruido')] = (zl, zr)
        out[('sistema', 'acorde')] = (zl * w[None] * 6, zr * w[None] * 6)
    return out


def renderizar():
    P, versos, informe = K.componer()
    escalas = {}
    v0, v1 = COLS['se expande'][0], COLS['se expande'][-1] + 1
    for n, p in P.items():
        ZL, ZR = p.escribir()
        if n == 'ruido': ZL[:] = 0; ZR[:] = 0          # el ruido del final vive sólo en sus versiones
        escalas[n] = sintetizar(ZL, ZR, R2 / f'{n}.wav')
        for (sec, nom), (zl, zr) in versiones(n, ZL, ZR).items():
            escalas[f'{n}|{sec}|{nom}'] = sintetizar(zl, zr, R2 / f'{n}__{sec}__{nom}.wav')
        if n in K.PROLACION:
            for k, sr in ((1, S * 3 // 2), (2, 2 * S)):
                escalas[f'{n}|prolacion|{k}'] = sintetizar(np.ascontiguousarray(ZL[v0:v1]), np.ascontiguousarray(ZR[v0:v1]),
                                                           R2 / f'{n}__prolacion__{k}.wav', sr=sr)
        del ZL, ZR
        print('  pista', n, 'lista', flush=True)
    json.dump({'escalas': escalas}, open(R2 / 'escalas.json', 'w'))


# ───────────── el telar ─────────────
def a_largo(x, ns):
    """Las versiones se sintetizan aparte y pueden salir una muestra más cortas: se ajustan."""
    if len(x) >= ns: return x[:ns]
    return np.concatenate([x, np.zeros((ns - len(x),) + x.shape[1:])])


def envolvente(x, ms=18):
    w = max(3, int(SR_OUT * ms / 1000))
    k = np.hanning(w); k /= k.sum()
    m = x if x.ndim == 1 else np.sqrt((x ** 2).mean(1))
    return np.sqrt(np.convolve(m ** 2, k, 'same'))


def encasillar(ruidoso, limpio):
    """El ruido toca como el instrumento: se le pone la envolvente del limpio."""
    el, er = envolvente(limpio), envolvente(ruidoso)
    g = el / (er + 1e-4 * (er.max() + 1e-12))
    g = np.minimum(g, 4.0)
    return ruidoso * g[:, None]


def suave(u):                                           # 0..1 → 0..1 sin quiebres (smootherstep)
    u = np.clip(u, 0, 1); return u * u * u * (u * (6 * u - 15) + 10)


def recorrido(n_muestras, k_versiones, u):
    """Pesos de potencia constante para recorrer k versiones a lo largo de u (0..k-1)."""
    W = np.zeros((k_versiones, n_muestras))
    i = np.clip(np.floor(u).astype(int), 0, k_versiones - 2)
    f = np.clip(u - i, 0, 1)
    a, b = np.cos(f * np.pi / 2), np.sin(f * np.pi / 2)
    W[i, np.arange(n_muestras)] = a
    W[i + 1, np.arange(n_muestras)] += b
    return W


# cada instrumento tiene su propio retraso en el tejido (en compases): no cambian juntos
RETRASO = {'bombo': .0, 'bateria': .4, 'bajo': .9, 'ostinato': .2, 'armonia': 1.3, 'helecho': .6, 'robot': .7,
           'voz': 2.2, 'magnetica': 1.6}


def tejer():
    esc = json.load(open(R2 / 'escalas.json'))['escalas']
    curvas = {}                                                       # para el dibujo del telar
    for n in NOMBRES:
        y = leer(R2 / f'{n}.wav', esc[n])
        limpio = y.copy()
        d = RETRASO.get(n, 0)

        # tormenta: limpio → arena media → arena máxima, cada uno a su tiempo
        if f'{n}|tormenta|arena-max' in esc:
            c0, c1 = COLS['tormenta'][0], COLS['tormenta'][-1] + 1
            seg = slice(L(c0), L(c1)); ns = L(c1) - L(c0)
            vs = [limpio[seg], a_largo(leer(R2 / f'{n}__tormenta__arena-media.wav', esc[f'{n}|tormenta|arena-media']), ns),
                  a_largo(leer(R2 / f'{n}__tormenta__arena-max.wav', esc[f'{n}|tormenta|arena-max']), ns)]
            tt = np.arange(ns) / SR_OUT / T                            # compases desde el inicio de la tormenta
            u = 2 * suave((tt - d * .6) / (len(COLS['tormenta']) - d * .6))
            W = recorrido(ns, 3, u)
            y[seg] = sum(W[k][:, None] * vs[k] for k in range(3))
            curvas[(n, 'tormenta')] = (c0, u[::480] / 2)

        # entropía: (espejo) → ruido medio → ruido pleno, el ruido encasillado en la envolvente del instrumento
        if f'{n}|entropía|ruido-pleno' in esc:
            c0, c1 = COLS['entropía'][0], COLS['entropía'][-1] + 1
            seg = slice(L(c0), L(c1)); ns = L(c1) - L(c0)
            vs = [limpio[seg]]
            if f'{n}|entropía|espejo' in esc:
                vs.append(a_largo(leer(R2 / f'{n}__entropía__espejo.wav', esc[f'{n}|entropía|espejo']), ns))
            ref = vs[-1]
            for nom in ('ruido-medio', 'ruido-pleno'):
                z = a_largo(leer(R2 / f'{n}__entropía__{nom}.wav', esc[f'{n}|entropía|{nom}']), ns)
                vs.append(encasillar(z, ref) if n not in VOCES else z)
            tt = np.arange(ns) / SR_OUT / T
            k = len(vs)
            u = (k - 1) * suave((tt - d * .5) / (len(COLS['entropía']) - .3 - d * .5))
            W = recorrido(ns, k, u)
            y[seg] = sum(W[j][:, None] * vs[j] for j in range(k))
            curvas[(n, 'entropía')] = (c0, u[::480] / (k - 1))

        # confundo: el ostinato y la armonía siguen en espejo y regresan al derecho al final;
        # la voz entra y sale de su negativo en una ola lenta, sólo dentro de las frases
        c0, c1 = COLS['confundo'][0], COLS['confundo'][-1] + 1
        seg = slice(L(c0), L(c1)); ns = L(c1) - L(c0)
        tt = np.arange(ns) / SR_OUT / T
        if f'{n}|confundo|espejo' in esc:
            esp = a_largo(leer(R2 / f'{n}__confundo__espejo.wav', esc[f'{n}|confundo|espejo']), ns)
            u = 1 - suave((tt - (len(COLS['confundo']) - 2.5)) / 2.2)    # espejo hasta casi el final
            W = recorrido(ns, 2, u)
            y[seg] = W[0][:, None] * limpio[seg] + W[1][:, None] * esp
            curvas[(n, 'confundo')] = (c0, u[::480])
        if f'{n}|confundo|negativo' in esc:
            neg = a_largo(leer(R2 / f'{n}__confundo__negativo.wav', esc[f'{n}|confundo|negativo']), ns)
            frases = envolvente(limpio[seg], ms=350); frases = np.clip(frases / (np.percentile(frases, 95) + 1e-12), 0, 1)
            neg = neg * frases[:, None]                                     # el negativo sólo vive en las frases
            u = .5 - .5 * np.cos(2 * np.pi * np.clip(tt - .5, 0, None) / 3.2)  # una ola de 3.2 compases
            u *= suave(tt / 1.5) * (1 - suave((tt - (len(COLS['confundo']) - 1.5)) / 1.4))
            W = recorrido(ns, 2, u)
            y[seg] = W[0][:, None] * limpio[seg] + W[1][:, None] * neg
            curvas[(n, 'confundo')] = (c0, u[::480])

        # se expande: la prolación entra en rampa (2 compases) y se va en el último
        if n in K.PROLACION:
            c0, c1 = COLS['se expande'][0], COLS['se expande'][-1] + 1
            ns = L(c1) - L(c0); tt = np.arange(ns) / SR_OUT / T
            env = suave(tt / 2) * (1 - suave((tt - (c1 - c0 - 1.2)) / 1.2))
            for k, pan in ((1, -.7), (2, .7)):
                z = leer(R2 / f'{n}__prolacion__{k}.wav', esc[f'{n}|prolacion|{k}'])
                z = np.concatenate([z] * 3)[:ns]
                gL, gR = M.paneo(pan)
                y[L(c0):L(c0) + ns, 0] += .45 * gL * env * z[:, 0]
                y[L(c0):L(c0) + ns, 1] += .45 * gR * env * z[:, 1]
            curvas[(n, 'se expande')] = (c0, env[::480])

        # sistema: el ruido se vuelve acorde por una curva continua, no por columnas
        if f'{n}|sistema|acorde' in esc:
            c0, c1 = COLS['sistema'][0], COLS['sistema'][-1] + 1
            seg = slice(L(c0), L(c1)); ns = L(c1) - L(c0); tt = np.arange(ns) / SR_OUT / T
            vs = [a_largo(leer(R2 / f'{n}__sistema__{v}.wav', esc[f'{n}|sistema|{v}']), ns) for v in ('ruido', 'acorde')]
            u = suave((tt - .5) / 5)
            W = recorrido(ns, 2, u)
            entra = suave(tt / 1.5)[:, None] * (1 - suave((tt - (c1 - c0 - 1.6)) / 1.6))[:, None]
            y[seg] = entra * (W[0][:, None] * vs[0] + W[1][:, None] * vs[1])
            curvas[(n, 'sistema')] = (c0, u[::480])

        # entradas con crescendo: la batería al entrar, la banda al volver de los callejones
        def rampa(c_ini, compases, g0=0.0):
            i0, i1 = L(c_ini), L(c_ini + compases)
            r = g0 + (1 - g0) * suave(np.arange(i1 - i0) / (i1 - i0))
            y[i0:i1] *= r[:, None]
        if n in ('bombo', 'bateria'): rampa(COLS['señal'][4], 2)
        if n in ('bombo', 'bateria', 'bajo', 'ostinato', 'armonia'):
            rampa(COLS['entropía'][0], 1.2, .25)                       # después del callejón de Mi
            rampa(COLS['confundo'][0], 1.5, .2)                        # después del helecho
        wavfile.write(R2 / f'tl-{n}.wav', SR_OUT, y.astype(np.float32))
        print('  tejida', n, flush=True)
    json.dump({f'{a}|{b}': [c0, list(map(float, u))] for (a, b), (c0, u) in curvas.items()},
              open(R2 / 'curvas.json', 'w'))


def mezclar():
    K.R = R2; K.TAG = TAG                                            # la misma mezcla del loop C, en otra carpeta
    K.mezclar()


if __name__ == '__main__':
    if '--tejer' not in sys.argv: renderizar()
    tejer()
    mezclar()
