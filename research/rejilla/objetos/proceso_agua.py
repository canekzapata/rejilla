"""Proceso de la percusión de agua (instrumento 5). Carpeta exclusiva proceso/agua-<id12>/.

  01  una burbuja: su forma de onda (sube de tono mientras se apaga, el «plop»), de la física de van den Doel
  02  las técnicas: gotas, palo de agua, güiro de agua, vaso que se llena, burbujeo y ola (espectrogramas)
  03  el agua que se vuelve ola (espectrograma con sus etapas)
  GIF el agua que se vuelve ola
  m4a muestrario: gotas, palo, güiro, chorro, burbujeo, ola y el agua que se vuelve ola
    python proceso_agua.py w3
"""
import hashlib, json, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
AQUI = Path(__file__).resolve().parent; R = AQUI / 'render'; ET = sys.argv[1]
ORDEN = ['gotas', 'palo', 'guiro', 'chorro', 'burbujeo', 'ola', 'agua-a-ola']
nonce = os.urandom(16).hex(); h = hashlib.sha256()
for f in [AQUI / 'motor' / 'agua.js', Path(__file__)] + [R / f'{ET}-agua-{n}.wav' for n in ORDEN]: h.update(f.read_bytes())
h.update(nonce.encode()); ID = h.hexdigest(); C = ID[:12]; SAL = AQUI / 'proceso' / f'agua-{C}'; os.mkdir(SAL)


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
h0 = 180 + int(C[:4], 16) % 80                                      # el agua: tonos fríos, derivados del id
FONDO, TXT, TEN, REJ = oklch(.13, .02, h0), oklch(.92, .03, h0), oklch(.55, .04, h0), oklch(.25, .03, h0)
W = 1500
lee = lambda n: (lambda q: (q[0], q[1].astype(float) / 32768))(wavfile.read(R / f'{ET}-agua-{n}.wav'))


def png(im, n):
    with open(SAL / n, 'xb') as f: im.save(f, 'PNG')


def espectrograma(x, sr, ancho, alto, tinte, fmax=9000, N=2048):
    hop = max(64, len(x) // 1500); cols = [np.abs(np.fft.rfft(x[a:a + N] * np.hanning(N))) for a in range(0, len(x) - N, hop)]
    S = 20 * np.log10(np.array(cols).T + 1e-7); fr = np.fft.rfftfreq(N, 1 / sr); S = S[np.searchsorted(fr, np.geomspace(60, fmax, alto))]
    S = np.clip((S - S.max() + 66) / 66, 0, 1); m = Image.fromarray((S[::-1] * 255).astype(np.uint8)).resize((ancho, alto), Image.BILINEAR)
    return Image.composite(Image.new('RGB', (ancho, alto), tinte), Image.new('RGB', (ancho, alto), FONDO), m)


# 01 una burbuja (la misma fórmula del motor): Do5, ε = 0.12
f0, eps = 523.25 / 2 ** (120 / 1200), .12; r = 3 / f0; d = .13 / r + .0072 * r ** -1.5; sig = eps * d
t = np.arange(0, .09, 1 / 48000); s = np.sin(2 * np.pi * f0 * (t + sig * t * t / 2)) * np.exp(-d * t)
im = Image.new('RGB', (W, 420), FONDO); dr = ImageDraw.Draw(im)
dr.text((24, 16), f'una burbuja (van den Doel): radio {r * 1000:.1f} mm → {f0:.0f} Hz que suben a {f0 * (1 + sig * .03):.0f} Hz mientras se apaga (d = {d:.0f}/s)', fill=TXT, font=Fg)
X = lambda u: 40 + (W - 80) * u / t[-1]
dr.line([(X(u), 230 - 150 * v) for u, v in zip(t[::3], s[::3])], fill=oklch(.82, .12, h0), width=2)
dr.line([(X(u), 230 - 150 * np.exp(-d * u)) for u in t[::30]], fill=TEN); dr.line([(X(u), 230 + 150 * np.exp(-d * u)) for u in t[::30]], fill=TEN)
dr.text((40, 392), 'todo el instrumento son nubes de esto: gotas, lluvia en un tubo, un güiro, un vaso, una ola', fill=TEN, font=F)
png(im, f'01-una-burbuja-{C}.png')

# 02 las técnicas
im = Image.new('RGB', (W, 60 + 3 * 230), FONDO); dr = ImageDraw.Draw(im)
dr.text((24, 16), 'las técnicas (60 Hz - 9 kHz): gotas · palo de agua · güiro de agua · vaso que se llena · burbujeo · ola', fill=TXT, font=Fg)
for k, n in enumerate(ORDEN[:6]):
    sr, x = lee(n); col, fila = k % 2, k // 2; ancho = (W - 90) // 2
    im.paste(espectrograma(x, sr, ancho, 180, oklch(.84, .11, h0 + 25 * k)), (30 + col * (ancho + 30), 80 + fila * 230))
    dr.text((30 + col * (ancho + 30), 60 + fila * 230), n, fill=TXT, font=F)
png(im, f'02-las-tecnicas-{C}.png')

# 03 el agua que se vuelve ola
sr, x = lee('agua-a-ola'); dur = len(x) / sr; ETAPAS = json.load(open(R / f'{ET}-agua-agua-a-ola.json', encoding='utf-8'))['etapas']
def lamina(hasta, ancho, alto, titulo=True):
    im = Image.new('RGB', (ancho, alto), FONDO); dr = ImageDraw.Draw(im)
    if titulo: dr.text((20, 14), 'el agua que se vuelve ola: gotas cada vez más densas → palo de agua → chorro → la ola rompe y se retira → una gota', fill=TXT, font=Fg)
    n = int(len(x) * min(1, hasta / dur)); w = max(2, int((ancho - 40) * min(1, hasta / dur)))
    if n > 4096: im.paste(espectrograma(x[:n], sr, w, alto - 110, oklch(.85, .12, h0 + 20)), (20, 60))
    for nom, a, b in ETAPAS:
        if a > hasta: continue
        xa = 20 + (ancho - 40) * a / dur; dr.line([(xa, alto - 45), (xa, alto - 30)], fill=TEN); dr.text((xa + 3, alto - 42), nom, fill=TXT, font=Fs)
    return im
png(lamina(dur, W, 560), f'03-agua-a-ola-{C}.png')
frames = [lamina(u, 760, 400, False) for u in np.linspace(.4, dur, 47)]
pal = frames[-1].quantize(colors=64, method=Image.Quantize.MEDIANCUT); frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
gif = AQUI / f'agua-a-ola-{C}.gif'
with open(gif, 'xb') as fh: frames[0].save(fh, 'GIF', save_all=True, append_images=frames[1:] + [frames[-1]] * 2, duration=200, loop=0, optimize=True)

partes = []
for n in ORDEN:
    sr, x = lee(n); partes += [x / (np.abs(x).max() + 1e-9) * .8, np.zeros(int(.4 * sr))]
wav = R / f'muestrario-agua-{C}.wav'; wavfile.write(wav, sr, (np.concatenate(partes) * 32767).astype(np.int16))
m4a = AQUI / f'muestrario-agua-{C}.m4a'
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-i', str(wav), '-af', 'loudnorm=I=-16:TP=-1.5', '-c:a', 'aac', '-b:a', '192k', str(m4a)], check=True)
sha = lambda q: hashlib.sha256(Path(q).read_bytes()).hexdigest()
with open(SAL / f'receta-{C}.json', 'x', encoding='utf-8') as fh:
    json.dump({'id': ID, 'nonce': nonce, 'etiqueta': ET, 'orden_muestrario': ORDEN,
               'archivos': {str(q.relative_to(AQUI)).replace('\\', '/'): sha(q) for q in sorted(SAL.glob('*.png')) + [gif, m4a]}}, fh, ensure_ascii=False, indent=1)
print(C, f'gif {gif.stat().st_size / 1e6:.2f} MB {200 * (len(frames) + 2) / 1000:.1f} s')
