"""Primero sueño en el cenote — instrumentos que no son de la tierra (48 kHz).

  metronomos(defs, N)    los metrónomos de cuerda (Ligeti, Poema sinfónico para 100 metrónomos): un escape de madera que hace
                         tic y tac (dos golpes distintos: el péndulo va y viene), una campanita en el primer tiempo si la trae, y
                         una CUERDA QUE SE ACABA: el resorte suelta, el tempo cae poco a poco al final y el metrónomo se para.
                         defs: [{t0, bpm, cuerda (s), compas (0 = sin campana), pan, v}]. Devuelve también los golpes (para el proceso).
  linterna(trazos, N)    la linterna mágica: un sintetizador que lee una imagen como espectro (el ANS de Murzin, 1957, con sus
                         placas de vidrio pintadas). 120 bandas en escala logarítmica de 55 Hz a 7 kHz; la imagen se pinta con
                         trazos (líneas, triángulos, puntos, rellenos) en tiempo × frecuencia y cada banda es un par de osciladores
                         apenas desafinados (el vidrio vibra). Devuelve también la imagen.
  vinilo(curva, N)       el crujido de un disco (Burial): chasquidos de Poisson y un siseo que siguen la curva.
"""
import math
import numpy as np
from scipy.signal import butter, sosfilt
SR = 48000


def _pan(y, p): a = (p + 1) * math.pi / 4; return np.stack([y * math.cos(a), y * math.sin(a)], 1)


def metronomos(defs, N, semilla=0):
    rng = np.random.default_rng(semilla); y = np.zeros((N, 2)); golpes = []
    L = int(.05 * SR); tl = np.arange(L) / SR
    madera = lambda f, g: (np.sin(2 * math.pi * f * tl) * np.exp(-tl / .006) + .5 * sosfilt(butter(2, [1800, 5200], 'band', fs=SR, output='sos'), rng.standard_normal(L)) * np.exp(-tl / .003)) * g
    Lc = int(.6 * SR); tc = np.arange(Lc) / SR
    campana = sum(a * np.sin(2 * math.pi * 2380 * r * tc) * np.exp(-tc / d) for r, a, d in ((1, 1, .35), (2.71, .4, .15), (5.2, .2, .06)))
    for m in defs:
        tic, tac = madera(rng.uniform(820, 980), 1), madera(rng.uniform(640, 760), .85)
        t, k, fin = m['t0'], 0, m['t0'] + m['cuerda']
        while t < min(fin, N / SR - .1):
            u = (t - m['t0']) / m['cuerda']; bpm = m['bpm'] * (1 - .45 * max(0, (u - .8) / .2) ** 1.5)       # el resorte suelta
            i0 = int(t * SR); x = (tic if k % 2 == 0 else tac) * m.get('v', .7) * (1 - .4 * max(0, u - .85) / .15)
            n = min(L, N - i0); y[i0:i0 + n] += _pan(x[:n], m['pan'])
            if m.get('compas') and k % m['compas'] == 0:
                n2 = min(Lc, N - i0); y[i0:i0 + n2] += _pan(campana[:n2] * .25 * m.get('v', .7), m['pan'])
            golpes.append((round(t, 4), m.get('id', 0))); t += 60 / bpm; k += 1
    return y / (np.abs(y).max() + 1e-12), golpes


BANDAS = np.geomspace(55, 7000, 120)


def pintar(trazos, T, FR=100):
    """trazos: [{tipo: 'linea'|'triangulo'|'punto'|'relleno', ...}] en segundos y Hz → imagen (frames × 120)"""
    nf = int(T * FR) + 1; img = np.zeros((nf, len(BANDAS))); lb = np.log(BANDAS)
    def fila(f): return np.interp(np.log(f), lb, np.arange(len(BANDAS)))
    for tr in trazos:
        a = int(tr['t0'] * FR); z = min(nf, int(tr['t1'] * FR)); v = tr.get('v', .6)
        if z <= a: continue
        u = np.linspace(0, 1, z - a)
        if tr['tipo'] == 'linea':                                     # una línea de f0 a f1 (glisando), grosor en bandas
            c = fila(tr['f0']) + (fila(tr['f1']) - fila(tr['f0'])) * u; w = tr.get('ancho', 1.2)
            for i, cc in enumerate(c): img[a + i] += v * np.exp(-((np.arange(len(BANDAS)) - cc) / w) ** 2)
        elif tr['tipo'] == 'triangulo':                               # la pirámide: base ancha abajo que se angosta hacia arriba con el tiempo
            base = fila(tr['f0']); cima = base + (fila(tr['f1']) - base) * u
            for i in range(z - a):
                sel = (np.arange(len(BANDAS)) >= base) & (np.arange(len(BANDAS)) <= cima[i]); img[a + i, sel] += v * (1 - .6 * (np.arange(len(BANDAS))[sel] - base) / max(1, cima[i] - base))
        elif tr['tipo'] == 'punto':                                   # una estrella: un punto que titila
            cc = fila(tr['f0']); img[a:z] += v * np.exp(-((np.arange(len(BANDAS)) - cc) / .7) ** 2)[None, :] * (np.sin(np.pi * u) ** 2)[:, None]
        elif tr['tipo'] == 'relleno':                                 # la luz que lo llena todo (el amanecer), de abajo hacia arriba
            for i in range(z - a):
                top = fila(tr['f0']) + (fila(tr['f1']) - fila(tr['f0'])) * u[i]; img[a + i, np.arange(len(BANDAS)) <= top] += v * u[i] * .5
    return np.clip(img, 0, 1.2)


def linterna(trazos, N, semilla=0, FR=100):
    rng = np.random.default_rng(semilla); T = N / SR; img = pintar(trazos, T, FR)
    t = np.arange(N) / SR; tf = np.arange(img.shape[0]) / FR; y = np.zeros((N, 2))
    for j, f in enumerate(BANDAS):
        col = img[:, j]
        if col.max() < 1e-3: continue
        env = np.interp(t, tf, col); env = np.convolve(env, np.ones(480) / 480, 'same')
        for k, det in enumerate((-.0025, .0025)):                    # el vidrio vibra: dos osciladores apenas desafinados
            y[:, k] += env * np.sin(2 * math.pi * f * (1 + det) * t + rng.uniform(0, 6)) / math.sqrt(f / 55) ** .5
    return y / (np.abs(y).max() + 1e-12), img


def vinilo(curva, N, semilla=0):
    rng = np.random.default_rng(semilla); t = np.arange(N) / SR; d = np.interp(t, [a for a, _ in curva], [b for _, b in curva])
    y = sosfilt(butter(2, [3000, 11000], 'band', fs=SR, output='sos'), rng.standard_normal((N, 2)) * .03, axis=0) * d[:, None]
    for i in np.nonzero(rng.random(N) < d * 25 / SR)[0]:
        L = rng.integers(20, 120)
        if i + L < N: y[i:i + L] += (rng.standard_normal(L) * np.exp(-np.arange(L) / 12) * rng.uniform(.2, 1))[:, None] * np.array([rng.uniform(.5, 1), rng.uniform(.5, 1)])
    return y / (np.abs(y).max() + 1e-12)
