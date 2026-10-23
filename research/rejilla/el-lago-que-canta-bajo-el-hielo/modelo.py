"""Placas Navier discretas, red de modos fundamentales y memoria de fracturas.

Las condiciones son w=Δw=0 (placa simplemente apoyada discreta), no bordes libres.
El acoplamiento entre fundamentales y los umbrales de cuña son modelos artísticos explícitos.
"""
import io,os,hashlib
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import eigsh
from PIL import Image
from comun import *
def construir():
 T=jleer(BASE/'terreno/terreno-227.json');G=T['G'];lab=np.fromfile(BASE/'terreno/regiones-227.i32',np.int32).reshape(G,G)
 H=np.fromfile(BASE/'terreno/h-227.f32',np.float32).reshape(G,G)
 dx=T['anchoKm']*1000*T['escala_acustica']/(G-1)
 ids=np.unique(lab);centros={int(k):np.argwhere(lab==k).mean(axis=0)[::-1].tolist() for k in ids if k>=0}
 bordes={}
 for axis in [0,1]:
  a=lab[:-1,:] if axis==0 else lab[:,:-1];b=lab[1:,:] if axis==0 else lab[:,1:]
  for y,x in np.argwhere((a!=b)&(a>=0)&(b>=0)):
   key=tuple(sorted([int(a[y,x]),int(b[y,x])]))
   bordes.setdefault(key,[]).append([float(x+.5),float(y+.5)])
 ad={k:set() for k in centros}
 for a,b in bordes:ad[a].add(b);ad[b].add(a)
 inicio=min(centros,key=lambda k:np.linalg.norm(np.array(centros[k])-[180,180]));sel=[inicio];frontera=set(ad[inicio])
 while len(sel)<32:
  k=min(frontera,key=lambda k:np.linalg.norm(np.array(centros[k])-[180,180]));sel.append(k);frontera.remove(k);frontera.update(ad[k]-set(sel))
 E,rho,nu,h=5e9,920,.3,.032;alpha=float(np.sqrt(E*h*h/(12*rho*(1-nu*nu))))
 placas=[];modos={}
 for k in sel:
  pix=np.argwhere(lab==k);n=len(pix);ix={tuple(v):i for i,v in enumerate(pix)};rows=[];cols=[];vals=[]
  for i,(y,x) in enumerate(pix):
   rows.append(i);cols.append(i);vals.append(4/dx**2)
   for dy,ddx in [(0,1),(0,-1),(1,0),(-1,0)]:
    j=ix.get((y+dy,x+ddx))
    if j is not None:rows.append(i);cols.append(j);vals.append(-1/dx**2)
  L=sparse.coo_matrix((vals,(rows,cols)),shape=(n,n)).tocsr();w,V=eigsh(L,k=min(10,n-2),which='SM',v0=np.ones(n));o=np.argsort(w);w=w[o];V=V[:,o]
  f=alpha*w/(2*np.pi);center=int(np.argmin(np.linalg.norm(pix-pix.mean(0),axis=1)));edge=int(np.argmax(np.linalg.norm(pix-pix.mean(0),axis=1)))
  vc=V[center];ve=V[edge];vc/=np.max(np.abs(vc));ve/=np.max(np.abs(ve))
  modos[str(k)]={'f':f.tolist(),'centro':vc.tolist(),'borde':ve.tolist()}
  c=np.array(centros[k]);placas.append({'id':k,'centro':(c/(G-1)).tolist(),'area':n*dx*dx,'f0':float(f[0]),'pan':float(np.clip((c[0]-180)/110,-.8,.8)),'distancia':float(np.linalg.norm(c-np.array([180,272]))*dx)})
 edges=[]
 for (a,b),pts in bordes.items():
  if a in sel and b in sel:edges.append({'id':len(edges),'a':a,'b':b,'longitud':len(pts)*dx,'puntos':[[x/(G-1),y/(G-1)] for x,y in pts[::max(1,len(pts)//18)]]})
 f0=placas[0]['f0']
 while f0<55:f0*=2
 while f0>110:f0/=2
 red={'semilla':227,'G':G,'escala_acustica':T['escala_acustica'],'ancho_acustico_m':dx*(G-1),'dx':dx,'alpha':alpha,'h':h,'E':E,'rho':rho,'nu':nu,'f0':f0,'placas':placas,'aristas':edges,'modos':modos}
 return red,H,lab
def estados(red):
 n=len(red['placas']);ix={p['id']:i for i,p in enumerate(red['placas'])};freq=np.array([p['f0'] for p in red['placas']]);Ls=[];historias=[]
 memoria=np.zeros(len(red['aristas']));rng=np.random.default_rng(SEED)
 for invierno in range(5):
  tension=np.zeros(len(memoria));umbrales=np.array([.8+.4*rng.random() for e in memoria])*(1-.11*np.minimum(memoria,3));abiertas=np.zeros(len(memoria),bool);ev=[]
  for paso in range(256):
   tension+=.010+.008*np.sin(np.arange(len(memoria))*.71+paso*.039)**2
   disponibles=np.flatnonzero((tension>umbrales)&~abiertas)
   for e in disponibles:
    abiertas[e]=True;energia=float(tension[e]);memoria[e]+=.65;ed=red['aristas'][e]
    ev.append({'paso':paso,'arista':int(e),'energia':energia,'memoria':float(memoria[e])})
    for j,ot in enumerate(red['aristas']):
     if j!=e and {ed['a'],ed['b']}&{ot['a'],ot['b']}:tension[j]+=.10
  K=np.diag((2*np.pi*freq)**2)
  for j,e in enumerate(red['aristas']):
   a,b=ix[e['a']],ix[e['b']];g=(2*np.pi*18)**2*e['longitud']/(1+memoria[j]*.8)
   K[a,a]+=g;K[b,b]+=g;K[a,b]-=g;K[b,a]-=g
  lam,U=np.linalg.eigh(K);Ls.append({'frecuencias':(np.sqrt(lam)/(2*np.pi)).tolist(),'vectores':U.tolist()});historias.append(ev)
 return Ls,historias
def main():
 red,H,lab=construir();Ls,hist=estados(red);red['estados']=Ls;red['inviernos']=hist
 # El PNG inicial entra en el hash de ejecución, junto con el programa y nonce.
 im=Image.fromarray(np.uint8(np.clip(H,0,1)*255)).convert('RGB');buf=io.BytesIO();im.save(buf,format='PNG');nonce=os.urandom(20).hex()
 full=hashlib.sha256(buf.getvalue()+Path(__file__).read_bytes()+VERSION.encode()+nonce.encode()).hexdigest();tag=full[:12]
 out=BASE/f'el-lago-que-canta-s227-{tag}';out.mkdir(exist_ok=False);(out/'proceso').mkdir();(BASE/'render'/tag).mkdir(parents=True,exist_ok=False)
 jguardar(out/'red.json',red);jguardar(out/'ejecucion.json',{'hash':full,'nonce':nonce,'version':VERSION,'semilla':227,'png_inicial_sha256':hashlib.sha256(buf.getvalue()).hexdigest()})
 guardar(out/'proceso'/f'01-lamina-s227-{tag}.png',buf.getvalue());guardar(out/'regiones-227.i32',lab.astype('int32').tobytes())
 # Puntero editable; las entregas permanecen exclusivas.
 (BASE/'ULTIMA.txt').write_text(out.name,encoding='utf-8')
 print(out);print('f0',red['f0'],'alpha',red['alpha'],'aristas',len(red['aristas']))
if __name__=='__main__':main()
