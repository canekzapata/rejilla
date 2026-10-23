from pathlib import Path
import json,sys
import numpy as np
from scipy.io import wavfile
out=Path(sys.argv[1]);tag=out.name.split('-')[-1];P=json.loads((out/'partitura.json').read_text('utf8'));M=json.loads((out/'mediciones-mezcla.json').read_text('utf8'));SR=32000
mapping={'lead':['metal-principal','garganta-principal','sinte-solista'],'contracanto':['sax-contracanto'],'coro':['coro-vocoders'],'armonia':['rhodes','piano-preparado','cuerdas','familias-espectrales'],'bajo':['fretless'],'percusion':['bateria'],'doble':['doble-del-lead'],'cobre-vocal':['cobre-vocal']}
files={n:wavfile.read(out/'render'/f'{n}-{tag}.wav',mmap=True)[1] for names in mapping.values() for n in names}
def rms(x):return np.sqrt(np.mean(x.astype(np.float64)**2))+1e-14
rows=[]
for s,m in zip(P['secciones'],M['secciones']):
 a=round(s['t']*SR);z=round(s['fin']*SR);n=z-a;duck=np.ones(n,np.float32)
 for e in P['bateria']:
  if e['pieza']!='kick':continue
  start=int(e['t']*SR)-a;end=min(n,start+int(.16*SR))
  if end<=0 or start>=n:continue
  i=max(0,start);duck[i:end]=np.minimum(duck[i:end],1-.38*np.exp(-np.arange(i-start,end-start)/SR/.05))
 G={}
 for k,names in mapping.items():
  frag=sum(files[name][a:z] for name in names)*m['ganancias'].get(k,0)
  if k in ['bajo','armonia','coro','doble','cobre-vocal']:frag*=duck[:,None]**(1.3 if k=='bajo' else .7)
  G[k]=frag
 # The requested main lead is a compound instrument: its doubles and vowel-resonated copy belong to the foreground.
 front=G['lead']+G['doble']+G['cobre-vocal']+(G['contracanto'] if s['nombre'] in ['solos','relevos'] else 0)+(G['coro'] if 'coro' in s['nombre'] else 0)
 remainder=sum(G.values())-front
 rows.append(dict(seccion=s['nombre'],frente_sobre_resto_db=round(float(20*np.log10(rms(front)/rms(remainder))),2),percusion_sobre_resto_db=round(float(20*np.log10(rms(G['percusion'])/rms(sum(G.values())-G['percusion']))),2)))
with (out/'balance-frente-compuesto.json').open('x',encoding='utf8') as f:json.dump(rows,f,ensure_ascii=False,indent=2)
print(json.dumps(rows,ensure_ascii=False,indent=2))
