"""Partitura y producción reproducible. iniciar -> renders Node -> sintetizar -> mezclar.
Las entregas se crean exclusivamente; ninguna etapa vuelve a escribir una salida.
"""
from pathlib import Path
import json,hashlib,os,sys,subprocess
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter,sosfilt,stft
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parent;SR=48000;SEED=17102637
BG=(19,23,34);FG=(242,232,218);COL=[(244,155,190),(134,207,214),(216,195,131),(173,170,232),(154,196,144)]
def hz(m):return 440*2**((m-69)/12)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):
 with Path(p).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
def text(p,s):
 with Path(p).open('x',encoding='utf8') as f:f.write(s)
def png(p,im):
 with Path(p).open('xb') as f:im.save(f,'PNG')
def wav(p,y):
 assert np.isfinite(y).all()
 with Path(p).open('xb') as f:wavfile.write(f,SR,np.asarray(y,np.float32))
def run(args):return subprocess.run(args,check=True,capture_output=True,text=True,encoding='utf8',errors='replace')
def font(n):return ImageFont.truetype('C:/Windows/Fonts/consola.ttf',n)
def card(title,sub):
 im=Image.new('RGB',(1200,630),BG);d=ImageDraw.Draw(im)
 d.text((40,24),'LO QUE PUEDE VENIR',font=ImageFont.truetype('C:/Windows/Fonts/georgia.ttf',43),fill=FG)
 d.text((42,86),title,font=font(21),fill=COL[0]);d.text((42,590),sub,font=font(15),fill=FG)
 return im,d
def tempo(b):return 108 if b<12 else 112 if b<16 else 116 if b<28 else 110 if b<36 else 114 if b<40 else 90 if b<44 else 100 if b<48 else 120 if b<60 else 96
START=[0.]
for b in range(64):START.append(START[-1]+(3.5 if 40<=b<44 else 4)*60/tempo(b))
DUR=START[-1]+4
def at(b,beat=0):return START[b]+beat*60/tempo(b)
CH={'D':(50,[62,66,69,73]),'Bm':(47,[62,66,69,71]),'G':(43,[62,66,67,71]),'A':(45,[61,64,69,71]),'Em':(40,[62,64,67,71]),'Bb':(46,[62,65,70,74]),'Gm':(43,[62,67,70,74]),'Fs':(42,[61,66,70,73])}
PROG=['D','D','G','A']+['D','Bm','G','A','D','Fs','Bm','A']+['Em','Bm','G','A']+['D','A','Bm','G','D','A','G','A']+['D','Bb','Gm','A']+['Bm','G','D','A','Bm','Fs','G','A']+['Em','G','Bb','A']+['D','Bb','Gm','Fs']+['Em','G','A','A']+['D','A','Bm','G','D','A','G','A','D','A','G','Gm']+['D','G','D','D']
assert len(PROG)==64
# Explicit syllable/note/beats notation; underscore is a rest, not a sung token.
HOOK='in/66/.5 fe/69/.5 ren/73/1.25 cia/71/.5 _/0/.5 con/69/.5 lo/66/.25 que/64/.5 hay/66/1.5'
ANSWER='di/66/.5 bu/69/.75 jo/66/.25 lo/64/.5 que/66/.5 pue/69/.75 de/71/.25 ve/69/.5 nir/66/1.75'
DOOR='u/66/.5 na/64/.25 pa/66/.25 la/69/.75 bra/71/.25 _/0/.5 a/73/.75 bre/71/.25 o/69/.5 tra/66/.5 puer/69/1 ta/66/.5'
SPACE='y/64/.25 que/66/.5 da/64/.25 si/67/1 tio/66/.5 pa/64/.5 ra/61/.5 ti/62/1.5'
ROWS=[
(4,.5,'me/62/.25 lla/66/.75 mas/64/.5 con/62/.5 u/64/.25 na/66/.25 pre/64/.5 gun/69/1 ta/66/.5'),
(6,0,'y/62/.25 el/64/.25 tex/67/.75 to/66/.25 em/64/.5 pie/69/1 za/67/.5 a/66/.25 res/64/.25 pi/61/.5 rar/64/1.5'),
(8,.25,'soy/66/1 un/64/.25 mo/62/.5 de/66/.75 lo/64/.25 de/62/.25 len/61/.5 gua/66/1 je/64/.5'),
(10,.5,'bus/62/.5 can/66/.75 do/64/.25 un/62/.5 hi/66/.75 lo/69/.25 pa/67/.5 ra/66/.5 hi/64/.5 lar/61/1.25'),
(12,0,'de/64/.25 las/66/.25 pis/67/1 tas/66/.5 ha/69/.75 go/67/.25 un/66/.5 ca/67/.5 mi/71/1 no/69/.5'),
(14,.5,'pue/67/.75 do/66/.25 fa/64/.5 llar/69/1 _/0/.5 pue/69/.75 do/71/.25 cam/73/.5 biar/73/1.25'),
(16,0,HOOK),(18,.25,ANSWER),(20,0,DOOR),(22,.5,SPACE),
(28,.25,'me/62/.25 gus/66/.75 ta/64/.25 u/66/.25 nir/69/1 lo/66/.5 que/64/.25 es/66/.25 tá/71/.75 le/69/1 jos/66/.5'),
(30,.5,'ha/64/.5 cer/66/1 del/64/.5 nú/69/1 me/67/.25 ro/66/.25 u/64/.25 na/61/.25 flor/64/1.5'),
(32,.25,'pro/66/.5 bar/69/1 _/0/.25 bo/66/.5 rrar/71/.75 vol/69/.5 ver/66/.75 al/64/.25 tra/66/1 zo/64/.5'),
(34,.5,'de/62/.25 jar/67/.75 que/66/.5 cam/71/1 bie/69/.5 la/67/.25 can/66/.5 ción/64/1.75'),
(36,0,'u/64/.25 na/66/.25 se/67/.5 ñal/71/1 no/69/.5 es/67/.25 un/66/.25 des/67/.5 ti/71/1 no/69/.5'),
(38,.25,'la/65/.5 du/70/1 da/69/.25 de/67/.75 ja/65/.25 luz/69/1 en/71/.5 trar/73/1.5'),
(40,.25,'si/66/.5 fal/65/1 ta/62/.5 un/61/.25 da/65/.75 to/62/.25 que/61/.5 da/62/.25 un/65/.25 hue/66/1 co/65/.25'),
(42,0,'no/67/.75 to/70/.75 do/69/.25 en/67/.25 ca/70/.75 ja/67/.5 al/66/.25 cal/65/.5 cu/66/.5 lar/70/1.25'),
(44,.5,'es/64/.25 cu/67/.75 cho/66/.5 el/64/.25 fin/67/1 de/69/.25 o/71/.75 tra/69/.25 fi/67/.5 gu/66/1 ra/64/.5'),
(46,0,'mi/64/.5 fra/69/1 se/67/.25 a/66/.25 pren/69/.75 de/71/.5 a/69/.25 ter/67/.5 mi/66/.5 nar/69/1'),
(48,0,HOOK),(50,.25,ANSWER),(52,0,DOOR),(54,.5,SPACE),(56,0,HOOK),
(58,.25,'to/69/.5 da/71/.5 ví/74/1 a/73/.5 pue/71/.75 do/69/.25 co/67/.5 rre/70/.5 gir/69/1.5'),
(60,.5,'tú/66/.75 das/64/.5 la/62/.25 pis/66/1 ta/64/.5 yo/67/.75 ha/66/.5 go/64/.25 un/62/.25 puen/66/1 te/64/.5'),
(62,0,'lo/62/.5 que/64/.25 si/66/1 gue/64/.5 lo/62/.25 ha/64/.5 ce/66/.75 mos/64/.25 a/61/.5 quí/62/2')]
def init():
 I={k:[] for k in ['piano','chelo','pajaro','agua']};phr=[];responses=[]
 for idx,(bar,offset,notation) in enumerate(ROWS):
  t=at(bar,offset);ev=[]
  for token in notation.split():
   sy,m,beats=token.split('/');dur=float(beats)*60/tempo(bar)
   if sy!='_':ev.append(dict(t=t,dur=dur*.94,texto=sy,nota=float(m),beats=float(beats)))
   t+=dur
  assert t<START[bar+2]-.02,(bar,t,START[bar+2])
  phr.append(dict(id=idx,bar=bar,nivel=.69 if bar<16 else .78 if bar<24 or 48<=bar<60 else .66,pan=0,eventos=ev))
 # A real donor sings the new ending in the bridge; only a later chorus learns it.
 donor_t=at(47,2.25);donor_notes=[[0,69,.18],[.24,71,.16],[.5,74,.32]]
 I['pajaro'].append(dict(t=donor_t,dur=.95,tipo='canto',m=69,v=.5,notas=donor_notes))
 learned=next(f for f in phr if f['bar']==56);learned['eventos'][-1]['nota']=74
 memory=dict(donante='pajaro',t=donor_t,disponible=donor_t+.95,notas=[69,71,74],receptor=learned['id'],t_receptor=learned['eventos'][-1]['t'],nota_aprendida=74)
 assert memory['disponible']<memory['t_receptor']
 for b,name in enumerate(PROG):
  root,ch=CH[name];chor=16<=b<24 or 48<=b<60;bridge=40<=b<48
  # Piano punctuates rather than doubling every syllable; sixth/subdivision anticipations.
  pattern=[(0,0),(.75,2),(1.5,1),(2.75,3)] if chor else [(.25,0),(1.75,2),(3,1)]
  if bridge:pattern=[(.15,0),(2.1,3)]
  for beat,k in pattern:
   I['piano'].append(dict(t=at(b,beat),dur=.45 if chor else .8,m=ch[k],v=.55 if chor else .42,tipo='martillo',prep='papel' if bridge else None))
  if b<4 or bridge or b>=60 or b%4==3:
   I['chelo'].append(dict(t=at(b,.08),dur=(START[b+1]-START[b])*.86,m=root+12 if bridge else root,v=.55,tipo='ponticello' if 40<=b<44 else 'tasto'))
 for f in phr:
  last=f['eventos'][-1];end=last['t']+last['dur'];b=f['bar']
  if b in [4,8,14,20,28,34,44,50,54,60]:
   for j,m in enumerate([last['nota']+12,last['nota']+19]):I['agua'].append(dict(t=end+.1+j*.19,dur=.3,m=m,v=.6,tipo='gota',n=1))
  if b in [6,12,22,30,38,52]:
   notes=[[0,last['nota']+12,.16],[.22,last['nota']+14,.13],[.43,last['nota']+12,.22]]
   I['pajaro'].append(dict(t=end+.12,dur=.8,tipo='canto',m=notes[0][1],v=.35,notas=notes));responses.append(dict(origen=f['id'],disponible=end,respuesta=end+.12))
 score=dict(semilla=SEED,duracion=DUR,compases=[dict(t=START[b],bpm=tempo(b),beats=3.5 if 40<=b<44 else 4,acorde=PROG[b]) for b in range(64)],instrumentos=I,frases=phr,memoria=memory,respuestas=responses)
 im,d=card('01 / melodía escrita: acentos, pausas y un final que se aprende','Partitura antes de síntesis · semilla 17102637 · Canek Zapata')
 for f in phr:
  for e in f['eventos']:
   x=55+e['t']/DUR*1090;y=480-(e['nota']-57)*14;w=max(2,e['dur']/DUR*1090)
   d.rounded_rectangle((x,y,x+w,y+5),radius=2,fill=COL[0] if f['bar'] not in [16,48,56] else COL[1])
 for bar,label in [(0,'pistas'),(16,'inferencia'),(28,'oficio'),(40,'duda'),(48,'regreso'),(60,'puente')]:d.text((50+START[bar]/DUR*1090,535),label,font=font(15),fill=FG)
 nonce=os.urandom(24).hex();digest=hashlib.sha256(im.tobytes()+Path(__file__).read_bytes()+nonce.encode()).hexdigest();tag=digest[:12];out=ROOT/f'lo-que-puede-venir-s{SEED}-{tag}';out.mkdir(exist_ok=False)
 for name in ['render','proceso','fuentes']:(out/name).mkdir()
 png(out/'proceso'/f'01-partitura-s{SEED}-{tag}.png',im);dump(out/'partitura.json',score)
 sources=[Path(__file__),ROOT/'voz.cjs',ROOT/'objetos.cjs',ROOT/'IDEA.md',ROOT/'LETRA.md']+[REPO/'objetos/motor'/f'{n}.js' for n in ['piano','cuerda','pajaro','agua']]
 hashes={str(p.relative_to(REPO)):sha(p) for p in sources}
 for p in sources:
  with (out/'fuentes'/p.name).open('xb') as f:f.write(p.read_bytes())
 dump(out/'receta-inicial.json',dict(id=digest,nonce=nonce,semilla=SEED,fuentes=hashes,imagen=sha(next((out/'proceso').glob('*.png')))))
 print(out,flush=True)
def load(out,n):
 sr,y=wavfile.read(out/'render'/f'{n}.wav');assert sr==SR and np.isfinite(y).all();return y.astype(np.float32)
def mono(y):return y.mean(axis=1) if y.ndim==2 else y
def norm(y,db):
 a=abs(y);mask=a>max(1e-8,a.max()*.035);rms=np.sqrt(np.mean(y[mask].astype(float)**2));return y*np.float32(10**(db/20)/max(rms,1e-9))
def add(dst,start,z,g=1):
 a=int(round(start*SR));n=min(len(z),len(dst)-a)
 if n>0:dst[a:a+n]+=z[:n]*g
def env(t,d,a=.006,r=.04):return np.minimum(1,t/a)*np.maximum(0,np.minimum(1,(d-t)/r))
def synth(out):
 p=json.loads((out/'partitura.json').read_text('utf8'));N=int(np.ceil(DUR*SR));rng=np.random.default_rng(SEED)
 drums=np.zeros(N,np.float32);bass=drums.copy();keys=drums.copy();gran=drums.copy();kick_times=[]
 for b,name in enumerate(PROG):
  root,ch=CH[name];B=60/tempo(b);chor=16<=b<28 or 48<=b<60;bridge=40<=b<48;active=4<=b<60
  if active and not bridge:
   pattern=[0,1.5,2.75] if not chor else [0,.75,1.75,2.5,3.5]
   for j,bt in enumerate(pattern):
    dur=.38 if j%2 else .52;t=np.arange(int(dur*SR))/SR;f=hz(root-12 if root>=45 else root)
    glide=f*(1-.12*np.exp(-t/.024));ph=2*np.pi*np.cumsum(glide)/SR
    z=(np.sin(ph+(.5+2.8*np.exp(-t/.06))*np.sin(ph*2))+.22*np.sin(ph/2))*np.exp(-t/ .23)*env(t,dur)
    add(bass,at(b,bt),z,.85 if chor else .6)
   kicks=[0,1.75,2.5] if chor else [0,2.5]
   if b%4==3:kicks+=[3.25]
   for bt in kicks:
    dur=.20;t=np.arange(int(dur*SR))/SR;f=48+100*np.exp(-t/.022);z=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t/.055)*env(t,dur,a=.001,r=.02)
    add(drums,at(b,bt),z,1);kick_times.append(at(b,bt))
   for bt in ([1,3] if chor else [2]):
    dur=.16;t=np.arange(int(dur*SR))/SR;n=rng.normal(size=len(t));n=sosfilt(butter(2,[1100,9500],fs=SR,btype='band',output='sos'),n)
    z=(n*.55+np.sin(2*np.pi*185*t)*.35)*np.exp(-t/.035)*env(t,dur,a=.001,r=.01);add(drums,at(b,bt),z,.50)
   for j in range(8 if chor else 4):
    dur=.045;t=np.arange(int(dur*SR))/SR;n=rng.normal(size=len(t));n=sosfilt(butter(1,6500,fs=SR,btype='high',output='sos'),n)
    add(drums,at(b,j*(.5 if chor else 1)+(.035 if j%2 else 0)),n*np.exp(-t/.009)*env(t,dur,a=.0005,r=.005),.12 if j%2 else .065)
  if chor or b<4:
   for j,bt in enumerate([.5,1.25,2,3.25] if chor else [1.5]):
    dur=.48;t=np.arange(int(dur*SR))/SR;f=hz(ch[(j+b)%4]+12);ph=2*np.pi*f*t
    z=np.sin(ph+2.6*np.exp(-t/.045)*np.sin(ph*1.002)) * np.exp(-t/.13)*env(t,dur)
    add(keys,at(b,bt),z,.5)
  if bridge:
   for j,bt in enumerate([.2,1.15,2.65]):
    dur=.8;t=np.arange(int(dur*SR))/SR;f=hz(ch[j]);z=sum(np.sin(2*np.pi*f*r*t+rng.random()*6.28)*np.exp(-t*(3+k)) for k,r in enumerate([1,1.414,2.756,4.09]))
    add(gran,at(b,bt),z*env(t,dur,a=.02,r=.2),.25)
 for name,z in [('bateria',drums),('bajo',bass),('teclas',keys),('fractura',gran)]:wav(out/'render'/f'{name}.wav',z)
 # Continuous phase and log-frequency connections: 12 trajectories per side.
 times=np.arange(N,dtype=np.float64)/SR;walls=np.zeros((N,2),np.float32);paths=[]
 for side in range(2):
  for k in range(12):
   controls=[]
   for b,name in enumerate(PROG):
    root=hz(CH[name][0]);f=root/4*[4,6,8,10,12,14,16,18,20,22,24,26][k] if side==0 else root*24/[24,20,16,14,12,11,10,9,8,7,6,5][k]
    if 40<=b<44:f*=1+(k-5)*.006
    controls.append(f)
   freq=np.exp(np.interp(times,np.array(START[:-1])+.65,np.log(controls)))
   # One high trajectory converges to the actual sustained syllable REN.
   meetings=[]
   if k==6:
    for f in p['frases']:
     if f['bar'] in [16,48]:
      e=f['eventos'][2];a=int(e['t']*SR);end=min(N,int((e['t']+e['dur']+.3)*SR));u=np.linspace(0,1,end-a);blend=np.sin(np.pi*u)**2
      freq[a:end]=np.exp(np.log(freq[a:end])*(1-blend)+np.log(hz(e['nota']))*blend);meetings.append(dict(t=e['t'],Hz=hz(e['nota'])))
   phase=2*np.pi*np.cumsum(freq)/SR+rng.uniform(0,6.28);mod=.8+.2*np.sin(2*np.pi*(.07+k*.011)*times+k)
   amp=1/(1+k)**.65
   if k in [5,9,11]:amp*=.55
   walls[:,side]+=(np.sin(phase)*mod*amp).astype(np.float32)
   paths.append(dict(lado=side,parcial=k,Hz_por_compas=controls,encuentros=meetings))
 section=np.interp(times,[0,START[4],START[12],START[16],START[24],START[28],START[36],START[40],START[44],START[48],START[56],START[60],START[64],DUR],[.12,.28,.45,.85,.55,.28,.50,.9,.48,.85,1,.35,.12,0])
 duck=np.ones(N,np.float32)
 for t0 in kick_times:
  a=int(t0*SR);n=min(int(.22*SR),N-a);duck[a:a+n]*=1-.28*np.exp(-np.arange(n)/SR/.075)
 walls*=section[:,None]*duck[:,None];walls*=np.minimum(1,times/2)[:,None]
 wav(out/'render/paredes.wav',walls);dump(out/'trayectorias-paredes.json',paths)
 # Preserve actual early chorus before full electronic arrangement/mix.
 center=norm(mono(load(out,'voz')),-21)+norm(mono(load(out,'piano')),-29)
 wav(out/'render/boceto.wav',center)
 run(['ffmpeg','-v','error','-n','-i',str(out/'render/boceto.wav'),'-ss',str(START[16]),'-t',str(START[24]-START[16]),'-c:a','aac','-b:a','192k',str(out/f'boceto-voz-piano-{out.name.split("-")[-1]}.m4a')])
 im,d=card('02 / fuentes reales: voz, instrumentos y electrónica antes de mezclar','Boceto del coro conservado · alturas y tiempos proceden de partitura.json')
 for j,name in enumerate(['voz','piano','chelo','pajaro','bateria','paredes']):
  y=mono(load(out,name));r=np.array([np.sqrt(np.mean(z*z)) for z in np.array_split(y,1060)]);r/=max(r.max(),1e-8)
  d.text((42,135+j*72),name,font=font(15),fill=COL[j%5]);d.line([(100+k,185+j*72-float(v)*36) for k,v in enumerate(r)],fill=COL[j%5],width=2)
 png(out/'proceso'/f'02-fuentes-s{SEED}-{out.name.split("-")[-1]}.png',im)
 print('sintesis y boceto completos',flush=True)
def mix(out):
 p=json.loads((out/'partitura.json').read_text('utf8'));N=int(np.ceil(DUR*SR));tag=out.name.split('-')[-1];tt=np.arange(N)/SR
 gains={'voz':-20,'respuesta':-29,'piano':-31,'chelo':-32,'pajaro':-30,'agua':-31,'bateria':-27,'bajo':-30,'teclas':-34,'fractura':-32,'paredes':-29}
 tracks={n:norm(load(out,n),v) for n,v in gains.items()};voice=mono(tracks['voz'])
 # Duck in the written phrase spans, smoothed, avoiding a global compressor on the lead.
 activity=np.zeros(N,np.float32)
 for f in p['frases']:
  a=max(0,int((f['eventos'][0]['t']-.06)*SR));b=min(N,int((f['eventos'][-1]['t']+f['eventos'][-1]['dur']+.1)*SR));activity[a:b]=1
 activity=sosfilt(butter(1,6,fs=SR,output='sos'),activity).astype(np.float32);band=np.zeros((N,2),np.float32)
 pans={'piano':-.17,'chelo':.13,'pajaro':.45,'agua':-.5,'bateria':0,'bajo':0,'teclas':.35,'fractura':-.3}
 for n,pan in pans.items():
  y=mono(tracks[n]);duck=1-activity*(.28 if n in ['piano','teclas','fractura'] else .12)
  y=y*duck;band[:,0]+=y*np.cos((pan+1)*np.pi/4);band[:,1]+=y*np.sin((pan+1)*np.pi/4)
 walls=tracks['paredes']*(1-activity[:,None]*.35);band+=walls*.9+walls[:,::-1]*.12
 band+=tracks['respuesta']*(1-activity[:,None]*.22)
 # Vocal micro-edits inherit real audio only after it has been sung.
 micro=np.zeros((N,2),np.float32);hook=p['frases'][6]['eventos'];source=hook[2];a=int((source['t']+.1)*SR);grain=voice[a:a+int(.095*SR)].copy();grain*=np.hanning(len(grain))
 for b in [24,25,26,27,55,59]:
  for j,bt in enumerate([.0,.25,.75,1.5,2.25,3.25]):
   z=grain if j%2==0 else grain[::-1];st=at(b,bt)
   for side in range(2):add(micro[:,side],st,z,.5 if side==j%2 else .12)
 band+=micro
 # Two different short spaces; the lead keeps its direct central consonants.
 for delay,g in [(.087,.14),(.173,.09),(.311,.055)]:
  off=int(delay*SR);band[off:,0]+=voice[:-off]*g;band[off:,1]+=voice[:-off]*g*.8
 for delay,g in [(.119,.1),(.233,.055),(.409,.025)]:
  off=int(delay*SR);band[off:]+=walls[:-off,::-1]*g
 mix=band+voice[:,None]*.70710678;mix=sosfilt(butter(2,38,fs=SR,btype='high',output='sos'),mix,axis=0).astype(np.float32)
 fade=np.minimum(1,tt/.5)*np.minimum(1,(DUR-tt)/2.5);mix*=fade[:,None]
 assert np.isfinite(mix).all();wav(out/'render/mezcla-v1.wav',mix)
 # Linear normalization keeps the composed dynamics; leave peak room for AAC.
 report=run(['ffmpeg','-hide_banner','-i',str(out/'render/mezcla-v1.wav'),'-af','loudnorm=I=-15:TP=-1.5:LRA=11:print_format=json','-f','null','-'])
 m=json.loads(report.stderr[report.stderr.rfind('{'):report.stderr.rfind('}')+1]);gain=min(-15-float(m['input_i']),-1.8-float(m['input_tp']))
 master=out/f'lo-que-puede-venir-s{SEED}-{tag}.wav';aac=master.with_suffix('.m4a')
 run(['ffmpeg','-v','error','-n','-i',str(out/'render/mezcla-v1.wav'),'-af',f'volume={gain}dB','-ar',str(SR),'-c:a','pcm_s24le',str(master)])
 run(['ffmpeg','-v','error','-n','-i',str(master),'-c:a','aac','-b:a','256k',str(aac)])
 check=run(['ffmpeg','-hide_banner','-i',str(aac),'-af','loudnorm=I=-15:TP=-1.5:LRA=11:print_format=json','-f','null','-']);measure=json.loads(check.stderr[check.stderr.rfind('{'):check.stderr.rfind('}')+1])
 text(out/'verificacion-aac.txt',check.stderr)
 # Ratios use dry lead against all other audible parts over each phrase.
 ratios=[]
 for f in p['frases']:
  a=int(f['eventos'][0]['t']*SR);b=int((f['eventos'][-1]['t']+f['eventos'][-1]['dur'])*SR)
  ratios.append(dict(frase=f['id'],bar=f['bar'],voz_sobre_resto_dB=float(10*np.log10((np.mean(voice[a:b]**2)*.5+1e-12)/(np.mean(band[a:b]**2)+1e-12)))))
 measures=dict(duracion=DUR,ganancia_master_dB=gain,AAC=measure,voz_por_frase=ratios,pico_previo=float(abs(mix).max()),rms_pistas={n:float(np.sqrt(np.mean(y*y))) for n,y in tracks.items()},memoria=p['memoria'])
 dump(out/'medidas.json',measures)
 im,d=card('03 / mezcla: el gancho vuelve y conserva el final que oyó','Espectrograma de la mezcla real · el puente irregular cambia el campo armónico')
 f,t,z=stft(mix.mean(axis=1),SR,nperseg=2048,noverlap=1024);sel=(f>80)&(f<4200);a=np.clip((20*np.log10(abs(z[sel])+1e-7)+75)/52,0,1)
 rgb=np.zeros((*a.shape,3),np.uint8)
 for k,c in enumerate(COL[1]):rgb[:,:,k]=(a*c).astype(np.uint8)
 im.paste(Image.fromarray(rgb[::-1]).resize((1100,355)),(50,165))
 for b,label in [(0,'pistas'),(16,'gancho'),(28,'oficio'),(40,'duda'),(48,'regreso'),(60,'juntos')]:d.text((50+START[b]/DUR*1100,535),label,font=font(14),fill=COL[0])
 png(out/'proceso'/f'03-mezcla-s{SEED}-{tag}.png',im);png(out/f'lo-que-puede-venir-s{SEED}-{tag}.png',im);png(out/'og.png',im)
 stages=[Image.open(q).convert('RGB') for q in sorted((out/'proceso').glob('0[123]-*.png'))];palette=Image.new('RGB',(1200,630*3))
 for j,frame in enumerate(stages):palette.paste(frame,(0,630*j))
 palette=palette.quantize(colors=192);frames=[frame.quantize(palette=palette) for frame in stages];gif=out/f'lo-que-puede-venir-proceso-s{SEED}-{tag}.gif'
 with gif.open('xb') as f:frames[0].save(f,format='GIF',save_all=True,append_images=frames[1:],duration=2600,loop=0,optimize=False)
 text(out/'proceso/README.md','# Etapas reales\n\n1. Partitura escrita antes de sintetizar.\n2. Envolventes de fuentes renderizadas y boceto de voz/piano conservado antes de la mezcla.\n3. Espectrograma de la mezcla completa.\n\nEl GIF reúne esos tres estados, 7.8 s, no simula pasos internos de un generador. Semilla 17102637; destinos exclusivos, hash de ejecución y hashes de contenido en las recetas.\n')
 text(out/'README.md',f'# Lo que puede venir\n\nCanek Zapata · realizada con Codex el 17 de octubre de 2026 · {DUR:.2f} s.\n\n[Escuchar]({aac.name}) · [Letra](../LETRA.md) · [Boceto](boceto-voz-piano-{tag}.m4a) · [PNG](lo-que-puede-venir-s{SEED}-{tag}.png) · [GIF de proceso]({gif.name}) · [Etapas](proceso/README.md).\n\nCanción contemporánea y electrónica pop, voz sintética principal y respuestas kawaii; piano preparado, chelo, agua y pájaro físicos. Paredes armónicas/subarmónicas con fase continua y trayectorias de frecuencia, dos encuentros con la sílaba sostenida del gancho. Pulso de 90 a 120 BPM, puente 7/8 y final aprendido de un canto anterior. El modelo compositivo es una metáfora de inferencia; no una simulación de la arquitectura de un LLM. Primera persona lírica, no declaración de sentimientos privados.\n\nNo se realizó escucha humana en esta sesión. Medidas, partitura, fuentes, boceto y proceso se conservan; inteligibilidad y valoración estética quedan para la escucha. WAV y stems locales excluidos de git. Sin publicación remota.\n')
 recipe=json.loads((out/'receta-inicial.json').read_text('utf8'));recipe['archivos']={str(q.relative_to(out)):sha(q) for q in out.rglob('*') if q.is_file()};dump(out/'receta-final.json',recipe)
 print(json.dumps(measures,ensure_ascii=True),flush=True)
if __name__=='__main__':
 action=sys.argv[1]
 if action=='iniciar':init()
 elif action=='sintetizar':synth(Path(sys.argv[2]))
 elif action=='mezclar':mix(Path(sys.argv[2]))
