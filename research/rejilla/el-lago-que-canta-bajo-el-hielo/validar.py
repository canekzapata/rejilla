"""Verificación de entrega: señal, unión de vocoder, modelo y fuentes fijadas."""
from comun import *
from scipy import sparse
from scipy.sparse.linalg import eigsh
from scipy.io import wavfile
from mezcla import importar,vocoder_bloques
def main():
 out=ultimo();tag=out.name.split('-')[-1];P=jleer(out/'partitura.json');R=jleer(out/'red.json');mix=jleer(out/'mezcla-medidas.json');run=BASE/'render'/tag
 sr,y=wavfile.read(out/(out.name+'.wav'));audio={'sr':sr,'duracion':len(y)/sr,'pico':float(abs(y).max()),'finito':bool(np.isfinite(y).all()),'cola_50ms':float(abs(y[-round(.05*sr):]).max())};del y
 assert audio['finito'] and audio['pico']<1 and abs(audio['duracion']-P['duracion'])<.001 and audio['cola_50ms']<.01
 assert len(P['eventos'])==30 and len(mix['capas'])==30 and all(v['activo_crudo']>1e-8 for v in mix['capas'].values())
 # Solución independiente conocida de una placa rectangular Navier discreta.
 nx,ny=8,11;dx=.1;D=lambda n:sparse.diags([-np.ones(n-1),2*np.ones(n),-np.ones(n-1)],[-1,0,1])
 L=(sparse.kron(sparse.eye(ny),D(nx))+sparse.kron(D(ny),sparse.eye(nx)))/dx**2
 w=np.sort(eigsh(L,k=8,which='SM',v0=np.ones(nx*ny))[0]);exact=np.sort([4/dx**2*(np.sin(i*np.pi/(2*(nx+1)))**2+np.sin(j*np.pi/(2*(ny+1)))**2) for i in range(1,nx+1) for j in range(1,ny+1)])[:8]
 rect_error=float(np.max(abs(w-exact)));assert rect_error<1e-8
 assert all(min(s['frecuencias'])>0 for s in R['estados'])
 # La voz activa cruza t=32 s; comparar un tramo largo con centros de 4 s.
 mod=np.fromfile(run/'sabina-M.f32',np.float32)[24*SR:40*SR];car=np.fromfile(run/'voc-hielo-M.f32',np.float32).reshape(-1,2)[24*SR:40*SR].mean(1)
 sn=importar(BASE/'fuentes/vocoder/sintes.py');a=vocoder_bloques(mod,car,sn,paso_s=4);b=vocoder_bloques(mod,car,sn,paso_s=16);err=float(np.linalg.norm(a-b)/(np.linalg.norm(b)+1e-12));assert err<.08,err
 # Todas las fichas y motores tomados deben coincidir con su manifiesto.
 lib=BASE/'instrumentos-5620a744f682';man=jleer(lib/'manifiesto.json');bad=[f for f,h in man['archivos'].items() if sha(lib/f)!=h];assert not bad,bad
 vids=list(out.glob('*.mp4'));assert not vids,'Canek reservó el render del video'
 data={'audio':audio,'capas_no_mudas':len(mix['capas']),'placa_rectangular_error_autovalor':rect_error,'vocoder_4s_vs_16s_error_relativo':err,'fuentes_biblioteca_verificadas':len(man['archivos']),'video_renderizado':False,'observacion':'verificación de señal y comportamiento; sin audición propia del agente'}
 jguardar(out/'validacion-entrega.json',data);print(json.dumps(data,indent=1))
if __name__=='__main__':main()
