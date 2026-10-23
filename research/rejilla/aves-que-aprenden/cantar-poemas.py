"""Loop 3/4: registrar fuentes; luego componer dos interpretaciones de Siringua."""
from pathlib import Path
import sys,json,hashlib,subprocess,shutil
import numpy as np
from scipy import signal
from scipy.io import wavfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageOps

out=Path(sys.argv[1]).resolve();stage=sys.argv[2]
recipe=json.loads(next(out.glob('receta-*.json')).read_text('utf-8'));sr=recipe['sr'];tag=recipe['tag'];proc=out/'proceso'
def fresh(p):
    if p.exists():raise FileExistsError(p)
    return p
def write(p,txt):
    with fresh(p).open('x',encoding='utf-8')as f:f.write(txt)
def read(slug,stem):
    rate,x=wavfile.read(out/f'{slug}-{stem}-{tag}.wav');assert rate==sr;assert np.isfinite(x).all();return x.astype(float)
def norm(x,rms=.115):
    x=x-x.mean(axis=0);active=np.abs(x)>max(np.max(np.abs(x))*1e-3,1e-10)
    level=np.sqrt(np.mean(x[active]**2)) if active.any() else 1
    return x*min(rms/max(level,1e-12),.78/max(np.max(np.abs(x)),1e-12))
def smooth(x,hz=45):return signal.sosfilt(signal.butter(2,hz,fs=sr,output='sos'),x)
def plot_sources():
    fig,ax=plt.subplots(2,1,figsize=(12,6.6),layout='constrained');fig.patch.set_facecolor('#f5f1e8')
    for a,p in zip(ax,recipe['poemas']):
        for e in p['eventos']:
            a.plot([e['t'],e['t']+e['dur']],[e['nota']]*2,color='#1c5672',lw=3)
        for e in p['aves']:
            a.plot([e['t'],e['t']+e['dur']],[e['m'],e.get('m2',e['m'])],color='#b4542f',lw=1,alpha=.65)
        a.set_title(p['title'],loc='left');a.set_ylabel('Altura MIDI');a.set_xlabel('Segundos')
        a.text(.99,.05,f"{len(p['eventos'])} palabras · {p['dur']:.2f} s",ha='right',transform=a.transAxes)
    fig.suptitle('01 · Dos poemas, dos fuentes que se contestan\nAzul: articulación / Cobre: silbidos y respuestas',fontsize=16)
    fig.savefig(fresh(proc/f'01-partituras-{tag}.png'),dpi=120);plt.close(fig)
def spectrogram(ax,x,label):
    if x.ndim>1:x=x.mean(axis=1)
    f,t,s=signal.spectrogram(x,sr,nperseg=512,noverlap=384)
    z=10*np.log10(np.maximum(s,1e-14));z-=z.max()
    ax.pcolormesh(t,f,z,vmin=-65,vmax=0,cmap='magma',shading='auto',rasterized=True)
    ax.set_ylim(80,6500);ax.set_ylabel('Hz');ax.set_xlabel('Segundos');ax.set_title(label,loc='left',fontsize=11)
if stage=='fuentes':
    # Captura antes de calcular el vocoder y la mezcla de los poemas.
    plot_sources()
    for p in recipe['poemas']:
        assert all(e['fonemas']for e in p['eventos'])
        assert max(s['t1']for s in p['segmentos'])<p['dur']
    print('Partituras capturadas; fonemas y límites temporales comprobados.');sys.exit()

bands=np.geomspace(100,8500,29)
def vocode(mod,car):
    y=np.zeros(len(mod));car=norm(car)
    for lo,hi in zip(bands[:-1],bands[1:]):
        sos=signal.butter(3,[lo,hi],btype='bandpass',fs=sr,output='sos')
        env=np.maximum(0,smooth(np.abs(signal.sosfilt(sos,mod)),32))
        y+=env*signal.sosfilt(sos,car)
    return norm(y)
def delay(x,sec):
    y=np.zeros_like(x);n=int(sr*sec)
    if n<len(x):y[n:]=x[:-n]
    return y
results=[];stats=[]
for p in recipe['poemas']:
    slug=p['slug'];water=norm(read(slug,'agua'));bird=norm(read(slug,'aves'));car=read(slug,'siringe')
    voc=vocode(water,car);gate=np.zeros(len(water));clarity=np.zeros(len(water));pan=np.zeros(len(water))
    for s in p['segmentos']:
        if s['clase']!='vocal':gate[int(s['t0']*sr):int(s['t1']*sr)]=1
    for e in p['eventos']:
        a=int(e['t']*sr);b=int((e['t']+e['dur']+.12)*sr)
        clarity[a:b]=e['clarity'];pan[a:b]=[-.32,.05,-.15][e['line']%3]
    gate=smooth(gate,100);clarity=smooth(clarity,18);pan=smooth(pan,12)
    hybrid=norm(.78*voc+.65*water*gate+.15*water)
    # La articulación aparece y vuelve a retirarse en las llamadas del final.
    lead=(.12+.95*clarity)*hybrid
    calls=(.88-.55*clarity)*bird
    left=lead*np.sqrt((1-pan)/2)+.55*calls
    right=lead*np.sqrt((1+pan)/2)+.8*delay(calls,.014)
    dry=np.column_stack([left,right]);wet=dry.copy()
    # Ecos cortos de rama; no realimentación, colas finitas.
    for dt,g in [(.137,.105),(.293,.065),(.467,.035)]:wet+=g*delay(dry[:,::-1],dt)
    wet=norm(wet,.12)
    # Fade del resultado completo y del margen final, sin cortar ninguna palabra.
    fade=int(.04*sr);wet[:fade]*=np.linspace(0,1,fade)[:,None];wet[-fade:]*=np.linspace(1,0,fade)[:,None]
    dest=fresh(out/f'{slug}-{tag}.wav')
    with dest.open('xb')as f:wavfile.write(f,sr,(wet*32767).astype(np.int16))
    m4a=fresh(dest.with_suffix('.m4a'))
    subprocess.run(['ffmpeg','-v','error','-n','-i',str(dest),'-c:a','aac','-b:a','192k',str(m4a)],check=True)
    # Referencia articulada para diagnosticar el idioma separadamente del pájaro.
    ref=fresh(out/f'{slug}-referencia-agua-{tag}.wav')
    with ref.open('xb')as f:wavfile.write(f,sr,(norm(water)*32767).astype(np.int16))
    subprocess.run(['ffmpeg','-v','error','-n','-i',str(ref),'-c:a','aac','-b:a','128k',str(fresh(ref.with_suffix('.m4a')))],check=True)
    decoded=subprocess.run(['ffmpeg','-v','error','-i',str(m4a),'-f','f32le','-'],capture_output=True,check=True).stdout
    a=np.frombuffer(decoded,dtype='<f4');assert np.isfinite(a).all();assert np.max(np.abs(a))<1
    results.append((p,wet,water,voc))
    stats.append({'poema':p['title'],'segundos':len(wet)/sr,'palabras':len(p['eventos']),'fonemas':len(p['segmentos']),
                  'pico_pcm':float(np.max(np.abs(wet))),'pico_aac':float(np.max(np.abs(a))),'rms':float(np.sqrt(np.mean(wet*wet))),
                  'finito':True,'escucha':'pendiente de escucha humana; no se afirma inteligibilidad'})

fig,ax=plt.subplots(2,1,figsize=(12,6.6),layout='constrained');fig.patch.set_facecolor('#f5f1e8')
for a,(p,x,w,v)in zip(ax,results):spectrogram(a,v,p['title']+' · sólo vocoder, antes de consonantes y canto')
fig.suptitle('02 · El agua articula la siringe\nVocoder de 28 bandas · texto español y fonética inglesa de repertorio',fontsize=16)
fig.savefig(fresh(proc/f'02-vocoder-bilingue-{tag}.png'),dpi=120);plt.close(fig)
fig,ax=plt.subplots(2,1,figsize=(12,6.6),layout='constrained');fig.patch.set_facecolor('#f5f1e8')
for a,(p,x,w,v)in zip(ax,results):spectrogram(a,x,p['title']+' · interpretación completa')
fig.suptitle('03 · Siringua canta dos poemas\nAgua, siringe grave, silbidos independientes y respuestas',fontsize=16)
png=fresh(proc/f'03-dos-poemas-cantados-{tag}.png');fig.savefig(png,dpi=120);plt.close(fig)
shutil.copyfile(png,fresh(out/f'siringua-dos-poemas-{tag}.png'))
frames=[ImageOps.contain(Image.open(p).convert('RGB'),(1000,560))for p in sorted(proc.glob('*.png'))]
gif=fresh(out/f'siringua-aprende-dos-poemas-{tag}.gif');frames[0].save(gif,save_all=True,append_images=frames[1:],duration=2600,loop=0,optimize=True)
im=ImageOps.contain(Image.open(png).convert('RGB'),(1200,630));og=Image.new('RGB',(1200,630),'#f5f1e8');og.paste(im,((1200-im.width)//2,(630-im.height)//2));og.save(fresh(out/'og.png'))
with Image.open(gif)as im:
    ms=0
    for k in range(im.n_frames):im.seek(k);ms+=im.info['duration']
assert ms<=10000 and gif.stat().st_size<15*1024*1024
shutil.copyfile(__file__,fresh(out/'fuentes/cantar-poemas.py'))
write(out/f'mediciones-{tag}.json',json.dumps({'poemas':stats,'gif':{'ms':ms,'bytes':gif.stat().st_size},'metodo':'híbrido de vocoder, consonantes y agua directa; mezcla compuesta, no aprendizaje automático'},indent=2,ensure_ascii=False))
print(json.dumps({'poemas':stats,'gif_ms':ms,'gif_bytes':gif.stat().st_size},ensure_ascii=False))
