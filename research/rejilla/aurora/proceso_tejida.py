"""El telar de «sobre la aurora» (loop D): cada instrumento es un hilo y su color cambia al recorrer
sus versiones (limpio → arena / ruido / espejo / negativo / acorde). Lee render/aurora-tejida/."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).parent.parent))
from colores import oklch, fuente
import cancion as K
import cancion_tejida as D

AQUI = Path(__file__).parent
P = AQUI / 'proceso' / 'tejida'; P.mkdir(parents=True, exist_ok=True)
TAG = D.TAG
curvas = json.load(open(D.R2 / 'curvas.json'))
h0 = (1015 * 47) % 360
FONDO = oklch(.10, .03, h0 + 230)
TC = tuple(int(c) for c in oklch(.9, .04, h0 + 40))
F, Fs = fuente(18), fuente(13)
HILOS = ['bombo', 'bateria', 'bajo', 'ostinato', 'armonia', 'helecho', 'robot', 'voz', 'magnetica', 'ruido']
W, H = 1600, 720
x0, x1 = 150, W - 30
total = K.C
fx = lambda b: x0 + b / total * (x1 - x0)
GESTO_TONO = {'tormenta': 60, 'entropía': 150, 'confundo': 300, 'se expande': 220, 'sistema': 20}


def telar(hasta=None):
    im = Image.new('RGB', (W, H), tuple(int(c) for c in FONDO)); d = ImageDraw.Draw(im)
    d.text((20, 14), 'sobre la aurora · el telar: cada hilo es un instrumento; el color es cuánto se ha ido hacia su versión (arena, ruido, espejo, negativo, acorde)',
           fill=TC, font=F)
    for sec, cols in K.COLS.items():
        x = fx(cols[0]); d.line([(x, 50), (x, H - 40)], fill=tuple(int(c) for c in oklch(.3, .04, h0)))
        d.text((x + 3, H - 34), sec.replace('í', 'i'), fill=TC, font=Fs)
    paso = (H - 120) / len(HILOS)
    for j, n in enumerate(HILOS):
        y = 70 + j * paso + paso / 2
        d.text((20, y - 8), n, fill=TC, font=Fs)
        base = oklch(.42, .02, h0 + 200)
        lim = fx(total) if hasta is None else fx(hasta)
        d.line([(x0, y), (lim, y)], fill=tuple(int(c) for c in base), width=2)
        for clave, (c0, u) in curvas.items():
            nom, sec = clave.split('|')
            if nom != n: continue
            u = np.array(u)
            ts = c0 + np.arange(len(u)) * 480 / D.SR_OUT / D.T
            for k in range(0, len(u) - 1, 3):
                if hasta is not None and ts[k] > hasta: break
                v = float(np.clip(u[k], 0, 1))
                col = oklch(.42 + .45 * v, .02 + .16 * v, GESTO_TONO.get(sec, 0) + h0)
                grosor = 2 + int(9 * v)
                yy = y + 5 * np.sin(ts[k] * 2.3 + j) * v                 # el hilo tiembla cuando cambia
                d.line([(fx(ts[k]), yy), (fx(ts[k + 1] if k + 1 < len(ts) else ts[k]), yy)],
                       fill=tuple(int(c) for c in col), width=grosor)
    if hasta is not None:
        d.line([(fx(hasta), 50), (fx(hasta), H - 40)], fill=tuple(int(c) for c in oklch(.97, .05, h0 + 60)), width=2)
    return im


telar().save(P / f'01-telar-{TAG}.png')
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(D.R2 / f'sobre-la-aurora-{TAG}.wav'), '-lavfi',
                'showspectrumpic=s=1400x700:mode=combined:scale=log:fscale=log:start=30:stop=14000:color=magma:legend=1',
                str(P / f'02-espectrograma-{TAG}.png')], check=True)
# 03: antes y después, el tramo entropía + confundo (lo que Canek señaló), en espectrograma
for nom, ruta in (('C', K.R / f'sobre-la-aurora-{K.TAG}.wav'), ('D', D.R2 / f'sobre-la-aurora-{TAG}.wav')):
    a, b = K.COLS['entropía'][0] * K.T, (K.COLS['confundo'][-1] + 1) * K.T
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-ss', f'{a:.2f}', '-to', f'{b:.2f}', '-i', str(ruta),
                    '-lavfi', 'showspectrumpic=s=1200x500:mode=combined:scale=log:fscale=log:start=30:stop=14000:color=magma:legend=0',
                    str(P / f'03-entropia-confundo-loop{nom}.png')], check=True)

frames = []
for h in list(np.linspace(0, total, 100)) + [total] * 8:
    frames.append(telar(h if h < total else None).resize((W * 2 // 3, H * 2 // 3), Image.LANCZOS))
pal = frames[-1].quantize(colors=160, method=Image.Quantize.MEDIANCUT)
frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
gif = AQUI / f'proceso-telar-{TAG}.gif'
frames[0].save(gif, save_all=True, append_images=frames[1:], duration=90, loop=0, optimize=True)
print('gif', f'{gif.stat().st_size / 1e6:.2f} MB', f'{90 * len(frames) / 1000:.1f} s')
