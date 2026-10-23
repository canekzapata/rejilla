"""La ciudad se hunde bailando — capas de Python: el bajo de cumbia y el teclado cumbianchero (en tiempo de disco), las sirenas
(en tiempo real) y el programa de cada estación de la radio: pedazos de nuestras canciones de rejilla (material propio, decodificado
con ffmpeg a mono) y una señal horaria (un pitido por segundo, largo en el minuto). La radio misma se arma en la mezcla, porque una de
sus estaciones es el propio sonidero.
    python render_py.py <carpeta> [capa…]"""
import json, os, subprocess, sys, numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI); import sintes10 as S
RUN = sys.argv[1]; solo = sys.argv[2:]; P = json.load(open(os.path.join(RUN, 'partitura.json'), encoding='utf-8')); SR = 48000; N = int(P['duracion'] * SR)
quiero = lambda n: not solo or n in solo
def guardar(n, y): y.astype(np.float32).tofile(os.path.join(RUN, n + '.f32')); print(n, y.shape, 'pico', round(float(np.abs(y).max()), 3), flush=True)
if quiero('bajo'): guardar('bajo', S.bajo(P['bajo'], N))
if quiero('teclado'): guardar('teclado', S.teclado(P['teclado'], N, 1))
if quiero('sirenas'): guardar('sirenas', S.sirena(P['sirenas'], N, 2))
if quiero('estaciones'):
    for k, e in enumerate(P['radio']['estaciones']):
        if e['tipo'] == 'musica':
            src = os.path.join(AQUI, '..', e['fuente'])
            raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(e['desde']), '-i', src, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
            x = np.frombuffer(raw, dtype=np.float32); y = np.zeros(N, np.float32)
            while len(x) and len(y) and np.count_nonzero(y) == 0:                      # si la canción se acaba, vuelve a empezar
                reps = int(np.ceil(N / len(x))); y = np.tile(x, reps)[:N]
            guardar(f'estacion{k}', y)
        elif e['tipo'] == 'horaria':
            t = np.arange(N) / SR; s = (t % 1) < np.where((t % 60) < 1, .5, .1)
            guardar(f'estacion{k}', (np.sin(2 * np.pi * 1000 * t) * s * .6).astype(np.float32))
