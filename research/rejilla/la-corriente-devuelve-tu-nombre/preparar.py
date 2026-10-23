"""Fija versiones sin cambiar biblioteca ni obras anteriores."""
from comun import *
R=BASE.parent;A=R.parent.parent;F=BASE/'fuentes'
def copia(src,dest):
 if dest.exists():
  assert sha(src)==sha(dest),dest
 else:guardar(dest,src.read_bytes())
for src,dest in [(R/'el-agua-no-termina/motor.mjs',F/'agua/motor.mjs'),(R/'el-lago-que-canta-bajo-el-hielo/mezcla.py',F/'lago/mezcla.py'),(R/'el-lago-que-canta-bajo-el-hielo/laminas.py',F/'lago/laminas.py'),(R/'el-lago-que-canta-bajo-el-hielo/fuentes/vocoder/sintes.py',F/'vocoder/sintes.py')]:copia(src,dest)
for f in ['difonos.js','g2p.js']:copia(R/'inferencia/vendor/difonos/runtime'/f,F/'difonos'/f)
src=R/'el-lago-que-canta-bajo-el-hielo/fuentes/traspuesta/hydra'
if not src.exists():
 candidates=list((R/'el-lago-que-canta-bajo-el-hielo/fuentes/traspuesta').rglob('*hydra*.js'));src=candidates[0]
 if src.is_file():copia(src,F/'hydra/hydra-synth.js')
else:
 for p in src.rglob('*'):
  if p.is_file():copia(p,F/'hydra'/p.relative_to(src))
for p in (R/'el-lago-que-canta-bajo-el-hielo/fuentes/traspuesta').rglob('*LICENSE*'):
 if p.is_file():copia(p,F/'hydra'/('LICENCIA-'+p.name))
subprocess.run(['python',str(A/'biblioteca-de-instrumentos/tomar.py'),'mbira','kalimbacaja','arpaboca','bateria-tr808','bateria-frito','objeto-chelo','objeto-contrabajo','objeto-tambor-que-habla','meleeviewer-8-basso','receta-organo-roto','--a',str(BASE)],check=True,env={**os.environ,'PYTHONIOENCODENCODING':'utf-8','PYTHONIOENCODING':'utf-8'})
jsave(BASE/'procedencia.json',{'fuentes':{str(p.relative_to(BASE)).replace('\\','/'):sha(p) for p in F.rglob('*') if p.is_file()},'banco_local':'../inferencia/vendor/difonos/bancos/sabina-1-b44e7fab5cee','adaptadores_reusados':'El lago: vocoder por bloques y escritura/lectura Rejilla; se adaptan localmente, sin importar sus globals.'})
print('fuentes fijadas',lib().name)
