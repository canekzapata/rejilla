"""Tocar el agua: gotas-burbuja afinadas a la escala del choque.

Canek, sobre lo opuesto a la serie nocturna («densa, trepidante, triste»): «como si tocaras
el agua y salieran chispas de todos colores; esto es como nocturno y siniestro».

Una gota que cae en agua suena por la burbuja que atrapa: una resonancia casi senoidal
que se apaga en decenas de milisegundos y SUBE de tono mientras se apaga (la burbuja
sube a la superficie; modelo de Minnaert y de van den Doel). No es una campanita: es corta,
con chirrido hacia arriba, y cada gota es distinta.

Una salpicadura son 5–12 gotas:
  - alturas de la escala del choque, subidas 1–3 octavas; algunas son un parcial (3.º, 5.º
    o 7.º) de la nota: el color sale de la serie armónica;
  - tiempos de rebote: la primera enseguida y luego intervalos que se alargan;
  - cada gota en otro lugar del estéreo (pan), con tamaño propio (decaimiento y chirrido);
  - anillos: dos o tres ecos más suaves y más oscuros, como las ondas que se abren.
"""
import numpy as np
from scipy.signal import lfilter

SR = 48000


def salpicar(rng, escala_hz, fuentes, t0, n_rango=(5, 13), octavas=(1, 1, 2, 2, 3)):
    if not escala_hz:
        return []
    n = int(rng.integers(*n_rango))
    gotas = []
    t = t0
    dt = rng.uniform(0.03, 0.06)
    for k in range(n):
        i = int(rng.integers(len(escala_hz)))
        f = escala_hz[i] * 2 ** int(rng.choice(list(octavas)))
        if rng.random() < 0.25:                         # chispa: un parcial de la nota
            f = escala_hz[i] * int(rng.choice([3, 5, 7]))
        while f > 5000:
            f /= 2
        tam = rng.uniform(0, 1)                          # 0 gota chica, 1 gota grande
        gotas.append({"t": float(t), "f": float(f), "fuente": fuentes[i],
                      "tau": float(0.012 + 0.05 * tam), "chirp": float(rng.uniform(0.15, 0.6)),
                      "amp": float(rng.uniform(0.45, 1.0) * (1 - 0.5 * k / n)),
                      "pan": float(rng.uniform(-1, 1)), "anillos": int(rng.integers(1, 4))})
        t += dt
        dt *= rng.uniform(1.1, 1.45)                     # los rebotes se espacian
    return gotas


def burbuja(g, rng):
    """Una gota con sus anillos."""
    tau = g["tau"]
    n = int((tau * 7 + 0.6) * SR)
    t = np.arange(n) / SR
    f = g["f"] * (1 + g["chirp"] * np.minimum(t, 4 * tau) / tau / 4)   # sube mientras se apaga
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / tau) * (1 - np.exp(-t / 0.0012))
    x *= g["amp"]
    out = x.copy()
    y = x
    for r in range(g["anillos"]):                        # ondas que se abren: eco más suave y oscuro
        y = lfilter([0.35], [1, -0.65], y)
        d = int((0.09 + 0.07 * r + rng.uniform(0, 0.03)) * SR)
        if d < n:
            out[d:] += 0.5 ** (r + 1) * y[: n - d]
    return out


def canto(a, b, separacion, rng, vel=0.8):
    """El agua devuelve, cantabile, la huella de una frase: dos notas ligadas que se deslizan
    de una a otra, con resonancia larga (Canek: «un poco más cantabile»), y dos o tres gotas
    chicas alrededor. a, b en Hz; separacion = tiempo entre sus ataques en la frase (s)."""
    for f in (a, b):
        pass
    while a < 500:
        a *= 2
    while b < 500:
        b *= 2
    sep = float(np.clip(separacion, 0.3, 1.6))
    dur = sep + 1.4
    n = int(dur * SR)
    t = np.arange(n) / SR
    tr = np.clip((t - sep * 0.6) / (sep * 0.5), 0, 1)
    f = a * (b / a) ** (tr * tr * (3 - 2 * tr))                   # se desliza de a hacia b
    f = f * (1 + 0.03 * np.exp(-t / 0.05))                         # la burbuja: un chirrido al nacer
    amp = (1 - np.exp(-t / 0.02)) * np.exp(-t / (dur * 0.45)) * (1 + 0.4 * np.exp(-((t - sep) / 0.08) ** 2))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * amp
    x += 0.18 * np.sin(2 * np.pi * np.cumsum(2 * f) / SR) * amp * np.exp(-t / 0.3)
    for k in range(int(rng.integers(2, 4))):                      # gotas chicas alrededor
        g = {"t": 0, "f": float(b * rng.choice([2, 3])), "tau": float(rng.uniform(0.01, 0.025)),
             "chirp": float(rng.uniform(0.2, 0.5)), "amp": float(rng.uniform(0.15, 0.3)), "pan": 0.0, "anillos": 1}
        y = burbuja(g, rng)
        i = int(rng.uniform(0.1, dur * 0.8) * SR)
        m = min(len(y), n - i)
        if m > 0:
            x[i:i + m] += y[:m]
    return vel * x


def arpa(rng, escala_hz, fuentes, t0, sube=True):
    """Agua arpa: las gotas caen EN ESCALA (la del choque, una o dos octavas arriba), rápidas
    y parejas, barriendo el estéreo, como un glissando de arpa hecho de burbujas.
    Canek: escalas «estilo arpa, rápidas», por la belleza del movimiento."""
    if not escala_hz:
        return []
    pares = sorted(zip(escala_hz, fuentes))
    notas = [(f * 2 ** o, fu) for o in (1, 2) for f, fu in pares]
    notas = [(f, fu) for f, fu in notas if f <= 4500]
    k = int(rng.integers(8, 15))
    if len(notas) > k:
        i0 = int(rng.integers(0, len(notas) - k + 1))
        notas = notas[i0:i0 + k]
    if not sube:
        notas = notas[::-1]
    dt = float(rng.uniform(0.045, 0.07))
    gotas = []
    for j, (f, fu) in enumerate(notas):
        x = j / max(1, len(notas) - 1)
        gotas.append({"t": float(t0 + j * dt * (1 + 0.08 * rng.normal())), "f": float(f), "fuente": fu,
                      "tau": float(rng.uniform(0.03, 0.05)), "chirp": 0.25,
                      "amp": float(0.5 + 0.4 * np.sin(np.pi * x)), "pan": float((2 * x - 1) * (0.8 if sube else -0.8)),
                      "anillos": 1})
    return gotas
