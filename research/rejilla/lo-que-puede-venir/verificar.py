"""Comprobaciones sobre render: altura abierta, prosodia, memoria y evidencia visual."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
from scipy.io import wavfile
from scipy.signal import correlate,butter,sosfilt
from PIL import Image
out=Path(sys.argv[1]);repo=out.parent.parent;tag=out.name.split('-')[-1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
P=json.loads((out/'partitura.json').read_text('utf8'));rec=json.loads((out/'receta-inicial.json').read_text('utf8'))
originales={n:sha(repo/n)==s for n,s in rec['fuentes'].items()};assert all(originales.values())
sr,y=wavfile.read(out/'render/voz.wav');y=y.mean(axis=1)
def yin(x,s):
 x=x.astype(float);x-=x.mean();maxlag=int(s/85);minlag=int(s/1100);w=len(x)-maxlag-1
 if w<100 or np.mean(x*x)<1e-10:return None
 ac=correlate(x,x[:w],mode='valid',method='fft')[:maxlag+1];en=np.r_[0,np.cumsum(x*x)];tau=np.arange(maxlag+1)
 diff=np.maximum(0,en[w]+en[w+tau]-en[tau]-2*ac);cm=np.ones_like(diff);cm[1:]=diff[1:]*tau[1:]/np.maximum(np.cumsum(diff[1:]),1e-15)
 below=np.flatnonzero(cm[minlag:]<.2)
 if not len(below):return None
 j=minlag+int(below[0])
 while j<maxlag-1 and cm[j+1]<cm[j]:j+=1
 if j>=maxlag:return None
 den=cm[j-1]-2*cm[j]+cm[j+1];delta=.5*(cm[j-1]-cm[j+1])/den if abs(den)>1e-12 else 0
 return float(s/(j+delta))
results=[];patterns=[]
for f in P['frases']:
 patterns.append(tuple(round(e['dur'],4) for e in f['eventos']))
 for e in f['eventos']:
  if e['dur']<.19:continue
  center=e['t']+e['dur']*.62;half=min(.08,e['dur']*.27);a=int((center-half)*sr);b=int((center+half)*sr);pitch=yin(y[a:b:3],sr/3)
  err=float(1200*np.log2(pitch/(440*2**((e['nota']-69)/12)))) if pitch else None
  results.append(dict(t=e['t'],texto=e['texto'],nota=e['nota'],Hz=pitch,cents=err))
vals=[abs(e['cents']) for e in results if e['cents'] is not None]
report=dict(metodo='YIN 85–1100 Hz, sin restringir a la nota; sólo sílabas >=190 ms; ventana dentro de la vocal programada. No prueba inteligibilidad.',analizadas=len(results),estables=len(vals),mediana_cents=float(np.median(vals)),p95_cents=float(np.percentile(vals,95)),dentro_50=int(sum(v<50 for v in vals)),frases=len(P['frases']),patrones_duracion=len(set(patterns)),detalle=results)
with (out/'verificacion-alturas.json').open('x',encoding='utf8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
# Audible energy of the donor before the learned note; no claim of cognitive learning.
sr,bird=wavfile.read(out/'render/pajaro.wav');mem=P['memoria'];a=int(mem['t']*sr);b=int(mem['disponible']*sr)
assert mem['disponible']<mem['t_receptor'] and np.sqrt(np.mean(bird[a:b]**2))>1e-5
sr,mix=wavfile.read(out/'render/mezcla-v1.wav');assert np.isfinite(mix).all()
bands={}
for lo,hi in [(40,150),(150,500),(500,2000),(2000,6000),(6000,16000)]:
 z=sosfilt(butter(2,[lo,hi],fs=sr,btype='band',output='sos'),mix,axis=0);bands[f'{lo}-{hi}']={}
 for name,a,b in [('verso',4,12),('coro',16,24),('puente',40,48),('regreso',48,60),('coda',60,64)]:
  l=int(P['compases'][a]['t']*sr);r=int((P['compases'][b]['t'] if b<64 else P['duracion']-4)*sr)
  bands[f'{lo}-{hi}'][name]=float(10*np.log10(np.mean(z[l:r]**2)/(np.mean(mix[l:r]**2)+1e-15)+1e-15))
gif=next(out.glob('*.gif'));im=Image.open(gif);frames=[];duration=0
for i in range(im.n_frames):im.seek(i);duration+=im.info['duration'];frames.append(im.convert('RGB').resize((600,315)))
assert duration<=10000 and gif.stat().st_size<=15*1024**2
sheet=Image.new('RGB',(600,315*len(frames)))
for i,frame in enumerate(frames):sheet.paste(frame,(0,i*315))
with (out/'proceso'/f'04-revision-gif-s{P["semilla"]}-{tag}.png').open('xb') as f:sheet.save(f,'PNG')
deps=[repo/'inferencia/vendor/difonos/runtime/g2p.js',repo/'inferencia/vendor/difonos/runtime/difonos.js',repo/'inferencia/vendor/difonos/bancos/sabina-1-b44e7fab5cee/manifiesto.json',repo/'inferencia/vendor/difonos/bancos/sabina-1-b44e7fab5cee/banco.flac']
extra=dict(fuentes_sin_cambios=originales,dependencias_voz={str(p.relative_to(repo)):sha(p) for p in deps},memoria_temporal_verificada=mem,donante_rms=float(np.sqrt(np.mean(bird[a:b]**2))) if False else float(np.sqrt(np.mean(bird[int(mem['t']*sr):int(mem['disponible']*sr)]**2))),bandas= bands,gif=dict(cuadros=len(frames),ms=duration,bytes=gif.stat().st_size))
with (out/'verificacion-adicional.json').open('x',encoding='utf8') as f:json.dump(extra,f,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in report.items() if k!='detalle'},ensure_ascii=True));print(json.dumps(extra,ensure_ascii=True))
