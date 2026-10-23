from pathlib import Path
import numpy as np
import json,hashlib,uuid,io
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent;REPO=R.parent;SEED=19103281;Q=60/146
FORM=[(0,4,'I · caja de luz'),(4,16,'II · verso'),(16,24,'III · escalera'),(24,40,'IV · estribillo'),(40,48,'V · invención/drop'),(48,64,'VI · diálogo eléctrico'),(64,72,'VII · verso 2'),(72,80,'VIII · escalera 2'),(80,96,'IX · estribillo 2'),(96,104,'X · voces lejanas'),(104,116,'XI · estribillo arriba'),(116,120,'XII · salida')]
METERS=[(3.5 if b%2==0 else 4.5) if 96<=b<104 else 4 for b in range(120)]
START=[0.]
for meter in METERS:START.append(START[-1]+meter*Q)
D=START[-1]+2.4
def at(b,p=0):return START[b]+p*Q
def section(b):return next(n for a,z,n in FORM if a<=b<z)
def font(n):return ImageFont.truetype('C:/Windows/Fonts/consola.ttf',n)
def png(p,im):
 with p.open('xb') as f:im.save(f,'PNG')
def js(p,x):
 with p.open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def chord(b):
 trans=2 if b>=104 else 0
 if b<4 or 24<=b<40 or 40<=b<48 or 80<=b<96 or b>=104:
  name,notes=[('Cmaj9',[36,60,64,67,71,74]),('Am9',[33,59,60,64,67,71]),('Fmaj9',[29,57,60,64,67,72]),('G13',[31,59,62,65,69,76])][((b-(104 if b>=104 else 80 if b>=80 else 40 if b>=40 else 24 if b>=24 else 0))//2)%4]
 elif 16<=b<24 or 72<=b<80:
  name,notes=[('CmMaj9',[36,60,63,67,71,74]),('Fsharp7',[30,58,61,64,66,70]),('Am7b5',[33,60,63,67,69,72]),('Bflat13',[34,60,62,68,72,75])][((b-(72 if b>=72 else 16))//2)%4]
 elif 48<=b<64:
  name,notes=[('Cm9',[36,58,62,63,67,74]),('Abmaj9',[32,58,60,63,67,70]),('Fm9',[29,56,60,63,67,72]),('Galt',[31,59,63,65,68,73])][((b-48)//2)%4]
 elif 96<=b<104:name,notes=('octatónica',[36,60,61,63,66,69])
 else:name,notes=[('Cm9',[36,58,62,63,67,74]),('Abmaj9',[32,58,60,63,67,70]),('Fm9',[29,56,60,63,67,72]),('G7sus',[31,60,62,65,68,74])][((b-(64 if b>=64 else 4))//2)%4]
 return name+('+2' if trans else ''),[m+trans for m in notes]

def compose():
 P=dict(titulo='El sol tiene dientes',semilla=SEED,duracion=D,bpm=146,cuarto_s=Q,cierre=START[-1]+.25,secciones=[dict(t=START[a],fin=START[z],nombre=n,b=a,fin_b=z) for a,z,n in FORM],compases=[dict(b=b,t=START[b],fin=START[b+1],pulso=METERS[b],acorde=chord(b)[0]) for b in range(120)],frases=[],**{k:[] for k in ['sax','sinte','rhodes','juguete','pluck','marimba','bajo','fretless','bateria']},transformaciones=[])
 def ev(k,b,p,m,d,v=.7,**kw):P[k].append(dict(t=at(b,p),dur=d*Q,m=float(m),v=v,b=b,**kw))
 # Memorable seven-note hook; four cadential endings, not one loop copied through the song.
 hooks=[[76,79,81,79,76,74,72],[74,76,79,76,74,72,69],[72,74,76,79,81,79,76,74],[76,74,72,69,67,69,72]]
 verses=[[72,74,75,79,80,79,75],[79,75,74,72,68,67,72],[75,79,80,84,80,79,75],[74,75,79,75,74,72,67]]
 pres=[[75,78,79,81,82,81,79],[76,78,81,82,85,84,82],[79,81,82,84,85,84,81],[82,81,79,78,76,75,79]]
 def phrase(b,notes,kind='aire',family=0,gain=.72,choral=False):
  weights=np.array(([.45,.55,.9,.35,.6,.85,2.0,.45,.6,.7]*2)[:len(notes)],float)
  if family%3==1:weights=np.roll(weights,2);weights[-1]=1.5
  if family%3==2:weights[1]*=1.5;weights[-1]=2.3
  weights*=7.05/weights.sum();t=at(b,[.0,.25,.125,.5][family%4]);events=[]
  for j,(m,d) in enumerate(zip(notes,weights)):
   e=dict(t=float(t),dur=float(d*Q*.97),nota=float(m),texto=['la','ri','a','mi','u','ya','a','i'][j%8])
   if choral:e['voicing']=chord(min(119,b+j))[1][1:5]
   events.append(e);t+=d*Q
  P['frases'].append(dict(id=len(P['frases']),bar=b,voz=kind,nivel=gain,seccion=section(b),eventos=events))
 for a,z in [(4,16),(64,72)]:
  for j,b in enumerate(range(a,z,2)):phrase(b,verses[(j+(2 if a==64 else 0))%4],family=j,gain=.7)
 for a in [16,72]:
  for j,b in enumerate(range(a,a+8,2)):phrase(b,pres[j],family=j+1,gain=.73)
 for a,z in [(24,40),(80,96),(104,116)]:
  for j,b in enumerate(range(a,z,2)):
   notes=hooks[j%4].copy();tr=2 if a==104 else 0
   if a==80 and j in [2,6]:notes[-3:]=[79,76,72]
   if a==104 and j==5:notes[-3:]=[74,72,72]
   phrase(b,[m+tr for m in notes],family=j,gain=.81)
   if j%2==0:
    c=chord(b)[1];phrase(b,[c[2],c[3],c[4]],'cobre-luz',j,.58,True)
 # Sparse hook fragments in the drop leave room for two independent instrumental voices.
 phrase(42,[79,81,79,76,72],family=2,gain=.6);phrase(46,[76,74,72],'cobre-luz',0,.55)
 # Spatial interlude: own vowels, never somebody else's sampled voice.
 for j,b in enumerate([96,98,100]):phrase(b,[[72,75,78],[79,78,75],[81,79,78]][j],'palo',j,.45)
 phrase(116,[78,81,83,81,78,76,74],family=0,gain=.75)
 # A modal toy states the hook in the six-second intro.
 for b in [0,2]:
  for j,m in enumerate(hooks[b//2]):ev('juguete',b,j*.48,m,.45,.65 if j==0 else .5)
 # Comping, bass and orchestral chords have different attacks and leave vocal space.
 for b in range(120):
  name,c=chord(b);chor=24<=b<40 or 80<=b<96 or 104<=b<116;pre=16<=b<24 or 72<=b<80;jazz=48<=b<64;bridge=96<=b<104
  if not bridge and b%2==0:
   for j,m in enumerate(c[1:5]):ev('rhodes',b,.12+j*.055,m,5.5 if chor else 3.2,.45,pan=-.32+j*.18)
  if jazz or pre:
   for j,m in enumerate(c[2:5]):ev('rhodes',b,2.65+j*.045,m,.75,.36,pan=-.2+j*.18)
  if chor and b%4==3:
   for j,m in enumerate([c[-1]+12,c[3]+12,c[2]+12]):ev('juguete',b,2.6+j*.4,m,.6,.34)
  if not bridge and not jazz:
   root=c[0]
   while root<33:root+=12
   if chor or 40<=b<48:pattern=[(0,root,1.35),(1.75,root,.7),(3.0,root+7,.65)] if b%2==0 else [(.25,root,1.15),(2.0,root+12,.65),(3.25,root,.55)]
   else:pattern=[(0,root,2.5)] if b%2==0 else [(1.5,root,1.5)]
   if b<2:pattern=[]
   for j,(p,m,d) in enumerate(pattern):ev('bajo',b,p,m,d,.75,rate=[2,3,1,4][(b+j)%4],growl=bool(chor or 40<=b<48))
  if jazz:
   root=c[0]
   for p,step,d in [(0,0,.8),(1.25,7,.55),(2.0,10,.7),(3.1,12,.55)]:ev('fretless',b,p,root+step,d,.68,glis=False)
  if b<2 or bridge:continue
  # Half-time dubstep in choruses/drop; broken nu-jazz in the dialogue; straight pop in verses.
  for st in range(16):
   beat=st/4;tt=at(b,beat+(.035 if jazz and st%2 else 0))
   def hit(k,g,pan=0):P['bateria'].append(dict(t=tt,pieza=k,g=g,pan=pan,b=b))
   if chor or 40<=b<48:
    if st in ([0,6,11] if b%4==2 else [0,7,14] if b%4==3 else [0,10]):hit('kick',.9)
    if st==8:hit('snare',.78);hit('clap',.3)
    if st%2==0:hit('hat',.16 if st%4 else .21,.24)
    if b%4==3 and st in [13,14,15]:hit('hat',.11+st*.005,-.2)
   elif jazz:
    if st in [0,7,10]:hit('kick',.58)
    if st in [4,12]:hit('snare',.38)
    if st in [3,9,15]:hit('rim',.17,-.2)
    if st in [0,3,6,8,11,14]:hit('openhat',.1,.3)
   else:
    if st in [0,6,10]:hit('kick',.66)
    if st in [4,12]:hit('snare',.56)
    if st%2==0:hit('hat',.12+.035*(st%4==0),.2)
   if b%8==7 and st in [13,15]:hit('tomlo',.35,-.15)
   if b%8==0 and st==0:hit('spray',.15,.5)
  if pre and b%2==1:
   for beat in [2.5,2.75,3.0,3.25,3.5,3.75]:P['bateria'].append(dict(t=at(b,beat),pieza='snare',g=.15+.08*(beat-2.5),pan=0,b=b))
 # Original subject + independent counter-subject, with documented transformations.
 subject=[60,67,64,62,60,69,67,64];rhythm=[.5,.5,.75,.25,.5,.5,.5,.5]
 counter=[72,71,69,67,65,64];cr=[.75,.25,1,.5,.75,.75]
 def line(k,b,notes,durations,tr=0,delay=0,stretch=1,tag=''):
  t=at(b,delay)
  for j,(m,d) in enumerate(zip(notes,durations)):
   P[k].append(dict(t=t,dur=d*Q*stretch*.88,m=float(m+tr),v=.65 if j%3 else .8,b=b,pan=-.3 if k=='pluck' else .3));t+=d*Q*stretch
  P['transformaciones'].append(dict(t=at(b,delay),voz=k,operacion=tag,notas=[m+tr for m in notes],aumentacion=stretch))
 line('pluck',40,subject,rhythm,tag='sujeto original');line('marimba',40,counter,cr,tag='contrasujeto propio')
 line('marimba',41,subject,rhythm,tr=7,tag='respuesta a quinta');line('pluck',41,counter,cr,tr=-12,tag='contrasujeto grave')
 line('pluck',42,[120-m for m in subject],rhythm,tr=12,tag='inversión alrededor de do4')
 line('marimba',43,subject[::-1],rhythm[::-1],tag='retrógrado')
 line('pluck',44,subject,rhythm,stretch=2,tag='aumentación al doble');line('marimba',44,counter,cr,tr=12,tag='contrapunto agudo')
 for j,(m,d) in enumerate(zip(subject,rhythm)):
  ev('pluck' if j%2==0 else 'marimba',46,sum(rhythm[:j]),m+12,d*.8,.7,pan=-.35 if j%2==0 else .35)
 line('pluck',47,subject[:4],rhythm[:4],tr=12,tag='cabeza del sujeto');line('marimba',47,counter[:3],cr[:3],tr=-12,delay=1.5,tag='estrecho')
 # Added central sixteenth: 2+2+3+2+2 is identical read forward and backward.
 for b in [17,21,73,77]:line('juguete',b,[72,75,78,75,72],[.5,.5,.75,.5,.5],delay=.25,tag='ritmo no retrogradable 2+2+3+2+2')
 # Synth/sax dialogue: 4-bar call, 4-bar answer, 2-bar trades, then one-bar trades and unison.
 jazzphrases=[[(0,72,.65),(.8,74,.3),(1.3,75,.45),(2.05,79,.7),(3.1,78,.25),(3.5,79,.35)],
 [(0,80,.8),(1.1,79,.45),(1.9,75,.65),(2.8,74,.3),(3.3,72,.55)],
 [(.25,67,.4),(.9,70,.3),(1.4,72,.6),(2.25,75,.5),(3.1,74,.6)],
 [(0,71,.3),(.45,73,.25),(.95,74,.55),(1.7,79,.65),(2.6,78,.25),(3.1,79,.65)]]
 for b in range(48,64):
  who=('sax' if b<52 else 'sinte' if b<56 else 'sax' if b<58 else 'sinte' if b<60 else 'sax' if b%2==0 else 'sinte')
  for j,(beat,m,d) in enumerate(jazzphrases[(b-48)%4]):ev(who,b,beat,m,d,.66 if j%3 else .82,lengua=j%3==0,glis=False)
  if b>=62:
   for j,(beat,m,d) in enumerate(jazzphrases[(b-48)%4][:3]):ev('sinte' if who=='sax' else 'sax',b,beat,m-12,d,.5,lengua=j==0,glis=False)
  # A lower subject head circulates under the solo, then rests a bar.
  if b%4==0:line('marimba',b,subject[:4],rhythm[:4],tr=-12,delay=2,tag='memoria bajo el diálogo')
 for a,z in [(24,40),(80,96),(104,116)]:
  for b in range(a+3,z,4):
   c=chord(b)[1]
   for j,m in enumerate([c[3]+12,c[2]+12,c[1]+12]):ev('sinte',b,2.6+j*.4,m,.35,.48,glis=False)
 # Decisive final tonic, followed by its own short decay.
 for j,m in enumerate([50,62,66,69,73,78]):ev('rhodes',119,2,m,1.7,.65,pan=-.4+j*.15)
 for j,m in enumerate([74,78,81]):ev('juguete',118,j*.65,m,.55,.54)
 P['bajo']=[e for e in P['bajo'] if e['b']!=119];ev('bajo',119,2,38,1.8,.8,rate=1,growl=False)
 P['bateria']=[e for e in P['bateria'] if not(e['b']==119 and e['t']>=at(119,2))]
 for piece,g in [('kick',.85),('clap',.3),('spray',.18)]:P['bateria'].append(dict(t=at(119,2),pieza=piece,g=g,pan=0,b=119))
 for k in ['sax','sinte','rhodes','juguete','pluck','marimba','bajo','fretless','bateria']:P[k].sort(key=lambda e:e['t'])
 return P

def preview(P,label):
 im=Image.new('RGB',(1800,1100),'#0b0b10');d=ImageDraw.Draw(im);d.text((30,18),'EL SOL TIENE DIENTES',font=font(42),fill='#f1e7d5');d.text((32,80),label,font=font(18),fill='#c5b7df')
 for s in P['secciones']:
  x=95+s['t']/D*1660;d.line((x,133,x,425),fill='#3c3850');d.text((x+4,138),s['nombre'].split(' · ')[0],font=font(13),fill='#b7aac8')
 for f in P['frases']:
  for e in f['eventos']:
   x=95+e['t']/D*1660;y=418-(e['nota']-28)*4.4;d.line((x,y,x+e['dur']/D*1660,y),fill={'aire':'#f4a2d1','cobre-luz':'#bca4ed','palo':'#9ebfb7'}[f['voz']],width=3)
 for k,col in [('sax','#f1b56a'),('sinte','#6cdecd'),('pluck','#94b8ed'),('marimba','#b5d67a'),('bajo','#be7fc0')]:
  for e in P[k]:
   x=95+e['t']/D*1660;y=418-(e['m']-28)*4.4;d.line((x,y,x+max(1,e['dur']/D*1660),y),fill=col,width=2)
 d.text((32,465),'voz rosa · coro lila · sax ocre · sinte turquesa · contrapunto azul/verde · bajo violeta',font=font(17),fill='#d5ccdc');d.text((32,520),'Audio y ocupación · se añaden después de renderizar',font=font(22),fill='#f1e7d5')
 d.text((32,1060),'Canek Zapata · 19 octubre 2026 · 146 BPM / half-time 73 · semilla 19103281',font=font(17),fill='#b7aac8');return im

def init():
 P=compose();im=preview(P,'01 · gancho pop, sujeto/contrasujeto, diálogo y regreso un tono arriba');buf=io.BytesIO();im.save(buf,'PNG')
 paths=[Path(__file__),R/'producir.py',R/'fisicos.cjs',R/'IDEA.md',REPO/'lo-que-tiembla-adentro/voces.cjs',REPO/'lo-que-tiembla-adentro/producir.py',REPO/'cuento-en-siete/sintes.py',REPO/'lo-que-tapa-la-traspuesta/sintes2.py',REPO/'objetos/motor/objeto.js',REPO/'otro-arriba/analizar-densidad.py',REPO/'otra-vez-hasta-romper/kit.cjs']
 nonce=uuid.uuid4().hex;full=hashlib.sha256(buf.getvalue()+b''.join(p.read_bytes() for p in paths)+nonce.encode()).hexdigest();tag=full[:12];out=R/f'el-sol-tiene-dientes-s{SEED}-{tag}';out.mkdir()
 for k in ['render','fuentes','proceso']:(out/k).mkdir()
 js(out/'partitura.json',P);png(out/'proceso'/f'01-escritura-s{SEED}-{tag}.png',im)
 for j,p in enumerate(paths):
  with (out/'fuentes'/f'{j:02d}-{p.name}').open('xb') as f:f.write(p.read_bytes())
 js(out/'receta-inicial.json',dict(hash_ejecucion=full,nonce=nonce,semilla=SEED,imagen_sha256=hashlib.sha256(buf.getvalue()).hexdigest(),fuentes={str(p.relative_to(REPO)):sha(p) for p in paths},fecha='2026-10-19'));print(out,flush=True)
if __name__=='__main__':init()
