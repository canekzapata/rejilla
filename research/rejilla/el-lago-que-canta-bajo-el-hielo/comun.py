"""Archivos exclusivos y señales de El lago. Ningún artefacto se pisa."""
from pathlib import Path
import hashlib,json,math,subprocess
import numpy as np
from scipy.io import wavfile
BASE=Path(__file__).resolve().parent
SR=32768
SEED=227
VERSION='lago-1.0.0'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def guardar(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(data)
def jguardar(p,x):guardar(p,json.dumps(x,ensure_ascii=False,indent=1,allow_nan=False).encode('utf-8'))
def jleer(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def ultimo():return BASE/(BASE/'ULTIMA.txt').read_text(encoding='utf-8').strip()
def hz(m):return 440*2**((np.asarray(m)-69)/12)
def midi(f):return 69+12*np.log2(np.asarray(f)/440)
def pan(y,p=0):
 a=(p+1)*np.pi/4;return np.column_stack([y*np.cos(a),y*np.sin(a)]).astype('float32')
def poner(dst,y,t,g=1,p=0,sr=SR):
 i=round(t*sr);off=max(0,-i);i=max(0,i);n=min(len(y)-off,len(dst)-i)
 if n>0:dst[i:i+n]+=g*(pan(y[off:off+n],p) if y.ndim==1 else y[off:off+n])
def env(n,a=.01,r=.06,sr=SR):
 t=np.arange(n)/sr;return np.sin(np.minimum(1,t/max(a,1/sr))*np.pi/2)**2*np.sin(np.minimum(1,(n/sr-t)/max(r,1/sr))*np.pi/2)**2
def wav(p,y,sr=SR):
 if Path(p).exists():raise FileExistsError(p)
 wavfile.write(p,sr,np.asarray(y,dtype='float32'))
def aac(p,y,lufs=-16,sr=SR):
 p=Path(p);w=p.with_suffix('.wav');wav(w,y,sr)
 r=subprocess.run(['ffmpeg','-n','-v','error','-i',str(w),'-af',f'loudnorm=I={lufs}:TP=-1.8:LRA=9','-ar','48000','-c:a','aac','-b:a','256k',str(p)],capture_output=True,text=True)
 if r.returncode:raise RuntimeError(r.stderr)
def activo(y):
 x=np.asarray(y);x=np.mean(x*x,axis=1) if x.ndim==2 else x*x;n=len(x)//1024*1024
 rms=np.sqrt(np.mean(x[:n].reshape(-1,1024),axis=1));v=rms[rms>max(1e-8,rms.max()*.035)]
 return float(np.sqrt(np.mean(v*v))) if len(v) else 0.
