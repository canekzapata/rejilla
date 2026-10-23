"""Abrir la obra por HTTP local, sin dependencias ni conexión exterior."""
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.request import urlopen
import threading, webbrowser

ROOT=Path(__file__).resolve().parent
STATE=ROOT/'puerto.local'
def running():
    try:
        url=STATE.read_text(encoding='utf-8').strip()
        if not url.startswith('http://127.0.0.1:'): return None
        with urlopen(url,timeout=1) as r:
            if b'P-adic Bell' in r.read(2000): return url
    except (OSError,ValueError): pass
    return None
def main():
    url=running()
    if url: webbrowser.open(url); return
    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self,*args): pass
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT/'dist')))
    url=f'http://127.0.0.1:{server.server_port}/'
    STATE.write_text(url,encoding='utf-8')
    threading.Timer(.2,lambda:webbrowser.open(url)).start()
    server.serve_forever()
if __name__=='__main__': main()
