"""El proceso del loop B (letra dispuesta + texturas), con el acuerdo de nombres del 13 de octubre:
carpeta exclusiva `proceso/texturas-<hash12>/`, ningún archivo escrito encima de otro.

  01  la letra dispuesta: 104 compases, quién dice qué, y las flechas del retraso (la Tierra contesta tarde)
  02  el telar del loop B: las cuatro curvas sobre la forma con letra
  03… una ficha por demo: espectrograma + qué es + lo medido
  GIF las fichas en orden · m4a el muestrario (las diez demos seguidas)
"""
import hashlib, json, math, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy.io import wavfile
sys.path.insert(0, str(Path(__file__).parent.parent))
from colores import oklch, fuente
import letra as LT

VERSION = 'maquina-texturas 1'
AQUI = Path(__file__).parent
R = AQUI.parent / 'render' / 'maquina-demos'
DEMOS = ['t01', 't02', 't03', 't04', 't05', 't06', 't07', 't08', 't09', 't10']
MED = json.load(open(R / 'medidas.json', encoding='utf-8'))

nonce = os.urandom(16).hex()
h = hashlib.sha256()
for p in [AQUI / f for f in ('nave.py', 'demos.py', 'letra.py', 'proceso_texturas.py')] + [R / f'{d}.final.wav' for d in DEMOS]:
    h.update(p.read_bytes())
h.update(VERSION.encode()); h.update(nonce.encode())
ID = h.hexdigest(); C = ID[:12]
SAL = AQUI / 'proceso' / f'texturas-{C}'
os.mkdir(SAL)


def png(im, nombre):
    with open(SAL / nombre, 'xb') as f: im.save(f, 'PNG')


h0 = 300 + np.random.default_rng(1031).uniform(-15, 15)
FONDO = tuple(int(c) for c in oklch(.12, .04, h0)); TC = tuple(int(c) for c in oklch(.92, .03, h0 + 40))
TENUE = tuple(int(c) for c in oklch(.34, .05, h0))
col = lambda dh, L=.76, Cc=.15: tuple(int(c) for c in oklch(L, Cc, h0 + dh))
QUIEN = {'nave': col(-250), 'tierra': col(-120, .8), 'tele': col(-40, .7, .1), 'glifo': col(60, .7, .12),
         'portadora': col(0, .8, .1)}
F, Fs, Fx, Fg = fuente(17), fuente(13), fuente(11), fuente(28)

# ---------- 01 la letra dispuesta ----------
W, H = 2200, 1180
im = Image.new('RGB', (W, H), FONDO); d = ImageDraw.Draw(im)
d.text((40, 22), 'la máquina del tiempo · la letra dispuesta («NADIE A BORDO», Canek Zapata)', fill=TC, font=Fg)
d.text((40, 62), '104 compases de 2.327 s (103 bpm) · cada carril es una voz · las flechas: la Tierra contesta con el retraso de la transmisión (se duplica)',
       fill=TC, font=Fs)
x0, x1 = 60, W - 30
X = lambda c: x0 + (x1 - x0) * (c - 1) / LT.TOTAL
CAR = {'tele': 150, 'nave': 270, 'tierra': 700, 'glifo': 930, 'portadora': 1010}
for nom, y in CAR.items():
    d.text((x0, y - 34), {'tele': 'telemetría', 'nave': 'la nave (Sabina canta)', 'tierra': 'la Tierra (coro de Ziras)',
                         'glifo': 'gestos de la tipografía', 'portadora': 'la portadora'}[nom], fill=QUIEN[nom], font=F)
for i, (nom, a, b) in enumerate(LT.SECCIONES):
    d.rectangle([X(a), H - 92, X(b + 1) - 3, H - 66], fill=col(55 * i, .38, .07))
    d.text((X(a) + 4, H - 58), nom, fill=TC, font=Fs)
    d.line([X(a), 110, X(a), H - 96], fill=TENUE)
for c in range(1, LT.TOTAL + 1, 4):
    d.text((X(c), H - 30), str(c), fill=TENUE, font=Fx)
alt = {}
for c, n, quien, texto, tx in LT.EVENTOS:
    y = CAR[quien] + (alt.get(quien, 0) % 3) * 0; alt[quien] = alt.get(quien, 0) + 1
    d.rectangle([X(c), y, X(c + n) - 2, y + 16], fill=QUIEN[quien])
    lineas = [s.strip() for s in texto.split('/')]
    for j, ln in enumerate(lineas[:6]):
        if quien == 'nave':
            yy = y + 24 + j * 15 + (alt[quien] % 2) * 100
        else:
            yy = y + 22 + j * 15
        d.text((X(c), yy), ln[:34], fill=QUIEN[quien], font=Fx)
for texto, llega, tx in LT.RESPUESTAS:
    y = CAR['tierra'] + 70 + (LT.RESPUESTAS.index((texto, llega, tx)) % 4) * 34
    d.rectangle([X(llega), y, X(llega + 1.6), y + 10], fill=QUIEN['tierra'])
    d.text((X(llega), y + 12), texto[:44], fill=QUIEN['tierra'], font=Fx)
    if tx in LT.DICHO_EN:
        xa = X(LT.DICHO_EN[tx]); d.line([(xa, CAR['nave'] + 16), (X(llega), y)], fill=col(-120, .55, .08), width=2)
png(im, f'01-letra-dispuesta-{C}.png')

# ---------- 02 el telar del loop B ----------
b = np.linspace(1, LT.TOTAL + 1, 1200)
ss = lambda v: np.clip(v, 0, 1) ** 2 * (3 - 2 * np.clip(v, 0, 1))
CURVAS = {
    'enfoque (coherencia)': .9 - .1 * np.sin(b / 2.3) - .75 * ss((b - 30) / 24) + .75 * ss((b - 57) / 6) - .45 * ss((b - 83) / 9) - .3 * ss((b - 93) / 4),
    'retraso del eco (log2 compases)': np.clip(np.interp(b, [1, 13, 19, 33, 41, 54, 61, 69, 77, 104], [0, 0, .1, .2, .35, .5, .65, .8, .95, 1]), 0, 1),
    'lejanía (cerca → teléfono)': ss((b - 30) / 20) * (1 - .4 * ss((b - 57) / 3)) + .2 * ss((b - 83) / 6) - .9 * ss((b - 96) / 5),
    'voz ↔ portadora': .12 + .85 * ss((b - 47) / 9) * (1 - ss((b - 56.5) / 1)) + .3 * ss((b - 83) / 8) * (1 - ss((b - 100) / 3)),
}
W2, H2 = 2200, 760
im = Image.new('RGB', (W2, H2), FONDO); d = ImageDraw.Draw(im)
d.text((40, 22), 'el telar del loop B: las curvas que tejen la forma (ningún cambio es un escalón)', fill=TC, font=Fg)
y0, y1 = 130, H2 - 140
for i, (nom, a, bb) in enumerate(LT.SECCIONES):
    d.rectangle([X(a), y1 + 14, X(bb + 1) - 3, y1 + 40], fill=col(55 * i, .38, .07))
    d.text((X(a) + 4, y1 + 48), nom, fill=TC, font=Fs)
    d.line([X(a), y0, X(a), y1], fill=TENUE)
for j, (nom, v) in enumerate(CURVAS.items()):
    cc = col(-250 + 75 * j, .78, .15)
    d.line([(X(bb), y1 - (y1 - y0) * (.06 + .88 * vv)) for bb, vv in zip(b, np.clip(v, 0, 1))], fill=cc, width=4)
    d.text((x0 + 10 + 520 * j, y0 - 40), '— ' + nom, fill=cc, font=F)
for c, txt in ((56, 'vacío'), (87, '███')):
    d.rectangle([X(c), y0, X(c + 1), y1], fill=tuple(int(q) for q in oklch(.05, .01, h0)))
    d.text((X(c) - 10, y1 + 70), txt, fill=TC, font=Fs)
png(im, f'02-telar-loop-b-{C}.png')

# ---------- 03… fichas de las demos ----------
fichas = []
for i, dm in enumerate(DEMOS):
    spec = R / f'{dm}.spec.png'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(R / f'{dm}.final.wav'), '-lavfi',
                    'showspectrumpic=s=1100x420:mode=combined:scale=log:fscale=log:start=25:stop=16000:color=magma:legend=0',
                    str(spec)], check=True)
    sp = Image.open(spec).convert('RGB')
    im = Image.new('RGB', (sp.width + 40, sp.height + 150), FONDO); d = ImageDraw.Draw(im)
    m = MED.get(dm, {}); d.text((20, 12), f'{dm} · {m.get("titulo", "")}', fill=TC, font=F)
    medidas = {k: v for k, v in m.items() if k != 'titulo'}
    linea = '  ·  '.join(f'{k}: {v}' for k, v in medidas.items()).replace("'", '')
    for j in range(0, min(len(linea), 540), 135):
        d.text((20, 44 + 18 * (j // 135)), linea[j:j + 135], fill=col(-120, .8, .08), font=Fx)
    im.paste(sp, (20, 130))
    png(im, f'{i + 3:02d}-{dm}-{C}.png'); fichas.append(im)

frames = [f.resize((f.width * 3 // 5, f.height * 3 // 5), Image.LANCZOS) for f in fichas for _ in range(2)]
pal = frames[0].quantize(colors=200, method=Image.Quantize.MEDIANCUT)
frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
gif = AQUI / f'texturas-s1031-{C}.gif'
with open(gif, 'xb') as f:
    frames[0].save(f, 'GIF', save_all=True, append_images=frames[1:], duration=480, loop=0, optimize=True)

# ---------- el muestrario ----------
pedazos, marcas, t = [], [], 0.0
for dm in DEMOS:
    sr, x = wavfile.read(R / f'{dm}.final.wav'); x = x.astype(float) / 32768
    marcas.append((dm, MED.get(dm, {}).get('titulo', ''), round(t, 2))); pedazos += [x, np.zeros((sr, 2))]; t += len(x) / sr + 1
wav = R / 'muestrario-texturas.wav'
wavfile.write(wav, sr, (np.concatenate(pedazos) * 32767).astype(np.int16))
m4a = AQUI / f'muestrario-texturas-s1031-{C}.m4a'
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-i', str(wav), '-c:a', 'aac', '-b:a', '192k', str(m4a)], check=True)

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
receta = {'id': ID, 'version': VERSION, 'nonce': nonce, 'semilla': 1031, 'bpm': 103.125, 'sr_rejilla': 56320,
          'marcas_muestrario_s': marcas, 'medidas': MED,
          'archivos': {str(p.relative_to(AQUI)).replace('\\', '/'): sha(p) for p in sorted(SAL.glob('*.png')) + [gif, m4a]}}
with open(SAL / f'receta-{C}.json', 'x', encoding='utf-8') as f: json.dump(receta, f, ensure_ascii=False, indent=1)
print(C, f'gif {gif.stat().st_size / 1e6:.2f} MB {480 * len(frames) / 1000:.1f} s · muestrario {t:.0f} s')
