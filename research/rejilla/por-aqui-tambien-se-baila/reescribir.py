"""Nueva entrega exclusiva: escritura r4, sin producir audio, visor ni video.
Reutiliza fichas/terreno y patrones cumbieros de r3. Recompone las frases,
los relevos, el solo, las percusiones y el silencio. Conserva r3 intacta.
"""
from comun import *
from laminas import *
from instrumentos_revision import transbordos,impactos_bolsa,comprobaciones
import partitura as anterior
from scipy.ndimage import map_coordinates
import shutil

ORIGEN=BASE/'por-aqui-partitura-s22-322db0e27565'
REV='laberinto-partitura-0.4'
PAUSA=(180.,200.)

def viaje(S,T,H,TR):
    paths=np.unique(np.asarray(S['caminos']),axis=0);U=np.array(S['u']);V=np.array(S['v'])
    # Cada tramo usa un camino que de verdad apareció en el modelo anterior.
    # Los transbordos entre ellos son conexiones compuestas, no carreteras medidas.
    way=[(0,23,0),(20,18,0),(50,8,3),(70,14,7),(100,4,7),(130,0,3),(160,6,0),(180,2,0),(200,2,0),(220,10,7),(240,23,0)]
    dt=.02;ts=np.arange(0,240+dt/2,dt);uv=[];vveh=np.asarray(TR['v'])[:,0];vtime=np.arange(len(vveh))*TR['paso_guardado']
    for t in ts:
        k=min(len(way)-2,max(0,np.searchsorted([w[0] for w in way],t,side='right')-1))
        ta,ia,pa=way[k];tb,ib,pb=way[k+1]
        # Integración de velocidad en cada tramo espacial, nunca cada dos compases.
        tt=np.arange(ta,tb+.01,.02);vv=np.interp(tt,vtime,vveh);vv=np.where(vv<.8,0,vv)
        ph=np.r_[0,np.cumsum((vv[:-1]+vv[1:])*.01)]
        a=float(np.interp(t,tt,ph)/max(ph[-1],1e-10))
        # Una polilínea atraviesa los nodos reales, incluidos sus recodos.
        inds=list(range(ia,ib+(1 if ib>=ia else -1),1 if ib>=ia else -1)) if ia!=ib else [ia]
        points=np.array([[U[i,paths[pa if q<len(inds)/2 else pb,i]],V[i,paths[pa if q<len(inds)/2 else pb,i]]] for q,i in enumerate(inds)])
        if len(points)==1:p=points[0]
        else:
            lengths=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))];lengths/=lengths[-1]
            p=np.array([np.interp(a,lengths,points[:,j]) for j in range(2)])
        uv.append(p)
    uv=np.asarray(uv);z=map_coordinates(H,[uv[:,1]*(T['G']-1),uv[:,0]*(T['G']-1)],order=1,mode='nearest')*T['relieve']+T['base']
    ds=np.linalg.norm(np.diff(uv,axis=0),axis=1)*T['anchoKm']*1000;dz=np.diff(z)
    grade=np.r_[0,np.divide(dz,ds,out=np.zeros_like(dz),where=ds>1e-8)];grade=np.clip(grade,-.6,.6)
    speed=np.interp(ts,vtime,vveh);speed[(ts>=180)&(ts<200)]=0
    # Humedad como personaje/material compuesto: no meteorología observada.
    lluvia=np.clip((ts-92)/38,0,1)*np.clip((225-ts)/25,0,1)
    return {'t':ts.tolist(),'u':uv[:,0].tolist(),'v':uv[:,1].tolist(),'altura_m':z.tolist(),
            'pendiente':grade.tolist(),'velocidad_control':speed.tolist(),'lluvia_compuesta':lluvia.tolist(),
            'distancia_m':float(ds.sum()),'ascenso_m':float(dz[dz>0].sum()),'descenso_m':float(-dz[dz<0].sum()),
            'origen_m':float(z[0]),'cota_mayor_m':float(z.max()),'final_m':float(z[-1]),'waypoints':way,
            'distincion':'alturas muestreadas de Traspuesta; escala temporal y conexiones de transporte compuestas; clima inventado'}

def generar(R,TR):
    # Recuperar únicamente las funciones instrumentales cumbieras, no vender
    # su número como prueba de complejidad. El resto se escribe abajo.
    old=leer(ORIGEN/'partitura-r3.json');P={k:v for k,v in old.items() if k not in ['eventos','letra','radio','traza_trafico','ruteo','solo_D','ciclos','armonia']}
    names=[x if x!='vibrafono' else 'bolsa-juguetes' for x in anterior.NOMBRES]
    ev={c:[] for c in names};trace=[];letra=[];radio=[];ciclos=[]
    keep=['bajo-cumbia','guiro','conga','campana','timbal','bombo','caja']
    for c in keep:
        for e in old['eventos'][c]:
            if e['t']<180 or e['t']>=200:ev[c].append(dict(e,procedencia='patrón cumbiero r3; nueva articulación por pendiente'))
    def at(key,t):return float(np.interp(t,R['t'],R[key]))
    def add(c,t,m,d,v=.5,**kw):
        if not 0<=t<240:return
        if 180<=t<200 and not kw.get('libre',False):return
        end=min(t+d,240.)
        if t<180<end:end=179.96
        if end<=t:return
        e={'t':round(float(t),6),'pulso':round(float(t/Q),6),'dur':round(float(end-t),6),'dur_pulsos':round(float((end-t)/Q),6),'midi':float(m),'vel':float(v),**kw}
        ev[c].append(e);return e
    # Un campo armónico con memoria: la lluvia introduce 7/4; después de
    # la avería queda 11/8. No reiniciar la progresión Dm9 cada ocho compases.
    campos=[(0,50,'D/A abierto',[1,1.5,2]),(50,100,'tercera 6/5 y quinta',[1,1.2,1.5]),(100,180,'séptima 7/4; metal húmedo',[1,1.2,1.5,1.75]),(200,240,'residuo 11/8',[1,1.2,1.375,1.75])]
    harm=[]
    for a,b,n,rat in campos:
        harm.append({'t':a,'t1':b,'campo':n,'razones_sobre_D2':rat})
        for j,r in enumerate(rat):
            m=38+12*np.log2(r);add('organo-drone',a,m,b-a,.17 if j else .24,funcion='campo sostenido sin ataques internos',razon=r)
        for t in np.arange(max(a,8),b,10):
            for q,j in enumerate([0,2,0,1]):add('guembri-drone',t+q*1.7,38+12*np.log2(rat[min(j,len(rat)-1)]),.6,.27,frase='ostinato de cuatro; la avería lo corta')
    # Cabeza: salto, nota insistida, hueco y contestación desplazada.
    # Sus intervalos y huecos pertenecen a todos los temas/solos posteriores.
    cells=[[(0,62,.5),(.75,69,.5),(1.5,68,.25),(2.5,68,.5),(3.25,65,.5)],
           [(.5,64,.5),(1.25,62,.75),(3,60,.6)],
           [(0,62,.5),(1,69,.75),(2.5,68,.25),(3.25,65,.5)],
           [(.5,64,.5),(2,63,.5),(3.25,62,.5)],
           [(0,62,.25),(.75,69,.75),(2,68,.5),(3.25,65,.5)],
           [(.5,64,.5),(1.5,62,.5),(3,60,.6)],
           [(0,60,.5),(1.5,64,.5),(2.75,63,.5)],
           [(.75,62,.5),(2.25,61,.5),(3.5,62,.4)]]
    P['tema_A']=cells
    # Tres relojes integrados de tráfico; se mantienen a lo largo del viaje.
    # El desplazamiento acotado facilita dirección sin borrar su pasado.
    VV=np.array(TR['v']);ts=np.arange(len(VV))*TR['paso_guardado'];phases={}
    for driver in [0,11,22]:
        rate=np.where(VV[:,driver]<.8,0,VV[:,driver]);ph=np.r_[0,np.cumsum((rate[:-1]+rate[1:])*.5*np.diff(ts))]
        phases[driver]=ph
    def local(c,t,m,d,v,driver=0,**kw):
        speed=float(np.interp(t,ts,VV[:,driver]));ph=float(np.interp(t,ts,phases[driver]));lag=.28*np.sin(ph/7+driver*.1)
        if speed<.8:
            trace.append({'capa':c,'t_nominal':t,'suprimido':True,'vehiculo':driver,'v':speed});return
        effort=max(0,at('pendiente',t));wet=at('lluvia_compuesta',t)
        eff=t+lag;dur=d/(1+2*effort)
        e=add(c,eff,m,dur,v*(1-.18*wet),vehiculo=driver,frase=kw.pop('frase','tema'),retardo_s=lag,pendiente=at('pendiente',t),humedad_compuesta=wet,**kw)
        if e:trace.append({'capa':c,'t_nominal':t,'t_efectivo':e['t'],'suprimido':False,'vehiculo':driver,'v':speed,'fase_acumulada':ph})
    for start in [4,12,20,28,36,44,68,80,88]:
        for k,ns in enumerate(cells):
            for j,(a,m,d) in enumerate(ns):
                t=(start+k)*BAR+a*Q
                if 180<=t<200:continue
                c='acordeon-tema' if start<28 or start>=68 else ('laser-directo' if j%2 else 'acordeon-tema')
                if start>=88:c='clarinete'
                # Después: la tercera de la respuesta no vuelve al temperamento.
                cents=0 if t<100 else -31.174 if m%12==0 else 0
                if t>=200 and j==len(ns)-1:m+=12*np.log2(11/8)-5
                local(c,t,m+cents/100,d*Q,.61,driver=[0,11,22][k%3],frase='tema-A' if t<170 else 'tema-con-memoria',cabeza=(k,j))
                if k%2 and start<88:local('acordeon-respuesta',t+.23,m-12,d*.38,.29,driver=22,frase='contestación incompleta')
    # Las respuestas son huecos del tema, no la misma escala otra vez.
    for b in [2,10,18,30,34,42,46,70,82,90]:
        for j,(a,m) in enumerate([(0,57),(1.75,63),(4.25,62)]):
            local('clarinete',b*BAR+a*Q,m,.8 if j<2 else 1.1,.34,driver=11,frase='contesta el hueco; deja sin resolver el semitono')
        add('chelo',b*BAR+.6,50 if b<40 else 50+12*np.log2(11/8),3.8,.26,articulacion='arco; presión según subida',pendiente=at('pendiente',b*BAR))
    # Solkattu como articulación propia. Tres estratos se relevan: aprendizaje
    # audible -> contrapunto 3/5 -> deuda tras el silencio -> remate compartido.
    for b in range(8,88,2):
        t0=b*BAR
        if 180<=t0<200:continue
        sub=3 if 28<=b<40 else 5 if 52<=b<68 else 4
        ending=b in [18,26,38,50,66,86];Rr=anterior.mora(sub)
        ticks=Rr['golpes'] if ending else [0,sub,sub+sub-1,3*sub+1,4*sub,6*sub-1,7*sub+sub-1]
        # Tras la avería, la primera célula omite su primer ataque: deuda real.
        if b==80:ticks=ticks[1:]
        for k,tick in enumerate(ticks):
            t=t0+tick/sub*Q;c=['membrana-din','membrana-ta','membrana-thom'][k%3]
            load=.5+1.8*at('lluvia_compuesta',t);grade=at('pendiente',t)
            d=.44 if c.endswith('din') else .16
            add(c,t,50 if k%3<2 else 38,d,.43+.13*(grade>0),sub=sub,carga_central=load,solkattu=['din','ta','thom'][k%3],remate=ending,frase='deuda-del-primer-ataque' if b==80 else 'ciclo-con-respuesta')
            if k%2:add('barro',t+.07,67,.12,.26,frase='respuesta a borde de membrana')
            if k%3==0:add('pandero',t+.11,60,.12,.2,frase='desgrana sin doblar todo el ciclo')
            if ending and k%2==0:add('boca-ritmica',t,50,.16,.36,vocal='u' if k%4==0 else 'a',consonante='k' if k%4==0 else 't',sub=sub)
        if ending:add('membrana-din',(b+2)*BAR,50,.5,.74,llegada=True)
        ciclos.append({'compas':b+1,'sub':sub,'mora':ending,'golpes_unidades':ticks,'carga_central':load})
    # Memoria contrapuntística: los impactos de la bolsa enseñan tres ataques
    # (3+2+3 unidades); Reich aquí añade huecos hasta completar la célula.
    for b in range(16,72,2):
        n=min(3,1+(b-16)//16)
        for q in [0,3,5][:n]:add('mbira-boca',b*BAR+q*Q/2,62+[0,7,6][[0,3,5].index(q)],.28,.3,frase='aprende los juguetes por sustitución de silencios')
    # Commutador ortogonal: el mismo motivo atraviesa A, B, A^-1, B^-1.
    # El sitio vuelve al origen, la distribución de tres voces no.
    a=.73;b=1.07;Ws=transbordos(a,b);solo=[]
    for k,bar in enumerate(range(52,68,2)):
        state=0 if k<2 else min(4,k-1);w=Ws[state]@np.array([1.,0,0]);t0=bar*BAR
        for j,(beat,m,d) in enumerate([(0,62,.5),(.75,69,.5),(1.5,68,.25),(2.5,68,.5),(3.25,65,.5),(4.5,64,.5),(5.25,63,.5),(7,62,.6)]):
            for ci,c in enumerate(['laser-directo','laser-laberinto','laser-talbot']):
                if abs(w[ci])<.025:continue
                local(c,t0+beat*Q,m,d*Q,.67*abs(w[ci]),driver=ci*11,frase='solo-D',fase_signo=int(np.sign(w[ci])),matriz_estado=state,tau='0' if ci==0 else '1/3' if ci==1 else '2/5',grano_id=j)
        add('raspador',t0+.5,62,3.5,.4,estado_deposito=min(19,int(t0/12)),direccion='contra el descenso' if at('pendiente',t0)>0 else 'a favor del descenso',frase='pendiente cambia velocidad de lectura, no sólo altura')
        solo.append({'compas':bar+1,'t':t0,'estado':state,'pesos_con_signo':w.tolist(),'operacion':['identidad','A','BA','A^-1 BA','B^-1 A^-1 BA'][state]})
    # Juguetes: accidentes calculados a partir de aceleraciones, no adornos al azar.
    t=np.asarray(R['t']);sp=np.asarray(R['velocidad_control']);aceleracion=np.gradient(sp,t)
    # Baches = curvatura del perfil a lo largo del recorrido; escala artística.
    z=np.asarray(R['altura_m']);road=np.gradient(np.gradient(z,t),t);drive=np.clip(2*aceleracion+.3*road,-16,16)
    drive[(t>=179.9)&(t<200)]=0
    impacts=impactos_bolsa(t,drive)
    assert len(impacts)>10,'la bolsa debe producir contactos, no sólo metadatos'
    for hit in impacts:
        tt=hit['t']
        if 8<tt<179.9 or 200<=tt<235:
            add('bolsa-juguetes',tt,[62,81,74][hit['objeto']],.28,.12+.18*min(1,hit['fuerza']),objeto=['trompo de lámina','cascabel','silbato de barro'][hit['objeto']],fuerza_impacto=hit['fuerza'],frase='consecuencia de bache o frenada')
    # Gesto humano escrito, distinto de los accidentes del modelo: al acomodar
    # la bolsa toca tres objetos. Primero se oye la fuente; después la mbira
    # aprende sus intervalos 3:2, aumentados al doble (0, .9375, 1.5625 s).
    for t0 in [8.4,28.4]:
        for j,off in enumerate([0,.46875,.78125]):
            add('bolsa-juguetes',t0+off,[62,81,74][j],.22,.37,objeto=['trompo de lámina','cascabel','silbato de barro'][j],
                fuerza_impacto=.55,frase='pasajera acomoda la bolsa: gesto escrito, no contacto calculado',fuente_ritmica='3+2+3 en ocho unidades; mbira aprende con aumentación x2')
    # Nueva letra: objetos reconocibles y consecuencias, sin bolsa metafísica.
    lines=[(8,'Sube una señora con juguetes en la bolsa','su be u na se ño ra con ju gue tes en la bol sa','verso'),
           (12,'En cada bache el trompo pega contra el cascabel','en ca da ba che el trom po pe ga con tra el cas ca bel','verso'),
           (16,'El pájaro de barro tiene un ala rota','el pá ja ro de ba rro tie ne un a la ro ta','verso'),
           (20,'Por aquí también se baila','por a quí tam bién se bai la','coro'),
           (24,'La subida nos devuelve el mismo golpe','la su bi da nos de vuel ve el mis mo gol pe','respuesta'),
           (40,'Empezó a llover del lado de su asiento','em pe zó a llo ver del la do de su a sien to','verso'),
           (44,'La radio pierde nombres pero guarda las vocales','la ra dio pier de nom bres pe ro guar da las vo ca les','verso'),
           (68,'Ya aprendió la caja el golpe de la bolsa','ya a pren dió la ca ja el gol pe de la bol sa','verso'),
           (70,'No le metas mano que se está calentando','no le me tas ma no que se es tá ca len tan do','respuesta'),
           (80,'Por aquí también se baila','por a quí tam bién se bai la','coro'),
           (84,'Ahora falta el golpe que esperábamos primero','a ho ra fal ta el gol pe que es pe rá ba mos pri me ro','respuesta'),
           (88,'La señora baja el pájaro se queda','la se ño ra ba ja el pá ja ro se que da','coda'),
           (92,'No es un pájaro es la radio que lo aprendió','no es un pá ja ro es la ra dio que lo a pren dió','coda')]
    for bar,tx,sy,kind in lines:
        pos=.5;syll=sy.split();ls=[]
        for j,s in enumerate(syll):
            d=[.5,.25,.5,.75][j%4] if kind=='verso' else [.5,.5,.75,.5,.75][j%5]
            m=[62,62,69,68,65,64,63,62][j%8];c='voz-respuesta' if kind=='respuesta' else 'voz-verso'
            e=add(c,(bar*4+pos)*Q,m,max(.1,d*.83*Q),.65,texto=s,frase=kind)
            if e:ls.append(e)
            pos+=d
        letra.append({'compas':bar+1,'t':bar*BAR,'texto':tx,'silabas':syll,'funcion':kind,'fin_s':(bar*4+pos)*Q})
    cues=[(0,'chofer','Ruta veintidós. Subimos por el abanico. Agárrense.'),(7,'pasajera','Son juguetes. No los vaya a pisar.'),
          (103,'chofer','Cierren esa ventana. Se está mojando la bocina.'),
          (180.8,'chofer','Espérenme tantito. Se calentó. No le den todavía.'),
          (187.3,'pasajera','Antes hacía tres golpes. Ya no hace el primero.'),
          (198.3,'chofer','Ahora sí. Despacito.'),
          (231,'pasajera','El de barro no era mío. Venía sonando desde antes.')]
    for t,who,tx in cues:
        dur=min(len(tx.split())*.34,5.8)
        if t<180:dur=min(dur,179.9-t)
        if 180<=t<200:dur=min(dur,199.7-t)
        add('radio-'+who,t,50 if who=='chofer' else 57,dur,.66,texto=tx,modo='hablado',libre=180<=t<200)
        add('estatica-senal',t,60,dur+.1,.15,gesto='radio sin portadora periódica',libre=180<=t<200)
        radio.append({'t':t,'voz':who,'texto':tx,'dur_estim_s':dur})
    # Avería escrita en tiempo libre: sin batería, drones pulsados ni crescendo.
    libres=[(182.17,'pitido distante',78,.19),(184.63,'primer arranque fallido',35,1.13),
            (189.41,'pitido doble sin repetición',75,.27),(192.87,'segundo arranque fallido',35,.74),
            (196.23,'golpe de dedo aislado sin completar la célula',62,.13),(197.61,'motor prende sin fijar pulso',35,1.46)]
    for t,g,m,d in libres:add('estatica-senal',t,m,d,.35,gesto=g,libre=True)
    # La rueda defectuosa de la letra tiene antecedente y deja un residuo:
    # silbato aislado -> clarinete lo recoge en coda sin regreso del solista.
    add('bolsa-juguetes',177.37,74,.4,.35,objeto='silbato de barro',frase='última caída antes de la avería')
    add('clarinete',224.17,74,.55,.4,frase='recuerdo del juguete; la pasajera ya bajó')
    # Articulación real del terreno y del clima aplicada a eventos existentes.
    for c in keep:
        for e in ev[c]:
            g=at('pendiente',e['t']);wet=at('lluvia_compuesta',e['t'])
            e['pendiente']=g;e['humedad_compuesta']=wet
            e['vel']*=1+.12*np.tanh(6*g)
            e['dur']*=1-.3*max(0,np.tanh(6*g));e['dur_pulsos']=e['dur']/Q
            e['corte_agudos_hz']=float(9000-5200*wet)
            if e['t']<180<e['t']+e['dur']:e['dur']=179.96-e['t'];e['dur_pulsos']=e['dur']/Q
    for es in ev.values():es.sort(key=lambda e:e['t'])
    assert len(ev)==30 and all(ev.values())
    secciones=[('I','Terminal: oír la bolsa',0,8),('II','Los juguetes enseñan una frase',8,20),('III','Estribillo y subida',20,28),('IV','Descenso corto; tres relojes',28,40),('V','Subir mojados; se cargan las membranas',40,52),('VI','Solo D: volver cambia quién habla',52,68),('VII','Calentamiento; frase cortada',68,72),('VIII','Avería: sin compás audible',72,80),('IX','Arranque con un ataque perdido',80,88),('X','Baja la pasajera; queda su frase',88,96)]
    P.update(version=REV,subtitulo='La bolsa tiene juguetes; el viaje tiene memoria',eventos=ev,letra=letra,radio=radio,traza_trafico=trace,armonia=harm,ciclos=ciclos,ruteo=[],solo_D=solo,
       secciones=[{'id':i,'nombre':n,'compas_inicio':a+1,'compas_fin':b,'t':a*BAR,'t1':b*BAR} for i,n,a,b in secciones],
       break_libre={'t':180,'t1':200,'porcentaje_de_inicio':180/246*100,'causa':'avería por calentamiento en la última subida; decisión dramática, no predicción del tráfico',
                    'eventos':libres,'interpretacion':'detener compás; referencias de segundos, no contar ocho compases en escena; no clicks audibles',
                    'corte':{'t':179.96,'fade_ms':35,'accion':'cerrar buses métricos y vaciar retardos de láser/Talbot/reverb; sólo radio y señales libres nuevas'},
                    'regreso':'200 s: vuelve el bajo; percusión omite primer ataque. Sin redoble, riser ni rampa de tempo.'},
       holonomia={'A_angulo':a,'B_angulo':b,'matrices':[x.tolist() for x in Ws],'verificacion':comprobaciones(),
                  'grafo_cerrado_nodos_radiales':[[2,3],[2,5],[4,5],[4,3],[2,3]],
                  'distincion':'el láser cierra este circuito local mientras el autobús sigue su recorrido; no confundir los dos caminos',
                  'dominio':'controlador artístico real de tres amplitudes con signo; no campo físico medido'},
       terreno_viaje={k:v for k,v in R.items() if k not in ['t','u','v','altura_m','pendiente','velocidad_control','lluvia_compuesta']},
       agentes={'bolsa':'trompo de lámina, cascabel y silbato de barro con un ala rota; la radio conserva su llamada en la coda',
                'clima':'lluvia que entra por una ventana, moja radio y carga membranas; no se obliga a que el clima sea un pasajero',
                'instrumentos_nuevos_r4':['bolsa de impactos: tres osciladores contra topes y cuerpos modales','motor que falla: encendido decreciente','controlador de transbordos no conmutativos; no se cuenta como timbre']},
       eleccion_solo={'A':'virtuosismo de requinto: fuera del encargo','B':'pius ornamentales: no producen consecuencia','C':'Talbot añadido como efecto: insuficiente','D':'el motivo cruza dos operadores no conmutativos; retorna al sitio con otra distribución de voces y fase con signo'},
       limites=['complejidad estructural escrita y comprobada; interés, belleza e inteligibilidad quedan pendientes de audición tras aprobar la partitura',
               'la avería se compone; el modelo de tráfico no predice fallas mecánicas','percusiones inspiradas en recursos carnáticos; no reproducción tradicional certificada',
               'ruta artística muestreada en terreno real del generador, no levantamiento de una carretera','firma de fase requiere aplicar signo antes de la red; el futuro render deberá respetarlo'],
       duracion_prevista=246,estado='R4 PARA REVISIÓN; detener antes del audio completo; visor después')
    return P,impacts

def main():
    S=leer(ORIGEN/'depositos-r2.json');T=leer(ORIGEN/'datos/terreno-22.json');TR=leer(ORIGEN/'trafico.json');H=np.fromfile(ORIGEN/'datos/h-22.f32',np.float32).reshape(T['G'],T['G'])
    R=viaje(S,T,H,TR)
    f,ax=figura('El recorrido sube, retrocede y vuelve a subir','Primera decisión de r4: medir el viaje antes de repartir sus consecuencias')
    ax[0].plot(R['t'],R['altura_m'],color='#732605');ax[0].axvspan(180,200,color='#1d2869',alpha=.12);ax[0].set_xlabel('segundos de partitura');ax[0].set_ylabel('cota de Traspuesta, m');b=png(f)
    nonce=os.urandom(24).hex();full=hashlib.sha256(b+REV.encode()+nonce.encode()+Path(__file__).read_bytes()).hexdigest();tag=full[:12]
    out=BASE/f'por-aqui-revision-s22-{tag}';out.mkdir(exist_ok=False);(out/'proceso').mkdir();shutil.copytree(ORIGEN/'datos',out/'datos')
    guardar(out/'proceso'/f'01-subidas-y-descensos-s22-{tag}.png',b)
    for name in ['depositos-r2.json','trafico.json']:guardar(out/name,(ORIGEN/name).read_bytes())
    guardar(out/'reescribir-fuente.py',Path(__file__).read_bytes())
    jsave(out/'ejecucion.json',{'hash':full,'nonce':nonce,'semilla':22,'version':REV,'imagen_inicial_sha256':hashlib.sha256(b).hexdigest(),'fecha_contexto':'2026-10-22','anterior':ORIGEN.name,'anterior_partitura_sha256':sha(ORIGEN/'partitura-r3.json')})
    jsave(out/'viaje.json',R);P,impacts=generar(R,TR);jsave(out/'partitura-r4.json',P);jsave(out/'impactos-bolsa.json',impacts)
    guardar(out/'PARTITURA.txt',b'partitura-r4.json');guardar(out/'DEPOSITOS.txt',b'depositos-r2.json');(BASE/'ULTIMA.txt').write_text(out.name,encoding='utf8')
    f,ax=figura('Treinta partes; veinte segundos sin pulso','r4: el vacío es parte de la forma; no es un filtro aplicado a la mezcla')
    for j,(c,es) in enumerate(P['eventos'].items()):
        for e in es:ax[0].plot([e['t'],e['t']+min(4,e['dur'])],[j,j],lw=1,color=['#1d2869','#732605','#638179'][j//10])
    ax[0].axvspan(180,200,color='#b99a69',alpha=.25);ax[0].set_yticks(range(30),list(P['eventos']),fontsize=6);ax[0].set_xlim(0,246);ax[0].set_xlabel('segundos; zona sombreada = avería, sin compás audible')
    salva(f,out/'proceso'/f'02-reorquestacion-y-vacio-s22-{tag}.png')
    f,ax=figura('Cerrar el camino no devuelve la misma voz','Solo D: A, B, inversa de A, inversa de B; tres amplitudes con signo')
    weights=np.array([np.array(w)@np.array([1.,0,0]) for w in P['holonomia']['matrices']]);ax[0].plot(range(5),weights,marker='o');ax[0].legend(['láser directo','red de cruces','Talbot'],loc='lower left');ax[0].set_xticks(range(5),['inicio','A','BA','A⁻¹BA','B⁻¹A⁻¹BA']);ax[0].set_ylim(-1.1,1.1);ax[0].set_ylabel('amplitud firmada antes de síntesis')
    salva(f,out/'proceso'/f'03-retorno-no-conmutativo-s22-{tag}.png')
    print(json.dumps({'carpeta':str(out),'eventos':sum(map(len,P['eventos'].values())),'viaje':P['terreno_viaje'],'holonomia':comprobaciones(),'impactos_modelo':len(impacts)},ensure_ascii=False))

if __name__=='__main__':main()
