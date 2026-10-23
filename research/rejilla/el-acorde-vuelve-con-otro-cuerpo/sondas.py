"""Medir motores reales antes de aceptar la orquestación. No sustituye una escucha."""
from comun import *
from laminas import *
from scipy.signal import butter,sosfiltfilt,hilbert,find_peaks,resample_poly
def frecuencia(y,lo,hi):
 n=len(y);Z=abs(np.fft.rfft(y*np.hanning(n),n=n*4));f=np.fft.rfftfreq(n*4,1/SR);ix=np.where((f>lo)&(f<hi))[0];k=ix[np.argmax(Z[ix])];v=np.log(Z[k-1:k+2]+1e-20);d=.5*(v[0]-v[2])/(v[0]-2*v[1]+v[2]);return float((k+d)*SR/(n*4))
def main():
 out=ultimo();R=run();tag=out.name.split('-')[-1];xs=[np.fromfile(R/(n+'.f32'),np.float32) for n in ['prueba-ep10','prueba-ep15','prueba-ep-coma']];F=[frecuencia(x[SR:9*SR],100,120) for x in xs]
 for f,target in zip(F,[110,110,111.375]):assert abs(f-target)<.03,(f,target)
 z=xs[0]+xs[2];bp=sosfiltfilt(butter(3,[100,125],btype='bandpass',fs=SR,output='sos'),z);am=abs(hilbert(bp));pk,_=find_peaks(am[SR:9*SR:128],distance=.55*SR/128,prominence=.02*am.max());times=1+pk*128/SR;period=float(np.median(np.diff(times)));assert abs(period-Q)<.02
 t=np.arange(64*SR)/SR;pair=np.sin(2*np.pi*110*t)+np.sin(2*np.pi*111.375*t);amp=abs(hilbert(pair));ix,_=find_peaks(amp[::128],distance=.6*SR/128,prominence=1);peaks=ix*128/SR
 jsave(out/'batidos.json',{'frecuencias_Hz':[110,111.375],'diferencia_Hz':1.375,'periodo_s':Q,'BPM':82.5,'banco_s':64,'picos_s':peaks.tolist(),'metodo':'máximos de envolvente analítica de la suma de dos senos; usados como disparos musicales'})
 fu={};fuy=[]
 for p in [.5,.85]:
  y=resample_poly(np.fromfile(R/f'prueba-fuelle-{p}.f32',np.float32),1,2);assert np.isfinite(y).all();fr=frecuencia(y[2*SR:4*SR],200,240);assert abs(fr-220)<1
  fu[str(p)]={'frecuencia_Hz':fr,'RMS_sostenido':float(np.sqrt(np.mean(y[2*SR:4*SR]**2))),'pico':float(abs(y).max())};fuy.append(y)
 assert fu['0.85']['RMS_sostenido']>fu['0.5']['RMS_sostenido']
 jsave(out/'pruebas-motores.json',{'pianos_Hz':F,'coma_medida_cents':float(1200*np.log2(F[2]/F[0])),'periodo_EP_s':period,'BPM_EP':60/period,'fuelle':fu,'limite':'análisis de señal y estabilidad; sin escucha auditiva ni validación física del fuelle'})
 clips=[x[:8*SR] for x in [xs[0],xs[1],z]]+[x[:5*SR] for x in fuy];aud=np.concatenate([np.concatenate([x*.6,np.zeros(SR//2)]) for x in clips]);wav(out/f'sonda-pianos-y-fuelle-s{SEED}-{tag}.wav',pan(aud));aac(out/f'sonda-pianos-y-fuelle-s{SEED}-{tag}.m4a',out/f'sonda-pianos-y-fuelle-s{SEED}-{tag}.wav')
 f,ax=figura('La coma sí llega al sonido','Motores fijados · dos pianos FM · batido medido · presión del fuelle',2)
 tt=np.arange(len(am))/SR;ax[0].plot(tt[::128],am[::128],color='#e9b46e');ax[0].plot(times,am[(times*SR).astype(int)],'o',color='#79c1bd',ms=4);ax[0].set_xlim(1,9);ax[0].set_xlabel('segundos');ax[0].set_title(f'EP reales: {F[0]:.4f} / {F[2]:.4f} Hz')
 for p,y in zip([.5,.85],fuy):ax[1].plot(np.arange(0,len(y),256)/SR,y[::256],lw=.5,label=f'presión {p}')
 ax[1].legend();ax[1].set_xlabel('segundos');ax[1].set_title('Lengüeta activa: prueba estacionaria');salva(f,out/'proceso'/f'03-pruebas-de-instrumentos-s{SEED}-{tag}.png');print(F,period,fu)
if __name__=='__main__':main()
