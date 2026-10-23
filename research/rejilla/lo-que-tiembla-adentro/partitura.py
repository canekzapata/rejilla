from pathlib import Path
import json,hashlib,uuid,io
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;REPO=R.parent;SEED=19103117;Q=60/66
FORM=[(0,5,'I · germen',4),(5,17,'II · canto',4),(17,27,'III · paredes',4),(27,35,'IV · claro',3.5),(35,47,'V · vuelo interior',4),(47,55,'VI · adentro',4)]
START=[0.]
for b in range(55):START.append(START[-1]+next(s[3] for s in FORM if s[0]<=b<s[1])*Q)
D=START[-1]+3;CENTER=440*2**((54-69)/12)
def at(b,p=0):return START[b]+p*Q
def sec(b):return next(s[2] for s in FORM if s[0]<=b<s[1])
def js(p,obj):
 with p.open('x',encoding='utf8') as f:json.dump(obj,f,ensure_ascii=False,indent=2)
def png(p,im):
 with p.open('xb') as f:im.save(f,'PNG')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def font(n):return ImageFont.truetype('C:/Windows/Fonts/consola.ttf',n)

def compose():
 P=dict(titulo='Lo que tiembla adentro',semilla=SEED,duracion=D,bpm=66,centro_hz=CENTER,cuarto_s=Q,secciones=[dict(t=START[a],fin=START[z],nombre=n,compas='7/8' if meter==3.5 else '4/4',b=a,fin_b=z) for a,z,n,meter in FORM],frases=[],pajaros=[],agua=[],madera=[],paredes=[])
 # A five-note cantabile, with a semitone shadow and an opening toward the fifth.
 A=[(0,66,1.5,'u'),(1.65,66.18,.9,'o'),(2.7,65.82,1.1,'a'),(4.0,69.8631,1.1,'e'),(5.35,66,2.0,'a')]
 B=[(.25,73.01955,1.4,'i'),(1.85,71.0,.8,'e'),(2.85,69.8631,1.5,'a'),(4.55,66.08,1.0,'o'),(5.75,66,1.8,'u')]
 C=[(0,66,2.0,'u'),(2.15,65,.65,'a'),(2.95,66.08,.8,'e'),(4.0,72.76,1.15,'i'),(5.4,71.6883,1.9,'o')]
 def phrase(b,who,notes,level=.7,label=''):
  P['frases'].append(dict(id=len(P['frases']),bar=b,voz=who,seccion=sec(b),nivel=level,gesto=label,eventos=[dict(t=at(b,p),dur=d*Q,nota=m,texto=syll) for p,m,d,syll in notes]))
 def bird(b,beat,seq,v=.6,voice=0):
  notes=[[dt*Q,m,dd*Q] for dt,m,dd in seq];dur=max(x[0]+x[2] for x in notes)+.05
  P['pajaros'].append(dict(t=at(b,beat),dur=dur,tipo='canto',m=seq[0][1],v=v,voz=voice,notas=notes))
 # Vocalists exchange phrases. Real rests and unequal turns prevent an unbroken lead blanket.
 for b,notes in [(5,A),(9,B),(13,A),(17,C),(21,B),(25,[(0,66,1.6,'a'),(1.8,66.23,1.7,'e'),(3.7,66,2.5,'u')]),(35,A),(39,C),(43,B)]:
  phrase(b,'aire',notes,.72,'cantabile')
 for b,notes in [(7,[(.4,61.01955,2.1,'u'),(2.75,64.8631,1.3,'a'),(4.35,66,2.8,'o')]),
                 (11,[(0,66,1.9,'o'),(2.1,65.86,1.2,'e'),(3.5,61.01955,3.1,'u')]),
                 (19,[(.1,66,1.4,'a'),(1.65,69.8631,1.5,'e'),(3.35,71.6883,1.3,'i'),(4.9,66,2.4,'u')]),
                 (23,[(0,64.8631,2,'o'),(2.2,66,2.1,'a'),(4.5,66.16,2.5,'e')]),
                 (29,[(.25,66,2.4,'u'),(2.9,65.84,1.5,'o'),(4.7,66.04,1.8,'a')]),
                 (37,[(0,61.01955,1.6,'u'),(1.85,66,1.4,'a'),(3.5,69.8631,1.3,'e'),(5.0,66,2.4,'o')]),
                 (41,[(0,66.04,2.2,'a'),(2.4,71.6883,1.4,'i'),(4.0,69.8631,1.2,'e'),(5.4,66,2.1,'u')]),
                 (47,[(0,66,2.4,'a'),(2.65,65.88,1.8,'o'),(4.7,66,2.4,'u')]),
                 (51,[(0,66.06,2.7,'u'),(3,66,4.2,'u')])]:phrase(b,'cobre-luz',notes,.65,'respuesta cantada')
 # A brief overlapping counterphrase only at the crest, then the ensemble opens again.
 phrase(45,'aire',[(.25,73.01955,1.8,'i'),(2.3,71.6883,1.6,'e'),(4.2,69.8631,1.2,'a'),(5.6,66,1.9,'o')],.68,'retorno transformado')
 phrase(45,'cobre-luz',[(0,61.01955,2.1,'u'),(2.5,64.8631,2.3,'o'),(5.1,66,2.4,'a')],.54,'contracanto independiente')
 for b,txt in [(3,'ta ka tum'),(15,'despacio'),(26,'tiembla'),(27,'ta ka'),(31,'escucha'),(33,'ta tum'),(46,'vuelve'),(49,'despacio')]:
  syll=txt.split() if ' ' in txt else {'despacio':['des','pa','cio'],'tiembla':['tiem','bla'],'escucha':['es','cu','cha'],'vuelve':['vuel','ve']}[txt]
  phrase(b,'palo',[(.3+j*.6,57+[0,2,7][j%3],.43,s) for j,s in enumerate(syll)],.62,'madera articulada: '+txt)
 for b,beat,notes in [(1,1.2,[(0,78,1.2),(1.4,78.15,.8),(2.5,81.86,.7)]),
 (6,2.6,[(0,85.01955,.35),(.5,83.69,.3),(.95,81.86,.65)]),(8,2.4,[(0,78,.6),(.8,79,.25),(1.2,78.07,.8)]),
 (12,2.9,[(0,81.86,.35),(.55,85.01955,.7)]),(16,.4,[(0,78,.9),(1.2,76.86,.4),(1.8,78.1,1.4)]),
 (18,2.6,[(0,85.01955,.25),(.4,88.69,.3),(.95,85.01955,.85)]),(22,2.5,[(0,81.86,.5),(.8,78,.8)]),
 (28,.3,[(0,78,1.0),(1.3,78.12,1.1)]),(30,.4,[(0,90,.7),(.9,88.69,.4),(1.5,85.01955,1.1)]),
 (32,1.7,[(0,81.86,.6),(.85,78,.85)]),(34,0,[(0,78,.4),(.6,81.86,.45),(1.2,85.01955,.9)]),
 (36,2.8,[(0,85.01955,.35),(.5,88.69,.45),(1.1,90,.65)]),(38,2.5,[(0,85.01955,.4),(.6,81.86,.5),(1.3,78,.8)]),
 (42,2.2,[(0,78,.6),(.8,79,.3),(1.3,78,.9)]),(44,2.6,[(0,85.01955,.35),(.5,86,.25),(.95,85.01955,.8)]),
 (48,2.5,[(0,81.86,.6),(.9,78,1.2)]),(50,2.0,[(0,78,1.1),(1.35,78.08,1.2)]),(53,.4,[(0,78,2.7)])]:bird(b,beat,notes,.55 if b<35 else .66)
 # Rare simultaneous second bird has a slower, lower independent trajectory.
 bird(40,.4,[(0,73.01955,1.5),(1.9,76.8631,1),(3.2,73.01955,1.5)],.47,1)
 for b in range(55):
  name=sec(b);meter=3.5 if 27<=b<35 else 4
  beats=([.1] if b<5 else [.1,2.0] if b<17 else [0,1.75,3.2] if b<27 else [] if b<35 else [0,2.25] if b<47 else [.4] if b%2==0 else [])
  # The explicit branch keeps the clear genuinely sparse, without a hidden generic drum kit.
  if 27<=b<35:beats=[.7] if b in [27,30,33] else []
  if b>=51:beats=[.4] if b==52 else []
  for j,beat in enumerate(beats):P['agua'].append(dict(t=at(b,beat),tipo='burbujeo' if j==0 else 'gota',m=42 if j==0 else [66,73.01955,69.8631][b%3],dur=.45,v=.5 if j==0 else .34))
  if b in [4,16,26,34,46]:P['agua'].append(dict(t=at(b,2.1),tipo='palo',m=74,dur=1.0,v=.22,tasa=75))
  if b>=5 and b<47 and not 27<=b<35:
   for beat in ([1.0,2.75] if b%3==0 else [1.4] if b%3==1 else [2.6,3.3]):P['madera'].append(dict(t=at(b,beat),m=54+([0,7,12][b%3]),v=.23,dur=.32))
 for f in P['frases']:
  if f['voz']=='palo':
   for e in f['eventos']:P['madera'].append(dict(t=e['t']-.015,m=e['nota'],v=.7,dur=e['dur']))
 # Paired walls do different work. No wall in the first 3 clear bars; only one thread then returns.
 configs=[(0,5,'izquierda',[2,4],.5,8),(5,17,'izquierda',[2,3,7],.38,10),(17,27,'izquierda',[2,3,4,7,9,11,13],.85,22),
          (19,27,'derecha',[3,4,5,6,7],.72,19),(30,35,'izquierda',[2],.2,4),
          (35,47,'izquierda',[2,3,4,7,9,11,13],.65,15),(35,47,'derecha',[3,4,5,6,7,9],.65,17),
          (47,51,'derecha',[4,5,6,7],.36,7),(51,55,'izquierda',[2],.32,3)]
 for a,z,side,ratios,v,cents in configs:P['paredes'].append(dict(t=START[a],fin=START[z],lado=side,indices=ratios,nivel=v,desvio_cents=cents,familia='subarmonica' if side=='derecha' else 'armonica'))
 for k in ['pajaros','agua','madera']:P[k].sort(key=lambda e:e['t'])
 P['cierre']=START[-1]+.4;return P

def preview(P,label):
 im=Image.new('RGB',(1600,1000),'#0b0b10');d=ImageDraw.Draw(im);d.text((28,18),'LO QUE TIEMBLA ADENTRO',font=font(37),fill='#eee8da');d.text((30,72),label,font=font(18),fill='#b1afc4')
 for s in P['secciones']:
  x=100+s['t']/D*1450;d.line((x,120,x,410),fill='#3c3c4f');d.text((x+4,123),s['nombre'],font=font(14),fill='#aaa8bc')
 for f in P['frases']:
  for e in f['eventos']:
   x=100+e['t']/D*1450;y=390-(e['nota']-40)*5;d.line((x,y,x+e['dur']/D*1450,y),fill={'aire':'#ee9abb','cobre-luz':'#a28dea','palo':'#d7b276'}[f['voz']],width=3)
 for e in P['pajaros']:
  for dt,m,du in e['notas']:
   x=100+(e['t']+dt)/D*1450;y=390-(m-40)*5;d.line((x,y,x+du/D*1450,y),fill='#83d8c0',width=2)
 d.text((30,440),'rosa · vocoder aire     violeta · vocoder cobre-luz     verde · pájaros     ocre · palos',font=font(16),fill='#d5cfdf')
 d.text((30,490),'Sonido y densidad · el espectrograma se añade después de renderizar',font=font(20),fill='#eee8da')
 d.text((30,960),'Canek Zapata · 19 octubre 2026 · 66 BPM · 4/4 y claro en 7/8 · semilla 19103117',font=font(16),fill='#aaa8bc');return im

def init():
 P=compose();im=preview(P,'01 · cantabile, relevos, claro sin paredes y retorno transformado');buf=io.BytesIO();im.save(buf,'PNG')
 paths=[Path(__file__),R/'producir.py',R/'fisicos.cjs',R/'voces.cjs',R/'IDEA.md',REPO/'cuento-en-siete/sintes.py',REPO/'otro-arriba/analizar-densidad.py']+[REPO/'objetos/motor'/x for x in ['objeto.js','pajaro.js','agua.js']]+[REPO/'inferencia/vendor/difonos/runtime'/x for x in ['g2p.js','difonos.js']]
 nonce=uuid.uuid4().hex;full=hashlib.sha256(buf.getvalue()+b''.join(p.read_bytes() for p in paths)+nonce.encode()).hexdigest();tag=full[:12];out=R/f'lo-que-tiembla-adentro-s{SEED}-{tag}';out.mkdir()
 for name in ['render','fuentes','proceso']:(out/name).mkdir()
 js(out/'partitura.json',P);png(out/'proceso'/f'01-escritura-s{SEED}-{tag}.png',im)
 for i,p in enumerate(paths):
  with (out/'fuentes'/f'{i:02d}-{p.name}').open('xb') as f:f.write(p.read_bytes())
 js(out/'receta-inicial.json',dict(hash_ejecucion=full,nonce=nonce,semilla=SEED,imagen_sha256=hashlib.sha256(buf.getvalue()).hexdigest(),fuentes={str(p.relative_to(REPO)):sha(p) for p in paths},fecha='2026-10-19'));print(out,flush=True)
if __name__=='__main__':init()
