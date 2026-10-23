"""La idea de «los pixeles y la luna» dibujada: la espiral de terceras justas que no cierra la
octava (Mi → Sol♯ → Do → Mi, 41 cents corto), los bits de «luna» que cantará Zira, y la forma
con la lectura de cada sección."""
import math, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).parent.parent))
from colores import oklch, fuente

AQUI = Path(__file__).parent
PROC = AQUI / 'proceso'; PROC.mkdir(exist_ok=True)
SEM = 5454
r0 = np.random.default_rng(SEM)
h0 = 255 + r0.uniform(-12, 12)                 # el azul eléctrico de las imágenes, derivado de la semilla
TONOS = [h0, h0 + 160, h0 + 95, h0 - 115]       # azul, amarillo, rosa, verde (giros desde el azul)
FONDO = tuple(int(c) for c in oklch(.13, .05, h0))
TC = tuple(int(c) for c in oklch(.93, .04, h0 + 160))
col = lambda i, L=.78, C=.17: tuple(int(c) for c in oklch(L, C, TONOS[i % 4]))
F, Fs, Fg = fuente(20), fuente(14), fuente(30)
W, H = 1400, 900
TERCERA = 1200 * math.log2(5 / 4)
PASOS = [('Mi', '1', 0), ('Sol#', '5/4', 1), ('Do', '25/16', 2), ('Mi -41c', '125/64', 3)]


def espiral(fraccion=1.0):
    im = Image.new('RGB', (W, H), FONDO); d = ImageDraw.Draw(im)
    cx, cy = 430, 470
    d.text((40, 24), 'los pixeles y la luna · todo es 5:4', fill=TC, font=Fg)
    d.text((40, 66), 'leer la imagen a 5/4 sube una tercera mayor justa (386.3 cents); tres no cierran la octava', fill=TC, font=Fs)
    # el círculo de la octava (12 casillas) y la espiral de cents
    for k in range(12):
        a = -math.pi / 2 + 2 * math.pi * k / 12
        d.line([(cx + 120 * math.cos(a), cy + 120 * math.sin(a)), (cx + 330 * math.cos(a), cy + 330 * math.sin(a))],
               fill=tuple(int(c) for c in oklch(.28, .04, h0)), width=1)
    total = 3 * TERCERA * fraccion
    pts = []
    for c in np.linspace(0, total, 400):
        a = -math.pi / 2 + 2 * math.pi * c / 1200
        r = 140 + 170 * c / 1200
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    if len(pts) > 1: d.line(pts, fill=col(0), width=4)
    # los cuatro puntos
    for nom, lec, i in PASOS:
        c = i * TERCERA
        if c > total + 1e-6: break
        a = -math.pi / 2 + 2 * math.pi * c / 1200; r = 140 + 170 * c / 1200
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        d.ellipse([x - 11, y - 11, x + 11, y + 11], fill=col(i))
        dx = -250 if i == 0 else 16                              # Mi de salida: la etiqueta a la izquierda, fuera de la espiral
        d.text((x + dx, y - 10), f'{nom}  (lectura {lec})', fill=col(i), font=F)
    if fraccion >= 1:
        # la octava que no llega: el hueco de 41 cents
        a1 = -math.pi / 2 + 2 * math.pi * (3 * TERCERA) / 1200
        a2 = -math.pi / 2 + 2 * math.pi
        rr = 140 + 170 * 3 * TERCERA / 1200 + 40
        d.arc([cx - rr, cy - rr, cx + rr, cy + rr], math.degrees(a1), math.degrees(a2), fill=col(2, .9, .2), width=6)
        d.text((cx + 40, cy - rr - 40), 'faltan 41 cents (128/125): casi en casa pero no', fill=col(2, .9, .2), font=F)
    # los bits de «luna» que Zira canta como «cero / uno»
    bits = ''.join(f'{ord(c):08b}' for c in 'luna')
    x0, y0 = 830, 170
    d.text((x0, y0 - 40), 'el gancho de Zira: los bits de «luna»', fill=TC, font=F)
    for i, b in enumerate(bits):
        x = x0 + (i % 16) * 32; y = y0 + (i // 16) * 70
        if b == '1': d.rectangle([x, y, x + 26, y + 40], fill=col(1))
        else: d.rectangle([x, y, x + 26, y + 40], outline=col(3), width=2)
        d.text((x + 2, y + 44), 'uno' if b == '1' else 'cero', fill=TC, font=fuente(10))
    # la forma: lectura por sección (altura = transposición en cents)
    forma = [('intro', 4, 0), ('verso 1', 8, 0), ('pre', 4, 0), ('coro 1', 8, 0), ('verso 2', 8, 1), ('coro 2', 8, 1),
             ('puente 4/5', 7.5, -1), ('coro final', 8, 2), ('outro', 6, 3)]
    total_c = sum(c for _, c, _ in forma)
    fx = lambda b: 830 + b / total_c * 520
    y_base = 760; b = 0
    d.text((830, 380), 'la forma: cada bloque sube una tercera por lectura', fill=TC, font=F)
    for nom, c, k in forma:
        cents = k * TERCERA
        y = y_base - cents * .2
        i = max(0, k) if k >= 0 else 0                           # el puente es Mi (más lento y grave)
        d.rectangle([fx(b), y - 18, fx(b + c) - 3, y + 18], fill=col(i, .55 if 'puente' in nom else .7))
        d.text((fx(b) + 3, y + 22), nom, fill=TC, font=fuente(11))
        b += c
    return im


espiral().save(PROC / f'01-espiral-de-terceras-s{SEM}.png')
frames = [espiral(f).resize((W * 2 // 3, H * 2 // 3), Image.LANCZOS) for f in list(np.linspace(0, 1, 70)) + [1] * 20]
pal = frames[-1].quantize(colors=128, method=Image.Quantize.MEDIANCUT)
frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
gif = AQUI / f'proceso-espiral-s{SEM}.gif'
frames[0].save(gif, save_all=True, append_images=frames[1:], duration=95, loop=0, optimize=True)
print('gif', f'{gif.stat().st_size / 1e6:.2f} MB', f'{95 * len(frames) / 1000:.1f} s')
