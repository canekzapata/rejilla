"""Abrir Braid Organ por HTTP local; no instala paquetes ni necesita Internet."""
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.request import urlopen
import threading
import webbrowser

ROOT = Path(__file__).resolve().parent
STATE = ROOT / 'puerto.local'

def main():
    try:
        previous = STATE.read_text(encoding='utf-8').strip()
        if previous.startswith('http://127.0.0.1:'):
            with urlopen(previous, timeout=1) as response:
                if b'Braid Organ' in response.read(2000):
                    webbrowser.open(previous)
                    return
    except (OSError, ValueError):
        pass
    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT / 'dist')))
    url = f'http://127.0.0.1:{server.server_port}/'
    STATE.write_text(url, encoding='utf-8')
    threading.Timer(.3, lambda: webbrowser.open(url)).start()
    print(url, flush=True)
    server.serve_forever()

if __name__ == '__main__':
    main()
