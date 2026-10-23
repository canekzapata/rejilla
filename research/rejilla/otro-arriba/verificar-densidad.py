"""Calibración breve del análisis y comprobación de las entregas, sin tocar el audio."""
import importlib.util,json,sys,csv
from pathlib import Path
import numpy as np
from PIL import Image

R=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('density',R/'analizar-densidad.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def main(out):
 tag=out.name.split('-')[-1];t=np.arange(m.SR)/m.SR;y=np.sin(2*np.pi*1000*t).astype(np.float32)
 same=m.analyze(np.stack([y,y],axis=-1));opposite=m.analyze(np.stack([y,-y],axis=-1));half=m.analyze(np.stack([y*.5,y*.5],axis=-1));zero=m.analyze(np.zeros((m.SR,2),np.float32))
 phase_error=float(np.max(abs(same['power']-opposite['power'])));assert phase_error<1e-10
 a=same['power'];b=half['power'];ix=a>1e-4;delta=float(np.median(10*np.log10(b[ix]/a[ix])));assert abs(delta+6.0206)<.002
 assert np.isfinite(zero['db']).all() and not (zero['db']>-60).any()
 with (out/f'otro-arriba-densidad-y-bandas-s19102819-{tag}.csv').open(encoding='utf8') as f:rows=list(csv.DictReader(f))
 times=np.array([float(r['tiempo_s']) for r in rows]);assert np.all(np.diff(times)>0) and times[0]==0
 occ=np.array([float(r['ocupacion_log_40_12000_sobre_menos60dBFS']) for r in rows]);assert np.all((occ>=0)&(occ<=1))
 bands=np.array([[float(v) for k,v in r.items() if k.startswith('energia_')] for r in rows]);total=bands.sum(axis=1)
 # The 1e-20 stabilizer matters in the final numerical silence; test unity where there is signal.
 assert np.all((total>=0)&(total<=1.000001)) and np.allclose(total[occ>0],1,atol=1e-5)
 initial=json.loads((out/'receta-inicial.json').read_text('utf8'));assert m.sha(R/'analizar-densidad.py')==initial['programa_sha256']
 recipe=json.loads((out/'receta-final.json').read_text('utf8'));assert all(m.sha(out/k)==v for k,v in recipe['archivos'].items())
 measures=json.loads((out/'medidas.json').read_text('utf8'));assert all(m.sha(m.REPO/k)==v for k,v in measures['fuentes_sha256'].items())
 dims={}
 for p in out.glob('*.png'):
  with Image.open(p) as im:im.verify()
  with Image.open(p) as im:dims[p.name]=list(im.size)
 gif=next(out.glob('*.gif'))
 with Image.open(gif) as im:
  duration=0
  for i in range(im.n_frames):im.seek(i);duration+=im.info['duration']
 assert duration<=10000 and gif.stat().st_size<=15*1024**2 and dims['og.png']==[1200,630]
 report=dict(calibracion_antifase_error_potencia=phase_error,calibracion_media_amplitud_db=delta,silencio_sin_falsos_positivos=True,csv_filas=len(rows),csv_tiempos_crecientes=True,bandas_suman_uno_con_senal_activa=True,estabilizador_bandas=1e-20,recetas_y_fuentes_intactas=True,dimensiones_png=dims,gif_duracion_ms=duration,gif_bytes=gif.stat().st_size,sin_escucha_propia=True)
 m.js(out/'verificacion-adicional.json',report);print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
