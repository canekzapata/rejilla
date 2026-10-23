"""Read the fixed engines, full states and actual complex trajectories at 48 kHz."""
import sys,json,time,importlib.util,math,gc,gzip,os
from pathlib import Path
import numpy as np
from scipy.signal import sosfilt,butter,resample_poly
BASE=Path(__file__).resolve().parent
OUT=Path(os.environ['LUCI_AUDIO_OUT']) if 'LUCI_AUDIO_OUT' in os.environ else BASE/(BASE/'REALIZACION-ACTUAL.txt').read_text().strip()
FIX=BASE/'luciernagas-reescritura-s1-29d4afe5aad2'/'realizacion'
P=json.loads((OUT/'partitura.json').read_text(encoding='utf8'));SR=48000;N=round(P['duracion']*SR)
SOURCES=OUT/'fuentes';SOURCES.mkdir(exist_ok=True)
# Only output storage and observation traces change; the recurrence and engine equations stay fixed.
source=(FIX/'motores.py').read_text(encoding='utf8')
source=source.replace('t=reloj(d,sr); n=len(t); B=max(32,round(sr*.003))','n=round(d*sr); B=max(32,round(sr*.003))')
source=source.replace('out=np.zeros((n,2)); trace=[]','out=np.zeros((n,2),np.float32); trace=[]')
source=source.replace("controls={'energia_'+str(k):np.interp(t,tt[:,0],tt[:,k+1]) for k in range(voices)}", "controls={'tiempos':tt[:,0],**{'energia_'+str(k):tt[:,k+1] for k in range(voices)}}")
source=source.replace('audio.astype(np.float32),traces,info','audio.astype(np.float32,copy=False),traces,info')
source=source.replace('np.interp(t,vt,vf[:,k])','np.interp(t+s.get(\'_offset\',0),vt,vf[:,k])')
modpath=SOURCES/'motores_con_observacion_ligera.py'
if not modpath.exists():modpath.write_text(source,encoding='utf8')
spec=importlib.util.spec_from_file_location('luci_motores',modpath);M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
def save(name,y):
    f=OUT/'render'/(name+'.f32.gz')
    with gzip.open(f,'xb',compresslevel=3) as out:
        for i in range(0,len(y),48000):out.write(y[i:i+48000].astype('<f4',copy=False).tobytes())
    peak=0.;ss=0.
    for i in range(0,len(y),48000):
        block=y[i:i+48000].astype(float);peak=max(peak,float(np.max(abs(block))));ss+=float(np.sum(block**2))
    print(name,'pico',peak,'rms',float(np.sqrt(ss/y.size)),flush=True)
def poner(out,y,t):
    i=round(t*SR);j=min(N,i+len(y))
    if j>i:out[i:j]+=y[:j-i]
def modales():
    sys.path.insert(0,str(FIX/'biblioteca'/'motores'));import rejilla as R
    for name,ficha in [('pua','rejilla-pixeles-guitarra-cortada'),('bajo','rejilla-pixeles-bajo-dedos')]:
        if (OUT/'render'/(name+'.f32.gz')).exists():continue
        K=json.loads((FIX/'biblioteca'/'fichas'/(ficha+'.json')).read_text(encoding='utf8'));out=np.zeros((N,2),np.float32)
        for e in P['eventos'][name]:
            modes=R.modos(K,e['midi'],0,e['vel'],tonica='E',dur=e['dur'],ny=SR*.44)
            d=min(3,e['dur']+.3);y=R.tiempo(modes,d,SR);pan=e['pan'];yy=M.estereo(y,pan);poner(out,yy,e['t'])
        save(name,out);del out;gc.collect()
def originales(names):
    for name in names:
        if (OUT/'render'/(name+'.f32.gz')).exists():continue
        start=time.time();s={'notas':P['eventos'][name],**P.get('controles',{}).get(name,{})};offset=0
        if name=='cuerda':s['base_midi']=64
        if name=='sala':
            offset=min(e['t'] for e in s['notas']);s['notas']=[dict(e,t=e['t']-offset) for e in s['notas']]
            s['controles']={k:[[0,float(np.interp(offset,*np.array(v).T))]]+[[t-offset,g] for t,g in v if t>offset] for k,v in s['controles'].items()}
        if name=='boca':
            out=np.zeros((N,2),np.float32);groups=[]
            for e in s['notas']:
                if not groups or e['t']>max(z['t']+z['dur'] for z in groups[-1])+.15:groups.append([])
                groups[-1].append(e)
            for group in groups:
                a=max(0,min(e['t'] for e in group)-.08);b=max(e['t']+e['dur'] for e in group)+.12
                part={**s,'_offset':a,'notas':[dict(e,t=e['t']-a) for e in group],
                      'consonantes':[[t-a,ph,v] for t,ph,v in s.get('consonantes',[]) if a<=t<=b]}
                y,_,_=M.render('boca',part,b-a,SR,P['semilla']);poner(out,y,a)
            save(name,out);del out
        else:
            y,trace,info=M.render(name,s,P['duracion']-offset,SR,P['semilla'])
            if offset:
                out=np.zeros((N,2),np.float32);poner(out,y,offset);save(name,out);del out
            else:save(name,y)
            if name in ['arpa','cuerda']:
                observation={k:v[::max(1,len(v)//2000)].tolist() for k,v in trace.items()}
                (OUT/(name+'-estados.json')).write_text(json.dumps(observation),encoding='utf8')
            del y,trace,info
        gc.collect();print(name,round(time.time()-start,1),'s',flush=True)
def juncos():
    for name in ['junco1','junco2','junco3','junco4']:
        if (OUT/'render'/(name+'.f32.gz')).exists():continue
        out=np.zeros((N,2),np.float32)
        for e in P['eventos'][name]:
            d=e['dur'];padding=.006 if e.get('plan') else 0
            tt=np.arange(-round(padding*SR),round((d+padding)*SR))/SR
            f=440*2**((e['midi']-69)/12);k=np.log(2)*(e.get('midi_fin',e['midi'])-e['midi'])/(12*d)
            phase=e.get('fase_inicial_rad',0)+(2*np.pi*f*tt if abs(k)<1e-12 else 2*np.pi*f*np.expm1(k*tt)/k)
            amp=e.get('amplitud_relativa',np.sqrt(e.get('masa',0)))
            # The first captured packet is raw. Apply its declared one-time active
            # normalization on entering Junco. The plans already contain that scale.
            if 'estado_complejo' in e:amp*=274.4515488228
            amp*=e.get('vel',1.)
            # Linear overlap of adjacent plan amplitudes for 12 ms; no phase reset.
            ramp=.012;w=np.minimum(1,np.maximum(0,(tt+padding)/ramp))*np.minimum(1,np.maximum(0,(d+padding-tt)/ramp))
            for at,gain in e.get('ganancia_cortes',[]):w*=np.where(e['t']+tt>=at,gain,1)
            if not e.get('plan'):w*=np.exp(-np.maximum(0,tt)*.20)
            y=np.cos(phase)*amp*w
            poner(out,M.estereo(y,e['pan']),e['t']-padding)
        save(name,out);del out;gc.collect()
def campana():
    import subprocess
    label='campana-v10' if '10.1' in P.get('version','') else 'campana'
    script=OUT/'fuentes'/(label+'-realizar.mjs')
    origin=P['eventos']['campana'][0]['t'];events=[dict(e,t=e['t']-origin+.05) for e in P['controles']['campana']['eventos']]
    script.write_text("import{render}from"+json.dumps((FIX/'campana-motor.mjs').as_uri())+";import fs from 'node:fs';const r=render({events:"+json.dumps(events)+"},2,48000);let o=new Float32Array(r.left.length*2);for(let i=0;i<r.left.length;i++){o[2*i]=r.left[i];o[2*i+1]=r.right[i];}fs.writeFileSync(process.argv[2],Buffer.from(o.buffer));console.log(r.metrics);",encoding='utf8')
    raw=OUT/'render'/(label+'-corto.raw');subprocess.run(['node',str(script),str(raw)],check=True)
    y=np.fromfile(raw,dtype='<f4').reshape(-1,2);out=np.zeros((N,2),np.float32);poner(out,y[round(.05*SR):],P['eventos']['campana'][0]['t']);save(label,out)
def vocoders():
    sys.path.insert(0,str(BASE.parent/'cuento-en-siete'));import sintes as S
    for name,carrier in [('corocuerda','cuerda'),('corojunco',None)]:
        es=P['eventos'][name];a=max(0,min(e['t'] for e in es)-.25);b=max(e['t']+e['dur'] for e in es)+.3;i=round(a*SR);j=round(b*SR)
        mod=read('prosodia-'+name,i,j).mean(1).astype(float)
        if carrier:car=read(carrier,i,j).mean(1).astype(float)
        else:
            car=sum(read(f'junco{k}',i,j).mean(1).astype(float) for k in range(1,5))
            level=np.sqrt(np.mean(car**2));car=np.tanh(car/(level+1e-9)*2.3)
        y=S.vocoder(mod,car,consonantes=.27,bandas=30);out=np.zeros((N,2),np.float32)
        pan=es[0]['pan'];poner(out,M.estereo(y,pan),a);save(name,out);del out;gc.collect()
def read(name,i=0,j=N):
    if name.startswith('junco') and (OUT/'render'/(name+'-fusion.f32.gz')).exists():name+='-fusion'
    with gzip.open(OUT/'render'/(name+'.f32.gz'),'rb') as f:
        f.seek(i*8);data=f.read((j-i)*8)
    return np.frombuffer(data,dtype='<f4').reshape(-1,2).copy()
if __name__=='__main__':
    job=sys.argv[1]
    if job=='modales':modales()
    elif job=='juncos':juncos()
    elif job=='campana':campana()
    elif job=='vocoders':vocoders()
    else:originales(sys.argv[1:])
