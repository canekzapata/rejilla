"""Proceso de los instrumentos 3 y 4 (clarinete bajo y cuerda frotada). Carpeta exclusiva proceso/clarinete-y-cuerdas-<id12>/.

  01  el clarinete bajo: su espectro (sólo armónicos impares: el tubo cilíndrico) y sus técnicas percutivas (espectrograma)
  02  las cuerdas: el violín por técnicas y el chelo percutido (espectrogramas)
  03  el pizz de chelo que se vuelve house (espectrograma + la curva de «casa»)
  GIF el pizz que se vuelve house
  m4a muestrario: clarinete (escala, subtono, percusivo, glisando), chelo, violín, chelo percutido, contrabajo, chelo → house
    python proceso_nuevos.py n2
"""
import hashlib, json, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
AQUI = Path(__file__).resolve().parent; R = AQUI / 'render'; ET = sys.argv[1]
ORDEN = ['clarinete-escala', 'clarinete-subtono', 'clarinete-percusivo', 'clarinete-glisando', 'chelo-arco', 'violin-colores', 'chelo-percusivo', 'contrabajo-pizz', 'chelo-a-house']
nonce = os.urandom(16).hex(); h = hashlib.sha256()
for f in [AQUI / 'motor' / 'clarinete.js', AQUI / 'motor' / 'cuerda.js', Path(__file__)] + [R / f'{ET}-{n}.wav' for n in ORDEN]: h.update(f.read_bytes())
h.update(nonce.encode()); ID = h.hexdigest(); C = ID[:12]; SAL = AQUI / 'proceso' / f'clarinete-y-cuerdas-{C}'; os.mkdir(SAL)


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
F, Fs, Fg = fuente(14), fuente(12), fuente(22); W = 1500
lee = lambda n: (lambda q: (q[0], q[1].astype(float) / 32768))(wavfile.read(R / f'{ET}-{n}.wav'))


def png(im, n):
    with open(SAL / n, 'xb') as f: im.save(f, 'PNG')


def espectrograma(x, sr, ancho, alto, tinte, fmax=6000, N=2048):
    hop = max(64, len(x) // 1400); cols = [np.abs(np.fft.rfft(x[a:a + N] * np.hanning(N))) for a in range(0, len(x) - N, hop)]
    S = 20 * np.log10(np.array(cols).T + 1e-7); fr = np.fft.rfftfreq(N, 1 / sr); S = S[np.searchsorted(fr, np.geomspace(40, fmax, alto))]
    S = np.clip((S - S.max() + 70) / 70, 0, 1); m = Image.fromarray((S[::-1] * 255).astype(np.uint8)).resize((ancho, alto), Image.BILINEAR)
    return Image.composite(Image.new('RGB', (ancho, alto), tinte), Image.new('RGB', (ancho, alto), FONDO), m)


# 01 clarinete
im = Image.new('RGB', (W, 640), FONDO); d = ImageDraw.Draw(im)
d.text((24, 16), 'el clarinete bajo: tubo cilíndrico → sólo armónicos impares (Re3, 0-2.5 kHz) · y sus técnicas percutivas', fill=TXT, font=Fg)
sr, x = lee('clarinete-escala'); a = int((.1 + 5 * .55 + .15) * sr); seg = x[a:a + 16384] * np.hanning(16384)       # Re3 (50): la sexta nota (índice 5)
S = 20 * np.log10(np.abs(np.fft.rfft(seg)) + 1e-9); fr = np.fft.rfftfreq(16384, 1 / sr); m = fr < 2500; S = S[m]; fr = fr[m]; f0 = 440 * 2 ** ((50 - 69) / 12)
Xs = lambda f: 40 + (W - 80) * f / 2500; Ys = lambda v: 220 - 150 * max(0, (v - S.max() + 60) / 60)
for k in range(1, 22): d.line([(Xs(f0 * k), 70), (Xs(f0 * k), 222)], fill=oklch(.4, .08, h0 + 30) if k % 2 else REJ); d.text((Xs(f0 * k) - 4, 226), str(k), fill=TEN if k % 2 else REJ, font=Fs)
d.line([(Xs(f), Ys(v)) for f, v in zip(fr, S)], fill=oklch(.8, .13, h0 + 30), width=1)
sr, x = lee('clarinete-percusivo'); im.paste(espectrograma(x, sr, W - 80, 300, oklch(.82, .12, h0 + 60)), (40, 290))
d.text((40, 264), 'slaps y llaves (3+3+2) · multifónico · aire', fill=TXT, font=F)
png(im, f'01-clarinete-bajo-{C}.png')

# 02 cuerdas
im = Image.new('RGB', (W, 660), FONDO); d = ImageDraw.Draw(im)
d.text((24, 16), 'las cuerdas: violín por técnicas (arco · ponticello · tasto · trémolo · armónicos) y chelo percutido (pizz · Bartók · col legno)', fill=TXT, font=Fg)
sr, x = lee('violin-colores'); im.paste(espectrograma(x, sr, W - 80, 260, oklch(.84, .11, h0 + 140), 8000), (40, 70))
dur = len(x) / sr
for k, nom in enumerate(['arco', 'ponticello', 'tasto', 'trémolo', 'armónicos']):
    xx = 40 + (W - 80) * (.1 + k * 1.8) / dur; d.line([(xx, 64), (xx, 332)], fill=TEN); d.text((xx + 4, 336), nom, fill=TXT, font=Fs)
sr, x = lee('chelo-percusivo'); im.paste(espectrograma(x, sr, W - 80, 260, oklch(.82, .12, h0 + 250)), (40, 380))
png(im, f'02-cuerdas-{C}.png')

# 03 chelo → house
sr, x = lee('chelo-a-house'); dur = len(x) / sr
def casa_en(t): return min(1, max(0, (t - 1) / 7))
def lamina(hasta, ancho, alto, titulo=True):
    im = Image.new('RGB', (ancho, alto), FONDO); d = ImageDraw.Draw(im)
    if titulo: d.text((20, 14), 'el pizz de chelo que se vuelve pluck de house ochentero: la madera se vuelve filtro resonante y sierras', fill=TXT, font=Fg if ancho > 1000 else F)
    n = int(len(x) * min(1, hasta / dur)); w = max(2, int((ancho - 40) * min(1, hasta / dur)))
    if n > 4096: im.paste(espectrograma(x[:n], sr, w, alto - 160, oklch(.84, .13, h0 + 320)), (20, 60))
    for i in range(w): c = casa_en(i / (ancho - 40) * dur); d.line([(20 + i, alto - 30), (20 + i, alto - 30 - 60 * c)], fill=oklch(.6 + .3 * c, .15, h0 + 320 - 120 * c))
    d.text((24, alto - 90), 'casa', fill=TEN, font=Fs)
    return im
png(lamina(dur, W, 560), f'03-chelo-a-house-{C}.png')
frames = [lamina(t, 760, 420, titulo=False) for t in np.linspace(.4, dur, 46)]
pal = frames[-1].quantize(colors=64, method=Image.Quantize.MEDIANCUT); frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
gif = AQUI / f'chelo-a-house-{C}.gif'
with open(gif, 'xb') as fh: frames[0].save(fh, 'GIF', save_all=True, append_images=frames[1:] + [frames[-1]] * 3, duration=200, loop=0, optimize=True)

partes = []
for n in ORDEN:
    sr, x = lee(n); partes += [x / (np.abs(x).max() + 1e-9) * .8, np.zeros(int(.4 * sr))]
wav = R / f'muestrario-nuevos-{C}.wav'; wavfile.write(wav, sr, (np.concatenate(partes) * 32767).astype(np.int16))
m4a = AQUI / f'muestrario-clarinete-y-cuerdas-{C}.m4a'
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-i', str(wav), '-af', 'loudnorm=I=-16:TP=-1.5', '-c:a', 'aac', '-b:a', '192k', str(m4a)], check=True)
sha = lambda q: hashlib.sha256(Path(q).read_bytes()).hexdigest()
with open(SAL / f'receta-{C}.json', 'x', encoding='utf-8') as fh:
    json.dump({'id': ID, 'nonce': nonce, 'etiqueta': ET, 'orden_muestrario': ORDEN, 'medidas': json.load(open(R / f'transformaciones-{ET}.json', encoding='utf-8')),
               'archivos': {str(q.relative_to(AQUI)).replace('\\', '/'): sha(q) for q in sorted(SAL.glob('*.png')) + [gif, m4a]}}, fh, ensure_ascii=False, indent=1)
print(C, f'gif {gif.stat().st_size / 1e6:.2f} MB {200 * (len(frames) + 3) / 1000:.1f} s')
