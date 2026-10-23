"""Lo que la cinta olvida — PNGs de etapas y GIF del proceso.
    python proceso.py <carpeta-de-render> <carpeta-de-entrega> [--b 03,04]
01 la llanura de meandros 26 y sus 13 vueltas (los cuatro cortes) · 02 rebajar = la sinuosidad: la velocidad de la cinta por vuelta
y el reloj de la cinta contra el reloj real · 03 la banda antes y después de la cinta (el mismo tramo: más lento y más grave) ·
04 los lagos de herradura: cada pasada más gastada · 05 quién toca · 06 las capas solas · 07 la mezcla · GIF: el río se recorre
mientras suena, y los lagos se encienden al cortarse. Colores OKLCh sembrados (s26): el agua y la tierra de la llanura.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
AQUI = os.path.dirname(os.path.abspath(__file__))
RUN, OUT = sys.argv[1], sys.argv[2]; P = json.load(open(os.path.join(OUT, 'partitura.json'), encoding='utf-8')); RC = json.load(open(os.path.join(OUT, 'receta.json'), encoding='utf-8'))
h = os.path.basename(OUT).rsplit('-', 1)[1]; s = P['semilla']; pr = os.path.join(OUT, 'proceso')
B = sys.argv[sys.argv.index('--b') + 1].split(',') if '--b' in sys.argv else None
if B is None: os.makedirs(pr, exist_ok=False)
DUR = P['duracion']; SR = 48000; W = 1700; G = 360; VU = P['vueltas']
H = np.fromfile(os.path.join(AQUI, 'terreno', 'h-26.f32'), dtype=np.float32).reshape(G, G)
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
AGUA = 200 + (s * 7.7) % 30; TIERRA = 70 + (s * 3.3) % 25
FONDO = oklch(.13, .015, TIERRA); TXT = oklch(.9, .03, TIERRA); TENUE = oklch(.55, .03, TIERRA)
def tinta(k, n, L=.75): return oklch(L, .12, TIERRA + (AGUA - TIERRA) * k / max(1, n - 1))
SECS = {'intro': (0, VU[0]['t0']), 'cumbia': (VU[0]['t0'], VU[3]['t1']), 'rebajada': (VU[4]['t0'], VU[6]['t1']), 'vivo': (VU[7]['t0'], P['fin_cinta']), 'coda': (P['fin_cinta'], DUR)}
def secciones(d, x0, Wd, y0, y1):
    for k, (a, z) in SECS.items(): xa = x0 + int(a / DUR * Wd); d.line([xa, y0, xa, y1], fill=oklch(.35, .03, TIERRA)); d.text((xa + 4, y0 + 2), k, font=fn(11), fill=TENUE)
CAU = np.array(P['cauce']); INF = P['inflexiones']
def vuelta_de_indice(i3):
    i = i3 * 3
    for vu, (a, b) in zip(VU, zip(INF[:-1], INF[1:])):
        if a <= i < b: return vu
    return None
def llanura(lado, hasta=None, lagos_on=()):
    lv = (H * 18).astype(int); borde = (np.abs(np.diff(lv, axis=0, prepend=lv[:1])) + np.abs(np.diff(lv, axis=1, prepend=lv[:, :1]))) > 0
    b0, b1 = np.array(oklch(.22, .04, TIERRA)), np.array(oklch(.55, .07, TIERRA)); img = b0 + H[..., None] * (b1 - b0); img[borde] = oklch(.7, .06, TIERRA)
    im = Image.fromarray(img.astype(np.uint8)).resize((lado, lado), Image.BILINEAR); d = ImageDraw.Draw(im)
    n = len(CAU) if hasta is None else max(2, int(hasta * len(CAU)))
    for i in range(1, len(CAU)):
        vu = vuelta_de_indice(i); k = (vu['n'] - 1) if vu else 0
        col = (tinta(k, 13, .8) if i < n else oklch(.35, .03, AGUA)) if vu else oklch(.5, .03, AGUA)
        w = 4 if (vu and vu['corte'] and (vu['n'] in lagos_on or hasta is None)) else 2
        d.line([tuple(CAU[i - 1] * lado), tuple(CAU[i] * lado)], fill=col, width=w)
    for i in INF: x, y = np.array(P['cauce'])[min(len(CAU) - 1, i // 3)] * lado; d.ellipse([x - 3, y - 3, x + 3, y + 3], outline=TENUE)
    return im

# 01 · la llanura y sus vueltas
im = Image.new('RGB', (W, 700), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), f"01  {P['terreno']}: las 13 vueltas del río entre las inflexiones de la curvatura; en gruesas, las cuatro más sinuosas (los cortes)", font=fn(15), fill=TXT)
im.paste(llanura(620), (20, 50))
for k, vu in enumerate(VU):
    y = 60 + k * 47; col = tinta(k, 13, .8)
    d.text((680, y), f"vuelta {vu['n']:2}  sinuosidad {vu['sinuosidad']:.2f}  →  v = {vu['v']:.2f}  ·  {120 * vu['v']:.0f} bpm  ·  {12 * math.log2(vu['v']):+.1f} semitonos" + ('   CORTE: lago de herradura' if vu['corte'] else ''), font=fn(14), fill=col)
    d.rectangle([680, y + 22, 680 + int(vu['sinuosidad'] / 3.2 * 900), y + 30], fill=col)
guardar(im, f'01-llanura-y-vueltas-s{s}-{h}.png')

# 02 · los dos relojes
M = P['mapa']; tau, tt, vv = np.array(M['tau']), np.array(M['t']), np.array(M['v'])
im = Image.new('RGB', (W, 560), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '02  rebajar = la sinuosidad: la cinta corre a la velocidad con que el río avanza valle abajo, v = (cuerda ÷ arco)^½. Arriba: v en el tiempo real.', font=fn(15), fill=TXT)
d.text((14, 32), '    Abajo: el reloj de la cinta (τ, la partitura a 120 bpm) contra el reloj real — donde el río se enreda, la curva se acuesta: la cumbia se rebaja', font=fn(13), fill=TXT)
X = lambda t: 60 + t / DUR * (W - 80)
d.line([(X(a), 250 - b * 220) for a, b in zip(tt, vv)], fill=oklch(.8, .13, AGUA), width=3); d.text((10, 30 + 220 * .2), 'v', font=fn(12), fill=TENUE)
for vref in (.6, .7, .8): d.line([60, 250 - vref * 220, W - 20, 250 - vref * 220], fill=oklch(.3, .02, TIERRA)); d.text((W - 60, 250 - vref * 220 - 14), f'{vref}', font=fn(10), fill=TENUE)
d.line([(X(a), 540 - b / tau[-1] * 260) for a, b in zip(tt, tau)], fill=oklch(.8, .13, TIERRA), width=3); d.line([(X(0), 540), (X(tau[-1]), 280)], fill=TENUE)
d.text((X(tau[-1]) + 6, 285), 'sin rebajar', font=fn(11), fill=TENUE); secciones(d, 60, W - 80, 260, 548)
guardar(im, f'02-dos-relojes-s{s}-{h}.png')

def espectro(x, alto, fmin=30, fmax=8000, hop=1024, Nf=4096):
    win = np.hanning(Nf); fr = [np.abs(np.fft.rfft(x[i:i + Nf] * win)) for i in range(0, len(x) - Nf, hop)]
    Sx = 20 * np.log10(np.array(fr).T + 1e-9); f = np.fft.rfftfreq(Nf, 1 / SR); filas = np.geomspace(fmin, fmax, alto)[::-1]
    img = Sx[np.searchsorted(f, filas)]; return np.clip((img - (img.max() - 60)) / 60, 0, 1)
def pinta(img, col): F = np.array(FONDO); return (np.power(img[..., None], 1.3) * np.array(col) + F * (1 - img[..., None])).astype(np.uint8)

# 03 · la banda antes y después de la cinta
bt = np.load(os.path.join(RUN, 'banda-tau.npy')); ci = np.load(os.path.join(RUN, 'cinta.npy')); vu = VU[5]
from partitura import t_
a_tau, b_tau = t_(vu['b0']), t_(vu['b0'] + 2)
im = Image.new('RGB', (W, 620), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), f"03  el mismo tramo (dos compases de la vuelta {vu['n']}, la más cerrada: v = {vu['v']:.2f}) antes y después de la cinta, 30 Hz–8 kHz log, a la misma escala de tiempo", font=fn(15), fill=TXT)
seg1 = bt[int(a_tau * SR):int(b_tau * SR)]; ta, tb = vu['t0'], vu['t0'] + (b_tau - a_tau) / vu['v']; seg2 = ci[int(ta * SR):int(tb * SR)]
ancho2 = W - 80; ancho1 = int(ancho2 * len(seg1) / len(seg2))
im.paste(Image.fromarray(pinta(espectro(seg1, 250, hop=512), oklch(.85, .1, TIERRA))).resize((ancho1, 250)), (60, 50)); d.text((60, 305), f'la banda en tiempo de cinta: {b_tau - a_tau:.1f} s a 120 bpm', font=fn(13), fill=TXT)
im.paste(Image.fromarray(pinta(espectro(seg2, 250, hop=512), oklch(.85, .1, AGUA))).resize((ancho2, 250)), (60, 340)); d.text((60, 595), f'por la cinta: {tb - ta:.1f} s a {120 * vu["v"]:.0f} bpm, {12 * math.log2(vu["v"]):+.1f} semitonos, con wow, cabeza y siseo', font=fn(13), fill=TXT)
guardar(im, f'03-antes-y-despues-de-la-cinta-s{s}-{h}.png')

# 04 · los lagos
im = Image.new('RGB', (W, 640), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '04  los lagos de herradura: cada corte se queda dando vueltas hasta el final y se gasta en cada pasada (Basinski): el óxido se cae en el mismo lugar del loop,', font=fn(15), fill=TXT)
d.text((14, 32), '    el filtro se cierra, la altura se desvía. Arriba: el espectro de cada lago en la canción. Abajo: nivel (línea) y fracción perdida (barras) por pasada', font=fn(13), fill=TXT)
for k, lg in enumerate(P['lagos']):
    x = np.load(os.path.join(RUN, f'lago{k + 1}.npy')); y0 = 60 + k * 70; col = tinta(k * 4, 13, .8)
    im.paste(Image.fromarray(pinta(espectro(x, 60, hop=4096), col)).resize((W - 80, 60)), (60, y0)); d.text((8, y0 + 20), f"vuelta {lg['vuelta']}", font=fn(11), fill=col)
    med = RC['lagos'][str(lg['vuelta'])]
    for m in med:
        xx = X(m['t']); d.rectangle([xx, 620 - m['perdido'] * 120, xx + 4, 620], fill=tuple(int(c * .5) for c in col))
    d.line([(X(m['t']), 470 - (m['nivel_db'] + 60) * 2.2) for m in med], fill=col, width=2)
guardar(im, f'04-lagos-de-herradura-s{s}-{h}.png')

# 05 · quién toca
from partitura import treal
filas = [(c, [(treal(e['t']), treal(e['t'] + e['dur']) - treal(e['t']), e['midi']) for e in P['web'][c]]) for c in ('acordeon', 'bajo', 'guiro', 'conga', 'organo', 'timbal')]
filas += [('requinto', [(treal(e['t']), .2, e['m']) for e in P['requinto']]), ('sonidero', [(treal(e['t']), e['dur'], e['nota']) for e in P['sabina'][0]['eventos']]),
          ('coro', [(treal(e['t']), e['dur'], e['nota']) for e in P['sabina'][1]['eventos']]), ('voz viva', [(e['t'], e['dur'], e['nota']) for e in P['sabina'][2]['eventos']]),
          ('cello', [(e['t'], e['dur'], e['m']) for e in P['chelo']]), ('lagos', [(lg['t1'], DUR - lg['t1'], lg['vuelta']) for lg in P['lagos']])]
im = Image.new('RGB', (W, 60 + 44 * len(filas)), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '05  quién toca, en tiempo real: la banda del sonidero (rebajada por la cinta), las voces, lo vivo y los lagos que se quedan', font=fn(15), fill=TXT)
for k, (nom, ns) in enumerate(filas):
    col = tinta(k, len(filas), .75); y0 = 46 + k * 44; d.text((10, y0 + 12), nom, font=fn(12), fill=col)
    if not ns: continue
    lo, hi = min(n[2] for n in ns), max(n[2] for n in ns) + 1
    for t, du, m in ns: x = 170 + t / DUR * (W - 190); x2 = 170 + (t + du) / DUR * (W - 190); y = y0 + 36 - (m - lo) / (hi - lo) * 32; d.rectangle([x, y - 1, max(x + 1, x2), y + 1], fill=col)
secciones(d, 170, W - 190, 38, im.height - 4); guardar(im, f'05-voces-s{s}-{h}.png')
if B is not None: sys.exit()

# 06 · capas solas
def leer(c, st, n=None):
    x = np.fromfile(os.path.join(RUN, c + '.f32'), dtype=np.float32).astype(float); return x.reshape(-1, 2).mean(1) if st else x
capas = [(c, True) for c in P['web'] if P['web'][c]] + [('requinto', False), ('sabina-sonidero', True), ('sabina-coro', True), ('chelo', False), ('garganta', True), ('agua', False), ('aves', False), ('sabina-viva', True)]
alto = 32; x0 = 170; im = Image.new('RGB', (W, 50 + (alto + 4) * len(capas)), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '06  las capas solas antes de mezclar (30 Hz–8 kHz). La banda está en tiempo de cinta (más corta: todavía no pasa por la cinta); lo vivo, en tiempo real', font=fn(14), fill=TXT)
for k, (c, st) in enumerate(capas):
    col = tinta(k, len(capas)); y0 = 44 + k * (alto + 4); x = leer(c, st); im.paste(Image.fromarray(pinta(espectro(x, alto, hop=4096), col)).resize((max(40, int((W - x0 - 10) * len(x) / SR / DUR)), alto)), (x0, y0)); d.text((8, y0 + 10), c, font=fn(11), fill=col)
guardar(im, f'06-capas-s{s}-{h}.png')

# 07 · mezcla
sr, x = wavfile.read(os.path.join(OUT, os.path.basename(OUT) + '.wav')); x = x.astype(float).mean(1) / 32768
mez = Image.new('RGB', (W, 400), FONDO); mez.paste(Image.fromarray(pinta(espectro(x, 330, fmax=10000), oklch(.92, .04, TIERRA))).resize((W - 20, 330)), (10, 50)); d = ImageDraw.Draw(mez)
d.text((14, 10), f'07  Lo que la cinta olvida (s{s}): la mezcla, {len(x) / sr:.0f} s', font=fn(18), fill=TXT); secciones(d, 10, W - 20, 44, 385)
guardar(mez, f'07-mezcla-s{s}-{h}.png')

# GIF: el río se recorre; los lagos se encienden al cortarse
vel = np.load(os.path.join(RUN, 'velocidad.npy'))
cuadros = []; NC = 36
for j in range(1, NC + 1):
    t = DUR * j / NC; c = Image.new('RGB', (W, 800), FONDO); dd = ImageDraw.Draw(c)
    tau_t = float(np.interp(t, tt, tau)); fr = min(1, tau_t / tau[-1]); on = [lg['vuelta'] for lg in P['lagos'] if t >= lg['t1']]
    c.paste(llanura(380, fr, on), (20, 10))
    vu = next((v for v in VU if t < v['t1']), None); nom = f"VUELTA {vu['n']} · SINUOSIDAD {vu['sinuosidad']:.2f}" if vu and t >= VU[0]['t0'] else ('EL SONIDERO SE PRESENTA' if t < VU[0]['t0'] else 'SÓLO LOS LAGOS')
    dd.text((430, 30), nom, font=fn(26), fill=TXT)
    v = float(vel[min(len(vel) - 1, int(t * 100))]); dd.text((430, 80), f'la cinta a {v:.2f} · {120 * v:.0f} bpm · {12 * math.log2(max(v, .05)):+.1f} semitonos', font=fn(18), fill=oklch(.8, .13, AGUA))
    dd.rectangle([430, 112, 430 + int(600 * v), 126], fill=oklch(.75, .13, AGUA)); dd.text((430, 145), f'lagos: {len(on)} de 4 · {t:5.1f} s', font=fn(16), fill=TENUE)
    c.paste(mez, (0, 400)); xx = 10 + int((W - 20) * j / NC); dd.rectangle([xx, 450, W - 10, 780], fill=FONDO); dd.line([xx, 450, xx, 780], fill=TXT, width=2)
    cuadros.append(c.resize((1100, 518)))
gif = os.path.join(OUT, f'lo-que-la-cinta-olvida-s{s}-{h}.gif'); cuadros[0].save(gif, save_all=True, append_images=cuadros[1:] + [cuadros[-1]] * 2, duration=260, loop=0, optimize=True)
cuadros[-1].save(nuevo(f'08-rio-y-mezcla-s{s}-{h}.png'))
print(gif, os.path.getsize(gif) // 1024, 'KB')
