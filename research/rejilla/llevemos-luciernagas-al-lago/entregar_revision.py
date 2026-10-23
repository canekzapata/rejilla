"""Cierre documental y visual; no renderiza ni mezcla la canción."""
from pathlib import Path
import hashlib,io,json,math,shutil,zipfile
from PIL import Image,ImageDraw,ImageFont,ImageOps
ROOT=Path(__file__).resolve().parent;OUT=ROOT/(ROOT/'REVISION-EN-CURSO.txt').read_text().strip();TAG=OUT.name.split('-')[-1]
P=json.loads((OUT/'partitura-v8.json').read_text('utf8'));V=json.loads((OUT/'validacion-v8.json').read_text('utf8'))
OLD=ROOT/'luciernagas-partitura-s1-054923e7c401';D=P['duracion'];C0,C1=P['centro']
def put(name,data):
 with (OUT/name).open('xb') as f:f.write(data)
def txt(name,s):put(name,s.encode('utf8'))
def js(name,obj):txt(name,json.dumps(obj,ensure_ascii=False,indent=1))
def f(n,b=False):return ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if b else 'arial.ttf'),n)
def save(name,im):
 b=io.BytesIO();im.save(b,format='PNG');put(name,b.getvalue())

# Sin rasterizar de nuevo el terreno ni fabricar etapas del pasado.
im=Image.new('RGB',(1600,1100),'#102421');d=ImageDraw.Draw(im)
d.text((45,30),'Llevemos unas luciérnagas al lago',font=f(43,True),fill='#f4e9c4')
d.text((47,92),'Partitura revisada / 36 partes / 4:18.667 / Traspuesta 1 / semilla 2026102201',font=f(23),fill='#bad2b9')
x0,x1,top,row=320,1550,205,18
for a,b in P['oscuridades']:
 d.rectangle((x0+(x1-x0)*a/D,top-15,x0+(x1-x0)*b/D,top+36*row),fill='#244039')
for j,tr in enumerate(P['partes']):
 y=top+j*row;d.text((40,y-7),f'{j+1:02} {tr["nombre"][:31]}',font=f(14),fill='#c4d6c0')
 for e in P['eventos'][tr['id']]:
  for a,b in e['salidas']:
   xa=x0+(x1-x0)*a/D;xb=x0+(x1-x0)*b/D
   d.line((xa,y,max(xa+1,xb),y),fill='#f2ad74' if e.get('libre') else '#9cd9c6',width=2)
for s in P['secciones']:
 x=x0+(x1-x0)*s['t']/D;d.line((x,top-20,x,top+36*row),fill='#668176')
 d.text((x+2,top-48),s['id'],font=f(21,True),fill='#f4e9c4')
d.text((45,906),'contacto → cuerda → junco → una espera en «en / otras»',font=f(32,True),fill='#f4e9c4')
d.text((45,957),'13 acontecimientos en el centro · 8 oscuridades · 24 llegadas heredadas',font=f(25),fill='#c4d6c0')
d.text((45,1002),'Pared: resonancia compartida / contagio de ataques / casi continuidad',font=f(24),fill='#c4d6c0')
d.text((45,1050),'Revisión 8. Escritura y estados comprobados; todavía sin audio.',font=f(20),fill='#e8ad7d')
png=f'luciernagas-partitura-final-s1-{TAG}.png';save(png,im);save(f'proceso/09-partitura-consolidada-s1-{TAG}.png',im)
og=Image.new('RGB',(1200,630),'#102421');small=im.resize((916,630));og.paste(small,(142,0));save('og.png',og)

# Biblioteca y motores fijados para que los nombres no dependan de un estado futuro.
lib=ROOT/'instrumentos-734cad81b33e';dest=OUT/'realizacion/biblioteca';dest.mkdir(exist_ok=False)
for p in sorted(lib.rglob('*')):
 if p.is_file():
  target=dest/p.relative_to(lib);target.parent.mkdir(parents=True,exist_ok=True)
  with target.open('xb') as h:h.write(p.read_bytes())
for name in ['campana-motor.mjs','campana-campana.py','el-androide-en-la-estacion__render_tt.py']:
 if (OLD/'fuentes'/name).exists():put('realizacion/'+name,(OLD/'fuentes'/name).read_bytes())
txt('realizacion/README.md','''# Fuentes fijadas para la realización

`modelos_memoria.py`, `instrumentos.py` y `motores.py` forman el núcleo de esta
revisión. `biblioteca/` conserva las catorce fichas y sus motores originales.
No modificar sus fuentes compartidas al interpretar. Las guías vocales, bancos
de Difonos/Sabina y adaptadores de mezcla se preparan en la fase de producción.
El contrato completo vive en ../INTERPRETACION.md. No se ha sintetizado audio.
''')

# GIF de seis etapas reales, sin presentar revisiones como un algoritmo interno.
ordered=[next((OUT/'proceso').glob('01-herencia-*.png')),next((OUT/'proceso').glob('02-frases-*.png')),
         next((OUT/'proceso').glob('03-contacto-*.png')),next((OUT/'proceso').glob('04-*.png')),
         next((OUT/'proceso').glob('08-centro-final-*.png')),OUT/'proceso'/f'09-partitura-consolidada-s1-{TAG}.png']
labels=['01 / lectura actual de la partitura anterior','02 / fraseo y respiración','03 / contacto y relevo calculado',
        '04 / reunión y nueva forma','08 / edición final del centro','09 / partitura consolidada']
frames=[]
for p,label in zip(ordered,labels):
 frame=Image.new('RGB',(1000,700),'#102421');pic=Image.open(p).convert('RGB');pic.thumbnail((980,635))
 frame.paste(pic,((1000-pic.width)//2,45+(635-pic.height)//2));dr=ImageDraw.Draw(frame)
 dr.text((18,12),label,font=f(20,True),fill='#f4e9c4');frames.append(frame.quantize(colors=160))
gif=f'luciernagas-reescritura-proceso-s1-{TAG}.gif'
buffer=io.BytesIO();frames[0].save(buffer,format='GIF',save_all=True,append_images=frames[1:],duration=[1350]*5+[1750],loop=0,disposal=2)
put(gif,buffer.getvalue());assert len(buffer.getvalue())<=15*1024*1024
review=Image.new('RGB',(1500,700),'#d5dfcf')
for j,frame in enumerate(frames):
 thumb=frame.convert('RGB').resize((500,350));review.paste(thumb,((j%3)*500,(j//3)*350))
save(f'proceso/10-revision-de-cuadros-gif-s1-{TAG}.png',review)
txt('proceso/README.md',f'''# Etapas reales de esta revisión

Semilla de terreno 1; composición 2026102201; ejecución `{TAG}`. Cada archivo
mantiene su nombre e identificador. No se sobreescribieron borradores.

1. **01 herencia:** lectura visual actual del JSON v4. Es una reconstrucción
   de la escritura anterior hecha en esta sesión, no una captura de su creación.
2. **02 frases:** checkpoint real tras reescribir voz y respiración.
3. **03 contacto:** checkpoint real tras escribir el contacto y su cadena central.
4. **04 reunión:** primera composición completa de esta revisión, todavía v5.
5. **05 edición completa / 06 centro editado:** primeras pruebas de PDF v7.
6. **07 edición final / 08 centro final:** PDF v8, con el tercer corte completado.
7. **09 consolidada:** ventanas de salida del JSON v8, sin cambiar datos para el dibujo.
8. **10 revisión de cuadros:** contacto de los seis cuadros que contiene el GIF.

El GIF selecciona 01/02/03/04/08/09. Muestra borradores y edición reales,
no un visor en tiempo real ni los pasos internos de una síntesis sonora.
Duración prevista 8.5 s, loop infinito; tamaño {len(buffer.getvalue())} bytes.
Revisar PNGs y cuadros antes de declarar inspección visual final en el cierre.

La ejecución `a1eab3500102` quedó interrumpida por reutilizar una variable de
masa como límite temporal. Se conserva aparte con ESTADO.md y tres etapas.
Se corrigió y se ejecutó de nuevo en esta carpeta exclusiva.
''')
pdf=f'luciernagas-partitura-analizada-v8-s1-{TAG}.pdf';xml=f'luciernagas-partitura-completa-v8-s1-{TAG}.musicxml'
txt('README.md',f'''# Llevemos unas luciérnagas al lago · revisión 8

Canek Zapata / Rejilla / 22 de octubre de 2026. **36 partes, 3,868 eventos
internos, 4:18.667.** Proto punk folk con contacto, memoria y pared final.

- [Partitura y guía analítica, 35 páginas]({pdf}).
- [Análisis completo de la pieza](ANALISIS-DE-LA-PIEZA.md): forma, voz,
  matemáticas, estados, antecedentes, comparación y objeciones pendientes de escucha.
- [MusicXML de todas las partes]({xml}), [eventos CSV](luciernagas-eventos-v8-s1-{TAG}.csv)
  y [partitura canónica](partitura-v8.json).
- [Contrato de interpretación](INTERPRETACION.md) y [validación](validacion-v8.json).
- [PNG final]({png}), [GIF del proceso]({gif}) y [etapas](proceso/README.md).

## Cambio compositivo

La voz tiene fraseo propio. Un roce falla y después libera un parcial; la cuerda
recibe sus envolventes, evoluciona y entrega una captación al junco. La pérdida
inicial produce una espera de **0.773579975 s** en palabras precisas del coro.
Veinticuatro planes heredan fuentes, masas y fases. Las tres olas sostienen,
propagan ataques y casi forman un cuerpo continuo. Los tres cortes dejan pérdidas.

El centro conserva sesenta segundos: trece acontecimientos y ocho oscuridades,
38.621 s de salida cerrada. El órgano conserva tres/cinco divisores a igual
presión con pasados distintos. Cambiar el orden de encuentros entre cajas deja
24.521 cents de distancia en el vector final de control.

## Vigencia y límites

Prevalecen **JSON v8, transportes-memoria-v8, paquete-modal-v6 y PDF/XML/CSV v8**.
`PARTITURA-FINAL.txt` identifica estos documentos. V5–v7 y las primeras ediciones
son borradores conservados. La entrega v4 anterior permanece intacta.

Se comprobaron estados, continuidades, pérdidas, ventanas, afinación y exportación.
No se generó ni escuchó audio. La dicción, el sostén del centro, las transiciones
de aristas y la claridad de la pared siguen para la interpretación posterior.
El visor elegido es el anterior; no se produjo un visor nuevo ni video de canción.

Los scripts escriben en exclusivo. No relanzarlos sobre esta carpeta.
El identificador completo, nonce y huellas están en las recetas. Los textos
congelados en fuentes conservan su contexto original: sus enlaces relativos
internos pueden referirse al repositorio de origen, no al directorio de esta copia.
''')
txt('PARTITURA-FINAL.txt',f'partitura-v8.json\ndatos/transportes-memoria-v8.json\ndatos/paquete-modal-v6.json\n{pdf}\n{xml}\nINTERPRETACION.md\nANALISIS-DE-LA-PIEZA.md\n')
put('fuentes/entregar_revision.py',Path(__file__).read_bytes())

# Receta anterior al ZIP: evitar autorreferencias y registrar todos los borradores.
files={p.relative_to(OUT).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
       for p in sorted(OUT.rglob('*')) if p.is_file()}
js('receta-final.json',{'id':TAG,'version':'partitura-8.0','archivos':files,
    'validacion':'validacion-v8.json','original_v4_intacto':True,'sin_audio':True,
    'limites':'La receta fija escritura y proceso. La inspección visual posterior al cierre se registra en PAQUETE.json y bitácora.'})
zipname=f'luciernagas-partitura-analisis-v8-s1-{TAG}.zip'
with zipfile.ZipFile(OUT/zipname,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(OUT.rglob('*')):
  if p.is_file() and p.name!=zipname:z.write(p,p.relative_to(OUT).as_posix())
with zipfile.ZipFile(OUT/zipname) as z:assert z.testzip() is None;entries=len(z.namelist())
g=Image.open(OUT/gif);duration=0
for i in range(g.n_frames):g.seek(i);duration+=g.info.get('duration',0)
assert duration<=10000 and g.info.get('loop')==0
js('PAQUETE.json',{'zip':zipname,'sha256':hashlib.sha256((OUT/zipname).read_bytes()).hexdigest(),'bytes':(OUT/zipname).stat().st_size,
 'archivos':entries,'crc_ok':True,'gif':gif,'gif_frames':g.n_frames,'gif_duracion_ms':duration,'gif_bytes':(OUT/gif).stat().st_size,
 'nota':'Inspección visual de PNG/PDF/GIF se registra al finalizar; CRC y duración no la sustituyen.'})
print(json.dumps({'out':str(OUT),'zip':zipname,'archivos':entries,'bytes_zip':(OUT/zipname).stat().st_size,'gif_ms':duration,
                 'gif_bytes':(OUT/gif).stat().st_size},ensure_ascii=False))
