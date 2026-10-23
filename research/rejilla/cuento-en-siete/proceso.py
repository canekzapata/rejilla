"""Cuento en siete — PNGs de etapas y GIF del proceso.
    python proceso.py <carpeta-de-render> <carpeta-de-entrega>
01 la forma y la armonía espectral · 02 el espectro de Grisey (los parciales y su estiramiento) · 03 la invención en 7/8 ·
04 el coral del coro de vocoders · 05 el dúo de bebop (acentos contra el pulso) · 06 las capas solas · 07 un verso por el vocoder
(moduladora, portadoras, salidas) · 08 la mezcla. GIF: la partitura y la mezcla se revelan con el cursor.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import sintes as SN
RUN, OUT = sys.argv[1], sys.argv[2]; P = json.load(open(os.path.join(OUT, 'partitura.json'), encoding='utf-8'))
h = os.path.basename(OUT).rsplit('-', 1)[1]; s = P['semilla']; pr = os.path.join(OUT, 'proceso'); os.makedirs(pr, exist_ok=False)
S16 = P['semicorchea']; C = P['compases']; DUR = P['duracion']; SR = 48000; FONDO = (11, 11, 15); TXT = (238, 232, 218)
fn = lambda n: ImageFont.truetype('C:/Windows/Fonts/consola.ttf', n)
def nuevo(nombre): p = os.path.join(pr, nombre); assert not os.path.exists(p); return p
def tinta(k, n, l=.62):                                    # el tono gira (OKLCh aproximado por senos), sin paleta fija
    a = 2 * math.pi * k / max(1, n) + s * .001; return tuple(int(255 * min(1, max(0, l + .32 * math.sin(a + d)))) for d in (0, 2.1, 4.2))
SECS = {}
for c in C: a, _ = SECS.get(c[2], (c[0] * S16, 0)); SECS[c[2]] = (a, (c[0] + c[1]) * S16)
NOMBRE = dict(I='I espectro', II='II invención', III='III coro', IV='IV dúo', V='V coro', VI='VI coda')
W = 1700
def secciones(d, x0, Wd, y0, y1, t0=0, t1=DUR):
    for k, (a, z) in SECS.items():
        if a < t0 or a > t1: continue
        xa = x0 + int((a - t0) / (t1 - t0) * Wd); d.line([xa, y0, xa, y1], fill=(62, 62, 80)); d.text((xa + 4, y0 + 2), NOMBRE[k], font=fn(13), fill=(175, 175, 190))
def rollo(d, notas, x0, y0, Wd, Hd, t0, t1, lo, hi, col, marca=None):
    for n in notas:
        if not (t0 <= n[0] < t1): continue
        x = x0 + (n[0] - t0) / (t1 - t0) * Wd; x2 = x0 + min(t1, n[0] + n[1]) / 1 * 0 + (min(t1, n[0] + n[1]) - t0) / (t1 - t0) * Wd
        y = y0 + Hd - (n[2] - lo) / (hi - lo) * Hd
        d.rectangle([x, y - 2, max(x + 1, x2 - 1), y + 2], fill=col if not (marca and n[3]) else marca)
NOMBRES = 'C C# D D# E F F# G G# A A# B'.split()

# 01 · forma y armonía
im = Image.new('RGB', (W, 360), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), f'01  forma: {len(C)} compases en 7/8 (y 7/8 + 9/8 en los coros) · negra = 144 · {DUR:.0f} s · armonía espectral (ciclo de Coltrane E C G#)', font=fn(17), fill=TXT)
x0, Wd = 20, W - 40
for k, c in enumerate(C):
    xa = x0 + c[0] * S16 / DUR * Wd; xb = x0 + (c[0] + c[1]) * S16 / DUR * Wd
    d.rectangle([xa, 60, xb - 1, 90], outline=(70, 70, 88), fill=tinta(list(SECS).index(c[2]), 6, .35))
    for j in range(1, c[1]): xs = xa + j * S16 / DUR * Wd; d.line([xs, 84, xs, 90], fill=(110, 110, 130) if j % 2 == 0 else (60, 60, 75))
secciones(d, x0, Wd, 96, 120)
acs = P['acordes']['III'] + P['acordes']['V']
for a in acs:
    xa = x0 + a['t'] / DUR * Wd; nom = NOMBRES[int(round(a['fund'])) % 12] + ('·o' if a['tipo'] == 'o' else '·u')
    for m in a['tonos']:
        y = 340 - (m - 40) * 2.6; d.rectangle([xa, y - 1, xa + 9, y + 1], fill=tinta(int(round(a['fund'])) % 12, 12) if a['tipo'] == 'o' else (150, 150, 200))
    d.text((xa, 130 + 14 * (acs.index(a) % 3)), nom, font=fn(11), fill=(200, 200, 210))
d.text((20, 335), 'o = otonal (parciales 4 5 6 7 9 11 13)   u = utonal (subarmónicos: oscuro)', font=fn(12), fill=(170, 170, 185))
im.save(nuevo(f'01-forma-s{s}-{h}.png'))

# 02 · espectro (Grisey)
E = P['espectro']; t = np.linspace(0, DUR, 1400); est = np.array(E['estira']); sig = np.interp(t, est[:, 0], est[:, 1])
ce = np.array(E['coda']['estira']); m = t >= E['coda']['t0']; sig[m] = np.interp(t[m], ce[:, 0], ce[:, 1])
im = Image.new('RGB', (W, 520), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '02  el espectro de Mi1: los parciales 2–24 entran del grave al agudo y se estiran (f_k = f1·k^(1+σ), σ hasta 0.045); en la coda se recogen', font=fn(16), fill=TXT)
f1 = 41.2; fl = lambda f: 500 - (math.log2(f / 60) / math.log2(1100 / 60)) * 430
for pa in E['parciales']:
    k = pa['k']; col = tinta(k, 24)
    for i in range(len(t) - 1):
        vivo = (t[i] >= pa['t'] and t[i] < SECS['II'][0]) or (t[i] >= E['coda']['t0'])
        if not vivo: continue
        x = 20 + t[i] / DUR * (W - 40); f = f1 * k ** (1 + sig[i]); d.point((x, fl(f)), fill=col); d.point((x, fl(f) + 1), fill=col)
    d.text((W - 60, fl(f1 * k) - 6), str(k), font=fn(10), fill=col)
secciones(d, 20, W - 40, 40, 510); im.save(nuevo(f'02-espectro-s{s}-{h}.png'))

# 03 · invención
a, z = SECS['II']; im = Image.new('RGB', (W, 420), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '03  invención a dos voces en 7/8: sujeto, respuesta, la cabeza por E C G#, hoquetus, estrecho, 5 contra 7, aumentación (la fuga se estira 3 %)', font=fn(16), fill=TXT)
pl = [(e['t'], e['dur'], e['midi'], 0) for e in P['web']['pluck']]; ma = [(e['t'], e['dur'], e['midi'], 0) for e in P['web']['marimba']]
rollo(d, pl, 20, 50, W - 40, 340, a, z, 36, 92, tinta(1, 6)); rollo(d, ma, 20, 50, W - 40, 340, a, z, 36, 92, tinta(4, 6))
for c in C:
    if c[2] == 'II': xa = 20 + (c[0] * S16 - a) / (z - a) * (W - 40); d.line([xa, 45, xa, 395], fill=(55, 55, 70)); d.text((xa + 3, 398), str(c[3]), font=fn(11), fill=(150, 150, 165))
d.text((20, 30), 'pluck (tapping)', font=fn(12), fill=tinta(1, 6)); d.text((180, 30), 'marimba', font=fn(12), fill=tinta(4, 6))
im.save(nuevo(f'03-invencion-s{s}-{h}.png'))

# 04 · coral
a, z = SECS['III']; im = Image.new('RGB', (W, 470), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '04  el coral (III): cuatro voces, cuatro acordes por verso. Sabina canta la soprano y modula: pájaro · agua · berimbau · arpa de boca · sinte', font=fn(16), fill=TXT)
PORT = dict(S='soprano → pájaro (siringe) + sinte', A='contralto → voz de agua', T='tenor → berimbau', B='bajo → lengüeta del arpa de boca')
for k, v in enumerate('SATB'):
    col = tinta(k, 4); rollo(d, [(e['t'], e['dur'], e['nota'], 0) for e in P['coro']['III'][v]], 20, 50, W - 40, 360, a, z, 34, 80, col); d.text((20 + 330 * k, 440), PORT[v], font=fn(12), fill=col)
for e in P['coro']['III']['S']:
    x = 20 + (e['t'] - a) / (z - a) * (W - 40); y = 50 + 360 - (e['nota'] - 34) / 46 * 360; d.text((x, y - 18), e['texto'], font=fn(12), fill=TXT)
im.save(nuevo(f'04-coral-s{s}-{h}.png'))

# 05 · dúo: el rollo y dónde caen los acentos
a, z = SECS['IV']; im = Image.new('RGB', (W, 560), FONDO); d = ImageDraw.Draw(im)
sx = [(e['t'], e['dur'], e['m'], e['v'] >= 1) for e in P['sax']]; si = [(e['t'], e['dur'], e['m'], e['v'] >= 1) for e in P['sinte']]
def lugar(tq):
    for c in reversed(C):
        if c[0] * S16 <= tq + 1e-6: return (tq / S16 - c[0])
acc = [lugar(n[0]) for n in sx + si if n[3] and a <= n[0] < z]
fuera = sum(1 for p in acc if abs(p - round(p)) > .05 or int(round(p)) % 2 == 1) / max(1, len(acc))
fuera_t = sum(1 for p in acc if round(p) % 14 not in (0, 4, 8)) / max(1, len(acc))
d.text((14, 10), f'05  dúo sinte–sax (IV): {len(sx)} + {len(si)} notas. Acentos fuera del pulso de corcheas: {100 * fuera:.0f} %; fuera de los tiempos del 2+2+3: {100 * fuera_t:.0f} %', font=fn(16), fill=TXT)
rollo(d, sx, 20, 50, W - 40, 320, a, z, 46, 90, tinta(0, 5, .5), marca=tinta(0, 5, .85)); rollo(d, si, 20, 50, W - 40, 320, a, z, 46, 90, tinta(3, 5, .5), marca=tinta(3, 5, .85))
for c in C:
    if c[2] == 'IV': xa = 20 + (c[0] * S16 - a) / (z - a) * (W - 40); d.line([xa, 45, xa, 375], fill=(55, 55, 70))
d.text((20, 30), 'sax (claro = acento)', font=fn(12), fill=tinta(0, 5, .85)); d.text((230, 30), 'sinte', font=fn(12), fill=tinta(3, 5, .85))
hist = np.zeros(14 * 3)
for p in acc: hist[int(round(p * 3)) % 42] += 1
d.text((20, 395), 'dónde caen los acentos dentro del 7/8 (en tercios de semicorchea; las rayas largas son 2+2+3)', font=fn(13), fill=(190, 190, 200))
for i, v in enumerate(hist):
    x = 40 + i * 38; hgt = v / max(1, hist.max()) * 120; d.rectangle([x, 540 - hgt, x + 30, 540], fill=tinta(i % 3, 3, .55))
    if i % 3 == 0: d.text((x + 8, 543 - 0), str(i // 3), font=fn(10), fill=(150, 150, 165))
for b in (0, 4, 8): d.line([40 + b * 3 * 38 - 4, 415, 40 + b * 3 * 38 - 4, 540], fill=(200, 200, 215), width=2)
im.save(nuevo(f'05-duo-bebop-s{s}-{h}.png'))

# 06 · capas solas
def espectro(x, alto, fmax=12000, hop=1024):
    N = 2048; win = np.hanning(N); fr = [np.abs(np.fft.rfft(x[i:i + N] * win)) for i in range(0, len(x) - N, hop)]
    Sx = 20 * np.log10(np.array(fr).T + 1e-9); f = np.fft.rfftfreq(N, 1 / SR); filas = np.geomspace(40, fmax, alto)[::-1]
    img = Sx[np.searchsorted(f, filas)]; return np.clip((img - (img.max() - 65)) / 65, 0, 1)
def pinta(img, col): return (np.power(img[..., None], 1.3) * np.array(col) + np.array(FONDO) * (1 - img[..., None])).astype(np.uint8)
capas = [(c, True) for c in P['web'] if P['web'][c]] + [(c, False) for c in ['sax', 'aves', 'aves-coro', 'agua', 'waterphone', 'gong', 'trombon', 'tambor', 'barra', 'vozagua']] + [('sabina-soprano', True)]
alto = 44; x0 = 150; im = Image.new('RGB', (W, 50 + (alto + 5) * len(capas)), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '06  las capas solas, antes de mezclar (espectrogramas 40 Hz–12 kHz): navegador, objetos que cantan, Sabina', font=fn(17), fill=TXT)
for k, (c, st) in enumerate(capas):
    x = np.fromfile(os.path.join(RUN, c + '.f32'), dtype=np.float32).astype(float); x = x.reshape(-1, 2).mean(1) if st else x
    col = tinta(k, len(capas)); y0 = 46 + k * (alto + 5); im.paste(Image.fromarray(pinta(espectro(x, alto, hop=2048), col)).resize((W - x0 - 10, alto)), (x0, y0)); d.text((8, y0 + 14), c, font=fn(12), fill=col)
secciones(d, x0, W - x0 - 10, 36, im.height - 4); im.save(nuevo(f'06-capas-s{s}-{h}.png'))

# 07 · un verso por el vocoder (el primero del III): la moduladora, una portadora y su salida
vv = P['coro']['III']['S'][:12]; t0, t1 = vv[0]['t'] - .1, vv[-1]['t'] + vv[-1]['dur'] + .2; a, b = int(t0 * SR), int(t1 * SR)
sab = np.fromfile(os.path.join(RUN, 'sabina-soprano.f32'), dtype=np.float32).astype(float).reshape(-1, 2).mean(1)[a:b]
filas = [('Sabina (moduladora)', sab)]
for nombre, archivo, st in [('pájaro de siringe', 'aves-coro', False), ('berimbau del tenor', 'berimbau-coro', True), ('arpa de boca', 'arpaboca-coro', True)]:
    car = np.fromfile(os.path.join(RUN, archivo + '.f32'), dtype=np.float32).astype(float); car = (car.reshape(-1, 2).mean(1) if st else car)[a:b]
    filas += [(nombre + ' (portadora)', car), (nombre + ' → vocoder', SN.vocoder(sab, car, suaviza=1 if 'berimbau' in nombre else 3))]
alto = 70; im = Image.new('RGB', (W, 50 + (alto + 6) * len(filas)), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '07  «cuen to en sie te y me so bra el a gua» por el vocoder: la envolvente de Sabina en 30 bandas sobre cada portadora blanqueada', font=fn(16), fill=TXT)
for k, (nombre, x) in enumerate(filas):
    col = tinta(k // 2 + (k > 0), 4, .65); y0 = 46 + k * (alto + 6)
    im.paste(Image.fromarray(pinta(espectro(x, alto, 9000, 256), col)).resize((W - 260, alto)), (250, y0)); d.text((8, y0 + 26), nombre, font=fn(12), fill=col)
im.save(nuevo(f'07-vocoder-s{s}-{h}.png'))

# 08 · mezcla
sr, x = wavfile.read(os.path.join(OUT, os.path.basename(OUT) + '.wav')); x = x.astype(float).mean(1) / 32768
img = espectro(x, 330); mez = Image.new('RGB', (W, 400), FONDO); mez.paste(Image.fromarray(pinta(img, (236, 228, 214))).resize((W - 20, 330)), (10, 50)); d = ImageDraw.Draw(mez)
d.text((14, 10), f'08  Cuento en siete (s{s}): la mezcla, {len(x) / sr:.0f} s', font=fn(18), fill=TXT); secciones(d, 10, W - 20, 44, 385)
mez.save(nuevo(f'08-mezcla-s{s}-{h}.png'))

# GIF: arriba la partitura (todas las notas, coloreadas por capa), abajo la mezcla; el cursor las revela (≈ 9.6 s)
roll = Image.new('RGB', (W, 300), FONDO); d = ImageDraw.Draw(roll)
grupos = [('pluck', [(e['t'], e['dur'], e['midi'], 0) for e in P['web']['pluck']]), ('marimba', [(e['t'], e['dur'], e['midi'], 0) for e in P['web']['marimba']]),
          ('coro', [(e['t'], e['dur'], e['nota'], 0) for v in 'SATB' for e in P['coro']['III'][v] + P['coro']['V'][v]]), ('sax', [(e['t'], e['dur'], e['m'], 0) for e in P['sax']]),
          ('sinte', [(e['t'], e['dur'], e['m'], 0) for e in P['sinte']]), ('bajo', [(e['t'], e['dur'], e['midi'], 0) for e in P['web']['bajo']]),
          ('aves', [(a_['t'], a_.get('dur', .3), a_.get('m', a_.get('notas', [[0, 90]])[0][1]) - 24, 0) for a_ in P['aves']])]
for k, (g, ns) in enumerate(grupos): rollo(d, ns, 10, 20, W - 20, 270, 0, DUR, 28, 100, tinta(k, len(grupos), .6))
secciones(d, 10, W - 20, 2, 298)
lienzo = Image.new('RGB', (W, 700), FONDO); lienzo.paste(roll, (0, 0)); lienzo.paste(mez, (0, 300))
cuadros = []
for j in range(1, 33):
    c = lienzo.copy(); dd = ImageDraw.Draw(c); xx = 10 + int((W - 20) * j / 32)
    dd.rectangle([xx, 20, W - 10, 290], fill=FONDO); dd.rectangle([xx, 350, W - 10, 680], fill=FONDO); dd.line([xx, 20, xx, 680], fill=TXT, width=2)
    cuadros.append(c.resize((1100, 453)))
gif = os.path.join(OUT, f'cuento-en-siete-s{s}-{h}.gif'); cuadros[0].save(gif, save_all=True, append_images=cuadros[1:] + [cuadros[-1]] * 3, duration=275, loop=0, optimize=True)
lienzo.save(nuevo(f'09-partitura-y-mezcla-s{s}-{h}.png'))
print(gif, os.path.getsize(gif) // 1024, 'KB', '· acentos fuera del pulso', round(100 * fuera), '%', '· fuera de 2+2+3', round(100 * fuera_t), '%')
