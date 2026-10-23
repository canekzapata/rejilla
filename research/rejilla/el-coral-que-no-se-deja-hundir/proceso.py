"""El coral que no se deja hundir — PNGs de etapas, sondas de la pieza y GIF del proceso.
    python proceso.py <carpeta-de-render> <carpeta-de-entrega> [--b 03,04]
01 el atolón 2 y su collar (los islotes leídos en ángulo → 32 dieciseisavos; la Boca Grande) · 02 el coral que crece (el corte del
arrecife a cuatro tiempos; cada partícula es un modo) · 03 los dos movimientos contrarios (el volcán baja, la copa del coral sube; el
batido en el cruce) · 04 las olas que se parten (el perfil en la orilla, una cresta por solitón) · 05 el tapete de Talbot sobre el collar
en III · 06 el volcán se borra (la vuelta de 2π) · 07 quién toca (las capas solas) · 08 la mezcla · GIF: el coral crece mientras el
volcán se hunde. Colores OKLCh sembrados (s2): la caliza y la laguna.
"""
import json, math, os, sys
from fractions import Fraction
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
AQUI = os.path.dirname(os.path.abspath(__file__))
RUN, OUT = sys.argv[1], sys.argv[2]; P = json.load(open(os.path.join(OUT, 'partitura.json'), encoding='utf-8'))
h = os.path.basename(OUT).rsplit('-', 1)[1]; s = P['semilla']; pr = os.path.join(OUT, 'proceso')
B = sys.argv[sys.argv.index('--b') + 1].split(',') if '--b' in sys.argv else None
if B is None: os.makedirs(pr, exist_ok=False)
DUR = P['duracion']; SR = 48000; W = 1700; G = 360
H = np.fromfile(os.path.join(AQUI, 'terreno', 'h-2.f32'), dtype=np.float32).reshape(G, G)
HF = np.fromfile(os.path.join(AQUI, 'terreno', 'fondo-2.f32'), dtype=np.float32).reshape(G, G)
CR = json.load(open(os.path.join(RUN, 'coral-crecimiento.json'), encoding='utf-8'))
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
CAL = 70 + (s * 37.1) % 40; LAG = 185 + (s * 13.7) % 40
FONDO = oklch(.12, .025, LAG + 20); TXT = oklch(.92, .03, CAL); TENUE = oklch(.58, .03, CAL)
VOLC, CORAL, AGUA = oklch(.72, .15, 30), oklch(.84, .12, CAL + 10), oklch(.74, .11, LAG)
def tinta(k, n, L=.75): return oklch(L, .12, LAG + (CAL + 360 - LAG) * k / max(1, n - 1))
NOM = {'I': 'LA ISLA ALTA', 'II': 'EL HUNDIMIENTO', 'III': 'EL CRUCE', 'IV': 'EL ARRECIFE', 'V': 'EL ATOLÓN'}
def secciones(d, x0, Wd, y0, y1):
    for e in P['secciones']: xa = x0 + int(e['t'] / DUR * Wd); d.line([xa, y0, xa, y1], fill=oklch(.35, .03, LAG)); d.text((xa + 4, y0 + 2), e['num'] + ' ' + NOM[e['num']], font=fn(11), fill=TENUE)
SONDA = {}

# 01 · el atolón y su collar
lam = P['lamina']; img = Image.new('RGB', (W, 760), FONDO); d = ImageDraw.Draw(img)
fz = (HF - HF.min()) / (HF.max() - HF.min() + 1e-9); base = np.array(oklch(.14, .04, LAG)) + fz[..., None] * (np.array(oklch(.45, .08, LAG)) - np.array(oklch(.14, .04, LAG)))
base[H > 0.0001] = oklch(.88, .08, CAL); mapa = Image.fromarray(base.astype(np.uint8)).resize((700, 700)); img.paste(mapa, (20, 40))
d.text((14, 10), f'01  el atolón 2 «El Banco de las Fragatas»: {len(lam["islotes"])} islotes, la Boca Grande ({lam["boca"][1]:.0f}°), la laguna de {lam["prof_laguna_m"]} m', font=fn(15), fill=TXT)
cx, cy, R0 = 1180, 390, 270
d.ellipse([cx - R0, cy - R0, cx + R0, cy + R0], outline=TENUE, width=1)
for k in range(32):
    a = 2 * math.pi * k / 32 - math.pi / 2; d.line([cx + (R0 - 8) * math.cos(a), cy + (R0 - 8) * math.sin(a), cx + (R0 + 8) * math.cos(a), cy + (R0 + 8) * math.sin(a)], fill=TENUE)
for e in P['collar']:
    a = 2 * math.pi * e['paso'] / 32 - math.pi / 2; r = 8 + 16 * e['peso']; x, y = cx + R0 * math.cos(a), cy + R0 * math.sin(a)
    d.ellipse([x - r, y - r, x + r, y + r], fill=CORAL)
a = 2 * math.pi * 16 / 32 - math.pi / 2; d.text((cx + (R0 + 30) * math.cos(a) - 50, cy + (R0 + 30) * math.sin(a)), 'LA BOCA (güiro)', font=fn(13), fill=AGUA)
d.text((cx - 240, cy - 20), 'el anillo en un ciclo de 32 dieciseisavos', font=fn(14), fill=TXT)
d.text((cx - 240, cy + 4), f'golpes: {sorted(e["paso"] for e in P["collar"])}', font=fn(12), fill=TENUE)
d.text((cx - 240, cy + 28), f'tónica = seiche de la laguna: {lam["f_seiche_hz"]:.5f} Hz × 2^{lam["octavas_arriba"]} = {440 * 2 ** ((P["tonica"] - 69) / 12):.1f} Hz', font=fn(12), fill=TENUE)
SONDA['collar'] = dict(islotes=len(lam['islotes']), golpes=len(P['collar']), boca_grados=lam['boca'])
guardar(img, f'01-atolon-y-collar-s{s}-{h}.png')

# 02 · el coral que crece (el corte a cuatro tiempos)
parts = CR['particulas']; tiempos = np.array(CR['tiempos']); Wc, Hc = P['coral']['W'], P['coral']['H']; basec = P['coral']['base']
def corte(t, ancho=380, alto=240):
    a = np.zeros((Hc + 2, Wc, 3), np.uint8); a[:] = oklch(.16, .05, LAG)
    for x in range(Wc):
        a[:basec[x] + 1, x] = oklch(.35, .05, 30)
    for (x, y, _), tt in zip(parts, tiempos):
        if tt <= t: a[y, x] = oklch(.55 + .35 * y / Hc, .1, CAL + 10)
    return Image.fromarray(a[::-1]).resize((ancho, alto), Image.NEAREST)
img = Image.new('RGB', (W, 380), FONDO); d = ImageDraw.Draw(img)
d.text((14, 10), f'02  el coral que crece: el plancton cae y se pega (DLA). {CR["modos"]} partículas = {CR["modos"]} modos, en {CR["notas_distintas"]} notas del modo 3; la altura en el arrecife es la altura de tono', font=fn(14), fill=TXT)
for k, t in enumerate((20, 80, 140, 200)):
    img.paste(corte(t, 400, 260), (20 + k * 420, 60)); n = int((tiempos <= t).sum())
    d.text((20 + k * 420, 330), f'{t} s · {n} modos · copa {max([y for (x, y, _), tt in zip(parts, tiempos) if tt <= t] or [0])}', font=fn(13), fill=CORAL)
guardar(img, f'02-coral-que-crece-s{s}-{h}.png')

# 03 · los dos movimientos contrarios y el cruce
fv = lambda t: P['f_cruce'] * 2 ** ((P['cruce'] - t) / P['t8'])
ts_ = np.linspace(0, DUR - 8, 800); ymax = np.array([max([y for (x, y, _), tt in zip(parts, tiempos) if tt <= t] or [CR['y_base']]) for t in ts_])
fbajo, falto, y0c = CR['f_bajo'], CR['f_alto'], CR['y_base']
fcopa = fbajo * (falto / fbajo) ** ((ymax - y0c) / (Hc - y0c))
MOD3 = [0, 2, 3, 4, 6, 7, 8, 10, 11]; esc = sorted({P['tonica'] + 12 * o + g for o in range(-4, 6) for g in MOD3})
cuant = lambda f: 440 * 2 ** ((min(esc, key=lambda e: abs(e - (69 + 12 * math.log2(f / 440)))) - 69) / 12)
fcq = np.array([cuant(f) for f in fcopa]); batido = np.abs(np.array([fv(t) for t in ts_]) - fcq)
k = int(np.argmin(batido)); SONDA['cruce'] = dict(t_cruce_partitura=P['cruce'], t_batido_minimo=round(float(ts_[k]), 2), batido_minimo_hz=round(float(batido[k]), 3),
                                                f_volcan=round(fv(ts_[k]), 3), f_coral_copa=round(float(fcq[k]), 3), batido_a_mas_menos_20s=[round(float(batido[np.argmin(np.abs(ts_ - (P['cruce'] + d)))]), 2) for d in (-20, 20)])
img = Image.new('RGB', (W, 520), FONDO); d = ImageDraw.Draw(img)
d.text((14, 10), f'03  dos movimientos contrarios: el volcán baja (una octava cada {P["t8"]:.0f} s), la copa del coral sube; batido en el cruce: {SONDA["cruce"]["batido_minimo_hz"]} Hz a los {SONDA["cruce"]["t_batido_minimo"]} s', font=fn(14), fill=TXT)
x0, y0, Wd, Hd = 60, 60, W - 100, 400; lo, hi = math.log2(min(fcq.min(), fv(DUR)) * .9), math.log2(max(fv(0), fcq.max()) * 1.1)
Y = lambda f: y0 + Hd - (math.log2(f) - lo) / (hi - lo) * Hd; X = lambda t: x0 + t / DUR * Wd
d.line([(X(t), Y(fv(t))) for t in ts_], fill=VOLC, width=3); d.line([(X(t), Y(f)) for t, f in zip(ts_, fcq)], fill=CORAL, width=3)
d.text((X(4), Y(fv(4)) - 22), 'el volcán (garganta) baja', font=fn(13), fill=VOLC); d.text((X(150), Y(fcq[np.argmin(np.abs(ts_ - 150))]) - 22), 'la copa del coral sube', font=fn(13), fill=CORAL)
d.ellipse([X(ts_[k]) - 7, Y(fcq[k]) - 7, X(ts_[k]) + 7, Y(fcq[k]) + 7], outline=TXT, width=2); d.text((X(ts_[k]) + 12, Y(fcq[k]) + 6), f'el cruce: {fcq[k]:.1f} Hz', font=fn(13), fill=TXT)
pv = P['volcan']['prof']; t_mar = np.interp(0, [b for _, b in pv], [a for a, _ in pv]); d.line([X(t_mar), y0, X(t_mar), y0 + Hd], fill=AGUA); d.text((X(t_mar) + 4, y0 + 4), 'el volcán entra al agua', font=fn(12), fill=AGUA)
secciones(d, x0, Wd, y0 + Hd + 6, y0 + Hd + 40)
guardar(img, f'03-dos-movimientos-y-el-cruce-s{s}-{h}.png')

# 04 · las olas que se parten
sys.path.insert(0, AQUI); import sintes8 as S8
img = Image.new('RGB', (W, 420), FONDO); d = ImageDraw.Draw(img); ll = json.load(open(os.path.join(RUN, 'olas-llegadas.json')))
d.text((14, 10), f'04  la ola que se parte en el arrecife: n solitones de KdV (κ = 1…n) llegan a la orilla uno tras otro, el más alto primero · {len(P["olas"])} olas', font=fn(14), fill=TXT)
crestas = []
for k, nsol in enumerate((1, 2, 3, 4, 5)):
    _, q, lle = S8.ola(0.0, nsol, int(5 * SR), dur=4.0, semilla=k); crestas.append(len(lle))
    x0 = 20 + k * 335; d.text((x0, 50), f'n = {nsol}: {len(lle)} crestas', font=fn(13), fill=AGUA)
    d.line([(x0 + i / len(q) * 310, 360 - 280 * v) for i, v in enumerate(q)], fill=AGUA, width=2)
SONDA['olas'] = dict(crestas_por_n=dict(zip((1, 2, 3, 4, 5), crestas)), crestas_en_la_pieza=sum(len(x) for x in ll), olas=len(ll))
guardar(img, f'04-olas-que-se-parten-s{s}-{h}.png')

# 05 · el tapete de Talbot sobre el collar
sys.path.insert(0, os.path.join(AQUI, '..', 'tapete-de-talbot')); import tapete as TP
img = Image.new('RGB', (W, 360), FONDO); d = ImageDraw.Draw(img)
d.text((14, 10), '05  el tapete de Talbot sobre el collar en III (exacto): cada τ = p/q vuelve el ciclo L copias corridas, con pesos de Gauss', font=fn(14), fill=TXT)
fila = 0; tal = {}
for _, tau in P['talbot']['tramos']:
    if tau == '0': continue
    L, c = TP.copias(Fraction(tau).numerator, Fraction(tau).denominator); voces = [j for j in range(L) if abs(c[j]) > 1e-9]
    tal[tau] = [f'{j}/{L}' for j in voces]; y = 70 + fila * 90; d.text((20, y + 10), f'τ = {tau}', font=fn(16), fill=TXT)
    d.line([200, y + 20, W - 40, y + 20], fill=TENUE)
    for e in P['collar']:
        for j in voces:
            x = 200 + ((e['paso'] / 32 + j / L) % 1) * (W - 240); hue = math.degrees(np.angle(c[j]))
            d.ellipse([x - 4, y + 16, x + 4, y + 24], fill=oklch(.8, .14, CAL + hue))
    d.text((20, y + 34), 'copias en ' + ', '.join(tal[tau]), font=fn(12), fill=TENUE); fila += 1
SONDA['talbot'] = tal
guardar(img, f'05-talbot-sobre-el-collar-s{s}-{h}.png')

# 06 · el volcán se borra
def leer(n, est):
    x = np.fromfile(os.path.join(RUN, n + '.f32'), dtype=np.float32).astype(float); return x.reshape(-1, 2).mean(1) if est else x
vol = leer('volcan', False); th = P['volcan']['theta']; t_a, t_z = th[1][0], th[2][0]
rms = lambda a, z: float(np.sqrt(np.mean(vol[int(a * SR):int(z * SR)] ** 2)) + 1e-15)
SONDA['volcan_borrado'] = dict(antes_db=round(20 * math.log10(rms(t_a - 6, t_a)), 1), despues_db=round(20 * math.log10(rms(t_z + .5, t_z + 6)), 1),
                               caida_db=round(20 * math.log10(rms(t_z + .5, t_z + 6) / rms(t_a - 6, t_a)), 1))
env = np.sqrt(np.convolve(vol ** 2, np.ones(4800) / 4800, 'same'))[::480]; tt = np.arange(len(env)) * .01
img = Image.new('RGB', (W, 300), FONDO); d = ImageDraw.Draw(img)
d.text((14, 10), f'06  el volcán (su garganta, sin mezclar): se apaga al hundirse y la vuelta de 2π lo borra ({t_a:.0f}–{t_z:.0f} s): {SONDA["volcan_borrado"]["caida_db"]} dB', font=fn(14), fill=TXT)
eb = 20 * np.log10(env / env.max() + 1e-12); d.line([(40 + t / DUR * (W - 80), 60 + min(200, -e * 2.2)) for t, e in zip(tt, eb)], fill=VOLC, width=2)
for v in (0, -40, -80): d.text((4, 60 + -v * 2.2 - 6), f'{v}', font=fn(11), fill=TENUE)
secciones(d, 40, W - 80, 268, 296)
guardar(img, f'06-volcan-se-borra-s{s}-{h}.png')

# 07 · las capas solas
def espectro(x, alto, f0=40, f1=8000, hop=4096):
    n = 8192; fr = np.fft.rfftfreq(n, 1 / SR); win = np.hanning(n); cols = []
    for i in range(0, len(x) - n, hop): cols.append(np.abs(np.fft.rfft(x[i:i + n] * win)))
    S = np.array(cols).T; fl = np.geomspace(f0, f1, alto); M = np.array([np.interp(fl, fr, c) for c in S.T]).T
    M = 20 * np.log10(M / (M.max() + 1e-12) + 1e-9); return np.clip((M + 70) / 70, 0, 1)[::-1]
def pinta(M, col): return (M[..., None] * np.array(col)[None, None, :] + (1 - M[..., None]) * np.array(FONDO)[None, None, :]).astype(np.uint8)
CAPAS = [('volcan', 0), ('coral', 1), ('coral-clics', 1), ('olas', 1), ('burbujas', 1), ('laguna', 1), ('congas', 1), ('vibrafono', 1), ('marimba', 1), ('steelpan', 1),
         ('bateria808', 1), ('aves0', 0), ('boca', 1), ('luciernagas', 1), ('sabina-lead', 1), ('sabina-coro', 1), ('sabina-chops', 1)]
alto = 30; x0 = 170; im = Image.new('RGB', (W, 50 + (alto + 4) * len(CAPAS)), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '07  las capas solas antes de mezclar (40 Hz–8 kHz) — el sub, el tapete y los vocoders se ven en la 08', font=fn(14), fill=TXT)
for k, (c, st) in enumerate(CAPAS):
    col = tinta(k, len(CAPAS)); y0 = 44 + k * (alto + 4); im.paste(Image.fromarray(pinta(espectro(leer(c, st), alto), col)).resize((W - x0 - 10, alto)), (x0, y0)); d.text((8, y0 + 8), c, font=fn(11), fill=col)
secciones(d, x0, W - x0 - 10, 36, im.height - 4); guardar(im, f'07-capas-s{s}-{h}.png')

# 08 · la mezcla
sr, x = wavfile.read(os.path.join(OUT, os.path.basename(OUT) + '.wav')); x = x.astype(float).mean(1) / 32768
mez = Image.new('RGB', (W, 400), FONDO); mez.paste(Image.fromarray(pinta(espectro(x, 330, 30, 12000), oklch(.92, .04, CAL))).resize((W - 20, 330)), (10, 50)); d = ImageDraw.Draw(mez)
d.text((14, 10), f'08  El coral que no se deja hundir (s{s}): la mezcla, {len(x) / sr:.0f} s', font=fn(18), fill=TXT); secciones(d, 10, W - 20, 44, 385)
guardar(mez, f'08-mezcla-s{s}-{h}.png')

# GIF: el coral crece mientras el volcán se hunde
cuadros = []; NC = 34
for j in range(1, NC + 1):
    t = (DUR - 8) * j / NC; c = Image.new('RGB', (W, 800), FONDO); dd = ImageDraw.Draw(c); c.paste(corte(t, 560, 360), (20, 20))
    sec = [e for e in P['secciones'] if e['t'] <= t][-1]['num']; n = int((tiempos <= t).sum())
    dd.text((620, 30), f'{sec}  {NOM[sec]}', font=fn(28), fill=TXT); dd.text((620, 80), f'{t:5.1f} s · coral: {n} modos', font=fn(18), fill=CORAL)
    dd.text((620, 110), f'volcán: {fv(t):6.1f} Hz', font=fn(18), fill=VOLC)
    c.paste(mez, (0, 400)); xx = 10 + int((W - 20) * t / DUR); dd.rectangle([xx, 450, W - 10, 780], fill=FONDO); dd.line([xx, 450, xx, 780], fill=TXT, width=2)
    cuadros.append(c.resize((1100, 518)))
gif = os.path.join(OUT, f'el-coral-que-no-se-deja-hundir-s{s}-{h}.gif'); cuadros[0].save(gif, save_all=True, append_images=cuadros[1:] + [cuadros[-1]] * 2, duration=270, loop=0, optimize=True)
cuadros[-1].save(nuevo(f'09-coral-y-mezcla-s{s}-{h}.png'))
if B is None: json.dump(SONDA, open(os.path.join(OUT, 'sondas.json'), 'x', encoding='utf-8'), ensure_ascii=False, indent=1)
print(gif, os.path.getsize(gif) // 1024, 'KB'); print(json.dumps(SONDA, ensure_ascii=False))
