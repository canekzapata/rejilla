"""Medir el piano (render/<et>-piano-*.wav): nota por nota (ventanas de 1.4 s desde cada ataque)
  f1_cents    — el parcial más grave contra la nota (cents)
  B           — rigidez: f_n = n·f1·√(1 + B n²) ajustado a los parciales 1-8 (un piano real: 1e-4 a 1e-3); en las notas
                preparadas pierde sentido y crece la desviación
  inarmonia   — desviación media de los parciales 2-8 respecto a n·f1 (cents)
  T60         — cuánto tarda la nota en caer 60 dB
  zumbido     — llanura espectral entre 2 y 8 kHz (0 = tonal, 1 = ruido)
    python herramientas/medir_piano.py p1
"""
import glob, json, sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
RAIZ = Path(__file__).resolve().parents[1]; et = sys.argv[1]; res = {}
hz = lambda m: 440 * 2 ** ((m - 69) / 12)
for f in sorted(glob.glob(str(RAIZ / 'render' / f'{et}-piano-*.wav'))):
    sr, x = wavfile.read(f); x = x.astype(float) / 32768; J = json.load(open(f[:-4] + '.json', encoding='utf-8'))
    if 'notas' not in J: continue
    nombre = Path(f).stem[len(et) + 7:]; filas = []
    for i, m in enumerate(J['notas']):
        a = int((i * J['cada'] + .03) * sr); seg = x[a:a + int(1.3 * sr)]
        N = 1 << 17; S = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), N)); fr = np.fft.rfftfreq(N, 1 / sr); f0 = hz(m)
        def pico(fc, ancho):
            k = (fr > fc * (1 - ancho)) & (fr < fc * (1 + ancho)); return float(fr[k][np.argmax(S[k])]) if k.any() else fc
        p1 = pico(f0, .04); ps = [p1]
        for n in range(2, 9):
            if n * p1 > sr * .45: break
            ps.append(pico(ps[-1] + p1, .5 / n))                 # busca el siguiente parcial cerca de donde caería
        n_ = np.arange(1, len(ps) + 1); r = (np.array(ps) / (n_ * p1)) ** 2 - 1
        B = float(np.sum(r[1:] * n_[1:] ** 2) / np.sum(n_[1:] ** 4)) if len(ps) > 2 else None
        inarm = float(np.mean([abs(1200 * np.log2(ps[k] / ((k + 1) * p1))) for k in range(1, len(ps))])) if len(ps) > 1 else None
        env = np.sqrt(np.convolve(seg ** 2, np.ones(480) / 480, 'same')); pk = env.argmax(); e = 20 * np.log10(env[pk:] / (env[pk] + 1e-12) + 1e-12)
        c60 = np.nonzero(e < -60)[0]; c20 = np.nonzero(e < -20)[0]
        t60 = round(c60[0] / sr, 2) if len(c60) else (round(3 * c20[0] / sr, 2) if len(c20) else '>1.3')
        alto = (fr > 2000) & (fr < 8000); Sa = S[alto] ** 2 + 1e-20; plano = float(np.exp(np.mean(np.log(Sa))) / np.mean(Sa))
        filas.append({'nota': m, 'f1_cents': round(1200 * np.log2(p1 / f0)), 'B': None if B is None else float(f'{B:.2e}'), 'inarmonia_cents': None if inarm is None else round(inarm),
                      'T60_s': t60, 'zumbido': round(plano, 3)})
    res[nombre] = filas
    print(nombre.ljust(16), ' '.join(f"{q['nota']}:{q['f1_cents']:+d}c/B{q['B']}/i{q['inarmonia_cents']}/T{q['T60_s']}/z{q['zumbido']}" for q in filas))
json.dump(res, open(RAIZ / 'render' / f'medidas-piano-{et}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
