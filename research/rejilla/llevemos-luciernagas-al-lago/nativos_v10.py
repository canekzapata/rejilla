"""Observación a 48 kHz de los controladores canónicos de guitarra, cuerda y junco."""
import numpy as np
import sys,json,math,gc
from audio_v10 import context,save,dump,SR,stage
from instrumentos import Guitarra,hz
from modelos_memoria import complejo,pares

def guitar():
    out,p=context();nframes=round(p['duracion']*SR);audio=np.zeros((nframes,2),np.float32)
    g=Guitarra();events=sorted(p['eventos']['guitarra'],key=lambda e:e['t']);slips=sorted([(e['t']+s,e) for e in events for s in e.get('contacto',{}).get('deslizamientos_s',[])],key=lambda a:a[0])
    source=json.loads((out/'inicio.json').read_text(encoding='utf8'))['partitura'];from pathlib import Path
    rows=json.loads((Path(source)/'datos/recorrido.json').read_text(encoding='utf8'))['muestras'];rt=np.array([r['t'] for r in rows]);slope=np.array([r['pendiente'] for r in rows])
    axis=np.array([.7,.3,1.]);length=np.linalg.norm(axis);u=axis/length;K=np.array([[0,-u[2],u[1]],[u[2],0,-u[0]],[-u[1],u[0],0]])
    h=np.arange(1,9);ei=si=0;t=0.;checkpoint=None;trace=[];rng=np.random.default_rng(p['semilla'])
    # Carrier frequency is bounded before observation, including all eight modes.
    while t<p['duracion']-1e-10:
        while ei<len(events) and events[ei]['t']<=t+1e-9:
            e=events[ei];ei+=1
            if e['articulacion']!='contacto':g.gesto(**e['parametros_motor'])
        while si<len(slips) and slips[si][0]<=t+1e-9:
            at,e=slips[si];si+=1;g.z[e['cuerda'],e['caja']]+=.28*np.sin(np.pi*h*e['nodo'])/h**1.2*np.exp(1j*h*(.37+(at-e['t'])*.8))
        if checkpoint is None and abs(t-105.4)<1e-9:
            checkpoint={'z':pares(g.z.ravel()),'phase':g.phase.tolist()}
        step=min(.005,p['duracion']-t)
        if ei<len(events) and events[ei]['t']>t+1e-9:step=min(step,events[ei]['t']-t)
        if si<len(slips) and slips[si][0]>t+1e-9:step=min(step,slips[si][0]-t)
        if t<105.4-1e-9:step=min(step,105.4-t)
        mid=t+step/2;active=[e for e in events if e.get('contacto') and e['t']<=mid<e['t']+e['dur']];continuous=[]
        for e in active:
            curve=np.array(e['contacto']['curva']);pr=np.interp(mid-e['t'],curve[:,0],curve[:,1]);drive=.055*max(0,pr-e['contacto']['umbral'])*step/.005
            continuous.append((e,drive*np.sin(np.pi*h*e['nodo'])/h**1.2*np.exp(1j*h*(.37+(mid-e['t'])*.8))))
        xs=np.zeros(3)
        for meet in p['encuentros_v10']:
            if meet['t']<=mid:xs=np.asarray(meet['despues'])
        wet=.05 if mid<29.1 else .65;pressure=float(np.clip(.3+6*abs(np.interp(mid,rt,slope)),0,1))
        f=hz(g.midi)[:,None,None]*2**(xs[None,:,None]/1200)*h
        assert f.max()<SR*.44
        old=g.z.copy();ph=g.phase.copy();g.phase=(g.phase+2*np.pi*f*step)%(2*np.pi)
        g.z*=np.exp(-step*(.4+.13*h+1.2*wet));angle=(.1+pressure)*step*length;R=np.eye(3)+math.sin(angle)*K+(1-math.cos(angle))*(K@K)
        g.z=np.einsum('ab,sbh->sah',R,g.z)
        for e,increment in continuous:g.z[e['cuerda'],e['caja']]+=increment
        a=round(t*SR);b=round((t+step)*SR);size=b-a
        if size:
            # Interpolate envelope only; oscillator phase is continuous through every gate.
            sel=np.flatnonzero(np.maximum(abs(old.ravel()),abs(g.z.ravel()))>1e-10)
            tt=np.arange(size)/SR;uu=np.clip(tt/step,0,1)
            if len(sel):
                envelope=old.ravel()[sel,None]*(1-uu)+g.z.ravel()[sel,None]*uu
                y=np.real(envelope*np.exp(1j*(ph.ravel()[sel,None]+2*np.pi*f.ravel()[sel,None]*tt)))
                box=(sel//8)%3;st=sel//24;pan=-.78+.22*box+.08*(st-2.5);weights=np.array([1,.2,-.15])[box]
                audio[a:b,0]+=(y*(np.cos((pan+1)*np.pi/4)*weights)[:,None]).sum(0)
                audio[a:b,1]+=(y*(np.sin((pan+1)*np.pi/4)*weights)[:,None]).sum(0)
            if active:
                scratch=sum(.028*np.interp(mid-e['t'],*np.array(e['contacto']['curva']).T)*(1+e['contacto']['pelicula']) for e in active)
                noise=rng.normal(0,1,size);audio[a:b,0]+=noise*scratch*.8;audio[a:b,1]+=noise*scratch*.3
        t+=step
        if len(trace)<int(t):trace.append([t,float(np.sum(abs(g.z)**2))])
    ref=p['centro_v10']['paquete']['guitarra_captacion'];zc=complejo(checkpoint['z']);zr=complejo(ref['z_completo'])
    err=float(np.max(abs(zc-zr)));pe=float(np.max(abs(np.exp(1j*np.array(checkpoint['phase']))-np.exp(1j*np.array(ref['phase'])))))
    assert err<1e-8 and pe<1e-7,(err,pe)
    dump(out/'guitarra-estados-v10.json',{'captacion_105_4':checkpoint,'error_z_canonico':err,'error_fase_canonica':pe,'traza_norma':trace,'dt_max':.005,'muestreo_audio':SR,'sin_reinicio_por_ventana':True})
    save(out,'guitarra',audio);print('Captación guitarra verificada',err,pe,flush=True)

def cuerda():
    out,p=context();N=round(p['duracion']*SR);audio=np.zeros((N,2),np.float32);state=np.zeros((3,7),complex);phase=np.zeros_like(state.real)
    h=np.arange(1,8);base=float(hz(64));freq=np.array([base*h,base*h*1.003,base*np.array([1,2.76,5.40,8.93,13.34,18.64,24.8])]);target=freq.copy();events=sorted(p['eventos']['cuerda'],key=lambda e:e['t']);ei=0;t=0.;cp=None
    ctrl=p['controles']['cuerda']['controles'];pressure=np.array(ctrl['presion']);bow=np.array(ctrl['arco']);ix=[0,1,2,4]
    while t<p['duracion']-1e-10:
        while ei<len(events) and events[ei]['t']<=t+1e-9:
            e=events[ei];ei+=1
            if e.get('inyeccion_modal'):
                state[:]=0;phase[:]=0;state[0,ix]=complejo(e['inyeccion_modal']['z'])
                freq=np.array([base*h,base*h*1.003,base*np.array([1,2.76,5.40,8.93,13.34,18.64,24.8])]);target=freq.copy()
            else:
                state[min(2,int(e.get('cuerda',0)))]+=e['vel']*.27/h**1.3;target=freq*(float(hz(e['midi']))/freq[0,0])
        if cp is None and abs(t-116.2)<1e-9:cp=state[0,ix]*np.exp(1j*phase[0,ix])
        step=min(.003,p['duracion']-t)
        if ei<len(events) and events[ei]['t']>t+1e-9:step=min(step,events[ei]['t']-t)
        for boundary in [106.2,116.2]:
            if t<boundary-1e-9:step=min(step,boundary-t)
        old=state.copy();ph=phase.copy();state*=np.exp(-step/np.array([2.9,1.25,.42])[:,None]*(1+np.arange(7)[None,:]*.21))
        if not (106.2-1e-9<=t<116.2-1e-9):freq+=(target-freq)*(1-np.exp(-step/.025))
        pr=float(np.interp(t,pressure[:,0],pressure[:,1]));br=float(np.interp(t,bow[:,0],bow[:,1]));state[1]+=br*step*.12/h**1.7
        for v,w,angle in [(0,1,(.1+pr*1.3)*step),(1,2,(.1+pr*1.3)*step*.85)]:
            x,y=state[v].copy(),state[w].copy();state[v]=np.cos(angle)*x-np.sin(angle)*y;state[w]=np.sin(angle)*x+np.cos(angle)*y
        phase=(phase+2*np.pi*freq*step)%(2*np.pi)
        a,b=round(t*SR),round((t+step)*SR)
        if b>a:
            tt=np.arange(b-a)/SR;uu=np.clip(tt/step,0,1);z=old[:,:,None]*(1-uu)+state[:,:,None]*uu
            y=np.real(z*np.exp(1j*(ph[:,:,None]+2*np.pi*freq[:,:,None]*tt))).sum(1)
            for v,pan in enumerate([-.6,0,.6]):audio[a:b,0]+=y[v]*math.cos((pan+1)*np.pi/4);audio[a:b,1]+=y[v]*math.sin((pan+1)*np.pi/4)
        t+=step
    ref=complejo(p['centro_v10']['paquete']['junco_z']);err=float(np.max(abs(cp-ref)));assert err<1e-8,err
    dump(out/'cuerda-estados-v10.json',{'captacion_116_2':pares(cp),'error_canonico':err,'dt_max':.003,'recepcion_asigna_estado_completo':True})
    save(out,'cuerda',audio);print('Captación cuerda verificada',err,flush=True)

def juncos():
    out,p=context();N=round(p['duracion']*SR);outputs=[np.zeros((N,2),np.float32) for _ in range(4)];maxerr=0.
    for seg in p['centro_v10']['segmentos']:
        a,b=round(seg['t']*SR),round(seg['fin']*SR);tt=np.arange(b-a)/SR;dur=seg['fin']-seg['t']
        mids=np.array(seg['midi_inicio']);ends=np.array(seg['midi_fin']);z0=complejo(seg['z_inicio']);k=np.log(2)*(ends-mids)/(12*dur)
        phase=np.array([2*np.pi*hz(m)*(tt if abs(kk)<1e-12 else np.expm1(kk*tt)/kk) for m,kk in zip(mids,k)])
        z=z0[:,None]*np.exp(-np.array(seg['gamma'])[:,None]*tt)*np.exp(1j*phase)
        if seg.get('cruce'):
            c=seg['cruce'];i,j=c['par'];ang=c['angulo_rad']*np.clip((seg['t']+tt-(seg['fin']-c['aplicar_antes_de_fin_s']))/c['aplicar_antes_de_fin_s'],0,1);zi,zj=z[i].copy(),z[j].copy();z[i]=np.cos(ang)*zi-np.sin(ang)*zj;z[j]=np.sin(ang)*zi+np.cos(ang)*zj
        for voice in range(4):
            pan=next(s['pan'] for s in p['partes'] if s['id']==f'junco{voice+1}');y=z[voice].real*.25
            outputs[voice][a:b,0]+=y*math.cos((pan+1)*np.pi/4);outputs[voice][a:b,1]+=y*math.sin((pan+1)*np.pi/4)
    maxf=0
    for voice in range(4):
        name=f'junco{voice+1}'
        for e in p['eventos'][name]:
            if 'segmento_centro' in e:continue
            dur=e['dur'];padding=.006 if e.get('plan') else 0
            a=round((e['t']-padding)*SR);b=min(N,round((e['t']+dur+padding)*SR));tt=np.arange(b-a)/SR-padding
            f=hz(e['midi']);f1=hz(e.get('midi_fin',e['midi']));maxf=max(maxf,f,f1);assert maxf<SR*.44
            k=np.log(2)*(e.get('midi_fin',e['midi'])-e['midi'])/(12*dur)
            phase=e.get('fase_inicial_rad',0)+2*np.pi*f*(tt if abs(k)<1e-12 else np.expm1(k*tt)/k)
            amp=e.get('amplitud_relativa',math.sqrt(e.get('masa',0)))*e['vel'];w=np.ones(len(tt))
            if e.get('plan'):w=np.minimum(1,np.maximum(0,(tt+padding)/.012))*np.minimum(1,np.maximum(0,(dur+padding-tt)/.012))
            for at,gain in e.get('ganancia_cortes',[]):w*=np.where(e['t']+tt>=at,gain,1)
            if not e.get('plan'):w*=np.exp(-e.get('amortiguacion_s_1',.2)*tt)
            y=np.cos(phase)*amp*w;pan=e['pan'];outputs[voice][a:b,0]+=y*math.cos((pan+1)*np.pi/4);outputs[voice][a:b,1]+=y*math.sin((pan+1)*np.pi/4)
        save(out,name+'-fusion',outputs[voice]);outputs[voice]=None;gc.collect()
    dump(out/'junco-fusiones-v10.json',{'centro':'fase analítica y rotación progresiva de los estados complejos canónicos','planes':24,'fmax_transporte_hz':float(maxf),'reinicio_por_ventana':False,'ganancia_inicial_ya_incluida_en_z':True,'gamma_por_voz':[.021,.034,.057,.088],'fusiones_s':.012,'borrador_anterior':'render/junco1..4.f32.gz conserva la primera observación sin rampas de fusión; no se usa en mezcla'})
    if not list((out/'proceso').glob('02-*.png')):stage(out,2,'Estados nativos convertidos a señal',['Guitarra: captación comprobada a 105.4 s','Cuerda: captación comprobada a 116.2 s','Juncos: cruces de 90 ms y fases analíticas','24 transportes nuevos; ningún tramo pegado del audio viejo'])
if __name__=='__main__':
    jobs={'guitarra':guitar,'cuerda':cuerda,'juncos':juncos}
    for name in sys.argv[1:]:jobs[name]()
