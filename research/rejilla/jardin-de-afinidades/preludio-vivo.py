"""Revisión del Preludio: tempo, articulación y dirección dinámica escritos por nota."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter,sosfilt,stft
import matplotlib.pyplot as plt
from PIL import Image
import preludio as util
ROOT=Path(__file__).resolve().parent;BANK=ROOT.parent/'objetos/motor'
SR=48000;SEED=1610264
OLD=ROOT/'preludio-puerta-entreabierta-s1610261-205824c3b5dc'
COL=util.COL;dump=util.dump;png=util.png;wav=util.wav;sha=util.sha;txt=util.textfile;pitch=util.pitch
BPM=np.array([[0,52],[8,52],[16,72],[28,100],[31.999,42],[32,88],[40,106],[44,106],[48,54],[56,42],[56.001,60],[65,36]],float)
DYN=np.array([[0,.48],[8,.62],[16,.86],[24,1.22],[28,1.48],[31.9,.80],[32,1.30],[40,1.65],[44,1.75],[48,.52],[54,.42],[56,.72],[60,.44],[65,.17]],float)
grid=np.linspace(0,70,70001);tempo=np.interp(grid,*BPM.T)
seconds=np.r_[0,np.cumsum((60/tempo[:-1]+60/tempo[1:])*.0005)]
def clock(beat):return float(1.2+np.interp(beat,grid,seconds)+(1.35 if beat>=32 else 0)+(.9 if beat>=48 else 0))
def title(fig,s):
 fig.suptitle('UNA PUERTA ENTREABIERTA / TIEMPO VIVO / '+s,x=.06,ha='left',fontsize=14)
 fig.text(.06,.025,'Jardín de afinidades · revisión del I. Preludio · Canek Zapata · semilla 1610264',fontsize=10)
 fig.tight_layout(rect=(.035,.06,.985,.91))
def initialize():
 original=json.loads((OLD/'partitura.json').read_text(encoding='utf8'));I={n:[] for n in COL}
 for name,events in original['instrumentos'].items():
  for old in events:
   e=dict(old);b=(e['t']-1)/(60/64);length=e['dur']/(60/64)
   factor=.78 if 32<=b<44 and length<2 else .86 if 16<=b<28 and length<2 else 1.
   e['t']=clock(b);e['dur']=clock(b+length*factor)-clock(b)
   dynamic=float(np.interp(b,*DYN.T));voiceboost=1.12 if name=='chelo' and 16<=b<24 else 1.07 if name=='clarinete' and 20<=b<28 else 1.
   e['v']=float(np.clip(old['v']*dynamic**.3,.22,.88))
   e['expresion']=dynamic*voiceboost
   e['beat_origen']=b;e['dur_beats_realizada']=length*factor
   if old.get('deriva_cents'):
    knots=[]
    for local,cents in old['deriva_cents']:
     frac=min(1,local/old['dur']);time=clock(b+frac*length*factor)-clock(b)
     if knots and abs(time-knots[-1][0])<1e-7:knots[-1]=[time,cents]
     else:knots.append([time,cents])
    e['deriva_cents']=knots
   I[name].append(e)
 end=max(e['t']+e['dur'] for events in I.values() for e in events)
 duration=int(np.ceil(end+3))
 P={'titulo':'Una puerta entreabierta — tiempo vivo','movimiento':'I. Preludio, revisión','semilla':SEED,'duracion':duration,'instrumentos':I,'tempo_por_beat':BPM.tolist(),'dinamica_por_beat':DYN.tolist(),'fermata_s':{'32':1.35,'48':.9},'origen':OLD.name,'forma':{'A':[clock(0),clock(32)],'A_prima':[clock(32),clock(56)],'salida':[clock(56),duration]},'nota':'Mismas 106 alturas y orden; nuevos tiempos, duraciones, presiones de los modelos y expresión. No es estiramiento del máster anterior.'}
 fig,axes=plt.subplots(2,1,figsize=(12,6.3),dpi=100)
 axes[0].plot(BPM[:,0],BPM[:,1],color='#e9cd95');axes[0].set(ylabel='pulso · BPM',xlim=(0,65),ylim=(25,115));axes[0].axhline(64,color='#82979d',ls='--',label='versión anterior: 64');axes[0].legend(facecolor='#233238',labelcolor='#e9e5d5')
 axes[1].plot(DYN[:,0],DYN[:,1],color='#9bd1b8');axes[1].set(ylabel='expresión escrita',xlabel='tiempos de negra · fermatas en 32 y 48',xlim=(0,65))
 title(fig,'01 / aceleración, frenada, regreso');fig.canvas.draw();nonce=os.urandom(24).hex()
 digest=hashlib.sha256(bytes(fig.canvas.buffer_rgba())+Path(__file__).read_bytes()+(ROOT/'preludio.py').read_bytes()+(ROOT/'preludio-render.cjs').read_bytes()+nonce.encode()).hexdigest();tag=digest[:12]
 out=ROOT/f'preludio-tiempo-vivo-s{SEED}-{tag}';out.mkdir(exist_ok=False)
 for d in ['render','proceso','fuentes']:(out/d).mkdir()
 png(out/'proceso'/f'01-direccion-s{SEED}-{tag}.png',fig);dump(out/'partitura.json',P)
 for p in [Path(__file__),ROOT/'preludio.py',ROOT/'preludio-render.cjs']+list(BANK.glob('*.js')):
  with (out/'fuentes'/p.name).open('xb') as f:f.write(p.read_bytes())
 dump(out/'receta-inicial.json',{'id':digest,'nonce':nonce,'semilla':SEED,'fecha':'2026-10-16','banco_sha256':{p.name:sha(p) for p in BANK.glob('*.js')},'fuentes_sha256':{p.name:sha(p) for p in (out/'fuentes').iterdir()},'partitura_anterior_sha256':sha(OLD/'partitura.json')})
 print(out,flush=True)

def finish(out):
 P=json.loads((out/'partitura.json').read_text(encoding='utf8'));initial=json.loads((out/'receta-inicial.json').read_text(encoding='utf8'));tag=initial['id'][:12];DUR=P['duracion']
 assert all(sha(BANK/n)==s for n,s in initial['banco_sha256'].items())
 N=round(DUR*SR);stems={};details=[]
 for name,events in P['instrumentos'].items():
  y=np.zeros(N,dtype=np.float32)
  for e in events:
   sr,x=wavfile.read(out/'render'/(e['id']+'.wav'));assert sr==SR and np.isfinite(x).all()
   expected=440*2**((e['m']-69)/12)
   values=[pitch(x,e['dur']*q) for q in [.35,.55,.75]]
   valid=[v for v in values if v];measured=float(np.median(valid)) if valid else None
   cents=1200*np.log2(measured/expected) if measured else None
   # Afinación por nota: sólo correcciones pequeñas; nunca ocultar saltos de octava.
   correction=expected/measured if name!='piano' and measured and abs(cents)<70 else 1
   if name!='piano' and measured and abs(cents)>70:raise ValueError((e['id'],'altura fuera de registro',cents))
   times=np.arange(len(x))/SR
   drift=np.interp(times,*np.array(e.get('deriva_cents',[[0,0],[e['dur'],0]])).T)
   rate=correction*2**(drift/1200);indices=np.r_[0,np.cumsum(rate[:-1])]
   z=np.interp(indices,np.arange(len(x)),x,left=0,right=0).astype(np.float32)
   z*=np.minimum(1,times/.008)*np.minimum(1,np.maximum(0,(len(x)/SR-times)/.025))
   # Igualar la respuesta de registro antes de dibujar la dinámica escrita.
   calibration=1.0
   if name!='piano':
    core=z[round(min(.15,e['dur']*.2)*SR):round(e['dur']*.8*SR)]
    calibration=.04/max(float(np.sqrt(np.mean(core.astype(float)**2))),1e-9)
    z*=calibration
   # Fraseo independiente de la presión del modelo: respiración y retirada en sostenidos.
   if name!='piano' and e['dur']>2:
    envelope=np.interp(times,[0,.15,e['dur']*.3,e['dur']*.7,e['dur'],e['dur']+1.1],[.12,.75,1,.65,.12,0])
   else:envelope=np.interp(times,[0,.12,max(.13,e['dur']*.65),e['dur'],e['dur']+1.1],[.82,1,1.03,.82,0])
   z*=envelope*(e['v']/.6)*e['expresion']
   a=round(e['t']*SR);count=min(len(z),N-a);y[a:a+count]+=z[:count]
   centers=[e['dur']*.35,e['dur']*.75];actual=[pitch(z,c) for c in centers]
   target=[expected*2**(np.interp(c,*np.array(e.get('deriva_cents',[[0,0],[e['dur'],0]])).T)/1200) for c in centers]
   errors=[float(1200*np.log2(v/f)) if v else None for v,f in zip(actual,target)]
   details.append({'id':e['id'],'crudo_Hz':values,'correccion_cents':float(1200*np.log2(correction)),'calibracion_registro':calibration,'deriva_programada_cents':e.get('deriva_cents'),'final_Hz':actual,'objetivo_Hz':target,'error_final_cents':errors,'nota_medidor':'Piano sin corrección. YIN puede elegir armónicos o la resonancia de caja.' if name=='piano' else None})
  active=np.abs(y)>.0001
  rms=np.sqrt(np.mean(y[active].astype(float)**2));target={'piano':.060,'chelo':.045,'clarinete':.038}[name]
  y*=target/max(rms,1e-10);stems[name]=y;wav(out/'render'/(name+'-mezcla.wav'),y)
 fig,ax=plt.subplots(figsize=(12,6.3),dpi=100)
 for name,events in P['instrumentos'].items():
  for e in events:ax.plot([e['t'],e['t']+e['dur']],[e['m']]*2,color=COL[name],lw=3)
  ax.plot([],[],color=COL[name],label=name)
 ax.set(xlim=(0,DUR),xlabel='segundos reales con cambios de pulso',ylabel='altura escrita · MIDI');ax.legend(facecolor='#233238',labelcolor='#e9e5d5')
 title(fig,'02 / fraseo renderizado');png(out/'proceso'/f'02-fraseo-s{SEED}-{tag}.png',fig)
 pan={'piano':-.18,'chelo':-.38,'clarinete':.35};dry=np.zeros((N,2))
 for name,y in stems.items():
  angle=(pan[name]+1)*np.pi/4;dry+=np.column_stack((y*np.cos(angle),y*np.sin(angle)))
 wet=np.zeros_like(dry)
 for k,delay in enumerate([.043,.077,.113,.173,.257,.367,.523,.719,1.013,1.387,1.823]):
  shift=round(delay*SR);source=dry[:,::-1] if k%2 else dry
  source=sosfilt(butter(1,5800-300*k,fs=SR,output='sos'),source,axis=0)
  wet[shift:]+=.11*np.exp(-delay/1.0)*source[:-shift]
 mix=dry+wet;mix*=np.minimum(1,np.maximum(0,(DUR-np.arange(N)/SR)/.7))[:,None]
 mix*=.78/max(np.max(np.abs(mix)),1e-12)
 base=f'preludio-tiempo-vivo-s{SEED}-{tag}';wav(out/(base+'.wav'),mix)
 ff='C:/msys64/mingw64/bin/ffmpeg.exe'
 # Ganancia fija: conserva las diferencias internas de dinámica.
 meter=subprocess.run([ff,'-hide_banner','-nostdin','-i',str(out/(base+'.wav')),'-af','loudnorm=I=-18:TP=-2:LRA=20:print_format=json','-f','null','-'],capture_output=True,text=True)
 before=json.JSONDecoder().raw_decode(meter.stderr[meter.stderr.rfind('{'):])[0]
 gain=min(-18-float(before['input_i']),-2-float(before['input_tp']))
 r=subprocess.run([ff,'-hide_banner','-nostdin','-n','-i',str(out/(base+'.wav')),'-af',f'volume={gain:.4f}dB','-c:a','aac','-b:a','256k',str(out/(base+'.m4a'))],capture_output=True,text=True);assert r.returncode==0,r.stderr
 dump(out/'master-ganancia.json',{'tipo':'ganancia fija sin compresión ni normalización dinámica','ganancia_dB':gain,'premaster':before})
 r=subprocess.run([ff,'-hide_banner','-nostdin','-i',str(out/(base+'.m4a')),'-af','loudnorm=I=-18:TP=-2:LRA=12:print_format=json','-f','null','-'],capture_output=True,text=True)
 metrics=json.JSONDecoder().raw_decode(r.stderr[r.stderr.rfind('{'):])[0]
 decoded=subprocess.run([ff,'-v','error','-i',str(out/(base+'.m4a')),'-f','f32le','-ar',str(SR),'-ac','2','-'],capture_output=True,check=True)
 pcm=np.frombuffer(decoded.stdout,np.float32).reshape(-1,2);assert np.isfinite(pcm).all() and np.max(np.abs(pcm))<1 and abs(len(pcm)/SR-DUR)<.1
 fig,axes=plt.subplots(2,1,figsize=(12,6.3),dpi=100)
 for name,y in stems.items():
  window=round(.1*SR);energy=np.sqrt(np.mean(y[:len(y)//window*window].reshape(-1,window).astype(float)**2,axis=1))
  axes[0].plot(np.arange(len(energy))*.1,energy,label=name,color=COL[name],lw=1)
 axes[0].set(xlim=(0,DUR),ylabel='RMS por instrumento');axes[0].legend(facecolor='#233238',labelcolor='#e9e5d5',fontsize=8)
 f,tt,z=stft(pcm.mean(axis=1),SR,nperseg=8192,noverlap=6144);mask=(f>=70)&(f<2400)
 axes[1].pcolormesh(tt,f[mask],20*np.log10(np.abs(z[mask])+1e-8),cmap='magma',vmin=-85,vmax=-30,shading='auto');axes[1].set(xlim=(0,DUR),xlabel='segundos',ylabel='Hz · AAC final')
 title(fig,'03 / impulso y retirada, AAC final');final=out/f'preludio-resultado-s{SEED}-{tag}.png';png(final,fig)
 with Image.open(final) as im:
  for p in [out/'og.png',out/'proceso'/f'03-mezcla-s{SEED}-{tag}.png']:
   with p.open('xb') as stream:im.save(stream,'PNG')
 frames=[]
 for p in sorted((out/'proceso').glob('*.png')):
  with Image.open(p) as im:frames.append(im.convert('RGB').resize((900,472)).quantize(colors=128))
 gif=out/f'preludio-proceso-s{SEED}-{tag}.gif'
 with gif.open('xb') as stream:frames[0].save(stream,format='GIF',save_all=True,append_images=frames[1:],duration=2600,loop=0,optimize=False)
 with Image.open(gif) as im:
  assert im.n_frames==3
  contact=Image.new('RGB',(600,945));duration=0
  for k in range(3):im.seek(k);duration+=im.info['duration'];contact.paste(im.convert('RGB').resize((600,315)),(0,k*315))
  assert duration==7800 and gif.stat().st_size<15_000_000
  with (out/'proceso'/f'04-revision-s{SEED}-{tag}.png').open('xb') as stream:contact.save(stream,'PNG')
 voiced=[abs(v) for d in details for v in d['error_final_cents'] if v is not None]
 dump(out/'verificacion.json',{'aac':metrics,'duracion_decodificada':len(pcm)/SR,'pico_muestra':float(np.max(np.abs(pcm))),'notas':len(details),'alturas_estables':len(voiced),'ventanas_total':2*len(details),'mediana_abs_error_cents':float(np.median(voiced)),'ventanas_dentro_50cents':int(np.sum(np.array(voiced)<50)),'metodo':'YIN 70–1200 Hz, ventanas 200 ms al 35/75% de cada nota original y procesada. No restringido a altura objetivo. Las alturas inestables se declaran nulas.','detalle':details,'banco_intacto':True,'escucha':'No se hizo escucha humana en producción.'})
 txt(out/'proceso'/'README.md','# Etapas reales\n\n1. Dirección escrita antes de renderizar: tempo y expresión frente al pulso anterior.\n2. Partitura temporal realizada por los modelos del banco.\n3. Energía por instrumento y espectrograma del AAC final.\n4. Revisión de cuadros decodificados del GIF.\n\nGIF de tres primeras etapas, 7.8 s. Semilla 1610264.\n')
 txt(out/'README.md',f'# Una puerta entreabierta — tiempo vivo\n\nRevisión del I. Preludio, Jardín de afinidades. Canek Zapata, 16 de octubre de 2026. {DUR} segundos.\n\nConserva las 106 notas y sus instrumentos: piano, chelo tasto, clarinete bajo normal. Reescribe sus ataques, duraciones, presión y expresión. Pulso de 52 a 100 BPM en la primera exposición; frenada a 42 y fermata de 1.35 s. Regreso a 88 y aceleración a 106; caída a 54 y fermata de .9 s antes de abrir la separación. Salida que vuelve a tomar impulso y frena hasta 36. Los tiempos exactos, dinámicas y articulaciones están en partitura.json. No se estiró el máster anterior: se renderizaron de nuevo todas las notas con sus nuevas duraciones y presiones.\n\nAfinación medida y corregida sólo en chelo/clarinete; deriva escrita por remuestreo de sus notas físicas. Se mantiene el piano sin corrección de altura. Calibración de registro antes de la expresión para no borrar el fraseo. Ganancia final fija sin compresión dinámica: master-ganancia.json.\n\nVersión previa conservada: ../preludio-puerta-entreabierta-s1610261-205824c3b5dc/. Los otros movimientos aún no reciben esta revisión.\n\nAudio {base}.m4a; WAV/stems sólo locales excluidos de git. PNGs reales, GIF 7.8 s, og.png 1200×630, fuentes, receta y mediciones. Sin escucha humana durante producción.\n')
 with (out/'fuentes'/'preludio-vivo-realizado.py').open('xb') as f:f.write(Path(__file__).read_bytes())
 dump(out/'receta.json',{'id':initial['id'],'nonce':initial['nonce'],'semilla':SEED,'archivos_sha256':{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},'nota':'El motor de cuerda usa sus semillas internas originales; semilla del proyecto identifica la ejecución, no altera ese motor. Se conserva fuente inicial y revisión del tratamiento del medidor; el piano no se corrige.'})
 print(json.dumps({'carpeta':str(out),'medidas':metrics,'notas':len(details),'mediana_error_cents':float(np.median(voiced)),'alturas_estables':len(voiced)},ensure_ascii=False),flush=True)
if __name__=='__main__':
 if sys.argv[1]=='iniciar':initialize()
 elif sys.argv[1]=='terminar':finish(Path(sys.argv[2]))
