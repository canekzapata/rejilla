"""Proceso del loop A de «suma uno»: la partitura del modelo. Carpeta exclusiva proceso/idea-<id12>/.

  01  la creencia: la distribución predictiva (12 clases de altura) a lo largo de la pieza, con la nota elegida encima
  02  entropía y sorpresa por evento, con las secciones
    python proceso_idea.py
"""
import hashlib, json, os, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
AQUI = Path(__file__).resolve().parent
js = ("require('./motor/cancion.js'); const C = globalThis.Cancion;"
      "console.log(JSON.stringify({M: C.modelo().map(e => ({p: e.p, dur: e.dur, pc: e.pc, tipo: e.tipo, sec: e.sec, prob: e.prob, s: e.s, H: e.H, dist: e.dist})), SECC: C.SECC, PULSOS: C.PULSOS}));")
D = json.loads(subprocess.run(['node', '-e', js], cwd=AQUI, capture_output=True, text=True, encoding='utf-8', check=True).stdout)
nonce = os.urandom(16).hex(); h = hashlib.sha256((AQUI / 'motor' / 'cancion.js').read_bytes() + Path(__file__).read_bytes() + nonce.encode())
ID = h.hexdigest(); C = ID[:12]; SAL = AQUI / 'proceso' / f'idea-{C}'; os.mkdir(SAL)


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
M, SECC, PUL = D['M'], D['SECC'], D['PULSOS']
W = 1500; X = lambda p: 70 + (W - 100) * p / PUL


def png(im, n):
    with open(SAL / n, 'xb') as f: im.save(f, 'PNG')


# 01 la creencia
H = 640; im = Image.new('RGB', (W, H), FONDO); d = ImageDraw.Draw(im)
d.text((24, 16), 'la creencia del modelo: qué tan probable cree cada nota (brillo), y la que eligió (marca)', fill=TXT, font=Fg)
Y = lambda pc: 90 + (11 - pc) * 42
for e in M:
    for pc in range(12):
        v = e['dist'][pc] ** .6
        d.rectangle([X(e['p']), Y(pc), X(e['p'] + e['dur']), Y(pc) + 40], fill=oklch(.13 + .75 * v, .02 + .14 * v, h0 + 40 + pc * 8))
for e in M:
    col = {'evidencia': oklch(.85, .12, h0 + 200), 'improbable': oklch(.95, .2, h0 + 330)}.get(e['tipo'], oklch(.97, .02, h0))
    d.rectangle([X(e['p']), Y(e['pc']) + 16, X(e['p'] + e['dur']) - 1, Y(e['pc']) + 24], fill=col)
for pc in range(12): d.text((14, Y(pc) + 12), NOM[pc], fill=TEN, font=Fs)
for s in SECC: d.line([(X(s['a']), 70), (X(s['a']), 600)], fill=TXT); d.text((X(s['a']) + 4, 70), s['n'], fill=TXT, font=F)
d.text((70, 608), 'marcas: blanco = la nota que eligió el modelo · de color tenue = la evidencia (el gancho pop) · la más intensa, al empezar la sorpresa = la nota improbable', fill=TEN, font=Fs)
png(im, f'01-la-creencia-{C}.png')

# 02 entropía y sorpresa
H = 440; im = Image.new('RGB', (W, H), FONDO); d = ImageDraw.Draw(im)
d.text((24, 16), 'entropía de la predicción (línea) y sorpresa de cada nota (barras), en bits', fill=TXT, font=Fg)
Yb = lambda b: 400 - 38 * b
for b in range(0, 9, 2): d.line([(X(0), Yb(b)), (X(PUL), Yb(b))], fill=REJ); d.text((30, Yb(b) - 7), str(b), fill=TEN, font=Fs)
for e in M: d.rectangle([X(e['p']), Yb(min(8.5, e['s'])), X(e['p'] + e['dur']) - 1, Yb(0)], fill=oklch(.45, .1, h0 + 330 if e['s'] > 4 else h0 + 60))
d.line([(X(e['p']), Yb(e['H'])) for e in M], fill=TXT, width=3)
for s in SECC: d.line([(X(s['a']), 60), (X(s['a']), 400)], fill=TEN); d.text((X(s['a']) + 4, 60), s['n'], fill=TXT, font=F)
png(im, f'02-entropia-y-sorpresa-{C}.png')
with open(SAL / f'receta-{C}.json', 'x', encoding='utf-8') as f:
    json.dump({'id': ID, 'nonce': nonce, 'eventos': len(M), 'cancion_js_sha256': hashlib.sha256((AQUI / 'motor' / 'cancion.js').read_bytes()).hexdigest()}, f, indent=1)
print(C)
