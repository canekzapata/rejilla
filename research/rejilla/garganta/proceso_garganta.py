"""Proceso de «la misma garganta» (loop 07). Carpeta exclusiva proceso/la-misma-garganta-<id12>/, con el id de
la entrega (el del m4a y su receta).

  01  las capas: la curva de cada instrumento a lo largo de los 60 compases (tejer, no cortar)
  02  las dos voces: notas de la partitura y altura medida; la tierra (PSOLA) sube, la nave (ardilla) baja, La3
  03  el espectrograma de la mezcla, con las secciones
  04  las medidas: bandas por sección, voz sobre el resto, afinación y el encuentro (distancia espectral)
  05  la niebla en tres borradores (e2, e3, e4): medios por segundo en los primeros 22 s
  GIF las dos voces dibujándose hasta encontrarse
    python proceso_garganta.py e4 02c404e621cf
  (la mezcla entregada: render/e4-mezcla.wav, la del m4a; las versiones nuevas se llaman <et>-mezcla-v<k>.wav)
"""
import json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, resample_poly
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[2] / 'meleeviewer' / 'output' / 'Arte' / '2026-10-09_yoshi_es_un_vector_16_jpop'))
import cantante as K
A = K.A
ET, C = sys.argv[1], sys.argv[2]
R = AQUI / 'render'
P = json.load(open(R / f'{ET}-partitura.json', encoding='utf-8')); T, NC = P['T'], P['compases']
MED = json.load(open(R / f'{ET}-medidas.json', encoding='utf-8')); MEZCLA = R / f'{ET}-mezcla.wav'; VOC = json.load(open(R / f'{ET}-voces.json', encoding='utf-8'))
ENC = json.load(open(R / f'{ET}-encuentro.json', encoding='utf-8'))
SAL = AQUI / 'proceso' / f'la-misma-garganta-{C}'; os.mkdir(SAL)


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


h0 = 20 + int(C[:4], 16) % 320
FONDO, TXT, TEN, REJ = oklch(.13, .025, h0), oklch(.9, .03, h0 + 20), oklch(.5, .04, h0), oklch(.22, .02, h0)
COL_T, COL_N, COL_U = oklch(.72, .14, h0 + 30), oklch(.8, .12, h0 + 190), oklch(.92, .09, h0 + 100)
F, Fs, Fg = fuente(14), fuente(11), fuente(22)
SECC = [('niebla', 0, 8), ('verso 1', 8, 20), ('coro', 20, 28), ('puente', 28, 36), ('verso 2', 36, 48), ('coro final', 48, 56), ('la misma', 56, 60)]


def png(im, n):
    with open(SAL / n, 'xb') as f: im.save(f, 'PNG')


def secciones(d, X, y0, y1):
    for ns, b0, b1 in SECC:
        d.line([(X(b0 * T), y0), (X(b0 * T), y1)], fill=REJ); d.text((X(b0 * T) + 4, y0 + 2), ns, fill=TEN, font=Fs)


W = 1500; dur = NC * T; X = lambda t: 60 + (W - 100) * t / dur

# 01 las capas
nombres = list(P['curvas'])
H = 110 + 46 * len(nombres); im = Image.new('RGB', (W, H), FONDO); d = ImageDraw.Draw(im)
d.text((30, 16), 'la misma garganta · las capas: cada instrumento cambia con su propia curva (nada se corta)', fill=TXT, font=Fg)
secciones(d, X, 56, H - 10)


def curva(K, b):
    if b <= K[0][0]: return K[0][1]
    for i in range(1, len(K)):
        if b <= K[i][0]:
            u = (b - K[i - 1][0]) / (K[i][0] - K[i - 1][0]); u = u * u * (3 - 2 * u); return K[i - 1][1] + (K[i][1] - K[i - 1][1]) * u
    return K[-1][1]


for j, nb in enumerate(nombres):
    y = 110 + 46 * j; col = oklch(.7, .12, h0 + 37 * j)
    pts = [(X(b * T), y + 30 - 30 * curva(P['curvas'][nb], b)) for b in np.linspace(0, NC, 600)]
    d.polygon(pts + [(X(dur), y + 30), (X(0), y + 30)], fill=oklch(.3, .06, h0 + 37 * j)); d.line(pts, fill=col, width=2)
    d.text((8, y + 10), nb[:7], fill=TXT, font=Fs)
png(im, f'01-las-capas-{C}.png')

# 02 las dos voces (notas + altura medida)
f0s = {}
for pista in ('tierra', 'nave', 'una'):
    sr, x = wavfile.read(R / f'{ET}-{pista}.wav'); x = resample_poly(x.mean(axis=1), 1, 4); sr //= 4
    f0, _ = A.curva(x, sr); f0s[pista] = (f0, sr)
m0, m1 = 38, 84; H2 = 640
Y = lambda m: H2 - 70 - (H2 - 160) * (m - m0) / (m1 - m0)


def voces(hasta, ancho=W, alto=H2, titulo=True):
    im = Image.new('RGB', (W, H2), FONDO); d = ImageDraw.Draw(im)
    if titulo:
        d.text((30, 16), 'las dos voces: la tierra (PSOLA) sube, la nave (ardilla) baja; en La3 los dos modos son el mismo sonido', fill=TXT, font=Fg)
    secciones(d, X, 56, H2 - 40)
    for m, nm in ((45, 'La2'), (57, 'La3'), (69, 'La4'), (81, 'La5')):
        d.line([(X(0), Y(m)), (X(dur), Y(m))], fill=oklch(.3, .05, h0) if m == 57 else REJ, width=2 if m == 57 else 1); d.text((10, Y(m) - 7), nm, fill=TEN, font=Fs)
    for r in P['partitura']:
        col = {'T': COL_T, 'N': COL_N, 'U': COL_U}[r['quien']]
        for e in r['eventos']:
            if e['t'] > hasta: continue
            d.rectangle([X(e['t']), Y(e['nota']) - 3, X(min(e['t'] + e['dur'], hasta)), Y(e['nota']) + 3], outline=col)
    for pista, col in (('tierra', COL_T), ('nave', COL_N), ('una', COL_U)):
        f0, sr = f0s[pista]; pts = []
        for i in range(0, min(len(f0), int(hasta * sr)), max(1, int(sr * .01))):
            if not np.isnan(f0[i]): pts.append((X(i / sr), Y(69 + 12 * np.log2(f0[i] / 440))))
            elif len(pts) > 1: d.line(pts, fill=col, width=2); pts = []
            else: pts = []
        if len(pts) > 1: d.line(pts, fill=col, width=2)
    d.text((30, H2 - 30), '■ tierra (PSOLA, grave, cerca)', fill=COL_T, font=F); d.text((330, H2 - 30), '■ nave (ardilla, aguda, por teléfono)', fill=COL_N, font=F)
    d.text((690, H2 - 30), '■ una sola voz', fill=COL_U, font=F); d.text((860, H2 - 30), 'rectángulos: notas de la partitura · líneas: altura medida', fill=TEN, font=F)
    return im


png(voces(dur), f'02-las-dos-voces-{C}.png')

# 03 espectrograma de la mezcla (frecuencia logarítmica 40 Hz - 8 kHz)
sr, x = wavfile.read(MEZCLA); x = x.mean(axis=1)
N, hop = 4096, 1200; cols = []
for a in range(0, len(x) - N, hop): cols.append(np.abs(np.fft.rfft(x[a:a + N] * np.hanning(N))))
S = 20 * np.log10(np.array(cols).T + 1e-7); fr = np.fft.rfftfreq(N, 1 / sr)
filas = np.geomspace(40, 8000, 360); idx = np.searchsorted(fr, filas)
S = S[idx]; S = np.clip((S - S.max() + 75) / 75, 0, 1)
H3 = 520; im = Image.new('RGB', (W, H3), FONDO); d = ImageDraw.Draw(im)
d.text((30, 16), 'la mezcla (40 Hz - 8 kHz, escala logarítmica): la niebla, el groove que entra en foco, el puente que se desenfoca', fill=TXT, font=Fg)
esp = Image.fromarray((S[::-1] * 255).astype(np.uint8)).resize((W - 100, 400), Image.BILINEAR)
tinte = Image.new('RGB', esp.size, oklch(.85, .1, h0 + 60)); im.paste(Image.composite(tinte, Image.new('RGB', esp.size, FONDO), esp), (60, 80))
secciones(d, X, 60, 490)
for f in (55, 220, 880, 3520): d.text((8, 80 + 400 * (1 - np.log(f / 40) / np.log(8000 / 40)) - 6), f'{f}', fill=TEN, font=Fs)
png(im, f'03-espectrograma-{C}.png')

# 04 medidas
im = Image.new('RGB', (W, 600), FONDO); d = ImageDraw.Draw(im)
d.text((30, 16), 'medidas: bandas por sección (dB respecto al total), voz sobre el resto, afinación y el encuentro', fill=TXT, font=Fg)
bandas = ['sub', 'graves', 'medios', 'presencia', 'aire']
for j, b in enumerate(bandas): d.text((240 + 110 * j, 60), b, fill=TEN, font=F)
d.text((800, 60), 'voz − resto', fill=TEN, font=F)
for i, (ns, _, _) in enumerate(SECC):
    y = 90 + 34 * i; m = MED[ns]; d.text((30, y), ns, fill=TXT, font=F)
    for j, b in enumerate(bandas):
        v = m[b]; w = max(2, 100 * (1 + v / 40)); d.rectangle([240 + 110 * j, y, 240 + 110 * j + w * .9, y + 18], fill=oklch(.62, .1, h0 + 30 * j))
        d.text((244 + 110 * j, y + 2), f'{v:.0f}', fill=FONDO, font=Fs)
    v = m['voz_sobre_resto_dB']; d.text((800, y), f'{v:+.1f} dB', fill=TXT if v > -2 or ns == 'niebla' else oklch(.7, .15, 25), font=F)
y = 360
for pista, col in (('tierra', COL_T), ('nave', COL_N), ('una', COL_U)):
    v = VOC[pista]; d.text((30, y), f"{pista}: {v['palabras']} palabras, mediana {v['mediana_cents']} cents, {v['a_mas_de_50']} a más de 50", fill=col, font=F); y += 26
y += 16; d.text((30, y), 'el encuentro (distancia espectral entre las dos voces, 0 = el mismo sonido):', fill=TXT, font=F); y += 30
for k, v in ENC.items():
    w = 900 * v['distancia_espectral'] / .35; d.rectangle([330, y, 330 + w, y + 18], fill=oklch(.7, .12, h0 + 150)); d.text((30, y), k, fill=TEN, font=Fs)
    d.text((340 + w, y + 1), f"{v['distancia_espectral']}", fill=TXT, font=Fs); y += 28
png(im, f'04-medidas-{C}.png')

# 05 la niebla en tres borradores
im = Image.new('RGB', (W, 420), FONDO); d = ImageDraw.Draw(im)
d.text((30, 16), 'la niebla en tres borradores: medios (300 Hz - 4 kHz) por segundo, respecto al verso 1', fill=TXT, font=Fg)
d.text((30, 46), 'pistas e2 y e3 con la mezcla intermedia (pared +16 dB y sin sub en la niebla; la primera mezcla de e2, con su hoyo de', fill=TEN, font=F)
d.text((30, 64), '−25 dB, se escribió encima: la midió el log, no se conserva) · e4: la partitura corregida, la que se entregó', fill=TEN, font=F)
Xn = lambda s: 80 + (W - 140) * s / 22; Yn = lambda v: 110 + 260 * (-v) / 30
for v in (0, -10, -20, -30): d.line([(Xn(0), Yn(v)), (Xn(22), Yn(v))], fill=REJ); d.text((30, Yn(v) - 7), f'{v}', fill=TEN, font=Fs)
d.line([(Xn(8 * T), 100), (Xn(8 * T), 380)], fill=TEN); d.text((Xn(8 * T) + 4, 100), 'entra la voz', fill=TEN, font=Fs)
sos = butter(4, [300, 4000], 'band', fs=48000, output='sos')
for k, et in enumerate(('e2', 'e3', 'e4')):
    if not (R / f'{et}-mezcla.wav').exists(): continue
    sr, y_ = wavfile.read(R / f'{et}-mezcla.wav'); m = sosfilt(sos, y_[:, 0].astype(float))
    cu = 10 * np.log10(np.mean(m[int(19 * sr):int(40 * sr)] ** 2))
    v = [10 * np.log10(np.mean(m[int(s * sr):int((s + 1) * sr)] ** 2) + 1e-12) - cu for s in range(22)]
    col = oklch(.55 + .13 * k, .13, h0 + 60 * k)
    d.line([(Xn(s + .5), Yn(max(-30, q))) for s, q in enumerate(v)], fill=col, width=3); d.text((Xn(21.2), Yn(max(-30, v[-1])) - 18), et, fill=col, font=F)
png(im, f'05-la-niebla-tres-borradores-{C}.png')

# GIF: las dos voces dibujándose (40 cuadros, 240 ms)
frames = [voces(t).resize((900, 384), Image.LANCZOS) for t in np.linspace(8 * T, dur, 40)]
pal = frames[-1].quantize(colors=64, method=Image.Quantize.MEDIANCUT)
frames = [fr.quantize(palette=pal, dither=Image.Dither.NONE) for fr in frames]
gif = AQUI / f'dos-alturas-una-garganta-{C}.gif'
with open(gif, 'xb') as fh: frames[0].save(fh, 'GIF', save_all=True, append_images=frames[1:] + [frames[-1]] * 4, duration=220, loop=0, optimize=True)
print(C, f'gif {gif.stat().st_size / 1e6:.2f} MB {220 * (len(frames) + 4) / 1000:.1f} s')
