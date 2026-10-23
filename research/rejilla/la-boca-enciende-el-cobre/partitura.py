from pathlib import Path
import json,hashlib,uuid,io
import numpy as np
from PIL import Image,ImageDraw,ImageFont

R=Path(__file__).resolve().parent;REPO=R.parent;SEED=19102743
SECTIONS=[(0,4,'umbrales',104),(4,12,'canto',104),(12,20,'respuesta',104),(20,28,'abrir',112),(28,40,'coro',112),(40,48,'cuerda y aire',88),(48,60,'solos',120),(60,68,'relevos',120),(68,80,'coro aprendido',116),(80,88,'baile',190),(88,96,'coda',108)]
def section(b):return next(s for s in SECTIONS if s[0]<=b<s[1])
def beats(b):return [3,5][(b-40)%2] if 40<=b<48 else [4,4,3,5][(b-60)%4] if 60<=b<68 else [4,4,3,5][(b-88)%4] if b>=88 else 4
START=[0.]
for b in range(96):START.append(START[-1]+beats(b)*60/section(b)[3])
DUR=START[-1]+.5
def at(b,k=0):return START[b]+k*60/section(b)[3]
def hz(m):return 440*2**((m-69)/12)
def midi(f):return 69+12*np.log2(f/440)
CH=[[50,57,60,64,65,69],[53,60,64,67,69,72],[51,58,62,65,67,72],[45,52,55,61,65,70],[46,53,57,60,64,69],[43,50,53,57,58,62],[40,47,50,55,58,62],[45,52,55,61,64,70]]
def chord(b):
 i=((b-4)//2)%8 if b<40 else ((b-40)//1+4)%8 if b<48 else ((b-48)//2)%8 if b<68 else ((b-68)//2)%8 if b<88 else [4,5,6,7,0,2,7,0][b-88]
 return CH[i]
P=dict(titulo='La boca enciende el cobre',semilla=SEED,duracion=DUR,compases=[dict(b=b,t=START[b],fin=START[b+1],pulsos=beats(b),bpm=section(b)[3],acorde=chord(b)) for b in range(96)],secciones=[dict(b=a,fin_b=z,nombre=n,bpm=p,t=START[a],fin=START[z]) for a,z,n,p in SECTIONS],**{k:[] for k in ['trompeta','garganta','sax','chelo','piano','rhodes','bajo','sinte','doble','voces','espectro','bateria','frases']})
def ev(k,b,p,m,d,v=.8,**kw):
 t=at(b,p);dur=d*60/section(b)[3]
 if t+dur>DUR:dur=DUR-t
 P[k].append(dict(t=round(t,6),dur=round(dur,6),m=float(m),v=v,b=b,**kw))
def absolute(k,t,m,d,v=.8,**kw):P[k].append(dict(t=round(t,6),dur=round(d,6),m=float(m),v=v,**kw))
# Four distinct two-bar phrases, with rests, pickups and different arrivals. p is beat offset across two bars.
THEME=[[(0,74,.68),(.75,77,.22),(1.25,76,.56),(2.1,72,.8),(3.25,74,.55),(4.25,69,.62),(5,71,.38),(5.75,72,1.1),(7.25,69,.5)],
 [(0,72,1.05),(1.25,76,.38),(2,79,.66),(2.9,77,.4),(3.5,76,.32),(4.3,74,.78),(5.25,72,.32),(6,70,.8),(7.1,69,.62)],
 [(.25,69,.4),(1,74,.7),(2,77,.45),(2.75,81,.85),(4,79,.55),(4.75,77,.4),(5.5,76,.55),(6.5,73,1.05)],
 [(0,74,.9),(1.25,72,.5),(2,70,.58),(3,69,.67),(4.25,67,.45),(5,70,.6),(6,73,.38),(6.75,74,.95)]]
COUNTER=[[(.5,62,1.5),(2.75,65,.62),(4,64,.9),(5.75,60,1.4)],[(0,64,1.4),(2,62,.75),(4,65,.7),(5.25,67,1.7)],[(0,65,.8),(1.5,64,1.4),(4,62,.6),(5.5,61,1.8)],[(.5,60,1.2),(2.5,64,.8),(4.5,67,.6),(6,61,1.6)]]
def phrase(k,b,table,tr=0,label='canto',variation=0,double=False):
 start=len(P[k])
 for j,(pos,m,d) in enumerate(table):
  bb=b+int(pos//4);p=pos%4
  if bb>=96:continue
  # Slightly different answers and endings keep a recognisable rhythm and contour.
  mm=m+tr+(2 if variation==1 and j==len(table)-2 else -1 if variation==2 and j==len(table)-1 else 0)
  vel=.78+(.12 if j in [0,3,len(table)-1] else -.14 if j%4==1 else 0)
  kw=dict(vocal='uaeio'[j%5],fonemas=[['d','u'],['b','a'],['i'],['u'],['a']][j%5],tipo='lengua' if d<.4 else 'normal',lengua=(j%3==0),frase=label)
  ev(k,bb,p,mm,d,vel,**kw)
  if double:ev('doble',bb,p,mm,d*.98,vel*.65,frase=label)
 P['frases'].append(dict(nombre=label,instrumento=k,t=START[b],fin=at(min(b+2,95)),eventos=len(P[k])-start))
def lead():
 # The first phrase is anticipated by three soft brass calls, not a long empty introduction.
 for b in range(4):
  phrase('trompeta',b,[(.25,69+b,.45),(1.5,74+(b%2)*3,.7),(3,72+b,.6)],label='umbral',double=b>1)
 for b in range(4,20,2):
  i=((b-4)//2)%4;k='trompeta' if b<12 or b in [16,18] else 'garganta'
  phrase(k,b,THEME[i],label='A: '+['llamada','réplica','extensión','llegada'][i],variation=1 if b>=12 else 0,double=True)
  phrase('sax',b,COUNTER[i],label='contracanto A',tr=0)
 # Prechorus: upward sequence and a countervoice moving down; no constant unison wall.
 for b in range(20,28,2):
  i=(b-20)//2;phrase('garganta' if i%2 else 'trompeta',b,THEME[(i+2)%4],tr=i%3,label='B: abrir',variation=2,double=True)
  phrase('sax',b,COUNTER[3-i],tr=-i,label='contrario B')
 # Three four-bar chorus sentences; each ends differently.
 for b in range(28,40,2):
  i=(b-28)//2;k='garganta' if i%3!=2 else 'trompeta'
  phrase(k,b,THEME[i%4],tr=2 if i in [2,3] else 0,label='C: coro',variation=1 if i>=4 else 0,double=True)
  phrase('sax',b,COUNTER[i%4],tr=7 if i%2 else 0,label='contracanto coro')
 # Chamber passage uses real 3/4 + 5/4 bars. Bow ascends, vocal copper descends.
 for b in range(40,48):
  q=beats(b);ev('chelo',b,0,45+(b-40)*2,q*.9,.58,tipo='tasto' if b<44 else 'ponticello',casa=0)
  ev('trompeta',b,.4,80-(b-40)*1.6,q*.65,.48,tipo='aire' if b%3==0 else 'normal',frase='D: cobre hacia abajo')
  if b%2:ev('garganta',b,1.4,68+(b-40)*.13,2,.58,vocal='u',fonemas=['u'],nota2=68.1+(b-40)*.13,frase='D: batimiento')
 # Actual new solo material: chord tones, approach notes, enclosures, longer targets and rests.
 for b in range(48,60):
  c=chord(b);k='trompeta' if b<52 else 'sax' if b<56 else 'sinte'
  target=c[3]+12 if k=='trompeta' else c[4]+(0 if k=='sax' else 12)
  line=[(.25,target-1,.16),(.5,target+1,.16),(.75,target,.45),(1.5,target+3,.24),(1.83,target+2,.23),(2.25,target-2,.55),(3.25,target+(.0 if b%2 else 5),.6)] if b%3 else [(0,target,.95),(1.25,target+7,.26),(1.75,target+5,.3),(2.5,target+2,.72),(3.5,target-1,.3)]
  phrase(k,b,line,label='E: solo '+k,double=k!='sinte')
  other='sax' if k=='trompeta' else 'trompeta'
  if b%2:ev(other,b,2.8,c[2]+12,.5,.55,frase='respuesta al solo',tipo='lengua',lengua=True)
 for b in range(60,68):
  q=beats(b);k=['trompeta','sax','garganta','sinte'][(b-60)%4];c=chord(b)
  for j in range(int(q*2)-1):ev(k,b,.25+j*.5,c[2+(j%3)]+(12 if k!='sax' else 0)+(1 if j%4==2 else 0),.33,.65+.18*(j%3==0),frase='F: relevo',tipo='lengua',lengua=True,vocal='a',fonemas=['d','a'])
 # The returning lead retains its hook, with the solo's chromatic enclosure before the last arrival.
 for b in range(68,80,2):
  i=(b-68)//2;k='trompeta' if i%2==0 else 'garganta'
  table=list(THEME[i%4])
  if i>=4:table=table[:-1]+[(6.75,73,.18),(7,75,.18),(7.3,74,.55)]
  phrase(k,b,table,label='G: A aprende del solo',variation=1,double=True)
  phrase('sax',b,COUNTER[(i+1)%4],tr=5 if i%2 else 0,label='contracanto retorno')
 for b in range(80,88):
  k=['trompeta','garganta','sinte','sax'][(b-80)%4];c=chord(b)
  phrase(k,b,[(0,c[4]+12,.6),(.75,c[3]+12,.3),(1.5,c[2]+12,.5),(2.25,c[4]+12,.35),(3,c[3]+12,.7)],label='H: baile',double=True)
 for b in range(88,96):
  q=beats(b);i=b-88;c=chord(b);k='garganta' if i%2 else 'trompeta'
  for j,p in enumerate([0,.75,1.5,2.5,3.5]):
   if p+.4<q:ev(k,b,p,[74,77,76,72,74][(j+i)%5]-(12 if i>5 else 0),min(.7,q-p-.1),.72,vocal='u',fonemas=['u'],tipo='normal',frase='I: coda')
def orchestration():
 for b in range(96):
  c=chord(b);q=beats(b);sec=section(b)[2];base=c[0]
  # Bass has connected, syncopated phrases and registral counter-motion, not inaudible infra-bass.
  if b not in [42,45]:
   bass=[(0,base,.7),(1.5,base+7,.38),(2.25,base+10,.35),(3.25,base+12,.45)] if sec not in ['solos','relevos'] else [(0,base,.7),(1,base+4,.7),(2,base+7,.55),(3.25,base-1,.5)]
   if sec=='cuerda y aire':bass=[(.25,base, q-.5)]
   for p,m,d in bass:
    if p>=q:continue
    while m>50:m-=12
    m=max(34,m);ev('bajo',b,p,m,min(d,q-p-.05),.72 if b>=4 else .5,glis=p==3.25,liso=p==3.25)
  # Two to three chord gestures per bar, moving inner voices and making room at lead arrivals.
  positions=[.75,2.5,3.5] if b%2 else [.5,1.75,3]
  if sec=='cuerda y aire':positions=[.5]
  for p in positions:
   if p>=q:continue
   for j,m in enumerate(c[2:]):ev('rhodes',b,p,m+(12 if j==0 and b%4==3 else 0),min(.75,q-p),.45+.1*(p>2),pan=(-.45+j*.25))
  if sec in ['umbrales','abrir','cuerda y aire','relevos','coda'] or b%2:
   for p,m in [(q-.65,c[3]+12),(.1,c[2])]:
    ev('piano',b,p,m,.24,.52,tipo='caja' if sec=='cuerda y aire' and b%2 else 'martillo')
  if sec!='cuerda y aire':
   for p in [1.25,2.75]:
    if p<q:ev('chelo',b,p,base+12,.28,.5,tipo='pizz' if b%4 else 'legno',casa=.65 if b>=68 else .18)
  # Four independent coral voices; durations and entry offsets vary by voice.
  if sec in ['abrir','coro','coro aprendido','coda']:
   for j,(m,pan) in enumerate(zip([c[-1]+12,c[-2],c[2],c[0]+12],[-.68,.6,-.34,.28])):
    p=[0,.25,.6,.1][j]
    target=m+(2 if b%4==3 and j==1 else 0)
    ev('voces',b,p,target,min([1.4,2.3,1.8,2.8][j],q-p-.15),.62,vocal='uaei'[(j+b)%4],carrier=j,pan=pan,frase='coral '+str(j))
    if j<2 and b%2 and q>3:ev('voces',b,3,target-(2 if j==0 else -1),.55,.48,vocal='o',carrier=j,pan=pan,frase='movimiento coral')
  # Answering vocal chops also serve as an audible lead continuation in its rests.
  if sec in ['canto','respuesta','solos','baile'] and b%2:
   ev('voces',b,2.9,c[3]+12,.3,.62,vocal='i',carrier=1,pan=.3,frase='respuesta vocal')
   ev('voces',b,3.45,c[2]+12,.28,.58,vocal='a',carrier=2,pan=-.3,frase='respuesta vocal')
  # Spectral families occur as phrases, not a continuous wallpaper. Anchor 5f persists between constructions.
  if sec in ['abrir','coro','cuerda y aire','coro aprendido','coda']:
   f=hz(c[0])/2;sub=(b%4>=2);freqs=[f*60/n for n in [5,6,8,10,12]] if sub else [f*n for n in [5,6,7,9,11]]
   for j,freq in enumerate(freqs):P['espectro'].append(dict(t=at(b,j*.06),dur=min(q*.9,3.4)*60/section(b)[3],hz=freq,razon=('60/'+str([5,6,8,10,12][j])) if sub else str([5,6,7,9,11][j]),familia='U' if sub else 'H',voz=j,pan=(-.85 if j%2 else .85),b=b))
  # Real variable meter: q*4 subdivisions in every bar. Dembow is stable enough to recognise.
  if sec=='cuerda y aire':
   if b%2==0:P['bateria'].append(dict(t=at(b,.2),pieza='tomlo',g=.35,b=b))
   continue
  for step in range(int(q*4)):
   p=step/4
   def drum(k,g):P['bateria'].append(dict(t=at(b,p),pieza=k,g=g,b=b))
   kicks=[0,8] if sec not in ['solos','relevos','baile'] else [0,7,10,14] if b%2 else [0,4,10]
   if step in kicks:drum('kick',.82 if step==0 else .7)
   if step in [6,14]:drum('snare',.68)
   if step in [3,11]:drum('rim',.35)
   if step%2==0:drum('hat',.14+.06*(step%4==0))
   if sec in ['coro','coro aprendido','baile'] and step in [4,12]:drum('clap',.32)
   if b%4==3 and step in [q*4-3,q*4-2,q*4-1]:drum('tomlo',.3+.04*(step%3))
   if sec in ['solos','relevos'] and step in [5,13]:drum('snare',.14)
   if sec=='baile' and step in [1,7,9,15]:drum('hat',.1)
   if b%4==0 and step==0:drum('spray',.17)
 # Last impact and return after two short edited anticipations in the final chorus.
 P['cortes']=[dict(t=at(74,3.25),dur=.22),dict(t=at(78,3),dur=.30)]
 P['golpe_final']=at(95,beats(95)-.55);P['corte_final']=P['golpe_final']+.26
 P['bateria'].append(dict(t=P['golpe_final'],pieza='kick',g=1,b=95))
 P['bateria'].append(dict(t=P['golpe_final'],pieza='clap',g=.7,b=95))
 for j,m in enumerate([50,57,65,69,76]):absolute('voces',P['golpe_final'],m,.24,.7,vocal='a',carrier=j%4,pan=(j-2)*.25)
 for k in ['trompeta','garganta','sax','chelo','piano','rhodes','bajo','sinte','doble','voces','bateria','espectro']:P[k].sort(key=lambda e:e['t'])
def font(s):return ImageFont.truetype('C:/Windows/Fonts/consola.ttf',s)
COLORS=dict(trompeta='#ffb35d',garganta='#f7a0c3',sax='#8bddca',sinte='#8bbdf9',doble='#bcafff',chelo='#ddd07b',voces='#ec8a78',bajo='#b5a0e8')
def visual(label,energy=None):
 im=Image.new('RGB',(1200,630),'#121621');d=ImageDraw.Draw(im);d.text((30,20),'LA BOCA ENCIENDE EL COBRE',font=font(39),fill='#fff0db');d.text((32,74),label,font=font(17),fill='#eda48c')
 for a,z,name,bpm in SECTIONS:
  x=42+START[a]/DUR*1116;d.line((x,118,x,526),fill='#353d50');d.text((x,543),name[:8],font=font(10),fill='#cdc6d3')
 for k,c in COLORS.items():
  for e in P[k]:
   x=42+e['t']/DUR*1116;y=483-(e['m']-34)*6;d.line((x,y,x+max(1,e['dur']/DUR*1116),y),fill=c,width=2)
 if energy is not None:
  for j,v in enumerate(energy):d.line((42+j,516,42+j,516-v*23),fill='#e6bb8a')
 d.text((32,583),'trompeta · garganta · sax · chelo · voces · sinte · bajo',font=font(15),fill='#ded3d8');d.text((32,608),'Canek Zapata · 19 octubre 2026 · semilla 19102743',font=font(13),fill='#c7c0ce');return im
def png(path,im):
 with path.open('xb') as f:im.save(f,'PNG')
def writejson(path,obj):
 with path.open('x',encoding='utf8') as f:json.dump(obj,f,ensure_ascii=False,indent=2)
def main():
 lead();im=visual('01 · cuatro frases, contracanto y desarrollo del lead')
 buf=io.BytesIO();im.save(buf,'PNG');nonce=uuid.uuid4().hex;full=hashlib.sha256(buf.getvalue()+Path(__file__).read_bytes()+(R/'producir.py').read_bytes()+nonce.encode()).hexdigest();tag=full[:12]
 out=R/f'la-boca-enciende-el-cobre-s{SEED}-{tag}';out.mkdir()
 for k in ['fuentes','render','proceso']:(out/k).mkdir()
 png(out/'proceso'/f'01-lead-s{SEED}-{tag}.png',im);writejson(out/'boceto-lead.json',P)
 orchestration();png(out/'proceso'/f'02-orquestacion-s{SEED}-{tag}.png',visual('02 · contrapunto, armonía, coro y cuerpo rítmico'));writejson(out/'partitura.json',P)
 sources=[Path(__file__),R/'producir.py',R/'fisicos.cjs',R/'IDEA.md',REPO/'lo-que-tapa-la-traspuesta/sintes2.py',REPO/'lo-que-tapa-la-traspuesta/motor/garganta.js']+[REPO/'objetos/motor'/f for f in ['metal.js','objeto.js','cuerda.js','piano.js']]+[REPO/'otra-vez-hasta-romper/kit.cjs',REPO/'catalogo-agua-que-habla/instrumentos-48b8a06e1049/motores/web.js']
 hashes={str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
 for j,p in enumerate(sources):
  with (out/'fuentes'/f'{j:02d}-{p.name}').open('xb') as f:f.write(p.read_bytes())
 writejson(out/'receta-inicial.json',dict(hash_ejecucion=full,nonce=nonce,semilla=SEED,fuentes=hashes,imagen_sha256=hashlib.sha256(buf.getvalue()).hexdigest()))
 print(out,flush=True)
if __name__=='__main__':main()
