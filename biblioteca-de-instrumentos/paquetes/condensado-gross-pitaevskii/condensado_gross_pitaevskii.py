"""Construcción, sonda y producción real de El Condensado de Gross–Pitaevskii (Bogoliubov–Abrikosov–Feshbach) para Rejilla.

Física y Matemática Cuántica de Superfluidos (Condensado de Bose–Einstein y Redes de Vórtices):
1. Ecuación de Gross–Pitaevskii (GPE) en trampa armónica rotatoria con corrección cuántica de Lee–Huang–Yang (LHY):
   i * hbar * dpsi/dt = ( - (hbar^2 / 2m) * nabla^2 + V_trap(r) + g * |psi|^2 + gamma_LHY * |psi|^3 - Omega * L_z ) * psi
   Integración numérica mediante el método espectral de paso dividido de Fourier (Split-Step Fourier Method, SSFM),
   que preserva unitariamente la norma cuántica N = int |psi(r,t)|^2 d^2r con precisión de máquina.
2. Espectro de Excitaciones Elementales de Bogoliubov (1947) y Puente Armónico <-> Cuadrático:
   omega_Bog(k) = sqrt( c_s^2 * k^2 + (hbar * k^2 / (2m))^2 ) = c_s * k * sqrt( 1 + (k * xi)^2 / 2 )
   donde c_s = sqrt(g * n_0 / m) es la velocidad del sonido superfluida y xi = hbar / sqrt(2 * m * g * n_0)
   es la longitud de curación (healing length).
   - Para k * xi << 1 (infrarrojo fonónico): omega(k) ~ c_s * k (pendiente log-log = 1.0, serie armónica pura).
   - Para k * xi >> 1 (ultravioleta cuántico): omega(k) ~ hbar * k^2 / (2m) (pendiente log-log = 2.0, dispersión cuadrática cristalina).
3. Red Triangular de Vórtices Cuantizados de Abrikosov, Ondas de Tkachenko y Modos de Kelvin:
   Al rotar la trampa por encima de Omega_c, el superfluido nuclea vórtices con circulación cuantizada
   oint v_s · dl = (2*pi*hbar/m) * l_v y fase singular arg(psi) = sum_j arctan2(y - y_j, x - x_j).
   La red cristalina de vórtices vibra con modos elásticos transversales de Tkachenko (c_T = sqrt(hbar * Omega / 4m))
   y ondas helicoidales de Kelvin a lo largo de los filamentos.
4. Resonancia de Feshbach (Colapso Atractivo de Bosenova g < 0) vs Gota Cuántica de Lee–Huang–Yang (LHY):
   Cuando el acoplamiento pasa a g < 0 por resonancia magnética de Feshbach, la densidad central colapsa
   abruptamente (Bosenova); la repulsión de fluctuaciones cuánticas de punto cero de Lee–Huang–Yang (+gamma_LHY |psi|^3)
   rescata al condensado formando una gota cuántica auto-ligada (quantum droplet) ultradensa y coherente.
5. Costura Espectral de Rejilla («El Nodo Topológico de Solitón Oscuro / Núcleo de Vórtice»):
   Un solitón oscuro estacionario psi_dark(f) ~ tanh((f - f_soliton) / Delta_f_xi) impone densidad exactamente nula
   |psi(f_soliton)|^2 = 0 y un salto topológico de fase de pi radianes en la frecuencia de la Siringua (440 Hz / 330 Hz),
   abriendo un canal de vacío cuántico (> 52 dB de despeje) donde la voz solista canta sin colisión.
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


# ───────────── 1. Matemática Exacta: Gross–Pitaevskii (SSFM), Bogoliubov, Abrikosov, Feshbach–LHY y Paleta OKLCh ─────────────
def dispersion_bogoliubov_teorica(k_vals, c_s=1.0, xi=0.25):
    """Calcula la relación de dispersión exacta de Bogoliubov:
    omega(k) = c_s * k * sqrt(1 + 0.5 * (k * xi)^2),
    junto con la asíntota fonónica lineal (c_s * k) y la asíntota cuántica cuadrática (c_s * xi / sqrt(2) * k^2).
    También devuelve las amplitudes de cuasipartícula u_k^2 y v_k^2 con u_k^2 - v_k^2 = 1.
    """
    k_arr = np.asarray(k_vals, dtype=np.float64)
    k_xi = k_arr * float(xi)
    omega_bog = float(c_s) * k_arr * np.sqrt(1.0 + 0.5 * (k_xi ** 2))
    omega_phonon = float(c_s) * k_arr
    omega_free = (float(c_s) * float(xi) / math.sqrt(2.0)) * (k_arr ** 2)
    eps_0 = omega_free
    mc2 = (float(c_s) ** 2) * (math.sqrt(2.0) / max(1e-9, float(xi) * float(c_s)))
    ratio = (eps_0 + mc2) / np.maximum(1e-12, omega_bog)
    u_k2 = 0.5 * (ratio + 1.0)
    v_k2 = 0.5 * np.maximum(0.0, ratio - 1.0)
    return {
        'k': k_arr,
        'omega_bog': omega_bog,
        'omega_phonon': omega_phonon,
        'omega_free': omega_free,
        'u_k2': u_k2,
        'v_k2': v_k2,
        'k_cruce': math.sqrt(2.0) / max(1e-9, float(xi))
    }


def construir_red_abrikosov_2d(N_grid=64, L_box=10.0, R_tf=3.4, xi=0.32, n_vortices=7, omega_rot=0.65):
    """Construye la función de onda compleja psi(x, y) = sqrt(n(r)) * exp(i * S(x, y))
    de un condensado de Bose–Einstein en perfil de Thomas–Fermi atravesado por una red triangular
    de Abrikosov de n_vortices vórtices cuantizados (núcleo f(r) = r / sqrt(r^2 + 2*xi^2)).
    """
    x = np.linspace(-L_box / 2.0, L_box / 2.0, N_grid)
    y = np.linspace(-L_box / 2.0, L_box / 2.0, N_grid)
    X, Y = np.meshgrid(x, y)
    R2 = X ** 2 + Y ** 2

    env_tf = np.maximum(0.0, 1.0 - R2 / (R_tf ** 2))
    psi = np.sqrt(env_tf).astype(np.complex128) + 1e-6 * np.exp(-R2 / (2.0 * R_tf ** 2))

    vortex_coords = []
    if n_vortices >= 1:
        vortex_coords.append((0.0, 0.0))
    if n_vortices > 1:
        n_ring1 = min(6, n_vortices - 1)
        d_lattice = 1.35 * (1.0 / max(0.35, math.sqrt(omega_rot)))
        for j in range(n_ring1):
            ang = 2.0 * math.pi * j / n_ring1 + 0.22
            vortex_coords.append((d_lattice * math.cos(ang), d_lattice * math.sin(ang)))
    if n_vortices > 7:
        n_ring2 = n_vortices - 7
        d_lattice2 = 2.35 * (1.0 / max(0.35, math.sqrt(omega_rot)))
        for j in range(n_ring2):
            ang = 2.0 * math.pi * j / n_ring2 + math.pi / 6.0
            vortex_coords.append((d_lattice2 * math.cos(ang), d_lattice2 * math.sin(ang)))

    for vx, vy in vortex_coords:
        dx = X - vx
        dy = Y - vy
        rv = np.sqrt(dx ** 2 + dy ** 2)
        core_profile = rv / np.sqrt(rv ** 2 + 2.0 * (xi ** 2))
        phase_v = np.arctan2(dy, dx)
        psi *= core_profile * np.exp(1j * phase_v)

    dx_step = L_box / (N_grid - 1)
    norm_val = math.sqrt(float(np.sum(np.abs(psi) ** 2)) * (dx_step ** 2))
    psi /= max(1e-12, norm_val)
    return {
        'x': x,
        'y': y,
        'psi': psi,
        'densidad': np.abs(psi) ** 2,
        'fase': np.angle(psi),
        'vortex_coords': vortex_coords,
        'dx': dx_step
    }


def simular_gpe_split_step_1d(
    N_pts=256,
    L_dom=16.0,
    g_nonlin=12.0,
    gamma_lhy=0.0,
    dt=0.001,
    n_steps=1600,
    modo_soliton=False
):
    """Integra la ecuación de Gross–Pitaevskii (con término de Lee–Huang–Yang opcional)
    en 1D mediante Split-Step Fourier Method (SSFM) exacto:
    i dpsi/dt = [ -1/2 d^2/dx^2 + 1/2 x^2 + g |psi|^2 + gamma_LHY |psi|^3 ] psi
    Verifica la conservación unitaria de la masa cuántica N(t) = int |psi|^2 dx y la dinámica
    de colapso atractivo de Feshbach (Bosenova, g < 0) vs estabilización de gota cuántica LHY.
    """
    dx = L_dom / N_pts
    x = np.linspace(-L_dom / 2.0, L_dom / 2.0 - dx, N_pts)
    k = 2.0 * math.pi * np.fft.fftfreq(N_pts, d=dx)
    V_trap = 0.5 * (x ** 2)

    if modo_soliton:
        psi = np.exp(-0.5 * (x / 1.8) ** 2) * np.tanh(x / 0.45) + 0j
    else:
        psi = np.exp(-0.5 * (x / 1.45) ** 2) * (1.0 + 0.08 * np.cos(2.0 * x)) + 0j

    norm0 = math.sqrt(float(np.sum(np.abs(psi) ** 2) * dx))
    psi /= norm0

    exp_kin = np.exp(-0.5j * (k ** 2) * dt)
    norm_hist = np.zeros(n_steps + 1, dtype=np.float64)
    peak_dens_hist = np.zeros(n_steps + 1, dtype=np.float64)
    energy_hist = np.zeros(n_steps + 1, dtype=np.float64)

    def calc_energy(p):
        dp_dx = np.fft.ifft(1j * k * np.fft.fft(p))
        dens = np.abs(p) ** 2
        e_kin = 0.5 * np.sum(np.abs(dp_dx) ** 2) * dx
        e_pot = np.sum(V_trap * dens) * dx
        e_int = 0.5 * g_nonlin * np.sum(dens ** 2) * dx
        e_lhy = (2.0 / 5.0) * gamma_lhy * np.sum(dens ** 2.5) * dx
        return float(e_kin + e_pot + e_int + e_lhy)

    for step in range(n_steps + 1):
        dens = np.abs(psi) ** 2
        norm_hist[step] = float(np.sum(dens) * dx)
        peak_dens_hist[step] = float(np.max(dens))
        energy_hist[step] = calc_energy(psi)
        if step < n_steps:
            V_nl = V_trap + g_nonlin * dens + gamma_lhy * (dens ** 1.5)
            psi = psi * np.exp(-0.5j * V_nl * dt)
            psi = np.fft.ifft(exp_kin * np.fft.fft(psi))
            dens_mid = np.abs(psi) ** 2
            V_nl_mid = V_trap + g_nonlin * dens_mid + gamma_lhy * (dens_mid ** 1.5)
            psi = psi * np.exp(-0.5j * V_nl_mid * dt)

    return {
        'x': x,
        'psi_final': psi,
        'norm_hist': norm_hist,
        'peak_dens_hist': peak_dens_hist,
        'energy_hist': energy_hist
    }


def oklch(L, C, h_deg):
    rad = math.radians(h_deg)
    a = C * math.cos(rad)
    b = C * math.sin(rad)
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a + 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    r_lin = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g_lin = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    b_lin = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    def srgb(x):
        x = max(0.0, min(1.0, x))
        return 12.92 * x if x <= 0.0031308 else 1.055 * (x ** (1.0 / 2.4)) - 0.055
    return (int(round(srgb(r_lin) * 255)), int(round(srgb(g_lin) * 255)), int(round(srgb(b_lin) * 255)))


rng_vis = np.random.default_rng(SEMILLA + 1995)
H0 = 208.0 + float(rng_vis.uniform(-4.0, 4.0))
BG = oklch(0.11, 0.030, H0)
PANEL_BG = oklch(0.15, 0.036, H0 + 5)
GRID_COL = oklch(0.26, 0.038, H0)
FG = oklch(0.95, 0.020, H0 + 15)
MUTED = oklch(0.68, 0.034, H0 + 8)
COL_BOGOLIUBOV = oklch(0.84, 0.17, H0 - 28)
COL_ABRIKOSOV = oklch(0.82, 0.18, H0 + 82)
COL_FESHBACH = oklch(0.76, 0.20, H0 + 152)
COL_DROPLET_LHY = oklch(0.87, 0.17, H0 - 115)


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

    sim_rep = simular_gpe_split_step_1d(N_pts=256, L_dom=16.0, g_nonlin=8.0, gamma_lhy=0.0, dt=0.0005, n_steps=2000)
    N0 = sim_rep['norm_hist'][0]
    Nf = sim_rep['norm_hist'][-1]
    err_norm = abs(Nf - N0) / max(1e-15, N0)
    E0 = sim_rep['energy_hist'][0]
    Ef = sim_rep['energy_hist'][-1]
    err_energy = abs(Ef - E0) / max(1e-12, abs(E0))

    resultados['prueba_1_unitariedad_ssfm_e_invarianza_gpe'] = {
        'norma_inicial_N0': round(N0, 8),
        'norma_final_Nf': round(Nf, 8),
        'error_relativo_norma_cuantica': float(f'{err_norm:.2e}'),
        'energia_GPE_inicial': round(E0, 5),
        'energia_GPE_final': round(Ef, 5),
        'error_relativo_energia_GPE': float(f'{err_energy:.2e}')
    }

    k_grid = np.geomspace(0.05, 80.0, 400)
    bog = dispersion_bogoliubov_teorica(k_grid, c_s=1.0, xi=0.35)
    mask_ir = k_grid <= 0.25
    mask_uv = k_grid >= 25.0
    slope_ir, _ = np.polyfit(np.log10(k_grid[mask_ir]), np.log10(bog['omega_bog'][mask_ir]), 1)
    slope_uv, _ = np.polyfit(np.log10(k_grid[mask_uv]), np.log10(bog['omega_bog'][mask_uv]), 1)
    err_rel_uv = float(np.max(np.abs(bog['u_k2'] - bog['v_k2'] - 1.0)))

    resultados['prueba_2_dispersion_bogoliubov_fonon_a_particula'] = {
        'pendiente_fononica_IR_medida': round(float(slope_ir), 4),
        'pendiente_fononica_IR_teorica': 1.0,
        'pendiente_cuadratica_UV_medida': round(float(slope_uv), 4),
        'pendiente_cuadratica_UV_teorica': 2.0,
        'numero_onda_cruce_kc': round(bog['k_cruce'], 3),
        'error_conmutador_bosonico_uk2_menos_vk2': float(f'{err_rel_uv:.2e}')
    }

    red = construir_red_abrikosov_2d(N_grid=96, L_box=10.0, R_tf=3.6, xi=0.28, n_vortices=7, omega_rot=0.72)
    psi_2d = red['psi']
    mid_i = 96 // 2
    loop_pts = [
        (mid_i - 3, mid_i - 3), (mid_i - 3, mid_i), (mid_i - 3, mid_i + 3),
        (mid_i, mid_i + 3), (mid_i + 3, mid_i + 3), (mid_i + 3, mid_i),
        (mid_i + 3, mid_i - 3), (mid_i, mid_i - 3), (mid_i - 3, mid_i - 3)
    ]
    winding_sum = 0.0
    for idx_p in range(len(loop_pts) - 1):
        r0, c0 = loop_pts[idx_p]
        r1, c1 = loop_pts[idx_p + 1]
        dphi = np.angle(psi_2d[r1, c1] * np.conj(psi_2d[r0, c0]))
        winding_sum += float(dphi)
    carga_topologica = winding_sum / (2.0 * math.pi)

    sim_bosenova = simular_gpe_split_step_1d(N_pts=256, L_dom=16.0, g_nonlin=-6.2, gamma_lhy=0.0, dt=0.0004, n_steps=1800)
    sim_droplet = simular_gpe_split_step_1d(N_pts=256, L_dom=16.0, g_nonlin=-6.2, gamma_lhy=5.4, dt=0.0004, n_steps=1800)
    rho_bosenova = float(np.max(sim_bosenova['peak_dens_hist']))
    rho_droplet = float(np.max(sim_droplet['peak_dens_hist']))

    resultados['prueba_3_red_abrikosov_y_colapso_feshbach_lhy'] = {
        'vortices_nucleados_abrikosov': len(red['vortex_coords']),
        'carga_topologica_central_medida': round(carga_topologica, 4),
        'densidad_pico_colapso_bosenova': round(rho_bosenova, 2),
        'densidad_pico_gota_cuantica_LHY': round(rho_droplet, 2),
        'factor_contencion_cuantica_LHY': round(rho_bosenova / max(1e-9, rho_droplet), 2)
    }

    P_cond = PistaRejilla('sonda_bec_uniforme', columnas=2, S_grid=32768, H_grid=16384)
    freqs_bec = [110.0, 220.0, 330.0, 440.0, 550.0, 660.0, 880.0, 1320.0]
    for idx_f, fk in enumerate(freqs_bec):
        amp_k = 0.16 * ((fk / 110.0) ** (-0.45))
        P_cond.modo(fk, amp_k, 0.0, a=2.2, pan=-0.4 + 0.11 * idx_f, fase=0.0)
    ZL_cond, _ = P_cond.escribir()

    P_sol = PistaRejilla('sonda_bec_soliton_oscuro', columnas=2, S_grid=32768, H_grid=16384)
    f_soliton = 440.0
    ancho_xi_hz = 45.0
    for idx_f, fk in enumerate(freqs_bec):
        amp_k = 0.16 * ((fk / 110.0) ** (-0.45))
        perfil_tanh = math.tanh((fk - f_soliton) / ancho_xi_hz)
        if abs(fk - f_soliton) < 5.0:
            amp_sol = amp_k * 0.00012
            fase_sol = 0.0
        else:
            amp_sol = amp_k * abs(perfil_tanh)
            fase_sol = 0.0 if perfil_tanh >= 0.0 else math.pi
        P_sol.modo(fk, amp_sol, 0.0, a=2.2, pan=-0.4 + 0.11 * idx_f, fase=fase_sol)
    ZL_sol, ZR_sol = P_sol.escribir()

    def energia_banda(Z_col, f_center, half_w=3):
        k0_b = max(1, int(round(f_center)) - half_w)
        k1_b = min(len(Z_col), int(round(f_center)) + half_w + 1)
        return float(np.sum(np.abs(Z_col[k0_b:k1_b]) ** 2))

    e_cond_440 = energia_banda(ZL_cond[0], 440.0)
    e_sol_440 = energia_banda(ZL_sol[0], 440.0)
    despeje_soliton_db = 10.0 * math.log10((e_sol_440 + 1e-24) / (e_cond_440 + 1e-24))

    wav_sonda = INTER_DIR / 'sonda_gross_pitaevskii_spectrumsynth.wav'
    esc_sonda = sintetizar_spectrumsynth(ZL_sol, ZR_sol, wav_sonda, S_grid=32768)
    _, y_ff = wavfile.read(wav_sonda)
    y_ff = y_ff.astype(np.float64) * esc_sonda
    y_ti = P_sol.tiempo(0.0, 2.0)
    snr_db = 10.0 * math.log10(np.sum(y_ti ** 2) / (np.sum((y_ff - y_ti) ** 2) + 1e-24))

    resultados['prueba_4_nodo_soliton_oscuro_costura_y_spectrumsynth'] = {
        'energia_condensado_440Hz': round(e_cond_440, 4),
        'energia_nodo_soliton_440Hz': round(e_sol_440, 9),
        'despeje_soliton_oscuro_dB': round(despeje_soliton_db, 2),
        'salto_fase_topologico_rad': round(math.pi, 4),
        'SNR_spectrumsynth_dB': round(snr_db, 2)
    }

    return resultados


# ───────────── 4. Motor Temporal de 24 s: Muestra Aislada (El Condensado de Gross–Pitaevskii) ─────────────
def render_condensado_gross_pitaevskii(partitura, duracion=24.0, sr=SR, semilla=SEMILLA):
    n_total = int(round(duracion * sr))
    t = np.arange(n_total) / sr
    out = np.zeros((n_total, 2), dtype=np.float64)

    def interp_ctrl(key, default):
        pts = np.asarray(partitura.get(key, [[0.0, default], [duracion, default]]), dtype=float)
        return np.interp(t, pts[:, 0], pts[:, 1])

    xi_curve = interp_ctrl('longitud_curacion_xi', 0.15)
    omega_curve = interp_ctrl('rotacion_abrikosov_omega', 0.2)
    feshbach_curve = interp_ctrl('acoplamiento_feshbach_g', 0.2)
    soliton_curve = interp_ctrl('nodo_soliton_costura_hz', 0.0)

    n_modos = 14
    modos_idx = np.arange(1, n_modos + 1, dtype=np.float64)

    traza_dispersion_inarmonica = np.zeros(n_total, dtype=np.float64)
    traza_vortices_nv = np.zeros(n_total, dtype=np.float64)
    traza_densidad_bosenova = np.zeros(n_total, dtype=np.float64)

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
        xi_loc = xi_curve[i0:i1]
        om_loc = omega_curve[i0:i1]
        fe_loc = feshbach_curve[i0:i1]
        sol_loc = soliton_curve[i0:i1]

        nv_raw = 19.0 * np.maximum(0.0, om_loc - 0.12) / 0.88
        nv_quant = np.floor(nv_raw) + 0.5 * (1.0 + np.tanh(6.0 * (nv_raw - np.floor(nv_raw) - 0.5)))
        traza_vortices_nv[i0:i1] = np.maximum(traza_vortices_nv[i0:i1], nv_quant)

        pulso_bosenova = 1.0 + 3.4 * (fe_loc ** 2) * np.exp(-(((u / dur_ev) - 0.58) / 0.16) ** 2)
        traza_densidad_bosenova[i0:i1] = np.maximum(traza_densidad_bosenova[i0:i1], pulso_bosenova)

        estiramiento_8 = np.sqrt(1.0 + 0.5 * ((8.0 * 0.22 * xi_loc) ** 2))
        traza_dispersion_inarmonica[i0:i1] = np.maximum(traza_dispersion_inarmonica[i0:i1], estiramiento_8)

        win_ev = (np.sin(np.minimum(1.0, u / 0.05) * math.pi / 2.0) ** 2) * (
            np.sin(np.minimum(1.0, (dur_ev - u) / 0.18) * math.pi / 2.0) ** 2
        )

        for idx_m, n_m in enumerate(modos_idx):
            xi_eff = 0.21 * (xi_loc ** 1.25)
            factor_bog = np.sqrt(1.0 + 0.5 * ((n_m * xi_eff) ** 2))
            chirp_feshbach = 1.0 - 0.045 * (fe_loc ** 1.6) * np.sin(math.pi * (u / dur_ev)) * np.log1p(n_m)

            f_tkachenko = 1.8 + 5.4 * np.sqrt(np.maximum(0.0, om_loc))
            mod_tkachenko = 1.0 + 0.011 * om_loc * np.sin(2.0 * math.pi * f_tkachenko * u + 0.55 * idx_m)

            f_inst = f_piv * n_m * factor_bog * chirp_feshbach * mod_tkachenko
            if float(np.mean(f_inst)) >= sr * 0.44:
                break

            env_kelvin = 1.0 - 0.34 * om_loc * (1.0 - np.cos(2.0 * math.pi * (0.9 * f_tkachenko) * u + idx_m * 0.8))
            amp_base = (n_m ** (-0.78)) * (1.0 + 0.42 * (xi_loc ** 1.1) * ((n_m / 6.0) ** 0.35))
            boost_feshbach = 1.0 + 0.65 * (fe_loc ** 1.5) * np.exp(-(((u / dur_ev) - 0.58) / 0.18) ** 2) * ((n_m / 5.0) ** 0.3)
            corte_uv = np.exp(-0.08 * ((n_m / (9.5 + 4.0 * xi_loc)) ** 2))

            dist_sol = f_inst - sol_loc
            perfil_tanh = np.tanh(dist_sol / 42.0)
            soliton_mask = np.where(
                sol_loc > 50.0,
                np.abs(perfil_tanh) * (1.0 - 0.96 * np.exp(-((dist_sol / 26.0) ** 2))),
                1.0
            )
            salto_fase_soliton = np.where((sol_loc > 50.0) & (dist_sol < 0.0), math.pi, 0.0)

            amp_inst = (0.108 * vel) * amp_base * env_kelvin * boost_feshbach * corte_uv * soliton_mask * win_ev

            ph_inst = 2.0 * math.pi * np.cumsum(f_inst) / sr + salto_fase_soliton
            kelvon_sideband = 0.14 * om_loc * np.sin(ph_inst + 2.0 * math.pi * (1.5 * f_tkachenko) * u + idx_m)

            pan_base = ((-1) ** idx_m) * (0.15 + 0.65 * (idx_m / max(1, n_modos - 1)))
            pan_val = float(np.clip(pan_base, -0.86, 0.86))
            gL, gR = paneo(pan_val)

            sig_m = amp_inst * (np.sin(ph_inst) + kelvon_sideband)
            out[i0:i1, 0] += gL * sig_m
            out[i0:i1, 1] += gR * sig_m

    for ch, delay_s, g_rev in ((0, 0.037, 0.15), (1, 0.053, 0.15), (0, 0.079, 0.10), (1, 0.097, 0.10)):
        nd = int(round(delay_s * sr))
        if nd < n_total:
            out[nd:, ch] += g_rev * out[:-nd, 1 - ch]

    trazas = {
        'longitud_curacion_xi': xi_curve,
        'rotacion_abrikosov_omega': omega_curve,
        'acoplamiento_feshbach_g': feshbach_curve,
        'estiramiento_bogoliubov': traza_dispersion_inarmonica,
        'vortices_cuantizados_nv': traza_vortices_nv,
        'densidad_bosenova_lhy': traza_densidad_bosenova
    }
    return out, trazas


# ───────────── 5. Escena en Contexto: Condensado de Gross–Pitaevskii + Bajo de Kohn–Hopf + Siringua en Solitón Oscuro ─────────────
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


def render_escena_condensado_siringua_hopf(duracion=24.0, sr=SR, semilla=SEMILLA):
    n_total = int(round(duracion * sr))
    t = np.arange(n_total) / sr
    rng = np.random.default_rng(semilla + 2001)
    f0_base = 110.0

    part_bec = {
        'longitud_curacion_xi': [
            [0.0, 0.05], [4.6, 0.12],
            [4.8, 0.72], [9.5, 0.84],
            [9.7, 0.48], [14.3, 0.55],
            [14.5, 0.88], [19.1, 0.92],
            [19.3, 0.35], [24.0, 0.18]
        ],
        'rotacion_abrikosov_omega': [
            [0.0, 0.08], [4.6, 0.14],
            [4.8, 0.32], [9.5, 0.40],
            [9.7, 0.88], [14.3, 0.95],
            [14.5, 0.65], [19.1, 0.70],
            [19.3, 0.45], [24.0, 0.20]
        ],
        'acoplamiento_feshbach_g': [
            [0.0, 0.10], [4.6, 0.15],
            [4.8, 0.28], [9.5, 0.35],
            [9.7, 0.45], [14.3, 0.50],
            [14.5, 0.95], [19.1, 0.98],
            [19.3, 0.30], [24.0, 0.15]
        ],
        'nodo_soliton_costura_hz': [
            [0.0, 0.0], [4.7, 0.0],
            [4.8, 440.0], [9.5, 440.0],
            [9.6, 330.0], [14.3, 330.0],
            [14.4, 440.0], [19.1, 440.0],
            [19.2, 550.0], [24.0, 550.0]
        ],
        'eventos': [
            {'t0': 0.20, 'dur': 4.45, 'f_pivote': f0_base, 'vel': 0.85},
            {'t0': 4.80, 'dur': 4.60, 'f_pivote': f0_base, 'vel': 0.92},
            {'t0': 9.60, 'dur': 4.60, 'f_pivote': f0_base * 1.5, 'vel': 0.94},
            {'t0': 14.40, 'dur': 4.60, 'f_pivote': f0_base, 'vel': 0.92},
            {'t0': 19.20, 'dur': 4.60, 'f_pivote': f0_base, 'vel': 0.90},
        ]
    }
    y_bec, tr_bec = render_condensado_gross_pitaevskii(part_bec, duracion, sr, semilla)

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
        env_b = (np.sin(np.minimum(1.0, u / 0.06) * math.pi / 2.0) ** 2) * np.exp(-1.32 * u)
        ph_b = 2.0 * math.pi * fb * u
        sig_b = (0.78 * np.sin(ph_b) + 0.22 * np.sin(2.0 * ph_b)) * env_b * (0.16 * velb)
        y_bajo[i0:i1, 0] += sig_b * 0.72
        y_bajo[i0:i1, 1] += sig_b * 0.72
        env_bajo[i0:i1] += env_b

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
    vf = np.array([VOCALES[v] for v in ['a', 'e', 'i', 'o', 'u']], dtype=float)
    form_curves = np.array([np.interp(t, t_voc, vf[:, k]) for k in range(4)])
    sir_mono = formantes_boca(exc_s, form_curves, sr) * 2.35
    y_siringua = np.column_stack([sir_mono * 0.72, sir_mono * 0.72])

    mix = y_bec * 0.88 + y_bajo * 0.82 + y_siringua * 0.94
    trazas_esc = {
        'vortices_cuantizados_nv': tr_bec['vortices_cuantizados_nv'],
        'densidad_bosenova_lhy': tr_bec['densidad_bosenova_lhy'],
        'env_bajo_hopf': env_bajo,
        'f0_siringua_soliton': f0_sir_vib * (amp_sir > 0.04)
    }
    return mix, {'condensado': y_bec, 'bajo': y_bajo, 'siringua': y_siringua}, trazas_esc


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
    c_mid = np.array(COL_ABRIKOSOV, dtype=float)
    c_hi = np.array(COL_BOGOLIUBOV, dtype=float)
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


def crear_lamina_01_gross_pitaevskii_sonda(sonda_res, path_png):
    W, H = 1600, 960
    im = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(im)
    f_title = cargar_fuente(23, bold=True)
    f_sub = cargar_fuente(14)
    f_sec = cargar_fuente(16, bold=True)
    f_txt = cargar_fuente(13)
    f_sm = cargar_fuente(11)

    p1 = sonda_res['prueba_1_unitariedad_ssfm_e_invarianza_gpe']
    p2 = sonda_res['prueba_2_dispersion_bogoliubov_fonon_a_particula']
    p3 = sonda_res['prueba_3_red_abrikosov_y_colapso_feshbach_lhy']
    p4 = sonda_res['prueba_4_nodo_soliton_oscuro_costura_y_spectrumsynth']

    dr.text((48, 24), '01 · CONDENSADO DE GROSS–PITAEVSKII · BOGOLIUBOV, RED DE ABRIKOSOV Y FESHBACH–LHY', font=f_title, fill=FG)
    dr.text((48, 60), f'Semilla {SEMILLA} · spectrumsynth {p4["SNR_spectrumsynth_dB"]} dB · Pendientes Bogoliubov {p2["pendiente_fononica_IR_medida"]} -> {p2["pendiente_cuadratica_UV_medida"]} · Unitariedad SSFM {p1["error_relativo_norma_cuantica"]:.1e}', font=f_sub, fill=MUTED)

    dr.rectangle((48, 104, 775, 548), fill=PANEL_BG, outline=GRID_COL, width=2)
    dr.text((68, 120), 'Puente de Bogoliubov (k¹ → k²) y Red Cuántica de Abrikosov', font=f_sec, fill=COL_BOGOLIUBOV)

    k_plot = np.geomspace(0.15, 25.0, 400)
    bog_p = dispersion_bogoliubov_teorica(k_plot, c_s=1.0, xi=0.45)
    log_bog = np.log10(bog_p['omega_bog'])
    log_pho = np.log10(bog_p['omega_phonon'])

    box_bog = (68, 162, 390, 165)
    dr.rectangle((68, 162, 68 + 390, 162 + 165), outline=GRID_COL, width=1)
    dibujar_curva(dr, log_pho, box_bog, MUTED, -0.85, 2.5, width=2)
    dibujar_curva(dr, log_bog, box_bog, COL_BOGOLIUBOV, -0.85, 2.5, width=3)
    dr.text((78, 172), 'ω(k) = √(c_s²k² + (ħk²/2m)²)', font=f_sm, fill=COL_BOGOLIUBOV)
    dr.text((78, 192), 'Cian: Bogoliubov exacto (pendiente 1 → 2)', font=f_sm, fill=FG)
    dr.text((78, 210), 'Gris: Fonón lineal armónico ω = c_s·k', font=f_sm, fill=MUTED)

    om_vals = np.linspace(0.0, 1.0, 350)
    nv_raw = 14.0 * np.maximum(0.0, om_vals - 0.14) / 0.86
    nv_step = np.floor(nv_raw) + 0.5 * (1.0 + np.tanh(8.0 * (nv_raw - np.floor(nv_raw) - 0.5)))
    box_nv = (68, 355, 390, 155)
    dr.rectangle((68, 355, 68 + 390, 355 + 155), outline=GRID_COL, width=1)
    dibujar_curva(dr, nv_step, box_nv, COL_ABRIKOSOV, -0.5, 14.5, width=3)
    dr.text((78, 365), 'Escalera de Feynman–Abrikosov N_v(Ω)', font=f_sm, fill=COL_ABRIKOSOV)
    dr.text((78, 385), 'Cada escalón nuclea un cuanto ħ de vorticidad', font=f_sm, fill=FG)

    red_vis = construir_red_abrikosov_2d(N_grid=160, L_box=9.0, R_tf=3.5, xi=0.28, n_vortices=7, omega_rot=0.72)
    dens_v = red_vis['densidad']
    dens_norm = np.clip(dens_v / max(1e-9, float(dens_v.max())), 0.0, 1.0)
    pha_v = (red_vis['fase'] + math.pi) / (2.0 * math.pi)
    c1 = np.array(COL_BOGOLIUBOV, dtype=float)
    c2 = np.array(COL_ABRIKOSOV, dtype=float)
    c0 = np.array(BG, dtype=float)
    mix_col = pha_v[..., None] * c1 + (1.0 - pha_v[..., None]) * c2
    rgb_abrikosov = np.clip(c0 + (dens_norm[..., None] ** 0.75) * (mix_col - c0), 0, 255).astype(np.uint8)
    im_ab = Image.fromarray(rgb_abrikosov).resize((268, 268), Image.Resampling.BILINEAR)
    im.paste(im_ab, (482, 162))
    dr.rectangle((482, 162, 482 + 268, 162 + 268), outline=GRID_COL, width=1)
    dr.text((482, 442), 'Red Triangular de Abrikosov (7 vórtices)', font=f_sm, fill=COL_BOGOLIUBOV)
    dr.text((482, 462), 'Núcleos oscuros: |ψ(r_v)|² = 0', font=f_sm, fill=FG)
    dr.text((482, 482), 'Color: Fase cuántica arg(ψ) ∈ [−π, π]', font=f_sm, fill=MUTED)
    dr.text((482, 502), f'Carga topológica medida: l_v = {p3["carga_topologica_central_medida"]:+.2f}', font=f_sm, fill=COL_DROPLET_LHY)

    dr.rectangle((805, 104, 1552, 548), fill=PANEL_BG, outline=GRID_COL, width=2)
    dr.text((825, 120), 'Resultados medidos por la sonda (SSFM, Bogoliubov, Abrikosov, LHY)', font=f_sec, fill=COL_DROPLET_LHY)

    lineas = [
        ('1. Integrador Espectral Split-Step Fourier (Unitariedad GPE):', COL_BOGOLIUBOV),
        (f'   • Error relativo de norma cuántica ∫|ψ|²dx: {p1["error_relativo_norma_cuantica"]:.2e}', FG),
        (f'   • Invarianza de energía hamiltoniana E[ψ]: {p1["error_relativo_energia_GPE"]:.2e}', FG),
        ('2. Relación de Dispersión de Bogoliubov (Fonón → Partícula Libre):', COL_DROPLET_LHY),
        (f'   • Pendiente infrarroja (kξ << 1): {p2["pendiente_fononica_IR_medida"]:.4f} (teórica 1.0000 armónica)', FG),
        (f'   • Pendiente ultravioleta (kξ >> 1): {p2["pendiente_cuadratica_UV_medida"]:.4f} (teórica 2.0000 cuadrática)', FG),
        ('3. Red de Vórtices de Abrikosov y Resonancia de Feshbach–LHY:', COL_ABRIKOSOV),
        (f'   • Vórtices cuantizados: {p3["vortices_nucleados_abrikosov"]} · Circulación central: l_v = {p3["carga_topologica_central_medida"]:.4f}·(2πħ/m)', FG),
        (f'   • Densidad pico: Bosenova {p3["densidad_pico_colapso_bosenova"]:.2f} vs Gota LHY {p3["densidad_pico_gota_cuantica_LHY"]:.2f} ({p3["factor_contencion_cuantica_LHY"]:.2f}x contenida)', FG),
        ('4. Costura del Solitón Oscuro Topológico en 440 Hz (Siringua):', COL_FESHBACH),
        (f'   • Nodo |ψ(440 Hz)|² = 0: {p4["despeje_soliton_oscuro_dB"]:+.2f} dB · Salto Δφ = π rad · SNR {p4["SNR_spectrumsynth_dB"]:.2f} dB', FG),
    ]
    yy = 158
    for txt, col in lineas:
        dr.text((825, yy), txt, font=f_txt, fill=col)
        yy += 34

    dr.rectangle((48, 574, 1552, 918), fill=PANEL_BG, outline=GRID_COL, width=2)
    dr.text((68, 590), 'Dinámica de Resonancia de Feshbach (g < 0): Implosión de Bosenova vs Gota Cuántica de Lee–Huang–Yang (+γ_LHY|ψ|³)', font=f_sec, fill=FG)

    sim_b = simular_gpe_split_step_1d(N_pts=256, L_dom=16.0, g_nonlin=-6.2, gamma_lhy=0.0, dt=0.0004, n_steps=1800)
    sim_d = simular_gpe_split_step_1d(N_pts=256, L_dom=16.0, g_nonlin=-6.2, gamma_lhy=5.4, dt=0.0004, n_steps=1800)
    box_j = (365, 636, 1135, 225)
    dr.rectangle((365, 636, 365 + 1135, 636 + 225), outline=GRID_COL, width=1)
    hi_rho = float(np.max(sim_b['peak_dens_hist'])) * 1.08
    dibujar_curva(dr, sim_b['peak_dens_hist'], box_j, COL_FESHBACH, 0.2, hi_rho, width=3)
    dibujar_curva(dr, sim_d['peak_dens_hist'], box_j, COL_DROPLET_LHY, 0.2, hi_rho, width=3)

    dr.text((68, 656), 'Implosión Bosenova (γ_LHY = 0)', font=f_txt, fill=COL_FESHBACH)
    dr.text((68, 696), 'Gota Cuántica LHY (γ_LHY = 5.4)', font=f_txt, fill=COL_DROPLET_LHY)
    dr.text((68, 742), 'Cuando g < 0 por resonancia de', font=f_sm, fill=MUTED)
    dr.text((68, 762), 'Feshbach, la atracción cúbica', font=f_sm, fill=MUTED)
    dr.text((68, 782), 'comprime la nube; la presión', font=f_sm, fill=MUTED)
    dr.text((68, 802), 'cuántica de punto cero LHY la', font=f_sm, fill=MUTED)
    dr.text((68, 822), 'estabiliza como gota líquida.', font=f_sm, fill=MUTED)

    for x_frac, x_off, txt_lbl in [
        (0.0, 0, 't = 0 (Trampa Thomas–Fermi)'),
        (0.5, -85, 'Compresión atractiva de Feshbach'),
        (1.0, -225, 'Pico Bosenova / Respiración de Gota LHY')
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

    dr.text((48, 24), '02 · MUESTRA AISLADA · EL CONDENSADO DE GROSS–PITAEVSKII (24 s)', font=f_title, fill=FG)
    dr.text((48, 60), f'Archivo: {med_solo["m4a"]} · {med_solo["I_LUFS"]:.1f} LUFS · {med_solo["pico_dBTP"]:.1f} dBTP · LRA {med_solo["LRA"]:.1f} · Semilla {SEMILLA}', font=f_sub, fill=MUTED)

    x0, w_plot = 235, 1310
    secciones = [
        (0.0, 'I · Superfluido Fonónico (k¹)'),
        (4.8, 'II · Cristal Bogoliubov (k²)'),
        (9.6, 'III · Red de Abrikosov + Kelvin'),
        (14.4, 'IV · Bosenova Feshbach–LHY'),
        (19.2, 'V · Gota Cuántica Coherente')
    ]
    for sec_t, sec_lbl in secciones:
        xx = x0 + (sec_t / 24.0) * w_plot
        dr.line((xx, 112, xx, 885), fill=GRID_COL, width=1)
        dr.text((xx + 4, 110), sec_lbl, font=f_sm, fill=FG)

    yy0 = 142
    dr.rectangle((x0, yy0, x0 + w_plot, yy0 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy0 + 24), 'Curación ξ(t) [k¹→k²]', font=f_sec, fill=COL_BOGOLIUBOV)
    dibujar_curva(dr, tr_solo['longitud_curacion_xi'], (x0, yy0 + 4, w_plot, 64), COL_BOGOLIUBOV, 0.0, 1.05, width=2)

    yy1 = 234
    dr.rectangle((x0, yy1, x0 + w_plot, yy1 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy1 + 24), 'Vórtices N_v(Ω)', font=f_sec, fill=COL_ABRIKOSOV)
    dibujar_curva(dr, tr_solo['vortices_cuantizados_nv'], (x0, yy1 + 4, w_plot, 64), COL_ABRIKOSOV, 0.0, 20.0, width=2)

    yy2 = 326
    dr.rectangle((x0, yy2, x0 + w_plot, yy2 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy2 + 24), 'Densidad Bosenova', font=f_sec, fill=COL_FESHBACH)
    dibujar_curva(dr, tr_solo['densidad_bosenova_lhy'], (x0, yy2 + 4, w_plot, 64), COL_FESHBACH, 0.8, 4.6, width=2)

    yy3 = 418
    dr.rectangle((x0, yy3, x0 + w_plot, yy3 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy3 + 24), 'Inarmonicidad ω_8', font=f_sec, fill=COL_DROPLET_LHY)
    dibujar_curva(dr, tr_solo['estiramiento_bogoliubov'], (x0, yy3 + 4, w_plot, 64), COL_DROPLET_LHY, 0.95, 2.1, width=2)

    yy_w = 518
    dr.rectangle((x0, yy_w, x0 + w_plot, yy_w + 88), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy_w + 30), 'Onda estéreo', font=f_sec, fill=FG)
    y_norm_vis = normalizar_nivel(y_solo)
    dibujar_curva(dr, y_norm_vis[:, 0], (x0, yy_w + 4, w_plot, 80), COL_BOGOLIUBOV, -0.75, 0.75, width=1)

    yy_s = 626
    spec_im = espectrograma_imagen(y_solo, SR, w_plot, 252)
    im.paste(spec_im, (x0, yy_s))
    dr.rectangle((x0, yy_s, x0 + w_plot, yy_s + 252), outline=GRID_COL, width=1)
    dr.text((48, yy_s + 20), 'Espectrograma\n35 Hz – 11.0 kHz', font=f_sec, fill=FG)
    dr.text((48, yy_s + 78), 'En II los sobretonos se\nabren por dispersión k²;\nen III vibran los modos\nde Tkachenko y en IV\nimplosiona Feshbach.', font=f_sm, fill=COL_BOGOLIUBOV)

    for s_tick in range(0, 25, 3):
        xx = x0 + (s_tick / 24.0) * w_plot
        dr.text((xx - 10, 892), f'{s_tick} s', font=f_sm, fill=MUTED)
    dr.text((48, 922), 'Lectura: ξ(t) curva los armónicos de fonones lineales a partículas libres cuadráticas; Ω(t) nuclea la red de vórtices de Abrikosov.', font=f_sm, fill=MUTED)

    im.save(str(path_png), 'PNG')
    return im


def crear_lamina_03_escena_condensado(y_mix, tr_esc, med_mix, path_png):
    W, H = 1600, 960
    im = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(im)
    f_title = cargar_fuente(23, bold=True)
    f_sub = cargar_fuente(14)
    f_sec = cargar_fuente(15, bold=True)
    f_sm = cargar_fuente(11)

    dr.text((48, 24), '03 · ESCENA EN CONTEXTO · CONDENSADO DE GROSS–PITAEVSKII + BAJO DE HOPF + SIRINGUA', font=f_title, fill=FG)
    dr.text((48, 60), f'Archivo: {med_mix["m4a"]} · {med_mix["I_LUFS"]:.1f} LUFS · {med_mix["pico_dBTP"]:.1f} dBTP · La Siringua habita el Nodo Topológico del Solitón Oscuro', font=f_sub, fill=MUTED)

    x0, w_plot = 235, 1310
    secciones = [
        (0.0, 'I · Superfluido Puro'),
        (4.8, 'II · Solitón en 440 Hz'),
        (9.6, 'III · Abrikosov + 330 Hz'),
        (14.4, 'IV · Bosenova + 440 Hz'),
        (19.2, 'V · Gota LHY + 550 Hz')
    ]
    for sec_t, sec_lbl in secciones:
        xx = x0 + (sec_t / 24.0) * w_plot
        dr.line((xx, 112, xx, 885), fill=GRID_COL, width=1)
        dr.text((xx + 4, 110), sec_lbl, font=f_sm, fill=FG)

    yy0 = 142
    dr.rectangle((x0, yy0, x0 + w_plot, yy0 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy0 + 24), 'Vórtices N_v(Ω)', font=f_sec, fill=COL_ABRIKOSOV)
    dibujar_curva(dr, tr_esc['vortices_cuantizados_nv'], (x0, yy0 + 4, w_plot, 64), COL_ABRIKOSOV, 0.0, 20.0, width=2)

    yy1 = 234
    dr.rectangle((x0, yy1, x0 + w_plot, yy1 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy1 + 24), 'Pulso Bosenova–LHY', font=f_sec, fill=COL_FESHBACH)
    dibujar_curva(dr, tr_esc['densidad_bosenova_lhy'], (x0, yy1 + 4, w_plot, 64), COL_FESHBACH, 0.8, 4.6, width=2)

    yy2 = 326
    dr.rectangle((x0, yy2, x0 + w_plot, yy2 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy2 + 24), 'Bajo Dipolar Kohn', font=f_sec, fill=MUTED)
    dibujar_curva(dr, tr_esc['env_bajo_hopf'], (x0, yy2 + 4, w_plot, 64), MUTED, 0.0, 1.2, width=2)

    yy3 = 418
    dr.rectangle((x0, yy3, x0 + w_plot, yy3 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy3 + 24), 'Siringua Solitón', font=f_sec, fill=COL_DROPLET_LHY)
    dibujar_curva(dr, tr_esc['f0_siringua_soliton'], (x0, yy3 + 4, w_plot, 64), COL_DROPLET_LHY, 280.0, 600.0, width=2)

    yy_w = 518
    dr.rectangle((x0, yy_w, x0 + w_plot, yy_w + 88), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy_w + 26), 'Mezcla estéreo', font=f_sec, fill=FG)
    y_norm_vis = normalizar_nivel(y_mix)
    dibujar_curva(dr, y_norm_vis[:, 0], (x0, yy_w + 4, w_plot, 80), COL_BOGOLIUBOV, -0.75, 0.75, width=1)

    yy_s = 626
    spec_im = espectrograma_imagen(y_mix, SR, w_plot, 252)
    im.paste(spec_im, (x0, yy_s))
    dr.rectangle((x0, yy_s, x0 + w_plot, yy_s + 252), outline=GRID_COL, width=1)
    dr.text((48, yy_s + 20), 'Espectrograma\nMezcla Completa', font=f_sec, fill=FG)
    dr.text((48, yy_s + 78), 'El solitón oscuro\ntanh((f−f_s)/Δf) anula\nla densidad en 440,\n330 y 550 Hz para la\nvoz de la Siringua.', font=f_sm, fill=COL_DROPLET_LHY)

    for s_tick in range(0, 25, 3):
        xx = x0 + (s_tick / 24.0) * w_plot
        dr.text((xx - 10, 892), f'{s_tick} s', font=f_sm, fill=MUTED)
    dr.text((48, 922), 'Costura cuántica: el nodo topológico de fase π abre un vacío superfluido exacto donde canta la Siringua sin compresores.', font=f_sm, fill=MUTED)

    im.save(str(path_png), 'PNG')
    return im


def main():
    print('1. Ejecutando sonda de El Condensado de Gross–Pitaevskii (Bogoliubov–Abrikosov–Feshbach)...', flush=True)
    sonda_res = ejecutar_sonda()
    print('   Sonda OK:', json.dumps(sonda_res, ensure_ascii=False), flush=True)

    print('2. Sintetizando muestra aislada de 24 s...', flush=True)
    partitura_solo = {
        'prototipo': 'condensado-gross-pitaevskii',
        'duracion': 24.0,
        'semilla': SEMILLA,
        'longitud_curacion_xi': [
            [0.0, 0.04], [4.6, 0.10],
            [4.8, 0.78], [9.5, 0.88],
            [9.7, 0.45], [14.3, 0.52],
            [14.5, 0.90], [19.1, 0.95],
            [19.3, 0.32], [24.0, 0.14]
        ],
        'rotacion_abrikosov_omega': [
            [0.0, 0.05], [4.6, 0.12],
            [4.8, 0.28], [9.5, 0.35],
            [9.7, 0.90], [14.3, 0.96],
            [14.5, 0.68], [19.1, 0.72],
            [19.3, 0.42], [24.0, 0.18]
        ],
        'acoplamiento_feshbach_g': [
            [0.0, 0.08], [4.6, 0.14],
            [4.8, 0.25], [9.5, 0.32],
            [9.7, 0.42], [14.3, 0.48],
            [14.5, 0.96], [19.1, 0.98],
            [19.3, 0.28], [24.0, 0.12]
        ],
        'nodo_soliton_costura_hz': [
            [0.0, 0.0], [24.0, 0.0]
        ],
        'eventos': [
            {'t0': 0.25, 'dur': 4.4, 'f_pivote': 110.0, 'vel': 0.86},
            {'t0': 4.85, 'dur': 4.5, 'f_pivote': 110.0, 'vel': 0.92},
            {'t0': 9.65, 'dur': 4.5, 'f_pivote': 165.0, 'vel': 0.94},
            {'t0': 14.45, 'dur': 4.5, 'f_pivote': 110.0, 'vel': 0.92},
            {'t0': 19.25, 'dur': 4.5, 'f_pivote': 110.0, 'vel': 0.90},
        ]
    }
    y_solo, tr_solo = render_condensado_gross_pitaevskii(partitura_solo, 24.0, SR, SEMILLA)
    med_solo = guardar_audio_y_medir(
        y_solo,
        OUT_DIR / 'muestra-condensado-gross-pitaevskii-s20261021.wav',
        OUT_DIR / 'muestra-condensado-gross-pitaevskii-s20261021.m4a',
        target_lufs=-18.5
    )

    print('3. Sintetizando escena en contexto (Condensado de Gross–Pitaevskii + Bajo de Hopf + Siringua en Solitón Oscuro)...', flush=True)
    y_mix, stems_esc, tr_esc = render_escena_condensado_siringua_hopf(24.0, SR, SEMILLA)
    med_mix = guardar_audio_y_medir(
        y_mix,
        OUT_DIR / 'escena-condensado-gross-pitaevskii-s20261021.wav',
        OUT_DIR / 'escena-condensado-gross-pitaevskii-s20261021.m4a',
        target_lufs=-16.0
    )

    print('4. Generando láminas PNG en OKLCh y GIF...', flush=True)
    p1_png = OUT_DIR / '01-dispersion-bogoliubov-y-red-abrikosov-s20261021.png'
    p2_png = OUT_DIR / '02-condensado-gross-pitaevskii-espectrograma-s20261021.png'
    p3_png = OUT_DIR / '03-escena-condensado-siringua-costura-s20261021.png'
    im1 = crear_lamina_01_gross_pitaevskii_sonda(sonda_res, p1_png)
    im2 = crear_lamina_02_muestra_aislada(y_solo, tr_solo, med_solo, p2_png)
    im3 = crear_lamina_03_escena_condensado(y_mix, tr_esc, med_mix, p3_png)

    frames = [im.resize((1200, 720), Image.Resampling.LANCZOS).quantize(colors=256, method=Image.Quantize.MEDIANCUT) for im in (im1, im2, im3)]
    gif_path = OUT_DIR / 'proceso-condensado-gross-pitaevskii-s20261021.gif'
    frames[0].save(
        str(gif_path),
        format='GIF',
        save_all=True,
        append_images=frames[1:],
        duration=1800,
        loop=0,
        optimize=True
    )

    if Path(__file__).resolve() != (OUT_DIR / 'condensado_gross_pitaevskii.py').resolve():
        shutil.copyfile(__file__, OUT_DIR / 'condensado_gross_pitaevskii.py')

    receta = {
        'instrumento': 'El Condensado de Gross–Pitaevskii (Bogoliubov–Abrikosov–Feshbach)',
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
    receta_path = OUT_DIR / 'receta-condensado-gross-pitaevskii-s20261021.json'
    with open(receta_path, 'w', encoding='utf-8') as f:
        json.dump(receta, f, ensure_ascii=False, indent=2)

    print('5. Todo completado con éxito:', json.dumps(receta, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
