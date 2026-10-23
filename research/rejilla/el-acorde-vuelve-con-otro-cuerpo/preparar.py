"""Instala una toma nueva; los orígenes permanecen intactos."""
from comun import *
R=BASE.parent;A=R.parent.parent;F=BASE/'fuentes'
def copia(s,d):
 if d.exists():assert sha(s)==sha(d),d
 else:guardar(d,s.read_bytes())
for s,d in [(R/'el-lago-que-canta-bajo-el-hielo/mezcla.py',F/'rejilla/mezcla-lago.py'),(R/'la-corriente-devuelve-tu-nombre/instrumentos.py',F/'adaptadores/instrumentos-corriente.py'),(R/'el-lago-que-canta-bajo-el-hielo/fuentes/vocoder/sintes.py',F/'vocoder/sintes.py'),(R/'telar-de-fase/motor.py',F/'telar/motor.py')]:copia(s,d)
for f in ['g2p.js','difonos.js']:copia(R/'inferencia/vendor/difonos/runtime'/f,F/'difonos'/f)
for p in (R/'la-corriente-devuelve-tu-nombre/fuentes/hydra').iterdir():
 if p.is_file():copia(p,F/'hydra'/p.name)
subprocess.run(['python',str(A/'biblioteca-de-instrumentos/tomar.py'),'meleeviewer-10-ep','meleeviewer-15-ep','bateria-acustico','bateria-tr808','objeto-piano-goma','objeto-chelo','objeto-contrabajo','objeto-flauta','vibrafono','consola-bass','jardin-farfisa','--a',str(BASE)],check=True,env={**os.environ,'PYTHONIOENCODING':'utf-8'})
jsave(BASE/'procedencia.json',{'fuentes':{str(p.relative_to(BASE)).replace('\\','/'):sha(p) for p in F.rglob('*') if p.is_file()},'banco_local':'../inferencia/vendor/difonos/bancos/sabina-1-b44e7fab5cee','decision':'Piano bifronte: EP10 y EP15 originales de biblioteca, con MIDI fraccionario. Nuevo fuelle: modelo fenomenológico activo de lengüetas, sin atribuir calibración de bayan real.','referencia_lengüetas':'https://doi.org/10.1121/1.1852546'})
print(lib().name)
