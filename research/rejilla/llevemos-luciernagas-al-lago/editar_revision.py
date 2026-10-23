"""Edición nueva de v7: partitura completa, guía de lectura, XML y CSV."""
from pathlib import Path
import json,math,io,csv,xml.etree.ElementTree as ET
from collections import defaultdict
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A3,A2,landscape
from reportlab.lib.utils import ImageReader
import fitz

ROOT=Path(__file__).resolve().parent;OUT=ROOT/(ROOT/'REVISION-EN-CURSO.txt').read_text().strip();TAG=OUT.name.split('-')[-1]
P=json.loads((OUT/'partitura-v8.json').read_text('utf8'));PACK=json.loads((OUT/'datos/paquete-modal-v6.json').read_text('utf8'))
PL=json.loads((OUT/'datos/transportes-memoria-v8.json').read_text('utf8'));Q=P['negra_s'];D=P['duracion'];C0,C1=P['centro'];DIV=12000
def put(name,data):
 with (OUT/name).open('xb') as f:f.write(data)
def js(name,data):put(name,json.dumps(data,ensure_ascii=False,indent=1).encode('utf8'))
def clock(t):return f'{int(t)//60}:{t%60:06.3f}'
def pitch(m):
 n=round(m);return ['Do','Do#','Re','Mib','Mi','Fa','Fa#','Sol','Lab','La','Sib','Si'][n%12]+str(n//12-1)+(f' {(m-n)*100:+.1f}c' if abs(m-n)>.0005 else '')
def segments(e):return e.get('salidas',[[e['t'],e['t']+e['dur']]])
def at(e,t):return e['midi']+(e.get('midi_fin',e['midi'])-e['midi'])*(t-e['t'])/e['dur']

# XML: ventanas de salida completas; cada voz tiene sus descansos y ligaduras.
xml=ET.Element('score-partwise',version='4.0');work=ET.SubElement(xml,'work');ET.SubElement(work,'work-title').text=P['titulo']+' / revisión 8'
ident=ET.SubElement(xml,'identification');ET.SubElement(ident,'creator',type='composer').text='Canek Zapata';ET.SubElement(ident,'rights').text='© 2026 Canek Zapata'
lst=ET.SubElement(xml,'part-list');maxerr=0;xmlcount=0
for tr in P['partes']:
 pid=f'P{tr["numero"]}';sp=ET.SubElement(lst,'score-part',id=pid);ET.SubElement(sp,'part-name').text=tr['nombre']
 part=ET.SubElement(xml,'part',id=pid);raw=[]
 for e in P['eventos'][tr['id']]:
  for index,(a,b) in enumerate(segments(e)):raw.append((a,b,e,index))
 raw.sort(key=lambda v:(v[0],v[1]));ends=[];assigned=[]
 for a,b,e,index in raw:
  lane=next((i for i,end in enumerate(ends) if end<=a+1e-9),len(ends))
  if lane==len(ends):ends.append(b)
  else:ends[lane]=b
  assigned.append((a,b,e,index,lane))
 for me in P['medidas_editoriales']:
  a,b=me['t'],me['fin'];total=round((b-a)/Q*DIV);mm=ET.SubElement(part,'measure',number=str(me['n']));attr=ET.SubElement(mm,'attributes')
  if me['n']==1:ET.SubElement(attr,'divisions').text=str(DIV)
  tm=ET.SubElement(attr,'time')
  if me['free']:ET.SubElement(tm,'senza-misura')
  else:ET.SubElement(tm,'beats').text='4';ET.SubElement(tm,'beat-type').text='4'
  if me['n']==1:
   clef=ET.SubElement(attr,'clef');ET.SubElement(clef,'sign').text='percussion' if tr['id'] in ['bombo','caja','hat','tom','aro','ride'] else 'G';ET.SubElement(clef,'line').text='2'
  if me['n']==1 or me['free'] or any(abs(a-s['t'])<1e-7 for s in P['secciones']):
   dr=ET.SubElement(mm,'direction');dt=ET.SubElement(dr,'direction-type');ET.SubElement(dt,'words').text=clock(a)+(' / segundos libres; celda editorial' if me['free'] else ' / negra=144')
   if me['n']==1:ET.SubElement(dr,'sound',tempo='144')
  hits=[v for v in assigned if v[0]<b-1e-9 and v[1]>a+1e-9];voices=sorted({v[-1] for v in hits}) or [0]
  for vi,lane in enumerate(voices):
   if vi:ET.SubElement(ET.SubElement(mm,'backup'),'duration').text=str(total)
   cur=0
   def rest(length):
    if length<=0:return
    nn=ET.SubElement(mm,'note');ET.SubElement(nn,'rest');ET.SubElement(nn,'duration').text=str(length);ET.SubElement(nn,'voice').text=str(lane+1)
   for u,v,e,index,l in [z for z in hits if z[-1]==lane]:
    aa=max(cur,round((max(u,a)-a)/Q*DIV));bb=min(total,round((min(v,b)-a)/Q*DIV))
    if bb<=aa:continue
    rest(aa-cur);nn=ET.SubElement(mm,'note',id=f'{e["id"]}_s{index}_m{me["n"]}');xmlcount+=1
    if e.get('altura_asignable',True):
     m=at(e,max(u,a));n=round(m);step,alter=[('C',0),('C',1),('D',0),('E',-1),('E',0),('F',0),('F',1),('G',0),('A',-1),('A',0),('B',-1),('B',0)][n%12]
     pp=ET.SubElement(nn,'pitch');ET.SubElement(pp,'step').text=step
     if abs(alter+m-n)>1e-10:ET.SubElement(pp,'alter').text=f'{alter+m-n:.9f}'
     ET.SubElement(pp,'octave').text=str(n//12-1)
    else:
     pp=ET.SubElement(nn,'unpitched');ET.SubElement(pp,'display-step').text='C';ET.SubElement(pp,'display-octave').text='5'
    ET.SubElement(nn,'duration').text=str(bb-aa)
    if u<a-1e-8:ET.SubElement(nn,'tie',type='stop')
    if v>b+1e-8:ET.SubElement(nn,'tie',type='start')
    ET.SubElement(nn,'voice').text=str(lane+1)
    if e.get('texto') and u>=a-1e-8 and abs(u-e['t'])<1e-7:
     ly=ET.SubElement(nn,'lyric');ET.SubElement(ly,'syllabic').text='single';ET.SubElement(ly,'text').text=e['texto']
    notation=ET.SubElement(nn,'notations');tech=ET.SubElement(notation,'technical')
    text=e['articulacion']+(f'; trayectoria continua hasta {pitch(e["midi_fin"])}; exacta en JSON' if 'midi_fin' in e else '')
    ET.SubElement(tech,'other-technical').text=text
    if e.get('acento'):ET.SubElement(ET.SubElement(notation,'articulations'),'accent')
    cur=bb;maxerr=max(maxerr,abs((aa*Q/DIV+a)-max(u,a)))
   rest(total-cur)
put(f'luciernagas-partitura-completa-v8-s1-{TAG}.musicxml',ET.tostring(xml,encoding='utf-8',xml_declaration=True))
buf=io.StringIO(newline='');wr=csv.writer(buf);wr.writerow(['parte','id','t_s','dur_s','MIDI','Hz','gesto','silaba','ancestro','evento_JSON'])
for tr in P['partes']:
 for e in P['eventos'][tr['id']]:wr.writerow([tr['id'],e['id'],e['t'],e['dur'],e['midi'],e['hz'],e['articulacion'],e.get('texto',''),e.get('ancestro',''),json.dumps(e,ensure_ascii=False)])
put(f'luciernagas-eventos-v8-s1-{TAG}.csv',buf.getvalue().encode('utf-8-sig'))

pdfmetrics.registerFont(TTFont('Ar','C:/Windows/Fonts/arial.ttf'));pdfmetrics.registerFont(TTFont('ArB','C:/Windows/Fonts/arialbd.ttf'))
PDF=OUT/f'luciernagas-partitura-analizada-v8-s1-{TAG}.pdf';assert not PDF.exists()
W,H=landscape(A3);c=canvas.Canvas(str(PDF),pagesize=(W,H));c.setTitle(P['titulo']+' / partitura revisada y analizada');c.setAuthor('Canek Zapata')
INK='#153532';ACC='#a34425';PAPER='#f4f1e2';pages=[]
def text(x,y,s,size=11,bold=False,col=INK):
 c.setFont('ArB' if bold else 'Ar',size);c.setFillColor(col);c.drawString(x,y,str(s))
def line(x,y,xx,yy,col=INK,width=.5):c.setStrokeColor(col);c.setLineWidth(width);c.line(x,y,xx,yy)
def para(s,y,size=13,x=48,width=None):
 width=width or W-x-48;acc=''
 for word in s.split():
  trial=(acc+' '+word).strip()
  if pdfmetrics.stringWidth(trial,'Ar',size)>width:text(x,y,acc,size);y-=size*1.5;acc=word
  else:acc=trial
 if acc:text(x,y,acc,size);y-=size*1.5
 assert y>44,('desborde',len(pages),y,s[:50]);return y
def new(title,sub='',big=False):
 global W,H
 if pages:c.showPage()
 W,H=A2 if big else landscape(A3);c.setPageSize((W,H));pages.append(title)
 c.setFillColor(PAPER);c.rect(0,0,W,H,fill=1,stroke=0);text(48,H-48,title,24,True);text(48,H-73,sub,10,col=ACC)
 line(48,35,W-48,35);text(48,20,'CANEK ZAPATA / REJILLA / REVISIÓN 8 / 22 OCT 2026 / PARTITURA SIN AUDIO',8);text(W-78,20,len(pages),9)

new('Llevemos unas luciérnagas al lago','Proto punk folk / contacto, transferencia y una respuesta que cambia de boca')
y=para('Dos personas llegan al agua. El rasgueo insiste. Un roce falla, encuentra un parcial y lo entrega a otro cuerpo. Cuando vuelve la canción, una espera ocupa el lugar donde antes la voz seguía de largo.',H-120,18)
y=para(f'4:18.667 / 144 negras por minuto en las zonas métricas / 36 partes / {sum(map(len,P["eventos"].values())):,} eventos internos / centro de 60 segundos sin pulso.',y-10,13)
for s in P['secciones']:
 text(48,y,f'{clock(s["t"])} - {clock(s["fin"])}',11,True);text(260,y,s['id']+' / '+s['nombre'],12);y-=28
y=para('Lectura: punto = entrada; línea = ventana de salida; pendiente = cambio continuo de altura. El eje vertical de cada parte se adapta a sus notas, con mínimo y máximo rotulados; no hay recorte oculto. Las páginas completas son proporcionales cromáticas, no pentagramas convencionales.',y-12,12)
para('JSON v8 conserva estado, controles y ventanas audibles. MusicXML escribe notas, silencios, alteraciones y trayectorias indicadas; los portamentos, vocoders y transferencias requieren el contrato adjunto. La revisión no produjo audio ni másters.',y-10,12)

new('La pregunta tiene cuerpo y huecos','Q y R: conservar el gancho, desarrollar sus respuestas')
for index,(pat,label) in enumerate([(P['tema_Q'],'Q / Mi - Si - Do / Fa tardío / Mi'),(P['tema_R'],'R / respuesta y descenso')]):
 y=H-170-index*220;text(48,y+42,label,17,True);x0=160;x1=W-70
 for beat in range(9):
  x=x0+(x1-x0)*beat/8;line(x,y-60,x,y+30,'#cbd3c0');text(x,y-79,beat,9)
 for beat,m,d in pat:
  x=x0+(x1-x0)*beat/8;yy=y+(m-62)*6;line(x,yy,x0+(x1-x0)*(beat+d)/8,yy,ACC,2);c.setFillColor(ACC);c.circle(x,yy,3,fill=1,stroke=0);text(x+4,yy+9,pitch(m),10)
para('El semitono Si-Do y el Fa tardío distinguen la pregunta. Al acercarse a la serie de Mi2, esas diferencias de altura pueden fusionarse: el regreso conserva una diferencia mediante la duración y la espera. La obstinación del riff tiene una función reconocible; sus ataques perdidos dejan sitio a otra respuesta.',H-610,13)

# Cada frase tiene su propio espacio y su prosodia visible.
leads=[l for l in P['letra'] if l['capa']=='voz'];byid={e['id']:e for es in P['eventos'].values() for e in es}
for offset in range(0,len(leads),3):
 new(f'Voz / frases {offset+1}-{min(offset+3,len(leads))}','Alturas, sílabas, duración y acento; el espacio vacío también pertenece a la frase')
 for j,ly in enumerate(leads[offset:offset+3]):
  yy=H-150-j*205;events=[byid[i] for i in ly['ids']];a,b=ly['t'],ly['fin'];text(48,yy+35,f'{clock(a)} / {ly["texto"]}',15,True)
  for e in events:
   xa=170+(W-230)*(e['t']-a)/(b-a);xb=170+(W-230)*(e['t']+e['dur']-a)/(b-a);y=yy+(e['midi']-63)*4
   line(xa,y,xb,y,ACC if e.get('acento') else INK,2);c.setFillColor(ACC);c.circle(xa,y,3 if e.get('acento') else 2,fill=1,stroke=0)
   text(xa,y-24,e['texto'],11,e.get('acento',False));text(xa,y+10,pitch(e['midi']),8)
  text(48,yy-73,f'Duración de frase {b-a:.3f} s / espera heredada {ly.get("espera_heredada_s",0):.3f} s',10,col=ACC)

new('Pantano / contacto, retirada y transferencia','V / 1:33.333-2:33.333 / sin metrónomo, voz humana, batería ni señales periódicas de salida')
y=H-120
for tr,e in sorted([(tr,e) for tr in P['partes'] for e in P['eventos'][tr['id']] if C0<=e['t']<C1],key=lambda z:z[1]['t']):
 text(48,y,clock(e['t']),11,True);text(155,y,tr['nombre'][:30],10);text(385,y,e['articulacion'][:65],10);text(W-120,y,f'{e["dur"]:.3f} s',10);y-=27
y=para(f'El contacto libera su primer deslizamiento a +1.005 s del segundo intento. La cuerda recibe después de {PACK["espera_hasta_cuerda_s"]:.6f} s. Su captación se obtiene del estado evolucionado de red_modal; el junco recibe esa captación y su fase.',y-12,12)
y=para(f'La pérdida entre guitarra y primera recepción define una espera de {PACK["espera_aprendida_s"]:.9f} s. En el regreso se escucha entre en y otras. No se pone una respiración dentro de llevemos.',y-10,12)
para('Ocho oscuridades se obtienen de las pausas escritas. Las salidas y los efectos se cierran; las fases y los estados siguen calculándose. El silencio acústico requiere verificación en la futura interpretación.',y-10,12)

new('Matemática que cambia una decisión','Restricciones locales, contacto con umbral, extracción y transporte con memoria')
y=H-120
for title,body in [
 ('Tres promesas y orden de encuentros','Cada encuentro acerca xj-xi a su promesa mediante una proyección relajada de .72. Se enseñan AB=0, BC=0 y CA=85 cents. Las operaciones conservan la suma de afinaciones, pero cumplir una puede deshacer otra. El orden AC y CA da resultados diferentes: 15.579 cents de distancia en el caso de prueba. No se atribuye esa regla a la geología.'),
 ('Contacto','La carga integra presión menos fuga: dq/dt = p - .72q. Al superar .34+.33*película, desliza y conserva .18 de la carga. La excitación y el ruido de contacto tienen curvas distintas. El primer intento no libera parcial; el segundo sí. La película cambia por una acción escrita de la lata, no por humedad medida.'),
 ('Transferencia efectiva','Se extraen envolventes complejas de modos 1/2/3/5 del contacto; se amortiguan y rotan antes de inyectarlas en cuerda. El estado de cuerda evoluciona con los coeficientes del motor, arco y presión; su primera cuerda presta cuatro modos al junco. La normalización inicial del junco es una ganancia activa declarada.'),
 ('Transporte que continúa','Veinticuatro planes. La fuente siguiente es el destino anterior; la masa siguiente es la recibida menos pérdidas explícitas. La fase de cada destino procede de la suma fasorial de sus aristas. Ocho planes cambian efectivamente al incluir costo por familia. Los cortes reducen permanentemente ciertas masas; no se restaura el acorde inicial.')]:
 text(48,y,title,16,True);y=para(body,y-27,12)-23

new('Tres maneras de acercarse a una pared','VIII / resonancia compartida, contagio de ataques, casi continuidad')
y=H-125
for title,body in [
 ('3:26.667-3:40.000 / compartir resonancia','Cuerda, chelo y arpa prolongan entradas separadas. La guitarra deja caer dos voces y el bombo camina aislado. El vocoder de cuerda toma el comienzo del texto. La densidad procede primero de duraciones, no de una ráfaga de ataques.'),
 ('3:40.000-3:53.333 / contagiar el ataque','La mbira llama; berimbau, guitarra y piano contestan en tres generaciones con retardos distintos. Cada réplica conserva la referencia a su fuente. Aro, caja y tom reciben esos ataques. El coro de junco continúa en otras formas de experiencia.'),
 ('3:53.333-4:06.667 / casi un cuerpo','Cinco, seis y siete ataques por compás sostienen el alambre; cuerda, órgano y sala prolongan el cuerpo. Las células de batería comprimen Q/R y cambian las divisiones del hat. Una última frase humana permanece legible entre los cortes.'),
 ('El corte deja una pérdida','Tres agujeros cierran todos los buses. El siguiente transporte retiene .43 de la cuarta masa y .87 de la primera, además de la amortiguación ordinaria. Apaga el teléfono termina también las sílabas de boca en curso. Al corte de banda quedan la última llegada del junco y el tercer parcial en waterphone.')]:
 text(48,y,title,16,True);y=para(body,y-28,13)-30

for start in [0,18]:
 new(f'Partes {start+1}-{start+18}','36 partes con acontecimientos; cuatro voces de junco y seis componentes de batería')
 y=H-120
 for tr in P['partes'][start:start+18]:
  text(48,y,f'{tr["numero"]:02} {tr["nombre"]}',12,True);text(430,y,tr['funcion'],10);text(W-120,y,len(P['eventos'][tr['id']]),10)
  text(48,y-15,tr['motor'],8,col=ACC);y-=34

new('Contrato de interpretación y alcance de la revisión','El análisis completo acompaña en ANALISIS-DE-LA-PIEZA.md')
y=H-120
for body in [
 'La partitura conserva eventos internos y ventanas salidas separadas. Un corte cierra sonido y efectos; no borra la historia ni crea otro ataque. Cada gesto de contacto consume su curva y su ruido propio: no se dobla con una púa automática.',
 'GuitarraMemoria consume las tres afinaciones del historial de encuentros, interpoladas en 30 ms. Humedad/película y presión se pasan explícitamente a su avance. La variante motores-memoria.py inyecta envolventes complejas en cuerda; conserva el resto del motor afinable.',
 'El junco realiza cada arista con fase integrada en frecuencia logarítmica. Al concluir un plan, suma por receptor y entrega su fase. Una fase se conserva también durante esperas y con salida cerrada. Las masas son representación compositiva normalizada; no julios acústicos.',
 'Difonos/Sabina necesita guías separadas con alturas, acentos y respiraciones escritos. Cada vocoder recibe su guía y portadora. El PDF completo muestra todas las ventanas de salida; JSON y CSV conservan también los estados internos y controles.',
 'Se conservaron Q, R, el riff seco, el órgano con histéresis, el terreno elegido y 36 partes. Se reescribieron las frases, el centro, las transferencias, el regreso y las tres olas. La relación con El río está en el desarrollo de una fuente; con V del Androide, en la transformación de cuerpo, articulación y sujeto.',
 'Límites: no se escuchó ni sintetizó la pieza. La claridad de texto, el balance de la pared, la aspereza del ataque y el sostén perceptivo de la pausa final siguen siendo preguntas para interpretar. Se mantienen los criterios de Compositor y las fuentes locales con su alcance de lectura declarado.'
 ]:y=para(body,y,13)-23

# Todas las partes en páginas A2: escala propia explícita, sin recortar alturas.
for sec in P['secciones']:
 span=10 if sec['modo'].startswith('senza') else 8*4*Q;a=sec['t']
 while a<sec['fin']-1e-7:
  b=min(sec['fin'],a+span);new(f'{sec["id"]} / {clock(a)} - {clock(b)}',sec['accion'],True)
  x0,x1,top,row=260,W-48,H-130,40
  for aa,bb in P['oscuridades']+P['agujeros_pared']:
   aa=max(a,aa);bb=min(b,bb)
   if bb>aa:c.setFillColor('#dde3d0');c.rect(x0+(x1-x0)*(aa-a)/(b-a),top-36*row,(x1-x0)*(bb-aa)/(b-a),36*row+20,fill=1,stroke=0)
  step=1 if sec['modo'].startswith('senza') else Q
  for tt in np.arange(math.ceil(a/step)*step,b+1e-8,step):
   xx=x0+(x1-x0)*(tt-a)/(b-a);line(xx,top+18,xx,top-36*row,'#c8d0bd',.3)
   if sec['modo'].startswith('senza') or abs(tt/(4*Q)-round(tt/(4*Q)))<1e-5:text(xx+1,top+30,f'{tt:.2f}',7)
  for j,tr in enumerate(P['partes']):
   yy=top-j*row;hits=[]
   for e in P['eventos'][tr['id']]:
    for aa,bb in segments(e):
     if aa<b and bb>a:hits.append((e,max(a,aa),min(b,bb)))
   vals=[at(e,t) for e,u,v in hits for t in [u,v]];lo=math.floor(min(vals))-1 if vals else 59;hi=math.ceil(max(vals))+1 if vals else 61
   text(48,yy+5,f'{tr["numero"]:02} {tr["nombre"][:30]}',8,True);text(48,yy-9,f'MIDI {lo}-{hi} / {tr["id"]}',7,col=ACC)
   line(x0,yy,x1,yy,'#cbd3bf',.3)
   for e,u,v in hits:
    xa=x0+(x1-x0)*(u-a)/(b-a);xb=x0+(x1-x0)*(v-a)/(b-a);ya=yy-14+28*(at(e,u)-lo)/(hi-lo);yb=yy-14+28*(at(e,v)-lo)/(hi-lo)
    line(xa,ya,xb,yb,ACC if e.get('libre') else INK,1.25)
    if abs(u-e['t'])<1e-7:
     c.setFillColor(ACC);c.circle(xa,ya,1.8,fill=1,stroke=0)
     label=e.get('texto') or (e['articulacion'][:45] if sec['modo'].startswith('senza') else '')
     if label:
      size=5.8;xx=min(xa+2,x1-pdfmetrics.stringWidth(label,'Ar',size));text(xx,ya+5,label,size,col=ACC)
  text(48,61,'Escala MIDI propia por parte y ventana, indicada a la izquierda. Trazos completos sin recortar alturas; exactitud en XML/CSV/JSON.',8)
  text(48,48,'Verde: salida escrita. Naranja: gesto del centro. Fondo sombreado: bus cerrado. Una reapertura no significa reataque.',8)
  a=b
c.save()

qa=ROOT/'tmp'/f'revision-v8-{TAG}';qa.mkdir(parents=True,exist_ok=False);doc=fitz.open(PDF)
for i,page in enumerate(doc):
 pix=page.get_pixmap(matrix=fitz.Matrix(.65,.65),alpha=False)
 with (qa/f'pagina-{i+1:02}.png').open('xb') as f:f.write(pix.tobytes('png'))
# Contacto visual real de todas las páginas, más página del centro a buena escala.
thumbw,thumbh=260,360;cols=6;rows=math.ceil(len(doc)/cols);sheet=Image.new('RGB',(cols*thumbw,rows*thumbh),'#d9ddd1');dr=ImageDraw.Draw(sheet)
for i,page in enumerate(doc):
 im=Image.open(qa/f'pagina-{i+1:02}.png');im.thumbnail((thumbw-12,thumbh-30));xx=(i%cols)*thumbw;yy=(i//cols)*thumbh
 sheet.paste(im,(xx+(thumbw-im.width)//2,yy+20));dr.text((xx+8,yy+3),f'{i+1}: {pages[i][:30]}',fill='black')
bb=io.BytesIO();sheet.save(bb,format='PNG');put(f'proceso/07-edicion-final-s1-{TAG}.png',bb.getvalue())
ci=pages.index('Pantano / contacto, retirada y transferencia');pix=doc[ci].get_pixmap(matrix=fitz.Matrix(1.25,1.25),alpha=False);put(f'proceso/08-centro-final-s1-{TAG}.png',pix.tobytes('png'))
js('datos/edicion-v8.json',{'pdf':PDF.name,'paginas':len(doc),'titulos':pages,'xml_notas':xmlcount,'xml_error_max_s':maxerr,'divisiones':DIV,'raster':str(qa)})
put('fuentes/editar_revision-v8.py',Path(__file__).read_bytes())
print(json.dumps({'pdf':str(PDF),'paginas':len(doc),'error_xml_s':maxerr,'raster':str(qa)},ensure_ascii=False))
