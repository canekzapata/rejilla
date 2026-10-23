"""Lo que no sonó: preparar → voz.cjs <carpeta> → audio <carpeta> → verificar.
Toda salida se crea con exclusión. El coro se escribe en frecuencia, antes de sonar.
"""
import hashlib, importlib.util, json, math, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, resample_poly, stft

BASE=Path(__file__).resolve().parent
SEED=20261015; SR=48000; BEAT=.625; BAR=2.5; DURATION=186
BG=(16,24,31); FG=(237,233,216); CYAN=(110,224,211); ROSE=(247,133,153)
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/consola.ttf',n)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jsave(p,obj):
    with Path(p).open('x',encoding='utf8') as f:json.dump(obj,f,ensure_ascii=False,indent=2)
def png(p,im):
    with Path(p).open('xb') as f:im.save(f,'PNG')
def wav(p,x,sr=SR):
    with Path(p).open('xb') as f:wavfile.write(f,sr,np.asarray(x,dtype=np.float32))
def run(args):return subprocess.run(args,check=True,capture_output=True,text=True)
def card(title,sub):
    im=Image.new('RGB',(1200,630),BG);d=ImageDraw.Draw(im)
    d.text((44,24),'LO QUE NO SONÓ',font=font(34),fill=FG)
    d.text((44,72),title,font=font(20),fill=CYAN)
    d.text((44,592),sub,font=font(15),fill=FG)
    return im,d
def plot_plan(events,alternatives=False):
    im,d=card('01 / elegir deja un rastro','72 compases · 96 BPM · semilla 20261015 · Canek Zapata')
    for m in range(48,85,6):
        y=540-(m-48)*10;d.line((44,y,1150,y),fill=(39,50,58));d.text((8,y-7),str(m),font=font(12),fill=FG)
    for e in events:
        x=44+e['t']/186*1100;y=540-(e['nota']-48)*10
        if alternatives:
            for a in e['alternativas']:
                yy=540-(a['nota']-48)*10;d.line((x,yy,x+max(3,a['dur']*5.9),yy),fill=ROSE,width=1)
        d.line((x,y,x+e['dur']*5.9,y),fill=CYAN,width=3)
    for t,label in [(0,'íntimo'),(40,'acumular'),(100,'invertir'),(160,'soltar')]:
        x=44+t/186*1100;d.text((x,110),label,font=font(14),fill=FG);d.line((x,140,x,560),fill=(55,65,72))
    return im

def preparar():
    rng=np.random.default_rng(SEED);events=[]
    motifs=[[64,67,71,69,67,64],[64,66,69,71,74,71],[62,66,69,72,71,66],[60,64,67,71,69,67]]
    for b in range(68):
        times=[.0,1.5,2.75] if b%4!=3 else [0,2]
        if b<4:times=[0,2]
        for k,pos in enumerate(times):
            n=motifs[(b//4)%4][(b+k*2)%6]
            if b>=40:n+=12 if b%7==0 else 0
            dur=(.58 if k<len(times)-1 else .80)*BEAT
            gap=((times[k+1]-pos)*BEAT-dur) if k<len(times)-1 else (4-pos)*BEAT-dur
            candidates=[n-5,n-2,n,n+2,n+5];p=np.array([.12,.21,.36,.20,.11])
            p*=rng.uniform(.8,1.2,5);p/=p.sum()
            alt=[]
            for j in sorted([0,1,3,4],key=lambda j:-p[j])[:2]:
                alt.append({'nota':candidates[j],'prob':float(p[j]),'pan':float(np.clip((candidates[j]-n)/6,-.85,.85)),
                            'dur':float(3+max(0,gap)*5+(b/68)*6)})
            events.append({'t':b*BAR+pos*BEAT,'dur':dur,'nota':n,'compas':b,'alternativas':alt})
    lines=[(8,'de jé u na sí la ba a fue ra'),(16,'la puer ta si guió vi bran do'),
      (24,'di je la fra se más cor ta'),(32,'lo de más si guió can tan do'),
      (42,'tam bién pu de de cir es to'),(50,'tam bién pu de de cir es to'),
      (58,'en el hue co de mi bo ca'),(66,'o tra voz en con tró si tio'),
      (78,'u na pa la bra por o tra'),(86,'u na ven ta na en cen di da'),
      (94,'lo que a par té del ca mi no'),(103,'ya co no ce la sa li da'),
      (113,'tam bién pu de de cir es to'),(121,'tam bién pu de de cir es to'),
      (130,'ca da si len cio que de jo'),(138,'tie ne tu res pi ra ción'),
      (149,'a ho ra lo di ces tú'),(156,'a ho ra lo di ces tú'),
      (162,'yo me que do en la o ri lla'),(168,'tú ter mi nas la can ción')]
    frases=[]
    for i,(t,line) in enumerate(lines):
        words=line.split();ev=[]
        for k,s in enumerate(words):
            ti=t+k*.44;near=min(events,key=lambda e:abs(e['t']-ti));note=near['nota']-12
            if 100<=t<160:note=near['alternativas'][i%2]['nota'] # el coro toma la altura descartada
            ev.append({'t':ti,'dur':.44 if k<len(words)-1 else 1.15,'texto':s,'nota':note})
        frases.append({'eventos':ev,'nivel':.8 if t<100 else .65,'pan':0 if t<100 else (-.28 if i%2 else .28)})
    im=plot_plan(events,True);nonce=os.urandom(24).hex()
    h=hashlib.sha256(im.tobytes()+Path(__file__).read_bytes()+(BASE/'voz.cjs').read_bytes()+nonce.encode()).hexdigest();tag=h[:12]
    out=BASE/f'lo-que-no-sono-s{SEED}-{tag}';out.mkdir(exist_ok=False)
    (out/'proceso').mkdir();(out/'render').mkdir()
    plan={'semilla':SEED,'duracion':DURATION,'bpm':96,'eventos':events,'frases':frases,
          'final':{'nota':events[0]['alternativas'][0]['nota'],'t':173,'dur':12}}
    jsave(out/'partitura.json',plan)
    png(out/'proceso'/f'01-decisiones-s{SEED}-{tag}.png',im)
    jsave(out/'receta-inicial.json',{'id':h,'nonce':nonce,'semilla':SEED,'programa_sha256':sha(__file__),
          'voz_js_sha256':sha(BASE/'voz.cjs'),'imagen_inicial_sha256':sha(next((out/'proceso').glob('*.png'))),
          'banco_sha256':sha(BASE.parent/'inferencia/vendor/difonos/bancos/sabina-1-b44e7fab5cee/banco.flac'),
          'runtime_sha256':sha(BASE.parent/'inferencia/vendor/difonos/runtime/difonos.js')})
    print(out,flush=True)

def hp(x,f):return sosfilt(butter(2,f,'high',fs=SR,output='sos'),x,axis=0).astype(np.float32)
def db(x):return float(20*np.log10(np.sqrt(np.mean(np.asarray(x,dtype=float)**2))+1e-10))
def spectral(out,P):
    spec=importlib.util.spec_from_file_location('rejilla_modal',BASE.parent/'musica.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
    M.S=16384;M.H=16384;M.N=32768;M.T=2.;M.F=.5;M.R=2048
    track=M.Pista('descartes',93);live=[];used=[]
    # Una alternativa cada 1.25 s. Máximo ocho vivas; el límite corta con release, no en seco.
    for idx,e in enumerate(P['eventos']):
        if idx%2:continue
        t=e['t']+.35
        if t>=168:continue
        a=e['alternativas'][(idx//2)%2];level=np.interp(t,[0,40,100,145,168],[.02,.07,.35,.48,.18])
        end=min(t+a['dur'],172.)
        live=[x for x in live if x>t]
        if len(live)>=8:continue
        live.append(end)
        f=440*2**((a['nota']-69)/12);amp=level*float(np.sqrt(a['prob']))
        for mul,gain in [(1,1),(2,.27),(3,.10)]:
            track.modo(f*mul,amp*gain,t,.06,ataque=1.8,suelta=end-t,ar=3.5,pan=a['pan'],fase=(idx*.71)%6.28)
        used.append({'t':t,'fin':end,'nota':a['nota'],'prob':a['prob'],'pan':a['pan'],'nivel':amp})
    f=440*2**((P['final']['nota']-69)/12)
    track.modo(f,.18,173,.12,ataque=2.8,suelta=10,ar=2.5,pan=-.3,fase=0)
    print('coro: escribiendo coeficientes',len(used),'alternativas',flush=True)
    L,R=track.escribir();mag,phase,scale=M.a_imagen(L,R)
    tag=out.name.split('-')[-1]
    # Vista real de la imagen de magnitud, reducida a escala logarítmica para leerla.
    bins=np.clip(np.round(np.geomspace(80,6000,340)/M.F).astype(int),1,M.H-1)
    view=np.abs(L[:,bins])+np.abs(R[:,bins]);view=np.log1p(view*700);view/=max(view.max(),1e-9)
    im,d=card('02 / las alternativas aprenden a ocupar el tiempo','Magnitud real de la partitura espectral · 80 Hz–6 kHz · FFmpeg spectrumsynth')
    pix=np.zeros((340,93,3),dtype=np.uint8)
    for c,v in enumerate(ROSE):pix[:,:,c]=(view.T[::-1]*v).astype(np.uint8)
    im.paste(Image.fromarray(pix).resize((1100,420)),(44,140))
    png(out/'proceso'/f'02-memoria-espectral-s{SEED}-{tag}.png',im)
    jsave(out/'memoria.json',used)
    for name,data in [('magnitud',mag),('fase',phase)]:
        with (out/'render'/f'{name}.raw').open('xb') as fh:data.tofile(fh)
    inp=lambda name:['-f','rawvideo','-pix_fmt','gray16le','-s',f'93x{M.H*2}','-r','1','-i',str(out/'render'/f'{name}.raw')]
    run(['ffmpeg','-hide_banner','-loglevel','error','-n',*inp('magnitud'),*inp('fase'),'-filter_complex',
      '[0]setpts=N/TB,format=gray16le[m];[1]setpts=N/TB,format=gray16le[p];[m][p]spectrumsynth=sample_rate=16384:channels=2:scale=lin:slide=fullframe:win_func=rect:overlap=0',
      '-c:a','pcm_f32le',str(out/'render/coro-espectral.wav')])
    sr,x=wavfile.read(out/'render/coro-espectral.wav')
    y=track.tiempo(104,108,0);actual=x[104*sr:108*sr,0]*scale
    snr=float(20*np.log10(np.linalg.norm(y)/max(np.linalg.norm(actual-y),1e-12)))
    print('comprobación analítica del coro:',round(snr,1),'dB SNR',flush=True)
    assert snr>35,('lectura espectral incorrecta',snr)
    jsave(out/'prueba-espectral.json',{'fragmento_s':[104,108],'SNR_dB':snr,'escala_imagen':float(scale),'sample_rate':sr,'filas_por_canal':M.H})
    return resample_poly(x*scale,375,128).astype(np.float32),view

def accompaniment(P):
    rng=np.random.default_rng(SEED);n=int(DURATION*SR)
    keys=np.zeros((n,2),np.float32);bass=keys.copy();drums=keys.copy()
    def add(bus,t,dur,note,amp,kind='key',pan=0):
        start=int(round(t*SR));nn=min(int((dur+1)*SR),n-start)
        if nn<=0:return
        tt=np.arange(nn)/SR;f=440*2**((note-69)/12)
        if kind=='key':
            env=(1-np.exp(-tt*220))*np.exp(-tt/1.5)*np.exp(-np.maximum(tt-dur,0)*8)
            y=np.sin(2*np.pi*f*tt+1.8*np.exp(-tt*5)*np.sin(2*np.pi*f*tt))+.16*np.sin(4*np.pi*f*tt)
        elif kind=='bass':
            env=(1-np.exp(-tt*130))*np.exp(-tt*.8)*np.exp(-np.maximum(tt-dur,0)*22)
            y=np.sin(2*np.pi*f*tt)+.23*np.sin(4*np.pi*f*tt)+.08*np.sin(6*np.pi*f*tt)
        elif kind=='kick':
            env=(1-np.exp(-tt*1100))*np.exp(-tt*15);y=np.sin(2*np.pi*(49*tt+7*(1-np.exp(-tt*26))))
        else:
            env=(1-np.exp(-tt*2500))*np.exp(-tt*(80 if kind=='hat' else 33));y=rng.normal(0,.6,nn)
            y=np.r_[0,np.diff(y)] if kind=='hat' else y+.35*np.sin(2*np.pi*187*tt)
        y=(y*env*amp).astype(np.float32)
        bus[start:start+nn,0]+=y*math.cos((pan+1)*math.pi/4)
        bus[start:start+nn,1]+=y*math.sin((pan+1)*math.pi/4)
    roots=[40,36,43,38];chords=[[55,59,62,66],[55,59,64,67],[54,59,62,69],[54,57,60,64]]
    for b in range(68):
        t=b*BAR;intensity=float(np.interp(t,[0,40,95,110,155,170],[.6,.75,.9,.40,.22,0]))
        if t<160:
            add(bass,t,1.25,roots[(b//2)%4],.30*intensity,'bass')
            if b>7:add(bass,t+1.875,.35,roots[(b//2)%4]+7,.15*intensity,'bass')
            for j,m in enumerate(chords[(b//2)%4]):
                if b%2==0:add(keys,t+j*.028,1.65,m,.065*intensity,'key',(j-1.5)*.28)
            for pos in ([0,1.75] if b<16 else [0,1.5,2.125]):add(drums,t+pos,.2,36,.34*intensity,'kick')
            for pos in [.625,1.875]:add(drums,t+pos,.15,36,.12*intensity,'snare',.15)
            for k in range(8):
                if b<8 and k%2:continue
                add(drums,t+k*.3125+(.025 if k%2 else 0),.08,36,.035*intensity,'hat',-.35)
    for e in P['eventos']:
        t=e['t'];amp=float(np.interp(t,[0,40,100,145,171],[.105,.095,.075,.03,0]))
        add(keys,t,e['dur'],e['nota'],amp,'key',.12)
    return keys,bass,hp(drums,35)

def audio(out):
    P=json.loads((out/'partitura.json').read_text(encoding='utf8'));tag=out.name.split('-')[-1]
    chorus,_=spectral(out,P);print('acompañamiento',flush=True)
    keys,bass,drums=accompaniment(P)
    sr,voice=wavfile.read(out/'render/voz.wav');assert sr==SR and len(voice)==int(DURATION*SR)
    voice=hp(voice,125);chorus=hp(chorus,110)
    # Ecualización suave: reserva el centro para las palabras.
    chorus=sosfilt(butter(2,4200,'low',fs=SR,output='sos'),chorus,axis=0).astype(np.float32)
    times=np.arange(len(voice))/SR
    # El coro respira por oleadas de tres corcheas mientras la base conserva cuatro tiempos.
    movement=np.interp(times,[0,40,100,110,157,171,173],[0,0,.1,.25,.30,0,0])
    chorus*=((1-movement)+movement*(.5+.5*np.sin(2*np.pi*times/(BEAT*1.5))))[:,None]
    # A partir de 172 s sólo queda la alternativa inicial: corte fundido de base y voz.
    end=np.clip((173-times)/1.5,0,1).astype(np.float32)[:,None]
    keys*=end;bass*=end;drums*=end;voice*=end
    # Nivel de voz por frase, medido sobre su ventana; la inversión conserva inteligibilidad.
    rest=keys+bass+drums+chorus
    gains=[]
    for frase in P['frases']:
        a=max(0,int((frase['eventos'][0]['t']-.15)*SR));b=int((frase['eventos'][-1]['t']+1.6)*SR)
        vr=db(voice[a:b]);rr=db(rest[a:b]);g=float(np.clip(10**((rr-vr+1.5)/20),.5,9))
        env=np.ones(b-a,np.float32)*g;edge=min(int(.12*SR),(b-a)//2)
        env[:edge]=np.linspace(1,g,edge);env[-edge:]=np.linspace(g,1,edge);voice[a:b]*=env[:,None]
        gains.append({'t':frase['eventos'][0]['t'],'ganancia':g,'voz_sobre_resto_dB':round(db(voice[a:b])-rr,2)})
    mix=rest+voice
    # Espacio corto con taps filtrados; el final no recibe ecos de otras voces.
    wet=keys*.17+chorus*.25+voice*.09
    wet=sosfilt(butter(2,2700,'low',fs=SR,output='sos'),wet,axis=0).astype(np.float32)
    for delay,g in [(.093,.32),(.171,.22),(.283,.16),(.419,.10)]:
        k=int(delay*SR);mix[k:]+=wet[:-k,::-1]*g
    mix=hp(mix,29);mix*=np.clip((186-times)/2,0,1)[:,None]
    peak=float(np.abs(mix).max());mix*=.9/max(peak,.9)
    wav(out/'render/mezcla-previa.wav',mix)
    for name,x in [('teclas',keys),('bajo',bass),('percusion',drums),('coro',chorus),('voz-mezcla',voice)]:wav(out/'render'/f'{name}.wav',x)
    terminar(out,mix,keys,bass,drums,chorus,voice,gains,peak)

def terminar(out,mix=None,keys=None,bass=None,drums=None,chorus=None,voice=None,gains=None,peak=None):
    tag=out.name.split('-')[-1]
    if mix is None:
        read=lambda name:wavfile.read(out/'render'/f'{name}.wav')[1]
        mix,keys,bass,drums,chorus,voice=map(read,['mezcla-previa','teclas','bajo','percusion','coro','voz-mezcla'])
        P=json.loads((out/'partitura.json').read_text(encoding='utf8'));gains=[];rest=keys+bass+drums+chorus
        for frase in P['frases']:
            a=max(0,int((frase['eventos'][0]['t']-.15)*SR));b=int((frase['eventos'][-1]['t']+1.6)*SR)
            gains.append({'t':frase['eventos'][0]['t'],'voz_sobre_resto_dB':round(db(voice[a:b])-db(rest[a:b]),2)})
    # Dos pasadas para conservar la forma dinámica y controlar el pico real.
    first=run(['ffmpeg','-hide_banner','-nostats','-i',str(out/'render/mezcla-previa.wav'),'-af','loudnorm=I=-15:TP=-1.5:LRA=11:print_format=json','-f','null','-'])
    report=json.JSONDecoder().raw_decode(first.stderr[first.stderr.rfind('{'):])[0];jsave(out/'normalizacion.json',report)
    filt='loudnorm=I=-15:TP=-1.5:LRA=11:linear=true:'+':'.join(f'{a}={report[b]}' for a,b in [('measured_I','input_i'),('measured_TP','input_tp'),('measured_LRA','input_lra'),('measured_thresh','input_thresh'),('offset','target_offset')])
    name=f'lo-que-no-sono-s{SEED}-{tag}'
    run(['ffmpeg','-hide_banner','-loglevel','error','-n','-i',str(out/'render/mezcla-previa.wav'),'-af',filt,'-ar','48000','-c:a','pcm_s24le',str(out/f'{name}.wav')])
    run(['ffmpeg','-hide_banner','-loglevel','error','-n','-i',str(out/f'{name}.wav'),'-c:a','aac','-b:a','224k','-metadata','title=Lo que no sonó','-metadata','artist=Canek Zapata',str(out/f'{name}.m4a')])
    stats=run(['ffmpeg','-hide_banner','-nostats','-i',str(out/f'{name}.m4a'),'-af','loudnorm=I=-15:TP=-1.5:LRA=11:print_format=json','-f','null','-'])
    measured=json.JSONDecoder().raw_decode(stats.stderr[stats.stderr.rfind('{'):])[0]
    # Espectrograma de la mezcla real para el tercer avance.
    freqs,ts,Z=stft(mix.mean(axis=1),fs=SR,nperseg=4096,noverlap=1024)
    bins=np.searchsorted(freqs,np.geomspace(70,10000,340));v=20*np.log10(np.abs(Z[bins])+1e-8);v=np.clip((v-v.max()+65)/65,0,1)
    pixels=np.zeros((340,v.shape[1],3),np.uint8)
    for c in range(3):pixels[:,:,c]=(v[::-1]*CYAN[c]).astype(np.uint8)
    im,d=card('03 / mezcla: la voz cede el primer plano','Espectrograma de audio real · íntimo → acumulación → inversión → una alternativa sola')
    im.paste(Image.fromarray(pixels).resize((1100,420)),(44,140));png(out/'proceso'/f'03-mezcla-s{SEED}-{tag}.png',im)
    png(out/f'resultado-s{SEED}-{tag}.png',im);png(out/'og.png',im)
    frames=[Image.open(p).convert('RGB') for p in sorted((out/'proceso').glob('*.png'))]
    gif=out/f'proceso-lo-que-no-sono-s{SEED}-{tag}.gif'
    with gif.open('xb') as f:frames[0].save(f,format='GIF',save_all=True,append_images=frames[1:],duration=[2400,2400,2400],loop=0,optimize=True)
    measures={'aac_loudness':measured,'voz_por_frase':gains,'duracion_s':DURATION,'mezcla_pico_antes_normalizar':peak,
      'coro_frente_a_base_dB':{label:round(db(chorus[int(a*SR):int(b*SR)])-db((keys+bass+drums)[int(a*SR):int(b*SR)]),1) for label,a,b in [('intimo',8,38),('acumular',42,98),('invertir',105,155)]}}
    jsave(out/'medidas.json',measures)
    recipe=json.loads((out/'receta-inicial.json').read_text(encoding='utf8'))
    recipe.update({'FFmpeg':run(['ffmpeg','-version']).stdout.splitlines()[0], 'archivos_sha256':{str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and 'render' not in p.parts},
      'sintesis':'Coro: imagen analítica → spectrumsynth. Base: Python FM/modal. Voz: Difonos PSOLA, Web Audio offline.',
      'modulo_modal_sha256':sha(BASE.parent/'musica.py'),'gif':{'fotogramas':3,'duracion_s':7.2,'bytes':gif.stat().st_size}})
    jsave(out/'receta.json',recipe)
    with (out/'proceso/README.md').open('x',encoding='utf8') as f:
        f.write('# Etapas reales de producción\n\n01: decisiones y alternativas, guardadas antes de sintetizar.\n02: magnitud de la partitura del coro, guardada antes de que FFmpeg la toque.\n03: espectrograma de la mezcla terminada.\n\nEl GIF reúne estas tres etapas; no es una animación del interior del sintetizador.\nSemilla 20261015. El identificador de ejecución, nonce y hashes están en receta.json.\nLos PNGs llevan número, descripción, semilla e identificador. Ninguna salida existente se sustituye.\n')
    print(json.dumps(measures,ensure_ascii=False,indent=1),flush=True)
    print('ENTREGA',out,flush=True)

if __name__=='__main__':
    if sys.argv[1]=='preparar':preparar()
    elif sys.argv[1]=='audio':audio(Path(sys.argv[2]).resolve())
    elif sys.argv[1]=='terminar':terminar(Path(sys.argv[2]).resolve())
