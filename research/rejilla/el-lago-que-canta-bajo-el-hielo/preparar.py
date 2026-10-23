"""Fija motores originales y exporta la lámina; correr una vez."""
from pathlib import Path
import shutil,subprocess,os
from comun import BASE,jguardar,sha
R=BASE.parent;MT=R.parent/'montanas-topograficas';F=BASE/'fuentes'
def copia(src,dest):
 dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.exists():
  if dest.read_bytes()==src.read_bytes():return
  raise FileExistsError(dest)
 with dest.open('xb') as w:w.write(src.read_bytes())
for name in ['nucleo.js','terreno.js']:copia(MT/name,F/'traspuesta'/name)
for carpeta in ['telar-de-fase','instrumentos-de-tres-tiempos']:
 name='motor.py' if carpeta=='telar-de-fase' else 'motores.py';copia(R/carpeta/name,F/carpeta/name)
copia(R/'monodromia-berry-ep2/monodromia_berry_ep2.py',F/'ep2/motor.py')
copia(R/'cuento-en-siete/sintes.py',F/'vocoder/sintes.py')
lib=R.parent.parent/'biblioteca-de-instrumentos'
subprocess.run(['python',str(lib/'tomar.py'),'bateria-tr808','bateria-frito','objeto-chelo','objeto-clarinete','objeto-trombon-plunger','objeto-piano-tornillo','--a',str(BASE)],check=True,env={**os.environ,'PYTHONIOENCODING':'utf-8'})
jguardar(BASE/'procedencia.json',{str(p.relative_to(BASE)).replace('\\','/'):sha(p) for p in F.rglob('*') if p.is_file()})
subprocess.run(['node',str(BASE/'exportar.cjs'),str(BASE/'terreno')],check=True)
