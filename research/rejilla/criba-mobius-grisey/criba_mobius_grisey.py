"""Construcción, sonda y producción real de El Candelabro (Criba) de Möbius–Grisey (mu * M_s) para Rejilla.

Ejecuta:
1. Sonda matemática y acústica en `spectrumsynth` (`S = 32768`, `H = 16384`, 1 col = 1.0 s, 1 fila = 1.0 Hz):
   - Prueba 1 (Inversión de Chen–Möbius / Convolución de Dirichlet sum_{d|m} mu(d) = delta_{m,1}):
     Compara un coro subarmónico crudo (donde cada subarmónico f_0/r dispara sus propios sobretonos contaminantes) frente al coro vestido con su inverso de Möbius mu(d). Mide en dB la supresión de los sobretonos compuestos parásitos (m = 2, 3, 4, 5, 6) y la limpieza del espectro subarmónico.
   - Prueba 2 (Huecos Square-Free mu(p^2 k) = 0 para Costura):
     Mide la caída en dB en las filas de los cuadrados perfectos (4f_0, 8f_0, 9f_0, 12f_0) cuando la criba de Möbius está activa (alpha_mu = 1.0) vs inactiva (alpha_mu = 0.0).
   - Prueba 3 (Trampa descubierta por la sonda — Inercia de ataque de Ford vs Cancelación de Dirichlet):
     Si los divisores d entran con retardos de Ford distintos t_d, durante el transitorio inicial la suma sum_{d|m} mu(d) aún no está completa y deja escapar un destello ("chispa aritmética de ataque") antes de cancelar en el sostén. La sonda mide la cancelación con ataques sincrónicos vs ataques escalonados de Ford.
   - Prueba 4 (Espejo de Mellin gamma: +1 -> 0 -> -1 y Sumas de Ramanujan c_q(n)):
     Mide la inversión del centroide espectral entre la torre armónica (gamma = +1) y el abismo subarmónico (gamma = -1), y la selectividad en dB del resonador de Ramanujan en q = 7 y q = 11.
   - Prueba 5 (SNR exacto de `spectrumsynth` gray16le vs suma temporal).
2. Muestra aislada de 24 s (`muestra-criba-mobius-grisey-s20261021.wav` y `.m4a`).
3. Escena en contexto de 24 s (`escena-grisey-siringua-s20261021.wav` y `.m4a`) con Candelabro de Möbius–Grisey + Trombón Fantasma de Mi0 (41.2 Hz, homenaje a *Partiels*) + Siringua/Boca cantando dentro de los túneles square-free (4f_0, 8f_0, 9f_0).
4. Tres láminas PNG en paleta OKLCh sembrada y GIF en loop del proceso.
"""
import hashlib, json, math, os, shutil, subprocess
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import stft, lfilter, iirpeak, butter, sosfilt
from PIL import Image, ImageDraw, ImageFont


SEMILLA = 20261021
SR = 32000

# Salida (rejilla, acuerdo del 13 oct 2026): carpeta exclusiva <pieza>-s<semilla>-<hash12>; nunca se pisa.
# La versión original escribía en el sandbox de otra herramienta (/working_dir/...).
AQUI = Path(__file__).resolve().parent
EJECUCION = hashlib.sha256(Path(__file__).read_bytes() + str(SEMILLA).encode() + os.urandom(16)).hexdigest()
OUT_DIR = AQUI / f'criba-mobius-grisey-s{SEMILLA}-{EJECUCION[:12]}'
INTER_DIR = OUT_DIR / 'intermedio'
if __name__ == '__main__':
    OUT_DIR.mkdir(parents=False, exist_ok=False)
    INTER_DIR.mkdir()

# ───────────── 1. Funciones de Teoría Analítica de Números (Möbius, Ramanujan, Liouville, Ford) ─────────────
def mobius_mu(n: int) -> int:
    """Función mu(n) de Möbius: +1 si libre de cuadrados con par de primos, -1 si impar, 0 si tiene p^2."""
    if n <= 0:
        raise ValueError("n debe ser >= 1")
    if n == 1:
        return 1
    factores = 0
    d = 2
    temp = n
    while d * d <= temp:
        if temp % d == 0:
            factores += 1
            temp //= d
            if temp % d == 0:
                return 0  # Factor cuadrado p^2 divide a n
        d += 1
    if temp > 1:
        factores += 1
    return -1 if (factores % 2 == 1) else 1

def ramanujan_cq(q: int, n: int) -> float:
    """Suma trigonométrica de Ramanujan c_q(n) = sum_{d | gcd(q, n)} mu(q/d) * d."""
    g = math.gcd(q, n)
    total = 0
    for d in range(1, g + 1):
        if g % d == 0:
            total += mobius_mu(q // d) * d
    return float(total)

def euler_phi(q: int) -> int:
    return sum(1 for a in range(1, q + 1) if math.gcd(a, q) == 1)

def radio_ford(p: int, q: int) -> float:
    """Radio del círculo de Ford C[p/q] = 1 / (2 * q^2) para fracción reducida."""
    g = math.gcd(p, q)
    q_red = q // g
    return 1.0 / (2.0 * (q_red ** 2))

# ───────────── 2. Paleta OKLCh Sembrada (Estándar Rejilla) ─────────────
def oklch(L, C, h_deg):
    rad = math.radians(h_deg)
    a = C * math.cos(rad)
    b = C * math.sin(rad)
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    r_lin = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g_lin = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    b_lin = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    def srgb(x):
        x = max(0.0, min(1.0, x))
        return 12.92 * x if x <= 0.0031308 else 1.055 * (x ** (1.0 / 2.4)) - 0.055
    return (int(round(srgb(r_lin) * 255)), int(round(srgb(g_lin) * 255)), int(round(srgb(b_lin) * 255)))

rng_vis = np.random.default_rng(SEMILLA)
H0 = 212.0 + float(rng_vis.uniform(-10.0, 10.0))
BG = oklch(0.12, 0.032, H0)
PANEL_BG = oklch(0.16, 0.038, H0 + 6)
GRID_COL = oklch(0.27, 0.038, H0)
FG = oklch(0.94, 0.022, H0 + 30)
MUTED = oklch(0.67, 0.038, H0 + 12)
COL_MU_POS = oklch(0.80, 0.16, H0 - 75)     # Verde/turquesa brillante: mu = +1 (biprimos y 1)
COL_MU_NEG = oklch(0.74, 0.18, H0 + 125)    # Coral/carmesí: mu = -1 (primos impares en negativo)
COL_MU_ZERO = oklch(0.56, 0.05, H0 + 15)    # Gris pizarra: mu = 0 (cuadrados prohibidos)
COL_MELLIN = oklch(0.84, 0.17, H0 - 135)    # Oro/ámbar de Partiels (Espejo de Mellin)
COL_RAMA = oklch(0.78, 0.16, H0 + 65)       # Violeta/lila (Sumas de Ramanujan / Siringua)

def cargar_fuente(size, bold=False):
    candidates = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf' if bold else '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        'C:/Windows/Fonts/consolab.ttf' if bold else 'C:/Windows/Fonts/consola.ttf',
    ]
    for c in candidates:
        if os.path.exists(c):
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()

def hz(midi):
    return 440.0 * (2.0 ** ((np.asarray(midi, float) - 69.0) / 12.0))

def paneo(p):
    ang = (np.asarray(p, float) + 1.0) * math.pi / 4.0
    return np.cos(ang), np.sin(ang)

# ───────────── 3. Motor Espectral Exacto (Fórmula cerrada + FFmpeg spectrumsynth) ─────────────
class PistaRejilla:
    def __init__(self, nombre, columnas, S_grid=32768, H_grid=16384):
        self.nombre = nombre
        self.C = columnas
        self.S = S_grid
        self.H = H_grid
        self.N = 2 * H_grid
        self.T = self.N / self.S  # 1.000 s exacto por columna
        self.F = self.S / self.N  # 1.0 Hz exacto por fila
        self.R = 1024
        self.segs = []
        self.grupo = 0

    def seg(self, B, f, a, ts, te, pan):
        if f <= 20 or f >= self.S / 2 - 100:
            return
        gL, gR = paneo(pan)
        if te is None or te == math.inf:
            te = ts + math.log(1e5) / max(a, 1e-3)
        te = min(te, self.C * self.T)
        if te > ts:
            self.segs.append((complex(B), float(f), float(a), float(ts), float(te), float(gL), float(gR), self.grupo))

    def modo(self, f, amp, t0, a, ataque=None, suelta=None, ar=None, pan=0.0, fase=0.0):
        self.grupo += 1
        B = amp * np.exp(1j * fase)
        if ataque and ataque > a:
            tp = math.log(ataque / a) / (ataque - a)
            B /= (math.exp(-a * tp) - math.exp(-ataque * tp))
        fin = t0 + suelta if suelta else None
        self.seg(B, f, a, t0, fin, pan)
        if ataque and ataque > a:
            self.seg(-B, f, ataque, t0, fin, pan)
        if suelta:
            L = suelta
            env = math.exp(-a * L) - (math.exp(-ataque * L) if (ataque and ataque > a) else 0.0)
            B1 = B * env * np.exp(2j * math.pi * f * L)
            self.seg(B1, f, ar or 12.0, t0 + L, None, pan)

    def escribir(self):
        ZL = np.zeros((self.C, self.H), complex)
        ZR = np.zeros((self.C, self.H), complex)
        todas = np.arange(1, self.H)
        ph_todas = -2j * math.pi * todas / self.N
        completa = set()
        for B, f, a, ts, te, gL, gR, g in self.segs:
            ms, me = ts * self.S, te * self.S
            for b in range(max(0, int(ms // self.N)), min(self.C, int(math.ceil(me / self.N)))):
                corte = 0.0
                if ms < b * self.N:
                    corte = abs(B) * math.exp(-a * (b * self.N - ms) / self.S)
                if me > (b + 1) * self.N:
                    corte = max(corte, abs(B) * math.exp(-a * ((b + 1) * self.N - ms) / self.S))
                if corte > 2e-5:
                    completa.add((g, b))
        for B, f, a, ts, te, gL, gR, g in self.segs:
            ms, me = ts * self.S, te * self.S
            kc = f / self.F
            k_v = np.arange(max(1, int(kc) - self.R), min(self.H, int(kc) + self.R + 1))
            if k_v.size == 0:
                continue
            ph_v = -2j * math.pi * k_v / self.N
            for b in range(max(0, int(ms // self.N)), min(self.C, int(math.ceil(me / self.N)))):
                m0 = max(math.ceil(ms), b * self.N)
                m1 = min(math.ceil(me), (b + 1) * self.N)
                M_len = m1 - m0
                if M_len <= 0:
                    continue
                k, ph = (todas, ph_todas) if (g, b) in completa else (k_v, ph_v)
                c = 0
                for Bc, pc in ((B / 2.0, complex(-a, 2.0 * math.pi * f)), (B.conjugate() / 2.0, complex(-a, -2.0 * math.pi * f))):
                    q = pc / self.S + ph
                    pre = Bc * np.exp(pc * (m0 - ms) / self.S) * np.exp(ph * (m0 - b * self.N))
                    c = c + pre * (np.expm1(M_len * q) / np.expm1(q))
                c /= self.N
                ZL[b, k] += gL * c
                ZR[b, k] += gR * c
        return ZL, ZR

    def tiempo(self, t0, t1):
        n = np.arange(int(round(t0 * self.S)), int(round(t1 * self.S)))
        t = n / self.S
        y = np.zeros((len(n), 2))
        for B, f, a, ts, te, gL, gR, _ in self.segs:
            ok = (n >= math.ceil(ts * self.S)) & (n < math.ceil(te * self.S))
            if not ok.any():
                continue
            sig = np.real(B * np.exp(complex(-a, 2.0 * math.pi * f) * (t[ok] - ts)))
            y[ok, 0] += gL * sig
            y[ok, 1] += gR * sig
        return y

def sintetizar_spectrumsynth(ZL, ZR, wav_path, S_grid=32768):
    H_grid = ZL.shape[1]
    W = ZL.shape[0]
    mag = np.empty((2 * H_grid, W))
    pha = np.empty_like(mag)
    mag[:H_grid] = np.abs(ZR).T[::-1]
    mag[H_grid:] = np.abs(ZL).T[::-1]
    pha[:H_grid] = np.angle(ZR).T[::-1]
    pha[H_grid:] = np.angle(ZL).T[::-1]
    escala = float(mag.max()) or 1.0
    m16 = np.round(mag / escala * 65535.0).astype('<u2')
    p16 = np.round((pha + math.pi) / (2.0 * math.pi) * 65535.0).astype('<u2')
    mr = Path(str(wav_path) + '.mag.raw')
    pr = Path(str(wav_path) + '.fase.raw')
    m16.tofile(mr)
    p16.tofile(pr)
    ent = lambda r: ['-f', 'rawvideo', '-pix_fmt', 'gray16le', '-s', f'{W}x{2 * H_grid}', '-r', '1', '-i', str(r)]
    subprocess.run([
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
        *ent(mr), *ent(pr),
        '-filter_complex',
        f'[0]setpts=N/TB,format=gray16le[m];[1]setpts=N/TB,format=gray16le[p];'
        f'[m][p]spectrumsynth=sample_rate={S_grid}:channels=2:scale=lin:slide=fullframe:win_func=rect:overlap=0',
        '-c:a', 'pcm_f32le', str(wav_path)
    ], check=True)
    mr.unlink()
    pr.unlink()
    return escala

# ───────────── 4. Escritura de la Criba de Möbius–Grisey en PistaRejilla ─────────────
def escribir_candelabro_mobius_en_pista(
    P, t0, f_pivote, N_max=12, M_over=6, gamma=1.0, alpha_mu=1.0, q_rama=1,
    retardo_ford=0.0, dur_base=0.48, modo_inverso_chen=False
):
    """Escribe un evento del Candelabro de Möbius-Grisey en la PistaRejilla.

    - Si `modo_inverso_chen=True`: demuestra la inversión exacta de Chen-Möbius sobre un generador
      con sobretonos compuestos. Excita generadores en d * f_pivote (o f_pivote / d) cuyos sobretonos
      k * (d * f_pivote) caen en m * f_pivote con m = d * k. Al pesar cada generador d con mu(d),
      la amplitud en cada múltiplo m * f_pivote es proporcional a sum_{d | m} mu(d) = delta_{m,1}.
    - Si `modo_inverso_chen=False`: construye el acorde espectralista de Grisey deformado por Mellin
      f_n(gamma) = f_pivote * (n ** gamma), pesado por interpolación entre 1 y mu(n) y filtrado por
      la suma de Ramanujan c_q(n).
    """
    phi_q = max(1.0, float(euler_phi(q_rama)))
    for d in range(1, N_max + 1):
        mu_d = mobius_mu(d)
        # Peso interpolado entre serie completa (+1) y criba de Möbius mu(d) in {-1, 0, +1}
        w_mu = (1.0 - alpha_mu) * 1.0 + alpha_mu * float(mu_d)
        if abs(w_mu) < 1e-6:
            continue

        # Factor de Ramanujan c_q(d)
        w_rama = 1.0 if q_rama <= 1 else (ramanujan_cq(q_rama, d) / phi_q)
        w_total_d = w_mu * (0.35 + 0.65 * abs(w_rama))
        signo_total = 1.0 if (w_mu * (1.0 if w_rama >= 0 else -1.0)) >= 0 else -1.0
        fase_d = -math.pi / 2.0 if signo_total > 0 else (+math.pi / 2.0)

        # Retardo de ataque gobernado por el radio del círculo de Ford 1/(2 d^2)
        dt_ford = retardo_ford * (1.0 - 1.0 / (d ** 2))
        t_onset = t0 + dt_ford

        if modo_inverso_chen:
            # Cada generador d emite su propia serie de sobretonos k = 1..M_over
            # En el múltiplo compuesto m = d * k, todas las parejas (d, k) comparten la misma
            # caída modal a_m y ataque at_m para que la identidad de Dirichlet sum_{d|m} mu(d) = delta_{m,1}
            # actúe limpiamente en cada fila m * f_pivote.
            for k in range(1, M_over + 1):
                m_comp = d * k
                if m_comp > N_max:
                    continue
                f_mk = f_pivote * (m_comp ** gamma)
                amp_mk = (0.14 / (m_comp ** 0.85)) * abs(w_mu)
                a_m = 3.2 + 0.35 * m_comp
                P.modo(
                    f_mk, amp_mk, t_onset, a_m,
                    ataque=110.0, suelta=dur_base, ar=28.0,
                    pan=0.0, fase=fase_d
                )
        else:
            # Modo Candelabro de Grisey (Mellin gamma in [-1, +1] + Criba square-free + Ramanujan)
            f_d = f_pivote * (d ** gamma)
            jacobiano_mellin = math.sqrt(max(0.25, abs(gamma))) if abs(gamma) > 0.08 else 0.5
            amp_d = (0.13 / (d ** 0.72)) * abs(w_total_d) * jacobiano_mellin
            # Paneo simétrico por paridad de Möbius (centro en d=1)
            pan_d = 0.0 if d == 1 else (0.38 * mu_d * math.sin(d * 0.7))
            a_d = 2.6 + 0.28 * d
            at_d = 35.0 + 18.0 * d  # En Partiels, los parciales altos entran con más filo
            P.modo(
                f_d, amp_d, t_onset, a_d,
                ataque=at_d, suelta=dur_base, ar=24.0,
                pan=pan_d, fase=fase_d
            )


# ───────────── 5. Sonda de Verificación (`ejecutar_sonda()`) ─────────────
def ejecutar_sonda():
    resultados = {}

    # 1. Prueba de Inversión de Chen–Möbius / Aniquilación de Dirichlet sum_{d|m} mu(d) = delta_{m,1}
    # Comparamos en f_pivote = 110 Hz (La2):
    # - Columna 0: Coro crudo (alpha_mu = 0.0, todos los divisores d suman en fase +1 -> los múltiplos compuestos m=2..8 se acumulan con fuerza d(m), el número de divisores).
    # - Columna 2: Coro con Inversión de Chen–Möbius y ataques sincrónicos (alpha_mu = 1.0, retardo_ford = 0.0 -> sum_{d|m} mu(d) = 0 aniquila todos los compuestos m >= 2).
    # - Columna 4: Coro con Inversión de Chen–Möbius pero con ataques escalonados de Ford (retardo_ford = 0.14 s -> la sonda descubre que el desfase de entrada deja una "chispa aritmética transitoria" en los compuestos!).
    P_chen = PistaRejilla('sonda_chen_mobius', columnas=6, S_grid=32768, H_grid=16384)
    f_piv = 110.0
    escribir_candelabro_mobius_en_pista(P_chen, 0.20, f_piv, N_max=8, M_over=8, gamma=1.0, alpha_mu=0.0, retardo_ford=0.0, dur_base=0.55, modo_inverso_chen=True)
    escribir_candelabro_mobius_en_pista(P_chen, 2.20, f_piv, N_max=8, M_over=8, gamma=1.0, alpha_mu=1.0, retardo_ford=0.0, dur_base=0.55, modo_inverso_chen=True)
    escribir_candelabro_mobius_en_pista(P_chen, 4.20, f_piv, N_max=8, M_over=8, gamma=1.0, alpha_mu=1.0, retardo_ford=0.14, dur_base=0.55, modo_inverso_chen=True)

    ZL_chen, ZR_chen = P_chen.escribir()
    wav_chen = INTER_DIR / 'sonda_chen_spectrumsynth.wav'
    esc_chen = sintetizar_spectrumsynth(ZL_chen, ZR_chen, wav_chen, S_grid=32768)
    _, y_ff = wavfile.read(wav_chen)
    y_ff = y_ff.astype(np.float64) * esc_chen
    y_ti = P_chen.tiempo(0.0, 6.0)
    diff_chen = y_ff - y_ti
    snr_chen_db = 10.0 * math.log10(np.sum(y_ti ** 2) / (np.sum(diff_chen ** 2) + 1e-24))

    def energia_banda(Z_col, f_center, half_w=4):
        k0 = max(1, int(round(f_center)) - half_w)
        k1 = min(len(Z_col), int(round(f_center)) + half_w + 1)
        return float(np.sum(np.abs(Z_col[k0:k1]) ** 2))

    # Energías en m = 1 (110 Hz, fundamental despejada) vs m = 2..6 (compuestos 220, 330, 440, 550, 660 Hz)
    e_m1_crudo = energia_banda(ZL_chen[0], 110.0)
    e_m1_mobius = energia_banda(ZL_chen[2], 110.0)
    e_comp_crudo = sum(energia_banda(ZL_chen[0], 110.0 * m) for m in range(2, 7))
    e_comp_mobius_sync = sum(energia_banda(ZL_chen[2], 110.0 * m) for m in range(2, 7))
    e_comp_mobius_ford = sum(energia_banda(ZL_chen[4], 110.0 * m) for m in range(2, 7))

    supresion_comp_sync_db = 10.0 * math.log10((e_comp_mobius_sync + 1e-24) / (e_comp_crudo + 1e-24))
    supresion_comp_ford_db = 10.0 * math.log10((e_comp_mobius_ford + 1e-24) / (e_comp_crudo + 1e-24))
    conservacion_m1_db = 10.0 * math.log10((e_m1_mobius + 1e-24) / (e_m1_crudo + 1e-24))

    resultados['prueba_1_inversion_chen_dirichlet'] = {
        'conservacion_fundamental_m1_dB': round(conservacion_m1_db, 2),
        'supresion_sobretonos_compuestos_sincrona_dB': round(supresion_comp_sync_db, 2),
        'supresion_sobretonos_con_desfase_ford_dB': round(supresion_comp_ford_db, 2),
        'SNR_spectrumsynth_dB': round(snr_chen_db, 2)
    }

    # 2. Prueba de Huecos Square-Free (mu(4) = mu(8) = mu(9) = mu(12) = 0) y Espejo de Mellin (gamma = +1 vs -1)
    # Usamos f_pivote = 330 Hz (Mi4) para que tanto armónicos (hasta 12*330 = 3960 Hz) como subarmónicos (330/12 = 27.5 Hz) queden bien resueltos.
    P_mellin = PistaRejilla('sonda_mellin_squarefree', columnas=6, S_grid=32768, H_grid=16384)
    f_piv_m = 330.0
    # Col 0: Serie ordinaria (alpha_mu = 0.0, gamma = +1.0) -> cuadrados 4, 8, 9, 12 presentes
    escribir_candelabro_mobius_en_pista(P_mellin, 0.20, f_piv_m, N_max=12, gamma=+1.0, alpha_mu=0.0, q_rama=1, dur_base=0.52)
    # Col 2: Criba de Möbius (alpha_mu = 1.0, gamma = +1.0) -> cuadrados 4, 8, 9, 12 apagados (mu = 0)
    escribir_candelabro_mobius_en_pista(P_mellin, 2.20, f_piv_m, N_max=12, gamma=+1.0, alpha_mu=1.0, q_rama=1, dur_base=0.52)
    # Col 4: Espejo Subarmónico de Mellin (alpha_mu = 1.0, gamma = -1.0) -> inversión hacia el grave 330 / d
    escribir_candelabro_mobius_en_pista(P_mellin, 4.20, f_piv_m, N_max=12, gamma=-1.0, alpha_mu=1.0, q_rama=1, dur_base=0.52)

    ZL_mel, _ = P_mellin.escribir()
    cuadrados = [4, 8, 9, 12]
    e_sq_ordinaria = sum(energia_banda(ZL_mel[0], f_piv_m * sq, half_w=3) for sq in cuadrados)
    e_sq_mobius = sum(energia_banda(ZL_mel[2], f_piv_m * sq, half_w=3) for sq in cuadrados)
    caida_squarefree_db = 10.0 * math.log10((e_sq_mobius + 1e-24) / (e_sq_ordinaria + 1e-24))

    freqs = np.arange(16384, dtype=float)
    cent_arm = float(np.sum(freqs * (np.abs(ZL_mel[2]) ** 2)) / (np.sum(np.abs(ZL_mel[2]) ** 2) + 1e-24))
    cent_sub = float(np.sum(freqs * (np.abs(ZL_mel[4]) ** 2)) / (np.sum(np.abs(ZL_mel[4]) ** 2) + 1e-24))

    # Comprobación de reciprocidad logarítmica respecto al pivote (330 Hz):
    # En gamma = +1, log2(cent_arm / 330) > 0; en gamma = -1, log2(cent_sub / 330) < 0
    oct_arriba = math.log2(cent_arm / f_piv_m)
    oct_abajo = math.log2(cent_sub / f_piv_m)

    resultados['prueba_2_squarefree_y_mellin'] = {
        'caida_cuadrados_4_8_9_12_dB': round(caida_squarefree_db, 2),
        'centroide_armonico_gamma_pos1_Hz': round(cent_arm, 1),
        'centroide_subarmonico_gamma_neg1_Hz': round(cent_sub, 1),
        'desplazamiento_octavas_arriba_pivote': round(oct_arriba, 3),
        'desplazamiento_octavas_abajo_pivote': round(oct_abajo, 3)
    }

    # 3. Prueba de Selectividad del Resonador de Ramanujan c_q(n) en q = 7 vs q = 1
    P_rama = PistaRejilla('sonda_ramanujan', columnas=4, S_grid=32768, H_grid=16384)
    escribir_candelabro_mobius_en_pista(P_rama, 0.20, 165.0, N_max=14, gamma=1.0, alpha_mu=1.0, q_rama=1, dur_base=0.50)
    escribir_candelabro_mobius_en_pista(P_rama, 2.20, 165.0, N_max=14, gamma=1.0, alpha_mu=1.0, q_rama=7, dur_base=0.50)
    ZL_r, _ = P_rama.escribir()
    # Razón de energía del 7º armónico (7 * 165 = 1155 Hz) respecto a los no múltiplos (2, 3, 5)
    rel_7_q1 = energia_banda(ZL_r[0], 165.0 * 7) / ( sum(energia_banda(ZL_r[0], 165.0 * k) for k in (2, 3, 5)) + 1e-24 )
    rel_7_q7 = energia_banda(ZL_r[2], 165.0 * 7) / ( sum(energia_banda(ZL_r[2], 165.0 * k) for k in (2, 3, 5)) + 1e-24 )
    realce_rama_7_db = 10.0 * math.log10((rel_7_q7 + 1e-24) / (rel_7_q1 + 1e-24))
    resultados['prueba_3_resonador_ramanujan'] = {
        'realce_relativo_7o_armonico_en_q7_dB': round(realce_rama_7_db, 2)
    }

    return resultados


# ───────────── 6. Motor Temporal de 24 s (Muestra Aislada: El Candelabro de Möbius–Grisey) ─────────────
def render_candelabro_temporal(partitura, duracion=24.0, sr=SR, semilla=SEMILLA):
    n_total = int(round(duracion * sr))
    t = np.arange(n_total) / sr
    out = np.zeros((n_total, 2), dtype=np.float64)
    rng = np.random.default_rng(semilla)

    def interp_ctrl(key, default):
        pts = np.asarray(partitura.get(key, [[0.0, default], [duracion, default]]), dtype=float)
        return np.interp(t, pts[:, 0], pts[:, 1])

    gamma_curve = interp_ctrl('espejo_mellin_gamma', 1.0)
    alpha_mu_curve = interp_ctrl('criba_mobius_alpha', 1.0)
    q_rama_curve = interp_ctrl('modulo_ramanujan_q', 1.0)
    beta_diff_curve = interp_ctrl('sombra_diferencial_beta', 0.4)

    divisores = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    eventos = partitura.get('eventos', [])
    trazas_nodos = []

    for ev_i, ev in enumerate(eventos):
        t0 = float(ev['t0'])
        dur_ev = float(ev.get('dur', 3.4))
        f_piv = float(ev['f_pivote'])
        vel = float(ev.get('vel', 0.88))
        modo_chen = bool(ev.get('modo_chen', False))
        # fiel (arreglo del 21 oct 2026, ver README): que el motor que suena cumpla lo que la sonda mide.
        #   · modo Chen: las parejas (d, k) que caen en el mismo m = d·k comparten amplitud, decaimiento (contado
        #     desde t0, no desde su entrada) y fase absoluta → con γ = 1, Σ_{d|m} μ(d) = 0 cancela de verdad en
        #     el sostén; el retardo de Ford sólo deja la chispa del ataque.
        #   · modo Candelabro: los armónicos internos h de cada parcial d respetan la criba (μ(d·h) = 0 → callan),
        #     para que los huecos 4, 8, 9, 12 sean huecos.
        # fiel = False reproduce la versión original bit a bit.
        fiel = bool(ev.get('fiel', partitura.get('fiel', True)))

        idx_c = min(n_total - 1, max(0, int(round((t0 + 0.3) * sr))))
        gamma_ev = float(ev.get('gamma', gamma_curve[idx_c]))
        alpha_mu = float(ev.get('alpha_mu', alpha_mu_curve[idx_c]))
        q_rama = int(round(float(ev.get('q_rama', q_rama_curve[idx_c]))))
        beta_diff = float(ev.get('beta_diff', beta_diff_curve[idx_c]))
        retardo_ford = float(ev.get('retardo_ford', 0.32))

        phi_q = max(1.0, float(euler_phi(max(1, q_rama))))
        frecuencias_activas = []

        for d in divisores:
            mu_d = mobius_mu(d)
            w_mu = (1.0 - alpha_mu) * 1.0 + alpha_mu * float(mu_d)
            if abs(w_mu) < 1e-4:
                continue

            w_rama = 1.0 if q_rama <= 1 else (ramanujan_cq(q_rama, d) / phi_q)
            signo = 1.0 if (w_mu * (1.0 if w_rama >= 0 else -1.0)) >= 0 else -1.0
            fase_0 = -math.pi / 2.0 if signo > 0 else (+math.pi / 2.0)

            dt_f = retardo_ford * (1.0 - 1.0 / (d ** 2))
            t_in = t0 + dt_f
            i0 = max(0, int(round(t_in * sr)))
            i1 = min(n_total, int(round((t_in + dur_ev) * sr)))
            if i1 <= i0:
                continue

            u = (np.arange(i0, i1) / sr) - t_in
            # Envolvente espectralista: los parciales de radio de Ford grande (d pequeño) abren majestuosos;
            # los primos lejanos entran más incisivos.
            a_decay = 1.15 + 0.16 * d
            at_rate = 14.0 + 9.5 * d
            tp = math.log(at_rate / a_decay) / (at_rate - a_decay)
            env = (np.exp(-a_decay * u) - np.exp(-at_rate * u)) / (math.exp(-a_decay * tp) - math.exp(-at_rate * tp))

            # Curva local de Mellin gamma(t) durante la nota
            g_loc = gamma_curve[i0:i1] if 'gamma' not in ev else np.full_like(u, gamma_ev)
            f_inst = np.clip(f_piv * (float(d) ** g_loc), 28.0, sr * 0.44)
            f_media = float(np.mean(f_inst))
            frecuencias_activas.append((d, mu_d, f_media, abs(w_mu)))

            trazas_nodos.append({
                'evento': ev_i, 'divisor': d, 'mu': mu_d,
                't_in': round(t_in, 3), 'f_media_Hz': round(f_media, 2),
                'gamma': round(float(np.mean(g_loc)), 3), 'q_rama': q_rama
            })

            pan_d = 0.0 if d == 1 else float(np.clip(0.48 * (mu_d if mu_d != 0 else 0.5) * math.sin(d * 0.85), -0.88, 0.88))
            gL, gR = paneo(pan_d)

            if modo_chen and fiel:
                t_fin = t0 + retardo_ford + dur_ev                                 # todos terminan juntos, con un fundido común
                i1 = min(n_total, int(round(t_fin * sr)))
                t_abs = np.arange(i0, i1) / sr; u = t_abs - t_in
                gate = np.sin(np.minimum(1.0, u / 0.012) * math.pi / 2.0) ** 2      # la entrada de Ford sólo abre
                gate = gate * np.sin(np.clip((t_fin - t_abs) / 0.15, 0.0, 1.0) * math.pi / 2.0) ** 2
                M_MAX = 15                                                         # cada d llega hasta m ≤ 15: Σ_{d|m} μ(d) completa
                for k in range(1, M_MAX // d + 1):
                    m = d * k
                    w_r = 1.0 if q_rama <= 1 else ramanujan_cq(q_rama, m) / phi_q  # Ramanujan por m, no por d
                    amp_m = (0.075 * vel / (m ** 0.68)) * (0.4 + 0.6 * abs(w_r))
                    if 'gamma' in ev:
                        ph = 2.0 * math.pi * f_piv * (float(d) ** gamma_ev) * k * t_abs - math.pi / 2.0   # fase absoluta
                    else:
                        ph = 2.0 * math.pi * np.cumsum(np.clip(f_inst * k, 28.0, sr * 0.44)) / sr - math.pi / 2.0
                    s_m = w_mu * amp_m * gate * np.cos(ph) * np.exp(-(1.15 + 0.16 * m) * (t_abs - t0))
                    gLm, gRm = paneo(0.0 if m == 1 else float(np.clip(0.48 * math.sin(m * 0.85), -0.88, 0.88)))   # paneo por m
                    out[i0:i1, 0] += gLm * s_m
                    out[i0:i1, 1] += gRm * s_m
            elif modo_chen:
                # Cada subarmónico/armónico dispara sobretonos k=1..5 pero pesados por mu(d) para auto-cancelar compuestos
                sig_d = np.zeros_like(u)
                for k in range(1, 6):
                    f_k = np.clip(f_inst * k, 28.0, sr * 0.44)
                    ph_k = 2.0 * math.pi * np.cumsum(f_k) / sr + fase_0
                    sig_d += (np.cos(ph_k) / (k ** 1.15))
                amp_d = (0.075 * vel / (d ** 0.68)) * abs(w_mu) * (0.4 + 0.6 * abs(w_rama))
                out[i0:i1, 0] += gL * amp_d * env * sig_d
                out[i0:i1, 1] += gR * amp_d * env * sig_d
            else:
                # Modo Candelabro de Grisey con armónicos internos square-free (1, 2, 3, 5)
                ph_base = 2.0 * math.pi * np.cumsum(f_inst) / sr
                cr = (lambda h: (1.0 - alpha_mu) + alpha_mu * abs(mobius_mu(d * h))) if fiel else (lambda h: 1.0)
                sig_d = (
                    1.00 * np.cos(ph_base + fase_0) +
                    0.28 * cr(2) * np.cos(2.0 * ph_base + fase_0) +
                    0.14 * cr(3) * np.cos(3.0 * ph_base - fase_0)
                )
                jac = np.sqrt(np.maximum(0.28, np.abs(g_loc)))
                amp_d = (0.088 * vel / (d ** 0.68)) * abs(w_mu) * (0.38 + 0.62 * abs(w_rama))
                out[i0:i1, 0] += gL * amp_d * jac * env * sig_d
                out[i0:i1, 1] += gR * amp_d * jac * env * sig_d

        # Tonos diferenciales de Grisey (|f_a - f_b| ponderados por mu(a)*mu(b) y rugosidad de compresión)
        if beta_diff > 0.05 and len(frecuencias_activas) >= 3:
            i0 = max(0, int(round((t0 + 0.15) * sr)))
            i1 = min(n_total, int(round((t0 + dur_ev) * sr)))
            if i1 > i0:
                u = (np.arange(i0, i1) / sr) - (t0 + 0.15)
                env_diff = np.sin(np.minimum(1.0, u / 0.18) * math.pi / 2.0) ** 2 * np.exp(-1.1 * u)
                sig_sub = np.zeros_like(u)
                # Pares de primos consecutivos (2,3), (3,5), (5,7), (7,11)
                for (d1, mu1, f1, w1), (d2, mu2, f2, w2) in zip(frecuencias_activas[:-1], frecuencias_activas[1:]):
                    f_diff = abs(f2 - f1)
                    if 28.0 <= f_diff <= 135.0:
                        fase_diff = 0.0 if (mu1 * mu2 >= 0) else math.pi
                        sig_sub += 0.032 * beta_diff * vel * np.sin(2.0 * math.pi * f_diff * u + fase_diff)
                # Sombra anclada al Mi0 de Partiels (41.20 Hz) y su octava Mi1 (82.41 Hz)
                f_mi0 = 41.2034
                sig_sub += 0.038 * beta_diff * vel * (np.sin(2.0 * math.pi * f_mi0 * u) + 0.55 * np.sin(2.0 * math.pi * (2.0 * f_mi0) * u))
                out[i0:i1, 0] += sig_sub * env_diff * 0.71
                out[i0:i1, 1] += sig_sub * env_diff * 0.71

    # Reverberación corta tipo sala espectral IRCAM (retardos primos relativos en muestras)
    for ch, delay_s, g_rev in ((0, 0.029, 0.14), (1, 0.037, 0.14), (0, 0.061, 0.08), (1, 0.073, 0.08)):
        nd = int(round(delay_s * sr))
        if nd < n_total:
            out[nd:, ch] += g_rev * out[:-nd, 1 - ch]

    trazas = {
        'gamma_mellin': gamma_curve,
        'alpha_mobius': alpha_mu_curve,
        'q_ramanujan': q_rama_curve,
        'beta_diferencial': beta_diff_curve,
    }
    return out, trazas, {'nodos_disparados': len(trazas_nodos)}


# ───────────── 7. Escena en Contexto (24 s): Candelabro + Trombón Mi0 (Partiels) + Siringua en Huecos Square-Free ─────────────
VOCALES = {
    'a': [730, 1090, 2440, 3400],
    'e': [500, 1800, 2600, 3500],
    'i': [290, 2300, 3000, 3600],
    'o': [470, 850, 2500, 3400],
    'u': [350, 700, 2400, 3300]
}

def formantes_boca(x, formants_curves, sr):
    out = np.zeros(len(x))
    B = max(32, round(sr * 0.004))
    z = [np.zeros(2) for _ in range(4)]
    for i in range(0, len(x), B):
        j = min(len(x), i + B)
        mid = (i + j - 1) // 2
        for k, weight in enumerate([1.0, 0.62, 0.27, 0.10]):
            f = float(formants_curves[k][mid])
            bw = [85, 110, 170, 240][k]
            b, a = iirpeak(min(f, sr * 0.42), max(1.0, f / bw), fs=sr)
            v, z[k] = lfilter(b, a, x[i:j], zi=z[k])
            out[i:j] += weight * v
    return out

def render_escena_grisey_costura(duracion=24.0, sr=SR, semilla=SEMILLA):
    """Escena de 24 s donde:
    - El Candelabro de Möbius-Grisey respira sobre el pivote Mi2/Mi3 (f0 = 82.41 Hz / 164.81 Hz).
    - Como mu(4) = mu(8) = mu(9) = mu(12) = 0, las frecuencias 4*f0 (329.6 Hz, Mi4), 8*f0 (659.3 Hz, Mi5),
      9*f0 (741.7 Hz, Fa#5) y 12*f0 (988.9 Hz, Si5) están completamente vacías en la armonía.
    - La Siringua / Voz formántica canta su melodía EXACTAMENTE sobre esos nodos square-free (4f0, 8f0, 9f0, 12f0),
      demostrando la Costura aritmética por teoría de números.
    - Abajo, el Trombón Fantasma de Mi0 (41.20 Hz) de *Partiels* abre cada ola espectral con presión de latón y subgrave.
    """
    n_total = int(round(duracion * sr))
    t = np.arange(n_total) / sr
    rng = np.random.default_rng(semilla + 19)

    f0_piv = 82.4069  # Mi2 (el doble exacto del Mi0 = 41.2034 Hz de Partiels)

    part_cand = {
        'espejo_mellin_gamma': [[0.0, 1.0], [6.0, 1.0], [11.5, 0.28], [13.0, -1.0], [18.5, -1.0], [21.0, 1.0], [24.0, 1.0]],
        'criba_mobius_alpha': [[0.0, 0.0], [3.5, 1.0], [24.0, 1.0]],
        'modulo_ramanujan_q': [[0.0, 1], [6.0, 6], [12.0, 7], [18.0, 11], [21.0, 6], [24.0, 6]],
        'sombra_diferencial_beta': [[0.0, 0.25], [8.0, 0.85], [16.0, 0.90], [24.0, 0.45]],
        'eventos': [
            {'t0': 0.2, 'dur': 4.2, 'f_pivote': f0_piv, 'gamma': 1.0, 'alpha_mu': 0.0, 'q_rama': 1, 'vel': 0.84},
            {'t0': 4.2, 'dur': 4.4, 'f_pivote': f0_piv, 'gamma': 1.0, 'alpha_mu': 1.0, 'q_rama': 6, 'vel': 0.90},
            {'t0': 8.4, 'dur': 4.2, 'f_pivote': f0_piv * 2.0, 'gamma': 0.35, 'alpha_mu': 1.0, 'q_rama': 7, 'vel': 0.88},
            {'t0': 12.4, 'dur': 5.6, 'f_pivote': f0_piv * 4.0, 'gamma': -1.0, 'alpha_mu': 1.0, 'q_rama': 7, 'vel': 0.92, 'modo_chen': True},
            {'t0': 18.2, 'dur': 5.4, 'f_pivote': f0_piv, 'gamma': 1.0, 'alpha_mu': 1.0, 'q_rama': 6, 'vel': 0.92, 'modo_chen': True},
        ]
    }
    y_cand, tr_cand, _ = render_candelabro_temporal(part_cand, duracion, sr, semilla)

    # 2. Trombón Fantasma de Mi0 (41.2034 Hz, homenaje directo al arranque de Partiels de Grisey)
    y_trombon = np.zeros((n_total, 2), dtype=np.float64)
    env_trombon = np.zeros(n_total, dtype=np.float64)
    golpes_mi0 = [
        (0.15, 3.6, 41.2034, 0.88, 0.25),   # Ola I: Mi0 profundo
        (4.15, 3.8, 41.2034, 0.92, 0.75),   # Ola II: Mi0 con crescendo brassy + raspado sul ponticello
        (8.35, 3.6, 41.2034 * 1.5, 0.85, 0.85),  # Ola III: Si0
        (12.35, 5.2, 41.2034, 0.94, 0.55),  # Ola IV: Mi0 sosteniendo el abismo subarmónico
        (18.15, 5.2, 41.2034, 0.90, 0.40),  # Ola V: Cierre en Mi0
    ]
    for t_g, dur_g, f_g, vel_g, brass_g in golpes_mi0:
        i0 = int(round(t_g * sr))
        i1 = min(n_total, int(round((t_g + dur_g) * sr)))
        if i1 <= i0:
            continue
        u = (np.arange(i0, i1) / sr) - t_g
        # Envolvente de ola de Grisey: ataque lento que se hincha hacia el final y corta con rasgueo
        swell = (np.sin(np.minimum(1.0, u / (dur_g * 0.62)) * math.pi / 2.0) ** 1.6) * np.exp(-2.8 * np.maximum(0.0, u - dur_g * 0.62))
        ph_t = 2.0 * math.pi * f_g * u
        # Síntesis no lineal de latón grave (parciales impares y pares con saturación progresiva)
        indice_fm = (0.8 + 2.4 * brass_g * swell)
        sig_laton = np.sin(ph_t + indice_fm * np.sin(ph_t)) + 0.45 * np.sin(2.0 * ph_t + 0.7 * indice_fm * np.sin(2.0 * ph_t))
        # Grano de arco sul ponticello al final de la ola (como el contrabajo en Partiels)
        crest_mask = np.exp(-((u - dur_g * 0.65) ** 2) / 0.08)
        ruido_arco = sosfilt(butter(2, [600, 3800], fs=sr, btype='bandpass', output='sos'), rng.normal(0, 1, len(u)))
        sig_tot = (0.19 * vel_g * sig_laton * swell) + (0.035 * brass_g * ruido_arco * crest_mask)
        y_trombon[i0:i1, 0] += sig_tot * 0.72
        y_trombon[i0:i1, 1] += sig_tot * 0.72
        env_trombon[i0:i1] += swell

    # 3. Siringua / Voz formántica cantando EXCLUSIVAMENTE en los huecos square-free donde mu(n) = 0:
    # n = 4 (4 * 82.41 = 329.63 Hz, Mi4)
    # n = 8 (8 * 82.41 = 659.26 Hz, Mi5)
    # n = 9 (9 * 82.41 = 741.66 Hz, Fa#5 natural)
    # n = 12 (12 * 82.41 = 988.88 Hz, Si5)
    # y sus espejos subarmónicos cuando gamma = -1!
    notas_hueco = [
        {'t': 4.4, 'dur': 1.8, 'mult_sq': 4.0, 'vel': 0.85},   # 4 * f0 = 329.63 Hz (mu(4)=0)
        {'t': 6.3, 'dur': 1.9, 'mult_sq': 8.0, 'vel': 0.82},   # 8 * f0 = 659.26 Hz (mu(8)=0)
        {'t': 8.6, 'dur': 1.7, 'mult_sq': 9.0, 'vel': 0.86},   # 9 * f0 = 741.66 Hz (mu(9)=0)
        {'t': 10.4, 'dur': 1.6, 'mult_sq': 4.0, 'vel': 0.84},  # 4 * f0 = 329.63 Hz
        {'t': 12.8, 'dur': 2.2, 'mult_sq': 4.0, 'vel': 0.90},  # En el abismo subarmónico, canta en el túnel 4*f0
        {'t': 15.1, 'dur': 2.5, 'mult_sq': 9.0 / 2.0, 'vel': 0.88},
        {'t': 18.5, 'dur': 2.1, 'mult_sq': 8.0, 'vel': 0.86},  # 8 * f0 (mu(8)=0)
        {'t': 20.7, 'dur': 2.7, 'mult_sq': 4.0, 'vel': 0.92},  # Cierre en el túnel 4 * f0 = Mi4
    ]
    f0_voz = np.full(n_total, f0_piv * 4.0)
    amp_voz = np.zeros(n_total)
    for nh in notas_hueco:
        i0 = int(round(nh['t'] * sr))
        nn = min(int(round(nh['dur'] * sr)), n_total - i0)
        if i0 >= 0 and nn > 0:
            f0_voz[i0:] = f0_piv * float(nh['mult_sq'])
            tt = np.arange(nn) / sr
            env_v = (np.sin(np.minimum(1.0, tt / 0.05) * math.pi / 2.0) ** 2) * (np.sin(np.minimum(1.0, (nn / sr - tt) / 0.14) * math.pi / 2.0) ** 2)
            amp_voz[i0:i0 + nn] = nh['vel'] * env_v

    a_lp = math.exp(-1.0 / (sr * 0.015))
    f0_v_smooth, _ = lfilter([1.0 - a_lp], [1.0, -a_lp], np.log(f0_voz), zi=[math.log(f0_voz[0]) * a_lp])
    f0_v_final = np.exp(f0_v_smooth) * (2.0 ** ((4.5 * np.sin(2.0 * math.pi * 5.1 * t)) / 1200.0))

    # Subarmónico de Siringua (f0 / 2) acoplado suavemente + formantes vocales
    ph_v = 2.0 * math.pi * np.cumsum(f0_v_final) / sr
    exc_v = (0.72 * np.sin(ph_v) + 0.28 * np.sin(0.5 * ph_v) + 0.18 * np.sin(2.0 * ph_v)) * amp_voz
    t_voc = np.array([0.0, 5.0, 10.0, 15.0, 20.0, 24.0])
    seq_voc = ['o', 'a', 'i', 'u', 'e', 'a']
    vf = np.array([VOCALES[v] for v in seq_voc], dtype=float)
    form_curves = np.array([np.interp(t, t_voc, vf[:, k]) for k in range(4)])
    voz_filtrada = formantes_boca(exc_v, form_curves, sr) * 2.4
    y_siringua = np.column_stack([voz_filtrada * 0.72, voz_filtrada * 0.72])

    mix = y_cand * 0.90 + y_trombon * 0.82 + y_siringua * 0.92
    trazas_esc = {
        'gamma_mellin': tr_cand['gamma_mellin'],
        'alpha_mobius': tr_cand['alpha_mobius'],
        'q_ramanujan': tr_cand['q_ramanujan'],
        'env_trombon_mi0': env_trombon,
        'f0_siringua_squarefree': f0_v_final * (amp_voz > 0.04),
    }
    return mix, {'candelabro': y_cand, 'trombon_mi0': y_trombon, 'siringua_huecos': y_siringua}, trazas_esc


# ───────────── 8. Medición LUFS y Generación de Láminas PNG + GIF ─────────────
def activo_rms(y):
    z = y[:len(y) // 320 * 320].reshape(-1, 320, 2)
    r = np.sqrt(np.mean(z * z, axis=(1, 2)))
    mask = r > max(1e-7, float(r.max()) * 0.045)
    return float(np.sqrt(np.mean(r[mask] ** 2))) if mask.any() else 0.0

def normalizar_nivel(y, target=0.14):
    act = activo_rms(y)
    pk = float(np.abs(y).max())
    gain = min(target / (act + 1e-12), 0.88 / (pk + 1e-12))
    return (y * gain).astype(np.float32)

def guardar_audio_y_medir(y, wav_path, m4a_path, target_lufs=-18.0):
    y = normalizar_nivel(y)
    wavfile.write(str(wav_path), SR, y)
    subprocess.run([
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
        '-i', str(wav_path),
        '-af', f'loudnorm=I={target_lufs}:TP=-1.8:LRA=9',
        '-ar', '48000', '-c:a', 'aac', '-b:a', '224k', str(m4a_path)
    ], check=True)
    r = subprocess.run([
        'ffmpeg', '-hide_banner', '-nostats', '-i', str(m4a_path),
        '-af', 'ebur128=peak=true', '-f', 'null', '-'
    ], capture_output=True, text=True).stderr
    tail = r[r.rfind('Summary:'):]
    val = lambda key: float(tail.split(key)[1].split()[0])
    return {
        'wav': wav_path.name,
        'm4a': m4a_path.name,
        'duracion_s': round(len(y) / SR, 2),
        'I_LUFS': val('I:'),
        'LRA': val('LRA:'),
        'pico_dBTP': val('Peak:'),
        'rms_activo_previo': round(activo_rms(y), 4),
        'sha256_wav': hashlib.sha256(wav_path.read_bytes()).hexdigest()[:16],
        'sha256_m4a': hashlib.sha256(m4a_path.read_bytes()).hexdigest()[:16]
    }

def espectrograma_imagen(y, sr, w, h):
    vals = []
    for c in range(2):
        f, t, z = stft(y[:, c], sr, nperseg=2048, noverlap=1536, boundary=None, padded=False)
        vals.append(np.abs(z) ** 2 * 4.0)
    power = 0.5 * (vals[0] + vals[1])
    db = 10.0 * np.log10(power + 1e-14)
    freqs = np.geomspace(35.0, 10500.0, h)[::-1]
    rows = np.array([np.interp(freqs, f, db[:, j]) for j in range(db.shape[1])]).T
    v = np.clip((rows + 82.0) / 66.0, 0.0, 1.0)
    c_low = np.array(BG, dtype=float)
    c_mid = np.array(COL_MU_NEG, dtype=float)
    c_hi = np.array(COL_MU_POS, dtype=float)
    mask_lo = v < 0.55
    t_lo = (v / 0.55)[..., None]
    t_hi = ((v - 0.55) / 0.45)[..., None]
    rgb_f = np.where(mask_lo[..., None], c_low + t_lo * (c_mid - c_low), c_mid + t_hi * (c_hi - c_mid))
    rgb = np.clip(rgb_f, 0, 255).astype(np.uint8)
    return Image.fromarray(rgb).resize((w, h), Image.Resampling.BILINEAR)

def dibujar_curva(dr, vals, box, color, lo=None, hi=None, width=2):
    x, y, w, h = box
    vals = np.asarray(vals, dtype=float)
    lo = float(vals.min()) if lo is None else float(lo)
    hi = float(vals.max()) if hi is None else float(hi)
    idx = np.linspace(0, len(vals) - 1, min(len(vals), int(w))).astype(int)
    span = max(1e-9, hi - lo)
    pts = [(x + j * w / max(1, len(idx) - 1), y + h - h * np.clip((vals[i] - lo) / span, 0.0, 1.0)) for j, i in enumerate(idx)]
    if len(pts) > 1:
        dr.line(pts, fill=color, width=width)

def crear_lamina_01_dirichlet_y_sonda(sonda_res, path_png):
    W, H = 1600, 960
    im = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(im)
    f_title = cargar_fuente(25, bold=True)
    f_sub = cargar_fuente(14)
    f_sec = cargar_fuente(16, bold=True)
    f_txt = cargar_fuente(13)
    f_sm = cargar_fuente(11)

    p1 = sonda_res['prueba_1_inversion_chen_dirichlet']
    p2 = sonda_res['prueba_2_squarefree_y_mellin']
    p3 = sonda_res['prueba_3_resonador_ramanujan']

    dr.text((48, 24), '01 · LA CRIBA DE MÖBIUS–GRISEY (μ * Ms) · INVERSIÓN DE DIRICHLET Y SONDA', font=f_title, fill=FG)
    dr.text((48, 60), f'Semilla {SEMILLA} · Prueba exacta en spectrumsynth (SNR {p1["SNR_spectrumsynth_dB"]} dB) · Cancelación de sobretonos compuestos sum_{{d|m}} μ(d) = δ_{{m,1}}', font=f_sub, fill=MUTED)

    # Panel izquierdo: Mapa aritmético de los primeros 16 divisores d y sus círculos de Ford
    dr.rectangle((48, 104, 775, 548), fill=PANEL_BG, outline=GRID_COL, width=2)
    dr.text((68, 120), 'Criba de Möbius μ(d) en d = 1..16 (+1 verde | −1 coral | 0 gris)', font=f_sec, fill=COL_MU_POS)

    for d in range(1, 17):
        mu_val = mobius_mu(d)
        col = COL_MU_POS if mu_val == 1 else (COL_MU_NEG if mu_val == -1 else COL_MU_ZERO)
        cx = 86 + (d - 1) * 42
        cy = 275
        bh = 105 if mu_val != 0 else 18
        y_top = cy - bh if mu_val > 0 else (cy if mu_val < 0 else cy - 9)
        y_bot = cy if mu_val > 0 else (cy + bh if mu_val < 0 else cy + 9)
        dr.rectangle((cx - 13, y_top, cx + 13, y_bot), fill=col if mu_val != 0 else None, outline=col, width=2)
        dr.text((cx - 9, 405), f'd={d}', font=f_sm, fill=FG)
        lbl_mu = '+1' if mu_val == 1 else ('-1' if mu_val == -1 else ' 0')
        dr.text((cx - 10, 424), lbl_mu, font=f_sm, fill=col)

    dr.line((68, 275, 755, 275), fill=GRID_COL, width=1)
    dr.text((68, 462), '• Cuadrados prohibidos (μ=0): d = 4, 8, 9, 12, 16 → abren túneles espectrales para la voz.', font=f_sm, fill=COL_MELLIN)
    dr.text((68, 484), '• Primos (μ=−1): d = 2, 3, 5, 7, 11, 13 → entran en fase π («voz en negativo»).', font=f_sm, fill=COL_MU_NEG)
    dr.text((68, 506), '• Biprimos (μ=+1): d = 6, 10, 14, 15 → entran en fase 0 y cancelan las colas compuestas.', font=f_sm, fill=COL_MU_POS)

    # Panel derecho: Hallazgos medidos en la sonda
    dr.rectangle((805, 104, 1552, 548), fill=PANEL_BG, outline=GRID_COL, width=2)
    dr.text((825, 120), 'Resultados medidos por la sonda en spectrumsynth', font=f_sec, fill=COL_MELLIN)

    lineas = [
        ('1. Inversión de Chen–Möbius (sum_{d|m} μ(d) = δ_{m,1}):', COL_MU_POS),
        (f'   • Fundamental m=1 (110 Hz):             {p1["conservacion_fundamental_m1_dB"]:+.2f} dB (intacta)', FG),
        (f'   • Sobretonos compuestos m=2..6 (sincr.): {p1["supresion_sobretonos_compuestos_sincrona_dB"]:+.2f} dB (aniquilados)', FG),
        ('2. Lo que descubrió la sonda (Desfase de Ford vs Dirichlet):', COL_MU_NEG),
        (f'   • Con retardo de Ford (Δt = 140 ms):    {p1["supresion_sobretonos_con_desfase_ford_dB"]:+.2f} dB en promedio', MUTED),
        ('   • ¿Por qué? Mientras los biprimos aún no entran, los primos suenan solos', MUTED),
        ('     creando una «chispa aritmética de ataque» antes de cancelar en el sostén.', FG),
        ('3. Costura Square-Free y Espejo de Mellin (γ: +1 ↔ −1):', COL_MELLIN),
        (f'   • Caída en túneles cuadrados (4,8,9,12): {p2["caida_cuadrados_4_8_9_12_dB"]:+.2f} dB (hueco limpio)', FG),
        (f'   • Centroide: {p2["centroide_armonico_gamma_pos1_Hz"]:.0f} Hz (γ=+1, +{p2["desplazamiento_octavas_arriba_pivote"]:.2f} oct) ↔ {p2["centroide_subarmonico_gamma_neg1_Hz"]:.0f} Hz (γ=−1, {p2["desplazamiento_octavas_abajo_pivote"]:+.2f} oct)', FG),
        (f'   • Realce del 7º armónico con Ramanujan c_7(n): {p3["realce_relativo_7o_armonico_en_q7_dB"]:+.2f} dB', COL_RAMA),
    ]
    yy = 156
    for txt, col in lineas:
        dr.text((825, yy), txt, font=f_txt, fill=col)
        yy += 34

    # Panel inferior: El Reloj de Arena del Espejo de Mellin f_d(gamma) = f_0 * d^gamma
    dr.rectangle((48, 574, 1552, 918), fill=PANEL_BG, outline=GRID_COL, width=2)
    dr.text((68, 590), 'El Reloj de Arena de Grisey–Mellin: inversión continua de Serie Armónica (γ = +1) a Serie Subarmónica (γ = −1)', font=f_sec, fill=FG)

    gammas = np.linspace(1.0, -1.0, 600)
    box_m = (250, 636, 1220, 225)
    dr.rectangle((250, 636, 250 + 1220, 636 + 225), outline=GRID_COL, width=1)
    # Línea central: f_0 (log2(f/f0) = 0)
    dr.line((250, 636 + 112, 250 + 1220, 636 + 112), fill=GRID_COL, width=1)

    for d in [1, 2, 3, 5, 6, 7, 10, 11]:
        mu_v = mobius_mu(d)
        col = COL_MELLIN if d == 1 else (COL_MU_POS if mu_v == 1 else COL_MU_NEG)
        # En octavas relativas a f_0: log2(d^gamma) = gamma * log2(d)
        oct_curve = gammas * math.log2(d)
        dibujar_curva(dr, oct_curve, box_m, col, -3.6, +3.6, width=3 if d == 1 else 2)

    dr.text((68, 656), 'γ = +1: Armónicos', font=f_txt, fill=COL_MU_POS)
    dr.text((68, 700), 'γ =  0: Cáustica f0', font=f_txt, fill=COL_MELLIN)
    dr.text((68, 744), 'γ = −1: Subarmónicos', font=f_txt, fill=COL_MU_NEG)
    dr.text((68, 788), 'Ausentes: d=4,8,9,12', font=f_sm, fill=MUTED)

    for g_val, lbl in [(1.0, 'γ = +1.0 (Torre Partiels)'), (0.5, 'γ = +0.5 (Comprimido)'), (0.0, 'γ = 0.0 (Colapso diferencial)'), (-0.5, 'γ = −0.5 (Inversión)'), (-1.0, 'γ = −1.0 (f0/d)')]:
        xx = 250 + ((1.0 - g_val) / 2.0) * 1220
        dr.line((xx, 636, xx, 861), fill=GRID_COL, width=1)
        dr.text((xx - 45, 872), lbl, font=f_sm, fill=FG)

    im.save(str(path_png), 'PNG')
    return im

def crear_lamina_02_muestra_aislada(y_solo, tr_solo, med_solo, path_png):
    W, H = 1600, 960
    im = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(im)
    f_title = cargar_fuente(25, bold=True)
    f_sub = cargar_fuente(14)
    f_sec = cargar_fuente(15, bold=True)
    f_sm = cargar_fuente(11)

    dr.text((48, 24), '02 · MUESTRA AISLADA · EL CANDELABRO DE MÖBIUS–GRISEY (24 s)', font=f_title, fill=FG)
    dr.text((48, 60), f'Archivo: {med_solo["m4a"]} · {med_solo["I_LUFS"]:.1f} LUFS · {med_solo["pico_dBTP"]:.1f} dBTP · LRA {med_solo["LRA"]:.1f} · Semilla {SEMILLA}', font=f_sub, fill=MUTED)

    x0, w_plot = 235, 1310
    secciones = [
        (0.0, 'I · Serie completa (α=0)'),
        (4.8, 'II · Criba Möbius (α=1)'),
        (9.6, 'III · Colapso Mellin (γ→0)'),
        (14.4, 'IV · Abismo f0/d (γ=−1)'),
        (19.4, 'V · Ramanujan (q=7→11)')
    ]
    for sec_t, sec_lbl in secciones:
        xx = x0 + (sec_t / 24.0) * w_plot
        dr.line((xx, 112, xx, 885), fill=GRID_COL, width=1)
        dr.text((xx + 4, 110), sec_lbl, font=f_sm, fill=FG)

    controles = [
        ('gamma_mellin', 'Espejo Mellin γ(t)', -1.1, 1.1, COL_MELLIN),
        ('alpha_mobius', 'Criba Möbius α(t)', -0.05, 1.08, COL_MU_POS),
        ('q_ramanujan', 'Módulo Ramanujan q', 0.5, 12.5, COL_RAMA),
        ('beta_diferencial', 'Sombra Mi0 β(t)', 0.0, 1.05, COL_MU_NEG),
    ]
    for idx, (k_c, lab, lo, hi, col) in enumerate(controles):
        yy = 142 + idx * 92
        dr.rectangle((x0, yy, x0 + w_plot, yy + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
        dr.text((48, yy + 24), lab, font=f_sec, fill=col)
        dibujar_curva(dr, tr_solo[k_c], (x0, yy + 4, w_plot, 64), col, lo, hi, width=2)

    yy_w = 518
    dr.rectangle((x0, yy_w, x0 + w_plot, yy_w + 88), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy_w + 30), 'Onda estéreo', font=f_sec, fill=FG)
    y_norm_vis = normalizar_nivel(y_solo)
    dibujar_curva(dr, y_norm_vis[:, 0], (x0, yy_w + 4, w_plot, 80), COL_MU_POS, -0.75, 0.75, width=1)

    yy_s = 626
    spec_im = espectrograma_imagen(y_solo, SR, w_plot, 252)
    im.paste(spec_im, (x0, yy_s))
    dr.rectangle((x0, yy_s, x0 + w_plot, yy_s + 252), outline=GRID_COL, width=1)
    dr.text((48, yy_s + 20), 'Espectrograma\n35 Hz – 10.5 kHz', font=f_sec, fill=FG)
    dr.text((48, yy_s + 78), 'En II desaparecen\n4f, 8f, 9f; en III\ncolapsa hacia f0 y\nen IV se abre hacia\nel abismo subgrave.', font=f_sm, fill=COL_MELLIN)

    for s_tick in range(0, 25, 3):
        xx = x0 + (s_tick / 24.0) * w_plot
        dr.text((xx - 10, 892), f'{s_tick} s', font=f_sm, fill=MUTED)
    dr.text((48, 922), 'Lectura: el paso de γ=+1 (I–II) a γ=0 (III) y γ=−1 (IV) invierte la pirámide armónica en un candelabro subarmónico limpio.', font=f_sm, fill=MUTED)

    im.save(str(path_png), 'PNG')
    return im

def crear_lamina_03_escena_costura(y_mix, tr_esc, med_mix, path_png):
    W, H = 1600, 960
    im = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(im)
    f_title = cargar_fuente(25, bold=True)
    f_sub = cargar_fuente(14)
    f_sec = cargar_fuente(15, bold=True)
    f_sm = cargar_fuente(11)

    dr.text((48, 24), '03 · ESCENA EN CONTEXTO · CANDELABRO + TROMBÓN Mi0 (PARTIELS) + SIRINGUA EN HUECOS μ=0', font=f_title, fill=FG)
    dr.text((48, 60), f'Archivo: {med_mix["m4a"]} · {med_mix["I_LUFS"]:.1f} LUFS · {med_mix["pico_dBTP"]:.1f} dBTP · La Siringua canta en 4f0, 8f0 y 9f0 donde μ(n) = 0', font=f_sub, fill=MUTED)

    x0, w_plot = 235, 1310
    secciones = [
        (0.0, 'I · Mi0 Partiels (α=0)'),
        (4.2, 'II · Costura (4f0, 8f0)'),
        (8.4, 'III · Compresión + 9f0'),
        (12.4, 'IV · Abismo f0/d (γ=−1)'),
        (18.2, 'V · Cierre (q=6)')
    ]
    for sec_t, sec_lbl in secciones:
        xx = x0 + (sec_t / 24.0) * w_plot
        dr.line((xx, 112, xx, 885), fill=GRID_COL, width=1)
        dr.text((xx + 4, 110), sec_lbl, font=f_sm, fill=FG)

    filas = [
        ('gamma_mellin', 'Espejo Mellin γ(t)', -1.1, 1.1, COL_MELLIN),
        ('env_trombon_mi0', 'Ola Trombón Mi0', 0.0, 1.15, COL_MU_NEG),
        ('f0_siringua_squarefree', 'Siringua (4f,8f,9f)', 280.0, 800.0, COL_RAMA),
        ('q_ramanujan', 'Módulo Ramanujan q', 0.5, 12.0, COL_MU_POS),
    ]
    for idx, (k_c, lab, lo, hi, col) in enumerate(filas):
        yy = 142 + idx * 92
        dr.rectangle((x0, yy, x0 + w_plot, yy + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
        dr.text((48, yy + 24), lab, font=f_sec, fill=col)
        dibujar_curva(dr, tr_esc[k_c], (x0, yy + 4, w_plot, 64), col, lo, hi, width=2)

    yy_w = 518
    dr.rectangle((x0, yy_w, x0 + w_plot, yy_w + 88), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy_w + 26), 'Mezcla estéreo', font=f_sec, fill=FG)
    y_norm_vis = normalizar_nivel(y_mix)
    dibujar_curva(dr, y_norm_vis[:, 0], (x0, yy_w + 4, w_plot, 80), COL_MELLIN, -0.75, 0.75, width=1)

    yy_s = 626
    spec_im = espectrograma_imagen(y_mix, SR, w_plot, 252)
    im.paste(spec_im, (x0, yy_s))
    dr.rectangle((x0, yy_s, x0 + w_plot, yy_s + 252), outline=GRID_COL, width=1)
    dr.text((48, yy_s + 20), 'Espectrograma\nMezcla Completa', font=f_sec, fill=FG)
    dr.text((48, yy_s + 78), 'Abajo ruge el Mi0\n(41.2 Hz); en medio\nla Siringua ocupa\nlos túneles 4f, 8f, 9f\ndejados por μ(n)=0.', font=f_sm, fill=COL_RAMA)

    for s_tick in range(0, 25, 3):
        xx = x0 + (s_tick / 24.0) * w_plot
        dr.text((xx - 10, 892), f'{s_tick} s', font=f_sm, fill=MUTED)
    dr.text((48, 922), 'Costura por teoría de números: donde el Candelabro tiene ceros de Möbius (n=4, 8, 9, 12), la Siringua entra sin pelear por espacio.', font=f_sm, fill=MUTED)

    im.save(str(path_png), 'PNG')
    return im


# ───────────── 5b. Sonda del motor que suena (21 oct 2026) ─────────────
def sonda_del_motor_que_suena():
    """La sonda original mide en el escritor espectral de laboratorio; ésta mide en render_candelabro_temporal,
    el que hace las muestras, con fiel = False (original) y fiel = True (arreglado). Sostén = 0.5–2.3 s de la nota."""
    def banda(y, f, bw=6.0):
        Y = np.abs(np.fft.rfft(y * np.hanning(len(y)))) ** 2; fr = np.fft.rfftfreq(len(y), 1 / SR)
        return float(Y[(fr > f - bw) & (fr < f + bw)].sum()) + 1e-30

    def db(a, b):
        return round(10 * math.log10(a / b), 2)

    def ev(fiel, a=.6, b=2.4, **kw):
        e = {'t0': 0.1, 'dur': 2.5, 'f_pivote': 110.0, 'gamma': 1.0, 'alpha_mu': 1.0, 'q_rama': 1, 'vel': .9, 'beta_diff': 0.0, 'fiel': fiel, **kw}
        y, _, _ = render_candelabro_temporal({'eventos': [e], 'sombra_diferencial_beta': [[0, 0], [3.5, 0]]}, 3.5, SR, SEMILLA)
        return y.sum(1)[int(a * SR):int(b * SR)]
    comp = lambda y: sum(banda(y, 110 * m) for m in range(2, 16))
    otros = lambda y: sum(banda(y, 110 * m) for m in (5, 6, 7, 10, 11)) / 5
    r = {}
    for fiel in (False, True):
        c = {}
        for ford in (0.0, 0.32):
            s0, s1 = ev(fiel, alpha_mu=0.0, modo_chen=True, retardo_ford=ford), ev(fiel, alpha_mu=1.0, modo_chen=True, retardo_ford=ford)
            a0, a1 = ev(fiel, .1, .45, alpha_mu=0.0, modo_chen=True, retardo_ford=ford), ev(fiel, .1, .45, alpha_mu=1.0, modo_chen=True, retardo_ford=ford)
            c[f'ford_{ford}'] = {'ataque_compuestos_dB': db(comp(a1), comp(a0)), 'sosten_compuestos_dB': db(comp(s1), comp(s0))}
        b1 = ev(fiel, alpha_mu=1.0, retardo_ford=0.0)
        r['fiel' if fiel else 'original'] = {'chen': c, 'huecos_vs_vecinos_dB': {str(m): db(banda(b1, 110 * m), otros(b1)) for m in (4, 8, 9, 12)}}
    mu0 = globals()['mobius_mu']
    g0 = ev(True, alpha_mu=1.0, gamma=0.0, retardo_ford=0.0)
    globals()['mobius_mu'] = lambda n: abs(mu0(n))
    g0abs = ev(True, alpha_mu=1.0, gamma=0.0, retardo_ford=0.0)
    globals()['mobius_mu'] = mu0
    r['gamma_0'] = {'pivote_con_mu_vs_con_abs_mu_dB': db(banda(g0, 110), banda(g0abs, 110)), 'mertens_M15': sum(mu0(d) for d in range(1, 16))}
    return r


def crear_lamina_04_motor_que_suena(sm, path_png):
    W, H = 1600, 960
    im = Image.new('RGB', (W, H), BG); dr = ImageDraw.Draw(im)
    ft, fs, fm = cargar_fuente(30, True), cargar_fuente(17, True), cargar_fuente(16)
    dr.text((48, 26), '04 · LO QUE SUENA · ORIGINAL CONTRA FIEL (sonda del 21 oct 2026)', font=ft, fill=FG)
    dr.text((48, 66), 'medido en render_candelabro_temporal, el motor de las muestras; La2 = 110 Hz; sostén 0.5–2.3 s, ataque 0–0.35 s', font=cargar_fuente(15), fill=MUTED)
    filas = [('Inversión de Dirichlet (modo Chen): compuestos 2–15 contra la serie sin criba', None)]
    for k in ('ford_0.0', 'ford_0.32'):
        o, f = sm['original']['chen'][k], sm['fiel']['chen'][k]
        filas.append((f'  retardo de Ford {k[5:]} s · sostén', (o['sosten_compuestos_dB'], f['sosten_compuestos_dB'])))
        filas.append((f'  retardo de Ford {k[5:]} s · ataque', (o['ataque_compuestos_dB'], f['ataque_compuestos_dB'])))
    filas.append(('Huecos libres de cuadrados (modo Candelabro): energía contra los vecinos 5, 6, 7, 10, 11', None))
    for m in ('4', '8', '9', '12'):
        filas.append((f'  {m}·f0', (sm['original']['huecos_vs_vecinos_dB'][m], sm['fiel']['huecos_vs_vecinos_dB'][m])))
    y = 140
    dr.text((900, y - 34), 'original', font=fs, fill=MUTED); dr.text((1180, y - 34), 'fiel', font=fs, fill=FG)
    for txt, v in filas:
        if v is None:
            y += 14; dr.text((60, y), txt, font=fs, fill=FG); y += 40; continue
        dr.text((60, y), txt, font=fm, fill=MUTED)
        for x, val, col in ((900, v[0], MUTED), (1180, v[1], FG)):
            dr.text((x, y), f'{val:+.1f} dB', font=fm, fill=col)
            L = min(240, abs(val) * 1.6); dr.rectangle((x + 110, y + 4, x + 110 + L * 0.5, y + 14), fill=COL_MU_POS if val < -20 else COL_MU_NEG)
        y += 36
    g = sm['gamma_0']
    dr.text((60, y + 30), f'Con γ = 0 los 15 parciales caen en el pivote: el signo de μ pesa {g["pivote_con_mu_vs_con_abs_mu_dB"]:+.1f} dB (la función de Mertens, M(15) = {g["mertens_M15"]}).', font=fm, fill=FG)
    dr.text((60, y + 64), 'Fiel: el modo Chen se limpia en el sostén (queda la senoide del pivote) y deja la chispa de Ford en el ataque; los huecos son huecos.', font=fm, fill=MUTED)
    im.save(str(path_png), 'PNG')
    return im


def main():
    print('1. Ejecutando sonda de La Criba de Möbius–Grisey...', flush=True)
    sonda_res = ejecutar_sonda()
    print('   Sonda OK:', json.dumps(sonda_res, ensure_ascii=False), flush=True)

    print('2. Sintetizando muestra aislada de 24 s...', flush=True)
    partitura_solo = {
        'prototipo': 'criba-mobius-grisey',
        'duracion': 24.0,
        'semilla': SEMILLA,
        'espejo_mellin_gamma': [
            [0.0, 1.0], [8.5, 1.0], [11.5, 0.12], [13.5, -0.35],
            [15.0, -1.0], [19.2, -1.0], [21.2, 1.0], [24.0, 1.0]
        ],
        'criba_mobius_alpha': [
            [0.0, 0.0], [4.2, 0.0], [5.2, 1.0], [24.0, 1.0]
        ],
        'modulo_ramanujan_q': [
            [0.0, 1], [9.5, 1], [10.0, 6], [15.0, 6],
            [19.5, 7], [21.2, 11], [22.5, 6], [24.0, 6]
        ],
        'sombra_diferencial_beta': [
            [0.0, 0.15], [5.0, 0.35], [10.0, 0.95],
            [15.0, 0.85], [20.0, 0.45], [24.0, 0.30]
        ],
        'eventos': [
            # I: Serie armónica completa tipo Partiels (alpha_mu = 0.0, gamma = +1.0) sobre La2 = 110 Hz
            {'t0': 0.25, 'dur': 4.3, 'f_pivote': 110.0, 'gamma': 1.0, 'alpha_mu': 0.0, 'q_rama': 1, 'vel': 0.86, 'retardo_ford': 0.38},
            # II: Se activa la Criba de Möbius (alpha_mu = 1.0): desaparecen los cuadrados 4, 8, 9, 12 y los primos invierten fase
            {'t0': 4.85, 'dur': 4.4, 'f_pivote': 110.0, 'gamma': 1.0, 'alpha_mu': 1.0, 'q_rama': 1, 'vel': 0.90, 'retardo_ford': 0.32, 'modo_chen': True},
            # III: Colapso en el Espejo de Mellin (gamma -> 0.15 -> -0.35) con batimientos diferenciales y sombra en Mi0 (41.2 Hz)
            {'t0': 9.65, 'dur': 4.5, 'f_pivote': 220.0, 'alpha_mu': 1.0, 'q_rama': 6, 'vel': 0.88, 'retardo_ford': 0.22},
            # IV: Abismo Subarmónico puro (gamma = -1.0) colgado de Mi4 = 329.63 Hz hacia Mi0 = 41.20 Hz con limpieza de Chen-Möbius
            {'t0': 14.50, 'dur': 4.6, 'f_pivote': 329.6276, 'gamma': -1.0, 'alpha_mu': 1.0, 'q_rama': 6, 'vel': 0.94, 'retardo_ford': 0.28, 'modo_chen': True},
            # V: Iluminación selectiva de Ramanujan (q = 7 -> 11 -> 6) resaltando el 7º y 11º armónicos
            {'t0': 19.45, 'dur': 2.1, 'f_pivote': 164.8138, 'gamma': 1.0, 'alpha_mu': 1.0, 'q_rama': 7, 'vel': 0.90, 'retardo_ford': 0.18},
            {'t0': 21.55, 'dur': 2.3, 'f_pivote': 164.8138, 'gamma': 1.0, 'alpha_mu': 1.0, 'q_rama': 11, 'vel': 0.92, 'retardo_ford': 0.18},
        ]
    }
    print('1b. Sonda del motor que suena (original contra fiel)...', flush=True)
    sonda_motor = sonda_del_motor_que_suena()
    print('   ', json.dumps(sonda_motor, ensure_ascii=False), flush=True)
    y_solo, tr_solo, info_solo = render_candelabro_temporal(partitura_solo, 24.0, SR, SEMILLA)
    # la misma partitura con fiel = False: sale igual a la muestra original (SHA eecfb01a7106fe79)
    y_orig, _, _ = render_candelabro_temporal({**partitura_solo, 'fiel': False}, 24.0, SR, SEMILLA)
    med_orig = guardar_audio_y_medir(
        y_orig,
        OUT_DIR / 'muestra-criba-mobius-grisey-original-s20261021.wav',
        OUT_DIR / 'muestra-criba-mobius-grisey-original-s20261021.m4a',
        target_lufs=-18.5
    )
    med_solo = guardar_audio_y_medir(
        y_solo,
        OUT_DIR / 'muestra-criba-mobius-grisey-s20261021.wav',
        OUT_DIR / 'muestra-criba-mobius-grisey-s20261021.m4a',
        target_lufs=-18.5
    )

    print('3. Sintetizando escena en contexto (Candelabro + Trombón Mi0 Partiels + Siringua en huecos μ=0)...', flush=True)
    y_mix, stems_esc, tr_esc = render_escena_grisey_costura(24.0, SR, SEMILLA)
    med_mix = guardar_audio_y_medir(
        y_mix,
        OUT_DIR / 'escena-grisey-siringua-s20261021.wav',
        OUT_DIR / 'escena-grisey-siringua-s20261021.m4a',
        target_lufs=-16.0
    )

    print('4. Generando láminas PNG en OKLCh y GIF...', flush=True)
    p1_png = OUT_DIR / '01-criba-dirichlet-y-sonda-s20261021.png'
    p2_png = OUT_DIR / '02-espejo-mellin-y-espectrograma-s20261021.png'
    p3_png = OUT_DIR / '03-escena-grisey-costura-squarefree-s20261021.png'
    im1 = crear_lamina_01_dirichlet_y_sonda(sonda_res, p1_png)
    im2 = crear_lamina_02_muestra_aislada(y_solo, tr_solo, med_solo, p2_png)
    im3 = crear_lamina_03_escena_costura(y_mix, tr_esc, med_mix, p3_png)
    im4 = crear_lamina_04_motor_que_suena(sonda_motor, OUT_DIR / '04-lo-que-suena-original-contra-fiel-s20261021.png')

    frames = [im.resize((1200, 720), Image.Resampling.LANCZOS).quantize(colors=256, method=Image.Quantize.MEDIANCUT) for im in (im1, im2, im3, im4)]
    gif_path = OUT_DIR / 'proceso-criba-mobius-s20261021.gif'
    frames[0].save(
        str(gif_path),
        format='GIF',
        save_all=True,
        append_images=frames[1:],
        duration=1800,
        loop=0,
        optimize=True
    )

    shutil.copyfile(__file__, OUT_DIR / 'criba_mobius_grisey.py')

    receta = {
        'instrumento': 'El Candelabro (Criba) de Möbius–Grisey (mu * M_s)',
        'fecha_utc': '2026-10-21',
        'semilla': SEMILLA,
        'ejecucion_sha256': EJECUCION,
        'sonda': sonda_res,
        'sonda_del_motor_que_suena': sonda_motor,
        'muestra_aislada': med_solo,
        'muestra_aislada_original_fiel_false': med_orig,
        'escena_contexto': med_mix,
        'gif': {
            'archivo': gif_path.name,
            'duracion_s': 7.2,
            'bytes': gif_path.stat().st_size,
            'cuadros': 4
        },
        'partitura_muestra': partitura_solo
    }
    receta_path = OUT_DIR / 'receta-criba-mobius-s20261021.json'
    with open(receta_path, 'w', encoding='utf-8') as f:
        json.dump(receta, f, ensure_ascii=False, indent=2)

    print('5. Todo completado con éxito:', json.dumps(receta, ensure_ascii=False, indent=2), flush=True)

if __name__ == '__main__':
    main()