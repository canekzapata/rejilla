"""Depósito conservativo en abanico y tráfico microscópico stop-go.
Modelos reducidos para composición; no predicen hidrología o tránsito de una ciudad.
"""
from comun import *
from laminas import *
from scipy.ndimage import map_coordinates
def sedimentos(H,T,G,paquetes=320,masa=9000.):
 nr=24;na=9;edges=np.linspace(0,G['L']*T['anchoKm']*1000,nr+1);theta=np.linspace(-G['mitad'],G['mitad'],na);r=(edges[1:]+edges[:-1])/2;th=G['a']+theta
 U=G['ax']+r[:,None]/(T['anchoKm']*1000)*np.cos(th);V=G['ay']+r[:,None]/(T['anchoKm']*1000)*np.sin(th);Z=map_coordinates(H,[(V*(T['G']-1)).ravel(),(U*(T['G']-1)).ravel()],order=1,mode='nearest').reshape(nr,na)*T['relieve']
 Z=Z.astype('float64');area=.5*(edges[1:]**2-edges[:-1]**2)*(2*G['mitad']/na);area=np.broadcast_to(area[:,None],Z.shape);dep=np.zeros_like(Z);salida=0.;paths=[];history=[];volume=0.;history.append(dep.copy())
 for p in range(paquetes):
  j=na//2;left=masa;path=[]
  for i in range(nr):
   cand=np.arange(max(0,j-1),min(na,j+2));score=Z[i,cand]+dep[i,cand]+.18*abs(cand-j);j=int(cand[np.argmin(score)]);path.append(j)
   # Depósito creciente al perder pendiente, siempre una fracción del paquete restante.
   slope=max(0,(Z[i-1,path[-2]]-Z[i,j])/max(1,r[i]-r[i-1])) if i else .1
   frac=.055+.16*np.exp(-12*slope);drop=left*frac;left-=drop;dep[i,j]+=drop/area[i,j]
  salida+=left;volume+=masa;paths.append(path)
  if (p+1)%16==0:history.append(dep.copy())
 stored=float(np.sum(dep*area));err=abs(volume-salida-stored)/volume
 assert err<1e-12
 return {'modelo':'red radial de depósito sobre alturas muestreadas de Traspuesta; tiempo y volumen amplificados','nr':nr,'na':na,'u':U.tolist(),'v':V.tolist(),'z_inicial_m':Z.tolist(),'area_m2':area.tolist(),'depositos_m':[d.tolist() for d in history],'caminos':paths,'volumen_entrada_m3':volume,'volumen_salida_m3':salida,'volumen_depositado_m3':stored,'error_balance_relativo':err,'cambios_de_camino':int(np.sum(np.any(np.diff(np.array(paths),axis=0)!=0,axis=1))),'masa_paquete_m3':masa,'pendiente_nota':'enrutamiento sólo hacia la siguiente corona; no resuelve Navier-Stokes ni avulsión natural completa'}
def trafico(duracion=250.,alpha=.95,dt=.04):
 L=720.;N=34;burn=180.;n=round((burn+duracion)/dt);p=np.arange(N)*L/N;p[0]+=.5;v=np.full(N,5.);P=[];V=[];caps=0;minh=1e9
 for k in range(n):
  h=(np.roll(p,-1)-p)%L;target=5*(np.tanh((h-20)/6)+np.tanh(20/6));v=np.maximum(0,v+dt*alpha*(target-v));dx=v*dt;safe=np.maximum(0,h-5.2);caps+=int(np.sum(dx>safe));dx=np.minimum(dx,safe);p=(p+dx)%L;minh=min(minh,float(h.min()))
  if k*dt>=burn and k%5==0:P.append(p.copy());V.append(v.copy())
 VV=np.array(V);PP=np.array(P);return {'modelo':'velocidad óptima tipo Bando en anillo, Euler y guarda de no solapamiento','L_m':L,'vehiculos':N,'alpha':alpha,'dt_integracion':dt,'paso_guardado':dt*5,'burn_s':burn,'v':VV.tolist(),'x':PP.tolist(),'v_min':float(VV.min()),'v_max':float(VV.max()),'fraccion_v_menor_08':float(np.mean(VV<.8)),'desv_v':float(VV.std()),'min_distancia_m':minh,'intervenciones_guarda':caps,'caos':'ondas irregulares stop-go; no se calculó exponente de Lyapunov y no se afirma caos determinista'}
def main():
 out=ultimo();tag=out.name.split('-')[-1];T=leer(out/'datos/terreno-22.json');geom=leer(BASE/'render/geometria-instrumentada-22/geometria-abanico.json')
 if not (out/'datos/geometria-abanico.json').exists():jsave(out/'datos/geometria-abanico.json',geom)
 H=np.fromfile(out/'datos/h-22.f32',np.float32).reshape(T['G'],T['G']);S=sedimentos(H,T,geom['geometria']);TR=trafico();jsave(out/'depositos.json',S);jsave(out/'trafico.json',TR)
 f,ax=figura('La ruta cambia lo que deja pasar','Alturas de Traspuesta → depósito conservado → siguientes recorridos',2);U=np.array(S['u']);V=np.array(S['v']);ax[0].contour(H,levels=30,colors=T['plumas'][0],linewidths=.4,origin='upper')
 for k in range(0,len(S['caminos']),16):
  j=np.array(S['caminos'][k]);ax[0].plot(U[np.arange(len(j)),j]*(T['G']-1),V[np.arange(len(j)),j]*(T['G']-1),alpha=.45,lw=.8,color=T['plumas'][-1])
 ax[0].set_aspect('equal');ax[0].set_axis_off();d=np.array(S['depositos_m'][-1]);im=ax[1].imshow(d.T,origin='lower',aspect='auto',cmap='cividis');f.colorbar(im,ax=ax[1],label='depósito, metros amplificados');ax[1].set_xlabel('corona radial');ax[1].set_ylabel('ramal');salva(f,out/'proceso'/f'02-deposito-y-recorridos-s{SEED}-{tag}.png')
 f,ax=figura('Detente. Avanza. El vecino vuelve a frenar.','34 vehículos · una perturbación inicial · el ciclo musical conservará su reloj',2);VV=np.array(TR['v']);ts=np.arange(len(VV))*TR['paso_guardado'];im=ax[0].imshow(VV.T,origin='lower',aspect='auto',extent=[0,ts[-1],0,34],cmap='magma',vmin=0,vmax=10);f.colorbar(im,ax=ax[0],label='m/s');ax[0].set_xlabel('segundos');ax[0].set_ylabel('vehículo')
 for j in [0,11,22]:ax[1].plot(ts,VV[:,j],lw=.8,label=f'vehículo {j}')
 ax[1].axhline(.8,color='gray',lw=.5);ax[1].legend(fontsize=8);ax[1].set_xlabel('segundos');ax[1].set_ylabel('m/s');salva(f,out/'proceso'/f'03-olas-de-trafico-s{SEED}-{tag}.png');print('depósito',S['error_balance_relativo'],S['cambios_de_camino'],'tráfico',TR['v_min'],TR['fraccion_v_menor_08'],TR['intervenciones_guarda'])
if __name__=='__main__':main()
