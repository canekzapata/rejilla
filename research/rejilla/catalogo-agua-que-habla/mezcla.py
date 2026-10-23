"""Catálogo de agua que habla — mezcla (Messiaen × hyperpop).

Lee las capas que rindieron render_web.cjs (biblioteca en el navegador) y render_node.cjs (objetos que cantan y Siringua), rinde
aquí las de Python (sub 808 de rejilla, dùndún y aves del jardín, desde la copia fijada de la biblioteca), coloca a Siringua (entera,
o subida de tono y cortada en el drop) y mezcla:
  · cada capa se iguala por su nivel «activo» y se lleva a su lugar (tabla NIVEL);
  · sidechain: cada bombo de la partitura agacha lo demás (drops 55 %, medio tiempo 30 %), 120 ms;
  · reverb sembrada (envíos por capa), saturación de master (tanh), tartamudeo glitch al final de los compases de `glitch`;
  · loudnorm −11 LUFS (ffmpeg).
Escribe la entrega en una carpeta nueva y exclusiva: catalogo-agua-que-habla-s1810-<hash12>/ (m4a, wav, receta, mediciones).
    python mezcla.py <carpeta-de-render>
"""
import datetime, hashlib, json, math, os, subprocess, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve, resample_poly

AQUI = os.path.dirname(os.path.abspath(__file__)); RUN = sys.argv[1]; SR = 48000
P = json.load(open(os.path.join(RUN, 'partitura.json'), encoding='utf-8')); INST = os.path.join(AQUI, P['instrumentos'])
sys.path.insert(0, os.path.join(INST, 'motores')); import rejilla as RJ, python as PY
N = int(P['duracion'] * SR); BAR = 4 * 60 / P['bpm']; S16 = BAR / 16
ficha = lambda i: json.load(open(os.path.join(INST, 'fichas', i + '.json'), encoding='utf-8'))


def panear(y, p):
    a = (p + 1) * math.pi / 4; return np.stack([y * math.cos(a), y * math.sin(a)], 1)


def poner(dest, y, t, p=0.0):
    i = int(round(t * SR))
    if i >= len(dest): return
    z = y[:len(dest) - i]; dest[i:i + len(z)] += panear(z, p) if z.ndim == 1 else z


def leer(nombre, estereo):
    x = np.fromfile(os.path.join(RUN, nombre + '.f32'), dtype=np.float32).astype(float)
    x = x.reshape(-1, 2) if estereo else np.stack([x, x], 1) * math.sqrt(.5)
    out = np.zeros((N, 2)); out[:min(N, len(x))] = x[:N]; return out


def transponer(y, st):
    """Hyperpop: subir la voz cambiando la velocidad (más aguda y más corta), como un sampler."""
    if st == 0: return y
    up, down = {7: (2, 3), 12: (1, 2), 5: (3, 4)}[st]; return resample_poly(y, up, down)


capas = {}
# ── las del navegador (estéreo) y las de node (mono) ──
for c in P['web']: capas[c] = leer(c, True)
for c in ['aves-siringe', 'agua', 'waterphone', 'tambor-que-habla']: capas[c] = leer(c, False)
# ── sub 808 (rejilla esquinas, modal) ──
K = ficha('rejilla-esquinas-sub808'); y = np.zeros(N)
for e in P['sub']: y += RJ.tiempo(RJ.modos(K, e['midi'] - (12 if e['midi'] >= 36 else 0), e['t'], e['vel'], dur=e['dur']), P['duracion'], SR)[:N]   # v4: el sub nunca sube a 73 Hz (ahí pega el bombo)
# v4: el sub suena sólo donde hay bombo (B2, C, E), con 0.3 s de salida: sus colas no entran al catálogo ni a la coda
puerta = np.zeros(N)
for k in ('B2', 'C', 'E'):
    a, z = P['secciones'][k]; i, j = int(a * BAR * SR), int(z * BAR * SR); puerta[i:j] = 1; r = min(int(.3 * SR), N - j); puerta[j:j + r] = np.linspace(1, 0, r)
capas['sub'] = np.stack([y * puerta, y * puerta], 1) * math.sqrt(.5)
# ── dùndún (jardín): cada golpe se desliza a su nota; las tónicas caen más (habla) ──
K = ficha('jardin-tambor-parlante'); y = np.zeros((N, 2))
for k, e in enumerate(P['dundun']):
    Ke = dict(K, fisica=dict(K['fisica'], habla=e['habla'])); z, sr = PY.nota(Ke, e['midi'], e['vel'], .3); poner(y, z, e['t'], -.3 if k % 2 else .3)
capas['dundun'] = y
# ── aves del jardín ──
y = np.zeros((N, 2))
for e in P['aves_jardin']: z, sr = PY.nota(ficha(e['ficha']), e['midi'], e['vel'], e['dur']); poner(y, z, e['t'], e['pan'])
capas['aves-jardin'] = y
# ── Siringua: entera (agua + ave) o cortada (las palabras tartamudean cada `paso`) ──
agua_f = np.fromfile(os.path.join(RUN, 'siringua-agua.f32'), dtype=np.float32).astype(float)
ave_f = np.fromfile(os.path.join(RUN, 'siringua-ave.f32'), dtype=np.float32).astype(float)
pal = [np.fromfile(os.path.join(RUN, f'siringua-palabra-{i}.f32'), dtype=np.float32).astype(float) for i in range(7)]
voz, ave_voz = np.zeros((N, 2)), np.zeros((N, 2))
for s in P['siringua']:
    if s['modo'] == 'entera':
        poner(voz, transponer(agua_f, s['transponer']), s['t'], 0); poner(ave_voz, transponer(ave_f, s['transponer']), s['t'], .5)
    else:
        t = s['t']
        for i in s['palabras']:
            w = transponer(pal[i], s['transponer']); L = int(s['paso'] * 1.6 * SR); rep = 3
            corte = w[int(.02 * SR):int(.02 * SR) + L].copy(); f = int(.004 * SR); corte[:f] *= np.linspace(0, 1, f); corte[-f:] *= np.linspace(1, 0, f)
            for j in range(rep): poner(voz, corte * (1 - .18 * j), t + j * s['paso'], (-.4, .4, 0)[j % 3])
            t += rep * s['paso']
capas['siringua'] = voz; capas['siringua-ave'] = ave_voz

# ── igualar por nivel activo y llevar cada capa a su lugar (dB) ──
# v2 (después de medir «contra la mezcla donde suena» en la v1): la voz del agua, los tambores que hablan, las aves y el agua al frente
NIVEL = {'bateria': -2, 'bateria-frito': -6, 'sub': -3, 'berimbau': -7, 'teponaztli': -9, 'dundun': -1, 'tambor-que-habla': -4, 'marimba': -10, 'mbira': -10,
         'saron': -8, 'gender': -9, 'gyil': -10, 'arpaboca': -6, 'aves-siringe': -6, 'aves-jardin': -7, 'agua': -8, 'waterphone': -11, 'siringua': 2, 'siringua-ave': -6}
medidas = {}
def activo(x):
    m = np.sqrt(np.mean(x.reshape(-1, 2400, 2) ** 2, axis=(1, 2))) if len(x) % 2400 == 0 else np.sqrt(np.mean(x[:len(x) // 2400 * 2400].reshape(-1, 2400, 2) ** 2, axis=(1, 2)))
    v = m[m > m.max() * .03]; return float(np.sqrt(np.mean(v ** 2))) if len(v) else 0.0
for c, x in capas.items():
    a = activo(x); medidas[c] = dict(activo_db=round(20 * math.log10(a + 1e-12), 1))
    assert a > 1e-6, f'la capa {c} está muda'
    capas[c] = x * (10 ** ((-20 + NIVEL[c]) / 20) / a)

# ── v3 (pedido de Canek tras escuchar la v2): limpiar el grave y hundir las vocales de Siringua ──
from scipy.signal import butter, sosfiltfilt, stft, istft
from scipy.ndimage import uniform_filter1d
GRAVES = ['sub', 'bateria', 'dundun', 'arpaboca', 'berimbau', 'marimba', 'teponaztli', 'gender', 'saron', 'mbira', 'gyil', 'siringua']
TERCIOS = [31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315]
def duenos(etiqueta):
    """En cada tercio de octava grave: qué capa domina y por cuántos dB sobre la segunda (más margen = banda más limpia)."""
    E = {}
    for c in GRAVES:
        X = np.abs(np.fft.rfft(capas[c].mean(1)[::4])) ** 2; f = np.fft.rfftfreq(len(capas[c][::4]), 4 / SR)
        E[c] = [10 * math.log10(X[(f >= b / 2 ** (1 / 6)) & (f < b * 2 ** (1 / 6))].sum() + 1e-20) for b in TERCIOS]
    fila = []
    for k, b in enumerate(TERCIOS):
        o = sorted(GRAVES, key=lambda c: -E[c][k]); fila.append(dict(hz=b, duena=o[0], segunda=o[1], margen_db=round(E[o[0]][k] - E[o[1]][k], 1)))
    print(etiqueta + ': ' + '  '.join(f"{r['hz']:g}:{r['duena']}+{r['margen_db']}({r['segunda']})" for r in fila)); return fila
GRAVE_ANTES = duenos('grave antes')
FILTROS = {  # cada quien su piso: el sub abajo de 95 Hz; el arpa de boca sin su fundamental (73 Hz = la del sub), sus armónicos elegidos empiezan en 294 Hz
    'sub': ('lowpass', 75, 4), 'arpaboca': ('highpass', 150, 4), 'dundun': ('highpass', 105, 2), 'berimbau': ('highpass', 120, 2), 'marimba': ('highpass', 115, 2),
    'teponaztli': ('highpass', 110, 2), 'mbira': ('highpass', 130, 2), 'saron': ('highpass', 140, 2), 'gyil': ('highpass', 150, 2), 'gender': ('highpass', 85, 2),
    'siringua': ('highpass', 160, 2), 'siringua-ave': ('highpass', 300, 2)}
# v4: el arpa de boca pierde su fundamental (73 Hz) sólo donde hay sub y bombo (B2, C, E); en A, D y F conserva el cuerpo del bordón
con_grave = np.zeros(N)
for k in ('B2', 'C', 'E'): a, z = P['secciones'][k]; con_grave[int(a * BAR * SR):int(z * BAR * SR)] = 1
con_grave = np.convolve(con_grave, np.ones(int(.4 * SR)) / int(.4 * SR), mode='same')[:, None]     # fundido de 0.4 s entre secciones
for c, (tipo, fc, orden) in FILTROS.items():
    sos = butter(orden, fc, btype=tipo, fs=SR, output='sos'); f = sosfiltfilt(sos, capas[c], axis=0)
    capas[c] = capas[c] * (1 - con_grave) + f * con_grave if c == 'arpaboca' else f
def crestas(x):
    """Cuánto sobresalen los picos (formantes) sobre su propia envolvente espectral, 300 Hz–5 kHz, en los cuadros donde hay voz."""
    f, _, Z = stft(x.mean(1), SR, nperseg=2048, noverlap=1536); M = 20 * np.log10(np.abs(Z) + 1e-9); b = (f > 300) & (f < 5000); act = M[b].max(0) > M[b].max() - 40
    env = uniform_filter1d(M[b][:, act], 25, axis=0); return round(float(np.mean((M[b][:, act] - env).max(0))), 1)
def hundir_picos(x, umbral=3.0, razon=2.5):
    """Comprime los picos del espectro que pasan `umbral` dB sobre su envolvente (promedio de ~25 bandas): la vocal sigue siendo la misma, sobresale menos."""
    out = np.zeros_like(x)
    for k in range(2):
        f, _, Z = stft(x[:, k], SR, nperseg=2048, noverlap=1536); M = 20 * np.log10(np.abs(Z) + 1e-9); env = uniform_filter1d(M, 25, axis=0)
        exc = np.maximum(0, M - env - umbral); g = 10 ** (-(exc * (1 - 1 / razon)) / 20)
        _, y = istft(Z * g, SR, nperseg=2048, noverlap=1536); out[:, k] = y[:len(x)] if len(y) >= len(x) else np.pad(y, (0, len(x) - len(y)))
    return out
CRESTA_ANTES = crestas(capas['siringua']); _a = activo(capas['siringua'])
capas['siringua'] = hundir_picos(capas['siringua']); capas['siringua'] *= _a * 10 ** (-2.5 / 20) / activo(capas['siringua'])   # mismo nivel activo que antes, menos 2.5 dB: los picos se hunden, la voz no se va
CRESTA_DESPUES = crestas(capas['siringua'])
print(f'vocales de Siringua: los picos sobresalían {CRESTA_ANTES} dB sobre su envolvente; ahora {CRESTA_DESPUES} dB (y la voz 2.5 dB abajo)')
GRAVE_DESPUES = duenos('grave después')

# ── sidechain desde la partitura ──
t = np.arange(N) / SR; duck = np.ones(N)
for e in P['web']['bateria']:
    if e.get('pieza') != 'kick': continue
    sec = next(k for k, (a, z) in P['secciones'].items() if a * BAR <= e['t'] < z * BAR); prof = .3 if sec == 'B2' else .55
    i = int(e['t'] * SR); L = int(.35 * SR); duck[i:i + L] = np.minimum(duck[i:i + L], 1 - prof * np.exp(-np.arange(min(L, N - i)) / (.12 * SR)))
SIN_DUCK = {'bateria', 'bateria-frito', 'sub'}
# v3: el sub se aparta del bombo 808 un instante (cada quien su golpe: el bombo pega, el sub sigue)
duck_sub = np.ones(N)
for e in P['web']['bateria']:
    if e.get('pieza') == 'kick': i = int(e['t'] * SR); L = int(.2 * SR); duck_sub[i:i + L] = np.minimum(duck_sub[i:i + L], 1 - .6 * np.exp(-np.arange(min(L, N - i)) / (.06 * SR)))
# ── reverb sembrada (IR estéreo 2.4 s) ──
rg = np.random.default_rng(P['semilla']); L = int(2.4 * SR); ir = rg.standard_normal((L, 2)) * np.exp(-np.arange(L) / SR * 2.6)[:, None]; ir[:int(.012 * SR)] = 0; ir /= np.sqrt((ir ** 2).sum(0))
ENVIO = {'aves-siringe': .35, 'aves-jardin': .35, 'agua': .3, 'waterphone': .45, 'siringua': .3,   # v3: la voz un poco más adentro de la sala
          'siringua-ave': .4, 'gender': .25, 'saron': .18, 'arpaboca': .15, 'marimba': .1, 'dundun': .12, 'tambor-que-habla': .2, 'mbira': .12}
seco = np.zeros((N, 2)); envio = np.zeros((N, 2))
for c, x in capas.items():
    x = (x * duck_sub[:, None] if c == 'sub' else x) if c in SIN_DUCK else x * duck[:, None]; seco += x
    if c in ENVIO: envio += x * ENVIO[c]
reverb = np.stack([fftconvolve(envio[:, k], ir[:, k])[:N] for k in range(2)], 1)
mezcla = seco + reverb * .55
# ── master: saturación (hyperpop) y tartamudeo glitch ──
mezcla /= np.abs(mezcla).max(); mezcla = np.tanh(2.2 * mezcla) / np.tanh(2.2)
for b in P['glitch']:
    fin = (b + 1) * BAR; ini = fin - BAR / 4; corte = mezcla[int((ini - S16) * SR):int(ini * SR)].copy()
    for j in range(4):                                  # el último tiempo se vuelve una semicorchea repetida que sube
        z = resample_poly(corte, 4, 4 + j) if j else corte; i = int((ini + j * S16) * SR); n = min(len(z), int(S16 * SR), N - i)
        mezcla[i:i + n] = z[:n] * (1 - .1 * j)
wav = os.path.join(RUN, 'mezcla.wav'); wavfile.write(wav, SR, (mezcla * .95).astype(np.float32))
# ── entrega: carpeta nueva y exclusiva, con hash (imagen = audio, versión = partitura + motores, nonce) ──
motores = b''.join(open(os.path.join(INST, 'motores', f), 'rb').read() for f in sorted(os.listdir(os.path.join(INST, 'motores'))))
nonce = os.urandom(16).hex(); run = hashlib.sha256(mezcla.astype(np.float32).tobytes() + json.dumps(P).encode() + motores + nonce.encode()).hexdigest(); h = run[:12]
out = os.path.join(AQUI, f'catalogo-agua-que-habla-s{P["semilla"]}-{h}'); os.makedirs(out, exist_ok=False)
base = os.path.join(out, f'catalogo-agua-que-habla-s{P["semilla"]}-{h}')
subprocess.run(['ffmpeg', '-v', 'error', '-i', wav, '-af', 'loudnorm=I=-11:TP=-1:LRA=8', '-ar', str(SR), '-c:a', 'pcm_s16le', base + '.wav'], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-i', base + '.wav', '-c:a', 'aac', '-b:a', '192k', base + '.m4a'], check=True)
# mediciones por sección (rms de la entrega) y peso de cada capa en la mezcla
_, fin = wavfile.read(base + ".wav"); fin = fin.astype(float) / 32768
for c, x in capas.items(): medidas[c]['en_mezcla_db'] = round(20 * math.log10(np.sqrt(np.mean(x ** 2)) + 1e-12), 1)
secciones = {k: round(20 * math.log10(np.sqrt(np.mean(fin[int(a * BAR * SR):int(z * BAR * SR)] ** 2)) + 1e-12), 1) for k, (a, z) in P['secciones'].items()}
receta = dict(titulo=P['titulo'], semilla=P['semilla'], ejecucion=run, nonce=nonce, fecha=datetime.date.today().isoformat(), instrumentos=P['instrumentos'],
              siringua=json.load(open(os.path.join(RUN, 'siringua.json'), encoding='utf-8')), niveles=NIVEL, envios=ENVIO, version='v4: grave limpio (arpa sin fundamental sólo con sub; sub abajo de 75 Hz) + vocales hundidas',
              filtros=FILTROS, grave_antes=GRAVE_ANTES, grave_despues=GRAVE_DESPUES, vocales_cresta_db=dict(antes=CRESTA_ANTES, despues=CRESTA_DESPUES, ajuste_db=-2.5), secciones_rms_db=secciones, capas=medidas,
              m4a_sha256=hashlib.sha256(open(base + '.m4a', 'rb').read()).hexdigest(), render=os.path.relpath(RUN, AQUI).replace('\\', '/'))
json.dump(receta, open(os.path.join(out, 'receta.json'), 'x', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(P, open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8'), ensure_ascii=False)
np.save(os.path.join(RUN, 'duck.npy'), duck[::480])
print(out); print('secciones (rms dB):', secciones)
# lo que cuenta: cada capa contra la mezcla en los momentos en que esa capa suena (ventanas de 50 ms; ¿se oye o la tapan?)
W50 = int(.05 * SR); nW = N // W50; pre = seco + reverb * .55; mez_v = np.sqrt(np.mean(pre[:nW * W50].reshape(nW, W50, 2) ** 2, axis=(1, 2)))
for c, x in capas.items():
    xv = np.sqrt(np.mean((x if c in SIN_DUCK else x * duck[:, None])[:nW * W50].reshape(nW, W50, 2) ** 2, axis=(1, 2))); act = xv > xv.max() * .1
    medidas[c]['contra_mezcla_db'] = round(20 * math.log10(np.sqrt(np.mean(xv[act] ** 2)) / np.sqrt(np.mean(mez_v[act] ** 2)) + 1e-12), 1) if act.any() else None
json.dump(dict(receta, capas=medidas), open(os.path.join(out, 'receta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for c, m in sorted(medidas.items(), key=lambda kv: -(kv[1]['contra_mezcla_db'] or -99)): print(f'  {c:18} {m["contra_mezcla_db"]:6.1f} dB contra la mezcla donde suena')
