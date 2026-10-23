"""Copias de escucha, una ganancia común por comparación; conservar sondas crudas."""
from comun import *
def main():
 out=ultimo();tag=out.name.split('-')[-1];rows=[]
 for manifest in ['sondas-instrumentos-r2.json','sondas-radio-trafico.json']:
  for key,v in leer(out/manifest).items():
   if not isinstance(v,dict) or 'archivo' not in v:continue
   name=v['archivo'];src=out/Path(name).with_suffix('.wav');sr,y=wavfile.read(src);peak=float(abs(y).max());gain=.75/(peak+1e-15);dest=out/('escuchar-'+name);w=dest.with_suffix('.wav');wav(w,y*gain,sr);subprocess.run(['ffmpeg','-n','-v','error','-i',str(w),'-ar','48000','-c:a','aac','-b:a','224k',str(dest)],check=True);rows.append({'instrumento':key,'origen':src.name,'archivo':dest.name,'ganancia_escucha':gain,'pico_crudo':peak,'nota':'una sola ganancia para todos los estados de la comparación; sin ecualización ni compresión'})
 jsave(out/'escucha-niveles.json',rows);print(len(rows),'copias de escucha; originales conservados')
if __name__=='__main__':main()
