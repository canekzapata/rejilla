"""¿Por quién se toma la tierra? — sintes propios.

  magma(tramos, N)    Scelsi: una nota que se pudre por dentro. Cada tramo es una edad del volcán con su bordón (f del relieve); entre
                      tramos la altura se desliza (30 s de glisando microtonal: la tierra no salta). Encima: batidos de dos copias a ±3
                      cents, un cuarto de tono que respira, armónicos que se encienden y apagan despacio (el timbre se mueve, la nota no)
  estratos(ev, N)     dub techno: cada acorde es un estrato — un golpe de pulso filtrado (arenisca: el filtro abre; esquisto: cerrado y
                      grave) que entra a un eco de cinta (3/8 de compás, retroalimentado, filtrado y saturado): las capas se apilan
  bajo_dub(notas, N)  seno con un poco de segundo armónico, ataque suave y saturación: el bajo de dub, abajo de 100 Hz
  avalancha(t0,t1,N)  el flanco que se cae: ruido rosa que crece y se oscurece, con golpes de bloques (ráfagas cortas)
"""
import math
import numpy as np
from scipy.signal import butter, sosfilt
SR = 48000
hz = lambda m: 440.0 * 2 ** ((np.asarray(m, float) - 69) / 12)


def magma(tramos, N, semilla=0):
    rng = np.random.default_rng(semilla); t = np.arange(N) / SR
    # la altura: escalones de edad unidos por glisandos de 30 s (empiezan antes de cada edad)
    f = np.full(N, tramos[0]['f'])
    for a, b in zip(tramos, tramos[1:]):
        t0 = b['t'] - 15; u = np.clip((t - t0) / 30, 0, 1); u = u * u * (3 - 2 * u)
        f = np.where(t >= t0, a['f'] * (b['f'] / a['f']) ** u, f)
    resp = 1 + (2 ** (25 / 1200) - 1) * np.sin(2 * np.pi * t / 11.3) * .5                 # un cuarto de tono que respira (±12 cents)
    y = np.zeros(N)
    for det in (-3, 0, 3):
        ph = 2 * np.pi * np.cumsum(f * resp * 2 ** (det / 1200)) / SR + rng.uniform(0, 6)
        for k in range(1, 14):
            if (f.max() * k) > 6000: break
            mov = .5 + .5 * np.sin(2 * np.pi * t / (7 + 3.1 * k) + rng.uniform(0, 6))       # cada armónico se enciende y se apaga
            y += (1 / k ** .9) * mov ** (1 + k / 4) * np.sin(k * ph)
    env = np.minimum(1, t / 6) * np.minimum(1, (t[-1] - t) / 4)
    return y * env / (np.abs(y * env).max() + 1e-12)


def estratos(ev, N, compas, semilla=0):
    rng = np.random.default_rng(semilla); seco = np.zeros(N)
    for e in ev:
        i0 = int(e['t'] * SR); n = min(N - i0, int(.45 * SR)); t = np.arange(n) / SR; x = np.zeros(n)
        for m in e['notas']:
            f = float(hz(m))
            for k in range(1, int(5000 / f)):
                x += (1 / k) * (1.3 if k % 2 else .8) * np.sin(2 * np.pi * f * k * t + rng.uniform(0, 6))
        corte = 2600 if e['capa'] == 'A' else 700
        x = sosfilt(butter(2, corte, 'low', fs=SR, output='sos'), x) * np.exp(-t / (.09 if e['capa'] == 'A' else .14)) * e['v']
        seco[i0:i0 + n] += x
    seco /= np.abs(seco).max() + 1e-12
    # el eco de cinta: 3/8 de compás, retroalimentado .62, cada vuelta más oscura y saturada (estéreo: izquierda y derecha alternan)
    d = int(compas * 3 / 8 * SR); L = seco.copy(); Rr = seco.copy() * .7; vuelta = seco.copy()
    for j in range(1, 9):
        vuelta = np.concatenate([np.zeros(d), vuelta[:-d]]) * .62
        vuelta = np.tanh(1.3 * sosfilt(butter(1, max(400, 2600 - 280 * j), 'low', fs=SR, output='sos'), vuelta))
        (L if j % 2 else Rr)[:] += vuelta
    out = np.stack([L, Rr], 1); return out / (np.abs(out).max() + 1e-12)


def bajo_dub(notas, N, semilla=0):
    y = np.zeros(N)
    for nt in notas:
        i0 = int(nt['t'] * SR); n = min(N - i0, int((nt['dur'] + .08) * SR)); t = np.arange(n) / SR; f = float(hz(nt['m']))
        while f > 100: f /= 2
        env = np.minimum(1, t / .012) * np.where(t < nt['dur'], 1, np.exp(-(t - nt['dur']) / .03))
        x = np.sin(2 * np.pi * f * t) + .25 * np.sin(4 * np.pi * f * t)
        y[i0:i0 + n] += np.tanh(1.4 * x * env * nt['v'])
    return y / (np.abs(y).max() + 1e-12)


def avalancha(t0, t1, N, semilla=0):
    rng = np.random.default_rng(semilla); i0, i1 = int(t0 * SR), min(N, int(t1 * SR)); n = i1 - i0; t = np.arange(n) / SR; T = t1 - t0
    w = rng.standard_normal(n); rosa = sosfilt(butter(1, 800, 'low', fs=SR, output='sos'), w)
    oscuro = np.zeros(n)
    for k, (a, b) in enumerate(((0, .35), (.35, .7), (.7, 1.01))):              # se oscurece mientras cae
        j0, j1 = int(a * n), int(min(1, b) * n)
        oscuro[j0:j1] = sosfilt(butter(2, [2000, 600, 180][k], 'low', fs=SR, output='sos'), rosa)[j0:j1]
    env = np.minimum(1, t / (T * .2)) * np.minimum(1, (T - t) / (T * .35))
    y = np.zeros(N); y[i0:i1] = oscuro * env
    for _ in range(40):                                                            # los bloques que golpean
        j = rng.integers(i0, i1 - 4800); L = rng.integers(800, 4800); y[j:j + L] += sosfilt(butter(2, rng.uniform(80, 400), 'low', fs=SR, output='sos'), rng.standard_normal(L)) * np.exp(-np.arange(L) / (L / 4)) * rng.uniform(.5, 2)
    return y / (np.abs(y).max() + 1e-12)
