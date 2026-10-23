"""Comprueba señales, eco y biblioteca; prepara controles de audio para Hydra."""
from comun import *
from instrumentos import Eco
from scipy.signal import butter,sosfiltfilt
def main():
 out=ultimo();tag=out.name.split('-')[-1];P=leer(out/'partitura.json');E=leer(out/'eco.json');M=leer(out/'mezcla-medidas.json');n=round(P['duracion']*SR);track={}
 for c in P['eventos']:
  p=run()/(c+'.f32');x=np.memmap(p,mode='r',dtype='float32');assert len(x) in [n,n*2] and np.isfinite(x).all(),c;peak=float(abs(x).max());assert peak>1e-8,c;track[c]={'muestras':len(x),'pico_crudo':peak}
 # Linealidad efectiva: la señal del residuo coincide con restar los otros dos audios.
 a=np.memmap(run()/'flujo-ideal.f32',mode='r',dtype='float32');b=np.memmap(run()/'flujo-viscoso.f32',mode='r',dtype='float32');r=np.memmap(run()/'residuo.f32',mode='r',dtype='float32');num=den=0
 for i in range(0,len(a),SR*4):
  d=b[i:i+SR*4].astype('float64')-a[i:i+SR*4];v=r[i:i+SR*4];num+=float(np.sum((v-d)**2));den+=float(np.sum(d*d))
 error=float(np.sqrt(num/den));assert error<2e-6,error
 assert E['ideal']['error_retorno']<E['ideal']['error_dt_doble'] and E['viscoso']['error_retorno']>.01
 for name in ['ideal','viscoso']:
  trace=E[name]['traza'];assert max(e['div'] for e in trace)<1e-10 and max(e['reality'] for e in trace)<1e-10
  for phase in ['ida','vuelta']:
   en=[e['energy'] for e in trace if e['fase']==phase]
   if name=='viscoso':assert np.max(np.diff(en))<1e-10
 manifest=leer(lib()/'manifiesto.json');assert all(sha(lib()/p)==h for p,h in manifest['archivos'].items());prov=leer(BASE/'procedencia.json');assert all(sha(BASE/p)==h for p,h in prov['fuentes'].items())
 sr,y=wavfile.read(master(out));assert sr==48000 and np.isfinite(y).all() and abs(y).max()<1 and abs(y[-round(sr*.05):]).max()<1e-7
 assert not list(BASE.rglob('*.mp4'))
 B=P['compas'];sections={}
 for name,b0,b1 in [('primer_peso',32,48),('solo_pulgares',48,64),('eco_D',64,88),('salida_pesada',88,120)]:
  z=y[round(b0*B*sr):round(b1*B*sr)];lo=sosfiltfilt(butter(3,[28,90],btype='bandpass',fs=sr,output='sos'),z,axis=0);mid=sosfiltfilt(butter(3,[160,650],btype='bandpass',fs=sr,output='sos'),z,axis=0)
  sections[name]={'RMS_dBFS':float(10*np.log10(np.mean(z*z)+1e-15)),'28_90_Hz_dBFS':float(10*np.log10(np.mean(lo*lo)+1e-15)),'160_650_Hz_dBFS':float(10*np.log10(np.mean(mid*mid)+1e-15))}
 delta=sections['salida_pesada']['RMS_dBFS']-sections['primer_peso']['RMS_dBFS'];low_delta=sections['salida_pesada']['28_90_Hz_dBFS']-sections['primer_peso']['28_90_Hz_dBFS'];assert delta>.5 and low_delta>1,('contraste final y sub',delta,low_delta)
 # Energía del máster, no eventos inferidos: 20 lecturas por segundo.
 low=sosfiltfilt(butter(3,[28,120],btype='bandpass',fs=sr,output='sos'),y.mean(1));step=sr//20;pad=np.pad(low,(0,(-len(low))%step));v=np.sqrt(np.mean(pad.reshape(-1,step)**2,axis=1));v/=max(np.percentile(v,95),1e-9)
 jsave(out/'audio-visual.json',{'fps':20,'bajo':np.clip(v,0,1.5).tolist(),'origen':'RMS 28–120 Hz del máster WAV real; sin analizar micrófono'})
 result={'duracion_s':len(y)/sr,'capas_no_mudas':len(track),'pico_PCM':float(abs(y).max()),'silencio_final_50ms':True,'residuo_igual_a_viscoso_menos_ideal_error_relativo':error,'eco_ideal_error':E['ideal']['error_retorno'],'eco_viscoso_distancia_inicial':E['viscoso']['error_retorno'],'biblioteca_archivos_verificados':len(manifest['archivos']),'secciones':sections,'salida_menos_primer_drop_dB':delta,'sub_salida_menos_primer_drop_dB':low_delta,'AAC':leer(out/'master-pesada.json')['AAC'],'video_renderizado':False,'audicion_propia':False,'limites':'modelo finito, voz PSOLA/formantes y síntesis; estas pruebas no certifican inteligibilidad, fidelidad de género o calidad musical'}
 jsave(out/'validacion.json',result);print(json.dumps(result,ensure_ascii=False,indent=1))
if __name__=='__main__':main()
