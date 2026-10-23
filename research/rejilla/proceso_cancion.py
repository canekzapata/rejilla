"""PNGs de etapas y GIF de la canción (lee render/cancion/, que deja musica.py)."""
import json, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from colores import oklch, fuente
import musica as M

AQUI = Path(__file__).parent
R = AQUI / 'render' / 'cancion'
P = AQUI / 'proceso' / 'cancion'
P.mkdir(parents=True, exist_ok=True)
TAG = M.TAG

V = dict(np.load(R / 'vistas.npz'))
info = json.load(open(R / 'partitura.json'))
esc = info['escalas']
C = next(iter(V.values())).shape[0]
CW = 22                                    # px por compás

h0 = (M.SEM * 47) % 360                    # tono base derivado de la semilla
FONDO = oklch(.12, .02, h0 + 200)
ORDEN = ['bombo', 'bajo', 'bateria', 'pad', 'teclas', 'voz', 'congelado']
TONO = {n: h0 + i * 360 / len(ORDEN) * 1.0 for i, n in enumerate(ORDEN)}
NOMBRE = {'bombo': 'bombo', 'bajo': 'bajo', 'bateria': 'caja y hats', 'pad': 'pad', 'teclas': 'rhodes y campanas',
          'voz': 'voz', 'congelado': 'coro congelado'}
F, Fs = fuente(18), fuente(14)


def capa(n):
    """Una pista en dB, 0..1, como luz de su color."""
    a = V[n] * esc[n] * M.GANANCIA[n]
    ref = max(V[k].max() * esc[k] * M.GANANCIA[k] for k in V)
    db = 20 * np.log10(a / ref + 1e-9)
    u = np.clip((db + 78) / 66, 0, 1)                         # (C, VISTA)
    u = np.repeat(u, CW, 0).T[::-1]                           # (VISTA, C*CW), agudos arriba
    col = oklch(np.full(u.shape, .80), np.full(u.shape, .16), np.full(u.shape, TONO[n]))
    return u[..., None] ** 1.3 * col.astype(float)


def partitura(nombres, hasta=None):
    luz = sum(capa(n) for n in nombres)
    img = np.clip(FONDO + luz, 0, 255).astype(np.uint8)
    if hasta is not None: img[:, int(hasta * CW):] = FONDO
    return img


def con_rotulos(img, titulo, nombres, cabeza=None):
    pad, arriba, abajo = 24, 40, 70
    out = np.zeros((img.shape[0] + arriba + abajo, img.shape[1] + 2 * pad, 3), np.uint8); out[:] = FONDO
    out[arriba:arriba + img.shape[0], pad:pad + img.shape[1]] = img
    im = Image.fromarray(out); d = ImageDraw.Draw(im)
    tc = tuple(int(c) for c in oklch(.88, .04, h0 + 40))
    d.text((pad, 10), titulo, fill=tc, font=F)
    y = arriba + img.shape[0] + 6
    sec_ant = None
    for b, (sec, ch) in enumerate(info['forma']):
        x = pad + b * CW
        if sec != sec_ant:
            d.line([(x, arriba), (x, y + 30)], fill=tuple(int(c) for c in oklch(.45, .03, h0)), width=1)
            d.text((x + 3, y + 16), sec, fill=tc, font=Fs); sec_ant = sec
    x = pad
    for n in nombres:
        c = tuple(int(v) for v in oklch(.80, .16, TONO[n]))
        d.rectangle([x, y + 40, x + 12, y + 52], fill=c); d.text((x + 17, y + 38), NOMBRE[n], fill=tc, font=Fs)
        x += 30 + 9 * len(NOMBRE[n])
    if cabeza is not None:
        xx = pad + int(cabeza * CW)
        d.line([(xx, arriba), (xx, arriba + img.shape[0])], fill=tuple(int(c) for c in oklch(.95, .05, h0 + 60)), width=2)
    return np.array(im)


# 01-05: la partitura se arma pista por pista (capas reales del mismo render)
etapas = [(['bombo', 'bajo'], '01-bombo-y-bajo'), (['bombo', 'bajo', 'bateria'], '02-bateria'),
          (['bombo', 'bajo', 'bateria', 'pad', 'teclas'], '03-armonia'),
          (['bombo', 'bajo', 'bateria', 'pad', 'teclas', 'voz'], '04-voz'), (ORDEN, '05-coro-congelado')]
for nombres, nom in etapas:
    img = con_rotulos(partitura(nombres), f'rejilla 02 · la partitura (30 Hz – 14 kHz, log) · 1 columna = 1 compás de 2.5 s', nombres)
    Image.fromarray(img).save(P / f'{nom}-{TAG}.png')

# 06: espectrograma de lo que salió de ffmpeg y se mezcló
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(R / f'cancion-{TAG}.wav'), '-lavfi',
                'showspectrumpic=s=1400x700:mode=combined:scale=log:fscale=log:start=30:stop=14000:color=magma:legend=1',
                str(P / f'06-espectrograma-{TAG}.png')], check=True)

# GIF: la partitura se escribe compás por compás y la cabeza la recorre
full = partitura(ORDEN)
frames = []
pasos = list(np.linspace(0, C, 100)) + [C] * 8
for h in pasos:
    img = full.copy(); img[:, int(h * CW):] = (img[:, int(h * CW):] * 0.18 + FONDO * 0.82).astype(np.uint8)
    fr = con_rotulos(img, f'rejilla 02 · compás {min(int(h) + 1, C):2d}/{C} · la imagen es la partitura, ffmpeg la toca', ORDEN,
                     cabeza=h if h < C else None)
    frames.append(Image.fromarray(fr).resize((fr.shape[1] * 3 // 4, fr.shape[0] * 3 // 4), Image.LANCZOS))
# una sola paleta para todo el GIF, sacada del cuadro completo (si no, cada cuadro decolora la leyenda)
paleta = frames[-1].quantize(colors=160, method=Image.Quantize.MEDIANCUT)
frames = [f.quantize(palette=paleta, dither=Image.Dither.NONE) for f in frames]
gif = AQUI / f'proceso-cancion-{TAG}.gif'
frames[0].save(gif, save_all=True, append_images=frames[1:], duration=90, loop=0, optimize=True)
print('gif', f'{gif.stat().st_size / 1e6:.2f} MB', f'{90 * len(frames) / 1000:.1f} s', frames[0].size)
