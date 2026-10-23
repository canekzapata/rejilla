"""Realización instrumental de Luciérnagas v8; cada ejecución es exclusiva."""
import sys,json,hashlib,secrets,shutil,time
from pathlib import Path
import numpy as np
BASE=Path(__file__).resolve().parent
SCORE=BASE/'luciernagas-reescritura-s1-29d4afe5aad2'
VERSION='luciernagas-realizacion-1'
SR=48000
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,d):
    with open(p,'x',encoding='utf8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=1)
def context():
    out=BASE/(BASE/'REALIZACION-ACTUAL.txt').read_text().strip()
    return out,json.loads((out/'partitura.json').read_text(encoding='utf8'))
def iniciar():
    nonce=secrets.token_hex(16);source=(SCORE/'partitura-v8.json').read_bytes()
    image=(SCORE/'luciernagas-partitura-final-s1-29d4afe5aad2.png').read_bytes()
    code=Path(__file__).read_bytes()
    ident=sha(source+image+code+VERSION.encode()+nonce.encode())
    out=BASE/('luciernagas-cancion-s1-'+ident[:12]);out.mkdir(exist_ok=False)
    (out/'render').mkdir();(out/'proceso').mkdir();(out/'partitura.json').write_bytes(source)
    dump(out/'inicio.json',dict(version=VERSION,ejecucion_sha256=ident,nonce=nonce,sr=SR,
         partitura_sha256=sha(source),imagen_sha256=sha(image),programa_inicial_sha256=sha(code)))
    (BASE/'REALIZACION-ACTUAL.txt').write_text(out.name,encoding='utf8')
    print(out,flush=True)
if __name__=='__main__':
    if sys.argv[1]=='iniciar':iniciar()
