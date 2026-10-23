"""Láminas y GIF de «planeta 9» en la carpeta de la entrega (la crea mezcla.py --entregar):
  01  el planeta: la serie armónica de Sol1 con las potencias de 2 tachadas, y el espectro real de la coda (nada en 49, 98, 196 Hz)
  02  la forma: entropía H(t), secciones, los planetas ausentes (la línea punteada) y la melodía
  03  la canción: espectrograma (log) con la fundamental ausente punteada debajo
  GIF el espectrograma dibujándose, con el planeta punteado
    python proceso_planeta9.py <render/VER.wav> <proceso/planeta-9-id>
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
AQUI = Path(__file__).resolve().parent; WAV = Path(sys.argv[1]); SAL = Path(sys.argv[2]); C = SAL.name.split('-')[-1]
J = json.loads(subprocess.run(['node', '-e', "require('./motor/cancion.js');const C=globalThis.Cancion;const H=[];for(let b=0;b<=70;b+=.125)H.push(C.entropia(b));"
                               "console.log(JSON.stringify({A:C.acordes(),S:C.SECC,T:C.T,H,P:C.partitura()}))"], capture_output=True, text=True, encoding='utf-8', cwd=AQUI).stdout)
T, A, S = J['T'], J['A'], J['S']


def oklch(L, Cc, hh):
    a, b = Cc * np.cos(np.radians(hh)), Cc * np.sin(np.radians(hh))
    l_, m_, s_ = L + .3963377774 * a + .2158037573 * b, L - .1055613458 * a - .0638541728 * b, L - .0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    rgb = np.clip([4.0767416621 * l - 3.3077115913 * m + .2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - .3413193965 * s,
                   -.0041960863 * l - .7034186147 * m + 1.7076147010 * s], 0, 1)
    rgb = np.where(rgb <= .0031308, 12.92 * rgb, 1.055 * rgb ** (1 / 2.4) - .055)
    return tuple(int(round(c * 255)) for c in rgb)


try: F, Fg = (ImageFont.truetype('C:/Windows/Fonts/consola.ttf', k) for k in (14, 22))
except OSError: F = Fg = ImageFont.load_default()
h0 = 250 + int(C[:4], 16) % 60                                       # azules-violetas de hielo lejano, derivados del id
FONDO, TXT, TEN, FRIO, CALIDO = oklch(.11, .02, h0), oklch(.92, .02, h0), oklch(.5, .04, h0), oklch(.8, .12, h0), oklch(.8, .13, h0 + 150)
W = 1500
png = lambda im, n: im.save(open(SAL / n, 'xb'), 'PNG')
sr, x = wavfile.read(WAV); x = x.astype(float); m = x.mean(axis=1) if x.ndim > 1 else x
hz = lambda mm: 440 * 2 ** ((mm - 69) / 12)

# 01 el planeta
im = Image.new('RGB', (W, 640), FONDO); dr = ImageDraw.Draw(im)
dr.text((24, 16), 'el planeta: la serie armónica de Sol1 (49 Hz). Las potencias de 2 (1, 2, 4, 8, 16) no suenan nunca: el oído deduce el 1', fill=TXT, font=Fg)
X = lambda f: 80 + (W - 120) * np.log(f / 40) / np.log(1800 / 40)
for n in range(1, 31):
    f = 49 * n; xx = X(f); pot = n & (n - 1) == 0
    if f > 1800: break
    dr.line([(xx, 120), (xx, 230)], fill=TEN if pot else FRIO, width=3)
    if pot: dr.line([(xx - 9, 160), (xx + 9, 190)], fill=CALIDO, width=3); dr.line([(xx - 9, 190), (xx + 9, 160)], fill=CALIDO, width=3)
    if n <= 16 or n in (18, 20, 24, 30): dr.text((xx - 6, 236), str(n), fill=CALIDO if pot else TXT, font=F)
dr.text((80, 90), 'armónicos de 49 Hz (escala log): azul = puede sonar · tachado = la clase del planeta', fill=TEN, font=F)
a, b = int(66.2 * T * sr), int(69.5 * T * sr); s = m[a:b]; E = np.abs(np.fft.rfft(s * np.hanning(len(s)))) ** 2; fr = np.fft.rfftfreq(len(s), 1 / sr)
ok = (fr > 40) & (fr < 1800); dbs = 10 * np.log10(E[ok] / E[ok].max() + 1e-12); y0 = 600
pts = [(X(f), y0 - 300 * max(0, (d + 70) / 70)) for f, d in zip(fr[ok][::3], dbs[::3])]
dr.line(pts, fill=FRIO, width=1)
for f in (49, 98, 196, 392, 784, 1568):                            # punteadas y rotuladas: con raya continua parecían picos
    for yy in range(305, y0, 10): dr.line([(X(f), yy), (X(f), yy + 4)], fill=CALIDO, width=1)
    dr.text((X(f) + 3, 306), f'{f}', fill=CALIDO, font=F)
dr.polygon(pts + [(pts[-1][0], y0), (pts[0][0], y0)], fill=oklch(.3, .06, h0)); dr.line(pts, fill=FRIO, width=1)
dr.text((80, 280), 'el espectro real de la coda (70 dB de rango). Punteado: 49, 98, 196, 392, 784, 1568 Hz — ahí no hay nada (−54 a −60 dB); el oído oye 49', fill=TEN, font=F)
png(im, f'01-el-planeta-{C}.png')

# 02 la forma
im = Image.new('RGB', (W, 700), FONDO); dr = ImageDraw.Draw(im)
dr.text((24, 16), 'la forma: la entropía H (arriba), los planetas ausentes (punteado) y la melodía (aguda / grave)', fill=TXT, font=Fg)
Xb = lambda bb: 60 + (W - 100) * bb / 70
H = J['H']; dr.line([(Xb(i * .125), 170 - 100 * h) for i, h in enumerate(H)], fill=CALIDO, width=3)
dr.text((12, 66), 'H 1', fill=TEN, font=F); dr.text((12, 162), 'H 0', fill=TEN, font=F)
for ns, b0, b1 in S: dr.line([(Xb(b0), 190), (Xb(b0), 680)], fill=TEN); dr.text((Xb(b0) + 4, 192), ns, fill=TEN, font=F)
Ym = lambda mm: 680 - (mm - 18) / (82 - 18) * 450
for (b0, fm, _), (b1, _, _) in zip(A[:-1], A[1:]):
    for xx in np.arange(Xb(b0), Xb(b1), 8): dr.line([(xx, Ym(fm)), (xx + 4, Ym(fm))], fill=CALIDO, width=2)
for r in J['P']:
    for e in r['eventos']:
        dr.line([(Xb(e['t'] / T), Ym(e['nota'])), (Xb((e['t'] + e['dur']) / T), Ym(e['nota']))], fill=FRIO if r['quien'] == 'A' else oklch(.7, .1, h0 + 40), width=3)
png(im, f'02-la-forma-{C}.png')

# 03 la canción + GIF
N = 8192; hop = len(m) // 1440; cols = [np.abs(np.fft.rfft(m[i:i + N] * np.hanning(N))) for i in range(0, len(m) - N, hop)]
Sg = 20 * np.log10(np.array(cols).T + 1e-9); fr = np.fft.rfftfreq(N, 1 / sr); FMIN, FMAX = 20, 8000; alto = 470
Sg = Sg[np.searchsorted(fr, np.geomspace(FMIN, FMAX, alto))]; Sg = np.clip((Sg - Sg.max() + 75) / 75, 0, 1)[::-1]
dur = len(m) / sr; Yf = lambda f: alto - 1 - (alto - 1) * np.log(f / FMIN) / np.log(FMAX / FMIN)
def lamina(hasta, ancho, alto_t, titulo=True):
    top = 60 if titulo else 10; im = Image.new('RGB', (ancho, alto + top + 20), FONDO); dr = ImageDraw.Draw(im)
    if titulo: dr.text((20, 14), 'la canción (20 Hz - 8 kHz, log). Punteado: el planeta de cada compás, que nunca suena', fill=TXT, font=Fg)
    w = max(2, int((ancho - 40) * min(1, hasta / dur))); k = max(1, int(Sg.shape[1] * min(1, hasta / dur)))
    msk = Image.fromarray((Sg[:, :k] * 255).astype(np.uint8)).resize((w, alto), Image.BILINEAR)
    im.paste(Image.composite(Image.new('RGB', msk.size, FRIO), Image.new('RGB', msk.size, FONDO), msk), (20, top))
    for (b0, fm, _), (b1, _, _) in zip(A[:-1], A[1:]):
        t0, t1 = b0 * T, min(b1 * T, hasta)
        if t0 >= hasta: break
        yy = top + Yf(hz(fm)); x0, x1 = 20 + (ancho - 40) * t0 / dur, 20 + (ancho - 40) * t1 / dur
        for xx in np.arange(x0, x1, 7): dr.line([(xx, yy), (min(x1, xx + 3), yy)], fill=CALIDO, width=2)
    return im
png(lamina(dur, W, 0), f'03-la-cancion-{C}.png')
frames = [lamina(t, 760, 0, False) for t in np.linspace(3, dur, 40)]
pal = frames[-1].quantize(colors=96, method=Image.Quantize.MEDIANCUT); frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
gif = SAL / f'el-planeta-que-no-suena-{C}.gif'
with open(gif, 'xb') as fh: frames[0].save(fh, 'GIF', save_all=True, append_images=frames[1:] + [frames[-1]] * 6, duration=200, loop=0, optimize=True)
print(C, f'gif {gif.stat().st_size / 1e6:.2f} MB {200 * (len(frames) + 6) / 1000:.1f} s')
