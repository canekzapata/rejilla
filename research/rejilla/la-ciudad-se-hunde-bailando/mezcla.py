"""La ciudad se hunde bailando — mezcla.

EL DISCO (tiempo de disco): güiro, conga, campana, shaker y el dembow (navegador), el bajo y el teclado (Python), el lead, el coro y
los chops (Sabina), un coro sintético y el sub. El dembow pasa por EL TAPETE DE TALBOT en III (τ = 1/3: el 3-3-2 se vuelve tres
copias corridas un sexto, un medio y cinco sextos: se adelanta solo; luego τ = 1/2). Todo el disco se REBAJA con el varispeed de la
partitura: la ciudad se hunde, el disco baja de velocidad (tempo y tono juntos).
EN VIVO (tiempo real): el MC (con EL ECO DEL VALLE: sus saludos rebotan en los conos vecinos a su distancia real, más oscuros
mientras más lejos), las sirenas (una por metro) y el crujido del vinilo, que crece con lo rebajado.
LA RADIO DE ONDA CORTA en tres tramos: el intro (la perilla busca entre nuestras canciones, la locutora, la señal horaria y la estática,
y cae en «¡esto es Sonido Texcoco!»), una vuelta en III (se va a otra estación y regresa) y el final (la canción se oye por la radio y
la perilla se la lleva a la estática).
Procesa capa por capa y mide cada grupo contra lo demás en cada sección (tiempo real). loudnorm −14 LUFS.
    python mezcla.py <carpeta-de-render> [--medir]
"""
import datetime, hashlib, json, math, os, subprocess, sys
from fractions import Fraction
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve, butter, sosfiltfilt
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI); import sintes10 as S10
sys.path.insert(0, os.path.join(AQUI, '..', 'cuento-en-siete')); import sintes as SN
sys.path.insert(0, os.path.join(AQUI, '..', 'tapete-de-talbot')); import tapete as TP
sys.path.insert(0, os.path.join(AQUI, '..', 'primero-sueno-en-el-cenote')); import sintes7 as S7
RUN = sys.argv[1]; SR = 48000
P = json.load(open(os.path.join(RUN, 'partitura.json'), encoding='utf-8'))
N = int(P['duracion'] * SR); SECS = {s['num']: (s['t_real'], s['t1_real']) for s in P['secciones']}; SECD = {s['num']: (s['t'], s['t1']) for s in P['secciones']}

def panear(y, p): a = (p + 1) * math.pi / 4; return np.stack([y * math.cos(a), y * math.sin(a)], 1).astype(np.float32)
def leer(nombre, estereo):
    x = np.fromfile(os.path.join(RUN, nombre + '.f32'), dtype=np.float32)
    x = x.reshape(-1, 2) if estereo else x
    out = np.zeros((N, 2) if estereo else N, np.float32); out[:min(N, len(x))] = x[:N]; return out
def filtro(x, tipo, fc, orden=2): return sosfiltfilt(butter(orden, fc, btype=tipo, fs=SR, output='sos'), x, axis=0).astype(np.float32)
def mono(x): return x.mean(1) if x.ndim == 2 else x
def ventana(tramos):
    w = np.zeros(N)
    for a, z in tramos: w[int(a * SR):int(z * SR)] = 1
    k = int(.08 * SR); return np.convolve(w, np.ones(k) / k, 'same').astype(np.float32)
def activo(x):
    n = len(x) // 2400 * 2400; m = np.sqrt(np.mean(x[:n].reshape(-1, 2400, 2).astype(float) ** 2, axis=(1, 2)))
    v = m[m > m.max() * .03]; return float(np.sqrt(np.mean(v ** 2))) if len(v) else 0.0

# ── el varispeed: tiempo real → posición del disco ──
VS = np.array(P['varispeed']); t_real = np.arange(N) / SR; r_fin = P['razon_final']
pos = np.interp(t_real, VS[:, 1], VS[:, 0]); antes = t_real < P['inicio_disco']; despues = t_real > P['fin_disco']
pos[despues] = P['disco_s'] + (t_real[despues] - P['fin_disco']) * r_fin; pos = (pos * SR).astype(np.float64)
def rebajar(x):
    """x en tiempo de disco (desde 0) → tiempo real."""
    idx = np.arange(len(x)); out = np.zeros_like(x)
    if x.ndim == 2:
        for k in range(2): out[:, k] = np.interp(pos, idx, x[:, k], right=0)
    else: out = np.interp(pos, idx, x, right=0).astype(np.float32)
    out[antes] = 0; return out.astype(np.float32)

DISCO = ['guiro', 'conga', 'campana', 'shaker', 'bateria808', 'bateria-frito', 'bajo', 'sub', 'teclado', 'pad', 'lead', 'coro', 'chops']
VIVO = ['mc', 'mc-eco', 'sirenas', 'vinilo']
# r2: los saludos del MC no sonaban donde iban (eventos sin ordenar; corregido en la partitura). r1 (medido por grupo): la cumbia tapaba (+4 en I), el MC −13 a −17 (+5), las voces −9 a −11 en I y V (+3), el vinilo subía de más al final (−6)
NIVEL = {'guiro': -11, 'conga': -10, 'campana': -15, 'shaker': -18, 'bateria808': -2, 'bateria-frito': -10, 'bajo': -6, 'sub': -9, 'teclado': -8, 'pad': -15,
         'lead': 3, 'coro': 0, 'chops': -3, 'mc': 4, 'mc-eco': -12, 'sirenas': -10, 'vinilo': -31}
FILTROS = {'sub': ('lowpass', 120), 'lead': ('highpass', 140), 'coro': ('highpass', 160), 'chops': ('highpass', 250), 'mc': ('highpass', 160), 'shaker': ('highpass', 2500), 'pad': ('lowpass', 2500)}
SIN_DUCK = {'bateria808', 'sub', 'mc', 'mc-eco', 'sirenas', 'lead', 'vinilo'}
SALA = {'lead': .2, 'coro': .3, 'chops': .25, 'teclado': .2, 'campana': .15, 'mc': .12, 'sirenas': .3, 'pad': .3}
GRUPOS = dict(cumbia=['guiro', 'conga', 'campana', 'shaker', 'bajo', 'teclado', 'pad'], dembow=['bateria808', 'bateria-frito', 'sub'], voces=['lead', 'coro', 'chops'],
              sonidero=['mc', 'mc-eco', 'sirenas', 'vinilo'], radio=['radio'])
GRUPO_DE = {c: g for g, cs in GRUPOS.items() for c in cs}
duck = np.zeros(N, np.float32) + 1
kicks = [e['t'] for e in P['web']['bateria808'] if e.get('pieza') == 'kick']
kreal = np.interp(np.array(kicks), VS[:, 0], VS[:, 1]) if kicks else []
for tk in kreal:
    i = int(tk * SR); L = min(int(.2 * SR), N - i); duck[i:i + L] = np.minimum(duck[i:i + L], 1 - .28 * np.exp(-np.arange(L) / (.06 * SR)))
talbot_info = {}

def capa(c):
    if c in ('guiro', 'conga', 'campana', 'shaker', 'bateria-frito'): return rebajar(leer(c, True))
    if c == 'bateria808':
        x = leer('bateria808', True); T = P['talbot']; Lp = int(round(T['ciclo'] * SR)); i0 = int(round(T['loop_desde'] * SR)); loop = x[i0:i0 + Lp].astype(float)
        a3 = SECD['III'][0]; xf = int(.05 * SR); tr = T['tramos']
        for (ta, tau), (tz, _) in zip(tr, tr[1:]):
            if tau == '0': continue
            z = TP.talbot(loop, Fraction(tau)); a, b = int(ta * SR), int(tz * SR); idx = (np.arange(a, b) - int(round(a3 * SR))) % Lp
            ww = np.ones(b - a); ww[:xf] = np.linspace(0, 1, xf); ww[-xf:] = np.linspace(1, 0, xf)
            x[a:b] = (x[a:b] * (1 - ww[:, None]) + z[idx] * ww[:, None]).astype(np.float32); talbot_info[tau] = TP.copias(Fraction(tau).numerator, Fraction(tau).denominator)[0]
        return rebajar(x)
    if c == 'bajo': return rebajar(panear(leer('bajo', False), 0))
    if c == 'sub': return rebajar(panear(np.tanh(2 * filtro(leer('bajo', False), 'lowpass', 90)), 0))
    if c == 'teclado': return rebajar(leer('teclado', True))
    if c == 'pad': return rebajar(panear(SN.sinte_coro(P['coros'], N, 5), 0))
    if c in ('lead', 'coro', 'chops'): return rebajar(leer('sabina-' + c, True))
    if c in ('mc', 'mc-eco'):
        m = mono(leer('sabina-mc', True)); m[:int(P['inicio_disco'] * SR)] = 0                 # en el intro el MC sólo se oye por la radio
        if c == 'mc': return panear(m, 0)
        y = np.zeros((N, 2), np.float32)
        for k, e in enumerate(P['ecos'][:3]):                                                    # el eco del valle: distancia real, más oscuro mientras más lejos
            d = int(e['retraso_s'] * SR); fc = max(700, 5000 * 1400 / e['dist_m']); g = 1400 / e['dist_m']
            if d < N: y[d:] += panear(filtro(m, 'lowpass', fc)[:N - d] * g, [-.6, .6, 0][k % 3])
        return y
    if c == 'sirenas': return leer('sirenas', True)
    if c == 'vinilo':
        prof = [[0, 0], [P['inicio_disco'], .25], [P['fin_disco'], .6], [P['duracion'], .35]]
        y = S7.vinilo(prof, N, 3); return y.astype(np.float32)
    raise KeyError(c)

seco = np.zeros((N, 2), np.float32); e1 = np.zeros((N, 2), np.float32); disco_bus = np.zeros(N, np.float32)
GS = {g: np.zeros((N, 2), np.float32) for g in GRUPOS}; medidas = {}
for c in DISCO + VIVO:
    x = capa(c); a = activo(x); medidas[c] = dict(activo_db=round(20 * math.log10(a + 1e-12), 1)); assert a > 1e-7, f'la capa {c} está muda'
    x = (x * (10 ** ((-20 + NIVEL[c]) / 20) / a)).astype(np.float32)
    if c in FILTROS: x = filtro(x, *FILTROS[c])
    if c not in SIN_DUCK: x *= duck[:, None]
    if c in DISCO: disco_bus += mono(x)
    GS[GRUPO_DE[c]] += x; seco += x
    if c in SALA: e1 += x * SALA[c]
    del x; print(' ', c, medidas[c]['activo_db'], flush=True)

# ── la radio de onda corta (tres tramos) ──
R = P['radio']; est = R['estaciones']; radio = np.zeros((N, 2), np.float32); wfin = np.ones(N, np.float32); voz_radio = mono(leer('sabina-radio', True)); mc_crudo = mono(leer('sabina-mc', True))
nivel_radio = 10 ** ((-20 - 3) / 20)
for nombre, tramo in (('intro', R['intro']), ('interludio', R['interludio']), ('final', R['final'])):
    a, b = int(tramo['desde'] * SR), min(N, int(tramo['hasta'] * SR)); n = b - a; ests = []
    for k, e in enumerate(est):
        if e['tipo'] in ('musica', 'horaria'): au = leer(f'estacion{k}', False)[a:b]
        elif e['tipo'] == 'voz': au = voz_radio[a:b]
        else: au = (mc_crudo[a:b] * 3 + disco_bus[a:b] * 2) if nombre == 'intro' else disco_bus[a:b] * 3
        au = au / (np.sqrt(np.mean(au ** 2)) + 1e-9) * .2
        ests.append(dict(f=e['f'], audio=au.astype(float), nivel=e['nivel'], tipo=e['tipo'], fading=0 if e['tipo'] == 'sonidero' else 1))
    y, inf = S10.radio(ests, tramo['dial'], n, semilla=len(nombre))
    env = np.ones(n); fx = int(.4 * SR); env[:fx] = np.linspace(0, 1, fx); env[-fx:] = np.linspace(1, 0, fx)
    radio[a:b] += panear(y * env * nivel_radio / (np.sqrt(np.mean(y ** 2)) + 1e-9) * .35, 0)
    if nombre == 'interludio':                                                               # mientras la perilla se va, el disco se esconde
        w = np.ones(N, np.float32); w[a:b] = 1 - .85 * np.sin(np.pi * np.arange(n) / n) ** .6; seco *= w[:, None]; wfin *= w
    if nombre == 'final':
        w = np.ones(N, np.float32); fz = a + int(5 * SR); w[fz:] = 0; w[a:fz] = np.linspace(1, 0, fz - a) ** 2; seco *= w[:, None]; wfin *= w
for g in GS: GS[g] *= wfin[:, None]                                            # los grupos llevan los mismos fundidos que la mezcla
seco += radio; GS['radio'] += radio
rg = np.random.default_rng(P['semilla'])
L = int(2.2 * SR); ir = rg.standard_normal((L, 2)) * np.exp(-np.arange(L) / SR * 2.8)[:, None]; ir[:int(.015 * SR)] = 0; ir /= np.sqrt((ir ** 2).sum(0))
pre = seco
for k in range(2): pre[:, k] += (fftconvolve(e1[:, k], ir[:, k])[:N] * .4).astype(np.float32)
del e1
grupos = {}
for k, (a, z) in list(SECS.items()) + [('radio-intro', (0, P['inicio_disco'])), ('final', (P['fin_disco'] - 6, P['duracion']))]:
    i, j = int(a * SR), int(z * SR); tot = pre[i:j]; fila = {}
    for g in GRUPOS:
        x = GS[g][i:j]; ex, er = np.mean(x.astype(float) ** 2), np.mean((tot - x).astype(float) ** 2)
        if ex > 1e-10: fila[g] = round(10 * math.log10(ex / (er + 1e-14)), 1)
    grupos[k] = fila
del GS
if '--medir' in sys.argv:
    [print(f'  {k:12}', '  '.join(f'{g} {v:+.1f}' for g, v in fl.items())) for k, fl in grupos.items()]; sys.exit()
mezcla = pre / np.abs(pre).max(); mezcla = np.tanh(1.5 * mezcla) / np.tanh(1.5)
wav = os.path.join(RUN, 'mezcla.wav'); wavfile.write(wav, SR, (mezcla * .95).astype(np.float32))
CODIGO = ('partitura.py', 'sintes10.py', 'mezcla.py', 'render_py.py', 'render_web.cjs', 'render_voz.cjs')
codigo = b''.join(open(os.path.join(AQUI, f), 'rb').read() for f in CODIGO)
nonce = os.urandom(16).hex(); run = hashlib.sha256(mezcla.astype(np.float32).tobytes() + json.dumps(P).encode() + codigo + nonce.encode()).hexdigest(); h = run[:12]
nombre = f'la-ciudad-se-hunde-bailando-s{P["semilla"]}-{h}'; out = os.path.join(AQUI, nombre); os.makedirs(out, exist_ok=False); base = os.path.join(out, nombre)
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
              niveles=NIVEL, sala=SALA, filtros=FILTROS, talbot_copias=talbot_info, secciones_rms_db=secciones, lufs_integrado=lufs, bandas_hz=BANDAS, bandas_por_seccion_db=por_banda,
              grupos_contra_resto_db=grupos, capas=medidas, m4a_sha256=hashlib.sha256(open(base + '.m4a', 'rb').read()).hexdigest(),
              wav_sha256=hashlib.sha256(open(base + '.wav', 'rb').read()).hexdigest(), render=os.path.relpath(RUN, AQUI).replace('\\', '/'))
with open(os.path.join(out, 'receta.json'), 'x', encoding='utf-8') as fo: json.dump(receta, fo, ensure_ascii=False, indent=1)
with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as fo: json.dump(P, fo, ensure_ascii=False)
print(out); print('secciones (rms dB):', secciones, '· LUFS', lufs)
[print(f'  {k:12}', '  '.join(f'{g} {v:+.1f}' for g, v in fl.items())) for k, fl in grupos.items()]
for k, v in por_banda.items(): print(f'  {k:4}', ' '.join(f'{x:6.1f}' for x in v))
