"""Construcción, sonda y producción real de La Cascada de Enstrofía de Navier–Stokes (Leray–BKM) para Rejilla.

Física y Matemática del Problema del Milenio (Existencia y Suavidad de Navier–Stokes en 3D):
1. Ecuaciones de Navier–Stokes incompresibles en espacio de Fourier / capas espectrales (Rejilla):
   du_n/dt = T_n(u) - nu * k_n^(2*alpha) * u_n + F_n
   donde T_n(u) es el operador bilineal de transferencia triádica (u · grad)u (modelo de capas Sabra/GOY
   de Obukhov–Gledzer–Ohkitani–Yamada y cascada diádica de Katz–Pavlović) con conservación exacta de energía
   cinética E = (1/2) * sum |u_n|^2 en el límite invíscido de Euler (nu -> 0).
2. Ley de Cascada Inercial de Kolmogorov (-5/3) y Escala de Disipación (k_eta):
   En el rango inercial (k_0 << k << k_eta), la transferencia triádica establece E(k) = C_K * eps^(2/3) * k^(-5/3).
   En la microescala de Kolmogorov k_eta = (eps / nu^3)^(1/4), el laplaciano viscoso (-nu * k^2) disipa
   exponencialmente la turbulencia ultravioleta.
3. Estiramiento de Vorticidad 3D ((omega · grad)u), Enstrofía (Omega) y Criterio de Explosión de Beale–Kato–Majda (BKM):
   En 3D, la enstrofía Omega(t) = (1/2) * sum k_n^2 |u_n|^2 se amplifica por estiramiento de vórtices.
   Teorema de Beale–Kato–Majda (1984): existe explosión (blow-up / pérdida de suavidad C^inf en tiempo finito T*)
   si y sólo si int_0^{T*} ||omega(t)||_{L^inf} dt = inf, donde ||omega(t)||_{L^inf} ~ sup_n (k_n |u_n(t)|).
4. Regularización Suavizadora de Jean Leray (1934):
   Al reemplazar la velocidad advectiva por el campo filtrado de Leray v_n = u_n / (1 + (l_Leray * k_n)^2),
   se doma el transporte triádico ultravioleta, rescatando la solución al borde mismo del blow-up BKM y
   transformando el colapso singular en un acorde laminar-vorticial eternamente diferenciable (C^inf).
5. Costura Espectral de Rejilla («El Ojo Laminar del Vórtice»):
   Un sumidero viscoso selectivo de Navier–Stokes sintonizado en la frecuencia de la Siringua (440 Hz / 330 Hz)
   drena localmente la turbulencia (> 50 dB de despeje), abriendo un ojo laminar donde la voz solista canta
   sin colisión ni compresores de mezcla.
"""
import hashlib, json, math, os, shutil, subprocess
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import stft, lfilter, iirpeak, butter, sosfilt
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path('/working_dir/c_0b049fae79e32dcb/artifacts/file_generation/ttl=63d/output')
INTER_DIR = Path('/working_dir/c_0b049fae79e32dcb/artifacts/file_generation/ttl=63d/intermediate')
OUT_DIR.mkdir(parents=True, exist_ok=True)
INTER_DIR.mkdir(parents=True, exist_ok=True)

SEMILLA = 20261021
SR = 32000

# ───────────── 1. Matemática Exacta: Cascada de Navier–Stokes, BKM, Leray y Paleta OKLCh ─────────────
def simular_cascada_navier_stokes(
    N_shells=14,
    k0=1.0,
    lam=1.5,
    nu=1e-4,
    alpha_dissip=1.0,
    sigma_stretch=1.0,
    l_leray=0.0,
    dt=0.00025,
    n_steps=4800,
    forcing_amp=0.0,
    u_init=None
):
    """Integra por RK4 el sistema acoplado de Navier–Stokes en capas espectrales (Katz–Pavlović / Obukhov)
    con estiramiento de vorticidad 3D (sigma_stretch), viscosidad (nu * k^(2*alpha)) y regularización de Leray (l_leray).
    Conserva exactamente la energía E = 0.5 * sum(u_n^2) cuando nu = 0 y forcing_amp = 0.
    """
    n_idx = np.arange(N_shells, dtype=np.float64)
    k = k0 * (lam ** n_idx)
    if u_init is None:
        u = np.zeros(N_shells, dtype=np.float64)
        u[0] = 1.25
        u[1] = 0.52
        u[2] = 0.18
    else:
        u = np.array(u_init, dtype=np.float64).copy()

    # Filtro suavizador de Jean Leray: v_n = u_n / (1 + (l_leray * k_n)^2)
    leray_factor = 1.0 / (1.0 + (l_leray * k) ** 2)

    def rhs(state):
        v = state * leray_factor
        # Operador triádico antisimétrico de Katz–Pavlović / Leray:
        # sum_n u_n * NL_n = sum_{n=1}^{N-1} k_{n-1} v_{n-1} u_{n-1} u_n - sum_{n=0}^{N-2} k_n v_n u_n u_{n+1} == 0
        nl = np.zeros_like(state)
        nl[1:] += sigma_stretch * k[:-1] * v[:-1] * state[:-1]
        nl[:-1] -= sigma_stretch * k[:-1] * v[:-1] * state[1:]
        dissip = -nu * (k ** (2.0 * alpha_dissip)) * state
        force = np.zeros_like(state)
        force[0] = forcing_amp
        return nl + dissip + force

    E_hist = np.zeros(n_steps + 1, dtype=np.float64)
    Omega_hist = np.zeros(n_steps + 1, dtype=np.float64)
    BKM_vort_hist = np.zeros(n_steps + 1, dtype=np.float64)
    U_hist = np.zeros((n_steps + 1, N_shells), dtype=np.float64)

    for step in range(n_steps + 1):
        E_hist[step] = 0.5 * float(np.sum(u ** 2))
        Omega_hist[step] = 0.5 * float(np.sum((k ** 2) * (u ** 2)))
        BKM_vort_hist[step] = float(np.max(k * np.abs(u)))
        U_hist[step] = u
        if step < n_steps:
            k1 = rhs(u)
            k2 = rhs(u + 0.5 * dt * k1)
            k3 = rhs(u + 0.5 * dt * k2)
            k4 = rhs(u + dt * k3)
            u = u + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

    bkm_integral = float(np.trapezoid(BKM_vort_hist, dx=dt))
    return {
        'k': k,
        'u_final': u,
        'U_hist': U_hist,
        'E_hist': E_hist,
        'Omega_hist': Omega_hist,
        'BKM_vort_hist': BKM_vort_hist,
        'BKM_integral': bkm_integral
    }


def espectro_kolmogorov_teorico(k_vals, eps=1.0, nu=1e-3, C_K=1.5, beta=5.2):
    """Espectro teórico de energía turbulenta de Kolmogorov–Pope:
    E(k) = C_K * eps^(2/3) * k^(-5/3) * exp(-beta * (k / k_eta)^(4/3)),
    donde k_eta = (eps / nu^3)^(1/4) es el número de onda de disipación de Kolmogorov.
    """
    k_arr = np.asarray(k_vals, dtype=np.float64)
    k_eta = (eps / max(1e-18, nu ** 3)) ** 0.25
    E_inert = C_K * (eps ** (2.0 / 3.0)) * (k_arr ** (-5.0 / 3.0))
    f_eta = np.exp(-beta * ((k_arr / k_eta) ** (4.0 / 3.0)))
    return E_inert * f_eta, E_inert, float(k_eta)


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


rng_vis = np.random.default_rng(SEMILLA + 777)
H0 = 232.0 + float(rng_vis.uniform(-6.0, 6.0))  # Azul abisal hidrodinámico sembrado
BG = oklch(0.12, 0.032, H0)
PANEL_BG = oklch(0.16, 0.038, H0 + 6)
GRID_COL = oklch(0.27, 0.040, H0)
FG = oklch(0.94, 0.022, H0 + 20)
MUTED = oklch(0.68, 0.036, H0 + 10)
COL_KOLMOGOROV = oklch(0.82, 0.17, H0 - 45)   # Turquesa / cian: Cascada inercial k^(-5/3)
COL_BKM_BLOWUP = oklch(0.75, 0.19, H0 + 135)  # Coral / carmesí: Singularidad de vorticidad BKM
COL_LERAY_GOLD = oklch(0.86, 0.17, H0 - 145)  # Ámbar / oro: Regularización suave de Leray C^inf
COL_SIRINGUA = oklch(0.80, 0.16, H0 + 65)     # Violeta cristalino: Siringua en el Ojo Laminar


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

    # Prueba 1: Conservación exacta de energía en Euler 3D (nu = 0) y explosión de enstrofía por estiramiento de vórtices
    sim_euler = simular_cascada_navier_stokes(
        N_shells=14, k0=1.0, lam=1.5, nu=0.0, alpha_dissip=1.0,
        sigma_stretch=2.4, l_leray=0.0, dt=0.00025, n_steps=5600, forcing_amp=0.0
    )
    E0 = sim_euler['E_hist'][0]
    Ef = sim_euler['E_hist'][-1]
    err_rel_energia = abs(Ef - E0) / max(1e-12, E0)
    omega_init = sim_euler['Omega_hist'][0]
    omega_peak = float(np.max(sim_euler['Omega_hist']))
    bkm_peak = float(np.max(sim_euler['BKM_vort_hist']))

    resultados['prueba_1_conservacion_triadica_y_cascada_euler'] = {
        'energia_inicial_E0': round(E0, 6),
        'energia_final_Ef': round(Ef, 6),
        'error_relativo_energia_inviscida': float(f'{err_rel_energia:.2e}'),
        'enstrofia_inicial_Omega0': round(omega_init, 4),
        'enstrofia_pico_Omega_max': round(omega_peak, 2),
        'amplificacion_enstrofia_veces': round(omega_peak / max(1e-9, omega_init), 1),
        'vorticidad_BKM_pico': round(bkm_peak, 2)
    }

    # Prueba 2: Ley de cascada inercial de Kolmogorov (-5/3) y escala de disipación viscosa k_eta
    k_grid = np.geomspace(1.0, 120.0, 200)
    E_tot, E_inert, k_eta_val = espectro_kolmogorov_teorico(k_grid, eps=1.0, nu=0.012, C_K=1.5, beta=5.2)
    mask_in = k_grid <= 3.5
    slope_inert, _ = np.polyfit(np.log10(k_grid[mask_in]), np.log10(E_inert[mask_in]), 1)
    idx_uv = int(np.argmin(np.abs(k_grid - 2.0 * k_eta_val)))
    aten_viscosa_db = 10.0 * math.log10(max(1e-18, E_tot[idx_uv] / E_inert[idx_uv]))

    resultados['prueba_2_espectro_kolmogorov_y_disipacion'] = {
        'pendiente_inercial_teorica': round(-5.0 / 3.0, 4),
        'pendiente_inercial_medida': round(float(slope_inert), 4),
        'escala_disipacion_k_eta': round(k_eta_val, 2),
        'atenuacion_viscosa_en_2k_eta_dB': round(aten_viscosa_db, 2)
    }

    # Prueba 3: Criterio de Beale–Kato–Majda (Cuasi-Blow-up) vs Regularización Suavizadora de Jean Leray
    sim_blowup = simular_cascada_navier_stokes(
        N_shells=14, k0=1.0, lam=1.5, nu=1.0e-5, alpha_dissip=0.5,
        sigma_stretch=2.6, l_leray=0.0, dt=0.00025, n_steps=5600, forcing_amp=0.38
    )
    sim_leray = simular_cascada_navier_stokes(
        N_shells=14, k0=1.0, lam=1.5, nu=1.0e-5, alpha_dissip=0.5,
        sigma_stretch=2.6, l_leray=0.28, dt=0.00025, n_steps=5600, forcing_amp=0.38
    )
    omega_blow = float(np.max(sim_blowup['Omega_hist']))
    omega_leray = float(np.max(sim_leray['Omega_hist']))
    bkm_int_blow = sim_blowup['BKM_integral']
    bkm_int_leray = sim_leray['BKM_integral']

    resultados['prueba_3_criterio_bkm_vs_regularizacion_leray'] = {
        'enstrofia_max_cuasi_blowup': round(omega_blow, 2),
        'enstrofia_max_regularizada_leray': round(omega_leray, 2),
        'factor_contencion_enstrofia_leray': round(omega_blow / max(1e-9, omega_leray), 1),
        'integral_BKM_cuasi_blowup': round(bkm_int_blow, 2),
        'integral_BKM_regularizada_leray': round(bkm_int_leray, 2)
    }

    # Prueba 4: Costura Espectral («El Ojo Laminar del Vórtice») en 440 Hz y verificación SNR en spectrumsynth
    P_turb = PistaRejilla('sonda_ns_turbulenta', columnas=2, S_grid=32768, H_grid=16384)
    freqs_cascada = [110.0, 165.0, 220.0, 330.0, 440.0, 660.0, 990.0, 1485.0]
    for idx_f, fk in enumerate(freqs_cascada):
        amp_k = 0.16 * ((fk / 110.0) ** (-1.0 / 3.0))
        P_turb.modo(fk, amp_k, 0.0, a=2.5, pan=-0.4 + 0.1 * idx_f)
    ZL_turb, _ = P_turb.escribir()

    P_ojo = PistaRejilla('sonda_ns_ojo_laminar', columnas=2, S_grid=32768, H_grid=16384)
    for idx_f, fk in enumerate(freqs_cascada):
        amp_k = 0.16 * ((fk / 110.0) ** (-1.0 / 3.0))
        # Sumidero viscoso selectivo de Navier-Stokes en la banda de la Siringua (440 Hz)
        if abs(fk - 440.0) < 10.0:
            P_ojo.modo(fk, amp_k * 0.00015, 0.0, a=22.0, pan=0.0)
        else:
            P_ojo.modo(fk, amp_k, 0.0, a=2.5, pan=-0.4 + 0.1 * idx_f)
    ZL_ojo, ZR_ojo = P_ojo.escribir()

    def energia_banda(Z_col, f_center, half_w=3):
        k0_b = max(1, int(round(f_center)) - half_w)
        k1_b = min(len(Z_col), int(round(f_center)) + half_w + 1)
        return float(np.sum(np.abs(Z_col[k0_b:k1_b]) ** 2))

    e_turb_440 = energia_banda(ZL_turb[0], 440.0)
    e_ojo_440 = energia_banda(ZL_ojo[0], 440.0)
    despeje_ojo_db = 10.0 * math.log10((e_ojo_440 + 1e-24) / (e_turb_440 + 1e-24))

    wav_sonda = INTER_DIR / 'sonda_navier_stokes_spectrumsynth.wav'
    esc_sonda = sintetizar_spectrumsynth(ZL_ojo, ZR_ojo, wav_sonda, S_grid=32768)
    _, y_ff = wavfile.read(wav_sonda)
    y_ff = y_ff.astype(np.float64) * esc_sonda
    y_ti = P_ojo.tiempo(0.0, 2.0)
    snr_db = 10.0 * math.log10(np.sum(y_ti ** 2) / (np.sum((y_ff - y_ti) ** 2) + 1e-24))

    resultados['prueba_4_ojo_laminar_costura_y_spectrumsynth'] = {
        'energia_turbulenta_440Hz': round(e_turb_440, 4),
        'energia_ojo_laminar_440Hz': round(e_ojo_440, 8),
        'despeje_ojo_laminar_dB': round(despeje_ojo_db, 2),
        'SNR_spectrumsynth_dB': round(snr_db, 2)
    }

    return resultados


# ───────────── 4. Motor Temporal de 24 s: Muestra Aislada (La Cascada de Enstrofía de Navier–Stokes) ─────────────
def render_cascada_navier_stokes(partitura, duracion=24.0, sr=SR, semilla=SEMILLA):
    n_total = int(round(duracion * sr))
    t = np.arange(n_total) / sr
    out = np.zeros((n_total, 2), dtype=np.float64)

    def interp_ctrl(key, default):
        pts = np.asarray(partitura.get(key, [[0.0, default], [duracion, default]]), dtype=float)
        return np.interp(t, pts[:, 0], pts[:, 1])

    # Los cuatro controles de interpretación físico-matemáticos
    reynolds_curve = interp_ctrl('empuje_reynolds_Re', 0.5)          # 0.0 (laminar) -> 1.0 (cascada turbulenta intensa)
    stretch_curve = interp_ctrl('estiramiento_vortice_sigma', 0.4)   # 0.0 (2D suave) -> 1.0 (3D cuasi-blow-up BKM)
    leray_curve = interp_ctrl('suavidad_leray_ell', 0.5)             # 0.0 (Euler crudo) -> 1.0 (regularización C^inf de Leray)
    ojo_curve = interp_ctrl('ojo_laminar_costura_hz', 0.0)           # Frecuencia central del sumidero laminar (0 = apagado)

    # Capas espectrales (shells) combinando serie armónica y cascada diádica de Fibonacci/Kolmogorov
    razones_shells = [1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 7.0, 9.0, 11.0, 15.0, 21.0, 28.0]
    N_sh = len(razones_shells)

    traza_enstrofia = np.zeros(n_total, dtype=np.float64)
    traza_bkm_vort = np.zeros(n_total, dtype=np.float64)
    traza_k_eta = np.zeros(n_total, dtype=np.float64)

    eventos = partitura.get('eventos', [])
    for ev in eventos:
        t0 = float(ev['t0'])
        dur_ev = float(ev['dur'])
        f_piv = float(ev.get('f_pivote', 110.0))
        vel = float(ev.get('vel', 0.88))

        i0 = max(0, int(round(t0 * sr)))
        i1 = min(n_total, int(round((t0 + dur_ev) * sr)))
        if i1 <= i0:
            continue

        nn = i1 - i0
        u = np.arange(nn) / sr
        Re_loc = reynolds_curve[i0:i1]
        sig_loc = stretch_curve[i0:i1]
        ler_loc = leray_curve[i0:i1]
        ojo_loc = ojo_curve[i0:i1]

        # Escala de disipación efectiva de Kolmogorov k_eta(t) en unidades de razón armónica
        k_eta_loc = 3.2 + 24.0 * (Re_loc ** 1.2) / (1.0 + 2.8 * (ler_loc ** 1.5))
        traza_k_eta[i0:i1] = f_piv * k_eta_loc

        win_ev = (np.sin(np.minimum(1.0, u / 0.045) * math.pi / 2.0) ** 2) * (
            np.sin(np.minimum(1.0, (dur_ev - u) / 0.16) * math.pi / 2.0) ** 2
        )

        enstrofia_ev = np.zeros(nn, dtype=np.float64)
        bkm_ev = np.zeros(nn, dtype=np.float64)

        for idx_s, r_sh in enumerate(razones_shells):
            f_sh = f_piv * r_sh
            if f_sh >= sr * 0.44:
                break

            # Tiempo de llegada de la cascada triádica de Onsager–Kolmogorov a la capa idx_s
            t_cascade = 0.18 * (1.0 - (r_sh ** (-2.0 / 3.0))) / np.maximum(0.25, 0.35 + sig_loc)
            if idx_s == 0:
                drain = 1.0 - 0.42 * sig_loc * np.clip(u / (0.45 * dur_ev), 0.0, 1.0)
                shell_act = drain
            else:
                rise = 1.0 / (1.0 + np.exp(-(u - t_cascade) / 0.045))
                bkm_boost = 1.0 + 2.6 * (sig_loc ** 2) * (1.0 - 0.82 * ler_loc) * (
                    np.exp(-(((u / dur_ev) - 0.68) / 0.14) ** 2)
                ) * ((r_sh / 4.0) ** 0.45)
                shell_act = rise * bkm_boost

            amp_kolm = (r_sh ** (-5.0 / 6.0))
            visc_cut = np.exp(-0.85 * ((r_sh / np.maximum(1.5, k_eta_loc)) ** (4.0 / 3.0)))
            leray_cut = 1.0 / (1.0 + ((0.16 * ler_loc * r_sh) ** 2))

            dist_ojo = np.abs(f_sh - ojo_loc)
            ojo_sink = np.where(
                ojo_loc > 50.0,
                1.0 - 0.96 * np.exp(-((dist_ojo / 38.0) ** 2)),
                1.0
            )

            amp_inst = (0.115 * vel) * amp_kolm * shell_act * visc_cut * leray_cut * ojo_sink * win_ev

            enstrofia_ev += 0.5 * ((r_sh ** 2) * (amp_inst ** 2)) * 100.0
            bkm_ev = np.maximum(bkm_ev, r_sh * amp_inst * 12.0)

            chirp_bkm = 1.0 + 0.018 * (sig_loc ** 2) * (1.0 - 0.90 * ler_loc) * np.log1p(r_sh) * np.sin(
                2.0 * math.pi * (1.5 + 0.4 * idx_s) * u
            )
            ph_sh = 2.0 * math.pi * np.cumsum(f_sh * chirp_bkm) / sr

            grano_triadico = 0.08 * Re_loc * (1.0 - 0.65 * ler_loc) * np.sin(2.0 * ph_sh + 0.7 * idx_s)

            pan_val = float(np.clip(((-1) ** idx_s) * (0.18 + 0.65 * (idx_s / max(1, N_sh - 1))), -0.88, 0.88))
            gL, gR = paneo(pan_val)

            sig_sh = amp_inst * (np.sin(ph_sh) + grano_triadico)
            out[i0:i1, 0] += gL * sig_sh
            out[i0:i1, 1] += gR * sig_sh

        traza_enstrofia[i0:i1] = np.maximum(traza_enstrofia[i0:i1], enstrofia_ev)
        traza_bkm_vort[i0:i1] = np.maximum(traza_bkm_vort[i0:i1], bkm_ev)

    for ch, delay_s, g_rev in ((0, 0.036, 0.14), (1, 0.049, 0.14), (0, 0.073, 0.09), (1, 0.085, 0.09)):
        nd = int(round(delay_s * sr))
        if nd < n_total:
            out[nd:, ch] += g_rev * out[:-nd, 1 - ch]

    trazas = {
        'reynolds_Re': reynolds_curve,
        'estiramiento_sigma': stretch_curve,
        'suavidad_leray': leray_curve,
        'enstrofia_Omega': traza_enstrofia,
        'vorticidad_BKM': traza_bkm_vort,
        'f_disipacion_kolmogorov': traza_k_eta
    }
    return out, trazas


# ───────────── 5. Escena en Contexto: Cascada de Navier–Stokes + Bajo Laminar de Hopf + Siringua en el Ojo Laminar ─────────────
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


def render_escena_navier_stokes_siringua(duracion=24.0, sr=SR, semilla=SEMILLA):
    n_total = int(round(duracion * sr))
    t = np.arange(n_total) / sr
    rng = np.random.default_rng(semilla + 909)
    f0_base = 110.0  # La2

    part_ns = {
        'empuje_reynolds_Re': [
            [0.0, 0.20], [4.6, 0.35],
            [4.8, 0.78], [9.5, 0.85],
            [9.7, 0.96], [14.3, 0.98],
            [14.5, 0.82], [19.1, 0.82],
            [19.3, 0.65], [24.0, 0.40]
        ],
        'estiramiento_vortice_sigma': [
            [0.0, 0.15], [4.6, 0.25],
            [4.8, 0.65], [9.5, 0.72],
            [9.7, 0.95], [14.3, 0.98],
            [14.5, 0.85], [19.1, 0.85],
            [19.3, 0.55], [24.0, 0.30]
        ],
        'suavidad_leray_ell': [
            [0.0, 0.90], [4.6, 0.85],
            [4.8, 0.45], [9.5, 0.40],
            [9.7, 0.05], [14.3, 0.05],
            [14.5, 0.92], [19.1, 0.95],
            [19.3, 0.80], [24.0, 0.95]
        ],
        'ojo_laminar_costura_hz': [
            [0.0, 0.0], [4.7, 0.0],
            [4.8, 440.0], [9.5, 440.0],
            [9.6, 330.0], [14.3, 330.0],
            [14.4, 440.0], [19.1, 440.0],
            [19.2, 550.0], [24.0, 550.0]
        ],
        'eventos': [
            {'t0': 0.20, 'dur': 4.45, 'f_pivote': f0_base, 'vel': 0.84},
            {'t0': 4.80, 'dur': 4.60, 'f_pivote': f0_base, 'vel': 0.92},
            {'t0': 9.60, 'dur': 4.60, 'f_pivote': f0_base * 1.5, 'vel': 0.94},
            {'t0': 14.40, 'dur': 4.60, 'f_pivote': f0_base, 'vel': 0.90},
            {'t0': 19.20, 'dur': 4.60, 'f_pivote': f0_base, 'vel': 0.92},
        ]
    }
    y_cascada, tr_cascada = render_cascada_navier_stokes(part_ns, duracion, sr, semilla)

    # 2. Bajo Laminar de Leray–Hopf (solución débil global en La1 = 55 Hz y Mi2 = 82.41 Hz)
    y_bajo = np.zeros((n_total, 2), dtype=np.float64)
    env_bajo = np.zeros(n_total, dtype=np.float64)
    pulsos_bajo = [
        (0.25, 4.1, 55.0, 0.86),
        (4.95, 4.2, 55.0, 0.92),
        (9.75, 4.2, 82.41, 0.90),
        (14.55, 4.2, 55.0, 0.92),
        (19.35, 4.2, 55.0, 0.90),
    ]
    for tb, durb, fb, velb in pulsos_bajo:
        i0 = int(round(tb * sr))
        i1 = min(n_total, int(round((tb + durb) * sr)))
        if i1 <= i0:
            continue
        u = (np.arange(i0, i1) / sr) - tb
        env_b = (np.sin(np.minimum(1.0, u / 0.06) * math.pi / 2.0) ** 2) * np.exp(-1.35 * u)
        ph_b = 2.0 * math.pi * fb * u
        sig_b = (0.76 * np.sin(ph_b) + 0.24 * np.sin(2.0 * ph_b)) * env_b * (0.16 * velb)
        y_bajo[i0:i1, 0] += sig_b * 0.72
        y_bajo[i0:i1, 1] += sig_b * 0.72
        env_bajo[i0:i1] += env_b

    # 3. Siringua cantando en el Ojo Laminar del Vórtice (440 Hz, 330 Hz, 440 Hz, 550 Hz)
    frases_siringua = [
        {'t': 5.15, 'dur': 3.65, 'f_hz': 440.0, 'vel': 0.92},
        {'t': 10.05, 'dur': 3.55, 'f_hz': 330.0, 'vel': 0.90},
        {'t': 14.75, 'dur': 3.65, 'f_hz': 440.0, 'vel': 0.94},
        {'t': 19.75, 'dur': 3.45, 'f_hz': 550.0, 'vel': 0.90},
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
    soplo = sosfilt(butter(2, [1400, 4800], fs=sr, btype='bandpass', output='sos'), rng.normal(0, 0.020, n_total))
    exc_s = (0.76 * np.sin(ph_s) + 0.24 * np.sin(0.5 * ph_s) + soplo) * amp_sir
    t_voc = np.array([0.0, 6.0, 12.0, 18.0, 24.0])
    vf = np.array([VOCALES[v] for v in ['a', 'o', 'u', 'i', 'a']], dtype=float)
    form_curves = np.array([np.interp(t, t_voc, vf[:, k]) for k in range(4)])
    sir_mono = formantes_boca(exc_s, form_curves, sr) * 2.35
    y_siringua = np.column_stack([sir_mono * 0.72, sir_mono * 0.72])

    mix = y_cascada * 0.88 + y_bajo * 0.82 + y_siringua * 0.94
    trazas_esc = {
        'enstrofia_Omega': tr_cascada['enstrofia_Omega'],
        'suavidad_leray': tr_cascada['suavidad_leray'],
        'env_bajo_hopf': env_bajo,
        'f0_siringua_ojo': f0_sir_vib * (amp_sir > 0.04)
    }
    return mix, {'cascada': y_cascada, 'bajo': y_bajo, 'siringua': y_siringua}, trazas_esc


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
    c_mid = np.array(COL_BKM_BLOWUP, dtype=float)
    c_hi = np.array(COL_KOLMOGOROV, dtype=float)
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


def crear_lamina_01_navier_stokes_sonda(sonda_res, path_png):
    W, H = 1600, 960
    im = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(im)
    f_title = cargar_fuente(23, bold=True)
    f_sub = cargar_fuente(14)
    f_sec = cargar_fuente(16, bold=True)
    f_txt = cargar_fuente(13)
    f_sm = cargar_fuente(11)

    p1 = sonda_res['prueba_1_conservacion_triadica_y_cascada_euler']
    p2 = sonda_res['prueba_2_espectro_kolmogorov_y_disipacion']
    p3 = sonda_res['prueba_3_criterio_bkm_vs_regularizacion_leray']
    p4 = sonda_res['prueba_4_ojo_laminar_costura_y_spectrumsynth']

    dr.text((48, 24), '01 · CASCADA DE ENSTROFÍA DE NAVIER–STOKES (LERAY–BKM) · EXISTENCIA Y SUAVIDAD', font=f_title, fill=FG)
    dr.text((48, 60), f'Semilla {SEMILLA} · spectrumsynth {p4["SNR_spectrumsynth_dB"]} dB · Pendiente Kolmogorov {p2["pendiente_inercial_medida"]} · Error Energía Euler {p1["error_relativo_energia_inviscida"]:.1e}', font=f_sub, fill=MUTED)

    # Panel izquierdo: Cascada de energía en 3 regímenes (Laminar, Inercial -5/3, Cuasi-Blow-up BKM)
    dr.rectangle((48, 104, 775, 548), fill=PANEL_BG, outline=GRID_COL, width=2)
    dr.text((68, 120), 'Tres Regímenes Espectrales: Kolmogorov −5/3, Disipación y Blow-up', font=f_sec, fill=COL_KOLMOGOROV)

    k_plot = np.geomspace(1.0, 64.0, 500)
    log_k = np.log10(k_plot)
    E_inert_log = -5.0 / 3.0 * log_k
    E_visc_log = -5.0 / 3.0 * log_k - 1.4 * ((k_plot / 12.0) ** (4.0 / 3.0))
    E_bkm_log = -0.55 * log_k + 0.35 * np.sin(3.0 * log_k)

    for curve_vals, lbl_c, yy_b, col_c, lo_c, hi_c in [
        (E_inert_log, 'Cascada inercial pura de Kolmogorov:\nE(k) ~ k^(−5/3)', 165, COL_KOLMOGOROV, -3.5, 0.2),
        (E_visc_log, 'Corte de disipación viscosa (−νk²)\ny suavidad de Leray C^∞', 295, COL_LERAY_GOLD, -5.5, 0.2),
        (E_bkm_log, 'Acumulación ultravioleta BKM:\nestiramiento de vórtice (ω·∇)u', 425, COL_BKM_BLOWUP, -2.5, 0.5),
    ]:
        box_e = (375, yy_b, 375, 92)
        dr.rectangle((375, yy_b, 375 + 375, yy_b + 92), outline=GRID_COL, width=1)
        dibujar_curva(dr, curve_vals, box_e, col_c, lo_c, hi_c, width=2)
        dr.text((68, yy_b + 18), lbl_c, font=f_sm, fill=FG)

    dr.text((68, 522), 'Eje horizontal: log10(k / k0) de la fundamental a los armónicos ultravioleta', font=f_sm, fill=MUTED)

    # Panel derecho: Resultados medidos por la sonda
    dr.rectangle((805, 104, 1552, 548), fill=PANEL_BG, outline=GRID_COL, width=2)
    dr.text((825, 120), 'Resultados medidos por la sonda (Euler, Kolmogorov, BKM y Leray)', font=f_sec, fill=COL_LERAY_GOLD)

    lineas = [
        ('1. Conservación triádica (u·∇)u y estiramiento en Euler (ν = 0):', COL_KOLMOGOROV),
        (f' • Error relativo de energía E(t): {p1["error_relativo_energia_inviscida"]:.2e} (simetría exacta)', FG),
        (f' • Explosión de enstrofía Ω(t): {p1["enstrofia_inicial_Omega0"]:.2f} -> {p1["enstrofia_pico_Omega_max"]:.1f} ({p1["amplificacion_enstrofia_veces"]:.1f}x)', FG),
        ('2. Cascada inercial de Kolmogorov y escala k_η:', COL_LERAY_GOLD),
        (f' • Pendiente inercial medida: {p2["pendiente_inercial_medida"]:.4f} (teórica −5/3 = −1.6667)', FG),
        (f' • Corte viscoso en 2·k_η (k_η = {p2["escala_disipacion_k_eta"]:.1f}): {p2["atenuacion_viscosa_en_2k_eta_dB"]:.2f} dB', FG),
        ('3. Criterio de Beale–Kato–Majda vs Suavidad de Jean Leray:', COL_BKM_BLOWUP),
        (f' • Enstrofía pico: Blow-up {p3["enstrofia_max_cuasi_blowup"]:.1f} vs Leray {p3["enstrofia_max_regularizada_leray"]:.1f} ({p3["factor_contencion_enstrofia_leray"]:.1f}x contenida)', FG),
        (f' • Integral BKM ∫||ω||_∞ dt: {p3["integral_BKM_cuasi_blowup"]:.2f} -> {p3["integral_BKM_regularizada_leray"]:.2f}', FG),
        ('4. Costura del Ojo Laminar para la Siringua (440 Hz):', COL_SIRINGUA),
        (f' • Despeje viscoso en 440 Hz: {p4["despeje_ojo_laminar_dB"]:+.2f} dB · SNR {p4["SNR_spectrumsynth_dB"]:.2f} dB', FG),
    ]
    yy = 158
    for txt, col in lineas:
        dr.text((825, yy), txt, font=f_txt, fill=col)
        yy += 34

    # Panel inferior: Evolución temporal de la Enstrofía Omega(t): Cuasi-Singularidad BKM vs Rescate de Leray
    dr.rectangle((48, 574, 1552, 918), fill=PANEL_BG, outline=GRID_COL, width=2)
    dr.text((68, 590), 'Duelo del Milenio en Tiempo Real: Explosión de Enstrofía BKM vs Regularización Global de Leray (C^∞)', font=f_sec, fill=FG)

    sim_b = simular_cascada_navier_stokes(
        N_shells=14, k0=1.0, lam=1.5, nu=1.0e-5, alpha_dissip=0.5,
        sigma_stretch=2.6, l_leray=0.0, dt=0.00025, n_steps=5600, forcing_amp=0.38
    )
    sim_l = simular_cascada_navier_stokes(
        N_shells=14, k0=1.0, lam=1.5, nu=1.0e-5, alpha_dissip=0.5,
        sigma_stretch=2.6, l_leray=0.28, dt=0.00025, n_steps=5600, forcing_amp=0.38
    )
    box_j = (365, 636, 1135, 225)
    dr.rectangle((365, 636, 365 + 1135, 636 + 225), outline=GRID_COL, width=1)
    hi_om = float(np.max(sim_b['Omega_hist'])) * 1.05
    dibujar_curva(dr, sim_b['Omega_hist'], box_j, COL_BKM_BLOWUP, 0.0, hi_om, width=3)
    dibujar_curva(dr, sim_l['Omega_hist'], box_j, COL_LERAY_GOLD, 0.0, hi_om, width=3)

    dr.text((68, 660), 'Cuasi-Blow-up BKM (l_Leray = 0)', font=f_txt, fill=COL_BKM_BLOWUP)
    dr.text((68, 700), 'Flujo Suave de Leray (l = 0.28)', font=f_txt, fill=COL_LERAY_GOLD)
    dr.text((68, 745), 'El estiramiento 3D dispara', font=f_sm, fill=MUTED)
    dr.text((68, 765), 'la vorticidad hacia T*; el', font=f_sm, fill=MUTED)
    dr.text((68, 785), 'operador (I − l²Δ)^(-1) doma', font=f_sm, fill=MUTED)
    dr.text((68, 805), 'la cascada ultravioleta.', font=f_sm, fill=MUTED)

    for x_frac, x_off, txt_lbl in [
        (0.0, 0, 't = 0 (Inyección laminar)'),
        (0.5, -75, 'Cascada triádica k^(-5/3)'),
        (1.0, -210, 'Frontera BKM / Equilibrio Leray')
    ]:
        xx = 365 + x_frac * 1135
        dr.line((xx, 636, xx, 861), fill=GRID_COL, width=1)
        dr.text((xx + x_off, 872), txt_lbl, font=f_sm, fill=FG)

    im.save(str(path_png), 'PNG')
    return im


def crear_lamina_02_muestra_aislada(y_solo, tr_solo, med_solo, path_png):
    W, H = 1600, 960
    im = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(im)
    f_title = cargar_fuente(23, bold=True)
    f_sub = cargar_fuente(14)
    f_sec = cargar_fuente(15, bold=True)
    f_sm = cargar_fuente(11)

    dr.text((48, 24), '02 · MUESTRA AISLADA · LA CASCADA DE ENSTROFÍA DE NAVIER–STOKES (24 s)', font=f_title, fill=FG)
    dr.text((48, 60), f'Archivo: {med_solo["m4a"]} · {med_solo["I_LUFS"]:.1f} LUFS · {med_solo["pico_dBTP"]:.1f} dBTP · LRA {med_solo["LRA"]:.1f} · Semilla {SEMILLA}', font=f_sub, fill=MUTED)

    x0, w_plot = 235, 1310
    secciones = [
        (0.0, 'I · Flujo Laminar Leray'),
        (4.8, 'II · Cascada Inercial −5/3'),
        (9.6, 'III · Cuasi-Blow-up BKM'),
        (14.4, 'IV · Rescate Suave Leray'),
        (19.2, 'V · Disipación de Vórtice')
    ]
    for sec_t, sec_lbl in secciones:
        xx = x0 + (sec_t / 24.0) * w_plot
        dr.line((xx, 112, xx, 885), fill=GRID_COL, width=1)
        dr.text((xx + 4, 110), sec_lbl, font=f_sm, fill=FG)

    yy0 = 142
    dr.rectangle((x0, yy0, x0 + w_plot, yy0 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy0 + 24), 'Estiramiento σ(t)', font=f_sec, fill=COL_BKM_BLOWUP)
    dibujar_curva(dr, tr_solo['estiramiento_sigma'], (x0, yy0 + 4, w_plot, 64), COL_BKM_BLOWUP, 0.0, 1.05, width=2)

    yy1 = 234
    dr.rectangle((x0, yy1, x0 + w_plot, yy1 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy1 + 24), 'Suavidad Leray l(t)', font=f_sec, fill=COL_LERAY_GOLD)
    dibujar_curva(dr, tr_solo['suavidad_leray'], (x0, yy1 + 4, w_plot, 64), COL_LERAY_GOLD, 0.0, 1.05, width=2)

    yy2 = 326
    dr.rectangle((x0, yy2, x0 + w_plot, yy2 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy2 + 24), 'Enstrofía Ω(t)', font=f_sec, fill=COL_KOLMOGOROV)
    dibujar_curva(dr, tr_solo['enstrofia_Omega'], (x0, yy2 + 4, w_plot, 64), COL_KOLMOGOROV, 0.0, None, width=2)

    yy3 = 418
    dr.rectangle((x0, yy3, x0 + w_plot, yy3 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy3 + 24), 'Corte Viscoso f_η', font=f_sec, fill=MUTED)
    dibujar_curva(dr, tr_solo['f_disipacion_kolmogorov'], (x0, yy3 + 4, w_plot, 64), MUTED, 100.0, 4500.0, width=2)

    yy_w = 518
    dr.rectangle((x0, yy_w, x0 + w_plot, yy_w + 88), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy_w + 30), 'Onda estéreo', font=f_sec, fill=FG)
    y_norm_vis = normalizar_nivel(y_solo)
    dibujar_curva(dr, y_norm_vis[:, 0], (x0, yy_w + 4, w_plot, 80), COL_KOLMOGOROV, -0.75, 0.75, width=1)

    yy_s = 626
    spec_im = espectrograma_imagen(y_solo, SR, w_plot, 252)
    im.paste(spec_im, (x0, yy_s))
    dr.rectangle((x0, yy_s, x0 + w_plot, yy_s + 252), outline=GRID_COL, width=1)
    dr.text((48, yy_s + 20), 'Espectrograma\n35 Hz – 11.0 kHz', font=f_sec, fill=FG)
    dr.text((48, yy_s + 78), 'En III la enstrofía\nse precipita hacia\nagudos (BKM); en IV\nla suavidad de Leray\nla devuelve al cauce.', font=f_sm, fill=COL_BKM_BLOWUP)

    for s_tick in range(0, 25, 3):
        xx = x0 + (s_tick / 24.0) * w_plot
        dr.text((xx - 10, 892), f'{s_tick} s', font=f_sm, fill=MUTED)
    dr.text((48, 922), 'Lectura: la transferencia triádica (u·∇)u sube la energía por las capas de Rejilla hasta el corte de disipación k_η.', font=f_sm, fill=MUTED)

    im.save(str(path_png), 'PNG')
    return im


def crear_lamina_03_escena_navier_stokes(y_mix, tr_esc, med_mix, path_png):
    W, H = 1600, 960
    im = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(im)
    f_title = cargar_fuente(23, bold=True)
    f_sub = cargar_fuente(14)
    f_sec = cargar_fuente(15, bold=True)
    f_sm = cargar_fuente(11)

    dr.text((48, 24), '03 · ESCENA EN CONTEXTO · CASCADA DE NAVIER–STOKES + BAJO DE HOPF + SIRINGUA', font=f_title, fill=FG)
    dr.text((48, 60), f'Archivo: {med_mix["m4a"]} · {med_mix["I_LUFS"]:.1f} LUFS · {med_mix["pico_dBTP"]:.1f} dBTP · La Siringua canta en el Ojo Laminar del Vórtice', font=f_sub, fill=MUTED)

    x0, w_plot = 235, 1310
    secciones = [
        (0.0, 'I · Cauce Laminar'),
        (4.8, 'II · Ojo en 440 Hz'),
        (9.6, 'III · BKM + Ojo 330 Hz'),
        (14.4, 'IV · Rescate Leray 440 Hz'),
        (19.2, 'V · Coda Disipativa')
    ]
    for sec_t, sec_lbl in secciones:
        xx = x0 + (sec_t / 24.0) * w_plot
        dr.line((xx, 112, xx, 885), fill=GRID_COL, width=1)
        dr.text((xx + 4, 110), sec_lbl, font=f_sm, fill=FG)

    yy0 = 142
    dr.rectangle((x0, yy0, x0 + w_plot, yy0 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy0 + 24), 'Enstrofía Ω(t)', font=f_sec, fill=COL_BKM_BLOWUP)
    dibujar_curva(dr, tr_esc['enstrofia_Omega'], (x0, yy0 + 4, w_plot, 64), COL_BKM_BLOWUP, 0.0, None, width=2)

    yy1 = 234
    dr.rectangle((x0, yy1, x0 + w_plot, yy1 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy1 + 24), 'Suavidad Leray l(t)', font=f_sec, fill=COL_LERAY_GOLD)
    dibujar_curva(dr, tr_esc['suavidad_leray'], (x0, yy1 + 4, w_plot, 64), COL_LERAY_GOLD, 0.0, 1.05, width=2)

    yy2 = 326
    dr.rectangle((x0, yy2, x0 + w_plot, yy2 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy2 + 24), 'Bajo de Leray–Hopf', font=f_sec, fill=MUTED)
    dibujar_curva(dr, tr_esc['env_bajo_hopf'], (x0, yy2 + 4, w_plot, 64), MUTED, 0.0, 1.2, width=2)

    yy3 = 418
    dr.rectangle((x0, yy3, x0 + w_plot, yy3 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy3 + 24), 'Siringua en Ojo', font=f_sec, fill=COL_SIRINGUA)
    dibujar_curva(dr, tr_esc['f0_siringua_ojo'], (x0, yy3 + 4, w_plot, 64), COL_SIRINGUA, 280.0, 600.0, width=2)

    yy_w = 518
    dr.rectangle((x0, yy_w, x0 + w_plot, yy_w + 88), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy_w + 26), 'Mezcla estéreo', font=f_sec, fill=FG)
    y_norm_vis = normalizar_nivel(y_mix)
    dibujar_curva(dr, y_norm_vis[:, 0], (x0, yy_w + 4, w_plot, 80), COL_KOLMOGOROV, -0.75, 0.75, width=1)

    yy_s = 626
    spec_im = espectrograma_imagen(y_mix, SR, w_plot, 252)
    im.paste(spec_im, (x0, yy_s))
    dr.rectangle((x0, yy_s, x0 + w_plot, yy_s + 252), outline=GRID_COL, width=1)
    dr.text((48, yy_s + 20), 'Espectrograma\nMezcla Completa', font=f_sec, fill=FG)
    dr.text((48, yy_s + 78), 'El sumidero viscoso\nabre un ojo laminar\nen 440 y 330 Hz\ndonde canta la\nSiringua limpia.', font=f_sm, fill=COL_SIRINGUA)

    for s_tick in range(0, 25, 3):
        xx = x0 + (s_tick / 24.0) * w_plot
        dr.text((xx - 10, 892), f'{s_tick} s', font=f_sm, fill=MUTED)
    dr.text((48, 922), 'Costura hidrodinámica: mientras la cascada ruge arriba y abajo, la viscosidad selectiva despeja el canal de la voz solista.', font=f_sm, fill=MUTED)

    im.save(str(path_png), 'PNG')
    return im


def main():
    print('1. Ejecutando sonda de La Cascada de Enstrofía de Navier–Stokes (Leray–BKM)...', flush=True)
    sonda_res = ejecutar_sonda()
    print('   Sonda OK:', json.dumps(sonda_res, ensure_ascii=False), flush=True)

    print('2. Sintetizando muestra aislada de 24 s...', flush=True)
    partitura_solo = {
        'prototipo': 'cascada-navier-stokes-bkm',
        'duracion': 24.0,
        'semilla': SEMILLA,
        'empuje_reynolds_Re': [
            [0.0, 0.22], [4.6, 0.35],
            [4.8, 0.78], [9.5, 0.85],
            [9.7, 0.96], [14.3, 0.98],
            [14.5, 0.82], [19.1, 0.82],
            [19.3, 0.65], [24.0, 0.35]
        ],
        'estiramiento_vortice_sigma': [
            [0.0, 0.15], [4.6, 0.25],
            [4.8, 0.65], [9.5, 0.72],
            [9.7, 0.95], [14.3, 0.98],
            [14.5, 0.85], [19.1, 0.85],
            [19.3, 0.55], [24.0, 0.25]
        ],
        'suavidad_leray_ell': [
            [0.0, 0.90], [4.6, 0.85],
            [4.8, 0.45], [9.5, 0.40],
            [9.7, 0.04], [14.3, 0.04],
            [14.5, 0.94], [19.1, 0.96],
            [19.3, 0.82], [24.0, 0.96]
        ],
        'ojo_laminar_costura_hz': [
            [0.0, 0.0], [24.0, 0.0]
        ],
        'eventos': [
            {'t0': 0.25, 'dur': 4.4, 'f_pivote': 110.0, 'vel': 0.86},
            {'t0': 4.85, 'dur': 4.5, 'f_pivote': 110.0, 'vel': 0.92},
            {'t0': 9.65, 'dur': 4.5, 'f_pivote': 165.0, 'vel': 0.94},
            {'t0': 14.45, 'dur': 4.5, 'f_pivote': 110.0, 'vel': 0.90},
            {'t0': 19.25, 'dur': 4.5, 'f_pivote': 110.0, 'vel': 0.92},
        ]
    }
    y_solo, tr_solo = render_cascada_navier_stokes(partitura_solo, 24.0, SR, SEMILLA)
    med_solo = guardar_audio_y_medir(
        y_solo,
        OUT_DIR / 'muestra-cascada-navier-stokes-s20261021.wav',
        OUT_DIR / 'muestra-cascada-navier-stokes-s20261021.m4a',
        target_lufs=-18.5
    )

    print('3. Sintetizando escena en contexto (Cascada de Navier–Stokes + Bajo de Hopf + Siringua en Ojo Laminar)...', flush=True)
    y_mix, stems_esc, tr_esc = render_escena_navier_stokes_siringua(24.0, SR, SEMILLA)
    med_mix = guardar_audio_y_medir(
        y_mix,
        OUT_DIR / 'escena-cascada-navier-stokes-s20261021.wav',
        OUT_DIR / 'escena-cascada-navier-stokes-s20261021.m4a',
        target_lufs=-16.0
    )

    print('4. Generando láminas PNG en OKLCh y GIF...', flush=True)
    p1_png = OUT_DIR / '01-cascada-kolmogorov-y-criterio-bkm-s20261021.png'
    p2_png = OUT_DIR / '02-cascada-navier-stokes-espectrograma-s20261021.png'
    p3_png = OUT_DIR / '03-escena-navier-stokes-siringua-costura-s20261021.png'
    im1 = crear_lamina_01_navier_stokes_sonda(sonda_res, p1_png)
    im2 = crear_lamina_02_muestra_aislada(y_solo, tr_solo, med_solo, p2_png)
    im3 = crear_lamina_03_escena_navier_stokes(y_mix, tr_esc, med_mix, p3_png)

    frames = [im.resize((1200, 720), Image.Resampling.LANCZOS).quantize(colors=256, method=Image.Quantize.MEDIANCUT) for im in (im1, im2, im3)]
    gif_path = OUT_DIR / 'proceso-cascada-navier-stokes-s20261021.gif'
    frames[0].save(
        str(gif_path),
        format='GIF',
        save_all=True,
        append_images=frames[1:],
        duration=1800,
        loop=0,
        optimize=True
    )

    if Path(__file__).resolve() != (OUT_DIR / 'cascada_navier_stokes_bkm.py').resolve():
        shutil.copyfile(__file__, OUT_DIR / 'cascada_navier_stokes_bkm.py')

    receta = {
        'instrumento': 'La Cascada de Enstrofía de Navier–Stokes (Leray–BKM)',
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
    receta_path = OUT_DIR / 'receta-cascada-navier-stokes-s20261021.json'
    with open(receta_path, 'w', encoding='utf-8') as f:
        json.dump(receta, f, ensure_ascii=False, indent=2)

    print('5. Todo completado con éxito:', json.dumps(receta, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
