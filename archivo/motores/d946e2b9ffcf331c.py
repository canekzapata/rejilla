"""Treinta capas -> planos por sección -> imagen Rejilla -> máster de dos pasadas.
Guarda medidas y rechaza toda entrega ya existente. --medir no entrega máster.
"""
import gc,re,sys,importlib.util,io,os
from scipy.signal import butter,sosfiltfilt,oaconvolve,stft,istft
from scipy.io import wavfile
from PIL import Image
from comun import *
from laminas import *
NIVELES={'lago':-8,'grietas-cerca':-6,'grietas-lejos':0,'cunas-graves':-1,'cunas-agudas':-3,'arco':2,'escarcha':-10,'deshielo':-9,
 'bateria808':0,'bateria-frita':-7,'fotones':-6,'androide':1,'sub':-5,'piano':-2,'chelo':-4,'clarinete':-4,'metal':-5,'terminal':0,
 'sabina-M':3,'sabina-T':-2,'voc-hielo-M':0,'voc-hielo-T':-3,'voc-cunas':-4,'voc-terminal':2,'chops':-4,'telar-T':-2,'telar-solo':3,'campo-H':-12,'campo-U':-10,'ep2':0}
FAMILIAS={'materia':['lago','grietas-cerca','grietas-lejos','cunas-graves','cunas-agudas','arco','escarcha','deshielo'],
 'electro':['bateria808','bateria-frita','fotones','androide','sub'],'camara':['piano','chelo','clarinete','metal','terminal'],
 'voces':['sabina-M','sabina-T','voc-hielo-M','voc-hielo-T','voc-cunas','voc-terminal','chops'],'telar':['telar-T','telar-solo'],'campos':['campo-H','campo-U','ep2']}
def importar(path):
 sp=importlib.util.spec_from_file_location('lago_vocoder',path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);m.SR=SR;return m
def vocoder_bloques(mod,car,sn,consonantes=.3,paso_s=4):
 """Misma distribución de bandas del vocoder fijado, sin normalización por tramo.
 Contexto de 1/4 s y malla STFT alineada; sólo se conserva el centro de cada tramo.
 """
 n=len(mod);out=np.zeros(n,np.float32);step=round(paso_s*SR);context=SR//4;nper=1024;hop=256
 floor_car=max(float(abs(car).max())*.001,1e-8);floor_mod=max(float(abs(mod).max())*1e-5,1e-10)
 for start in range(0,n,step):
  end=min(n,start+step);a=max(0,start-context);b=min(n,end+context)
  if np.max(abs(mod[a:b]))<1e-8:continue
  f,_,M=stft(mod[a:b],SR,nperseg=nper,noverlap=nper-hop);_,_,C0=stft(car[a:b],SR,nperseg=nper,noverlap=nper-hop)
  B=sn._banco(f,30,90,7500).astype(np.float32);Em=B@abs(M);Ec=B@abs(C0)
  Em=np.apply_along_axis(lambda row:np.convolve(row,np.ones(3,dtype=np.float32)/3,'same'),1,Em)
  G=np.clip(Em/(Ec+floor_car),0,30)*(Em>floor_mod);cen=np.geomspace(90,7500,32)[1:-1];low=cen<260
  if low.any():G[low]=np.clip(Em[~low].sum(0)/(Ec[~low].sum(0)+floor_car),0,30)[None,:]
  W=B/(B.sum(0,keepdims=True)+1e-9);_,v=istft(C0*(W.T@G),SR,nperseg=nper,noverlap=nper-hop)
  v=v[:b-a];out[start:end]=v[start-a:end-a]
 sib=sosfiltfilt(butter(4,5000,btype='highpass',fs=SR,output='sos'),mod).astype(np.float32)
 return out+consonantes*sib
def grid(y,out,run,tag):
 cols=int(np.ceil(len(y)/SR));mx=0.;target=np.zeros_like(y)
 def coef(i):
  block=np.zeros((SR,2),np.float32);n=min(SR,len(y)-i*SR);block[:n]=y[i*SR:i*SR+n]
  Z=np.fft.rfft(block,axis=0)/SR;Z[0]=0;Z[-1]=0;return Z,n
 for i in range(cols):
  Z,n=coef(i);mx=max(mx,float(abs(Z).max()));target[i*SR:i*SR+n]=np.fft.irfft(Z*SR,n=SR,axis=0)[:n]
 m16=np.zeros((SR,cols),dtype='<u2');p16=np.zeros_like(m16)
 for i in range(cols):
  Z,_=coef(i);Z=Z[:SR//2];mag=np.concatenate([abs(Z[:,1])[::-1],abs(Z[:,0])[::-1]]);phase=np.concatenate([np.angle(Z[:,1])[::-1],np.angle(Z[:,0])[::-1]])
  m16[:,i]=np.round(mag/mx*65535).astype('<u2');p16[:,i]=np.round((phase+np.pi)/(2*np.pi)*65535).astype('<u2')
 mr=run/'master.mag.raw';pr=run/'master.fase.raw';guardar(mr,m16.tobytes());guardar(pr,p16.tobytes())
 for name,a in [('magnitud',m16),('fase',p16)]:
  b=io.BytesIO();Image.fromarray(a).save(b,format='PNG');guardar(out/f'rejilla-{name}-s227-{tag}.png',b.getvalue())
 inp=lambda p:['-f','rawvideo','-pix_fmt','gray16le','-s',f'{cols}x{SR}','-r','1','-i',str(p)]
 dest=run/'master-spectrumsynth.wav';subprocess.run(['ffmpeg','-n','-v','error',*inp(mr),*inp(pr),'-filter_complex',f'[0]setpts=N/TB,format=gray16le[m];[1]setpts=N/TB,format=gray16le[p];[m][p]spectrumsynth=sample_rate={SR}:channels=2:scale=lin:slide=fullframe:win_func=rect:overlap=0','-c:a','pcm_f32le',str(dest)],check=True)
 _,z=wavfile.read(dest);got=z[:len(y)]*mx;snr=float(20*np.log10(np.linalg.norm(target)/(np.linalg.norm(target-got)+1e-15)))
 assert snr>50,('SNR Rejilla',snr)
 return got,{'SNR_sin_DC_Nyquist_dB':snr,'SNR_original_dB':float(20*np.log10(np.linalg.norm(y)/(np.linalg.norm(y-got)+1e-15))),'columnas':cols,'filas_canal':SR//2,'magnitud_max':mx,'origen':'DFT de motores temporales; lectura efectiva de toda la mezcla por spectrumsynth'}
def main():
 out=ultimo();P=jleer(out/'partitura.json');tag=out.name.split('-')[-1];run=BASE/'render'/tag;N=round(P['duracion']*SR);tt=np.arange(N)/SR;sn=importar(BASE/'fuentes/vocoder/sintes.py');Q=P['negra'];BAR=P['compas']
 def leer(c):
  file={'chops':'sabina-chops'}.get(c,c);x=np.fromfile(run/(file+'.f32'),np.float32)
  if c in ['piano','chelo','clarinete','metal','sabina-M','sabina-T','chops','sabina-solo']:x=pan(x,{'piano':-.25,'chelo':-.35,'clarinete':.35,'metal':-.15,'sabina-M':-.12,'sabina-T':.15}.get(c,0))
  else:x=x.reshape(-1,2)
  assert len(x)==N,(c,len(x),N)
  return x
 work=run/('mezcla-'+hashlib.sha256(os.urandom(20)).hexdigest()[:12]);work.mkdir(exist_ok=False)
 y=np.zeros((N,2),np.float32);send=np.zeros_like(y);groups={g:np.memmap(work/(g+'.grupo.f32'),mode='w+',shape=(N,2),dtype='float32') for g in FAMILIAS}
 for g in groups.values():g[:]=0
 duck=np.ones(N,np.float32)
 for e in P['eventos']['bateria808']:
  if e['pieza']!='kick':continue
  i=round(e['t']*SR);n=min(round(.23*SR),N-i);duck[i:i+n]=np.minimum(duck[i:i+n],1-.28*np.exp(-np.arange(n)/(.07*SR)))
 medidas={}
 for c in NIVELES:
  print('mezcla',c,flush=True)
  if c.startswith('voc-'):
   cache=run/(c+'-procesado-bloques-v2.f32')
   if cache.exists():x=np.fromfile(cache,np.float32).reshape(-1,2)
   else:
    mod=leer('sabina-solo' if c=='voc-terminal' else ('sabina-T' if c.endswith('-T') else 'sabina-M')).mean(1)
    car=leer(c).mean(1);v=vocoder_bloques(mod,car,sn,consonantes=.22 if c=='voc-cunas' else .32);x=pan(v,{'voc-hielo-M':-.25,'voc-hielo-T':.3,'voc-cunas':.2,'voc-terminal':0}[c]);guardar(cache,x.astype('float32').tobytes());del car,mod,v
  else:x=leer(c)
  fc=32 if c in ['lago','sub','ep2'] else (90 if c.startswith('voc') or c=='sabina-T' else 120 if c=='sabina-M' else 42)
  x=sosfiltfilt(butter(2,fc,btype='highpass',fs=SR,output='sos'),x,axis=0).astype(np.float32)
  a=activo(x);assert a>1e-8,(c,'muda');gain=10**((-25+NIVELES[c])/20)/a;x*=gain
  # Automatizaciones de función: los solos tienen su lugar y el acompañamiento responde.
  w=np.ones(N,np.float32)
  if c=='arco':w[(tt>=48*BAR)&(tt<64*BAR)]*=1.5
  if c=='telar-solo':w[(tt>=64*BAR)&(tt<80*BAR)]*=2.4
  if c=='terminal':w[(tt>=64*BAR)&(tt<80*BAR)]*=1.8
  if c in FAMILIAS['voces']:w[(tt>=8*BAR)&(tt<32*BAR)]*=1.6
  if c in ['bateria808','bateria-frita','androide','fotones']:
   w[(tt>=64*BAR)&(tt<80*BAR)]*=.65;w[(tt>=8*BAR)&(tt<32*BAR)]*=.9
  if c in ['campo-H','campo-U','telar-T']:w[(tt>=32*BAR)&(tt<48*BAR)]*=.65
  x*=w[:,None]
  if c not in ['bateria808','bateria-frita','fotones','sub','grietas-cerca']:x*=duck[:,None]
  group=next(g for g,cs in FAMILIAS.items() if c in cs);groups[group]+=x;y+=x
  if c not in ['bateria808','bateria-frita','fotones','sub','androide','grietas-cerca']:send+=x*(.07 if c=='grietas-lejos' else .14)
  medidas[c]={'activo_crudo':a,'ganancia':gain,'pico_procesado':float(abs(x).max()),'eventos':len(P['eventos'][c])};del x;gc.collect()
 balance={}
 for sec in P['secciones']:
  i,j=round(sec['t']*SR),round(sec['t1']*SR);balance[sec['id']]={}
  for g,x in groups.items():
   v=np.asarray(x[i:j]);rest=y[i:j]-v;balance[sec['id']][g]=float(10*np.log10((np.mean(v*v)+1e-14)/(np.mean(rest*rest)+1e-14)))
 for g in groups.values():g.flush()
 info={'capas':medidas,'grupos_contra_resto_dB':balance,'niveles':NIVELES}
 if '--medir' in sys.argv:
  jguardar(work/'balance.json',info);print(json.dumps(balance,indent=1));return
 rng=np.random.default_rng(SEED);n=round(1.7*SR);t=np.arange(n)/SR
 for k in range(2):
  ir=rng.normal(0,1,n)*np.exp(-t*4.1);ir[:round(.022*SR)]=0;ir/=np.linalg.norm(ir);y[:,k]+=oaconvolve(send[:,k],ir,mode='full')[:N]*.35
 del groups,g,x,v,rest,send;gc.collect()
 y*=np.minimum(1,np.maximum(0,(P['duracion']-tt)/.45))[:,None];y*=.75/(abs(y).max()+1e-12)
 print('Rejilla: imagen y lectura de la mezcla completa',flush=True);z,gr=grid(y,out,work,tag);wav(work/'mezcla-rejilla.wav',z)
 first=subprocess.run(['ffmpeg','-hide_banner','-i',str(work/'mezcla-rejilla.wav'),'-af','loudnorm=I=-13.5:TP=-1.8:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
 met=json.loads(re.findall(r'\{[^{}]+\}',first.stderr)[-1]);flt=f"loudnorm=I=-13.5:TP=-1.8:LRA=9:measured_I={met['input_i']}:measured_TP={met['input_tp']}:measured_LRA={met['input_lra']}:measured_thresh={met['input_thresh']}:offset={met['target_offset']}:linear=true"
 name=out.name;master=out/(name+'.wav');subprocess.run(['ffmpeg','-n','-v','error','-i',str(work/'mezcla-rejilla.wav'),'-af',flt,'-ar','48000','-c:a','pcm_f32le',str(master)],check=True)
 subprocess.run(['ffmpeg','-n','-v','error','-i',str(master),'-c:a','aac','-b:a','256k','-movflags','+faststart',str(out/(name+'.m4a'))],check=True)
 check=subprocess.run(['ffmpeg','-hide_banner','-i',str(out/(name+'.m4a')),'-af','loudnorm=I=-13.5:TP=-1.8:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
 info['rejilla']=gr;info['aac']=json.loads(re.findall(r'\{[^{}]+\}',check.stderr)[-1]);jguardar(out/'mezcla-medidas.json',info)
 # Muestras de la música efectivamente mezclada, con sus tiempos de la partitura.
 for label,a,b in [('solo-D',64*BAR,80*BAR),('coral',32*BAR,48*BAR),('arco-en-contexto',48*BAR,56*BAR)]:
  dest=out/f'{label}-s227-{tag}.m4a';subprocess.run(['ffmpeg','-n','-v','error','-ss',str(a),'-i',str(master),'-t',str(b-a),'-c:a','aac','-b:a','224k',str(dest)],check=True)
 fig,ax=figura('El lago ya tiene treinta voces','Mezcla terminada · DFT → imágenes de magnitud/fase → spectrumsynth',2)
 ax[0].plot(tt[::128],z[::128,0],lw=.35,color=C[0]);ax[0].set_xlabel('segundos');ax[0].set_title('Forma y respiración',color=FG)
 ax[1].specgram(z.mean(1)[::4],NFFT=512,Fs=SR/4,noverlap=384,cmap='magma',vmin=-95,vmax=-25);ax[1].set_ylim(100,4000);ax[1].set_xlabel('segundos');ax[1].set_title('Campo de la mezcla',color=FG);salva(fig,out/'proceso'/f'05-mezcla-y-rejilla-s227-{tag}.png')
 print('MASTER',master,gr,info['aac'],flush=True)
if __name__=='__main__':main()
