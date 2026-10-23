"""III. Coral: múltiplos que florecen, divisores que echan raíces."""
import json,os,sys,hashlib,subprocess
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter,sosfilt,stft
import matplotlib.pyplot as plt
from PIL import Image
import preludio as util
ROOT=Path(__file__).resolve().parent;BANK=ROOT.parent/'objetos/motor'
SR=48000;DUR=86;SEED=1610263
COL={'violin':'#e0bfdd','viola':'#bca6d4','chelo':'#9fcba9','bajo':'#679c93','clarinete':'#9dc2e3','metal':'#e7c58b','gong':'#b7bdc0'}
dump=util.dump;png=util.png;wav=util.wav;sha=util.sha;txt=util.textfile;pitch=util.pitch
def title(fig,s):
 fig.suptitle('RAÍCES DEL MISMO CIELO / '+s,x=.06,ha='left',fontsize=16)
 fig.text(.06,.025,'Jardín de afinidades · III. Coral · Canek Zapata · semilla 1610263',fontsize=10)
 fig.tight_layout(rect=(.035,.06,.985,.91))
def hz(m):return 440*2**((m-69)/12)
def initialize():
 I={n:[] for n in COL}
 def add(name,t,f,dur,v=.53,tipo=None,drift=None):
  e={'id':f'{name}-{len(I[name]):03}','t':t,'dur':dur,'m':float(69+12*np.log2(f/440)),'Hz_objetivo':f,'v':v,'tipo':tipo or ('normal' if name in ['clarinete','metal'] else 'roce' if name=='gong' else 'tasto' if name=='viola' else 'arco')}
  if drift:e['deriva_cents']=drift
  I[name].append(e)
 # I: el tema arriba, una quinta inmóvil por dentro; una tercera se abre y se retira.
 add('chelo',1,110,14,.46);add('viola',1.7,165,13.2,.43)
 for t,f,d in [(2,220,2.7),(5,247.5,2.6),(8,330,4.4),(12.6,293.3333333333,3.4)]:add('violin',t,f,d,.53)
 add('clarinete',3,220,4.1,.45);add('clarinete',8.1,247.5,3.9,.46);add('clarinete',12.7,220,2.9,.42)
 add('metal',5.3,137.5,5.8,.46);add('metal',12.2,146.6666666667,3.4,.43)
 # II: las raíces divisoras, con el motivo trasladado al grave.
 add('viola',21,165,15.8,.44);add('metal',21.7,220,7.4,.44)
 add('violin',22,264,6.3,.47);add('violin',29,330,4.4,.48);add('violin',33.8,264,4,.43)
 for t,f,d in [(22,110,2.5),(24.9,123.75,2.6),(28,165,5),(33.5,146.6666666667,4.4)]:add('chelo',t,f,d,.51)
 add('clarinete',23,198,4,.45);add('clarinete',28,220,4.4,.46);add('clarinete',33.4,198,4.3,.43)
 add('metal',30,132,7.8,.43);add('bajo',24,110,12,.35)
 # III: la pared se construye con entradas y divisiones de cuerda.
 add('chelo',43,110,16.8,.53);add('bajo',44,82.5,14.8,.37)
 add('metal',44.8,165,14.7,.46)
 add('viola',45.6,275,13.8,.50,drift=[[0,-8],[6,0],[8,0],[13.8,17]])
 add('violin',46.5,330,13.8,.53,drift=[[0,10],[5.1,0],[7.1,0],[13.8,-24]])
 add('clarinete',47.2,220,12.3,.47,drift=[[0,-7],[4.4,0],[6.4,0],[12.3,18]])
 add('violin',48.4,385,10.8,.33,drift=[[0,-5],[4,0],[7,5],[10.8,12]])
 add('metal',49.2,264,9.9,.37)
 add('viola',50.3,440,9.8,.35,drift=[[0,4],[3,0],[5,0],[9.8,-13]])
 add('gong',49.4,55,2.8,.20)
 # IV: memoria del cielo mayor dentro de un campo de raíces menores.
 add('viola',65,165,12,.43);add('chelo',65.6,110,13.7,.43)
 add('metal',66.3,137.5,4,.42);add('metal',71.1,132,7.5,.40)
 for t,f,d in [(66,220,2.2),(68.6,247.5,2.4),(71.4,330,3.4),(75.2,293.3333333333,3.3)]:add('clarinete',t,f,d,.47)
 add('violin',67,330,5.8,.43);add('violin',73.5,264,5,.40)
 add('viola',78,220,3.7,.32)
 P={'titulo':'Raíces del mismo cielo','movimiento':'III. Coral','duracion':DUR,'semilla':SEED,'instrumentos':I,'forma':{'I_multiplicacion':[1,17],'II_division':[21,39],'III_floracion':[43,61],'IV_memoria':[65,82]},'armonias':{'multiplicacion':'110 × (1, 3/2, 2, 5/2, 3, 7/2, 4)','division':'660 / (2, 3, 4, 5, 6), con duplicaciones de octava; 264 Hz = 132×2','tema':'220,247.5,330,293.333…; en el chelo una octava abajo','tercera_frase':'Divisiones virtuales de cuerdas y metal; meseta aproximada 51.6–53.6 s en el par 330×2 / 220×3. La afinación final se mide por nota, no se afirma fase común.'}}
 fig,ax=plt.subplots(figsize=(12,6.3),dpi=100)
 for name,events in I.items():
  for e in events:ax.plot([e['t'],e['t']+e['dur']],[e['m']]*2,color=COL[name],lw=3)
  ax.plot([],[],color=COL[name],label=name)
 for a,b,label in [(1,17,'I'),(21,39,'II'),(43,61,'III'),(65,82,'IV')]:ax.axvspan(a,b,alpha=.05,color='#e7c58b');ax.text(a+.3,72,label)
 ax.set(xlim=(0,DUR),ylim=(31,74),xlabel='segundos · cuatro frases con respiraciones',ylabel='altura escrita · MIDI');ax.legend(facecolor='#233238',labelcolor='#e9e5d5',fontsize=8,loc='lower right')
 title(fig,'01 / voces conservadas, raíces que cambian');fig.canvas.draw();nonce=os.urandom(24).hex()
 digest=hashlib.sha256(bytes(fig.canvas.buffer_rgba())+Path(__file__).read_bytes()+(ROOT/'coral-render.cjs').read_bytes()+(ROOT/'preludio.py').read_bytes()+nonce.encode()).hexdigest();tag=digest[:12]
 out=ROOT/f'coral-raices-del-mismo-cielo-s{SEED}-{tag}';out.mkdir(exist_ok=False)
 for d in ['proceso','render','fuentes']:(out/d).mkdir()
 png(out/'proceso'/f'01-partitura-s{SEED}-{tag}.png',fig);dump(out/'partitura.json',P)
 for p in [Path(__file__),ROOT/'coral-render.cjs',ROOT/'preludio.py']+list(BANK.glob('*.js')):
  with (out/'fuentes'/p.name).open('xb') as f:f.write(p.read_bytes())
 dump(out/'receta-inicial.json',{'id':digest,'nonce':nonce,'semilla':SEED,'fecha':'2026-10-16','banco_sha256':{p.name:sha(p) for p in BANK.glob('*.js')},'fuentes_sha256':{p.name:sha(p) for p in (out/'fuentes').iterdir()}})
 print(out,flush=True)
def probes(out):
 result=[]
 for p in sorted((out/'render').glob('sonda-*.wav')):
  sr,x=wavfile.read(p);m=float(p.stem.split('-')[-1]);values=[pitch(x,c) for c in [.4,.8,1.4,2]]
  result.append({'archivo':p.name,'Hz_objetivo':hz(m),'Hz':values,'error_cents':[1200*np.log2(f/hz(m)) if f else None for f in values]})
 dump(out/'sondas-medidas.json',result);print(json.dumps(result,ensure_ascii=False),flush=True)

def finish(out):
 P=json.loads((out/'partitura.json').read_text(encoding='utf8'));initial=json.loads((out/'receta-inicial.json').read_text(encoding='utf8'));tag=initial['id'][:12];N=round(SR*DUR)
 assert all(sha(BANK/n)==s for n,s in initial['banco_sha256'].items())
 stems={};details=[];isolated={}
 for name,events in P['instrumentos'].items():
  y=np.zeros(N,dtype=np.float32)
  for e in events:
   sr,x=wavfile.read(out/'render'/(e['id']+'.wav'));assert sr==SR and np.isfinite(x).all()
   f=e.get('Hz_objetivo',hz(e['m']));values=[pitch(x,e['dur']*q) for q in [.35,.55,.75]];valid=[v for v in values if v]
   measured=float(np.median(valid)) if valid else None;cents=1200*np.log2(measured/f) if measured else None
   correction=f/measured if name not in ['piano','gong'] and measured and abs(cents)<70 else 1
   if name in ['violin','viola','chelo','bajo','clarinete','metal'] and measured and abs(cents)>70:raise ValueError((e['id'],'altura fuera de registro',cents))
   times=np.arange(len(x))/SR;knots=e.get('deriva_cents',[[0,0],[e['dur'],0]])
   # Interpolación cúbica suave por tramo: velocidad nula en los nudos del encuentro.
   kt,kc=np.array(knots).T;ix=np.clip(np.searchsorted(kt,times,side='right')-1,0,len(kt)-2)
   u=np.clip((times-kt[ix])/(kt[ix+1]-kt[ix]),0,1);drift=kc[ix]+(kc[ix+1]-kc[ix])*(3*u*u-2*u*u*u)
   rate=correction*2**(drift/1200);indices=np.r_[0,np.cumsum(rate[:-1])]
   z=np.interp(indices,np.arange(len(x)),x,left=0,right=0).astype(np.float32)
   z*=np.minimum(1,times/.008)*np.minimum(1,np.maximum(0,(len(x)/SR-times)/.035))
   gain=1.
   if name not in ['piano','gong']:
    core=z[round(min(.12,e['dur']*.2)*SR):round(e['dur']*.8*SR)]
    gain=.04/max(float(np.sqrt(np.mean(core.astype(float)**2))),1e-9);z*=gain
   env=np.interp(times,[0,.08,e['dur']*.4,e['dur']*.8,e['dur'],e['dur']+(6 if name=='gong' else 1.3)],[.25,.85,1,.65,.12,0]) if e['dur']>1 else np.interp(times,[0,.04,e['dur'],e['dur']+(6 if name=='gong' else 1.3)],[.5,1,.65,0])
   z*=env*(e['v']/.6);a=round(e['t']*SR);count=min(len(z),N-a);y[a:a+count]+=z[:count]
   if e.get('deriva_cents'):isolated[e['id']]=z
   final=[]
   for q in [.35,.75]:
    c=e['dur']*q;det=pitch(z,c);d=float(np.interp(c,times,drift));target=f*2**(d/1200)
    final.append({'t_local':c,'Hz':det,'objetivo_Hz':target,'error_cents':1200*np.log2(det/target) if det else None})
   details.append({'id':e['id'],'crudo_Hz':values,'correccion_cents':1200*np.log2(correction),'calibracion_registro':gain,'final':final})
  active=np.abs(y)>1e-4;rms=np.sqrt(np.mean(y[active].astype(float)**2));y*= {'violin':.034,'viola':.034,'chelo':.040,'bajo':.024,'clarinete':.030,'metal':.023,'gong':.008}[name]/max(rms,1e-9)
  stems[name]=y;wav(out/'render'/(name+'-mezcla.wav'),y)
 # Etapa real: armonía y energía de los instrumentos ya sintetizados.
 fig,ax=plt.subplots(figsize=(12,6.3),dpi=100)
 for name,y in stems.items():
  w=4800;energy=np.sqrt(np.mean(y[:len(y)//w*w].reshape(-1,w).astype(float)**2,axis=1))
  ax.plot(np.arange(len(energy))*.1,energy,color=COL[name],label=name,lw=1)
 ax.set(xlim=(0,DUR),xlabel='segundos',ylabel='RMS antes del espacio y máster');ax.legend(facecolor='#233238',labelcolor='#e9e5d5',fontsize=8)
 title(fig,'02 / cuatro respiraciones del ensamble');png(out/'proceso'/f'02-ensamble-s{SEED}-{tag}.png',fig)
 dry=np.zeros((N,2));pans={'violin':-.48,'viola':-.22,'chelo':.26,'bajo':.03,'clarinete':.17,'metal':.45,'gong':-.05}
 for name,y in stems.items():
  angle=(pans[name]+1)*np.pi/4;dry+=np.column_stack((y*np.cos(angle),y*np.sin(angle)))
 wet=np.zeros_like(dry)
 for k,delay in enumerate([.043,.077,.113,.173,.257,.367,.523,.719,1.013,1.387,1.823]):
  shift=round(delay*SR);source=sosfilt(butter(1,5800-300*k,fs=SR,output='sos'),dry[:,::-1] if k%2 else dry,axis=0)
  wet[shift:]+=.11*np.exp(-delay)*source[:-shift]
 mix=dry+wet;mix*=np.minimum(1,np.maximum(0,(DUR-np.arange(N)/SR)/.8))[:,None];mix*=.76/np.max(np.abs(mix))
 base=f'coral-raices-del-mismo-cielo-s{SEED}-{tag}';wav(out/(base+'.wav'),mix)
 ff='C:/msys64/mingw64/bin/ffmpeg.exe'
 r=subprocess.run([ff,'-hide_banner','-nostdin','-n','-i',str(out/(base+'.wav')),'-af','loudnorm=I=-18:TP=-2:LRA=12','-c:a','aac','-b:a','256k',str(out/(base+'.m4a'))],capture_output=True,text=True);assert r.returncode==0,r.stderr
 r=subprocess.run([ff,'-hide_banner','-nostdin','-i',str(out/(base+'.m4a')),'-af','loudnorm=I=-18:TP=-2:LRA=12:print_format=json','-f','null','-'],capture_output=True,text=True);metrics=json.JSONDecoder().raw_decode(r.stderr[r.stderr.rfind('{'):])[0]
 r=subprocess.run([ff,'-v','error','-i',str(out/(base+'.m4a')),'-f','f32le','-ar',str(SR),'-ac','2','-'],capture_output=True,check=True);pcm=np.frombuffer(r.stdout,np.float32).reshape(-1,2)
 assert np.isfinite(pcm).all() and np.max(np.abs(pcm))<1 and abs(len(pcm)/SR-DUR)<.1
 fig,axes=plt.subplots(2,1,figsize=(12,6.3),dpi=100)
 for name,y in stems.items():
  w=4800;energy=np.sqrt(np.mean(y[:len(y)//w*w].reshape(-1,w).astype(float)**2,axis=1));axes[0].plot(np.arange(len(energy))*.1,energy,color=COL[name],label=name,lw=1)
 axes[0].legend(facecolor='#233238',labelcolor='#e9e5d5',fontsize=8);axes[0].set(xlim=(0,DUR),ylabel='RMS de las partes')
 f,tt,z=stft(pcm.mean(axis=1),SR,nperseg=8192,noverlap=6144);mask=(f>=70)&(f<2400);axes[1].pcolormesh(tt,f[mask],20*np.log10(np.abs(z[mask])+1e-8),cmap='magma',vmin=-85,vmax=-30,shading='auto');axes[1].set(xlim=(0,DUR),xlabel='segundos',ylabel='Hz · AAC final')
 title(fig,'03 / coral completo, cuatro frases');final=out/f'coral-resultado-s{SEED}-{tag}.png';png(final,fig)
 with Image.open(final) as im:
  for p in [out/'og.png',out/'proceso'/f'03-mezcla-s{SEED}-{tag}.png']:
   with p.open('xb') as f:im.save(f,'PNG')
 frames=[]
 for p in sorted((out/'proceso').glob('*.png')):
  with Image.open(p) as im:frames.append(im.convert('RGB').resize((900,472)).quantize(colors=128))
 gif=out/f'coral-proceso-s{SEED}-{tag}.gif'
 with gif.open('xb') as f:frames[0].save(f,format='GIF',save_all=True,append_images=frames[1:],duration=2600,loop=0,optimize=False)
 with Image.open(gif) as im:
  canvas=Image.new('RGB',(1200,210));duration=0
  for i in range(im.n_frames):im.seek(i);duration+=im.info['duration'];canvas.paste(im.convert('RGB').resize((400,210)),(400*i,0))
  assert im.n_frames==3 and duration==7800 and gif.stat().st_size<15_000_000
  with (out/'proceso'/f'04-revision-s{SEED}-{tag}.png').open('xb') as f:canvas.save(f,'PNG')
 errors=[abs(p['error_cents']) for e in details for p in e['final'] if p['error_cents'] is not None]
 dump(out/'verificacion.json',{'aac':metrics,'duracion_decodificada':len(pcm)/SR,'pico_muestra':float(np.max(np.abs(pcm))),'notas':len(details),'ventanas':len(details)*2,'periodicidad_YIN':len(errors),'dentro_50cents':int(np.sum(np.array(errors)<50)),'mediana_abs_cents':float(np.median(errors)),'detalle':details,'banco_intacto':True,'metodo':'YIN abierto 70–1200 Hz, ventanas 200 ms; El gong es inarmónico: su periodicidad, si aparece, no es una evaluación de afinación.','escucha':'Sin escucha humana durante producción.'})
 txt(out/'proceso'/'README.md','# Etapas reales\n\n1. Voces y armonías escritas antes de síntesis.\n2. Energía de siete partes instrumentales ya sintetizadas, afinadas y fraseadas.\n3. Energía de las partes y espectrograma del AAC final.\n4. Revisión de cuadros decodificados del GIF.\n\nGIF 7.8 s, tres etapas efectivamente capturadas. Semilla 1610263; algunos motores conservan semillas internas.\n')
 txt(out/'README.md',f'# Raíces del mismo cielo\n\nIII. Coral de Jardín de afinidades. Canek Zapata, 16 de octubre de 2026. 1:26.\n\nCuatro frases: I 1–17 s, II 21–39, III 43–61, IV 65–82, más colas. Violín, viola, chelo, contrabajo, clarinete bajo, trombón con sordina cup y un roce de gong. Las familias de múltiplos de 110 Hz y divisores de 660 Hz dan colores de La mayor/menor; el tema 220–247.5–330–293.333 Hz aparece arriba y después en el chelo una octava abajo. Se sostienen notas comunes entre cambios internos de cada frase. Las pausas entre frases permiten oír la retirada.\n\nLa tercera frase construye una pared por entradas sucesivas y divisiones virtuales de violines, violas y metal. Parciales séptimos aportan 385 Hz; pequeñas desviaciones cúbicas hacen que las voces se acerquen y se separen. La última frase conserva la tercera mayor y después la cambia por su vecina menor (137.5 → 132 Hz), mientras el resto sostiene la memoria del acorde.\n\nModelos originales cuerda.js, clarinete.js, metal.js y gong.js, sin cambios. Afinación pequeña por nota cuando YIN es estable y deriva por remuestreo del audio físico. Sin síntesis aditiva ni voz. Subarmónico significa alturas compuestas por división, no una técnica física de arco. El gong queda sin corrección de altura. Las partes virtuales admiten solapamientos y divisiones: no se afirma una ejecución por un único instrumentista por familia.\n\nAudio: {base}.m4a. WAV y stems locales excluidos de git. Partitura, fuentes y mediciones conservadas. PNG final, og.png 1200×630 y GIF de proceso 7.8 s. Sin escucha humana durante producción.\n')
 dump(out/'receta.json',{'id':initial['id'],'nonce':initial['nonce'],'semilla':SEED,'contenido_sha256':{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}})
 print(json.dumps({'carpeta':str(out),'notas':len(details),'aac':metrics,'mediana_cents':float(np.median(errors))},ensure_ascii=False),flush=True)
if __name__=='__main__':
 if sys.argv[1]=='iniciar':initialize()
 elif sys.argv[1]=='sondas':probes(Path(sys.argv[2]))
 elif sys.argv[1]=='terminar':finish(Path(sys.argv[2]))
