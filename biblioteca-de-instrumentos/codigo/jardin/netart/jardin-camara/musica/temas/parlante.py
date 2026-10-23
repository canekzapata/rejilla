"""Tambor parlante (dùndún): membrana cuyo tono se desliza mientras suena.

Canek: «también había un tambor bonito» (el aro modal de *sombrilla*) y después: «tambor
parlante». En el talking drum yoruba la mano aprieta las cuerdas que tensan los dos
parches: el golpe sube o baja de tono mientras suena, y así el tambor imita una lengua
tonal. Aquí «habla» la escala del choque: cada golpe sale de la altura del anterior y se
desliza a su nota, como sílabas de una frase.

Membrana circular: modos 1, 1.594, 2.136, 2.296, 2.653 y 2.918 (Bessel), con los agudos
apagándose antes. El deslizamiento es exponencial (la mano aprieta y se queda). Golpe con
un chasquido breve de piel y, a veces, apagado con la mano (más corto, más seco).
"""
import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
MODOS = [(1.0, 1.0, 1.0), (1.594, 0.55, 0.6), (2.136, 0.38, 0.45), (2.296, 0.3, 0.4),
         (2.653, 0.18, 0.3), (2.918, 0.12, 0.25)]     # (razón, amplitud, decaimiento relativo)


def golpe(f_desde, f_hasta, rng, vel=1.0, glide=0.07, largo=0.45, apagado=False):
    n = int((largo + 0.05) * SR)
    t = np.arange(n) / SR
    f = f_hasta + (f_desde - f_hasta) * np.exp(-t / glide)
    tau = 0.09 if apagado else 0.28
    x = np.zeros(n)
    fase = 2 * np.pi * np.cumsum(f) / SR
    for r, a, d in MODOS:
        x += a * np.sin(r * fase + rng.uniform(0, 6)) * np.exp(-t / (tau * d))
    sos = butter(2, [1800, 6500], btype="band", fs=SR, output="sos")
    piel = sosfilt(sos, rng.standard_normal(n)) * np.exp(-t / 0.004)
    x += (0.6 if apagado else 0.35) * piel
    return vel * x / 2.0


def registro(f):
    """El tambor habla grave: la nota se lleva a 110–330 Hz."""
    while f > 330:
        f /= 2
    while f < 110:
        f *= 2
    return f


def frase(rng, escala_hz, t0, desde=None, unidad=0.18):
    """Una respuesta de 2 a 6 golpes con ritmo de habla. Devuelve [(t, audio)] y el registro."""
    if not escala_hz:
        return [], []
    alturas = sorted(registro(f) for f in escala_hz)
    k = int(rng.integers(2, 7))
    t = t0
    prev = desde or alturas[int(rng.integers(len(alturas)))]
    i = int(rng.integers(len(alturas)))
    out, notas = [], []
    for j in range(k):
        i = int(np.clip(i + rng.choice([-2, -1, 1, 1, 2]), 0, len(alturas) - 1))
        meta = alturas[i]
        apagado = rng.random() < 0.25
        vel = 0.7 + 0.3 * rng.random() - (0.15 if apagado else 0)
        out.append((t, golpe(prev, meta, rng, vel, glide=rng.uniform(0.03, 0.12), apagado=apagado)))
        notas.append({"t": round(float(t), 3), "desde_hz": round(float(prev), 2), "hasta_hz": round(float(meta), 2),
                      "apagado": bool(apagado)})
        prev = meta
        t += float(rng.choice([0.5, 1, 1, 1.5, 2])) * unidad
    return out, notas


def frase_libre(rng, alturas_hz, t0, desde=None, unidad=0.18):
    """El dùndún con voz propia (Canek: «que tuvieran más libertad y no sólo esperaran
    evento»): frases de 3 a 9 golpes con rubato, un arco de dinámica, sílabas repetidas y,
    a veces, un golpe doble (flam). Habla con las notas que el muro suena en ese momento."""
    if not alturas_hz:
        return [], [], desde
    alturas = sorted({round(registro(f), 3) for f in alturas_hz})
    k = int(rng.integers(3, 10))
    t = t0
    prev = desde or alturas[int(rng.integers(len(alturas)))]
    i = int(np.argmin([abs(np.log2(a / prev)) for a in alturas]))
    arco = str(rng.choice(["crece", "decrece", "monte"]))
    out, notas = [], []
    for j in range(k):
        x = j / max(1, k - 1)
        dinam = {"crece": 0.55 + 0.45 * x, "decrece": 1.0 - 0.45 * x, "monte": 0.55 + 0.45 * np.sin(np.pi * x)}[arco]
        if rng.random() > 0.3:                                    # 3 de cada 10 golpes repiten la sílaba
            i = int(np.clip(i + rng.choice([-2, -1, -1, 1, 1, 2]), 0, len(alturas) - 1))
        meta = alturas[i]
        apagado = rng.random() < 0.3
        vel = dinam * (0.85 + 0.15 * rng.random()) - (0.12 if apagado else 0)
        if rng.random() < 0.12:                                   # flam: un golpe de gracia antes
            out.append((t - 0.025, golpe(prev, prev, rng, vel * 0.45, glide=0.02, largo=0.15, apagado=True)))
        out.append((t, golpe(prev, meta, rng, vel, glide=rng.uniform(0.03, 0.15), apagado=apagado)))
        notas.append({"t": round(float(t), 3), "desde_hz": round(float(prev), 2), "hasta_hz": round(float(meta), 2),
                      "apagado": bool(apagado), "vel": round(float(vel), 2)})
        prev = meta
        t += float(rng.choice([0.5, 1, 1, 1.5, 2, 3])) * unidad * (1 + rng.normal(0, 0.12))   # rubato
    return out, notas, prev
