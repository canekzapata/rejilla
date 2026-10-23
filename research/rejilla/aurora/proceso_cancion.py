"""PNGs y GIF de «sobre la aurora» (lee render/aurora/, que deja cancion.py)."""
import json, math, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).parent.parent))
from colores import oklch, fuente
import cancion as K

AQUI = Path(__file__).parent
R = K.R
P = AQUI / 'proceso' / 'cancion'; P.mkdir(parents=True, exist_ok=True)
TAG = K.TAG
V = dict(np.load(R / 'vistas.npz'))
esc = json.load(open(R / 'escalas.json'))['escalas']
part = json.load(open(R / 'partitura.json', encoding='utf-8'))
h0 = (1015 * 47) % 360
FONDO = oklch(.10, .03, h0 + 230)
ORDEN = ['bombo', 'bateria', 'bajo', 'ostinato', 'armonia', 'helecho', 'voz', 'magnetica', 'robot', 'radio', 'ruido']
TONO = {n: h0 + 330 * i / len(ORDEN) for i, n in enumerate(ORDEN)}
NOMBRE = {'bombo': 'sub-bombo', 'bateria': 'placa y polvo', 'bajo': 'sub', 'ostinato': 'piano preparado',
          'armonia': 'piano y órgano', 'helecho': 'helecho', 'voz': 'Sabina', 'magnetica': 'Zira (magnética)',
          'robot': 'robot', 'radio': 'radio', 'ruido': 'ruido → sistema'}
F, Fs, Fl = fuente(18), fuente(13), fuente(22)
TC = tuple(int(c) for c in oklch(.9, .04, h0 + 40))
CW = 16
REF = max(V[n].max() * esc[n] * K.GANANCIA[n] for n in ORDEN)
ascii_ = lambda s: s.replace('♭', 'b').replace('♯', '#')


def capa(clave, n):
    a = V[clave] * esc[n] * K.GANANCIA[n]
    u = .6 * np.clip((20 * np.log10(a / REF + 1e-9) + 72) / 60, 0, 1) ** 1.5
    img = np.repeat(u, CW, 0).T[::-1]
    return img[..., None] * oklch(np.full(img.shape, .8), np.full(img.shape, .16), np.full(img.shape, TONO[n])).astype(float)


def partitura(sufijo=''):
    return np.clip(FONDO + sum(capa(n + sufijo, n) for n in ORDEN), 0, 255).astype(np.uint8)


def rotular(img, titulo, cabeza=None, verso=None):
    pad, arriba, abajo = 22, 44, 92
    out = np.zeros((img.shape[0] + arriba + abajo, img.shape[1] + 2 * pad, 3), np.uint8); out[:] = FONDO
    out[arriba:arriba + img.shape[0], pad:pad + img.shape[1]] = img
    im = Image.fromarray(out); d = ImageDraw.Draw(im)
    d.text((pad, 12), titulo, fill=TC, font=F)
    y = arriba + img.shape[0] + 4
    for sec, cols in K.COLS.items():
        x = pad + cols[0] * CW
        d.line([(x, arriba), (x, y + 28)], fill=tuple(int(c) for c in oklch(.42, .04, h0)), width=1)
        d.text((x + 3, y + 12), ascii_(sec), fill=TC, font=Fs)
    x = pad
    for n in ORDEN:
        c = tuple(int(v) for v in oklch(.8, .16, TONO[n]))
        d.rectangle([x, y + 44, x + 11, y + 55], fill=c); d.text((x + 15, y + 42), NOMBRE[n], fill=TC, font=Fs)
        x += 28 + 8 * len(NOMBRE[n])
    if cabeza is not None:
        d.line([(pad + cabeza, arriba), (pad + cabeza, arriba + img.shape[0])], fill=tuple(int(c) for c in oklch(.97, .05, h0 + 60)), width=2)
    if verso:
        d.text((pad, arriba + img.shape[0] + 66), f'«{ascii_(verso)}»', fill=tuple(int(c) for c in oklch(.92, .1, TONO['voz'])), font=Fl)
    return np.array(im)


escrita, final = partitura('-escrita'), partitura()
Image.fromarray(rotular(escrita, 'sobre la aurora · la partitura como se escribe (1 columna = 1 compás de 2.31 s)')).save(P / f'01-partitura-escrita-{TAG}.png')
Image.fromarray(rotular(final, 'después de los gestos: arena, entropía, espejo, voz en negativo, ruido incorporado')).save(P / f'02-partitura-con-gestos-{TAG}.png')

# 03 · la letra: rollo de la melodía cantada (x = tiempo, y = nota), palabra por sílaba
versos = part['versos']
W3, H3 = 1700, 600
im = Image.new('RGB', (W3, H3), tuple(int(c) for c in FONDO)); d = ImageDraw.Draw(im)
total16 = K.C * 16
fx = lambda a16: 40 + a16 / total16 * (W3 - 80)
fy = lambda m: H3 - 60 - (m - 50) / 22 * (H3 - 190)
for sec, cols in K.COLS.items():
    x = fx(cols[0] * 16); d.line([(x, 50), (x, H3 - 40)], fill=tuple(int(c) for c in oklch(.32, .04, h0)))
    d.text((x + 3, H3 - 36), ascii_(sec), fill=TC, font=Fs)
for k, (sec, ln, cur, notas, pos, dur) in enumerate(versos):
    col = tuple(int(c) for c in oklch(.8, .14, TONO['voz'] + 40 * (k % 3)))
    sil, _ = K.I.silabear(ln)
    for s, n, p, du in zip(sil, notas, pos, dur):
        x0, x1 = fx(cur + p), fx(cur + p + du); yy = fy(n)
        d.rectangle([x0, yy - 3, max(x0 + 2, x1 - 1), yy + 3], fill=col)
    carril = 52 + 15 * (k % 4)                                     # cuatro carriles fijos arriba
    d.line([(fx(cur), carril + 14), (fx(cur), fy(notas[0]) - 4)], fill=tuple(int(c) for c in oklch(.35, .05, TONO['voz'])))
    d.text((fx(cur) + 2, carril), ascii_(ln)[:26], fill=col, font=Fs)
d.text((40, 14), 'la letra cantada: cada barra es una sílaba (x = tiempo, y = nota, Fa3–Sol#4); Zira la canta una octava abajo',
       fill=TC, font=F)
im.save(P / f'03-letra-cantada-{TAG}.png')

# 04 · espectrograma del audio final
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(R / f'sobre-la-aurora-{TAG}.wav'), '-lavfi',
                'showspectrumpic=s=1400x700:mode=combined:scale=log:fscale=log:start=30:stop=14000:color=magma:legend=1',
                str(P / f'04-espectrograma-{TAG}.png')], check=True)

# GIF: la cabeza recorre la partitura con gestos, y abajo el verso que suena
frames, ancho = [], final.shape[1]
for x in list(np.linspace(0, ancho, 100)) + [ancho] * 8:
    xi = int(x); a16 = x / CW * 16
    verso = next((ln for sec, ln, cur, notas, pos, dur in versos if cur <= a16 <= cur + pos[-1] + dur[-1] + 6), None)
    img = final.copy(); img[:, xi:] = (img[:, xi:] * .25 + FONDO * .75).astype(np.uint8)
    fr = rotular(img, 'sobre la aurora · la imagen es la partitura y ffmpeg la toca', cabeza=xi if xi < ancho else None, verso=verso)
    frames.append(Image.fromarray(fr).resize((fr.shape[1] * 3 // 4, fr.shape[0] * 3 // 4), Image.LANCZOS))
pal = frames[-1].quantize(colors=180, method=Image.Quantize.MEDIANCUT)
frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
gif = AQUI / f'proceso-cancion-{TAG}.gif'
frames[0].save(gif, save_all=True, append_images=frames[1:], duration=90, loop=0, optimize=True)
print('gif', f'{gif.stat().st_size / 1e6:.2f} MB', f'{90 * len(frames) / 1000:.1f} s', frames[0].size)
