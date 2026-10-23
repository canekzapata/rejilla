"""El tapete de Talbot — un instrumento de rejilla desde el grupo metapléctico (21 oct 2026).

La idea
-------
Un loop de N muestras es una función sobre el grupo finito ℤ/N. El grupo metapléctico también existe sobre grupos
finitos (la representación de Weil finita, la de las funciones theta de retícula), y uno de sus generadores es la
fase cuadrática 𝒯. Aquí se aplica en el lado de Fourier: el armónico n del loop gira con

        Y[n] = X[n] · e^{−iπ n² τ}                      (dispersión cuadrática: el «dispersar» del Telar)

Eso es el efecto Talbot (1836) en el tiempo:
  · τ = 0           el loop tal cual.
  · τ = p/q         el loop se vuelve L copias de sí mismo corridas j·T/L (L = q si p·q es par, 2q si es impar),
                    cada una con un peso complejo c_j = suma de Gauss. Un peso complejo en una copia real suena
                    como mezcla de la copia y su transformada de Hilbert (otro color del mismo golpe).
                    Muchas copias pesan cero: la aritmética decide cuántas voces suenan.  → tresillos, cánones.
  · τ irracional    no hay periodo en n: el loop se deshace en una nube (el tapete es fractal).
  · τ = 1           (−1)^n: el loop corrido medio periodo.   τ = 2: vuelve idéntico.
Las sumas de Gauss llevan raíces octavas de la unidad (ε_q ∈ {1, i} por √q): son el multiplicador metapléctico,
la raíz cuadrada ε(z)² = cz + d con la que la función theta es forma modular de peso 1/2.

El instrumento: el loop es la urdimbre, τ es la trama. Una partitura es un CAMINO por el tapete: τ(t).
Se lee por bloques solapados (Hann, 2048/1024): cada bloque toma su τ, calcula el loop entero y lee la ventana
que le toca (la fase del loop corre con el tiempo).

Ejecutar: python tapete.py  → carpeta exclusiva tapete-de-talbot-s<semilla>-<hash12>/
"""
import hashlib, json, math, os, shutil, subprocess, sys
from fractions import Fraction
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, stft
from PIL import Image, ImageDraw, ImageFont

SR = 48000
SEMILLA = 20261021
AQUI = Path(__file__).resolve().parent


# ───────────── el motor ─────────────
def indices(N, hilos=None):
    """Los armónicos n = 0..N/2 del loop. Con `hilos` = M se reducen al grupo finito ℤ/M (ñ = n mod M, centrado en
    [−M/2, M/2)): es la misma fase cuadrática, pero de la representación de Weil de ℤ/M. Las copias caen entonces en
    una retícula de T/M (M = 16: los dieciseisavos del compás) y el tapete deja de ser fractal: se puede deslizar."""
    n = np.arange(N // 2 + 1, dtype=np.int64)
    return n if not hilos else (n + hilos // 2) % hilos - hilos // 2


def fase_talbot(N, tau, hilos=None):
    """e^{−iπ ñ² τ}. Con τ racional (Fraction) se calcula exacto con enteros (ñ² p mod 2q)."""
    n = indices(N, hilos)
    if isinstance(tau, Fraction):
        p, q = tau.numerator, tau.denominator
        r = (n * n % (2 * q)) * p % (2 * q)
        return np.exp(-1j * math.pi * r / q)
    r = np.mod((n * n).astype(np.float64) * float(tau), 2.0)  # n² < 2^53: exacto en flotante
    return np.exp(-1j * math.pi * r)


def talbot(x, tau, hilos=None):
    """El loop x (un periodo, N muestras) bajo la fase cuadrática τ. Real, mismo N, misma energía."""
    X = np.fft.rfft(x, axis=0)
    ph = fase_talbot(len(x), tau, hilos)
    return np.fft.irfft(X * (ph[:, None] if X.ndim == 2 else ph), n=len(x), axis=0)


def urdimbre(tau, M):
    """Con `hilos` = M el loop transformado es Re Σ_i w_i · xa(t − i·T/M): los pesos de los M hilos.
    w = transformada inversa de la fase sobre ℤ/M. Una fila del tapete de M hilos."""
    n = (np.arange(M) + M // 2) % M - M // 2
    if isinstance(tau, Fraction):
        p, q = tau.numerator, tau.denominator
        ph = np.exp(-1j * math.pi * ((n * n % (2 * q)) * p % (2 * q)) / q)
    else:
        ph = np.exp(-1j * math.pi * np.mod(n * n * float(tau), 2.0))
    return np.fft.ifft(ph)


def leer(loop, camino, dur, hilos=None, B=2048):
    """Recorre el tapete: camino(t) → τ. Bloques Hann de B con salto B/2; cada uno lee el loop transformado
    en la posición que le toca (t mod T). Devuelve (y, [(t, τ)] por bloque)."""
    N = len(loop); n_tot = int(round(dur * SR)); H = B // 2
    w = np.sin(np.pi * (np.arange(B) + .5) / B) ** 2            # Hann periódica: con salto B/2 suma exactamente 1
    y = np.zeros((n_tot + B, loop.shape[1])); cache = {}; taus = []
    for i0 in range(-H, n_tot, H):
        tc = (i0 + H) / SR; tau = camino(tc)
        key = tau if isinstance(tau, Fraction) else round(float(tau), 9)
        if key not in cache:
            if len(cache) > 64: cache.clear()
            cache[key] = talbot(loop, tau, hilos)
        z = cache[key]; idx = np.arange(i0, i0 + B) % N
        a = max(0, i0)
        y[a:i0 + B] += (z[idx] * w[:, None])[a - i0:]
        taus.append((tc, float(tau)))
    return y[:n_tot], taus


def camino_por_nudos(nudos):
    """nudos: [(t, τ)], con τ Fraction en los tramos quietos. Entre dos nudos iguales se queda (exacto);
    entre distintos se desliza en línea recta (flotante: pasa por la nube)."""
    def c(t):
        for (t0, a), (t1, b) in zip(nudos, nudos[1:]):
            if t0 <= t < t1:
                return a if a == b else float(a) + (float(b) - float(a)) * (t - t0) / (t1 - t0)
        return nudos[-1][1]
    return c


# ───────────── la aritmética: copias y sumas de Gauss ─────────────
def copias(p, q):
    """τ = p/q → (L, c_j): el loop transformado es Re Σ_j c_j · xa(t − jT/L), con xa la señal analítica."""
    L = q if (p * q) % 2 == 0 else 2 * q
    m = np.arange(L); ph = np.exp(-1j * math.pi * ((m * m * p) % (2 * q)) / q)
    c = np.array([np.mean(ph * np.exp(2j * math.pi * m * j / L)) for j in range(L)])   # serie de Fourier de la fase periódica en n
    return L, c


def analitica(x):
    X = np.fft.fft(x, axis=0); N = len(x); h = np.zeros(N); h[0] = 1; h[1:N // 2] = 2; h[N // 2] = 1
    return np.fft.ifft(X * (h[:, None] if X.ndim == 2 else h), axis=0)


def legendre(a, p):
    a %= p
    return 0 if a == 0 else (1 if pow(a, (p - 1) // 2, p) == 1 else -1)


# ───────────── los loops (todo sintetizado aquí, circular: lo que se pasa del final entra por el principio) ─────────────
def _doblar(buf, N):
    out = np.zeros((N, buf.shape[1]))
    for k in range(0, len(buf), N):
        seg = buf[k:k + N]; out[:len(seg)] += seg
    return out


def _quitar_extremos(x):
    """Sin DC ni Nyquist: así la fase cuadrática es exacta también en la señal real (ver sonda)."""
    X = np.fft.rfft(x, axis=0); X[0] = 0; X[-1] = 0
    return np.fft.irfft(X, n=len(x), axis=0)


def _pan(y, p):
    a = (p + 1) * math.pi / 4
    return np.stack([y * math.cos(a), y * math.sin(a)], 1)


def loop_clave(T=0.5, semilla=SEMILLA):
    """Un golpe de madera por periodo: el tapete puro."""
    rng = np.random.default_rng(semilla); N = int(round(T * SR)); L = int(.12 * SR); t = np.arange(L) / SR
    g = sum(a * np.sin(2 * math.pi * f * t) * np.exp(-t / d) for f, a, d in ((1180, 1, .018), (2470, .55, .011), (3890, .25, .006)))
    g += .25 * sosfilt(butter(2, [2000, 7000], 'band', fs=SR, output='sos'), rng.standard_normal(L)) * np.exp(-t / .002)
    g *= np.minimum(1, t / .0004)
    buf = np.zeros((N + L, 2)); buf[:L] += _pan(g, 0)
    return _quitar_extremos(_doblar(buf, N))


def loop_bateria(T=2.0, semilla=SEMILLA):
    """Un compás de 4/4 a 120 (16 pasos de 1/8 s): bombo sincopado, tarola en 2 y 4, hats, aro."""
    rng = np.random.default_rng(semilla + 1); N = int(round(T * SR)); paso = T / 16
    buf = np.zeros((N + SR, 2))

    def pone(i, sig, pan=0.0, v=1.0):
        a = int(round(i * paso * SR)); buf[a:a + len(sig)] += _pan(sig * v, pan)

    t = np.arange(int(.6 * SR)) / SR
    bombo = np.sin(2 * math.pi * np.cumsum(48 + 110 * np.exp(-t / .035)) / SR) * np.exp(-t / .32) + .3 * np.exp(-t / .004) * rng.standard_normal(len(t)) * .2
    tn = t[:int(.35 * SR)]
    tarola = .55 * np.sin(2 * math.pi * 188 * tn) * np.exp(-tn / .06) + sosfilt(butter(2, [1500, 8000], 'band', fs=SR, output='sos'), rng.standard_normal(len(tn))) * np.exp(-tn / .13)
    th = t[:int(.3 * SR)]
    hat = lambda d: sosfilt(butter(4, 7000, 'high', fs=SR, output='sos'), rng.standard_normal(len(th))) * np.exp(-th / d)
    ta = t[:int(.08 * SR)]
    aro = sum(a * np.sin(2 * math.pi * f * ta) * np.exp(-ta / d) for f, a, d in ((1720, 1, .012), (2930, .5, .007)))
    for i in (0, 6, 10): pone(i, bombo, 0, 1.0)
    for i in (4, 12): pone(i, tarola, .05, .8)
    for i in range(0, 16, 2): pone(i, hat(.035 if i != 14 else .22), .35, .32 if i % 4 else .45)
    for i in (3, 9, 13): pone(i, aro, -.4, .45)
    return _quitar_extremos(_doblar(buf, N))


def loop_tema(T=4.0, semilla=SEMILLA):
    """Una frase de cuerda grave en re menor (8 notas en 4 s), para los cánones."""
    N = int(round(T * SR)); buf = np.zeros((N + 4 * SR, 2)); t = np.arange(int(3.5 * SR)) / SR
    frase = [(0.0, 0), (0.5, 3), (1.0, 7), (1.5, 10), (2.0, 8), (2.75, 7), (3.25, 3), (3.5, 2)]
    for k, (t0, st) in enumerate(frase):
        f0 = 440 * 2 ** ((50 + st - 69) / 12); s = np.zeros(len(t))
        for h in range(1, 13):
            fh = h * f0 * math.sqrt(1 + 2e-4 * h * h)
            if fh > 9000: break
            s += (1 / h ** 1.25) * np.sin(2 * math.pi * fh * t) * np.exp(-t * (1.1 + .55 * h))
        s *= np.minimum(1, t / .003); a = int(t0 * SR)
        buf[a:a + len(s)] += _pan(s, -.25 + .5 * (k % 2))
    return _quitar_extremos(_doblar(buf, N))


# ───────────── la sonda ─────────────
def sonda():
    F = Fraction
    r = {}
    x = loop_bateria(); N = len(x)
    xa = analitica(x)
    # 1. a τ = p/q, la fase cuadrática es exactamente una suma de L copias con pesos de Gauss
    exacta = {}
    for p, q in ((1, 2), (1, 3), (2, 3), (1, 4), (3, 4), (1, 5), (2, 5), (1, 6), (1, 8), (1, 1), (2, 1)):
        L, c = copias(p, q)
        assert N % L == 0
        y = talbot(x, Fraction(p, q))
        z = np.real(sum(c[j] * np.roll(xa, j * N // L, axis=0) for j in range(L)))
        voces = [j for j in range(L) if abs(c[j]) > 1e-9]
        exacta[f'{p}/{q}'] = {
            'L': L, 'voces': len(voces), 'corrimientos_T': [f'{j}/{L}' for j in voces],
            'peso_abs': round(float(np.max(np.abs(c))), 6), 'fase_pesos_grados': [round(math.degrees(np.angle(c[j])), 1) for j in voces],
            'error_rel': float(np.max(np.abs(y - z)) / np.max(np.abs(y)))}
    r['copias_exactas'] = exacta
    # 2. unitaria: la energía no cambia con ningún τ (es sólo fase)
    r['energia_rel_max'] = float(max(abs(np.sum(talbot(x, t) ** 2) / np.sum(x ** 2) - 1) for t in (0.123, Fraction(1, 3), math.pi - 3, 0.618034)))
    # 3. τ = 1 corre medio periodo; τ = 2 vuelve
    r['tau_1_vs_medio_periodo'] = float(np.max(np.abs(talbot(x, Fraction(1)) - np.roll(x, N // 2, axis=0))))
    r['tau_2_vs_identidad'] = float(np.max(np.abs(talbot(x, Fraction(2)) - x)))
    # 4. la raíz octava: G(p, q) = Σ e^{2πi p m²/q} = (p|q)·ε_q·√q, ε_q = 1 (q ≡ 1 mod 4) o i (q ≡ 3 mod 4)
    err = 0.0
    for q in (3, 5, 7, 11, 13, 17, 19, 23):
        eps = 1 if q % 4 == 1 else 1j
        for p in range(1, q):
            G = np.sum(np.exp(2j * math.pi * p * np.arange(q) ** 2 / q))
            err = max(err, abs(G - legendre(p, q) * eps * math.sqrt(q)))
    r['gauss_vs_reciprocidad_err'] = err
    # 5. la nube: factor de cresta de la envolvente del compás (alto = golpes claros; bajo = nube)
    def cresta(y):
        e = np.abs(analitica(y.sum(1)))
        return round(float(e.max() / np.sqrt(np.mean(e ** 2))), 2)
    r['cresta'] = {k: cresta(talbot(x, v)) for k, v in (('0', Fraction(0)), ('1/2', Fraction(1, 2)), ('1/3', Fraction(1, 3)), ('1/4', Fraction(1, 4)),
                                                         ('0.618034 (áurea)', 0.618034), ('0.414214 (√2−1)', 0.414214), ('1/3 + 1e-6', 1 / 3 + 1e-6))}
    # 6. lo sensible del tapete: cuánto se aleja de 1/3 un τ apenas movido (correlación con el loop en 1/3)
    y3 = talbot(x, Fraction(1, 3))
    r['sensibilidad_1_3'] = {f'{d:g}': round(float(np.sum(y3 * talbot(x, 1 / 3 + d)) / np.sum(y3 ** 2)), 4) for d in (1e-9, 1e-8, 1e-7, 1e-6, 1e-5)}
    # 7. el lector: con τ quieto, leer el tapete por bloques = repetir el loop transformado
    yl, _ = leer(x, lambda t: Fraction(1, 3), 4.0)
    ref = np.tile(y3, (2, 1))[:len(yl)]
    r['lector_err'] = float(np.max(np.abs(yl[2048:-2048] - ref[2048:-2048])))
    # 8. con 16 hilos: el loop transformado es exactamente la suma de sus 16 corrimientos de un dieciseisavo con los pesos w
    h16 = {}
    for tau in (F(1, 2), F(1, 4), F(1, 8), F(3, 8), F(1, 16), F(1, 3), F(1, 5), 0.3):
        w = urdimbre(tau, 16); y = talbot(x, tau, 16)
        z = np.real(sum(w[i] * np.roll(xa, i * N // 16, axis=0) for i in range(16)))
        suenan = [i for i in range(16) if abs(w[i]) > 1e-9]
        h16[str(tau)] = {'hilos_que_suenan': len(suenan), 'en_dieciseisavos': suenan if len(suenan) < 16 else 'todos',
                         'error_rel': float(np.max(np.abs(y - z)) / np.max(np.abs(y)))}
    # 9. qué tan liso es el tapete: correlación del loop en τ con el loop en τ + δ, todos los armónicos contra 16 hilos
    def liso(hilos, d):
        a = talbot(x, .3, hilos); b = talbot(x, .3 + d, hilos)
        return round(float(np.sum(a * b) / np.sum(a * a)), 4)
    r['hilos_16'] = {'copias': h16, 'liso_todos': {f'{d:g}': liso(None, d) for d in (1e-4, 1e-3, 1e-2)},
                     'liso_16': {f'{d:g}': liso(16, d) for d in (1e-4, 1e-3, 1e-2)}}
    return r


# ───────────── audio ─────────────
def medir(wav):
    out = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(wav), '-af', 'loudnorm=print_format=json', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    j = json.loads(out[out.rindex('{'):out.rindex('}') + 1])
    return float(j['input_i']), float(j['input_tp']), float(j['input_lra'])


def guardar(y, base, lufs=-16.0):
    y = y / (np.abs(y).max() + 1e-12) * .5
    wav = base.with_suffix('.wav'); wavfile.write(str(wav), SR, y.astype(np.float32))
    i, tp, _ = medir(wav); g = 10 ** ((lufs - i) / 20); y = y * g
    pico = np.abs(y).max()
    if pico > .89:                                        # limitador suave sólo en lo que se pasa
        y = np.where(np.abs(y) > .7, np.sign(y) * (.7 + .19 * np.tanh((np.abs(y) - .7) / .19)), y)
    wavfile.write(str(wav), SR, y.astype(np.float32))
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(wav), '-c:a', 'aac', '-b:a', '192k', str(base.with_suffix('.m4a'))], check=True)
    i, tp, lra = medir(wav)
    return {'archivo': base.with_suffix('.m4a').name, 'dur_s': round(len(y) / SR, 2), 'LUFS': i, 'dBTP': tp, 'LRA': lra,
            'sha256_wav': hashlib.sha256(wav.read_bytes()).hexdigest()[:16]}


F = Fraction
CAMINOS = {
    # 1. la clave exacta (todos los armónicos): quieta en cada racional, cruzando la nube entre uno y otro
    'clave': [(0, F(0)), (3, F(0)), (3.6, F(1, 4)), (6, F(1, 4)), (6.6, F(1, 3)), (9, F(1, 3)), (9.6, F(1, 2)), (12, F(1, 2)),
              (12.6, F(2, 3)), (15, F(2, 3)), (15.6, F(3, 4)), (18, F(3, 4)), (18.6, F(1)), (21, F(1)), (23, F(2)), (26, F(2))],
    # 2. la batería exacta: compases de 2 s; pasa una vez por la nube áurea
    'bateria': [(0, F(0)), (4, F(0)), (4.25, F(1, 2)), (8, F(1, 2)), (8.25, F(1, 3)), (12, F(1, 3)), (12.25, F(1, 4)), (16, F(1, 4)),
                (16.25, .618034), (17.75, .618034), (18, F(2, 3)), (22, F(2, 3)), (22.25, F(2, 5)), (26, F(2, 5)),
                (26.25, F(1, 6)), (30, F(1, 6)), (30.25, F(1)), (34, F(1)), (36, F(2)), (40, F(2))],
    # 3. la batería en 16 hilos: las copias caen en dieciseisavos y los deslizamientos se oyen como cánones que se mueven
    'bateria-16': [(0, F(0)), (4, F(0)), (4.25, F(1, 4)), (8, F(1, 4)), (12, F(1, 2)), (16, F(1, 2)), (16.25, F(1, 8)), (20, F(1, 8)),
                   (20.25, F(3, 8)), (24, F(3, 8)), (24.25, F(1, 16)), (28, F(1, 16)), (32, F(1, 3)), (36, F(1, 3)),
                   (36.25, F(1)), (40, F(1)), (44, F(2)), (48, F(2))],
    # 4. el tema: cada τ = 1/q es un canon; la frase dura 4 s
    'canon': [(0, F(0)), (8, F(0)), (8.3, F(1, 2)), (16, F(1, 2)), (16.3, F(1, 3)), (24, F(1, 3)), (24.3, F(1, 4)), (32, F(1, 4)),
              (32.3, F(2, 5)), (40, F(2, 5)), (42, F(2)), (48, F(2))],
}


# ───────────── láminas ─────────────
def oklch(L, C, h):
    a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
    l_, m_, s_ = L + .3963377774 * a + .2158037573 * b, L - .1055613458 * a - .0638541728 * b, L - .0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    rgb = (4.0767416621 * l - 3.3077115913 * m + .2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - .3413193965 * s,
           -.0041960863 * l - .7034186147 * m + 1.7076147010 * s)
    f = lambda x: 12.92 * x if x <= .0031308 else 1.055 * x ** (1 / 2.4) - .055
    return tuple(int(round(max(0, min(1, f(max(0, min(1, c))))) * 255)) for c in rgb)


rng_vis = np.random.default_rng(SEMILLA)
H0 = float(rng_vis.uniform(0, 360))
BG, FG, MUTED, GRID = oklch(.14, .03, H0), oklch(.93, .02, H0 + 30), oklch(.66, .04, H0 + 20), oklch(.30, .04, H0)
ACENTO = oklch(.82, .15, H0 + 140)


def fuente(n, bold=False):
    for c in ('C:/Windows/Fonts/consolab.ttf' if bold else 'C:/Windows/Fonts/consola.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'):
        if os.path.exists(c): return ImageFont.truetype(c, n)
    return ImageFont.load_default()


def color_peso(w):
    """Un peso complejo → color: la luz es la magnitud, el matiz es la fase (las raíces octavas se ven como 8 colores)."""
    m = abs(w)
    if m < 1e-3: return BG
    v = min(1.0, m)                                     # lineal: los racionales sencillos (pocos hilos fuertes) brillan
    return oklch(.18 + .74 * v, .03 + .15 * v, H0 + math.degrees(np.angle(w)))


def tejer(M, filas, tmax=2):
    """El tapete de M hilos: filas de τ ∈ [0, tmax] (racionales k/(filas/tmax)), columnas = los M hilos (corrimientos)."""
    img = np.zeros((filas, M, 3), np.uint8)
    for i in range(filas):
        w = urdimbre(F(i * tmax, filas - 1) if filas > 1 else F(0), M)
        for j in range(M): img[i, j] = color_peso(w[j])
    return img


def pinta(D, w, h, matiz):
    """D (filas × columnas en 0..1) → imagen; para espectrogramas."""
    filas, cols = D.shape; lut = {}; img = np.zeros((filas, cols, 3), np.uint8)
    for i in range(filas):
        for j in range(cols):
            v = round(float(D[i, j]) * 40) / 40
            if v not in lut: lut[v] = oklch(.10 + .82 * v ** 1.3, .02 + .15 * v, matiz + 60 * v)
            img[i, j] = lut[v]
    return Image.fromarray(img).resize((w, h), Image.Resampling.LANCZOS)


def ejes_tau(dr, x0, y0, h, tmax, fs, lista, izq=True):
    for fr in lista:
        yy = y0 + h * float(fr) / tmax
        if izq:
            dr.line((x0 - 8, yy, x0 - 2, yy), fill=MUTED); dr.text((x0 - 44, yy - 7), str(fr), font=fs, fill=MUTED)
        else:
            dr.line((x0 + 2, yy, x0 + 8, yy), fill=MUTED)


def lamina_urdimbres(sonda_r, filas_hasta=None):
    W, Hh = 1600, 960; im = Image.new('RGB', (W, Hh), BG); dr = ImageDraw.Draw(im)
    ft, fs, fm = fuente(30, True), fuente(15), fuente(13)
    dr.text((48, 26), '01 · EL TAPETE DE TALBOT · TRES URDIMBRES', font=ft, fill=FG)
    dr.text((48, 66), 'filas: τ de 0 a 2 · columnas: los M hilos (corrimientos de T/M) · luz: |peso| · color: fase del peso (suma de Gauss)', font=fs, fill=MUTED)
    y0, h = 120, 780; marcas = [F(0), F(1, 4), F(1, 3), F(1, 2), F(2, 3), F(3, 4), F(1), F(3, 2), F(2)]
    for k, (M, x0, w) in enumerate(((16, 110, 320), (48, 520, 384), (120, 990, 480))):
        filas = 481
        img = tejer(M, filas)
        if filas_hasta is not None: img[int(filas * filas_hasta):] = BG
        im.paste(Image.fromarray(img).resize((w, h), Image.Resampling.NEAREST), (x0, y0)); dr = ImageDraw.Draw(im)
        ejes_tau(dr, x0, y0, h, 2, fm, marcas)
        dr.text((x0, y0 - 24), f'M = {M} hilos', font=fuente(16, True), fill=FG)
    s16 = sonda_r['hilos_16']['copias']
    dr.text((48, 912), 'con 16 hilos: ' + ' · '.join(f'{k}: {v["hilos_que_suenan"]} hilos' for k, v in s16.items()), font=fm, fill=MUTED)
    return im


def lamina_bateria16(ruta, dur):
    W, Hh = 1600, 960; im = Image.new('RGB', (W, Hh), BG); dr = ImageDraw.Draw(im)
    ft, fs, fm = fuente(30, True), fuente(15), fuente(13)
    dr.text((48, 26), '02 · UN COMPÁS DE BATERÍA EN 16 HILOS · EL CAMINO DE LA MUESTRA', font=ft, fill=FG)
    dr.text((48, 66), 'izquierda: el tapete (cada columna es el compás corrido un dieciseisavo) · derecha: τ(t) de la muestra, con la misma escala de τ', font=fs, fill=MUTED)
    y0, h = 120, 780
    img = tejer(16, 481)
    im.paste(Image.fromarray(img).resize((512, h), Image.Resampling.NEAREST), (110, y0)); dr = ImageDraw.Draw(im)
    ejes_tau(dr, 110, y0, h, 2, fm, [F(0), F(1, 16), F(1, 8), F(1, 4), F(1, 3), F(3, 8), F(1, 2), F(1), F(2)])
    for j in range(17):
        dr.line((110 + 32 * j, y0 + h + 4, 110 + 32 * j, y0 + h + (12 if j % 4 == 0 else 7)), fill=MUTED)
    dr.text((110, y0 + h + 16), 'corrimiento: 0 … 15 dieciseisavos', font=fm, fill=MUTED)
    x0, w = 700, 840
    dr.rectangle((x0, y0, x0 + w, y0 + h), outline=GRID)
    for t in range(0, int(dur) + 1, 4):
        xx = x0 + w * t / dur; dr.line((xx, y0, xx, y0 + h), fill=GRID); dr.text((xx - 8, y0 + h + 6), f'{t}', font=fm, fill=MUTED)
    dr.line([(x0 + w * tc / dur, y0 + h * tau / 2) for tc, tau in ruta], fill=ACENTO, width=3)
    for tc, tau in ruta[::40]:
        dr.line((622, y0 + h * tau / 2, x0 + w * tc / dur, y0 + h * tau / 2), fill=GRID)
    dr.text((x0, y0 + h + 24), 'segundos de la muestra 3 (48 s)', font=fm, fill=MUTED)
    return im


def lamina_canon(sonda_r):
    W, Hh = 1600, 960; im = Image.new('RGB', (W, Hh), BG); dr = ImageDraw.Draw(im)
    ft, fs, fm = fuente(30, True), fuente(15), fuente(13)
    dr.text((48, 26), '03 · QUIÉN SUENA EN CADA RACIONAL · LAS SUMAS DE GAUSS', font=ft, fill=FG)
    dr.text((48, 66), 'cada fila: un τ = p/q (exacto, todos los armónicos) · los círculos son las copias del loop en su corrimiento; tamaño |c|, color: fase', font=fs, fill=MUTED)
    c = sonda_r['copias_exactas']; x0, w = 260, 1000; y = 120; paso = 62
    for t in range(0, 11):
        xx = x0 + w * t / 10; dr.line((xx, 110, xx, 112 + paso * len(c)), fill=GRID)
    for key, v in c.items():
        dr.text((60, y + 10), f'τ = {key}', font=fuente(17, True), fill=FG)
        dr.text((150, y + 13), f'{v["voces"]} de {v["L"]}', font=fm, fill=MUTED)
        for sh, fase in zip(v['corrimientos_T'], v['fase_pesos_grados']):
            a, b = sh.split('/'); xx = x0 + w * int(a) / int(b); r = 22 * v['peso_abs'] ** .5
            col = oklch(.78, .16, H0 + fase)
            dr.ellipse((xx - r, y + 20 - r, xx + r, y + 20 + r), fill=col)
            dr.text((xx - 14, y + 42), f'{fase:+.0f}°', font=fuente(11), fill=MUTED)
        y += paso
    dr.text((x0 - 4, y + 6), '0', font=fm, fill=MUTED); dr.text((x0 + w - 4, y + 6), '1', font=fm, fill=MUTED)
    dr.text((x0 + w / 2 - 190, y + 6), 'corrimiento dentro del loop (fracción de T)', font=fm, fill=MUTED)
    lin = [f'error de la suma de copias contra la fase cuadrática: ≤ {max(v["error_rel"] for v in c.values()):.1e}',
           f'sumas de Gauss contra (p|q)·ε_q·√q, q primo ≤ 23: error {sonda_r["gauss_vs_reciprocidad_err"]:.1e}',
           f'τ = 1 contra el loop corrido medio periodo: {sonda_r["tau_1_vs_medio_periodo"]:.1e} · τ = 2 contra el loop: {sonda_r["tau_2_vs_identidad"]:.1e}']
    for k, s in enumerate(lin): dr.text((60, 862 + 24 * k), s, font=fm, fill=MUTED)
    return im


def lamina_espectros(muestras, rutas):
    W, Hh = 1600, 960; im = Image.new('RGB', (W, Hh), BG); dr = ImageDraw.Draw(im)
    ft, fm = fuente(30, True), fuente(13)
    dr.text((48, 26), '04 · LAS CUATRO MUESTRAS · ESPECTROGRAMA Y CAMINO τ(t)', font=ft, fill=FG)
    y0 = 84
    for k, (nombre, y) in enumerate(muestras):
        x0, w, h = 220, 1330, 170
        f, t, Z = stft(y.sum(1), SR, nperseg=2048, noverlap=1536)
        fl = np.geomspace(40, 12000, h); Zl = np.array([np.interp(fl, f, np.abs(Z[:, j])) for j in range(Z.shape[1])]).T
        D = np.clip((20 * np.log10(Zl / Zl.max() + 1e-9) + 70) / 70, 0, 1)[::-1]
        cols = np.linspace(0, D.shape[1] - 1, w).astype(int)
        im.paste(pinta(D[:, cols], w, h, H0 + 90 * k), (x0, y0)); dr = ImageDraw.Draw(im)
        rt = rutas[nombre]; dur = len(y) / SR
        dr.line([(x0 + w * tc / dur, y0 + h - h * tau / 2.05) for tc, tau in rt], fill=ACENTO, width=2)
        dr.text((48, y0 + 6), f'{k + 1}. {nombre}', font=fuente(17, True), fill=FG)
        dr.text((48, y0 + 32), f'{dur:.0f} s\nlínea: τ(t)\n(0 abajo, 2 arriba)', font=fm, fill=MUTED)
        y0 += h + 47
    return im


# ───────────── main ─────────────
def main():
    ej = hashlib.sha256(Path(__file__).read_bytes() + str(SEMILLA).encode() + os.urandom(16)).hexdigest()
    out = AQUI / f'tapete-de-talbot-s{SEMILLA}-{ej[:12]}'
    out.mkdir(parents=False, exist_ok=False)
    print('1. sonda…', flush=True); s = sonda(); print(json.dumps(s, ensure_ascii=False), flush=True)

    bat = loop_bateria()
    plan = [('clave', loop_clave(), 26.0, None), ('bateria', bat, 40.0, None), ('bateria-16', bat, 48.0, 16), ('canon', loop_tema(), 48.0, None)]
    muestras, rutas, med = [], {}, {}
    for k, (nombre, x, dur, hilos) in enumerate(plan, 1):
        print(f'{k + 1}. muestra {nombre}…', flush=True)
        y, rt = leer(x, camino_por_nudos(CAMINOS[nombre]), dur, hilos)
        med[nombre] = {**guardar(y, out / f'muestra-{k}-{nombre}-s{SEMILLA}'), 'hilos': hilos or 'todos'}
        muestras.append((nombre, y)); rutas[nombre] = rt

    print('6. láminas…', flush=True)
    ims = [lamina_urdimbres(s), lamina_bateria16(rutas['bateria-16'], 48.0), lamina_canon(s), lamina_espectros(muestras, rutas)]
    for n, im in zip(('01-tres-urdimbres', '02-bateria-16-hilos', '03-quien-suena', '04-espectrogramas'), ims):
        im.save(out / f'{n}-s{SEMILLA}.png')

    print('7. GIF…', flush=True)   # el tapete tejiéndose fila por fila (τ de 0 a 2), y luego las otras láminas
    cuadros = [lamina_urdimbres(s, filas_hasta=k / 8) for k in range(1, 8)] + ims
    q = [c.resize((960, 576), Image.Resampling.LANCZOS).quantize(colors=200, method=Image.Quantize.MEDIANCUT) for c in cuadros]
    gif = out / f'proceso-tapete-de-talbot-s{SEMILLA}.gif'
    dur_ms = [600] * 7 + [1300] * 4
    q[0].save(gif, save_all=True, append_images=q[1:], duration=dur_ms, loop=0, optimize=True)

    shutil.copyfile(__file__, out / 'tapete.py')
    receta = {'instrumento': 'El tapete de Talbot', 'fecha': '2026-10-21', 'semilla': SEMILLA, 'ejecucion_sha256': ej,
              'sonda': s, 'muestras': med,
              'caminos': {k: [[t, str(v) if isinstance(v, Fraction) else v] for t, v in c] for k, c in CAMINOS.items()},
              'gif': {'archivo': gif.name, 'cuadros': len(q), 'dur_s': sum(dur_ms) / 1000, 'bytes': gif.stat().st_size}}
    (out / f'receta-tapete-de-talbot-s{SEMILLA}.json').write_text(json.dumps(receta, ensure_ascii=False, indent=1), encoding='utf-8')
    print('listo:', out.name, json.dumps(med, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
