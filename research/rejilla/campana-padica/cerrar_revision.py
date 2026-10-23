from pathlib import Path
import hashlib,json,re,wave,struct
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parent;TAG='s20261021-9b5d27254a47';OUT=ROOT/f'campana-distancias-{TAG}'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((OUT/f'receta-{TAG}.json').read_text(encoding='utf-8'));identity=json.loads((OUT/f'identidad-{TAG}.json').read_text(encoding='utf-8'))
assert identity['ejecucion_sha256']==r['ejecucion_sha256'] and sha(ROOT/'motor.mjs')==r['motor_sha256']
worklet=json.loads((OUT/f'verificacion-worklet-{TAG}.json').read_text(encoding='utf-8'));demo=json.loads((OUT/f'verificacion-demo-{TAG}.json').read_text(encoding='utf-8'))
assert worklet['processorVsOfflineMaxError']==0 and demo['maxError']==0
wav=OUT/worklet['exportedWav'];w=wave.open(str(wav));assert (w.getnchannels(),w.getframerate(),w.getnframes())==(2,48000,20480)
data=wav.read_bytes();i=data.index(b'ICMT');n=struct.unpack('<I',data[i+4:i+8])[0];embedded=json.loads(data[i+8:i+8+n-1])
assert len(embedded['ejecucion_sha256'])==64
assert embedded['pcm16_sha256']==hashlib.sha256(data[44:44+20480*4]).hexdigest()
portable=ROOT/'campana-portatil-s20261021-9b96e17a6f4f';pr=json.loads(next(portable.glob('receta-*.json')).read_text(encoding='utf-8'))
assert sha(portable/pr['archivo'])==pr['html_sha256'] and sha(ROOT/'og.png')==pr['imagen_sha256']
assert Image.open(ROOT/'og.png').size==(1200,630)
missing=[]
for path in [ROOT/'README.md',OUT/'proceso'/'README.md']:
 for href in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
  if '://' not in href and not (path.parent/href).exists():missing.append(href)
assert not missing,missing
gif=json.loads((OUT/f'verificacion-proceso-{TAG}.json').read_text(encoding='utf-8'))
assert gif['duracion_s']<=10 and gif['bytes']<15*1024**2 and gif['loop']==0
# Decode all frames for the final visual check; never replace a delivery image.
g=Image.open(OUT/gif['gif']);sheet=Image.new('RGB',(1440,600),'#17151d')
for i in range(g.n_frames):g.seek(i);sheet.paste(ImageOps.pad(g.convert('RGB'),(480,300),color='#17151d'),((i%3)*480,(i//3)*300))
(ROOT/'render').mkdir(exist_ok=True)
with (ROOT/'render'/f'revision-gif-{TAG}.png').open('xb') as f:sheet.save(f,format='PNG')
browser={'fecha':'2026-10-21','url':'http://127.0.0.1:54305/',
 'observado':['Interfaz, golpe en zona 9 y vibración real','Golpes y cambios de controles durante uso de la interfaz','Grabación interna de 25 s guardada con confirmación visible'],
 'consola':'Sin errores ni advertencias en la revisión hecha con el motor activo.',
 'portatil':'Sintaxis del HTML y Worklet comprobadas; procesador autosuficiente en Blob. No se probó file: por la política HTTP/HTTPS del navegador automatizado.',
 'incidencia_ui':'Al acomodar una captura se movió el apagado accidentalmente; se restauró a 0.55 y se informó a Canek.',
 'escucha':'No hubo escucha humana propia.'}
final={**r,'revision_navegador':browser,'verificacion_demo':demo,'verificacion_grabacion':{'lector_wav':'2 canales, 48 kHz, 20480 cuadros, PCM16; huella PCM correcta','error_worklet_vs_motor':0},
 'gif':gif,'portatil':pr,'contenido_sha256':{str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file()},
 'programas_sha256':{p.name:sha(p) for p in sorted(ROOT.iterdir()) if p.is_file() and (p.suffix in ('.py','.mjs','.md','.html','.bat','.png') or p.name in ('.gitignore','.gitattributes'))}}
with (OUT/f'receta-final-{TAG}.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(final,f,ensure_ascii=False,indent=2)
print(json.dumps({'gif':gif,'enlaces':'OK','identidad':'OK','WAV_y_receta':'OK','portatil':'OK','archivos_con_huella':len(final['contenido_sha256'])},ensure_ascii=True))
