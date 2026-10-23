"""Partitura de dirección, material notado, MusicXML íntegro y tabla de eventos.
No sintetiza la canción. PDF con revisión raster en el mismo paquete.
"""
from comun import *
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import xml.etree.ElementTree as ET,csv
PAPEL='#f7f0e7';INK='#1d2869';ACC='#732605'
def fmt(t):return f'{int(t//60)}:{t%60:04.1f}'
def nom(m):return ['C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B'][int(round(m))%12]+str(int(round(m))//12-1)
def degree(m):
 names=[0,0,1,2,2,3,3,4,5,5,6,6];m=round(m);return (m//12-5)*7+names[m%12]
def intercambio(out,P,tag):
 root=ET.Element('score-partwise',version='4.0');w=ET.SubElement(root,'work');ET.SubElement(w,'work-title').text=P['titulo']+' - partitura para revisión';ident=ET.SubElement(root,'identification');ET.SubElement(ident,'creator',type='composer').text='Canek Zapata';pl=ET.SubElement(root,'part-list');div=960
 for idx,(name,events) in enumerate(P['eventos'].items(),1):
  sp=ET.SubElement(pl,'score-part',id=f'P{idx}');ET.SubElement(sp,'part-name').text=name
  part=ET.SubElement(root,'part',id=f'P{idx}');ends=[];lanes=[]
  for e in events:
   a=e['pulso'];b=a+e['dur_pulsos'];lane=next((j for j,z in enumerate(ends) if z<=a+1e-6),len(ends))
   if lane==len(ends):ends.append(b)
   else:ends[lane]=b
   lanes.append((e,lane))
  for bar in range(96):
   mm=ET.SubElement(part,'measure',number=str(bar+1))
   if bar==0:
    at=ET.SubElement(mm,'attributes');ET.SubElement(at,'divisions').text=str(div);ti=ET.SubElement(at,'time');ET.SubElement(ti,'beats').text='4';ET.SubElement(ti,'beat-type').text='4';cl=ET.SubElement(at,'clef');ET.SubElement(cl,'sign').text='G';ET.SubElement(cl,'line').text='2'
    if idx==1:dire=ET.SubElement(mm,'direction');ET.SubElement(dire,'sound',tempo=str(BPM))
   pieces=[(e,l) for e,l in lanes if e['pulso']<4*(bar+1) and e['pulso']+e['dur_pulsos']>4*bar]
   voices=sorted(set(l for e,l in pieces)) or [0]
   for vi,l in enumerate(voices):
    if vi:ET.SubElement(ET.SubElement(mm,'backup'),'duration').text=str(4*div)
    cur=0
    for e,_ in [x for x in pieces if x[1]==l]:
     a=max(0,round((e['pulso']-4*bar)*div));b=min(4*div,round((e['pulso']+e['dur_pulsos']-4*bar)*div));a=max(cur,a);b=max(a+1,b)
     if a>=4*div:continue
     b=min(4*div,b)
     if a>cur:
      nt=ET.SubElement(mm,'note');ET.SubElement(nt,'rest');ET.SubElement(nt,'duration').text=str(a-cur);ET.SubElement(nt,'voice').text=str(l+1)
     nt=ET.SubElement(mm,'note');pitch=ET.SubElement(nt,'pitch');m=int(round(e['midi']));steps=[('C',0),('C',1),('D',0),('E',-1),('E',0),('F',0),('F',1),('G',0),('A',-1),('A',0),('B',-1),('B',0)];st,alt=steps[m%12];ET.SubElement(pitch,'step').text=st
     if alt:ET.SubElement(pitch,'alter').text=str(alt)
     ET.SubElement(pitch,'octave').text=str(m//12-1);ET.SubElement(nt,'duration').text=str(b-a);ET.SubElement(nt,'voice').text=str(l+1)
     if e['pulso']<4*bar:ET.SubElement(nt,'tie',type='stop')
     if e['pulso']+e['dur_pulsos']>4*(bar+1):ET.SubElement(nt,'tie',type='start')
     if e.get('texto') and e['pulso']>=4*bar:ET.SubElement(ET.SubElement(nt,'lyric'),'text').text=e['texto']
     cur=b
    if cur<4*div:
     nt=ET.SubElement(mm,'note');ET.SubElement(nt,'rest');ET.SubElement(nt,'duration').text=str(4*div-cur);ET.SubElement(nt,'voice').text=str(l+1)
 guardar(out/f'partitura-completa-s{SEED}-{tag}.musicxml',ET.tostring(root,encoding='utf-8',xml_declaration=True))
 b=io.StringIO(newline='');writer=csv.writer(b);writer.writerow(['capa','pulso','segundos','duracion_pulsos','duracion_s','MIDI','nota','texto','funcion','vehiculo','velocidad_m_s','estado_deposito','ramal'])
 for c,es in P['eventos'].items():
  for e in es:writer.writerow([c,e['pulso'],e['t'],e['dur_pulsos'],e['dur'],e['midi'],nom(e['midi']),e.get('texto',''),e.get('frase',e.get('funcion','')),e.get('vehiculo',''),e.get('velocidad_m_s',''),e.get('estado_deposito',''),e.get('ramal','')])
 guardar(out/f'eventos-completos-s{SEED}-{tag}.csv',b.getvalue().encode('utf-8-sig'))
def main():
 out=ultimo();P=leer(score());tag=out.name.split('-')[-1];intercambio(out,P,tag);bench=leer(out/'sondas-instrumentos-r2.json');TR=leer(out/'trafico.json');S=leer(depo());W,H=landscape(A4);margin=40;path=out/f'partitura-para-revisar-s{SEED}-{tag}.pdf'
 if path.exists():raise FileExistsError(path)
 pdfmetrics.registerFont(TTFont('Ar','C:/Windows/Fonts/arial.ttf'));pdfmetrics.registerFont(TTFont('ArB','C:/Windows/Fonts/arialbd.ttf'));c=canvas.Canvas(str(path),pagesize=(W,H));c.setTitle(P['titulo']+' - partitura para revisar');c.setAuthor('Canek Zapata');page=0
 def text(x,y,s,size=10,bold=False,color=INK):c.setFillColor(color);c.setFont('ArB' if bold else 'Ar',size);c.drawString(x,y,str(s))
 def para(s,y,size=10,width=W-80,leading=15,x=40):
  line=''
  for word in s.split():
   trial=(line+' '+word).strip()
   if pdfmetrics.stringWidth(trial,'Ar',size)>width:
    text(x,y,line,size);y-=leading;line=word
   else:line=trial
  if line:text(x,y,line,size);y-=leading
  assert y>30,('texto fuera de página',page,y);return y
 def new(title,sub=''):
  nonlocal page
  if page:c.showPage()
  page+=1;c.setFillColor(PAPEL);c.rect(0,0,W,H,fill=1,stroke=0);text(40,H-42,title,21,True);text(40,H-63,sub,9,color=ACC);c.setStrokeColor(INK);c.setLineWidth(.5);c.line(40,34,W-40,34);text(40,21,'POR AQUÍ TAMBIÉN SE BAILA  |  PRIMERA ETAPA  |  SIN MÁSTER NI VIDEO',7);text(W-76,21,str(page),8)
 def staff(x,y,w,notes,label='',bars=4):
  gap=6;c.setStrokeColor(INK);c.setLineWidth(.35)
  for k in range(5):c.line(x,y+k*gap,x+w,y+k*gap)
  bw=w/bars
  for k in range(bars+1):c.line(x+k*bw,y-4,x+k*bw,y+28)
  if label:text(x,y+46,label,10,True)
  for beat,m,d in notes:
   xx=x+bw*beat/4+3;yy=y+(degree(m)-degree(64))*gap/2
   for dd in range(-8,18,2):
    ly=y+dd*gap/2
    if (dd<0 or dd>8) and abs(ly-yy)<gap*.55:c.line(xx-5,ly,xx+5,ly)
   c.setFillColor(INK);c.ellipse(xx-3,yy-2,xx+3,yy+2,fill=1,stroke=0);c.line(xx+3,yy,xx+3,yy+19);c.setStrokeColor(ACC);c.setLineWidth(1.1);c.line(xx,yy-9,xx+max(3,bw*d/4-3),yy-9);c.setStrokeColor(INK);c.setLineWidth(.35);text(xx-4,y-28,nom(m),6)
 new('Por aquí también se baila','Canek Zapata - Traspuesta 22 - partitura de dirección para revisión, 21-22 de octubre de 2026')
 y=para('Laberinto de transporte. Cumbia sonidera, recursos rítmicos carnáticos, repetición y drones de jazz contemporáneo, Reich y contacto instrumental de Lachenmann.',H-98,13,leading=19)
 y=para('96 compases 4/4 a 96 BPM: 4:00 de escritura + 6 s de cola previstos. Dos compases forman un ciclo de ocho pulsos agrupado 4+2+2. Treinta capas con relevos; solista: láser de transbordos, sin solo de requinto.',y-5,10)
 y-=14
 for s in P['secciones']:
  text(42,y,f'{s["compas_inicio"]:02d}-{s["compas_fin"]:02d}',10,True);text(100,y,fmt(s['t']),10);text(158,y,s['nombre'],11);y-=25
 y=para('Cómo leer: páginas de temas en notación proporcional (altura en pentagrama; trazo inferior = duración en pulsos), remates exactos y solo D; después, el plan de los 96 compases. MusicXML incluye las treinta partes y CSV enumera todos los eventos. Los timbres finales aún no se han producido.',y-6,9,leading=14)
 para('Parada acordada: revisar contigo la escritura y las sondas de instrumentos. No continuar a la mezcla completa hasta esa revisión.',y-8,11,leading=16)
 new('A. La frase tiene pregunta y respuesta','Notación proporcional; clave de sol, línea inferior E4. Barras de compás a 4 pulsos. No son figuras rítmicas convencionales.')
 for row in range(2):
  notes=[(k*4+a,m,d) for k in range(4) for a,m,d in P['tema_A'][row*4+k]];staff(52,395-row*150,W-104,notes,f'Tema A - compases del motivo {row*4+1} a {row*4+4}')
 y=para('Cabeza D-F-A, respuesta descendente y llegada C#-D. Acordeón presenta; láser aprende la misma frase; clarinete responde con otro aliento. El regreso modifica el inicio de los dos últimos compases y conserva la llegada.',120,11,leading=16)
 para('Armonía de ocho compases: Dm9 | Dm9 | G6/D | G6/D | Bbmaj7/D | Bbmaj7/D | A7sus | A7. El pedal D/A sostiene el espacio; la dominante llega al cierre, no cambia de acorde en cada irregularidad del tráfico.',y-7,10)
 new('B. Contar el camino y volver al uno','Recursos de solkattu y subdivisión: escritura propia inspirada en práctica carnática; no transcripción de una korvai tradicional.')
 for row,R in enumerate(P['moras']):
  yy=435-row*115;sub=R['subdivision'];bw=(W-115)/(8*sub);text(42,yy+28,f'{sub} unidades por pulso: M={R["M"]}; pausa={R["silencio"]}; 3M+2P={R["total_unidades"]}',11,True)
  for j in range(8*sub):
   x=48+j*bw;c.setStrokeColor(INK);c.setLineWidth(.6 if j%sub==0 else .15);c.line(x,yy-8,x,yy+16)
   if j in R['golpes']:c.setFillColor(ACC);c.circle(x+3,yy,2.5,fill=1,stroke=0)
   if j%sub==0:text(x,yy-25,j//sub+1,8)
  text(W-65,yy,'1',13,True);text(48,yy-46,'Agrupación de referencia: 1-2-3-4 | 5-6 | 7-8. La llegada está en el siguiente pulso 1.',9)
 para('El pulso de ocho continúa durante un atasco. Lo que cambia entre subdivisiones es el fraseo interior: cuatro, tres o cinco unidades por pulso. Los silencios son parte de las tres repeticiones del remate. Las entradas vocales rítmicas tienen articulación t/k y vocales escritas por separado en Boca de tres tiempos.',90,9,leading=13)
 new('C. Solo D: hacer transbordo con una frase','Compases 53-68. Presentación - réplica - red - atasco - Talbot - cadencia. Sin voz de verso ni requinto.')
 for row,start in enumerate([52*4,60*4]):
  notes=[]
  for name in ['laser-directo','laser-laberinto','laser-talbot']:
   for e in P['eventos'][name]:
    if start<=e['pulso']<start+16:notes.append((e['pulso']-start,e['midi'],e['dur_pulsos']))
  staff(52,395-row*145,W-104,notes,f'Entradas efectivas - compases {start//4+1} a {start//4+4}')
 y=para('Diferencia decisiva: el solo conserva la cabeza D-F-A, pero cambia los caminos de sus respuestas. Retardos de la red desde distancias de la lámina, comprimidas 1:16; cruces ortogonales con pérdidas. Talbot 1/3 y 2/5 separa copias de la célula. El tráfico modifica el reloj local antes de entrar a esa red.',115,10,leading=15)
 para('El raspador lee el depósito efectivamente acumulado. Dos drones permanecen como referencia. Al regreso no se restaura la distribución inicial: el acordeón recupera el motivo que el láser llevó por otras rutas.',y-4,10)
 new('D. La lámina y lo que cambia al recorrerla','Datos originales de Traspuesta; red radial reducida de depósito y trazas de transporte como decisiones de composición.')
 img=next((out/'proceso').glob('02b-*.png'));c.drawImage(str(img),(W-600)/2,190,width=600,height=315,preserveAspectRatio=True,anchor='c')
 y=para(f'La Mesa 22 mide 7 km de ancho y 340 m de relieve. Su Abanico del Alcor está dentro de la hoja. Modelo vigente: 320 paquetes de 600 m3, {len(np.unique(np.array(S["caminos"]),axis=0))} recorridos distintos y una misma salida. El depósito máximo se amplifica hasta {np.max(S["depositos_m"]):.1f} m; no es una predicción geológica.',152,10)
 para('Tráfico: 34 vehículos en un anillo de 720 m, velocidad óptima según distancia al vecino. El reloj local integra velocidad y se cierra musicalmente cada ocho pulsos; por debajo de 0.8 m/s se suspenden ciertas entradas. No hay varispeed del máster ni afirmación de caos determinista.',y-5,10)
 # Plan íntegro de eventos: seis páginas, dieciséis compases cada una.
 names=list(P['eventos']);rowh=12.2;x0=174;cw=(W-40-x0)/16
 for group in range(6):
  a=group*16;b=a+16;new(f'Plan de dirección - compases {a+1:02d} a {b:02d}','Cada trazo es un evento efectivo: posición = entrada; longitud = duración. El archivo MusicXML conserva notas/pausas y voces.')
  for k in range(16):
   x=x0+k*cw;text(x+3,H-91,a+k+1,8,True);text(x+1,H-107,P['armonia'][a+k]['acorde'],6)
  top=H-121
  for j,name in enumerate(names):
   y=top-j*rowh;text(40,y,name,7,bold=name.startswith('laser'))
   c.setStrokeColor('#aaa59c');c.setLineWidth(.2);c.line(x0,y-2,W-40,y-2)
   for k in range(17):c.line(x0+k*cw,y-2,x0+k*cw,y+8)
   c.setStrokeColor(ACC if 15<=j<=19 else INK);c.setLineWidth(1.6)
   for e in P['eventos'][name]:
    start=max(a*4,e['pulso']);end=min(b*4,e['pulso']+e['dur_pulsos'])
    if end<=start:continue
    x=x0+(start-a*4)/4*cw;xx=x0+(end-a*4)/4*cw;c.line(x,y+3,max(x+1,xx),y+3)
  secs=[s['nombre'] for s in P['secciones'] if s['compas_inicio']<=b and s['compas_fin']>a];para('Escenas: '+' / '.join(secs),75,9,leading=13)
 new('Texto cantado: estaciones dentro de una bolsa','Letra original; alturas, duraciones y sílabas completas en la partitura de eventos/MusicXML. No está grabada la canción.')
 y=H-99
 for li,e in enumerate(P['letra']):
  if li==6:new('Texto cantado: el regreso cambió de lado','Segunda parte de la letra original; el relato continúa después del solo D.');y=H-99
  text(42,y,f'c. {e["compas"]:02d}  {fmt(e["t"])}',9,True,color=ACC);text(159,y,e['funcion'].upper(),8,True);y=para(e['texto'],y-19,13,width=W-210,x=159,leading=17)-13
 new('Radio: el anuncio llegó antes que el vehículo','Dos locutores ficticios; la radio ya existente se conserva como instrumento. Sonda breve PSOLA, no locución definitiva.')
 y=H-103
 for e in P['radio']:
  text(42,y,f'c. {e["compas"]:02d}  {fmt(e["t"])}',9,True,color=ACC);text(159,y,e['voz'].upper(),9,True);y=para(e['texto'],y-21,12,width=W-205,x=159,leading=17)-24
 new('Instrumentos construidos y qué revisar ahora','Pruebas cortas, no canción producida. Las medidas no sustituyen tu escucha.')
 y=H-101
 items=[('Membrana cargada','Elementos finitos radiales; golpes abiertos, apagados y graves. Modelo inspirado en membranas cargadas, sin calibración de mridangam.'),('Láser de transbordos','Chirp sobremuestreado, Talbot existente y red de retardos. Tres lecturas del mismo motivo; cruces con error de ortogonalidad menor que 1e-12.'),('Raspador de depósitos','Contactos positivos sobre un perfil real antes/después de acumular material. Misma ganancia de comparación.'),('Boca y drone','Boca de tres tiempos y Cuerdas de estación fijados; la vocalización no necesita una voz humana como moduladora.'),('Radio y tráfico','Radio original con guía PSOLA y comparación de pulso fijo frente a ataques efectivos del reloj local.')]
 for title,desc in items:text(42,y,title,12,True);y=para(desc,y-21,10,leading=15)-15
 y=para('Referencias: David P. Nelson / Solkattu Manual (Wesleyan); Reich / Music for Pieces of Wood; Lachenmann / Guero; Nik Bärtsch / Continuum; Natural Information Society con Evan Parker / descension. Bando et al. / modelo de velocidad óptima. Fuentes y límites detallados en REFERENCIAS.md.',y,9,leading=13)
 para('Revisión solicitada: tema/estribillo, rareza y fraseo del láser, respiración del tráfico, presencia de cumbia y modos de la radio. La mezcla completa y la implementación final de Hydra esperan esta conversación. El video completo queda a cargo de Canek.',y-12,10,leading=15)
 c.save();print(path,'páginas',page)
 # Rasterización para revisar TODO el documento; no es render de video.
 import fitz
 doc=fitz.open(path);render=BASE/'render/pdf';render.mkdir(exist_ok=True)
 for i,p in enumerate(doc):
  pix=p.get_pixmap(matrix=fitz.Matrix(1.1,1.1));dest=render/f'pagina-{i+1:02d}.png'
  if dest.exists():raise FileExistsError(dest)
  pix.save(dest)
 # Una página real de la partitura es la siguiente captura cronológica del proceso.
 p=doc[1].get_pixmap(matrix=fitz.Matrix(1.5,1.5));guardar(out/'proceso'/f'08-tema-notado-en-partitura-s{SEED}-{tag}.png',p.tobytes('png'))
 jsave(out/'pdf-medidas.json',{'paginas':len(doc),'raster_revisar':str(render),'partitura_fuente':score().name,'eventos':sum(map(len,P['eventos'].values())),'instrumentos':30,'video_renderizado':False})
if __name__=='__main__':main()
