"""¿Por quién se toma la tierra? — mezcla.

Lee las capas de render_web.cjs (vibráfono, krar, masenqo, conga, órgano, batería), render_node.cjs (garganta de volcán y su caldera,
el cuello, los metales, el washint, el tam-tam, los lagos) y render_voz.cjs (Sabina); sintetiza aquí el magma (Scelsi), los estratos
de dub techno con su eco de cinta, el bajo dub y la avalancha; arma los vocoders (Sabina modula al sinte del coral, al órgano y AL
MAGMA: la tierra dice la letra) y mezcla con sidechain de dub techno (30 %), reverb sembrada, loudnorm −11 LUFS. Mide por grupo y por
banda en cada edad del volcán. Entrega en carpeta nueva: por-quien-se-toma-la-tierra-s177-<hash>/.
    python mezcla.py <carpeta-de-render>
"""
import datetime, hashlib, json, math, os, subprocess, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve, resample_poly, butter, sosfiltfilt
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'cuento-en-siete'))
import sintes as SN, sintes4 as S4
RUN = sys.argv[1]; SR = 48000
P = json.load(open(os.path.join(RUN, 'partitura.json'), encoding='utf-8'))
N = int(P['duracion'] * SR)
ED = P['edades']; SECS = {e['nombre']: (e['t'], (ED[k + 1]['t'] if k + 1 < len(ED) else P['fin'])) for k, e in enumerate(ED)}

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
for c in ['vibrafono', 'krar', 'masenqo', 'conga', 'organo', 'bateria', 'bateria-frito']: capas[c] = leer(c, True)
for c, p in [('garganta', .1), ('caldera', 0), ('garganta-cuello', 0), ('sax', -.25), ('trompeta', .3), ('trombon', .05), ('washint', .35), ('tamtam', 0), ('lagos', -.3)]:
    capas[c] = panear(leer(c, False), p)
sab = leer('sabina-soprano', True)

print('sintes…', flush=True)
capas['magma'] = ancho(S4.magma(P['magma'], N, 1), 0, 19)
capas['estratos'] = S4.estratos(P['estratos'], N, P['compas'], 2)
capas['bajo'] = panear(S4.bajo_dub(P['bajo'], N, 3), 0)
capas['avalancha'] = ancho(S4.avalancha(P['colapso']['t0'], P['colapso']['t1'] + 3, N, 4), -.2, 13)

print('vocoders…', flush=True)
mod = mono(sab)
coros = ventana([(e['t'] - .05, e['t'] + e['dur'] + .3) for k in ('verso', 'estribillo', 'estribillo2') for e in P['coros'][k]['S']])
voces = {v: sum((P['coros'][k][v] for k in ('verso', 'estribillo', 'estribillo2')), []) for v in 'SATB'}
capas['voc-sinte'] = ancho(SN.vocoder(mod, SN.sinte_coro(voces, N, 6), consonantes=.4), 0, 13)
capas['voc-organo'] = ancho(SN.vocoder(mod, mono(capas['organo']) * coros, consonantes=.25), -.2, 17)
capas['voc-magma'] = ancho(SN.vocoder(mod, mono(capas['magma']) * coros, consonantes=.2), .2, 23)      # el magma dice la letra
capas['sabina'] = sab

# v2 (medido por grupo en la v1): en el cuello la garganta quedaba −13 dB bajo el magma («sólo la garganta canta» no se cumplía) y el
# coro −5 dB en el groove: garganta del cuello +14 (v2 +8 todavía quedaba −4 bajo el magma), magma −2, vocoders y Sabina +2, la garganta del coro +2
NIVEL = {'vibrafono': -3, 'krar': -7, 'masenqo': -4, 'conga': -9, 'organo': -11, 'bateria': -5, 'bateria-frito': -9, 'garganta': -3, 'caldera': -6, 'garganta-cuello': 12,
         'sax': -5, 'trompeta': -6, 'trombon': -7, 'washint': -5, 'tamtam': -8, 'lagos': -13, 'magma': -8, 'estratos': -6, 'bajo': -5, 'avalancha': -6,
         'voc-sinte': -1, 'voc-organo': -4, 'voc-magma': -3, 'sabina': -6}
medidas = {}
def activo(x):
    n = len(x) // 2400 * 2400; m = np.sqrt(np.mean(x[:n].reshape(-1, 2400, 2) ** 2, axis=(1, 2)))
    v = m[m > m.max() * .03]; return float(np.sqrt(np.mean(v ** 2))) if len(v) else 0.0
for c, x in capas.items():
    a = activo(x); medidas[c] = dict(activo_db=round(20 * math.log10(a + 1e-12), 1)); assert a > 1e-7, f'la capa {c} está muda'
    capas[c] = x * (10 ** ((-20 + NIVEL[c]) / 20) / a)
FILTROS = {'bajo': ('lowpass', 160, 2), 'magma': ('highpass', 30, 2), 'krar': ('highpass', 150, 2), 'conga': ('highpass', 70, 2), 'organo': ('highpass', 120, 2),
           'voc-sinte': ('highpass', 110, 2), 'voc-organo': ('highpass', 110, 2), 'voc-magma': ('highpass', 90, 2), 'sabina': ('highpass', 160, 2), 'estratos': ('highpass', 90, 2),
           'garganta': ('highpass', 60, 2), 'caldera': ('lowpass', 90, 2)}
for c, (tipo, fc, o) in FILTROS.items(): capas[c] = filtro(capas[c], tipo, fc, o)
# sidechain de dub techno: cada bombo agacha lo demás 30 %
duck = np.ones(N)
for e in P['web']['bateria']:
    if e.get('pieza') != 'kick' or e['vel'] < .1: continue
    i = int(e['t'] * SR); L = min(int(.3 * SR), N - i); duck[i:i + L] = np.minimum(duck[i:i + L], 1 - .3 * np.exp(-np.arange(L) / (.1 * SR)))
SIN_DUCK = {'bateria', 'bateria-frito', 'bajo', 'magma', 'caldera', 'avalancha', 'tamtam', 'garganta-cuello'}
rg = np.random.default_rng(P['semilla']); L = int(3.0 * SR); ir = rg.standard_normal((L, 2)) * np.exp(-np.arange(L) / SR * 2.0)[:, None]; ir[:int(.02 * SR)] = 0; ir /= np.sqrt((ir ** 2).sum(0))
ENVIO = {'vibrafono': .2, 'krar': .12, 'masenqo': .3, 'washint': .35, 'sax': .18, 'trompeta': .2, 'trombon': .15, 'organo': .2, 'garganta': .3, 'garganta-cuello': .4,
         'magma': .25, 'tamtam': .4, 'avalancha': .3, 'lagos': .35, 'voc-sinte': .2, 'voc-organo': .25, 'voc-magma': .3, 'sabina': .3, 'conga': .08}
crece = np.ones((N, 1))
seco = np.zeros((N, 2)); envio = np.zeros((N, 2))
for c, x in capas.items():
    x = x if c in SIN_DUCK else x * duck[:, None]; seco += x
    if c in ENVIO: envio += x * ENVIO[c]
reverb = np.stack([fftconvolve((envio * crece)[:, k], ir[:, k])[:N] for k in range(2)], 1)
pre = seco + reverb * .5
mezcla = pre / np.abs(pre).max(); mezcla = np.tanh(1.7 * mezcla) / np.tanh(1.7)
wav = os.path.join(RUN, 'mezcla.wav'); wavfile.write(wav, SR, (mezcla * .95).astype(np.float32))

codigo = b''.join(open(os.path.join(AQUI, f), 'rb').read() for f in ('partitura.py', 'sintes4.py', 'mezcla.py', 'render_node.cjs', 'render_web.cjs', 'render_voz.cjs', 'motor/garganta_volcan.js'))
nonce = os.urandom(16).hex(); run = hashlib.sha256(mezcla.astype(np.float32).tobytes() + json.dumps(P).encode() + codigo + nonce.encode()).hexdigest(); h = run[:12]
nombre = f'por-quien-se-toma-la-tierra-s{P["semilla"]}-{h}'; out = os.path.join(AQUI, nombre); os.makedirs(out, exist_ok=False); base = os.path.join(out, nombre)
subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', wav, '-af', 'loudnorm=I=-11:TP=-1:LRA=11', '-ar', str(SR), '-c:a', 'pcm_s16le', base + '.wav'], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', base + '.wav', '-c:a', 'aac', '-b:a', '192k', base + '.m4a'], check=True)
_, fin = wavfile.read(base + '.wav'); fin = fin.astype(float) / 32768
secciones = {k: round(20 * math.log10(np.sqrt(np.mean(fin[int(a * SR):int(z * SR)] ** 2)) + 1e-12), 1) for k, (a, z) in SECS.items()}
BANDAS = [(20, 60), (60, 120), (120, 250), (250, 500), (500, 1000), (1000, 2000), (2000, 4000), (4000, 8000), (8000, 16000)]
def bandas(x):
    X = np.abs(np.fft.rfft(x.mean(1))) ** 2; fr = np.fft.rfftfreq(len(x), 1 / SR); tot = X.sum()
    return [round(10 * math.log10(X[(fr >= a) & (fr < b)].sum() / tot + 1e-12), 1) for a, b in BANDAS]
por_banda = {k: bandas(fin[int(a * SR):int(z * SR)]) for k, (a, z) in SECS.items()}
GRUPOS = dict(magma=['magma', 'caldera', 'tamtam', 'avalancha'], estratos=['estratos', 'organo'], groove=['bateria', 'bateria-frito', 'conga', 'bajo'],
              mulatu=['krar', 'vibrafono', 'sax', 'trompeta', 'trombon', 'masenqo', 'washint'], coro=['voc-sinte', 'voc-organo', 'voc-magma', 'sabina', 'garganta', 'garganta-cuello'], lagos=['lagos'])
grupos = {}
for k, (a, z) in SECS.items():
    i, j = int(a * SR), int(z * SR); tot = pre[i:j]; fila = {}
    for g, cs in GRUPOS.items():
        x = sum((capas[c] if c in SIN_DUCK else capas[c] * duck[:, None])[i:j] for c in cs); ex, er = np.mean(x ** 2), np.mean((tot - x) ** 2)
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
