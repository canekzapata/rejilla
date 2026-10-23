"""Orquestar fuentes fijadas y voces derivadas; conservar cada salida existente."""
from comun import *
from scipy.signal import butter,sosfiltfilt,lfilter,resample_poly
from laminas import *
import gc
def read(c):return np.fromfile(run()/(c+'.f32'),np.float32)
def main():
 out=ultimo();P=leer(out/'partitura.json');R=run();N=round(P['duracion']*SR);tt=np.arange(N)/SR;tag=out.name.split('-')[-1]
 def store(c,y):
  assert np.isfinite(y).all() and len(y)==N,c
  raw(c,y);print(c,round(activo(y),6),flush=True)
 for c in ['fuelle-alto','fuelle-bajo','fuelle-portadora']:
  if not (R/(c+'.f32')).exists():store(c,resample_poly(read(c+'-os2'),1,2)[:N])
 PY=importar(lib()/'motores/python.py','acorde_python');K=leer(lib()/'fichas/jardin-farfisa.json')
 for c in ['kick','caja','ride','hats','rim','maquina808','farfisa','pedal110','radio-izq','radio-der','telar']:
  if (R/(c+'.f32')).exists():continue
  y=np.zeros((N,2),np.float32);cache={}
  if c=='telar':
   TF=importar(BASE/'fuentes/telar/motor.py','acorde_telar');notes=[{**e,'cuerpo':'cobre','estirar':1.8,'dispersion':.4,'referencia':.25} for e in P['eventos'][c]];y,rec=TF.render({'notas':notes},P['duracion'],sr=SR,semilla=SEED);jsave(out/'telar-recibos.json',rec)
  else:
   for e in P['eventos'][c]:
    n=round((e['dur']+.2)*SR);t=np.arange(n)/SR;v=e['vel'];p=e.get('pan',0)
    if c in ['kick','caja','ride','hats','rim','maquina808']:
     kit='bateria-tr808' if c=='maquina808' else 'bateria-acustico';j=int(np.argmin(abs(np.array([.3,.6,.9])-v)));key=(kit,e['pieza'],j)
     if key not in cache:cache[key]=read(f'{kit}-{e["pieza"]}-{j}')
     z=cache[key];v=1
    elif c=='farfisa':
     key=(e['midi'],e['dur'],v)
     if key not in cache:
      z,sr=PY.nota(K,e['midi'],v,e['dur']);z=z[round(.25*sr):];cache[key]=resample_poly(z,SR,sr)
     z=cache[key];v=1
    elif c=='pedal110':z=(np.sin(2*np.pi*hz(e['midi'])*t)+.16*np.sin(4*np.pi*hz(e['midi'])*t))*.2*env(n,.25,.5)
    else:
     z=.2*np.sin(2*np.pi*hz(e['midi'])*t+2*np.exp(-t*30)*np.sin(2*np.pi*hz(e['midi'])*1.414*t))*np.exp(-t*20)*env(n,.003,.06)
    poner(y,z,e['t'],v,p)
  store(c,y);del y;gc.collect()
 # Dos memorias modales excitadas por el piano REAL, sin reiniciar el estado.
 if not (R/'resonador-A.f32').exists() or not (R/'resonador-coma.f32').exists():
  ex=read('ep-tema')+.35*read('ep-comping');ex+=read('pedal110').reshape(-1,2).mean(1)*.3
  for c,f0 in [('resonador-A',110),('resonador-coma',111.375)]:
   if (R/(c+'.f32')).exists():continue
   y=np.zeros((N,2),np.float32)
   for h in range(1,9):
    r=np.exp(-np.log(1000)/((5+h*.65)*SR));pole=r*np.exp(2j*np.pi*f0*h/SR);z=2*np.real(lfilter([1-r],[1,-pole],ex));y+=pan(z,(-1 if h%2 else 1)*.45)/h**.65
   gate=np.clip((tt-52*BAR)/3,0,1);y*=gate[:,None];store(c,y);del y;gc.collect()
 if not (R/'batidos.f32').exists():
  gate=np.clip((tt-52*BAR)/5,0,1)*np.minimum(1,np.maximum(0,(P['duracion']-tt)/3));z=.09*(np.sin(2*np.pi*110*tt)+np.sin(2*np.pi*111.375*tt))*gate;store('batidos',pan(z))
 if not (R/'pulsos-batido.f32').exists():
  beat=leer(out/'batidos.json');y=np.zeros((N,2),np.float32);z=read('bateria-acustico-rim-0')
  for cycle in range(3):
   for t in beat['picos_s']:
    at=52*BAR+cycle*64+t
    if at<P['duracion']-1:poner(y,z,at,.45,.12)
  store('pulsos-batido',y)
 V=importar(BASE/'fuentes/adaptadores/instrumentos-corriente.py','acorde_vocal')
 for c,src in [('voz','sabina-voz'),('voz-doble','sabina-doble'),('fragmento','sabina-fragmento'),('voz-fuelle','sabina-voz')]:
  if (R/(c+'.f32')).exists():continue
  z=read(src)
  if c=='voz':z=V.pecho(z,.92)
  if c=='voz-fuelle':
   # La portadora es la lengüeta nueva; sólo se conserva la segunda ventana vocal.
   gate=np.zeros(N,np.float32);gate[round(20*BAR*SR):round(24*BAR*SR)]=1;z=V.vocoder(z,read('fuelle-portadora'))*gate
  y=pan(z,{'voz':0,'voz-doble':-.18,'fragmento':.32,'voz-fuelle':.15}[c]);store(c,y)
 # Captura del estado real de los motores antes de mezclar.
 f,ax=figura('Treinta capas, varias maneras de decir','El piano reconoce el tema · el fuelle respira · el chelo cruza · las paredes recuerdan',2)
 for c,col in [('chelo','#79c1bd'),('fuelle-alto','#e9b46e'),('fuelle-bajo','#d4a5b7')]:
  z=read(c);a,b=round(40*BAR*SR),round(52*BAR*SR);ax[0].plot(tt[a:b:256],z[a:b:256],lw=.45,label=c,color=col)
 ax[0].legend(fontsize=8);ax[0].set_xlabel('segundos');ax[0].set_title('Cruce real de registros')
 for j,c in enumerate(['ep-tema','voz','voz-doble','voz-fuelle','fragmento']):
  z=read(c);z=z.reshape(N,-1);r=np.sqrt(np.mean(z[:N//1024*1024].reshape(-1,1024,z.shape[1])**2,axis=(1,2)));ax[1].plot(np.arange(len(r))*1024/SR,r/(r.max()+1e-9)*.7+j,lw=.7,label=c)
 ax[1].set_yticks(range(5),['piano','voz','doble','vocoder','corte']);ax[1].set_xlabel('segundos');ax[1].set_title('La voz deja lugar');salva(f,out/'proceso'/f'04-fuentes-reales-s{SEED}-{tag}.png')
if __name__=='__main__':main()
