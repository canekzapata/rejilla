"""II. Invención. Frases deformadas analíticamente y encuentros 3:2 / 5:3."""
import json,os,sys,hashlib,subprocess
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter,sosfilt,stft,find_peaks
import matplotlib.pyplot as plt
from PIL import Image
import preludio as util
ROOT=Path(__file__).resolve().parent;BANK=ROOT.parent/'objetos/motor'
SR=48000;DUR=84;SEED=1610262
COL={'clarinete':'#97bfdf','viola':'#d3acdc','bajo':'#9fc8a5','piano':'#e7c58b'}
dump=util.dump;png=util.png;wav=util.wav;sha=util.sha;txt=util.textfile;pitch=util.pitch
def title(fig,s):
 fig.suptitle('APRENDER A IRSE / '+s,x=.06,ha='left',fontsize=17)
 fig.text(.06,.025,'Jardín de afinidades · II. Invención · Canek Zapata · semilla 1610262',fontsize=10)
 fig.tight_layout(rect=(.035,.06,.985,.91))
def hz(m):return 440*2**((m-69)/12)
def initialize():
 I={n:[] for n in COL};rules=[];meetings=[]
 def add(name,t,m,dur,v=.55,f=None,drift=None):
  e={'id':f'{name}-{len(I[name]):03}','t':float(t),'m':float(m),'dur':float(dur),'v':v,'tipo':{'viola':'arco','clarinete':'normal','bajo':'pizz','piano':'martillo'}[name]}
  if f:e['Hz_objetivo']=float(f)
  if drift:e['deriva_cents']=drift
  I[name].append(e);return e['id']
 starts=[1,10,20,31,42,54,65];trans=[0,0,-2,-2,5,-2,0]
 for j,(start,shift) in enumerate(zip(starts,trans)):
  eps=[0,.35,.6,.65,.5,.3,0][j]
  lag=[1.9,1.2,.5,.1,1.1,1.6,1.1][j]
  rules.append({'frase':j,'t':start,'epsilon':eps,'retardo_viola_s':lag,'formula':'T(u)=5.2*(u ± epsilon*sin(2*pi*u)/(2*pi)); u=[0,.125,.25,.625]. Derivada positiva; extremos preservados.'})
  for name,sign,motif in [('clarinete',1,[57,59,64,62]),('viola',-1,[64,62,57,59])]:
   delay=0 if name=='clarinete' else lag
   for k,u in enumerate([0,.125,.25,.625]):
    onset=start+delay+5.2*(u+sign*eps*np.sin(2*np.pi*u)/(2*np.pi))
    # Ritmo temático reconocible; las entradas interiores se flexionan sin cambiar el orden.
    length=[.46,.50,1.32,.65][k]
    add(name,onset,motif[k]+shift,length,[.56,.49,.62,.48][k]*(.9 if j==5 else 1))
  if j not in [1,3,6]:
   add('clarinete',start+5.25,60+shift,.55,.45)
   add('viola',start+6.05,62+shift,.8,.46)
  # Bajo y piano articulan huecos; no forman un ostinato continuo.
  root=[47,50,45,48,41,43,45][j]
  add('bajo',start-.15,root,.6,.52);add('bajo',start+5.1,root+7,.45,.42)
  add('piano',start+2.9,root+19,.35,.43);add('piano',start+4.35,root+14,.3,.36)
 # Tres pequeñas cadencias espectrales. Impares reales del clarinete: tercero y quinto.
 for j,fc,fv,pc,pv in [(1,220,330,3,2),(3,198,330,5,3),(6,220,330,3,2)]:
  start=starts[j]+6.2
  # C1 continua, con meseta de afinidad de .5 s, seguida de separación contraria.
  cl=add('clarinete',start,69+12*np.log2(fc/440),3.1,.54,f=fc,drift=[[0,14],[1.1,0],[1.6,0],[3.1,-30]])
  vl=add('viola',start,69+12*np.log2(fv/440),3.9,.56,f=fv,drift=[[0,-18],[1.1,0],[1.6,0],[3.1,34],[3.9,42]])
  meetings.append({'t':start,'clarinete':cl,'viola':vl,'parciales':[pc,pv],'Hz_compartido':fc*pc,'meseta_s':[start+1.1,start+1.6]})
 # La última viola sigue el contorno invertido del tema cuando el clarinete ya se retiró.
 for t,m,d,v in [(75.7,62,.75,.48),(76.7,57,.55,.42),(77.6,59,2.4,.42)]:add('viola',t,m,d,v)
 P={'titulo':'Aprender a irse','movimiento':'II. Invención','duracion':DUR,'semilla':SEED,'instrumentos':I,'reglas_tiempo':rules,'encuentros':meetings,'forma':{'entradas':[0,20],'dialogo':[20,42],'episodio':[42,65],'reunion_salida':[65,84]}}
 fig,ax=plt.subplots(figsize=(12,6.3),dpi=100)
 for name,events in I.items():
  for e in events:ax.plot([e['t'],e['t']+e['dur']],[e['m']]*2,lw=3,color=COL[name])
  ax.plot([],[],color=COL[name],label=name)
 for m in meetings:ax.axvspan(*m['meseta_s'],color='#d8dec0',alpha=.25)
 ax.set(xlabel='segundos · franjas claras: encuentros escritos',ylabel='altura escrita · MIDI',xlim=(0,DUR),ylim=(38,72));ax.legend(facecolor='#233238',labelcolor='#e9e5d5',loc='upper right')
 title(fig,'01 / dos líneas, tres encuentros');fig.canvas.draw();nonce=os.urandom(24).hex()
 digest=hashlib.sha256(bytes(fig.canvas.buffer_rgba())+Path(__file__).read_bytes()+(ROOT/'invencion-render.cjs').read_bytes()+(ROOT/'preludio.py').read_bytes()+nonce.encode()).hexdigest();tag=digest[:12]
 out=ROOT/f'invencion-aprender-a-irse-s{SEED}-{tag}';out.mkdir(exist_ok=False)
 for d in ['proceso','render','fuentes']:(out/d).mkdir()
 png(out/'proceso'/f'01-partitura-s{SEED}-{tag}.png',fig);dump(out/'partitura.json',P)
 for p in [Path(__file__),ROOT/'invencion-render.cjs',ROOT/'preludio.py']+list(BANK.glob('*.js')):
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
   correction=f/measured if name!='piano' and measured and abs(cents)<70 else 1
   if name in ['viola','clarinete'] and measured and abs(cents)>70:raise ValueError((e['id'],'altura fuera de registro',cents))
   times=np.arange(len(x))/SR;knots=e.get('deriva_cents',[[0,0],[e['dur'],0]])
   # Interpolación cúbica suave por tramo: velocidad nula en los nudos del encuentro.
   kt,kc=np.array(knots).T;ix=np.clip(np.searchsorted(kt,times,side='right')-1,0,len(kt)-2)
   u=np.clip((times-kt[ix])/(kt[ix+1]-kt[ix]),0,1);drift=kc[ix]+(kc[ix+1]-kc[ix])*(3*u*u-2*u*u*u)
   rate=correction*2**(drift/1200);indices=np.r_[0,np.cumsum(rate[:-1])]
   z=np.interp(indices,np.arange(len(x)),x,left=0,right=0).astype(np.float32)
   z*=np.minimum(1,times/.008)*np.minimum(1,np.maximum(0,(len(x)/SR-times)/.035))
   gain=1.
   if name!='piano':
    core=z[round(min(.12,e['dur']*.2)*SR):round(e['dur']*.8*SR)]
    gain=.04/max(float(np.sqrt(np.mean(core.astype(float)**2))),1e-9);z*=gain
   env=np.interp(times,[0,.08,e['dur']*.4,e['dur']*.8,e['dur'],e['dur']+1.3],[.25,.85,1,.65,.12,0]) if e['dur']>1 else np.interp(times,[0,.04,e['dur'],e['dur']+1.3],[.5,1,.65,0])
   z*=env*(e['v']/.6);a=round(e['t']*SR);count=min(len(z),N-a);y[a:a+count]+=z[:count]
   if e.get('deriva_cents'):isolated[e['id']]=z
   final=[]
   for q in [.35,.75]:
    c=e['dur']*q;det=pitch(z,c);d=float(np.interp(c,times,drift));target=f*2**(d/1200)
    final.append({'t_local':c,'Hz':det,'objetivo_Hz':target,'error_cents':1200*np.log2(det/target) if det else None})
   details.append({'id':e['id'],'crudo_Hz':values,'correccion_cents':1200*np.log2(correction),'calibracion_registro':gain,'final':final})
  active=np.abs(y)>1e-4;rms=np.sqrt(np.mean(y[active].astype(float)**2));y*= {'clarinete':.048,'viola':.049,'bajo':.025,'piano':.026}[name]/max(rms,1e-9)
  stems[name]=y;wav(out/'render'/(name+'-mezcla.wav'),y)
 # Verificación independiente de los parciales presentes durante la meseta escrita.
 contacts=[]
 for m in P['encuentros']:
  measured=[]
  for name in ['clarinete','viola']:
   z=isolated[m[name]];seg=z[round(1.12*SR):round(1.58*SR)].astype(float)
   spec=np.abs(np.fft.rfft(seg*np.hanning(len(seg)),2**19));freq=np.fft.rfftfreq(2**19,1/SR)
   inds,_=find_peaks(spec);candidates=[k for k in inds if abs(freq[k]-m['Hz_compartido'])<12]
   k=max(candidates,key=lambda k:spec[k]) if candidates else None
   measured.append({'instrumento':name,'Hz_pico':float(freq[k]) if k is not None else None,'dB_relativo_max_espectro':float(20*np.log10(spec[k]/spec.max()+1e-15)) if k is not None else None})
  contacts.append({'t':m['t'],'objetivo_Hz':m['Hz_compartido'],'medidos':measured,'diferencia_Hz':abs(measured[0]['Hz_pico']-measured[1]['Hz_pico']) if all(x['Hz_pico'] for x in measured) else None})
 dump(out/'encuentros-medidos.json',contacts)
 fig,ax=plt.subplots(figsize=(12,6.3),dpi=100)
 for contact in contacts:
  for i,e in enumerate(contact['medidos']):ax.scatter(contact['t']+i*.25,e['Hz_pico']-contact['objetivo_Hz'],color=list(COL.values())[i],s=60)
 ax.axhline(0,color='#e7c58b',alpha=.5);ax.set(xlabel='inicio del encuentro · segundos',ylabel='desvío del parcial medido · Hz');title(fig,'02 / parciales reales durante el contacto');png(out/'proceso'/f'02-encuentros-s{SEED}-{tag}.png',fig)
 dry=np.zeros((N,2));pans={'clarinete':-.32,'viola':.32,'piano':-.12,'bajo':.06}
 for name,y in stems.items():
  angle=(pans[name]+1)*np.pi/4;dry+=np.column_stack((y*np.cos(angle),y*np.sin(angle)))
 wet=np.zeros_like(dry)
 for k,delay in enumerate([.043,.077,.113,.173,.257,.367,.523,.719,1.013,1.387,1.823]):
  shift=round(delay*SR);source=sosfilt(butter(1,5800-300*k,fs=SR,output='sos'),dry[:,::-1] if k%2 else dry,axis=0)
  wet[shift:]+=.11*np.exp(-delay)*source[:-shift]
 mix=dry+wet;mix*=np.minimum(1,np.maximum(0,(DUR-np.arange(N)/SR)/.8))[:,None];mix*=.76/np.max(np.abs(mix))
 base=f'invencion-aprender-a-irse-s{SEED}-{tag}';wav(out/(base+'.wav'),mix)
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
 title(fig,'03 / invención completa');final=out/f'invencion-resultado-s{SEED}-{tag}.png';png(final,fig)
 with Image.open(final) as im:
  for p in [out/'og.png',out/'proceso'/f'03-mezcla-s{SEED}-{tag}.png']:
   with p.open('xb') as f:im.save(f,'PNG')
 frames=[]
 for p in sorted((out/'proceso').glob('*.png')):
  with Image.open(p) as im:frames.append(im.convert('RGB').resize((900,472)).quantize(colors=128))
 gif=out/f'invencion-proceso-s{SEED}-{tag}.gif'
 with gif.open('xb') as f:frames[0].save(f,format='GIF',save_all=True,append_images=frames[1:],duration=2600,loop=0,optimize=False)
 with Image.open(gif) as im:
  canvas=Image.new('RGB',(1200,210));duration=0
  for i in range(im.n_frames):im.seek(i);duration+=im.info['duration'];canvas.paste(im.convert('RGB').resize((400,210)),(400*i,0))
  assert im.n_frames==3 and duration==7800 and gif.stat().st_size<15_000_000
  with (out/'proceso'/f'04-revision-s{SEED}-{tag}.png').open('xb') as f:canvas.save(f,'PNG')
 errors=[abs(p['error_cents']) for e in details for p in e['final'] if p['error_cents'] is not None]
 dump(out/'verificacion.json',{'aac':metrics,'duracion_decodificada':len(pcm)/SR,'pico_muestra':float(np.max(np.abs(pcm))),'notas':len(details),'ventanas':len(details)*2,'periodicidad_YIN':len(errors),'dentro_50cents':int(np.sum(np.array(errors)<50)),'mediana_abs_cents':float(np.median(errors)),'detalle':details,'banco_intacto':True,'metodo':'YIN abierto 70–1200 Hz, ventanas 200 ms; FFT de contactos 460 ms, máximo local a ±12 Hz del parcial previsto. Esa búsqueda verifica energía cerca del objetivo, no determina altura global.','escucha':'Sin escucha humana durante producción.'})
 txt(out/'proceso'/'README.md','# Etapas reales\n\n1. Partitura de eventos y franjas de encuentros antes de síntesis.\n2. Parciales medidos en las notas físicas procesadas, mesetas de los tres encuentros.\n3. Energía de stems y espectrograma del AAC final.\n4. Revisión de cuadros decodificados del GIF.\n\nGIF 7.8 s, tres etapas efectivamente capturadas. Semilla 1610262; los motores conservan sus semillas internas.\n')
 txt(out/'README.md',f'# Aprender a irse\n\nII. Invención de Jardín de afinidades. Canek Zapata, 16 de octubre de 2026. 1:24.\n\nClarinete bajo y viola desarrollan La–Si–Mi–Re y su inversión Mi–Re–La–Si; contrabajo pizz y piano con goma puntúan huecos. Siete frases: entradas, diálogo, episodio y reunión abreviada. Las entradas interiores se deforman con T(u)=5.2×[u ± ε sin(2πu)/(2π)], con ε entre 0 y .65: la derivada siempre positiva conserva el orden y los extremos, aunque las voces se adelantan y retrasan dentro de la frase. No es un canon con tempos fijos distintos.\n\nTres cadencias espectrales: clarinete 220×3 / viola 330×2 = 660 Hz; clarinete 198×5 / viola 330×3 = 990 Hz; regreso a 660 Hz. Las desviaciones se acercan con curvas cúbicas de velocidad nula en cada nudo, comparten una meseta de .5 s y se alejan. Los contactos escritos se contrastan con los parciales reales en encuentros-medidos.json; no se afirma coincidencia física exacta. Después el clarinete termina antes y la viola completa Mi–Re–La–Si.\n\nSon los motores originales cuerda.js (viola y contrabajo), clarinete.js y piano.js. Corrección pequeña de afinación por nota si YIN es estable; deriva por remuestreo de las notas físicas. Sin osciladores aditivos ni cantante. El piano queda sin corrección. Semilla 1610262 identifica la ejecución; algunos motores usan sus semillas internas originales.\n\nAudio {base}.m4a; WAV y stems locales excluidos de git. PNG final, og.png 1200×630, PNGs de etapas y GIF de 7.8 s. Partitura, fuentes y mediciones conservadas. No hubo escucha humana durante la producción.\n')
 dump(out/'receta.json',{'id':initial['id'],'nonce':initial['nonce'],'semilla':SEED,'contenido_sha256':{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}})
 print(json.dumps({'carpeta':str(out),'notas':len(details),'aac':metrics,'mediana_cents':float(np.median(errors)),'contactos':contacts},ensure_ascii=False),flush=True)
if __name__=='__main__':
 if sys.argv[1]=='iniciar':initialize()
 elif sys.argv[1]=='sondas':probes(Path(sys.argv[2]))
 elif sys.argv[1]=='terminar':finish(Path(sys.argv[2]))
