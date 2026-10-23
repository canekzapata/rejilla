"""Idea D: escribir llegadas. Frase, contrapunto y solos sobre la red 227.

Los eventos de fractura guardan emisor y llegada de referencia por separado.
Tónica = primer modo de la placa central, octavado; negra = f0/40.
"""
from comun import *
from laminas import *
def componer(red):
 f0=red['f0'];root=float(midi(f0));Q=40/f0;BAR=4*Q;S=Q/4
 fases=[('I','La primera llegada',0,8),('II','Los inviernos de máquina',8,32),('III','Dos voces bajo el hielo',32,48),('IV','El arco conoce el borde',48,64),('V','Reunir la grieta',64,80),('VI','Cambiar de hoja',80,96),('VII','Otro invierno',96,112),('VIII','Lo que llega junto',112,116)]
 secciones=[{'id':i,'nombre':n,'t':a*BAR,'t1':b*BAR,'compases':[a,b]} for i,n,a,b in fases];dur=116*BAR+4
 nombres=['lago','grietas-cerca','grietas-lejos','cunas-graves','cunas-agudas','arco','escarcha','deshielo','bateria808','bateria-frita','fotones','androide','sub','piano','chelo','clarinete','metal','terminal','sabina-M','sabina-T','voc-hielo-M','voc-hielo-T','voc-cunas','voc-terminal','chops','telar-T','telar-solo','campo-H','campo-U','ep2']
 P={'titulo':'El lago que canta bajo el hielo','semilla':SEED,'sr':SR,'f0':f0,'tonica_midi':root,'bpm':60/Q,'negra':Q,'compas':BAR,'duracion':dur,'secciones':secciones,'eventos':{n:[] for n in nombres},'sabina':[],'letra':[],'idea':'D: emisión preparada y llegada dispersa; se reúnen por compensación de fase'}
 ev=P['eventos'];rng=np.random.default_rng(SEED);pp=red['placas'];byid={q['id']:q for q in pp};esc=[0,2,3,5,7,8,10]
 def grado(g,oct=0):k,r=divmod(int(g),7);return root+12*(oct+k)+esc[r]
 def T(m,arriba=True):
  tri=[root+12*k+v for k in range(-4,6) for v in [0,3,7]]
  return min(v for v in tri if v>m+.001) if arriba else max(v for v in tri if v<m-.001)
 def add(c,t,m=60,d=.2,v=.7,pan0=0,**kw):ev[c].append({'t':round(float(t),6),'midi':float(m),'dur':float(d),'vel':float(v),'pan':float(pan0),**kw})
 # El sujeto deriva del ORDEN DE LLEGADA de los diez modos de la placa, proyectado
 # 24 veces en tiempo musical; sus grados se editan como frase y se guarda la procedencia.
 mod=red['modos'][str(pp[0]['id'])];ff=np.array(mod['f']);r=pp[0]['distancia'];arr=r/(2*np.sqrt(red['alpha']*2*np.pi*ff));order=np.argsort(arr)
 subj=[6,5,4,2,3,1,0,2,1,0];rit=[1,1,2,1,3,1,2,1,2,2]
 P['sujeto']={'grados':subj,'ritmo_semicorcheas':rit,'orden_modos':order.tolist(),'llegadas_fisicas_s':arr[order].tolist(),'operacion':'orden descendente de frecuencias → arco escalar editado; duraciones compuestas, no igualadas a la propagación'}
 # Red de inviernos: el orden de apertura controla las entradas y el reparto.
 rutas=[]
 for invierno,(b0,b1) in enumerate([(1,8),(8,32),(32,48),(48,64),(64,80),(96,112)]):
  hist=red['inviernos'][min(invierno,4)];count=min(74,len(hist));tt0=b0*BAR;tt1=b1*BAR
  for j,he in enumerate(hist[:count]):
   ed=red['aristas'][he['arista']];pl=byid[ed['a']];t=tt0+(j+.3)/count*(tt1-tt0-.5)
   if 8<=b0<32 or b0>=96:t=round(t/S)*S
   lam=0 if b0<64 else (j/max(1,count-1) if b0==64 else .35+.6*(j%7)/6)
   tau=(1-lam)*pl['distancia']/(2*np.sqrt(red['alpha']*2*np.pi*1200));emite=t-tau
   common={'celda':ed['a'],'arista':he['arista'],'invierno':min(invierno,4),'memoria':he['memoria'],'compensacion':lam,'distancia':pl['distancia'],'emision':emite,'llegada':t}
   add('grietas-lejos',t,d=.2,v=.45+.3*(j%5==0),pan0=pl['pan'],**common)
   if j%3==0:add('grietas-cerca',emite,d=.1,v=.35,pan0=pl['pan']*.7,**common)
   add('cunas-graves' if pl['area']>np.median([q['area'] for q in pp]) else 'cunas-agudas',t,m=grado((j*3)%7,-1),d=.4,v=.45+.3*(j%4==0),pan0=pl['pan'],**common)
   if j%5==0:add('lago',t,d=min(5,tt1-t+1),v=.5,pan0=pl['pan']*.4,celda=ed['a'],estado=min(invierno,4))
   rutas.append({'t':emite,'llegada':t,'arista':he['arista'],'invierno':min(invierno,4),'lambda':lam})
 # Electro con frases de batería distintas, 3-3-2 y acentos derivados de la red.
 for b in list(range(8,32))+list(range(36,48))+list(range(64,80))+list(range(96,112)):
  finales=b%8==7;lleno=b>=96 or 24<=b<32
  for s in ([0,3,8,11,14] if b%2 else [0,6,10]):add('bateria808',(b*16+s)*S,d=.2,v=.95 if s==0 else .72,pieza='kick')
  for s in [4,12]:
   add('bateria808',(b*16+s)*S,d=.15,v=.72,pieza='snare');add('bateria-frita',(b*16+s)*S+.008,d=.12,v=.4 if b<96 else .65,pieza='clap')
  for s in range(16):
   if s%2 or (lleno and s%4==0):add('bateria808',(b*16+s)*S,d=.1,v=.2+.2*(s%4==3),pan0=.3,pieza='hat' if s%8!=7 else 'openhat')
  if finales:
   for j in range(8):add('bateria-frita',(b*16+12+j*.5)*S,d=.08,v=.25+.055*j,pan0=-.5+j/7,pieza='hat')
   add('bateria-frita',(b*16+14)*S,d=.2,v=.42,pieza='spray')
  for j,s in enumerate([0,3,6,10,13]):
   g=[0,0,-1,2,1][(j+b//4)%5];add('androide',(b*16+s)*S,grado(g,-1),S*[2.5,1,2,2,1][j],.8)
   if j in [0,3]:add('sub',(b*16+s)*S,grado(g,-1)-12,S*2.6,.75)
  if b%4 in [1,3]:
   for s in [2,7,15]:add('fotones',(b*16+s)*S,grado(s%5,1),.12,.45,(-1 if s%2 else 1)*.4)
 # Semillas del sujeto: entradas, respuesta invertida, hoquetus y aumentación.
 for b in [2,5,10,14,18,22,26,30,50,54,58,62,98,102,106,110]:
  off=b*BAR;inv=b in [18,26,54,62,106];degrees=[6-g for g in subj] if inv else subj[:]
  if b>=96:degrees=degrees[:6]+[2,4,1,0] # adopta el final del solo; no restaura la primera frase
  for j,(g,d) in enumerate(zip(degrees,rit)):
   tt=off+sum(rit[:j])*S;cl=pp[(j*5+b)%len(pp)];m=grado(g,1)
   add('piano' if j%2==0 else 'terminal',tt,m,d*S*.85,.55,(-.35 if j%2==0 else .3))
   if b>=8:add('telar-T',tt+.6,T(m,not inv),d*S,.6,pan0=.2,cuerpo='vidrio',giro=(b%8)*.18,inclinacion=.2*np.sin(j),dispersion=.1)
  if b in [14,22,54,102]:
   for j,g in enumerate(degrees[::2]):add('chelo',off+j*Q*1.5,grado(g,-1),Q*1.35,.5,-.35,tipo='armonico' if j%2 else 'ponticello')
 # El acorde de una grieta se abre en instrumentos de cámara y sombras H/U.
 for k,b in enumerate([1,6,33,40,48,56,80,88,96,112]):
  fbase=hz(grado([0,2,0,4,1,0,3,1,0,0][k],0));durc=BAR*(2 if b!=112 else 3)
  add('campo-H',b*BAR,midi(fbase),durc,.5,stretch=.012*k)
  add('campo-U',b*BAR+Q,midi(fbase*4),durc,.42)
  for j in range(3):
   ta=red['placas'][(k*3+j)%32]['distancia']/(2*np.sqrt(red['alpha']*2*np.pi*[300,1200,4800][j]))
   tt=b*BAR+24*ta;add(['metal','clarinete','chelo'][j],tt,grado([0,2,4][j],0),Q*(2+j),.5,[-.4,.35,0][j],tipo=['aire','subtono','tasto'][j])
 # Solo de arco: presión y duración cambian frase a frase, respuestas de cámara.
 for k,b in enumerate(range(48,64,2)):
  for j,g in enumerate([0,2,1,4,3] if k%2==0 else [5,4,2,1]):
   d=[1,1.5,.5,2,2][j]*Q;t=b*BAR+j*.65*Q
   add('arco',t,grado(g,1),d,.75,celda=pp[(k*3+j)%32]['id'],presion=.2+.075*k,velocidad=.2+.08*j)
  add('clarinete',(b+1)*BAR+2*Q,grado(4-k%4,1),Q,.5,.4,tipo='multifonico' if k%3==0 else 'slap')
 # Solo D: los intervalos vienen de tiempos de llegada, luego se recogen.
 P['solo_D']=[]
 for k in range(16):
  b=64+k;lam=k/15;cl=pp[(k*7)%32];frecs=np.array(red['modos'][str(cl['id'])]['f']);freqs=np.sort(frecs)[::-1][:5]
  delays=cl['distancia']/(2*np.sqrt(red['alpha']*2*np.pi*freqs));delays=(delays-delays.min())*24*(1-lam)
  for j,de in enumerate(delays):
   m=grado(int(np.round([6,4,3,1,0][j]*(1-lam)))+k%3,1)
   add('telar-solo',b*BAR+float(de)+.6,m,Q*(.4+.8*lam),.8,cl['pan'],cuerpo='cobre' if k%3 else 'vidrio',giro=lam*4*np.pi,inclinacion=.5*(1-lam),dispersion=.6*(1-lam))
   if j%2==0:add('terminal',b*BAR+float(de),m-12,Q*.5,.62,-cl['pan'])
  P['solo_D'].append({'t':b*BAR,'lambda':lam,'celda':cl['id'],'retardos_proyectados':delays.tolist()})
 # Deshielo y EP2: dos vueltas en un evento sostenido; gotas recogen finales previos.
 add('ep2',80*BAR,root+24,16*BAR,.7)
 for i in range(96):
  t=80*BAR+i/96*16*BAR;add('deshielo',t,grado((i*3)%9,2),.2,.2+.35*(i%7==0),float(np.sin(i)*.65))
 # Escarcha recuerda los patrones de las grietas; acelera de impulsos a timbre al entrar en V.
 for b in list(range(8,32))+list(range(60,80))+list(range(98,112)):
  for j in range(4 if b<60 else 8):add('escarcha',b*BAR+j*BAR/(4 if b<60 else 8),grado((j+b)%7,2),.05,.25,(-1 if j%2 else 1)*.5,rapidez=4+(b-60)*2 if b>=60 else 4)
 # Frases originales: cada una tiene recorrido fonético, respiración y final distintos.
 frases=[('ba jo el hie lo que da u na voz',[0,1,2,4,3,2,1,0,1,0],[2,1,1,3,1,2,1,2,1,6]),
 ('lle ga pri me ro lo que bri lla',[2,3,4,6,5,4,3,2,1],[1,1,2,2,3,1,2,2,7]),
 ('lo que pe sa lle ga des pués',[4,3,2,1,2,3,1,0],[2,2,3,1,1,2,2,8]),
 ('ca da in vier no en cuen tra o tra bo ca',[0,2,1,3,4,2,3,5,4,3,1,0],[1,1,2,1,3,1,2,1,1,2,2,5]),
 ('te oi go don de ya no es tás',[6,5,3,4,2,1,2,1,0],[2,1,3,1,2,1,1,3,8]),
 ('jun to la luz que lle ga ro ta',[0,1,3,4,6,5,3,2,1],[1,2,1,4,1,1,2,3,7]),
 ('dos vo ces mi den la dis tan cia',[2,3,5,4,3,1,0,1,0],[2,1,2,3,1,2,1,3,9]),
 ('el la go guar da lo que cam bia',[0,1,2,4,3,5,4,2,0],[1,1,2,2,1,3,2,4,8])]
 vocales={'M':[],'T':[],'solo':[],'chops':[]}
 expos=[(16,0),(24,1),(32,2),(36,3),(40,4),(44,5),(81,6),(88,7),(96,3),(100,5),(104,6),(108,7),(112,0)]
 for k,(b,fi) in enumerate(expos):
  text,gs,ds=frases[fi];t=b*BAR+.25*Q;start=t;syll=text.split();arriba=k%3!=1
  for j,(sy,g,d) in enumerate(zip(syll,gs,ds)):
   dd=d*S*(1.25 if b>=104 else 1);m=grado(g,1);mt=T(m,arriba)
   if b>=96 and j==len(gs)-2:m=grado(4,1);mt=T(m,arriba)
   vocales['M'].append({'t':t,'dur':dd*.91,'texto':sy,'nota':m});vocales['T'].append({'t':t+.025,'dur':dd*.94,'texto':sy,'nota':mt-12})
   add('sabina-M',t,m,dd,.8);add('sabina-T',t+.025,mt-12,dd,.7)
   for c,nm,cell in [('voc-hielo-M',m,pp[(j+k)%32]),('voc-hielo-T',mt-12,pp[(2*j+k)%32])]:add(c,t,nm,dd,.8,cell['pan']*.45,celda=cell['id'],presion=.35+.04*(j%5))
   if j%2==0:add('voc-cunas',t,mt-12,dd,.6,.25,celda=pp[(j+k)%32]['id'])
   t+=dd
  P['letra'].append({'t':start,'t1':t,'texto':text.replace(' ',' '),'frase':fi,'autor':'texto original para esta pieza'})
 # Solo de vocoder: tres gestos contrastantes, no copia del estribillo.
 for k,(b,syll,gs,ds) in enumerate([(83,'a e i u o',[6,4,2,3,0],[2,1,3,1,5]),(86,'ma ta ri a',[0,3,6,5],[1,1,1,7]),(92,'u a e i a',[4,2,1,3,0],[4,1,1,2,8])]):
  t=b*BAR
  for sy,g,d in zip(syll.split(),gs,ds):
   vocales['solo'].append({'t':t,'dur':d*Q*.85,'texto':sy,'nota':grado(g,1)});add('voc-terminal',t,grado(g,1),d*Q,.8,.1);t+=d*Q
 for k,b in enumerate([29,46,78,99,107]):
  for j,sy in enumerate(['hie','lo','lle','ga']):
   t=b*BAR+j*.5*Q;vocales['chops'].append({'t':t,'dur':Q*.3,'texto':sy,'nota':grado((k+j)%7,2)});add('chops',t,grado((k+j)%7,2),Q*.3,.7)
 P['sabina']=[{'capa':c,'nivel':.9,'pan':-.15 if c=='M' else .15,'eventos':sorted(es,key=lambda e:e['t'])} for c,es in vocales.items()]
 P['grietas']=sorted(rutas,key=lambda e:e['t'])
 for c in ev:ev[c].sort(key=lambda e:e['t'])
 assert len(ev)==30 and all(len(v)>0 for v in ev.values())
 return P
def main():
 out=ultimo();red=jleer(out/'red.json');P=componer(red);tag=out.name.split('-')[-1];jguardar(out/'partitura.json',P)
 fig,ax=figura('Treinta planos, una llegada','Partitura compuesta · frases, cámara, inviernos, enfoque y cambio de hoja')
 for k,(c,ev) in enumerate(P['eventos'].items()):
  for e in ev:ax[0].plot([e['t'],e['t']+min(e['dur'],3)],[k,k],color=C[k//8%4],lw=1.3)
 ax[0].set_yticks(range(30),[c for c in P['eventos']],fontsize=6);ax[0].set_xlabel('segundos');ax[0].set_xlim(0,P['duracion']);salva(fig,out/'proceso'/f'04-partitura-treinta-planos-s227-{tag}.png')
 print('duración',P['duracion'],'BPM',P['bpm'],'eventos',sum(map(len,P['eventos'].values())))
if __name__=='__main__':main()
