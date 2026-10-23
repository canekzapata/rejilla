"""Contrastar ataques del audio con el score. No confundir silencio exacto con rango dinámico."""
import json,sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
out=Path(sys.argv[1]).resolve();P=json.loads((out/'partitura.json').read_text(encoding='utf8'));result={}
for name,start in [('piano',45),('bajo',65)]:
    sr,y=wavfile.read(out/'render'/f'{name}.wav');first={}
    for e in P[name]:first.setdefault(e['ciclo'],e)
    offsets=[];rises=[]
    for e in first.values():
        if not start<e['t']<145:continue
        a=int(e['t']*sr);clip=y[a-960:a+1920].astype(float)
        energy=np.mean(clip*clip,axis=1);env=np.sqrt(np.convolve(energy,np.ones(145)/145,'same'))
        change=env[240:]-env[:-240]
        j=np.flatnonzero(change>.2*change.max())[0]
        offsets.append((float(j)+120-960)/sr*1000)
        pre=np.sqrt(np.mean(y[a-1200:a].astype(float)**2));post=np.sqrt(np.mean(y[a:a+2400].astype(float)**2))
        rises.append(20*np.log10(max(post,1e-4)/max(pre,1e-4)))
    median=float(np.median(np.abs(offsets)));p95=float(np.percentile(np.abs(offsets),95))
    assert median<25 and p95<45,(name,median,p95)
    result[name]={'ataques':len(offsets),'mediana_desvio_absoluto_ms':median,'p95_desvio_absoluto_ms':p95,
        'subida_mediana_dB_con_piso_menos80dBFS':float(np.median(rises))}
result['metodo']='Primera subida al 20% del crecimiento máximo de envolvente RMS de 3 ms, diferencia de 5 ms, en ventana -20 a +40 ms alrededor del ataque escrito. El piano arpegia sus tres voces en 16 ms. Buscar sólo el máximo de crecimiento atrasaba la detección del bajo hasta 26 ms por su ataque y deslizamiento.'
result['correccion']='La subida de 181 dB del bajo en verificacion.json divide por silencio exacto más epsilon: es un índice numérico, no rango dinámico acústico. Aquí se limita el piso a -80 dBFS.'
with (out/'verificacion-ataques.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=False,indent=1))
