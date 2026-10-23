"""Los ceros que tocan a los primos — un instrumento de rejilla desde la función zeta de Riemann (21 oct 2026).

La fórmula explícita (Riemann–von Mangoldt), escrita en u = log x:

        Σ_n Λ(n) n^{−1/2} δ(u − log n)  =  e^{u/2}  −  2 Σ_{γ>0} cos(γ u)  −  (ceros triviales, despreciable)

donde ½ + iγ recorre los ceros no triviales y Λ(n) = log p si n = p^k (cero si no). Es decir: la suma de un coseno
por cada cero, −2 Σ cos(γ_n u), se cancela casi en todas partes y sólo se refuerza en u = log 2, log 3, log 4,
log 5, log 7, log 8, log 9, log 11… con peso log p / p^{k/2}. Nadie escribe ese ritmo: lo deciden los ceros.

El instrumento suena esa suma con u(t) = ∫ r(t) dt:
  · r grande  → cada cero es un parcial de frecuencia γ_n·r/2π: un acorde inarmónico (los ceros no guardan razón).
  · r chico   → los mismos cosenos son lentos y su interferencia da golpes en los log p^k: el ritmo de los primos.
  · γ_max     → la nitidez: con 12 ceros los primos son oleajes; con 2000, golpes secos (ancho ≈ π/γ_max en u).
Los pesos llevan una ventana cos²(π/2 · γ/γ_max) para que el corte no suene a Gibbs.

La muestra es un palíndromo con espejo en el 2: u corre HACIA ATRÁS desde 346 (el acorde), frena exponencialmente
(la escala baja, los primos llegan al revés: …7, 5, 3, 2), da la vuelta en u = 0.45 y avanza: 2, 3, 4, 5, 7…
en accelerando hasta el rugido. Una tarola cae en los picos que se DETECTAN en el audio (no desde una lista de primos).

Ejecutar: python ceros_primos.py   (necesita datos/ceros-zeta-2000.json, de ceros.py)
"""
import hashlib, json, math, os, shutil, subprocess
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfiltfilt, sosfilt, find_peaks, resample_poly, stft
from PIL import Image, ImageDraw, ImageFont

SEMILLA = 20261021
SR = 48000
SRC = 2000                        # la suma se calcula a 2 kHz: su banda nunca pasa de ~750 Hz (ver γ_max·r/2π)
AQUI = Path(__file__).resolve().parent
DATOS = json.loads((AQUI / 'datos' / 'ceros-zeta-2000.json').read_text(encoding='utf-8'))
GAMMA = np.array(DATOS['gammas'])


# ───────────── la aritmética ─────────────
def mangoldt(n):
    """Λ(n): log p si n = p^k, si no 0."""
    if n < 2: return 0.0
    for p in range(2, int(n ** .5) + 2):
        if n % p == 0:
            while n % p == 0: n //= p
            return math.log(p) if n == 1 else 0.0
    return math.log(n)


def potencias_de_primos(hasta):
    return [(n, mangoldt(n)) for n in range(2, hasta + 1) if mangoldt(n) > 0]


def peso(gmax):
    g = np.asarray(gmax, float)
    x = GAMMA[None, :] / g[..., None]
    return np.where(x < 1, np.cos(np.pi / 2 * x) ** 2, 0.0)


def suma(u, gmax, paridad=None):
    """−2 Σ w_n cos(γ_n u), en trozos. paridad: None (todos), 0 (n par) o 1 (n impar) para el estéreo del acorde."""
    u = np.asarray(u, float); gmax = np.broadcast_to(np.asarray(gmax, float), u.shape)
    sel = np.arange(len(GAMMA)) if paridad is None else np.arange(paridad, len(GAMMA), 2)
    out = np.zeros_like(u)
    for a in range(0, len(u), 2048):
        uu, gg = u[a:a + 2048], gmax[a:a + 2048]
        W = peso(gg)[:, sel]
        out[a:a + 2048] = -2 * np.sum(W * np.cos(GAMMA[sel][None, :] * uu[:, None]), axis=1)
    return out


def esperado(u, gmax, hasta=200000):
    """El lado izquierdo, suavizado con el mismo núcleo: Σ Λ(n) n^{−1/2} K(u − log n) − (e^{u/2} suavizada).
    K(v) = −2 Σ w_n cos(γ_n v) restringido... aquí sólo se usan las posiciones log n para comparar picos."""
    return [(math.log(n), lam / math.sqrt(n), n) for n, lam in potencias_de_primos(hasta)]


# ───────────── el camino: u(t), r(t), γ_max(t) ─────────────
T_I, T_II, T_III, F_BANDA, U_ESPEJO = 9.0, 7.0, 25.0, 180.0, 0.45
F1 = 73.416                                   # re2: el primer cero suena aquí en el acorde
R_ACORDE = 2 * math.pi * F1 / GAMMA[0]        # ≈ 32.6 unidades de u por segundo
R_RITMO = 0.45
DUR = T_I + T_II + T_III


def camino(sr=SRC):
    t = np.arange(int(DUR * sr)) / sr
    tau = T_II / math.log(R_ACORDE / R_RITMO)
    r = np.where(t < T_I, -R_ACORDE, np.where(t < T_I + T_II, -R_ACORDE * np.exp(-(t - T_I) / tau), R_RITMO))
    u = np.cumsum(r) / sr
    u = u - u[int((T_I + T_II) * sr)] + U_ESPEJO          # u vale 0.45 justo en el espejo
    # nitidez: el acorde va de 12 a 48 ceros; en la bajada se suman ceros manteniendo la banda ≤ 180 Hz; en el ritmo, los 2000
    g_acorde = np.interp(t, [0, 6.0, T_I], [GAMMA[11] * 1.02, GAMMA[47] * 1.02, GAMMA[47] * 1.02])
    g_banda = np.clip(2 * math.pi * F_BANDA / np.abs(r), GAMMA[47] * 1.02, GAMMA[-1] * 1.0001)
    gmax = np.where(t < T_I, g_acorde, g_banda)
    abierto = np.clip(1 - (t - T_I) / T_II, 0, 1)            # estéreo del acorde (pares a un lado, impares al otro) → mono en el ritmo
    return t, u, r, gmax, abierto


# ───────────── sonido ─────────────
def tarola(rng, v):
    L = int(.35 * SR); t = np.arange(L) / SR
    ruido = sosfilt(butter(2, [1400, 7000], 'band', fs=SR, output='sos'), rng.standard_normal(L)) * np.exp(-t / .09)
    return v * (.5 * np.sin(2 * math.pi * 186 * t) * np.exp(-t / .05) + ruido) * np.minimum(1, t / .0006)


def aro(v):
    L = int(.08 * SR); t = np.arange(L) / SR
    return v * sum(a * np.sin(2 * math.pi * f * t) * np.exp(-t / d) for f, a, d in ((1720, 1, .011), (2930, .5, .006)))


def golpes(y, t, sr=SRC, desde=T_I + 4.0):
    """Picos de la suma: prominencia > 3.5× el rms local (0.5 s), separados ≥ 25 ms. Sólo después de que hay nitidez."""
    hp = sosfiltfilt(butter(2, 25, 'high', fs=sr, output='sos'), y)
    rms = np.sqrt(np.convolve(hp ** 2, np.ones(sr // 2) / (sr // 2), 'same')) + 1e-12
    pk, pr = find_peaks(hp, distance=int(.025 * sr))
    k = pk[(hp[pk] > 3.5 * rms[pk]) & (t[pk] >= desde)]
    return k, hp[k] / rms[k]


def render():
    t, u, r, gmax, abierto = camino()
    par, impar = suma(u, gmax, 0), suma(u, gmax, 1)
    mono = par + impar
    norma = np.sqrt(np.sum(peso(gmax) ** 2, axis=1)) + 1e-9                   # el acorde y el ritmo al mismo orden
    L = (mono + .55 * abierto * (par - impar)) / norma
    R = (mono - .55 * abierto * (par - impar)) / norma
    k, fuerza = golpes(mono / norma, t)
    y = np.stack([L, R], 1)
    y = sosfiltfilt(butter(2, 25, 'high', fs=SRC, output='sos'), y, axis=0)
    y = resample_poly(y, SR // SRC, 1, axis=0)
    y = np.tanh(1.6 * y / (np.percentile(np.abs(y), 99.5) + 1e-9)) / math.tanh(1.6)   # un poco de grano de órgano
    rng = np.random.default_rng(SEMILLA); tar = np.zeros_like(y)
    for i, f in zip(k, fuerza):
        a = int(t[i] * SR); g = tarola(rng, min(1.0, f / 9)) if f > 5 else aro(min(1.0, f / 5))
        n = min(len(g), len(tar) - a); tar[a:a + n] += g[:n, None] * np.array([.95, 1.0])
    fade = np.minimum(1, (DUR - np.arange(len(y)) / SR) / 2.5)[:, None]
    mezcla = (y + .30 * tar) * np.clip(fade, 0, 1)
    return mezcla, mono / norma, {'t': t, 'u': u, 'r': r, 'gmax': gmax, 'golpes_t': t[k], 'golpes_u': u[k], 'golpes_fuerza': fuerza}


# ───────────── sondas ─────────────
def emparejar(u_picos, alturas, umin, umax, tol=0.004):
    pp = [(lu, w, n) for lu, w, n in esperado(None, None) if umin <= lu <= umax]
    usados, aciertos, err = set(), [], []
    for lu, w, n in pp:
        if len(u_picos) == 0: break
        j = int(np.argmin(np.abs(u_picos - lu)))
        if abs(u_picos[j] - lu) < tol and j not in usados:
            usados.add(j); aciertos.append((n, w, float(alturas[j]))); err.append(abs(u_picos[j] - lu))
    falsos = [float(u_picos[j]) for j in range(len(u_picos)) if j not in usados]
    return pp, aciertos, err, falsos


def sonda():
    r = {'ceros': DATOS['comprobacion']}
    # 1. en u (la fórmula): para cada n = p^k, la altura de la suma en log n contra el ruido de fondo
    #    (mediana de la desviación absoluta lejos de toda potencia de primo). Un pico «se oye» si pasa 5× ese ruido.
    u = np.arange(0.5, 7.0, 1e-4)
    pp = [(math.log(n), lam / math.sqrt(n), n) for n, lam in potencias_de_primos(int(math.exp(7.0)))]
    lejos = np.ones_like(u, bool)
    for lu, _, _ in pp: lejos &= np.abs(u - lu) > 0.004
    for N, clave in ((2000, 'en_u_con_2000_ceros'), (100, 'en_u_con_100_ceros')):
        s = suma(u, GAMMA[N - 1] * 1.0001)
        d = s - np.convolve(s, np.ones(801) / 801, 'same')          # sin la tendencia e^{u/2}
        ruido = 1.4826 * np.median(np.abs(d[lejos] - np.median(d[lejos]))) + 1e-12
        alt = []
        for lu, w, n in pp:
            m = np.abs(u - lu) < max(0.0008, math.pi / GAMMA[N - 1])
            alt.append((n, w, float(float(d[m].max()) / ruido) if m.any() else 0.0))
        oye = [x for x in alt if x[2] > 5]
        falta = next((n for n, _, snr in alt if snr <= 5), None)
        ws = np.array([w for _, w, _ in oye]); hs = np.array([h for _, _, h in oye])
        r[clave] = {'potencias_de_primos_hasta_e7': len(pp), 'se_oyen_5x_ruido': len(oye), 'todas_hasta': max([n for n, _, _ in alt if falta is None or n < falta] or [None], key=lambda v: v or 0),
                    'primera_que_no': falta, 'correlacion_altura_vs_logp_sobre_raiz_n': round(float(np.corrcoef(ws, hs)[0, 1]), 4) if len(oye) > 2 else None,
                    'snr_de_2_3_16_101': {str(n): round(float(snr), 1) for n, _, snr in alt if n in (2, 3, 16, 101)}}
    return r


def sonda_audio(mono, meta):
    """3. En el audio que suena (antes de la tarola): los golpes detectados, convertidos a u, contra los log p^k."""
    gu, gf = np.asarray(meta['golpes_u']), np.asarray(meta['golpes_fuerza'])
    ida = meta['golpes_t'] >= T_I + T_II
    vuelta = ~ida
    out = {}
    for nombre, m in (('ida_III', ida), ('vuelta_II', vuelta)):
        if not m.any(): out[nombre] = None; continue
        uu = gu[m]; lo, hi = float(uu.min()) - .01, float(uu.max()) + .01
        pp, ac, err, fa = emparejar(uu, gf[m], max(.5, lo), hi, tol=0.006)
        # hasta dónde se resuelven todas: la primera potencia de primo que falta
        faltan = [n for _, _, n in pp if n not in {a for a, _, _ in ac}]
        out[nombre] = {'golpes': int(m.sum()), 'rango_u': [round(lo, 3), round(hi, 3)], 'potencias_en_rango': len(pp),
                       'acertadas': len(ac), 'golpes_falsos': len(fa), 'primera_que_falta': faltan[0] if faltan else None,
                       'todas_hasta': max([n for _, _, n in pp if all(x not in faltan for x in range(2, n + 1))] or [None], key=lambda v: v or 0),
                       'error_max_ms': round(max(err) / R_RITMO * 1000, 2) if err and nombre == 'ida_III' else (round(max(err), 4) if err else None),
                       'primeras': [a for a, _, _ in ac[:16]]}
    # 4. el acorde: picos del espectro en 1–8 s contra γ_n·r/2π
    t = meta['t']; sel = (t > 1.0) & (t < 8.0)
    Y = np.abs(np.fft.rfft(mono[sel] * np.hanning(sel.sum()))); fr = np.fft.rfftfreq(sel.sum(), 1 / SRC)
    esperadas = GAMMA[:12] * R_ACORDE / (2 * math.pi)
    medidas = [float(fr[np.argmax(np.where(np.abs(fr - f) < 1.5, Y, 0))]) for f in esperadas]
    out['acorde'] = {'primeros_12_Hz_esperados': [round(f, 2) for f in esperadas], 'medidos': [round(f, 2) for f in medidas],
                     'error_max_Hz': round(float(np.max(np.abs(np.array(medidas) - esperadas))), 3)}
    return out


# ───────────── audio ─────────────
def medir(wav):
    o = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(wav), '-af', 'loudnorm=print_format=json', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    j = json.loads(o[o.rindex('{'):o.rindex('}') + 1]); return float(j['input_i']), float(j['input_tp']), float(j['input_lra'])


def guardar(y, base, lufs=-16.0):
    y = y / (np.abs(y).max() + 1e-12) * .5; wav = base.with_suffix('.wav'); wavfile.write(str(wav), SR, y.astype(np.float32))
    i, _, _ = medir(wav); y = y * 10 ** ((lufs - i) / 20)
    y = np.where(np.abs(y) > .7, np.sign(y) * (.7 + .19 * np.tanh((np.abs(y) - .7) / .19)), y)
    wavfile.write(str(wav), SR, y.astype(np.float32))
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(wav), '-c:a', 'aac', '-b:a', '192k', str(base.with_suffix('.m4a'))], check=True)
    i, tp, lra = medir(wav)
    return {'archivo': base.with_suffix('.m4a').name, 'dur_s': round(len(y) / SR, 2), 'LUFS': i, 'dBTP': tp, 'LRA': lra,
            'sha256_wav': hashlib.sha256(wav.read_bytes()).hexdigest()[:16]}


# ───────────── láminas ─────────────
def oklch(L, C, h):
    a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
    l_, m_, s_ = L + .3963377774 * a + .2158037573 * b, L - .1055613458 * a - .0638541728 * b, L - .0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    rgb = (4.0767416621 * l - 3.3077115913 * m + .2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - .3413193965 * s,
           -.0041960863 * l - .7034186147 * m + 1.7076147010 * s)
    f = lambda x: 12.92 * x if x <= .0031308 else 1.055 * x ** (1 / 2.4) - .055
    return tuple(int(round(max(0, min(1, f(max(0, min(1, c))))) * 255)) for c in rgb)


H0 = float(np.random.default_rng(SEMILLA + 7).uniform(0, 360))
BG, FG, MUTED, GRID = oklch(.13, .025, H0), oklch(.93, .02, H0 + 30), oklch(.64, .035, H0 + 20), oklch(.28, .03, H0)
CERO, PRIMO, ACENTO = oklch(.80, .14, H0 + 150), oklch(.78, .16, H0 + 30), oklch(.85, .15, H0 + 260)


def fuente(n, bold=False):
    for c in ('C:/Windows/Fonts/consolab.ttf' if bold else 'C:/Windows/Fonts/consola.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'):
        if os.path.exists(c): return ImageFont.truetype(c, n)
    return ImageFont.load_default()


def lienzo(titulo, sub):
    im = Image.new('RGB', (1600, 960), BG); dr = ImageDraw.Draw(im)
    dr.text((48, 26), titulo, font=fuente(30, True), fill=FG); dr.text((48, 66), sub, font=fuente(15), fill=MUTED)
    return im, dr


def curva(dr, xs, ys, caja, col, lo=None, hi=None, w=1):
    x0, y0, x1, y1 = caja; lo = np.min(ys) if lo is None else lo; hi = np.max(ys) if hi is None else hi
    X = x0 + (x1 - x0) * (np.asarray(xs) - xs[0]) / (xs[-1] - xs[0]); Y = y1 - (y1 - y0) * (np.clip(ys, lo, hi) - lo) / (hi - lo + 1e-12)
    dr.line(list(zip(X.tolist(), Y.tolist())), fill=col, width=w)


def lamina_ceros(son):
    im, dr = lienzo('01 · LOS CEROS · CALCULADOS AQUÍ (RIEMANN–SIEGEL + EULER–MACLAURIN)',
                    'izquierda: los primeros 40 ceros ½ + iγ en la recta crítica · derecha: cuántos hay bajo T contra θ(T)/π + 1')
    f = fuente(13); x0 = 120
    dr.line((x0, 110, x0, 900), fill=GRID, width=2)
    for k, g in enumerate(GAMMA[:40]):
        y = 900 - 790 * g / GAMMA[39]
        dr.ellipse((x0 - 5, y - 5, x0 + 5, y + 5), fill=CERO)
        if k < 12 or k % 4 == 0: dr.text((x0 + 14, y - 8), f'γ{k + 1} = {g:.6f}', font=f, fill=MUTED)
    dr.text((x0 - 30, 905), 'σ = ½', font=f, fill=MUTED)
    caja = (560, 120, 1540, 760); dr.rectangle(caja, outline=GRID)
    T = np.linspace(10, GAMMA[-1], 2000); cnt = np.searchsorted(GAMMA, T)
    th = T / 2 * np.log(T / (2 * math.pi)) - T / 2 - math.pi / 8
    curva(dr, T, cnt, caja, CERO, 0, 2000, 2); curva(dr, T, th / math.pi + 1, caja, PRIMO, 0, 2000, 1)
    dr.text((570, 130), 'N(T): los 2000 ceros encontrados', font=fuente(15, True), fill=CERO)
    dr.text((570, 154), 'θ(T)/π + 1 (Riemann–von Mangoldt)', font=fuente(15), fill=PRIMO)
    c = son['ceros']
    for k, s in enumerate([f'ceros: {c["cuantos"]}, el último γ = {c["ultimo_gamma"]}',
                           f'primeros 10 contra los publicados: error {c["error_max_primeros_10"]:.1e}',
                           f'cuenta: {c["cuenta_contra_riemann_von_mangoldt"]["encontrados"]} contra {c["cuenta_contra_riemann_von_mangoldt"]["N_T_suave"]} (suave)',
                           f'separación mínima entre ceros: {c["separacion_minima"]}']):
        dr.text((570, 790 + 26 * k), s, font=fuente(15), fill=FG if k == 0 else MUTED)
    return im


def lamina_suma(n_hasta=None, titulo=True):
    im, dr = lienzo('02 · LA SUMA DE LOS CEROS ENCUENTRA A LOS PRIMOS', '−2 Σ w_n cos(γ_n u) con más y más ceros · las rayas son log n para n = p^k (su peso: log p / √n)')
    u = np.linspace(0.45, 3.75, 2400)
    filas = [10, 40, 200, 2000] if n_hasta is None else [n_hasta]
    alto = 760 // len(filas)
    marcas = [(math.log(n), w, n) for n, lam in potencias_de_primos(42) for w in [lam / math.sqrt(n)]]
    for i, N in enumerate(filas):
        y0 = 110 + i * alto; caja = (120, y0 + 10, 1540, y0 + alto - 14)
        for lu, w, n in marcas:
            x = 120 + 1420 * (lu - u[0]) / (u[-1] - u[0])
            dr.line((x, caja[1], x, caja[3]), fill=GRID)
            if i == len(filas) - 1: dr.text((x - 6, caja[3] + 2), str(n), font=fuente(11), fill=PRIMO)
        s = suma(u, GAMMA[N - 1] * 1.0001)
        curva(dr, u, s, caja, CERO, None, None, 1)
        dr.text((48, y0 + 14), f'{N}\nceros', font=fuente(15, True), fill=FG)
    return im


def lamina_muestra(y, meta):
    im, dr = lienzo('03 · LA MUESTRA · ACORDE → LA ESCALA BAJA → ESPEJO EN EL 2 → ACCELERANDO',
                    'espectrograma 30 Hz – 4 kHz · abajo: u(t) (log x), la rapidez |r| y la nitidez γ_max · rayas: los golpes detectados (tarola)')
    f, tt, Z = stft(y.sum(1), SR, nperseg=4096, noverlap=3072)
    h, w = 430, 1420; fl = np.geomspace(30, 4000, h)
    D = np.array([np.interp(fl, f, np.abs(Z[:, j])) for j in range(Z.shape[1])]).T
    D = np.clip((20 * np.log10(D / D.max() + 1e-9) + 70) / 70, 0, 1)[::-1]
    cols = np.linspace(0, D.shape[1] - 1, w).astype(int); D = D[:, cols]
    img = np.zeros((h, w, 3), np.uint8); lut = {}
    for i in range(h):
        for j in range(w):
            v = round(float(D[i, j]) * 32) / 32
            if v not in lut: lut[v] = oklch(.10 + .82 * v ** 1.3, .02 + .15 * v, H0 + 150 + 60 * v)
            img[i, j] = lut[v]
    im.paste(Image.fromarray(img), (120, 110)); dr = ImageDraw.Draw(im)
    t = meta['t']
    for tg in meta['golpes_t']:
        x = 120 + w * tg / DUR; dr.line((x, 545, x, 560), fill=ACENTO)
    for k, (clave, nombre, col, lo, hi, logy) in enumerate((('u', 'u = log x', CERO, 0, 30, False), ('r', '|r| (u por segundo)', PRIMO, None, None, True),
                                                             ('gmax', 'γ_max (nitidez)', ACENTO, None, None, True))):
        caja = (120, 580 + k * 120, 1540, 680 + k * 120); dr.rectangle(caja, outline=GRID)
        v = np.abs(meta[clave]); v = np.log10(v + 1e-9) if logy else np.minimum(v, hi)
        curva(dr, t, v, caja, col, lo if not logy else None, hi if not logy else None, 2)
        dr.text((40, caja[1] + 4), nombre, font=fuente(13, True), fill=col)
    for s in range(0, int(DUR) + 1, 5):
        x = 120 + w * s / DUR; dr.text((x - 6, 942), f'{s}', font=fuente(12), fill=MUTED)
    for xx, et in ((T_I, 'II'), (T_I + T_II, 'III · espejo')):
        x = 120 + w * xx / DUR; dr.line((x, 110, x, 920), fill=GRID); dr.text((x + 4, 112), et, font=fuente(13, True), fill=FG)
    dr.text((124, 112), 'I · acorde', font=fuente(13, True), fill=FG)
    return im


def lamina_sonda(son, sa, meta):
    im, dr = lienzo('04 · LA SONDA EN EL AUDIO QUE SUENA', 'los golpes detectados en la suma (antes de la tarola), pasados a u, contra log p^k')
    f, fb = fuente(15), fuente(17, True); y = 120
    e = son['en_u_con_2000_ceros']; e1 = son['en_u_con_100_ceros']
    lin = [('En u (la fórmula), u de 0.5 a 7 (n hasta 1096): el pico en log n contra el ruido de fondo', None),
           (f'  con 2000 ceros: {e["se_oyen_5x_ruido"]} de {e["potencias_de_primos_hasta_e7"]} potencias de primos pasan 5× el ruido; todas hasta n = {e["todas_hasta"]}, la primera que no: {e["primera_que_no"]}', FG),
           (f'  altura contra log p / √n: correlación {e["correlacion_altura_vs_logp_sobre_raiz_n"]} · señal/ruido de ' + ', '.join(f'{k}: {v}' for k, v in e['snr_de_2_3_16_101'].items()), MUTED),
           (f'  con 100 ceros: sólo {e1["se_oyen_5x_ruido"]} pasan (los picos son anchos y se enciman: la nitidez es el número de ceros)', MUTED)]
    for nombre, clave in (('III, la ida (u avanza a 0.45/s)', 'ida_III'), ('II, la vuelta (u retrocede, frenando)', 'vuelta_II')):
        a = sa[clave]
        if a is None: continue
        lin += [(f'En el audio, {nombre}:', None),
                (f'  {a["golpes"]} golpes detectados · {a["acertadas"]} caen en una potencia de primo (±{"13 ms" if clave == "ida_III" else "0.006 en u"}) · {a["golpes_falsos"]} falsos · u de {a["rango_u"][0]} a {a["rango_u"][1]}', FG),
                (f'  todas, sin faltar una, hasta n = {a["todas_hasta"]} · la primera que falta: {a["primera_que_falta"]}', MUTED),
                (f'  las primeras: {a["primeras"]}', MUTED)]
    ac = sa['acorde']
    lin += [('El acorde (I, 1–8 s):', None), (f'  los 12 primeros ceros caen en γ·r/2π con error ≤ {ac["error_max_Hz"]} Hz: ' + ', '.join(f'{v:.1f}' for v in ac['medidos'][:8]) + '… Hz', FG)]
    for s, col in lin:
        if col is None: y += 10; dr.text((60, y), s, font=fb, fill=PRIMO); y += 32
        else: dr.text((60, y), s, font=f, fill=col); y += 28
    # la línea de tiempo en u de la ida: rayas = log p^k, puntos = golpes
    caja = (120, 760, 1540, 900); dr.rectangle(caja, outline=GRID)
    m = meta['golpes_t'] >= T_I + T_II; gu = meta['golpes_u'][m]; u0, u1 = .5, 4.6
    for n, lam in potencias_de_primos(int(math.exp(u1))):
        x = 120 + 1420 * (math.log(n) - u0) / (u1 - u0); hgt = 120 * min(1, lam / math.sqrt(n) / .5)
        dr.line((x, 900, x, 900 - hgt), fill=PRIMO)
    for g in gu:
        if u0 <= g <= u1:
            x = 120 + 1420 * (g - u0) / (u1 - u0); dr.ellipse((x - 3, 768, x + 3, 774), fill=ACENTO)
    dr.text((120, 906), f'u = {u0} … {u1}: rayas = log n (alto: log p/√n) · puntos = golpes detectados en el audio', font=fuente(13), fill=MUTED)
    return im


# ───────────── main ─────────────
def main():
    ej = hashlib.sha256(Path(__file__).read_bytes() + str(SEMILLA).encode() + DATOS['sha256_gammas'].encode() + os.urandom(16)).hexdigest()
    out = AQUI / f'ceros-que-tocan-primos-s{SEMILLA}-{ej[:12]}'; out.mkdir(parents=False, exist_ok=False)
    print('1. sonda en u…', flush=True); son = sonda(); print(json.dumps(son, ensure_ascii=False), flush=True)
    print('2. la muestra…', flush=True); y, mono, meta = render()
    med = guardar(y, out / f'muestra-ceros-que-tocan-primos-s{SEMILLA}')
    print('3. sonda en el audio…', flush=True); sa = sonda_audio(mono, meta); print(json.dumps(sa, ensure_ascii=False), flush=True)
    print('4. láminas y GIF…', flush=True)
    ims = [lamina_ceros(son), lamina_suma(), lamina_muestra(y, meta), lamina_sonda(son, sa, meta)]
    for n, im in zip(('01-los-ceros', '02-la-suma-encuentra-a-los-primos', '03-la-muestra', '04-la-sonda-en-el-audio'), ims):
        im.save(out / f'{n}-s{SEMILLA}.png')
    cuadros = [lamina_suma(N) for N in (1, 2, 3, 5, 8, 13, 25, 50, 100, 200, 500, 1000, 2000)]
    q = [c.resize((960, 576), Image.Resampling.LANCZOS).quantize(colors=128, method=Image.Quantize.MEDIANCUT) for c in cuadros]
    gif = out / f'proceso-ceros-que-tocan-primos-s{SEMILLA}.gif'
    dur_ms = [550] * 12 + [2400]
    q[0].save(gif, save_all=True, append_images=q[1:], duration=dur_ms, loop=0, optimize=True)
    shutil.copyfile(__file__, out / 'ceros_primos.py')
    receta = {'instrumento': 'Los ceros que tocan a los primos', 'fecha': '2026-10-21', 'semilla': SEMILLA, 'ejecucion_sha256': ej,
              'ceros': {'archivo': 'datos/ceros-zeta-2000.json', 'sha256_gammas': DATOS['sha256_gammas'], **DATOS['comprobacion']},
              'camino': {'T_I': T_I, 'T_II': T_II, 'T_III': T_III, 'F1_Hz': F1, 'R_acorde': R_ACORDE, 'R_ritmo': R_RITMO,
                         'U_espejo': U_ESPEJO, 'banda_Hz': F_BANDA, 'u_inicial': float(meta['u'][0])},
              'sonda_en_u': son, 'sonda_en_el_audio': sa, 'muestra': med, 'golpes': len(meta['golpes_t']),
              'gif': {'archivo': gif.name, 'cuadros': len(q), 'dur_s': sum(dur_ms) / 1000, 'bytes': gif.stat().st_size}}
    (out / f'receta-ceros-que-tocan-primos-s{SEMILLA}.json').write_text(json.dumps(receta, ensure_ascii=False, indent=1), encoding='utf-8')
    print('listo:', out.name, json.dumps(med, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
