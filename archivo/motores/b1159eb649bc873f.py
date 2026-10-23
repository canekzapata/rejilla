"""Edición PDF, MusicXML y CSV. Ninguna función sintetiza audio."""
from pathlib import Path
import json,math,io,csv,xml.etree.ElementTree as ET
from collections import defaultdict
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3,A2,landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import fitz

ROOT=Path(__file__).resolve().parent;OUT=ROOT/(ROOT/'ULTIMA.txt').read_text().strip();TAG=OUT.name.split('-')[-1]
P=json.loads((OUT/'partitura-v4.json').read_text('utf8'));R=json.loads((OUT/'datos/recorrido.json').read_text('utf8'))
Q=P['negra_s'];DUR=P['duracion'];C0,C1=P['centro'];STOP=P['corte_banda'];DIV=12000
def put(f,b):
 with (OUT/f).open('xb') as h:h.write(b)
def js(f,v):put(f,json.dumps(v,ensure_ascii=False,indent=1).encode('utf8'))
def pitch(m):
 n=round(m);names=['C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B'];c=(m-n)*100
 return f'{names[n%12]}{n//12-1}'+(f' {c:+.1f}c' if abs(c)>.05 else '')
def clock(t):return f'{int(t)//60}:{t%60:06.3f}'

# Exportar todas las voces, silencios y continuaciones. La cuantización de
# MusicXML no altera el contrato canónico en segundos/Hz.
root=ET.Element('score-partwise',version='4.0');work=ET.SubElement(root,'work');ET.SubElement(work,'work-title').text=P['titulo']
ident=ET.SubElement(root,'identification');ET.SubElement(ident,'creator',type='composer').text='Canek Zapata'
ET.SubElement(ident,'rights').text='© 2026 Canek Zapata'
pl=ET.SubElement(root,'part-list');xmlstats={};maxerr=0
for tr in P['partes']:
 idp='P'+str(tr['numero']);sp=ET.SubElement(pl,'score-part',id=idp);ET.SubElement(sp,'part-name').text=tr['nombre'];ET.SubElement(sp,'part-abbreviation').text=tr['id']
 part=ET.SubElement(root,'part',id=idp);events=P['eventos'][tr['id']];ends=[];assigned=[]
 for e in events:
  lane=next((i for i,end in enumerate(ends) if end<=e['t']+1e-9),len(ends))
  if lane==len(ends):ends.append(e['t']+e['dur'])
  else:ends[lane]=e['t']+e['dur']
  assigned.append((e,lane))
 for me in P['medidas_editoriales']:
  a,b=me['t'],me['fin'];total=round((b-a)/Q*DIV);mm=ET.SubElement(part,'measure',number=str(me['n']))
  at=ET.SubElement(mm,'attributes')
  if me['n']==1:ET.SubElement(at,'divisions').text=str(DIV)
  ti=ET.SubElement(at,'time')
  if me['free']:ET.SubElement(ti,'senza-misura')
  else:ET.SubElement(ti,'beats').text='4';ET.SubElement(ti,'beat-type').text='4'
  if me['n']==1:
   clef=ET.SubElement(at,'clef');ET.SubElement(clef,'sign').text='percussion' if tr['numero'] in range(20,26) else 'G';ET.SubElement(clef,'line').text='2'
  if me['n']==1 or me['free'] or any(abs(a-s['t'])<1e-6 for s in P['secciones']):
   dr=ET.SubElement(mm,'direction',placement='above');dt=ET.SubElement(dr,'direction-type');sec=next((s for s in P['secciones'] if s['t']<=a<s['fin']),P['secciones'][-1]);ET.SubElement(dt,'words').text=f'{sec["id"]} / {clock(a)}'+(' / celda editorial en segundos; sin pulso' if me['free'] else '')
   if me['n']==1:ET.SubElement(dr,'sound',tempo='144')
  hits=[(e,l) for e,l in assigned if e['t']<b-1e-9 and e['t']+e['dur']>a+1e-9]
  voices=sorted({l for e,l in hits}) or [0]
  for vi,lane in enumerate(voices):
   if vi:ET.SubElement(ET.SubElement(mm,'backup'),'duration').text=str(total)
   cur=0
   def rest(n):
    if n<=0:return
    ne=ET.SubElement(mm,'note');ET.SubElement(ne,'rest');ET.SubElement(ne,'duration').text=str(n);ET.SubElement(ne,'voice').text=str(lane+1)
   for e,_ in [x for x in hits if x[1]==lane]:
    aa=max(0,round((e['t']-a)/Q*DIV));bb=min(total,round((e['t']+e['dur']-a)/Q*DIV));aa=max(aa,cur)
    if bb<=aa:continue
    rest(aa-cur);ne=ET.SubElement(mm,'note',id=e['id']+f'_m{me["n"]}')
    if e.get('altura_asignable',True):
     pp=ET.SubElement(ne,'pitch');n=round(e['midi']);steps=[('C',0),('C',1),('D',0),('E',-1),('E',0),('F',0),('F',1),('G',0),('A',-1),('A',0),('B',-1),('B',0)];st,alter=steps[n%12];ET.SubElement(pp,'step').text=st
     alt=alter+e['midi']-n
     if abs(alt)>1e-10:ET.SubElement(pp,'alter').text=f'{alt:.9f}'
     ET.SubElement(pp,'octave').text=str(n//12-1)
    else:
     pp=ET.SubElement(ne,'unpitched');ET.SubElement(pp,'display-step').text='C';ET.SubElement(pp,'display-octave').text='5'
    ET.SubElement(ne,'duration').text=str(bb-aa)
    if e['t']<a-1e-8:ET.SubElement(ne,'tie',type='stop')
    if e['t']+e['dur']>b+1e-8:ET.SubElement(ne,'tie',type='start')
    ET.SubElement(ne,'voice').text=str(lane+1)
    if e.get('texto') and a<=e['t']+1e-8:
     ly=ET.SubElement(ne,'lyric');ET.SubElement(ly,'syllabic').text='single';ET.SubElement(ly,'text').text=e['texto']
    nots=ET.SubElement(ne,'notations');tech=ET.SubElement(nots,'technical')
    words=e['articulacion']+(f' / → {pitch(e["midi_fin"])}' if 'midi_fin' in e else '')
    ET.SubElement(tech,'other-technical').text=words
    cur=bb
    maxerr=max(maxerr,abs((aa*Q/DIV+a)-max(a,e['t'])))
   rest(total-cur)
 xmlstats[tr['id']]={'voces_max':len(ends),'eventos':len(events),'medidas':len(P['medidas_editoriales'])}
put(f'partitura-completa-r5-s1-{TAG}.musicxml',ET.tostring(root,encoding='utf8',xml_declaration=True))
buf=io.StringIO(newline='');wr=csv.writer(buf);wr.writerow(['capa','id','segundos','duracion_s','MIDI_continuo','Hz','velocidad','pan','gesto','silaba','ancestro','parametros_JSON'])
for tr in P['partes']:
 for e in P['eventos'][tr['id']]:wr.writerow([tr['id'],e['id'],e['t'],e['dur'],e['midi'],e['hz'],e['vel'],e['pan'],e['articulacion'],e.get('texto',''),e.get('ancestro',''),json.dumps(e,ensure_ascii=False)])
put(f'eventos-completos-r5-s1-{TAG}.csv',buf.getvalue().encode('utf-8-sig'))

# Cuaderno de dirección y partitura proporcional completa, con tamaños de
# página diferentes para conservar legibles las 36 partes.
pdfmetrics.registerFont(TTFont('Ar','C:/Windows/Fonts/arial.ttf'));pdfmetrics.registerFont(TTFont('ArB','C:/Windows/Fonts/arialbd.ttf'))
PDF=OUT/f'partitura-luciernagas-r5-s1-{TAG}.pdf'
if PDF.exists():raise FileExistsError(PDF)
W,H=landscape(A3);c=canvas.Canvas(str(PDF),pagesize=(W,H));c.setTitle(P['titulo']+' / partitura completa');c.setAuthor('Canek Zapata');page=0;pages=[]
INK='#152d28';ACC='#8a3c24';PAPER='#f4f1df';MUTED='#577166'
def txt(x,y,s,size=11,bold=False,col=INK):c.setFont('ArB' if bold else 'Ar',size);c.setFillColor(col);c.drawString(x,y,str(s))
def line(x,y,xx,yy,col=INK,lw=.5):c.setStrokeColor(col);c.setLineWidth(lw);c.line(x,y,xx,yy)
def para(s,y,size=12,width=None,x=48,leading=None):
 leading=leading or size*1.47;width=width or W-96;acc=''
 for word in s.split():
  trial=(acc+' '+word).strip()
  if pdfmetrics.stringWidth(trial,'Ar',size)>width:txt(x,y,acc,size);y-=leading;acc=word
  else:acc=trial
 if acc:txt(x,y,acc,size);y-=leading
 if y<48:raise ValueError(('texto fuera de página',page,y,s[:50]))
 return y
def new(title,sub='',big=False):
 global W,H,page
 if page:c.showPage()
 W,H=A2 if big else landscape(A3);c.setPageSize((W,H));page+=1;pages.append(title)
 c.setFillColor(PAPER);c.rect(0,0,W,H,fill=1,stroke=0)
 txt(48,H-48,title,25,True);txt(48,H-72,sub,10,col=ACC)
 line(48,35,W-48,35);txt(48,20,'CANEK ZAPATA / REJILLA / 22 OCT 2026 / PARTITURA 4.0 / SIN AUDIO',8)
 txt(W-80,20,page,9)
def pic(p,x,y,w,h=None):
 im=Image.open(p);hh=h or w*im.height/im.width;c.drawImage(ImageReader(im),x,y,width=w,height=hh,preserveAspectRatio=True,mask='auto')

new('Llevemos unas luciérnagas al lago','Proto punk folk / misterio material / polifonía computacional / 36 partes')
y=para('Dos personas llegan al agua. Una lata tiene una raíz en la boca. El rasgueo se detiene y los cuerpos pequeños toman la respuesta. Cuando la canción vuelve, su afinación y su manera de responder ya cambiaron.',H-115,17,leading=25)
y=para('4:18.667. Negra = 144 en las zonas métricas. Centro de 60 segundos sin pulso. 36 partes, 5717 eventos; cuatro voces de junco y seis componentes de batería se cuentan como partes, no como instrumentos nuevos.',y-12,13)
for s in P['secciones']:
 txt(48,y-9,f'{clock(s["t"])} - {clock(s["fin"])}',11,True);txt(252,y-9,f'{s["id"]} / {s["nombre"]}',12);y-=27
y=para('Dos instrumentos nuevos: guitarra de alambre y tres cajas; junco de acuerdos. Biblioteca fijada por huella y motores anteriores conservados. El cuaderno incluye la escritura completa; el MusicXML y JSON conservan afinaciones y tiempos precisos.',y-12,12)
para('Etapa acordada: revisar la partitura. Los másters y la interpretación completa se harán después. No se generó audio ni un visor musical nuevo.',y-10,12)

new('1 / Pregunta, respuesta y residuo','Escritura proporcional cromática: eje horizontal = negras; altura = MIDI continuo. No son figuras de duración convencional.')
for idx,(pattern,label) in enumerate([(P['tema_Q'],'Q / salto de quinta, semitono, pregunta detenida'),(P['tema_R'],'R / responde después de un hueco')]):
 yy=H-155-idx*205;txt(48,yy+35,label,15,True);x0=110;x1=W-80
 for beat in range(9):
  x=x0+(x1-x0)*beat/8;line(x,yy-75,x,yy+15,'#c8cebb');txt(x,yy-92,beat,9)
 for beat,m,dd in pattern:
  x=x0+(x1-x0)*beat/8;xm=x0+(x1-x0)*(beat+dd)/8;y=yy-(m-64)*4
  c.setFillColor(ACC);c.circle(x,y,3,fill=1,stroke=0);line(x,y,xm,y,ACC,2);txt(x+4,y+9,pitch(m),10)
y=para('Identidad: E4-B3-C4, un F4 tardío y regreso a E4. Respuesta: G4-F4-D4-C4-B3-E4. Se enseñan antes del centro. El regreso conserva ataques reconocibles y adopta afinación fraccional; la llegada vocal se transforma hacia la serie y conserva un desplazamiento de caja, en vez del E temperado inicial.',H-580,13)
para('Comparación de trabajo: una versión convencional repetiría riff y coro intactos después de bajar el volumen. Aquí se retiran las señales métricas, una captación releva a otra, la presión guarda historia y el acorde llega por trayectorias especificadas. Ese mecanismo todavía tiene que demostrar su interés al escuchar.',y-10,12)

new('2 / Llegar al lago y volver','Traspuesta 1: El Teso del Tecolote / lago Pinahuizapan. Ruta compuesta sobre alturas originales.')
pic(OUT/'proceso'/f'02-recorrido-y-deuda-s1-{TAG}.png',(W-870)/2,210,870)
para(f'Ruta de {R["distancia_m"]/1000:.3f} km; ascenso y descenso acumulados {R["ascenso_m"]:.3f} m. Sale y regresa a {R["salida_m"]:.3f} m. u hacia el este, v hacia el sur. Es tiempo de composición, no una caminata simulada de cuatro minutos.',170,12)
para('La pendiente altera velocidad de los relojes y presión de guitarra. La suma de giros absolutos deja 96.336 cents de deuda al regresar. Agua estancada, olor, lata y raíz pertenecen a la ficción; Traspuesta aporta alturas e hidrología, no medidas de humedad o contaminación.',110,11)

new('3 / Dos instrumentos que cambian quién responde','Diseños nuevos, con estados y planes numéricos. Sin muestras sonoras ni calibración acústica todavía.')
y=H-120
for title,body in [
 ('Guitarra de alambre y tres cajas','Seis cuerdas, tres cajas y ocho modos por cuerda. Púa, roce, armónico, madera y apagado son excitaciones distintas. La vibración y la fase continúan al cambiar de caja. Nodo y parcial especifican el armónico; MIDI fundamental y altura resultante se guardan por separado.'),
 ('Tres acuerdos incompatibles','Se buscan diferencias b-a=0, c-b=0, a-c=deuda. La suma exige una diferencia no nula; ajustar afinaciones no elimina ese residuo. Mínimos cuadrados ponderados reparte la diferencia entre las cajas. Con deuda=0 desaparece el conflicto. Es un controlador propio, no una imposibilidad de que tres cuerpos físicos vibren juntos.'),
 ('Junco de acuerdos / cuatro voces','Cuatro destinos reciben masa de los parciales 1, 2, 3 y 5 del primer E4 de la guitarra. Cada plan conserva marginales y minimiza el costo declarado. Una arista del plan se realiza como trayectoria de altura con fase continua. Son cuatro voces del mismo instrumento y hasta dieciséis trayectorias, sin respiración humana obligatoria.'),
 ('Contrato de fase y energía','La fase se obtiene integrando 2*pi*f(t). Cambiar una imagen de magnitud no basta. Las masas del transporte y la norma de envolventes son magnitudes del modelo; no se anuncian como energía acústica conservada de la mezcla. El roce y la saturación requieren interpretación posterior.')]:
 txt(48,y,title,16,True);y=para(body,y-27,13,leading=20)-30

new('4 / Pantano: 60 segundos de escucha','V / 1:33.333-2:33.333 / senza misura. Ni voz principal ni batería. No hay click, ostinato, delay periódico o redoble de salida.')
y=H-115
events=sorted([(tr['nombre'],e) for tr in P['partes'] for e in P['eventos'][tr['id']] if C0<=e['t']<C1],key=lambda x:x[1]['t'])
for name,e in events:
 txt(48,y,clock(e['t']),11,True);txt(152,y,name[:31],11);txt(410,y,e['articulacion'],11);txt(700,y,pitch(e['midi']) if e.get('altura_asignable',True) else 'sin altura fija',10);txt(905,y,f'{e["dur"]:.3f} s / v={e["vel"]:.2f}',10);y-=26
y-=6
for a,b in P['oscuridades']:txt(48,y,f'OSCURIDAD {clock(a)}-{clock(b)} / {b-a:.2f} s',10,True,col=ACC);y-=21
para('Cada oscuridad cierra la salida y las colas. Los estados internos pueden conservar memoria; al reabrir no se inventa un nuevo ataque. La validez del silencio acústico se comprobará al interpretar: aquí se verifica la ausencia de acontecimientos escritos.',y-10,11)

new('5 / Carbono: cuatro relojes, cinco cuerdas, una memoria','VI / 2:33.333-3:00.000. Referencias de gusto: el centro de El río y V Abajo del Androide.')
y=H-115
for title,body in [
 ('Arpa / micelio','El motivo pasa por cinco cuerdas. Enlaces cada dos compases giran envolventes de una cuerda a otra, con signos y fase continua. La variante afinable hace que la altura del evento realmente cambie la cuerda. No se reinicia la red al entrar una nota.'),
 ('Cuerda y órgano','La cuerda tiene presión y arco separados. El órgano se oyó primero a .47, pasó por .93 y vuelve a .47: con histéresis retiene cinco divisores donde antes había tres. La salida puede callar sin borrar el estado.'),
 ('Relojes 17 / 19 / 23 / 29','Arpa, mbira, boca y fotones integran fases desde el comienzo sobre tiempo absoluto; la pendiente modula su velocidad. Durante el centro continúan sólo como cálculo. Al volver no arrancan todos en cero ni cada cuatro compases.'),
 ('Dos solos y un relevo','Terminal en los primeros ocho compases de VI; bajo de androide en los ocho siguientes. Comparten parciales y preguntas de Q. Las ráfagas responden a cierres de frase; el acompañamiento deja huecos. El coro humano está ausente en estos solos.')]:
 txt(48,y,title,16,True);y=para(body,y-27,13,leading=20)-28
para('La referencia es relacional: material común, tiempos propios, instrumentos que se prestan algo y un regreso distinto. Tener treinta y seis partes no demuestra haber conseguido la riqueza de las piezas que eligió Canek.',y,12)

new('6 / Solo A, B, C y D','Se elige D. Las cuatro alternativas son posibilidades de escritura, no cuatro audios producidos.')
y=H-120
for title,body in [
 ('A / amplificar el riff','Solo de guitarra sobre el campo inicial, con el mismo orden de ataques. Clara identidad punk; poca transformación del reparto entre cuerpos.'),
 ('B / canon de cuerda','El arpa toma Q y chelo/clarinete responden por inversión y aumentación. Mantiene el hilo folk; el conflicto de afinación podría quedar de fondo.'),
 ('C / dispersión de luciérnagas','Repartir fragmentos de Q por las cuatro voces de junco con tiempos libres. Buena continuidad con V; riesgo de prolongar la misma textura demasiado tiempo.'),
 ('D / una frase termina en otro cuerpo','Primero la terminal toca los parciales de Q; después el bajo de androide recoge su registro grave. Los planes llevan el primer E de la guitarra hacia cuatro destinos. La cuerda cede, el órgano conserva divisores y el coro vuelve desde esa distribución. Se escribieron los eventos y los controles de este recorrido.')]:
 txt(48,y,title,17,True);y=para(body,y-29,14,leading=22)-35
para('Objeción: el mecanismo puede ser tan continuo que borre los ataques ásperos del proto punk. En la interpretación habrá que comparar la sección sin juncos, luego con ellos, conservando ganancias; adelgazar si el riff pierde función.',y-8,13)

new('7 / Percusiones: aprender el hueco','Cuatro compases iniciales. Puntos = ataques; el eje es una negra. Los remates cambian en las demás secciones.')
x0=240;x1=W-60;yy=H-140
for k in ['bombo','caja','hat','tom','aro','ride','fotones']:
 txt(48,yy,k,13,True)
 for beat in range(17):
  x=x0+(x1-x0)*beat/16;line(x,yy-12,x,yy+14,'#b8c3ae');
  if beat%4==0:txt(x,yy+24,int(beat/4)+1,10)
 for e in P['eventos'][k]:
  if e['t']>=16*Q:continue
  x=x0+(x1-x0)*e['t']/(16*Q);c.setFillColor(ACC);c.circle(x,yy,2+2*e['vel'],fill=1,stroke=0)
 yy-=67
y=para('Las partes aparecen gradualmente: la ausencia de hat, aro y plato al inicio también está escrita. El tom usa la pieza tomlo del motor existente. El grave cambia entre dos células; caja y aro no doblan todos los ataques. Los remates de fotones responden a las frases de los solos.',yy-15,13)
para('En el regreso faltan primeros ataques escogidos de bajo y bombo. Los tres agujeros de VIII cierran además rasgueo, voces, campos y efectos. Al final se corta la banda; no hay fade-out de toda la canción.',y-12,13)

for start in range(0,len(P['letra']),8):
 new(f'8 / Voz y prosodia / {start+1}-{min(start+8,len(P["letra"]))}','Sílabas y alturas completas en MusicXML/JSON. El texto libre no añade una radio explicativa.')
 y=H-116
 for lyric in P['letra'][start:start+8]:
  txt(48,y,f'{clock(lyric["t"])} / {lyric["capa"]} / {lyric["procedencia"]}',10,True,col=ACC)
  y=para(lyric['texto'],y-22,17,leading=24)
  y=para(lyric['silabas'],y,10,leading=15)-14

for start in [0,18]:
 new(f'9 / Partes {start+1}-{start+18}','36 capas con acontecimientos. Buses aparte. Cada instrumento conserva una fuente y una función.')
 y=H-119
 for tr in P['partes'][start:start+18]:
  txt(48,y,f'{tr["numero"]:02} {tr["nombre"]}',12,True);txt(420,y,tr['funcion'],11)
  txt(48,y-15,tr['motor'],8,col=ACC);txt(950,y,str(len(P['eventos'][tr['id']]))+' ev.',10);y-=34

new('10 / Antes de interpretar','Comprobación de escritura y preguntas para revisar con Canek. No son un certificado estético.')
y=H-117
for text in [
 'Pasado: Q y R se enseñan; el órgano cruza un umbral; una pausa deja de ser acompañamiento; los parciales de la guitarra tienen filiación explícita. Consecuencia: afinación fraccional, divisores retenidos, final vocal cambiado y pared con memoria.',
 'Silencios: la partitura prescribe cierre de todas las salidas y cola limitada. Habrá que comprobarlos sobre la futura señal, incluidos retardos, reverberación y señales regulares. No se ha generado audio para esa prueba.',
 'El territorio vuelve a su punto inicial. La deuda acumulada por giros absolutos no se cancela al volver. Es nuestra elección de memoria; no una ley geológica o acústica.',
 'MusicXML redondea a 12000 divisiones/negra y preserva alteraciones fraccionarias. En V y IX las medidas son celdas editoriales en segundos, sin pulso. JSON y CSV son el contrato completo de controles, glissandi, salida y filiación.',
 'Las páginas siguientes muestran todos los acontecimientos: tiempo horizontal y altura cromática por cada parte. Línea = duración máxima de salida; pendiente de línea = glissando. Referencia MIDI junto al nombre. No son pentagramas diatónicos convencionales.',
 'Tres pruebas futuras: reconocer Q al salir del centro; oír el mismo .47 del órgano con estados distintos; distinguir transporte del acorde y un fundido común. La mezcla deberá sostener la aspereza del rasgueo y dejar sitio a la voz.',
 'Parada de este encargo: partitura y diseños instrumentales. Después de tu revisión se hará la interpretación y los másters. No se produjo un visor musical nuevo ni un video de la canción.'
 ]:y=para(text,y,13,leading=20)-21

# Partitura proporcional completa. A2 vertical mantiene 36 líneas legibles.
windows=[]
for sec in P['secciones']:
 span=10 if sec['modo'].startswith('senza') else 8*4*Q
 a=sec['t']
 while a<sec['fin']-1e-7:
  b=min(sec['fin'],a+span);windows.append((a,b,sec));a=b
for a,b,sec in windows:
 new(f'{sec["id"]} / {clock(a)} - {clock(b)}',sec['accion']+' / Partitura proporcional completa',True)
 x0,x1=255,W-48;top=H-125;row=40
 # Oscuridades y huecos son tiempos de salida nula en todas las partes.
 for aa,bb in P['oscuridades']+P['agujeros_pared']:
  aa=max(aa,a);bb=min(bb,b)
  if bb>aa:c.setFillColor('#dbe2ce');c.rect(x0+(x1-x0)*(aa-a)/(b-a),top-36*row,x1-x0 if False else (x1-x0)*(bb-aa)/(b-a),36*row+20,fill=1,stroke=0)
 step=1 if sec['modo'].startswith('senza') else Q
 for tt in np.arange(math.ceil(a/step)*step,b+1e-8,step):
  x=x0+(x1-x0)*(tt-a)/(b-a);line(x,top+18,x,top-36*row,'#bdc6b4',.3)
  if sec['modo'].startswith('senza') or abs(tt/(4*Q)-round(tt/(4*Q)))<1e-5:txt(x+2,top+29,f'{tt:.2f}',7)
 for j,tr in enumerate(P['partes']):
  y=top-j*row;events=P['eventos'][tr['id']];hits=[e for e in events if e['t']<b and e['t']+e['dur']>a]
  allm=[e['midi'] for e in events];ref=12*round(np.median(allm)/12) if allm else 60
  txt(48,y+5,f'{tr["numero"]:02} {tr["nombre"][:30]}',8,True);txt(48,y-8,f'ref MIDI {ref:.0f} / '+tr['id'],6.5,col=MUTED)
  line(x0,y-15,x1,y-15,'#d1d7c4',.3);line(x0,y,x1,y,'#c5cfbb',.3);line(x0,y+15,x1,y+15,'#d1d7c4',.3)
  for e in hits:
   aa=max(a,e['t']);bb=min(b,e['t']+e['dur']);xa=x0+(x1-x0)*(aa-a)/(b-a);xb=x0+(x1-x0)*(bb-a)/(b-a)
   def py(t):
    u=(t-e['t'])/e['dur'];m=e['midi']+(e.get('midi_fin',e['midi'])-e['midi'])*u
    return y-float(np.clip((m-ref)*.65,-17,17))
   ya,yb=py(aa),py(bb);line(xa,ya,xb,yb,ACC if e.get('libre') else INK,1.2)
   if e['t']>=a:
    c.setFillColor(ACC);c.circle(xa,ya,1.7,fill=1,stroke=0)
    if e.get('texto'):txt(xa+2,ya+4,e['texto'],5.6,col=ACC)
    elif sec['modo'].startswith('senza'):txt(xa+3,ya+5,e['articulacion'][:32],6.5,col=ACC)
  # Nombre y eje de cada parte hacen explícita su referencia cromática.
 txt(48,61,'Escala vertical: 0.65 pt/semitono alrededor de ref; extremos recortados a ±17 pt sólo en el dibujo. Alturas exactas en MusicXML/CSV.',8)
 txt(48,48,'Cada punto y duración procede de partitura-v4.json. Velocidad, fase, gesto y controles completos acompañan la escritura.',8)
c.save()

# Renders de revisión, no reconstrucciones de proceso.
qa=ROOT/'tmp'/('pdf-r5-'+TAG);qa.mkdir(parents=True,exist_ok=False)
doc=fitz.open(PDF)
for i,p in enumerate(doc):
 pix=p.get_pixmap(matrix=fitz.Matrix(.9,.9),alpha=False);(qa/f'pagina-{i+1:02}.png').write_bytes(pix.tobytes('png'))
pre=doc[4].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False)
put(f'proceso/07-centro-sin-restos-s1-{TAG}.png',pre.tobytes('png'))
overview=doc[-3].get_pixmap(matrix=fitz.Matrix(.9,.9),alpha=False)
put(f'partitura-completa-resultado-r5-s1-{TAG}.png',overview.tobytes('png'))
js('datos/edicion-r5.json',{'pdf_archivo':PDF.name,'paginas':len(doc),'titulos':pages,'xml':xmlstats,'error_max_s_xml':maxerr,'raster_revision':str(qa),'musicxml_celdas':len(P['medidas_editoriales']),'formato_pdf':'dirección + partitura proporcional de todos los eventos','limite_grafico':'eje vertical recorta extremos por legibilidad; CSV/XML conserva alturas'})
put('fuentes/edicion-r5.py',Path(__file__).read_bytes())
print(json.dumps({'pdf':str(PDF),'paginas':len(doc),'raster':str(qa),'xml_error_s':maxerr},ensure_ascii=False))
