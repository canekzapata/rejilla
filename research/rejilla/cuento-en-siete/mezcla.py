"""Cuento en siete — mezcla.

Lee las capas de render_web.cjs (biblioteca en el navegador), render_node.cjs (objetos que cantan) y render_voz.cjs (Sabina),
sintetiza aquí las de sintes.py (espectro, sinte del dúo, sinte del coro, sub 808), arma el coro de vocoders y mezcla:
  · el coro: Sabina modula cuatro portadoras — el pájaro de siringe que canta la soprano, el berimbau del tenor, el arpa de boca
    (la lengüeta en la fundamental del acorde, la boca en la soprano: Stimmung) y el sinte de sierras —; la voz de agua canta la
    contralto con su propia garganta de burbujas, sin vocoder;
  · cada capa se iguala por su nivel «activo» y va a su lugar (NIVEL); cada quien su piso (FILTROS);
  · sidechain desde los bombos de la partitura (coros 50 %, invención y dúo 18 %);
  · reverb sembrada, saturación de master, tartamudeo glitch al final de los versos 2 y 4; loudnorm −11 LUFS.
Escribe la entrega en una carpeta nueva y exclusiva: cuento-en-siete-s1910-<hash12>/ (m4a, wav, receta, mediciones).
    python mezcla.py <carpeta-de-render>
"""
import datetime, hashlib, json, math, os, subprocess, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve, resample_poly, butter, sosfiltfilt
import sintes as SN

AQUI = os.path.dirname(os.path.abspath(__file__)); RUN = sys.argv[1]; SR = 48000
P = json.load(open(os.path.join(RUN, 'partitura.json'), encoding='utf-8'))
N = int(P['duracion'] * SR); S = P['semicorchea']; C = P['compases']
SECS = {}
for c in C: a, z = SECS.get(c[2], (c[0] * S, 0)); SECS[c[2]] = (a, (c[0] + c[1]) * S)
SECS['VI'] = (SECS['VI'][0], P['duracion'])


def panear(y, p): a = (p + 1) * math.pi / 4; return np.stack([y * math.cos(a), y * math.sin(a)], 1)
def leer(nombre, estereo):
    x = np.fromfile(os.path.join(RUN, nombre + '.f32'), dtype=np.float32).astype(float)
    x = x.reshape(-1, 2) if estereo else x
    out = np.zeros((N, 2) if estereo else N); out[:min(N, len(x))] = x[:N]; return out
def ancho(y, p=0.0, ms=11):
    """mono → estéreo ancho: el lado derecho llega unos ms después (Haas), un poco hacia p"""
    d = int(ms / 1000 * SR); r = np.concatenate([np.zeros(d), y[:-d]]); return np.stack([y * (1 - .3 * p), r * (1 + .3 * p)], 1) * .7
def filtro(x, tipo, fc, orden=2): return sosfiltfilt(butter(orden, fc, btype=tipo, fs=SR, output='sos'), x, axis=0)
def mono(x): return x.mean(1) if x.ndim == 2 else x
def estereo(x, p=0.0): return x if x.ndim == 2 else panear(x, p)

capas = {}
WEB = ['pluck', 'marimba', 'berimbau', 'berimbau-coro', 'arpaboca', 'arpaboca-coro', 'teponaztli', 'bateria', 'bateria-frito', 'bajo']
for c in WEB: capas[c] = leer(c, True)
for c, p in [('sax', -.18), ('aves', .5), ('agua', -.3), ('waterphone', .35), ('gong', 0), ('trombon', 0), ('tambor', -.25), ('barra', .15), ('vozagua', -.45)]:
    capas[c] = panear(leer(c, False), p)
crudo_aves_coro = leer('aves-coro', False)
sab = leer('sabina-soprano', True); sab_baja = leer('sabina-baja', True)

# ── sintes ──
print('sintes…', flush=True)
capas['espectro'] = ancho(SN.espectro(P, N), 0, 17)
capas['sinte'] = ancho(SN.sinte_lead(P['sinte'], N, P['semilla']), .3, 9)
voces_coro = {v: P['coro']['III'][v] + P['coro']['V'][v] for v in 'SATB'}
sinte_coro = SN.sinte_coro(voces_coro, N, P['semilla'] + 1)
sub = SN.sub808(P['sub'], N); capas['sub'] = np.stack([sub, sub], 1) * math.sqrt(.5)
# v5: el 808 sucio de hyperpop: el mismo sub saturado, sólo de 110 a 320 Hz (sus armónicos 3–5). El sub limpio se queda abajo de
# 80 Hz; este llena el hueco de 120–250 Hz que dejaban los vocoders en los coros
sucio = filtro(np.tanh(5 * sub), 'bandpass', (110, 320), 2); capas['808-sucio'] = np.stack([sucio, sucio], 1) * math.sqrt(.5)

# ── el coro de vocoders ──
print('vocoders…', flush=True)
mod = mono(sab) + .7 * mono(sab_baja)
def voc(car, **kw): return SN.vocoder(mod, car, **kw)
capas['voc-pajaro'] = panear(voc(crudo_aves_coro, consonantes=.25), .45)
capas['voc-berimbau'] = panear(voc(mono(capas['berimbau-coro']), suaviza=1, consonantes=.2), -.3)    # el berimbau no se suaviza: su golpe es el ritmo
capas['voc-arpa'] = panear(voc(mono(capas['arpaboca-coro']), consonantes=.2), .2)
capas['voc-sinte'] = ancho(voc(sinte_coro, consonantes=.4), 0, 13)
capas['aves-coro'] = panear(crudo_aves_coro, .6)                                    # el pájaro también canta sin vocoder, atrás
capas['sabina'] = sab + .6 * sab_baja
# chops de hyperpop: antes de cada verso del V, la primera sílaba de Sabina una octava arriba, en tresillos de semicorchea
chop = np.zeros((N, 2)); sopV = P['coro']['V']['S']
for verso in range(4):
    e = sopV[12 * verso]; a = int(e['t'] * SR); L = int(S * 2 / 3 * SR)
    trozo = resample_poly(sab[a:a + 2 * L], 1, 2, axis=0)[:L]; f = int(.003 * SR); w = np.ones(L); w[:f] = np.linspace(0, 1, f); w[-f:] = np.linspace(1, 0, f)
    for j in range(6):
        i = a - int((6 - j) * S * 2 / 3 * SR)
        if i > 0: chop[i:i + L] += trozo * w[:, None] * (.55 + .08 * j) * np.array([[1 - .5 * (j % 2), .5 + .5 * (j % 2)]])
capas['chops'] = chop
del capas['berimbau-coro'], capas['arpaboca-coro']

# ── igualar por nivel activo y llevar cada capa a su lugar (dB) ──
# v2 (medido en la v1): el coro de vocoders quedaba a −8/−12 dB contra la mezcla donde suena y el coro se hundía en sub (20–60 Hz = −6 dB
# del total): vocoders +2/+3, voz de agua +2, Sabina +3; sub −3, batería −1; el sinte +1 para emparejar el dúo
NIVEL = {'bateria': -4, 'bateria-frito': -7, 'sub': -7, '808-sucio': -12, 'bajo': -8, 'pluck': -7, 'marimba': -9, 'berimbau': -10, 'teponaztli': -11, 'arpaboca': -8,
         'sax': -2, 'sinte': -2, 'aves': -9, 'agua': -12, 'waterphone': -11, 'gong': -9, 'trombon': -6, 'tambor': -6, 'barra': -12, 'espectro': -6,
         'vozagua': -3, 'voc-pajaro': -1, 'voc-berimbau': -4, 'voc-arpa': -3, 'voc-sinte': -1, 'aves-coro': -14, 'sabina': -6, 'chops': -8}
medidas = {}
def activo(x):
    n = len(x) // 2400 * 2400; m = np.sqrt(np.mean(x[:n].reshape(-1, 2400, 2) ** 2, axis=(1, 2)))
    v = m[m > m.max() * .03]; return float(np.sqrt(np.mean(v ** 2))) if len(v) else 0.0
for c, x in capas.items():
    a = activo(x); medidas[c] = dict(activo_db=round(20 * math.log10(a + 1e-12), 1)); assert a > 1e-7, f'la capa {c} está muda'
    capas[c] = x * (10 ** ((-20 + NIVEL[c]) / 20) / a)

# ── cada quien su piso: el sub abajo de 80 Hz, el bajo de 45 a 400, lo demás con su pasa altos ──
FILTROS = {'sub': ('lowpass', 80, 4), 'bajo': ('highpass', 45, 2), 'pluck': ('highpass', 180, 2), 'marimba': ('highpass', 110, 2), 'berimbau': ('highpass', 120, 2),
           'teponaztli': ('highpass', 110, 2), 'sax': ('highpass', 110, 2), 'sinte': ('highpass', 140, 2), 'voc-pajaro': ('highpass', 200, 2),
           'voc-berimbau': ('highpass', 130, 2), 'voc-arpa': ('highpass', 90, 2), 'voc-sinte': ('highpass', 110, 2), 'vozagua': ('highpass', 150, 2),
           'sabina': ('highpass', 160, 2), 'chops': ('highpass', 300, 2), 'aves': ('highpass', 400, 2), 'aves-coro': ('highpass', 400, 2), 'barra': ('highpass', 150, 2)}
for c, (tipo, fc, o) in FILTROS.items(): capas[c] = filtro(capas[c], tipo, fc, o)
# el arpa de boca y el trombón conservan su fundamental de Mi (es el bordón del espectro): no se filtran
# el sax del modelo es delgado: un poco de cuerpo (200–600 Hz) y de aire arriba
capas['sax'] = capas['sax'] + .25 * filtro(capas['sax'], 'bandpass', (220, 650)) + .2 * filtro(capas['sax'], 'highpass', 2500)

# ── sidechain desde la partitura ──
duck = np.ones(N)
for e in P['web']['bateria']:
    if e.get('pieza') != 'kick': continue
    sec = next((c[2] for c in reversed(C) if c[0] * S <= e['t'] + 1e-6), 'I'); prof = .5 if sec in ('III', 'V') else .18
    i = int(e['t'] * SR); L = min(int(.3 * SR), N - i); duck[i:i + L] = np.minimum(duck[i:i + L], 1 - prof * np.exp(-np.arange(L) / (.1 * SR)))
duck_sub = np.ones(N)
for e in P['web']['bateria']:
    if e.get('pieza') == 'kick': i = int(e['t'] * SR); L = min(int(.18 * SR), N - i); duck_sub[i:i + L] = np.minimum(duck_sub[i:i + L], 1 - .6 * np.exp(-np.arange(L) / (.05 * SR)))
SIN_DUCK = {'bateria', 'bateria-frito', 'sub', '808-sucio'}

# ── reverb sembrada (IR estéreo 2.2 s) ──
rg = np.random.default_rng(P['semilla']); L = int(2.2 * SR); ir = rg.standard_normal((L, 2)) * np.exp(-np.arange(L) / SR * 2.8)[:, None]; ir[:int(.014 * SR)] = 0; ir /= np.sqrt((ir ** 2).sum(0))
ENVIO = {'aves': .4, 'aves-coro': .45, 'agua': .3, 'waterphone': .5, 'gong': .35, 'espectro': .3, 'trombon': .2, 'arpaboca': .2, 'vozagua': .3, 'voc-pajaro': .3,
         'voc-arpa': .25, 'voc-sinte': .18, 'voc-berimbau': .12, 'sabina': .25, 'sax': .16, 'sinte': .12, 'pluck': .08, 'marimba': .1, 'tambor': .15, 'barra': .3}
seco = np.zeros((N, 2)); envio = np.zeros((N, 2))
for c, x in capas.items():
    x = (x * duck_sub[:, None] if c in ('sub', '808-sucio') else x) if c in SIN_DUCK else x * duck[:, None]; seco += x
    if c in ENVIO: envio += x * ENVIO[c]
reverb = np.stack([fftconvolve(envio[:, k], ir[:, k])[:N] for k in range(2)], 1)
mezcla = seco + reverb * .5
pre = mezcla.copy()
# ── master: saturación y glitch ──
mezcla /= np.abs(mezcla).max(); mezcla = np.tanh(2.0 * mezcla) / np.tanh(2.0)
for t0 in P['glitch']:
    ini = t0; corte = mezcla[int((ini - S) * SR):int(ini * SR)].copy()
    for j in range(4):                                  # las últimas cuatro semicorcheas se vuelven la misma, cada vez más aguda
        z = resample_poly(corte, 4, 4 + j, axis=0) if j else corte; i = int((ini + j * S) * SR); n = min(len(z), int(S * SR), N - i)
        mezcla[i:i + n] = z[:n] * (1 - .1 * j)
wav = os.path.join(RUN, 'mezcla.wav'); wavfile.write(wav, SR, (mezcla * .95).astype(np.float32))

# ── entrega: carpeta nueva y exclusiva, con hash (audio + partitura + código + nonce) ──
codigo = b''.join(open(os.path.join(AQUI, f), 'rb').read() for f in ('partitura.py', 'sintes.py', 'mezcla.py', 'render_node.cjs', 'render_web.cjs', 'render_voz.cjs'))
nonce = os.urandom(16).hex(); run = hashlib.sha256(mezcla.astype(np.float32).tobytes() + json.dumps(P).encode() + codigo + nonce.encode()).hexdigest(); h = run[:12]
nombre = f'cuento-en-siete-s{P["semilla"]}-{h}'; out = os.path.join(AQUI, nombre); os.makedirs(out, exist_ok=False)
base = os.path.join(out, nombre)
subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', wav, '-af', 'loudnorm=I=-11:TP=-1:LRA=9', '-ar', str(SR), '-c:a', 'pcm_s16le', base + '.wav'], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', base + '.wav', '-c:a', 'aac', '-b:a', '192k', base + '.m4a'], check=True)
_, fin = wavfile.read(base + '.wav'); fin = fin.astype(float) / 32768
secciones = {k: round(20 * math.log10(np.sqrt(np.mean(fin[int(a * SR):int(z * SR)] ** 2)) + 1e-12), 1) for k, (a, z) in SECS.items()}
# lo que cuenta: cada capa contra la mezcla donde suena (ventanas de 50 ms)
W = int(.05 * SR); nW = N // W; mez_v = np.sqrt(np.mean(pre[:nW * W].reshape(nW, W, 2) ** 2, axis=(1, 2)))
for c, x in capas.items():
    xv = np.sqrt(np.mean((x if c in SIN_DUCK else x * duck[:, None])[:nW * W].reshape(nW, W, 2) ** 2, axis=(1, 2))); act = xv > xv.max() * .1
    medidas[c]['contra_mezcla_db'] = round(20 * math.log10(np.sqrt(np.mean(xv[act] ** 2)) / np.sqrt(np.mean(mez_v[act] ** 2)) + 1e-12), 1) if act.any() else None
# bandas por sección (¿dónde se amontona?)
BANDAS = [(20, 60), (60, 120), (120, 250), (250, 500), (500, 1000), (1000, 2000), (2000, 4000), (4000, 8000), (8000, 16000)]
def bandas(x):
    X = np.abs(np.fft.rfft(x.mean(1))) ** 2; f = np.fft.rfftfreq(len(x), 1 / SR); tot = X.sum()
    return [round(10 * math.log10(X[(f >= a) & (f < b)].sum() / tot + 1e-12), 1) for a, b in BANDAS]
por_banda = {k: bandas(fin[int(a * SR):int(z * SR)]) for k, (a, z) in SECS.items()}
receta = dict(titulo=P['titulo'], semilla=P['semilla'], ejecucion=run, nonce=nonce, fecha=datetime.date.today().isoformat(), instrumentos=P['instrumentos'],
              niveles=NIVEL, envios=ENVIO, filtros=FILTROS, secciones_rms_db=secciones, bandas_hz=BANDAS, bandas_por_seccion_db=por_banda, capas=medidas,
              m4a_sha256=hashlib.sha256(open(base + '.m4a', 'rb').read()).hexdigest(), wav_sha256=hashlib.sha256(open(base + '.wav', 'rb').read()).hexdigest(),
              render=os.path.relpath(RUN, AQUI).replace('\\', '/'))
with open(os.path.join(out, 'receta.json'), 'x', encoding='utf-8') as f: json.dump(receta, f, ensure_ascii=False, indent=1)
with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as f: json.dump(P, f, ensure_ascii=False)
np.save(os.path.join(RUN, 'duck.npy'), duck[::480])
# por grupos: cada familia contra todo lo demás, sección por sección (¿el coro se lee en el coro? ¿el dúo en el dúo?)
GRUPOS = dict(coro=['voc-pajaro', 'voc-sinte', 'voc-arpa', 'voc-berimbau', 'vozagua', 'sabina', 'chops', 'aves-coro'], ritmo=['bateria', 'bateria-frito', 'sub', '808-sucio', 'bajo'],
              duo=['sax', 'sinte'], invencion=['pluck', 'marimba', 'berimbau', 'teponaztli', 'tambor', 'barra'],
              resonadores=['espectro', 'trombon', 'gong', 'waterphone', 'arpaboca'], aves_agua=['aves', 'agua'])
grupos = {}
for k, (a, z) in SECS.items():
    i, j = int(a * SR), int(z * SR); tot = pre[i:j]; fila = {}
    for g, cs in GRUPOS.items():
        x = sum((capas[c] if c in SIN_DUCK else capas[c] * duck[:, None])[i:j] for c in cs if c in capas); resto = tot - x
        ex, er = np.mean(x ** 2), np.mean(resto ** 2)
        if ex > 1e-10: fila[g] = round(10 * math.log10(ex / (er + 1e-14)), 1)
    grupos[k] = fila
receta['grupos_contra_resto_db'] = grupos
json.dump(receta, open(os.path.join(out, 'receta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(out); print('secciones (rms dB):', secciones)
for k, f in grupos.items(): print(f'  {k:4} grupo contra el resto:', '  '.join(f'{g} {v:+.1f}' for g, v in f.items()))
for k, v in por_banda.items(): print(f'  {k:4}', ' '.join(f'{x:6.1f}' for x in v))
for c, m in sorted(medidas.items(), key=lambda kv: -(kv[1]['contra_mezcla_db'] or -99)): print(f'  {c:14} {m["contra_mezcla_db"]:6.1f} dB contra la mezcla donde suena')
