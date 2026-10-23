"""Prueba de integración de 40 s: activa las 23 capas sin renderizar la canción completa."""
import copy
import json
import math
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = json.loads((ROOT/'partituras/lo-que-el-agua-dibuja.json').read_text(encoding='utf8'))
    original = copy.deepcopy(p)
    d = 40
    p.update(titulo='Prueba técnica de 23 capas (no es la obra completa)', duracion=d)
    ratio = d/original['duracion']
    for s in p['secciones']:
        for key in ('t', 't1', 't_real', 't1_real'):
            if key in s:
                s[key] *= ratio
    p['guitarra']['dur'] = d
    fr = p['guitarra']['fr']
    for c in p['guitarra']['cuerdas']:
        c['curva'] = [c['abierta']+5+math.sin(i/fr)*.7 for i in range(d*fr+2)]
        c['pulsos'] = [[i+.1, .7] for i in range(0, d-2, 2)]
    p['gotas'] = [{**next(e for e in original['gotas'] if e['toque']==toque), 't': 1+i, 'dur': 1.2} for i, toque in enumerate(('pizz', 'arco', 'col'))]
    p['rayos'] = [{**original['rayos'][0], 'llega': .3}]
    p['lluvia']['intensidad'] = [30.]*(d*p['lluvia']['fr']+2)
    p['hats'] = [{**original['hats'][0], 't': i+.3} for i in range(1, d-2)]
    p['ocho'] = [{**original['ocho'][0], 't': i+.2} for i in range(1, d-2, 2)]
    p['viento'] = [[0, 9], [d, 12]]
    p['sabina'] = []
    v = next(s['t'] for s in p['secciones'] if s['num']=='V')
    for capa in dict.fromkeys(r['capa'] for r in original['sabina']):
        r = copy.deepcopy(next(r for r in original['sabina'] if r['capa']==capa))
        r['eventos'] = [{'t': v+.1 if capa=='rio' else 1.2, 'dur': 1.6, 'texto': 'agua', 'nota': 62}]
        p['sabina'].append(r)
    p['coros'] = {k: [{**events[0], 't': 2., 'dur': 1.}] for k, events in original['coros'].items()}
    p['web'] = {k: [{**events[0], 't': i+.4} for i in range(1, d-2, 2)] for k, events in original['web'].items()}
    dest = ROOT/'renders'/('prueba-agua-'+uuid.uuid4().hex[:12])
    dest.mkdir(parents=True, exist_ok=False)
    score = dest/'partitura-prueba.json'
    score.write_text(json.dumps(p, ensure_ascii=False), encoding='utf8')
    subprocess.run([sys.executable, str(ROOT/'herramientas/producir_agua.py'), '--partitura', str(score), '--destino', str(dest)], cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
