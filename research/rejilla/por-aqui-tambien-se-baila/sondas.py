"""Sólo pruebas cortas aisladas y comparaciones, nunca un máster de la pieza."""
from comun import *
from instrumentos import *
from laminas import *
from scipy.signal import find_peaks
def main():
 out=ultimo();tag=out.name.split('-')[-1];S=leer(depo());TR=leer(out/'trafico.json');P=leer(score());info={};clips=[];rev=(out/'sondas-instrumentos.json').exists()
 # Membrana: una ganancia común mantiene contrastes de técnica/carga.
 y=np.zeros((round(12*SR),2));f,ax=figura('Una membrana no tiene una sola voz','Elementos finitos radiales · centro cargado · golpes abiertos, apagados y graves',2)
 for j,(g,c) in enumerate([('din',0),('din',3),('ta',3),('thom',3),('din',3),('ta',3)]):
  z=membrana(g,146.832 if g!='thom' else 73.416,1.5,carga=c);poner(y,z,j*1.8+.1,p=.1 if j%2 else -.1)
 modes,_=modos_membrana();ratios=[float(r) for r,m,_ in modes[:10]];base,_=modos_membrana(0);rawr=[float(r) for r,m,_ in base[:10]]
 ax[0].vlines(rawr,0,1,color='#1d2869',label='sin carga');ax[0].vlines(ratios,0,.7,color='#732605',label='carga central');ax[0].legend();ax[0].set_xlabel('frecuencia / fundamental');ax[0].set_title('Modos calculados, no parciales impuestos')
 z=membrana('din');ax[1].plot(np.arange(len(z))[::32]/SR,z[::32],lw=.6,color='#1d2869');ax[1].set_xlabel('segundos');ax[1].set_title('Golpe abierto de la prueba');salva(f,out/'proceso'/f'{"05b" if rev else "05"}-membrana-cargada-s{SEED}-{tag}.png');info['membrana']={**muestra(out,'sonda-membrana-cargada',y),'ratios_con_carga':ratios,'ratios_sin_carga':rawr,'limite':'modelo de membrana con densidad central; no mridangam calibrado ni técnica tradicional certificada'}
 # El mismo motivo se conserva en las tres lecturas del solista raro.
 notes=[{'t':a*Q,'midi':m,'dur':d*Q,'vel':.7} for a,m,d in [(0,62,.5),(.75,65,.5),(1.5,69,.75),(3,67,.75),(4.5,65,.5),(5.5,64,.5),(6.75,61,.5),(7.5,62,.4)]]
 variations=[];met=[]
 x=np.zeros(5*SR)
 for e in notes:
  z=chirp(e['midi'],e['dur'],e['vel']);i=round(e['t']*SR);nn=min(len(z),len(x)-i);x[i:i+nn]+=z[:nn]
 variations.append(pan(np.r_[x,np.zeros(SR)]));met.append({'estado':'seco','Talbot':'0'})
 for st in [4,18]:
  v,m=laser_frase(notes,5,st);variations.append(v[:6*SR]);met.append(m)
 sep=np.zeros((SR//2,2));yl=np.concatenate([np.concatenate([v,sep]) for v in variations]);info['laser']={**muestra(out,'sonda-laser-tres-recorridos',yl),'lecturas':met}
 f,ax=figura('El láser lleva una frase por tres salidas','Mismo tema · seco / red con Talbot 1/3 / red con Talbot 2/5',2)
 for j,v in enumerate(variations):
  r=np.sqrt(np.mean(v[:len(v)//256*256].reshape(-1,256,2)**2,axis=(1,2)));ax[0].plot(np.arange(len(r))*256/SR,r+j*.05,label=['seco','transbordo','depósito avanzado'][j],lw=.8)
 ax[0].legend(fontsize=8);ax[0].set_xlabel('segundos');M=matriz_cruce(3);ax[1].imshow(M,vmin=-1,vmax=1,cmap='RdBu_r');ax[1].set_title('Cruce ortogonal de tres puertos');ax[1].set_xticks(range(3),['A','B','C']);ax[1].set_yticks(range(3),['A','B','C']);salva(f,out/'proceso'/f'{"06b" if rev else "06"}-laser-y-cruces-s{SEED}-{tag}.png');err=float(np.linalg.norm(M.T@M-np.eye(3)));assert err<1e-12;info['laser']['error_ortogonalidad']=err
 # Raspador: mismo recorrido, antes y después del depósito. Ganancia común x12 para la sonda.
 Z=np.array(S['z_inicial_m']);D=np.array(S['depositos_m'][-1]);path=np.array(S['caminos'][0]);before=Z[np.arange(S['nr']),path];after=(Z+D)[np.arange(S['nr']),path];a,ma=raspador(before);b,mb=raspador(after);yr=np.r_[a,np.zeros(SR//2),b]*12;info['raspador']={**muestra(out,'sonda-raspador-antes-despues',pan(yr)),'antes':ma,'despues':mb,'diferencia_relativa':float(np.linalg.norm(a-b)/(np.linalg.norm(a)+1e-15)),'ganancia_fija_sonda':12}
 # Dos remates propios: 4 y 3 unidades por pulso, cada uno aterriza en el pulso 8.
 yt=np.zeros((12*SR,2))
 for base,sub in [(0,4),(6,3)]:
  rr=next(r for r in P['moras'] if r['subdivision']==sub)
  for j,k in enumerate(rr['golpes']):poner(yt,membrana(['din','ta','thom'][j%3],146.832 if j%3!=2 else 73.416,.7),base+k/sub*Q)
  poner(yt,membrana('din',dur=1),base+8*Q,.9)
 info['remates']={**muestra(out,'sonda-remates-ocho-pulsos',yt),'moras':P['moras']}
 # Drone real del banco y boca de tres tiempos: frase sin voz humana de moduladora.
 TT=importar(BASE/'fuentes/tres-tiempos/motores.py','baila_tt');a,_,_=TT.render('estacion',{'notas':[{'t':0,'dur':10,'midi':38,'vel':.35,'pan':-.2},{'t':0,'dur':10,'midi':45,'vel':.3,'pan':.2}]},12,sr=SR,semilla=SEED);b,_,_=TT.render('boca',{'notas':[{'t':i*.5+1,'dur':.3,'midi':[50,57,55,50][i%4],'vel':.5} for i in range(16)],'vocales':[[0,'u'],[3,'a'],[5,'i'],[8,'o']],'consonantes':[[i*.5+1,'t' if i%2 else 'k',.6] for i in range(16)]},12,sr=SR,semilla=SEED);info['drone_boca']={**muestra(out,'sonda-drone-y-boca-autonoma',a+b*.6),'motor':'Cuerdas de estación y Boca de tres tiempos fijados; comparación breve, no interpretación completa'}
 # Guardar resultados sin declarar escucha auditiva ni certificación de caos/género.
 jsave(out/('sondas-instrumentos-r2.json' if rev else 'sondas-instrumentos.json'),info);print(json.dumps({k:{'archivo':v['archivo'],'segundos':v['segundos']} for k,v in info.items()},ensure_ascii=True,indent=1))
if __name__=='__main__':main()
