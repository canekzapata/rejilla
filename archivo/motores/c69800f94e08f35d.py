"""Interpretación autorizada por Canek el 22 de octubre: audio, sin visor/video."""
from comun import *
from scipy.signal import butter,sosfilt,sosfiltfilt

def salida_audio():return BASE/(BASE/'RENDER-ACTUAL.txt').read_text(encoding='utf8').strip()
def contexto():
    out=salida_audio();cfg=leer(out/'interpretacion.json');return out,cfg,leer(out/'partitura-aprobada.json'),Path(cfg['scratch'])
def rawsave(folder,c,x):
    assert np.isfinite(x).all(),c
    guardar(folder/(c+'.f32'),np.asarray(x,np.float32).tobytes())
def rawread(folder,c,N):
    z=np.fromfile(folder/(c+'.f32'),np.float32)
    assert len(z) in [N,N*2],(c,len(z),N)
    return pan(z) if len(z)==N else z.reshape(-1,2)
def corte(x,libre=False):
    """Corte de buses métricos con 35 ms de fade a 179.960; reabre en 200.
    La radio libre usa otro bus. Se aplica de nuevo después de efectos/lectura.
    """
    if libre:return x
    a=round(179.96*SR);f=round(.035*SR);b=round(200*SR)
    x[a:a+f]*=np.linspace(1,0,f,dtype=np.float32).reshape((-1,)+(1,)*(x.ndim-1));x[a+f:b]=0
    return x
def activo(y):
    z=np.asarray(y).reshape(len(y),-1);k=1024;z=z[:len(z)//k*k].reshape(-1,k,z.shape[1]);p=np.mean(z*z,axis=(1,2));good=p>max(1e-15,float(p.max())*1e-5)
    return float(np.sqrt(np.mean(p[good]))) if good.any() else 0.

def iniciar():
    src=ultimo();P=leer(score());assert P['version']=='laberinto-partitura-0.4'
    image=next((src/'proceso').glob('02-*.png')).read_bytes();nonce=os.urandom(24).hex();version='por-aqui-audio-1.0'
    code=Path(__file__).read_bytes();full=hashlib.sha256(image+version.encode()+nonce.encode()+code).hexdigest();tag=full[:12]
    out=BASE/f'por-aqui-cancion-s22-{tag}';out.mkdir(exist_ok=False);(out/'proceso').mkdir();(out/'fuentes-fijadas').mkdir()
    scratch=BASE/'render'/f'audio-{tag}';scratch.mkdir(parents=True,exist_ok=False);(scratch/'fuentes').mkdir()
    guardar(out/'proceso'/f'01-partitura-aprobada-s22-{tag}.png',image);guardar(out/'partitura-aprobada.json',score().read_bytes());guardar(out/'viaje.json',(src/'viaje.json').read_bytes())
    cfg={'titulo':P['titulo'],'version':version,'sr':SR,'duracion':P['duracion_prevista'],'semilla':22,'hash':full,'nonce':nonce,'imagen_inicial_sha256':hashlib.sha256(image).hexdigest(),'fuente_inicio_sha256':hashlib.sha256(code).hexdigest(),'partitura_origen':str(src),'partitura_sha256':sha(score()),'scratch':str(scratch),'biblioteca':str(lib()),'autorizacion':'Canek: renderiza, 2026-10-22; visor y video después','canales':list(P['eventos']),'fem_carga_resolucion':.01}
    guardar(out/'fuentes-fijadas/audio_comun.py',code);jsave(out/'interpretacion.json',cfg);(BASE/'RENDER-ACTUAL.txt').write_text(out.name,encoding='utf8');print(out,flush=True)

if __name__=='__main__':iniciar()
