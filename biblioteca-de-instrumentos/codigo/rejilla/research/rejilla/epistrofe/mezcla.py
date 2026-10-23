"""«epístrofe» · la mezcla. Toma las pistas del navegador (render/<et>-<pista>.wav, 32 bits flotantes), les pone
espacio y costura, mide el balance por bandas y por sección y escribe una versión nueva (nunca encima).

    python mezcla.py e2                 → render/e2-mezcla-v<k>.wav + medidas
    python mezcla.py e2 --entregar      → además epistrofe-<hash12>.m4a y proceso/receta-<hash12>.json

Muy moderna: sin cinta ni ruido de piso (eso era la edad de «la misma garganta»). El espacio es una sala neutra
(la armonía cambia de tonalidad todo el tiempo: una sala afinada en La la ensuciaría), la ardilla lleva un eco
cruzado de 3/16 y el bombo empuja al muro, al bajo y al piano (funk).
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
PART = json.load(open(RENDER / f'{ET}-partitura.json', encoding='utf-8'))
T, COMP = PART['T'], PART['compases']

NIVEL = {'muro': -3, 'piano': -2, 'bajo': -6, 'bombo': -5, 'kit': 8, 'ardilla': 1, 'grave': 2, 'esquina': 1}
# e7: Canek, «la voz aguda es demasiado pesada»: ardilla −2 dB (con −4 quedaba 3 dB bajo el resto), sin cuerpo bajo 300 Hz y con la mitad de eco
# e2: el muro sonaba medio segundo por compás (bug de limpieza); en e3 se sostiene y vuelve a −3 dB (medido)
SALA = {'muro': .25, 'piano': .3, 'bajo': 0, 'bombo': 0, 'kit': .12, 'ardilla': .18, 'grave': .1, 'esquina': .35}
SECCIONES = [('muro', 0, 8), ('verso 1', 8, 24), ('coro', 24, 32), ('callejón', 32, 40), ('verso 2', 40, 48),
             ('coro final', 48, 56), ('salida', 56, 64)]
BANDAS = [('sub', None, 90), ('graves', 90, 300), ('medios', 300, 2000), ('presencia', 2000, 6000), ('aire', 6000, None)]
VOCES = ('ardilla', 'grave', 'esquina')


def lee(p):
    sr, x = wavfile.read(RENDER / f'{ET}-{p}.wav'); assert sr == SR
    return x.astype(np.float64)


def db(v): return 10 ** (v / 20)


def banda(x, lo, hi, orden=4):
    if lo and hi: sos = butter(orden, [lo, hi], 'band', fs=SR, output='sos')
    elif lo: sos = butter(orden, lo, 'high', fs=SR, output='sos')
    else: sos = butter(orden, hi, 'low', fs=SR, output='sos')
    return sosfilt(sos, x, axis=0)


def sala_neutra(cola=2.2):
    """Reflexiones tempranas + cola de ruido estéreo que se oscurece (sin afinar)."""
    rng = np.random.default_rng(108); n = int(cola * SR); t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-t * 3.1)[:, None]
    ir = banda(ir, 180, None, 2); oscura = banda(ir, None, 2500, 2); w = np.minimum(1, t / 1.2)[:, None]
    ir = ir * (1 - w) + oscura * w
    for d, g in ((.011, .5), (.019, .38), (.027, .3), (.041, .22)):
        k = int(d * SR); ir[k, 0] += g; ir[int(k * 1.13), 1] += g
    return ir / np.sqrt((ir ** 2).sum(axis=0).mean()) * .9


def eco_cruzado(x, retraso, fb=.35, mezcla=.22):
    """Eco de ida y vuelta entre los dos lados, cada vuelta más oscura."""
    d = int(retraso * SR); y = x.copy(); v = x.copy()
    for k in range(4):
        v = np.concatenate([np.zeros((d, 2)), v[:-d]])[:, ::-1]
        v = banda(v, 250, 4200 - 600 * k, 2) * fb; y += v * mezcla / fb
    return y


def envolvente(x, ataque=.003, suelta=.14):
    e = np.abs(x).max(axis=1); out = np.zeros_like(e); a, r = np.exp(-1 / (ataque * SR)), np.exp(-1 / (suelta * SR)); v = 0
    for i in range(0, len(e), 64):
        m = e[i:i + 64].max(); v = a * v + (1 - a) * m if m > v else r ** 64 * v; out[i:i + 64] = v
    return out


pistas = {p: lee(p) for p in NIVEL if (RENDER / f'{ET}-{p}.wav').exists()}
n = max(len(x) for x in pistas.values())
for p in pistas: pistas[p] = np.pad(pistas[p], ((0, n - len(pistas[p])), (0, 0)))
seco = {p: pistas[p] * db(NIVEL[p]) for p in pistas}
def curva_t(puntos, n):
    """[[compás, dB]…] → curva por muestra, suave en las uniones."""
    t = np.arange(n) / SR / T; y = np.full(n, float(puntos[-1][1]))
    for (b0, v0), (b1, v1) in zip(puntos[:-1], puntos[1:]):
        m = (t >= b0) & (t < b1); u = (t[m] - b0) / (b1 - b0); u = u * u * (3 - 2 * u); y[m] = v0 + (v1 - v0) * u
    return y


# la entrada tiene que oírse (medido: el muro solo quedaba 11 dB bajo el cuerpo) y en el callejón la voz hablada
# quedaba 6 dB bajo el muro roto
if 'muro' in seco: seco['muro'] = seco['muro'] * db(curva_t([[0, 8], [7, 7], [9, 0], [64, 0]], n))[:, None]
if 'grave' in seco: seco['grave'] = seco['grave'] * db(curva_t([[0, 0], [33, 0], [34, 6], [39.5, 6], [40.5, 0], [64, 0]], n))[:, None]
if 'ardilla' in seco: seco['ardilla'] = eco_cruzado(banda(seco['ardilla'], 300, None, 2), T * 3 / 16, mezcla=.11)
for p in ('bajo', 'piano'):
    if p in seco: seco[p] = np.tanh(seco[p] * 1.3) / 1.3              # grano: saturación suave
if 'bombo' in seco:                                                  # costura: el bombo empuja (hasta 5 dB)
    e = envolvente(seco['bombo']); e = e / (e.max() + 1e-9); duck = db(-5 * e)[:, None]
    for p in ('muro', 'bajo', 'piano'):
        if p in seco: seco[p] = seco[p] * duck
suma = sum(seco.values())
envio = sum(seco[p] * SALA[p] for p in seco)
ir = sala_neutra()
mezcla = suma + np.stack([fftconvolve(envio[:, c], ir[:, c])[:n] for c in range(2)], 1) * .3
mezcla = banda(mezcla, 28, None, 2)                                  # nada debajo de 28 Hz
mezcla = np.tanh(mezcla * .9) / .9

med = {}
bandas = {nb: banda(mezcla, lo, hi) for nb, lo, hi in BANDAS}
rms = lambda v: float(10 * np.log10(np.mean(v ** 2) + 1e-12))
for ns, b0, b1 in SECCIONES:
    a, b = int(b0 * T * SR), int(b1 * T * SR); tot = rms(mezcla[a:b])
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
    m4a = AQUI / f'epistrofe-{C}.m4a'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-i', str(RENDER / f'{VER}.wav'),
                    '-af', 'loudnorm=I=-13:TP=-1.2:LRA=8', '-ar', '48000', '-c:a', 'aac', '-b:a', '192k', str(m4a)], check=True)
    sha = lambda q: hashlib.sha256(Path(q).read_bytes()).hexdigest()
    with open(AQUI / 'proceso' / f'receta-{C}.json', 'x', encoding='utf-8') as fh:
        json.dump({'id': ID, 'nonce': nonce, 'etiqueta': ET, 'mezcla': VER, 'niveles_dB': NIVEL, 'sala': SALA, 'medidas': med,
                   'pistas_sha256': {p: sha(RENDER / f'{ET}-{p}.wav') for p in sorted(pistas)},
                   'cancion_js_sha256': sha(AQUI / 'motor' / 'cancion.js'), 'm4a': {m4a.name: sha(m4a)}}, fh, ensure_ascii=False, indent=1)
    print('entregado', m4a.name)
