"""Cerquita de ti: partitura, render con motores existentes, paredes aditivas y mezcla.
Cada ejecución crea su carpeta exclusiva; nunca sustituye una entrega.
"""
from pathlib import Path
import hashlib,json,os,sys,subprocess
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter,sosfilt,stft
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent; REPO=ROOT.parent
SR=48000; BPM=84; B=60/BPM; BAR=4*B; DUR=32*BAR+4; SEED=16102684
COL=[(237,179,163),(153,198,213),(222,208,166),(178,189,143),(186,160,208)]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p,x):
 with p.open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
def txt(p,s):
 with p.open('x',encoding='utf8') as f:f.write(s)
def png(p,im):
 with p.open('xb') as f:im.save(f,'PNG')
def wav(p,y):
 with p.open('xb') as f:wavfile.write(f,SR,np.asarray(y,np.float32))
def run(a):return subprocess.run(a,check=True,capture_output=True,text=True,encoding='utf8',errors='replace')
def card(label):
 im=Image.new('RGB',(1200,630),(24,26,36)); d=ImageDraw.Draw(im)
 d.text((44,28),'CERQUITA DE TI',font=ImageFont.truetype('C:/Windows/Fonts/georgia.ttf',44),fill=(245,228,213))
 d.text((46,92),label,font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',19),fill=COL[1])
 d.text((44,595),'Canek Zapata · 84 BPM · piano / clarinete bajo / chelo · semilla '+str(SEED),font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',15),fill=(192,187,195))
 return im,d
CH={'C':(48,[60,64,67,71]),'Am':(45,[60,64,67,69]),'F':(41,[60,64,65,69]),'G':(43,[59,62,67,69]),'Dm':(38,[60,62,65,69]),'Fm':(41,[60,65,68,72])}
PROG=['C','C','C','Am','F','G','C','Am','F','G','Dm','Am','F','G','C','G','Am','F','C','G','F','G','Am','F','C','G','C','G','F','Fm','C','C']
ROWS=[(2,'si te que das un ra ti to',[64,64,67,67,69,67,64,62]),(4,'ca be el mun do en el so fá',[65,65,69,69,67,65,64,62,62]),(6,'yo te guar do mi la di to',[64,67,67,69,67,64,62,60]),(8,'por si quie res des can sar',[65,69,69,67,65,64,62]),(10,'no ha ce fal ta de cir na da',[65,65,69,69,67,64,64,62,64]),(12,'tu ma ni ta jun to a mí',[65,65,69,67,67,65,62,62]),(14,'cer qui ta cer qui ta de ti',[67,69,67,64,67,69,67,64]),(16,'se me a flo ja el co ra zón',[69,69,72,71,69,67,65,64,65]),(18,'cer qui ta cer qui ta de ti',[67,69,67,64,67,69,67,64]),(20,'to do ca be en es ta can ción',[69,69,67,65,65,64,62,62,62]),(22,'si la tar de se nos duer me',[64,64,69,69,67,65,64,65]),(24,'yo me que do un po co más',[64,64,67,67,69,67,64,62]),(26,'cer qui ta cer qui ta de ti',[67,69,67,64,67,69,67,64]),(28,'mi lu gar es jun to a ti',[69,69,67,65,68,68,65,60])]
def init():
 I={n:[] for n in ['piano','clarinete','chelo']}; phrases=[]
 for bar,name in enumerate(PROG):
  root,ch=CH[name]; t=bar*BAR; chorus=14<=bar<22 or 26<=bar<30
  for k in range(8 if chorus else 4):
   step=.5 if chorus else 1; m=ch[[0,2,1,3,2,1,3,2][k]]
   I['piano'].append(dict(t=t+k*step*B+.018*(k%2),dur=.6*B,m=m,v=.48 if chorus else .38,tipo='martillo'))
  I['chelo'].append(dict(t=t+.02,dur=3.65*B,m=root,v=.48,tipo='arco'))
  if bar%2==1 and bar>1:
   for k,m in enumerate([ch[2]-12,ch[1]-12]):I['clarinete'].append(dict(t=t+(2.75+k*.55)*B,dur=.58*B,m=m,v=.48,tipo='normal'))
 for bar,line,notes in ROWS:
  syll=line.split(); assert len(notes)==len(syll),(line,len(notes),len(syll))
  # Six beats of syllables plus a sustained ending, leaving space for responses.
  weights=np.array([.55]*(len(syll)-1)+[1.35]); weights*=6.5/weights.sum(); cursor=(bar*4+.35)*B
  ev=[]
  for s,m,w in zip(syll,notes,weights):ev.append(dict(t=cursor,dur=float(w*B),texto=s,nota=m));cursor+=w*B
  phrases.append(dict(nivel=.7,pan=0,eventos=ev))
 score=dict(semilla=SEED,duracion=DUR,bpm=BPM,progresion=PROG,instrumentos=I,frases=phrases)
 im,d=card('01 / partitura real: la voz entre dos paredes de resonancia')
 for i,(bar,line,notes) in enumerate(ROWS):
  for k,m in enumerate(notes):
   x=60+(bar*4+k*6.5/len(notes))/(32*4)*1080;y=430-(m-60)*19
   d.ellipse((x-4,y-4,x+4,y+4),fill=COL[0])
 for j,label in enumerate(['intro','verso','pre','coro','verso','coro','coda']):d.text((50+[0,2,10,14,22,26,30][j]/32*1080,530),label,fill=COL[1])
 nonce=os.urandom(24).hex(); digest=hashlib.sha256(im.tobytes()+Path(__file__).read_bytes()+nonce.encode()).hexdigest(); tag=digest[:12]
 out=ROOT/f'cerquita-de-ti-s{SEED}-{tag}';out.mkdir(exist_ok=False)
 for folder in ['render','proceso','fuentes']:(out/folder).mkdir()
 png(out/'proceso'/f'01-partitura-s{SEED}-{tag}.png',im); js(out/'partitura.json',score)
 sources=[Path(__file__),REPO/'mi-boca-en-otra-parte/render.cjs',REPO/'lo-que-no-sono/voz.cjs']+list((REPO/'objetos/motor').glob('*.js'))
 hashes={str(p.relative_to(REPO)):sha(p) for p in sources}
 for p in sources:
  with (out/'fuentes'/p.name).open('xb') as f:f.write(p.read_bytes())
 js(out/'receta-inicial.json',dict(id=digest,nonce=nonce,semilla=SEED,fuentes=hashes,imagen=sha(next((out/'proceso').glob('*.png')))))
 print(out,flush=True)
def load(out,name):
 sr,y=wavfile.read(out/'render'/f'{name}.wav');assert sr==SR and np.isfinite(y).all()
 return y.mean(axis=1) if y.ndim==2 else y
def norm(y,target):
 active=np.abs(y)>max(1e-7,np.max(np.abs(y))*.025)
 rms=np.sqrt(np.mean(y[active].astype(float)**2));return y*(10**(target/20)/max(rms,1e-8))
def finish(out):
 tag=out.name.split('-')[-1];N=int(np.ceil(DUR*SR));rng=np.random.default_rng(SEED)
 tracks={n:norm(load(out,n),v) for n,v in [('voz',-20),('piano',-29),('clarinete',-31),('chelo',-30)]}
 walls=[np.zeros(N,np.float32),np.zeros(N,np.float32)];freqs=[]
 for bar,name in enumerate(PROG):
  root,ch=CH[name];base=440*2**((root-69)/12);start=int(bar*BAR*SR);length=min(int((BAR+1.5)*SR),N-start);t=np.arange(length)/SR
  env=np.minimum(1,t/1.15)*np.minimum(1,(length/SR-t)/1.45);env=np.sin(np.maximum(0,env)*np.pi/2)**2
  chorus=14<=bar<22 or 26<=bar<30; gain=1 if chorus else .43
  for side in range(2):
   ratios=[2,3,4,5,6,7,9,11,13] if side==0 else [12/n for n in [3,4,5,6,7,9,11]]
   z=np.zeros(length); fs=[]
   for k,r in enumerate(ratios):
    f=base*r;fs.append(f);amp=1/(1+k)**.8
    if side==0 and k>=5:amp*=.32
    z+=amp*np.sin(2*np.pi*f*t+rng.uniform(0,2*np.pi))*(.9+.1*np.sin(2*np.pi*.17*t+k))
   walls[side][start:start+length]+=(z*env*gain).astype(np.float32)
   freqs.append(dict(compas=bar+1,lado=side,Hz=fs,ley='n*f' if side==0 else '12*f/n'))
 walls=[norm(w,-33) for w in walls];js(out/'paredes-frecuencias.json',freqs)
 for n,w in zip(['pared-armonica','pared-subarmonica'],walls):wav(out/'render'/f'{n}.wav',w)
 center=sum(tracks.values());wav(out/'render'/'boceto-centro.wav',center)
 run(['ffmpeg','-v','error','-n','-i',str(out/'render/boceto-centro.wav'),'-ss',str(14*BAR),'-t','23','-c:a','aac','-b:a','192k',str(out/f'boceto-centro-s{SEED}-{tag}.m4a')])
 im,d=card('02 / cuatro fuentes centrales renderizadas, antes de las paredes')
 for j,(name,y) in enumerate(tracks.items()):
  a=np.array_split(y,1060);r=np.array([np.sqrt(np.mean(v*v)) for v in a]);r/=max(r.max(),1e-8)
  d.text((48,145+j*100),name,fill=COL[j]);d.line([(90+k,210+j*100-float(v)*45) for k,v in enumerate(r)],fill=COL[j],width=2)
 png(out/'proceso'/f'02-centro-s{SEED}-{tag}.png',im)
 mix=np.column_stack([center,center])*.707
 mix[:,0]+=walls[0]*.96+walls[1]*.16;mix[:,1]+=walls[1]*.96+walls[0]*.16
 # Short, low-level room around central sources; dry lead remains in the middle.
 for delay,g in [(.071,.10),(.113,.075),(.181,.05),(.269,.025)]:
  off=int(delay*SR);mix[off:,0]+=center[:-off]*g;mix[off:,1]+=center[:-off]*g*.92
 fade=np.minimum(1,np.arange(N)/SR/1.4)*np.minimum(1,(N-1-np.arange(N))/SR/3)
 mix*=fade[:,None];mix=sosfilt(butter(2,45,fs=SR,btype='highpass',output='sos'),mix,axis=0)
 assert np.isfinite(mix).all();wav(out/'render/mezcla-previa.wav',mix)
 af='loudnorm=I=-17:TP=-1.5:LRA=10:print_format=json'
 result=run(['ffmpeg','-hide_banner','-n','-i',str(out/'render/mezcla-previa.wav'),'-af',af,'-ar',str(SR),'-c:a','pcm_s24le',str(out/f'cerquita-de-ti-s{SEED}-{tag}.wav')])
 txt(out/'normalizacion.txt',result.stderr)
 final=out/f'cerquita-de-ti-s{SEED}-{tag}.m4a';run(['ffmpeg','-v','error','-n','-i',str(out/f'cerquita-de-ti-s{SEED}-{tag}.wav'),'-c:a','aac','-b:a','256k',str(final)])
 im,d=card('03 / mezcla: armónicos a la izquierda, subarmónicos a la derecha')
 for side in range(2):
  f,ts,z=stft(mix[:,side],SR,nperseg=2048,noverlap=1024);sel=(f>100)&(f<3200);a=20*np.log10(abs(z[sel])+1e-6);a=np.clip((a+75)/55,0,1)
  rgb=np.zeros((*a.shape,3),np.uint8)
  for k,c in enumerate(COL[side]):rgb[:,:,k]=(a*c).astype(np.uint8)
  tile=Image.fromarray(rgb[::-1]).resize((530,350));im.paste(tile,(50+side*570,180))
  d.text((50+side*570,150),['L / pared armónica','R / pared subarmónica'][side],fill=COL[side])
 png(out/'proceso'/f'03-mezcla-s{SEED}-{tag}.png',im);png(out/f'cerquita-de-ti-s{SEED}-{tag}.png',im);png(out/'og.png',im)
 frames=[Image.open(p).convert('RGB') for p in sorted((out/'proceso').glob('*.png'))];pal=frames[-1].quantize(colors=128)
 frames=[v.quantize(palette=pal) for v in frames];gif=out/f'cerquita-de-ti-proceso-s{SEED}-{tag}.gif'
 with gif.open('xb') as h:frames[0].save(h,format='GIF',save_all=True,append_images=frames[1:],duration=2400,loop=0,optimize=False)
 measures=dict(duracion=DUR,bpm=BPM,pico_previo=float(abs(mix).max()),correlacion_LR=float(np.corrcoef(mix.T)[0,1]),rms={k:float(np.sqrt(np.mean(v*v))) for k,v in tracks.items()},gif_bytes=gif.stat().st_size)
 js(out/'medidas.json',measures)
 verification=run(['ffmpeg','-hide_banner','-i',str(final),'-af','ebur128=peak=true','-f','null','-']);txt(out/'verificacion-aac.txt',verification.stderr)
 recipe=json.loads((out/'receta-inicial.json').read_text('utf8'));recipe['archivos']={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()};js(out/'receta-final.json',recipe)
 txt(out/'proceso/README.md','# Etapas reales\n\n1. Partitura antes del render.\n2. Envolventes del centro sintetizado; boceto de coro conservado.\n3. Espectrogramas de la mezcla con paredes.\n\nEl GIF reúne estas tres etapas sucesivas, no una animación interna del sintetizador. 7.2 segundos. Semilla '+str(SEED)+'. Nombres exclusivos con hash de ejecución; parámetros y hashes en las recetas.\n')
 txt(out/'README.md',f'# Cerquita de ti\n\nCanek Zapata · 16 de octubre de 2026. {DUR:.2f} segundos, 84 BPM.\n\n[Escuchar]({final.name}) · [Boceto del centro](boceto-centro-s{SEED}-{tag}.m4a) · [PNG](cerquita-de-ti-s{SEED}-{tag}.png) · [GIF de proceso]({gif.name}) · [Etapas](proceso/README.md).\n\nVoz Sabina Difonos PSOLA y tres instrumentos físicos: piano, clarinete bajo y chelo, al centro. Dos campos aditivos laterales con series armónicas y divisoras; se abren durante el coro. Pop sin batería, pulso en piano y chelo. Forma: intro, verso, pre, coro, verso breve, coro y coda. Coda con iv menor. El canto conserva sílabas y alturas en partitura.json.\n\nMediciones en medidas.json y verificacion-aac.txt. No se realizó escucha humana durante la producción; inteligibilidad y valoración musical quedan para la escucha de Canek. WAV maestro y pistas quedan locales. Motores originales utilizados sin modificación.\n')
 print(out,flush=True)
if __name__=='__main__':
 if sys.argv[1]=='iniciar':init()
 elif sys.argv[1]=='terminar':finish(Path(sys.argv[2]))
