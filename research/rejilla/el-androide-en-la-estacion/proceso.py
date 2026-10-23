"""El androide en la estación — PNGs de etapas y GIF del proceso.
    python proceso.py <carpeta-de-render> <carpeta-de-entrega> [--b 03,04]
01 el archipiélago 2038 y el descenso por gradiente (con la batimetría inventada) · 02 la pulsación de 17 s: tónica y tempo; la
retícula frigia arriba y la serie armónica abajo · 03 el traductor que se oxida: sus coeficientes de reflexión en el tiempo y la
voz guía contra la voz de la celosía · 04 el convoy que no sale: el espectro sube para siempre y en el descenso baja · 05 las
luciérnagas: destellos y coherencia · 06 quién toca · 07 las capas solas · 08 la mezcla · GIF: la terminal baja por el
archipiélago mientras suena la mezcla. Colores OKLCh sembrados (s2038): el silicio frío, el carbono tibio.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
AQUI = os.path.dirname(os.path.abspath(__file__))
RUN, OUT = sys.argv[1], sys.argv[2]; P = json.load(open(os.path.join(OUT, 'partitura.json'), encoding='utf-8'))
h = os.path.basename(OUT).rsplit('-', 1)[1]; s = P['semilla']; pr = os.path.join(OUT, 'proceso')
B = sys.argv[sys.argv.index('--b') + 1].split(',') if '--b' in sys.argv else None
if B is None: os.makedirs(pr, exist_ok=False)
DUR = P['duracion']; SR = 48000; W = 1700; G = 360; SC = P['secciones']
H = np.fromfile(os.path.join(AQUI, 'terreno', 'h-2038.f32'), dtype=np.float32).reshape(G, G)
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
FRIO = 190 + (s * 3.1) % 40; TIBIO = 40 + (s * 1.7) % 30                     # silicio y carbono, sembrados
FONDO = oklch(.12, .02, FRIO + 20); TXT = oklch(.9, .03, FRIO); TENUE = oklch(.55, .03, FRIO)
def tinta(k, n, L=.75): return oklch(L, .12, FRIO + (TIBIO + 360 - FRIO) * k / max(1, n - 1))   # del frío al tibio: el descenso
def secciones(d, x0, Wd, y0, y1):
    for e in SC: xa = x0 + int(e['t'] / DUR * Wd); d.line([xa, y0, xa, y1], fill=oklch(.35, .03, FRIO)); d.text((xa + 4, y0 + 2), e['num'] + ' ' + e['nombre'][:20], font=fn(11), fill=TENUE)
def isla_img(lado, hasta=None):
    from scipy.ndimage import distance_transform_edt
    mar = H <= 1e-4; prof = np.sqrt(distance_transform_edt(mar)); prof /= prof.max()
    lv = (H * 20).astype(int); borde = (np.abs(np.diff(lv, axis=0, prepend=lv[:1])) + np.abs(np.diff(lv, axis=1, prepend=lv[:, :1]))) > 0
    tierra_b, tierra_a = np.array(oklch(.3, .05, TIBIO)), np.array(oklch(.75, .1, TIBIO))
    agua_s, agua_p = np.array(oklch(.35, .07, FRIO)), np.array(oklch(.1, .03, FRIO))
    img = np.where(mar[..., None], agua_s + prof[..., None] * (agua_p - agua_s), tierra_b + H[..., None] * (tierra_a - tierra_b))
    img[borde & ~mar] = oklch(.9, .08, TIBIO); lvp = (prof * 10).astype(int); bp = (np.abs(np.diff(lvp, axis=0, prepend=lvp[:1])) + np.abs(np.diff(lvp, axis=1, prepend=lvp[:, :1]))) > 0
    img[bp & mar] = oklch(.45, .06, FRIO)
    im = Image.fromarray(img.astype(np.uint8)).resize((lado, lado), Image.BILINEAR); d = ImageDraw.Draw(im); C = P['camino']
    n = len(C) if hasta is None else max(2, int(hasta * len(C)))
    d.line([(a * lado, b * lado) for a, b, _ in C[:n]], fill=oklch(.95, .05, FRIO), width=3)
    a, b, _ = C[n - 1]; d.ellipse([a * lado - 6, b * lado - 6, a * lado + 6, b * lado + 6], outline=oklch(.95, .15, FRIO), width=3)
    return im

# 01 · el archipiélago y el descenso por gradiente
im = Image.new('RGB', (W, 700), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), f"01  {P['terreno']}: el descenso por gradiente desde la cumbre — el algoritmo con que se entrena una máquina", font=fn(16), fill=TXT)
im.paste(isla_img(620), (20, 50))
C = np.array(P['camino']); z = C[:, 2]
d.text((680, 60), 'la altura a lo largo del camino (la tierra arriba de 0; abajo, la batimetría INVENTADA: la distancia a la costa)', font=fn(13), fill=TXT)
pts = [(680 + i / (len(z) - 1) * 980, 360 - v * 250) for i, v in enumerate(z)]; d.line([(680, 360), (1660, 360)], fill=TENUE)
for i in range(len(pts) - 1): d.line([pts[i], pts[i + 1]], fill=tinta(i, len(pts)), width=3)
xc = 680 + P['costa'] * 980; d.line([xc, 90, xc, 640], fill=oklch(.6, .08, FRIO)); d.text((xc + 6, 95), 'la costa', font=fn(12), fill=TENUE)
d.text((680, 640), 'la terminal vectorial: x = la altura (de metal a vocal: de silicio a carbono), y = la pendiente (pulso / aire)', font=fn(13), fill=TXT)
guardar(im, f'01-descenso-por-gradiente-s{s}-{h}.png')

# 02 · la pulsación de 17 s
im = Image.new('RGB', (W, 520), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), f"02  «una pulsación cada diecisiete segundos»: ×2¹⁰ = {P['tonica_hz']:.2f} Hz (la tónica) · ×2⁵ = {1 / P['negra']:.3f} Hz (la negra, {60 / P['negra']:.1f} bpm) · 8 compases = 17 s", font=fn(15), fill=TXT)
for k, p in enumerate(P['pulsos']):
    x = 60 + p / DUR * (W - 80); d.line([x, 50, x, 80], fill=oklch(.9, .1, FRIO), width=3)
d.text((60, 86), 'las quince pulsaciones de la pantalla de Sutura (y la última)', font=fn(12), fill=TENUE); secciones(d, 60, W - 80, 110, 500)
R0 = P['raiz']; yy = lambda m: 480 - (m - R0) / 36 * 340
for o in range(3):
    for g in P['frigio']: m = R0 + 12 * o + g; d.line([60, yy(m), 830, yy(m)], fill=tinta(0, 2, .55)); d.text((20, yy(m) - 7), f'{g}', font=fn(10), fill=tinta(0, 2, .6))
    for n in range(8, 17): m = R0 + 12 * o + 12 * math.log2(n / 8); d.line([870, yy(m), W - 20, yy(m)], fill=tinta(1, 2, .6)); d.text((W - 16, yy(m) - 7), f'{n}', font=fn(10), fill=tinta(1, 2, .65))
d.text((60, 135), 'arriba: la retícula (frigio temperado: el silicio)', font=fn(13), fill=tinta(0, 2)); d.text((870, 135), 'abajo: la serie armónica de la misma tónica (parciales 8–16: el carbono)', font=fn(13), fill=tinta(1, 2))
guardar(im, f'02-pulsacion-y-afinacion-s{s}-{h}.png')

# 03 · el traductor que se oxida
K = json.load(open(os.path.join(RUN, 'traductor-k.json'))); Km = np.array([k[1:] for k in K]); tk = np.array([k[0] for k in K])
im = Image.new('RGB', (W, 640), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '03  el traductor que se oxida: sus 16 coeficientes de reflexión en el tiempo (la celosía del chip LPC = las secciones del tubo de la garganta)', font=fn(15), fill=TXT)
d.text((14, 32), '    con óxido 0 saltan en escalones de 22.5 ms (LPC-10, cuantizado); luego se arrastran, el óxido salta en las uniones y al final toman la forma de la isla', font=fn(13), fill=TXT)
Kimg = (np.clip(Km.T, -1, 1) + 1) / 2; ancho_ = W - 80
pal = np.array([oklch(.15 + .75 * v, .12, FRIO + (TIBIO + 360 - FRIO) * v) for v in np.linspace(0, 1, 64)])
img = pal[(Kimg * 63).astype(int)]; im.paste(Image.fromarray(img.astype(np.uint8)).resize((ancho_, 300), Image.NEAREST), (60, 70))
ox = P['oxido']; d.line([(60 + a / DUR * ancho_, 560 - b * 170) for a, b in ox], fill=oklch(.8, .14, TIBIO), width=3); d.text((10, 400), 'óxido', font=fn(12), fill=oklch(.8, .14, TIBIO))
for e in P['traductor']: x = 60 + e['t'] / DUR * ancho_; d.line([x, 380, x, 388], fill=TENUE)
d.text((60, 590), 'las rayas: las sílabas del traductor', font=fn(11), fill=TENUE); secciones(d, 60, ancho_, 372, 600)
guardar(im, f'03-traductor-se-oxida-s{s}-{h}.png')

def espectro(x, alto, fmin=25, fmax=12000, hop=1024, Nf=2048, lin=False):
    win = np.hanning(Nf); fr = [np.abs(np.fft.rfft(x[i:i + Nf] * win)) for i in range(0, len(x) - Nf, hop)]
    Sx = 20 * np.log10(np.array(fr).T + 1e-9); f = np.fft.rfftfreq(Nf, 1 / SR); filas = (np.linspace(fmin, fmax, alto) if lin else np.geomspace(fmin, fmax, alto))[::-1]
    img = Sx[np.searchsorted(f, filas)]; return np.clip((img - (img.max() - 65)) / 65, 0, 1)
def pinta(img, col): F = np.array(FONDO); return (np.power(img[..., None], 1.3) * np.array(col) + F * (1 - img[..., None])).astype(np.uint8)
def leer(c, st): x = np.fromfile(os.path.join(RUN, c + '.f32'), dtype=np.float32).astype(float); return x.reshape(-1, 2).mean(1) if st else x

# 04 · el convoy
cv = leer('convoy', True); a0, a1 = 0, P['secciones'][4]['t'] + 20
im = Image.new('RGB', (W, 520), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), f'04  el convoy que no sale (sólo el convoy, 0–{a1:.0f} s, 30–2000 Hz log): parciales a octavas de la tónica que suben para siempre (Shepard–Risset);', font=fn(15), fill=TXT)
d.text((14, 32), '    en el descenso se invierte y baja para siempre; arriba de todo, las juntas del riel aceleran sin llegar', font=fn(13), fill=TXT)
im.paste(Image.fromarray(pinta(espectro(cv[:int(a1 * SR)], 420, 30, 2000, hop=1024, Nf=8192), oklch(.85, .1, FRIO))).resize((W - 80, 440)), (60, 64))
guardar(im, f'04-convoy-que-no-sale-s{s}-{h}.png')

# 05 · las luciérnagas
rr = np.load(os.path.join(RUN, 'luciernagas-r.npy')) if os.path.exists(os.path.join(RUN, 'luciernagas-r.npy')) else None
im = Image.new('RGB', (W, 420), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '05  las luciérnagas (Didi-Huberman: la luz que el reflector no borra): 40 osciladores de Kuramoto cerca de la negra; el acoplamiento las junta y', font=fn(15), fill=TXT)
d.text((14, 32), '    en VI la pantalla de Sutura las arrastra a su pulso. Coherencia r (0–1) en el tiempo.', font=fn(13), fill=TXT)
if rr is not None:
    t0 = rr[0, 0]; xs = 60 + (rr[0] - 0) / DUR * (W - 80); d.line(list(zip(xs[::50], 380 - rr[1][::50] * 300)), fill=oklch(.85, .14, TIBIO + 30), width=2)
secciones(d, 60, W - 80, 60, 400); guardar(im, f'05-luciernagas-s{s}-{h}.png')

# 06 · quién toca
TT = P['tres_tiempos']
filas = [('traductor', [(e['t'], e['dur'], e['nota']) for e in P['traductor']]), ('voz de andén', [(e['t'], e['dur'], e['nota']) for e in P['sabina'][1]['eventos']]),
         ('coro (soprano)', [(e['t'], e['dur'], e['nota']) for e in P['sabina'][2]['eventos']]), ('boca (simbionte)', [(n['t'], n['dur'], n['midi']) for n in TT['boca']['notas']])]
for k in ('androide', 'cristal', 'terminal', 'estacion', 'plasma', 'fotones', 'arpa', 'cuerda', 'sala'):
    filas.append((k, [(n['t'], n['dur'], n['midi']) for n in TT[k]['notas']]))
filas += [('808 · sub', [(e['t'], e['dur'], e['midi']) for e in P['sub']]), ('estación', [(e['t'], .3, 0) for e in P['impresora'] + P['torniquete'] + P['campana']])]
im = Image.new('RGB', (W, 60 + 42 * len(filas)), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '06  quién toca: el traductor y las voces arriba; el silicio en medio; el carbono abajo; la estación Sutura al fondo', font=fn(15), fill=TXT)
for k, (nom, ns) in enumerate(filas):
    col = tinta(k, len(filas), .75); y0 = 44 + k * 42; d.text((10, y0 + 12), nom, font=fn(12), fill=col)
    if not ns: continue
    lo, hi = min(n[2] for n in ns), max(n[2] for n in ns) + 1
    for t, du, m in ns: x = 170 + t / DUR * (W - 190); x2 = 170 + (t + du) / DUR * (W - 190); y = y0 + 34 - (m - lo) / (hi - lo) * 30; d.rectangle([x, y - 1, max(x + 1, x2), y + 1], fill=col)
secciones(d, 170, W - 190, 36, im.height - 4); guardar(im, f'06-voces-s{s}-{h}.png')
if B is not None: sys.exit()

# 07 · capas solas
capas = [(c, True) for c in P['web'] if P['web'][c]] + [(c, True) for c in ('boca', 'arpa', 'cuerda', 'sala', 'organo', 'cristal', 'estacion', 'terminal', 'terminal-solo', 'plasma', 'androide', 'androide-solo', 'fotones', 'convoy')]
capas += [('traductor', False), ('agua', False), ('sabina-guia', True), ('sabina-anden', True), ('sabina-soprano', True)]
alto = 30; x0 = 160; im = Image.new('RGB', (W, 50 + (alto + 4) * len(capas)), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '07  las capas solas, antes de mezclar (25 Hz–12 kHz) — la estación, las luciérnagas y el sub (Python) se ven en la 08; sabina-guia no suena: la analiza el traductor', font=fn(14), fill=TXT)
for k, (c, st) in enumerate(capas):
    col = tinta(k, len(capas)); y0 = 44 + k * (alto + 4); im.paste(Image.fromarray(pinta(espectro(leer(c, st), alto, hop=2048), col)).resize((W - x0 - 10, alto)), (x0, y0)); d.text((8, y0 + 8), c, font=fn(11), fill=col)
secciones(d, x0, W - x0 - 10, 36, im.height - 4); guardar(im, f'07-capas-s{s}-{h}.png')

# 08 · mezcla
sr, x = wavfile.read(os.path.join(OUT, os.path.basename(OUT) + '.wav')); x = x.astype(float).mean(1) / 32768
mez = Image.new('RGB', (W, 400), FONDO); mez.paste(Image.fromarray(pinta(espectro(x, 330), oklch(.92, .04, FRIO))).resize((W - 20, 330)), (10, 50)); d = ImageDraw.Draw(mez)
d.text((14, 10), f'08  El androide en la estación (s{s}): la mezcla, {len(x) / sr:.0f} s', font=fn(18), fill=TXT); secciones(d, 10, W - 20, 44, 385)
guardar(mez, f'08-mezcla-s{s}-{h}.png')

# GIF: la terminal baja por el archipiélago; el óxido; la mezcla
def sec_de(t):
    k = 0
    for i, e in enumerate(SC):
        if t >= e['t']: k = i
    return SC[k]
vx = P['tres_tiempos']['terminal']['controles']['vector_x']; t2, t6 = SC[1]['t'], SC[5]['t']
cuadros = []; NC = 36
for j in range(1, NC + 1):
    t = DUR * j / NC; c = Image.new('RGB', (W, 800), FONDO); dd = ImageDraw.Draw(c); e = sec_de(t)
    cst = P['costa']; sp = float(np.interp(t, [t2, SC[3]['t'] + 8 * P['compas'], t6], [0, cst, 1]))
    c.paste(isla_img(380, max(.01, sp)), (20, 10)); dd.text((430, 30), e['num'] + '  ' + e['nombre'], font=fn(28), fill=TXT)
    o = float(np.interp(t, [a for a, _ in P['oxido']], [b for _, b in P['oxido']]))
    dd.text((430, 80), f'óxido del traductor {o:.2f}', font=fn(18), fill=oklch(.8, .14, TIBIO)); dd.rectangle([430, 112, 430 + int(600 * o), 126], fill=oklch(.75, .14, TIBIO))
    pul = min(len(P['pulsos']), int(t // P['periodo']) + 1); dd.text((430, 145), f'pulsación {pul} de {len(P["pulsos"])} · {t:5.1f} s', font=fn(16), fill=TENUE)
    c.paste(mez, (0, 400)); xx = 10 + int((W - 20) * j / NC); dd.rectangle([xx, 450, W - 10, 780], fill=FONDO); dd.line([xx, 450, xx, 780], fill=TXT, width=2)
    cuadros.append(c.resize((1100, 518)))
gif = os.path.join(OUT, f'el-androide-en-la-estacion-s{s}-{h}.gif'); cuadros[0].save(gif, save_all=True, append_images=cuadros[1:] + [cuadros[-1]] * 2, duration=260, loop=0, optimize=True)
cuadros[-1].save(nuevo(f'09-descenso-y-mezcla-s{s}-{h}.png'))
print(gif, os.path.getsize(gif) // 1024, 'KB')
