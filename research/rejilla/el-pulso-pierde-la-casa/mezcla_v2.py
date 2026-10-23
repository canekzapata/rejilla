from pathlib import Path
import sys,json,subprocess,hashlib
import numpy as np
from scipy.io import wavfile
out=Path(sys.argv[1]);tag=out.name.split('-')[-1];sr=24000
S={k:wavfile.read(out/'render'/f'{k}-{tag}.wav')[1] for k in ['solistas','chelo','bajo','vocoder','sinte','percusion']}
# Preserve crisp front percussion while restoring the lead's active level.
gain=np.ones(len(S['percusion']),np.float32)
for a,z,db in [(0,42,-2),(58,82,0),(82,108,-4),(108,138,-3),(138,165,0),(165,202,-4)]:
 i=int(a*sr);j=int(z*sr);g=10**(db/20);gain[i:j]=g
 # A short ramp prevents bus-gain steps at structural boundaries.
 n=min(int(.025*sr),j-i)
 if i>0:gain[i:i+n]=np.linspace(gain[i-1],g,n)
y=S['percusion']*gain[:,None]+S['solistas']*1.5+S['chelo']*1.15+S['bajo']+S['vocoder']*1.2+S['sinte']*1.4
for a,z in [(181.3,183),(190.1,193.1),(200.38,202)]:
 i=int(a*sr);j=int(z*sr);n=int(.012*sr);y[i:i+n]*=np.linspace(1,0,n)[:,None];y[i+n:j]=0
y*=.8/abs(y).max();assert np.isfinite(y).all()
wav=out/f'mezcla-v2-{tag}.wav'
with wav.open('xb') as f:wavfile.write(f,sr,y.astype(np.float32))
master=out/f'el-pulso-pierde-la-casa-v2-{tag}.m4a'
subprocess.run(['ffmpeg','-v','error','-n','-i',str(wav),'-af','volume=4dB,alimiter=limit=0.70:attack=3:release=55:level=false:latency=true','-c:a','aac','-b:a','256k',str(master)],check=True)
r=subprocess.run(['ffmpeg','-hide_banner','-i',str(master),'-af','loudnorm=I=-14:TP=-1:LRA=9:print_format=json','-f','null','-'],capture_output=True,check=True);s=r.stderr.decode('utf8','replace');m=json.JSONDecoder().raw_decode(s[s.rfind('{'):])[0]
with (out/'verificacion-v2.json').open('x') as f:json.dump(dict(lufs=m['input_i'],true_peak=m['input_tp'],lra=m['input_lra'],finito=True,duracion=len(y)/sr,sha256=hashlib.sha256(master.read_bytes()).hexdigest()),f,indent=2)
print(master,m['input_i'],m['input_tp'],m['input_lra'])
