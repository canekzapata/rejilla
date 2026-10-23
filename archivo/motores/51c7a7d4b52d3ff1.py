from pathlib import Path
import sys,json,subprocess,importlib.util,csv
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly,butter,sosfilt
from PIL import Image,ImageDraw
import partitura as sc
R=Path(__file__).resolve().parent;REPO=R.parent;SR=32000
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
sn=module('sintes_cuento',REPO/'cuento-en-siete/sintes.py')
an=module('lectura_densidad',REPO/'otro-arriba/analizar-densidad.py')
hz=lambda m:440*2**((np.asarray(m)-69)/12)
def run(args):return subprocess.run(args,check=True,capture_output=True)
def wav(path,y):
 assert np.isfinite(y).all()
 with path.open('xb') as f:wavfile.write(f,SR,y.astype(np.float32))
def env(n,a=.02,r=.08,sr=SR):
 t=np.arange(n)/sr;return np.minimum(1,t/max(1/sr,a))*np.minimum(1,(n/sr-t)/max(1/sr,r))
def active(y):
 n=SR//20;z=y if y.ndim==2 else y[:,None];z=z[:len(z)//n*n].reshape(-1,n,z.shape[1]);r=np.sqrt(np.mean(z*z,axis=(1,2)));u=r>max(float(r.max())*.05,1e-8);return float(np.sqrt(np.mean(r[u]**2))) if u.any() else 0
def level(y,target):return (y*min(target/(active(y)+1e-12),.92/(abs(y).max()+1e-12))).astype(np.float32)
def stereo(y,pan=0):
 a=(pan+1)*np.pi/4;return np.stack([y*np.cos(a),y*np.sin(a)],axis=-1).astype(np.float32)

def main(out):
 P=json.loads((out/'partitura.json').read_text('utf8'));tag=out.name.split('-')[-1];N=int(np.ceil(P['duracion']*SR));D=P['duracion'];rng=np.random.default_rng(P['semilla'])
 if not (out/'render/moduladoras.wav').exists():subprocess.run(['node',str(R/'voces.cjs'),str(out)],check=True)
 subprocess.run(['node',str(R/'fisicos.cjs'),str(out)],check=True)
 def fit(y):return np.pad(y,((0,max(0,N-len(y))),)+((0,0),)*(y.ndim-1))[:N]
 def blank():return np.zeros((N,2),np.float32)
 def add(dst,y,t,g=1,pan=0):
  i=round(t*SR);n=min(len(y),N-i)
  if i<0 or n<=0:return
  dst[i:i+n]+=stereo(y[:n]*g,pan)
 raw={k:np.fromfile(out/'render'/f'{k}.f32',dtype=np.float32) for k in ['pajaros','agua','madera']}
 sr,mods=wavfile.read(out/'render/moduladoras.wav');assert sr==48000 and mods.shape[1]==3
 # Stage 2 uses real rendered source material before carrier processing.
 source=fit(resample_poly(mods[:,0]+mods[:,1],2,3));srcimg=sc.preview(P,'02 · moduladoras PSOLA y cuerpos físicos renderizados; antes del vocoder')
 A=an.analyze(stereo(source));srcimg.paste(an.spec_image(A['db'],1450,315),(100,540));sc.png(out/'proceso'/f'02-fuentes-s{P["semilla"]}-{tag}.png',srcimg)
 stems={};metrics={}
 def save(k,y):
  y=fit(y).astype(np.float32);assert y.shape==(N,2) and np.isfinite(y).all();wav(out/'render'/f'{k}-{tag}.wav',y);stems[k]=y;metrics[k]=dict(pico=float(abs(y).max()),rms_activo=active(y))
 save('pajaros',stereo(level(fit(resample_poly(raw['pajaros'],2,3)),.16),.22))
 save('agua',stereo(level(fit(resample_poly(raw['agua'],2,3)),.095),-.15))
 save('madera',stereo(level(fit(resample_poly(raw['madera'],2,3)),.085),-.24))
 vocal={k:np.zeros(N,np.float32) for k in ['aire','cobre-luz','palos-parlantes']};cues=[]
 for f in P['frases']:
  events=f['eventos'];a=max(0,events[0]['t']-.13);z=events[-1]['t']+events[-1]['dur']+.18;i=round(a*48000);j=min(len(mods),round(z*48000));n=j-i;t=a+np.arange(n)/48000
  who=f['voz'];chan={'aire':0,'cobre-luz':1,'palo':2}[who];mod=mods[i:j,chan].astype(float)
  freq=np.full(n,float(hz(events[0]['nota'])))
  for k,e in enumerate(events):
   aa=max(0,round((e['t']-a)*48000));f0=float(hz(e['nota']));old=freq[max(0,aa-1)];freq[aa:]=f0;L=min(n-aa,720)
   if L>0:freq[aa:aa+L]=np.linspace(old,f0,L)
  ph=2*np.pi*np.cumsum(freq)/48000
  if who=='aire':
   car=np.zeros(n)
   for h in range(1,25):car+=np.sin(ph*h+.14*np.sin(t*.61+h))*(.65+.35*np.cos(t*.32+h*.7)**2)/h**1.1
  elif who=='cobre-luz':
   # Modest phase modulation at a bounded fundamental, reinforced by additive upper modes.
   index=1.2+.5*np.sin(t*.21);car=np.sin(ph+index*np.sin(ph*2))+ .3*np.sin(ph*3+.27*np.sin(t*1.1))
   for h in [2,4,5,7,9,11]:car+=np.sin(ph*h+.03*np.sin(t*.9))/h**1.05
  else:car=raw['madera'][i:j].astype(float)
  car*=env(n,.018,.06,48000)
  v=sn.vocoder(mod,car,bandas=32,suaviza=3,consonantes=.12 if who!='palo' else .22,graves=180)
  v=resample_poly(v,2,3);v=level(v,.17*(f['nivel']/.7) if who!='palo' else .10)
  key=who if who!='palo' else 'palos-parlantes';ii=round(a*SR);nn=min(len(v),N-ii);vocal[key][ii:ii+nn]+=v[:nn]
  cues.append(dict(frase=f['id'],voz=key,t=a,fin=z,portadora='madera modal golpeada' if who=='palo' else 'aditiva de modos móviles' if who=='aire' else 'fase modulada y modos aditivos'))
  print('Vocoder',f['id']+1,'/',len(P['frases']),flush=True)
 for k,pan in [('aire',-.04),('cobre-luz',.06),('palos-parlantes',-.24)]:save(k,stereo(level(vocal[k],.17 if k!='palos-parlantes' else .095),pan))
 sc.js(out/'vocoders.json',cues)
 # Halo de fase: analyze actual vocal output, then synthesize only the measured upper partials.
 halo=blank();echo=blank();measurements=[];learn=[]
 for f in P['frases']:
  if f['voz']=='palo':continue
  signal=vocal[f['voz']]
  for ei,e in enumerate(f['eventos']):
   a=round((e['t']+min(.22,e['dur']*.25))*SR);n=min(round(e['dur']*.5*SR),round(.7*SR));grain=signal[a:a+n]
   if len(grain)<100:continue
   power=abs(np.fft.rfft(grain*np.hanning(len(grain)),n=65536));freq=np.fft.rfftfreq(65536,1/SR);f0=float(hz(e['nota']));peaks=[]
   for h in [2,3,4,5,7,9,11]:
    target=f0*h
    if target>7200:continue
    ix=np.flatnonzero((freq>target*.985)&(freq<target*1.015))
    k=ix[np.argmax(power[ix])];peaks.append(dict(parcial=h,hz=float(freq[k]),magnitud=float(power[k]),esperado_hz=target))
   chosen=sorted(peaks,key=lambda p:p['magnitud'],reverse=True)[:3]
   if not chosen or chosen[0]['magnitud']<1e-7:continue
   onset=e['t']+.09;length=min(1.25,e['dur']*.68+.1);nn=round(length*SR);tt=np.arange(nn)/SR
   for k,pk in enumerate(chosen):
    weight=(pk['magnitud']/chosen[0]['magnitud'])**.5;ff=pk['hz'];phase=2*np.pi*ff*tt
    yy=(np.sin(phase+.08*np.sin(2*np.pi*.7*tt))+.17*np.sin(2*np.pi*ff*2**(2.2/1200)*tt))*env(nn,.035,.2)*np.exp(-tt/.7)
    pan=(-.45 if (ei+k)%2 else .45);add(halo,yy,onset+k*.018,.045*weight/(1+k*.4),pan)
    for delay,g in [(.061,.25),(.103,.14),(.157,.075)]:add(echo,yy,onset+k*.018+delay,.045*weight*g/(1+k*.4),-pan)
    if 17<=f['bar']<27:
     folded=ff;octaves=0
     while folded>420:folded/=2;octaves-=1
     while folded<165:folded*=2;octaves+=1
     learn.append(dict(hz=folded,fuente_hz=ff,octavas=octaves,frase=f['id'],parcial=pk['parcial']))
   measurements.append(dict(frase=f['id'],nota=ei,intervalo_fuente=[a/SR,(a+n)/SR],seleccion=chosen,t_halo=onset,duracion=length,ecos_s=[.061,.103,.157]))
 save('halo',level(halo,.065));save('ecos-halo',echo)
 sc.js(out/'halo-mediciones.json',dict(metodo='Picos reales dentro de ±1.5 % de los parciales escritos; selección de los tres con mayor magnitud, sin incluir fundamental. No se afirma extracción de formantes.',notas=measurements,aprendizaje_retorno=learn))
 print('Halo medido y ecos escritos',flush=True)
 # Walls are wide, quiet, independently articulated harmonic and subharmonic spectra.
 left=blank();right=blank();wallrecords=[]
 for e in P['paredes']:
  n=round((e['fin']-e['t'])*SR);t=np.arange(n)/SR;u=t/(n/SR);amp=env(n,2.0,2.4)
  dst=left if e['lado']=='izquierda' else right;pan=-.8 if dst is left else .8
  for j,k in enumerate(e['indices']):
   f0=P['centro_hz']*k if e['familia']=='armonica' else P['centro_hz']*16/k
   cents=e['desvio_cents']*np.sin(2*np.pi*(.035+.012*j)*t+j*.8)*np.sin(np.pi*u)
   f=f0*2**(cents/1200);phase=2*np.pi*np.cumsum(f)/SR
   wave=np.sin(phase)+.34*np.sin(phase+2*np.pi*(.13+.061*j)*t+.6)
   wave*=amp*(.7+.3*np.sin(2*np.pi*(.017+.006*j)*t+j)**2)
   # Wide spectral expansion without increasing every component at the same moment.
   if len(e['indices'])>4:wave*=np.clip((u-(j*.06))/.22,0,1)
   add(dst,wave,e['t'],e['nivel']*.048/(1+j*.19),pan)
   wallrecords.append(dict(**e,indice=k,hz_nominal=f0,batimiento_hz=.13+.061*j))
 # The return is altered by the vocal spectrum measured in the preceding wall section.
 selected=learn[::max(1,len(learn)//6)][:6]
 for j,e in enumerate(selected):
  start=sc.START[35]+j*.28;end=sc.START[47]-j*.35;n=round((end-start)*SR);t=np.arange(n)/SR
  root=e['hz'];target=min([P['centro_hz']*2,P['centro_hz']*3,P['centro_hz']*4],key=lambda f:abs(np.log2(f/root)))
  f=root*(target/root)**np.linspace(0,.65,n);wave=np.sin(2*np.pi*np.cumsum(f)/SR)*env(n,3.5,4.0)
  add(left if j%2 else right,wave,start,.018/(1+j*.25),-.6 if j%2 else .6)
 sc.js(out/'paredes-y-retorno.json',dict(cuerpos=wallrecords,frecuencias_aprendidas=selected,regreso='Las frecuencias plegadas por octavas se aproximan 65 % en log-frecuencia al parcial estable más cercano; no cambio global de tonalidad.'))
 save('pared-izquierda',left);save('pared-derecha',right)
 # Shared room, with explicit foreground priorities and no generic beat hidden under the requested percussion.
 gains={'aire':1.05,'cobre-luz':1.05,'palos-parlantes':.8,'pajaros':.82,'agua':.78,'madera':.55,'halo':.75,'ecos-halo':.75,'pared-izquierda':.9,'pared-derecha':.9}
 vocalenv=sosfilt(butter(1,8,fs=SR,output='sos'),abs(vocal['aire'])+abs(vocal['cobre-luz']));vocalenv=np.clip(vocalenv/(np.quantile(vocalenv,.96)+1e-12),0,1)
 mix=blank();room=blank()
 for k,g in gains.items():
  y=stems[k]*g
  if k.startswith('pared'):y*=(1-.28*vocalenv[:,None])
  mix+=y
  if k not in ['ecos-halo']:room+=y*(.8 if k in ['aire','cobre-luz','pajaros','palos-parlantes'] else .35)
 room=sosfilt(butter(2,[220,6500],fs=SR,btype='band',output='sos'),room,axis=0)
 for delay,g in [(.031,.075),(.057,.055),(.089,.04),(.173,.035),(.281,.022),(.419,.014)]:
  shift=round(delay*SR);mix[shift:]+=room[:-shift,::-1]*g
 fade=round(1.8*SR);cut=round(P['cierre']*SR);mix[cut:cut+fade]*=np.linspace(1,0,min(fade,N-cut))[:,None];mix[cut+fade:]=0
 mix*=.82/(abs(mix).max()+1e-12);src=out/'render'/f'mezcla-{tag}.wav';wav(src,mix)
 def loud(path):
  log=run(['ffmpeg','-hide_banner','-i',str(path),'-af','loudnorm=I=-15:TP=-1.8:LRA=10:print_format=json','-f','null','-']).stderr.decode('utf8','replace');return json.JSONDecoder().raw_decode(log[log.rfind('{'):])[0]
 def masterize(src,dst,target=-15):
  m=loud(src);af=f'loudnorm=I={target}:TP=-1.8:LRA=10:measured_I={m["input_i"]}:measured_TP={m["input_tp"]}:measured_LRA={m["input_lra"]}:measured_thresh={m["input_thresh"]}:offset={m["target_offset"]}:linear=true'
  run(['ffmpeg','-v','error','-n','-i',str(src),'-af',af,'-ar','48000','-c:a','aac','-b:a','288k',str(dst)])
 master=out/f'{out.name}.m4a';masterize(src,master)
 demo=sum(stems[k]*gains[k] for k in ['aire','cobre-luz','palos-parlantes','pajaros','halo','ecos-halo']);demo*=.75/(abs(demo).max()+1e-12);tmp=out/'render'/f'solistas-halo-{tag}.wav';wav(tmp,demo);masterize(tmp,out/f'solistas-y-halo-s{P["semilla"]}-{tag}.m4a')
 measured=loud(master);decoded=an.read_audio(master);assert np.isfinite(decoded).all() and abs(decoded).max()<1 and float(measured['input_tp'])<-.9
 assert abs(len(decoded)/SR-D)<.1 and abs(mix[-round(.3*SR):]).max()==0
 inputs=json.loads((out/'receta-inicial.json').read_text('utf8'))['fuentes'];assert all(sc.sha(REPO/k)==v for k,v in inputs.items())
 report=dict(duracion=D,lufs=measured['input_i'],pico_verdadero_db=measured['input_tp'],lra=measured['input_lra'],finito=True,cola_silenciosa=True,fuentes_intactas=True,sr_motores=48000,sr_mezcla=SR,sr_entrega=48000,metricas_stems=metrics,ganancias=gains,notas_halo_analizadas=len(measurements),parciales_que_alteran_retorno=len(selected),sin_escucha_propia=True)
 sc.js(out/'verificacion.json',report)
 # A real AAC spectrogram, sharing time with the written solos and the form.
 A=an.analyze(decoded);im=sc.preview(P,'03 · mezcla: centro vivo, paredes, claros y armónicos que responden al canto');d=ImageDraw.Draw(im);d.rectangle((0,480,1599,950),fill='#0b0b10');d.text((30,490),'Audio entregado · 40 Hz–12 kHz · brillo fijo −85 a −20 dBFS por bin',font=sc.font(19),fill='#eee8da');im.paste(an.spec_image(A['db'],1450,315),(100,535))
 for f in [50,100,250,500,1000,2000,5000,10000]:
  yy=535+315*(1-np.log(f/40)/np.log(12000/40));d.text((12,yy-7),str(f),font=sc.font(12),fill='#aaa8bc')
 for s in P['secciones']:
  xx=100+s['t']/D*1450;d.line((xx,535,xx,850),fill='#494354');d.text((xx+4,540),s['nombre'],font=sc.font(13),fill='#c6c1d5')
 for t in range(0,int(D),20):d.text((90+t/D*1450,862),f'{t//60}:{t%60:02}',font=sc.font(13),fill='#aaa8bc')
 occupied=(A['db']>-60).mean(axis=0);pts=[(100+t/D*1450,939-v*40) for t,v in zip(A['t'],occupied) if t<=D];d.line(pts,fill='#ee9abb',width=2);d.text((30,896),'Ocupación',font=sc.font(13),fill='#aaa8bc');d.text((30,918),'sobre −60 dB',font=sc.font(11),fill='#aaa8bc')
 sc.png(out/'proceso'/f'03-mezcla-s{P["semilla"]}-{tag}.png',im);sc.png(out/f'partitura-y-espectrograma-s{P["semilla"]}-{tag}.png',im)
 og=im.crop((0,430,1600,950));canvas=Image.new('RGB',(1200,630),'#0b0b10');canvas.paste(og.resize((1200,390)),(0,150));dd=ImageDraw.Draw(canvas);dd.text((25,30),'LO QUE TIEMBLA ADENTRO',font=sc.font(37),fill='#eee8da');dd.text((25,88),'Balada · pájaros, vocoders y paredes electrónicas',font=sc.font(20),fill='#aaa8bc');sc.png(out/'og.png',canvas)
 sheet=Image.new('RGB',(1600,140+len(stems)*140),'#0b0b10');d=ImageDraw.Draw(sheet);d.text((25,20),'LOS CUERPOS POR SEPARADO',font=sc.font(29),fill='#eee8da');d.text((25,65),'Ganancia nominal; misma escala −85 a −20 dBFS; antes del espacio y ducking de paredes.',font=sc.font(15),fill='#aaa8bc')
 groupstats={}
 for j,(k,y) in enumerate(stems.items()):
  B=an.analyze(y*gains[k]);yy=140+j*140;d.text((100,yy-24),k,font=sc.font(16),fill='#d5c3e7');sheet.paste(an.spec_image(B['db'],1450,106),(100,yy))
  for s in P['secciones']:
   xx=100+s['t']/D*1450;d.line((xx,yy,xx,yy+106),fill='#454050')
  groupstats[k]=float((B['db']>-60).mean());print('Gráfica',k,flush=True)
 sc.png(out/f'espectrogramas-por-cuerpo-s{P["semilla"]}-{tag}.png',sheet)
 with (out/f'densidad-s{P["semilla"]}-{tag}.csv').open('x',encoding='utf8',newline='') as f:
  writer=csv.writer(f);writer.writerow(['tiempo_s','ocupacion_sobre_menos60dbfs'])
  writer.writerows((round(float(t),4),float(v)) for t,v in zip(A['t'],occupied) if t<=D)
 sc.js(out/'densidad-secciones.json',{s['nombre']:dict(ocupacion_media=float(occupied[(A['t']>=s['t'])&(A['t']<s['fin'])].mean()),inicio=s['t'],fin=s['fin']) for s in P['secciones']})
 frames=[Image.open(x).convert('RGB').resize((1200,750)) for x in sorted((out/'proceso').glob('0[123]-*.png'))];palette=frames[-1].quantize(colors=96);frames=[x.quantize(palette=palette) for x in frames]
 gif=out/f'proceso-lo-que-tiembla-adentro-s{P["semilla"]}-{tag}.gif'
 with gif.open('xb') as f:frames[0].save(f,format='GIF',save_all=True,append_images=frames[1:],duration=2400,loop=0,optimize=False)
 contact=Image.new('RGB',(1200,750),'#0b0b10');duration=0
 with Image.open(gif) as g:
  for j in range(g.n_frames):g.seek(j);duration+=g.info['duration'];contact.paste(g.convert('RGB').resize((600,375)),((j%2)*600,(j//2)*375))
 assert duration<=10000 and gif.stat().st_size<=15*1024**2;sc.png(out/'proceso'/f'04-revision-gif-s{P["semilla"]}-{tag}.png',contact)
 with (out/'proceso/README.md').open('x',encoding='utf8') as f:f.write(f'01: partitura capturada antes de renderizar.\n02: moduladoras PSOLA y cuerpos físicos ya renderizados, espectrograma de las moduladoras; antes de vocoders, halo y paredes.\n03: audio AAC completo y ocupación de frecuencias después de componer halo, retorno y mezcla.\n04: cuadros decodificados del GIF para revisión, fuera de la animación.\n\nTres etapas reales, no pasos internos de un generador. Semilla {P["semilla"]}. GIF {duration/1000} s y {gif.stat().st_size} bytes.\n')
 sc.js(out/'receta-final.json',dict(hash_ejecucion=json.loads((out/'receta-inicial.json').read_text('utf8'))['hash_ejecucion'],semilla=P['semilla'],banco_sabina_sha256=sc.sha(REPO/'inferencia/vendor/difonos/bancos/sabina-1-b44e7fab5cee/banco.flac'),archivos={str(x.relative_to(out)):sc.sha(x) for x in out.rglob('*') if x.is_file()},gif_ms=duration,gif_bytes=gif.stat().st_size))
 print('TERMINADO',master,report['lufs'],report['pico_verdadero_db'],flush=True)
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
