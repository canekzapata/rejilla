"""Etapas reales y entregas exclusivas. Nunca reutiliza un nombre de entrega."""
from pathlib import Path
import sys,json,hashlib,uuid,subprocess,io,csv,shutil
import numpy as np
from scipy.io import wavfile
from scipy.signal import stft,correlate,find_peaks
from PIL import Image,ImageDraw,ImageFont
import motores as m
import partituras as p

ROOT=Path(__file__).resolve().parent; SR=m.SR; COLORS=['#ff85ae','#d5b581','#9b9dff','#76d5c4','#8396de','#a4d273','#f0ce8b','#6daed0','#b99cec','#ff9071','#72c5af','#dd88c8']
BG='#101019'; FG='#e5e4ef'; MUTED='#9293aa'
def fuente(n):return ImageFont.truetype('C:/Windows/Fonts/consola.ttf',n)
def guardar_json(path,obj):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2)
def guardar_png(path,im):
    with Path(path).open('xb') as f:im.save(f,'PNG')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def ejecutar(args):
    r=subprocess.run(args,capture_output=True)
    if r.returncode:raise RuntimeError(r.stderr.decode('utf8','replace')[-3500:])
    return r
def etiqueta(out):return out.name.rsplit('-',1)[-1]
def nombre(out,stem,ext):return out/(stem+'-s'+str(p.SEMILLA)+'-'+etiqueta(out)+'.'+ext)
def fuentes(out,stage):
    folder=out/'fuentes'/stage;folder.mkdir(parents=True,exist_ok=False)
    result={}
    for file in sorted(ROOT.glob('*.py')):
        shutil.copyfile(file,folder/file.name);result[file.name]=sha(file)
    guardar_json(folder/'huellas.json',result)
    return result
def activo(y):
    z=y[:len(y)//320*320].reshape(-1,320,2);r=np.sqrt(np.mean(z*z,axis=(1,2)));mask=r>max(1e-7,float(r.max())*.045)
    return float(np.sqrt(np.mean(r[mask]**2))) if mask.any() else 0.
def nivel(y,target=.13):
    return (y*min(target/(activo(y)+1e-12),.86/(float(abs(y).max())+1e-12))).astype(np.float32)
def ffjson(stderr):
    txt=stderr.decode('utf8','replace');a=txt.rfind('{');b=txt.find('}',a)
    return json.loads(txt[a:b+1])
def entregar_audio(out,stem,y,target=-19):
    y=np.asarray(y,np.float32);assert y.ndim==2 and y.shape[1]==2 and np.isfinite(y).all() and float(abs(y).max())<1
    raw=out/'render'/(stem+'-'+etiqueta(out)+'.wav')
    with raw.open('xb') as f:wavfile.write(f,SR,y)
    base=['ffmpeg','-hide_banner','-nostdin','-i',str(raw)]
    stats=ffjson(ejecutar(base+['-af',f'loudnorm=I={target}:TP=-2:LRA=10:print_format=json','-f','null','NUL']).stderr)
    measured=':'.join(k+'='+stats[v] for k,v in [('measured_I','input_i'),('measured_TP','input_tp'),('measured_LRA','input_lra'),('measured_thresh','input_thresh')])
    af=f'loudnorm=I={target}:TP=-2:LRA=10:{measured}:offset={stats["target_offset"]}:linear=true'
    dst=nombre(out,stem,'m4a')
    ejecutar(base+['-n','-af',af,'-ar','48000','-c:a','aac','-b:a','224k',str(dst)])
    stats2=ffjson(ejecutar(['ffmpeg','-hide_banner','-nostdin','-i',str(dst),'-af',f'loudnorm=I={target}:TP=-2:LRA=10:print_format=json','-f','null','NUL']).stderr)
    return {'archivo':dst.name,'wav_local':str(raw.relative_to(out)),'duracion_escrita':len(y)/SR,
            'lufs':float(stats2['input_i']),'dBTP':float(stats2['input_tp']),'LRA':float(stats2['input_lra']),
            'pico_previa':float(abs(y).max()),'rms_activo_previa':activo(y)}
def decodificar(path):
    r=ejecutar(['ffmpeg','-hide_banner','-nostdin','-i',str(path),'-f','f32le','-ar',str(SR),'-ac','2','pipe:1'])
    return np.frombuffer(r.stdout,dtype=np.float32).reshape(-1,2)
def espectro(y,w,h):
    # Average channel powers, never downmix before squaring.
    vals=[]
    for c in range(2):
        f,t,z=stft(y[:,c],SR,nperseg=2048,noverlap=1536,boundary=None,padded=False)
        vals.append(abs(z)**2*4)
    power=(vals[0]+vals[1])*.5; db=10*np.log10(power+1e-14)
    freqs=np.geomspace(48,12000,h)[::-1]; rows=np.array([np.interp(freqs,f,db[:,j]) for j in range(db.shape[1])]).T
    v=np.clip((rows+85)/69,0,1); rgb=np.stack([v*.87,v*.91,v],axis=-1)
    return Image.fromarray(np.uint8(rgb*255)).resize((w,h),Image.Resampling.BILINEAR)
def base(title,subtitle,w=1600,h=960):
    im=Image.new('RGB',(w,h),BG);dr=ImageDraw.Draw(im)
    dr.text((48,28),title,font=fuente(32),fill=FG);dr.text((48,78),subtitle,font=fuente(16),fill=MUTED)
    return im,dr
def poly(dr,values,box,color,lo=None,hi=None):
    x,y,w,h=box;vals=np.asarray(values);lo=float(vals.min()) if lo is None else lo;hi=float(vals.max()) if hi is None else hi
    idx=np.linspace(0,len(vals)-1,min(len(vals),round(w))).astype(int)
    coords=[(x+j*w/max(1,len(idx)-1),y+h-h*(float(vals[i])-lo)/max(1e-9,hi-lo)) for j,i in enumerate(idx)]
    if len(coords)>1:dr.line(coords,fill=color,width=2)
def etapa_plan():
    im,dr=base('DOCE INSTRUMENTOS / primera construcción','Semilla 19103419 · partitura escrita antes de sintetizar · 19 octubre 2026')
    for i,(k,n) in enumerate(m.NOMBRES.items()):
        col=i//6;row=i%6;x=55+col*780;y=160+row*115
        dr.text((x,y),f'{i+1:02d}  {n}',font=fuente(23),fill=COLORS[i])
        dr.line((x+55,y+50,x+650,y+50),fill='#333447',width=3)
    dr.text((48,910),'Etapa real: motores y partituras preparados; audio todavía sin renderizar.',font=fuente(16),fill=MUTED)
    return im
def iniciar():
    im=etapa_plan();bio=io.BytesIO();im.save(bio,'PNG'); nonce=uuid.uuid4().hex
    versions={x.name:sha(x) for x in ROOT.glob('*.py')}
    digest=hashlib.sha256(bio.getvalue()+json.dumps(versions,sort_keys=True).encode()+nonce.encode()).hexdigest()
    out=ROOT/f'instrumentos-de-tres-tiempos-s{p.SEMILLA}-{digest[:12]}'
    out.mkdir(exist_ok=False)
    for name in ['proceso','render','fuentes']: (out/name).mkdir()
    guardar_png(out/'proceso'/f'01-plan-s{p.SEMILLA}-{digest[:12]}.png',im)
    guardar_json(out/'receta-inicial.json',{'semilla':p.SEMILLA,'hash_ejecucion':digest,'nonce':nonce,'hash_imagen_inicial':hashlib.sha256(bio.getvalue()).hexdigest(),'codigo':versions,'fecha':'2026-10-19','motor':'síntesis temporal numpy/scipy, no spectrumsynth','sr_motor':SR,'anti_sobrescritura':'mkdir exclusivo y open x/xb, ffmpeg -n'})
    guardar_json(out/'partituras-demostracion.json',{k:p.demo(k) for k in m.NOMBRES})
    guardar_json(out/'partitura-escena.json',p.escena())
    print(out,flush=True)
    return out
def panel_boca(out,spec,trace,y):
    im,dr=base('BOCA DE TRES TIEMPOS / tres recorridos','Audio sintetizado · 24 s · sin letra ni muestras de voz humana')
    for at,label in spec['partitura']['secciones']:
        x=210+at/24*1310;dr.line((x,145,x,890),fill='#343449',width=1);dr.text((x+5,120),label,font=fuente(16),fill=MUTED)
    for j,(name,lab,lo,hi) in enumerate([('f0_hz','melodía · Hz',180,420),('F1_hz','vocal · F1',250,800),('F2_hz','vocal · F2',600,2500),('cierre','articulación',0,1)]):
        yy=175+j*125;dr.text((38,yy+12),lab,font=fuente(18),fill=COLORS[j]);poly(dr,trace[name],(210,yy,1310,82),COLORS[j],lo,hi)
    im.paste(espectro(y,1310,180),(210,680));dr.text((38,716),'AAC real\n48 Hz–12 kHz',font=fuente(16),fill=MUTED)
    dr.text((48,910),'La coincidencia final se escribe; los tres recorridos no se reinician juntos en cada nota.',font=fuente(16),fill=FG)
    return im
def prueba_boca():
    a={'notas':[p.nota(0,57,2,.8)],'vocales':[[0,'a'],[2,'a']]};u={'notas':[p.nota(0,57,2,.8)],'vocales':[[0,'u'],[2,'u']]}
    ya,_,_=m.render('boca',a,2,semilla=100);yu,_,_=m.render('boca',u,2,semilla=100)
    def pitch(y):
        v=y[SR//2:SR,0];z=correlate(v,v,mode='full',method='fft')[len(v)-1:];z/=np.arange(len(v),0,-1)
        peaks,_=find_peaks(z);peaks=peaks[(peaks>SR/700)&(peaks<SR/80)]
        lag=int(peaks[z[peaks]>=.98*np.max(z[peaks])][0])
        shift=.5*(z[lag-1]-z[lag+1])/(z[lag-1]-2*z[lag]+z[lag+1])
        return float(SR/(lag+shift))
    def centroid(y):
        v=y[SR//2:SR,0];powr=abs(np.fft.rfft(v*np.hanning(len(v))))**2;f=np.fft.rfftfreq(len(v),1/SR);return float((f*powr).sum()/powr.sum())
    fa,fu=pitch(ya),pitch(yu);ca,cu=centroid(ya),centroid(yu)
    assert abs(fa-220)<4 and abs(fu-220)<4,(fa,fu)
    assert abs(ca-cu)>100,(ca,cu)
    return {'f0_esperada':220,'f0_vocal_a':fa,'f0_vocal_u':fu,'centroide_a':ca,'centroide_u':cu,'conclusion':'cambiar vocal cambia el espectro conservando la periodicidad fundamental; no prueba inteligibilidad'}
def grupo(out,stage,keys,num):
    if (out/(stage+'.json')).exists():raise FileExistsError('Etapa ya realizada; no se pisa')
    versions=fuentes(out,stage);deliveries={};images=[];all_scores=json.loads((out/'partituras-demostracion.json').read_text('utf8'))
    traces_for_boca=None
    for i,k in enumerate(keys):
        s=all_scores[k]; print('Sintetizando',m.NOMBRES[k],flush=True)
        y,trace,info=m.render(k,s['partitura'],s['duracion'],semilla=s['semilla']);y=nivel(y)
        delivery=entregar_audio(out,'muestra-'+k,y)
        if k=='boca':
            delivery['prueba']=prueba_boca();traces_for_boca=trace
            with nombre(out,'controles-boca','csv').open('x',newline='',encoding='utf8') as f:
                w=csv.writer(f);w.writerow(['tiempo_s',*trace]);
                for j in range(0,len(y),128):w.writerow([j/SR,*[float(z[j]) for z in trace.values()]])
        if k in ('cuerda','arpa'):assert info['error_max_intercambio']<1e-10
        if k=='organo':
            # Same pressure, different prior traversal; inspect actual state gains.
            first=round(12*SR);second=round(21*SR);hist={key:[float(v[first]),float(v[second])] for key,v in trace.items() if key.startswith('divisor_')}
            assert any(abs(a-b)>.7 for a,b in hist.values());info['igual_presion_distinto_estado']=hist
        delivery['medidas_motor']=info;delivery['codigo']=versions;deliveries[k]=delivery
        decoded=decodificar(out/delivery['archivo']);images.append((k,decoded));print('Entregado',k,delivery['lufs'],'LUFS',flush=True)
    if stage=='02-boca':
        im=panel_boca(out,all_scores['boca'],traces_for_boca,images[0][1])
    else:
        im,dr=base('CUERPOS IMPOSIBLES' if num==3 else 'ESTACIÓN ELECTRÓNICA / sci-fi','Etapa real: muestras independientes renderizadas · espectros del AAC entregado')
        for i,(k,y) in enumerate(images):
            row=i//2;col=i%2;x=45+col*780;yy=140+row*250
            dr.text((x,yy),m.NOMBRES[k],font=fuente(20),fill=COLORS[list(m.NOMBRES).index(k)])
            im.paste(espectro(y,730,175),(x,yy+35))
        dr.text((48,915),'Escala fija: 48 Hz–12 kHz / −85 a −16 dBFS por bin · potencia media estéreo.',font=fuente(16),fill=MUTED)
    guardar_png(out/'proceso'/f'{num:02d}-{stage.split("-",1)[1]}-s{p.SEMILLA}-{etiqueta(out)}.png',im)
    guardar_json(out/(stage+'.json'),deliveries)
    print('Etapa completa:',stage,flush=True)

def escena(out):
    versions=fuentes(out,'05-escena');score=json.loads((out/'partitura-escena.json').read_text('utf8'));stems={};raw_metrics={}
    for i,(k,s) in enumerate(score['pistas'].items()):
        print('Escena:',m.NOMBRES[k],flush=True);y,trace,info=m.render(k,s,score['duracion'],semilla=p.SEMILLA+i)
        y=nivel(y,.12)*score['ganancias'][k];stems[k]=y
        with (out/'render'/f'escena-{k}-{etiqueta(out)}.wav').open('xb') as f:wavfile.write(f,SR,y)
        raw_metrics[k]={'pico':float(abs(y).max()),'rms_activo':activo(y),'ganancia':score['ganancias'][k]}
    mix=sum(stems.values());voice=stems['boca']; other=mix-voice
    # Modest common space and selective breathing space under the lead.
    envelope=np.sqrt(np.mean(voice*voice,axis=1));duck=1-.22*np.clip(m.suavizar(envelope,SR,.04)/.085,0,1)
    mix=voice+other*duck[:,None]
    for channel,delay in [(0,.073),(1,.131)]:
        n=round(delay*SR);mix[n:,channel]+=.075*mix[:-n,1-channel].copy()
    mix*=m.envolvente(len(mix),SR,.03,1.5)[:,None];mix=nivel(mix,.15)
    deliver=entregar_audio(out,'la-boca-abre-una-estacion',mix,-16)
    solo=entregar_audio(out,'escena-boca-sola',nivel(voice),-19)
    decoded=decodificar(out/deliver['archivo']);im=panorama(score,stems,decoded)
    guardar_png(nombre(out,'partitura-y-espectrograma','png'),im)
    guardar_png(out/'proceso'/f'05-escena-s{p.SEMILLA}-{etiqueta(out)}.png',im.resize((1600,960),Image.Resampling.LANCZOS))
    guardar_json(out/'05-escena.json',{'mezcla':deliver,'boca_sola':solo,'pistas':raw_metrics,'codigo':versions,'mezcla_descripcion':'stems con ganancias nominales, ducking hasta 22 % sobre acompañamiento, espacio común 73/131 ms al 7.5 %, ajuste global de loudness; stems no son sumandos exactos del AAC'})
    print('Escena completa',deliver,flush=True)
def panorama(score,stems,y):
    im,dr=base('LA BOCA ABRE UNA ESTACIÓN','Partitura, energía por cuerpo y espectrograma del AAC · 84 s · doce prototipos',1800,1180)
    x0=255;w=1490;dur=score['duracion']
    for at,label in score['secciones']:
        x=x0+at/dur*w;dr.line((x,135,x,1125),fill='#44445b');dr.text((x+4,120),label,font=fuente(15),fill=FG)
    for i,(k,s) in enumerate(score['pistas'].items()):
        yy=160+i*31;dr.text((20,yy),m.NOMBRES[k][:23],font=fuente(14),fill=COLORS[i]);dr.line((x0,yy+24,x0+w,yy+24),fill='#252535')
        for e in s['notas']:
            x=x0+e['t']/dur*w;wid=max(2,e['dur']/dur*w);dy=np.clip((e['midi']-35)/57,0,1)*14
            dr.rectangle((x,yy+18-dy,x+wid,yy+22-dy),fill=COLORS[i])
    dr.text((255,549),'Ataques y alturas de referencia; las colas se ven en la energía de las pistas.',font=fuente(14),fill=MUTED)
    for i,k in enumerate(score['pistas']):
        yy=585+i*10;z=stems[k];B=640;v=z[:len(z)//B*B].reshape(-1,B,2);power=np.mean(v*v,axis=(1,2));db=10*np.log10(power+1e-12)
        val=np.clip((db+65)/47,0,1);rgb=np.array(Image.new('RGB',(1,1),COLORS[i]))[0,0];arr=(val[None,:,None]*rgb).astype(np.uint8)
        im.paste(Image.fromarray(arr).resize((w,8)),(x0,yy))
    dr.text((30,620),'Energía de pistas\nantes de la mezcla',font=fuente(14),fill=MUTED)
    im.paste(espectro(y,w,330),(x0,745));dr.text((25,755),'12 kHz',font=fuente(16),fill=MUTED);dr.text((25,1040),'48 Hz',font=fuente(16),fill=MUTED)
    for sec in range(0,85,7):dr.text((x0+sec/dur*w,1090),str(sec)+' s',font=fuente(14),fill=MUTED)
    dr.text((45,1140),'Escala fija −85 a −16 dBFS/bin · FFT 2048 / salto 512 · potencia estéreo · ocupación no equivale a calidad.',font=fuente(15),fill=MUTED)
    return im

def cerrar(out):
    fuentes(out,'06-cierre')
    stages=['02-boca','03-imposibles','04-electronicos','05-escena']
    infos={stage:json.loads((out/(stage+'.json')).read_text('utf8')) for stage in stages}
    playlist=[]; cues=[]; cursor=0
    for stage in stages[:3]:
        for k,info in infos[stage].items():
            y=decodificar(out/info['archivo']);playlist.append(y);playlist.append(np.zeros((round(.6*SR),2),np.float32))
            cues.append({'id':k,'nombre':m.NOMBRES[k],'inicio_s':cursor/SR,'fin_s':(cursor+len(y))/SR,'muestra':info['archivo']});cursor+=len(y)+round(.6*SR)
    guardar_json(out/'indice-atlas.json',cues)
    atlas=entregar_audio(out,'atlas-doce-instrumentos',nivel(np.concatenate(playlist)), -19)
    shots=sorted((out/'proceso').glob('0[1-5]-*.png'));frames=[Image.open(x).convert('RGB').resize((1200,720),Image.Resampling.LANCZOS) for x in shots]
    gif=nombre(out,'proceso-doce-instrumentos','gif')
    with gif.open('xb') as f:frames[0].save(f,format='GIF',save_all=True,append_images=frames[1:],duration=1500,loop=0,optimize=True)
    with Image.open(gif) as g:
        duration=0;decoded_frames=[];nframes=g.n_frames
        for i in range(nframes):
            g.seek(i);duration+=g.info['duration']/1000;decoded_frames.append(g.convert('RGB').copy())
    assert duration<=10 and gif.stat().st_size<=15_000_000
    contact=Image.new('RGB',(1200,720*len(frames)),BG)
    for i,frame in enumerate(decoded_frames):contact.paste(frame,(0,i*720))
    guardar_png(out/'proceso'/f'06-cuadros-del-gif-s{p.SEMILLA}-{etiqueta(out)}.png',contact)
    image=Image.open(nombre(out,'partitura-y-espectrograma','png')).convert('RGB');og=image.resize((1200,787),Image.Resampling.LANCZOS).crop((0,0,1200,630));guardar_png(out/'og.png',og)
    guardar_json(out/'06-cierre.json',{'atlas':atlas,'gif':{'archivo':gif.name,'duracion_s':duration,'bytes':gif.stat().st_size,'cuadros':nframes},'analisis':{'sr':SR,'FFT':2048,'salto':512,'dbFS_por_bin':[-85,-16],'hz':[48,12000],'canales':'potencia media, no suma mono'},'escucha':'verificación técnica; no se atribuye escucha humana propia ni inteligibilidad al prototipo'})
    # Hash only immutable deliverables; exclude WAVs and the manifest itself.
    manifest={str(f.relative_to(out)):sha(f) for f in sorted(out.rglob('*')) if f.is_file() and f.suffix!='.wav'}
    guardar_json(out/'huellas-entrega.json',manifest)
    print('Cierre:',atlas,'GIF',duration,'s',flush=True)

if __name__=='__main__':
    stage=sys.argv[1]
    if stage=='iniciar':iniciar()
    else:
        out=Path(sys.argv[2]).resolve(); assert out.parent==ROOT and out.is_dir()
        if stage=='boca':grupo(out,'02-boca',['boca'],2)
        elif stage=='imposibles':grupo(out,'03-imposibles',['cuerda','piano','arpa','organo','sala'],3)
        elif stage=='electronicos':grupo(out,'04-electronicos',['cristal','estacion','terminal','plasma','androide','fotones'],4)
        elif stage=='escena':escena(out)
        elif stage=='cerrar':cerrar(out)
        else:raise ValueError(stage)
