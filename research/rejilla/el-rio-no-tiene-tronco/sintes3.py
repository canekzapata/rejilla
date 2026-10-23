"""El río no tiene tronco — sintes propios (los de las otras piezas se importan de ../cuento-en-siete/sintes.py y
../lo-que-tapa-la-traspuesta/sintes2.py).

  arpa(notas, N)      cuerda pulsada aditiva: parciales k con amplitud sin(kπp)/k² (p = dónde se pulsa), cada uno se apaga más
                      rápido cuanto más agudo, con un poco de inarmonía (cuerda de tripa) y el golpe del dedo; altura exacta (los
                      microtonos del monocordio importan)
  armonio(eventos, N) lengüetas libres: muchos armónicos impares y pares, el fuelle que respira (2–4 s), un poco de desafinación
                      entre dos lengüetas (el batido del armonio)
  tambura(eventos, N) el jawari: cada cuerda pulsada florece (los armónicos agudos crecen después del golpe, por el puente plano)
                      y zumba; patrón de cuatro cuerdas que no para
  mar(voces, N)       Scelsi: cada voz llega deslizándose a la nota del mar y se queda, desviada dev(t) = dev0·e^(−t/τ) cents (τ = lo que le queda / 4.5) más
                      una oscilación lenta de un cuarto de tono que también se cierra; arco (ruido de crin) y una vocal que la
                      forma (formantes que se mueven a, o, u): una sola nota que se mueve por dentro
"""
import math
import numpy as np
from scipy.signal import butter, sosfilt
SR = 48000
hz = lambda m: 440.0 * 2 ** ((np.asarray(m, float) - 69) / 12)


def arpa(notas, N, semilla=0):
    y = np.zeros(N); rng = np.random.default_rng(semilla)
    for nt in notas:
        i0 = int(nt['t'] * SR); f = float(hz(nt['m'])); dur = max(1.2, min(4.5, 2.2 + 300 / f)) ; n = min(N - i0, int(dur * SR))
        if n <= 0: continue
        t = np.arange(n) / SR; x = np.zeros(n); p = .13 + .05 * rng.random()
        for k in range(1, 30):
            fk = f * k * math.sqrt(1 + .00012 * k * k)
            if fk > 12000: break
            a = abs(math.sin(k * math.pi * p)) / k ** 1.6
            x += a * np.exp(-t * (1.2 + .55 * k) * (f / 220) ** .35) * np.sin(2 * np.pi * fk * t + rng.uniform(0, 6))
        x[:int(.004 * SR)] += rng.standard_normal(int(.004 * SR)) * .15 * np.linspace(1, 0, int(.004 * SR))   # la uña
        y[i0:i0 + n] += x * nt['v']
    return y / (np.abs(y).max() + 1e-12)


def armonio(eventos, N, semilla=0):
    y = np.zeros(N); rng = np.random.default_rng(semilla)
    for e in eventos:
        i0 = int(e['t'] * SR); n = min(N - i0, int(e['dur'] * SR)); t = np.arange(n) / SR
        fuelle = .7 + .3 * np.sin(2 * np.pi * t / 3.1 + rng.uniform(0, 6)) ** 2
        env = np.minimum(1, t / 2.5) * np.minimum(1, (e['dur'] - t) / 2) * fuelle
        x = np.zeros(n)
        for m in e['notas']:
            f = float(hz(m))
            for det in (-3.5, 3.5):                       # dos lengüetas: baten
                fd = f * 2 ** (det / 1200)
                for k in range(1, int(5000 / f)):
                    x += (1 / k ** 1.1) * (1.4 if k % 2 else 1) * np.sin(2 * np.pi * fd * k * t + rng.uniform(0, 6))
        y[i0:i0 + n] += x * env * e['v']
    return y / (np.abs(y).max() + 1e-12)


def tambura(eventos, N, semilla=0):
    y = np.zeros(N); rng = np.random.default_rng(semilla)
    for e in eventos:
        f0 = float(hz(e['m'])); i = 0; t0 = e['t']; k = 0
        while t0 < e['t'] + e['dur']:
            f = f0 * e['patron'][k % 4] / 4; i0 = int(t0 * SR); n = min(N - i0, int(3.4 * SR)); t = np.arange(n) / SR; x = np.zeros(n)
            for h in range(1, int(6000 / f)):
                flor = (1 - np.exp(-t / (.08 + .02 * h))) if h > 3 else 1      # el jawari: los agudos florecen después
                x += (1 / h ** .8) * flor * np.exp(-t * (.6 + .05 * h)) * np.sin(2 * np.pi * f * h * t + rng.uniform(0, 6))
            y[i0:i0 + n] += x * .5; t0 += 1.15; k += 1
    return y / (np.abs(y).max() + 1e-12)


FORM = dict(a=(800, 1200, 2500), o=(500, 880, 2400), u=(330, 780, 2300), e=(450, 1900, 2550), i=(300, 2200, 2950))


def mar(voces, N, semilla=0):
    """estéreo: cada voz en su lugar (el pan de su brazo)"""
    L = np.zeros(N); Rr = np.zeros(N); rng = np.random.default_rng(semilla)
    for k, v in enumerate(voces):
        i0 = int(v['t'] * SR); n = min(N - i0, int(v['dur'] * SR)); t = np.arange(n) / SR
        glis = np.clip(t / 2.0, 0, 1); glis = glis * glis * (3 - 2 * glis)
        tau = v['dur'] / 4.5                                  # cada voz se cierra en el tiempo que le queda (con τ fijo de 9 s los últimos brazos llegaban al final batiendo)
        cents = v['dev0'] * np.exp(-t / tau) + 25 * np.exp(-t / (tau * .8)) * np.sin(2 * np.pi * t / (5.5 + k) + k)   # el cuarto de tono que respira y se cierra
        m = v['desde'] * (1 - glis) + v['m'] * glis + cents / 100
        f = hz(m); ph = 2 * np.pi * np.cumsum(f) / SR
        # la vocal se mueve por dentro: de la suya a la siguiente, despacio
        orden = ['a', 'o', 'u', 'o', 'a']; vo = [FORM[orden[(k + j) % 5]] for j in range(3)]
        u = np.clip(t / max(1, v['dur']), 0, 1) * 2; j0 = np.minimum(1, u.astype(int)); fr = u - j0
        x = np.zeros(n)
        for h in range(1, int(6000 / float(f.mean()))):
            fh = f * h; amp = np.zeros(n)
            for q in range(3):
                Fq = np.array([vo[0][q], vo[1][q], vo[2][q]])
                c = Fq[j0] * (1 - fr) + Fq[np.minimum(2, j0 + 1)] * fr
                amp += np.exp(-((fh - c) / (60 + 40 * q)) ** 2) * [1, .6, .35][q]
            x += (amp + .08 / h) * np.sin(h * ph + rng.uniform(0, 6))
        crin = sosfilt(butter(2, [float(f.mean()) * 2, float(f.mean()) * 8], 'band', fs=SR, output='sos'), rng.standard_normal(n)) * .05   # el arco
        env = np.minimum(1, t / 1.5) * np.minimum(1, (v['dur'] - t) / 4)
        z = (x + crin) * env; a = (v['pan'] + 1) * math.pi / 4
        L[i0:i0 + n] += z * math.cos(a); Rr[i0:i0 + n] += z * math.sin(a)
    pk = max(np.abs(L).max(), np.abs(Rr).max()) + 1e-12
    return np.stack([L / pk, Rr / pk], 1)
