"""Partitura canónica: segundos, Hz, capas, filiación y controles. No audio."""
from pathlib import Path
import json,math,hashlib,shutil,io,csv
from collections import Counter
import numpy as np
from scipy.ndimage import map_coordinates
from PIL import Image,ImageDraw,ImageFont
from instrumentos import acuerdos,transporte,junco_gestos,comprobar

ROOT=Path(__file__).resolve().parent
OUT=ROOT/(ROOT/'ULTIMA.txt').read_text().strip();TAG=OUT.name.split('-')[-1]
SEED=2026102201;RNG=np.random.default_rng(SEED);Q=60/144;BAR=4*Q
C0=56*BAR;C1=C0+60;P1=C1+16*BAR;P2=P1+16*BAR;STOP=P2+24*BAR;DUR=STOP+12
def put(name,data):
 with (OUT/name).open('xb') as f:f.write(data)
def js(name,data):put(name,json.dumps(data,ensure_ascii=False,indent=1).encode('utf8'))
def png(name,im):
 b=io.BytesIO();im.save(b,format='PNG');put(name,b.getvalue())
def font(s,bold=False):return ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if bold else 'arial.ttf'),s)
def frame(title,sub):
 im=Image.new('RGB',(1600,1000),'#101713');d=ImageDraw.Draw(im);d.text((55,34),title,font=font(43,True),fill='#e9efc6');d.text((58,98),sub,font=font(22),fill='#b8c583');return im,d
def hz(m):return 440*2**((float(m)-69)/12)
def midi(f):return 69+12*math.log2(float(f)/440)

# Terreno original y ruta propia sobre su campo. No se inventa batimetría.
T=json.loads((OUT/'datos/terreno-s1.json').read_text('utf8'));G=T['G']
H=np.fromfile(OUT/'datos/alturas-s1.f32',np.float32).reshape(G,G).astype(float)
p0=np.array([T['nombres'][0]['u'],T['nombres'][0]['v']]);lake=np.array([T['hidro']['lagos'][0]['u'],T['hidro']['lagos'][0]['v']])
anchors=np.array([p0,[.38,.58],[.26,.68],lake+[.055,-.04],lake+[.04,.025],lake+[.006,.05],lake+[-.045,.016],lake+[-.025,-.04],lake+[.035,-.065],[.18,.70],[.32,.60],p0])
raw=np.concatenate([np.linspace(a,b,80,endpoint=False) for a,b in zip(anchors,anchors[1:])]+[anchors[-1:]])
sraw=np.r_[0,np.cumsum(np.linalg.norm(np.diff(raw,axis=0),axis=1))];s=np.linspace(0,sraw[-1],1201)
route=np.column_stack([np.interp(s,sraw,raw[:,k]) for k in range(2)])
z=T['base']+T['relieve']*map_coordinates(H,[route[:,1]*(G-1),route[:,0]*(G-1)],order=1,mode='nearest')
dist=s*T['anchoKm']*1000;ds=np.gradient(dist);slope=np.gradient(z)/np.maximum(ds,1e-9)
directions=np.unwrap(np.arctan2(np.gradient(route[:,1]),np.gradient(route[:,0])))
turn=np.r_[0,np.cumsum(np.abs(np.diff(directions)))];debt=np.minimum(100,turn*15)
# Tiempo del trayecto compuesto: ida, vuelta alrededor de la laguna y regreso.
distknots=[0,.33,.44,.66,.83,1];timeknots=[0,80,C0,C1,P1,STOP]
rt=np.interp(s/s[-1],distknots,timeknots)
route_data={'orientacion':'u crece al este, v al sur; origen noroeste','coordenadas':'normalizadas [0,1] del campo, sin rotación de la vista',
 'ancho_m':T['anchoKm']*1000,'tipo':'ruta compuesta sobre campo original; no camino real ni simulación de marcha',
 'semilla':1,'nombre':'El Teso del Tecolote / Pinahuizapan','anclas':anchors.tolist(),
 'distancia_m':float(dist[-1]),'ascenso_m':float(np.maximum(np.diff(z),0).sum()),'descenso_m':float(-np.minimum(np.diff(z),0).sum()),
 'salida_m':float(z[0]),'llegada_m':float(z[-1]),'min_m':float(z.min()),'max_m':float(z.max()),
 'muestras':[dict(t=float(t),u=float(p[0]),v=float(p[1]),z_m=float(zz),s_m=float(ss),pendiente=float(g),giro_abs_rad=float(a),deuda_cents=float(dc)) for t,p,zz,ss,g,a,dc in zip(rt,route,z,dist,slope,turn,debt)]}
js('datos/recorrido.json',route_data)
def terrain(t):
 return {k:float(np.interp(t,rt,v)) for k,v in [('altura_m',z),('pendiente',slope),('deuda_cents',debt),('u',route[:,0]),('v',route[:,1])]}

im,d=frame('02 / El recorrido deja una diferencia','Terreno original; ruta y reloj compuestos. Norte arriba. Semilla 1.')
mn,mx=float(H.min()),float(H.max());a=np.uint8(255*(H-mn)/(mx-mn));rel=Image.fromarray(a).resize((680,680));im.paste(rel,(55,180));d=ImageDraw.Draw(im)
pts=[(55+680*u,180+680*v) for u,v in route];d.line(pts,fill='#e2a86c',width=4)
d.ellipse((55+680*lake[0]-7,180+680*lake[1]-7,55+680*lake[0]+7,180+680*lake[1]+7),fill='#91d8ce')
for title,val,unit,yy in [('Distancia',dist[-1]/1000,'km',210),('Ascenso',route_data['ascenso_m'],'m',280),('Descenso',route_data['descenso_m'],'m',350),('Deuda final',debt[-1],'cents',420)]:d.text((800,yy),f'{title}: {val:.3f} {unit}',font=font(28),fill='#e8e8b9')
profile=[(800+720*k/(len(z)-1),770-220*(zz-z.min())/max(1,z.max()-z.min())) for k,zz in enumerate(z)];d.line(profile,fill='#b7da9c',width=3)
d.text((800,815),'El regreso cierra posición, no borra la memoria.',font=font(23),fill='#e8e8b9')
png(f'proceso/02-recorrido-y-deuda-s1-{TAG}.png',im)

specs=[
('guitarra','Guitarra de alambre / tres cajas','nueva:guitarra','rasgueo, roce y memoria',[-1,1]),
('pua','Guitarra cortada','rejilla-pixeles-guitarra-cortada','ataque sin altura asignable',[-.7,-.7]),
('krar','Krar','meleeviewer-3-krar','respuesta folk fragmentada',[.5,.5]),
('berimbau','Berimbau','berimbau','borde y tensión',[.6,.6]),
('arpa','Arpa que presta vibración','tres-tiempos:arpa','micelio; enlaces entre cuerdas',[-.6,.6]),
('cuerda','Cuerda de cuerpos incompatibles','tres-tiempos:cuerda','arco y presión independientes',[-.3,.3]),
('organo','Órgano de divisores con memoria','tres-tiempos:organo','persistencia por histéresis',[-.8,.8]),
('clarinete','Clarinete','objeto-clarinete','respuesta a la voz',[.35,.35]),
('chelo','Chelo','objeto-chelo','contracanto grave',[-.35,-.35]),
('contrabajo','Contrabajo','objeto-contrabajo','piso folk con silencios',[-.1,-.1]),
('bajo','Bajo de dedos','rejilla-pixeles-bajo-dedos','riff y sus omisiones',[0,0]),
('androide','Bajo de androide','tres-tiempos:androide','solo no humano; retícula a serie',[.1,.1]),
('terminal','Terminal vectorial','tres-tiempos:terminal','respuesta al bajo y salto de cuerpo',[-.1,.1]),
('piano','Piano con papel','objeto-piano-papel','ruido ligado a ataques',[-.45,-.45]),
('mbira','Mbira','mbira','memoria de la figura',[.45,.45]),
('arpaboca','Arpa de boca','arpaboca','vocal del rasgueo',[.2,.2]),
('campana','Campana p-ádica','campana-padica:motor','vecindades en resonancia',[-.7,.7]),
('waterphone','Waterphone','objeto-waterphone','armónicos aislados y relevo',[-.55,-.55]),
('gong','Gong de dos alturas','objeto-gong-dos-alturas','bisagra de sección',[.6,.6]),
('bombo','Bombo acústico','bateria-acustico:kick','frase grave',[0,0]),
('caja','Caja acústica','bateria-acustico:snare','contragolpe y huecos',[-.1,-.1]),
('hat','Charles','bateria-acustico:hat','articulación corta',[.35,.35]),
('tom','Tom de piso','bateria-acustico:tom','respuesta a cada cuarto gesto',[-.4,-.4]),
('aro','Aro frito','bateria-frito:rim','contradicción de la caja',[.4,.4]),
('ride','Plato y borde','bateria-acustico:ride','expansión sólo al final',[.5,.5]),
('fotones','Batería de fotones','tres-tiempos:fotones','remates en alturas',[-.6,.6]),
('junco1','Junco I / raíz','nueva:junco','trayectoria de masa 1',[-.8,-.8]),
('junco2','Junco II / barro','nueva:junco','trayectoria de masa 2',[-.25,-.25]),
('junco3','Junco III / mosco','nueva:junco','trayectoria de masa 3',[.25,.25]),
('junco4','Junco IV / luz','nueva:junco','trayectoria de masa 4',[.8,.8]),
('voz','Voz principal','difonos:Sabina','prosodia; se retira en el centro',[0,0]),
('duo','Otra persona','difonos:Sabina-registro-grave','contesta, no dobla todo',[-.15,-.15]),
('corocuerda','Vocoder de cuerda','vocoder:guia-a-cuerda','la cuerda recoge palabras',[-.45,-.45]),
('corojunco','Vocoder de junco','vocoder:guia-a-junco','coro hecho con el destino',[.45,.45]),
('boca','Boca de tres tiempos','tres-tiempos:boca','sílabas parciales independientes',[.15,.15]),
('sala','Sala plegada tocada','tres-tiempos:sala','golpes propios, no bus contado',[-.8,.8])]
TRACKS=[dict(id=k,nombre=n,motor=mo,funcion=fun,pan=p[0],salidas=p,numero=i+1) for i,(k,n,mo,fun,p) in enumerate(specs)]
EV={k:[] for k,*_ in specs};N=0
def sec(t):
 for s in SECTIONS:
  if s['t']<=t<s['fin'] or abs(t-DUR)<1e-8:return s['id']
 return 'fuera'
SECTIONS=[
 dict(id='I',nombre='La lata y la raíz',t=0,fin=16*BAR,modo='4/4',accion='riff seco; pregunta y respuesta; olor a metal y agua quieta'),
 dict(id='II',nombre='Cabezas / mosquitos',t=16*BAR,fin=32*BAR,modo='4/4',accion='verso; el clarinete hereda una pausa'),
 dict(id='III',nombre='Llevemos',t=32*BAR,fin=48*BAR,modo='4/4',accion='coro; tres promesas de afinación'),
 dict(id='IV',nombre='La cuerda se pega',t=48*BAR,fin=C0,modo='4/4 roto',accion='se pierde el último ataque; 35 ms de corte antes del centro'),
 dict(id='V',nombre='Pantano / nadie dirige',t=C0,fin=C1,modo='senza misura, segundos',accion='60 s; seis oscuridades; armónicos, roce, madera; sin solista humano'),
 dict(id='VI',nombre='Carbono / cuatro orillas',t=C1,fin=P1,modo='4/4 con relojes propios',accion='polifonía; solos y transporte del acorde recordado'),
 dict(id='VII',nombre='La respuesta cambia de boca',t=P1,fin=P2,modo='4/4',accion='coro heredado por cuerdas y juncos; final de frase modificado'),
 dict(id='VIII',nombre='Casi una pared',t=P2,fin=STOP,modo='4/4',accion='tres olas distintas de densidad; agujeros comunes; la voz cabe'),
 dict(id='IX',nombre='Dos cosas que todavía caen',t=STOP,fin=DUR,modo='senza misura, segundos',accion='corte de banda; dos resonancias y silencio final')]
def note(k,t,m,d=.2,v=.65,art='ordinario',anc=None,phrase='',**kw):
 global N
 if t<0 or t>=DUR:return None
 d=min(float(d),DUR-t)
 if d<=0:return None
 N+=1;ter=terrain(t)
 e=dict(id=f'e{N:05}',t=round(float(t),8),dur=round(d,8),midi=round(float(m),9),hz=round(hz(m),8),vel=round(float(v),5),
  pan=next(x['pan'] for x in TRACKS if x['id']==k),articulacion=art,seccion=sec(t),frase=phrase,ancestro=anc,**kw)
 # Mapeo explícito: presión del instrumento y articulación consumen pendiente.
 e['terreno']={x:round(y,8) for x,y in ter.items()}
 EV[k].append(e);return e

QUESTION=[(0,64,.70),(1.5,59,.35),(2,60,1.20),(4.25,65,.40),(5.5,64,1.50)]
ANSWER=[(0,67,.6),(1,65,.5),(2.5,62,1),(4,60,.75),(5.25,59,.4),(6,64,1.2)]
seed_events=[]
for i,(b,m,dur) in enumerate(QUESTION):
 e=note('guitarra',b*Q,m,dur*Q,.82 if i in [0,3] else .57,'pua',phrase='Q0',cuerda=[4,3,2,5,4][i],caja=0,nodo=.17,parcial=1)
 seed_events.append(e['id'])
def transform(m,t,voice=0):
 # Desde el centro, desplazamientos del ciclo y paso a parciales de E2.
 if t<C0:return m
 a=acuerdos(terrain(t)['deuda_cents'],[1,2,1])['cents'][voice%3]/100
 target=midi(hz(40)*round(hz(m)/hz(40)))
 w=min(1,max(0,(t-C1)/(P2-C1)))
 return (1-w)*m+w*target+a
def motif(k,t0,pattern=QUESTION,shift=0,stretch=1,mode='tema',end=None,voice=0):
 for j,(b,m,d) in enumerate(pattern):
  t=t0+b*Q*stretch
  if end is not None and t>=end:continue
  length=d*Q*stretch
  if end is not None:length=min(length,end-t)
  note(k,t,transform(m+shift,t,voice),length,.64 if j else .81,mode,seed_events[j%5],mode,
       **({'cuerda':j%6,'caja':voice%3,'nodo':.17,'parcial':1} if k=='guitarra' else {}))

# Rasgueo punk folk; voces de acorde explícitas, huecos que se transmiten.
CHORDS=[[40,47,52,59],[40,48,53,60],[43,50,55,62],[40,47,53,59]]
metric_bars=[(b,b*BAR) for b in range(56)]+[(56+j,C1+j*BAR) for j in range(56)]
for b,t0 in metric_bars:
 progress=(t0/STOP);ch=CHORDS[(b//2)%4]
 # Ataque inicial se presenta antes de añadir las cuerdas intermedias.
 hits=[0,1,2,2.75,3.5] if b%4!=3 else [0,.75,2,3.25]
 if 48<=b<56:hits=hits[:max(1,5-(b-48)//2)]
 if b>=104:hits=[0,.5,1.5,2,2.75,3.5] if b%2==0 else [0,1.25,2.5,3.25]
 for j,beat in enumerate(hits):
  t=t0+beat*Q
  if t+Q*.42>=C0 and t<C0:continue
  for vi,m in enumerate(ch):
   if b<4 and vi not in [0,2]:continue
   if b>=56 and vi==0 and b%4==0:continue # hueco heredado en el regreso
   note('guitarra',t+vi*.0027,transform(m,t,vi),Q*(.50 if b<56 else 1.1),.34+(j==0)*.16,'rasgueo',seed_events[vi%5],f'rasgueo-{b//4}',cuerda=vi,caja=vi%3,nodo=.12+.03*vi,parcial=1,presion=float(np.clip(.3+abs(terrain(t)['pendiente'])*6,0,1)),humedad=.18+.6*min(1,t/C0))
  if b%2==0:note('pua',t,60,.065,.42,'pua apagada',seed_events[j%5],f'grano-{b//2}',altura_asignable=False)
 # Percusión con pregunta/contestación y mutaciones de remates.
 kick=[0,1.75,2.5] if b%4<2 else [0,.75,2.75]
 sn=[1,3] if b%4!=3 else [1,2.75,3.5]
 if b in [55,56,72,88,104]:kick=kick[1:];sn=sn[:1]
 for beat in kick:note('bombo',t0+beat*Q,36,.13,.82,'centro',phrase=f'grave-{b%4}',pieza='kick',altura_asignable=False)
 for beat in sn:note('caja',t0+beat*Q,38,.105,.78 if beat==3 else .64,'parche y bordón',phrase=f'respuesta-{b%4}',pieza='snare',altura_asignable=False)
 if b>=8:
  for j in range(8):
   if (j+b)%7==0:continue
   note('hat',t0+j*Q/2,42,.045,.23+.13*(j%3==0),'cerrado',phrase=f'aire-{b%5}',pieza='hat',altura_asignable=False)
 if b%4==3:
  for j in range(3):note('tom',t0+(2.2+j*.57)*Q,43,.15,.65-j*.1,'borde descendente',phrase='remate 3',pieza='tom',altura_asignable=False)
 if b>=16 and b%3==1:
  for j in [1.25,3.75]:note('aro',t0+j*Q,37,.06,.45,'aro',phrase='contra caja',pieza='rim',altura_asignable=False)
 if b>=88:
  for j in [0,1.5,3.25]:note('ride',t0+j*Q,51,.6,.34,'borde sin crash continuo',phrase='ola de pared',pieza='ride',altura_asignable=False)
 # Dos bajos con funciones separadas.
 if b<32 or b>=72:
  for j,beat in enumerate([0,1.5,2.75]):
   if b>=72 and b%4==0 and j==0:continue
   note('bajo',t0+beat*Q,transform([40,47,43][j],t0),Q*.85,.7,'dedo corto',seed_events[j],'riff con deuda')
 if b in range(8,48) and b%2==0:
  note('contrabajo',t0+.25*Q,40 if b%4==0 else 35,2.5*Q,.65,'pizzicato',seed_events[0],'andar separado')
 if 4<=b<48 and b%4 in [1,3]:motif('krar',t0+.5*Q,ANSWER,-12,.75,'respuesta recortada',t0+BAR)
 if b%4 in [0,2] and b>=12:motif('berimbau',t0+.25*Q,QUESTION,-24,.42,'tensión / huecos',t0+BAR)
 if b%8==6:motif('piano',t0,ANSWER,-12,.45,'papel contra pua',t0+BAR)
 if b%8==7 and b>=16:note('gong',t0+3.5*Q,52,2*Q,.28,'borde',seed_events[3],'bisagra')

# Tema reconocible y contrapunto antes de la disolución.
for b in [4,12,20,28,36,44]:motif('guitarra',b*BAR,QUESTION,0,1,'Q presentada')
for b in [6,14,22,30,38,46]:motif('clarinete',b*BAR,ANSWER,0,1,'R responde al hueco')
for b in range(20,48,4):motif('chelo',b*BAR+.75*Q,QUESTION,-24,1.25,'contracanto oblicuo',min(C0,(b+4)*BAR),1)
for b in range(24,48,4):motif('arpaboca',b*BAR+.33*Q,QUESTION,-12,.63,'vocal del rasgueo',(b+3)*BAR)
for b in [28,40]:motif('mbira',b*BAR+2*Q,ANSWER,12,.8,'recuerdo con huecos',(b+4)*BAR)

# Relojes primos integrados sobre tiempo absoluto: nunca se reinician por compás.
CLOCKS=[]
for idx,(k,period) in enumerate([('arpa',17),('mbira',19),('boca',23),('fotones',29)]):
 dt=.01;grid=np.arange(0,DUR+dt,dt);gg=np.array([terrain(t)['pendiente'] for t in grid]);speed=(4/Q)/period*(1+np.clip(gg*2,-.12,.12))
 phase=np.r_[0,np.cumsum((speed[:-1]+speed[1:])*.5*dt)];last=-1;count=0
 for j in np.flatnonzero(np.floor(phase[1:])>np.floor(phase[:-1]))+1:
  t=float(grid[j]);enabled=(20<t<80) or (C1<=t<STOP)
  if not enabled:continue
  count+=1;cyc=int(phase[j]);pat=QUESTION if idx%2==0 else ANSWER;m=pat[cyc%len(pat)][1]
  if k=='fotones':m+=12
  note(k,t,transform(m,t,idx),.11 if k=='fotones' else .48,.36 if t<C0 else .53,'reloj propio',seed_events[cyc%5],f'primo-{period}',fase_acumulada=float(phase[j]),periodo_subdivisiones=period,cuerda=cyc%5)
 CLOCKS.append(dict(capa=k,periodo=period,fase_a_inicio_centro=float(np.interp(C0,grid,phase)),fase_a_fin_centro=float(np.interp(C1,grid,phase)),eventos=count,metodo='integración trapezoidal dt=.01 s, no reinicio; fase no implica señal audible'))

# Texto propio nuevo y fragmentos originales identificados; una sílaba por nota.
LINES=[
 ('la lata','hay u na la ta en el a gua',8,'nuevo', 'Hay una lata en el agua'),
 ('la raíz','u na ra íz sa le por la bo ca',12,'nuevo','una raíz sale por la boca'),
 ('el cuerpo','tra es lo do en los te nis',16,'nuevo','traes lodo en los tenis'),
 ('el mosco','y e se mos qui to nos a ta ca',20,'adaptado del poema','y ese mosquito nos ataca'),
 ('choque','nues tras ca be zas cho can',24,'fragmento literal','nuestras cabezas chocan'),
 ('acuerdo','de ci mos sí al mis mo tiem po',28,'fragmento literal','decimos sí al mismo tiempo'),
 ('coro1','lle ve mos u nas lu ciér na gas al la go',32,'verso literal','llevemos unas luciérnagas al lago'),
 ('espera','a es pe rar a que cai ga la no che',36,'verso literal','a esperar a que caiga la noche'),
 ('posibilidad','es po si ble que el a mor e xis ta',40,'verso literal','es posible que el amor exista'),
 ('otras','en o tras for mas de ex pe rien cia',44,'verso literal','en otras formas de experiencia')]
LYRICS=[]
def sing(k,text,t,length,phrase,source,plain,variant=0,parent=None):
 syll=text.split();weights=np.array([1.6 if any(a in sy for a in ['á','é','í','ó','ú']) else 1 for sy in syll],float);weights[-1]=2.2
 weights=weights/weights.sum()*length;tt=t
 melody=[64,64,59,60,65,64,62,60,59,64,67,65] if not variant else [64,67,65,62,60,59,64,65,67,64,62,64]
 for j,(sy,dd) in enumerate(zip(syll,weights)):
  m=melody[j%len(melody)]+(-12 if k=='duo' else 0)
  if t>=C1:m=transform(m,tt,variant)
  if variant and j==len(syll)-1:m=transform(65,tt,1) # residuo F en el regreso
  note(k,tt,m,dd*.86,.72 if k=='voz' else .5,'silábico',parent or seed_events[j%5],phrase,texto=sy,silaba=j+1,silabas_total=len(syll),origen_texto=source)
  tt+=dd
 LYRICS.append(dict(t=t,fin=tt,capa=k,texto=plain,silabas=text,frase=phrase,procedencia=source,variant=variant))
for title,sy,b,src,plain in LINES:sing('voz',sy,b*BAR,3.4*BAR,title,src,plain)
for b,sy,plain in [(23,'ya lo vi','ya lo vi'),(31,'al mis mo tiem po','al mismo tiempo')]:sing('duo',sy,b*BAR,.8*BAR,'otra persona','nuevo',plain)

# Centro: gestos irregularmente escritos y seis zonas sin acontecimiento/salida.
DARK=[(C0+5.7,C0+8.2),(C0+15.4,C0+18.4),(C0+25.7,C0+29.3),(C0+36.4,C0+39.8),(C0+46.2,C0+49.7),(C0+56.2,C1)]
GEST=[(.63,'guitarra',64,.31,'roce',1),(2.17,'waterphone',88,.9,'armónico aislado',3),(4.36,'guitarra',64,.38,'armonico',5),
 (8.61,'cuerda',76,1.35,'arco sin altura estable',3),(11.14,'junco2',83,.72,'borde de aire',5),(13.91,'guitarra',59,.41,'madera',1),
 (18.83,'campana',88,1.1,'familia lejana',7),(21.37,'guitarra',64,.58,'armonico',7),(24.31,'waterphone',95,.7,'rozar y retirar',5),
 (29.72,'cuerda',65,1.24,'presión apenas suficiente',2),(32.46,'junco3',91,.84,'contesta al roce',7),(35.03,'guitarra',64,.62,'apagar',1),
 (40.11,'guitarra',64,.36,'roce',1),(42.53,'junco1',76,.64,'armónico que toma el hueco',3),(44.97,'waterphone',88,.55,'sin vibrato periódico',5),
 (50.04,'campana',100,.72,'distancia cambia tras golpe',7),(52.77,'guitarra',64,.54,'armonico',5),(55.13,'junco4',95,.56,'última pregunta',7)]
for j,(off,k,m,dd,art,h) in enumerate(GEST):
 t=C0+off
 fundamental=transform(m,t,j);sounding=fundamental+12*math.log2(h) if k=='guitarra' and art=='armonico' else fundamental
 note(k,t,sounding,dd,.15+.04*(j%3),art,seed_events[j%5],f'libre-{j+1}',libre=True,cuerda=j%6,caja=j%3,nodo=1/h if h>1 else .17,parcial=h,release_s=.03,fundamental_midi=fundamental,altura_asignable=art not in ['madera','roce','apagar','arco sin altura estable'])

# Regreso y carbono: tema por filiación; los instrumentos tienen controles propios.
for b,t0 in metric_bars:
 if b<56:continue
 j=b-56
 if j%4==0:motif('arpa',t0,QUESTION,0,1.05,'Q en micelio',t0+4*BAR,j%3)
 if j%4==2:motif('clarinete',t0+.25*Q,ANSWER,0,.9,'R después de escuchar',t0+3*BAR,1)
 if j%8==1:motif('chelo',t0,ANSWER,-24,1.6,'contrapunto lento',t0+5*BAR,2)
 if j%4==0:note('cuerda',t0,transform(52,t0,1),3.6*BAR,.58,'arco vivo',seed_events[2],'cuerpo incompatible')
 if j%8==0:note('organo',t0,88,7.7*BAR,.45,'sostener memoria',seed_events[0],'presión no reiniciada',ataque=.4)
 if j%4==1:note('sala',t0+.73*Q,transform(64,t0),.17,.4,'golpe que pliega',seed_events[3],'objeto / cavidad')
 if j%8==3:motif('berimbau',t0,ANSWER,-24,.73,'otra orilla',t0+3*BAR)
 if j%8==7:motif('piano',t0,QUESTION,-12,.52,'papel aprende',t0+2*BAR)
 if j%8==6:note('campana',t0+.17,88,2*BAR,.28,'parentesco',seed_events[4],'captación lateral')

# Solos A/B/C/D posibles: se escribe D, intercambio real de material y ruta.
for n,(t0,k) in enumerate([(C1,'terminal'),(C1+8*BAR,'androide')]):
 t=t0;i=0;end=t0+8*BAR
 rhythm=[1,1,2,3,1,5,2,1,4,3] # dieciseisavos, no patrón fijo bajo todo el solo
 while t<end-.1:
  dd=min(rhythm[i%len(rhythm)]*Q/4,end-t)
  hs=[8,9,10,12,14,15,16,21,11][(i*2+i//5)%9]
  m=midi(hz(40)*hs/(4 if k=='androide' else 1))+acuerdos(terrain(t)['deuda_cents'],[1,2,1])['cents'][n]/100
  note(k,t,m,dd*.83,.7,'solo D',seed_events[i%5],f'solo-D-{k}',parcial=hs,memoria_de='Q0',vector_x=min(1,(t-C1)/(16*BAR)),vector_y=float(np.clip(abs(terrain(t)['pendiente'])*10,0,1)))
  if i%4==2:note('fotones',t+dd*.24,m+12,min(.11,dd*.3),.32,'responde al solo',phrase='remate no constante')
  t+=dd;i+=1

# Transporte: las cuatro fuentes son parciales de la frase, enseñados antes.
PLANS=[]
for k,t0 in enumerate(np.arange(C1,STOP-2,2*BAR)):
 source=[64+12*math.log2(h) for h in [1,2,3,5]]
 shifts=acuerdos(terrain(t0)['deuda_cents'],[1,2,1])['cents']
 dest=[transform(m,t0,j) for j,m in enumerate([76,79,83,88])]
 a=np.array([.4,.25,.2,.15]);b=np.roll(a,k%4)
 plan=transporte(source,dest,a,b,.7 if k%3==0 else 0)
 ancestors=[seed_events[0]]*4;gests=junco_gestos(plan,source,dest,float(t0),2*BAR*.93,ancestors)
 pid=f'plan-{k+1:02}';PLANS.append(dict(id=pid,t=float(t0),source=source,parciales_fuente=[1,2,3,5],ancestro=seed_events[0],target=dest,a=a.tolist(),b=b.tolist(),**plan))
 for gg in gests:
  ix=gg['voz'];m=gg.pop('midi');tt=gg.pop('t');dd=gg.pop('dur');ancestor=gg.pop('ancestro');gg.pop('voz')
  note('junco'+str(ix+1),tt,m,dd,.36 if t0<P2 else .53,'transporte continuo',ancestor,pid,plan=pid,**gg)

# Cuatro cuerdas del micelio transfieren envolventes; el órgano guarda estado.
LINKS=[]
for i,t in enumerate(np.arange(C1+Q,STOP-1,2*BAR)):
 LINKS.append([float(t),i%5,(i+2)%5,1.1 if i%2 else -.85])
PRESSURE=[[0,.15],[70,.82],[C0-.06,.93],[C0,.47],[C1,.47],[P1,.26],[P2,.74],[STOP,.47],[DUR,.47]]
CONTROLS={
 'arpa':{'cuerdas_midi':[64,67,71,74,76],'enlaces':LINKS},
 'cuerda':{'base_midi':52,'controles':{'presion':[[0,.1],[C0,.12],[C1,.82],[P1,.45],[P2,.93],[STOP,0]],'arco':[[0,0],[C0,0],[C1,.7],[P1,.22],[P2,.83],[STOP,0]]}},
 'organo':{'controles':{'presion':PRESSURE},'estado':'Schmitt continúa durante mute; el gate de nota no borra histéresis'},
 'sala':{'controles':{'pliegue_0':[[0,.1],[C1,.8],[P1,.2],[STOP,.95]],'pliegue_1':[[0,.7],[C1,.2],[P2,.9],[STOP,.3]]}},
 'boca':{'vocales':[[0,'a'],[C0,'u'],[C1,'i'],[P1,'a'],[STOP,'u']],'consonantes':[[C1+.17,'k',.4],[P1+.38,'s',.4]]},
 'guitarra':{'deuda':'datos/recorrido.json → deuda_cents → acuerdos.cents → afinación de las tres cajas','presion':'abs(pendiente)*6+.3, limitada [0,1]','humedad':'control compuesto .18→.78; no humedad medida','estado':'6x3x8 envolventes y fases; sin reinicio en cambios de sección'},
 'junco':{'planes':'datos/transportes.json','fase':'integrar frecuencia de cada trayectoria; no asignar fase nueva al cambiar de columna','masa':'masa abstracta normalizada; no energía acústica conservada de mezcla'},
 'campana':{'eventos':[{'t':C0+18.83,'hit':9,'vel':.24},{'t':C0+19.1,'params':{'fold':1}},{'t':C0+50.04,'hit':1,'vel':.24},{'t':C0+50.3,'params':{'pickup':3}}]},
 'terminal':{'controles':{'vector_x':[[C1,0],[P1,1]],'vector_y':[[C1,.15],[C1+8*BAR,.93],[P1,.3]]}},
 'androide':{'controles':{'desgarro':[[C1,.1],[C1+8*BAR,.8],[P1,.35],[STOP,.7]]}}}

# Coro transformado: una voz humana en VII; VIII pertenece en parte a los cuerpos.
for i,(_,sy,_,src,plain) in enumerate(LINES[6:]):
 sing('voz',sy,P1+i*4*BAR,3.5*BAR,f'coro-regreso-{i}',src,plain,1)
 sing('corocuerda',sy,P2+i*4*BAR+.13,3.1*BAR,f'coro-cuerda-{i}',src,plain,1)
 if i in [1,3]:sing('corojunco',sy,P2+i*4*BAR+1.2*Q,3.0*BAR,f'coro-junco-{i}',src,plain,1)
sing('duo','a pa ga el te lé fo no',P2+17*BAR,2*BAR,'apagar teléfono','nuevo','apaga el teléfono',1)
sing('voz','sí al mis mo tiem po',P2+20*BAR,2.7*BAR,'última respuesta','adaptación de verso','sí al mismo tiempo',1)

# Agujeros compartidos en la pared, no sólo bajar bombo. Limitar/suprimir eventos.
HOLES=[(P2+7*BAR+2.7*Q,P2+8*BAR),(P2+15*BAR+1.8*Q,P2+16*BAR),(P2+22*BAR+2*Q,P2+22*BAR+3.1*Q)]
MUTES=[(C0-.035,C0+.3),(STOP-.035,STOP+.02)]+DARK+HOLES
def clip_event(e,holes):
 start=e['t'];end=start+e['dur'];ranges=[(start,end)]
 for a,b in holes:
  new=[]
  for x,y in ranges:
   if y<=a or x>=b:new.append((x,y))
   else:
    if x<a:new.append((x,a))
    if y>b:new.append((b,y))
  ranges=new
 return [(a,b) for a,b in ranges if b-a>.012]
for layer,es in EV.items():
 result=[]
 for e in es:
  if C0<=e['t']<C1 and not e.get('libre'):continue
  rs=clip_event(e,MUTES)
  for j,(a,b) in enumerate(rs):
   ee=dict(e,t=round(a,8),dur=round(b-a,8))
   if len(rs)>1:ee.update(id=e['id']+f'.{j}',continuacion_de=e['id'],reataque=False)
   result.append(ee)
 EV[layer]=sorted(result,key=lambda e:(e['t'],e['id']))
# Coda: dos ataques heredados y sus caídas distintas; nada tras DUR-2.
note('junco4',STOP+.21,transform(88,STOP,2),4.3,.16,'residuo de luz',seed_events[3],'coda',fase_continua=True)
note('waterphone',STOP+1.37,transform(95,STOP,1),6.1,.12,'residuo de barro',seed_events[4],'coda')

# Pautas métrica/free: MusicXML usa celdas editoriales claramente identificadas.
MEAS=[]
for b in range(56):MEAS.append(dict(n=len(MEAS)+1,t=b*BAR,fin=(b+1)*BAR,free=False,beats=4))
for j in range(10):MEAS.append(dict(n=len(MEAS)+1,t=C0+6*j,fin=C0+6*(j+1),free=True,beats=14.4))
for j in range(56):MEAS.append(dict(n=len(MEAS)+1,t=C1+j*BAR,fin=C1+(j+1)*BAR,free=False,beats=4))
for j in range(3):MEAS.append(dict(n=len(MEAS)+1,t=STOP+4*j,fin=STOP+4*(j+1),free=True,beats=9.6))
P=dict(titulo='Llevemos unas luciérnagas al lago',autor='Canek Zapata',fecha='2026-10-22',version='partitura-1.0',semilla=SEED,semilla_terreno=1,
 duracion=DUR,bpm_referencia=144,negra_s=Q,centro=[C0,C1],corte_banda=STOP,parada='Sólo partitura e instrumentos; producción y másters después',
 secciones=SECTIONS,partes=TRACKS,eventos=EV,tema_Q=QUESTION,tema_R=ANSWER,fuentes_tema=seed_events,
 oscuridades=DARK,agujeros_pared=HOLES,cortes_buses=[dict(t=a,fin=b,accion='cerrar salida, cola limitada, reabrir sin reataque',destino='todos los buses, sin delay ni click',rampa_s=.012) for a,b in MUTES],
 controles=CONTROLS,relojes=CLOCKS,medidas_editoriales=MEAS,letra=LYRICS,
 reglas={'no_humano':'relojes 17/19/23/29 integrados, afinación continua, transferencias de cinco cuerdas, transporte de cuatro distribuciones, tres acuerdos incompatibles; no implica IA o conciencia',
 'fase':'no reiniciar por compás; cierre de salida no borra envolvente ni histéresis; al reabrir se verifica señal sin chasquido',
 'afinacion':'Hz y MIDI fraccional canónicos; MusicXML a 12000 divisiones/negra; no redondear a MIDI entero',
 'centro':'segundos libres sin metrónomo ni ostinato periódico; relojes internos no se oyen',
 'capas':'36 partes con eventos propios; cuatro juncos son cuatro voces del mismo instrumento; seis partes de batería son componentes; buses no cuentan',
 'adaptaciones':'letra original nueva identificada y versos del corpus con procedencia; vocoder necesita guía de sílabas, no copiar mezcla anterior'})
js('partitura-v1.json',P);js('datos/transportes.json',PLANS);js('datos/controles.json',CONTROLS);js('datos/sondas-instrumentos.json',comprobar())
im,d=frame('03 / Primera escritura de 36 partes','Cada trazo es un acontecimiento real del JSON; aún no hay sonido.')
x0,x1=330,1545;y0=175;row=19
for a,b in DARK:d.rectangle((x0+(x1-x0)*a/DUR,y0-12,x0+(x1-x0)*b/DUR,y0+36*row),fill='#24332d')
for j,tr in enumerate(TRACKS):
 y=y0+j*row;d.text((35,y-7),f'{j+1:02} {tr["nombre"][:31]}',font=font(15),fill='#cdd9b1')
 for e in EV[tr['id']]:
  x=x0+(x1-x0)*e['t']/DUR;xx=x0+(x1-x0)*(e['t']+e['dur'])/DUR
  d.line((x,y,max(x+1,xx),y),fill='#dba574' if e.get('libre') else '#a3d9c7',width=2)
for s in SECTIONS:
 x=x0+(x1-x0)*s['t']/DUR;d.line((x,y0-25,x,y0+36*row),fill='#65705b');d.text((x+2,y0-43),s['id'],font=font(17,True),fill='#eff5d0')
d.text((45,925),f'{sum(map(len,EV.values()))} eventos / 4:18.667 / centro de 60 s / seis oscuridades / tiempo absoluto en segundos',font=font(24),fill='#e9efc6')
png(f'proceso/03-borrador-de-eventos-s1-{TAG}.png',im)
put('fuentes/componer.py',Path(__file__).read_bytes());put('fuentes/instrumentos-vigentes.py',(ROOT/'instrumentos.py').read_bytes())
print(json.dumps({'out':str(OUT),'duracion':DUR,'eventos':sum(map(len,EV.values())),'partes':len(TRACKS),'ruta':{k:v for k,v in route_data.items() if k in ['distancia_m','ascenso_m','descenso_m','salida_m','llegada_m']},'capas_vacias':[k for k,v in EV.items() if not v]},ensure_ascii=False))
