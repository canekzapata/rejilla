"""Check delivered samples, source identity, voice presence and continuous organ state."""
from pathlib import Path
import json,hashlib,gzip,math,subprocess,gc
import numpy as np
from scipy.io import wavfile
BASE=Path(__file__).resolve().parent;OUT=BASE/(BASE/'REALIZACION-ACTUAL.txt').read_text().strip()
P=json.loads((OUT/'partitura.json').read_text(encoding='utf8'));R=json.loads((OUT/'mezcla-r2.json').read_text(encoding='utf8'))
sr,x=wavfile.read(OUT/R['salida_wav']);assert sr==48000;x=x.astype(np.float32)/2147483648;N=len(x)
assert N==round(P['duracion']*sr);assert np.isfinite(x).all();assert len(R['partes'])==36
assert all(v['pico_mezclado']>0 for v in R['partes'].values())
cuts=[]
for c in P['cortes_buses']:
    a,b=round(c['t']*sr),round(c['fin']*sr);peak=float(np.max(abs(x[a:b])))
    assert peak==0,(c,peak);cuts.append(dict(t=c['t'],fin=c['fin'],pico=peak))
def read(name,a=0,b=P['duracion']):
    with gzip.open(OUT/'render'/(name+'.f32.gz'),'rb') as f:f.seek(round(a*sr)*8);data=f.read(round((b-a)*sr)*8)
    return np.frombuffer(data,dtype='<f4').reshape(-1,2).copy()
voice=np.zeros_like(x)
for name in ['voz','duo','corocuerda','corojunco']:voice+=read('mezclada-r1-'+name)
balances={}
for s in P['secciones']:
    a,b=round(s['t']*sr),round(s['fin']*sr);v=voice[a:b];m=x[a:b]/10**(R['ganancia_estatica_db']/20)
    count=len(v)//2400
    if not count:continue
    env=np.sqrt(np.mean(v[:count*2400].reshape(count,2400,2)**2,axis=(1,2)));on=env>max(1e-8,env.max()*.10)
    if not on.any():continue
    mask=np.repeat(on,2400);v=v[:len(mask)][mask];rest=(m[:len(mask)]-voice[a:a+len(mask)])[mask]
    balances[s['id']]=float(10*np.log10((np.mean(v**2)+1e-20)/(np.mean(rest**2)+1e-20)))
del voice;gc.collect()
states=json.loads((OUT/'organo-estados.json').read_text(encoding='utf8'));counts={}
for t in [55,154]:
    state={}
    for e in states['cambios']:
        if e['t']<=t:state[e['divisor']]=e['activo']
    counts[str(t)]=sum(state.values())
assert counts=={'55':3,'154':5},counts
e=P['eventos']['junco1'][0];tone=read('junco1',e['t']+.3,e['t']+1.8).mean(1);n=2**math.ceil(math.log2(len(tone)*8));sp=abs(np.fft.rfft(tone*np.hanning(len(tone)),n));fr=np.fft.rfftfreq(n,1/sr);target=e['hz'];ix=np.where((fr>target*.97)&(fr<target*1.03))[0];k=ix[np.argmax(sp[ix])];l=np.log(sp[k-1:k+2]+1e-20);delta=.5*(l[0]-l[2])/(l[0]-2*l[1]+l[2]);f=(k+delta)*sr/n;cents=1200*np.log2(f/target);assert abs(cents)<.5,cents
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
fixed=BASE/'luciernagas-reescritura-s1-29d4afe5aad2'/'partitura-v8.json';assert sha(fixed)==sha(OUT/'partitura.json')
report={'sr':sr,'canales':2,'muestras':N,'duracion_s':N/sr,'partes_no_mudas':36,'muestras_finitas':True,
 'pico_wav':float(np.max(abs(x))),'cortes_despues_efectos_y_limitador':cuts,'organo_divisores_activos':counts,
 'junco_captacion_hz':f,'junco_objetivo_hz':target,'junco_error_cents':cents,'voz_contra_resto_durante_frase_db':balances,
 'partitura_fuente_sin_cambios':True,'wav_sha256':sha(OUT/R['salida_wav']),'aac_sha256':sha(OUT/R['salida_aac'])}
with open(OUT/'validacion-sonora.json','x',encoding='utf8') as out:json.dump(report,out,ensure_ascii=False,indent=1)
print(json.dumps(report,ensure_ascii=False))
