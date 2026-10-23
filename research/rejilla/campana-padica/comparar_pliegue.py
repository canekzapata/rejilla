from pathlib import Path
import json,subprocess
import numpy as np
from scipy.io import wavfile
from campana import render
ROOT=Path(__file__).resolve().parent;TAG='s20261021-9b5d27254a47';OUT=ROOT/f'campana-distancias-{TAG}'
score={'duration':10,'initial':{'fold':0,'depth':.7,'tension':7,'damping':.2,'midi':48,'pickup':1},'events':[{'t':.12,'hit':9,'vel':.8}]}
reference,_=render(score,10,24000);_,dynamic=wavfile.read(OUT/f'un-golpe-cambia-de-mundo-{TAG}.wav')
before=float(np.max(abs(reference[:33600]-dynamic[:33600])))
a=reference[36000:84000].astype(float).ravel();b=dynamic[36000:84000].astype(float).ravel();gain=float(a@b/(a@a));residual=float(np.linalg.norm(b-gain*a)/np.linalg.norm(b))
assert before==0 and residual>.1
name=f'referencia-un-golpe-sin-plegar-{TAG}'
with (OUT/(name+'.wav')).open('xb') as f:wavfile.write(f,24000,reference)
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-n','-i',str(OUT/(name+'.wav')),'-c:a','aac','-b:a','192k',str(OUT/(name+'.m4a'))],check=True)
r={'referencia':name+'.m4a','antes_de_1_4_s_error_maximo':before,'segmento_comparado_s':[1.5,3.5],
 'ganancia_escalar_ajustada':gain,'residuo_relativo_despues_de_ajustar_ganancia':residual,
 'interpretacion':'Antes del gesto las señales son idénticas. Después, una ganancia escalar no explica la diferencia. Esto no sustituye la evaluación perceptiva.'}
with (OUT/f'comparacion-pliegue-{TAG}.json').open('x',encoding='utf-8') as f:json.dump(r,f,ensure_ascii=False,indent=2)
print(json.dumps(r,ensure_ascii=True))
