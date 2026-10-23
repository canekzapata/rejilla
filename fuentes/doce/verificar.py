"""Pruebas de comportamiento sobre audio y estado; no puntúan belleza."""
from pathlib import Path
import json,sys
import numpy as np
import motores as m
import partituras as p
from producir import prueba_boca,guardar_json

def main():
    report={'boca':prueba_boca()}
    # The future event affects the CURRENT attack before the future is played.
    one={'notas':[p.nota(.1,60,.7),p.nota(1.5,67,.5)]}
    two={'notas':[p.nota(.1,60,.7),p.nota(1.5,76,.5)]}
    a,_,_=m.render('piano',one,2.5);b,_,_=m.render('piano',two,2.5)
    diff=float(np.sqrt(np.mean((a[3200:6400]-b[3200:6400])**2)))
    assert diff>.001
    report['piano']={'rms_diferencia_en_ataque_actual_por_cambiar_solo_nota_futura':diff}
    arpa={'notas':[p.nota(.1,50,.2,.9,cuerda=0)],'enlaces':[[.8,0,1,1.3]],'cuerdas_midi':[50,57,60,64,69]}
    a,tr,info=m.render('arpa',arpa,2.5)
    before=float(tr['energia_1'][round(.6*m.SR)]);after=float(tr['energia_1'][round(1.4*m.SR)])
    assert before<1e-12 and after>.001 and info['error_max_intercambio']<1e-10
    report['arpa']={'cuerda_receptora_antes':before,'cuerda_receptora_despues':after,'error_norma':info['error_max_intercambio']}
    cuerda={'notas':[p.nota(.1,50,.2)],'controles':{'arco':[[0,0]],'presion':[[0,0]]}}
    bow={'notas':[p.nota(.1,50,.2)],'controles':{'arco':[[0,.9]],'presion':[[0,.9]]}}
    a,_,_=m.render('cuerda',cuerda,2.5);b,_,info=m.render('cuerda',bow,2.5)
    change=float(np.sqrt(np.mean((a-b)**2))); assert change>.005 and info['error_max_intercambio']<1e-10
    report['cuerda']={'rms_cambio_gesto':change,'error_norma':info['error_max_intercambio']}
    base={'notas':[p.nota(.15,57,.3)],'controles':{'pliegue_0':[[0,0]],'pliegue_1':[[0,0]]}}
    folded={'notas':base['notas'],'controles':{'pliegue_0':[[0,.9]],'pliegue_1':[[0,.8]]}}
    a,_,_=m.render('sala',base,2.5);b,_,_=m.render('sala',folded,2.5)
    delta=float(np.sqrt(np.mean((a-b)**2)));tail=float(np.sqrt(np.mean(a[round(.6*m.SR):round(1.3*m.SR)]**2)))
    assert delta>1e-4 and tail>1e-5
    report['sala']={'rms_diferencia_topologia':delta,'rms_resonancia_tras_excitacion':tail}
    # Retain the same pressure twice; history changes a real rendered divisor.
    spec=p.demo('organo');a,tr,info=m.render('organo',spec['partitura'],24)
    pairs={k:[float(v[12*m.SR]),float(v[21*m.SR])] for k,v in tr.items() if k.startswith('divisor_')}
    assert any(abs(x-y)>.7 for x,y in pairs.values())
    report['organo']={'presion_ambas':float(tr['presion'][12*m.SR]),'estados':pairs}
    probes={}
    for i,k in enumerate(['cristal','estacion','terminal','plasma','androide','fotones']):
        spec={'notas':[p.nota(.1,45 if k=='androide' else 69,1.8,.75)],'controles':{'vector_x':[[0,0],[2.5,1]],'vector_y':[[0,1],[2.5,0]]}}
        a,_,_=m.render(k,spec,2.5,semilla=66);b,_,_=m.render(k,spec,2.5,semilla=66)
        rms=float(np.sqrt(np.mean(a*a)));err=float(abs(a-b).max())
        assert np.isfinite(a).all() and rms>1e-4 and err==0
        probes[k]={'rms':rms,'error_repeticion_misma_semilla':err,'pico':float(abs(a).max())}
    report['electronicos']=probes
    # The two opposite corners actually change the vector instrument spectrum.
    zero={'notas':[p.nota(.1,69,1.5,.7)],'controles':{'vector_x':[[0,0]],'vector_y':[[0,0]]}}
    one={'notas':zero['notas'],'controles':{'vector_x':[[0,1]],'vector_y':[[0,1]]}}
    a,_,_=m.render('terminal',zero,2);b,_,_=m.render('terminal',one,2)
    delta=float(np.sqrt(np.mean((a-b)**2)));assert delta>.005
    report['terminal_cambio_vector']=delta
    report['limites']='Sin escucha humana propia; no verifica belleza, identidad de una boca ni inteligibilidad. Transferencia modal es norma de envolventes, no energía acústica.'
    if len(sys.argv)>1:guardar_json(Path(sys.argv[1]),report)
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
