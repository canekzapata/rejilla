"""Rejilla 03 · Esquinas.

Monk (Epistrophy, Evidence, Misterioso, Brilliant Corners) pasado por PC Music, J-pop,
música contemporánea y el Weather Report de los ochenta (Zawinul, fretless, MIDI).

El nudo: en la rejilla, leer la misma imagen al doble de sample_rate es el doble de
tempo Y una octava arriba. La duplicación de tempo de Brilliant Corners y el chipmunk
de PC Music son la misma operación. La sección «Doble» es la imagen de «Esquina»
leída a 2×S, dos vueltas, con un piso nuevo debajo a tempo normal.

Otras contradicciones escritas en la imagen:
- el piano swinguea, la batería es MIDI cuadrada;
- «sí» y «no» cantados a la vez a medio tono: un cluster hecho de una contradicción;
- los acordes de la Pregunta llevan la envolvente de las vocales de «sí» y «no»;
- en el Misterioso la voz dice «otra vez» al revés: conjugar la fase de una columna
  invierte el compás en el tiempo.

    python esquinas.py
"""
import json, math, subprocess, hashlib
from fractions import Fraction
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly
import musica as M

AQUI = Path(__file__).parent
RENDER = AQUI / 'render' / 'esquinas'
TTS = AQUI / 'render' / 'tts'
TAG = 's1110'
SEM = 1110
BPM = 92
M.fijar_tempo(BPM)
S, N, H, T = M.S, M.N, M.H, M.T
SR_OUT = 48000
rng = np.random.default_rng(SEM)
M.rng = rng                                   # los instrumentos de musica.py también siembran de aquí
M._bordes = np.round(np.geomspace(30, 14000, M.VISTA + 1) / M.F).astype(int)   # la vista, con el nuevo Hz por fila


class Pista(M.Pista):
    """Pista de la rejilla que además acepta muestras: el pedazo de una grabación que cae en
    una columna entra con su DFT exacta."""
    def __init__(self, nombre, columnas):
        super().__init__(nombre, columnas)
        self.muestras = []
        self.reves = set()           # columnas cuya fase se conjuga (el compás al revés)

    def muestra(self, w, t0, g=1.0, pan=0.0):
        gL, gR = M.paneo(pan)
        self.muestras.append((np.asarray(w, float) * g, int(round(t0 * S)), gL, gR))

    def escribir(self):
        ZL, ZR = super().escribir()
        for w, n0, gL, gR in self.muestras:
            n1 = n0 + len(w)
            for b in range(max(0, n0 // N), min(self.C, -(-n1 // N))):
                a, z = max(n0, b * N), min(n1, (b + 1) * N)
                buf = np.zeros(N); buf[a - b * N:z - b * N] = w[a - n0:z - n0]
                c = np.fft.rfft(buf)[:H] / N
                c[0] = 0
                ZL[b] += gL * c; ZR[b] += gR * c
        for b in self.reves:
            ZL[b] = np.conj(ZL[b]); ZR[b] = np.conj(ZR[b])
        return ZL, ZR


# ───────────── voces: sílabas de Sabina y Zira ─────────────
VOCES = {'sabina': 'Microsoft Sabina Desktop', 'zira': 'Microsoft Zira Desktop'}


def tts(texto, voz='sabina', rapidez=1):
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
    env = np.convolve(np.abs(x), np.ones(256) / 256, 'same')        # recortar silencios
    vivo = np.where(env > 0.04)[0]
    x = x[max(0, vivo[0] - 80):vivo[-1] + 400]
    return a_sr(x, sr, S)


def a_sr(x, de, a):
    fr = Fraction(a / de).limit_denominator(400)
    return resample_poly(x, fr.numerator, fr.denominator)


def f0(x):
    """Tono de la parte sonora (autocorrelación sobre el 40 % central)."""
    n = len(x); seg = x[int(n * .3):int(n * .7)]
    if len(seg) < 2048: seg = x
    seg = seg - seg.mean()
    ac = np.correlate(seg, seg, 'full')[len(seg) - 1:]
    lo, hi = int(S / 400), int(S / 80)
    return S / (lo + np.argmax(ac[lo:hi]))


SILABAS = {}
def silaba(txt, voz='sabina'):
    if (txt, voz) not in SILABAS:
        x = tts(txt, voz)
        SILABAS[(txt, voz)] = (x, f0(x))
    return SILABAS[(txt, voz)]


def chop(txt, midi, voz='sabina', largo=None, tartamudeo=0):
    """La sílaba afinada por remuestreo (se acorta al subir: el gesto chipmunk),
    con ataque/caída cortos y, si se pide, tartamudeo de 32avos."""
    x, f = silaba(txt, voz)
    r = M.hz(midi) / f
    y = a_sr(x, r * S, S)                     # leerla r veces más rápido
    if largo: y = y[:int(largo * S)]
    k = min(len(y) // 4, int(.004 * S))
    env = np.ones(len(y)); env[:k] = np.linspace(0, 1, k); env[-4 * k:] *= np.linspace(1, 0, 4 * k)
    y = y * env
    if tartamudeo:
        g = y[:int(T / 32 * S)]
        y = np.concatenate([g] * tartamudeo + [y])
    return y


def envolvente_vocal(txt, voz='sabina'):
    """La envolvente espectral de una vocal (magnitud suavizada), para que un acorde la diga."""
    x, tono = silaba(txt, voz)
    # el tramo más sonoro (la vocal, no la consonante): máxima energía en 200-1000 Hz
    from scipy.signal import butter, sosfilt
    v = sosfilt(butter(4, [200, 1000], 'bandpass', fs=S, output='sos'), x)
    L = int(0.08 * S); e = np.convolve(v * v, np.ones(L), 'valid')
    i0 = int(np.argmax(e)); seg = x[i0:i0 + L] * np.hanning(L)
    X = np.abs(np.fft.rfft(seg, 1 << 15)); fr = np.fft.rfftfreq(1 << 15, 1 / S)
    ancho = int(1.6 * tono / (fr[1] - fr[0]))       # más ancho que la separación de armónicos: queda la envolvente
    X = np.convolve(X, np.ones(ancho) / ancho, 'same')
    X /= X.max()
    return lambda f: float(np.interp(f, fr, X))


# ───────────── instrumentos ─────────────
def piano(P, midi, t0, vel, dur, pan=0.0):
    """Piano modal: armónicos con un poco de inarmonicidad, los agudos se apagan antes."""
    f = M.hz(midi); B = 0.0003
    for n in range(1, 9):
        fn = n * f * math.sqrt(1 + B * n * n)
        amp = 0.13 * vel * (1 / n ** (1.25 - 0.5 * vel))
        P.modo(fn, amp, t0, 0.9 + 0.55 * n + f / 900, ataque=900, suelta=dur, ar=9, pan=pan, fase=rng.uniform(0, 6.28))


def coro_vocal(P, midi, t0, dur, vel, env, pan=0.0):
    """Un acorde que dice una vocal: armónicos ricos pesados por la envolvente de la sílaba."""
    f = M.hz(midi)
    for n in range(1, 26):
        fn = n * f
        if fn > 6000: break
        amp = 0.055 * vel * env(fn) / n ** 0.4
        if amp < 1e-4: continue
        P.modo(fn * (1 + rng.normal(0, 0.0007)), amp, t0, 2.0, ataque=60, suelta=dur, ar=10, pan=pan,
               fase=rng.uniform(0, 6.28))


def sub808(P, midi, t0, dur, vel):
    f = M.hz(midi)
    P.modo(f, 0.55 * vel, t0, 0.9, ataque=500, suelta=dur, ar=14)
    P.modo(2 * f, 0.10 * vel, t0, 3.0, ataque=500, suelta=dur, ar=14)


def fretless(P, midi, t0, dur, vel):
    """El bajo que canta: casi sin ataque, un 'mwah' que es el segundo armónico abriéndose."""
    f = M.hz(midi)
    for n, amp, a, at in ((1, 1.0, 1.1, 90), (2, 0.55, 1.6, 22), (3, 0.22, 2.6, 30), (4, 0.08, 4, 40)):
        P.modo(n * f, 0.30 * vel * amp, t0, a, ataque=at, suelta=dur, ar=12, fase=rng.uniform(0, 6.28))


def zawinul(P, midi, t0, dur, vel, pan=0.0):
    """Lead de metal tipo Prophet: armónicos hasta arriba, ataque en swell, dos osciladores
    que baten."""
    f = M.hz(midi)
    for det, p in ((-0.9, pan - 0.3), (0.9, pan + 0.3)):
        for n in range(1, 13):
            P.modo(n * (f + det), 0.030 * vel / n ** 0.85, t0, 0.5 + 0.12 * n, ataque=14 + 2 * n, suelta=dur, ar=8,
                   pan=max(-1, min(1, p)), fase=rng.uniform(0, 6.28))


def pad_azucar(P, midi, t0, dur, vel):
    """Supersaw de J-pop: cinco sierras desafinadas (armónicos 1/n)."""
    f = M.hz(midi)
    for j, det in enumerate((-0.012, -0.006, 0.0, 0.006, 0.012)):
        for n in range(1, 9):
            P.modo(n * f * (1 + det), 0.011 * vel / n, t0, 0.15, ataque=6, suelta=dur, ar=4,
                   pan=-0.8 + 0.4 * j, fase=rng.uniform(0, 6.28))


def campana(P, midi, t0, vel, pan=0.0):
    f = M.hz(midi)
    for mult, amp, a in ((1, 1.0, 3.5), (2.76, 0.4, 7), (5.40, 0.18, 12), (8.93, 0.07, 18)):
        P.modo(f * mult, 0.06 * vel * amp, t0, a, ataque=1500, pan=pan, fase=rng.uniform(0, 6.28))


MODOS_CLAP = np.exp(rng.uniform(math.log(800), math.log(6000), 70))
MODOS_HAT = np.exp(rng.uniform(math.log(7000), math.log(18000), 40))
MODOS_TIN = np.array([2310, 3420, 5170, 6630.])


def bombo(P, t0, vel):                     # LinnDrum + PC Music: cuerpo corto y clic
    P.modo(56, 1.0 * vel, t0, 11, ataque=700)
    P.modo(92, 0.35 * vel, t0, 26, ataque=900)
    for f in (1900, 2700, 3900, 5200): P.modo(f, 0.02 * vel, t0, 220, fase=rng.uniform(0, 6.28))


def clap(P, t0, vel, pan=0.1):
    for k, d in enumerate((0, 0.009, 0.019)):            # tres manos casi juntas
        for f in MODOS_CLAP[k::3]:
            P.modo(f, 0.05 * vel * (0.6 if k < 2 else 1), t0 + d, 34 if k == 2 else 160, ataque=5000, pan=pan,
                   fase=rng.uniform(0, 6.28))


def hat(P, t0, vel, pan=-0.3):
    for f in MODOS_HAT: P.modo(f, 0.018 * vel, t0, 90 * rng.uniform(.8, 1.2), ataque=6000, pan=pan, fase=rng.uniform(0, 6.28))


def tin(P, t0, vel, pan=0.5):              # el cencerrito metálico
    for f in MODOS_TIN: P.modo(f, 0.05 * vel, t0, 30, ataque=4000, pan=pan, fase=rng.uniform(0, 6.28))


def lenio(P, midi, t0, vel, pan=-0.5):     # tambor de leño (log drum), Weather Report
    f = M.hz(midi)
    for mult, amp, a in ((1, 1, 14), (2.42, 0.4, 22), (3.9, 0.15, 30)):
        P.modo(f * mult, 0.12 * vel * amp, t0, a, ataque=2500, pan=pan, fase=rng.uniform(0, 6.28))


# ───────────── la pieza ─────────────
def dom7(r):
    """Voicing de Monk para un dominante: raíz, séptima, tercera arriba, #9 que raspa."""
    return [r, r + 10, r + 16, r + 27]


SWING = 0.62
def tp(b, pos, swing=True, humano=0.006):
    """El piano swinguea..."""
    p = pos + (2 * (SWING - 0.5) if swing and int(pos) % 2 == 1 and pos == int(pos) else 0)
    return b * T + p * T / 16 + rng.normal(0, humano)


def tq(b, pos):
    """...la batería es MIDI: cuadrada, sin mano."""
    return b * T + pos * T / 16


# Pregunta: dominantes que oscilan a medio tono, golpes desplazados, silencios
PREGUNTA = [  # por compás: [(pos, raíz, dur16, voz)] ; voz: 'si', 'no', 'sino' (cluster) o None
    [(3, 37, 2, 'si'), (6, 38, 3, None), (11, 37, 1, None), (14, 38, 2, 'no')],
    [(2, 37, 2, None), (7, 38, 1, 'sino'), (10, 38, 4, None)],
    [(3, 37, 2, 'si'), (6, 38, 3, None), (11, 37, 1, None), (14, 38, 2, 'no')],
    [(0, 39, 2, 'sino'), (4, 40, 2, None)],                                       # y silencio
    [(3, 39, 2, 'si'), (6, 40, 3, None), (11, 39, 1, None), (14, 40, 2, 'no')],
    [(2, 39, 2, None), (7, 40, 1, 'sino'), (10, 40, 4, None)],
    [(1, 41, 1, None), (3, 40, 1, None), (5, 39, 1, None), (7, 38, 1, 'sino'), (9, 37, 6, None)],
    [(0, 36, 3, 'sino')],                                                         # y silencio
]

# Esquina: dominantes cromáticos que bajan, dos por compás
ESQ_ACORDES = [(39, 40), (38, 37), (36, 35), (34, 33)] * 2
ESQ_MELODIA = [  # (pos, sílaba, midi, dur16, voz) — una octava abajo; en «Doble» suben solas
    [(0, 'es', 67, 2), (2, 'qui', 61, 1), (3, 'na', 60, 3), (8, 'bri', 64, 1), (9, 'llan', 59, 1), (10, 'te', 65, 4)],
    [(2, 'o', 66, 2), (4, 'tra', 60, 2), (6, 'vez', 59, 2), (6, 'vez', 60, 2), (12, 'no', 56, 1), (13, 'no', 56, 1), (14, 'no', 55, 2)],
    [(1, 'es', 65, 2), (3, 'qui', 59, 1), (4, 'na', 58, 3), (9, 'bri', 62, 1), (10, 'llan', 57, 1), (11, 'te', 63, 4)],
    [(i, 'sí', n, 1) for i, n in enumerate([72, 70, 68, 66, 64, 62, 60, 58])] + [(12, 'wrong', 61, 3), (12, 'wrong', 62, 3)],
    [(0, 'es', 67, 2), (2, 'qui', 61, 1), (3, 'na', 60, 3), (8, 'bri', 64, 1), (9, 'llan', 59, 1), (10, 'te', 65, 4)],
    [(2, 'o', 66, 2), (4, 'tra', 60, 2), (6, 'vez', 59, 2), (6, 'vez', 60, 2), (11, 'again', 63, 3)],
    [(0, 'yes', 70, 1), (1, 'no', 71, 1), (3, 'yes', 64, 1), (4, 'no', 65, 1), (6, 'yes', 58, 1), (7, 'no', 59, 1), (10, 'corner', 61, 5)],
    [(0, 'mal', 60, 2), (0, 'mal', 61, 2)],                                                   # cluster y corte
]
INGLES = {'wrong', 'again', 'yes', 'corner'}

# Misterioso: sextas que caminan, fretless que canta, la voz al revés
MIST_SEXTAS = [(48, 57), (50, 59), (52, 61), (53, 62), (55, 64), (56, 65), (57, 66), (58, 67)]
MIST_FRETLESS = [  # (pos, midi, dur16)
    [(0, 43, 6), (6, 46, 2), (8, 47, 8)],
    [(0, 48, 4), (4, 52, 4), (8, 55, 3), (11, 54, 5)],
    [(0, 53, 6), (6, 51, 2), (8, 49, 4), (12, 46, 4)],
    [(0, 44, 2), (2, 45, 14)],
]

# columnas de la imagen base (la Doble no ocupa columnas: es la Esquina leída a 2×)
COL = {'pregunta': range(0, 8), 'esquina': range(8, 16), 'misterioso': range(16, 20),
       'esquina2': range(20, 28), 'coda': range(28, 30)}
C = 31
NOMBRES = ['bombo', 'bateria', 'sub', 'piano', 'voz', 'pad', 'metal']


def componer():
    P = {n: Pista(n, C) for n in NOMBRES}
    env_si, env_no = envolvente_vocal('sí'), envolvente_vocal('no')

    # Pregunta
    for k, b in enumerate(COL['pregunta']):
        for pos, r, du, v in PREGUNTA[k]:
            t = tp(b, pos)
            for i, n in enumerate(dom7(r)): piano(P['piano'], n, t + 0.008 * i, 0.85, du * T / 16, pan=-0.3 + 0.2 * i)
            if v:
                env = env_si if v != 'no' else env_no
                for n in dom7(r)[1:]: coro_vocal(P['pad'], n + 12, t, du * T / 16, 0.8, env, pan=0.3)
                top = dom7(r)[-1] + 12 - 24
                if v in ('si', 'sino'): P['voz'].muestra(chop('sí', top + 12), t, 0.5, pan=-0.35)
                if v in ('no', 'sino'): P['voz'].muestra(chop('no', top + 13), t, 0.5, pan=0.35)
            sub808(P['sub'], r - 12 if r - 12 >= 28 else r, t, du * T / 16, 0.7)
        if k >= 4:  # la batería entra a la mitad: cuadrada contra el piano que swinguea
            for pos in (0, 10): bombo(P['bombo'], tq(b, pos), 0.9)
            clap(P['bateria'], tq(b, 8), 0.8)
            if k in (5, 6):
                for i in range(8): hat(P['bateria'], tq(b, 12 + i / 2), 0.25 + 0.08 * i)

    # Esquina (dos veces: la segunda con el metal de Zawinul doblando el tema)
    for seccion in ('esquina', 'esquina2'):
        for k, b in enumerate(COL[seccion]):
            a1, a2 = ESQ_ACORDES[k]
            ultimo = (k == 7)
            for j, r in enumerate((a1, a2)):
                if ultimo and j == 1: break
                t = tp(b, 8 * j + (0 if j == 0 else 1))      # el segundo acorde llega tarde
                du = 3 if ultimo else 6
                for i, n in enumerate(dom7(r)): piano(P['piano'], n, t + 0.006 * i, 0.75, du * T / 16, pan=-0.3 + 0.2 * i)
                sub808(P['sub'], r - 12 if r - 12 >= 28 else r, tq(b, 8 * j), (3 if ultimo else 7.5) * T / 16, 0.9)
                if not ultimo:   # el azúcar: tríada mayor un tritono arriba del dominante
                    for n in (r + 18, r + 22, r + 25): pad_azucar(P['pad'], n + 12, tq(b, 8 * j), 7.5 * T / 16, 0.9)
            if ultimo:   # cluster de antebrazo y corte seco
                for n in range(55, 68): piano(P['piano'], n, tp(b, 0) + rng.uniform(0, .015), 1.0, T * 0.25, pan=(n - 61) / 8)
            for pos, s, n, du in ESQ_MELODIA[k]:
                voz = 'zira' if s in INGLES else 'sabina'
                P['voz'].muestra(chop(s, n, voz, largo=du * T / 16 * 1.05, tartamudeo=2 if (s == 'no' and pos == 12) else 0),
                                 tq(b, pos), 0.75, pan=0.0)
                if seccion == 'esquina2': zawinul(P['metal'], n + 12, tq(b, pos), du * T / 16, 0.9, pan=0.25)
            if k == 3:   # tonos enteros que bajan, en campanas
                for i, n in enumerate([84, 82, 80, 78, 76, 74, 72, 70]): campana(P['metal'], n, tq(b, i), 0.8, pan=0.7 - 0.2 * i)
            # batería MIDI
            if not ultimo:
                for pos in (0, 6, 10): bombo(P['bombo'], tq(b, pos), 1.0 if pos == 0 else 0.85)
                for pos in (4, 12): clap(P['bateria'], tq(b, pos), 1.0)
                for pos in range(16): hat(P['bateria'], tq(b, pos), 0.5 if pos % 2 == 0 else 0.25)
                if k % 4 == 3:
                    for i in range(8): hat(P['bateria'], tq(b, 12 + i / 2), 0.3 + 0.07 * i)
                # Weather Report: leño en 3 contra 4 y cencerrito
                for i in range(12): lenio(P['bateria'], [45, 52, 50][i % 3] + (12 if i % 4 == 0 else 0), tq(b, i * 16 / 12), 0.6)
                for pos in (3, 11, 14): tin(P['bateria'], tq(b, pos), 0.5)
            else:
                bombo(P['bombo'], tq(b, 0), 1.0); clap(P['bateria'], tq(b, 0), 1.0)

    # Misterioso: sextas que caminan con nota aplastada, fretless, voz al revés
    for k, b in enumerate(COL['misterioso']):
        for q in range(4):
            lo, hi = MIST_SEXTAS[(2 * k + q) % 8]
            t = tp(b, 4 * q)
            piano(P['piano'], hi - 1, t - 0.035, 0.45, 0.05)                    # la nota equivocada, aplastada
            piano(P['piano'], lo, t, 0.6, T / 4 * 0.9, pan=-0.2); piano(P['piano'], hi, t, 0.6, T / 4 * 0.9, pan=0.2)
        for pos, n, du in MIST_FRETLESS[k]: fretless(P['sub'], n - 12, tp(b, pos), du * T / 16, 0.9)
        frase = [('o', 64, 0), ('tra', 63, 3), ('vez', 59, 6), ('again', 61, 10)]
        for s, n, pos in frase:
            P['voz'].muestra(chop(s, n, 'zira' if s in INGLES else 'sabina'), tq(b, pos), 0.6, pan=-0.2 + 0.1 * pos / 4)
        P['voz'].reves.add(b)
        for pos in (0, 6, 9, 12): tin(P['bateria'], tq(b, pos), 0.25, pan=-0.6)

    # coda: silencio, y una pregunta chiquita
    b = COL['coda'][0]
    P['voz'].muestra(chop('no', 79, 'zira'), tq(b, 6), 1.4)
    P['voz'].muestra(chop('sí', 80), tq(b, 9), 0.9, pan=0.5)
    return P


def doble(P):
    """El piso nuevo bajo la Doble, a tempo normal: 8 compases (= 2 vueltas de la Esquina a 2×)."""
    D = {n: Pista(n, 9) for n in ('bombo', 'bateria', 'sub')}
    for b in range(8):
        for pos in (0, 4, 8, 12): bombo(D['bombo'], tq(b, pos), 1.0)
        for pos in (4, 12): clap(D['bateria'], tq(b, pos), 0.7)
        sub808(D['sub'], 36 + (0 if b % 4 < 2 else 1), tq(b, 0), T * 0.98, 0.8)     # pedal que se niega a seguir
    return D


def sintetizar(m16, p16, wav, sr):
    W = m16.shape[1]
    mr, pr = wav.with_suffix('.mag.raw'), wav.with_suffix('.fase.raw')
    m16.tofile(mr); p16.tofile(pr)
    ent = lambda r: ['-f', 'rawvideo', '-pix_fmt', 'gray16le', '-s', f'{W}x{2 * H}', '-r', '1', '-i', str(r)]
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', *ent(mr), *ent(pr), '-filter_complex',
                    '[0]setpts=N/TB,format=gray16le[m];[1]setpts=N/TB,format=gray16le[p];'
                    f'[m][p]spectrumsynth=sample_rate={sr}:channels=2:scale=lin:slide=fullframe:win_func=rect:overlap=0,'
                    f'aresample={SR_OUT}:filter_size=64:phase_shift=12',
                    '-c:a', 'pcm_f32le', str(wav)], check=True)
    mr.unlink(); pr.unlink()


def leer(wav, esc):
    sr, x = wavfile.read(wav)
    return x.astype(float) * esc


def main():
    RENDER.mkdir(parents=True, exist_ok=True)
    P = componer(); D = doble(P)
    print(f'S={S} T={T:.4f}s', {n: (len(p.segs), len(p.muestras)) for n, p in P.items()})
    largo = lambda cols: int(round(cols * T * SR_OUT))
    vistas, escalas = {}, {}
    q0, q1 = COL['esquina'][0], COL['esquina'][-1] + 1
    for n, p in P.items():
        ZL, ZR = p.escribir()
        vistas[n] = M.vista(ZL + ZR)
        m16, p16, esc = M.a_imagen(ZL, ZR); escalas[n] = esc
        sintetizar(m16, p16, RENDER / f'{n}.wav', S)
        # la Doble: las mismas columnas de la Esquina, leídas a 2×S
        sintetizar(np.ascontiguousarray(m16[:, q0:q1]), np.ascontiguousarray(p16[:, q0:q1]), RENDER / f'{n}-doble.wav', 2 * S)
        del ZL, ZR, m16, p16
        print('  pista', n, 'lista')
    for n, p in D.items():
        ZL, ZR = p.escribir()
        m16, p16, esc = M.a_imagen(ZL, ZR); escalas[n + '-piso'] = esc
        sintetizar(m16, p16, RENDER / f'{n}-piso.wav', S)
        vistas[n + '-piso'] = M.vista(ZL + ZR)

    # línea de tiempo: Pregunta+Esquina | Doble ×2 (+ piso) | Misterioso+Esquina2+coda
    corte = largo(q1)
    for n in NOMBRES:
        base = leer(RENDER / f'{n}.wav', escalas[n])
        dob = leer(RENDER / f'{n}-doble.wav', escalas[n])[:largo(4)]
        dob = np.concatenate([dob, dob])
        if n + '-piso' in escalas:
            piso = leer(RENDER / f'{n}-piso.wav', escalas[n + '-piso'])[:largo(8)]
            L = min(len(dob), len(piso)); dob = dob[:L] + piso[:L]
        y = np.concatenate([base[:corte], dob, base[corte:]])
        wavfile.write(RENDER / f'tl-{n}.wav', SR_OUT, y.astype(np.float32))
    np.savez_compressed(RENDER / 'vistas.npz', **vistas)
    json.dump({'escalas': escalas, 'T': T, 'S': S, 'col': {k: [v[0], v[-1] + 1] for k, v in COL.items()}},
              open(RENDER / 'partitura.json', 'w'))
    mezclar()


GANANCIA = {'bombo': 0.55, 'bateria': 2.2, 'sub': 0.38, 'piano': 0.9, 'voz': 1.0, 'pad': 1.7, 'metal': 1.8}


def mezclar():
    g = GANANCIA
    ent = sum([['-i', str(RENDER / f'tl-{n}.wav')] for n in NOMBRES], [])
    i = {n: k for k, n in enumerate(NOMBRES)}
    grafo = ';'.join([
        f"[{i['bombo']}]volume={g['bombo']},asplit=3[k][kc1][kc2]",
        f"[{i['bateria']}]volume={g['bateria']}[dr]",
        f"[{i['sub']}]volume={g['sub']}[sb0]",
        f"[{i['piano']}]volume={g['piano']}[pi]",
        f"[{i['voz']}]volume={g['voz']},highpass=f=140,equalizer=f=3000:t=o:w=1.2:g=4[vo]",
        f"[{i['pad']}]volume={g['pad']}[pa0]",
        f"[{i['metal']}]volume={g['metal']}[me]",
        "[pa0][kc1]sidechaincompress=threshold=0.05:ratio=4:attack=4:release=160:makeup=1[pa]",
        "[sb0][kc2]sidechaincompress=threshold=0.06:ratio=3:attack=3:release=120:makeup=1[sb]",
        "[k][dr]amix=inputs=2:normalize=0,asoftclip=type=tanh:threshold=0.8[drums]",      # brillo de PC Music
        "[pi][vo][pa][me]amix=inputs=4:normalize=0,asplit[seco][w0]",
        "aevalsrc=d=2.4:s=48000:exprs='(random(0)*2-1)*exp(-t*2.6)|(random(1)*2-1)*exp(-t*2.6)',lowpass=f=7000,highpass=f=300[ir]",
        "[w0][ir]afir=dry=0:wet=1[rev]",
        "[seco][rev]amix=inputs=2:weights=1 0.10:normalize=0[musica]",
        "[drums][sb][musica]amix=inputs=3:normalize=0,highpass=f=26,equalizer=f=4000:t=o:w=1.5:g=3,"
        "acompressor=threshold=0.2:ratio=2.5:attack=10:release=180:makeup=1,"
        "loudnorm=I=-12:TP=-1.0:LRA=9,aresample=48000[out]",
    ])
    final = RENDER / f'esquinas-{TAG}.wav'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', *ent, '-filter_complex', grafo,
                    '-map', '[out]', '-c:a', 'pcm_s16le', str(final)], check=True)
    m4a = AQUI / f'esquinas-{TAG}.m4a'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(final), '-c:a', 'aac', '-b:a', '224k', str(m4a)], check=True)
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(final), '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    tail = r[r.rfind('Summary:'):]
    val = lambda key: float(tail.split(key)[1].split()[0])
    med = {'I_LUFS': val('I:'), 'LRA': val('LRA:'), 'pico_dBTP': val('Peak:'),
           'duracion_s': round(wavfile.read(final)[1].shape[0] / SR_OUT, 2),
           'sha256_m4a': hashlib.sha256(m4a.read_bytes()).hexdigest()}
    print(med)
    json.dump(med, open(AQUI / f'medidas-esquinas-{TAG}.json', 'w'), indent=1)


if __name__ == '__main__':
    import sys
    if '--mezcla' in sys.argv: mezclar()
    else: main()
