"""Treinta capas, planos por sección y paso efectivo por Rejilla."""
from comun import *
from laminas import *
from scipy.signal import butter,sosfiltfilt
from PIL import Image
import ast,re,gc
NIVELES={'ep-tema':6,'ep-comping':-4,'ep-sombra':-8,'piano-goma':-4,'vibrafono':-6,'kick':1,'caja':-1,'ride':-13,'hats':-15,'rim':-10,'maquina808':-8,'contrabajo':-1,'bajo-electrico':-4,'pedal110':-12,'chelo':2,'fuelle-alto':0,'fuelle-bajo':-2,'flauta':-5,'farfisa':-12,'resonador-A':-8,'resonador-coma':-8,'batidos':-13,'pulsos-batido':-11,'radio-izq':-10,'radio-der':-10,'telar':-8,'voz':4,'voz-doble':-8,'voz-fuelle':-7,'fragmento':-8}
FAMILIAS={'piano':list(NIVELES)[:5],'bateria':list(NIVELES)[5:11],'bajos':list(NIVELES)[11:14],'camara':list(NIVELES)[14:19],'presencias':list(NIVELES)[19:26],'voces':list(NIVELES)[26:]}
def grid_fijado(y,out,work,tag):
 source=(BASE/'fuentes/rejilla/mezcla-lago.py').read_text(encoding='utf-8');tree=ast.parse(source);f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='grid');code=ast.get_source_segment(source,f).replace('s227-',f's{SEED}-');ns=globals().copy();exec(compile(code,'grid-fijada-del-lago','exec'),ns);return ns['grid'](y,out,work,tag)
def main():
 out=ultimo();P=leer(out/'partitura.json');R=run();tag=out.name.split('-')[-1];N=round(P['duracion']*SR);tt=np.arange(N)/SR;work=R/('mezcla-'+os.urandom(6).hex());work.mkdir(exist_ok=False)
 if master().exists():raise FileExistsError(master())
 def read(c):
  x=np.fromfile(R/(c+'.f32'),np.float32);p={'ep-tema':-.08,'ep-comping':-.23,'ep-sombra':.27,'chelo':-.18,'fuelle-alto':.22,'fuelle-bajo':-.24,'contrabajo':-.08,'vibrafono':.25,'flauta':.2}.get(c,0)
  if len(x)==N:x=pan(x,p)
  else:x=x.reshape(-1,2)
  assert len(x)==N and np.isfinite(x).all(),c;return x
 y=np.zeros((N,2),np.float32);send=np.zeros_like(y);groups={c:np.memmap(work/(c+'.grupo.f32'),mode='w+',shape=(N,2),dtype='float32') for c in FAMILIAS}
 for g in groups.values():g[:]=0
 vocal=np.zeros(N,np.float32)
 for a,b in P['solista_ventanas']:
  vocal[(tt>a)&(tt<b)]=1
 info={'capas':{},'niveles_dB_relativos':NIVELES,'grupos':FAMILIAS}
 for c,level in NIVELES.items():
  print('mezcla',c,flush=True);x=read(c);hp=28 if c in ['kick','contrabajo','bajo-electrico'] else 65 if c.startswith('voz') or c=='fragmento' else 85
  x=sosfiltfilt(butter(2,hp,btype='highpass',fs=SR,output='sos'),x,axis=0).astype('float32');ar=activo(x);assert ar>1e-9,(c,'muda');gain=10**((-27+level)/20)/ar;x*=gain;w=np.ones(N,np.float32)
  if c in ['ep-comping','farfisa','vibrafono']:w*=1-.35*vocal
  if c in ['chelo','fuelle-alto','fuelle-bajo']:w[(tt>=40*BAR)&(tt<52*BAR)]*=1.5
  if c=='ep-tema':w[(tt>=52*BAR)&(tt<64*BAR)]*=1.15;w[tt>=76*BAR]*=.5
  if c in ['resonador-A','resonador-coma','batidos']:w[tt>=76*BAR]*=2.8
  if c in ['radio-izq','radio-der','telar']:w[tt>=76*BAR]*=1.4
  # Rampas suaves entre planos; los eventos musicales conservan sus ataques.
  from scipy.ndimage import uniform_filter1d
  w=uniform_filter1d(uniform_filter1d(w,round(SR*.035)),round(SR*.035));x*=w[:,None];g=next(g for g,cs in FAMILIAS.items() if c in cs);groups[g]+=x;y+=x
  if c not in FAMILIAS['bajos']+['kick','hats','ride']:send+=x*(.07 if c=='voz' else .13)
  info['capas'][c]={'RMS_activo_filtrado':ar,'ganancia':gain,'pico':float(abs(x).max()),'eventos':len(P['eventos'][c]),'pasa_altas_Hz':hp};del x;gc.collect()
 info['secciones']={}
 for s in P['secciones']:
  i,j=round(s['t']*SR),round(s['t1']*SR);info['secciones'][s['id']]={g:float(10*np.log10((np.mean(v[i:j]**2)+1e-15)/(np.mean((y[i:j]-v[i:j])**2)+1e-15))) for g,v in groups.items()}
 for g in groups.values():g.flush()
 del groups,g;gc.collect()
 for delay,level in [(.21,.27),(.43,.14)]:
  k=round(delay*SR);y[k:,0]+=send[:-k,1]*level;y[k:,1]+=send[:-k,0]*level
 del send;y*=np.minimum(1,np.maximum(0,(P['duracion']-tt)/2))[:,None];y*=.78/(abs(y).max()+1e-12)
 print('Rejilla: lectura de toda la mezcla',flush=True);z,gr=grid_fijado(y,out,work,tag)
 # La eliminación de DC por columnas puede dejar offset al final; sellar el silencio DESPUÉS.
 z*=np.minimum(1,np.maximum(0,(P['duracion']-tt)/.35))[:,None];z[-round(.09*SR):]=0;wav(work/'mezcla-rejilla.wav',z)
 first=subprocess.run(['ffmpeg','-hide_banner','-i',str(work/'mezcla-rejilla.wav'),'-af','loudnorm=I=-15:TP=-2.2:LRA=12:print_format=json','-f','null','-'],capture_output=True,text=True,check=True);met=json.loads(re.findall(r'\{[^{}]+\}',first.stderr)[-1]);flt=f"loudnorm=I=-15:TP=-2.2:LRA=12:measured_I={met['input_i']}:measured_TP={met['input_tp']}:measured_LRA={met['input_lra']}:measured_thresh={met['input_thresh']}:offset={met['target_offset']}:linear=true"
 subprocess.run(['ffmpeg','-n','-v','error','-i',str(work/'mezcla-rejilla.wav'),'-af',flt,'-ar','48000','-c:a','pcm_f32le',str(master())],check=True);aac(master().with_suffix('.m4a'),master())
 r=subprocess.run(['ffmpeg','-hide_banner','-i',str(master().with_suffix('.m4a')),'-af','loudnorm=I=-15:TP=-2.2:LRA=12:print_format=json','-f','null','-'],capture_output=True,text=True,check=True);info['aac']=json.loads(re.findall(r'\{[^{}]+\}',r.stderr)[-1]);info['rejilla']=gr;jsave(out/'mezcla-medidas.json',info)
 for label,a,b in [('tema-y-motor',24*BAR,36*BAR),('fuelle-y-chelo',40*BAR,52*BAR),('solo-D',52*BAR,64*BAR),('tema-otro-cuerpo',64*BAR,76*BAR)]:
  subprocess.run(['ffmpeg','-n','-v','error','-ss',str(a),'-i',str(master()),'-t',str(b-a),'-c:a','aac','-b:a','256k',str(out/f'{label}-s{SEED}-{tag}.m4a')],check=True)
 f,ax=figura('El acorde vuelve con otro cuerpo','Audio terminado · treinta capas · Rejilla de magnitud y fase · tres apariciones humanas',2);ax[0].plot(tt[::128],z[::128,0],color='#e9b46e',lw=.4);ax[0].set_xlabel('segundos');ax[0].set_title('Forma de la mezcla');ax[1].specgram(z.mean(1)[::4],NFFT=1024,Fs=SR/4,noverlap=768,cmap='magma',vmin=-100,vmax=-30);ax[1].set_yscale('log');ax[1].set_ylim(50,4000);ax[1].set_xlabel('segundos');salva(f,out/'proceso'/f'05-mezcla-y-rejilla-s{SEED}-{tag}.png');print(info['aac'],gr,flush=True)
if __name__=='__main__':main()
