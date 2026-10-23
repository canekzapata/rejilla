"""Render de las capas propias. Fuentes temporales, luego adaptadas a Rejilla por DFT.
Procesa una capa a la vez; rechaza archivos existentes.
"""
import importlib.util,sys,gc
from comun import *
from hielo import *
from scipy.signal import butter,sosfilt
def importar(name,path):
 sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def main():
 out=ultimo();P=jleer(out/'partitura.json');red=jleer(out/'red.json');tag=out.name.split('-')[-1];run=BASE/'render'/tag;N=round(P['duracion']*SR)
 factor=red['f0']/red['placas'][0]['f0'];red['octavacion']=factor
 for m in red['modos'].values():m['octavacion']=factor
 alpha=red['alpha'];TT=importar('lago_tt',BASE/'fuentes/instrumentos-de-tres-tiempos/motores.py');TF=importar('lago_telar',BASE/'fuentes/telar-de-fase/motor.py')
 chosen=sys.argv[1:] or list(P['eventos']);medidas={}
 def store(c,y):
  assert np.isfinite(y).all(),c
  guardar(run/(c+'.f32'),np.asarray(y,dtype='float32').tobytes());print(c,'rms activo',round(activo(y),6),'pico',round(float(abs(y).max()),4),flush=True)
  return {'activo':activo(y),'pico':float(abs(y).max()),'eventos':len(P['eventos'][c])}
 for c in chosen:
  es=P['eventos'][c]
  if c in ['sabina-M','sabina-T','chops','piano','chelo','clarinete','metal']:continue
  if (run/(c+'.f32')).exists():print('ya existe; se conserva',c,flush=True);continue
  if c in ['fotones','androide','terminal']:
   y,_,info=TT.render(c,{'notas':es,'controles':{'vector_x':[[0,.1],[P['compas']*64,.85],[P['compas']*80,.2],[P['duracion'],.6]],'vector_y':[[0,.1],[P['compas']*64,.2],[P['compas']*80,.8],[P['duracion'],.4]]}},P['duracion'],sr=SR,semilla=SEED)
   medidas[c]=store(c,y);del y;gc.collect();continue
  if c.startswith('telar'):
   notes=[{**e,'t':e['t'],'cuerpo':e['cuerpo']} for e in es];y,rec=TF.render({'notas':notes},P['duracion'],sr=SR,semilla=SEED);medidas[c]=store(c,y);jguardar(run/(c+'-recibos.json'),rec);del y;gc.collect();continue
  y=np.zeros((N,2),np.float32)
  if c.startswith('bateria'):
   kit='bateria-tr808' if c=='bateria808' else 'bateria-frito';cache={}
   for e in es:
    iv=int(np.argmin(abs(np.array([.3,.6,.9])-e['vel'])));key=(e['pieza'],iv)
    if key not in cache:cache[key]=np.fromfile(run/f'{kit}-{key[0]}-{iv}.f32',np.float32)
    poner(y,cache[key],e['t'],p=e['pan'])
  elif c=='ep2':
   A=importar('lago_ep2',BASE/'fuentes/ep2/motor.py');e=es[0];dur=e['dur'];sc={'angulo_monodromia_phi':[[0,0],[dur,4*np.pi]],'eventos':[{'t0':0,'dur':dur,'f_pivote':P['f0']*4,'vel':.8,'eta_jordan':.15}]}
   sig,tr=A.render_monodromia_berry_ep2(sc,duracion=dur,sr=SR,semilla=SEED);poner(y,sig,e['t']);
   jguardar(out/'ep2-traza.json',{'t':(np.arange(0,len(sig),SR//8)/SR).tolist(),'f_plus':tr['f_hoja_pos'][::SR//8].tolist(),'f_minus':tr['f_hoja_neg'][::SR//8].tolist(),'limite':'seguimiento espectral sonificado; no integración de estado no hermítico'})
  elif c in ['campo-H','campo-U']:
   for e in es:
    n=round(e['dur']*SR);t=np.arange(n)/SR;x=np.zeros(n);f=hz(e['midi']);ratios=np.arange(1,17) if c=='campo-H' else 1/np.arange(1,13)
    for j,ratio in enumerate(ratios):
     fr=f*ratio*(1+e.get('stretch',0)*np.sin(j*.8))
     if 25<fr<SR*.4:x+=np.sin(2*np.pi*fr*t+.2*j)/(1+j)**1.05
    poner(y,.1*x*env(n,.4,.8),e['t'],e['vel'],p=(-.4 if c=='campo-H' else .4))
  else:
   for k,e in enumerate(es):
    v=e['vel'];p=e['pan'];t=e['t'];cell=str(e.get('celda',red['placas'][k%32]['id']));mod=red['modos'][cell]
    if c.startswith('grietas'):
     rr=e['distancia'] if c.endswith('lejos') else max(1,e['distancia']*.12)
     sig=fractura(rr,alpha,e['compensacion'] if c.endswith('lejos') else 0,semilla=227+e['arista']);
     # e.t es la llegada a 1200 Hz; el impulso nominal se coloca antes.
     tau=(1-e['compensacion'])*rr/(2*np.sqrt(alpha*2*np.pi*1200)) if c.endswith('lejos') else 0
     poner(y,sig,t-tau-LEAD,v,p)
    elif c.startswith('cunas'):
     sig=placa(mod,dur=.9,borde=True,memoria=e['memoria']);poner(y,sig,t,v,p)
    elif c=='lago':poner(y,red_modal(red,e['estado'],int(cell),e['dur']),t,v,p)
    elif c=='arco':poner(y,arco(mod,e['midi'],e['dur'],e['presion'],e['velocidad']),t,v,p)
    elif c.startswith('voc-hielo'):
     # Fuente sostenida de placa: articulación por modo y excitaciones repetidas,
     # no normalización individual ni alargamiento de un golpe aislado.
     sig=arco(mod,e['midi'],e['dur'],e['presion'],.35);poner(y,sig,t,v,p)
    elif c=='voc-cunas':
     for tt in np.arange(0,e['dur'],.11):poner(y,placa(mod,e['midi'],dur=.22,borde=True),t+tt,v*.5,p)
    elif c=='voc-terminal':
     local={**e,'t':0};sig,_,_=TT.render('terminal',{'notas':[local],'controles':{'vector_x':[[0,.1],[e['dur'],.9]],'vector_y':[[0,.4]]}},e['dur']+.3,SR,SEED);poner(y,sig,t,v)
    elif c=='sub':
     n=round((e['dur']+.2)*SR);tt=np.arange(n)/SR;sig=.5*np.sin(2*np.pi*hz(e['midi'])*tt)*env(n,.008,.12);poner(y,sig,t,v,0)
    elif c=='deshielo':
     n=round(.4*SR);tt=np.arange(n)/SR;f=hz(e['midi']);sig=.3*np.sin(2*np.pi*f*(tt+.06*(1-np.exp(-tt/.04))))*np.exp(-tt*20)*env(n,.002,.03);poner(y,sig,t,v,p)
    elif c=='escarcha':
     # La rapidez pasa de eventos separados a rugosidad periódica; contactos
     # con modos de borde y microimpactos de ruido fijados por la red.
     n=round(.4*SR);tt=np.arange(n)/SR;rng=np.random.default_rng(SEED+k);pulse=(np.maximum(0,np.sin(2*np.pi*max(2,e['rapidez'])*tt))**16)
     sig=sosfilt(butter(2,[2500,11000],btype='bandpass',fs=SR,output='sos'),rng.normal(0,.4,n))*pulse*np.exp(-tt*12)*env(n,.001,.04);poner(y,sig,t,v,p)
  medidas[c]=store(c,y);del y;gc.collect()
 if medidas:jguardar(run/f'render-python-{hashlib.sha256("-".join(medidas).encode()).hexdigest()[:12]}.json',{'octavacion_modelo':factor,'capas':medidas})
if __name__=='__main__':main()
