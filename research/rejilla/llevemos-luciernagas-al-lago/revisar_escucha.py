"""Revisión localizada tras la escucha de Canek; conserva el audio desde 2:33.333."""
from pathlib import Path
import json,hashlib,secrets,sys,gzip,subprocess,math,gc
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter,sosfilt
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

B=Path(__file__).resolve().parent
OLD=B/'luciernagas-cancion-s1-22ac84d49ccd'
SR=48000;JOIN=153.33333333333334;J=round(JOIN*SR)
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,x):
    with p.open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=1)
def setup():
    nonce=secrets.token_hex(16)
    ident=sha((OLD/'partitura.json').read_bytes()+(OLD/'og.png').read_bytes()+Path(__file__).read_bytes()+nonce.encode())
    out=B/('luciernagas-relevos-s1-'+ident[:12]);out.mkdir(exist_ok=False);(out/'proceso').mkdir();(out/'render').mkdir()
    p=json.loads((OLD/'partitura.json').read_text(encoding='utf8'));p['version']='v9-escucha';p['relevos_escucha']=[]
    # Cada retiro tiene continuación instrumental escrita, no una cuota de silencio.
    replaced={'raiz','tenis','coro-noche','coro-otras'}
    phrases={f:[e for e in p['eventos']['voz'] if e['frase']==f] for f in replaced}
    for name in ['voz','duo','boca']:
        for e in p['eventos'][name]:
            if e['t']<93.333 and (name!='voz' or e['frase'] in replaced):e['salidas']=[];e['retiro_v9']='ceder la conducción a instrumentos'
    # R se extiende, Q se fragmenta y su última nota deja una respuesta en otro cuerpo.
    plans=[('raiz','clarinete',20.,1.12,0),('tenis','piano',29.16666667,.95,-12),
           ('respuesta-vi','chelo',38.4,.72,-12),('coro-noche','clarinete',60.33333333,1.08,0),
           ('coro-otras','piano',74.5,1.16,0)]
    n=0
    for phrase,part,start,stretch,trans in plans:
        motif=p['tema_R'] if part in ['clarinete','chelo'] else p['tema_Q']
        for k,(beat,midi,dur) in enumerate(motif):
            # La segunda respuesta invierte el contorno de R sobre Mi, conservando ritmo.
            pitch=(128-midi if phrase=='coro-noche' else midi)+trans
            t=start+beat*p['negra_s']*stretch;d=dur*p['negra_s']*stretch
            if phrase=='coro-otras' and k==len(motif)-1:d*=1.4
            n+=1;event={'id':f'escucha-relevo-{n:03}','t':t,'dur':d,'midi':pitch,'hz':440*2**((pitch-69)/12),
                'vel':.66 if k%3 else .82,'pan':.32 if part=='clarinete' else -.4 if part=='piano' else -.2,
                'articulacion':'R invertida' if phrase=='coro-noche' else 'frase instrumental con respiración',
                'frase':'relevo-'+phrase,'seccion':'I' if t<26.667 else 'II' if t<53.334 else 'III',
                'ancestro':phrases[phrase][min(k,len(phrases[phrase])-1)]['id'] if phrase in phrases else 'tema_R',
                'salidas':[[t,t+d+.13]],'procedencia':'revisión de escucha: conducción instrumental'}
            p['eventos'][part].append(event);p['relevos_escucha'].append(dict(event,parte=part))
    # Un minuto de escucha cercana conserva el reloj y los estados de la reunión.
    oldcuts=p['oscuridades'];lengths=[.35,.55,.45,.8,.6,.7,.45,.9]
    newcuts=[]
    for (a,b),length in zip(oldcuts,lengths):
        # Último aliento desemboca en la entrada original; los demás, en el centro del hueco.
        end=b if b>150 else (a+b+length)/2
        newcuts.append([end-length,end])
    for c in p['cortes_buses']:
        for old,new in zip(oldcuts,newcuts):
            if abs(c['t']-old[0])<1e-7:c['t'],c['fin']=new;c['revision']='v9: oscuridad breve, mantener estado'
    p['oscuridades']=newcuts
    p['observaciones_centro_v9']={'guitarra':[[93.4833333333,105.95]],'cuerda':[[106.0400949,115.85],[125.34865856,134.2]],
      'waterphone':[[106.6700949,109.5]],'campana':[[134.44865856,138.7]],
      'juncos':'observaciones intermitentes del estado recibido: fase absoluta, amortiguación, sin reataque ni reinicio'}
    p['interpretacion_v9']={'voz_antes_del_centro_db':-9,'boca_antes_del_centro':'salida cerrada; el reloj sigue',
      'captacion_centro':'ganancia activa hasta +24 dB, envolvente RMS interpolada cada 250 ms; conserva fase, no energía acústica',
      'centro_rms_dbfs':-33,'conservar_pcm_desde_s':JOIN,
      'alcance':'Revisión de exposición y centro; reunión, solos, regreso y pared conservados del audio r2.'}
    dump(out/'partitura-v9.json',p)
    dump(out/'inicio.json',{'hash_ejecucion':ident,'nonce':nonce,'version':'relevos-escucha-1','semilla':p['semilla'],
        'fuente':str(OLD),'imagen_sha256':sha((OLD/'og.png').read_bytes()),'programa_sha256':sha(Path(__file__).read_bytes()),
        'partitura_anterior_sha256':sha((OLD/'partitura.json').read_bytes()),'partitura_v9_sha256':sha((out/'partitura-v9.json').read_bytes())})
    (B/'REVISION-ESCUCHA-ACTUAL.txt').write_text(out.name,encoding='utf8')
    fig,ax=plt.subplots(figsize=(12,5));ax.barh(['v8: oscuridad','v9: oscuridad'],[sum(b-a for a,b in oldcuts),sum(lengths)],color=['#a16c73','#8cae9a'])
    ax.set_xlim(0,60);ax.set_xlabel('Segundos en el centro de un minuto');ax.set_title('Primera corrección escrita tras la escucha de Canek')
    fig.savefig(out/'proceso'/('01-cortes-reescritos-s1-'+ident[:12]+'.png'),dpi=115);plt.close(fig)
    print(out,flush=True)
def context():
    out=B/(B/'REVISION-ESCUCHA-ACTUAL.txt').read_text().strip();return out,json.loads((out/'partitura-v9.json').read_text(encoding='utf8'))
def read(name,end=J):
    with gzip.open(OLD/'render'/(name+'.f32.gz'),'rb') as f:return np.frombuffer(f.read(end*8),'<f4').reshape(-1,2).copy()
def window(intervals,n=J,ramp=.025):
    g=np.zeros(n,np.float32)
    for a,b in intervals:
        i=max(0,round(a*SR));j=min(n,round(b*SR));r=min(round(ramp*SR),(j-i)//2)
        if j<=i:continue
        g[i:j]=1
        if r:g[i:i+r]=np.linspace(0,1,r);g[j-r:j]=np.linspace(1,0,r)
    return g
def audio():
    out,p=context();tag=out.name.split('-')[-1];mix=np.zeros((J,2),np.float32);voice=np.zeros_like(mix);band=np.zeros_like(mix)
    norm=10**(.36/20)
    # Recuperación de las 36 observaciones ya realizadas, con revisión sólo antes del centro.
    for part in p['partes']:
        name=part['id'];src='mezclada-r2-guitarra' if name=='guitarra' else 'mezclada-r1-'+name
        x=read(src);x[round(93.333333333*SR):]=0
        if name=='voz':x*=window([w for e in p['eventos'][name] for w in e['salidas']])[:,None]*10**(-9/20)
        elif name in ['duo','boca']:x[:]=0
        elif name in ['guitarra','krar','berimbau','clarinete','piano','mbira']:x*=10**(2/20)
        mix+=x
        if name in ['voz','duo','boca','corocuerda','corojunco']:voice+=x
        else:band+=x
        del x;gc.collect()
    with gzip.open(out/'render'/'relevos.f32.gz','rb') as f:lead=np.frombuffer(f.read(),'<f4').reshape(-1,2).copy()[:J]
    # Un único nivel de captación por frase; se conservan sus acentos internos.
    for phrase in sorted(set(e['frase'] for e in p['relevos_escucha'])):
        es=[e for e in p['relevos_escucha'] if e['frase']==phrase];a=min(e['t'] for e in es);b=max(e['salidas'][0][1] for e in es)
        i,j=round(a*SR),round(b*SR);rms=np.sqrt(np.mean(lead[i:j].astype(float)**2));lead[i:j]*=10**(-23.5/20)/max(rms,1e-12)
    mix+=lead;band+=lead
    center=np.zeros_like(mix)
    for name,windows in p['observaciones_centro_v9'].items():
        if name=='juncos':continue
        x=read('guitarra-captacion' if name=='guitarra' else name)
        x*=window(windows,ramp=.07)[:,None]
        rms=np.sqrt(np.mean(x[window(windows)>.5].astype(float)**2))
        if rms>1e-12:center+=x*(10**(-36/20)/rms)
        del x
    # Captar el estado de los juncos en ventanas desiguales; no generar otro pulso.
    flashes=[[116.01865856,119.75],[120.08,122.7],[123.13,125.16],[127.95,130.1],
        [130.63,133.2],[136.15,138.2],[139.03,142.2],[143.09,145.15],[145.83,148.07],[148.61,153.25]]
    juncos=np.zeros_like(mix);t=np.arange(J)/SR
    for k in range(1,5):
        e=next(e for e in p['eventos']['junco'+str(k)] if e['frase']=='junco-recibe')
        dt=t-e['t'];amp=np.sqrt(e['masa'])*274.4515488228*np.exp(-.027*np.maximum(dt,0))
        phase=e['fase_inicial_rad']+2*np.pi*e['hz']*dt
        x=(np.sin(phase)*amp*window([[max(a,e['t']),b] for a,b in flashes if b>e['t']],ramp=.12)).astype(np.float32)
        angle=(e['pan']+1)*np.pi/4;juncos[:,0]+=x*np.cos(angle);juncos[:,1]+=x*np.sin(angle)
    mask=np.max(abs(juncos),axis=1)>1e-8;rms=np.sqrt(np.mean(juncos[mask].astype(float)**2))
    juncos*=10**(-35/20)/rms;center+=juncos
    center=sosfilt(butter(2,45,'highpass',fs=SR,output='sos'),center,axis=0).astype(np.float32)
    # Las colas casi inaudibles también necesitan captación: acortar el mute solo
    # no resolvía la escucha. Ganancia activa común, nunca normalización por junco.
    block=round(.25*SR);length=J//block
    envelope=np.sqrt(np.mean(center[:length*block].reshape(length,block,2).astype(float)**2,axis=(1,2)))
    pickup=np.clip(10**(-39/20)/np.maximum(envelope,1e-12),1,10**(24/20))
    gain_curve=np.interp(np.arange(J),(.5+np.arange(length))*block,pickup).astype(np.float32)
    center*=gain_curve[:,None]
    for a,b in p['oscuridades']:center[round(a*SR):round(b*SR)]=0
    mix+=center;mix*=norm
    # Limitar el nuevo prefijo, después reponer el PCM aprobado sin pasar por otro procesador.
    wavfile.write(out/'render'/'prefijo.wav',SR,mix)
    raw=out/'render'/'prefijo-limitado.f32'
    subprocess.run(['ffmpeg','-v','error','-n','-i',str(out/'render'/'prefijo.wav'),'-af',
      'aresample=192000,alimiter=limit=0.89125:level=0:attack=5:release=70:latency=1,aresample=48000','-f','f32le',str(raw)],check=True)
    limited=np.fromfile(raw,dtype='<f4').reshape(-1,2)
    for c in p['cortes_buses']:
        a,b=round(c['t']*SR),min(J,round(c['fin']*SR))
        if a<J:
            limited[max(0,a):b]=0
            r=round(.012*SR)
            if a>=r:limited[a-r:a]*=np.linspace(1,0,r)[:,None]
            if b+r<=J:limited[b:b+r]*=np.linspace(0,1,r)[:,None]
    sr,old=wavfile.read(OLD/'luciernagas-cancion-r2-s1-22ac84d49ccd.wav');assert sr==SR
    new=old.copy();new[:J]=(np.clip(limited,-1,1)*2147483648).astype(np.int32)
    # 80 ms de fundido localizado antes del empalme; desde JOIN todo es idéntico.
    r=round(.08*SR);w=np.linspace(0,1,r)[:,None];new[J-r:J]=((1-w)*new[J-r:J]+w*old[J-r:J]).astype(np.int32)
    assert np.array_equal(new[J:],old[J:])
    filename='luciernagas-relevos-s1-'+tag
    wavfile.write(out/'render'/'entero-i32.wav',SR,new)
    subprocess.run(['ffmpeg','-v','error','-n','-i',str(out/'render'/'entero-i32.wav'),'-c:a','pcm_s24le',str(out/(filename+'.wav'))],check=True)
    subprocess.run(['ffmpeg','-v','error','-n','-i',str(out/(filename+'.wav')),'-c:a','aac','-b:a','256k','-movflags','+faststart',str(out/(filename+'.m4a'))],check=True)
    report={'duracion':len(new)/SR,'sr':SR,'voces_retiradas_primera_exposicion':sorted(['raiz','tenis','coro-noche','coro-otras']),
        'programa_audio_sha256':sha(Path(__file__).read_bytes()),
        'voz_restante_ganancia_db':-9,'boca_y_duo_hasta_centro':'salida cerrada',
        'cortes_centro_s':sum(b-a for a,b in p['oscuridades']),'mayor_corte_centro_s':max(b-a for a,b in p['oscuridades']),
        'pcm_identico_desde_s':JOIN,'pcm_identico':bool(np.array_equal(new[J:],old[J:])),
        'ganancia_comun_juncos':float(10**(-35/20)/rms),'no_normalizar_cada_junco':True,
        'captacion_activa_centro_max_db':24,'captacion_activa_centro_rejilla_s':.25,
        'motores_relevos':'objetos.js original: clarinete, piano con papel, chelo',
        'pico':float(np.max(abs(new.astype(float)))/2147483648),
        'voz_resto_db_en_frases':{}}
    for sec in p['secciones'][:3]:
        mask=window([w for e in p['eventos']['voz'] if e['seccion']==sec['id'] for w in e['salidas']])>.1
        report['voz_resto_db_en_frases'][sec['id']]=float(10*np.log10((np.mean(voice[mask].astype(float)**2)+1e-20)/(np.mean(band[mask].astype(float)**2)+1e-20)))
    for ext in ['wav','m4a']:report[ext+'_sha256']=sha((out/(filename+'.'+ext)).read_bytes())
    dump(out/'validacion.json',report)
    # Capturas de señales realmente producidas en esta ejecución.
    fig,axes=plt.subplots(2,1,figsize=(12,6),sharex=True)
    for ax,x,title in zip(axes,[voice,band],['Voz retenida, con nuevo nivel','Instrumentos y frases nuevas']):
        step=2400;z=x[:(80*SR)//step*step].reshape(-1,step,2);ax.plot(np.arange(len(z))*.05,np.sqrt(np.mean(z*z,axis=(1,2))));ax.set_title(title);ax.set_ylim(0,.23)
    axes[-1].set_xlabel('Segundos');fig.tight_layout();fig.savefig(out/'proceso'/('02-relevos-realizados-s1-'+tag+'.png'),dpi=115);plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(12,6))
    a=round(93.333333333*SR);step=960;z=new[a:J].astype(float)/2147483648;z=z[:len(z)//step*step].reshape(-1,step,2)
    axes[0].plot(93.3333+np.arange(len(z))*.02,np.sqrt(np.mean(z*z,axis=(1,2))));axes[0].set_title('Centro revisado · señal real y oscuridades breves');axes[0].set_xlabel('Segundos')
    step=4800;z=new.astype(float)/2147483648;z=z[:len(z)//step*step].reshape(-1,step,2);axes[1].plot(np.arange(len(z))*.1,np.max(abs(z),axis=(1,2)))
    axes[1].axvspan(JOIN,len(new)/SR,alpha=.2,color='green',label='PCM conservado de r2');axes[1].legend();axes[1].set_title('Canción completa · exposición y centro corregidos');fig.tight_layout()
    fig.savefig(out/'proceso'/('03-centro-y-resultado-s1-'+tag+'.png'),dpi=115);plt.close(fig)
    images=[]
    for file in sorted((out/'proceso').glob('*.png')):
        im=Image.open(file).convert('RGB');im.thumbnail((1200,700));canvas=Image.new('RGB',(1200,700),'white');canvas.paste(im,((1200-im.width)//2,(700-im.height)//2));images.append(canvas)
    images[0].save(out/('luciernagas-proceso-relevos-s1-'+tag+'.gif'),save_all=True,append_images=images[1:],duration=2000,loop=0)
    images[-1].resize((1200,630)).save(out/'og.png')
    print(json.dumps(report,ensure_ascii=False,indent=1),flush=True)
if __name__=='__main__':{'preparar':setup,'audio':audio}[sys.argv[1]]()
