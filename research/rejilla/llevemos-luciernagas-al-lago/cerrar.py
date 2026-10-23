"""Cierre documental, imágenes del proceso y paquete de partitura. Sin audio."""
from pathlib import Path
import json,hashlib,io,zipfile
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
ROOT=Path(__file__).resolve().parent;OUT=ROOT/(ROOT/'ULTIMA.txt').read_text().strip();TAG=OUT.name.split('-')[-1]
P=json.loads((OUT/'partitura-v4.json').read_text('utf8'));V=json.loads((OUT/'validacion-v4.json').read_text('utf8'));R=json.loads((OUT/'datos/recorrido.json').read_text('utf8'))
def put(f,b):
 with (OUT/f).open('xb') as h:h.write(b)
def text(f,s):put(f,s.encode('utf8'))
def js(f,v):text(f,json.dumps(v,ensure_ascii=False,indent=1))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def font(s,b=False):return ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if b else 'arial.ttf'),s)
def png(name,im):
 buf=io.BytesIO();im.save(buf,format='PNG');put(name,buf.getvalue())
im=Image.new('RGB',(1600,1000),'#101713');d=ImageDraw.Draw(im)
d.text((48,30),'Llevemos unas luciérnagas al lago',font=font(43,True),fill='#e9efc6')
d.text((48,92),'Partitura final / 36 partes / 5,717 eventos / 4:18.667 / sin audio',font=font(24),fill='#becd9f')
x0,x1=330,1545;y0=171;row=19.5;D=P['duracion']
for a,b in P['oscuridades']+P['agujeros_pared']:
 d.rectangle((x0+(x1-x0)*a/D,y0-14,x0+(x1-x0)*b/D,y0+36*row),fill='#2a3b2c')
for j,tr in enumerate(P['partes']):
 y=y0+j*row;d.text((40,y-7),f'{j+1:02} {tr["nombre"][:31]}',font=font(15),fill='#cad6ae')
 for e in P['eventos'][tr['id']]:
  x=x0+(x1-x0)*e['t']/D;xx=x0+(x1-x0)*(e['t']+e['dur'])/D
  d.line((x,y,max(x+1,xx),y),fill='#e0a776' if e.get('libre') else '#9edbc1',width=2)
for s in P['secciones']:
 x=x0+(x1-x0)*s['t']/D;d.line((x,y0-20,x,y0+36*row),fill='#72805b');d.text((x+2,y0-43),s['id'],font=font(18,True),fill='#eef3ce')
d.text((48,934),'La posición regresa; la afinación, el órgano y la respuesta conservan el recorrido.',font=font(23),fill='#e9efc6')
result=f'luciernagas-partitura-resultado-s1-{TAG}.png';png(result,im);png(f'proceso/08-escritura-final-s1-{TAG}.png',im)
og=ImageOps.fit(im,(1200,630),method=Image.Resampling.LANCZOS,centering=(.5,.5));png('og.png',og)

# Secuencia de estados efectivamente producidos, sin simular trazado o sonido.
files=sorted((OUT/'proceso').glob('*.png'));frames=[]
for p in files:
 a=Image.open(p).convert('RGB');a=ImageOps.contain(a,(1120,700),method=Image.Resampling.LANCZOS)
 canvas=Image.new('RGB',(1120,750),'#101713');canvas.paste(a,((1120-a.width)//2,(700-a.height)//2))
 draw=ImageDraw.Draw(canvas);label=p.name.split('-s1-')[0].replace('-',' ');draw.text((22,716),label,font=font(18),fill='#e4edc8')
 frames.append(canvas.quantize(colors=128))
gif=f'luciernagas-escritura-proceso-s1-{TAG}.gif';buf=io.BytesIO();frames[0].save(buf,format='GIF',save_all=True,append_images=frames[1:],duration=1100,loop=0,optimize=True);put(gif,buf.getvalue())
with Image.open(OUT/gif) as g:
 durations=[]
 for j in range(g.n_frames):g.seek(j);durations.append(g.info.get('duration',0))
 assert sum(durations)<=10000 and g.info.get('loop')==0
assert (OUT/gif).stat().st_size<=15*1024*1024
js('datos/proceso-medidas.json',{'gif':gif,'cuadros':len(frames),'duracion_ms':sum(durations),'bytes':(OUT/gif).stat().st_size,'loop':0,'tipo':'borradores y revisiones reales; no video de canción ni pasos internos del compositor'})
rows='\n'.join(f'| {tr["numero"]:02} | {tr["nombre"]} | {tr["funcion"]} | {len(P["eventos"][tr["id"]])} |' for tr in P['partes'])
readme=f'''# Llevemos unas luciérnagas al lago

Canek Zapata · 22 de octubre de 2026 · partitura 4.0 · **4:18.667 · 36 partes · 5,717 eventos**.

Proto punk folk estadounidense cruzado con escritura computacional: rasgueo áspero, pregunta y respuesta; centro silencioso con acciones materiales y armónicos; polifonía de carbono; salida a una pared con tres agujeros. Esta entrega contiene la composición escrita, dos diseños instrumentales y su proceso. **La interpretación, la escucha y los másters quedan para la siguiente etapa.**

## Abrir primero

- [Partitura PDF vigente, 36 páginas](partitura-luciernagas-r6-s1-{TAG}.pdf): dirección, tema, recorrido, instrumentos, centro gesto por gesto, letra/prosodia y todas las partes en notación proporcional. Las páginas de conjunto son A2 vertical; conviene ampliar para leer detalles.
- [MusicXML completo vigente](partitura-completa-r6-s1-{TAG}.musicxml): 36 partes y 125 posiciones editoriales por parte; silencios, voces paralelas y alteraciones fraccionarias. Las celdas del centro no son compases con pulso.
- [Partitura canónica](partitura-v4.json) y [CSV de todos los eventos](eventos-completos-r5-s1-{TAG}.csv): segundos, Hz, MIDI continuo, gesto, sílaba, controles y filiación. Estos datos contienen más información que la notación impresa.
- [PNG del conjunto]({result}) · [GIF de la escritura]({gif}) · [orden y explicación del proceso](proceso/README.md).
- [Verificaciones](validacion-v4.json). Revisadas visualmente las 36 páginas por contactos y los detalles de tema, centro, corrección y polifonía. No hubo audición nueva.

## Lo que ocurre y por qué vuelve distinto

| Tiempo | Pasaje | Función |
|---|---|---|
| 0:00–0:26.667 | I / La lata y la raíz | Riff directo; Q y R se presentan antes de la transformación. |
| 0:26.667–0:53.333 | II / Cabezas y mosquitos | Verso y respuestas; el órgano aprende un primer estado. |
| 0:53.333–1:20 | III / Llevemos | Coro del poema; se prepara la diferencia entre cajas. |
| 1:20–1:33.333 | IV / La cuerda se pega | Se pierden ataques y se corta la salida antes del centro. |
| 1:33.333–2:33.333 | V / Pantano | 18 gestos irregulares y seis oscuridades, que suman 19.8 s. Sin batería, voces o señales métricas escritas. |
| 2:33.333–3:00 | VI / Carbono | Arpa, cuerda y órgano con memoria; terminal y bajo de androide se relevan; entran las trayectorias de junco. |
| 3:00–3:26.667 | VII / Otra boca | Regresa la letra con afinación y final transformados. |
| 3:26.667–4:06.667 | VIII / Casi una pared | Tres olas de densidad y tres cortes de todo el conjunto; los vocoders toman el coro. |
| 4:06.667–4:18.667 | IX / Dos residuos | Corte de banda; junco y waterphone caen a distinta velocidad; silencio final. |

| Material inicial | Operación | Consecuencia | Pasaje |
|---|---|---|---|
| Q: E–B–C, F tardío y E | Reparto entre cuerdas, afinación y parcialización | Una frase reconocible termina en otro cuerpo | I, V, VI y VII |
| Primer E4 de guitarra | Transporte de parciales 1, 2, 3 y 5 | Cuatro destinos con trayectorias explícitas, no un simple fundido | 28 planes desde VI |
| Tres acuerdos locales de afinación | Mínimos cuadrados ponderados sobre un ciclo con deuda | Volver a la posición no devuelve la afinación inicial | Tres cajas; deuda final {V['deuda_final_cents']:.6f} cents |
| Presión .47 del órgano | Cruzar .93 y volver a .47 con histéresis | Tres divisores primero y cinco después | II/III frente a VI |
| Una fase de partida | Relojes integrados 17/19/23/29, velocidad modulada por pendiente | El regreso no reinicia todas las voces al uno | II, silencio interno en V y VI |
| Una voz que pregunta | Ceder el centro a acciones de otros cuerpos | El coro recibe una respuesta que no controla por completo | V, VI y VIII |

## Dos instrumentos nuevos y una variante necesaria

**Guitarra de alambre y tres cajas.** Seis cuerdas y ocho modos por caja; púa, roce, armónico, madera y apagado. El dedo que toca el nodo y la púa que excita están separados para no anular el armónico buscado. `parametros_guitarra(e)` convierte altura escrita a fundamental y evita aplicar dos veces los cents de la caja. Conserva estados y fases; pesos del acuerdo (1,2,1). Es un modelo modal abstracto, sin calibración de guitarra real.

**Junco de acuerdos.** Cuatro voces, hasta dieciséis trayectorias con fase persistente. `transporte` calcula planes; `Junco.avanzar` integra fases en log Hz. Se verificaron marginales, caso identidad, caso pequeño de costo 4 y estado finito. Falta realizar y escuchar su señal completa. La masa y la norma de envolventes no se confunden con julios acústicos.

**Arpa existente, variante afinable.** El original recibe `cuerda` pero no retuna por `midi`. Se fijó [una variante](fuentes/motores-arpa-afinable.py) que retuna la cuerda excitada sin reiniciar su fase, conservando los enlaces. El original se conserva en fuentes. No se cuenta como un tercer instrumento nuevo.

Los modelos vigentes están en [instrumentos-v3.py](fuentes/instrumentos-v3.py); las instrucciones completas están en `interpretacion` de la partitura. Se han calculado estados y planes; no se han producido muestras sonoras ni certificado timbres.

## Terreno y referencias que elegiste

Se abrió el atlas y el visor real de Traspuesta con Chrome automatizado, sirviendo los archivos locales mediante interceptación de peticiones; el navegador de la app no respondió y el acceso loopback falló. Se compararon las láminas 1, 27 y 43. Se eligió **Traspuesta 1 / El Teso del Tecolote**, llanura de meandros con lagos de herradura, con **Pinahuizapan** como zona del recorrido. Las capturas de las otras dos láminas están en datos.

El campo original mide 9 km de lado. La ruta compuesta recorre {R['distancia_m']/1000:.3f} km, con {R['ascenso_m']:.3f} m de ascenso y descenso acumulados; sale y vuelve a {R['salida_m']:.3f} m. No es un descenso monótono ni una carretera real. u crece al este y v al sur; las alturas se muestrean del campo, mientras el tiempo, humedad, olor y ficción de la lata son decisiones de composición. La integración de giros absolutos es una regla de memoria nuestra.

Canek señaló como referencias las partes centrales de **El río no tiene tronco** (Alice Coltrane: río, canon del delta y paso al mar) y **V / Abajo · me oxido** de **El androide en la estación** (2:33–3:24). Se revisaron sus partituras y motores; no se afirmó una audición nueva. Se tomaron relaciones: fuente común, relojes propios, relevo, serie, estados y cambio de cuerpo. Ambas referencias ya quedaron anotadas en COMPOSITOR.md.

Texto: cuatro versos del poema de las luciérnagas y fragmentos de cabezas/mosquito se identifican en `letra`. Las tres líneas de lata, raíz y tenis, las respuestas y la petición de apagar el teléfono son escritura nueva/adaptación identificada. La lectura de Scelsi, Cagney, Cage/Clarkson, Arvatov, Bois/Krauss y Drucker está registrada en las notas previas congeladas en fuentes. La alusión a Lachenmann orienta presión, roce y resistencia; no anuncia una transcripción de su música.

## Las 36 partes

| # | Parte | Función | Eventos |
|---|---|---|---:|
{rows}

Son 36 **partes**, con 14 fichas de biblioteca fijadas por huella más motores anteriores. Cuatro partes pertenecen al mismo junco; seis pertenecen al kit de batería. Los buses no inflan la cuenta. Ninguna parte está vacía, pero no todas suenan a la vez. La función de la sala incluye excitaciones propias.

## Pruebas y límites

Comprobados: duración y eventos, ausencia de eventos en oscuridades, 18 gestos libres y cero eventos métricos/vocales en V; parentescos del material; afinación de la caja escrita (error {V['error_afinacion_caja_semitonos']:.2e} semitonos); 28 planes (error marginal máximo {V['error_marginal_max']:.2e}); órgano 3→5 a la misma presión; ruta cerrada; MusicXML con 36×125 medidas editoriales, voces completas, 2,505 segmentos microtonales; CSV de 5,717 eventos; PDF sin texto fuera de página. Error temporal máximo del XML: 17.08 microsegundos.

**Crítica:** la continuidad del junco y el órgano puede ablandar demasiado el ataque proto punk. La interpretación deberá comparar primero riff seco, luego carbono y finalmente todo, sin convertir el mayor volumen en una prueba de riqueza. El centro puede resultar demasiado escaso: su duración tiene que sostener expectativa y percepción del esfuerzo. La escucha decidirá si conviene alargar respuestas concretas, no rellenarlo automáticamente.

**Preguntas de escucha:** ¿se reconoce Q cuando cambia de cuerpo? ¿la retirada humana permite otra forma de atención? ¿la diferencia de estado del órgano se escucha? ¿la pared deja oír la respuesta que la originó? El silencio acústico, las colas, el balance y la inteligibilidad requieren la futura interpretación. No se deducen del número de capas o de la validación.

## Versiones, protección y reproducción

La entrega vigente es PDF r6, XML r6 y JSON v4. Los PDF r3–r5, XML iniciales y JSON v1–v3 quedan como borradores. No usar los XML anteriores: se corrigió la declaración UTF-8. También se conservan una corrección de desborde de etiqueta y la retirada de una cola de gong que reaparecía tras el corte. El primer CSV falló por el alias de codificación; una primera edición desbordó una página de letra. Esos fallos llevaron a corregir y volver a verificar, no a fabricar capturas retrospectivas.

Los scripts rechazan destinos existentes. Para otra ejecución hay que crear una carpeta e identificador nuevos; los programas de cada etapa no deben relanzarse sobre estos resultados. El identificador de esta ejecución es `{TAG}`; el SHA-256 completo y nonce están en la receta inicial. La receta final agrega huellas de contenido y de las fuentes de cada etapa. No hay publicación ni push.
'''
text('README.md',readme)
proceso='''# Proceso real de escritura

22 de octubre de 2026. Las imágenes se guardaron durante etapas efectivamente ejecutadas. El GIF reúne borradores sucesivos y correcciones; no muestra una interpretación, un video de canción o una simulación de los pasos mentales del compositor.

1. **01:** captura real del visor de Traspuesta, lámina 1, después de comparar 27 y 43.
2. **02:** ruta y deuda calculadas sobre el campo original; reloj compuesto.
3. **03:** primer JSON de 36 partes, 5,716 acontecimientos y primera vista completa.
4. **04:** revisión de memoria del órgano y contratos con los motores. Dos notas anteriores dan pasado al retorno.
5. **05:** página de diseños instrumentales de la primera edición PDF. El nombre antiguo dice «centro», pero la captura muestra la página de instrumentos; se conserva sin renombrar.
6. **06:** página del centro de una edición intermedia, antes de retirar la continuación de gong.
7. **07:** centro vigente sin ese resto métrico: 18 gestos y seis oscuridades.
8. **08:** escritura vigente de 36 partes y 5,717 acontecimientos.

Semilla de terreno: 1. Semilla de composición: 2026102201. El identificador compartido está en los nombres. Los mismos datos deterministas no autorizan sobrescribir una carpeta: cada ejecución lleva nonce e identificador nuevos. Las figuras finales usan el mismo identificador de ejecución, con nombres de revisión cuando procede.

Inspección: PNGs revisados visualmente; PDF completo por contactos y páginas detalladas. GIF revisado en sus cuadros y duración/tamaño comprobados en `datos/proceso-medidas.json`. No se exportó audio. La captura de la página de instrumentos y las versiones del centro son etapas reales, no dibujos fabricados para aparentar un proceso.
'''
text('proceso/README.md',proceso)
text('ESTADO.md','Vigentes: partitura-v4.json, PDF r6, MusicXML r6 y CSV r5. Borradores y exportaciones anteriores conservados; ver README. Parada: sólo partitura e instrumentos, sin máster.\n')
put('fuentes/edicion-definitiva.py',(ROOT/'edicion.py').read_bytes());put('fuentes/cerrar.py',Path(__file__).read_bytes())
initial=json.loads((OUT/'receta-inicial.json').read_text('utf8'))
files={str(p.relative_to(OUT)).replace('\\','/'):sha(p) for p in OUT.rglob('*') if p.is_file()}
recipe={**initial,'version_final':'partitura-4.0','hashes_contenido':files,
 'canonica':'partitura-v4.json','pdf':f'partitura-luciernagas-r6-s1-{TAG}.pdf','musicxml':f'partitura-completa-r6-s1-{TAG}.musicxml',
 'csv':f'eventos-completos-r5-s1-{TAG}.csv','gif':gif,'png':result,
 'origen_id':'imagen elegida + versión/programa inicial + nonce; revisiones de la misma ejecución registradas por huella',
 'verificacion':'validacion-v4.json; sólo escritura y sondas numéricas; no audio',
 'biblioteca_sha256':sha(ROOT/'instrumentos-734cad81b33e/manifiesto.json'),
 'revision_visual':'36 páginas por contactos; tema, centro, etiqueta y carbono a resolución legible; PNGs de proceso y cuadros de GIF inspeccionados'}
js('receta-final.json',recipe)
# Paquete utilizable con archivos vigentes. Borradores quedan en el repositorio.
zipname=f'luciernagas-partitura-entrega-s1-{TAG}.zip';zipdest=OUT/zipname
selected=[OUT/'README.md',OUT/'partitura-v4.json',OUT/f'partitura-luciernagas-r6-s1-{TAG}.pdf',OUT/f'partitura-completa-r6-s1-{TAG}.musicxml',OUT/f'eventos-completos-r5-s1-{TAG}.csv',OUT/'validacion-v4.json',OUT/'receta-final.json',OUT/'receta-inicial.json',OUT/gif,OUT/result,OUT/'og.png']
selected+=list((OUT/'proceso').glob('*'))+list((OUT/'datos').glob('*'))+list((OUT/'fuentes').glob('*'))
with zipfile.ZipFile(zipdest,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as zz:
 for p in selected:
  if p.is_file():zz.write(p,OUT.name+'/'+str(p.relative_to(OUT)))
 for p in (ROOT/'instrumentos-734cad81b33e').rglob('*'):
  if p.is_file():zz.write(p,str(p.relative_to(ROOT)))
js('paquete.json',{'archivo':zipname,'sha256':sha(zipdest),'bytes':zipdest.stat().st_size,'contenido':'archivos vigentes, datos, fuentes, proceso y biblioteca fijada; sin audio'})
print(json.dumps({'gif':gif,'gif_bytes':(OUT/gif).stat().st_size,'gif_s':sum(durations)/1000,'zip':zipname,'zip_bytes':zipdest.stat().st_size,'pngs':len(files)},ensure_ascii=False))
