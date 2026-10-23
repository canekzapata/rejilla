"""«la misma garganta» · la mezcla. Toma las pistas que renderizó el navegador (render/<etiqueta>-<pista>.wav,
32 bits flotantes) y les pone espacio, edad y costura; mide el balance por bandas y por sección; escribe el m4a.

    python mezcla.py e1                 → render/e1-mezcla-v<k>.wav (versión nueva, nunca encima) + medidas
    python mezcla.py e1 --entregar      → además la-misma-garganta-<hash12>.m4a y su receta (nombre con hash, nunca encima)

Las seis capas (TEXTURAS.md de la máquina del tiempo) aquí:
  cuerpo      lo pone cada instrumento en cancion.js (parciales dobles, peine, FM)
  grano       saturación suave por pista; ruido afinado (peine de La) como piso
  movimiento  las curvas de cancion.js; el teléfono de la nave se abre conforme baja a La3
  espacio     planos: tierra cerca y seca; nave por teléfono y lejos; sala afinada en La (Lucier) para todo lo demás
  edad        cinta: wow lento, piso de ruido afinado, agudos que se gastan
  costura     bombo que empuja al bajo, la portadora y la pared (sidechain); nada termina en seco
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

# niveles de cada pista (dB) — se ajustan midiendo por bandas
NIVEL = {'portadora': -7, 'bajo': -7, 'bombo': -5, 'caja': -5, 'pared': -6, 'vidrio': -8, 'consonantes': -5,
         'tierra': 3, 'nave': 1, 'una': 3}
# e2 → e3: el sub quedaba a −3 dB del total y la voz 4-8 dB bajo el resto (medido): graves −3, voz +4, presencia +4
SALA = {'portadora': .18, 'bajo': 0, 'bombo': .04, 'caja': .35, 'pared': .5, 'vidrio': .7, 'consonantes': .3,
        'tierra': .12, 'nave': .45, 'una': .25}                       # cuánto va a la sala afinada


def lee(p):
    sr, x = wavfile.read(RENDER / f'{ET}-{p}.wav'); assert sr == SR
    return x.astype(np.float64)


def db(v): return 10 ** (v / 20)


def curva_t(puntos, n):
    """[[compás, valor]…] → curva por muestra (suave en las uniones, como cancion.js)."""
    t = np.arange(n) / SR / T; y = np.full(n, float(puntos[-1][1]))
    for (b0, v0), (b1, v1) in zip(puntos[:-1], puntos[1:]):
        m = (t >= b0) & (t < b1); u = (t[m] - b0) / (b1 - b0); u = u * u * (3 - 2 * u); y[m] = v0 + (v1 - v0) * u
    y[t < puntos[0][0]] = puntos[0][1]
    return y


def banda(x, lo, hi, orden=4):
    if lo and hi: sos = butter(orden, [lo, hi], 'band', fs=SR, output='sos')
    elif lo: sos = butter(orden, lo, 'high', fs=SR, output='sos')
    else: sos = butter(orden, hi, 'low', fs=SR, output='sos')
    return sosfilt(sos, x, axis=0)


def sala_afinada(cola=2.8):
    """Respuesta de una sala que resuena en La (Lucier): armónicos de 55 Hz que decaen + ruido que decae.
    Normalizada por su respuesta en los armónicos (si no, amplifica la portadora: medido en la portadora, +5 dB)."""
    rng = np.random.default_rng(1015); n = int(cola * SR); t = np.arange(n) / SR; ir = np.zeros((n, 2))
    for c in range(2):
        for k in range(2, 90):
            f = 55 * k
            if f > 9000: break
            ir[:, c] += .4 / np.sqrt(k) * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi)) * np.exp(-t / (.8 / (1 + k / 30)))
        ir[:, c] += rng.standard_normal(n) * .5 * np.exp(-t * 2.6)
        ir[:, c] *= np.minimum(1, t / .015)
    resp = max(abs(np.sum(ir[::2, 0] * np.exp(-2j * np.pi * 55 * k * t[::2]))) * 2 for k in range(2, 20))
    return ir / resp * 6


def telefono(x, u):
    """La nave por teléfono: banda 380-2800 Hz y un poco de saturación; u = cuánto (0 = voz limpia)."""
    tel = np.tanh(banda(x, 380, 2800) * 2.2) / 1.6
    return x * (1 - u[:, None]) + tel * u[:, None]


def eco(x, retraso, fb=.32, mezcla=.3):
    """Eco con filtro (cada vuelta más oscura): la nave se repite como si el aire se la devolviera tarde."""
    d = int(retraso * SR); y = np.zeros_like(x); y[:] = x; vuelta = x.copy()
    for k in range(5):
        vuelta = banda(np.concatenate([np.zeros((d, 2)), vuelta[:-d]]), None, 3200 - 400 * k, 2) * fb
        y += vuelta * mezcla / fb
    return y


def envolvente(x, ataque=.004, suelta=.18):
    e = np.abs(x).max(axis=1); out = np.zeros_like(e); a, r = np.exp(-1 / (ataque * SR)), np.exp(-1 / (suelta * SR)); v = 0
    # un paso por bloques de 64 muestras basta para un sidechain
    for i in range(0, len(e), 64):
        m = e[i:i + 64].max(); v = a * v + (1 - a) * m if m > v else r ** 64 * v; out[i:i + 64] = v
    return out


pistas = {p: lee(p) for p in NIVEL if (RENDER / f'{ET}-{p}.wav').exists()}
n = max(len(x) for x in pistas.values())
for p in pistas: pistas[p] = np.pad(pistas[p], ((0, n - len(pistas[p])), (0, 0)))
seco = {p: pistas[p] * db(NIVEL[p]) for p in pistas}

# la niebla tiene que oírse en bocinas chicas: la pared (medios) sube 9 dB al principio y baja al entrar la voz
# (medido en e2/e3: la niebla quedaba 9 dB bajo el cuerpo y casi toda en sub; en la portadora eso fue «no oigo nada»)
if 'pared' in seco: seco['pared'] = seco['pared'] * db(curva_t([[0, 12], [7.5, 16], [10.5, 0], [60, 0]], n))[:, None]
if 'portadora' in seco:                 # y la portadora, sin su sub mientras dura la niebla (vuelve con el bombo)
    k = curva_t([[0, 1], [6, 1], [8.5, 0], [60, 0]], n)[:, None]
    seco['portadora'] = seco['portadora'] * (1 - k) + banda(seco['portadora'], 160, None, 2) * k
# grano: saturación suave en lo que tiene cuerpo
for p in ('bajo', 'portadora', 'caja'):
    if p in seco: seco[p] = np.tanh(seco[p] * 1.4) / 1.4
# la nave: teléfono que se abre conforme baja (verso 1 todo teléfono → unísono limpio) y su eco que se achica
if 'nave' in seco:
    u = curva_t([[0, 1], [19, 1], [27, .85], [36, .7], [43, .5], [48, .3], [52, 0], [60, 0]], n)
    seco['nave'] = telefono(seco['nave'], u)
    mezcla_eco = curva_t([[0, .35], [36, .3], [44, .15], [52, 0], [60, 0]], n)[:, None]
    seco['nave'] = seco['nave'] * (1 - mezcla_eco) + eco(seco['nave'], T * 3 / 8) * mezcla_eco
    pan = curva_t([[0, .35], [44, .25], [52, 0], [60, 0]], n)            # de la derecha al centro
    seco['nave'] = np.stack([seco['nave'][:, 0] * (1 - pan), seco['nave'][:, 1] * (1 + pan) / (1 + pan.max())], 1)
if 'tierra' in seco:
    pan = curva_t([[0, -.15], [44, -.1], [52, 0], [60, 0]], n)
    seco['tierra'] = np.stack([seco['tierra'][:, 0] * (1 - pan) / (1 - pan.min()), seco['tierra'][:, 1] * (1 + pan)], 1)
# costura: el bombo empuja al bajo, a la portadora y a la pared (hasta 4.5 dB)
if 'bombo' in seco:
    e = envolvente(seco['bombo']); e = e / (e.max() + 1e-9); duck = db(-4.5 * e)[:, None]
    for p in ('bajo', 'portadora', 'pared'):
        if p in seco: seco[p] = seco[p] * duck

suma = sum(seco.values())
envio = sum(seco[p] * SALA[p] for p in seco)
ir = sala_afinada()
humedo = np.stack([fftconvolve(envio[:, c], ir[:, c])[:n] for c in range(2)], 1)
mezcla = suma + humedo * .35

# edad: cinta (wow de 0.55 Hz, ±0.9 ms), piso de ruido afinado en La, agudos gastados
t = np.arange(n) / SR
retraso = (.0012 + .0009 * np.sin(2 * np.pi * .55 * t) + .0003 * np.sin(2 * np.pi * 3.1 * t)) * SR
idx = np.clip(np.arange(n) - retraso, 0, n - 1)
mezcla = np.stack([np.interp(idx, np.arange(n), mezcla[:, c]) for c in range(2)], 1)
rng = np.random.default_rng(7)
piso = rng.standard_normal((n, 2))
piso = sum(banda(piso, 55 * k * .995, 55 * k * 1.005, 2) / k for k in (2, 3, 4, 6, 8, 12)) * db(-46)
mezcla = banda(mezcla + piso, None, 13500, 2)
mezcla = np.tanh(mezcla * .9) / .9                                         # un techo suave antes del loudnorm

# medidas: balance por bandas y por sección (APRENDIDO §5: dos veces salió sepultada en sub)
SECCIONES = [('niebla', 0, 8), ('verso 1', 8, 20), ('coro', 20, 28), ('puente', 28, 36), ('verso 2', 36, 48),
             ('coro final', 48, 56), ('la misma', 56, 60)]
BANDAS = [('sub', None, 90), ('graves', 90, 300), ('medios', 300, 2000), ('presencia', 2000, 6000), ('aire', 6000, None)]
med = {}
bandas = {nb: banda(mezcla, lo, hi) for nb, lo, hi in BANDAS}
rms = lambda v: 10 * np.log10(np.mean(v ** 2) + 1e-12)
for ns, b0, b1 in SECCIONES:
    a, b = int(b0 * T * SR), int(b1 * T * SR); tot = rms(mezcla[a:b])
    med[ns] = {'total_dB': round(tot, 1), **{nb: round(rms(bandas[nb][a:b]) - tot, 1) for nb, _, _ in BANDAS}}
    med[ns]['voz_sobre_resto_dB'] = round(rms(sum(seco[p] for p in ('tierra', 'nave', 'una') if p in seco)[a:b]) -
                                          rms(sum(seco[p] for p in seco if p not in ('tierra', 'nave', 'una'))[a:b]), 1)
for ns, m in med.items(): print(f'{ns:11s}', {k: float(v) for k, v in m.items()})
# cada mezcla es una versión nueva (nunca encima): render/<et>-mezcla-v<k>.wav y sus medidas
k = 1
while (RENDER / f'{ET}-mezcla-v{k}.wav').exists(): k += 1
VER = f'{ET}-mezcla-v{k}'
with open(RENDER / f'{VER}.wav', 'xb') as fh:
    wavfile.write(fh, SR, (mezcla / max(1, np.abs(mezcla).max()) * .98).astype(np.float32))
with open(RENDER / f'{VER}-medidas.json', 'x', encoding='utf-8') as fh:
    json.dump({'niveles_dB': NIVEL, 'sala': SALA, 'secciones': med}, fh, ensure_ascii=False, indent=1)
print('mezcla', VER)

if ENTREGAR:
    nonce = os.urandom(16).hex(); h = hashlib.sha256()
    for f in [AQUI / 'motor' / 'cancion.js', Path(__file__)] + [RENDER / f'{ET}-{p}.wav' for p in sorted(pistas)]: h.update(f.read_bytes())
    h.update(nonce.encode()); ID = h.hexdigest(); C = ID[:12]
    m4a = AQUI / f'la-misma-garganta-{C}.m4a'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-i', str(RENDER / f'{VER}.wav'),
                    '-af', 'loudnorm=I=-14:TP=-1.2:LRA=9', '-ar', '48000', '-c:a', 'aac', '-b:a', '192k', str(m4a)], check=True)
    sha = lambda q: hashlib.sha256(Path(q).read_bytes()).hexdigest()
    with open(AQUI / 'proceso' / f'receta-{C}.json', 'x', encoding='utf-8') as fh:
        json.dump({'id': ID, 'nonce': nonce, 'etiqueta': ET, 'mezcla': VER, 'niveles_dB': NIVEL, 'sala': SALA, 'medidas': med,
                   'pistas_sha256': {p: sha(RENDER / f'{ET}-{p}.wav') for p in sorted(pistas)},
                   'cancion_js_sha256': sha(AQUI / 'motor' / 'cancion.js'), 'm4a': {m4a.name: sha(m4a)}}, fh, ensure_ascii=False, indent=1)
    print('entregado', m4a.name)
