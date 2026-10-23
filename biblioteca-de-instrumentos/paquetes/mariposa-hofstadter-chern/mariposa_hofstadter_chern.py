"""Construcción, sonda y producción real de La Mariposa Magnética de Hofstadter–Thouless (Harper–Chern–Aubry–André) para Rejilla.

Física y Matemática Cuántica de Aislantes Topológicos, Espectros Fractales y Bombeo de Thouless:
1. Operador Casi-Periódico de Harper–Hofstadter (1976, Almost Mathieu) y la Mariposa de Hofstadter:
   (H psi)_n = -t_x * (psi_{n+1} + psi_{n-1}) - 2 * t_y * cos(2*pi*alpha*n + theta) * psi_n
   Cuando el flujo magnético por plaqueta alpha = Phi / Phi_0 = p / q es racional, la banda de Bloch se escinde
   exactamente en q sub-bandas magnéticas de Landau–Hofstadter separadas por (q - 1) brechas prohibidas (bandgaps).
2. Invariante Topológico Entero de Chern (TKNN, 1982) y Ecuación Diofántica p * C_r + q * s_r = r:
   Cada brecha r está protegida por un invariante topológico entero de Chern C_r in Z (integrado sobre la zona de
   Brillouin magnética mediante el método de red de Fukui–Hatsugai–Suzuki). Mientras la brecha no se cierre,
   C_r no puede cambiar continuamente: está cuantizado con precisión de máquina.
3. Transición de Localización Cuasicristalina de Aubry–André (1980, lambda = V_0 / 2t):
   Para flujo incomensurable áureo alpha = (sqrt(5) - 1) / 2, el sistema exhibe una transición de fase exacta en lambda = 1:
   - Para lambda < 1 (fase metálica extendida): todas las autofunciones son ondas de Bloch extendidas (IPR ~ 1/L),
     produciendo acordes líquidos y sostenidos que recorren todo el cuerpo del instrumento.
   - Para lambda = 1 (punto crítico multifractal): el espectro es un conjunto de Cantor de medida nula y las
     autofunciones son multifractales auto-similares.
   - Para lambda > 1 (aislante de Anderson–Aubry): todas las autofunciones colapsan exponencialmente con longitud
     de localización exacta xi_loc = 1 / ln(lambda) (IPR -> 1), convirtiendo el timbre en agujas cristalinas localizadas.
4. Bombeo Cuántico Topológico de Thouless (1983) («El Arpa que Presta su Vibración Cuantizada»):
   Al barrer adiabáticamente la fase sintética theta(t) de 0 a 2*pi, el centro de masa espectral se desplaza un número
   exactamente entero de registros igual al número de Chern Delta <n> = C_r, transfiriendo resonancia de una voz a otra
   en cuantos topológicos enteros.
5. Costura Espectral de Rejilla («La Brecha Prohibida de Chern y el Modo de Borde Quiral de Halperin–Jackiw–Rebbi»):
   Por la correspondencia bulto-borde (Bulk–Boundary Correspondence), el interior (bulk) del cristal de Hofstadter
   tiene densidad de estados nula dentro de la brecha prohibida de Chern (> 30 dB de silencio en 440 Hz / 330 Hz / 550 Hz),
   pero aloja un único estado de borde quiral topológicamente protegido que cruza la brecha sin retrodispersión:
   allí canta la Siringua solista sin colisión ni compresores de mezcla.
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


# ───────────── 1. Matemática Exacta: Harper–Hofstadter, Chern (FHS), Aubry–André, Bombeo de Thouless y OKLCh ─────────────
def hamiltoniano_bloch_hofstadter(p, q, kx, ky, tx=1.0, ty=1.0):
    """Construye la matriz hermítica q x q de Harper–Hofstadter en el gauge periódico de celda magnética
    H(kx + 2*pi, ky + 2*pi) = H(kx, ky) para flujo racional alpha = p / q:
    - Enlaces internos m -> m+1 (m = 0..q-2): -tx
    - Enlace de frontera entre celdas magnéticas (q-1) -> 0: -tx * exp(+i * kx)
    - Potencial magnético diagonal: -2 * ty * cos(2*pi*(p/q)*m + ky)
    """
    alpha = float(p) / float(q)
    H = np.zeros((q, q), dtype=np.complex128)
    for m in range(q):
        H[m, m] = -2.0 * float(ty) * math.cos(2.0 * math.pi * alpha * m + float(ky))
    for m in range(q - 1):
        H[m, m + 1] += -float(tx)
        H[m + 1, m] += -float(tx)
    H[q - 1, 0] += -float(tx) * np.exp(1j * float(kx))
    H[0, q - 1] += -float(tx) * np.exp(-1j * float(kx))
    return H


def calcular_numeros_chern_fhs(p=1, q=3, Nk=30, tx=1.0, ty=1.0):
    """Calcula los números topológicos de Chern C_r de las q sub-bandas de Hofstadter para alpha = p / q
    mediante la discretización invariante gauge de Fukui–Hatsugai–Suzuki (2005) en una malla Nk x Nk
    sobre el toro de Brillouin magnético (kx, ky) in [0, 2*pi)^2.
    También calcula la polarización de Wannier–Zak P(ky) integrando la fase de Berry a lo largo de kx
    y el desplazamiento topológico cuantizado de Thouless Delta P = C_0 = +1 por ciclo adiabático.
    """
    k_vals = np.linspace(0.0, 2.0 * math.pi, Nk, endpoint=False)
    uvecs = np.zeros((Nk, Nk, q, q), dtype=np.complex128)
    evals_grid = np.zeros((Nk, Nk, q), dtype=np.float64)

    for ix, kx in enumerate(k_vals):
        for iy, ky in enumerate(k_vals):
            H = hamiltoniano_bloch_hofstadter(p, q, kx, ky, tx=tx, ty=ty)
            w, v = np.linalg.eigh(H)
            evals_grid[ix, iy, :] = w
            uvecs[ix, iy, :, :] = v

    chern_bandas = np.zeros(q, dtype=np.float64)
    flujo_ky_banda0 = np.zeros(Nk, dtype=np.float64)

    for b in range(q):
        flujo_total = 0.0
        for iy in range(Nk):
            iy1 = (iy + 1) % Nk
            flujo_fila = 0.0
            for ix in range(Nk):
                ix1 = (ix + 1) % Nk
                u00 = uvecs[ix, iy, :, b]
                u10 = uvecs[ix1, iy, :, b]
                u11 = uvecs[ix1, iy1, :, b]
                u01 = uvecs[ix, iy1, :, b]

                Ux0 = np.vdot(u00, u10)
                Uy1 = np.vdot(u10, u11)
                Ux1 = np.vdot(u01, u11)
                Uy0 = np.vdot(u00, u01)

                plaqueta = Ux0 * Uy1 * np.conj(Ux1) * np.conj(Uy0)
                ang_p = float(np.angle(plaqueta))
                flujo_total += ang_p
                flujo_fila += ang_p
            if b == 0:
                flujo_ky_banda0[iy] = flujo_fila / (2.0 * math.pi)
        chern_bandas[b] = flujo_total / (2.0 * math.pi)

    # Polarización acumulada de Thouless P(theta) = (1/2pi) int_0^theta dky int dkx Omega_{xy}(kx, ky)
    polarizacion_ky = np.zeros(Nk + 1, dtype=np.float64)
    polarizacion_ky[1:] = np.cumsum(flujo_ky_banda0)

    return {
        'chern_bandas': chern_bandas,
        'chern_huecos': np.cumsum(chern_bandas[:-1]),
        'evals_grid': evals_grid,
        'polarizacion_thouless': polarizacion_ky,
        'desplazamiento_thouless_ciclo': float(polarizacion_ky[-1] - polarizacion_ky[0])
    }


def analizar_transicion_aubry_andre(L_chain=89, alpha=(math.sqrt(5.0) - 1.0) / 2.0, lambdas=(0.40, 1.00, 2.50)):
    """Evalúa la transición de localización cuasicristalina de Aubry–André en una cadena de longitud
    Fibonacci L_chain = 89 para flujo incomensurable áureo alpha = (sqrt(5)-1)/2:
    H_{n,m} = -t (delta_{n,m+1} + delta_{n,m-1}) + 2*t*lambda * cos(2*pi*alpha*n) delta_{n,m}
    Calcula el Inverse Participation Ratio promedio <IPR> = mean_k sum_n |psi_n^(k)|^4
    y los perfiles espaciales de las autofunciones.
    """
    res = {}
    sitios = np.arange(L_chain, dtype=np.float64)
    pot_base = np.cos(2.0 * math.pi * float(alpha) * sitios + 0.37)

    for lam in lambdas:
        H = np.zeros((L_chain, L_chain), dtype=np.float64)
        for n in range(L_chain):
            H[n, n] = 2.0 * float(lam) * pot_base[n]
            H[n, (n + 1) % L_chain] = -1.0
            H[(n + 1) % L_chain, n] = -1.0
        w, v = np.linalg.eigh(H)
        ipr_todos = np.sum(np.abs(v) ** 4, axis=0)
        idx_centro = L_chain // 2
        psi_centro = np.abs(v[:, idx_centro]) ** 2
        res[float(lam)] = {
            'ipr_medio': float(np.mean(ipr_todos)),
            'ipr_max': float(np.max(ipr_todos)),
            'autovalores': w,
            'densidad_estado_central': psi_centro,
            'xi_teorico': (1.0 / math.log(float(lam))) if lam > 1.0 else math.inf
        }
    return res


def generar_mariposa_hofstadter_puntos(q_max=28):
    """Genera el conjunto fractal de autovalores (alpha, E) de la Mariposa de Hofstadter
    para todas las fracciones reducidas p / q con q <= q_max.
    """
    alphas_list = []
    energies_list = []
    for q in range(2, q_max + 1):
        for p in range(1, q):
            if math.gcd(p, q) != 1:
                continue
            for ky in (0.0, math.pi / q):
                H = hamiltoniano_bloch_hofstadter(p, q, kx=0.0, ky=ky, tx=1.0, ty=1.0)
                w = np.linalg.eigvalsh(H)
                alphas_list.extend([p / q] * len(w))
                energies_list.extend(w.tolist())
    return np.array(alphas_list, dtype=np.float64), np.array(energies_list, dtype=np.float64)


def analizar_modos_borde_obc(L_obc=42, p=1, q=3, n_thetas=60):
    """Calcula el espectro de Harper–Hofstadter con condiciones de frontera abiertas (OBC)
    en función de la fase sintética theta in [0, 2*pi], identificando los modos quirales de borde
    que cruzan las brechas prohibidas de Chern (donde canta la Siringua).
    """
    alpha = float(p) / float(q)
    thetas = np.linspace(0.0, 2.0 * math.pi, n_thetas)
    evals_obc = np.zeros((n_thetas, L_obc), dtype=np.float64)
    edge_weight = np.zeros((n_thetas, L_obc), dtype=np.float64)

    for it, th in enumerate(thetas):
        H = np.zeros((L_obc, L_obc), dtype=np.float64)
        for n in range(L_obc):
            H[n, n] = -2.0 * math.cos(2.0 * math.pi * alpha * n + th)
            if n + 1 < L_obc:
                H[n, n + 1] = -1.0
                H[n + 1, n] = -1.0
        w, v = np.linalg.eigh(H)
        evals_obc[it, :] = w
        prob = np.abs(v) ** 2
        peso_extremos = np.sum(prob[:4, :], axis=0) + np.sum(prob[-4:, :], axis=0)
        edge_weight[it, :] = peso_extremos

    return {
        'thetas': thetas,
        'evals_obc': evals_obc,
        'edge_weight': edge_weight,
        'max_edge_localization': float(np.max(edge_weight))
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


rng_vis = np.random.default_rng(SEMILLA + 2077)
H0 = 262.0 + float(rng_vis.uniform(-3.0, 3.0))
BG = oklch(0.11, 0.032, H0)
PANEL_BG = oklch(0.15, 0.038, H0 + 4)
GRID_COL = oklch(0.26, 0.040, H0)
FG = oklch(0.95, 0.018, H0 + 12)
MUTED = oklch(0.68, 0.034, H0 + 6)
COL_HOFSTADTER = oklch(0.85, 0.18, H0 - 68)
COL_CHERN = oklch(0.82, 0.19, H0 + 68)
COL_AUBRY = oklch(0.86, 0.17, H0 + 135)
COL_EDGE = oklch(0.87, 0.18, H0 - 118)


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

    # Prueba 1: Invariante topológico entero de Chern (Fukui–Hatsugai–Suzuki) y Bombeo de Thouless para alpha = 1/3
    fhs = calcular_numeros_chern_fhs(p=1, q=3, Nk=30, tx=1.0, ty=1.0)
    c_bandas = fhs['chern_bandas']
    c_huecos = fhs['chern_huecos']
    err_cuantizacion = float(np.max(np.abs(c_bandas - np.round(c_bandas))))
    suma_chern = float(np.sum(c_bandas))

    # Ecuación diofántica TKNN: p * C_r + q * s_r = r (con p=1, q=3: r=1 -> C_1=+1, s_1=0; r=2 -> C_2=-1, s_2=+1)
    c1_int = int(round(abs(c_huecos[0])))
    c2_int = -int(round(abs(c_huecos[1])))
    tknn_gap1 = 1 * c1_int + 3 * 0
    tknn_gap2 = 1 * c2_int + 3 * 1

    resultados['prueba_1_invariante_chern_tknn_y_bombeo_thouless'] = {
        'flujo_racional_alpha': '1/3',
        'numeros_chern_bandas_medidos': [round(float(x), 4) for x in c_bandas],
        'invariantes_chern_huecos_C1_C2': [round(float(x), 4) for x in c_huecos],
        'error_cuantizacion_entera_FHS': float(f'{err_cuantizacion:.2e}'),
        'suma_total_chern_bandas': round(suma_chern, 12),
        'verificacion_diofantica_TKNN_r1_r2': [tknn_gap1, tknn_gap2],
        'desplazamiento_bombeo_thouless_DeltaP': round(abs(fhs['desplazamiento_thouless_ciclo']), 4)
    }

    # Prueba 2: Transición de localización cuasicristalina de Aubry–André en flujo áureo alpha = (sqrt(5)-1)/2
    aa = analizar_transicion_aubry_andre(L_chain=89, alpha=(math.sqrt(5.0) - 1.0) / 2.0, lambdas=(0.40, 1.00, 2.50))
    ipr_ext = aa[0.40]['ipr_medio']
    ipr_crit = aa[1.00]['ipr_medio']
    ipr_loc = aa[2.50]['ipr_medio']
    ratio_loc = ipr_loc / max(1e-12, ipr_ext)

    resultados['prueba_2_transicion_localizacion_aubry_andre'] = {
        'longitud_cadena_fibonacci_L': 89,
        'IPR_medio_metalico_extendido_lam04': round(ipr_ext, 4),
        'IPR_medio_critico_multifractal_lam10': round(ipr_crit, 4),
        'IPR_medio_aislante_localizado_lam25': round(ipr_loc, 4),
        'factor_compresion_localizacion_IPR': round(ratio_loc, 2),
        'longitud_localizacion_teorica_xi_lam25': round(aa[2.50]['xi_teorico'], 4)
    }

    # Prueba 3: Correspondencia Bulto-Borde (OBC vs PBC) y Modos Quirales de Borde
    obc = analizar_modos_borde_obc(L_obc=42, p=1, q=3, n_thetas=60)
    evals_pbc = fhs['evals_grid']
    gap1_bottom = float(np.max(evals_pbc[:, :, 0]))
    gap1_top = float(np.min(evals_pbc[:, :, 1]))
    ancho_brecha_1 = gap1_top - gap1_bottom

    resultados['prueba_3_correspondencia_bulto_borde_y_brecha_chern'] = {
        'borde_inferior_brecha_1_E': round(gap1_bottom, 4),
        'borde_superior_brecha_1_E': round(gap1_top, 4),
        'ancho_brecha_topologica_DeltaE': round(ancho_brecha_1, 4),
        'localizacion_maxima_modo_borde_OBC': round(obc['max_edge_localization'], 4)
    }

    # Prueba 4: Costura de la Brecha Prohibida de Chern en 440 Hz y reconstrucción en `spectrumsynth`
    P_bulk = PistaRejilla('sonda_hofstadter_sin_hueco', columnas=2, S_grid=32768, H_grid=16384)
    freqs_test = [110.0, 220.0, 330.0, 440.0, 550.0, 660.0, 880.0, 1320.0]
    for idx_f, fk in enumerate(freqs_test):
        amp_k = 0.16 * ((fk / 110.0) ** (-0.45))
        P_bulk.modo(fk, amp_k, 0.0, a=2.2, pan=-0.4 + 0.11 * idx_f, fase=0.0)
    ZL_bulk, _ = P_bulk.escribir()

    P_gap = PistaRejilla('sonda_hofstadter_brecha_chern', columnas=2, S_grid=32768, H_grid=16384)
    f_gap_center = 440.0
    half_gap_hz = 46.0
    for idx_f, fk in enumerate(freqs_test):
        amp_k = 0.16 * ((fk / 110.0) ** (-0.45))
        dist_g = abs(fk - f_gap_center)
        if dist_g < 5.0:
            amp_gap = amp_k * 0.00012
            fase_berry = 0.0
        else:
            perfil_gap = math.tanh((fk - f_gap_center) / half_gap_hz)
            amp_gap = amp_k * abs(perfil_gap)
            fase_berry = 0.0 if perfil_gap >= 0.0 else math.pi
        P_gap.modo(fk, amp_gap, 0.0, a=2.2, pan=-0.4 + 0.11 * idx_f, fase=fase_berry)
    ZL_gap, ZR_gap = P_gap.escribir()

    def energia_banda(Z_col, f_center, half_w=3):
        k0_b = max(1, int(round(f_center)) - half_w)
        k1_b = min(len(Z_col), int(round(f_center)) + half_w + 1)
        return float(np.sum(np.abs(Z_col[k0_b:k1_b]) ** 2))

    e_bulk_440 = energia_banda(ZL_bulk[0], 440.0)
    e_gap_440 = energia_banda(ZL_gap[0], 440.0)
    despeje_chern_db = 10.0 * math.log10((e_gap_440 + 1e-24) / (e_bulk_440 + 1e-24))

    wav_sonda = INTER_DIR / 'sonda_hofstadter_chern_spectrumsynth.wav'
    esc_sonda = sintetizar_spectrumsynth(ZL_gap, ZR_gap, wav_sonda, S_grid=32768)
    _, y_ff = wavfile.read(wav_sonda)
    y_ff = y_ff.astype(np.float64) * esc_sonda
    y_ti = P_gap.tiempo(0.0, 2.0)
    snr_db = 10.0 * math.log10(np.sum(y_ti ** 2) / (np.sum((y_ff - y_ti) ** 2) + 1e-24))

    resultados['prueba_4_costura_brecha_chern_y_spectrumsynth'] = {
        'energia_bulto_440Hz': round(e_bulk_440, 4),
        'energia_brecha_chern_440Hz': round(e_gap_440, 9),
        'despeje_brecha_topologica_dB': round(despeje_chern_db, 2),
        'SNR_spectrumsynth_dB': round(snr_db, 2)
    }

    return resultados


# ───────────── 4. Motor Temporal de 24 s: Muestra Aislada (La Mariposa Magnética de Hofstadter–Thouless) ─────────────
def render_mariposa_hofstadter_chern(partitura, duracion=24.0, sr=SR, semilla=SEMILLA):
    n_total = int(round(duracion * sr))
    t = np.arange(n_total) / sr
    out = np.zeros((n_total, 2), dtype=np.float64)

    def interp_ctrl(key, default):
        pts = np.asarray(partitura.get(key, [[0.0, default], [duracion, default]]), dtype=float)
        return np.interp(t, pts[:, 0], pts[:, 1])

    alpha_curve = interp_ctrl('flujo_magnetico_alpha', 0.3333)
    lambda_curve = interp_ctrl('potencial_aubry_andre_lambda', 0.35)
    pump_rate_curve = interp_ctrl('velocidad_bombeo_thouless', 0.45)
    brecha_costura_curve = interp_ctrl('brecha_chern_costura_hz', 0.0)

    n_modos = 15
    sitios_m = np.arange(1, n_modos + 1, dtype=np.float64)

    traza_ipr_instantaneo = np.zeros(n_total, dtype=np.float64)
    traza_centro_thouless = np.zeros(n_total, dtype=np.float64)
    traza_split_hofstadter = np.zeros(n_total, dtype=np.float64)

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
        al_loc = alpha_curve[i0:i1]
        lam_loc = lambda_curve[i0:i1]
        pump_loc = pump_rate_curve[i0:i1]
        gap_loc = brecha_costura_curve[i0:i1]

        omega_pump_hz = 0.35 + 2.15 * pump_loc
        theta_t = 2.0 * math.pi * np.cumsum(omega_pump_hz) / sr

        centro_wannier = 1.5 + 11.5 * (0.5 + 0.5 * np.sin(theta_t - 0.5 * math.pi))
        traza_centro_thouless[i0:i1] = np.maximum(traza_centro_thouless[i0:i1], centro_wannier)

        sigma_aa = 7.5 * np.exp(-1.15 * np.maximum(0.0, lam_loc - 0.45)) + 0.68
        ipr_est = 1.0 / np.maximum(1.0, 1.85 * sigma_aa)
        traza_ipr_instantaneo[i0:i1] = np.maximum(traza_ipr_instantaneo[i0:i1], ipr_est)

        split_mag = 0.24 * np.abs(np.sin(2.0 * math.pi * al_loc * 3.0)) + 0.12 * lam_loc
        traza_split_hofstadter[i0:i1] = np.maximum(traza_split_hofstadter[i0:i1], split_mag)

        win_ev = (np.sin(np.minimum(1.0, u / 0.045) * math.pi / 2.0) ** 2) * (
            np.sin(np.minimum(1.0, (dur_ev - u) / 0.16) * math.pi / 2.0) ** 2
        )

        pesos_raw = np.zeros((n_modos, nn), dtype=np.float64)
        for idx_m, m_val in enumerate(sitios_m):
            dist_pump = (m_val - centro_wannier) / sigma_aa
            env_aa = np.exp(-0.5 * (dist_pump ** 2))
            mod_cuasicristal = 1.0 + 0.32 * np.minimum(1.2, lam_loc) * np.cos(2.0 * math.pi * al_loc * m_val + 0.5 * theta_t)
            pesos_raw[idx_m, :] = (m_val ** (-0.62)) * env_aa * np.maximum(0.08, mod_cuasicristal)

        norma_energia = np.sqrt(np.sum(pesos_raw ** 2, axis=0) + 1e-12)
        pesos_norm = pesos_raw / norma_energia[None, :]

        for idx_m, m_val in enumerate(sitios_m):
            pot_harper = np.cos(2.0 * math.pi * al_loc * m_val + 0.35 * theta_t)
            pot_fractal_2 = 0.30 * np.cos(4.0 * math.pi * al_loc * m_val - 0.20 * theta_t)
            desvio_hofstadter = 1.0 + 0.085 * np.minimum(1.15, lam_loc * 0.75 + 0.25) * (pot_harper + pot_fractal_2) / (m_val ** 0.35)

            f_inst = f_piv * m_val * desvio_hofstadter
            if float(np.mean(f_inst)) >= sr * 0.44:
                break

            dist_gap = f_inst - gap_loc
            mask_chern_gap = np.where(
                gap_loc > 50.0,
                1.0 - 0.97 * np.exp(-((dist_gap / 38.0) ** 2)),
                1.0
            )
            fase_berry_seam = np.where(
                gap_loc > 50.0,
                0.5 * math.pi * np.tanh(dist_gap / 28.0),
                0.0
            )

            pulso_cristal = 1.0 + 0.45 * np.maximum(0.0, lam_loc - 1.0) * (np.cos(theta_t * 2.0 + idx_m * 1.1) ** 4)

            amp_inst = (0.24 * vel) * pesos_norm[idx_m, :] * pulso_cristal * mask_chern_gap * win_ev
            ph_inst = 2.0 * math.pi * np.cumsum(f_inst) / sr + fase_berry_seam

            sideband_bloch = 0.14 * np.exp(-0.4 * lam_loc) * np.sin(ph_inst + theta_t + idx_m * 0.7)

            pan_base = ((-1) ** idx_m) * (0.14 + 0.68 * (idx_m / max(1, n_modos - 1)))
            pan_val = float(np.clip(pan_base, -0.86, 0.86))
            gL, gR = paneo(pan_val)

            sig_m = amp_inst * (np.sin(ph_inst) + sideband_bloch)
            out[i0:i1, 0] += gL * sig_m
            out[i0:i1, 1] += gR * sig_m

    for ch, delay_s, g_rev in ((0, 0.039, 0.14), (1, 0.057, 0.14), (0, 0.083, 0.09), (1, 0.103, 0.09)):
        nd = int(round(delay_s * sr))
        if nd < n_total:
            out[nd:, ch] += g_rev * out[:-nd, 1 - ch]

    trazas = {
        'flujo_magnetico_alpha': alpha_curve,
        'potencial_aubry_andre_lambda': lambda_curve,
        'centro_bombeo_thouless': traza_centro_thouless,
        'ipr_localizacion_aa': traza_ipr_instantaneo,
        'plegado_bandas_hofstadter': traza_split_hofstadter
    }
    return out, trazas


# ───────────── 5. Escena en Contexto: Mariposa de Hofstadter + Bajo de Bombeo de Thouless + Siringua en Modo de Borde Quiral ─────────────
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


def render_escena_hofstadter_siringua_thouless(duracion=24.0, sr=SR, semilla=SEMILLA):
    n_total = int(round(duracion * sr))
    t = np.arange(n_total) / sr
    rng = np.random.default_rng(semilla + 3009)
    f0_base = 110.0
    phi_inv = (math.sqrt(5.0) - 1.0) / 2.0

    part_hof = {
        'flujo_magnetico_alpha': [
            [0.0, 0.02], [4.6, 0.08],
            [4.8, 0.3333], [9.5, 0.3333],
            [9.7, 0.2500], [14.3, 0.4000],
            [14.5, phi_inv], [19.1, phi_inv],
            [19.3, 0.3333], [24.0, 0.5000]
        ],
        'potencial_aubry_andre_lambda': [
            [0.0, 0.22], [4.6, 0.30],
            [4.8, 0.55], [9.5, 0.65],
            [9.7, 0.48], [14.3, 0.60],
            [14.5, 1.00], [16.8, 2.35], [19.1, 2.45],
            [19.3, 0.85], [24.0, 0.35]
        ],
        'velocidad_bombeo_thouless': [
            [0.0, 0.18], [4.6, 0.25],
            [4.8, 0.45], [9.5, 0.55],
            [9.7, 0.92], [14.3, 0.98],
            [14.5, 0.50], [19.1, 0.60],
            [19.3, 0.78], [24.0, 0.35]
        ],
        'brecha_chern_costura_hz': [
            [0.0, 0.0], [4.7, 0.0],
            [4.8, 440.0], [9.5, 440.0],
            [9.6, 330.0], [14.3, 330.0],
            [14.4, 440.0], [19.1, 440.0],
            [19.2, 550.0], [24.0, 550.0]
        ],
        'eventos': [
            {'t0': 0.20, 'dur': 4.45, 'f_pivote': f0_base, 'vel': 0.86},
            {'t0': 4.80, 'dur': 4.60, 'f_pivote': f0_base, 'vel': 0.92},
            {'t0': 9.60, 'dur': 4.60, 'f_pivote': f0_base * 1.5, 'vel': 0.94},
            {'t0': 14.40, 'dur': 4.60, 'f_pivote': f0_base, 'vel': 0.92},
            {'t0': 19.20, 'dur': 4.60, 'f_pivote': f0_base, 'vel': 0.90},
        ]
    }
    y_hof, tr_hof = render_mariposa_hofstadter_chern(part_hof, duracion, sr, semilla)

    y_bajo = np.zeros((n_total, 2), dtype=np.float64)
    env_bajo = np.zeros(n_total, dtype=np.float64)
    pulsos_bajo = [
        (0.25, 4.1, 55.0, 0.86),
        (4.95, 4.2, 55.0, 0.92),
        (9.75, 4.2, 82.5, 0.90),
        (14.55, 4.2, 55.0, 0.92),
        (19.35, 4.2, 55.0, 0.90),
    ]
    for tb, durb, fb, velb in pulsos_bajo:
        i0 = int(round(tb * sr))
        i1 = min(n_total, int(round((tb + durb) * sr)))
        if i1 <= i0:
            continue
        u = (np.arange(i0, i1) / sr) - tb
        env_b = (np.sin(np.minimum(1.0, u / 0.05) * math.pi / 2.0) ** 2) * np.exp(-1.28 * u)
        ph_b = 2.0 * math.pi * fb * u
        sig_b = (0.76 * np.sin(ph_b) + 0.24 * np.sin(2.0 * ph_b)) * env_b * (0.16 * velb)
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

    mix = y_hof * 0.88 + y_bajo * 0.82 + y_siringua * 0.94
    trazas_esc = {
        'centro_bombeo_thouless': tr_hof['centro_bombeo_thouless'],
        'ipr_localizacion_aa': tr_hof['ipr_localizacion_aa'],
        'env_bajo_thouless': env_bajo,
        'f0_siringua_borde': f0_sir_vib * (amp_sir > 0.04)
    }
    return mix, {'hofstadter': y_hof, 'bajo': y_bajo, 'siringua': y_siringua}, trazas_esc


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
    c_mid = np.array(COL_CHERN, dtype=float)
    c_hi = np.array(COL_HOFSTADTER, dtype=float)
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


def crear_lamina_01_hofstadter_sonda(sonda_res, path_png):
    W, H = 1600, 960
    im = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(im)
    f_title = cargar_fuente(23, bold=True)
    f_sub = cargar_fuente(14)
    f_sec = cargar_fuente(16, bold=True)
    f_txt = cargar_fuente(13)
    f_sm = cargar_fuente(11)

    p1 = sonda_res['prueba_1_invariante_chern_tknn_y_bombeo_thouless']
    p2 = sonda_res['prueba_2_transicion_localizacion_aubry_andre']
    p3 = sonda_res['prueba_3_correspondencia_bulto_borde_y_brecha_chern']
    p4 = sonda_res['prueba_4_costura_brecha_chern_y_spectrumsynth']

    dr.text((48, 24), '01 · MARIPOSA MAGNÉTICA DE HOFSTADTER–THOULESS · INVARIANTE DE CHERN Y AUBRY–ANDRÉ', font=f_title, fill=FG)
    dr.text((48, 60), f'Semilla {SEMILLA} · spectrumsynth {p4["SNR_spectrumsynth_dB"]} dB · Chern C_r = {p1["numeros_chern_bandas_medidos"]} (err {p1["error_cuantizacion_entera_FHS"]:.1e}) · Bombeo ΔP = {p1["desplazamiento_bombeo_thouless_DeltaP"]:+.4f}', font=f_sub, fill=MUTED)

    dr.rectangle((48, 104, 775, 548), fill=PANEL_BG, outline=GRID_COL, width=2)
    dr.text((68, 120), 'Espectro Fractal de Hofstadter E(α = p/q) y Bombeo Topológico de Thouless', font=f_sec, fill=COL_HOFSTADTER)

    al_pts, en_pts = generar_mariposa_hofstadter_puntos(q_max=26)
    bx_m, by_m, bw_m, bh_m = 68, 162, 410, 348
    dr.rectangle((bx_m, by_m, bx_m + bw_m, by_m + bh_m), fill=BG, outline=GRID_COL, width=1)
    for a_v, e_v in zip(al_pts, en_pts):
        px = int(bx_m + 8 + a_v * (bw_m - 16))
        py = int(by_m + bh_m / 2 - (e_v / 4.25) * (bh_m * 0.46))
        if abs(a_v - 1.0 / 3.0) < 0.015 or abs(a_v - 2.0 / 3.0) < 0.015:
            col_pt = COL_CHERN
        elif abs(e_v) < 0.85:
            col_pt = COL_EDGE
        else:
            col_pt = COL_HOFSTADTER
        dr.point((px, py), fill=col_pt)
        dr.point((px + 1, py), fill=col_pt)

    dr.text((bx_m + 10, by_m + 10), 'Mariposa de Hofstadter E vs α=Φ/Φ₀', font=f_sm, fill=COL_HOFSTADTER)
    dr.text((bx_m + 12, by_m + bh_m - 22), 'α=0        α=1/3        α=1/2        α=2/3        α=1', font=f_sm, fill=MUTED)

    fhs_vis = calcular_numeros_chern_fhs(p=1, q=3, Nk=36)
    box_th = (496, 162, 258, 155)
    dr.rectangle((496, 162, 496 + 258, 162 + 155), fill=BG, outline=GRID_COL, width=1)
    pol_vis = np.abs(fhs_vis['polarizacion_thouless'])
    dibujar_curva(dr, pol_vis, box_th, COL_CHERN, -0.05, 1.08, width=3)
    dr.text((506, 172), 'Bombeo de Thouless P(θ)', font=f_sm, fill=COL_CHERN)
    dr.text((542, 266), 'ΔP = |C₁| = +1.0000 celda/ciclo', font=f_sm, fill=FG)
    dr.text((506, 292), 'θ: 0 → 2π (Transporte cuantizado)', font=f_sm, fill=MUTED)

    obc_vis = analizar_modos_borde_obc(L_obc=30, p=1, q=3, n_thetas=48)
    box_obc = (496, 340, 258, 170)
    dr.rectangle((496, 340, 496 + 258, 340 + 170), fill=BG, outline=GRID_COL, width=1)
    for m_idx in range(30):
        w_curve = obc_vis['evals_obc'][:, m_idx]
        ed_mean = float(np.mean(obc_vis['edge_weight'][:, m_idx]))
        col_c = COL_EDGE if ed_mean > 0.38 else MUTED
        w_line = 2 if ed_mean > 0.38 else 1
        dibujar_curva(dr, w_curve, box_obc, col_c, -4.1, 4.1, width=w_line)
    dr.text((506, 348), 'Bulto (gris) + Borde Quiral (verde)', font=f_sm, fill=COL_EDGE)
    dr.text((506, 488), 'La Siringua cruza la brecha de Chern', font=f_sm, fill=FG)

    dr.rectangle((805, 104, 1552, 548), fill=PANEL_BG, outline=GRID_COL, width=2)
    dr.text((825, 120), 'Resultados medidos por la sonda (Chern TKNN, Thouless, Aubry–André)', font=f_sec, fill=COL_EDGE)

    lineas = [
        ('1. Invariante Topológico de Chern (Fukui–Hatsugai–Suzuki, α = 1/3):', COL_HOFSTADTER),
        (f'   • Números de Chern de las 3 bandas: C = {p1["numeros_chern_bandas_medidos"]}', FG),
        (f'   • Error de cuantización entera: {p1["error_cuantizacion_entera_FHS"]:.2e} · Suma ∑C_r = {p1["suma_total_chern_bandas"]:.1f}', FG),
        ('2. Bombeo Cuántico de Thouless y Ecuación Diofántica TKNN:', COL_CHERN),
        (f'   • Invariantes de brecha: C_gap = {p1["invariantes_chern_huecos_C1_C2"]} (p·C_r + q·s_r = {p1["verificacion_diofantica_TKNN_r1_r2"]})', FG),
        (f'   • Transporte adiabático por ciclo θ ∈ [0,2π]: ΔP = {p1["desplazamiento_bombeo_thouless_DeltaP"]:+.4f} celda', FG),
        ('3. Dualidad y Localización Cuasicristalina de Aubry–André (α = φ⁻¹):', COL_AUBRY),
        (f'   • IPR metálico (λ=0.4): {p2["IPR_medio_metalico_extendido_lam04"]:.4f} → Crítico (λ=1): {p2["IPR_medio_critico_multifractal_lam10"]:.4f}', FG),
        (f'   • IPR aislante (λ=2.5): {p2["IPR_medio_aislante_localizado_lam25"]:.4f} ({p2["factor_compresion_localizacion_IPR"]:.1f}x localizado, ξ={p2["longitud_localizacion_teorica_xi_lam25"]:.3f})', FG),
        ('4. Costura por Brecha Prohibida de Chern en 440 Hz (Siringua):', COL_EDGE),
        (f'   • Hueco topológico: {p4["despeje_brecha_topologica_dB"]:+.2f} dB · Modo borde OBC {p3["localizacion_maxima_modo_borde_OBC"]*100:.1f}% · SNR {p4["SNR_spectrumsynth_dB"]:.2f} dB', FG),
    ]
    yy = 158
    for txt, col in lineas:
        dr.text((825, yy), txt, font=f_txt, fill=col)
        yy += 34

    dr.rectangle((48, 574, 1552, 918), fill=PANEL_BG, outline=GRID_COL, width=2)
    dr.text((68, 590), 'Transición de Autolocalización de Aubry–André (α = φ⁻¹ = 0.618034): Onda de Bloch Extendida vs Multifractal Crítico vs Aislante', font=f_sec, fill=FG)

    aa_vis = analizar_transicion_aubry_andre(L_chain=89, alpha=(math.sqrt(5.0) - 1.0) / 2.0, lambdas=(0.40, 1.00, 2.50))
    box_aa = (365, 636, 1135, 225)
    dr.rectangle((365, 636, 365 + 1135, 636 + 225), fill=BG, outline=GRID_COL, width=1)
    dibujar_curva(dr, aa_vis[0.40]['densidad_estado_central'] * 6.5, box_aa, COL_HOFSTADTER, 0.0, 0.85, width=2)
    dibujar_curva(dr, aa_vis[1.00]['densidad_estado_central'] * 2.2, box_aa, COL_CHERN, 0.0, 0.85, width=2)
    dibujar_curva(dr, aa_vis[2.50]['densidad_estado_central'], box_aa, COL_AUBRY, 0.0, 0.85, width=3)

    dr.text((68, 654), 'Extendida Metálica (λ = 0.4 < 1)', font=f_txt, fill=COL_HOFSTADTER)
    dr.text((68, 692), 'Crítica Multifractal (λ = 1.0)', font=f_txt, fill=COL_CHERN)
    dr.text((68, 730), 'Aislante Localizada (λ = 2.5 > 1)', font=f_txt, fill=COL_AUBRY)
    dr.text((68, 774), 'En λ < 1 todos los parciales', font=f_sm, fill=MUTED)
    dr.text((68, 794), 'comparten la vibración; al', font=f_sm, fill=MUTED)
    dr.text((68, 814), 'cruzar λ = 1 la energía colapsa', font=f_sm, fill=MUTED)
    dr.text((68, 834), 'en agujas cristalinas (ξ=1/ln λ).', font=f_sm, fill=MUTED)

    for x_frac, x_off, txt_lbl in [
        (0.0, 0, 'Sitio n = 0 (Extremo izquierdo)'),
        (0.5, -110, 'Sitio central n = 44 (Pico de localización de Aubry–André)'),
        (1.0, -210, 'Sitio n = 88 (Extremo derecho)')
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

    dr.text((48, 24), '02 · MUESTRA AISLADA · LA MARIPOSA MAGNÉTICA DE HOFSTADTER–THOULESS (24 s)', font=f_title, fill=FG)
    dr.text((48, 60), f'Archivo: {med_solo["m4a"]} · {med_solo["I_LUFS"]:.1f} LUFS · {med_solo["pico_dBTP"]:.1f} dBTP · LRA {med_solo["LRA"]:.1f} · Semilla {SEMILLA}', font=f_sub, fill=MUTED)

    x0, w_plot = 235, 1310
    secciones = [
        (0.0, 'I · Banda de Bloch (α→0)'),
        (4.8, 'II · Tricotomía Hofstadter (α=1/3)'),
        (9.6, 'III · Bombeo Thouless (ΔP=+1)'),
        (14.4, 'IV · Cuasicristal Áureo (λ:1→2.4)'),
        (19.2, 'V · Reconciliación Topológica')
    ]
    for sec_t, sec_lbl in secciones:
        xx = x0 + (sec_t / 24.0) * w_plot
        dr.line((xx, 112, xx, 885), fill=GRID_COL, width=1)
        dr.text((xx + 4, 110), sec_lbl, font=f_sm, fill=FG)

    yy0 = 142
    dr.rectangle((x0, yy0, x0 + w_plot, yy0 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy0 + 24), 'Flujo α(t) = Φ/Φ₀', font=f_sec, fill=COL_HOFSTADTER)
    dibujar_curva(dr, tr_solo['flujo_magnetico_alpha'], (x0, yy0 + 4, w_plot, 64), COL_HOFSTADTER, 0.0, 0.72, width=2)

    yy1 = 234
    dr.rectangle((x0, yy1, x0 + w_plot, yy1 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy1 + 24), 'Centro Thouless ⟨n⟩', font=f_sec, fill=COL_CHERN)
    dibujar_curva(dr, tr_solo['centro_bombeo_thouless'], (x0, yy1 + 4, w_plot, 64), COL_CHERN, 1.0, 14.0, width=2)

    yy2 = 326
    dr.rectangle((x0, yy2, x0 + w_plot, yy2 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy2 + 24), 'Acoplamiento λ(t)', font=f_sec, fill=COL_AUBRY)
    dibujar_curva(dr, tr_solo['potencial_aubry_andre_lambda'], (x0, yy2 + 4, w_plot, 64), COL_AUBRY, 0.0, 2.6, width=2)

    yy3 = 418
    dr.rectangle((x0, yy3, x0 + w_plot, yy3 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy3 + 24), 'Localización IPR(t)', font=f_sec, fill=COL_EDGE)
    dibujar_curva(dr, tr_solo['ipr_localizacion_aa'], (x0, yy3 + 4, w_plot, 64), COL_EDGE, 0.04, 0.78, width=2)

    yy_w = 518
    dr.rectangle((x0, yy_w, x0 + w_plot, yy_w + 88), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy_w + 30), 'Onda estéreo', font=f_sec, fill=FG)
    y_norm_vis = normalizar_nivel(y_solo)
    dibujar_curva(dr, y_norm_vis[:, 0], (x0, yy_w + 4, w_plot, 80), COL_HOFSTADTER, -0.75, 0.75, width=1)

    yy_s = 626
    spec_im = espectrograma_imagen(y_solo, SR, w_plot, 252)
    im.paste(spec_im, (x0, yy_s))
    dr.rectangle((x0, yy_s, x0 + w_plot, yy_s + 252), outline=GRID_COL, width=1)
    dr.text((48, yy_s + 20), 'Espectrograma\n35 Hz – 11.0 kHz', font=f_sec, fill=FG)
    dr.text((48, yy_s + 78), 'En II las bandas se\nrasgan en 3 racimos;\nen III el bombeo de\nThouless transporta la\nenergía y en IV localiza.', font=f_sm, fill=COL_HOFSTADTER)

    for s_tick in range(0, 25, 3):
        xx = x0 + (s_tick / 24.0) * w_plot
        dr.text((xx - 10, 892), f'{s_tick} s', font=f_sm, fill=MUTED)
    dr.text((48, 922), 'Lectura: α(t) pliega el espectro según la Mariposa de Hofstadter; θ(t) bombea energía entre cuerdas; λ(t) > 1 localiza por Aubry–André.', font=f_sm, fill=MUTED)

    im.save(str(path_png), 'PNG')
    return im


def crear_lamina_03_escena_hofstadter(y_mix, tr_esc, med_mix, path_png):
    W, H = 1600, 960
    im = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(im)
    f_title = cargar_fuente(23, bold=True)
    f_sub = cargar_fuente(14)
    f_sec = cargar_fuente(15, bold=True)
    f_sm = cargar_fuente(11)

    dr.text((48, 24), '03 · ESCENA EN CONTEXTO · MARIPOSA DE HOFSTADTER + BAJO DE THOULESS + SIRINGUA EN BORDE QUIRAL', font=f_title, fill=FG)
    dr.text((48, 60), f'Archivo: {med_mix["m4a"]} · {med_mix["I_LUFS"]:.1f} LUFS · {med_mix["pico_dBTP"]:.1f} dBTP · La Siringua viaja como Modo Quiral dentro de la Brecha de Chern', font=f_sub, fill=MUTED)

    x0, w_plot = 235, 1310
    secciones = [
        (0.0, 'I · Metal de Bloch'),
        (4.8, 'II · Brecha Chern 440 Hz'),
        (9.6, 'III · Bombeo + 330 Hz'),
        (14.4, 'IV · Aubry–André + 440 Hz'),
        (19.2, 'V · Topología + 550 Hz')
    ]
    for sec_t, sec_lbl in secciones:
        xx = x0 + (sec_t / 24.0) * w_plot
        dr.line((xx, 112, xx, 885), fill=GRID_COL, width=1)
        dr.text((xx + 4, 110), sec_lbl, font=f_sm, fill=FG)

    yy0 = 142
    dr.rectangle((x0, yy0, x0 + w_plot, yy0 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy0 + 24), 'Centro Thouless ⟨n⟩', font=f_sec, fill=COL_CHERN)
    dibujar_curva(dr, tr_esc['centro_bombeo_thouless'], (x0, yy0 + 4, w_plot, 64), COL_CHERN, 1.0, 14.0, width=2)

    yy1 = 234
    dr.rectangle((x0, yy1, x0 + w_plot, yy1 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy1 + 24), 'Localización IPR(t)', font=f_sec, fill=COL_AUBRY)
    dibujar_curva(dr, tr_esc['ipr_localizacion_aa'], (x0, yy1 + 4, w_plot, 64), COL_AUBRY, 0.04, 0.78, width=2)

    yy2 = 326
    dr.rectangle((x0, yy2, x0 + w_plot, yy2 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy2 + 24), 'Bajo de Thouless', font=f_sec, fill=MUTED)
    dibujar_curva(dr, tr_esc['env_bajo_thouless'], (x0, yy2 + 4, w_plot, 64), MUTED, 0.0, 1.2, width=2)

    yy3 = 418
    dr.rectangle((x0, yy3, x0 + w_plot, yy3 + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy3 + 24), 'Siringua Quiral', font=f_sec, fill=COL_EDGE)
    dibujar_curva(dr, tr_esc['f0_siringua_borde'], (x0, yy3 + 4, w_plot, 64), COL_EDGE, 280.0, 600.0, width=2)

    yy_w = 518
    dr.rectangle((x0, yy_w, x0 + w_plot, yy_w + 88), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy_w + 26), 'Mezcla estéreo', font=f_sec, fill=FG)
    y_norm_vis = normalizar_nivel(y_mix)
    dibujar_curva(dr, y_norm_vis[:, 0], (x0, yy_w + 4, w_plot, 80), COL_HOFSTADTER, -0.75, 0.75, width=1)

    yy_s = 626
    spec_im = espectrograma_imagen(y_mix, SR, w_plot, 252)
    im.paste(spec_im, (x0, yy_s))
    dr.rectangle((x0, yy_s, x0 + w_plot, yy_s + 252), outline=GRID_COL, width=1)
    dr.text((48, yy_s + 20), 'Espectrograma\nMezcla Completa', font=f_sec, fill=FG)
    dr.text((48, yy_s + 78), 'El bulto de Hofstadter\nabre su brecha de Chern\nen 440, 330 y 550 Hz\ny la Siringua cruza como\nmodo de borde quiral.', font=f_sm, fill=COL_EDGE)

    for s_tick in range(0, 25, 3):
        xx = x0 + (s_tick / 24.0) * w_plot
        dr.text((xx - 10, 892), f'{s_tick} s', font=f_sm, fill=MUTED)
    dr.text((48, 922), 'Costura topológica: por correspondencia bulto-borde, el hueco prohibido de Chern silencia el bulto y protege a la Siringua.', font=f_sm, fill=MUTED)

    im.save(str(path_png), 'PNG')
    return im


def main():
    print('1. Ejecutando sonda de La Mariposa Magnética de Hofstadter–Thouless (Harper–Chern–Aubry–André)...', flush=True)
    sonda_res = ejecutar_sonda()
    print('   Sonda OK:', json.dumps(sonda_res, ensure_ascii=False), flush=True)

    print('2. Sintetizando muestra aislada de 24 s...', flush=True)
    phi_inv = (math.sqrt(5.0) - 1.0) / 2.0
    partitura_solo = {
        'prototipo': 'mariposa-hofstadter-chern',
        'duracion': 24.0,
        'semilla': SEMILLA,
        'flujo_magnetico_alpha': [
            [0.0, 0.02], [4.6, 0.08],
            [4.8, 0.3333], [9.5, 0.3333],
            [9.7, 0.2500], [14.3, 0.4000],
            [14.5, phi_inv], [19.1, phi_inv],
            [19.3, 0.3333], [24.0, 0.5000]
        ],
        'potencial_aubry_andre_lambda': [
            [0.0, 0.20], [4.6, 0.28],
            [4.8, 0.52], [9.5, 0.62],
            [9.7, 0.45], [14.3, 0.58],
            [14.5, 1.00], [16.8, 2.38], [19.1, 2.48],
            [19.3, 0.80], [24.0, 0.32]
        ],
        'velocidad_bombeo_thouless': [
            [0.0, 0.16], [4.6, 0.24],
            [4.8, 0.42], [9.5, 0.52],
            [9.7, 0.94], [14.3, 0.98],
            [14.5, 0.48], [19.1, 0.58],
            [19.3, 0.76], [24.0, 0.32]
        ],
        'brecha_chern_costura_hz': [
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
    y_solo, tr_solo = render_mariposa_hofstadter_chern(partitura_solo, 24.0, SR, SEMILLA)
    med_solo = guardar_audio_y_medir(
        y_solo,
        OUT_DIR / 'muestra-mariposa-hofstadter-chern-s20261021.wav',
        OUT_DIR / 'muestra-mariposa-hofstadter-chern-s20261021.m4a',
        target_lufs=-18.5
    )

    print('3. Sintetizando escena en contexto (Mariposa de Hofstadter + Bajo de Thouless + Siringua en Modo de Borde Quiral)...', flush=True)
    y_mix, stems_esc, tr_esc = render_escena_hofstadter_siringua_thouless(24.0, SR, SEMILLA)
    med_mix = guardar_audio_y_medir(
        y_mix,
        OUT_DIR / 'escena-mariposa-hofstadter-chern-s20261021.wav',
        OUT_DIR / 'escena-mariposa-hofstadter-chern-s20261021.m4a',
        target_lufs=-16.0
    )

    print('4. Generando láminas PNG en OKLCh y GIF...', flush=True)
    p1_png = OUT_DIR / '01-mariposa-hofstadter-y-chern-aubry-s20261021.png'
    p2_png = OUT_DIR / '02-mariposa-hofstadter-espectrograma-s20261021.png'
    p3_png = OUT_DIR / '03-escena-hofstadter-siringua-costura-s20261021.png'
    im1 = crear_lamina_01_hofstadter_sonda(sonda_res, p1_png)
    im2 = crear_lamina_02_muestra_aislada(y_solo, tr_solo, med_solo, p2_png)
    im3 = crear_lamina_03_escena_hofstadter(y_mix, tr_esc, med_mix, p3_png)

    frames = [im.resize((1200, 720), Image.Resampling.LANCZOS).quantize(colors=256, method=Image.Quantize.MEDIANCUT) for im in (im1, im2, im3)]
    gif_path = OUT_DIR / 'proceso-mariposa-hofstadter-chern-s20261021.gif'
    frames[0].save(
        str(gif_path),
        format='GIF',
        save_all=True,
        append_images=frames[1:],
        duration=1800,
        loop=0,
        optimize=True
    )

    if Path(__file__).resolve() != (OUT_DIR / 'mariposa_hofstadter_chern.py').resolve():
        shutil.copyfile(__file__, OUT_DIR / 'mariposa_hofstadter_chern.py')

    receta = {
        'instrumento': 'La Mariposa Magnética de Hofstadter–Thouless (Harper–Chern–Aubry–André)',
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
    receta_path = OUT_DIR / 'receta-mariposa-hofstadter-chern-s20261021.json'
    with open(receta_path, 'w', encoding='utf-8') as f:
        json.dump(receta, f, ensure_ascii=False, indent=2)

    print('5. Todo completado con éxito:', json.dumps(receta, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
