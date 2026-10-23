"""Extensiones de los dos instrumentos. Estados de control; no exporta audio.

Las normas son de envolventes complejas, no julios acústicos. La película de
barro es una decisión del modelo, no una medición ambiental de Traspuesta.
"""
import numpy as np
from scipy.linalg import expm
from scipy.optimize import linprog
from instrumentos import Guitarra, hz

VERSION = 'luciernagas-memoria-2.0'


def encuentro(x, i, j, promesa, respuesta=.72):
    """Proyección afín relajada: x[j]-x[i] se acerca a promesa; sum x fija."""
    out = np.asarray(x, float).copy()
    error = float(promesa)-(out[j]-out[i])
    out[i] -= respuesta*error/2
    out[j] += respuesta*error/2
    return out


class GuitarraMemoria(Guitarra):
    def avanzar(self, dt, afinaciones=(0,0,0), humedad=0, presion=.2, **unused):
        h=np.arange(1,9)
        f=hz(self.midi)[:,None,None]*2**(np.asarray(afinaciones)[None,:,None]/1200)*h
        self.phase=(self.phase+2*np.pi*f*dt)%(2*np.pi)
        self.z*=np.exp(-dt*(.4+.13*h+1.2*humedad))
        B=np.array([[0,-1,.3],[1,0,-.7],[-.3,.7,0]])*(.1+presion)*dt
        self.z=np.einsum('ab,sbh->sah',expm(B),self.z); self.t+=dt
        return self.z


def contacto(curva, pelicula=.65, nodo=.17, carga=0., dt=.005):
    """Carga con fuga, umbral y deslizamientos; excitación modal sostenida.

    Para realizar: evaluar a este dt, interpolar excitación y ruido de contacto
    al reloj de interpretación. No convertir cada muestra en un nuevo ataque.
    """
    curve=np.asarray(curva,float); duration=float(curve[-1,0]); tt=np.arange(0,duration+dt/2,dt)
    z=np.zeros(8,complex); h=np.arange(1,9); slips=[]; trace=[]; threshold=.34+.33*pelicula
    for index,t in enumerate(tt):
        p=float(np.interp(t,curve[:,0],curve[:,1])); carga+=dt*(p-.72*carga)
        slip=carga>=threshold
        if slip: slips.append(float(t)); carga*=.18
        drive=max(0,p-threshold)*.055+(float(slip)*.28)
        z*=np.exp(-dt*(.4+.13*h+1.2*pelicula))
        z+=drive*np.sin(np.pi*h*nodo)/h**1.2*np.exp(1j*h*(.37+t*.8))
        if index%6==0:trace.append([float(t),p,float(carga),drive,float(.028*p*(1+pelicula))])
    return {'curva':curve.tolist(),'pelicula':pelicula,'umbral':threshold,
            'deslizamientos_s':slips,'carga_final':float(carga),
            'z_final':[[float(v.real),float(v.imag)] for v in z],
            'traza_t_presion_carga_exc_ruido':trace,'dt_s':dt,
            'norma_final':float(np.sum(abs(z)**2))}


def complejo(pairs):return np.array([complex(a,b) for a,b in pairs])
def pares(z):return [[float(v.real),float(v.imag)] for v in z]


def recibir(z, espera, retenciones, angulo=.47):
    """Cuerda: decaer, intercambiar modos y conservar fase compleja recibida."""
    z=np.asarray(z,complex); n=len(z); B=np.zeros((n,n))
    for i in range(n-1):B[i,i+1]=-angulo;B[i+1,i]=angulo
    return expm(B)@(z*np.exp(-np.asarray(retenciones)*espera))


def plan_memoria(source,target,a,b,source_colors,target_colors,penalty=0):
    source=np.asarray(source);target=np.asarray(target);a=np.asarray(a);b=np.asarray(b)
    C=(source[:,None]-target[None,:])**2
    C+=penalty*(np.asarray(source_colors)[:,None]!=np.asarray(target_colors)[None,:])
    A=np.zeros((8,16))
    for i in range(4):A[i,4*i:4*i+4]=1
    for j in range(4):A[4+j,j::4]=1
    r=linprog(C.ravel(),A_eq=A,b_eq=np.r_[a,b],bounds=(0,None),method='highs')
    if not r.success:raise ValueError(r.message)
    pi=r.x.reshape(4,4)
    return {'pi':pi.tolist(),'costos':C.tolist(),'costo':float(r.fun),
            'error_marginal':float(max(np.max(abs(pi.sum(1)-a)),np.max(abs(pi.sum(0)-b))))}


def transferir_fases(pi, source_phase, fallback):
    """Suma fasorial ponderada; cancelación no se confunde con masa perdida."""
    z=np.asarray(pi).T@np.exp(1j*np.asarray(source_phase))
    return np.where(abs(z)>1e-12,np.angle(z),np.asarray(fallback))


def comprobar():
    x=np.zeros(3); A=lambda y:encuentro(y,0,1,0); C=lambda y:encuentro(y,2,0,85)
    ac=A(C(x));ca=C(A(x));difference=float(np.linalg.norm(ac-ca))
    assert difference>1 and abs(ac.sum())<1e-10
    fail=contacto([[0,0],[.3,.30],[1.5,.30],[1.9,0]])
    success=contacto([[0,0],[.4,.91],[2.8,.91],[3.1,0]])
    assert not fail['deslizamientos_s'] and success['deslizamientos_s']
    v=recibir(np.ones(4,complex),.7,[.3,.6,.9,1.4]);assert np.sum(abs(v)**2)<4
    return {'orden_encuentros_diferencia_cents':difference,'contacto_falla_sin_parcial':True,
            'contacto_supera_umbral':True,'transferencia_amortigua':True,
            'limite':'Estados de control comprobados; sin audición ni calibración física.'}
