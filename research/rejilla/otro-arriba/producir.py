from pathlib import Path
import sys,json,hashlib,subprocess,importlib.util,warnings
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter,sosfilt,resample_poly,find_peaks
from PIL import Image
R=Path(__file__).resolve().parent;REPO=R.parent;SR=32000
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
sc=module('score_arriba',R/'partitura.py');dsp=module('cobre_helpers',REPO/'la-boca-enciende-el-cobre/producir.py');sy=dsp.sy
def run(a):return subprocess.run(a,check=True,capture_output=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def wav(p,y):
 assert np.isfinite(y).all()
 with p.open('xb') as f:wavfile.write(f,SR,y.astype(np.float32))
def hz(m):return 440*2**((m-69)/12)
def stereo(y,pan=0):
 a=(pan+1)*np.pi/4;return np.stack([y*np.cos(a),y*np.sin(a)],axis=-1)
def main(out):
 P=json.loads((out/'partitura.json').read_text('utf8'));sc.P=P;D=P['duracion'];N=int(np.ceil(D*SR));tag=out.name.split('-')[-1]
 print('Render de voz PSOLA y cuerpos existentes',flush=True)
 subprocess.run(['node',str(R/'voz.cjs'),str(out)],check=True)
 subprocess.run(['node',str(R/'fisicos.cjs'),str(out)],check=True)
 subprocess.run(['node',str(REPO/'otra-vez-hasta-romper/kit.cjs'),str(out)],check=True)
 def blank():return np.zeros((N,2),np.float32)
 def add(dst,y,t,g=1,pan=0):
  a=round(t*SR);n=min(len(y),N-a)
  if a<0 or n<=0:return
  ang=(pan+1)*np.pi/4;dst[a:a+n,0]+=y[:n]*g*np.cos(ang);dst[a:a+n,1]+=y[:n]*g*np.sin(ang)
 def fit(y):return np.pad(y,((0,max(0,N-len(y))),)+((0,0),)*(y.ndim-1))[:N]
 def raw(name):return fit(resample_poly(np.fromfile(out/'render'/f'{name}.f32',dtype=np.float32),2,3))
 def level(y,target):return dsp.level(y,target)
 stems={};metrics={}
 def save(name,y):
  assert len(y)==N and np.isfinite(y).all();y=y.astype(np.float32);wav(out/'render'/f'{name}-{tag}.wav',y);stems[name]=y;metrics[name]=dict(activo=dsp.active(y),pico=float(abs(y).max()))
 sr,voice=wavfile.read(out/'render/voz.wav');assert sr==48000
 voice=fit(resample_poly(voice.mean(axis=1),2,3));voice=sosfilt(butter(2,110,fs=SR,btype='high',output='sos'),voice).astype(np.float32);voice=level(voice,.19)
 save('voz-principal',stereo(voice))
 for name,dest,target,pan in [('trompeta','respuestas-metal',.14,.2),('sax','sax',.09,-.3),('garganta','garganta',.06,.35),('piano','piano',.08,.3)]:save(dest,stereo(level(raw(name),target),pan))
 save('chelo',stereo(level(raw('chelo-arco'),.08),-.3)+stereo(level(raw('chelo-pizz'),.065),-.2))
 for name,timbre,dest,target in [('bajo','fretless','bajo',.11),('sinte','zawinul','sinte',.12)]:
  with warnings.catch_warnings():warnings.simplefilter('ignore',RuntimeWarning);y=sy.mono(P[name],int(np.ceil(D*48000)),timbre,P['semilla'])
  assert np.isfinite(y).all();save(dest,stereo(level(fit(resample_poly(y,2,3)),target)))
 rh=blank()
 for e in P['rhodes']:
  n=int((e['dur']+.4)*SR);t=np.arange(n)/SR;ph=2*np.pi*hz(e['m'])*t;y=(np.sin(ph)*np.exp(-t/1.2)+.3*np.sin(ph*2)*np.exp(-t/.4)+.15*np.sin(ph*3.003)*np.exp(-t/.25)+.1*np.sin(ph*7.01)*np.exp(-t/.1))*dsp.env(n,.002,.08);add(rh,np.tanh(y*1.2),e['t'],e['v']*.1,e['pan'])
 save('rhodes',level(rh,.085))
 # Derivation from recorded source, not from a preselected theoretical harmonic series.
 donor=next(f for f in P['frases'] if f['bar']==56)['eventos'][-1];a=round((donor['t']+donor['dur']*.22)*SR);z=round((donor['t']+donor['dur']*.82)*SR);grain=voice[a:z];assert len(grain)>100
 fftN=65536;power=abs(np.fft.rfft(grain*np.hanning(len(grain)),n=fftN));freq=np.fft.rfftfreq(fftN,1/SR);peaks,_=find_peaks(power,distance=int(70/(SR/fftN)),prominence=float(power.max())*.018);peaks=[j for j in peaks if 180<freq[j]<5000];peaks=sorted(peaks,key=lambda j:power[j],reverse=True)[:7];assert len(peaks)>=3
 measured=sorted(float(freq[j]) for j in peaks);folded=[]
 for f in measured:
  x=f;octv=0
  while x>900:x/=2;octv-=1
  while x<180:x*=2;octv+=1
  folded.append(dict(medido_hz=f,usado_hz=x,octavas=octv))
 field=blank();record=[]
 for b in range(72,88):
  q=60/sc.section(b)[3];dur=4*q+.3;aa=sc.at(b)
  for j,r in enumerate(folded):
   f=r['usado_hz'];target=min([hz(m) for m in [62,66,69,73,74,78]],key=lambda x:abs(np.log2(x/f)))
   progress=max(0,(b-79)/8);f0=f*(target/f)**progress;n=min(round(dur*SR),N-round(aa*SR));t=np.arange(n)/SR
   y=(np.sin(2*np.pi*f0*t)+.2*np.sin(2*np.pi*(f0+.5+.13*j)*t))*dsp.env(n,.18,.3)
   add(field,y,aa+j*.025,.035/(1+j*.18),(-.8 if j%2 else .8));record.append(dict(b=b,fuente_hz=f,hz=f0,destino_hz=target,voz=j))
 save('vocal-hecha-armonia',level(field,.07))
 sc.js(out/'vocal-a-armonia.json',dict(frase_donante=56,silaba=donor,intervalo_fuente=[a/SR,z/SR],fft_n=fftN,frecuencias=folded,recorrido=record,metodo='Picos de magnitud de la vocal PSOLA del coro 2; registro explícito por octavas; regreso gradual hacia notas del acorde final. No se afirma identificar formantes anatómicos.'))
 # Four separate carriers follow their own chord notes, shaped by the actual main vocal's bands.
 edges=np.geomspace(120,13800,21);filters=[butter(2,[a,b],fs=SR,btype='band',output='sos') for a,b in zip(edges[:-1],edges[1:])];sm=butter(1,30,fs=SR,output='sos');coral=blank();vevents=[]
 for part in range(4):
  carrier=np.zeros(N,np.float32)
  for b in list(range(20,36))+list(range(56,72))+list(range(80,88)):
   _,c=sc.chord(b);m=[c[4],c[3],c[2],c[1]-12][part];t0=sc.at(b,[0,.2,.5,.1][part]);dur=[1.9,1.6,1.8,2.1][part]*60/sc.section(b)[3];n=round(dur*SR);t=np.arange(n)/SR;f=hz(m);ph=2*np.pi*f*t
   wave=(sum(np.sin(ph*k)/k for k in range(1,min(32,int(14000/f))))) if part%2==0 else np.sin(ph+2*np.sin(ph*2.003)*np.exp(-t/1.3))
   i=round(t0*SR);nn=min(n,N-i);carrier[i:i+nn]+=wave[:nn]*dsp.env(n,.02,.08)[:nn]
   vevents.append(dict(voz=part,b=b,t=t0,dur=dur,m=m))
  y=np.zeros(N,np.float32)
  for fi in filters:y+=(sosfilt(fi,carrier)*sosfilt(sm,abs(sosfilt(fi,voice)))).astype(np.float32)
  y+=.12*sosfilt(butter(2,250,fs=SR,output='sos'),carrier)*sosfilt(sm,abs(voice));add(coral,level(y,.055),0,1,[-.65,.65,-.32,.32][part]);print('Vocoder',part+1,'de 4',flush=True)
 save('coro',level(coral,.1));sc.js(out/'orquestacion-vocal.json',vevents)
 chops=blank()
 for f in P['frases']:
  if 'coro' not in f['seccion']:continue
  e=f['eventos'][-1];i=round(e['t']*SR);n=round(e['dur']*SR);yy=resample_poly(voice[i:i+n],2,3);add(chops,yy*dsp.env(len(yy),.008,.04),e['t']+.13,.2,(-.55 if f['bar']%4 else .55))
 save('dobles-agudos',chops)
 kit={k:dsp.unit(resample_poly(np.fromfile(out/'render'/f'kit-{k}.f32',dtype=np.float32),4,3)) for k in ['kick','snare','hat','rim','clap','spray','tomlo']};drums=blank();duck=np.ones(N,np.float32)
 for e in P['bateria']:
  k=e['pieza'];add(drums,kit[k],e['t'],e['g']*.55,0 if k in ['kick','snare','clap'] else .3 if k=='hat' else -.25)
  if k=='kick':
   i=round(e['t']*SR);n=min(int(.16*SR),N-i);duck[i:i+n]=np.minimum(duck[i:i+n],1-.38*np.exp(-np.arange(n)/SR/.05))
 save('dembow',level(drums,.14));energy=[float(abs(voice[int(j*N/1116):int((j+1)*N/1116)]).max()) for j in range(1116)];sc.png(out/'proceso'/f'03-voz-y-vocal-s{P["semilla"]}-{tag}.png',sc.visual('03 · voz PSOLA; una vocal real produce la armonía del puente',True,energy))
 # Voice stays in front of the band; breathing room is driven by the actual syllabic envelope.
 vocalenv=sosfilt(butter(1,12,fs=SR,output='sos'),abs(voice));vocalenv=np.clip(vocalenv/(float(vocalenv.max())*.25+1e-12),0,1)
 backing=blank();mix=stems['voz-principal']*1.6;gainmap={'respuestas-metal':.65,'sax':.55,'garganta':.5,'piano':.7,'chelo':.75,'bajo':.8,'sinte':.7,'rhodes':.65,'vocal-hecha-armonia':.7,'coro':.65,'dobles-agudos':.8,'dembow':.9}
 for k,g in gainmap.items():
  y=stems[k]*g
  if k in ['bajo','rhodes','coro','vocal-hecha-armonia']:y*=duck[:,None]**(1.2 if k=='bajo' else .6)
  if k in ['rhodes','sax','piano','garganta','vocal-hecha-armonia','chelo']:y*=(1-.32*vocalenv[:,None])
  backing+=y
 mix+=backing
 for delay,g in [(.047,.065),(.089,.045),(.143,.028)]:
  shift=round(delay*SR);mix[shift:]+=sosfilt(butter(1,4500,fs=SR,output='sos'),stems['voz-principal'][:-shift],axis=0)*g
 cut=round(P['cierre']*SR);fade=min(int(.3*SR),N-cut);mix[cut:cut+fade]*=np.linspace(1,0,fade)[:,None];mix[cut+fade:]=0
 assert np.isfinite(mix).all();mix*=.82/(float(abs(mix).max())+1e-12);src=out/f'mezcla-s{P["semilla"]}-{tag}.wav';wav(src,mix)
 for name,y in [('voz-principal',stems['voz-principal']),('boceto-voz-rhodes',stems['voz-principal']*1.6+stems['rhodes']*.6+stems['bajo']*.6)]:
  tmp=out/'render'/f'{name}-escucha-{tag}.wav';wav(tmp,dsp.unit(y,.7));run(['ffmpeg','-v','error','-n','-i',str(tmp),'-c:a','aac','-b:a','192k',str(out/f'{name}-{tag}.m4a')])
 master=out/f'otro-arriba-s{P["semilla"]}-{tag}.m4a';log=run(['ffmpeg','-hide_banner','-i',str(src),'-af','loudnorm=I=-14:TP=-1.8:LRA=8:print_format=json','-f','null','-']).stderr.decode('utf8','replace');m=json.JSONDecoder().raw_decode(log[log.rfind('{'):])[0];af=f'loudnorm=I=-14:TP=-1.8:LRA=8:measured_I={m["input_i"]}:measured_TP={m["input_tp"]}:measured_LRA={m["input_lra"]}:measured_thresh={m["input_thresh"]}:offset={m["target_offset"]}:linear=true';run(['ffmpeg','-v','error','-n','-i',str(src),'-af',af,'-ar','48000','-c:a','aac','-b:a','288k',str(master)])
 log=run(['ffmpeg','-hide_banner','-i',str(master),'-af','loudnorm=I=-14:TP=-1:LRA=8:print_format=json','-f','null','-']).stderr.decode('utf8','replace');m=json.JSONDecoder().raw_decode(log[log.rfind('{'):])[0]
 sc.js(out/'verificacion.json',dict(duracion=D,finito=True,lufs=m['input_i'],pico_verdadero=m['input_tp'],lra=m['input_lra'],sr_motores=48000,sr_mezcla=SR,sr_entrega=48000,fuentes_originales_intactas=all(sha(REPO/k)==v for k,v in json.loads((out/'receta-inicial.json').read_text('utf8'))['fuentes'].items()),sin_escucha_propia=True,metricas_stems=metrics))
 energy=[float(abs(mix[int(j*N/1116):int((j+1)*N/1116)]).max()) for j in range(1116)];im=sc.visual('04 · voz al frente, coro, metal y retorno de la vocal transformada',True,energy);sc.png(out/'proceso'/f'04-mezcla-s{P["semilla"]}-{tag}.png',im);sc.png(out/f'otro-arriba-s{P["semilla"]}-{tag}.png',im);sc.png(out/'og.png',im)
 frames=[Image.open(p).convert('RGB') for p in sorted((out/'proceso').glob('*.png'))];palette=frames[-1].quantize(colors=96);frames=[f.quantize(palette=palette) for f in frames]
 with (out/f'proceso-otro-arriba-s{P["semilla"]}-{tag}.gif').open('xb') as f:frames[0].save(f,format='GIF',save_all=True,append_images=frames[1:],duration=2100,loop=0,optimize=False)
 with (out/'proceso/README.md').open('x',encoding='utf8') as f:f.write('01: melodía y acentos; 02: orquestación escrita antes de sintetizar; 03: voz PSOLA y análisis real de una vocal para generar el campo del puente; 04: mezcla y energía. Cuatro etapas reales, GIF de 8.4 s. Semilla 19102819. No representa pasos internos de síntesis.\n')
 sc.js(out/'receta-final.json',dict(hash_ejecucion=json.loads((out/'receta-inicial.json').read_text('utf8'))['hash_ejecucion'],semilla=P['semilla'],sabina_sha256=sha(REPO/'inferencia/vendor/difonos/bancos/sabina-1-b44e7fab5cee/banco.flac'),archivos={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()}))
 print('TERMINADO',master,m['input_i'],m['input_tp'],flush=True)
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
