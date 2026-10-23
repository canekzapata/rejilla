"""Revisar la relación entre escritura, contraste, silencio y entrega de audio."""
from pathlib import Path
import sys,json,csv,subprocess
import numpy as np
from scipy.io import wavfile
from PIL import Image
import partitura as sc

def main(out):
 tag=out.name.split('-')[-1];P=json.loads((out/'partitura.json').read_text('utf8'));V=json.loads((out/'verificacion.json').read_text('utf8'))
 modal=[]
 for f in P['frases']:
  if f['voz']!='aire':continue
  if 4<=f['bar']<16 or 64<=f['bar']<72:allowed={0,2,3,7,8};family='Tizita menor temperada'
  elif 16<=f['bar']<24 or 72<=f['bar']<80:allowed={0,1,3,4,6,7,9,10};family='octatónica'
  elif 24<=f['bar']<40 or 80<=f['bar']<96:allowed={0,2,4,7,9};family='pentatónica mayor'
  elif f['bar']>=104:allowed={2,4,6,9,11};family='pentatónica mayor un tono arriba'
  else:continue
  pcs={round(e['nota'])%12 for e in f['eventos']};assert pcs<=allowed,(f['bar'],pcs,allowed);modal.append(dict(frase=f['id'],familia=family,clases=sorted(pcs)))
 trans=P['transformaciones'];assert any(x['aumentacion']==2 for x in trans)
 palindrome=[e for e in P['juguete'] if e['b']==17];times=[e['t'] for e in palindrome]
 rhythm=np.diff(times).tolist()+[palindrome[-1]['dur']/.88];assert np.allclose(rhythm,rhythm[::-1],atol=1e-5)
 assert P['compases'][96]['pulso']==3.5 and P['compases'][97]['pulso']==4.5
 # The two basses really exchange roles instead of playing the same riff together.
 sr,dub=wavfile.read(out/'render'/f'bajo-dub-{tag}.wav');sr,fret=wavfile.read(out/'render'/f'fretless-{tag}.wav');assert sr==32000
 lo=round((sc.START[48]+.2)*sr);hi=round((sc.START[64]-.2)*sr);assert abs(dub[lo:hi]).max()==0 and np.sqrt(np.mean(fret[lo:hi]**2))>.005
 sr,mix=wavfile.read(out/'render'/f'mezcla-{tag}.wav');a,z=V['silencio_antes_coro'];assert abs(mix[round(a*sr):round(z*sr)]).max()==0
 master=out/(out.name+'.m4a');raw=subprocess.run(['ffmpeg','-v','error','-i',str(master),'-f','f32le','-ar','32000','-ac','2','-'],capture_output=True,check=True).stdout;y=np.frombuffer(raw,np.float32).reshape(-1,2);assert np.isfinite(y).all() and abs(y).max()<1
 # Exclude the AAC boundary overlap from the silence measurement.
 silence=y[round((a+.06)*sr):round((z-.06)*sr)];silencedb=float(20*np.log10(np.sqrt(np.mean(silence**2))+1e-15));assert silencedb<-60
 probe=json.loads(subprocess.run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(master)],check=True,capture_output=True).stdout);assert probe['streams'][0]['sample_rate']=='48000' and abs(float(probe['format']['duration'])-P['duracion'])<.1
 measures={}
 for k,g in V['ganancias'].items():
  sr,x=wavfile.read(out/'render'/f'{k}-{tag}.wav');assert np.isfinite(x).all() and abs(x).max()>0
  measures[k]={s['nombre']:float(np.sqrt(np.mean(x[round(s['t']*sr):round(s['fin']*sr)]**2))*g) for s in P['secciones']}
 recipe=json.loads((out/'receta-final.json').read_text('utf8'));assert all(sc.sha(out/k)==v for k,v in recipe['archivos'].items())
 for p in list(out.glob('*.png'))+list((out/'proceso').glob('*.png')):
  with Image.open(p) as im:im.verify()
 with Image.open(out/'og.png') as im:assert im.size==(1200,630)
 gif=next(out.glob('*.gif'));duration=0
 with Image.open(gif) as im:
  for j in range(im.n_frames):im.seek(j);duration+=im.info['duration']
 assert duration<=10000 and gif.stat().st_size<=15*1024**2
 rows=list(csv.DictReader(next(out.glob('densidad-*.csv')).open(encoding='utf8')));assert all(0<=float(r['ocupacion_sobre_menos60dbfs'])<=1 for r in rows)
 sc.js(out/'revision-musical-y-tecnica.json',dict(familias_melodicas=modal,ritmo_no_retrogradable_beats=[round(float(x/sc.Q),3) for x in rhythm],operaciones=trans,bajo_dub_ausente_en_dialogo=True,silencio_aac_dbfs=silencedb,duracion_aac=float(probe['format']['duration']),rms_nominal_por_seccion=measures,gif_ms=duration,gif_bytes=gif.stat().st_size,recetas_verificadas=True,sin_escucha_propia=True,limite='Las medidas verifican escritura y señal; no certifican pegajosidad del gancho, belleza ni una práctica etíope tradicional.'))
 print('VERIFICADO',P['duracion'],'s; silencio',silencedb,'dBFS; GIF',duration,'ms',gif.stat().st_size,'bytes')
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
