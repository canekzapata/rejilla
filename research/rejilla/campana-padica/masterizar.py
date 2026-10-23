from pathlib import Path
import json,subprocess
ROOT=Path(__file__).resolve().parent;TAG='s20261021-9b5d27254a47';OUT=ROOT/f'campana-distancias-{TAG}'
def measure(p):
 r=subprocess.run(['ffmpeg','-hide_banner','-i',str(p),'-af','loudnorm=I=-18:TP=-2:LRA=11:print_format=json','-f','null','-'],capture_output=True,check=True)
 s=r.stderr.decode('utf-8',errors='replace');return json.JSONDecoder().raw_decode(s[s.rfind('{'):])[0]
src=OUT/f'la-campana-aprende-otra-distancia-{TAG}.wav';dest=OUT/f'la-campana-aprende-otra-distancia-master-{TAG}.m4a'
if dest.exists():raise FileExistsError(dest)
m=measure(src);filt='loudnorm=I=-18:TP=-2:LRA=11:linear=true:'+':'.join(f'{k}={m[v]}' for k,v in [('measured_I','input_i'),('measured_TP','input_tp'),('measured_LRA','input_lra'),('measured_thresh','input_thresh'),('offset','target_offset')])
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-n','-i',str(src),'-af',filt,'-ar','48000','-c:a','aac','-b:a','192k',str(dest)],check=True)
final=measure(dest);receipt={'archivo':dest.name,'original':src.name,'objetivo_lufs':-18,'medido_aac':final,'previo':m,'alcance':'Máster de escucha; muestras y motor conservan ganancia original.'}
with (OUT/f'medidas-master-{TAG}.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
print(json.dumps(receipt))
