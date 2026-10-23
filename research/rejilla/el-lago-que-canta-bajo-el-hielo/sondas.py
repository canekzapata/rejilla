"""Pruebas de señal independientes de la composición; escribe una sola vez por entrega."""
from comun import *
from hielo import *
from laminas import *
from scipy.signal import butter,sosfiltfilt
def main():
 out=ultimo();tag=out.name.split('-')[-1];red=jleer(out/'red.json');alpha=red['alpha'];sr=SR
 red_lamina(red,out/'proceso'/f'02-red-y-memoria-s227-{tag}.png')
 n=3*sr;t=np.arange(n)/sr;f=np.fft.rfftfreq(n,1/sr);x=np.zeros(n);x[sr]=1
 prepared=np.fft.irfft(np.fft.rfft(x)*np.exp(1j*23*np.sqrt(2*np.pi*f/alpha)),n)
 arrived=dispersar(prepared,23,alpha,0,sr,False);ref=np.fft.irfft(np.fft.rfft(x)*banda(f),n)
 error=float(np.linalg.norm(arrived-ref)/np.linalg.norm(ref))
 widths=[];centros=[];ys=[]
 for l in [0,.5,1]:
  y=dispersar(x,23,alpha,l,sr,False);energy=y*y;mu=float(t@energy/energy.sum());sigma=float(np.sqrt(((t-mu)**2)@energy/energy.sum()));widths.append(sigma);ys.append(y)
 for fc in [300,1200,4800]:
  packet=np.sin(2*np.pi*fc*(t-1))*np.exp(-((t-1)/.025)**2);y=dispersar(packet,23,alpha,0,sr,False);mu=float(t@(y*y)/sum(y*y))-1;expected=23/(2*np.sqrt(alpha*2*np.pi*fc));centros.append({'Hz':fc,'retardo_medido':mu,'teorico':float(expected),'error_s':mu-expected})
 mod=red['modos'][str(red['placas'][0]['id'])];a=arco(mod,64,2,.25);b=arco(mod,64,2,.8)
 medidas={'fase_compensada_error_relativo':error,'anchuras_rms_s':widths,'bandas':centros,'arco_diferencia_presion':float(np.linalg.norm(a-b)),'arco_picos':[float(abs(a).max()),float(abs(b).max())],'red_estados_diferentes_Hz':float(np.linalg.norm(np.array(red['estados'][0]['frecuencias'])-red['estados'][-1]['frecuencias']))}
 assert error<1e-10 and widths[-1]<widths[0]/5 and all(abs(q['error_s'])<.003 for q in centros) and np.linalg.norm(a-b)>1e-3
 jguardar(out/'sondas.json',medidas)
 demo=[]
 for r in [3,12,23]:demo.append(fractura(r,alpha)*.8);demo.append(np.zeros(round(.25*sr)))
 aac(out/f'tres-distancias-s227-{tag}.m4a',np.concatenate(demo),-19)
 demo=[]
 for l in [0,.5,1]:demo.extend([fractura(23,alpha,l),np.zeros(round(.2*sr))])
 aac(out/f'reunir-la-grieta-s227-{tag}.m4a',np.concatenate(demo),-19)
 aac(out/f'arco-presion-s227-{tag}.m4a',np.concatenate([a,np.zeros(sr//2),b]),-19)
 fig,axs=figura('Idea D · componer la llegada','Misma distancia · compensación de fase 0 → ½ → 1 · prueba calculada',2)
 for l,y in zip([0,.5,1],ys):axs[0].plot(t,y,label=f'λ={l}',alpha=.8)
 axs[0].set_xlim(.95,1.25);axs[0].legend(facecolor=BG,labelcolor=FG);axs[0].set_xlabel('segundos');axs[0].set_title('La energía vuelve a coincidir',color=FG)
 axs[1].plot([q['Hz'] for q in centros],[q['retardo_medido']*1000 for q in centros],'o-',color=C[0]);axs[1].set_xscale('log');axs[1].set_ylabel('retardo medido (ms)');axs[1].set_xlabel('frecuencia (Hz)');salva(fig,out/'proceso'/f'03-dispersion-y-enfoque-s227-{tag}.png')
 print(json.dumps(medidas,indent=1))
if __name__=='__main__':main()
