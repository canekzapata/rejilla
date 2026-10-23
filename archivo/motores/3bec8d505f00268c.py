import numpy as np, sys
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
sr,x=wavfile.read(sys.argv[1]); m=x.astype(float).mean(1)/32768
T=131072/52429
secs=[('intro',0,4),('verso',4,12),('coro',12,20),('verso2',20,28),('quiebre',36,40),('final',40,48),('outro',48,52)]
bands=[('sub',20,80),('low',80,250),('mid',250,2000),('pres',2000,6000),('air',6000,20000)]
fb={n:sosfilt(butter(4,[lo,hi],'bandpass',fs=sr,output='sos') if hi<sr/2 else butter(4,lo,'highpass',fs=sr,output='sos'),m) for n,lo,hi in bands}
print('sección    rms   '+'  '.join(f'{n:>6s}' for n,_,_ in bands))
for s,a,b in secs:
    i,j=int(a*T*sr),int(b*T*sr); r=20*np.log10(m[i:j].std())
    print(f'{s:9s} {r:6.1f} '+'  '.join(f'{20*np.log10(fb[n][i:j].std())-r:6.1f}' for n,_,_ in bands))
