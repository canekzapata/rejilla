from pathlib import Path
import json,hashlib,sys
import numpy as np
from scipy.io import wavfile
from PIL import Image
out=Path(sys.argv[1]);repo=out.parent.parent;tag=out.name.split('-')[-1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rec=json.loads((out/'receta-inicial.json').read_text('utf8'));P=json.loads((out/'partitura.json').read_text('utf8'))
sources={k:sha(repo/k)==v for k,v in rec['fuentes'].items() if Path(k).parts[0]!='la-garganta-sale-bailando'};assert all(sources.values()),sources
snapshots={k:sha(out/'fuentes'/Path(k).name)==v for k,v in rec['fuentes'].items()};assert all(snapshots.values()),snapshots
assert all(e['t']>=0 and e['t']+e['dur']<P['duracion'] for e in P['motivos']+P['chelo'])
assert min(e['casa'] for e in P['chelo'])==0 and max(e['casa'] for e in P['chelo'])==1
parts={}
for p in (out/'render').glob('*.wav'):
 sr,y=wavfile.read(p);assert np.isfinite(y).all();parts[p.name]=dict(sr=sr,segundos=len(y)/sr,peak=float(np.max(np.abs(y))))
sr,y=wavfile.read(out/'render/mezcla.wav');sections={}
for a,b,name in [(0,12,'invocacion'),(12,24,'imitacion'),(24,40,'presion'),(40,60,'house'),(60,80,'coda')]:
 lo=int(P['compases'][a]['t']*sr);hi=int((P['compases'][b]['t'] if b<80 else P['duracion']-5)*sr);z=y[lo:hi]
 sections[name]=dict(rms_db=float(20*np.log10(np.sqrt(np.mean(z*z))+1e-12)),peak=float(np.max(np.abs(z))),inicio=lo/sr)
 assert np.sqrt(np.mean(z*z))>.005
gif=next(out.glob('*.gif'));im=Image.open(gif);frames=[];ms=0
for i in range(im.n_frames):im.seek(i);ms+=im.info['duration'];frames.append(im.convert('RGB').resize((600,315)))
assert ms<=10000 and gif.stat().st_size<15*1024**2
sheet=Image.new('RGB',(600,315*len(frames)))
for i,f in enumerate(frames):sheet.paste(f,(0,i*315))
dest=out/'proceso'/f'04-revision-gif-s{P["semilla"]}-{tag}.png'
with dest.open('xb') as f:sheet.save(f,'PNG')
result=dict(fuentes_sin_cambios=sources,pistas=parts,secciones=sections,gif=dict(ms=ms,bytes=gif.stat().st_size,cuadros=len(frames)),coda_entradas_imitativas=sum(bool(e.get('imitacion')) for e in P['motivos']),sin_letra=True,limite='Las mediciones no acreditan escucha humana, inteligibilidad ni calidad estética.')
with (out/'verificacion.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=True))
