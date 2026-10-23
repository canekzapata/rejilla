"""La lluvia que hizo los cráteres — PNGs de etapas y GIF del proceso.
    python proceso.py <carpeta-de-render> <carpeta-de-entrega> [--b 03,04]
01 el campo de impactos 18 con sus 41 cráteres (familia, orden de llegada) y el gran impacto con los que borra · 02 cada cráter es un
tambor: f = K / D y los modos de Bessel · 03 la lluvia: los 41 caen en su orden, cada vez más seguido · 04 el footwork: dos compases,
qué cráter toca cada dieciseisavo · 05 el gran impacto de cerca · 06 quién toca · 07 las capas solas · 08 la mezcla · GIF: los cráteres
se encienden cuando suenan. Colores OKLCh sembrados (s18).
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
DUR = P['duracion']; SR = 48000; W = 1700; G = 360; TB = P['tambores']; GR = P['gran']
H = np.fromfile(os.path.join(AQUI, 'terreno', 'h-18.f32'), dtype=np.float32).reshape(G, G)
KM = float(P['terreno'].split(',')[1].split('km')[0])
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
POLVO = 30 + (s * 9.1) % 30; NOCHE = 260 + (s * 4.3) % 30
FONDO = oklch(.12, .02, NOCHE); TXT = oklch(.9, .03, POLVO); TENUE = oklch(.55, .03, POLVO)
FAMC = {'complejo': oklch(.8, .15, POLVO), 'mediano': oklch(.78, .12, POLVO + 60), 'chico': oklch(.75, .1, POLVO + 140), 'diminuto': oklch(.72, .08, NOCHE), 'grande': oklch(.9, .16, POLVO - 20)}
def secciones(d, x0, Wd, y0, y1):
    for e in P['secciones']: xa = x0 + int(e['t'] / DUR * Wd); d.line([xa, y0, xa, y1], fill=oklch(.35, .03, NOCHE)); d.text((xa + 4, y0 + 2), e['num'], font=fn(12), fill=TENUE)
def campo(lado, luz=None, gran=True, numeros=False):
    lv = (H * 22).astype(int); borde = (np.abs(np.diff(lv, axis=0, prepend=lv[:1])) + np.abs(np.diff(lv, axis=1, prepend=lv[:, :1]))) > 0
    b0, b1 = np.array(oklch(.15, .02, NOCHE)), np.array(oklch(.5, .04, POLVO)); img = b0 + H[..., None] * (b1 - b0); img[borde] = oklch(.62, .04, POLVO)
    im = Image.fromarray(img.astype(np.uint8)).resize((lado, lado), Image.BILINEAR); d = ImageDraw.Draw(im)
    for k, tb in TB.items():
        if k == 'grande' and not gran: continue
        r = tb['D'] / (KM * 1000) / 2 * lado; x, y = tb['u'] * lado, tb['v'] * lado; col = FAMC[tb['familia']]
        on = luz is not None and luz.get(k, 0) > 0
        if on: d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(c * (.3 + .7 * min(1, luz[k]))) for c in col))
        d.ellipse([x - r, y - r, x + r, y + r], outline=col, width=3 if on else 1)
        if numeros and k != 'grande': d.text((x - 6, y - 6), k, font=fn(10), fill=col)
        if gran and k in GR['borrados']: d.line([x - r, y - r, x + r, y + r], fill=FAMC['grande'], width=1)
    return im

# 01 · el campo
im = Image.new('RGB', (W, 700), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), f"01  {P['terreno']}: cada cráter, un tambor. Color: familia; número: orden de llegada (0 el más viejo). El círculo grande: el gran impacto de IV;", font=fn(15), fill=TXT)
d.text((14, 32), f"    los cráteres que caen en su tazón (tachados) se callan para siempre: {len(GR['borrados'])} de 41", font=fn(13), fill=TXT)
im.paste(campo(620, numeros=True), (20, 56))
y = 70
for f, col in FAMC.items():
    ks = P['familias'].get(f, ['grande'] if f == 'grande' else [])
    fs = [TB[k]['f'] for k in ks]; d.text((680, y), f"{f:9} {len(ks):2} tambores · {min(fs):.0f}–{max(fs):.0f} Hz", font=fn(16), fill=col); y += 34
guardar(im, f'01-campo-de-impactos-s{s}-{h}.png')

# 02 · cada cráter es un tambor
im = Image.new('RGB', (W, 560), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), f"02  una membrana circular: f₀₁ = K / D (K = {P['K']:.0f} m·Hz: el cráter de 1.8 km da 45 Hz, la tónica) y los modos de Bessel j_mn / j_01", font=fn(15), fill=TXT)
Ds = np.array([TB[k]['D'] for k in TB]); xs = lambda D: 60 + (math.log(D) - math.log(200)) / (math.log(2600) - math.log(200)) * 760; ys = lambda f: 520 - (math.log(f) - math.log(25)) / (math.log(420) - math.log(25)) * 440
d.line([(xs(D), ys(P['K'] / D)) for D in np.geomspace(200, 2600, 60)], fill=TENUE, width=1)
for k, tb in TB.items(): x, y = xs(tb['D']), ys(tb['f']); d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=FAMC[tb['familia']])
d.text((60, 530), 'diámetro (m, log) →', font=fn(12), fill=TENUE); d.text((10, 60), 'Hz', font=fn(12), fill=TENUE)
RAT = [1, 1.594, 2.136, 2.296, 2.653, 2.918, 3.156, 3.501, 3.599, 3.648, 4.059, 4.132]; MM = [0, 1, 2, 0, 3, 1, 4, 2, 0, 5, 3, 6]
for i, (r, m) in enumerate(zip(RAT, MM)):
    x = 900 + (r - 1) / 3.2 * 740; col = oklch(.8, .13, POLVO + 40 * m); d.line([x, 460, x, 460 - 300 / (1 + .5 * i)], fill=col, width=4); d.text((x - 10, 470 + 14 * (i % 2)), f'{r:.2f}', font=fn(11), fill=col)
d.text((900, 60), 'los modos de una membrana (color = m: los m = 0 son los que despierta un golpe al centro;\nel cráter complejo, con pico central, sube esos modos ×1.12 y suma tres de sus terrazas)', font=fn(12), fill=TXT, spacing=4)
guardar(im, f'02-cada-crater-un-tambor-s{s}-{h}.png')

# 03 · la lluvia
a, b = P['secciones'][0]['t'], P['secciones'][0]['t1']
im = Image.new('RGB', (W, 420), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '03  la lluvia (I): los 41 cráteres caen en el orden en que el motor los estampó, cada vez más seguido (Poisson que se acelera). Alto: diámetro', font=fn(15), fill=TXT)
for k, t in P['caida'].items():
    tb = TB[k]; x = 60 + (t - a) / (b - a) * (W - 100); hh = tb['D'] / 2000 * 320; d.line([x, 400, x, 400 - hh], fill=FAMC[tb['familia']], width=3); d.text((x - 6, 380 - hh), k, font=fn(10), fill=FAMC[tb['familia']])
guardar(im, f'03-la-lluvia-s{s}-{h}.png')

# 04 · el footwork: dos compases
t0 = P['secciones'][1]['t'] + 24 * P['compas']; t1 = t0 + 2 * P['compas']
im = Image.new('RGB', (W, 560), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '04  el footwork (II, compases 25–26, 160 bpm): cada fila es un cráter, ordenados por tamaño; los complejos hacen de bombo (3-3-2), los medianos de toms,', font=fn(15), fill=TXT)
d.text((14, 32), '    los chicos de fantasmas, los diminutos de hats, rotando por el campo (su lugar en x es su lugar en el estéreo)', font=fn(13), fill=TXT)
orden = sorted([k for k in TB if k != 'grande'], key=lambda k: -TB[k]['D'])
for i, k in enumerate(orden): d.text((10, 62 + i * 11.5), k.rjust(2), font=fn(9), fill=FAMC[TB[k]['familia']])
for q in range(33): x = 60 + q / 32 * (W - 100); d.line([x, 58, x, 540], fill=oklch(.25 if q % 4 else .4, .02, NOCHE))
for f in ('complejo', 'mediano', 'chico', 'diminuto'):
    for g in P['golpes'][f]:
        if t0 <= g['t'] < t1:
            i = orden.index(g['id']); x = 60 + (g['t'] - t0) / (t1 - t0) * (W - 100); y = 62 + i * 11.5; r = 2 + 5 * g['v']
            d.ellipse([x - r, y + 5 - r, x + r, y + 5 + r], fill=FAMC[f])
guardar(im, f'04-footwork-s{s}-{h}.png')

def espectro(x, alto, fmin=20, fmax=8000, hop=1024, Nf=4096):
    win = np.hanning(Nf); fr = [np.abs(np.fft.rfft(x[i:i + Nf] * win)) for i in range(0, len(x) - Nf, hop)]
    Sx = 20 * np.log10(np.array(fr).T + 1e-9); f = np.fft.rfftfreq(Nf, 1 / SR); filas = np.geomspace(fmin, fmax, alto)[::-1]
    img = Sx[np.searchsorted(f, filas)]; return np.clip((img - (img.max() - 65)) / 65, 0, 1)
def pinta(img, col): F = np.array(FONDO); return (np.power(img[..., None], 1.3) * np.array(col) + F * (1 - img[..., None])).astype(np.uint8)
sr, mz = wavfile.read(os.path.join(OUT, os.path.basename(OUT) + '.wav')); mz = mz.astype(float).mean(1) / 32768

# 05 · el gran impacto
tg = GR['t']; seg = mz[int((tg - 6) * SR):int((tg + 8) * SR)]
im = Image.new('RGB', (W, 640), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), f"05  el gran impacto (IV, {tg:.1f} s): un cráter nuevo de {GR['D'] / 1000:.1f} km ({TB['grande']['f']:.1f} Hz) con su onda de choque; un compás de silencio y el footwork vuelve sin los {len(GR['borrados'])} que borró", font=fn(15), fill=TXT)
im.paste(campo(300, gran=False), (20, 60)); im.paste(campo(300, gran=True), (340, 60)); d.text((20, 365), 'antes', font=fn(13), fill=TXT); d.text((340, 365), 'después', font=fn(13), fill=TXT)
im.paste(Image.fromarray(pinta(espectro(seg, 240, hop=512), oklch(.88, .1, POLVO))).resize((W - 700, 300)), (680, 60)); d.text((680, 365), 'la mezcla, 6 s antes a 8 s después (20 Hz–8 kHz)', font=fn(13), fill=TXT)
guardar(im, f'05-gran-impacto-s{s}-{h}.png')

# 06 · quién toca
filas = [(f, [(g['t'], .1, TB[g['id']]['f']) for g in P['golpes'][f]]) for f in ('complejo', 'mediano', 'chico', 'diminuto', 'grande')]
filas += [('footwork 808', [(e['t'], .1, 0) for e in P['web']['bateria']]), ('sub', [(e['t'], e['dur'], e['midi']) for e in P['sub']]), ('kiai', [(e['t'], e['dur'], e['nota']) for e in P['garganta']]),
          ('sonda', [(e['t'], e['dur'], e['midi']) for e in P['sonda']])] + [(c['capa'], [(e['t'], e['dur'], e['nota']) for e in c['eventos']]) for c in P['sabina']]
im = Image.new('RGB', (W, 60 + 42 * len(filas)), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '06  quién toca: los cráteres por familia (alto = su altura), el footwork, el kiai, la sonda y las voces', font=fn(15), fill=TXT)
for k, (nom, ns) in enumerate(filas):
    col = FAMC.get(nom, oklch(.75, .1, POLVO + 25 * k)); y0 = 44 + k * 42; d.text((10, y0 + 12), nom, font=fn(12), fill=col)
    if not ns: continue
    lo, hi = min(n[2] for n in ns), max(n[2] for n in ns) + 1e-6
    for t, du, m in ns: x = 170 + t / DUR * (W - 190); x2 = 170 + (t + du) / DUR * (W - 190); y = y0 + 34 - (m - lo) / (hi - lo + 1e-9) * 30; d.rectangle([x, y - 1, max(x + 1, x2), y + 1], fill=col)
secciones(d, 170, W - 190, 36, im.height - 4); guardar(im, f'06-voces-s{s}-{h}.png')
if B is not None: sys.exit()

# 07 · capas solas
def leer(c, st): x = np.fromfile(os.path.join(RUN, c + '.f32'), dtype=np.float32).astype(float); return x.reshape(-1, 2).mean(1) if st else x
capas = [('crater-' + f, True) for f in ('complejo', 'mediano', 'chico', 'diminuto', 'grande')] + [('bateria', True), ('bateria-frito', True), ('garganta', False), ('viento', True), ('sonda', True)]
capas += [('sabina-' + c, True) for c in ('susurro', 'chops', 'coro', 'viva')]
alto = 34; x0 = 170; im = Image.new('RGB', (W, 50 + (alto + 4) * len(capas)), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '07  las capas solas antes de mezclar (20 Hz–8 kHz) — el polvo, el sub y los vocoders (Python) se ven en la 08', font=fn(14), fill=TXT)
for k, (c, st) in enumerate(capas):
    col = oklch(.78, .11, POLVO + 22 * k); y0 = 44 + k * (alto + 4); im.paste(Image.fromarray(pinta(espectro(leer(c, st), alto, hop=4096), col)).resize((W - x0 - 10, alto)), (x0, y0)); d.text((8, y0 + 10), c, font=fn(11), fill=col)
secciones(d, x0, W - x0 - 10, 36, im.height - 4); guardar(im, f'07-capas-s{s}-{h}.png')

# 08 · mezcla
mez = Image.new('RGB', (W, 400), FONDO); mez.paste(Image.fromarray(pinta(espectro(mz, 330, fmax=12000), oklch(.92, .04, POLVO))).resize((W - 20, 330)), (10, 50)); d = ImageDraw.Draw(mez)
d.text((14, 10), f'08  La lluvia que hizo los cráteres (s{s}): la mezcla, {len(mz) / sr:.0f} s', font=fn(18), fill=TXT); secciones(d, 10, W - 20, 44, 385)
guardar(mez, f'08-mezcla-s{s}-{h}.png')

# GIF: los cráteres se encienden cuando suenan
todos = [g for f in P['golpes'] for g in P['golpes'][f]]
cuadros = []; NC = 36
for j in range(1, NC + 1):
    t = DUR * j / NC; luz = {}
    for g in todos:
        if t - 1.2 < g['t'] <= t: luz[g['id']] = max(luz.get(g['id'], 0), g['v'] * (1 - (t - g['t']) / 1.2))
    c = Image.new('RGB', (W, 800), FONDO); dd = ImageDraw.Draw(c); c.paste(campo(380, luz, gran=t >= GR['t']), (20, 10))
    sec = [e for e in P['secciones'] if e['t'] <= t][-1]['num']; nom = {'I': 'LA LLUVIA', 'II': 'FOOTWORK', 'III': 'TAIKO', 'IV': 'EL GRAN IMPACTO', 'V': 'LA AGUJA'}[sec]
    dd.text((430, 30), f'{sec}  {nom}', font=fn(28), fill=TXT); dd.text((430, 80), f'{len(luz)} cráteres sonando · {t:5.1f} s', font=fn(18), fill=FAMC['mediano'])
    c.paste(mez, (0, 400)); xx = 10 + int((W - 20) * j / NC); dd.rectangle([xx, 450, W - 10, 780], fill=FONDO); dd.line([xx, 450, xx, 780], fill=TXT, width=2)
    cuadros.append(c.resize((1100, 518)))
gif = os.path.join(OUT, f'la-lluvia-que-hizo-los-crateres-s{s}-{h}.gif'); cuadros[0].save(gif, save_all=True, append_images=cuadros[1:] + [cuadros[-1]] * 2, duration=260, loop=0, optimize=True)
cuadros[-1].save(nuevo(f'09-campo-y-mezcla-s{s}-{h}.png'))
print(gif, os.path.getsize(gif) // 1024, 'KB')
