"""Pruebas que pueden refutar la escritura; no certifican su musicalidad."""
from comun import *
from instrumentos_revision import transbordos,comprobaciones,juguete,motor_fallido
import xml.etree.ElementTree as ET

def main():
    out=ultimo();P=leer(score());R=leer(out/'viaje.json');checks={}
    assert len(P['eventos'])==30 and all(P['eventos'].values());checks['partes']=30
    count=0
    for c,es in P['eventos'].items():
        assert all(es[k]['t']<=es[k+1]['t'] for k in range(len(es)-1))
        for e in es:
            count+=1;assert np.isfinite([e['t'],e['dur'],e['midi'],e['vel']]).all()
            assert e['dur']>0 and 0<=e['t'] and e['t']+e['dur']<=240.000001
            assert abs(e['pulso']*Q-e['t'])<1e-6
            if e['t']<200 and e['t']+e['dur']>180:
                assert c in ['radio-chofer','radio-pasajera','estatica-senal'] and e.get('libre')
    checks['eventos']=count;checks['capas_metricas_en_break']=0
    assert P['break_libre']['corte']['t']==179.96 and P['break_libre']['t1']==200
    assert P['break_libre']['corte']['fade_ms']==35;checks['corte_y_vaciado']='escritos; pendientes de comprobar sobre audio futuro'
    assert not any(130<=e['t']<170 for c in ['voz-verso','voz-respuesta'] for e in P['eventos'][c]);checks['solo_sin_solista_humano']=True
    mat=np.array(P['holonomia']['matrices'][-1]);assert np.max(abs(mat.T@mat-np.eye(3)))<1e-12 and np.linalg.norm(mat-np.eye(3))>.5
    assert np.max(abs(transbordos(.73,0)[-1]-np.eye(3)))<1e-12
    assert P['holonomia']['grafo_cerrado_nodos_radiales'][0]==P['holonomia']['grafo_cerrado_nodos_radiales'][-1]
    checks['controlador']=comprobaciones();checks['caso_con_B_identidad']='retorno identidad'
    assert R['ascenso_m']>100 and R['descenso_m']>100 and abs(R['origen_m']-R['final_m'])<1e-6
    assert np.allclose([R['u'][0],R['v'][0]],[R['u'][-1],R['v'][-1]])
    checks['ruta_cerrada_con_subida_y_bajada']=True
    assert len(leer(out/'impactos-bolsa.json'))>10
    bolsa=P['eventos']['bolsa-juguetes'];assert min(e['t'] for e in bolsa)<10
    mb=P['eventos']['mbira-boca'];assert min(e['t'] for e in mb)>min(e['t'] for e in bolsa)
    checks['fuente_presentada_antes_de_aprendizaje']=True;checks['impactos_modelados']=len(leer(out/'impactos-bolsa.json'))
    root=ET.parse(next(out.glob('*.musicxml'))).getroot();assert len(root.findall('part'))==30
    fractional=0
    for part in root.findall('part'):
        ms=part.findall('measure');assert len(ms)==96
        assert ms[72].find('attributes/time/senza-misura') is not None
        assert ms[80].findtext('attributes/time/beats')=='4'
        for measure in ms:
            voices={}
            for nt in measure.findall('note'):
                voice=nt.findtext('voice');voices[voice]=voices.get(voice,0)+int(nt.findtext('duration'))
                al=nt.findtext('pitch/alter')
                if al is not None and abs(float(al)-round(float(al)))>1e-8:fractional+=1
            assert all(v==3840 for v in voices.values()),(part.attrib,measure.attrib,voices)
    assert fractional>0;checks['xml']='30x96 posiciones; cada voz 3840 ticks; break senza misura';checks['notas_microtonales_xml']=fractional
    for j in range(3):assert np.isfinite(juguete(j,duracion=.1)).all()
    assert np.isfinite(motor_fallido(duracion=.1)).all();checks['motores']='salidas numéricas finitas; no se exportó audio'
    run=leer(out/'ejecucion.json');first=next((out/'proceso').glob('01-*.png'));b=first.read_bytes()
    h=hashlib.sha256(b+run['version'].encode()+run['nonce'].encode()+(out/'reescribir-fuente.py').read_bytes()).hexdigest();assert h==run['hash'];checks['identificador_reproducible']=True
    assert not list(out.glob('*.wav')) and not list(out.glob('*.mp4')) and not list(out.glob('*.m4a'));checks['sin_render_de_cancion_ni_video']=True
    jsave(out/'validacion-r4.json',checks);print(json.dumps(checks,ensure_ascii=False))

if __name__=='__main__':main()
