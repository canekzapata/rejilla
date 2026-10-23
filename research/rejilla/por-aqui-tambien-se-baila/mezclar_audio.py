"""Treinta capas reales, cortes por buses, lectura Rejilla y máster de audio."""
from audio_comun import *
from laminas import *
from scipy.signal import stft,istft
from scipy.ndimage import uniform_filter1d
from PIL import Image
import ast,gc,re

LEVELS={'acordeon-tema':-23,'acordeon-respuesta':-30,'bajo-cumbia':-23,'guiro':-35,'conga':-29,'campana':-34,'timbal':-29,'bombo':-23,'caja':-28,
 'membrana-din':-27,'membrana-ta':-29,'membrana-thom':-27,'barro':-32,'pandero':-34,'boca-ritmica':-29,
 'laser-directo':-23,'laser-laberinto':-23,'laser-talbot':-23,'raspador':-31,'mbira-boca':-29,'guembri-drone':-30,'organo-drone':-34,
 'clarinete':-26,'chelo':-30,'bolsa-juguetes':-29,'voz-verso':-20,'voz-respuesta':-22,'radio-chofer':-21,'radio-pasajera':-21,'estatica-senal':-32}
GROUPS={'cumbia':['acordeon-tema','acordeon-respuesta','bajo-cumbia','guiro','conga','campana','timbal','bombo','caja'],
 'percusiones':['membrana-din','membrana-ta','membrana-thom','barro','pandero','boca-ritmica','bolsa-juguetes','mbira-boca'],
 'solo':['laser-directo','laser-laberinto','laser-talbot','raspador'],
 'campo':['guembri-drone','organo-drone','clarinete','chelo'],
 'voces':['voz-verso','voz-respuesta'],'libres':['radio-chofer','radio-pasajera','estatica-senal']}

def lectura_rejilla(y,out,work,tag):
    src=BASE.parent/'el-acorde-vuelve-con-otro-cuerpo/fuentes/rejilla/mezcla-lago.py';text=src.read_text(encoding='utf8');tree=ast.parse(text);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='grid');code=ast.get_source_segment(text,node).replace('s227-',f's{SEED}-');guardar(out/'fuentes-fijadas/rejilla-grid-origen.py',src.read_bytes());ns=globals().copy();exec(compile(code,'rejilla-fijada-por-aqui','exec'),ns);return ns['grid'](y,out,work,tag)

def radio_clip(x,c,P,via,recuerdo=None):
    """Receptor fijado + clima: voz PSOLA real como contenido de la estación."""
    RAD=importar(BASE/'fuentes/radio/sintes10.py','baila_radio_final');RAD.SR=SR;out=np.zeros_like(x)
    for j,e in enumerate(P['eventos'][c]):
        a=max(0,round((e['t']-.06)*SR));b=min(len(x),round((e['t']+e['dur']+.1)*SR));z=x[a:b].mean(1);d=len(z)/SR
        # La estación retransmite el silbato real ya oído, no otro oscilador
        # parecido. Se vuelve contenido del receptor y atraviesa su desintonía.
        if recuerdo is not None and e['t']>=220:
            k=round(.72*SR);n=min(len(recuerdo),len(z)-k)
            if n>0:z=z.copy();z[k:k+n]+=.65*recuerdo[:n]
        f=620 if c.endswith('chofer') else 630
        q,_=RAD.radio([{'f':f,'audio':z,'nivel':1,'fading':0}],[[0,f+.8],[.12,f],[max(.13,d-.15),f],[d,f+.35]],len(z),22+j)
        wet=float(np.interp(e['t'],via['t'],via['lluvia_compuesta']));dark=sosfilt(butter(2,1700,fs=SR,output='sos'),q);q=(1-.5*wet)*q+.5*wet*dark
        out[a:b]+=pan(q,-.18 if c.endswith('chofer') else .25)
    return out

def respuesta_vocoder(x,P):
    """Vocalización parcial del coro sobre lengüeta, dentro de sus mismos eventos."""
    # Es color de la pista de respuesta, no una voz extra que ocupa los solos.
    y=x.mean(1);carrier=np.zeros(len(y),np.float32)
    for e in P['eventos']['voz-respuesta']:
        i=round(e['t']*SR);n=min(round((e['dur']+.08)*SR),len(y)-i);t=np.arange(n)/SR;f=hz(e['midi']);q=sum(np.sin(2*np.pi*f*h*t)/h for h in range(1,min(32,int(SR*.42/f))))*env(n,.008,.06)
        carrier[i:i+n]+=q*.2
    ans=np.zeros(len(y),np.float32)
    for start in range(0,len(y),4*SR):
        end=min(len(y),start+4*SR);a=max(0,start-SR//4);b=min(len(y),end+SR//4)
        if np.max(abs(y[a:b]))<1e-8:continue
        f,_,M=stft(y[a:b],SR,nperseg=1024,noverlap=768);_,_,C=stft(carrier[a:b],SR,nperseg=1024,noverlap=768)
        bands=np.geomspace(80,7200,30);B=np.array([np.maximum(0,1-abs(np.log(np.maximum(f,1)/fc))/np.log(bands[min(j+1,29)]/fc if j<29 else fc/bands[j-1])) for j,fc in enumerate(bands)],np.float32)
        em=B@abs(M);ec=B@abs(C);weights=B/(B.sum(0,keepdims=True)+1e-9);gain=np.clip(em/(ec+1e-5),0,20);_,v=istft(C*(weights.T@gain),SR,nperseg=1024,noverlap=768);ans[start:end]=v[start-a:end-a]
    # El texto conserva su articulación seca; sólo un color de lengüeta.
    return x*.83+pan(ans,.12)*.28

def main():
    out,cfg,P,work=contexto();tag=out.name.split('-')[-1];N=round(cfg['duracion']*SR);R=work/'fuentes';via=leer(out/'viaje.json');tt=np.arange(N)/SR
    assert set(LEVELS)==set(P['eventos'])
    master=out/f'por-aqui-tambien-se-baila-s22-{tag}.wav'
    if master.exists():raise FileExistsError(master)
    mixdir=work/('mezcla-'+os.urandom(6).hex());mixdir.mkdir(exist_ok=False)
    groups={g:np.memmap(mixdir/(g+'.f32'),mode='w+',dtype='float32',shape=(N,2)) for g in GROUPS}
    for a in groups.values():a[:]=0
    music=np.zeros((N,2),np.float32);free=np.zeros_like(music);send=np.zeros_like(music);info={'canales':{},'grupos':GROUPS,'niveles_dB_activos':LEVELS,'interpretacion':'30 partes de la r4 aprobada; sin visor/video'}
    voc=np.zeros(N,np.float32)
    for line in P['letra']:
        a=max(0,round((line['t']-.05)*SR));b=min(N,round((line['fin_s']+.25)*SR));voc[a:b]=1
    voc=uniform_filter1d(voc,round(.07*SR))
    laser_ref=activo(rawread(R,'laser-directo',N));assert laser_ref>0
    for c,level in LEVELS.items():
        print('mezcla',c,flush=True);x=rawread(R,c,N);g=next(g for g,cs in GROUPS.items() if c in cs)
        if c in ['radio-chofer','radio-pasajera']:
            memory=None
            if c=='radio-pasajera':
                bag=rawread(R,'bolsa-juguetes',N);a=round(177.37*SR);memory=bag[a:a+round(.55*SR)].mean(1).copy();del bag
            x=radio_clip(x,c,P,via,memory).astype(np.float32)
            if memory is not None:info['memoria_radio']={'fuente':'bolsa-juguetes.f32','inicio_fuente_s':177.37,'largo_fuente_s':.55,'retorno_s':231.72,'ganancia_antes_receptor':.65,'operacion':'retransmisión del silbato efectivamente renderizado, antes de selectividad y clima'}
        if c=='voz-respuesta':x=respuesta_vocoder(x,P).astype(np.float32)
        hp=28 if c in ['bajo-cumbia','bombo','membrana-thom','guembri-drone'] else 90 if c.startswith(('voz','radio')) else 55
        x=sosfilt(butter(2,hp,btype='highpass',fs=SR,output='sos'),x,axis=0).astype(np.float32)
        ar=activo(x);assert ar>1e-9,(c,'muda');ref=laser_ref if c.startswith('laser') else ar;gain=10**(level/20)/ref;x*=gain
        if c in ['acordeon-respuesta','organo-drone','clarinete','chelo']:x*=(1-.34*voc[:,None])
        if c.startswith('laser'):x[(tt>=130)&(tt<170)]*=1.25
        if c=='bolsa-juguetes':x[(tt<33)]*=1.3
        # Presión/clima ya alteraron golpes y modos; este filtro lleva sus
        # consecuencias espectrales al acordeón y los instrumentos de ancla.
        if c in ['acordeon-tema','acordeon-respuesta','guiro','conga','campana','timbal','caja','mbira-boca','raspador']:
            wet=np.interp(tt,via['t'],via['lluvia_compuesta']).astype(np.float32);dark=sosfilt(butter(2,3800,fs=SR,output='sos'),x,axis=0).astype(np.float32);x=x*(1-.5*wet[:,None])+dark*(.5*wet[:,None]);del dark,wet
        if c not in ['radio-chofer','radio-pasajera','estatica-senal']:corte(x)
        # Panorama de biblioteca originalmente mono.
        p={'acordeon-tema':-.12,'acordeon-respuesta':.28,'guiro':.38,'conga':-.28,'campana':.3,'timbal':-.18,'clarinete':.25,'chelo':-.25,'guembri-drone':-.08}.get(c)
        if p is not None:x=pan(x.mean(1)*np.sqrt(2),p).astype(np.float32)
        groups[g]+=x
        if g=='libres':free+=x
        else:
            music+=x
            if c not in ['bajo-cumbia','bombo','caja','guiro','campana','pandero','membrana-thom']:send+=x*(.08 if c.startswith('voz') else .12)
        info['canales'][c]={'eventos':len(P['eventos'][c]),'rms_activo_previo':ar,'ganancia':gain,'pico_procesado':float(abs(x).max()),'pasaaltas_hz':hp,'grupo':g,'normalizacion_compartida_laser':c.startswith('laser')}
        del x;gc.collect()
    # Espacio corto y cruzado. Cortar después del efecto; la avería no hereda ecos.
    for sec,lev in [(.137,.28),(.287,.18),(.461,.09)]:
        k=round(sec*SR);music[k:,0]+=send[:-k,1]*lev;music[k:,1]+=send[:-k,0]*lev
    del send;corte(music);y=music+free
    y*=np.minimum(1,np.maximum(0,(cfg['duracion']-tt)/1.5))[:,None];y[-round(.1*SR):]=0
    # Medida a partir de los buses reales, no sólo de ausencia de notas.
    a,b=180*SR,200*SR;info['averia']={'pico_bus_metrico':float(abs(music[a:b]).max()),'rms_bus_libre':float(np.sqrt(np.mean(free[a:b]**2))),'rms_bus_metrico':float(np.sqrt(np.mean(music[a:b]**2)))};assert info['averia']['pico_bus_metrico']==0
    info['balance_secciones']={}
    for s in P['secciones']:
        a,b=round(s['t']*SR),round(s['t1']*SR);info['balance_secciones'][s['id']]={g:float(10*np.log10((np.mean(q[a:b]**2)+1e-15)/(np.mean((y[a:b]-q[a:b])**2)+1e-15))) for g,q in groups.items()}
    for q in groups.values():q.flush()
    del groups,q,free,music;gc.collect()
    y*=.78/(float(abs(y).max())+1e-12)
    # PNG de los buses en la parada, antes de pasar por Rejilla.
    f,ax=figura('La avería existe también en la señal','Buses renderizados: pulso cortado, radio y motor libres; regreso en 3:20',2)
    for j,g in enumerate(['cumbia','percusiones','solo','libres']):
        z=np.memmap(mixdir/(g+'.f32'),mode='r',dtype='float32',shape=(N,2));i,k=172*SR,208*SR;v=np.mean(z[i:k].reshape(-1,256,2)**2,axis=(1,2))**.5;ax[0].plot(np.arange(len(v))*256/SR+172,v+j*.05,label=g,lw=.8);del z
    ax[0].axvspan(180,200,color='#baa47d',alpha=.2);ax[0].legend(fontsize=8);ax[0].set_xlabel('segundos');ax[1].plot(tt[::256],y[::256,0],lw=.4);ax[1].set_xlabel('segundos de la mezcla');salva(f,out/'proceso'/f'03-buses-y-averia-s22-{tag}.png')
    print('Lectura Rejilla: magnitud y fase de toda la mezcla',flush=True);z,gr=lectura_rejilla(y,out,mixdir,tag);info['rejilla']=gr
    # Rectangular DFT de 1 s puede dejar un offset de columna; preservar el bus
    # libre original durante el corte elimina esa contaminación sin cambiar su ritmo.
    # Se registra el empalme y se funde 10 ms en ambos extremos.
    a,b=180*SR,200*SR;edge=round(.01*SR);w=np.ones(b-a,np.float32);w[:edge]=np.linspace(0,1,edge);w[-edge:]=np.linspace(1,0,edge);z[a:b]=z[a:b]*(1-w[:,None])+y[a:b]*w[:,None]
    info['rejilla']['averia']='se repone bus libre pre-Rejilla 180-200 s con empalmes de 10 ms para evitar DC por columnas; resto leído por Rejilla'
    z[-round(.1*SR):]=0;wav(mixdir/'mezcla-rejilla.wav',z)
    measure=subprocess.run(['ffmpeg','-hide_banner','-i',str(mixdir/'mezcla-rejilla.wav'),'-af','loudnorm=I=-15:TP=-2.2:LRA=18:print_format=json','-f','null','-'],capture_output=True,text=True,check=True);met=json.loads(re.findall(r'\{[^{}]+\}',measure.stderr)[-1]);flt=f"loudnorm=I=-15:TP=-2.2:LRA=18:measured_I={met['input_i']}:measured_TP={met['input_tp']}:measured_LRA={met['input_lra']}:measured_thresh={met['input_thresh']}:offset={met['target_offset']}:linear=true"
    subprocess.run(['ffmpeg','-n','-v','error','-i',str(mixdir/'mezcla-rejilla.wav'),'-af',flt,'-ar','48000','-c:a','pcm_s24le',str(master)],check=True)
    aac=master.with_suffix('.m4a');subprocess.run(['ffmpeg','-n','-v','error','-i',str(master),'-c:a','aac','-b:a','256k','-movflags','+faststart',str(aac)],check=True)
    ck=subprocess.run(['ffmpeg','-hide_banner','-i',str(aac),'-af','loudnorm=I=-15:TP=-2.2:LRA=18:print_format=json','-f','null','-'],capture_output=True,text=True,check=True);info['aac']=json.loads(re.findall(r'\{[^{}]+\}',ck.stderr)[-1]);info['normalizacion_primera_medida']=met
    jsave(out/'mezcla-medidas.json',info)
    for name,a,b in [('tema-y-juguetes',18,50),('solo-del-laser',130,170),('averia-y-regreso',172,218)]:
        subprocess.run(['ffmpeg','-n','-v','error','-ss',str(a),'-i',str(master),'-t',str(b-a),'-c:a','aac','-b:a','224k',str(out/f'{name}-s22-{tag}.m4a')],check=True)
    f,ax=figura('Por aquí también se baila: audio completo','Treinta partes interpretadas; la radio guarda el silbido; 4:06',2);ax[0].plot(tt[::256],z[::256,0],lw=.45,color='#732605');ax[0].axvspan(180,200,alpha=.13,color='#1d2869');ax[0].set_xlabel('segundos');ax[1].specgram(z.mean(1)[::4],NFFT=1024,Fs=SR/4,noverlap=768,cmap='magma',vmin=-100,vmax=-30);ax[1].set_yscale('log');ax[1].set_ylim(70,4000);ax[1].set_xlabel('segundos');salva(f,out/'proceso'/f'04-master-y-rejilla-s22-{tag}.png')
    jsave(out/'audio-entrega.json',{'master':master.name,'escucha':aac.name,'duracion_s':cfg['duracion'],'sr_master':48000,'formato_master':'PCM 24 bits estéreo','mezcla_scratch':str(mixdir),'clips':[['tema-y-juguetes',18,50],['solo-del-laser',130,170],['averia-y-regreso',172,218]]})
    print(json.dumps(info['aac']),flush=True)

if __name__=='__main__':main()
