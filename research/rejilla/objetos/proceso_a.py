"""Proceso del loop A de «objetos que cantan»: el instrumento que cambia. Carpeta exclusiva proceso/instrumento-<id12>/.

  01  los tres objetos: el espectro de una nota de cada uno (saxofón: todos los armónicos; flauta: pocos y aire;
      barra: parciales inarmónicos que se van)
  02  las transformaciones: espectrogramas de saxofón → flauta, saxofón → percusión y flauta → percusión
  03  la frase que recorre los tres objetos, con quién domina en cada momento
  GIF la frase dibujándose, con el peso de cada lazo (caña, chorro, barra)
  m4a el muestrario: los tres puros y las cuatro transformaciones, uno tras otro
    python proceso_a.py a5
"""
import hashlib, json, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
AQUI = Path(__file__).resolve().parent; R = AQUI / 'render'; ET = sys.argv[1]
ORDEN = ['puro-saxofon', 'puro-flauta', 'puro-golpe', 'sax-a-flauta', 'sax-a-golpe', 'flauta-a-golpe', 'frase-tres-objetos']
nonce = os.urandom(16).hex(); h = hashlib.sha256()
for f in [AQUI / 'motor' / 'objeto.js', Path(__file__)] + [R / f'{ET}-{n}.wav' for n in ORDEN]: h.update(f.read_bytes())
h.update(nonce.encode()); ID = h.hexdigest(); C = ID[:12]; SAL = AQUI / 'proceso' / f'instrumento-{C}'; os.mkdir(SAL)


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
FONDO, TXT, TEN, REJ = oklch(.13, .02, h0), oklch(.92, .03, h0), oklch(.55, .04, h0), oklch(.25, .03, h0)
COL = [oklch(.78, .14, h0 + 30), oklch(.82, .1, h0 + 160), oklch(.8, .13, h0 + 280)]          # caña, chorro, barra
F, Fs, Fg = fuente(14), fuente(12), fuente(22); W = 1500
lee = lambda n: (lambda sr_x: (sr_x[0], sr_x[1].astype(float) / 32768))(wavfile.read(R / f'{ET}-{n}.wav'))


def png(im, n):
    with open(SAL / n, 'xb') as f: im.save(f, 'PNG')


def espectrograma(x, sr, ancho, alto, fmax=6000, tinte=None):
    N, hop = 2048, 256; cols = [np.abs(np.fft.rfft(x[a:a + N] * np.hanning(N))) for a in range(0, len(x) - N, hop)]
    S = 20 * np.log10(np.array(cols).T + 1e-7); fr = np.fft.rfftfreq(N, 1 / sr)
    S = S[np.searchsorted(fr, np.geomspace(60, fmax, alto))]; S = np.clip((S - S.max() + 70) / 70, 0, 1)
    m = Image.fromarray((S[::-1] * 255).astype(np.uint8)).resize((ancho, alto), Image.BILINEAR)
    return Image.composite(Image.new('RGB', (ancho, alto), tinte or TXT), Image.new('RGB', (ancho, alto), FONDO), m)


# 01 los tres objetos: espectro de la nota La3 (la sexta de la escala) de cada uno
im = Image.new('RGB', (W, 520), FONDO); d = ImageDraw.Draw(im)
d.text((24, 16), 'los tres objetos: el espectro de un La3 (0-4 kHz) — la física decide los parciales, no una lista', fill=TXT, font=Fg)
for k, (n, nom) in enumerate([('puro-saxofon', 'saxofón: caña + tubo cónico (todos los armónicos)'), ('puro-flauta', 'flauta: chorro + tubo (pocos armónicos y aire)'),
                              ('puro-golpe', 'barra: golpe + dispersión (parciales inarmónicos)')]):
    sr, x = lee(n); a = int(5 * .55 * sr + .05 * sr); seg = x[a:a + 8192] * np.hanning(8192)
    S = 20 * np.log10(np.abs(np.fft.rfft(seg)) + 1e-9); fr = np.fft.rfftfreq(8192, 1 / sr); m = fr < 4000; S = S[m]; fr = fr[m]
    y0 = 70 + k * 150; d.text((30, y0), nom, fill=COL[k], font=F)
    Xs = lambda f: 30 + (W - 60) * f / 4000; Ys = lambda v: y0 + 130 - 100 * max(0, (v - S.max() + 60) / 60)
    d.line([(Xs(f), Ys(v)) for f, v in zip(fr, S)], fill=COL[k], width=1)
    for armo in range(1, 19): d.line([(Xs(220 * armo), y0 + 20), (Xs(220 * armo), y0 + 132)], fill=REJ)
d.text((30, 500), 'líneas tenues: los armónicos de 220 Hz', fill=TEN, font=Fs)
png(im, f'01-los-tres-objetos-{C}.png')

# 02 las transformaciones
im = Image.new('RGB', (W, 760), FONDO); d = ImageDraw.Draw(im)
d.text((24, 16), 'las transformaciones (60 Hz - 6 kHz): el aire pasa de un lazo a otro y el material cambia', fill=TXT, font=Fg)
for k, (n, nom, a, b) in enumerate([('sax-a-flauta', 'saxofón → flauta (una nota larga)', 1, 6), ('sax-a-golpe', 'saxofón → percusión (el soplo se acorta hasta ser golpe)', 1, 6.5),
                                    ('flauta-a-golpe', 'flauta → percusión', 1, 6.5)]):
    sr, x = lee(n); y0 = 60 + k * 230; esp = espectrograma(x, sr, W - 60, 180, tinte=COL[[1, 2, 2][k]]); im.paste(esp, (30, y0 + 26))
    d.text((30, y0), nom, fill=TXT, font=F); dur = len(x) / sr
    for t, lbl in ((a, 'empieza'), (b, 'termina')): xx = 30 + (W - 60) * t / dur; d.line([(xx, y0 + 22), (xx, y0 + 206)], fill=TEN); d.text((xx + 4, y0 + 208), lbl, fill=TEN, font=Fs)
png(im, f'02-las-transformaciones-{C}.png')

# 03 la frase de los tres objetos (pesos de cada lazo sobre el tiempo)
sr, x = lee('frase-tres-objetos'); dur = len(x) / sr
TRAMOS = [(0, 'saxofon', 'saxofon', 1), (2.5, 'saxofon', 'flauta', 3.5), (5.5, 'flauta', 'golpe', 6.5), (8.5, 'golpe', 'saxofon', 9.8)]
IDX = {'saxofon': 0, 'flauta': 1, 'golpe': 2}
def pesos(t):
    for t0, a, b, t1 in reversed(TRAMOS):
        if t >= t0:
            u = min(1, max(0, (t - t0) / (t1 - t0))); w = [0, 0, 0]; w[IDX[a]] += 1 - u; w[IDX[b]] += u; return w
    return [1, 0, 0]
def frase(hasta, ancho=W, alto=520, titulo=True):
    im = Image.new('RGB', (ancho, alto), FONDO); d = ImageDraw.Draw(im); m = 24
    if titulo: d.text((m, 14), 'una frase que cambia de objeto: saxofón → flauta → percusión → saxofón', fill=TXT, font=Fg if ancho > 1000 else F)
    esp = espectrograma(x[:int(hasta * sr)] if hasta < dur else x, sr, max(2, int((ancho - 2 * m) * min(hasta, dur) / dur)), alto - 200)
    im.paste(esp, (m, 60))
    for i in range(int((ancho - 2 * m) * min(hasta, dur) / dur)):
        w = pesos(i / (ancho - 2 * m) * dur); y = alto - 120
        for k in range(3): d.line([(m + i, y + k * 34 + 26), (m + i, y + k * 34 + 26 - 26 * w[k])], fill=COL[k])
    for k, nom in enumerate(['caña', 'chorro', 'barra']): d.text((m + 4, alto - 120 + k * 34 + 6), nom, fill=TXT, font=Fs)
    return im
png(frase(dur), f'03-la-frase-{C}.png')
frames = [frase(t, 760, 420, titulo=False) for t in np.linspace(.4, dur, 44)]
pal = frames[-1].quantize(colors=64, method=Image.Quantize.MEDIANCUT); frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
gif = AQUI / f'el-objeto-que-cambia-{C}.gif'
with open(gif, 'xb') as fh: frames[0].save(fh, 'GIF', save_all=True, append_images=frames[1:] + [frames[-1]] * 4, duration=200, loop=0, optimize=True)

# el muestrario: uno tras otro, con un respiro de 0.5 s
partes = []
for n in ORDEN:
    sr, x = lee(n); partes += [x / (np.abs(x).max() + 1e-9) * .8, np.zeros(int(.5 * sr))]
wav = R / f'muestrario-{C}.wav'; wavfile.write(wav, sr, (np.concatenate(partes) * 32767).astype(np.int16))
m4a = AQUI / f'muestrario-objetos-{C}.m4a'
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-i', str(wav), '-af', 'loudnorm=I=-16:TP=-1.5', '-c:a', 'aac', '-b:a', '192k', str(m4a)], check=True)
sha = lambda q: hashlib.sha256(Path(q).read_bytes()).hexdigest()
with open(SAL / f'receta-{C}.json', 'x', encoding='utf-8') as fh:
    json.dump({'id': ID, 'nonce': nonce, 'etiqueta': ET, 'orden_muestrario': ORDEN, 'medidas': json.load(open(R / f'transformaciones-{ET}.json', encoding='utf-8')),
               'archivos': {str(q.relative_to(AQUI)).replace('\\', '/'): sha(q) for q in sorted(SAL.glob('*.png')) + [gif, m4a]}}, fh, ensure_ascii=False, indent=1)
print(C, f'gif {gif.stat().st_size / 1e6:.2f} MB {200 * (len(frames) + 4) / 1000:.1f} s')
