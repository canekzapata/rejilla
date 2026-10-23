"""¿Tiemblan las vocales sostenidas? En cada sílaba larga (≥ 0.4 s), el centroide espectral cada 10 ms en su tramo
central; se mide cuánto se mueve (desviación, en %) y cuánta de esa modulación cae entre 3 y 14 Hz (lo que se oye
como vibrato o aleteo). Una vocal sostenida limpia casi no se mueve.
    python medir_temblor.py e3
"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
AQUI = Path(__file__).resolve().parent
ET = sys.argv[1]; P = json.load(open(AQUI / 'render' / f'{ET}-partitura.json', encoding='utf-8'))
res = {}
for pista, q in (('ardilla', 'A'), ('grave', 'G')):
    sr, x = wavfile.read(AQUI / 'render' / f'{ET}-{pista}.wav'); x = x.mean(axis=1)
    N, hop = 1024, int(sr * .01); fr = np.fft.rfftfreq(N, 1 / sr); m = (fr > 150) & (fr < 6000)
    desv, mod = [], []
    for r in P['partitura']:
        if r['quien'] != q: continue
        for e in r['eventos']:
            if e['dur'] < .4: continue
            a, b = int((e['t'] + e['dur'] * .3) * sr), int((e['t'] + e['dur'] * .85) * sr)
            c = []
            for i in range(a, b - N, hop):
                s = np.abs(np.fft.rfft(x[i:i + N] * np.hanning(N)))[m] ** 2
                if s.sum() > 1e-9: c.append((s * fr[m]).sum() / s.sum())
            c = np.array(c)
            if len(c) < 16: continue
            desv.append(c.std() / c.mean() * 100)
            esp = np.abs(np.fft.rfft((c - c.mean()) * np.hanning(len(c)))) ** 2; f = np.fft.rfftfreq(len(c), .01)
            mod.append(esp[(f >= 3) & (f <= 14)].sum() / (esp[f > .5].sum() + 1e-12) * 100)
    res[pista] = {'silabas_largas': len(desv), 'centroide_se_mueve_%': round(float(np.median(desv)), 1),
                  'de_eso_entre_3_y_14_Hz_%': round(float(np.median(mod)), 1)}
    print(pista, res[pista])
json.dump(res, open(AQUI / 'render' / f'{ET}-temblor.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
