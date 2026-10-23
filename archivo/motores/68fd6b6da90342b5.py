"""Mi boca termina en otra parte. iniciar → sondas (node) → componer → render/voz → relevar → terminar → verificar.
Archivos exclusivos. La guía vocal se conserva completa; la cantante audible se retira según el score.
"""
import hashlib,json,math,os,re,subprocess,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.io import wavfile
from scipy.signal import butter,sosfilt,find_peaks,stft,correlate
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parent
SR=48000;DUR=210;N=DUR*SR;SEED=161026;MOTIF=[57,58,64,63,59]
NAMES=['voz','piano','agua','clarinete','metal','chelo']
COLORS=[(242,223,192),(237,170,96),(95,205,217),(172,197,119),(231,123,151),(169,157,221)]
BG=(24,25,34);FG=(238,232,215);FONT=lambda n:ImageFont.truetype('C:/Windows/Fonts/consola.ttf',n)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):
    with Path(p).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
def txt(p,s):
    with Path(p).open('x',encoding='utf8') as f:f.write(s)
def png(p,im):
    with Path(p).open('xb') as f:im.save(f,'PNG')
def wav(p,x):
    with Path(p).open('xb') as f:wavfile.write(f,SR,np.asarray(x,np.float32))
def read(out,name):
    sr,x=wavfile.read(out/'render'/f'{name}.wav');assert sr==SR and np.isfinite(x).all()
    return x.mean(axis=1).astype(np.float32) if x.ndim==2 else x.astype(np.float32)
def run(args):return subprocess.run(args,check=True,capture_output=True,text=True,encoding='utf8',errors='replace')
def db(x):return float(10*np.log10(np.mean(np.asarray(x,dtype=float)**2)+1e-14))
def band(x,lo=None,hi=None):
    return sosfilt(butter(2,[lo,hi] if lo and hi else lo or hi,'band' if lo and hi else 'high' if lo else 'low',fs=SR,output='sos'),x).astype(np.float32)
def card(title,sub):
    im=Image.new('RGB',(1200,630),BG);d=ImageDraw.Draw(im)
    d.text((32,20),'MI BOCA TERMINA EN OTRA PARTE',font=FONT(29),fill=FG)
    d.text((32,65),title,font=FONT(18),fill=COLORS[2]);d.text((32,600),sub,font=FONT(13),fill=FG);return im,d
def initialize():
    im,d=card('01 / una frase puede terminar fuera de su garganta','Esquema de composición antes de medir y sintetizar · semilla 161026 · Canek Zapata')
    for i,(m,s) in enumerate(zip(MOTIF,['La3','Sib3','Mi4','Mib4','Si3'])):
        x=85+i*220;y=325-(m-57)*12;d.ellipse((x-12,y-12,x+12,y+12),fill=COLORS[i]);d.text((x-20,410),s,font=FONT(20),fill=FG)
        if i<4:d.line((x+20,y,x+190,325-(MOTIF[i+1]-57)*12),fill=(90,88,102),width=2)
    d.text((56,155),'boca → agua → aire → metal → cuerda',font=FONT(23),fill=COLORS[0])
    d.text((56,490),'Boca / Relevo / Fricción / Recuerdo de canción / Otra parte',font=FONT(17),fill=FG)
    nonce=os.urandom(24).hex();digest=hashlib.sha256(im.tobytes()+Path(__file__).read_bytes()+(ROOT/'render.cjs').read_bytes()+nonce.encode()).hexdigest();tag=digest[:12]
    out=ROOT/f'mi-boca-en-otra-parte-s{SEED}-{tag}';out.mkdir(exist_ok=False)
    for folder in ['render','proceso','fuentes']:(out/folder).mkdir()
    dump(out/'partitura.json',{'semilla':SEED,'duracion':DUR,'estado':'antes de las sondas'})
    png(out/'proceso'/f'01-esquema-s{SEED}-{tag}.png',im)
    sources=[Path(__file__),ROOT/'render.cjs',REPO/'lo-que-no-sono/voz.cjs']+list((REPO/'objetos/motor').glob('*.js'))
    hashes={}
    for p in sources:
        with (out/'fuentes'/p.name).open('xb') as f:f.write(p.read_bytes())
        hashes[str(p.relative_to(REPO))]=sha(p)
    dump(out/'receta-inicial.json',{'id':digest,'nonce':nonce,'semilla':SEED,'fecha_local':'2026-10-16','fuentes_sha256':hashes,'imagen_inicial_sha256':sha(next((out/'proceso').glob('*.png')))})
    print(out,flush=True)

def analyze_probe(out,name):
    y=read(out,'sonda-'+name);seg=y[SR:3*SR].astype(float);n=2**19
    z=np.abs(np.fft.rfft(seg*np.hanning(len(seg)),n));freq=np.fft.rfftfreq(n,1/SR)
    ix,_=find_peaks(z,distance=math.ceil(12/(SR/n)),prominence=z.max()*.008)
    ix=[i for i in ix if 95<freq[i]<1500];ix=sorted(ix,key=lambda i:-z[i])[:5]
    result=[]
    for i in ix:
        f=float(freq[i]);fold=f
        while fold>440:fold/=2
        while fold<110:fold*=2
        result.append({'Hz_medido':f,'Hz_reducido':fold,'midi':float(69+12*np.log2(fold/440)),'amplitud_relativa':float(z[i]/z.max())})
    assert len(result)>=2,(name,result)
    return result

def compose(out):
    fields={n:analyze_probe(out,n) for n in ['gong','waterphone']};dump(out/'resonancias.json',fields)
    I={name:[] for name in ['piano','clarinete','chelo','metal','agua','bajo','campo','gong','waterphone']}
    phrases=[];relays=[]
    hook='mi bo ca ter mi na en o tra par te'
    rows=[(3,'de jo u na vo cal en cen di da'),(12,'has ta que en cuen tre dón de vi vir'),(22,hook),(30,hook),
       (40,'la ma de ra re tie ne el co mien zo'),(49,'el me tal con ti nú a la luz'),(58,hook),(70,'el a gua pro nun cia des pa cio'),(78,hook),
       (88,'quién sos tie ne la úl ti ma le tra'),(98,'quién res pi ra des pués de la voz'),(106,hook),
       (118,'me que do del la do de a fue ra'),(128,hook),(135,hook),(142,'hay al guien can tan do sin mí'),(147,hook),
       (154,'a den tro ter mi na la can ción'),(163,'de jo u na vo cal en cen di da'),(172,hook),(188,hook)]
    spacing=np.array([.75,.5,.75,.5,.75,.5,.5,.75,.5,.75,1.75])*.75
    for pidx,(t,line) in enumerate(rows):
        syll=line.split();ev=[];cur=t
        for k,s in enumerate(syll):
            note=MOTIF[k%5] if line==hook else MOTIF[(k+pidx)%5]
            dur=float(spacing[k%len(spacing)]) if line==hook else float([.42,.55,.38,.65,.48][k%5])
            if k==len(syll)-1:dur=1.0 if line!=hook else float(spacing[-1])
            e={'t':cur,'dur':dur,'texto':s,'nota':note};ev.append(e)
            if t<35:route=['voz']
            elif t<85:route=['voz','agua','clarinete'] if k%2==0 else ['piano','metal','chelo']
            elif t<135:route=['piano','chelo','metal'] if k%2==0 else ['agua','clarinete','chelo']
            elif t<160:route=['voz']
            elif t<170:route=['voz','agua','metal']
            else:route=['agua','clarinete','metal'] if k%2==0 else ['piano','metal','chelo']
            rid=len(relays);vowel=re.findall('[aeiouáéíóúü]',s.lower());vowel=(vowel[-1] if vowel else 'a').translate(str.maketrans('áéíóúü','aeiouu'))
            relays.append({**e,'id':rid,'frase':pidx,'ruta':route,'vocal':vowel})
            for source in set(route)-{'voz'}:
                event={'t':cur,'dur':dur+.04,'m':note,'v':.68,'relay':rid}
                if source=='piano':event.update(tipo='apagada' if t<85 else 'martillo',prep='papel' if t<85 else 'tornillo-suelto')
                if source=='clarinete':event['tipo']='normal'
                if source=='chelo':event['tipo']='ponticello' if 85<t<135 else 'arco'
                if source=='metal':event.update(tipo='normal',sordina='harmon' if k%2==0 else 'plunger')
                if source=='agua':event.update(texto=vowel*3)
                I[source].append(event)
            if t<35 or 135<=t<160:
                if k%3==0:I['piano'].append({'t':cur+.015,'dur':.35,'m':note-12,'v':.5,'tipo':'apagada','prep':'papel'})
                if k==0 and t<35:I['clarinete'].append({'t':cur+.4,'dur':1.2,'m':note-12,'v':.5,'tipo':'subtono'})
            cur+=dur
        phrases.append({'eventos':ev,'nivel':.7,'pan':0,'hook':line==hook,'texto':line})
    # Los campos derivan de picos medidos; el motivo principal conserva sus cinco notas.
    pool=fields['gong'][:3]+fields['waterphone'][:3]
    for k,t in enumerate(np.arange(.5,194,9.0)):
        for j in range(2 if t<85 else 3):
            m=pool[(k+j)%len(pool)]['midi']+(-12 if j==0 else 0)+(.045 if k%2 else 0)
            I['campo'].append({'t':float(t+j*.3),'dur':6.2 if t<135 else 4.5,'m':float(m),'v':.42,'tipo':'tasto' if t<85 or t>135 else 'ponticello'})
    # Ocho compases a 80 BPM: 24 segundos de recuerdo house, del 135 al 159.
    for b in range(8):
        for k,pos in enumerate([0,.75,1.5,2.25]):
            I['bajo'].append({'t':135+b*3+pos,'dur':.32,'m':[33,40,34,39][(b+k)%4]+(12 if k==3 else 0),'v':.8,'tipo':'pizz','casa':.3+.7*b/7})
    for t in [0,35,85,135,160,194]:I['gong'].append({'t':t,'dur':.2,'m':57,'v':.4,'tipo':'cruce','abre':4 if t<135 else 2})
    for k,t in enumerate([.5,67,90,124,166,196]):I['waterphone'].append({'t':t,'dur':3.2,'v':.4,'tipo':'arco','vara':3 if k%2==0 else 8,'agua':.3 if k==0 else 1.5,'ola':.25})
    for name in I:I[name].sort(key=lambda e:e['t'])
    P={'semilla':SEED,'duracion':DUR,'motivo':MOTIF,'frases':phrases,'relevos':relays,'instrumentos':I,'resonancias':fields,
       'secciones':[['Boca',0,35],['Relevo',35,85],['Fricción',85,135],['Recuerdo',135,160],['Otra parte',160,210]],
       'coda':{'inicio':198,'fin':210,'nota':57,'vocales':['a','i'],'diferencia_Hz':[.65,.08]}}
    # El esquema previo queda intacto; el renderer final recibe una partitura en una ruta nueva.
    dump(out/'partitura-compuesta.json',P)
    im,d=card('02 / resonancias medidas y una melodía repartida','FFT de sondas reales, 1–3 s · el score se compuso después de medir los cuerpos')
    for i,name in enumerate(['gong','waterphone']):
        d.text((40,125+i*115),name,font=FONT(20),fill=COLORS[1+i])
        for j,r in enumerate(fields[name]):d.text((210+j*182,125+i*115),f"{r['Hz_medido']:.1f} Hz",font=FONT(17),fill=FG)
    for i,name in enumerate(NAMES):
        yy=355+i*30;d.text((40,yy),name,font=FONT(13),fill=COLORS[i])
        for e in relays:
            if name in e['ruta']:
                x=160+e['t']/DUR*1000;d.line((x,yy+10,x+max(2,e['dur']/DUR*1000),yy+10),fill=COLORS[i],width=3)
    tag=out.name.split('-')[-1];png(out/'proceso'/f'02-resonancias-y-score-s{SEED}-{tag}.png',im)
    print('SCORE',len(relays),'sílabas;', {k:len(v) for k,v in I.items()},fields,flush=True)

def score(out):return json.loads((out/'partitura-compuesta.json').read_text(encoding='utf8'))
def smooth_envelope(x,cut=35):return np.sqrt(np.maximum(0,sosfilt(butter(1,cut,'low',fs=SR,output='sos'),x*x))).astype(np.float32)
def active_rms(x):
    e=np.mean(x[:len(x)//2400*2400].reshape(-1,2400).astype(float)**2,axis=1);e=e[e>max(e.max()*1e-5,1e-12)]
    return float(np.sqrt(np.mean(e)))
def mask_note(dur,route,index,length):
    u=np.arange(length)/SR/dur
    if len(route)==1:return np.sin(np.pi*np.clip(u,0,1))**.22*(u<1)
    centers=np.linspace(.12,.88,len(route));sigma=.24 if len(route)==3 else .35
    weights=np.stack([np.exp(-.5*((u-c)/sigma)**2) for c in centers]);weights/=np.maximum(np.sqrt(np.sum(weights**2,axis=0)),1e-9)
    edge=np.minimum(1,np.maximum(0,u)*dur/.018)*np.minimum(1,np.maximum(0,1-u)*dur/.045)
    return weights[index]*edge

def relay(out):
    P=score(out);guide=read(out,'voz');assert len(guide)==N
    raw={n:read(out,n) for n in NAMES if n!='voz'}
    # Ajuste por cuerpo completo para que los relevos no respondan a ganancias arbitrarias del modelo.
    scales={n:.10/max(active_rms(x),1e-8) for n,x in raw.items()}
    for n in raw:raw[n]*=scales[n]
    edges=np.geomspace(130,5000,13);colored={n:np.zeros(N,np.float32) for n in raw}
    reference_rms=np.maximum(smooth_envelope(guide),.001)
    # Ocho voces físicas no se fuerzan a tener armónicos ausentes: ganancias acotadas, 40% de cuerpo original.
    for lo,hi in zip(edges[:-1],edges[1:]):
        g=band(guide,float(lo),float(hi));shape=np.sqrt(np.maximum(0,sosfilt(butter(1,22,'low',fs=SR,output='sos'),g*g))).astype(np.float32)/reference_rms
        for name,x in raw.items():
            y=band(x,float(lo),float(hi));baseline=max(active_rms(y),.0005)
            colored[name]+=y*np.clip(shape*.10/baseline,.15,4)*.60
    masks={n:np.zeros(N,np.float32) for n in NAMES}
    for e in P['relevos']:
        a=round(e['t']*SR);length=min(N-a,round(e['dur']*SR));route=e['ruta']
        for i,name in enumerate(route):masks[name][a:a+length]=np.maximum(masks[name][a:a+length],mask_note(e['dur'],route,i,length))
    outputs={};measurements=[]
    for name in raw:
        source=.4*raw[name]+colored[name]
        # La envolvente energética de la guía une los relevos; se limita el ruido en sus huecos.
        env=smooth_envelope(source);target=reference_rms
        shaped=source*np.clip(target/np.maximum(env,.002),.20,5)
        outputs[name]=shaped*masks[name]
    outputs['voz']=guide*masks['voz']
    # Primer acto y recuerdo: piano y subtono cerca, fuera del vocoder, como acompañamiento.
    tt=np.arange(N)/SR;bed=((tt<35)|((tt>=135)&(tt<160))).astype(np.float32)
    outputs['piano']+=raw['piano']*bed*.45;outputs['clarinete']+=raw['clarinete']*(tt<35)*.2
    for name,x in outputs.items():wav(out/'render'/f'relevo-{name}.wav',x)
    for e in P['relevos']:
        a=round(e['t']*SR);b=a+round(e['dur']*SR);joined=sum(outputs[n][a:b] for n in e['ruta'])
        ref=smooth_envelope(guide[a:b],cut=15);got=smooth_envelope(joined,cut=15)
        trim=min(2400,len(ref)//4);corr=float(np.corrcoef(ref[trim:-trim],got[trim:-trim])[0,1]) if len(ref)>2*trim+10 else None
        measurements.append({'id':e['id'],'t':e['t'],'ruta':e['ruta'],'correlacion_envolvente':corr,'diferencia_RMS_dB':db(joined)-db(guide[a:b])})
    dump(out/'medidas-relevos.json',{'ganancias_modelos':scales,'bandas_Hz':edges.tolist(),'metodo':'12 bandas de envolvente espectral de la guía, 40% de cuerpo original; compuertas con solapamiento y amplitud limitada.',
       'silabas':measurements,'mediana_correlacion_relevos':float(np.nanmedian([e['correlacion_envolvente'] for e in measurements if len(e['ruta'])>1 and e['correlacion_envolvente'] is not None]))})
    # Boceto real con los dos tipos de relevo, antes de campos y mezcla final.
    preview=sum(outputs.values())[40*SR:65*SR];wav(out/'render/boceto-relevos.wav',preview)
    tag=out.name.split('-')[-1]
    run(['ffmpeg','-hide_banner','-loglevel','error','-n','-i',str(out/'render/boceto-relevos.wav'),'-af','loudnorm=I=-17:TP=-2:LRA=10','-c:a','aac','-b:a','192k',str(out/f'boceto-relevos-s{SEED}-{tag}.m4a')])
    im,d=card('03 / la frase transferida a los cuerpos','Audio real del boceto, 40–65 s · curvas de energía por fuente antes de la mezcla final')
    for i,name in enumerate(NAMES):
        yy=130+i*73;d.text((32,yy),name,font=FONT(14),fill=COLORS[i]);x=outputs[name][40*SR:65*SR];hop=1200
        env=np.sqrt(np.mean(x[:len(x)//hop*hop].reshape(-1,hop)**2,axis=1));env/=max(env.max(),1e-8)
        d.line([(160+j/(len(env)-1)*1000,yy+48-float(v)*43) for j,v in enumerate(env)],fill=COLORS[i],width=2)
    png(out/'proceso'/f'03-boceto-relevos-s{SEED}-{tag}.png',im)
    print('RELEVOS LISTOS',flush=True)

def final(out):
    P=score(out);tag=out.name.split('-')[-1];t=np.arange(N)/SR
    parts={n:read(out,'relevo-'+n) for n in NAMES};mixed=np.zeros((N,2),np.float32);wet=mixed.copy()
    pans={'voz':0,'piano':-.3,'agua':.4,'clarinete':-.15,'metal':.18,'chelo':-.4};levels={'voz':1,'piano':.8,'agua':.9,'clarinete':.9,'metal':.72,'chelo':.8}
    for name,x in parts.items():
        x=band(x,95 if name!='piano' else 120,6500)*levels[name]
        pan=pans[name];st=x[:,None]*np.array([math.cos((pan+1)*math.pi/4),math.sin((pan+1)*math.pi/4)],np.float32)
        mixed+=st;wet+=st*(.1 if name=='voz' else .22)
    backgrounds={};targets={'campo':-32,'bajo':-25,'gong':-32,'waterphone':-33}
    for name,target in targets.items():
        x=read(out,name);x*=10**(target/20)/max(active_rms(x),1e-8)
        x=band(x,35 if name=='bajo' else 120,7000)
        if name=='campo':x*=np.interp(t,[0,35,85,110,135,160,195,198,210],[.4,.5,.9,1,.6,.5,.3,0,0])
        else:x*=np.clip((198-t)/1.5,0,1)
        pan={'campo':-.55,'bajo':0,'gong':.1,'waterphone':.6}[name]
        st=x[:,None]*np.array([math.cos((pan+1)*math.pi/4),math.sin((pan+1)*math.pi/4)],np.float32)
        mixed+=st;wet+=st*(.10 if name=='bajo' else .35);backgrounds[name]=db(x)
    # La coda es realmente dos vocales de agua: la segunda se remuestrea con velocidad variable.
    a=read(out,'coda-a');i=read(out,'coda-i');length=12*SR;tc=np.arange(length)/SR;freqdiff=np.interp(tc,[0,10,12],[.65,.08,.08]);ratio=(220+freqdiff)/220
    index=np.cumsum(ratio)-ratio[0];warped=np.interp(index,np.arange(len(i)),i,right=0).astype(np.float32)
    a=a[:length];a*=.07/max(active_rms(a),1e-8);warped*=.07/max(active_rms(warped),1e-8)
    fade=np.clip(tc/.8,0,1)*np.clip((12-tc)/3,0,1);coda=(a+warped)*fade
    onset=198*SR;mixed[onset:,0]+=coda*.8;mixed[onset:,1]+=(a*.65+warped*.9)*fade
    wav(out/'render/coda-doble.wav',coda)
    wetL=band(wet[:,0],150,3400);wetR=band(wet[:,1],150,3400)
    for delay,gain in [(.041,.25),(.087,.2),(.139,.14),(.223,.1),(.361,.065),(.587,.04)]:
        k=round(delay*SR);mixed[k:,0]+=wetR[:-k]*gain;mixed[k:,1]+=wetL[:-k]*gain
    mixed[:,0]=band(mixed[:,0],29);mixed[:,1]=band(mixed[:,1],29)
    mixed*=np.clip((210-t)/2.5,0,1)[:,None];mixed*=.88/max(.88,float(np.abs(mixed).max()))
    wav(out/'render/mezcla-previa.wav',mixed)
    raw=run(['ffmpeg','-hide_banner','-nostats','-i',str(out/'render/mezcla-previa.wav'),'-af','loudnorm=I=-15:TP=-1.6:LRA=11:print_format=json','-f','null','-']).stderr
    norm=json.JSONDecoder().raw_decode(raw[raw.rfind('{'):])[0];dump(out/'normalizacion.json',norm)
    af='loudnorm=I=-15:TP=-1.6:LRA=11:linear=true:'+':'.join(f'{a}={norm[b]}' for a,b in [('measured_I','input_i'),('measured_TP','input_tp'),('measured_LRA','input_lra'),('measured_thresh','input_thresh'),('offset','target_offset')])
    basename=f'mi-boca-en-otra-parte-s{SEED}-{tag}'
    run(['ffmpeg','-hide_banner','-loglevel','error','-n','-i',str(out/'render/mezcla-previa.wav'),'-af',af,'-ar','48000','-c:a','pcm_s24le',str(out/f'{basename}.wav')])
    run(['ffmpeg','-hide_banner','-loglevel','error','-n','-i',str(out/f'{basename}.wav'),'-c:a','aac','-b:a','224k','-metadata','title=Mi boca termina en otra parte','-metadata','artist=Canek Zapata',str(out/f'{basename}.m4a')])
    raw=run(['ffmpeg','-hide_banner','-nostats','-i',str(out/f'{basename}.m4a'),'-af','loudnorm=I=-15:TP=-1.6:LRA=11:print_format=json','-f','null','-']).stderr
    loud=json.JSONDecoder().raw_decode(raw[raw.rfind('{'):])[0]
    measures={}
    for name,a,b in P['secciones']:
        seg=mixed[int(a*SR):int(b*SR)];total=db(seg)
        measures[name]={'total_dBFS':total,**{label:round(db(np.stack([band(seg[:,c],lo,hi) for c in range(2)],axis=1))-total,1) for label,lo,hi in [('sub',30,90),('graves',90,300),('medios',300,2000),('presencia',2000,6000),('aire',6000,14000)]}}
    dump(out/'medidas.json',{'aac':loud,'bandas_por_seccion':measures,'niveles_relevos':levels,'fondos_dBFS':backgrounds,'coda_diferencia_frecuencias_Hz':[.65,.08]})
    _,_,Z=stft(mixed.mean(axis=1),SR,nperseg=4096,noverlap=1024);freq=np.fft.rfftfreq(4096,1/SR);ix=np.searchsorted(freq,np.geomspace(45,11000,390));v=20*np.log10(np.abs(Z[ix])+1e-8);v=np.clip((v-v.max()+65)/65,0,1)
    pix=np.stack([v[::-1]*130,v[::-1]*209,v[::-1]*220],axis=2).astype(np.uint8)
    im,d=card('04 / la cantante se retira; la frase sigue','Espectrograma del audio terminado · Boca / Relevo / Fricción / Recuerdo / Otra parte')
    im.paste(Image.fromarray(pix).resize((1136,440)),(32,125));png(out/'proceso'/f'04-mezcla-s{SEED}-{tag}.png',im);png(out/f'resultado-s{SEED}-{tag}.png',im);png(out/'og.png',im)
    frames=[Image.open(p).convert('RGB') for p in sorted((out/'proceso').glob('0[1234]-*.png'))];sheet=Image.new('RGB',(1200,630*len(frames)));[sheet.paste(f,(0,k*630)) for k,f in enumerate(frames)];palette=sheet.quantize(colors=128);q=[f.quantize(palette=palette) for f in frames]
    with (out/f'proceso-mi-boca-s{SEED}-{tag}.gif').open('xb') as fh:q[0].save(fh,format='GIF',save_all=True,append_images=q[1:],duration=[2000]*len(q),loop=0,optimize=False)
    txt(out/'proceso/README.md','# Etapas reales\n\n01: esquema antes de medir y sintetizar.\n02: resonancias medidas de las sondas y score compuesto.\n03: energía de los relevos en el boceto real antes de la mezcla final.\n04: espectrograma de la mezcla terminada.\n05: hoja de revisión de cuadros decodificados, fuera del GIF.\n\nGIF de estas cuatro capturas reales, ocho segundos, loop y paleta común. Semilla 161026; no hay pasos internos de generadores simulados.\n')
    print('MEZCLA',loud,flush=True)

def verify(out):
    P=score(out);tag=out.name.split('-')[-1]
    sr,x=wavfile.read(next(out.glob('mi-boca-en-otra-parte-*.wav')));assert sr==SR and x.shape==(N,2)
    x=x.astype(float)/2**31;assert np.isfinite(x).all() and np.abs(x).max()<1
    actual=read(out,'relevo-voz');assert np.max(np.abs(actual[172*SR:]))==0
    assert len(P['instrumentos']['bajo'])==32 and all(135<=e['t']<159 for e in P['instrumentos']['bajo'])
    hooks=[f for f in P['frases'] if f['hook']];normalized=lambda f:[(round(e['t']-f['eventos'][0]['t'],6),e['nota'],e['texto']) for e in f['eventos']]
    assert all(normalized(f)==normalized(hooks[0]) for f in hooks)
    guide=read(out,'voz');errors=[]
    for f in P['frases']:
        e=f['eventos'][-1];seg=guide[int((e['t']+.3)*SR):int((e['t']+.65)*SR)][::3].astype(float);seg-=seg.mean();f0=440*2**((e['nota']-69)/12)
        ac=correlate(seg,seg,mode='full',method='fft')[len(seg)-1:];lo=int(16000/(f0*1.35));hi=int(16000/(f0*.75));peaks,_=find_peaks(ac[lo:hi])
        if len(peaks):
            j=lo+peaks[np.argmax(ac[lo:hi][peaks])];delta=.5*(ac[j-1]-ac[j+1])/(ac[j-1]-2*ac[j]+ac[j+1]);errors.append(float(1200*np.log2(16000/(j+delta)/f0)))
    gif=next(out.glob('*.gif'));g=Image.open(gif);duration=0;contact=Image.new('RGB',(1200,1260),BG)
    for k in range(g.n_frames):g.seek(k);duration+=g.info['duration'];contact.paste(g.convert('RGB').resize((600,315)),((k%2)*600,(k//2)*315))
    assert g.n_frames==4 and duration<=10000 and gif.stat().st_size<=15*1024**2
    png(out/'proceso'/f'05-revision-gif-s{SEED}-{tag}.png',contact.crop((0,0,1200,630)))
    for p in out.rglob('*.png'):
        with Image.open(p) as im:im.verify()
    assert Image.open(out/'og.png').size==(1200,630)
    result={'duracion_s':N/SR,'pico_muestra_dBFS':float(20*np.log10(np.abs(x).max())),'repeticiones_gancho_identicas':len(hooks),
       'cantante_audible_despues_172_s':float(np.max(np.abs(actual[172*SR:]))),'guia_afinacion_mediana_abs_cents':float(np.median(np.abs(errors))),
       'metodo_afinacion':'Autocorrelación local orientativa en sílabas largas de la guía; no demuestra la inteligibilidad de los instrumentos.',
       'recuerdo_house':{'compases':8,'bpm':80,'inicio_s':135,'fin_s':159},'gif':{'frames':4,'segundos':duration/1000,'bytes':gif.stat().st_size}}
    dump(out/'verificacion.json',result);print(json.dumps(result,ensure_ascii=False,indent=1),flush=True)

if __name__=='__main__':
    if sys.argv[1]=='iniciar':initialize()
    else:{'componer':compose,'relevar':relay,'terminar':final,'verificar':verify}[sys.argv[1]](Path(sys.argv[2]).resolve())
