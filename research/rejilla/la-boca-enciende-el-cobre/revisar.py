"""Checks on the actual delivered audio and decoded process frames, kept separate from composition."""
from pathlib import Path
import sys,json,hashlib,subprocess
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter,sosfilt
from PIL import Image
R=Path(__file__).resolve().parent;out=Path(sys.argv[1]).resolve();tag=out.name.split('-')[-1]
P=json.loads((out/'partitura.json').read_text('utf8'));V=json.loads((out/'verificacion.json').read_text('utf8'));SR,y=wavfile.read(out/f'mezcla-s{P["semilla"]}-{tag}.wav')
assert np.isfinite(y).all() and float(abs(y).max())<1
assert float(V['pico_verdadero'])<-.8
assert V['fuentes_originales_intactas']
assert abs(len(y)/SR-P['duracion'])<1/SR
tail=y[round((P['corte_final']+.02)*SR):];assert abs(tail).max()==0
def rms(a):return float(np.sqrt(np.mean(a.astype(np.float64)**2))+1e-14)
bands={}
for a,b in [(20,60),(60,120),(120,350),(350,2000),(2000,8000),(8000,15000)]:
 f=sosfilt(butter(2,[a,b],fs=SR,btype='band',output='sos'),y,axis=0)
 bands[f'{a}-{b}']={s['nombre']:round(20*np.log10(rms(f[round(s['t']*SR):round(s['fin']*SR)])/rms(y[round(s['t']*SR):round(s['fin']*SR)])),2) for s in P['secciones']}
# Check foreground coverage in time. Instrument notes count only where they actually occupy a frame.
coverage={}
for s in P['secciones']:
 t=np.arange(s['t'],s['fin'],.02);mask=np.zeros(len(t),bool)
 for k in ['trompeta','garganta','sinte','sax']:
  for e in P[k]:mask|=(t>=e['t'])&(t<e['t']+e['dur'])
 coverage[s['nombre']]=round(float(mask.mean()),3)
gif=out/f'proceso-la-boca-s{P["semilla"]}-{tag}.gif';im=Image.open(gif);frames=[];duration=0
for j in range(im.n_frames):im.seek(j);duration+=im.info.get('duration',0);frames.append(im.convert('RGB').resize((600,315)))
assert duration<=10000 and gif.stat().st_size<15*1024**2
sheet=Image.new('RGB',(600,315*len(frames)))
for j,frame in enumerate(frames):sheet.paste(frame,(0,j*315))
with (out/'proceso'/f'05-revision-gif-s{P["semilla"]}-{tag}.png').open('xb') as f:sheet.save(f,'PNG')
report=dict(master=V,bandas_relativas_db=bands,ocupacion_frente_escrito=coverage,corte_final_silencioso=True,gif=dict(ms=duration,bytes=gif.stat().st_size,cuadros=im.n_frames),limites='Ocupación escrita no mide protagonismo perceptivo; bandas y niveles no valoran belleza ni fraseo. No se realizó escucha propia.')
with (out/'revision-entrega.json').open('x',encoding='utf8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
with (out/'fuentes/revisar.py').open('xb') as f:f.write(Path(__file__).read_bytes())
print(json.dumps(dict(master=V,gif=report['gif'],ocupacion=coverage),ensure_ascii=False,indent=2))
