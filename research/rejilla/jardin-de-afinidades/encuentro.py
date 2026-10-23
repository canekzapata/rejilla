"""Primer encuentro: síntesis aditiva, dos cuerpos y una huella. Salidas exclusivas."""
from pathlib import Path
import hashlib, json, os, subprocess
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, stft
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

ROOT=Path(__file__).resolve().parent
SR=48000; DUR=48; SEED=161026
rng=np.random.default_rng(SEED)
t=np.arange(SR*DUR)/SR
def curve(knots): return np.interp(t,*np.array(knots).T)
def smooth(knots):
    x=curve(knots)
    return x*x*(3-2*x)
fa=220+0.025*np.sin(2*np.pi*.071*t)
delta=curve([(0,7),(8,7),(14,3),(20,.6),(24,0),(31,0),(37,-2),(43,-5),(48,-5)])
fb=(3*fa+delta)/2
contact=smooth([(0,0),(18,0),(25,1),(31,1),(38,0),(48,0)])
ea=smooth([(0,0),(5,1),(39,1),(48,0)])
eb=smooth([(0,0),(7,0),(14,1),(39,1),(46,0),(48,0)])
plt.rcParams.update({'figure.facecolor':'#101d22','axes.facecolor':'#101d22','text.color':'#e6e8d4','axes.labelcolor':'#e6e8d4','xtick.color':'#a8bdbc','ytick.color':'#a8bdbc','axes.edgecolor':'#536667','font.family':'DejaVu Sans'})
def figure(): return plt.subplots(figsize=(12,6.3),dpi=100)
def finish(fig,title):
    fig.suptitle('JARDÍN DE AFINIDADES / '+title,fontsize=17,x=.06,ha='left')
    fig.text(.06,.025,'Canek Zapata · primer encuentro · síntesis aditiva · semilla 161026',fontsize=10)
    fig.tight_layout(rect=(.04,.06,.98,.91))
def save(fig,p):
    with p.open('xb') as f:fig.savefig(f,format='png',facecolor=fig.get_facecolor())
    plt.close(fig)
fig,ax=figure()
ax.plot(t[::480],(3*fa)[::480],color='#f1d58c',label='Cuerpo A · tercer parcial')
ax.plot(t[::480],(2*fb)[::480],color='#8fd5cc',label='Cuerpo B · segundo parcial')
ax.set(xlabel='segundos',ylabel='Hz',ylim=(653,669));ax.legend(facecolor='#203238',labelcolor='#e6e8d4');ax.grid(alpha=.15)
finish(fig,'01 / acercamiento escrito')
nonce=os.urandom(24).hex()
fig.canvas.draw()
digest=hashlib.sha256(bytes(fig.canvas.buffer_rgba())+Path(__file__).read_bytes()+nonce.encode()).hexdigest();tag=digest[:12]
out=ROOT/f'primer-encuentro-s{SEED}-{tag}';out.mkdir(exist_ok=False)
(out/'proceso').mkdir()
save(fig,out/'proceso'/f'01-acercamiento-s{SEED}-{tag}.png')
print(out,flush=True)
def writejson(name,data):
    with (out/name).open('x',encoding='utf8') as f:json.dump(data,f,ensure_ascii=False,indent=2)
writejson('receta-inicial.json',{'id':digest,'nonce':nonce,'semilla':SEED,'sr':SR,'duracion':DUR,'fuente_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'metodo':'Síntesis aditiva; no usa los modelos físicos del banco. Subarmónicos compuestos por división de frecuencia.'})
def body(f,env,kind):
    y=np.zeros(len(t));components=[]
    for n in range(1,19):
        amp=(1/n**1.18)*(1 if kind==0 or n%2 else .52)
        # Cada banda respira con velocidad distinta; los parciales de contacto quedan alineados a su fundamental.
        chosen=n==(3 if kind==0 else 2)
        freq=n*f+(0 if chosen else .028*n*np.sin(2*np.pi*(.023+n*.002)*t+kind+n))
        phase=2*np.pi*np.cumsum(freq)/SR+rng.uniform(-np.pi,np.pi)
        gain=(1+.08*np.sin(2*np.pi*(.09+n*.006)*t+n))
        if chosen:gain=gain*(1+2.1*contact)
        bright=curve([(0,.35),(12,.60),(25,1),(33,.8),(48,.35)])
        gain=gain*(1 if n<4 else bright)
        part=amp*gain*np.sin(phase)
        y+=part
        if chosen:components.append(part*env)
    # Una raíz divisora de cada cuerpo, introducida con lentitud.
    rootphase=2*np.pi*np.cumsum(f/2)/SR
    y+=.26*np.sin(rootphase)*smooth([(0,0),(9,0),(21,1),(40,1),(48,0)])
    breath=sosfilt(butter(2,[700,4200],fs=SR,btype='bandpass',output='sos'),rng.normal(0,1,len(t)))
    y+=breath*(.013 if kind==0 else .026)
    return (y*env*.18).astype(np.float32),components[0]*.18
a,pa=body(fa,ea,0);b,pb=body(fb,eb,1)
# Huella: A retiene suavemente 330 Hz después del contacto, B retiene 220.
memory=smooth([(0,0),(30,0),(35,1),(41,1),(48,0)])
a+=.034*memory*np.sin(2*np.pi*330*t+.3)
b+=.028*memory*np.sin(2*np.pi*220*t+1.2)
fig,ax=figure()
freq,tt,z=stft(a+b,SR,nperseg=8192,noverlap=6144)
sel=(freq>60)&(freq<1600)
ax.pcolormesh(tt,freq[sel],20*np.log10(np.abs(z[sel])+1e-7),cmap='magma',vmin=-85,vmax=-25,shading='auto')
ax.set(xlabel='segundos',ylabel='Hz',ylim=(60,1600));finish(fig,'02 / cuerpos sintetizados')
save(fig,out/'proceso'/f'02-cuerpos-s{SEED}-{tag}.png')
print('Cuerpos y espectro guardados',flush=True)
# Primer plano estéreo moderado; reflexiones filtradas y colas largas sin chorus tonal.
dry=np.column_stack((.84*a+.48*b,.48*a+.84*b))
wet=np.zeros_like(dry)
for k,delay in enumerate([.127,.193,.311,.449,.673,.947,1.313,1.831,2.477,3.211]):
    shift=round(delay*SR);g=.13*np.exp(-delay/1.9)
    source=dry[:,::-1] if k%2 else dry
    filtered=sosfilt(butter(1, max(1600,5800-k*380),fs=SR,output='sos'),source,axis=0)
    wet[shift:]+=g*filtered[:-shift]
mix=dry+wet
mix*=smooth([(0,1),(44,1),(48,0)])[:,None]
mix*=.76/np.max(np.abs(mix))
assert np.isfinite(mix).all()
base=f'primer-encuentro-s{SEED}-{tag}'
with (out/(base+'.wav')).open('xb') as f:wavfile.write(f,SR,mix.astype(np.float32))
ff='C:/msys64/mingw64/bin/ffmpeg.exe'
r=subprocess.run([ff,'-hide_banner','-nostdin','-n','-i',str(out/(base+'.wav')),'-af','loudnorm=I=-19:TP=-2:LRA=12','-c:a','aac','-b:a','256k',str(out/(base+'.m4a'))],capture_output=True,text=True)
assert r.returncode==0,r.stderr
probe=subprocess.run([ff,'-hide_banner','-nostdin','-i',str(out/(base+'.m4a')),'-af','loudnorm=I=-19:TP=-2:LRA=12:print_format=json','-f','null','-'],capture_output=True,text=True)
metrics=json.JSONDecoder().raw_decode(probe.stderr[probe.stderr.rfind('{'):])[0]
writejson('medidas.json',{'aac':metrics,'finito':True,'duracion':DUR,'separacion_parciales_Hz':{'inicio':7,'contacto_24_31s':0,'salida':-5},'escucha':'Sin escucha humana en la producción. Prueba pendiente de reacción de Canek.'})
fig,axes=plt.subplots(2,1,figsize=(12,6.3),dpi=100)
axes[0].plot(t[::480],mix[::480,0],color='#8fd5cc',linewidth=.5)
axes[0].set(xlabel='segundos',ylabel='amplitud',xlim=(0,DUR))
axes[1].pcolormesh(tt,freq[sel],20*np.log10(np.abs(z[sel])+1e-7),cmap='magma',vmin=-85,vmax=-25,shading='auto')
axes[1].set(xlabel='segundos',ylabel='Hz',ylim=(60,1600))
finish(fig,'03 / encuentro, floración y huella')
final=out/f'jardin-resultado-s{SEED}-{tag}.png';save(fig,final)
with Image.open(final) as im:
    with (out/'og.png').open('xb') as f:im.save(f,'PNG')
    with (out/'proceso'/f'03-mezcla-s{SEED}-{tag}.png').open('xb') as f:im.save(f,'PNG')
frames=[]
for p in sorted((out/'proceso').glob('*.png')):
    with Image.open(p) as im:frames.append(im.convert('RGB').resize((900,472)).quantize(colors=128))
gif=out/f'jardin-proceso-s{SEED}-{tag}.gif'
with gif.open('xb') as f:frames[0].save(f,format='GIF',save_all=True,append_images=frames[1:],duration=2400,loop=0,optimize=False)
with Image.open(gif) as im:assert im.n_frames==3 and sum((im.seek(i) or im.info['duration']) for i in range(im.n_frames))==7200
assert gif.stat().st_size<15_000_000
with (out/'proceso'/'README.md').open('x',encoding='utf8') as f:f.write('# Proceso real\n\n1. Trayectorias escritas antes de sintetizar.\n2. Espectrograma de los dos cuerpos sintetizados, antes del espacio y máster.\n3. Mezcla: onda del premáster y el mismo espectrograma de cuerpos como referencia. No es espectrograma del AAC.\n\nEl GIF reúne estas tres etapas efectivamente generadas; 7.2 s en loop. Síntesis aditiva, semilla 161026. El hash de ejecución combina imagen inicial, programa y nonce; los archivos se crean de forma exclusiva.\n')
with (out/'README.md').open('x',encoding='utf8') as f:f.write(f'# Jardín de afinidades — primer encuentro\n\nPrueba de 48 segundos, 16 de octubre de 2026. Dos cuerpos de síntesis aditiva, fundamentales alrededor de 220 y 330 Hz. Sus parciales tercero y segundo se acercan desde 7 Hz de separación y coinciden de 24 a 31 s. Después se separan hasta 5 Hz y conservan una huella a 330/220 Hz. Raíces por división a la mitad de cada fundamental. Sin letra.\n\nNo usa los modelos físicos existentes: esta prueba aísla el mecanismo espectral antes de incorporar sus materiales. No es todavía la obra completa de cinco minutos. Sin escucha humana durante producción.\n\nAudio: {base}.m4a; WAV flotante local excluido de git. PNGs y GIF en proceso/ y en esta carpeta. Máster AAC medido en medidas.json. Trayectorias programadas, no estimaciones auditivas de batimientos.\n')
with (out/'encuentro-fuente.py').open('xb') as f:f.write(Path(__file__).read_bytes())
hashes={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}
writejson('receta.json',{'id':digest,'nonce':nonce,'semilla':SEED,'contenido_sha256':hashes})
print(json.dumps({'carpeta':str(out),'medidas':metrics,'gif_bytes':gif.stat().st_size},ensure_ascii=False),flush=True)
