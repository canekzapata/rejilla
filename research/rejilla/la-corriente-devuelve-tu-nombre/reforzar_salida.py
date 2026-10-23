"""Revisión por banda: más sub al volver, conservando tres versiones del máster."""
from comun import *
from scipy.signal import butter,sosfiltfilt
from partitura import figura,salva
import re
out=ultimo();tag=out.name.split('-')[-1];P=leer(out/'partitura.json');B=P['compas'];src=master(out);sr,y=wavfile.read(src);t=np.arange(len(y))/sr
low=sosfiltfilt(butter(4,[28,90],btype='bandpass',fs=sr,output='sos'),y.mean(1));gate=np.minimum(np.clip((t-88*B)/.4,0,1),np.clip((120*B-t)/.6,0,1));y+=((10**(3.5/20)-1)*low*gate)[:,None];g=min(1,.8/float(abs(y).max()));y*=g;dest=out/(out.name+'-pesada.wav');wav(dest,y,sr);aac(dest.with_suffix('.m4a'),dest)
r=subprocess.run(['ffmpeg','-hide_banner','-i',str(dest.with_suffix('.m4a')),'-af','loudnorm=I=-12.5:TP=-2.5:LRA=10:print_format=json','-f','null','-'],capture_output=True,text=True,check=True);met=json.loads(re.findall(r'\{[^{}]+\}',r.stderr)[-1]);jsave(out/'master-pesada.json',{'master':dest.name,'revision_de':src.name,'AAC':met,'refuerzo_final':{'banda_Hz':[28,90],'dB_nominal':3.5,'inicio_s':88*B,'fin_s':120*B,'normalizacion_pico_global':g,'nota':'ecualización suave de la componente central después de la lectura Rejilla; margen global único, sin compresor por sección'},'silencio_final_50ms':float(abs(y[-2400:]).max()),'versiones_conservadas':True});guardar(out/'MASTER-VIGENTE.txt',dest.name.encode('utf-8'))
for label,a,b in [('salida-pesada-final',96*B,116*B),('solo-eco-D-final',64*B,88*B),('pulgares-vocales-final',48*B,64*B)]:subprocess.run(['ffmpeg','-n','-v','error','-ss',str(a),'-i',str(dest),'-t',str(b-a),'-c:a','aac','-b:a','256k',str(out/f'{label}-s{SEED}-{tag}.m4a')],check=True)
f,ax=figura('El regreso gana peso también abajo','Revisión real del máster · +3.5 dB nominales en 28–90 Hz durante la última entrada',2)
ax[0].plot(t[::200],y[::200,0],lw=.4,color='#ab98ff');ax[0].set_xlabel('segundos');ax[1].plot(t[::200],gate[::200]*3.5,color='#ff9769');ax[1].set_xlabel('segundos');ax[1].set_ylabel('refuerzo nominal en dB');salva(f,out/'proceso'/f'06-revision-del-subgrave-s{SEED}-{tag}.png')
print(dest,met,flush=True)
