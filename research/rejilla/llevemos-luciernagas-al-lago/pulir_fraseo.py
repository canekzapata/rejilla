"""v7: poner la espera en 'en / otras', afinar contratos y conservar v6."""
from pathlib import Path
import json,math
ROOT=Path(__file__).resolve().parent;OUT=ROOT/(ROOT/'REVISION-EN-CURSO.txt').read_text().strip()
P=json.loads((OUT/'partitura-v6.json').read_text('utf8'));byid={e['id']:e for es in P['eventos'].values() for e in es}
gap=P['analisis_datos']['espera_aprendida_s'];changed={}
for line in P['letra']:
 if not line.get('espera_heredada_s'):continue
 # El silencio cae entre palabras; los otros regresos conservan articulación.
 keep=line['texto'].startswith('en otras') or line['texto'].startswith('a esperar')
 if keep:continue
 for eid in line['ids']:
  e=byid[eid]
  if e['silaba']>1:
   e['t']-=gap;changed[eid]=-gap
  e['respiracion_antes']=False;e['ancestro']=None
  e['operacion_herencia']='regreso de la frase: campo de afinación cambiado, articulación continua'
 line['fin']-=gap;line['espera_heredada_s']=0
for e in P['eventos']['clarinete']:
 if e.get('ancestro') in changed:e['t']+=changed[e['ancestro']]
for e in P['eventos']['guitarra']:
 if 'contacto' in e:
  e['parametros_motor']['gesto']='contacto';e['parametros_motor']['contrato']='contacto continuo: drive + ruido; no ejecutar púa adicional'
# Recalcular las salidas después del cambio de fraseo, con el mismo estado.
for key,events in P['eventos'].items():
 for e in events:
  segs=[(e['t'],e['t']+e['dur'])]
  for cut in P['cortes_buses']:
   a,b=cut['t'],cut['fin'];new=[]
   for u,v in segs:
    if v<=a or u>=b:new.append((u,v))
    else:
     if u<a:new.append((u,a))
     if v>b:new.append((b,v))
   segs=new
  if key=='boca':
   end=P['analisis_datos']['telefono_apagado_s'];segs=[(u,min(v,end)) for u,v in segs if u<end]
  e['salidas']=[[u,v] for u,v in segs if v-u>.008]
 events.sort(key=lambda e:(e['t'],e['id']))
pack=json.loads((OUT/'datos/paquete-modal-v6.json').read_text('utf8'))
P['analisis_datos'].update(paquete='datos/paquete-modal-v6.json',planes='datos/transportes-memoria-v6.json',
  normalizacion_inicial_junco={'norma_captada':pack['normas'][-1],'factor_amplitud':1/math.sqrt(pack['normas'][-1]),
    'regla':'Normalizar una vez la distribución captada; después conservar masas recibidas menos pérdidas. Es ganancia activa declarada, no conservación de energía acústica.'})
P['interpretacion']['datos_canonicos']='partitura-v7.json; controles completos y ventanas salidas'
P['version']='luciernagas-partitura-7.0';P['correcciones']+=['La espera heredada ocurre entre palabras; se elimina una pausa interna en llevemos.',
 'El contacto continuo tiene su ruta propia de excitación, sin doblarlo con una púa automática.',
 'La normalización inicial del junco se declara como ganancia activa, separada de las normas modales.']
with (OUT/'partitura-v7.json').open('x',encoding='utf8') as f:json.dump(P,f,ensure_ascii=False,indent=1)
with (OUT/'fuentes/pulir_fraseo.py').open('xb') as f:f.write(Path(__file__).read_bytes())
print('v7: fraseo entre palabras y contratos completos')
