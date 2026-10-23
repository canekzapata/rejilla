"""Balance de «sobre la aurora» por sección: bandas del total y nivel de cada pista (ya con ganancia)."""
import json, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
import cancion as K

sr, x = wavfile.read(K.R / f'sobre-la-aurora-{K.TAG}.wav'); m = x.astype(float).mean(1) / 32768
T = K.T
bands = [('sub', 20, 80), ('low', 80, 250), ('mid', 250, 2000), ('pres', 2000, 6000), ('air', 6000, 20000)]
fb = {n: sosfilt(butter(4, [lo, hi], 'bandpass', fs=sr, output='sos') if hi < sr / 2 else butter(4, lo, 'highpass', fs=sr, output='sos'), m) for n, lo, hi in bands}
st = {n: wavfile.read(K.R / f'tl-{n}.wav')[1].mean(1) * K.GANANCIA[n] for n in K.NOMBRES}
print('sección      rms  ' + ' '.join(f'{n:>5s}' for n, _, _ in bands) + '   | pistas (dB, con ganancia)')
for sec, cols in K.COLS.items():
    i, j = int(cols[0] * T * sr), int((cols[-1] + 1) * T * sr)
    r = 20 * np.log10(m[i:j].std() + 1e-12)
    pistas = {n: 20 * np.log10(st[n][i:j].std() + 1e-12) for n in K.NOMBRES}
    top = sorted(pistas.items(), key=lambda kv: -kv[1])[:5]
    print(f'{sec:11s} {r:6.1f} ' + ' '.join(f'{20 * np.log10(fb[n][i:j].std() + 1e-12) - r:5.1f}' for n, _, _ in bands)
          + '   | ' + '  '.join(f'{n} {v:.0f}' for n, v in top) + f'  | voz {pistas["voz"]:.0f}')
