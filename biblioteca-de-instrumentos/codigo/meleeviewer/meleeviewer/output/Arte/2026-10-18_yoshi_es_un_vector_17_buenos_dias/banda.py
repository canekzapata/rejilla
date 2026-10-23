"""La banda de «buenos días» (yoshi es un vector, parte 17): instrumentos nuevos, cada uno con una idea verdadera.

  luz        la luz del SOL bajada 40 octavas: un ruido con la forma exacta de la curva de Planck a 5772 K (pico en
             308.6 Hz). Es todos los colores a la vez: por eso es ruido. Entra por la ventana: resuena en los parciales
             del acorde. Sube con el sol (la elevación es una curva sobre la canción).
  granitos   en «viene en granitos de luz» la luz se vuelve fotones: granos cortos que llegan como un proceso de
             Poisson (ruido de disparo), cada uno con una frecuencia sorteada de la distribución de fotones de Planck.
  pixeles    la luz de la PANTALLA bajada 40 octavas: tres tonos puros, los primarios del sRGB (≈612, 547 y 465 nm →
             445.5, 498.5 y 586.4 Hz: La+22c, Si+16c, Re−3c) con el parpadeo de 60 Hz del PWM. Tres líneas, no un
             continuo. El renglón «rojo, verde y azul» canta esas tres notas.
  armonia    familia ARMÓNICA (n·f) para los acordes mayores y SUBARMÓNICA (F/n) para los menores y para la noche
             (el lenguaje del jardín): mayor = otonal, menor = utonal. Con el sol se abren parciales más altos.
  bajo       contrabajo pulsado (Karplus-Strong) que baja por grados.
  hammond    barras con Leslie (del jardín): el altavoz que gira es la Tierra que gira. En los coros.
  ondas      ondas Martenot (del jardín) con la «palme» afinada a Re: lo que toca hace sonar la casa por simpatía.
             Toca el motivo «buenos días» (La Si Re La) transformado: aumentado, invertido, retrógrado, fragmentado.
  flauta     en el alba, el motivo aumentado; el cenzontle lo imita.
  aves       el coro del alba (Réveil des oiseaux) con especies de aquí; callan donde canta la voz (nicho acústico)
             y adentro, con la pantalla.
  olla       el café de olla: el agua CANTA ANTES DE HERVIR (burbujas chicas que nacen y se colapsan, cada vez más y
             más agudas) y cuando hierve SE CALLA (burbujas grandes, graves y pocas). Gotas-arpa en la escala.
  parlante   tambor parlante (dùndún): dice el contorno de la letra. En cada día bisiesto, un deslizamiento.
  percusion  canción de cuna en 3/4: membrana grave en el 1, escobillas en el 2 y el 3; la cuchara en la taza.
  theremin   la coda: dobla la última frase, lejos.

    python banda.py   → render/stems/*.wav (48 kHz, estéreo, flotante) + eventos.json (para el video)
"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, sosfiltfilt, lfilter, fftconvolve

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import letra as L  # noqa: E402

TEMAS = AQUI.parents[3] / "netart" / "jardin-camara" / "musica" / "temas"
sys.path.insert(0, str(TEMAS))      # aves.py importa pajaros.py por nombre


def importa(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    m = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = m
    spec.loader.exec_module(m)
    return m


I = importa("instrumentos_jardin", TEMAS / "instrumentos.py")
AV = importa("aves_jardin", TEMAS / "aves.py")
AG = importa("agua_jardin", TEMAS / "agua.py")
PA = importa("parlante_jardin", TEMAS / "parlante.py")
I.CASA_HZ = [146.83, 220.0, 293.66, 369.99]      # la «palme» de las ondas, afinada a Re (en memoria: el archivo no se toca)

SR = 48000
N = int(L.LARGO * SR)
SEM = 1718
STEMS = AQUI / "render" / "stems"
STEMS.mkdir(parents=True, exist_ok=True)
EVENTOS = []        # (t, tipo, datos) para el video


def ev(t, tipo, **d):
    EVENTOS.append({"t": round(float(t), 4), "tipo": tipo, **d})


def hz(m):
    return 440 * 2 ** ((np.asarray(m, float) - 69) / 12)


def pc_hz(pc, octava):
    return float(hz(12 * (octava + 1) + pc))


def stereo():
    return np.zeros((2, N))


def pon(dst, t, x, pan=0.0, g=1.0):
    """Suma x (mono) en dst (2, N) a partir de t s, con paneo de potencia constante."""
    o = int(t * SR)
    if o >= N or len(x) == 0:
        return
    if o < 0:
        x, o = x[-o:], 0
    z = min(N, o + len(x))
    a = (pan + 1) * np.pi / 4
    dst[0, o:z] += g * np.cos(a) * x[:z - o]
    dst[1, o:z] += g * np.sin(a) * x[:z - o]


def bar_t(b):
    return L.tb(b)


def tiempo_a_bar(t):
    for b in range(L.NBAR):
        if t < bar_t(b + 1):
            return b
    return L.NBAR - 1


# ── el sol: elevación sobre la canción (0 = horizonte) ───────────────────────────────────────────────────────
def elevacion(t):
    """−1 de noche, 0 en el horizonte (inicio del verso, compás 8), 1 al mediodía de la canción (último coro)."""
    t = np.asarray(t, float)
    th = bar_t(8)
    tm = bar_t(76)
    return np.where(t < th, -1 + t / th, np.clip((t - th) / (tm - th), 0, 1) ** .7)


def es_menor(nombre):
    rp, pcs, _ = L.acorde(nombre)
    return (rp + 3) % 12 in pcs and (rp + 4) % 12 not in pcs


# ── armonía: familias armónica y subarmónica ─────────────────────────────────────────────────────────────────
def familia(b):
    """Frecuencias (Hz) y pesos del acorde del compás b. Mayor/dominante: n·f; menor y alba: F/n."""
    nombre = L.ACORDES[b]
    rp, pcs, _ = L.acorde(nombre)
    t = bar_t(b)
    sol = float(elevacion(t + .1))
    abre = int(np.clip(round(3 + 5 * max(0.0, sol)), 3, 8))          # cuántos colores se abren con el sol
    f0 = pc_hz(rp, 2)
    while f0 > 98:
        f0 /= 2
    if b < 8 or es_menor(nombre):
        # utonal: la tríada menor es F/6, F/5, F/4 (10:12:15) con la raíz en F/6
        F = 6 * f0 * 2
        ns = [4, 5, 6, 8, 10, 12, 7, 16][:abre]
        return [(F / n, 1 / (n / 4) ** .6) for n in ns], "sub"
    ns = [2, 3, 4, 5, 6, 8, 10, 12][:abre]
    if "7" in nombre:
        ns += [7, 14]
    if sol > .75:
        ns += [11, 13]                                                    # pleno día: los colores raros, bajitos
    return [(f0 * n, (1 / n ** .65) * (.35 if n in (11, 13) else 1)) for n in ns], "arm"


def armonia():
    out = stereo()
    luz_res = []
    rng = np.random.default_rng(SEM)
    for b in range(L.NBAR):
        if L.seccion(b) == "pantalla":
            continue                                                       # en la pantalla la armonía es otra luz
        parc, fam = familia(b)
        t0, t1 = bar_t(b) - .25, bar_t(b + 1) + .35
        n = int((t1 - t0) * SR)
        tt = np.arange(n) / SR
        env = np.clip(tt / .35, 0, 1) * np.clip((t1 - t0 - tt) / .45, 0, 1)
        for f, a in parc:
            for d, p in ((-.13, -.6), (.13, .6)):                          # dos copias que baten despacio
                x = np.sin(2 * np.pi * (f + d) * tt + rng.uniform(0, 6)) * a * env
                pon(out, t0, x, pan=p * min(1, f / 600), g=.5)
        luz_res.append((b, parc))
        ev(bar_t(b), "acorde", nombre=L.ACORDES[b], familia=fam, hz=[round(f, 2) for f, _ in parc])
    return out, luz_res


# ── la luz del sol: Planck bajado 40 octavas ─────────────────────────────────────────────────────────────────
OCT = 2.0 ** 40
H_K = 4.799243e-11      # h/k (K·s)
T_SOL = 5772.0


def planck_mag(f):
    x = H_K * f * OCT / T_SOL
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        p = np.where(f > 0, f ** 3 / np.expm1(x), 0)
    return np.sqrt(np.nan_to_num(p))


def ruido_planck(n, rng):
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    m = planck_mag(f)
    return np.fft.irfft(X * m / m.max(), n)


def luz(luz_res):
    rng = np.random.default_rng(SEM + 1)
    out = stereo()
    nz = np.stack([ruido_planck(N, rng), ruido_planck(N, rng)])
    nz /= np.abs(nz).max()
    t = np.arange(N) / SR
    sol = elevacion(t)
    adentro = np.ones(N)
    a, z = int(bar_t(48) * SR), int(bar_t(64) * SR)
    adentro[a:z] = .25                                                     # la persiana: en la pantalla, poca luz
    adentro = fftconvolve(adentro, np.hanning(SR) / np.hanning(SR).sum(), "same")
    crudo = np.clip(sol + .9, 0, 1.9) / 1.9 * adentro
    out += nz * crudo * .35
    # por la ventana: el mismo ruido resonando en los parciales del acorde
    for b, parc in luz_res:
        t0, t1 = bar_t(b) - .1, bar_t(b + 1) + .6
        a, z = int(t0 * SR), min(N, int(t1 * SR))
        seg = nz[:, a:z]
        e = np.clip(np.arange(z - a) / (.3 * SR), 0, 1) * np.clip((z - a - np.arange(z - a)) / (.5 * SR), 0, 1)
        y = np.zeros_like(seg)
        for f, w in parc:
            if f < 80 or f > 2500:
                continue
            for c in (0, 1):
                y[c] += w * I._resonador(seg[c], f, 1.2)
        out[:, a:z] += y * e * max(0.0, float(elevacion(t0)) + .3) * 2.2
    return out


def granitos():
    """Fotones: llegadas de Poisson; frecuencia sorteada de la distribución de fotones (n ∝ ν²/(e^x − 1))."""
    rng = np.random.default_rng(SEM + 2)
    out = stereo()
    f = np.linspace(20, 4000, 4000)
    x = H_K * f * OCT / T_SOL
    p = f ** 2 / np.expm1(x)
    p /= p.sum()
    for b0, b1, tasa0, tasa1 in ((24, 32, 4, 26), (88, 92, 3, 10)):
        t, fin = bar_t(b0), bar_t(b1)
        while t < fin:
            u = (t - bar_t(b0)) / (fin - bar_t(b0))
            t += rng.exponential(1 / (tasa0 + (tasa1 - tasa0) * u))
            fq = float(rng.choice(f, p=p)) * 2                             # una octava arriba: que se oigan como granos
            d = rng.uniform(.006, .02)
            tt = np.arange(int(d * SR)) / SR
            g = np.sin(2 * np.pi * fq * tt) * np.hanning(len(tt))
            pon(out, t, g, pan=float(rng.uniform(-.9, .9)), g=.5)
            if rng.random() < .25:
                ev(t, "foton", hz=round(fq, 1))
    return out


# ── la pantalla: tres líneas con parpadeo ────────────────────────────────────────────────────────────────────
C_LUZ = 299792458.0
RGB_NM = {"rojo": 612.0, "verde": 547.0, "azul": 465.0}
RGB_HZ = {k: C_LUZ / (v * 1e-9) / OCT for k, v in RGB_NM.items()}


def pixeles():
    rng = np.random.default_rng(SEM + 3)
    out = stereo()
    t0, t1 = bar_t(48) - .8, bar_t(64) + .3
    n = int((t1 - t0) * SR)
    tt = np.arange(n) / SR
    env = np.clip(tt / .8, 0, 1) * np.clip((t1 - t0 - tt) / .3, 0, 1)
    pwm = .75 + .25 * np.sign(np.sin(2 * np.pi * 60 * tt))                 # el parpadeo de 60 Hz
    pwm = sosfilt(butter(2, 900, "low", fs=SR, output="sos"), pwm)
    for (nombre, f), p in zip(RGB_HZ.items(), (-.7, 0, .7)):
        x = np.sin(2 * np.pi * f * tt + rng.uniform(0, 6)) * pwm * env
        pon(out, t0, x, pan=p, g=.22)
        pon(out, t0, np.sin(2 * np.pi * f / 2 * tt) * env * pwm, pan=p, g=.12)
    # el barrido de refresco: rojo, verde, azul en corcheas
    orden = list(RGB_HZ.items())
    k = 0
    for b in range(48, 64):
        for beat in (0, .5, 1, 1.5, 2, 2.5):
            t = L.tb(b, beat)
            nombre, f = orden[k % 3]
            k += 1
            d = int(.09 * SR)
            x = np.sin(2 * np.pi * f * 2 * np.arange(d) / SR) * np.exp(-np.arange(d) / (.02 * SR))
            pon(out, t, x, pan=(-.7, 0, .7)[k % 3], g=.18)
            ev(t, "pixel", color=nombre)
    return out


# ── el bajo: contrabajo pulsado ──────────────────────────────────────────────────────────────────────────────
def ks(f, dur, rng, brillo=.5):
    n = int(dur * SR)
    per = SR / f
    Lp = int(round(per - .5))                       # el promedio de dos muestras añade medio periodo de muestra
    x = np.zeros(n)
    exc = rng.standard_normal(Lp) * np.hanning(Lp)
    exc = sosfilt(butter(1, 400 + 2200 * brillo, "low", fs=SR, output="sos"), exc)
    x[:Lp] = exc
    g = .996
    a = np.zeros(Lp + 2)
    a[0] = 1
    a[Lp] = a[Lp + 1] = -g * .5
    y = lfilter([1], a, x)
    e = np.exp(-np.arange(n) / (SR * dur * .45))
    y = sosfilt(butter(2, 1200, "low", fs=SR, output="sos"), y) * e
    return y / (np.abs(y).max() + 1e-9)


def bajo():
    rng = np.random.default_rng(SEM + 4)
    out = stereo()
    for b in range(8, L.NBAR - 1):
        sec = L.seccion(b)
        _, _, bp = L.acorde(L.ACORDES[b])
        f = pc_hz(bp, 1)
        while f < 41:
            f *= 2
        while f > 82:
            f /= 2
        golpes = [(0, 1.0)] if sec in ("verso", "pantalla", "coda") else [(0, 1.0), (2, .55)]
        for beat, v in golpes:
            t = L.tb(b, beat)
            d = L.tb(b, 3) - t + .1
            pon(out, t, ks(f, d, rng), pan=0, g=.8 * v)
            ev(t, "bajo", hz=round(f, 2))
    return out


# ── líneas del jardín: hammond, ondas, flauta, theremin ──────────────────────────────────────────────────────
def frase(instr, notas, rng):
    t0, x = I.tocar_frase(instr, notas, rng)
    return t0, x


def voicing(b, prev=None):
    """Tres voces cerradas del acorde, alrededor de Re4, con movimiento mínimo."""
    _, pcs, _ = L.acorde(L.ACORDES[b])
    pcs = pcs[:4]
    cands = []
    for base in range(52, 70):
        if base % 12 in pcs:
            cands.append(base)
    if prev is None:
        prev = [57, 62, 66]
    out = []
    for p in prev:
        mejor = min(cands, key=lambda c: (abs(c - p), c in out))
        out.append(mejor)
    return sorted(out)


def hammond():
    rng = np.random.default_rng(SEM + 5)
    out = stereo()
    zonas = [(24, 32, .55), (32, 48, 1.0), (64, 72, .5), (72, 88, 1.0), (88, 96, .6)]
    for b0, b1, g in zonas:
        prev = None
        voces = [[], [], []]
        for b in range(b0, b1):
            v = voicing(b, prev)
            prev = v
            t, d = L.tb(b), L.tb(b + 1) - L.tb(b)
            for k in range(3):
                voces[k].append((t, float(hz(v[k])), d, .8))
        for k, vz in enumerate(voces):
            t0, x = frase("hammond", vz, rng)
            pon(out, t0, x, pan=(-.4, 0, .4)[k], g=.33 * g)
    return out


MOTIVO = [69, 71, 74, 69]          # «bue-nos dí-as»: La Si Re La (el sol que sube)


def transforma(tipo, base=0):
    m = [n + base for n in MOTIVO]
    if tipo == "inversion":
        return [m[0] - (n - m[0]) for n in m]
    if tipo == "retro":
        return m[::-1]
    if tipo == "fragmento":
        return m[:2] * 2
    if tipo == "cae":
        return [m[2], m[1], m[0], m[0] - 5]
    return m


# (compás, tiempo, instrumento, transformación, transposición, duración por nota en tiempos)
APARICIONES = [
    (4, 0, "flauta", "recto", -12, 1.5),         # alba: aumentado, grave
    (6, 0, "flauta", "recto", 0, 1.0),
    (15, 2, "ondas", "fragmento", 0, .5),        # se asoma en el bisiesto
    (22, 4.5, "ondas", "recto", 0, .5),
    (31, 0, "ondas", "inversion", 0, .75),       # el bisiesto del pre
    (39, 4, "ondas", "retro", 0, .5),
    (47, 0, "ondas", "inversion", 0, 1.0),       # fin del coro
    (63, 0, "ondas", "retro", 0, .75),           # la pantalla termina: el motivo al revés
    (66, 3, "ondas", "fragmento", -12, .5),      # el café
    (71, 0, "ondas", "recto", 2, .75),           # la modulación: ya en Mi
    (79, 3, "ondas", "inversion", 2, .5),
    (87, 3, "ondas", "recto", 2, 1.0),
    (96, 0, "theremin", "cae", 2, 1.5),          # coda: el sol ya arriba, el motivo baja
]


def motivos():
    rng = np.random.default_rng(SEM + 6)
    out = stereo()
    visitas = []
    for b, beat, instr, tipo, tr, dur in APARICIONES:
        ns = transforma(tipo, tr)
        notas = [(L.tb(b, beat + k * dur), float(hz(n)), dur * L.SPB * .98, .9) for k, n in enumerate(ns)]
        t0, x = frase(instr, notas, rng)
        pon(out, t0, x, pan=(.35 if instr == "ondas" else -.25), g={"flauta": .5, "ondas": .42, "theremin": .35}[instr])
        ev(notas[0][0], "motivo", instrumento=instr, transformacion=tipo, notas=[int(n) for n in ns])
        visitas.append({"t": notas[0][0], "t_fin": notas[-1][0] + notas[-1][2],
                        "notas": [{"hz": f} for _, f, _, _ in notas], "escala": [{"hz": f} for _, f, _, _ in notas]})
    # theremin: dobla la última frase, una octava arriba, lejos
    rs = [r for r in L.renglones() if r["bar"] >= 92]
    notas = [(s["t"], float(hz(s["nota"] + 12)), s["t_dur"], .7) for r in rs for s in r["silabas"]]
    t0, x = frase("theremin", notas, rng)
    pon(out, t0, x, pan=-.3, g=.2)
    return out, visitas


# ── las aves ─────────────────────────────────────────────────────────────────────────────────────────────────
def aves(visitas, ocupado):
    rng = np.random.default_rng(SEM + 7)
    out = stereo()

    def escala_en(t):
        b = tiempo_a_bar(t)
        rp, pcs, _ = L.acorde(L.ACORDES[b])
        ton = 4 if b >= 72 else 2
        mayor = [(ton + g) % 12 for g in (0, 2, 4, 7, 9)]                 # pentatónica de la tonalidad + el acorde
        return sorted({pc_hz(p, 4) for p in set(pcs) | set(mayor)})

    perfil = {"especies": ["clarin", "cenzontle", "primavera", "colibri", "cenzontle", "clarin"], "alba": True,
              "imitar": .9, "presentir": .5, "corte": 3600}
    evs, reg, desc = AV.coro(rng, perfil, L.LARGO - 4, ocupado, escala_en, visitas)
    for t, x, pan in evs:
        sec = L.seccion(tiempo_a_bar(t))
        if sec == "pantalla":
            continue                                                       # adentro, con la pantalla, no se oyen
        g = {"alba": 1.0, "verso": .55, "pre": .5, "coro": .7, "cafe": .6, "coro2": .8, "coda": 1.0}[sec]
        pon(out, t, x, pan=pan, g=.35 * g)
        ev(t, "ave", pan=round(pan, 2), dur=round(len(x) / SR, 2))
    json.dump({"aves": desc, "registro": reg}, open(AQUI / "render" / "aves.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
    return out


# ── la olla de café ──────────────────────────────────────────────────────────────────────────────────────────
def olla():
    rng = np.random.default_rng(SEM + 8)
    out = stereo()
    escala = [pc_hz(p, 5) for p in (2, 4, 6, 9, 11)]
    # de fondo desde el alba: la olla en la estufa, lejos
    t = bar_t(1)
    while t < bar_t(64):
        u = t / bar_t(64)
        t += rng.exponential(1 / (.6 + 3 * u))
        g = {"t": 0, "f": float(rng.uniform(500, 1400)), "fuente": 0, "tau": float(rng.uniform(.01, .03)),
             "chirp": float(rng.uniform(.2, .5)), "amp": float(rng.uniform(.3, .8)), "pan": float(rng.uniform(-.5, .5)), "anillos": 1}
        pon(out, t, AG.burbuja(g, rng), pan=g["pan"], g=.06)
    # el café: canta antes de hervir (compases 64–68: cada vez más burbujas, más chicas, más agudas) …
    t = bar_t(64)
    while t < bar_t(68):
        u = (t - bar_t(64)) / (bar_t(68) - bar_t(64))
        t += rng.exponential(1 / (8 + 70 * u ** 1.5))
        f = escala[int(rng.integers(len(escala)))] * 2 ** int(rng.integers(0, 2)) * (1 + .5 * u)
        g = {"t": 0, "f": float(min(f, 4800)), "fuente": 0, "tau": float(.006 + .02 * (1 - u)), "chirp": .5,
             "amp": float(rng.uniform(.4, 1.0)), "pan": float(rng.uniform(-.9, .9)), "anillos": 1}
        pon(out, t, AG.burbuja(g, rng), pan=g["pan"], g=.16 + .14 * u)
        if rng.random() < .15:
            ev(t, "burbuja", hz=round(g["f"], 1), canta=True)
    # … y cuando hierve se calla: pocas burbujas grandes y graves (compases 68–72)
    t = bar_t(68)
    while t < bar_t(72):
        t += rng.exponential(.55)
        g = {"t": 0, "f": float(rng.uniform(120, 260)), "fuente": 0, "tau": float(rng.uniform(.05, .09)), "chirp": .15,
             "amp": 1.0, "pan": float(rng.uniform(-.4, .4)), "anillos": 2}
        pon(out, t, AG.burbuja(g, rng), pan=g["pan"], g=.18)
        ev(t, "burbuja", hz=round(g["f"], 1), canta=False)
    # gotas-arpa: al final de cada coro y en la pantalla, la escala del momento
    for b, sube in ((39, True), (47, True), (71, True), (79, True), (87, False), (97, False)):
        b = min(b, L.NBAR - 1)
        rp, pcs, _ = L.acorde(L.ACORDES[b])
        esc = sorted({pc_hz(p, 4) for p in pcs} | {pc_hz(p, 5) for p in pcs})
        for gt in AG.arpa(rng, esc, list(range(len(esc))), L.tb(b, 1.5), sube=sube):
            pon(out, gt["t"], AG.burbuja(gt, rng), pan=gt["pan"], g=.22)
            ev(gt["t"], "gota", hz=round(gt["f"], 1))
    return out


# ── percusión: canción de cuna en 3/4, el tambor parlante y la cuchara ───────────────────────────────────────
def escobilla(rng, d=.18):
    n = int(d * SR)
    x = sosfilt(butter(2, [1800, 7000], "band", fs=SR, output="sos"), rng.standard_normal(n))
    return x * np.sin(np.linspace(0, np.pi, n)) ** 2


def taza(rng):
    """La cuchara en la taza: modos de una taza de cerámica (inarmónicos), apagados por el café."""
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    f0 = 1180 * (1 + rng.uniform(-.01, .01))
    x = sum(a * np.sin(2 * np.pi * f0 * r * t + rng.uniform(0, 6)) * np.exp(-t / d)
            for r, a, d in ((1, 1, .5), (2.32, .5, .3), (4.1, .3, .15), (6.2, .15, .08)))
    return x * (1 - np.exp(-t / .0008)) / 2


def percusion():
    rng = np.random.default_rng(SEM + 9)
    out = stereo()
    for b in range(8, L.NBAR - 2):
        sec = L.seccion(b)
        if sec == "pantalla":
            continue
        vel = {"verso": .6, "pre": .75, "coro": 1.0, "cafe": .8, "coro2": 1.0, "coda": .5}[sec]
        g = PA.golpe(70, 58, rng, vel=vel, glide=.03, largo=.5, apagado=False)
        pon(out, L.tb(b), sosfilt(butter(2, 300, "low", fs=SR, output="sos"), g), g=.9)
        ev(L.tb(b), "bombo")
        for beat in (1, 2) + ((1.5, 2.5) if sec in ("coro", "coro2") else ()):
            pon(out, L.tb(b, beat), escobilla(rng), pan=float(rng.uniform(-.3, .3)), g=.12 * vel)
        if sec in ("coro", "coro2", "cafe") and b % 2 == 0:
            pon(out, L.tb(b), taza(rng), pan=.4, g=.12)
            ev(L.tb(b), "taza")
    # el tambor parlante dice el contorno de la letra en el café y en los coros (sólo las tónicas, grave)
    prev = None
    for r in L.renglones():
        if r["seccion"] not in ("cafe", "coro2"):
            continue
        for s in r["silabas"]:
            if not s["tonica"]:
                continue
            f = PA.registro(float(hz(s["nota"])))
            x = PA.golpe(prev or f, f, rng, vel=.7, glide=float(rng.uniform(.03, .09)), apagado=bool(rng.random() < .3))
            pon(out, s["t"] + .01, x, pan=-.35, g=.45)
            ev(s["t"], "parlante", hz=round(f, 1))
            prev = f
    # el día que sobra: en cada tiempo bisiesto, el tambor sube y baja (y la taza, si es de día)
    for b in sorted(L.BISIESTO):
        t = L.T0 + (L.INICIO[b] + 3) * L.SPB
        x = PA.golpe(110, 196, rng, vel=.9, glide=.12, largo=.6)
        pon(out, t, x, pan=.2, g=.55)
        if b > 8:
            pon(out, t + L.SPB / 2, PA.golpe(196, 98, rng, vel=.6, glide=.2, largo=.5), pan=-.2, g=.4)
        ev(t, "bisiesto", compas=b)
    return out


# ── el alba: un pedal subarmónico (trautonium) que se apaga cuando sale el sol ──────────────────────────────
def alba():
    rng = np.random.default_rng(SEM + 10)
    out = stereo()
    notas = [(L.tb(0), float(hz(38)), L.tb(8) - L.tb(0) + 1.0, .7)]
    t0, x = frase("trautonium", notas, rng)
    n = len(x)
    e = np.clip(1.4 - np.arange(n) / n * 1.2, 0, 1) * np.clip(np.arange(n) / (3 * SR), 0, 1)
    pon(out, t0, x * e, g=.35)
    # y vuelve en la coda, más clara: el día lleno ya no necesita el pedal oscuro, sólo su sombra
    notas = [(L.tb(90), float(hz(40)), L.tb(98) - L.tb(90), .5)]
    t0, x = frase("trautonium", notas, rng)
    n = len(x)
    pon(out, t0, x * np.clip(np.arange(n) / (2 * SR), 0, 1) * np.clip((n - np.arange(n)) / (3 * SR), 0, 1), g=.18)
    return out


def escribe(nombre, x):
    wavfile.write(str(STEMS / f"{nombre}.wav"), SR, x.T.astype(np.float32))


def ocupado_por_voz():
    """Nicho acústico a escala de sílaba: las aves sólo se quitan de las TÓNICAS de la voz (la frase entera las callaba:
    la voz casi no para y después del alba no cantaba ninguna)."""
    rs = L.renglones()
    tramos = [(s["t"] - .08, s["t"] + min(s["t_dur"], .6)) for r in rs for s in r["silabas"] if s["tonica"]]
    return lambda t: any(a <= t <= z for a, z in tramos)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    import time
    t0 = time.time()
    arm, luz_res = armonia()
    escribe("armonia", arm)
    print("armonía", round(time.time() - t0), "s")
    escribe("luz", luz(luz_res))
    escribe("granitos", granitos())
    escribe("pixeles", pixeles())
    print("luz, granitos y pixeles", round(time.time() - t0), "s")
    escribe("bajo", bajo())
    escribe("hammond", hammond())
    print("bajo y hammond", round(time.time() - t0), "s")
    mot, visitas = motivos()
    escribe("motivos", mot)
    escribe("aves", aves(visitas, ocupado_por_voz()))
    print("motivos y aves", round(time.time() - t0), "s")
    escribe("olla", olla())
    escribe("percusion", percusion())
    escribe("alba", alba())
    print("olla, percusión y alba", round(time.time() - t0), "s")
    EVENTOS.sort(key=lambda e: e["t"])
    json.dump({"rgb_hz": {k: round(v, 2) for k, v in RGB_HZ.items()}, "rgb_nm": RGB_NM,
               "planck_pico_hz": round(2.821439 / (H_K * OCT / T_SOL), 2), "eventos": EVENTOS},
              open(AQUI / "render" / "eventos.json", "w", encoding="utf8"), ensure_ascii=False)
    print("eventos", len(EVENTOS), "RGB", {k: round(v, 1) for k, v in RGB_HZ.items()})


if __name__ == "__main__":
    main()
