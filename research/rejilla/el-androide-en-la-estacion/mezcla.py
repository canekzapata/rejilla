"""El androide en la estación — mezcla.

Lee las capas de render_tt.py (los instrumentos de tres tiempos), render_web.cjs (TR-808 y batería frita), render_node.cjs (el
traductor que se oxida, el convoy que no sale, el agua) y render_voz.cjs (Sabina: voz de andén y soprano); sintetiza aquí la
estación Sutura (impresora, torniquete, campana, lluvia, la pulsación), las luciérnagas y el sub 808; arma los vocoders (Sabina
modula al sinte del coral, AL CONVOY y al órgano de divisores) y mezcla:
  - la voz de andén pasa por un altavoz de estación (banda de 350 Hz a 3.5 kHz, un poco rota, ecos del andén);
  - el silicio se hunde: el grupo electro pasa por un pasabajas que baja a 500 Hz en el descenso (bajo el agua, Drexciya);
  - sidechain de 25 % en cada bombo; la batería y el sub van secos; reverb sembrada para lo demás; loudnorm −11 LUFS.
Mide por grupo contra lo demás y por bandas en cada sección. Entrega en carpeta nueva: el-androide-en-la-estacion-s2038-<hash>/.
    python mezcla.py <carpeta-de-render> [--medir]
"""
import datetime, hashlib, json, math, os, subprocess, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve, butter, sosfiltfilt
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'cuento-en-siete'))
import sintes as SN, sintes6 as S6
RUN = sys.argv[1]; SR = 48000
P = json.load(open(os.path.join(RUN, 'partitura.json'), encoding='utf-8'))
N = int(P['duracion'] * SR)
SC = P['secciones']; SECS = {s['num']: (s['t'], (SC[k + 1]['t'] if k + 1 < len(SC) else P['fin'])) for k, s in enumerate(SC)}
T = np.arange(N) / SR

def panear(y, p): a = (p + 1) * math.pi / 4; return np.stack([y * math.cos(a), y * math.sin(a)], 1)
def leer(nombre, estereo):
    x = np.fromfile(os.path.join(RUN, nombre + '.f32'), dtype=np.float32).astype(float)
    x = x.reshape(-1, 2) if estereo else x
    out = np.zeros((N, 2) if estereo else N); out[:min(N, len(x))] = x[:N]; return out
def ancho(y, p=0.0, ms=11): d = int(ms / 1000 * SR); r = np.concatenate([np.zeros(d), y[:-d]]); return np.stack([y * (1 - .3 * p), r * (1 + .3 * p)], 1) * .7
def filtro(x, tipo, fc, orden=2): return sosfiltfilt(butter(orden, fc, btype=tipo, fs=SR, output='sos'), x, axis=0)
def mono(x): return x.mean(1) if x.ndim == 2 else x
def curva(v): return np.interp(T, [a for a, _ in v], [b for _, b in v])
def ventana(tramos):
    w = np.zeros(N)
    for a, z in tramos: w[int(a * SR):int(z * SR)] = 1
    k = int(.08 * SR); return np.convolve(w, np.ones(k) / k, 'same')

capas = {}
TTC = ['boca', 'arpa', 'cuerda', 'sala', 'organo', 'cristal', 'estacion', 'terminal', 'terminal-solo', 'plasma', 'androide', 'androide-solo', 'fotones']
for c in TTC + ['bateria', 'bateria-frito', 'convoy']: capas[c] = leer(c, True)
def agc(x, tau=.3, rango=36):
    """nivela la voz: el óxido le cambia el timbre, no el volumen (medido en r1: de −23 a −48 dB en «estoy tierra»)"""
    k = int(tau * SR); c = np.concatenate([[0], np.cumsum(x * x)]); env = np.sqrt(np.maximum(0, (c[k:] - c[:-k]) / k)); env = np.concatenate([np.full(k // 2, env[0]), env, np.full(len(x) - len(env) - k // 2, env[-1])])
    piso = env.max() * 10 ** (-rango / 20); g = np.where(env > piso, env.max() * .3 / np.maximum(env, piso), 0); g = np.minimum(g, 10 ** (rango / 20))
    m = int(.08 * SR); g = np.convolve(g, np.ones(m) / m, 'same'); return x * g
capas['traductor'] = panear(agc(leer('traductor', False)), 0); capas['agua'] = ancho(leer('agua', False), -.3, 17)
sop = leer('sabina-soprano', True)

print('estación…', flush=True)
capas['impresora'] = S6.impresora(P['impresora'], N, 1)
capas['torniquete'] = S6.torniquete(P['torniquete'], N, 2)
capas['campana'] = S6.campana(P['campana'], N, 3)
capas['lluvia'] = S6.lluvia(P['lluvia'], N, 4)
capas['pulso'] = S6.pulso(P['pulsos'], P['tonica_hz'], N, 5)
capas['sub'] = panear(SN.sub808(P['sub'], N), 0)
L_ = P['luciernagas']; capas['luciernagas'], tt_luc, r_luc, dest = S6.luciernagas(L_['t0'], L_['t1'], N, 1 / P['negra'], L_['K'], L_['notas'], L_['forz'], semilla=6)
# la voz de andén: el altavoz de la estación (banda, un poco rota) y los ecos del andén
an = mono(leer('sabina-anden', True)); an = np.tanh(2.2 * filtro(an, 'bandpass', [350, 3500], 2) / (np.abs(an).max() + 1e-9))
eco = an.copy()
for ms, g in ((183, .45), (371, .3), (612, .2), (877, .12)): d = int(ms / 1000 * SR); eco[d:] += g * an[:-d]
capas['anden'] = np.stack([eco, np.concatenate([np.zeros(int(.009 * SR)), eco[:-int(.009 * SR)]])], 1) * .7

print('vocoders…', flush=True)
mod = mono(sop); coro = ventana([(e['t'] - .05, e['t'] + e['dur'] + .3) for e in P['sabina'][2]['eventos']])
capas['voc-sinte'] = ancho(SN.vocoder(mod, SN.sinte_coro(P['coros'], N, 7), consonantes=.4), 0, 13)
capas['voc-convoy'] = ancho(SN.vocoder(mod, mono(capas['convoy']) * coro, consonantes=.3), .25, 19)     # el convoy dice la letra
capas['voc-organo'] = ancho(SN.vocoder(mod, mono(capas['organo']) * coro, consonantes=.25), -.25, 23)
capas['soprano'] = sop * coro[:, None] * .5

# r1 (medido por grupo): el coro de V quedaba −11 contra lo demás (vocoders +6, Sabina +3); el traductor perdía 25 dB con el óxido (agc, y +3 para el diálogo de III); solos +2
NIVEL = {'bateria': -5, 'bateria-frito': -9, 'fotones': -9, 'sub': -6, 'androide': -6, 'androide-solo': 0, 'cristal': -10, 'estacion': -8, 'terminal': -10, 'terminal-solo': -1,
         'plasma': -9, 'boca': -4, 'arpa': -8, 'cuerda': -9, 'sala': -12, 'organo': -11, 'luciernagas': -11, 'agua': -12, 'traductor': 1,
         'impresora': -12, 'torniquete': -12, 'campana': -9, 'lluvia': -13, 'pulso': -8, 'anden': -4, 'convoy': -10,
         'voc-sinte': 3, 'voc-convoy': 1, 'voc-organo': 0, 'soprano': -7}
medidas = {}
def activo(x):
    n = len(x) // 2400 * 2400; m = np.sqrt(np.mean(x[:n].reshape(-1, 2400, 2) ** 2, axis=(1, 2)))
    v = m[m > m.max() * .03]; return float(np.sqrt(np.mean(v ** 2))) if len(v) else 0.0
for c, x in capas.items():
    a = activo(x); medidas[c] = dict(activo_db=round(20 * math.log10(a + 1e-12), 1)); assert a > 1e-7, f'la capa {c} está muda'
    capas[c] = x * (10 ** ((-20 + NIVEL[c]) / 20) / a)
FILTROS = {'sub': ('lowpass', 140, 2), 'androide': ('highpass', 40, 2), 'traductor': ('highpass', 55, 2), 'voc-sinte': ('highpass', 120, 2), 'voc-convoy': ('highpass', 110, 2),
           'voc-organo': ('highpass', 110, 2), 'soprano': ('highpass', 160, 2), 'convoy': ('highpass', 35, 2), 'lluvia': ('highpass', 200, 2), 'cristal': ('highpass', 300, 2)}
for c, (tipo, fc, o) in FILTROS.items(): capas[c] = filtro(capas[c], tipo, fc, o)
# el silicio se hunde: pasabajas que baja a 500 Hz a la mitad del descenso (mezcla de tres versiones del grupo, sin clics)
SILICIO = ['bateria', 'fotones', 'androide', 'cristal', 'terminal', 'estacion', 'plasma']
S = P['secciones']; tS = {s['num']: s['t'] for s in S}
hundido = curva([[0, 0], [tS['IV'], 0], [tS['IV'] + 8, 1], [tS['V'], .6], [tS['V'] + 6, .35], [tS['VI'], .5], [tS['VII'], .8], [P['duracion'], .8]])
for c in SILICIO:
    x = capas[c]; a, b = filtro(x, 'lowpass', 2400, 2), filtro(x, 'lowpass', 500, 2)
    w0 = np.clip(1 - 2 * hundido, 0, 1); w2 = np.clip(2 * hundido - 1, 0, 1); w1 = 1 - w0 - w2
    capas[c] = x * w0[:, None] + a * w1[:, None] + b * w2[:, None]
duck = np.ones(N)
for e in P['web']['bateria']:
    if e.get('pieza') != 'kick': continue
    i = int(e['t'] * SR); L = min(int(.25 * SR), N - i); duck[i:i + L] = np.minimum(duck[i:i + L], 1 - .25 * np.exp(-np.arange(L) / (.08 * SR)))
SIN_DUCK = {'bateria', 'bateria-frito', 'sub', 'fotones', 'pulso', 'campana', 'anden', 'traductor', 'impresora', 'torniquete'}
rg = np.random.default_rng(P['semilla']); L = int(3.6 * SR); ir = rg.standard_normal((L, 2)) * np.exp(-np.arange(L) / SR * 1.6)[:, None]; ir[:int(.03 * SR)] = 0; ir /= np.sqrt((ir ** 2).sum(0))
ENVIO = {'anden': .35, 'campana': .45, 'convoy': .2, 'cristal': .25, 'estacion': .3, 'terminal': .2, 'terminal-solo': .2, 'plasma': .2, 'boca': .25, 'arpa': .35, 'cuerda': .3,
         'organo': .3, 'luciernagas': .35, 'agua': .3, 'traductor': .18, 'voc-sinte': .2, 'voc-convoy': .3, 'voc-organo': .3, 'soprano': .3, 'impresora': .2, 'torniquete': .25, 'lluvia': .15}
seco = np.zeros((N, 2)); envio = np.zeros((N, 2))
for c, x in capas.items():
    x = x if c in SIN_DUCK else x * duck[:, None]; seco += x
    if c in ENVIO: envio += x * ENVIO[c]
reverb = np.stack([fftconvolve(envio[:, k], ir[:, k])[:N] for k in range(2)], 1)
pre = seco + reverb * .5
mezcla = pre / np.abs(pre).max(); mezcla = np.tanh(1.6 * mezcla) / np.tanh(1.6)
GRUPOS = dict(silicio=['bateria', 'bateria-frito', 'fotones', 'sub', 'androide', 'cristal', 'terminal', 'plasma', 'estacion'], solos=['terminal-solo', 'androide-solo'],
              sutura=['impresora', 'torniquete', 'campana', 'lluvia', 'pulso', 'anden', 'convoy'], carbono=['boca', 'arpa', 'cuerda', 'sala', 'organo', 'luciernagas', 'agua'],
              traductor=['traductor'], coro=['voc-sinte', 'voc-convoy', 'voc-organo', 'soprano'])
grupos = {}
for k, (a, z) in SECS.items():
    i, j = int(a * SR), int(z * SR); tot = pre[i:j]; fila = {}
    for g, cs in GRUPOS.items():
        x = sum((capas[c] if c in SIN_DUCK else capas[c] * duck[:, None])[i:j] for c in cs); ex, er = np.mean(x ** 2), np.mean((tot - x) ** 2)
        if ex > 1e-10: fila[g] = round(10 * math.log10(ex / (er + 1e-14)), 1)
    grupos[k] = fila
if '--medir' in sys.argv:
    for k, fl in grupos.items(): print(f'  {k:4} grupo contra el resto:', '  '.join(f'{g} {v:+.1f}' for g, v in fl.items()))
    sys.exit()
wav = os.path.join(RUN, 'mezcla.wav'); wavfile.write(wav, SR, (mezcla * .95).astype(np.float32))
codigo = b''.join(open(os.path.join(AQUI, f), 'rb').read() for f in ('partitura.py', 'sintes6.py', 'mezcla.py', 'render_node.cjs', 'render_web.cjs', 'render_voz.cjs', 'render_tt.py',
                                                                        'motor/traductor.js', 'motor/convoy.js'))
nonce = os.urandom(16).hex(); run = hashlib.sha256(mezcla.astype(np.float32).tobytes() + json.dumps(P).encode() + codigo + nonce.encode()).hexdigest(); h = run[:12]
nombre = f'el-androide-en-la-estacion-s{P["semilla"]}-{h}'; out = os.path.join(AQUI, nombre); os.makedirs(out, exist_ok=False); base = os.path.join(out, nombre)
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
              tres_tiempos=P['tres_tiempos_codigo'], tonica_hz=P['tonica_hz'], niveles=NIVEL, envios=ENVIO, filtros=FILTROS, secciones_rms_db=secciones, lufs_integrado=lufs,
              bandas_hz=BANDAS, bandas_por_seccion_db=por_banda, grupos_contra_resto_db=grupos, capas=medidas,
              luciernagas=dict(destellos=len(dest), r_por_seccion={k: round(float(np.mean(r_luc[(tt_luc >= a) & (tt_luc < z)])), 2) for k, (a, z) in SECS.items() if ((tt_luc >= a) & (tt_luc < z)).any()}),
              m4a_sha256=hashlib.sha256(open(base + '.m4a', 'rb').read()).hexdigest(), wav_sha256=hashlib.sha256(open(base + '.wav', 'rb').read()).hexdigest(),
              render=os.path.relpath(RUN, AQUI).replace('\\', '/'))
with open(os.path.join(out, 'receta.json'), 'x', encoding='utf-8') as fo: json.dump(receta, fo, ensure_ascii=False, indent=1)
with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as fo: json.dump(P, fo, ensure_ascii=False)
np.save(os.path.join(RUN, 'luciernagas-r.npy'), np.stack([tt_luc, r_luc]))
print(out); print('secciones (rms dB):', secciones, '· LUFS', lufs)
for k, fl in grupos.items(): print(f'  {k:4} grupo contra el resto:', '  '.join(f'{g} {v:+.1f}' for g, v in fl.items()))
for k, v in por_banda.items(): print(f'  {k:4}', ' '.join(f'{x:6.1f}' for x in v))
