"""Medir los objetos renderizados (render/<et>-*.wav):
  altura      — f0 mediana (YIN de la cantante) en el cuerpo de la nota, contra la pedida (cents)
  periódico   — autocorrelación normalizada en el periodo medido (1 = tono puro de ciclos iguales; ruido ≈ 0)
  pares/impares — energía de los armónicos pares contra impares (dB): un cilindro cerrado (clarinete) casi no tiene
                pares; el saxofón (cónico) y la flauta (abierta) sí
  inarmonía   — cuánto se apartan los parciales 2-6 de los múltiplos enteros (cents, media): ≈ 0 en vientos
  T60         — en lo golpeado, cuánto tarda en caer 60 dB
    python herramientas/medir.py a1
"""
import glob, json, sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ.parents[2] / 'meleeviewer' / 'output' / 'Arte' / '2026-10-09_yoshi_es_un_vector_16_jpop'))
import cantante as K
A = K.A
et = sys.argv[1]; res = {}
for f in sorted(glob.glob(str(RAIZ / 'render' / f'{et}-*.wav'))):
    sr, x = wavfile.read(f); x = x.astype(float) / 32768; J = json.load(open(f[:-4] + '.json', encoding='utf-8'))
    nombre = Path(f).stem[len(et) + 1:]; r = {'pico_crudo': round(J['pico'], 3)}
    fp = 440 * 2 ** ((J['nota'] - 69) / 12) if 'nota' in J else None
    a, b = int(.3 * sr), int(min(len(x), 1.3 * sr)); seg = x[a:b]
    f0, _ = A.curva(seg, sr); v = f0[~np.isnan(f0)]
    if len(v) > sr * .05:
        fm = float(np.median(v)); r['f0'] = round(fm, 1)
        if fp: r['altura_cents'] = round(1200 * np.log2(fm / fp))
        L = int(round(sr / fm)); s = seg[:len(seg) - L]; r['periodico'] = round(float(np.dot(s, seg[L:L + len(s)]) / (np.linalg.norm(s) * np.linalg.norm(seg[L:L + len(s)]) + 1e-12)), 2)
    ref = r.get('f0', fp)
    N = 1 << int(np.ceil(np.log2(len(seg)))); E = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), N)) ** 2; fr = np.fft.rfftfreq(N, 1 / sr)
    def pico(fc, ancho=.03):
        m = (fr > fc * (1 - ancho)) & (fr < fc * (1 + ancho)); return (float(fr[m][np.argmax(E[m])]), float(E[m].max())) if m.any() else (fc, 0)
    if ref:
        ps = [pico(ref * k, .06 if J.get('obj') == 'golpe' else .03) for k in range(1, 9)]
        par = sum(p[1] for k, p in enumerate(ps, 1) if k % 2 == 0); imp = sum(p[1] for k, p in enumerate(ps, 1) if k % 2 == 1 and k > 1)
        r['pares_sobre_impares_dB'] = round(10 * np.log10((par + 1e-15) / (imp + 1e-15)), 1)
        r['inarmonia_cents'] = round(float(np.mean([abs(1200 * np.log2(ps[k - 1][0] / (ps[0][0] * k))) for k in range(2, 7)])), 1)
    env = np.sqrt(np.convolve(x ** 2, np.ones(480) / 480, 'same')); pk = env.argmax(); e = 20 * np.log10(env[pk:] / env[pk] + 1e-12)
    caida = np.nonzero(e < -60)[0]; r['T60_s'] = round(caida[0] / sr, 2) if len(caida) else None
    res[nombre] = r; print(f'{nombre:12s}', r)
json.dump(res, open(RAIZ / 'render' / f'medidas-{et}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
