"""Lo que el agua dibuja — sondas: se mide lo que SUENA (las capas rendidas), no lo que dice la partitura.
    python sondas/medir.py <carpeta-de-render>      → <carpeta>/sondas.json
 1 guitarra   la altura del slide (autocorrelación, 16 kHz) contra la curva del perfil: error en cents
 2 zing       el pico del chirrido contra la predicción |dx/dt| / 0.4 mm
 3 xenakis    las velocidades de las gotas (|v| / a) contra la distribución de Maxwell (Kolmogórov–Smirnov); y una gota aislada
              rendida con el instrumento: la pendiente de su altura medida contra la de la partitura
 4 trueno     el centroide espectral de cada trueno contra su distancia (más lejos, más oscuro)
 5 erosión    dónde está el nudo (la pendiente mayor) al empezar cada sección: ¿retrocede aguas arriba?
 6 crecida    cuánto tarda el pico del caudal tras el pico de la lluvia, y cuántos pedregones suenan
 7 primos     los golpes de cada redoble detectados en los hats, llevados de vuelta a u, contra los log p^k
"""
import json, math, os, sys
import numpy as np
from scipy.signal import resample_poly, butter, sosfiltfilt, find_peaks
from scipy.special import erf
from scipy.stats import kstest
AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, AQUI); import sintes11 as S11
RUN = sys.argv[1]; SR = 48000; P = json.load(open(os.path.join(RUN, 'partitura.json'), encoding='utf-8')); N = int(P['duracion'] * SR)
def leer(n, est): x = np.fromfile(os.path.join(RUN, n + '.f32'), dtype=np.float32); return x.reshape(-1, 2).mean(1) if est else x
hzf = lambda m: 440 * 2 ** ((np.asarray(m) - 69) / 12)
out = {}

# 1 · la guitarra contra el perfil
G = P['guitarra']; cu = G['cuerdas'][0]; curva = np.array(cu['curva']); fr = G['fr']
x = resample_poly(leer('guitarra', True), 1, 3).astype(np.float32); sr = 16000
hop, W = 160, 1024; ts, med, esp = [], [], []
puas = np.array([p[0] for p in cu['pulsos']])
rms_g = np.sqrt(np.convolve(x.astype(float) ** 2, np.ones(W) / W, 'same'))
umbral = np.percentile(rms_g[rms_g > 0], 60) * .3
for i in range(0, len(x) - W, hop):
    t = (i + W / 2) / sr; k = np.searchsorted(puas, t)
    if k and t - puas[k - 1] < .04: continue                                                     # el golpe de la púa no tiene altura
    if rms_g[i + W // 2] < umbral: continue
    m_esp = float(np.interp(t, np.arange(len(curva)) / fr, curva)); f_esp = float(hzf(m_esp))
    seg = x[i:i + W] * np.hanning(W); ac = np.fft.irfft(np.abs(np.fft.rfft(seg, 2 * W)) ** 2)[:W]
    lo, hi = int(sr / (f_esp * 1.25)), int(sr / (f_esp / 1.25))                                  # busca el periodo cerca de lo esperado (±4 semitonos)
    if hi >= W - 2: continue
    j = lo + int(np.argmax(ac[lo:hi]))
    if ac[j] < .3 * ac[0]: continue
    a, b, c = ac[j - 1], ac[j], ac[j + 1]; d = .5 * (a - c) / (a - 2 * b + c + 1e-12)
    f0 = sr / (j + d); ts.append(t); med.append(69 + 12 * math.log2(f0 / 440)); esp.append(m_esp)
err = (np.array(med) - np.array(esp)) * 100
out['guitarra'] = dict(cuadros=len(err), mediana_abs_cents=round(float(np.median(np.abs(err))), 1), dentro_de_30_cents=round(float(np.mean(np.abs(err) < 30)), 3),
                       sesgo_cents=round(float(np.median(err)), 1))
tormentas = {}
for k, n in P['carcava']['nudos'].items():
    s = next(e for e in P['secciones'] if e['num'] == k); sel = (np.array(ts) > s['t'] + 1) & (np.array(ts) < s['t1'] - .3)
    if sel.sum() > 10:
        mm = np.array(med)[sel]; tormentas[k] = dict(x_m=n['x_m'], al_entrar=round(float(np.median(mm[:15])), 2), al_salir=round(float(np.median(mm[-15:])), 2),
                                                     se_hunde_st=round(float(np.median(mm[:15]) - np.median(mm[-15:])), 2), partitura_st=n['cae_st'])
out['guitarra']['tormentas'] = tormentas
del x, rms_g

# 2 · el zing
z = leer('zing', False).astype(np.float32); m48 = np.interp(np.arange(0, N, 480) / SR, np.arange(len(curva)) / fr, curva)
f = hzf(m48); dm = np.gradient(m48, 480 / SR); fab = float(hzf(cu['abierta'])); vx = np.abs(.648 * fab * (f * math.log(2) / 12 * dm) / f ** 2); fz = vx / .0004
pares = []
for k in np.nonzero((fz > 400) & (fz < 6000))[0]:
    i = k * 480; seg = z[i:i + 2048]
    if len(seg) < 2048 or np.sqrt(np.mean(seg ** 2)) < 1e-4: continue
    X = np.abs(np.fft.rfft(seg * np.hanning(2048))); fq = np.fft.rfftfreq(2048, 1 / SR); band = (fq > 150) & (fq < 8000)
    pares.append((fz[k], fq[band][np.argmax(X[band])]))
pares = np.array(pares)
out['zing'] = dict(cuadros=len(pares), razon_medido_sobre_predicho_mediana=round(float(np.median(pares[:, 1] / pares[:, 0])), 3) if len(pares) else None,
                   dentro_de_un_tercio_de_octava=round(float(np.mean(np.abs(np.log2(pares[:, 1] / pares[:, 0])) < 1 / 3)), 3) if len(pares) else None)
del z

# 3 · Xenakis
gs = P['gotas']; w = np.array([abs(g['v']) / g['temp'] for g in gs])
cdf = lambda x: erf(x) - 2 / math.sqrt(math.pi) * x * np.exp(-x * x)                           # Maxwell con a = 1
ks = kstest(w, cdf)
prueba = []
for v in (-12.0, -4.0, 6.0, 18.0):
    e = dict(t=.05, m0=84.0, v=v, dur=.6, a=1, pan=0, toque='arco'); y = S11.lluvia_xenakis([e], int(.8 * SR), 1, ('arco',)).mean(1)
    tt, mm = [], []
    for i in range(int(.12 * SR), int(.6 * SR), 960):
        seg = y[i:i + 4096] * np.hanning(4096); X = np.abs(np.fft.rfft(seg, 16384)); fq = np.fft.rfftfreq(16384, 1 / SR)
        b = (fq > 150) & (fq < 3000); tt.append((i + 2048) / SR); mm.append(69 + 12 * math.log2(fq[b][np.argmax(X[b])] / 440))
    prueba.append(dict(v_partitura=v, v_medida=round(float(np.polyfit(tt, mm, 1)[0]), 2)))
out['xenakis'] = dict(gotas=len(gs), ks_contra_maxwell=dict(D=round(float(ks.statistic), 4), p=round(float(ks.pvalue), 4)), media_v_sobre_a=round(float(w.mean()), 3),
                      maxwell_teorica=round(2 / math.sqrt(math.pi), 3), toques={t: sum(g['toque'] == t for g in gs) for t in ('pizz', 'arco', 'col')}, gota_aislada=prueba)

# 4 · el trueno
tr = leer('trueno', True); filas = []
for r in P['rayos']:
    i = int(r['llega'] * SR); seg = tr[i:i + 2 * SR]; X = np.abs(np.fft.rfft(seg)) ** 2; fq = np.fft.rfftfreq(len(seg), 1 / SR)
    filas.append(dict(lugar=r['lugar'], dist_m=r['dist_m'], retraso_s=r['retraso_s'], centroide_hz=round(float((X * fq).sum() / X.sum()), 1)))
dd = np.array([f_['dist_m'] for f_ in filas]); cc = np.array([f_['centroide_hz'] for f_ in filas])
out['trueno'] = dict(rayos=filas, correlacion_distancia_centroide=round(float(np.corrcoef(dd, cc)[0, 1]), 3))
del tr

# 5 · la erosión: el nudo
import importlib.util
spec = importlib.util.spec_from_file_location('partitura', os.path.join(AQUI, 'partitura.py')); sys.argv = ['partitura.py']; PT = importlib.util.module_from_spec(spec); spec.loader.exec_module(PT)
nudo = {}
for s in P['secciones']:
    z_ = PT.z_en(s['t']); S = -np.gradient(z_, PT.DX); S[-PT.NX // 30:] = 0; nudo[s['num']] = dict(x_m=round(float(PT.XS[np.argmax(S)])), pendiente=round(float(S.max()), 4))
z_fin = PT.z_en(P['duracion']); cava = PT.Z0 - z_fin
out['erosion'] = dict(nudo_por_seccion=nudo, K=P['carcava']['K'], hondo_max_m=round(float(cava.max()), 2), hondo_medio_m=round(float(cava.mean()), 2),
                      donde_max_m=round(float(PT.XS[np.argmax(cava)])), boca_fija_m=round(float(PT.Z0[-1] - z_fin[-1]), 4))

# 6 · la crecida
H = json.load(open(os.path.join(RUN, 'hidrograma.json'))); Q = np.array(H['Q']); I = np.array(P['lluvia']['intensidad']); frh = H['fr']; lag = {}
for k in P['tormentas']:
    s = next(e for e in P['secciones'] if e['num'] == k); a, b = int(s['t'] * frh), int((s['t1'] + 15) * frh)
    lag[k] = dict(pico_lluvia_s=round(a / frh + np.argmax(I[a:b]) / frh, 2), pico_caudal_s=round(a / frh + np.argmax(Q[a:b]) / frh, 2), Q_pico=round(float(Q[a:b].max()), 3))
    lag[k]['retraso_s'] = round(lag[k]['pico_caudal_s'] - lag[k]['pico_lluvia_s'], 2)
pd = leer('pedregones', True); env = np.abs(pd); pk, _ = find_peaks(env, height=.05, distance=int(.03 * SR))
out['crecida'] = dict(tormentas=lag, pedregones_detectados=len(pk)); del pd, env

# 7 · los redobles primos, en los hats que suenan. El ataque se busca en la energía aguda suavizada a 3 ms (más fino, el metal de
#     la 808 fluctúa y da ataques falsos), como subida de ≥ 3 dB contra 3 ms antes. Sólo los redobles de un tiempo entero: en los de
#     medio tiempo los últimos golpes quedan a ~5 ms y no se separan.
h = leer('hats', True)
def es_pot(n):
    for p in range(2, n + 1):
        if n % p == 0:
            while n % p == 0: n //= p
            return n == 1
    return False
pp = np.array([math.log(n) for n in range(2, 73) if es_pot(n)])
u0 = math.log(1.8); u1 = max(p[0] for p in S11.picos_primos(72)[0]) + .01
acier, total, esperados, errs, med = 0, 0, 0, [], 0
for r in P['redobles']:
    if r['D'] < .8: continue
    a, b = int((r['t'] - .003) * SR), int((r['t'] + r['D'] + .003) * SR); seg = h[a:b].astype(float)
    hp = sosfiltfilt(butter(2, 5000, 'high', fs=SR, output='sos'), seg); fr_ = 144
    le = 20 * np.log10(np.sqrt(np.convolve(hp ** 2, np.ones(fr_) / fr_, 'same')) + 1e-9); dd = np.concatenate([np.zeros(fr_), np.maximum(0, le[fr_:] - le[:-fr_])])
    k, _ = find_peaks(dd, height=3, distance=int(.007 * SR)); tk = (a + k - fr_ // 2) / SR
    x = (tk - r['t']) / r['D']; u = u0 + (x if r['ida'] else 1 - x) * (u1 - u0); med += 1; esperados += r['golpes']
    for uu in u:
        e_ = float(np.min(np.abs(pp - uu))); errs.append(e_); total += 1; acier += e_ < .01
out['primos'] = dict(redobles=len(P['redobles']), medidos=med, golpes_esperados=esperados, golpes_detectados=total, caen_en_log_pk=acier, fraccion=round(acier / max(total, 1), 3),
                     error_mediano_u=round(float(np.median(errs)), 5) if errs else None, picos_en_la_suma=P['picos_primos'])
json.dump(out, open(os.path.join(RUN, 'sondas.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=lambda o: o.item())
print(json.dumps(out, ensure_ascii=False, indent=1, default=lambda o: o.item())[:7000])
