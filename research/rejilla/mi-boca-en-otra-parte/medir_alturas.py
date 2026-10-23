"""YIN sobre el relevo audible (sin fondos): rango abierto 80–1000 Hz, sin centrarlo en la nota escrita."""
import json,sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import correlate
out=Path(sys.argv[1]).resolve();P=json.loads((out/'partitura-compuesta.json').read_text(encoding='utf8'))
names=['voz','piano','agua','clarinete','metal','chelo'];joined=None
for n in names:
    sr,x=wavfile.read(out/'render'/f'relevo-{n}.wav')
    joined=x.astype(float) if joined is None else joined+x
def yin(x,sr):
    x=x-x.mean();maxlag=int(sr/80);minlag=int(sr/1000);w=len(x)-maxlag-1
    if w<200 or np.mean(x*x)<1e-10:return None
    ac=correlate(x,x[:w],mode='valid',method='fft')[:maxlag+1]
    energy=np.r_[0,np.cumsum(x*x)];tau=np.arange(maxlag+1)
    dif=np.maximum(0,energy[w]+energy[w+tau]-energy[tau]-2*ac)
    cmnd=np.ones_like(dif);cmnd[1:]=dif[1:]*tau[1:]/np.maximum(np.cumsum(dif[1:]),1e-15)
    below=np.flatnonzero(cmnd[minlag:]<.20)
    if not len(below):return None
    j=minlag+int(below[0])
    while j<maxlag-1 and cmnd[j+1]<cmnd[j]:j+=1
    if j<=0 or j>=maxlag:return None
    denominator=cmnd[j-1]-2*cmnd[j]+cmnd[j+1]
    delta=.5*(cmnd[j-1]-cmnd[j+1])/denominator if abs(denominator)>1e-12 else 0
    return float(sr/(j+delta)),float(1-cmnd[j])
results=[]
for e in P['relevos']:
    center=e['t']+.55*e['dur'];a=round((center-.08)*sr);b=round((center+.08)*sr)
    detected=yin(joined[a:b:3],sr/3);expected=440*2**((e['nota']-69)/12)
    results.append({'id':e['id'],'t':e['t'],'ruta':e['ruta'],'nota':e['nota'],'Hz':detected[0] if detected else None,
       'confianza':detected[1] if detected else None,'error_cents':float(1200*np.log2(detected[0]/expected)) if detected else None})
voiced=[abs(e['error_cents']) for e in results if e['error_cents'] is not None]
multi=[abs(e['error_cents']) for e in results if e['error_cents'] is not None and len(e['ruta'])>1]
report={'metodo':'YIN, 80–1000 Hz, ventana 160 ms al 55% de cada sílaba, audio de relevos sumado sin campos ni coda. Sin restringir la búsqueda a la nota escrita. Las notas sin mínimo YIN <.20 se declaran sin altura estable.',
 'silabas':len(results),'con_altura_estable':len(voiced),'mediana_abs_cents':float(np.median(voiced)),
 'relevos_con_altura_estable':len(multi),'relevos_mediana_abs_cents':float(np.median(multi)),
 'relevos_dentro_50_cents':int(np.sum(np.array(multi)<50)),'detalle':results}
with (out/'verificacion-alturas-relevos.json').open('x',encoding='utf8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in report.items() if k!='detalle'},ensure_ascii=False,indent=1))
