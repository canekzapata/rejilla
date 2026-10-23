from pathlib import Path
import hashlib,uuid,json,shutil,io,sys
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent;SEED=1;VERSION='partitura-pantano-1.0'
expl=ROOT/sys.argv[1]
image=next(expl.glob('traspuesta-s1-*.png')).read_bytes();nonce=uuid.uuid4().hex
program=b''.join((ROOT/f).read_bytes() for f in ['iniciar.py','instrumentos.py','seleccionar.cjs'])
full=hashlib.sha256(image+VERSION.encode()+program+nonce.encode()).hexdigest();tag=full[:12]
out=ROOT/f'luciernagas-partitura-s{SEED}-{tag}';out.mkdir(exist_ok=False)
for f in ['proceso','fuentes','datos']: (out/f).mkdir()
def put(name,data):
 p=out/name
 with p.open('xb') as f:f.write(data)
def js(name,data):put(name,json.dumps(data,ensure_ascii=False,indent=1).encode('utf8'))
put(f'proceso/01-visor-elegido-s1-{tag}.png',image)
for s in [27,43]:put(f'datos/comparada-s{s}-{tag}.png',next(expl.glob(f'traspuesta-s{s}-*.png')).read_bytes())
put('datos/consulta-atlas.json',(expl/'consulta-atlas.json').read_bytes())
put('datos/exploracion.json',(expl/'exploracion.json').read_bytes())
T=json.loads((expl/'terreno-s1.json').read_text('utf8'))
import numpy as np
put('datos/alturas-s1.f32',np.asarray(T.pop('h'),np.float32).tobytes());js('datos/terreno-s1.json',T)
put('datos/lamina-original-s1.svg',next(expl.glob('lamina-s1-*.svg')).read_bytes())
for f in ['iniciar.py','instrumentos.py','seleccionar.cjs']:put('fuentes/'+f,(ROOT/f).read_bytes())
for name in ['nucleo.js','terreno.js','lamina.js','visor.js','ver.html']:
 put('fuentes/traspuesta-'+name,(expl/'fuentes'/name).read_bytes())
base=ROOT.parent
for f in ['COMPOSITOR.md','LECTURA-POEMARIO-PANTANO-2026-10-22.md','MATEMATICAS-PARA-COMPONER-2026-10-22.md']:
 put('fuentes/'+f,(base/f).read_bytes())
for f in ['el-rio-no-tiene-tronco/partitura.py','el-androide-en-la-estacion/partitura.py','el-androide-en-la-estacion/render_tt.py','instrumentos-de-tres-tiempos/motores.py']:
 put('fuentes/'+f.replace('/','__'),(base/f).read_bytes())
poems=base.parent.parent/'netart/poemario/poemas de canek.txt'
put('fuentes/poemas-de-canek.txt',poems.read_bytes())
js('receta-inicial.json',{'version':VERSION,'semilla_terreno':SEED,'semilla_composicion':2026102201,
 'id_completo':full,'id':tag,'nonce':nonce,'imagen_origen_sha256':hashlib.sha256(image).hexdigest(),
 'codigo_inicial_sha256':hashlib.sha256(program).hexdigest(),'seleccion':'visor real de Traspuesta, tres láminas comparadas; elegida s1',
 'orientacion':'u al este, v al sur, origen esquina noroeste del campo; la proyección de la lámina tiene otra rotación',
 'no_sobrescribir':True,'etapa':'partitura e instrumentos; sin audio, máster, visor nuevo o video de canción'})
with (ROOT/'ULTIMA.txt').open('x',encoding='utf8') as f:f.write(out.name+'\n')
print(out)
