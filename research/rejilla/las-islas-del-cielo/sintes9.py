"""Las islas del cielo — instrumentos propios (48 kHz).

  caida(H)              la física de la cascada que no llega (el Salto Ángel se vuelve niebla antes de tocar el suelo): el chorro
                        cae libre hasta romperse en gotas (inestabilidad de Rayleigh–Plateau; aquí a un 30 % de la pared, h_r), y
                        desde ahí las gotas caen a su velocidad terminal (~9 m/s) y se evaporan. Devuelve los tiempos: t_rompe, t_total.
  cascada(t0, H, f, N)  el sonido de esa caída: 1) LA COLUMNA, un tono (la altura de su isla) con ruido de chorro, que baja una
                        octava mientras acelera; 2) LAS GOTAS, el tono se granula: granos cortos cada vez más espaciados y agudos;
                        3) LA NIEBLA, los granos se vuelven siseo que se apaga antes del suelo. NO hay golpe al final: no llega.
  capachos(ev, N)       las maracas llaneras: semillas dentro de una tapara. Cada sacudida es una nube de choques de Poisson
                        (semillas contra la pared) filtrada por la cáscara (3–7 kHz) y un modo del cuerpo (~700 Hz). El joropo
                        las toca «escobilladas»: un arrastre en cada corchea y un acento al frente.
  tuki(ev, N)           los stabs del changa tuki: acorde de sierras desafinadas, muy corto, con un barrido de filtro que cierra.
  lluvia(curva, N)      la niebla que vuelve como lluvia sobre el llano: gotas de Minnaert pequeñas y un siseo, con densidad que sigue
                        la curva.
"""
import math
import numpy as np
from scipy.signal import butter, sosfilt
SR = 48000
G = 9.81
hz = lambda m: 440.0 * 2 ** ((np.asarray(m, float) - 69) / 12)


def _pan(y, p): a = (p + 1) * math.pi / 4; return np.stack([y * math.cos(a), y * math.sin(a)], 1)
def _bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x)


def caida(H, frac=.3, v_t=9.0):
    h_r = frac * H; t_r = math.sqrt(2 * h_r / G); return t_r, t_r + (H - h_r) / v_t


def cascada(t0, H, f, N, pan=0.0, semilla=0, escala_t=1.0):
    """H en metros; f en Hz. escala_t comprime el tiempo físico (1 = real)."""
    rng = np.random.default_rng(semilla); t_r, t_tot = caida(H); t_r *= escala_t; t_tot *= escala_t
    L = int(t_tot * SR); t = np.arange(L) / SR; y = np.zeros(L)
    # 1) la columna: hasta t_r. El tono baja una octava mientras acelera; el ruido del chorro crece con la velocidad
    col = t < t_r; u = np.clip(t / t_r, 0, 1)
    fc = f * 2 ** (-u); ph = 2 * np.pi * np.cumsum(fc) / SR
    tono = (np.sin(ph) + .3 * np.sin(2 * ph) + .12 * np.sin(3 * ph)) * np.minimum(1, t / .4)
    chorro = _bp(rng.standard_normal(L), 300, 4000) * (.2 + .6 * u)
    y += (tono * .6 + chorro * .5) * col * (1 - .3 * u)
    # 2) las gotas: granos cada vez más espaciados (la columna se deshace), cada uno un seno corto que sube (Minnaert, gotas chicas)
    dur_g = t_tot - t_r; k = t_r
    while k < t_r + .7 * dur_g:
        v = (k - t_r) / dur_g; gl = int((.03 + .05 * rng.random()) * SR); a = int(k * SR)
        if a + gl >= L: break
        tg = np.arange(gl) / SR; fg = f / 2 * 2 ** (rng.uniform(1, 3.5) + 2 * v) * (1 + 3 * tg)
        y[a:a + gl] += np.sin(2 * np.pi * np.cumsum(fg) / SR) * np.exp(-tg / .012) * (1 - v) * .5
        k += rng.exponential(.02 + .25 * v)
    # 3) la niebla: siseo que se agudiza y se apaga antes del suelo (nada al final)
    w = np.clip((t - t_r) / dur_g, 0, 1); niebla = np.sin(np.pi * np.clip(w * 1.25, 0, 1)) ** 2 * (w > 0) * (1 - w) ** 1.5
    y += _bp(rng.standard_normal(L), 2500, 11000) * niebla * .35
    out = np.zeros((N, 2)); a = int(t0 * SR); m = min(L, N - a)
    if m > 0: out[a:a + m] = _pan(y[:m], pan)
    return out, dict(H=H, t_rompe=round(t_r, 2), t_total=round(t_tot, 2), energia_ultimo_10pc=float(np.sqrt(np.mean(y[int(.9 * L):] ** 2)) / (np.sqrt(np.mean(y[:int(.3 * L)] ** 2)) + 1e-12)))


def capachos(eventos, N, semilla=0):
    """eventos: {t, dur, v, pan}: cada uno, una sacudida (arrastre de semillas)."""
    rng = np.random.default_rng(semilla); y = np.zeros((N, 2)); L = int(.25 * SR)
    for e in eventos:
        a = int(e['t'] * SR); d = e.get('dur', .12); n = int(d * SR) + int(.05 * SR)
        if a + n >= N: continue
        tt = np.arange(n) / SR; env = np.clip(tt / .006, 0, 1) * np.exp(-np.clip(tt - d * .6, 0, None) / .02)
        choques = (rng.random(n) < (900 / SR) * (.3 + env)) * rng.uniform(.3, 1, n)
        s = _bp(choques * env, 3000, 7500) + .25 * _bp(choques * env, 600, 850)
        y[a:a + n] += _pan(s * e.get('v', .6), e.get('pan', 0))
    return y / (np.abs(y).max() + 1e-12)


def tuki(eventos, N, semilla=0):
    """eventos: {t, notas: [midi], dur, v}."""
    rng = np.random.default_rng(semilla); y = np.zeros((N, 2))
    for e in eventos:
        a = int(e['t'] * SR); d = e.get('dur', .12); n = int((d + .06) * SR)
        if a + n >= N: continue
        tt = np.arange(n) / SR; s = np.zeros(n)
        for m in e['notas']:
            for det in (-.008, 0, .009):
                f = float(hz(m)) * (1 + det); s += 2 * ((tt * f + rng.random()) % 1) - 1
        env = np.clip(tt / .002, 0, 1) * np.exp(-tt / (d * .6))
        fc = 600 + 5000 * np.exp(-tt / .05); out = np.zeros(n); zi = np.zeros((1, 2)); B = 256
        for i in range(0, n, B):
            j = min(n, i + B); sos = butter(2, float(fc[i]), 'low', fs=SR, output='sos'); out[i:j], zi = sosfilt(sos, s[i:j] * env[i:j], zi=zi)
        y[a:a + n] += _pan(np.tanh(1.5 * out / (len(e['notas']) * 3)), e.get('pan', 0)) * e.get('v', .7)
    return y / (np.abs(y).max() + 1e-12)


def lluvia(curva, N, semilla=0):
    rng = np.random.default_rng(semilla); t = np.arange(N) / SR; d = np.interp(t, [a for a, _ in curva], [b for _, b in curva])
    y = np.zeros((N, 2)); L = int(.04 * SR); tl = np.arange(L) / SR
    for i in np.nonzero(rng.random(N) < d * 60 / SR)[0]:
        if i + L >= N: continue
        r = rng.uniform(.6, 2.2) / 1000; f0 = 3.26 / r; dd = .13 / r * 1e-3 + .0072 * r ** -1.5 * 1e-3
        g = np.sin(2 * np.pi * np.cumsum(f0 * (1 + .1 * dd * tl * 1000)) / SR) * np.exp(-tl * dd * 400)
        y[i:i + L] += _pan(g * rng.uniform(.2, 1), rng.uniform(-.9, .9))
    y += np.stack([_bp(rng.standard_normal(N), 3000, 9000), _bp(rng.standard_normal(N), 3000, 9000)], 1) * d[:, None] * .02
    return y / (np.abs(y).max() + 1e-12)
