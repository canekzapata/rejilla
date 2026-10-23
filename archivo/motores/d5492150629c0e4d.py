"""Eco con captación musical, graves sobremuestreados y articulación de lengüetas."""
from comun import *
from scipy.signal import stft,istft,butter,sosfiltfilt,resample_poly,lfilter,iirpeak
from scipy.ndimage import gaussian_filter1d
def pecho(y,factor=.8):
 """Baja la envolvente espectral conservando las frecuencias de los parciales."""
 out=np.zeros_like(y);step=SR*4;context=SR//4
 for i in range(0,len(y),step):
  j=min(len(y),i+step);a=max(0,i-context);b=min(len(y),j+context)
  if abs(y[a:b]).max()<1e-9:continue
  f,t,Z=stft(y[a:b],SR,nperseg=1024,noverlap=768);log=gaussian_filter1d(np.log(abs(Z)+1e-6),7,axis=0)
  old=np.arange(len(f));ix=np.minimum(old/factor,len(f)-1);k=np.floor(ix).astype(int);r=ix-k;k1=np.minimum(k+1,len(f)-1)
  desired=log[k]*(1-r[:,None])+log[k1]*r[:,None];G=np.clip(np.exp(desired-log),.25,3)
  _,z=istft(Z*G,SR,nperseg=1024,noverlap=768);out[i:j]=z[i-a:j-a]
 low=sosfiltfilt(butter(3,[85,800],btype='bandpass',fs=SR,output='sos'),out)
 return (out*.78+np.tanh(low*4)*.22).astype('float32')
def vocoder(mod,car):
 """Adaptador del vocoder de El lago: piso global y contexto alineado a STFT."""
 n=len(mod);out=np.zeros(n,np.float32);step=4*SR;context=SR//4;fc=max(float(abs(car).max())*.001,1e-8);fm=max(float(abs(mod).max())*1e-5,1e-10)
 sn=importar(BASE/'fuentes/vocoder/sintes.py','corriente_voc');sn.SR=SR
 for i in range(0,n,step):
  j=min(n,i+step);a=max(0,i-context);b=min(n,j+context)
  if max(abs(mod[a:b]))<1e-8:continue
  f,t,M=stft(mod[a:b],SR,nperseg=1024,noverlap=768);_,_,C=stft(car[a:b],SR,nperseg=1024,noverlap=768);B=sn._banco(f,32,65,7000).astype('float32');Em=B@abs(M);Ec=B@abs(C)
  Em=np.apply_along_axis(lambda x:np.convolve(x,np.ones(3)/3,'same'),1,Em);G=np.clip(Em/(Ec+fc),0,24)*(Em>fm);W=B/(B.sum(0,keepdims=True)+1e-9)
  _,v=istft(C*(W.T@G),SR,nperseg=1024,noverlap=768);out[i:j]=v[i-a:j-a]
 return out
def bajo(e,kind='sub'):
 mul=1 if kind=='sub' else 4;sr=SR*mul;n=round((e['dur']+.12)*sr);t=np.arange(n)/sr;f=hz(e['midi']);prev=hz(e.get('prev',e['midi']));curve=f*(prev/f)**np.exp(-t/e.get('glide',.05));phase=2*np.pi*np.cumsum(curve)/sr
 if kind=='sub':y=np.sin(phase)+.12*np.sin(phase*2)
 elif kind=='cuerpo':y=np.tanh((np.sin(phase)+.35*np.sin(2*phase))*3)
 else:
  motion=.5+.5*np.sin(2*np.pi*(1.2+e.get('gesto',0)*.31)*t)**2
  y=np.sin(phase+(1+3*motion)*np.sin(phase*.5))+.35*np.sin(phase*1.007);y=np.tanh(y*2.7)
  y=sosfiltfilt(butter(3,2700,btype='lowpass',fs=sr,output='sos'),y)
 fade=np.minimum(1,t/.009)**2*np.minimum(1,np.maximum(0,(e['dur']+.12-t)/.12))**2;y*=fade*np.exp(-t/(1.4 if kind=='sub' else 3))*.45*e['vel']
 return resample_poly(y,1,mul).astype('float32') if mul>1 else y.astype('float32')
def boca_pulgar(car,events):
 """Lengüeta real como excitación: resonadores vocales móviles cada 4 ms."""
 vowels=np.array([[650,1050,2400],[280,650,2100],[400,800,2300],[350,1650,2450]])
 times=[0]+[e['t'] for e in events];targets=np.vstack([vowels[1],vowels[np.arange(len(events))%4]]);y=np.zeros(len(car),np.float32);zi=[np.zeros(2) for _ in range(3)];step=128
 for a in range(0,len(car),step):
  b=min(a+step,len(car));cent=(a+b)/2/SR;F=[np.interp(cent,times,targets[:,k]) for k in range(3)]
  for k in range(3):
   co,den=iirpeak(F[k],max(1,F[k]/[90,130,220][k]),fs=SR);v,zi[k]=lfilter(co,den,np.tanh(car[a:b]*5),zi=zi[k]);y[a:b]+=v*[2.7,1.7,.6][k]
 return y+.18*car
class Eco:
 def __init__(self,out,P):
  self.E=leer(out/'eco.json');self.P=P;self.K=np.array(self.E['K']);self.M=self.E['dimension'];self.N=self.E['N'];self.arr={}
  for c in ['ideal','viscoso']:
   for f in ['ida','vuelta']:self.arr[c,f]=np.memmap(out/f'{c}-{f}.f32',mode='r',dtype='float32',shape=(self.N+1,self.M))
  self.pos=np.where((self.K[:,0]>0)|((self.K[:,0]==0)&(self.K[:,1]>0))|((self.K[:,0]==0)&(self.K[:,1]==0)&(self.K[:,2]>0)))[0]
 def estado(self,t,kind):
  a=self.P['eco_musical']['fin_ida'];b=self.P['eco_musical']['fin_vuelta'];t=np.asarray(t);phase=np.where(t<a,0,np.where(t<b,1,2));u=np.zeros((len(t),self.M))
  for f,ind,frac in [('ida',phase==0,t/a),('vuelta',phase==1,(t-a)/(b-a))]:
   if not ind.any():continue
   ix=np.clip(frac[ind],0,1)*self.N;lo=np.floor(ix).astype(int);r=ix-lo;hi=np.minimum(lo+1,self.N)
   def sample(k):v=self.arr[k,f];return v[lo]*(1-r[:,None])+v[hi]*r[:,None]
   u[ind]=sample('ideal') if kind=='ideal' else sample('viscoso') if kind=='viscoso' else sample('viscoso')-sample('ideal')
  ind=phase==2
  if ind.any():u[ind]=np.array(self.E['ideal']['retornado'] if kind=='ideal' else self.E['viscoso']['retornado'] if kind=='viscoso' else self.E['residuo'])
  return u.reshape(-1,len(self.K),3,2)
 def audio(self,kind='residuo',midi=42,moving=False):
  D=self.P['duracion'];n=round(D*SR);out=np.zeros((n,2),np.float32);base=float(hz(midi));Q=self.P['negra'];B=self.P['compas'];phase=0.;weights=np.array([[1,.22,.12],[.22,1,.12]])
  for start in range(0,n,SR*2):
   end=min(n,start+SR*2);tt=np.arange(start,end)/SR;small=np.arange(start/SR,end/SR+1/100,1/100);u=self.estado(small,kind);pickup=.4+(.9*np.sin(small*.21) if moving else np.zeros_like(small));ang=self.K[self.pos,2][None,:]*pickup[:,None];cc=np.cos(ang);ss=np.sin(ang);coeff=[]
   picked=np.take(u,self.pos,axis=1)
   for ch in range(2):
    r=np.einsum('tpc,c->tp',picked[:,:,:,0],weights[ch]);im=np.einsum('tpc,c->tp',picked[:,:,:,1],weights[ch]);coeff.append(2*((r*cc-im*ss)+1j*(r*ss+im*cc)))
   if moving:
    controls=self.P['gestos_captador'];f=np.interp(tt,[0]+[c['t'] for c in controls]+[D],[base]+[float(hz(c['nota'])) for c in controls]+[base]);pp=phase+2*np.pi*np.cumsum(f)/SR;phase=float(pp[-1])
   else:pp=2*np.pi*base*tt
   for h in sorted(set(self.K[self.pos,:3]@np.array([1,3,7]))):
    if h==0:continue
    ix=np.where((self.K[self.pos,:3]@np.array([1,3,7]))==h)[0]
    for ch in range(2):
     z=coeff[ch][:,ix].sum(1);r=np.interp(tt,small,z.real);im=np.interp(tt,small,z.imag);out[start:end,ch]+=(r*np.cos(h*pp)-im*np.sin(h*pp)).astype('float32')*.28
  # Fade at both polarity changes; field comparisons remain unmodified.
  for t in [self.P['eco_musical']['fin_ida'],self.P['eco_musical']['fin_vuelta']]:
   i=round(t*SR);a=max(0,i-512);b=min(n,i+512)
   if b>a:out[a:b]*=np.abs(np.linspace(-1,1,b-a))[:,None]
  out*=np.minimum(1,np.arange(n)/SR/.15)[:,None];return out
