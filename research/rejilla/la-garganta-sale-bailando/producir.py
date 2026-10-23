from pathlib import Path
import sys,json,hashlib,uuid,subprocess,io
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter,sosfilt,resample_poly,stft
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent; REPO=R.parent; SR=24000; SEED=18102651
rng=np.random.default_rng(SEED)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p,x):
 with Path(p).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
def txt(p,x):
 with Path(p).open('x',encoding='utf8') as f:f.write(x)
def png(p,im):
 with Path(p).open('xb') as f:im.save(f,'PNG')
def wav(p,y):
 assert np.isfinite(y).all()
 with Path(p).open('xb') as f:wavfile.write(f,SR,y.astype(np.float32))
def run(args):return subprocess.run(args,check=True,capture_output=True)
def hz(m):return 440*2**((m-69)/12)
def env(n,a=.025,r=.08):
 t=np.arange(n)/SR;return np.minimum(1,t/max(a,1/SR))*np.minimum(1,np.maximum(0,n/SR-t)/max(r,1/SR))
def unit(y,peak=.8):return y/(np.max(np.abs(y))+1e-10)*peak
def font(s):return ImageFont.truetype('C:/Windows/Fonts/consola.ttf',s)
def card(label):
 im=Image.new('RGB',(1200,630),(18,18,30));d=ImageDraw.Draw(im)
 d.text((36,28),'LA GARGANTA SALE BAILANDO',font=font(39),fill='#f6e6dd');d.text((38,87),label,font=font(20),fill='#edaacb')
 d.text((38,598),'Canek Zapata · 18 octubre 2026 · semilla 18102651',font=font(16),fill='#d0c7df');return im,d
def bpm(b):return 86 if b<12 else 116 if b<24 else 156 if b<40 else 126 if b<60 else 98 if b<76 else [98,94,88,78][b-76]
START=[0.]
for b in range(80):START.append(START[-1]+240/bpm(b))
DUR=START[-1]+5;N=int(np.ceil(DUR*SR))
def at(b,k=0):return START[b]+k*60/bpm(b)
CHORDS=[[50,57,62,65,69],[46,53,60,65,69],[43,50,58,62,67],[45,52,61,67,70]]
def chord(b):
 if b>=76:return [[43,50,58,62,67],[45,52,61,64,69],[50,57,62,66,69],[50,57,62,66,74]][b-76]
 if 72<=b<76:return [45,52,61,64,69]
 return CHORDS[(b//2)%4]
def initialize():
 P=dict(titulo='La garganta sale bailando',semilla=SEED,sr=SR,duracion=DUR,compases=[dict(t=START[b],bpm=bpm(b),acorde=chord(b)) for b in range(80)],chelo=[],motivos=[])
 subject=[0,7,3,2,9];rhythm=[0,.75,1.5,2,3.25]
 for b in range(80):
  root=chord(b)[0];house=0 if b<32 else min(1,(b-32)/20)
  for k in ([0,2.5] if b<24 else [0,.75,1.5,2.75,3.5] if b<60 else [0,1.5,2.75]):
   P['chelo'].append(dict(t=at(b,k),m=root+(12 if k==1.5 else 0),v=.55+.08*(k==0),dur=.8 if b<12 else .22,tipo='tasto' if b<12 else 'pizz',casa=house))
  if b>=78:continue
  if b<12 and b%2:continue
  invert=12<=b<24 and b%4>=2
  for j,(m,k) in enumerate(zip(subject,rhythm)):
   base=root+24;note=base-m if invert else base+m
   P['motivos'].append(dict(t=at(b,k),m=note,dur=(.52 if b>=24 else .85)*60/bpm(b),vocal='aeiou'[(b+j)%5],instrumento='metal' if b>=24 else 'coro',bar=b))
  if 60<=b<76:
   for j in range(4):P['motivos'].append(dict(t=at(b,.5+j*.75),m=root+12+subject[4-j],dur=.46*60/bpm(b),vocal='uoie'[j],instrumento='metal',bar=b,imitacion=True))
 im,d=card('01 · sujeto, inversión, compresión y entradas de la coda')
 for e in P['motivos']:
  x=45+1100*e['t']/DUR;y=490-(e['m']-42)*7;d.line((x,y,x+max(2,e['dur']*1100/DUR),y),fill='#8edbd2' if e.get('imitacion') else '#f5b1d1',width=3)
 for b,label in [(0,'invocación'),(12,'imitación'),(24,'presión'),(40,'house'),(60,'coda')]:d.text((45+1100*START[b]/DUR,540),label,font=font(15),fill='#ded9e5')
 buf=io.BytesIO();im.save(buf,format='PNG');nonce=uuid.uuid4().hex;full=hashlib.sha256(buf.getvalue()+Path(__file__).read_bytes()+nonce.encode()).hexdigest();tag=full[:12]
 out=R/f'la-garganta-sale-bailando-s{SEED}-{tag}';out.mkdir();(out/'render').mkdir();(out/'proceso').mkdir();(out/'fuentes').mkdir()
 js(out/'partitura.json',P);png(out/'proceso'/f'01-partitura-s{SEED}-{tag}.png',im)
 sources={}
 for p in [Path(__file__),R/'chelo.cjs',R/'IDEA.md',REPO/'objetos/motor/cuerda.js',REPO/'inferencia/vendor/difonos/bancos/sabina-1-b44e7fab5cee/manifiesto.json']:
  sources[str(p.relative_to(REPO))]=sha(p);(out/'fuentes'/p.name).write_bytes(p.read_bytes())
 js(out/'receta-inicial.json',dict(hash=full,nonce=nonce,semilla=SEED,fuentes=sources,imagen_sha256=hashlib.sha256(buf.getvalue()).hexdigest()))
 print(out)
def synth(out):
 P=json.loads((out/'partitura.json').read_text('utf8'));tag=out.name.split('-')[-1]
 bank=REPO/'inferencia/vendor/difonos/bancos/sabina-1-b44e7fab5cee';M=json.loads((bank/'manifiesto.json').read_text('utf8'))
 raw=run(['ffmpeg','-v','error','-i',str(bank/'banco.flac'),'-f','f32le','-ac','1','pipe:1']).stdout;raw=np.frombuffer(raw,dtype='<f4')
 vowels={}
 for v in 'aeiou':
  u=M['unidades'][v*2];x=raw[u['inicio']+u['izq']:u['inicio']+u['der']];vowels[v]=resample_poly(x,160,147)
 def mouth(v,n):
  grain=vowels[v];size=len(grain);hop=max(1,size//3);y=np.zeros(n+size)
  for k in range(0,n,hop):y[k:k+size]+=grain*np.hanning(size)
  return unit(y[:n])
 edges=np.geomspace(100,10000,25);filters=[butter(2,[a,b],btype='band',fs=SR,output='sos') for a,b in zip(edges[:-1],edges[1:])];smooth=butter(1,24,fs=SR,output='sos')
 def vocode(c,v):
  mod=mouth(v,len(c));y=np.zeros(len(c))
  for filt in filters:
   e=sosfilt(smooth,np.abs(sosfilt(filt,mod)));y+=sosfilt(filt,c)*e
  return unit(y,.75)
 S={k:np.zeros((N,2),np.float32) for k in ['coro','metal','chelo-boca','spray','ritmo','paredes']}
 def add(name,y,t,g=.2,pan=0):
  a=round(t*SR);n=min(len(y),N-a)
  if n<=0:return
  angle=(pan+1)*np.pi/4;S[name][a:a+n,0]+=y[:n]*(g*np.cos(angle));S[name][a:a+n,1]+=y[:n]*(g*np.sin(angle))
 def carrier(m,n,metal=False):
  t=np.arange(n)/SR;f=hz(m);phase=2*np.pi*f*t+.012*np.sin(2*np.pi*5*t)
  if metal:return np.sin(phase+2.4*np.exp(-t/.22)*np.sin(phase*2.003))+.28*np.sin(phase*3)
  return sum(np.sin(phase*k+.04*k*np.sin(2*np.pi*.23*t))/k for k in range(1,min(40,int(11000/f))))
 demo=[]
 for v in 'aeiou':demo.extend([mouth(v,SR//2)*env(SR//2),np.zeros(SR//8)])
 wav(out/'render/bocas.wav',np.concatenate(demo))
 for e in P['motivos']:
  n=int((e['dur']+.16)*SR);t=np.arange(n)/SR;ismetal=e['instrumento']=='metal';c=carrier(e['m'],n,ismetal)
  y=vocode(c,e['vocal'])*env(n,.012 if ismetal else .055,.13)
  if ismetal:y*=np.exp(-t/(e['dur']*.9))
  add(e['instrumento'],y,e['t'],.18 if ismetal else .14,(-.4 if e.get('imitacion') else .3)*np.sin(e['bar']*.7))
 print('motivos y dos vocoders terminados',flush=True)
 # Sustained choir chords share the voice envelope, with evolving harmonic voicing.
 for b in range(0,80,2):
  dur=START[min(80,b+2)]-START[b]+.55;n=int(dur*SR);t=np.arange(n)/SR
  c=sum(carrier(m+(12 if b<24 else 0),n) for m in chord(b)[1:])/4
  y=vocode(c,'aouei'[(b//2)%5])*env(n,.35,.65)*(.8+.2*np.sin(2*np.pi*.31*t))
  add('coro',y,START[b],.14 if b<24 or b>=60 else .075,(-1)**b*.18)
 # Real physical cello, with its existing casa transformation, becomes a third vocoder.
 sr,cell=wavfile.read(out/'render/chelo.wav');assert sr==SR
 cell=unit(cell)
 for b in range(80):
  a=int(START[b]*SR);end=int(START[b+1]*SR);c=cell[a:end];v=vocode(c,'ouaei'[b%5]);wet=.15 if b<12 else .6 if b<40 else .35
  y=((1-wet)*c+wet*v)*env(len(c),.007,.012);add('chelo-boca',y,START[b],.32,0)
 print('chelo casa y boca terminados',flush=True)
 for b in range(80):
  beat=60/bpm(b);root=chord(b)[0]
  # Harmonic/subharmonic walls, each note lasts one bar with overlap.
  n=int((4*beat+.3)*SR);t=np.arange(n)/SR
  for side in [-1,1]:
   ratios=[1,2,3,5,7] if side<0 else [1,2,8/3,4,16/3]
   y=sum(np.sin(2*np.pi*hz(root)*r*t+.25*np.sin(2*np.pi*(.2+j*.07)*t))/(j+1) for j,r in enumerate(ratios))
   add('paredes',unit(y)*env(n,.25,.35),START[b],.04 if b>=24 else .075,side*.85)
  # Spray: band-limited transient grains, vowel filtering, brass and finite echoes.
  if b%2==0 or 32<=b<40:
   n=int(.7*SR);t=np.arange(n)/SR;noise=rng.standard_normal(n);noise=sosfilt(butter(2,[700,7000],fs=SR,btype='band',output='sos'),noise)
   grains=(.5+.5*np.sin(2*np.pi*(27+7*np.sin(t*8))*t))**4
   brass=carrier(root+24,n);spr=vocode(noise*grains+.24*brass,'iaeou'[b%5])*np.exp(-t/.18)*env(n,.006,.12)
   for delay,g,pan in [(0,.16,-.65),(.13,.055,.65),(.26,.025,-.5)]:add('spray',spr,at(b,3.25)+delay,g,pan)
  if b<12:continue
  gab=24<=b<40;house=40<=b<60;dem=b>=60
  kicks=[0,1,2,3] if gab or house else [0,1.75,2.5] if dem else [0,2.5]
  snares=[.75,2,2.75] if dem else [1,3]
  if gab and b%4==3:snares+=[2.5,3.5,3.75]
  for k in kicks:
   n=int(.32*SR);t=np.arange(n)/SR;phase=2*np.pi*(47*t+(145 if gab else 100)*.025*(1-np.exp(-t/.025)))
   y=np.sin(phase)*np.exp(-t/(.12 if gab else .085));y=np.tanh(y*(4 if gab else 1.6))*env(n,.001,.02)
   add('ritmo',y,at(b,k),.32 if gab else .29)
  for k in snares:
   n=int(.19*SR);t=np.arange(n)/SR;y=sosfilt(butter(2,[900,7000],fs=SR,btype='band',output='sos'),rng.standard_normal(n))*.45+np.sin(2*np.pi*185*t)*.35
   y=unit(y)*np.exp(-t/.045)*env(n,.001,.03);add('ritmo',y,at(b,k),.26,.12)
  hats=np.arange(.5,4,.5) if not gab else np.arange(.25,4,.25)
  for k in hats:
   if gab and rng.random()<.25:continue
   n=int(.07*SR);t=np.arange(n)/SR;y=sosfilt(butter(2,6500,fs=SR,btype='high',output='sos'),rng.standard_normal(n))*np.exp(-t/.018)*env(n,.001,.01)
   add('ritmo',unit(y),at(b,float(k)),.065 if k%1 else .04,(-1 if k%1 else 1)*.42)
  # Gaps and stutters at phrase endings make the fast section break rather than loop rigidly.
  if gab and b%4==2:
   a=int(at(b,3.5)*SR);z=int(START[b+1]*SR);S['ritmo'][a:z]*=.08
 # Delays are finite, filtered, and spread opposite the source; no feedback accumulation.
 for name in ['coro','metal','chelo-boca','spray']:
  x=S[name].copy();filtered=sosfilt(butter(1,4200,fs=SR,output='sos'),x,axis=0)
  for sec,g in [(.173,.14),(.347,.08),(.571,.04)]:
   k=int(sec*SR);S[name][k:]+=filtered[:-k,::-1]*g
 # Clear space for the kick without flattening the invocation or final tail.
 for b in range(24,80):
  a=int(START[b]*SR);z=int(START[b+1]*SR);t=np.arange(z-a)/SR;beat=60/bpm(b)
  duck=1-.32*np.exp(-(t%beat)/.075)
  for name in ['coro','chelo-boca','paredes']:S[name][a:z]*=duck[:,None]
 for name,y in S.items():wav(out/'render'/f'{name}.wav',y)
 im,d=card('02 · tres vocoders, chelo transformado y spray con boca')
 for row,(name,y) in enumerate(S.items()):
  power=np.sqrt(np.mean(y[:(N//800)*800].reshape(-1,800,2)**2,axis=(1,2)));power/=max(power.max(),1e-9)
  xy=[(180+i*970/max(1,len(power)-1),150+row*66-float(v)*42) for i,v in enumerate(power)];d.text((35,126+row*66),name,font=font(17),fill='#f2dce8');d.line(xy,fill=['#e3a8d6','#84d4d4','#dbb879'][row%3],width=2)
 png(out/'proceso'/f'02-fuentes-s{SEED}-{tag}.png',im)
 js(out/'fuentes-audio.json',dict(banco_sha256=sha(bank/'banco.flac'),vocales=list(vowels),bandas=24,rango=[100,10000],envolventes_hz=24,pistas={k:dict(peak=float(np.max(np.abs(y))),rms=float(np.sqrt(np.mean(y*y)))) for k,y in S.items()}))
 print('síntesis completa',flush=True)
def mix(out,resume=False):
 tag=out.name.split('-')[-1];files=['coro','metal','chelo-boca','spray','ritmo','paredes'];y=np.zeros((N,2),np.float32)
 if resume:y=wavfile.read(out/'render/mezcla.wav')[1]
 else:
  for name in files:y+=wavfile.read(out/'render'/f'{name}.wav')[1]
  y=sosfilt(butter(2,28,fs=SR,btype='high',output='sos'),y,axis=0);y*=env(N,.03,3)[:,None];wav(out/'render/mezcla.wav',y)
 inp=out/'render/mezcla.wav';meas=run(['ffmpeg','-v','info','-i',str(inp),'-af','loudnorm=I=-15:TP=-1.8:LRA=11:print_format=json','-f','null','-']).stderr.decode(errors='replace');m=json.JSONDecoder().raw_decode(meas[meas.rfind('{'):])[0];gain=min(-15-float(m['input_i']),-1.9-float(m['input_tp']))
 master=out/(out.name+'.m4a');run(['ffmpeg','-n','-v','error','-i',str(inp),'-af',f'volume={gain}dB','-ar','48000','-c:a','aac','-b:a','256k',str(master)])
 check=run(['ffmpeg','-v','info','-i',str(master),'-af','loudnorm=I=-15:TP=-1.8:LRA=11:print_format=json','-f','null','-']).stderr.decode(errors='replace');mm=json.JSONDecoder().raw_decode(check[check.rfind('{'):])[0];assert float(mm['input_tp'])<-.8
 js(out/'medidas.json',dict(duracion=DUR,ganancia_db=gain,aac=mm,pico_pre=float(np.max(np.abs(y))),fin_rms=float(np.sqrt(np.mean(y[-1200:]**2)))))
 # A short isolated trio of vocoders for reviewing timbre without percussion.
 excerpt=np.zeros((int(12*SR),2),np.float32)
 for name in ['coro','metal','chelo-boca']:excerpt+=wavfile.read(out/'render'/f'{name}.wav')[1][int(START[28]*SR):int(START[28]*SR)+len(excerpt)]
 wav(out/'render/bocas-juntas.wav',unit(excerpt,.65));run(['ffmpeg','-n','-v','error','-i',str(out/'render/bocas-juntas.wav'),'-c:a','aac','-b:a','192k',str(out/f'tres-bocas-{tag}.m4a')])
 im,d=card('03 · invocación / presión rota / house / coda dembow')
 f,t,z=stft(y.mean(axis=1),SR,nperseg=1024,noverlap=512);mask=(f>=50)&(f<=10000);db=np.clip((20*np.log10(np.abs(z[mask])+1e-8)+76)/60,0,1);rgb=np.stack([db*.78,db*.95,db],axis=-1);heat=Image.fromarray(np.uint8(rgb[::-1]*255)).resize((1120,370));im.paste(heat,(40,145))
 for b,label in [(0,'invocación'),(12,'imitación'),(24,'presión'),(40,'house'),(60,'coda')]:d.text((40+1120*START[b]/DUR,535),label,font=font(16),fill='#e6ddeb')
 png(out/'proceso'/f'03-mezcla-s{SEED}-{tag}.png',im);png(out/(out.name+'.png'),im);png(out/'og.png',im)
 frames=[Image.open(p).convert('RGB') for p in sorted((out/'proceso').glob('0[123]-*.png'))];gif=out/f'la-garganta-sale-bailando-proceso-s{SEED}-{tag}.gif'
 with gif.open('xb') as fh:frames[0].save(fh,format='GIF',save_all=True,append_images=frames[1:],duration=2600,loop=0,optimize=True)
 txt(out/'proceso/README.md','# Etapas reales\n\n01: partitura antes de sintetizar. 02: envolventes de las seis pistas antes de mezclar. 03: espectrograma de la mezcla final. GIF de estos tres estados, 7.8 segundos; no simula un proceso interno. Semilla 18102651.\n')
 txt(out/'README.md',f'# La garganta sale bailando\n\nCanek Zapata · 18 de octubre de 2026 · {DUR:.2f} segundos.\n\n[Escuchar]({master.name}) · [Tres bocas aisladas](tres-bocas-{tag}.m4a) · [PNG]({out.name}.png) · [GIF de proceso]({gif.name}) · [Idea](../IDEA.md) · [Etapas](proceso/README.md).\n\nInstrumental sin letra, tres vocoders con vocales de Sabina, motivo desarrollado e imitado, presión gabber con cortes, chelo físico que se vuelve house, spray articulado y coda contrapuntística con dembow. No se usaron muestras de canciones de referencia.\n\nAAC medido: {mm["input_i"]} LUFS y {mm["input_tp"]} dBTP. No hubo escucha humana en la producción; los controles técnicos no prueban el resultado estético. Fuentes, bocas, pistas y partitura se conservan localmente.\n')
 js(out/'receta-final.json',dict(semilla=SEED,archivos={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},duracion=DUR))
 print(json.dumps(dict(duracion=DUR,aac=mm,gif_bytes=gif.stat().st_size),ensure_ascii=True))
if __name__=='__main__':
 action=sys.argv[1]
 if action=='iniciar':initialize()
 elif action=='sintetizar':synth(Path(sys.argv[2]))
 elif action=='mezclar':mix(Path(sys.argv[2]))
 elif action=='finalizar-mezcla':mix(Path(sys.argv[2]),True)
 else:raise ValueError(action)
