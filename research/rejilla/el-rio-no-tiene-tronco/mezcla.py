"""El río no tiene tronco — mezcla.

Lee las capas de render_web.cjs (marimba de los afluentes, batería del delta), render_node.cjs (garganta de río, voz de agua,
agua, aves, tabla, trombón, tam-tam) y render_voz.cjs (Sabina); sintetiza aquí el arpa (el río y los cinco brazos), el armonio,
la tambura, el bajo, el 808 y el mar de Scelsi; arma los vocoders (Sabina modula al arpa, al armonio y al sinte del coral) y mezcla
con sidechain sólo en el delta, tartamudeo glitch al final de cada ocho tiempos del delta, reverb que crece hacia el mar,
loudnorm −12 LUFS. Mide por grupo y por banda, sección por sección. Entrega en carpeta nueva: el-rio-no-tiene-tronco-s412601-<hash>/.
    python mezcla.py <carpeta-de-render>
"""
import datetime, hashlib, json, math, os, subprocess, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve, resample_poly, butter, sosfiltfilt
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'cuento-en-siete')); sys.path.insert(0, os.path.join(AQUI, '..', 'lo-que-tapa-la-traspuesta'))
import sintes as SN, sintes2 as S2, sintes3 as S3
RUN = sys.argv[1]; SR = 48000
P = json.load(open(os.path.join(RUN, 'partitura.json'), encoding='utf-8'))
N = int(P['duracion'] * SR); SECS = {k: tuple(v) for k, v in P['secciones'].items()}; TT = P['tiempos']

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
for c in ['marimba', 'bateria', 'bateria-frito']: capas[c] = leer(c, True)
for c, p in [('vozagua', -.4), ('agua', -.25), ('aves', .5), ('tabla', -.2), ('trombon', .1), ('gong', 0)]: capas[c] = panear(leer(c, False), p)
for c in ['garganta-coro', 'garganta-mar']: capas[c] = leer(c, True)
sab = {c: leer('sabina-' + c, True) for c in ('soprano', 'mar')}

print('sintes…', flush=True)
capas['arpa-rio'] = ancho(S3.arpa([n for n in P['arpa'] if n['voz'] in ('rio', 'glis')], N, 1), -.1, 9)
delta = np.zeros((N, 2))
for i, b in enumerate(P['delta']['brazos']): delta += panear(S3.arpa([n for n in P['arpa'] if n['voz'] == f'brazo{i}'], N, 10 + i), b['pan'])
capas['arpa-delta'] = delta
capas['armonio'] = ancho(S3.armonio(P['armonio'], N, 2), .1, 15)
capas['tambura'] = ancho(S3.tambura(P['tambura'], N, 3), -.2, 7)
capas['bajo'] = panear(S2.mono(P['bajo'], N, 'fretless', 4), 0)
sub = SN.sub808(P['sub'], N); capas['sub'] = np.stack([sub, sub], 1) * math.sqrt(.5)
sucio = filtro(np.tanh(5 * sub), 'bandpass', (110, 320)); capas['808-sucio'] = np.stack([sucio, sucio], 1) * math.sqrt(.5)
capas['mar'] = S3.mar(P['mar'], N, 5)

print('vocoders…', flush=True)
mod = mono(sab['soprano']) + .8 * mono(sab['mar'])
voces = {v: sum((C[v] for C in P['coros'].values()), []) for v in 'SATB'}
coros = ventana([(e['t'] - .05, e['t'] + e['dur'] + .3) for C in P['coros'].values() for e in C['S']])
capas['voc-sinte'] = ancho(SN.vocoder(mod, SN.sinte_coro(voces, N, 6), consonantes=.4), 0, 13)
capas['voc-arpa'] = ancho(SN.vocoder(mod, mono(capas['arpa-rio'] + capas['arpa-delta']) * coros, suaviza=1, consonantes=.25), .2, 9)   # el arpa dice la letra
capas['voc-armonio'] = ancho(SN.vocoder(mod, mono(capas['armonio']) * coros, consonantes=.2), -.2, 17)
capas['sabina'] = sab['soprano'] + .7 * sab['mar']

# v2 (medido por grupo en la v1): los afluentes de Reich quedaban −13.8 dB bajo el río y el canon del delta bajo el coro; el delta
# con sub de más (20–60 Hz −8 dB del total): afluentes +5, canon +3, sub −3, 808 sucio +2
NIVEL = {'marimba': -3, 'bateria': -6, 'bateria-frito': -9, 'vozagua': -4, 'agua': -10, 'aves': -12, 'tabla': -7, 'trombon': -8, 'gong': -10,
         'garganta-coro': -4, 'garganta-mar': -5, 'arpa-rio': -3, 'arpa-delta': 0, 'armonio': -9, 'tambura': -10, 'bajo': -6, 'sub': -11, '808-sucio': -11,
         'mar': -3, 'voc-sinte': -3, 'voc-arpa': -4, 'voc-armonio': -6, 'sabina': -7}
medidas = {}
def activo(x):
    n = len(x) // 2400 * 2400; m = np.sqrt(np.mean(x[:n].reshape(-1, 2400, 2) ** 2, axis=(1, 2)))
    v = m[m > m.max() * .03]; return float(np.sqrt(np.mean(v ** 2))) if len(v) else 0.0
for c, x in capas.items():
    a = activo(x); medidas[c] = dict(activo_db=round(20 * math.log10(a + 1e-12), 1)); assert a > 1e-7, f'la capa {c} está muda'
    capas[c] = x * (10 ** ((-20 + NIVEL[c]) / 20) / a)
FILTROS = {'sub': ('lowpass', 80, 4), 'bajo': ('highpass', 35, 2), 'marimba': ('highpass', 150, 2), 'arpa-delta': ('highpass', 90, 2), 'voc-sinte': ('highpass', 110, 2),
           'voc-arpa': ('highpass', 130, 2), 'voc-armonio': ('highpass', 110, 2), 'vozagua': ('highpass', 150, 2), 'sabina': ('highpass', 160, 2), 'aves': ('highpass', 400, 2),
           'garganta-coro': ('highpass', 80, 2), 'tabla': ('highpass', 70, 2)}
for c, (tipo, fc, o) in FILTROS.items(): capas[c] = filtro(capas[c], tipo, fc, o)

# sidechain sólo en el delta (hyperpop)
duck = np.ones(N)
for e in P['web']['bateria']:
    if e.get('pieza') != 'kick': continue
    i = int(e['t'] * SR); L = min(int(.3 * SR), N - i); duck[i:i + L] = np.minimum(duck[i:i + L], 1 - .45 * np.exp(-np.arange(L) / (.1 * SR)))
SIN_DUCK = {'bateria', 'bateria-frito', 'sub', '808-sucio', 'mar', 'garganta-mar', 'trombon', 'gong'}
# reverb sembrada: la sala crece hacia el mar (el envío sube después del ápice)
rg = np.random.default_rng(P['semilla']); L = int(3.2 * SR); ir = rg.standard_normal((L, 2)) * np.exp(-np.arange(L) / SR * 1.9)[:, None]; ir[:int(.02 * SR)] = 0; ir /= np.sqrt((ir ** 2).sum(0))
ENVIO = {'arpa-rio': .2, 'arpa-delta': .25, 'armonio': .2, 'tambura': .15, 'marimba': .12, 'agua': .3, 'aves': .4, 'vozagua': .3, 'garganta-coro': .25, 'garganta-mar': .5,
         'mar': .45, 'trombon': .4, 'gong': .5, 'voc-sinte': .18, 'voc-arpa': .25, 'voc-armonio': .3, 'sabina': .3, 'tabla': .1}
crece = 1 + 1.2 * np.clip((np.arange(N) / SR - TT['apice']) / (TT['mar'] - TT['apice']), 0, 1)[:, None]
seco = np.zeros((N, 2)); envio = np.zeros((N, 2))
for c, x in capas.items():
    x = (x if c in SIN_DUCK else x * duck[:, None]) if c not in ('sub', '808-sucio') else x; seco += x
    if c in ENVIO: envio += x * ENVIO[c]
reverb = np.stack([fftconvolve((envio * crece)[:, k], ir[:, k])[:N] for k in range(2)], 1)
pre = seco + reverb * .5
mezcla = pre / np.abs(pre).max(); mezcla = np.tanh(1.7 * mezcla) / np.tanh(1.7)
S16 = P['semicorchea']
for t0 in P['glitch']:                                   # el delta tartamudea: la última semicorchea repetida y cada vez más aguda
    corte = mezcla[int((t0 - S16) * SR):int(t0 * SR)].copy()
    for j in range(2):
        z = resample_poly(corte, 4, 4 + j, axis=0) if j else corte; i = int((t0 + j * S16) * SR); n = min(len(z), int(S16 * SR), N - i); mezcla[i:i + n] = z[:n] * (1 - .1 * j)
wav = os.path.join(RUN, 'mezcla.wav'); wavfile.write(wav, SR, (mezcla * .95).astype(np.float32))

codigo = b''.join(open(os.path.join(AQUI, f), 'rb').read() for f in ('partitura.py', 'sintes3.py', 'mezcla.py', 'render_node.cjs', 'render_web.cjs', 'render_voz.cjs', 'motor/garganta_rio.js'))
nonce = os.urandom(16).hex(); run = hashlib.sha256(mezcla.astype(np.float32).tobytes() + json.dumps(P).encode() + codigo + nonce.encode()).hexdigest(); h = run[:12]
nombre = f'el-rio-no-tiene-tronco-s{P["semilla"]}-{h}'; out = os.path.join(AQUI, nombre); os.makedirs(out, exist_ok=False); base = os.path.join(out, nombre)
subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', wav, '-af', 'loudnorm=I=-12:TP=-1:LRA=12', '-ar', str(SR), '-c:a', 'pcm_s16le', base + '.wav'], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', base + '.wav', '-c:a', 'aac', '-b:a', '192k', base + '.m4a'], check=True)
_, fin = wavfile.read(base + '.wav'); fin = fin.astype(float) / 32768
secciones = {k: round(20 * math.log10(np.sqrt(np.mean(fin[int(a * SR):int(z * SR)] ** 2)) + 1e-12), 1) for k, (a, z) in SECS.items()}
BANDAS = [(20, 60), (60, 120), (120, 250), (250, 500), (500, 1000), (1000, 2000), (2000, 4000), (4000, 8000), (8000, 16000)]
def bandas(x):
    X = np.abs(np.fft.rfft(x.mean(1))) ** 2; fr = np.fft.rfftfreq(len(x), 1 / SR); tot = X.sum()
    return [round(10 * math.log10(X[(fr >= a) & (fr < b)].sum() / tot + 1e-12), 1) for a, b in BANDAS]
por_banda = {k: bandas(fin[int(a * SR):int(z * SR)]) for k, (a, z) in SECS.items()}
GRUPOS = dict(rio=['arpa-rio', 'armonio', 'tambura', 'bajo'], afluentes=['marimba'], coro=['voc-sinte', 'voc-arpa', 'voc-armonio', 'vozagua', 'garganta-coro', 'sabina'],
              delta=['arpa-delta'], ritmo=['bateria', 'bateria-frito', 'sub', '808-sucio', 'tabla'], mar=['mar', 'garganta-mar', 'trombon', 'gong'], ambiente=['agua', 'aves'])
grupos = {}
for k, (a, z) in SECS.items():
    i, j = int(a * SR), int(z * SR); tot = pre[i:j]; fila = {}
    for g, cs in GRUPOS.items():
        x = sum((capas[c] if c in SIN_DUCK or c in ('sub', '808-sucio') else capas[c] * duck[:, None])[i:j] for c in cs); ex, er = np.mean(x ** 2), np.mean((tot - x) ** 2)
        if ex > 1e-10: fila[g] = round(10 * math.log10(ex / (er + 1e-14)), 1)
    grupos[k] = fila
lufs = subprocess.run(['ffmpeg', '-i', base + '.wav', '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True, errors='replace').stderr
lufs = float([l for l in lufs.splitlines() if l.strip().startswith('I:')][-1].split()[1])
receta = dict(titulo=P['titulo'], semilla=P['semilla'], terreno=P['terreno'], ejecucion=run, nonce=nonce, fecha=datetime.date.today().isoformat(), instrumentos=P['instrumentos'],
              niveles=NIVEL, envios=ENVIO, filtros=FILTROS, secciones_rms_db=secciones, lufs_integrado=lufs, bandas_hz=BANDAS, bandas_por_seccion_db=por_banda,
              grupos_contra_resto_db=grupos, capas=medidas, m4a_sha256=hashlib.sha256(open(base + '.m4a', 'rb').read()).hexdigest(),
              wav_sha256=hashlib.sha256(open(base + '.wav', 'rb').read()).hexdigest(), render=os.path.relpath(RUN, AQUI).replace('\\', '/'))
with open(os.path.join(out, 'receta.json'), 'x', encoding='utf-8') as fo: json.dump(receta, fo, ensure_ascii=False, indent=1)
with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as fo: json.dump(P, fo, ensure_ascii=False)
print(out); print('secciones (rms dB):', secciones, '· LUFS', lufs)
for k, fl in grupos.items(): print(f'  {k:4} grupo contra el resto:', '  '.join(f'{g} {v:+.1f}' for g, v in fl.items()))
for k, v in por_banda.items(): print(f'  {k:4}', ' '.join(f'{x:6.1f}' for x in v))
