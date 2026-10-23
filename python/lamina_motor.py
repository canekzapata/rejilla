"""Lámina adicional desde el pedido y WAV reales; nunca modifica el audio."""
import json,textwrap
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy import signal
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageOps

def ampliar(folder):
    folder=Path(folder);r=json.loads(next(folder.glob('receta-*.json')).read_text(encoding='utf8'));c=r['config'];tag=r['ejecucion'][:12];seed=r['semilla'];dest=folder/'proceso'/f'04-partitura-espectro-s{seed}-{tag}.png'
    if dest.exists():raise FileExistsError(dest)
    rate,y=wavfile.read(next(folder.glob('*.wav')));y=y.astype(float)/32768;y=y.mean(axis=1)if y.ndim>1 else y
    notes=[]
    def walk(o):
        if isinstance(o,dict):
            if 't'in o and any(k in o for k in('m','midi','nota','notas','f','chars')):notes.append(o)
            else:
                for v in o.values():walk(v)
        elif isinstance(o,list):
            for v in o:walk(v)
    walk(c)
    if r.get('detalles',{}).get('partitura'):notes=r['detalles']['partitura']['waterEvents']
    fig,axes=plt.subplots(2,1,figsize=(11,7));fig.suptitle(r['motor']+' · pedido y audio conservados',fontsize=14)
    if notes:
        hz=False
        for e in notes:
            vals=e.get('notas',[e.get('m',e.get('midi',e.get('nota',e.get('f',e.get('chars',0)))))])
            if not isinstance(vals,list):vals=[vals]
            for v in vals:
                if isinstance(v,(int,float)):axes[0].plot([e['t'],e['t']+e.get('dur',.12)],[v,v],lw=3)
            if 'f'in e:hz=True
        axes[0].set(xlabel='Segundos',ylabel='Hz'if hz else 'Nota MIDI / valor del evento',title='Eventos del pedido (cada línea es una entrada)')
    elif c.get('perfil'):
        axes[0].plot(c['perfil']);axes[0].set(xlabel='Sección del tubo',ylabel='Área normalizada',title='Perfil sintético de la cavidad; no es terreno medido')
    else:
        found=False
        for key in('velocidad','dir','cerca','oxido','caldera','brama'):
            if isinstance(c.get(key),list):
                a=np.asarray(c[key]);axes[0].plot(a[:,0],a[:,1],label=key);found=True
        if found:axes[0].legend();axes[0].set(xlabel='Segundos',title='Controles del pedido; valores en escala del motor')
        else:
            # Procesos sin notas: mostrar la envolvente medida del WAV, sin inventar eventos.
            block=max(1,rate//50);a=y[:len(y)//block*block].reshape(-1,block);rms=np.sqrt(np.mean(a*a,axis=1));axes[0].plot(np.arange(len(rms))*block/rate,rms);axes[0].set(xlabel='Segundos',ylabel='RMS',title='Envolvente del audio producido (ventanas de 20 ms)')
    f,p=signal.welch(y,rate,nperseg=min(8192,len(y)));axes[1].semilogx(f[1:],10*np.log10(np.maximum(p[1:],1e-14)),lw=1,color='#27676c');axes[1].set(xlim=(30,min(rate/2,16000)),ylim=(-140,-15),xlabel='Hz · escala logarítmica',ylabel='dB/Hz (referencia 1)',title='Densidad espectral media del WAV · no mide inteligibilidad')
    fig.text(.05,.015,'Semilla '+str(seed)+' · '+textwrap.shorten(r['limite'],width=140,placeholder='…'),fontsize=8);fig.tight_layout(rect=(0,.04,1,.96));fig.savefig(dest,dpi=120);plt.close(fig)
    pics=[dest,*sorted((folder/'proceso').glob('0[23]-*.png'))];frames=[ImageOps.pad(Image.open(p).convert('RGB'),(1000,600),color='white')for p in pics]
    gif=folder/f'proceso-ampliado-{r["motor"]}-s{seed}-{tag}.gif';frames[0].save(gif,save_all=True,append_images=frames[1:],duration=1700,loop=0,optimize=True)
    with(folder/'proceso/README.md').open('a',encoding='utf8')as out:out.write('\nLámina 04 y GIF ampliado: calculados después a partir del pedido, receta y WAV conservados. Muestran eventos o entradas, densidad espectral media, onda y espectrograma. No son otra interpretación ni una reconstrucción de borradores. Se conserva también el primer GIF.\n')
    import hashlib
    (folder/'HUELLAS.json').write_text(json.dumps({p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in folder.rglob('*')if p.is_file()and p.name!='HUELLAS.json'},indent=2),encoding='utf8')
    return dest

if __name__=='__main__':
    import sys
    ampliar(sys.argv[1])
