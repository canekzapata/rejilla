"""Medir los demos de un objeto (render/<et>-<objeto>-*.wav, eventos en el .json):
  rms crudo     — nivel antes de normalizar (dB): para igualar gestos entre sí
  peor segundo  — el segundo más callado entre el primer y el último evento (dB bajo el rms): hoyos
  centroide     — centro de masa espectral (Hz)
  por evento    — pico espectral más fuerte cada 40 ms: mediana y percentiles 10 / 90 en Hz sobre su cuerpo
    python herramientas/medir_objeto.py w1 waterphone
"""
import glob, json, sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
RAIZ = Path(__file__).resolve().parents[1]
et, obj = sys.argv[1], sys.argv[2]
for f in sorted(glob.glob(str(RAIZ / 'render' / f'{et}-{obj}-*.wav'))):
    sr, x = wavfile.read(f); x = x.astype(float) / 32768; J = json.load(open(f[:-4] + '.json', encoding='utf-8'))
    ev = J.get('eventos') or []; crudo = J['pico'] / .9; rms = np.sqrt(np.mean(x ** 2))
    a = int(min(e['t'] for e in ev) * sr) if ev else 0; b = int(max(e['t'] + e.get('dur', .3) for e in ev) * sr) if ev else len(x)
    seg = [np.sqrt(np.mean(x[i:i + sr] ** 2)) for i in range(a, max(a + 1, b - sr), sr // 4)]
    E = np.abs(np.fft.rfft(x)) ** 2; fr = np.fft.rfftfreq(len(x), 1 / sr)
    print(f"== {Path(f).stem[len(et) + 1:]}  rms crudo {20 * np.log10(rms * crudo):.1f} dB  peor segundo {20 * np.log10(min(seg) / rms + 1e-9):.1f} dB  centroide {np.sum(fr * E) / np.sum(E):.0f} Hz")
    for e in ev[:14]:
        d = e.get('dur', .4); p, q = int((e['t'] + min(.3, d * .2)) * sr), int((e['t'] + max(.25, d * .9)) * sr)
        # el pico espectral más fuerte (100 Hz - 6 kHz) cada 40 ms: en objetos inarmónicos o encimados YIN inventa fundamentales
        N = 4096; pk = []
        for i in range(p, max(p + 1, q - N), sr // 25):
            S = np.abs(np.fft.rfft(x[i:i + N] * np.hanning(N))); fq = np.fft.rfftfreq(N, 1 / sr); m = (fq > 100) & (fq < 6000)
            j = np.argmax(S * m); pk.append(fq[j] + (fq[1] * .5 * (S[j - 1] - S[j + 1]) / (S[j - 1] - 2 * S[j] + S[j + 1] + 1e-12) if 0 < j < len(S) - 1 else 0))
        nom = ' '.join(f'{k}={e[k]}' for k in ('tipo', 'vara', 'm', 'texto', 'agua') if k in e)
        print(f'  {nom:34s}', f'pico espectral {np.median(pk):7.1f} Hz  [{np.percentile(pk, 10):7.1f} – {np.percentile(pk, 90):7.1f}]' if pk else '—')
