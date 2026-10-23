"""«planeta 9» · la mezcla. Pistas del navegador (render/<et>-<pista>.wav, estéreo float32) y objetos de node
(render/<et>-<objeto>.wav, mono float32). Cada pista se lleva a un nivel medido en su tramo activo, el bombo hace
bombear un poco al muro y a las teclas en los coros (J-pop), una sala oscura y grande; limitador suave.

Mide, además de bandas por sección y la voz contra el resto:
  LA NOTA QUE NO ESTÁ  por cada acorde, la energía en las octavas del planeta (f, 2f, 4f … ±1.5 %) contra la de su
                       quinta (3f, 6f, 12f …): debe quedar muy abajo — la fundamental nunca suena
  EL PLANETA SE OYE    en la coda, la autocorrelación de la mezcla encuentra el periodo de f (49 Hz) aunque no haya
                       nada en 49, 98, 196 Hz…
    python mezcla.py a2 [--etobj a1] [--entregar]
"""
import hashlib, json, os, subprocess, sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, fftconvolve
AQUI = Path(__file__).resolve().parent; RENDER = AQUI / 'render'; SR = 48000
ET = sys.argv[1]; ENTREGAR = '--entregar' in sys.argv
ETOBJ = sys.argv[sys.argv.index('--etobj') + 1] if '--etobj' in sys.argv else ET
C = json.loads(subprocess.run(['node', '-e', "require('./motor/cancion.js');const C=globalThis.Cancion;console.log(JSON.stringify({A:C.acordes(),S:C.SECC,T:C.T}))"],
                              capture_output=True, text=True, cwd=AQUI).stdout)
T = C['T']
#            pista        dB (rms activo)  sala   paneo/haas (objetos)
NIVEL = {'muro': (-19, .4), 'hielo': (-30, .5), 'teclas': (-22, .25), 'bajo': (-20, .08), 'bombo': (-19, .05), 'kit': (-24, .12),
         'ardilla': (-12, .2), 'grave': (-14.5, .16),   # +2: en a2-v1 la voz quedaba de −1.3 a −2.3 dB bajo el resto en presoros y coros
         'waterphone': (-25, .5), 'gong': (-25, .45), 'agua': (-27, .35), 'vozagua': (-18, .25)}
OBJ = ('waterphone', 'gong', 'agua', 'vozagua'); VOCES = ('ardilla', 'grave', 'vozagua')
BANDAS = [('sub', None, 90), ('graves', 90, 300), ('medios', 300, 2000), ('presencia', 2000, 6000), ('aire', 6000, None)]


def banda(x, lo, hi, orden=4):
    sos = butter(orden, [lo, hi], 'band', fs=SR, output='sos') if lo and hi else butter(orden, lo, 'high', fs=SR, output='sos') if lo else butter(orden, hi, 'low', fs=SR, output='sos')
    return sosfilt(sos, x, axis=0)


def lee(p):
    sr, x = wavfile.read(RENDER / f'{ETOBJ if p in OBJ else ET}-{p}.wav'); x = x.astype(np.float64)
    if x.ndim == 1: d = int(.011 * SR); x = np.stack([x, np.concatenate([np.zeros(d), x[:-d]])], 1) * .75   # mono: abierto con Haas
    return x


def rms_activo(x):
    m = x.mean(axis=1); c = np.sqrt(np.mean(m[:len(m) // 4800 * 4800].reshape(-1, 4800) ** 2, axis=1)); v = c[c > c.max() * 10 ** (-35 / 20)]
    return np.sqrt(np.mean(v ** 2))


pistas = {p: lee(p) for p in NIVEL if (RENDER / f'{ETOBJ if p in OBJ else ET}-{p}.wav').exists()}
n = max(len(x) for x in pistas.values())
for p in pistas: pistas[p] = np.pad(pistas[p], ((0, n - len(pistas[p])), (0, 0)))
seco = {p: x * 10 ** (NIVEL[p][0] / 20) / (rms_activo(x) + 1e-12) for p, x in pistas.items()}
# bombeo: el bombo baja 3 dB al muro y a las teclas 120 ms (sólo donde hay bombo)
if 'bombo' in seco:
    env = np.abs(seco['bombo']).max(axis=1); a = np.exp(-1 / (.12 * SR)); e = np.zeros(n); acc = 0
    for i in range(0, n, 48):
        acc = max(env[i:i + 48].max(), acc * a ** 48); e[i:i + 48] = acc
    g = 1 - .3 * np.clip(e / (e.max() + 1e-12) * 1.5, 0, 1)
    for p in ('muro', 'teclas'):
        if p in seco: seco[p] = seco[p] * g[:, None]
rng = np.random.default_rng(909); nir = int(3.6 * SR); t = np.arange(nir) / SR
ir = rng.standard_normal((nir, 2)) * np.exp(-t * 1.9)[:, None]; ir = banda(ir, 150, None, 2); osc = banda(ir, None, 2600, 2); w = np.minimum(1, t / 1.4)[:, None]
ir = ir * (1 - w) + osc * w; ir /= np.sqrt((ir ** 2).sum(axis=0).mean())
envio = sum(seco[p] * NIVEL[p][1] for p in seco)
mezcla = sum(seco.values()) + np.stack([fftconvolve(envio[:, c], ir[:, c])[:n] for c in range(2)], 1) * .3
mezcla = banda(mezcla, 25, None, 2)
tot0 = np.sqrt(np.mean(mezcla ** 2)); mezcla = np.tanh(mezcla / (tot0 * 10 ** (14 / 20))) * tot0 * 10 ** (14 / 20)    # techo suave a 14 dB del rms
mezcla *= .89 / np.abs(mezcla).max()

rms = lambda v: float(10 * np.log10(np.mean(v ** 2) + 1e-15))
med = {'secciones': {}, 'nota_que_no_esta': [], }
bandas = {nb: banda(mezcla, lo, hi) for nb, lo, hi in BANDAS}
for ns, b0, b1 in C['S']:
    a, b = int(b0 * T * SR), int(b1 * T * SR); tt = rms(mezcla[a:b])
    s = {'total_dB': round(tt, 1), **{nb: round(rms(bandas[nb][a:b]) - tt, 1) for nb, _, _ in BANDAS}}
    v = [seco[p] for p in VOCES if p in seco]; r = [seco[p] for p in seco if p not in VOCES]
    s['voz_sobre_resto_dB'] = round(rms(sum(v)[a:b]) - rms(sum(r)[a:b]), 1); med['secciones'][ns] = s
    print(f'{ns:8s}', s)
# la nota que no está: por acorde, energía en las bandas de f·2^k contra 3f·2^k (FFT del tramo, ±1.5 %)
m = mezcla.mean(axis=1); peor = -999
for (b0, fm, nombre), (b1, _, _) in zip(C['A'][:-1], C['A'][1:]):
    a, b = int((b0 * T + .15) * SR), int((b1 * T - .05) * SR)
    if b - a < SR // 2: continue
    X = np.abs(np.fft.rfft(m[a:b] * np.hanning(b - a))) ** 2; fr = np.fft.rfftfreq(b - a, 1 / SR); f = 440 * 2 ** ((fm - 69) / 12)
    en = lambda base: sum(X[(fr > base * 2 ** k * .985) & (fr < base * 2 ** k * 1.015)].sum() for k in range(8) if base * 2 ** k < 6000)
    d = 10 * np.log10(en(f) / (en(3 * f) + 1e-20) + 1e-20); peor = max(peor, d)
    # y contra toda la energía del tramo entre 40 Hz y 6 kHz (en el puente los parciales se estiran y la quinta se sale de su banda)
    dt = 10 * np.log10(en(f) / (X[(fr > 40) & (fr < 6000)].sum() + 1e-20) + 1e-20)
    med['nota_que_no_esta'].append([b0, round(f, 1), nombre, round(float(d), 1), round(float(dt), 1)])
esc = [q for q in med['nota_que_no_esta'] if q[2] != 'sustituto']; vis = [q for q in med['nota_que_no_esta'] if q[2] == 'sustituto']
print('la nota que no está (octavas del planeta contra su quinta, dB): peor', max(q[3] for q in esc), 'en el compás', max(esc, key=lambda q: q[3])[0],
      '· mediana', round(float(np.median([q[3] for q in esc])), 1), '· el pez beta (se ve a propósito):', [q[3] for q in vis])
print('   contra toda la energía: peor fuera del puente', max(q[4] for q in esc if not 46 <= q[0] < 54), '· en el puente', max(q[4] for q in esc if 46 <= q[0] < 54),
      '· mediana', round(float(np.median([q[4] for q in esc])), 1), '· el pez beta', [q[4] for q in vis])
# el planeta se oye: autocorrelación de la coda (compases 66-69), entre 30 y 400 Hz
a, b = int(66.2 * T * SR), int(69.5 * T * SR); s = m[a:b]; F = np.fft.rfft(s, 2 * len(s)); ac = np.fft.irfft(np.abs(F) ** 2)[:len(s)]; ac /= ac[0]
lags = np.arange(len(ac)); ok = (lags > SR / 400) & (lags < SR / 30); L = lags[ok][np.argmax(ac[ok])]
X = np.abs(np.fft.rfft(s * np.hanning(len(s)))) ** 2; fr = np.fft.rfftfreq(len(s), 1 / SR)
e49 = X[(fr > 47) & (fr < 51)].sum() / X[(fr > 140) & (fr < 155)].sum()
med['coda'] = {'periodo_hallado_Hz': round(SR / L, 2), 'energia_49_sobre_147_dB': round(10 * np.log10(e49 + 1e-20), 1)}
print('coda: la autocorrelación halla', round(SR / L, 2), 'Hz (el planeta: 49.0) · energía en 49 Hz contra 147 Hz:', med['coda']['energia_49_sobre_147_dB'], 'dB')
k = 1
while (RENDER / f'{ET}-mezcla-v{k}.wav').exists(): k += 1
VER = f'{ET}-mezcla-v{k}'
with open(RENDER / f'{VER}.wav', 'xb') as fh: wavfile.write(fh, SR, mezcla.astype(np.float32))
with open(RENDER / f'{VER}-medidas.json', 'x', encoding='utf-8') as fh: json.dump({'niveles': NIVEL, 'etobj': ETOBJ, **med}, fh, ensure_ascii=False, indent=1)
print('mezcla', VER)
if ENTREGAR:
    nonce = os.urandom(16).hex(); h = hashlib.sha256()
    for f in [AQUI / 'motor' / 'cancion.js', AQUI / 'objetos.js', Path(__file__), RENDER / f'{VER}.wav']: h.update(f.read_bytes())
    h.update(nonce.encode()); ID = h.hexdigest(); CC = ID[:12]; SAL = AQUI / 'proceso' / f'planeta-9-{CC}'; os.mkdir(SAL)
    m4a = AQUI / f'planeta-9-{CC}.m4a'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-i', str(RENDER / f'{VER}.wav'), '-af', 'loudnorm=I=-14:TP=-1.2:LRA=11',
                    '-ar', '48000', '-c:a', 'aac', '-b:a', '256k', str(m4a)], check=True)
    sha = lambda q: hashlib.sha256(Path(q).read_bytes()).hexdigest()
    with open(SAL / f'receta-{CC}.json', 'x', encoding='utf-8') as fh:
        json.dump({'id': ID, 'nonce': nonce, 'etiqueta': ET, 'etobj': ETOBJ, 'mezcla': VER, 'niveles': NIVEL, 'medidas': med,
                   'pistas_sha256': {p: sha(RENDER / f'{ETOBJ if p in OBJ else ET}-{p}.wav') for p in sorted(pistas)}, 'm4a': {m4a.name: sha(m4a)}}, fh, ensure_ascii=False, indent=1)
    print('entregado', m4a.name, SAL.name)
