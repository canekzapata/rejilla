"""Prueba exacta de suenan_juntos, después del render: lo que pintó ffmpeg contra los mismos modos sumados en el tiempo,
en una ventana donde cada instrumento suena (máximo y rms relativos).    python biblioteca/prueba_exacta.py <h>"""
import json, math, sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
sys.path.insert(0, str(Path(__file__).parent)); import suenan_juntos as SJ
h = sys.argv[1]; render = SJ.AQUI.parent / 'render' / f'biblioteca-{h}'; out = SJ.AQUI / f'suenan-juntos-{h}'
receta = json.loads((out / 'receta.json').read_text(encoding='utf-8')); ev = SJ.partitura(); dur = 9 * 4 * SJ.B + 3.0; cols = math.ceil(dur / SJ.Mu.T) + 1
res = {}
for inst in ('arpaboca', 'saron', 'marimba'):
    P = SJ.Mu.Pista(inst, cols); notas = [e for e in ev if e[0] == inst]
    for _, t, m, v, d, pan in notas: SJ.RJ.a_pista(P, SJ.K[inst], m, t, v, pan=pan, tonica=SJ.TON, escala=SJ.ESC, dur=d)
    a = min(e[1] for e in notas) + .5; b = a + 4
    sr, x = wavfile.read(render / f'{inst}.wav'); esc = receta['medidas'][inst]['escala']
    y = P.tiempo(a, b, 0) / esc; seg = x[int(round(a * sr)):int(round(a * sr)) + len(y), 0]
    e = seg - y; res[inst] = dict(ventana=[round(a, 2), round(b, 2)], error_max=float(np.abs(e).max() / np.abs(y).max()), error_rms_db=round(20 * math.log10(np.sqrt(np.mean(e ** 2)) / np.sqrt(np.mean(y ** 2))), 1))
    print(inst, res[inst])
receta['prueba_exacta'] = res; (out / 'receta.json').write_text(json.dumps(receta, ensure_ascii=False, indent=1), encoding='utf-8')
