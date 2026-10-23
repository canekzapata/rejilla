from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent;OUT=ROOT/(ROOT/'ULTIMA.txt').read_text().strip()
P=json.loads((OUT/'partitura-v3.json').read_text('utf8'));a,b=P['centro'];removed=[]
for k,events in P['eventos'].items():
 final=[]
 for e in events:
  if not e.get('libre'):
   if a<=e['t']<b:removed.append({'capa':k,'evento':e,'motivo':'continuación métrica después del corte'});continue
   if e['t']<a<e['t']+e['dur']:e['dur']=round(a-.035-e['t'],8)
  if e['dur']>.00001:final.append(e)
 P['eventos'][k]=final
P['version']='partitura-4.0';P['correcciones'].append('Retirar una continuación de gong creada al recortar el corte global; V tiene exactamente 18 gestos libres, sin restos métricos.')
for name,value in [('partitura-v4.json',P),('datos/correccion-centro-v4.json',removed)]:
 with (OUT/name).open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=1)
with (OUT/'PARTITURA-FINAL.txt').open('x',encoding='utf8') as f:f.write('partitura-v4.json\n')
with (OUT/'fuentes/cerrar_centro.py').open('xb') as f:f.write(Path(__file__).read_bytes())
print('v4: retiradas',len(removed),'continuaciones; eventos',sum(map(len,P['eventos'].values())))
