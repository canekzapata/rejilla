"""La ciudad se hunde bailando — instrumentos propios (48 kHz).

  radio(estaciones, dial, N)   LA RADIO DE ONDA CORTA (a lo *Hymnen* de Stockhausen): una banda con estaciones de AM, cada una con su
                               frecuencia (kHz), su contenido (música, voz, una señal horaria, o nada) y su desvanecimiento. Una perilla
                               (dial: [[t, kHz]]) la recorre, y lo que suena sale del receptor:
                                 · SELECTIVIDAD: cada estación entra por el filtro de FI según su desintonía δ = dial − f (gaussiana, ±2.5 kHz)
                                 · DESINTONÍA: el audio se corre de tono 250 Hz por kHz (la voz «de pato» de la banda lateral)
                                 · HETERODINO: cerca de una estación se oye el chiflido de su portadora a |δ|·1000 Hz, que baja a
                                   cero cuando se sintoniza
                                 · DESVANECIMIENTO: Rayleigh lento (la ionosfera): cada estación sube y baja sola
                                 · ESTÁTICA: siseo y chasquidos de Poisson; el CAG (control automático de ganancia) la sube cuando no
                                   hay señal: entre estaciones, el ruido «respira»
                               y la bocina: banda de 200 a 3800 Hz y un poco de saturación.
  sirena(ev, N)                la sirena del sonidero (la de dub): un seno con vibrato que sube y baja, con eco corto.
  teclado(notas, N)            el teclado cumbianchero: cuadrada + sierra con vibrato y portamento, chorus (la cumbia sonidera).
  bajo(notas, N)               el bajo de cumbia: triángulo con un poco de saturación.
"""
import math
import numpy as np
from scipy.signal import butter, sosfilt, hilbert
SR = 48000
hz = lambda m: 440.0 * 2 ** ((np.asarray(m, float) - 69) / 12)


def _pan(y, p): a = (p + 1) * math.pi / 4; return np.stack([y * math.cos(a), y * math.sin(a)], 1)
def _bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x)
def _lp(x, fc, o=2): return sosfilt(butter(o, fc, 'low', fs=SR, output='sos'), x)


def _correr(x, df):
    """corre el espectro de x por df(t) Hz (señal analítica)."""
    a = hilbert(x); fase = 2 * np.pi * np.cumsum(df) / SR
    return np.real(a * np.exp(1j * fase))


def radio(estaciones, dial, N, semilla=0, bw=2.5):
    """estaciones: [{f (kHz), audio (np.array mono, N) | None, nivel, tipo}]; dial: [[t, kHz]]."""
    rng = np.random.default_rng(semilla); t = np.arange(N) / SR
    d = np.interp(t, [a for a, _ in dial], [b for _, b in dial])
    total = np.zeros(N); senal = np.zeros(N); info = []
    for k, e in enumerate(estaciones):
        delta = d - e['f']; g = np.exp(-(delta / bw) ** 2)
        if g.max() < 1e-3: continue
        # desvanecimiento de Rayleigh: módulo de un gaussiano complejo filtrado a ~0.3 Hz
        z = rng.standard_normal((N // 480 + 2, 2)); z = sosfilt(butter(1, .3, 'low', fs=100, output='sos'), z, axis=0)
        fad = np.hypot(z[:, 0], z[:, 1]); fad = fad / (np.sqrt(np.mean(fad ** 2)) + 1e-12); fad = np.interp(t, np.arange(len(fad)) / 100, fad)
        fad = .35 + .65 * np.clip(fad, 0, 2) * e.get('fading', 1) + (1 - e.get('fading', 1)) * .65
        x = e['audio'] if e.get('audio') is not None else np.zeros(N)
        x = _bp(x, 150, 4000)
        x = _correr(x, 250 * delta)                                            # la desintonía: la voz «de pato»
        silbido = np.sin(2 * np.pi * np.cumsum(np.clip(np.abs(delta) * 1000, 0, 5000)) / SR) * (np.abs(delta) > .12) * .25
        s = (x * e.get('nivel', 1) + silbido) * g * fad
        total += s; senal += g * fad * e.get('nivel', 1); info.append(dict(f=e['f'], tipo=e.get('tipo')))
    # la estática y el CAG: el ruido sube donde no hay señal
    sise = _bp(rng.standard_normal(N), 300, 3800) * .08
    chasq = np.zeros(N); idx = np.nonzero(rng.random(N) < 6 / SR)[0]
    for i in idx:
        L = int(rng.integers(30, 300))
        if i + L < N: chasq[i:i + L] += rng.standard_normal(L) * np.exp(-np.arange(L) / (L / 4)) * rng.uniform(.2, 1)
    sen = _lp(np.abs(senal), 2) ; cag = 1 / (.25 + np.clip(sen, 0, 2))
    y = (total + (sise + _bp(chasq, 400, 5000) * .6) * cag * .4) * np.clip(cag, .4, 3) * .5
    y = np.tanh(1.4 * _bp(y, 200, 3800))
    return y / (np.abs(y).max() + 1e-12), dict(estaciones=info, dial_khz=[float(d.min()), float(d.max())])


def sirena(eventos, N, semilla=0):
    """eventos: {t, dur, f0, f1, pan}: sube de f0 a f1 y baja, con vibrato acelerado (la sirena de dub)."""
    y = np.zeros((N, 2))
    for e in eventos:
        a = int(e['t'] * SR); d = e.get('dur', 2.5); L = int(d * SR)
        if a + L >= N: continue
        tt = np.arange(L) / SR; u = tt / d
        f = e['f0'] + (e['f1'] - e['f0']) * np.sin(np.pi * u) ** .7
        f *= 1 + .03 * np.sin(2 * np.pi * (4 + 10 * u) * tt)
        s = (np.sin(2 * np.pi * np.cumsum(f) / SR) + .3 * np.sign(np.sin(2 * np.pi * np.cumsum(f * .5) / SR))) * np.minimum(1, tt / .05) * np.minimum(1, (d - tt) / .3)
        y[a:a + L] += _pan(s, e.get('pan', 0))
        for k, g in ((1, .45), (2, .2)):                                       # eco corto de sonidero (3/8)
            b = a + int(k * .47 * SR); m = min(L, N - b)
            if m > 0: y[b:b + m] += _pan(s[:m] * g, -e.get('pan', 0))
    return y / (np.abs(y).max() + 1e-12)


def teclado(notas, N, semilla=0):
    """notas: {t, dur, m, v}; portamento de 25 ms entre notas ligadas; vibrato que entra tarde."""
    rng = np.random.default_rng(semilla); notas = sorted(notas, key=lambda n: n['t']); y = np.zeros((N, 2))
    for i, n in enumerate(notas):
        a = int(n['t'] * SR); L = int((n['dur'] + .08) * SR)
        if a + L >= N: continue
        tt = np.arange(L) / SR; f1 = float(hz(n['m']))
        f0 = float(hz(notas[i - 1]['m'])) if i and n['t'] - (notas[i - 1]['t'] + notas[i - 1]['dur']) < .04 else f1
        f = f1 + (f0 - f1) * np.exp(-tt / .025); f *= 1 + .007 * np.sin(2 * np.pi * 5.6 * tt) * np.clip((tt - .18) / .2, 0, 1)
        s = 0
        for det, pan in ((-.004, -.5), (.004, .5)):
            ph = np.cumsum(f * (1 + det)) / SR
            s = s + _pan(.6 * np.sign(np.sin(2 * np.pi * ph)) + .4 * (2 * (ph % 1) - 1), pan)
        env = np.minimum(1, tt / .006) * np.clip((n['dur'] + .08 - tt) / .08, 0, 1)
        y[a:a + L] += s * env[:, None] * n.get('v', .7)
    y = np.stack([_lp(y[:, 0], 3200), _lp(y[:, 1], 3200)], 1)
    return y / (np.abs(y).max() + 1e-12)


def bajo(notas, N):
    y = np.zeros(N)
    for n in notas:
        a = int(n['t'] * SR); L = int((n['dur'] + .05) * SR)
        if a + L >= N: continue
        tt = np.arange(L) / SR; ph = np.cumsum(np.full(L, float(hz(n['m'])))) / SR
        tri = 2 * np.abs(2 * (ph % 1) - 1) - 1
        y[a:a + L] += np.tanh(1.6 * tri) * np.minimum(1, tt / .004) * np.clip((n['dur'] + .05 - tt) / .05, 0, 1) * np.exp(-tt / 1.5) * n.get('v', .8)
    return y / (np.abs(y).max() + 1e-12)
