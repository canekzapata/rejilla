"""Afinación de las voces renderizadas contra la partitura: mediana de error por palabra (YIN de la cantante).
    python medir_voces.py e4
"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[2] / 'meleeviewer' / 'output' / 'Arte' / '2026-10-09_yoshi_es_un_vector_16_jpop'))
import cantante as K
A = K.A
ET = sys.argv[1]; P = json.load(open(AQUI / 'render' / f'{ET}-partitura.json', encoding='utf-8'))
res = {}
for pista, quien in (('ardilla', 'A'), ('grave', 'G')):
    sr, x = wavfile.read(AQUI / 'render' / f'{ET}-{pista}.wav'); x = resample_poly(x.mean(axis=1), 1, 2); sr //= 2
    f0, _ = A.curva(x, sr); err = []
    for r in P['partitura']:
        if r['quien'] != quien: continue
        for e in r['eventos']:
            # el cuerpo de la nota; en las cortas (≤ .35 s) la primera mitad: en PSOLA las consonantes duran lo natural y
            # el final de una nota corta ya es la consonante sonora de la siguiente (medía ±3 semitonos que no eran)
            p0, p1 = (0, .5) if e['dur'] <= .35 else (.3, .9)
            a, b = int((e['t'] + e['dur'] * p0) * sr), int((e['t'] + e['dur'] * p1) * sr)
            v = f0[a:b]; v = v[~np.isnan(v)]
            if len(v) > sr * .03: err.append((e['texto'], e['nota'], round(float(1200 * np.log2(np.median(v) / (440 * 2 ** ((e['nota'] - 69) / 12)))))))
    e = np.array([abs(q[2]) for q in err])
    res[pista] = {'palabras': len(err), 'mediana_cents': float(np.median(e)), 'a_mas_de_50': int((e > 50).sum()),
                  'peores': sorted(err, key=lambda q: -abs(q[2]))[:5]}
    print(pista, res[pista])
json.dump(res, open(AQUI / 'render' / f'{ET}-voces.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
