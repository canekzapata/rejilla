from pathlib import Path
import sys,json,subprocess,importlib.util,warnings,hashlib
import numpy as np
from scipy.signal import butter,sosfilt,resample_poly,iirpeak,lfilter
from scipy.io import wavfile
from PIL import Image

R=Path(__file__).resolve().parent;REPO=R.parent;SR=32000
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
sc=module('score',R/'partitura.py');sy=module('sintes',REPO/'lo-que-tapa-la-traspuesta/sintes2.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):return subprocess.run(args,check=True,capture_output=True)
def env(n,a=.01,r=.06):
 t=np.arange(n)/SR;return np.minimum(1,t/max(a,1/SR))*np.minimum(1,np.maximum(0,n/SR-t)/max(r,1/SR))
def unit(y,p=.9):return y*(p/(np.max(np.abs(y))+1e-12))
def writewav(p,y):
 assert np.isfinite(y).all(),p
 with p.open('xb') as f:wavfile.write(f,SR,y.astype(np.float32))
def active(y):
 # Use 50 ms frames, excluding actual rests; never boost an isolated event by whole-track RMS.
 a=y.mean(axis=1) if y.ndim==2 else y;n=len(a)//1600
 rms=np.sqrt(np.mean(a[:n*1600].reshape(n,1600)**2,axis=1));use=rms>max(float(rms.max())*.06,1e-8)
 return float(np.sqrt(np.mean(rms[use]**2))) if use.any() else 0
def level(y,target=.12):
 if not np.any(y):return y
 gain=target/(active(y)+1e-12);gain=min(gain,.95/(float(np.max(abs(y)))+1e-12));return (y*gain).astype(np.float32)
def resonador_cobre(x,events):
 """New effect instrument: a bank of measured vowel regions, excited by the existing trumpet signal."""
 V={'a':[(700,5),(1300,6),(2900,9)],'e':[(420,6),(1900,7),(2900,9)],'i':[(280,6),(2350,8),(3200,9)],'o':[(450,6),(950,7),(2600,9)],'u':[(310,6),(750,7),(2350,9)]}
 y=np.zeros(len(x),np.float32);sumw=np.zeros(len(x),np.float32)
 for vowel,peaks in V.items():
  w=np.zeros(len(x),np.float32)
  for e in events:
   if e.get('vocal','a')!=vowel:continue
   a=int(e['t']*SR);n=min(int((e['dur']+.06)*SR),len(x)-a)
   if n>0:w[a:a+n]=np.maximum(w[a:a+n],env(n,.018,.08))
  if not w.any():continue
  q=np.zeros(len(x),np.float32)
  for f,Q in peaks:
   b,a=iirpeak(f,Q,fs=SR);q+=lfilter(b,a,x).astype(np.float32)*Q*.7
  y+=q*w;sumw+=w
 y/=np.maximum(1,sumw)
 return level(y,.10)

def main(out):
 P=json.loads((out/'partitura.json').read_text('utf8'));sc.P=P;tag=out.name.split('-')[-1];D=P['duracion'];N=int(np.ceil(D*SR));rng=np.random.default_rng(P['semilla'])
 print('Render físico a 48 kHz',flush=True)
 subprocess.run(['node',str(R/'fisicos.cjs'),str(out)],check=True)
 subprocess.run(['node',str(REPO/'otra-vez-hasta-romper/kit.cjs'),str(out)],check=True)
 stems={};metrics={}
 def save(name,y):
  y=np.asarray(y,np.float32);assert len(y)==N
  metrics[name]=dict(activo=active(y),pico=float(np.max(abs(y))))
  writewav(out/'render'/f'{name}-{tag}.wav',y);stems[name]=y
 def stereo(y,pan=0):
  angle=(pan+1)*np.pi/4;return np.stack([y*np.cos(angle),y*np.sin(angle)],axis=-1)
 def blank():return np.zeros((N,2),np.float32)
 def add(dest,y,t,g=1,pan=0):
  a=round(t*SR);n=min(len(y),N-a)
  if a<0 or n<=0:return
  angle=(pan+1)*np.pi/4;dest[a:a+n,0]+=y[:n]*g*np.cos(angle);dest[a:a+n,1]+=y[:n]*g*np.sin(angle)
 phys={}
 for name in ['trompeta','garganta','sax','chelo-arco','chelo-pizz','piano']:
  y=resample_poly(np.fromfile(out/'render'/f'{name}.f32',dtype=np.float32),2,3)
  y=np.pad(y,(0,max(0,N-len(y))))[:N];y=sosfilt(butter(2,100 if name!='chelo-arco' else 65,fs=SR,btype='high',output='sos'),y).astype(np.float32)
  phys[name]=level(y,.16 if name in ['trompeta','garganta','sax'] else .095)
 save('metal-principal',stereo(phys['trompeta'],-.07));save('garganta-principal',stereo(phys['garganta'],.08));save('sax-contracanto',stereo(phys['sax'],.29))
 save('cuerdas',stereo(phys['chelo-arco'],-.3)+stereo(phys['chelo-pizz'],-.25));save('piano-preparado',stereo(phys['piano'],.25))
 metalv=resonador_cobre(phys['trompeta'],P['trompeta']);save('cobre-vocal',stereo(metalv,.45))
 print('Cobre vocal y cuerpos físicos completos',flush=True)
 # Bass and electric lead from existing engines. RuntimeWarnings are checked by finite output assertions.
 for name,timbre,dest,target,pan in [('bajo','fretless','fretless',.15,0),('sinte','zawinul','sinte-solista',.17,-.1),('doble','zawinul','doble-del-lead',.065,-.18)]:
  with warnings.catch_warnings():
   warnings.simplefilter('ignore',RuntimeWarning);y=sy.mono(P[name],int(np.ceil(D*48000)),timbre,P['semilla'])
  assert np.isfinite(y).all(),dest
  y=resample_poly(y,2,3);y=np.pad(y,(0,max(0,N-len(y))))[:N];save(dest,stereo(level(y,target),pan))
 # New modal Rhodes: changing fundamental decay, tine at 7f, gentle bark; its score has independent comping.
 rh=blank()
 for e in P['rhodes']:
  n=int((e['dur']+.42)*SR);t=np.arange(n)/SR;f=sc.hz(e['m']);ph=2*np.pi*f*t
  y=(np.sin(ph)*np.exp(-t/1.1)+.32*np.sin(ph*2)*np.exp(-t/.38)+.17*np.sin(ph*3.003)*np.exp(-t/.23)+.11*np.sin(ph*7.01)*np.exp(-t/.12))*env(n,.002,.08)
  y=np.tanh(y*(1+e['v']*.7));add(rh,y,e['t'],e['v']*.09,e.get('pan',0))
 save('rhodes',level(rh,.11))
 # Spectral fields use explicit Hz and ratios. Source envelope gives each family a copper-shaped excitation.
 spectral=blank();copper_env=sosfilt(butter(1,18,fs=SR,output='sos'),np.abs(phys['trompeta']));copper_env/=max(float(copper_env.max()),1e-12)
 for e in P['espectro']:
  n=int(e['dur']*SR);t=np.arange(n)/SR;f=e['hz'];a=int(e['t']*SR);n=min(n,N-a);t=t[:n]
  y=(np.sin(2*np.pi*f*t)+.22*np.sin(2*np.pi*(f+.45+.18*e['voz'])*t))*env(n,.12,.22)*(.35+.65*copper_env[a:a+n])
  add(spectral,y,e['t'],.025/(1+e['voz']*.15),e['pan'])
 save('familias-espectrales',level(spectral,.07))
 # Vocal modulators from local vowel diphones. Each score voice uses its own carrier/line/position.
 bank=REPO/'inferencia/vendor/difonos/bancos/sabina-1-b44e7fab5cee';M=json.loads((bank/'manifiesto.json').read_text('utf8'))
 raw=np.frombuffer(run(['ffmpeg','-v','error','-i',str(bank/'banco.flac'),'-f','f32le','-ac','1','pipe:1']).stdout,dtype='<f4');vowels={}
 for v in 'aeiou':
  u=M['unidades'][v*2];vowels[v]=resample_poly(raw[u['inicio']+u['izq']:u['inicio']+u['der']],640,441)
 edges=np.geomspace(100,13800,25);filters=[butter(2,[a,b],fs=SR,btype='band',output='sos') for a,b in zip(edges[:-1],edges[1:])];sm=butter(1,28,fs=SR,output='sos');voice=blank()
 for count,e in enumerate(P['voces']):
  n=int(e['dur']*SR);t=np.arange(n)/SR;grain=vowels[e['vocal']];mod=np.zeros(n+len(grain))
  for j in range(0,n,max(1,len(grain)//3)):mod[j:j+len(grain)]+=grain*np.hanning(len(grain))
  f=sc.hz(e['m']);ph=2*np.pi*f*t;kind=e['carrier']
  if kind==0:carrier=sum(np.sin(ph*k)/k for k in range(1,min(36,int(14000/f))))
  elif kind==1:carrier=np.sin(ph+2.8*np.sin(ph*2.003)*np.exp(-t/1.4))
  elif kind==2:carrier=sum(np.sin(ph*k)/k**.7 for k in range(1,min(24,int(14000/f)),2))
  else:carrier=np.sin(ph)+.5*np.sin(ph*2)+.25*np.sin(ph*3)
  vocal=np.zeros(n)
  for filt in filters:vocal+=sosfilt(filt,carrier)*sosfilt(sm,np.abs(sosfilt(filt,mod[:n])))
  # Restore the body under 250 Hz using the modulator's broadband envelope.
  vocal+=.15*sosfilt(butter(2,250,fs=SR,output='sos'),carrier)*sosfilt(sm,abs(mod[:n]))
  add(voice,unit(vocal)*env(n,.02,.08),e['t'],.12*e['v'],e['pan'])
  if count%75==0:print('Voces',count,'/',len(P['voces']),flush=True)
 save('coro-vocoders',level(voice,.15))
 # Original fixed drum kit, resampled from its documented 24 kHz sample render.
 kit={k:unit(resample_poly(np.fromfile(out/'render'/f'kit-{k}.f32',dtype=np.float32),4,3)) for k in ['kick','snare','clap','hat','rim','tomlo','spray']}
 drums=blank();duck=np.ones(N,np.float32)
 for e in P['bateria']:
  k=e['pieza'];add(drums,kit[k],e['t'],e['g']*.6,0 if k in ['kick','snare','clap'] else .32 if k=='hat' else -.28)
  if k=='kick':
   a=int(e['t']*SR);n=min(int(.16*SR),N-a);duck[a:a+n]=np.minimum(duck[a:a+n],1-.38*np.exp(-np.arange(n)/SR/.05))
 save('bateria',level(drums,.16))
 sc.png(out/'proceso'/f'03-motores-s{P["semilla"]}-{tag}.png',sc.visual('03 · modelos físicos, Rhodes, resonador vocal y cuatro vocoders'))
 # Mix by section and role. All ratios are measured on the rendered buses, not guessed gains.
 leadnames=['metal-principal','garganta-principal','sinte-solista'];lead=sum(stems[k] for k in leadnames)
 accompaniment=sum(stems[k] for k in ['rhodes','piano-preparado','cuerdas','familias-espectrales'])
 counter=stems['sax-contracanto'];voices=stems['coro-vocoders'];bass=stems['fretless'];perc=stems['bateria'];double=stems['doble-del-lead'];wet=stems['cobre-vocal']
 groups={'lead':lead,'contracanto':counter,'coro':voices,'armonia':accompaniment,'bajo':bass,'percusion':perc,'doble':double,'cobre-vocal':wet}
 mixed={k:blank() for k in groups};report=[]
 for s in P['secciones']:
  a=round(s['t']*SR);z=min(N,round(s['fin']*SR));name=s['nombre'];chamber=name=='cuerda y aire';chorus='coro' in name
  targets={'lead':.14 if not chamber else .11,'contracanto':.075 if name not in ['solos','relevos'] else .135,'coro':.14 if chorus else .075,'armonia':.09 if chamber else .07,'bajo':.09,'percusion':.115 if not chamber else .038,'doble':.038,'cobre-vocal':.045 if not chamber else .08}
  if name=='baile':targets.update(percusion=.15,armonia=.05,lead=.145)
  row=dict(seccion=name,t=s['t'],fin=s['fin'],ganancias={})
  for k,y in groups.items():
   frag=y[a:z];ar=active(frag)
   if ar<1e-7:continue
   g=min(targets[k]/ar,2.8);local=(frag*g).copy()
   if k in ['bajo','armonia','coro','doble','cobre-vocal']:local*=duck[a:z,None]**(1.3 if k=='bajo' else .7)
   # Smooth 12 ms at section edges; each edge has its own musical event anyway.
   n=min(int(.012*SR),len(local)//2);local[:n]*=np.linspace(0,1,n)[:,None];local[-n:]*=np.linspace(1,0,n)[:,None]
   mixed[k][a:z]=local;row['ganancias'][k]=float(g)
  report.append(row)
 # A small filtered room from the actual foreground; the rhythm remains dry.
 foreground=mixed['lead']+mixed['contracanto']*.5+mixed['coro']*.65
 room=blank()
 for delay,gain in [(.047,.07),(.083,.055),(.129,.04),(.193,.025)]:
  shift=int(delay*SR);room[shift:]+=sosfilt(butter(1,5000,fs=SR,output='sos'),foreground[:-shift,::-1],axis=0)*gain
 mix=sum(mixed.values())+room
 for e in P['cortes']:
  a=int(e['t']*SR);z=a+int(e['dur']*SR);n=int(.004*SR);mix[a:a+n]*=np.linspace(1,0,n)[:,None];mix[a+n:z]=0
 a=int(P['corte_final']*SR);n=int(.008*SR);mix[a:a+n]*=np.linspace(1,0,n)[:,None];mix[a+n:]=0
 assert np.isfinite(mix).all();mix*=.82/(np.max(abs(mix))+1e-12)
 writewav(out/f'mezcla-s{P["semilla"]}-{tag}.wav',mix)
 # Actual small-ensemble sketch and isolated lead are listenable artifacts, not a substitute for the composition.
 for label,y in [('lead-aislado',foreground),('boceto-lead-bajo-rhodes',lead+bass*.65+stems['rhodes']*.65)]:
  y=unit(y,.7);tmp=out/'render'/f'{label}-{tag}.wav';writewav(tmp,y);run(['ffmpeg','-v','error','-n','-i',str(tmp),'-c:a','aac','-b:a','192k',str(out/f'{label}-{tag}.m4a')])
 master=out/f'la-boca-enciende-el-cobre-s{P["semilla"]}-{tag}.m4a'
 # Two-pass true-peak-aware loudness normalization at 48 kHz before encoding.
 src=out/f'mezcla-s{P["semilla"]}-{tag}.wav';analysis=run(['ffmpeg','-hide_banner','-i',str(src),'-af','loudnorm=I=-13:TP=-1.8:LRA=8:print_format=json','-f','null','-']).stderr.decode('utf8','replace');l=json.JSONDecoder().raw_decode(analysis[analysis.rfind('{'):])[0]
 filt=f'loudnorm=I=-13:TP=-1.8:LRA=8:measured_I={l["input_i"]}:measured_TP={l["input_tp"]}:measured_LRA={l["input_lra"]}:measured_thresh={l["input_thresh"]}:offset={l["target_offset"]}:linear=true'
 run(['ffmpeg','-v','error','-n','-i',str(src),'-af',filt,'-ar','48000','-c:a','aac','-b:a','288k',str(master)])
 log=run(['ffmpeg','-hide_banner','-i',str(master),'-af','loudnorm=I=-13:TP=-1:LRA=8:print_format=json','-f','null','-']).stderr.decode('utf8','replace');l=json.JSONDecoder().raw_decode(log[log.rfind('{'):])[0]
 sc.writejson(out/'verificacion.json',dict(duracion=D,finito=True,lufs=l['input_i'],pico_verdadero=l['input_tp'],lra=l['input_lra'],sr_mezcla=SR,sr_motores=48000,sr_entrega=48000,fuentes_originales_intactas=all(sha(REPO/k)==v for k,v in json.loads((out/'receta-inicial.json').read_text('utf8'))['fuentes'].items()),sin_escucha_propia=True))
 sc.writejson(out/'mediciones-mezcla.json',dict(stems=metrics,secciones=report))
 energy=[float(abs(mix[int(i*N/1116):int((i+1)*N/1116)]).max()) for i in range(1116)]
 final=sc.visual('04 · lead al frente; contraste entre cámara, solos, coro y dembow',energy)
 sc.png(out/'proceso'/f'04-mezcla-s{P["semilla"]}-{tag}.png',final);sc.png(out/f'la-boca-enciende-el-cobre-s{P["semilla"]}-{tag}.png',final);sc.png(out/'og.png',final)
 frames=[Image.open(p).convert('RGB') for p in sorted((out/'proceso').glob('*.png'))]
 # A fixed palette prevents different frames from recolouring the score.
 palette=frames[-1].quantize(colors=96)
 indexed=[im.quantize(palette=palette) for im in frames]
 with (out/f'proceso-la-boca-s{P["semilla"]}-{tag}.gif').open('xb') as f:indexed[0].save(f,format='GIF',save_all=True,append_images=indexed[1:],duration=2100,loop=0,optimize=False)
 (out/'proceso/README.md').write_text('01: lead y contracanto antes de orquestar. 02: orquestación escrita antes de renderizar. 03: motores físicos, Rhodes y resonador vocal ya renderizados. 04: mezcla final y su energía medida. El GIF reúne estas etapas reales, 8.4 segundos. Semilla 19102743. Los PNGs no son fotogramas internos del sintetizador.\n',encoding='utf8')
 sc.writejson(out/'receta-final.json',dict(hash_ejecucion=json.loads((out/'receta-inicial.json').read_text())['hash_ejecucion'],semilla=P['semilla'],banco_sabina_sha256=sha(bank/'banco.flac'),archivos={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}))
 print('TERMINADO',master,l['input_i'],l['input_tp'],flush=True)
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
