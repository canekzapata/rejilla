"""La mesa se mueve: preparar / trio / mezcla / verificar <carpeta>.
Se conserva cada salida; un destino existente hace fallar la operación.
"""
import hashlib,importlib.util,json,math,os,subprocess,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.io import wavfile
from scipy.signal import butter,sosfilt,resample_poly,stft,correlate,find_peaks
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parent
SEED=20261016;SR=48000;TICK=60/96/4;DUR=185.;N=int(DUR*SR)
BG=(26,24,34);FG=(246,231,207);COL={'piano':(253,177,89),'bajo':(104,215,200),'percusion':(211,143,238)}
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/consola.ttf',n)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def savejson(p,x):
    with Path(p).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
def textfile(p,s):
    with Path(p).open('x',encoding='utf8') as f:f.write(s)
def png(p,x):
    with Path(p).open('xb') as f:x.save(f,'PNG')
def wav(p,x,sr=SR):
    with Path(p).open('xb') as f:wavfile.write(f,sr,np.asarray(x,dtype=np.float32))
def run(args):return subprocess.run(args,check=True,capture_output=True,text=True,encoding='utf8',errors='replace')
def rmsdb(x):return float(10*np.log10(np.mean(np.asarray(x,dtype=float)**2)+1e-14))
def hp(x,f):return sosfilt(butter(2,f,'high',fs=SR,output='sos'),x,axis=0).astype(np.float32)
def read(out,n):
    sr,x=wavfile.read(out/'render'/f'{n}.wav');assert sr==SR and len(x)==N
    return x.astype(np.float32)
def card(title,sub):
    im=Image.new('RGB',(1200,630),BG);d=ImageDraw.Draw(im)
    d.text((40,22),'LA MESA SE MUEVE',font=font(35),fill=FG)
    d.text((40,74),title,font=font(20),fill=COL['piano'])
    d.text((40,594),sub,font=font(14),fill=FG);return im,d
def phases(P):
    im,d=card('01 / cada quien vuelve a otra hora','Partitura real · 96 BPM · ciclos de 15, 17 y 16 subdivisiones · semilla 20261016')
    for i,name in enumerate(COL):
        yy=190+i*130;d.text((40,yy-48),name,font=font(19),fill=COL[name])
        d.line((40,yy+35,1155,yy+35),fill=(61,53,66))
        for e in P[name]:
            x=40+e['t']/185*1110;mod=(e['tick']%16)/16
            d.ellipse((x-1,yy+30-mod*65,x+2,yy+33-mod*65),fill=COL[name])
    for t,label in [(0,'sentarse'),(40,'piano 15'),(60,'bajo 17'),(100,'coincidir'),(150,'hacer sitio')]:
        x=40+t/185*1110;d.line((x,130,x,560),fill=(65,56,70));d.text((x,115),label,font=font(13),fill=FG)
    return im

def prepare():
    piano=[];bass=[];perc=[];rng=np.random.default_rng(SEED)
    voicings=[[50,55,60],[50,55,62],[50,57,62],[52,57,62],[52,57,60],[50,55,60]]
    roots=[38,43,34,40,33,38]
    # Los ciclos se agendan por su inicio. Se cambia su silencio final, conservando los ataques internos.
    tick=0;k=0
    while tick*TICK<150:
        t=tick*TICK;length=16 if t<40 else 15;ch=voicings[(k//2)%6]
        for j,pos in enumerate([0,3,7,10,13]):
            notes=ch if j==0 else [[65,69,67,62][j-1]+(0 if k%4<2 else 2)]
            piano.append({'t':(tick+pos)*TICK+(.018 if pos%2 else 0),'tick':tick+pos,'ciclo':k,'periodo':length,
              'notas':notes,'dur':.62 if j==0 else [.35,.48,.3,.42][j-1],'v':.85 if j==0 else .62+(.15 if j==3 else 0)})
        tick+=length;k+=1
    tick=0;k=0
    while tick*TICK<150:
        length=16 if tick*TICK<60 else 17;root=roots[(k//2)%6]
        for j,pos in enumerate([0,5,11]):
            bass.append({'t':(tick+pos)*TICK,'tick':tick+pos,'ciclo':k,'periodo':length,
             'nota':root+[0,7,12][j],'dur':[.65,.42,.38][j],'v':[.78,.48,.55][j]})
        tick+=length;k+=1
    # Los encuentros generan ataques nuevos. El patrón final se elige de los encuentros observados.
    meetings=sorted({e['tick'] for e in piano if 100<=e['t']<150 and any(abs(e['t']-b['t'])<.028 for b in bass)})
    hist=np.bincount([t%16 for t in meetings],minlength=16);found=sorted(np.argsort(-hist,kind='stable')[:4].tolist())
    for b in range(60):
        start=b*16
        for pos,unit,v in [(0,'#k',.65),(4,'#t',.5),(6,'#s',.19),(10,'#k',.3),(12,'#C',.4),(14,'#s',.16)]:
            if b<4 and pos not in [0,6,12]:continue
            perc.append({'t':(start+pos)*TICK,'tick':start+pos,'unidad':unit,'v':v,'tipo':'pulso'})
    for tick in meetings:
        perc.append({'t':tick*TICK,'tick':tick,'unidad':'#t','v':.65,'tipo':'encuentro'})
    # Final escrito en común con el nuevo patrón; no es el mcm de los tres ciclos.
    piano=[e for e in piano if e['t']<150];bass=[e for e in bass if e['t']<150]
    for b in range(60,71):
        root=roots[((b-60)//2)%6];ch=voicings[((b-60)//2)%6]
        for j,pos in enumerate(found):
            piano.append({'t':(b*16+pos)*TICK,'tick':b*16+pos,'ciclo':100+b,'periodo':16,'notas':ch if j==0 else [62+[0,3,7,5][j]],'dur':.66,'v':.7})
            if j in [0,2]:bass.append({'t':(b*16+pos)*TICK,'tick':b*16+pos,'ciclo':100+b,'periodo':16,'nota':root+(7 if j==2 else 0),'dur':.7,'v':.68})
            perc.append({'t':(b*16+pos)*TICK,'tick':b*16+pos,'unidad':['#k','#s','#t','#C'][j],'v':.45,'tipo':'sitio'})
    piano.append({'t':178,'tick':178/TICK,'ciclo':200,'periodo':0,'notas':[50,55,62,65],'dur':2.0,'v':.7})
    bass.append({'t':178,'tick':178/TICK,'ciclo':200,'periodo':0,'nota':38,'dur':2.0,'v':.6})
    lines=[(7.5,'de jé tu va so en la me sa'),(15,'don de ter mi na la luz'),(22.5,'la si lla guar da tu for ma'),(30,'yo me a co mo do des pués'),
      (40,'te guar dé el mis mo lu gar'),(47.5,'pe ro la me sa se mue ve'),(55,'te guar dé el mis mo lu gar'),(62.5,'pe ro la me sa se mue ve'),
      (72.5,'pu se la ma no en el bor de'),(80,'el bor de cam bió de lu gar'),(87.5,'mi co do lle gó pri me ro'),(95,'mi som bra em pe zó a bai lar'),
      (105,'si vuel vo a de cir tu nom bre'),(112.5,'la fra se me que da de trás'),(122.5,'te guar dé el mis mo lu gar'),(130,'pe ro la me sa se mue ve'),
      (140,'co rre tu si lla o tro po co'),(147.5,'a quí nos po de mos sen tar'),(155,'tu va so ya en con tró el bor de'),(162.5,'mi ma no te en cuen tra al lle gar'),
      (170,'te guar dé el mis mo lu gar'),(176,'hi ci mos un si tio al mo ver nos')]
    melody=[57,60,62,65,64,62,60,57,55,57,60];hook=[62,65,64,62,60,57,60,62,57]
    phrases=[]
    for idx,(t,line) in enumerate(lines):
        syllables=line.split();ev=[];cur=t+(.3125 if t>=150 else 0)
        for j,s in enumerate(syllables):
            dur=([2,2,3,2,2,3,2,4,2,2,3][j%11])*TICK
            note=(hook if 'guar dé' in line or 'mue ve' in line else melody)[j%(len(hook) if 'guar dé' in line or 'mue ve' in line else len(melody))]
            if idx%4==1 and t<40:note-=2
            if j==len(syllables)-1:dur=.85 if t<175 else 1.5
            ev.append({'t':cur,'dur':dur+.025 if j<len(syllables)-1 else dur,'texto':s,'nota':note});cur+=dur
        phrases.append({'eventos':ev,'nivel':.7,'pan':-.03})
    P={'semilla':SEED,'bpm':96,'duracion':DUR,'tick_s':TICK,'piano':piano,'bajo':bass,'percusion':sorted(perc,key=lambda e:e['t']),
       'encuentros_ticks':meetings,'patron_final':found,'frases':phrases,'secciones':[['sentarse',0,40],['correrse',40,100],['perder el borde',100,150],['hacer sitio',150,185]]}
    im=phases(P);nonce=os.urandom(24).hex();digest=hashlib.sha256(im.tobytes()+Path(__file__).read_bytes()+nonce.encode()).hexdigest();tag=digest[:12]
    out=ROOT/f'la-mesa-se-mueve-s{SEED}-{tag}';out.mkdir(exist_ok=False)
    for name in ['proceso','render','fuentes']: (out/name).mkdir()
    savejson(out/'partitura.json',P);png(out/'proceso'/f'01-partitura-s{SEED}-{tag}.png',im)
    with (out/'fuentes/producir.py').open('xb') as f:f.write(Path(__file__).read_bytes())
    with (out/'fuentes/voz.cjs').open('xb') as f:f.write((REPO/'lo-que-no-sono/voz.cjs').read_bytes())
    savejson(out/'receta-inicial.json',{'id':digest,'nonce':nonce,'semilla':SEED,'fecha_local':'2026-10-15',
      'nota_semilla':'Identificador numérico, no fecha de producción.', 'fuentes':{'producir.py':sha(__file__),'voz.cjs':sha(REPO/'lo-que-no-sono/voz.cjs'),'musica.py':sha(REPO/'musica.py')},
      'imagen_inicial_sha256':sha(next((out/'proceso').glob('*.png'))),'banco_sha256':sha(REPO/'inferencia/vendor/difonos/bancos/sabina-1-b44e7fab5cee/banco.flac')})
    print(out,flush=True)

def piano_render(out,P):
    spec=importlib.util.spec_from_file_location('modal_mesa',REPO/'musica.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
    M.S=16384;M.H=16384;M.N=32768;M.T=2.;M.F=.5;M.R=2048
    track=M.Pista('piano',93)
    for i,e in enumerate(P['piano']):
        metal=float(np.interp(e['t'],[0,45,100,130,150,180],[0,.05,.65,.85,.4,.08]))
        for j,m in enumerate(e['notas']):
            f=440*2**((m-69)/12);t=e['t']+j*.008;pan=-.3+j*.14
            for mul,a,decay in [(1,1,2.4),(2.001+metal*.018,.29,4.5),(3.006+metal*.08,.13,7),(5.01+metal*.2,.035+metal*.07,11)]:
                track.modo(f*mul,.12*e['v']*a,t,decay,ataque=800,suelta=e['dur'],ar=12,pan=pan,fase=(i*.31+j)%6.28)
    print('piano: partitura espectral',len(track.segs),'segmentos',flush=True)
    L,R=track.escribir();mag,phase,scale=M.a_imagen(L,R)
    for name,x in [('magnitud',mag),('fase',phase)]:
        with (out/'render'/f'piano-{name}.raw').open('xb') as f:x.tofile(f)
    inp=lambda name:['-f','rawvideo','-pix_fmt','gray16le','-s',f'93x{M.H*2}','-r','1','-i',str(out/'render'/f'piano-{name}.raw')]
    run(['ffmpeg','-hide_banner','-loglevel','error','-n',*inp('magnitud'),*inp('fase'),'-filter_complex',
      '[0]setpts=N/TB,format=gray16le[m];[1]setpts=N/TB,format=gray16le[p];[m][p]spectrumsynth=sample_rate=16384:channels=2:scale=lin:slide=fullframe:win_func=rect:overlap=0',
      '-c:a','pcm_f32le',str(out/'render/piano-rejilla.wav')])
    sr,y=wavfile.read(out/'render/piano-rejilla.wav');ref=track.tiempo(76,80,0);got=y[76*sr:80*sr,0]*scale
    snr=float(20*np.log10(np.linalg.norm(ref)/np.linalg.norm(got-ref)));assert snr>35
    savejson(out/'prueba-piano.json',{'SNR_dB':snr,'fragmento_s':[76,80],'escala':float(scale),'sample_rate':sr})
    return resample_poly(y*scale,375,128)[:N].astype(np.float32)

def trio(out):
    P=json.loads((out/'partitura.json').read_text(encoding='utf8'));tag=out.name.split('-')[-1]
    piano=piano_render(out,P);bass=np.zeros((N,2),np.float32);perc=bass.copy()
    def add(bus,t,y,pan=0):
        a=int(round(t*SR));n=min(len(y),len(bus)-a)
        if n>0:bus[a:a+n]+=np.asarray(y[:n],np.float32)[:,None]*np.array([math.cos((pan+1)*math.pi/4),math.sin((pan+1)*math.pi/4)],np.float32)
    previous=38
    for e in P['bajo']:
        tt=np.arange(int((e['dur']+.5)*SR))/SR;note=e['nota']+(np.clip(previous-e['nota'],-4,4))*np.exp(-tt/ .032)
        freq=440*2**((note-69)/12);phase=np.cumsum(freq)/SR*2*np.pi
        env=(1-np.exp(-tt*130))*np.exp(-tt*1.9)*np.exp(-np.maximum(tt-e['dur'],0)*20)
        y=(np.sin(phase)+.24*np.sin(2*phase)+.085*np.sin(3*phase))*env*.34*e['v']
        add(bass,e['t'],y,.05);previous=e['nota']
    bank=REPO/'inferencia/vendor/difonos/bancos/sabina-1-b44e7fab5cee'
    run(['ffmpeg','-hide_banner','-loglevel','error','-n','-i',str(bank/'banco.flac'),'-c:a','pcm_f32le',str(out/'render/banco-decodificado.wav')])
    sr,x=wavfile.read(out/'render/banco-decodificado.wav');x=x.mean(axis=1) if x.ndim==2 else x
    manifest=json.loads((bank/'manifiesto.json').read_text(encoding='utf8'));samples={}
    for unit in ['#k','#t','#s','#C']:
        u=manifest['unidades'][unit];y=x[u['inicio']+u['izq']:u['inicio']+u['der']].astype(float)
        y=resample_poly(y,320,147);y/=max(np.sqrt(np.mean(y*y)),1e-7)
        edge=min(180,len(y)//4);env=np.ones(len(y));env[:edge]=np.linspace(0,1,edge);env[-edge:]=np.linspace(1,0,edge);samples[unit]=y*env
    for e in P['percusion']:
        shade=float(np.interp(e['t'],[0,100,130,150,180],[.8,.9,.65,1,.55]))
        add(perc,e['t'],samples[e['unidad']]*.065*e['v']*shade,{'#k':-.18,'#t':.12,'#s':-.5,'#C':.4}[e['unidad']])
        # k excita un pequeño cuerpo de madera: el golpe comparte la envolvente de la consonante.
        if e['unidad']=='#k':
            tt=np.arange(int(.16*SR))/SR;y=(np.sin(2*np.pi*82*tt)+.35*np.sin(2*np.pi*174*tt))*(1-np.exp(-tt*900))*np.exp(-tt*31)*e['v']*.13
            add(perc,e['t'],y,-.12)
    # Un arco dinámico cambia el peso de cada parte sin modificar sus tiempos.
    times=np.arange(N)/SR;end=np.clip((183-times)/2,0,1)[:,None]
    piano*=end;bass*=end;perc*=end
    for name,x in [('piano',piano),('bajo',bass),('percusion',hp(perc,60))]:wav(out/'render'/f'{name}.wav',x)
    excerpt=piano[50*SR:78*SR]+bass[50*SR:78*SR]+perc[50*SR:78*SR]
    wav(out/'render/boceto-trio.wav',excerpt)
    run(['ffmpeg','-hide_banner','-loglevel','error','-n','-i',str(out/'render/boceto-trio.wav'),'-af','loudnorm=I=-17:TP=-2:LRA=10','-c:a','aac','-b:a','192k',str(out/f'boceto-trio-s{SEED}-{tag}.m4a')])
    im,d=card('02 / el trío ya cambia de apoyo','Boceto real de 28 s: 50–78 s · piano naranja, bajo turquesa, consonantes lila')
    for i,(name,bus) in enumerate([('piano',piano),('bajo',bass),('percusion',perc)]):
        yy=190+i*130;d.text((40,yy-25),name,font=font(16),fill=COL[name])
        sig=bus[50*SR:78*SR];hop=1200;env=np.sqrt(np.mean(sig[:len(sig)//hop*hop].reshape(-1,hop,2)**2,axis=(1,2)))
        env/=max(env.max(),1e-9)
        pts=[(40+j/(len(env)-1)*1110,yy+60-float(v)*65) for j,v in enumerate(env)];d.line(pts,fill=COL[name],width=2)
        for e in P[name]:
            if 50<=e['t']<78:
                x=40+(e['t']-50)/28*1110;d.line((x,yy+60,x,yy+66),fill=FG)
    png(out/'proceso'/f'02-trio-s{SEED}-{tag}.png',im)
    savejson(out/'boceto-medidas.json',{'fragmento_s':[50,78],'piano_periodo_s':15*TICK,'bajo_periodo_s':17*TICK,'percusion_periodo_s':16*TICK,
       'encuentros':len(P['encuentros_ticks']),'patron_final':P['patron_final'],'rms_dBFS':{'piano':rmsdb(piano),'bajo':rmsdb(bass),'percusion':rmsdb(perc)}})
    print('TRÍO LISTO; patrón encontrado:',P['patron_final'],flush=True)

def mezcla(out):
    P=json.loads((out/'partitura.json').read_text(encoding='utf8'));tag=out.name.split('-')[-1]
    piano,bass,perc,voice=[read(out,n) for n in ['piano','bajo','percusion','voz']]
    piano*=1.5;bass*=.8;perc*=.85;voice=hp(voice,115)
    # Al perder el borde cambia el timbre del piano, conservando su fraseo.
    times=np.arange(N)/SR;drive=np.interp(times,[0,40,100,125,150,180],[0,0,.28,.6,.18,0]).astype(np.float32)[:,None]
    piano=piano*(1-drive)+np.tanh(piano*4)/2*drive
    rest=piano+bass+perc;gains=[]
    for phrase in P['frases']:
        a=max(0,int((phrase['eventos'][0]['t']-.12)*SR));b=min(N,int((phrase['eventos'][-1]['t']+phrase['eventos'][-1]['dur']+.15)*SR))
        gain=float(np.clip(10**((rmsdb(rest[a:b])-rmsdb(voice[a:b])+1)/20),.4,8));env=np.full(b-a,gain,np.float32);edge=min(4800,(b-a)//2)
        env[:edge]=np.linspace(1,gain,edge);env[-edge:]=np.linspace(gain,1,edge);voice[a:b]*=env[:,None]
        gains.append({'t':phrase['eventos'][0]['t'],'ganancia':gain,'voz_sobre_resto_dB':rmsdb(voice[a:b])-rmsdb(rest[a:b])})
    # Arco por frase; el banco conserva consonantes y encadena vocales con 25 ms de encime.
    mix=rest+voice;wet=piano*.16+voice*.16
    wet=sosfilt(butter(2,3200,'low',fs=SR,output='sos'),wet,axis=0).astype(np.float32)
    for delay,g in [(.043,.26),(.079,.19),(.137,.13),(.223,.09),(.347,.05)]:
        k=int(delay*SR);mix[k:]+=wet[:-k,::-1]*g
    mix=hp(mix,30);mix*=np.clip((DUR-times)/2,0,1)[:,None];mix*=.88/max(.88,float(np.abs(mix).max()))
    wav(out/'render/mezcla-previa.wav',mix);wav(out/'render/voz-mezcla.wav',voice)
    raw=run(['ffmpeg','-hide_banner','-nostats','-i',str(out/'render/mezcla-previa.wav'),'-af','loudnorm=I=-15:TP=-1.5:LRA=10:print_format=json','-f','null','-']).stderr
    norm=json.JSONDecoder().raw_decode(raw[raw.rfind('{'):])[0];savejson(out/'normalizacion.json',norm)
    filt='loudnorm=I=-15:TP=-1.5:LRA=10:linear=true:'+':'.join(f'{a}={norm[b]}' for a,b in [('measured_I','input_i'),('measured_TP','input_tp'),('measured_LRA','input_lra'),('measured_thresh','input_thresh'),('offset','target_offset')])
    name=f'la-mesa-se-mueve-s{SEED}-{tag}'
    run(['ffmpeg','-hide_banner','-loglevel','error','-n','-i',str(out/'render/mezcla-previa.wav'),'-af',filt,'-ar','48000','-c:a','pcm_s24le',str(out/f'{name}.wav')])
    run(['ffmpeg','-hide_banner','-loglevel','error','-n','-i',str(out/f'{name}.wav'),'-c:a','aac','-b:a','224k','-metadata','title=La mesa se mueve','-metadata','artist=Canek Zapata',str(out/f'{name}.m4a')])
    raw=run(['ffmpeg','-hide_banner','-nostats','-i',str(out/f'{name}.m4a'),'-af','loudnorm=I=-15:TP=-1.5:LRA=10:print_format=json','-f','null','-']).stderr
    loud=json.JSONDecoder().raw_decode(raw[raw.rfind('{'):])[0]
    measures={'aac':loud,'voz_por_frase':gains,'bandas_por_seccion':{}}
    for label,a,b in P['secciones']:
        seg=mix[int(a*SR):int(b*SR)];total=rmsdb(seg);bands={}
        for name,lo,hi in [('sub',30,90),('graves',90,300),('medios',300,2000),('presencia',2000,6000),('aire',6000,15000)]:
            bands[name]=round(rmsdb(sosfilt(butter(2,[lo,hi],'band',fs=SR,output='sos'),seg,axis=0))-total,1)
        measures['bandas_por_seccion'][label]={'total_dBFS':total,**bands}
    savejson(out/'medidas.json',measures)
    f,t,z=stft(mix.mean(axis=1),SR,nperseg=4096,noverlap=1024);bins=np.searchsorted(f,np.geomspace(45,11000,350));v=20*np.log10(np.abs(z[bins])+1e-8);v=np.clip((v-v.max()+65)/65,0,1)
    pixels=np.stack([v[::-1]*253,v[::-1]*177,v[::-1]*120],axis=2).astype(np.uint8)
    im,d=card('03 / otro groove aparece entre los instrumentos','Espectrograma de la mezcla real · 45 Hz–11 kHz · Canek Zapata')
    im.paste(Image.fromarray(pixels).resize((1110,430)),(40,135))
    png(out/'proceso'/f'03-mezcla-s{SEED}-{tag}.png',im);png(out/f'resultado-s{SEED}-{tag}.png',im);png(out/'og.png',im)
    # Una paleta global para mantener colores y tipografía constantes entre las etapas reales.
    frames=[Image.open(p).convert('RGB') for p in sorted((out/'proceso').glob('0[123]-*.png'))]
    sheet=Image.new('RGB',(1200,1890));[sheet.paste(f,(0,i*630)) for i,f in enumerate(frames)]
    palette=sheet.quantize(colors=128);q=[f.quantize(palette=palette) for f in frames]
    with (out/f'proceso-la-mesa-se-mueve-s{SEED}-{tag}.gif').open('xb') as fh:q[0].save(fh,format='GIF',save_all=True,append_images=q[1:],duration=[2400]*3,loop=0,optimize=False)
    textfile(out/'proceso/README.md','# Etapas reales\n\n01: partitura antes de sintetizar.\n02: envolventes medidas del boceto real del trío (50–78 s), antes de mezclar voces.\n03: espectrograma de la mezcla terminada.\n\nEl GIF reúne estas tres etapas reales, 7.2 segundos, loop y paleta común. Semilla 20261016.\nEl hash, nonce, parámetros y hashes de fuentes están en las recetas. Sin sobrescribir salidas previas.\n')
    print('MEZCLA LISTA',loud,flush=True)

def verify(out):
    P=json.loads((out/'partitura.json').read_text(encoding='utf8'))
    sr,x=wavfile.read(next(out.glob('la-mesa-se-mueve-*.wav')));assert sr==SR and x.shape==(N,2)
    x=x.astype(float)/2**31;assert np.isfinite(x).all() and np.abs(x).max()<1
    # Períodos de inicio de ciclo medidos en la partitura.
    periods={};onsets={}
    for name,start,expected in [('piano',45,15),('bajo',65,17)]:
        ev=P[name]
        first={}
        for e in ev:first.setdefault(e['ciclo'],e)
        seq=[e for e in first.values() if start<e['t']<145]
        diff=np.diff([e['tick'] for e in seq]);assert np.all(diff==expected),(name,diff)
        periods[name]={'subdivisiones':expected,'segundos':expected*TICK,'ciclos_comprobados':len(diff)}
        # Comprobar señal del stem en cada ataque escrito, descontando la cola anterior.
        y=read(out,name);hits=[]
        for e in seq:
            a=int(e['t']*SR);pre=np.sqrt(np.mean(y[max(0,a-1200):a]**2));post=np.sqrt(np.mean(y[a:a+2400]**2));hits.append(float(20*np.log10((post+1e-10)/(pre+1e-10))))
        onsets[name]={'ataques':len(hits),'subida_mediana_dB':float(np.median(hits))}
    assert P['encuentros_ticks'] and all(t in {e['tick'] for e in P['piano']} and t in {e['tick'] for e in P['bajo']} for t in P['encuentros_ticks'])
    gif=next(out.glob('*.gif'));im=Image.open(gif);total=0
    contact=Image.new('RGB',(1200,1260),BG)
    for i in range(im.n_frames):
        im.seek(i);total+=im.info['duration'];contact.paste(im.convert('RGB').resize((600,315)),((i%2)*600,(i//2)*315))
    assert im.n_frames==3 and total<=10000 and gif.stat().st_size<=15*1024**2
    tag=out.name.split('-')[-1];png(out/'proceso'/f'04-revision-gif-s{SEED}-{tag}.png',contact.crop((0,0,1200,630)))
    for p in out.rglob('*.png'):
        with Image.open(p) as im:im.verify()
    assert Image.open(out/'og.png').size==(1200,630)
    # Altura orientativa sobre el cuerpo de las últimas sílabas largas, fuera de consonantes.
    y=read(out,'voz').mean(axis=1);errs=[]
    for phrase in P['frases']:
        e=phrase['eventos'][-1];f0=440*2**((e['nota']-69)/12);seg=y[int((e['t']+.30)*SR):int((e['t']+.62)*SR)][::3].astype(float);seg-=seg.mean()
        ac=correlate(seg,seg,mode='full',method='fft')[len(seg)-1:];lo=int(16000/(f0*1.35));hi=int(16000/(f0*.75));peaks,_=find_peaks(ac[lo:hi])
        if len(peaks):
            j=lo+peaks[np.argmax(ac[lo:hi][peaks])];delta=.5*(ac[j-1]-ac[j+1])/(ac[j-1]-2*ac[j]+ac[j+1]);cents=1200*np.log2(16000/(j+delta)/f0);errs.append(float(cents))
    result={'duracion_s':N/SR,'pico_dBFS':float(20*np.log10(np.abs(x).max())),'periodos':periods,'onsets':onsets,'encuentros':len(P['encuentros_ticks']),
      'patron_final_subdivisiones':P['patron_final'],'afinacion_silabas_largas_mediana_abs_cents':float(np.median(np.abs(errs))),
      'nota_afinacion':'Autocorrelación local orientativa; no sustituye escucha humana.', 'gif':{'frames':3,'segundos':total/1000,'bytes':gif.stat().st_size}}
    savejson(out/'verificacion.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=1),flush=True)

if __name__=='__main__':
    command=sys.argv[1]
    if command=='preparar':prepare()
    else:{'trio':trio,'mezcla':mezcla,'verificar':verify}[command](Path(sys.argv[2]).resolve())
