from pathlib import Path
import json,hashlib,uuid,io
import numpy as np
from PIL import Image,ImageDraw,ImageFont

R=Path(__file__).resolve().parent;REPO=R.parent;SEED=19102819
SECTIONS=[(0,4,'umbral',104),(4,12,'verso 1',104),(12,20,'pre 1',108),(20,36,'coro 1',112),(36,40,'metal',112),(40,48,'verso 2',104),(48,56,'pre 2',108),(56,72,'coro 2',116),(72,80,'puente',96),(80,88,'coro final',112),(88,92,'regalo',100)]
def section(b):return next(s for s in SECTIONS if s[0]<=b<s[1])
START=[0.]
for b in range(92):START.append(START[-1]+240/section(b)[3])
D=START[-1]+1.6
def at(b,p=0):return START[b]+p*60/section(b)[3]
CH={'D':[50,61,64,66,69],'Bm':[47,57,61,62,66],'G':[43,57,59,62,66],'A':[45,55,59,61,66],'Bb':[46,57,60,62,65],'Gm':[43,57,58,62,65],'Em':[40,55,59,62,66],'Fs':[42,57,58,61,64]}
def chord(b):
 name=(['Em','A'][b%2] if b<4 else ['D','Bm','G','A'][((b-4)//2)%4] if b<12 else ['Em','G','Bb','A'][((b-12)//2)%4] if b<20 else ['D','A','Bm','G','D','A','G','A'][((b-20)//2)%8] if b<36 else ['G','A'][((b-36)//2)%2] if b<40 else ['Bm','G','D','A'][((b-40)//2)%4] if b<48 else ['Em','G','Gm','A'][((b-48)//2)%4] if b<56 else ['D','A','Bm','G','D','A','G','Gm'][((b-56)//2)%8] if b<72 else ['Bm','Bb','Gm','Fs'][((b-72)//2)%4] if b<80 else ['D','A','G','Gm'][((b-80)//2)%4] if b<88 else ['D','G','D','D'][b-88])
 return name,CH[name]
P=dict(titulo='Otro arriba',semilla=SEED,duracion=D,frases=[],**{k:[] for k in ['trompeta','garganta','sax','chelo','piano','rhodes','bajo','sinte','voces','bateria']},compases=[dict(b=b,t=START[b],fin=START[b+1],bpm=section(b)[3],acorde=chord(b)[0]) for b in range(92)],secciones=[dict(b=a,fin_b=z,nombre=n,t=START[a],fin=START[z],bpm=bpm) for a,z,n,bpm in SECTIONS])
# Explicit syllables retain written accents and melodic stress. _ is a rest, never pronounced.
VERSE1=[('En el aceite del charco','en el a cei te del char co',[62,64,66,69,67,66,64,62]),('la noche aprende a doblar','la no che a pren de a do blar',[64,66,67,66,69,67,66,64,61]),('La luz que sale del vidrio','la luz que sa le del vi drio',[62,66,64,67,69,67,66,64]),('se queda mirando igual','se que da mi ran do i gual',[64,66,69,67,66,64,61,62])]
PRE1=[('Si este suelo me sostiene','si es te sue lo me sos tie ne',[64,66,67,71,69,67,66,69,67]),('¿por qué tiembla al verte entrar?','por qué tiem bla al ver te en trar',[66,69,71,69,67,71,73,71,69]),('Algo cambia de costado','al go cam bia de cos ta do',[65,67,70,69,67,65,69,70]),('sin cambiarse de lugar','sin cam biar se de lu gar',[67,69,71,73,71,69,73])]
CHORUS=[('Enséñame otro arriba','en sé ña me o tro a rri ba',[66,69,66,64,66,69,71,74,73]),('otra manera de caer','o tra ma ne ra de ca er',[71,69,66,67,69,66,64,62]),('Si me cambias de planeta','si me cam bias de pla ne ta',[66,67,69,73,71,69,67,66]),('que cambie éste también','que cam bie és te tam bién',[64,66,69,67,66,64,62]),('Quédate cerca un momento','qué da te cer ca un mo men to',[69,69,71,73,74,73,71,69,66]),('todavía no sé ver','to da ví a no sé ver',[67,69,71,73,71,69,67]),('hay un mundo en tu manera','hay un mun do en tu ma ne ra',[66,69,73,71,69,67,66,64,66]),('de moverme de lugar','de mo ver me de lu gar',[64,66,69,71,69,66,62])]
VERSE2=[('Tu sombra cruzó la mesa','tu som bra cru zó la me sa',[62,66,64,62,69,67,66,64]),('el vaso empezó a temblar','el va so em pe zó a tem blar',[64,67,66,64,66,69,67,64,62]),('Por un momento las cosas','por un mo men to las co sas',[62,64,66,69,67,66,69,67]),('tuvieron otro lugar','tu vie ron o tro lu gar',[64,66,67,66,64,61,62])]
PRE2=[('No hace falta que me expliques','no ha ce fal ta que me ex pli ques',[64,66,67,69,67,66,64,66,71,69]),('lo que empieza a aparecer','lo que em pie za a a pa re cer',[66,67,69,71,69,67,66,69,71,73]),('Acércate un poco más','a cér ca te un po co más',[65,70,69,67,65,67,69,70]),('quiero aprender a caer','quie ro a pren der a ca er',[67,69,71,73,71,69,71,73])]
BRIDGE=[('Arriba tenía otro nombre','a rri ba te ní a o tro nom bre',[69,71,69,67,70,69,67,65,66,64]),('Abajo empezaba a crecer','a ba jo em pe za ba a cre cer',[67,65,64,65,67,70,69,67,65,66]),('Había sitio en lo imposible','ha bí a si tio en lo im po si ble',[66,69,67,66,65,64,65,67,70,69,67]),('Yo estaba ahí también','yo es ta ba a hí tam bién',[66,65,64,61,62,66,65,66])]
FINAL=[CHORUS[0],('ya sé otra forma de caer','ya sé o tra for ma de ca er',[71,73,74,73,71,69,66,64,62]),('No me cambies de planeta','no me cam bies de pla ne ta',[66,67,69,73,71,69,67,66]),CHORUS[3]]
CODA=[('Ese sería el regalo','e se se rí a el re ga lo',[66,64,62,67,66,64,62,64,66]),('volver y volver a ver','vol ver y vol ver a ver',[64,66,64,62,64,61,62])]
def sung(b,row,idx,section_name):
 text,syllables,notes=row;syll=syllables.split();assert len(syll)==len(notes),(text,len(syll),len(notes))
 # Four rhythmic families with explicit local stress; each has a distinct pickup and end duration.
 weights=np.array(([.5,.75,.25,.5,.4,.35,.7,.45,.6,.35,.4]*2)[:len(syll)],float)
 for j,s in enumerate(syll):
  if any(a in s for a in 'áéíóú') or s in ['luz','char','blar','rar','gar','ver','rri','ran']:weights[j]*=1.45
 weights[-1]=1.55 if idx%3!=1 else 1.15
 total=[6.8,7.1,6.65,7.0][idx%4];weights*=total/weights.sum();pickup=[.25,0,.5,.15][idx%4];t=at(b,pickup);q=60/section(b)[3];events=[]
 for j,(s,m,w) in enumerate(zip(syll,notes,weights)):
  events.append(dict(t=round(t,6),dur=float(w*q*.94),texto=s,nota=float(m),acento=any(a in s for a in 'áéíóú'),peso=float(w)))
  t+=w*q
 assert t<START[b+2],(text,t,START[b+2])
 P['frases'].append(dict(id=len(P['frases']),bar=b,seccion=section_name,letra=text,nivel=.78 if 'coro' in section_name else .7,pan=0,eventos=events))
def ev(k,b,p,m,d,v=.7,**kw):P[k].append(dict(t=at(b,p),dur=d*60/section(b)[3],m=float(m),v=v,b=b,**kw))
def compose():
 for start,rows,name in [(4,VERSE1,'verso 1'),(12,PRE1,'pre 1'),(20,CHORUS,'coro 1'),(40,VERSE2,'verso 2'),(48,PRE2,'pre 2'),(56,CHORUS,'coro 2'),(72,BRIDGE,'puente'),(80,FINAL,'coro final'),(88,CODA,'regalo')]:
  for i,row in enumerate(rows):sung(start+i*2,row,i,name)
 # Responses begin only after the sung phrase ends; identity from the end of its melody.
 for f in P['frases']:
  last=f['eventos'][-1];end=last['t']+last['dur'];next_start=START[min(f['bar']+2,92)];space=next_start-end-.06
  if space>.2:
   for j,m in enumerate([last['nota']+7,last['nota']+4]):
    P['trompeta'].append(dict(t=end+.06+j*space*.45,dur=min(.22,space*.4),m=float(m),v=.6,tipo='lengua',vocal='a',frase='respuesta a '+str(f['id'])))
  # Independent quiet sax under selected sustained syllables; not a constant vocal doubling.
  if f['bar']%4==0 and f['seccion']!='puente':
   c=chord(f['bar'])[1];ev('sax',f['bar'],2.25,c[2],1.2,.52,lengua=True);ev('sax',f['bar']+1,1.5,c[3],.9,.5,lengua=False)
 for b in range(92):
  _,c=chord(b);name=section(b)[2];chor='coro' in name;bridge=name=='puente';root=c[0]
  if b<4:
   for j,m in enumerate([66,69,74] if b%2 else [69,67,66]):ev('trompeta',b,.35+j*.85,m,.6,.56,tipo='normal',vocal='u')
  if 36<=b<40:
   for j,(p,m,d) in enumerate([(0,c[-1],.7),(.9,c[-1]+3,.25),(1.4,c[-1]+2,.35),(2,c[-1]+7,.6),(3,c[-1]+5,.65)]):ev('trompeta' if b%2==0 else 'sinte',b,p,m,d,.72,tipo='normal',vocal='a')
  for p,step,d in ([(0,0,.7),(1.5,7,.35),(2.75,10,.45)] if not bridge else [(0,0,3.2)]):
   m=root+step
   while m>50:m-=12
   ev('bajo',b,p,max(35,m),d,.72,glis=p==2.75,liso=True)
  for p in ([.75,2.5,3.5] if chor else [.5,2.5] if not bridge else [.25]):
   for j,m in enumerate(c[1:]):ev('rhodes',b,p,m,.7 if not bridge else 2.5,.5,pan=-.4+j*.23)
  for p,m in [(1.75,c[2]+12),(3.25,c[3])]:
   if b%2 or bridge:ev('piano',b,p,m,.35,.42,tipo='martillo' if not bridge else 'caja')
  if bridge:
   ev('chelo',b,0,50+(b-72)*1.5,3.7,.6,tipo='tasto' if b<76 else 'armonico',casa=0)
   ev('garganta',b,.5,74-(b-72)*1.2,2.5,.4,fonemas=['u'],vocal='u')
  elif b%2:ev('chelo',b,1.25,root+12,.32,.5,tipo='pizz',casa=.45 if b>=56 else .15)
  # Drums preserve the dembow; the bridge keeps rim and selected hats instead of a blanket drop.
  if b<2:continue
  for st in range(16):
   p=st/4
   def hit(k,g):P['bateria'].append(dict(t=at(b,p),pieza=k,g=g,b=b))
   if st in ([0] if bridge else [0,8] if not chor else [0,7,10]):hit('kick',.8)
   if st in [6,14] and not bridge:hit('snare',.65)
   if st in [3,11]:hit('rim',.3 if not bridge else .2)
   if st%2==0 and (not bridge or st%4==2):hit('hat',.14+.03*(st%4==0))
   if chor and st in [4,12]:hit('clap',.3)
   if b%4==3 and st in [13,15] and not bridge:hit('tomlo',.3)
   if chor and b%4==2 and st in [1,9,15]:hit('hat',.095)
   if st==0 and b%8==4:hit('spray',.12)
 P['cierre']=START[-1]+.55
 for k in ['trompeta','garganta','sax','chelo','piano','rhodes','bajo','sinte','bateria']:P[k].sort(key=lambda e:e['t'])
def font(n):return ImageFont.truetype('C:/Windows/Fonts/consola.ttf',n)
def visual(label,orchestra=False,energy=None):
 im=Image.new('RGB',(1200,630),'#141924');d=ImageDraw.Draw(im);d.text((32,23),'OTRO ARRIBA',font=font(48),fill='#fff0d9');d.text((34,89),label,font=font(17),fill='#eaaabc')
 for a,z,n,bpm in SECTIONS:
  x=42+START[a]/D*1116;d.line((x,135,x,530),fill='#3c4357');d.text((x+1,542),n[:8],font=font(11),fill='#c8c0d5')
 for f in P['frases']:
  for e in f['eventos']:
   x=42+e['t']/D*1116;y=475-(e['nota']-46)*9;d.line((x,y,x+max(1,e['dur']/D*1116),y),fill='#f3abc2',width=3)
 if orchestra:
  for k,c in [('trompeta','#e8bf6c'),('sax','#86d9cd'),('chelo','#b4a4ed'),('bajo','#8bb6dc')]:
   for e in P[k]:
    x=42+e['t']/D*1116;y=490-(e['m']-33)*7;d.line((x,y,x+max(1,e['dur']/D*1116),y),fill=c,width=2)
 if energy is not None:
  for j,v in enumerate(energy):d.line((42+j,520,42+j,520-v*22),fill='#f5c17b')
 d.text((34,584),'voz · metal · vocalizaciones · Rhodes · chelo · dembow',font=font(16),fill='#e0d3df');d.text((34,608),'Canek Zapata · 19 octubre 2026 · semilla 19102819',font=font(13),fill='#c5bdcd');return im
def js(p,x):
 with p.open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
def png(p,im):
 with p.open('xb') as f:im.save(f,'PNG')
def main():
 compose();im=visual('01 · letra, acentos, respiraciones y melodía antes de sintetizar');buf=io.BytesIO();im.save(buf,'PNG');nonce=uuid.uuid4().hex;full=hashlib.sha256(buf.getvalue()+Path(__file__).read_bytes()+(R/'producir.py').read_bytes()+nonce.encode()).hexdigest();tag=full[:12];out=R/f'otro-arriba-s{SEED}-{tag}';out.mkdir()
 for k in ['render','fuentes','proceso']:(out/k).mkdir()
 js(out/'partitura.json',P);png(out/'proceso'/f'01-melodia-s{SEED}-{tag}.png',im);png(out/'proceso'/f'02-instrumentacion-s{SEED}-{tag}.png',visual('02 · respuestas en los huecos, contrapunto y acompañamiento',True))
 paths=[Path(__file__),R/'producir.py',R/'voz.cjs',R/'fisicos.cjs',REPO/'PROPUESTA-OTRO-ARRIBA.md',REPO/'la-boca-enciende-el-cobre/producir.py',REPO/'la-boca-enciende-el-cobre/fisicos.cjs',REPO/'lo-que-tapa-la-traspuesta/sintes2.py',REPO/'lo-que-tapa-la-traspuesta/motor/garganta.js']+[REPO/'objetos/motor'/n for n in ['metal.js','objeto.js','cuerda.js','piano.js']]+[REPO/'otra-vez-hasta-romper/kit.cjs',REPO/'inferencia/vendor/difonos/runtime/difonos.js',REPO/'inferencia/vendor/difonos/runtime/g2p.js']
 sources={str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
 for i,p in enumerate(paths):
  with (out/'fuentes'/f'{i:02d}-{p.name}').open('xb') as f:f.write(p.read_bytes())
 js(out/'receta-inicial.json',dict(hash_ejecucion=full,nonce=nonce,semilla=SEED,imagen_sha256=hashlib.sha256(buf.getvalue()).hexdigest(),fuentes=sources));print(out,flush=True)
if __name__=='__main__':main()
