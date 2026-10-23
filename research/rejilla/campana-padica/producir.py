"""Actual mathematics, audio and process images. Every run is exclusive."""
from pathlib import Path
import hashlib,io,json,os,subprocess,argparse
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
from scipy.io import wavfile
from scipy.signal import stft
from PIL import Image,ImageOps
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from campana import render,coeficientes_rejilla

ROOT=Path(__file__).resolve().parent;SEED=20261021;SR=24000
BG='#17151d';FG='#f0e9da';MUTED='#b3aabb';GOLD='#edb976';PURPLE='#c4b0ff'
plt.rcParams.update({'figure.facecolor':BG,'axes.facecolor':BG,'axes.edgecolor':'#413c50','text.color':FG,
 'axes.labelcolor':MUTED,'xtick.color':MUTED,'ytick.color':MUTED,'font.family':'DejaVu Sans','font.size':11})
def put(path,data):
    with Path(path).open('xb') as f:f.write(data)
def dump(path,obj):put(path,json.dumps(obj,ensure_ascii=False,indent=2).encode('utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def png(fig):
    b=io.BytesIO();fig.savefig(b,format='png',dpi=100);plt.close(fig);return b.getvalue()
def figure(title,subtitle):
    fig=plt.figure(figsize=(12,7.5));fig.text(.07,.94,'REJILLA / CAMPANA P-ÁDICA',color=GOLD,fontsize=11)
    fig.text(.07,.88,title,fontsize=27);fig.text(.07,.83,subtitle,color=MUTED,fontsize=11)
    fig.text(.07,.025,'CANEK ZAPATA · 2026 · semilla 20261021 · datos y señal del motor',color=MUTED,fontsize=10)
    return fig
def test():
    p=subprocess.run(['node',str(ROOT/'pruebas.mjs')],check=True,capture_output=True)
    r=json.loads(p.stdout);a=r.pop('analytic');ms=r['matrices'];L=np.array(a['matrix']);w,V=np.linalg.eigh(L)
    om=2*np.pi*440*2**((a['midi']-69)/12)*np.sqrt(1+a['tension']*w);v0=np.zeros(64);v0[a['zone']]=a['velocity']
    exact=V@(np.sin(om*a['t'])/om*(V.T@v0));err=float(np.linalg.norm(exact-a['q'])/np.linalg.norm(exact))
    m0=np.array(ms['local']);m1=np.array(ms['padic'])
    r['referenceEigenError']=err;r['commutatorNorm']=float(np.linalg.norm(m0@m1-m1@m0))
    r['matrixSymmetryError']=float(np.max(abs(m1-m1.T)));r['rowSumError']=float(np.max(abs(m1.sum(axis=1))))
    r['minimumEigenvalues']=[float(np.linalg.eigvalsh(m).min()) for m in [m0,m1]]
    assert err<.0005 and r['commutatorNorm']>.1 and min(r['minimumEigenvalues'])>-1e-12
    return r
def audio(out,name,score):
    dump(out/(name+'-partitura.json'),score)
    y,receipt=render(score,score['duration'],SR)
    assert np.isfinite(y).all() and abs(y).max()>1e-4 and not receipt['metrics']['limitedFrames']
    with (out/(name+'.wav')).open('xb') as f:wavfile.write(f,SR,y.astype(np.float32))
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-n','-i',str(out/(name+'.wav')),'-c:a','aac','-b:a','192k',str(out/(name+'.m4a'))],check=True)
    dump(out/(name+'-estado.json'),receipt)
    return y,receipt
def spectrogram(title,subtitle,y,sr=SR):
    fig=figure(title,subtitle);a=fig.add_axes([.09,.53,.86,.23]);b=fig.add_axes([.09,.12,.86,.29]);t=np.arange(len(y))/sr
    a.plot(t[::16],y.mean(axis=1)[::16],color=GOLD,lw=.6);a.set(xlabel='Tiempo (s)',ylabel='Amplitud')
    f,t,z=stft(y.mean(axis=1),fs=sr,nperseg=2048,noverlap=1792)
    b.pcolormesh(t,f,20*np.log10(np.maximum(abs(z),1e-7)),vmin=-90,vmax=-30,cmap='magma',shading='auto');b.set(ylim=(0,1500),xlabel='Tiempo (s)',ylabel='Frecuencia (Hz)')
    return png(fig)
def produce():
    tests=test();local=np.array(tests['matrices']['local']);padic=np.array(tests['matrices']['padic'])
    # First captured transformation: calculate actual arithmetic distances.
    distances=np.zeros((64,64))
    for i in range(64):
      for j in range(64):
       if i!=j:
        n=abs(i-j);k=0
        while n%2==0:n//=2;k+=1
        distances[i,j]=2**(-k)
    fig=figure('01 / Cambiar lo que significa cerca','64 regiones; cercanía por congruencia módulo 2, 4, 8, 16 y 32.')
    a=fig.add_axes([.09,.13,.43,.62]);im=a.imshow(distances,cmap='magma_r',vmin=0,vmax=1);a.set(xlabel='Región',ylabel='Región')
    b=fig.add_axes([.62,.22,.31,.44]);b.axis('off');b.text(0,.92,'d₂(1, 2) = 1\nd₂(1, 3) = ½\nd₂(1, 9) = ⅛',fontsize=24,color=GOLD,linespacing=1.9);b.text(0,.1,'Los números nombran regiones.\nLa distancia decide sus conexiones.',color=MUTED,fontsize=12)
    first=png(fig);nonce=os.urandom(24);engine=(ROOT/'motor.mjs').read_bytes();full=hashlib.sha256(first+engine+b'1.0.0'+nonce).hexdigest();tag=f's{SEED}-{full[:12]}'
    out=ROOT/f'campana-distancias-{tag}';out.mkdir(exist_ok=False);proc=out/'proceso';proc.mkdir();print(str(out),flush=True)
    dump(out/f'identidad-{tag}.json',{'ejecucion_sha256':full,'nonce_hex':nonce.hex(),'semilla':SEED,'version':'1.0.0',
      'imagen_inicial_sha256':hashlib.sha256(first).hexdigest(),'motor_sha256':hashlib.sha256(engine).hexdigest(),
      'identidad':'SHA256(PNG inicial + motor.mjs + versión + nonce)'})
    put(proc/f'01-distancias-aritmeticas-{tag}.png',first)
    dump(out/f'pruebas-{tag}.json',tests);put(out/f'motor-{tag}.mjs',engine)
    fig=figure('02 / De la superficie al parentesco','Matrices reales del Laplaciano: conexiones locales y conexiones 2-ádicas.')
    for i,(m,name) in enumerate([(local,'Vecindad ordinaria · cuadrícula'),(padic,'Vecindad 2-ádica · familias')]):
        ax=fig.add_axes([.09+i*.47,.16,.37,.59]);ax.imshow(-m+np.diag(np.diag(m)),cmap='magma',vmin=0,vmax=.5);ax.set(title=name,xlabel='Región',ylabel='Región')
    put(proc/f'02-matrices-de-conexion-{tag}.png',png(fig))
    positions={'duration':10,'initial':{'fold':1,'depth':.7,'tension':7,'damping':.65,'midi':48,'pickup':1},'events':[]}
    for i,zone in enumerate([1,2,9]):positions['events'] += [{'t':i*3.2,'clear':True},{'t':.15+i*3.2,'hit':zone,'vel':.8}]
    yp,rp=audio(out,f'tres-zonas-un-parentesco-{tag}',positions)
    put(proc/f'03-golpear-1-2-y-9-{tag}.png',spectrogram('03 / Tres zonas, un parentesco','Mismo cuerpo, afinación y fuerza; zonas 1, 2 y 9, con captación fija en la familia 1.',yp))
    fold={'duration':10,'initial':{'fold':0,'depth':.7,'tension':7,'damping':.2,'midi':48,'pickup':1},'events':[{'t':.12,'hit':9,'vel':.8},{'t':1.4,'params':{'fold':1}},{'t':3.7,'params':{'depth':1.8}},{'t':5.8,'params':{'fold':0,'depth':.7}}]}
    yf,rf=audio(out,f'un-golpe-cambia-de-mundo-{tag}',fold)
    put(proc/f'04-un-golpe-y-tres-transformaciones-{tag}.png',spectrogram('04 / Un golpe cambia de mundo','Sólo un golpe a 0.12 s; plegado a 1.4 s, profundidad a 3.7 s y regreso a 5.8 s.',yf))
    score={'duration':34,'initial':{'fold':0,'depth':.7,'tension':7,'damping':.55,'midi':45,'pickup':1},'events':[]}
    for t,z in zip([.2,2.5,4.5,6.5],[9,1,2,9]):score['events'].append({'t':t,'hit':z,'vel':.8})
    score['events'].append({'t':8,'params':{'fold':1,'midi':48,'tension':8,'damping':.35}})
    for t,z in zip([8.5,10,11.5,13],[1,9,17,25]):score['events'].append({'t':t,'hit':z,'vel':.72})
    score['events'] += [{'t':16,'params':{'depth':1.7,'tension':11,'damping':.2,'midi':50}},
      {'t':16.4,'hit':33,'vel':.8},{'t':18,'params':{'fold':.4}},{'t':20,'params':{'fold':1}},
      {'t':21,'params':{'midi':55}},{'t':22,'hit':17,'vel':.65},{'t':24,'params':{'fold':0,'tension':6,'damping':.5,'midi':48}}]
    for t,z,m in zip([25,27,29],[1,9,33],[52,50,48]):score['events'].append({'t':t,'params':{'midi':m},'hit':z,'vel':.6})
    ys,rs=audio(out,f'la-campana-aprende-otra-distancia-{tag}',score)
    put(proc/f'05-frase-en-un-solo-cuerpo-{tag}.png',spectrogram('05 / La campana aprende otra distancia','34 segundos · golpes, parentesco, pliegue sostenido y una frase de regreso.',ys))
    Z=coeficientes_rejilla(ys,SR);recovered=np.fft.irfft(Z.transpose(1,2,0)*SR,n=SR,axis=1).reshape(-1,2)[:len(ys)]
    error=float(np.linalg.norm(recovered-ys)/np.linalg.norm(ys));assert error<1e-12
    # Social image from the actual strongest connections, with no UI overlay.
    fig=plt.figure(figsize=(12,6.3));ax=fig.add_axes([.04,.05,.92,.62]);ax.axis('off');ax.set(xlim=(-1.4,1.4),ylim=(-.75,.75))
    ang=np.arange(64)/64*2*np.pi;xx=np.cos(ang);yy=.57*np.sin(ang)
    for j in range(64):
        if j!=9:
            w=-padic[9,j];ax.plot([xx[9],xx[j]],[yy[9],yy[j]],color=PURPLE,lw=.4+5*w,alpha=.15+min(.7,w*2))
    ax.scatter(xx,yy,s=20,c=GOLD);ax.scatter([xx[9]],[yy[9]],s=80,c=PURPLE)
    fig.text(.07,.86,'Campana de distancias imposibles',fontsize=30,fontfamily='DejaVu Serif');fig.text(.07,.77,'CANEK ZAPATA / REJILLA / 2026',fontsize=11,color=GOLD)
    og=png(fig);put(out/f'campana-distancias-{tag}.png',og)
    if not (ROOT/'og.png').exists():put(ROOT/'og.png',og)
    if not (ROOT/'favicon.png').exists():
        b=io.BytesIO();Image.open(io.BytesIO(og)).crop((340,200,860,630)).resize((64,64)).save(b,format='PNG');put(ROOT/'favicon.png',b.getvalue())
    recipe={'fecha_real':datetime.now(ZoneInfo('America/Mexico_City')).isoformat(),'version':'1.0.0','semilla':SEED,'ejecucion_sha256':full,'nonce_hex':nonce.hex(),
     'identidad':'SHA256(PNG inicial + motor.mjs + versión + nonce)','imagen_inicial_sha256':hashlib.sha256(first).hexdigest(),'motor_sha256':hashlib.sha256(engine).hexdigest(),'tag':tag,
     'pruebas':{k:v for k,v in tests.items() if k!='matrices'},'rejilla_dft_error_relativo':error,
     'audio':{'tres_zonas':rp['metrics'],'un_golpe':rf['metrics'],'frase':rs['metrics']},
     'limites':['Modelo finito 2-ádico inspirado en operadores jerárquicos; no todo Q₂ ni implementación validada del operador de Vladimirov.',
     'La modulación cambia la rigidez y realiza trabajo; sólo se prueba conservación numérica aproximada con parámetros fijos y sin amortiguación.',
     'Sin escucha humana propia; el valor musical se entrega a evaluación mediante muestras.'],
     'fuentes':['https://arxiv.org/abs/math-ph/0012019','https://arxiv.org/abs/math-ph/0303045']}
    dump(out/f'receta-{tag}.json',recipe)
    print(json.dumps({'entrega':out.name,'dft_error':error,'picos':recipe['audio']},ensure_ascii=True),flush=True)
def finish(out):
    out=out.resolve()
    if out.parent!=ROOT:raise ValueError('Entrega fuera del proyecto')
    r=json.loads(next(out.glob('receta-*.json')).read_text(encoding='utf-8'));tag=r['tag'];files=sorted((out/'proceso').glob('*.png'))
    frames=[ImageOps.pad(Image.open(p).convert('RGB'),(960,600),color=BG) for p in files]
    dest=out/f'campana-padica-proceso-{tag}.gif'
    with dest.open('xb') as f:frames[0].save(f,format='GIF',save_all=True,append_images=frames[1:],duration=1200,loop=0,optimize=True)
    g=Image.open(dest);duration=0
    for i in range(g.n_frames):g.seek(i);duration+=g.info.get('duration',0)
    assert duration<=10000 and dest.stat().st_size<15*1024**2
    txt='# Proceso real de la Campana p-ádica\n\n21 de octubre de 2026. Semilla 20261021. Ejecución `'+r['ejecucion_sha256']+'`.\n\n'
    for p in files:txt+=f'- [{p.name}]({p.name})\n'
    txt+='\nOrden: cálculo de distancias → matrices de acoplamiento → golpes en tres zonas → un golpe transformado sin reiniciar → frase del mismo cuerpo → capturas reales de la interfaz. Los PNGs se conservaron al producir cada transformación. El GIF reúne etapas reales de cálculo y construcción, no simula un proceso histórico.\n\nLas matrices y espectrogramas son datos del motor; la animación de la interfaz muestra sus desplazamientos reales. El PNG de resultado y og.png se trazaron con la matriz de conexiones. Nombres descriptivos, semilla y hash según el acuerdo del 13 de octubre; carpeta exclusiva y archivos sin sobrescritura.\n'
    put(out/'proceso'/'README.md',txt.encode('utf-8'))
    dump(out/f'verificacion-proceso-{tag}.json',{'gif':dest.name,'duracion_s':duration/1000,'bytes':dest.stat().st_size,'cuadros':g.n_frames,'loop':g.info.get('loop')})
    print(json.dumps({'gif':dest.name,'duration_s':duration/1000,'bytes':dest.stat().st_size}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cerrar',type=Path);a=p.parse_args();finish(a.cerrar) if a.cerrar else produce()
