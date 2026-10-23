"""v6: completa el relevo coral y coteja extracción y fases con el motor modal."""
from pathlib import Path
import copy,json,math
import numpy as np
from modelos_memoria import complejo,pares,extraer_cuerda
from instrumentos import Junco,hz
ROOT=Path(__file__).resolve().parent;OUT=ROOT/(ROOT/'REVISION-EN-CURSO.txt').read_text().strip()
P=json.loads((OUT/'partitura-v5.json').read_text('utf8'));E=P['eventos'];C0,C1=P['centro'];PACK=json.loads((OUT/'datos/paquete-modal.json').read_text('utf8'))
plans=json.loads((OUT/'datos/transportes-memoria.json').read_text('utf8'));byid={e['id']:e for es in E.values() for e in es}
c=byid[PACK['cuerda_evento']];j0=byid[PACK['junco_eventos'][0]]
zj,probe=extraer_cuerda(complejo(PACK['cuerda_z']),c['t'],j0['t'],
  P['controles']['cuerda']['controles']['presion'],P['controles']['cuerda']['controles']['arco'])
PACK['junco_z_borrador']=PACK['junco_z'];PACK['junco_z']=pares(zj);PACK['extraccion_real_red_modal']=probe
PACK['normas'][2]=float(np.sum(abs(zj)**2))
source=np.array(plans[0]['source']);anchor=j0['t'];phase0=np.angle(zj)
for j,eid in enumerate(PACK['junco_eventos']):
 e=byid[eid];e['estado_complejo']=pares([zj[j]])[0];e['masa']=float(abs(zj[j])**2)
 e['fase_inicial_rad']=float((phase0[j]+2*np.pi*hz(source[j])*(e['t']-anchor))%(2*np.pi))
 e['operacion_herencia']='captación del estado de red_modal tras evolucionar presión, arco y amortiguación; fase portadora incluida'
last=next(e for e in E['junco4'] if e['frase']=='último-resto')
last['fase_inicial_rad']=float((phase0[-1]+2*np.pi*hz(source[-1])*(last['t']-anchor))%(2*np.pi))
last['estado_complejo']=pares([zj[-1]])[0];last['masa']=float(abs(zj[-1])**2)
phase=phase0+2*np.pi*hz(source)*(plans[0]['t']-anchor)
phase[-1]+=2*np.pi*(hz(last['midi'])-hz(source[-1]))*(plans[0]['t']-last['t'])
phase%=2*np.pi
# Recalcular las masas desde la captación efectiva; mantener extremos y tiempos.
from modelos_memoria import plan_memoria
a=abs(zj)**2;a/=a.sum()
for k,pl in enumerate(plans):
 origin=a.copy();aa=a*np.array(pl['retencion']);mix=np.eye(4)*.72+np.roll(np.eye(4),1,axis=0)*.28;bb=mix@aa
 actual=plan_memoria(pl['source'],pl['target'],aa,bb,pl['colores_origen'],pl['colores_destino'],pl['penalizacion'])
 plain=plan_memoria(pl['source'],pl['target'],aa,bb,pl['colores_origen'],pl['colores_destino'],0)
 pi=np.array(actual['pi']);pl.update(actual,a=aa.tolist(),b=bb.tolist(),masa_recibida=origin.tolist(),perdida=(origin-aa).tolist(),
   fases_origen=phase.tolist(),cambio_pi_sin_familias=float(np.max(abs(pi-np.array(plain['pi'])))))
 # Una arista puede aparecer/desaparecer al cambiar la distribución: regenerar
 # sólo estas voces y sus referencias, conservando v5 completa como borrador.
 a=bb

# Reconstruir todos los eventos de planes con fuentes completas, sin ancestros colgantes.
for key in ['junco1','junco2','junco3','junco4']:E[key]=[e for e in E[key] if not e.get('plan')]
previous=[[eid] for eid in PACK['junco_eventos']]
phase=phase0+2*np.pi*hz(source)*(plans[0]['t']-anchor)
phase[-1]+=2*np.pi*(hz(last['midi'])-hz(source[-1]))*(plans[0]['t']-last['t']);phase%=2*np.pi
for k,pl in enumerate(plans):
 pi=np.array(pl['pi']);pl['fases_origen']=phase.tolist();ids=[[] for _ in range(4)]
 for i in range(4):
  for j in range(4):
   if pi[i,j]<=1e-12:continue
   t=pl['t'];end=pl['fin'];eid=f'transporte-{k+1:02}-{i}-{j}'
   segs=[(t,end)]
   for cut in P['cortes_buses']:
    aa,bb=cut['t'],cut['fin'];rr=[]
    for u,v in segs:
     if v<=aa or u>=bb:rr.append((u,v))
     else:
      if u<aa:rr.append((u,aa))
      if v>bb:rr.append((bb,v))
    segs=rr
   e=dict(id=eid,t=t,dur=end-t,midi=pl['source'][i],midi_fin=pl['target'][j],hz=float(hz(pl['source'][i])),vel=.2 if t<206.6667 else (.29 if t<233.3333 else .41),
      pan=[-.8,-.25,.25,.8][j],articulacion='transporte heredado; fase por arista',seccion=next(s['id'] for s in P['secciones'] if s['t']<=t<s['fin']),
      frase=pl['id'],ancestro=previous[i][0],contribuyentes_estado=previous[i],operacion_herencia='altura y masa del destino anterior; fase de su suma fasorial',
      masa=float(pi[i,j]),amplitud_relativa=float(np.sqrt(pi[i,j])),fase_inicial_rad=float(phase[i]),plan=pl['id'],origen_fila=i,destino_columna=j,
      salidas=[[u,v] for u,v in segs if v-u>.008])
   E['junco'+str(j+1)].append(e);ids[j].append(eid)
 osc=Junco();osc.phase[:]=phase[:,None];osc.avanzar(pl['fin']-pl['t'],pl['source'],pl['target'],0,1,pi)
 z=np.sum(np.sqrt(pi)*np.exp(1j*osc.phase),axis=0);phase=np.where(abs(z)>1e-12,np.angle(z),phase)
 pl['fases_destino']=phase.tolist();pl['eventos_destino']=ids;pl['ancestros']=[v[0] for v in previous];previous=ids
coda=next(e for e in E['junco4'] if e['frase']=='coda');coda['ancestro']=previous[-1][0];coda['contribuyentes_estado']=previous[-1]
coda['fase_inicial_rad']=float((phase[-1]+2*np.pi*hz(plans[-1]['target'][-1])*(coda['t']-plans[-1]['fin']))%(2*np.pi));coda['masa']=plans[-1]['b'][-1]

# Coro del junco: continúa la palabra que la cuerda dejó, con contorno propio.
text='en o tras for mas de ex pe rien cia'.split();mel=[64,67,65,64,59.01955,64,67.863137,64,59.01955,64]
rh=[.5,1.5,.5,1,.5,.5,.25,.5,2,2.5];tt=220.15;start=tt;ids=[]
for j,(sy,m,r) in enumerate(zip(text,mel,rh)):
 if j==1:tt+=PACK['espera_aprendida_s']
 dd=r*P['negra_s']*.9;eid=f'corojunco-v6-{j}'
 E['corojunco'].append(dict(id=eid,t=tt,dur=dd*.91,midi=m,hz=float(hz(m)),vel=.53 if j in [1,3,8] else .36,
  pan=.45,articulacion='vocoder; recibir una articulación',seccion='VIII',frase='otras-coro-junco',ancestro=PACK['junco_eventos'][2] if j==1 else None,
  texto=sy,silaba=j+1,silabas_total=10,acento=j in [1,3,8],respiracion_antes=j==1,salidas=[[tt,tt+dd*.91]],
  origen_texto='verso literal',operacion_herencia='espera del relevo central' if j==1 else 'frase coral escrita'))
 ids.append(eid);tt+=dd
P['letra'].append(dict(t=start,fin=tt,capa='corojunco',texto='en otras formas de experiencia',silabas=' '.join(text),
 frase='otras-coro-junco',procedencia='verso literal',acentos_indices=[1,3,8],ritmo_negras=rh,escala=.9,espera_heredada_s=PACK['espera_aprendida_s'],ids=ids))
for e in E['boca']:
 end=P['analisis_datos']['telefono_apagado_s'];e['salidas']=[[a,min(b,end)] for a,b in e.get('salidas',[[e['t'],e['t']+e['dur']]]) if a<end]
for es in E.values():es.sort(key=lambda e:(e['t'],e['id']))
P['letra'].sort(key=lambda e:(e['t'],e['capa']));P['version']='luciernagas-partitura-6.0'
P['interpretacion']['datos_canonicos']='partitura-v6.json; salidas = ventanas audibles, eventos = estados completos'
P['interpretacion']['nuevos']['junco']+='; consolidar_revision.py conserva fase durante el centro y recalcula masas desde red_modal'
P['correcciones']=['v5 conservada; se completa la entrada del vocoder de junco',
 'La entrega de cuerda toma su estado evolucionado con el motor, en vez de transformar otra vez sólo la inyección inicial.',
 'Se integra fase durante la espera central y entre planes; la coda hereda la última llegada.',
 'Apagar el teléfono cierra también el final de una sílaba de boca que estuviera en curso.']
for file,data in [('partitura-v6.json',P),('datos/paquete-modal-v6.json',PACK),('datos/transportes-memoria-v6.json',plans)]:
 with (OUT/file).open('x',encoding='utf8') as f:json.dump(data,f,ensure_ascii=False,indent=1)
for file in ['modelos_memoria.py','consolidar_revision.py']:
 with (OUT/'fuentes'/('v6-'+file)).open('xb') as f:f.write((ROOT/file).read_bytes())
print(json.dumps({'eventos':sum(map(len,E.values())),'partes_no_vacias':sum(bool(x) for x in E.values()),'captacion_norma':PACK['normas'][-1],
 'planes_penalizacion_efectiva':sum(p['cambio_pi_sin_familias']>1e-9 for p in plans)},ensure_ascii=False))
