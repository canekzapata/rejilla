"""Servidor temporal local: sólo permite crear voz.wav dentro de una ejecución existente."""
import http.server, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DEST = Path(sys.argv[1]).resolve()
assert DEST.is_relative_to(ROOT / 'lo-que-no-sono') and DEST.is_dir()
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw): super().__init__(*a,directory=str(ROOT),**kw)
    def log_message(self,*a): pass
    def do_PUT(self):
        n=int(self.headers.get('Content-Length',0))
        if self.path!='/voz.wav' or not 0<n<150_000_000: self.send_error(400); return
        try:
            with (DEST/'render'/'voz.wav').open('xb') as f: f.write(self.rfile.read(n))
        except FileExistsError: self.send_error(409); return
        self.send_response(201); self.end_headers()
http.server.ThreadingHTTPServer(('127.0.0.1',8493),H).serve_forever()
