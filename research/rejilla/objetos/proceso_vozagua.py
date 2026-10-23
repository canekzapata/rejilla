"""Proceso del watervoicephone (instrumento 7). Carpeta exclusiva proceso/vozagua-<id12>/.

  01  los pulsos: 40 ms de una «a» cantada; cada pulso de la nota suelta burbujas en los formantes
  02  el agua aprende a hablar: la misma frase con voz 0 → 1/3 → 2/3 → 1 (espectrograma)
  03  dos vocales a la vez: la envolvente armónica de cada par, con los formantes de las dos vocales marcados
  04  los modos: susurro, canto, gárgara y dos voces de agua (espectrogramas)
  GIF el agua aprendiendo a hablar, dibujándose
  m4a muestrario de todos los demos
    python proceso_vozagua.py v5
"""
import hashlib, json, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
AQUI = Path(__file__).resolve().parent; R = AQUI / 'render'; ET = sys.argv[1]
ORDEN = ['susurro', 'canto', 'gargara', 'aprende', 'dos-voces', 'dos-vocales']
FOR = {'a': [800, 1200, 2500], 'e': [450, 1900, 2550], 'i': [300, 2300, 3000], 'o': [500, 880, 2400], 'u': [330, 780, 2300]}
nonce = os.urandom(16).hex(); h = hashlib.sha256()
for f in [AQUI / 'motor' / 'vozagua.js', Path(__file__)] + [R / f'{ET}-vozagua-{n}.wav' for n in ORDEN]: h.update(f.read_bytes())
h.update(nonce.encode()); ID = h.hexdigest(); C = ID[:12]; SAL = AQUI / 'proceso' / f'vozagua-{C}'; os.mkdir(SAL)


def oklch(L, Cc, hh):
    a, b = Cc * np.cos(np.radians(hh)), Cc * np.sin(np.radians(hh))
    l_, m_, s_ = L + .3963377774 * a + .2158037573 * b, L - .1055613458 * a - .0638541728 * b, L - .0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    rgb = np.clip([4.0767416621 * l - 3.3077115913 * m + .2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - .3413193965 * s,
                   -.0041960863 * l - .7034186147 * m + 1.7076147010 * s], 0, 1)
    rgb = np.where(rgb <= .0031308, 12.92 * rgb, 1.055 * rgb ** (1 / 2.4) - .055)
    return tuple(int(round(c * 255)) for c in rgb)


try: F, Fg = (ImageFont.truetype('C:/Windows/Fonts/consola.ttf', k) for k in (14, 22))
except OSError: F = Fg = ImageFont.load_default()
h0 = 190 + int(C[:4], 16) % 70                                      # agua que habla: azules y turquesas, derivados del id
FONDO, TXT, TEN = oklch(.13, .025, h0), oklch(.92, .03, h0), oklch(.55, .05, h0)
W = 1500
lee = lambda n: (lambda q: (q[0], q[1].astype(float) / 32768))(wavfile.read(R / f'{ET}-vozagua-{n}.wav'))
meta = lambda n: json.load(open(R / f'{ET}-vozagua-{n}.json', encoding='utf-8'))


def png(im, n):
    with open(SAL / n, 'xb') as f: im.save(f, 'PNG')


def espectrograma(x, sr, ancho, alto, tinte, fmin=100, fmax=9000, N=2048):
    hop = max(48, len(x) // 1500); cols = [np.abs(np.fft.rfft(x[a:a + N] * np.hanning(N))) for a in range(0, len(x) - N, hop)]
    S = 20 * np.log10(np.array(cols).T + 1e-7); fr = np.fft.rfftfreq(N, 1 / sr); S = S[np.searchsorted(fr, np.geomspace(fmin, fmax, alto))]
    S = np.clip((S - S.max() + 60) / 60, 0, 1); m = Image.fromarray((S[::-1] * 255).astype(np.uint8)).resize((ancho, alto), Image.BILINEAR)
    return Image.composite(Image.new('RGB', (ancho, alto), tinte), Image.new('RGB', (ancho, alto), FONDO), m)


# 01 los pulsos: 40 ms de la «a» de «la» en el canto
sr, x = lee('canto'); e = [q for q in meta('canto')['eventos'] if q['texto'] == 'la'][0]; f0 = 440 * 2 ** ((e['nota'] - 69) / 12)
a = int((e['t'] + .15) * sr); seg = x[a:a + int(.04 * sr)]; seg = seg / np.abs(seg).max()
im = Image.new('RGB', (W, 420), FONDO); dr = ImageDraw.Draw(im)
dr.text((24, 16), f'los pulsos: 40 ms de la «a» de «la» ({f0:.0f} Hz). Cada pulso suelta burbujas en F1 800, F2 1200, F3 2500 Hz', fill=TXT, font=Fg)
for k in range(int(.04 * f0) + 1):
    xx = 40 + (W - 80) * k / (f0 * .04); dr.line([(xx, 70), (xx, 380)], fill=TEN, width=1)
dr.line([(40 + (W - 80) * i / len(seg), 225 - 140 * v) for i, v in enumerate(seg)], fill=oklch(.84, .12, h0), width=2)
dr.text((40, 390), 'líneas: los pulsos de la glotis de agua (1/f0); la onda: las burbujas que nacen en cada uno', fill=TXT, font=F)
png(im, f'01-los-pulsos-{C}.png')

# 02 el agua aprende a hablar
sr, x = lee('aprende'); dur = len(x) / sr; ev = meta('aprende')['eventos']


def lamina(hasta, ancho, alto, titulo=True):
    im = Image.new('RGB', (ancho, alto), FONDO); dr = ImageDraw.Draw(im); top = 60 if titulo else 34
    if titulo: dr.text((20, 14), 'el agua aprende a hablar: «aprendo a hablar» con voz 0 (burbujas al azar) → 1/3 → 2/3 → 1 (en los formantes)', fill=TXT, font=Fg)
    n = int(len(x) * min(1, hasta / dur)); w = max(2, int((ancho - 40) * min(1, hasta / dur)))
    if n > 4096: im.paste(espectrograma(x[:n], sr, w, alto - top - 20, oklch(.86, .12, h0 + 20)), (20, top))
    for q in ev:
        if q['texto'] == 'aprendo' and q['t'] < hasta: dr.text((20 + (ancho - 40) * q['t'] / dur, top - 22), f"voz {q['voz']:.2f}", fill=TXT, font=F)
    return im


png(lamina(dur, W, 560), f'02-el-agua-aprende-a-hablar-{C}.png')
frames = [lamina(t, 760, 380, False) for t in np.linspace(.3, dur, 40)]

# 03 dos vocales a la vez: envolvente armónica de cada par
sr, x = lee('dos-vocales'); ev = meta('dos-vocales')['eventos']
im = Image.new('RGB', (W, 100 + 4 * 150), FONDO); dr = ImageDraw.Draw(im)
dr.text((24, 16), 'dos vocales a la vez: amplitud de cada armónico (barras) y formantes de las dos vocales (marcas arriba / abajo)', fill=TXT, font=Fg)
X = lambda f: 120 + (W - 160) * np.log(f / 150) / np.log(3600 / 150)
for k, q in enumerate(ev):
    a, b = int((q['t'] + .25 * q['dur']) * sr), int((q['t'] + .85 * q['dur']) * sr); seg = x[a:b]
    fp = 440 * 2 ** ((q['nota'] - 69) / 12); n = np.arange(len(seg)); hn = np.hanning(len(seg))
    amp = np.array([20 * np.log10(abs(np.sum(seg * hn * np.exp(-2j * np.pi * j * fp * n / sr))) + 1e-9) for j in range(1, int(3600 / fp))]); amp -= amp.max()
    y0 = 80 + k * 150; v1, v2 = q['texto'][0], q['doble']; dr.text((24, y0 + 50), f'{v1} + {v2}', fill=TXT, font=Fg)
    for j, A in enumerate(amp):
        hgt = max(0, 40 + A) / 40 * 100; dr.line([(X((j + 1) * fp), y0 + 115), (X((j + 1) * fp), y0 + 115 - hgt)], fill=oklch(.8, .1, h0 + 10), width=4)
    for fm in FOR[v1][:3]: dr.polygon([(X(fm) - 6, y0), (X(fm) + 6, y0), (X(fm), y0 + 10)], fill=oklch(.8, .15, h0 + 120))
    for fm in FOR[v2][:3]: dr.polygon([(X(fm) - 6, y0 + 130), (X(fm) + 6, y0 + 130), (X(fm), y0 + 120)], fill=oklch(.8, .15, h0 - 120))
    dr.text((X(FOR[v1][0]) + 10, y0 - 4), v1, fill=TXT, font=F); dr.text((X(FOR[v2][0]) + 10, y0 + 118), v2, fill=TXT, font=F)
for fm in (200, 500, 1000, 2000, 3000): dr.text((X(fm) - 14, 100 + 4 * 150 - 22), f'{fm} Hz', fill=TEN, font=F)
png(im, f'03-dos-vocales-a-la-vez-{C}.png')

# 04 los modos
im = Image.new('RGB', (W, 60 + 2 * 240), FONDO); dr = ImageDraw.Draw(im)
dr.text((24, 16), 'los modos (100 Hz - 9 kHz): susurro (sin altura) · canto · gárgara (compuerta y gorgoteo) · dos voces de agua', fill=TXT, font=Fg)
for k, n in enumerate(['susurro', 'canto', 'gargara', 'dos-voces']):
    sr, xx = lee(n); col, fila = k % 2, k // 2; ancho = (W - 90) // 2
    im.paste(espectrograma(xx, sr, ancho, 190, oklch(.85, .12, h0 + 25 * k)), (30 + col * (ancho + 30), 80 + fila * 240))
    dr.text((30 + col * (ancho + 30), 60 + fila * 240), n, fill=TXT, font=F)
png(im, f'04-los-modos-{C}.png')

pal = frames[-1].quantize(colors=64, method=Image.Quantize.MEDIANCUT); frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
gif = AQUI / f'el-agua-aprende-a-hablar-{C}.gif'
with open(gif, 'xb') as fh: frames[0].save(fh, 'GIF', save_all=True, append_images=frames[1:] + [frames[-1]] * 6, duration=200, loop=0, optimize=True)
partes = []
for n in ORDEN:
    sr, xx = lee(n); partes += [xx / (np.abs(xx).max() + 1e-9) * .8, np.zeros(int(.5 * sr))]
wav = R / f'muestrario-vozagua-{C}.wav'; wavfile.write(wav, sr, (np.concatenate(partes) * 32767).astype(np.int16))
m4a = AQUI / f'muestrario-vozagua-{C}.m4a'
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-i', str(wav), '-af', 'loudnorm=I=-16:TP=-1.5', '-c:a', 'aac', '-b:a', '192k', str(m4a)], check=True)
sha = lambda q: hashlib.sha256(Path(q).read_bytes()).hexdigest()
with open(SAL / f'receta-{C}.json', 'x', encoding='utf-8') as fh:
    json.dump({'id': ID, 'nonce': nonce, 'etiqueta': ET, 'orden_muestrario': ORDEN,
               'archivos': {str(q.relative_to(AQUI)).replace('\\', '/'): sha(q) for q in sorted(SAL.glob('*.png')) + [gif, m4a]}}, fh, ensure_ascii=False, indent=1)
print(C, f'gif {gif.stat().st_size / 1e6:.2f} MB {200 * (len(frames) + 6) / 1000:.1f} s')
