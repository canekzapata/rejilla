from comun import *
from laminas import figura
import matplotlib.pyplot as plt
from fractions import Fraction
ratio=Fraction(3,2)**4/(4*Fraction(5,4));assert ratio==Fraction(81,80)
t=np.arange(SR*6)/SR;a=np.sin(2*np.pi*110*t);b=np.sin(2*np.pi*111.375*t);f,ax=figura('El mismo La vuelve con otra afinación','81/80 · 21.506 cents · 110 y 111.375 Hz · un batido de 82.5 BPM',2)
ax[0].plot(t[::128],(a+b)[::128],lw=.5,color='#e9b46e');ax[0].plot(t[::128],2*np.abs(np.cos(np.pi*1.375*t[::128])),color='#79c1bd',lw=1);ax[0].set_xlim(0,6);ax[0].set_xlabel('segundos');ax[0].set_title('Dos señales calculadas, envolvente analítica')
ratios=[1,1.5,1.125,1.6875,1.265625,1.0125];ax[1].plot(range(6),np.array(ratios)*110,'o-',color='#79c1bd');ax[1].set_xticks(range(6),['A','E','B','F#','C#','A']);ax[1].set_ylabel('Hz');ax[1].set_title('El recorrido no cierra a 110 Hz')
buf=io.BytesIO();f.savefig(buf,format='png',dpi=100);plt.close(f);nonce=os.urandom(24).hex();h=hashlib.sha256(buf.getvalue()+VERSION.encode()+nonce.encode()+Path(__file__).read_bytes()).hexdigest();out=BASE/f'el-acorde-s{SEED}-{h[:12]}';out.mkdir(exist_ok=False);(out/'proceso').mkdir();(BASE/'render'/h[:12]).mkdir(parents=True,exist_ok=False)
guardar(out/'proceso'/f'01-coma-y-batido-s{SEED}-{h[:12]}.png',buf.getvalue());jsave(out/'ejecucion.json',{'hash':h,'nonce':nonce,'version':VERSION,'semilla':SEED,'imagen_sha256':hashlib.sha256(buf.getvalue()).hexdigest(),'ratio':[81,80],'coma_cents':float(CENTS),'batido_Hz':1.375,'bpm':82.5,'fecha_local':'2026-10-21'});(BASE/'ULTIMA.txt').write_bytes(out.name.encode('utf-8'));print(out)
