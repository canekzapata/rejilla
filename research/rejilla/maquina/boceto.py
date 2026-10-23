"""Boceto del loop A de «la máquina del tiempo»: funk de una sola nota.

La rejilla leída a sr = 55·1024 = 56320 Hz hace que una columna dure 131072/56320 = 2.327 s
(un compás a 103.1 bpm) y que la fila k suene a k·55/128 Hz. Entonces:
  fila 1  = una vez por compás (el Uno)        fila 4  = negras
  fila 16 = dieciseisavos                      fila 128 = La1, 55 Hz
El ritmo y la altura viven en el mismo eje, siete octavas aparte.

Un groove es una envolvente periódica por compás; su serie de Fourier son bandas laterales a
±m filas de cada parcial. La MAGNITUD de esas bandas es la armonía; la FASE decide dónde caen
los golpes. Con fases al azar el mismo espectro deja de tener tiempo (ambient); con otras
fases, el mismo espectro es otro groove.
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI.parent / 'pixeles'))
import motor as M                                   # sintetizar(): imagen 16 bits → spectrumsynth

SR = 55 * 1024                                      # 56320: la fila 128 es La1
FILAS = 65536
T = 2 * FILAS / SR                                  # 2.327 s = un compás
BPM = 60 * 4 / T
MMAX = 60                                           # bandas laterales por lado (< 64: no chocan parciales vecinos)
SEM = 1031
R = AQUI.parent / 'render' / 'maquina'; R.mkdir(parents=True, exist_ok=True)

# el acorde: un solo La y sus parciales; pesa los que hacen el A7#9 de funk (8:10:12:14:19)
# y deja 11 y 13 crudos (sin temperar, como salen de la serie)
PESOS = {1: 1.0, 2: .8, 3: .45, 4: .5, 5: .3, 6: .32, 7: .42, 8: .22, 10: .2, 11: .2, 12: .18, 13: .16,
         14: .2, 16: .08, 19: .14, 21: .07, 22: .08, 26: .06, 28: .06, 33: .04, 38: .05, 44: .03, 52: .03}
BANDA = lambda n: 'bajo' if n <= 3 else ('medio' if n <= 14 else 'alto')

# los golpes por dieciseisavo (0..15) de cada banda: el Uno fuerte, el bajo anticipa, palmada en 2 y 4
GROOVE_A = {'bajo': {0: 1, 3: .55, 6: .45, 10: .75, 13: .4, 14: .6},
            'medio': {4: 1, 12: 1, 11: .25, 15: .2},
            'alto': {i: .3 + .35 * (i % 2 == 0) + .2 * (i % 4 == 2) for i in range(16)}}
# el que vuelve (tercera síntesis): el bajo corrido y abierto, la palmada se adelanta un 16avo
GROOVE_B = {'bajo': {0: 1, 2: .35, 5: .6, 8: .5, 9: .7, 12: .35, 15: .55},
            'medio': {3: .9, 11: 1, 7: .3},
            'alto': {i: .25 + .45 * (i % 3 == 0) for i in range(16)}}
TAU = {'bajo': .16, 'medio': .08, 'alto': .035}


def envolvente(golpes, tau, n=8192):
    """Un compás de envolvente (golpes que decaen, periódica) → coeficientes c_0..c_MMAX."""
    t = np.arange(n) / n * T
    e = np.zeros(n)
    for paso, g in golpes.items():
        d = (t - paso * T / 16) % T
        e += g * np.exp(-d / tau) * (1 - np.exp(-d / .004))
    E = np.fft.rfft(e) / n
    return E[:MMAX + 1]


def coefs(groove):
    return {b: envolvente(groove[b], TAU[b]) for b in groove}


CA, CB = coefs(GROOVE_A), coefs(GROOVE_B)
rng = np.random.default_rng(SEM)
FASE_P = {n: rng.uniform(0, 2 * np.pi) for n in PESOS}
DESORDEN = {(n, o): rng.uniform(-np.pi, np.pi, MMAX + 1) for n in PESOS for o in range(2)}

# la forma del boceto, compás por compás: (cuánto groove, coherencia, mezcla A→B)
#   1-3 la nota sola · 4-6 el groove sale de la nota · 7-10 funk de una nota
#   11-14 se pierde el tiempo (mismo espectro, fases al azar) · 15-18 vuelve otro groove
N = 18
s = lambda u: np.clip(u, 0, 1) ** 2 * (3 - 2 * np.clip(u, 0, 1))
groove = np.array([s((b - 2.5) / 3.5) for b in range(N)])
coher = np.array([1 - s((b - 10) / 3.2) + s((b - 13.6) / 2.6) if b >= 10 else 1.0 for b in range(N)]).clip(0, 1)
mezcla = np.array([s((b - 11.5) / 2.5) for b in range(N)])


def columna(b, oido):
    z = np.zeros(FILAS, complex)
    for n, a in PESOS.items():
        k0 = 128 * n
        c = (1 - mezcla[b]) * CA[BANDA(n)] + mezcla[b] * CB[BANDA(n)]
        c = c / (np.abs(CA[BANDA(n)][0]) + 1e-12)                  # c_0 = 1: la nota sin groove pesa lo mismo
        lat = c.copy(); lat[1:] *= groove[b]                       # el groove sale de la nota
        des = np.exp(1j * (1 - coher[b]) * DESORDEN[(n, oido if n > 14 else 0)])
        lat = lat * des
        fase = np.exp(1j * FASE_P[n])
        z[k0] += a * lat[0] * fase
        for m in range(1, MMAX + 1):                               # e·cos(ωt) = Re Σ c_m e^{i(ω+m)t}
            z[k0 + m] += a * lat[m] * fase
            z[k0 - m] += a * np.conj(lat[m]) * fase * np.exp(1j * 0)  # c_{-m} = conj(c_m)
    return z


if __name__ == '__main__':
    ZL = np.array([columna(b, 0) for b in range(N)]); ZR = np.array([columna(b, 1) for b in range(N)])
    wav = R / 'boceto.wav'
    esc = M.sintetizar(ZL, ZR, wav, sr=SR)
    x = M.leer(wav, esc)
    x = x / np.abs(x).max() * .9
    wavfile.write(R / 'boceto-norm.wav', 48000, x.astype(np.float32))
    json.dump({'sr_rejilla': SR, 'compas_s': T, 'bpm': BPM, 'compases': N, 'groove': groove.tolist(),
               'coherencia': coher.tolist(), 'mezcla_A_B': mezcla.tolist(), 'semilla': SEM},
              open(R / 'boceto.json', 'w'), indent=1)
    print(f'compás {T:.4f} s · {BPM:.2f} bpm · {len(x) / 48000:.1f} s')
