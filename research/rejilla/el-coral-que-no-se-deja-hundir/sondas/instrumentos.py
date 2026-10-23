"""Sondas de los instrumentos nuevos: el volcán se borra en 2π, el coral crece hacia arriba, la ola llega partida (el más alto primero)."""
import sys, os, math, json, time
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); import sintes8 as S
r = {}
N = 6 * S.SR
y0 = S.volcan([[0, 147], [6, 140]], [[0, -10], [6, -10]], [[0, 0], [6, 0]], [[0, 0], [6, 0]], N, rumor=0)
yb = S.volcan([[0, 147], [6, 140]], [[0, -10], [6, -10]], [[0, 0], [1, 0], [5, 2 * math.pi], [6, 2 * math.pi]], [[0, 0], [6, 0]], N, rumor=0)
# sin normalizar: comparo el mismo tramo antes y después del giro dentro de la misma toma
rms = lambda x: float(np.sqrt(np.mean(x ** 2)) + 1e-15)
r['volcan_borrado_dB'] = round(20 * math.log10(rms(yb[int(5.2 * S.SR):int(5.9 * S.SR)]) / rms(yb[int(.2 * S.SR):int(.9 * S.SR)])), 1)
t = time.time(); parts, base = S.crecer_coral(W=120, H=80, n=900, base=(6 + 10 * np.exp(-((np.arange(120) - 60) / 30.) ** 2)).astype(int), semilla=2)
ys = np.array([p[1] for p in parts]); top = np.maximum.accumulate(ys)
r['coral'] = {'particulas': len(parts), 'segundos': round(time.time() - t, 1), 'altura_final': int(ys.max()), 'copa_a_1/4_1/2_3/4': [int(top[len(top) * k // 4]) for k in (1, 2, 3)],
              'ramas_hijas_por_padre_max': int(np.bincount([p[2] for p in parts if p[2] >= 0]).max())}
_, q, llegadas = S.ola(0.0, 4, 8 * S.SR, dur=4.0, semilla=1)
r['ola_4_solitones'] = {'crestas': len(llegadas), 'llegadas_s': [round(x, 3) for x in llegadas]}
print(json.dumps(r, ensure_ascii=False, indent=1))
