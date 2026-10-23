"""IV. Danza 3+3+2, propagación de ataques, suspensión y regreso abreviado."""
from pathlib import Path
import json,os,sys,hashlib,subprocess
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter,sosfilt,stft,find_peaks,correlate
import matplotlib.pyplot as plt
from PIL import Image
import preludio as util
ROOT=Path(__file__).resolve().parent;BANK=ROOT.parent/'objetos/motor';SR=48000;DUR=63;SEED=1610267
COL={'piano':'#e7c58b','cuerda':'#d3acdc','bajo':'#9fcba9','clarinete':'#9dc2e3','objeto':'#ec9e8b','agua':'#83c9ca'}
dump=util.dump;png=util.png;wav=util.wav;sha=util.sha;txt=util.textfile;pitch=util.pitch
def hz(m):return 440*2**((m-69)/12)
def strict_pitch(x,center):
 a=max(0,round((center-.1)*SR));b=min(len(x),round((center+.1)*SR));y=x[a:b:3].astype(float)
 if len(y)<600:return None
 y-=y.mean();sr=SR/3;hi=int(sr/70);lo=int(sr/1200);w=len(y)-hi-1
 if np.mean(y*y)<1e-11:return None
 ac=correlate(y,y[:w],mode='valid',method='fft')[:hi+1];en=np.r_[0,np.cumsum(y*y)];tau=np.arange(hi+1)
 dif=np.maximum(0,en[w]+en[w+tau]-en[tau]-2*ac);cm=np.ones_like(dif);cm[1:]=dif[1:]*tau[1:]/np.maximum(np.cumsum(dif[1:]),1e-15)
 ix=np.flatnonzero(cm[lo:]<.005)
 if not len(ix):return None
 j=lo+int(ix[0])
 while j<hi-1 and cm[j+1]<cm[j]:j+=1
 if j>=hi:return None
 den=cm[j-1]-2*cm[j]+cm[j+1];fraction=.5*(cm[j-1]-cm[j+1])/den if abs(den)>1e-12 else 0
 return float(sr/(j+fraction))
def estimate(name,e,x,center):
 return strict_pitch(x,center) if name=='objeto' and e['tipo']!='barra' else pitch(x,center)
def title(fig,s):
 fig.suptitle('LO QUE SALTA DE UNA RAMA / '+s,x=.06,ha='left',fontsize=16)
 fig.text(.06,.025,'Jardín de afinidades · IV. Scherzo · Canek Zapata · semilla 1610267',fontsize=10)
 fig.tight_layout(rect=(.035,.06,.985,.91))
def metrical(points,maximum):
 grid=np.linspace(0,maximum,maximum*1000+1);bpm=np.interp(grid,*np.array(points).T)
 seconds=np.r_[0,np.cumsum((30/bpm[:-1]+30/bpm[1:])*.0005)]
 return lambda u:float(np.interp(u,grid,seconds))
def initialize():
 I={n:[] for n in COL};cascades=[]
 def add(name,t,m,dur=.22,v=.55,tipo=None,prep=None,drift=None):
  e={'id':f'{name}-{len(I[name]):03}','t':float(t),'m':float(m),'dur':float(dur),'v':float(v),'tipo':tipo or {'piano':'martillo','cuerda':'pizz','bajo':'pizz','clarinete':'llaves','objeto':'barra','agua':'gota'}[name]}
  if name=='piano':e['prep']=prep or 'papel'
  if drift:e['deriva_cents']=drift
  I[name].append(e);return e['id']
 def cascade(t,gap,label):
  names=['cuerda','piano','objeto','clarinete','piano','cuerda','objeto'];notes=[57,59,64,62,69,64,57]
  offsets=[0]
  for k in range(6):offsets.append(offsets[-1]+gap*np.exp(-.16*k))
  ids=[]
  for k,(name,m,o) in enumerate(zip(names,notes,offsets)):ids.append(add(name,t+o,m,.32,.55+.03*k,prep='goma'))
  cascades.append({'t':t,'tipo':label,'separacion_inicial_s':gap,'offsets_s':offsets,'eventos':ids})
 pulseA=[[0,112],[16,124],[40,144],[56,128],[80,156],[96,96]];ta=metrical(pulseA,96)
 motif=[57,59,64,62];routes=['cuerda','piano','objeto','piano']
 for cycle in range(12):
  shift=[0,0,-2,0,0,3,-2,0,5,0,-2,0][cycle];strength=.75+cycle*.035
  if cycle in [3,7,11]:cascade(1+ta(cycle*8),[.16,.055,.003][[3,7,11].index(cycle)],'contracción')
  else:
   for k,pulse in enumerate([0,2,3,6]):
    m=motif[k]+shift
    if routes[k]=='objeto':m=min(m,67)
    add(routes[k],1+ta(cycle*8+pulse),m,.23 if k!=2 else .34,(.60 if pulse in [0,3,6] else .45)*strength,prep='goma' if cycle%3==1 else 'papel')
  for pulse in [1,4,7]:
   if cycle%4==2 and pulse==4:continue
   add('clarinete',1+ta(cycle*8+pulse),[50,57,52][pulse%3],.10,.35*strength)
  if cycle%2==0:
   add('bajo',1+ta(cycle*8),[45,43,41,47,45,40][cycle//2],.35,.54*strength)
   add('bajo',1+ta(cycle*8+6),52,.22,.39*strength)
 endA=1+ta(96)
 # El último acorde se suspende; algunos ataques todavía intentan seguir la danza.
 add('objeto',26,57,13.2,.61,tipo='sax-flauta',drift=[[0,10],[4,0],[6,0],[11,-18],[13.2,-22]])
 dm=69+12*np.log2((440/3)/440)
 add('clarinete',27.1,dm,10.8,.52,tipo='normal',drift=[[0,-10],[2.9,0],[4.9,0],[10.8,20]])
 for k,t in enumerate([25.2,25.65,26.25,27.1,28.25,29.8]):
  add('cuerda' if k%2 else 'piano',t,[57,59,64,62,59,57][k],.22,.45-.035*k,prep='goma')
 for t,m in [(34.5,57),(37.4,62),(40.3,59)]:add('agua',t,m,.18,.42)
 # Retorno: más corto y rápido. Las cascadas ahora se abren.
 pulseB=[[0,138],[16,156],[40,176],[64,192]];tb=metrical(pulseB,64)
 for cycle in range(8):
  t=44+tb(cycle*8)
  if cycle in [0,3,7]:cascade(t,[.003,.065,.19][[0,3,7].index(cycle)],'dispersión')
  else:
   for k,pulse in enumerate([0,2,3,6]):
    if (cycle,k) in [(2,1),(5,3),(6,0)]:continue
    add(routes[(k+1)%4],44+tb(cycle*8+pulse),motif[k],.17,.65 if k in [0,2] else .43,prep='papel')
  for pulse in [1,4,7]:
   if cycle in [2,5] and pulse==7:continue
   add('clarinete',44+tb(cycle*8+pulse),52,.085,.35)
  if cycle%2==1:add('bajo',t,45 if cycle<5 else 43,.22,.55)
 cascade(57,.23,'última dispersión')
 for name,m in [('bajo',45),('piano',52),('cuerda',59)]:add(name,59.2,m,.18,.64,prep='goma')
 P={'titulo':'Lo que salta de una rama','movimiento':'IV. Scherzo','semilla':SEED,'duracion':DUR,'instrumentos':I,'cascadas':cascades,'forma':{'danza':[1,endA],'trio':[25.2,41.8],'regreso':[44,60.5]},'pulso_A_BPM':pulseA,'pulso_B_BPM':pulseB,'unidad_mapa':'corcheas; integración de 30/BPM','agrupacion':[3,3,2],'corte_s':[60.45,60.5],'dinamica_s':[[0,.8],[12,1],[22,1.15],[25,.8],[31,.65],[39,.4],[44,.95],[52,1.15],[57,.9],[59.2,1.1],[60.5,0]],'nota':'Ataques de las cascadas: separación g·exp(−.16k). El ritmo regular se construye con 3+3+2 y tempo variable, no con un loop de audio.'}
 fig,axes=plt.subplots(2,1,figsize=(12,6.3),dpi=100)
 for j,(name,events) in enumerate(I.items()):
  for e in events:axes[0].plot([e['t'],e['t']+e['dur']],[j]*2,color=COL[name],lw=2)
 axes[0].set(yticks=range(6),yticklabels=list(I),xlim=(0,DUR),xlabel='segundos · danza / suspensión / regreso')
 for c in cascades:axes[1].plot(np.arange(7),np.array(c['offsets_s'])*1000,marker='.',lw=1,label=f"{c['t']:.1f}s {c['tipo']}")
 axes[1].set(xlabel='ataque dentro de la cascada',ylabel='demora acumulada · ms');axes[1].legend(facecolor='#233238',labelcolor='#e9e5d5',fontsize=7,ncol=2)
 title(fig,'01 / un ataque puede convertirse en acorde');fig.canvas.draw();nonce=os.urandom(24).hex()
 digest=hashlib.sha256(bytes(fig.canvas.buffer_rgba())+Path(__file__).read_bytes()+(ROOT/'scherzo-render.cjs').read_bytes()+(ROOT/'preludio.py').read_bytes()+nonce.encode()).hexdigest();tag=digest[:12]
 out=ROOT/f'scherzo-lo-que-salta-s{SEED}-{tag}';out.mkdir(exist_ok=False)
 for d in ['render','proceso','fuentes']:(out/d).mkdir()
 png(out/'proceso'/f'01-ataques-s{SEED}-{tag}.png',fig);dump(out/'partitura.json',P)
 for p in [Path(__file__),ROOT/'scherzo-render.cjs',ROOT/'preludio.py']+list(BANK.glob('*.js')):
  with (out/'fuentes'/p.name).open('xb') as f:f.write(p.read_bytes())
 dump(out/'receta-inicial.json',{'id':digest,'nonce':nonce,'semilla':SEED,'fecha':'2026-10-16','banco_sha256':{p.name:sha(p) for p in BANK.glob('*.js')},'fuentes_sha256':{p.name:sha(p) for p in (out/'fuentes').iterdir()}})
 print(out,flush=True)
def probes(out):
 result=[]
 for p in sorted((out/'render').glob('sonda-*.wav')):
  sr,x=wavfile.read(p);centers=[.7,2.5,4.2] if 'morfosis' in p.name else [.15,.3]
  result.append({'archivo':p.name,'centros_s':centers,'Hz_YIN':[pitch(x,c) for c in centers],'Hz_YIN_estricto':[strict_pitch(x,c) for c in centers] if 'morfosis' in p.name else None,'pico':float(np.max(np.abs(x)))})
 dump(out/'sondas-medidas.json',result);print(json.dumps(result),flush=True)

def finish(out):
 P=json.loads((out/'partitura.json').read_text(encoding='utf8'));initial=json.loads((out/'receta-inicial.json').read_text(encoding='utf8'));tag=initial['id'][:12];N=round(SR*DUR)
 assert all(sha(BANK/n)==s for n,s in initial['banco_sha256'].items())
 stems={};details=[];isolated={}
 for name,events in P['instrumentos'].items():
  y=np.zeros(N,dtype=np.float32)
  for e in events:
   sr,x=wavfile.read(out/'render'/(e['id']+'.wav'));assert sr==SR and np.isfinite(x).all()
   f=e.get('Hz_objetivo',hz(e['m']));values=[estimate(name,e,x,e['dur']*q) for q in [.35,.55,.75]];valid=[v for v in values if v]
   measured=float(np.median(valid)) if valid else None;cents=1200*np.log2(measured/f) if measured else None
   pitched=name in ['cuerda','bajo'] or (name=='clarinete' and e['tipo']=='normal') or (name=='objeto' and e['tipo']!='barra')
   correction=f/measured if pitched and measured and abs(cents)<70 else 1
   if pitched and name not in ['cuerda','bajo'] and measured and abs(cents)>70:raise ValueError((e['id'],'altura fuera de registro',cents))
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
    gain=min(80,.04/max(float(np.sqrt(np.mean(core.astype(float)**2))),1e-9));z*=gain
   env=np.interp(times,[0,.08,e['dur']*.4,e['dur']*.8,e['dur'],e['dur']+1.3],[.25,.85,1,.65,.12,0]) if e['dur']>1 else np.interp(times,[0,.04,e['dur'],e['dur']+1.3],[.5,1,.65,0])
   z*=env*(e['v']/.6)*np.interp(times+e['t'],*np.array(P['dinamica_s']).T);a=round(e['t']*SR);count=min(len(z),N-a);y[a:a+count]+=z[:count]
   isolated[e['id']]=z
   final=[]
   for q in [.35,.75]:
    c=e['dur']*q;det=estimate(name,e,z,c);d=float(np.interp(c,times,drift));target=f*2**(d/1200)
    final.append({'t_local':c,'Hz':det,'objetivo_Hz':target,'error_cents':1200*np.log2(det/target) if det else None})
   details.append({'id':e['id'],'crudo_Hz':values,'correccion_cents':1200*np.log2(correction),'calibracion_registro':gain,'afinable':pitched,'tipo':e['tipo'],'final':final})
  active=np.abs(y)>1e-4;rms=np.sqrt(np.mean(y[active].astype(float)**2));y*= {'piano':.035,'cuerda':.048,'bajo':.035,'clarinete':.025,'objeto':.045,'agua':.018}[name]/max(rms,1e-9)
  stems[name]=y;wav(out/'render'/(name+'-mezcla.wav'),y)
 # Etapa real: latencia física de ataques frente a sus disparos, y cambio del cuerpo sax/flauta.
 arrival={}
 for id,z in isolated.items():
  energy=np.cumsum(z[:round(.2*SR)].astype(float)**2)
  arrival[id]=float(np.searchsorted(energy,energy[-1]*.1)/SR) if energy[-1]>1e-14 else None
 details_by_id={e['id']:e for events in P['instrumentos'].values() for e in events}
 attacks=[]
 fig,axes=plt.subplots(2,1,figsize=(12,6.3),dpi=100)
 for c in P['cascadas']:
  realized=[details_by_id[id]['t']+arrival[id] if arrival[id] is not None else None for id in c['eventos']]
  relative=[v-c['t'] if v is not None else None for v in realized]
  attacks.append({**c,'llegada_10pct_energia_s':relative,'metodo':'Tiempo para alcanzar 10% de energía de los primeros 200 ms de la nota procesada; no es un detector perceptivo de ataque.'})
  axes[0].plot(np.arange(7),np.array(relative,dtype=float)*1000,marker='.',label=f"{c['t']:.1f}s",lw=1)
 axes[0].set(xlabel='ataque',ylabel='llegada de energía · ms');axes[0].legend(facecolor='#233238',labelcolor='#e9e5d5',fontsize=7,ncol=4)
 morph=next(e for e in P['instrumentos']['objeto'] if e['tipo']=='sax-flauta');z=isolated[morph['id']]
 f,tt,zz=stft(z,SR,nperseg=4096,noverlap=3072);mask=(f>100)&(f<3500)
 axes[1].pcolormesh(tt,f[mask],20*np.log10(np.abs(zz[mask])+1e-8),cmap='magma',vmin=-85,vmax=-30,shading='auto');axes[1].set(xlabel='segundos locales · saxofón a flauta',ylabel='Hz')
 title(fig,'02 / ataques reales y cuerpo que cambia');png(out/'proceso'/f'02-cuerpos-s{SEED}-{tag}.png',fig);dump(out/'ataques-medidos.json',attacks)
 dry=np.zeros((N,2));pans={'piano':-.18,'cuerda':-.4,'bajo':.04,'clarinete':.32,'objeto':.12,'agua':.44}
 for name,y in stems.items():
  angle=(pans[name]+1)*np.pi/4;dry+=np.column_stack((y*np.cos(angle),y*np.sin(angle)))
 wet=np.zeros_like(dry)
 for k,delay in enumerate([.043,.077,.113,.173,.257,.367,.523,.719,1.013,1.387,1.823]):
  shift=round(delay*SR);source=sosfilt(butter(1,5800-300*k,fs=SR,output='sos'),dry[:,::-1] if k%2 else dry,axis=0)
  wet[shift:]+=.08*np.exp(-delay/.7)*source[:-shift]
 mix=(dry+wet)*np.interp(np.arange(N)/SR,[0,*P['corte_s'],DUR],[1,1,0,0])[:,None];mix*=np.minimum(1,np.maximum(0,(DUR-np.arange(N)/SR)/.8))[:,None];mix*=.76/np.max(np.abs(mix))
 base=f'scherzo-lo-que-salta-s{SEED}-{tag}';wav(out/(base+'.wav'),mix)
 ff='C:/msys64/mingw64/bin/ffmpeg.exe'
 meter=subprocess.run([ff,'-hide_banner','-nostdin','-i',str(out/(base+'.wav')),'-af','loudnorm=I=-18:TP=-2:LRA=20:print_format=json','-f','null','-'],capture_output=True,text=True)
 before=json.JSONDecoder().raw_decode(meter.stderr[meter.stderr.rfind('{'):])[0];gain=min(-18-float(before['input_i']),-2-float(before['input_tp']))
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
 title(fig,'03 / danza, suspensión y regreso');final=out/f'scherzo-resultado-s{SEED}-{tag}.png';png(final,fig)
 with Image.open(final) as im:
  for p in [out/'og.png',out/'proceso'/f'03-mezcla-s{SEED}-{tag}.png']:
   with p.open('xb') as f:im.save(f,'PNG')
 frames=[]
 for p in sorted((out/'proceso').glob('*.png')):
  with Image.open(p) as im:frames.append(im.convert('RGB').resize((900,472)).quantize(colors=128))
 gif=out/f'scherzo-proceso-s{SEED}-{tag}.gif'
 with gif.open('xb') as f:frames[0].save(f,format='GIF',save_all=True,append_images=frames[1:],duration=2600,loop=0,optimize=False)
 with Image.open(gif) as im:
  canvas=Image.new('RGB',(1200,210));duration=0
  for i in range(im.n_frames):im.seek(i);duration+=im.info['duration'];canvas.paste(im.convert('RGB').resize((400,210)),(400*i,0))
  assert im.n_frames==3 and duration==7800 and gif.stat().st_size<15_000_000
  with (out/'proceso'/f'04-revision-s{SEED}-{tag}.png').open('xb') as f:canvas.save(f,'PNG')
 errors=[abs(p['error_cents']) for e in details if e['afinable'] for p in e['final'] if p['error_cents'] is not None]
 dump(out/'verificacion.json',{'aac':metrics,'duracion_decodificada':len(pcm)/SR,'pico_muestra':float(np.max(np.abs(pcm))),'notas':len(details),'ventanas_afinables':sum(2 for e in details if e['afinable']),'periodicidad_YIN':len(errors),'dentro_50cents':int(np.sum(np.array(errors)<50)),'mediana_abs_cents':float(np.median(errors)),'detalle':details,'banco_intacto':True,'metodo':'YIN abierto 70–1200 Hz, ventanas 200 ms; Sólo se evalúan como afinables cuerdas pulsadas, viento normal y objeto sax/flauta. Llaves, piano preparado, barra y agua conservan sus lecturas crudas sin interpretarlas como afinación.','escucha':'Sin escucha humana durante producción.'})
 txt(out/'proceso'/'README.md','# Etapas reales\n\n1. Partitura de ataques y curvas de propagación antes de renderizar.\n2. Llegadas de energía medidas en las notas físicas y espectrograma de la transformación sax/flauta.\n3. Energía de las partes y espectrograma del AAC final.\n4. Revisión de cuadros decodificados del GIF.\n\nGIF7.8 s, tres etapas reales. Semilla1610267; algunos motores conservan sus semillas internas.\n')
 txt(out/'README.md',f'# Lo que salta de una rama\n\nIV. Scherzo de Jardín de afinidades. Canek Zapata,16 de octubre de2026. 1:03.\n\nDanza de3/8+3/8+2/8, trío suspendido y regreso abreviado. Piano con papel/goma, viola pizz, contrabajo pizz, llaves/voz normal de clarinete bajo, objeto barra/sax/flauta y tres gotas de agua. Tema La–Si–Mi–Re repartido entre cuerpos. Dos mapas de tempo variables: primera danza112–156 con frenada a96; regreso138–192 BPM. Los ataques de las cascadas usan separaciones g×exp(−.16k), con g que baja de160 a3 ms y luego crece hasta230 ms. Se mide la llegada de energía física, distinta del disparo programado.\n\nTrío: el objeto a220 Hz se transforma en sus lazos físicos de saxofón a flauta, con registro seguro. Clarinete a146.667 Hz puede compartir la zona de440 Hz por su tercer parcial y el segundo del objeto. Pequeñas derivas se aproximan y se separan; no se afirma coincidencia física exacta. Los ataques rezagados frenan y quedan tres gotas. El regreso tiene omisiones escritas y termina con dispersión, último impulso y corte a60.5 s.\n\nCinco modelos originales sin cambios: piano.js,cuerda.js,clarinete.js,objeto.js yagua.js. Sin osciladores aditivos ni cantante. Afinación pequeña por nota cuando estable en cuerdas/vientos; deriva por remuestreo. No se corrigen como alturas llaves,piano preparado,barra ni gotas. Ganancia final fija sin compresión. Los campos input del medidor corresponden al AAC; output es una normalización hipotética enviada a null.\n\nAudio {base}.m4a. WAV/stems locales excluidos de git. Partitura, fuentes, recetas y verificación; PNGs reales, og.png1200×630 y GIF7.8 s. Sin escucha humana durante producción.\n')
 dump(out/'receta.json',{'id':initial['id'],'nonce':initial['nonce'],'semilla':SEED,'contenido_sha256':{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}})
 print(json.dumps({'carpeta':str(out),'notas':len(details),'aac':metrics,'mediana_cents':float(np.median(errors))},ensure_ascii=False),flush=True)
if __name__=='__main__':
 if sys.argv[1]=='iniciar':initialize()
 elif sys.argv[1]=='sondas':probes(Path(sys.argv[2]))
 elif sys.argv[1]=='terminar':finish(Path(sys.argv[2]))
