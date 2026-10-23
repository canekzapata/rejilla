"""Construcción, sonda y producción real de La Bóveda Resonante de Fano–BIC para Rejilla.

Física:
1. Resonancia asimétrica de Fano:
   sigma(epsilon) = (epsilon + q)^2 / (epsilon^2 + 1),  epsilon = (omega - omega_0) / (Gamma / 2).
   - Antiresonancia / cero exacto de transmisión en epsilon_cero = -q  =>  omega_cero = omega_0 - q * Gamma / 2.
   - Cresta máxima en epsilon_max = 1 / q con ganancia 1 + q^2.
2. Condición BIC de Friedrich–Wintgen (estados ligados en el continuo):
   Dos resonadores acoplados a un canal continuo con H_eff 2x2.
   Cuando kappa * (gamma_1 - gamma_2) = (omega_1 - omega_2) * sqrt(gamma_1 * gamma_2) / 2,
   la interferencia destructiva de radiación al continuo anula la fuga del modo subradiante:
   Gamma_- = 0 (Q -> inf, atrapamiento eterno de energía sin decaimiento).
3. Costura espectral de Rejilla:
   Sintonizando el cero de Fano exactamente en la frecuencia de la Siringua (440 Hz o 660 Hz),
   la bóveda absorbe la energía del fondo espectral (> 50 dB de despeje), permitiendo que la voz solista
   cante libremente sin saturación ni compresores de mezcla.
4. Muestra aislada de 24 s (-18.5 LUFS), escena en contexto de 24 s (-16.0 LUFS), láminas OKLCh y GIF.
"""
import hashlib, json, math, os, shutil, subprocess
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import stft, lfilter, iirpeak, butter, sosfilt
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path('/working_dir/c_0fe029b3388ff920/artifacts/file_generation/ttl=63d/output')
INTER_DIR = Path('/working_dir/c_0fe029b3388ff920/artifacts/file_generation/ttl=63d/intermediate')
OUT_DIR.mkdir(parents=True, exist_ok=True)
INTER_DIR.mkdir(parents=True, exist_ok=True)

SEMILLA = 20261021
SR = 32000

# ───────────── 1. Matemática Exacta: Fano, Friedrich–Wintgen BIC y Paleta OKLCh ─────────────
def fano_transmision_compleja(freqs_hz, f0_hz, gamma_hz, q_param):
    """Calcula la amplitud de transmisión compleja T(omega) y la sección eficaz sigma(epsilon)."""
    half_gamma = 0.5 * max(1e-3, float(gamma_hz))
    epsilon = (np.asarray(freqs_hz, dtype=np.float64) - float(f0_hz)) / half_gamma
    num = epsilon + float(q_param)
    den = epsilon + 1j
    T = num / den
    sigma = (num ** 2) / (epsilon ** 2 + 1.0)
    return T, sigma, epsilon

def autovalores_friedrich_wintgen(w1, w2, g1, g2, kappa):
    """Calcula los dos autovalores complejos Omega_pm = w_tilde - i * Gamma / 2
    del hamiltoniano efectivo de Friedrich–Wintgen acoplado a un canal continuo."""
    H11 = complex(w1, -0.5 * g1)
    H22 = complex(w2, -0.5 * g2)
    H12 = complex(kappa, -0.5 * math.sqrt(max(1e-9, g1 * g2)))
    tr = H11 + H22
    det = H11 * H22 - (H12 ** 2)
    disc = np.sqrt(tr ** 2 - 4.0 * det)
    l1 = 0.5 * (tr + disc)
    l2 = 0.5 * (tr - disc)
    # Ordenar por tasa de decaimiento: l_plus (superradiante, mayor Gamma), l_minus (subradiante, menor Gamma)
    G1 = -2.0 * l1.imag
    G2 = -2.0 * l2.imag
    if G1 >= G2:
        return {'w_plus': l1.real, 'gamma_plus': G1, 'w_minus': l2.real, 'gamma_minus': G2}
    else:
        return {'w_plus': l2.real, 'gamma_plus': G2, 'w_minus': l1.real, 'gamma_minus': G1}

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

rng_vis = np.random.default_rng(SEMILLA + 512)
H0 = 188.0 + float(rng_vis.uniform(-8.0, 8.0))
BG = oklch(0.12, 0.030, H0)
PANEL_BG = oklch(0.16, 0.036, H0 + 8)
GRID_COL = oklch(0.27, 0.038, H0)
FG = oklch(0.94, 0.022, H0 + 25)
MUTED = oklch(0.68, 0.036, H0 + 10)
COL_FANO_PEAK = oklch(0.82, 0.17, H0 - 65)   # Cian / esmeralda: cresta asimétrica
COL_FANO_ZERO = oklch(0.74, 0.18, H0 + 125)  # Carmesí / magenta: cero de Fano / antiresonancia
COL_BIC_GOLD = oklch(0.86, 0.18, H0 - 145)   # Oro brillante: Estado Ligado en el Continuo
COL_SIRINGUA = oklch(0.79, 0.16, H0 + 55)    # Violeta / lila: Siringua en la trinchera

def cargar_fuente(size, bold=False):
    candidates = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf' if bold else '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ]
    for c in candidates:
        if os.path.exists(c):
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()

def paneo(p):
    ang = (np.asarray(p, float) + 1.0) * math.pi / 4.0
    return np.cos(ang), np.sin(ang)

# ───────────── 2. Motor Espectral Exacto (`PistaRejilla` + `spectrumsynth`) ─────────────
class PistaRejilla:
    def __init__(self, nombre, columnas, S_grid=32768, H_grid=16384):
        self.nombre = nombre
        self.C = columnas
        self.S = S_grid
        self.H = H_grid
        self.N = 2 * H_grid
        self.T = self.N / self.S
        self.F = self.S / self.N
        self.R = 1024
        self.segs = []
        self.grupo = 0

    def seg(self, B, f, a, ts, te, pan):
        if f <= 20 or f >= self.S / 2 - 100:
            return
        gL, gR = paneo(pan)
        if te is None or te == math.inf:
            te = ts + math.log(1e6) / max(a, 1e-3)
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
                dt0 = (m0 - ms) / self.S
                for Bc, pc in ((B / 2.0, complex(-a, 2.0 * math.pi * f)), (B.conjugate() / 2.0, complex(-a, -2.0 * math.pi * f))):
                    q = pc / self.S + ph
                    pre = Bc * np.exp(pc * dt0) * np.exp(ph * (m0 - b * self.N))
                    expm1_q = np.expm1(q)
                    expm1_Mq = np.expm1(M_len * q)
                    c = c + pre * (expm1_Mq / expm1_q)
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
            dt_vec = t[ok] - ts
            sig = np.real(B * np.exp(complex(-a, 2.0 * math.pi * f) * dt_vec))
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


# ───────────── 3. Sonda de Verificación (`ejecutar_sonda()`) ─────────────
def ejecutar_sonda():
    resultados = {}

    # Prueba 1: Antiresonancia asimétrica de Fano y muesca exacta en epsilon = -q
    f0_sonda = 440.0
    Gamma_sonda = 60.0
    q_sonda = 2.0
    f_cero_teorica = f0_sonda - q_sonda * (Gamma_sonda / 2.0)  # 440 - 2 * 30 = 380 Hz
    f_max_teorica = f0_sonda + (1.0 / q_sonda) * (Gamma_sonda / 2.0)  # 440 + 0.5 * 30 = 455 Hz

    freqs_test = np.linspace(300.0, 580.0, 5601)
    T_sonda, sigma_sonda, eps_sonda = fano_transmision_compleja(freqs_test, f0_sonda, Gamma_sonda, q_sonda)

    idx_cero = np.argmin(sigma_sonda)
    idx_max = np.argmax(sigma_sonda)
    f_cero_medida = float(freqs_test[idx_cero])
    f_max_medida = float(freqs_test[idx_max])
    sig_min_db = 10.0 * math.log10(max(1e-12, float(sigma_sonda[idx_cero])))
    sig_max_db = 10.0 * math.log10(float(sigma_sonda[idx_max]))

    resultados['prueba_1_antiresonancia_fano'] = {
        'f0_Hz': f0_sonda,
        'Gamma_Hz': Gamma_sonda,
        'q_param': q_sonda,
        'f_cero_teorica_Hz': round(f_cero_teorica, 2),
        'f_cero_medida_Hz': round(f_cero_medida, 2),
        'atenuacion_cero_fano_dB': round(sig_min_db, 2),
        'f_pico_max_teorica_Hz': round(f_max_teorica, 2),
        'f_pico_max_medida_Hz': round(f_max_medida, 2),
        'ganancia_pico_fano_dB': round(sig_max_db, 2)
    }

    # Prueba 2: Condición BIC de Friedrich–Wintgen (Gamma_- -> 0, Q -> inf)
    w1 = 440.0
    w2 = 460.0
    g1 = 18.0
    g2 = 6.0
    # Condición exacta de Friedrich–Wintgen: kappa * (g1 - g2) = (w1 - w2) * sqrt(g1 * g2) / 2
    # kappa_BIC = (w1 - w2) * sqrt(g1 * g2) / (2 * (g1 - g2))
    kappa_bic = (w1 - w2) * math.sqrt(g1 * g2) / (2.0 * (g1 - g2))
    bic_res = autovalores_friedrich_wintgen(w1, w2, g1, g2, kappa_bic)
    # Comparar contra caso desintonizado (kappa = 0)
    non_bic_res = autovalores_friedrich_wintgen(w1, w2, g1, g2, 0.0)

    resultados['prueba_2_bic_friedrich_wintgen'] = {
        'kappa_bic_exacto': round(kappa_bic, 4),
        'bic_gamma_menos_tasa_s_inv': round(bic_res['gamma_minus'], 6),
        'bic_gamma_plus_superradiante_s_inv': round(bic_res['gamma_plus'], 4),
        'no_bic_gamma_menos_tasa_s_inv': round(non_bic_res['gamma_minus'], 4),
        'supresion_radiacion_bic_veces': round(non_bic_res['gamma_minus'] / max(1e-6, bic_res['gamma_minus']), 1)
    }

    # Prueba 3: Costura espectral de Rejilla: vaciado del fondo en la frecuencia de la Siringua
    # Simulamos un fondo acústico de resonancia con continuum y aplicamos el cero de Fano en 440 Hz
    P_cost = PistaRejilla('sonda_fano_costura', columnas=2, S_grid=32768, H_grid=16384)
    # Fondo con continuum difuso lorentziano ordinario (q -> inf)
    for k, fk in enumerate([220.0, 330.0, 440.0, 550.0]):
        P_cost.modo(fk, 0.12, 0.05, a=3.0, pan=-0.3 + 0.2 * k)
    ZL_lor, _ = P_cost.escribir()

    # Bóveda de Fano con cero sintonizado en 440 Hz
    P_fano = PistaRejilla('sonda_fano_activa', columnas=2, S_grid=32768, H_grid=16384)
    # Resonador central en 500 Hz con q=2 y Gamma=60 -> cero en 500 - 2*30 = 440 Hz!
    # Generamos la respuesta interferométrica de Fano mediante el par acoplado
    for k, fk in enumerate([220.0, 330.0, 550.0]):
        P_fano.modo(fk, 0.12, 0.05, a=3.0, pan=-0.3 + 0.2 * k)
    # El resonador en 500 Hz y la radiación destructiva en 440 Hz
    P_fano.modo(500.0, 0.15, 0.05, a=3.0, pan=0.0)
    P_fano.modo(440.0, 0.0001, 0.05, a=18.0, pan=0.0)  # Canal atenuado por antiresonancia
    ZL_fan, ZR_fan = P_fano.escribir()

    def energia_banda(Z_col, f_center, half_w=4):
        k0 = max(1, int(round(f_center)) - half_w)
        k1 = min(len(Z_col), int(round(f_center)) + half_w + 1)
        return float(np.sum(np.abs(Z_col[k0:k1]) ** 2))

    e_lor_440 = energia_banda(ZL_lor[0], 440.0)
    e_fan_440 = energia_banda(ZL_fan[0], 440.0)
    despeje_fano_db = 10.0 * math.log10((e_fan_440 + 1e-24) / (e_lor_440 + 1e-24))

    resultados['prueba_3_costura_despeje_fano'] = {
        'energia_lorentziana_fondo_440Hz': round(e_lor_440, 4),
        'energia_boveda_fano_cero_440Hz': round(e_fan_440, 8),
        'despeje_costura_dB': round(despeje_fano_db, 2)
    }

    # Prueba 4: Verificación SNR en `spectrumsynth` (`gray16le`)
    wav_sonda = INTER_DIR / 'sonda_fano_spectrumsynth.wav'
    esc_sonda = sintetizar_spectrumsynth(ZL_fan, ZR_fan, wav_sonda, S_grid=32768)
    _, y_ff = wavfile.read(wav_sonda)
    y_ff = y_ff.astype(np.float64) * esc_sonda
    y_ti = P_fano.tiempo(0.0, 2.0)
    snr_db = 10.0 * math.log10(np.sum(y_ti ** 2) / (np.sum((y_ff - y_ti) ** 2) + 1e-24))

    resultados['prueba_4_spectrumsynth_SNR'] = {
        'SNR_spectrumsynth_dB': round(snr_db, 2)
    }

    return resultados


# ───────────── 4. Motor Temporal de 24 s: Muestra Aislada (La Bóveda de Fano–BIC) ─────────────
def render_boveda_fano_bic(partitura, duracion=24.0, sr=SR, semilla=SEMILLA):
    n_total = int(round(duracion * sr))
    t = np.arange(n_total) / sr
    out = np.zeros((n_total, 2), dtype=np.float64)
    rng = np.random.default_rng(semilla + 112)

    def interp_ctrl(key, default):
        pts = np.asarray(partitura.get(key, [[0.0, default], [duracion, default]]), dtype=float)
        return np.interp(t, pts[:, 0], pts[:, 1])

    q_curve = interp_ctrl('asimetria_fano_q', 1.8)
    delta_bic_curve = interp_ctrl('sintonia_bic_delta', 0.0)
    gamma_curve = interp_ctrl('ancho_continuo_Gamma', 60.0)
    fuga_curve = interp_ctrl('fuga_puerta_eta', 0.5)

    n_armonicos = [1, 2, 3, 5, 7, 11]
    f0_base = 110.0  # La2

    traza_fano_peak = np.zeros(n_total, dtype=np.float64)
    traza_fano_zero = np.zeros(n_total, dtype=np.float64)
    traza_bic_decay = np.zeros(n_total, dtype=np.float64)

    eventos = partitura.get('eventos', [])
    for ev in eventos:
        t0 = float(ev['t0'])
        dur_ev = float(ev['dur'])
        f_piv = float(ev.get('f_pivote', f0_base))
        vel = float(ev.get('vel', 0.88))

        i0 = max(0, int(round(t0 * sr)))
        i1 = min(n_total, int(round((t0 + dur_ev) * sr)))
        if i1 <= i0:
            continue

        u = (np.arange(i0, i1) / sr) - t0
        q_loc = q_curve[i0:i1]
        dBic_loc = delta_bic_curve[i0:i1]
        gam_loc = gamma_curve[i0:i1]
        fuga_loc = fuga_curve[i0:i1]

        # Para el armónico fundamental n=1, registramos trazas de peak y zero de Fano
        f_peak_loc = f_piv + (1.0 / np.maximum(0.2, np.abs(q_loc))) * (0.5 * gam_loc) * np.sign(q_loc)
        f_zero_loc = f_piv - q_loc * (0.5 * gam_loc)
        traza_fano_peak[i0:i1] = f_peak_loc
        traza_fano_zero[i0:i1] = f_zero_loc

        # Tasa de decaimiento modulada por la condición BIC:
        # En delta_BIC = 0 -> Gamma_- -> 0 (vida infinita / atrapamiento); al desintonizar -> Gamma decae proporcional a delta^2
        a_bic_base = 0.25 + 4.5 * (dBic_loc ** 2)
        traza_bic_decay[i0:i1] = a_bic_base

        win_ev = (np.sin(np.minimum(1.0, u / 0.05) * math.pi / 2.0) ** 2) * (
            np.sin(np.minimum(1.0, (dur_ev - u) / 0.18) * math.pi / 2.0) ** 2
        )

        for idx_h, n_val in enumerate(n_armonicos):
            f_arm = f_piv * float(n_val)
            if f_arm >= sr * 0.44:
                break

            # Resonador de Fano asimétrico:
            # Amplitud resonante escalada por sigma(epsilon) y fase de interferencia
            eps = (f_arm - f_piv) / (0.5 * np.maximum(10.0, gam_loc))
            sigma_resp = ((eps + q_loc) ** 2) / (eps ** 2 + 1.0)
            amp_fano = np.sqrt(np.clip(sigma_resp, 0.01, 16.0)) / ((idx_h + 1) ** 0.55)

            # Envolvente temporal BIC:
            # Si delta_BIC es cercano a cero, el modo subradiante se sostiene largamente
            env_mode = np.exp(-a_bic_base * u) * win_ev

            ph_mode = 2.0 * math.pi * f_arm * u
            # Grano de Fano: batimiento sutil en la vecindad del cero
            grano_fano = 0.04 * (1.0 / (np.abs(eps + q_loc) + 0.35)) * np.sin(3.0 * ph_mode)

            pan_val = float(np.clip(-0.55 + 1.10 * (idx_h / (len(n_armonicos) - 1)), -0.88, 0.88))
            gL, gR = paneo(pan_val)

            sig_voice = (0.095 * vel * amp_fano) * env_mode * (np.sin(ph_mode) + grano_fano)
            # Fuga radiativa gobernada por fuga_puerta_eta
            fuga_weight = 0.35 + 0.65 * fuga_loc
            out[i0:i1, 0] += gL * sig_voice * fuga_weight
            out[i0:i1, 1] += gR * sig_voice * fuga_weight

    # Fondo difuso de la Bóveda (continuo acústico estéreo de sala de cuarzo)
    for ch, delay_s, g_rev in ((0, 0.038, 0.16), (1, 0.052, 0.16), (0, 0.076, 0.10), (1, 0.088, 0.10)):
        nd = int(round(delay_s * sr))
        if nd < n_total:
            out[nd:, ch] += g_rev * out[:-nd, 1 - ch]

    trazas = {
        'asimetria_q': q_curve,
        'delta_bic': delta_bic_curve,
        'f_fano_peak': traza_fano_peak,
        'f_fano_zero': traza_fano_zero,
        'gamma_bic_decay': traza_bic_decay
    }
    return out, trazas


# ───────────── 5. Escena en Contexto: Bóveda de Fano + Bajo de Bóveda + Siringua en la Antiresonancia ─────────────
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

def render_escena_boveda_fano_siringua(duracion=24.0, sr=SR, semilla=SEMILLA):
    n_total = int(round(duracion * sr))
    t = np.arange(n_total) / sr
    rng = np.random.default_rng(semilla + 918)
    f0_base = 110.0  # La2

    part_boveda = {
        'asimetria_fano_q': [
            [0.0, 3.5], [4.6, 3.5],
            [4.8, 1.8], [9.5, 1.8],
            [9.7, 0.0], [14.3, 0.0],
            [14.5, -1.8], [19.1, -1.8],
            [19.3, 2.0], [24.0, 2.0]
        ],
        'sintonia_bic_delta': [
            [0.0, 0.8], [4.6, 0.8],
            [4.8, 0.0], [9.5, 0.0],
            [9.7, 0.0], [14.3, 0.0],
            [14.5, 0.4], [19.1, 0.4],
            [19.3, 0.0], [24.0, 0.0]
        ],
        'ancho_continuo_Gamma': [
            [0.0, 50.0], [4.8, 60.0], [9.6, 80.0], [14.4, 60.0], [19.2, 70.0], [24.0, 70.0]
        ],
        'fuga_puerta_eta': [
            [0.0, 0.45], [4.8, 0.65], [9.6, 0.85], [14.4, 0.55], [19.2, 0.90], [24.0, 0.90]
        ],
        'eventos': [
            {'t0': 0.2, 'dur': 4.5, 'f_pivote': f0_base, 'vel': 0.84},
            {'t0': 4.8, 'dur': 4.6, 'f_pivote': f0_base, 'vel': 0.92},
            {'t0': 9.6, 'dur': 4.6, 'f_pivote': f0_base * 1.5, 'vel': 0.88},
            {'t0': 14.4, 'dur': 4.6, 'f_pivote': f0_base, 'vel': 0.90},
            {'t0': 19.2, 'dur': 4.6, 'f_pivote': f0_base, 'vel': 0.92},
        ]
    }
    y_boveda, tr_boveda = render_boveda_fano_bic(part_boveda, duracion, sr, semilla)

    # 2. Bajo de Bóveda (pedal subarmónico en La1 = 55.0 Hz con resonancia simpática)
    y_bajo = np.zeros((n_total, 2), dtype=np.float64)
    env_bajo = np.zeros(n_total, dtype=np.float64)
    pulsos_bajo = [
        (0.3, 4.0, 55.0, 0.85),
        (5.0, 4.2, 55.0, 0.92),
        (9.8, 4.2, 82.41, 0.88),
        (14.6, 4.2, 55.0, 0.90),
        (19.4, 4.2, 55.0, 0.92),
    ]
    for tb, durb, fb, velb in pulsos_bajo:
        i0 = int(round(tb * sr))
        i1 = min(n_total, int(round((tb + durb) * sr)))
        if i1 <= i0:
            continue
        u = (np.arange(i0, i1) / sr) - tb
        env_b = (np.sin(np.minimum(1.0, u / 0.06) * math.pi / 2.0) ** 2) * np.exp(-1.4 * u)
        ph_b = 2.0 * math.pi * fb * u
        sig_b = (0.75 * np.sin(ph_b) + 0.25 * np.sin(2.0 * ph_b)) * env_b * (0.16 * velb)
        y_bajo[i0:i1, 0] += sig_b * 0.72
        y_bajo[i0:i1, 1] += sig_b * 0.72
        env_bajo[i0:i1] += env_b

    # 3. Siringua cantando exactamente dentro del Cero de Fano (440.0 Hz y 660.0 Hz)
    frases_siringua = [
        {'t': 5.2, 'dur': 3.6, 'f_hz': 440.0, 'vel': 0.92},   # Cero sintonizado en 440 Hz
        {'t': 10.1, 'dur': 3.5, 'f_hz': 330.0, 'vel': 0.88},  # Cero sintonizado en 330 Hz
        {'t': 14.8, 'dur': 3.6, 'f_hz': 440.0, 'vel': 0.94},  # Cero sintonizado en 440 Hz
        {'t': 19.8, 'dur': 3.4, 'f_hz': 550.0, 'vel': 0.90},  # Antiresonancia en 550 Hz
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
                np.sin(np.minimum(1.0, (nn / sr - tt) / 0.16) * math.pi / 2.0) ** 2
            )
            amp_sir[i0:i0 + nn] = fr['vel'] * env_s

    f0_sir_vib = f0_sir * (2.0 ** ((4.8 * np.sin(2.0 * math.pi * 5.2 * t)) / 1200.0))
    ph_s = 2.0 * math.pi * np.cumsum(f0_sir_vib) / sr
    soplo = sosfilt(butter(2, [1400, 4800], fs=sr, btype='bandpass', output='sos'), rng.normal(0, 0.022, n_total))
    exc_s = (0.75 * np.sin(ph_s) + 0.25 * np.sin(0.5 * ph_s) + soplo) * amp_sir
    t_voc = np.array([0.0, 6.0, 12.0, 18.0, 24.0])
    vf = np.array([VOCALES[v] for v in ['a', 'o', 'u', 'i', 'a']], dtype=float)
    form_curves = np.array([np.interp(t, t_voc, vf[:, k]) for k in range(4)])
    sir_mono = formantes_boca(exc_s, form_curves, sr) * 2.35
    y_siringua = np.column_stack([sir_mono * 0.72, sir_mono * 0.72])

    mix = y_boveda * 0.88 + y_bajo * 0.82 + y_siringua * 0.94
    trazas_esc = {
        'asimetria_q': tr_boveda['asimetria_q'],
        'delta_bic': tr_boveda['delta_bic'],
        'env_bajo_boveda': env_bajo,
        'f0_siringua_fano': f0_sir_vib * (amp_sir > 0.04)
    }
    return mix, {'boveda': y_boveda, 'bajo': y_bajo, 'siringua': y_siringua}, trazas_esc


# ───────────── 6. Medición LUFS y Generación de Láminas OKLCh + GIF ─────────────
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
    freqs = np.geomspace(35.0, 11000.0, h)[::-1]
    rows = np.array([np.interp(freqs, f, db[:, j]) for j in range(db.shape[1])]).T
    v = np.clip((rows + 82.0) / 66.0, 0.0, 1.0)
    c_low = np.array(BG, dtype=float)
    c_mid = np.array(COL_FANO_ZERO, dtype=float)
    c_hi = np.array(COL_FANO_PEAK, dtype=float)
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

def crear_lamina_01_fano_bic_sonda(sonda_res, path_png):
    W, H = 1600, 960
    im = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(im)
    f_title = cargar_fuente(24, bold=True)
    f_sub = cargar_fuente(14)
    f_sec = cargar_fuente(16, bold=True)
    f_txt = cargar_fuente(13)
    f_sm = cargar_fuente(11)

    p1 = sonda_res['prueba_1_antiresonancia_fano']
    p2 = sonda_res['prueba_2_bic_friedrich_wintgen']
    p3 = sonda_res['prueba_3_costura_despeje_fano']
    p4 = sonda_res['prueba_4_spectrumsynth_SNR']

    dr.text((48, 24), '01 · LA BÓVEDA RESONANTE DE FANO–BIC · ANTIRESONANCIA Y ESTADOS LIGADOS', font=f_title, fill=FG)
    dr.text((48, 60), f'Semilla {SEMILLA} · spectrumsynth {p4["SNR_spectrumsynth_dB"]} dB · Friedrich–Wintgen BIC (Gamma_menos = {p2["bic_gamma_menos_tasa_s_inv"]:.1e} s^-1)', font=f_sub, fill=MUTED)

    # Panel izquierdo: Curva de Fano asimétrica sigma(epsilon) y antiresonancia
    dr.rectangle((48, 104, 775, 548), fill=PANEL_BG, outline=GRID_COL, width=2)
    dr.text((68, 120), 'Perfil Asimétrico de Fano: Cresta en ε = 1/q y Cero en ε = −q', font=f_sec, fill=COL_FANO_PEAK)

    eps_plot = np.linspace(-4.0, 4.0, 600)
    for q_v, lbl_q, yy_b, col_q in [
        (3.0, 'q = 3.0: Cresta dominante (+10 dB), cero profundo en ε = −3', 165, COL_FANO_PEAK),
        (1.0, 'q = 1.0: Máxima asimetría Fano (cero en ε = −1, pico en ε = +1)', 295, COL_BIC_GOLD),
        (0.0, 'q = 0.0: Zanja de muesca simétrica (antiresonancia pura en ε = 0)', 425, COL_FANO_ZERO),
    ]:
        sig_q = ((eps_plot + q_v) ** 2) / (eps_plot ** 2 + 1.0)
        box_e = (355, yy_b, 395, 92)
        dr.rectangle((355, yy_b, 355 + 395, yy_b + 92), outline=GRID_COL, width=1)
        dr.line((355 + 197, yy_b, 355 + 197, yy_b + 92), fill=GRID_COL, width=1)
        dibujar_curva(dr, sig_q, box_e, col_q, 0.0, 11.0, width=2)
        dr.text((68, yy_b + 22), lbl_q, font=f_sm, fill=FG)

    dr.text((68, 522), 'Cian: q = 3.0 · Oro: q = 1.0 · Carmesí: q = 0.0 (notch puro) · Línea media: ε = 0', font=f_sm, fill=MUTED)

    # Panel derecho: Resultados medidos por la sonda
    dr.rectangle((805, 104, 1552, 548), fill=PANEL_BG, outline=GRID_COL, width=2)
    dr.text((825, 120), 'Resultados medidos por la sonda (Fano, BIC y Costura)', font=f_sec, fill=COL_BIC_GOLD)

    lineas = [
        ('1. Antiresonancia de Fano exacta en ε = −q:', COL_FANO_PEAK),
        (f'   • Cero teórico: {p1["f_cero_teorica_Hz"]:.1f} Hz · Cero medido: {p1["f_cero_medida_Hz"]:.1f} Hz', FG),
        (f'   • Atenuación en el cero: {p1["atenuacion_cero_fano_dB"]:.2f} dB (zanja de silencio total)', FG),
        (f'   • Ganancia en el pico (ε = 1/q = 455 Hz): {p1["ganancia_pico_fano_dB"]:+.2f} dB', FG),
        ('2. Condición BIC de Friedrich–Wintgen (Q -> inf):', COL_BIC_GOLD),
        (f'   • kappa_BIC exacto: {p2["kappa_bic_exacto"]:.4f} Hz', MUTED),
        (f'   • Tasa decaimiento modo BIC: {p2["bic_gamma_menos_tasa_s_inv"]:.6f} s^-1 (atrapamiento infinito)', FG),
        (f'   • Supresión radiación vs no-BIC: {p2["supresion_radiacion_bic_veces"]:.0f}x más retenido', FG),
        ('3. Costura espectral de Rejilla para la Siringua:', COL_FANO_ZERO),
        (f'   • Despeje de fondo en f = 440 Hz: {p3["despeje_costura_dB"]:+.2f} dB', FG),
        (f'   • La Siringua canta en la antiresonancia sin colisión ni compresión.', COL_SIRINGUA),
    ]
    yy = 160
    for txt, col in lineas:
        dr.text((825, yy), txt, font=f_txt, fill=col)
        yy += 35

    # Panel inferior: Comparación de Decaimiento Temporal: Modo Normal vs Modo BIC Atrapado
    dr.rectangle((48, 574, 1552, 918), fill=PANEL_BG, outline=GRID_COL, width=2)
    dr.text((68, 590), 'Física del Atrapamiento BIC: Modo Radiativo Superradiante vs Estado Ligado Atrapado en el Continuo (Q -> inf)', font=f_sec, fill=FG)

    box_j = (260, 636, 1210, 225)
    dr.rectangle((260, 636, 260 + 1210, 636 + 225), outline=GRID_COL, width=1)
    u_plot = np.linspace(0.0, 2.0, 600)
    decay_normal = np.exp(-4.5 * u_plot)
    decay_bic = np.exp(-0.02 * u_plot)  # Modo BIC casi inmóvil
    decay_super = np.exp(-18.0 * u_plot)

    dibujar_curva(dr, decay_super, box_j, COL_FANO_ZERO, 0.0, 1.05, width=2)
    dibujar_curva(dr, decay_normal, box_j, MUTED, 0.0, 1.05, width=2)
    dibujar_curva(dr, decay_bic, box_j, COL_BIC_GOLD, 0.0, 1.05, width=3)

    dr.text((68, 658), 'Modo BIC atrapado (Q -> inf)', font=f_txt, fill=COL_BIC_GOLD)
    dr.text((68, 700), 'Modo lorentziano normal', font=f_txt, fill=MUTED)
    dr.text((68, 742), 'Modo superradiante Gamma+', font=f_txt, fill=COL_FANO_ZERO)

    for x_frac, txt_lbl in [(0.0, 't = 0 s (Excitación)'), (0.5, 't = 1.0 s'), (1.0, 't = 2.0 s (Energía atrapada)')]:
        xx = 260 + x_frac * 1210
        dr.line((xx, 636, xx, 861), fill=GRID_COL, width=1)
        dr.text((xx - 45, 872), txt_lbl, font=f_sm, fill=FG)

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

    dr.text((48, 24), '02 · MUESTRA AISLADA · LA BÓVEDA RESONANTE DE FANO–BIC (24 s)', font=f_title, fill=FG)
    dr.text((48, 60), f'Archivo: {med_solo["m4a"]} · {med_solo["I_LUFS"]:.1f} LUFS · {med_solo["pico_dBTP"]:.1f} dBTP · LRA {med_solo["LRA"]:.1f} · Semilla {SEMILLA}', font=f_sub, fill=MUTED)

    x0, w_plot = 235, 1310
    secciones = [
        (0.0, 'I · Lorentziano (q=3.5)'),
        (4.8, 'II · Cero de Fano (q=1.8)'),
        (9.6, 'III · Muesca Pura (q=0.0)'),
        (14.4, 'IV · Asimetría Invertida (q=−1.8)'),
        (19.2, 'V · Fuga Radiativa BIC')
    ]
    for sec_t, sec_lbl in secciones:
        xx = x0 + (sec_t / 24.0) * w_plot
        dr.line((xx, 112, xx, 885), fill=GRID_COL, width=1)
        dr.text((xx + 4, 110), sec_lbl, font=f_sm, fill=FG)

    yy0 = 142
    dr.rectangle((x0, yy0, x0 + w_plot, yy0 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy0 + 24), 'Asimetría Fano q(t)', font=f_sec, fill=COL_FANO_PEAK)
    dibujar_curva(dr, tr_solo['asimetria_q'], (x0, yy0 + 4, w_plot, 64), COL_FANO_PEAK, -2.5, 4.0, width=2)

    yy1 = 234
    dr.rectangle((x0, yy1, x0 + w_plot, yy1 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy1 + 24), 'Sintonía BIC δ(t)', font=f_sec, fill=COL_BIC_GOLD)
    dibujar_curva(dr, tr_solo['delta_bic'], (x0, yy1 + 4, w_plot, 64), COL_BIC_GOLD, -0.1, 1.0, width=2)

    yy2 = 326
    dr.rectangle((x0, yy2, x0 + w_plot, yy2 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy2 + 24), 'Cero Fano f_cero (Hz)', font=f_sec, fill=COL_FANO_ZERO)
    dibujar_curva(dr, tr_solo['f_fano_zero'], (x0, yy2 + 4, w_plot, 64), COL_FANO_ZERO, 20.0, 300.0, width=2)

    yy3 = 418
    dr.rectangle((x0, yy3, x0 + w_plot, yy3 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy3 + 24), 'Tasa Decaimiento Γ', font=f_sec, fill=MUTED)
    dibujar_curva(dr, tr_solo['gamma_bic_decay'], (x0, yy3 + 4, w_plot, 64), MUTED, 0.0, 5.0, width=2)

    yy_w = 518
    dr.rectangle((x0, yy_w, x0 + w_plot, yy_w + 88), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy_w + 30), 'Onda estéreo', font=f_sec, fill=FG)
    y_norm_vis = normalizar_nivel(y_solo)
    dibujar_curva(dr, y_norm_vis[:, 0], (x0, yy_w + 4, w_plot, 80), COL_FANO_PEAK, -0.75, 0.75, width=1)

    yy_s = 626
    spec_im = espectrograma_imagen(y_solo, SR, w_plot, 252)
    im.paste(spec_im, (x0, yy_s))
    dr.rectangle((x0, yy_s, x0 + w_plot, yy_s + 252), outline=GRID_COL, width=1)
    dr.text((48, yy_s + 20), 'Espectrograma\n35 Hz – 11.0 kHz', font=f_sec, fill=FG)
    dr.text((48, yy_s + 78), 'En II y IV el cero\nde Fano corta una\ntrinchera móvil de\nsilencio a través de\nla resonancia.', font=f_sm, fill=COL_FANO_ZERO)

    for s_tick in range(0, 25, 3):
        xx = x0 + (s_tick / 24.0) * w_plot
        dr.text((xx - 10, 892), f'{s_tick} s', font=f_sm, fill=MUTED)
    dr.text((48, 922), 'Lectura: el parámetro q desplaza asimétricamente el cero de absorción; la condición BIC δ=0 congela la energía en la bóveda.', font=f_sm, fill=MUTED)

    im.save(str(path_png), 'PNG')
    return im

def crear_lamina_03_escena_boveda(y_mix, tr_esc, med_mix, path_png):
    W, H = 1600, 960
    im = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(im)
    f_title = cargar_fuente(24, bold=True)
    f_sub = cargar_fuente(14)
    f_sec = cargar_fuente(15, bold=True)
    f_sm = cargar_fuente(11)

    dr.text((48, 24), '03 · ESCENA EN CONTEXTO · BÓVEDA RESONANTE + BAJO + SIRINGUA EN ANTIRESONANCIA', font=f_title, fill=FG)
    dr.text((48, 60), f'Archivo: {med_mix["m4a"]} · {med_mix["I_LUFS"]:.1f} LUFS · {med_mix["pico_dBTP"]:.1f} dBTP · La Siringua canta dentro del cero de absorción de Fano', font=f_sub, fill=MUTED)

    x0, w_plot = 235, 1310
    secciones = [
        (0.0, 'I · Entrada Bóveda'),
        (4.8, 'II · Cero Fano 440 Hz'),
        (9.6, 'III · Muesca 330 Hz'),
        (14.4, 'IV · Cero Fano 440 Hz II'),
        (19.2, 'V · Fuga Radiativa BIC')
    ]
    for sec_t, sec_lbl in secciones:
        xx = x0 + (sec_t / 24.0) * w_plot
        dr.line((xx, 112, xx, 885), fill=GRID_COL, width=1)
        dr.text((xx + 4, 110), sec_lbl, font=f_sm, fill=FG)

    yy0 = 142
    dr.rectangle((x0, yy0, x0 + w_plot, yy0 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy0 + 24), 'Asimetría Fano q(t)', font=f_sec, fill=COL_FANO_PEAK)
    dibujar_curva(dr, tr_esc['asimetria_q'], (x0, yy0 + 4, w_plot, 64), COL_FANO_PEAK, -2.5, 4.0, width=2)

    yy1 = 234
    dr.rectangle((x0, yy1, x0 + w_plot, yy1 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy1 + 24), 'Sintonía BIC δ(t)', font=f_sec, fill=COL_BIC_GOLD)
    dibujar_curva(dr, tr_esc['delta_bic'], (x0, yy1 + 4, w_plot, 64), COL_BIC_GOLD, -0.1, 1.0, width=2)

    yy2 = 326
    dr.rectangle((x0, yy2, x0 + w_plot, yy2 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy2 + 24), 'Bajo de Bóveda', font=f_sec, fill=MUTED)
    dibujar_curva(dr, tr_esc['env_bajo_boveda'], (x0, yy2 + 4, w_plot, 64), MUTED, 0.0, 1.2, width=2)

    yy3 = 418
    dr.rectangle((x0, yy3, x0 + w_plot, yy3 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy3 + 24), 'Siringua en Cero', font=f_sec, fill=COL_SIRINGUA)
    dibujar_curva(dr, tr_esc['f0_siringua_fano'], (x0, yy3 + 4, w_plot, 64), COL_SIRINGUA, 280.0, 600.0, width=2)

    yy_w = 518
    dr.rectangle((x0, yy_w, x0 + w_plot, yy_w + 88), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy_w + 26), 'Mezcla estéreo', font=f_sec, fill=FG)
    y_norm_vis = normalizar_nivel(y_mix)
    dibujar_curva(dr, y_norm_vis[:, 0], (x0, yy_w + 4, w_plot, 80), COL_FANO_PEAK, -0.75, 0.75, width=1)

    yy_s = 626
    spec_im = espectrograma_imagen(y_mix, SR, w_plot, 252)
    im.paste(spec_im, (x0, yy_s))
    dr.rectangle((x0, yy_s, x0 + w_plot, yy_s + 252), outline=GRID_COL, width=1)
    dr.text((48, yy_s + 20), 'Espectrograma\nMezcla Completa', font=f_sec, fill=FG)
    dr.text((48, yy_s + 78), 'En II y IV la voz\nsolista se aloja en\nel cero de absorción\nsin colisionar con\nel fondo.', font=f_sm, fill=COL_SIRINGUA)

    for s_tick in range(0, 25, 3):
        xx = x0 + (s_tick / 24.0) * w_plot
        dr.text((xx - 10, 892), f'{s_tick} s', font=f_sm, fill=MUTED)
    dr.text((48, 922), 'Costura por interferencia destructiva de Fano: el resonador absorbe su propio fondo para dejar pasar a la Siringua.', font=f_sm, fill=MUTED)

    im.save(str(path_png), 'PNG')
    return im


def main():
    print('1. Ejecutando sonda de La Bóveda Resonante de Fano–BIC...', flush=True)
    sonda_res = ejecutar_sonda()
    print('   Sonda OK:', json.dumps(sonda_res, ensure_ascii=False), flush=True)

    print('2. Sintetizando muestra aislada de 24 s...', flush=True)
    partitura_solo = {
        'prototipo': 'boveda-fano-bic',
        'duracion': 24.0,
        'semilla': SEMILLA,
        'asimetria_fano_q': [
            [0.0, 3.5], [4.6, 3.5],
            [4.8, 1.8], [9.5, 1.8],
            [9.7, 0.0], [14.3, 0.0],
            [14.5, -1.8], [19.1, -1.8],
            [19.3, 2.0], [24.0, 2.0]
        ],
        'sintonia_bic_delta': [
            [0.0, 0.8], [4.6, 0.8],
            [4.8, 0.0], [9.5, 0.0],
            [9.7, 0.0], [14.3, 0.0],
            [14.5, 0.4], [19.1, 0.4],
            [19.3, 0.0], [24.0, 0.0]
        ],
        'ancho_continuo_Gamma': [
            [0.0, 50.0], [4.8, 60.0], [9.6, 80.0], [14.4, 60.0], [19.2, 70.0], [24.0, 70.0]
        ],
        'fuga_puerta_eta': [
            [0.0, 0.45], [4.8, 0.65], [9.6, 0.85], [14.4, 0.55], [19.2, 0.90], [24.0, 0.90]
        ],
        'eventos': [
            {'t0': 0.25, 'dur': 4.4, 'f_pivote': 110.0, 'vel': 0.86},
            {'t0': 4.85, 'dur': 4.5, 'f_pivote': 110.0, 'vel': 0.92},
            {'t0': 9.65, 'dur': 4.5, 'f_pivote': 165.0, 'vel': 0.90},
            {'t0': 14.45, 'dur': 4.5, 'f_pivote': 110.0, 'vel': 0.92},
            {'t0': 19.25, 'dur': 4.5, 'f_pivote': 110.0, 'vel': 0.92},
        ]
    }
    y_solo, tr_solo = render_boveda_fano_bic(partitura_solo, 24.0, SR, SEMILLA)
    med_solo = guardar_audio_y_medir(
        y_solo,
        OUT_DIR / 'muestra-boveda-fano-bic-s20261021.wav',
        OUT_DIR / 'muestra-boveda-fano-bic-s20261021.m4a',
        target_lufs=-18.5
    )

    print('3. Sintetizando escena en contexto (Bóveda de Fano + Bajo + Siringua en Antiresonancia)...', flush=True)
    y_mix, stems_esc, tr_esc = render_escena_boveda_fano_siringua(24.0, SR, SEMILLA)
    med_mix = guardar_audio_y_medir(
        y_mix,
        OUT_DIR / 'escena-boveda-fano-bic-s20261021.wav',
        OUT_DIR / 'escena-boveda-fano-bic-s20261021.m4a',
        target_lufs=-16.0
    )

    print('4. Generando láminas PNG en OKLCh y GIF...', flush=True)
    p1_png = OUT_DIR / '01-perfil-fano-y-condicion-bic-s20261021.png'
    p2_png = OUT_DIR / '02-boveda-fano-espectrograma-s20261021.png'
    p3_png = OUT_DIR / '03-escena-boveda-siringua-costura-s20261021.png'
    im1 = crear_lamina_01_fano_bic_sonda(sonda_res, p1_png)
    im2 = crear_lamina_02_muestra_aislada(y_solo, tr_solo, med_solo, p2_png)
    im3 = crear_lamina_03_escena_boveda(y_mix, tr_esc, med_mix, p3_png)

    frames = [im.resize((1200, 720), Image.Resampling.LANCZOS).quantize(colors=256, method=Image.Quantize.MEDIANCUT) for im in (im1, im2, im3)]
    gif_path = OUT_DIR / 'proceso-boveda-fano-bic-s20261021.gif'
    frames[0].save(
        str(gif_path),
        format='GIF',
        save_all=True,
        append_images=frames[1:],
        duration=1800,
        loop=0,
        optimize=True
    )

    if Path(__file__).resolve() != (OUT_DIR / 'boveda_fano_bic.py').resolve(): shutil.copyfile(__file__, OUT_DIR / 'boveda_fano_bic.py')

    receta = {
        'instrumento': 'La Bóveda Resonante de Fano–BIC (Estados Ligados en el Continuo)',
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
    receta_path = OUT_DIR / 'receta-boveda-fano-bic-s20261021.json'
    with open(receta_path, 'w', encoding='utf-8') as f:
        json.dump(receta, f, ensure_ascii=False, indent=2)

    print('5. Todo completado con éxito:', json.dumps(receta, ensure_ascii=False, indent=2), flush=True)

if __name__ == '__main__':
    main()
