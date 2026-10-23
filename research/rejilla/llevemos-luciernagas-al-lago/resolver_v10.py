"""Interpretación de controles de v10.1, sin generar audio ni sustituir motores."""
from pathlib import Path
import json,math
import numpy as np
ROOT=Path(__file__).resolve().parent
def cargar():
    out=ROOT/(ROOT/'PARTITURA-EN-CURSO.txt').read_text().strip()
    return out,json.loads((out/'partitura-v10.1.json').read_text(encoding='utf8'))
def integral(m0,m1,d,u=1):
    k=math.log(2)*(m1-m0)/12
    return 440*2**((m0-69)/12)*d*(math.expm1(k*u)/k if abs(k)>1e-12 else u)
def complejo(pairs):return np.array([complex(a,b) for a,b in pairs])
def centro(p,t):
    segs=p['centro_v10']['segmentos'];s=next((s for s in segs if s['t']<=t<s['fin']),segs[-1])
    dt=np.clip(t-s['t'],0,s['fin']-s['t']);dur=s['fin']-s['t'];u=dt/dur
    z=complejo(s['z_inicio'])*np.exp(-np.array(s['gamma'])*dt)
    phase=np.array([2*np.pi*integral(m,n,dur,u) for m,n in zip(s['midi_inicio'],s['midi_fin'])]);z*=np.exp(1j*phase)
    if s.get('cruce'):
        c=s['cruce'];ramp=c['aplicar_antes_de_fin_s'];fraction=float(np.clip((t-(s['fin']-ramp))/ramp,0,1))
        i,j=c['par'];a=c['angulo_rad']*fraction;zi,zj=z[i],z[j];z[i]=math.cos(a)*zi-math.sin(a)*zj;z[j]=math.sin(a)*zi+math.cos(a)*zj
    return z
def ventanas(e,cortes):
    windows=[w[:] for w in e['salidas']]
    for c in cortes:
        a,b=c['t'],c['fin'];new=[]
        for u,v in windows:
            if v<=a or u>=b:new.append([u,v])
            else:
                if u<a:new.append([u,a])
                if v>b:new.append([b,v])
        windows=new
    return windows
def resolver(p):
    rows=[]
    for part in p['partes']:
        name=part['id']
        for e in p['eventos'][name]:
            row={'parte':name,'motor':part['motor'],'evento':e['id'],'t':e['t'],'dur':e['dur'],
                'parametros':{'midi':e['midi'],'vel':e['vel'],'dur':e['dur']},'salidas':ventanas(e,p['cortes_buses']),
                'ganancia_relativa_db':p['niveles_relativos_v10_db'][name],'pan':e['pan']}
            if name=='guitarra':
                row['parametros']=e['parametros_motor'];row['afinaciones_cajas_cents']=e['afinaciones_cajas_cents']
                if e.get('contacto'):row['contacto']=e['contacto']
            if name in ['voz','duo','corocuerda','corojunco']:
                row['texto']=e.get('texto','');row['acento']=e.get('acento',False);row['respiracion_antes']=e.get('respiracion_antes',False)
            if name.startswith('junco'):
                for k in ['midi_fin','fase_inicial_rad','masa','amortiguacion_s_1','ganancia_cortes','segmento_centro','plan']:
                    if k in e:row[k]=e[k]
                if 'segmento_centro' in e:row['control_central']=p['centro_v10']['segmentos'][e['segmento_centro']]
            if e.get('inyeccion_modal'):row['inyeccion_modal']=e['inyeccion_modal']
            if e.get('pieza'):row['parametros']['pieza']=e['pieza']
            if p['centro'][0]<=e['t']<p['centro'][1]:
                field='juncos_conjunto' if name.startswith('junco') else name if name in ['guitarra','cuerda'] else 'objetos'
                row['captacion_objetivo_dbfs_activo']=p['centro_v10']['captacion_db'][field]
                row['ganancia_compartida']='juncos_conjunto' if name.startswith('junco') else field
            rows.append(row)
    return sorted(rows,key=lambda r:(r['t'],r['parte'],r['evento']))
if __name__=='__main__':
    out,p=cargar();rows=resolver(p)
    with (out/'interpretacion-resuelta-v10.1.json').open('x',encoding='utf8',newline='\n') as f:json.dump({'eventos':rows,'controles':p['controles'],'relojes':p['relojes_v10']},f,ensure_ascii=False,indent=1)
    with (out/'fuentes/resolver_v10.py').open('xb') as f:f.write(Path(__file__).read_bytes())
    print('Interpretación resuelta:',len(rows),'eventos; no audio')
