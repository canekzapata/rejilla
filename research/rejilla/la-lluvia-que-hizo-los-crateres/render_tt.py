"""La lluvia que hizo los cráteres — la señal de la sonda: el cristal orbital de los instrumentos de tres tiempos (Codex; copia fijada).
    python render_tt.py <carpeta>"""
import json, os, sys, numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); RUN = sys.argv[1]; P = json.load(open(os.path.join(RUN, 'partitura.json'), encoding='utf-8'))
sys.path.insert(0, os.path.join(AQUI, P['tres_tiempos_codigo'])); from motores import render
a, _, _ = render('cristal', {'notas': P['sonda']}, P['duracion'], sr=48000, semilla=P['semilla']); a.astype(np.float32).tofile(os.path.join(RUN, 'sonda.f32'))
print('sonda', len(P['sonda']), 'notas · pico', round(float(np.abs(a).max()), 3))
