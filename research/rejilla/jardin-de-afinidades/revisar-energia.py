"""Revisiones II–III: escritura temporal, presión y dinámica; versiones exclusivas."""
from pathlib import Path
import json,os,sys,hashlib,subprocess
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter,sosfilt,stft,find_peaks
import matplotlib.pyplot as plt
from PIL import Image
import preludio as util
ROOT=Path(__file__).resolve().parent;BANK=ROOT.parent/'objetos/motor';SR=48000
dump=util.dump;png=util.png;wav=util.wav;sha=util.sha;txt=util.textfile;pitch=util.pitch
def hz(m):return 440*2**((m-69)/12)
CONFIG={
 'invencion':{
  'titulo':'APRENDER A IRSE / IMPULSO Y SUSPENSIÓN','slug':'invencion-impulso','semilla':1610265,
  'anterior':'invencion-aprender-a-irse-s1610262-451354700f62','render':'invencion-render.cjs',
  'mapa':[[0,0],[1,1],[9.5,7.2],[16.2,12.4],[17.3,13.8],[17.8,15.5],[20.1,17.8],[31,24.5],[37.2,28.6],[38.3,30],[38.8,32.3],[41.2,34],[42,36.2],[54,43.2],[64,49],[65,51.5],[71.2,56.5],[72.3,58],[72.8,60],[75.2,62.5],[77.6,64],[80,67.2],[84,71.2]],
  'dinamica':[[0,.78],[10,1.05],[16,.78],[17.5,.58],[20,1.18],[31,1.5],[37,.9],[38.5,.55],[42,.78],[54,1.7],[64,1.5],[65,.85],[71,.75],[72.5,.48],[75,.8],[78,.6],[82,.20]],
  'corte':[[0,1],[34.15,1],[34.20,0],[35.98,0],[36.10,1],[100,1]],
  'colores':{'clarinete':'#97bfdf','viola':'#d3acdc','bajo':'#9fc8a5','piano':'#e7c58b'},
  'resumen':'Las siete frases se comprimen de manera distinta; tres mesetas armónicas suspenden la carrera durante 1.7, 2.3 y 2 segundos. Articulaciones cortas en los pasajes de impulso, interrupción real antes del episodio y salida concentrada. Conserva las 101 alturas y sus instrumentos.'},
 'coral':{
  'titulo':'RAÍCES DEL MISMO CIELO / CRECER Y CORTAR','slug':'coral-respiracion','semilla':1610266,
  'anterior':'coral-raices-del-mismo-cielo-s1610263-2a14a5b40bde','render':'coral-render.cjs',
  'mapa':[[0,0],[1,1.5],[17,20.2],[21,24],[39,40.5],[43,45],[49.4,49.5],[53,52.4],[59.4,56.5],[61,57.6],[65,63.8],[82,81.8],[86,86]],
  'dinamica':[[0,.72],[17,.80],[21,1.05],[32,1.25],[39,1.35],[43,.82],[49,1.15],[54,1.65],[59.5,2.15],[61,2.15],[65,.48],[72,.55],[78,.34],[84,.18]],
  'corte':[[0,1],[56.80,1],[56.85,0],[63.65,0],[63.78,1],[100,1]],
  'colores':{'violin':'#e0bfdd','viola':'#bca6d4','chelo':'#9fcba9','bajo':'#679c93','clarinete':'#9dc2e3','metal':'#e7c58b','gong':'#b7bdc0'},
  'resumen':'Primera frase más espaciosa; segunda con más tensión; tercera comprimida, en crescendo sostenido hasta el corte. Silencio de casi siete segundos y regreso frágil. Conserva las 46 alturas/eventos de las siete partes; cambia duraciones, presión, expresión y articulación del tutti.'}
}
def configure(mode):
 global C,COL,SEED
 C=CONFIG[mode];COL=C['colores'];SEED=C['semilla']
def warp(t):return float(np.interp(t,*np.array(C['mapa']).T))
def title(fig,s):
 fig.suptitle(C['titulo']+' / '+s,x=.06,ha='left',fontsize=13)
 fig.text(.06,.025,f'Jardín de afinidades · revisión de tiempo e intensidad · Canek Zapata · semilla {SEED}',fontsize=10)
 fig.tight_layout(rect=(.035,.06,.985,.91))
def initialize(mode):
 old=ROOT/C['anterior'];original=json.loads((old/'partitura.json').read_text(encoding='utf8'))
 I={name:[] for name in original['instrumentos']}
 for name,events in original['instrumentos'].items():
  for olde in events:
   e=dict(olde);t=e['t'];dur=e['dur'];e['t_origen']=t;e['dur_origen']=dur
   factor=.82 if mode=='invencion' and dur<1.0 and (20<=t<37 or 42<=t<65) else 1.
   e['t']=warp(t);e['dur']=warp(t+dur*factor)-warp(t)
   e['v']=float(np.clip(olde['v']*np.interp(t,*np.array(C['dinamica']).T)**.22,.26,.83))
   if olde.get('deriva_cents'):
    knots=[]
    for local,cents in olde['deriva_cents']:
     k=[warp(t+min(local,dur)*factor)-warp(t),cents]
     if knots and abs(k[0]-knots[-1][0])<1e-8:knots[-1]=k
     else:knots.append(k)
    e['deriva_cents']=knots
   I[name].append(e)
 duration=int(np.ceil(max(e['t']+e['dur'] for evs in I.values() for e in evs)+3))
 P={**original,'semilla':SEED,'duracion':duration,'instrumentos':I,'version':'revisión de energía','origen':C['anterior'],'mapa_tiempo':C['mapa'],'expresion_tiempo_original':C['dinamica'],'corte_tiempo_real':C['corte'],'cambios':C['resumen']}
 if 'forma' in P:P['forma']={n:[warp(a),warp(b)] for n,(a,b) in P['forma'].items()}
 if 'reglas_tiempo' in P:
  P['reglas_tiempo_originales']=P.pop('reglas_tiempo')
  P['nota_reglas']='Las entradas originales se reinterpretan con mapa_tiempo. Las reglas anteriores se conservan sólo como procedencia.'
 if 'encuentros' in P:P['encuentros']=[{**m,'t':warp(m['t']),'meseta_s':[warp(x) for x in m['meseta_s']]} for m in P['encuentros']]
 fig,axes=plt.subplots(2,1,figsize=(12,6.3),dpi=100)
 knots=np.array(C['mapa']);speed=np.diff(knots[:,0])/np.diff(knots[:,1]);mid=(knots[:-1,1]+knots[1:,1])/2
 axes[0].step(mid,speed,where='mid',color='#e9cd95');axes[0].axhline(1,color='#768c95',ls='--');axes[0].set(ylabel='velocidad relativa',xlabel='segundos nuevos · 1 = anterior')
 dk=np.array(C['dinamica']);axes[1].plot([warp(x) for x in dk[:,0]],dk[:,1],color='#9bd1b8');axes[1].set(ylabel='expresión escrita',xlabel='segundos nuevos')
 title(fig,'01 / dirección antes de sintetizar');fig.canvas.draw();nonce=os.urandom(24).hex()
 digest=hashlib.sha256(bytes(fig.canvas.buffer_rgba())+Path(__file__).read_bytes()+(ROOT/C['render']).read_bytes()+(ROOT/'preludio.py').read_bytes()+nonce.encode()).hexdigest();tag=digest[:12]
 out=ROOT/f'{C["slug"]}-s{SEED}-{tag}';out.mkdir(exist_ok=False)
 for d in ['render','proceso','fuentes']:(out/d).mkdir()
 png(out/'proceso'/f'01-direccion-s{SEED}-{tag}.png',fig);dump(out/'partitura.json',P)
 for p in [Path(__file__),ROOT/C['render'],ROOT/'preludio.py']+list(BANK.glob('*.js')):
  with (out/'fuentes'/p.name).open('xb') as f:f.write(p.read_bytes())
 dump(out/'receta-inicial.json',{'id':digest,'nonce':nonce,'semilla':SEED,'fecha':'2026-10-16','banco_sha256':{p.name:sha(p) for p in BANK.glob('*.js')},'fuentes_sha256':{p.name:sha(p) for p in (out/'fuentes').iterdir()},'partitura_anterior_sha256':sha(old/'partitura.json')})
 print(out,flush=True)

def finish_invencion(out):
 P=json.loads((out/'partitura.json').read_text(encoding='utf8'));initial=json.loads((out/'receta-inicial.json').read_text(encoding='utf8'));tag=initial['id'][:12];DUR=P['duracion'];N=round(SR*DUR)
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
   oldtime=np.interp(times+e['t'],np.array(C['mapa'])[:,1],np.array(C['mapa'])[:,0])
   expression=np.interp(oldtime,*np.array(C['dinamica']).T)
   z*=env*(e['v']/.6)*expression;a=round(e['t']*SR);count=min(len(z),N-a);y[a:a+count]+=z[:count]
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
   z=isolated[m[name]];left,right=m['meseta_s'];seg=z[round((left-m['t']+.03)*SR):round((right-m['t']-.03)*SR)].astype(float)
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
 mix=(dry+wet)*np.interp(np.arange(N)/SR,*np.array(C['corte']).T)[:,None];mix*=np.minimum(1,np.maximum(0,(DUR-np.arange(N)/SR)/.8))[:,None];mix*=.76/np.max(np.abs(mix))
 base=f'{C["slug"]}-s{SEED}-{tag}';wav(out/(base+'.wav'),mix)
 ff='C:/msys64/mingw64/bin/ffmpeg.exe'
 meter=subprocess.run([ff,'-hide_banner','-nostdin','-i',str(out/(base+'.wav')),'-af','loudnorm=I=-18:TP=-2:LRA=20:print_format=json','-f','null','-'],capture_output=True,text=True)
 before=json.JSONDecoder().raw_decode(meter.stderr[meter.stderr.rfind('{'):])[0]
 gain=min(-18-float(before['input_i']),-2-float(before['input_tp']))
 r=subprocess.run([ff,'-hide_banner','-nostdin','-n','-i',str(out/(base+'.wav')),'-af',f'volume={gain:.4f}dB','-c:a','aac','-b:a','256k',str(out/(base+'.m4a'))],capture_output=True,text=True);assert r.returncode==0,r.stderr
 dump(out/'master-ganancia.json',{'tipo':'ganancia fija sin compresión','ganancia_dB':gain,'premaster':before})
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
 dump(out/'verificacion.json',{'aac':metrics,'duracion_decodificada':len(pcm)/SR,'pico_muestra':float(np.max(np.abs(pcm))),'notas':len(details),'ventanas':len(details)*2,'periodicidad_YIN':len(errors),'dentro_50cents':int(np.sum(np.array(errors)<50)),'mediana_abs_cents':float(np.median(errors)),'detalle':details,'banco_intacto':True,'metodo':'YIN abierto 70–1200 Hz, ventanas 200 ms; FFT de contactos sobre las nuevas mesetas menos 30 ms por extremo, máximo local a ±12 Hz del parcial previsto. Esa búsqueda verifica energía cerca del objetivo, no determina altura global.','escucha':'Sin escucha humana durante producción.'})
 txt(out/'proceso'/'README.md',f'# Etapas reales\n\n1. Dirección temporal y dinámica antes de sintetizar.\n2. '+('Parciales medidos durante las nuevas suspensiones.' if C['slug'].startswith('invencion') else 'Energía de las siete partes ya sintetizadas y fraseadas.')+'\n3. Energía de partes y espectrograma del AAC final.\n4. Revisión de los cuadros decodificados del GIF.\n\nGIF 7.8 s, tres primeras etapas. Semilla '+str(SEED)+'.\n')
 txt(out/'README.md',f'# {C["titulo"].title()}\n\nRevisión de tiempo e intensidad, Jardín de afinidades. Canek Zapata, 16 de octubre de 2026. {DUR} segundos.\n\n{C["resumen"]}\n\nSe reescribieron tiempos, duraciones, presión de los modelos y expresión. Todas las notas se renderizaron de nuevo; no se estiró ni automatizó el máster previo. Ganancia final fija, sin compresión dinámica. Partitura.json conserva el mapa entre tiempo anterior y nuevo, los cortes, expresión y fuentes. La calibración de registro se aplica antes de la expresión para no borrar el fraseo.\n\nVersión anterior conservada: ../{C["anterior"]}/. Los motores originales siguen intactos. Afinación pequeña por nota si es estable y deriva por remuestreo del sonido físico; sin osciladores aditivos ni cantante. La división virtual de partes admite solapamientos. Piano con goma y gong, cuando presentes, son percusivos/inarmónicos; no se interpretan como notas desafinadas a partir de periodicidades espurias.\n\nAudio {base}.m4a. WAV y stems locales excluidos de git. PNGs reales, og.png 1200×630 y GIF de 7.8 s. Recetas, fuentes y verificación conservadas. Los campos input del medidor describen el AAC real; los campos output son una normalización hipotética enviada a null. No hubo escucha humana durante producción.\n')
 dump(out/'receta.json',{'id':initial['id'],'nonce':initial['nonce'],'semilla':SEED,'contenido_sha256':{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}})
 print(json.dumps({'carpeta':str(out),'notas':len(details),'aac':metrics,'mediana_cents':float(np.median(errors)),'contactos':contacts},ensure_ascii=False),flush=True)

def finish_coral(out):
 P=json.loads((out/'partitura.json').read_text(encoding='utf8'));initial=json.loads((out/'receta-inicial.json').read_text(encoding='utf8'));tag=initial['id'][:12];DUR=P['duracion'];N=round(SR*DUR)
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
   oldtime=np.interp(times+e['t'],np.array(C['mapa'])[:,1],np.array(C['mapa'])[:,0])
   expression=np.interp(oldtime,*np.array(C['dinamica']).T)
   if 43<=e['t_origen']<61 and name!='gong':env=np.interp(times,[0,.15,e['dur'],e['dur']+1.3],[.12,.85,1,0])
   z*=env*(e['v']/.6)*expression;a=round(e['t']*SR);count=min(len(z),N-a);y[a:a+count]+=z[:count]
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
 mix=(dry+wet)*np.interp(np.arange(N)/SR,*np.array(C['corte']).T)[:,None];mix*=np.minimum(1,np.maximum(0,(DUR-np.arange(N)/SR)/.8))[:,None];mix*=.76/np.max(np.abs(mix))
 base=f'{C["slug"]}-s{SEED}-{tag}';wav(out/(base+'.wav'),mix)
 ff='C:/msys64/mingw64/bin/ffmpeg.exe'
 meter=subprocess.run([ff,'-hide_banner','-nostdin','-i',str(out/(base+'.wav')),'-af','loudnorm=I=-18:TP=-2:LRA=20:print_format=json','-f','null','-'],capture_output=True,text=True)
 before=json.JSONDecoder().raw_decode(meter.stderr[meter.stderr.rfind('{'):])[0]
 gain=min(-18-float(before['input_i']),-2-float(before['input_tp']))
 r=subprocess.run([ff,'-hide_banner','-nostdin','-n','-i',str(out/(base+'.wav')),'-af',f'volume={gain:.4f}dB','-c:a','aac','-b:a','256k',str(out/(base+'.m4a'))],capture_output=True,text=True);assert r.returncode==0,r.stderr
 dump(out/'master-ganancia.json',{'tipo':'ganancia fija sin compresión','ganancia_dB':gain,'premaster':before})
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
 txt(out/'proceso'/'README.md',f'# Etapas reales\n\n1. Dirección temporal y dinámica antes de sintetizar.\n2. '+('Parciales medidos durante las nuevas suspensiones.' if C['slug'].startswith('invencion') else 'Energía de las siete partes ya sintetizadas y fraseadas.')+'\n3. Energía de partes y espectrograma del AAC final.\n4. Revisión de los cuadros decodificados del GIF.\n\nGIF 7.8 s, tres primeras etapas. Semilla '+str(SEED)+'.\n')
 txt(out/'README.md',f'# {C["titulo"].title()}\n\nRevisión de tiempo e intensidad, Jardín de afinidades. Canek Zapata, 16 de octubre de 2026. {DUR} segundos.\n\n{C["resumen"]}\n\nSe reescribieron tiempos, duraciones, presión de los modelos y expresión. Todas las notas se renderizaron de nuevo; no se estiró ni automatizó el máster previo. Ganancia final fija, sin compresión dinámica. Partitura.json conserva el mapa entre tiempo anterior y nuevo, los cortes, expresión y fuentes. La calibración de registro se aplica antes de la expresión para no borrar el fraseo.\n\nVersión anterior conservada: ../{C["anterior"]}/. Los motores originales siguen intactos. Afinación pequeña por nota si es estable y deriva por remuestreo del sonido físico; sin osciladores aditivos ni cantante. La división virtual de partes admite solapamientos. Piano con goma y gong, cuando presentes, son percusivos/inarmónicos; no se interpretan como notas desafinadas a partir de periodicidades espurias.\n\nAudio {base}.m4a. WAV y stems locales excluidos de git. PNGs reales, og.png 1200×630 y GIF de 7.8 s. Recetas, fuentes y verificación conservadas. Los campos input del medidor describen el AAC real; los campos output son una normalización hipotética enviada a null. No hubo escucha humana durante producción.\n')
 dump(out/'receta.json',{'id':initial['id'],'nonce':initial['nonce'],'semilla':SEED,'contenido_sha256':{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}})
 print(json.dumps({'carpeta':str(out),'notas':len(details),'aac':metrics,'mediana_cents':float(np.median(errors))},ensure_ascii=False),flush=True)
if __name__=='__main__':
 mode=sys.argv[2];configure(mode)
 if sys.argv[1]=='iniciar':initialize(mode)
 elif sys.argv[1]=='terminar':
  (finish_invencion if mode=='invencion' else finish_coral)(Path(sys.argv[3]))
