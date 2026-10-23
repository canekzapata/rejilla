"""Mezcla de treinta capas; grave repartido, salida pesada, ida/vuelta por Rejilla."""
from comun import *
from instrumentos import *
from partitura import figura,salva
from PIL import Image
import ast,gc,re
NIVELES={'sub':3,'808-cuerpo':1,'falcon':-3,'mandibula':3,'residuo-grave':-4,'organo-roto':-8,'kick':2,'caja':0,'clap':-7,'hats':-13,'hats-tresillos':-12,'perc-frita':-10,'dundun':-3,'mbira':-4,'kalimba':-7,'arpa-boca':-5,'mbira-vocal':0,'kalimba-vocal':-5,'solista-grave':7,'doble-grave':-3,'voz-residual':3,'chops-graves':1,'coro-oscuro':-9,'boca-percusiva':-3,'flujo-ideal':-14,'flujo-viscoso':-14,'residuo':-10,'eco-captador':-1,'chelo':-8,'contrabajo':-10}
FAMILIAS={'graves':list(NIVELES)[:6],'ritmo':list(NIVELES)[6:13],'pulgares':list(NIVELES)[13:18],'voces':list(NIVELES)[18:24],'fluido':list(NIVELES)[24:28],'cuerdas':list(NIVELES)[28:]}
def grid_fijado(y,out,work,tag):
 # Se extrae únicamente la función de rejilla fijada, sin ejecutar el módulo/obra.
 source=(BASE/'fuentes/lago/mezcla.py').read_text(encoding='utf-8');tree=ast.parse(source);f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='grid');code=ast.get_source_segment(source,f).replace('s227-',f's{SEED}-');ns=globals().copy();exec(compile(code,'grid-derivada-del-lago','exec'),ns);return ns['grid'](y,out,work,tag)
def main():
 out=ultimo();tag=out.name.split('-')[-1];P=leer(out/'partitura.json');N=round(P['duracion']*SR);tt=np.arange(N)/SR;B=P['compas'];R=run();work=R/('mezcla-'+os.urandom(6).hex());work.mkdir(exist_ok=False)
 master=out/(out.name+'.wav')
 if master.exists():raise FileExistsError(master)
 def read(c):
  x=np.fromfile(R/(c+'.f32'),np.float32)
  if len(x)==N:x=pan(x,{'mbira':-.3,'kalimba':.3,'chelo':-.25,'contrabajo':.12}.get(c,0))
  else:x=x.reshape(-1,2)
  assert len(x)==N and np.isfinite(x).all(),c;return x
 y=np.zeros((N,2),np.float32);send=np.zeros_like(y);groups={c:np.memmap(work/(c+'.grupo.f32'),mode='w+',shape=(N,2),dtype='float32') for c in FAMILIAS}
 for v in groups.values():v[:]=0
 duck=np.ones(N,np.float32)
 for e in P['eventos']['kick']:
  i=round(e['t']*SR);n=min(round(.17*SR),N-i);duck[i:i+n]=np.minimum(duck[i:i+n],1-.6*np.exp(-np.arange(n)/(.055*SR)))
 voice=read('solista-grave').mean(1);a=np.abs(voice);a=lfilter([1-np.exp(-1/(.025*SR))],[1,-np.exp(-1/(.025*SR))],a);activity=np.clip(a/(np.percentile(a[a>1e-6],70)+1e-9),0,1).astype('float32');del voice,a
 info={'capas':{},'macro':'última entrada de graves x1.55; cuerpo mono abajo de 90 Hz; voz principal conserva fundamental; vacíos de batería durante el retorno'}
 for c in NIVELES:
  print('mezcla',c,flush=True);x=read(c)
  hp=26 if c=='sub' else 65 if c=='solista-grave' else 55 if c in ['doble-grave','chops-graves','voz-residual'] else 34 if c=='kick' else 100 if c in ['falcon','mandibula','808-cuerpo','contrabajo','residuo-grave'] else 125 if c in ['flujo-ideal','flujo-viscoso','residuo','organo-roto'] else 90
  x=sosfiltfilt(butter(3,hp,btype='highpass',fs=SR,output='sos'),x,axis=0).astype('float32')
  if c=='sub':x=sosfiltfilt(butter(4,88,btype='lowpass',fs=SR,output='sos'),x,axis=0).astype('float32')
  ar=activo(x);assert ar>1e-8,(c,'silencio');gain=10**((-24+NIVELES[c])/20)/ar;x*=gain
  w=np.ones(N,np.float32)
  if c in FAMILIAS['graves']:w[(tt>=88*B)&(tt<120*B)]*=1.55
  if c in ['mandibula','falcon']:w[(tt>=32*B)&(tt<48*B)]*=1.15
  if c in FAMILIAS['ritmo']:w[(tt>=88*B)&(tt<120*B)]*=1.18
  if c in ['mbira-vocal','kalimba-vocal','dundun','arpa-boca']:w[(tt>=48*B)&(tt<64*B)]*=1.6
  if c=='eco-captador':w[(tt>=64*B)&(tt<88*B)]*=2.2
  if c=='residuo-grave':w[tt<64*B]=0;w[(tt>=64*B)&(tt<88*B)]*=.65
  if c in FAMILIAS['fluido']:
   w[tt<8*B]*=1.4;w[(tt>=8*B)&(tt<64*B)]*=.65;w[(tt>=88*B)&(tt<120*B)]*=.55
  if c in ['solista-grave','voz-residual']:w[(tt>=88*B)&(tt<120*B)]*=1.16
  if c in ['flujo-ideal','flujo-viscoso']:w[tt>=120*B]*=.4
  x*=w[:,None]
  if c in ['sub','808-cuerpo','falcon','mandibula','residuo-grave']:x*=duck[:,None]
  if c in ['falcon','mandibula','organo-roto','chelo','contrabajo','eco-captador']:
   band=sosfiltfilt(butter(2,[160,650],btype='bandpass',fs=SR,output='sos'),x,axis=0).astype('float32');x-=band*(activity*.5)[:,None];del band
  family=next(g for g,cs in FAMILIAS.items() if c in cs);groups[family]+=x;y+=x
  if c not in FAMILIAS['graves']+['kick','caja','clap','hats','hats-tresillos']:send+=x*(.055 if c=='solista-grave' else .13)
  info['capas'][c]={'activo_filtrado':ar,'ganancia':gain,'pico':float(abs(x).max()),'eventos':len(P['eventos'][c]),'pasa_altos_Hz':hp};del x;gc.collect()
 info['secciones']={}
 for s in P['secciones']:
  i,j=round(s['t']*SR),round(s['t1']*SR);info['secciones'][s['id']]={'RMS_dBFS':float(10*np.log10(np.mean(y[i:j]**2)+1e-15)),'grupos_contra_resto_dB':{}}
  for name,v in groups.items():
   z=np.asarray(v[i:j]);rest=y[i:j]-z;info['secciones'][s['id']]['grupos_contra_resto_dB'][name]=float(10*np.log10((np.mean(z*z)+1e-15)/(np.mean(rest*rest)+1e-15)))
 for g in groups.values():g.flush()
 del groups,z,rest,g;gc.collect()
 # Dos ecos cortos: el grave permanece seco y centrado.
 for delay,level in [(.19,.24),(.37,.13)]:
  k=round(delay*SR);y[k:,0]+=send[:-k,1]*level;y[k:,1]+=send[:-k,0]*level
 del send;fade=np.minimum(1,np.maximum(0,(P['duracion']-tt)/1.5));y*=fade[:,None];y[-round(.06*SR):]=0;y*=.78/(abs(y).max()+1e-12)
 print('paso completo por Rejilla',flush=True);z,gr=grid_fijado(y,out,work,tag);wav(work/'mezcla-rejilla.wav',z)
 first=subprocess.run(['ffmpeg','-hide_banner','-i',str(work/'mezcla-rejilla.wav'),'-af','loudnorm=I=-12.5:TP=-2.5:LRA=10:print_format=json','-f','null','-'],capture_output=True,text=True,check=True);met=json.loads(re.findall(r'\{[^{}]+\}',first.stderr)[-1]);flt=f"loudnorm=I=-12.5:TP=-2.5:LRA=10:measured_I={met['input_i']}:measured_TP={met['input_tp']}:measured_LRA={met['input_lra']}:measured_thresh={met['input_thresh']}:offset={met['target_offset']}:linear=true"
 subprocess.run(['ffmpeg','-n','-v','error','-i',str(work/'mezcla-rejilla.wav'),'-af',flt,'-ar','48000','-c:a','pcm_f32le',str(master)],check=True);aac(master.with_suffix('.m4a'),master)
 r=subprocess.run(['ffmpeg','-hide_banner','-i',str(master.with_suffix('.m4a')),'-af','loudnorm=I=-12.5:TP=-2.5:LRA=10:print_format=json','-f','null','-'],capture_output=True,text=True,check=True);info['aac']=json.loads(re.findall(r'\{[^{}]+\}',r.stderr)[-1]);info['rejilla']=gr;jsave(out/'mezcla-medidas.json',info)
 for label,a,b in [('salida-pesada',96*B,116*B),('solo-eco-D',64*B,88*B),('pulgares-que-vocalizan',48*B,64*B)]:
  subprocess.run(['ffmpeg','-n','-v','error','-ss',str(a),'-i',str(master),'-t',str(b-a),'-c:a','aac','-b:a','256k',str(out/f'{label}-s{SEED}-{tag}.m4a')],check=True)
 f,ax=figura('La corriente devuelve tu nombre','Mezcla efectiva · subgrave / caja a medio tiempo / solista grave / residuo',2)
 ax[0].plot(tt[::128],z[::128,0],color='#af9aff',lw=.4);ax[0].set_xlabel('segundos');ax[0].set_title('Dejar peso para el regreso')
 ax[1].specgram(z.mean(1)[::4],NFFT=1024,Fs=SR/4,noverlap=768,cmap='magma',vmin=-95,vmax=-25);ax[1].set_yscale('log');ax[1].set_ylim(25,4000);ax[1].set_xlabel('segundos');salva(f,out/'proceso'/f'05-mezcla-y-grave-s{SEED}-{tag}.png')
 print('MASTER',master,info['aac'],gr,flush=True)
if __name__=='__main__':main()
