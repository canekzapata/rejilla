"""Motor de «sobre la aurora»: la rejilla a 104 bpm, voces y gestos de imagen.

Reusa la síntesis modal de musica.py y los instrumentos de esquinas.py (que sólo dependen de
segundos y Hz, no del tempo). Importa esquinas ANTES de fijar el tempo: esquinas fija 92 bpm
al importarse y aquí se pisa con 104.
"""
import hashlib, io, math, subprocess, sys
from fractions import Fraction
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.io import wavfile
from scipy.signal import resample_poly, butter, sosfilt

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ))
import musica as M
import esquinas as E                      # fija 92 bpm al importarse…

BPM = 104
SEM = 1015
M.fijar_tempo(BPM)                        # …y aquí se pisa
S, N, H, T, F = M.S, M.N, M.H, M.T, M.F
M._bordes = np.round(np.geomspace(30, 14000, M.VISTA + 1) / F).astype(int)
SR_OUT = 48000
rng = np.random.default_rng(SEM)
M.rng = rng; E.rng = rng                  # todos los instrumentos siembran de aquí
TTS = RAIZ / 'render' / 'tts'


class Pista(M.Pista):
    """Modos con fórmula cerrada + muestras con su DFT + columnas escritas directo."""
    def __init__(self, nombre, columnas):
        super().__init__(nombre, columnas)
        self.muestras, self.directo = [], []

    def muestra(self, w, t0, g=1.0, pan=0.0):
        gL, gR = M.paneo(pan)
        self.muestras.append((np.asarray(w, float) * g, int(round(t0 * S)), gL, gR))

    def columna(self, b, ZcL, ZcR):
        """Escribir una columna a mano (estática, ruido incorporado…)."""
        self.directo.append((b, ZcL, ZcR))

    def escribir(self):
        ZL, ZR = super().escribir()
        for w, n0, gL, gR in self.muestras:
            n1 = n0 + len(w)
            for b in range(max(0, n0 // N), min(self.C, -(-n1 // N))):
                a, z = max(n0, b * N), min(n1, (b + 1) * N)
                buf = np.zeros(N); buf[a - b * N:z - b * N] = w[a - n0:z - n0]
                c = np.fft.rfft(buf)[:H] / N; c[0] = 0
                ZL[b] += gL * c; ZR[b] += gR * c
        for b, cL, cR in self.directo:
            ZL[b] += cL; ZR[b] += cR
        return ZL, ZR


# ───────────── voces ─────────────
VOCES = {'sabina': 'Microsoft Sabina Desktop', 'zira': 'Microsoft Zira Desktop'}


def a_sr(x, de, a):
    fr = Fraction(a / de).limit_denominator(400)
    return resample_poly(x, fr.numerator, fr.denominator)


def tts(texto, voz='sabina', rapidez=0):
    TTS.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256(f'{voz}|{rapidez}|{texto}'.encode()).hexdigest()[:16]
    ruta = TTS / f'{h}.wav'
    if not ruta.exists():
        ps = ("Add-Type -AssemblyName System.Speech;$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
              f"$s.SelectVoice('{VOCES[voz]}');$s.Rate={rapidez};"
              f"$s.SetOutputToWaveFile('{ruta}');$s.Speak([Console]::In.ReadToEnd());$s.Dispose()")
        subprocess.run(['powershell', '-NoProfile', '-Command', ps], input=texto, text=True, encoding='utf-8',
                       check=True, capture_output=True)
    sr, x = wavfile.read(ruta)
    x = x.astype(float)
    if x.ndim > 1: x = x.mean(1)
    x /= (np.abs(x).max() or 1)
    env = np.convolve(np.abs(x), np.ones(256) / 256, 'same')
    vivo = np.where(env > 0.04)[0]
    return a_sr(x[max(0, vivo[0] - 80):vivo[-1] + 400], sr, S)


def f0(x):
    n = len(x); seg = x[int(n * .3):int(n * .7)]
    if len(seg) < 2048: seg = x
    seg = seg - seg.mean()
    ac = np.correlate(seg, seg, 'full')[len(seg) - 1:]
    lo, hi = int(S / 400), int(S / 70)
    return S / (lo + np.argmax(ac[lo:hi]))


_cache = {}
def dicho(texto, voz='sabina', rapidez=0):
    k = (texto, voz, rapidez)
    if k not in _cache:
        x = tts(texto, voz, rapidez); _cache[k] = (x, f0(x))
    return _cache[k]


def envolvente(x, largo=None):
    k = min(len(x) // 4, int(.004 * S))
    e = np.ones(len(x)); e[:k] = np.linspace(0, 1, k); e[-4 * k:] *= np.linspace(1, 0, 4 * k)
    return x * e


def afinar(texto, midi, voz='sabina', largo=None, tartamudeo=0, rapidez=0):
    """Remuestrear para que suene en `midi` (se acorta al subir)."""
    x, f = dicho(texto, voz, rapidez)
    y = a_sr(x, M.hz(midi) / f * S, S)
    if largo: y = y[:int(largo * S)]
    y = envolvente(y)
    if tartamudeo: y = np.concatenate([y[:int(T / 32 * S)]] * tartamudeo + [y])
    return y


def hablar(texto, acorde, voz='sabina', rapidez=0, max_st=2.0):
    """Sprechgesang: la palabra se corre a la nota del acorde más cercana a su propio tono,
    nunca más de `max_st` semitonos (para que se siga entendiendo)."""
    x, f = dicho(texto, voz, rapidez)
    m0 = 69 + 12 * math.log2(f / 440)
    cand = [n + 12 * o for n in acorde for o in range(-4, 5)]
    m = min(cand, key=lambda n: abs(n - m0))
    if abs(m - m0) > max_st: m = m0
    return envolvente(a_sr(x, M.hz(m) / f * S, S))


def euclides(k, n, rot=0):
    """k golpes repartidos en n lo más parejo posible (Bjorklund por Bresenham)."""
    pat = [(i * k) // n != ((i + 1) * k) // n for i in range(n)]
    pat = pat[-1:] + pat[:-1]
    return [i for i in range(n) if pat[(i - rot) % n]]


# ───────────── gestos sobre la imagen ─────────────
def arena(Z, cols, generaciones, calidad=85):
    """La tormenta: cada columna pasa `g` veces por JPEG (magnitud en dB y fase, 8 bits).
    Los bloques de 8×8 mezclan 8 compases vecinos y 8 filas: la música se entierra."""
    Z = Z.copy()
    sub = Z[cols]
    mx = np.abs(sub).max() or 1
    db = 20 * np.log10(np.abs(sub) / mx + 1e-12)
    u_m = np.clip((db + 70) / 70, 0, 1) * 255
    u_p = (np.angle(sub) + np.pi) / (2 * np.pi) * 255
    def jpeg(u, g):
        # JPEG a la misma calidad es casi idempotente (medido: la generación 8 = la 1). Como en
        # Snow, cada generación corre la imagen unas filas: los bloques de 8×8 caen en otro lado
        # y la pérdida sí se acumula.
        out = u.copy()
        for gen in range(g):
            corr = 3 * (gen % 8) + 1
            out = np.roll(out, corr, axis=1)
            partes = []
            for h0 in range(0, out.shape[1], 32768):      # JPEG no pasa de 65535 de alto
                im = Image.fromarray(np.round(np.clip(out[:, h0:h0 + 32768], 0, 255).T).astype(np.uint8))
                b = io.BytesIO(); im.save(b, 'JPEG', quality=calidad); b.seek(0)
                partes.append(np.array(Image.open(b)).T.astype(float))
            out = np.roll(np.concatenate(partes, 1), -corr, axis=1)
        return out
    gens = sorted(set(generaciones))
    m_g = {g: jpeg(u_m, g) for g in gens}; p_g = {g: jpeg(u_p, g) for g in gens}
    for i, (c, g) in enumerate(zip(cols, generaciones)):
        m = np.where(m_g[g][i] > 0.5, mx * 10 ** ((m_g[g][i] / 255 * 70 - 70) / 20), 0.0)
        p = p_g[g][i] / 255 * 2 * np.pi - np.pi
        Z[c] = m * np.exp(1j * p) if g else Z[c]
    return Z


def entropia(Z, cols, eps, semilla=7):
    """La misma magnitud, la fase cada vez más al azar: eps=0 la nota, eps=1 ruido con su espectro."""
    Z = Z.copy(); r = np.random.default_rng(semilla)
    for c, e in zip(cols, eps):
        Z[c] = np.abs(Z[c]) * np.exp(1j * (np.angle(Z[c]) + e * r.uniform(-np.pi, np.pi, Z.shape[1])))
    return Z


def suavizar(a, filas):
    k = np.ones(filas) / filas
    return np.convolve(a, k, 'same')


_fase_fija = np.random.default_rng(SEM + 3).uniform(-np.pi, np.pi, H)
def negativo(Z, cols, lo=180, hi=6000, filas=40, igualar=0.5):
    """El silencio con forma de voz: dentro de la banda, magnitud = techo − voz (suavizada);
    fase fija por fila (sin costuras). `igualar`: la energía del negativo respecto a la de la voz
    que reemplaza (sin esto, «techo − voz» en toda la banda es un soplido 10 dB arriba de todo)."""
    Z = Z.copy(); k0, k1 = int(lo / F), int(hi / F)
    for c in cols:
        e0 = np.sum(np.abs(Z[c]) ** 2)
        a = suavizar(np.abs(Z[c]), filas)[k0:k1]
        techo = np.percentile(a, 99.5)
        neg = np.clip(techo - a, 0, None)
        Z[c] = 0; Z[c, k0:k1] = neg * np.exp(1j * _fase_fija[k0:k1])
        e1 = np.sum(np.abs(Z[c]) ** 2)
        if igualar and e1 > 0: Z[c] *= math.sqrt(igualar * e0 / e1)
    return Z


def peine(acorde, armonicos=10, ancho=1.5, inclina=0.8):
    """Peine de armónicos de un acorde sobre las filas (lorentzianas de `ancho` filas)."""
    k = np.arange(H); w = np.zeros(H)
    for n in acorde:
        for h in range(1, armonicos + 1):
            kc = h * M.hz(n) / F
            if kc >= H: break
            w += 1 / h ** inclina / (1 + ((k - kc) / ancho) ** 2)
    return w / w.max()


def ruido(lo=60, hi=9000, inclina=0.5, semilla=11):
    """Ruido de banda con fase fija por fila: sostenido y sin costuras entre columnas."""
    k = np.arange(H) * F
    mag = np.where((k > lo) & (k < hi), 1 / np.maximum(k, lo) ** inclina, 0.0)
    return mag / mag.max() * np.exp(1j * np.random.default_rng(semilla).uniform(-np.pi, np.pi, H))


# ───────────── síntesis ─────────────
def sintetizar(ZL, ZR, wav, sr=None, filas=None):
    """Imagen de 16 bits → spectrumsynth → 48 kHz. Devuelve la escala (amplitud real = wav·escala)."""
    filas = filas or ZL.shape[1]
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
                    f'[m][p]spectrumsynth=sample_rate={sr or S}:channels=2:scale=lin:slide=fullframe:win_func=rect:overlap=0,'
                    f'aresample={SR_OUT}:filter_size=64:phase_shift=12', '-c:a', 'pcm_f32le', str(wav)], check=True)
    mr.unlink(); pr.unlink()
    return esc


def leer(wav, esc=1.0):
    sr, x = wavfile.read(wav)
    return x.astype(float) * esc
