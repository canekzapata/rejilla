from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter,sosfilt
from PIL import Image,ImageOps,ImageDraw
out=Path(sys.argv[1]);repo=out.parent.parent;tag=out.name.split('-')[-1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
score=json.loads((out/'partitura.json').read_text('utf8'));recipe=json.loads((out/'receta-inicial.json').read_text('utf8'))
unchanged={p:sha(repo/p)==h for p,h in recipe['fuentes'].items()};assert all(unchanged.values())
sr,voice=wavfile.read(out/'render/voz.wav');voice=voice.mean(axis=1)
events=[e for f in score['frases'] for e in f['eventos']]
energy=[float(np.sqrt(np.mean(voice[int((e['t']+.05)*sr):int((e['t']+e['dur']-.02)*sr)]**2))) for e in events]
assert min(energy)>1e-5
sr,y=wavfile.read(out/'render/mezcla-previa.wav');assert np.isfinite(y).all() and abs(y).max()<1
bands={}
for lo,hi in [(45,150),(150,500),(500,2000),(2000,6000),(6000,16000)]:
 z=sosfilt(butter(2,[lo,hi],fs=sr,btype='band',output='sos'),y,axis=0)
 bands[f'{lo}-{hi}']={}
 for name,a,b in [('verso',2,10),('pre',10,14),('coro',14,22),('final',26,30)]:
  l=int(a*4*60/84*sr);r=int(b*4*60/84*sr)
  bands[f'{lo}-{hi}'][name]=float(10*np.log10(np.mean(z[l:r]**2)/(np.mean(y[l:r]**2)+1e-15)+1e-15))
gif=next(out.glob('*.gif'));im=Image.open(gif);frames=[];duration=0
for i in range(im.n_frames):
 im.seek(i);duration+=im.info['duration'];frames.append(im.convert('RGB').resize((600,315)))
assert duration<=10000 and gif.stat().st_size<=15*1024**2 and len(frames)==3
sheet=Image.new('RGB',(600,945));
for i,f in enumerate(frames):sheet.paste(f,(0,i*315))
dest=out/'proceso'/f'04-revision-gif-{tag}.png'
with dest.open('xb') as h:sheet.save(h,'PNG')
deps=[repo/'inferencia/vendor/difonos/runtime/g2p.js',repo/'inferencia/vendor/difonos/runtime/difonos.js',repo/'inferencia/vendor/difonos/bancos/sabina-1-b44e7fab5cee/manifiesto.json',repo/'inferencia/vendor/difonos/bancos/sabina-1-b44e7fab5cee/banco.flac']
result=dict(fuentes_sin_cambios=unchanged,silabas_con_energia=len(energy),min_rms_silaba=min(energy),bandas_dB_relativas=bands,gif=dict(cuadros=len(frames),duracion_ms=duration,bytes=gif.stat().st_size),dependencias_voz={str(p.relative_to(repo)):sha(p) for p in deps})
with (out/'verificacion-adicional.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=True,indent=2))
