"""La ciudad se hunde bailando — PNGs de etapas, sondas de la pieza y GIF del proceso.
    python proceso.py <carpeta-de-render> <carpeta-de-entrega> [--b 03,04]
01 el campo de conos 769: el MC en el Cerro de los Lagos y el eco del valle (los conos vecinos, su distancia, su retraso) · 02 la ciudad
se hunde (metros por año, aproximado) y el disco se rebaja (semitonos, bpm); las sirenas, una por metro · 03 los dos relojes (tiempo de
disco contra tiempo real) · 04 la radio de onda corta: la perilla en sus tres tramos, sobre las estaciones · 05 el tapete de Talbot
sobre el dembow · 06 las capas solas · 07 la mezcla · GIF: el valle, los anillos de las bocinas y el año. Colores OKLCh sembrados (s769).
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
ROSA = 340 + (s * .7) % 20; LAGO = 200 + (s * 1.3) % 30
FONDO = oklch(.12, .03, ROSA + 20); TXT = oklch(.93, .03, ROSA); TENUE = oklch(.6, .04, ROSA); NEON = oklch(.72, .2, ROSA); AGUA = oklch(.72, .12, LAGO); AMBAR = oklch(.82, .15, 75)
SEC = {e['num']: (e['t_real'], e['t1_real']) for e in P['secciones']}
NOM = {'I': '1900 EL LAGO', 'II': '1930 LOS POZOS', 'III': '1950 EL GRAN HUNDIMIENTO', 'IV': '1970 EL ORIENTE', 'V': '2010 EL LAGO VUELVE'}
def secciones(d, x0, Wd, y0, y1):
    for k, (a, _) in SEC.items(): xa = x0 + int(a / DUR * Wd); d.line([xa, y0, xa, y1], fill=oklch(.35, .04, ROSA)); d.text((xa + 4, y0 + 2), NOM[k], font=fn(11), fill=TENUE)
SONDA = {}
VS = np.array(P['varispeed'])

# 01 · el valle y el eco
H = np.fromfile(os.path.join(AQUI, 'terreno', 'h-769.f32'), dtype=np.float32).reshape(G, G); a = (H - H.min()) / np.ptp(H)
img_m = (np.array(oklch(.15, .04, LAGO)) + a[..., None] * (np.array(oklch(.7, .08, ROSA - 30)) - np.array(oklch(.15, .04, LAGO)))).astype(np.uint8)
def valle(lado, anillos=None, t=None):
    im = Image.fromarray(img_m).resize((lado, lado)); d = ImageDraw.Draw(im); X = lambda c: (c['u'] * lado, c['v'] * lado)
    for c in P['conos']: x, y = X(c); d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=NEON)
    mx, my = X(P['mc_en']); d.ellipse([mx - 9, my - 9, mx + 9, my + 9], outline=AMBAR, width=3)
    if anillos is not None:
        for c in P['conos']:
            x, y = X(c)
            for k in range(3):
                r = ((t * 1.6 + k / 3) % 1) * 40; d.ellipse([x - r, y - r, x + r, y + r], outline=oklch(.5 + .3 * (1 - r / 40), .18, ROSA))
    return im, d
img = Image.new('RGB', (W, 760), FONDO); im, dd = valle(700); img.paste(im, (20, 40)); d = ImageDraw.Draw(img)
d.text((14, 10), f'01  el campo de conos 769: {len(P["conos"])} conos de {P["altura_media_conos_m"]:.0f} m en promedio (como tubo: la tónica); el MC en El Cerro de los Lagos', font=fn(15), fill=TXT)
for k, e in enumerate(P['ecos'][:5]):
    x0, y0 = 20 + P['mc_en']['u'] * 700, 40 + P['mc_en']['v'] * 700; x1, y1 = 20 + e['u'] * 700, 40 + e['v'] * 700
    d.line([x0, y0, x1, y1], fill=AMBAR if k < 3 else TENUE, width=2 if k < 3 else 1)
    d.text((760, 80 + 28 * k), f"{(e['nombre'] or 'un cono sin nombre').lower():<28} {e['dist_m']:>5} m → eco a {e['retraso_s']:5.1f} s{'  (suena)' if k < 3 else ''}", font=fn(13), fill=AMBAR if k < 3 else TENUE)
d.text((760, 240), 'el eco del valle: ida y vuelta a 343 m/s; más lejos, más oscuro', font=fn(12), fill=TENUE)
d.text((760, 290), 'los saludos del sonidero:', font=fn(13), fill=TXT)
for k, l in enumerate(P['lugares'][:10]): d.text((760, 314 + 20 * k), '· ' + l.lower(), font=fn(12), fill=NEON)
SONDA['eco'] = [dict(cono=e['nombre'], dist_m=e['dist_m'], retraso_s=e['retraso_s']) for e in P['ecos'][:3]]
guardar(img, f'01-valle-y-eco-s{s}-{h}.png')

# 02 · la ciudad se hunde, el disco se rebaja
img = Image.new('RGB', (W, 520), FONDO); d = ImageDraw.Draw(img)
d.text((14, 10), f'02  la ciudad se hunde (curva aproximada del centro: ~9 m de 1900 a 2026) y el disco se rebaja {P["semitonos_por_metro"]} semitonos por metro (tempo y tono juntos)', font=fn(14), fill=TXT)
x0, y0, Wd, Hd = 60, 60, W - 120, 360; t = np.linspace(P['inicio_disco'], P['fin_disco'], 600); p = np.interp(t, VS[:, 1], VS[:, 0])
def anio(pp):
    for e in P['secciones']:
        if e['t'] <= pp <= e['t1']: return e['anios'][0] + (e['anios'][1] - e['anios'][0]) * (pp - e['t']) / (e['t1'] - e['t'])
    return 2026
hund = np.array([np.interp(anio(x), [a for a, _ in P['hundimiento_m']], [b for _, b in P['hundimiento_m']]) for x in p])
X = lambda tt: x0 + tt / DUR * Wd
d.line([(X(tt), y0 + hm / 10 * Hd) for tt, hm in zip(t, hund)], fill=AGUA, width=3); d.text((X(t[-1]) - 160, y0 + hund[-1] / 10 * Hd + 8), f'{hund[-1]:.1f} m bajo 1900', font=fn(12), fill=AGUA)
bpm = P['bpm'] * 2 ** (-P['semitonos_por_metro'] * hund / 12)
d.line([(X(tt), y0 + (96 - b) / 25 * Hd) for tt, b in zip(t, bpm)], fill=NEON, width=2); d.text((X(t[-1]) - 160, y0 + (96 - bpm[-1]) / 25 * Hd - 20), f'{bpm[-1]:.1f} bpm', font=fn(12), fill=NEON)
for si in P['sirenas']: d.line([X(si['t']), y0 - 6, X(si['t']), y0 + Hd], fill=oklch(.5, .12, 30)); d.text((X(si['t']) + 2, y0 - 4), f"{si['metro']} m", font=fn(10), fill=oklch(.75, .15, 30))
secciones(d, x0, Wd, y0 + Hd + 10, y0 + Hd + 44)
# la rebajada medida: el intervalo entre bombos en tiempo real al principio y al final del dembow
kick = sorted(e['t'] for e in P['web']['bateria808'] if e.get('pieza') == 'kick'); kr = np.interp(kick, VS[:, 0], VS[:, 1]); dk = np.diff(kr)
SONDA['rebajada'] = dict(hundimiento_final_m=round(float(hund[-1]), 2), semitonos_finales=round(-P['semitonos_por_metro'] * float(hund[-1]), 2), razon_final=P['razon_final'],
                         intervalo_bombos_primero_s=round(float(dk[0]), 4), intervalo_bombos_ultimo_s=round(float(dk[-1]), 4), bpm_real_inicio=round(60 / dk[0], 1), bpm_real_final=round(60 / dk[-1], 1),
                         sirenas=[(x['metro'], x['t']) for x in P['sirenas']])
guardar(img, f'02-hundimiento-y-rebajada-s{s}-{h}.png')

# 03 · los dos relojes
img = Image.new('RGB', (W, 420), FONDO); d = ImageDraw.Draw(img)
d.text((14, 10), f'03  los dos relojes: el disco ({P["disco_s"]:.0f} s de disco) se estira a {P["fin_disco"] - P["inicio_disco"]:.0f} s reales; el MC, las sirenas y la radio van en tiempo real', font=fn(14), fill=TXT)
x0, y0, Wd, Hd = 60, 50, W - 120, 300
d.line([(x0 + tt / DUR * Wd, y0 + Hd - pp / P['disco_s'] * Hd) for pp, tt in VS], fill=NEON, width=3)
d.line([x0 + P['inicio_disco'] / DUR * Wd, y0 + Hd, x0 + (P['inicio_disco'] + P['disco_s']) / DUR * Wd, y0], fill=TENUE)
d.text((x0 + 10, y0 + 10), 'tiempo de disco (vertical) contra tiempo real (horizontal); la recta tenue: sin rebajar', font=fn(12), fill=TENUE)
secciones(d, x0, Wd, y0 + Hd + 6, y0 + Hd + 40)
guardar(img, f'03-dos-relojes-s{s}-{h}.png')

# 04 · la radio
R = P['radio']; img = Image.new('RGB', (W, 420), FONDO); d = ImageDraw.Draw(img)
d.text((14, 10), '04  la radio de onda corta (a lo Hymnen): la perilla en sus tres tramos sobre las estaciones (kHz de la banda)', font=fn(14), fill=TXT)
x0, y0, Wd, Hd = 60, 50, W - 360, 320; lo, hi = 5.5, 18
Y = lambda f: y0 + Hd - (f - lo) / (hi - lo) * Hd
COL = {'musica': AGUA, 'voz': AMBAR, 'horaria': TENUE, 'sonidero': NEON}
for e in R['estaciones']:
    d.line([x0, Y(e['f']), x0 + Wd, Y(e['f'])], fill=COL[e['tipo']]); nom = e['tipo'] if e['tipo'] != 'musica' else os.path.basename(e['fuente']).split('-s')[0]
    d.text((x0 + Wd + 10, Y(e['f']) - 7), f"{e['f']:.1f}  {nom}", font=fn(12), fill=COL[e['tipo']])
for nombre, tr in (('intro', R['intro']), ('interludio', R['interludio']), ('final', R['final'])):
    a0 = tr['desde']; d.line([(x0 + (a0 + tt) / DUR * Wd, Y(f)) for tt, f in tr['dial']], fill=TXT, width=3)
    d.text((x0 + a0 / DUR * Wd + 4, y0 + Hd + 8), nombre, font=fn(12), fill=TXT)
SONDA['radio'] = json.load(open(os.path.join(AQUI, 'sondas', 'radio.json'))) if os.path.exists(os.path.join(AQUI, 'sondas', 'radio.json')) else 'ver sondas/radio.py'
guardar(img, f'04-radio-s{s}-{h}.png')

# 05 · el tapete sobre el dembow
sys.path.insert(0, os.path.join(AQUI, '..', 'tapete-de-talbot')); import tapete as TP
img = Image.new('RGB', (W, 300), FONDO); d = ImageDraw.Draw(img)
d.text((14, 10), '05  el tapete de Talbot sobre el dembow (III, exacto): el 3-3-2 de dos compases en τ = 1/3 y 1/2', font=fn(14), fill=TXT)
golpes = [e for e in P['web']['bateria808'] if P['talbot']['loop_desde'] <= e['t'] < P['talbot']['loop_desde'] + P['talbot']['ciclo'] and e.get('pieza') in ('kick', 'snare')]
SONDA['talbot'] = {}
for fila, (_, tau) in enumerate([x for x in P['talbot']['tramos'] if x[1] != '0']):
    L, c = TP.copias(Fraction(tau).numerator, Fraction(tau).denominator); voces = [j for j in range(L) if abs(c[j]) > 1e-9]; SONDA['talbot'][tau] = [f'{j}/{L}' for j in voces]
    y = 70 + fila * 100; d.text((20, y + 6), f'τ = {tau}', font=fn(16), fill=TXT); d.line([160, y + 20, W - 40, y + 20], fill=TENUE)
    for e in golpes:
        u = (e['t'] - P['talbot']['loop_desde']) / P['talbot']['ciclo']
        for j in voces:
            x = 160 + ((u + j / L) % 1) * (W - 200); col = NEON if e['pieza'] == 'snare' else AGUA; r = 6 if e['pieza'] == 'kick' else 4
            d.ellipse([x - r, y + 20 - r, x + r, y + 20 + r], fill=col)
    d.text((160, y + 36), 'copias en ' + ', '.join(SONDA['talbot'][tau]) + '  (azul: bombo · rosa: caja)', font=fn(12), fill=TENUE)
guardar(img, f'05-talbot-dembow-s{s}-{h}.png')

# 06 · capas solas, 07 · mezcla
def leer(n, est):
    x = np.fromfile(os.path.join(RUN, n + '.f32'), dtype=np.float32).astype(float); return x.reshape(-1, 2).mean(1) if est else x
def espectro(x, alto, f0=40, f1=8000, hop=4096):
    n = 8192; fr = np.fft.rfftfreq(n, 1 / SR); win = np.hanning(n); cols = []
    for i in range(0, len(x) - n, hop): cols.append(np.abs(np.fft.rfft(x[i:i + n] * win)))
    S = np.array(cols).T; fl = np.geomspace(f0, f1, alto); M = np.array([np.interp(fl, fr, c) for c in S.T]).T
    M = 20 * np.log10(M / (M.max() + 1e-12) + 1e-9); return np.clip((M + 70) / 70, 0, 1)[::-1]
def pinta(M, col): return (M[..., None] * np.array(col)[None, None, :] + (1 - M[..., None]) * np.array(FONDO)[None, None, :]).astype(np.uint8)
CAPAS = [('guiro', 1), ('conga', 1), ('campana', 1), ('bateria808', 1), ('bajo', 0), ('teclado', 1), ('sabina-coro', 1), ('sabina-lead', 1), ('sabina-chops', 1), ('sabina-mc', 1), ('sirenas', 1), ('sabina-radio', 1), ('estacion0', 0)]
alto = 30; x0 = 170; im = Image.new('RGB', (W, 50 + (alto + 4) * len(CAPAS)), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '06  las capas solas antes de mezclar, cada una en su reloj (las del disco, sin rebajar todavía)', font=fn(14), fill=TXT)
for k, (c, st) in enumerate(CAPAS):
    col = oklch(.75, .14, ROSA + (LAGO + 360 - ROSA) * k / len(CAPAS)); y0 = 44 + k * (alto + 4)
    im.paste(Image.fromarray(pinta(espectro(leer(c, st), alto), col)).resize((W - x0 - 10, alto)), (x0, y0)); d.text((8, y0 + 8), c, font=fn(11), fill=col)
guardar(im, f'06-capas-s{s}-{h}.png')
sr, x = wavfile.read(os.path.join(OUT, os.path.basename(OUT) + '.wav')); x = x.astype(float).mean(1) / 32768
mez = Image.new('RGB', (W, 400), FONDO); mez.paste(Image.fromarray(pinta(espectro(x, 330, 30, 12000), oklch(.92, .05, ROSA))).resize((W - 20, 330)), (10, 50)); d = ImageDraw.Draw(mez)
d.text((14, 10), f'07  La ciudad se hunde bailando (s{s}): la mezcla, {len(x) / sr:.0f} s', font=fn(18), fill=TXT); secciones(d, 10, W - 20, 44, 385)
guardar(mez, f'07-mezcla-s{s}-{h}.png')

# GIF: el valle, las bocinas, el año y los metros
cuadros = []; NC = 34
for j in range(1, NC + 1):
    t = DUR * j / NC; c = Image.new('RGB', (W, 800), FONDO); im, _ = valle(380, anillos=True, t=t); c.paste(im, (20, 10)); dd = ImageDraw.Draw(c)
    if t < P['inicio_disco']: rot, an, m = 'LA RADIO BUSCA', None, 0
    elif t > P['fin_disco']: rot, an, m = 'LA RADIO SE LA LLEVA', 2026, 9
    else:
        pp = float(np.interp(t, VS[:, 1], VS[:, 0])); an = anio(pp); m = float(np.interp(an, [a for a, _ in P['hundimiento_m']], [b for _, b in P['hundimiento_m']])); rot = [NOM[k] for k, (a, z) in SEC.items() if a <= t][-1]
    dd.text((430, 30), rot, font=fn(30), fill=TXT)
    if an: dd.text((430, 90), f'{int(an)} · la ciudad bajó {m:.1f} m · el disco {-P["semitonos_por_metro"] * m:+.1f} semitonos', font=fn(18), fill=AGUA)
    c.paste(mez, (0, 400)); xx = 10 + int((W - 20) * t / DUR); dd.rectangle([xx, 450, W - 10, 780], fill=FONDO); dd.line([xx, 450, xx, 780], fill=TXT, width=2)
    cuadros.append(c.resize((1100, 518)))
gif = os.path.join(OUT, f'la-ciudad-se-hunde-bailando-s{s}-{h}.gif'); cuadros[0].save(gif, save_all=True, append_images=cuadros[1:] + [cuadros[-1]] * 2, duration=270, loop=0, optimize=True)
cuadros[-1].save(nuevo(f'08-valle-y-mezcla-s{s}-{h}.png'))
if B is None: json.dump(SONDA, open(os.path.join(OUT, 'sondas.json'), 'x', encoding='utf-8'), ensure_ascii=False, indent=1)
print(gif, os.path.getsize(gif) // 1024, 'KB'); print(json.dumps(SONDA, ensure_ascii=False))
