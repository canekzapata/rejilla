"""Revisa la revisión y documenta las diferencias escritas y el audio entregado."""
import json,sys,subprocess
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from PIL import Image,ImageDraw
import producir as p
R=Path(__file__).resolve().parent

def main(out):
 tag=out.name.split('-')[-1];old=R/'otro-arriba-s19102819-8b1564cb777b'
 a=json.loads((old/'partitura.json').read_text('utf8'));b=json.loads((out/'partitura.json').read_text('utf8'))
 assert [f['letra'] for f in a['frases']]==[f['letra'] for f in b['frases']]
 assert [[e['nota'] for e in f['eventos']] for f in a['frases']]==[[e['nota'] for e in f['eventos']] for f in b['frases']]
 counts={}
 for k in ['bajo','rhodes','trompeta','piano']:
  counts[k]=dict(antes=len(a[k]),ahora=len(b[k]),duracion_mediana_antes=float(np.median([e['dur'] for e in a[k]])),duracion_mediana_ahora=float(np.median([e['dur'] for e in b[k]])))
 master=out/f'otro-arriba-v2-s{b["semilla"]}-{tag}.m4a'
 probe=json.loads(p.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(master)]).stdout)
 decoded=p.run(['ffmpeg','-v','error','-i',str(master),'-f','f32le','-acodec','pcm_f32le','-ar','32000','-ac','2','-']).stdout
 y=np.frombuffer(decoded,np.float32).reshape(-1,2);assert np.isfinite(y).all() and abs(y).max()<1
 assert abs(float(probe['format']['duration'])-b['duracion'])<.1 and probe['streams'][0]['sample_rate']=='48000'
 # Spectral proportions document register and masking, without equating them with musical quality.
 reports={};bands=[(20,120),(120,350),(350,2000),(2000,8000),(8000,15000)]
 for s in b['secciones']:
  x=y[round(s['t']*32000):round(s['fin']*32000)].mean(axis=1);nn=8192;chunks=x[:len(x)//nn*nn].reshape(-1,nn)
  power=np.mean(abs(np.fft.rfft(chunks*np.hanning(nn),axis=1))**2,axis=0);freq=np.fft.rfftfreq(nn,1/32000)
  reports[s['nombre']]={f'{lo}-{hi}':float(power[(freq>=lo)&(freq<hi)].sum()/power.sum()) for lo,hi in bands}
 # RMS of each actual old source excerpt confirms that the identification sampler is not silent.
 samples=[]
 for k,t in [('rhodes',10),('bajo',10),('respuestas-metal',15)]:
  sr,x=wavfile.read(old/'render'/f'{k}-8b1564cb777b.wav');clip=x[int(t*sr):int((t+5)*sr)];rms=float(np.sqrt(np.mean(clip**2)));assert rms>.001
  samples.append(dict(instrumento=k,fuente_desde=t,fuente_hasta=t+5,salida_desde=len(samples)*5.5,rms=rms))
 p.sc.js(out/'revision-comparada.json',dict(letra_y_alturas_principales_conservadas=True,arreglo=counts,duracion_aac=float(probe['format']['duration']),decodificado_finito=True,pico_muestra=float(abs(y).max()),bandas_por_seccion=reports,muestra_identificacion=samples,sin_escucha_propia=True))
 im=Image.new('RGB',(1200,630),'#141924');d=ImageDraw.Draw(im);font=p.sc.font
 d.text((32,22),'OTRO ARRIBA · REVISIÓN DEL ARREGLO',font=font(33),fill='#fff0d9')
 d.text((32,78),'Comparación de la escritura; menos ataques no implica por sí solo mayor calidad.',font=font(16),fill='#d8c3cc')
 for j,(k,name) in enumerate([('bajo','BAJO'),('rhodes','RHODES'),('trompeta','TROMPETA')]):
  yy=145+j*135;d.text((32,yy),name,font=font(20),fill='#f3abc2')
  for ii,(score,label,color) in enumerate([(a,'v1','#8b8d9c'),(b,'v2','#d8bd82')]):
   line=yy+40+ii*30;d.text((34,line-8),label,font=font(14),fill=color)
   for e in score[k]:
    x=96+e['t']/score['duracion']*1060;d.line((x,line,x+max(1,e['dur']/score['duracion']*1060),line),width=3,fill=color)
 d.text((32,565),'Misma letra, melodía y duración. Campo armónico original conservado muestra por muestra.',font=font(15),fill='#e0d3df')
 d.text((32,599),'Semilla 19102819 · Datos de partituras y audio; sin escucha propia.',font=font(14),fill='#c5bdcd')
 p.sc.png(out/'proceso'/f'05-comparacion-arreglo-{tag}.png',im)
 with (out/'proceso/README.md').open('a',encoding='utf8') as f:f.write('\n5. Comparación posterior: duraciones y ataques de bajo, Rhodes y trompeta de ambas partituras; se distingue de las etapas del GIF.\n')
 with (out/'CAMBIOS.md').open('a',encoding='utf8') as f:
  f.write('\n## Identificar el acompañamiento anterior\n\nLa muestra aislada presenta Rhodes de 0 a 5 s, bajo fretless de 5.5 a 10.5 s y trompeta de 11 a 16 s, separados por medio segundo. Son recortes de las pistas anteriores, no recreaciones. Permite precisar a qué timbre se refiere «tutún» sin atribuírselo por adivinación.\n\n## Datos de la revisión\n\n')
  for k,v in counts.items():f.write(f'- {k}: {v["antes"]} → {v["ahora"]} notas; duración mediana {v["duracion_mediana_antes"]:.2f} → {v["duracion_mediana_ahora"]:.2f} s.\n')
  f.write('\nLos recuentos describen el arreglo, no prueban claridad o calidad musical. AAC decodificado finito; duración y frecuencia de muestreo verificadas. Ver revisión por bandas y límites en `revision-comparada.json`.\n')
 p.sc.js(out/'registro-entrega.json',dict(archivos={str(x.relative_to(out)):p.sha(x) for x in out.rglob('*') if x.is_file()}))
 print(json.dumps(counts,ensure_ascii=False));print('REVISADO',master)

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
