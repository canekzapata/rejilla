"""Primero sueño en el cenote — mezcla.

Lee la cueva, el katajjaq, el bordón y las aves (render_node.cjs); los metrónomos, la linterna y el vinilo (render_py.py); el órgano
de divisores, la boca y la sala (render_tt.py); el garage (render_web.cjs) y las voces de Sabina (render_voz.cjs). Arma el sub y los
vocoders: las vocales largas de Sabina modulan A LA CUEVA (la cueva dice las vocales), la soprano modula al sinte del coral y A LA
LINTERNA (la luz dice la letra). Garage seco con sidechain de 25 %; la cueva y las voces con una reverb larga de caverna; loudnorm
−12 LUFS. Mide por grupo contra lo demás y por bandas en cada sección.
    python mezcla.py <carpeta-de-render> [--medir]
"""
import datetime, hashlib, json, math, os, subprocess, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve, butter, sosfiltfilt
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'cuento-en-siete')); import sintes as SN
RUN = sys.argv[1]; SR = 48000
P = json.load(open(os.path.join(RUN, 'partitura.json'), encoding='utf-8'))
N = int(P['duracion'] * SR); SECS = {s['num']: (s['t'], s['t1']) for s in P['secciones']}

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
def activo(x):
    n = len(x) // 2400 * 2400; m = np.sqrt(np.mean(x[:n].reshape(-1, 2400, 2) ** 2, axis=(1, 2)))
    v = m[m > m.max() * .03]; return float(np.sqrt(np.mean(v ** 2))) if len(v) else 0.0

capas = {}
for c in ('cueva', 'metronomos', 'linterna', 'vinilo', 'organo', 'boca', 'sala', 'bateria', 'bateria-frito'): capas[c] = leer(c, True)
capas['katajjaq0'] = panear(leer('katajjaq0', False), -.45); capas['katajjaq1'] = panear(leer('katajjaq1', False), .45)
capas['bordon'] = panear(leer('bordon', False), 0); capas['aves'] = ancho(leer('aves', False), .3, 23)
for c in ('lead', 'chops'): capas[c] = leer('sabina-' + c, True)
print('vocoders…', flush=True)
voc = mono(leer('sabina-vocales', True)); cor = leer('sabina-coro', True); mcor = mono(cor)
vv = ventana([(e['t'] - .05, e['t'] + e['dur'] + .3) for e in P['sabina'][3]['eventos']]); vc = ventana([(e['t'] - .05, e['t'] + e['dur'] + .3) for e in P['sabina'][1]['eventos']])
capas['voc-cueva'] = ancho(SN.vocoder(voc, mono(capas['cueva']) * vv + 1e-4 * np.random.default_rng(1).standard_normal(N), consonantes=.2), -.2, 19)   # la cueva dice las vocales
capas['voc-coro'] = ancho(SN.vocoder(mcor, SN.sinte_coro(P['coros'], N, 5), consonantes=.4), 0, 13)
capas['voc-linterna'] = ancho(SN.vocoder(mcor, mono(capas['linterna']) * vc, consonantes=.3), .2, 17)        # la luz dice la letra
capas['coro'] = cor * vc[:, None] * .5
capas['sub'] = panear(SN.sub808(P['sub'], N), 0)
# r1 (medido por grupo): las voces quedaban −10.6 a −12 en II–IV (chops, coro, vocoders: +3 a +5) y la linterna −18 en III (+2)
NIVEL = {'cueva': -5, 'metronomos': -10, 'linterna': -6, 'vinilo': -18, 'organo': -11, 'boca': -6, 'sala': -12, 'bateria': -6, 'bateria-frito': -11, 'sub': -6,
         'katajjaq0': -6, 'katajjaq1': -6, 'bordon': -11, 'aves': -17, 'lead': -2, 'chops': -3, 'voc-cueva': -1, 'voc-coro': -1, 'voc-linterna': -5, 'coro': -6}
medidas = {}
for c, x in capas.items():
    a = activo(x); medidas[c] = dict(activo_db=round(20 * math.log10(a + 1e-12), 1)); assert a > 1e-7, f'la capa {c} está muda'
    capas[c] = x * (10 ** ((-20 + NIVEL[c]) / 20) / a)
FILTROS = {'sub': ('lowpass', 130), 'lead': ('highpass', 140), 'coro': ('highpass', 160), 'chops': ('highpass', 250), 'voc-cueva': ('highpass', 110), 'voc-coro': ('highpass', 120),
           'voc-linterna': ('highpass', 110), 'aves': ('highpass', 300), 'metronomos': ('highpass', 300), 'bordon': ('highpass', 35)}
for c, (tipo, fc) in FILTROS.items(): capas[c] = filtro(capas[c], tipo, fc)
duck = np.ones(N)
for e in P['web']['bateria']:
    if e.get('pieza') != 'kick': continue
    i = int(e['t'] * SR); L = min(int(.22 * SR), N - i); duck[i:i + L] = np.minimum(duck[i:i + L], 1 - .25 * np.exp(-np.arange(L) / (.07 * SR)))
SIN_DUCK = {'bateria', 'bateria-frito', 'sub', 'lead', 'vinilo', 'metronomos'}
rg = np.random.default_rng(P['semilla']); L = int(5.0 * SR); ir = rg.standard_normal((L, 2)) * np.exp(-np.arange(L) / SR * 1.2)[:, None]; ir[:int(.04 * SR)] = 0; ir /= np.sqrt((ir ** 2).sum(0))   # caverna
ENVIO = {'cueva': .35, 'katajjaq0': .25, 'katajjaq1': .25, 'bordon': .3, 'linterna': .3, 'boca': .3, 'organo': .3, 'lead': .25, 'coro': .35, 'chops': .4, 'voc-cueva': .4,
         'voc-coro': .25, 'voc-linterna': .35, 'aves': .4, 'metronomos': .15}
seco = np.zeros((N, 2)); envio = np.zeros((N, 2))
for c, x in capas.items():
    x = x if c in SIN_DUCK else x * duck[:, None]; seco += x
    if c in ENVIO: envio += x * ENVIO[c]
pre = seco + np.stack([fftconvolve(envio[:, k], ir[:, k])[:N] for k in range(2)], 1) * .5
GRUPOS = dict(cueva=['cueva', 'sala'], reloj=['metronomos'], luz=['linterna'], garage=['bateria', 'bateria-frito', 'sub', 'vinilo'], voces=['lead', 'coro', 'chops', 'voc-cueva', 'voc-coro', 'voc-linterna'],
              cuerpo=['katajjaq0', 'katajjaq1', 'bordon', 'boca'], noche=['organo', 'aves'])
grupos = {}
for k, (a, z) in SECS.items():
    i, j = int(a * SR), int(z * SR); tot = pre[i:j]; fila = {}
    for g, cs in GRUPOS.items():
        x = sum((capas[c] if c in SIN_DUCK else capas[c] * duck[:, None])[i:j] for c in cs); ex, er = np.mean(x ** 2), np.mean((tot - x) ** 2)
        if ex > 1e-10: fila[g] = round(10 * math.log10(ex / (er + 1e-14)), 1)
    grupos[k] = fila
if '--medir' in sys.argv:
    [print(f'  {k:4}', '  '.join(f'{g} {v:+.1f}' for g, v in fl.items())) for k, fl in grupos.items()]; sys.exit()
mezcla = pre / np.abs(pre).max(); mezcla = np.tanh(1.5 * mezcla) / np.tanh(1.5)
wav = os.path.join(RUN, 'mezcla.wav'); wavfile.write(wav, SR, (mezcla * .95).astype(np.float32))
codigo = b''.join(open(os.path.join(AQUI, f), 'rb').read() for f in ('partitura.py', 'sintes7.py', 'mezcla.py', 'render_node.cjs', 'render_web.cjs', 'render_voz.cjs', 'render_py.py', 'render_tt.py', 'motor/cueva.js'))
nonce = os.urandom(16).hex(); run = hashlib.sha256(mezcla.astype(np.float32).tobytes() + json.dumps(P).encode() + codigo + nonce.encode()).hexdigest(); h = run[:12]
nombre = f'primero-sueno-en-el-cenote-s{P["semilla"]}-{h}'; out = os.path.join(AQUI, nombre); os.makedirs(out, exist_ok=False); base = os.path.join(out, nombre)
subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', wav, '-af', 'loudnorm=I=-12:TP=-1:LRA=12', '-ar', str(SR), '-c:a', 'pcm_s16le', base + '.wav'], check=True)
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
              niveles=NIVEL, envios=ENVIO, filtros=FILTROS, secciones_rms_db=secciones, lufs_integrado=lufs, bandas_hz=BANDAS, bandas_por_seccion_db=por_banda,
              grupos_contra_resto_db=grupos, capas=medidas, m4a_sha256=hashlib.sha256(open(base + '.m4a', 'rb').read()).hexdigest(),
              wav_sha256=hashlib.sha256(open(base + '.wav', 'rb').read()).hexdigest(), render=os.path.relpath(RUN, AQUI).replace('\\', '/'))
with open(os.path.join(out, 'receta.json'), 'x', encoding='utf-8') as fo: json.dump(receta, fo, ensure_ascii=False, indent=1)
with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as fo: json.dump(P, fo, ensure_ascii=False)
print(out); print('secciones (rms dB):', secciones, '· LUFS', lufs)
[print(f'  {k:4}', '  '.join(f'{g} {v:+.1f}' for g, v in fl.items())) for k, fl in grupos.items()]
for k, v in por_banda.items(): print(f'  {k:4}', ' '.join(f'{x:6.1f}' for x in v))
