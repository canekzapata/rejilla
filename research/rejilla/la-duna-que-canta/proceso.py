"""La duna que canta — PNGs de etapas y GIF del proceso.
    python proceso.py <carpeta-de-render> <carpeta-de-entrega>
01 la duna 675 (barjanes) con sus quince crestas y los transectos del noreste al suroeste · 02 las crestas como melodía (Ryoan-ji y
el solo nómada) · 03 la nota y el pulso: f₀ = 0.4·√(g/d), la corchea a f₀/16, y la frecuencia de los choques con la coherencia de
Kuramoto en el tiempo · 04 la avalancha 2 de cerca: los clics se vuelven nota · 05 Clapping Music: la duna migra · 06 quién toca ·
07 las capas solas · 08 la mezcla · GIF: la duna con la cresta que suena, la coherencia y la mezcla.
Los colores salen de OKLCh con el matiz sembrado (s675): arena cálida contra la noche fría.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
AQUI = os.path.dirname(os.path.abspath(__file__))
RUN, OUT = sys.argv[1], sys.argv[2]; P = json.load(open(os.path.join(OUT, 'partitura.json'), encoding='utf-8'))
h = os.path.basename(OUT).rsplit('-', 1)[1]; s = P['semilla']; pr = os.path.join(OUT, 'proceso')
B = sys.argv[sys.argv.index('--b') + 1].split(',') if '--b' in sys.argv else None   # --b 03,04: rehace esas etapas como 03b, 04b (no pisa)
if B is None: os.makedirs(pr, exist_ok=False)
DUR = P['duracion']; SR = 48000; W = 1700; G = 360; SC = P['secciones']
H = np.fromfile(os.path.join(AQUI, 'terreno', 'h-675.f32'), dtype=np.float32).reshape(G, G)
COH = np.array(json.load(open(os.path.join(RUN, 'duna-coherencia.json'))))
fn = lambda n: ImageFont.truetype('C:/Windows/Fonts/consola.ttf', n)
def nuevo(nombre):
    if B is not None: nombre = nombre[:2] + 'b' + nombre[2:]
    p = os.path.join(pr, nombre); assert not os.path.exists(p); return p
def guardar(img, nombre):
    if B is None or nombre[:2] in B: img.save(nuevo(nombre))

def oklch(L, C, hdeg):
    a, b = C * math.cos(math.radians(hdeg)), C * math.sin(math.radians(hdeg))
    l_, m_, s_ = L + .3963377774 * a + .2158037573 * b, L - .1055613458 * a - .0638541728 * b, L - .0894841775 * a - 1.2914855480 * b
    l, m, s3 = l_ ** 3, m_ ** 3, s_ ** 3
    rgb = (4.0767416621 * l - 3.3077115913 * m + .2309699292 * s3, -1.2684380046 * l + 2.6097574011 * m - .3413193965 * s3, -.0041960863 * l - .7034186147 * m + 1.7076147010 * s3)
    return tuple(int(255 * min(1, max(0, (12.92 * c if c <= .0031308 else 1.055 * c ** (1 / 2.4) - .055)))) for c in rgb)
ARENA = 55 + (s * 7.3) % 30                                           # el matiz de la arena (cálido), sembrado
FONDO = oklch(.13, .015, ARENA + 200); TXT = oklch(.9, .03, ARENA); TENUE = oklch(.55, .03, ARENA)
def tinta(k, n, L=.75): return oklch(L, .11, ARENA + 220 * k / max(1, n - 1))    # de la arena al azul de la noche
def secciones(d, x0, Wd, y0, y1):
    for e in SC: xa = x0 + int(e['t'] / DUR * Wd); d.line([xa, y0, xa, y1], fill=oklch(.35, .03, ARENA)); d.text((xa + 4, y0 + 2), e['num'] + ' ' + e['nombre'][:20], font=fn(11), fill=TENUE)
def duna_img(lado, resalta=None):
    lv = (H * 24).astype(int); borde = (np.abs(np.diff(lv, axis=0, prepend=lv[:1])) + np.abs(np.diff(lv, axis=1, prepend=lv[:, :1]))) > 0
    baja, alta, linea = np.array(oklch(.2, .03, ARENA)), np.array(oklch(.62, .1, ARENA)), np.array(oklch(.85, .12, ARENA + 10))
    img = baja + H[..., None] * (alta - baja); img[borde] = linea
    im = Image.fromarray(img.astype(np.uint8)).resize((lado, lado), Image.BILINEAR); d = ImageDraw.Draw(im)
    for k, p in enumerate(P['picos']):
        a, z = (p['u'] + .11 / math.sqrt(2), p['v'] - .11 / math.sqrt(2)), (p['u'] - .11 / math.sqrt(2), p['v'] + .11 / math.sqrt(2))
        col = tinta(k, 15, .82) if resalta in (None, k) else oklch(.4, .02, ARENA)
        d.line([a[0] * lado, a[1] * lado, z[0] * lado, z[1] * lado], fill=col, width=3 if resalta == k else 1)
        d.ellipse([p['u'] * lado - 4, p['v'] * lado - 4, p['u'] * lado + 4, p['v'] * lado + 4], outline=col, width=2)
        if resalta is None: d.text((p['u'] * lado + 6, p['v'] * lado - 6), str(k + 1), font=fn(12), fill=col)
    return im

# 01 · la duna y sus crestas
im = Image.new('RGB', (W, 700), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), f"01  la duna 675 de Traspuesta: {P['terreno']}", font=fn(16), fill=TXT)
im.paste(duna_img(620), (20, 50))
d.text((670, 50), 'las quince crestas más prominentes (como las quince piedras de Ryoan-ji)\ny su transecto del noreste (barlovento: la ladera suave) al suroeste\n(sotavento: la cara de avalancha, abrupta — de ahí baja la arena que canta)', font=fn(13), fill=TXT, spacing=6)
for k, c in enumerate(P['crestas']):
    x0, y0 = 670 + (k % 5) * 205, 140 + (k // 5) * 180; col = tinta(k, 15, .8)
    d.text((x0, y0), f'cresta {k + 1}', font=fn(12), fill=col)
    pts = [(x0 + i * 190 / (len(c) - 1), y0 + 150 - v * 120) for i, v in enumerate(c)]; d.line(pts, fill=col, width=2); d.line([x0, y0 + 150, x0 + 190, y0 + 150], fill=TENUE)
d.text((670, 680), 'NE  →  SO', font=fn(12), fill=TENUE)
guardar(im, f'01-duna-y-crestas-s{s}-{h}.png')

# 02 · las crestas como melodía
im = Image.new('RGB', (W, 620), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '02  las crestas como melodía — arriba: la garganta de duna canta el contorno de cuatro crestas como glisandos (Cage, Ryoan-ji);', font=fn(15), fill=TXT)
d.text((14, 32), '    abajo: el solo de guitarra NÓMADA (Khannanov): la pentatónica sigue la altura, la ladera suave da notas largas, la cara de avalancha corre; acentos por gradación', font=fn(13), fill=TXT)
ry = [e for e in P['garganta'] if 'ryoanji' in e]; t0, t1 = ry[0]['t'] - .5, ry[-1]['t'] + ry[-1]['dur'] + .5
for e in ry:
    col = tinta(e['ryoanji'], 4, .8); pts = [(30 + (e['t'] + u * e['dur'] - t0) / (t1 - t0) * (W - 60), 260 - (n - P['raiz'] - 12) * 9) for u, n in e['curva']]
    d.line(pts, fill=col, width=3); d.text((pts[0][0], 270), f"«{e['fonemas'][0]}»", font=fn(12), fill=col)
gs = [e for e in P['guitarra'] if e.get('solo')]; t0, t1 = gs[0]['t'], gs[-1]['t'] + gs[-1]['dur']
for e in gs:
    x = 30 + (e['t'] - t0) / (t1 - t0) * (W - 60); x2 = 30 + (e['t'] + e['dur'] - t0) / (t1 - t0) * (W - 60); y = 590 - (e['m'] - P['raiz'] - 12) * 8
    col = oklch(.45 + .45 * e['v'], .12, ARENA + 30); d.rectangle([x, y - 3, max(x + 2, x2 - 1), y + 3], fill=col)
for c in P['solo']: d.text((30 + (c['t0'] - t0) / (t1 - t0) * (W - 60), 330), f"cresta {c['cresta'] + 1}", font=fn(12), fill=tinta(c['cresta'], 15, .8))
guardar(im, f'02-crestas-como-melodia-s{s}-{h}.png')

# 03 · la nota y el pulso
im = Image.new('RGB', (W, 560), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), f"03  la nota: f₀ = 0.4·√(g/d) con d = {P['grano_mm']:.2f} mm → {P['f0']:.1f} Hz.  El pulso: la corchea del 12/8 = f₀/16 = {16 / 16 / P['tresillo']:.2f} golpes/s ({P['tresillo'] * 1000:.0f} ms).", font=fn(15), fill=TXT)
d.text((14, 34), '    En cada avalancha la frecuencia de los choques sube cuatro octavas: las palmas se vuelven la nota (Kontakte X, al revés). Abajo, la coherencia r de Kuramoto.', font=fn(13), fill=TXT)
def curva(v, t): return np.interp(t, [a for a, _ in v], [b for _, b in v])
tt = np.linspace(0, DUR, 1600); f = curva(P['duna']['f'], tt); fl = curva(P['duna']['flujo'], tt)
y_f = lambda fr: 300 - (math.log2(fr) - math.log2(4)) / (math.log2(120) - math.log2(4)) * 220
for fr, lab in ((4.86, 'pulso (4.86)'), (19.4, '~20 Hz: el ritmo se vuelve altura'), (P['f0'], f"f₀ {P['f0']:.1f}")):
    d.line([60, y_f(fr), W - 20, y_f(fr)], fill=oklch(.32, .03, ARENA)); d.text((W - 300, y_f(fr) - 15), lab, font=fn(11), fill=TENUE)
d.line([(60 + x / DUR * (W - 80), y_f(v)) for x, v in zip(tt, f)], fill=oklch(.8, .13, ARENA), width=2)
d.text((10, 70), 'Hz\n(log)', font=fn(11), fill=TENUE)
rr = COH[:int(DUR * 100)]; tx = np.arange(len(rr)) / 100
d.line([(60 + x / DUR * (W - 80), 520 - r * 170) for x, r in zip(tx[::20], rr[::20])], fill=oklch(.75, .12, ARENA + 200), width=2)
d.line([(60 + x / DUR * (W - 80), 520 - v * 170) for x, v in zip(tt, fl)], fill=oklch(.5, .05, ARENA), width=1)
d.text((10, 345), 'r (azul)\nflujo (gris)', font=fn(11), fill=TENUE); secciones(d, 60, W - 80, 60, 540)
guardar(im, f'03-nota-y-pulso-s{s}-{h}.png')

def espectro(x, alto, fmin=25, fmax=12000, hop=1024, Nf=2048, lin=False):
    win = np.hanning(Nf); fr = [np.abs(np.fft.rfft(x[i:i + Nf] * win)) for i in range(0, len(x) - Nf, hop)]
    Sx = 20 * np.log10(np.array(fr).T + 1e-9); f = np.fft.rfftfreq(Nf, 1 / SR); filas = (np.linspace(fmin, fmax, alto) if lin else np.geomspace(fmin, fmax, alto))[::-1]
    img = Sx[np.searchsorted(f, filas)]; return np.clip((img - (img.max() - 65)) / 65, 0, 1)
def pinta(img, col): F = np.array(FONDO); return (np.power(img[..., None], 1.3) * np.array(col) + F * (1 - img[..., None])).astype(np.uint8)
def leer(c, st): x = np.fromfile(os.path.join(RUN, c + '.f32'), dtype=np.float32).astype(float); return x.reshape(-1, 2).mean(1) if st else x

# 04 · la avalancha 2 de cerca
a0, a1 = P['avalanchas'][1]; dn = (leer('duna', True) + .6 * leer('duna2', True))[int(a0 * SR) - SR:int(a1 * SR) + 2 * SR]   # las dos dunas (la segunda a −4.4 dB, como en la mezcla)
im = Image.new('RGB', (W, 520), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), f'04  la avalancha 2 de cerca ({a0:.0f}–{a1:.0f} s), las dos dunas, 0–600 Hz lineal: los choques sincronizados aceleran de 4.86 a {P["f0"]:.1f} Hz y la masa', font=fn(15), fill=TXT)
d.text((14, 32), f'    se vuelve nota (con sus armónicos); entra la segunda duna, más fina ({P["f0b"]:.1f} Hz): batido; al final regresa a clics (Kontakte X completo)', font=fn(13), fill=TXT)
im.paste(Image.fromarray(pinta(espectro(dn, 420, 20, 600, hop=256, Nf=8192, lin=True), oklch(.85, .12, ARENA))).resize((W - 80, 440)), (60, 64))
for fr in (P['f0'], P['f0b'], 2 * P['f0'], 2 * P['f0b'], 3 * P['f0']): y = 64 + 440 * (1 - (fr - 20) / 580); d.text((8, y - 7), f'{fr:.0f}', font=fn(11), fill=TENUE)
guardar(im, f'04-avalancha-de-cerca-s{s}-{h}.png')
if B is not None: sys.exit()

# 05 · Clapping Music
im = Image.new('RGB', (W, 470), FONDO); d = ImageDraw.Draw(im); CL = P['clapping']
d.text((14, 10), '05  Clapping Music (Reich, 1972) en IV: la primera palma fija, la segunda se corre un pulso cada dos compases — la duna migra con el viento y el pulso no cambia', font=fn(15), fill=TXT)
d.text((14, 32), '    («corre estando quieta», Khannanov). Doce corrimientos, veinticuatro compases, y vuelven a coincidir.', font=fn(13), fill=TXT)
for k in range(13):
    y0 = 64 + k * 30; d.text((14, y0 + 6), f'{2 * k:2d}', font=fn(11), fill=TENUE)
    for j in range(12):
        x = 60 + j * 26; d.rectangle([x, y0, x + 22, y0 + 22], fill=tinta(0, 2, .7) if CL[j] else oklch(.2, .02, ARENA))
        x = 420 + j * 26; d.rectangle([x, y0, x + 22, y0 + 22], fill=tinta(1, 2, .7) if CL[(j + k) % 12] else oklch(.2, .02, ARENA))
        x = 780 + j * 26; both = CL[j] and CL[(j + k) % 12]; d.rectangle([x, y0, x + 22, y0 + 22], fill=oklch(.88, .08, ARENA) if both else (tinta(0, 2, .45) if CL[j] or CL[(j + k) % 12] else oklch(.2, .02, ARENA)))
d.text((60, 455 - 20), 'palma 1', font=fn(12), fill=tinta(0, 2)); d.text((420, 435), 'palma 2', font=fn(12), fill=tinta(1, 2)); d.text((780, 435), 'juntas (claro: coinciden)', font=fn(12), fill=TXT)
guardar(im, f'05-clapping-music-s{s}-{h}.png')

# 06 · quién toca
im = Image.new('RGB', (W, 560), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '06  quién toca: la duna, el guembri, los qraqeb, la guitarra y su solo, las palmas, el hyperpop seco, la llamada y el coro, la garganta de duna', font=fn(15), fill=TXT)
filas = [('duna (Hz)', [(a, 0, 69 + 12 * math.log2(f / 440)) for a, f in P['duna']['f']]), ('guembri', [(e['t'], e['dur'], e['m']) for e in P['guembri']]),
         ('qraqeb', [(e['t'], .05, 0) for e in P['qraqeb']]), ('guitarra', [(e['t'], e['dur'], e['m']) for e in P['guitarra'] if not e.get('solo')]),
         ('solo nómada', [(e['t'], e['dur'], e['m']) for e in P['guitarra'] if e.get('solo')]), ('palmas', [(e['t'], .05, 0 if k == 'palmas1' else 1) for k in ('palmas1', 'palmas2') for e in P['web'][k]]),
         ('808 · sub', [(e['t'], e['dur'], e['midi']) for e in P['sub']]), ('llamada (Sabina)', [(e['t'], e['dur'], e['nota']) for e in P['sabina'][0]['eventos']]),
         ('coro (soprano)', [(e['t'], e['dur'], e['nota']) for e in P['sabina'][1]['eventos']]), ('garganta de duna', [(e['t'], e['dur'], e['nota']) for e in P['garganta']])]
for k, (nom, ns) in enumerate(filas):
    col = tinta(k, len(filas), .75); y0 = 48 + k * 50; d.text((10, y0 + 14), nom, font=fn(12), fill=col)
    lo, hi = min(n[2] for n in ns), max(n[2] for n in ns) + 1
    if nom.startswith('duna'):
        d.line([(170 + t / DUR * (W - 190), y0 + 40 - (m - lo) / (hi - lo) * 36) for t, _, m in ns], fill=col, width=2); continue
    for t, du, m in ns: x = 170 + t / DUR * (W - 190); x2 = 170 + (t + du) / DUR * (W - 190); y = y0 + 40 - (m - lo) / (hi - lo) * 36; d.rectangle([x, y - 1, max(x + 1, x2), y + 1], fill=col)
secciones(d, 170, W - 190, 40, 550); guardar(im, f'06-voces-s{s}-{h}.png')

# 07 · capas solas
capas = [(c, True) for c in P['web'] if P['web'][c]] + [(c, True) for c in ('duna', 'duna2', 'duna-voz', 'viento')] + [(c, False) for c in ('garganta', 'garganta-final', 'guembri', 'guitarra', 'guitarra-solo')] + [('sabina-lead', True), ('sabina-soprano', True)]
alto = 36; x0 = 160; im = Image.new('RGB', (W, 50 + (alto + 5) * len(capas)), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '07  las capas solas, antes de mezclar (25 Hz–12 kHz) — los qraqeb y el sub (Python) se ven en la 08', font=fn(16), fill=TXT)
for k, (c, st) in enumerate(capas):
    col = tinta(k, len(capas)); y0 = 46 + k * (alto + 5); im.paste(Image.fromarray(pinta(espectro(leer(c, st), alto, hop=2048), col)).resize((W - x0 - 10, alto)), (x0, y0)); d.text((8, y0 + 10), c, font=fn(12), fill=col)
secciones(d, x0, W - x0 - 10, 36, im.height - 4); guardar(im, f'07-capas-s{s}-{h}.png')

# 08 · mezcla
sr, x = wavfile.read(os.path.join(OUT, os.path.basename(OUT) + '.wav')); x = x.astype(float).mean(1) / 32768
mez = Image.new('RGB', (W, 400), FONDO); mez.paste(Image.fromarray(pinta(espectro(x, 330), oklch(.92, .05, ARENA))).resize((W - 20, 330)), (10, 50)); d = ImageDraw.Draw(mez)
d.text((14, 10), f'08  La duna que canta (s{s}): la mezcla, {len(x) / sr:.0f} s', font=fn(18), fill=TXT); secciones(d, 10, W - 20, 44, 385)
guardar(mez, f'08-mezcla-s{s}-{h}.png')

# GIF: la duna con la cresta que suena, la sección, la coherencia; la mezcla abajo
def sec_de(t):
    k = 0
    for i, e in enumerate(SC):
        if t >= e['t']: k = i
    return SC[k]
cuadros = []; NC = 36
for j in range(1, NC + 1):
    t = DUR * j / NC; c = Image.new('RGB', (W, 800), FONDO); dd = ImageDraw.Draw(c); e = sec_de(t)
    k = min(14, int(t / DUR * 15)); c.paste(duna_img(380, k), (20, 10))
    dd.text((430, 30), e['num'] + '  ' + e['nombre'], font=fn(28), fill=TXT)
    r = COH[min(len(COH) - 1, int(t * 100))]; f = float(np.interp(t, [a for a, _ in P['duna']['f']], [b for _, b in P['duna']['f']]))
    dd.text((430, 80), f'la duna: {f:5.1f} Hz · coherencia r = {r:.2f}', font=fn(18), fill=oklch(.8, .12, ARENA + 200))
    dd.rectangle([430, 115, 430 + int(600 * r), 130], fill=oklch(.75, .12, ARENA + 200))
    dd.text((430, 145), f'cresta {k + 1} · {t:5.1f} s', font=fn(16), fill=TENUE)
    c.paste(mez, (0, 400)); xx = 10 + int((W - 20) * j / NC); dd.rectangle([xx, 450, W - 10, 780], fill=FONDO); dd.line([xx, 450, xx, 780], fill=TXT, width=2)
    cuadros.append(c.resize((1100, 518)))
gif = os.path.join(OUT, f'la-duna-que-canta-s{s}-{h}.gif'); cuadros[0].save(gif, save_all=True, append_images=cuadros[1:] + [cuadros[-1]] * 2, duration=260, loop=0, optimize=True)
cuadros[-1].save(nuevo(f'09-duna-y-mezcla-s{s}-{h}.png'))
print(gif, os.path.getsize(gif) // 1024, 'KB')
