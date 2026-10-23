"""Actual source, intermediate and delivered audio plots. No hypothetical sound."""
import sys,json,gzip,gc,math
from pathlib import Path
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import spectrogram
from scipy.io import wavfile
from PIL import Image
BASE=Path(__file__).resolve().parent;OUT=BASE/(BASE/'REALIZACION-ACTUAL.txt').read_text().strip()
P=json.loads((OUT/'partitura.json').read_text(encoding='utf8'));SR=48000;TAG='s1-'+OUT.name.split('-')[-1]
plt.rcParams.update({'font.family':'Segoe UI','font.size':10,'figure.facecolor':'#11171b','axes.facecolor':'#11171b','text.color':'#e5e3d8','axes.labelcolor':'#d0d8cf','xtick.color':'#acbdb5','ytick.color':'#acbdb5','axes.edgecolor':'#587165','savefig.facecolor':'#11171b'})
def save(fig,stem):
    p=OUT/'proceso'/(stem+'-'+TAG+'.png')
    if p.exists():plt.close(fig);return
    fig.savefig(p,dpi=125,bbox_inches='tight');plt.close(fig);print(p.name,flush=True)
def read(name,a=0,b=P['duracion']):
    with gzip.open(OUT/'render'/(name+'.f32.gz'),'rb') as f:f.seek(round(a*SR)*8);y=np.frombuffer(f.read(round((b-a)*SR)*8),dtype='<f4').reshape(-1,2)
    return y
def envelope(y,step=2400):
    n=len(y)//step;z=y[:n*step].reshape(n,step,2);return np.max(np.abs(z),axis=(1,2))
def fuentes():
    fig,ax=plt.subplots(figsize=(14,8));names=[p['id'] for p in P['partes']];counts=[len(P['eventos'][k]) for k in names]
    ax.barh(np.arange(36),counts,color=plt.cm.viridis(np.linspace(.2,.9,36)));ax.set_yticks(np.arange(36),names);ax.invert_yaxis();ax.set_xscale('log');ax.set_xlabel('Eventos internos, escala logarítmica');ax.set_title('Luciérnagas · fuentes fijadas y 36 partes realizadas',loc='left',pad=18)
    fig.text(.50,.04,'Motores originales de biblioteca · estados Guitarra/Junco · Sabina PSOLA\nEtapa capturada después de sintetizar las fuentes, antes de la mezcla.',ha='center',color='#acc2b6');save(fig,'01-rutas-y-partes')
    names=['guitarra','prosodia-voz','cuerda','organo','junco1','bombo'];fig,axes=plt.subplots(6,1,figsize=(14,8),sharex=True)
    for ax,name in zip(axes,names):
        y=read(name);v=envelope(y);ax.plot(np.arange(len(v))*.05,v,lw=.8);ax.set_ylabel(name,rotation=0,ha='right',fontsize=9);del y;gc.collect()
        ax.grid(alpha=.13)
    axes[-1].set_xlabel('Segundos');axes[0].set_title('Observaciones de los motores antes de mezcla y ventanas de salida',loc='left',pad=16);save(fig,'02-fuentes-sintetizadas')
def vocoder():
    a,b=219.9,224.9;names=['prosodia-corojunco','junco1','corojunco'];fig,axes=plt.subplots(3,1,figsize=(14,7),sharex=True)
    for ax,name in zip(axes,names):
        y=read(name,a,b).mean(1);step=48;ax.plot(a+np.arange(0,len(y),step)/SR,y[::step],lw=.7);ax.set_ylabel(name,fontsize=9);ax.grid(alpha=.15)
    axes[0].set_title('Una articulación pasa al junco · guía, portadora y vocoder real',loc='left',pad=18);axes[-1].set_xlabel('Segundos');save(fig,'03-portadora-y-vocoder')
def finales():
    report=json.loads(max(OUT.glob('mezcla-r*.json'),key=lambda p:p.stat().st_mtime).read_text(encoding='utf8'));sr,y=wavfile.read(OUT/report['salida_wav']);assert sr==SR;y=y.astype(np.float32)/2147483648
    labels=[s['id'] for s in P['secciones']];groups=report['grupos_contra_resto_db'];arr=np.array([[max(-35,min(15,v.get(k,-35))) for k in labels] for v in groups.values()])
    fig,ax=plt.subplots(figsize=(14,7));im=ax.imshow(arr,aspect='auto',cmap='coolwarm',vmin=-30,vmax=10);ax.set_xticks(range(9),labels);ax.set_yticks(range(len(groups)),list(groups));ax.set_title('Mezcla · cada grupo contra el resto por sección (dB)',loc='left',pad=18);fig.colorbar(im,ax=ax,label='dB de energía relativa');save(fig,'04-grupos-en-la-forma')
    i,j=round(P['centro'][0]*SR),round(P['centro'][1]*SR);fig,axes=plt.subplots(2,1,figsize=(14,7),sharex=True);x=y[i:j];t=P['centro'][0]+np.arange(len(x))/SR
    axes[0].plot(t[::48],x[::48].mean(1),lw=.6,color='#cdaa7c');axes[0].set_ylabel('Amplitud')
    for k,name in enumerate(['guitarra','cuerda','junco1','junco2','junco3','junco4','waterphone','campana']):
        for e in P['eventos'][name]:
            for a,b in e['salidas']:
                if a>=P['centro'][0] and b<=P['centro'][1]:axes[1].plot([a,b],[k,k],lw=5)
    axes[1].set_yticks(range(8),['guitarra','cuerda','junco 1','junco 2','junco 3','junco 4','waterphone','campana']);axes[1].set_xlabel('Segundos');axes[0].set_title('Centro · audio entregado y relevos escritos',loc='left',pad=18);save(fig,'05-centro-y-oscuridades')
    fig,axes=plt.subplots(3,1,figsize=(14,7),sharey=True)
    for ax,(a,b,title) in zip(axes,[(206.666667,220,'1 · Resonancia'),(220,233.333333,'2 · Contagio'),(233.333333,246.666667,'3 · Casi continuidad')]):
        i,j=round(a*SR),round(b*SR);v=envelope(y[i:j],480);ax.plot(a+np.arange(len(v))*.01,v,lw=.8);ax.set_title(title,loc='left');ax.set_xlim(a,b);ax.grid(alpha=.15)
    axes[-1].set_xlabel('Segundos · escala de amplitud común');save(fig,'06-tres-olas-de-la-pared')
    fig,axes=plt.subplots(2,1,figsize=(14,8),sharex=True,gridspec_kw={'height_ratios':[1,3]});v=envelope(y);axes[0].plot(np.arange(len(v))*.05,v,color='#d2ae7d',lw=.7);axes[0].set_ylabel('Pico / 50 ms')
    f,t,z=spectrogram(y.mean(1),SR,nperseg=2048,noverlap=1024)
    # Average power into display columns before converting to dB. Fixed Hz/dB
    # scales are retained; the figure need not allocate millions of invisible quads.
    stride=math.ceil(z.shape[1]/1600);cols=z.shape[1]//stride;z=z[:,:cols*stride].reshape(len(f),cols,stride).mean(2);t=t[:cols*stride].reshape(cols,stride).mean(1)
    db=10*np.log10(z+1e-16);axes[1].pcolormesh(t,f,db,shading='auto',cmap='magma',vmin=-95,vmax=-30);axes[1].set_yscale('log');axes[1].set_ylim(40,18000);axes[1].set_ylabel('Hz');axes[1].set_xlabel('Segundos')
    for s in P['secciones']:
        axes[0].axvline(s['t'],alpha=.4,color='white',lw=.7);axes[1].axvline(s['t'],alpha=.3,color='white',lw=.7);axes[0].text((s['t']+s['fin'])/2,.95,s['id'],transform=axes[0].get_xaxis_transform(),ha='center',va='top')
    axes[0].set_title('Llevemos unas luciérnagas al lago · canción completa · audio entregado',loc='left',pad=18);save(fig,'07-resultado-y-espectrograma')
    fig,ax=plt.subplots(figsize=(14,8));names=[q['id'] for q in P['partes']]
    for k,name in enumerate(names):
        for e in P['eventos'][name]:
            for a,b in e['salidas']:ax.plot([a,b],[k,k],lw=2.5,color=plt.cm.viridis(k/36))
    for s in P['secciones']:ax.axvline(s['t'],lw=.6,alpha=.4,color='white');ax.text((s['t']+s['fin'])/2,-1.5,s['id'],ha='center')
    ax.set_yticks(range(36),names,fontsize=8);ax.invert_yaxis();ax.set_xlabel('Segundos');ax.set_title('Forma completa · salidas que gobiernan la realización',loc='left',pad=18);save(fig,'08-forma-y-partitura')
    files=sorted((OUT/'proceso').glob('*.png'));frames=[]
    for p in files:
        im=Image.open(p).convert('RGB');im.thumbnail((1200,700));canvas=Image.new('RGB',(1200,700),(17,23,27));canvas.paste(im,((1200-im.width)//2,(700-im.height)//2));frames.append(canvas.quantize(colors=128))
    gif=OUT/('luciernagas-proceso-cancion-'+TAG+'.gif');assert not gif.exists();frames[0].save(gif,save_all=True,append_images=frames[1:],duration=1000,loop=0,optimize=True)
    image=Image.open(next((OUT/'proceso').glob('07-*.png'))).convert('RGB');image.resize((1200,630)).save(OUT/'og.png')
    (OUT/'proceso'/'README.md').write_text('# Proceso de la realización sonora\n\n01–02 se capturaron tras sintetizar las fuentes; 03, al terminar los vocoders. 04–08 vienen de la mezcla y del WAV entregado, con frecuencia y escala comunes. El GIF reúne estas láminas, no una simulación del render interno.\n\nLa partitura v8 conserva 36 partes y 4:18.667. Semilla de terreno 1; semilla de composición 2026102201. Cada nombre conserva el identificador de esta ejecución.\n',encoding='utf8')
if __name__=='__main__':{'fuentes':fuentes,'vocoder':vocoder,'finales':finales}[sys.argv[1]]()
