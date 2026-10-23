"""Láser de transbordos, membrana cargada y raspador de depósitos.
Tres instrumentos de primera etapa, no mezcla completa.
"""
from comun import *
from scipy.signal import lfilter,butter,sosfilt,resample_poly
from scipy.linalg import eigh
from scipy.ndimage import gaussian_filter1d
from scipy.interpolate import CubicSpline
from fractions import Fraction
def matriz_cruce(k):return 2*np.ones((k,k))/k-np.eye(k)
def red_laser(x,estado=0,sr=SR,cola=1.5,perdida=.78,impulso=False):
 # Grafo fijo del laberinto; los retardos proceden de longitudes del abanico muestreado.
 S=leer(depo());path=np.array(S['caminos'][min(len(S['caminos'])-1,estado*16)]);U=np.array(S['u']);V=np.array(S['v']);rr=np.linspace(0,len(path)-1,6).astype(int);pts=np.column_stack([U[rr,path[rr]],V[rr,path[rr]]]);km=leer(ultimo()/'datos/terreno-22.json')['anchoKm'];edges=[(0,1),(1,2),(2,3),(3,4),(4,5),(2,4),(1,3)]
 # Rutas adicionales 2-4 y 1-3 son transbordos compuestos, no cauces afirmados del terreno.
 lengths=np.array([np.linalg.norm(pts[a]-pts[b])*km*1000 for a,b in edges]);delays=np.maximum(24,np.round(lengths/343/16*sr)).astype(int);directed=[]
 for k,(a,b) in enumerate(edges):directed.extend([(a,b,k),(b,a,k)])
 # Implementación por bloques: cada arco tiene retardo entero >= tamaño de bloque.
 n=len(x)+round(cola*sr);buf=np.zeros((len(directed),n+int(delays.max())+2),np.float64);y=np.zeros((n,2));nodes=sorted(set(a for a,b,k in directed));incoming={v:[i for i,(_,b,_) in enumerate(directed) if b==v] for v in nodes};outgoing={v:[i for i,(a,_,_) in enumerate(directed) if a==v] for v in nodes};block=int(min(delays));energy_in=float(np.sum(x*x));peak_state=0
 # Las columnas se ordenan por arco/vecino de igual modo a ambos lados del cruce.
 for t in range(0,n,block):
  z=min(n,t+block);l=z-t
  for v in nodes:
   inc=incoming[v];outs=outgoing[v];A=buf[inc,t:z].copy();d=len(inc);mix=matriz_cruce(d)@A
   if v==0 and t<len(x):
    stop=min(z,len(x));mix[:, :stop-t]+=x[t:stop][None,:]/np.sqrt(d)
   if v in [3,5]:y[t:z,int(v==5)]+=A.sum(0)/np.sqrt(d)*.22
   for j,idx in enumerate(outs):
    # Una pérdida fija atenúa cada arco, sin normalizar sus cruces.
    k=directed[idx][2];delay=delays[k];end=min(n+int(delays.max()),t+delay+l);buf[idx,t+delay:end]+=mix[j,:end-t-delay]*perdida
   peak_state=max(peak_state,float(abs(mix).max()))
 return y.astype('float32'),{'longitudes_m':lengths.tolist(),'retardos_s':(delays/sr).tolist(),'compresion_distancias':16,'estado_deposito':estado,'grafo':edges,'perdida_por_arco':perdida,'energia_entrada':energy_in,'energia_salidas':float(np.sum(y*y)),'pico_estado':peak_state,'nota':'red activa por inyección y lectura; cruces ortogonales, pérdidas explícitas; no simulación de láser óptico'}
def chirp(midi=69,dur=.36,vel=.7):
 sr=SR*4;t=np.arange(round((dur+.12)*sr))/sr;target=float(hz(midi));f=target*(1+3*np.exp(-t/.045));phase=2*np.pi*np.cumsum(f)/sr;y=(np.sin(phase)+.17*np.sin(2*phase))*.3*vel*np.exp(-t/((dur+.1)*.7));y*=np.minimum(1,t/.004)*np.minimum(1,np.maximum(0,(dur+.12-t)/.08));return resample_poly(y,1,4).astype('float32')
def laser_frase(notes,duracion,estado=0):
 x=np.zeros(round(duracion*SR))
 for e in notes:
  y=chirp(e.get('midi',69),e.get('dur',.3),e.get('vel',.7));i=round(e['t']*SR);n=min(len(y),len(x)-i)
  if n>0:x[i:i+n]+=y[:n]
 # Talbot existente transforma una célula completa antes de entrar a la red.
 TT=importar(BASE/'fuentes/talbot/tapete.py','baila_talbot');tau=Fraction(0) if estado==0 else Fraction(1,3) if estado<10 else Fraction(2,5);z=TT.talbot(x,tau,hilos=32);y,meta=red_laser(z,estado);meta['talbot_tau']=str(tau);meta['Talbot_diferencia_energia']=float(abs(np.sum(z*z)-np.sum(x*x))/(np.sum(x*x)+1e-20));return y,meta
def modos_membrana(carga=3.,rad=.43,n=64,mmax=4):
 # Elementos finitos radiales lineales, cuadratura Gauss; membrana con densidad central.
 rs=np.linspace(0,1,n+1);gx,gw=np.polynomial.legendre.leggauss(4);allm=[]
 for m in range(mmax+1):
  K=np.zeros((n+1,n+1));M=np.zeros_like(K)
  for e in range(n):
   a,b=rs[e:e+2];r=(a+b)/2+gx*(b-a)/2;w=gw*(b-a)/2;N=np.array([(b-r)/(b-a),(r-a)/(b-a)]);d=np.array([-1,1])/(b-a);rho=1+carga*np.exp(-(r/rad)**8);ke=np.outer(d,d)*np.sum(w*r)+np.einsum('q,iq,jq->ij',w*m*m/r,N,N);me=np.einsum('q,iq,jq->ij',w*r*rho,N,N);K[e:e+2,e:e+2]+=ke;M[e:e+2,e:e+2]+=me
  ix=np.arange(0 if m==0 else 1,n);val,vec=eigh(K[np.ix_(ix,ix)],M[np.ix_(ix,ix)],subset_by_index=[0,4]);
  for j,z in enumerate(val):
   shape=np.zeros(n+1);shape[ix]=vec[:,j];allm.append((float(np.sqrt(z)),m,shape))
 allm.sort(key=lambda x:x[0]);f0=allm[0][0];return [(f/f0,m,s) for f,m,s in allm],rs
_MEM={}
def membrana(golpe='din',f0=146.832,dur=1.,carga=3.,vel=.7):
 key=float(carga)
 if key not in _MEM:_MEM[key]=modos_membrana(carga)
 modes,rs=_MEM[key];n=round(dur*SR);t=np.arange(n)/SR;rin=.08 if golpe=='din' else .62 if golpe=='ta' else .38;rout=.41;z=np.zeros(n)
 for ratio,m,sh in modes[:18]:
  if f0*ratio>SR*.4:continue
  gain=np.interp(rin,rs,sh)*np.interp(rout,rs,sh)*np.cos(m*.73)/(1+ratio)**1.2
  decay=(.7 if golpe=='din' else .09 if golpe=='ta' else .4)/(1+.12*ratio);f=f0*ratio
  if golpe=='thom':phase=2*np.pi*f*(t+.015*(1-np.exp(-t/.08)))
  else:phase=2*np.pi*f*t
  z+=gain*np.sin(phase)*np.exp(-t/decay)
 # Un mismo factor por todos los golpes y cargas: no igualar individualmente sus niveles.
 z*=.018*vel*env(n,.001,.04);return z.astype('float32')
def raspador(perfil,duracion=3.,speed=1.,seed=SEED):
 # Lectura espacial con punta unilateral suave; el perfil real se amplía como superficie.
 r=np.linspace(0,1,len(perfil));p=np.asarray(perfil,float);p=p-np.linspace(p[0],p[-1],len(p));p/=max(1,float(np.ptp(p)));t=np.arange(round(duracion*SR))/SR;travel=np.minimum(.999999,t/duracion*speed);curve=CubicSpline(r,p)(travel);smooth=gaussian_filter1d(curve,SR*.003);contact=np.maximum(0,np.diff(smooth,prepend=smooth[0]));rng=np.random.default_rng(seed);noise=rng.normal(0,1,len(t));exc=contact*noise*50
 z=np.zeros(len(t))
 for f,decay in [(430,.07),(1180,.045),(2710,.025)]:
  rad=np.exp(-1/(decay*SR));w=2*np.pi*f/SR;z+=lfilter([1-rad],[1,-2*rad*np.cos(w),rad*rad],exc)
 z=sosfilt(butter(2,5500,fs=SR,output='sos'),z)*env(len(t),.02,.1)*.8;return z.astype('float32'),{'contacto_suma':float(np.sum(contact)),'contactos_positivos':int(np.sum(contact>1e-7)),'perfil_sha256':hashlib.sha256(np.asarray(perfil).tobytes()).hexdigest()}
def auxiliar(tipo='barro',vel=.6,seed=SEED):
 """Cuerpo hueco modal o pandero ruidoso. Aproximaciones sintéticas, sin calibración tradicional."""
 n=round(.65*SR);t=np.arange(n)/SR;rng=np.random.default_rng(seed);noise=rng.normal(0,1,n);z=np.zeros(n)
 if tipo=='barro':
  for f,tau,amp in [(196,.11,1),(547,.07,.45),(937,.045,.25)]:z+=amp*np.sin(2*np.pi*f*t)*np.exp(-t/tau)
  z+=sosfilt(butter(2,[500,3500],btype='bandpass',fs=SR,output='sos'),noise)*np.exp(-t*85)*.15
 else:
  z=membrana('ta',196,.65,vel=.7)*3
  z+=sosfilt(butter(2,[2500,7500],btype='bandpass',fs=SR,output='sos'),noise)*np.exp(-t*32)*.09
 return (z*.12*vel*env(n,.001,.03)).astype('float32')
