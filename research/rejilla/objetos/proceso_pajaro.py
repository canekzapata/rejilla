"""Proceso del pájaro (instrumento 6). Carpeta exclusiva proceso/pajaro-<id12>/.

  01  la siringe: la misma oscilación de los labios (van der Pol) con presión baja (casi un silbido puro) y alta (ronca)
  02  los gestos: silbidos, trinos, gorjeo y chips, ronco, carpintero (espectrogramas)
  03  el canto a lo Messiaen (modo 2) con la segunda voz de la siringe
  GIF el canto dibujándose
  m4a muestrario de todos los gestos
    python proceso_pajaro.py b2
"""
import hashlib, json, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
AQUI = Path(__file__).resolve().parent; R = AQUI / 'render'; ET = sys.argv[1]
ORDEN = ['silbidos', 'trinos', 'gorjeo-chips', 'canto-messiaen', 'ronco', 'carpintero']
nonce = os.urandom(16).hex(); h = hashlib.sha256()
for f in [AQUI / 'motor' / 'pajaro.js', Path(__file__)] + [R / f'{ET}-pajaro-{n}.wav' for n in ORDEN]: h.update(f.read_bytes())
h.update(nonce.encode()); ID = h.hexdigest(); C = ID[:12]; SAL = AQUI / 'proceso' / f'pajaro-{C}'; os.mkdir(SAL)


def oklch(L, Cc, hh):
    a, b = Cc * np.cos(np.radians(hh)), Cc * np.sin(np.radians(hh))
    l_, m_, s_ = L + .3963377774 * a + .2158037573 * b, L - .1055613458 * a - .0638541728 * b, L - .0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    rgb = np.clip([4.0767416621 * l - 3.3077115913 * m + .2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - .3413193965 * s,
                   -.0041960863 * l - .7034186147 * m + 1.7076147010 * s], 0, 1)
    rgb = np.where(rgb <= .0031308, 12.92 * rgb, 1.055 * rgb ** (1 / 2.4) - .055)
    return tuple(int(round(c * 255)) for c in rgb)


try: F, Fs, Fg = (ImageFont.truetype('C:/Windows/Fonts/consola.ttf', k) for k in (14, 12, 22))
except OSError: F = Fs = Fg = ImageFont.load_default()
h0 = 60 + int(C[:4], 16) % 90                                       # el pájaro: verdes y amarillos, derivados del id
FONDO, TXT, TEN = oklch(.13, .02, h0), oklch(.92, .03, h0), oklch(.55, .04, h0)
W = 1500
lee = lambda n: (lambda q: (q[0], q[1].astype(float) / 32768))(wavfile.read(R / f'{ET}-pajaro-{n}.wav'))


def png(im, n):
    with open(SAL / n, 'xb') as f: im.save(f, 'PNG')


def espectrograma(x, sr, ancho, alto, tinte, fmin=400, fmax=12000, N=1024):
    hop = max(48, len(x) // 1500); cols = [np.abs(np.fft.rfft(x[a:a + N] * np.hanning(N))) for a in range(0, len(x) - N, hop)]
    S = 20 * np.log10(np.array(cols).T + 1e-7); fr = np.fft.rfftfreq(N, 1 / sr); S = S[np.searchsorted(fr, np.geomspace(fmin, fmax, alto))]
    S = np.clip((S - S.max() + 60) / 60, 0, 1); m = Image.fromarray((S[::-1] * 255).astype(np.uint8)).resize((ancho, alto), Image.BILINEAR)
    return Image.composite(Image.new('RGB', (ancho, alto), tinte), Image.new('RGB', (ancho, alto), FONDO), m)


# 01 la siringe: van der Pol x'' = −ω² x + ω (p − x²) x', con p = 0.1 y p = 1.8 (la misma ecuación del motor)
im = Image.new('RGB', (W, 440), FONDO); dr = ImageDraw.Draw(im)
dr.text((24, 16), 'la siringe: los labios oscilan como van der Pol — presión baja: casi un silbido puro; presión alta: ronco (relajación)', fill=TXT, font=Fg)
for k, (p, nom) in enumerate([(.1, 'presión 0.1 (silbido)'), (1.8, 'presión 1.8 (ronco)')]):
    f, sr = 1000, 192000; w = 2 * np.pi * f; dt = 1 / sr; x, v = .01, 0; xs = []
    for i in range(int(.012 * sr)):
        v += dt * (-w * w * x + w * (p - x * x) * v); x += dt * v; xs.append(x)
    xs = np.array(xs[-int(.004 * sr):]); xs /= np.abs(xs).max()
    y0 = 120 + k * 160; dr.text((30, y0 - 50), nom, fill=TXT, font=F)
    dr.line([(40 + (W - 80) * i / len(xs), y0 + 40 - 60 * v_) for i, v_ in enumerate(xs)], fill=oklch(.82, .13, h0 + 40 * k), width=2)
png(im, f'01-la-siringe-{C}.png')

# 02 los gestos
im = Image.new('RGB', (W, 60 + 3 * 220), FONDO); dr = ImageDraw.Draw(im)
dr.text((24, 16), 'los gestos (400 Hz - 12 kHz): silbidos · trinos · gorjeo y chips · canto · ronco · carpintero', fill=TXT, font=Fg)
for k, n in enumerate(ORDEN):
    sr, x = lee(n); col, fila = k % 2, k // 2; ancho = (W - 90) // 2
    im.paste(espectrograma(x, sr, ancho, 170, oklch(.85, .12, h0 + 22 * k), 150 if n in ('ronco', 'carpintero') else 400), (30 + col * (ancho + 30), 80 + fila * 220))
    dr.text((30 + col * (ancho + 30), 60 + fila * 220), n, fill=TXT, font=F)
png(im, f'02-los-gestos-{C}.png')

# 03 el canto a lo Messiaen + GIF
sr, x = lee('canto-messiaen'); dur = len(x) / sr
def lamina(hasta, ancho, alto, titulo=True):
    im = Image.new('RGB', (ancho, alto), FONDO); dr = ImageDraw.Draw(im)
    if titulo: dr.text((20, 14), 'un canto a lo Messiaen: modo 2 (octatónico) en células que se repiten y cambian; abajo, la segunda voz de la siringe', fill=TXT, font=Fg)
    n = int(len(x) * min(1, hasta / dur)); w = max(2, int((ancho - 40) * min(1, hasta / dur)))
    if n > 2048: im.paste(espectrograma(x[:n], sr, w, alto - 90, oklch(.86, .13, h0 + 30), 500, 8000), (20, 60))
    return im
png(lamina(dur, W, 520), f'03-canto-messiaen-{C}.png')
frames = [lamina(t, 760, 380, False) for t in np.linspace(.2, dur, 40)]
pal = frames[-1].quantize(colors=64, method=Image.Quantize.MEDIANCUT); frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
gif = AQUI / f'canto-de-pajaro-{C}.gif'
with open(gif, 'xb') as fh: frames[0].save(fh, 'GIF', save_all=True, append_images=frames[1:] + [frames[-1]] * 6, duration=200, loop=0, optimize=True)

partes = []
for n in ORDEN:
    sr, x = lee(n); partes += [x / (np.abs(x).max() + 1e-9) * .8, np.zeros(int(.4 * sr))]
wav = R / f'muestrario-pajaro-{C}.wav'; wavfile.write(wav, sr, (np.concatenate(partes) * 32767).astype(np.int16))
m4a = AQUI / f'muestrario-pajaro-{C}.m4a'
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-i', str(wav), '-af', 'loudnorm=I=-16:TP=-1.5', '-c:a', 'aac', '-b:a', '192k', str(m4a)], check=True)
sha = lambda q: hashlib.sha256(Path(q).read_bytes()).hexdigest()
with open(SAL / f'receta-{C}.json', 'x', encoding='utf-8') as fh:
    json.dump({'id': ID, 'nonce': nonce, 'etiqueta': ET, 'orden_muestrario': ORDEN,
               'archivos': {str(q.relative_to(AQUI)).replace('\\', '/'): sha(q) for q in sorted(SAL.glob('*.png')) + [gif, m4a]}}, fh, ensure_ascii=False, indent=1)
print(C, f'gif {gif.stat().st_size / 1e6:.2f} MB {200 * (len(frames) + 6) / 1000:.1f} s')
