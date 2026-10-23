"""v8: tercer corte dentro del último plan y rutas definitivas de realización."""
from pathlib import Path
import json,math
ROOT=Path(__file__).resolve().parent;OUT=ROOT/(ROOT/'REVISION-EN-CURSO.txt').read_text().strip()
P=json.loads((OUT/'partitura-v7.json').read_text('utf8'));plans=json.loads((OUT/'datos/transportes-memoria-v6.json').read_text('utf8'))
last=plans[-1];end=P['agujeros_pared'][-1][1];r=[.87,1.,1.,.43]
assert last['t']<end<last['fin']
last['atenuaciones_durante_plan']=[{'t':end,'retenciones_destino':r,'causa':'tercer agujero; reapertura sin restaurar masas'}]
last['b_salida']=[v*w for v,w in zip(last['b'],r)]
for k,es in P['eventos'].items():
 for e in es:
  if e.get('plan')==last['id']:
   j=e['destino_columna'];e['ganancia_cortes']=[[end,math.sqrt(r[j])]]
   e['masa_fin_salida']=e['masa']*r[j]
  if k=='junco4' and e['frase']=='coda':
   e['masa']=last['b_salida'][-1];e['operacion_herencia']='última llegada, fase continua y pérdida del tercer corte'
P['analisis_datos']['planes']='datos/transportes-memoria-v8.json'
P['analisis_datos']['masa_final_tras_tercer_corte']=sum(last['b_salida'])
P['interpretacion']['datos_canonicos']='partitura-v8.json; datos/transportes-memoria-v8.json; INTERPRETACION.md'
P['interpretacion']['nuevos']['guitarra']='realizacion/modelos_memoria.py / GuitarraMemoria y contacto; afinaciones de encuentros interpoladas 30 ms'
P['interpretacion']['nuevos']['junco']='realizacion/modelos_memoria.py / plan_memoria; realizacion/instrumentos.py / Junco; fases y ganancias por arista'
P['interpretacion']['existentes']['tres-tiempos']='realizacion/motores.py: arpa afinable e inyección compleja de cuerda'
P['interpretacion']['inyeccion_cuerda']='realizacion/motores.py: inyeccion_modal en red_modal'
P['controles']['arpa']['variante']='realizacion/motores.py'
P['interpretacion']['fusion_aristas']='transición de amplitudes de 12 ms entre sumas entrantes y salientes, conservando fases; no asumir conservación acústica'
P['interpretacion']['ganancia_cortes']='ganancia_cortes por arista multiplica su envolvente desde el tiempo indicado; el último plan conserva la pérdida en b_salida y coda'
P['version']='luciernagas-partitura-8.0';P['correcciones']+=['El tercer corte cae dentro del último plan: se atenúa su reapertura y se conserva la pérdida en b_salida/coda.',
 'Rutas definitivas de realización agrupadas en realizacion/. El análisis separa masas de plan y masas tras cortes.']
(OUT/'realizacion').mkdir(exist_ok=False)
for name,source in [('modelos_memoria.py',ROOT/'modelos_memoria.py'),('instrumentos.py',ROOT/'instrumentos.py'),('motores.py',OUT/'fuentes/motores-memoria.py')]:
 with (OUT/'realizacion'/name).open('xb') as f:f.write(source.read_bytes())
for name,value in [('partitura-v8.json',P),('datos/transportes-memoria-v8.json',plans)]:
 with (OUT/name).open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=1)
with (OUT/'fuentes/cerrar_estado.py').open('xb') as f:f.write(Path(__file__).read_bytes())
print('v8: masa final tras tres cortes',sum(last['b_salida']))
