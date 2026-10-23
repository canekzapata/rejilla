"""Revisión de arreglo, fraseo y espacio. No modifica la primera entrega."""
from pathlib import Path
import sys,json,hashlib,uuid,io,copy,subprocess,warnings,unicodedata
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter,sosfilt,resample_poly
from PIL import Image,ImageDraw
import producir as p
R=Path(__file__).resolve().parent;OLD=R/'otro-arriba-s19102819-8b1564cb777b';SR=p.SR
sc=p.sc;dsp=p.dsp;SEED=19102819

def clean(s):return ''.join(c for c in unicodedata.normalize('NFD',s.lower()) if c.isalpha())
def write(path,s):
 with path.open('x',encoding='utf8') as f:f.write(s)
def stage(P,label):
 sc.P=P;return sc.visual(label,True)

def init():
 old=json.loads((OLD/'partitura.json').read_text('utf8'));P=copy.deepcopy(old)
 P['revision']='v2: continuidad vocal y funciones instrumentales'
 for f in P['frases']:
  ends=np.cumsum([len(clean(w)) for w in f['letra'].split()]);n=0
  assert sum(len(clean(e['texto'])) for e in f['eventos'])==ends[-1],f['letra']
  for i,e in enumerate(f['eventos']):
   n+=len(clean(e['texto']));e['fin_palabra']=bool(n in ends)
   if i+1<len(f['eventos']):e['dur']=f['eventos'][i+1]['t']-e['t']+(-.014 if e['fin_palabra'] else .008)
 P['rhodes']=[];P['bajo']=[];P['trompeta']=[];P['piano']=[]
 sc.P=P
 def ev(k,b,beat,m,d,v=.7,**kw):sc.ev(k,b,beat,m,d,v,**kw)
 # The bass has two-bar phrases, with arrivals and occasional pickups, not a repeating three-note cell.
 for b in range(0,92,2):
  _,c=sc.chord(b);root=c[0]
  while root>45:root-=12
  q=60/sc.section(b)[3];chor='coro' in sc.section(b)[2]
  pattern=([(0,root,3.8),(4.0,root,2.6),(7.25,root-1,.55)] if chor and b%4==2 else
           [(0,root,5.3),(6.5,root+7,1.1)] if chor else
           [(0,root,6.9)] if sc.section(b)[2]=='puente' else
           [(0,root,3.4),(4.5,root+12,1.4),(6.75,root+7,.6)] if b%8==6 else [(0,root,6.5)])
  for beat,m,d in pattern:
   P['bajo'].append(dict(t=sc.at(b)+beat*q,dur=d*q,m=m,v=.72,glis=False,liso=True,b=b))
 # A chord is held through the voice; a small moving top line joins selected cadences.
 for b in range(0,92,2):
  _,c=sc.chord(b);chor='coro' in sc.section(b)[2];q=60/sc.section(b)[3]
  voicing=[c[1],c[2],c[3],c[4]]
  for j,m in enumerate(voicing):ev('rhodes',b,.12+j*.055,m,6.4 if b%4==0 else 5.7,.55,pan=-.25+j*.16)
  if chor and b%4==2:
   for j,m in enumerate([c[3]+12,c[2]+12,c[4]]):
    P['rhodes'].append(dict(t=sc.at(b)+(5.8+j*.65)*q,dur=.75*q,m=m,v=.32,pan=.15,b=b))
 # Four complete replies in rests; an independent four-bar solo; no automatic answer to every line.
 for b,notes in [(10,[69,71,73,69]),(18,[76,73,71,69]),(46,[74,73,69,67]),(54,[70,69,73,76]),(70,[77,74,73,69]),(86,[74,73,69,66])]:
  f=next(f for f in P['frases'] if f['bar']==b);e=f['eventos'][-1]
  t=e['t']+e['dur']+.08;q=60/sc.section(b)[3]
  # A reply may extend into the next bar only in an instrumental window; otherwise use the actual gap.
  nextf=next((x for x in P['frases'] if x['bar']>b),None);limit=nextf['eventos'][0]['t']-.08 if nextf else sc.START[-1]
  span=min(1.6,max(.24,limit-t));durs=np.array([.22,.18,.24,.36])*span
  for j,(m,d) in enumerate(zip(notes,durs)):
   P['trompeta'].append(dict(t=t,dur=float(d*.94),m=m,v=.52+.05*j,tipo='normal',vocal='u',frase=f'respuesta escrita {b}',b=b));t+=d
 for b,seq in [(0,[(.4,69,1.4),(2.3,66,1.2)]),(2,[(.2,67,.8),(1.2,69,1.3),(3,73,.8)]),
               (36,[(.1,74,.9),(1.2,73,.5),(1.9,69,1.5)]),(37,[(.4,71,.6),(1.2,74,1),(2.5,78,1.2)]),
               (38,[(0,76,1.4),(1.8,73,.6),(2.6,71,1)]),(39,[(.1,69,1.5),(2,67,.7),(3,66,.8)])]:
  for beat,m,d in seq:ev('trompeta',b,beat,m,d,.66,tipo='normal',vocal='u')
 # Prepared piano punctuates the form instead of doubling a pulse throughout.
 for b in [3,11,19,35,47,55,71,79,87,91]:
  c=sc.chord(b)[1]
  for j,m in enumerate([c[2]+12,c[4]+12,c[3]+12]):ev('piano',b,.25+j*1.05,m,.8+.2*j,.4,tipo='martillo')
 for k in ['bajo','rhodes','trompeta','piano']:P[k].sort(key=lambda e:e['t'])
 im=stage(P,'01 · revisión escrita: frases de bajo, acordes largos y menos respuestas')
 buf=io.BytesIO();im.save(buf,'PNG');nonce=uuid.uuid4().hex
 sources=[Path(__file__),R/'voz-v2.cjs',R/'instrumentos-v2.cjs',R/'producir.py',R/'partitura.py']
 full=hashlib.sha256(buf.getvalue()+b''.join(x.read_bytes() for x in sources)+nonce.encode()).hexdigest();tag=full[:12]
 out=R/f'otro-arriba-v2-s{SEED}-{tag}';out.mkdir()
 for name in ['render','proceso','fuentes']:(out/name).mkdir()
 sc.js(out/'partitura.json',P);sc.png(out/'proceso'/f'01-arreglo-v2-s{SEED}-{tag}.png',im)
 for i,src in enumerate(sources):(out/'fuentes'/f'{i:02d}-{src.name}').write_bytes(src.read_bytes())
 sc.js(out/'receta-inicial.json',dict(hash_ejecucion=full,nonce=nonce,semilla=SEED,imagen_sha256=hashlib.sha256(buf.getvalue()).hexdigest(),fuentes={str(x.relative_to(R.parent)):p.sha(x) for x in sources},version_anterior=str(OLD.relative_to(R.parent))))
 write(out/'CAMBIOS.md','# Otro arriba · revisión 2\n\nMisma letra, alturas principales, duración y dembow. Nuevo fraseo dinámico y unión silábica; coro con portadoras continuas y sincronizadas con frases completas. Bajo grave con frases de dos compases; Rhodes cálido con acordes sostenidos y movimientos interiores; trompeta cup con respuestas seleccionadas y solo. Piano preparado en límites de secciones. Se retiran los recortes agudos de sílaba y se reduce el sax bajo el canto. Las voces y el acompañamiento comparten reflexiones cortas.\n\nEl campo `vocal-hecha-armonia` se toma de la primera entrega sin cambiar sus muestras; su ganancia final se documenta en la mezcla. Se conservan sin cambios los motores y la primera entrega. Las etapas del proceso son capturas reales de esta revisión. No hay escucha propia ni verificación humana de comprensión.\n')
 print(out,flush=True)

def produce(out):
 P=json.loads((out/'partitura.json').read_text('utf8'));sc.P=P;N=int(np.ceil(P['duracion']*SR));tag=out.name.split('-')[-1]
 for script,target in [('voz-v2.cjs','voz-v2.wav'),('instrumentos-v2.cjs','piano.f32')]:
  if not (out/'render'/target).exists():subprocess.run(['node',str(R/script),str(out)],check=True)
 def fit(y):return np.pad(y,((0,max(0,N-len(y))),)+((0,0),)*(y.ndim-1))[:N]
 def blank():return np.zeros((N,2),np.float32)
 def add(dst,y,t,g=1,pan=0):
  a=round(t*SR);n=min(len(y),N-a)
  if a<0 or n<=0:return
  dst[a:a+n]+=p.stereo(y[:n]*g,pan)
 stems={};metrics={};inputs={}
 def save(k,y):
  assert y.shape==(N,2) and np.isfinite(y).all();y=y.astype(np.float32);p.wav(out/'render'/f'{k}-{tag}.wav',y);stems[k]=y;metrics[k]=dict(activo=dsp.active(y),pico=float(abs(y).max()))
 def prior(k):
  src=OLD/'render'/f'{k}-8b1564cb777b.wav';sr,y=wavfile.read(src);assert sr==SR;inputs[str(src.relative_to(R))]=p.sha(src);return y
 sr,voice=wavfile.read(out/'render/voz-v2.wav');assert sr==48000
 voice=fit(resample_poly(voice,2,3));voice=sosfilt(butter(2,95,fs=SR,btype='high',output='sos'),voice)
 # Preserve consonants; gentle saturation reduces vowel peaks before normalizing the phrase.
 voice=dsp.level(np.tanh(voice*1.5)/1.5,.18).astype(np.float32);save('voz-principal',p.stereo(voice))
 for k,target,pan,lp in [('trompeta',.11,.2,4800),('piano',.065,-.2,4800)]:
  y=fit(resample_poly(np.fromfile(out/'render'/f'{k}.f32',dtype=np.float32),2,3));y=sosfilt(butter(2,lp,fs=SR,output='sos'),y);save(k,p.stereo(dsp.level(y,target),pan))
 with warnings.catch_warnings():
  warnings.simplefilter('ignore',RuntimeWarning);y=p.sy.mono(P['bajo'],int(np.ceil(P['duracion']*48000)),'fretless',SEED)
 y=fit(resample_poly(y,2,3));y=sosfilt(butter(3,360,fs=SR,output='sos'),y);y=sosfilt(butter(2,33,fs=SR,btype='high',output='sos'),y);save('bajo',p.stereo(dsp.level(y,.12)))
 rh=blank()
 for e in P['rhodes']:
  n=round((e['dur']+.45)*SR);t=np.arange(n)/SR;ph=2*np.pi*p.hz(e['m'])*t
  y=(np.sin(ph)*np.exp(-t/3.3)+.2*np.sin(ph*2)*np.exp(-t/1.5)+.055*np.sin(ph*3.003)*np.exp(-t/.7))*dsp.env(n,.022,.2)
  add(rh,y,e['t'],e['v']*.13,e['pan'])
 save('rhodes',dsp.level(sosfilt(butter(2,3100,fs=SR,output='sos'),rh,axis=0),.08))
 for k in ['vocal-hecha-armonia','dembow','chelo','garganta','sinte']:save(k,prior(k))
 # Keep selected sax lines; remove the identical response under every four-bar vocal group.
 sax=prior('sax');mask=np.zeros(N,np.float32)
 for a,z in [(30,36),(62,68),(84,88)]:
  i,j=round(sc.START[a]*SR),round(sc.START[z]*SR);mask[i:j]=1;L=round(.15*SR);mask[i:i+L]*=np.linspace(0,1,L);mask[j-L:j]*=np.linspace(1,0,L)
 save('sax',sax*mask[:,None])
 energy=[float(abs(voice[int(j*N/1116):int((j+1)*N/1116)]).max()) for j in range(1116)]
 sc.png(out/'proceso'/f'02-voz-y-arreglo-s{SEED}-{tag}.png',sc.visual('02 · canto renderizado; bajo grave, Rhodes sostenido y trompeta cup',True,energy))
 # Continuous oscillator phase. Chord transitions glide over 60 ms; full phrase envelope follows the singer.
 coral=blank();events=[];edges=np.geomspace(120,12500,19);smooth=butter(1,35,fs=SR,output='sos')
 for part in range(3):
  carrier=np.zeros(N,np.float32);freq=np.full(N,p.hz(62),np.float32);gate=np.zeros(N,np.float32)
  for b in range(92):
   i,j=round(sc.START[b]*SR),round(sc.START[b+1]*SR);c=sc.chord(b)[1];m=[c[2],c[3],c[4]][part];new=p.hz(m);old=freq[i-1] if i else new;freq[i:j]=new;L=min(j-i,round(.06*SR));freq[i:i+L]=np.linspace(old,new,L)
  for f in P['frases']:
   if 'coro' not in f['seccion'] or (part==2 and f['seccion']=='coro 1'):continue
   i=max(0,round((f['eventos'][0]['t']-.12)*SR));j=min(N,round((f['eventos'][-1]['t']+f['eventos'][-1]['dur']+.1)*SR));gate[i:j]=dsp.env(j-i,.04,.09)
   events.append(dict(voz=part,frase=f['id'],t=i/SR,fin=j/SR))
  phase=2*np.pi*np.cumsum(freq)/SR
  for k in range(1,24):carrier+=(np.sin(phase*k)/k).astype(np.float32)
  carrier*=gate;y=np.zeros(N,np.float32)
  for a,b in zip(edges[:-1],edges[1:]):
   fi=butter(2,[a,b],fs=SR,btype='band',output='sos');env=sosfilt(smooth,abs(sosfilt(fi,voice)));y+=(sosfilt(fi,carrier)*env).astype(np.float32)
  add(coral,dsp.level(y,.048),0,1,[-.28,.28,.05][part]);print('Coro continuo',part+1,flush=True)
 save('coro',dsp.level(coral,.09));sc.js(out/'orquestacion-vocal.json',events)
 vocalenv=np.clip(sosfilt(butter(1,12,fs=SR,output='sos'),abs(voice))/(abs(voice).max()*.25+1e-12),0,1)
 duck=np.ones(N,np.float32)
 for e in P['bateria']:
  if e['pieza']=='kick':
   i=round(e['t']*SR);n=min(round(.16*SR),N-i);duck[i:i+n]=np.minimum(duck[i:i+n],1-.3*np.exp(-np.arange(n)/SR/.05))
 gains={'voz-principal':1.6,'trompeta':.74,'piano':.5,'bajo':.9,'rhodes':.68,'vocal-hecha-armonia':.7,'dembow':.9,'chelo':.66,'garganta':.3,'sinte':.4,'sax':.36,'coro':.52}
 mix=blank();room=blank()
 for k,g in gains.items():
  y=stems[k]*g
  if k in ['bajo','rhodes','coro','vocal-hecha-armonia']:y*=duck[:,None]**(1 if k=='bajo' else .6)
  if k in ['rhodes','sax','piano','garganta','sinte','chelo']:y*=(1-.4*vocalenv[:,None])
  mix+=y
  if k not in ['bajo','dembow']:room+=y*(1 if k in ['voz-principal','coro','trompeta'] else .45)
 room=sosfilt(butter(2,[350,5200],fs=SR,btype='band',output='sos'),room,axis=0)
 for delay,g in [(.027,.07),(.043,.052),(.071,.038),(.109,.025)]:
  shift=round(delay*SR);mix[shift:]+=room[:-shift]*g
 cut=round(P['cierre']*SR);fade=round(.3*SR);mix[cut:cut+fade]*=np.linspace(1,0,fade)[:,None];mix[cut+fade:]=0
 mix*=.82/(abs(mix).max()+1e-12);src=out/'render'/f'mezcla-v2-{tag}.wav';p.wav(src,mix)
 master=out/f'otro-arriba-v2-s{SEED}-{tag}.m4a'
 def loud(path):
  log=p.run(['ffmpeg','-hide_banner','-i',str(path),'-af','loudnorm=I=-14:TP=-1.8:LRA=8:print_format=json','-f','null','-']).stderr.decode('utf8','replace');return json.JSONDecoder().raw_decode(log[log.rfind('{'):])[0]
 m=loud(src);af=f'loudnorm=I=-14:TP=-1.8:LRA=8:measured_I={m["input_i"]}:measured_TP={m["input_tp"]}:measured_LRA={m["input_lra"]}:measured_thresh={m["input_thresh"]}:offset={m["target_offset"]}:linear=true'
 p.run(['ffmpeg','-v','error','-n','-i',str(src),'-af',af,'-ar','48000','-c:a','aac','-b:a','288k',str(master)]);measured=loud(master)
 # Short actual stems identify the source of the old three-note pulse, with equal active levels.
 sample=[]
 for k in ['rhodes','bajo','respuestas-metal']:
  y=prior(k);a=round(10*SR) if k!='respuestas-metal' else round(15*SR);clip=y[a:a+round(5*SR)];sample.extend([dsp.level(clip,.12),np.zeros((SR//2,2),np.float32)])
 demo=np.concatenate(sample);tmp=out/'render'/f'identificacion-v1-{tag}.wav';p.wav(tmp,demo)
 p.run(['ffmpeg','-v','error','-n','-i',str(tmp),'-c:a','aac','-b:a','192k',str(out/f'identificacion-v1-rhodes-bajo-trompeta-{tag}.m4a')])
 bed=out/'render'/f'vocal-hecha-armonia-{tag}.wav';oldbed=OLD/'render/vocal-hecha-armonia-8b1564cb777b.wav';assert p.sha(bed)==p.sha(oldbed)
 assert float(measured['input_tp'])<-.8 and np.isfinite(mix).all() and np.max(abs(mix[-int(.3*SR):]))==0
 sources=json.loads((out/'receta-inicial.json').read_text('utf8'))['fuentes'];assert all(p.sha(R.parent/k)==v for k,v in sources.items())
 sc.js(out/'verificacion.json',dict(duracion=P['duracion'],lufs=measured['input_i'],pico_verdadero=measured['input_tp'],lra=measured['input_lra'],finito=True,cola_silenciosa=True,sin_escucha_propia=True,fuentes_intactas=True,campo_armonico_identico_sha256=p.sha(bed),entradas_reutilizadas=inputs,ganancias=gains,metricas_stems=metrics))
 im=stage(P,'03 · mezcla v2: coro ligado al canto, espacio común y roles diferenciados')
 sc.png(out/'proceso'/f'03-mezcla-v2-s{SEED}-{tag}.png',im);sc.png(out/f'otro-arriba-v2-s{SEED}-{tag}.png',im);sc.png(out/'og.png',im)
 frames=[Image.open(x).convert('RGB') for x in sorted((out/'proceso').glob('*.png'))];palette=frames[-1].quantize(colors=96);frames=[f.quantize(palette=palette) for f in frames]
 gif=out/f'proceso-otro-arriba-v2-s{SEED}-{tag}.gif'
 with gif.open('xb') as f:frames[0].save(f,format='GIF',save_all=True,append_images=frames[1:],duration=2400,loop=0,optimize=False)
 with Image.open(gif) as g:
  duration=0;contact=Image.new('RGB',(1200,630))
  for i in range(g.n_frames):g.seek(i);duration+=g.info['duration'];contact.paste(g.convert('RGB').resize((600,315)),((i%2)*600,(i//2)*315))
 assert duration<=10000 and gif.stat().st_size<=15*1024**2;sc.png(out/'proceso'/f'04-revision-gif-{tag}.png',contact)
 write(out/'proceso/README.md',f'# Proceso real de la revisión 2\n\n1. Arreglo y fraseo nuevos, capturados antes de sintetizar.\n2. Voz, bajo, Rhodes y metal ya renderizados, antes del coro continuo y la mezcla.\n3. Mezcla terminada, después de integrar el coro y las reflexiones comunes.\n4. Hoja de revisión con cuadros decodificados del GIF; no forma parte de la animación.\n\nSemilla {SEED}; ejecución {tag}. El GIF reúne tres estados reales de trabajo; no muestra pasos internos del motor de voz. Duración {duration/1000:.1f} s; {gif.stat().st_size} bytes. No se reconstruyeron borradores de la primera versión.\n')
 sc.js(out/'receta-final.json',dict(hash_ejecucion=json.loads((out/'receta-inicial.json').read_text('utf8'))['hash_ejecucion'],semilla=SEED,archivos={str(x.relative_to(out)):p.sha(x) for x in out.rglob('*') if x.is_file()}))
 print('TERMINADO',master,measured['input_i'],measured['input_tp'],flush=True)

if __name__=='__main__':
 if len(sys.argv)==1:init()
 else:produce(Path(sys.argv[1]).resolve())
