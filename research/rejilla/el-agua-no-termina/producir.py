"""Produce a new exclusive run; --cerrar DIR adds real UI captures to GIF."""
from pathlib import Path
import json,hashlib,io,os,subprocess,sys
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
from PIL import Image,ImageOps,ImageDraw
from scipy.io import wavfile
from scipy.signal import stft
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from agua import render,coeficientes_rejilla
HERE=Path(__file__).resolve().parent
VERSION='1.0.0';SEED=20261021;SR=32768
BG='#091519';INK='#e9efdf';A='#99e8cb';B='#fb9b82'
plt.rcParams.update({'figure.facecolor':BG,'axes.facecolor':BG,'axes.edgecolor':'#314b49','text.color':INK,'axes.labelcolor':INK,'xtick.color':'#9baaa6','ytick.color':'#9baaa6','font.family':'DejaVu Sans','grid.color':'#314b49'})
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,b):
    with Path(p).open('xb') as f:f.write(b)
def dump(p,o):write(p,json.dumps(o,ensure_ascii=False,indent=2).encode('utf-8'))
def png(fig):
    b=io.BytesIO();fig.savefig(b,format='png',dpi=100,facecolor=BG);plt.close(fig);return b.getvalue()
def fig(title,sub):
    f=plt.figure(figsize=(12,7.5));f.text(.06,.94,'REJILLA / EL AGUA NO TERMINA',color=A,fontsize=11);f.text(.06,.88,title,fontsize=25);f.text(.06,.83,sub,color='#9baaa6',fontsize=11);f.text(.06,.03,'CANEK ZAPATA · 2026 · modelo finito · semilla 20261021',color='#9baaa6',fontsize=10);return f
K=np.array([(x,y,z,x*x+y*y+z*z) for x in range(-2,3) for y in range(-2,3) for z in range(-2,3) if 0<x*x+y*y+z*z<=5])
def field(u,z=.4,N=65):
    xy=np.linspace(0,2*np.pi,N);x,y=np.meshgrid(xy,xy);out=np.zeros((3,N,N));u=np.array(u).reshape(-1,3,2)
    for k,v in zip(K,u):
        phase=k[0]*x+k[1]*y+k[2]*z
        out+=v[:,0,None,None]*np.cos(phase)-v[:,1,None,None]*np.sin(phase)
    return xy,out
def field_plate(h,title,sub):
    f=fig(title,sub);ax=f.add_axes([.08,.13,.55,.61]);xy,v=field(h['u']);speed=np.hypot(v[0],v[1]);ax.streamplot(xy,xy,v[0],v[1],color=speed,cmap='summer',density=1.8,linewidth=.4+1.1*speed/max(.01,speed.max()),arrowsize=.6);ax.set_aspect('equal');ax.set(xlabel='x',ylabel='y');a=f.add_axes([.72,.20,.22,.4]);a.bar(range(1,6),h['shells'],color=[A,B,A,B,A]);a.set(xlabel='Capa |k|²',ylabel='Energía');f.text(.7,.7,f"E = {h['energy']:.5f}\nΩ = {h['enstrophy']:.5f}\nt = {h['t']:.2f} s",fontsize=15,linespacing=1.8);return png(f)
def audio(out,name,y):
    p=out/(name+'.wav')
    with p.open('xb') as f:wavfile.write(f,SR,np.asarray(y,np.float32))
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-n','-i',str(p),'-c:a','aac','-b:a','192k',str(out/(name+'.m4a'))],check=True)
    return {'m4a':name+'.m4a','duration_s':len(y)/SR,'peak':float(abs(y).max()),'rms':float(np.sqrt(np.mean(y*y)))}
def grid(out,y,tag):
    full=coeficientes_rejilla(y,SR);recovered=np.fft.irfft(full.transpose(1,2,0)*SR,n=SR,axis=1).reshape(-1,2)[:len(y)]
    exact=float(np.linalg.norm(y-recovered)/np.linalg.norm(y));assert exact<1e-12
    z=full[:,:,:SR//2].copy();z[:,:,0]=0;mag=np.vstack([abs(z[1]).T[::-1],abs(z[0]).T[::-1]]);phase=np.vstack([np.angle(z[1]).T[::-1],np.angle(z[0]).T[::-1]])
    scale=mag.max();w=mag.shape[1];h=mag.shape[0]
    for name,a in [('magnitud',np.round(mag/scale*65535)),('fase',np.round((phase+np.pi)/(2*np.pi)*65535))]:
        a=a.astype('<u2');write(out/f'rejilla-{name}-{tag}.raw',a.tobytes());b=io.BytesIO();Image.fromarray(a).save(b,format='PNG');write(out/f'rejilla-{name}-{tag}.png',b.getvalue())
    inp=lambda name:['-f','rawvideo','-pix_fmt','gray16le','-s',f'{w}x{h}','-r','1','-i',str(out/f'rejilla-{name}-{tag}.raw')]
    dest=out/f'rejilla-vuelta-{tag}.wav'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-n',*inp('magnitud'),*inp('fase'),'-filter_complex',f'[0]setpts=N/TB,format=gray16le[m];[1]setpts=N/TB,format=gray16le[p];[m][p]spectrumsynth=sample_rate={SR}:channels=2:scale=lin:slide=fullframe:win_func=rect:overlap=0','-c:a','pcm_f32le',str(dest)],check=True)
    _,got=wavfile.read(dest);got=got[:len(y)]*scale
    representable=full.copy();representable[:,:,0]=0;representable[:,:,-1]=0
    target=np.fft.irfft(representable.transpose(1,2,0)*SR,n=SR,axis=1).reshape(-1,2)[:len(y)]
    snr=float(20*np.log10(np.linalg.norm(target)/np.linalg.norm(target-got)))
    original_snr=float(20*np.log10(np.linalg.norm(y)/np.linalg.norm(y-got)))
    assert snr>55,('SNR señal representable',snr,'SNR original',original_snr)
    return {'DFT_relative_error':exact,'spectrumsynth_SNR_without_DC_Nyquist_dB':snr,'spectrumsynth_SNR_original_dB':original_snr,'magnitude_scale':float(scale),'sr':SR,'columns':w,'DC_Nyquist':'Retirados sólo al escribir las imágenes de spectrumsynth; incluidos en el adaptador completo.'}
def build(out,tag):
    engine=(HERE/'motor.mjs').read_text(encoding='utf-8');template=(HERE/'interfaz.html').read_text(encoding='utf-8')
    html=template.replace('/* MOTOR */',engine).replace('__ENGINE_JSON__',json.dumps(engine,ensure_ascii=False))
    write(out/f'el-agua-no-termina-{tag}.html',html.encode('utf-8'))
    # Syntax-check the actual portable module.
    script=html.split('<script type="module">')[1].split('</script>')[0];p=out/f'comprobar-html-{tag}.mjs';write(p,script.encode('utf-8'));subprocess.run(['node','--check',str(p)],check=True)
def produce():
    tests=json.loads(subprocess.check_output(['node',str(HERE/'pruebas.mjs')],text=True))
    f=fig('01 / Un cuerpo de 56 modos','Dominio periódico tridimensional; bola simétrica 0 < |k|² ≤ 5.');ax=f.add_axes([.15,.13,.7,.6],projection='3d');ax.scatter(*K[:,:3].T,c=K[:,3],cmap='summer',s=50);ax.set(xlabel='kx',ylabel='ky',zlabel='kz');first=png(f)
    nonce=os.urandom(24).hex();run=sha(first+VERSION.encode()+(HERE/'motor.mjs').read_bytes()+nonce.encode());tag=f's{SEED}-{run[:12]}';out=HERE/f'el-agua-no-termina-{tag}';out.mkdir(exist_ok=False);proc=out/'proceso';proc.mkdir()
    dump(out/f'identidad-{tag}.json',{'run_sha256':run,'nonce':nonce,'version':VERSION,'seed':SEED,'date':datetime.now(ZoneInfo('America/Mexico_City')).isoformat(),'identity_inputs':['PNG 01','version','motor.mjs','nonce']});write(proc/f'01-modos-{tag}.png',first);dump(out/f'pruebas-{tag}.json',tests);print(out,flush=True)
    common={'nu':.035,'midi':45,'speed':1,'nonlinear':1};kick={'t':.1,'kick':{'x':.7,'y':1.5,'z':.4,'force':.7,'fine':.3}}
    dry,meta=render({'initial':common,'events':[kick]},duracion=9,sr=SR);dump(out/f'impulso-y-estados-{tag}.json',meta);print('impulso y estados',flush=True)
    write(proc/f'02-impulso-{tag}.png',field_plate(meta['history'][3],'02 / Un impulso queda adentro','Captura del estado calculado: campo, cinco escalas y energía.'))
    write(proc/f'03-intercambio-{tag}.png',field_plate(meta['history'][72],'03 / Los remolinos se afectan','El mismo cuerpo seis segundos después; sin añadir otra excitación.'))
    linear,lmeta=render({'initial':{**common,'nonlinear':0},'events':[kick]},duracion=9,sr=SR)
    visc,vmeta=render({'initial':{**common,'nu':.27},'events':[kick]},duracion=9,sr=SR)
    f=fig('04 / Suavizar tiene una consecuencia','Mismo impulso y ganancia: las escalas pequeñas se disipan antes.');ax=f.add_axes([.09,.15,.84,.58]);
    for label,m,col in [('Flujo ν=.035',meta,A),('Sólo disipación',lmeta,B),('Flujo ν=.27',vmeta,'#b4a3ed')]:
        ax.plot([h['t'] for h in m['history']],[h['enstrophy'] for h in m['history']],color=col,label=label)
    ax.set(xlabel='Tiempo musical (s)',ylabel='Enstrofía');ax.legend(facecolor=BG,labelcolor=INK);write(proc/f'04-disipacion-{tag}.png',png(f))
    residue=float(np.linalg.norm(dry-linear)/np.linalg.norm(dry));tests['audio_nonlinear_vs_linear_relative_difference']=residue
    comp=np.concatenate([dry,np.zeros((SR//2,2)),linear,np.zeros((SR//2,2)),visc]);audios={'comparacion':audio(out,f'tres-aguas-misma-fuerza-{tag}',comp),'impulso':audio(out,f'un-remolino-{tag}',dry)}
    events=[kick,{'t':3,'params':{'midi':48}},{'t':5,'kick':{'x':3.6,'y':2.2,'force':.45,'fine':.8}},{'t':7,'params':{'midi':52}},{'t':10,'params':{'midi':55}},{'t':12,'kick':{'x':1,'y':4.2,'force':.35,'fine':1}},{'t':14,'params':{'midi':50,'nu':.22}},{'t':18,'params':{'midi':45,'nu':.035}},{'t':20,'kick':{'x':.7,'y':1.5,'force':.4,'fine':.1}}]
    song,smeta=render({'initial':common,'events':events},duracion=26,sr=SR);dump(out/f'partitura-y-estados-{tag}.json',smeta);audios['recorrido']=audio(out,f'el-agua-insiste-{tag}',song);print('muestras listas',flush=True)
    f=fig('05 / El agua insiste','26 segundos. Un cuerpo, tres impulsos nuevos y cambios de altura y viscosidad.');ax=f.add_axes([.08,.13,.86,.60]);freq,t,z=stft(song.mean(axis=1),fs=SR,nperseg=1024,noverlap=768);ax.pcolormesh(t,freq,20*np.log10(np.maximum(abs(z),1e-7)),cmap='magma',vmin=-85,vmax=-25,shading='auto');ax.set(ylim=(0,3500),xlabel='Tiempo (s)',ylabel='Frecuencia audible (Hz)');write(proc/f'05-partitura-{tag}.png',png(f))
    g=grid(out,dry[:SR*6],tag);dump(out/f'verificacion-rejilla-{tag}.json',g)
    # Own-field artwork, no interface overlays. Preserved at required OG dimensions.
    f=plt.figure(figsize=(12,6.3));ax=f.add_axes([0,0,1,1]);xy,v=field(smeta['history'][70]['u'],N=100);speed=np.hypot(v[0],v[1]);ax.streamplot(xy,xy,v[0],v[1],color=speed,cmap='summer',density=2.5,linewidth=.5+2*speed/max(.01,speed.max()),arrowsize=.65);ax.set_aspect('equal',adjustable='datalim');ax.axis('off');cover=png(f);write(out/f'el-agua-campo-{tag}.png',cover)
    for p in [out/'og.png',HERE/'og.png']:
        if not p.exists():write(p,cover)
    im=Image.open(io.BytesIO(cover)).resize((64,64));b=io.BytesIO();im.save(b,format='PNG')
    for p in [out/'favicon.png',HERE/'favicon.png']:
        if not p.exists():write(p,b.getvalue())
    build(out,tag);dump(out/f'receta-{tag}.json',{'run_sha256':run,'seed':SEED,'version':VERSION,'tests':tests,'rejilla':g,'audios':audios,'finite_model':'56 Fourier modes on a 3D torus, exact truncated convolution, Leray projection, RK4','sonification':'moving spatial probe with c=(1,3,7), smooth coefficient interpolation and explicit tanh output','saturator_samples':{k:m['output_saturator_samples'] for k,m in [('dry',meta),('linear',lmeta),('viscous',vmeta),('song',smeta)]},'source_sha256':{p.name:sha(p.read_bytes()) for p in [HERE/'motor.mjs',HERE/'agua.py',HERE/'interfaz.html']}})
    write(HERE/'abrir-agua.bat',('@echo off\r\nstart "" "%~dp0'+out.name+'\\el-agua-no-termina-'+tag+'.html"\r\n').encode('utf-8'))
    print('DONE '+tag,flush=True)
def close(out):
    out=Path(out);tag=out.name.removeprefix('el-agua-no-termina-');paths=sorted((out/'proceso').glob('*.png'));frames=[]
    for p in paths:
        im=ImageOps.contain(Image.open(p).convert('RGB'),(1000,680));bg=Image.new('RGB',(1000,680),BG);bg.paste(im,((1000-im.width)//2,(680-im.height)//2));frames.append(bg.quantize(colors=128))
    duration=min(1200,9000//len(frames));dest=out/f'el-agua-proceso-{tag}.gif'
    with dest.open('xb') as f:frames[0].save(f,format='GIF',save_all=True,append_images=frames[1:],duration=duration,loop=0,optimize=True)
    gif=Image.open(dest);total=0
    for i in range(gif.n_frames):gif.seek(i);gif.convert('RGB').load();total+=gif.info['duration']
    assert total<=10000 and dest.stat().st_size<=15*1024*1024
    text='# Proceso real · El agua no termina\n\nLas etapas 01–05 se guardaron durante el cálculo, antes de construir el portátil. Las capturas posteriores corresponden a pruebas reales de la interfaz. El GIF reúne esas etapas; no es una ejecución continua ni muestra procesos ocultos.\n\n'+''.join(f'{i+1}. [{p.name}]({p.name})\n' for i,p in enumerate(paths))+f'\nSemilla documental {SEED}; el motor no usa ruido aleatorio. GIF: {total/1000:g} s, {dest.stat().st_size} bytes, loop infinito. Identidad completa y nonce en identidad; hashes de contenido en manifiesto. Se aplica el acuerdo de nombres del 13 de octubre: carpeta exclusiva y archivos nuevos; ninguna entrega se sobrescribe.\n'
    write(out/'proceso'/'README.md',text.encode('utf-8'));dump(out/f'manifiesto-{tag}.json',{'files':{str(p.relative_to(out)):sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()},'GIF_duration_ms':total,'GIF_bytes':dest.stat().st_size});print(dest)
if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--cerrar':close(sys.argv[2])
    else:produce()
