from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parent
core=(ROOT/'dist/audio/motor.mjs').read_bytes();original=ROOT.parent/'campana-padica/motor.mjs'
assert hashlib.sha256(core).hexdigest()==(hashlib.sha256(original.read_bytes()).hexdigest() if original.exists() else 'df2f9216cce60456e56d314714551b8374c49c689e04836dc142d3c9f9cfb812')
source=core.decode('utf-8').replace('export ','')+'\n'+(ROOT/'dist/audio/captacion.mjs').read_text(encoding='utf-8').replace('export ','')+'\n'+(ROOT/'dist/canciones.mjs').read_text(encoding='utf-8').replace('export ','')+'\n'+(ROOT/'audio_processor.mjs').read_text(encoding='utf-8')
subprocess.run(['node','--input-type=module','--check'],input=source.encode('utf-8'),check=True)
(ROOT/'dist/audio/paquete.mjs').write_bytes(('export const AUDIO_SOURCE='+json.dumps(source,ensure_ascii=False)+';\n').encode('utf-8'))
receipt={'motor_original':'../campana-padica/motor.mjs','motor_sha256':hashlib.sha256(core).hexdigest(),'fisica':'Copia byte por byte; Se añaden transporte, RMS y ocho aperturas de captación; la proyección espacial se procesa fuera del motor original.',
 'three_revision':'180','vendor_origen':'../../../output/jardin-esculturas/vendor','licencia':'MIT',
 'vendor_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'dist/vendor').iterdir() if p.is_file()}}
(ROOT/'PROCEDENCIA.json').write_bytes(json.dumps(receipt,ensure_ascii=False,indent=2).encode('utf-8'))
print('Motor verificado y procesador RMS preparado.')
