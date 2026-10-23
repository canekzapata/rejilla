"""¿Por quién se toma la tierra? — PNGs de etapas y GIF del proceso.
    python proceso.py <carpeta-de-render> <carpeta-de-entrega>
01 el volcán a seis edades (Traspuesta 177) y el magma que sale de su relieve · 02 la doble articulación (el sedimento en orden
estadístico y su pliegue) · 03 la garganta de volcán (el tubo a cada edad y la caldera como resonador de Helmholtz) · 04 quién toca
· 05 las capas solas · 06 la mezcla · GIF: el volcán envejece mientras suena la mezcla.
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
AQUI = os.path.dirname(os.path.abspath(__file__))
RUN, OUT = sys.argv[1], sys.argv[2]; P = json.load(open(os.path.join(OUT, 'partitura.json'), encoding='utf-8'))
h = os.path.basename(OUT).rsplit('-', 1)[1]; s = P['semilla']; pr = os.path.join(OUT, 'proceso'); os.makedirs(pr, exist_ok=False)
DUR = P['duracion']; SR = 48000; FONDO = (12, 9, 9); TXT = (236, 228, 214); W = 1700; G = 360; ED = P['edades']
CORTES = json.load(open(os.path.join(AQUI, 'terreno', 'cortes-177.json'), encoding='utf-8'))
fn = lambda n: ImageFont.truetype('C:/Windows/Fonts/consola.ttf', n)
def nuevo(nombre): p = os.path.join(pr, nombre); assert not os.path.exists(p); return p
def tinta(k, n, l=.62):
    a = 2 * math.pi * k / max(1, n) + s * .031; return tuple(int(255 * min(1, max(0, l + .36 * math.sin(a + d)))) for d in (0, 2.1, 4.2))
def secciones(d, x0, Wd, y0, y1):
    for k, e in enumerate(ED): xa = x0 + int(e['t'] / DUR * Wd); d.line([xa, y0, xa, y1], fill=(70, 60, 60)); d.text((xa + 4, y0 + 2), e['nombre'][:22], font=fn(12), fill=(190, 180, 170))
def relieve_img(edad, lado):
    hh = np.fromfile(os.path.join(AQUI, 'terreno', f'h-177-e{edad}.f32'), np.float32).reshape(G, G) * next(c['relieve'] for c in CORTES if c['edad'] == edad) / 4100
    lv = (hh * 20).astype(int); borde = (np.abs(np.diff(lv, axis=0, prepend=lv[:1])) + np.abs(np.diff(lv, axis=1, prepend=lv[:, :1]))) > 0
    img = np.zeros((G, G, 3)); img[...] = (hh[..., None] * np.array([150, 70, 50]) + 18); img[borde] = (240, 150, 90); img[115, :] = (120, 200, 230)
    return Image.fromarray(img.astype(np.uint8)).resize((lado, lado), Image.NEAREST)

# 01 · el volcán a seis edades
im = Image.new('RGB', (W, 640), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '01  el mismo volcán (Traspuesta 177) a seis edades — la raya azul es el corte que se vuelve garganta — y el magma: f = 55 Hz · 4100 m / relieve', font=fn(16), fill=TXT)
eds = [0.03, 0.25, 0.5, 0.62, 0.8, 0.97]
for k, e in enumerate(eds):
    x = 20 + k * 278; im.paste(relieve_img(e, 260), (x, 50)); c = next(c for c in CORTES if c['edad'] == e)
    d.text((x, 318), f"edad {e}: {c['nombre']}", font=fn(12), fill=TXT); d.text((x, 336), f"relieve {c['relieve']} m → magma {55 * 4100 / c['relieve']:.2f} Hz", font=fn(12), fill=tinta(k, 6, .75))
d.text((20, 370), 'los seis cortes encimados (misma escala: el volcán se gasta, colapsa, se vacía, queda el cuello)', font=fn(13), fill=TXT)
for k, e in enumerate(eds):
    c = next(c for c in CORTES if c['edad'] == e); pts = [(20 + i * 1640 / (len(c['perfil']) - 1), 610 - v * 200) for i, v in enumerate(c['perfil'])]; d.line(pts, fill=tinta(k, 6, .75), width=2)
im.save(nuevo(f'01-volcan-seis-edades-s{s}-{h}.png'))

# 02 · la doble articulación
im = Image.new('RGB', (W, 300), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '02  la doble articulación (Mil mesetas): primero la sedimentación — arenisca A y esquisto B en orden estadístico (Markov, quedarse 0.7) —; luego el plegamiento', font=fn(15), fill=TXT)
for k, ch in enumerate(P['sedimento']):
    x = 20 + k * 17; d.rectangle([x, 70, x + 15, 120], fill=(230, 190, 120) if ch == 'A' else (70, 60, 80)); d.text((x + 3, 124), ch, font=fn(11), fill=TXT)
d.text((20, 160), 'el pliegue: los primeros 8 doblados sobre sí mismos (palíndromo): el riff estable de la erosión en adelante', font=fn(13), fill=TXT)
for k, ch in enumerate(P['pliegue']):
    x = 20 + k * 40; d.rectangle([x, 190, x + 36, 250], fill=(230, 190, 120) if ch == 'A' else (70, 60, 80)); d.text((x + 13, 254), ch, font=fn(13), fill=TXT)
d.line([20 + 8 * 40 - 2, 180, 20 + 8 * 40 - 2, 262], fill=(240, 120, 90), width=3)
im.save(nuevo(f'02-doble-articulacion-s{s}-{h}.png'))

# 03 · la garganta de volcán
js = """const G=require('./%s/codigo/rejilla/research/rejilla/lo-que-tapa-la-traspuesta/motor/garganta.js'),C=JSON.parse(require('fs').readFileSync('terreno/cortes-177.json','utf8'));
process.stdout.write(JSON.stringify(C.map(c=>Array.from(G.areaTerreno(Float32Array.from(c.perfil),48,new Float64Array(48))))));""" % P['instrumentos']
A = json.loads(subprocess.run(['node', '-e', js], cwd=AQUI, capture_output=True, text=True, check=True).stdout)
im = Image.new('RGB', (W, 560), FONDO); d = ImageDraw.Draw(im); Hh = P['helmholtz']
d.text((14, 10), '03  la garganta de volcán: el tubo (largo 2: 48 secciones) envejece con el volcán; al colapsar, la caldera es un resonador de Helmholtz', font=fn(15), fill=TXT)
for k, ar in enumerate(A):
    y0 = 70 + k * 72; d.text((20, y0 - 8), f'edad {eds[k]}', font=fn(12), fill=tinta(k, 6, .75))
    for j, a_ in enumerate(ar):
        r = math.sqrt(a_ / math.pi) * 18; x = 130 + j * 18; d.rectangle([x, y0 - r, x + 16, y0 + r], fill=tuple(int(c * .45) for c in tinta(k, 6, .75)), outline=tinta(k, 6, .75))
d.text((1030, 80), f"Helmholtz: f = c/2π · √(A / (V·L))\nV = {Hh['V_m3'] / 1e9:.2f} km³ (la caldera)\nA = {Hh['A_m2'] / 1e6:.2f} km² (la brecha)\nL = {Hh['L_m'] / 1000:.1f} km\n\nf real = {Hh['f_real_hz']:.4f} Hz (un ciclo cada {1 / Hh['f_real_hz']:.0f} s)\n×2^11 → {Hh['f_hz']:.1f} Hz: el bramido", font=fn(15), fill=TXT, spacing=8)
im.save(nuevo(f'03-garganta-de-volcan-s{s}-{h}.png'))

# 04 · quién toca
im = Image.new('RGB', (W, 520), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '04  quién toca: el magma (Scelsi), los estratos (dub), el groove, Mulatu (krar, metales, vibráfono, masenqo, washint), el coro y la garganta', font=fn(15), fill=TXT)
filas = [('magma', [(m['t'], m['dur'], m['m']) for m in P['magma']]), ('estratos', [(e['t'], .4, e['notas'][0]) for e in P['estratos']]),
         ('bajo', [(e['t'], e['dur'], e['m']) for e in P['bajo']]), ('krar', [(e['t'], e['dur'], e['midi']) for e in P['web']['krar']]),
         ('metales', [(e['t'], e['dur'], e['m']) for e in P['metales']]), ('vibráfono', [(e['t'], e['dur'], e['midi']) for e in P['web']['vibrafono']]),
         ('masenqo · washint', [(e['t'], e['dur'], e['midi']) for e in P['web']['masenqo']] + [(e['t'], e['dur'], e['m']) for e in P['washint']]),
         ('coro', [(e['t'], e['dur'], e['nota']) for k in ('verso', 'estribillo', 'estribillo2') for e in P['coros'][k]['S']]),
         ('garganta', [(e['t'], e['dur'], e['nota']) for e in P['garganta']])]
for k, (nom, ns) in enumerate(filas):
    col = tinta(k, len(filas), .72); y0 = 50 + k * 50; d.text((10, y0 + 14), nom, font=fn(12), fill=col)
    if not ns: continue
    lo, hi = min(n[2] for n in ns), max(n[2] for n in ns) + 1
    for t, du, m in ns: x = 170 + t / DUR * (W - 190); x2 = 170 + (t + du) / DUR * (W - 190); y = y0 + 40 - (m - lo) / (hi - lo) * 36; d.rectangle([x, y - 1, max(x + 1, x2), y + 1], fill=col)
secciones(d, 170, W - 190, 40, 510); im.save(nuevo(f'04-voces-s{s}-{h}.png'))

def espectro(x, alto, fmax=12000, hop=1024):
    N = 2048; win = np.hanning(N); fr = [np.abs(np.fft.rfft(x[i:i + N] * win)) for i in range(0, len(x) - N, hop)]
    Sx = 20 * np.log10(np.array(fr).T + 1e-9); f = np.fft.rfftfreq(N, 1 / SR); filas = np.geomspace(25, fmax, alto)[::-1]
    img = Sx[np.searchsorted(f, filas)]; return np.clip((img - (img.max() - 65)) / 65, 0, 1)
def pinta(img, col): return (np.power(img[..., None], 1.3) * np.array(col) + np.array(FONDO) * (1 - img[..., None])).astype(np.uint8)
# 05 · capas solas
capas = [(c, True) for c in P['web'] if P['web'][c]] + [(c, False) for c in ['garganta', 'caldera', 'garganta-cuello', 'sax', 'trompeta', 'trombon', 'washint', 'tamtam', 'lagos']] + [('sabina-soprano', True)]
alto = 40; x0 = 160; im = Image.new('RGB', (W, 50 + (alto + 5) * len(capas)), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '05  las capas solas, antes de mezclar (25 Hz–12 kHz) — las de Python (magma, estratos, bajo, avalancha) se ven en la 06', font=fn(16), fill=TXT)
for k, (c, st) in enumerate(capas):
    x = np.fromfile(os.path.join(RUN, c + '.f32'), dtype=np.float32).astype(float); x = x.reshape(-1, 2).mean(1) if st else x
    col = tinta(k, len(capas)); y0 = 46 + k * (alto + 5); im.paste(Image.fromarray(pinta(espectro(x, alto, hop=2048), col)).resize((W - x0 - 10, alto)), (x0, y0)); d.text((8, y0 + 12), c, font=fn(12), fill=col)
secciones(d, x0, W - x0 - 10, 36, im.height - 4); im.save(nuevo(f'05-capas-s{s}-{h}.png'))
# 06 · mezcla
sr, x = wavfile.read(os.path.join(OUT, os.path.basename(OUT) + '.wav')); x = x.astype(float).mean(1) / 32768
mez = Image.new('RGB', (W, 400), FONDO); mez.paste(Image.fromarray(pinta(espectro(x, 330), (240, 220, 200))).resize((W - 20, 330)), (10, 50)); d = ImageDraw.Draw(mez)
d.text((14, 10), f'06  ¿Por quién se toma la tierra? (s{s}): la mezcla, {len(x) / sr:.0f} s', font=fn(18), fill=TXT); secciones(d, 10, W - 20, 44, 385)
mez.save(nuevo(f'06-mezcla-s{s}-{h}.png'))
# GIF: el volcán envejece arriba, la mezcla abajo
imgs = {e: relieve_img(e, 380) for e in eds}; cuadros = []; NC = 34
def edad_de(t):
    k = 0
    for i, e in enumerate(ED):
        if t >= e['t']: k = i
    return k
for j in range(1, NC + 1):
    t = DUR * j / NC; c = Image.new('RGB', (W, 800), FONDO); dd = ImageDraw.Draw(c); k = edad_de(t); e = ED[k]
    c.paste(imgs[e['edad']], (20, 10)); dd.text((430, 40), e['nombre'], font=fn(28), fill=TXT); dd.text((430, 90), f"magma {e['bordon_hz']:.1f} Hz · {e['qenet']}", font=fn(18), fill=tinta(k, 6, .8))
    dd.text((430, 125), f'{t:5.1f} s', font=fn(16), fill=(190, 180, 170))
    c.paste(mez, (0, 400)); xx = 10 + int((W - 20) * j / NC); dd.rectangle([xx, 450, W - 10, 780], fill=FONDO); dd.line([xx, 450, xx, 780], fill=TXT, width=2)
    cuadros.append(c.resize((1100, 518)))
gif = os.path.join(OUT, f'por-quien-se-toma-la-tierra-s{s}-{h}.gif'); cuadros[0].save(gif, save_all=True, append_images=cuadros[1:] + [cuadros[-1]] * 2, duration=270, loop=0, optimize=True)
cuadros[-1].save(nuevo(f'07-volcan-y-mezcla-s{s}-{h}.png'))
print(gif, os.path.getsize(gif) // 1024, 'KB')
