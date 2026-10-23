"""Instrumentos/controladores de r4. No ejecuta un render al importar.
La bolsa es un modelo de impactos de tres osciladores contra topes, no
una simulación calibrada de juguetes reales. El transporte es ficción.
"""
import numpy as np
from scipy.signal import lfilter

def rotacion(i,j,a):
    R=np.eye(3);c,s=np.cos(a),np.sin(a)
    R[i,i]=R[j,j]=c;R[i,j]=-s;R[j,i]=s
    return R

def transbordos(a,b):
    A=rotacion(0,1,a);B=rotacion(1,2,b)
    # Recorrido cerrado en el grafo de cuatro instrucciones; no conmutan.
    return [np.eye(3),A,B@A,A.T@B@A,B.T@A.T@B@A]

def impactos_bolsa(t,aceleracion,semilla=22):
    """Integra en segundos; retorna contactos, con identidad de cada objeto.
    Tres longitudes distintas. Topes + restitución disipan energía; no RNG.
    La semilla identifica la receta, no genera impactos aleatorios.
    """
    t=np.asarray(t);a=np.asarray(aceleracion);x=np.array([.045,-.03,.02]);v=np.zeros(3)
    L=np.array([.11,.073,.047]);lim=np.array([.17,.12,.085]);restit=np.array([.38,.47,.31]);out=[]
    ultimo=np.full(3,-10.)
    for k in range(1,len(t)):
        dt=t[k]-t[k-1]
        v+=dt*(-9.81*x/L-1.5*v-a[k]);x+=dt*v
        for j in range(3):
            if abs(x[j])>lim[j]:
                fuerza=abs(v[j]);x[j]=np.sign(x[j])*lim[j];v[j]*=-restit[j]
                if t[k]-ultimo[j]>.09 and fuerza>.035:
                    out.append({'t':float(t[k]),'objeto':j,'fuerza':float(fuerza)});ultimo[j]=t[k]
    return out

def juguete(objeto,fuerza=.3,sr=32000,duracion=.6):
    """Tres cuerpos modales: trompo de lámina, cascabel, pájaro de barro.
    No imita una especie ni utiliza grabaciones de terceros.
    """
    t=np.arange(round(sr*duracion))/sr
    modos=[[431,793,1297],[2261,3127,4711],[873,1311,2017]][objeto]
    y=sum(np.sin(2*np.pi*f*t)*np.exp(-t*(9+j*8))/(j+1) for j,f in enumerate(modos))
    return np.tanh(fuerza)*y*np.minimum(1,t/.0015)

def motor_fallido(duracion=1.1,sr=32000,esfuerzo=1.):
    """Pulsos de encendido que pierden frecuencia; sin bucle de metrónomo."""
    t=np.arange(round(sr*duracion))/sr
    fase=2*np.pi*(17*t-6*t*t/max(duracion,.01))
    y=np.maximum(0,np.sin(fase))**12*np.sin(2*np.pi*47*t)
    return esfuerzo*lfilter([1],[1,-.78],y)*np.exp(-4*t/duracion)

def comprobaciones():
    W=transbordos(.73,1.07);C=W[-1]
    return {'error_ortogonal':float(np.max(abs(C.T@C-np.eye(3)))),
            'distancia_del_retorno_a_identidad':float(np.linalg.norm(C-np.eye(3))),
            'norma_inicial':1.,'norma_final':float(np.linalg.norm(C@np.array([1.,0,0]))),
            'nota':'conservación de norma del controlador de tres voces; no energía acústica de la mezcla'}
