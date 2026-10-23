"""Build a standalone offline HTML; never overwrites a previous build."""
from pathlib import Path
import hashlib,json,os,subprocess

HERE=Path(__file__).resolve().parent
html=(HERE/'index.html').read_text(encoding='utf-8')
engine=(HERE/'motor.mjs').read_text(encoding='utf-8').replace('export ','')
archive=(HERE/'archivo.mjs').read_text(encoding='utf-8').replace('export ','')
interface='\n'.join(line for line in (HERE/'interfaz.mjs').read_text(encoding='utf-8').splitlines() if not line.startswith('import '))
script=engine+'\n'+archive+'\n'+interface
subprocess.run(['node','--input-type=module','--check'],input=script.encode('utf-8'),check=True)
html=html.replace('<script type="module" src="interfaz.mjs"></script>','<script type="module">\n'+script+'\n</script>')
html=html.replace('href="README.md"','href="../README.md"').replace('href="favicon.png"','href="../favicon.png"')
data=html.encode('utf-8');nonce=os.urandom(24)
image=(HERE/'og.png').read_bytes()
full=hashlib.sha256(data+image+b'1.0.0'+nonce).hexdigest()
out=HERE/f'telar-portatil-s20261021-{full[:12]}';out.mkdir(exist_ok=False)
with (out/f'telar-de-fase-s20261021-{full[:12]}.html').open('xb') as f:f.write(data)
recipe={'version':'1.0.0','semilla':20261021,'ejecucion_sha256':full,'nonce_hex':nonce.hex(),
 'identidad':'SHA256(HTML autónomo + og.png + versión + nonce)',
 'html_sha256':hashlib.sha256(data).hexdigest(),'og_sha256':hashlib.sha256(image).hexdigest(),
 'uso':'Abrir el HTML en tu navegador. Funciona sin servidor, sin conexión y sin dependencias.'}
with (out/f'receta-portatil-{full[:12]}.json').open('x',encoding='utf-8') as f:json.dump(recipe,f,ensure_ascii=False,indent=2)
print(out)
