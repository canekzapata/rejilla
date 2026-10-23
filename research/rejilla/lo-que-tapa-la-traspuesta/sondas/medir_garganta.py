import numpy as np, scipy.signal as ss, sys
from scipy.linalg import solve_toeplitz
y=np.fromfile(sys.argv[1],np.float32).astype(float);SR=48000
def formantes(x,orden=12):
    x=ss.resample_poly(x,1,4); sr=SR/4; x=x*np.hamming(len(x)); x=np.append(x[0],x[1:]-.9*x[:-1])
    r=np.correlate(x,x,'full')[len(x)-1:len(x)+orden+1]; r[0]*=1.0001
    a=solve_toeplitz(r[:-1],r[1:]);raices=np.roots(np.concatenate([[1],-a]));raices=raices[np.imag(raices)>0]
    f=np.angle(raices)*sr/2/np.pi;bw=-np.log(np.abs(raices))*sr/np.pi
    return sorted([round(x_) for x_,b in zip(f,bw) if 150<x_<4500 and b<600])[:4]
def f0(x):
    ac=np.correlate(x,x,'full')[len(x)-1:];lo=int(SR/600);hi=int(SR/60);k=lo+np.argmax(ac[lo:hi]);return round(69+12*np.log2(SR/k/440),2)
t=.1
for v in 'aeiou':
    seg=y[int((t+.3)*SR):int((t+.8)*SR)];print(v,'F',formantes(seg),'f0',f0(seg),'rms',round(float(np.sqrt(np.mean(seg**2))),3));t+=1.1
seg=y[int((t+.4)*SR):int((t+1.2)*SR)];print('montaña F',formantes(seg),'f0',f0(seg),'rms',round(float(np.sqrt(np.mean(seg**2))),3));t+=1.6
seg=y[int((t+.4)*SR):int((t+1.0)*SR)];print('bifonía f0',f0(seg),'rms',round(float(np.sqrt(np.mean(seg**2))),3));t+=1.4
for s in ['ka','sa','ta','pa','ma','la','rra']:
    seg=y[int(t*SR):int((t+.32)*SR)];e=[round(float(20*np.log10(np.sqrt(np.mean(seg[i:i+960]**2))+1e-9))) for i in range(0,len(seg)-960,1920)];print(s,e);t+=.4
