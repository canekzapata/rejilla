"""El río no tiene tronco — PNGs de etapas y GIF del proceso.
    python proceso.py <carpeta-de-render> <carpeta-de-entrega>
01 el delta y el monocordio (el mapa, el canal, los brazos, los afluentes; cada largo → su altura) · 02 el reloj de agua (cuándo nace
y se junta cada afluente, el ápice, cuándo llega cada brazo) · 03 la garganta de río (tronco con la forma del río y sus cinco bocas)
· 04 quién toca (rollo) · 05 el mar de Scelsi (las desviaciones que se cierran) · 06 las capas solas · 07 la mezcla · GIF: el frente
del agua avanza por el mapa mientras suena la mezcla.
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
AQUI = os.path.dirname(os.path.abspath(__file__))
RUN, OUT = sys.argv[1], sys.argv[2]; P = json.load(open(os.path.join(OUT, 'partitura.json'), encoding='utf-8'))
h = os.path.basename(OUT).rsplit('-', 1)[1]; s = P['semilla']; pr = os.path.join(OUT, 'proceso'); os.makedirs(pr, exist_ok=False)
DUR = P['duracion']; SR = 48000; FONDO = (8, 11, 16); TXT = (232, 232, 222); W = 1700; G = 360; TT = P['tiempos']; SECS = P['secciones']
Hm = np.fromfile(os.path.join(AQUI, 'terreno', 'h-412601.f32'), np.float32).reshape(G, G)
CANAL = json.load(open(os.path.join(AQUI, 'terreno', 'canal-412601.json'))); RED = json.load(open(os.path.join(AQUI, 'terreno', 'red-412601.json')))
fn = lambda n: ImageFont.truetype('C:/Windows/Fonts/consola.ttf', n)
def nuevo(nombre): p = os.path.join(pr, nombre); assert not os.path.exists(p); return p
def tinta(k, n, l=.62):
    a = 2 * math.pi * k / max(1, n) + s % 89 * .05; return tuple(int(255 * min(1, max(0, l + .36 * math.sin(a + d)))) for d in (0, 2.1, 4.2))
NOM = dict(I='I las fuentes', II='II el río', III='III el delta', IV='IV el mar')
def secciones(d, x0, Wd, y0, y1):
    for k, (a, z) in SECS.items(): xa = x0 + int(a / DUR * Wd); d.line([xa, y0, xa, y1], fill=(60, 64, 80)); d.text((xa + 4, y0 + 2), NOM[k], font=fn(13), fill=(175, 178, 190))
def mapa(lado, hasta_t=None):
    """el delta: tierra en grises por altura, el mar oscuro, el canal y los brazos; con hasta_t, sólo el agua que ya pasó"""
    img = np.zeros((G, G, 3)); mar = Hm <= 1e-4
    img[~mar] = (np.clip(Hm[~mar], 0, 1)[:, None] * np.array([90, 96, 84]) + 26)
    img[mar] = [12, 22, 40]; im = Image.fromarray(img.astype(np.uint8)).resize((lado, lado), Image.NEAREST); d = ImageDraw.Draw(im)
    X = lambda p: (p[0] * lado, p[1] * lado)
    rio = np.array(CANAL['rio'])[::-1]; n = len(rio)
    for a in P['afluentes']:
        Q = RED['orientados'][a['rio']]; frac = 1 if hasta_t is None else np.clip((hasta_t - a['t0']) / max(.1, a['t_conf'] - a['t0']), 0, 1)
        k = max(2, int(len(Q) * frac)); d.line([X(p) for p in Q[:k]], fill=(110, 190, 200), width=2) if frac > 0 else None
    k = n if hasta_t is None else int(np.clip((hasta_t - TT['lluvia']) / (TT['apice'] - TT['lluvia']), 0, 1) * n)
    if k > 1: d.line([X(p) for p in rio[:k]], fill=(150, 220, 235), width=4)
    for i, b in enumerate(CANAL['brazos']):
        frac = 1 if hasta_t is None else np.clip((hasta_t - TT['apice']) / (TT['llegan'][i] - TT['apice']), 0, 1); k = int(len(b) * frac)
        if k > 1: d.line([X(p) for p in b[:k]], fill=tinta(i, 5, .75), width=4)
    return im

# 01 · el delta y el monocordio
im = Image.new('RGB', (W, 760), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '01  el delta 412601: cada río es una cuerda y su largo le da su altura (f = f0·L_mayor/L) — los cinco brazos son un arpa', font=fn(17), fill=TXT)
im.paste(mapa(680), (20, 50))
x0 = 740; d.text((x0, 60), 'monocordio', font=fn(16), fill=TXT)
cuerdas = [('río (canal)', P['delta']['largo_rio'], P['f_rio'])] + [(f'brazo {i}', b['largo'], P['f_brazos'][i]) for i, b in enumerate(P['delta']['brazos'])]
Lm = max(c[1] for c in cuerdas)
for k, (nom, L, f) in enumerate(cuerdas):
    y = 110 + k * 70; col = (150, 220, 235) if k == 0 else tinta(k - 1, 5, .75); d.line([x0, y, x0 + int(900 * L / Lm), y], fill=col, width=4)
    d.text((x0, y + 8), f'{nom}: largo {L:.3f} → {f:.1f} Hz  ({69 + 12 * math.log2(f / 440):.2f} midi)', font=fn(13), fill=col)
d.text((x0, 560), f"f0 = {P['f0']:.0f} Hz (el brazo más largo) · el río es una cuerda de {P['f_rio']:.2f} Hz: su melodía son sus armónicos 18 → 4", font=fn(13), fill=TXT)
d.text((x0, 585), f"{len(P['afluentes'])} afluentes (en azul): cada uno, una cuerda corta con su ostinato", font=fn(13), fill=(110, 190, 200))
im.save(nuevo(f'01-delta-monocordio-s{s}-{h}.png'))

# 02 · el reloj de agua
im = Image.new('RGB', (W, 420), FONDO); d = ImageDraw.Draw(im); X = lambda t: 20 + t / DUR * (W - 40)
d.text((14, 10), '02  un solo reloj de agua: el tiempo es la distancia a lo largo del agua (los afluentes nacen y se juntan; en el delta el agua se frena 2.5×)', font=fn(16), fill=TXT)
for k, a in enumerate(P['afluentes']):
    y = 60 + k * 14; d.line([X(a['t0']), y, X(a['t_conf']), y], fill=(110, 190, 200), width=3); d.ellipse([X(a['t_conf']) - 4, y - 4, X(a['t_conf']) + 4, y + 4], fill=(150, 220, 235))
y = 60 + len(P['afluentes']) * 14 + 16; d.line([X(TT['lluvia']), y, X(TT['apice']), y], fill=(150, 220, 235), width=6); d.text((X(TT['lluvia']), y + 6), 'el canal', font=fn(12), fill=TXT)
for i, t1 in enumerate(TT['llegan']):
    yy = y + 30 + i * 18; d.line([X(TT['apice']), yy, X(t1), yy], fill=tinta(i, 5, .75), width=5); d.line([X(t1), yy, X(TT['fin']), yy], fill=tuple(int(c * .45) for c in tinta(i, 5, .75)), width=5)
    d.text((X(t1) + 6, yy - 7), f'brazo {i} llega al mar', font=fn(11), fill=tinta(i, 5, .75))
secciones(d, 20, W - 40, 40, 410); im.save(nuevo(f'02-reloj-de-agua-s{s}-{h}.png'))

# 03 · la garganta de río
js = """const G=require('./motor/garganta_rio.js'),D=JSON.parse(require('fs').readFileSync('terreno/delta.json'));const o={};
o.tronco=Array.from(G.areaTerreno(Float32Array.from(D.perfil_rio),24,new Float64Array(24)));for(const v of 'aou')o[v]=Array.from(G.areaVocal(v,24,new Float64Array(24)));process.stdout.write(JSON.stringify(o));"""
A = json.loads(subprocess.run(['node', '-e', js], cwd=AQUI, capture_output=True, text=True, check=True).stdout)
im = Image.new('RGB', (W, 500), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '03  la garganta de río: una siringe sopla un tubo con la forma del perfil del río; en el ápice el tubo se parte en cinco bocas (una unión de N puertos)', font=fn(15), fill=TXT)
for row, (nom, ar) in enumerate([('el tronco = el perfil del río (sierra → ápice)', A['tronco']), ('deformado hacia «a»', A['a']), ('hacia «u»', A['u'])]):
    y0 = 110 + row * 130; d.text((20, y0 - 50), nom, font=fn(13), fill=TXT)
    for j, a_ in enumerate(ar):
        r = math.sqrt(a_ / math.pi) * 30; x = 30 + j * 26; d.rectangle([x, y0 - r, x + 24, y0 + r], fill=(40, 80, 95), outline=(150, 220, 235))
    xa = 30 + 24 * 26
    for i, b in enumerate(P['delta']['brazos']):
        ang = math.radians(-35 + 70 * (b['pan'] + 1) / 2); L = b['secciones'] * 26
        d.line([xa, y0, xa + L * math.cos(ang), y0 + L * math.sin(ang)], fill=tinta(i, 5, .75), width=10)
d.text((900, 120), 'las bocas, cada una con su largo (el de su brazo),\nsu lugar en el estéreo (su ángulo) y su retraso\n(0.6 ms por sección): una voz sale por cinco bocas', font=fn(14), fill=TXT, spacing=6)
im.save(nuevo(f'03-garganta-de-rio-s{s}-{h}.png'))

# 04 · quién toca
im = Image.new('RGB', (W, 560), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '04  quién toca: afluentes (Reich), el río (arpa, sus armónicos), el coro, el canon de los brazos, el mar', font=fn(16), fill=TXT)
m_de = lambda f: 69 + 12 * math.log2(f / 440)
filas = [('afluentes', [(e['t'], e['dur'], e['midi']) for e in P['web']['marimba']] + [(e['t'], .2, e['m']) for e in P['agua'] if e['tipo'] == 'gota']),
         ('el río', [(e['t'], e['dur'], e['m']) for e in P['melodia']]), ('coro S', [(e['t'], e['dur'], e['nota']) for C in P['coros'].values() for e in C['S']]),
         ('coro T (garganta)', [(e['t'], e['dur'], e['nota']) for e in P['garganta'] if e['voz'] == 'coro'])]
filas += [(f'brazo {i}', [(c['t'], c['dur'], c['m']) for c in P['canon'] if c['brazo'] == i]) for i in range(5)]
filas += [('el mar', [(v['t'], v['dur'], v['m']) for v in P['mar']])]
for k, (nom, ns) in enumerate(filas):
    col = tinta(k, len(filas), .72); y0 = 50 + k * 49; d.text((10, y0 + 14), nom, font=fn(12), fill=col)
    if not ns: continue
    lo, hi = min(n[2] for n in ns), max(n[2] for n in ns) + 1
    for t, du, m in ns: x = 170 + t / DUR * (W - 190); x2 = 170 + (t + du) / DUR * (W - 190); y = y0 + 40 - (m - lo) / (hi - lo) * 36; d.rectangle([x, y - 1, max(x + 1, x2), y + 1], fill=col)
secciones(d, 170, W - 190, 40, 550); im.save(nuevo(f'04-voces-s{s}-{h}.png'))

# 05 · el mar
im = Image.new('RGB', (W, 420), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '05  el mar (Scelsi): cada brazo llega, se desliza a la nota del mar y se queda desviado unos cents; la desviación se cierra en el tiempo que le queda', font=fn(15), fill=TXT)
a0, a1 = TT['mar'] - 2, TT['fin']; X = lambda t: 60 + (t - a0) / (a1 - a0) * (W - 100); Y = lambda c: 220 - c * 3.2
d.line([X(a0), Y(0), X(a1), Y(0)], fill=(90, 90, 110)); d.text((10, Y(0) - 7), '0 ¢', font=fn(12), fill=TXT); d.text((10, Y(50) - 7), '+50', font=fn(12), fill=TXT); d.text((10, Y(-50) - 7), '−50', font=fn(12), fill=TXT)
for k, v in enumerate(P['mar']):
    tau = v['dur'] / 4.5; ts = np.linspace(0, v['dur'], 400)
    c = v['dev0'] * np.exp(-ts / tau) + 25 * np.exp(-ts / (tau * .8)) * np.sin(2 * np.pi * ts / (5.5 + k) + k)
    d.line([(X(v['t'] + t), Y(cc)) for t, cc in zip(ts, c)], fill=tinta(k, 5, .75), width=2); d.text((X(v['t']) + 4, Y(c[0]) - 16), f'brazo {k}', font=fn(11), fill=tinta(k, 5, .75))
im.save(nuevo(f'05-mar-scelsi-s{s}-{h}.png'))

# 06 · capas solas
def espectro(x, alto, fmax=12000, hop=1024):
    N = 2048; win = np.hanning(N); fr = [np.abs(np.fft.rfft(x[i:i + N] * win)) for i in range(0, len(x) - N, hop)]
    Sx = 20 * np.log10(np.array(fr).T + 1e-9); f = np.fft.rfftfreq(N, 1 / SR); filas = np.geomspace(40, fmax, alto)[::-1]
    img = Sx[np.searchsorted(f, filas)]; return np.clip((img - (img.max() - 65)) / 65, 0, 1)
def pinta(img, col): return (np.power(img[..., None], 1.3) * np.array(col) + np.array(FONDO) * (1 - img[..., None])).astype(np.uint8)
capas = [(c, True) for c in P['web'] if P['web'][c]] + [(c, False) for c in ['vozagua', 'agua', 'aves', 'tabla', 'trombon', 'gong']] + [(c, True) for c in ['garganta-coro', 'garganta-mar', 'sabina-soprano', 'sabina-mar']]
alto = 42; x0 = 160; im = Image.new('RGB', (W, 50 + (alto + 5) * len(capas)), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '06  las capas solas, antes de mezclar (40 Hz–12 kHz) — las de Python (arpa, armonio, tambura, mar) están en la 07', font=fn(16), fill=TXT)
for k, (c, st) in enumerate(capas):
    x = np.fromfile(os.path.join(RUN, c + '.f32'), dtype=np.float32).astype(float); x = x.reshape(-1, 2).mean(1) if st else x
    col = tinta(k, len(capas)); y0 = 46 + k * (alto + 5); im.paste(Image.fromarray(pinta(espectro(x, alto, hop=2048), col)).resize((W - x0 - 10, alto)), (x0, y0)); d.text((8, y0 + 12), c, font=fn(12), fill=col)
secciones(d, x0, W - x0 - 10, 36, im.height - 4); im.save(nuevo(f'06-capas-s{s}-{h}.png'))

# 07 · mezcla
sr, x = wavfile.read(os.path.join(OUT, os.path.basename(OUT) + '.wav')); x = x.astype(float).mean(1) / 32768
mez = Image.new('RGB', (W, 400), FONDO); mez.paste(Image.fromarray(pinta(espectro(x, 330), (226, 232, 236))).resize((W - 20, 330)), (10, 50)); d = ImageDraw.Draw(mez)
d.text((14, 10), f'07  El río no tiene tronco (s{s}): la mezcla, {len(x) / sr:.0f} s', font=fn(18), fill=TXT); secciones(d, 10, W - 20, 44, 385)
mez.save(nuevo(f'07-mezcla-s{s}-{h}.png'))

# GIF: el frente del agua avanza por el mapa; abajo la mezcla
cuadros = []; NC = 34
for j in range(1, NC + 1):
    t = DUR * j / NC; c = Image.new('RGB', (W, 820), FONDO); c.paste(mapa(400, t), (20, 10)); dd = ImageDraw.Draw(c)
    sec = next((k for k, (a, z) in SECS.items() if a <= t < z), 'IV'); dd.text((460, 30), NOM[sec], font=fn(30), fill=TXT); dd.text((460, 80), f'{t:5.1f} s', font=fn(20), fill=(170, 175, 190))
    c.paste(mez, (0, 420)); xx = 10 + int((W - 20) * j / NC); dd.rectangle([xx, 470, W - 10, 800], fill=FONDO); dd.line([xx, 470, xx, 800], fill=TXT, width=2)
    cuadros.append(c.resize((1100, 531)))
gif = os.path.join(OUT, f'el-rio-no-tiene-tronco-s{s}-{h}.gif'); cuadros[0].save(gif, save_all=True, append_images=cuadros[1:] + [cuadros[-1]] * 2, duration=270, loop=0, optimize=True)
cuadros[-1].save(nuevo(f'08-agua-y-mezcla-s{s}-{h}.png'))
print(gif, os.path.getsize(gif) // 1024, 'KB')
