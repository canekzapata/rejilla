"""Dos diseños instrumentales; estado modal y planes. No exporta audio.

Guitarra: seis cuerdas x tres cajas x ocho modos, excitación localizada,
captación y roce. Junco: cuatro lengüetas que reciben masa de un transporte.
Las pruebas numéricas verifican contratos; todavía no validan su sonido.
"""
import numpy as np
from scipy.optimize import linprog

VERSION='pantano-instrumentos-1.0'
CUERDAS=np.array([40,45,50,55,59,64],float)

def hz(m):return 440*2**((np.asarray(m)-69)/12)

def acuerdos(deuda,pesos=(1.,1.,1.)):
    """δx≈(0,0,deuda), sum x=0. Residuo del ciclo no borrable por afinar."""
    w=np.asarray(pesos,float);assert np.all(w>0)
    eta=np.array([0.,0.,float(deuda)])
    residual=-eta.sum()/np.sum(1/w)/w
    dif=eta+residual
    x=np.array([0,dif[0],dif[0]+dif[1]]);x-=x.mean()
    return {'cents':x.tolist(),'residuos':residual.tolist(),'diferencias':dif.tolist(),'deuda_ciclo':float(deuda)}

class Guitarra:
    """Envolventes complejas; conversión de modos activa, sin alegar julios."""
    def __init__(self):
        self.z=np.zeros((6,3,8),complex);self.phase=np.zeros((6,3,8));self.t=0.
    def gesto(self,cuerda,vel=.6,gesto='pua',nodo=.17,caja=0,parcial=1):
        h=np.arange(1,9);shape=np.sin(np.pi*h*np.clip(nodo,.01,.99))/h**1.2
        if gesto=='armonico':shape*=np.exp(-.5*((h-parcial)/.35)**2)
        if gesto=='madera':shape=np.cos(h*1.37)/(h+.5)**.8
        if gesto=='roce':shape*=np.cos(h*2.1)*.38
        if gesto=='apagar':self.z[cuerda]*=.04;return
        self.z[cuerda,caja]+=vel*shape*(1+.2j)
    def avanzar(self,dt,deuda=0,pesos=(1,1,1),humedad=0,presion=.2):
        assert dt>0
        shifts=np.asarray(acuerdos(deuda,pesos)['cents'])
        h=np.arange(1,9);f=hz(CUERDAS)[:,None,None]*2**(shifts[None,:,None]/1200)*h[None,None,:]
        self.phase=(self.phase+2*np.pi*f*dt)%(2*np.pi)
        self.z*=np.exp(-dt*(.4+.13*h[None,None,:]+1.2*humedad))
        # Red antisymétrica integrada por exponencial ortogonal exacta 3x3.
        from scipy.linalg import expm
        B=np.array([[0,-1,.3],[1,0,-.7],[-.3,.7,0]])*(.1+presion)*dt
        R=expm(B);self.z=np.einsum('ab,sbh->sah',R,self.z);self.t+=dt
        return {'envolvente_norma2':float(np.sum(abs(self.z)**2)),'cents':shifts.tolist(),'t':self.t}
    def observar(self,pickup=(1,.2,-.15)):
        return np.real(np.einsum('c,sch->sh',np.asarray(pickup),self.z*np.exp(1j*self.phase))).sum(axis=1)

def transporte(source_midi,target_midi,a,b,penalizacion=0):
    x=np.asarray(source_midi,float);y=np.asarray(target_midi,float);a=np.asarray(a,float);b=np.asarray(b,float)
    assert np.all(a>=0) and np.all(b>=0) and abs(a.sum()-b.sum())<1e-9
    n,m=len(x),len(y);C=(x[:,None]-y[None,:])**2
    C+=float(penalizacion)*(np.arange(n)[:,None]!=np.arange(m)[None,:])
    A=np.zeros((n+m,n*m))
    for i in range(n):A[i,i*m:(i+1)*m]=1
    for j in range(m):A[n+j,j::m]=1
    r=linprog(C.ravel(),A_eq=A,b_eq=np.r_[a,b],bounds=(0,None),method='highs')
    if not r.success:raise ValueError(r.message)
    pi=r.x.reshape(n,m)
    return {'pi':pi.tolist(),'costo':float(r.fun),'costos':C.tolist(),'error_marginal':float(max(np.max(abs(pi.sum(1)-a)),np.max(abs(pi.sum(0)-b))))}

def junco_gestos(plan,source_midi,target_midi,t,dur,ancestros):
    """Trayectorias interpoladas en MIDI continuo; masa y fase son distintas."""
    out=[]
    for i,row in enumerate(plan['pi']):
        for j,mass in enumerate(row):
            if mass<=1e-10:continue
            out.append(dict(t=t,dur=dur,voz=j,midi=source_midi[i],midi_fin=target_midi[j],
                masa=mass,amplitud_relativa=float(np.sqrt(mass)),ancestro=ancestros[i],
                fase='integrar 2pi*f(t); conservar estado por voz; evitar reinicio entre segmentos'))
    return out

def comprobar():
    a=acuerdos(100);b=acuerdos(0)
    assert abs(sum(a['residuos'])+100)<1e-9 and max(abs(x) for x in b['residuos'])==0
    g=Guitarra();g.gesto(0);before=float(np.sum(abs(g.z)**2));trace=g.avanzar(.01,100,humedad=.8)
    assert np.isfinite(g.observar()).all() and trace['envolvente_norma2']<before
    aplan=transporte([60,67],[62,69],[.5,.5],[.5,.5]);assert abs(aplan['costo']-4)<1e-9
    identity=transporte([60,67],[60,67],[.5,.5],[.5,.5]);assert identity['costo']==0
    return {'guitarra_estado_finito':True,'amortiguacion_disminuye_norma':True,'acuerdos':a,
            'ciclo_sin_deuda':b,'transporte_caso_4':aplan['costo'],'transporte_identidad':identity['costo'],
            'modelo':'envolventes de un diseño abstracto; sin calibración física ni audio exportado'}
