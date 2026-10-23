from comun import *
from instrumentos import pecho,vocoder
from partitura import figura,salva
from scipy.signal import butter,sosfiltfilt,correlate
out=ultimo();tag=out.name.split('-')[-1];y=np.fromfile(run()/'sabina-prueba.f32',np.float32);dark=pecho(y,.8);G=importar(lib()/'motores/gemelo.py','gemelo_prueba');K=leer(lib()/'fichas/mbira.json');carrier=np.zeros(len(y))
for j,t in enumerate([.15,.6,1.05,1.5,1.95,2.4,2.85,3.3,3.75]):
 v=G.nota(K,54+[0,0,3,2,0,-2,0,-2,0][j],.75,segundos=1.3,sr=SR,tonica='F#');i=round(t*SR);n=min(len(v),len(y)-i);carrier[i:i+n]+=v[:n]
talk=vocoder(y,np.tanh(carrier*5))+.18*carrier
versions=[y,dark,talk];seq=[]
for v in versions:
 v=v*.35/max(activo(v),1e-9);v=sosfiltfilt(butter(2,60,btype='highpass',fs=SR,output='sos'),v);seq.extend([v,np.zeros(SR//2)])
z=np.concatenate(seq);z*=.85/max(abs(z).max(),1e-9);w=out/f'prueba-tres-voces-graves-s{SEED}-{tag}.wav';wav(w,pan(z));aac(w.with_suffix('.m4a'),w)
raw('prueba-pecho',dark);raw('prueba-mbira-vocal',talk)
P=leer(out/'partitura.json');pitches=[]
for e in P['prueba_voz']:
 i=round((e['t']+.12)*SR);v=dark[i:i+round(.18*SR)];v-=v.mean();c=correlate(v,v,method='fft')[len(v)-1:];expected=float(hz(e['nota']));a=int(SR/(expected*1.15));b=int(SR/(expected*.87));lag=a+np.argmax(c[a:b]);pitches.append({'silaba':e['texto'],'esperada_Hz':expected,'periodicidad_local_Hz':SR/lag})
jsave(out/'prueba-voz-medidas.json',{'orden':['Sabina PSOLA grave sin cambio de formantes','misma voz, envolvente espectral a 0.8 y cuerpo paralelo','mbira original saturada como portadora de las mismas sílabas'],'segundos':len(z)/SR,'periodicidades':pitches,'nota':'medida local condicionada al entorno de la nota esperada; no evaluación de inteligibilidad ni escucha propia'})
f,ax=figura('El pulgar adquiere una garganta','Tres ensayos reales · misma frase y registro · seco / pecho / lengüeta vocalizada',2)
for v,label,col in zip(versions,['seco','pecho','mbira'],['#b1a0ff','#ff9769','#80d9ce']):
 Z=np.abs(np.fft.rfft(v));freq=np.fft.rfftfreq(len(v),1/SR);ax[0].semilogx(freq,20*np.log10(Z/max(Z.max(),1e-9)+1e-7),label=label,color=col,lw=.65)
ax[0].set_xlim(65,7000);ax[0].set_ylim(-85,2);ax[0].legend();ax[0].set_xlabel('Hz');ax[1].plot(np.arange(len(z))/SR,z,lw=.4,color='#ff9769');ax[1].set_xlabel('segundos');salva(f,out/'proceso'/f'04-tres-voces-graves-s{SEED}-{tag}.png')
print(w.with_suffix('.m4a'))
