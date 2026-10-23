"""Proceso del loop B de «suma uno». Carpeta exclusiva proceso/suma-uno-<id12>/ con el id de la entrega.

  01  el espectrograma de la mezcla, con las secciones: clúster → La mayor → pop → la improbable → sorpresa → regreso
  02  las medidas: bandas por sección, voz sobre el resto, afinación
  GIF la creencia del modelo cambiando: las 12 barras de la predicción, la nota elegida y la entropía (≤ 10 s)
    python proceso_pieza.py e1 f02c58d9e0a0 e1-mezcla-v2
"""
import json, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
AQUI = Path(__file__).resolve().parent
ET, C, MEZ = sys.argv[1], sys.argv[2], sys.argv[3]
R = AQUI / 'render'
MED = json.load(open(R / f'{MEZ}-medidas.json', encoding='utf-8'))['secciones']; VOC = json.load(open(R / f'{ET}-voces.json', encoding='utf-8'))
js = ("require('./motor/cancion.js'); const C = globalThis.Cancion;"
      "console.log(JSON.stringify({M: C.modelo().map(e => ({p: e.p, pc: e.pc, tipo: e.tipo, sec: e.sec, prob: e.prob, s: e.s, H: e.H, dist: e.dist})), SECC: C.SECC, P16: C.P16}));")
D = json.loads(subprocess.run(['node', '-e', js], cwd=AQUI, capture_output=True, text=True, encoding='utf-8', check=True).stdout)
SAL = AQUI / 'proceso' / f'suma-uno-{C}'; os.mkdir(SAL)


def oklch(L, Cc, hh):
    a, b = Cc * np.cos(np.radians(hh)), Cc * np.sin(np.radians(hh))
    l_, m_, s_ = L + .3963377774 * a + .2158037573 * b, L - .1055613458 * a - .0638541728 * b, L - .0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    rgb = np.clip([4.0767416621 * l - 3.3077115913 * m + .2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - .3413193965 * s,
                   -.0041960863 * l - .7034186147 * m + 1.7076147010 * s], 0, 1)
    rgb = np.where(rgb <= .0031308, 12.92 * rgb, 1.055 * rgb ** (1 / 2.4) - .055)
    return tuple(int(round(c * 255)) for c in rgb)


def fuente(n):
    try: return ImageFont.truetype('C:/Windows/Fonts/consola.ttf', n)
    except OSError: return ImageFont.load_default()


h0 = int(C[:4], 16) % 360
FONDO, TXT, TEN, REJ = oklch(.13, .02, h0), oklch(.92, .03, h0), oklch(.55, .04, h0), oklch(.25, .03, h0)
F, Fs, Fg = fuente(14), fuente(12), fuente(22)
NOM = ['Do', 'Do#', 'Re', 'Mib', 'Mi', 'Fa', 'Fa#', 'Sol', 'Lab', 'La', 'Sib', 'Si']
M, SECC, P16 = D['M'], D['SECC'], D['P16']; W = 1500


def png(im, n):
    with open(SAL / n, 'xb') as f: im.save(f, 'PNG')


# 01 espectrograma
sr, x = wavfile.read(R / f'{MEZ}.wav'); x = x.mean(axis=1)
N, hop = 4096, 1200; cols = [np.abs(np.fft.rfft(x[a:a + N] * np.hanning(N))) for a in range(0, len(x) - N, hop)]
S = 20 * np.log10(np.array(cols).T + 1e-7); fr = np.fft.rfftfreq(N, 1 / sr)
S = S[np.searchsorted(fr, np.geomspace(40, 9000, 400))]; S = np.clip((S - S.max() + 72) / 72, 0, 1)
im = Image.new('RGB', (W, 540), FONDO); d = ImageDraw.Draw(im)
d.text((24, 16), 'la mezcla (40 Hz - 9 kHz, logarítmica): clúster · la evidencia · el pop · la improbable · sorpresa · inferencia', fill=TXT, font=Fg)
esp = Image.fromarray((S[::-1] * 255).astype(np.uint8)).resize((W - 100, 420), Image.BILINEAR)
im.paste(Image.composite(Image.new('RGB', esp.size, oklch(.86, .1, h0 + 60)), Image.new('RGB', esp.size, FONDO), esp), (60, 80))
dur = len(x) / sr; Xs = lambda t: 60 + (W - 100) * t / dur
for s in SECC: d.line([(Xs(s['a'] * P16), 60), (Xs(s['a'] * P16), 510)], fill=REJ); d.text((Xs(s['a'] * P16) + 4, 60), s['n'], fill=TEN, font=Fs)
png(im, f'01-espectrograma-{C}.png')

# 02 medidas
im = Image.new('RGB', (W, 420), FONDO); d = ImageDraw.Draw(im)
d.text((24, 16), 'medidas: bandas por sección (dB respecto al total), voz sobre el resto y afinación', fill=TXT, font=Fg)
bandas = ['sub', 'graves', 'medios', 'presencia', 'aire']
for j, b in enumerate(bandas): d.text((240 + 110 * j, 60), b, fill=TEN, font=F)
d.text((800, 60), 'total', fill=TEN, font=F); d.text((900, 60), 'voz − resto', fill=TEN, font=F)
for i, s in enumerate(SECC):
    y = 90 + 34 * i; m = MED[s['n']]; d.text((30, y), s['n'], fill=TXT, font=F)
    for j, b in enumerate(bandas):
        w = max(2, 100 * (1 + m[b] / 40)); d.rectangle([240 + 110 * j, y, 240 + 110 * j + w * .9, y + 18], fill=oklch(.62, .1, h0 + 30 * j))
        d.text((244 + 110 * j, y + 2), f'{m[b]:.0f}', fill=FONDO, font=Fs)
    d.text((800, y), f"{m['total_dB']:.1f}", fill=TXT, font=F); d.text((900, y), f"{m['voz_sobre_resto_dB']:+.1f} dB", fill=TXT, font=F)
y = 290
for p in ('ardilla', 'grave'):
    v = VOC[p]; d.text((30, y), f"{p}: {v['palabras']} sílabas, mediana {v['mediana_cents']} cents, {v['a_mas_de_50']} a más de 50", fill=TXT, font=F); y += 26
png(im, f'02-medidas-{C}.png')

# GIF: la creencia cambiando (60 cuadros, 160 ms = 9.6 s)
frames = []
for k in range(60):
    p = (k + .5) / 60 * 1300; e = [q for q in M if q['p'] <= p][-1]
    im = Image.new('RGB', (720, 420), FONDO); d = ImageDraw.Draw(im)
    d.text((20, 14), f"{e['sec']} · lo que el modelo cree que sigue", fill=TXT, font=F)
    d.text((20, 36), f"entropía {e['H']:.2f} bits · eligió {NOM[e['pc']]} (p = {e['prob']:.3f}, sorpresa {e['s']:.1f} bits)", fill=TEN, font=Fs)
    for pc in range(12):
        x0 = 30 + pc * 56; hgt = 300 * e['dist'][pc] / max(e['dist'])
        col = oklch(.5 + .4 * e['dist'][pc] / max(e['dist']), .12, h0 + 40 + pc * 10)
        d.rectangle([x0, 370 - hgt, x0 + 44, 370], fill=col)
        if pc == e['pc']: d.rectangle([x0 - 3, 370 - hgt - 3, x0 + 47, 373], outline=TXT, width=2)
        d.text((x0 + 8, 380), NOM[pc], fill=TEN, font=Fs)
    d.rectangle([30, 404, 30 + 660 * p / 1300, 408], fill=TEN)
    frames.append(im)
pal = frames[30].quantize(colors=64, method=Image.Quantize.MEDIANCUT)
frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
gif = AQUI / f'la-creencia-{C}.gif'
with open(gif, 'xb') as fh: frames[0].save(fh, 'GIF', save_all=True, append_images=frames[1:], duration=160, loop=0, optimize=True)
print(C, f'gif {gif.stat().st_size / 1e6:.2f} MB {160 * len(frames) / 1000:.1f} s')
