"""Instrumentos propios del lago y compensación de dispersión en banda limitada.

Transformada exp(-iwt): propagación exp(-ir sqrt(w/alpha)). Precompensación de FASE,
sin invertir pérdidas. Las bandas se vuelven a reunir cuando lambda=1.
"""
import numpy as np
from scipy.signal import butter,sosfilt,resample_poly
from comun import SR,env
LEAD=1.
def banda(f):
 w=np.clip((f-70)/80,0,1)*np.clip((9000-f)/1800,0,1)
 return np.sin(w*np.pi/2)**2
def dispersar(x,r,alpha,compensacion=0,sr=SR,perdidas=True):
 f=np.fft.rfftfreq(len(x),1/sr);k=np.sqrt(2*np.pi*f/alpha)
 A=(1+.0015*r*np.sqrt(f/1000))**-1 if perdidas else np.ones(len(f))
 return np.fft.irfft(np.fft.rfft(x)*banda(f)*A*np.exp(-1j*(1-compensacion)*r*k),len(x))
def fractura(r,alpha,compensacion=0,energia=1,sr=SR,semilla=227):
 n=round(3*sr);t=np.arange(n)/sr-LEAD;rng=np.random.default_rng(semilla)
 x=np.exp(-(t/.0007)**2)*rng.normal(0,1,n)
 x=sosfilt(butter(2,[110,8500],btype='bandpass',fs=sr,output='sos'),x)*3.5
 return dispersar(x,r,alpha,compensacion,sr)*energia/(1+.05*r)
def placa(mod,midi=None,dur=1.3,borde=False,memoria=0,sr=SR):
 f=np.asarray(mod['f'])*mod.get('octavacion',1);g=np.asarray(mod['borde' if borde else 'centro'])**2
 if midi is not None:f=f*(440*2**((midi-69)/12)/f[0])
 t=np.arange(round((dur+.8)*sr))/sr;y=np.zeros(len(t));f=f/(1+.035*memoria)
 for j,(ff,gg) in enumerate(zip(f,g)):
  if ff>sr*.43:continue
  decay=(1.5+.4*j)/(1+.18*memoria)
  y+=gg*np.exp(-decay*t)*np.sin(2*np.pi*ff*t+.11*j)/(1+j*.35)
 return .12*y*env(len(y),.001,.08,sr)
def arco(mod,midi,dur=2,presion=.45,velocidad=.35,sr=SR):
 # Rotaciones exactas de osciladores amortiguados, forzados por fricción dependiente
 # de la velocidad modal del contacto. Integración explícita de la fuerza a 8192 Hz.
 sr0=8192;n=round((dur+.5)*sr0);f=np.asarray(mod['f'][:7]);f*=440*2**((midi-69)/12)/f[0]
 good=f<sr0*.35;f=f[good];w=np.asarray(mod['borde'][:7])[good];w=w/(np.linalg.norm(w)+1e-9)
 c=np.cos(2*np.pi*f/sr0);s=np.sin(2*np.pi*f/sr0);d=np.exp(-(1.1+np.arange(len(f))*.35)/sr0)
 q=np.zeros(len(f));v=q.copy();y=np.zeros(n);e=env(n,.12,.3,sr0)
 for i in range(n):
  relative=velocidad*(.8+.2*np.sin(2*np.pi*.63*i/sr0))-float(w@v)*1.5
  F=presion*(np.exp(-4*abs(relative))*np.tanh(35*relative)+.02*relative)*e[i]
  qn=d*(c*q+s*v);v=d*(-s*q+c*v)+w*F*.016;q=qn;y[i]=w@q
 return resample_poly(y*3.0,sr,sr0)
def red_modal(red,estado,celda,dur=4,sr=SR):
 est=red['estados'][estado];f=np.asarray(est['frecuencias'])*red.get('octavacion',1);U=np.asarray(est['vectores']);i=[p['id'] for p in red['placas']].index(celda)
 g=U[i]**2;t=np.arange(round(dur*sr))/sr;y=np.zeros(len(t))
 for j,ff in enumerate(f):y+=g[j]*np.sin(2*np.pi*ff*t)*np.exp(-(1.1+.04*j)*t)
 return .35*y*env(len(y),.008,.15,sr)
