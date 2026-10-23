"""Primera etapa: partitura e instrumentos; no producir canción completa."""
from pathlib import Path
import numpy as np,hashlib,json,os,io,subprocess,importlib.util,sys
from scipy.io import wavfile
BASE=Path(__file__).resolve().parent
SR=32000;SEED=22;VERSION='laberinto-partitura-0.1';BPM=96;Q=60/BPM;BAR=4*Q
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def guardar(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(data)
def jsave(p,v):guardar(p,json.dumps(v,ensure_ascii=False,indent=1,allow_nan=False).encode('utf8'))
def leer(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def ultimo():return BASE/(BASE/'ULTIMA.txt').read_text(encoding='utf8').strip()
def score(out=None):
 out=out or ultimo();p=out/'PARTITURA.txt';return out/(p.read_text(encoding='utf8').strip() if p.exists() else 'partitura.json')
def depo(out=None):
 out=out or ultimo();p=out/'DEPOSITOS.txt';return out/(p.read_text(encoding='utf8').strip() if p.exists() else 'depositos.json')
def lib():return next(BASE.glob('instrumentos-*'))
def hz(m):return 440*2**((np.asarray(m)-69)/12)
def importar(p,n):
 spec=importlib.util.spec_from_file_location(n,p);mod=importlib.util.module_from_spec(spec);sys.modules[n]=mod;spec.loader.exec_module(mod);return mod
def wav(p,y,sr=SR):
 if Path(p).exists():raise FileExistsError(p)
 wavfile.write(p,sr,np.asarray(y,np.float32))
def muestra(out,name,y):
 y=np.asarray(y,np.float32);assert np.isfinite(y).all();assert len(y)/SR<45,'sólo sondas cortas en esta etapa'
 peak=float(abs(y).max());g=min(1,.78/(peak+1e-12));y*=g
 suffix='-r2' if (out/'sondas-instrumentos.json').exists() else '';p=out/(name+suffix+f'-s{SEED}-'+out.name.split('-')[-1]+'.wav');wav(p,y);subprocess.run(['ffmpeg','-n','-v','error','-i',str(p),'-ar','48000','-c:a','aac','-b:a','224k',str(p.with_suffix('.m4a'))],check=True);return {'archivo':p.with_suffix('.m4a').name,'segundos':len(y)/SR,'ganancia_seguridad':g,'pico_previo':peak}
def pan(y,p=0):
 a=(p+1)*np.pi/4;return np.column_stack([np.cos(a)*y,np.sin(a)*y])
def poner(dst,y,t,g=1,p=0):
 i=round(t*SR);j=max(0,-i);i=max(0,i);n=min(len(dst)-i,len(y)-j)
 if n>0:dst[i:i+n]+=g*(pan(y[j:j+n],p) if y.ndim==1 else y[j:j+n])
def env(n,a=.005,r=.06):
 t=np.arange(n)/SR;return np.minimum(1,t/a)*np.minimum(1,np.maximum(0,(n/SR-t)/r))
