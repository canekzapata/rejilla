#!/usr/bin/env python3
"""Generador de temas v1 · laberintos de afinidad.

Canek, después de los seis ganchos: «piénsalo con los laberintos a lo Monk; los
acompañamientos van bien, pero es más de armonía chocando entre sí en armónicos y
subarmónicos que en ritmo».

Como en «epístrofe» (rejilla, loop 08), dos caminantes recorren un laberinto a distintas
velocidades y casi nunca están en el mismo lugar:

  arriba   caminante ARMÓNICO: cuatro parciales de F0 (27.5·n, n en 8…20)
  abajo    caminante SUBARMÓNICO: cuatro divisores de FU = 3300 (FU/m, m en 8…20) — el
           acompañamiento que gustó, con su bajo

Cada paso mueve UNA voz (n ± 1 o ± 2). El laberinto es un árbol de Prim sembrado sobre esos
acordes: tiene callejones, y al llegar a uno el caminante regresa por donde vino; los
regresos son los lugares que el oído reconoce. Arriba se da un paso cada 3 tiempos y abajo
uno cada 4: se alinean cada 12. Como FU/F0 = 120, las dos familias coinciden exactamente
cuando n·m = 120 (8·15, 10·12, 12·10, 15·8) y casi coinciden en muchos otros lugares: ahí
chocan y baten. El muro es la suma: rugoso donde chocan, claro donde coinciden.

Monk entra como comentario de piano: cada nota que se mueve arriba suena con su gemela
subarmónica más cercana chafada 25 ms antes (la segunda menor de Monk, aquí un choque entre
familias), en una célula de tres notas desplazada cada 3 dieciseisavos. En los callejones,
una escalera de armónicos que baja de dos en dos.

La rugosidad (modelo de Sethares) se calcula de los parciales que suenan y queda en la receta.

Uso:  python laberintos.py [--semillas 3 14 59 265]
"""
import argparse, hashlib, json, secrets, sys, tempfile
from pathlib import Path
import numpy as np
from scipy.signal import fftconvolve

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "estudio1"))
import afinidades as A

SR = A.SR
PROGRAMA = "laberintos-de-afinidad-v1.5"
# v1.5: más instrumentos parientes de la Farfisa y la flauta (gustaron en v1.4): theremin,
# trautonium (subarmónicos propios), ondas Martenot (palme afinada a casa), Hammond con Leslie.
# v1.4: el instrumento del comentario se elige aparte (piano, voz, farfisa, flauta, cuerda;
# ver instrumentos.py). Los que no son piano tocan cada visita como una línea que desliza,
# con azar propio (semilla + 2000), así que las notas son idénticas entre instrumentos.
# v1.3: comentario «choque-<lente>»: cada paso de arriba es una VISITA A UNA FLOR que
# desencadena la escala del choque leída por una lente (etíope, jazz, indostaní, híbrida;
# ver escalas_choque.py), y cada nota trae debajo sus subarmónicos casi paralelos (f/k + δ)
# que vibran contra ella: el armónico k de la sombra bate con la nota a k·δ Hz.
# v1.2: el comentario (el «piano de Monk») es intercambiable y tiene su propia semilla, para
# comparar instrumentos con el MISMO muro. Canek oyó en v1.1 un cimbalón o clavicordio.
# v1.1: los dos caminantes salen de CASA, el mismo acorde en las dos familias
# (27.5·{8,10,12,15} = 3300/{15,12,10,8} = 220, 275, 330, 412.5 Hz), se pierden en el
# laberinto escogiendo pasillos según una curva de tensión y regresan por donde vinieron
# hasta coincidir. En v1 vagaban sin encontrarse y el muro no respiraba (±15 %).
CASA = (8, 10, 12, 15)
CASA_ABAJO = None    # divisores de casa del caminante subarmónico; None = los mismos que arriba (K = 120)
# Ganchos para la serie (serie.py los cambia por canción; los valores por omisión dejan la
# v1.5 tal cual): probabilidad de no visitar una flor, bordón de casa, conjunto de
# instrumentos del «ensamble» y la función del pulso (se define más abajo).
SILENCIO = 0.2
SPAN = 11            # distancia máxima entre la voz más grave y la más aguda (en n o m)
# Ganchos de las gemelas «de día» (serie v1): voces por caminante, quién lleva el bajo,
# batido de las sombras, brillo del muro, ganancias extra y gotas (agua.py).
N_VOCES = 4
BAJO_DE = "abajo"
BATIDO = (2.5, 6.0)
MURO_BRILLO = (2200, 1200)
MEZCLA_EXTRA = {}
AGUA = False
PARLANTE = False      # de día: el tambor parlante contesta cada visita con la escala del choque (parlante.py)
GOTAS = {"n": (5, 13), "octavas": (1, 1, 2, 2, 3)}
PAJAROS = False       # de día v1.3: a veces un pájaro contesta al agua (pajaros.py)
CEDE = False          # de día v1.3: las gotas y los pájaros bajan cuando suena la línea del instrumento
SALA_EXTRA = {}
PAJAROS_VOZ = {"lo": 1200, "hi": 4500, "corte": None}   # de día v1.4: más graves y lejos
NORMA_PICO = set()    # pistas escasas que se normalizan por pico (no por energía): sus picos no revientan
TAMBOR_LIBRE = 0.0
AVES = None           # de día v1.5: perfil del coro de aves (aves.py): cantan a su tiempo, callan en la línea    # de día v1.4: el dùndún habla por su cuenta (densidad de frases)
PRINCIPAL = None      # None: como v1.6. "azar" | "persistente" | "aprende" (principal.py), con azar separado
AGUA_CANTA = False
AGUA_ARPA = False     # v1.9: a veces (y después de una carrera «arpa» del principal) las gotas caen en escala
PRINCIPAL_GUARDA = False
VERICUETOS = False         # v1.8: el canto se tuerce a lo Monk cada vez más
CRECER = False             # v1.8: florecer: el canto crece y sube
RESONANCIA_AVES = False    # v1.8: las notas de las aves encienden el parcial del muro que les queda cerca   # principal v2: no calla dos veces seguidas y guarda el regalo cuando calla    # el agua guarda la huella de la frase y la devuelve cantabile (agua.canto)
MEZCLA_TECHO = None   # si se da, la mezcla se escala a este pico ANTES del tanh (de día: las gotas no saturan)
BORDON = False
ENSAMBLE = ["hammond", "farfisa", "flauta", "theremin", "trautonium", "ondas"]
RESERVA = {"arriba": 2, "abajo": 1}   # pasos quietos en casa al final
F0, FU = 27.5, 3300.0
RANGO = range(8, 21)
BPM = 76
BEAT = 60 / BPM
PASO_ARRIBA, PASO_ABAJO = 3, 4      # tiempos por paso: se alinean cada 12
TIEMPOS = 96


# ---------------------------------------------------------------- laberinto
def valido(c):
    return all(b - a >= 2 for a, b in zip(c, c[1:])) and c[-1] - c[0] <= SPAN and c[0] in RANGO and c[-1] in RANGO


def vecinos(c):
    for i in range(len(c)):
        for d in (-2, -1, 1, 2):
            n = list(c)
            n[i] += d
            n = tuple(n)
            if valido(n):
                yield n


def laberinto(rng, inicio):
    """Árbol de Prim aleatorio sobre los acordes válidos: pasillos y callejones."""
    arbol = {inicio: []}
    frontera = [(inicio, v) for v in vecinos(inicio)]
    while frontera:
        a, b = frontera.pop(int(rng.integers(len(frontera))))
        if b in arbol:
            continue
        arbol[a].append(b)
        arbol[b] = [a]
        frontera += [(b, v) for v in vecinos(b) if v not in arbol]
    return arbol


def recorrer(rng, arbol, inicio, pasos):
    """El caminante entra al pasillo nuevo que encuentre; en un callejón regresa."""
    camino, pila, visto, callejones = [inicio], [inicio], {inicio}, []
    regresando = False
    while len(camino) < pasos:
        aqui = pila[-1]
        nuevos = [v for v in arbol[aqui] if v not in visto]
        if nuevos:
            v = nuevos[int(rng.integers(len(nuevos)))]
            visto.add(v)
            pila.append(v)
            regresando = False
        else:
            if len(pila) == 1:
                break
            if not regresando:           # recién llegó al fondo de un callejón
                callejones.append(len(camino) - 1)
            regresando = True
            pila.pop()
            v = pila[-1]
        camino.append(v)
    return camino, callejones


# ---------------------------------------------------------------- choque
def parciales_de(f, amp, k_max=8, decl=1.3):
    return [(f * k, amp / k ** decl) for k in range(1, k_max + 1) if f * k < 5000]


def rugosidad(parciales):
    """Sethares (1993): suma de disonancia entre todos los pares de parciales."""
    if len(parciales) < 2:
        return 0.0
    f = np.array([p[0] for p in parciales])
    a = np.array([p[1] for p in parciales])
    i, j = np.triu_indices(len(f), 1)
    fmin = np.minimum(f[i], f[j])
    s = 0.24 / (0.021 * fmin + 19)
    d = np.abs(f[i] - f[j])
    return float(np.sum(a[i] * a[j] * (np.exp(-3.5 * s * d) - np.exp(-5.75 * s * d))))


def gemela(f):
    """La nota subarmónica (FU/m, en cualquier octava) más cercana que choca: 20–110 cents."""
    mejor = None
    for m in range(5, 41):
        g = FU / m
        while g < f / 1.5:
            g *= 2
        while g > f * 1.5:
            g /= 2
        c = abs(1200 * np.log2(g / f))
        if 20 <= c <= 110 and (mejor is None or c < mejor[1]):
            mejor = (g, c)
    return mejor


def tension(x):
    """Curva objetivo de 0 a 1: sube hasta el 60 % de la pieza; luego el regreso manda."""
    return min(1.0, x / 0.6)


def acorde_hz(c, familia):
    return [F0 * n for n in c] if familia == "arriba" else [FU / m for m in c]


def rug_acordes(co, cu):
    return rugosidad([p for f in acorde_hz(co, "arriba") + acorde_hz(cu, "abajo") for p in parciales_de(f, 1.0)])


def caminar_juntos(rng, labs, rmin, rmax):
    """Los dos caminantes, en orden de tiempo. Adelante: el pasillo nuevo cuya rugosidad
    (con el otro caminante) queda más cerca de la tensión buscada. Callejón: regresa.
    Cuando los pasos que quedan sólo alcanzan para volver, desanda el camino a CASA."""
    paso = {"arriba": PASO_ARRIBA, "abajo": PASO_ABAJO}
    N = {k: TIEMPOS // paso[k] for k in paso}
    casa = {"arriba": CASA, "abajo": CASA_ABAJO or CASA}
    W = {k: {"camino": [casa[k]], "pila": [casa[k]], "visto": {casa[k]}, "regresando": False,
             "callejones": [], "vuelta": None} for k in paso}
    for beat in range(1, TIEMPOS):
        for k in ("arriba", "abajo"):
            if beat % paso[k]:
                continue
            w = W[k]
            i = len(w["camino"])
            if i >= N[k]:
                continue
            quedan = N[k] - 1 - i - RESERVA[k]          # pasos después de éste, antes de la reserva
            aqui = w["pila"][-1]
            nuevos = [v for v in labs[k][aqui] if v not in w["visto"]]
            puede_ir = len(w["pila"]) <= quedan       # tras avanzar, la distancia a casa cabe
            otro = W["abajo" if k == "arriba" else "arriba"]["camino"][-1]
            if nuevos and puede_ir:
                meta = rmin + (rmax - rmin) * tension(beat / TIEMPOS)
                r = [rug_acordes(v, otro) if k == "arriba" else rug_acordes(otro, v) for v in nuevos]
                orden = np.argsort(np.abs(np.array(r) - meta))
                v = nuevos[int(orden[0 if len(orden) == 1 or rng.random() < 0.7 else 1])]
                w["visto"].add(v)
                w["pila"].append(v)
                w["regresando"] = False
            elif len(w["pila"]) > 1:
                if nuevos and not puede_ir and w["vuelta"] is None:
                    w["vuelta"] = i
                elif not nuevos and not w["regresando"] and w["vuelta"] is None:
                    w["callejones"].append(i - 1)
                w["regresando"] = True
                w["pila"].pop()
                v = w["pila"][-1]
            else:
                v = aqui                                 # en casa: se queda
            w["camino"].append(v)
    return W


def estimar_rango(rng, todos):
    r = [rug_acordes(todos[int(rng.integers(len(todos)))], todos[int(rng.integers(len(todos)))]) for _ in range(300)]
    return float(np.percentile(r, 5)), float(np.percentile(r, 95))


# ---------------------------------------------------------------- piano
def cimbalon(f, dur, rng, vel=1.0):
    """El comentario de v1.1: dos cuerdas que baten, martillo, notas cortas. Suena a cimbalón."""
    n = int((dur + 1.2) * SR)
    t = np.arange(n) / SR
    B = 0.00025
    x = np.zeros(n)
    for k in range(1, 28):
        fk = f * k * np.sqrt(1 + B * k * k)
        if fk > 9000:
            break
        a = (1 / k ** 1.1) / np.sqrt(1 + (fk / 2200) ** 2)
        tau = 2.5 / (1 + 0.25 * k) * (220 / f) ** 0.4
        for d in (-0.15, 0.15):
            x += 0.5 * a * np.sin(2 * np.pi * (fk + d) * t + rng.uniform(0, 6)) * np.exp(-t / tau)
    x += 0.15 * rng.standard_normal(n) * np.exp(-t / 0.004)
    e = np.ones(n)
    nr = int(0.25 * SR)
    fin = min(n, int((dur + 0.05) * SR))
    e[fin:] = 0
    e[max(0, fin - nr):fin] *= np.linspace(1, 0, min(nr, fin))
    return vel * x * e / 3


def piano(f, dur, rng, vel=1.0):
    """Piano: una cuerda (tres casi al unísono), martillo blando, se deja sonar; oscuro."""
    n = int((dur + 1.8) * SR)
    t = np.arange(n) / SR
    B = 0.0004
    x = np.zeros(n)
    for k in range(1, 24):
        fk = f * k * np.sqrt(1 + B * k * k)
        if fk > 7000:
            break
        a = (1 / k ** 1.4) / np.sqrt(1 + (fk / 1700) ** 2) * (1 + 0.6 * np.exp(-0.5 * ((k - 3) / 1.5) ** 2))
        tau1 = 0.9 / (1 + 0.3 * k) * (220 / f) ** 0.5   # caída rápida
        tau2 = 4.0 / (1 + 0.3 * k) * (220 / f) ** 0.5   # cola larga (dos etapas, como el piano)
        ph = rng.uniform(0, 6)
        for d, g in ((0.0, 0.6), (0.04, 0.4)):
            x += g * a * np.sin(2 * np.pi * (fk + d) * t + ph) * (0.6 * np.exp(-t / tau1) + 0.4 * np.exp(-t / tau2))
    sos = __import__("scipy.signal", fromlist=["butter"]).butter(2, [200, 2500], btype="band", fs=SR, output="sos")
    x += 0.04 * __import__("scipy.signal", fromlist=["sosfilt"]).sosfilt(sos, rng.standard_normal(n)) * np.exp(-t / 0.01)
    e = np.ones(n)
    fin = min(n, int((dur + 0.3) * SR))
    nr = int(0.35 * SR)
    e[fin:] = 0
    e[max(0, fin - nr):fin] *= np.linspace(1, 0, min(nr, fin))
    return vel * x * e / 2.5


def fm(f, dur, rng, vel=1.0):
    """Piano eléctrico oscuro de FM (el de los ganchos v0)."""
    import ganchos
    return 0.6 * ganchos.lead("fm", f, dur, rng, vel)


COMENTARIOS = {"cimbalon": (cimbalon, 2), "piano": (piano, 4), "fm": (fm, 3), "ninguno": (None, 0),
               "choque-etiope": (piano, 0), "choque-jazz": (piano, 0),
               "choque-indostani": (piano, 0), "choque-hibrida": (piano, 0),
               "choque-etiope-clara": (piano, 0), "choque-jazz-clara": (piano, 0),
               "choque-indostani-clara": (piano, 0), "choque-hibrida-clara": (piano, 0)}


def voz_sostenida(f, dur, rng, brillo=2000, ataque=0.35):
    """Voz de muro: armónicos 1–8 sin desafinación propia, para que los batimientos sean del choque."""
    n = int((dur + 0.6) * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for fk, a in parciales_de(f, 1.0):
        x += a / np.sqrt(1 + (fk / brillo) ** 4) * np.sin(2 * np.pi * fk * t + rng.uniform(0, 6))
    resp = 1 + 0.1 * np.sin(2 * np.pi * rng.uniform(0.08, 0.2) * t + rng.uniform(0, 6))
    return x * resp * A.env_adsr(n, ataque, 1.0, 0.85, 0.55)


# ---------------------------------------------------------------- tema
def tema(semilla, comentario="cimbalon", instrumento="piano"):
    rng = np.random.default_rng(semilla)
    rc = np.random.default_rng(semilla + 1000)      # el comentario no mueve el azar del muro
    ri = np.random.default_rng(semilla + 2000)      # el instrumento no mueve el azar del comentario
    ra = np.random.default_rng(semilla + 4000)      # las gotas tampoco
    rp = np.random.default_rng(semilla + 5000)      # ni el tambor parlante
    rpj = np.random.default_rng(semilla + 6000)     # ni los pájaros
    rpr = np.random.default_rng(semilla + 9000)     # el principal hecho pájaro (rubatos, sombras, decisiones)
    prin = None
    if PRINCIPAL in ("persistente", "aprende"):
        import principal as PR
        prin = PR.Principal(np.random.default_rng(semilla + 9100), PRINCIPAL, PRINCIPAL_GUARDA, VERICUETOS, CRECER)
    if PRINCIPAL:
        import instrumentos as _I
        _I.ARTICULAR = True
    agua_ultimo, rasgo_pendiente, regalos, devoluciones = None, None, [], []
    toca, largo = COMENTARIOS[comentario]
    todos = [c for c in __import__("itertools").combinations(RANGO, N_VOCES) if valido(c)]
    lab_o, lab_u = laberinto(rng, CASA), laberinto(rng, CASA_ABAJO or CASA)
    rmin, rmax = estimar_rango(rng, todos)
    W = caminar_juntos(rng, {"arriba": lab_o, "abajo": lab_u}, rmin, rmax)
    cam_o, cal_o = W["arriba"]["camino"], W["arriba"]["callejones"]
    cam_u, cal_u = W["abajo"]["camino"], W["abajo"]["callejones"]
    total = TIEMPOS * BEAT + 4
    P = {k: A.Pista(total) for k in ("arriba", "abajo", "bajo", "piano", "sombras", "bombo", "hats", "gotas_i", "gotas_d", "tambor", "pajaros_i", "pajaros_d", "resuena")}
    es_choque = comentario.startswith("choque-")

    def segmentos(camino, paso_t):
        """Por voz: tramos en que la nota no cambia (una voz se mueve por paso)."""
        out = []
        for v in range(len(camino[0])):
            t0, val = 0, camino[0][v]
            for i, c in enumerate(camino[1:], 1):
                if c[v] != val:
                    out.append((v, val, t0 * paso_t * BEAT, (i - t0) * paso_t * BEAT, t0 > 0))
                    t0, val = i, c[v]
            out.append((v, val, t0 * paso_t * BEAT, (len(camino) - t0) * paso_t * BEAT, t0 > 0))
        return out

    for v, n, t, d, movida in segmentos(cam_o, PASO_ARRIBA):
        P["arriba"].pon(t, voz_sostenida(F0 * n, d, rng, MURO_BRILLO[0], 0.12 if movida else 1.2))
        if BAJO_DE == "arriba" and v == 0:   # de día: el armónico es el cimiento
            fb = F0 * n / 2
            while fb > 120:
                fb /= 2
            P["bajo"].pon(t, 0.8 * A.voz_bajo(fb, min(d, 4 * BEAT), rng))
    for v, m, t, d, movida in segmentos(cam_u, PASO_ABAJO):
        P["abajo"].pon(t, A.voz_pad(FU / m, d, rng, 0.3, MURO_BRILLO[1]))
        if BAJO_DE == "abajo" and v == len(cam_u[0]) - 1:   # divisor mayor = nota más grave: el bajo
            P["bajo"].pon(t, 0.8 * A.voz_bajo(FU / m / 2, min(d, 4 * BEAT), rng))

    # piano de Monk: célula de 3 notas desplazada cada 3 dieciseisavos, nota gemela chafada
    paso16 = BEAT / 4
    despl = 0
    choques = []
    for i in range(1, len(cam_o)):
        antes, ahora = cam_o[i - 1], cam_o[i]
        if antes == ahora or toca is None or es_choque:
            continue
        v = next(j for j in range(len(ahora)) if antes[j] != ahora[j])
        f_nueva, f_vieja = F0 * ahora[v], F0 * antes[v]
        t = i * PASO_ARRIBA * BEAT + despl * paso16
        despl = (despl + 3) % 12
        celda = [f_nueva, f_vieja, f_nueva * 2] if rc.random() < 0.5 else [f_nueva, f_nueva * 2, f_vieja]
        for j, f in enumerate(celda):
            tj = t + j * 3 * paso16 + rc.normal(0, 0.004)
            g = gemela(f)
            if g and j == 0:
                P["piano"].pon(tj - 0.025, toca(g[0], 0.05, rc, 0.55))
                choques.append({"t": round(tj, 3), "nota": round(f, 2), "gemela": round(g[0], 2), "cents": round(g[1], 1)})
            P["piano"].pon(tj, toca(f, largo * paso16, rc, 0.9 if j == 0 else 0.7))
        if (i - 1) in cal_o:  # callejón: escalera de armónicos que baja de dos en dos
            top = max(ahora)
            for j, n in enumerate(range(top + 6, top - 4, -2)):
                P["piano"].pon(t + 2 * BEAT + j * paso16 * 1.5, toca(F0 * n, paso16 * 1.4, rc, 0.6))

    # visitas a flores: la escala del choque, con sombras subarmónicas que vibran
    visitas = []
    if es_choque:
        import escalas_choque as E
        version = comentario.split("-", 1)[1]
        lente = None
        for i in range(1, len(cam_o)):
            antes, ahora = cam_o[i - 1], cam_o[i]
            if antes == ahora or rc.random() < SILENCIO:     # a veces no se visita: silencio
                continue
            t_paso = i * PASO_ARRIBA * BEAT
            cu = cam_u[min(len(cam_u) - 1, int(t_paso / (PASO_ABAJO * BEAT)))]
            if lente is None or rc.random() < 0.3:
                lente = E.escoger_lente(rc, version)
            nombre, plantilla, gram = lente
            v = next(j for j in range(len(ahora)) if antes[j] != ahora[j])
            comun = [F0 * n for n in ahora for m in cu if abs(F0 * n - FU / m) < 1e-6]
            ton = comun[0] if comun else F0 * ahora[v]
            while ton < 300:
                ton *= 2
            while ton > 600:
                ton /= 2
            escala = E.afinar(ton, plantilla, E.poza(ahora, cu, gemela))
            notas = E.frase(rc, gram, escala, gemela)
            if not notas:
                continue
            ks = sorted(rc.choice([2, 3, 4, 5, 6], int(rc.choice([1, 2])), replace=False).tolist())
            batido = float(rc.uniform(*BATIDO))                # Hz entre la nota y cada sombra
            signo = float(rc.choice([-1, 1]))
            off = int(rc.choice([0, 1, 2, 3, 5, 6]))
            funcion = None
            jit = rc if PRINCIPAL is None else rpr        # con PRINCIPAL, el azar de las notas no mueve las visitas
            if prin is not None:
                extra = {"progreso": t_paso / (TIEMPOS * BEAT), "gemela": gemela} if (VERICUETOS or CRECER) else {}
                notas, funcion = prin.frase(rpr, [e["hz"] for e in escala],
                                            agua_ultimo if PRINCIPAL == "aprende" else None, rasgo_pendiente, **extra)
                notas = [(p, f, d, vel, "repetida" if a == "eco" else a) for p, f, d, vel, a in notas]
                if not (PRINCIPAL_GUARDA and funcion.split("+")[0] == "calla"):
                    agua_ultimo, rasgo_pendiente = None, None
            elif PRINCIPAL == "azar":
                funcion = "azar"
            linea = []
            for p, f, d, vel, adorno in notas:
                tt = t_paso + (off + p) * paso16 + jit.normal(0, 0.004)
                if instrumento == "piano":
                    P["piano"].pon(tt, piano(f, d * paso16 + 0.1, rc, vel))
                else:
                    linea.append((tt, f, d * paso16, vel))
                if adorno in ("meend", "aproximación"):
                    continue
                for k in ks:
                    fs = f / k + signo * batido / k
                    P["sombras"].pon(tt, (0.8 * vel / k ** 0.3) * voz_sostenida(fs, d * paso16 + 0.5, jit, 1800, 0.05))
            if linea:
                import instrumentos as I
                quien = instrumento if instrumento != "ensamble" else ENSAMBLE[int(ri.integers(len(ENSAMBLE)))]
                t0l, audio = I.tocar_frase(quien, linea, ri)
                P["piano"].pon(t0l, audio)
            salpicadura = []
            agua_arpa = None
            if AGUA:      # tocar el agua: gotas-burbuja afinadas a la escala del choque
                import agua
                hizo_arpa = any(a == "arpa" for _, _, _, _, a in notas)
                if AGUA_ARPA and (hizo_arpa or ra.random() < 0.1 + 0.3 * t_paso / (TIEMPOS * BEAT)):
                    # el agua contesta a la carrera con la misma escala, en sentido contrario, al terminar la frase
                    fin = t_paso + (off + max(p + d for p, _, d, _, _ in notas)) * paso16 if notas else t_paso + off * paso16
                    sube = not (hizo_arpa and notas[-1][1] > notas[0][1])
                    salpicadura = agua.arpa(ra, [e["hz"] for e in escala], [e["fuente"] for e in escala],
                                            fin + 0.25 if hizo_arpa else t_paso + off * paso16, sube)
                    agua_arpa = {"t": round(salpicadura[0]["t"], 3), "sube": sube, "gotas": len(salpicadura),
                                 "contesta_carrera": hizo_arpa} if salpicadura else None
                else:
                    salpicadura = agua.salpicar(ra, [e["hz"] for e in escala], [e["fuente"] for e in escala],
                                                t_paso + off * paso16, GOTAS["n"], GOTAS["octavas"])
                for gt in salpicadura:
                    x = agua.burbuja(gt, ra)
                    P["gotas_i"].pon(gt["t"], x * np.sqrt((1 - gt["pan"]) / 2))
                    P["gotas_d"].pon(gt["t"], x * np.sqrt((1 + gt["pan"]) / 2))
            canto = []
            if AGUA and PAJAROS and salpicadura and rpj.random() < 0.5:   # el agua resuena y contesta un pájaro
                import pajaros
                cantos, canto = pajaros.cantar(rpj, [e["hz"] for e in escala], salpicadura[-1]["t"] + rpj.uniform(0.2, 0.8),
                                               PAJAROS_VOZ["lo"], PAJAROS_VOZ["hi"], PAJAROS_VOZ["corte"])
                for tc, x, pan in cantos:
                    P["pajaros_i"].pon(tc, x * np.sqrt((1 - pan) / 2))
                    P["pajaros_d"].pon(tc, x * np.sqrt((1 + pan) / 2))
            if not notas:                                 # el principal calla: el jardín sigue (agua, aves, tambor)
                notas_calla = True
            else:
                notas_calla = False
            habla = []
            if PARLANTE and not notas_calla and rp.random() < 0.75:   # el tambor contesta al terminar la frase (casi siempre)
                import parlante
                t_fin = t_paso + (off + max(p + d for p, _, d, _, _ in notas) + 1) * paso16
                golpes, habla = parlante.frase(rp, [e["hz"] for e in escala], t_fin, unidad=paso16 * 2)
                for tg, a in golpes:
                    P["tambor"].pon(tg, a)
            t_fin_linea = t_paso + (off + (max(p + d for p, _, d, _, _ in notas) if notas else 0)) * paso16
            devuelve = None
            if AGUA_CANTA and notas and len(notas) >= 2:  # el agua guarda la huella y la devuelve cantabile
                import agua
                dos = sorted(sorted(notas, key=lambda n: -n[2])[:2], key=lambda n: n[0])
                sep = (dos[1][0] - dos[0][0]) * paso16
                td = t_fin_linea + float(rpr.uniform(1.0, 2.5))
                x = agua.canto(dos[0][1], dos[1][1], sep, rpr)
                pan = float(rpr.uniform(-0.6, 0.6))
                P["gotas_i"].pon(td, x * np.sqrt((1 - pan) / 2))
                P["gotas_d"].pon(td, x * np.sqrt((1 + pan) / 2))
                devuelve = {"t": round(td, 3), "a_hz": round(dos[0][1], 2), "b_hz": round(dos[1][1], 2), "separacion_s": round(sep, 3)}
                devoluciones.append(devuelve)
                if PRINCIPAL == "aprende":
                    agua_ultimo = dos[1][1]                 # la siguiente frase puede arrancar donde terminó el agua
                    if rasgo_pendiente is None:
                        import principal as PR
                        e_hz = [e["hz"] for e in escala]
                        rasgo_pendiente = {"tipo": "intervalo", "paso": PR.mas_cercano(e_hz, dos[1][1]) - PR.mas_cercano(e_hz, dos[0][1])}
            regalo = None
            if PRINCIPAL == "aprende" and AVES and notas and rpr.random() < 0.45:   # el cenzontle regala un final
                import principal as PR
                nh, rasgo = PR.regalo_del_cenzontle(rpr, [n[1] for n in notas], [e["hz"] for e in escala])
                if nh:
                    regalo = {"t": round(t_fin_linea + float(rpr.uniform(0.5, 1.2)), 3), "notas": [round(f, 2) for f in nh], "paso": rasgo["paso"]}
                    regalos.append(regalo)
                    rasgo_pendiente = rasgo
            visitas.append({"t": round(t_paso, 3), "t_fin": round(t_fin_linea, 3), "funcion": funcion, "agua_devuelve": devuelve,
                            "agua_arpa": agua_arpa,
                            "regalo": regalo, "pajaros": canto, "parlante": habla, "instrumento": quien if linea else instrumento, "lente": nombre, "gramatica": gram, "tonica_hz": round(ton, 3),
                            "escala": [{k2: (round(v2, 3) if isinstance(v2, float) else v2) for k2, v2 in e.items()} for e in escala],
                            "notas": [{"paso16": round(off + p, 2), "hz": round(f, 3), "dur16": d, "adorno": a} for p, f, d, _, a in notas],
                            "sombras_k": ks, "batido_hz": round(batido, 2)})

    # el dùndún libre: frases propias a su tiempo, con las notas que suena el muro ahora y,
    # si hubo una flor hace poco, con la escala de esa flor (memoria)
    libre = []
    if TAMBOR_LIBRE > 0:
        import parlante
        rtl = np.random.default_rng(semilla + 7000)
        t = float(rtl.uniform(1, 4))
        prev = None
        fin = TIEMPOS * BEAT - 2
        while t < fin:
            co = cam_o[min(len(cam_o) - 1, int(t / (PASO_ARRIBA * BEAT)))]
            cu = cam_u[min(len(cam_u) - 1, int(t / (PASO_ABAJO * BEAT)))]
            notas_ahora = [F0 * n for n in co] + [FU / m for m in cu]
            recientes = [v for v in visitas if 0 <= t - v["t"] < 8]
            if recientes and rtl.random() < 0.5:
                notas_ahora = [e["hz"] for e in recientes[-1]["escala"]]
            golpes, reg, prev = parlante.frase_libre(rtl, notas_ahora, t, prev, unidad=BEAT / 4 * float(rtl.choice([1.5, 2, 3])))
            for tg, a in golpes:
                if tg < fin + 1:
                    P["tambor"].pon(tg, 0.85 * a)
            libre.append({"t": round(t, 3), "golpes": reg, "memoria": bool(recientes)})
            dur = (reg[-1]["t"] - t) if reg else 1.0
            t += dur + float(rtl.exponential(5.0 / TAMBOR_LIBRE)) + 0.8

    # el coro de aves: a su tiempo, en los huecos de la línea, presienten e imitan
    aves_reg = None
    if AVES:
        import aves as AV
        rav = np.random.default_rng(semilla + 8000)
        tramos = sorted((v["t"] + n["paso16"] * paso16, v["t"] + (n["paso16"] + n["dur16"]) * paso16)
                        for v in visitas for n in v["notas"])

        def ocupado(t):
            return any(a - 0.15 <= t <= b + 0.25 for a, b in tramos)

        def escala_en(t):
            recientes = [v for v in visitas if 0 <= t - v["t"] < 6]
            if recientes:
                return [e["hz"] for e in recientes[-1]["escala"]]
            co = cam_o[min(len(cam_o) - 1, int(t / (PASO_ARRIBA * BEAT)))]
            cu = cam_u[min(len(cam_u) - 1, int(t / (PASO_ABAJO * BEAT)))]
            return [F0 * n for n in co] + [FU / m for m in cu]

        perfil = dict(AVES, regalos=regalos, nicho_completo=bool(PRINCIPAL))
        cantos, registro_aves, descripcion = AV.coro(rav, perfil, TIEMPOS * BEAT, ocupado, escala_en, visitas)
        for tc, x, pan in cantos:
            P["pajaros_i"].pon(tc, x * np.sqrt((1 - pan) / 2))
            P["pajaros_d"].pon(tc, x * np.sqrt((1 + pan) / 2))
        aves_reg = {"aves": descripcion, "cantos": registro_aves}
        # resonancia simpática: si un ave canta cerca (±40 cents) de un parcial del muro, ese parcial se enciende
        if RESONANCIA_AVES:
            encendidos = []
            tt = np.arange(int(2.6 * SR)) / SR
            for e in registro_aves:
                if e.get("callo") or not e.get("hz"):
                    continue
                co = cam_o[min(len(cam_o) - 1, int(e["t"] / (PASO_ARRIBA * BEAT)))]
                cu = cam_u[min(len(cam_u) - 1, int(e["t"] / (PASO_ABAJO * BEAT)))]
                parciales = [F0 * n * h for n in co for h in range(1, 13)] + [FU / m * h for m in cu for h in range(1, 13)]
                for f in sorted(set(e["hz"])):
                    p = min(parciales, key=lambda q: abs(np.log2(q / f)))
                    if abs(1200 * np.log2(p / f)) <= 40:
                        x = np.sin(2 * np.pi * p * tt) * (1 - np.exp(-tt / 0.12)) * np.exp(-tt / 0.9)
                        x += 0.3 * np.sin(2 * np.pi * (p / 2) * tt) * (1 - np.exp(-tt / 0.3)) * np.exp(-tt / 1.3)
                        P["resuena"].pon(e["t"] + 0.08, x)
                        encendidos.append({"t": e["t"], "ave_hz": f, "parcial_hz": round(p, 2), "cents": round(1200 * np.log2(p / f), 1)})
            aves_reg["muro_encendido"] = encendidos

    # cuando la flauta se retira, el agua guarda el recuerdo: devuelve dos veces su canto
    if prin is not None and AGUA_CANTA and visitas:
        import agua
        ult = max(v["t_fin"] for v in visitas if v["notas"]) if any(v["notas"] for v in visitas) else None
        if ult is not None:
            c = prin.canto
            ref = prin.ultima_hz or 440.0
            for k, dt in enumerate((5.0, 13.0)):
                if ult + dt < TIEMPOS * BEAT - 3:
                    x = agua.canto(ref, ref * (1.25 if k == 0 else 1.125), c["ritmo"][0] * paso16, rpr, 0.7)
                    P["gotas_i"].pon(ult + dt, x * 0.7)
                    P["gotas_d"].pon(ult + dt, x * 0.7)
                    devoluciones.append({"t": round(ult + dt, 3), "recuerdo": True})

    # pulso discreto: el ritmo acompaña, no manda
    PULSO(P, rng)
    if BORDON:   # bordón de casa (como tanpura): la nota más grave y su quinta, todo el tiempo
        rb = np.random.default_rng(semilla + 3000)
        raiz = min(F0 * n for n in CASA)
        while raiz > 140:
            raiz /= 2
        for f, g in ((raiz, 0.5), (raiz * 1.5, 0.3), (raiz * 2, 0.25)):
            P["abajo"].pon(0, g * voz_sostenida(f, TIEMPOS * BEAT + 1.5, rb, 1500, 2.5))

    # cierre: los dos últimos acordes juntos
    tf = TIEMPOS * BEAT
    for n in cam_o[-1]:
        P["arriba"].pon(tf, 0.7 * voz_sostenida(F0 * n, 2.5, rng, 1800, 0.3))
    for m in cam_u[-1]:
        P["abajo"].pon(tf, 0.8 * A.voz_pad(FU / m, 2.5, rng, 0.3, 1100))

    # rugosidad del muro (sin piano), en una rejilla de medio tiempo
    curva, coinc = [], []
    for k in range(TIEMPOS * 2):
        tt = k * BEAT / 2
        co = cam_o[min(len(cam_o) - 1, int(tt / (PASO_ARRIBA * BEAT)))]
        cu = cam_u[min(len(cam_u) - 1, int(tt / (PASO_ABAJO * BEAT)))]
        parc = [p for n in co for p in parciales_de(F0 * n, 1.0)] + [p for m in cu for p in parciales_de(FU / m, 1.0)]
        solo = [p for n in co for p in parciales_de(F0 * n, 1.0)]
        curva.append((round(tt, 3), round(rugosidad(parc), 4), round(rugosidad(solo), 4)))
        # coincidencia exacta (en cualquier octava): n·m·F0/FU es potencia de 2 (n·m/120 en K = 120)
        exactas = [n for n in co for m in cu if abs(np.log2(n * m * F0 / FU) - round(np.log2(n * m * F0 / FU))) < 1e-9]
        coinc.append(len(exactas))
    gen = {"semilla": semilla, "comentario": comentario, "instrumento": instrumento, "camino_arriba_n": cam_o, "camino_abajo_m": cam_u,
           "callejones_arriba": cal_o, "callejones_abajo": cal_u,
           "nodos_laberinto": [len(lab_o), len(lab_u)], "bpm": BPM,
           "rango_rugosidad_p5_p95": [round(rmin, 3), round(rmax, 3)],
           "vuelta_arriba": W["arriba"]["vuelta"], "vuelta_abajo": W["abajo"]["vuelta"],
           "rugosidad": curva, "coincidencias_por_medio_tiempo": coinc, "choques_piano": choques, "visitas": visitas, "tambor_libre": libre, "aves": aves_reg,
           "principal": ({"modo": PRINCIPAL, "canto": prin.canto, "herencia_final": prin.herencia} if prin else {"modo": PRINCIPAL}),
           "devoluciones_del_agua": devoluciones, "regalos": regalos}
    return P, total, gen


def pulso_discreto(P, rng):
    for b in range(0, TIEMPOS, 4):
        P["bombo"].pon(b * BEAT, 0.7 * A.bombo(rng))
        for p in (1, 2, 3):
            P["hats"].pon(b * BEAT + p * BEAT + rng.normal(0, 0.004), 0.35 * (0.6 + 0.4 * rng.random()) * A.hat(rng))


PULSO = pulso_discreto


def mezclar(P, semilla):
    rng = np.random.default_rng(semilla + 7)
    G = {"arriba": -15, "abajo": -14, "bajo": -12, "piano": -13, "sombras": -17, "bombo": -15, "hats": -30,
         "gotas_i": -15, "gotas_d": -15, "tambor": -19, "pajaros_i": -25, "pajaros_d": -25, "resuena": -16}
    G = {k: v + MEZCLA_EXTRA.get(k, 0) for k, v in G.items()}
    PAN = {"arriba": -0.25, "abajo": 0.2, "bajo": 0, "piano": 0.1, "sombras": -0.05, "bombo": 0, "hats": 0.35,
           "gotas_i": -0.85, "gotas_d": 0.85, "tambor": 0.15, "pajaros_i": -0.9, "pajaros_d": 0.9, "resuena": 0.0}
    SALA = {"arriba": 0.45, "abajo": 0.5, "bajo": 0.05, "piano": 0.35, "sombras": 0.55, "bombo": 0.05, "hats": 0.2,
            "gotas_i": 0.5, "gotas_d": 0.5, "tambor": 0.35, "pajaros_i": 0.9, "pajaros_d": 0.9, "resuena": 0.6}
    SALA = {k: SALA_EXTRA.get(k, v) for k, v in SALA.items()}
    # v1.9.1: la resonancia de las aves se nivela sola, 8 dB bajo las aves de ESA canción (con muchos
    # encendidos encimados, normalizar por pico la hundía de 12 a 19 dB y no se oía)
    ajuste_res = 0.0
    if RESONANCIA_AVES and np.any(P["resuena"].x) and np.any(P["pajaros_i"].x) :
        def _norm(k):
            x = P[k].x
            if k in NORMA_PICO:
                return x / (np.max(np.abs(x)) + 1e-12) * 10 ** (G[k] / 20)
            return x / (np.sqrt(np.mean(x ** 2)) + 1e-12) * 10 ** (G[k] / 20)

        def _activo(x):
            w = 2400
            m = len(x) // w
            r = np.sqrt(np.mean(x[: m * w].reshape(m, w) ** 2, axis=1))
            on = r > 0.01 * r.max()
            return 20 * np.log10(np.mean(r[on]) + 1e-12)
        ajuste_res = (_activo(_norm("pajaros_i") + _norm("pajaros_d")) - 8.0) - _activo(_norm("resuena"))
    cede = None
    if CEDE:   # la línea del instrumento manda: gotas y pájaros bajan hasta 8 dB mientras suena
        from scipy.signal import lfilter as _lf
        a = np.exp(-1 / (0.08 * SR))
        env = _lf([1 - a], [1, -a], np.abs(P["piano"].x))
        env = np.clip(env / (np.percentile(env[env > 1e-6], 95) + 1e-12), 0, 1) if np.any(env > 1e-6) else env
        cede = 1 - 0.6 * env
    n = len(P["arriba"].x)
    seco, envio = np.zeros((n, 2)), np.zeros((n, 2))
    for k, p in P.items():
        if k in NORMA_PICO:
            x = p.x / (np.max(np.abs(p.x)) + 1e-12) * 10 ** (G[k] / 20)
        else:
            x = p.x / (np.sqrt(np.mean(p.x ** 2)) + 1e-12) * 10 ** (G[k] / 20)
        if k == "resuena":
            x = x * 10 ** (ajuste_res / 20)
        if cede is not None and k.startswith(("gotas", "pajaros")):
            x = x * cede
        st = np.stack([x * np.sqrt((1 - PAN[k]) / 2), x * np.sqrt((1 + PAN[k]) / 2)], 1)
        seco += st
        envio += st * SALA[k]
    ir = A.ir_sala(rng, 3.0, 1.0, 4500)
    mix = seco + np.stack([fftconvolve(envio[:, c], ir[:, c])[:n] for c in range(2)], 1)
    if MEZCLA_TECHO:
        mix = mix / np.max(np.abs(mix)) * MEZCLA_TECHO
    mix = np.tanh(mix * 1.1) / 1.1
    return mix / np.max(np.abs(mix)) * 0.89


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--semillas", type=int, nargs="*", default=[3, 14, 59, 265])
    ap.add_argument("--comentarios", nargs="*", default=["cimbalon"], choices=list(COMENTARIOS))
    ap.add_argument("--instrumentos", nargs="*", default=["piano"], choices=["piano", "voz", "farfisa", "flauta", "cuerda",
                                                                       "theremin", "trautonium", "ondas", "hammond", "ensamble"])
    ap.add_argument("--salida", default=str(Path(__file__).resolve().parent.parent / "estudios"))
    args = ap.parse_args()
    codigo = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    nonce = secrets.token_hex(16)
    ejec = hashlib.sha256((PROGRAMA + codigo + ",".join(map(str, args.semillas)) + ",".join(args.comentarios) + ",".join(args.instrumentos) + nonce).encode()).hexdigest()
    corto = ejec[:12]
    carpeta = Path(args.salida) / f"laberintos-de-afinidad-{corto}"
    carpeta.mkdir(exist_ok=False)
    tmp = Path(tempfile.mkdtemp(prefix="laberintos-"))
    reg = {"ejecucion_sha256": ejec, "nonce": nonce, "codigo_sha256": codigo, "programa": PROGRAMA,
           "F0": F0, "FU": FU, "semillas": args.semillas, "comentarios": args.comentarios,
           "instrumentos": args.instrumentos, "temas": {}}
    if any(i == "voz" for i in args.instrumentos):
        import instrumentos as I
        reg["procedencia_voz"] = I.procedencia_banco()
    mezclas = []
    for s, com, ins in [(s, c, i) for s in args.semillas for c in args.comentarios for i in args.instrumentos]:
        P, total, gen = tema(s, com, ins)
        com = com if ins == "piano" else f"{com}-{ins}"
        mix = mezclar(P, s)[: int((total + 0.5) * SR)]
        wav = tmp / f"s{s}-{com}.wav"
        A.escribir_wav(wav, mix)
        dest = carpeta / f"laberinto-s{s}-{com}-{corto}.m4a"
        A.m4a(wav, dest)
        mezclas.append(mix / np.sqrt(np.mean(mix ** 2)) * 0.12)
        r = np.array([c[1] for c in gen["rugosidad"]])
        gen.update({"archivo": dest.name, "contenido_sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
                    "duracion_s": round(len(mix) / SR, 2), "finito": bool(np.all(np.isfinite(mix))),
                    "bandas": A.balance(mix),
                    "rugosidad_resumen": {"min": round(float(r.min()), 3), "max": round(float(r.max()), 3),
                                          "media": round(float(r.mean()), 3),
                                          "medios_tiempos_con_coincidencia": int(np.sum(np.array(gen["coincidencias_por_medio_tiempo"]) > 0))}})
        reg["temas"][f"{s}-{com}"] = gen
        print(f"s{s} {com}: laberintos {gen['nodos_laberinto']}  callejones {len(gen['callejones_arriba'])}/{len(gen['callejones_abajo'])}  "
              f"rugosidad {gen['rugosidad_resumen']}  choques de piano {len(gen['choques_piano'])}  {gen['duracion_s']} s", flush=True)
    hueco = np.zeros((SR, 2))
    tejido = np.concatenate(sum([[m, hueco] for m in mezclas], [])[:-1])
    A.escribir_wav(tmp / "tejido.wav", tejido / np.max(np.abs(tejido)) * 0.89)
    dest = carpeta / f"laberintos-tejidos-{corto}.m4a"
    A.m4a(tmp / "tejido.wav", dest)
    reg["tejido"] = {"archivo": dest.name, "contenido_sha256": hashlib.sha256(dest.read_bytes()).hexdigest()}
    with open(carpeta / f"receta-{corto}.json", "x", encoding="utf-8") as fh:
        json.dump(reg, fh, ensure_ascii=False)
    print(carpeta)


if __name__ == "__main__":
    main()
