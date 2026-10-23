#!/usr/bin/env python3
"""Serie del jardín: siete canciones, una por porte de planta.

Todas comparten lo que la escucha de Canek fijó (16 oct 2026):
  - el muro: un caminante armónico arriba contra uno subarmónico abajo, por un laberinto;
    salen de casa (el mismo acorde en las dos familias) y regresan a ella;
  - cada visita a una flor desencadena la escala del choque, leída por una lente
    (etíope, jazz, indostaní, híbrida), con sombras subarmónicas casi paralelas que vibran;
  - instrumentos que sostienen y no evocan un teclado temperado (Hammond el mejor;
    Farfisa, flauta, theremin, trautonium, ondas Martenot también).

Lo que hace a cada canción OTRA (el genoma del porte):
  F0 (centro), K (qué parciales coinciden: n·m/K potencia de 2), rango de los caminantes,
  pasos de cada caminante (prolación), tempo, duración, lente, instrumento, pulso,
  silencios, bordón y la curva de tensión.

La casa se BUSCA: cuatro n del rango y cuatro m que coincidan en altura (módulo octava)
y formen acordes válidos; se elige la menos rugosa. FU = K·F0/2^j, con j tal que el
caminante subarmónico quede debajo del armónico («subarmónicos abajo»).

Uso:  python serie.py [--solo afinidades ...] [--prueba]
"""
import argparse, hashlib, itertools, json, secrets, sys, tempfile
from pathlib import Path
import numpy as np

import laberintos as L
import escalas_choque as E
A = L.A
SR = L.SR
PROGRAMA = "serie-del-jardin-v1.9.1"   # v1.9.1: la resonancia se nivela sola a 8 dB bajo las aves;   # v1.9: mismas leyes para las cuatro; vericueto arpa; agua arpa;   # v1.8.1: resonancia de aves 10 dB arriba (no se oía);   # v1.8: vericuetos a lo Monk, florecer crece, aves encienden el muro;   # v1.7: principal «aprende» y agua que canta en el día; palme afinada a la casa;   # v1.6: aves 8 dB más cerca (10 en tizita), menos sala;   # v1.5: coro de aves con canto propio;   # v1.4: pájaros por pico, graves y lejos; dùndún libre;   # v1.3: agua en el equipo (menos, más lejos, cede) + pájaros;   # v1.1: gotas −6 dB y techo antes del tanh; v1.2: tambor parlante   # v0.1: casa propia del caminante de abajo; ikebana con menos silencio


# ---------------------------------------------------------------- pulsos
def pulso_ninguno(P, rng):
    pass


def pulso_afinidades(P, rng):
    L.pulso_discreto(P, rng)


def pulso_tizita(P, rng):
    """12/8 ligero: bombo en 1 y en el 4.º octavo-de-tresillo, hats en tresillos."""
    tres = L.BEAT / 3
    for b in range(0, L.TIEMPOS, 4):
        t = b * L.BEAT
        for tb in (0, 2.0 * L.BEAT + 2 * tres):
            P["bombo"].pon(t + tb, 0.65 * A.bombo(rng))
        for k in range(12):
            P["hats"].pon(t + k * tres + rng.normal(0, 0.003), (0.5 if k % 3 == 0 else 0.25) * A.hat(rng))


def pulso_mixtur(P, rng):
    """Sólo un latido grave cada dos compases."""
    for b in range(0, L.TIEMPOS, 8):
        P["bombo"].pon(b * L.BEAT, 0.6 * A.bombo(rng))


def pulso_sombrilla(P, rng):
    """5/4 de funk lento: bombo en 1 y 3.5, aro afinado en 4, hats en octavos."""
    for b in range(0, L.TIEMPOS, 5):
        t = b * L.BEAT
        for tb in (0, 2.5 * L.BEAT):
            P["bombo"].pon(t + tb + rng.normal(0, 0.003), 0.75 * A.bombo(rng))
        P["hats"].pon(t + 3 * L.BEAT, 0.5 * A.aro(rng))
        for k in range(10):
            P["hats"].pon(t + k * L.BEAT / 2 + rng.normal(0, 0.003), (0.4 if k % 2 else 0.25) * A.hat(rng))


def pulso_rosal(P, rng):
    for b in range(0, L.TIEMPOS, 4):
        P["bombo"].pon(b * L.BEAT, 0.7 * A.bombo(rng))
        P["bombo"].pon((b + 2.5) * L.BEAT, 0.45 * A.bombo(rng))
        for p in range(8):
            P["hats"].pon((b + p / 2) * L.BEAT + rng.normal(0, 0.003), (0.35 if p % 2 else 0.2) * A.hat(rng))


# ---------------------------------------------------------------- tensiones
def tension_subida(x):            # la de la v1.1–1.5
    return min(1.0, x / 0.6)


def tension_perturbacion(x):      # «lo que vuelve a crecer»: quieto, golpe a 35 %, se recupera
    if x < 0.3:
        return 0.15
    if x < 0.42:
        return 1.0
    return max(0.1, 1.0 - (x - 0.42) / 0.4)


def tension_ola(x):               # dos crestas
    return 0.5 - 0.5 * np.cos(2 * np.pi * 2 * min(1.0, x / 0.85))


def tambor(rng, vel=1.0):
    """«También había un tambor bonito» → «tambor parlante»: en el pulso, un golpe de
    membrana que se desliza entre dos notas de la casa (parlante.py)."""
    import parlante
    casa = [parlante.registro(L.F0 * n) for n in L.CASA]
    a, b = rng.choice(casa, 2, replace=False)
    return parlante.golpe(float(a), float(b), rng, vel, glide=rng.uniform(0.04, 0.1), apagado=rng.random() < 0.3)


def pulso_agua_68(P, rng):
    """6/8 que flota: sólo un bombo suave al principio del compás y tresillos muy quietos."""
    tres = L.BEAT / 3
    for b in range(0, L.TIEMPOS, 4):
        t = b * L.BEAT
        P["bombo"].pon(t, 0.4 * A.bombo(rng))
        P["tambor"].pon(t + 2 * L.BEAT + 2 * tres, 0.45 * tambor(rng))      # el tambor afinado, a contratiempo
        P["tambor"].pon(t + 3 * L.BEAT + tres, 0.3 * tambor(rng))
        for k in range(12):
            if k % 3 == 0 or rng.random() < 0.35:
                P["hats"].pon(t + k * tres + rng.normal(0, 0.003), (0.3 if k % 6 == 0 else 0.15) * A.hat(rng))


def pulso_sol_54(P, rng):
    """5/4 sin bombo: aro afinado en 1 y hats ligeros."""
    for b in range(0, L.TIEMPOS, 5):
        t = b * L.BEAT
        P["tambor"].pon(t, 0.45 * tambor(rng))
        P["tambor"].pon(t + 3 * L.BEAT, 0.4 * tambor(rng))
        for k in range(10):
            if rng.random() < 0.6:
                P["hats"].pon(t + k * L.BEAT / 2 + rng.normal(0, 0.003), 0.18 * A.hat(rng))


def pulso_florecer(P, rng):
    """Casi nada: el tambor afinado cada dos compases, a veces."""
    for b in range(0, L.TIEMPOS, 8):
        if rng.random() < 0.7:
            P["tambor"].pon((b + rng.choice([0, 1.5, 2.5])) * L.BEAT, 0.35 * tambor(rng))


def tension_agua(x):              # casi siempre cerca de casa; ondas breves de choque
    return 0.12 + 0.28 * max(0.0, np.sin(2 * np.pi * 3 * x)) ** 3


def tension_florecer(x):          # se abre poco a poco, sin golpe, y vuelve
    return 0.1 + 0.45 * np.sin(np.pi * min(1.0, x / 0.8)) ** 2


# ---------------------------------------------------------------- genomas
SERIE = [
    {"porte": "candelabro", "titulo": "afinidades", "semilla": 14, "F0": 27.5, "K": 120, "rango": (8, 20), "span": 11,
     "pasos": (3, 4), "bpm": 76, "seg": 80, "lente": "hibrida", "instrumento": "hammond",
     "pulso": pulso_afinidades, "silencio": 0.2, "bordon": False, "tension": tension_subida,
     "idea": "la de s14: densa; Hammond, el que más gustó"},
    {"porte": "espiga", "titulo": "tizita-electrica", "semilla": 31, "F0": 24.5, "K": 180, "rango": (8, 20), "span": 11,
     "pasos": (2, 3), "bpm": 92, "seg": 85, "lente": "etiope", "instrumento": "farfisa",
     "pulso": pulso_tizita, "silencio": 0.15, "bordon": False, "tension": tension_ola,
     "idea": "ethio-jazz de los setenta: caminantes rápidos, qenet, Farfisa, 12/8 ligero"},
    {"porte": "mata", "titulo": "mixtur", "semilla": 59, "F0": 29.14, "K": 140, "rango": (7, 20), "span": 13,
     "pasos": (2, 3), "bpm": 70, "seg": 85, "lente": "jazz", "instrumento": "trautonium",
     "pulso": pulso_mixtur, "silencio": 0.1, "bordon": False, "tension": tension_subida,
     "idea": "la más densa: coincidencias de séptima (K = 140), tonos enteros y disminuidas, trautonium con subarmónicos propios"},
    {"porte": "arco", "titulo": "raices-invertidas", "semilla": 265, "F0": 20.6, "K": 144, "rango": (8, 20), "span": 11,
     "pasos": (4, 6), "bpm": 60, "seg": 95, "lente": "indostani", "instrumento": "flauta",
     "pulso": pulso_ninguno, "silencio": 0.25, "bordon": True, "tension": tension_subida,
     "idea": "lenta, sin pulso, con bordón de casa como tanpura; raga, flauta con meend largos"},
    {"porte": "corimbo", "titulo": "sombrilla", "semilla": 7, "F0": 32.7, "K": 140, "rango": (7, 20), "span": 13,
     "pasos": (5, 4), "bpm": 84, "seg": 85, "lente": "hibrida", "instrumento": "theremin",
     "pulso": pulso_sombrilla, "silencio": 0.2, "bordon": False, "tension": tension_ola,
     "idea": "5/4 de funk lento con séptimas naturales; theremin: el que tocará el cuerpo"},
    {"porte": "ikebana", "titulo": "lo-que-vuelve-a-crecer", "semilla": 3, "F0": 23.12, "K": 180, "rango": (8, 20), "span": 11,
     "pasos": (4, 5), "bpm": 58, "seg": 95, "lente": "etiope", "instrumento": "ondas",
     "pulso": pulso_ninguno, "silencio": 0.3, "bordon": False, "tension": tension_perturbacion,
     "idea": "casi quieta, silencios con función; una perturbación a un tercio y la recuperación; ondas Martenot con la palme afinada a casa"},
    {"porte": "rosal", "titulo": "rosal", "semilla": 2026, "F0": 30.87, "K": 120, "rango": (8, 20), "span": 11,
     "pasos": (3, 4), "bpm": 88, "seg": 85, "lente": "hibrida", "instrumento": "ensamble",
     "pulso": pulso_rosal, "silencio": 0.15, "bordon": False, "tension": tension_ola,
     "idea": "el ensamble: cada visita la toca un instrumento distinto, como si cada flor fuera uno"},
]


# Las gemelas «de día» de las cuatro que gustaron (Canek: «como si tocaras el agua y salieran
# chispas de todos colores»; la serie de noche es «nocturna y siniestra»). Opuestos:
#   denso → aireado (3 voces por caminante, cerca de casa casi siempre)
#   trepidante → sereno (pasos largos, sombras que respiran a 0.3–1 Hz, menos pulso)
#   triste → luminoso (el armónico es el cimiento y lleva el bajo; el subarmónico va ARRIBA
#            como color; lentes claras: tizita y bati mayor, lidia, yaman, bilawal, hamsadhwani)
#   + gotas-burbuja afinadas a la escala del choque en cada visita (agua.py)
DIA = {"voces": 3, "bajo_de": "arriba", "sub_arriba": True, "batido": (0.3, 1.0),
       "brillo": (3200, 2600), "mezcla": {"arriba": -1, "abajo": -6, "sombras": -4, "bajo": -2, "gotas_i": -11, "gotas_d": -11,
                                         "pajaros_i": 19, "pajaros_d": 19,
                                         "resuena": 10},   # v1.8.1: el muro encendido quedaba 18 dB bajo las aves: no se oía
       "agua": True, "techo": 0.85, "parlante": True,
       # v1.3: el agua era «el instrumento principal»; ahora es parte del equipo, y le contestan pájaros
       "gotas": {"n": (3, 8), "octavas": (0, 1, 1, 2)}, "pajaros": True, "cede": True,
       "sala": {"gotas_i": 0.85, "gotas_d": 0.85, "pajaros_i": 0.55, "pajaros_d": 0.55},
       # v1.4: los pájaros de tizita picaban (escasos + normalizados por energía); el dùndún, libre
       "pajaros_voz": {"lo": 900, "hi": 3000, "corte": 3000}, "norma_pico": {"pajaros_i", "pajaros_d"},
       "tambor_libre": 0.5,
       # v1.5: los pájaros ya no van pegados al agua; cantan ellos (aves.py)
       "pajaros": False,
       # v1.7: el principal hecho pájaro en modo «aprende» (Canek lo eligió en amanecer) y el agua que canta
       "principal": "aprende", "agua_canta": True, "principal_guarda": True,
       # v1.8: «tun turin tun» en tizita y sombrilla; «después del minuto se pone interesante»
       "vericuetos": True, "crecer": False, "resonancia_aves": True,
       "agua_arpa": True}
SERIE_DIA = [
    dict(DIA, porte="espiga", titulo="tizita-mayor", gemela_de="tizita-electrica", semilla=31, F0=36.75, K=180,
         rango=(8, 20), span=11, pasos=(4, 6), bpm=100, seg=85, lente="etiope-clara", instrumento="farfisa",
         pulso=pulso_agua_68, silencio=0.25, bordon=False, tension=tension_agua,
         aves={"especies": ["primavera", "cenzontle"], "alba": False, "imitar": 0.5, "presentir": 0.3, "corte": 4000},
         mezcla=dict(DIA["mezcla"], pajaros_i=19, pajaros_d=19),
         idea="la Farfisa de tizita eléctrica en tizita y bati mayor, 6/8 que flota, gotas"),
    dict(DIA, porte="arco", titulo="amanecer", gemela_de="raices-invertidas", semilla=265, F0=30.9, K=144,
         rango=(8, 20), span=11, pasos=(6, 8), bpm=60, seg=95, lente="indostani-clara", instrumento="flauta",
         pulso=pulso_ninguno, silencio=0.2, bordon=True, tension=tension_agua, tambor_libre=1.0,
         # v1.9: «si ya aplicamos leyes a una, todas las llevarían»: amanecer con las mismas leyes
         aves={"especies": ["colibri", "primavera", "clarin", "cenzontle", "clarin"], "alba": True,
               "imitar": 0.6, "presentir": 0.5, "corte": 4000},
         idea="la flauta de raíces en yaman, bilawal o hamsadhwani; bordón claro; gotas"),
    dict(DIA, porte="ikebana", titulo="florecer", gemela_de="lo-que-vuelve-a-crecer", semilla=3, F0=34.65, K=180,
         rango=(8, 20), span=11, pasos=(5, 6), bpm=64, seg=95, lente="jazz-clara", instrumento="ondas",
         pulso=pulso_florecer, crecer=True,
         aves={"especies": ["cenzontle"], "alba": False, "imitar": 0.8, "presentir": 0.3, "corte": 4000}, silencio=0.25, bordon=False, tension=tension_florecer,
         idea="sin perturbación: el jardín sólo se abre; ondas Martenot en lidia; gotas"),
    dict(DIA, porte="corimbo", titulo="sombrilla-de-sol", gemela_de="sombrilla", semilla=7, F0=43.65, K=140,
         rango=(7, 20), span=13, pasos=(5, 5), bpm=92, seg=85, lente="hibrida-clara", instrumento="theremin",
         pulso=pulso_sol_54, silencio=0.2, bordon=False, tension=tension_agua,
         aves={"especies": ["clarin", "colibri"], "alba": False, "imitar": 0.4, "presentir": 0.4, "corte": 4000},
         idea="theremin alto sobre armónicos, 5/4 sin bombo, gotas"),
]
NOCHE = {"voces": 4, "bajo_de": "abajo", "sub_arriba": False, "batido": (2.5, 6.0),
         "brillo": (2200, 1200), "mezcla": {}, "agua": False, "techo": None, "parlante": False,
         "gotas": {"n": (5, 13), "octavas": (1, 1, 2, 2, 3)}, "pajaros": False, "cede": False, "sala": {},
         "pajaros_voz": {"lo": 1200, "hi": 4500, "corte": None}, "norma_pico": set(), "tambor_libre": 0.0,
         "aves": None, "principal": None, "agua_canta": False, "principal_guarda": False,
         "vericuetos": False, "crecer": False, "resonancia_aves": False, "agua_arpa": False}


def potencia_de_2(x):
    l = np.log2(x)
    return abs(l - round(l)) < 1e-9


def buscar_casa(g):
    """Cuatro n y cuatro m que coinciden en altura (módulo octava), ambos acordes válidos."""
    lo, hi = g["rango"]
    rng_ = range(lo, hi + 1)
    mejores = []
    for ns in itertools.combinations(rng_, L.N_VOCES):
        if not L.valido(ns):
            continue
        opciones = [[m for m in rng_ if potencia_de_2(n * m / g["K"])] for n in ns]
        if not all(opciones):
            continue
        for ms in itertools.product(*opciones):
            mset = tuple(sorted(ms))
            if len(set(ms)) == len(ms) and L.valido(mset):
                mejores.append((L.rug_acordes(ns, mset), ns, mset))
    if not mejores:
        return None
    mejores.sort()
    return mejores[0]


def configurar(g):
    """Pone el genoma en los módulos (son globales de laberintos y escalas_choque)."""
    g = dict(NOCHE, **g)
    L.N_VOCES = g["voces"]
    L.BAJO_DE = g["bajo_de"]
    L.BATIDO = g["batido"]
    L.MURO_BRILLO = g["brillo"]
    L.MEZCLA_EXTRA = g["mezcla"]
    L.AGUA = g["agua"]
    L.MEZCLA_TECHO = g["techo"]
    L.PARLANTE = g["parlante"]
    L.GOTAS = g["gotas"]
    L.PAJAROS = g["pajaros"]
    L.CEDE = g["cede"]
    L.SALA_EXTRA = g["sala"]
    L.PAJAROS_VOZ = g["pajaros_voz"]
    L.NORMA_PICO = g["norma_pico"]
    L.TAMBOR_LIBRE = g["tambor_libre"]
    L.AVES = g["aves"]
    L.PRINCIPAL = g["principal"]
    L.AGUA_CANTA = g["agua_canta"]
    L.PRINCIPAL_GUARDA = g["principal_guarda"]
    L.VERICUETOS = g["vericuetos"]
    L.CRECER = g["crecer"]
    L.RESONANCIA_AVES = g["resonancia_aves"]
    L.AGUA_ARPA = g["agua_arpa"]
    if g["resonancia_aves"]:
        L.NORMA_PICO = set(L.NORMA_PICO) | {"resuena"}
    import instrumentos as I
    I.ARTICULAR = bool(g["principal"])
    L.F0 = g["F0"]
    L.RANGO = range(g["rango"][0], g["rango"][1] + 1)
    L.SPAN = g["span"]
    # FU: K·F0 corrido por octavas para que el subarmónico quede debajo del armónico
    medio_arriba = g["F0"] * np.mean(L.RANGO)
    FU = g["K"] * g["F0"]
    meta = 1.5 if g["sub_arriba"] else 0.75             # de día el subarmónico va arriba, de color
    while FU / np.mean(L.RANGO) > meta * medio_arriba:
        FU /= 2
    while FU / np.mean(L.RANGO) < meta / 2 * medio_arriba:
        FU *= 2
    L.FU = FU
    E.F0, E.FU = g["F0"], FU
    E.RED = E.red()
    casa = buscar_casa(g)
    L.CASA = casa[1]
    L.CASA_ABAJO = casa[2]
    I.CASA_HZ = [g["F0"] * n for n in casa[1]] if g["principal"] else [220.0, 275.0, 330.0, 412.5]   # la palme, afinada a la casa
    L.PASO_ARRIBA, L.PASO_ABAJO = g["pasos"]
    L.BPM = g["bpm"]
    L.BEAT = 60 / g["bpm"]
    mcm = np.lcm(*g["pasos"])
    L.TIEMPOS = int(round(g["seg"] / L.BEAT / mcm) * mcm)
    L.SILENCIO = g["silencio"]
    L.BORDON = g["bordon"]
    L.PULSO = g["pulso"]
    L.tension = g["tension"]
    return {"casa_n": list(casa[1]), "casa_m_abajo": list(casa[2]), "rugosidad_casa": round(casa[0], 3),
            "FU": FU, "casa_hz_arriba": [round(g["F0"] * n, 2) for n in casa[1]],
            "casa_hz_abajo": [round(FU / m, 2) for m in casa[2]], "tiempos": L.TIEMPOS}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", nargs="*")
    ap.add_argument("--prueba", action="store_true", help="sólo busca casas y registros")
    ap.add_argument("--dia", action="store_true", help="las gemelas de día en vez de la serie de noche")
    ap.add_argument("--salida", default=str(Path(__file__).resolve().parent.parent / "estudios"))
    args = ap.parse_args()
    genomas = [g for g in (SERIE_DIA if args.dia else SERIE) if not args.solo or g["titulo"] in args.solo]
    if args.prueba:
        for g in genomas:
            c = configurar(g)
            print(g["titulo"], c)
        return
    codigos = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(Path(__file__).resolve().parent.glob("*.py"))}
    nonce = secrets.token_hex(16)
    ejec = hashlib.sha256((PROGRAMA + json.dumps(codigos, sort_keys=True) + ",".join(g["titulo"] for g in genomas) + nonce).encode()).hexdigest()
    corto = ejec[:12]
    carpeta = Path(args.salida) / (f"serie-del-jardin-de-dia-{corto}" if args.dia else f"serie-del-jardin-{corto}")
    carpeta.mkdir(exist_ok=False)
    tmp = Path(tempfile.mkdtemp(prefix="serie-"))
    import instrumentos as I
    reg = {"ejecucion_sha256": ejec, "nonce": nonce, "codigos_sha256": codigos, "programa": PROGRAMA,
           "procedencia_voz": I.procedencia_banco(), "canciones": []}
    mezclas = []
    for num, g in enumerate(genomas, 1):
        conf = configurar(g)
        P, total, gen = L.tema(g["semilla"], f"choque-{g['lente']}", g["instrumento"])
        mix = L.mezclar(P, g["semilla"])[: int((total + 0.5) * SR)]
        wav = tmp / f"{g['titulo']}.wav"
        A.escribir_wav(wav, mix)
        dest = carpeta / f"{num:02d}-{g['porte']}-{g['titulo']}-s{g['semilla']}-{corto}.m4a"
        g = dict(NOCHE, **g)
        A.m4a(wav, dest)
        mezclas.append(mix / np.sqrt(np.mean(mix ** 2)) * 0.12)
        r = np.array([c[1] for c in gen["rugosidad"]])
        ficha = {k: (v.__name__ if callable(v) else sorted(v) if isinstance(v, set) else v) for k, v in g.items()}
        ficha.update(conf)
        ficha.update({"archivo": dest.name, "contenido_sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
                      "duracion_s": round(len(mix) / SR, 2), "finito": bool(np.all(np.isfinite(mix))),
                      "bandas": A.balance(mix), "rugosidad_min_max": [round(float(r.min()), 3), round(float(r.max()), 3)],
                      "visitas": len(gen["visitas"]), "tema": gen})
        reg["canciones"].append(ficha)
        print(f"{num:02d} {g['titulo']:24s} casa {conf['casa_hz_arriba']}  {L.BPM} bpm  {ficha['duracion_s']} s  "
              f"rug {ficha['rugosidad_min_max']}  visitas {ficha['visitas']}  {ficha['bandas']}", flush=True)
    hueco = np.zeros((int(1.5 * SR), 2))
    tejido = np.concatenate(sum([[m, hueco] for m in mezclas], [])[:-1])
    A.escribir_wav(tmp / "tejido.wav", tejido / np.max(np.abs(tejido)) * 0.89)
    dest = carpeta / (f"serie-de-dia-tejida-{corto}.m4a" if args.dia else f"serie-del-jardin-tejida-{corto}.m4a")
    A.m4a(tmp / "tejido.wav", dest)
    reg["tejido"] = {"archivo": dest.name, "contenido_sha256": hashlib.sha256(dest.read_bytes()).hexdigest()}
    with open(carpeta / f"receta-{corto}.json", "x", encoding="utf-8") as fh:
        json.dump(reg, fh, ensure_ascii=False)
    print(carpeta)


if __name__ == "__main__":
    main()
