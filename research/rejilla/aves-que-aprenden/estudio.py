"""Comparación reproducible; síntesis y gráficas reales, sin evaluación perceptiva automática."""
from pathlib import Path
import sys,json,hashlib,subprocess,shutil
import numpy as np
from scipy import signal
from scipy.io import wavfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

out=Path(sys.argv[1]).resolve(); stage=sys.argv[2]
recipe_path=next(out.glob('receta-*.json')); recipe=json.loads(recipe_path.read_text('utf-8'))
tag=f"s{recipe['semilla']}-{recipe['id']}"; sr=recipe['sr']; proc=out/'proceso'
def exclusive(p):
    if p.exists(): raise FileExistsError(p)
    return p
def read(stem):
    rate,x=wavfile.read(out/f'{stem}-{tag}.wav'); assert rate==sr
    return x.astype(float)
def norm(x, rms=.12):
    x=np.asarray(x); x=x-x.mean(axis=0)
    active=np.abs(x)>max(np.max(np.abs(x))*1e-3,1e-10)
    level=np.sqrt(np.mean(x[active]**2)) if np.any(active) else 1
    return x*min(rms/max(level,1e-12),.84/max(np.max(np.abs(x)),1e-12))
def save(stem,x):
    assert np.all(np.isfinite(x))
    x=norm(x); dest=exclusive(out/f'{stem}-{tag}.wav')
    with dest.open('xb') as f: wavfile.write(f,sr,(x*32767).astype(np.int16))
    m4a=exclusive(dest.with_suffix('.m4a'))
    subprocess.run(['ffmpeg','-v','error','-n','-i',str(dest),'-c:a','aac','-b:a','160k',str(m4a)],check=True)
    return x
def figure(num,title,rows,sub):
    fig,axes=plt.subplots(len(rows),1,figsize=(12,6.6),layout='constrained')
    fig.patch.set_facecolor('#f5f1e8')
    for ax,(label,x) in zip(np.atleast_1d(axes),rows):
        if x.ndim>1:x=x.mean(axis=1)
        f,t,S=signal.spectrogram(x,sr,nperseg=512,noverlap=416)
        z=10*np.log10(np.maximum(S,1e-14));z-=z.max()
        ax.pcolormesh(t,f,z,vmin=-65,vmax=0,cmap='magma',shading='auto',rasterized=True)
        ax.set_ylim(80,6000);ax.set_ylabel('Hz');ax.set_title(label,loc='left',fontsize=11)
    np.atleast_1d(axes)[-1].set_xlabel('Tiempo (segundos)')
    fig.suptitle(title+'\n'+sub,fontsize=15)
    p=exclusive(proc/f'{num:02d}-{title.lower().replace(" ","-")}-{tag}.png')
    fig.savefig(p,dpi=120);plt.close(fig);return p

water=read('01-agua-dice');bird=read('02-pajaro-doble');carrier=read('03-siringe-grave-cruda')
if stage=='fuentes':
    figure(1,'Tres fuentes reales',[("Agua: fonemas de «todavía estoy aquí»",water),('Dos lados: silbidos con trayectorias independientes',bird),('Siringe grave: fuente antes del filtro del pico',carrier)],'Primera captura del experimento · semilla 18026')
    save('04-referencia-agua',water);save('05-referencia-pajaro',bird)
    print('Fuentes capturadas y referencias AAC listas.');sys.exit()

# Vocoder de canales: modulador y portadora pasan por los mismos filtros.
# La envolvente del agua gobierna cada banda de la fuente de pájaro.
# Se preserva el contraste espectral de la portadora: NO se amplifican bandas vacías.
edges=np.geomspace(100,8500,29);smooth=signal.butter(2,32,fs=sr,output='sos')
def vocode(mod,car):
    car=norm(car); result=np.zeros_like(mod);envelopes=[];energies=[]
    for lo,hi in zip(edges[:-1],edges[1:]):
        bp=signal.butter(3,[lo,hi],btype='bandpass',fs=sr,output='sos')
        m=signal.sosfilt(bp,mod);c=signal.sosfilt(bp,car)
        env=np.maximum(0,signal.sosfilt(smooth,np.abs(m)))
        result+=env*c
        envelopes.append(env);energies.append(float(np.sqrt(np.mean(c*c))))
    return norm(result),np.array(envelopes),energies
narrow,env,eN=vocode(norm(water),bird)
wide,_,eW=vocode(norm(water),carrier)
save('06-vocoder-silbido-estrecho',narrow);save('07-vocoder-siringe-rica',wide)
figure(2,'El agua articula al pajaro',[("Control: vocoder con silbidos agudos",narrow),('Vocoder: siringe grave sin el filtro del pico',wide),('Modulador: agua que articula la frase',water)],'28 bandas · 100–8500 Hz · envolventes a 32 Hz · sin voz humana grabada')

# Híbrido explícito. Consonantes del agua por segmentación; el vocoder conserva las vocales.
# No se vende como vocoder puro ni como reconstrucción exacta de una siringe animal.
segments=json.loads((out/'segmentos.json').read_text('utf-8'))
gate=np.zeros(len(water))
for seg in segments:
    if seg['clase'] not in ('vocal',):
        a=max(0,int(seg['t0']*sr)); b=min(len(gate),int(seg['t1']*sr));gate[a:b]=1
gate=signal.sosfilt(signal.butter(1,100,fs=sr,output='sos'),gate)
articulated=norm(.78*norm(wide)+.65*norm(water)*gate+.15*norm(water))
save('08-hibrido-con-consonantes',articulated)
gap=np.zeros(int(.65*sr))
# Tres ensayos de una misma frase: el agua entra progresivamente, el pájaro sigue independiente.
repeats=[]
for k in range(3):
    a=[.03,.35,.85][k];b=[1,.68,.22][k]
    left=b*norm(bird)+a*articulated
    # Un pequeño retardo separa en espacio las dos fuentes, no simula dos voces biológicas nuevas.
    right=b*np.roll(norm(bird),int(.009*sr))+a*articulated
    pair=np.column_stack([left,right]);pair=norm(pair)
    repeats.extend([pair,np.column_stack([gap,gap])])
learning=np.concatenate(repeats)
save('09-el-pajaro-aprende',learning)
figure(3,'Tres intentos de decir',[("1. Canto / 2. Aparece articulación / 3. Predomina el mensaje",learning)],'«todavía estoy aquí» · mezcla progresiva, no aprendizaje automático')

# Diagnóstico de bandas: cantidad de bandas con energía respecto al máximo de cada fuente.
threshold=-35
def bands(e):
    e=np.array(e);return int(np.sum(20*np.log10(np.maximum(e,1e-15)/max(e))>threshold))
stats={'bandas':28,'rango_hz':[100,8500],'envolvente_hz':32,
       'bandas_a_menos_de_35db_del_maximo':{'silbido':bands(eN),'siringe_rica':bands(eW)},
       'duracion_aprendizaje':len(learning)/sr,'escucha_humana':'pendiente; no se afirma inteligibilidad',
       'metodo':'Vocoder de canales + consonantes de VozAgua + mezcla progresiva en el híbrido final',
       'archivos':{}}
for p in out.glob('*.wav'):
    rate,y=wavfile.read(p); yf=y.astype(float)/(32768 if y.dtype==np.int16 else 1)
    assert np.isfinite(yf).all()
    stats['archivos'][p.name]={'segundos':len(y)/rate,'pico':float(np.max(np.abs(yf))),
                             'rms':float(np.sqrt(np.mean(yf*yf))),'finito':True}
with exclusive(out/f'mediciones-{tag}.json').open('x',encoding='utf-8') as f:json.dump(stats,f,indent=2,ensure_ascii=False)
frames=[]
for p in sorted(proc.glob('*.png')):
    im=Image.open(p).convert('RGB');im.thumbnail((1000,600));frames.append(im)
gif=exclusive(out/f'como-el-agua-da-palabras-al-pajaro-{tag}.gif')
frames[0].save(gif,save_all=True,append_images=frames[1:],duration=2400,loop=0,optimize=True)
shutil.copyfile(sorted(proc.glob('03-*.png'))[0],exclusive(out/f'el-pajaro-aprende-{tag}.png'))
with Image.open(gif) as im:
    duration=0
    for k in range(im.n_frames):im.seek(k);duration+=im.info['duration']
assert duration<=10000 and gif.stat().st_size<=15*1024**2
recipe['resultado']={'mediciones':stats,'gif':{'duracion_ms':duration,'bytes':gif.stat().st_size},
 'sha256_contenidos':{str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and p!=recipe_path}}
with exclusive(out/f'receta-final-{tag}.json').open('x',encoding='utf-8') as f:json.dump(recipe,f,indent=2,ensure_ascii=False)
print(json.dumps({k:v for k,v in stats.items() if k!='archivos'},ensure_ascii=False));print(gif)
