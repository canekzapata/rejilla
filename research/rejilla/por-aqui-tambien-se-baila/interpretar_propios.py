"""Interpretar los controles escritos: FEM, redes/Talbot, bolsa, radio y bordones."""
from audio_comun import *
from instrumentos import membrana,chirp,red_laser,raspador,auxiliar
from instrumentos_revision import juguete,motor_fallido
from fractions import Fraction
from scipy.signal import resample_poly,stft,istft
import gc

def main():
    out,cfg,P,work=contexto();R=work/'fuentes';N=round(cfg['duracion']*SR);S=leer(depo());via=leer(out/'viaje.json');receipts={};TT=importar(BASE/'fuentes/tres-tiempos/motores.py','baila_render_tt');TA=importar(BASE/'fuentes/talbot/tapete.py','baila_render_talbot')
    def store(c,y):
        assert len(y)==N;rawsave(R,c,corte(np.asarray(y,np.float32),c in ['radio-chofer','radio-pasajera','estatica-senal']));print(c,round(activo(y),6),flush=True)
    for c in ['membrana-din','membrana-ta','membrana-thom','barro','pandero','bolsa-juguetes','raspador']:
        if (R/(c+'.f32')).exists():continue
        y=np.zeros((N,2),np.float32);meta=[]
        for j,e in enumerate(P['eventos'][c]):
            if c.startswith('membrana'):
                load=round(e.get('carga_central',.5),2);z=membrana(c.split('-')[-1],float(hz(e['midi'])),max(.3,e['dur']+(.65 if c.endswith('din') else .2)),load,e['vel']);meta.append({'t':e['t'],'carga_escrita':e.get('carga_central',.5),'carga_calculada':load})
            elif c in ['barro','pandero']:z=auxiliar(c,e['vel'],SEED+j)
            elif c=='bolsa-juguetes':
                obj={'trompo de lámina':0,'cascabel':1,'silbato de barro':2}[e['objeto']];z=juguete(obj,e.get('fuerza_impacto',.4),SR,.7)*e['vel'];meta.append({'t':e['t'],'objeto':obj,'origen':e['frase']})
            else:
                state=e['estado_deposito'];path=np.array(S['caminos'][min(319,state*16)]);profile=(np.array(S['z_inicial_m'])+np.array(S['depositos_m'][state]))[np.arange(24),path]
                if e['direccion']=='contra el descenso':profile=profile[::-1]
                grade=abs(float(np.interp(e['t'],via['t'],via['pendiente'])));z,m=raspador(profile,e['dur'],speed=.75+min(.6,grade*2),seed=22+j);z*=e['vel']*12;meta.append({'t':e['t'],'vel_lectura':.75+min(.6,grade*2),**m})
            poner(y,z,e['t'],p={'barro':-.35,'pandero':.42,'bolsa-juguetes':.35,'membrana-din':-.15,'membrana-ta':.15,'membrana-thom':-.1,'raspador':-.3}[c])
        store(c,y);receipts[c]=meta;del y;gc.collect()
    # Calibración fija de transferencia, independiente de los pesos del solo.
    # Conserva sus relaciones en cada estado; nunca normaliza cada célula.
    probe=np.zeros(SR);z=chirp(62,.3,.7);probe[:len(z)]=z;ref=np.sum(probe*probe);cal={};lasers={}
    for c,tau in [('laser-directo',Fraction(0)),('laser-laberinto',Fraction(1,3)),('laser-talbot',Fraction(2,5))]:
        if c=='laser-directo':cal[c]=1.
        else:
            test=TA.talbot(probe,tau,hilos=32);q,_=red_laser(test,3,cola=1.5);cal[c]=float(np.sqrt(ref/(np.sum(q*q)+1e-20)))
        if (R/(c+'.f32')).exists():continue
        y=np.zeros((N,2),np.float32);cells={};rec=[]
        for e in P['eventos'][c]:cells.setdefault(int(e['t']//5),[]).append(e)
        for k,es in cells.items():
            t0=k*5;x=np.zeros(5*SR,np.float32)
            for e in es:
                q=chirp(e['midi'],e['dur'],e['vel'])*e.get('fase_signo',1);i=round((e['t']-t0)*SR);n=min(len(q),len(x)-i)
                if n>0:x[i:i+n]+=q[:n]
            if c=='laser-directo':q=pan(x,.02);meta={}
            else:
                zz=TA.talbot(x,tau,hilos=32);energy=float(abs(np.sum(zz*zz)-np.sum(x*x))/(np.sum(x*x)+1e-20));state=min(19,int(t0/12));q,meta=red_laser(zz,state,cola=1.7);q*=cal[c];meta.update(error_energia_talbot=energy,estado=state)
            poner(y,q,t0);rec.append({'t':t0,'tau':str(tau),'calibracion_fija':cal[c],'signos':[e.get('fase_signo',1) for e in es],**meta})
        store(c,y);lasers[c]=rec;del y;gc.collect()
    receipts['laser']=lasers;receipts['calibracion_laser']=cal
    if not (R/'organo-drone.f32').exists():
        y=np.zeros((N,2),np.float32)
        for j,e in enumerate(P['eventos']['organo-drone']):
            z=TT.tono(e['midi'],e['dur'],SR,e['vel'],'estacion',22+j);poner(y,z,e['t'],p=(-1 if j%2 else 1)*.45)
        store('organo-drone',y);del y;gc.collect()
    if not (R/'boca-ritmica.f32').exists():
        y=np.zeros((N,2),np.float32)
        # Frases cortas conservan consonante y vocal sin calcular un tubo mudo
        # durante cuatro minutos. Cada remate mantiene sus tiempos del score.
        groups={}
        for e in P['eventos']['boca-ritmica']:groups.setdefault(int(e['t']//5),[]).append(e)
        for k,es in groups.items():
            t0=k*5;notes=[{**e,'t':e['t']-t0} for e in es];s={'notas':notes,'vocales':[[e['t']-t0,e.get('vocal','u')] for e in es],'consonantes':[[e['t']-t0,e.get('consonante','k'),.6] for e in es]};z,_,_=TT.render('boca',s,6.,sr=SR,semilla=22+k);poner(y,z,t0)
        store('boca-ritmica',y);del y;gc.collect()
    # Señales libres. Los gestos del motor son cortos y decrecientes, no beat.
    if not (R/'estatica-senal.f32').exists():
        y=np.zeros((N,2),np.float32);rng=np.random.default_rng(22)
        for j,e in enumerate(P['eventos']['estatica-senal']):
            g=e['gesto'];n=round(e['dur']*SR);t=np.arange(n)/SR
            if 'arranque' in g or 'motor prende' in g:z=motor_fallido(e['dur'],SR,e['vel'])*(1 if 'fallido' in g else .65)
            elif 'pitido' in g:
                z=np.sin(2*np.pi*hz(e['midi'])*t)*env(n,.008,.035)*e['vel']*.22
                if 'doble' in g:z*=((t<.065)|((t>.155)&(t<.24)))
            elif 'dedo' in g:z=auxiliar('barro',.55)[:n]
            else:
                z=sosfilt(butter(2,[550,3900],btype='bandpass',fs=SR,output='sos'),rng.normal(0,1,n))*e['vel']*.085*env(n,.04,.09)
            poner(y,z,e['t'],p=(-.55 if j%2 else .55))
        store('estatica-senal',y);del y;gc.collect()
    jsave(out/'instrumentos-interpretados.json',receipts)
    print('Instrumentos propios interpretados',flush=True)

if __name__=='__main__':main()
