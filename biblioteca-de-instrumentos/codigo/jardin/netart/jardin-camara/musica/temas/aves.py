"""Aves con canto propio: un coro que vive a su tiempo, calla cuando suena la flor,
presiente la que viene e imita la que pasó.

Canek: los pájaros «no como un acontecimiento pegado al instrumento principal, sino como
también ellos cantan», y luego: «¿Messiaen nos va a conducir a más pájaros?».

De Messiaen se toman tres cosas:
  - cada ave es una ESPECIE con su manera de cantar (Catalogue d'oiseaux);
  - el coro del alba que se va sumando (Réveil des oiseaux), para «amanecer»;
  - varias aves a la vez, cada una a su tiempo (Chronochromie, Épode).
Las especies son de aquí:
  clarín jilguero  silbidos de flauta, largos, que bajan deslizándose
  cenzontle        repite cada frase 2–3 veces e IMITA lo que tocó el instrumento
  primavera        frases cortas de llamado, medianas
  colibrí          chasquidos y trinos rápidos, bajito
Bernie Krause (nicho acústico): cada voz canta en el hueco de las otras. Aquí las aves
callan mientras suena la línea del instrumento y cantan en los silencios.

Cada ave tiene un MOTIVO propio (gestos con grados fijos de la escala, duraciones y
pausas) que repite con variaciones; las alturas salen de la escala que suena en ese
momento, así que el motivo se reconoce y la afinación cambia (como el gancho en grados).
"""
import numpy as np
from pajaros import _tono, lejos, registro

SR = 48000

ESPECIES = {
    "clarin": {"reg": (900, 2600), "gestos": {"silbido": 0.7, "llamado": 0.2, "trino": 0.1},
               "largo": (2, 4), "pausa": 5.0, "repite": 1, "dur": 1.6, "vol": 1.0},
    "cenzontle": {"reg": (1000, 3000), "gestos": {"silbido": 0.3, "trino": 0.25, "gorjeo": 0.25, "llamado": 0.2},
                  "largo": (2, 3), "pausa": 4.0, "repite": 3, "dur": 1.0, "vol": 0.9},
    "primavera": {"reg": (1200, 3000), "gestos": {"llamado": 0.5, "silbido": 0.3, "gorjeo": 0.2},
                  "largo": (3, 5), "pausa": 6.0, "repite": 1, "dur": 0.8, "vol": 0.85},
    "colibri": {"reg": (1800, 3400), "gestos": {"gorjeo": 0.6, "trino": 0.4},
                "largo": (1, 3), "pausa": 7.0, "repite": 1, "dur": 0.6, "vol": 0.5},
}


# ---------------------------------------------------------------- gestos explícitos
def g_silbido(a, b, d, curva=1.0):
    n = int(d * SR)
    t = np.linspace(0, 1, n)
    return _tono(a * (b / a) ** (t ** curva), np.sin(np.pi * t) ** 0.7)


def g_trino(a, b, d, vel=16.0):
    n = int(d * SR)
    t = np.arange(n) / SR
    c = 0.5 + 0.5 * np.tanh(4 * np.sin(2 * np.pi * vel * t))
    return _tono(a * (b / a) ** c, np.sin(np.pi * t / d) ** 0.5 * (0.6 + 0.4 * c))


def g_gorjeo(notas, rng):
    partes = []
    for f in notas:
        d = rng.uniform(0.03, 0.07)
        t = np.linspace(0, 1, int(d * SR))
        partes += [_tono(f * (0.8 + 0.3 * t), np.sin(np.pi * t) ** 0.6), np.zeros(int(rng.uniform(0.02, 0.06) * SR))]
    return np.concatenate(partes)


def g_llamado(a, b):
    n1, n2 = int(0.12 * SR), int(0.28 * SR)
    t1, t2 = np.linspace(0, 1, n1), np.linspace(0, 1, n2)
    return np.concatenate([_tono(np.full(n1, a), np.sin(np.pi * t1)), np.zeros(int(0.05 * SR)),
                           _tono(b * (1 - 0.12 * t2 ** 2), np.sin(np.pi * t2) ** 0.6)])


# ---------------------------------------------------------------- aves
class Ave:
    def __init__(self, rng, especie, nombre):
        self.especie, self.nombre = especie, nombre
        e = ESPECIES[especie]
        self.e = e
        self.pan = float(rng.uniform(-0.95, 0.95))
        tipos, pesos = list(e["gestos"]), np.array(list(e["gestos"].values()))
        self.motivo = []
        for k in range(int(rng.integers(e["largo"][0], e["largo"][1] + 1))):
            tipo = str(rng.choice(tipos, p=pesos / pesos.sum()))
            self.motivo.append({"tipo": tipo, "ga": int(rng.integers(0, 6)), "gb": int(rng.integers(0, 6)),
                                "d": float(rng.uniform(0.6, 1.4) * 0.3 * e["dur"]),
                                "pausa": float(rng.uniform(0.05, 0.25))})

    def notas(self, escala_hz):
        lo, hi = self.e["reg"]
        return sorted({round(registro(f, lo, hi), 3) for f in escala_hz}) or [lo]

    def cantar(self, rng, escala_hz, variar=True):
        """El motivo en la escala del momento, con variación ligera. Devuelve audio."""
        ns = self.notas(escala_hz)
        partes = []
        self.usadas = []                                            # v1.8: qué notas cantó (para la resonancia del muro)
        for g in self.motivo:
            if variar and rng.random() < 0.15:                       # a veces se salta un gesto
                continue
            a = ns[(g["ga"] + (int(rng.integers(-1, 2)) if variar and rng.random() < 0.2 else 0)) % len(ns)]
            b = ns[g["gb"] % len(ns)]
            veces = int(rng.integers(2, self.e["repite"] + 1)) if self.e["repite"] > 1 else 1
            self.usadas += [a, b]
            for _ in range(veces):
                if g["tipo"] == "silbido":
                    x = g_silbido(a, b if b != a else ns[(g["gb"] + 1) % len(ns)], g["d"], rng.uniform(0.6, 1.6))
                elif g["tipo"] == "trino":
                    x = g_trino(a, ns[(ns.index(a) + 1) % len(ns)], g["d"], rng.uniform(12, 22))
                elif g["tipo"] == "gorjeo":
                    x = g_gorjeo([ns[(g["ga"] + j) % len(ns)] for j in range(int(rng.integers(3, 7)))], rng)
                else:
                    x = g_llamado(a, b)
                partes += [x, np.zeros(int(g["pausa"] * SR))]
        return np.concatenate(partes) if partes else np.zeros(1)

    def imitar(self, rng, notas_hz):
        """Como el cenzontle: los pasos del instrumento, en su registro, deslizados y rápidos."""
        ns = [registro(f, *self.e["reg"]) for f in notas_hz][:6]
        if len(ns) < 2:
            return np.zeros(1)
        partes = []
        for a, b in zip(ns, ns[1:]):
            partes += [g_silbido(a, b, rng.uniform(0.09, 0.18), rng.uniform(0.5, 1.5)), np.zeros(int(0.03 * SR))]
        return np.concatenate(partes)


def coro(rng, perfil, duracion, ocupado, escala_en, visitas):
    """El coro completo. perfil: especies, alba, imitar, presentir, corte.
    ocupado(t) → si la línea del instrumento suena; escala_en(t) → escala del momento.
    Devuelve [(t, audio, pan)] y el registro."""
    aves = [Ave(rng, e, f"{e}-{i}") for i, e in enumerate(perfil["especies"])]
    eventos, reg = [], []

    completo = perfil.get("nicho_completo", False)

    def libre(t, dur):
        if completo:      # todo el canto, cada 0.1 s
            return not any(ocupado(t + k * 0.1) for k in range(int(dur / 0.1) + 1))
        return not ocupado(t) and not ocupado(t + min(dur, 1.5) * 0.5)

    def poner(t, x, ave, motivo, notas=None):
        # nicho: si cae sobre la línea, se recorre al siguiente hueco (hasta 4 s); si no hay, calla
        for _ in range(40):
            if libre(t, len(x) / SR):
                break
            t += 0.1
        else:
            reg.append({"t": round(t, 2), "ave": ave.nombre, "que": motivo, "callo": True})
            return
        x = lejos(x, perfil["corte"]) * ave.e["vol"]
        eventos.append((t, x, ave.pan))
        reg.append({"t": round(t, 2), "ave": ave.nombre, "que": motivo, "dur": round(len(x) / SR, 2),
                    "hz": [round(float(f), 2) for f in (notas or [])]})

    # por su cuenta: cada ave canta en tandas a su tiempo; en el alba se van sumando
    for i, ave in enumerate(aves):
        t = (duracion * 0.65 * i / max(1, len(aves))) + rng.uniform(0, 3) if perfil["alba"] else rng.uniform(1, 8)
        while t < duracion - 2:
            x = ave.cantar(rng, escala_en(t))
            poner(t, x, ave, "canto", ave.usadas)
            t += len(x) / SR + rng.exponential(ave.e["pausa"]) + 0.5
    # antes: presienten la flor que viene; después: el cenzontle imita lo que tocó el instrumento
    imitadores = [a for a in aves if a.especie == "cenzontle"] or aves[:1]
    for v in visitas:
        if not v["notas"]:
            continue
        if rng.random() < perfil["presentir"]:
            ave = aves[int(rng.integers(len(aves)))]
            ns = ave.notas([e["hz"] for e in v["escala"]])
            a, b = ns[0], ns[-1]
            poner(v["t"] - rng.uniform(0.8, 2.0), g_silbido(a, b, rng.uniform(0.25, 0.5)), ave, "presiente", [a, b])
        if rng.random() < perfil["imitar"]:
            ave = imitadores[int(rng.integers(len(imitadores)))]
            fin = v["t_fin"]
            poner(fin + rng.uniform(0.3, 1.2), ave.imitar(rng, [n["hz"] for n in v["notas"]]), ave, "imita",
                  [registro(n["hz"], *ave.e["reg"]) for n in v["notas"]][:6])
    # regalos (la flauta hecha pájaro): el cenzontle comprime el arranque del canto y le pone un final propio
    for rg in perfil.get("regalos", []):
        ave = imitadores[0]
        poner(rg["t"], ave.imitar(rng, rg["notas"]), ave, "regala", [registro(f, *ave.e["reg"]) for f in rg["notas"]])
    descripcion = [{"ave": a.nombre, "especie": a.especie, "pan": round(a.pan, 2), "motivo": a.motivo} for a in aves]
    return eventos, reg, descripcion
