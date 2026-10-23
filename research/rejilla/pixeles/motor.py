"""Motor de «los pixeles y la luna»: la rejilla a 98 bpm con RELOJ MÓVIL.

La pieza modula leyendo la imagen más rápido (5/4 = una tercera mayor justa arriba) sin cambiar
el tempo. Para eso cada sección se ESCRIBE con el reloj de la rejilla a S/r (compases r veces más
largos, alturas en Mi) y se LEE a S: el tiempo vuelve a su lugar y las alturas suben ×r.
Por eso aquí nada guarda S, T ni F como constante: todo se consulta en `M` (musica.py) en el
momento, y `reloj(r)` lo cambia.

Reusa la síntesis modal de musica.py y los instrumentos de esquinas.py (sólo dependen de segundos
y Hz). Importa esquinas ANTES de fijar el tempo (esquinas fija 92 bpm al importarse).
"""
import hashlib, io, math, subprocess, sys
from contextlib import contextmanager
from fractions import Fraction
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.io import wavfile
from scipy.signal import resample_poly

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ))
import musica as M
import esquinas as E

BPM = 98
SEM = 5454
N, H = M.N, M.H
M.fijar_tempo(BPM)
S0, T0 = M.S, M.T                         # el reloj de lectura: 98 bpm, 2.449 s por compás
SR_OUT = 48000
rng = np.random.default_rng(SEM)
M.rng = rng; E.rng = rng
TTS = RAIZ / 'render' / 'tts'


@contextmanager
def reloj(r=1.0):
    """Escribir con la rejilla a S0/r: el compás dura r·T0 mientras se escribe; leído a S0 vuelve a T0
    y todas las alturas suben ×r."""
    viejo = (M.S, M.T, M.F)
    M.S = S0 / r; M.T = N / M.S; M.F = M.S / N
    try: yield
    finally: M.S, M.T, M.F = viejo


def q(b, pos):                            # compás y dieciseisavo → segundos, en el reloj vigente
    return b * M.T + pos * M.T / 16


class Pista(M.Pista):
    def __init__(self, nombre, columnas):
        super().__init__(nombre, columnas)
        self.muestras, self.directo = [], []
        self.S = M.S                      # el reloj con que se escribe esta pista

    def muestra(self, w, t0, g=1.0, pan=0.0):
        """w ya está a self.S muestras por segundo (las voces se remuestrean al reloj de escritura)."""
        gL, gR = M.paneo(pan)
        self.muestras.append((np.asarray(w, float) * g, int(round(t0 * self.S)), gL, gR))

    def escribir(self):
        viejo = (M.S, M.T, M.F)
        M.S = self.S; M.T = N / M.S; M.F = M.S / N
        try:
            ZL, ZR = super().escribir()
        finally:
            M.S, M.T, M.F = viejo
        for w, n0, gL, gR in self.muestras:
            n1 = n0 + len(w)
            for b in range(max(0, n0 // N), min(self.C, -(-n1 // N))):
                a, z = max(n0, b * N), min(n1, (b + 1) * N)
                buf = np.zeros(N); buf[a - b * N:z - b * N] = w[a - n0:z - n0]
                c = np.fft.rfft(buf)[:H] / N; c[0] = 0
                ZL[b] += gL * c; ZR[b] += gR * c
        return ZL, ZR


# ───────────── voces ─────────────
VOCES = {'sabina': 'Microsoft Sabina Desktop', 'zira': 'Microsoft Zira Desktop'}


def a_sr(x, de, a):
    fr = Fraction(a / de).limit_denominator(600)
    return resample_poly(x, fr.numerator, fr.denominator)


def tts(texto, voz='sabina', rapidez=0, sr=48000):
    TTS.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256(f'{voz}|{rapidez}|{texto}'.encode()).hexdigest()[:16]
    ruta = TTS / f'{h}.wav'
    if not ruta.exists():
        ps = ("Add-Type -AssemblyName System.Speech;$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
              f"$s.SelectVoice('{VOCES[voz]}');$s.Rate={rapidez};"
              f"$s.SetOutputToWaveFile('{ruta}');$s.Speak([Console]::In.ReadToEnd());$s.Dispose()")
        subprocess.run(['powershell', '-NoProfile', '-Command', ps], input=texto, text=True, encoding='utf-8',
                       check=True, capture_output=True)
    s, x = wavfile.read(ruta)
    x = x.astype(float)
    if x.ndim > 1: x = x.mean(1)
    x /= (np.abs(x).max() or 1)
    env = np.convolve(np.abs(x), np.ones(256) / 256, 'same')
    vivo = np.where(env > 0.04)[0]
    return a_sr(x[max(0, vivo[0] - 80):vivo[-1] + 400], s, sr)


def f0(x, sr):
    n = len(x); seg = x[int(n * .3):int(n * .7)]
    if len(seg) < 2048: seg = x
    seg = seg - seg.mean()
    L = len(seg); taus = np.arange(int(sr / 1000), int(sr / 70))
    d = np.array([np.sum((seg[:L - t] - seg[t:]) ** 2) for t in taus])
    cm = d * np.arange(1, len(d) + 1) / np.cumsum(d)
    deb = np.where(cm < .15)[0]
    i = deb[0] if len(deb) else int(np.argmin(cm))
    while i + 1 < len(cm) and cm[i + 1] < cm[i]: i += 1
    return sr / taus[i]


def chop(texto, midi, voz='zira', largo=None, sr=None):
    """Sílaba afinada por remuestreo, al reloj de escritura (sr)."""
    sr = sr or M.S
    x = tts(texto, voz, sr=48000); f = f0(x, 48000)
    y = a_sr(x, M.hz(midi) / f * 48000, sr)
    if largo: y = y[:int(largo * sr)]
    k = min(len(y) // 4, int(.004 * sr))
    e = np.ones(len(y)); e[:k] = np.linspace(0, 1, k); e[-4 * k:] *= np.linspace(1, 0, 4 * k)
    return y * e


def cinta(y, sr=SR_OUT, prof_ms=1.6, f=0.55, flutter_ms=.18, ff=6.3, semilla=1):
    """Wow y flutter de casete: un retraso que ondula (en el tiempo, después de la rejilla)."""
    r = np.random.default_rng(semilla)
    n = len(y); t = np.arange(n) / sr
    d = (prof_ms * np.sin(2 * np.pi * f * t + r.uniform(0, 6)) + flutter_ms * np.sin(2 * np.pi * ff * t)) / 1000 * sr
    idx = np.clip(np.arange(n) - d - prof_ms / 1000 * sr * 1.2, 0, n - 1)
    i0 = np.floor(idx).astype(int); fr = idx - i0; i1 = np.minimum(i0 + 1, n - 1)
    if y.ndim == 1: return y[i0] * (1 - fr) + y[i1] * fr
    return y[i0] * (1 - fr)[:, None] + y[i1] * fr[:, None]


# ───────────── gestos de imagen ─────────────
def tornasol(Z, cols, tau_ms, profundidad=.85):
    """La película de aceite: interferencia de dos reflejos con retraso tau = peine |cos(π f τ)|.
    Un τ por columna (para que se mueva, se tejen varias versiones)."""
    Z = Z.copy(); f = np.arange(Z.shape[1]) * (S0 / N)
    for c, tau in zip(cols, np.broadcast_to(tau_ms, len(cols))):
        peine = (1 - profundidad) + profundidad * np.abs(np.cos(np.pi * f * tau / 1000))
        Z[c] = Z[c] * peine
    return Z


def arena(Z, cols, generaciones, calidad=85):
    """JPEG generación tras generación, corriendo la imagen entre pasadas (si no, JPEG es idempotente)."""
    Z = Z.copy(); sub = Z[cols]
    mx = np.abs(sub).max() or 1
    u_m = np.clip((20 * np.log10(np.abs(sub) / mx + 1e-12) + 70) / 70, 0, 1) * 255
    u_p = (np.angle(sub) + np.pi) / (2 * np.pi) * 255
    def jpeg(u, g):
        out = u.copy()
        for gen in range(g):
            corr = 3 * (gen % 8) + 1
            out = np.roll(out, corr, axis=1); partes = []
            for h0 in range(0, out.shape[1], 32768):
                im = Image.fromarray(np.round(np.clip(out[:, h0:h0 + 32768], 0, 255).T).astype(np.uint8))
                b = io.BytesIO(); im.save(b, 'JPEG', quality=calidad); b.seek(0)
                partes.append(np.array(Image.open(b)).T.astype(float))
            out = np.roll(np.concatenate(partes, 1), -corr, axis=1)
        return out
    for i, (c, g) in enumerate(zip(cols, generaciones)):
        if not g: continue
        m_, p_ = jpeg(u_m[i:i + 1], g)[0], jpeg(u_p[i:i + 1], g)[0]
        Z[c] = np.where(m_ > .5, mx * 10 ** ((m_ / 255 * 70 - 70) / 20), 0) * np.exp(1j * (p_ / 255 * 2 * np.pi - np.pi))
    return Z


# ───────────── síntesis ─────────────
def sintetizar(ZL, ZR, wav, sr=None):
    """Imagen 16 bits → spectrumsynth (leída a `sr`, por defecto S0) → 48 kHz. Devuelve la escala."""
    filas = ZL.shape[1]
    mag = np.empty((2 * filas, ZL.shape[0])); pha = np.empty_like(mag)
    mag[:filas] = np.abs(ZR).T[::-1]; mag[filas:] = np.abs(ZL).T[::-1]
    pha[:filas] = np.angle(ZR).T[::-1]; pha[filas:] = np.angle(ZL).T[::-1]
    esc = mag.max() or 1.0
    m16 = np.round(mag / esc * 65535).astype('<u2'); p16 = np.round((pha + np.pi) / (2 * np.pi) * 65535).astype('<u2')
    wav = Path(wav); mr, pr = wav.with_suffix('.mag.raw'), wav.with_suffix('.fase.raw')
    m16.tofile(mr); p16.tofile(pr)
    W = ZL.shape[0]
    ent = lambda r: ['-f', 'rawvideo', '-pix_fmt', 'gray16le', '-s', f'{W}x{2 * filas}', '-r', '1', '-i', str(r)]
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', *ent(mr), *ent(pr), '-filter_complex',
                    '[0]setpts=N/TB,format=gray16le[m];[1]setpts=N/TB,format=gray16le[p];'
                    f'[m][p]spectrumsynth=sample_rate={int(round(sr or S0))}:channels=2:scale=lin:slide=fullframe:win_func=rect:overlap=0,'
                    f'aresample={SR_OUT}:filter_size=64:phase_shift=12', '-c:a', 'pcm_f32le', str(wav)], check=True)
    mr.unlink(); pr.unlink()
    return esc


def leer(wav, esc=1.0):
    sr, x = wavfile.read(wav)
    return x.astype(float) * esc
