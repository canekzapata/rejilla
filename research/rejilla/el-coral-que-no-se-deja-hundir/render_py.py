"""El coral que no se deja hundir — capas de Python: las olas que se parten en solitones, el coral que crece (lo excitan las olas),
el volcán que se hunde (y se borra en 2π), los pájaros de boca, la laguna y las luciérnagas (el plancton que brilla).
    python render_py.py <carpeta> [capa…]"""
import json, os, sys, time, math, numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI); import sintes8 as S8
sys.path.insert(0, os.path.join(AQUI, '..', 'el-androide-en-la-estacion')); import sintes6 as S6
RUN = sys.argv[1]; solo = sys.argv[2:]; P = json.load(open(os.path.join(RUN, 'partitura.json'), encoding='utf-8')); SR = 48000; N = int(P['duracion'] * SR)
quiero = lambda n: not solo or n in solo
def guardar(n, y): y.astype(np.float32).tofile(os.path.join(RUN, n + '.f32')); print(n, y.shape, 'pico', round(float(np.abs(y).max()), 3), flush=True)
FR = 200
if quiero('olas') or quiero('coral'):
    y = np.zeros((N, 2)); exc = np.zeros(N * FR // SR + 2); llegadas = []
    for i, o in enumerate(P['olas']):
        s, q, ll = S8.ola(o['t'], o['n'], N, dur=o['dur'], semilla=i, brillo=.6 + .4 * (o['n'] > 3)); y += s * (.35 + .15 * o['n']); llegadas.append(ll)
        a = int(o['t'] * FR); qq = np.interp(np.arange(int(o['dur'] * FR)) / FR, np.arange(len(q)) * o['dur'] / len(q), q); m = min(len(qq), len(exc) - a)
        if m > 0: exc[a:a + m] = np.maximum(exc[a:a + m], qq[:m] * (o['n'] / 5))
    guardar('olas', y / (np.abs(y).max() + 1e-12)); np.save(os.path.join(RUN, 'olas-excita.npy'), exc); json.dump(llegadas, open(os.path.join(RUN, 'olas-llegadas.json'), 'w'))
if quiero('coral'):
    C = P['coral']; t = time.time(); parts, base = S8.crecer_coral(C['W'], C['H'], C['n'], C['base'], C['semilla'])
    ys = np.array([p[1] for p in parts]); top = np.maximum.accumulate(ys); y0, y1 = int(max(C['base'])), C['H']
    fc = lambda tt: P['f_cruce'] * 2 ** ((tt - P['cruce']) / P['t8'])
    f_bajo, f_alto = fc(C['inicio']), fc(P['duracion'] - 8)
    # cada partícula llega cuando la copa del arrecife alcanza su tono: la copa sube con fc(t)
    t_top = lambda yy: P['cruce'] + P['t8'] * math.log2(f_bajo * (f_alto / f_bajo) ** ((yy - y0) / (y1 - y0)) / P['f_cruce'])
    tiempos = []; k = 0
    while k < len(parts):
        j = k
        while j + 1 < len(parts) and top[j + 1] == top[k]: j += 1
        a = t_top(top[k]); z = t_top(top[j + 1]) if j + 1 < len(parts) else P['duracion'] - 8
        for i in range(k, j + 1): tiempos.append(a + (z - a) * (i - k) / (j - k + 1))
        k = j + 1
    tiempos = np.clip(tiempos, C['inicio'], P['duracion'] - 8)
    exc = np.load(os.path.join(RUN, 'olas-excita.npy'))
    org, clics, info = S8.coral(parts, tiempos, C['W'], C['H'] - y0, f_bajo, f_alto, P['tonica'], N, excita=exc, semilla=C['semilla'])
    guardar('coral', org); guardar('coral-clics', clics)
    json.dump(dict(info, particulas=[[int(x), int(yy), int(p)] for x, yy, p in parts], tiempos=[round(float(x), 3) for x in tiempos], y_base=y0, f_bajo=f_bajo, f_alto=f_alto,
                   segundos=round(time.time() - t, 1)), open(os.path.join(RUN, 'coral-crecimiento.json'), 'w'))
    print('  coral', info, round(time.time() - t, 1), 's')
if quiero('volcan'):
    V = P['volcan']; y = S8.volcan(V['f'], V['prof'], V['theta'], V['vocal'], N, semilla=3); guardar('volcan', y)
if quiero('boca'): guardar('boca', S8.boca_pajaro(P['boca'], N, 4))
if quiero('laguna'): L = P['laguna']; guardar('laguna', S8.laguna(L['f'], L['curva'], N, 5))
if quiero('luciernagas'):
    L = P['luciernagas']; y, tt, r, destellos = S6.luciernagas(L['t0'], L['t1'], N, L['f_pulso'], L['K'], L['notas'], semilla=6)
    guardar('luciernagas', y); json.dump(dict(r=[round(float(x), 3) for x in r[::50]], destellos=len(destellos)), open(os.path.join(RUN, 'luciernagas-orden.json'), 'w'))
