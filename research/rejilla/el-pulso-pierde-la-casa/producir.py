"""Nueva escritura por escenas; fuentes previas sólo aportan motores, nunca su partitura."""
from pathlib import Path
import importlib.util,json,uuid,hashlib,io,subprocess,sys
import numpy as np
from scipy.signal import butter,sosfilt,resample_poly
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent; REPO=R.parent
def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
h=module('h',REPO/'la-garganta-sale-bailando/producir.py')
sy=module('sy',REPO/'lo-que-tapa-la-traspuesta/sintes2.py')
SR=24000;D=202.;N=int(D*SR);SEED=19102673
SECTIONS=[(0,18,'Cuerpo'),(18,42,'Canto'),(42,58,'Presión'),(58,82,'Cuatro bocas'),(82,108,'Ráfagas'),(108,138,'Ventana'),(138,165,'Intercambio'),(165,202,'Dos finales falsos')]
P=dict(titulo='El pulso pierde la casa',duracion=D,semilla=SEED,secciones=SECTIONS,garganta=[],metal=[],chelo=[],bajo=[],voces=[],sinte=[],bateria=[])
def note(voice,t,m,d,v=.8,**kw):
 if t+d<D:P[voice].append(dict(t=round(t,5),m=m,dur=d,v=v,**kw))
def phrase(voice,t,pitches,lengths,unit=.5,transpose=0,v=.8):
 for j,(m,d) in enumerate(zip(pitches,lengths)):
  if m is not None:note(voice,t,m+transpose,d*unit*.89,v,vocal='uaeio'[j%5])
  t+=d*unit
 return t
B=[69,76,74,72,71,None,67,70,69];BD=[2,3,1,2,4,1,2,3,5]
ANSWER=[74,72,79,77,76,None,70,71,68];AD=[1,2,3,1,4,2,2,1,4]
def score():
 phrase('metal',.6,[57,None,64,60,59],[1,1,1,2,3],.5)
 phrase('metal',9.7,[57,64,None,67,65,60],[1,1,2,1,2,3],.5)
 phrase('garganta',18,B,BD,.51)
 phrase('garganta',30.6,ANSWER,AD,.53)
 # A's last pitch becomes a sustained microtonal split, then the chorus bass.
 note('chelo',42,56,7,.65,tipo='tasto',casa=0)
 note('chelo',49.3,56.13,8,.6,tipo='armonico',casa=0)
 note('garganta',44,68,5,.7,vocal='u');note('garganta',50,68.14,6,.8,vocal='a')
 for j,(ps,ds) in enumerate([([68,71,73,76,75],[4,3,5,2,6]),([63,64,68,66,68],[3,5,4,5,3]),([59,61,60,63],[6,4,3,7]),([44,47,49,46,44],[5,3,4,4,4])]):
  t=58+j*.18
  for k,(m,d) in enumerate(zip(ps,ds)):note('voces',t,m,d*.48,.7,vocal='uaeo'[j],pan=[-.65,.65,-.3,.3][j],carrier=j);t+=d*.5
 phrase('metal',68.3,[68,75,73,71,70],[2,1,3,1,3],.5)
 phrase('voces',73.4,[76,73,71,68],[1,2,1,3],.48)
 phrase('metal',77.1,[70,73,77],[1,1,2],.46)
 phrase('voces',79.1,[75,71,68],[1,1,2],.43)
 for t,ps,ds in [(87,[68,68.11],[2,3]),(95,[69,76,74],[1,2,3]),(103,[70,71,68],[1,1,3])]:phrase('garganta',t,ps,ds,.5)
 phrase('sinte',108,[81,88,86,84,83,None,79,82,81],BD,.55)
 phrase('garganta',121,ANSWER,AD,.45,2)
 phrase('metal',131,[73,76,80,78,75,71,70],[1,1,2,1,2,1,3],.53)
 phrase('bajo',138,B,BD,.82,-24)
 phrase('metal',140,[64,68,66,71,69,73,70],[4,2,3,2,5,2,4],.62)
 phrase('sinte',158,[81,76,None,72,75,71],[1,2,1,2,1,3],.55)
 for t in np.arange(139,164,.91):note('garganta',float(t),57,.105,.7,vocal='i')
 phrase('voces',165,B,BD,.42,0)
 phrase('metal',175,ANSWER,AD,.35,-5)
 phrase('voces',184,[81,79,76,75,71,73,80],[2,1,3,1,2,2,4],.43)
 phrase('sinte',193.1,[73,80,82,85,84,80,78],[1,1,1,1,2,1,3],.42)
 for m in [42,49,58,66,73,80]:note('voces',199.4,m,1.3,.65,vocal='a',pan=(m-61)/35,carrier=2)
 # Bass/harmony move independently; longer solo gaps invite short chelo answers.
 for a,z,name in SECTIONS:
  if a in [42,138]:continue
  for j,t in enumerate(np.arange(a,z-1,2.4 if a<82 else 1.9)):
   root=([45,41,48,43] if a<42 else [44,47,49,46] if a<108 else [42,50,47,44])[j%4]
   note('bajo',float(t),root,.36,.85)
   if j%3!=1:note('chelo',float(t+.8),root+12,.38,.65,tipo='pizz',casa=.7 if a>=108 else .25)
 for t,m in [(24.2,60),(28.4,64),(35.9,62),(40.6,56),(117.8,66),(128.2,70)]:note('chelo',t,m,.6,.6,tipo='armonico',casa=0)
 # Different drum syntax per scene, including full withdrawals and unequal false endings.
 for a,z,name in SECTIONS:
  if a==42:continue
  bpm=100 if a<82 else 184 if a==82 else 172 if a==108 else 112 if a==138 else 196
  q=60/bpm;bar=0;t=a
  while t<z-.1:
   pattern=[0,8] if a<82 or a==138 else [0,4,8,12] if a in [82,165] else [[0,7,10],[0,4,11,14],[0,6,8,13]][bar%3]
   for step in range(16):
    tt=t+step*q/4
    if tt>=z or any(x<=tt<y for x,y in [(86.7,89.7),(94.7,98),(102.7,105.8),(181.3,183),(190.1,193.1),(200.3,202)]):continue
    if a==108 and bar%4==3 and step>6:continue
    def drum(k,g):P['bateria'].append(dict(t=tt,pieza=k,g=g))
    if step in pattern:drum('gabber' if a in [82,165] else 'kick',.82)
    if step in ([6,14] if a<82 or a==138 else [4,12]):drum('snare',.62)
    if step in [3,11] and a<82:drum('rim',.35)
    if step%2==0 and not (a==138 and step%4==2):drum('hat',.12+.06*(step%4==0))
    if bar%3==2 and step in [13,15]:drum('tomlo',.33)
    if bar%4==0 and step==0:drum('spray',.17)
   t+=q*4;bar+=1
 P['bateria'].append(dict(t=200.12,pieza='gabber',g=1.1))
 for k in ['garganta','metal','chelo','bajo','voces','sinte']:P[k].sort(key=lambda x:x['t'])
def card(stage):
 im=Image.new('RGB',(1200,630),'#111421');d=ImageDraw.Draw(im);d.text((32,20),'EL PULSO PIERDE LA CASA',font=h.font(43),fill='#fff0e0');d.text((34,79),stage,font=h.font(19),fill='#f0b299')
 colors=['#f4a6c2','#81e0d1','#dbd38a','#b7a8f4','#ed895d','#7fb6f3']
 for a,z,name in SECTIONS:
  x=40+a/D*1120;d.line((x,125,x,535),fill='#3b4051');d.text((x,545),name[:10],font=h.font(12),fill='#cbc6d5')
 for k,c in zip(['garganta','metal','chelo','bajo','voces','sinte'],colors):
  for e in P[k]:
   x=40+e['t']/D*1120;y=490-(e['m']-35)*6;d.line((x,y,x+max(2,e['dur']/D*1120),y),fill=c,width=3)
 d.text((35,595),'Canek Zapata · 19 octubre 2026 · semilla 19102673',font=h.font(16),fill='#cbc6d5');return im,d
def main():
 score();im,d=card('01 · frases escritas, solos, retiradas y respuestas')
 buf=io.BytesIO();im.save(buf,'PNG');nonce=uuid.uuid4().hex;full=hashlib.sha256(buf.getvalue()+Path(__file__).read_bytes()+nonce.encode()).hexdigest();tag=full[:12]
 out=R/f'el-pulso-pierde-la-casa-s{SEED}-{tag}';out.mkdir()
 for k in ['render','proceso','fuentes']:(out/k).mkdir()
 h.js(out/'partitura.json',P);h.png(out/'proceso'/f'01-escritura-{tag}.png',im)
 sources=[Path(__file__),R/'fisicos.cjs',REPO/'lo-que-tapa-la-traspuesta/sintes2.py',REPO/'lo-que-tapa-la-traspuesta/motor/garganta.js',REPO/'objetos/motor/cuerda.js',REPO/'objetos/motor/metal.js',REPO/'otra-vez-hasta-romper/kit.cjs']
 hashes={str(p.relative_to(REPO)):h.sha(p) for p in sources}
 for j,p in enumerate(sources):(out/'fuentes'/f'{j:02d}-{p.name}').write_bytes(p.read_bytes())
 h.js(out/'receta-inicial.json',dict(hash=full,nonce=nonce,semilla=SEED,fuentes=hashes))
 print(out,flush=True)
 # Audible three-instrument score before orchestration, kept as an actual intermediate.
 sketch=np.zeros(N,np.float32)
 for name,scale in [('garganta',1),('metal',.55),('bajo',.65)]:
  for e in P[name]:
   n=int(e['dur']*SR);t=np.arange(n)/SR;y=np.sin(2*np.pi*h.hz(e['m'])*t)*h.env(n)*.15*scale;a=int(e['t']*SR);sketch[a:a+n]+=y
 h.wav(out/'render'/f'boceto-tres-voces-{tag}.wav',sketch)
 subprocess.run(['node',str(R/'fisicos.cjs'),str(out)],check=True)
 subprocess.run(['node',str(REPO/'otra-vez-hasta-romper/kit.cjs'),str(out)],check=True)
 S={k:np.zeros((N,2),np.float32) for k in ['solistas','chelo','bajo','vocoder','sinte','percusion']}
 def add(k,y,t=0,g=1,pan=0):
  a=int(t*SR);n=min(len(y),N-a);ang=(pan+1)*np.pi/4
  S[k][a:a+n,0]+=y[:n]*g*np.cos(ang);S[k][a:a+n,1]+=y[:n]*g*np.sin(ang)
 for name,group,g,pan in [('garganta','solistas',.32,-.12),('metal','solistas',.27,.22),('chelo','chelo',.25,-.3)]:
  y=resample_poly(np.fromfile(out/'render'/f'{name}.f32',dtype=np.float32),1,2);add(group,h.unit(y),g=g,pan=pan)
 for name,timbre,g in [('bajo','fretless',.26),('sinte','zawinul',.20)]:
  y=resample_poly(sy.mono(P[name],int(D*48000),timbre,SEED),1,2);add(name,y,g=g)
 bank=REPO/'inferencia/vendor/difonos/bancos/sabina-1-b44e7fab5cee';M=json.loads((bank/'manifiesto.json').read_text('utf8'));raw=np.frombuffer(h.run(['ffmpeg','-v','error','-i',str(bank/'banco.flac'),'-f','f32le','-ac','1','pipe:1']).stdout,dtype='<f4');vowels={}
 for v in 'aeiou':
  u=M['unidades'][v*2];vowels[v]=resample_poly(raw[u['inicio']+u['izq']:u['inicio']+u['der']],160,147)
 edges=np.geomspace(100,10500,25);filters=[butter(2,[a,b],fs=SR,btype='band',output='sos') for a,b in zip(edges[:-1],edges[1:])];sm=butter(1,26,fs=SR,output='sos')
 for e in P['voces']:
  n=int(e['dur']*SR);t=np.arange(n)/SR;grain=vowels[e.get('vocal','a')];mod=np.zeros(n+len(grain))
  for j in range(0,n,max(1,len(grain)//3)):mod[j:j+len(grain)]+=grain*np.hanning(len(grain))
  ph=2*np.pi*h.hz(e['m'])*t;kind=e.get('carrier',0)
  carrier=sum(np.sin(k*ph)/k for k in range(1,min(32,int(10500/h.hz(e['m']))))) if kind%2==0 else np.sin(ph+3*np.sin(ph*2.003)*np.exp(-t/2))
  y=sum(sosfilt(f,carrier)*sosfilt(sm,np.abs(sosfilt(f,mod[:n]))) for f in filters)
  add('vocoder',h.unit(y)*h.env(n,.025,.09),e['t'],.22,e.get('pan',.1))
 print('Voces, instrumentos y boceto completos',flush=True)
 kit={k:h.unit(np.fromfile(out/'render'/f'kit-{k}.f32',dtype=np.float32)) for k in ['kick','snare','hat','rim','tomlo','spray']}
 t=np.arange(int(.26*SR))/SR;kit['gabber']=np.tanh(5*np.sin(2*np.pi*(51*t+125*.023*(1-np.exp(-t/.023))))*np.exp(-t/.13))*h.env(len(t),.001,.025)
 duck=np.ones(N,np.float32)
 for e in P['bateria']:
  k=e['pieza'];add('percusion',kit[k],e['t'],e['g']*.66,0 if k in ['kick','gabber','snare'] else -.25 if k=='rim' else .35)
  if k in ['kick','gabber','snare']:
   a=int(e['t']*SR);n=min(int(.18*SR),N-a);duck[a:a+n]=np.minimum(duck[a:a+n],1-.48*np.exp(-np.arange(n)/SR/.055))
 im,d=card('02 · motores físicos y vocoders; ataques de percusión al frente')
 for e in P['bateria']:
  x=40+e['t']/D*1120;d.line((x,515,x,515-20*e['g']),fill='#f58b57',width=2)
 h.png(out/'proceso'/f'02-orquestacion-{tag}.png',im)
 # Keep attacks dry; lower sustained spectrum on each impact, bass ducks deeper.
 mix=np.zeros((N,2),np.float32);stats={}
 for k,y in S.items():
  if k!='percusion':
   y*=duck[:,None]**(1.5 if k=='bajo' else 1)
   if k not in ['bajo']:y[:]=sosfilt(butter(2,150,fs=SR,btype='high',output='sos'),y,axis=0)
  stats[k]=dict(peak=float(abs(y).max()),rms=float(np.sqrt(np.mean(y*y))))
  h.wav(out/'render'/f'{k}-{tag}.wav',y);mix+=y
 # Real silences and final cut include all tails.
 for a,z in [(181.3,183),(190.1,193.1),(200.38,202)]:
  i=int(a*SR);j=int(z*SR);r=int(.012*SR);mix[i:i+r]*=np.linspace(1,0,r)[:,None];mix[i+r:j]=0
 mix*=.79/(np.max(np.abs(mix))+1e-12);h.wav(out/f'mezcla-{tag}.wav',mix)
 master=out/f'el-pulso-pierde-la-casa-{tag}.m4a'
 h.run(['ffmpeg','-v','error','-n','-i',str(out/f'mezcla-{tag}.wav'),'-af','volume=3dB,alimiter=limit=0.85:attack=3:release=55:level=false:latency=true','-c:a','aac','-b:a','256k',str(master)])
 im,d=card('03 · mezcla: percusión seca, bajo con espacio, dos cortes desiguales')
 for j in range(1120):
  y=mix[int(j*N/1120):int((j+1)*N/1120)];p=float(abs(y).max());x=40+j;d.line((x,520-p*34,x,520+p*10),fill='#fa905f')
 h.png(out/'proceso'/f'03-mezcla-{tag}.png',im);h.png(out/f'el-pulso-pierde-la-casa-{tag}.png',im);h.png(out/'og.png',im)
 ims=[Image.open(p).convert('RGB') for p in sorted((out/'proceso').glob('*.png'))]
 with (out/f'proceso-el-pulso-{tag}.gif').open('xb') as f:ims[0].save(f,format='GIF',save_all=True,append_images=ims[1:],duration=2600,loop=0)
 h.txt(out/'proceso/README.md','Tres etapas reales, guardadas antes de renderizar, después de orquestar y después de mezclar. GIF: 7.8 s, borradores sucesivos; no representa animación interna del motor. Semilla 19102673.\n')
 h.js(out/'mediciones-buses.json',stats)
 h.txt(out/'ESCUCHA.md','# El pulso pierde la casa\n\n3:22. Instrumental sin letra. Percusión más al frente: bombo/caja secos, espacio dinámico en el bajo y reducción breve de las capas sostenidas con cada ataque.\n\n'+ '\n'.join(f'- {a:g}–{z:g} s: {name}.' for a,z,name in SECTIONS)+'\n\nB tiene exposición de garganta, desarrollo agudo y aumento en bajo. Coro de cuatro movimientos distintos, metal con turnos progresivamente cortos, presión sin batería y falsos cierres de 1.7 y 3 segundos. El último impacto corta todas las colas.\n\nSe conservaron boceto de tres voces, pistas y fuentes. Perfil de garganta sintético, no terreno de Traspuesta. Motores físicos a 48 kHz, mezcla a 24 kHz. Los vocoders usan vocales del banco local Sabina; no hay palabras. La inspección realizada es de partitura, datos y mezcla; la valoración auditiva queda para la escucha de Canek.\n')
 assert all(h.sha(REPO/k)==v for k,v in hashes.items())
 h.js(out/'receta-final.json',dict(hash=full,semilla=SEED,fuentes_intactas=True,archivos={str(p.relative_to(out)):h.sha(p) for p in out.rglob('*') if p.is_file()}))
 print('TERMINADO',master,flush=True)
if __name__=='__main__':main()
