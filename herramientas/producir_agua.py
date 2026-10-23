"""Cadena completa de Lo que el agua dibuja. Cada ejecución crea una carpeta nueva."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
AGUA = ROOT / 'research/rejilla/lo-que-el-agua-dibuja'


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--partitura', type=Path, default=ROOT / 'partituras/lo-que-el-agua-dibuja.json')
    ap.add_argument('--destino', type=Path, default=ROOT / 'renders')
    a = ap.parse_args()
    for program in ('node', 'ffmpeg'):
        if not shutil.which(program):
            ap.error('Falta ' + program + '. Consulta README.md')
    score = json.loads(a.partitura.read_text(encoding='utf-8'))
    score['instrumentos'] = os.path.relpath(ROOT / 'biblioteca-de-instrumentos', AGUA).replace('\\', '/')
    nonce = uuid.uuid4().hex
    full = hashlib.sha256(a.partitura.read_bytes() + Path(__file__).read_bytes() + nonce.encode()).hexdigest()
    a.destino.mkdir(parents=True, exist_ok=True)
    run = a.destino.resolve() / f'agua-s{score["semilla"]}-{full[:12]}'
    run.mkdir(exist_ok=False)
    (run / 'partitura.json').write_text(json.dumps(score, ensure_ascii=False), encoding='utf-8')
    stages = [('guitarra', ['node', str(AGUA / 'render_node.cjs'), str(run)]),
              ('lluvia, trueno, crecida y batería Python', [sys.executable, str(AGUA / 'render_py.py'), str(run)]),
              ('voces de Sabina', ['node', str(AGUA / 'render_voz.cjs'), str(run)]),
              ('batería Web Audio', ['node', str(AGUA / 'render_web.cjs'), str(run)]),
              ('mezcla y master', [sys.executable, str(AGUA / 'mezcla.py'), str(run)])]
    for name, command in stages:
        print('\nEtapa: ' + name, flush=True)
        subprocess.run(command, check=True, cwd=ROOT, env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
    receipt = dict(ejecucion=full, nonce=nonce, partitura=str(a.partitura), carpeta=str(run),
                   entrega=json.loads((run / 'entrega-mezcla.json').read_text(encoding='utf-8')))
    from proceso_agua import guardar
    receipt['proceso'] = guardar(run, receipt['entrega'])
    (run / 'EJECUCION.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
