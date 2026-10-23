"""Proceso de un objeto (instrumentos 8-11: waterphone, gong, tambor parlante, metales). Carpeta exclusiva
proceso/<objeto>-<id12>/:
  01  la física del objeto (una lámina propia de cada uno, ver LAMINA)
  02  los gestos: espectrogramas de todos los demos
  03  el demo destacado, grande
  GIF el demo destacado dibujándose
  m4a muestrario de todos los demos
    python proceso_objeto.py waterphone w2
"""
import hashlib, json, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
AQUI = Path(__file__).resolve().parent; R = AQUI / 'render'; OBJ, ET = sys.argv[1], sys.argv[2]
CONFIG = {
    'waterphone': dict(motor='waterphone.js', orden=['arcos', 'gemido', 'golpes', 'bola', 'escena'], destacado='gemido', gif='el-gemido-del-waterphone',
                       tono=(200, 80), rango=(100, 8000),
                       titulo='el gemido: varillas con arco mientras el agua se mueve adentro de la vasija y dobla la altura (hasta 3 semitonos)'),
    'gong': dict(motor='gong.js', orden=['tam-tam', 'opera', 'cruce', 'arco', 'escena'], destacado='cruce', gif='el-gong-de-dos-alturas',
                 tono=(40, 60), rango=(60, 9000), titulo='el gong de dos alturas que se cruzan: un modo sube con la amplitud y el otro baja'),
    'tambor': dict(motor='tambor.js', orden=['golpes', 'habla', 'cancion', 'ritmo'], destacado='habla', gif='el-tambor-que-habla',
                   tono=(20, 50), rango=(50, 4000), titulo='el tambor que habla: cada sílaba un golpe; la sílaba con acento, el parche más tenso (más agudo)'),
    'metal': dict(motor='metal.js', orden=['trombon', 'plunger', 'growl', 'harmon', 'lengua-aire', 'funk'], destacado='plunger', gif='el-trombon-con-plunger',
                  tono=(60, 60), rango=(60, 8000), titulo='el trombón con plunger: la vara se desliza y la sordina abre y cierra (wah)'),
}[OBJ]
ORDEN = CONFIG['orden']
nonce = os.urandom(16).hex(); h = hashlib.sha256()
for f in [AQUI / 'motor' / CONFIG['motor'], AQUI / 'motor' / 'modos.js', Path(__file__)] + [R / f'{ET}-{OBJ}-{n}.wav' for n in ORDEN]: h.update(f.read_bytes())
h.update(nonce.encode()); ID = h.hexdigest(); C = ID[:12]; SAL = AQUI / 'proceso' / f'{OBJ}-{C}'; os.mkdir(SAL)


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
h0 = CONFIG['tono'][0] + int(C[:4], 16) % CONFIG['tono'][1]          # el tono base se deriva del id, dentro del arco de cada objeto
FONDO, TXT, TEN = oklch(.13, .025, h0), oklch(.92, .03, h0), oklch(.55, .05, h0)
W = 1500; FMIN, FMAX = CONFIG['rango']
lee = lambda n: (lambda q: (q[0], q[1].astype(float) / 32768))(wavfile.read(R / f'{ET}-{OBJ}-{n}.wav'))
meta = lambda n: json.load(open(R / f'{ET}-{OBJ}-{n}.json', encoding='utf-8'))


def png(im, n):
    with open(SAL / n, 'xb') as f: im.save(f, 'PNG')


def espectrograma(x, sr, ancho, alto, tinte, N=4096):
    hop = max(48, len(x) // 1500); cols = [np.abs(np.fft.rfft(x[a:a + N] * np.hanning(N))) for a in range(0, len(x) - N, hop)]
    S = 20 * np.log10(np.array(cols).T + 1e-7); fr = np.fft.rfftfreq(N, 1 / sr); S = S[np.searchsorted(fr, np.geomspace(FMIN, FMAX, alto))]
    S = np.clip((S - S.max() + 60) / 60, 0, 1); m = Image.fromarray((S[::-1] * 255).astype(np.uint8)).resize((ancho, alto), Image.BILINEAR)
    return Image.composite(Image.new('RGB', (ancho, alto), tinte), Image.new('RGB', (ancho, alto), FONDO), m)


def modos_lamina(titulo, filas, nota):
    """filas: [(nombre, [(razón, amplitud 0-1)…])] → barras en escala logarítmica de razón 1-40"""
    im = Image.new('RGB', (W, 90 + 110 * len(filas)), FONDO); dr = ImageDraw.Draw(im); dr.text((24, 16), titulo, fill=TXT, font=Fg)
    X = lambda q: 260 + (W - 300) * np.log(q) / np.log(40)
    for k, (nom, ms) in enumerate(filas):
        y0 = 80 + 110 * k; dr.text((24, y0 + 40), nom, fill=TXT, font=F); dr.line([(260, y0 + 90), (W - 40, y0 + 90)], fill=TEN)
        for q, a in ms:
            if q <= 40: dr.line([(X(q), y0 + 90), (X(q), y0 + 90 - 80 * a)], fill=oklch(.82, .12, h0 + 30 * k), width=3)
    for q in (1, 2, 5, 10, 20, 40): dr.text((X(q) - 6, 90 + 110 * len(filas) - 20), f'{q}', fill=TEN, font=F)
    dr.text((24, 52), nota, fill=TEN, font=F)
    return im


def lamina_waterphone():
    vol = [(1, 1), (6.267, .6), (17.55, .4), (34.39, .25)]
    vas = [(f / 143, .5) for f in (143, 231, 389, 517, 702, 911, 1288, 1704, 2210)]
    return modos_lamina('la física: cada varilla es una viga en voladizo (modos 1 : 6.27 : 17.55 : 34.39); la vasija, modos inarmónicos graves',
                        [('varilla (voladizo)', vol), ('vasija (sobre 143 Hz)', vas)], 'razón de frecuencia sobre el modo 1 (escala log)')


def lamina_generica():
    J = meta(CONFIG['destacado']); filas = J.get('modos_lamina') or []
    return modos_lamina(J.get('titulo_lamina', 'los modos'), [(n, [tuple(q) for q in ms]) for n, ms in filas], 'razón de frecuencia sobre el modo 1 (escala log)')


png(lamina_waterphone() if OBJ == 'waterphone' else lamina_generica(), f'01-la-fisica-{C}.png')

# 02 los gestos
fil = (len(ORDEN) + 1) // 2; im = Image.new('RGB', (W, 60 + fil * 240), FONDO); dr = ImageDraw.Draw(im)
dr.text((24, 16), f'los gestos ({FMIN} Hz - {FMAX / 1000:g} kHz): ' + ' · '.join(ORDEN), fill=TXT, font=Fg)
for k, n in enumerate(ORDEN):
    sr, x = lee(n); col, fila = k % 2, k // 2; ancho = (W - 90) // 2
    im.paste(espectrograma(x, sr, ancho, 190, oklch(.85, .12, h0 + 22 * k)), (30 + col * (ancho + 30), 80 + fila * 240))
    dr.text((30 + col * (ancho + 30), 60 + fila * 240), n, fill=TXT, font=F)
png(im, f'02-los-gestos-{C}.png')

# 03 el destacado + GIF
sr, x = lee(CONFIG['destacado']); dur = len(x) / sr


def lamina(hasta, ancho, alto, titulo=True):
    im = Image.new('RGB', (ancho, alto), FONDO); dr = ImageDraw.Draw(im); top = 60 if titulo else 20
    if titulo: dr.text((20, 14), CONFIG['titulo'], fill=TXT, font=Fg)
    n = int(len(x) * min(1, hasta / dur)); w = max(2, int((ancho - 40) * min(1, hasta / dur)))
    if n > 8192: im.paste(espectrograma(x[:n], sr, w, alto - top - 20, oklch(.86, .13, h0 + 30)), (20, top))
    return im


png(lamina(dur, W, 560), f'03-{CONFIG["destacado"]}-{C}.png')
frames = [lamina(t, 760, 380, False) for t in np.linspace(.4, dur, 40)]
pal = frames[-1].quantize(colors=64, method=Image.Quantize.MEDIANCUT); frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
gif = AQUI / f'{CONFIG["gif"]}-{C}.gif'
with open(gif, 'xb') as fh: frames[0].save(fh, 'GIF', save_all=True, append_images=frames[1:] + [frames[-1]] * 6, duration=200, loop=0, optimize=True)
partes = []
for n in ORDEN:
    sr, xx = lee(n); partes += [xx / (np.abs(xx).max() + 1e-9) * .8, np.zeros(int(.5 * sr))]
wav = R / f'muestrario-{OBJ}-{C}.wav'; wavfile.write(wav, sr, (np.concatenate(partes) * 32767).astype(np.int16))
m4a = AQUI / f'muestrario-{OBJ}-{C}.m4a'
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-i', str(wav), '-af', 'loudnorm=I=-16:TP=-1.5', '-c:a', 'aac', '-b:a', '192k', str(m4a)], check=True)
sha = lambda q: hashlib.sha256(Path(q).read_bytes()).hexdigest()
with open(SAL / f'receta-{C}.json', 'x', encoding='utf-8') as fh:
    json.dump({'id': ID, 'nonce': nonce, 'objeto': OBJ, 'etiqueta': ET, 'orden_muestrario': ORDEN,
               'archivos': {str(q.relative_to(AQUI)).replace('\\', '/'): sha(q) for q in sorted(SAL.glob('*.png')) + [gif, m4a]}}, fh, ensure_ascii=False, indent=1)
print(C, f'gif {gif.stat().st_size / 1e6:.2f} MB {200 * (len(frames) + 6) / 1000:.1f} s')
