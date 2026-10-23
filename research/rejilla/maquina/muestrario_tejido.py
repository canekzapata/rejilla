"""El muestrario TEJIDO del loop B. El primero pegaba las diez demos con un segundo de silencio entre
cada una (un catálogo, no música: Canek lo notó). Aquí se encadenan sobre la rejilla del compás,
encimadas dos compases con curvas de potencia constante, y debajo corre la portadora de punta a
punta (el La con su latido): el hilo que las cose. El único silencio es el vacío funky de t08.

Acuerdo de nombres del 13 de octubre: id SHA-256 (programa + demos + nonce); nada se escribe encima.
"""
import hashlib, json, os, subprocess
from pathlib import Path
import numpy as np
from scipy.io import wavfile
import demos as D
import nave as V

VERSION = 'muestrario-tejido 1'
AQUI = Path(__file__).parent
R = D.R
DEMOS = ['t01', 't02', 't03', 't04', 't05', 't06', 't07', 't08', 't09', 't10']
ENCIME = 2                                                   # compases encimados entre una demo y la siguiente

nonce = os.urandom(16).hex(); h = hashlib.sha256()
for p in [Path(__file__)] + [R / f'{d}.final.wav' for d in DEMOS]: h.update(p.read_bytes())
h.update(VERSION.encode()); h.update(nonce.encode()); ID = h.hexdigest(); C = ID[:12]

xs = []
for d in DEMOS:
    sr, x = wavfile.read(R / f'{d}.final.wav'); xs.append(x.astype(float) / 32768)
barras = [int(np.ceil(len(x) / D.L(1))) for x in xs]
inicio = [0]
for b in barras[:-1]: inicio.append(inicio[-1] + b - ENCIME)
total = inicio[-1] + barras[-1]
n = D.L(total)
y = np.zeros((n, 2))
marcas = []
for k, (x, i0, nb) in enumerate(zip(xs, inicio, barras)):
    x = D.largo(x, D.L(nb)); m = len(x)
    w = np.ones(m); f = D.L(ENCIME)
    u = np.linspace(0, 1, f)
    if k > 0: w[:f] = np.sin(u * np.pi / 2)                  # entra
    if k < len(xs) - 1: w[-f:] = np.cos(u * np.pi / 2)       # sale mientras entra la siguiente
    a = D.L(i0); y[a:a + m] += x * w[:, None]
    marcas.append((DEMOS[k], round(a / D.SR, 2)))

# el hilo: la portadora sola con su latido y su halo, de punta a punta, sin raya
plan = lambda b: {'groove': 0, 'halo': .55, 'timbre': .5, 'latido': .8}
hilo = D.liso('hilo', lambda off: D.portadora_off(total, plan, off), total)
hilo = D.largo(hilo, n); hilo = hilo / (np.sqrt((hilo ** 2).mean()) + 1e-12)
k = D.L(.5); cs = np.concatenate([[0], np.cumsum((y ** 2).mean(1))]); vivo = np.sqrt((cs[k:] - cs[:-k]) / k)
nivel = .18 * np.median(vivo)                                # el hilo queda ~15 dB bajo las demos
# el vacío de t08 (su tercer compás) también calla el hilo
v0 = D.L(inicio[DEMOS.index('t08')] + 2); v1 = D.L(inicio[DEMOS.index('t08')] + 3)
g = np.ones(n); r = D.L(.03); g[v0 - r:v0] = np.linspace(1, 0, r); g[v0:v1] = 0; g[v1:v1 + r] = np.linspace(0, 1, r)
y = y + hilo * nivel * g[:, None]

wav = R / 'muestrario-tejido.wav'
wavfile.write(wav, D.SR, (y / np.abs(y).max() * .9).astype(np.float32))
m4a = AQUI / f'muestrario-texturas-tejido-s1031-{C}.m4a'
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-i', str(wav), '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',
                '-c:a', 'aac', '-b:a', '192k', str(m4a)], check=True)

# medir: ¿dónde hay silencio (< -60 dBFS por más de 0.2 s)?
mm = np.abs(y.mean(1)) / np.abs(y).max(); w50 = int(.05 * D.SR)
e = 20 * np.log10(np.array([mm[i:i + w50].max() for i in range(0, len(mm) - w50, w50)]) + 1e-9)
sil, i = [], 0
while i < len(e):
    if e[i] < -60:
        j = i
        while j < len(e) and e[j] < -60: j += 1
        if (j - i) * .05 >= .2: sil.append((round(i * .05, 1), round((j - i) * .05, 2)))
        i = j
    else: i += 1
receta = {'id': ID, 'version': VERSION, 'nonce': nonce, 'encime_compases': ENCIME, 'marcas_s': marcas,
          'duracion_s': round(n / D.SR, 1), 'silencios_(inicio_s, dur_s)': sil,
          'm4a': {m4a.name: hashlib.sha256(m4a.read_bytes()).hexdigest()}}
with open(AQUI / 'proceso' / f'receta-muestrario-tejido-{C}.json', 'x', encoding='utf-8') as f:
    json.dump(receta, f, ensure_ascii=False, indent=1)
print(C, f'{n / D.SR:.0f} s', 'silencios:', sil)
