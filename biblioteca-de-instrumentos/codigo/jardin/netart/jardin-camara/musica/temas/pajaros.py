"""Pájaros que contestan al agua.

Canek, sobre las gemelas de día: «es mucho más espacial, raro, como lo que podríamos estar
buscando; cuando resuena el instrumento de agua ¿puede también resonar pájaros? o algo que
tenga el slide de las notas».

Un pájaro aquí es un tono casi puro (con un poco de 2.º armónico) cuya altura dibuja un
gesto. Las alturas son la escala del choque llevada al registro de los pájaros (1.2–4.5 kHz):
  silbido   se desliza lento de una nota a otra (subiendo o bajando), 0.2–0.5 s
  trino     alterna dos notas vecinas muy rápido (12–22 Hz), 0.3–0.8 s
  gorjeo    3–7 chirridos cortos que suben, cada uno a otra nota
  llamado   dos notas con un salto y una caída final (como un «tiu-iii»)

Cantan lejos (poca ganancia, mucha sala, sin agudos de más) y a veces un segundo pájaro
contesta desde el otro lado. Messiaen escribió pájaros para las ondas Martenot, y el
trautonium hizo los de Hitchcock: son de la familia.
"""
import numpy as np

SR = 48000


def registro(f, lo=1200, hi=4500):
    while f < lo:
        f *= 2
    while f > hi:
        f /= 2
    return f


def lejos(x, fc=3000):
    """El aire se come los agudos de un pájaro lejano: pasabajos de un polo."""
    from scipy.signal import lfilter
    a = np.exp(-2 * np.pi * fc / SR)
    return lfilter([1 - a], [1, -a], x)


def _tono(fc, amp):
    """fc: frecuencia instantánea (array), amp: envolvente (array)."""
    fase = 2 * np.pi * np.cumsum(fc) / SR
    return amp * (np.sin(fase) + 0.12 * np.sin(2 * fase + 0.5))


def gesto(rng, notas):
    tipo = str(rng.choice(["silbido", "trino", "gorjeo", "llamado"], p=[0.35, 0.25, 0.25, 0.15]))
    a, b = (float(x) for x in rng.choice(notas, 2, replace=len(notas) < 2))
    if tipo == "silbido":
        d = rng.uniform(0.2, 0.5)
        n = int(d * SR)
        t = np.linspace(0, 1, n)
        fc = a * (b / a) ** (t ** rng.uniform(0.6, 1.6))
        amp = np.sin(np.pi * t) ** 0.7
        x = _tono(fc, amp)
    elif tipo == "trino":
        d = rng.uniform(0.3, 0.8)
        n = int(d * SR)
        t = np.arange(n) / SR
        vel = rng.uniform(12, 22)
        cuad = 0.5 + 0.5 * np.tanh(4 * np.sin(2 * np.pi * vel * t))   # alterna con un poco de pendiente
        fc = a * (b / a) ** cuad
        amp = np.sin(np.pi * t / d) ** 0.5 * (0.6 + 0.4 * cuad)
        x = _tono(fc, amp)
    elif tipo == "gorjeo":
        partes = []
        for k in range(int(rng.integers(3, 8))):
            f = float(rng.choice(notas))
            d = rng.uniform(0.03, 0.08)
            n = int(d * SR)
            t = np.linspace(0, 1, n)
            fc = f * (0.8 + 0.3 * t)                                     # chirrido que sube
            partes.append(_tono(fc, np.sin(np.pi * t) ** 0.6))
            partes.append(np.zeros(int(rng.uniform(0.02, 0.07) * SR)))
        x = np.concatenate(partes)
    else:
        n1, n2 = int(0.12 * SR), int(0.3 * SR)
        t1, t2 = np.linspace(0, 1, n1), np.linspace(0, 1, n2)
        x = np.concatenate([_tono(np.full(n1, a), np.sin(np.pi * t1)),
                            np.zeros(int(0.05 * SR)),
                            _tono(b * (1 - 0.12 * t2 ** 2), np.sin(np.pi * t2) ** 0.6)])
    return tipo, x


def cantar(rng, escala_hz, t0, lo=1200, hi=4500, corte=None):
    """Uno o dos pájaros. Devuelve [(t, audio, pan)] y el registro de lo cantado.
    v1.4: registro (lo, hi) y `corte` (Hz) para cantar más lejos."""
    notas = sorted({round(registro(f, lo, hi), 3) for f in escala_hz})
    if not notas:
        return [], []
    out, reg = [], []
    pan = float(rng.choice([-1, 1]) * rng.uniform(0.4, 0.95))
    t = t0
    for vuelta in range(int(rng.integers(1, 3))):
        tipo, x = gesto(rng, notas)
        out.append((t, x * rng.uniform(0.6, 1.0), pan))
        reg.append({"t": round(float(t), 3), "tipo": tipo, "pan": round(pan, 2)})
        t += len(x) / SR + rng.uniform(0.15, 0.6)
    if rng.random() < 0.4:                                           # otro pájaro contesta del otro lado
        tipo, x = gesto(rng, notas)
        out.append((t + rng.uniform(0.1, 0.4), x * rng.uniform(0.4, 0.7), -pan))
        reg.append({"t": round(float(t), 3), "tipo": tipo, "pan": round(-pan, 2), "contesta": True})
    if corte:
        out = [(t, lejos(x, corte), p) for t, x, p in out]
    return out, reg
