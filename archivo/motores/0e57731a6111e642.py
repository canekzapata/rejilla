"""Preludio instrumental: iniciar → sondas → revisar → notas → terminar."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter,sosfilt,correlate,stft
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
ROOT=Path(__file__).resolve().parent;BANK=ROOT.parent/'objetos/motor'
SR=48000;DUR=66;BEAT=60/64;SEED=1610261
COL={'piano':'#e9cd95','chelo':'#9bd1b8','clarinete':'#a6bce5'}
plt.rcParams.update({'figure.facecolor':'#172127','axes.facecolor':'#172127','text.color':'#e9e5d5','axes.labelcolor':'#e9e5d5','xtick.color':'#b5c3c5','ytick.color':'#b5c3c5','axes.edgecolor':'#617177','font.family':'DejaVu Sans'})
def dump(p,x):
 with p.open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
def textfile(p,s):
 with p.open('x',encoding='utf8') as f:f.write(s)
def png(p,fig):
 with p.open('xb') as f:fig.savefig(f,format='png',facecolor=fig.get_facecolor())
 plt.close(fig)
def wav(p,x):
 with p.open('xb') as f:wavfile.write(f,SR,np.asarray(x,np.float32))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def title(fig,s):
 fig.suptitle('UNA PUERTA ENTREABIERTA / '+s,x=.065,ha='left',fontsize=16)
 fig.text(.065,.025,'Jardín de afinidades · I. Preludio · Canek Zapata · semilla 1610261',fontsize=10)
 fig.tight_layout(rect=(.04,.065,.98,.91))
def yin(x,sr):
 x=x.astype(float)-np.mean(x);hi=int(sr/70);lo=int(sr/1200);w=len(x)-hi-1
 if w<100 or np.mean(x*x)<1e-11:return None
 ac=correlate(x,x[:w],mode='valid',method='fft')[:hi+1]
 en=np.r_[0,np.cumsum(x*x)];tau=np.arange(hi+1)
 dif=np.maximum(0,en[w]+en[w+tau]-en[tau]-2*ac)
 cm=np.ones_like(dif);cm[1:]=dif[1:]*tau[1:]/np.maximum(np.cumsum(dif[1:]),1e-15)
 ix=np.flatnonzero(cm[lo:]<.2)
 if not len(ix):return None
 j=lo+int(ix[0])
 while j<hi-1 and cm[j+1]<cm[j]:j+=1
 if j>=hi:return None
 den=cm[j-1]-2*cm[j]+cm[j+1];frac=.5*(cm[j-1]-cm[j+1])/den if abs(den)>1e-12 else 0
 return float(sr/(j+frac))
def pitch(x,center):
 a=max(0,round((center-.10)*SR));b=min(len(x),round((center+.10)*SR))
 return yin(x[a:b:3],SR/3)
def initialize():
 I={n:[] for n in COL}
 def add(n,bar,beat,m,length,v=.6,tipo=None,drift=None):
  e={'id':f'{n}-{len(I[n]):03}','t':1+(bar*4+beat)*BEAT,'dur':length*BEAT,'m':m,'v':v,'tipo':tipo or {'piano':'martillo','chelo':'tasto','clarinete':'normal'}[n]}
  if drift:e['deriva_cents']=drift
  I[n].append(e)
 def melody(bar,notes,v=.6):
  for k,(beat,length) in enumerate([(0,.46),(.5,.46),(1,1.43),(2.5,.47)]):
   if k<len(notes):add('piano',bar,beat,notes[k],length,v+[0,-.07,.035,-.08][k])
 rows={0:[57,59,64,62],1:[60,59,57,55],2:[57,59,64,62],3:[60,62,59],
       6:[62,64,60,59],7:[57,59,64],8:[57,59,64,62],9:[61,59,57,56],
       10:[69,71,76,74],11:[72,71,69,67],12:[57,59,64,62],13:[60,59,57],14:[57,59,64]}
 for bar,notes in rows.items():melody(bar,notes,.62 if bar<4 else .55 if bar<8 else .64 if bar<12 else .49)
 # Bajo y voces interiores de piano: articulaciones espaciadas, sin pedal de acorde continuo.
 for bar,notes in [(0,[45,52]),(2,[43,50]),(4,[41,48]),(6,[47,54]),(8,[45,52]),(10,[42,49]),(12,[43,50]),(14,[45])]:
  for k,m in enumerate(notes):add('piano',bar,k*.14,m,2.8,.36)
 for bar,notes in [(4,[52,57,60]),(5,[50,55,59])]:
  for k,m in enumerate(notes):add('piano',bar,k*.75+.25,m,.65,.39)
 # Chelo: respuesta en registro grave, luego una nota que permanece mientras el piano continúa.
 for bar,beat,m,l,v in [(1,2,52,1.6,.47),(2,3,50,1.1,.43),(3,1,48,1.8,.5),
 (4,0,45,.5,.54),(4,.5,47,.5,.48),(4,1,52,1.5,.57),(4,2.5,50,1,.49),
 (5,1,48,1,.46),(5,2,47,1.5,.45),(6,2,45,1.7,.48),(7,1,52,2.8,.54)]:add('chelo',bar,beat,m,l,v)
 add('chelo',8,0,57,7.5,.55,drift=[[0,0],[2.5,0],[6.2,24],[7.5,28]])
 add('chelo',10,1,54,2.5,.5)
 add('chelo',11,0,52,3.5,.48)
 add('chelo',12,0,57,6.7,.53,drift=[[0,0],[1.5,0],[5,20],[6.7,28]])
 add('chelo',13,3,52,1.6,.43)
 for bar,beat,m,l,v in [(14,2.6,50,1.3,.5),(15,0,48,1,.46),(15,1.2,47,4.8,.40)]:add('chelo',bar,beat,m,l,v)
 # El clarinete tiene frases propias y deja huecos para el chelo.
 for bar,beat,m,l,v in [(1,.1,52,1.1,.54),(2,2.7,55,.7,.48),(3,0,52,.85,.53),
 (3,2,50,1.3,.49),(5,.1,52,.8,.55),(5,1.3,53,.65,.48),(5,2.2,52,.75,.5),
 (6,.1,50,1.4,.50),(7,0,47,.7,.47),(7,2,52,1.7,.53)]:add('clarinete',bar,beat,m,l,v)
 add('clarinete',8,1,52,6.3,.49,drift=[[0,0],[1.6,0],[5,-16],[6.3,-20]])
 for bar,beat,m,l,v in [(10,0,59,1.1,.52),(10,2,57,1.4,.5),(11,1,55,1,.47),(11,2.5,52,1,.48)]:add('clarinete',bar,beat,m,l,v)
 add('clarinete',12,.2,57,5.2,.47,drift=[[0,0],[1.2,0],[4,-18],[5.2,-22]])
 add('clarinete',13,2.4,55,1.1,.43)
 add('clarinete',14,0,52,1.8,.40)
 fig,ax=plt.subplots(figsize=(12,6.3),dpi=100)
 for name,events in I.items():
  for e in events:ax.plot([e['t'],e['t']+e['dur']],[e['m']]*2,color=COL[name],lw=3)
  ax.plot([],[],color=COL[name],label=name)
 for x,s in [(1,'A · presentar'),(31,"A′ · abrir"),(53.5,'salida')]:ax.axvline(x,color='#78888b',alpha=.6);ax.text(x+.4,78,s,fontsize=10)
 ax.set(xlabel='segundos',ylabel='altura escrita · MIDI',xlim=(0,DUR),ylim=(38,81));ax.legend(loc='lower right',facecolor='#233238',labelcolor='#e9e5d5')
 title(fig,'01 / frases antes de sonar');fig.canvas.draw();nonce=os.urandom(24).hex()
 digest=hashlib.sha256(bytes(fig.canvas.buffer_rgba())+Path(__file__).read_bytes()+(ROOT/'preludio-render.cjs').read_bytes()+nonce.encode()).hexdigest();tag=digest[:12]
 out=ROOT/f'preludio-puerta-entreabierta-s{SEED}-{tag}';out.mkdir(exist_ok=False)
 for d in ['proceso','render','fuentes']:(out/d).mkdir()
 png(out/'proceso'/f'01-partitura-s{SEED}-{tag}.png',fig)
 dump(out/'partitura.json',{'titulo':'Una puerta entreabierta','movimiento':'I. Preludio','semilla':SEED,'duracion':DUR,'bpm':64,'forma':{'A':[1,31],'A_prima':[31,53.5],'salida':[53.5,66]},'instrumentos':I})
 for p in [Path(__file__),ROOT/'preludio-render.cjs']+list(BANK.glob('*.js')):
  with (out/'fuentes'/p.name).open('xb') as f:f.write(p.read_bytes())
 dump(out/'receta-inicial.json',{'id':digest,'nonce':nonce,'semilla':SEED,'fecha':'2026-10-16','banco_sha256':{p.name:sha(p) for p in BANK.glob('*.js')},'fuentes_sha256':{p.name:sha(p) for p in (out/'fuentes').iterdir()}})
 print(out,flush=True)
def probes(out):
 result=[]
 for p in sorted((out/'render').glob('sonda-*.wav')):
  sr,x=wavfile.read(p);m=float(p.stem.split('-')[-2]);f=440*2**((m-69)/12)
  values=[pitch(x,c) for c in [.6,1.2,2,2.6]];valid=[v for v in values if v]
  result.append({'archivo':p.name,'Hz_objetivo':f,'Hz':values,'mediana_error_cents':float(np.median([1200*np.log2(v/f) for v in valid])) if valid else None})
 dump(out/'sondas-medidas.json',result);print(json.dumps(result,ensure_ascii=False),flush=True)
def finish(out):
 P=json.loads((out/'partitura.json').read_text(encoding='utf8'));initial=json.loads((out/'receta-inicial.json').read_text(encoding='utf8'));tag=initial['id'][:12]
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
   correction=expected/measured if measured and abs(cents)<70 else 1
   if measured and abs(cents)>70:raise ValueError((e['id'],'altura fuera de registro',cents))
   times=np.arange(len(x))/SR
   drift=np.interp(times,*np.array(e.get('deriva_cents',[[0,0],[e['dur'],0]])).T)
   rate=correction*2**(drift/1200);indices=np.r_[0,np.cumsum(rate[:-1])]
   z=np.interp(indices,np.arange(len(x)),x,left=0,right=0).astype(np.float32)
   z*=np.minimum(1,times/.008)*np.minimum(1,np.maximum(0,(len(x)/SR-times)/.025))
   # Fraseo independiente de la presión del modelo.
   envelope=np.interp(times,[0,.12,max(.13,e['dur']*.65),e['dur'],e['dur']+1.1],[.82,1,1.03,.82,0])
   z*=envelope*(e['v']/.6)
   a=round(e['t']*SR);count=min(len(z),N-a);y[a:a+count]+=z[:count]
   centers=[e['dur']*.35,e['dur']*.75];actual=[pitch(z,c) for c in centers]
   target=[expected*2**(np.interp(c,*np.array(e.get('deriva_cents',[[0,0],[e['dur'],0]])).T)/1200) for c in centers]
   errors=[float(1200*np.log2(v/f)) if v else None for v,f in zip(actual,target)]
   details.append({'id':e['id'],'crudo_Hz':values,'correccion_cents':float(1200*np.log2(correction)),'deriva_programada_cents':e.get('deriva_cents'),'final_Hz':actual,'objetivo_Hz':target,'error_final_cents':errors})
  active=np.abs(y)>.0001
  rms=np.sqrt(np.mean(y[active].astype(float)**2));target={'piano':.060,'chelo':.045,'clarinete':.038}[name]
  y*=target/max(rms,1e-10);stems[name]=y;wav(out/'render'/(name+'-mezcla.wav'),y)
 fig,ax=plt.subplots(figsize=(12,6.3),dpi=100)
 for name,y in stems.items():
  seg=y[round(34*SR):round(35*SR)].astype(float);z=np.abs(np.fft.rfft(seg*np.hanning(len(seg))));freq=np.fft.rfftfreq(len(seg),1/SR)
  ax.plot(freq,20*np.log10(z/max(z.max(),1e-12)+1e-8),label=name,color=COL[name],lw=1)
 ax.set(xlim=(80,2400),ylim=(-85,3),xlabel='Hz · ventana 34–35 s',ylabel='dB relativos por instrumento');ax.legend(facecolor='#233238',labelcolor='#e9e5d5')
 title(fig,'02 / cuerpos del banco, afinados y separados');png(out/'proceso'/f'02-instrumentos-s{SEED}-{tag}.png',fig)
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
 base=f'preludio-puerta-entreabierta-s{SEED}-{tag}';wav(out/(base+'.wav'),mix)
 ff='C:/msys64/mingw64/bin/ffmpeg.exe'
 cmd=[ff,'-hide_banner','-nostdin','-n','-i',str(out/(base+'.wav')),'-af','loudnorm=I=-18:TP=-2:LRA=12','-c:a','aac','-b:a','256k',str(out/(base+'.m4a'))]
 r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode==0,r.stderr
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
 title(fig,'03 / preludio completo, A–A′–salida');final=out/f'preludio-resultado-s{SEED}-{tag}.png';png(final,fig)
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
 textfile(out/'proceso'/'README.md','# Etapas reales\n\n1. Frases y orquestación escritas antes de renderizar.\n2. Espectros de los tres instrumentos físicos ya renderizados, afinados y con deriva; ventana 34–35 s normalizada por instrumento.\n3. Curvas de energía de los stems y espectrograma del AAC final.\n4. Revisión de los cuadros decodificados del GIF.\n\nGIF: tres primeras etapas, 7.8 s, loop. Semilla 1610261. No son cuadros internos del sintetizador.\n')
 textfile(out/'README.md',f'# Una puerta entreabierta\n\nI. Preludio de Jardín de afinidades. Canek Zapata, 16 de octubre de 2026. 66 segundos, 64 BPM, 16 compases y colas.\n\nPiano normal presenta La–Si–Mi–Re; chelo y clarinete bajo responden. A: 1–31 s; A′: 31–53.5 s; salida: 53.5–66 s. La repetición conserva el tema y abre la afinación de notas largas. El piano omite el Re final; el chelo continúa Re–Do–Si y permanece después de los demás.\n\nTres modelos originales del banco: piano.js, cuerda.js y clarinete.js. Sin osciladores aditivos ni cantante. Chelo tasto; clarinete normal. Afinación medida por nota y corrección pequeña por remuestreo; deriva posterior variable de dos notas de chelo (hasta +28 cents) y dos de clarinete (hasta −20/−22 cents). Es procesamiento del audio del modelo, no una técnica nativa de glissando del arco. El piano permanece temperado. El ritmo del tema se fija en corchea, corchea, negra con puntillo, corchea y silencio de negra: cuatro tiempos.\n\nAudio: {base}.m4a. WAV flotante y stems sólo locales, excluidos de git. Medidas, partitura y fuentes conservadas. GIF y PNGs de etapas efectivas, og.png 1200×630. Sin escucha humana durante producción ni publicación remota.\n')
 dump(out/'receta.json',{'id':initial['id'],'nonce':initial['nonce'],'semilla':SEED,'archivos_sha256':{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},'nota':'El motor de cuerda usa sus semillas internas originales; semilla del proyecto identifica la ejecución, no altera ese motor.'})
 print(json.dumps({'carpeta':str(out),'medidas':metrics,'notas':len(details),'mediana_error_cents':float(np.median(voiced)),'alturas_estables':len(voiced)},ensure_ascii=False),flush=True)
if __name__=='__main__':
 if sys.argv[1]=='iniciar':initialize()
 elif sys.argv[1]=='sondas':probes(Path(sys.argv[2]))
 elif sys.argv[1]=='terminar':finish(Path(sys.argv[2]))
