"""Muestrario del loop B de «los pixeles y la luna»: un audio con las demos en orden, una ficha por
demo (espectrograma + qué es) y un GIF que las recorre."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy.io import wavfile
sys.path.insert(0, str(Path(__file__).parent.parent))
from colores import oklch, fuente
import demos as D

AQUI = Path(__file__).parent
PROC = AQUI / 'proceso' / 'instrumentos'; PROC.mkdir(parents=True, exist_ok=True)
h0 = 255 + np.random.default_rng(5454).uniform(-12, 12)
FONDO = tuple(int(c) for c in oklch(.13, .05, h0)); TC = tuple(int(c) for c in oklch(.93, .04, h0 + 160))
F, Fs = fuente(19), fuente(14)
ascii_ = lambda s: s.replace('♭', 'b').replace('♯', '#')

pedazos, marcas, t = [], [], 0.0
for n in D.TODAS:
    sr, x = wavfile.read(D.R / f'{n}.final.wav'); x = x.astype(float) / 32768
    marcas.append((n, round(t, 2))); pedazos += [x, np.zeros((sr, 2))]; t += len(x) / sr + 1
wavfile.write(D.R / 'muestrario.wav', sr, (np.concatenate(pedazos) * 32767).astype(np.int16))
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(D.R / 'muestrario.wav'), '-c:a', 'aac',
                '-b:a', '192k', str(AQUI / 'muestrario-instrumentos-s5454.m4a')], check=True)
json.dump(marcas, open(D.DEMOS / 'marcas.json', 'w'))

fichas = []
for i, n in enumerate(D.TODAS):
    spec = D.R / f'{n}.spec.png'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(D.R / f'{n}.final.wav'), '-lavfi',
                    'showspectrumpic=s=900x380:mode=combined:scale=log:fscale=log:start=40:stop=14000:color=magma:legend=0',
                    str(spec)], check=True)
    sp = Image.open(spec).convert('RGB')
    im = Image.new('RGB', (sp.width + 40, sp.height + 120), FONDO); d = ImageDraw.Draw(im)
    d.text((20, 12), n, fill=TC, font=F)
    linea, y = '', 40
    for pal in ascii_(D.TITULO[n]).split():
        if len(linea) + len(pal) > 100: d.text((20, y), linea, fill=TC, font=Fs); y += 18; linea = ''
        linea += pal + ' '
    d.text((20, y), linea, fill=TC, font=Fs)
    im.paste(sp, (20, 110))
    im.save(PROC / f'{i + 1:02d}-{n}-s5454.png'); fichas.append(im)

frames = [f.resize((f.width * 2 // 3, f.height * 2 // 3), Image.LANCZOS) for f in fichas for _ in range(3)]
pal = frames[0].quantize(colors=200, method=Image.Quantize.MEDIANCUT)
frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
gif = AQUI / 'proceso-instrumentos-s5454.gif'
frames[0].save(gif, save_all=True, append_images=frames[1:], duration=480, loop=0, optimize=True)
print('gif', f'{gif.stat().st_size / 1e6:.2f} MB', f'{480 * len(frames) / 1000:.1f} s', '· muestrario', f'{t:.1f} s')
