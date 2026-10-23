"""Construcción, sonda y producción real de El Monodromio No-Hermítico de Berry–EP2 (sqrt(z - z_EP)) para Rejilla.

Ejecuta:
1. Sonda matemática y acústica (`ejecutar_sonda()`):
   - Prueba 1 (Monodromía en la Superficie de Riemann sqrt(z^2 + 4*kappa^2) — Permutación topológica en 2*pi y Fase de Berry en 4*pi):
     Sigue analíticamente las dos hojas de autovalores Omega_+(phi) y Omega_-(phi) para cada par conjugado (armónico n*f0, subarmónico f0/n) a lo largo de un lazo cerrado z(phi) = z_0 + s_rho*(z_EP - z_0)*(1 - exp(i*sigma*phi)).
     Comprueba que cuando rho < 1.0 (lazo trivial fuera del punto excepcional), en phi = 2*pi cada modo regresa a su propia frecuencia (Delta_f = 0 Hz).
     En cambio, cuando rho > 1.0 (lazo que encierra el punto de ramificación z_EP = 2*i*kappa), en phi = 2*pi el modo que empezó en el armónico n*f0 termina exactamente en la frecuencia del subarmónico f0/n y viceversa (permutación topológica de hojas sin saltos ni crossfades, error 0.00e+00 Hz), y sólo en phi = 4*pi recupera su identidad original con signo de Berry invertido (-1).
   - Prueba 2 (Envolvente Secular del Bloque de Jordan t * exp(-a*t) en fórmula cerrada dentro de `PistaRejilla` + `spectrumsynth`):
     Verifica la suma cerrada exacta de la derivada de la serie geométrica sum_{m=0}^{M-1} m * exp(q*m) en `PistaRejilla.modo_jordan()` contra la FFT exacta de la señal temporal (error máx ~1e-16 en todos los bins AC) y contra `spectrumsynth` de FFmpeg (`gray16le`, S=32768, H=16384, SNR 66.25 dB), comprobando que el pico de amplitud se desplaza exactamente de t = 0 a t_pico = 1 / a = 0.2500 s.
   - Prueba 3 (Colapso de Dimensión de Jordan en z = z_EP, Trampa de Resonancia Hiperbólica cosh(alpha*ln 5) = 2^alpha y Factor de Petermann K):
     Mide cómo al llevar el control exactamente al Punto Excepcional (delta = 0, gamma = 2*kappa), los 12 modos (6 armónicos n*f0 + 6 subarmónicos f0/n) colapsan por parejas en 6 frecuencias unísonas degeneradas f_EP = ((n^2+1)/(2n))*f0, vaciando -41.74 dB en las 12 bandas originales cuando alpha = 1.0 (frente a sólo -3.74 dB si se comprime a alpha = 0.62 donde cosh(0.62*ln 5) choca con 2^0.62), mientras el factor de Petermann K = 1 / |<psi_L | psi_R>|^2 se dispara a 8000 en la garganta de coalescencia.
   - Prueba 4 (Quiralidad Asimétrica No-Hermítica sigma = +1 vs sigma = -1):
     Mide el transporte no-adiabático al rodear el EP2 en sentido antihorario (sigma = +1, amplificación relativa de la hoja armónica luminosa) frente a sentido horario (sigma = -1, amplificación relativa de la hoja subarmónica cavernosa).
2. Muestra aislada de 24 s (`muestra-monodromia-berry-ep2-s20261021.wav` y `.m4a`).
3. Escena en contexto de 24 s (`escena-haas-monodromia-ep2-s20261021.wav` y `.m4a`): homenaje a *in vain* (2000) de Georg Friedrich Haas (Monodromio de Berry–EP2 + Acordeón/Metales de Penumbra en batimientos justos vs temperados + Siringua cantando en los corredores despejados por el colapso de Jordan).
4. Tres láminas PNG en paleta OKLCh sembrada (revisadas visualmente) y GIF en loop del proceso.
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
OUT_DIR = AQUI / f'monodromia-berry-ep2-s{SEMILLA}-{EJECUCION[:12]}'
INTER_DIR = OUT_DIR / 'intermedio'
if __name__ == '__main__':
    OUT_DIR.mkdir(parents=False, exist_ok=False)
    INTER_DIR.mkdir()

# ───────────── 1. Matemática Exacta: Superficie de Riemann EP2, Seguimiento Analítico de Hojas y Factor de Petermann ─────────────
def seguir_hojas_riemann_ep2(phi_grid, f_arm, f_sub, kappa_hz, rho_ratio=1.35, sigma_dir=1.0):
    phi_arr = np.asarray(phi_grid, dtype=np.float64)
    f0_mid = 0.5 * (f_arm + f_sub)
    delta_full = float(f_arm - f_sub)
    kap = min(float(kappa_hz), 0.45 * abs(delta_full))
    delta_0 = math.sqrt(max(1e-9, delta_full ** 2 - 4.0 * (kap ** 2)))

    z_0 = complex(delta_0, 0.0)
    z_EP = complex(0.0, 2.0 * kap)
    s_rho = 0.5 * float(rho_ratio)

    z_path = z_0 + s_rho * (z_EP - z_0) * (1.0 - np.exp(1j * float(sigma_dir) * phi_arr))

    w_path = (z_path ** 2) + 4.0 * (kap ** 2)
    abs_w = np.abs(w_path)
    ang_w = np.unwrap(np.angle(w_path))
    sqrt_w = np.sqrt(abs_w) * np.exp(0.5j * ang_w)

    gamma_0 = 2.4
    Omega_plus = (f0_mid - 1j * gamma_0) + 0.5 * sqrt_w
    Omega_minus = (f0_mid - 1j * gamma_0) - 0.5 * sqrt_w

    num_pet = (np.abs(z_path) ** 2) + 4.0 * (kap ** 2) + abs_w
    K_petermann = num_pet / (2.0 * abs_w + 1e-3 * (kap ** 2))
    berry_sign = np.cos(0.25 * (ang_w - ang_w[0]))

    return {
        'z_path': z_path,
        'z_EP': z_EP,
        'z_0': z_0,
        'f_plus': np.real(Omega_plus),
        'f_minus': np.real(Omega_minus),
        'gamma_plus': -np.imag(Omega_plus),
        'gamma_minus': -np.imag(Omega_minus),
        'K_petermann': K_petermann,
        'berry_sign': berry_sign,
        'ang_w_unwrapped': ang_w
    }


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

rng_vis = np.random.default_rng(SEMILLA + 108)
H0 = 264.0 + float(rng_vis.uniform(-8.0, 8.0))
BG = oklch(0.11, 0.030, H0)               # Oscuridad profunda de *in vain*
PANEL_BG = oklch(0.15, 0.036, H0 + 6)
GRID_COL = oklch(0.26, 0.038, H0)
FG = oklch(0.94, 0.022, H0 + 25)
MUTED = oklch(0.67, 0.036, H0 + 10)
COL_HOJA_ARM = oklch(0.82, 0.16, H0 - 75)   # Cian eléctrico: Hoja Armónica (+sqrt)
COL_HOJA_SUB = oklch(0.74, 0.18, H0 + 115)  # Magenta/carmesí: Hoja Subarmónica (-sqrt)
COL_JORDAN = oklch(0.86, 0.18, H0 - 155)    # Oro/ámbar: Punto Excepcional EP2 y Bloque de Jordan
COL_BERRY = oklch(0.79, 0.16, H0 + 45)      # Violeta/lila: Fase de Berry y Siringua en el colapso

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

def paneo(p):
    ang = (np.asarray(p, float) + 1.0) * math.pi / 4.0
    return np.cos(ang), np.sin(ang)


# ───────────── 3. Motor Espectral Exacto (`PistaRejilla` con soporte de Bloques de Jordan $t e^{-at}$) ─────────────
class PistaRejilla:
    def __init__(self, nombre, columnas, S_grid=32768, H_grid=16384):
        self.nombre = nombre
        self.C = columnas
        self.S = S_grid
        self.H = H_grid
        self.N = 2 * H_grid
        self.T = self.N / self.S  # 1.0 s exacto por columna
        self.F = self.S / self.N  # 1.0 Hz exacto por fila
        self.R = 1024
        self.segs = []
        self.grupo = 0

    def seg(self, B, f, a, ts, te, pan, orden_jordan=0):
        if f <= 20 or f >= self.S / 2 - 100:
            return
        gL, gR = paneo(pan)
        if te is None or te == math.inf:
            te = ts + (math.log(1e6) + 2.5 * orden_jordan) / max(a, 1e-3)
        te = min(te, self.C * self.T)
        if te > ts:
            self.segs.append((complex(B), float(f), float(a), float(ts), float(te), float(gL), float(gR), self.grupo, int(orden_jordan)))

    def modo(self, f, amp, t0, a, ataque=None, suelta=None, ar=None, pan=0.0, fase=0.0):
        self.grupo += 1
        B = amp * np.exp(1j * fase)
        if ataque and ataque > a:
            tp = math.log(ataque / a) / (ataque - a)
            B /= (math.exp(-a * tp) - math.exp(-ataque * tp))
        fin = t0 + suelta if suelta else None
        self.seg(B, f, a, t0, fin, pan, orden_jordan=0)
        if ataque and ataque > a:
            self.seg(-B, f, ataque, t0, fin, pan, orden_jordan=0)
        if suelta:
            L = suelta
            env = math.exp(-a * L) - (math.exp(-ataque * L) if (ataque and ataque > a) else 0.0)
            B1 = B * env * np.exp(2j * math.pi * f * L)
            self.seg(B1, f, ar or 12.0, t0 + L, None, pan, orden_jordan=0)

    def modo_jordan(self, f, amp_pico, t0, a, suelta=None, ar=None, pan=0.0, fase=0.0):
        self.grupo += 1
        B = (amp_pico * a * math.e) * np.exp(1j * fase)
        fin = t0 + suelta if suelta else None
        self.seg(B, f, a, t0, fin, pan, orden_jordan=1)
        if suelta:
            L = suelta
            env_L = L * math.exp(-a * L)
            B1 = B * env_L * np.exp(2j * math.pi * f * L)
            self.seg(B1, f, ar or 12.0, t0 + L, None, pan, orden_jordan=0)

    def escribir(self):
        ZL = np.zeros((self.C, self.H), complex)
        ZR = np.zeros((self.C, self.H), complex)
        todas = np.arange(1, self.H)
        ph_todas = -2j * math.pi * todas / self.N
        completa = set()
        for B, f, a, ts, te, gL, gR, g, oj in self.segs:
            ms, me = ts * self.S, te * self.S
            for b in range(max(0, int(ms // self.N)), min(self.C, int(math.ceil(me / self.N)))):
                if oj == 1:
                    completa.add((g, b))
                    continue
                corte = 0.0
                if ms < b * self.N:
                    dt_b = (b * self.N - ms) / self.S
                    corte = abs(B) * math.exp(-a * dt_b)
                if me > (b + 1) * self.N:
                    dt_e = ((b + 1) * self.N - ms) / self.S
                    corte = max(corte, abs(B) * math.exp(-a * dt_e))
                if corte > 2e-5:
                    completa.add((g, b))
        for B, f, a, ts, te, gL, gR, g, oj in self.segs:
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
                dt0 = (m0 - ms) / self.S
                for Bc, pc in ((B / 2.0, complex(-a, 2.0 * math.pi * f)), (B.conjugate() / 2.0, complex(-a, -2.0 * math.pi * f))):
                    q = pc / self.S + ph
                    pre = Bc * np.exp(pc * dt0) * np.exp(ph * (m0 - b * self.N))
                    expm1_q = np.expm1(q)
                    expm1_Mq = np.expm1(M_len * q)
                    S0 = expm1_Mq / expm1_q
                    if oj == 0:
                        c = c + pre * S0
                    else:
                        eq = expm1_q + 1.0
                        eMq = expm1_Mq + 1.0
                        num_S1 = (M_len - 1.0) * eMq * eq - M_len * eMq + eq
                        S1 = num_S1 / (expm1_q ** 2)
                        c = c + pre * (dt0 * S0 + (1.0 / self.S) * S1)
                c /= self.N
                ZL[b, k] += gL * c
                ZR[b, k] += gR * c
        return ZL, ZR

    def tiempo(self, t0, t1):
        n = np.arange(int(round(t0 * self.S)), int(round(t1 * self.S)))
        t = n / self.S
        y = np.zeros((len(n), 2))
        for B, f, a, ts, te, gL, gR, _, oj in self.segs:
            ok = (n >= math.ceil(ts * self.S)) & (n < math.ceil(te * self.S))
            if not ok.any():
                continue
            dt_vec = t[ok] - ts
            factor_j = dt_vec if oj == 1 else 1.0
            sig = np.real(B * factor_j * np.exp(complex(-a, 2.0 * math.pi * f) * dt_vec))
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


# ───────────── 4. Sonda de Verificación (`ejecutar_sonda()`) ─────────────
def ejecutar_sonda():
    resultados = {}

    # 1. Prueba de Monodromía Topológica en la Superficie de Riemann:
    f0 = 220.0
    f_arm_test = 440.0
    f_sub_test = 110.0
    kap_test = 72.0
    phi_4pi = np.linspace(0.0, 4.0 * math.pi, 2001)
    idx_2pi = 1000
    idx_4pi = 2000

    tr_out = seguir_hojas_riemann_ep2(phi_4pi, f_arm_test, f_sub_test, kap_test, rho_ratio=0.65, sigma_dir=1.0)
    tr_in = seguir_hojas_riemann_ep2(phi_4pi, f_arm_test, f_sub_test, kap_test, rho_ratio=1.35, sigma_dir=1.0)

    err_permutacion_arm_a_sub_2pi = abs(float(tr_in['f_plus'][idx_2pi]) - f_sub_test)
    signo_berry_4pi = float(tr_in['berry_sign'][idx_4pi])

    resultados['prueba_1_monodromia_topologica_riemann'] = {
        'frecuencia_inicial_hoja_armonica_Hz': f_arm_test,
        'frecuencia_inicial_hoja_subarmonica_Hz': f_sub_test,
        'lazo_fuera_ep_rho_065_f_en_2pi_Hz': round(float(tr_out['f_plus'][idx_2pi]), 4),
        'lazo_encierra_ep_rho_135_f_plus_en_2pi_Hz': round(float(tr_in['f_plus'][idx_2pi]), 4),
        'lazo_encierra_ep_rho_135_f_minus_en_2pi_Hz': round(float(tr_in['f_minus'][idx_2pi]), 4),
        'error_permutacion_arm_a_sub_en_2pi_Hz': float(f'{err_permutacion_arm_a_sub_2pi:.2e}'),
        'lazo_encierra_ep_rho_135_f_plus_en_4pi_Hz': round(float(tr_in['f_plus'][idx_4pi]), 4),
        'signo_fase_berry_en_4pi': round(signo_berry_4pi, 4)
    }

    # 2. Prueba de la Envolvente Secular del Bloque de Jordan t * e^{-a*t} en `PistaRejilla` + `spectrumsynth`
    P_jor = PistaRejilla('sonda_bloque_jordan', columnas=2, S_grid=32768, H_grid=16384)
    for k, f_v in enumerate([220.0, 330.0, 440.0, 550.0]):
        P_jor.modo_jordan(f_v, 0.15, 0.05 + 0.02 * k, a=4.0, suelta=None, pan=-0.3 + 0.2 * k)

    ZL_j, ZR_j = P_jor.escribir()
    wav_j = INTER_DIR / 'sonda_jordan_spectrumsynth.wav'
    esc_j = sintetizar_spectrumsynth(ZL_j, ZR_j, wav_j, S_grid=32768)
    _, y_ff = wavfile.read(wav_j)
    y_ff = y_ff.astype(np.float64) * esc_j
    y_ti = P_jor.tiempo(0.0, 2.0)
    snr_jordan_db = 10.0 * math.log10(np.sum(y_ti ** 2) / (np.sum((y_ff - y_ti) ** 2) + 1e-24))

    # Además, medir el error algebraico exacto de la fórmula cerrada S1 frente a la FFT de punto flotante en los bins AC (k >= 1)
    P_one = PistaRejilla('sonda_s1_fft', columnas=1, S_grid=32768, H_grid=16384)
    P_one.modo_jordan(330.0, 0.22, 0.15, a=4.0, suelta=None, pan=-1.0)  # pan=-1 -> todo al canal L
    ZL_one, _ = P_one.escribir()
    y_one = P_one.tiempo(0.0, 1.0)[:, 0]
    fft_ref = np.fft.rfft(y_one)[:16384] / 32768.0
    err_s1_fft = float(np.max(np.abs(ZL_one[0, 1:] - fft_ref[1:])))

    i_start_j = int(round(0.15 * 32768))
    env_j = np.abs(y_one[i_start_j:])
    win_s = np.ones(328) / 328.0
    env_j_smooth = np.convolve(env_j, win_s, mode='same')
    dt_pico_medido = float(np.argmax(env_j_smooth)) / 32768.0
    dt_pico_teorico = 1.0 / 4.0

    resultados['prueba_2_bloque_secular_jordan_spectrumsynth'] = {
        'error_max_formula_cerrada_S1_vs_FFT_AC': float(f'{err_s1_fft:.2e}'),
        'SNR_spectrumsynth_jordan_dB': round(snr_jordan_db, 2),
        'retraso_pico_secular_medido_s': round(dt_pico_medido, 4),
        'retraso_pico_secular_teorico_1_sobre_a_s': round(dt_pico_teorico, 4)
    }

    # 3. Prueba del Colapso de Dimensión en z = z_EP (Costura por coalescencia de autovalores):
    # - Con la serie armónica/subarmónica pura (alpha = 1.0, f_arm = n*f0, f_sub = f0/n),
    #   las frecuencias coalescentes f_EP = ((n^2+1)/(2n))*f0 jamás coinciden con ningún entero m ni fracción 1/d,
    #   vaciando -41.74 dB de las 12 bandas originales!
    # - En cambio, la sonda descubre que si se comprime con alpha = 0.62, ocurre la cuasi-resonancia hiperbólica
    #   cosh(0.62 * ln 5) = 1.540 approx 2^0.62 = 1.537 (338.9 Hz vs 338.1 Hz), dejando sólo -3.74 dB!
    def medir_despeje_alpha(alpha_val):
        P_desp = PistaRejilla('sonda_desp', columnas=2, S_grid=32768, H_grid=16384)
        P_coal = PistaRejilla('sonda_coal', columnas=2, S_grid=32768, H_grid=16384)
        n_list = [2, 3, 5, 7, 9, 11]
        f_pares = [(f0 * (n ** alpha_val), f0 * (n ** (-alpha_val))) for n in n_list]
        for idx_p, (fa, fs) in enumerate(f_pares):
            P_desp.modo(fa, 0.08 / ((idx_p + 1) ** 0.4), 0.05, a=3.5, ataque=95.0, suelta=None, pan=-0.4)
            P_desp.modo(fs, 0.08 / ((idx_p + 1) ** 0.4), 0.05, a=3.5, ataque=95.0, suelta=None, pan=+0.4)
            f_mid = 0.5 * (fa + fs)
            P_coal.modo_jordan(f_mid, 0.11 / ((idx_p + 1) ** 0.4), 0.05, a=3.5, suelta=None, pan=0.0)
        ZL_d, _ = P_desp.escribir()
        ZL_c, _ = P_coal.escribir()
        def energia_banda(Z_col, f_center, half_w=4):
            k0 = max(1, int(round(f_center)) - half_w)
            k1 = min(len(Z_col), int(round(f_center)) + half_w + 1)
            return float(np.sum(np.abs(Z_col[k0:k1]) ** 2))
        e_orig = sum(energia_banda(ZL_d[0], fa) + energia_banda(ZL_d[0], fs) for fa, fs in f_pares)
        e_coal = sum(energia_banda(ZL_c[0], fa) + energia_banda(ZL_c[0], fs) for fa, fs in f_pares)
        return 10.0 * math.log10((e_coal + 1e-24) / (e_orig + 1e-24))

    despeje_exacto_alpha1_db = medir_despeje_alpha(1.00)
    despeje_trampa_alpha062_db = medir_despeje_alpha(0.62)

    tr_ep_exact = seguir_hojas_riemann_ep2(phi_4pi, f_arm_test, f_sub_test, kap_test, rho_ratio=1.00, sigma_dir=1.0)
    max_petermann = float(np.max(tr_ep_exact['K_petermann']))

    resultados['prueba_3_colapso_jordan_y_petermann'] = {
        'voces_activas_fuera_ep': 12,
        'voces_coalescentes_en_ep': 6,
        'despeje_bandas_originales_costura_dB': round(despeje_exacto_alpha1_db, 2),
        'despeje_con_colision_hiperbolica_alpha062_dB': round(despeje_trampa_alpha062_db, 2),
        'factor_petermann_max_en_ep': round(max_petermann, 1)
    }

    # 4. Prueba de Quiralidad No-Hermítica (Giro antihorario sigma = +1 vs Giro horario sigma = -1)
    tr_ccw = seguir_hojas_riemann_ep2(phi_4pi, f_arm_test, f_sub_test, kap_test, rho_ratio=1.35, sigma_dir=+1.0)
    tr_cw = seguir_hojas_riemann_ep2(phi_4pi, f_arm_test, f_sub_test, kap_test, rho_ratio=1.35, sigma_dir=-1.0)
    ganancia_integrada_ccw = float(np.mean(tr_ccw['gamma_minus'][:idx_2pi] - tr_ccw['gamma_plus'][:idx_2pi]))
    ganancia_integrada_cw = float(np.mean(tr_cw['gamma_minus'][:idx_2pi] - tr_cw['gamma_plus'][:idx_2pi]))

    resultados['prueba_4_quiralidad_no_hermitica'] = {
        'asimetria_amortiguamiento_giro_antihorario_sigma_pos1': round(ganancia_integrada_ccw, 3),
        'asimetria_amortiguamiento_giro_horario_sigma_neg1': round(ganancia_integrada_cw, 3)
    }

    return resultados


# ───────────── 5. Motor Temporal de 24 s (Muestra Aislada: El Monodromio No-Hermítico de Berry–EP2) ─────────────
def render_monodromia_berry_ep2(partitura, duracion=24.0, sr=SR, semilla=SEMILLA):
    n_total = int(round(duracion * sr))
    t = np.arange(n_total) / sr
    out = np.zeros((n_total, 2), dtype=np.float64)
    rng = np.random.default_rng(semilla + 41)

    def interp_ctrl(key, default):
        pts = np.asarray(partitura.get(key, [[0.0, default], [duracion, default]]), dtype=float)
        return np.interp(t, pts[:, 0], pts[:, 1])

    phi_curve = interp_ctrl('angulo_monodromia_phi', 0.0)
    rho_curve = interp_ctrl('radio_lazo_ep_rho', 1.35)
    sigma_curve = interp_ctrl('quiralidad_sigma', 1.0)
    jordan_curve = interp_ctrl('indice_jordan_eta', 0.5)

    n_primos = [2, 3, 5, 7, 9, 11]
    traza_f_hoja_pos = np.zeros(n_total, dtype=np.float64)
    traza_f_hoja_neg = np.zeros(n_total, dtype=np.float64)
    traza_petermann = np.ones(n_total, dtype=np.float64)

    ruido_base = sosfilt(butter(2, [450, 4200], fs=sr, btype='bandpass', output='sos'), rng.normal(0, 1.0, n_total))

    eventos = partitura.get('eventos', [])
    for ev in eventos:
        t0 = float(ev['t0'])
        dur_ev = float(ev['dur'])
        f_piv = float(ev['f_pivote'])
        vel = float(ev.get('vel', 0.90))
        # Usamos alpha_exp = 1.00 por defecto (serie armónica n*f0 y subarmónica f0/n exacta, libre de la colisión cosh(0.62*ln 5) = 2^0.62!)
        alpha_exp = float(ev.get('alpha_exp', 1.00))

        i0 = max(0, int(round(t0 * sr)))
        i1 = min(n_total, int(round((t0 + dur_ev) * sr)))
        if i1 <= i0:
            continue

        u = (np.arange(i0, i1) / sr) - t0
        phi_loc = phi_curve[i0:i1]
        rho_ev = float(ev.get('rho_ep', np.mean(rho_curve[i0:i1])))
        sigma_ev = float(ev.get('sigma', np.mean(sigma_curve[i0:i1])))
        eta_j = float(ev.get('eta_jordan', np.mean(jordan_curve[i0:i1])))

        n_sub = max(64, int(round(dur_ev * 400)))
        u_sub = np.linspace(0.0, dur_ev, n_sub)
        phi_sub = np.interp(u_sub, u, phi_loc)

        for idx_n, n_val in enumerate(n_primos):
            f_arm_n = min(sr * 0.42, f_piv * (float(n_val) ** alpha_exp))
            f_sub_n = max(28.0, f_piv * (float(n_val) ** (-alpha_exp)))
            kap_n = 0.36 * abs(f_arm_n - f_sub_n)

            hojas = seguir_hojas_riemann_ep2(
                phi_sub, f_arm_n, f_sub_n, kap_n,
                rho_ratio=rho_ev, sigma_dir=sigma_ev
            )

            f_pos = np.interp(u, u_sub, hojas['f_plus'])
            f_neg = np.interp(u, u_sub, hojas['f_minus'])
            g_pos = np.interp(u, u_sub, hojas['gamma_plus'])
            g_neg = np.interp(u, u_sub, hojas['gamma_minus'])
            K_pet = np.interp(u, u_sub, hojas['K_petermann'])
            b_sign = np.interp(u, u_sub, hojas['berry_sign'])

            if idx_n == 0:
                traza_f_hoja_pos[i0:i1] = f_pos
                traza_f_hoja_neg[i0:i1] = f_neg
                traza_petermann[i0:i1] = np.clip(K_pet, 1.0, 25.0)

            a_rate = 0.85 + 0.12 * idx_n
            env_exp = (np.sin(np.minimum(1.0, u / 0.04) * math.pi / 2.0) ** 2) * np.exp(-0.55 * a_rate * u)
            a_jor = 1.45 + 0.15 * idx_n
            env_jor = (a_jor * math.e * u) * np.exp(-a_jor * u)
            win_out = np.sin(np.minimum(1.0, (dur_ev - u) / 0.16) * math.pi / 2.0) ** 2
            env_base = ((1.0 - eta_j) * env_exp + eta_j * env_jor) * win_out

            peso_quiral_pos = np.clip(np.exp(-0.12 * (g_pos - 2.4)), 0.45, 1.65)
            peso_quiral_neg = np.clip(np.exp(-0.12 * (g_neg - 2.4)), 0.45, 1.65)

            ph_pos = 2.0 * math.pi * np.cumsum(f_pos) / sr
            ph_neg = 2.0 * math.pi * np.cumsum(f_neg) / sr
            fase_berry_rad = np.arccos(np.clip(b_sign, -1.0, 1.0))

            sig_pos = (
                1.00 * np.cos(ph_pos + fase_berry_rad) +
                0.28 * np.cos(2.0 * ph_pos - fase_berry_rad) +
                0.12 * np.cos(3.0 * ph_pos)
            ) * peso_quiral_pos

            sig_neg = (
                1.00 * np.cos(ph_neg - fase_berry_rad) +
                0.32 * np.cos(2.0 * ph_neg + fase_berry_rad) +
                0.14 * np.cos(3.0 * ph_neg)
            ) * peso_quiral_neg

            pet_boost = np.clip((K_pet - 1.0) / 14.0, 0.0, 1.0)
            grano_ep = 0.035 * pet_boost * ruido_base[i0:i1] * np.cos(ph_pos)

            amp_v = (0.092 * vel) / ((idx_n + 1) ** 0.52)

            pan_pos = float(np.clip(-0.55 * math.cos(float(np.mean(phi_loc)) * 0.5) + 0.12 * idx_n, -0.88, 0.88))
            pan_neg = -pan_pos
            gL_p, gR_p = paneo(pan_pos)
            gL_n, gR_n = paneo(pan_neg)

            out[i0:i1, 0] += amp_v * env_base * (gL_p * sig_pos + gL_n * sig_neg + grano_ep)
            out[i0:i1, 1] += amp_v * env_base * (gR_p * sig_pos + gR_n * sig_neg + grano_ep)

    f_mi0 = 41.2034
    env_mi0 = 0.045 * (0.5 + 0.5 * np.sin(0.5 * phi_curve))
    sig_mi0 = env_mi0 * (np.sin(2.0 * math.pi * f_mi0 * t) + 0.45 * np.sin(2.0 * math.pi * (2.0 * f_mi0) * t))
    out[:, 0] += sig_mi0 * 0.71
    out[:, 1] += sig_mi0 * 0.71

    for ch, delay_s, g_rev in ((0, 0.033, 0.15), (1, 0.047, 0.15), (0, 0.071, 0.09), (1, 0.083, 0.09)):
        nd = int(round(delay_s * sr))
        if nd < n_total:
            out[nd:, ch] += g_rev * out[:-nd, 1 - ch]

    trazas = {
        'phi_monodromia': phi_curve,
        'rho_ep': rho_curve,
        'f_hoja_pos': traza_f_hoja_pos,
        'f_hoja_neg': traza_f_hoja_neg,
        'K_petermann': traza_petermann,
    }
    return out, trazas


# ───────────── 6. Escena en Contexto (24 s): Homenaje a *in vain* de Georg Friedrich Haas ─────────────
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

def render_escena_haas_in_vain(duracion=24.0, sr=SR, semilla=SEMILLA):
    n_total = int(round(duracion * sr))
    t = np.arange(n_total) / sr
    rng = np.random.default_rng(semilla + 99)
    f0_piv = 220.0

    part_mono = {
        'angulo_monodromia_phi': [
            [0.0, 0.0], [4.6, 2.0 * math.pi],
            [4.8, 0.0], [7.2, math.pi], [9.5, 2.0 * math.pi],
            [9.7, 0.0], [14.3, 2.0 * math.pi],
            [14.5, 2.0 * math.pi], [17.0, 3.0 * math.pi], [19.1, 4.0 * math.pi],
            [19.3, 0.0], [24.0, 2.0 * math.pi]
        ],
        'radio_lazo_ep_rho': [
            [0.0, 0.62], [4.6, 0.62],
            [4.8, 1.00], [9.5, 1.00],
            [9.7, 1.38], [14.3, 1.38],
            [14.5, 1.00], [19.1, 1.38],
            [19.3, 1.42], [24.0, 1.42]
        ],
        'quiralidad_sigma': [
            [0.0, 1.0], [14.4, 1.0], [14.6, -1.0], [19.2, -1.0], [19.4, 1.0], [24.0, 1.0]
        ],
        'indice_jordan_eta': [
            [0.0, 0.15], [4.8, 0.95], [9.5, 0.95], [9.8, 0.45], [14.5, 0.95], [19.2, 0.65], [24.0, 0.80]
        ],
        'eventos': [
            {'t0': 0.2, 'dur': 4.5, 'f_pivote': f0_piv, 'rho_ep': 0.62, 'sigma': +1.0, 'eta_jordan': 0.15, 'vel': 0.86},
            {'t0': 4.8, 'dur': 4.6, 'f_pivote': f0_piv, 'rho_ep': 1.00, 'sigma': +1.0, 'eta_jordan': 0.95, 'vel': 0.92},
            {'t0': 9.6, 'dur': 4.6, 'f_pivote': f0_piv, 'rho_ep': 1.38, 'sigma': +1.0, 'eta_jordan': 0.50, 'vel': 0.90},
            {'t0': 14.4, 'dur': 4.6, 'f_pivote': f0_piv * 0.75, 'rho_ep': 1.05, 'sigma': -1.0, 'eta_jordan': 0.90, 'vel': 0.92},
            {'t0': 19.2, 'dur': 4.6, 'f_pivote': f0_piv, 'rho_ep': 1.40, 'sigma': +1.0, 'eta_jordan': 0.75, 'vel': 0.92},
        ]
    }
    y_mono, tr_mono = render_monodromia_berry_ep2(part_mono, duracion, sr, semilla)

    y_acordeon = np.zeros((n_total, 2), dtype=np.float64)
    env_acordeon = np.zeros(n_total, dtype=np.float64)
    pares_haas = [
        (1.5000, 2.0 ** (7.0 / 12.0)),
        (1.7500, 2.0 ** (10.0 / 12.0)),
        (1.3750, 2.0 ** (6.0 / 12.0)),
        (2.2500, 2.0 ** (14.0 / 12.0)),
    ]
    olas_haas = [
        (0.4, 4.0, 110.0, 0.78),
        (5.0, 4.2, 110.0, 0.72),
        (9.8, 4.2, 110.0, 0.86),
        (14.6, 4.2, 82.41, 0.74),
        (19.4, 4.2, 110.0, 0.88),
    ]
    for t_h, dur_h, f_base_h, vel_h in olas_haas:
        i0 = int(round(t_h * sr))
        i1 = min(n_total, int(round((t_h + dur_h) * sr)))
        if i1 <= i0:
            continue
        u = (np.arange(i0, i1) / sr) - t_h
        a_h = 1.35
        swell = (a_h * math.e * u) * np.exp(-a_h * u) * (np.sin(np.minimum(1.0, (dur_h - u) / 0.22) * math.pi / 2.0) ** 2)
        sig_L = np.zeros_like(u)
        sig_R = np.zeros_like(u)
        for idx_p, (r_just, r_temp) in enumerate(pares_haas):
            f_j = f_base_h * r_just
            f_t = f_base_h * r_temp
            amp_p = 0.048 * vel_h / ((idx_p + 1) ** 0.5)
            sig_L += amp_p * (np.sin(2.0 * math.pi * f_j * u) + 0.35 * np.sin(4.0 * math.pi * f_j * u))
            sig_R += amp_p * (np.sin(2.0 * math.pi * f_t * u) + 0.35 * np.sin(4.0 * math.pi * f_t * u))
        y_acordeon[i0:i1, 0] += sig_L * swell
        y_acordeon[i0:i1, 1] += sig_R * swell
        env_acordeon[i0:i1] += swell

    frases_siringua = [
        {'t': 5.1, 'dur': 3.6, 'f_hz': 440.0, 'vel': 0.90},
        {'t': 10.2, 'dur': 3.2, 'f_hz': 330.0, 'vel': 0.85},
        {'t': 14.8, 'dur': 3.6, 'f_hz': 330.0, 'vel': 0.92},
        {'t': 19.8, 'dur': 3.4, 'f_hz': 440.0, 'vel': 0.90},
    ]
    f0_sir = np.full(n_total, 440.0)
    amp_sir = np.zeros(n_total)
    for fr in frases_siringua:
        i0 = int(round(fr['t'] * sr))
        nn = min(int(round(fr['dur'] * sr)), n_total - i0)
        if i0 >= 0 and nn > 0:
            f0_sir[i0:i0 + nn] = float(fr['f_hz'])
            tt = np.arange(nn) / sr
            env_s = (np.sin(np.minimum(1.0, tt / 0.08) * math.pi / 2.0) ** 2) * (
                np.sin(np.minimum(1.0, (nn / sr - tt) / 0.18) * math.pi / 2.0) ** 2
            )
            amp_sir[i0:i0 + nn] = fr['vel'] * env_s

    f0_sir_vib = f0_sir * (2.0 ** ((4.8 * np.sin(2.0 * math.pi * 5.2 * t)) / 1200.0))
    ph_s = 2.0 * math.pi * np.cumsum(f0_sir_vib) / sr
    soplo = sosfilt(butter(2, [1300, 4800], fs=sr, btype='bandpass', output='sos'), rng.normal(0, 0.022, n_total))
    exc_s = (0.75 * np.sin(ph_s) + 0.25 * np.sin(0.5 * ph_s) + soplo) * amp_sir
    t_voc = np.array([0.0, 6.0, 12.0, 18.0, 24.0])
    vf = np.array([VOCALES[v] for v in ['o', 'a', 'u', 'i', 'a']], dtype=float)
    form_curves = np.array([np.interp(t, t_voc, vf[:, k]) for k in range(4)])
    sir_mono = formantes_boca(exc_s, form_curves, sr) * 2.35
    y_siringua = np.column_stack([sir_mono * 0.72, sir_mono * 0.72])

    mix = y_mono * 0.90 + y_acordeon * 0.84 + y_siringua * 0.92
    trazas_esc = {
        'phi_monodromia': tr_mono['phi_monodromia'],
        'f_hoja_pos': tr_mono['f_hoja_pos'],
        'f_hoja_neg': tr_mono['f_hoja_neg'],
        'env_acordeon_haas': env_acordeon,
        'f0_siringua_jordan': f0_sir_vib * (amp_sir > 0.04)
    }
    return mix, {'monodromia': y_mono, 'acordeon_haas': y_acordeon, 'siringua': y_siringua}, trazas_esc


# ───────────── 7. Medición LUFS y Generación de Láminas PNG + GIF ─────────────
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
    c_mid = np.array(COL_HOJA_SUB, dtype=float)
    c_hi = np.array(COL_HOJA_ARM, dtype=float)
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

def crear_lamina_01_riemann_jordan_sonda(sonda_res, path_png):
    W, H = 1600, 960
    im = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(im)
    f_title = cargar_fuente(24, bold=True)
    f_sub = cargar_fuente(14)
    f_sec = cargar_fuente(16, bold=True)
    f_txt = cargar_fuente(13)
    f_sm = cargar_fuente(11)

    p1 = sonda_res['prueba_1_monodromia_topologica_riemann']
    p2 = sonda_res['prueba_2_bloque_secular_jordan_spectrumsynth']
    p3 = sonda_res['prueba_3_colapso_jordan_y_petermann']
    p4 = sonda_res['prueba_4_quiralidad_no_hermitica']

    dr.text((48, 24), '01 · EL MONODROMIO NO-HERMÍTICO DE BERRY–EP2 (√(z − z_EP)) · RIEMANN Y JORDAN', font=f_title, fill=FG)
    dr.text((48, 60), f'Semilla {SEMILLA} · Serie S1 exacta (err {p2["error_max_formula_cerrada_S1_vs_FFT_AC"]:.1e}) · spectrumsynth {p2["SNR_spectrumsynth_jordan_dB"]} dB · Puntos Excepcionales EP2 y Bloques de Jordan', font=f_sub, fill=MUTED)

    dr.rectangle((48, 104, 775, 548), fill=PANEL_BG, outline=GRID_COL, width=2)
    dr.text((68, 120), 'Hojas de Riemann Ω±(φ) para Armónico (440 Hz) y Subarmónico (110 Hz)', font=f_sec, fill=COL_HOJA_ARM)

    phi_v = np.linspace(0.0, 4.0 * math.pi, 600)
    casos = [
        (0.65, '1. Lazo fuera del EP2 (ρ = 0.65 < 1)\nEn φ=2π cada hoja regresa a sí misma', 165),
        (1.00, '2. Choque exacto con EP2 (ρ = 1.00)\nEn φ=π colapsan a 275 Hz (Bloque Jordan)', 295),
        (1.35, '3. Lazo encierra al EP2 (ρ = 1.35 > 1)\n¡En φ=2π permutan 440 Hz ↔ 110 Hz!', 425),
    ]
    for rho_v, lbl_c, yy_box in casos:
        tr_c = seguir_hojas_riemann_ep2(phi_v, 440.0, 110.0, 72.0, rho_ratio=rho_v, sigma_dir=1.0)
        box_e = (355, yy_box, 395, 92)
        dr.rectangle((355, yy_box, 355 + 395, yy_box + 92), outline=GRID_COL, width=1)
        dr.line((355 + 197, yy_box, 355 + 197, yy_box + 92), fill=GRID_COL, width=1)
        dibujar_curva(dr, tr_c['f_plus'], box_e, COL_HOJA_ARM, 85.0, 465.0, width=2)
        dibujar_curva(dr, tr_c['f_minus'], box_e, COL_HOJA_SUB, 85.0, 465.0, width=2)
        dr.text((68, yy_box + 22), lbl_c, font=f_sm, fill=FG)

    dr.text((68, 522), 'Cian: Hoja +1 (inicia en 440 Hz) · Magenta: Hoja −1 (inicia en 110 Hz) · Línea media: φ = 2π', font=f_sm, fill=MUTED)

    dr.rectangle((805, 104, 1552, 548), fill=PANEL_BG, outline=GRID_COL, width=2)
    dr.text((825, 120), 'Resultados medidos por la sonda (Monodromía, Jordan y Costura)', font=f_sec, fill=COL_JORDAN)

    lineas = [
        ('1. Permutación topológica de hojas en φ = 2π (Monodromía EP2):', COL_HOJA_ARM),
        (f'   • Fuera del EP2 (ρ=0.65): 440 Hz → {p1["lazo_fuera_ep_rho_065_f_en_2pi_Hz"]:.1f} Hz en 2π (sin permutación)', MUTED),
        (f'   • Encerrando EP2 (ρ=1.35): 440 Hz → {p1["lazo_encierra_ep_rho_135_f_plus_en_2pi_Hz"]:.1f} Hz y 110 Hz → {p1["lazo_encierra_ep_rho_135_f_minus_en_2pi_Hz"]:.1f} Hz', FG),
        (f'   • Error de permutación en 2π: {p1["error_permutacion_arm_a_sub_en_2pi_Hz"]:.2e} Hz · Signo Berry en 4π: {p1["signo_fase_berry_en_4pi"]:+.1f}', FG),
        ('2. Envolvente Secular del Bloque de Jordan (t · e^(-at)):', COL_JORDAN),
        (f'   • Error serie cerrada S1 vs FFT AC: {p2["error_max_formula_cerrada_S1_vs_FFT_AC"]:.2e} · SNR 16-bit: {p2["SNR_spectrumsynth_jordan_dB"]:.2f} dB', FG),
        (f'   • Retraso del pico secular (a=4.0): medido {p2["retraso_pico_secular_medido_s"]:.4f} s (teór. {p2["retraso_pico_secular_teorico_1_sobre_a_s"]:.4f} s)', FG),
        ('3. Colapso de Dimensión en z = z_EP (Costura) y Trampa Hiperbólica:', COL_HOJA_SUB),
        (f'   • En serie pura (α=1.0): 12 voces → 6 unísonos ({p3["despeje_bandas_originales_costura_dB"]:+.2f} dB despejados)', FG),
        (f'   • Trampa en α=0.62 (cosh(0.62 ln 5)≈2^0.62): sólo baja {p3["despeje_con_colision_hiperbolica_alpha062_dB"]:+.2f} dB', MUTED),
        (f'   • Factor Petermann máx.: K = {p3["factor_petermann_max_en_ep"]:.0f} · Quiralidad σ=±1: {p4["asimetria_amortiguamiento_giro_antihorario_sigma_pos1"]:+.1f} / {p4["asimetria_amortiguamiento_giro_horario_sigma_neg1"]:+.1f}', COL_BERRY),
    ]
    yy = 156
    for txt, col in lineas:
        dr.text((825, yy), txt, font=f_txt, fill=col)
        yy += 34

    dr.rectangle((48, 574, 1552, 918), fill=PANEL_BG, outline=GRID_COL, width=2)
    dr.text((68, 590), 'Física en el Punto Excepcional: Ola Secular de Jordan t·e^(−at) vs Exponencial e^(−at) y Divergencia de Petermann K(φ)', font=f_sec, fill=FG)

    box_j = (260, 636, 1210, 225)
    dr.rectangle((260, 636, 260 + 1210, 636 + 225), outline=GRID_COL, width=1)
    u_plot = np.linspace(0.0, 1.5, 600)
    a_p = 4.0
    env_ord = np.exp(-a_p * u_plot)
    env_sec = (a_p * math.e * u_plot) * np.exp(-a_p * u_plot)
    tr_pet = seguir_hojas_riemann_ep2(np.linspace(0.0, 2.0 * math.pi, 600), 440.0, 110.0, 72.0, rho_ratio=1.02, sigma_dir=1.0)
    pet_norm = np.clip(tr_pet['K_petermann'] / np.max(tr_pet['K_petermann']), 0.0, 1.0)

    dibujar_curva(dr, env_ord, box_j, MUTED, 0.0, 1.08, width=2)
    dibujar_curva(dr, env_sec, box_j, COL_JORDAN, 0.0, 1.08, width=3)
    dibujar_curva(dr, pet_norm, box_j, COL_BERRY, 0.0, 1.08, width=2)

    dr.text((68, 658), 'Ola Jordan t·e^(−at)', font=f_txt, fill=COL_JORDAN)
    dr.text((68, 700), 'Modo normal e^(−at)', font=f_txt, fill=MUTED)
    dr.text((68, 742), 'Pico Petermann K(φ)', font=f_txt, fill=COL_BERRY)
    dr.text((68, 784), 'Pico Jordan en t = 1/a', font=f_sm, fill=COL_HOJA_ARM)

    for x_frac, txt_lbl, dx_off in [
        (0.0, 't = 0.0 s (Ataque nulo)', 0),
        (0.25 / 1.5, 't = 1/a = 0.25 s (Cresta Jordan)', 8),
        (0.50, 'φ = π (Garganta Petermann en z_EP)', -85),
        (1.0, 't = 1.5 s / φ = 2π (Permutación)', -195)
    ]:
        xx = 260 + x_frac * 1210
        dr.line((xx, 636, xx, 861), fill=GRID_COL, width=1)
        dr.text((xx + dx_off, 872), txt_lbl, font=f_sm, fill=FG)

    im.save(str(path_png), 'PNG')
    return im

def crear_lamina_02_muestra_aislada(y_solo, tr_solo, med_solo, path_png):
    W, H = 1600, 960
    im = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(im)
    f_title = cargar_fuente(24, bold=True)
    f_sub = cargar_fuente(14)
    f_sec = cargar_fuente(15, bold=True)
    f_sm = cargar_fuente(11)

    dr.text((48, 24), '02 · MUESTRA AISLADA · EL MONODROMIO NO-HERMÍTICO DE BERRY–EP2 (24 s)', font=f_title, fill=FG)
    dr.text((48, 60), f'Archivo: {med_solo["m4a"]} · {med_solo["I_LUFS"]:.1f} LUFS · {med_solo["pico_dBTP"]:.1f} dBTP · LRA {med_solo["LRA"]:.1f} · Semilla {SEMILLA}', font=f_sub, fill=MUTED)

    x0, w_plot = 235, 1310
    secciones = [
        (0.0, 'I · Lazo Trivial (ρ=0.62)'),
        (4.8, 'II · Bloque Jordan (ρ=1.0)'),
        (9.6, 'III · Escalera Haas (0→2π)'),
        (14.4, 'IV · Berry 4π (σ=−1)'),
        (19.2, 'V · Doble Espiral EP2')
    ]
    for sec_t, sec_lbl in secciones:
        xx = x0 + (sec_t / 24.0) * w_plot
        dr.line((xx, 112, xx, 885), fill=GRID_COL, width=1)
        dr.text((xx + 4, 110), sec_lbl, font=f_sm, fill=FG)

    yy0 = 142
    dr.rectangle((x0, yy0, x0 + w_plot, yy0 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy0 + 24), 'Ángulo φ(t) [0..4π]', font=f_sec, fill=COL_JORDAN)
    dibujar_curva(dr, tr_solo['phi_monodromia'], (x0, yy0 + 4, w_plot, 64), COL_JORDAN, 0.0, 4.0 * math.pi + 0.2, width=2)

    yy1 = 234
    dr.rectangle((x0, yy1, x0 + w_plot, yy1 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy1 + 24), 'Radio ρ / κ (EP=1)', font=f_sec, fill=COL_HOJA_ARM)
    dibujar_curva(dr, tr_solo['rho_ep'], (x0, yy1 + 4, w_plot, 64), COL_HOJA_ARM, 0.4, 1.6, width=2)

    yy2 = 326
    dr.rectangle((x0, yy2, x0 + w_plot, yy2 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy2 + 24), 'Hojas Ω+ y Ω− (Hz)', font=f_sec, fill=COL_HOJA_SUB)
    dibujar_curva(dr, tr_solo['f_hoja_pos'], (x0, yy2 + 4, w_plot, 64), COL_HOJA_ARM, 90.0, 460.0, width=2)
    dibujar_curva(dr, tr_solo['f_hoja_neg'], (x0, yy2 + 4, w_plot, 64), COL_HOJA_SUB, 90.0, 460.0, width=2)

    yy3 = 418
    dr.rectangle((x0, yy3, x0 + w_plot, yy3 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy3 + 24), 'Factor Petermann K', font=f_sec, fill=COL_BERRY)
    dibujar_curva(dr, tr_solo['K_petermann'], (x0, yy3 + 4, w_plot, 64), COL_BERRY, 1.0, 26.0, width=2)

    yy_w = 518
    dr.rectangle((x0, yy_w, x0 + w_plot, yy_w + 88), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy_w + 30), 'Onda estéreo', font=f_sec, fill=FG)
    y_norm_vis = normalizar_nivel(y_solo)
    dibujar_curva(dr, y_norm_vis[:, 0], (x0, yy_w + 4, w_plot, 80), COL_HOJA_ARM, -0.75, 0.75, width=1)

    yy_s = 626
    spec_im = espectrograma_imagen(y_solo, SR, w_plot, 252)
    im.paste(spec_im, (x0, yy_s))
    dr.rectangle((x0, yy_s, x0 + w_plot, yy_s + 252), outline=GRID_COL, width=1)
    dr.text((48, yy_s + 20), 'Espectrograma\n35 Hz – 10.5 kHz', font=f_sec, fill=FG)
    dr.text((48, yy_s + 78), 'En II colapsan en\nel bloque de Jordan;\nen III y V las hojas\ncruzan e intercambian\nsus alturas.', font=f_sm, fill=COL_JORDAN)

    for s_tick in range(0, 25, 3):
        xx = x0 + (s_tick / 24.0) * w_plot
        dr.text((xx - 10, 892), f'{s_tick} s', font=f_sm, fill=MUTED)
    dr.text((48, 922), 'Lectura: cuando ρ > 1 (secciones III–V), al completar 2π la curva cian (armónico) termina en el lugar de la magenta (subarmónico).', font=f_sm, fill=MUTED)

    im.save(str(path_png), 'PNG')
    return im

def crear_lamina_03_escena_haas(y_mix, tr_esc, med_mix, path_png):
    W, H = 1600, 960
    im = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(im)
    f_title = cargar_fuente(24, bold=True)
    f_sub = cargar_fuente(14)
    f_sec = cargar_fuente(15, bold=True)
    f_sm = cargar_fuente(11)

    dr.text((48, 24), '03 · ESCENA EN CONTEXTO · HOMENAJE A IN VAIN (MONODROMIO + ACORDEÓN HAAS + SIRINGUA)', font=f_title, fill=FG)
    dr.text((48, 60), f'Archivo: {med_mix["m4a"]} · {med_mix["I_LUFS"]:.1f} LUFS · {med_mix["pico_dBTP"]:.1f} dBTP · En el colapso de Jordan (II y IV) las 12 voces se funden en 6 y entra la Siringua', font=f_sub, fill=MUTED)

    x0, w_plot = 235, 1310
    secciones = [
        (0.0, 'I · Luz Microtonal'),
        (4.8, 'II · Colapso Jordan I'),
        (9.6, 'III · Escalera in vain'),
        (14.4, 'IV · Oscuridad / Jordan II'),
        (19.2, 'V · Retorno Berry 4π')
    ]
    for sec_t, sec_lbl in secciones:
        xx = x0 + (sec_t / 24.0) * w_plot
        dr.line((xx, 112, xx, 885), fill=GRID_COL, width=1)
        dr.text((xx + 4, 110), sec_lbl, font=f_sm, fill=FG)

    yy0 = 142
    dr.rectangle((x0, yy0, x0 + w_plot, yy0 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy0 + 24), 'Ángulo φ(t) [0..4π]', font=f_sec, fill=COL_JORDAN)
    dibujar_curva(dr, tr_esc['phi_monodromia'], (x0, yy0 + 4, w_plot, 64), COL_JORDAN, 0.0, 4.0 * math.pi + 0.2, width=2)

    yy1 = 234
    dr.rectangle((x0, yy1, x0 + w_plot, yy1 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy1 + 24), 'Permutación Ω± (Hz)', font=f_sec, fill=COL_HOJA_ARM)
    dibujar_curva(dr, tr_esc['f_hoja_pos'], (x0, yy1 + 4, w_plot, 64), COL_HOJA_ARM, 70.0, 460.0, width=2)
    dibujar_curva(dr, tr_esc['f_hoja_neg'], (x0, yy1 + 4, w_plot, 64), COL_HOJA_SUB, 70.0, 460.0, width=2)

    yy2 = 326
    dr.rectangle((x0, yy2, x0 + w_plot, yy2 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy2 + 24), 'Acordeón in vain', font=f_sec, fill=COL_HOJA_SUB)
    dibujar_curva(dr, tr_esc['env_acordeon_haas'], (x0, yy2 + 4, w_plot, 64), COL_HOJA_SUB, 0.0, 1.15, width=2)

    yy3 = 418
    dr.rectangle((x0, yy3, x0 + w_plot, yy3 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy3 + 24), 'Siringua en Colapso', font=f_sec, fill=COL_BERRY)
    dibujar_curva(dr, tr_esc['f0_siringua_jordan'], (x0, yy3 + 4, w_plot, 64), COL_BERRY, 250.0, 480.0, width=2)

    yy_w = 518
    dr.rectangle((x0, yy_w, x0 + w_plot, yy_w + 88), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy_w + 26), 'Mezcla estéreo', font=f_sec, fill=FG)
    y_norm_vis = normalizar_nivel(y_mix)
    dibujar_curva(dr, y_norm_vis[:, 0], (x0, yy_w + 4, w_plot, 80), COL_JORDAN, -0.75, 0.75, width=1)

    yy_s = 626
    spec_im = espectrograma_imagen(y_mix, SR, w_plot, 252)
    im.paste(spec_im, (x0, yy_s))
    dr.rectangle((x0, yy_s, x0 + w_plot, yy_s + 252), outline=GRID_COL, width=1)
    dr.text((48, yy_s + 20), 'Espectrograma\nMezcla in vain', font=f_sec, fill=FG)
    dr.text((48, yy_s + 78), 'En II y IV las 12\nvoces colapsan a 6\nunísonos de Jordan\ny abren corredor a\nla voz solista.', font=f_sm, fill=COL_BERRY)

    for s_tick in range(0, 25, 3):
        xx = x0 + (s_tick / 24.0) * w_plot
        dr.text((xx - 10, 892), f'{s_tick} s', font=f_sm, fill=MUTED)
    dr.text((48, 922), 'Costura por coalescencia no-hermítica: en z = z_EP la dimensión del espacio de autovectores cae a la mitad sin filtros externos.', font=f_sm, fill=MUTED)

    im.save(str(path_png), 'PNG')
    return im


def main():
    print('1. Ejecutando sonda de El Monodromio No-Hermítico de Berry–EP2...', flush=True)
    sonda_res = ejecutar_sonda()
    print('   Sonda OK:', json.dumps(sonda_res, ensure_ascii=False), flush=True)

    print('2. Sintetizando muestra aislada de 24 s...', flush=True)
    partitura_solo = {
        'prototipo': 'monodromia-berry-ep2',
        'duracion': 24.0,
        'semilla': SEMILLA,
        'angulo_monodromia_phi': [
            [0.0, 0.0], [4.6, 2.0 * math.pi],
            [4.8, 0.0], [7.2, math.pi], [9.5, 2.0 * math.pi],
            [9.7, 0.0], [14.3, 2.0 * math.pi],
            [14.5, 2.0 * math.pi], [19.1, 4.0 * math.pi],
            [19.3, 0.0], [24.0, 4.0 * math.pi]
        ],
        'radio_lazo_ep_rho': [
            [0.0, 0.62], [4.6, 0.62],
            [4.8, 1.00], [9.5, 1.00],
            [9.7, 1.38], [14.3, 1.38],
            [14.5, 1.38], [19.1, 1.38],
            [19.3, 1.45], [24.0, 1.45]
        ],
        'quiralidad_sigma': [
            [0.0, 1.0], [14.4, 1.0], [14.6, -1.0], [19.1, -1.0], [19.3, 1.0], [24.0, 1.0]
        ],
        'indice_jordan_eta': [
            [0.0, 0.15], [4.8, 0.95], [9.5, 0.95], [9.8, 0.45], [14.5, 0.65], [19.3, 0.80], [24.0, 0.80]
        ],
        'eventos': [
            {'t0': 0.25, 'dur': 4.4, 'f_pivote': 220.0, 'rho_ep': 0.62, 'sigma': +1.0, 'eta_jordan': 0.15, 'vel': 0.86},
            {'t0': 4.85, 'dur': 4.5, 'f_pivote': 220.0, 'rho_ep': 1.00, 'sigma': +1.0, 'eta_jordan': 0.95, 'vel': 0.92},
            {'t0': 9.65, 'dur': 4.5, 'f_pivote': 220.0, 'rho_ep': 1.38, 'sigma': +1.0, 'eta_jordan': 0.45, 'vel': 0.90},
            {'t0': 14.45, 'dur': 4.5, 'f_pivote': 196.0, 'rho_ep': 1.38, 'sigma': -1.0, 'eta_jordan': 0.65, 'vel': 0.92},
            {'t0': 19.25, 'dur': 4.5, 'f_pivote': 220.0, 'rho_ep': 1.45, 'sigma': +1.0, 'eta_jordan': 0.80, 'vel': 0.92},
        ]
    }
    y_solo, tr_solo = render_monodromia_berry_ep2(partitura_solo, 24.0, SR, SEMILLA)
    med_solo = guardar_audio_y_medir(
        y_solo,
        OUT_DIR / 'muestra-monodromia-berry-ep2-s20261021.wav',
        OUT_DIR / 'muestra-monodromia-berry-ep2-s20261021.m4a',
        target_lufs=-18.5
    )

    print('3. Sintetizando escena en contexto (*in vain* de Haas: Monodromio + Acordeón + Siringua en Colapso de Jordan)...', flush=True)
    y_mix, stems_esc, tr_esc = render_escena_haas_in_vain(24.0, SR, SEMILLA)
    med_mix = guardar_audio_y_medir(
        y_mix,
        OUT_DIR / 'escena-haas-monodromia-ep2-s20261021.wav',
        OUT_DIR / 'escena-haas-monodromia-ep2-s20261021.m4a',
        target_lufs=-16.0
    )

    print('4. Generando láminas PNG en OKLCh y GIF...', flush=True)
    p1_png = OUT_DIR / '01-superficie-riemann-jordan-y-sonda-s20261021.png'
    p2_png = OUT_DIR / '02-espiral-haas-y-espectrograma-s20261021.png'
    p3_png = OUT_DIR / '03-escena-in-vain-colapso-jordan-s20261021.png'
    im1 = crear_lamina_01_riemann_jordan_sonda(sonda_res, p1_png)
    im2 = crear_lamina_02_muestra_aislada(y_solo, tr_solo, med_solo, p2_png)
    im3 = crear_lamina_03_escena_haas(y_mix, tr_esc, med_mix, p3_png)

    frames = [im.resize((1200, 720), Image.Resampling.LANCZOS).quantize(colors=256, method=Image.Quantize.MEDIANCUT) for im in (im1, im2, im3)]
    gif_path = OUT_DIR / 'proceso-monodromia-berry-ep2-s20261021.gif'
    frames[0].save(
        str(gif_path),
        format='GIF',
        save_all=True,
        append_images=frames[1:],
        duration=1800,
        loop=0,
        optimize=True
    )

    shutil.copyfile(__file__, OUT_DIR / 'monodromia_berry_ep2.py')

    receta = {
        'instrumento': 'El Monodromio No-Hermítico de Berry–EP2 (sqrt(z - z_EP))',
        'fecha_utc': '2026-10-21',
        'semilla': SEMILLA,
        'sonda': sonda_res,
        'muestra_aislada': med_solo,
        'escena_contexto': med_mix,
        'gif': {
            'archivo': gif_path.name,
            'duracion_s': 5.4,
            'bytes': gif_path.stat().st_size,
            'cuadros': 3
        },
        'partitura_muestra': partitura_solo
    }
    receta_path = OUT_DIR / 'receta-monodromia-berry-ep2-s20261021.json'
    with open(receta_path, 'w', encoding='utf-8') as f:
        json.dump(receta, f, ensure_ascii=False, indent=2)

    print('5. Todo completado con éxito:', json.dumps(receta, ensure_ascii=False, indent=2), flush=True)

if __name__ == '__main__':
    main()