"""Taller local: catálogo, secuenciador y muestras calculadas con los motores originales."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit, unquote
import uuid
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
CATALOGO = {r['id']: r for r in json.loads((ROOT/'CATALOGO-TALLER.json').read_text(encoding='utf8'))}
PEDIDOS = {}
for p in (ROOT/'ejemplos').rglob('*.json'):
    r = json.loads(p.read_text(encoding='utf8'))
    if 'motor_propio' in r:
        PEDIDOS['propio-'+r['motor_propio']] = p
    elif 'prototipo' in r:
        PEDIDOS['prototipo-'+r['prototipo']] = p
LOCK = threading.Lock()


def disponible(row):
    return row['id'] in PEDIDOS or row.get('ficha', {}).get('motor') in ('modal', 'golpe', 'boca', 'arco', 'python', 'objeto')


class Taller(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def json(self, value, code=200):
        raw = json.dumps(value, ensure_ascii=False).encode('utf8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        uri = urlsplit(self.path)
        if uri.path == '/api/catalogo':
            return self.json({'muestras': [k for k, r in CATALOGO.items() if disponible(r)]})
        if uri.path != '/api/muestra':
            # No exponer archivos ocultos (incluidos .git y .env).
            if any(x.startswith('.') for x in unquote(uri.path).split('/') if x):
                return self.send_error(404)
            return super().do_GET()
        ident = parse_qs(uri.query).get('id', [''])[0]
        row = CATALOGO.get(ident)
        if not row or not disponible(row):
            return self.json({'error': 'Esta entrada conserva fuentes; todavía no tiene una muestra integrada.'}, 422)
        try:
            # Una producción por vez: evita saturar el equipo y duplicar una misma muestra.
            with LOCK:
                cache = ROOT/'renders'/'catalogo'
                cache.mkdir(parents=True, exist_ok=True)
                stamp = hashlib.sha256((ident+'taller-v2').encode()).hexdigest()[:16]
                index = cache/(stamp+'.json')
                if index.exists():
                    return self.json(json.loads(index.read_text(encoding='utf8')))
                dest = cache/(ident+'-'+uuid.uuid4().hex[:12])
                dest.mkdir(exist_ok=False)
                if ident in PEDIDOS:
                    cmd = [sys.executable, str(ROOT/'python/taller.py'), str(PEDIDOS[ident]), '--destino', str(dest)]
                else:
                    out = dest/'nota.wav'
                    if row['ficha']['motor'] == 'objeto':
                        cmd = ['node', str(ROOT/'herramientas/nota-objeto.cjs'), ident, str(out)]
                    else:
                        cmd = [sys.executable, str(ROOT/'herramientas/nota.py'), ident, '--salida', str(out)]
                done = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding='utf8', errors='replace', timeout=240,
                                      env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
                if done.returncode:
                    raise RuntimeError((done.stderr or done.stdout)[-1800:])
                waves = list(dest.rglob('*.wav'))
                if not waves:
                    raise RuntimeError('El productor terminó sin escribir audio WAV.')
                wav = max(waves, key=lambda p: p.stat().st_size)
                result = {'id': ident, 'url': '/'+wav.relative_to(ROOT).as_posix(), 'motor': row['motor']}
                with index.open('x', encoding='utf8') as f:
                    json.dump(result, f, ensure_ascii=False)
                return self.json(result)
        except Exception as e:
            return self.json({'error': str(e)}, 500)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--puerto', type=int, default=8481)
    ap.add_argument('--abrir', action='store_true')
    a = ap.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', a.puerto), Taller)
    url = f'http://127.0.0.1:{a.puerto}/laboratorio.html'
    print('Rejilla: '+url, flush=True)
    if a.abrir:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
