"""El proceso del loop A de «la máquina del tiempo», con el acuerdo de nombres del 13 de octubre:
cada ejecución tiene un identificador SHA-256 (programa + versión + audio del boceto + nonce),
su carpeta se crea en exclusiva y ningún archivo se escribe encima de otro.

  01  el telar del tiempo: la forma propuesta, con sus curvas continuas
  02  la rejilla del boceto: magnitud = luz, fase = tono (el groove es orden en la fase)
  03  el reloj del compás: la envolvente de cada banda doblada sobre un compás, medida
  04  espectrograma del boceto
  GIF el reloj del compás compás por compás (la nota → el groove → sin tiempo → otro groove)
"""
import hashlib, json, math, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy.io import wavfile
from scipy.signal import butter, sosfiltfilt, hilbert
sys.path.insert(0, str(Path(__file__).parent.parent))
from colores import oklch, fuente
import boceto as B

VERSION = 'maquina-idea 2'
AQUI = Path(__file__).parent
wav = B.R / 'boceto-norm.wav'
nonce = os.urandom(16).hex()
h = hashlib.sha256()
for p in (AQUI / 'boceto.py', Path(__file__), wav): h.update(p.read_bytes())
h.update(VERSION.encode()); h.update(nonce.encode())
ID = h.hexdigest(); C = ID[:12]
SAL = AQUI / 'proceso' / f'idea-{C}'
SAL.parent.mkdir(exist_ok=True)
os.mkdir(SAL)                                       # exclusiva: si existe, truena


def guardar_png(im, nombre):
    p = SAL / nombre
    with open(p, 'xb') as f: im.save(f, 'PNG')
    return p


# color: todo sale de un tono derivado de la semilla; frío (nave) contra cálido (funk)
h0 = 300 + np.random.default_rng(B.SEM).uniform(-15, 15)
FONDO = tuple(int(c) for c in oklch(.12, .04, h0)); TC = tuple(int(c) for c in oklch(.92, .03, h0 + 40))
TENUE = tuple(int(c) for c in oklch(.32, .05, h0))
col = lambda dh, L=.75, Cc=.16: tuple(int(c) for c in oklch(L, Cc, h0 + dh))
CB = {'bajo': col(-250), 'medio': col(-200, .8), 'alto': col(-130, .85, .12)}
F, Fs, Fg = fuente(19), fuente(14), fuente(30)

# ---------- 01 el telar del tiempo (la forma propuesta en IDEA.md) ----------
FORMA = [  # (sección, compases, transmisión)
    ('I. presente vivo', 20, 'TX 001-002 · retraso 0 → 8 min'),
    ('II. la señal se retrasa', 34, 'TX 004-016 · 41 min → 1 día'),
    ('III. vacío funky', 2, 'heliopausa'),
    ('IV. lo que vuelve', 28, 'TX 0#7 · años'),
    ('epílogo', 14, 'la antena encendida'),
]
TOT = sum(c for _, c, _ in FORMA)
u = np.linspace(0, 1, 900); b = u * TOT
ss = lambda v: np.clip(v, 0, 1) ** 2 * (3 - 2 * np.clip(v, 0, 1))
CURVAS = {
    'coherencia (tiempo)': 1 - .9 * ss((b - 24) / 26) + .9 * ss((b - 56) / 10) - .55 * ss((b - 86) / 10),
    'retraso del eco (log)': ss((b - 6) / 50) * (1 - ss((b - 54) / 2)) + .25 * ss((b - 58) / 30),
    'lejanía (banda de teléfono)': ss((b - 30) / 26) * (1 - .7 * ss((b - 57) / 14)) + .6 * ss((b - 86) / 12),
    'groove ↔ nota sola': 1 - .8 * ss((b - 30) / 24) + .8 * ss((b - 56) / 6) - .9 * ss((b - 88) / 10),
}
W, H = 1500, 760
im = Image.new('RGB', (W, H), FONDO); d = ImageDraw.Draw(im)
d.text((40, 24), 'la máquina del tiempo · el telar (forma propuesta, loop A)', fill=TC, font=Fg)
d.text((40, 66), f'{TOT} compases de {B.T:.3f} s = {TOT * B.T / 60:.1f} min · La = 55 Hz = fila 128 · el Uno = fila 1 · 103 bpm',
       fill=TC, font=Fs)
x0, x1, y0, y1 = 60, W - 40, 150, H - 170
X = lambda bb: x0 + (x1 - x0) * bb / TOT
acc = 0
for i, (nom, c, tx) in enumerate(FORMA):
    d.rectangle([X(acc), y1 + 14, X(acc + c) - 3, y1 + 40], fill=col(70 * i, .4, .08))
    if c < 5:                                       # la sección corta se rotula arriba, junto a «nada»
        d.text((X(acc) - 60, y0 - 4), f'{nom} · {tx}', fill=TC, font=Fs)
    else:
        d.text((X(acc) + 6, y1 + 50), nom, fill=TC, font=Fs); d.text((X(acc) + 6, y1 + 70), tx, fill=TC, font=Fs)
    d.line([X(acc), y0, X(acc), y1], fill=TENUE); acc += c
for j, (nom, v) in enumerate(CURVAS.items()):
    cc = col(-250 + 60 * j, .78, .15)
    pts = [(X(bb), y1 - (y1 - y0) * (.08 + .84 * vv)) for bb, vv in zip(b, np.clip(v, 0, 1))]
    d.line(pts, fill=cc, width=4)
    d.text((x0 + 10 + 360 * j, y0 - 34), '— ' + nom, fill=cc, font=Fs)
d.rectangle([X(54), y0, X(56), y1], fill=tuple(int(c) for c in oklch(.06, .01, h0)))
d.text((X(54) - 4, y0 + 20), 'nada', fill=TC, font=Fs)
guardar_png(im, f'01-telar-del-tiempo-{C}.png')

# ---------- 02 la rejilla del boceto: luz = magnitud, tono = fase ----------
Z = np.array([B.columna(c, 0) for c in range(B.N)])            # (compases, filas)
filas = slice(60, 450)                                          # parciales 1, 2 y 3 con sus bandas
sub = Z[:, filas]
mag = np.abs(sub); L = .1 + .85 * (np.log10(mag / mag.max() + 1e-5) + 5) / 5
fa = np.degrees(np.angle(sub))
im2 = np.zeros((sub.shape[1], sub.shape[0], 3), np.uint8)
for c in range(sub.shape[0]):
    im2[:, c] = oklch(L[c].clip(.08, .95), .16 * L[c].clip(0, 1), h0 + fa[c])[::-1]
rej = Image.fromarray(im2).resize((B.N * 60, sub.shape[1] * 2), Image.NEAREST)
im = Image.new('RGB', (rej.width + 340, rej.height + 120), FONDO); d = ImageDraw.Draw(im)
im.paste(rej, (60, 90))
d.text((30, 20), 'la rejilla del boceto · filas 60-450 (La1, La2, Mi3 y sus bandas laterales)', fill=TC, font=F)
d.text((30, 50), 'luz = magnitud · tono = fase. El groove es orden en la fase; sin tiempo, la fase se revuelve', fill=TC, font=Fs)
for n in (1, 2, 3):
    y = 90 + (filas.stop - 128 * n) * 2
    d.text((rej.width + 70, y - 8), f'parcial {n}: fila {128 * n} = {55 * n} Hz', fill=TC, font=Fs)
for c, et in ((0, 'nota'), (4, 'sale'), (7, 'funk'), (12, 'sin tiempo'), (15, 'otro')):
    d.text((60 + c * 60, rej.height + 96), et, fill=TC, font=Fs)
guardar_png(im, f'02-rejilla-fase-es-tiempo-{C}.png')

# ---------- 03 + GIF: el reloj del compás ----------
sr, x = wavfile.read(wav); m = x.mean(1)
BANDAS = {'bajo': (35, 190), 'medio': (210, 830), 'alto': (850, 3000)}
env = {k: np.abs(hilbert(sosfiltfilt(butter(4, f, 'bandpass', fs=sr, output='sos'), m))) for k, f in BANDAS.items()}
for k in env: env[k] /= np.percentile(env[k], 99.5)
ESTADO = ['la nota sola'] * 3 + ['el groove sale de la nota'] * 3 + ['funk de una nota'] * 4 + \
         ['se pierde el tiempo (mismo espectro)'] * 4 + ['vuelve otro groove'] * 4


def reloj(c, ancho=760):
    im = Image.new('RGB', (ancho, ancho), FONDO); d = ImageDraw.Draw(im)
    cx = cy = ancho // 2 + 20
    for k in range(16):
        a = -math.pi / 2 + 2 * math.pi * k / 16
        d.line([(cx + 70 * math.cos(a), cy + 70 * math.sin(a)), (cx + 300 * math.cos(a), cy + 300 * math.sin(a))],
               fill=TENUE, width=3 if k % 4 == 0 else 1)
    i0, n = int(c * B.T * sr), int(B.T * sr)
    for j, (k, base) in enumerate((('bajo', 80), ('medio', 155), ('alto', 225))):
        e = env[k][i0:i0 + n:40]; ang = -math.pi / 2 + 2 * math.pi * np.arange(len(e)) / len(e)
        r = base + 80 * np.clip(e, 0, 1.2)
        d.line(list(zip(cx + r * np.cos(ang), cy + r * np.sin(ang))), fill=CB[k], width=3)
    d.text((24, 18), f'compás {c + 1:2d}/{B.N} · {ESTADO[c]}', fill=TC, font=F)
    d.text((24, 46), 'una vuelta = un compás · arriba el Uno · adentro bajo, en medio palmada, afuera brillo', fill=TC, font=Fs)
    d.text((cx - 6, cy - 300 - 26), '1', fill=TC, font=F)
    return im


tira = Image.new('RGB', (4 * 380, 380 + 40), FONDO); dd = ImageDraw.Draw(tira)
for i, c in enumerate((1, 8, 12, 16)):
    tira.paste(reloj(c).resize((380, 380), Image.LANCZOS), (i * 380, 40))
dd.text((20, 8), 'el reloj del compás (medido del audio): nota sola · funk de una nota · sin tiempo · otro groove', fill=TC, font=Fs)
guardar_png(tira, f'03-reloj-del-compas-{C}.png')

esp = SAL / f'04-espectrograma-boceto-{C}.png'
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-i', str(wav), '-lavfi',
                'showspectrumpic=s=1400x600:mode=combined:scale=log:fscale=log:start=30:stop=4000:color=magma:legend=1',
                str(esp)], check=True)

frames = [reloj(c).resize((540, 540), Image.LANCZOS) for c in range(B.N) for _ in range(2)]
pal = frames[16].quantize(colors=96, method=Image.Quantize.MEDIANCUT)
frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
gif = AQUI / f'reloj-del-compas-s{B.SEM}-{C}.gif'
with open(gif, 'xb') as f:
    frames[0].save(f, 'GIF', save_all=True, append_images=frames[1:], duration=270, loop=0, optimize=True)

m4a = AQUI / f'funk-de-una-nota-s{B.SEM}-{C}.m4a'
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-i', str(wav), '-af', 'loudnorm=I=-16:TP=-1.5',
                '-c:a', 'aac', '-b:a', '192k', str(m4a)], check=True)

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
receta = {'id': ID, 'version': VERSION, 'nonce': nonce, 'semilla': B.SEM, 'sr_rejilla': B.SR, 'compas_s': B.T,
          'bpm': B.BPM, 'archivos': {str(p.relative_to(AQUI)).replace('\\', '/'): sha(p)
                                     for p in sorted(SAL.glob('*.png')) + [gif, m4a]},
          'audio_fuente_sha256': sha(wav)}
with open(SAL / f'receta-{C}.json', 'x', encoding='utf-8') as f: json.dump(receta, f, ensure_ascii=False, indent=1)
print(C, f'gif {gif.stat().st_size / 1e6:.2f} MB {270 * len(frames) / 1000:.1f} s')
