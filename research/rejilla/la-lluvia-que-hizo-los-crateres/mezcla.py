"""La lluvia que hizo los cráteres — mezcla.

Lee los cráteres (render_node.cjs: una capa por familia de tamaño y el gran impacto), la garganta del kiai y el viento; la batería
del footwork (render_web.cjs: TR-808 y frita); la señal de la sonda (render_tt.py) y las voces (render_voz.cjs: susurro, chops, coro,
voz final). Sintetiza aquí el polvo que cae (granos) y el sub 808; arma los vocoders (Sabina modula al sinte del coral y a los
tambores medianos: los cráteres dicen la letra). Los tambores van secos y al frente; sidechain de 20 % en los bombos de los complejos;
reverb sembrada para el cielo; loudnorm −11 LUFS. Mide por grupo contra lo demás y por bandas en cada sección.
    python mezcla.py <carpeta-de-render> [--medir]
"""
import datetime, hashlib, json, math, os, subprocess, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve, butter, sosfiltfilt, sosfilt
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'cuento-en-siete')); import sintes as SN
RUN = sys.argv[1]; SR = 48000
P = json.load(open(os.path.join(RUN, 'partitura.json'), encoding='utf-8'))
N = int(P['duracion'] * SR); SECS = {s['num']: (s['t'], s['t1']) for s in P['secciones']}
T = np.arange(N) / SR

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
def polvo(curva, semilla=0):
    """el polvo que cae: granos de 2–12 ms (ruido agudo filtrado) con densidad que sigue la curva; de vez en cuando, una piedrita"""
    rng = np.random.default_rng(semilla); dens = np.interp(T, [a for a, _ in curva], [b for _, b in curva]); y = np.zeros((N, 2))
    gr = np.nonzero(rng.random(N) < dens * 400 / SR)[0]
    for i in gr:
        L = int(rng.uniform(.002, .012) * SR)
        if i + L >= N: break
        g = rng.standard_normal(L) * np.hanning(L) * rng.uniform(.2, 1); p = rng.uniform(-1, 1)
        y[i:i + L, 0] += g * (1 - p) * .5; y[i:i + L, 1] += g * (1 + p) * .5
    y = sosfilt(butter(2, [1800, 9000], 'band', fs=SR, output='sos'), y, axis=0)
    for i in np.nonzero(rng.random(N) < dens * 3 / SR)[0]:
        L = int(.04 * SR)
        if i + L < N: y[i:i + L] += (np.sin(2 * math.pi * rng.uniform(180, 600) * np.arange(L) / SR) * np.exp(-np.arange(L) / (.006 * SR)))[:, None] * .5
    return y

capas = {}
for f in ('complejo', 'mediano', 'chico', 'diminuto', 'grande'): capas['crater-' + f] = leer('crater-' + f, True)
for c in ('bateria', 'bateria-frito', 'viento'): capas[c] = leer(c, True)
capas['garganta'] = panear(leer('garganta', False), 0); capas['sonda'] = leer('sonda', True)
capas['susurro'] = leer('sabina-susurro', True); capas['chops'] = leer('sabina-chops', True); capas['viva'] = leer('sabina-viva', True)
print('polvo y vocoders…', flush=True)
capas['polvo'] = polvo(P['polvo'], 1)
capas['sub'] = panear(SN.sub808(P['sub'], N), 0)
cor = leer('sabina-coro', True); mod = mono(cor); ven = ventana([(e['t'] - .05, e['t'] + e['dur'] + .3) for e in P['sabina'][2]['eventos']])
capas['voc-sinte'] = ancho(SN.vocoder(mod, SN.sinte_coro(P['coros'], N, 4), consonantes=.4), 0, 13)
capas['voc-tambor'] = ancho(SN.vocoder(mod, mono(capas['crater-mediano'] + capas['crater-chico']) * ven, consonantes=.3), .25, 19)   # los cráteres dicen la letra
capas['coro'] = cor * ven[:, None] * .6
# r1 (medido por grupo): las voces quedaban −9 a −10.5 en el footwork (+4) y el viento tapaba al taiko en III (cielo +0.8 contra cráteres −1.6): −4
NIVEL = {'crater-complejo': -2, 'crater-mediano': -5, 'crater-chico': -8, 'crater-diminuto': -10, 'crater-grande': 2, 'bateria': -12, 'bateria-frito': -9, 'sub': -6,
         'viento': -16, 'garganta': -5, 'sonda': -9, 'polvo': -16, 'susurro': -3, 'chops': -2, 'viva': -1, 'voc-sinte': 0, 'voc-tambor': -2, 'coro': -6}
medidas = {}
for c, x in capas.items():
    a = activo(x); medidas[c] = dict(activo_db=round(20 * math.log10(a + 1e-12), 1)); assert a > 1e-7, f'la capa {c} está muda'
    capas[c] = x * (10 ** ((-20 + NIVEL[c]) / 20) / a)
FILTROS = {'sub': ('lowpass', 120), 'susurro': ('highpass', 200), 'chops': ('highpass', 180), 'viva': ('highpass', 150), 'voc-sinte': ('highpass', 130), 'voc-tambor': ('highpass', 110),
           'coro': ('highpass', 160), 'crater-diminuto': ('highpass', 150)}
for c, (tipo, fc) in FILTROS.items(): capas[c] = filtro(capas[c], tipo, fc)
duck = np.ones(N)                                                       # sidechain: los bombos (los complejos en el footwork) agachan lo demás 20 %
for g in P['golpes']['complejo']:
    i = int(g['t'] * SR); L = min(int(.22 * SR), N - i); duck[i:i + L] = np.minimum(duck[i:i + L], 1 - .2 * np.exp(-np.arange(L) / (.07 * SR)))
SIN_DUCK = {'crater-complejo', 'crater-grande', 'bateria', 'bateria-frito', 'sub', 'garganta', 'susurro', 'chops', 'viva'}
rg = np.random.default_rng(P['semilla']); L = int(3.2 * SR); ir = rg.standard_normal((L, 2)) * np.exp(-np.arange(L) / SR * 1.8)[:, None]; ir[:int(.03 * SR)] = 0; ir /= np.sqrt((ir ** 2).sum(0))
ENVIO = {'crater-complejo': .12, 'crater-grande': .3, 'viento': .3, 'garganta': .35, 'sonda': .45, 'polvo': .2, 'susurro': .25, 'viva': .35, 'voc-sinte': .25, 'voc-tambor': .25, 'coro': .3}
seco = np.zeros((N, 2)); envio = np.zeros((N, 2))
for c, x in capas.items():
    x = x if c in SIN_DUCK else x * duck[:, None]; seco += x
    if c in ENVIO: envio += x * ENVIO[c]
pre = seco + np.stack([fftconvolve(envio[:, k], ir[:, k])[:N] for k in range(2)], 1) * .5
GRUPOS = dict(crateres=['crater-complejo', 'crater-mediano', 'crater-chico', 'crater-diminuto', 'crater-grande'], footwork=['bateria', 'bateria-frito', 'sub'],
              voces=['susurro', 'chops', 'viva', 'voc-sinte', 'voc-tambor', 'coro'], cielo=['viento', 'garganta', 'sonda', 'polvo'])
grupos = {}
for k, (a, z) in SECS.items():
    i, j = int(a * SR), int(z * SR); tot = pre[i:j]; fila = {}
    for g, cs in GRUPOS.items():
        x = sum((capas[c] if c in SIN_DUCK else capas[c] * duck[:, None])[i:j] for c in cs); ex, er = np.mean(x ** 2), np.mean((tot - x) ** 2)
        if ex > 1e-10: fila[g] = round(10 * math.log10(ex / (er + 1e-14)), 1)
    grupos[k] = fila
if '--medir' in sys.argv:
    [print(f'  {k:4}', '  '.join(f'{g} {v:+.1f}' for g, v in fl.items())) for k, fl in grupos.items()]; sys.exit()
mezcla = pre / np.abs(pre).max(); mezcla = np.tanh(1.6 * mezcla) / np.tanh(1.6)
wav = os.path.join(RUN, 'mezcla.wav'); wavfile.write(wav, SR, (mezcla * .95).astype(np.float32))
codigo = b''.join(open(os.path.join(AQUI, f), 'rb').read() for f in ('partitura.py', 'mezcla.py', 'render_node.cjs', 'render_web.cjs', 'render_voz.cjs', 'render_tt.py', 'motor/crater.js'))
nonce = os.urandom(16).hex(); run = hashlib.sha256(mezcla.astype(np.float32).tobytes() + json.dumps(P).encode() + codigo + nonce.encode()).hexdigest(); h = run[:12]
nombre = f'la-lluvia-que-hizo-los-crateres-s{P["semilla"]}-{h}'; out = os.path.join(AQUI, nombre); os.makedirs(out, exist_ok=False); base = os.path.join(out, nombre)
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
              niveles=NIVEL, envios=ENVIO, filtros=FILTROS, secciones_rms_db=secciones, lufs_integrado=lufs, bandas_hz=BANDAS, bandas_por_seccion_db=por_banda,
              grupos_contra_resto_db=grupos, capas=medidas, m4a_sha256=hashlib.sha256(open(base + '.m4a', 'rb').read()).hexdigest(),
              wav_sha256=hashlib.sha256(open(base + '.wav', 'rb').read()).hexdigest(), render=os.path.relpath(RUN, AQUI).replace('\\', '/'))
with open(os.path.join(out, 'receta.json'), 'x', encoding='utf-8') as fo: json.dump(receta, fo, ensure_ascii=False, indent=1)
with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as fo: json.dump(P, fo, ensure_ascii=False)
print(out); print('secciones (rms dB):', secciones, '· LUFS', lufs)
[print(f'  {k:4}', '  '.join(f'{g} {v:+.1f}' for g, v in fl.items())) for k, fl in grupos.items()]
for k, v in por_banda.items(): print(f'  {k:4}', ' '.join(f'{x:6.1f}' for x in v))
