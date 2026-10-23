"""Realización completa de v10.1. Salidas exclusivas; motores nativos y estados canónicos."""
from pathlib import Path
import json,sys,os,secrets,hashlib,shutil,gzip,math,gc,subprocess
import numpy as np
from scipy.signal import butter,sosfilt,oaconvolve
from scipy.io import wavfile
from PIL import Image,ImageDraw,ImageFont

B=Path(__file__).resolve().parent
SR=48000
VERSION='luciernagas-audio-10.1.1'
def sha(data):return hashlib.sha256(data).hexdigest()
def dump(path,data):
    with path.open('x',encoding='utf8',newline='\n') as f:json.dump(data,f,ensure_ascii=False,indent=1)
def context():
    out=B/(B/'AUDIO-V10-EN-CURSO.txt').read_text().strip()
    return out,json.loads((out/'partitura.json').read_text(encoding='utf8'))
def save(out,name,y):
    assert np.isfinite(y).all(),name
    with gzip.open(out/'render'/(name+'.f32.gz'),'xb',compresslevel=3) as f:
        for i in range(0,len(y),SR):f.write(y[i:i+SR].astype('<f4',copy=False).tobytes())
    print(name,'pico',float(np.max(abs(y))),flush=True)
def read(out,name):
    if name.startswith('junco') and (out/'render'/(name+'-fusion.f32.gz')).exists():name+='-fusion'
    if name=='aro' and (out/'render/aro-frito-v10.f32.gz').exists():name='aro-frito-v10'
    if name=='campana' and (out/'render/campana-v10.f32.gz').exists():name='campana-v10'
    with gzip.open(out/'render'/(name+'.f32.gz'),'rb') as f:return np.frombuffer(f.read(),'<f4').reshape(-1,2).copy()
def stage(out,n,title,lines):
    im=Image.new('RGB',(1200,700),'#10201e');d=ImageDraw.Draw(im)
    font=lambda s:ImageFont.truetype('C:/Windows/Fonts/arial.ttf',s)
    d.text((50,45),'LUCIÉRNAGAS / REALIZACIÓN 10.1',font=font(25),fill='#abc8b6')
    d.text((50,110),title,font=font(34),fill='#ead3a8')
    for j,line in enumerate(lines):d.text((50,205+j*57),line,font=font(23),fill='#d8e0d7')
    d.text((50,646),'Captura de una etapa realizada · semilla terreno 1 · sin audio anterior pegado',font=font(18),fill='#abc8b6')
    target=out/'proceso'/f'{n:02}-etapa-audio-s1-{out.name.split("-")[-1]}.png'
    assert not target.exists();im.save(target)
def init():
    score=B/(B/'PARTITURA-ACTUAL.txt').read_text().strip();data=(score/'partitura-v10.1.json').read_bytes()
    image=(score/'og.png').read_bytes();nonce=secrets.token_hex(16);code=Path(__file__).read_bytes()
    ident=sha(data+image+code+VERSION.encode()+nonce.encode())
    out=B/f'luciernagas-audio-v10-s1-{ident[:12]}';out.mkdir(exist_ok=False)
    for name in ['render','proceso','fuentes']:(out/name).mkdir()
    with (out/'partitura.json').open('xb') as f:f.write(data)
    for file in ['audio_v10.py','nativos_v10.py','interpretar.cjs','motores_audio.py','estados.cjs','instrumentos.py','modelos_memoria.py','resolver_v10.py']:
        shutil.copyfile(B/file,out/'fuentes'/file)
    dump(out/'inicio.json',{'version':VERSION,'sha256_ejecucion':ident,'nonce':nonce,'partitura':str(score),
      'partitura_sha256':sha(data),'imagen_sha256':sha(image),'programa_sha256':sha(code),'sr':SR,
      'semilla_terreno':1,'semilla_composicion':2026102201,'autorizacion':'Canek: ok, me parece bien, lo oimos; 22 de octubre de 2026'})
    (B/'AUDIO-V10-EN-CURSO.txt').write_text(out.name,encoding='utf8')
    stage(out,1,'Partitura recibida y fuentes fijadas',['36 partes / 1,714 eventos / 4:18.667','Guitarra → cuerda → cuatro juncos → 24 transportes','Sabina PSOLA y portadoras propias','El audio completo se interpreta desde la partitura 10.1'])
    print(out,flush=True)
def gate(windows,n):
    merged=[]
    for a,b in sorted(windows):
        if merged and a<=merged[-1][1]+1/SR:merged[-1][1]=max(merged[-1][1],b)
        else:merged.append([a,b])
    g=np.zeros(n,np.float32);r=round(.012*SR)
    for a,b in merged:
        i=max(0,round(a*SR));j=min(n,round(b*SR));rr=min(r,(j-i)//2)
        if j<=i:continue
        g[i:j]=1
        if rr:g[i:i+rr]=np.linspace(0,1,rr,endpoint=False);g[j-rr:j]=np.linspace(1,0,rr,endpoint=False)
    return g
def globalgate(p,n):
    g=np.ones(n,np.float32);r=round(.012*SR)
    for c in p['cortes_buses']:
        i,j=round(c['t']*SR),round(c['fin']*SR);g[i:j]=0
        if i>=r:g[i-r:i]=np.minimum(g[i-r:i],np.linspace(1,0,r,endpoint=False))
        if j+r<=n:g[j:j+r]=np.minimum(g[j:j+r],np.linspace(0,1,r,endpoint=False))
    return g
def active(x):
    blocks=[float(np.mean(x[i:i+2400].astype(float)**2)) for i in range(0,len(x),2400)]
    v=np.array(blocks);selected=v>max(float(v.max())*.0009,1e-24)
    return float(np.sqrt(v[selected].mean())) if selected.any() else 0
def db(x):return 20*math.log10(max(x,1e-16))
ROOM={'guitarra':.09,'krar':.08,'berimbau':.07,'arpa':.23,'cuerda':.22,'organo':.10,'clarinete':.12,
 'chelo':.20,'contrabajo':.08,'androide':.06,'terminal':.14,'piano':.09,'mbira':.12,'arpaboca':.12,
 'campana':.24,'waterphone':.25,'gong':.15,'fotones':.08,'junco1':.16,'junco2':.16,'junco3':.16,'junco4':.16,
 'voz':.09,'duo':.12,'corocuerda':.10,'corojunco':.10,'boca':.12}
def mix():
    out,p=context();n=round(p['duracion']*SR);ci,cj=[round(t*SR) for t in p['centro']];gg=globalgate(p,n)
    total=np.zeros((n,2),np.float32);stats={};center_fields={};junco=np.zeros_like(total)
    for k in range(1,5):
        name=f'junco{k}';y=read(out,name);y*=gate([w for e in p['eventos'][name] for w in e['salidas']],n)[:,None];junco+=y
    ordinary=junco.copy();ordinary[ci:cj]=0;junco_active=active(ordinary);center_fields['juncos_conjunto']=active(junco[ci:cj]);del junco,ordinary,y;gc.collect()
    objects=np.zeros((cj-ci,2),np.float32)
    for name in ['waterphone','campana']:
        y=read(out,name);g=gate([w for e in p['eventos'][name] for w in e['salidas']],n);objects+=y[ci:cj]*g[ci:cj,None]
    center_fields['objetos']=active(objects);del objects,y,g;gc.collect()
    rng=np.random.default_rng(p['semilla']+811);t=np.arange(round(1.8*SR))/SR
    ir=(rng.standard_normal((len(t),2))*np.exp(-t*3.7)[:,None]).astype(np.float32);ir[:round(.023*SR)]=0
    ir/=np.sqrt(np.sum(ir**2,axis=0));ir*=.65
    for part in p['partes']:
        name=part['id'];src='prosodia-'+name if name in ['voz','duo'] else name
        x=read(out,src);g=gate([w for e in p['eventos'][name] for w in e['salidas']],n);x*=g[:,None]
        outside=x.copy();outside[ci:cj]=0;a=junco_active if name.startswith('junco') else active(outside)
        del outside
        # Calibration occurs once for the whole family, never per flash or moving RMS.
        level=p['niveles_relativos_v10_db'][name];gain=10**((-20+level)/20)/a if a>1e-12 else 0
        field='juncos_conjunto' if name.startswith('junco') else name if name in ['guitarra','cuerda'] else 'objetos'
        ca=center_fields.get(field,active(x[ci:cj]));target=p['centro_v10']['captacion_db'][field]
        cg=10**(target/20)/max(ca,1e-12) if ca>1e-12 else 0
        x[:ci]*=gain;x[cj:]*=gain;x[ci:cj]*=cg
        cutoff=30 if name in ['bajo','contrabajo','androide','bombo'] else 65 if name in ['voz','duo','corocuerda','corojunco'] else 35
        x=sosfilt(butter(2,cutoff,'highpass',fs=SR,output='sos').astype(np.float32),x,axis=0)
        if name=='guitarra':x=(np.tanh(x*2.2)/2.2).astype(np.float32)
        waves={'guitarra':[1,.8,1.8],'cuerda':[1.35,.85,1.65],'arpa':[1.35,.85,1.15],
          'berimbau':[.8,1.6,1],'mbira':[.8,1.6,1],'piano':[.8,1.5,1.1],'organo':[.8,1.15,1.7],
          'bombo':[1,1.05,1.3],'caja':[1,1.1,1.3],'sala':[1,1,1.7]}
        for (a0,b0),v in zip([(206.666666667,220),(220,233.333333333),(233.333333333,246.666666667)],waves.get(name,[1,1,1])):x[round(a0*SR):round(b0*SR)]*=v
        if name in ROOM:
            for ch in range(2):x[:,ch]+=ROOM[name]*oaconvolve(x[:,ch],ir[:,ch],mode='full')[:n]
        x*=g[:,None];x*=gg[:,None]
        assert np.isfinite(x).all() and float(np.max(abs(x)))>1e-12,name
        total+=x;save(out,'mezclada-v10-'+name,x)
        stats[name]={'ganancia_ordinaria':gain,'ganancia_centro_fija':cg,'nivel_relativo_db':level,
          'rms_activo_origen':a,'rms_centro_origen':ca,'pico':float(np.max(abs(x))),
          'rms_secciones_dbfs':{s['id']:db(float(np.sqrt(np.mean(x[round(s['t']*SR):round(s['fin']*SR)].astype(float)**2)))) for s in p['secciones']}}
        del x,g;gc.collect()
    total*=gg[:,None];wavfile.write(out/'render/premaster-v10.wav',SR,total)
    dump(out/'mezcla-v10.json',{'partes':stats,'rutas':{p0['id']:p0['motor'] for p0 in p['partes']},'fuente':'partitura-v10.1 completa; sin PCM histórico','centro':'ganancia fija por campo; juncos una sola calibración compartida'})
    stage(out,4,'Mezcla completa de las 36 partes',['Todos los instrumentos tienen señal finita y salida escrita','Ganancias centrales fijas; fases y estados no se reinician','Voz principal: −6 dB relativos / guitarra: 0 dB','Tres olas: resonancia, contagio, casi continuidad'])
    print('Premáster completo',flush=True)
def loudness(path):
    r=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(path),'-af','loudnorm=I=-14:TP=-1:LRA=30:print_format=json','-f','null','-'],capture_output=True,text=True,errors='replace',check=True).stderr
    return json.JSONDecoder().raw_decode(r[r.rfind('{'):])[0]
def master():
    out,p=context();tag=out.name.split('-')[-1];pre=out/'render/premaster-v10.wav';m=loudness(pre)
    gain=min(-14-float(m['input_i']),-1-float(m['input_tp'])+2)
    raw=out/'render/master-v10.f32'
    subprocess.run(['ffmpeg','-v','error','-n','-i',str(pre),'-af',f'volume={gain}dB,aresample=192000,alimiter=limit=0.89125:level=0:attack=5:release=70:latency=1,aresample=48000','-f','f32le',str(raw)],check=True)
    x=np.memmap(raw,dtype='<f4',mode='r+').reshape(-1,2);n=round(p['duracion']*SR);assert len(x)==n
    x*=globalgate(p,n)[:,None];x.flush();del x;gc.collect()
    prefix='luciernagas-v10.1-s1-'+tag;wav=out/(prefix+'.wav');aac=out/(prefix+'.m4a')
    subprocess.run(['ffmpeg','-v','error','-n','-f','f32le','-ar',str(SR),'-ac','2','-i',str(raw),'-c:a','pcm_s24le',str(wav)],check=True)
    subprocess.run(['ffmpeg','-v','error','-n','-i',str(wav),'-c:a','aac','-b:a','256k','-movflags','+faststart',str(aac)],check=True)
    post=loudness(wav);dump(out/'master-v10.json',{'previo':m,'final':post,'ganancia_estatica_db':gain,'limitador_sobremuestreo':4,'wav':wav.name,'aac':aac.name,'sr':SR,'duracion':p['duracion']})
    print('ENTREGA',wav,aac,post,flush=True)
if __name__=='__main__':{'iniciar':init,'mezcla':mix,'master':master}[sys.argv[1]]()
