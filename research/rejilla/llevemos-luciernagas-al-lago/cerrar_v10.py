"""Cerrar la edición nueva: PNG, GIF de etapas reales, índice y huellas."""
from pathlib import Path
import json,hashlib,sys
from PIL import Image,ImageDraw,ImageFont
from resolver_v10 import cargar,ventanas
OUT,P=cargar();ROOT=Path(__file__).resolve().parent;TAG=OUT.name.split('-')[-1]
def put(name,b):
    with (OUT/name).open('xb') as f:f.write(b)
def text(name,s):put(name,s.encode('utf8'))
def font(n,b=False):return ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if b else 'arial.ttf'),n)
im=Image.new('RGB',(1800,1200),'#142523');dr=ImageDraw.Draw(im)
dr.text((38,25),'Llevemos unas luciérnagas al lago',font=font(41,True),fill='#efe7ce')
dr.text((40,87),'Partitura v10.1 / 36 partes / 4:18.667 / terreno 1 / sin audio nuevo',font=font(25),fill='#bbcfbd')
x0,x1,top,row=375,1760,190,22
for k,tr in enumerate(P['partes']):
    y=top+k*row;dr.text((25,y-7),f'{tr["numero"]:02} {tr["nombre"][:35]}',font=font(15),fill='#cbd9c8')
    for e in P['eventos'][tr['id']]:
        for a,b in ventanas(e,P['cortes_buses']):dr.line((x0+(x1-x0)*a/P['duracion'],y,x0+(x1-x0)*b/P['duracion'],y),width=3,fill='#eead75' if e.get('revision')=='v10' else '#8fbda8')
for sec in P['secciones']:
    x=x0+(x1-x0)*sec['t']/P['duracion'];dr.line((x,top-12,x,top+36*row),fill='#54736a');dr.text((x+2,top-39),sec['id'],font=font(23,True),fill='#efe7ce')
dr.text((40,1020),'Nueve episodios de guitarra / cuatro recorridos de junco / regreso recalculado',font=font(29,True),fill='#efe7ce')
dr.text((40,1075),'Partitura completa: PDF de 26 páginas + MusicXML + JSON/CSV + controles resueltos',font=font(23),fill='#cbd9c8')
dr.text((40,1120),'Las líneas indican salidas escritas; no son medidas de volumen ni una escucha de la canción.',font=font(22),fill='#cbd9c8')
png=f'luciernagas-partitura-v10.1-s1-{TAG}.png';assert not (OUT/png).exists();im.save(OUT/png)
stage=OUT/'proceso'/f'09-partitura-consolidada-s1-{TAG}.png';assert not stage.exists();im.save(stage)
og=im.resize((1200,800));og=og.crop((0,0,1200,630));og.save(OUT/'og.png')
frames=[];paths=[]
for prefix in ['01-','02-','03-','04-','05-','09-']:
    p=next((OUT/'proceso').glob(prefix+'*.png'));paths.append(p.name);pic=Image.open(p).convert('RGB');pic.thumbnail((1140,680))
    frame=Image.new('RGB',(1200,740),'#142523');frame.paste(pic,((1200-pic.width)//2,45+(680-pic.height)//2))
    ImageDraw.Draw(frame).text((18,12),p.name.split('-s1-')[0],font=font(21),fill='#efe7ce');frames.append(frame.quantize(colors=160))
gif=f'luciernagas-escritura-v10.1-s1-{TAG}.gif';frames[0].save(OUT/gif,save_all=True,append_images=frames[1:],duration=[1300]*5+[1500],loop=0,disposal=2)
image=Image.open(OUT/gif);duration=0
for i in range(image.n_frames):image.seek(i);duration+=image.info.get('duration',0)
assert duration<=10000 and (OUT/gif).stat().st_size<=15*1024*1024
sheet=Image.new('RGB',(1800,740),'#dae0d6')
for i in range(image.n_frames):
    image.seek(i);pic=image.convert('RGB');pic.thumbnail((600,350));sheet.paste(pic,((i%3)*600,(i//3)*370))
sheet.save(OUT/'proceso'/f'10-cuadros-del-gif-s1-{TAG}.png')
text('proceso/README.md',f'''# Etapas reales de la partitura

Semillas: terreno 1; composición 2026102201. Identificador {TAG}; hash completo y nonce en inicio.json. Todos los archivos se crearon sin sobrescribir una ruta previa.

01: lectura actual de las ventanas del JSON v9, conservada antes de reescribir. Es una reconstrucción de esa escritura para compararla; no se presenta como captura de su creación original. 02: checkpoint después de recomponer exposición y acompañamiento. 03: checkpoint después de la captura completa y los cuatro recorridos del centro. 04: primer cierre del regreso recalculado. 05: contacto de las 26 páginas del PDF efectivamente generado. 06–08: ampliaciones reales del PDF para revisar el centro, los episodios y una página completa. 09: vista final de la partitura canónica v10.1. 10: los seis cuadros extraídos del GIF para inspección.

El GIF selecciona {', '.join(paths)}. Reúne borradores y edición de esta ejecución, no pasos ocultos de un generador ni un visor de la canción. Duración comprobada {duration/1000:.1f} s, {image.n_frames} cuadros, loop infinito; tamaño {(OUT/gif).stat().st_size} bytes. No se generó audio ni video.

La primera ejecución 1672edfb5300 se conserva con ESTADO.md: se corrigieron una ambigüedad de drive/impulsos del contacto y una parte vacía antes de la edición final. La prueba de continuidad también distinguió un hueco compuesto de 1.783 s de una guarda numérica inicialmente demasiado estricta; no se cambió la música para satisfacer una cuota arbitraria de silencio.
''')
text('README.md',f'''# Llevemos unas luciérnagas al lago · partitura corregida

Canek Zapata · 22 de octubre de 2026 · revisión 10.1 · 36 partes · 4:18.667.

**[Abrir partitura completa: PDF de 26 páginas](luciernagas-partitura-v10.1-s1-{TAG}.pdf)** · [MusicXML](luciernagas-partitura-v10.1-s1-{TAG}.musicxml) · [JSON canónico](partitura-v10.1.json) · [CSV](luciernagas-eventos-v10.1-s1-{TAG}.csv).

[Análisis de la reescritura](ANALISIS-DE-LA-REESCRITURA.md) · [lecturas del poemario y teoría, comparación con tres cumbias](LECTURAS-Y-COMPARACION.md) · [validación de escritura](validacion-escritura-v10.1.json) · [prueba causal y edición](datos/causalidad-y-edicion-verificadas.json).

Se reescribió la exposición en nueve episodios de guitarra con respuestas del acompañamiento; se restauraron raíz y tenis; la voz principal cede episodios completos. El centro tiene cuatro recorridos, amortiguación y cruces con fases heredadas. Su llegada alimenta 24 transportes nuevos. Terminal y androide conservan su diálogo reconocible cerca de 2:40, modificado desde la nueva fuente. La espera aprendida es {P['centro_v10']['paquete']['espera_aprendida_s']:.6f} s y vuelve en canto y arpa. No se conserva el audio previo por empalme.

[PNG de la partitura]({png}) · [GIF del proceso, {duration/1000:.1f} s]({gif}) · [etapas y límites](proceso/README.md). og.png: 1200×630.

**Esta entrega corrige la partitura. No se renderizó la canción ni se produjo máster, visor o video nuevos.** El audio Relevos v9 permanece como antecedente; no representa esta escritura. La comprobación de estados y notación no acredita interés musical ni balance perceptual.

`interpretacion-resuelta-v10.1.json` expande eventos, ventanas tras cortes, parámetros, ganancias y controles para preparar una futura interpretación. `fuentes/` conserva composición, modelos, resolución, verificación y edición. Se ejecutan los programas originales desde la carpeta de la pieza; las copias congeladas registran su versión. Las bibliotecas nativas siguen fijadas en la entrega v8; no se reemplazan por familias genéricas.

Para repetir en una carpeta nueva: recomponer_v10.py iniciar, exposicion, centro, regreso; afinar_v10.py; resolver_v10.py; verificar_v10.py; editar_v10.py; cerrar_v10.py. El primer paso crea un hash/nonce nuevo; todos los demás rechazan salidas existentes. Las lecturas y el análisis acompañan la edición y sus fuentes consultadas. No se hizo push.
''')
put('fuentes/cerrar_v10.py',Path(__file__).read_bytes())
# Huellas de todos los archivos, incluida la imagen inicial y las fuentes, sin autorreferencia.
manifest={'version':P['version'],'semilla_terreno':1,'semilla_composicion':2026102201,'archivos':{},'fuentes_consultadas':{}}
for file in sorted(OUT.rglob('*')):
    if file.is_file():manifest['archivos'][str(file.relative_to(OUT))]=hashlib.sha256(file.read_bytes()).hexdigest()
for file in [ROOT.parent/'COMPOSITOR.md',ROOT/'CRITICA-RELEVOS-FRENTE-A-DUNA-2026-10-22.md',
 ROOT.parent/'por-aqui-tambien-se-baila/reescribir.py',ROOT.parent/'lo-que-la-cinta-olvida/partitura.py',ROOT.parent/'la-ciudad-se-hunde-bailando/partitura.py']:
    manifest['fuentes_consultadas'][str(file.resolve())]=hashlib.sha256(file.read_bytes()).hexdigest()
text('receta-huellas.json',json.dumps(manifest,ensure_ascii=False,indent=1))
(ROOT/'PARTITURA-ACTUAL.txt').write_text(OUT.name,encoding='utf8');print('Cierre',OUT,'GIF',duration,'ms',flush=True)
