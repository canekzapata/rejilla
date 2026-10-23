"""Escalas del choque: el comentario recorre la escala que forman, en ese momento, las
voces de las dos familias que están chocando, leída a través de una «lente» de alguna
tradición.

Canek: «las escalas que se generan con los choques son bellas»; «pueden ser cosas raras,
combinaciones de escalas etíopes con contemporáneo jazz o tradiciones indo-pakistaníes».

Cómo:
  1. Poza: las 8 voces que suenan (27.5·n arriba, 3300/m abajo), en todas sus octavas
     de 300 a 1300 Hz, más su gemela de la otra familia.
  2. Lente: una plantilla en cents (qenet, modo de jazz, esqueleto de raga) sobre una
     tónica sacada de la poza. Cada grado se AFINA a la nota de la poza más cercana
     (±70 c); si no hay, a la red de las dos familias (n, m ≤ 24, ±45 c); si tampoco, el
     grado se queda vacío. Así la forma viene de la tradición y la afinación del choque.
  3. Híbrida: los grados de abajo (< 650 c) de una tradición y los de arriba de otra.
  4. Gramática de frase propia de cada lente, con largo de 1 a 6 notas, silencios y
     arranques desplazados; sin octava automática.

Las plantillas son aproximaciones en 12 partes para ubicar la forma; la afinación final
nunca es temperada.
"""
import numpy as np

F0, FU = 27.5, 3300.0

LENTES = {
    "etiope": {   # qenet (Kebede; Abate): pentatónicos, con los dos «menores» de semitono
        "tizita mayor": [0, 200, 400, 700, 900],
        "tizita menor": [0, 200, 300, 700, 800],
        "bati mayor": [0, 400, 500, 700, 1100],
        "bati menor": [0, 300, 500, 700, 1000],
        "ambassel": [0, 100, 500, 700, 800],
        "anchihoye": [0, 100, 500, 600, 900],
    },
    "jazz": {     # simétricas y modos de la menor melódica; Monk vive en tonos enteros
        "tonos enteros": [0, 200, 400, 600, 800, 1000],
        "disminuida st-t": [0, 100, 300, 400, 600, 700, 900, 1000],
        "lidia dominante": [0, 200, 400, 600, 700, 900, 1000],
        "alterada": [0, 100, 300, 400, 600, 800, 1000],
        "cuartas": [0, 500, 1000, 300, 800],
    },
    "indostani": {   # esqueletos de raga (thaat + omisiones); el movimiento va en la gramática
        "bhairav": [0, 100, 400, 500, 700, 800, 1100],
        "todi": [0, 100, 300, 600, 700, 800, 1100],
        "marwa": [0, 100, 400, 600, 900, 1100],
        "yaman": [0, 200, 400, 600, 700, 900, 1100],
        "bhairavi": [0, 100, 300, 500, 700, 800, 1000],
    },
    # claras (serie v1, gemelas «de día»): mayores, lidias, pentatónicas luminosas
    "etiope-clara": {
        "tizita mayor": [0, 200, 400, 700, 900],
        "bati mayor": [0, 400, 500, 700, 1100],
    },
    "jazz-clara": {
        "lidia": [0, 200, 400, 600, 700, 900, 1100],
        "lidia dominante": [0, 200, 400, 600, 700, 900, 1000],
        "tonos enteros": [0, 200, 400, 600, 800, 1000],
    },
    "indostani-clara": {
        "yaman": [0, 200, 400, 600, 700, 900, 1100],
        "bilawal": [0, 200, 400, 500, 700, 900, 1100],
        "hamsadhwani": [0, 200, 400, 700, 1100],
    },
}


def red():
    """Todas las notas de las dos familias (n, m ≤ 24) en el registro del comentario."""
    out = []
    for fam, gen in (("O", lambda k: F0 * k), ("U", lambda k: FU / k)):
        for k in range(1, 25):
            f = gen(k)
            while f < 300:
                f *= 2
            while f > 1300:
                f /= 2
            while f <= 1300:
                out.append((f, f"{fam}{k}"))
                f *= 2
    return out


RED = red()


def poza(arriba, abajo, gemela):
    """Las voces que suenan, en sus octavas de 300–1300 Hz, más sus gemelas."""
    out = []
    for fam, notas in (("O", [(F0 * n, n) for n in arriba]), ("U", [(FU / m, m) for m in abajo])):
        for f, k in notas:
            while f < 300:
                f *= 2
            while f <= 1300:
                out.append((f, f"{fam}{k}"))
                g = gemela(f)
                if g:
                    out.append((g[0], f"gemela de {fam}{k}"))
                f *= 2
    return out


def afinar(tonica, plantilla, pz):
    """Grado a grado: la nota de la poza más cercana; si no, de la red; si no, vacío."""
    escala = []
    for c in plantilla:
        meta = tonica * 2 ** ((c % 1200) / 1200)
        mejor = None
        for fuente, tol, castigo in ((pz, 70, 0), (RED, 45, 40)):
            for f, nombre in fuente:
                d = abs(1200 * np.log2(f / meta))
                if d <= tol and (mejor is None or d + castigo < mejor[2]):
                    mejor = (f, nombre, d + castigo, 1200 * np.log2(f / meta))
            if mejor:
                break
        if mejor:
            escala.append({"grado_cents": c % 1200, "hz": mejor[0], "fuente": mejor[1],
                           "error_cents": round(float(mejor[3]), 1)})
    escala.sort(key=lambda e: e["hz"])
    # sin repetidos (dos grados afinados a la misma nota)
    limpia = []
    for e in escala:
        if not limpia or abs(1200 * np.log2(e["hz"] / limpia[-1]["hz"])) > 15:
            limpia.append(e)
    return limpia


def escoger_lente(rng, version):
    if version == "hibrida-clara":
        a, b = rng.choice(["etiope-clara", "jazz-clara", "indostani-clara"], 2, replace=False)
        pa = rng.choice(list(LENTES[a]))
        pb = rng.choice(list(LENTES[b]))
        plantilla = [c for c in LENTES[a][pa] if c % 1200 < 650] + [c for c in LENTES[b][pb] if c % 1200 >= 650]
        gram = str(rng.choice([a, b])).replace("-clara", "")
        return f"{a}:{pa} abajo + {b}:{pb} arriba", sorted(plantilla), gram
    if version.endswith("-clara"):
        p = rng.choice(list(LENTES[version]))
        return f"{version}:{p}", LENTES[version][p], version.replace("-clara", "")
    if version == "hibrida":
        a, b = rng.choice(["etiope", "jazz", "indostani"], 2, replace=False)
        pa = rng.choice(list(LENTES[a]))
        pb = rng.choice(list(LENTES[b]))
        plantilla = [c for c in LENTES[a][pa] if c % 1200 < 650] + [c for c in LENTES[b][pb] if c % 1200 >= 650]
        gram = rng.choice([a, b])
        return f"{a}:{pa} abajo + {b}:{pb} arriba", sorted(plantilla), gram
    p = rng.choice(list(LENTES[version]))
    return f"{version}:{p}", LENTES[version][p], version


def frase(rng, gram, escala, gemela):
    """Índices y figuras según la gramática. Devuelve [(paso16, hz, dur16, vel, adorno)]."""
    n = len(escala)
    if n < 2:
        return []
    hz = [e["hz"] for e in escala]
    out = []
    t = 0
    largo = int(rng.choice([1, 2, 3, 3, 4, 5, 6]))
    i = int(rng.integers(n))
    if gram == "etiope":
        # pentatónico: saltos de uno o dos grados, nota repetida como adorno, cierra en tónica o quinta
        for k in range(largo):
            d = int(rng.choice([1, 2, 3]))
            out.append((t, hz[i], d, 0.8, None))
            if rng.random() < 0.25:
                out.append((t + d, hz[i], 1, 0.55, "repetida"))
                t += 1
            t += d
            i = int(np.clip(i + rng.choice([-2, -1, 1, 2]), 0, n - 1))
        if largo > 2:
            out[-1] = (out[-1][0], hz[0] if rng.random() < 0.6 else hz[min(n - 1, n // 2 + 1)], 3, 0.75, "cierre")
    elif gram == "jazz":
        # simétrico: el mismo intervalo de escala repetido (tonos enteros de Monk), con un
        # desplazamiento de octava ocasional y aproximación por la gemela al final
        paso = int(rng.choice([1, 2, 3])) * int(rng.choice([-1, 1]))
        for k in range(largo):
            f = hz[i % n] * (2 if (rng.random() < 0.15 and k > 0) else 1)
            d = int(rng.choice([1, 1, 2, 3]))
            out.append((t, f, d, 0.85, None))
            t += d
            i = i + paso
            if not 0 <= i < n:
                paso = -paso
                i = int(np.clip(i + 2 * paso, 0, n - 1))
        g = gemela(out[-1][1])
        if g and largo > 1:
            out.insert(len(out) - 1, (max(0, out[-1][0] - 0.25), g[0], 0.25, 0.5, "aproximación"))
    else:
        # indostaní: vakra (sube dos, baja uno), meend como apoyatura que se desliza desde el
        # grado vecino, andolan = oscilar lento entre la nota y su gemela del choque
        for k in range(largo):
            d = int(rng.choice([2, 2, 3, 4]))
            f = hz[i]
            if rng.random() < 0.3 and i > 0:
                out.append((t, hz[i - 1], 0.25, 0.45, "meend"))
                t += 0.25
            g = gemela(f)
            if g and rng.random() < 0.3:
                for r in range(4):
                    out.append((t + r, f if r % 2 == 0 else g[0], 1, 0.7 - 0.08 * r, "andolan"))
                t += 4
            else:
                out.append((t, f, d, 0.8, None))
                t += d
            i = int(np.clip(i + (2 if k % 2 == 0 else -1), 0, n - 1))
    return out
