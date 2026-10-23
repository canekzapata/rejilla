"""Entrega de «el tiempo es la altura»: carpeta exclusiva pieza/el-tiempo-es-la-altura-<id12>/ con
  01  el sujeto: la letra hecha melodía (una nota por sílaba, los acentos largos)
  02  el canon: las siete voces en el tiempo (altura en escala log), la convergencia y las salidas
  03  la mezcla: espectrograma de la pieza con las secciones
  GIF el canon con el cursor avanzando hasta converger
  m4a la pieza (loudnorm −16 LUFS) y receta con los hashes
    python pieza/proceso_pieza.py p1 v1
"""
import hashlib, json, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
AQUI = Path(__file__).resolve().parent; OBJ = AQUI.parent; R = OBJ / 'render'; ET, VER = sys.argv[1], sys.argv[2]
MEZ = R / f'{ET}-mezcla-{VER}.wav'
P = json.loads(subprocess.run(['node', '-e', "const P=require('./pieza/partitura.js'); console.log(JSON.stringify({S:P.SUJETO, L:P.LETRA, TC:P.TC, DUR:P.DUR, BEAT:P.BEAT, V:P.VOCES.map(v=>P.voz(v.nombre))}))"],
                          capture_output=True, text=True, encoding='utf-8', cwd=OBJ).stdout)
nonce = os.urandom(16).hex(); h = hashlib.sha256()
for f in [AQUI / 'partitura.js', AQUI / 'stems.js', AQUI / 'mezcla.py', Path(__file__), MEZ]: h.update(f.read_bytes())
h.update(nonce.encode()); ID = h.hexdigest(); C = ID[:12]; SAL = AQUI / f'el-tiempo-es-la-altura-{C}'; os.mkdir(SAL)


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
h0 = int(C[:4], 16) % 360                                          # el arco de color de las voces se deriva del id
FONDO, TXT, TEN = oklch(.12, .015, h0), oklch(.93, .02, h0), oklch(.5, .03, h0)
COL = [oklch(.78, .14, h0 + 360 * k / 7 * .8) for k in range(7)]   # siete voces, de lentas (graves) a rápidas (agudas)
W = 1500
png = lambda im, n: im.save(open(SAL / n, 'xb'), 'PNG')

# 01 el sujeto
S = P['S']['notas']; B = P['S']['beats']; im = Image.new('RGB', (W, 470), FONDO); dr = ImageDraw.Draw(im)
dr.text((24, 16), 'el sujeto: la letra hecha melodía — una nota por sílaba, los acentos (MAYÚSCULAS) duran más y saltan; Mi locrio', fill=TXT, font=Fg)
mn, mx = min(n['m'] for n in S) - 2, max(n['m'] for n in S) + 2; X = lambda b: 40 + (W - 80) * b / B; Y = lambda m: 380 - 290 * (m - mn) / (mx - mn)
for n in S:
    c = COL[3] if n['acento'] else oklch(.62, .06, h0 + 60)
    dr.rectangle([X(n['b']), Y(n['m']) - 5, X(n['b'] + n['d']) - 3, Y(n['m']) + 5], fill=c)
    dr.text((X(n['b']), 395 + 18 * (n['verso'] % 2)), n['silaba'].upper() if n['acento'] else n['silaba'], fill=TXT if n['acento'] else TEN, font=F)
png(im, f'01-el-sujeto-{C}.png')

# 02 el canon
DUR, TC = P['DUR'], P['TC']; allm = [n['m'] for v in P['V'] for n in v['notas']]; lo, hi = min(allm) - 2, max(allm) + 2
def canon(hasta, ancho, alto, titulo=True):
    im = Image.new('RGB', (ancho, alto), FONDO); dr = ImageDraw.Draw(im); top = 70 if titulo else 16; izq = 150 if titulo else 10
    X = lambda t: izq + (ancho - izq - 20) * t / DUR; Y = lambda m: alto - 30 - (alto - 30 - top) * (m - lo) / (hi - lo)
    if titulo: dr.text((24, 16), 'el canon: el mismo sujeto a siete tempos; la razón de tempo es también la de altura. Convergen en el tam-tam y se van.', fill=TXT, font=Fg)
    dr.line([(X(TC), top), (X(TC), alto - 30)], fill=TEN, width=2)
    for k, v in enumerate(P['V']):
        for n in v['notas']:
            if n['t'] > hasta: continue
            dr.line([(X(n['t']), Y(n['m'])), (X(min(hasta, n['t'] + n['dur'])), Y(n['m']))], fill=COL[k], width=4 if n['acento'] else 2)
        if titulo:
            fr = {4 / 7: '4/7', 2 / 3: '2/3', 4 / 5: '4/5', 1: '1', 5 / 4: '5/4', 3 / 2: '3/2', 7 / 4: '7/4'}
            nom = next((q for r_, q in fr.items() if abs(r_ - v['r']) < 1e-6), '')
            dr.text((12, Y(np.mean([n['m'] for n in v['notas']])) - 8), f"{v['nombre']} {nom}", fill=COL[k], font=F)
    dr.line([(X(min(hasta, DUR)), top), (X(min(hasta, DUR)), alto - 30)], fill=TXT, width=1)
    if titulo:
        for t in range(0, DUR + 1, 20): dr.text((X(t) - 10, alto - 24), f'{t}s', fill=TEN, font=F)
        dr.text((X(TC) + 6, top), 'convergencia', fill=TXT, font=F)
    return im
png(canon(DUR, W, 720), f'02-el-canon-{C}.png')
frames = [canon(t, 760, 400, False) for t in np.linspace(4, DUR, 40)]

# 03 la mezcla
sr, x = wavfile.read(MEZ); x = x.astype(float).mean(axis=1) / 32768
N = 4096; hop = len(x) // 1460; cols = [np.abs(np.fft.rfft(x[a:a + N] * np.hanning(N))) for a in range(0, len(x) - N, hop)]
Sg = 20 * np.log10(np.array(cols).T + 1e-7); fr = np.fft.rfftfreq(N, 1 / sr); Sg = Sg[np.searchsorted(fr, np.geomspace(40, 12000, 420))]
Sg = np.clip((Sg - Sg.max() + 70) / 70, 0, 1); msk = Image.fromarray((Sg[::-1] * 255).astype(np.uint8)).resize((W - 40, 420), Image.BILINEAR)
im = Image.new('RGB', (W, 520), FONDO); im.paste(Image.composite(Image.new('RGB', msk.size, oklch(.85, .1, h0 + 40)), Image.new('RGB', msk.size, FONDO), msk), (20, 70))
dr = ImageDraw.Draw(im); dr.text((24, 16), 'la mezcla (40 Hz - 12 kHz): niebla de waterphone · entradas de lentas a rápidas · convergencia · salidas · coda de agua', fill=TXT, font=Fg)
for t, q in ((TC, 'convergencia'), (168, 'coda')): xx = 20 + (W - 40) * t / DUR; dr.line([(xx, 70), (xx, 490)], fill=TXT); dr.text((xx + 4, 494), q, fill=TXT, font=F)
png(im, f'03-la-mezcla-{C}.png')

pal = frames[-1].quantize(colors=96, method=Image.Quantize.MEDIANCUT); frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
gif = SAL / f'el-canon-converge-{C}.gif'
with open(gif, 'xb') as fh: frames[0].save(fh, 'GIF', save_all=True, append_images=frames[1:] + [frames[-1]] * 6, duration=200, loop=0, optimize=True)
m4a = SAL / f'el-tiempo-es-la-altura-{C}.m4a'
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-i', str(MEZ), '-af', 'loudnorm=I=-16:TP=-1.5', '-c:a', 'aac', '-b:a', '256k', str(m4a)], check=True)
sha = lambda q: hashlib.sha256(Path(q).read_bytes()).hexdigest()
with open(SAL / f'receta-{C}.json', 'x', encoding='utf-8') as fh:
    json.dump({'id': ID, 'nonce': nonce, 'etiqueta': ET, 'mezcla': MEZ.name, 'sha_mezcla': sha(MEZ), 'TC': TC, 'DUR': DUR,
               'voces': [{k: v[k] for k in ('nombre', 'r', 'semi', 'entra', 'sale', 'antes', 'despues')} for v in P['V']],
               'archivos': {q.name: sha(q) for q in sorted(SAL.glob('*.png')) + [gif, m4a]}}, fh, ensure_ascii=False, indent=1)
print(C, f'gif {gif.stat().st_size / 1e6:.2f} MB {200 * (len(frames) + 6) / 1000:.1f} s')
