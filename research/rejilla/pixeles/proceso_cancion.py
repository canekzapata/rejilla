"""El GIF de la canción: la espiral de terceras recorrida por una cabeza al ritmo de la canción
(los cents que suena cada momento), con el verso que se canta; más el espectrograma completo."""
import json, math, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).parent.parent))
from colores import oklch, fuente
import cancion as K

AQUI = Path(__file__).parent
P = AQUI / 'proceso' / 'cancion'; P.mkdir(parents=True, exist_ok=True)
part = json.load(open(K.R / 'partitura.json', encoding='utf-8'))
marcas = part['marcas']
total = marcas[-1][1] + K.PARO[2] * K.T0
h0 = 255 + np.random.default_rng(5454).uniform(-12, 12)
TONOS = [h0, h0 + 160, h0 + 95, h0 - 115]
FONDO = tuple(int(c) for c in oklch(.13, .05, h0)); TC = tuple(int(c) for c in oklch(.93, .04, h0 + 160))
col = lambda i, L=.78, C=.17: tuple(int(c) for c in oklch(L, C, TONOS[i % 4]))
F, Fg, Fl = fuente(18), fuente(28), fuente(24)
W, H = 1200, 820
TER = 1200 * math.log2(5 / 4)
CENTS = {'intro': 0, 'verso 1': 0, 'pre': 0, 'coro 1': 0, 'verso 2': TER, 'coro 2': TER, 'puente': -TER,
         'coro final': 2 * TER, 'outro': 3 * TER, 'paro de cinta': 3 * TER}


def cents_en(t):
    """Cents que suena el momento t (las cintas se deslizan entre una sección y la siguiente)."""
    for (s, t0), (s2, t1) in zip(marcas, marcas[1:] + [('fin', total)]):
        if t0 <= t < t1:
            if s.startswith('cinta'):
                a = CENTS[s[6:]]; nxt = s2 if s2 in CENTS else 'outro'; b = CENTS[nxt]
                u = (t - t0) / (t1 - t0); u = u * u * (3 - 2 * u); return a + (b - a) * u, s
            if s == 'paro de cinta':
                u = (t - t0) / (t1 - t0); return 3 * TER + 1200 * math.log2(1 - .72 * u), s
            return CENTS.get(s, 0), s
    return 3 * TER, 'fin'


def verso_en(t):
    for s, t0 in marcas:
        if s not in part['letra']: continue
        for ln, cur, notas, pos, dur in part['letra'][s]:
            lec = .8 if s == 'puente' else 1
            a = t0 + cur * K.T0 / 16 / lec; b = a + (pos[-1] + dur[-1]) * K.T0 / 16 / lec
            if a - .2 <= t <= b + .4: return ln
    return None


def cuadro(t):
    im = Image.new('RGB', (W, H), FONDO); d = ImageDraw.Draw(im)
    cx, cy = 600, 420
    d.text((30, 20), 'los pixeles y la luna', fill=TC, font=Fg)
    for k in range(12):
        a = -math.pi / 2 + 2 * math.pi * k / 12
        d.line([(cx + 110 * math.cos(a), cy + 110 * math.sin(a)), (cx + 330 * math.cos(a), cy + 330 * math.sin(a))],
               fill=tuple(int(c) for c in oklch(.27, .04, h0)), width=1)
    pos = lambda c: (cx + (140 + 150 * c / 1200) * math.cos(-math.pi / 2 + 2 * math.pi * c / 1200),
                     cy + (140 + 150 * c / 1200) * math.sin(-math.pi / 2 + 2 * math.pi * c / 1200))
    d.line([pos(c) for c in np.linspace(-TER, 3 * TER, 300)], fill=tuple(int(c) for c in oklch(.4, .06, h0)), width=2)
    # el rastro recorrido hasta t
    hist = [cents_en(tt)[0] for tt in np.linspace(0, t, 160)]
    denso = [hist[0]] if hist else []
    for c0, c1 in zip(hist, hist[1:]):                  # entre dos momentos, seguir la espiral (no la cuerda)
        denso += list(np.linspace(c0, c1, 2 + int(abs(c1 - c0) / 8)))[1:]
    if len(denso) > 1: d.line([pos(c) for c in denso], fill=col(0), width=5)
    c, s = cents_en(t)
    x, y = pos(c); i = {'verso 2': 1, 'coro 2': 1, 'puente': 3, 'coro final': 2}.get(s, 0)
    d.ellipse([x - 13, y - 13, x + 13, y + 13], fill=col(i))
    d.text((30, 64), f'{s} · {c:+.0f} cents', fill=col(i), font=F)
    d.text((30, H - 40), f'{int(t // 60)}:{int(t % 60):02d}', fill=TC, font=F)
    v = verso_en(t)
    if v: d.text((30, H - 90), f'«{v}»', fill=col(i, .9, .12), font=Fl)
    return im


cuadro(total * .97).save(P / f'01-espiral-recorrida-{K.TAG}.png')
frames = [cuadro(tt).resize((W * 2 // 3, H * 2 // 3), Image.LANCZOS) for tt in np.linspace(0, total, 105)]
pal = frames[len(frames) // 2].quantize(colors=128, method=Image.Quantize.MEDIANCUT)
frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
gif = AQUI / f'proceso-cancion-{K.TAG}.gif'
frames[0].save(gif, save_all=True, append_images=frames[1:], duration=92, loop=0, optimize=True)
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(K.R / f'los-pixeles-y-la-luna-{K.TAG}.wav'), '-lavfi',
                'showspectrumpic=s=1400x700:mode=combined:scale=log:fscale=log:start=30:stop=14000:color=magma:legend=1',
                str(P / f'02-espectrograma-{K.TAG}.png')], check=True)
print('gif', f'{gif.stat().st_size / 1e6:.2f} MB', f'{92 * len(frames) / 1000:.1f} s')
