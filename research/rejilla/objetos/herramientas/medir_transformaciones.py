"""¿Qué pasa durante una transformación? Para cada render (render/<et>-*.wav + .json con sus notas), cada 50 ms:
altura (YIN) contra la nota que tocaba, centroide espectral y periodicidad. Resumen por tercios del archivo:
  afinadas   — % de cuadros con altura a menos de 50 cents de su nota (entre los que tienen altura)
  brincos    — cuadros a más de 6 semitonos de su nota (el tubo saltó de registro)
  con_altura — % de cuadros donde YIN encuentra altura (un golpe inarmónico casi no tiene)
  centroide  — Hz (el brillo)
    python herramientas/medir_transformaciones.py a3
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
    notas = J.get('notas'); nombre = Path(f).stem[len(et) + 1:]
    f0, _ = A.curva(x, sr); hop = int(.05 * sr); N = 2048; fr = np.fft.rfftfreq(N, 1 / sr)
    filas = []
    for i in range(0, len(x) - N, hop):
        seg = x[i:i + N]; e = np.sqrt(np.mean(seg ** 2))
        if e < 1e-3: continue
        S = np.abs(np.fft.rfft(seg * np.hanning(N))) ** 2; cen = float((S * fr).sum() / S.sum())
        v = f0[i:i + N]; v = v[~np.isnan(v)]; t = (i + N / 2) / sr
        m = None
        if notas:
            for tn, mn in notas:
                if t >= tn: m = mn
        cents = float(1200 * np.log2(np.median(v) / (440 * 2 ** ((m - 69) / 12)))) if len(v) > N / 4 and m else None
        filas.append((t, cents, cen))
    dur = len(x) / sr; r = {}
    for k, (a, b) in enumerate(((0, dur / 3), (dur / 3, 2 * dur / 3), (2 * dur / 3, dur))):
        q = [fl for fl in filas if a <= fl[0] < b]
        if not q: continue
        c = [fl[1] for fl in q if fl[1] is not None]
        r[['inicio', 'medio', 'final'][k]] = {'con_altura_%': round(100 * len(c) / len(q)), 'afinadas_%': round(100 * np.mean([abs(v) < 50 for v in c])) if c else None,
                                              'brincos': int(sum(abs(v) > 600 for v in c)), 'centroide_Hz': round(float(np.median([fl[2] for fl in q])))}
    res[nombre] = r; print(f'{nombre:20s}', r)
json.dump(res, open(RAIZ / 'render' / f'transformaciones-{et}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
