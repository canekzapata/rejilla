"""Proceso de «epístrofe» (loop 08). Carpeta exclusiva proceso/epistrofe-<id12>/ con el id de la entrega.

  01  el laberinto: las 24 tríadas en círculo (quintas, cada mayor junto a su relativa menor), los pasillos que
      excavó la semilla y el recorrido
  02  los caminantes: en qué tríada está el bajo y en cuál el piano, compás por compás (coinciden en 0, 21, 60, 61)
  03  el espectrograma de la mezcla, con las secciones
  04  las medidas: bandas por sección, voz sobre el resto, afinación
  05  el muro en dos borradores: e2 (sonaba medio segundo por compás: la limpieza caía dentro de la ventana) y e3
  GIF los dos caminantes recorriendo el laberinto; cuando coinciden, el muro se aclara
    python proceso_epistrofe.py e3 e8c37024f3ea e3-mezcla-v2
"""
import json, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
AQUI = Path(__file__).resolve().parent
ET, C, MEZ = sys.argv[1], sys.argv[2], sys.argv[3]
R = AQUI / 'render'
P = json.load(open(R / f'{ET}-partitura.json', encoding='utf-8')); T = P['T']
MED = json.load(open(R / f'{MEZ}-medidas.json', encoding='utf-8'))['secciones']
VOC = json.load(open(R / f'{ET}-voces.json', encoding='utf-8'))
SAL = AQUI / 'proceso' / f'epistrofe-{C}'; os.mkdir(SAL)
# el laberinto y los caminantes, del mismo motor (node)
js = ("require('./motor/cancion.js'); const C = globalThis.Cancion; const cam = C.camino(); const pasos = [];"
      "for (let b = 0; b < 64; b += .25) pasos.push([b].concat(C.caminantes(b + .01)));"
      "console.log(JSON.stringify({camino: cam, pasos}));")
D = json.loads(subprocess.run(['node', '-e', js], cwd=AQUI, capture_output=True, text=True, encoding='utf-8', check=True).stdout)


def oklch(L, Cc, hh):
    a, b = Cc * np.cos(np.radians(hh)), Cc * np.sin(np.radians(hh))
    l_, m_, s_ = L + .3963377774 * a + .2158037573 * b, L - .1055613458 * a - .0638541728 * b, L - .0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    rgb = np.clip([4.0767416621 * l - 3.3077115913 * m + .2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - .3413193965 * s,
                   -.0041960863 * l - .7034186147 * m + 1.7076147010 * s], 0, 1)
    rgb = np.where(rgb <= .0031308, 12.92 * rgb, 1.055 * rgb ** (1 / 2.4) - .055)
    return tuple(int(round(c * 255)) for c in rgb)


def fuente(n):
    try: return ImageFont.truetype('C:/Windows/Fonts/consola.ttf', n)
    except OSError: return ImageFont.load_default()


h0 = int(C[:4], 16) % 360
FONDO, TXT, TEN, REJ = oklch(.13, .025, h0), oklch(.9, .03, h0 + 20), oklch(.5, .04, h0), oklch(.24, .03, h0)
COL_B, COL_P, COL_ENC = oklch(.75, .15, h0 + 40), oklch(.78, .12, h0 + 200), oklch(.95, .08, h0 + 110)
F, Fs, Fg = fuente(14), fuente(12), fuente(22)
SECC = [('muro', 0, 8), ('verso 1', 8, 24), ('coro', 24, 32), ('callejón', 32, 40), ('verso 2', 40, 48), ('coro final', 48, 56), ('salida', 56, 64)]
NOM = ['Do', 'Do♯', 'Re', 'Mi♭', 'Mi', 'Fa', 'Fa♯', 'Sol', 'La♭', 'La', 'Si♭', 'Si']


rot = lambda n: n.replace('♭', 'b')   # Consolas no trae ♭ (salía un cuadrito)


def png(im, n):
    with open(SAL / n, 'xb') as f: im.save(f, 'PNG')


# posiciones: círculo de quintas, cada mayor seguida de su relativa menor (24 puntos)
orden = []
for k in range(12):
    r = (k * 7) % 12; orden += [NOM[r], NOM[(r + 9) % 12] + 'm']
def pos(nombre, cx, cy, rad):
    i = orden.index(nombre); a = -np.pi / 2 + 2 * np.pi * i / 24
    return cx + rad * np.cos(a), cy + rad * np.sin(a)


cam = D['camino']; aristas = {tuple(sorted((cam[i], cam[i + 1]))) for i in range(len(cam) - 1)}


def laberinto(W, H, bajo=None, piano=None, titulo=None, rastro=0):
    im = Image.new('RGB', (W, H), FONDO); d = ImageDraw.Draw(im)
    cx, cy, rad = W / 2, H / 2 + (14 if titulo else 0), min(W, H) * .38
    for o in orden: x, y = pos(o, cx, cy, rad); d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=REJ)
    for a, b in aristas: d.line([pos(a, cx, cy, rad), pos(b, cx, cy, rad)], fill=oklch(.33, .05, h0), width=2)
    if rastro:                                                     # el tramo ya recorrido por el bajo
        for i in range(min(rastro, len(cam) - 1)): d.line([pos(cam[i], cx, cy, rad), pos(cam[i + 1], cx, cy, rad)], fill=oklch(.55, .1, h0 + 40), width=3)
    for o in orden:
        x, y = pos(o, cx, cy, rad * 1.1); d.text((x - 12, y - 7), rot(o), fill=TEN, font=Fs)
    enc = bajo is not None and bajo == piano
    for quien, col, r in ((piano, COL_P, 11), (bajo, COL_B, 8)):
        if quien is None: continue
        x, y = pos(quien, cx, cy, rad); c = COL_ENC if enc else col
        d.ellipse([x - r, y - r, x + r, y + r], outline=c, width=3)
    if titulo: d.text((24, 16), titulo, fill=TXT, font=Fg)
    return im, enc


im, _ = laberinto(1100, 900, titulo='el laberinto: 24 tríadas, los pasillos que excavó la semilla (cada paso mueve una voz)', rastro=len(cam))
d = ImageDraw.Draw(im); d.text((24, 860), 'recorrido: ' + ' → '.join(map(rot, cam[:16])) + ' …', fill=TEN, font=Fs)
png(im, f'01-el-laberinto-{C}.png')

# 02 los caminantes compás por compás
W = 1500; im = Image.new('RGB', (W, 560), FONDO); d = ImageDraw.Draw(im)
d.text((24, 16), 'los caminantes: la tríada del bajo (abajo) y la del piano (arriba); donde coinciden, el muro es un solo espectro', fill=TXT, font=Fg)
X = lambda b: 60 + (W - 100) * b / 64
for ns, b0, b1 in SECC: d.line([(X(b0), 60), (X(b0), 520)], fill=REJ); d.text((X(b0) + 4, 60), ns, fill=TEN, font=Fs)
Yo = lambda nombre, base: base - 120 * orden.index(nombre) / 23
for k in range(len(D['pasos']) - 1):
    b, tb, tp = D['pasos'][k]; b2 = D['pasos'][k + 1][0]
    d.line([(X(b), Yo(tb, 500)), (X(b2), Yo(tb, 500))], fill=COL_B, width=3); d.line([(X(b), Yo(tp, 260)), (X(b2), Yo(tp, 260))], fill=COL_P, width=3)
    if tb == tp: d.rectangle([X(b), 280, X(b2), 370], fill=COL_ENC)
d.text((60, 290), 'coinciden', fill=TEN, font=Fs)
png(im, f'02-los-caminantes-{C}.png')

# 03 espectrograma de la mezcla
sr, x = wavfile.read(R / f'{MEZ}.wav'); x = x.mean(axis=1)
N, hop = 4096, 1200; cols = [np.abs(np.fft.rfft(x[a:a + N] * np.hanning(N))) for a in range(0, len(x) - N, hop)]
S = 20 * np.log10(np.array(cols).T + 1e-7); fr = np.fft.rfftfreq(N, 1 / sr)
S = S[np.searchsorted(fr, np.geomspace(40, 9000, 400))]; S = np.clip((S - S.max() + 72) / 72, 0, 1)
im = Image.new('RGB', (W, 540), FONDO); d = ImageDraw.Draw(im)
d.text((24, 16), 'la mezcla (40 Hz - 9 kHz, logarítmica): muros, el funk que entra, el callejón roto, la salida que se aclara', fill=TXT, font=Fg)
esp = Image.fromarray((S[::-1] * 255).astype(np.uint8)).resize((W - 100, 420), Image.BILINEAR)
im.paste(Image.composite(Image.new('RGB', esp.size, oklch(.85, .12, h0 + 60)), Image.new('RGB', esp.size, FONDO), esp), (60, 80))
dur = len(x) / sr; Xs = lambda t: 60 + (W - 100) * t / dur
for ns, b0, b1 in SECC: d.line([(Xs(b0 * T), 60), (Xs(b0 * T), 510)], fill=REJ); d.text((Xs(b0 * T) + 4, 60), ns, fill=TEN, font=Fs)
png(im, f'03-espectrograma-{C}.png')

# 04 medidas
im = Image.new('RGB', (W, 520), FONDO); d = ImageDraw.Draw(im)
d.text((24, 16), 'medidas: bandas por sección (dB respecto al total), voz sobre el resto y afinación', fill=TXT, font=Fg)
bandas = ['sub', 'graves', 'medios', 'presencia', 'aire']
for j, b in enumerate(bandas): d.text((240 + 110 * j, 60), b, fill=TEN, font=F)
d.text((800, 60), 'total', fill=TEN, font=F); d.text((900, 60), 'voz − resto', fill=TEN, font=F)
for i, (ns, _, _) in enumerate(SECC):
    y = 90 + 34 * i; m = MED[ns]; d.text((30, y), ns, fill=TXT, font=F)
    for j, b in enumerate(bandas):
        w = max(2, 100 * (1 + m[b] / 40)); d.rectangle([240 + 110 * j, y, 240 + 110 * j + w * .9, y + 18], fill=oklch(.62, .1, h0 + 30 * j))
        d.text((244 + 110 * j, y + 2), f'{m[b]:.0f}', fill=FONDO, font=Fs)
    d.text((800, y), f"{m['total_dB']:.1f}", fill=TXT, font=F)
    v = m['voz_sobre_resto_dB']; d.text((900, y), '—' if v is None or ns == 'muro' else f'{v:+.1f} dB', fill=TXT, font=F)
y = 360
for pista, col in (('ardilla', COL_P), ('grave', COL_B)):
    v = VOC[pista]; d.text((30, y), f"{pista}: {v['palabras']} sílabas, mediana {v['mediana_cents']} cents, {v['a_mas_de_50']} a más de 50 "
                                    "(casi todas: la consonante siguiente ya canta con la nota nueva)", fill=col, font=F); y += 28
png(im, f'04-medidas-{C}.png')

# 05 el muro en dos borradores
im = Image.new('RGB', (W, 380), FONDO); d = ImageDraw.Draw(im)
d.text((24, 16), 'el muro en dos borradores: nivel cada 0.25 s en los primeros 20 s', fill=TXT, font=Fg)
d.text((24, 46), 'e2: la limpieza de cada compás caía dentro de la ventana de anticipación y cortaba el muro al medio segundo · e3: se sostiene', fill=TEN, font=F)
Xn = lambda s: 70 + (W - 120) * s / 20; Yn = lambda v: 100 + 240 * (-v) / 80
for v in (-20, -40, -60, -80): d.line([(Xn(0), Yn(v)), (Xn(20), Yn(v))], fill=REJ); d.text((24, Yn(v) - 7), f'{v}', fill=TEN, font=Fs)
for k, et in enumerate(('e2', 'e3')):
    sr, y_ = wavfile.read(R / f'{et}-muro.wav'); y_ = y_.mean(axis=1)
    v = [max(-80, 20 * np.log10(y_[int(s * sr):int((s + .25) * sr)].std() + 1e-9)) for s in np.arange(0, 20, .25)]
    col = oklch(.55 + .2 * k, .14, h0 + 120 * k)
    d.line([(Xn(s + .125), Yn(q)) for s, q in zip(np.arange(0, 20, .25), v)], fill=col, width=3); d.text((Xn(19.3), Yn(v[-1]) - 20), et, fill=col, font=F)
png(im, f'05-el-muro-dos-borradores-{C}.png')

# GIF: los caminantes en el laberinto (un cuadro por compás, 64 cuadros a 150 ms = 9.6 s)
frames = []
for b in range(64):
    _, tb, tp = D['pasos'][b * 4]
    paso = min(len(cam) - 1, int(b * (len(cam) - 1) / 62))
    im, enc = laberinto(640, 640, tb, tp, rastro=paso)
    dd = ImageDraw.Draw(im); sec = [s for s in SECC if s[1] <= b < s[2]][0][0]
    dd.text((18, 14), f'compás {b:2d} · {sec}', fill=TXT, font=F); dd.text((18, 36), f'bajo {rot(tb)}   piano {rot(tp)}' + ('   · un solo espectro' if enc else ''), fill=COL_ENC if enc else TEN, font=Fs)
    frames.append(im)
pal = frames[21].quantize(colors=48, method=Image.Quantize.MEDIANCUT)
frames = [fr.quantize(palette=pal, dither=Image.Dither.NONE) for fr in frames]
gif = AQUI / f'tres-caminantes-{C}.gif'
with open(gif, 'xb') as fh: frames[0].save(fh, 'GIF', save_all=True, append_images=frames[1:], duration=150, loop=0, optimize=True)
print(C, f'gif {gif.stat().st_size / 1e6:.2f} MB {150 * len(frames) / 1000:.1f} s')
