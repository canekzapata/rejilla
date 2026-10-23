"""Producir los motores recuperados con audio, datos, PNGs y GIF obligatorios.
Uso por el asistente: python python/motores_propios.py ejemplos/motores-propios/siringua.json
"""
import argparse,ast,hashlib,importlib.util,json,math,shutil,subprocess,sys,uuid
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent
def load(path):
    spec=importlib.util.spec_from_file_location('motor_'+hashlib.sha256(str(path).encode()).hexdigest()[:12],path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def producir(archivo,destino=None):
    import numpy as np
    from scipy import signal
    from scipy.io import wavfile
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from PIL import Image,ImageOps
    raw=Path(archivo).read_bytes();req=json.loads(raw.decode('utf-8-sig'));rows=json.loads((BASE/'MOTORES-NUEVOS.json').read_text(encoding='utf8'));row=next(x for x in rows if x['id']==req['motor_propio']);c={**row['config'],**req.get('config',{})}
    source=BASE/row['archivo'];nonce=uuid.uuid4().hex;full=hashlib.sha256(raw+source.read_bytes()+Path(__file__).read_bytes()+(BASE/'og.png').read_bytes()+nonce.encode()).hexdigest();tag=full[:12];seed=int(c.get('semilla',20261020));parent=Path(destino)if destino else BASE/'salidas';parent.mkdir(parents=True,exist_ok=True);out=parent/f"{row['id']}-s{seed}-{tag}";out.mkdir(exist_ok=False);proc=out/'proceso';proc.mkdir()
    (out/f'pedido-{tag}.json').write_bytes(raw);sr=48000;traces={};parts={};meta={}
    print(row['nombre']+' -> '+str(out),flush=True)
    if row['tipo']in('js','siringua','siringua-vocoder','traductor','volcan'):
        node=shutil.which('node')
        if not node:raise RuntimeError('Este motor necesita Node.js. Consulta el manual; el asistente puede preparar la instalación.')
        source_raw=out/f'pcm-{tag}.f32';subprocess.run([node,str(BASE/'python/render_propio.cjs'),str(Path(archivo).resolve()),str(source_raw)],check=True,cwd=BASE)
        meta=json.loads(Path(str(source_raw)+'.json').read_text(encoding='utf8'));sr=meta['sr'];audio=np.fromfile(source_raw,dtype=np.float32).reshape(-1,meta['channels'])
        parts={k:np.fromfile(out/v,dtype=np.float32)for k,v in meta['partes'].items()}
        if row['tipo']=='siringua-vocoder':
            # Funciones originales del ensayo, sin ejecutar su programa de línea de comandos.
            tree=ast.parse(source.read_text(encoding='utf8'));defs=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in('norm','vocode')];env={'np':np,'signal':signal,'sr':sr,'edges':np.geomspace(100,8500,29),'smooth':signal.butter(2,32,fs=sr,output='sos')};exec(compile(ast.Module(body=defs,type_ignores=[]),str(source),'exec'),env)
            norm,vocode=env['norm'],env['vocode'];water,carrier,bird=parts['agua'],parts['portadora'],parts['ave'];wide,envs,energies=vocode(norm(water),carrier);gate=np.zeros(len(water))
            for seg in meta['segmentos']:
                if seg['clase']!='vocal':gate[max(0,int(seg['t0']*sr)):min(len(gate),int(seg['t1']*sr))]=1
            gate=signal.sosfilt(signal.butter(1,100,fs=sr,output='sos'),gate);art=norm(.78*norm(wide)+.65*norm(water)*gate+.15*norm(water));u=np.linspace(0,1,len(water));left=(1-.75*u)*norm(bird)+(.04+.81*u)*art;audio=np.column_stack((left,(1-.75*u)*np.roll(norm(bird),int(.009*sr))+(.04+.81*u)*art));parts['vocoder']=wide;traces={'aparicion_articulacion':(.04+.81*u),'consonantes':gate};meta['energia_portadora_por_banda']=energies
        if row['tipo']=='traductor':
            traces['oxido']=np.interp(np.arange(len(audio))/sr,*np.array(c['oxido']).T)
    elif row['tipo']in('cinta','lago'):
        M=load(source);d=float(c['dur']);N=round(d*sr);t=np.arange(N)/sr
        if c.get('entrada_wav'):
            rate,x=wavfile.read(c['entrada_wav']);dtype=x.dtype;x=x.astype(float)
            if np.issubdtype(dtype,np.signedinteger):x/=float(2**(np.iinfo(dtype).bits-1))
            elif not np.issubdtype(dtype,np.floating):raise ValueError('Entrada WAV: usar PCM16/PCM32 o float.')
            if rate!=sr:x=signal.resample_poly(x,sr//math.gcd(sr,rate),rate//math.gcd(sr,rate),axis=0)
            if x.ndim==1:x=np.column_stack((x,x))
        else:
            x=np.zeros((N,2))
            for at in np.arange(.1,d-.5,.5):
                L=min(round(.45*sr),N-round(at*sr));u=np.arange(L)/sr;v=(np.sin(2*np.pi*220*u)+.35*np.sin(2*np.pi*554.36*u))*np.exp(-u*12);i=round(at*sr);x[i:i+L]+=v[:,None]*.4
        parts['entrada']=x
        if row['tipo']=='cinta':
            pts=np.array(c['velocidad']);mp=M.mapa(lambda tau:float(np.interp(tau,pts[:,0],pts[:,1])),len(x)/sr);audio,vt=M.tocar(x,mp,N,curv=lambda s:.5+.4*math.sin(s),semilla=seed);traces['velocidad']=vt
        else:
            audio,measure=M.lago(x,.1,1.3,d,semilla=seed);audio+=x*.2;meta['vueltas']=measure
    elif row['tipo']in('cobre','halo'):
        sr=32000;N=round(float(c.get('dur',4))*sr);tt=np.arange(N)/sr;x=np.zeros(N)
        events=c['eventos']
        for e in events:
            a=round(e['t']*sr);n=min(N-a,round(e['dur']*sr));t=np.arange(n)/sr;f0=440*2**((e['nota']-69)/12)
            x[a:a+n]+=sum(np.sin(2*np.pi*f0*h*t)/h for h in range(1,13)if f0*h<sr*.45)*np.minimum(1,t/.02)*np.minimum(1,(n/sr-t)/.07)*.13
        parts['entrada']=x
        tree=ast.parse(source.read_text(encoding='utf8'));names=('env','unit','active','level','resonador_cobre')if row['tipo']=='cobre'else('env','active','level','stereo');defs=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names]
        env={'np':np,'SR':sr,'iirpeak':signal.iirpeak,'lfilter':signal.lfilter,'N':N,'hz':lambda m:440*2**((np.asarray(m)-69)/12)}
        exec(compile(ast.Module(body=defs,type_ignores=[]),str(source),'exec'),env)
        if row['tipo']=='cobre':audio=env['resonador_cobre'](x,events)
        else:
            main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');helpers=[n for n in main.body if isinstance(n,ast.FunctionDef)and n.name in('blank','add')];exec(compile(ast.Module(body=helpers,type_ignores=[]),str(source),'exec'),env)
            start=next(i for i,n in enumerate(main.body)if isinstance(n,ast.Assign)and any(isinstance(a,ast.Name)and a.id=='halo'for a in n.targets));stop=next(i for i in range(start+1,len(main.body))if isinstance(main.body[i],ast.Expr)and isinstance(main.body[i].value,ast.Call)and isinstance(main.body[i].value.func,ast.Name)and main.body[i].value.func.id=='save')
            env.update(P={'frases':[{'id':0,'voz':'demo','bar':20,'eventos':events}]},vocal={'demo':x})
            exec(compile(ast.Module(body=main.body[start:stop],type_ignores=[]),str(source),'exec'),env)
            audio=env['halo']+env['echo'];meta['selecciones']=env['measurements'];meta['aprendizaje_retorno']=env['learn'];meta['extraccion']='Bloque AST original de Halo, sin ejecutar la canción completa; guía aditiva de demostración.'
    else:
        M=load(source);N=round(float(c.get('dur',4))*sr);kwargs=dict(c.get('argumentos',{}));import inspect
        fn=getattr(M,row['funcion']);params=inspect.signature(fn).parameters
        if 'semilla'in params:kwargs['semilla']=seed
        result=fn(N=N,**kwargs)
        if isinstance(result,tuple):
            audio=result[0]
            if row['funcion']=='luciernagas':traces['coherencia']=result[2];meta['destellos']=len(result[3])
        else:audio=result
    audio=np.asarray(audio,dtype=float)
    if audio.ndim==1:audio=np.column_stack((audio,audio))
    if not np.isfinite(audio).all()or np.max(np.abs(audio))<1e-8:raise ValueError('Motor sin señal válida')
    peak=float(np.max(np.abs(audio)));gain=min(1,.85/peak);audio*=gain
    wave=out/f"{row['id']}-s{seed}-{tag}.wav";wavfile.write(wave,sr,np.round(np.clip(audio,-1,1)*32767).astype(np.int16))
    imgs=[]
    def figsave(fig,num,name):
        p=proc/f'{num:02d}-{name}-s{seed}-{tag}.png';fig.savefig(p,dpi=120,bbox_inches='tight');plt.close(fig);imgs.append(p)
    fig,axes=plt.subplots(2,1,figsize=(11,6));fig.suptitle(row['nombre'])
    notes=c.get('eventos',c.get('notas',c.get('golpes',[])))
    if meta.get('partitura'):notes=meta['partitura']['waterEvents']
    for i,n in enumerate(notes):
        if isinstance(n,dict):axes[0].plot([n.get('t',0),n.get('t',0)+n.get('dur',.2)],[n.get('m',n.get('nota',n.get('midi',i)))]*2,lw=3)
    if not axes[0].lines:axes[0].text(.02,.7,row['idea'],wrap=True,transform=axes[0].transAxes,fontsize=10)
    axes[0].set(xlabel='Segundos',ylabel='Nota o índice del evento',title='Entradas / intención del ejemplo')
    for key,a in traces.items():
        arr=np.asarray(a);step=max(1,len(arr)//1600);axes[1].plot(np.linspace(0,len(audio)/sr,len(arr))[::step],arr[::step],label=key)
    if not traces:
        for key in ['oxido','cerca','dir','velocidad','caldera','brama']:
            if key in c and isinstance(c[key],list):axes[1].plot(*np.array(c[key]).T,label=key)
    if axes[1].lines:axes[1].legend(loc='upper right',fontsize=8)
    else:axes[1].text(.02,.5,'Parámetros exactos en el pedido JSON y la receta.',transform=axes[1].transAxes)
    axes[1].set(xlabel='Segundos',title='Controles / trazas (unidades según leyenda)');fig.tight_layout();figsave(fig,1,'entradas-controles')
    fig,ax=plt.subplots(figsize=(11,4));tt=np.arange(len(audio))/sr;step=max(1,len(audio)//18000);ax.plot(tt[::step],audio[::step,0],lw=.5);ax.set(title='Audio calculado · canal izquierdo',xlabel='Segundos',ylabel='Amplitud');figsave(fig,2,'onda')
    fig,ax=plt.subplots(figsize=(11,4));f,tt,power=signal.spectrogram(audio.mean(axis=1),sr,nperseg=1024,noverlap=768);ax.pcolormesh(tt,f,10*np.log10(np.maximum(power,1e-14)),shading='auto',cmap='magma',vmin=-105,vmax=-35);ax.set(yscale='log',ylim=(30,min(sr/2-10,14000)),xlabel='Segundos',ylabel='Hz',title='Espectrograma del resultado');figsave(fig,3,'espectrograma')
    frames=[ImageOps.pad(Image.open(p).convert('RGB'),(1000,550),color='white')for p in imgs];frames[0].save(out/f'proceso-{row["id"]}-s{seed}-{tag}.gif',save_all=True,append_images=frames[1:],duration=1700,loop=0,optimize=True)
    (proc/'README.md').write_text('Etapas reales calculadas en esta ejecución: entradas/controles, onda y espectrograma. GIF de 5.1 s. No representa borradores históricos.\n'+row['idea']+'\nLímite: '+row['limite']+'\n',encoding='utf8')
    r={'ejecucion':full,'nonce':nonce,'semilla':seed,'motor':row['id'],'origen':row['archivo'],'fuente_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'adaptador_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'config':c,'sample_rate':sr,'duracion':len(audio)/sr,'pico_crudo':peak,'ganancia_final':gain,'detalles':meta,'limite':row['limite'],'evaluacion':'Señal y archivos comprobados; no equivale a escucha humana.'}
    (out/f'receta-{tag}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2,default=lambda x:x.tolist()if hasattr(x,'tolist')else str(x)),encoding='utf8')
    (out/'HUELLAS.json').write_text(json.dumps({p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in out.rglob('*')if p.is_file()},indent=2),encoding='utf8')
    print('Listo: '+str(out),flush=True);return out
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('pedido');ap.add_argument('--destino');a=ap.parse_args();producir(a.pedido,a.destino)
