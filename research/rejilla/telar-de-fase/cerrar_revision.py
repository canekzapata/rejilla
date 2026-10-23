"""Final receipt, preserves all previous receipts and all run files."""
from pathlib import Path
import hashlib,json,re
from PIL import Image
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'telar-de-fase-s20261021-b17128d9b652'
TAG='s20261021-b17128d9b652'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
recipe=json.loads((OUT/f'receta-{TAG}.json').read_text(encoding='utf-8'))
hashes=json.loads((OUT/f'huellas-contenido-{TAG}.json').read_text(encoding='utf-8'))['archivos_sha256']
for p,h in hashes.items():assert sha(OUT/p)==h,p
portable=ROOT/'telar-portatil-s20261021-48d35d4afd7e'
pr=json.loads(next(portable.glob('receta-*.json')).read_text(encoding='utf-8'))
assert sha(next(portable.glob('*.html')))==pr['html_sha256']
assert sha(ROOT/'motor.py')==recipe['motor_sha256']
assert Image.open(ROOT/'og.png').size==(1200,630)
missing=[]
for p in [ROOT/'README.md',OUT/'proceso'/'README.md']:
    for href in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if '://' not in href and not (p.parent/href).exists():missing.append((p.name,href))
assert not missing,missing
audio=json.loads((OUT/f'medidas-master-{TAG}.json').read_text(encoding='utf-8'))
assert abs(float(audio['medido_aac']['input_i'])+18)<.4
browser={'fecha':'2026-10-21','url_local':'http://127.0.0.1:54199/',
 'probado':['Carga y dibujo de paquetes y forma de onda','Una vuelta con referencia: CANCELACIÓN en pantalla',
   'Nota mediante botón','Dos vueltas: vuelve la amplitud original en pantalla',
   'Frase de ocho notas y detener','Selección de vidrio y cambio de orden',
   'Guardar WAV: confirmación de receta y nuevo identificador'],
 'archivo_pcm':'WAV exportado por la misma función JS validado con lector wave y receta JSON LIST/INFO/ICMT.',
 'portatil':'Sintaxis Node aprobada, sin imports. file: bloqueado por política del navegador automatizado; no se intentó eludirla.',
 'comparacion_python_js_error_maximo':1.45e-8,
 'visuales':'Los cuatro PNGs de señal y dos capturas se revisaron visualmente. Los seis cuadros decodificados del GIF se revisaron juntos; sin traslapes. OG revisado, 1200x630.',
 'escucha':'Sin escucha humana propia; no se infiere calidad musical de las mediciones.'}
final={**recipe,'cierre_fecha':'2026-10-21','revision':browser,'master':audio,
 'gif':json.loads((OUT/f'verificacion-final-{TAG}.json').read_text(encoding='utf-8'))['gif'],
 'contenido_sha256':{str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file()},
 'programas_sha256':{p.name:sha(p) for p in sorted(ROOT.iterdir()) if p.is_file() and p.suffix in ('.py','.mjs','.html','.bat','.png','.md')},
 'portatil_vigente':pr,'borradores_portatiles':'623736f46a69 y a1e0e24c3ad6 conservados; no usar.'}
with (OUT/f'receta-final-{TAG}.json').open('x',encoding='utf-8') as f:json.dump(final,f,ensure_ascii=False,indent=2)
print(json.dumps({'huellas_comprobadas':len(hashes),'enlaces_locales':'OK','portatil':'OK','og':'1200x630',
 'master_lufs':audio['medido_aac']['input_i'],'gif':final['gif']},ensure_ascii=True))
