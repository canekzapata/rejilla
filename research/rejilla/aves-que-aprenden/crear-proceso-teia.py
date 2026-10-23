"""Captura las transformaciones reales de la prueba local, sin inventar etapas."""
import hashlib, json, math, struct, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out = Path(sys.argv[1]).resolve()
meta = json.loads((out / 'registro.json').read_text(encoding='utf-8'))
rid, seed = meta['runId'], meta['semilla']
W, H = 1200, 675
BG, PAPER, DIM, CYAN, GOLD, PINK = '#101516', '#edf0e7', '#87918c', '#8de0ce', '#efc778', '#e7a2a7'
fontdir = Path('C:/Windows/Fonts')
def font(name, size):
    return ImageFont.truetype(str(fontdir / name), size)
sans, mono, serif = font('segoeui.ttf', 28), font('consola.ttf', 23), font('georgia.ttf', 38)
stages=[]
def canvas(kicker, title, subtitle):
    im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
    d.text((70,42),kicker,font=mono,fill=CYAN)
    d.text((70,91),title,font=font('georgia.ttf',52),fill=PAPER)
    d.text((70,163),subtitle,font=sans,fill=DIM)
    d.line((70,220,1130,220),fill='#33403d',width=2)
    return im,d
def save_stage(im, idx, name):
    p=out/'proceso'/f'{idx:02d}-{name}-s{seed}-{rid}.png'; p.parent.mkdir(exist_ok=True)
    im.save(p); stages.append(p)
    return p

im,d=canvas('01 / TEIA · REGISTRO PÚBLICO','Un canal abierto deja una huella','Prueba de lectura · canal 10 · mensaje 168 · consulta de solo lectura')
d.rounded_rectangle((70,285,1130,530),radius=22,outline='#53615b',width=2)
d.text((112,324),'evento on-chain',font=mono,fill=GOLD); d.text((112,374),'message_posted → registro 168',font=serif,fill=PAPER)
d.line((490,407,650,407),fill=CYAN,width=4); d.polygon([(650,407),(630,396),(630,418)],fill=CYAN)
d.text((690,324),'referencia IPFS',font=mono,fill=GOLD); d.text((690,382),'QmVxFZtC…myipAN',font=mono,fill=PAPER)
d.text((70,592),'Canal abierto · access_mode: unrestricted · mensaje visible',font=mono,fill=DIM)
save_stage(im,1,'registro')

im,d=canvas('02 / IPFS · TEXTO DEL MENSAJE','La pieza recibe palabras','Fragmento público leído desde el contenido JSON; se conserva el original del mensaje.')
excerpt='“Art is exclusive and egocentric by nature, no need to hide that behind a false sense of belonging.”'
d.rounded_rectangle((70,270,1130,510),radius=20,fill='#1b2422',outline='#46534d',width=2)
lines=['Art is exclusive and egocentric by nature,','no need to hide that behind a false sense','of belonging.']
for i,line in enumerate(lines): d.text((108,300+i*58),line,font=serif,fill=PAPER)
d.text((70,572),'18 palabras · el texto se trata como dato, nunca como código',font=mono,fill=CYAN)
save_stage(im,2,'mensaje')

im,d=canvas('03 / DIFONOS · eSpeak NG WASM','Palabras en fonemas','Proveedor local · inglés estadounidense · pronunciación nueva, sin léxico escrito a mano')
for j,w in enumerate(meta['words'][:7]):
    y=255+j*52
    d.text((84,y),w['text'],font=mono,fill=GOLD)
    d.text((350,y), ' '.join(w['phones']),font=mono,fill=PAPER)
    d.text((875,y),w['ipa'] or '',font=mono,fill=CYAN)
d.text((70,628),'18 de 18 palabras resueltas · inventario ARPABET adaptado a VozAgua',font=mono,fill=DIM)
save_stage(im,3,'fonemas')

im,d=canvas('04 / SIRINGUA · AGUA + RESPUESTA','El jardín responde','Cada palabra articula agua; después, un motivo breve del pájaro responde.')
wav=out/f"siringua-mensaje-de-teia-s{seed}-{rid}.wav"
with wav.open('rb') as f:
    f.seek(44); raw=f.read(); n=len(raw)//4
samples=struct.unpack('<%df'%(n),raw)
left,right=80,1120; mid=355
d.line((left,mid,right,mid),fill='#33403d',width=1)
count=850; pts=[]
for x in range(count):
    a=int(x*n/count); b=max(a+1,int((x+1)*n/count)); v=max(samples[a:b],key=abs)
    pts.append((left+x*(right-left)/count,mid-v*58))
d.line(pts,fill=CYAN,width=2)
d.text((80,465),'AGUA · voz articulada',font=mono,fill=CYAN)
d.text((630,465),'AVE · llamada en respuesta',font=mono,fill=GOLD)
d.text((80,532),excerpt,font=font('georgia.ttf',24),fill=PAPER)
d.text((80,600),f"{meta['duration']} s · semilla {seed} · dos líneas, una conversación",font=mono,fill=DIM)
save_stage(im,4,'agua-y-ave')

# PNG final: última etapa real del proceso.
final=stages[-1]
final_img=Image.open(final).convert('RGB')
final_img.save(out/f'pieza-s{seed}-{rid}.png')
# OG a partir del cuadro final, encuadrado en 1200×630.
og=final_img.resize((1200,630),Image.Resampling.LANCZOS)
og.save(out/'og.png')
# Borrador sucesivo de las cuatro etapas capturadas.
gif=out/f'siringua-proceso-s{seed}-{rid}.gif'
frames=[Image.open(p).convert('P',palette=Image.Palette.ADAPTIVE,colors=128) for p in stages]
frames[0].save(gif,save_all=True,append_images=frames[1:],duration=[1500,1500,1800,1800],loop=0,optimize=True)

readme=f'''# Prueba de un mensaje abierto en Siringua

El protocolo sí puede alimentar una obra si ésta consulta el evento del canal,
recupera el contenido JSON de IPFS y lo interpreta como texto. La cadena registra
el evento y la referencia; Teia no canta ni modifica la obra por sí sola.

Esta prueba sigue en modo local un mensaje público del canal **{meta['channel']}**,
mensaje **{meta['message']}**, CID `{meta['cid']}`. La lectura real se verificó
siguiendo el evento de Teia/TzKT al registro del big map y de ahí al JSON del
gateway IPFS. La síntesis usa el fragmento de 18 palabras que aparece en el PNG.
El sintetizador consume la transcripción archivada: no hace la consulta de red
durante la generación de audio. Por eso es una prueba del recorrido y de la voz,
no todavía un cliente Teia en vivo.

## Escucha

- `agua-habla-s{seed}-{rid}.wav`: texto articulado por agua.
- `respuesta-del-ave-s{seed}-{rid}.wav`: notas del ave.
- `siringua-mensaje-de-teia-s{seed}-{rid}.wav`: mezcla final.
- `siringua-mensaje-de-teia-s{seed}-{rid}.m4a`: versión ligera para escuchar.

La pronunciación proviene de `{meta['provider']}` y cubrió las 18 palabras.
VozAgua articula cada palabra; el ave responde palabra a palabra. Semilla:
**{seed}**. Duración: **{meta['duration']} s**. Los fonemas ARPABET y su IPA quedan
en `registro.json`.

## Proceso visual

El GIF reúne cuatro capturas sucesivas de la transformación: evento/canal,
fragmento recuperado, fonemas entregados al instrumento y audio de agua con
respuesta del ave. Son visualizaciones de etapas efectivamente usadas, no capturas
del navegador ni supuestos pasos internos de eSpeak.

1. `01-registro`: canal abierto y referencia del mensaje verificados en Teia/TzKT.
2. `02-mensaje`: fragmento del JSON público de IPFS elegido para la escucha.
3. `03-fonemas`: salida de eSpeak NG y adaptación a Siringua.
4. `04-agua-y-ave`: forma de onda de la mezcla renderizada por los dos motores.

## Receta y alcance

- Canal/mensaje: {meta['channel']}/{meta['message']} · CID {meta['cid']}.
- Idioma/proveedor: en-US · {meta['provider']}.
- Adaptador: `siringua-arpabet-adapter-1`.
- Semilla: {seed}. Hash completo de esta ejecución: `{meta['runHash']}`.
- Ejecutar desde `research/rejilla`: `node aves-que-aprenden/prueba-teia-siringua.cjs`.
- Los motores son locales; la fuente Teia se verificó por separado con lectura web.
- Los mensajes deben tratarse como datos, filtrar ocultamientos/ediciones y limitar
  longitud antes de sintetizar. Los gateways y el indexador TzKT son dependencias.
- Sin cartera conectada, publicación, gasto de XTZ ni edición acuñada.
'''
(out/'README.md').write_text(readme,encoding='utf-8')
assets=[gif,out/f'pieza-s{seed}-{rid}.png',out/'og.png',out/f'siringua-mensaje-de-teia-s{seed}-{rid}.m4a',out/'README.md',out/'registro.json',*out.glob('*.wav'),*stages]
gif_frame=Image.open(gif)
gif_duration=sum((gif_frame.seek(i) or gif_frame.info.get('duration',0)) for i in range(gif_frame.n_frames))
recipe={'runHash':meta['runHash'],'imageBasisHash':meta['imageBasisHash'],'nonce':meta['nonce'],'seed':seed,'assetHashes':{str(p.relative_to(out)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in assets},'gifDurationMs':gif_duration,'gifFrames':gif_frame.n_frames,'gifBytes':gif.stat().st_size}
(out/'receta.json').write_text(json.dumps(recipe,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'gif':str(gif),'stages':[str(p) for p in stages],'final':str(out/f'pieza-s{seed}-{rid}.png'),'og':str(out/'og.png'),'gifBytes':gif.stat().st_size,'recipe':str(out/'receta.json')},ensure_ascii=False,indent=2))
