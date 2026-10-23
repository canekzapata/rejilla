from pathlib import Path
import json,sys,subprocess,hashlib
import numpy as np
out=Path(sys.argv[1]);tag=out.name.split('-')[-1];p=out/f'otra-vez-hasta-romper-master-v2-s18102692-{tag}.m4a'
def run(x):return subprocess.run(x,check=True,capture_output=True)
s=run(['ffmpeg','-v','info','-i',str(p),'-af','loudnorm=I=-13:TP=-1.6:LRA=10:print_format=json','-f','null','-']).stderr.decode(errors='replace');m=json.JSONDecoder().raw_decode(s[s.rfind('{'):])[0];assert float(m['input_tp'])<-.8
z=np.frombuffer(run(['ffmpeg','-v','error','-i',str(p),'-f','f32le','-ac','2','-ar','24000','pipe:1']).stdout,dtype='<f4').reshape(-1,2);assert np.isfinite(z).all()
P=json.loads((out/'partitura.json').read_text('utf8'));i=int(P['golpe_final']*24000);j=int(P['corte']*24000)
stats=dict(aac=m,proceso='mezcla.wav -> volume=4dB, alimiter limit=.75 attack=5 release=50 level=false latency=true -> AAC 256k 48kHz',duracion_decodificada=len(z)/24000,golpe_rms=float(np.sqrt(np.mean(z[i:j]**2))),ultimos_20ms_rms=float(np.sqrt(np.mean(z[-480:]**2))))
with (out/'master-v2-medidas.json').open('x',encoding='utf8') as f:json.dump(stats,f,ensure_ascii=False,indent=2)
excerpt=out/f'cierre-bucles-s18102692-{tag}.m4a';run(['ffmpeg','-n','-v','error','-ss','151','-i',str(p),'-c:a','aac','-b:a','192k',str(excerpt)])
with (out/'MASTER-V2.md').open('x',encoding='utf8') as f:f.write(f'# Entrega vigente: máster v2\n\n[Escuchar]({p.name}) · [Escuchar sólo el cierre]({excerpt.name}).\n\n{m["input_i"]} LUFS, pico {m["input_tp"]} dBTP, LRA {m["input_lra"]}. La primera exportación se conserva: −18.05 LUFS. La v2 usa +4 dB sobre la mezcla y limitador de picos con techo .75, ataque 5 ms, recuperación 50 ms y compensación de latencia. No cambia eventos ni orden. Mediciones del AAC efectivamente entregado en master-v2-medidas.json.\n\nEl GIF de 7.8 s muestra las etapas compositivas hasta la mezcla anterior al máster; la hoja 04 es control visual de sus cuadros. La masterización posterior no está representada como una etapa adicional del GIF. Sin escucha humana durante producción.\n')
print(json.dumps(stats))
