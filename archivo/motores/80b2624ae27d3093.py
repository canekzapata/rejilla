"""Verificar la cadena musical y las exportaciones; no sintetiza la obra."""
from pathlib import Path
from collections import Counter
import json,math,hashlib,csv,xml.etree.ElementTree as ET
import numpy as np
import fitz
from modelos_memoria import encuentro,contacto,complejo,recibir,extraer_cuerda,comprobar
from instrumentos import Junco,hz
ROOT=Path(__file__).resolve().parent;OUT=ROOT/(ROOT/'REVISION-EN-CURSO.txt').read_text().strip();TAG=OUT.name.split('-')[-1]
P=json.loads((OUT/'partitura-v7.json').read_text('utf8'));E=P['eventos'];C0,C1=P['centro'];D=P['duracion']
PACK=json.loads((OUT/'datos/paquete-modal-v6.json').read_text('utf8'));PL=json.loads((OUT/'datos/transportes-memoria-v6.json').read_text('utf8'))
all_events=[(k,e) for k,es in E.items() for e in es];ids={e['id']:e for k,e in all_events}
assert len(E)==36 and all(E.values()) and len(ids)==len(all_events)
for k,e in all_events:
 assert 0<=e['t']<D and 0<e['dur'] and e['t']+e['dur']<=D+1e-6,(k,e['id'])
 assert all(math.isfinite(e[x]) for x in ['t','dur','midi','hz','vel','pan'])
 assert abs(e['hz']/float(hz(e['midi']))-1)<1e-8
 if e.get('ancestro'):
  assert e['ancestro'] in ids,(e['id'],e['ancestro'])
  assert ids[e['ancestro']]['t']<=e['t']+1e-7,(e['id'],'antecedente futuro')
 for parent in e.get('contribuyentes_estado',[]):assert parent in ids and ids[parent]['t']<=e['t']+1e-7
 for a,b in e['salidas']:
  assert a>=e['t']-1e-7 and b<=e['t']+e['dur']+1e-7 and b>a
  for cut in P['cortes_buses']:assert b<=cut['t']+1e-7 or a>=cut['fin']-1e-7,(e['id'],cut)
for k in ['voz','duo','corocuerda','corojunco','boca','bombo','caja','hat','tom','aro','ride','fotones']:
 assert not [e for e in E[k] if e['t']<C1 and e['t']+e['dur']>C0],k
center=[e for k,e in all_events if C0<=e['t']<C1];assert len(center)==13 and all(e.get('libre') for e in center)
assert len(P['oscuridades'])==8
contact_event=ids[PACK['contacto_evento']];test=contacto(contact_event['contacto']['curva'],contact_event['contacto']['pelicula'])
assert np.max(abs(complejo(test['z_final'])[[0,1,2,4]]-complejo(PACK['guitarra_z'])))<1e-12
zc=recibir(complejo(PACK['guitarra_z']),PACK['espera_hasta_cuerda_s'],[.07,.12,.19,.37],.47)
assert np.max(abs(zc-complejo(PACK['cuerda_z'])))<1e-12
ce=ids[PACK['cuerda_evento']];je=ids[PACK['junco_eventos'][0]]
zj,trace=extraer_cuerda(zc,ce['t'],je['t'],P['controles']['cuerda']['controles']['presion'],P['controles']['cuerda']['controles']['arco'])
assert np.max(abs(zj-complejo(PACK['junco_z'])))<1e-12
learned=.42+1.1*(1-PACK['normas'][1]/PACK['normas'][0]);assert abs(learned-P['analisis_datos']['espera_aprendida_s'])<1e-12
prosody=[]
for ly in P['letra']:
 notes=[ids[i] for i in ly['ids']];assert len(notes)==len(ly['silabas'].split())
 assert ' '.join(e['texto'] for e in notes)==ly['silabas']
 if ly.get('espera_heredada_s'):
  measured=notes[1]['t']-notes[0]['t']-ly['ritmo_negras'][0]*P['negra_s']*ly['escala']
  assert abs(measured-learned)<1e-6,(ly['frase'],measured)
  assert ly['texto'].startswith(('en otras','a esperar'))
  prosody.append({'frase':ly['frase'],'espera_s':measured,'silaba_antes':notes[0]['texto'],'silaba_despues':notes[1]['texto']})
early=[ly for ly in P['letra'] if ly['capa']=='voz' and ly['t']<C0]
windows={round(ly['fin']-ly['t'],6) for ly in early};assert len(windows)>5
prefixes={tuple(round(ids[i]['midi'],5) for i in ly['ids'][:5]) for ly in early};assert len(prefixes)>5
marginal=phase_error=source_error=mass_error=0
for k,pl in enumerate(PL):
 pi=np.array(pl['pi']);marginal=max(marginal,float(max(abs(pi.sum(1)-pl['a']).max(),abs(pi.sum(0)-pl['b']).max())))
 assert np.all(pi>=-1e-10)
 assert np.max(abs(np.array(pl['masa_recibida'])-pl['perdida']-pl['a']))<1e-10
 if k:
  source_error=max(source_error,float(np.max(abs(np.array(pl['source'])-PL[k-1]['target']))))
  mass_error=max(mass_error,float(np.max(abs(np.array(pl['masa_recibida'])-PL[k-1]['b']))))
  phase_error=max(phase_error,float(np.max(abs(np.angle(np.exp(1j*(np.array(pl['fases_origen'])-PL[k-1]['fases_destino'])))))))
 osc=Junco();osc.phase[:]=np.array(pl['fases_origen'])[:,None];osc.avanzar(pl['fin']-pl['t'],pl['source'],pl['target'],0,1,pi)
 zz=np.sum(np.sqrt(pi)*np.exp(1j*osc.phase),axis=0)
 assert np.max(abs(np.angle(np.exp(1j*(np.angle(zz)-pl['fases_destino'])))))<1e-9
assert max(marginal,source_error,mass_error,phase_error)<1e-8
assert sum(p['cambio_pi_sin_familias']>1e-9 for p in PL)==8
# El intercambio puede reponer una columna desde otra: la pérdida irreversible
# corresponde al total, no a una desigualdad monótona de cada receptor.
assert sum(PL[-1]['b'])<sum(PL[0]['masa_recibida'])
MEET=json.loads((OUT/'datos/encuentros.json').read_text('utf8'));x=np.zeros(3);xr=np.zeros(3)
for e in MEET:x=encuentro(x,e['i'],e['j'],e['promesa_cents']);assert np.max(abs(x-e['despues']))<1e-10
for e in reversed(MEET):xr=encuentro(xr,e['i'],e['j'],e['promesa_cents'])
assert np.linalg.norm(x-xr)>1
# Estado del órgano a igual presión con pasados diferentes.
def organ(q):
 pp=np.array(P['controles']['organo']['controles']['presion']);out=[]
 ts=np.arange(0,q+.005,.01);curve=np.interp(ts,pp[:,0],pp[:,1])
 for j in range(6):
  state=False;on=.12+.125*j;off=max(0,on-.2)
  for v in curve:
   if v>=on:state=True
   elif v<=off:state=False
  out.append(int(state))
 return out
assert sum(organ(55))==3 and sum(organ(C1+.1))==5
gerr=0
for e in E['guitarra']:
 pa=e['parametros_motor'];sh=e['afinaciones_cajas_cents'][pa['caja']]
 gerr=max(gerr,abs(pa['midi']+sh/100+12*math.log2(pa['parcial'])-e['midi']))
assert gerr<1e-9
def stats(a,b):
 total=0;parts=0;attacks=0
 for k,ev in E.items():
  intervals=[]
  for e in ev:
   if a<=e['t']<b-1e-7:attacks+=1
   for u,v in e['salidas']:
    if u<b and v>a:intervals.append([max(a,u),min(b,v)])
  merged=[]
  for u,v in sorted(intervals):
   if merged and u<=merged[-1][1]:merged[-1][1]=max(v,merged[-1][1])
   else:merged.append([u,v])
  total+=sum(v-u for u,v in merged);parts+=bool(merged)
 return {'inicio_s':a,'fin_s':b,'ataques':attacks,'partes_con_salida':parts,'ocupacion_media_partes':total/(b-a)}
wall=[stats(206.66666666666666+j*40/3,206.66666666666666+(j+1)*40/3) for j in range(3)]
assert wall[0]['ataques']<wall[1]['ataques']<wall[2]['ataques']
# Exportación: todas las voces, alteraciones y descansos completan sus celdas.
xml=ET.parse(OUT/f'luciernagas-partitura-completa-v7-s1-{TAG}.musicxml').getroot();assert len(xml.findall('part'))==36
for part in xml.findall('part'):
 assert len(part.findall('measure'))==len(P['medidas_editoriales'])
 for mm,ref in zip(part.findall('measure'),P['medidas_editoriales']):
  count=Counter()
  for n in mm.findall('note'):count[n.findtext('voice')]+=int(n.findtext('duration'))
  assert all(v==round((ref['fin']-ref['t'])/P['negra_s']*12000) for v in count.values())
with (OUT/f'luciernagas-eventos-v7-s1-{TAG}.csv').open(encoding='utf-8-sig',newline='') as f:assert len(list(csv.DictReader(f)))==len(all_events)
doc=fitz.open(OUT/f'luciernagas-partitura-analizada-v7-s1-{TAG}.pdf');outside=[]
for i,page in enumerate(doc):
 for block in page.get_text('dict')['blocks']:
  for ln in block.get('lines',[]):
   for sp in ln['spans']:
    rect=fitz.Rect(sp['bbox'])
    if rect.x0<0 or rect.y0<0 or rect.x1>page.rect.width+.1 or rect.y1>page.rect.height+.1:outside.append([i+1,sp['text']])
assert not outside,outside
original=ROOT/'luciernagas-partitura-s1-054923e7c401/partitura-v4.json'
assert hashlib.sha256(original.read_bytes()).hexdigest()=='41769bb43acb5db3084b09f2a843902c90b2f611572da1b6ccd7b9f82c85c0a4'
result={'partes':len(E),'eventos_internos':len(all_events),'duracion_s':D,'gestos_centro':len(center),
 'oscuridades':len(P['oscuridades']),'oscuridad_total_s':sum(b-a for a,b in P['oscuridades']),
 'contornos_iniciales_distintos_5_notas':len(prefixes),'ventanas_vocales_distintas':len(windows),'prosodia_heredada':prosody,
 'espera_aprendida_s':learned,'extraccion_red_modal_comprobada':True,'normas_paquete':PACK['normas'],
 'planes':len(PL),'planes_con_costo_familia_efectivo':8,'error_marginal_max':marginal,
 'error_herencia_alturas':source_error,'error_herencia_masas':mass_error,'error_herencia_fase_rad':phase_error,
 'masa_total_inicial':sum(PL[0]['masa_recibida']),'masa_total_final':sum(PL[-1]['b']),
 'encuentros_orden_invertido_diferencia_cents':float(np.linalg.norm(x-xr)),
 'organo_antes':organ(55),'organo_despues':organ(C1+.1),'error_afinacion_guitarra_semitonos':gerr,
 'pared':wall,'pdf_paginas':len(doc),'texto_fuera_pdf':outside,'xml_partes':36,'xml_celdas_por_parte':len(P['medidas_editoriales']),
 'modelos':comprobar(),'sin_audio':not any(OUT.glob('*.wav')),'original_intacto':True,
 'limite':'Escritura, estados y exportación; no evaluación de audición, mezcla, dicción o belleza.'}
with (OUT/'validacion-v7.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=1)
with (OUT/'fuentes/verificar_revision.py').open('xb') as f:f.write(Path(__file__).read_bytes())
print(json.dumps(result,ensure_ascii=False,indent=1))
