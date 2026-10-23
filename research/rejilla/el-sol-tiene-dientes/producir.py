from pathlib import Path
import json,sys,subprocess,importlib.util,warnings,csv
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly,butter,sosfilt
from PIL import Image,ImageDraw
import partitura as sc
R=Path(__file__).resolve().parent;REPO=R.parent;SR=32000
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
shared=module('tiembla_helpers',REPO/'lo-que-tiembla-adentro/producir.py');sn=shared.sn;an=shared.an
sy=module('electricos',REPO/'lo-que-tapa-la-traspuesta/sintes2.py')
env=shared.env;level=shared.level;stereo=shared.stereo;wav=shared.wav;active=shared.active;run=shared.run;hz=shared.hz

def main(out):
 P=json.loads((out/'partitura.json').read_text('utf8'));tag=out.name.split('-')[-1];D=P['duracion'];N=int(np.ceil(D*SR));rng=np.random.default_rng(P['semilla'])
 if not(out/'render/moduladoras.wav').exists():subprocess.run(['node',str(REPO/'lo-que-tiembla-adentro/voces.cjs'),str(out)],check=True)
 if not(out/'render/sax.f32').exists():subprocess.run(['node',str(R/'fisicos.cjs'),str(out)],check=True)
 if not(out/'render/kit-tomlo.f32').exists():subprocess.run(['node',str(REPO/'otra-vez-hasta-romper/kit.cjs'),str(out)],check=True)
 def fit(y):return np.pad(y,((0,max(0,N-len(y))),)+((0,0),)*(y.ndim-1))[:N]
 def blank():return np.zeros((N,2),np.float32)
 def add(dst,y,t,g=1,pan=0):
  i=round(t*SR);n=min(len(y),N-i)
  if i<0 or n<=0:return
  dst[i:i+n]+=stereo(y[:n]*g,pan)
 stems={};metrics={}
 def save(k,y):
  y=fit(y).astype(np.float32);assert y.shape==(N,2) and np.isfinite(y).all();wav(out/'render'/f'{k}-{tag}.wav',y);stems[k]=y;metrics[k]=dict(pico=float(abs(y).max()),activo=active(y))
 sr,mods=wavfile.read(out/'render/moduladoras.wav');assert sr==48000 and mods.shape[1]==3
 im=sc.preview(P,'02 · voz PSOLA, sax y kit ya renderizados; antes del arreglo electrónico');A=an.analyze(stereo(fit(resample_poly(mods[:,0],2,3))));im.paste(an.spec_image(A['db'],1660,330),(95,575));sc.png(out/'proceso'/f'02-fuentes-s{P["semilla"]}-{tag}.png',im)
 voices={k:np.zeros(N,np.float32) for k in ['voz','coro','susurros']};cues=[]
 for f in P['frases']:
  es=f['eventos'];a=max(0,es[0]['t']-.12);z=es[-1]['t']+es[-1]['dur']+.14;i=round(a*48000);j=min(len(mods),round(z*48000));n=j-i;t=a+np.arange(n)/48000
  who={'aire':'voz','cobre-luz':'coro','palo':'susurros'}[f['voz']];c={'voz':0,'coro':1,'susurros':2}[who];mod=mods[i:j,c].astype(float)
  if who=='susurros':
   y=resample_poly(mod,2,3);y=sosfilt(butter(2,[600,9000],fs=SR,btype='band',output='sos'),y);y=level(y,.07)
  else:
   freq=np.full(n,float(hz(es[0]['nota'])));amp=np.ones(n)
   for k,e in enumerate(es):
    aa=max(0,round((e['t']-a)*48000));new=float(hz(e['nota']));old=freq[max(0,aa-1)];freq[aa:]=new;L=min(n-aa,570)
    if L>0:freq[aa:aa+L]=np.linspace(old,new,L)
   ph=2*np.pi*np.cumsum(freq)/48000;carrier=np.zeros(n)
   if who=='voz':
    for h in range(1,19):carrier+=np.sin(ph*h+.1*np.sin(t*.8+h))*(.7+.3*np.sin(t*.47+h*.5)**2)/h**.92
   else:
    # Written chord changes share the modulator's breath, without chopping the carriers in mid-word.
    for k,e in enumerate(es):
     aa=max(0,round((e['t']-a)*48000));zz=round((es[k+1]['t']-a)*48000) if k+1<len(es) else n;tt=np.arange(zz-aa)/48000
     chord=e.get('voicing',[e['nota'],e['nota']+4,e['nota']+7]);vv=np.zeros(zz-aa)
     for v,m in enumerate(chord):
      for det in [-5,5]:
       ff=float(hz(m))*2**(det/1200)
       for h in range(1,min(20,int(12000/ff))):vv+=np.sin(2*np.pi*ff*h*tt+.6*v)/(h*len(chord)*2)
     carrier[aa:zz]+=vv*env(len(vv),.018,.035,48000)
   carrier*=env(n,.015,.05,48000);y=sn.vocoder(mod,carrier,bandas=32,suaviza=2,consonantes=.22,graves=200)
   y=resample_poly(y,2,3);y=level(y,.18*f['nivel']/.76 if who=='voz' else .115*f['nivel']/.58)
   if who=='voz':y+=level(resample_poly(mod,2,3),.022)
  ii=round(a*SR);nn=min(N-ii,len(y));voices[who][ii:ii+nn]+=y[:nn];cues.append(dict(frase=f['id'],grupo=who,t=a,fin=z));print('Canto',f['id']+1,'/',len(P['frases']),flush=True)
 save('voz',stereo(level(voices['voz'],.18)))
 choir=stereo(level(voices['coro'],.12),-.12);shift=round(.006*SR);choir[shift:,1]+=.2*voices['coro'][:-shift];save('coro',choir)
 save('susurros',stereo(voices['susurros']))
 sc.js(out/'voces-y-portadoras.json',dict(frases=cues,principal='Moduladora PSOLA + vocoder de 32 bandas; portadora aditiva, refuerzo seco leve.',coro='Otra moduladora y acordes escritos; transición por eventos propios.'))
 sax=fit(resample_poly(np.fromfile(out/'render/sax.f32',dtype=np.float32),2,3));save('sax',stereo(level(sax,.14),-.18))
 for key,timbre,target in [('sinte','zawinul',.14),('fretless','fretless',.1)]:
  with warnings.catch_warnings():warnings.simplefilter('ignore',RuntimeWarning);y=sy.mono(P[key],int(np.ceil(D*48000)),timbre,P['semilla'])
  y=fit(resample_poly(y,2,3))
  if key=='fretless':y=sosfilt(butter(3,420,fs=SR,output='sos'),y)
  save(key,stereo(level(y,target),.23 if key=='sinte' else 0))
 # A warm modal electric piano: upper voice moves while the lower chord holds.
 rh=blank()
 for e in P['rhodes']:
  n=round((e['dur']+.35)*SR);t=np.arange(n)/SR;ph=2*np.pi*float(hz(e['m']))*t
  y=(np.sin(ph)*np.exp(-t/2.4)+.2*np.sin(ph*2)*np.exp(-t/.85)+.05*np.sin(ph*3.003)*np.exp(-t/.35))*env(n,.008,.12);add(rh,y,e['t'],e['v']*.1,e['pan'])
 save('rhodes',level(rh,.085))
 # Modal toy, plucked subject and wooden counter-subject stay separate in the saved stems.
 for key,target,ratios,decay in [('juguete',.08,[1,2.003,3.98,6.05],.42),('pluck',.11,[1,2,3,4,5,6],.16),('marimba',.105,[1,3.98,10.1],.28)]:
  dst=blank()
  for e in P[key]:
   n=round((e['dur']+.2)*SR);t=np.arange(n)/SR;f0=float(hz(e['m']));y=np.zeros(n)
   for j,r in enumerate(ratios):
    if f0*r<12000:y+=np.sin(2*np.pi*f0*r*t+r*.2)*np.exp(-t/(decay/(1+j*.3)))/(1+j*.7)
   y*=env(n,.0015,.07);add(dst,y,e['t'],e['v']*.17,e.get('pan',-.2 if key=='pluck' else .25))
  save(key,level(dst,target))
 # Bass is synthesized at 64 kHz and downsampled after saturation; the clean fundamental is retained.
 bass=blank();bassrecords=[]
 for e in P['bajo']:
  dur=e['dur']+.09;n=round(dur*64000);t=np.arange(n)/64000;f0=float(hz(e['m']));ph=2*np.pi*f0*t
  rate=e['rate']/P['cuarto_s'];u=.5+.5*np.sin(2*np.pi*rate*t-.8);fc=160+(2300 if e['growl'] else 420)*u**2;body=np.zeros(n)
  for h in range(2,min(90,int(12000/f0))):
   fk=f0*h;lp=1/np.sqrt(1+(fk/fc)**4);form=1+1.6*np.exp(-.5*(np.log(fk/(500+900*u))/.3)**2)
   body+=np.sin(ph*h+.13*h)*lp*form/h
  wave=.7*np.sin(ph)+.26*np.tanh(2.0*body);wave*=env(n,.009,.1,64000)*e['v'];wave=resample_poly(wave,1,2);add(bass,wave,e['t'],.18)
  bassrecords.append(dict(t=e['t'],dur=e['dur'],fundamental_hz=f0,lfo_hz=rate,growl=e['growl']))
 save('bajo-dub',level(bass,.15));sc.js(out/'bajo-dub.json',dict(sr_interno=64000,notas=bassrecords))
 kit={k:resample_poly(np.fromfile(out/'render'/f'kit-{k}.f32',dtype=np.float32),4,3) for k in ['kick','snare','rim','clap','hat','openhat','spray','tomlo']}
 for k in kit:kit[k]*=.9/(abs(kit[k]).max()+1e-12)
 drums=blank();duck=np.ones(N,np.float32)
 for e in P['bateria']:
  add(drums,kit[e['pieza']],e['t'],e['g']*.43,e['pan'])
  if e['pieza']=='kick':
   i=round(e['t']*SR);n=min(N-i,round(.17*SR));duck[i:i+n]=np.minimum(duck[i:i+n],1-.46*np.exp(-np.arange(n)/SR/.055))
 save('bateria',level(drums,.16))
 # The distant interlude is made from our actual sung chorus, not an external artist's recording.
 memory=blank();record=[];donors=[next(f for f in P['frases'] if f['bar']==b and f['voz']=='aire') for b in [24,28,32,36]]
 for j,b in enumerate([96,98,100,102]):
  f=donors[j];e=f['eventos'][-1];a=round((e['t']+.04)*SR);z=round((e['t']+e['dur'])*SR);grain=voices['voz'][a:z].copy();assert len(grain)>100
  if j%2:grain=grain[::-1]
  stretch=[2,3,2,4][j];grain=resample_poly(grain,stretch,1);grain*=env(len(grain),.06,.12)
  for k in range(4):add(memory,grain,sc.at(b,.2)+k*.29,.32/(1+k*.9),(-.72 if (j+k)%2 else .72))
  record.append(dict(b=b,frase_fuente=f['id'],intervalo_fuente=[a/SR,z/SR],reversa=bool(j%2),lectura_lenta=stretch,ecos_s=[0,.29,.58,.87]))
 save('memoria-espacial',level(sosfilt(butter(2,[220,7000],fs=SR,btype='band',output='sos'),memory,axis=0),.075));sc.js(out/'memoria-del-estribillo.json',record)
 # Put the main line and percussion forward; give the band common early reflections.
 gains={'voz':1.35,'coro':.68,'susurros':.7,'sax':.86,'sinte':.8,'fretless':.9,'rhodes':.7,'juguete':.7,'pluck':.8,'marimba':.8,'bajo-dub':.92,'bateria':1.05,'memoria-espacial':.9}
 ve=sosfilt(butter(1,14,fs=SR,output='sos'),abs(voices['voz']));ve=np.clip(ve/(np.quantile(ve,.96)+1e-12),0,1);mix=blank();room=blank()
 for k,g in gains.items():
  y=stems[k]*g
  if k in ['bajo-dub','rhodes','coro']:y*=duck[:,None]**(1.2 if k=='bajo-dub' else .65)
  if k in ['rhodes','juguete','coro','sinte']:y*=(1-.28*ve[:,None])
  mix+=y
  if k not in ['bajo-dub','fretless','bateria','memoria-espacial']:room+=y
 room=sosfilt(butter(2,[320,5500],fs=SR,btype='band',output='sos'),room,axis=0)
 for delay,g in [(.023,.055),(.047,.04),(.083,.028),(.137,.018)]:
  shift=round(delay*SR);mix[shift:]+=room[:-shift]*g
 # A real two-beat silence before the elevated final chorus, including effect tails.
 a=round(sc.at(103,2.5)*SR);z=round(sc.at(104)*SR);L=round(.008*SR);mix[a-L:a]*=np.linspace(1,0,L)[:,None];mix[a:z]=0
 cut=round(P['cierre']*SR);fade=round(1.6*SR);mix[cut:cut+fade]*=np.linspace(1,0,min(fade,N-cut))[:,None];mix[cut+fade:]=0
 mix*=.82/(abs(mix).max()+1e-12);src=out/'render'/f'mezcla-{tag}.wav';wav(src,mix)
 def loud(path):
  log=run(['ffmpeg','-hide_banner','-i',str(path),'-af','loudnorm=I=-13.5:TP=-1.8:LRA=9:print_format=json','-f','null','-']).stderr.decode('utf8','replace');return json.JSONDecoder().raw_decode(log[log.rfind('{'):])[0]
 def masterize(src,dst):
  m=loud(src);af=f'loudnorm=I=-13.5:TP=-1.8:LRA=9:measured_I={m["input_i"]}:measured_TP={m["input_tp"]}:measured_LRA={m["input_lra"]}:measured_thresh={m["input_thresh"]}:offset={m["target_offset"]}:linear=true'
  run(['ffmpeg','-v','error','-n','-i',str(src),'-af',af,'-ar','48000','-c:a','aac','-b:a','288k',str(dst)])
 master=out/(out.name+'.m4a');masterize(src,master)
 front=sum(stems[k]*gains[k] for k in ['voz','coro','sax','sinte','pluck','marimba','juguete']);front*=.75/(abs(front).max()+1e-12);tmp=out/'render'/f'frente-{tag}.wav';wav(tmp,front);masterize(tmp,out/f'voces-y-dialogo-s{P["semilla"]}-{tag}.m4a')
 m=loud(master);decoded=an.read_audio(master);assert np.isfinite(decoded).all() and abs(decoded).max()<1 and float(m['input_tp'])<-.8 and abs(len(decoded)/SR-D)<.1
 inputs=json.loads((out/'receta-inicial.json').read_text('utf8'))['fuentes'];assert all(sc.sha(REPO/k)==v for k,v in inputs.items());assert abs(mix[a:z]).max()==0 and abs(mix[-round(.4*SR):]).max()==0
 sc.js(out/'verificacion.json',dict(duracion=D,lufs=m['input_i'],pico_verdadero_db=m['input_tp'],lra=m['input_lra'],finito=True,silencio_antes_coro=[a/SR,z/SR],cola_silenciosa=True,fuentes_intactas=True,ganancias=gains,metricas_stems=metrics,sr_mezcla=SR,sr_motores=48000,sr_bajo=64000,sr_entrega=48000,sin_escucha_propia=True))
 A=an.analyze(decoded);occ=(A['db']>-60).mean(axis=0);im=sc.preview(P,'03 · mezcla: coro pop, bajo dubstep, invención, diálogo y silencio antes del regreso');d=ImageDraw.Draw(im);d.rectangle((0,510,1799,1040),fill='#0b0b10');d.text((32,520),'Audio AAC real · 40 Hz–12 kHz · brillo fijo −85 a −20 dBFS por bin',font=sc.font(21),fill='#f1e7d5');im.paste(an.spec_image(A['db'],1660,340),(95,567))
 for f in [50,100,250,500,1000,2000,5000,10000]:
  yy=567+340*(1-np.log(f/40)/np.log(12000/40));d.text((12,yy-7),str(f),font=sc.font(12),fill='#aaa8bc')
 for s in P['secciones']:
  xx=95+s['t']/D*1660;d.line((xx,567,xx,907),fill='#494354');d.text((xx+4,572),s['nombre'].split(' · ')[0],font=sc.font(13),fill='#ccc1dd')
 for t in range(0,int(D),20):d.text((85+t/D*1660,919),f'{t//60}:{t%60:02}',font=sc.font(13),fill='#aaa8bc')
 pts=[(95+t/D*1660,1025-v*65) for t,v in zip(A['t'],occ) if t<=D];d.line(pts,fill='#f4a2d1',width=2);d.text((32,960),'Ocupación',font=sc.font(13),fill='#aaa8bc');d.text((32,980),'sobre −60 dB',font=sc.font(11),fill='#aaa8bc')
 sc.png(out/f'partitura-y-espectrograma-s{P["semilla"]}-{tag}.png',im);sc.png(out/'proceso'/f'03-mezcla-s{P["semilla"]}-{tag}.png',im)
 og=Image.new('RGB',(1200,630),'#0b0b10');og.paste(im.crop((0,560,1800,1035)).resize((1200,317)),(0,205));dd=ImageDraw.Draw(og);dd.text((25,35),'EL SOL TIENE DIENTES',font=sc.font(40),fill='#f1e7d5');dd.text((25,105),'Pop, voces, contrapunto y bajo que cambia de forma',font=sc.font(20),fill='#c5b7df');sc.png(out/'og.png',og)
 sheet=Image.new('RGB',(1800,145+len(stems)*135),'#0b0b10');d=ImageDraw.Draw(sheet);d.text((28,18),'DENSIDAD POR CUERPO',font=sc.font(31),fill='#f1e7d5');d.text((28,70),'Ganancias nominales, antes del ducking y espacio. Escala fija −85 a −20 dBFS · 40 Hz–12 kHz.',font=sc.font(17),fill='#b7aac8')
 for j,(k,y) in enumerate(stems.items()):
  B=an.analyze(y*gains[k]);yy=145+j*135;d.text((95,yy-24),k,font=sc.font(16),fill='#d4b9e2');sheet.paste(an.spec_image(B['db'],1660,102),(95,yy))
  for s in P['secciones']:
   xx=95+s['t']/D*1660;d.line((xx,yy,xx,yy+102),fill='#3d384a')
  print('Gráfica',k,flush=True)
 sc.png(out/f'espectrogramas-por-cuerpo-s{P["semilla"]}-{tag}.png',sheet)
 with(out/f'densidad-s{P["semilla"]}-{tag}.csv').open('x',encoding='utf8',newline='') as f:
  writer=csv.writer(f);writer.writerow(['tiempo_s','ocupacion_sobre_menos60dbfs']);writer.writerows((round(float(t),4),float(v)) for t,v in zip(A['t'],occ) if t<=D)
 sc.js(out/'densidad-secciones.json',{s['nombre']:dict(inicio=s['t'],fin=s['fin'],ocupacion_media=float(occ[(A['t']>=s['t'])&(A['t']<s['fin'])].mean())) for s in P['secciones']})
 frames=[Image.open(p).convert('RGB').resize((1200,733)) for p in sorted((out/'proceso').glob('0[123]-*.png'))];palette=frames[-1].quantize(colors=96);frames=[x.quantize(palette=palette) for x in frames]
 gif=out/f'proceso-el-sol-tiene-dientes-s{P["semilla"]}-{tag}.gif'
 with gif.open('xb') as f:frames[0].save(f,format='GIF',save_all=True,append_images=frames[1:],duration=2400,loop=0,optimize=False)
 contact=Image.new('RGB',(1200,734),'#0b0b10');duration=0
 with Image.open(gif) as g:
  for i in range(g.n_frames):g.seek(i);duration+=g.info['duration'];contact.paste(g.convert('RGB').resize((600,367)),((i%2)*600,(i//2)*367))
 assert duration<=10000 and gif.stat().st_size<=15*1024**2;sc.png(out/'proceso'/f'04-revision-gif-s{P["semilla"]}-{tag}.png',contact)
 with(out/'proceso/README.md').open('x',encoding='utf8') as f:f.write(f'01: escritura antes del render; gancho, contrapunto y relevos.\n02: PSOLA/sax/kit renderizados; espectrograma de la moduladora principal antes del vocoder y arreglo.\n03: AAC real y ocupación después de mezcla; memoria espacial derivada de nuestras voces.\n04: hoja con cuadros decodificados del GIF, fuera de la animación.\n\nEtapas reales; no pasos internos de síntesis. Semilla {P["semilla"]}. GIF {duration/1000} s, {gif.stat().st_size} bytes.\n')
 sc.js(out/'receta-final.json',dict(hash_ejecucion=json.loads((out/'receta-inicial.json').read_text('utf8'))['hash_ejecucion'],semilla=P['semilla'],archivos={str(p.relative_to(out)):sc.sha(p) for p in out.rglob('*') if p.is_file()},banco_sabina_sha256=sc.sha(REPO/'inferencia/vendor/difonos/bancos/sabina-1-b44e7fab5cee/banco.flac'),gif_ms=duration,gif_bytes=gif.stat().st_size))
 print('TERMINADO',master,m['input_i'],m['input_tp'],flush=True)
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
