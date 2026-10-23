"""Full instrumental mix: 36 realized parts, output gates after effects, three waves."""
from pathlib import Path
import json,sys,math,gzip,hashlib,gc,subprocess,re
import numpy as np
from scipy.signal import butter,sosfilt,oaconvolve
from scipy.io import wavfile
BASE=Path(__file__).resolve().parent;OUT=BASE/(BASE/'REALIZACION-ACTUAL.txt').read_text().strip()
P=json.loads((OUT/'partitura.json').read_text(encoding='utf8'));SR=48000;N=round(P['duracion']*SR)
REV=sys.argv[1] if len(sys.argv)>1 else 'r1'
LEVEL={'guitarra':-5,'pua':-16,'krar':-11,'berimbau':-12,'arpa':-12,'cuerda':-10,'organo':-13,
 'clarinete':-12,'chelo':-12,'contrabajo':-9,'bajo':-8,'androide':-4,'terminal':-2,'piano':-13,
 'mbira':-14,'arpaboca':-14,'campana':-17,'waterphone':-17,'gong':-14,'bombo':-6,'caja':-7,
 'hat':-16,'tom':-11,'aro':-15,'ride':-15,'fotones':-18,'junco1':-12,'junco2':-12,'junco3':-12,'junco4':-12,
 'voz':3,'duo':0,'corocuerda':2,'corojunco':3,'boca':-12,'sala':-14}
ROOM={'guitarra':.09,'krar':.08,'berimbau':.07,'arpa':.23,'cuerda':.22,'organo':.10,'clarinete':.12,
 'chelo':.20,'contrabajo':.08,'androide':.06,'terminal':.14,'piano':.09,'mbira':.12,'arpaboca':.12,
 'campana':.24,'waterphone':.25,'gong':.15,'fotones':.08,'junco1':.16,'junco2':.16,'junco3':.16,'junco4':.16,
 'voz':.09,'duo':.12,'corocuerda':.10,'corojunco':.10,'boca':.12}
GROUPS={'cancion':['guitarra','pua','krar','berimbau','clarinete','piano','mbira','arpaboca'],
 'graves':['contrabajo','bajo','androide'],'percusion':['bombo','caja','hat','tom','aro','ride','fotones'],
 'carbono':['arpa','cuerda','organo','chelo','terminal','sala'],
 'objetos':['campana','waterphone','gong'],
 'juncos':['junco1','junco2','junco3','junco4'],
 'voces':['voz','duo','corocuerda','corojunco','boca']}
def source(name):return 'guitarra-captacion' if name=='guitarra' and REV=='r2' else ('prosodia-'+name if name in ['voz','duo'] else name)
def processed(name):return 'mezclada-r1-'+name if REV=='r2' and name!='guitarra' else 'mezclada-'+REV+'-'+name
def read(name):
    with gzip.open(OUT/'render'/(name+'.f32.gz'),'rb') as f:data=f.read()
    x=np.frombuffer(data,dtype='<f4').reshape(-1,2).copy();assert len(x)==N,(name,len(x));return x
def write(name,x):
    h=hashlib.sha256()
    with gzip.open(OUT/'render'/(name+'.f32.gz'),'xb',compresslevel=3) as f:
        for i in range(0,len(x),SR):
            block=x[i:i+SR].astype('<f4',copy=False).tobytes();h.update(block);f.write(block)
    return h.hexdigest()
def gate(windows):
    merged=[]
    for a,b in sorted(windows):
        if merged and a<=merged[-1][1]+1/SR:merged[-1][1]=max(merged[-1][1],b)
        else:merged.append([a,b])
    g=np.zeros(N,np.float32);r=round(.012*SR)
    for a,b in merged:
        i=max(0,round(a*SR));j=min(N,round(b*SR));size=j-i
        if size<=0:continue
        g[i:j]=1;rr=min(r,size//2)
        if rr:g[i:i+rr]=np.linspace(0,1,rr,endpoint=False);g[j-rr:j]=np.linspace(1,0,rr,endpoint=False)
    return g
def partgate(name):return gate([w for e in P['eventos'][name] for w in e['salidas']])
def globalgate():
    g=np.ones(N,np.float32);r=round(.012*SR)
    for c in P['cortes_buses']:
        i=round(c['t']*SR);j=round(c['fin']*SR);g[max(0,i):min(N,j)]=0
        if i-r>=0:g[i-r:i]=np.minimum(g[i-r:i],np.linspace(1,0,r,endpoint=False))
        if j+r<=N:g[j:j+r]=np.minimum(g[j:j+r],np.linspace(0,1,r,endpoint=False))
    return g
def active(x):
    rms=[]
    for i in range(0,len(x),2400):rms.append(float(np.sqrt(np.mean(x[i:i+2400].astype(float)**2))))
    rms=np.asarray(rms);on=rms>rms.max()*.03
    return float(np.sqrt(np.mean(rms[on]**2))) if on.any() else 0.
def energy(x):return float(np.mean(x.astype(float)**2))
def automation(name,x):
    # Relative levels follow roles already composed in each wave.
    waves={'guitarra':[1.,.8,1.8],'cuerda':[1.35,.85,1.65],'arpa':[1.35,.85,1.15],
      'berimbau':[.8,1.6,1.],'mbira':[.8,1.6,1.],'piano':[.8,1.5,1.1],'organo':[.8,1.15,1.7],
      'bombo':[1,1.05,1.3],'caja':[1,1.1,1.3],'sala':[1,1,1.7]}
    centers={'guitarra':.40,'cuerda':.20,'junco1':.35,'junco2':.35,'junco3':.35,'junco4':.35,
             'waterphone':.28,'campana':.35}
    if name in centers:x[round(P['centro'][0]*SR):round(P['centro'][1]*SR)]*=centers[name]
    vals=waves.get(name,[1,1,1])
    for (a,b),v in zip([(206.666666667,220),(220,233.333333333),(233.333333333,246.666666667)],vals):
        i,j=round(a*SR),round(b*SR);x[i:j]*=v
    if name in ['guitarra','bajo','organo','arpa','cuerda','sala']:
        # A short 15% release only in the wall; the initial folk stays direct.
        for e in P['eventos']['bombo']:
            if e['t']<206.666:continue
            i=round(e['t']*SR);j=min(N,i+round(.18*SR));t=np.arange(j-i)/SR;x[i:j]*=(1-.15*np.exp(-t/.055))[:,None]
    return x
def main():
    gg=globalgate();mix=np.zeros((N,2),np.float32);stats={};stemhash={}
    prior=json.loads((OUT/'mezcla-r1.json').read_text(encoding='utf8')) if REV=='r2' and (OUT/'mezcla-r1.json').exists() else None
    shared=np.zeros_like(mix)
    for k in range(1,5):
        y=read('junco'+str(k));y*=partgate('junco'+str(k))[:,None];shared+=y
    junco_level=active(shared);del shared,y;gc.collect()
    rng=np.random.default_rng(P['semilla']+811)
    length=round(1.8*SR);t=np.arange(length)/SR
    ir=rng.standard_normal((length,2)).astype(np.float32)*np.exp(-t*3.7).astype(np.float32)[:,None]
    ir[:round(.023*SR)]=0;ir/=np.sqrt(np.sum(ir**2,axis=0));ir*=.65
    for part in P['partes']:
        name=part['id']
        if REV=='r2' and name!='guitarra':
            x=read(processed(name));mix+=x
            stats[name]=prior['partes'][name] if prior else {'motor':part['motor'],'mezcla_reutilizada':'r1',
              'normalizacion_objetivo_db':-20+LEVEL[name],'nivel_relativo_db':LEVEL[name],'pico_mezclado':float(np.max(abs(x))),
              'por_seccion_rms_db':{s['id']:10*math.log10(energy(x[round(s['t']*SR):round(s['fin']*SR)])+1e-20) for s in P['secciones']}}
            h=hashlib.sha256()
            for i in range(0,N,SR):h.update(x[i:i+SR].tobytes())
            stemhash[name]=h.hexdigest();del x;gc.collect();print(name,'mezcla conservada r1',flush=True);continue
        x=read(source(name));g=partgate(name);x*=g[:,None]
        a=junco_level if name.startswith('junco') else active(x)
        assert a>1e-8,(name,'muda');gain=10**((-20+LEVEL[name])/20)/a;x*=gain
        cutoff=30 if name in ['bajo','contrabajo','androide','bombo'] else 65 if name in ['voz','duo','corocuerda','corojunco'] else 35
        x=sosfilt(butter(2,cutoff,'highpass',fs=SR,output='sos').astype(np.float32),x,axis=0)
        if name=='guitarra':x=(np.tanh(x*2.2)/2.2).astype(np.float32)
        x=automation(name,x)
        if name in ROOM:
            for channel in range(2):x[:,channel]+=ROOM[name]*oaconvolve(x[:,channel],ir[:,channel],mode='full')[:N]
        x*=g[:,None];x*=gg[:,None];assert np.isfinite(x).all()
        mix+=x;stemhash[name]=write(processed(name),x)
        stats[name]={'motor':part['motor'],'activo_origen_rms':a,'ganancia':gain,'nivel_relativo_db':LEVEL[name],
          'pico_mezclado':float(np.max(abs(x))),'por_seccion_rms_db':{s['id']:10*math.log10(energy(x[round(s['t']*SR):round(s['fin']*SR)])+1e-20) for s in P['secciones']}}
        print(name,round(stats[name]['pico_mezclado'],3),flush=True);del x,g;gc.collect()
    mix*=gg[:,None]
    # Read processed stems one group at a time for coherent group-versus-rest measures.
    group_report={}
    for group,names in GROUPS.items():
        summed=np.zeros_like(mix)
        for name in names:summed+=read(processed(name))
        group_report[group]={}
        for s in P['secciones']:
            i,j=round(s['t']*SR),round(s['fin']*SR);e=energy(summed[i:j]);rest=energy(mix[i:j]-summed[i:j]);group_report[group][s['id']]=10*math.log10((e+1e-20)/(rest+1e-20))
        del summed;gc.collect()
    premix=OUT/'render'/('mezcla-'+REV+'.wav');wavfile.write(premix,SR,mix)
    write('mezcla-'+REV,mix);del mix;gc.collect()
    measure=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(premix),'-af','loudnorm=I=-12.5:TP=-1:LRA=20:print_format=json','-f','null','-'],capture_output=True,text=True,errors='replace',check=True).stderr
    measured=json.JSONDecoder().raw_decode(measure[measure.rfind('{'):])[0];gain=min(-12.5-float(measured['input_i']),-1-float(measured['input_tp'])+4)
    limited=OUT/'render'/('limitada-'+REV+'.f32')
    subprocess.run(['ffmpeg','-v','error','-n','-i',str(premix),'-af',f'volume={gain}dB,aresample=192000,alimiter=limit=0.89125:level=0:attack=5:release=70:latency=1,aresample=48000','-f','f32le',str(limited)],check=True)
    final=np.memmap(limited,dtype='<f4',mode='r+').reshape(-1,2)
    assert len(final)==N,(len(final),N)
    final*=gg[:,None];final.flush();del final;gc.collect()
    prefix='luciernagas-cancion-'+REV+'-s1-'+OUT.name.split('-')[-1];wav=OUT/(prefix+'.wav');aac=OUT/(prefix+'.m4a')
    subprocess.run(['ffmpeg','-v','error','-n','-f','f32le','-ar',str(SR),'-ac','2','-i',str(limited),'-c:a','pcm_s24le',str(wav)],check=True)
    subprocess.run(['ffmpeg','-v','error','-n','-i',str(wav),'-c:a','aac','-b:a','256k','-movflags','+faststart',str(aac)],check=True)
    report={'version':REV,'sr':SR,'duracion':P['duracion'],'partes':stats,'grupos_contra_resto_db':group_report,'stem_hashes_descomprimidos':stemhash,
      'mezcla_previa_loudnorm':measured,'ganancia_estatica_db':gain,'limite_amplitud':.89125,'sobremuestreo_limitador':4,
      'cortes_despues_del_limitador':True,'salida_wav':wav.name,'salida_aac':aac.name,'ganancia_inicial_paquete_junco':274.4515488228,
      'fuente_voz':'Sabina PSOLA con difonos completos escalados al tiempo de cada sílaba, f0 y formantes conservados',
      'portadoras_vocoder':{'corocuerda':'motor cuerda','corojunco':'suma de cuatro juncos, excitación no lineal tanh para enriquecer las bandas'}}
    with open(OUT/('mezcla-'+REV+'.json'),'x',encoding='utf8') as f:json.dump(report,f,ensure_ascii=False,indent=1)
    print('ENTREGA',wav,aac,flush=True)
if __name__=='__main__':main()
