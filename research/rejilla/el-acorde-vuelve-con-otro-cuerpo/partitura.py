"""Tema de piano, motor recto, cruce de registros y retorno de una coma."""
from comun import *
from laminas import *
def componer():
 names=['ep-tema','ep-comping','ep-sombra','piano-goma','vibrafono','kick','caja','ride','hats','rim','maquina808','contrabajo','bajo-electrico','pedal110','chelo','fuelle-alto','fuelle-bajo','flauta','farfisa','resonador-A','resonador-coma','batidos','pulsos-batido','radio-izq','radio-der','telar','voz','voz-doble','voz-fuelle','fragmento']
 sections=[('I','Una habitación para el piano',0,8,'piano'),('II','El acorde aprende a caminar',8,24,'piano y voz'),('III','El motor toma una frase',24,40,'piano y señales'),('IV','Cruzar el fuelle y la cuerda',40,52,'fuelle y chelo'),('V','Volver por otra afinación',52,64,'piano bifronte'),('VI','El mismo tema, otro cuerpo',64,76,'piano'),('VII','Lo que retienen las paredes',76,80,'resonadores')]
 P={'titulo':'El acorde vuelve con otro cuerpo','semilla':SEED,'sr':SR,'instrumentos':lib().name,'bpm':60/Q,'negra':Q,'compas':BAR,'duracion':80*BAR+5,'coma_cents':float(CENTS),'coma_ratio':COMA,'frecuencias_retorno':[110,111.375],'secciones':[{'id':i,'nombre':n,'t':a*BAR,'t1':b*BAR,'compases':[a,b],'protagonista':who} for i,n,a,b,who in sections],'eventos':{c:[] for c in names},'sabina':[],'letra':[],'solista_ventanas':[[12*BAR,16*BAR],[20*BAR,24*BAR],[68*BAR,72*BAR]],'solo_D':[],'sujeto':{'midi':[64,59,61,57,54],'tiempos_negras':[0,.75,1.5,2.75,4.5],'duraciones_negras':[.55,.6,1,.9,1.7]},'regla_relevos':'El solista tiene tres frases; los solos IV/V y la coda VII no contienen eventos humanos. El piano es protagonista y el campo de resonadores toma el cierre.'}
 ev=P['eventos'];rng=np.random.default_rng(SEED)
 def add(c,t,m=60,d=.3,v=.7,p=0,**kw):ev[c].append({'t':round(float(t),6),'midi':float(m),'dur':float(d),'vel':float(v),'pan':float(p),**kw})
 def cents(b):return float(CENTS) if b>=64 else 0.
 chords=[[56,59,61,64],[57,61,64,68],[57,61,62,66],[56,62,66,73]];roots=[33,30,35,28]
 # Un sujeto identificable con silencios, anticipaciones y tres transformaciones.
 for b in [0,4,8,16,24,28,32,36,64,72,76]:
  notes=P['sujeto']['midi'][:]
  if b==16:notes=[64,61,59,57,54]
  if b==28:notes=[64,66,61,59,57]
  if b==36:notes=[64,59,61,66,64]
  if b>=64:notes=[64,59,61,56,57] # conserva la resolución descubierta en el solo
  stretch=1.5 if b==76 else 1
  for j,(m,at,d) in enumerate(zip(notes,P['sujeto']['tiempos_negras'],P['sujeto']['duraciones_negras'])):
   add('ep-tema',b*BAR+at*Q*stretch,m+cents(b)/100,d*Q*stretch,.73 if j in [0,3] else .55,p=-.08,frase='regreso' if b>=64 else 'sujeto')
   if b in [4,16,28,36,72]:add('flauta',b*BAR+at*Q+Q*.5,m+12+cents(b)/100,d*Q*.65,.45,p=.25)
 # Episodios de piano: secuencia, aumentación, mano izquierda y pregunta/respuesta.
 for b in [10,18,26,30,34,38,66,74]:
  for j,g in enumerate([0,4,7,11,9,7,2,0]):
   c='ep-tema' if j%2==0 else 'piano-goma';t=b*BAR+(.25+j*.65)*Q
   add(c,t,57+g+cents(b)/100,Q*(.42 if j<6 else .8),.6,p=-.12 if c=='ep-tema' else .2)
 # Comping de voicings abiertos: el bajo tiene la fundamental.
 for b in list(range(2,40,2))+list(range(64,76,2)):
  chord=chords[b//2%4];offset=cents(b)/100
  for beat in [.35,3.5,6.25]:
   for j,m in enumerate(chord):add('ep-comping',b*BAR+beat*Q+j*.009,m+offset,Q*(1.4 if beat!=3.5 else .8),.37+j*.025,p=-.22)
  if b%4==2:
   for j,m in enumerate(chord[::2]):add('vibrafono',(b+1)*BAR+(j+.2)*Q,m+12+offset,Q*1.7,.4,p=.3)
 # Dos caras independientes: la sombra recuerda el La inicial después del viaje.
 for b in [6,14,22,34,40,48,52,58,62,66,70,74,78]:
  for m in [45,52,59]:add('ep-sombra',b*BAR,m,BAR*1.6,.37,p=.3,cara='memoria110')
 # Groove de hip-hop: pareja de corcheas .57/.43, caja retrasada y fantasmas.
 for b in list(range(8,40))+list(range(64,76)):
  for beat in ([0,1.65,2.75] if b%2 else [0,1.5,3.25]):add('kick',b*BAR+beat*Q,d=.2,v=.8 if beat==0 else .55,pieza='kick')
  for beat in [1,3]:add('caja',b*BAR+beat*Q+.018,d=.2,v=.7,pieza='snare')
  if b%2:add('caja',b*BAR+2.75*Q,d=.12,v=.25,pieza='snare')
  for beat in range(4):
   for off in [0,.57]:add('hats',b*BAR+(beat+off)*Q,d=.08,v=.2+.12*(off>0),p=.2,pieza='hat')
  if b%4 in [0,2]:add('ride',b*BAR+.5*Q,d=.8,v=.3,p=.3,pieza='ride')
  if b%4==3:add('rim',b*BAR+3.6*Q,d=.1,v=.35,p=-.3,pieza='rim')
 # El motor electrónico tiene su propio fraseo recto y aprende la cabeza del piano.
 for b in list(range(24,40))+list(range(54,76)):
  if 54<=b<64 and b%2:continue
  for beat in [0,1,2,3]:add('maquina808',b*BAR+beat*Q,d=.12,v=.36 if beat%2 else .5,pieza='rim' if beat%2 else 'kick')
  for j,beat in enumerate([0,.5,1.5,2,3,3.5]):
   m=roots[b//2%4]+[0,0,7,0,2,4][j]+cents(b)/100;add('bajo-electrico',b*BAR+beat*Q,m,Q*.42,.58)
 for b in list(range(0,24,2))+list(range(32,40,2))+list(range(64,76,2)):
  root=roots[b//2%4]+12+cents(b)/100
  for j,beat in enumerate([0,1.5,3,4.5,6,7]):add('contrabajo',b*BAR+beat*Q,root+[0,7,9,4,2,-1][j],Q*.8,.5,p=-.15,tipo='pizzicato')
 # Fuelle y cuerda intercambian registros; tres arcos, cada uno deja una voz distinta.
 for k,b in enumerate([40,44,48]):
  for j,(a,z) in enumerate([(69-k*3,45+k*3),(45+k*3,69-k*3)]):
   c='fuelle-alto' if j==0 else 'fuelle-bajo';add(c,b*BAR,a,BAR*3.6,.75,p=.25 if j==0 else -.25,m2=z,presion=.55+.12*k,aire=1 if j==0 else -1)
  add('chelo',b*BAR,45+k*3,BAR*3.6,.6,p=-.15,m2=69-k*3,tipo='tasto')
  for j,m in enumerate([57,61,64]):add('piano-goma',(b+2)*BAR+j*Q,m,Q*.6,.4,p=.2)
 for b in [8,24,32,64,72]:
  for m in chords[b//2%4][::2]:add('farfisa',b*BAR,m+cents(b)/100,BAR*2,.35,p=-.25)
 # Solo D: cuatro quintas octavadas y cierre por tercera justa.
 ratios=[1,1.5,1.125,1.6875,1.265625,COMA];labels=['A','E','B','F#','C#','A']
 for k,r in enumerate(ratios):
  b=52+2*k;root=float(midi(220*r));P['solo_D'].append({'t':b*BAR,'nombre':labels[k],'ratio':float(r),'root_Hz':220*r,'nota_float':root})
  add('ep-tema',b*BAR,root,Q*1.7,.8,p=-.08,frase='raiz-del-recorrido')
  for j,step in enumerate([7,4,2,0,-3]):add('ep-tema',b*BAR+(2+j*.9)*Q,root+step,Q*.65,.62,p=-.08,frase='desarrollo-D')
  for m in [root+4,root+11]:add('fuelle-alto',b*BAR+2*Q,m,Q*3.5,.4,p=.2,m2=m,presion=.48,aire=1)
 # Presencias: resonadores conservan el piano, señales se contestan con su propia sintaxis.
 for c in ['resonador-A','resonador-coma','batidos','pulsos-batido']:
  add(c,52*BAR,45,28*BAR+5,.5)
 for b in [3,7,17,25,27,29,31,35,39,46,50,65,73,77,79]:
  for j in range(3):add('radio-izq' if j%2==0 else 'radio-der',b*BAR+j*.3*Q,76+[0,7,2][j]+cents(b)/100,Q*(.12+j*.06),.4,p=-.55 if j%2==0 else .55,tipo='burbuja' if b%2 else 'clic')
 for b in [0,6,22,38,50,62,76]:
  add('telar',b*BAR,57+cents(b)/100,BAR*2,.4,p=.1,giro=b/10)
 for b in [0,40,52,64,76]:add('pedal110',b*BAR,45+(CENTS/100 if b>=64 else 0),BAR*2,.35)
 # Tres apariciones vocales. El doble, vocoder y corte viven dentro de esas ventanas.
 texts=[('el a cor de vuel ve con o tro cuer po',[0,2,4,2,0,-2,0,2,4,2,0]),('la mis ma luz no cae en el mis mo lu gar',[4,2,0,-2,0,2,4,2,0,-2,0,2]),('te de jo el nom bre me lle vo el la ti do',[0,2,4,7,4,2,0,-2,0,2,0,-2,0])]
 voice=[];double=[];fragment=[]
 for k,b in enumerate([12,20,68]):
  tx,steps=texts[k];sy=tx.split();t=b*BAR+.25*Q;start=t
  for j,(s,g) in enumerate(zip(sy,steps)):
   beats=2 if j==len(sy)-1 else [.7,.5,1,.7][j%4];m=45+g+cents(b)/100;d=beats*Q*.88;voice.append({'t':t,'dur':d,'texto':s,'nota':m});add('voz',t,m,d,.8)
   if k==2 and j%2==0:double.append({'t':t+.025,'dur':d,'texto':s,'nota':m-5});add('voz-doble',t+.025,m-5,d,.4)
   if k==1:add('voz-fuelle',t,m,d,.5)
   t+=beats*Q
  if k==2:
   for j,s in enumerate(['la','ti','do']):fragment.append({'t':t+j*.4*Q,'dur':.28*Q,'texto':s,'nota':45+CENTS/100});add('fragmento',t+j*.4*Q,45,.28*Q,.5)
  P['letra'].append({'t':start,'t1':t,'texto':tx,'aparicion':k+1})
 P['sabina']=[{'capa':c,'eventos':v} for c,v in [('voz',voice),('doble',double),('fragmento',fragment)]]
 for c in ev:ev[c].sort(key=lambda e:e['t'])
 assert len(ev)==30 and all(ev.values());return P
def main():
 out=ultimo();tag=out.name.split('-')[-1];P=componer();jsave(out/'partitura.json',P)
 f,ax=figura('El piano tiene la palabra','Treinta capas · tres apariciones humanas · fuelle y cuerda cruzan · resonadores cierran')
 for i,(c,events) in enumerate(P['eventos'].items()):
  for e in events:ax[0].plot([e['t'],e['t']+min(e['dur'],5)],[i,i],color=['#e9b46e','#79c1bd','#d4a5b7'][i//10],lw=1)
 ax[0].set_yticks(range(30),list(P['eventos']),fontsize=6);ax[0].set_xlabel('segundos');ax[0].set_xlim(0,P['duracion']);salva(f,out/'proceso'/f'02-partitura-y-relevos-s{SEED}-{tag}.png');print(P['duracion'],'s',sum(map(len,P['eventos'].values())),'eventos')
if __name__=='__main__':main()
