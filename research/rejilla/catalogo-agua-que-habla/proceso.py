"""Catálogo de agua que habla — PNGs de etapas y GIF del proceso.
    python proceso.py <carpeta-de-render> <carpeta-de-entrega>
01 la partitura (cada capa en su renglón, con las secciones) · 02 las capas solas (espectrogramas, antes de mezclar) ·
03 el bombeo del sidechain en un drop · 04 la mezcla final (espectrograma con las secciones) · GIF: la mezcla se revela con el cursor.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
RUN, OUT = sys.argv[1], sys.argv[2]; P = json.load(open(os.path.join(OUT, 'partitura.json'), encoding='utf-8'))
h = os.path.basename(OUT).rsplit('-', 1)[1]; s = P['semilla']; pr = os.path.join(OUT, 'proceso'); os.makedirs(pr, exist_ok=False)
BAR = 4 * 60 / P['bpm']; DUR = P['duracion']; SR = 48000; FONDO = (10, 11, 16)
fn = lambda n: ImageFont.truetype('C:/Windows/Fonts/consola.ttf', n)
def nuevo(nombre): p = os.path.join(pr, nombre); assert not os.path.exists(p); return p
def tinta(k, n): a = 2 * math.pi * k / n; return tuple(int(150 + 95 * (.5 + .5 * math.sin(a + d))) for d in (0, 2.1, 4.2))      # el tono gira, sin paleta fija
def secciones(d, x0, W, y0, y1):
    for k, (a, z) in P['secciones'].items():
        xa = x0 + int(a * BAR / DUR * W); d.line([xa, y0, xa, y1], fill=(60, 62, 80)); d.text((xa + 4, y0 + 2), k, font=fn(13), fill=(170, 170, 185))

# 01 · partitura
filas = [(c, [(e['t'], e['midi']) for e in v]) for c, v in P['web'].items() if v] + [('sub 808', [(e['t'], e['midi']) for e in P['sub']]), ('dùndún', [(e['t'], e['midi']) for e in P['dundun']]),
         ('tambor que habla', [(e['t'], 60) for e in P['tambor_habla']]), ('aves (siringe)', [(e['t'], e['m']) for e in P['aves_objeto']]), ('aves (jardín)', [(e['t'], e['midi']) for e in P['aves_jardin']]),
         ('agua', [(e['t'], e.get('m', 70)) for e in P['agua']]), ('Siringua', [(e['t'], 60 + e['transponer']) for e in P['siringua']])]
W, H, x0 = 1700, 26 * len(filas) + 70, 170; im = Image.new('RGB', (W, H), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), f"01  partitura: {sum(len(f[1]) for f in filas)} eventos en {len(filas)} capas · 160 bpm · modo 2 sobre D", font=fn(18), fill=(240, 232, 218))
for k, (nombre, ev) in enumerate(filas):
    y0 = 50 + 26 * k; col = tinta(k, len(filas)); d.text((10, y0 + 5), nombre, font=fn(13), fill=col); lo = min(m for _, m in ev); hi = max(m for _, m in ev) + 1
    for t, m in ev: x = x0 + int(t / DUR * (W - x0 - 10)); y = y0 + 20 - int((m - lo) / max(1, hi - lo) * 16); d.rectangle([x, y, x + 1, y + 2], fill=col)
secciones(d, x0, W - x0 - 10, 44, H - 6); im.save(nuevo(f'01-partitura-s{s}-{h}.png'))

# 02 · capas solas
def espectro(x, alto, fmax=12000, hop=1024):
    N = 2048; win = np.hanning(N); fr = [np.abs(np.fft.rfft(x[i:i + N] * win)) for i in range(0, len(x) - N, hop)]
    S = 20 * np.log10(np.array(fr).T + 1e-9); f = np.fft.rfftfreq(N, 1 / SR); filas = np.geomspace(40, fmax, alto)[::-1]
    img = S[np.searchsorted(f, filas)]; return np.clip((img - (img.max() - 65)) / 65, 0, 1)
capas = [c for c in P['web'] if P['web'][c]] + ['aves-siringe', 'agua', 'waterphone', 'tambor-que-habla']
alto = 60; im = Image.new('RGB', (W, 50 + (alto + 6) * len(capas)), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '02  las capas solas, antes de mezclar (espectrogramas 40 Hz–12 kHz)', font=fn(18), fill=(240, 232, 218))
for k, c in enumerate(capas):
    x = np.fromfile(os.path.join(RUN, c + '.f32'), dtype=np.float32).astype(float); x = x.reshape(-1, 2).mean(1) if c in P['web'] else x
    img = espectro(x, alto, hop=2048); col = np.array(tinta(k, len(capas)))
    rgb = (np.power(img[..., None], 1.3) * col + np.array(FONDO) * (1 - img[..., None])).astype(np.uint8)
    y0 = 46 + k * (alto + 6); im.paste(Image.fromarray(rgb).resize((W - x0 - 10, alto)), (x0, y0)); d.text((10, y0 + 20), c, font=fn(13), fill=tuple(int(v) for v in col))
im.save(nuevo(f'02-capas-s{s}-{h}.png'))

# 03 · sidechain: dos compases del drop
duck = np.load(os.path.join(RUN, 'duck.npy')); a, z = int(24 * BAR * 100), int(26 * BAR * 100)
im = Image.new('RGB', (W, 260), FONDO); d = ImageDraw.Draw(im); d.text((14, 10), '03  el bombeo: cada bombo agacha lo demás 55 % y lo suelta en 120 ms (compases 24–25)', font=fn(18), fill=(240, 232, 218))
pts = [(x0 + int((i - a) / (z - a) * (W - x0 - 10)), 230 - int(duck[i] * 170)) for i in range(a, z)]; d.line(pts, fill=(140, 225, 170), width=2)
for e in P['web']['bateria']:
    if e.get('pieza') == 'kick' and 24 * BAR <= e['t'] < 26 * BAR: x = x0 + int((e['t'] * 100 - a) / (z - a) * (W - x0 - 10)); d.line([x, 50, x, 240], fill=(236, 120, 110))
d.text((10, 60), 'ganancia', font=fn(13), fill=(140, 225, 170)); d.text((10, 80), 'bombos', font=fn(13), fill=(236, 120, 110)); im.save(nuevo(f'03-sidechain-s{s}-{h}.png'))

# 04 · mezcla
sr, x = wavfile.read(os.path.join(OUT, os.path.basename(OUT) + '.wav')); x = x.astype(float).mean(1) / 32768
img = espectro(x, 330); rgb = (np.power(img[..., None], 1.25) * np.array([236, 228, 214]) + np.array(FONDO) * (1 - img[..., None])).astype(np.uint8)
mez = Image.new('RGB', (W, 400), FONDO); mez.paste(Image.fromarray(rgb).resize((W - 20, 330)), (10, 50)); d = ImageDraw.Draw(mez)
d.text((14, 10), f"04  Catálogo de agua que habla (s{s}): la mezcla, {len(x) / sr:.0f} s", font=fn(18), fill=(240, 232, 218)); secciones(d, 10, W - 20, 44, 385)
mez.save(nuevo(f'04-mezcla-s{s}-{h}.png'))
# GIF: la mezcla se revela con el cursor (36 cuadros × 0.27 s ≈ 9.7 s)
cuadros = []
for j in range(1, 37):
    c = mez.copy(); dd = ImageDraw.Draw(c); xx = 10 + int((W - 20) * j / 36); dd.rectangle([xx, 50, W - 10, 380], fill=FONDO); dd.line([xx, 50, xx, 380], fill=(240, 232, 218), width=2); cuadros.append(c.resize((1100, 259)))
gif = os.path.join(OUT, f'catalogo-agua-que-habla-s{s}-{h}.gif'); cuadros[0].save(gif, save_all=True, append_images=cuadros[1:] + [cuadros[-1]] * 2, duration=270, loop=0, optimize=True)
print(gif, os.path.getsize(gif) // 1024, 'KB')
