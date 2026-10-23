"""Auditoría editorial y resolución de referencias de la reescritura v10."""
from pathlib import Path
import json,copy,math
ROOT=Path(__file__).resolve().parent;OUT=ROOT/(ROOT/'PARTITURA-EN-CURSO.txt').read_text().strip()
P=json.loads((OUT/'partitura-v10.json').read_text(encoding='utf8'));P['version']='luciernagas-partitura-10.1'
ids={e['id'] for es in P['eventos'].values() for e in es};retired=[]
for es in P['eventos'].values():
    for e in es:
        if e.get('ancestro') and e['ancestro'] not in ids:
            retired.append({'evento':e['id'],'referencia_anterior':e['ancestro']})
            e['referencia_editorial_v8']=e['ancestro'];e['ancestro']=None
        if e.get('contribuyentes_estado'):
            missing=[a for a in e['contribuyentes_estado'] if a not in ids]
            if missing:e['contribuyentes_editoriales_v8']=missing;e['contribuyentes_estado']=[a for a in e['contribuyentes_estado'] if a in ids]
P['referencias_editoriales_retiradas_v10']=retired
# Las recepciones de transportes registran todos los contribuyentes, además del identificador corto.
groups=[[a] for a in P['centro_v10']['paquete']['ancestros_fin']]
lookup={e['id']:e for es in P['eventos'].values() for e in es}
for plan in P['transportes_v10']:
    plan['contribuyentes_origen']=copy.deepcopy(groups)
    for e in lookup.values():
        if e.get('plan')==plan['id']:e['contribuyentes_estado']=groups[e['origen_fila']]
    groups=plan['eventos_destino']
# El mismo valor de espera modifica enlaces de arpa, voz y vectores: no una etiqueta suelta.
tau=P['centro_v10']['paquete']['espera_aprendida_s']
for i,link in enumerate(P['controles']['arpa']['enlaces']):link[3]=(tau+.3)*(1 if i%2==0 else -1)
P['controles']['junco']={'centro':'centro_v10.segmentos','planes':'transportes_v10',
    'captacion':'centro_v10.paquete','ganancia_inicial':'centro_v10.paquete.normalizacion_inicial_junco',
    'fase':'integral exponencial por segmento; cruces del centro en los últimos 90 ms; fusiones con rampa 12 ms',
    'masa':'norma de control y distribución abstracta; no julios acústicos'}
P['controles']['guitarra']['afinacion']='Estado de encuentro por tramos; actualizar cada 5 ms en el controlador de referencia, sin volver a afinar todas las cajas a un promedio.'
P['controles']['guitarra']['simulacion_de_captacion']='fuentes/recomponer_v10.py:guitar_capture; dt=.005, presión en punto medio; captura completa a 105.4 s'
P['controles']['cuerda']['inyeccion_106_2']='La recepción asigna un nuevo estado de tres cuerdas y siete modos: cero salvo los cuatro modos recibidos en la primera. La fase de guitarra ya está incluida en z.'
P['relojes_v10']=[{'parte':part,'periodo_s':n*P['negra_s']/4,'fase_en_t0':0,'fase_disparo':9.31/(n*P['negra_s']/4),
    'regla':'fase=t/periodo_s; emisiones de exposición seleccionadas en 9.31+k*periodo; después la frase puede abrir otras ventanas sin reiniciar fase'}
    for part,n in [('mbira',19),('arpaboca',17),('fotones',29)]]
P['relojes_editoriales_v8']=P.pop('relojes',[])
for clock in P['relojes_v10']:
    for e in P['eventos'][clock['parte']]:
        if 'fase_acumulada' in e:e['fase_editorial_v8']=e.pop('fase_acumulada')
        e['fase_reloj']=e['t']/clock['periodo_s'];e['periodo_s']=clock['periodo_s']
P['niveles_relativos_v10_db']={'guitarra':0,'pua':-14,'krar':-7,'berimbau':-11,'arpa':-10,'cuerda':-9,'organo':-12,
    'clarinete':-7,'chelo':-10,'contrabajo':-6,'bajo':-7,'androide':-4,'terminal':-2,'piano':-10,'mbira':-13,'arpaboca':-14,
    'campana':-17,'waterphone':-17,'gong':-16,'bombo':-6,'caja':-7,'hat':-17,'tom':-12,'aro':-15,'ride':-15,'fotones':-18,
    'junco1':-12,'junco2':-12,'junco3':-12,'junco4':-12,'voz':-6,'duo':-8,'corocuerda':-7,'corojunco':-7,'boca':-15,'sala':-14}
P['mezcla_escrita_v10']={'referencia':'Normalizar nivel activo una vez por motor; nivel relativo a referencia -20 dBFS. Los cuatro juncos comparten una sola ganancia.',
    'centro':'Durante V sustituir niveles ordinarios por centro_v10.captacion_db; fijos por campo, no AGC de RMS ni normalización por destello.',
    'verificacion_pendiente':'Escuchar equilibrio, dicción, aspereza y pared al interpretar; estos niveles son decisiones de partitura, no medidas de audio.'}
P['reglas']['filiacion']='ancestro identifica fuente compositiva vigente; referencias a eventos v8 retirados se conservan como referencia_editorial_v8, sin fingir transformación causal'
P['reglas']['fase']='fase absoluta de estado; reloj interno continuo y ventanas audibles separadas; ningún mute reinicia el estado'
P['interpretacion']['datos_canonicos']='partitura-v10.1.json; resolver_v10.py expande eventos, ganancias, cortes y control del centro'
P['interpretacion']['no_leer_metadatos_historicos']='relojes_editoriales_v8 y referencias editoriales son procedencia, no controles vigentes'
with (OUT/'partitura-v10.1.json').open('x',encoding='utf8',newline='\n') as f:json.dump(P,f,ensure_ascii=False,indent=1)
with (OUT/'datos/referencias-resueltas-v10.1.json').open('x',encoding='utf8',newline='\n') as f:json.dump(retired,f,ensure_ascii=False,indent=1)
with (OUT/'fuentes/afinar_v10.py').open('xb') as f:f.write(Path(__file__).read_bytes())
print('Referencias editoriales separadas:',len(retired),'espera aplicada:',tau)
