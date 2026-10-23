"""Primero sueño en el cenote — PNGs de etapas y GIF del proceso.
    python proceso.py <carpeta-de-render> <carpeta-de-entrega> [--b 03,04]
01 el karst 43 y sus cámaras (las dolinas leídas del mapa, los cenotes) · 02 cada cámara: su Helmholtz, su bóveda y su gotero ·
03 los goteros se encarrilan: libres, pegados a la rejilla del garage, sueltos, parados uno por uno · 04 la linterna mágica: la imagen
pintada y lo que suena · 05 los metrónomos de cuerda · 06 quién toca (las voces en capas) · 07 las capas solas · 08 la mezcla ·
GIF: las cámaras se encienden cuando gotean. Colores OKLCh sembrados (s43): la caliza y el agua de noche.
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
DUR = P['duracion']; SR = 48000; W = 1700; G = 360; CI = P['camaras_info']
H = np.fromfile(os.path.join(AQUI, 'terreno', 'h-43.f32'), dtype=np.float32).reshape(G, G)
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
CAL = 80 + (s * 5.3) % 30; AGUA = 200 + (s * 2.9) % 40
FONDO = oklch(.11, .02, AGUA + 40); TXT = oklch(.9, .03, CAL); TENUE = oklch(.55, .03, CAL)
def tinta(k, n, L=.75): return oklch(L, .12, AGUA + (CAL + 360 - AGUA) * k / max(1, n - 1))
NOM = {'I': 'PIRAMIDAL, FUNESTA', 'II': 'EL SUEÑO', 'III': 'EL ALMA VUELA', 'IV': 'LA CAÍDA', 'V': 'Y YO DESPIERTA'}
def secciones(d, x0, Wd, y0, y1):
    for e in P['secciones']: xa = x0 + int(e['t'] / DUR * Wd); d.line([xa, y0, xa, y1], fill=oklch(.35, .03, AGUA)); d.text((xa + 4, y0 + 2), e['num'] + ' ' + NOM[e['num']][:18], font=fn(11), fill=TENUE)
def karst(lado, luz=None):
    lv = (H * 22).astype(int); borde = (np.abs(np.diff(lv, axis=0, prepend=lv[:1])) + np.abs(np.diff(lv, axis=1, prepend=lv[:, :1]))) > 0
    b0, b1 = np.array(oklch(.15, .02, AGUA)), np.array(oklch(.6, .04, CAL)); img = b0 + H[..., None] * (b1 - b0); img[borde] = oklch(.7, .04, CAL)
    im = Image.fromarray(img.astype(np.uint8)).resize((lado, lado), Image.BILINEAR); d = ImageDraw.Draw(im)
    for c in CI:
        r = max(2, c['radio_m'] / (9500) * lado); x, y = c['u'] * lado, c['v'] * lado; col = oklch(.85, .14, AGUA) if c['cenote'] else tinta(int(c['id']) % 12, 12, .75)
        on = luz is not None and luz.get(c['id'], 0) > 0
        if on: d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(q * (.3 + .7 * min(1, luz[c['id']]))) for q in col))
        d.ellipse([x - r, y - r, x + r, y + r], outline=col, width=2 if on else 1)
    return im

# 01 · el karst y sus cámaras
im = Image.new('RGB', (W, 700), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), f"01  {P['terreno']}: las dolinas leídas del mapa (alto suavizado − alto); cada una, una cámara con un gotero. En azul claro, los tres cenotes", font=fn(15), fill=TXT)
im.paste(karst(620), (20, 50))
y = 60
for c in CI[:16]:
    d.text((680, y), f"cámara {c['id']:>2}  Ø {2 * c['radio_m']:5} m  hondo {c['prof_m']:5.1f} m  Helmholtz {c['fh_real']:.4f} Hz → {c['fh']:.1f} Hz  bóveda {c['fb']:.0f} Hz" + ('  CENOTE' if c['cenote'] else ''), font=fn(13), fill=oklch(.85, .14, AGUA) if c['cenote'] else TXT); y += 30
d.text((680, y + 10), f"… y {len(CI) - 16} más. La tónica: la cámara más grande ({CI[0]['fh']:.1f} Hz)", font=fn(13), fill=TENUE)
guardar(im, f'01-karst-y-camaras-s{s}-{h}.png')

# 02 · los goteros se encarrilan
im = Image.new('RGB', (W, 620), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '02  los goteros: una fila por cámara (arriba las grandes, que gotean lento). I: todos empiezan juntos (el Ligeti de agua). II: se pegan a la rejilla del garage', font=fn(15), fill=TXT)
d.text((14, 32), '    (las gotas se alinean en columnas). III: se sueltan. IV: se paran uno por uno. V: queda la cámara grande', font=fn(13), fill=TXT)
nC = len(CI)
for g in P['gotas']:
    x = 60 + g['t'] / DUR * (W - 80); yy = 60 + int(g['id']) * (520 / nC); d.line([x, yy, x, yy + max(2, 520 / nC - 2)], fill=tinta(int(g['id']) % 12, 12, .5 + .4 * g['v']))
secciones(d, 60, W - 80, 52, 590); guardar(im, f'02-goteros-se-encarrilan-s{s}-{h}.png')

# 03 · los goteros de cerca: II, dos compases (antes y después de encarrilarse)
im = Image.new('RGB', (W, 520), FONDO); d = ImageDraw.Draw(im); a2 = P['secciones'][1]['t']; BAR = P['compas']
d.text((14, 10), '03  de cerca: dos compases al entrar el garage (izquierda) y dos compases ya encarrilados (derecha); las rayas grises son los octavos del garage', font=fn(15), fill=TXT)
for j, (t0, x0) in enumerate(((a2 + 1 * BAR, 40), (a2 + 12 * BAR, 870))):
    for q in range(17): xx = x0 + q / 16 * 790; d.line([xx, 50, xx, 500], fill=oklch(.3, .02, AGUA))
    for g in P['gotas']:
        if t0 <= g['t'] < t0 + 2 * BAR: xx = x0 + (g['t'] - t0) / (2 * BAR) * 790; yy = 50 + int(g['id']) * (440 / nC); d.ellipse([xx - 3, yy - 3, xx + 3, yy + 3], fill=tinta(int(g['id']) % 12, 12, .8))
guardar(im, f'03-goteros-de-cerca-s{s}-{h}.png')

def espectro(x, alto, fmin=40, fmax=8000, hop=1024, Nf=4096):
    win = np.hanning(Nf); fr = [np.abs(np.fft.rfft(x[i:i + Nf] * win)) for i in range(0, len(x) - Nf, hop)]
    Sx = 20 * np.log10(np.array(fr).T + 1e-9); f = np.fft.rfftfreq(Nf, 1 / SR); filas = np.geomspace(fmin, fmax, alto)[::-1]
    img = Sx[np.searchsorted(f, filas)]; return np.clip((img - (img.max() - 60)) / 60, 0, 1)
def pinta(img, col): F = np.array(FONDO); return (np.power(img[..., None], 1.3) * np.array(col) + F * (1 - img[..., None])).astype(np.uint8)
def leer(c, st): x = np.fromfile(os.path.join(RUN, c + '.f32'), dtype=np.float32).astype(float); return x.reshape(-1, 2).mean(1) if st else x

# 04 · la linterna
img = np.load(os.path.join(RUN, 'linterna-imagen.npy')); lin = leer('linterna', True)
im = Image.new('RGB', (W, 640), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '04  la linterna mágica (un ANS: la imagen se lee como espectro). Arriba, la placa pintada (tiempo × 120 bandas de 55 Hz a 7 kHz): la pirámide de sombra que sube con', font=fn(15), fill=TXT)
d.text((14, 32), '    el tema A en su filo, las estrellas, el vuelo del alma, la caída y el amanecer que lo llena todo. Abajo, lo que suena', font=fn(13), fill=TXT)
placa = (np.clip(img.T[::-1], 0, 1) * 255).astype(np.uint8); col = np.array(oklch(.9, .1, CAL))
im.paste(Image.fromarray((placa[..., None] / 255 * col + np.array(FONDO) * (1 - placa[..., None] / 255)).astype(np.uint8)).resize((W - 80, 260)), (60, 60))
im.paste(Image.fromarray(pinta(espectro(lin, 260, 50, 7500, hop=2048), oklch(.85, .1, AGUA))).resize((W - 80, 260)), (60, 340)); secciones(d, 60, W - 80, 330, 610)
guardar(im, f'04-linterna-magica-s{s}-{h}.png')

# 05 · los metrónomos
gol = json.load(open(os.path.join(RUN, 'metronomos-golpes.json')))
im = Image.new('RGB', (W, 470), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '05  los doce metrónomos de cuerda (Ligeti): se dan cuerda en I uno tras otro, cada uno a su razón del tempo del garage (1, 3/4, 2/3, 5/4…); en IV se les acaba', font=fn(15), fill=TXT)
d.text((14, 32), '    la cuerda, se frenan y se paran uno por uno', font=fn(13), fill=TXT)
for m in P['metronomos']:
    yy = 70 + m['id'] * 30; d.text((10, yy), f"{m['bpm']:.0f}", font=fn(11), fill=tinta(m['id'], 12))
    for t, i in gol:
        if i == m['id']: xx = 60 + t / DUR * (W - 80); d.line([xx, yy, xx, yy + 20], fill=tinta(m['id'], 12))
secciones(d, 60, W - 80, 60, 440); guardar(im, f'05-metronomos-s{s}-{h}.png')

# 06 · quién toca
filas = [(c['capa'], [(e['t'], e['dur'], e['nota']) for e in c['eventos']]) for c in P['sabina']] + [('katajjaq', [(e['t'], e['dur'], e['nota'] + 5 * e['lado']) for e in P['garganta']]),
         ('bordón', [(e['t'], e['dur'], e['nota']) for e in P['bordon']]), ('boca (el alma)', [(n['t'], n['dur'], n['midi']) for n in P['tres_tiempos']['boca']['notas']]),
         ('garage', [(e['t'], .1, 0) for e in P['web']['bateria']]), ('sub (tema A)', [(e['t'], e['dur'], e['midi']) for e in P['sub']]), ('gotas', [(g['t'], .05, -int(g['id'])) for g in P['gotas'][::3]])]
im = Image.new('RGB', (W, 60 + 44 * len(filas)), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '06  quién toca: las voces en capas (los versos, el coro, los chops, las vocales que modulan a la cueva, el katajjaq, el bordón, el alma), el garage y las gotas', font=fn(15), fill=TXT)
for k, (nom, ns) in enumerate(filas):
    col = tinta(k, len(filas), .78); y0 = 44 + k * 44; d.text((10, y0 + 12), nom, font=fn(12), fill=col)
    if not ns: continue
    lo, hi = min(n[2] for n in ns), max(n[2] for n in ns) + 1e-6
    for t, du, m in ns: x = 170 + t / DUR * (W - 190); x2 = 170 + (t + du) / DUR * (W - 190); y = y0 + 36 - (m - lo) / (hi - lo + 1e-9) * 32; d.rectangle([x, y - 1, max(x + 1, x2), y + 1], fill=col)
secciones(d, 170, W - 190, 36, im.height - 4); guardar(im, f'06-voces-s{s}-{h}.png')
if B is not None: sys.exit()

# 07 · capas solas
capas = [(c, True) for c in ('cueva', 'metronomos', 'linterna', 'vinilo', 'organo', 'boca', 'sala', 'bateria', 'bateria-frito')] + [(c, False) for c in ('katajjaq0', 'katajjaq1', 'bordon', 'aves')] + [('sabina-' + c, True) for c in ('lead', 'coro', 'chops', 'vocales')]
alto = 30; x0 = 170; im = Image.new('RGB', (W, 50 + (alto + 4) * len(capas)), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '07  las capas solas antes de mezclar (40 Hz–8 kHz) — el sub y los vocoders (Python) se ven en la 08', font=fn(14), fill=TXT)
for k, (c, st) in enumerate(capas):
    col = tinta(k, len(capas)); y0 = 44 + k * (alto + 4); im.paste(Image.fromarray(pinta(espectro(leer(c, st), alto, hop=4096), col)).resize((W - x0 - 10, alto)), (x0, y0)); d.text((8, y0 + 8), c, font=fn(11), fill=col)
secciones(d, x0, W - x0 - 10, 36, im.height - 4); guardar(im, f'07-capas-s{s}-{h}.png')

# 08 · mezcla
sr, x = wavfile.read(os.path.join(OUT, os.path.basename(OUT) + '.wav')); x = x.astype(float).mean(1) / 32768
mez = Image.new('RGB', (W, 400), FONDO); mez.paste(Image.fromarray(pinta(espectro(x, 330, 30, 12000), oklch(.92, .04, CAL))).resize((W - 20, 330)), (10, 50)); d = ImageDraw.Draw(mez)
d.text((14, 10), f'08  Primero sueño en el cenote (s{s}): la mezcla, {len(x) / sr:.0f} s', font=fn(18), fill=TXT); secciones(d, 10, W - 20, 44, 385)
guardar(mez, f'08-mezcla-s{s}-{h}.png')

# GIF: las cámaras se encienden cuando gotean
cuadros = []; NC = 36; gotas = P['gotas']
for j in range(1, NC + 1):
    t = DUR * j / NC; luz = {}
    for g in gotas:
        if t - 1.5 < g['t'] <= t: luz[g['id']] = max(luz.get(g['id'], 0), g['v'] * (1 - (t - g['t']) / 1.5))
    c = Image.new('RGB', (W, 800), FONDO); dd = ImageDraw.Draw(c); c.paste(karst(380, luz), (20, 10))
    sec = [e for e in P['secciones'] if e['t'] <= t][-1]['num']
    dd.text((430, 30), f'{sec}  {NOM[sec]}', font=fn(28), fill=TXT); dd.text((430, 80), f'{len(luz)} cámaras goteando · {t:5.1f} s', font=fn(18), fill=oklch(.85, .12, AGUA))
    c.paste(mez, (0, 400)); xx = 10 + int((W - 20) * j / NC); dd.rectangle([xx, 450, W - 10, 780], fill=FONDO); dd.line([xx, 450, xx, 780], fill=TXT, width=2)
    cuadros.append(c.resize((1100, 518)))
gif = os.path.join(OUT, f'primero-sueno-en-el-cenote-s{s}-{h}.gif'); cuadros[0].save(gif, save_all=True, append_images=cuadros[1:] + [cuadros[-1]] * 2, duration=260, loop=0, optimize=True)
cuadros[-1].save(nuevo(f'09-karst-y-mezcla-s{s}-{h}.png'))
print(gif, os.path.getsize(gif) // 1024, 'KB')
