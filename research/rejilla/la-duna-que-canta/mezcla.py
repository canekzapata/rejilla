"""La duna que canta — mezcla.

Lee las capas de render_node.cjs (la duna, la segunda duna, la duna que dice la letra, el viento, la garganta de duna, el guembri, la
guitarra del desierto y su solo), render_web.cjs (batería 808, frita, las dos palmas de Clapping Music, el tende) y render_voz.cjs
(Sabina: la llamada y la soprano); sintetiza aquí los qraqeb y el sub 808; arma los vocoders (Sabina modula al sinte del coral y A LA
DUNA: la duna dice la letra) y mezcla: el hyperpop va SECO (la batería, el sub y las palmas no mandan a la reverb), sidechain de 25 %
en cada bombo, reverb sembrada para lo demás. En VI la mezcla de II (el gnawa con su llamada) suena AL REVÉS debajo y no se separa.
loudnorm −11 LUFS. Mide por grupo y por banda en cada sección. Entrega en carpeta nueva: la-duna-que-canta-s675-<hash>/.
    python mezcla.py <carpeta-de-render> [--medir]
"""
import datetime, hashlib, json, math, os, subprocess, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve, butter, sosfiltfilt
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'cuento-en-siete'))
import sintes as SN, sintes5 as S5
RUN = sys.argv[1]; SR = 48000
P = json.load(open(os.path.join(RUN, 'partitura.json'), encoding='utf-8'))
N = int(P['duracion'] * SR)
SC = P['secciones']; SECS = {s['num']: (s['t'], (SC[k + 1]['t'] if k + 1 < len(SC) else P['fin'])) for k, s in enumerate(SC)}

def panear(y, p): a = (p + 1) * math.pi / 4; return np.stack([y * math.cos(a), y * math.sin(a)], 1)
def leer(nombre, estereo):
    x = np.fromfile(os.path.join(RUN, nombre + '.f32'), dtype=np.float32).astype(float)
    x = x.reshape(-1, 2) if estereo else x
    out = np.zeros((N, 2) if estereo else N); out[:min(N, len(x))] = x[:N]; return out
def ancho(y, p=0.0, ms=11): d = int(ms / 1000 * SR); r = np.concatenate([np.zeros(d), y[:-d]]); return np.stack([y * (1 - .3 * p), r * (1 + .3 * p)], 1) * .7
def filtro(x, tipo, fc, orden=2): return sosfiltfilt(butter(orden, fc, btype=tipo, fs=SR, output='sos'), x, axis=0)
def mono(x): return x.mean(1) if x.ndim == 2 else x
def ventana(tramos):
    w = np.zeros(N)
    for a, z in tramos: w[int(a * SR):int(z * SR)] = 1
    k = int(.08 * SR); return np.convolve(w, np.ones(k) / k, 'same')

capas = {}
for c in ['bateria', 'bateria-frito', 'palmas1', 'palmas2', 'tende', 'duna', 'duna2', 'duna-voz', 'viento']: capas[c] = leer(c, True)
for c, p in [('garganta', .15), ('garganta-final', 0), ('guembri', -.2), ('guitarra', .3), ('guitarra-solo', .1)]: capas[c] = panear(leer(c, False), p)
capas['lead'] = leer('sabina-lead', True); sop = leer('sabina-soprano', True)

print('sintes…', flush=True)
capas['qraqeb'] = S5.qraqeb(P['qraqeb'], N, 1)
capas['sub'] = panear(SN.sub808(P['sub'], N), 0)

print('vocoders…', flush=True)
mod = mono(sop); E = P['sabina'][1]['eventos']
coro = ventana([(e['t'] - .05, e['t'] + e['dur'] + .3) for e in E if not e.get('solo_vocoder')])
solo = ventana([(e['t'] - .05, e['t'] + e['dur'] + .3) for e in E if e.get('solo_vocoder')])
capas['voc-sinte'] = ancho(SN.vocoder(mod * coro, SN.sinte_coro(P['coros'], N, 6), consonantes=.4), 0, 13)
capas['voc-duna'] = ancho(SN.vocoder(mod, mono(capas['duna-voz']), consonantes=.3), .2, 19)           # la duna dice la letra
capas['soprano'] = sop * coro[:, None] * .7 + sop * solo[:, None] * .25
del capas['duna-voz']

# r2 (medido por grupo en r1): el siseo de la duna (incoherente) quedaba −39 dB en II, IV y VI — inaudible: la normalización la fija el
# bramido, 24 dB más fuerte —; ahora la duna sube cuando pierde coherencia (abajo). El guembri −11 en el gnawa (+3), la llamada y el
# coro −6 a −10 (+2/+3), el solo nómada −9 en IV (+4), lo que suena al revés +0.9 sobre el vocoder solo de VI (−3)
NIVEL = {'bateria': -5, 'bateria-frito': -8, 'palmas1': -9, 'palmas2': -9, 'tende': -10, 'qraqeb': -10, 'sub': -6,
         'duna': -4, 'duna2': -8, 'viento': -11, 'garganta': -6, 'garganta-final': -1, 'guembri': -1, 'guitarra': -6, 'guitarra-solo': 1,
         'lead': -1, 'voc-sinte': -2, 'voc-duna': 0, 'soprano': -8}
medidas = {}
def activo(x):
    n = len(x) // 2400 * 2400; m = np.sqrt(np.mean(x[:n].reshape(-1, 2400, 2) ** 2, axis=(1, 2)))
    v = m[m > m.max() * .03]; return float(np.sqrt(np.mean(v ** 2))) if len(v) else 0.0
for c, x in capas.items():
    a = activo(x); medidas[c] = dict(activo_db=round(20 * math.log10(a + 1e-12), 1)); assert a > 1e-7, f'la capa {c} está muda'
    capas[c] = x * (10 ** ((-20 + NIVEL[c]) / 20) / a)
# la arena que se mueve: cuando la masa es estadística (r bajo) el siseo sube hasta 16 dB; cuando brama, queda como está
COH = np.array(json.load(open(os.path.join(RUN, 'duna-coherencia.json'))))
COH = np.convolve(COH, np.ones(25) / 25, 'same'); rr = np.interp(np.arange(N) / SR, np.arange(len(COH)) / 100, COH)   # suavizada 1/4 s (a 100 Hz)
capas['duna'] = capas['duna'] * (10 ** (16 * np.clip(1 - rr, 0, 1) / 20))[:, None]
FILTROS = {'sub': ('lowpass', 140, 2), 'guembri': ('highpass', 45, 2), 'guitarra': ('highpass', 110, 2), 'guitarra-solo': ('highpass', 140, 2), 'palmas1': ('highpass', 300, 2),
           'palmas2': ('highpass', 300, 2), 'voc-sinte': ('highpass', 120, 2), 'voc-duna': ('highpass', 100, 2), 'lead': ('highpass', 160, 2), 'soprano': ('highpass', 160, 2),
           'garganta': ('highpass', 70, 2), 'garganta-final': ('highpass', 70, 2), 'viento': ('highpass', 60, 2), 'duna': ('highpass', 28, 2), 'duna2': ('highpass', 28, 2)}
for c, (tipo, fc, o) in FILTROS.items(): capas[c] = filtro(capas[c], tipo, fc, o)
duck = np.ones(N)                                                       # sidechain: cada bombo agacha lo demás 25 %
for e in P['web']['bateria']:
    if e.get('pieza') != 'kick': continue
    i = int(e['t'] * SR); L = min(int(.25 * SR), N - i); duck[i:i + L] = np.minimum(duck[i:i + L], 1 - .25 * np.exp(-np.arange(L) / (.08 * SR)))
SIN_DUCK = {'bateria', 'bateria-frito', 'sub', 'duna', 'duna2', 'palmas1', 'palmas2', 'garganta-final'}
rg = np.random.default_rng(P['semilla']); L = int(3.4 * SR); ir = rg.standard_normal((L, 2)) * np.exp(-np.arange(L) / SR * 1.7)[:, None]; ir[:int(.025 * SR)] = 0; ir /= np.sqrt((ir ** 2).sum(0))
ENVIO = {'duna': .2, 'duna2': .3, 'viento': .2, 'garganta': .35, 'garganta-final': .45, 'guembri': .06, 'guitarra': .15, 'guitarra-solo': .22, 'lead': .25,
         'voc-sinte': .2, 'voc-duna': .3, 'soprano': .3, 'tende': .1, 'qraqeb': .08}   # el hyperpop (batería, sub, palmas) va seco
seco = np.zeros((N, 2)); envio = np.zeros((N, 2))
for c, x in capas.items():
    x = x if c in SIN_DUCK else x * duck[:, None]; seco += x
    if c in ENVIO: envio += x * ENVIO[c]
reverb = np.stack([fftconvolve(envio[:, k], ir[:, k])[:N] for k in range(2)], 1)
pre = seco + reverb * .5
# VI · correr al revés: la mezcla del gnawa (II, con su llamada) suena al revés debajo; la arena negra y la blanca no se separan
(d0, d1), (a0, a1) = P['reves']['de'], P['reves']['a']
seg = pre[int(d0 * SR):int(d1 * SR)][::-1]; n = min(len(seg), int((a1 - a0) * SR) + int(1.5 * SR), N - int(a0 * SR))
env = np.minimum(1, np.minimum(np.arange(n) / (1.2 * SR), (n - np.arange(n)) / (2.0 * SR)))[:, None]
capas['reves'] = np.zeros((N, 2)); capas['reves'][int(a0 * SR):int(a0 * SR) + n] = seg[:n] * env * 10 ** (-9 / 20)
pre = pre + capas['reves']; SIN_DUCK.add('reves')
mezcla = pre / np.abs(pre).max(); mezcla = np.tanh(1.6 * mezcla) / np.tanh(1.6)
wav = os.path.join(RUN, 'mezcla.wav'); wavfile.write(wav, SR, (mezcla * .95).astype(np.float32))

GRUPOS = dict(duna=['duna', 'duna2'], viento=['viento'], cuerdas=['guembri', 'guitarra'], solo=['guitarra-solo'], ritmo=['bateria', 'bateria-frito', 'sub', 'tende', 'qraqeb'],
              palmas=['palmas1', 'palmas2'], llamada=['lead', 'garganta', 'garganta-final'], coro=['voc-sinte', 'voc-duna', 'soprano'], reves=['reves'])
grupos = {}
for k, (a, z) in SECS.items():
    i, j = int(a * SR), int(z * SR); tot = pre[i:j]; fila = {}
    for g, cs in GRUPOS.items():
        x = sum((capas[c] if c in SIN_DUCK else capas[c] * duck[:, None])[i:j] for c in cs); ex, er = np.mean(x ** 2), np.mean((tot - x) ** 2)
        if ex > 1e-10: fila[g] = round(10 * math.log10(ex / (er + 1e-14)), 1)
    grupos[k] = fila
if '--medir' in sys.argv:                                               # borrador: sólo medir, sin entrega
    for k, fl in grupos.items(): print(f'  {k:4} grupo contra el resto:', '  '.join(f'{g} {v:+.1f}' for g, v in fl.items()))
    sys.exit()
codigo = b''.join(open(os.path.join(AQUI, f), 'rb').read() for f in ('partitura.py', 'sintes5.py', 'mezcla.py', 'render_node.cjs', 'render_web.cjs', 'render_voz.cjs',
                                                                        'motor/duna.js', 'motor/cuerda.js', 'motor/garganta_duna.js'))
nonce = os.urandom(16).hex(); run = hashlib.sha256(mezcla.astype(np.float32).tobytes() + json.dumps(P).encode() + codigo + nonce.encode()).hexdigest(); h = run[:12]
nombre = f'la-duna-que-canta-s{P["semilla"]}-{h}'; out = os.path.join(AQUI, nombre); os.makedirs(out, exist_ok=False); base = os.path.join(out, nombre)
subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', wav, '-af', 'loudnorm=I=-11:TP=-1:LRA=11', '-ar', str(SR), '-c:a', 'pcm_s16le', base + '.wav'], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', base + '.wav', '-c:a', 'aac', '-b:a', '192k', base + '.m4a'], check=True)
_, fin = wavfile.read(base + '.wav'); fin = fin.astype(float) / 32768
secciones = {k: round(20 * math.log10(np.sqrt(np.mean(fin[int(a * SR):int(z * SR)] ** 2)) + 1e-12), 1) for k, (a, z) in SECS.items()}
BANDAS = [(20, 60), (60, 120), (120, 250), (250, 500), (500, 1000), (1000, 2000), (2000, 4000), (4000, 8000), (8000, 16000)]
def bandas(x):
    X = np.abs(np.fft.rfft(x.mean(1))) ** 2; fr = np.fft.rfftfreq(len(x), 1 / SR); tot = X.sum()
    return [round(10 * math.log10(X[(fr >= a) & (fr < b)].sum() / tot + 1e-12), 1) for a, b in BANDAS]
por_banda = {k: bandas(fin[int(a * SR):int(z * SR)]) for k, (a, z) in SECS.items()}
lufs = subprocess.run(['ffmpeg', '-i', base + '.wav', '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True, errors='replace').stderr
lufs = float([l for l in lufs.splitlines() if l.strip().startswith('I:')][-1].split()[1])
receta = dict(titulo=P['titulo'], semilla=P['semilla'], terreno=P['terreno'], ejecucion=run, nonce=nonce, fecha=datetime.date.today().isoformat(), instrumentos=P['instrumentos'],
              f0=P['f0'], niveles=NIVEL, envios=ENVIO, filtros=FILTROS, secciones_rms_db=secciones, lufs_integrado=lufs, bandas_hz=BANDAS, bandas_por_seccion_db=por_banda,
              grupos_contra_resto_db=grupos, capas=medidas, m4a_sha256=hashlib.sha256(open(base + '.m4a', 'rb').read()).hexdigest(),
              wav_sha256=hashlib.sha256(open(base + '.wav', 'rb').read()).hexdigest(), render=os.path.relpath(RUN, AQUI).replace('\\', '/'))
with open(os.path.join(out, 'receta.json'), 'x', encoding='utf-8') as fo: json.dump(receta, fo, ensure_ascii=False, indent=1)
with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as fo: json.dump(P, fo, ensure_ascii=False)
print(out); print('secciones (rms dB):', secciones, '· LUFS', lufs)
for k, fl in grupos.items(): print(f'  {k:4} grupo contra el resto:', '  '.join(f'{g} {v:+.1f}' for g, v in fl.items()))
for k, v in por_banda.items(): print(f'  {k:4}', ' '.join(f'{x:6.1f}' for x in v))
