from pathlib import Path
import sys,json,subprocess,hashlib
from scipy.io import wavfile
import numpy as np
out=Path(sys.argv[1]);tag=out.name.split('-')[-1];src=out/f'mezcla-{tag}.wav'
master=out/f'la-fase-vuelve-distinta-v2-{tag}.m4a'
# The raw mix was already peak-normalized; leave headroom for AAC intersample peaks.
subprocess.run(['ffmpeg','-v','error','-n','-i',str(src),'-af','volume=-2dB,alimiter=limit=0.64:attack=5:release=60:level=false:latency=true','-c:a','aac','-b:a','256k',str(master)],check=True)
r=subprocess.run(['ffmpeg','-hide_banner','-i',str(master),'-af','loudnorm=I=-14:TP=-1:LRA=9:print_format=json','-f','null','-'],capture_output=True,check=True);log=r.stderr.decode('utf8','replace');m=json.JSONDecoder().raw_decode(log[log.rfind('{'):])[0]
assert float(m['input_tp']) < -0.8
y=wavfile.read(src)[1];assert np.isfinite(y).all()
with (out/'verificacion-v2.json').open('x') as f:json.dump(dict(duracion=len(y)/24000,pico=float(abs(y).max()),input_lufs=m['input_i'],input_tp=m['input_tp'],input_lra=m['input_lra'],finito=True,escucha_humana=False,sha256=hashlib.sha256(master.read_bytes()).hexdigest()),f,indent=2)
print(master,m['input_i'],m['input_tp'],m['input_lra'])
