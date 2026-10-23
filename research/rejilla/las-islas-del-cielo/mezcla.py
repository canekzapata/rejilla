"""Las islas del cielo — mezcla.

Lee las arpas (la meseta y una por isla, cada isla en su lugar del estéreo, el de su mesa), el cuatro (node); las cascadas, los
capachos, el tuki, la lluvia y la campana (Python); la 909 (navegador) y las voces de Sabina (lead, coro, chops, una voz por isla).
Arma el sub y dos vocoders: las voces de las islas modulan A LAS CASCADAS (IV: el agua canta los dialectos) y el coro modula A LA
CAMPANA (I y V: el cuerpo común). Sidechain del bombo; una sala y una reverb larga de niebla; loudnorm −14 LUFS. Procesa capa por
capa (poca memoria libre) y mide cada grupo contra lo demás en cada sección.
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
PAN = {f'isla{i}': isla['pan'] for i, isla in enumerate(P['islas'])}

def panear(y, p): a = (p + 1) * math.pi / 4; return np.stack([y * math.cos(a), y * math.sin(a)], 1).astype(np.float32)
def leer(nombre, estereo):
    x = np.fromfile(os.path.join(RUN, nombre + '.f32'), dtype=np.float32)
    x = x.reshape(-1, 2) if estereo else x
    out = np.zeros((N, 2) if estereo else N, np.float32); out[:min(N, len(x))] = x[:N]; return out
def ancho(y, p=0.0, ms=11): d = int(ms / 1000 * SR); r = np.concatenate([np.zeros(d), y[:-d]]); return (np.stack([y * (1 - .3 * p), r * (1 + .3 * p)], 1) * .7).astype(np.float32)
def filtro(x, tipo, fc, orden=2): return sosfiltfilt(butter(orden, fc, btype=tipo, fs=SR, output='sos'), x, axis=0).astype(np.float32)
def mono(x): return x.mean(1) if x.ndim == 2 else x
def ventana(tramos):
    w = np.zeros(N)
    for a, z in tramos: w[int(a * SR):int(z * SR)] = 1
    k = int(.08 * SR); return np.convolve(w, np.ones(k) / k, 'same').astype(np.float32)
def activo(x):
    n = len(x) // 2400 * 2400; m = np.sqrt(np.mean(x[:n].reshape(-1, 2400, 2).astype(float) ** 2, axis=(1, 2)))
    v = m[m > m.max() * .03]; return float(np.sqrt(np.mean(v ** 2))) if len(v) else 0.0

# r2: coro −9 en I (+3). r1 (medido por grupo): las tres arpas tapaban en III (+2.1), voces −11 en III y −8 en IV (+4), aves −21 (+7), changa −9 en IV (+2), cascadas −4.8 en IV (−2)
NIVEL = {'arpa-meseta': -4, 'arpa-isla0': -9, 'arpa-isla1': -9, 'arpa-isla2': -9, 'cuatro': -8, 'capachos': -13,
         'bateria': -4, 'tuki': -8, 'sub': -6, 'campana': -9, 'cascadas': -8, 'lluvia': -14, 'aves0': -5, 'aves1': -6,
         'lead': 2, 'coro': 0, 'chops': -3, 'isla0': 1, 'isla1': 1, 'isla2': 1, 'voc-cascadas': -2, 'voc-campana': -5}
FILTROS = {'sub': ('lowpass', 140), 'lead': ('highpass', 140), 'coro': ('highpass', 160), 'chops': ('highpass', 250), 'isla0': ('highpass', 150), 'isla1': ('highpass', 150),
           'isla2': ('highpass', 150), 'voc-cascadas': ('highpass', 120), 'voc-campana': ('highpass', 100), 'aves0': ('highpass', 400), 'aves1': ('highpass', 400), 'capachos': ('highpass', 1500)}
SIN_DUCK = {'bateria', 'sub', 'lead', 'tuki'}
SALA = {'arpa-meseta': .25, 'arpa-isla0': .25, 'arpa-isla1': .25, 'arpa-isla2': .25, 'cuatro': .12, 'lead': .2, 'coro': .3, 'chops': .3, 'isla0': .3, 'isla1': .3, 'isla2': .3,
        'aves0': .3, 'aves1': .3, 'campana': .2, 'voc-campana': .3}
NIEBLA = {'cascadas': .5, 'lluvia': .4, 'voc-cascadas': .45, 'campana': .3}
GRUPOS = dict(arpas=['arpa-meseta', 'arpa-isla0', 'arpa-isla1', 'arpa-isla2'], joropo=['cuatro', 'capachos'], changa=['bateria', 'tuki', 'sub'], campana=['campana', 'voc-campana'],
              agua=['cascadas', 'lluvia', 'voc-cascadas'], aves=['aves0', 'aves1'], voces=['lead', 'coro', 'chops', 'isla0', 'isla1', 'isla2'])
GRUPO_DE = {c: g for g, cs in GRUPOS.items() for c in cs}
duck = np.ones(N, np.float32)
for e in P['web']['bateria']:
    if e.get('pieza') != 'kick': continue
    i = int(e['t'] * SR); L = min(int(.2 * SR), N - i); duck[i:i + L] = np.minimum(duck[i:i + L], 1 - .28 * np.exp(-np.arange(L) / (.06 * SR)))
vc = ventana([(e['t'] - .05, e['t'] + e['dur'] + .3) for e in P['sabina'][1]['eventos']])
ruido = lambda k: 1e-4 * np.random.default_rng(k).standard_normal(N).astype(np.float32)

def capa(c):
    if c.startswith('arpa-'): return panear(leer(c, False), PAN.get(c[5:], 0.0))
    if c == 'cuatro': return panear(leer('cuatro', False), .2)
    if c in ('aves0', 'aves1'): return ancho(leer(c, False), -.3 if c == 'aves0' else .4, 17 if c == 'aves0' else 23)
    if c in ('lead', 'chops'): return leer('sabina-' + c, True)
    if c in PAN: return leer('sabina-' + c, True)
    if c == 'coro': return (leer('sabina-coro', True) * vc[:, None] * .7).astype(np.float32)
    if c == 'sub': return panear(SN.sub808(P['sub'], N), 0)
    if c == 'voc-cascadas':
        print('vocoder cascadas…', flush=True); mod = sum(mono(leer('sabina-' + k, True)) for k in PAN)
        return ancho(SN.vocoder(mod, mono(leer('cascadas', True)) + ruido(1), consonantes=.35), .1, 17)
    if c == 'voc-campana':
        print('vocoder campana…', flush=True); mod = mono(leer('sabina-coro', True))
        return ancho(SN.vocoder(mod, mono(leer('campana', True)) + ruido(2), consonantes=.35), -.2, 13)
    return leer(c, True)

seco = np.zeros((N, 2), np.float32); e1 = np.zeros((N, 2), np.float32); e2 = np.zeros((N, 2), np.float32)
GS = {g: np.zeros((N, 2), np.float32) for g in GRUPOS}; medidas = {}
for c in NIVEL:
    x = capa(c); a = activo(x); medidas[c] = dict(activo_db=round(20 * math.log10(a + 1e-12), 1)); assert a > 1e-7, f'la capa {c} está muda'
    x = (x * (10 ** ((-20 + NIVEL[c]) / 20) / a)).astype(np.float32)
    if c in FILTROS: x = filtro(x, *FILTROS[c])
    if c not in SIN_DUCK: x *= duck[:, None]
    seco += x; GS[GRUPO_DE[c]] += x
    if c in SALA: e1 += x * SALA[c]
    if c in NIEBLA: e2 += x * NIEBLA[c]
    del x; print(' ', c, medidas[c]['activo_db'], flush=True)
rg = np.random.default_rng(P['semilla'])
def ir(seg, dec, oscura=False):
    L = int(seg * SR); x = rg.standard_normal((L, 2)) * np.exp(-np.arange(L) / SR * dec)[:, None]; x[:int(.02 * SR)] = 0
    if oscura: x = sosfiltfilt(butter(2, 3500, 'low', fs=SR, output='sos'), x, axis=0)
    return x / np.sqrt((x ** 2).sum(0))
IR_SALA, IR_NIEBLA = ir(2.4, 2.6), ir(6.0, .9, True)
pre = seco
for env_, irr, g in ((e1, IR_SALA, .4), (e2, IR_NIEBLA, .5)):
    for k in range(2): pre[:, k] += (fftconvolve(env_[:, k], irr[:, k])[:N] * g).astype(np.float32)
del e1, e2
grupos = {}
for k, (a, z) in SECS.items():
    i, j = int(a * SR), int(z * SR); tot = pre[i:j]; fila = {}
    for g in GRUPOS:
        x = GS[g][i:j]; ex, er = np.mean(x.astype(float) ** 2), np.mean((tot - x).astype(float) ** 2)
        if ex > 1e-10: fila[g] = round(10 * math.log10(ex / (er + 1e-14)), 1)
    grupos[k] = fila
del GS
if '--medir' in sys.argv:
    [print(f'  {k:4}', '  '.join(f'{g} {v:+.1f}' for g, v in fl.items())) for k, fl in grupos.items()]; sys.exit()
mezcla = pre / np.abs(pre).max(); mezcla = np.tanh(1.5 * mezcla) / np.tanh(1.5)
wav = os.path.join(RUN, 'mezcla.wav'); wavfile.write(wav, SR, (mezcla * .95).astype(np.float32))
CODIGO = ('partitura.py', 'sintes9.py', 'mezcla.py', 'render_py.py', 'render_node.cjs', 'render_web.cjs', 'render_voz.cjs', 'motor/cuerda.js')
codigo = b''.join(open(os.path.join(AQUI, f), 'rb').read() for f in CODIGO)
nonce = os.urandom(16).hex(); run = hashlib.sha256(mezcla.astype(np.float32).tobytes() + json.dumps(P).encode() + codigo + nonce.encode()).hexdigest(); h = run[:12]
nombre = f'las-islas-del-cielo-s{P["semilla"]}-{h}'; out = os.path.join(AQUI, nombre); os.makedirs(out, exist_ok=False); base = os.path.join(out, nombre)
subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', wav, '-af', 'loudnorm=I=-14:TP=-1:LRA=12', '-ar', str(SR), '-c:a', 'pcm_s16le', base + '.wav'], check=True)
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
              niveles=NIVEL, sala=SALA, niebla=NIEBLA, filtros=FILTROS, secciones_rms_db=secciones, lufs_integrado=lufs, bandas_hz=BANDAS, bandas_por_seccion_db=por_banda,
              grupos_contra_resto_db=grupos, capas=medidas, m4a_sha256=hashlib.sha256(open(base + '.m4a', 'rb').read()).hexdigest(),
              wav_sha256=hashlib.sha256(open(base + '.wav', 'rb').read()).hexdigest(), render=os.path.relpath(RUN, AQUI).replace('\\', '/'))
with open(os.path.join(out, 'receta.json'), 'x', encoding='utf-8') as fo: json.dump(receta, fo, ensure_ascii=False, indent=1)
with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as fo: json.dump(P, fo, ensure_ascii=False)
print(out); print('secciones (rms dB):', secciones, '· LUFS', lufs)
[print(f'  {k:4}', '  '.join(f'{g} {v:+.1f}' for g, v in fl.items())) for k, fl in grupos.items()]
for k, v in por_banda.items(): print(f'  {k:4}', ' '.join(f'{x:6.1f}' for x in v))
