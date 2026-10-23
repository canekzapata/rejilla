"""Sondas: la cascada no llega (lo último de la caída es casi nada), su duración sale de la pared; los capachos y el tuki suenan."""
import sys, os, math, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); import sintes9 as S
r = {}
for H in (500, 800, 1000):
    tr, tt = S.caida(H); y, info = S.cascada(0, H, 220, int((tt + 1) * S.SR), semilla=1)
    r[f'cascada_{H}m'] = dict(t_rompe=round(tr, 2), t_total=round(tt, 2), ultimo_10pc_vs_columna_dB=round(20 * math.log10(info['energia_ultimo_10pc'] + 1e-12), 1))
y = S.capachos([dict(t=.1 + .14 * i, dur=.1, v=.7) for i in range(10)], 2 * S.SR); r['capachos_pico'] = round(float(np.abs(y).max()), 3)
y = S.tuki([dict(t=.1, notas=[57, 60, 64], dur=.15, v=.8)], S.SR); r['tuki_pico'] = round(float(np.abs(y).max()), 3)
print(json.dumps(r, ensure_ascii=False))
