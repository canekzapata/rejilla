"""Construcción, sonda y producción real de El Astrolabio Metapléctico (Mp_{2n}) para Rejilla.

Ejecuta:
1. Sonda matemática y de señal (comparando:
   - Una sola hoja aislada vs Doble Hoja interferométrica.
   - El error de poner el paneo espacial en Mp_2 (cos(theta/2), que invertía L/R en 2*pi y sólo cancelaba -10.04 dB) vs poner el paneo en Sp_2 (cos(theta), que devuelve el sonido al mismo punto estéreo en 2*pi).
   - La caída de -28.98 dB en la banda de la fundamental en 2*pi y recuperación de 0.00 dB en 4*pi.
   - Prueba exacta: Imagen 16 bits -> FFmpeg `spectrumsynth` vs suma directa en el tiempo: SNR 69.69 dB).
2. Muestra aislada de 24 s (`muestra-astrolabio-s20261020.wav` y `.m4a`) recorriendo theta = 0 -> pi/4 -> pi/2 -> pi -> 2*pi -> 4*pi.
3. Escena de 24 s (`escena-astrolabio-bajo-boca-s20261020.wav` y `.m4a`): Astrolabio + Bajo + una boca de formantes propia,
   con una rotación de controles bajo↔boca (antes se llamaba «Mp_4»; ver README).

Arreglo del 20 oct 2026 (Claude, en la máquina de Canek), ver README.md:
- `reparto`: cómo gira la fase de cada armónico en la Hoja Viajera.
    'hermite'  (nuevo, por omisión): el armónico m se trata como el modo m de Hermite y gira con e^{-i(m+1/2)θ},
               la ley de la representación del oscilador. En 2π TODOS llevan −1 y la nota se borra contra su testigo;
               en 4π vuelve entera. Medido: a mitad de la vuelta suena casi igual que 'global', porque la viajera
               está en otro lugar del plano y no se encuentra con su testigo; la diferencia sólo cuenta donde coinciden.
    'global'   todos con −θ/2: sólo el signo del recubrimiento; mismo timbre hasta borrarse en 2π.
    'impares'  el reparto original: impares −θ/2, pares −θ. En 2π invierte sólo los impares → octava hueca.
               No lo obliga el grupo: es un filtro de impares. Se conserva porque suena bien.
- la rotación bajo↔boca usa de verdad los valores rotados (antes se calculaban y se tiraban).
4. Láminas PNG en paleta OKLCh sembrada (revisadas visualmente contra traslapes) y GIF en loop del proceso real.
"""
import hashlib, json, math, os, shutil, subprocess
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import stft, lfilter, iirpeak, butter, sosfilt
from PIL import Image, ImageDraw, ImageFont

SEMILLA = 20261020
SR = 32000

# Salida (rejilla, acuerdo del 13 oct 2026): carpeta exclusiva <pieza>-s<semilla>-<hash12>; nunca se pisa.
# La versión original escribía en el sandbox de otra herramienta (/working_dir/...).
AQUI = Path(__file__).resolve().parent
EJECUCION = hashlib.sha256(Path(__file__).read_bytes() + str(SEMILLA).encode() + os.urandom(16)).hexdigest()
OUT_DIR = AQUI / f'astrolabio-metaplectico-s{SEMILLA}-{EJECUCION[:12]}'
INTER_DIR = OUT_DIR / 'intermedio'
if __name__ == '__main__':
    OUT_DIR.mkdir(parents=False, exist_ok=False)
    INTER_DIR.mkdir()

# ───────────── Paleta OKLCh sembrada (regla de Rejilla) ─────────────
def oklch(L, C, h_deg):
    """Convierte OKLCh (L en 0..1, C en 0..0.4, h en grados) a tupla RGB (0..255)."""
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
H0 = 248.0 + float(rng_vis.uniform(-12.0, 12.0))
BG = oklch(0.13, 0.035, H0)
PANEL_BG = oklch(0.17, 0.04, H0 + 8)
GRID_COL = oklch(0.28, 0.04, H0)
FG = oklch(0.93, 0.025, H0 + 35)
MUTED = oklch(0.68, 0.04, H0 + 15)
COL_HOJA_POS = oklch(0.78, 0.16, H0 - 110)   # Verde/esmeralda cálido (Hoja +1)
COL_HOJA_NEG = oklch(0.74, 0.16, H0 + 95)    # Magenta/rosado frío (Hoja -1, negativo)
COL_RITMO = oklch(0.80, 0.17, H0 - 45)       # Cian brillante (Giro a ritmo theta=pi/2)
COL_CAUSTICA = oklch(0.86, 0.18, H0 - 165)   # Ámbar/oro brillante (Cáustica de Maslov)
COL_MP4 = oklch(0.76, 0.16, H0 + 45)         # Violeta/lila (Acoplamiento Mp4)

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

# ───────────── 1. Motor Espectral Exacto (Fórmula cerrada + FFmpeg spectrumsynth) ─────────────
class PistaRejilla:
    """Implementación exacta de la serie geométrica modal por columna para spectrumsynth."""
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

# ───────────── 2. Transformación Metapléctica Mp_2(R) sobre paquetes tiempo-frecuencia ─────────────
def transformar_evento_mp2(t_k, f_k, dur_k, t_c, f_c, theta, comp_a=1.0, chirp_c=0.0, sigma_t=0.26, sigma_f=110.0):
    q = (t_k - t_c) / sigma_t
    p = (f_k - f_c) / sigma_f
    qa = comp_a * q
    pa = (chirp_c * comp_a) * q + (1.0 / comp_a) * p
    ct, st = math.cos(theta), math.sin(theta)
    q_new = ct * qa + st * pa
    p_new = -st * qa + ct * pa

    t_new = t_c + sigma_t * q_new
    f_new = max(35.0, min(12000.0, f_c + sigma_f * p_new))

    stretch_t = math.sqrt((ct / comp_a) ** 2 + (st * comp_a) ** 2)
    dur_new = max(0.08, min(2.4, dur_k * stretch_t))
    amp_scale = 1.0 / math.sqrt(max(0.25, stretch_t))

    fase_weyl = 0.25 * math.pi * (q_new * p_new - q * p)
    return t_new, f_new, dur_new, amp_scale, fase_weyl

REPARTOS = ('hermite', 'global', 'impares')

def kappa(m_idx, reparto='hermite'):
    """Cuánto gira la fase del armónico m_idx+1 por radián de θ en la Hoja Viajera (ver el docstring del módulo)."""
    if reparto == 'hermite':
        return m_idx + 0.5
    if reparto == 'global':
        return 0.5
    if reparto == 'impares':
        return 0.5 if (m_idx % 2 == 0) else 1.0
    raise ValueError(f'reparto desconocido: {reparto!r} (usa {REPARTOS})')

def escribir_acorde_astrolabio_en_pista(P, t_c, midi_raiz, semitonos, theta, comp_a=1.0, chirp_c=0.0, mezcla=0.5, vel=0.85, dur_base=0.45, pan_en_sp2=True, semilla=100, reparto='hermite'):
    rng = np.random.default_rng(semilla)
    f_c = float(hz(midi_raiz + np.mean(semitonos)))
    for idx, st_val in enumerate(semitonos):
        f_k = float(hz(midi_raiz + st_val))
        t_k = t_c + (idx - (len(semitonos) - 1) / 2.0) * 0.012
        dur_k = dur_base
        t_new, f_new, dur_new, amp_sc, fase_weyl = transformar_evento_mp2(
            t_k, f_k, dur_k, t_c, f_c, theta, comp_a=comp_a, chirp_c=chirp_c
        )
        pan_base = -0.50 + 1.00 * (idx / max(1, len(semitonos) - 1))

        for m_idx in range(6):
            harm = m_idx + 1
            amp_base = (0.095 * vel / (harm ** 1.18)) * (1.15 if idx == 0 else 0.85)
            tasa_a = 3.2 + 0.55 * harm
            fase_0 = -math.pi / 2.0

            if mezcla < 1.0:
                P.modo(
                    f_k * harm, amp_base * (1.0 - mezcla), max(0.02, t_k),
                    tasa_a, ataque=120.0, suelta=dur_k, ar=28.0,
                    pan=pan_base, fase=fase_0
                )

            if mezcla > 0.0:
                fase_maslov = -kappa(m_idx, reparto) * theta + fase_weyl
                ang_pan = theta if pan_en_sp2 else (0.5 * theta)
                pan_viajero = float(np.clip(pan_base * math.cos(ang_pan) + 0.55 * math.sin(ang_pan), -0.95, 0.95))
                tasa_new = tasa_a / max(0.35, (dur_new / dur_k))
                P.modo(
                    f_new * harm, amp_base * mezcla * amp_sc, max(0.02, t_new),
                    tasa_new, ataque=120.0, suelta=dur_new, ar=28.0,
                    pan=pan_viajero, fase=fase_0 + fase_maslov
                )

        caustica = math.exp(-((abs(math.sin(theta)) - 1.0) ** 2) / 0.045)
        if caustica > 0.15:
            for r_ratio in (1.0, 2.32, 3.87):
                f_caust = min(11000.0, f_new * r_ratio * 2.0)
                P.modo(
                    f_caust, 0.015 * vel * caustica, max(0.02, t_new),
                    8.5, ataque=45.0, suelta=0.32, ar=28.0,
                    pan=float(rng.uniform(-0.75, 0.75)),
                    fase=float(rng.uniform(0, 2 * math.pi)) + math.pi / 4.0
                )

# ───────────── 3. Motor Temporal de Prototipo (24 s) ─────────────
def render_astrolabio_temporal(partitura, duracion=24.0, sr=SR, semilla=SEMILLA):
    n_total = int(round(duracion * sr))
    t = np.arange(n_total) / sr
    out = np.zeros((n_total, 2), dtype=np.float64)
    rng = np.random.default_rng(semilla)

    def interp_ctrl(key, default):
        pts = np.asarray(partitura.get(key, [[0.0, default], [duracion, default]]), dtype=float)
        return np.interp(t, pts[:, 0], pts[:, 1])

    theta_curve = interp_ctrl('giro_theta_rad', 0.0)
    comp_curve = interp_ctrl('compresion_a', 1.0)
    chirp_curve = interp_ctrl('cizalla_chirp', 0.0)
    mezcla_curve = interp_ctrl('mezcla_hojas', 0.5)

    eventos = partitura.get('eventos', [])
    trazas_eventos = []

    for ev_i, ev in enumerate(eventos):
        t_c = float(ev['t_c'])
        midi_raiz = float(ev['midi'])
        semitonos = ev.get('semitonos', [0, 7, 12, 16, 19, 22.68, 26.04])
        vel = float(ev.get('vel', 0.85))
        idx_c = min(n_total - 1, max(0, int(round(t_c * sr))))

        theta = float(ev.get('theta', theta_curve[idx_c]))
        comp_a = float(ev.get('comp_a', comp_curve[idx_c]))
        chirp_c = float(ev.get('chirp_c', chirp_curve[idx_c]))
        mezcla = float(ev.get('mezcla', mezcla_curve[idx_c]))
        reparto = ev.get('reparto', partitura.get('reparto', 'hermite'))

        f_c = float(hz(midi_raiz + np.mean(semitonos)))

        for idx, st_val in enumerate(semitonos):
            f_k = float(hz(midi_raiz + st_val))
            t_k = t_c + (idx - (len(semitonos) - 1) / 2.0) * 0.015
            dur_k = float(ev.get('dur', 1.55))

            t_new, f_new, dur_new, amp_sc, fase_weyl = transformar_evento_mp2(
                t_k, f_k, dur_k, t_c, f_c, theta, comp_a=comp_a, chirp_c=chirp_c
            )
            trazas_eventos.append({
                'evento': ev_i, 'voz': idx,
                't_orig': round(t_k, 4), 'f_orig': round(f_k, 2),
                't_rot': round(t_new, 4), 'f_rot': round(f_new, 2),
                'theta': round(theta, 4), 'hoja_signo': round(math.cos(theta / 2.0), 4)
            })

            pan_base = -0.50 + 1.00 * (idx / max(1, len(semitonos) - 1))
            pan_rot = float(np.clip(pan_base * math.cos(theta) + 0.55 * math.sin(theta), -0.95, 0.95))

            if mezcla < 1.0:
                i0 = max(0, int(round(t_k * sr)))
                i1 = min(n_total, int(round((t_k + dur_k + 0.8) * sr)))
                if i1 > i0:
                    u = (np.arange(i0, i1) / sr) - t_k
                    sig_t = np.zeros_like(u)
                    for m_idx in range(7):
                        harm = m_idx + 1
                        if f_k * harm >= sr * 0.44:
                            break
                        a_rate = 1.35 + 0.42 * harm
                        at_rate = 95.0
                        tp = math.log(at_rate / a_rate) / (at_rate - a_rate)
                        env = (np.exp(-a_rate * u) - np.exp(-at_rate * u)) / (math.exp(-a_rate * tp) - math.exp(-at_rate * tp))
                        amp_h = (0.085 * vel / (harm ** 1.18)) * (1.2 if idx == 0 else 0.85)
                        sig_t += amp_h * (1.0 - mezcla) * env * np.cos(2.0 * math.pi * (f_k * harm) * u - math.pi / 2.0)
                    gL, gR = paneo(pan_base)
                    out[i0:i1, 0] += gL * sig_t
                    out[i0:i1, 1] += gR * sig_t

            if mezcla > 0.0:
                i0 = max(0, int(round(t_new * sr)))
                i1 = min(n_total, int(round((t_new + dur_new + 0.9) * sr)))
                if i1 > i0:
                    u = (np.arange(i0, i1) / sr) - t_new
                    sig_v = np.zeros_like(u)
                    chirp_inst = chirp_c * 35.0
                    for m_idx in range(7):
                        harm = m_idx + 1
                        if f_new * harm >= sr * 0.44:
                            break
                        a_rate = (1.35 + 0.42 * harm) / max(0.35, (dur_new / dur_k))
                        at_rate = 95.0
                        tp = math.log(at_rate / a_rate) / (at_rate - a_rate)
                        env = (np.exp(-a_rate * u) - np.exp(-at_rate * u)) / (math.exp(-a_rate * tp) - math.exp(-at_rate * tp))
                        fase_maslov = -kappa(m_idx, reparto) * theta + fase_weyl
                        fase_inst = 2.0 * math.pi * (f_new * harm * u + 0.5 * chirp_inst * harm * (u ** 2)) - math.pi / 2.0 + fase_maslov
                        amp_h = (0.085 * vel / (harm ** 1.18)) * (1.2 if idx == 0 else 0.85)
                        sig_v += amp_h * mezcla * amp_sc * env * np.cos(fase_inst)
                    gL, gR = paneo(pan_rot)
                    out[i0:i1, 0] += gL * sig_v
                    out[i0:i1, 1] += gR * sig_v

            caustica = math.exp(-((abs(math.sin(theta)) - 1.0) ** 2) / 0.045)
            if caustica > 0.15:
                i0 = max(0, int(round(t_new * sr)))
                i1 = min(n_total, int(round((t_new + 0.55) * sr)))
                if i1 > i0:
                    u = (np.arange(i0, i1) / sr) - t_new
                    env_c = np.sin(np.minimum(1.0, u / 0.045) * math.pi / 2.0) ** 2 * np.exp(-5.5 * u)
                    ruido_afinado = np.zeros_like(u)
                    for r_ratio in (1.0, 2.32, 3.87, 5.43):
                        fc = min(sr * 0.42, f_new * r_ratio * 1.5)
                        ruido_afinado += np.cos(2.0 * math.pi * fc * u + rng.uniform(0, 2 * math.pi) + math.pi / 4.0) / r_ratio
                    gL, gR = paneo(rng.uniform(-0.75, 0.75))
                    out[i0:i1, 0] += gL * 0.014 * vel * caustica * env_c * ruido_afinado
                    out[i0:i1, 1] += gR * 0.014 * vel * caustica * env_c * ruido_afinado

    for ch, d_s in ((0, 1.0 / 55.0), (1, 1.0 / 82.5)):
        n_d = int(round(d_s * sr))
        if n_d < n_total:
            out[n_d:, ch] += 0.12 * out[:-n_d, 1 - ch]

    trazas = {
        'theta_rad': theta_curve,
        'hoja_maslov': np.cos(theta_curve / 2.0),
        'compresion_a': comp_curve,
        'cizalla_chirp': chirp_curve,
        'caustica_maslov': np.exp(-((np.abs(np.sin(theta_curve)) - 1.0) ** 2) / 0.045)
    }
    return out, trazas, {'eventos_transformados': trazas_eventos}


# ───────────── 4. Escena: Astrolabio + Bajo + boca de formantes, con rotación de controles bajo↔boca ─────────────
# (la boca es propia de este archivo, no la «boca de tres tiempos» de Codex)
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

def render_escena_mp4(duracion=24.0, sr=SR, semilla=SEMILLA, reparto='impares'):
    """La escena conserva por omisión el reparto 'impares': su sección III usa la octava hueca como halo para la voz."""
    n_total = int(round(duracion * sr))
    t = np.arange(n_total) / sr
    rng = np.random.default_rng(semilla + 7)

    phi_mp4 = np.interp(t, [0, 5.5, 8.5, 11.5, 14.0, 18.0, 24.0], [0.0, 0.0, math.pi / 2.0, math.pi / 2.0, math.pi / 4.0, 0.0, 0.0])

    part_astro = {
        'giro_theta_rad': [[0, 0], [6, 0], [9, math.pi / 2], [12, math.pi], [14, 2 * math.pi], [18, 2 * math.pi], [21, 4 * math.pi], [24, 4 * math.pi]],
        'compresion_a': [[0, 1.0], [8, 1.35], [15, 0.8], [24, 1.0]],
        'cizalla_chirp': [[0, 0.0], [7, 0.55], [12, -0.45], [18, 0.0], [24, 0.0]],
        'mezcla_hojas': [[0, 0.5], [24, 0.5]],
        'reparto': reparto,
        'eventos': [
            {'t_c': 1.8, 'midi': 57, 'semitonos': [0, 7, 12, 16, 19, 22.68], 'theta': 0.0, 'vel': 0.85},
            {'t_c': 5.5, 'midi': 57, 'semitonos': [0, 7, 12, 16, 19, 22.68], 'theta': math.pi / 4.0, 'vel': 0.82},
            {'t_c': 9.2, 'midi': 53, 'semitonos': [0, 7, 12, 16, 19, 22.68], 'theta': math.pi / 2.0, 'vel': 0.88},
            {'t_c': 13.0, 'midi': 57, 'semitonos': [0, 7, 12, 16, 19, 22.68], 'theta': 2.0 * math.pi, 'vel': 0.85},
            {'t_c': 16.5, 'midi': 55, 'semitonos': [0, 7, 12, 16, 19, 22.68], 'theta': 2.0 * math.pi, 'vel': 0.80},
            {'t_c': 20.2, 'midi': 57, 'semitonos': [0, 7, 12, 16, 19, 22.68], 'theta': 4.0 * math.pi, 'vel': 0.92},
        ]
    }
    y_astro, tr_astro, _ = render_astrolabio_temporal(part_astro, duracion, sr, semilla)

    pulsos_base = [0.0, 0.6, 1.5, 2.4, 3.0, 3.9, 4.8, 5.4,
                   6.0, 6.45, 7.2, 7.95, 8.7, 9.3, 10.2, 11.1,
                   12.0, 13.2, 14.4, 15.6, 16.8,
                   18.0, 18.6, 19.5, 20.4, 21.0, 21.9, 22.8]
    midis_bajo = [33, 33, 40, 33, 36, 33, 40, 38,
                  29, 29, 36, 41, 29, 36, 40, 38,
                  33, 33, 31, 31, 29,
                  33, 40, 45, 33, 40, 36, 33]

    y_bajo = np.zeros((n_total, 2), dtype=np.float64)
    env_bajo_q = np.zeros(n_total, dtype=np.float64)

    t_voc = np.array([0.0, 4.0, 8.0, 12.0, 15.5, 19.0, 24.0])
    seq_voc = ['a', 'o', 'u', 'i', 'e', 'a', 'a']
    vf = np.array([VOCALES[v] for v in seq_voc], dtype=float)
    formantes_base = np.array([np.interp(t, t_voc, vf[:, k]) for k in range(4)])
    p_boca_norm = (formantes_base[1] - 1200.0) / 900.0


    for p_t, m_b in zip(pulsos_base, midis_bajo):
        idx_p = min(n_total - 1, int(round(p_t * sr)))
        phi = float(phi_mp4[idx_p])
        dt_shift = 0.095 * math.sin(phi) * float(p_boca_norm[idx_p])
        t_onset = max(0.0, min(duracion - 0.5, p_t + dt_shift))
        dur_b = 0.52 * (1.0 + 0.25 * math.sin(phi))
        i0 = int(round(t_onset * sr))
        i1 = min(n_total, int(round((t_onset + dur_b) * sr)))
        if i1 <= i0:
            continue
        u = (np.arange(i0, i1) / sr) - t_onset
        f_b = float(hz(m_b)) * (1.0 + 0.035 * np.exp(-u / 0.04))
        ph_b = 2.0 * math.pi * np.cumsum(f_b) / sr
        env_b = np.sin(np.minimum(1.0, u / 0.010) * math.pi / 2.0) ** 2 * np.exp(-3.2 * u)
        sig_b = (0.65 * np.sin(ph_b) + 0.35 * np.tanh(1.8 * np.sin(ph_b * 2.0) + 0.7 * np.sin(ph_b * 3.0))) * env_b * 0.34
        y_bajo[i0:i1, 0] += sig_b * 0.72
        y_bajo[i0:i1, 1] += sig_b * 0.72
        env_bajo_q[i0:i1] += env_b

    # Rotación de controles en el plano (q = envolvente del bajo, p = posición de F2 de la boca).
    # Antes se calculaba q_rot/p_rot sólo para medir la norma y se tiraba; ahora la boca canta con p_rot:
    # en φ = 0 F2 sigue su vocal; en φ = π/2 F2 es el pulso del bajo (y la vocal pasó al bajo: dt_shift, arriba,
    # es la parte −sin φ · p de q_rot). La norma q² + p² se conserva por construcción.
    q_n = env_bajo_q / (env_bajo_q.max() + 1e-12)
    q_rot = np.cos(phi_mp4) * q_n - np.sin(phi_mp4) * p_boca_norm
    p_rot = np.sin(phi_mp4) * q_n + np.cos(phi_mp4) * p_boca_norm
    norma_antes_mp4 = q_n ** 2 + p_boca_norm ** 2
    norma_despues_mp4 = q_rot ** 2 + p_rot ** 2
    formantes_acoplados = formantes_base.copy()
    formantes_acoplados[1] = np.clip(1200.0 + 900.0 * p_rot, 550.0, 2950.0)
    formantes_acoplados[0] = np.clip(formantes_base[0] * (1.0 + 0.38 * (p_rot - p_boca_norm)), 240.0, 1100.0)

    def _corr(x, y):
        return float(np.corrcoef(x, y)[0, 1]) if np.std(x) > 1e-9 and np.std(y) > 1e-9 else 0.0
    w0 = (t >= 0.0) & (t < 5.5)
    w1 = (t >= 8.5) & (t < 11.5)
    corr_f2_bajo = {'phi_0': round(_corr(formantes_acoplados[1][w0], q_n[w0]), 3),
                    'phi_pi2': round(_corr(formantes_acoplados[1][w1], q_n[w1]), 3)}

    notas_boca = [
        {'t': 0.6, 'dur': 1.6, 'midi': 69, 'vel': 0.78},
        {'t': 2.3, 'dur': 1.1, 'midi': 72, 'vel': 0.75},
        {'t': 3.5, 'dur': 1.7, 'midi': 71, 'vel': 0.72},
        {'t': 6.2, 'dur': 2.6, 'midi': 69, 'vel': 0.85},
        {'t': 8.9, 'dur': 2.4, 'midi': 67, 'vel': 0.82},
        {'t': 12.4, 'dur': 1.4, 'midi': 74, 'vel': 0.88},
        {'t': 13.9, 'dur': 1.2, 'midi': 76, 'vel': 0.90},
        {'t': 15.2, 'dur': 2.3, 'midi': 72, 'vel': 0.86},
        {'t': 19.0, 'dur': 1.5, 'midi': 71, 'vel': 0.82},
        {'t': 20.6, 'dur': 2.6, 'midi': 69, 'vel': 0.90},
    ]
    f0_boca = np.full(n_total, float(hz(69)))
    amp_boca = np.zeros(n_total)
    for nb in notas_boca:
        i0 = int(round(nb['t'] * sr))
        nn = min(int(round(nb['dur'] * sr)), n_total - i0)
        if i0 >= 0 and nn > 0:
            f0_boca[i0:] = float(hz(nb['midi']))
            tt = np.arange(nn) / sr
            env_n = (np.sin(np.minimum(1.0, tt / 0.045) * math.pi / 2.0) ** 2) * (np.sin(np.minimum(1.0, (nn / sr - tt) / 0.11) * math.pi / 2.0) ** 2)
            amp_boca[i0:i0 + nn] = nb['vel'] * env_n

    a_lp = math.exp(-1.0 / (sr * 0.012))
    f0_smooth, _ = lfilter([1.0 - a_lp], [1.0, -a_lp], np.log(f0_boca), zi=[math.log(f0_boca[0]) * a_lp])
    f0_final = np.exp(f0_smooth) * (2.0 ** ((4.0 * np.sin(2.0 * math.pi * 5.2 * t)) / 1200.0))

    ph_boca = 2.0 * math.pi * np.cumsum(f0_final) / sr
    exc_boca = np.zeros(n_total)
    for h_i in range(1, 36):
        exc_boca += np.sin(h_i * ph_boca) / (h_i ** 1.22)
    exc_boca = (exc_boca * 0.35 + rng.normal(0, 0.010, n_total)) * amp_boca

    gates_boca = np.ones(n_total)
    fric_boca = np.zeros(n_total)
    for onset, ph_c, inten in [(0.58, 'k', 0.8), (2.28, 't', 0.7), (6.18, 's', 0.85), (12.38, 'k', 0.9), (15.18, 's', 0.8), (20.58, 'm', 0.85)]:
        ic = int(round(onset * sr))
        dur_c = 0.11 if ph_c == 's' else 0.065
        nc = min(int(round(dur_c * sr)), n_total - ic)
        if ic > 0 and nc > 4:
            ttc = np.arange(nc) / sr
            sh = np.sin(np.minimum(1.0, ttc / 0.008) * math.pi / 2.0) ** 2 * np.sin(np.minimum(1.0, (dur_c - ttc) / 0.025) * math.pi / 2.0) ** 2
            noise_c = sosfilt(butter(2, [2200, 9500], fs=sr, btype='bandpass', output='sos'), rng.normal(0, 1, nc))
            fric_boca[ic:ic + nc] += noise_c * sh * inten * 0.12
            gates_boca[ic:ic + nc] *= (1.0 - 0.65 * sh)

    voz_mono = formantes_boca(exc_boca * gates_boca, formantes_acoplados, sr) * 4.2 + fric_boca
    y_boca = np.column_stack([voz_mono * 0.72, voz_mono * 0.72])

    env_voz = np.sqrt(np.mean(y_boca ** 2, axis=1))
    a_duck = math.exp(-1.0 / (sr * 0.035))
    env_voz_s = lfilter([1.0 - a_duck], [1.0, -a_duck], env_voz)
    duck = 1.0 - 0.24 * np.clip(env_voz_s / 0.08, 0.0, 1.0)

    mix = y_boca + (y_astro * 0.88 + y_bajo * 0.82) * duck[:, None]
    err_mp4 = float(np.max(np.abs(norma_antes_mp4 - norma_despues_mp4)))

    trazas_mp4 = {
        'phi_mp4': phi_mp4,
        'env_bajo_q': env_bajo_q,
        'F1_acoplado': formantes_acoplados[0],
        'F2_acoplado': formantes_acoplados[1],
        'F2_base': formantes_base[1],
        'f0_boca': f0_final,
        'amp_boca': amp_boca,
        'theta_astro': tr_astro['theta_rad'],
    }
    return mix, {'astro': y_astro, 'bajo': y_bajo, 'boca': y_boca}, trazas_mp4, {'error_max_norma_rotacion': err_mp4, 'correlacion_F2_con_bajo': corr_f2_bajo, 'reparto': reparto}


# ───────────── 5. Sonda de Verificación ─────────────
def ejecutar_sonda():
    resultados = {}
    semitonos = [0, 7, 12, 16, 19, 22.68]

    def render_angulo_aislado(th, mezcla=0.5, pan_sp2=True, reparto='impares'):
        # las mediciones de siempre (una hoja, paneo, centroides) siguen con el reparto original 'impares'
        P = PistaRejilla(f'th_{th:.2f}', columnas=2, S_grid=32768, H_grid=16384)
        escribir_acorde_astrolabio_en_pista(P, 0.35, 57, semitonos, th, mezcla=mezcla, dur_base=0.45, pan_en_sp2=pan_sp2, semilla=200, reparto=reparto)
        ZL, ZR = P.escribir()
        y_t = P.tiempo(0.0, 1.0)
        return ZL[0], ZR[0], y_t[:, 0]

    z0_1, _, y0_1 = render_angulo_aislado(0.0, mezcla=1.0, pan_sp2=True)
    z2pi_1, _, y2pi_1 = render_angulo_aislado(2.0 * math.pi, mezcla=1.0, pan_sp2=True)
    corr_mag_una_hoja = float(np.corrcoef(np.abs(z0_1), np.abs(z2pi_1))[0, 1])
    corr_onda_una_hoja = float(np.corrcoef(y0_1, y2pi_1)[0, 1])

    z0_err, _, _ = render_angulo_aislado(0.0, mezcla=0.5, pan_sp2=False)
    z2pi_err, _, _ = render_angulo_aislado(2.0 * math.pi, mezcla=0.5, pan_sp2=False)
    caida_err_db = 10.0 * math.log10((float(np.sum(np.abs(z2pi_err[105:116]) ** 2)) + 1e-24) / (float(np.sum(np.abs(z0_err[105:116]) ** 2)) + 1e-24))

    z0_2, _, y0_2 = render_angulo_aislado(0.0, mezcla=0.5, pan_sp2=True)
    zpi2_2, _, ypi2_2 = render_angulo_aislado(math.pi / 2.0, mezcla=0.5, pan_sp2=True)
    z2pi_2, _, y2pi_2 = render_angulo_aislado(2.0 * math.pi, mezcla=0.5, pan_sp2=True)
    z4pi_2, _, y4pi_2 = render_angulo_aislado(4.0 * math.pi, mezcla=0.5, pan_sp2=True)

    e_fund_0_iso = float(np.sum(np.abs(z0_2[105:116]) ** 2))
    e_fund_2pi_iso = float(np.sum(np.abs(z2pi_2[105:116]) ** 2))
    e_fund_4pi_iso = float(np.sum(np.abs(z4pi_2[105:116]) ** 2))
    caida_iso_db = 10.0 * math.log10((e_fund_2pi_iso + 1e-24) / (e_fund_0_iso + 1e-24))
    regreso_iso_db = 10.0 * math.log10((e_fund_4pi_iso + 1e-24) / (e_fund_0_iso + 1e-24))

    P_doble_sec = PistaRejilla('doble_hoja_sec', columnas=8, S_grid=32768, H_grid=16384)
    for col_idx, th in [(0, 0.0), (2, math.pi / 2.0), (4, 2.0 * math.pi), (6, 4.0 * math.pi)]:
        escribir_acorde_astrolabio_en_pista(P_doble_sec, col_idx * 1.0 + 0.35, 57, semitonos, th, mezcla=0.5, dur_base=0.45, pan_en_sp2=True, semilla=200, reparto='impares')
    ZL_2, ZR_2 = P_doble_sec.escribir()
    wav_spec = INTER_DIR / 'sonda_doble_hoja_spectrumsynth.wav'
    escala_spec = sintetizar_spectrumsynth(ZL_2, ZR_2, wav_spec, S_grid=32768)
    sr_w, y_ffmpeg = wavfile.read(wav_spec)
    y_ffmpeg = y_ffmpeg.astype(np.float64) * escala_spec
    y_tiempo = P_doble_sec.tiempo(0.0, 8.0)

    diff = y_ffmpeg - y_tiempo
    snr_db = 10.0 * math.log10(np.sum(y_tiempo ** 2) / (np.sum(diff ** 2) + 1e-24))
    err_rel_max = float(np.max(np.abs(diff)) / (np.max(np.abs(y_tiempo)) + 1e-12))
    resultados['spectrumsynth_vs_tiempo'] = {
        'SNR_dB': round(snr_db, 2),
        'error_relativo_max': round(err_rel_max, 6),
        'sample_rate_rejilla': 32768,
        'filas_por_canal': 16384
    }

    e_fund_0_sec = float(np.sum(np.abs(ZL_2[0, 105:116]) ** 2))
    e_fund_2pi_sec = float(np.sum(np.abs(ZL_2[4, 105:116]) ** 2))
    caida_sec_db = 10.0 * math.log10((e_fund_2pi_sec + 1e-24) / (e_fund_0_sec + 1e-24))

    freqs_grid = np.arange(16384, dtype=float)
    cent_0 = float(np.sum(freqs_grid * (np.abs(z0_2) ** 2)) / np.sum(np.abs(z0_2) ** 2))
    cent_2pi = float(np.sum(freqs_grid * (np.abs(z2pi_2) ** 2)) / np.sum(np.abs(z2pi_2) ** 2))
    cent_4pi = float(np.sum(freqs_grid * (np.abs(z4pi_2) ** 2)) / np.sum(np.abs(z4pi_2) ** 2))

    def duracion_efectiva_rms(sig):
        env2 = sig ** 2
        env2 /= (np.sum(env2) + 1e-24)
        t_loc = np.arange(len(sig)) / 32768.0
        mu = np.sum(t_loc * env2)
        return float(np.sqrt(np.sum(((t_loc - mu) ** 2) * env2)))

    sigma_t_0 = duracion_efectiva_rms(y0_2)
    sigma_t_pi2 = duracion_efectiva_rms(ypi2_2)

    resultados['experimento_hojas'] = {
        'una_hoja_aislada': {
            'correlacion_magnitud_0_vs_2pi': round(corr_mag_una_hoja, 6),
            'correlacion_onda_0_vs_2pi': round(corr_onda_una_hoja, 6),
        },
        'paneo_erroneo_en_theta_medios': {
            'caida_fundamental_en_2pi_dB': round(caida_err_db, 2),
        },
        'doble_hoja_interferometrica': {
            'caida_fundamental_aislada_en_2pi_dB': round(caida_iso_db, 2),
            'caida_fundamental_secuencial_con_cola_previa_dB': round(caida_sec_db, 2),
            'recuperacion_fundamental_en_4pi_dB': round(regreso_iso_db, 2),
            'centroide_theta_0_Hz': round(cent_0, 1),
            'centroide_theta_2pi_Hz': round(cent_2pi, 1),
            'centroide_theta_4pi_Hz': round(cent_4pi, 1),
            'dispersion_temporal_acorde_theta_0_s': round(sigma_t_0, 4),
            'dispersion_temporal_ritmo_theta_pi2_s': round(sigma_t_pi2, 4),
        }
    }
    # Los tres repartos, testigo + viajera a mitad y mitad: energía en π/2, 2π y 4π contra θ = 0 (fundamental y total)
    def energia(z, lo=None, hi=None):
        return float(np.sum(np.abs(z[lo:hi]) ** 2))

    def db(x, y):
        return round(10.0 * math.log10((x + 1e-30) / (y + 1e-30)), 2)

    def cen(z):
        return round(float(np.sum(freqs_grid * np.abs(z) ** 2) / (np.sum(np.abs(z) ** 2) + 1e-30)), 1)
    rep = {}
    for r in REPARTOS:
        zs = {k: render_angulo_aislado(th, 0.5, True, r)[0] for k, th in (('0', 0.0), ('pi2', math.pi / 2), ('2pi', 2 * math.pi), ('4pi', 4 * math.pi))}
        rep[r] = {
            'fundamental_2pi_dB': db(energia(zs['2pi'], 105, 116), energia(zs['0'], 105, 116)),
            'total_2pi_dB': db(energia(zs['2pi']), energia(zs['0'])),
            'total_pi2_dB': db(energia(zs['pi2']), energia(zs['0'])),
            'total_4pi_dB': db(energia(zs['4pi']), energia(zs['0'])),
            'centroide_0_Hz': cen(zs['0']),
            'centroide_pi2_Hz': cen(zs['pi2']),
        }
    resultados['repartos'] = rep
    return resultados


# ───────────── 6. Utilidades de Audio y Gráficas (Estándar Rejilla) ─────────────
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
    freqs = np.geomspace(48.0, 11000.0, h)[::-1]
    rows = np.array([np.interp(freqs, f, db[:, j]) for j in range(db.shape[1])]).T
    v = np.clip((rows + 82.0) / 66.0, 0.0, 1.0)
    c_low = np.array(BG, dtype=float)
    c_mid = np.array(COL_HOJA_NEG, dtype=float)
    c_hi = np.array(COL_HOJA_POS, dtype=float)
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

# ───────────── 7. Generación de las 3 Láminas PNG y el GIF ─────────────
def crear_lamina_01_teoria_y_sonda(sonda_res, path_png):
    W, H = 1600, 960
    im = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(im)
    f_title = cargar_fuente(26, bold=True)
    f_sub = cargar_fuente(15)
    f_sec = cargar_fuente(17, bold=True)
    f_txt = cargar_fuente(13)
    f_sm = cargar_fuente(11)

    dr.text((48, 26), '01 · EL ASTROLABIO METAPLÉCTICO (Mp2) · RECUBRIMIENTO DOBLE Y SONDA', font=f_title, fill=FG)
    dr.text((48, 64), f'Semilla {SEMILLA} · Prueba exacta en spectrumsynth (SNR {sonda_res["spectrumsynth_vs_tiempo"]["SNR_dB"]} dB) · Interferómetro Hoja Testigo + Hoja Viajera', font=f_sub, fill=MUTED)

    dr.rectangle((48, 110, 775, 555), fill=PANEL_BG, outline=GRID_COL, width=2)
    dr.text((68, 126), 'Geometría en el espacio fase (q = tiempo, p = frecuencia)', font=f_sec, fill=COL_HOJA_POS)

    angulos = [
        (0.0, 'θ = 0 (Hoja +1)\nAcorde vertical', COL_HOJA_POS),
        (math.pi / 2.0, 'θ = π/2 (Cáustica)\nAcorde → Ritmo', COL_RITMO),
        (2.0 * math.pi, 'θ = 2π (Hoja −1)\nimpares: hueca', COL_HOJA_NEG),
        (4.0 * math.pi, 'θ = 4π (Hoja +1)\n2ª vuelta: resurge', COL_CAUSTICA),
    ]
    for i, (th, label, col) in enumerate(angulos):
        cx = 148 + i * 170
        cy = 315
        r_box = 66
        dr.rectangle((cx - r_box, cy - r_box, cx + r_box, cy + r_box), outline=GRID_COL, width=1)
        dr.line((cx - r_box, cy, cx + r_box, cy), fill=GRID_COL, width=1)
        dr.line((cx, cy - r_box, cx, cy + r_box), fill=GRID_COL, width=1)
        for k_p in range(-2, 4):
            p0 = (k_p - 0.5) * 19.0
            q0 = 0.0
            qr = q0 * math.cos(th) + p0 * math.sin(th)
            pr = -q0 * math.sin(th) + p0 * math.cos(th)
            px, py = cx + qr, cy - pr
            if abs(th - 2 * math.pi) < 0.1:
                dr.ellipse((px - 6, py - 6, px + 6, py + 6), outline=col, width=2)
            else:
                dr.ellipse((px - 6, py - 6, px + 6, py + 6), fill=col)
        dr.text((cx - 66, cy + r_box + 14), label, font=f_sm, fill=col)
    dr.text((68, 502), 'Eje q: tiempo · Eje p: frecuencia · Círculo hueco: fundamental cancelada (−ψ)', font=f_sm, fill=MUTED)

    dr.rectangle((805, 110, 1552, 555), fill=PANEL_BG, outline=GRID_COL, width=2)
    dr.text((825, 126), 'Hallazgos medidos en la sonda', font=f_sec, fill=COL_HOJA_NEG)

    exp = sonda_res['experimento_hojas']
    u_info = exp['una_hoja_aislada']
    p_err = exp['paneo_erroneo_en_theta_medios']
    d_info = exp['doble_hoja_interferometrica']

    rp = sonda_res['repartos']
    lineas_sonda = [
        (f'1. Una hoja sola: onda {u_info["correlacion_onda_0_vs_2pi"]:+.2f}, magnitud {u_info["correlacion_magnitud_0_vs_2pi"]:+.2f} → no se oye', COL_RITMO),
        (f'2. Paneo en cos(θ/2): {p_err["caida_fundamental_en_2pi_dB"]:+.1f} dB · en cos(θ) [Sp2]: {d_info["caida_fundamental_aislada_en_2pi_dB"]:+.1f} dB', COL_HOJA_POS),
        ('3. Reparto de fase (testigo + viajera, mitad y mitad), en 2π:', COL_CAUSTICA),
        (f'   • hermite e^-i(m+½)θ: total {rp["hermite"]["total_2pi_dB"]:+.0f} dB → se borra; 4π {rp["hermite"]["total_4pi_dB"]:+.2f} dB', FG),
        (f'     ≈ global: en π/2 centroide {rp["hermite"]["centroide_pi2_Hz"]:.0f} vs {rp["global"]["centroide_pi2_Hz"]:.0f} Hz (las hojas no se tocan)', MUTED),
        (f'   • global −θ/2: total {rp["global"]["total_2pi_dB"]:+.0f} dB → se borra (sólo el signo)', FG),
        (f'   • impares (original): fundamental {rp["impares"]["fundamental_2pi_dB"]:+.0f} dB, total {rp["impares"]["total_2pi_dB"]:+.1f} dB', FG),
        (f'     → octava hueca, centroide {d_info["centroide_theta_0_Hz"]:.0f} → {d_info["centroide_theta_2pi_Hz"]:.0f} Hz (filtro de impares)', MUTED),
        (f'4. Anchura temporal: {d_info["dispersion_temporal_acorde_theta_0_s"]*1000:.0f} ms (acorde) → {d_info["dispersion_temporal_ritmo_theta_pi2_s"]*1000:.0f} ms (ritmo, θ=π/2)', COL_RITMO),
    ]
    yy = 166
    for txt, col in lineas_sonda:
        dr.text((825, yy), txt, font=f_txt, fill=col)
        yy += 37

    dr.rectangle((48, 580, 1552, 915), fill=PANEL_BG, outline=GRID_COL, width=2)
    dr.text((68, 596), 'Recubrimiento doble: trayectoria simpléctica cos(θ) [periodo 2π] vs fase metapléctica cos(θ/2) [periodo 4π]', font=f_sec, fill=FG)

    th_grid = np.linspace(0, 4 * math.pi, 1200)
    symp_curve = np.cos(th_grid)
    meta_curve = np.cos(th_grid / 2.0)
    caust_curve = np.exp(-((np.abs(np.sin(th_grid)) - 1.0) ** 2) / 0.045)

    box_c = (240, 645, 1230, 210)
    dr.rectangle((240, 645, 240 + 1230, 645 + 210), outline=GRID_COL, width=1)
    dr.line((240, 645 + 105, 240 + 1230, 645 + 105), fill=GRID_COL, width=1)
    dibujar_curva(dr, symp_curve, box_c, MUTED, -1.05, 1.05, width=2)
    dibujar_curva(dr, meta_curve, box_c, COL_HOJA_POS, -1.05, 1.05, width=3)
    dibujar_curva(dr, caust_curve * 2.0 - 1.0, box_c, COL_CAUSTICA, -1.05, 1.05, width=2)

    dr.text((68, 665), 'cos(θ/2) · Hoja Mp2', font=f_txt, fill=COL_HOJA_POS)
    dr.text((68, 710), 'cos(θ) · Posición Sp2', font=f_txt, fill=MUTED)
    dr.text((68, 755), 'Cáustica de Maslov', font=f_txt, fill=COL_CAUSTICA)

    for mult_pi, lbl in [(0, 'θ=0 (Hoja +1)'), (0.5, 'π/2 (Ritmo)'), (1.0, 'π (Espejo)'), (2.0, '2π (Hoja −1: hueco)'), (3.0, '3π (Cáustica)'), (4.0, '4π (Hoja +1)')]:
        xx = 240 + (mult_pi / 4.0) * 1230
        dr.line((xx, 645, xx, 855), fill=GRID_COL, width=1)
        dr.text((xx - 36, 868), lbl, font=f_sm, fill=FG)

    im.save(str(path_png), 'PNG')
    return im

def crear_lamina_02_muestra_aislada(y_solo, tr_solo, med_solo, path_png, reparto='hermite'):
    hueca = reparto == 'impares'
    W, H = 1600, 960
    im = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(im)
    f_title = cargar_fuente(26, bold=True)
    f_sub = cargar_fuente(15)
    f_sec = cargar_fuente(16, bold=True)
    f_sm = cargar_fuente(12)

    dr.text((48, 26), f'02 · MUESTRA AISLADA · EL ASTROLABIO METAPLÉCTICO (24 s) · reparto {reparto}', font=f_title, fill=FG)
    dr.text((48, 64), f'Archivo: {med_solo["m4a"]} · {med_solo["I_LUFS"]:.1f} LUFS · {med_solo["pico_dBTP"]:.1f} dBTP · LRA {med_solo["LRA"]:.1f} · Semilla {SEMILLA}', font=f_sub, fill=MUTED)

    x0, w_plot = 235, 1310
    secciones = [
        (0.0, 'I · Hoja +1 (θ=0: acorde)'),
        (4.5, 'II · Giro FrFT (θ→π/2: diagonal/ritmo)'),
        (9.8, 'III · Espejo (θ=π)'),
        (13.5, 'IV · Hoja −1 (θ=2π: ' + ('sombra hueca' if hueca else 'se borra') + ')'),
        (19.0, 'V · 2ª vuelta (θ=4π: regreso +1)')
    ]
    for sec_t, sec_lbl in secciones:
        xx = x0 + (sec_t / 24.0) * w_plot
        dr.line((xx, 115, xx, 885), fill=GRID_COL, width=1)
        dr.text((xx + 5, 112), sec_lbl, font=f_sm, fill=FG)

    controles = [
        ('theta_rad', 'Giro θ (0 → 4π)', 0.0, 4.0 * math.pi, COL_HOJA_POS),
        ('hoja_maslov', 'Signo cos(θ/2)', -1.05, 1.05, COL_HOJA_NEG),
        ('compresion_a', 'Dilatación a(t)', 0.6, 1.6, COL_RITMO),
        ('caustica_maslov', 'Cáustica Maslov', 0.0, 1.05, COL_CAUSTICA),
    ]
    for idx, (k_c, lab, lo, hi, col) in enumerate(controles):
        yy = 145 + idx * 92
        dr.rectangle((x0, yy, x0 + w_plot, yy + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
        dr.text((48, yy + 24), lab, font=f_sec, fill=col)
        dibujar_curva(dr, tr_solo[k_c], (x0, yy + 4, w_plot, 64), col, lo, hi, width=2)

    yy_w = 520
    dr.rectangle((x0, yy_w, x0 + w_plot, yy_w + 88), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy_w + 30), 'Onda estéreo', font=f_sec, fill=FG)
    y_norm_vis = normalizar_nivel(y_solo)
    dibujar_curva(dr, y_norm_vis[:, 0], (x0, yy_w + 4, w_plot, 80), COL_HOJA_POS, -0.75, 0.75, width=1)

    yy_s = 628
    spec_im = espectrograma_imagen(y_solo, SR, w_plot, 250)
    im.paste(spec_im, (x0, yy_s))
    dr.rectangle((x0, yy_s, x0 + w_plot, yy_s + 250), outline=GRID_COL, width=1)
    dr.text((48, yy_s + 20), 'Espectrograma\n48 Hz – 11 kHz', font=f_sec, fill=FG)
    dr.text((48, yy_s + 80), ('En IV (θ=2π) se ve\nel hueco grave de\nla fundamental\n(110 Hz cancelada)' if hueca else 'En IV (θ=2π) la\nviajera borra a su\ntestigo: silencio\nhasta la 2ª vuelta'), font=f_sm, fill=COL_HOJA_NEG)

    for s_tick in range(0, 25, 3):
        xx = x0 + (s_tick / 24.0) * w_plot
        dr.text((xx - 10, 892), f'{s_tick} s', font=f_sm, fill=MUTED)
    dr.text((48, 922), ('Lectura: en IV (13.5–18.5 s) las notas caen en el mismo sitio que en I, pero la Hoja −1 borra la fundamental y deja los armónicos pares.' if hueca else 'Lectura: cada armónico m gira con e^-i(m+½)θ; en 2π todos llevan −1 y la viajera borra a su testigo (IV en silencio); en 4π la nota vuelve entera.'), font=f_sm, fill=MUTED)

    im.save(str(path_png), 'PNG')
    return im

def crear_lamina_03_escena_mp4(y_mix, tr_mp4, med_mix, info_mp4, path_png):
    W, H = 1600, 960
    im = Image.new('RGB', (W, H), BG)
    dr = ImageDraw.Draw(im)
    f_title = cargar_fuente(26, bold=True)
    f_sub = cargar_fuente(15)
    f_sec = cargar_fuente(16, bold=True)
    f_sm = cargar_fuente(11)

    dr.text((48, 26), '03 · ESCENA · ASTROLABIO + BAJO + BOCA DE FORMANTES · ROTACIÓN BAJO↔BOCA', font=f_title, fill=FG)
    dr.text((48, 64), f'Archivo: {med_mix["m4a"]} · {med_mix["I_LUFS"]:.1f} LUFS · reparto {info_mp4["reparto"]} · F2 sigue al bajo: r = {info_mp4["correlacion_F2_con_bajo"]["phi_0"]:+.2f} (φ=0) → {info_mp4["correlacion_F2_con_bajo"]["phi_pi2"]:+.2f} (φ=π/2)', font=f_sub, fill=MUTED)

    x0, w_plot = 235, 1310
    secciones = [
        (0.0, 'I · Presentación (φ=0, θ=0)'),
        (6.0, 'II · Rotación (φ=π/2: la boca canta el bajo)'),
        (12.0, 'III · Hoja −1 (θ=2π: hueco vocal)'),
        (18.0, 'IV · Regreso (θ=4π, φ=0)')
    ]
    for sec_t, sec_lbl in secciones:
        xx = x0 + (sec_t / 24.0) * w_plot
        dr.line((xx, 115, xx, 885), fill=GRID_COL, width=1)
        dr.text((xx + 5, 112), sec_lbl, font=f_sm, fill=FG)

    filas = [
        ('phi_mp4', 'Ángulo φ(t)', 0.0, math.pi / 2.0 + 0.1, COL_MP4),
        ('env_bajo_q', 'Pulso Bajo q1(t)', 0.0, 1.2, COL_HOJA_POS),
        ('F2_acoplado', 'Boca F2 (Hz) p2(t)', 650.0, 2800.0, COL_CAUSTICA),
        ('theta_astro', 'Astrolabio θ(t)', 0.0, 4.0 * math.pi + 0.2, COL_HOJA_NEG),
    ]
    for idx, (k_c, lab, lo, hi, col) in enumerate(filas):
        yy = 145 + idx * 92
        dr.rectangle((x0, yy, x0 + w_plot, yy + 72), fill=PANEL_BG, outline=GRID_COL, width=1)
        dr.text((48, yy + 24), lab, font=f_sec, fill=col)
        if k_c == 'F2_acoplado':
            dibujar_curva(dr, tr_mp4['F2_base'], (x0, yy + 4, w_plot, 64), MUTED, lo, hi, width=1)
        dibujar_curva(dr, tr_mp4[k_c], (x0, yy + 4, w_plot, 64), col, lo, hi, width=2)

    yy_w = 520
    dr.rectangle((x0, yy_w, x0 + w_plot, yy_w + 88), fill=PANEL_BG, outline=GRID_COL, width=1)
    dr.text((48, yy_w + 20), 'Melodía Boca\nf0 (Hz)', font=f_sec, fill=COL_RITMO)
    dibujar_curva(dr, tr_mp4['f0_boca'] * (tr_mp4['amp_boca'] > 0.05), (x0, yy_w + 6, w_plot, 76), COL_RITMO, 180.0, 380.0, width=2)

    yy_s = 628
    spec_im = espectrograma_imagen(y_mix, SR, w_plot, 250)
    im.paste(spec_im, (x0, yy_s))
    dr.rectangle((x0, yy_s, x0 + w_plot, yy_s + 250), outline=GRID_COL, width=1)
    dr.text((48, yy_s + 20), 'Espectrograma\nMezcla', font=f_sec, fill=FG)
    dr.text((48, yy_s + 80), 'En II (6–12 s) el\nbajo ondula F2; en\nIII (12–18 s) la\nHoja −1 abre hueco\npara el solo vocal.', font=f_sm, fill=COL_MP4)

    for s_tick in range(0, 25, 3):
        xx = x0 + (s_tick / 24.0) * w_plot
        dr.text((xx - 10, 892), f'{s_tick} s', font=f_sm, fill=MUTED)
    dr.text((48, 922), 'Costura metapléctica: el hueco de la Hoja −1 en 12–18 s despeja el registro grave/medio sin apagar la armonía.', font=f_sm, fill=MUTED)

    im.save(str(path_png), 'PNG')
    return im


def main():
    print('1. Ejecutando sonda del Astrolabio Metapléctico...', flush=True)
    sonda_res = ejecutar_sonda()
    print('   Sonda OK:', json.dumps(sonda_res, ensure_ascii=False), flush=True)

    print('2. Sintetizando muestra aislada de 24 s...', flush=True)
    partitura_solo = {
        'prototipo': 'astrolabio-metaplectico',
        'duracion': 24.0,
        'semilla': SEMILLA,
        'giro_theta_rad': [[0.0, 0.0], [4.0, 0.0], [6.5, math.pi / 4.0], [8.5, math.pi / 2.0], [11.5, math.pi], [14.0, 2.0 * math.pi], [18.0, 2.0 * math.pi], [20.5, 3.0 * math.pi], [22.0, 4.0 * math.pi], [24.0, 4.0 * math.pi]],
        'compresion_a': [[0.0, 1.0], [6.0, 1.414], [11.0, 0.707], [15.0, 1.0], [24.0, 1.0]],
        'cizalla_chirp': [[0.0, 0.0], [5.5, 0.65], [9.5, -0.65], [14.0, 0.0], [24.0, 0.0]],
        'mezcla_hojas': [[0.0, 0.5], [24.0, 0.5]],
        'reparto': 'hermite',
        'eventos': [
            {'t_c': 1.8, 'midi': 57, 'semitonos': [0, 7, 12, 16, 19, 22.68, 26.04], 'theta': 0.0, 'comp_a': 1.0, 'chirp_c': 0.0, 'vel': 0.88},
            {'t_c': 5.5, 'midi': 57, 'semitonos': [0, 7, 12, 16, 19, 22.68, 26.04], 'theta': math.pi / 4.0, 'comp_a': 1.35, 'chirp_c': 0.55, 'vel': 0.85},
            {'t_c': 8.2, 'midi': 57, 'semitonos': [0, 7, 12, 16, 19, 22.68, 26.04], 'theta': math.pi / 2.0, 'comp_a': 1.25, 'chirp_c': 0.25, 'vel': 0.90},
            {'t_c': 11.2, 'midi': 57, 'semitonos': [0, 7, 12, 16, 19, 22.68, 26.04], 'theta': math.pi, 'comp_a': 0.78, 'chirp_c': -0.50, 'vel': 0.85},
            {'t_c': 14.8, 'midi': 57, 'semitonos': [0, 7, 12, 16, 19, 22.68, 26.04], 'theta': 2.0 * math.pi, 'comp_a': 1.0, 'chirp_c': 0.0, 'vel': 0.88},
            {'t_c': 17.2, 'midi': 57, 'semitonos': [0, 7, 12, 16, 19, 22.68, 26.04], 'theta': 2.0 * math.pi, 'comp_a': 1.0, 'chirp_c': 0.0, 'vel': 0.86},
            {'t_c': 21.2, 'midi': 57, 'semitonos': [0, 7, 12, 16, 19, 22.68, 26.04], 'theta': 4.0 * math.pi, 'comp_a': 1.0, 'chirp_c': 0.0, 'vel': 0.92},
        ]
    }
    y_solo, tr_solo, info_solo = render_astrolabio_temporal(partitura_solo, 24.0, SR, SEMILLA)
    med_solo = guardar_audio_y_medir(
        y_solo,
        OUT_DIR / 'muestra-astrolabio-hermite-s20261020.wav',
        OUT_DIR / 'muestra-astrolabio-hermite-s20261020.m4a',
        target_lufs=-18.5
    )
    # la misma partitura con el reparto original, para comparar (sale igual a la muestra de la primera corrida)
    partitura_impares = {**partitura_solo, 'reparto': 'impares'}
    y_imp, tr_imp, _ = render_astrolabio_temporal(partitura_impares, 24.0, SR, SEMILLA)
    med_imp = guardar_audio_y_medir(
        y_imp,
        OUT_DIR / 'muestra-astrolabio-impares-s20261020.wav',
        OUT_DIR / 'muestra-astrolabio-impares-s20261020.m4a',
        target_lufs=-18.5
    )

    print('3. Sintetizando escena (Astrolabio + Bajo + boca de formantes, rotación bajo↔boca)...', flush=True)
    y_mix, stems_mp4, tr_mp4, info_mp4 = render_escena_mp4(24.0, SR, SEMILLA)
    med_mix = guardar_audio_y_medir(
        y_mix,
        OUT_DIR / 'escena-astrolabio-bajo-boca-s20261020.wav',
        OUT_DIR / 'escena-astrolabio-bajo-boca-s20261020.m4a',
        target_lufs=-16.0
    )

    print('4. Generando láminas PNG en OKLCh y GIF...', flush=True)
    p1 = OUT_DIR / '01-hojas-y-espacio-fase-s20261020.png'
    p2 = OUT_DIR / '02-muestra-hermite-s20261020.png'
    p2b = OUT_DIR / '02b-muestra-impares-s20261020.png'
    p3 = OUT_DIR / '03-escena-bajo-y-boca-s20261020.png'
    im1 = crear_lamina_01_teoria_y_sonda(sonda_res, p1)
    im2 = crear_lamina_02_muestra_aislada(y_solo, tr_solo, med_solo, p2, reparto='hermite')
    im2b = crear_lamina_02_muestra_aislada(y_imp, tr_imp, med_imp, p2b, reparto='impares')
    im3 = crear_lamina_03_escena_mp4(y_mix, tr_mp4, med_mix, info_mp4, p3)

    frames = [im.resize((1200, 720), Image.Resampling.LANCZOS).quantize(colors=256, method=Image.Quantize.MEDIANCUT) for im in (im1, im2, im2b, im3)]
    gif_path = OUT_DIR / 'proceso-astrolabio-s20261020.gif'
    frames[0].save(
        str(gif_path),
        format='GIF',
        save_all=True,
        append_images=frames[1:],
        duration=1800,
        loop=0,
        optimize=True
    )

    shutil.copyfile(__file__, OUT_DIR / 'astrolabio_metaplectico.py')

    receta = {
        'instrumento': 'El Astrolabio Metapléctico (Mp_{2n})',
        'fecha_utc': '2026-10-20',
        'semilla': SEMILLA,
        'sonda': sonda_res,
        'ejecucion_sha256': EJECUCION,
        'muestra_aislada_hermite': med_solo,
        'muestra_aislada_impares': med_imp,
        'escena_bajo_boca': {**med_mix, **info_mp4},
        'gif': {
            'archivo': gif_path.name,
            'duracion_s': 7.2,
            'bytes': gif_path.stat().st_size,
            'cuadros': 4
        },
        'partitura_muestra': partitura_solo
    }
    receta_path = OUT_DIR / 'receta-astrolabio-s20261020.json'
    with open(receta_path, 'w', encoding='utf-8') as f:
        json.dump(receta, f, ensure_ascii=False, indent=2)

    print('5. Todo completado con éxito:', json.dumps(receta['sonda'], ensure_ascii=False, indent=2), flush=True)

if __name__ == '__main__':
    main()