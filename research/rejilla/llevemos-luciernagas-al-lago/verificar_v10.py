"""Comprobar relaciones y edición; no inferir musicalidad desde las medidas."""
from pathlib import Path
import json,math,sys
import numpy as np
from resolver_v10 import cargar,centro,complejo,resolver,ventanas,integral
out,p=cargar();ids={e['id']:e for es in p['eventos'].values() for e in es};allrows=[e for es in p['eventos'].values() for e in es]
assert len(ids)==len(allrows);assert len(p['partes'])==36 and all(p['eventos'].values())
for e in allrows:
    assert 0<=e['t']<p['duracion'] and e['dur']>0 and e['t']+e['dur']<=p['duracion']+1e-6,e['id']
    assert abs(float(e['hz'])/(440*2**((e['midi']-69)/12))-1)<1e-8,e['id']
    assert e.get('ancestro') is None or e['ancestro'] in ids,e['id']
    assert all(a in ids for a in e.get('contribuyentes_estado',[])),e['id']
    for a,b in e['salidas']:assert e['t']-1e-7<=a<b<=e['t']+e['dur']+1e-7,(e['id'],a,b)
for lyric in p['letra']:assert all(a in ids for a in lyric['ids'])
assert any('raíz' in l['texto'] for l in p['letra'] if l['t']<93)
assert any('tenis' in l['texto'] for l in p['letra'] if l['t']<93)
assert len([l for l in p['letra'] if l['capa']=='voz' and l['t']<93])==4
centerparts=[]
for part,es in p['eventos'].items():
    if any(p['centro'][0]<=e['t']<p['centro'][1] for e in es):centerparts.append(part)
assert set(centerparts)<=set(['guitarra','cuerda','waterphone','campana','junco1','junco2','junco3','junco4'])
gates=p['centro_v10']['ventanas_por_voz'];assert len({json.dumps(w) for w in gates})==4
segments=p['centro_v10']['segmentos'];maxcontinuity=0.;maxrotation=0.
for i,s in enumerate(segments):
    z0=complejo(s['z_inicio']);z1=complejo(s['z_fin_antes_cruce']);d=s['fin']-s['t']
    expected=z0*np.exp(-np.array(s['gamma'])*d)*np.exp(1j*np.array([2*np.pi*integral(m,n,d) for m,n in zip(s['midi_inicio'],s['midi_fin'])]))
    assert np.max(abs(expected-z1))<1e-10
    if s.get('cruce'):
        r=np.array(s['cruce']['matriz']);assert np.max(abs(r.T@r-np.eye(4)))<1e-12
        z2=r@z1;maxrotation=max(maxrotation,abs(np.sum(abs(z1)**2)-np.sum(abs(z2)**2)))
        assert np.max(abs(z2-complejo(segments[i+1]['z_inicio'])))<1e-10
        before=centro(p,np.nextafter(s['fin'],-np.inf));after=centro(p,s['fin']);maxcontinuity=max(maxcontinuity,float(np.max(abs(before-after))))
assert maxcontinuity<1e-8,maxcontinuity
packet=p['centro_v10']['paquete'];zf=complejo(packet['junco_fin_centro_z']);assert np.max(abs(centro(p,p['centro'][1])-zf))<1e-10
assert abs(np.linalg.norm(complejo(packet['junco_z']))*packet['normalizacion_inicial_junco']-1)<1e-12
assert packet['normas'][1]<packet['normas'][0]
tau=.42+1.1*(1-packet['normas'][1]/packet['normas'][0]);assert abs(tau-packet['espera_aprendida_s'])<1e-12
contacts=[e for e in p['eventos']['guitarra'] if e.get('contacto')];assert not contacts[0]['contacto']['deslizamientos_s'];assert contacts[-1]['contacto']['deslizamientos_s']
plans=p['transportes_v10'];maxmarg=0.
assert np.max(abs(np.array(plans[0]['masa_recibida'])-abs(zf)**2))<1e-12
assert np.max(abs(np.array(plans[0]['source'])-np.array(packet['junco_fin_centro_midi'])))<1e-12
for i,s in enumerate(plans):
    pi=np.array(s['pi']);err=max(np.max(abs(pi.sum(1)-s['a'])),np.max(abs(pi.sum(0)-s['b'])));maxmarg=max(maxmarg,float(err));assert err<1e-9
    assert np.min(pi)>=-1e-12
    if i:
        assert np.max(abs(np.array(s['masa_recibida'])-np.array(plans[i-1]['b_salida'])))<1e-12
        assert np.max(abs(np.array(s['source'])-np.array(plans[i-1]['target'])))<1e-12
    assert sum(s['b_salida'])<=sum(s['masa_recibida'])+1e-12
assert p['analisis_datos']['masa_final']<p['analisis_datos']['masa_inicial_transporte']
coda=next(e for e in p['eventos']['junco4'] if e['t']>246.7);assert abs(coda['masa']-plans[-1]['b_salida'][3])<1e-12
# Ventana máxima sin salida escrita, después de todos los cortes; no prueba nivel audible.
windows=sorted(w for e in allrows for w in ventanas(e,p['cortes_buses']) if w[1]>p['centro'][0] and w[0]<p['centro'][1]);merged=[]
for a,b in windows:
    a=max(a,p['centro'][0]);b=min(b,p['centro'][1])
    if merged and a<=merged[-1][1]:merged[-1][1]=max(b,merged[-1][1])
    else:merged.append([a,b])
gaps=[];last=p['centro'][0]
for a,b in merged:
    if a>last:gaps.append([last,a])
    last=b
if last<p['centro'][1]:gaps.append([last,p['centro'][1]])
maxgap=max(b-a for a,b in gaps)
# Guardia contra vacíos accidentales largos; no es una cuota estética universal.
assert maxgap<contacts[-1]['dur'],maxgap
resolved=resolver(p);assert len(resolved)==len(allrows);assert all('ganancia_relativa_db' in e for e in resolved)
report={'version':p['version'],'partes':len(p['partes']),'eventos':len(allrows),'referencias_causales_validas':True,
 'frases_solista_antes_centro':4,'episodios_guitarra':len(p['desarrollo_v10']),'centro_capas':centerparts,
 'cuatro_ventanas_distintas':True,'mayor_hueco_escrito_centro_s':maxgap,'gaps_centro':gaps,
 'continuidad_compleja_centros_error_max':maxcontinuity,'error_rotacion_norma_max':float(maxrotation),
 'planes':len(plans),'error_marginal_max':maxmarg,'espera_aprendida_s':tau,'masa_entrada_regreso':p['analisis_datos']['masa_inicial_transporte'],
 'masa_final':p['analisis_datos']['masa_final'],'coda_hereda_ultimo_corte':True,
 'contactos_deslizamientos':[c['contacto']['deslizamientos_s'] for c in contacts],
 'limite':'Verifica datos, controles y continuidad; no audición ni certificación de balance o calidad musical.'}
file=out/'validacion-escritura-v10.1.json'
with file.open('x',encoding='utf8',newline='\n') as f:json.dump(report,f,ensure_ascii=False,indent=1)
with (out/'fuentes/verificar_v10.py').open('xb') as f:f.write(Path(__file__).read_bytes())
print(json.dumps(report,ensure_ascii=False,indent=1))
