from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter,sosfilt
from PIL import Image
R=Path(__file__).resolve().parent;out=Path(sys.argv[1]).resolve();tag=out.name.split('-')[-1];P=json.loads((out/'partitura.json').read_text('utf8'));V=json.loads((out/'verificacion.json').read_text('utf8'));SR,y=wavfile.read(out/f'mezcla-s{P["semilla"]}-{tag}.wav')
assert np.isfinite(y).all() and float(abs(y).max())<1
assert float(V['pico_verdadero'])<-.8 and V['fuentes_originales_intactas']
assert abs(len(y)/SR-P['duracion'])<1/SR
tail=y[round((P['cierre']+.35)*SR):];assert float(abs(tail).max())==0
def rms(a):return float(np.sqrt(np.mean(a.astype(np.float64)**2))+1e-14)
bands={}
for lo,hi in [(20,60),(60,120),(120,350),(350,2000),(2000,8000),(8000,15000)]:
 filtered=sosfilt(butter(2,[lo,hi],fs=SR,btype='band',output='sos'),y,axis=0)
 bands[f'{lo}-{hi}']={s['nombre']:round(20*np.log10(rms(filtered[round(s['t']*SR):round(s['fin']*SR)])/rms(y[round(s['t']*SR):round(s['fin']*SR)])),2) for s in P['secciones']}
gif=out/f'proceso-otro-arriba-s{P["semilla"]}-{tag}.gif';im=Image.open(gif);frames=[];duration=0
for j in range(im.n_frames):im.seek(j);duration+=im.info.get('duration',0);frames.append(im.convert('RGB').resize((600,315)))
assert duration<=10000 and gif.stat().st_size<15*1024**2
sheet=Image.new('RGB',(600,315*len(frames)))
for j,frame in enumerate(frames):sheet.paste(frame,(0,j*315))
with (out/'proceso'/f'05-revision-gif-s{P["semilla"]}-{tag}.png').open('xb') as f:sheet.save(f,'PNG')
with (out/f'otro-arriba-letra-{tag}.lrc').open('x',encoding='utf8') as f:
 f.write('[ti:Otro arriba]\n[ar:Canek Zapata]\n')
 for phrase in P['frases']:
  t=phrase['eventos'][0]['t'];f.write(f'[{int(t//60):02d}:{t%60:05.2f}]{phrase["letra"]}\n')
with (out/'revision-entrega.json').open('x',encoding='utf8') as f:json.dump(dict(master=V,mezcla_finita=True,corte_final=True,gif_ms=duration,gif_bytes=gif.stat().st_size,frases_cantadas=len(P['frases']),bandas_relativas_db=bands,comentario='Revisiones técnicas y visuales; la estimación de afinación está en revision-melodia.json. No se realizó escucha propia ni prueba de inteligibilidad.'),f,ensure_ascii=False,indent=2)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
more=[R/'analizar_voz.py',Path(__file__),R/'README.md',R.parent/'lo-que-no-sono/voz.cjs',R.parent/'inferencia/vendor/difonos/bancos/sabina-1-b44e7fab5cee/manifiesto.json',R.parent/'catalogo-agua-que-habla/instrumentos-48b8a06e1049/motores/web.js']
for i,p in enumerate(more):
 with (out/'fuentes'/f'cierre-{i:02d}-{p.name}').open('xb') as f:f.write(p.read_bytes())
initial=json.loads((out/'receta-inicial.json').read_text('utf8'))
with (out/'receta-entrega.json').open('x',encoding='utf8') as f:json.dump(dict(hash_ejecucion=initial['hash_ejecucion'],semilla=P['semilla'],nonce=initial['nonce'],archivos={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and p.name!='receta-entrega.json'}),f,ensure_ascii=False,indent=2)
print(dict(duracion=P['duracion'],lufs=V['lufs'],pico=V['pico_verdadero'],gif_ms=duration,gif_bytes=gif.stat().st_size))
