"""«una sola línea» · la mezcla de los noventa. Pistas del navegador (render/<et>-<pista>.wav, estéreo float32).

  sampler 1997   batería, bajo y los cortes de la voz aguda pasan por un sampler de 12 bits a 26 040 Hz sin filtro
                 antialias (S950/MPC: el alias es el brillo de la época)
  teléfono       Doina: 300-3400 Hz, 8 kHz, μ-law de 8 bits y el siseo de la línea
  vinilo         polvo (clics Poisson) y un siseo bajito todo el tiempo
  frenazo        «la línea baja a la mitad» (compás 26): la cinta se detiene en 0.7 s y el trip-hop vuelve a la mitad
  rebobinado     al reconectar (compás 40): los dos segundos anteriores, al revés y acelerando (pull-up de DJ)
  sin final      corte seco en el compás 56 (3 ms): «no hay línea de apagado»
Mide: bandas y voz contra resto por sección, el peor segundo, el tempo del break por sección (autocorrelación de los
golpes: 84 / 168) y los tonos del módem (425, 2100 Hz y el peine de 150 Hz).
    python mezcla.py b1 [--entregar]
"""
import hashlib, json, os, subprocess, sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, fftconvolve, resample_poly
AQUI = Path(__file__).resolve().parent; RENDER = AQUI / 'render'; SR = 48000
ET = sys.argv[1]; ENTREGAR = '--entregar' in sys.argv
C = json.loads(subprocess.run(['node', '-e', "require('./motor/cancion.js');const C=globalThis.Cancion;console.log(JSON.stringify({S:C.SECC,T:C.T,M:C.MAPA,N:C.COMPASES}))"],
                              capture_output=True, text=True, cwd=AQUI).stdout)
T = C['T']; FIN = int(C['N'] * T * SR)
# b1-v1 → v2: el sub quedaba a −3.7/−4.3 dB del total en los versos (sepultado, otra vez) y la voz de −0.4 a −2.5 bajo el resto
NIVEL = {'modem': (-22, .15), 'kit': (-16.5, .12), 'bajo': (-20.5, .05), 'rhodes': (-22, .25), 'cuerdas': (-25, .35),
         'ardilla': (-12.5, .18), 'grave': (-12.5, .15), 'telefono': (-15, .1)}
VOCES = ('ardilla', 'grave', 'telefono')
BANDAS = [('sub', None, 90), ('graves', 90, 300), ('medios', 300, 2000), ('presencia', 2000, 6000), ('aire', 6000, None)]


def banda(x, lo, hi, orden=4):
    sos = butter(orden, [lo, hi], 'band', fs=SR, output='sos') if lo and hi else butter(orden, lo, 'high', fs=SR, output='sos') if lo else butter(orden, hi, 'low', fs=SR, output='sos')
    return sosfilt(sos, x, axis=0)


def sampler1997(x, bits=12, sr2=26040):
    idx = np.floor(np.arange(len(x)) * sr2 / SR).astype(int); primero = np.searchsorted(idx, np.arange(idx[-1] + 1))
    held = x[primero][idx]                                                  # retención sin antialias: el alias brilla
    pk = np.abs(held).max() + 1e-12; q = 2 ** (bits - 1)
    return np.round(np.tanh(held / pk * 1.2) / np.tanh(1.2) * q) / q * pk


def telefono(x):
    m = banda(x.mean(axis=1), 300, 3400, 6); y = resample_poly(m, 1, 6); pk = np.abs(y).max() + 1e-12; mu = 255
    c = np.sign(y) * np.log1p(mu * np.abs(y / pk)) / np.log1p(mu); c = np.round(c * 127) / 127               # μ-law, 8 bits
    y = np.sign(c) * ((1 + mu) ** np.abs(c) - 1) / mu * pk; y = resample_poly(y, 6, 1)[:len(m)]
    y = y + banda(np.random.default_rng(8).standard_normal(len(y)) * pk * .004, 300, 3400, 2)
    return np.stack([y * .9, y * .75], 1)


def rms_activo(x):
    m = x.mean(axis=1); c = np.sqrt(np.mean(m[:len(m) // 4800 * 4800].reshape(-1, 4800) ** 2, axis=1)); v = c[c > c.max() * 10 ** (-35 / 20)]
    return np.sqrt(np.mean(v ** 2))


pistas = {}
for p in NIVEL:
    f = RENDER / f'{ET}-{p}.wav'
    if f.exists(): sr, x = wavfile.read(f); pistas[p] = x.astype(np.float64)
n = max(len(x) for x in pistas.values())
for p in pistas: pistas[p] = np.pad(pistas[p], ((0, n - len(pistas[p])), (0, 0)))
for p in ('kit', 'bajo', 'ardilla'):
    if p in pistas: pistas[p] = sampler1997(pistas[p], 12 if p != 'ardilla' else 14)
if 'telefono' in pistas: pistas['telefono'] = telefono(pistas['telefono'])
seco = {p: x * 10 ** (NIVEL[p][0] / 20) / (rms_activo(x) + 1e-12) for p, x in pistas.items()}
# el bombeo del break sobre el bajo y las cuerdas (sólo se nota en el drum'n'bass)
if 'kit' in seco:
    env = banda(seco['kit'], None, 150, 2).mean(axis=1) ** 2; env = np.sqrt(np.convolve(env, np.ones(480) / 480, 'same'))
    g = 1 - .35 * np.clip(env / (np.percentile(env, 99.5) + 1e-12), 0, 1)
    for p in ('bajo', 'cuerdas'):
        if p in seco: seco[p] = seco[p] * g[:, None]
rng = np.random.default_rng(1997); nir = int(1.8 * SR); t = np.arange(nir) / SR
ir = rng.standard_normal((nir, 2)) * np.exp(-t * 3.4)[:, None]; ir = banda(ir, 200, 7000, 2); ir /= np.sqrt((ir ** 2).sum(axis=0).mean())
envio = sum(seco[p] * NIVEL[p][1] for p in seco)
mez = sum(seco.values()) + np.stack([fftconvolve(envio[:, c], ir[:, c])[:n] for c in range(2)], 1) * .3
# vinilo: clics de polvo (Poisson 5/s, de 0.3 a 2 ms) y siseo
tot0 = np.sqrt(np.mean(mez[:FIN] ** 2)); vin = np.zeros(n)
for k in rng.integers(0, n - 200, int(n / SR * 5)): L = int(rng.integers(15, 90)); vin[k:k + L] += rng.standard_normal(L) * np.hanning(L) * rng.uniform(.3, 1)
vin = banda(vin, 1500, None, 2) * tot0 * .9 + banda(rng.standard_normal(n), 2000, 9000, 2) * tot0 * .02
mez += np.stack([vin, np.roll(vin, 7)], 1)
# el frenazo de cinta antes del compás 26
def frena(x, t1, dur):
    a, b = int((t1 - dur) * SR), int(t1 * SR); L = b - a; v = np.linspace(1, 0, L) ** 1.6; pos = a + np.cumsum(v)
    y = np.stack([np.interp(pos, np.arange(len(x)), x[:, c]) for c in range(2)], 1); x[a:b] = y * np.linspace(1, .2, L)[:, None]
frena(mez, 26 * T, .7)
# el rebobinado al reconectar (compás 40): 2 s al revés comprimidos en 0.6 s, acelerando, encima del arranque
a, b = int(38.8 * T * SR), int(40 * T * SR); src = mez[a:b][::-1]; L = int(.6 * SR); u = np.linspace(0, 1, L) ** 1.5 * (len(src) - 1)
rw = np.stack([np.interp(u, np.arange(len(src)), src[:, c]) for c in range(2)], 1) * np.hanning(2 * L)[L:, None]
k0 = int(40 * T * SR); mez[k0 - L // 3:k0 - L // 3 + L] = mez[k0 - L // 3:k0 - L // 3 + L] * .4 + rw * .9
mez = banda(mez, 30, None, 2)
mez = mez + banda(mez, 3000, None, 2) * .35                                # presencia: +2.6 dB arriba de 3 kHz (la voz y los hats)
mez = mez[:FIN]; mez[-int(.003 * SR):] *= np.linspace(1, 0, int(.003 * SR))[:, None]      # sin línea de apagado
t0 = np.sqrt(np.mean(mez ** 2)); techo = t0 * 10 ** (13 / 20); mez = np.tanh(mez / techo) * techo; mez *= .89 / np.abs(mez).max()

rms = lambda v: float(10 * np.log10(np.mean(v ** 2) + 1e-15))
med = {'secciones': {}}; bandas = {nb: banda(mez, lo, hi) for nb, lo, hi in BANDAS}
m = mez.mean(axis=1)
for ns, b0, b1 in C['S']:
    a, b = int(b0 * T * SR), int(min(b1 * T * SR, FIN)); tt = rms(mez[a:b])
    s = {'total_dB': round(tt, 1), **{nb: round(rms(bandas[nb][a:b]) - tt, 1) for nb, _, _ in BANDAS}}
    v = [seco[p][a:b] for p in VOCES if p in seco]; r = [seco[p][a:b] for p in seco if p not in VOCES]
    s['voz_sobre_resto_dB'] = round(rms(sum(v)) - rms(sum(r)), 1)
    if 'kit' in seco and rms(seco['kit'][a:b]) > rms(seco['kit']) - 20:      # tempo: el periodo de la caja (contratiempo cada 2 tiempos)
        e = banda(seco['kit'][a:b].mean(axis=1), 1700, 2600, 4) ** 2; e = np.convolve(e, np.ones(480) / 480, 'same')[::48]; e -= e.mean()
        ac = np.correlate(e, e, 'full')[len(e) - 1:]; fs = SR / 48; lags = np.arange(len(ac)) / fs
        ok = (lags > .5) & (lags < 2); s['bpm_break'] = round(float(2 * 60 / lags[ok][np.argmax(ac[ok])]), 1)   # (con la envolvente entera, los hats daban 162 en el trip-hop)
    med['secciones'][ns] = s; print(f'{ns:9s}', s)
seg = np.sqrt(np.mean(m[:len(m) // SR * SR].reshape(-1, SR) ** 2, axis=1)); tt = np.sqrt(np.mean(m ** 2))
med['peor_segundo'] = [round(20 * np.log10(seg[2:-2].min() / tt), 1), int(np.argmin(seg[2:-2]) + 2)]
def pico(t0_, t1_, lo, hi):
    a, b = int(t0_ * SR), int(t1_ * SR); X = np.abs(np.fft.rfft(m[a:b] * np.hanning(b - a))); fr = np.fft.rfftfreq(b - a, 1 / SR); k = (fr > lo) & (fr < hi)
    return round(float(fr[k][np.argmax(X[k])]), 1)
med['modem'] = {'tono_de_marcar_Hz': pico(.1, T * .9, 300, 600), 'ANSam_Hz': pico(2.1 * T, 3.5 * T, 1500, 2600)}
print('peor segundo', med['peor_segundo'], '· módem:', med['modem'])
k = 1
while (RENDER / f'{ET}-mezcla-v{k}.wav').exists(): k += 1
VER = f'{ET}-mezcla-v{k}'
with open(RENDER / f'{VER}.wav', 'xb') as fh: wavfile.write(fh, SR, mez.astype(np.float32))
with open(RENDER / f'{VER}-medidas.json', 'x', encoding='utf-8') as fh: json.dump({'niveles': NIVEL, **med}, fh, ensure_ascii=False, indent=1)
print('mezcla', VER)
if ENTREGAR:
    nonce = os.urandom(16).hex(); h = hashlib.sha256()
    for f in [AQUI / 'motor' / 'cancion.js', Path(__file__), RENDER / f'{VER}.wav']: h.update(f.read_bytes())
    h.update(nonce.encode()); ID = h.hexdigest(); CC = ID[:12]; SAL = AQUI / 'proceso' / f'una-sola-linea-{CC}'; os.mkdir(SAL)
    m4a = AQUI / f'una-sola-linea-{CC}.m4a'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-i', str(RENDER / f'{VER}.wav'), '-af', 'loudnorm=I=-13:TP=-1:LRA=9',
                    '-ar', '48000', '-c:a', 'aac', '-b:a', '256k', str(m4a)], check=True)
    sha = lambda q: hashlib.sha256(Path(q).read_bytes()).hexdigest()
    with open(SAL / f'receta-{CC}.json', 'x', encoding='utf-8') as fh:
        json.dump({'id': ID, 'nonce': nonce, 'etiqueta': ET, 'mezcla': VER, 'niveles': NIVEL, 'medidas': med,
                   'pistas_sha256': {p: sha(RENDER / f'{ET}-{p}.wav') for p in sorted(pistas)}, 'm4a': {m4a.name: sha(m4a)}}, fh, ensure_ascii=False, indent=1)
    print('entregado', m4a.name, SAL.name)
