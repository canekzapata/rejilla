"""Renderizar cualquiera de los doce prototipos, con audio e imágenes obligatorias."""
import hashlib, importlib.util, json, sys, uuid
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent
def producir(archivo,destino=None):
    import numpy as np
    from scipy.io import wavfile
    from scipy.signal import spectrogram
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from PIL import Image,ImageOps
    raw=Path(archivo).read_bytes(); s=json.loads(raw.decode('utf-8-sig'))
    source=BASE/'fuentes/doce/motores.py'; spec=importlib.util.spec_from_file_location('doce_original',source); M=importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
    nonce=uuid.uuid4().hex; full=hashlib.sha256(raw+source.read_bytes()+Path(__file__).read_bytes()+nonce.encode()).hexdigest(); tag=full[:12]
    seed=int(s.get('semilla',19103419)); nombre=s['prototipo']; d=float(s.get('duracion',24))
    if not 1<=d<=120: raise ValueError('Duración del prototipo: 1..120 segundos.')
    parent=Path(destino) if destino else BASE/'salidas'; parent.mkdir(exist_ok=True,parents=True)
    out=parent/f'{nombre}-s{seed}-{tag}'; out.mkdir(exist_ok=False); proc=out/'proceso'; proc.mkdir()
    print('Calculando '+M.NOMBRES[nombre]+'. Salida: '+str(out),flush=True)
    y,traces,info=M.render(nombre,s['partitura'],d,sr=32000,semilla=seed)
    peak=float(np.max(np.abs(y))); gain=min(1,.8/max(peak,1e-9)); y=y*gain
    if not np.isfinite(y).all() or peak<1e-9: raise ValueError('Audio vacío/no finito.')
    wavfile.write(out/f'{nombre}-s{seed}-{tag}.wav',32000,np.round(np.clip(y,-1,1)*32767).astype(np.int16))
    imgs=[]
    def guardar(fig,i,desc):
        p=proc/f'{i:02d}-{desc}-s{seed}-{tag}.png'; fig.savefig(p,dpi=120,bbox_inches='tight'); plt.close(fig); imgs.append(p)
    fig,ax=plt.subplots(figsize=(11,4))
    for n in s['partitura'].get('notas',[]): ax.plot([n['t'],n['t']+n['dur']],[n['midi']]*2,lw=4)
    ax.set(title=M.NOMBRES[nombre]+' · partitura',xlabel='Segundos',ylabel='MIDI'); guardar(fig,1,'partitura')
    grupos=[[],[],[]]
    for key,value in traces.items():
        a=np.asarray(value)
        if a.ndim==1 and len(a)>1:
            grupos[0 if key=='f0_hz' else 1 if key.endswith('_hz') else 2].append((key,a))
    activos=[g for g in grupos if g]
    fig,axes=plt.subplots(max(1,len(activos)),1,figsize=(11,3*max(1,len(activos))),squeeze=False)
    ax=axes[0,0]
    for axis,grupo in zip(axes[:,0],activos):
        for key,a in grupo:
            paso=max(1,len(a)//2400); axis.plot(np.linspace(0,d,len(a))[::paso],a[::paso],label=key,lw=.8)
        axis.set_xlabel('Segundos');axis.legend(fontsize=8,loc='upper right');axis.grid(alpha=.18)
    if not activos:
        for key,pts in s['partitura'].get('controles',{}).items(): ax.plot(*np.array(pts).T,label=key)
        if ax.lines: ax.legend()
        else: ax.plot(np.arange(len(y))/32000,y[:,0],lw=.5,label='señal izquierda'); ax.legend()
    ax.set_title('Controles y trazas reales del motor (unidades según etiqueta)');fig.tight_layout(); guardar(fig,2,'controles')
    fig,ax=plt.subplots(figsize=(11,4)); f,t,p=spectrogram(y.mean(axis=1),32000,nperseg=1024,noverlap=768)
    ax.pcolormesh(t,f,10*np.log10(np.maximum(p,1e-14)),shading='auto',cmap='magma',vmin=-110,vmax=-35); ax.set(yscale='log',ylim=(30,14000),xlabel='Segundos',ylabel='Hz',title='Audio producido · espectrograma'); guardar(fig,3,'espectrograma')
    frames=[ImageOps.pad(Image.open(p).convert('RGB'),(1000,480),color='white') for p in imgs]
    frames[0].save(out/f'proceso-{nombre}-s{seed}-{tag}.gif',save_all=True,append_images=frames[1:],duration=1800,loop=0,optimize=True)
    (out/f'partitura-{tag}.json').write_bytes(raw)
    (out/f'receta-{tag}.json').write_text(json.dumps({'ejecucion':full,'nonce':nonce,'semilla':seed,'motor_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'partitura_sha256':hashlib.sha256(raw).hexdigest(),'pico_previo':peak,'ganancia':gain,'info':info,'nota':'No se usó FFmpeg ni una imagen como entrada. Síntesis temporal del prototipo original.'},ensure_ascii=False,indent=2,default=lambda x:x.tolist() if hasattr(x,'tolist') else str(x)),encoding='utf8')
    (proc/'README.md').write_text('Etapas calculadas en esta ejecución: partitura, controles/trazas, espectrograma del audio. GIF de 5.4 s, sin representar borradores previos. Cambiar parámetros requiere volver a comprobar señal y escuchar.\n',encoding='utf8')
    (out/'HUELLAS.json').write_text(json.dumps({p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()},indent=2),encoding='utf8')
    print('Listo: '+str(out),flush=True); return out
if __name__=='__main__': producir(sys.argv[1])
