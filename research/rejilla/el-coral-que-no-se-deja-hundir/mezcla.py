"""El coral que no se deja hundir — mezcla.

Lee las capas de Python (olas, coral y sus clics, volcán, pájaros de boca, laguna, luciérnagas), de node (fragatas, burbujas), del
navegador (exotica y hyperpop) y de Sabina. Además:
  · EL TAPETE DE TALBOT sobre el collar en III: un ciclo de congas de II (dos compases) pasa por τ = 1/2, 1/3, 1/4 (exacto: 2, 3 y 4
    copias corridas; en 1/3 caen en 1/6, 3/6 y 5/6 del ciclo: el tresillo se adelanta solo) y vuelve a τ = 0.
  · LOS VOCODERS cambian de cuerpo en el cruce: el coro modula AL VOLCÁN hasta el cruce y AL CORAL después (2 s de fundido).
  · LA LUZ: el coral sube desde lo hondo; un pasa bajos lo va abriendo (de 500 Hz a 9 kHz) hasta que llega a la superficie en IV.
  · LA EXOTICA OSCURA: vibráfono, marimba y steel pan con pasa bajos y un poco de saturación (grave y con filo).
Sidechain del bombo 808 en IV; dos reverbs (la sala tropical y una oscura, bajo el agua); loudnorm −14 LUFS.
Mide por grupo contra lo demás en cada sección.
    python mezcla.py <carpeta-de-render> [--medir]
"""
import datetime, hashlib, json, math, os, subprocess, sys
from fractions import Fraction
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve, butter, sosfiltfilt, sosfilt
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'cuento-en-siete')); import sintes as SN
sys.path.insert(0, os.path.join(AQUI, '..', 'tapete-de-talbot')); import tapete as TP
RUN = sys.argv[1]; SR = 48000
P = json.load(open(os.path.join(RUN, 'partitura.json'), encoding='utf-8'))
N = int(P['duracion'] * SR); SECS = {s['num']: (s['t'], s['t1']) for s in P['secciones']}

def panear(y, p): a = (p + 1) * math.pi / 4; return np.stack([y * math.cos(a), y * math.sin(a)], 1).astype(np.float32)
def leer(nombre, estereo):
    x = np.fromfile(os.path.join(RUN, nombre + '.f32'), dtype=np.float32)
    x = x.reshape(-1, 2) if estereo else x
    out = np.zeros((N, 2) if estereo else N, np.float32); out[:min(N, len(x))] = x[:N]; return out
def ancho(y, p=0.0, ms=11): d = int(ms / 1000 * SR); r = np.concatenate([np.zeros(d), y[:-d]]); return (np.stack([y * (1 - .3 * p), r * (1 + .3 * p)], 1) * .7).astype(np.float32)
def filtro(x, tipo, fc, orden=2): return sosfiltfilt(butter(orden, fc, btype=tipo, fs=SR, output='sos'), x, axis=0).astype(np.float32)
def mono(x): return x.mean(1) if x.ndim == 2 else x
def curva(c): t = np.arange(N) / SR; return np.interp(t, [a for a, _ in c], [b for _, b in c])
def ventana(tramos):
    w = np.zeros(N)
    for a, z in tramos: w[int(a * SR):int(z * SR)] = 1
    k = int(.08 * SR); return np.convolve(w, np.ones(k) / k, 'same')
def activo(x):
    n = len(x) // 2400 * 2400; m = np.sqrt(np.mean(x[:n].reshape(-1, 2400, 2) ** 2, axis=(1, 2)))
    v = m[m > m.max() * .03]; return float(np.sqrt(np.mean(v ** 2))) if len(v) else 0.0
def pasabajos_variable(x, fc_t, B=2048):
    out = np.zeros_like(x); zi = np.zeros((1, 2, x.shape[1]))
    for i in range(0, len(x), B):
        j = min(len(x), i + B); sos = butter(2, float(fc_t[(i + j) // 2]), 'low', fs=SR, output='sos')
        out[i:j], zi = sosfilt(sos, x[i:j], axis=0, zi=zi)
    return out

# Se procesa capa por capa (la máquina tiene poca memoria libre): cada capa se lee, se trata, se nivela y se suma a su grupo y a los
# envíos; sólo quedan en memoria las sumas por grupo, la seca y los dos envíos.
# r1 (medido por grupo): voces −9 a −11 en I, II, IV y V (+3 a +4), aves −21 a −23 (+6), luz −16 (+6), olas/burbujas abajo (+2); exotica fuerte en II (−1)
NIVEL = {'volcan': -4, 'coral': -5, 'coral-clics': -16, 'olas': -8, 'burbujas': -11, 'laguna': -12, 'luciernagas': -6,
         'congas': -7, 'guiro': -14, 'shaker': -17, 'vibrafono': -11, 'marimba': -10, 'steelpan': -13, 'teponaztli': -12,
         'bateria808': -6, 'bateria-frito': -12, 'sub': -6, 'aves0': -8, 'aves1': -9, 'boca': -8,
         'lead': 1.5, 'coro': -3, 'chops': -3, 'voc-volcan': -1, 'voc-coral': -1}
FILTROS = {'sub': ('lowpass', 140), 'lead': ('highpass', 140), 'coro': ('highpass', 160), 'chops': ('highpass', 250), 'voc-volcan': ('highpass', 90),
           'voc-coral': ('highpass', 110), 'aves0': ('highpass', 400), 'aves1': ('highpass', 400), 'boca': ('highpass', 180), 'shaker': ('highpass', 2000), 'laguna': ('lowpass', 900)}
SIN_DUCK = {'bateria808', 'bateria-frito', 'sub', 'lead', 'volcan'}
ENVIO = {'lead': .2, 'coro': .3, 'chops': .3, 'voc-volcan': .25, 'voc-coral': .3, 'vibrafono': .3, 'marimba': .15, 'steelpan': .3, 'aves0': .35, 'aves1': .35, 'boca': .3,
         'congas': .12, 'luciernagas': .4, 'teponaztli': .25}
AGUA = {'volcan': .35, 'burbujas': .5, 'coral': .35, 'laguna': .4, 'olas': .2}
GRUPOS = dict(volcan=['volcan'], coral=['coral', 'coral-clics', 'laguna'], agua=['olas', 'burbujas'], exotica=['vibrafono', 'marimba', 'steelpan', 'teponaztli', 'congas', 'guiro', 'shaker'],
              hyperpop=['bateria808', 'bateria-frito', 'sub'], aves=['aves0', 'aves1', 'boca'], voces=['lead', 'coro', 'chops', 'voc-volcan', 'voc-coral'], luz=['luciernagas'])
GRUPO_DE = {c: g for g, cs in GRUPOS.items() for c in cs}
duck = np.ones(N, np.float32)
for e in P['web']['bateria808']:
    if e.get('pieza') != 'kick': continue
    i = int(e['t'] * SR); L = min(int(.2 * SR), N - i); duck[i:i + L] = np.minimum(duck[i:i + L], 1 - .3 * np.exp(-np.arange(L) / (.06 * SR)))
fc_coral = np.exp(curva([[0, math.log(500)], [SECS['III'][0], math.log(1400)], [SECS['IV'][0], math.log(9000)], [P['duracion'], math.log(9000)]]))
vc = ventana([(e['t'] - .05, e['t'] + e['dur'] + .3) for e in P['sabina'][1]['eventos']])
w_v = np.clip((P['cruce'] + 1 - np.arange(N) / SR) / 2, 0, 1).astype(np.float32)      # el volcán es la portadora hasta el cruce
mcor = mono(leer('sabina-coro', True))
talbot_info = {}


def capa(c):
    """lee y trata una capa (antes de nivelar)."""
    if c == 'volcan': return panear(leer('volcan', False), 0)
    if c in ('aves0', 'aves1'): return ancho(leer(c, False), -.3 if c == 'aves0' else .4, 17 if c == 'aves0' else 23)
    if c in ('lead', 'chops'): return leer('sabina-' + c, True)
    if c == 'coro': return (leer('sabina-coro', True) * vc[:, None] * .6).astype(np.float32)
    if c == 'sub': return panear(SN.sub808(P['sub'], N), 0)
    if c == 'voc-volcan':
        print('vocoder volcán…', flush=True); car = leer('volcan', False) + 1e-4 * np.random.default_rng(1).standard_normal(N).astype(np.float32)
        return ancho(SN.vocoder(mcor * w_v, car, consonantes=.35), -.2, 19)
    if c == 'voc-coral':
        print('vocoder coral…', flush=True); car = mono(leer('coral', True)) + 1e-4 * np.random.default_rng(2).standard_normal(N).astype(np.float32)
        return ancho(SN.vocoder(mcor * (1 - w_v), car, consonantes=.35), .2, 13)
    x = leer(c, True)
    if c == 'congas':                                                               # el tapete de Talbot sobre el collar (III)
        T = P['talbot']; Lp = int(round(T['ciclo'] * SR)); i0 = int(round(T['loop_desde'] * SR)); loop = x[i0:i0 + Lp].astype(float)
        tramos = T['tramos']; a3 = SECS['III'][0]; xf = int(.05 * SR); w = np.ones(N, np.float32)
        a, b = int(SECS['III'][0] * SR), int(tramos[-1][0] * SR); w[a:b] = 0; w[a - xf:a] = np.linspace(1, 0, xf); w[b:b + xf] = np.linspace(0, 1, xf); x = x * w[:, None]
        for (ta, tau), (tz, _) in zip(tramos, tramos[1:]):
            if tau == '0': continue
            z = TP.talbot(loop, Fraction(tau)); a, b = int(ta * SR), min(N, int(tz * SR))
            idx = (np.arange(a, b) - int(round(a3 * SR))) % Lp; ww = np.ones(b - a); ww[:xf] = np.linspace(0, 1, xf); ww[-xf:] = np.linspace(1, 0, xf)
            x[a:b] += (z[idx] * ww[:, None]).astype(np.float32); talbot_info[tau] = TP.copias(Fraction(tau).numerator, Fraction(tau).denominator)[0]
        return x
    if c in ('coral', 'coral-clics'): return pasabajos_variable(x, fc_coral).astype(np.float32)        # la luz: el coral sube desde lo hondo
    if c in ('vibrafono', 'marimba', 'steelpan'):                                                       # la exotica oscura
        fc = {'vibrafono': 2200, 'marimba': 1800, 'steelpan': 2600}[c]
        return (np.tanh(2.2 * filtro(x, 'lowpass', fc) / (np.abs(x).max() + 1e-12)) / math.tanh(2.2)).astype(np.float32)
    return x


seco = np.zeros((N, 2), np.float32); e1 = np.zeros((N, 2), np.float32); e2 = np.zeros((N, 2), np.float32)
GS = {g: np.zeros((N, 2), np.float32) for g in GRUPOS}; medidas = {}
for c in NIVEL:
    x = capa(c); a = activo(x); medidas[c] = dict(activo_db=round(20 * math.log10(a + 1e-12), 1)); assert a > 1e-7, f'la capa {c} está muda'
    x = (x * (10 ** ((-20 + NIVEL[c]) / 20) / a)).astype(np.float32)
    if c in FILTROS: x = filtro(x, *FILTROS[c])
    if c not in SIN_DUCK: x *= duck[:, None]
    seco += x; GS[GRUPO_DE[c]] += x
    if c in ENVIO: e1 += x * ENVIO[c]
    if c in AGUA: e2 += x * AGUA[c]
    del x; print(' ', c, medidas[c]['activo_db'], flush=True)
rg = np.random.default_rng(P['semilla'])


def ir(seg, dec, oscura=False):
    L = int(seg * SR); x = rg.standard_normal((L, 2)) * np.exp(-np.arange(L) / SR * dec)[:, None]; x[:int(.02 * SR)] = 0
    if oscura: x = filtro(x, 'lowpass', 900)
    return x / np.sqrt((x ** 2).sum(0))


IR_SALA, IR_AGUA = ir(2.8, 2.2), ir(4.0, 1.4, True)
pre = seco
for env_, irr, g in ((e1, IR_SALA, .45), (e2, IR_AGUA, .5)):
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
CODIGO = ('partitura.py', 'sintes8.py', 'mezcla.py', 'render_py.py', 'render_node.cjs', 'render_web.cjs', 'render_voz.cjs', 'motor/cueva.js')
codigo = b''.join(open(os.path.join(AQUI, f), 'rb').read() for f in CODIGO)
nonce = os.urandom(16).hex(); run = hashlib.sha256(mezcla.astype(np.float32).tobytes() + json.dumps(P).encode() + codigo + nonce.encode()).hexdigest(); h = run[:12]
nombre = f'el-coral-que-no-se-deja-hundir-s{P["semilla"]}-{h}'; out = os.path.join(AQUI, nombre); os.makedirs(out, exist_ok=False); base = os.path.join(out, nombre)
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
              niveles=NIVEL, envios=ENVIO, envios_agua=AGUA, filtros=FILTROS, talbot_copias=talbot_info, secciones_rms_db=secciones, lufs_integrado=lufs, bandas_hz=BANDAS,
              bandas_por_seccion_db=por_banda, grupos_contra_resto_db=grupos, capas=medidas, m4a_sha256=hashlib.sha256(open(base + '.m4a', 'rb').read()).hexdigest(),
              wav_sha256=hashlib.sha256(open(base + '.wav', 'rb').read()).hexdigest(), render=os.path.relpath(RUN, AQUI).replace('\\', '/'))
with open(os.path.join(out, 'receta.json'), 'x', encoding='utf-8') as fo: json.dump(receta, fo, ensure_ascii=False, indent=1)
with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as fo: json.dump(P, fo, ensure_ascii=False)
print(out); print('secciones (rms dB):', secciones, '· LUFS', lufs)
[print(f'  {k:4}', '  '.join(f'{g} {v:+.1f}' for g, v in fl.items())) for k, fl in grupos.items()]
for k, v in por_banda.items(): print(f'  {k:4}', ' '.join(f'{x:6.1f}' for x in v))
