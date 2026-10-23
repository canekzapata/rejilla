"""Instrumentos que deslizan y sostienen, para el comentario de los laberintos.

Canek: el piano (y más el cimbalón desafinado) vuelve críptica la escala del choque, porque
el oído espera un piano temperado. Pidió probar voz sin palabras, Farfisa, flauta y cuerda
frotada sin trastes.

Cada frase se toca como UNA línea continua: la altura f0(t) se desliza entre notas ligadas
(meend, portamento) y la envolvente sólo vuelve a atacar después de un silencio.

  voz      PSOLA en el tiempo con granos de dos periodos tomados de las vocales sostenidas
           (oo, uu, aa, mm) del banco de difonos de Sabina (sólo lectura; ver BANCO_*). El
           timbre se queda al cambiar la altura. Sin palabras: las vocales se funden lento.
  farfisa  órgano combo: cuadrada 8', cuadrada 4', seno 16', vibrato de 6.2 Hz; no desliza.
  flauta   grave, casi seno, con soplo filtrado, chiff al atacar y vibrato tardío.
  cuerda   frotada sin trastes: sierra con cuerpo resonante (picos de caja), arco ruidoso,
           ataque lento, tasto oscuro, vibrato tardío; desliza.
"""
from pathlib import Path
import hashlib, json
import numpy as np
from scipy.signal import butter, sosfilt, resample_poly, lfilter
from scipy.io import wavfile

SR = 48000
BANCO = Path(__file__).resolve().parents[4] / "difonos" / "bancos" / "sabina-1-b44e7fab5cee"

# deslizamiento entre notas ligadas (s), ataque y release de la línea (s)
PERFIL = {
    "voz": {"glide": 0.07, "ataque": 0.07, "release": 0.25, "vib": (5.0, 0.004, 0.3), "techo": 700},
    "farfisa": {"glide": 0.0, "ataque": 0.006, "release": 0.05, "vib": (6.2, 0.0045, 0.0), "techo": 1400},
    "flauta": {"glide": 0.045, "ataque": 0.05, "release": 0.18, "vib": (4.6, 0.003, 0.35), "techo": 1400},
    "cuerda": {"glide": 0.09, "ataque": 0.12, "release": 0.3, "vib": (5.2, 0.006, 0.3), "techo": 1000},
    # v1.5: parientes de la Farfisa y la flauta
    "theremin": {"glide": 0.14, "ataque": 0.09, "release": 0.35, "vib": (5.6, 0.008, 0.08), "techo": 1400},
    "trautonium": {"glide": 0.06, "ataque": 0.02, "release": 0.12, "vib": (5.0, 0.003, 0.4), "techo": 1100},
    "ondas": {"glide": 0.1, "ataque": 0.06, "release": 0.3, "vib": (5.4, 0.005, 0.25), "techo": 1400},
    "hammond": {"glide": 0.0, "ataque": 0.004, "release": 0.04, "vib": (0.8, 0.0, 0.0), "techo": 1100},
}
CASA_HZ = [220.0, 275.0, 330.0, 412.5]   # el acorde de casa de los laberintos: la «palme» de las ondas


def lp(fk, fc, orden=2):
    return 1 / np.sqrt(1 + (fk / fc) ** (2 * orden))


def bump(fk, centro, ancho, g):
    return 1 + g * np.exp(-0.5 * (np.log2(fk / centro) / ancho) ** 2)


# ---------------------------------------------------------------- línea
ARTICULAR = False   # si es True, dos notas iguales seguidas vuelven a atacar (no se funden en una sostenida)


def linea(notas, perfil, rng):
    """notas: [(t, f, dur, vel)] en segundos. Devuelve t0, f0(t), amplitud(t), onsets."""
    notas = sorted(notas, key=lambda x: x[0])
    t0 = notas[0][0]
    fin = max(t + d for t, _, d, _ in notas) + perfil["release"] + 0.1
    n = int((fin - t0) * SR)
    f0 = np.zeros(n)
    gate = np.zeros(n)
    onsets = []
    prev_fin = -1
    for i, (t, f, d, vel) in enumerate(notas):
        a = int((t - t0) * SR)
        sig = notas[i + 1][0] if i + 1 < len(notas) else None
        ligada_sig = sig is not None and sig <= t + d + 0.06
        if ARTICULAR and ligada_sig and abs(np.log2(notas[i + 1][1] / f)) < 1e-3:
            ligada_sig = False                                   # repetida: corte y nuevo ataque
        b = int(((sig if ligada_sig else t + d) - t0) * SR)
        if ARTICULAR and not ligada_sig and sig is not None and sig <= t + d + 0.06:
            b = max(a + 1, b - int(0.045 * SR))                  # un respiro de 45 ms antes de repetir
        f0[a:max(b, a + 1)] = f
        gate[a:max(b, a + 1)] = vel
        if a > prev_fin + int(0.02 * SR):
            onsets.append((a, vel))
        prev_fin = b
    # huecos: sostener la última altura para que el release no caiga a 0 Hz
    ult = notas[0][1]
    for i in range(n):
        if f0[i] == 0:
            f0[i] = ult
        else:
            ult = f0[i]
    # deslizamiento: suavizado exponencial en log-frecuencia
    if perfil["glide"] > 0:
        a = np.exp(-1 / (perfil["glide"] * SR / 3))
        lf = np.log(f0)
        out, _ = lfilter([1 - a], [1, -a], lf - lf[0], zi=[0.0])
        f0 = np.exp(out + lf[0])
    # vibrato tardío: crece después de `retraso` s de nota sostenida
    hz, prof, retraso = perfil["vib"]
    t = np.arange(n) / SR
    cambio = np.r_[True, np.abs(np.diff(np.log(f0))) > 1e-4]
    ultimo = np.maximum.accumulate(np.where(cambio, np.arange(n), 0))
    sost = (np.arange(n) - ultimo) / SR
    llega = np.clip((sost - retraso) / 0.3, 0, 1) if retraso > 0 else np.ones(n)
    f0 = f0 * (1 + prof * llega * np.sin(2 * np.pi * hz * t + rng.uniform(0, 6)))
    # envolvente: ataque/release de primer orden sobre la compuerta
    env = np.zeros(n)
    ka = 1 - np.exp(-1 / (perfil["ataque"] * SR))
    kr = 1 - np.exp(-1 / (perfil["release"] * SR))
    y = 0.0
    for i in range(n):
        g = gate[i]
        y += (ka if g > y else kr) * (g - y)
        env[i] = y
    return t0, f0, env, onsets


def aditivo(f0, amps_fn, rng, k_max=40):
    fase = 2 * np.pi * np.cumsum(f0) / SR
    fm = float(np.median(f0))
    x = np.zeros(len(f0))
    for k in range(1, k_max + 1):
        if fm * k > 12000:
            break
        a = amps_fn(k, fm * k)
        if a > 1e-4:
            x += a * np.sin(k * fase + rng.uniform(0, 6))
    return x


def ruido_banda(n, lo, hi, rng, orden=2):
    sos = butter(orden, [lo, hi], btype="band", fs=SR, output="sos")
    return sosfilt(sos, rng.standard_normal(n))


# ---------------------------------------------------------------- voz (PSOLA)
_GRANOS = None


def granos():
    """Granos de dos periodos de las vocales sostenidas del banco, a 48 kHz."""
    global _GRANOS
    if _GRANOS is not None:
        return _GRANOS
    M = json.load(open(BANCO / "manifiesto.json", encoding="utf-8"))
    sr, audio = wavfile.read(BANCO / "banco.wav")
    audio = audio.astype(float) / 32768
    base = 440 * 2 ** ((M["nota_base_midi"] - 69) / 12)
    out = {}
    for v in ("oo", "uu", "aa", "mm"):
        u = M["unidades"][v]
        s = audio[u["inicio"] + u["izq"]:u["inicio"] + u["der"]]
        s = resample_poly(s, 160, 147)                 # 22050 → 48000
        f = base * 2 ** ((u["cents"] or 0) / 1200)
        P = int(round(SR / f))
        nuc = s[int(len(s) * 0.25):int(len(s) * 0.75)]
        marcas = []
        m = int(np.argmax(np.abs(nuc[:P]))) + P
        while m + P < len(nuc):
            lo, hi = m - P // 8, m + P // 8
            m = lo + int(np.argmax(np.abs(nuc[lo:hi])))
            marcas.append(m)
            m += P
        w = np.hanning(2 * P)
        gs = [nuc[m - P:m + P] * w for m in marcas if m - P >= 0 and m + P <= len(nuc)]
        gs = [g / (np.sqrt(np.mean(g ** 2)) + 1e-9) for g in gs]
        out[v] = (P, gs)
    _GRANOS = out
    return out


def voz(f0, env, onsets, rng):
    G = granos()
    n = len(f0)
    x = np.zeros(n + 4000)
    # mezcla lenta de vocales sin palabras: o y u oscuras, a de vez en cuando, mm cerrada
    pesos_base = np.array([1.0, 0.8, 0.35, 0.6])
    lfo = rng.uniform(0.15, 0.4)
    nombres = ["oo", "uu", "aa", "mm"]
    pos = 0.0
    while pos < n - 1:
        i = int(pos)
        fase = 2 * np.pi * lfo * i / SR
        w = pesos_base * (1 + 0.8 * np.sin(fase + np.arange(4) * 1.7))
        v = nombres[int(rng.choice(4, p=w / w.sum()))]
        P, gs = G[v]
        g = gs[int(rng.integers(len(gs)))]
        a = i - P
        if a >= 0:
            x[a:a + 2 * P] += g * env[i]
        pos += SR / f0[i] * (1 + rng.normal(0, 0.003))   # jitter de periodo
    x = x[:n]
    x += 0.04 * ruido_banda(n, 1500, 6000, rng) * env      # aire
    return x / 3.0


# ---------------------------------------------------------------- los otros
def farfisa(f0, env, onsets, rng):
    def cuadrada(k, fk):
        return (1 / k if k % 2 else 0) * lp(fk, 3800)
    fase = 2 * np.pi * np.cumsum(f0) / SR
    x = np.zeros(len(f0))
    fm = float(np.median(f0))
    for k in range(1, 40, 2):                                 # 8'
        if fm * k > 12000:
            break
        x += cuadrada(k, fm * k) * np.sin(k * fase)
    for k in range(1, 30, 2):                                 # 4'
        if 2 * fm * k > 12000:
            break
        x += 0.5 * cuadrada(k, 2 * fm * k) * np.sin(2 * k * fase + 0.3)
    x += 0.45 * np.sin(fase / 2)                              # 16'
    for a, vel in onsets:                                     # clic de tecla
        b = min(len(x), a + int(0.004 * SR))
        x[a:b] += 0.3 * vel * rng.standard_normal(b - a)
    return x * env / 2.2


def flauta(f0, env, onsets, rng):
    x = aditivo(f0, lambda k, fk: [1, 0.22, 0.1, 0.04, 0.02, 0.01][k - 1] if k <= 6 else 0, rng)
    n = len(f0)
    soplo = ruido_banda(n, 400, 4000, rng) * 0.09
    for a, vel in onsets:                                     # chiff
        b = min(n, a + int(0.035 * SR))
        soplo[a:b] += 0.5 * vel * ruido_banda(b - a + 64, 1200, 5000, rng)[64:] * np.linspace(1, 0, b - a)
    return (x + soplo) * env / 1.4


def cuerda(f0, env, onsets, rng):
    def amps(k, fk):
        caja = bump(fk, 280, 0.25, 1.2) * bump(fk, 520, 0.3, 0.8) * bump(fk, 1150, 0.3, 0.6) * bump(fk, 2600, 0.25, 0.4)
        return (1 / k) * caja * lp(fk, 2000, 2)               # tasto: oscuro
    x = aditivo(f0, amps, rng)
    n = len(f0)
    # el arco: ruido que sigue a la envolvente y un poco a la altura
    arco = ruido_banda(n, 800, 5000, rng) * 0.05
    rasp = 1 + 0.25 * np.sin(2 * np.pi * rng.uniform(3, 7) * np.arange(n) / SR)
    return (x / 2.0 + arco * rasp) * env


def theremin(f0, env, onsets, rng):
    """Casi un seno; la heterodina le deja un poco de 2.º y 3.º armónico. Nunca ataca seco."""
    x = aditivo(f0, lambda k, fk: [1, 0.12, 0.05, 0.015][k - 1] if k <= 4 else 0, rng)
    return x * env / 1.1


def trautonium(f0, env, onsets, rng):
    """Mixtur-Trautonium (Sala): pulso con formantes filosos y una MEZCLA DE SUBARMÓNICOS
    exactos (f/2, f/3, f/4, f/5, dos por frase) que el instrumento genera por división."""
    n = len(f0)
    fase = 2 * np.pi * np.cumsum(f0) / SR
    fm = float(np.median(f0))

    def pulso(fase_k, fbase, ancho=0.22):
        y = np.zeros(n)
        for k in range(1, 50):
            fk = fbase * k
            if fk > 10000:
                break
            a = np.sin(np.pi * k * ancho) / k * bump(fk, 950, 0.25, 2.0) * bump(fk, 2300, 0.2, 1.2) * lp(fk, 3200)
            y += a * np.sin(k * fase_k)
        return y
    x = pulso(fase, fm)
    ks = sorted(rng.choice([2, 3, 4, 5], 2, replace=False).tolist())
    for j, k in enumerate(ks):
        x += (0.55 / (j + 1)) * pulso(fase / k, fm / k, 0.35)
    return x * env / 3.0


def _resonador(x, f, t60):
    """Resonador de dos polos (cuerda simpática): f en Hz, t60 en s."""
    r = np.exp(-6.91 / (t60 * SR))
    w = 2 * np.pi * f / SR
    return lfilter([1 - r], [1, -2 * r * np.cos(w), r * r], x)


def ondas(f0, env, onsets, rng):
    """Ondas Martenot: onda casi triangular por el difusor «palme», cuyas cuerdas simpáticas
    están afinadas al acorde de casa: lo que toca la mano hace sonar la casa por simpatía."""
    x = aditivo(f0, lambda k, fk: ((1 / k ** 2) if k % 2 else 0.08 / k) * lp(fk, 4000), rng) * env / 1.2
    halo = np.zeros(len(x))
    for f in CASA_HZ:
        for o in (0.5, 1, 2):
            halo += _resonador(x, f * o, 3.0)
    halo /= (np.max(np.abs(halo)) + 1e-9) / (np.max(np.abs(x)) + 1e-9)
    return x + 0.45 * halo


def hammond(f0, env, onsets, rng):
    """Barras 16' 8' 5⅓' 4' 2⅔' (senos) por un Leslie lento (coral): amplitud y doppler giran."""
    fase = 2 * np.pi * np.cumsum(f0) / SR
    barras = [(0.5, 0.7), (1, 1.0), (1.5, 0.5), (2, 0.55), (3, 0.25)]
    n = len(f0)
    t = np.arange(n) / SR
    rot = 2 * np.pi * 0.8 * t + rng.uniform(0, 6)
    x = sum(a * np.sin(m * fase + 0.0012 * m * float(np.median(f0)) * np.sin(rot) / 6) for m, a in barras)
    x *= 1 + 0.18 * np.sin(rot)
    for a, vel in onsets:                                     # percusión breve de la tecla
        b = min(n, a + int(0.006 * SR))
        x[a:b] += 0.2 * vel * rng.standard_normal(b - a)
    return x * env / 2.4


TOCA = {"voz": voz, "farfisa": farfisa, "flauta": flauta, "cuerda": cuerda,
        "theremin": theremin, "trautonium": trautonium, "ondas": ondas, "hammond": hammond}


def tocar_frase(instrumento, notas, rng):
    """notas: [(t_s, hz, dur_s, vel)]. Devuelve (t0, audio)."""
    perfil = PERFIL[instrumento]
    if max(f for _, f, _, _ in notas) > perfil["techo"]:      # registro cantable: toda la frase baja una octava
        notas = [(t, f / 2, d, v) for t, f, d, v in notas]
    t0, f0, env, onsets = linea(notas, perfil, rng)
    return t0, TOCA[instrumento](f0, env, onsets, rng)


def procedencia_banco():
    M = json.load(open(BANCO / "manifiesto.json", encoding="utf-8"))
    return {"banco": str(BANCO.relative_to(BANCO.parents[2])), "id": M["id"],
            "banco_wav_sha256": hashlib.sha256((BANCO / "banco.wav").read_bytes()).hexdigest(),
            "unidades": ["oo", "uu", "aa", "mm"]}
