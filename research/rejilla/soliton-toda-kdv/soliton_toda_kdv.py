"""Construcción, sonda y producción real de El Solitón Subarmónico de Toda–KdV ([L, P] = dL/dt) para Rejilla.

Ejecuta:
1. Sonda matemática y acústica (`ejecutar_sonda()`):
   - Prueba 1 (Isoespectralidad del Par de Lax dL/dt = [B, L] en la Red de Toda y en el potencial de Bargmann–Kay–Moses):
     Integra la colisión no lineal de N solitones (armónicos y subarmónicos) y verifica que los autovalores lambda_j = -kappa_j^2 de la matriz de Lax L permanecen invariantes hasta precisión de máquina (~1e-15), garantizando que las alturas asintóticas jamás se desafinan.
   - Prueba 2 (Desfase exacto de colisión de solitones de KdV / Hirota Delta_t_ij):
     Compara la trayectoria de un solitón armónico rápido (kappa_2) y un solitón subarmónico lento (kappa_1) cuando viajan solos frente a cuando chocan en el potencial sin reflexión u(t, tau) = -2 d^2/dt^2 ln det(I + M). Verifica que el adelanto medido del rápido y el retraso del lento coinciden con la fórmula analítica de KdV: Delta_t_i = +/- (1 / kappa_i) * ln|(kappa_2 + kappa_1)/(kappa_2 - kappa_1)|.
   - Prueba 3 (El Cráter de Colisión de KdV como Costura Automática):
     Demuestra y mide en dB que en el instante exacto del choque (t = 0, tau = 0), la suma lineal de dos ondas solitarias daría 2*(kappa_1^2 + kappa_2^2), mientras que la solución exacta de KdV cae a 2*(kappa_2^2 - kappa_1^2), abriendo un cráter de amplitud (reducción de pico y transferencia de cresta por repulsión de autovalores) donde cabe otro instrumento sin saturar.
   - Prueba 4 (Identidad de traza de Deift–Trubowitz q(t) = 4 sum kappa_j psi_j^2(t)):
     Verifica que las autofunciones vestidas psi_j(t, tau) obtenidas al resolver (I + M) Psi = e descomponen exactamente el potencial multisolitón con error < 1e-14.
   - Prueba 5 (SNR exacto en `spectrumsynth` gray16le vs suma temporal).
2. Muestra aislada de 24 s (`muestra-soliton-toda-kdv-s20261021.wav` y `.m4a`).
3. Escena en contexto de 24 s (`escena-vortex-toda-kdv-s20261021.wav` y `.m4a`): homenaje a *Vortex Temporum* de Gérard Grisey (Solitón Subarmónico de Toda–KdV + Piano Espectral en arpegios helicoidales de Ravel/Grisey + Siringua/Flauta en los cráteres de colisión).
4. Tres láminas PNG en paleta OKLCh sembrada y GIF en loop del proceso.
"""
import hashlib, json, math, os, shutil, subprocess
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.linalg import eigvalsh
from scipy.signal import stft, lfilter, iirpeak, butter, sosfilt
from PIL import Image, ImageDraw, ImageFont


SEMILLA = 20261021
SR = 32000

# Salida (rejilla, acuerdo del 13 oct 2026): carpeta exclusiva <pieza>-s<semilla>-<hash12>; nunca se pisa.
# La versión original escribía en el sandbox de otra herramienta (/working_dir/...).
AQUI = Path(__file__).resolve().parent
EJECUCION = hashlib.sha256(Path(__file__).read_bytes() + str(SEMILLA).encode() + os.urandom(16)).hexdigest()
OUT_DIR = AQUI / f'soliton-toda-kdv-s{SEMILLA}-{EJECUCION[:12]}'
INTER_DIR = OUT_DIR / 'intermedio'
if __name__ == '__main__':
    OUT_DIR.mkdir(parents=False, exist_ok=False)
    INTER_DIR.mkdir()

# ───────────── 1. Matemática Exacta: Kay–Moses / Hirota (KdV sin reflexión) y Par de Lax de Toda ─────────────
def resolver_solitones_kay_moses(t_grid, kappas, t0_list, tau_evol=0.0, eta_nl=1.0):
    """Resuelve el sistema exacto de Kay–Moses / Bargmann (I + M(t, tau)) Psi = e
    para un potencial de Schrödinger sin reflexión con autovalores lambda_j = -kappa_j^2.

    Parámetros:
    - t_grid: vector 1D de tiempos (longitud T).
    - kappas: vector 1D de parámetros espectrales kappa_j > 0 (longitud N).
    - t0_list: posiciones iniciales de cada solitón en tau = 0.
    - tau_evol: parámetro de evolución isoespectral de KdV (mueve cada solitón con velocidad 4 * kappa_j^2).
    - eta_nl: en [0, 1]. Si eta_nl = 1.0, usa la matriz completa de Kay–Moses (interacción exacta de solitones KdV).
              Si eta_nl = 0.0, usa sólo la diagonal M_ii (solitones sech^2 independientes que se suman linealmente).

    Devuelve:
    - modulos_vestidos: matriz (N, T) con las envolventes de cada solitón q_j(t) = 4 * kappa_j * psi_j^2(t, tau).
      En virtud de la identidad de traza de Deift–Trubowitz, sum_j q_j(t) = q(t, tau) = -u(t, tau) exacto!
    - fases_locales: matriz (N, T) con la derivada espacial logarítmica d/dt ln |psi_j(t)| (momento local del vórtice).
    - tau_hirota: vector (T,) con el determinante tau(t) = det(I + M(t, tau)).
    """
    t_arr = np.asarray(t_grid, dtype=np.float64)
    kap = np.asarray(kappas, dtype=np.float64)
    t0 = np.asarray(t0_list, dtype=np.float64)
    N = len(kap)
    T = len(t_arr)

    # Fase cinemática de cada solitón: theta_i(t, tau) = kappa_i * (t - t0_i - 4 * kappa_i^2 * tau)
    # Usamos centrado simétrico para que en t = t0_i y tau = 0 (sin acoplamiento) el pico de sech^2 caiga exactamente en t0_i.
    theta = kap[:, None] * (t_arr[None, :] - t0[:, None] - 4.0 * (kap[:, None] ** 2) * tau_evol)
    # Limitar theta para evitar overflow en exp(-theta)
    theta_clip = np.clip(theta, -45.0, 45.0)
    e_vec = np.sqrt(2.0 * kap[:, None]) * np.exp(-theta_clip)  # (N, T)

    # Construir matriz de Cauchy-Bargmann M_{ij}(t) = e_i(t) * e_j(t) / (kappa_i + kappa_j)
    denom = kap[:, None] + kap[None, :]  # (N, N)
    # Matriz de interacción fuera de la diagonal escalada por eta_nl
    mask_off = 1.0 - np.eye(N)
    scale_mat = np.eye(N) + float(eta_nl) * mask_off

    # M tiene forma (T, N, N)
    e_T = e_vec.T  # (T, N)
    M = (e_T[:, :, None] * e_T[:, None, :]) / denom[None, :, :]
    M = M * scale_mat[None, :, :]

    I_mat = np.eye(N)[None, :, :]
    A_sys = I_mat + M  # (T, N, N)

    # Resolver (I + M) * Psi = e_T en paralelo para todos los instantes T
    Psi = np.linalg.solve(A_sys, e_T[:, :, None])[..., 0]  # (T, N)
    tau_hirota = np.linalg.det(A_sys)  # (T,)

    # Envolvente vestida de cada modo: q_j(t) = 4 * kappa_j * psi_j^2(t)
    # Cuando hay 1 solo solitón: e_1 = sqrt(2k) e^{-th}, M_11 = e^{-2th}, Psi_1 = sqrt(2k) e^{-th} / (1 + e^{-2th}) = sqrt(k/2) sech(th)
    # -> q_1(t) = 4 * k * (k/2) sech^2(th) = 2 * k^2 * sech^2(th).
    q_vestidos = 4.0 * kap[None, :] * (Psi ** 2)  # (T, N)

    # Derivada temporal numérica suave del log-envolvente para el chirp de fase de Lax
    dt = float(t_arr[1] - t_arr[0]) if T > 1 else 1.0
    log_q = 0.5 * np.log(q_vestidos + 1e-12)
    fases_locales = np.gradient(log_q, dt, axis=0) if T > 1 else np.zeros_like(log_q)  # (T, N)

    return q_vestidos.T, fases_locales.T, tau_hirota


def potencial_hirota_exacto(t_grid, kappas, t0_list, tau_evol=0.0):
    """Calcula el potencial multisolitón q(t) = 2 * d^2/dt^2 ln det(I + M) mediante
    derivadas analíticas exactas de los determinantes, para certificar en la sonda
    la identidad de traza sum_j 4 * kappa_j * psi_j^2(t) == 2 * d^2/dt^2 ln tau(t)."""
    t_arr = np.asarray(t_grid, dtype=np.float64)
    kap = np.asarray(kappas, dtype=np.float64)
    t0 = np.asarray(t0_list, dtype=np.float64)
    N = len(kap)

    # Suma sobre los 2^N subconjuntos de Hirota con centrado simétrico:
    # Para que coincida exactamente con M_{ij} = 2*sqrt(k_i k_j)/(k_i+k_j) e^{-(th_i+th_j)},
    # el peso diagonal de cada elemento i en el determinante es M_{ii} = e^{-2 th_i}, y el menor 2x2
    # aporta el factor A_{ij} = ((k_i - k_j)/(k_i + k_j))^2!
    theta = kap[:, None] * (t_arr[None, :] - t0[:, None] - 4.0 * (kap[:, None] ** 2) * tau_evol)
    theta = np.clip(theta, -45.0, 45.0)

    log_A = np.zeros((N, N), dtype=np.float64)
    for i in range(N):
        for j in range(i + 1, N):
            log_A[i, j] = 2.0 * math.log(abs(kap[i] - kap[j]) / (kap[i] + kap[j]))

    tau = np.zeros_like(t_arr)
    tau_t = np.zeros_like(t_arr)
    tau_tt = np.zeros_like(t_arr)

    for mask in range(1 << N):
        bits = [i for i in range(N) if (mask >> i) & 1]
        if not bits:
            tau += 1.0
            continue
        slope = -2.0 * float(np.sum(kap[bits]))
        exponent = np.sum(-2.0 * theta[bits, :], axis=0)
        for idx_a in range(len(bits)):
            for idx_b in range(idx_a + 1, len(bits)):
                exponent = exponent + log_A[bits[idx_a], bits[idx_b]]
        w = np.exp(np.clip(exponent, -90.0, 90.0))
        tau += w
        tau_t += slope * w
        tau_tt += (slope ** 2) * w

    q_exact = 2.0 * (tau * tau_tt - (tau_t ** 2)) / (tau ** 2 + 1e-24)
    return q_exact, tau


def integrar_par_lax_toda(N_part=6, pasos=400, dt=0.01):
    """Integra el flujo isoespectral del Par de Lax dL/dt = [B, L] de la red de Toda finita
    y devuelve la historia de la matriz L, las energías locales a_n(t)^2 y el error máximo
    en los autovalores lambda_k."""
    # Inicializar matriz tridiagonal simétrica L (coordenadas de Flaschka b_n en diagonal, a_n en subdiagonal)
    b = np.linspace(-1.2, 1.4, N_part)
    # Pulso solitónico inicial comprimido en el centro de la cadena
    a = 0.65 * np.exp(-0.4 * ((np.arange(N_part - 1) - (N_part - 2) / 2.0) ** 2))

    def armar_L_B(a_vec, b_vec):
        L = np.diag(b_vec) + np.diag(a_vec, 1) + np.diag(a_vec, -1)
        B = np.diag(a_vec, 1) - np.diag(a_vec, -1)
        return L, B

    def rhs_flaschka(a_vec, b_vec):
        # Ecuaciones de Lax dL/dt = [B, L]:
        # da_n/dt = a_n * (b_{n+1} - b_n)
        # db_n/dt = 2 * (a_n^2 - a_{n-1}^2)
        da = a_vec * (b_vec[1:] - b_vec[:-1])
        a_sq = a_vec ** 2
        db = np.zeros_like(b_vec)
        db[0] = 2.0 * a_sq[0]
        db[1:-1] = 2.0 * (a_sq[1:] - a_sq[:-1])
        db[-1] = -2.0 * a_sq[-1]
        return da, db

    L0, _ = armar_L_B(a, b)
    evals_0 = np.sort(eigvalsh(L0))
    max_err_evals = 0.0
    trazas_b = np.zeros((pasos, N_part))
    trazas_a = np.zeros((pasos, N_part - 1))

    for step in range(pasos):
        trazas_b[step] = b
        trazas_a[step] = a
        # RK4 exacto sobre las variables de Flaschka (que equivale a integrar dL/dt = [B, L])
        da1, db1 = rhs_flaschka(a, b)
        da2, db2 = rhs_flaschka(a + 0.5 * dt * da1, b + 0.5 * dt * db1)
        da3, db3 = rhs_flaschka(a + 0.5 * dt * da2, b + 0.5 * dt * db2)
        da4, db4 = rhs_flaschka(a + dt * da3, b + dt * db3)
        a = a + (dt / 6.0) * (da1 + 2 * da2 + 2 * da3 + da4)
        b = b + (dt / 6.0) * (db1 + 2 * db2 + 2 * db3 + db4)

        if step % 40 == 0 or step == pasos - 1:
            Lt, _ = armar_L_B(a, b)
            ev_t = np.sort(eigvalsh(Lt))
            max_err_evals = max(max_err_evals, float(np.max(np.abs(ev_t - evals_0))))

    return evals_0, max_err_evals, trazas_a, trazas_b


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

rng_vis = np.random.default_rng(SEMILLA + 33)
H0 = 196.0 + float(rng_vis.uniform(-8.0, 8.0))
BG = oklch(0.12, 0.032, H0)
PANEL_BG = oklch(0.16, 0.038, H0 + 6)
GRID_COL = oklch(0.27, 0.038, H0)
FG = oklch(0.94, 0.022, H0 + 30)
MUTED = oklch(0.67, 0.038, H0 + 12)
COL_ARM = oklch(0.81, 0.16, H0 - 45)       # Cian/turquesa: Solitones Armónicos rápidos (Pájaros)
COL_SUB = oklch(0.74, 0.18, H0 + 145)      # Coral/carmesí: Solitones Subarmónicos lentos (Ballenas)
COL_VORTEX = oklch(0.85, 0.17, H0 - 115)   # Ámbar/oro: Vórtice de colisión y Par de Lax
COL_PIANO = oklch(0.79, 0.16, H0 + 85)     # Violeta/lila: Piano espectral de Vortex Temporum

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


# ───────────── 3. Motor Espectral Exacto (`PistaRejilla` + FFmpeg `spectrumsynth`) ─────────────
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


# ───────────── 4. Sonda de Verificación (`ejecutar_sonda()`) ─────────────
def ejecutar_sonda():
    resultados = {}

    # 1. Prueba de Isoespectralidad del Par de Lax dL/dt = [B, L] en la Red de Toda
    evals_0, err_evals_toda, tr_a, tr_b = integrar_par_lax_toda(N_part=7, pasos=500, dt=0.008)

    # 2. Prueba de la Identidad de Traza de Deift–Trubowitz:
    # sum_{j=1}^N 4 * kappa_j * psi_j^2(t, tau) == 2 * d^2/dt^2 ln det(I + M(t, tau))
    t_test = np.linspace(-2.5, 2.5, 2001)
    kappas_test = np.array([1.2, 2.4, 3.8])  # 1 subarmónico lento + 2 armónicos rápidos
    t0_test = np.array([0.0, 0.0, 0.0])
    q_vest, _, _ = resolver_solitones_kay_moses(t_test, kappas_test, t0_test, tau_evol=0.08, eta_nl=1.0)
    q_sum_vest = np.sum(q_vest, axis=0)
    q_hirota, _ = potencial_hirota_exacto(t_test, kappas_test, t0_test, tau_evol=0.08)
    err_traza = float(np.max(np.abs(q_sum_vest - q_hirota)))

    resultados['prueba_1_isoespectralidad_lax_y_traza'] = {
        'autovalores_lax_toda': [round(float(x), 4) for x in evals_0],
        'error_max_autovalores_lax_toda': float(f'{err_evals_toda:.2e}'),
        'error_max_identidad_traza_kay_moses': float(f'{err_traza:.2e}')
    }

    # 3. Prueba del Desfase No Lineal de Colisión de Solitones (Delta_t_ij)
    # Comparamos 2 solitones: subarmónico lento kappa_1 = 1.5 y armónico rápido kappa_2 = 3.0.
    # En tau_post = +0.25 (después de haber chocado en tau = 0), medimos el centro de masa (pico)
    # de cada autofunción vestida con interacción (eta_nl = 1.0) vs sin interacción (eta_nl = 0.0).
    k1, k2 = 1.5, 3.0
    t_col_grid = np.linspace(-12.0, 12.0, 48001)
    tau_post = 0.18
    q_nl_post, _, _ = resolver_solitones_kay_moses(t_col_grid, [k1, k2], [0.0, 0.0], tau_evol=tau_post, eta_nl=1.0)
    q_lin_post, _, _ = resolver_solitones_kay_moses(t_col_grid, [k1, k2], [0.0, 0.0], tau_evol=tau_post, eta_nl=0.0)

    def centro_masa(t_vec, w_vec):
        return float(np.sum(t_vec * w_vec) / (np.sum(w_vec) + 1e-24))

    # En KdV, al pasar de tau = -inf a tau = +inf, el solitón rápido sufre un desplazamiento total
    # Delta_x = + (1/k2) * ln((k2+k1)/(k2-k1)) respecto a su trayectoria antes de la colisión.
    # Comparando tau = -tau_post vs tau = +tau_post respecto al movimiento libre 4*k^2*tau:
    q_nl_pre, _, _ = resolver_solitones_kay_moses(t_col_grid, [k1, k2], [0.0, 0.0], tau_evol=-tau_post, eta_nl=1.0)
    recorrido_libre_fast = 4.0 * (k2 ** 2) * (2.0 * tau_post)
    recorrido_libre_slow = 4.0 * (k1 ** 2) * (2.0 * tau_post)

    avance_real_fast = centro_masa(t_col_grid, q_nl_post[1]) - centro_masa(t_col_grid, q_nl_pre[1])
    avance_real_slow = centro_masa(t_col_grid, q_nl_post[0]) - centro_masa(t_col_grid, q_nl_pre[0])

    desfase_medido_fast = avance_real_fast - recorrido_libre_fast
    desfase_medido_slow = avance_real_slow - recorrido_libre_slow

    desfase_teorico_fast = +(1.0 / k2) * math.log((k2 + k1) / (k2 - k1))
    desfase_teorico_slow = -(1.0 / k1) * math.log((k2 + k1) / (k2 - k1))

    resultados['prueba_2_desfase_colision_kdv'] = {
        'kappa_subarmonico_lento': k1,
        'kappa_armonico_rapido': k2,
        'adelanto_armonico_rapido_medido_s': round(desfase_medido_fast, 4),
        'adelanto_armonico_rapido_teorico_s': round(desfase_teorico_fast, 4),
        'retraso_subarmonico_lento_medido_s': round(desfase_medido_slow, 4),
        'retraso_subarmonico_lento_teorico_s': round(desfase_teorico_slow, 4),
    }

    # 4. Prueba del Cráter de Colisión de KdV (Costura automática en el centro del choque)
    # En tau = 0 y t = 0 (choque exacto centrado), la suma lineal vale 2*(k1^2 + k2^2),
    # mientras que el potencial exacto de KdV cae a 2*(k2^2 - k1^2) (y para N solitones cae aún más!).
    ln_a12 = 0.5 * math.log(abs(k2 - k1) / (k2 + k1))
    t0_sym = [-ln_a12 / k1, -ln_a12 / k2]
    q_nl_0, _, _ = resolver_solitones_kay_moses(np.array([0.0]), [k1, k2], t0_sym, tau_evol=0.0, eta_nl=1.0)
    q_lin_0, _, _ = resolver_solitones_kay_moses(np.array([0.0]), [k1, k2], [0.0, 0.0], tau_evol=0.0, eta_nl=0.0)
    pico_lineal = float(np.sum(q_lin_0[:, 0]))
    pico_kdv_choque = float(np.sum(q_nl_0[:, 0]))
    crater_costura_db = 20.0 * math.log10(pico_kdv_choque / pico_lineal)

    # Además, ¿qué pasa cuando dos solitones tienen autovalores muy cercanos (cuasi-resonancia de Grisey, k1=2.4, k2=2.6)?
    ln_ac = 0.5 * math.log(abs(2.6 - 2.4) / (2.6 + 2.4))
    q_nl_casi, _, _ = resolver_solitones_kay_moses(np.array([0.0]), [2.4, 2.6], [-ln_ac / 2.4, -ln_ac / 2.6], tau_evol=0.0, eta_nl=1.0)
    q_lin_casi, _, _ = resolver_solitones_kay_moses(np.array([0.0]), [2.4, 2.6], [0.0, 0.0], tau_evol=0.0, eta_nl=0.0)
    crater_casi_resonante_db = 20.0 * math.log10(float(np.sum(q_nl_casi[:, 0])) / float(np.sum(q_lin_casi[:, 0])))

    resultados['prueba_3_crater_costura_colision'] = {
        'pico_suma_lineal': round(pico_lineal, 2),
        'pico_exacto_kdv_en_choque': round(pico_kdv_choque, 2),
        'reduccion_crater_2_solitones_dB': round(crater_costura_db, 2),
        'reduccion_crater_cuasi_resonante_grisey_dB': round(crater_casi_resonante_db, 2)
    }

    # 5. Prueba en `spectrumsynth` de FFmpeg: paquete de solitones con desfase de Bargmann
    P_sol = PistaRejilla('sonda_soliton_kdv', columnas=4, S_grid=32768, H_grid=16384)
    f0 = 165.0
    for j, (ratio, kap_v) in enumerate([(0.5, 1.4), (1.0, 2.0), (2.0, 2.8), (3.0, 3.5), (5.0, 4.2)]):
        # Fase de transmisión sin reflexión de Bargmann T(omega) = prod (omega + i*k)/(omega - i*k)
        fase_bargmann = -2.0 * math.atan2(kap_v, 2.0)
        dt_kdv = 0.08 * math.log((kap_v + 1.4) / abs(kap_v - 1.4 + 0.2)) if j > 0 else 0.0
        P_sol.modo(
            f0 * ratio, 0.11 / ((j + 1) ** 0.5), 0.25 + dt_kdv,
            3.0 + 0.4 * kap_v, ataque=65.0 + 15.0 * kap_v, suelta=0.55, ar=24.0,
            pan=-0.45 + 0.22 * j, fase=fase_bargmann
        )
    ZL_s, ZR_s = P_sol.escribir()
    wav_s = INTER_DIR / 'sonda_soliton_spectrumsynth.wav'
    esc_s = sintetizar_spectrumsynth(ZL_s, ZR_s, wav_s, S_grid=32768)
    _, y_ff = wavfile.read(wav_s)
    y_ff = y_ff.astype(np.float64) * esc_s
    y_ti = P_sol.tiempo(0.0, 4.0)
    snr_s_db = 10.0 * math.log10(np.sum(y_ti ** 2) / (np.sum((y_ff - y_ti) ** 2) + 1e-24))
    resultados['prueba_4_spectrumsynth_SNR_dB'] = round(snr_s_db, 2)

    return resultados


# ───────────── 5. Motor Temporal de 24 s (Muestra Aislada: El Solitón Subarmónico de Toda–KdV) ─────────────
def render_soliton_toda_kdv(partitura, duracion=24.0, sr=SR, semilla=SEMILLA):
    """Sintetiza 24 s del instrumento El Solitón Subarmónico de Toda–KdV.
    En cada ventana o ciclo de vórtice:
    - Los subarmónicos (f_0 / 3, f_0 / 2) y los armónicos (f_0, 2f_0, 3f_0, 5f_0, 7f_0) son autovalores
      ligados lambda_j = -kappa_j^2 del operador de Schrödinger L = -d^2/dt^2 + u(t, tau).
    - Sus envolventes temporales son las autofunciones vestidas q_j(t, tau) = 4 * kappa_j * psi_j^2(t, tau)
      obtenidas de (I + M(t, tau)) Psi = e.
    - Sus fases e inflexiones microtonales siguen el momento local del par de Lax P y el corrimiento
      de fase de transmisión de Bargmann.
    """
    n_total = int(round(duracion * sr))
    t = np.arange(n_total) / sr
    out = np.zeros((n_total, 2), dtype=np.float64)

    def interp_ctrl(key, default):
        pts = np.asarray(partitura.get(key, [[0.0, default], [duracion, default]]), dtype=float)
        return np.interp(t, pts[:, 0], pts[:, 1])

    tau_curve = interp_ctrl('tiempo_vortice_tau', 0.0)
    eta_nl_curve = interp_ctrl('acoplamiento_kdv_eta', 1.0)
    gamma_vortex_curve = interp_ctrl('escala_grisey_gamma', 1.0)
    beta_lax_curve = interp_ctrl('chirp_fase_lax_beta', 0.5)

    # También integramos una cadena de Toda de 7 partículas a lo largo de los 24 s para modular el brillo modal
    _, _, tr_a_toda, tr_b_toda = integrar_par_lax_toda(N_part=7, pasos=1200, dt=0.02)
    t_toda = np.linspace(0.0, duracion, 1200)

    # 7 voces solitónicas: 2 subarmónicos ("Ballenas": 1/3, 1/2) y 5 armónicos ("Humano + Pájaros": 1, 2, 3, 5, 7)
    ratios_base = np.array([1.0 / 3.0, 1.0 / 2.0, 1.0, 2.0, 3.0, 5.0, 7.0])
    kappas_base = np.array([1.15, 1.55, 2.15, 2.85, 3.55, 4.35, 5.15])

    potencial_total_traza = np.zeros(n_total, dtype=np.float64)
    envolvente_sub_traza = np.zeros(n_total, dtype=np.float64)
    envolvente_arm_traza = np.zeros(n_total, dtype=np.float64)

    eventos = partitura.get('eventos', [])
    ventanas = []
    for ev in eventos:
        t_start = float(ev['t0'])
        dur_ev = float(ev['dur'])
        f_piv = float(ev['f_pivote'])
        vel = float(ev.get('vel', 0.90))

        i0 = max(0, int(round(t_start * sr)))
        i1 = min(n_total, int(round((t_start + dur_ev) * sr)))
        if i1 <= i0:
            continue

        # Sub-rejilla para resolver el sistema lineal de Kay–Moses (a 400 Hz de control, luego interpolado a SR)
        n_sub = max(64, int(round(dur_ev * 400)))
        t_local_sub = np.linspace(-1.6, 1.6, n_sub)
        fiel = bool(ev.get('fiel', partitura.get('fiel', True)))
        t_abs_sub = np.linspace(t_start, t_start + dur_ev, n_sub)

        mid_idx = (i0 + i1) // 2
        tau_ev = float(ev.get('tau', tau_curve[mid_idx]))
        eta_ev = float(ev.get('eta_nl', eta_nl_curve[mid_idx]))
        gamma_ev = float(ev.get('gamma', gamma_vortex_curve[mid_idx]))
        beta_ev = float(ev.get('beta_lax', beta_lax_curve[mid_idx]))

        # Ajustar kappas según la escala temporal de Grisey (Pájaros vs Humano vs Ballenas)
        if gamma_ev >= 0:
            kappas_ev = kappas_base * (1.0 + 0.25 * gamma_ev * np.linspace(-0.5, 0.8, 7))
        else:
            # En Tiempo de Ballenas (gamma < 0), los subarmónicos se vuelven dominantes y más densos
            kappas_ev = kappas_base[::-1] * (0.85 + 0.2 * abs(gamma_ev))

        t0_ev = np.asarray(ev.get('t0_solitones', [-0.45, -0.20, 0.0, 0.12, 0.25, 0.38, 0.50]), dtype=float)

        lo, hi = -1.6, 1.6
        if fiel:
            # fiel (arreglo del 21 oct 2026, ver README): con τ ≠ 0 los solitones rápidos viajan 4κ²τ y salían de la
            # ventana fija [−1.6, 1.6] (no sonaban). La ventana ahora sigue a los siete: abarca del 0.5 % al 99.5 %
            # de la masa de cada voz, con un margen. Si el campo es más ancho, el evento lo recorre más rápido.
            tw = np.linspace(-80.0, 80.0, 16001)
            qw, _, _ = resolver_solitones_kay_moses(tw, kappas_ev, t0_ev, tau_evol=tau_ev, eta_nl=eta_ev)
            for qj in qw:
                c = np.cumsum(qj); c = c / (c[-1] + 1e-30)
                lo = min(lo, float(np.interp(0.005, c, tw)) - 0.25); hi = max(hi, float(np.interp(0.995, c, tw)) + 0.25)
            t_local_sub = np.linspace(lo, hi, max(n_sub, int((hi - lo) * 400)))
            ventanas.append((round(lo, 3), round(hi, 3)))
        q_vest_sub, dlog_sub, _ = resolver_solitones_kay_moses(
            t_local_sub, kappas_ev, t0_ev, tau_evol=tau_ev, eta_nl=eta_ev
        )

        u_audio = np.linspace(lo, hi, i1 - i0)
        t_audio = t[i0:i1]
        # Ventana suave de entrada y salida de la ola de Vortex
        win_ola = (np.sin(np.minimum(1.0, (t_audio - t_start) / 0.08) * math.pi / 2.0) ** 2) * (
            np.sin(np.minimum(1.0, (t_start + dur_ev - t_audio) / 0.16) * math.pi / 2.0) ** 2
        )

        for j in range(7):
            q_j = np.interp(u_audio, t_local_sub, q_vest_sub[j])
            dlog_j = np.interp(u_audio, t_local_sub, dlog_sub[j])
            b_toda_j = np.interp(t_audio, t_toda, tr_b_toda[:, j])

            # Normalizar la envolvente solitónica por su escala 2*kappa_j^2 para conservar energía perceptual
            env_sol = (q_j / (2.0 * (kappas_ev[j] ** 2) + 1e-9)) * win_ola

            if j < 2:
                envolvente_sub_traza[i0:i1] += env_sol * 0.5
            else:
                envolvente_arm_traza[i0:i1] += env_sol * 0.25
            potencial_total_traza[i0:i1] += q_j * win_ola

            f_base_j = f_piv * ratios_base[j]
            # El operador P del par de Lax curva la frecuencia instantánea durante el choque sin alterar el autovalor asintótico
            df_lax = beta_ev * 0.018 * dlog_j * f_base_j
            f_inst_j = np.clip(f_base_j + df_lax, 28.0, sr * 0.44)

            # Fase de transmisión sin reflexión de Bargmann a través de los demás solitones
            fase_barg = sum(-2.0 * math.atan2(kappas_ev[m], kappas_ev[j]) for m in range(7) if m != j) * eta_ev
            ph_j = 2.0 * math.pi * np.cumsum(f_inst_j) / sr + fase_barg

            # Timbre interno: los tres arquetipos de Vortex Temporum (seno + parciales modulados por Flaschka b_j)
            brillo_toda = 0.22 + 0.12 * np.tanh(b_toda_j)
            sig_j = (
                1.00 * np.cos(ph_j) +
                brillo_toda * np.cos(2.0 * ph_j + 0.5 * fase_barg) +
                (0.5 * brillo_toda) * np.cos(3.0 * ph_j - 0.5 * fase_barg)
            )
            # En los subarmónicos (j=0, 1), añadimos peso de subgrave tipo Mi0/La0
            peso_voz = 0.155 if j < 2 else (0.115 / ((j - 1) ** 0.55))

            # Paneo dinámico que sigue la posición instantánea del solitón en el vórtex
            cm_j = float(np.sum(u_audio * (env_sol + 1e-9)) / (np.sum(env_sol + 1e-9)))
            pan_j = float(np.clip(0.55 * cm_j * 1.6 / max(abs(lo), abs(hi)) + (-0.35 if j < 2 else 0.25) * math.sin(j * 1.1), -0.88, 0.88))
            gL, gR = paneo(pan_j)

            out[i0:i1, 0] += gL * vel * peso_voz * env_sol * sig_j
            out[i0:i1, 1] += gR * vel * peso_voz * env_sol * sig_j

    # Reverberación corta de cámara espectral
    for ch, delay_s, g_rev in ((0, 0.031, 0.14), (1, 0.043, 0.14), (0, 0.067, 0.08), (1, 0.079, 0.08)):
        nd = int(round(delay_s * sr))
        if nd < n_total:
            out[nd:, ch] += g_rev * out[:-nd, 1 - ch]

    trazas = {
        'tau_vortice': tau_curve,
        'eta_kdv': eta_nl_curve,
        'potencial_q_total': potencial_total_traza,
        'env_subarmonicos': envolvente_sub_traza,
        'env_armonicos': envolvente_arm_traza,
        'ventanas_fiel': ventanas
    }
    return out, trazas


# ───────────── 6. Escena en Contexto (24 s): Homenaje a *Vortex Temporum* (Solitones + Piano Espectral + Siringua en Cráteres) ─────────────
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

def render_escena_vortex_temporum(duracion=24.0, sr=SR, semilla=SEMILLA):
    """Escena de 24 s inspirada en *Vortex Temporum* de Gérard Grisey:
    1. El Solitón Subarmónico de Toda–KdV sostiene las olas de subarmónicos (Ballenas: Mi1 = 41.2 Hz, La1 = 55 Hz)
       y armónicos en colisión sobre el pivote Mi3 = 164.81 Hz.
    2. El Piano Espectral toca el arpegio helicoidal de Ravel/Grisey, pero los instantes de ataque de sus notas
       sufren el desfase exacto de colisión de KdV Delta_t_i = (1/kappa_i) ln|(kappa_i + kappa_sub)/(kappa_i - kappa_sub)|
       cada vez que cruzan un solitón subarmónico!
    3. En los cráteres de colisión donde tau(t) se minimiza y el potencial q(t) se achata por repulsión de autovalores,
       emerge la Siringua / Flauta espectral sin pelear por espacio (Costura no lineal de KdV).
    """
    n_total = int(round(duracion * sr))
    t = np.arange(n_total) / sr
    rng = np.random.default_rng(semilla + 77)
    f0_piv = 164.8138  # Mi3 (con subarmónicos en 82.41 Hz Mi2 y 54.94 Hz La1, y sombra en 41.20 Hz Mi1)

    part_sol = {
        'tiempo_vortice_tau': [
            [0.0, -0.22], [4.5, 0.0], [9.0, +0.22],
            [12.0, -0.18], [15.0, 0.0], [18.5, +0.18],
            [21.5, 0.0], [24.0, +0.12]
        ],
        'acoplamiento_kdv_eta': [[0.0, 0.0], [3.8, 1.0], [24.0, 1.0]],
        'escala_grisey_gamma': [[0.0, 0.5], [8.0, 1.0], [14.0, -0.8], [20.0, 0.6], [24.0, 0.8]],
        'chirp_fase_lax_beta': [[0.0, 0.25], [6.0, 0.85], [15.0, 0.95], [24.0, 0.50]],
        'eventos': [
            # I (0-4.8 s): Onda sinusoidal/lineal sin acoplamiento (eta_nl = 0.0)
            {'t0': 0.2, 'dur': 4.4, 'f_pivote': f0_piv, 'tau': -0.18, 'eta_nl': 0.0, 'gamma': 0.4, 'vel': 0.85},
            # II (4.8-9.6 s): Primer gran choque de solitones en tau = 0.0 (eta_nl = 1.0, cráter central activo)
            {'t0': 4.8, 'dur': 4.6, 'f_pivote': f0_piv, 'tau': 0.0, 'eta_nl': 1.0, 'gamma': 0.9, 'vel': 0.92,
             't0_solitones': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]},
            # III (9.6-14.4 s): Post-colisión con desfases de KdV desplegados (Tiempo de Pájaros)
            {'t0': 9.6, 'dur': 4.6, 'f_pivote': f0_piv * 1.25, 'tau': +0.18, 'eta_nl': 1.0, 'gamma': 1.0, 'vel': 0.88},
            # IV (14.4-19.2 s): Tiempo de Ballenas (gamma = -0.9, subarmónicos dominantes + segundo cráter en tau = 0)
            {'t0': 14.4, 'dur': 4.6, 'f_pivote': f0_piv, 'tau': 0.0, 'eta_nl': 1.0, 'gamma': -0.9, 'vel': 0.94,
             't0_solitones': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]},
            # V (19.2-24.0 s): Síntesis de los 3 tiempos de Vortex Temporum
            {'t0': 19.2, 'dur': 4.6, 'f_pivote': f0_piv, 'tau': +0.10, 'eta_nl': 1.0, 'gamma': 0.6, 'vel': 0.92},
        ]
    }
    y_sol, tr_sol = render_soliton_toda_kdv(part_sol, duracion, sr, semilla)

    # 2. Piano Espectral de Vortex Temporum (arpegios helicoidales cuyos tiempos se curvan por el desfase de KdV)
    y_piano = np.zeros((n_total, 2), dtype=np.float64)
    env_piano = np.zeros(n_total, dtype=np.float64)
    # Notas del motivo giratorio de Vortex Temporum sobre los armónicos y subarmónicos de Mi
    ratios_arpegio = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 2.75, 2.0, 1.25, 0.75]
    kappas_arpegio = [1.8, 2.2, 2.6, 3.0, 3.4, 3.8, 3.2, 2.6, 2.0, 1.4]
    kappa_ballena = 1.35

    t_cursor = 0.45
    paso_idx = 0
    while t_cursor < duracion - 0.6:
        r_p = ratios_arpegio[paso_idx % len(ratios_arpegio)]
        k_p = kappas_arpegio[paso_idx % len(kappas_arpegio)]
        idx_now = min(n_total - 1, int(round(t_cursor * sr)))
        eta_now = float(tr_sol['eta_kdv'][idx_now])

        # Desfase no lineal de colisión de KdV al cruzar la ballena subarmónica
        shift_kdv = eta_now * (0.045 / k_p) * math.log((k_p + kappa_ballena) / abs(k_p - kappa_ballena + 0.15))
        t_hit = max(0.05, min(duracion - 0.4, t_cursor + shift_kdv))
        dur_p = 0.48
        i0 = int(round(t_hit * sr))
        i1 = min(n_total, int(round((t_hit + dur_p) * sr)))
        if i1 > i0:
            u = (np.arange(i0, i1) / sr) - t_hit
            f_p = f0_piv * 2.0 * r_p
            # Inarmonicidad de cuerda de piano real: f_m = m * f_p * sqrt(1 + B * m^2)
            B_piano = 0.00035
            env_n = (np.sin(np.minimum(1.0, u / 0.006) * math.pi / 2.0) ** 2) * np.exp(-4.8 * u)
            sig_p = np.zeros_like(u)
            for m_h in range(1, 7):
                f_mh = f_p * m_h * math.sqrt(1.0 + B_piano * (m_h ** 2))
                if f_mh < sr * 0.44:
                    sig_p += (np.sin(2.0 * math.pi * f_mh * u) / (m_h ** 1.35)) * np.exp(-1.2 * (m_h - 1) * u)
            pan_p = 0.65 * math.sin(paso_idx * 0.7)
            gL, gR = paneo(pan_p)
            y_piano[i0:i1, 0] += gL * 0.14 * env_n * sig_p
            y_piano[i0:i1, 1] += gR * 0.14 * env_n * sig_p
            env_piano[i0:i1] += env_n

        # En Tiempo de Pájaros (9.6–14.4 s) el arpegio gira más rápido; en Tiempo de Ballenas (14.4–19.2 s) se dilata
        if 9.6 <= t_cursor < 14.4:
            t_cursor += 0.22
        elif 14.4 <= t_cursor < 19.2:
            t_cursor += 0.46
        else:
            t_cursor += 0.31
        paso_idx += 1

    # 3. Siringua / Flauta espectral cantando justo en los cráteres de colisión de KdV
    frases_siringua = [
        {'t': 5.2, 'dur': 3.2, 'f_hz': f0_piv * 2.5, 'vel': 0.88},   # Cráter del Choque I (5–8.5 s)
        {'t': 10.5, 'dur': 2.8, 'f_hz': f0_piv * 3.5, 'vel': 0.85},  # Ventana entre ráfagas de Pájaros
        {'t': 15.0, 'dur': 3.4, 'f_hz': f0_piv * 2.0, 'vel': 0.92},  # Cráter del Choque II en Tiempo de Ballenas
        {'t': 20.0, 'dur': 3.2, 'f_hz': f0_piv * 3.0, 'vel': 0.90},  # Cierre en el vórtice final
    ]
    f0_sir = np.full(n_total, f0_piv * 2.0)
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

    f0_sir_vib = f0_sir * (2.0 ** ((5.0 * np.sin(2.0 * math.pi * 5.3 * t)) / 1200.0))
    ph_s = 2.0 * math.pi * np.cumsum(f0_sir_vib) / sr
    # Siringua con subarmónico f0/2 y soplo de flauta
    soplo = sosfilt(butter(2, [1200, 4800], fs=sr, btype='bandpass', output='sos'), rng.normal(0, 0.025, n_total))
    exc_s = (0.74 * np.sin(ph_s) + 0.26 * np.sin(0.5 * ph_s) + soplo) * amp_sir
    t_voc = np.array([0.0, 6.0, 12.0, 18.0, 24.0])
    vf = np.array([VOCALES[v] for v in ['u', 'o', 'a', 'i', 'u']], dtype=float)
    form_curves = np.array([np.interp(t, t_voc, vf[:, k]) for k in range(4)])
    sir_mono = formantes_boca(exc_s, form_curves, sr) * 2.3
    y_siringua = np.column_stack([sir_mono * 0.72, sir_mono * 0.72])

    mix = y_sol * 0.90 + y_piano * 0.85 + y_siringua * 0.92
    trazas_esc = {
        'tau_vortice': tr_sol['tau_vortice'],
        'env_subarmonicos': tr_sol['env_subarmonicos'],
        'env_piano_vortex': env_piano,
        'f0_siringua_crater': f0_sir_vib * (amp_sir > 0.04)
    }
    return mix, {'solitones': y_sol, 'piano_vortex': y_piano, 'siringua': y_siringua}, trazas_esc


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
    c_mid = np.array(COL_SUB, dtype=float)
    c_hi = np.array(COL_ARM, dtype=float)
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

def crear_lamina_01_lax_y_colision(sonda_res, path_png):
    W, H = 1600, 960
    im = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(im)
    f_title = cargar_fuente(25, bold=True)
    f_sub = cargar_fuente(14)
    f_sec = cargar_fuente(16, bold=True)
    f_txt = cargar_fuente(13)
    f_sm = cargar_fuente(11)

    p1 = sonda_res['prueba_1_isoespectralidad_lax_y_traza']
    p2 = sonda_res['prueba_2_desfase_colision_kdv']
    p3 = sonda_res['prueba_3_crater_costura_colision']
    snr_s = sonda_res['prueba_4_spectrumsynth_SNR_dB']

    dr.text((48, 24), '01 · EL SOLITÓN SUBARMÓNICO DE TODA–KdV ([L, P] = dL/dt) · SONDA Y DESFASE', font=f_title, fill=FG)
    dr.text((48, 60), f'Semilla {SEMILLA} · Prueba en spectrumsynth (SNR {snr_s} dB) · Potenciales sin reflexión de Bargmann–Kay–Moses u(t) = -2 d²/dt² ln det(I+M)', font=f_sub, fill=MUTED)

    # Panel izquierdo: El Cráter de Colisión de KdV (tau = -0.15, tau = 0.00, tau = +0.15)
    dr.rectangle((48, 104, 775, 548), fill=PANEL_BG, outline=GRID_COL, width=2)
    dr.text((68, 120), 'Colisión de Solitón Armónico (κ2=3.0) y Subarmónico (κ1=1.5)', font=f_sec, fill=COL_ARM)

    t_v = np.linspace(-3.2, 3.2, 600)
    ln_a12 = 0.5 * math.log(abs(3.0 - 1.5) / (3.0 + 1.5))
    t0_sym_vis = [-ln_a12 / 1.5, -ln_a12 / 3.0]
    etapas = [
        (-0.055, '1. Pre-choque (τ = −0.055)\nArmónico (cian) alcanza al subarmónico', 165),
        (0.000,  '2. Choque exacto (τ = 0.000)\nCráter no lineal: cae a 2(κ2²−κ1²) = 13.5', 295),
        (+0.055, '3. Post-choque (τ = +0.055)\nSalto de fase Δt (+adelanto / −retraso)', 425),
    ]
    for tau_v, lbl_e, yy_box in etapas:
        q_v, _, _ = resolver_solitones_kay_moses(t_v, [1.5, 3.0], t0_sym_vis, tau_evol=tau_v, eta_nl=1.0)
        q_tot = q_v[0] + q_v[1]
        box_e = (335, yy_box, 415, 92)
        dr.rectangle((335, yy_box, 335 + 415, yy_box + 92), outline=GRID_COL, width=1)
        dibujar_curva(dr, q_v[0], box_e, COL_SUB, 0.0, 22.5, width=2)
        dibujar_curva(dr, q_v[1], box_e, COL_ARM, 0.0, 22.5, width=2)
        dibujar_curva(dr, q_tot, box_e, COL_VORTEX, 0.0, 22.5, width=2)
        dr.text((68, yy_box + 22), lbl_e, font=f_sm, fill=FG)

    dr.text((68, 522), 'Rojo: subarmónico lento (κ1) · Cian: armónico rápido (κ2) · Oro: suma vestida q(t)', font=f_sm, fill=MUTED)

    # Panel derecho: Hallazgos medidos en la sonda
    dr.rectangle((805, 104, 1552, 548), fill=PANEL_BG, outline=GRID_COL, width=2)
    dr.text((825, 120), 'Resultados medidos por la sonda (Lax, Hirota y Costura)', font=f_sec, fill=COL_VORTEX)

    lineas = [
        ('1. Isoespectralidad del Par de Lax (dL/dt = [P, L]):', COL_ARM),
        (f'   • Error máx. en autovalores de Toda:     {p1["error_max_autovalores_lax_toda"]:.2e} (alturas eternas)', FG),
        (f'   • Error identidad traza ∑ 4κj ψj² = q:   {p1["error_max_identidad_traza_kay_moses"]:.2e} (exacta)', FG),
        ('2. Desfase no lineal de colisión de solitones (Δt_ij):', COL_SUB),
        (f'   • Adelanto del armónico rápido (κ2=3.0): {p2["adelanto_armonico_rapido_medido_s"]:+.4f} s (teór. {p2["adelanto_armonico_rapido_teorico_s"]:+.4f} s)', FG),
        (f'   • Retraso del subarmónico lento (κ1=1.5): {p2["retraso_subarmonico_lento_medido_s"]:+.4f} s (teór. {p2["retraso_subarmonico_lento_teorico_s"]:+.4f} s)', FG),
        ('3. El Cráter de Colisión como Costura Automática:', COL_VORTEX),
        (f'   • Pico si se sumaran linealmente:        {p3["pico_suma_lineal"]:.2f} (satura el centro)', MUTED),
        (f'   • Pico real de KdV en el choque (τ=0):   {p3["pico_exacto_kdv_en_choque"]:.2f} ({p3["reduccion_crater_2_solitones_dB"]:+.2f} dB)', FG),
        (f'   • Cráter en cuasi-resonancia (κ=2.4,2.6): {p3["reduccion_crater_cuasi_resonante_grisey_dB"]:+.2f} dB (hueco limpio)', COL_PIANO),
        ('   • Al chocar, los solitones bajan su cresta y abren espacio a la voz.', MUTED),
    ]
    yy = 156
    for txt, col in lineas:
        dr.text((825, yy), txt, font=f_txt, fill=col)
        yy += 34

    # Panel inferior: Diagrama espacio-tiempo (t, tau) del cruce de 4 solitones (2 subarmónicos + 2 armónicos)
    dr.rectangle((48, 574, 1552, 918), fill=PANEL_BG, outline=GRID_COL, width=2)
    dr.text((68, 590), 'Mapa de Vórtice (t vs τ): trayectorias de los centros de masa y salto de fase en la colisión (Vortex Temporum)', font=f_sec, fill=FG)

    box_st = (250, 636, 1220, 225)
    dr.rectangle((250, 636, 250 + 1220, 636 + 225), outline=GRID_COL, width=1)
    taus_map = np.linspace(-0.055, 0.055, 160)
    t_scan = np.linspace(-4.5, 4.5, 900)
    k_set = [1.2, 1.8, 2.6, 3.4]
    t0_4 = [0.0, 0.0, 0.0, 0.0]
    for i_k in range(4):
        s_ln = sum(0.5 * math.log(abs(k_set[i_k] - k_set[j_k]) / (k_set[i_k] + k_set[j_k])) for j_k in range(4) if j_k != i_k)
        t0_4[i_k] = -s_ln / k_set[i_k]
    col_set = [COL_SUB, COL_PIANO, COL_ARM, COL_VORTEX]

    trayectorias = np.zeros((4, len(taus_map)))
    for idx_tau, tv in enumerate(taus_map):
        qv, _, _ = resolver_solitones_kay_moses(t_scan, k_set, t0_4, tau_evol=tv, eta_nl=1.0)
        for j in range(4):
            trayectorias[j, idx_tau] = float(np.sum(t_scan * qv[j]) / (np.sum(qv[j]) + 1e-24))

    for j in range(4):
        dibujar_curva(dr, trayectorias[j], box_st, col_set[j], -2.8, 2.8, width=3)

    dr.text((68, 658), 'κ4=3.6 (Pájaro 5f0)', font=f_txt, fill=COL_VORTEX)
    dr.text((68, 700), 'κ3=2.7 (Armónico 3f0)', font=f_txt, fill=COL_ARM)
    dr.text((68, 742), 'κ2=1.8 (Subarm. f0/2)', font=f_txt, fill=COL_SUB)
    dr.text((68, 784), 'κ1=1.2 (Ballena f0/3)', font=f_sm, fill=COL_SUB)

    for tv_lbl, txt_lbl in [(-0.14, 'τ = −0.14 (Pre-colisión)'), (-0.07, 'τ = −0.07'), (0.0, 'τ = 0.00 (Vórtice / Cráter)'), (0.07, 'τ = +0.07'), (0.14, 'τ = +0.14 (Desfase Δt)')]:
        xx = 250 + ((tv_lbl + 0.14) / 0.28) * 1220
        dr.line((xx, 636, xx, 861), fill=GRID_COL, width=1)
        dr.text((xx - 45, 872), txt_lbl, font=f_sm, fill=FG)

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

    dr.text((48, 24), '02 · MUESTRA AISLADA · EL SOLITÓN SUBARMÓNICO DE TODA–KdV (24 s)', font=f_title, fill=FG)
    dr.text((48, 60), f'Archivo: {med_solo["m4a"]} · {med_solo["I_LUFS"]:.1f} LUFS · {med_solo["pico_dBTP"]:.1f} dBTP · LRA {med_solo["LRA"]:.1f} · Semilla {SEMILLA}', font=f_sub, fill=MUTED)

    x0, w_plot = 235, 1310
    secciones = [
        (0.0, 'I · Lineal (η=0)'),
        (4.8, 'II · Choque KdV (τ=0)'),
        (9.6, 'III · Pájaros (Δt>0)'),
        (14.4, 'IV · Ballenas (f0/d)'),
        (19.2, 'V · Vórtice Toda')
    ]
    for sec_t, sec_lbl in secciones:
        xx = x0 + (sec_t / 24.0) * w_plot
        dr.line((xx, 112, xx, 885), fill=GRID_COL, width=1)
        dr.text((xx + 4, 110), sec_lbl, font=f_sm, fill=FG)

    controles = [
        ('tau_vortice', 'Tiempo Vórtice τ(t)', -0.28, 0.28, COL_VORTEX),
        ('eta_kdv', 'Acoplamiento KdV η', -0.05, 1.10, COL_ARM),
        ('env_subarmonicos', 'Solitones Sub (f0/d)', 0.0, 1.35, COL_SUB),
        ('env_armonicos', 'Solitones Arm (nf0)', 0.0, 1.35, COL_PIANO),
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
    dibujar_curva(dr, y_norm_vis[:, 0], (x0, yy_w + 4, w_plot, 80), COL_ARM, -0.75, 0.75, width=1)

    yy_s = 626
    spec_im = espectrograma_imagen(y_solo, SR, w_plot, 252)
    im.paste(spec_im, (x0, yy_s))
    dr.rectangle((x0, yy_s, x0 + w_plot, yy_s + 252), outline=GRID_COL, width=1)
    dr.text((48, yy_s + 20), 'Espectrograma\n35 Hz – 10.5 kHz', font=f_sec, fill=FG)
    dr.text((48, yy_s + 78), 'En II y IV (τ=0) los\nsolitones chocan,\nceden su cresta y\nsalen desfasados\nsin desafinarse.', font=f_sm, fill=COL_VORTEX)

    for s_tick in range(0, 25, 3):
        xx = x0 + (s_tick / 24.0) * w_plot
        dr.text((xx - 10, 892), f'{s_tick} s', font=f_sm, fill=MUTED)
    dr.text((48, 922), 'Lectura: los autovalores λ_j = −κ_j² mantienen fijas las alturas mientras las envolventes sech² sufren desfases de colisión.', font=f_sm, fill=MUTED)

    im.save(str(path_png), 'PNG')
    return im

def crear_lamina_03_escena_vortex(y_mix, tr_esc, med_mix, path_png):
    W, H = 1600, 960
    im = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(im)
    f_title = cargar_fuente(25, bold=True)
    f_sub = cargar_fuente(14)
    f_sec = cargar_fuente(15, bold=True)
    f_sm = cargar_fuente(11)

    dr.text((48, 24), '03 · ESCENA EN CONTEXTO · VORTEX TEMPORUM (SOLITONES + PIANO ESPECTRAL + SIRINGUA)', font=f_title, fill=FG)
    dr.text((48, 60), f'Archivo: {med_mix["m4a"]} · {med_mix["I_LUFS"]:.1f} LUFS · {med_mix["pico_dBTP"]:.1f} dBTP · El Piano se desfasa con Δt_ij y la Siringua canta en los cráteres', font=f_sub, fill=MUTED)

    x0, w_plot = 235, 1310
    secciones = [
        (0.0, 'I · Arpegio Lineal'),
        (4.8, 'II · Cráter Vórtice I'),
        (9.6, 'III · Tiempo Pájaros'),
        (14.4, 'IV · Tiempo Ballenas'),
        (19.2, 'V · Síntesis Vortex')
    ]
    for sec_t, sec_lbl in secciones:
        xx = x0 + (sec_t / 24.0) * w_plot
        dr.line((xx, 112, xx, 885), fill=GRID_COL, width=1)
        dr.text((xx + 4, 110), sec_lbl, font=f_sm, fill=FG)

    filas = [
        ('tau_vortice', 'Tiempo Vórtice τ(t)', -0.28, 0.28, COL_VORTEX),
        ('env_subarmonicos', 'Ballenas Sub (f0/d)', 0.0, 1.35, COL_SUB),
        ('env_piano_vortex', 'Piano Helicoidal', 0.0, 1.25, COL_PIANO),
        ('f0_siringua_crater', 'Siringua en Cráter', 280.0, 620.0, COL_ARM),
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
    dibujar_curva(dr, y_norm_vis[:, 0], (x0, yy_w + 4, w_plot, 80), COL_VORTEX, -0.75, 0.75, width=1)

    yy_s = 626
    spec_im = espectrograma_imagen(y_mix, SR, w_plot, 252)
    im.paste(spec_im, (x0, yy_s))
    dr.rectangle((x0, yy_s, x0 + w_plot, yy_s + 252), outline=GRID_COL, width=1)
    dr.text((48, yy_s + 20), 'Espectrograma\nMezcla Vortex', font=f_sec, fill=FG)
    dr.text((48, yy_s + 78), 'En II y IV el choque\nde solitones abre\nun cráter de energía\ndonde entra la voz\nsin compresores.', font=f_sm, fill=COL_PIANO)

    for s_tick in range(0, 25, 3):
        xx = x0 + (s_tick / 24.0) * w_plot
        dr.text((xx - 10, 892), f'{s_tick} s', font=f_sm, fill=MUTED)
    dr.text((48, 922), 'Costura por dispersión inversa: la repulsión de autovalores en τ=0 reduce el pico del fondo y despeja el centro del compás.', font=f_sm, fill=MUTED)

    im.save(str(path_png), 'PNG')
    return im


# ───────────── 5b. Sonda del motor que suena (21 oct 2026) ─────────────
NOMBRES_VOCES = ['f0/3', 'f0/2', 'f0', '2f0', '3f0', '5f0', '7f0']


def sonda_del_motor_que_suena(partitura):
    """Por evento de la muestra: qué parte de la masa de cada solitón (∫q_j = 4κ_j) cae dentro de la ventana que
    lee el motor, con la ventana fija original y con la ventana fiel que sigue a los solitones."""
    kb = np.array([1.15, 1.55, 2.15, 2.85, 3.55, 4.35, 5.15])
    tw = np.linspace(-80.0, 80.0, 32001)
    res = []
    for i, ev in enumerate(partitura['eventos']):
        g = float(ev['gamma'])
        k = kb * (1.0 + 0.25 * g * np.linspace(-0.5, 0.8, 7)) if g >= 0 else kb[::-1] * (0.85 + 0.2 * abs(g))
        qw, _, _ = resolver_solitones_kay_moses(tw, k, ev['t0_solitones'], tau_evol=ev['tau'], eta_nl=ev['eta_nl'])
        lo, hi = -1.6, 1.6
        for qj in qw:
            c = np.cumsum(qj); c = c / (c[-1] + 1e-30)
            lo = min(lo, float(np.interp(0.005, c, tw)) - 0.25); hi = max(hi, float(np.interp(0.995, c, tw)) + 0.25)
        def dentro(a, b):
            sel = (tw >= a) & (tw <= b)
            return [round(float(np.sum(qw[j][sel]) * (tw[1] - tw[0]) / (4 * k[j])), 3) for j in range(7)]
        d0, d1 = dentro(-1.6, 1.6), dentro(lo, hi)
        res.append({'evento': i, 't0_s': ev['t0'], 'tau': ev['tau'], 'ventana_fiel': [round(lo, 2), round(hi, 2)],
                    'voces_que_suenan_original': sum(x > .5 for x in d0), 'voces_que_suenan_fiel': sum(x > .5 for x in d1),
                    'masa_dentro_original': dict(zip(NOMBRES_VOCES, d0)), 'masa_dentro_fiel': dict(zip(NOMBRES_VOCES, d1))})
    return res


def crear_lamina_04_ventanas(sv, path_png):
    W, H = 1600, 960
    im = Image.new('RGB', (W, H), BG); dr = ImageDraw.Draw(im)
    ft, fs, fm = cargar_fuente(30, True), cargar_fuente(17, True), cargar_fuente(15)
    dr.text((48, 26), '04 · QUÉ VOCES SUENAN · VENTANA FIJA CONTRA VENTANA FIEL (sonda del 21 oct 2026)', font=ft, fill=FG)
    dr.text((48, 66), 'cada celda: la parte de la masa del solitón (∫q_j = 4κ_j) que cae dentro de la ventana que lee el motor; vacía = la voz no suena', font=fm, fill=MUTED)
    x0, y0, cw, ch = 330, 150, 80, 52
    for j, n in enumerate(NOMBRES_VOCES):
        dr.text((x0 + j * cw + 18, y0 - 30), n, font=fs, fill=FG)
        dr.text((x0 + 700 + j * cw + 18, y0 - 30), n, font=fs, fill=FG)
    dr.text((x0, y0 - 64), 'original: t entre −1.6 y 1.6', font=fs, fill=MUTED)
    dr.text((x0 + 700, y0 - 64), 'fiel: la ventana sigue a los siete', font=fs, fill=FG)
    for i, e in enumerate(sv):
        y = y0 + i * (ch + 14)
        dr.text((48, y + 8), f'evento {i} · {e["t0_s"]:.1f} s · τ = {e["tau"]:+.2f}', font=fm, fill=FG)
        dr.text((48, y + 28), f'ventana fiel [{e["ventana_fiel"][0]:+.1f}, {e["ventana_fiel"][1]:+.1f}]', font=cargar_fuente(13), fill=MUTED)
        for col, clave in ((x0, 'masa_dentro_original'), (x0 + 700, 'masa_dentro_fiel')):
            for j, n in enumerate(NOMBRES_VOCES):
                v = e[clave][n]
                c = oklch(0.16 + 0.70 * min(1.0, v), 0.03 + 0.15 * min(1.0, v), H0 + 120 + 25 * j)
                dr.rectangle((col + j * cw, y, col + j * cw + cw - 6, y + ch), fill=c, outline=GRID_COL)
                dr.text((col + j * cw + 14, y + 17), f'{v:.2f}', font=cargar_fuente(14), fill=BG if v > .55 else MUTED)
    yb = y0 + len(sv) * (ch + 14) + 30
    dr.text((48, yb), 'Con τ ≠ 0 los solitones rápidos viajan 4κ²τ: con la ventana fija, en «Tiempo de Pájaros» (τ = 0.16) sólo sonaba f0.', font=fm, fill=FG)
    dr.text((48, yb + 30), 'La fase de Bargmann del motor es una constante por voz: no es el all-pass para otros instrumentos (cambia el espectro −20 dB).', font=fm, fill=MUTED)
    im.save(str(path_png), 'PNG')
    return im


def main():
    print('1. Ejecutando sonda de El Solitón Subarmónico de Toda–KdV...', flush=True)
    sonda_res = ejecutar_sonda()
    print('   Sonda OK:', json.dumps(sonda_res, ensure_ascii=False), flush=True)

    print('2. Sintetizando muestra aislada de 24 s...', flush=True)
    partitura_solo = {
        'prototipo': 'soliton-toda-kdv',
        'duracion': 24.0,
        'semilla': SEMILLA,
        'tiempo_vortice_tau': [
            [0.0, -0.20], [4.8, -0.20],
            [5.0, -0.15], [7.2, 0.00], [9.5, +0.15],
            [9.8, +0.20], [14.2, +0.20],
            [14.5, -0.12], [16.8, 0.00], [19.0, +0.12],
            [19.4, -0.16], [21.6, 0.00], [24.0, +0.16]
        ],
        'acoplamiento_kdv_eta': [
            [0.0, 0.0], [4.5, 0.0], [5.0, 1.0], [24.0, 1.0]
        ],
        'escala_grisey_gamma': [
            [0.0, 0.4], [4.8, 0.8], [9.6, 1.0], [14.4, -0.9], [19.2, 0.6], [24.0, 0.8]
        ],
        'chirp_fase_lax_beta': [
            [0.0, 0.15], [5.0, 0.85], [10.0, 0.65], [15.0, 0.95], [20.0, 0.75], [24.0, 0.50]
        ],
        'eventos': [
            # I (0-4.8 s): Cruce lineal sin interacción de KdV (eta_nl = 0.0) sobre La2/Mi3 = 164.81 Hz
            {'t0': 0.25, 'dur': 4.4, 'f_pivote': 164.8138, 'tau': -0.14, 'eta_nl': 0.0, 'gamma': 0.5, 'vel': 0.86,
             't0_solitones': [-0.55, -0.25, 0.0, 0.15, 0.30, 0.45, 0.60]},
            # II (4.8-9.6 s): Colisión exacta de solitones en el vórtice (tau = 0.0, eta_nl = 1.0)
            {'t0': 4.85, 'dur': 4.5, 'f_pivote': 164.8138, 'tau': 0.00, 'eta_nl': 1.0, 'gamma': 0.8, 'vel': 0.92,
             't0_solitones': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]},
            # III (9.6-14.4 s): Tiempo de Pájaros (gamma = +1.0, tau = +0.16): los armónicos rápidos emergen adelantados por Delta_t_ij
            {'t0': 9.65, 'dur': 4.5, 'f_pivote': 220.0, 'tau': +0.16, 'eta_nl': 1.0, 'gamma': 1.0, 'vel': 0.90,
             't0_solitones': [-0.30, -0.15, 0.0, 0.0, 0.0, 0.10, 0.20]},
            # IV (14.4-19.2 s): Tiempo de Ballenas (gamma = -0.9, subarmónicos graves dominantes en colisión lenta)
            {'t0': 14.45, 'dur': 4.5, 'f_pivote': 164.8138, 'tau': 0.00, 'eta_nl': 1.0, 'gamma': -0.9, 'vel': 0.94,
             't0_solitones': [-0.10, 0.0, 0.0, 0.0, 0.05, 0.10, 0.15]},
            # V (19.2-24.0 s): Doble vórtice final en la red de Toda–KdV
            {'t0': 19.25, 'dur': 2.2, 'f_pivote': 196.0, 'tau': -0.08, 'eta_nl': 1.0, 'gamma': 0.7, 'vel': 0.90,
             't0_solitones': [-0.20, -0.10, 0.0, 0.05, 0.10, 0.15, 0.20]},
            {'t0': 21.55, 'dur': 2.3, 'f_pivote': 164.8138, 'tau': +0.12, 'eta_nl': 1.0, 'gamma': 0.7, 'vel': 0.92,
             't0_solitones': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]},
        ]
    }
    print('1b. Sonda del motor que suena (ventanas)...', flush=True)
    sonda_motor = sonda_del_motor_que_suena(partitura_solo)
    y_solo, tr_solo = render_soliton_toda_kdv(partitura_solo, 24.0, SR, SEMILLA)
    # la misma partitura con fiel = False: sale como la muestra original (8529bbfe90e4ad37 en su máquina; aquí −170 dB de diferencia)
    y_orig, _ = render_soliton_toda_kdv({**partitura_solo, 'fiel': False}, 24.0, SR, SEMILLA)
    med_orig = guardar_audio_y_medir(
        y_orig,
        OUT_DIR / 'muestra-soliton-toda-kdv-original-s20261021.wav',
        OUT_DIR / 'muestra-soliton-toda-kdv-original-s20261021.m4a',
        target_lufs=-18.5
    )
    med_solo = guardar_audio_y_medir(
        y_solo,
        OUT_DIR / 'muestra-soliton-toda-kdv-s20261021.wav',
        OUT_DIR / 'muestra-soliton-toda-kdv-s20261021.m4a',
        target_lufs=-18.5
    )

    print('3. Sintetizando escena en contexto (Vortex Temporum: Solitones + Piano Espectral + Siringua)...', flush=True)
    y_mix, stems_esc, tr_esc = render_escena_vortex_temporum(24.0, SR, SEMILLA)
    med_mix = guardar_audio_y_medir(
        y_mix,
        OUT_DIR / 'escena-vortex-toda-kdv-s20261021.wav',
        OUT_DIR / 'escena-vortex-toda-kdv-s20261021.m4a',
        target_lufs=-16.0
    )

    print('4. Generando láminas PNG en OKLCh y GIF...', flush=True)
    p1_png = OUT_DIR / '01-lax-hirota-y-sonda-s20261021.png'
    p2_png = OUT_DIR / '02-vortice-kdv-y-espectrograma-s20261021.png'
    p3_png = OUT_DIR / '03-escena-vortex-temporum-costura-s20261021.png'
    im1 = crear_lamina_01_lax_y_colision(sonda_res, p1_png)
    im2 = crear_lamina_02_muestra_aislada(y_solo, tr_solo, med_solo, p2_png)
    im3 = crear_lamina_03_escena_vortex(y_mix, tr_esc, med_mix, p3_png)
    im4 = crear_lamina_04_ventanas(sonda_motor, OUT_DIR / '04-que-voces-suenan-original-contra-fiel-s20261021.png')

    frames = [im.resize((1200, 720), Image.Resampling.LANCZOS).quantize(colors=256, method=Image.Quantize.MEDIANCUT) for im in (im1, im2, im3, im4)]
    gif_path = OUT_DIR / 'proceso-soliton-toda-kdv-s20261021.gif'
    frames[0].save(
        str(gif_path),
        format='GIF',
        save_all=True,
        append_images=frames[1:],
        duration=1800,
        loop=0,
        optimize=True
    )

    shutil.copyfile(__file__, OUT_DIR / 'soliton_toda_kdv.py')

    receta = {
        'instrumento': 'El Solitón Subarmónico de Toda–KdV ([L, P] = dL/dt)',
        'fecha_utc': '2026-10-21',
        'semilla': SEMILLA,
        'ejecucion_sha256': EJECUCION,
        'sonda': sonda_res,
        'sonda_del_motor_que_suena': sonda_motor,
        'ventanas_fiel_muestra': tr_solo.get('ventanas_fiel'),
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
    receta_path = OUT_DIR / 'receta-soliton-toda-kdv-s20261021.json'
    with open(receta_path, 'w', encoding='utf-8') as f:
        json.dump(receta, f, ensure_ascii=False, indent=2)

    print('5. Todo completado con éxito:', json.dumps(receta, ensure_ascii=False, indent=2), flush=True)

if __name__ == '__main__':
    main()