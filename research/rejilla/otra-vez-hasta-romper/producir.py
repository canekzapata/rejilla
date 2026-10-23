from pathlib import Path
import importlib.util,json,sys,hashlib,uuid,io
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter,sosfilt,resample_poly,stft
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent;REPO=R.parent
helper=REPO/'la-garganta-sale-bailando/producir.py';spec=importlib.util.spec_from_file_location('utilidades',helper);h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
SR=24000;SEED=18102692;rng=np.random.default_rng(SEED)
def bpm(b):return 96 if b<24 else 100+68*(b-24)/15 if b<40 else 180 if b<64 else 174 if b<88 else 192
START=[0.]
for b in range(96):START.append(START[-1]+240/bpm(b))
# Last impact is at the final bar's fourth beat. Its release is 90 ms, then 50 ms silence.
HIT=START[95]+180/192;CUT=HIT+.23;DUR=CUT+.05;N=int(np.ceil(DUR*SR))
def at(tick):
 b=int(tick//16);return START[b]+(tick%16)*15/bpm(b)
def card(s):
 im=Image.new('RGB',(1200,630),'#11141d');d=ImageDraw.Draw(im);d.text((35,25),'OTRA VEZ HASTA ROMPER',font=h.font(44),fill='#f8e6db');d.text((38,89),s,font=h.font(19),fill='#f5a7bc');d.text((38,598),'Canek Zapata · semilla 18102692 · 18 octubre 2026',font=h.font(16),fill='#d8cbd8');return im,d
def init():
 E=[];cycles=[]
 def note(tick,m,length,voice,cycle,kind):
  if tick>=88*16:return
  end=min(tick+length,88*16);E.append(dict(t=at(tick),dur=at(end)-at(tick),m=m,voz=voice,ciclo=cycle,operacion=kind,tick=tick))
 # Fixed identity is heard first; deletions and unequal cycles only come after recognition.
 tick=0;cy=0
 while tick<64*16:
  length=16 if tick<16*16 else [15,17,16,13][cy%4];ds=[3,1,2,3,1,4,2];ms=[69,69.14,69,76,72,71,69];pos=0
  for j,(d,m) in enumerate(zip(ds,ms)):
   if pos>=length:break
   omitted=tick>=24*16 and cy%4==2 and j in [1,4]
   if not omitted:note(tick+pos,69+(m-69)*(0 if tick<8*16 else 1),min(d*.82,length-pos),'boca',cy,'supresion' if omitted else 'ciclo')
   pos+=d
  cycles.append(dict(tick=tick,periodo=length,voz='boca'));tick+=length;cy+=1
 tick=8*16;cy=0
 while tick<64*16:
  length=16 if tick<16*16 else 17;ms=[57,64,60,59,57];ds=[2,3,3,2,6];pos=0
  for j,(d,m) in enumerate(zip(ds,ms)):
   note(tick+pos,m if cy%4<2 else 114-m,d*.78,'respuesta',cy,'inversion' if cy%4>=2 else 'respuesta');pos+=d
  cycles.append(dict(tick=tick,periodo=length,voz='respuesta'));tick+=length;cy+=1
 # Four composed phrases, each 32 ticks; the return changes register, order and ending.
 phrases=[([69,72,76,79,78,76,71,74],[3,1,4,6,2,4,4,8]),([76,74,72,71,67,69],[4,3,1,8,6,10]),([69,76,81,83,79,78,76],[2,2,5,3,4,8,8]),([74,72,71,67,68,69],[3,3,2,8,4,12])]
 for k in range(12):
  tick=(64+k*2)*16;ms,ds=phrases[k%4];pos=0
  for j,(m,d) in enumerate(zip(ms,ds)):
   pitch=m+(12 if k in [8,10] and j<3 else 0);note(tick+pos,pitch,d*.87,'boca',100+k,'arco')
   if k%3==1 and j%2==0:note(tick+pos+2,126-m,min(d*1.3,6),'respuesta',100+k,'canon-invertido')
   elif j%2:note(tick+pos, pitch-12 if k%2 else pitch-7,d*.65,'respuesta',100+k,'hoquetus')
   pos+=d
 A={e['tick'] for e in E if e['voz']=='boca'};B={e['tick'] for e in E if e['voz']=='respuesta'};meet=sorted(A&B)
 P=dict(titulo='Otra vez hasta romper',semilla=SEED,duracion=DUR,golpe_final=HIT,corte=CUT,compases=[dict(t=START[b],bpm=bpm(b)) for b in range(96)],eventos=E,ciclos=cycles,encuentros=[dict(tick=t,t=at(t),parcial=[3,5,7,11][i%4]) for i,t in enumerate(meet)],bucles_finales=[8,5,3,2,1],secciones=[['dembow',0],['deformacion',START[24]],['gabber',START[40]],['arco-digital',START[64]],['cierre',START[88]]])
 im,d=card('01 · dos ciclos se desplazan; sus encuentros excitan el espectro')
 for e in E:
  x=40+1110*e['t']/DUR;y=465-(e['m']-45)*6;d.line((x,y,x+max(2,1110*e['dur']/DUR),y),fill='#85ded7' if e['voz']=='respuesta' else '#f4a5c0',width=3)
 for e in P['encuentros']:x=40+1110*e['t']/DUR;d.line((x,492,x,508),fill='#e0d18b')
 buf=io.BytesIO();im.save(buf,format='PNG');nonce=uuid.uuid4().hex;full=hashlib.sha256(buf.getvalue()+Path(__file__).read_bytes()+nonce.encode()).hexdigest();tag=full[:12]
 out=R/f'otra-vez-hasta-romper-s{SEED}-{tag}';out.mkdir();(out/'render').mkdir();(out/'proceso').mkdir();(out/'fuentes').mkdir()
 h.js(out/'partitura.json',P);h.png(out/'proceso'/f'01-partitura-s{SEED}-{tag}.png',im)
 paths=[Path(__file__),R/'kit.cjs',R/'IDEA.md',helper,REPO/'catalogo-agua-que-habla/instrumentos-48b8a06e1049/motores/web.js',REPO/'catalogo-agua-que-habla/instrumentos-48b8a06e1049/fichas/bateria-frito.json']
 sources={}
 for i,p in enumerate(paths):sources[str(p.relative_to(REPO))]=h.sha(p);(out/'fuentes'/f'{i:02d}-{p.name}').write_bytes(p.read_bytes())
 h.js(out/'receta-inicial.json',dict(hash=full,nonce=nonce,semilla=SEED,fuentes=sources));print(out,flush=True)
def synth(out):
 P=json.loads((out/'partitura.json').read_text('utf8'));tag=out.name.split('-')[-1];S={n:np.zeros((N,2),np.float32) for n in ['bocas','respuesta','nota-interior','bajo','dembow','gabber','spray']}
 def add(name,y,t,g=1,pan=0):
  a=round(t*SR);n=min(len(y),N-a)
  if a<0 or n<=0:return
  ang=(pan+1)*np.pi/4;S[name][a:a+n,0]+=y[:n]*g*np.cos(ang);S[name][a:a+n,1]+=y[:n]*g*np.sin(ang)
 kit={name:h.unit(np.fromfile(out/'render'/f'kit-{name}.f32',dtype=np.float32),.8) for name in ['kick','snare','rim','clap','hat','openhat','spray','tomlo']}
 bank=REPO/'inferencia/vendor/difonos/bancos/sabina-1-b44e7fab5cee';M=json.loads((bank/'manifiesto.json').read_text('utf8'));raw=np.frombuffer(h.run(['ffmpeg','-v','error','-i',str(bank/'banco.flac'),'-f','f32le','-ac','1','pipe:1']).stdout,dtype='<f4');vowels={}
 for v in 'aeiou':
  u=M['unidades'][v*2];vowels[v]=resample_poly(raw[u['inicio']+u['izq']:u['inicio']+u['der']],160,147)
 filts=[butter(2,[a,b],fs=SR,btype='band',output='sos') for a,b in zip(np.geomspace(120,10000,23)[:-1],np.geomspace(120,10000,23)[1:])];sm=butter(1,32,fs=SR,output='sos');cache={}
 def vocal(m,n,v,fm=False):
  key=(round(m,3),n,v,fm)
  if key in cache:return cache[key]
  t=np.arange(n)/SR;grain=vowels[v];mod=np.zeros(n+len(grain))
  for k in range(0,n,len(grain)//3):mod[k:k+len(grain)]+=grain*np.hanning(len(grain))
  mod=h.unit(mod[:n]);ph=2*np.pi*h.hz(m)*t
  carrier=np.sin(ph+2*np.exp(-t/.15)*np.sin(ph*2.01)) if fm else sum(np.sin(ph*k)/k for k in range(1,min(28,int(10500/h.hz(m)))))
  y=np.zeros(n)
  for f in filts:y+=sosfilt(f,carrier)*sosfilt(sm,np.abs(sosfilt(f,mod)))
  y=h.unit(y,.8)*h.env(n,.012,.05);cache[key]=y;return y
 for e in P['eventos']:
  n=max(600,int(e['dur']*SR));v='aeiou'[e['ciclo']%5];isreply=e['voz']=='respuesta';y=vocal(e['m'],n,v,isreply)
  gain=.19 if not isreply else .125;add('respuesta' if isreply else 'bocas',y,e['t'],gain,.32 if isreply else -.18)
 print('voces y repeticiones renderizadas',flush=True)
 # One note evolving internally: continuous phases, independent microtonal beating and overtone weights.
 t=np.arange(N)/SR;f0=110.;inside=np.zeros((N,2),np.float32)
 for k in range(1,15):
  cents=(2+15*np.sin(2*np.pi*t/47+k))*(.2+.8*np.minimum(1,t/90));f=f0*k*2**(cents/1200);phase=2*np.pi*np.cumsum(f)/SR
  weight=(.3+.7*np.sin(np.pi*t/(13+k*2)+k)**2)/k**1.2
  for e in P['encuentros']:
   if e['parcial']==k:weight+=.65*np.exp(-np.maximum(0,t-e['t'])/1.6)*(t>=e['t'])
  amp=.028*weight;inside[:,0]+=np.sin(phase)*amp;inside[:,1]+=np.sin(phase+.35*np.sin(t*.17+k))*amp
 inside*=h.env(N,.08,.005)[:,None];S['nota-interior']=inside
 # Beat transformations preserve the dembow syncopation while the kick grid gains force.
 for b in range(96):
  gab=np.clip((b-24)/16,0,1);q=60/bpm(b);base=START[b];end=START[b+1];root=[45,41,48,43][((b-64)//2)%4] if 64<=b<88 else 45
  for tick in [0,8]:add('dembow',kit['kick'],at(b*16+tick),.36*(1-.8*gab))
  for tick in [6,14]:add('dembow',kit['snare'],at(b*16+tick),.25 if b<40 else .12)
  for tick in [3,11]:add('dembow',kit['rim'],at(b*16+tick),.18 if b<40 else .08,-.2)
  for tick in range(0,16,2 if b<32 else 1):
   if b>=64 and tick%5==0:continue
   add('dembow',kit['hat'],at(b*16+tick),.07 if tick%2==0 else .035,(-1)**tick*.4)
  for tick in ([0,3,8,11] if b<40 else [0,4,8,12]):
   n=int(q*.6*SR);tt=np.arange(n)/SR;freq=h.hz(root+(12 if tick==11 else 0));y=(np.sin(2*np.pi*freq*tt)+.18*np.sin(2*np.pi*freq*2*tt))*np.exp(-tt/.12)*h.env(n,.006,.025);add('bajo',y,at(b*16+tick),.25*(1-.55*gab))
  if gab>0:
   hits=[0,4,8,12] if not 64<=b<88 else [[0,7,10],[0,4,10,14],[0,6,8,11],[0,3,10,12]][b%4]
   for tick in hits:
    n=int(.22*SR);tt=np.arange(n)/SR;phase=2*np.pi*(53*tt+110*.023*(1-np.exp(-tt/.023)));y=np.tanh(5*np.sin(phase)*np.exp(-tt/.11))*h.env(n,.001,.025);add('gabber',y,at(b*16+tick),.31*gab)
   if b>=64:
    for tick in [4,12,13.5] if b%2 else [4,12]:add('dembow',kit['snare'],at(b*16+tick),.22 if tick in [4,12] else .09,.1)
  if b in [0,16,24,32,40,48,64,72,80,88,92]:add('spray',kit['spray'],base,.16)
  # Deliberate shared silences at phrases' edges, progressively narrower than a beat.
  if b in [23,39,55,63,79,87]:
   a=round(at(b*16+15)*SR);z=round(end*SR)
   for name in S:S[name][a:z]*=h.env(z-a,.001,.006)[:,None]*.025
 # Finite echoes. The last section will overwrite none of the score: it reuses earlier rendered material.
 for name in ['bocas','respuesta']:
  src=S[name].copy()
  for sec,g in [(.117,.13),(.239,.065)]:k=int(sec*SR);S[name][k:]+=src[:-k,::-1]*g
 # Shared edits to earlier ensemble fragments: literal repeats, shortening, then hard final unison.
 source=int(START[68]*SR);rendered=sum(S.values());cuts=[]
 for i,b in enumerate(range(88,96)):
  a=int(START[b]*SR);z=min(N,int(START[b+1]*SR));step=[8,8,5,5,3,2,1,1][i];length=int(step*15/192*SR)
  grain=rendered[source:source+length].copy();grain*=h.env(len(grain),.002,.006)[:,None]
  for name in S:S[name][a:z]*=.15 if name in ['dembow','gabber'] else 0
  for pos in range(a,z,length):n=min(length,z-pos);S['bocas'][pos:pos+n]+=grain[:n]*(.8+i*.055)
  cuts.append(dict(compas=b,subdivisiones=step,fuente_t=source/SR))
 # One full impact, short release, no tail. Band-limited synthesis and 5 ms ramp avoid a digital click.
 a=int(HIT*SR)
 for name in S:S[name][a:]=0
 n=int(.23*SR);tt=np.arange(n)/SR;impact=np.tanh(3*(np.sin(2*np.pi*55*tt)+.3*np.sin(2*np.pi*110*tt)))*h.env(n,.001,.005)
 add('gabber',impact,HIT,.48);add('spray',kit['spray'][:n]*h.env(n,.001,.005),HIT,.22)
 for m in [57,64,69,81]:add('bocas',vocal(m,n,'a')*h.env(n,.001,.005),HIT,.13,0)
 for name,y in S.items():y[int(CUT*SR):]=0;h.wav(out/'render'/f'{name}.wav',y)
 h.js(out/'transformaciones.json',dict(bucles=cuts,fuente_vocal_sha256=h.sha(bank/'banco.flac'),pistas={k:dict(peak=float(np.abs(v).max()),rms=float(np.sqrt(np.mean(v*v)))) for k,v in S.items()}))
 im,d=card('02 · vocales, una nota por dentro y el ritmo que cambia de cuerpo')
 for i,(name,y) in enumerate(S.items()):
  v=np.sqrt(np.mean(y[:N//1000*1000].reshape(-1,1000,2)**2,axis=(1,2)));v/=max(v.max(),1e-9);d.text((35,133+i*61),name,font=h.font(16),fill='#eadbe1');d.line([(220+j*930/(len(v)-1),166+i*61-vv*35) for j,vv in enumerate(v)],fill=['#f6aac7','#87d8d6','#e1ce8a'][i%3],width=2)
 h.png(out/'proceso'/f'02-fuentes-s{SEED}-{tag}.png',im);print('síntesis terminada',flush=True)
def finish(out):
 tag=out.name.split('-')[-1];names=['bocas','respuesta','nota-interior','bajo','dembow','gabber','spray'];y=sum(wavfile.read(out/'render'/f'{n}.wav')[1] for n in names)
 y=sosfilt(butter(2,28,fs=SR,btype='high',output='sos'),y,axis=0);y[int(CUT*SR)-120:int(CUT*SR)]*=np.linspace(1,0,120)[:,None];y[int(CUT*SR):]=0;h.wav(out/'render/mezcla.wav',y)
 def measure(p):
  s=h.run(['ffmpeg','-v','info','-i',str(p),'-af','loudnorm=I=-13:TP=-1.6:LRA=10:print_format=json','-f','null','-']).stderr.decode(errors='replace');return json.JSONDecoder().raw_decode(s[s.rfind('{'):])[0]
 m=measure(out/'render/mezcla.wav');gain=min(-13-float(m['input_i']),-1.9-float(m['input_tp']));target=out/(out.name+'.m4a');h.run(['ffmpeg','-v','error','-n','-i',str(out/'render/mezcla.wav'),'-af',f'volume={gain}dB','-ar','48000','-c:a','aac','-b:a','256k',str(target)]);mm=measure(target);assert float(mm['input_tp'])<-.8
 h.js(out/'medidas.json',dict(duracion=DUR,aac=mm,ganancia_db=gain,golpe_final=HIT,corte=CUT,ultimo_rms=float(np.sqrt(np.mean(y[-800:]**2)))) )
 im,d=card('03 · dembow → gabber → arco digital → cierre duro')
 f,t,z=stft(y.mean(axis=1),SR,nperseg=1024,noverlap=512);sel=(f>=40)&(f<11000);a=np.clip((20*np.log10(np.abs(z[sel])+1e-8)+70)/55,0,1);rgb=np.stack([a*.9,a*.72,a],axis=-1);im.paste(Image.fromarray(np.uint8(rgb[::-1]*255)).resize((1120,365)),(40,145))
 for b,label in [(0,'dembow'),(24,'deformación'),(40,'gabber'),(64,'arco digital'),(88,'cierre')]:d.text((40+1120*START[b]/DUR,540),label,font=h.font(15),fill='#f0dfe8')
 h.png(out/'proceso'/f'03-mezcla-s{SEED}-{tag}.png',im);h.png(out/(out.name+'.png'),im);h.png(out/'og.png',im)
 frames=[Image.open(p).convert('RGB') for p in sorted((out/'proceso').glob('0[123]-*.png'))];gif=out/f'otra-vez-hasta-romper-proceso-s{SEED}-{tag}.gif'
 with gif.open('xb') as fh:frames[0].save(fh,format='GIF',save_all=True,append_images=frames[1:],duration=2600,loop=0,optimize=True)
 h.txt(out/'proceso/README.md','# Etapas reales\n\n01: partitura y encuentros antes de renderizar. 02: pistas y transformaciones antes de la mezcla. 03: espectrograma final. GIF de tres estados, 7.8 s, no animación interna. Semilla 18102692.\n')
 h.txt(out/'README.md',f'# Otra vez hasta romper\n\nCanek Zapata · 18 de octubre de 2026 · {DUR:.2f} s.\n\n[Audio]({target.name}) · [PNG]({out.name}.png) · [GIF]({gif.name}) · [Idea y referencias](../IDEA.md).\n\nDembow desde el primer golpe, deformación de ciclos, gabber y arco melódico con breaks. Una nota cambia por dentro y recibe los encuentros de las líneas. Repeticiones finales de 8/5/3/2/1 subdivisiones, golpe común y corte sin fade-out. Sin letra. Spray del motor original de la biblioteca.\n\nAAC: {mm["input_i"]} LUFS, {mm["input_tp"]} dBTP. Verificación técnica; no hubo escucha humana durante producción.\n')
 h.js(out/'receta-final.json',dict(archivos={str(p.relative_to(out)):h.sha(p) for p in out.rglob('*') if p.is_file()},semilla=SEED));print(json.dumps(dict(duracion=DUR,aac=mm,gif_bytes=gif.stat().st_size)))
if __name__=='__main__':
 if sys.argv[1]=='iniciar':init()
 elif sys.argv[1]=='sintetizar':synth(Path(sys.argv[2]))
 elif sys.argv[1]=='mezclar':finish(Path(sys.argv[2]))
