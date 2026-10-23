"""Produce an exclusive, fingerprinted run. No output file is overwritten.

python producir.py             # audio + actual intermediate PNGs
python producir.py --cerrar DIR # add GIF, process README and final file hashes
"""
from pathlib import Path
import argparse, hashlib, io, json, math, os, subprocess
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
from scipy.io import wavfile
from scipy.signal import stft
from PIL import Image,ImageOps
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import motor
from pruebas import comprobar

HERE=Path(__file__).resolve().parent
BG='#101719'; FG='#efece1'; MUTED='#a4b3b2'; GOLD='#eebd80'; CYAN='#73d6c3'
plt.rcParams.update({'figure.facecolor':BG,'axes.facecolor':BG,'axes.edgecolor':'#344346',
 'text.color':FG,'axes.labelcolor':MUTED,'xtick.color':MUTED,'ytick.color':MUTED,
 'font.family':'DejaVu Sans','font.size':11,'grid.color':'#344346','axes.titlepad':16})


def exclusive(path,data):
    with Path(path).open('xb') as f: f.write(data)


def dump(path,obj):
    exclusive(path,json.dumps(obj,ensure_ascii=False,indent=2).encode('utf-8'))


def sha(data): return hashlib.sha256(data).hexdigest()


def png(fig):
    b=io.BytesIO();fig.savefig(b,format='png',dpi=100);plt.close(fig);return b.getvalue()


def plate(title,subtitle,lines=None,audio=None,sr=motor.SR):
    fig,ax=plt.subplots(2,1,figsize=(12,7.5),gridspec_kw={'height_ratios':[1,1.1]})
    fig.subplots_adjust(left=.09,right=.96,top=.81,bottom=.10,hspace=.38)
    fig.text(.07,.94,'REJILLA / TELAR DE FASE',color=CYAN,fontsize=11)
    fig.text(.07,.885,title,fontsize=25)
    fig.text(.07,.835,subtitle,color=MUTED,fontsize=11)
    if lines:
        for t,y,label,col in lines:
            ax[0].plot(t,y,color=col,lw=1,label=label)
        ax[0].legend(loc='upper right',facecolor=BG,labelcolor=FG,edgecolor='#344346')
    else:
        t=np.arange(len(audio))/sr
        a=audio.mean(axis=1) if audio.ndim==2 else audio
        ax[0].plot(t[::16],a[::16],color=CYAN,lw=.6)
    ax[0].set(xlabel='Tiempo (s)',ylabel='Señal / amplitud');ax[0].grid(alpha=.4)
    if audio is not None:
        a=audio.mean(axis=1) if audio.ndim==2 else audio
        f,t,z=stft(a,fs=sr,nperseg=1024,noverlap=768)
        ax[1].pcolormesh(t,f,20*np.log10(np.maximum(abs(z),1e-7)),vmin=-85,vmax=-25,cmap='magma',shading='auto',rasterized=True)
        ax[1].set(ylim=(0,4200),xlabel='Tiempo (s)',ylabel='Frecuencia (Hz)')
    else:
        ax[1].axis('off')
    fig.text(.07,.025,'CANEK ZAPATA · 2026 · señal propia · semilla 20261021',color=MUTED,fontsize=10)
    return png(fig)


def spectrum_grid(out,audio,tag):
    """16-bit Rejilla images -> ffmpeg spectrumsynth -> comparison with motor."""
    Z=motor.coeficientes_rejilla(audio)
    if Z.shape[0]==1: Z=np.repeat(Z,2,axis=0)
    mag=np.vstack([abs(Z[1]).T[::-1],abs(Z[0]).T[::-1]])
    phase=np.vstack([np.angle(Z[1]).T[::-1],np.angle(Z[0]).T[::-1]])
    maxval=float(mag.max())
    mr=out/f'rejilla-magnitud-{tag}.raw';pr=out/f'rejilla-fase-{tag}.raw'
    exclusive(mr,np.round(mag/maxval*65535).astype('<u2').tobytes())
    exclusive(pr,np.round((phase+np.pi)/(2*np.pi)*65535).astype('<u2').tobytes())
    w=mag.shape[1];h=mag.shape[0];dest=out/f'prueba-rejilla-{tag}.wav'
    inp=lambda p:['-f','rawvideo','-pix_fmt','gray16le','-s',f'{w}x{h}','-r','1','-i',str(p)]
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-n',*inp(mr),*inp(pr),
      '-filter_complex',f'[0]setpts=N/TB,format=gray16le[m];[1]setpts=N/TB,format=gray16le[p];[m][p]spectrumsynth=sample_rate={motor.SR}:channels=2:scale=lin:slide=fullframe:win_func=rect:overlap=0',
      '-c:a','pcm_f32le',str(dest)],check=True)
    _,decoded=wavfile.read(dest)
    # Magnitude scaling was removed from the images, restore it after synthesis.
    n=min(len(audio),len(decoded));target=audio[:n]
    if target.ndim==1:target=np.column_stack([target,target])
    got=decoded[:n]*maxval
    snr=20*np.log10(np.linalg.norm(target)/np.linalg.norm(target-got))
    if snr<55:raise AssertionError(('spectrumsynth SNR',float(snr)))
    # Store original 16-bit magnitude and phase as PNGs, not just decorative plots.
    for name,arr in [('magnitud',np.round(mag/maxval*65535).astype('uint16')),('fase',np.round((phase+np.pi)/(2*np.pi)*65535).astype('uint16'))]:
        b=io.BytesIO();Image.fromarray(arr).save(b,format='PNG');exclusive(out/f'rejilla-{name}-{tag}.png',b.getvalue())
    return {'snr_db':float(snr),'escala_magnitud':maxval,'columnas':w,'filas_por_canal':motor.SR//2,
            'sample_rate':motor.SR,'origen':'DFT muestreada del motor temporal; imágenes reales de 16 bits',
            'raw_ignorados':[mr.name,pr.name]}


def save_audio(out,name,y):
    wav=out/(name+'.wav');aac=out/(name+'.m4a')
    with wav.open('xb') as f:wavfile.write(f,motor.SR,np.asarray(y,np.float32))
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-n','-i',str(wav),'-c:a','aac','-b:a','192k',str(aac)],check=True)
    return {'wav':wav.name,'m4a':aac.name,'duracion_s':len(y)/motor.SR,
      'pico':float(abs(y).max()),'rms':float(np.sqrt(np.mean(y*y))),'finito':bool(np.isfinite(y).all())}


def produce():
    tests=comprobar()
    dry,_=motor.nota()
    initial=plate('01 / Nace el cuerpo', 'Siete paquetes gaussianos: cobre, señal compleja y afinación central de 220 Hz.',audio=dry)
    nonce=os.urandom(24)
    version=motor.VERSION.encode();engine=(HERE/'motor.py').read_bytes()
    full=sha(initial+version+engine+nonce)
    tag=f's{motor.SEMILLA}-{full[:12]}'
    out=HERE/f'telar-de-fase-{tag}';out.mkdir(exist_ok=False);proc=out/'proceso';proc.mkdir()
    exclusive(proc/f'01-cuerpo-original-{tag}.png',initial)
    print(str(out),flush=True)
    dump(out/f'pruebas-matematicas-{tag}.json',tests)
    exclusive(out/f'motor-{tag}.py',engine)
    results={'origen':save_audio(out,f'cobre-original-{tag}',dry)}
    # These are actual intermediate computations, retained before later steps.
    transformed,_=motor.nota(inclinacion=.65,estirar=1.35,dispersion=.15)
    exclusive(proc/f'02-inclinar-estirar-dispersar-{tag}.png',plate('02 / La materia se inclina',
      'Dilatación 1.35 · chirp 0.65 · dispersión 0.15 · misma fuente y misma ganancia.',audio=transformed))
    proof=np.zeros(motor.SR*21)
    sections=[('Origen',{}),('Inclinar',{'inclinacion':.65}),('Estirar',{'estirar':1.8}),
      ('Girar',{'giro':np.pi/2}),('Dispersar',{'dispersion':.6}),
      ('Inclinar → girar',{'giro':.9,'inclinacion':.8}),
      ('Girar → inclinar',{'giro':.9,'inclinacion':.8,'orden':'girar-inclinar'})]
    for i,(_,p) in enumerate(sections):
        for d in (0,.7):
            v,_=motor.nota(**p);k=round((i*3+d)*motor.SR);proof[k:k+len(v)]+=v
    results['gestos']=save_audio(out,f'siete-gestos-{tag}',proof)
    phase=np.zeros(motor.SR*12)
    for i,theta in enumerate((0,2*np.pi,4*np.pi)):
        for d in (0,.75,1.5):
            v,_=motor.nota(giro=theta,referencia=1);k=round((i*4+d)*motor.SR);phase[k:k+len(v)]+=v
    results['retorno']=save_audio(out,f'una-vuelta-desaparece-dos-regresa-{tag}',phase)
    exclusive(proc/f'03-retorno-y-cancelacion-{tag}.png',plate('03 / El regreso cambia de signo',
       '0–4 s: origen + testigo · 4–8 s: una vuelta, cancelación · 8–12 s: dos vueltas, regreso.',audio=phase))
    events=[];melody=[57,60,64,67,69,64,62,60,57,55,60,62,64,67,64,57]
    for section in range(4):
        for j,m in enumerate(melody):
            p={'t':1+section*8+j*.45,'midi':m,'vel':.85,'pan':.18*math.sin(j*.7)}
            if section==1:p.update(giro=.35*np.pi,inclinacion=.35,estirar=1.3)
            if section==2:p.update(giro=.9,inclinacion=.65,dispersion=.25,orden='inclinar-girar' if j%2 else 'girar-inclinar',cuerpo='vidrio')
            if section==3:p.update(giro=2*np.pi if j<6 else 4*np.pi,referencia=1)
            events.append(p)
        for j in range(4):events.append({'t':1+section*8+j*1.8,'midi':[45,48,50,52][j],'vel':.65,'estirar':1.6,'pan':-.1})
    score={'titulo':'La vuelta deja un hueco','notas':events,'secciones':[
      {'t':0,'nombre':'Cobre enfocado'},{'t':8,'nombre':'La inclinación abre la frase'},
      {'t':16,'nombre':'El orden deja huellas en vidrio'},
      {'t':24,'nombre':'La melodía se cancela y regresa; el grave conserva el pulso'}]}
    scene,receipts=motor.render(score,34)
    results['escena']=save_audio(out,f'la-vuelta-deja-un-hueco-{tag}',scene)
    dump(out/f'partitura-{tag}.json',score)
    dump(out/f'notas-renderizadas-{tag}.json',receipts)
    exclusive(proc/f'04-frase-y-espectrograma-{tag}.png',plate('04 / La vuelta deja un hueco',
      '34 segundos · cuatro recorridos · melodía y grave hechos sólo con el Telar de fase.',audio=scene))
    # Adapter proof includes a transformed signal, not just the original case.
    grid=spectrum_grid(out,proof[:motor.SR*6],tag)
    dump(out/f'prueba-spectrumsynth-{tag}.json',grid)
    # Own sound, no interface: a waveform and spectrum become the social card.
    fig,ax=plt.subplots(figsize=(12,6.3));fig.subplots_adjust(left=.065,right=.96,bottom=.14,top=.65)
    t=np.arange(len(transformed))/motor.SR
    ax.plot(t,transformed,color=CYAN,lw=.7);ax.plot(t,dry,color=GOLD,lw=.45,alpha=.7)
    ax.set(xlim=(0,1.3),ylim=(-.5,.5));ax.axis('off')
    fig.text(.07,.86,'Telar de fase',fontsize=48,fontfamily='DejaVu Serif')
    fig.text(.075,.75,'UN CUERPO SONORO ENTRE TIEMPO Y FRECUENCIA',color=CYAN,fontsize=12)
    fig.text(.075,.09,'CANEK ZAPATA / REJILLA / 2026',color=MUTED,fontsize=12)
    og=png(fig);exclusive(out/f'telar-de-fase-{tag}.png',og)
    if not (HERE/'og.png').exists(): exclusive(HERE/'og.png',og)
    icon=Image.open(io.BytesIO(og)).crop((400,230,800,630)).resize((64,64));b=io.BytesIO();icon.save(b,format='PNG')
    if not (HERE/'favicon.png').exists(): exclusive(HERE/'favicon.png',b.getvalue())
    recipe={'fecha_real':datetime.now(ZoneInfo('America/Mexico_City')).isoformat(),
      'version':motor.VERSION,'semilla':motor.SEMILLA,'ejecucion_sha256':full,'nonce_hex':nonce.hex(),
      'identidad':'SHA256(PNG original + versión + motor.py + nonce de 24 bytes)',
      'imagen_original_sha256':sha(initial),'motor_sha256':sha(engine),
      'tag':tag,'salida':out.name,'audio':results,'pruebas':tests,'rejilla':grid,
      'limites':['Núcleo unitario continuo sobre paquetes gaussianos; salida real muestreada con portadora externa.',
        'Cada nota usa controles fijos. Cambiar controles afecta notas siguientes; no es un procesador de grabaciones.',
        'Ventana de 1.5 s y borde de 6 ms pueden cortar colas en gestos extremos.',
        'No hubo escucha humana propia; verificaciones matemáticas y de señal.'],
      'no_sobrescribir':'Carpeta exclusiva y archivos creados con xb o ffmpeg -n.',
      'fuentes':['https://doi.org/10.1016/j.jmaa.2014.03.013','https://link.springer.com/article/10.1007/s10701-012-9636-x']}
    dump(out/f'receta-{tag}.json',recipe)
    print(json.dumps({'entrega':out.name,'audio':results,'spectrumsynth_snr_db':grid['snr_db']},ensure_ascii=False),flush=True)


def finish(out):
    out=out.resolve()
    if out.parent != HERE:raise ValueError('La entrega debe vivir dentro del proyecto')
    recipe_path=next(out.glob('receta-*.json'));recipe=json.loads(recipe_path.read_text(encoding='utf-8'));tag=recipe['tag']
    files=sorted((out/'proceso').glob('*.png'))
    frames=[ImageOps.pad(Image.open(p).convert('RGB'),(960,600),color=BG) for p in files]
    dest=out/f'telar-de-fase-proceso-{tag}.gif'
    with dest.open('xb') as f:frames[0].save(f,format='GIF',save_all=True,append_images=frames[1:],duration=[1400]*len(frames),loop=0,optimize=True)
    with Image.open(dest) as gif:
        duration=0
        for i in range(gif.n_frames):gif.seek(i);duration+=gif.info.get('duration',0)
        assert duration<=10000 and dest.stat().st_size<=15*1024**2
        gifmeta={'duracion_s':duration/1000,'bytes':dest.stat().st_size,'cuadros':gif.n_frames,'loop':gif.info.get('loop')}
    text='# Proceso real del Telar de fase\n\n21 de octubre de 2026. Semilla 20261021. Ejecución `'+recipe['ejecucion_sha256']+'`.\n\n'
    explanations=['Síntesis del cuerpo original: siete paquetes complejos gaussianos.',
      'Aplicación real de dilatación, chirp y dispersión; la fuente y ganancia se conservan.',
      'Audio medido del origen, cancelación de una vuelta y retorno de dos vueltas.',
      'Partitura renderizada: cuatro secciones de melodía y grave con el motor.',
      'Captura de la interfaz local después de implementar y probar los controles.']
    for i,p in enumerate(files):text+=f'{i+1}. [{p.name}]({p.name}): {explanations[min(i,4)]}\n'
    text+='\nEl GIF reúne estas etapas de cálculo y construcción; no representa pasos internos de un generador de imágenes. Las elipses de la interfaz son contornos de paquetes individuales, no una distribución completa de Wigner.\n\nEl nombre descriptivo y hash siguen el acuerdo del 13 de octubre: no se sobrescribieron corridas anteriores. Los PNGs tienen el mismo identificador y semilla.\n'
    exclusive(out/'proceso'/'README.md',text.encode('utf-8'))
    dump(out/f'verificacion-final-{tag}.json',{'gif':gifmeta,'pngs':[{ 'archivo':p.name,'tamano':Image.open(p).size} for p in files]})
    hashes={str(p.relative_to(out)):sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}
    dump(out/f'huellas-contenido-{tag}.json',{'ejecucion_sha256':recipe['ejecucion_sha256'],'archivos_sha256':hashes})
    print(json.dumps({'gif':str(dest),'verificacion':gifmeta},ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cerrar',type=Path);a=p.parse_args()
    finish(a.cerrar) if a.cerrar else produce()
