"""«suma uno» · la mezcla. Toma las pistas del navegador (render/<et>-<pista>.wav, 32 bits flotantes), les pone
espacio y costura, mide por bandas y por sección, y escribe una versión nueva (nunca encima).

    python mezcla.py e1                 → render/e1-mezcla-v<k>.wav + medidas
    python mezcla.py e1 --entregar      → además suma-uno-<hash12>.m4a y proceso/receta-<hash12>.json

Contemporánea y limpia: sala neutra grande para la pared y la muestra (una sala de concierto, no un club); el pop
seco y al frente (es un síntoma que irrumpe); las voces cerca. En la sorpresa todo se abre más de sala.
"""
import hashlib, json, os, subprocess, sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, fftconvolve

AQUI = Path(__file__).resolve().parent
RENDER = AQUI / 'render'
SR = 48000
ET = sys.argv[1]; ENTREGAR = '--entregar' in sys.argv
P16 = 60 / 104 / 4
NIVEL = {'pared': 0, 'muestra': 0, 'evidencia': -2, 'pop': -4, 'reloj': 16, 'ardilla': 6, 'grave': 5}
# e1-v1 → v2: la voz quedaba 7-8.6 dB bajo el resto en prior, posterior y sorpresa (medido)
SALA = {'pared': .35, 'muestra': .45, 'evidencia': .25, 'pop': .05, 'reloj': .3, 'ardilla': .15, 'grave': .12}
SECCIONES = [('prior', 0, 240), ('evidencia', 240, 540), ('posterior', 540, 764), ('sorpresa', 764, 1084), ('inferencia', 1084, 1300)]
BANDAS = [('sub', None, 90), ('graves', 90, 300), ('medios', 300, 2000), ('presencia', 2000, 6000), ('aire', 6000, None)]
VOCES = ('ardilla', 'grave')


def lee(p):
    sr, x = wavfile.read(RENDER / f'{ET}-{p}.wav'); assert sr == SR
    return x.astype(np.float64)


def db(v): return 10 ** (v / 20)


def banda(x, lo, hi, orden=4):
    if lo and hi: sos = butter(orden, [lo, hi], 'band', fs=SR, output='sos')
    elif lo: sos = butter(orden, lo, 'high', fs=SR, output='sos')
    else: sos = butter(orden, hi, 'low', fs=SR, output='sos')
    return sosfilt(sos, x, axis=0)


def curva_p(puntos, n):
    """[[pulso, valor]…] → curva por muestra, suave en las uniones."""
    t = np.arange(n) / SR / P16; y = np.full(n, float(puntos[-1][1]))
    for (b0, v0), (b1, v1) in zip(puntos[:-1], puntos[1:]):
        m = (t >= b0) & (t < b1); u = (t[m] - b0) / (b1 - b0); u = u * u * (3 - 2 * u); y[m] = v0 + (v1 - v0) * u
    return y


def sala(cola=3.2):
    rng = np.random.default_rng(1300); n = int(cola * SR); t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-t * 2.2)[:, None]
    ir = banda(ir, 120, None, 2); oscura = banda(ir, None, 2200, 2); w = np.minimum(1, t / 1.6)[:, None]
    ir = ir * (1 - w) + oscura * w
    for d, g in ((.013, .45), (.023, .35), (.031, .3), (.047, .22), (.061, .18)):
        k = int(d * SR); ir[k, 0] += g; ir[int(k * 1.17), 1] += g
    return ir / np.sqrt((ir ** 2).sum(axis=0).mean()) * .9


pistas = {p: lee(p) for p in NIVEL if (RENDER / f'{ET}-{p}.wav').exists()}
n = max(len(x) for x in pistas.values())
for p in pistas: pistas[p] = np.pad(pistas[p], ((0, n - len(pistas[p])), (0, 0)))
seco = {p: pistas[p] * db(NIVEL[p]) for p in pistas}
abre = curva_p([[0, 1], [760, 1], [770, 1.8], [1080, 1.8], [1100, 1.1], [1300, 1.1]], n)[:, None]     # la sorpresa, más sala
suma = sum(seco.values())
envio = sum(seco[p] * SALA[p] for p in seco) * abre
ir = sala()
mezcla = suma + np.stack([fftconvolve(envio[:, c], ir[:, c])[:n] for c in range(2)], 1) * .3
mezcla = banda(mezcla, 28, None, 2)
mezcla = np.tanh(mezcla * .9) / .9

med = {}
bandas = {nb: banda(mezcla, lo, hi) for nb, lo, hi in BANDAS}
rms = lambda v: float(10 * np.log10(np.mean(v ** 2) + 1e-12))
for ns, b0, b1 in SECCIONES:
    a, b = int(b0 * P16 * SR), int(b1 * P16 * SR); tot = rms(mezcla[a:b])
    med[ns] = {'total_dB': round(tot, 1), **{nb: round(rms(bandas[nb][a:b]) - tot, 1) for nb, _, _ in BANDAS}}
    voz = [seco[p] for p in VOCES if p in seco]; resto = [seco[p] for p in seco if p not in VOCES]
    med[ns]['voz_sobre_resto_dB'] = round(rms(sum(voz)[a:b]) - rms(sum(resto)[a:b]), 1) if voz else None
for ns, m in med.items(): print(f'{ns:11s}', m)
k = 1
while (RENDER / f'{ET}-mezcla-v{k}.wav').exists(): k += 1
VER = f'{ET}-mezcla-v{k}'
with open(RENDER / f'{VER}.wav', 'xb') as fh: wavfile.write(fh, SR, (mezcla / max(1, np.abs(mezcla).max()) * .98).astype(np.float32))
with open(RENDER / f'{VER}-medidas.json', 'x', encoding='utf-8') as fh:
    json.dump({'niveles_dB': NIVEL, 'sala': SALA, 'secciones': med}, fh, ensure_ascii=False, indent=1)
print('mezcla', VER)

if ENTREGAR:
    nonce = os.urandom(16).hex(); h = hashlib.sha256()
    for f in [AQUI / 'motor' / 'cancion.js', Path(__file__)] + [RENDER / f'{ET}-{p}.wav' for p in sorted(pistas)]: h.update(f.read_bytes())
    h.update(nonce.encode()); ID = h.hexdigest(); C = ID[:12]
    m4a = AQUI / f'suma-uno-{C}.m4a'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-i', str(RENDER / f'{VER}.wav'),
                    '-af', 'loudnorm=I=-15:TP=-1.2:LRA=11', '-ar', '48000', '-c:a', 'aac', '-b:a', '192k', str(m4a)], check=True)
    sha = lambda q: hashlib.sha256(Path(q).read_bytes()).hexdigest()
    with open(AQUI / 'proceso' / f'receta-{C}.json', 'x', encoding='utf-8') as fh:
        json.dump({'id': ID, 'nonce': nonce, 'etiqueta': ET, 'mezcla': VER, 'niveles_dB': NIVEL, 'sala': SALA, 'medidas': med,
                   'pistas_sha256': {p: sha(RENDER / f'{ET}-{p}.wav') for p in sorted(pistas)},
                   'cancion_js_sha256': sha(AQUI / 'motor' / 'cancion.js'), 'm4a': {m4a.name: sha(m4a)}}, fh, ensure_ascii=False, indent=1)
    print('entregado', m4a.name)
