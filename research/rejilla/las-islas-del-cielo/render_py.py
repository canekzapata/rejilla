"""Las islas del cielo — capas de Python: las cascadas que no llegan (una por isla), los capachos, el tuki, la lluvia del llano y la
campana de distancias imposibles (campana-padica/campana.py de Codex: el mismo resonador JS, 24 kHz, subido a 48 kHz).
    python render_py.py <carpeta> [capa…]"""
import json, os, sys, numpy as np
from scipy.signal import resample_poly
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI); import sintes9 as S9
sys.path.insert(0, os.path.join(AQUI, '..', 'campana-padica')); import campana as CP
RUN = sys.argv[1]; solo = sys.argv[2:]; P = json.load(open(os.path.join(RUN, 'partitura.json'), encoding='utf-8')); SR = 48000; N = int(P['duracion'] * SR)
quiero = lambda n: not solo or n in solo
def guardar(n, y): y.astype(np.float32).tofile(os.path.join(RUN, n + '.f32')); print(n, y.shape, 'pico', round(float(np.abs(y).max()), 3), flush=True)
if quiero('cascadas'):
    y = np.zeros((N, 2)); info = []
    for i, c in enumerate(P['cascadas']):
        s, inf = S9.cascada(c['t'], c['H'], c['f'], N, pan=c['pan'], semilla=i); y += s; info.append(dict(inf, t=c['t'], f=c['f']))
    guardar('cascadas', y / (np.abs(y).max() + 1e-12)); json.dump(info, open(os.path.join(RUN, 'cascadas-info.json'), 'w'))
if quiero('capachos'): guardar('capachos', S9.capachos(P['capachos'], N, 1))
if quiero('tuki'): guardar('tuki', S9.tuki(P['tuki'], N, 2))
if quiero('lluvia'): guardar('lluvia', S9.lluvia(P['lluvia'], N, 3))
if quiero('campana'):
    # el motor de Codex acepta hasta 180 s: dos tramos (0–176 s y 130–240 s, éste con los parámetros que el cuerpo lleva a los 130 s)
    # cruzados entre 140 y 150 s, cuando el segundo ya suena
    C = P['campana']; corte = 130.0; xa, xz = 140.0, 150.0
    A, ra = CP.render(dict(initial=C['initial'], events=[e for e in C['events'] if e['t'] < 176]), duracion=176, sr=24000)
    ini = dict(C['initial'])
    for e in C['events']:
        if e['t'] < corte and 'params' in e: ini.update(e['params'])
    Bv, rb = CP.render(dict(initial=ini, events=[dict(e, t=round(e['t'] - corte, 4)) for e in C['events'] if e['t'] >= corte]), duracion=P['duracion'] - corte, sr=24000)
    A = resample_poly(A, 2, 1, axis=0); Bv = resample_poly(Bv, 2, 1, axis=0); y = np.zeros((N, 2))
    t = np.arange(N) / SR; w = np.clip((t - xa) / (xz - xa), 0, 1)[:, None]
    nA = min(len(A), N); y[:nA] += A[:nA] * (1 - w[:nA]); i0 = int(corte * SR); nB = min(len(Bv), N - i0); y[i0:i0 + nB] += Bv[:nB] * w[i0:i0 + nB]
    guardar('campana', y / (np.abs(y).max() + 1e-12)); json.dump(dict(tramo_1=ra, tramo_2=rb, corte=corte, cruce=[xa, xz]), open(os.path.join(RUN, 'campana-recibo.json'), 'w'))
