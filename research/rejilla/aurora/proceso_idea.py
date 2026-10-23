"""PNG y GIF del laberinto de «sobre la aurora»: el camino sobre el Tonnetz desenrollado.

En el Tonnetz la nota de (a, b) es 7a + 4b (mod 12): quintas a la derecha, terceras mayores
en diagonal. Es un toro (4 quintas = 1 tercera mayor; 3 terceras = 1 octava); aquí se
desenrolla en el plano: cada paso se dibuja en la copia del acorde más cercana al anterior,
así el camino se ve continuo.
"""
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).parent.parent))
from colores import oklch, fuente
from laberinto import NOTAS, nombre as _nombre

# la fuente monoespaciada no tiene ♭ ni ♯: en el dibujo van como b y #
ascii = lambda s: s.replace('♭', 'b').replace('♯', '#')
nombre = lambda t: ascii(_nombre(t))

AQUI = Path(__file__).parent
PROC = AQUI / 'proceso'
PROC.mkdir(exist_ok=True)
L = json.load(open(AQUI / 'laberinto.json'))
camino = [((r, bool(m)), op) for r, m, op in L['camino']]
callejones = set(L['callejones'])
SEM = 1015
h0 = (SEM * 47) % 360
FONDO = oklch(.12, .03, h0 + 230); TC = tuple(int(c) for c in oklch(.9, .04, h0 + 40))
F, Fs, Fb = fuente(20), fuente(14), fuente(17)


def a_plano(a, b): return a + 0.5 * b, b * math.sqrt(3) / 2


def raiz_ab(r):
    for a in range(12):
        for b in range(3):
            if (7 * a + 4 * b) % 12 == r: return a, b


def centro(t, a, b):
    r, m = t
    if not m: return a + 1 / 3, b + 1 / 3            # (r, r+4, r+7): (a,b) (a,b+1) (a+1,b)
    return a + 2 / 3, b - 1 / 3                      # (r, r+3, r+7): (a,b) (a+1,b-1) (a+1,b)


# camino continuo en el plano desenrollado
pos = []
for i, (t, op) in enumerate(camino):
    a0, b0 = raiz_ab(t[0])
    cands = [centro(t, a0 + 4 * k, b0 - k + 3 * j) for k in range(-6, 7) for j in range(-4, 5)]
    if not pos: c = min(cands, key=lambda c: abs(c[0]) + abs(c[1]))
    else: c = min(cands, key=lambda c: (a_plano(*c)[0] - a_plano(*pos[-1])[0]) ** 2 + (a_plano(*c)[1] - a_plano(*pos[-1])[1]) ** 2)
    pos.append(c)
xy = np.array([a_plano(*c) for c in pos])
x0, y0 = xy.min(0) - 1.6; x1, y1 = xy.max(0) + 1.6
W, H, MARG = 1200, 900, 60
esc = min((W - 2 * MARG) / (x1 - x0), (H - 2 * MARG - 60) / (y1 - y0))
px = lambda x, y: (MARG + (x - x0) * esc, H - MARG - (y - y0) * esc)


def fondo():
    im = Image.new('RGB', (W, H), tuple(int(c) for c in FONDO)); d = ImageDraw.Draw(im)
    rej = tuple(int(c) for c in oklch(.32, .03, h0 + 230)); txt = tuple(int(c) for c in oklch(.55, .05, h0 + 200))
    for a in range(-20, 30):
        for b in range(-20, 30):
            x, y = a_plano(a, b)
            if not (x0 - 1 < x < x1 + 1 and y0 - 1 < y < y1 + 1): continue
            for da, db in ((1, 0), (0, 1), (1, -1)):
                d.line([px(x, y), px(*a_plano(a + da, b + db))], fill=rej, width=1)
            p = px(x, y); d.text((p[0] - 9, p[1] - 8), ascii(NOTAS[(7 * a + 4 * b) % 12]), fill=txt, font=Fs)
    return im


def color(i, op):
    if op == 'regresa': return oklch(.70, .13, h0 + 180)
    return oklch(.80, .16, h0 + 300 * i / 22)


def cuadro(hasta):
    im = fondo(); d = ImageDraw.Draw(im)
    for i in range(1, hasta + 1):
        t, op = camino[i]
        c = tuple(int(v) for v in color(i, op))
        off = 5 if op == 'regresa' else 0                  # el regreso corre junto al pasillo, en espejo
        a, b = px(*xy[i - 1]), px(*xy[i])
        d.line([(a[0] + off, a[1] + off), (b[0] + off, b[1] + off)], fill=c, width=5 if op != 'regresa' else 3)
    for i in range(hasta + 1):
        t, op = camino[i]
        p = px(*xy[i]); c = tuple(int(v) for v in color(i, op))
        r = 9 if i in callejones else 6
        if op != 'regresa' or i in callejones:
            d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=c if i not in callejones else None,
                      outline=c, width=3)
            d.text((p[0] + 10, p[1] - 22), nombre(t), fill=TC, font=Fb)
    t, op = camino[hasta]; p = px(*xy[hasta])
    d.ellipse([p[0] - 14, p[1] - 14, p[0] + 14, p[1] + 14], outline=TC, width=2)
    estado = 'callejón sin salida: stop-time' if hasta in callejones else ('regresa (espejo)' if op == 'regresa' else f'avanza por {op}')
    d.text((MARG, 18), f'sobre la aurora · el laberinto armónico · paso {hasta:2d}/46 · {nombre(t)} · {estado}', fill=TC, font=F)
    d.text((MARG, H - 34), 'Tonnetz desenrollado: quintas a la derecha, terceras mayores en diagonal. Cada paso mueve una sola voz (P, L: medio tono; R: un tono).',
           fill=TC, font=Fs)
    return im


cuadro(len(camino) - 1).save(PROC / f'01-laberinto-s{SEM}.png')
frames = [cuadro(i) for i in range(len(camino))] + [cuadro(len(camino) - 1)] * 10
frames = [f.resize((W * 3 // 4, H * 3 // 4), Image.LANCZOS) for f in frames]
pal = frames[-1].quantize(colors=128, method=Image.Quantize.MEDIANCUT)
frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
dur = [170 if i in callejones else 150 for i in range(len(camino))] + [150] * 10
dur = [d * 9500 // sum(dur) for d in dur]
gif = AQUI / f'proceso-laberinto-s{SEM}.gif'
frames[0].save(gif, save_all=True, append_images=frames[1:], duration=dur, loop=0, optimize=True)
print('gif', f'{gif.stat().st_size / 1e6:.2f} MB', f'{sum(dur) / 1000:.1f} s')
