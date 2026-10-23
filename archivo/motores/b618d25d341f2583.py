"""Doce prototipos offline. Audio propio; numpy/scipy, sin servicios ni muestras.

API: render(nombre, partitura, duracion, sr=32000, semilla=19103419).
Partitura: notas [{t,dur,midi,vel,pan}], controles {nombre:[[t,valor],...]},
vocales [[t,'a'],...], consonantes [[t,'s',intensidad],...], enlaces [[t,a,b,angulo],...].
Las energías de las redes modales son normas de envolventes, no julios acústicos.
"""
import numpy as np
from scipy.signal import lfilter, butter, sosfilt, iirpeak, resample_poly

SR = 32000
VOCALES = {'a': [730,1090,2440,3400], 'e': [500,1800,2600,3500],
           'i': [290,2300,3000,3600], 'o': [470,850,2500,3400],
           'u': [350,700,2400,3300]}
NOMBRES = {'boca':'Boca de tres tiempos', 'cuerda':'Cuerda de cuerpos incompatibles',
 'piano':'Piano de tres presentes', 'arpa':'Arpa que presta su vibración',
 'organo':'Órgano de divisores con memoria', 'sala':'Sala plegada que se toca',
 'cristal':'Cristal orbital', 'estacion':'Cuerdas de estación', 'terminal':'Terminal vectorial',
 'plasma':'Plumón de plasma', 'androide':'Bajo de androide', 'fotones':'Batería de fotones'}

def hz(m): return 440 * 2**((np.asarray(m)-69)/12)
def reloj(d,sr): return np.arange(round(d*sr))/sr
def control(s,k,t,default=0):
    pts=s.get('controles',{}).get(k,[[0,default]])
    return np.interp(t,*np.asarray(pts,float).T)
def envolvente(n,sr,a=.012,r=.07):
    t=np.arange(n)/sr
    return np.sin(np.minimum(1,t/max(a,1/sr))*np.pi/2)**2 * np.sin(np.minimum(1,(n/sr-t)/max(r,1/sr))*np.pi/2)**2
def estereo(y,p=0):
    a=(np.asarray(p)+1)*np.pi/4
    return np.column_stack((y*np.cos(a),y*np.sin(a)))
def poner(dst,y,t,sr,g=1,p=0):
    i=round(t*sr); off=max(0,-i); i=max(0,i); n=min(len(y)-off,len(dst)-i)
    if n>0: dst[i:i+n]+=g*(estereo(y[off:off+n],p) if y.ndim==1 else y[off:off+n])
def fase(f,sr): return 2*np.pi*np.cumsum(np.broadcast_to(f,np.shape(f)))/sr
def fuente(f,sr,aire=0,seed=0):
    ph=fase(f,sr); y=np.zeros(len(ph)); lim=min(44,int(sr*.43/max(1,float(np.max(f)))))
    for h in range(1,lim+1): y+=np.sin(h*ph)/(h**1.25)
    if aire: y+=np.random.default_rng(seed).normal(0,aire,len(y))
    return y*.36
def suavizar(x,sr,tau=.012):
    a=np.exp(-1/(sr*tau)); return lfilter([1-a],[1,-a],x)
def perfil_notas(s,t,sr,default=57):
    f=np.full(len(t),float(hz(default))); amp=np.zeros(len(t))
    for e in s.get('notas',[]):
        i=round(e['t']*sr); n=min(round(e['dur']*sr),len(t)-i)
        if i<0 or n<=0: continue
        f[i:]=hz(e['midi']); amp[i:i+n]=float(e.get('vel',.8))*envolvente(n,sr,e.get('ataque',.04),e.get('soltar',.09))
    # Interpolate pitch in log space, preserving full-interval pitch curves.
    a=np.exp(-1/(sr*.009)); smooth,_=lfilter([1-a],[1,-a],np.log(f),zi=[np.log(f[0])*a])
    return np.exp(smooth),amp

def formantes(x,formants,sr):
    """Parallel resonators, 4 ms coefficient updates, filter state never reset."""
    out=np.zeros(len(x)); B=max(32,round(sr*.004)); z=[np.zeros(2) for _ in range(4)]
    for i in range(0,len(x),B):
        j=min(len(x),i+B)
        for k,weight in enumerate([1.0,.62,.27,.10]):
            f=float(formants[k][(i+j-1)//2]); bandwidth=[85,110,170,240][k]
            b,a=iirpeak(min(f,sr*.42),max(1,f/bandwidth),fs=sr)
            v,z[k]=lfilter(b,a,x[i:j],zi=z[k]); out[i:j]+=weight*v
    return out

def render_boca(s,d,sr,seed):
    t=reloj(d,sr); f,amp=perfil_notas(s,t,sr)
    f*=2**((3.5*np.sin(2*np.pi*5.1*t)*control(s,'vibrato',t,.3))/1200)
    vs=s.get('vocales',[[0,'a'],[d,'u']]); vt=np.array([p[0] for p in vs]); vf=np.array([VOCALES[p[1]] for p in vs])
    curves=np.array([np.interp(t,vt,vf[:,k]) for k in range(4)])
    rng=np.random.default_rng(seed); excitation=fuente(f,sr,.012,seed)*amp
    # Consonants have independent onsets; closures affect the ongoing vowel.
    fric=np.zeros(len(t)); gates=np.ones(len(t))
    for onset,ph,v in s.get('consonantes',[]):
        i=round(onset*sr); dur=.13 if ph=='s' else .07 if ph=='k' else .045 if ph=='t' else .18
        n=min(round(dur*sr),len(t)-i)
        if i<0 or n<2: continue
        tt=np.arange(n)/sr; noise=rng.normal(0,1,n)
        if ph in ('k','t','s'):
            lo,hi=(3400,10000) if ph=='s' else (1500,6500) if ph=='k' else (2500,10500)
            noise=sosfilt(butter(2,[lo,min(hi,.44*sr)],fs=sr,btype='bandpass',output='sos'),noise)
            shape=envolvente(n,sr,.009 if ph=='s' else .001,.035 if ph=='s' else .022)
            fric[i:i+n]+=noise*shape*v*(.10 if ph=='s' else .15)
            gates[i:i+n]*=1-(.40 if ph=='s' else .85)*shape
        elif ph=='m':
            shape=envolvente(n,sr,.03,.04); gates[i:i+n]*=1-.72*shape
            fric[i:i+n]+=.12*np.sin(fase(f[i:i+n],sr))*shape*v
    y=formantes(excitation*gates,curves,sr)*4.5+fric
    return estereo(y),{'f0_hz':f,'amplitud':amp,'F1_hz':curves[0],'F2_hz':curves[1],'cierre':1-gates},{}

def tono(m,d,sr,v=1,kind='cristal',seed=0,offset=0,s=None,_alto=False):
    if kind in ('cristal','terminal','fotones') and not _alto:
        return resample_poly(tono(m,d,sr*4,v,kind,seed,offset,s,True),1,4)[:round(d*sr)]
    t=reloj(d,sr); f=float(hz(m)); ph=2*np.pi*f*t; rng=np.random.default_rng(seed)
    if kind=='cristal':
        index=(1.5+5*v)*np.exp(-t/(.18+.3*v))+.15
        y=np.sin(ph+index*np.sin(ph*3.001))*np.exp(-t/1.35)
        y+=.21*np.sin(ph*2+(.3+.7*v)*np.sin(ph*1.5))*np.exp(-t/.7)
        y*=envolvente(len(t),sr,.003,.12)*.25
    elif kind=='estacion':
        y=np.zeros(len(t))
        for cents in [-7,0,7]:
            ff=f*2**(cents/1200); pp=2*np.pi*ff*t+.11*np.sin(t*2*np.pi*.47+cents)
            for h in range(1,min(25,int(sr*.4/ff))):
                y+=np.sin(pp*h)*np.exp(-h/(4+2*np.sin(t*.6)**2))/h/3
        y*=envolvente(len(t),sr,.42,.65)*.25
    elif kind=='plasma':
        glide=.065; freq=f*(1-.035*np.exp(-t/glide)); pp=fase(freq,sr); y=np.zeros(len(t))
        width=.43+.11*np.sin(2*np.pi*.8*(t+offset))
        for h in range(1,min(40,int(sr*.4/f))):
            brightness=np.exp(-h/(3.2+8*v*np.exp(-t/.35)+2*np.sin(t*2.1)**2))
            y+=np.sin(pp*h)*np.sin(np.pi*h*width)*brightness/h
        y+=sosfilt(butter(2,[1800,6500],fs=sr,btype='bandpass',output='sos'),rng.normal(0,1,len(t)))*np.exp(-t/.025)*.06
        y*=envolvente(len(t),sr,.009,.07)*.32
    elif kind=='terminal':
        a=np.sin(ph+2.2*np.exp(-t/.27)*np.sin(ph*2.77))*np.exp(-t/1.8)
        b=fuente(np.full(len(t),f),sr); ff=np.array([np.full(len(t),v) for v in VOCALES['u']]); b=formantes(b,ff,sr)*5
        c=(np.sin(ph)+.3*np.sin(ph*2)+.15*np.sin(ph*3))*np.exp(-t/.30)
        noise=sosfilt(butter(2,[f,min(sr*.4,f*8)],fs=sr,btype='bandpass',output='sos'),rng.normal(0,.15,len(t)))
        xx=control(s or {},'vector_x',t+offset,.5); yy=control(s or {},'vector_y',t+offset,.5)
        y=((1-xx)*(1-yy)*a+xx*(1-yy)*b+(1-xx)*yy*c+xx*yy*noise)*.32*envolvente(len(t),sr,.035,.18)
    elif kind=='androide':
        pp=fase(f*(1+.028*np.exp(-t/.045)),sr); sub=np.sin(pp)
        exc=fuente(np.full(len(t),f),sr); u=.5+.5*np.sin(t*2*np.pi*1.1+offset)
        ff=np.array([(1-u)*VOCALES['u'][k]+u*VOCALES['e'][k] for k in range(4)])
        mid=formantes(exc,ff,sr)*5
        y=(.30*sub+.60*np.tanh(mid*2))*envolvente(len(t),sr,.008,.08)
    elif kind=='fotones':
        freq=(f*.65+(f*5-f*.65)*np.exp(-t/.027)); pp=fase(freq,sr)
        metal=np.sin(2*np.pi*f*2.31*t)*np.sin(2*np.pi*f*3.71*t)
        y=(np.sin(pp)*np.exp(-t/.12)+.20*metal*np.exp(-t/.07))*envolvente(len(t),sr,.001,.03)*.50
        y+=rng.normal(0,.035,len(t))*np.exp(-t/.018)
    else: raise ValueError(kind)
    return y*v

def electronico(s,d,sr,seed,kind):
    y=np.zeros((round(d*sr),2)); notes=s.get('notas',[])
    for i,e in enumerate(notes):
        v=tono(e['midi'],e['dur'],sr,e.get('vel',.8),kind,seed+i,e['t'],s)
        pan=e.get('pan',0); yy=estereo(v,pan)
        if kind=='estacion':
            # Subtle early stereo spread belongs to this preset, not all instruments.
            delay=round(.011*sr)
            if len(v)>delay: yy[delay:,1]+=.10*v[:-delay]
        poner(y,yy,e['t'],sr)
    return y,{},{}

def render_piano(s,d,sr,seed):
    y=np.zeros((round(d*sr),2)); notes=s.get('notas',[]); assignments=[]
    for i,e in enumerate(notes):
        t=reloj(e['dur']+.85,sr); prev=notes[max(0,i-1)]['midi']; nxt=notes[min(len(notes)-1,i+1)]['midi']; cur=e['midi']
        # Future attack is newly synthesized; it is not a reversed sample.
        attack=np.sin(2*np.pi*hz(nxt)*t+2.9*np.exp(-t/.05)*np.sin(2*np.pi*hz(nxt)*2.1*t))*np.exp(-t/.060)
        body=(np.sin(2*np.pi*hz(cur)*t)+.4*np.sin(2*np.pi*hz(cur)*2*t))*np.exp(-t/1.1)
        tail=np.sin(2*np.pi*hz(prev)*t)*(-np.expm1(-t/.16))*np.exp(-t/1.65)
        v=(.14*attack+.20*body+.14*tail)*envolvente(len(t),sr,.002,.18)*e.get('vel',.8)
        poner(y,v,e['t'],sr,p=e.get('pan',0)); assignments.append({'t':e['t'],'ataque_midi':nxt,'cuerpo_midi':cur,'cola_midi':prev})
    return y,{}, {'asignaciones':assignments,'anticipacion':'partitura conocida, no predicción'}

def red_modal(s,d,sr,seed,kind):
    """Control-rate orthogonal exchange of normalized complex modal envelopes.

    Carrier oscillators keep independent frequencies. This is an abstract active
    frequency-converting instrument, not a passive acoustic bridge simulation.
    """
    t=reloj(d,sr); n=len(t); B=max(32,round(sr*.003)); voices=3 if kind=='cuerda' else 5; H=7
    state=np.zeros((voices,H),complex); out=np.zeros((n,2)); trace=[]; before=[]; after=[]; consumed=[]
    if kind=='cuerda':
        base=float(hz(s.get('base_midi',50))); ratios=np.array([1,2,3,4,5,6,7.])
        freqs=np.array([base*ratios,base*ratios*1.003,base*np.array([1,2.76,5.40,8.93,13.34,18.64,24.8])])
    else:
        bases=hz(s.get('cuerdas_midi',[50,57,60,64,69])); freqs=bases[:,None]*np.arange(1,H+1)[None,:]
    phases=np.zeros_like(freqs); target_freqs=freqs.copy(); exc=s.get('notas',[]); done=set(); links=s.get('enlaces',[])
    maxf=float(freqs.max()); assert maxf<sr*.44
    for a in range(0,n,B):
        b=min(n,a+B); dt=(b-a)/sr; now=a/sr; old=state.copy()
        damp=np.array([2.9,1.25,.42]) if kind=='cuerda' else np.full(voices,2.8)
        state*=np.exp(-dt/damp[:,None]*(1+np.arange(H)[None,:]*.21))
        for j,e in enumerate(exc):
            if j not in done and e['t']<(b/sr):
                v=min(voices-1,int(e.get('cuerda',0))); amp=e.get('vel',.8)*.27
                if 'inyeccion_modal' in e:
                    packet=e['inyeccion_modal']; vals=np.array([complex(re,im) for re,im in packet['z']])
                    for hmode,value in zip(packet['modos'],vals): state[v,hmode-1]+=value
                else: state[v]+=amp/(np.arange(1,H+1)**1.3)
                done.add(j)
                if kind=='cuerda': target_freqs=freqs*(float(hz(e['midi']))/freqs[0,0])
                else: target_freqs[v]=float(hz(e['midi']))*np.arange(1,H+1)
        freqs+=(target_freqs-freqs)*(1-np.exp(-dt/.025))
        if kind=='cuerda':
            pressure=float(control(s,'presion',np.array([now]),.4)[0]); bow=float(control(s,'arco',np.array([now]),0)[0])
            if bow>0: state[1]+=bow*dt*.12/(np.arange(1,H+1)**1.7)
            angle=(.1+pressure*1.3)*dt
            actions=[(0,1,angle),(1,2,angle*.85)]
        else:
            actions=[]
            for j,(at,v,w,ang) in enumerate(links):
                # A finite gesture, spread over 0.45 s, avoids an abrupt amplitude jump.
                if at<=now<at+.45: actions.append((int(v),int(w),ang*dt/.45))
        for v,w,ang in actions:
            e0=float(np.sum(abs(state)**2)); x=state[v].copy(); yy=state[w].copy()
            state[v]=np.cos(ang)*x-np.sin(ang)*yy; state[w]=np.sin(ang)*x+np.cos(ang)*yy
            e1=float(np.sum(abs(state)**2)); before.append(e0); after.append(e1)
        # Convex interpolation preserves bounded envelope norm between states.
        u=np.linspace(0,1,b-a,endpoint=False)
        for v in range(voices):
            mono=np.zeros(b-a)
            for h in range(H):
                envelope=old[v,h]*(1-u)+state[v,h]*u
                phase=phases[v,h]+2*np.pi*freqs[v,h]*np.arange(b-a)/sr
                mono+=np.real(envelope*np.exp(1j*phase))
                phases[v,h]=(phases[v,h]+2*np.pi*freqs[v,h]*(b-a)/sr)%(2*np.pi)
            out[a:b]+=estereo(mono,(-.6+1.2*v/max(1,voices-1)))
        trace.append([now,*np.sum(abs(state)**2,axis=1)])
    out*=envolvente(n,sr,.008,.25)[:,None]
    tt=np.array(trace); controls={'energia_'+str(k):np.interp(t,tt[:,0],tt[:,k+1]) for k in range(voices)}
    return out,controls,{'norma_antes':before[::max(1,len(before)//300)],'norma_despues':after[::max(1,len(after)//300)],
        'error_max_intercambio':float(max([abs(a-b) for a,b in zip(before,after)],default=0)),
        'modelo':'norma de envolventes complejas; conversión activa entre alturas; no energía acústica en julios'}

def render_organo(s,d,sr,seed):
    t=reloj(d,sr); f,gate=perfil_notas(s,t,sr,86); pressure=control(s,'presion',t,.5)
    divisors=[1,2,3,5,7,9]; state=np.zeros(len(t),bool); y=np.zeros((len(t),2)); trace={}; switches=[]
    for j,k in enumerate(divisors):
        on=.12+.125*j; off=max(0,on-.20); changes=np.zeros(len(t)); running=False
        # Exact Schmitt trigger state changes, not gain modulation called memory.
        edges=np.flatnonzero((pressure[1:]>=on)!=(pressure[:-1]>=on))+1
        edges2=np.flatnonzero((pressure[1:]<=off)!=(pressure[:-1]<=off))+1
        cuts=np.unique(np.r_[0,edges,edges2,len(t)])
        for a,b in zip(cuts[:-1],cuts[1:]):
            previous=running
            if pressure[a]>=on: running=True
            elif pressure[a]<=off: running=False
            state[a:b]=running
            if running!=previous: switches.append({'t':a/sr,'divisor':k,'activo':bool(running),'presion':float(pressure[a])})
        gain=suavizar(state.astype(float),sr,.065); ph=fase(f/k,sr)
        yy=np.sin(ph+.006*np.sin(t*(.4+j*.1)))*gain*gate*.19/(1+j*.25)
        y+=estereo(yy,(-.75 if j%2 else .75)*(j/5))
        trace['divisor_'+str(k)]=gain.copy()
    trace['presion']=pressure
    return y,trace,{'cambios':switches,'divisores':divisors,'umbrales_on':[.12+.125*j for j in range(6)],'banda_histeresis':.20}

def render_sala(s,d,sr,seed):
    t=reloj(d,sr); rng=np.random.default_rng(seed); x=np.zeros(len(t))
    for e in s.get('notas',[]):
        i=round(e['t']*sr); nn=min(round(e['dur']*sr),len(t)-i)
        if nn<=0: continue
        tt=np.arange(nn)/sr; freq=float(hz(e['midi']))
        xx=(np.sin(2*np.pi*freq*tt)*np.exp(-tt/.04)+rng.normal(0,.3,nn)*np.exp(-tt/.02))*e.get('vel',.8)*.3
        x[i:i+nn]+=xx*envolvente(nn,sr,.002,.025)
    # Independent low and high networks have distinct delay routes and rotations.
    low=sosfilt(butter(2,850,fs=sr,output='sos'),x); high=x-low
    y=np.zeros((len(t),2)); energy=[]; H=np.eye(4)-np.ones((4,4))*.5; B=128
    for group,drive in enumerate([low,high]):
        delays=np.round(sr*np.array([.031,.043,.059,.071] if group==0 else [.013,.019,.023,.037])).astype(int)
        buffers=np.zeros((4,len(t)+max(delays)+B)); filstate=np.zeros(4); yy=np.zeros((len(t),2))
        loss=.84 if group==0 else .77; lp=.16 if group==0 else .55
        for a in range(0,len(t),B):
            b=min(len(t),a+B); size=b-a; tap=buffers[:,a:b].copy(); angle=float(control(s,'pliegue_'+str(group),np.array([a/sr]),.3)[0])*np.pi*.9
            R=np.eye(4); R[:2,:2]=[[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]]
            feedback=(R@H)@tap
            for k in range(4):
                filtered,zi=lfilter([lp],[1,-(1-lp)],feedback[k],zi=[filstate[k]])
                filstate[k]=zi[0]; start=a+delays[k]
                buffers[k,start:start+size]+=filtered*loss+drive[a:b]*[.5,.35,.4,.25][k]
            yy[a:b,0]=np.array([1,.3,-.4,.2])@tap*.45
            yy[a:b,1]=np.array([.2,-.4,.3,1])@tap*.45
        y+=yy
    y+=estereo(x)*.10; y*=envolvente(len(t),sr,.001,.35)[:,None]
    return y,{'pliegue_graves':control(s,'pliegue_0',t,.3),'pliegue_agudos':control(s,'pliegue_1',t,.3)}, {'redes':2,'rutas_por_red':4,'retencion':[.84,.77],'matriz':'rotación ortogonal por Householder; filtros pasivos; retardos fijos'}

def render(nombre,partitura,duracion,sr=SR,semilla=19103419):
    if nombre=='boca': result=render_boca(partitura,duracion,sr,semilla)
    elif nombre in ('cuerda','arpa'): result=red_modal(partitura,duracion,sr,semilla,nombre)
    elif nombre=='piano': result=render_piano(partitura,duracion,sr,semilla)
    elif nombre=='organo': result=render_organo(partitura,duracion,sr,semilla)
    elif nombre=='sala': result=render_sala(partitura,duracion,sr,semilla)
    elif nombre in NOMBRES: result=electronico(partitura,duracion,sr,semilla,nombre)
    else: raise ValueError('Instrumento desconocido: '+nombre)
    audio,traces,info=result
    if not np.isfinite(audio).all(): raise ValueError('Señal no finita en '+nombre)
    return audio.astype(np.float32),traces,info
