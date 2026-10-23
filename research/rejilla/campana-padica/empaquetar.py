"""Build AudioWorklet bundle and exclusive standalone HTML. UTF-8, no overwrite."""
from pathlib import Path
import hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parent
engine=(ROOT/'motor.mjs').read_text(encoding='utf-8').replace('export ','')
worklet=(ROOT/'worklet.mjs').read_text(encoding='utf-8')
archive=(ROOT/'archivo.mjs').read_text(encoding='utf-8').replace('export ','')
interface='\n'.join(s for s in (ROOT/'interfaz.mjs').read_text(encoding='utf-8').splitlines() if not s.startswith('import '))
source=engine+'\n'+worklet
bundle='export const WORKLET_SOURCE='+json.dumps(source,ensure_ascii=False)+';\n'
# This is source for the current program, not an output run or historical draft.
(ROOT/'paquete.mjs').write_text(bundle,encoding='utf-8')
script='const WORKLET_SOURCE='+json.dumps(source,ensure_ascii=False)+';\n'+archive+'\n'+interface
subprocess.run(['node','--input-type=module','--check'],input=script.encode('utf-8'),check=True)
subprocess.run(['node','--input-type=module','--check'],input=source.encode('utf-8'),check=True)
html=(ROOT/'index.html').read_text(encoding='utf-8').replace('<script type="module" src="interfaz.mjs"></script>','<script type="module">\n'+script+'\n</script>')
html=html.replace('href="README.md"','href="../README.md"').replace('href="favicon.png"','href="../favicon.png"')
data=html.encode('utf-8');nonce=os.urandom(24);pic=(ROOT/'og.png').read_bytes() if (ROOT/'og.png').exists() else engine.encode('utf-8')
full=hashlib.sha256(data+pic+b'1.0.0'+nonce).hexdigest();out=ROOT/f'campana-portatil-s20261021-{full[:12]}';out.mkdir(exist_ok=False)
name=f'campana-padica-s20261021-{full[:12]}.html'
with (out/name).open('xb') as f:f.write(data)
receipt={'version':'1.0.0','semilla':20261021,'ejecucion_sha256':full,'nonce_hex':nonce.hex(),'html_sha256':hashlib.sha256(data).hexdigest(),
 'imagen_sha256':hashlib.sha256(pic).hexdigest(),'identidad':'SHA256(HTML + imagen OG o motor si no existe + versión + nonce)','archivo':name}
with (out/f'receta-portatil-{full[:12]}.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
print(out)
