"""Renderiza etapas con datos reales verificados; nunca sobreescribe salidas."""
import hashlib, io, json, struct, wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent
PROC = OUT / 'proceso'
RUN, SEED, W, H = '5c60e41cb3dc', 181026, 1200, 630
BG, PANEL, PAPER, DIM = '#101712', '#17231b', '#e4e8d9', '#9cac9a'
TEAL, GOLD, PINK, LINE = '#86d7c6', '#edc877', '#e7a2a7', '#405247'
FONT = Path('C:/Windows/Fonts')
mono = ImageFont.truetype(str(FONT / 'consola.ttf'), 22)
small = ImageFont.truetype(str(FONT / 'consola.ttf'), 17)
body = ImageFont.truetype(str(FONT / 'segoeui.ttf'), 28)
serif = ImageFont.truetype(str(FONT / 'georgia.ttf'), 48)

def write_new(path, data):
    if path.exists(): raise FileExistsError(f'No se sobreescribe: {path}')
    with path.open('xb') as f: f.write(data)

def image_new(image, path):
    stream = io.BytesIO()
    image.save(stream, format='PNG')
    write_new(path, stream.getvalue())

def canvas(kicker, title, subtitle):
    im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
    d.text((64, 38), kicker, font=mono, fill=TEAL)
    d.text((64, 86), title, font=serif, fill=PAPER)
    d.text((64, 153), subtitle, font=body, fill=DIM)
    d.line((64, 208, 1136, 208), fill=LINE, width=2)
    return im, d

record = json.loads((OUT / 'registro.json').read_text(encoding='utf-8'))
audio = json.loads((OUT / f'audio-{RUN}.json').read_text(encoding='utf-8'))
stages = []

im, d = canvas('01 / TEIA · EVENTO PÚBLICO', 'El comentario nombra su pieza', 'El evento trae la pareja FA2 + token_id y el comment_id.')
d.rounded_rectangle((64, 250, 1136, 495), radius=20, fill=PANEL, outline=LINE, width=2)
d.text((96, 283), 'comment_posted', font=mono, fill=GOLD)
d.text((96, 337), 'OBJKT 885842', font=serif, fill=PAPER)
d.text((580, 337), 'comentario 80', font=serif, fill=TEAL)
d.text((96, 413), record['teia']['fa2Address'], font=small, fill=DIM)
d.text((64, 550), 'Contrato de comentarios · lectura pública · sin canal', font=mono, fill=DIM)
stages.append(PROC / f'01-evento-s{SEED}-{RUN}.png'); image_new(im, stages[-1])

im, d = canvas('02 / TZKT · BIG MAP comments/80', 'El registro apunta al contenido', 'La fila conserva ocultamiento, versión y referencia del texto.')
d.rounded_rectangle((64, 250, 1136, 510), radius=20, fill=PANEL, outline=LINE, width=2)
d.text((96, 282), 'hidden: false      version: 1      parent_id: null', font=mono, fill=GOLD)
d.text((96, 338), 'content (hex)', font=mono, fill=DIM)
hexv = record['teia']['bigmap']['contentHex']
d.text((96, 385), hexv[:66], font=small, fill=PAPER)
d.text((96, 411), hexv[66:], font=small, fill=PAPER)
d.text((96, 457), '↓', font=serif, fill=TEAL)
d.text((153, 461), record['teia']['contentUri'], font=mono, fill=TEAL)
stages.append(PROC / f'02-bigmap-s{SEED}-{RUN}.png'); image_new(im, stages[-1])

im, d = canvas('03 / IPFS · teia-token-comment', 'Las palabras llegan como dato', 'El JSON de Teia entrega contenido plano para la lectura de Siringua.')
d.rounded_rectangle((64, 250, 1136, 510), radius=20, fill=PANEL, outline=LINE, width=2)
d.text((96, 282), '{ "type": "teia-token-comment", "version": 1,', font=mono, fill=DIM)
d.text((96, 325), '  "tokenId": "885842", "author": "tz1VHekC…",', font=mono, fill=DIM)
d.text((96, 380), '  "content":', font=mono, fill=DIM)
d.text((300, 366), '«hola bola de hola»', font=serif, fill=GOLD)
d.text((96, 454), '4 palabras · español mexicano · Difonos', font=mono, fill=TEAL)
stages.append(PROC / f'03-ipfs-s{SEED}-{RUN}.png'); image_new(im, stages[-1])

wav_path = OUT / audio['files'][2]
with wave.open(str(wav_path), 'rb') as f:
    raw, rate, n = f.readframes(f.getnframes()), f.getframerate(), f.getnframes()
samples = struct.unpack('<%dh' % (len(raw) // 2), raw)
im, d = canvas('04 / SIRINGUA · AGUA + AVE', 'La pieza responde con su cuerpo', 'Cada palabra articula agua; después, la siringe contesta.')
left, right, mid, bins = 64, 1136, 335, 900
d.line((left, mid, right, mid), fill=LINE, width=1)
pts = []
for i in range(bins):
    a, b = i * len(samples) // bins, max(i * len(samples) // bins + 1, (i + 1) * len(samples) // bins)
    peak = max(samples[a:b], key=abs) / 32768
    pts.append((left + i * (right-left) / (bins-1), mid - peak * 76))
d.line(pts, fill=TEAL, width=2)
for x, word in [(64,'hola'),(390,'bola'),(748,'de'),(975,'hola')]: d.text((x,445), word, font=mono, fill=GOLD)
for x in [250, 590, 856]: d.text((x,445), '• ♫', font=mono, fill=PINK)
d.text((64,525), f"{audio['duration']} s · {rate//1000} kHz · semilla {SEED}", font=mono, fill=DIM)
d.text((635,525), 'AGUA · voz articulada   AVE · respuesta', font=small, fill=TEAL)
stages.append(PROC / f'04-siringua-s{SEED}-{RUN}.png'); image_new(im, stages[-1])

result = OUT / f'siringua-prueba-comentarios-s{SEED}-{RUN}-resultado.png'
image_new(im.copy(), result)
image_new(im.copy(), OUT / 'og.png')
frames = [Image.open(p).convert('P', palette=Image.Palette.ADAPTIVE, colors=128) for p in stages]
gif_stream = io.BytesIO()
frames[0].save(gif_stream, format='GIF', save_all=True, append_images=frames[1:], duration=[1500,1500,1600,1800], loop=0, optimize=True)
gif_path = OUT / f'proceso-siringua-comentarios-s{SEED}-{RUN}.gif'
write_new(gif_path, gif_stream.getvalue())

files = [*stages, result, OUT/'og.png', gif_path, wav_path,
         OUT/audio['files'][0], OUT/audio['files'][1], OUT/f'audio-{RUN}.json',
         OUT/'registro.json', OUT/'index.html', OUT/'lib/siringua/teia-comentarios.js', OUT/'test/teia-comentarios.test.cjs']
recipe = {'runId':RUN,'runHash':record['runHash'],'programVersion':'siringua-token-comments-reader-1',
          'imageBasisHash':record['imageBasisHash'],'nonce':record['nonce'],'seed':SEED,
          'assetHashes':{str(p.relative_to(OUT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
          'gifDurationMs':6400,'gifFrames':len(frames),'gifBytes':gif_path.stat().st_size}
write_new(OUT/'receta.json', json.dumps(recipe,ensure_ascii=False,indent=2).encode('utf-8'))
print(json.dumps({'stages':[p.name for p in stages],'result':result.name,'og':'og.png','gif':gif_path.name,
                  'gifBytes':gif_path.stat().st_size,'recipe':'receta.json'},ensure_ascii=False,indent=2))
