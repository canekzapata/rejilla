"""Muestrario del loop B: un audio con todas las demos en orden, una ficha PNG por demo
(espectrograma + qué es) y un GIF que las recorre."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy.io import wavfile
sys.path.insert(0, str(Path(__file__).parent.parent))
from colores import oklch, fuente
import demos as D

MODO = 'espectral' if 'espectral' in sys.argv else ('oscuras' if 'oscuras' in sys.argv else '')
LISTA = {'espectral': D.ESPECTRAL, 'oscuras': D.OSCURAS}.get(MODO, D.TODAS)
SUF = {'espectral': '-espectral', 'oscuras': '-oscuro'}.get(MODO, '')

AQUI = Path(__file__).parent
PROC = AQUI / 'proceso' / {'espectral': 'instrumentos-espectral', 'oscuras': 'instrumentos-oscuros'}.get(MODO, 'instrumentos'); PROC.mkdir(parents=True, exist_ok=True)
h0 = (1015 * 47) % 360
FONDO = tuple(int(c) for c in oklch(.12, .03, h0 + 230)); TC = tuple(int(c) for c in oklch(.9, .04, h0 + 40))
F, Fs = fuente(19), fuente(14)

# audio: todas las demos con 1 s de silencio entre ellas
pedazos, marcas, t = [], [], 0.0
for n in LISTA:
    sr, x = wavfile.read(D.R / f'{n}.final.wav'); x = x.astype(float) / 32768
    marcas.append((n, round(t, 2))); pedazos += [x, np.zeros((sr, 2))]; t += len(x) / sr + 1
mues = np.concatenate(pedazos)
wavfile.write(D.R / f'muestrario{SUF}.wav', sr, (mues * 32767).astype(np.int16))
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(D.R / f'muestrario{SUF}.wav'), '-c:a', 'aac',
                '-b:a', '192k', str(AQUI / f'muestrario-instrumentos{SUF}-s1015.m4a')], check=True)
json.dump(marcas, open(D.DEMOS / f'marcas{SUF}.json', 'w'))

# fichas
fichas = []
for i, n in enumerate(LISTA):
    spec = D.R / f'{n}.spec.png'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(D.R / f'{n}.final.wav'), '-lavfi',
                    'showspectrumpic=s=900x380:mode=combined:scale=log:fscale=log:start=40:stop=14000:color=magma:legend=0',
                    str(spec)], check=True)
    sp = Image.open(spec).convert('RGB')
    im = Image.new('RGB', (sp.width + 40, sp.height + 110), FONDO); d = ImageDraw.Draw(im)
    titulo = D.TITULO[n].replace('♭', 'b').replace('♯', '#')
    d.text((20, 12), f'{n}', fill=TC, font=F)
    linea, y = '', 40
    for pal in titulo.split():
        if len(linea) + len(pal) > 100: d.text((20, y), linea, fill=TC, font=Fs); y += 18; linea = ''
        linea += pal + ' '
    d.text((20, y), linea, fill=TC, font=Fs)
    im.paste(sp, (20, 100))
    im.save(PROC / f'{i + 1:02d}-{n}-s1015.png')
    fichas.append(im)

frames = [f.resize((f.width * 2 // 3, f.height * 2 // 3), Image.LANCZOS) for f in fichas for _ in range(2)]
pal = frames[0].quantize(colors=200, method=Image.Quantize.MEDIANCUT)
frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
gif = AQUI / f'proceso-instrumentos{SUF}-s1015.gif'
frames[0].save(gif, save_all=True, append_images=frames[1:], duration=430, loop=0, optimize=True)
print('gif', f'{gif.stat().st_size / 1e6:.2f} MB', f'{430 * len(frames) / 1000:.1f} s', '· muestrario', f'{t:.1f} s')
