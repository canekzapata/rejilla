"""Sonda de la radio: sintonizada, la estación entra entera y sin chiflido; a 1 kHz de desintonía se oye el heterodino a ~1 kHz y la
voz corrida 250 Hz; entre estaciones manda la estática (el CAG la sube)."""
import sys, os, math, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); import sintes10 as S
SR = S.SR; N = 9 * SR; t = np.arange(N) / SR
tono = np.sin(2 * np.pi * 700 * t) * .5                                       # una estación que transmite un tono de 700 Hz
def pico(y, a, b):
    Y = np.abs(np.fft.rfft(y[int(a * SR):int(b * SR)] * np.hanning(int((b - a) * SR)))); f = np.fft.rfftfreq(int((b - a) * SR), 1 / SR); return f, Y
y, _ = S.radio([dict(f=10.0, audio=tono, nivel=1, fading=0)], [[0, 10.0], [3, 10.0], [3.01, 11.0], [6, 11.0], [6.01, 16.0], [9, 16.0]], N, semilla=1)
r = {}
f, Y = pico(y, .5, 2.5); r['sintonizada_pico_hz'] = round(float(f[np.argmax(Y)]), 1)
f, Y = pico(y, 3.5, 5.5); orden = np.argsort(Y)[::-1]; r['desintonia_1khz_picos_hz'] = sorted({round(float(f[i]), 0) for i in orden[:40] if Y[i] > Y.max() * .3})
rms = lambda a, b: float(np.sqrt(np.mean(y[int(a * SR):int(b * SR)] ** 2)))
r['nivel_estacion_vs_entre_estaciones_dB'] = round(20 * math.log10(rms(.5, 2.5) / rms(6.5, 8.5)), 1)
print(json.dumps(r, ensure_ascii=False)); json.dump(r, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'radio.json'), 'w', encoding='utf-8'), ensure_ascii=False)
