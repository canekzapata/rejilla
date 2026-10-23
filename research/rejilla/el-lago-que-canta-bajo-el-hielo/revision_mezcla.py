"""Otra ejecución exclusiva que conserva la misma interpretación y revisa la mezcla.
Reutiliza copias exclusivas de señales de trabajo; no modifica los originales.
"""
import os,hashlib,shutil
from comun import *
old=ultimo();tag0=old.name.split('-')[-1];nonce=os.urandom(20).hex();initial=next((old/'proceso').glob('01-*.png')).read_bytes()
full=hashlib.sha256(initial+VERSION.encode()+(BASE/'mezcla.py').read_bytes()+nonce.encode()).hexdigest();tag=full[:12]
out=BASE/f'el-lago-que-canta-s227-{tag}';out.mkdir(exist_ok=False);(out/'proceso').mkdir();run=BASE/'render'/tag;run.mkdir(exist_ok=False)
for name in ['red.json','partitura.json','sondas.json','ep2-traza.json','regiones-227.i32']:guardar(out/name,(old/name).read_bytes())
for p in (old/'proceso').glob('*.png'):
 if int(p.name[:2])<=4:guardar(out/'proceso'/p.name.replace(tag0,tag),p.read_bytes())
for p in old.glob('*.m4a'):
 if p.name.startswith(('tres-distancias','reunir-la-grieta','arco-presion')):guardar(out/p.name.replace(tag0,tag),p.read_bytes())
count=0
for p in (BASE/'render'/tag0).glob('*.f32'):
 if 'procesado' in p.name or '.grupo.' in p.name:continue
 with p.open('rb') as r,(run/p.name).open('xb') as w:shutil.copyfileobj(r,w,1024*1024)
 count+=1
jguardar(out/'ejecucion.json',{'hash':full,'nonce':nonce,'version':VERSION,'semilla':SEED,'png_inicial_sha256':hashlib.sha256(initial).hexdigest(),'revision_de':old.name,'reutiliza':'misma partitura y señales crudas; PNG 01–04 y tres muestras conservan las capturas y señales originales; se recalcula la mezcla','senales_reutilizadas':count})
(BASE/'ULTIMA.txt').write_text(out.name,encoding='utf-8');print(out)
