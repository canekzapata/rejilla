"""Lo que el agua dibuja — capas de Python (sintes11): la lluvia de Xenakis en sus tres toques (pizz, arco, col legno), los truenos,
la crecida y sus pedregones, los hi-hats de la 808 con los redobles primos, el 808 que se desliza y el viento seco.
    python render_py.py <carpeta> [capa…]"""
import json, os, sys, numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI); import sintes11 as S
RUN = sys.argv[1]; solo = sys.argv[2:]; P = json.load(open(os.path.join(RUN, 'partitura.json'), encoding='utf-8')); SR = 48000; N = int(P['duracion'] * SR)
quiero = lambda n: not solo or n in solo
def guardar(n, y): y.astype(np.float32).tofile(os.path.join(RUN, n + '.f32')); print(n, y.shape, 'pico', round(float(np.abs(y).max()), 3), flush=True)
for capa, toque in (('lluvia', 'pizz'), ('arco', 'arco'), ('col-legno', 'col')):
    if quiero(capa): guardar(capa, S.lluvia_xenakis(P['gotas'], N, len(capa), (toque,)))
if quiero('trueno'):
    y = np.zeros((N, 2), np.float32); info = []
    for r in P['rayos']:
        x, lag = S.trueno(r['dist_m'], r['semilla']); i = int(r['llega'] * SR); m = min(len(x), N - i)
        if m > 0: y[i:i + m] += x[:m] * (1500 / r['dist_m']) ** .5
        info.append((r['lugar'], r['dist_m'], round(lag, 2), round(len(x) / SR, 1)))
    print('truenos', info); guardar('trueno', y / np.abs(y).max())
if quiero('crecida') or quiero('pedregones'):
    LL = P['lluvia']; Q = S.hidrograma(np.array(LL['intensidad']), LL['fr'])
    ruge, piedra, tasa = S.crecida(Q, LL['fr'], N, 5)
    json.dump(dict(fr=LL['fr'], Q=[round(float(x), 4) for x in Q], tasa=[round(float(x), 3) for x in tasa]), open(os.path.join(RUN, 'hidrograma.json'), 'w'))
    guardar('crecida', ruge); guardar('pedregones', piedra)
if quiero('hats'): guardar('hats', S.hats808(P['hats'], N, 3))
if quiero('bajo808'): guardar('bajo808', S.ocho_ocho(P['ocho'], N))
if quiero('viento'):
    y, v = S.viento(P['viento'], N, 9); guardar('viento', y)
