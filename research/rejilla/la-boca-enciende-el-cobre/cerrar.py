from pathlib import Path
import sys,json,hashlib
R=Path(__file__).resolve().parent;out=Path(sys.argv[1]).resolve()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['revisar.py','balance.py','cerrar.py','README.md']:
 target=out/'fuentes'/name
 if target.exists():
  assert target.read_bytes()==(R/name).read_bytes()
 else:
  with target.open('xb') as f:f.write((R/name).read_bytes())
initial=json.loads((out/'receta-inicial.json').read_text('utf8'));qa=json.loads((out/'revision-entrega.json').read_text('utf8'))
assert qa['master']['fuentes_originales_intactas'] and float(qa['master']['pico_verdadero'])<-.8
assert all(sha(R.parent/k)==v for k,v in initial['fuentes'].items())
with (out/'receta-entrega.json').open('x',encoding='utf8') as f:json.dump(dict(hash_ejecucion=initial['hash_ejecucion'],semilla=initial['semilla'],nonce=initial['nonce'],fuentes_originales_intactas=True,archivos={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and p.name!='receta-entrega.json'}),f,ensure_ascii=False,indent=2)
print('Entrega cerrada y fuentes originales verificadas')
