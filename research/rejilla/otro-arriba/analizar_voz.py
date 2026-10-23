from pathlib import Path
import sys,json
import numpy as np
from scipy.io import wavfile
from scipy.signal import correlate,butter,sosfilt
out=Path(sys.argv[1]);P=json.loads((out/'partitura.json').read_text('utf8'));sr,y=wavfile.read(out/'render/voz.wav');y=y.mean(axis=1);y=sosfilt(butter(2,[90,7000],fs=sr,btype='band',output='sos'),y)
def yin(frame):
 frame=frame-frame.mean();n=len(frame);corr=correlate(frame,frame,mode='full',method='fft')[n-1:];energy=np.concatenate([[0.],np.cumsum(frame*frame)]);lags=np.arange(1,min(n//2,int(sr/120)))
 diff=energy[n-lags]+energy[n]-energy[lags]-2*corr[lags];diff=np.maximum(diff,0);cmnd=diff*lags/(np.cumsum(diff)+1e-15);low=int(sr/1100)
 candidates=[i for i in range(low,len(cmnd)-1) if cmnd[i]<.17 and cmnd[i]<=cmnd[i-1] and cmnd[i]<cmnd[i+1]]
 if not candidates:return None
 i=candidates[0];den=cmnd[i-1]-2*cmnd[i]+cmnd[i+1];offset=.5*(cmnd[i-1]-cmnd[i+1])/den if abs(den)>1e-12 else 0
 lag=i+1+np.clip(offset,-.5,.5);return float(sr/lag),float(cmnd[i])
rows=[]
for f in P['frases']:
 for e in f['eventos']:
  if e['dur']<.22:continue
  for p in [.45,.65,.78]:
   center=e['t']+e['dur']*p;n=3072;a=round(center*sr-n/2);frame=y[a:a+n]
   if len(frame)!=n or np.sqrt(np.mean(frame*frame))<.002:continue
   result=yin(frame)
   if result:
    hz,confidence=result;pitch=69+12*np.log2(hz/440);rows.append(dict(frase=f['id'],texto=e['texto'],t=center,nota=e['nota'],f0=hz,cents=float((pitch-e['nota'])*100),cmnd=confidence))
errors=np.array([abs(x['cents']) for x in rows]);report=dict(ventanas_periodicas=len(rows),mediana_error_absoluto_cents=float(np.median(errors)) if len(errors) else None,p95_error_absoluto_cents=float(np.percentile(errors,95)) if len(errors) else None,dentro_50_cents=int(sum(errors<50)),limites='Ventanas periódicas de sílabas largas; consonantes, transiciones y errores de octava pueden afectar estimaciones. No mide inteligibilidad ni belleza.',ventanas=rows)
with (out/'revision-melodia.json').open('x',encoding='utf8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
print({k:v for k,v in report.items() if k!='ventanas'})
