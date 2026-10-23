"""Comprobar contrato musical, fuentes y audio entregado. Sin certificar gusto por métricas."""
from comun import *
def main():
 out=ultimo();P=leer(out/'partitura.json');N=round(P['duracion']*SR);info={'capas':{},'fuentes_cotejadas':0}
 for rel,h in leer(BASE/'procedencia.json')['fuentes'].items():assert sha(BASE/rel)==h,rel;info['fuentes_cotejadas']+=1
 for rel,h in leer(lib()/'manifiesto.json')['archivos'].items():assert sha(lib()/rel)==h,rel;info['fuentes_cotejadas']+=1
 assert len(P['eventos'])==30
 for c in P['eventos']:
  y=np.fromfile(run()/(c+'.f32'),np.float32);assert len(y) in [N,2*N] and np.isfinite(y).all() and abs(y).max()>1e-6,c;info['capas'][c]={'muestras':len(y),'pico':float(abs(y).max())}
 ratios=[e['ratio'] for e in P['solo_D']];assert np.allclose(ratios,[1,3/2,9/8,27/16,81/64,81/80]);assert abs((3/2)**4/(5/4)/4-COMA)<1e-14
 root=[e for e in P['eventos']['ep-tema'] if e.get('frase')=='raiz-del-recorrido'];assert np.allclose([float(hz(e['midi'])) for e in root],[220*r for r in ratios]);assert all(abs(e['midi']-round(e['midi'])-CENTS/100)<1e-7 for e in P['eventos']['ep-tema'] if e['t']>=64*BAR)
 # Unión de intervalos previstos, distinta de ocupación perceptiva del máster.
 pairs=sorted((e['t'],e['t']+e['dur']) for e in P['eventos']['voz']);merged=[]
 for a,b in pairs:
  if merged and a<=merged[-1][1]:merged[-1][1]=max(b,merged[-1][1])
  else:merged.append([a,b])
 planned=sum(b-a for a,b in merged);info['voz']={'apariciones':3,'union_notas_s':planned,'porcentaje_partitura':100*planned/P['duracion'],'ventanas':P['solista_ventanas'],'fuera_de_ventanas':{}}
 gate=np.zeros(N,bool)
 for a,b in P['solista_ventanas']:gate[max(0,round((a-.08)*SR)):min(N,round((b+.08)*SR))]=True
 for c in ['voz','voz-doble','voz-fuelle','fragmento']:
  y=np.fromfile(run()/(c+'.f32'),np.float32).reshape(N,2);outside=float(abs(y[~gate]).max());assert outside<1e-5,(c,outside);info['voz']['fuera_de_ventanas'][c]=outside
  for s in ['IV','V','VII']:
   sec=next(x for x in P['secciones'] if x['id']==s);assert abs(y[round(sec['t']*SR):round(sec['t1']*SR)]).max()<1e-6,(c,s)
 sr,y=wavfile.read(master());assert sr==48000 and len(y.shape)==2 and y.shape[1]==2 and np.isfinite(y).all();assert abs(len(y)/sr-P['duracion'])<.002;assert abs(y).max()<1;assert abs(y[-round(.05*sr):]).max()<1e-7
 mm=leer(out/'mezcla-medidas.json');assert mm['rejilla']['SNR_sin_DC_Nyquist_dB']>50;assert float(mm['aac']['input_tp'])<-.8
 info['master']={'sr':sr,'segundos':len(y)/sr,'pico':float(abs(y).max()),'cola_50ms':float(abs(y[-round(.05*sr):]).max()),'sha256':sha(master()),'aac':mm['aac'],'rejilla':mm['rejilla']};assert not list(BASE.rglob('*.mp4'));info['video_renderizado']=False
 info['limite']='Pruebas numéricas y visuales; no hubo audición propia. El fuelle no está calibrado contra un instrumento físico.';jsave(out/'validacion.json',info);print(json.dumps({k:v for k,v in info.items() if k!='capas'},ensure_ascii=False,indent=1))
if __name__=='__main__':main()
