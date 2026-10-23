"""¿Se tejió? Brusquedad en las rayas de compás y ritmo del ruido, loop C contra loop D."""
import json
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
import cancion as K
import cancion_tejida as D

res = {}
for nom, ruta in (('C', K.R / f'sobre-la-aurora-{K.TAG}.wav'), ('D', D.R2 / f'sobre-la-aurora-{D.TAG}.wav')):
    sr, x = wavfile.read(ruta); m = x.astype(float).mean(1) / 32768
    a, b = K.COLS['entropía'][0], K.COLS['confundo'][-1] + 1
    seg = m[int(a * K.T * sr):int(b * K.T * sr)]
    # 1. brusquedad: cambio espectral (flujo, 50 ms) en las rayas vs. dentro del compás
    hop = int(.05 * sr); fr = np.array([np.abs(np.fft.rfft(seg[i:i + 2 * hop] * np.hanning(2 * hop))) for i in range(0, len(seg) - 2 * hop, hop)])
    lf = np.log10(fr + 1e-6); flujo = np.sqrt((np.diff(lf, axis=0) ** 2).mean(1))
    t = (np.arange(len(flujo)) + 1) * hop / sr / K.T
    raya = np.abs(t - np.round(t)) < .03
    res[f'{nom}_flujo_en_rayas_vs_dentro'] = round(float(flujo[raya].mean() / flujo[~raya].mean()), 3)
    # 2. ruido encasillado: profundidad de modulación de la banda 2-8 kHz a 6.93 Hz (dieciseisavos)
    hb = sosfilt(butter(4, [2000, 8000], 'bandpass', fs=sr, output='sos'), seg)
    env = np.sqrt(np.convolve(hb ** 2, np.ones(int(.01 * sr)) / int(.01 * sr), 'same'))[::int(.005 * sr)]
    E = np.abs(np.fft.rfft(env - env.mean())); f = np.fft.rfftfreq(len(env), .005)
    f16 = 16 / K.T
    pico = E[(f > f16 - .3) & (f < f16 + .3)].max(); fondo = np.median(E[(f > 3) & (f < 12)])
    res[f'{nom}_ruido_late_a_16avos_dB'] = round(float(20 * np.log10(pico / fondo)), 1)
print(json.dumps(res, indent=1))
json.dump(res, open(D.R2 / 'medidas-tejido.json', 'w'), indent=1)
