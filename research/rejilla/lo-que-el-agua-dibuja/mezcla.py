"""Lo que el agua dibuja — mezcla. 23 capas en cinco grupos:

  guitarra  la guitarra de cárcava (el slide que camina el perfil) y el pulgar (el bajo monótono del Delta)
  lluvia    la lluvia de Xenakis en sus tres toques (pizz, arco, col legno), los truenos y el viento seco
  crecida   el rugido de la crecida, los pedregones del arrastre y EL RÍO QUE CANTA: un vocoder cuya portadora es la crecida misma
            y cuya moduladora es Sabina cantando «lo que el agua dibuja» (sólo en V, en la boca)
  drill     los hi-hats de la 808 con los redobles primos, el bombo y la tarola de la TR-808, las palmas fritas, el 808 que se
            desliza y su sub
  voces     el blues (lead y su doble), las tres voces de la respuesta, el rap, los chops y un coro sintético

Procesa capa por capa (los grupos van a disco, la memoria es poca) y mide cada grupo contra lo demás en cada sección.
loudnorm −14 LUFS.
    python mezcla.py <carpeta-de-render> [--medir]
"""
import datetime, hashlib, json, math, os, subprocess, sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
from scipy.io import wavfile
from scipy.signal import oaconvolve, butter, sosfiltfilt
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(AQUI, '..', 'cuento-en-siete')); import sintes as SN
RUN = sys.argv[1]; SR = 48000
P = json.load(open(os.path.join(RUN, 'partitura.json'), encoding='utf-8'))
N = int(P['duracion'] * SR); SECS = {s['num']: (s['t'], s['t1']) for s in P['secciones']}

def panear(y, p): a = (p + 1) * math.pi / 4; return np.stack([y * math.cos(a), y * math.sin(a)], 1).astype(np.float32)
def leer(nombre, estereo):
    x = np.fromfile(os.path.join(RUN, nombre + '.f32'), dtype=np.float32)
    x = x.reshape(-1, 2) if estereo else x
    out = np.zeros((N, 2) if estereo else N, np.float32); out[:min(N, len(x))] = x[:N]; return out
def filtro(x, tipo, fc, orden=2): return sosfiltfilt(butter(orden, fc, btype=tipo, fs=SR, output='sos'), x, axis=0).astype(np.float32)
def mono(x): return x.mean(1) if x.ndim == 2 else x
def activo(x):
    n = len(x) // 2400 * 2400; m = np.sqrt(np.mean(x[:n].reshape(-1, 2400, 2).astype(float) ** 2, axis=(1, 2)))
    v = m[m > m.max() * .03]; return float(np.sqrt(np.mean(v ** 2))) if len(v) else 0.0

CAPAS = ['guitarra', 'pulgar', 'lluvia', 'arco', 'col-legno', 'trueno', 'viento', 'crecida', 'pedregones', 'rio',
         'hats', 'bateria808', 'bateria-frito', 'bajo808', 'sub', 'lead', 'doble', 'respuesta', 'respuesta3', 'respuesta8', 'rap', 'chops', 'pad']
# r1 (medido por grupo): en las tormentas la guitarra tapaba la lluvia (+5.8 contra −6.4 en t1); la crecida en la boca −11; el rap −1.
#     → la guitarra baja 7–8 dB SÓLO en las tormentas (AUTOMATA), la lluvia +3, la crecida +4, el río +3, el rap +3, la guitarra +2; el lead y la respuesta +1 (III y IV quedaban en −2).
NIVEL = {'guitarra': 2, 'pulgar': -8, 'lluvia': -3, 'arco': -6, 'col-legno': -7, 'trueno': -2, 'viento': -14, 'crecida': -6, 'pedregones': -11, 'rio': -2,
         'hats': -12, 'bateria808': -4, 'bateria-frito': -11, 'bajo808': -3, 'sub': -9, 'lead': 4, 'doble': -5, 'respuesta': 1, 'respuesta3': -3, 'respuesta8': -4,
         'rap': 6, 'chops': -4, 'pad': -15}
AUTOMATA = {'guitarra': {'t1': -7, 't2': -7, 't3': -8}}                                            # dB por sección, con fundidos de 0.6 s
def automata(c):
    g = np.zeros(N, np.float32)
    for k, db in AUTOMATA.get(c, {}).items(): a, z = SECS[k]; g[int(a * SR):int(z * SR)] = db
    k = int(.6 * SR); g = oaconvolve(g, np.ones(k, np.float32) / k, mode='same'); return (10 ** (g / 20)).astype(np.float32)
FILTROS = {'sub': ('lowpass', 110), 'lead': ('highpass', 140), 'doble': ('highpass', 110), 'respuesta': ('highpass', 160), 'respuesta3': ('highpass', 150),
           'respuesta8': ('highpass', 120), 'rap': ('highpass', 130), 'chops': ('highpass', 300), 'pad': ('lowpass', 2500), 'viento': ('highpass', 150), 'pulgar': ('lowpass', 1800)}
SIN_DUCK = {'bateria808', 'bajo808', 'sub', 'lead', 'rap', 'trueno'}
SALA = {'guitarra': .22, 'lead': .25, 'doble': .2, 'respuesta': .35, 'respuesta3': .35, 'respuesta8': .3, 'arco': .4, 'lluvia': .3, 'col-legno': .3, 'trueno': .45,
        'chops': .25, 'rio': .35, 'pad': .3, 'rap': .08}
GRUPOS = dict(guitarra=['guitarra', 'pulgar'], lluvia=['lluvia', 'arco', 'col-legno', 'trueno', 'viento'], crecida=['crecida', 'pedregones', 'rio'],
              drill=['hats', 'bateria808', 'bateria-frito', 'bajo808', 'sub'], voces=['lead', 'doble', 'respuesta', 'respuesta3', 'respuesta8', 'rap', 'chops', 'pad'])
GRUPO_DE = {c: g for g, cs in GRUPOS.items() for c in cs}
duck = np.ones(N, np.float32)
for e in P['web']['bateria808']:
    if e.get('pieza') != 'kick': continue
    i = int(e['t'] * SR); L = min(int(.2 * SR), N - i); duck[i:i + L] = np.minimum(duck[i:i + L], 1 - .25 * np.exp(-np.arange(L) / (.06 * SR)))
rio_info = {}

def capa(c):
    if c in ('guitarra', 'pulgar', 'lluvia', 'arco', 'col-legno', 'trueno', 'viento', 'crecida', 'pedregones', 'hats', 'bateria808', 'bateria-frito'): return leer(c, True)
    if c == 'bajo808': return panear(leer('bajo808', False), 0)
    if c == 'sub': return panear(np.tanh(2 * filtro(leer('bajo808', False), 'lowpass', 80)), 0)
    if c in ('lead', 'doble', 'respuesta', 'respuesta3', 'respuesta8', 'rap', 'chops'):
        x = leer('sabina-' + c, True)
        if c in ('respuesta3', 'respuesta8'): x = panear(mono(x), -.45 if c == 'respuesta3' else .45)
        return x
    if c == 'pad': return panear(SN.sinte_coro(P['coros'], N, 5).astype(np.float32), 0)
    if c == 'rio':                                                                                    # el río canta: vocoder con la crecida de portadora
        a = int((SECS['V'][0] - 1) * SR); mod = mono(leer('sabina-rio', True))[a:]; car = mono(leer('crecida', True))[a:]
        car = car + .15 * filtro(np.random.default_rng(2).standard_normal(len(car)).astype(np.float32), 'highpass', 3000) * np.abs(car).max()   # aire para las consonantes
        y = SN.vocoder(mod.astype(float), car.astype(float)); rio_info['tramo_s'] = [round(a / SR, 2), P['duracion']]
        out = np.zeros(N, np.float32); out[a:a + len(y)] = y[:N - a]; return panear(out, 0)
    raise KeyError(c)

seco = np.zeros((N, 2), np.float32); e1 = np.zeros((N, 2), np.float32)
GS = {g: np.lib.format.open_memmap(os.path.join(RUN, f'grupo-{g}.npy'), 'w+', np.float32, (N, 2)) for g in GRUPOS}; medidas = {}
for c in CAPAS:
    x = capa(c); a = activo(x); medidas[c] = dict(activo_db=round(20 * math.log10(a + 1e-12), 1)); assert a > 1e-7, f'la capa {c} está muda'
    x = (x * (10 ** ((-20 + NIVEL[c]) / 20) / a)).astype(np.float32)
    if c in FILTROS: x = filtro(x, *FILTROS[c])
    if c in AUTOMATA: x *= automata(c)[:, None]
    if c not in SIN_DUCK: x *= duck[:, None]
    GS[GRUPO_DE[c]][:] += x; seco += x
    if c in SALA: e1 += x * SALA[c]
    del x; print(' ', c, medidas[c]['activo_db'], flush=True)
wfin = np.ones(N, np.float32); fz = int((P['duracion'] - 4) * SR); wfin[fz:] = np.linspace(1, 0, N - fz) ** 1.5
seco *= wfin[:, None]; e1 *= wfin[:, None]
rg = np.random.default_rng(P['semilla'])
L = int(2.6 * SR); ir = rg.standard_normal((L, 2)) * np.exp(-np.arange(L) / SR * 2.4)[:, None]; ir[:int(.02 * SR)] = 0; ir /= np.sqrt((ir ** 2).sum(0))
pre = seco
for k in range(2): pre[:, k] += (oaconvolve(e1[:, k], ir[:, k].astype(np.float32))[:N] * .4).astype(np.float32)
del e1
grupos = {}
for k, (a, z) in list(SECS.items()) + [('final', (P['duracion'] - 7, P['duracion']))]:
    i, j = int(a * SR), int(z * SR); tot = pre[i:j]; fila = {}
    for g in GRUPOS:
        x = GS[g][i:j] * wfin[i:j, None]; ex, er = np.mean(x.astype(float) ** 2), np.mean((tot - x).astype(float) ** 2)
        if ex > 1e-10: fila[g] = round(10 * math.log10(ex / (er + 1e-14)), 1)
    grupos[k] = fila
for g in list(GS): del GS[g]
for g in GRUPOS: os.remove(os.path.join(RUN, f'grupo-{g}.npy'))
if '--medir' in sys.argv:
    [print(f'  {k:6}', '  '.join(f'{g} {v:+.1f}' for g, v in fl.items())) for k, fl in grupos.items()]; sys.exit()
mezcla = pre / np.abs(pre).max(); mezcla = np.tanh(1.5 * mezcla) / np.tanh(1.5)
wav = os.path.join(RUN, 'mezcla.wav'); wavfile.write(wav, SR, (mezcla * .95).astype(np.float32))
CODIGO = ('partitura.py', 'sintes11.py', 'motor/carcava.js', 'mezcla.py', 'render_py.py', 'render_node.cjs', 'render_web.cjs', 'render_voz.cjs')
codigo = b''.join(open(os.path.join(AQUI, f), 'rb').read() for f in CODIGO)
nonce = os.urandom(16).hex(); run = hashlib.sha256(mezcla.astype(np.float32).tobytes() + json.dumps(P).encode() + codigo + nonce.encode()).hexdigest(); h = run[:12]
nombre = f'lo-que-el-agua-dibuja-s{P["semilla"]}-{h}'; parent = os.path.abspath(os.path.join(AQUI, '../../../salidas')); os.makedirs(parent, exist_ok=True); out = os.path.join(parent, nombre); os.makedirs(out, exist_ok=False); base = os.path.join(out, nombre)
del mezcla, pre, seco
subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', wav, '-af', 'loudnorm=I=-14:TP=-1:LRA=12', '-ar', str(SR), '-c:a', 'pcm_s16le', base + '.wav'], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', base + '.wav', '-c:a', 'aac', '-b:a', '192k', base + '.m4a'], check=True)
_, fin = wavfile.read(base + '.wav'); fin = fin.astype(np.float32) / 32768
secciones = {k: round(20 * math.log10(np.sqrt(np.mean(fin[int(a * SR):int(z * SR)].astype(float) ** 2)) + 1e-12), 1) for k, (a, z) in SECS.items()}
BANDAS = [(20, 60), (60, 120), (120, 250), (250, 500), (500, 1000), (1000, 2000), (2000, 4000), (4000, 8000), (8000, 16000)]
def bandas(x):
    X = np.abs(np.fft.rfft(x.mean(1))) ** 2; fr = np.fft.rfftfreq(len(x), 1 / SR); tot = X.sum()
    return [round(10 * math.log10(X[(fr >= a) & (fr < b)].sum() / tot + 1e-12), 1) for a, b in BANDAS]
por_banda = {k: bandas(fin[int(a * SR):int(z * SR)]) for k, (a, z) in SECS.items()}
lufs = subprocess.run(['ffmpeg', '-i', base + '.wav', '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True, errors='replace').stderr
lufs = float([l for l in lufs.splitlines() if l.strip().startswith('I:')][-1].split()[1])
receta = dict(titulo=P['titulo'], semilla=P['semilla'], terreno=P['terreno'], ejecucion=run, nonce=nonce, fecha=datetime.date.today().isoformat(), instrumentos=P['instrumentos'],
              niveles=NIVEL, automata=AUTOMATA, sala=SALA, filtros=FILTROS, rio=rio_info, secciones_rms_db=secciones, lufs_integrado=lufs, bandas_hz=BANDAS, bandas_por_seccion_db=por_banda,
              grupos_contra_resto_db=grupos, capas=medidas, m4a_sha256=hashlib.sha256(open(base + '.m4a', 'rb').read()).hexdigest(),
              wav_sha256=hashlib.sha256(open(base + '.wav', 'rb').read()).hexdigest(), render=os.path.relpath(RUN, AQUI).replace('\\', '/'))
with open(os.path.join(out, 'receta.json'), 'x', encoding='utf-8') as fo: json.dump(receta, fo, ensure_ascii=False, indent=1)
with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as fo: json.dump(P, fo, ensure_ascii=False)
print(out); print('secciones (rms dB):', secciones, '· LUFS', lufs)
[print(f'  {k:6}', '  '.join(f'{g} {v:+.1f}' for g, v in fl.items())) for k, fl in grupos.items()]
for k, v in por_banda.items(): print(f'  {k:5}', ' '.join(f'{x:6.1f}' for x in v))

with open(os.path.join(RUN, 'entrega-mezcla.json'), 'x', encoding='utf-8') as f:
    json.dump(dict(carpeta=out, wav=base+'.wav', m4a=base+'.m4a'),f,ensure_ascii=False)
