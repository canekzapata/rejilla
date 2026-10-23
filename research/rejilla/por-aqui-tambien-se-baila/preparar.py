"""Fijar originales, sin cambiar biblioteca ni obras previas."""
from comun import *
R=BASE.parent;A=R.parent.parent;MT=R.parent/'montanas-topograficas'
def copia(src,dest):
 if dest.exists():
  if dest.read_bytes()==src.read_bytes():return
  raise FileExistsError(dest)
 guardar(dest,src.read_bytes())
for name in ['nucleo','terreno','idioma','letra','vistas','toponimia/glosario','toponimia/nombrar','lamina']:copia(MT/(name+'.js'),BASE/'fuentes/traspuesta'/(name+'.js'))
for src,dst in [(R/'tapete-de-talbot/tapete.py','talbot/tapete.py'),(R/'instrumentos-de-tres-tiempos/motores.py','tres-tiempos/motores.py'),(R/'la-ciudad-se-hunde-bailando/sintes10.py','radio/sintes10.py'),(R/'la-duna-que-canta/motor/cuerda.js','guembri/cuerda.js'),(A/'biblioteca-de-instrumentos/runtime/g2p.js','difonos/g2p.js'),(A/'biblioteca-de-instrumentos/runtime/difonos.js','difonos/difonos.js')]:
 if 'difonos' in dst and not src.exists():
  src=R/'inferencia/vendor/difonos/runtime'/src.name
 copia(src,BASE/'fuentes'/dst)
if not list(BASE.glob('instrumentos-*')):
 ids=['meleeviewer-13-acordeon','meleeviewer-13-bajo','meleeviewer-13-conga','meleeviewer-13-guiro','meleeviewer-13-campana','bateria-acustico','bateria-tr808','objeto-chelo','objeto-clarinete','mbira','arpaboca','objeto-piano-goma','vibrafono']
 subprocess.run(['python',str(A/'biblioteca-de-instrumentos/tomar.py'),*ids,'--a',str(BASE)],check=True,env={**os.environ,'PYTHONIOENCODING':'utf-8'})
if not (BASE/'procedencia.json').exists():jsave(BASE/'procedencia.json',{'fuentes':{str(p.relative_to(BASE)).replace('\\','/'):sha(p) for p in (BASE/'fuentes').rglob('*') if p.is_file()},'banco_voz_local':'../inferencia/vendor/difonos/bancos/sabina-1-b44e7fab5cee','alcance':'primera etapa, sin mezcla completa ni video'})
