"""Las islas del cielo — PNGs de etapas, sondas de la pieza y GIF del proceso.
    python proceso.py <carpeta-de-render> <carpeta-de-entrega> [--b 03,04]
01 la meseta (mesa 134) y las tres islas (tepuyes 2572): sus paredes, sus nombres, su lugar · 02 el tema se parte: cada isla, generación
por generación; la distancia al tema original y el consenso del llano · 03 la afinación y el compás de cada isla (cents en el tiempo;
dónde acentúa cada una) · 04 las cascadas que no llegan (columna → gotas → niebla; su duración es su pared) · 05 la campana: la
vecindad cambia con la erosión · 06 las capas solas · 07 la mezcla · GIF: el tema partiéndose. Colores OKLCh sembrados (s2572).
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
DUR = P['duracion']; SR = 48000; W = 1700; G = 360
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
ARE = 55 + (s * 1.7) % 30; SEL = 150 + (s * 3.1) % 40
FONDO = oklch(.12, .02, SEL + 20); TXT = oklch(.92, .03, ARE); TENUE = oklch(.58, .03, ARE)
ISLA_COL = [oklch(.78, .14, ARE + 120 * i) for i in range(len(P['islas']))]
NOM = {'I': 'LA MESETA', 'II': 'EL LEVANTAMIENTO', 'III': 'LA EROSIÓN', 'IV': 'LAS ISLAS DEL CIELO', 'V': 'EL LLANO'}
def secciones(d, x0, Wd, y0, y1):
    for e in P['secciones']: xa = x0 + int(e['t'] / DUR * Wd); d.line([xa, y0, xa, y1], fill=oklch(.35, .03, SEL)); d.text((xa + 4, y0 + 2), e['num'] + ' ' + NOM[e['num']], font=fn(11), fill=TENUE)
SONDA = {}
def mapa(arch, lado, umbral=.5):
    hh = np.fromfile(os.path.join(AQUI, 'terreno', arch), dtype=np.float32).reshape(G, G); a = (hh - hh.min()) / (np.ptp(hh) + 1e-9)
    b0, b1 = np.array(oklch(.15, .03, SEL)), np.array(oklch(.75, .07, ARE)); img = b0 + a[..., None] * (b1 - b0)
    lv = (a * 18).astype(int); borde = (np.abs(np.diff(lv, axis=0, prepend=lv[:1])) + np.abs(np.diff(lv, axis=1, prepend=lv[:, :1]))) > 0; img[borde] = oklch(.85, .05, ARE)
    return Image.fromarray(img.astype(np.uint8)).resize((lado, lado))

# 01 · la meseta y las islas
img = Image.new('RGB', (W, 760), FONDO); d = ImageDraw.Draw(img)
d.text((14, 10), f'01  antes y después de la erosión: la mesa 134 (la meseta) y los tepuyes 2572 (tres islas, paredes de {min(i["pared_m"] for i in P["islas"])}–{max(i["pared_m"] for i in P["islas"])} m)', font=fn(15), fill=TXT)
img.paste(mapa('h-134.f32', 640), (20, 60)); img.paste(mapa('h-2572.f32', 640), (700, 60)); d = ImageDraw.Draw(img)
d.text((24, 706), 'I–II · la meseta: un tema, una afinación', font=fn(14), fill=TENUE)
for i, isla in enumerate(P['islas']):
    x, y = 700 + isla['u'] * 640, 60 + isla['v'] * 640; d.ellipse([x - 8, y - 8, x + 8, y + 8], outline=ISLA_COL[i], width=3)
    d.text((x + 12, y - 8), isla['nombre'], font=fn(13), fill=ISLA_COL[i])
    d.text((1360, 90 + 120 * i), isla['nombre'], font=fn(14), fill=ISLA_COL[i])
    d.text((1360, 112 + 120 * i), f"pared {isla['pared_m']} m · tope {isla['tope_m']} m", font=fn(12), fill=TENUE)
    d.text((1360, 130 + 120 * i), f"afinación: {isla['cents_meta']:+.1f} cents · compás {isla['compas']} · pan {isla['pan']:+.1f}", font=fn(12), fill=TENUE)
d.text((1360, 470), f"tónica: la pared media ({P['pared_media_m']} m)", font=fn(12), fill=TENUE); d.text((1360, 488), f"como tubo: {P['f_tubo_hz']:.4f} Hz × 2^{P['octavas_arriba']}", font=fn(12), fill=TENUE)
d.text((704, 706), 'III–V · las islas: cada una su variante', font=fn(14), fill=TENUE)
guardar(img, f'01-meseta-e-islas-s{s}-{h}.png')

# 02 · el tema se parte
V = P['variantes']; ng = len(V[0]); dist = [[sum(1 for a, b in zip(P['tema'], g) if a != b) for g, _ in V[i]] for i in range(len(V))]
SONDA['tema'] = dict(original=P['tema'], finales=[V[i][-1][0] for i in range(len(V))], distancias_finales=[dd[-1] for dd in dist], consenso=P['consenso'],
                     distancia_consenso=P['distancia_consenso'], distancia_entre_finales=[sum(1 for a, b in zip(V[i][-1][0], V[j][-1][0]) if a != b) for i in range(len(V)) for j in range(i + 1, len(V))])
img = Image.new('RGB', (W, 640), FONDO); d = ImageDraw.Draw(img)
d.text((14, 10), f'02  el tema se parte: cada isla lo canta a su manera y muta por su lado (una generación cada {P["generacion_D"]} compases); al final el consenso, {P["distancia_consenso"]} notas distinto', font=fn(14), fill=TXT)
cel = 14
for i in range(len(V)):
    x0 = 30 + i * 420; d.text((x0, 40), P['islas'][i]['nombre'], font=fn(13), fill=ISLA_COL[i])
    for gi, (g, l) in enumerate(V[i]):
        for c in range(12):
            col = oklch(.25 + .06 * (g[c] + 2), .1, ARE + 120 * i) if not l[c] else FONDO
            d.rectangle([x0 + c * cel * 2, 64 + gi * 15, x0 + c * cel * 2 + cel * 2 - 2, 64 + gi * 15 + 13], fill=col)
    d.text((x0, 64 + ng * 15 + 6), f'distancia al original: {dist[i][-1]} de 12', font=fn(12), fill=TENUE)
x0 = 1290; d.text((x0, 40), 'el llano: el consenso', font=fn(13), fill=TXT)
for c in range(12): d.rectangle([x0 + c * 30, 64, x0 + c * 30 + 28, 77], fill=oklch(.25 + .06 * (P['consenso'][c] + 2), .03, ARE))
for c in range(12): d.rectangle([x0 + c * 30, 84, x0 + c * 30 + 28, 97], fill=oklch(.25 + .06 * (P['tema'][c] + 2), .03, ARE))
d.text((x0, 102), 'arriba: consenso · abajo: el tema de la meseta', font=fn(11), fill=TENUE)
guardar(img, f'02-el-tema-se-parte-s{s}-{h}.png')

# 03 · la afinación y el compás
sys.path.insert(0, AQUI)
import importlib.util
img = Image.new('RGB', (W, 470), FONDO); d = ImageDraw.Draw(img)
d.text((14, 10), '03  cada isla se corre hacia el tono de su pared (cents, sobre la cuarta que subió el levantamiento) y agrupa las corcheas en su compás', font=fn(14), fill=TXT)
x0, y0, Wd, Hd = 60, 60, W - 420, 300; T = np.linspace(0, DUR, 600)
SEC = {e['num']: (e['t'], e['t1']) for e in P['secciones']}
def cents(i, t):
    a, z = SEC['III'][0], SEC['IV'][1]; v5, z5 = SEC['V'][0], SEC['V'][0] + 12 * P['D']; cm = P['islas'][i]['cents_meta']
    if t < a: return 0.0
    if t < z: u = (t - a) / (z - a); return cm * u * u * (3 - 2 * u)
    if t < z5: u = (t - v5) / (z5 - v5); return cm * (1 - u) + P['cents_llano'] * u
    return P['cents_llano']
lo, hi = -20, 20; Y = lambda c: y0 + Hd / 2 - c / (hi - lo) * Hd
d.line([x0, Y(0), x0 + Wd, Y(0)], fill=TENUE)
for i in range(len(P['islas'])): d.line([(x0 + t / DUR * Wd, Y(cents(i, t))) for t in T], fill=ISLA_COL[i], width=3)
secciones(d, x0, Wd, y0 + Hd + 6, y0 + Hd + 40)
for i, isla in enumerate(P['islas']):
    yy = 80 + 110 * i; d.text((W - 340, yy), f"{isla['nombre']} · {isla['compas']}", font=fn(13), fill=ISLA_COL[i])
    for c in range(12):
        x = W - 340 + c * 24; acento = c in isla['acentos']; d.rectangle([x, yy + 24, x + 20, yy + 24 + (40 if acento else 16)], fill=ISLA_COL[i] if acento else TENUE)
comunes = sorted(set.intersection(*[set(i['acentos']) for i in P['islas']])); SONDA['compases'] = dict(acentos=[i['acentos'] for i in P['islas']], coinciden_las_tres_en=comunes)
SONDA['afinacion'] = dict(cents_meta=[i['cents_meta'] for i in P['islas']], cents_llano=P['cents_llano'])
guardar(img, f'03-afinacion-y-compas-s{s}-{h}.png')

# 04 · las cascadas
def leer(n, est):
    x = np.fromfile(os.path.join(RUN, n + '.f32'), dtype=np.float32).astype(float); return x.reshape(-1, 2).mean(1) if est else x
CI = json.load(open(os.path.join(RUN, 'cascadas-info.json'))); SONDA['cascadas'] = CI
cas = leer('cascadas', True); env = np.sqrt(np.convolve(cas ** 2, np.ones(4800) / 4800, 'same'))[::480]; tt = np.arange(len(env)) * .01
img = Image.new('RGB', (W, 380), FONDO); d = ImageDraw.Draw(img)
d.text((14, 10), '04  las cascadas que no llegan: columna (cae libre hasta romperse) → gotas → niebla; su duración sale de su pared; nada golpea el suelo', font=fn(14), fill=TXT)
eb = 20 * np.log10(env / env.max() + 1e-9); d.line([(40 + t / DUR * (W - 80), 60 + min(220, -e * 3)) for t, e in zip(tt, eb)], fill=oklch(.8, .1, SEL), width=2)
for i, c in enumerate(CI):
    xa, xr, xz = (40 + (c['t'] + k) / DUR * (W - 80) for k in (0, c['t_rompe'], c['t_total']))
    y = 300 + 18 * i; d.line([xa, y, xr, y], fill=ISLA_COL[i], width=5); d.line([xr, y, xz, y], fill=ISLA_COL[i], width=1)
    d.text((40 + (xa - 40) * 0 + 40, y - 7), f"{P['islas'][i]['nombre'].lower()}: pared {c['H']} m → {c['t_total']:.0f} s (se rompe a los {c['t_rompe']:.1f} s)", font=fn(11), fill=ISLA_COL[i])
secciones(d, 40, W - 80, 350, 378)
guardar(img, f'04-cascadas-que-no-llegan-s{s}-{h}.png')

# 05 · la campana
cp = P['campana']; img = Image.new('RGB', (W, 360), FONDO); d = ImageDraw.Draw(img)
d.text((14, 10), '05  la campana de distancias imposibles (Codex): en III–IV cada isla golpea su familia (zonas ≡ isla mod 4); la vecindad se vuelve un árbol hondo con la erosión', font=fn(14), fill=TXT)
fold, depth = [[0, cp['initial']['fold']]], [[0, cp['initial']['depth']]]
for e in cp['events']:
    if 'params' in e:
        if 'fold' in e['params']: fold.append([e['t'], e['params']['fold']])
        if 'depth' in e['params']: depth.append([e['t'], e['params']['depth']])
for curva, col, nom, k in ((fold, oklch(.8, .12, ARE), 'pliegue (fold): de cerca a parentesco', 1), (depth, oklch(.8, .12, SEL), 'profundidad del árbol', 2)):
    pts = []; v = curva[0][1]
    for t in np.linspace(0, DUR, 400):
        for a, b in curva:
            if a <= t: v = b
        pts.append((40 + t / DUR * (W - 80), 250 - v / k * 160))
    d.line(pts, fill=col, width=2); d.text((W - 380, 60 + 22 * k), nom, font=fn(12), fill=col)
for e in cp['events']:
    if 'hit' in e: x = 40 + e['t'] / DUR * (W - 80); d.line([x, 270, x, 270 + 10 + (e['hit'] % 4) * 6], fill=ISLA_COL[e['hit'] % 3] if e['hit'] % 4 < 3 else TENUE)
secciones(d, 40, W - 80, 320, 356)
SONDA['campana'] = {k: (v['metrics'] if isinstance(v, dict) and 'metrics' in v else v) for k, v in json.load(open(os.path.join(RUN, 'campana-recibo.json'))).items()}   # sin las capturas del estado (pesan MB)
guardar(img, f'05-campana-s{s}-{h}.png')

# 06 · las capas solas
def espectro(x, alto, f0=40, f1=8000, hop=4096):
    n = 8192; fr = np.fft.rfftfreq(n, 1 / SR); win = np.hanning(n); cols = []
    for i in range(0, len(x) - n, hop): cols.append(np.abs(np.fft.rfft(x[i:i + n] * win)))
    S = np.array(cols).T; fl = np.geomspace(f0, f1, alto); M = np.array([np.interp(fl, fr, c) for c in S.T]).T
    M = 20 * np.log10(M / (M.max() + 1e-12) + 1e-9); return np.clip((M + 70) / 70, 0, 1)[::-1]
def pinta(M, col): return (M[..., None] * np.array(col)[None, None, :] + (1 - M[..., None]) * np.array(FONDO)[None, None, :]).astype(np.uint8)
CAPAS = [('arpa-meseta', 0), ('arpa-isla0', 0), ('arpa-isla1', 0), ('arpa-isla2', 0), ('cuatro', 0), ('capachos', 1), ('bateria', 1), ('tuki', 1), ('campana', 1), ('cascadas', 1),
         ('lluvia', 1), ('aves0', 0), ('sabina-lead', 1), ('sabina-coro', 1), ('sabina-isla0', 1), ('sabina-isla1', 1), ('sabina-isla2', 1)]
alto = 30; x0 = 170; im = Image.new('RGB', (W, 50 + (alto + 4) * len(CAPAS)), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '06  las capas solas antes de mezclar (40 Hz–8 kHz) — el sub y los vocoders se ven en la 07', font=fn(14), fill=TXT)
for k, (c, st) in enumerate(CAPAS):
    col = oklch(.75, .12, SEL + (ARE + 360 - SEL) * k / len(CAPAS)); y0 = 44 + k * (alto + 4)
    im.paste(Image.fromarray(pinta(espectro(leer(c, st), alto), col)).resize((W - x0 - 10, alto)), (x0, y0)); d.text((8, y0 + 8), c, font=fn(11), fill=col)
secciones(d, x0, W - x0 - 10, 36, im.height - 4); guardar(im, f'06-capas-s{s}-{h}.png')

# 07 · la mezcla
sr, x = wavfile.read(os.path.join(OUT, os.path.basename(OUT) + '.wav')); x = x.astype(float).mean(1) / 32768
mez = Image.new('RGB', (W, 400), FONDO); mez.paste(Image.fromarray(pinta(espectro(x, 330, 30, 12000), oklch(.92, .04, ARE))).resize((W - 20, 330)), (10, 50)); d = ImageDraw.Draw(mez)
d.text((14, 10), f'07  Las islas del cielo (s{s}): la mezcla, {len(x) / sr:.0f} s', font=fn(18), fill=TXT); secciones(d, 10, W - 20, 44, 385)
guardar(mez, f'07-mezcla-s{s}-{h}.png')

# GIF: el tema se parte, con la mezcla
cuadros = []; NC = 34
for j in range(1, NC + 1):
    t = DUR * j / NC; c = Image.new('RGB', (W, 800), FONDO); dd = ImageDraw.Draw(c); sec = [e for e in P['secciones'] if e['t'] <= t][-1]['num']
    dd.text((30, 24), f'{sec}  {NOM[sec]}', font=fn(30), fill=TXT); dd.text((30, 70), f'{t:5.1f} s', font=fn(18), fill=TENUE)
    gen = int(np.clip((t - SEC['III'][0]) // (P['generacion_D'] * P['D']), 0, ng - 1))
    for i in range(len(V)):
        g, l = (P['tema'], [False] * 12) if t < SEC['III'][0] else ((P['consenso'], [False] * 12) if t >= SEC['V'][0] + 12 * P['D'] else V[i][gen])
        x0 = 40 + i * 540; dd.text((x0, 120), P['islas'][i]['nombre'] if t >= SEC['III'][0] else 'LA MESETA', font=fn(15), fill=ISLA_COL[i] if t >= SEC['III'][0] else TXT)
        for k2 in range(12):
            if l[k2]: continue
            yb = 330 - (g[k2] + 2) * 18; dd.rectangle([x0 + k2 * 40, yb, x0 + k2 * 40 + 34, yb + 14], fill=ISLA_COL[i] if t >= SEC['III'][0] else TXT)
    c.paste(mez, (0, 400)); xx = 10 + int((W - 20) * t / DUR); dd.rectangle([xx, 450, W - 10, 780], fill=FONDO); dd.line([xx, 450, xx, 780], fill=TXT, width=2)
    cuadros.append(c.resize((1100, 518)))
gif = os.path.join(OUT, f'las-islas-del-cielo-s{s}-{h}.gif'); cuadros[0].save(gif, save_all=True, append_images=cuadros[1:] + [cuadros[-1]] * 2, duration=270, loop=0, optimize=True)
cuadros[-1].save(nuevo(f'08-islas-y-mezcla-s{s}-{h}.png'))
if B is None: json.dump(SONDA, open(os.path.join(OUT, 'sondas.json'), 'x', encoding='utf-8'), ensure_ascii=False, indent=1)
print(gif, os.path.getsize(gif) // 1024, 'KB'); print(json.dumps({k: v for k, v in SONDA.items() if k != 'campana'}, ensure_ascii=False))
