"""El androide en la estación — las capas de los instrumentos de tres tiempos (Codex, 19-20 oct; copia fijada en tres-tiempos-<hash>/):
boca, arpa, cuerda, sala, órgano, cristal, cuerdas de estación, terminal vectorial, plasma, bajo de androide, fotones. Cada una se
rinde a 48 kHz con su partitura y se guarda estéreo en <carpeta>/<capa>.f32 (L,R entrelazados). Los solos van en capa aparte.
    python render_tt.py <carpeta> [capa…]
"""
import json, os, sys, time
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); RUN = sys.argv[1]; solo = sys.argv[2:]
P = json.load(open(os.path.join(RUN, 'partitura.json'), encoding='utf-8')); sys.path.insert(0, os.path.join(AQUI, P['tres_tiempos_codigo']))
from motores import render
for k, part in P['tres_tiempos'].items():
    for nombre, filtro in ((k, lambda n: not n.get('solo')), (k + '-solo', lambda n: n.get('solo'))):
        notas = [n for n in part['notas'] if filtro(n)]
        if not notas or (solo and nombre not in solo): continue
        t = time.time(); p = dict(part, notas=notas)
        a, _, _ = render(k, p, P['duracion'], sr=48000, semilla=P['semilla'] + len(nombre))
        a.astype(np.float32).tofile(os.path.join(RUN, nombre + '.f32'))
        print(f'{nombre:15}{len(notas):5} notas {time.time() - t:6.1f} s · pico {np.abs(a).max():.3f} · rms {20 * np.log10(np.sqrt((a ** 2).mean()) + 1e-12):.1f} dB', flush=True)
