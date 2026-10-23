"""Láminas y GIF de «una sola línea» en la carpeta de la entrega (la crea mezcla.py --entregar):
  01  el saludo como partitura: espectrograma lineal (0-4 kHz) de la intro, con los cinco tiempos del libro
  02  la forma: quién tiene la línea (la red o la voz), la velocidad / el tempo y quién canta
  03  la canción: espectrograma (log) con las secciones
  GIF la línea: el espectrograma de la canción dibujándose, con el estado de la línea arriba
    python proceso_linea.py <render/VER.wav> <proceso/una-sola-linea-id>
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
AQUI = Path(__file__).resolve().parent; WAV = Path(sys.argv[1]); SAL = Path(sys.argv[2]); C = SAL.name.split('-')[-1]
J = json.loads(subprocess.run(['node', '-e', "require('./motor/cancion.js');const C=globalThis.Cancion;console.log(JSON.stringify({S:C.SECC,T:C.T,M:C.MAPA,P:C.partitura(),N:C.COMPASES}))"],
                              capture_output=True, text=True, encoding='utf-8', cwd=AQUI).stdout)
T, N = J['T'], J['N']


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
h0 = 120 + int(C[:4], 16) % 50                                       # verde de monitor CRT (fósforo), derivado del id
FONDO, TXT, TEN, FOS, AMBAR = oklch(.12, .02, h0), oklch(.9, .08, h0), oklch(.5, .05, h0), oklch(.82, .17, h0), oklch(.8, .14, 70)
W = 1500; png = lambda im, n: im.save(open(SAL / n, 'xb'), 'PNG')
sr, x = wavfile.read(WAV); m = x.astype(float).mean(axis=1)


def espectro(s, ancho, alto, fmin, fmax, log, N_=2048, rango=70):
    hop = max(32, len(s) // ancho); cols = [np.abs(np.fft.rfft(s[i:i + N_] * np.hanning(N_))) for i in range(0, len(s) - N_, hop)]
    S = 20 * np.log10(np.array(cols).T + 1e-9); fr = np.fft.rfftfreq(N_, 1 / sr)
    ejes = np.geomspace(fmin, fmax, alto) if log else np.linspace(fmin, fmax, alto)
    S = S[np.searchsorted(fr, ejes)]; S = np.clip((S - S.max() + rango) / rango, 0, 1)[::-1]
    msk = Image.fromarray((S * 255).astype(np.uint8)).resize((ancho, alto), Image.BILINEAR)
    return Image.composite(Image.new('RGB', (ancho, alto), FOS), Image.new('RGB', (ancho, alto), FONDO), msk)


# 01 el saludo como partitura
im = Image.new('RGB', (W, 640), FONDO); dr = ImageDraw.Draw(im)
dr.text((24, 16), 'el saludo del módem como partitura (0-4 kHz, lineal): tono / pregunta / respuesta / acuerdo / arena', fill=TXT, font=Fg)
im.paste(espectro(m[:int(8 * T * sr)], W - 60, 500, 0, 4000, False, 4096), (30, 80)); dr = ImageDraw.Draw(im)
for nom, b0, b1 in (('tono 425 Hz', 0, 1), ('pregunta: DTMF + timbre', 1, 2), ('respuesta: ANSam 2100 Hz', 2, 3.6), ('acuerdo: V.8, INFO, sondeo', 3.65, 5.8), ('arena', 5.9, 8)):
    xx = 30 + (W - 60) * b0 / 8; dr.line([(xx, 80), (xx, 580)], fill=AMBAR); dr.text((xx + 4, 586), nom, fill=AMBAR, font=F)
for f in (425, 2100): dr.text((W - 90, 80 + 500 * (1 - f / 4000) - 8), f'{f} Hz', fill=TEN, font=F)
png(im, f'01-el-saludo-{C}.png')

# 02 la forma
im = Image.new('RGB', (W, 520), FONDO); dr = ImageDraw.Draw(im)
dr.text((24, 16), 'la forma: quién tiene la línea, a qué velocidad, y quién canta', fill=TXT, font=Fg)
X = lambda b: 140 + (W - 180) * b / N
ESTADO = {'nada': ('', TEN), 'arena': ('saludo', AMBAR), 'trip': ('14 400 · 84 bpm', FOS), 'dnb': ('28 800 · 168', FOS), 'dnb2': ('33 600 · 168', FOS),
          'atasco': ('atasco ×3', AMBAR), 'escobilla': ('LA VOZ: llamada', oklch(.8, .14, 20))}
dr.text((12, 80), 'la línea', fill=TEN, font=F)
for b, mm in enumerate(J['M']):
    nom, col = ESTADO[mm['kit']]; y = 70 if mm['kit'] in ('trip', 'atasco') else 60 if mm['kit'] != 'escobilla' else 90
    if nom: dr.rectangle([X(b), 74, X(b + 1) - 1, 104], fill=col)
    if nom and (b == 0 or J['M'][b - 1]['kit'] != mm['kit']): dr.text((X(b) + 3, 108), nom, fill=col, font=F)
for ns, b0, b1 in J['S']: dr.line([(X(b0), 140), (X(b0), 500)], fill=TEN); dr.text((X(b0) + 3, 142), ns, fill=TEN, font=F)
fila = {'A': 220, 'G': 330, 'T': 430}; dr.text((12, 212), 'aguda', fill=TXT, font=F); dr.text((12, 322), 'grave', fill=TXT, font=F); dr.text((12, 422), 'Doina (tel.)', fill=TXT, font=F)
for r in J['P']:
    for e in r['eventos']:
        y = fila[r['quien']] - (e['nota'] - 60) * 3; dr.line([(X(e['t'] / T), y), (X((e['t'] + e['dur']) / T), y)], fill=FOS if r['quien'] != 'T' else AMBAR, width=3)
png(im, f'02-la-forma-{C}.png')

# 03 la canción + GIF
im = Image.new('RGB', (W, 560), FONDO); im.paste(espectro(m, W - 40, 460, 40, 12000, True, 4096, 75), (20, 70)); dr = ImageDraw.Draw(im)
dr.text((24, 16), 'la canción (40 Hz - 12 kHz, log): la red y la voz se disputan el mismo cable', fill=TXT, font=Fg)
for ns, b0, b1 in J['S']: xx = 20 + (W - 40) * b0 / N; dr.line([(xx, 70), (xx, 530)], fill=AMBAR); dr.text((xx + 3, 534), ns, fill=AMBAR, font=F)
png(im, f'03-la-cancion-{C}.png')
completo = espectro(m, 740, 340, 40, 12000, True, 2048, 75)
frames = []
for t in np.linspace(3, len(m) / sr, 40):
    fr_ = Image.new('RGB', (760, 380), FONDO); w = max(2, int(740 * t / (len(m) / sr))); fr_.paste(completo.crop((0, 0, w, 340)), (10, 30)); d = ImageDraw.Draw(fr_)
    b = min(N - 1, int(t / T)); nom, col = ESTADO[J['M'][b]['kit']]; d.text((12, 6), (nom or '…') + f'   {int(t // 60)}:{int(t % 60):02d}', fill=col, font=F)
    frames.append(fr_)
pal = frames[-1].quantize(colors=96, method=Image.Quantize.MEDIANCUT); frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
gif = SAL / f'la-red-y-la-voz-{C}.gif'
with open(gif, 'xb') as fh: frames[0].save(fh, 'GIF', save_all=True, append_images=frames[1:] + [frames[-1]] * 6, duration=200, loop=0, optimize=True)
print(C, f'gif {gif.stat().st_size / 1e6:.2f} MB {200 * (len(frames) + 6) / 1000:.1f} s')
