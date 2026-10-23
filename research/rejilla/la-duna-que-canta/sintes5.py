"""La duna que canta — sintes propios.

  qraqeb(golpes, N)   las castañuelas de hierro de los gnawa: dos pares de placas cóncavas atadas que chocan. Cada golpe son dos
                      choques casi juntos (el flam de 6–14 ms entre las dos placas), ruido por un banco de modos inarmónicos de placa
                      (2.1, 3.4, 4.9, 6.6, 8.3 kHz; cada par un poco desafinado del otro) que se apagan en 25–60 ms. Estéreo por golpe.
"""
import math
import numpy as np
from scipy.signal import butter, sosfilt
SR = 48000
MODOS = [2100, 3400, 4900, 6600, 8300]


def qraqeb(golpes, N, semilla=0):
    rng = np.random.default_rng(semilla); y = np.zeros((N, 2)); n = int(.09 * SR); t = np.arange(n) / SR
    pares = [[f * rng.uniform(.97, 1.03) for f in MODOS] for _ in range(2)]
    for g in golpes:
        i0 = int(g['t'] * SR); x = np.zeros(n + int(.016 * SR))
        for k, par in enumerate(pares):
            off = 0 if k == 0 else int(rng.uniform(.006, .014) * SR); a = g['v'] * (1 if k == 0 else rng.uniform(.5, .8))
            for j, f in enumerate(par):
                dec = rng.uniform(.025, .06) / (1 + .3 * j)
                x[off:off + n] += a * np.sin(2 * math.pi * f * t + rng.uniform(0, 6)) * np.exp(-t / dec) * (1 / (1 + .4 * j))
            x[off:off + 240] += a * .8 * rng.standard_normal(240) * np.exp(-np.arange(240) / 40)     # el clic del choque
        m = min(len(x), N - i0)
        if m <= 0: continue
        p = (g.get('pan', 0) + rng.uniform(-.15, .15) + 1) * math.pi / 4
        y[i0:i0 + m, 0] += x[:m] * math.cos(p); y[i0:i0 + m, 1] += x[:m] * math.sin(p)
    y = sosfilt(butter(2, 900, 'high', fs=SR, output='sos'), y, axis=0)
    return y / (np.abs(y).max() + 1e-12)
