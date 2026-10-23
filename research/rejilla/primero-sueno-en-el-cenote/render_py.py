"""Primero sueño en el cenote — capas de Python: los metrónomos de cuerda, la linterna mágica (lenta: unos 4 min) y el vinilo.
    python render_py.py <carpeta> [capa…]"""
import json, os, sys, time, numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI); import sintes7 as S7
RUN = sys.argv[1]; solo = sys.argv[2:]; P = json.load(open(os.path.join(RUN, 'partitura.json'), encoding='utf-8')); N = int(P['duracion'] * 48000)
def guardar(n, y): y.astype(np.float32).tofile(os.path.join(RUN, n + '.f32')); print(n, y.shape, 'pico', round(float(np.abs(y).max()), 3), flush=True)
if not solo or 'metronomos' in solo:
    y, golpes = S7.metronomos(P['metronomos'], N, 1); guardar('metronomos', y); json.dump(golpes, open(os.path.join(RUN, 'metronomos-golpes.json'), 'w'))
if not solo or 'linterna' in solo:
    t = time.time(); y, img = S7.linterna(P['trazos'], N, 2); guardar('linterna', y); np.save(os.path.join(RUN, 'linterna-imagen.npy'), img.astype(np.float32)); print('  linterna', round(time.time() - t), 's')
if not solo or 'vinilo' in solo: guardar('vinilo', S7.vinilo(P['vinilo'], N, 3))
