"""Segunda escritura: corrige contratos con los motores. Conserva v1."""
from pathlib import Path
import json,math,hashlib,copy,io
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent;OUT=ROOT/(ROOT/'ULTIMA.txt').read_text().strip();TAG=OUT.name.split('-')[-1]
P=json.loads((OUT/'partitura-v1.json').read_text('utf8'));Q=P['negra_s'];C0,C1=P['centro'];END=P['corte_banda']
def put(f,b):
 with (OUT/f).open('xb') as h:h.write(b)
def js(f,v):put(f,json.dumps(v,ensure_ascii=False,indent=1).encode('utf8'))
E=P['eventos'];P['version']='partitura-2.0';changes=[]
for e in E['tom']:e['pieza']='tomlo'
changes.append('Tom: usar la pieza tomlo que existe en la biblioteca, en lugar de tom.')
P['controles'].pop('androide',None)
for name in ['terminal','androide']:
 for e in E[name]:
  e.pop('vector_x',None);e.pop('vector_y',None)
changes.append('Eliminar desgarro, que el bajo original no consume; terminal usa curvas globales vector_x/vector_y ya soportadas.')
# Dar pasado audible a la histéresis: misma presión .47 antes y después del máximo.
P['controles']['organo']['controles']['presion']=[[0,.15],[45,.47],[60,.47],[70,.93],[C0-.06,.93],[C0,.47],[C1,.47],[C1+16*4*Q,.26],[C1+32*4*Q,.74],[END,.47],[P['duracion'],.47]]
ref=E['organo'][0]
for i,(a,b,v) in enumerate([(49,59,.22),(70,C0-.05,.29)]):
 e=copy.deepcopy(ref);e.update(id=f'organ-pasado-{i}',t=a,dur=b-a,vel=v,seccion='II' if a<53.333 else 'III',frase='presión .47 / aprender el umbral',ancestro=P['fuentes_tema'][0]);E['organo'].append(e)
E['organo'].sort(key=lambda x:x['t'])
changes.append('Órgano: dos apariciones antes del centro; .47 de presión primero activa 3 divisores y después del máximo conserva 5.')

# Afinación del arpa: el motor original ignora midi en sus eventos de arpa.
# Se fija una variante mínima que conserva fases, gira envolventes y retuna la
# cuerda excitada. No se modifica el original compartido.
source=(OUT/'fuentes/instrumentos-de-tres-tiempos__motores.py').read_text('utf8')
needle="if kind=='cuerda': target_freqs=freqs*(float(hz(e['midi']))/freqs[0,0])"
assert source.count(needle)==1
variant=source.replace(needle,needle+"\n                else: target_freqs[v]=float(hz(e['midi']))*np.arange(1,H+1)")
needle2="if kind=='cuerda': freqs+=(target_freqs-freqs)*(1-np.exp(-dt/.025))"
assert variant.count(needle2)==1
variant=variant.replace(needle2,"freqs+=(target_freqs-freqs)*(1-np.exp(-dt/.025))")
compile(variant,'motores-arpa-afinable.py','exec');put('fuentes/motores-arpa-afinable.py',variant.encode('utf8'))
P['controles']['arpa']['cuerdas_midi']=[64,59,60,65,67]
P['controles']['arpa']['variante']='fuentes/motores-arpa-afinable.py; mismo motor de red_modal con retune por evento y fase continua'
changes.append('Arpa: variante congelada para que midi por evento sí cambie la cuerda y conserve fases; el motor original sólo usa cuerda.')
for k in ['arpa','boca','fotones']:
 for e in E[k]:
  if k=='arpa':e['cuerda']=int(np.argmin(abs(np.array([64,59,60,65,67])-e['midi'])))
# Registro de adaptadores/instrucciones completo, sin simular que ya existe una mezcla.
P['interpretacion']={
 'version':'contrato-2.0','datos_canonicos':'partitura-v2.json; tiempos absolutos en segundos y alturas Hz',
 'biblioteca':'../instrumentos-734cad81b33e/manifiesto.json',
 'nuevos':{'guitarra':'instrumentos.py / Guitarra: gesto.cuerda/caja/nodo/parcial y fundamental_midi; avanzar(deuda,pesos,humedad,presion); captura lineal con fase continua',
 'junco':'instrumentos.py / transporte y junco_gestos: realizar cada arista no nula del plan con fase independiente persistente; sumar por destino; interpolar log Hz; no reiniciar en cada columna'},
 'existentes':{'tres-tiempos':'fuentes/motores-arpa-afinable.py; salvo arpa, copia idéntica de los motores ya existentes',
 'campana':'fuentes/campana-motor.mjs; eventos globales hit/params + nota midi; conservar u y v',
 'objetos':'objetos.js; eventos con t,dur,m,v; aplicar salida prescrita porque las colas del motor exceden la duración de nota',
 'bateria':'web.js; pieza y vel; altura de tabla para escritura sin afirmar pitch fijo',
 'voces':'guía silábica con MIDI continuo; preparar Difonos/Sabina en fase de interpretación; no se hizo en esta etapa',
 'vocoders':'guía de cada parte coral articulada sobre su portadora (cuerda o junco); no samplear la canción anterior'},
 'campos_de_partitura_que_exigen_adaptador':['gestos extendidos de objetos','salidas/captaciones de guitarra','realización de junco','mutes globales','vocoder'],
 'cola':'La duración de cada evento es salida máxima incluyendo release; truncar con rampa final .012 s. Cerrar todos los buses en cada oscuridad y agujero.',
 'voces_humanas':'voz, duo y coros no tienen eventos en el centro. Boca de tres tiempos también queda en silencio en V.',
 'limite':'Los dos diseños nuevos tienen cálculo de estados/planes; no se certifica su realizabilidad acústica o timbre sin implementar y escuchar la interpretación.'}
for fname in ['motor.mjs','campana.py']:
 put('fuentes/campana-'+fname,(ROOT.parent/'campana-padica'/fname).read_bytes())
P['correcciones']=changes
js('partitura-v2.json',P);js('datos/correcciones-v2.json',changes)
put('fuentes/revisar.py',Path(__file__).read_bytes());put('fuentes/instrumentos-finales.py',(ROOT/'instrumentos.py').read_bytes())
with (OUT/'PARTITURA.txt').open('x',encoding='utf8') as f:f.write('partitura-v2.json\n')

# Vista real de la revisión: no es un borrador simulado retrospectivamente.
im=Image.new('RGB',(1600,1000),'#111813');d=ImageDraw.Draw(im)
F=lambda s:ImageFont.truetype('C:/Windows/Fonts/arial.ttf',s)
d.text((55,35),'04 / Una misma presión, dos pasados',font=F(43),fill='#eaf0ca')
d.text((55,105),'Revisión del órgano y de los contratos; sin render de audio.',font=F(24),fill='#afc897')
xy=P['controles']['organo']['controles']['presion'];xx=np.array(xy)
pts=[(70+1450*t/P['duracion'],570-370*v) for t,v in xy];d.line(pts,fill='#94d7be',width=5)
for tt,label,mask in [(55,'Antes: .47 / 3 divisores',[1,1,1,0,0,0]),(C1+.1,'Después: .47 / 5 divisores',[1,1,1,1,1,0])]:
 x=70+1450*tt/P['duracion'];y=570-370*.47;d.ellipse((x-7,y-7,x+7,y+7),fill='#edb982');d.text((x-25,610),label,font=F(24),fill='#eaf0ca')
 for j,on in enumerate(mask):d.rectangle((x-25+j*34,660,x+j*34,705),fill='#edb982' if on else '#2e3d32')
for i,ch in enumerate(changes):
 text=ch if len(ch)<110 else ch[:107]+'...';d.text((55,775+i*39),text,font=F(19),fill='#c4d2af')
b=io.BytesIO();im.save(b,format='PNG');put(f'proceso/04-revision-de-memoria-s1-{TAG}.png',b.getvalue())
print(json.dumps({'version':P['version'],'eventos':sum(len(v) for v in E.values()),'cambios':len(changes)},ensure_ascii=False))
