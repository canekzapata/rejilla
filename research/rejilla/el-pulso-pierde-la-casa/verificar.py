from pathlib import Path
import json,subprocess,sys,hashlib
import numpy as np
from scipy.io import wavfile
from PIL import Image,ImageDraw
out=Path(sys.argv[1]);tag=out.name.split('-')[-1]
audio=out/f'el-pulso-pierde-la-casa-{tag}.m4a'
r=subprocess.run(['ffmpeg','-hide_banner','-i',str(audio),'-af','loudnorm=I=-14:TP=-1:LRA=9:print_format=json','-f','null','-'],capture_output=True,check=True)
log=r.stderr.decode('utf8','replace');measurement=json.JSONDecoder().raw_decode(log[log.rfind('{'):])[0]
sr,y=wavfile.read(out/f'mezcla-{tag}.wav');assert np.isfinite(y).all()
assert np.max(abs(y))<1
silences={f'{a}-{b}':float(np.max(abs(y[int(a*sr):int(b*sr)]))) for a,b in [(181.34,182.95),(190.14,193.05),(200.42,201.95)]}
assert max(silences.values())==0
gif=out/f'proceso-el-pulso-{tag}.gif';im=Image.open(gif);duration=0;sheet=Image.new('RGB',(600,945))
for j in range(im.n_frames):
 im.seek(j);duration+=im.info.get('duration',0);sheet.paste(im.convert('RGB').resize((600,315)),(0,j*315))
assert duration<=10000 and gif.stat().st_size<15*1024**2
with (out/'proceso'/f'04-revision-gif-{tag}.png').open('xb') as f:sheet.save(f,'PNG')
report=dict(loudnorm_entrada={k:measurement[k] for k in ['input_i','input_tp','input_lra']},duracion=len(y)/sr,finito=True,pico=float(abs(y).max()),silencios=silences,gif_ms=duration,gif_bytes=gif.stat().st_size,observacion='El warning de sintes2 proviene de 1/x en muestras de frecuencia cero fuera de frase; salida completa finita. No hubo escucha humana en esta verificación.')
with (out/'verificacion.json').open('x',encoding='utf8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
with (out/'huellas-entrega.json').open('x',encoding='utf8') as f:json.dump({str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p.name!='huellas-entrega.json'},f,indent=2)
print(json.dumps(report,indent=2))
