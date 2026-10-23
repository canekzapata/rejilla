"""El acorde vuelve con otro cuerpo: archivos exclusivos y señales."""
from pathlib import Path
import numpy as np
import hashlib,json,os,subprocess,io,importlib.util,sys
from scipy.io import wavfile
BASE=Path(__file__).resolve().parent
SR=32768
SEED=21102681
VERSION='acorde-1.0.0'
COMA=81/80
CENTS=1200*np.log2(COMA)
Q=1/(111.375-110)
BAR=4*Q
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def guardar(p,b):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def jsave(p,x):guardar(p,json.dumps(x,ensure_ascii=False,indent=1,allow_nan=False).encode('utf-8'))
def leer(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def ultimo():return BASE/(BASE/'ULTIMA.txt').read_text(encoding='utf-8').strip()
def run():return BASE/'render'/ultimo().name.split('-')[-1]
def lib():return next(BASE.glob('instrumentos-*'))
def master(out=None):
 out=out or ultimo();return out/(out.name+'.wav')
def hz(m):return 440*2**((np.asarray(m)-69)/12)
def midi(f):return 69+12*np.log2(np.asarray(f)/440)
def pan(y,p=0):
 a=(p+1)*np.pi/4;return np.column_stack([y*np.cos(a),y*np.sin(a)]).astype('float32')
def poner(dst,y,t,g=1,p=0):
 i=round(t*SR);a=max(0,-i);i=max(0,i);n=min(len(y)-a,len(dst)-i)
 if n>0:dst[i:i+n]+=g*(pan(y[a:a+n],p) if y.ndim==1 else y[a:a+n])
def env(n,a=.01,r=.1):
 t=np.arange(n)/SR;return np.minimum(1,t/a)**2*np.minimum(1,(n/SR-t)/r)**2
def wav(p,y,sr=SR):
 if Path(p).exists():raise FileExistsError(p)
 wavfile.write(p,sr,np.asarray(y,dtype='float32'))
def raw(c,y):guardar(run()/(c+'.f32'),np.asarray(y,dtype='float32').tobytes())
def importar(p,n='fuente'):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def aac(p,w):subprocess.run(['ffmpeg','-n','-v','error','-i',str(w),'-c:a','aac','-b:a','256k','-movflags','+faststart',str(p)],check=True)
def activo(x):
 z=np.mean(x*x,axis=1) if x.ndim==2 else x*x;n=len(z)//1024*1024;r=np.sqrt(z[:n].reshape(-1,1024).mean(1));r=r[r>max(1e-9,r.max()*.04)]
 return float(np.sqrt(np.mean(r*r))) if len(r) else 0.
