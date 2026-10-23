"""Canción pop con los motores físicos de objetos/: preparar, proceso-instrumentos, mezclar, verificar.
Todos los destinos de ejecución son exclusivos. No modifica ni sustituye motores o entregas anteriores.
"""
import hashlib,json,math,os,subprocess,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.io import wavfile
from scipy.signal import butter,sosfilt,stft,correlate,find_peaks
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parent
SR=48000;BPM=112;BEAT=60/BPM;BAR=4*BEAT;SEED=171015;DUR=88*BAR+5;N=math.ceil(DUR*SR)
BG=(22,23,37);FG=(239,234,215);LIME=(197,224,109);PINK=(240,143,179);CYAN=(109,211,216)
FONT=lambda n:ImageFont.truetype('C:/Windows/Fonts/consola.ttf',n)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):
    with Path(p).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
def txt(p,s):
    with Path(p).open('x',encoding='utf8') as f:f.write(s)
def png(p,im):
    with Path(p).open('xb') as f:im.save(f,'PNG')
def wav(p,x):
    with Path(p).open('xb') as f:wavfile.write(f,SR,np.asarray(x,np.float32))
def cmd(args):return subprocess.run(args,check=True,capture_output=True,text=True,encoding='utf8',errors='replace')
def db(x):return float(10*np.log10(np.mean(np.asarray(x,dtype=float)**2)+1e-14))
def filt(x,lo=None,hi=None):
    mode='band' if lo and hi else 'high' if lo else 'low';freq=[lo,hi] if lo and hi else lo or hi
    return sosfilt(butter(2,freq,mode,fs=SR,output='sos'),x,axis=0).astype(np.float32)
def card(title,sub):
    im=Image.new('RGB',(1200,630),BG);d=ImageDraw.Draw(im)
    d.text((32,20),'LA SALIDA CAMBIA DE LUGAR',font=FONT(31),fill=FG)
    d.text((32,65),title,font=FONT(18),fill=LIME);d.text((32,600),sub,font=FONT(13),fill=FG)
    return im,d
def transform(ch,op):
    r,major=ch
    return ((r+(4 if major else -4))%12,not major) if op=='L' else ((r+(-3 if major else 3))%12,not major) if op=='R' else (r,not major)
def triad(ch):return sorted([ch[0],(ch[0]+(4 if ch[1] else 3))%12,(ch[0]+7)%12])
def score_image(P):
    im,d=card('01 / forma pop, caminos que se bifurcan','Partitura antes de renderizar · 112 BPM · semilla 171015 · Canek Zapata')
    for i,s in enumerate(P['secciones']):
        x=32+s['a']/DUR*1134;w=(s['b']-s['a'])/DUR*1134
        d.rectangle((x,110,x+w-2,157),fill=[(70,84,72),(75,58,85),(50,79,95)][i%3]);d.text((x+3,119),s['corto'],font=FONT(13),fill=FG)
    for i,name in enumerate(['piano','bajo','viento','clarinete','cuerdas','metal','vozagua','agua','pajaro','waterphone','gong','tambor']):
        y=182+i*30;d.text((32,y),name,font=FONT(12),fill=FG)
        for e in P['instrumentos'][name]:
            x=145+e['t']/DUR*1020;w=max(2,e.get('dur',.18)/DUR*1020)
            d.rectangle((x,y+3,x+w,y+13),fill=[LIME,PINK,CYAN][i%3])
    return im

def prepare():
    rng=np.random.default_rng(SEED)
    form=[('intro','I',4),('verso 1','V1',16),('pre 1','P1',4),('coro 1','C1',8),('post','X',4),('verso 2','V2',16),('pre 2','P2',4),('coro 2','C2',8),('puente','B',8),('coro final','CF',12),('outro','O',4)]
    sections=[];bars=[];b=0;ch=(9,False);walk=[]
    # Recorrido sembrado: cada arista P/R/L conserva dos clases de altura; el segundo verso desanda otro tramo.
    for k in range(160):
        op=str(rng.choice(['P','R','L']));nxt=transform(ch,op);assert len(set(triad(ch))&set(triad(nxt)))==2
        walk.append({'desde':list(ch),'op':op,'hasta':list(nxt)});ch=nxt
    cursor=0
    for name,short,count in form:
        sections.append({'nombre':name,'corto':short,'compas':b,'n':count,'a':b*BAR,'b':(b+count)*BAR})
        for j in range(count):
            if name.startswith('coro'):chord=[(9,False),(5,True),(2,False),(4,True)][(j//2)%4]
            elif name.startswith('pre'):chord=[(2,False),(5,False),(4,False),(4,True)][j]
            elif name=='intro' or name=='outro':chord=(9,False)
            else:
                ix=cursor if name!='verso 2' else 65-cursor%32
                chord=tuple(walk[ix%len(walk)]['hasta']);cursor+=1
            bars.append({'b':b+j,'sec':name,'j':j,'acorde':list(chord)})
        b+=count
    instruments={name:[] for name in ['piano','bajo','cuerdas','clarinete','agua','vozagua','waterphone','tambor','metal','pajaro','gong','viento']}
    def add(name,t,m=None,dur=.3,v=.7,**kw):
        e={'t':float(t),'dur':float(dur),'v':float(v),**kw}
        if m is not None:e['m']=float(m)
        instruments[name].append(e)
    preparations=[{'t':0,'de':'normal','a':'papel','dur':16*BAR},{'t':20*BAR,'de':'papel','a':'moneda','dur':4*BAR},
       {'t':32*BAR,'de':'moneda','a':'goma','dur':8*BAR},{'t':48*BAR,'de':'goma','a':'tornillo','dur':8*BAR},
       {'t':64*BAR,'de':'tornillo','a':'tornillo_suelto','dur':8*BAR},{'t':72*BAR,'de':'tornillo_suelto','a':'normal','dur':12*BAR}]
    for row in bars:
        b=row['b'];t=b*BAR;sec=row['sec'];j=row['j'];ch=tuple(row['acorde']);root=ch[0];notes=triad(ch);chorus=sec.startswith('coro');verse=sec.startswith('verso');pre=sec.startswith('pre');bridge=sec=='puente'
        # Piano preparado: una voz común queda fija; las otras se abren, con desplazamientos de tres corcheas.
        for k,pos in enumerate([0,1.5,3,5.5,7]):
            if sec=='intro' and j<2 and k>1:continue
            if sec=='outro' and k>1:continue
            pcs=notes if k in [0,3] else [notes[(k+j)%3]]
            for q,pc in enumerate(pcs):
                add('piano',t+pos*BEAT/2+q*.009,48+((pc-0)%12)+(12 if k==2 else 0),.32 if k else .8,.48 if chorus else .58,tipo='martillo' if k%2==0 else 'apagada')
        # Bajo acústico → house entre pre y coro, regresando por otra curva.
        house=float(np.interp(b,[0,18,24,32,40,54,60,64,70,76,84,88],[0,0,1,.85,.12,.3,1,.95,.1,1,.7,.1]))
        if sec!='intro' or j>=2:
            positions=[0,1.5,2.5,3.25] if chorus else [0,1.75,3]
            for k,pos in enumerate(positions):add('bajo',t+pos*BEAT,33+((root-9)%12)+([0,12,7,12][k] if chorus else [0,7,12][k]),.31 if chorus else .42,.8,tipo='pizz',casa=house)
        # Tambor: la misma membrana da bombo, apagados y borde; golpes de habla contestan la letra.
        if sec not in ['intro','outro']:
            for pos,tipo,v in [(0,'centro',.85),(1,'apagado',.48),(1.75,'palo',.25),(2,'centro',.72),(3,'borde',.65)]:
                if bridge and pos not in [0,3]:continue
                add('tambor',t+pos*BEAT,38 if tipo=='centro' else 45,.2,v,tipo=tipo,curva=[[0,0],[.1,2 if j%4==3 else 0],[.25,0]])
            if j%8==7:add('tambor',t+2.5*BEAT,43,.16,.55,tipo='habla',texto='¿dónde está?',alto=3)
        if j%2==0 and sec!='outro':
            add('agua',t+BEAT*.5,72+(notes[j%3]%12),.22,.5,tipo='guiro',n=10,sube=j%4==0)
        if pre or sec=='post':add('agua',t+BEAT*2,79,.55,.42,tipo='palo')
        if bridge and j in [0,4]:add('agua',t,None,2*BAR,.35,tipo='ola')
        # Contrapunto: el viento cuenta una ruta armónica lateral, a tres corcheas, dentro de su rango medido.
        if verse or pre or sec=='post' or chorus and j%2==1:
            lateral=tuple(walk[(b*3)%len(walk)]['hasta']);pcs=triad(lateral)
            for k,pos in enumerate([.25,1.75,3.25]):
                m=52+((pcs[k]-4)%12)
                de,a=('saxofon','flauta') if b<36 else ('flauta','golpe') if b<64 else ('golpe','saxofon')
                add('viento',t+pos*BEAT,m,.48 if chorus else .62,.6,de=de,a=a)
        # Clarinete bajo: respuestas, llaves, subtono y multifónico en la bifurcación.
        if verse and j%2==1 or bridge:
            m=38+((root-2)%12)
            add('clarinete',t+2*BEAT,m,.8,.62,tipo='multifonico' if bridge and j%3==0 else 'subtono' if j%4==1 else 'normal')
            add('clarinete',t+3.5*BEAT,m+7,.08,.65,tipo='llaves' if j%3 else 'slap')
        # Arco → ponticello → pizz house: personajes contrapuntísticos, sin un pad fijo.
        if pre or chorus or bridge:
            m=60+notes[(j+1)%3]
            add('cuerdas',t+BEAT*.75,m,1.25 if pre else .9,.56,tipo='ponticello' if bridge else 'tasto' if pre else 'pizz',casa=.7 if chorus else 0)
        if chorus:
            for k,pos in enumerate([.5,2.75]):add('metal',t+pos*BEAT,45+((root-9)%12)+[7,12][k],.18 if k==0 else .38,.68,tipo='lengua' if k==0 else 'growl')
        if (verse and j in [3,11]) or (bridge and j%2==0) or sec=='post':
            add('pajaro',t+2.75*BEAT,81+notes[j%3],.24,.5,tipo='trino' if bridge else 'silbido',m2=84+notes[(j+1)%3],rate=14+j)
        if (pre and j==2) or bridge and j in [1,5]:add('waterphone',t,None,2.3,.5,tipo='arco',vara=(b*7)%24,agua=2.3,ola=.47)
        if chorus and j==0:add('gong',t,57,.3,.42,tipo='cruce',abre=4)
        if bridge and j==6:add('gong',t,45,2,.35,tipo='arco')
    # Agua cantada: contesta al estribillo y lo dobla en el final con dos vocales simultáneas.
    chorus_mel=[64,64,67,69,67,65,64,62,60,62,64]
    chorus_text=['la sa li da cam bia de lu gar','ca da vez que te vuel vo a mi rar','si me pier do den tro de tu voz','vuel ve a a brir me la mis ma can ción']
    verses=[['a brí la puer ta de siem pre','del o tro la do ha bí a mar','el mar co guar da ba mi som bra','mi som bra que rí a pa sar'],
            ['un pá ja ro cru za el te cho','re gre sa he cho de me tal','le di de be ber a mi nom bre','el a gua lo em pe zó a con tar']]
    phrases=[];hooks=[]
    def phrase(t,line,hook=False,rise=False,ending=False):
        syll=line.split();ev=[];pos=0.;mel=chorus_mel if hook else [57,60,59,62,64,62,60,59,57,55,57,59]
        for k,s in enumerate(syll):
            delta=([.5,.5,.75,.5,.5,.75,.5,.5,.5,.75,.5,.5][k%12] if hook else [.75,.5,.75,.5,.75,.75,.5,.75,.5,.75,.5,.5][k%12])*BEAT
            duration=delta+.025 if k<len(syll)-1 else (.9 if not ending else 1.5)
            note=mel[k%len(mel)]+(2 if rise and k>len(syll)//2 else 0)
            ev.append({'t':t+pos,'dur':duration,'texto':s,'nota':note});pos+=delta
        phrases.append({'eventos':ev,'nivel':.7,'pan':0,'hook':hook,'texto':line})
        if hook:hooks.append([{'dt':round(e['t']-t,7),'dur':e['dur'],'nota':e['nota'],'texto':e['texto']} for e in ev])
    for s in sections:
        name=s['nombre'];start=s['a']
        if name.startswith('verso'):
            for k,line in enumerate(verses[0 if name=='verso 1' else 1]):phrase(start+k*4*BAR+.25*BEAT,line)
        elif name.startswith('pre'):
            for k,line in enumerate(['no sé quién mue ve las pa re des','cuan do ter mi no de can tar' if name=='pre 1' else 'ya las es cu cho res pi rar']):phrase(start+k*2*BAR,line,rise=True)
        elif name.startswith('coro'):
            for k,line in enumerate(chorus_text):phrase(start+k*2*BAR,line,True)
            if name=='coro final':
                phrase(start+8*BAR,chorus_text[0],True);phrase(start+10*BAR,'yo te en cuen tro cam bian do de voz',False,ending=True)
            for k,word in enumerate(['salida','lugar','voz','canción']):
                add('vozagua',start+(k*2+1.25)*BAR,None,.7,.5,texto=word,nota=[60,57,62,64][k],modo='canto',voz=1,doble='i' if name=='coro final' else None)
        elif name=='puente':
            for k,line in enumerate(['a pren dí de me mo ria la vuel ta','la vuel ta de jó de e xis tir','si la ca sa me es tá re cor dan do','quién de los dos va a sa lir']):phrase(start+k*2*BAR,line)
    for name in instruments:instruments[name].sort(key=lambda e:e['t'])
    P={'semilla':SEED,'bpm':BPM,'compas':BAR,'duracion':DUR,'secciones':sections,'compases':bars,'laberinto':walk,'instrumentos':instruments,'preparaciones':preparations,'frases':phrases,'hooks':hooks}
    im=score_image(P);nonce=os.urandom(24).hex();h=hashlib.sha256(im.tobytes()+Path(__file__).read_bytes()+(ROOT/'render.cjs').read_bytes()+nonce.encode()).hexdigest();tag=h[:12]
    out=ROOT/f'la-salida-cambia-s{SEED}-{tag}';out.mkdir(exist_ok=False)
    for folder in ['proceso','render','fuentes']: (out/folder).mkdir()
    dump(out/'partitura.json',P);png(out/'proceso'/f'01-forma-y-rutas-s{SEED}-{tag}.png',im)
    sources=[Path(__file__),ROOT/'render.cjs',REPO/'lo-que-no-sono/voz.cjs']+list((REPO/'objetos/motor').glob('*.js'))
    hashes={}
    for f in sources:
        target=out/'fuentes'/f.name
        with target.open('xb') as fh:fh.write(f.read_bytes())
        hashes[str(f.relative_to(REPO))]=sha(f)
    dump(out/'receta-inicial.json',{'id':h,'nonce':nonce,'semilla':SEED,'fecha_local':'2026-10-15','fuentes_sha256':hashes,'imagen_inicial_sha256':sha(next((out/'proceso').glob('*.png')))})
    print(out,flush=True)

def spectra(out):
    P=json.loads((out/'partitura.json').read_text(encoding='utf8'));tag=out.name.split('-')[-1]
    im,d=card('02 / los cuerpos reales de los instrumentos','Espectros medidos de los stems físicos, antes de mezclar la canción')
    names=['piano','bajo','viento','clarinete','cuerdas','metal','vozagua','agua','pajaro','waterphone','gong','tambor']
    meta={}
    for i,name in enumerate(names):
        sr,y=wavfile.read(out/'render'/f'{name}.wav');assert sr==SR and len(y)==N and np.isfinite(y).all()
        y=y.astype(np.float32);_,tt,z=stft(y,SR,nperseg=2048,noverlap=0)
        spec=np.mean(np.abs(z)**2,axis=1);freq=np.fft.rfftfreq(2048,1/SR);bins=np.searchsorted(freq,np.geomspace(40,12000,450))
        v=10*np.log10(spec[bins]+1e-15);v=np.clip((v-v.max()+55)/55,0,1)
        col=i%3;row=i//3;x0=32+col*385;y0=115+row*117;d.text((x0,y0),name,font=FONT(15),fill=FG)
        d.line([(x0+j/449*350,y0+96-float(u)*65) for j,u in enumerate(v)],fill=[LIME,PINK,CYAN][col],width=2)
        energies=np.mean(y[:len(y)//4800*4800].reshape(-1,4800)**2,axis=1);active=energies[energies>max(energies.max()*1e-5,1e-12)]
        meta[name]={'pico':float(np.abs(y).max()),'rms_activo_dBFS':float(10*np.log10(np.mean(active)+1e-14)),'eventos':len(P['instrumentos'][name])}
    png(out/'proceso'/f'02-instrumentos-s{SEED}-{tag}.png',im);dump(out/'instrumentos-medidos.json',meta)
    print('instrumentos medidos',meta,flush=True)

# Mezcla: se calibra cada instrumento completo por su RMS activo; se preserva la diferencia de sus ataques.
TARGET={'piano':-24,'bajo':-23,'viento':-28,'clarinete':-28,'cuerdas':-28,'agua':-30,'vozagua':-25,'waterphone':-31,'tambor':-25,'metal':-27,'pajaro':-33,'gong':-29}
PAN={'piano':-.22,'bajo':0,'viento':.35,'clarinete':-.4,'cuerdas':.55,'agua':-.55,'vozagua':.3,'waterphone':-.65,'tambor':0,'metal':-.25,'pajaro':.65,'gong':.1}
SEND={'piano':.15,'bajo':.025,'viento':.2,'clarinete':.15,'cuerdas':.28,'agua':.22,'vozagua':.13,'waterphone':.4,'tambor':.06,'metal':.12,'pajaro':.25,'gong':.35}
def mix(out):
    P=json.loads((out/'partitura.json').read_text(encoding='utf8'));meta=json.loads((out/'instrumentos-medidos.json').read_text(encoding='utf8'));tag=out.name.split('-')[-1]
    rest=np.zeros((N,2),np.float32);wet=rest.copy();gains={};section_levels={s['nombre']:{} for s in P['secciones']}
    t=np.arange(N)/SR;duck=np.zeros(N,np.float32)
    for phrase in P['frases']:
        a=max(0,int((phrase['eventos'][0]['t']-.10)*SR));b=min(N,int((phrase['eventos'][-1]['t']+phrase['eventos'][-1]['dur']+.12)*SR))
        duck[a:b]=1
    duck=sosfilt(butter(1,8,'low',fs=SR,output='sos'),duck).astype(np.float32)
    for name,target in TARGET.items():
        sr,y=wavfile.read(out/'render'/f'{name}.wav');y=y.astype(np.float32)
        gain=10**((target-meta[name]['rms_activo_dBFS'])/20);gains[name]=gain;y*=gain
        y=filt(y,lo=35 if name in ['bajo','tambor'] else 110 if name in ['piano','clarinete','metal'] else 170)
        # Quitar excesos de una resonancia sin aplastar el ataque; pasa a través de una saturación suave.
        y=np.tanh(y*1.2)/1.2
        if name in ['piano','viento','cuerdas','clarinete','metal']:y*=1-.20*duck
        if name=='bajo':y*=np.interp(t,[0,20*BAR,24*BAR,32*BAR,56*BAR,64*BAR,72*BAR,84*BAR,DUR],[.75,.75,1.1,.9,1.1,.8,1.15,.7,0])
        if name in ['agua','waterphone','gong']:y=filt(y,hi=8500)
        pan=PAN[name];stereo=y[:,None]*np.array([math.cos((pan+1)*math.pi/4),math.sin((pan+1)*math.pi/4)],np.float32)
        # Instrumentos cercanos con un pequeño cuerpo a los lados, lejos con retardo propio.
        delay=int((.007+abs(pan)*.011)*SR)
        if name not in ['bajo','tambor']:stereo[delay:,1]+=stereo[:-delay,0]*.10
        rest+=stereo;wet+=stereo*SEND[name]
        for s in P['secciones']:section_levels[s['nombre']][name]=round(db(stereo[int(s['a']*SR):int(s['b']*SR)]),1)
    sr,voice=wavfile.read(out/'render/voz.wav');assert sr==SR and len(voice)==N
    voice=filt(voice,lo=130);vg=[]
    for phrase in P['frases']:
        a=max(0,int((phrase['eventos'][0]['t']-.12)*SR));b=min(N,int((phrase['eventos'][-1]['t']+phrase['eventos'][-1]['dur']+.12)*SR))
        wanted=1.3 if phrase['hook'] else 1.0;gain=float(np.clip(10**((db(rest[a:b])-db(voice[a:b])+wanted)/20),.3,10));curve=np.full(b-a,gain,np.float32);edge=min(4000,(b-a)//2)
        curve[:edge]=np.linspace(1,gain,edge);curve[-edge:]=np.linspace(gain,1,edge);voice[a:b]*=curve[:,None]
        vg.append({'t':phrase['eventos'][0]['t'],'voz_sobre_resto_dB':round(db(voice[a:b])-db(rest[a:b]),2),'ganancia':gain})
    wet+=voice*.12;wet=filt(wet,lo=150,hi=3900);mixed=rest+voice
    for delay,g in [(.031,.32),(.067,.25),(.113,.18),(.179,.14),(.283,.10),(.431,.07),(.617,.035)]:
        k=int(delay*SR);mixed[k:]+=wet[:-k,::-1]*g
    mixed=filt(mixed,lo=29);mixed*=np.clip((DUR-t)/2.5,0,1)[:,None];mixed*=.88/max(.88,float(np.abs(mixed).max()))
    wav(out/'render/mezcla-previa.wav',mixed);wav(out/'render/voz-mezcla.wav',voice)
    raw=cmd(['ffmpeg','-hide_banner','-nostats','-i',str(out/'render/mezcla-previa.wav'),'-af','loudnorm=I=-14.5:TP=-1.6:LRA=10:print_format=json','-f','null','-']).stderr
    normal=json.JSONDecoder().raw_decode(raw[raw.rfind('{'):])[0];dump(out/'normalizacion.json',normal)
    af='loudnorm=I=-14.5:TP=-1.6:LRA=10:linear=true:'+':'.join(f'{a}={normal[b]}' for a,b in [('measured_I','input_i'),('measured_TP','input_tp'),('measured_LRA','input_lra'),('measured_thresh','input_thresh'),('offset','target_offset')])
    name=f'la-salida-cambia-s{SEED}-{tag}'
    cmd(['ffmpeg','-hide_banner','-loglevel','error','-n','-i',str(out/'render/mezcla-previa.wav'),'-af',af,'-ar','48000','-c:a','pcm_s24le',str(out/f'{name}.wav')])
    cmd(['ffmpeg','-hide_banner','-loglevel','error','-n','-i',str(out/f'{name}.wav'),'-c:a','aac','-b:a','224k','-metadata','title=La salida cambia de lugar','-metadata','artist=Canek Zapata',str(out/f'{name}.m4a')])
    raw=cmd(['ffmpeg','-hide_banner','-nostats','-i',str(out/f'{name}.m4a'),'-af','loudnorm=I=-14.5:TP=-1.6:LRA=10:print_format=json','-f','null','-']).stderr
    loud=json.JSONDecoder().raw_decode(raw[raw.rfind('{'):])[0]
    bands={}
    for s in P['secciones']:
        a,b=int(s['a']*SR),int(s['b']*SR);seg=mixed[a:b];total=db(seg)
        bands[s['nombre']]={'total_dBFS':round(total,1),**{label:round(db(filt(seg,lo,hi))-total,1) for label,lo,hi in [('sub',30,90),('graves',90,300),('medios',300,2000),('presencia',2000,6000),('aire',6000,15000)]}}
    dump(out/'medidas.json',{'aac':loud,'ganancias_stems':gains,'voz_por_frase':vg,'niveles_instrumentos_por_seccion':section_levels,'bandas_por_seccion':bands})
    _,_,Z=stft(mixed.mean(axis=1),SR,nperseg=4096,noverlap=1024);freq=np.fft.rfftfreq(4096,1/SR);ix=np.searchsorted(freq,np.geomspace(45,12000,390));v=20*np.log10(np.abs(Z[ix])+1e-8);v=np.clip((v-v.max()+65)/65,0,1)
    pix=np.stack([v[::-1]*195,v[::-1]*223,v[::-1]*150],axis=2).astype(np.uint8)
    im,d=card('03 / misma canción, otros cuerpos','Audio real · verso / pre / coro / verso / pre / coro / puente / coro final')
    im.paste(Image.fromarray(pix).resize((1134,440)),(32,125));png(out/'proceso'/f'03-mezcla-s{SEED}-{tag}.png',im);png(out/f'resultado-s{SEED}-{tag}.png',im);png(out/'og.png',im)
    frames=[Image.open(p).convert('RGB') for p in sorted((out/'proceso').glob('0[123]-*.png'))];sheet=Image.new('RGB',(1200,1890));[sheet.paste(f,(0,i*630)) for i,f in enumerate(frames)];palette=sheet.quantize(colors=128);q=[f.quantize(palette=palette) for f in frames]
    with (out/f'proceso-la-salida-cambia-s{SEED}-{tag}.gif').open('xb') as f:q[0].save(f,format='GIF',save_all=True,append_images=q[1:],duration=[2600]*3,loop=0,optimize=False)
    txt(out/'proceso/README.md','# Proceso real\n\n01: score de forma y entradas, antes de renderizar.\n02: espectros medidos de los doce stems físicos, antes de mezclar voz.\n03: espectrograma de la mezcla terminada.\n\nEl GIF reúne estas tres capturas reales, 7.8 s y paleta común. No simula el interior de un generador.\n04 es la hoja de revisión de sus cuadros decodificados. Semilla 171015; hash y nonce en la receta.\n')
    print('MEZCLA',loud,flush=True)

def verify(out):
    P=json.loads((out/'partitura.json').read_text(encoding='utf8'));tag=out.name.split('-')[-1]
    sr,x=wavfile.read(next(out.glob('la-salida-cambia-*.wav')));assert sr==SR and x.shape==(N,2)
    x=x.astype(float)/2**31;assert np.isfinite(x).all() and np.abs(x).max()<1
    assert sum(s['n'] for s in P['secciones'])==88
    # La misma letra y melodía del primer renglón vuelven en los tres coros y la repetición final.
    lines=[f for f in P['frases'] if f['texto']=='la sa li da cam bia de lu gar']
    normalized=lambda f:[(round(e['t']-f['eventos'][0]['t'],6),e['nota'],e['texto']) for e in f['eventos']]
    assert len(lines)==4 and all(normalized(f)==normalized(lines[0]) for f in lines)
    assert all(len(set(triad(tuple(e['desde'])))&set(triad(tuple(e['hasta']))))==2 for e in P['laberinto'])
    y=wavfile.read(out/'render/voz.wav')[1].mean(axis=1);err=[]
    for phrase in P['frases']:
        e=phrase['eventos'][-1];f0=440*2**((e['nota']-69)/12);seg=y[int((e['t']+.3)*SR):int((e['t']+.65)*SR)][::3].astype(float)
        if len(seg)<100:continue
        seg-=seg.mean();ac=correlate(seg,seg,mode='full',method='fft')[len(seg)-1:];lo=int(16000/(f0*1.35));hi=int(16000/(f0*.75));peaks,_=find_peaks(ac[lo:hi])
        if len(peaks):
            j=lo+peaks[np.argmax(ac[lo:hi][peaks])];delta=.5*(ac[j-1]-ac[j+1])/(ac[j-1]-2*ac[j]+ac[j+1]);err.append(float(1200*np.log2(16000/(j+delta)/f0)))
    gif=next(out.glob('*.gif'));im=Image.open(gif);duration=0;contact=Image.new('RGB',(1200,630),BG)
    for i in range(im.n_frames):im.seek(i);duration+=im.info['duration'];contact.paste(im.convert('RGB').resize((600,315)),((i%2)*600,(i//2)*315))
    assert im.n_frames==3 and duration<=10000 and gif.stat().st_size<=15*1024**2
    png(out/'proceso'/f'04-revision-gif-s{SEED}-{tag}.png',contact)
    for p in out.rglob('*.png'):
        with Image.open(p) as im:im.verify()
    assert Image.open(out/'og.png').size==(1200,630)
    meta=json.loads((out/'instrumentos-medidos.json').read_text(encoding='utf8'));assert all(v['pico']>1e-5 for v in meta.values())
    result={'duracion_s':len(x)/sr,'pico_muestra_dBFS':float(20*np.log10(np.abs(x).max())),'compases':88,'stems_fisicos_no_vacios':len(meta),'aristas_P_R_L_comprobadas':len(P['laberinto']),
      'repeticiones_identicas_gancho':len(lines),'afinacion_silabas_largas_mediana_abs_cents':float(np.median(np.abs(err))),
      'metodo_afinacion':'Autocorrelación local alrededor de la nota escrita; comprobación orientativa, no escucha humana.',
      'gif':{'cuadros':3,'segundos':duration/1000,'bytes':gif.stat().st_size}}
    dump(out/'verificacion.json',result);print(json.dumps(result,ensure_ascii=False,indent=1),flush=True)

if __name__=='__main__':
    action=sys.argv[1]
    if action=='preparar':prepare()
    else:{'proceso-instrumentos':spectra,'mezclar':mix,'verificar':verify}[action](Path(sys.argv[2]).resolve())
