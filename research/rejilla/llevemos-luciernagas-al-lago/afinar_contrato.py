"""Ajustes de interpretación tras revisar el cálculo instrumental, sin audio."""
from pathlib import Path
import json,hashlib
import numpy as np
from instrumentos import parametros_guitarra,comprobar
ROOT=Path(__file__).resolve().parent;OUT=ROOT/(ROOT/'ULTIMA.txt').read_text().strip()
P=json.loads((OUT/'partitura-v2.json').read_text('utf8'));R=json.loads((OUT/'datos/recorrido.json').read_text('utf8'))
rows=R['muestras'];t=np.array([r['t'] for r in rows]);mapping={'altura_m':'z_m','pendiente':'pendiente','deuda_cents':'deuda_cents','u':'u','v':'v'}
for k,events in P['eventos'].items():
 for e in events:
  e['terreno']={key:float(np.interp(e['t'],t,[r[col] for r in rows])) for key,col in mapping.items()}
  if k=='guitarra':e['parametros_motor']=parametros_guitarra(e)
P['version']='partitura-3.0'
P['interpretacion']['nuevos']['guitarra']='instrumentos-v3.py / parametros_guitarra(e) → Guitarra.gesto; avanzar con deuda, pesos (1,2,1), humedad y presión. Corrige doble aplicación de cents y separa nodo de dedo y punto de púa.'
P['interpretacion']['nuevos']['junco']='instrumentos-v3.py / Junco: 16 fases persistentes, cuatro salidas; integrar cada arista del plan en log Hz. No se exportó audio.'
P['correcciones']+=['Armónico: tocar un nodo no significa pulsar allí; se separó el punto de púa para no anular el parcial deseado.',
 'Guitarra: adaptar altura de la caja escrita a fundamental antes de aplicar su desplazamiento, evitando duplicar cents.',
 'Recuperar terreno correcto para los dos eventos de órgano añadidos y segmentos recortados. Sin cambio de notas o tiempos de v2.']
for name,value in [('partitura-v3.json',P),('datos/sondas-instrumentos-v3.json',comprobar())]:
 with (OUT/name).open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=1)
for name,src in [('fuentes/instrumentos-v3.py',ROOT/'instrumentos.py'),('fuentes/afinar_contrato.py',Path(__file__))]:
 with (OUT/name).open('xb') as f:f.write(src.read_bytes())
with (OUT/'PARTITURA-VIGENTE.txt').open('x',encoding='utf8') as f:f.write('partitura-v3.json\n')
print('partitura 3: notas y tiempos conservados, contratos instrumentales corregidos')
