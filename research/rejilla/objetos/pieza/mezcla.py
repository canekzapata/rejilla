"""Mezcla de «el tiempo es la altura»: stems render/<et>-pieza-*.wav → render/<et>-mezcla-v<k>.wav (estéreo, nunca sobrescribe).

  Cada stem se lleva a un nivel medido en su tramo activo (rms de los cuadros a menos de 40 dB de su máximo), se coloca
  en el estéreo (paneo de igual potencia; el agua y el waterphone se abren con un Haas de 11 ms) y manda a una
  reverberación común (ruido que decae, T60 2.8 s, cola oscura, L y R independientes).
  Mide: secciones de 10 s, peor segundo (hoyos) y la voz de agua contra todo lo demás.
    python pieza/mezcla.py p1
"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve
R = Path(__file__).resolve().parents[1] / 'render'; ET = sys.argv[1]; SR = 48000
#          stem          nivel dB  paneo (-1 a 1)  envío a la reverb  haas
MEZCLA = {'vozagua':    (-13.5, 0, .22, False),
          'contrabajo': (-20, 0, .15, False),
          'trombon':    (-21, -.35, .2, False),
          'tambor':     (-21.5, .35, .18, False),
          'sax':        (-22, -.6, .22, False),
          'piano':      (-22, .6, .25, False),
          'pajaro':     (-25, .2, .35, False),
          'waterphone': (-22, 0, .5, True),
          'gong':       (-22, 0, .45, True),
          'agua':       (-23, 0, .3, True)}


def lee(n):
    sr, x = wavfile.read(R / f'{ET}-pieza-{n}.wav'); J = json.load(open(R / f'{ET}-pieza-{n}.json', encoding='utf-8'))
    return x.astype(float) / 32768 * J['pico'] / .9


def rms_activo(x):
    c = np.sqrt(np.mean(x[:len(x) // 4800 * 4800].reshape(-1, 4800) ** 2, axis=1)); v = c[c > c.max() * 10 ** (-40 / 20)]
    return np.sqrt(np.mean(v ** 2))


L = None; stems = {}
for n, (db, pan, env, haas) in MEZCLA.items():
    x = lee(n); x *= 10 ** (db / 20) / (rms_activo(x) + 1e-12); stems[n] = x
    if L is None: L, Rr, send = (np.zeros(len(x)) for _ in range(3))
    a = (pan + 1) * np.pi / 4; gl, gr = np.cos(a), np.sin(a)
    if haas: d = int(.011 * SR); L += x * .75; Rr[d:] += x[:-d] * .75
    else: L += x * gl * 1.41; Rr += x * gr * 1.41                     # (al centro: 0.71 · 1.41 = 1 en cada lado)
    send += x * env
# la reverb: ruido que decae (T60 2.8 s), con la cola más oscura (pasabajos que se cierra), predelay 18 ms
rng = np.random.default_rng(31); N = int(3.2 * SR); t = np.arange(N) / SR
def ir():
    z = rng.standard_normal(N) * np.exp(-6.9 * t / 2.8); Z = np.fft.rfft(z); f = np.fft.rfftfreq(N, 1 / SR)
    # oscurecer: cada frecuencia decae más rápido arriba de 3 kHz (aprox. con un filtro fijo + la envolvente)
    z = np.fft.irfft(Z / (1 + (f / 3500) ** 2), N); z = np.concatenate([np.zeros(int(.018 * SR)), z]); return z / np.sqrt(np.sum(z ** 2))
wl, wr = fftconvolve(send, ir())[:len(L)] * .5, fftconvolve(send, ir())[:len(L)] * .5
mez = np.stack([L + wl, Rr + wr], axis=1)
# limitador: los golpes (pizz-house, lengua del trombón, tam-tam) dejaban una cresta de 23 dB y la pieza quedaba a −24 dB rms.
# La ganancia baja al instante donde la envolvente pasa el umbral (6 dB arriba del rms de 1 s de alrededor... aquí: un umbral fijo
# a 13 dB sobre el rms total) y se recupera en 150 ms; la envolvente mira 5 ms adelante
tot0 = np.sqrt(np.mean(mez ** 2)); umbral = tot0 * 10 ** (13 / 20); env = np.abs(mez).max(axis=1)
from scipy.ndimage import maximum_filter1d
env = maximum_filter1d(env, int(.005 * SR) * 2 + 1, origin=0); g = np.minimum(1, umbral / (env + 1e-12)); gs = np.empty_like(g); a = 1
rel = np.exp(-1 / (.15 * SR))
for i in range(len(g)):
    a = g[i] if g[i] < a else rel * a + (1 - rel) * g[i]; gs[i] = a
mez *= gs[:, None]; print('limitador: reducción máxima', round(20 * np.log10(gs.min()), 1), 'dB; tiempo limitando (>1 dB)', round(np.mean(gs < .89) * 100, 1), '%')
pk = np.abs(mez).max(); mez *= .89 / pk                                  # pico a −1 dB
k = 1
while (R / f'{ET}-mezcla-v{k}.wav').exists(): k += 1
sal = R / f'{ET}-mezcla-v{k}.wav'; wavfile.write(sal, SR, (mez * 32767).astype(np.int16)); print('->', sal.name)
# medidas
m = mez.mean(axis=1); seg = np.sqrt(np.mean(m[:len(m) // SR * SR].reshape(-1, SR) ** 2, axis=1)); tot = np.sqrt(np.mean(m ** 2))
fin = int(188)
print('rms total', round(20 * np.log10(tot), 1), 'dB · peor segundo (2-188 s)', round(20 * np.log10(seg[2:fin].min() / tot), 1), 'dB en', int(np.argmin(seg[2:fin]) + 2), 's')
print('secciones (dB rel. total):', ' '.join(f'{k * 10}:{20 * np.log10(np.sqrt(np.mean(m[k * 10 * SR:(k + 1) * 10 * SR] ** 2)) / tot):+.0f}' for k in range(20)))
g = pk / .89; voz = stems['vozagua'] / g; resto = sum(v for n, v in stems.items() if n != 'vozagua') / g
for a, b, nom in ((48, 118, 'aprende'), (118, 143, 'converge'), (168, 190, 'coda')):
    sv, sr_ = voz[a * SR:b * SR], resto[a * SR:b * SR]
    print(f'voz de agua contra el resto, {nom} ({a}-{b} s): {20 * np.log10(np.sqrt(np.mean(sv ** 2)) / np.sqrt(np.mean(sr_ ** 2))):+.1f} dB')
json.dump({'stems': {n: list(v) for n, v in MEZCLA.items()}, 'pico_crudo': float(pk)}, open(str(sal)[:-4] + '.json', 'x', encoding='utf-8'), ensure_ascii=False, indent=1)
