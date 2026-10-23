"""Proceso del contrabajo que se vuelve bajo de house. Carpeta exclusiva proceso/contrabajo-a-house-<id12>/.
  01  espectrograma (30 Hz - 4 kHz, logarítmico) con la curva de «casa»; GIF del mismo dibujándose; m4a
    python proceso_contrabajo.py h1
"""
import hashlib, json, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
AQUI = Path(__file__).resolve().parent; R = AQUI / 'render'; ET = sys.argv[1]; WAV = R / f'{ET}-contrabajo-a-house.wav'
nonce = os.urandom(16).hex(); h = hashlib.sha256()
for f in [AQUI / 'motor' / 'cuerda.js', AQUI / 'herramientas' / 'contrabajo_house.js', Path(__file__), WAV]: h.update(f.read_bytes())
h.update(nonce.encode()); ID = h.hexdigest(); C = ID[:12]; SAL = AQUI / 'proceso' / f'contrabajo-a-house-{C}'; os.mkdir(SAL)


def oklch(L, Cc, hh):
    a, b = Cc * np.cos(np.radians(hh)), Cc * np.sin(np.radians(hh))
    l_, m_, s_ = L + .3963377774 * a + .2158037573 * b, L - .1055613458 * a - .0638541728 * b, L - .0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    rgb = np.clip([4.0767416621 * l - 3.3077115913 * m + .2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - .3413193965 * s,
                   -.0041960863 * l - .7034186147 * m + 1.7076147010 * s], 0, 1)
    rgb = np.where(rgb <= .0031308, 12.92 * rgb, 1.055 * rgb ** (1 / 2.4) - .055)
    return tuple(int(round(c * 255)) for c in rgb)


try: F, Fg = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 13), ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 21)
except OSError: F = Fg = ImageFont.load_default()
h0 = int(C[:4], 16) % 360; FONDO, TXT, TEN = oklch(.13, .02, h0), oklch(.92, .03, h0), oklch(.55, .04, h0)
sr, x = wavfile.read(WAV); x = x.astype(float) / 32768; dur = len(x) / sr
N, hop = 4096, 256; cols = [np.abs(np.fft.rfft(x[a:a + N] * np.hanning(N))) for a in range(0, len(x) - N, hop)]
S = 20 * np.log10(np.array(cols).T + 1e-7); fr = np.fft.rfftfreq(N, 1 / sr); S = S[np.searchsorted(fr, np.geomspace(30, 4000, 340))]; S = np.clip((S - S.max() + 66) / 66, 0, 1)
casa = lambda t: min(1, max(0, (t - 1) / 7))


def lamina(hasta, ancho, alto, titulo=True):
    im = Image.new('RGB', (ancho, alto), FONDO); d = ImageDraw.Draw(im)
    if titulo: d.text((20, 14), 'el contrabajo pizz que se vuelve bajo de house ochentero (122 bpm): madera → filtro resonante + sierras', fill=TXT, font=Fg)
    k = max(2, int(S.shape[1] * min(1, hasta / dur))); w = max(2, int((ancho - 40) * k / S.shape[1]))
    m = Image.fromarray((S[::-1, :k] * 255).astype(np.uint8)).resize((w, alto - 150), Image.BILINEAR)
    im.paste(Image.composite(Image.new('RGB', m.size, oklch(.84, .13, h0 + 300)), Image.new('RGB', m.size, FONDO), m), (20, 55))
    for i in range(w): c = casa(i / (ancho - 40) * dur); d.line([(20 + i, alto - 25), (20 + i, alto - 25 - 55 * c)], fill=oklch(.6 + .3 * c, .15, h0 + 300 - 120 * c))
    d.text((24, alto - 85), 'casa', fill=TEN, font=F)
    return im


with open(SAL / f'01-contrabajo-a-house-{C}.png', 'xb') as fh: lamina(dur, 1500, 540).save(fh, 'PNG')
frames = [lamina(t, 760, 400, False) for t in np.linspace(.4, dur, 46)]
pal = frames[-1].quantize(colors=64, method=Image.Quantize.MEDIANCUT); frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
gif = AQUI / f'contrabajo-a-house-{C}.gif'
with open(gif, 'xb') as fh: frames[0].save(fh, 'GIF', save_all=True, append_images=frames[1:] + [frames[-1]] * 3, duration=200, loop=0, optimize=True)
m4a = AQUI / f'contrabajo-a-house-{C}.m4a'
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-i', str(WAV), '-af', 'loudnorm=I=-14:TP=-1.2', '-c:a', 'aac', '-b:a', '192k', str(m4a)], check=True)
sha = lambda q: hashlib.sha256(Path(q).read_bytes()).hexdigest()
with open(SAL / f'receta-{C}.json', 'x', encoding='utf-8') as fh:
    json.dump({'id': ID, 'nonce': nonce, 'etiqueta': ET, 'archivos': {str(q.relative_to(AQUI)).replace('\\', '/'): sha(q) for q in sorted(SAL.glob('*.png')) + [gif, m4a]}}, fh, ensure_ascii=False, indent=1)
print(C, f'gif {gif.stat().st_size / 1e6:.2f} MB {200 * (len(frames) + 3) / 1000:.1f} s')
