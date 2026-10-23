"""Invariantes musicales/datos de la entrega; sin render de señal."""
from pathlib import Path
import json,math,collections,csv,xml.etree.ElementTree as ET
import numpy as np
import fitz
from instrumentos import acuerdos,comprobar,parametros_guitarra
ROOT=Path(__file__).resolve().parent;OUT=ROOT/(ROOT/'ULTIMA.txt').read_text().strip();TAG=OUT.name.split('-')[-1]
P=json.loads((OUT/'partitura-v4.json').read_text('utf8'));R=json.loads((OUT/'datos/recorrido.json').read_text('utf8'))
C0,C1=P['centro'];D=P['duracion'];E=P['eventos'];all_events=[e for es in E.values() for e in es]
assert len(E)==36 and all(E.values()) and len(all_events)==5717
ids={e['id'] for e in all_events};assert len(ids)==len(all_events)
for e in all_events:
 assert 0<=e['t']<D and e['dur']>0 and e['t']+e['dur']<=D+1e-6
 assert all(math.isfinite(e[k]) for k in ['t','dur','midi','hz','vel','pan'])
 assert abs(e['hz']/(440*2**((e['midi']-69)/12))-1)<1e-8
 assert e.get('ancestro') is None or e['ancestro'] in ids
for a,b in P['oscuridades']+P['agujeros_pared']:
 assert not [e for e in all_events if e['t']<b-1e-7 and e['t']+e['dur']>a+1e-7],(a,b)
center=[e for e in all_events if C0<=e['t']<C1]
assert len(center)==18 and all(e.get('libre') for e in center)
for k in ['voz','duo','corocuerda','corojunco','boca','bombo','caja','hat','tom','aro','ride','fotones']:
 assert not [e for e in E[k] if e['t']<C1 and e['t']+e['dur']>C0],k
assert all(c['fase_a_fin_centro']>c['fase_a_inicio_centro'] for c in P['relojes'])
assert np.linalg.norm(np.array(R['anclas'][0])-R['anclas'][-1])<1e-12
assert abs(R['salida_m']-R['llegada_m'])<1e-9 and abs(R['ascenso_m']-R['descenso_m'])<1e-9
debt=R['muestras'][-1]['deuda_cents'];assert debt>50
plans=json.loads((OUT/'datos/transportes.json').read_text('utf8'))
err=0
for p in plans:
 x=np.asarray(p['pi']);err=max(err,float(max(np.max(abs(x.sum(1)-p['a'])),np.max(abs(x.sum(0)-p['b'])))))
 assert np.all(x>=-1e-10) and err<1e-8
 assert p['ancestro'] in ids
# Afinación de guitarra: la caja/harmónico observada coincide con la altura escrita.
gerr=0
for e in E['guitarra']:
 par=e['parametros_motor'];ac=acuerdos(e['terreno']['deuda_cents'],[1,2,1])
 m=par['midi']+ac['cents'][par['caja']]/100+12*math.log2(par['parcial'])
 gerr=max(gerr,abs(m-e['midi']))
assert gerr<1e-9
# Histéresis con dos pasados y la MISMA presión observada.
def states_at(query):
 pts=P['controles']['organo']['controles']['presion'];tt=np.linspace(0,query,round(query*100)+1);pres=np.interp(tt,*np.array(pts).T);out=[]
 for j in range(6):
  state=False;on=.12+.125*j;off=max(0,on-.20)
  for p in pres:
   if p>=on:state=True
   elif p<=off:state=False
  out.append(int(state))
 return out
before=states_at(55);after=states_at(C1+.1);assert sum(before)==3 and sum(after)==5
for lyric in P['letra']:
 es=[e for e in E[lyric['capa']] if e['frase']==lyric['frase'] and lyric['t']-1e-7<=e['t']<lyric['fin']+1e-7]
 syllables={e['silaba'] for e in es};assert len(syllables)==len(lyric['silabas'].split()),lyric['frase']
# MusicXML: toda voz suma exactamente la duración de su medida, incluidos descansos.
XML=OUT/f'partitura-completa-r6-s1-{TAG}.musicxml';root=ET.parse(XML).getroot();parts=root.findall('part');assert len(parts)==36
micro=0;xml_count=0
for part in parts:
 assert len(part.findall('measure'))==len(P['medidas_editoriales'])
 for mm,ref in zip(part.findall('measure'),P['medidas_editoriales']):
  target=round((ref['fin']-ref['t'])/P['negra_s']*12000);counts=collections.Counter()
  for note in mm.findall('note'):
   counts[note.findtext('voice')]+=int(note.findtext('duration'))
   if note.find('rest') is None:xml_count+=1
   alt=note.findtext('pitch/alter')
   if alt and abs(float(alt)-round(float(alt)))>1e-8:micro+=1
  assert all(v==target for v in counts.values()),(part.attrib,mm.attrib,counts,target)
  assert (mm.find('attributes/time/senza-misura') is not None)==ref['free']
with (OUT/f'eventos-completos-r5-s1-{TAG}.csv').open(encoding='utf-8-sig',newline='') as f:assert len(list(csv.DictReader(f)))==len(all_events)
PDF=OUT/f'partitura-luciernagas-r6-s1-{TAG}.pdf';doc=fitz.open(PDF);assert len(doc)==36
outside=[]
for i,page in enumerate(doc):
 for block in page.get_text('dict')['blocks']:
  if 'lines' not in block:continue
  for ln in block['lines']:
   for span in ln['spans']:
    r=fitz.Rect(span['bbox'])
    if r.x0<0 or r.y0<0 or r.x1>page.rect.width+.1 or r.y1>page.rect.height+.1:outside.append([i+1,span['text']])
assert not outside,outside
assert not list(OUT.glob('*.wav')) and not list(OUT.glob('*.m4a')) and not list(OUT.glob('*.mp4'))
result={'partes':36,'eventos':len(all_events),'duracion_s':D,'centro_s':C1-C0,'eventos_libres_en_centro':len(center),
 'oscuridades':len(P['oscuridades']),'silencio_escrito_s':sum(b-a for a,b in P['oscuridades']),
 'agujeros_de_pared':len(P['agujeros_pared']),'eventos_metricos_o_vocales_en_centro':0,
 'relojes_con_fase_acumulada':P['relojes'],'deuda_final_cents':debt,'ruta_cerrada_m':R['distancia_m'],
 'organo_antes_047':before,'organo_despues_047':after,'error_afinacion_caja_semitonos':gerr,
 'planes_transporte':len(plans),'error_marginal_max':err,'xml_partes':len(parts),'xml_medidas_por_parte':len(P['medidas_editoriales']),
 'xml_notas_segmentadas':xml_count,'xml_notas_microtonales':micro,'pdf_paginas':len(doc),'texto_fuera_pdf':outside,
 'modelos':comprobar(),'sin_audio_master_o_video':True,
 'limites':'Escritura y casos numéricos, no audición. Los cortes se deberán comprobar sobre el audio futuro. PDF proporcional; XML/CSV/JSON conservan notas y controles.'}
with (OUT/'validacion-v4.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=1)
with (OUT/'fuentes/validar.py').open('xb') as f:f.write(Path(__file__).read_bytes())
print(json.dumps({k:result[k] for k in ['partes','eventos','centro_s','planes_transporte','xml_notas_microtonales','pdf_paginas','deuda_final_cents']},ensure_ascii=False))
