from pathlib import Path
import json,sys,hashlib,subprocess
import numpy as np
from scipy.io import wavfile
from PIL import Image
out=Path(sys.argv[1]);repo=out.parent.parent;tag=out.name.split('-')[-1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
P=json.loads((out/'partitura.json').read_text('utf8'));rec=json.loads((out/'receta-inicial.json').read_text('utf8'))
sources={k:sha(repo/k)==v for k,v in rec['fuentes'].items()};assert all(sources.values()),sources
ev=P['eventos'];a={e['tick'] for e in ev if e['voz']=='boca'};b={e['tick'] for e in ev if e['voz']=='respuesta'}
assert {e['tick'] for e in P['encuentros']}==a&b
assert all(0<=e['t']<e['t']+e['dur']<P['duracion'] for e in ev)
periods={k:sorted({e['periodo'] for e in P['ciclos'] if e['voz']==k}) for k in ['boca','respuesta']}
for k in periods:
 c=[e for e in P['ciclos'] if e['voz']==k]
 assert all(v['tick']-u['tick']==u['periodo'] for u,v in zip(c,c[1:]))
sr,y=wavfile.read(out/'render/mezcla.wav');assert np.isfinite(y).all();cut=int(P['corte']*sr);assert np.max(np.abs(y[cut:]))==0
hit=int(P['golpe_final']*sr);impact=float(np.sqrt(np.mean(y[hit:cut]**2)));assert impact>.1
sec={}
for i,(name,start) in enumerate(P['secciones']):
 stop=P['secciones'][i+1][1] if i+1<len(P['secciones']) else P['corte'];z=y[int(start*sr):int(stop*sr)];sec[name]=dict(rms_db=float(20*np.log10(np.sqrt(np.mean(z*z))+1e-12)),peak=float(np.max(np.abs(z))))
gif=next(out.glob('*.gif'));im=Image.open(gif);frames=[];ms=0
for i in range(im.n_frames):im.seek(i);ms+=im.info['duration'];frames.append(im.convert('RGB').resize((600,315)))
assert ms<=10000 and gif.stat().st_size<=15*1024**2
sheet=Image.new('RGB',(600,315*len(frames)))
for i,f in enumerate(frames):sheet.paste(f,(0,315*i))
with (out/'proceso'/f'04-revision-gif-s{P["semilla"]}-{tag}.png').open('xb') as f:sheet.save(f,'PNG')
result=dict(fuentes_sin_cambios=sources,notas=len(ev),encuentros=len(a&b),periodos=periods,secciones=sec,cierre=dict(golpe_rms=impact,silencio_final_ms=(len(y)-cut)*1000/sr,corte_s=P['corte']),gif=dict(ms=ms,bytes=gif.stat().st_size,cuadros=len(frames)))
with (out/'verificacion.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=True))
