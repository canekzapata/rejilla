"""El androide en la estación — la estación Sutura y las luciérnagas (sintes propios, 48 kHz).

  impresora(lineas, N)     la impresora de boletos: matriz de 9 agujas. Cada carácter es una columna de golpes de aguja (clics
                           agudos, 2–5 kHz, a ~1.1 kHz de columna); el motor del carro chilla mientras imprime; al final de la
                           línea, el avance de papel (un golpe sordo). Son los hats de la estación.
  torniquete(golpes, N)    el trinquete: seis clics que se frenan en 0.3 s y el golpe del brazo de metal.
  campana(notas, N)        la campana de andén de dos tonos: un tubo de metal (parciales 1, 2.76, 5.40, 8.93) con 2.4 s de cola.
  lluvia(curva, N)         la lluvia sobre la lámina del techo: gotas de Poisson (la densidad sigue `curva`), cada una excita tres
                           modos de una lámina corrugada; debajo, el siseo del agua.
  pulso(tiempos, f, N)     la pantalla de Sutura: «una pulsación cada diecisiete segundos». Un golpe grave en la tónica y el
                           chillido de un tubo de rayos catódicos.
  luciernagas(...)         Kuramoto a 1 kHz: 40 luciérnagas con frecuencia propia cerca del pulso; el acoplamiento K(t) las
                           sincroniza, y la pantalla de Sutura las arrastra (forzamiento). Cada destello es un ping (dos parciales)
                           con la nota que le toca a esa luciérnaga. Devuelve también la coherencia r(t).
"""
import math
import numpy as np
from scipy.signal import butter, sosfilt
SR = 48000


def _bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x)
def _pan(y, p): a = (p + 1) * math.pi / 4; return np.stack([y * math.cos(a), y * math.sin(a)], 1)


def impresora(lineas, N, semilla=0):
    rng = np.random.default_rng(semilla); y = np.zeros((N, 2))
    for ln in lineas:
        i0 = int(ln['t'] * SR); col = SR / ln.get('velocidad', 1100); n = int(ln['chars'] * 7 * col); x = np.zeros(n + SR // 2)
        clic = _bp(rng.standard_normal(96), 2000, 5200) * np.exp(-np.arange(96) / 14)
        for c in range(ln['chars'] * 7):
            if c % 7 == 6: continue                                              # el espacio entre caracteres
            j = int(c * col); agujas = rng.integers(1, 7)
            x[j:j + 96] += clic * (.25 + .12 * agujas) * rng.uniform(.8, 1.2)
        t = np.arange(n) / SR; x[:n] += .05 * np.sin(2 * math.pi * (410 + 30 * np.sin(2 * math.pi * 7 * t)) * t) * np.minimum(1, t / .02)   # el carro
        k = int(.12 * SR); tk = np.arange(k) / SR; x[n:n + k] += .9 * np.sin(2 * math.pi * 95 * tk) * np.exp(-tk / .03) + .3 * _bp(rng.standard_normal(k), 200, 900) * np.exp(-tk / .02)   # avance de papel
        m = min(len(x), N - i0)
        if m > 0: y[i0:i0 + m] += _pan(x[:m] * ln.get('v', .8), ln.get('pan', .3))
    return y / (np.abs(y).max() + 1e-12)


def torniquete(golpes, N, semilla=0):
    rng = np.random.default_rng(semilla); y = np.zeros((N, 2))
    for g in golpes:
        i0 = int(g["t"] * SR); x = np.zeros(int(.7 * SR)); tt = 0.0
        for c in range(6):
            j = int(tt * SR); L = 240; x[j:j + L] += _bp(rng.standard_normal(L), 1500, 6000) * np.exp(-np.arange(L) / 30) * (.9 - .1 * c); tt += .03 + .012 * c
        j = int(tt * SR); L = int(.25 * SR); tk = np.arange(L) / SR
        x[j:j + L] += (np.sin(2 * math.pi * 330 * tk) + .6 * np.sin(2 * math.pi * 811 * tk) + .3 * np.sin(2 * math.pi * 1530 * tk)) * np.exp(-tk / .07) * .6
        m = min(len(x), N - i0)
        if m > 0: y[i0:i0 + m] += _pan(x[:m] * g.get('v', .8), g.get('pan', -.4))
    return y / (np.abs(y).max() + 1e-12)


def campana(notas, N, semilla=0):
    rng = np.random.default_rng(semilla); y = np.zeros((N, 2)); L = int(3.2 * SR); t = np.arange(L) / SR
    for e in notas:
        f = 440 * 2 ** ((e['m'] - 69) / 12); x = np.zeros(L)
        for r_, a, d in ((1, 1, 2.4), (2.76, .5, 1.2), (5.40, .3, .6), (8.93, .15, .3)):
            x += a * np.sin(2 * math.pi * f * r_ * t + rng.uniform(0, 6)) * np.exp(-t / d) * (1 + .02 * np.sin(2 * math.pi * 4.5 * t))
        x *= np.minimum(1, t / .002); i0 = int(e['t'] * SR); m = min(L, N - i0)
        if m > 0: y[i0:i0 + m] += _pan(x[:m] * e.get('v', .7), e.get('pan', 0))
    return y / (np.abs(y).max() + 1e-12)


def lluvia(curva, N, semilla=0):
    rng = np.random.default_rng(semilla); t = np.arange(N) / SR
    dens = np.interp(t, [a for a, _ in curva], [b for _, b in curva]); y = np.zeros((N, 2))
    MODOS = [310, 470, 820, 1240, 1890, 2650, 3700]; L = int(.06 * SR); tl = np.arange(L) / SR
    gotas = rng.random(N) < dens * 60 / SR                                        # hasta 60 gotas por segundo
    for i in np.nonzero(gotas)[0]:
        if i + L >= N: break
        x = sum(rng.uniform(.3, 1) * np.sin(2 * math.pi * f * rng.uniform(.97, 1.03) * tl) * np.exp(-tl / rng.uniform(.006, .02)) for f in rng.choice(MODOS, 3, replace=False))
        y[i:i + L] += _pan(x * rng.uniform(.2, 1), rng.uniform(-.9, .9))
    sis = _bp(rng.standard_normal((N, 2)) * 1.0, 1500, 9000, 1) * dens[:, None] * .4
    y = y + sis
    return y / (np.abs(y).max() + 1e-12)


def pulso(tiempos, f, N, semilla=0):
    y = np.zeros(N); L = int(.6 * SR); t = np.arange(L) / SR
    x = np.sin(2 * math.pi * f * t * (1 + .5 * np.exp(-t / .03))) * np.exp(-t / .25) + .04 * np.sin(2 * math.pi * 7860 * t) * np.exp(-t / .4)
    for tt in tiempos:
        i0 = int(tt * SR); m = min(L, N - i0)
        if m > 0: y[i0:i0 + m] += x[:m]
    return _pan(y / (np.abs(y).max() + 1e-12), 0)


def luciernagas(t0, t1, N, f_pulso, K, notas, forz=None, M=40, semilla=0):
    """K: [[t, múltiplo del umbral]]; forz: [[t, 0–1]] cuánto las arrastra la pantalla (fase del pulso). notas: lista de midis."""
    rng = np.random.default_rng(semilla); FR = 1000; n = int((t1 - t0) * FR); sig = .08
    w = 2 * math.pi * f_pulso * (1 + sig * rng.standard_normal(M)); th = rng.uniform(0, 2 * math.pi, M)
    tt = t0 + np.arange(n) / FR; Kc = 1.6 * sig * 2 * math.pi * f_pulso
    Kt = np.interp(tt, [a for a, _ in K], [b for _, b in K]) * Kc; Ft = np.interp(tt, [a for a, _ in (forz or [[0, 0]])], [b for _, b in (forz or [[0, 0]])]) * Kc
    destellos = []; r = np.zeros(n); nota = rng.choice(notas, M); pan = rng.uniform(-.9, .9, M)
    for i in range(n):
        z = np.exp(1j * th).mean(); r[i] = abs(z); psi = np.angle(z); fase_pulso = 2 * math.pi * f_pulso * tt[i]
        th_n = th + (w + Kt[i] * r[i] * np.sin(psi - th) + Ft[i] * np.sin(fase_pulso - th)) / FR + .25 * rng.standard_normal(M) / math.sqrt(FR)
        cruz = np.nonzero(np.floor(th_n / (2 * math.pi)) > np.floor(th / (2 * math.pi)))[0]
        for k in cruz: destellos.append((tt[i], k))
        th = th_n
    y = np.zeros((N, 2)); L = int(.5 * SR); tl = np.arange(L) / SR
    for (tf, k) in destellos:
        f = 440 * 2 ** ((nota[k] - 69) / 12); x = (np.sin(2 * math.pi * f * tl) + .3 * np.sin(2 * math.pi * f * 3.01 * tl)) * np.minimum(1, tl / .004) * np.exp(-tl / .18)
        i0 = int(tf * SR); m = min(L, N - i0)
        if m > 0: y[i0:i0 + m] += _pan(x[:m] * rng.uniform(.4, 1), pan[k])
    return y / (np.abs(y).max() + 1e-12), tt, r, destellos
