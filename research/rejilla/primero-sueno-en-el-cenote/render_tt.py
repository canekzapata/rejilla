"""Primero sueño en el cenote — los instrumentos de tres tiempos (Codex; copia fijada): el órgano de divisores con memoria, la boca
(el alma) y la sala plegada (la cueva que se dobla).    python render_tt.py <carpeta>"""
import json, os, sys, numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); RUN = sys.argv[1]; P = json.load(open(os.path.join(RUN, 'partitura.json'), encoding='utf-8'))
sys.path.insert(0, os.path.join(AQUI, P['tres_tiempos_codigo'])); from motores import render
for k, part in P['tres_tiempos'].items():
    a, _, _ = render(k, part, P['duracion'], sr=48000, semilla=P['semilla'] + len(k)); a.astype(np.float32).tofile(os.path.join(RUN, k + '.f32')); print(k, 'pico', round(float(np.abs(a).max()), 3), flush=True)
