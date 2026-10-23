"""Servidor local de taller: sirve la pieza y acepta PUT de audio renderizado en el navegador, SÓLO dentro de
render/ (que git ignora); ahora también acepta .json (la partitura de cada render), con nombres simples y sin pisar archivos existentes. No es para publicar.

    python tools/servidor.py 8487
"""
import http.server, re, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
RENDER = RAIZ / 'render'


class Taller(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(RAIZ), **k)

    def end_headers(self):
        # que el navegador revise cada vez: con caché heurística servía un sonido.js viejo junto a un index.html nuevo
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def do_PUT(self):
        m = re.fullmatch(r'/render/([a-z0-9\-]{1,80}\.(?:wav|png|json))', self.path)
        n = int(self.headers.get('Content-Length', 0))
        if not m or n <= 0 or n > 400_000_000:
            self.send_error(400, 'sólo render/<nombre>.wav|png|json'); return
        RENDER.mkdir(exist_ok=True)
        destino = RENDER / m.group(1)
        try:
            with open(destino, 'xb') as f: f.write(self.rfile.read(n))      # nunca se escribe encima
        except FileExistsError:
            self.send_error(409, 'ya existe'); return
        self.send_response(201); self.end_headers(); self.wfile.write(b'ok')


if __name__ == '__main__':
    http.server.ThreadingHTTPServer(('127.0.0.1', int(sys.argv[1]) if len(sys.argv) > 1 else 8487), Taller).serve_forever()
