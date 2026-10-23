"""Lo que la cinta olvida — mezcla.

1. LA BANDA DEL SONIDERO, en tiempo de cinta τ: las capas de render_web.cjs (acordeón, bajo, güiro, conga, campana, sirena, timbal,
   órgano), el requinto (render_node.cjs) y las voces de render_voz.cjs (la voz de sonidero por la bocina con su eco, el coro y los
   vocoders: Sabina modula al acordeón y al sinte del coral). Se nivelan por grupo y se mide su balance en τ.
2. LA CINTA DE MEANDRO (motor/cinta.py) la toca a la velocidad del río: rebaja, wow, flutter, cabeza, saturación, siseo.
3. LOS LAGOS: los dos últimos compases de las cuatro vueltas más sinuosas se quedan dando vueltas desde su corte hasta el final y se
   gastan (Basinski).
4. LO VIVO, en tiempo real: el cello con su eco de cinta (Arthur Russell), la voz viva, el vocoder del cello, la garganta de río, el
   agua y los pájaros.
Mide por grupo contra lo demás y por bandas en cada tramo del río; loudnorm −12 LUFS. Entrega en carpeta nueva:
lo-que-la-cinta-olvida-s26-<hash>/.
    python mezcla.py <carpeta-de-render> [--medir]
"""
import datetime, hashlib, json, math, os, subprocess, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve, butter, sosfiltfilt, sosfilt
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'cuento-en-siete')); sys.path.insert(0, os.path.join(AQUI, 'motor')); sys.path.insert(0, AQUI)
import sintes as SN, cinta as CI
import partitura as PT                                                      # el mismo mapa de velocidades que escribió la partitura
RUN = sys.argv[1]; SR = 48000
P = json.load(open(os.path.join(RUN, 'partitura.json'), encoding='utf-8'))
N = int(P['duracion'] * SR); NT = int(P['T_tau'] * SR)
VU = P['vueltas']; SECS = {'intro': (0, VU[0]['t0']), 'cumbia': (VU[0]['t0'], VU[3]['t1']), 'rebajada': (VU[4]['t0'], VU[6]['t1']), 'vivo': (VU[7]['t0'], P['fin_cinta']), 'coda': (P['fin_cinta'], P['duracion'] - 1)}
SECS_TAU = {'intro': (0, PT.t_(PT.INTRO)), 'cumbia': (PT.t_(VU[0]['b0']), PT.t_(VU[3]['b1'])), 'rebajada': (PT.t_(VU[4]['b0']), PT.t_(VU[6]['b1'])), 'vivo': (PT.t_(VU[7]['b0']), PT.t_(VU[-1]['b1']))}

def panear(y, p): a = (p + 1) * math.pi / 4; return np.stack([y * math.cos(a), y * math.sin(a)], 1)
def leer(nombre, estereo, n):
    x = np.fromfile(os.path.join(RUN, nombre + '.f32'), dtype=np.float32).astype(float)
    x = x.reshape(-1, 2) if estereo else x
    out = np.zeros((n, 2) if estereo else n); out[:min(n, len(x))] = x[:n]; return out
def ancho(y, p=0.0, ms=11): d = int(ms / 1000 * SR); r = np.concatenate([np.zeros(d), y[:-d]]); return np.stack([y * (1 - .3 * p), r * (1 + .3 * p)], 1) * .7
def filtro(x, tipo, fc, orden=2): return sosfiltfilt(butter(orden, fc, btype=tipo, fs=SR, output='sos'), x, axis=0)
def mono(x): return x.mean(1) if x.ndim == 2 else x
def ventana(tramos, n):
    w = np.zeros(n)
    for a, z in tramos: w[int(a * SR):int(z * SR)] = 1
    k = int(.08 * SR); return np.convolve(w, np.ones(k) / k, 'same')
def activo(x):
    n = len(x) // 2400 * 2400; m = np.sqrt(np.mean(x[:n].reshape(-1, 2400, 2) ** 2, axis=(1, 2)))
    v = m[m > m.max() * .03]; return float(np.sqrt(np.mean(v ** 2))) if len(v) else 0.0
def eco(x, ms, fb, corte, n=8):
    """eco de cinta: cada vuelta más oscura"""
    d = int(ms / 1000 * SR); y = x.copy(); v = x.copy()
    for _ in range(n): v = np.concatenate([np.zeros((d,) + x.shape[1:]), v[:-d]]) * fb; v = filtro(v, 'lowpass', corte); y = y + v
    return y
def grupos_de(capas, G, secs, total, sin_duck=None):
    res = {}
    for k, (a, z) in secs.items():
        i, j = int(a * SR), int(z * SR); tot = total[i:j]; fila = {}
        for g, cs in G.items():
            x = sum(capas[c][i:j] for c in cs if c in capas); ex, er = np.mean(x ** 2), np.mean((tot - x) ** 2)
            if ex > 1e-10: fila[g] = round(10 * math.log10(ex / (er + 1e-14)), 1)
        res[k] = fila
    return res

# ═════════ 1 · la banda en τ ═════════
banda = {}
for c in ['acordeon', 'bajo', 'guiro', 'conga', 'campana', 'sirena', 'timbal', 'organo']: banda[c] = leer(c, True, NT)
banda['requinto'] = panear(leer('requinto', False, NT), .35)
son = mono(leer('sabina-sonidero', True, NT)); son = np.tanh(2.5 * filtro(son, 'bandpass', [300, 4200]) / (np.abs(son).max() + 1e-9))   # la bocina del sonidero
banda['sonidero'] = eco(panear(son, 0), 375, .45, 2500, 6)                                                                          # y su eco
coro = leer('sabina-coro', True, NT); mod = mono(coro)
ven = ventana([(e['t'] - .05, e['t'] + e['dur'] + .3) for e in sum(P['coros'].values(), [])] + [(e['t'] - .05, e['t'] + e['dur'] + .3) for e in P['sabina'][1]['eventos']], NT)
banda['coro'] = coro
banda['voc-acordeon'] = ancho(SN.vocoder(mod, mono(banda['acordeon']) * ven, consonantes=.35), -.2, 13)
banda['voc-coro'] = ancho(SN.vocoder(mod, SN.sinte_coro(P['coros'], NT, 3), consonantes=.4), .2, 17)
# r1 (medido en τ): el bajo tapaba (+0.4 contra lo demás en lo vivo, −1.1 en lo rebajado): −3; las voces de la cumbia −5.8: +2
NIVEL_B = {'acordeon': -5, 'bajo': -7, 'guiro': -9, 'conga': -9, 'campana': -13, 'sirena': -9, 'timbal': -10, 'organo': -11, 'requinto': -5,
           'sonidero': -3, 'coro': -2, 'voc-acordeon': -6, 'voc-coro': -6}
medidas = {}
for c, x in banda.items():
    a = activo(x); medidas[c] = dict(activo_db=round(20 * math.log10(a + 1e-12), 1)); assert a > 1e-7, f'la capa {c} está muda'
    banda[c] = x * (10 ** ((-20 + NIVEL_B[c]) / 20) / a)
for c, (tipo, fc) in {'bajo': ('lowpass', 900), 'guiro': ('highpass', 1200), 'campana': ('highpass', 500), 'voc-acordeon': ('highpass', 150), 'voc-coro': ('highpass', 150), 'coro': ('highpass', 150)}.items():
    banda[c] = filtro(banda[c], tipo, fc)
rg = np.random.default_rng(P['semilla']); L = int(2.2 * SR); ir = rg.standard_normal((L, 2)) * np.exp(-np.arange(L) / SR * 2.6)[:, None]; ir[:int(.015 * SR)] = 0; ir /= np.sqrt((ir ** 2).sum(0))
ENV_B = {'acordeon': .15, 'coro': .25, 'voc-acordeon': .2, 'voc-coro': .2, 'organo': .2, 'requinto': .15, 'conga': .08, 'timbal': .1}
sala = sum(banda[c] * e for c, e in ENV_B.items())
banda_tau = sum(banda.values()) + np.stack([fftconvolve(sala[:, k], ir[:, k])[:NT] for k in range(2)], 1) * .5
GB = dict(ritmo=['guiro', 'conga', 'campana', 'timbal'], bajo=['bajo'], acordeon=['acordeon', 'organo', 'requinto'], voces=['sonidero', 'coro', 'voc-acordeon', 'voc-coro'])
grupos_tau = grupos_de(banda, GB, SECS_TAU, banda_tau)

# ═════════ 2 · la cinta de meandro ═════════
print('la cinta…', flush=True)
def curv(t):
    for vu in VU:
        if t < vu['t1']: return min(1, max(0, (vu['sinuosidad'] - 1.4) / 1.7))
    return .3
cinta, vt = CI.tocar(banda_tau, PT.MP, N, curv, P['semilla'])
cinta[int(P['fin_cinta'] * SR):] *= np.exp(-np.arange(N - int(P['fin_cinta'] * SR)) / (.25 * SR))[:, None]      # la cinta se detiene

# ═════════ 3 · los lagos de herradura ═════════
print('los lagos…', flush=True)
capas = {'cinta': cinta}; lagos_med = {}
for k, lg in enumerate(P['lagos']):
    capas[f'lago{k + 1}'], lagos_med[lg['vuelta']] = CI.lago(cinta, lg['t0'], lg['t1'], P['duracion'] - 1, P['semilla'] + k, final_db=-10)

# ═════════ 4 · lo vivo ═════════
ch = leer('chelo', False, N); capas['chelo'] = eco(panear(ch, -.15), 410, .5, 1800, 9)       # Arthur Russell: el eco de cinta
viva = leer('sabina-viva', True, N); capas['viva'] = viva
venv = ventana([(e['t'] - .05, e['t'] + e['dur'] + .3) for e in P['sabina'][2]['eventos']], N)
capas['voc-chelo'] = ancho(SN.vocoder(mono(viva), ch * venv, consonantes=.3), .25, 19)
capas['garganta'] = leer('garganta', True, N); capas['agua'] = ancho(leer('agua', False, N), -.3, 17); capas['aves'] = ancho(leer('aves', False, N), .4, 9)
# r1: en la coda los lagos quedaban −10.6 bajo lo vivo (la coda es de los lagos): se gastan menos (−10 dB al final, no −16) y la voz viva +2
NIVEL = {'cinta': -1, 'lago1': -9, 'lago2': -9, 'lago3': -9, 'lago4': -9, 'chelo': -6, 'viva': -1, 'voc-chelo': -8, 'garganta': -14, 'agua': -15, 'aves': -16}
for c, x in capas.items():
    a = activo(x); medidas[c] = dict(activo_db=round(20 * math.log10(a + 1e-12), 1)); assert a > 1e-7, f'la capa {c} está muda'
    capas[c] = x * (10 ** ((-20 + NIVEL[c]) / 20) / a)
for c, (tipo, fc) in {'chelo': ('highpass', 55), 'viva': ('highpass', 140), 'voc-chelo': ('highpass', 120), 'garganta': ('highpass', 60), 'aves': ('highpass', 1500)}.items(): capas[c] = filtro(capas[c], tipo, fc)
ENV = {'chelo': .25, 'viva': .3, 'voc-chelo': .3, 'garganta': .35, 'aves': .3, 'agua': .2, 'lago1': .2, 'lago2': .2, 'lago3': .2, 'lago4': .2}
ir2 = rg.standard_normal((int(3.5 * SR), 2)) * np.exp(-np.arange(int(3.5 * SR)) / SR * 1.5)[:, None]; ir2[:int(.03 * SR)] = 0; ir2 /= np.sqrt((ir2 ** 2).sum(0))
env = sum(capas[c] * e for c, e in ENV.items())
pre = sum(capas.values()) + np.stack([fftconvolve(env[:, k], ir2[:, k])[:N] for k in range(2)], 1) * .5
GRUPOS = dict(cinta=['cinta'], lagos=['lago1', 'lago2', 'lago3', 'lago4'], vivo=['chelo', 'viva', 'voc-chelo'], rio=['garganta', 'agua', 'aves'])
grupos = grupos_de(capas, GRUPOS, SECS, pre)
if '--medir' in sys.argv:
    print('en la cinta (τ):'); [print(f'  {k:9}', '  '.join(f'{g} {v:+.1f}' for g, v in fl.items())) for k, fl in grupos_tau.items()]
    print('en la canción:'); [print(f'  {k:9}', '  '.join(f'{g} {v:+.1f}' for g, v in fl.items())) for k, fl in grupos.items()]
    print('lagos (primera / última pasada):', {k: (m[0]['nivel_db'], m[-1]['nivel_db'], m[-1]['perdido'], len(m)) for k, m in lagos_med.items()})
    sys.exit()
mezcla = pre / np.abs(pre).max(); mezcla = np.tanh(1.4 * mezcla) / np.tanh(1.4)
wav = os.path.join(RUN, 'mezcla.wav'); wavfile.write(wav, SR, (mezcla * .95).astype(np.float32))
codigo = b''.join(open(os.path.join(AQUI, f), 'rb').read() for f in ('partitura.py', 'mezcla.py', 'render_node.cjs', 'render_web.cjs', 'render_voz.cjs', 'motor/cinta.py', 'motor/cuerda.js', 'motor/garganta_rio.js'))
nonce = os.urandom(16).hex(); run = hashlib.sha256(mezcla.astype(np.float32).tobytes() + json.dumps(P).encode() + codigo + nonce.encode()).hexdigest(); h = run[:12]
nombre = f'lo-que-la-cinta-olvida-s{P["semilla"]}-{h}'; out = os.path.join(AQUI, nombre); os.makedirs(out, exist_ok=False); base = os.path.join(out, nombre)
subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', wav, '-af', 'loudnorm=I=-12:TP=-1:LRA=12', '-ar', str(SR), '-c:a', 'pcm_s16le', base + '.wav'], check=True)
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
np.save(os.path.join(RUN, 'velocidad.npy'), vt[::480])
np.save(os.path.join(RUN, 'banda-tau.npy'), banda_tau.mean(1).astype(np.float32)); np.save(os.path.join(RUN, 'cinta.npy'), cinta.mean(1).astype(np.float32))
for k in range(len(P['lagos'])): np.save(os.path.join(RUN, f'lago{k + 1}.npy'), capas[f'lago{k + 1}'].mean(1).astype(np.float32))
receta = dict(titulo=P['titulo'], semilla=P['semilla'], terreno=P['terreno'], ejecucion=run, nonce=nonce, fecha=datetime.date.today().isoformat(), instrumentos=P['instrumentos'],
              niveles_banda=NIVEL_B, niveles=NIVEL, secciones_rms_db=secciones, lufs_integrado=lufs, bandas_hz=BANDAS, bandas_por_seccion_db=por_banda,
              grupos_en_la_cinta_db=grupos_tau, grupos_contra_resto_db=grupos, lagos=lagos_med, capas=medidas,
              m4a_sha256=hashlib.sha256(open(base + '.m4a', 'rb').read()).hexdigest(), wav_sha256=hashlib.sha256(open(base + '.wav', 'rb').read()).hexdigest(),
              render=os.path.relpath(RUN, AQUI).replace('\\', '/'))
with open(os.path.join(out, 'receta.json'), 'x', encoding='utf-8') as fo: json.dump(receta, fo, ensure_ascii=False, indent=1)
with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as fo: json.dump(P, fo, ensure_ascii=False)
print(out); print('secciones (rms dB):', secciones, '· LUFS', lufs)
print('en la cinta (τ):'); [print(f'  {k:9}', '  '.join(f'{g} {v:+.1f}' for g, v in fl.items())) for k, fl in grupos_tau.items()]
print('en la canción:'); [print(f'  {k:9}', '  '.join(f'{g} {v:+.1f}' for g, v in fl.items())) for k, fl in grupos.items()]
for k, v in por_banda.items(): print(f'  {k:9}', ' '.join(f'{x:6.1f}' for x in v))
