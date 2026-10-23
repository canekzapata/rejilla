"""Lo que tapa la traspuesta — PNGs de etapas y GIF del proceso.
    python proceso.py <carpeta-de-render> <carpeta-de-entrega>
01 el terreno 420048 y su retícula (curvas cada 250 m → periodo 11; las cumbres de las siluetas → grados {0 5 9 10}) ·
02 la forma (los tres aspectos del ritornelo) · 03 la garganta de montaña (el perfil y las vocales como tubos) · 04 el viento
(crestas que lee y su espectrograma, liso → estriado) · 05 el coro y los solos (rollo) · 06 las capas solas · 07 la mezcla con
las tijeras de Nobuto · GIF: la pluma camina la cordillera fila por fila mientras suena la mezcla.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI)
RUN, OUT = sys.argv[1], sys.argv[2]; P = json.load(open(os.path.join(OUT, 'partitura.json'), encoding='utf-8'))
h = os.path.basename(OUT).rsplit('-', 1)[1]; s = P['semilla']; pr = os.path.join(OUT, 'proceso'); os.makedirs(pr, exist_ok=False)
DUR = P['duracion']; SR = 48000; FONDO = (9, 10, 14); TXT = (236, 230, 216); W = 1700
H = np.fromfile(os.path.join(AQUI, 'terreno', 'h-420048.f32'), np.float32).reshape(360, 360)
fn = lambda n: ImageFont.truetype('C:/Windows/Fonts/consola.ttf', n)
def nuevo(nombre): p = os.path.join(pr, nombre); assert not os.path.exists(p); return p
def neon(k, n, l=.62):                                     # el tono gira por la semilla; croma alto (las láminas oscuras de Traspuesta)
    a = 2 * math.pi * k / max(1, n) + s % 97 * .07; return tuple(int(255 * min(1, max(0, l + .38 * math.sin(a + d)))) for d in (0, 2.1, 4.2))
SECS = P['secciones']; NOM = dict(I='I punto gris', II='II casa', III='III coro', IV='IV abrir', V='V liso', VI='VI coda')
def secciones(d, x0, Wd, y0, y1):
    for k, (a, z) in SECS.items(): xa = x0 + int(a / DUR * Wd); d.line([xa, y0, xa, y1], fill=(60, 62, 80)); d.text((xa + 4, y0 + 2), NOM[k], font=fn(13), fill=(175, 175, 190))

# 01 · terreno y retícula
im = Image.new('RGB', (W, 760), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), f"01  el terreno 420048 (cordillera, {2750} m de relieve): curvas cada 250 m = {P['periodo']} escalones → la escala se repite cada {P['periodo']} semitonos", font=fn(17), fill=TXT)
lv = np.minimum(P['periodo'] - 1, (H * P['periodo']).astype(int)); img = np.zeros((360, 360, 3), np.uint8)
for k in range(P['periodo']): img[lv == k] = [int(c * (.25 + .5 * k / P['periodo'])) for c in neon(k, P['periodo'], .5)]
borde = (np.abs(np.diff(lv, axis=0, prepend=lv[:1])) + np.abs(np.diff(lv, axis=1, prepend=lv[:, :1]))) > 0; img[borde] = (240, 235, 220)
im.paste(Image.fromarray(img).resize((640, 640), Image.NEAREST), (20, 50))
for nombre, sil, y0 in (('silueta de frente (máximo de cada columna)', H.max(0), 70), ('silueta de lado (máximo de cada fila)', H.max(1), 330)):
    pts = [(690 + i * 2.6, y0 + 200 - v * 180) for i, v in enumerate(sil)]; d.line(pts, fill=neon(3, 6, .75), width=2); d.text((690, y0 - 16), nombre, font=fn(13), fill=TXT)
    for k in range(P['periodo'] + 1): yk = y0 + 200 - k / P['periodo'] * 180; d.line([690, yk, 690 + 936, yk], fill=(45, 45, 60))
    sm = np.convolve(sil, np.ones(5) / 5, 'same')
    for i in range(3, 357):
        if sm[i] > sm[i - 1] and sm[i] >= sm[i + 1] and sm[i] > sm[i - 3] and sm[i] >= sm[i + 3]:
            x, y = 690 + i * 2.6, y0 + 200 - sm[i] * 180; d.ellipse([x - 5, y - 5, x + 5, y + 5], outline=neon(0, 6, .8), width=2); d.text((x + 6, y - 18), f'escalón {int(round(sm[i] * P["periodo"])) % P["periodo"]}', font=fn(11), fill=neon(0, 6, .8))
d.text((690, 600), f"grados = escalones de las cumbres: {P['grados']}   retícula: {P['reticula'][:16]}", font=fn(13), fill=TXT)
d.text((690, 622), f"cancioncilla = las cinco cumbres de lado, en orden: {P['cancioncilla']}", font=fn(13), fill=TXT)
im.save(nuevo(f'01-terreno-reticula-s{s}-{h}.png'))

# 02 · forma
im = Image.new('RGB', (W, 300), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '02  la forma es el ritornelo (Mil mesetas, 1837): el punto gris en el caos · la casa (el círculo) · abrir el círculo (improvisar)', font=fn(17), fill=TXT)
TXT2 = dict(I='Lachenmann: aire, madera, presión;\nla montaña respira; el niño canturrea', II='Weather Report: bajo sin trastes,\nsinte y sax al unísono; verso 1',
            III='hyperpop + tijeras de Nobuto:\n«cada curva es una cerca»', IV='solos: Siringua de tres gargantas,\nvocoder scat, cambios, pájaros', V='liso: la retícula se disuelve,\ntormenta; «mapa no, territorio»', VI='la cancioncilla sola\nen el viento')
for k, (a, z) in SECS.items():
    xa, xb = 20 + a / DUR * (W - 40), 20 + z / DUR * (W - 40); i = list(SECS).index(k)
    d.rectangle([xa, 60, xb - 2, 120], fill=tuple(int(c * .45) for c in neon(i, 6)), outline=neon(i, 6, .8)); d.text((xa + 6, 66), NOM[k], font=fn(15), fill=TXT)
    d.multiline_text((xa + 6, 140), TXT2[k], font=fn(12), fill=neon(i, 6, .8), spacing=4)
im.save(nuevo(f'02-forma-s{s}-{h}.png'))

# 03 · la garganta: el tubo del perfil y los tubos de las vocales
import subprocess
js = """const G=require('./motor/garganta.js');const N=24,o={};for(const v of 'aeiou')o[v]=Array.from(G.areaVocal(v,N,new Float64Array(N)));
const fs=require('fs'),H=new Float32Array(fs.readFileSync('terreno/h-420048.f32').buffer.slice(0));const p=new Float32Array(360);let mx=0;for(let i=0;i<360;i++){p[i]=H[180*360+i];mx=Math.max(mx,p[i]);}for(let i=0;i<360;i++)p[i]/=mx;
o.montana=Array.from(G.areaTerreno(p,N,new Float64Array(N)));o.montana2=Array.from(G.areaTerreno(p,48,new Float64Array(48)));process.stdout.write(JSON.stringify(o));"""
A = json.loads(subprocess.run(['node', '-e', js], cwd=AQUI, capture_output=True, text=True, check=True).stdout)
im = Image.new('RGB', (W, 520), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '03  la garganta de montaña: siringe de pájaro (van der Pol) → tubo de Kelly-Lochbaum con la forma del perfil del terreno; para hablar, el tubo se deforma hacia la vocal', font=fn(15), fill=TXT)
MED = dict(a='700/1225 (meta 700/1250)', e='450/1800 (450/1900)', i='300/2600 (300/2300)', o='500/950 (500/950)', u='325/800 (330/800)')
for k, nombre in enumerate(['montana', 'a', 'e', 'i', 'o', 'u']):
    x0 = 30 + k * 275; ar = A[nombre]; col = neon(k, 6, .75); n = len(ar)
    for j, a_ in enumerate(ar):
        r = math.sqrt(a_ / math.pi) * 34; xx = x0 + j * 230 / n; d.rectangle([xx, 270 - r, xx + 230 / n - 1, 270 + r], fill=tuple(int(c * .55) for c in col), outline=col)
    d.text((x0, 70), 'el perfil (fila 180)' if nombre == 'montana' else f'«{nombre}»', font=fn(16), fill=col)
    d.text((x0, 420), 'glotis → labios', font=fn(11), fill=(150, 150, 165)); d.text((x0, 440), 'formantes medidas:' if nombre != 'montana' else 'largo 2: un tubo de 34 cm', font=fn(11), fill=TXT)
    d.text((x0, 458), MED.get(nombre, 'las formantes bajan una octava'), font=fn(11), fill=TXT)
im.save(nuevo(f'03-garganta-s{s}-{h}.png'))

# 04 · el viento: el perfil que lee y su sonido (liso → estriado)
def espectro(x, alto, fmax=12000, hop=1024, fmin=40):
    N = 2048; win = np.hanning(N); fr = [np.abs(np.fft.rfft(x[i:i + N] * win)) for i in range(0, len(x) - N, hop)]
    Sx = 20 * np.log10(np.array(fr).T + 1e-9); f = np.fft.rfftfreq(N, 1 / SR); filas = np.geomspace(fmin, fmax, alto)[::-1]
    img = Sx[np.searchsorted(f, filas)]; return np.clip((img - (img.max() - 65)) / 65, 0, 1)
def pinta(img, col): return (np.power(img[..., None], 1.3) * np.array(col) + np.array(FONDO) * (1 - img[..., None])).astype(np.uint8)
vi = np.fromfile(os.path.join(RUN, 'viento.f32'), np.float32).astype(float).reshape(-1, 2).mean(1)
im = Image.new('RGB', (W, 420), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '04  el viento lee el terreno: cada cresta silba f = 0.2·v/d; liso (altura continua) en I, V y VI; estriado (la retícula de 11) en II–IV', font=fn(16), fill=TXT)
im.paste(Image.fromarray(pinta(espectro(vi, 330, 6000, 2048, 60), neon(2, 6, .8))).resize((W - 40, 330)), (20, 50)); secciones(d, 20, W - 40, 44, 385)
im.save(nuevo(f'04-viento-s{s}-{h}.png'))

# 05 · coro y solos (rollo)
im = Image.new('RGB', (W, 520), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '05  quién canta: coro (S pájaro+vocoder · A agua · T garganta · B sinte), solos (garganta, vocoder scat, sax), bajo sin trastes, sinte', font=fn(15), fill=TXT)
filas = [('coro S', [(e['t'], e['dur'], e['nota']) for C in P['coros'].values() for e in C['S']]), ('coro A (agua)', [(e['t'], e['dur'], e['nota']) for C in P['coros'].values() for e in C['A']]),
         ('coro T (garganta)', [(e['t'], e['dur'], e['nota']) for C in P['coros'].values() for e in C['T']]), ('solo garganta', [(e['t'], e['dur'], e['nota']) for e in P['garganta'] if e['voz'] == 'solo']),
         ('solo vocoder', [(e['t'], e['dur'], e['m']) for e in P['vocsolo']]), ('sax', [(e['t'], e['dur'], e['m']) for e in P['sax']]), ('sinte', [(e['t'], e['dur'], e['m']) for e in P['sinte']]),
         ('bajo', [(e['t'], e['dur'], e['m']) for e in P['bajo']]), ('cancioncilla', [(e['t'], e['dur'], e['nota']) for e in P['vozagua'] if e['t'] < SECS['II'][0] or e['t'] > SECS['VI'][0]])]
for k, (nombre, ns) in enumerate(filas):
    col = neon(k, len(filas), .72); d.text((10, 60 + k * 50), nombre, font=fn(12), fill=col)
    if not ns: continue
    lo, hi = min(n[2] for n in ns), max(n[2] for n in ns) + 1
    for t, du, m in ns: x = 170 + t / DUR * (W - 190); x2 = 170 + (t + du) / DUR * (W - 190); y = 60 + k * 50 + 40 - (m - lo) / (hi - lo) * 36; d.rectangle([x, y - 1, max(x + 1, x2), y + 1], fill=col)
secciones(d, 170, W - 190, 44, 510); im.save(nuevo(f'05-voces-s{s}-{h}.png'))

# 06 · capas solas
capas = [(c, True) for c in P['web'] if P['web'][c]] + [(c, False) for c in ['garganta-montana', 'garganta-coro', 'garganta-solo', 'sax', 'clarinete', 'chelo', 'piano', 'trombon', 'gong', 'aves', 'aves-coro', 'siringa', 'agua', 'vozagua']] + [('viento', True), ('sabina-soprano', True), ('sabina-scat', True)]
alto = 40; x0 = 160; im = Image.new('RGB', (W, 50 + (alto + 5) * len(capas)), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '06  las capas solas, antes de mezclar (40 Hz–12 kHz): navegador, instrumentos imposibles, objetos que cantan, Sabina', font=fn(16), fill=TXT)
for k, (c, st) in enumerate(capas):
    x = np.fromfile(os.path.join(RUN, c + '.f32'), dtype=np.float32).astype(float); x = x.reshape(-1, 2).mean(1) if st else x
    col = neon(k, len(capas), .7); y0 = 46 + k * (alto + 5); im.paste(Image.fromarray(pinta(espectro(x, alto, hop=2048), col)).resize((W - x0 - 10, alto)), (x0, y0)); d.text((8, y0 + 12), c, font=fn(12), fill=col)
secciones(d, x0, W - x0 - 10, 36, im.height - 4); im.save(nuevo(f'06-capas-s{s}-{h}.png'))

# 07 · la mezcla con las tijeras
sr, x = wavfile.read(os.path.join(OUT, os.path.basename(OUT) + '.wav')); x = x.astype(float).mean(1) / 32768
mez = Image.new('RGB', (W, 400), FONDO); mez.paste(Image.fromarray(pinta(espectro(x, 330), (236, 228, 214))).resize((W - 20, 330)), (10, 50)); d = ImageDraw.Draw(mez)
d.text((14, 10), f'07  Lo que tapa la traspuesta (s{s}): la mezcla, {len(x) / sr:.0f} s · en rojo, las tijeras de Nobuto (repite, al revés, sube, salta)', font=fn(16), fill=TXT); secciones(d, 10, W - 20, 44, 385)
for tj in P['tijeras']:
    xa = 10 + tj['t'] / DUR * (W - 20); xb = 10 + (tj['t'] + tj['dur']) / DUR * (W - 20); d.rectangle([xa, 382, max(xa + 2, xb), 392], fill=(240, 70, 90))
mez.save(nuevo(f'07-mezcla-s{s}-{h}.png'))

# GIF: arriba la cordillera fila por fila (la fila que suena en ese momento, en neón, sobre las ya recorridas), abajo la mezcla
cuadros = []; NC = 34
for j in range(1, NC + 1):
    t = DUR * j / NC; c = Image.new('RGB', (W, 760), FONDO); dd = ImageDraw.Draw(c)
    fila_t = max(p for p in P['perfiles'] if p[0] <= t)[1] if any(p[0] <= t for p in P['perfiles']) else P['perfiles'][0][1]
    for jj in range(30, fila_t + 1, 6):
        v = H[jj]; pts = [(40 + i * 4.5, 330 - (jj - 30) * .55 - v[i] * 160) for i in range(360)]; dd.line(pts, fill=(70, 72, 88) if jj < fila_t - 5 else neon(j, NC, .8), width=1 if jj < fila_t - 5 else 3)
    sec = next(k for k, (a, z) in SECS.items() if a <= t < z or k == 'VI'); dd.text((40, 20), f'{NOM[sec]}   ·   fila {fila_t} de la cordillera 420048', font=fn(20), fill=TXT)
    c.paste(mez, (0, 360)); xx = 10 + int((W - 20) * j / NC); dd.rectangle([xx, 410, W - 10, 740], fill=FONDO); dd.line([xx, 410, xx, 740], fill=TXT, width=2)
    cuadros.append(c.resize((1100, 492)))
gif = os.path.join(OUT, f'lo-que-tapa-la-traspuesta-s{s}-{h}.gif'); cuadros[0].save(gif, save_all=True, append_images=cuadros[1:] + [cuadros[-1]] * 2, duration=270, loop=0, optimize=True)
cuadros[-1].save(nuevo(f'08-cordillera-y-mezcla-s{s}-{h}.png'))
print(gif, os.path.getsize(gif) // 1024, 'KB')
