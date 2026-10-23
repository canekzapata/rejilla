"""Verificación del audio, intervalos del claro y procedencia del halo."""
from pathlib import Path
import json,sys,csv,subprocess
import numpy as np
from scipy.io import wavfile
from PIL import Image
import partitura as sc

def main(out):
 tag=out.name.split('-')[-1];P=json.loads((out/'partitura.json').read_text('utf8'));V=json.loads((out/'verificacion.json').read_text('utf8'));halo=json.loads((out/'halo-mediciones.json').read_text('utf8'));wall=json.loads((out/'paredes-y-retorno.json').read_text('utf8'))
 def read(k):
  sr,y=wavfile.read(out/'render'/f'{k}-{tag}.wav');assert sr==32000 and np.isfinite(y).all();return y
 assert len(halo['notas'])>30 and len(wall['frecuencias_aprendidas'])==6
 errors=[]
 for note in halo['notas']:
  assert note['intervalo_fuente'][1]>note['intervalo_fuente'][0] and note['ecos_s']==[.061,.103,.157]
  for p in note['seleccion']:
   assert p['parcial']>=2 and p['magnitud']>0;errors.append(abs(1200*np.log2(p['hz']/p['esperado_hz'])))
 assert max(errors)<27
 clear=next(s for s in P['secciones'] if 'claro' in s['nombre']);a=round((clear['t']+.1)*32000);z=round(sc.START[30]*32000)
 for k in ['pared-izquierda','pared-derecha']:assert abs(read(k)[a:z]).max()==0
 # Quantify all groups by section, with nominal mix gains; do not label counts as musical quality.
 names=['aire','cobre-luz','palos-parlantes','pajaros','agua','madera','halo','ecos-halo','pared-izquierda','pared-derecha']
 groups={};nonzero={}
 for k in names:
  y=read(k)*V['ganancias'][k];nonzero[k]=float(abs(y).max());assert nonzero[k]>1e-6
  groups[k]={s['nombre']:float(np.sqrt(np.mean(y[round(s['t']*32000):round(s['fin']*32000)]**2))) for s in P['secciones']}
 # AAC decoding, true peak already measured independently in production.
 master=out/(out.name+'.m4a');probe=json.loads(subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(master)],check=True,capture_output=True).stdout)
 assert probe['streams'][0]['sample_rate']=='48000' and abs(float(probe['format']['duration'])-P['duracion'])<.1
 recipe=json.loads((out/'receta-final.json').read_text('utf8'));assert all(sc.sha(out/k)==v for k,v in recipe['archivos'].items())
 gif=next(out.glob('*.gif'));duration=0
 with Image.open(gif) as im:
  for i in range(im.n_frames):im.seek(i);duration+=im.info['duration']
 assert duration<=10000 and gif.stat().st_size<=15*1024**2
 for p in list(out.glob('*.png'))+list((out/'proceso').glob('*.png')):
  with Image.open(p) as im:im.verify()
 with Image.open(out/'og.png') as im:assert im.size==(1200,630)
 rows=list(csv.DictReader(next(out.glob('densidad-*.csv')).open(encoding='utf8')));times=[float(r['tiempo_s']) for r in rows];assert np.all(np.diff(times)>0)
 for row in rows:assert 0<=float(row['ocupacion_sobre_menos60dbfs'])<=1
 sc.js(out/'revision-musical-y-tecnica.json',dict(claro_sin_paredes=[a/32000,z/32000],ecos_cortos_s=[.061,.103,.157],notas_halo=len(halo['notas']),desvio_maximo_parcial_cents=max(errors),frecuencias_que_transforman_retorno=wall['frecuencias_aprendidas'],rms_nominal_por_seccion=groups,picos_nominales=nonzero,receta_verificada=True,duracion_aac=float(probe['format']['duration']),gif_ms=duration,gif_bytes=gif.stat().st_size,sin_escucha_propia=True,limite='Las mediciones no verifican belleza, comprensión de las palabras breves ni preferencia musical.'))
 print('VERIFICADO',len(halo['notas']),'notas de halo; claro',a/32000,z/32000,'s; GIF',duration,'ms',gif.stat().st_size,'bytes')
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
