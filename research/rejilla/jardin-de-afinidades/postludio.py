"""V. Retorno del tema, reunión breve y una separación que conserva el decaimiento final."""
from pathlib import Path
import json,os,sys,hashlib,subprocess
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter,sosfilt,stft
import matplotlib.pyplot as plt
from PIL import Image
import preludio as util
ROOT=Path(__file__).resolve().parent;BANK=ROOT.parent/'objetos/motor';SR=48000;DUR=76;SEED=1610268
COL={'piano':'#e7c58b','viola':'#d3acdc','chelo':'#9fcba9','clarinete':'#9dc2e3','metal':'#dca895','piano_final':'#eee6c5'}
dump=util.dump;png=util.png;wav=util.wav;sha=util.sha;txt=util.textfile;pitch=util.pitch
def hz(m):return 440*2**((m-69)/12)
def title(fig,s):
 fig.suptitle('CADA QUIEN GUARDA OTRA LUZ / '+s,x=.06,ha='left',fontsize=16)
 fig.text(.06,.025,'Jardín de afinidades · V. Postludio · Canek Zapata · semilla 1610268',fontsize=10)
 fig.tight_layout(rect=(.035,.06,.985,.91))
def local_clock(beat,bpm0,bpm1):
 k=(bpm1-bpm0)/4
 return float(60*beat/bpm0 if abs(k)<1e-8 else 60/k*np.log((bpm0+k*beat)/bpm0))
def initialize():
 I={n:[] for n in COL};phrases=[]
 def add(name,t,m,dur,v=.53,f=None,drift=None):
  e={'id':f'{name}-{len(I[name]):03}','t':float(t),'m':float(m),'dur':float(dur),'v':v,'tipo':'martillo' if name.startswith('piano') else 'normal' if name in ['clarinete','metal'] else 'tasto' if name=='chelo' else 'arco'}
  if f:e['Hz_objetivo']=float(f)
  if drift:e['deriva_cents']=drift
  I[name].append(e)
 def phrase(t,notes,b0,b1,v=.56):
  phrases.append({'t':t,'notas':notes,'BPM_inicio':b0,'BPM_fin':b1,'regla':'BPM lineal en tiempos de negra: t(b)=60/k log((BPM0+k b)/BPM0)'})
  for k,(beat,length) in enumerate([(0,.46),(.5,.46),(1,1.43),(2.5,.48)]):
   if k<len(notes):add('piano',t+local_clock(beat,b0,b1),notes[k],local_clock(beat+length,b0,b1)-local_clock(beat,b0,b1),v+[0,-.07,.03,-.08][k])
 phrase(.8,[57,59,64,62],52,62,.52)
 phrase(6.6,[60,59,57,52],56,64,.49)
 phrase(12.2,[57,59,64,62],60,66,.54)
 phrase(19,[57,59,64,62],72,92,.60)
 phrase(25,[60,62,59,57],88,104,.61)
 phrase(30.2,[57,59,64,62],104,88,.59)
 phrase(43,[57,59,64],52,40,.45)
 for t,m,l in [(1,45,2.5),(7,43,2),(13,45,2.6),(19,41,2),(25,47,1.4),(31,45,2.5)]:add('piano',t,m,l,.34)
 add('chelo',12.5,45,4,.47);add('clarinete',15,52,2.8,.44)
 for k,(t,m,d) in enumerate([(19.5,57,.55),(20.3,59,.55),(21.2,64,1.4),(23.3,62,.8)]):add('clarinete',t,m,d,.48+.02*(k==2))
 for t,m,d in [(22.4,64,1.0),(23.8,62,.9),(25.1,57,1.6),(27.5,59,1.4)]:add('viola',t,m,d,.48)
 for t,f,d in [(19.8,110,3.2),(24.2,123.75,2.4),(28.2,165,3.1)]:add('chelo',t,69+12*np.log2(f/440),d,.49,f=f)
 for t,f,d in [(22,165,3.8),(27.1,146.6666666667,3.1)]:add('metal',t,69+12*np.log2(f/440),d,.45,f=f)
 # Reunión breve: las tres voces comparten una zona de990 Hz desde fundamentales distintas.
 add('chelo',32,45,6.4,.51,f=110)
 add('viola',32.5,64,6.4,.53,f=330,drift=[[0,-10],[2,0],[3.1,0],[6.4,16]])
 add('clarinete',33,55,5.2,.49,f=198,drift=[[0,10],[1.5,0],[2.6,0],[5.2,-18]])
 add('metal',33.6,52,4.5,.45,f=165)
 add('viola',34.2,61,3.8,.36,f=275)
 # Salida más larga que la reunión. Las voces se llevan notas distintas.
 add('viola',39,64,10.8,.46,f=330,drift=[[0,0],[3,0],[8,25],[10.8,29]])
 add('clarinete',41.1,57,8.2,.45,f=220,drift=[[0,0],[2.5,0],[6,-22],[8.2,-27]])
 add('metal',40,52,6.8,.42,f=165)
 add('chelo',40.8,45,6.4,.42,f=110)
 add('metal',49.4,48,4.5,.38,f=132)
 add('clarinete',52.2,59,3.2,.39,f=247.5)
 add('viola',53,59,6.2,.38,f=247.5)
 for t,f,d,v in [(49.3,146.6666666667,3.3,.43),(53.4,132,2.8,.40),(56.8,123.75,5.3,.36)]:add('chelo',t,69+12*np.log2(f/440),d,v,f=f)
 # Una nota de piano sola; el instrumento entrega su decaimiento sin envolvente ni espacio adicional.
 add('piano_final',65.5,64,8.5,.40)
 P={'titulo':'Cada quien guarda otra luz','movimiento':'V. Postludio','semilla':SEED,'duracion':DUR,'instrumentos':I,'frases_piano':phrases,'forma':{'recuerdo':[0,18],'reunion':[18,39],'separacion':[39,65.5],'ultimo_cuerpo':[65.5,76]},'dinamica_s':[[0,.70],[12,.82],[19,1],[28,1.25],[34,1.50],[38,.9],[40,.72],[48,.55],[58,.35],[64,.22],[76,.2]],'cierre':'Mi4 de piano solo a65.5, sin fade artificial ni espacio añadido; off a74 cuando el decaimiento ya es muy débil. Ganancia constante en su stem.'}
 fig,axes=plt.subplots(2,1,figsize=(12,6.3),dpi=100)
 for name,evs in I.items():
  for e in evs:axes[0].plot([e['t'],e['t']+e['dur']],[e['m']]*2,color=COL[name],lw=3)
  axes[0].plot([],[],color=COL[name],label=name)
 axes[0].set(xlim=(0,DUR),ylim=(41,68),xlabel='segundos',ylabel='altura escrita · MIDI');axes[0].legend(facecolor='#233238',labelcolor='#e9e5d5',ncol=3,fontsize=8)
 for ph in phrases:
  axes[1].plot([ph['t'],ph['t']+local_clock(4,ph['BPM_inicio'],ph['BPM_fin'])],[ph['BPM_inicio'],ph['BPM_fin']],color='#e7c58b',lw=2)
 axes[1].set(xlim=(0,DUR),ylim=(30,115),xlabel='segundos · después el tiempo lo llevan las respiraciones',ylabel='BPM de las frases')
 title(fig,'01 / recordar, reunirse, dejar ir');fig.canvas.draw();nonce=os.urandom(24).hex()
 digest=hashlib.sha256(bytes(fig.canvas.buffer_rgba())+Path(__file__).read_bytes()+(ROOT/'postludio-render.cjs').read_bytes()+(ROOT/'preludio.py').read_bytes()+nonce.encode()).hexdigest();tag=digest[:12]
 out=ROOT/f'postludio-cada-quien-guarda-s{SEED}-{tag}';out.mkdir(exist_ok=False)
 for d in ['render','proceso','fuentes']:(out/d).mkdir()
 png(out/'proceso'/f'01-forma-s{SEED}-{tag}.png',fig);dump(out/'partitura.json',P)
 for p in [Path(__file__),ROOT/'postludio-render.cjs',ROOT/'preludio.py']+list(BANK.glob('*.js')):
  with (out/'fuentes'/p.name).open('xb') as f:f.write(p.read_bytes())
 dump(out/'receta-inicial.json',{'id':digest,'nonce':nonce,'semilla':SEED,'fecha':'2026-10-16','banco_sha256':{p.name:sha(p) for p in BANK.glob('*.js')},'fuentes_sha256':{p.name:sha(p) for p in (out/'fuentes').iterdir()}})
 print(out,flush=True)

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
   correction=f/measured if not name.startswith('piano') and measured and abs(cents)<70 else 1
   if name in ['violin','viola','chelo','bajo','clarinete','metal'] and measured and abs(cents)>70:raise ValueError((e['id'],'altura fuera de registro',cents))
   times=np.arange(len(x))/SR;knots=e.get('deriva_cents',[[0,0],[e['dur'],0]])
   # Interpolación cúbica suave por tramo: velocidad nula en los nudos del encuentro.
   kt,kc=np.array(knots).T;ix=np.clip(np.searchsorted(kt,times,side='right')-1,0,len(kt)-2)
   u=np.clip((times-kt[ix])/(kt[ix+1]-kt[ix]),0,1);drift=kc[ix]+(kc[ix+1]-kc[ix])*(3*u*u-2*u*u*u)
   rate=correction*2**(drift/1200);indices=np.r_[0,np.cumsum(rate[:-1])]
   z=np.interp(indices,np.arange(len(x)),x,left=0,right=0).astype(np.float32)
   z*=np.minimum(1,times/.008)*np.minimum(1,np.maximum(0,(len(x)/SR-times)/.035))
   gain=1.
   if not name.startswith('piano'):
    core=z[round(min(.12,e['dur']*.2)*SR):round(e['dur']*.8*SR)]
    gain=.04/max(float(np.sqrt(np.mean(core.astype(float)**2))),1e-9);z*=gain
   env=np.interp(times,[0,.08,e['dur']*.4,e['dur']*.8,e['dur'],e['dur']+(6 if name=='gong' else 1.3)],[.25,.85,1,.65,.12,0]) if e['dur']>1 else np.interp(times,[0,.04,e['dur'],e['dur']+(6 if name=='gong' else 1.3)],[.5,1,.65,0])
   if name=='piano_final':z=x.astype(np.float32).copy()
   else:z*=env*(e['v']/.6)*np.interp(times+e['t'],*np.array(P['dinamica_s']).T)
   a=round(e['t']*SR);count=min(len(z),N-a);y[a:a+count]+=z[:count]
   if e.get('deriva_cents'):isolated[e['id']]=z
   final=[]
   for q in [.35,.75]:
    c=e['dur']*q;det=pitch(z,c);d=float(np.interp(c,times,drift));target=f*2**(d/1200)
    final.append({'t_local':c,'Hz':det,'objetivo_Hz':target,'error_cents':1200*np.log2(det/target) if det else None})
   details.append({'id':e['id'],'crudo_Hz':values,'correccion_cents':1200*np.log2(correction),'calibracion_registro':gain,'final':final})
  if name=='piano_final':y*=.10/max(float(np.max(np.abs(y))),1e-9)
  else:
   active=np.abs(y)>1e-4;rms=np.sqrt(np.mean(y[active].astype(float)**2));y*= {'piano':.052,'viola':.036,'chelo':.042,'clarinete':.032,'metal':.027}[name]/max(rms,1e-9)
  stems[name]=y;wav(out/'render'/(name+'-mezcla.wav'),y)
 # Etapa real: armonía y energía de los instrumentos ya sintetizados.
 fig,ax=plt.subplots(figsize=(12,6.3),dpi=100)
 for name,y in stems.items():
  w=4800;energy=np.sqrt(np.mean(y[:len(y)//w*w].reshape(-1,w).astype(float)**2,axis=1))
  ax.plot(np.arange(len(energy))*.1,energy,color=COL[name],label=name,lw=1)
 ax.set(xlim=(0,DUR),xlabel='segundos',ylabel='RMS antes del espacio y máster');ax.legend(facecolor='#233238',labelcolor='#e9e5d5',fontsize=8)
 title(fig,'02 / las voces se retiran; queda el piano');png(out/'proceso'/f'02-ensamble-s{SEED}-{tag}.png',fig)
 dry=np.zeros((N,2));room=np.zeros_like(dry);pans={'piano':-.12,'viola':-.35,'chelo':.30,'clarinete':.12,'metal':.42,'piano_final':0}
 for name,y in stems.items():
  angle=(pans[name]+1)*np.pi/4;panned=np.column_stack((y*np.cos(angle),y*np.sin(angle)));dry+=panned
  if name!='piano_final':room+=panned
 wet=np.zeros_like(dry)
 for k,delay in enumerate([.043,.077,.113,.173,.257,.367,.523,.719,1.013,1.387,1.823]):
  shift=round(delay*SR);source=sosfilt(butter(1,5800-300*k,fs=SR,output='sos'),room[:,::-1] if k%2 else room,axis=0)
  wet[shift:]+=.11*np.exp(-delay)*source[:-shift]
 mix=dry+wet;mix*=.76/np.max(np.abs(mix))
 base=f'postludio-cada-quien-guarda-s{SEED}-{tag}';wav(out/(base+'.wav'),mix)
 ff='C:/msys64/mingw64/bin/ffmpeg.exe'
 meter=subprocess.run([ff,'-hide_banner','-nostdin','-i',str(out/(base+'.wav')),'-af','loudnorm=I=-18:TP=-2:LRA=20:print_format=json','-f','null','-'],capture_output=True,text=True)
 before=json.JSONDecoder().raw_decode(meter.stderr[meter.stderr.rfind('{'):])[0];gain=min(-18-float(before['input_i']),-2-float(before['input_tp']))
 r=subprocess.run([ff,'-hide_banner','-nostdin','-n','-i',str(out/(base+'.wav')),'-af',f'volume={gain:.4f}dB','-c:a','aac','-b:a','256k',str(out/(base+'.m4a'))],capture_output=True,text=True);assert r.returncode==0,r.stderr
 dump(out/'master-ganancia.json',{'tipo':'ganancia fija sin compresión','ganancia_dB':gain,'premaster':before,'ultimo_piano':'sin envolvente posterior ni reverb; escala constante'})
 r=subprocess.run([ff,'-hide_banner','-nostdin','-i',str(out/(base+'.m4a')),'-af','loudnorm=I=-18:TP=-2:LRA=12:print_format=json','-f','null','-'],capture_output=True,text=True);metrics=json.JSONDecoder().raw_decode(r.stderr[r.stderr.rfind('{'):])[0]
 r=subprocess.run([ff,'-v','error','-i',str(out/(base+'.m4a')),'-f','f32le','-ar',str(SR),'-ac','2','-'],capture_output=True,check=True);pcm=np.frombuffer(r.stdout,np.float32).reshape(-1,2)
 assert np.isfinite(pcm).all() and np.max(np.abs(pcm))<1 and abs(len(pcm)/SR-DUR)<.1
 fig,axes=plt.subplots(2,1,figsize=(12,6.3),dpi=100)
 for name,y in stems.items():
  w=4800;energy=np.sqrt(np.mean(y[:len(y)//w*w].reshape(-1,w).astype(float)**2,axis=1));axes[0].plot(np.arange(len(energy))*.1,energy,color=COL[name],label=name,lw=1)
 axes[0].legend(facecolor='#233238',labelcolor='#e9e5d5',fontsize=8);axes[0].set(xlim=(0,DUR),ylabel='RMS de las partes')
 f,tt,z=stft(pcm.mean(axis=1),SR,nperseg=8192,noverlap=6144);mask=(f>=70)&(f<2400);axes[1].pcolormesh(tt,f[mask],20*np.log10(np.abs(z[mask])+1e-8),cmap='magma',vmin=-85,vmax=-30,shading='auto');axes[1].set(xlim=(0,DUR),xlabel='segundos',ylabel='Hz · AAC final')
 title(fig,'03 / postludio completo');final=out/f'postludio-resultado-s{SEED}-{tag}.png';png(final,fig)
 with Image.open(final) as im:
  for p in [out/'og.png',out/'proceso'/f'03-mezcla-s{SEED}-{tag}.png']:
   with p.open('xb') as f:im.save(f,'PNG')
 frames=[]
 for p in sorted((out/'proceso').glob('*.png')):
  with Image.open(p) as im:frames.append(im.convert('RGB').resize((900,472)).quantize(colors=128))
 gif=out/f'postludio-proceso-s{SEED}-{tag}.gif'
 with gif.open('xb') as f:frames[0].save(f,format='GIF',save_all=True,append_images=frames[1:],duration=2600,loop=0,optimize=False)
 with Image.open(gif) as im:
  canvas=Image.new('RGB',(1200,210));duration=0
  for i in range(im.n_frames):im.seek(i);duration+=im.info['duration'];canvas.paste(im.convert('RGB').resize((400,210)),(400*i,0))
  assert im.n_frames==3 and duration==7800 and gif.stat().st_size<15_000_000
  with (out/'proceso'/f'04-revision-s{SEED}-{tag}.png').open('xb') as f:canvas.save(f,'PNG')
 errors=[abs(p['error_cents']) for e in details for p in e['final'] if p['error_cents'] is not None]
 dump(out/'verificacion.json',{'aac':metrics,'duracion_decodificada':len(pcm)/SR,'pico_muestra':float(np.max(np.abs(pcm))),'notas':len(details),'ventanas':len(details)*2,'periodicidad_YIN':len(errors),'dentro_50cents':int(np.sum(np.array(errors)<50)),'mediana_abs_cents':float(np.median(errors)),'detalle':details,'banco_intacto':True,'metodo':'YIN abierto 70–1200 Hz, ventanas 200 ms; El piano no recibe corrección; se preservan posibles ambigüedades de periodicidad.','escucha':'Sin escucha humana durante producción.'})
 txt(out/'proceso'/'README.md','# Etapas reales\n\n1. Partitura de retornos y curvas de pulso antes de sintetizar.\n2. Energía de las seis partes físicas ya afinadas y fraseadas.\n3. Energía de las partes y espectrograma del AAC final.\n4. Revisión de cuadros decodificados del GIF.\n\nGIF7.8 s,tres primeras etapas. Semilla1610268.\n')
 txt(out/'README.md',f'# Cada quien guarda otra luz\n\nV. Postludio de Jardín de afinidades. Canek Zapata,16 de octubre de2026. 1:16.\n\nRegresa La–Si–Mi–Re en el piano; respuestas de chelo,viola,clarinete bajo y trombón con sordina cup. Las frases del piano aceleran52→62,56→64,60→66,72→92 y88→104; luego frenan104→88 y52→40. Los intervalos se obtienen integrando el tempo sobre tiempos de negra. La reunión32–39 s usa voces de la familia armónica y una zona compartida de990 Hz; la separación39–65.5 ocupa más tiempo y cada voz se lleva una nota distinta. El piano omite el último Re y el chelo continúa Re–Do–Si, mientras los demás se retiran.\n\nA65.5 s queda un Mi4 de piano solo. Ese stem conserva el render físico original con una escala constante, sin envolvente posterior ni reverberación añadida. Se deja resonar antes del apagador nativo a74 s. La mezcla completa no lleva fade de salida. El archivo final usa ganancia fija sin compresión. Los campos input del medidor corresponden al AAC real; output es una normalización hipotética enviada a null.\n\nMotores originales piano/cuerda/clarinete/metal intactos. Corrección pequeña de afinación en cuerdas y vientos si es estable; deriva por remuestreo de notas físicas. Sin osciladores aditivos ni cantante. Los motores de cuerda mantienen sus semillas internas originales;1610268 identifica la ejecución.\n\nAudio {base}.m4a. WAV/stems sólo locales excluidos de git. Partitura,fuentes,medidas,PNGs reales,og.png1200×630 y GIF7.8 s. No hubo escucha humana durante producción.\n')
 dump(out/'receta.json',{'id':initial['id'],'nonce':initial['nonce'],'semilla':SEED,'contenido_sha256':{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}})
 print(json.dumps({'carpeta':str(out),'notas':len(details),'aac':metrics,'mediana_cents':float(np.median(errors))},ensure_ascii=False),flush=True)
if __name__=='__main__':
 if sys.argv[1]=='iniciar':initialize()
 elif sys.argv[1]=='terminar':finish(Path(sys.argv[2]))
