"""PNGs de etapas y GIF de Esquinas (lee render/esquinas/, que deja esquinas.py)."""
import json, math, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from colores import oklch, fuente
import esquinas as E

M = E.M
AQUI = Path(__file__).parent
R = AQUI / 'render' / 'esquinas'
P = AQUI / 'proceso' / 'esquinas'
P.mkdir(parents=True, exist_ok=True)
TAG = E.TAG

V = dict(np.load(R / 'vistas.npz'))
info = json.load(open(R / 'partitura.json'))
esc = info['escalas']
h0 = (E.SEM * 47) % 360
FONDO = oklch(.11, .025, h0 + 250)
TONO = {n: h0 + i * 360 / len(E.NOMBRES) for i, n in enumerate(E.NOMBRES)}
NOMBRE = {'bombo': 'bombo', 'bateria': 'clap, hats, leño', 'sub': 'sub y fretless', 'piano': 'piano',
          'voz': 'voces', 'pad': 'acordes que dicen / azúcar', 'metal': 'Zawinul y campanas'}
F, Fs = fuente(18), fuente(14)
TC = tuple(int(c) for c in oklch(.9, .04, h0 + 40))
OCT = round(M.VISTA * math.log(2) / math.log(14000 / 30))        # una octava, en píxeles de la vista
gan = lambda k: E.GANANCIA[k.replace('-piso', '')]
REF = max(V[k].max() * esc[k] * gan(k) for k in V)
CW = 26


def columnas(clave, cols, ancho, sube=0):
    """Columnas de una pista como luz de su color (VISTA, n*ancho, 3), agudos arriba, subida `sube` px."""
    n = clave.replace('-piso', '')
    a = V[clave][cols] * esc[clave] * gan(clave)
    u = 0.55 * np.clip((20 * np.log10(a / REF + 1e-9) + 74) / 62, 0, 1) ** 1.6     # 0.55: siete pistas sumadas no revientan a blanco
    l = u[..., None] * oklch(np.full(u.shape, .80), np.full(u.shape, .16), np.full(u.shape, TONO[n])).astype(float)
    img = np.repeat(l, ancho, 0).transpose(1, 0, 2)[::-1]
    if sube: img = np.concatenate([img[sube:], np.zeros((sube,) + img.shape[1:])], 0)
    return img


def linea_de_tiempo(nombres):
    """Pregunta+Esquina | la Esquina a mitad de ancho y una octava arriba, dos veces (+ piso) | lo demás."""
    q0, q1 = info['col']['esquina']
    tramos = []
    for n in nombres:
        d = columnas(n, slice(q0, q1), CW // 2, sube=OCT)
        d = np.concatenate([d, d], 1)
        if n + '-piso' in V: d = d + columnas(n + '-piso', slice(0, 8), CW)[:, :d.shape[1]]
        tramos.append(np.concatenate([columnas(n, slice(0, q1), CW), d, columnas(n, slice(q1, None), CW)], 1))
    return np.clip(FONDO + sum(tramos), 0, 255).astype(np.uint8)


SECC = [('pregunta', 0), ('esquina', 8), ('doble ×2', 16), ('misterioso', 24), ('esquina', 28), ('coda', 36)]
def rotular(img, titulo, nombres, cabeza=None, secc=SECC):
    pad, arriba, abajo = 22, 40, 74
    out = np.zeros((img.shape[0] + arriba + abajo, img.shape[1] + 2 * pad, 3), np.uint8); out[:] = FONDO
    out[arriba:arriba + img.shape[0], pad:pad + img.shape[1]] = img
    im = Image.fromarray(out); d = ImageDraw.Draw(im)
    d.text((pad, 10), titulo, fill=TC, font=F)
    y = arriba + img.shape[0] + 6
    for nom, b0 in secc:
        x = pad + b0 * CW
        d.line([(x, arriba), (x, y + 30)], fill=tuple(int(c) for c in oklch(.45, .04, h0)), width=1)
        d.text((x + 3, y + 14), nom, fill=TC, font=Fs)
    x = pad
    for n in nombres:
        c = tuple(int(v) for v in oklch(.80, .16, TONO[n]))
        d.rectangle([x, y + 42, x + 12, y + 54], fill=c); d.text((x + 17, y + 40), NOMBRE[n], fill=TC, font=Fs)
        x += 32 + 8 * len(NOMBRE[n])
    if cabeza is not None:
        d.line([(pad + cabeza, arriba), (pad + cabeza, arriba + img.shape[0])],
               fill=tuple(int(c) for c in oklch(.97, .05, h0 + 60)), width=2)
    return np.array(im)


# 01 · las voces: la sílaba como la dijo la TTS (gris) y afinada a Mi4 (color): más aguda = más corta
sil = [('sí', 'sabina'), ('no', 'sabina'), ('es', 'sabina'), ('qui', 'sabina'), ('na', 'sabina'), ('bri', 'sabina'),
       ('llan', 'sabina'), ('te', 'sabina'), ('o', 'sabina'), ('tra', 'sabina'), ('vez', 'sabina'), ('mal', 'sabina'),
       ('wrong', 'zira'), ('again', 'zira'), ('yes', 'zira'), ('no', 'zira'), ('corner', 'zira')]
W1, fila = 1300, 64
im = Image.new('RGB', (W1, 60 + fila * len(sil)), tuple(int(c) for c in FONDO)); d = ImageDraw.Draw(im)
d.text((20, 14), 'las voces: sílaba de la TTS (gris) → afinada a Mi4 por remuestreo (color). Más aguda = más corta.', fill=TC, font=F)
esc_t = (W1 - 220) / 0.45
for i, (s, v) in enumerate(sil):
    y0 = 60 + i * fila + fila // 2
    x, f = E.silaba(s, v); yv = E.chop(s, 64, v)
    d.text((20, y0 - 9), f'{s} · {v} · {f:.0f} Hz', fill=TC, font=Fs)
    for w, col, dy in ((x, oklch(.5, .02, h0), -12), (yv, oklch(.8, .15, TONO['voz'] + 20 * i), 12)):
        n = len(w); paso = max(1, n // 1000)
        xs = lambda j: 210 + j / E.S * esc_t
        top = [(xs(j), y0 + dy - float(w[j:j + paso].max()) * 11) for j in range(0, n, paso)]
        bot = [(xs(j), y0 + dy - float(w[j:j + paso].min()) * 11) for j in range(0, n, paso)][::-1]
        d.polygon(top + bot, fill=tuple(int(c) for c in col))
im.save(P / f'01-voces-{TAG}.png')

# 02 · un acorde que dice «sí» y «no»
im = Image.new('RGB', (1300, 540), tuple(int(c) for c in FONDO)); d = ImageDraw.Draw(im)
d.text((20, 14), 'un acorde que dice una vocal: los armónicos de D7 (sin raíz) pesados por la envolvente de «sí» y de «no»', fill=TC, font=F)
fx = lambda f: 60 + f / 5000 * 1180
for k, (txt, y0) in enumerate((('sí', 260), ('no', 500))):
    env = E.envolvente_vocal(txt)
    col = tuple(int(c) for c in oklch(.82, .15, TONO['pad'] + 120 * k))
    for n in E.dom7(38)[1:]:
        f = M.hz(n + 12)
        for h in range(1, 26):
            if h * f > 5000: break
            a = env(h * f) / h ** 0.4
            d.line([(fx(h * f), y0), (fx(h * f), y0 - a * 170)], fill=tuple(int(c) for c in oklch(.6, .1, TONO['pad'] + 120 * k)), width=2)
    d.line([(fx(f), y0 - env(f) * 170) for f in np.linspace(50, 5000, 600)], fill=col, width=2)
    d.text((fx(4300), y0 - 190), f'«{txt}»', fill=col, font=F)
    d.text((fx(0) - 10, y0 + 6), '0 Hz', fill=TC, font=Fs); d.text((fx(5000) - 30, y0 + 6), '5 kHz', fill=TC, font=Fs)
im.save(P / f'02-acorde-que-dice-{TAG}.png')

# 03 · la imagen tal como se escribe: 31 columnas (la Doble no ocupa columnas)
base = np.clip(FONDO + sum(columnas(n, slice(None), CW) for n in E.NOMBRES), 0, 255).astype(np.uint8)
secc_base = [(k, v[0]) for k, v in info['col'].items()]
Image.fromarray(rotular(base, 'la imagen que se escribe: 31 columnas, un compás cada una (30 Hz – 14 kHz, log)', E.NOMBRES,
                        secc=secc_base)).save(P / f'03-imagen-escrita-{TAG}.png')

# 04 · lo que suena: la Esquina leída a 2×S = mitad de ancho y una octava arriba, dos veces, con su piso
tl = linea_de_tiempo(E.NOMBRES)
Image.fromarray(rotular(tl, 'lo que suena: la Esquina al doble = mitad de ancho, una octava arriba',
                        E.NOMBRES)).save(P / f'04-linea-de-tiempo-{TAG}.png')

# 05 · espectrograma del audio final
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(R / f'esquinas-{TAG}.wav'), '-lavfi',
                'showspectrumpic=s=1400x700:mode=combined:scale=log:fscale=log:start=30:stop=14000:color=magma:legend=1',
                str(P / f'05-espectrograma-{TAG}.png')], check=True)

# GIF: la cabeza recorre lo que suena
frames, ancho = [], tl.shape[1]
for x in list(np.linspace(0, ancho, 100)) + [ancho] * 8:
    img = tl.copy(); xi = int(x)
    img[:, xi:] = (img[:, xi:] * 0.2 + FONDO * 0.8).astype(np.uint8)
    fr = rotular(img, 'Esquinas · al doble de sample rate: doble tempo y una octava arriba',
                 E.NOMBRES, cabeza=xi if xi < ancho else None)
    frames.append(Image.fromarray(fr).resize((fr.shape[1] * 3 // 4, fr.shape[0] * 3 // 4), Image.LANCZOS))
paleta = frames[-1].quantize(colors=160, method=Image.Quantize.MEDIANCUT)
frames = [f.quantize(palette=paleta, dither=Image.Dither.NONE) for f in frames]
gif = AQUI / f'proceso-esquinas-{TAG}.gif'
frames[0].save(gif, save_all=True, append_images=frames[1:], duration=90, loop=0, optimize=True)
print('gif', f'{gif.stat().st_size / 1e6:.2f} MB', f'{90 * len(frames) / 1000:.1f} s', frames[0].size)
