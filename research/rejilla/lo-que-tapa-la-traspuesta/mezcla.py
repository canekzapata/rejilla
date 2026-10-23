"""Lo que tapa la traspuesta — mezcla.

Lee las capas de render_web.cjs, render_node.cjs (garganta de montaña, viento, objetos que cantan, voz de agua) y render_voz.cjs
(Sabina), sintetiza aquí el bajo sin trastes, el sinte de Zawinul, las portadoras del coro y del solo, y el 808; arma los
vocoders y mezcla:
  · el coro: Sabina modula al pájaro de siringe (soprano), al sinte del coral y AL VIENTO (el viento estriado canta la letra);
    la voz de agua canta la contralto y la garganta de montaña el tenor, con sus propias gargantas;
  · el solo de vocoder: Sabina canta scat y modula al sinte que toca su misma línea;
  · cada capa por su nivel activo (NIVEL), cada quien su piso (FILTROS); sidechain en el coro hyperpop;
  · LAS TIJERAS de Nobuto: la mezcla se corta y se pega a sí misma (repite, al revés, sube, salta a otro momento);
  · reverb sembrada, saturación de master, loudnorm −11 LUFS. Medidas por capa, por grupo y por banda, sección por sección.
Entrega en carpeta nueva y exclusiva: lo-que-tapa-la-traspuesta-s420048-<hash12>/.
    python mezcla.py <carpeta-de-render>
"""
import datetime, hashlib, json, math, os, subprocess, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve, resample_poly, butter, sosfiltfilt
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(AQUI, '..', 'cuento-en-siete'))
import sintes as SN, sintes2 as S2

RUN = sys.argv[1]; SR = 48000
P = json.load(open(os.path.join(RUN, 'partitura.json'), encoding='utf-8'))
N = int(P['duracion'] * SR); S = P['semicorchea']; SECS = {k: tuple(v) for k, v in P['secciones'].items()}; SECS['VI'] = (SECS['VI'][0], P['duracion'])

def panear(y, p): a = (p + 1) * math.pi / 4; return np.stack([y * math.cos(a), y * math.sin(a)], 1)
def leer(nombre, estereo):
    x = np.fromfile(os.path.join(RUN, nombre + '.f32'), dtype=np.float32).astype(float)
    x = x.reshape(-1, 2) if estereo else x
    out = np.zeros((N, 2) if estereo else N); out[:min(N, len(x))] = x[:N]; return out
def ancho(y, p=0.0, ms=11): d = int(ms / 1000 * SR); r = np.concatenate([np.zeros(d), y[:-d]]); return np.stack([y * (1 - .3 * p), r * (1 + .3 * p)], 1) * .7
def filtro(x, tipo, fc, orden=2): return sosfiltfilt(butter(orden, fc, btype=tipo, fs=SR, output='sos'), x, axis=0)
def mono(x): return x.mean(1) if x.ndim == 2 else x
def ventana(tramos):                                       # 1 dentro de los tramos [(a, z)], con fundidos de 80 ms
    w = np.zeros(N)
    for a, z in tramos: w[int(a * SR):int(z * SR)] = 1
    k = int(.08 * SR); return np.convolve(w, np.ones(k) / k, 'same')

capas = {}
for c in ['berimbau', 'teponaztli', 'bateria', 'bateria-frito', 'marimba']: capas[c] = leer(c, True)
for c, p in [('garganta-montana', 0), ('garganta-coro', .25), ('garganta-solo', -.1), ('sax', -.2), ('clarinete', -.45), ('chelo', .4), ('piano', -.25),
             ('trombon', .2), ('gong', 0), ('aves', .5), ('siringa', .45), ('agua', -.35), ('vozagua', -.4)]:
    capas[c] = panear(leer(c, False), p)
capas['viento'] = leer('viento', True)
# el chelo del punto gris (legno, bartok, ponticello cortos) queda 20 dB bajo su ponticello largo del V: cada uno con su nivel
enI = np.clip((SECS['I'][1] + .5 - np.arange(N) / SR) / .5, 0, 1)[:, None]
capas['chelo-I'] = capas['chelo'] * enI; capas['chelo'] = capas['chelo'] * (1 - enI)
aves_coro = leer('aves-coro', False)
sab = {c: leer('sabina-' + c, True) for c in ('soprano', 'baja', 'scat')}

print('sintes…', flush=True)
capas['bajo'] = panear(S2.mono(P['bajo'], N, 'fretless', 1), .05)
capas['sinte'] = ancho(S2.mono(P['sinte'], N, 'zawinul', 2), .3, 9)
voces = {v: sum((C[v] for C in P['coros'].values()), []) for v in 'SATB'}
sinte_coro = SN.sinte_coro(voces, N, 3)
sub = SN.sub808(P['sub'], N); capas['sub'] = np.stack([sub, sub], 1) * math.sqrt(.5)
sucio = filtro(np.tanh(5 * sub), 'bandpass', (110, 320)); capas['808-sucio'] = np.stack([sucio, sucio], 1) * math.sqrt(.5)

print('vocoders…', flush=True)
mod = mono(sab['soprano']) + .7 * mono(sab['baja'])
coros = ventana([(e['t'] - .05, e['t'] + e['dur'] + .3) for C in P['coros'].values() for e in C['S']])
capas['voc-pajaro'] = panear(SN.vocoder(mod, aves_coro, consonantes=.25), .45)
capas['voc-sinte'] = ancho(SN.vocoder(mod, sinte_coro, consonantes=.4), 0, 13)
capas['voc-viento'] = ancho(SN.vocoder(mod, mono(capas['viento']) * coros, consonantes=.15), -.2, 17)   # el viento estriado dice la letra
car_solo = S2.mono(P['vocsolo'], N, 'zawinul', 4)
capas['voc-solo'] = ancho(SN.vocoder(mono(sab['scat']), car_solo, suaviza=1, consonantes=.45), .15, 7)
capas['aves-coro'] = panear(aves_coro, .6)
capas['sabina'] = sab['soprano'] + .6 * sab['baja'] + .35 * sab['scat']

# v2 (medido por grupo en la v1): el tema de Zawinul en II quedaba −8 dB, los solos del IV apenas al nivel del ritmo, el viento que
# habla −13 dB contra la mezcla: sinte +3, solos +2, viento hablado +3, voz de agua +2, bajo sin trastes +2, batería −1
NIVEL = {'bateria': -6, 'bateria-frito': -8, 'sub': -8, '808-sucio': -13, 'bajo': -3, 'berimbau': -11, 'teponaztli': -12, 'marimba': -12,
         'garganta-montana': -7, 'garganta-coro': -4, 'garganta-solo': 1, 'sax': -2, 'sinte': 0, 'clarinete': -8, 'chelo': -9, 'chelo-I': -6, 'piano': -9, 'trombon': -8,
         'gong': -9, 'aves': -9, 'siringa': -4, 'agua': -12, 'vozagua': -2, 'viento': -8, 'voc-pajaro': -3, 'voc-sinte': -2, 'voc-viento': -2, 'voc-solo': 1,
         'aves-coro': -14, 'sabina': -7}
medidas = {}
def activo(x):
    n = len(x) // 2400 * 2400; m = np.sqrt(np.mean(x[:n].reshape(-1, 2400, 2) ** 2, axis=(1, 2)))
    v = m[m > m.max() * .03]; return float(np.sqrt(np.mean(v ** 2))) if len(v) else 0.0
for c, x in capas.items():
    a = activo(x); medidas[c] = dict(activo_db=round(20 * math.log10(a + 1e-12), 1)); assert a > 1e-7, f'la capa {c} está muda'
    capas[c] = x * (10 ** ((-20 + NIVEL[c]) / 20) / a)
FILTROS = {'viento': ('highpass', 45, 2), 'sub': ('lowpass', 80, 4), 'bajo': ('highpass', 38, 2), 'sax': ('highpass', 110, 2), 'sinte': ('highpass', 140, 2), 'voc-pajaro': ('highpass', 200, 2),
           'voc-sinte': ('highpass', 110, 2), 'voc-viento': ('highpass', 150, 2), 'voc-solo': ('highpass', 150, 2), 'vozagua': ('highpass', 150, 2),
           'sabina': ('highpass', 160, 2), 'aves': ('highpass', 400, 2), 'aves-coro': ('highpass', 400, 2), 'siringa': ('highpass', 500, 2),
           'berimbau': ('highpass', 120, 2), 'teponaztli': ('highpass', 110, 2), 'marimba': ('highpass', 150, 2), 'garganta-coro': ('highpass', 90, 2),
           'garganta-solo': ('highpass', 90, 2)}
for c, (tipo, fc, o) in FILTROS.items(): capas[c] = filtro(capas[c], tipo, fc, o)
# v3: en el IV (los solos) el ritmo baja 3 dB: abrir el círculo es dejar que la voz salga (v2: solos −1.2 contra ritmo −2.4)
enIV = ventana([SECS['IV']])[:, None] * (10 ** (-3 / 20) - 1) + 1
for c in ('bateria', 'bajo', 'berimbau', 'teponaztli', 'marimba'): capas[c] = capas[c] * enIV
capas['sax'] = capas['sax'] + .25 * filtro(capas['sax'], 'bandpass', (220, 650)) + .2 * filtro(capas['sax'], 'highpass', 2500)

# sidechain: fuerte en el coro hyperpop (III), suave en lo demás
duck = np.ones(N)
for e in P['web']['bateria']:
    if e.get('pieza') != 'kick': continue
    prof = .5 if SECS['III'][0] <= e['t'] < SECS['III'][1] or SECS['V'][0] <= e['t'] < SECS['V'][1] else .15
    i = int(e['t'] * SR); L = min(int(.3 * SR), N - i); duck[i:i + L] = np.minimum(duck[i:i + L], 1 - prof * np.exp(-np.arange(L) / (.1 * SR)))
duck_sub = np.ones(N)
for e in P['web']['bateria']:
    if e.get('pieza') == 'kick': i = int(e['t'] * SR); L = min(int(.18 * SR), N - i); duck_sub[i:i + L] = np.minimum(duck_sub[i:i + L], 1 - .6 * np.exp(-np.arange(L) / (.05 * SR)))
SIN_DUCK = {'bateria', 'bateria-frito', 'sub', '808-sucio'}
rg = np.random.default_rng(P['semilla']); L = int(2.6 * SR); ir = rg.standard_normal((L, 2)) * np.exp(-np.arange(L) / SR * 2.4)[:, None]; ir[:int(.016 * SR)] = 0; ir /= np.sqrt((ir ** 2).sum(0))
ENVIO = {'aves': .4, 'aves-coro': .45, 'siringa': .35, 'agua': .3, 'gong': .35, 'garganta-montana': .4, 'garganta-coro': .25, 'garganta-solo': .2, 'vozagua': .3,
         'voc-pajaro': .3, 'voc-viento': .35, 'voc-sinte': .18, 'voc-solo': .15, 'sabina': .25, 'sax': .16, 'sinte': .14, 'clarinete': .3, 'chelo': .3, 'chelo-I': .3, 'piano': .3,
         'trombon': .25, 'marimba': .12, 'viento': .15}
seco = np.zeros((N, 2)); envio = np.zeros((N, 2))
for c, x in capas.items():
    x = (x * duck_sub[:, None] if c in ('sub', '808-sucio') else x) if c in SIN_DUCK else x * duck[:, None]; seco += x
    if c in ENVIO: envio += x * ENVIO[c]
reverb = np.stack([fftconvolve(envio[:, k], ir[:, k])[:N] for k in range(2)], 1)
pre = seco + reverb * .5
mezcla = pre / np.abs(pre).max(); mezcla = np.tanh(1.8 * mezcla) / np.tanh(1.8)

# las tijeras de Nobuto: la mezcla se corta y se pega a sí misma
fuente = mezcla.copy(); f = int(.003 * SR)
def pegar(i, z):
    n = min(len(z), N - i); z = z[:n].copy(); z[:f] *= np.linspace(0, 1, f)[:, None]; z[-f:] *= np.linspace(1, 0, f)[:, None]; mezcla[i:i + n] = z
for tj in P['tijeras']:
    i = int(tj['t'] * SR); n = int(tj['dur'] * SR); trozo = fuente[i:i + n]
    if tj['tipo'] == 'repite':                       # el primer cuarto, cuatro veces
        q = fuente[i:i + n // 4]; pegar(i, np.concatenate([q * (1 - .12 * j) for j in range(4)]))
    elif tj['tipo'] == 'reversa': pegar(i, trozo[::-1])
    elif tj['tipo'] == 'sube': pegar(i, np.concatenate([resample_poly(trozo[:n // 2], 1, 2, axis=0)] * 2))   # una octava arriba, dos veces
    elif tj['tipo'] == 'salto': j = int(tj['desde'] * SR); pegar(i, fuente[j:j + n])
wav = os.path.join(RUN, 'mezcla.wav'); wavfile.write(wav, SR, (mezcla * .95).astype(np.float32))

codigo = b''.join(open(os.path.join(AQUI, f), 'rb').read() for f in ('partitura.py', 'sintes2.py', 'mezcla.py', 'render_node.cjs', 'render_web.cjs', 'render_voz.cjs', 'motor/garganta.js', 'motor/viento.js'))
nonce = os.urandom(16).hex(); run = hashlib.sha256(mezcla.astype(np.float32).tobytes() + json.dumps(P).encode() + codigo + nonce.encode()).hexdigest(); h = run[:12]
nombre = f'lo-que-tapa-la-traspuesta-s{P["semilla"]}-{h}'; out = os.path.join(AQUI, nombre); os.makedirs(out, exist_ok=False); base = os.path.join(out, nombre)
subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', wav, '-af', 'loudnorm=I=-11:TP=-1:LRA=11', '-ar', str(SR), '-c:a', 'pcm_s16le', base + '.wav'], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', base + '.wav', '-c:a', 'aac', '-b:a', '192k', base + '.m4a'], check=True)
_, fin = wavfile.read(base + '.wav'); fin = fin.astype(float) / 32768
secciones = {k: round(20 * math.log10(np.sqrt(np.mean(fin[int(a * SR):int(z * SR)] ** 2)) + 1e-12), 1) for k, (a, z) in SECS.items()}
BANDAS = [(20, 60), (60, 120), (120, 250), (250, 500), (500, 1000), (1000, 2000), (2000, 4000), (4000, 8000), (8000, 16000)]
def bandas(x):
    X = np.abs(np.fft.rfft(x.mean(1))) ** 2; fr = np.fft.rfftfreq(len(x), 1 / SR); tot = X.sum()
    return [round(10 * math.log10(X[(fr >= a) & (fr < b)].sum() / tot + 1e-12), 1) for a, b in BANDAS]
por_banda = {k: bandas(fin[int(a * SR):int(z * SR)]) for k, (a, z) in SECS.items()}
GRUPOS = dict(coro=['voc-pajaro', 'voc-sinte', 'voc-viento', 'vozagua', 'garganta-coro', 'sabina', 'aves-coro'], solos=['garganta-solo', 'siringa', 'voc-solo', 'sax'],
              lachenmann=['clarinete', 'chelo', 'chelo-I', 'piano', 'trombon', 'gong', 'garganta-montana'], ritmo=['bateria', 'bateria-frito', 'sub', '808-sucio', 'bajo'],
              percusion=['berimbau', 'teponaztli', 'marimba'], zawinul=['sinte'], ambiente=['viento', 'aves', 'agua'])
grupos = {}
for k, (a, z) in SECS.items():
    i, j = int(a * SR), int(z * SR); tot = pre[i:j]; fila = {}
    for g, cs in GRUPOS.items():
        x = sum((capas[c] if c in SIN_DUCK else capas[c] * duck[:, None])[i:j] for c in cs); ex, er = np.mean(x ** 2), np.mean((tot - x) ** 2)
        if ex > 1e-10: fila[g] = round(10 * math.log10(ex / (er + 1e-14)), 1)
    grupos[k] = fila
W = int(.05 * SR); nW = N // W; mez_v = np.sqrt(np.mean(pre[:nW * W].reshape(nW, W, 2) ** 2, axis=(1, 2)))
for c, x in capas.items():
    xv = np.sqrt(np.mean((x if c in SIN_DUCK else x * duck[:, None])[:nW * W].reshape(nW, W, 2) ** 2, axis=(1, 2))); act = xv > xv.max() * .1
    medidas[c]['contra_mezcla_db'] = round(20 * math.log10(np.sqrt(np.mean(xv[act] ** 2)) / np.sqrt(np.mean(mez_v[act] ** 2)) + 1e-12), 1) if act.any() else None
lufs = subprocess.run(['ffmpeg', '-i', base + '.wav', '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True, errors='replace').stderr
lufs = float([l for l in lufs.splitlines() if l.strip().startswith('I:')][-1].split()[1])
receta = dict(titulo=P['titulo'], semilla=P['semilla'], terreno=P['terreno'], ejecucion=run, nonce=nonce, fecha=datetime.date.today().isoformat(), instrumentos=P['instrumentos'],
              niveles=NIVEL, envios=ENVIO, filtros=FILTROS, tijeras=P['tijeras'], secciones_rms_db=secciones, lufs_integrado=lufs, bandas_hz=BANDAS, bandas_por_seccion_db=por_banda,
              grupos_contra_resto_db=grupos, capas=medidas, m4a_sha256=hashlib.sha256(open(base + '.m4a', 'rb').read()).hexdigest(),
              wav_sha256=hashlib.sha256(open(base + '.wav', 'rb').read()).hexdigest(), render=os.path.relpath(RUN, AQUI).replace('\\', '/'))
with open(os.path.join(out, 'receta.json'), 'x', encoding='utf-8') as fo: json.dump(receta, fo, ensure_ascii=False, indent=1)
with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as fo: json.dump(P, fo, ensure_ascii=False)
np.save(os.path.join(RUN, 'duck.npy'), duck[::480])
print(out); print('secciones (rms dB):', secciones, '· LUFS', lufs)
for k, fl in grupos.items(): print(f'  {k:4} grupo contra el resto:', '  '.join(f'{g} {v:+.1f}' for g, v in fl.items()))
for k, v in por_banda.items(): print(f'  {k:4}', ' '.join(f'{x:6.1f}' for x in v))
for c, m in sorted(medidas.items(), key=lambda kv: -(kv[1]['contra_mezcla_db'] or -99)): print(f'  {c:17} {m["contra_mezcla_db"]:6.1f} dB contra la mezcla donde suena')
