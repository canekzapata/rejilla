"""Luciérnagas v10: composición por etapas, sin síntesis de audio."""
from pathlib import Path
import sys,json,copy,hashlib,secrets,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from modelos_memoria import contacto,encuentro,recibir,extraer_cuerda,plan_memoria,pares,complejo
from instrumentos import Guitarra,hz

ROOT=Path(__file__).resolve().parent;V8=ROOT/'luciernagas-reescritura-s1-29d4afe5aad2'
V9=ROOT/'luciernagas-relevos-s1-92168980d35d';Q=60/144;D=258.6666666666667;C0=93.33333333333334;C1=153.33333333333334
VERSION='luciernagas-partitura-10.0';N=0
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(out,name,x):
    with (out/name).open('x',encoding='utf8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=1)
def context(name):
    out=ROOT/(ROOT/'PARTITURA-EN-CURSO.txt').read_text().strip();return out,json.loads((out/name).read_text(encoding='utf8'))
def stage(out,p,n,title):
    tag=out.name.split('-')[-1];im=Image.new('RGB',(1700,1100),'#11201f');dr=ImageDraw.Draw(im)
    font=lambda s:ImageFont.truetype('C:/Windows/Fonts/arial.ttf',s)
    dr.text((35,22),title,font=font(35),fill='#ece4cf');dr.text((35,75),'Checkpoint real de escritura / terreno 1 / composición 2026102201 / sin audio nuevo',font=font(21),fill='#b4ccbf')
    x0,x1,top,row=350,1665,165,22
    for k,part in enumerate(p['partes']):
        y=top+k*row;dr.text((20,y-6),part['id'],font=font(16),fill='#d0d9c8')
        for e in p['eventos'][part['id']]:
            for a,b in e.get('salidas',[]):
                dr.line((x0+(x1-x0)*a/D,y,x0+(x1-x0)*b/D,y),fill='#edaa73' if e.get('revision')=='v10' else '#87bcad',width=3)
    for sec in p['secciones']:
        x=x0+(x1-x0)*sec['t']/D;dr.line((x,top-10,x,top+36*row),fill='#56716a');dr.text((x,top-35),sec['id'],font=font(17),fill='#e5d4ab')
    dr.text((35,1000),'Ventanas audibles escritas. El color identifica eventos nuevos, no volumen ni calidad musical.',font=font(22),fill='#c0d5c7')
    file=out/'proceso'/f'{n:02}-{title.lower().split(" / ")[0].replace(" ","-")}-s1-{tag}.png';assert not file.exists();im.save(file)
def init():
    image=(V9/'og.png').read_bytes();code=Path(__file__).read_bytes();nonce=secrets.token_hex(16)
    full=sha(image+code+VERSION.encode()+nonce.encode());out=ROOT/f'luciernagas-partitura-s1-{full[:12]}';out.mkdir(exist_ok=False)
    for d in ['proceso','datos','fuentes']:(out/d).mkdir()
    p=json.loads((V9/'partitura-v9.json').read_text(encoding='utf8'));dump(out,'lectura-v9.json',p);stage(out,p,1,'Lectura de la revisión anterior / ventanas del JSON v9')
    for file in ['recorrido.json','terreno-s1.json']:
        with (out/'datos'/file).open('xb') as f:f.write((V8/'datos'/file).read_bytes())
    for file in ['recomponer_v10.py','modelos_memoria.py','instrumentos.py']:
        with (out/'fuentes'/file).open('xb') as f:f.write((ROOT/file).read_bytes())
    dump(out,'inicio.json',{'version':VERSION,'hash_completo':full,'nonce':nonce,'semilla_terreno':1,'semilla_composicion':2026102201,
      'imagen_sha256':sha(image),'programa_sha256':sha(code),'fuente_v9_sha256':sha((V9/'partitura-v9.json').read_bytes()),
      'autorizacion':'Corregir partitura; 2:40 es referencia favorable y puede modificarse por instrucción de Canek.'})
    (ROOT/'PARTITURA-EN-CURSO.txt').write_text(out.name,encoding='utf8');print(out,flush=True)
def add(p,part,t,m,d,v=.5,phrase='',parent=None,**kw):
    global N
    N+=1;e={'id':f'v10-{N:05}','t':float(t),'dur':float(min(d,D-t)),'midi':float(m),'hz':float(hz(m)),
      'vel':float(v),'pan':next(x['pan'] for x in p['partes'] if x['id']==part),'frase':phrase,'ancestro':parent,
      'articulacion':kw.pop('articulacion','pua' if part=='guitarra' else 'ordinario'),
      'seccion':next(s['id'] for s in p['secciones'] if s['t']<=t<s['fin']+1e-8),'revision':'v10',**kw}
    e['salidas']=e.get('salidas',[[e['t'],e['t']+e['dur']]])
    if part=='guitarra':
        e.setdefault('cuerda',4);e.setdefault('caja',0);e.setdefault('nodo',.17);e.setdefault('parcial',1)
        e['parametros_motor']={k:e[k] for k in ['cuerda','caja','nodo','parcial']}
        e['parametros_motor'].update(midi=e['midi']-12*np.log2(e['parcial']),vel=e['vel'],gesto=e['articulacion'])
    p['eventos'][part].append(e);return e
def set_counter(p):
    global N
    N=max([int(e['id'].split('-')[-1]) for es in p['eventos'].values() for e in es if e['id'].startswith('v10-')]+[0])
def lyric(p,old,frase,part,t,scale=1):
    source=next(l for l in old['letra'] if l['frase']==frase);lookup={e['id']:e for es in old['eventos'].values() for e in es}
    ids=[]
    for id0 in source['ids']:
        z=lookup[id0];at=t+(z['t']-source['t'])*scale
        e=add(p,part,at,z['midi'],z['dur']*scale,z['vel'],frase+'-v10',texto=z['texto'],acento=z.get('acento',False),
              articulacion='canto; acento escrito' if z.get('acento') else 'canto ligado',respiracion_antes=z.get('respiracion_antes',False),
              silaba=z.get('silaba'),origen_texto=source['procedencia'],referencia_editorial=id0)
        ids.append(e['id'])
    p['letra'].append({**copy.deepcopy(source),'t':t,'fin':t+(source['fin']-source['t'])*scale,'capa':part,
       'frase':frase+'-v10','ids':ids,'escala':source.get('escala',1)*scale})
def exposure():
    out,_=context('lectura-v9.json');old=json.loads((V8/'partitura-v8.json').read_text(encoding='utf8'));p=copy.deepcopy(old)
    p['version']=VERSION;p['parada']='Partitura para revisión; no interpretar canción ni producir másters en esta sesión.'
    p['eventos']={k:[e for e in es if e['t']>=C0] for k,es in old['eventos'].items()}
    p['letra']=[x for x in old['letra'] if x['t']>=C0];p['desarrollo_v10']=[];p['genealogia_v10']=[]
    # El órgano prepara la memoria del umbral; sus eventos de exposición se conservan.
    p['eventos']['organo']=[copy.deepcopy(e) for e in old['eventos']['organo']]
    for t in [0,3.333333333,6.666666667,10.]:
        for j,(beat,m,d) in enumerate(p['tema_Q']):
            e=add(p,'guitarra',t+beat*Q,m,d*Q,.77 if j==0 else .55,'Q: cuatro vueltas de insistencia',caja=j%3)
            if j in [0,2]:add(p,'bajo',e['t'],m-24,min(.8,d*Q*1.8),.58,'raíz que recoge Q',e['id'])
        add(p,'bombo',t,36,.16,.7,'paso obstinado',pieza='kick');add(p,'caja',t+2*Q,38,.12,.67,'respuesta al paso',pieza='snare')
        for q in [1,3,5,7]:add(p,'hat',t+q*Q/2,42,.06,.3,'corcheas entre ataques',pieza='hat')
    # Cuatro episodios con contornos, respiraciones y respuestas diferentes.
    forms=[('A: el alambre pregunta',18.,[(0,64,.62),(1.4,59,.31),(2.3,60,.9),(4.7,65,.23),(5.6,64,1.25),(8.6,62,.52)],0),
      ('B: otra caja demora',22.7,[(0,59,.72),(2.1,60,.25),(2.9,64,.38),(4.2,65,.52),(6.3,64,.9)],1),
      ('C: la raíz cruza el riff',26.7,[(0,64,.38),(.9,67,.24),(1.8,65,.67),(3.8,60,.46),(5.5,59,.8)],2),
      ('D: cortar no acaba la frase',31.1,[(0,59,.23),(.6,60,.2),(1.3,64,.4),(2.5,65,.35),(4.3,64,.6)],0),
      ('E: el mosquito desplaza',38.2,[(0,64,.23),(.7,64,.19),(1.4,67,.43),(3.2,65,.7),(5.5,59,.32),(6.7,60,.56),(8.7,64,1.0)],1),
      ('F: respuesta por dentro',43.5,[(0,64,.8),(2.7,65,.28),(3.7,64,.3),(5.2,60,.54),(7.3,59,.95)],2),
      ('G: ahora falta el primer golpe',50.1,[(.9,59,.38),(2.2,60,.45),(3.8,65,.2),(4.6,64,.84)],0),
      ('H: el coro deja su hueco',59.4,[(0,64,.6),(1.8,59,.23),(2.7,60,.42),(4.8,65,.52),(6.5,64,1.05)],1),
      ('I: el pulso ya no alcanza',70.7,[(0,64,.4),(1.3,60,.38),(3.2,59,.74),(5.5,65,.35),(6.9,64,1.0)],2)]
    for ni,(name,start,cell,box) in enumerate(forms):
        roots=[]
        for j,(beat,m,d) in enumerate(cell):
            gesture='roce' if ni in [5,8] and j==len(cell)-1 else 'armonico' if ni==3 and j==3 else 'pua'
            partial=5 if gesture=='armonico' else 1
            e=add(p,'guitarra',start+beat*Q,m+12*np.log2(partial),d*(.78 if gesture=='roce' else 1),.67-.055*(j%3),name,
                  articulacion=gesture,caja=box,nodo=.2 if partial==5 else .12+.035*(j%4),parcial=partial)
            roots.append(e)
            # El bajo recoge puntos de llegada, no dobla cada nota.
            if j in [0,len(cell)-1]:add(p,'contrabajo',e['t']+.095,m-24,min(1.3,e['dur']+.34),.48,'llegada de '+name,e['id'])
            if j==len(cell)-1:
                for ii,(delay,offset) in enumerate([(.18,-5),(.51,-4),(1.02,0)]):
                    target='krar' if ni%2==0 else 'clarinete'
                    add(p,target,e['t']+e['dur']+delay,m+offset,.18 if ii<2 else .46,.42,'completa el hueco de '+name,e['id'])
            if j%3==0:add(p,'bombo',e['t'],36,.15,.61,'acento del alambre',e['id'],pieza='kick')
            elif j==len(cell)-1:add(p,'caja',e['t']+e['dur']+.06,38,.13,.58,'contesta la cesura',e['id'],pieza='snare')
            else:add(p,'aro',e['t']+.07,37,.065,.32,'borde entre notas',e['id'],pieza='rim')
        # Remate compuesto desde los tres últimos ataques: retrogradar intervalos, no redoblar por defecto.
        last=roots[-1];intervals=np.diff([e['t'] for e in roots[-3:]])[::-1];at=last['t']+last['dur']+.16
        for j,gap in enumerate(intervals):
            add(p,'tom',at,45,.13,.39+.1*j,'remate de '+name,last['id'],pieza='tomlo');at+=min(.48,gap*.42)
        p['desarrollo_v10'].append({'episodio':name,'inicio':start,'fin':last['t']+last['dur'],'caja':box,
          'ids':[e['id'] for e in roots],'funcion':'guitarra conduce; grave elige llegadas; krar/clarinete completa huecos; percusión hereda cesuras'})
    # Escenas completas: cuatro entradas del solista, interlocutor y coros con funciones distintas.
    for f,part,t,s in [('lata','voz',13.75,1),('tenis','duo',29.166666667,1),('mosco','voz',35.,1),
       ('cabezas','duo',42.083333333,1),('raiz','duo',46.45,1),('acuerdo','corocuerda',51.1,.85),
       ('coro-lago','voz',55.,1),('coro-noche','corocuerda',64.1,1),('coro-amor','voz',66.833333333,1),('coro-otras','duo',76.,.94)]:
        lyric(p,old,f,part,t,s)
    # La portadora aparece antes de que se articule: el vocoder no depende de reciclar el canto principal.
    for t,m,d in [(50.9,60,3.8),(63.8,64,4.4)]:add(p,'cuerda',t,m,d,.24,'portadora que aprende la respuesta')
    # Presencias con episodios y relojes que no se reinician en cada vuelta.
    for part,period,base in [('mbira',19*Q/4,76),('arpaboca',17*Q/4,52),('fotones',29*Q/4,88)]:
        for k in range(1,35):
            t=9.31+k*period
            if t>=88:break
            if any(a<t<b for a,b in [(18,28),(38,53),(70,76)]):
                e=add(p,part,t,base+[0,-5,-4,1,0][k%5],.11 if part=='fotones' else .26,.22,'reloj continuo: contesta sólo en episodios')
                e['fase_reloj']=t/period;e['periodo_s']=period
    for t,part,m in [(12.5,'berimbau',52),(25.7,'piano',59),(40.8,'chelo',52),(58.85,'arpa',76),(73.9,'pua',64),(79.4,'ride',51)]:
        add(p,part,t,m,.35,.3,'respuesta singular, no relleno')
    # El cierre introduce el fallo. La presión insuficiente deja carga para el siguiente intento.
    trigger=p['desarrollo_v10'][5]['ids'][-1]
    for t,v,gesture in [(80.1,.57,'pua'),(82.25,.39,'pua'),(85.3,.3,'roce'),(88.7,.21,'madera')]:
        add(p,'guitarra',t,64,1.05 if gesture=='roce' else .32,v,'IV: el ataque pierde cuerpo',trigger,articulacion=gesture,caja=1)
    # Afinación por encuentros; el orden está en la partitura completa.
    xs=np.zeros(3);meet=[]
    for t,i,j,target in [(22.,0,1,0),(56.4,1,2,0),(87.9,2,0,85),(109.8,0,1,0),(124.6,1,2,0),(139.4,2,0,85)]:
        before=xs.copy();xs=encuentro(xs,i,j,target);meet.append({'t':t,'i':i,'j':j,'promesa_cents':target,'antes':before.tolist(),'despues':xs.tolist()})
    p['encuentros_v10']=meet
    for e in p['eventos']['guitarra']:
        states=[a for a in meet if a['t']<=e['t']];cents=states[-1]['despues'] if states else [0,0,0]
        e['afinaciones_cajas_cents']=cents
        if e.get('revision')=='v10':
            e['midi']+=cents[e['caja']]/100;e['hz']=float(hz(e['midi']))
    p['controles']['guitarra']['encuentros']='encuentros_v10';p['controles']['guitarra']['pelicula']=[[0,.05],[29.1,.65],[D,.65]]
    p['controles']['guitarra']['ganancia_exposicion']='instrumento principal; la voz no cubre automáticamente su frase'
    # Una acción del objeto, además de la palabra lata.
    add(p,'piano',29.1,76,.17,.31,'la lata moja el contacto',altura_asignable=False,accion_material={'pelicula_antes':.05,'pelicula_despues':.65})
    p['lectura_roles_v10']={'voz':'cuatro frases antes del centro; interlocutor y coros no duplican su línea',
       'guitarra':'nueve episodios; tres cajas cambian función y los otros instrumentos responden a sus finales',
       'percusion':'acento, cesura, borde y remate derivados de eventos concretos de guitarra; no una base intacta bajo el solo'}
    for es in p['eventos'].values():es.sort(key=lambda e:e['t'])
    dump(out,'borrador-exposicion-v10.json',p);stage(out,p,2,'Exposición recompuesta / frases y acompañamiento');print('exposición escrita',len(p['desarrollo_v10']),'episodios',flush=True)

def integral(m0,m1,d):
    k=math.log(2)*(m1-m0)/12;return float(hz(m0))*d*(math.expm1(k)/k if abs(k)>1e-12 else 1)
def guitar_capture(p,until):
    # Motor de envolventes fijado, control dt=.005; estado completo, sin audio.
    g=Guitarra();events=sorted([e for e in p['eventos']['guitarra'] if e['t']<=until],key=lambda e:e['t']);n=0;t=0.;dt=.005
    rows=json.loads((V8/'datos/recorrido.json').read_text(encoding='utf8'))['muestras'];rt=np.array([r['t'] for r in rows]);slope=np.array([r['pendiente'] for r in rows])
    axis=np.array([.7,.3,1.]);length=np.linalg.norm(axis);u=axis/length;K=np.array([[0,-u[2],u[1]],[u[2],0,-u[0]],[-u[1],u[0],0]])
    trace=[]
    while t<until-1e-10:
        while n<len(events) and events[n]['t']<=t+1e-9:
            e=events[n];n+=1
            if e['articulacion']!='contacto':g.gesto(**e['parametros_motor'])
        step=min(dt,until-t);mid=t+step/2
        active=[e for e in events if e.get('contacto') and e['t']<=mid<e['t']+e['dur']]
        for e in active:
            a=np.array(e['contacto']['traza_t_presion_carga_exc_ruido']);drive=np.interp(mid-e['t'],a[:,0],a[:,3])
            h=np.arange(1,9);g.z[e['cuerda'],e['caja']]+=drive*step*np.sin(np.pi*h*e['nodo'])/h**1.2*np.exp(1j*h*(.37+(mid-e['t'])*.8))
        xs=np.zeros(3)
        for m in p['encuentros_v10']:
            if m['t']<=mid:xs=np.asarray(m['despues'])
        wet=.05 if mid<29.1 else .65;pressure=float(np.clip(.3+6*abs(np.interp(mid,rt,slope)),0,1));h=np.arange(1,9)
        f=hz(g.midi)[:,None,None]*2**(xs[None,:,None]/1200)*h
        g.phase=(g.phase+2*np.pi*f*step)%(2*np.pi);g.z*=np.exp(-step*(.4+.13*h+1.2*wet))
        angle=(.1+pressure)*step*length;R=np.eye(3)+math.sin(angle)*K+(1-math.cos(angle))*(K@K)
        g.z=np.einsum('ab,sbh->sah',R,g.z);t+=step
        if len(trace)<int(t*5):trace.append([t,float(np.sum(abs(g.z)**2))])
    z=g.z[4,1,[0,1,2,4]]*np.exp(1j*g.phase[4,1,[0,1,2,4]])
    return z,{'dt_s':dt,'hasta_s':until,'z_completo':pares(g.z.ravel()),'phase':g.phase.tolist(),'captacion':'cuerda 4, caja 1, modos 1/2/3/5; fase incluida','traza_norma':trace}
def center():
    out,p=context('borrador-exposicion-v10.json');set_counter(p)
    for part in p['eventos']:p['eventos'][part]=[e for e in p['eventos'][part] if not (C0<=e['t']<C1)]
    p['oscuridades']=[[99.5,100.05],[113.97,114.28],[142.15,142.55]]
    p['cortes_buses']=[c for c in p['cortes_buses'] if not(C0<c['t']<C1)]
    for a,b in p['oscuridades']:p['cortes_buses'].append({'t':a,'fin':b,'rampa_s':.012,'destino':'todos los buses','accion':'cerrar salida; continuar estado'})
    charge=0.;contact_events=[]
    for start,peak,dur,box in [(93.65,.30,1.9,0),(97.05,.43,1.8,1),(100.633333333,.91,3.1,1)]:
        curve=[[0,0],[.3,peak],[dur-.25,peak],[dur,0]]
        if contact_events:charge*=math.exp(-.72*(start-(contact_events[-1]['t']+contact_events[-1]['dur'])))
        model=contacto(curve,pelicula=.65,carga=charge);charge=model['carga_final']
        e=add(p,'guitarra',start,64,dur,.22,'contacto: un intento deja carga',contact_events[-1]['id'] if contact_events else p['desarrollo_v10'][-1]['ids'][-1],
              articulacion='contacto',caja=box,cuerda=4,nodo=.17,altura_asignable=False,contacto=model,libre=True,carga_antes=model['traza_t_presion_carga_exc_ruido'][0][2])
        contact_events.append(e)
    for t,gesture,v in [(95.88,'madera',.18),(96.35,'roce',.12),(104.15,'armonico',.17)]:
        add(p,'guitarra',t,64+(12*np.log2(5) if gesture=='armonico' else 0),.72 if gesture=='armonico' else .27,v,'escuchar la resistencia',contact_events[-1]['id'],
            articulacion=gesture,parcial=5 if gesture=='armonico' else 1,nodo=.2 if gesture=='armonico' else .17,caja=1,libre=True,altura_asignable=gesture=='armonico')
    z,trace=guitar_capture(p,105.4);zc=recibir(z,.8,[.07,.12,.19,.37]);norm0=float(np.sum(abs(z)**2));norm1=float(np.sum(abs(zc)**2));tau=.42+1.1*(1-norm1/norm0)
    ec=add(p,'cuerda',106.2,64,10.,.27,'recibir el estado completo de la guitarra',contact_events[-1]['id'],
        inyeccion_modal={'z':pares(zc),'modos':[1,2,3,5],'fuente':pares(z),'captacion_t':105.4,'espera_s':.8},libre=True,
        salidas=[[106.2,110.8],[111.3,113.92],[114.32,116.2]])
    pressure=[[0,.1],[106.2,.19],[107.9,.73],[111,.24],[113.7,.57],[116.2,.31],[C1,.31],[206.666666667,.65],[246.666666667,0]]
    bow=[[0,0],[106.2,0],[106.67,.63],[110.8,.18],[111.3,.48],[113.92,0],[114.32,.22],[116.2,0],[C1,.41],[246.666666667,0]]
    p['controles']['cuerda']['controles']={'presion':pressure,'arco':bow}
    zj,extract=extraer_cuerda(zc,106.2,116.2,pressure,bow,base_midi=64)
    G=1/np.linalg.norm(zj);state=zj*G;base=np.array([64,76,64+12*np.log2(3),64+12*np.log2(5)]);gamma=np.array([.021,.034,.057,.088])
    gates=[[[116.2,118.4],[121.1,124.3],[128.6,131.9],[136.6,140.5],[145.8,C1]],
      [[117.05,120.7],[124.,127.4],[132.1,136.9],[140.3,144.6],[148.1,C1]],
      [[118.9,122.45],[126.7,130.65],[134.4,138.4],[143.6,147.1],[150.25,C1]],
      [[116.8,117.55],[120.2,122.6],[125.6,128.1],[131.3,133.7],[138.,141.4],[146.1,149.9],[151.4,C1]]]
    times=[116.2,120.3,125.8,131.4,137.6,143.8,149.7,C1];segments=[];parents=[ec['id']]*4
    for i,(a,b) in enumerate(zip(times,times[1:])):
        start=base.copy();shift=np.array([0,.07,-.11,.18])*([0,1,-1,2,-2,1,0][i]);end=start+shift
        record={'t':a,'fin':b,'midi_inicio':start.tolist(),'midi_fin':end.tolist(),'z_inicio':pares(state),'gamma':gamma.tolist(),'ventanas':[[] for _ in range(4)]}
        newparents=[]
        for k in range(4):
            windows=[[max(a,u),min(b,v)] for u,v in gates[k] if max(a,u)<min(b,v)]
            record['ventanas'][k]=windows
            e=add(p,'junco'+str(k+1),a,start[k],b-a,.25,'centro: voz con recorrido propio',parents[k],libre=True,midi_fin=float(end[k]),
                fase_inicial_rad=float(np.angle(state[k])),masa=float(abs(state[k])**2),amplitud_relativa=float(abs(state[k])),
                amortiguacion_s_1=float(gamma[k]),salidas=windows,segmento_centro=i)
            newparents.append(e['id'])
        phase=np.array([2*np.pi*integral(x,y,b-a) for x,y in zip(start,end)])
        advanced=state*np.exp(-gamma*(b-a))*np.exp(1j*phase);record['z_fin_antes_cruce']=pares(advanced)
        if i<len(times)-2:
            j,k=[(0,1),(1,2),(2,3),(0,2),(1,3),(0,3)][i];angle=[.23,-.38,.51,-.29,.43,-.34][i]
            R=np.eye(4);R[j,j]=R[k,k]=math.cos(angle);R[j,k]=-math.sin(angle);R[k,j]=math.sin(angle)
            state=R@advanced;record['cruce']={'par':[j,k],'angulo_rad':angle,'matriz':R.tolist(),'rampa_s':.09,
               'interpretacion':'aplicar R(angulo*u) a la observación compleja en los últimos 90 ms del segmento; u va de 0 a 1; el siguiente empieza en R@z_fin',
               'aplicar_antes_de_fin_s':.09,
               'norma_antes':float(np.sum(abs(advanced)**2)),'norma_despues':float(np.sum(abs(state)**2))}
            record['z_fin_despues_cruce']=pares(state)
        else:state=advanced
        segments.append(record);base=end;parents=newparents
    for t,part,m,d in [(107.1,'waterphone',64,.8),(111.01,'guitarra',64,.17),(112.35,'waterphone',76,.64),(133.85,'campana',88,.82)]:
        add(p,part,t,m,d,.15,'reflejo de una recepción, sin pulso',ec['id'],libre=True,**({'articulacion':'madera','caja':1} if part=='guitarra' else {}))
    p['controles']['campana']['eventos']=[{'t':133.85,'hit':9,'vel':.15},{'t':134.,'params':{'pickup':3,'fold':1}}]
    packet={'guitarra_z':pares(z),'cuerda_z':pares(zc),'junco_z':pares(zj),'normalizacion_inicial_junco':G,
      'espera_aprendida_s':tau,'normas':[norm0,norm1,float(np.sum(abs(zj)**2))],'guitarra_captacion':trace,
      'cuerda_captacion':extract,'junco_fin_centro_z':pares(state),'junco_fin_centro_midi':base.tolist(),'ancestros_fin':parents,
      'limite':'Envolventes complejas y norma de control; ganancia activa inicial; no julios ni sistema acústico pasivo.'}
    p['centro_v10']={'paquete':packet,'segmentos':segments,'ventanas_por_voz':gates,'normalizacion_una_vez':True,
      'captacion_db':{'guitarra':-31,'cuerda':-32,'juncos_conjunto':-34,'objetos':-37},
      'ganancia_dependiente_de_RMS':False,'control':'rotaciones, decaimiento, ventanas y fases escritos en este JSON; no rama paralela al regreso'}
    p['cortes_buses']=sorted(p['cortes_buses'],key=lambda c:c['t'])
    dump(out,'borrador-centro-v10.json',p);stage(out,p,3,'Centro con memoria / cuatro recorridos y un estado de llegada');print('centro escrito; espera',tau,'masa llegada',float(np.sum(abs(state)**2)),flush=True)

def return_score():
    out,p=context('borrador-centro-v10.json');set_counter(p);oldplans=json.loads((V8/'datos/transportes-memoria-v8.json').read_text(encoding='utf8'))
    for k in range(1,5):p['eventos']['junco'+str(k)]=[e for e in p['eventos']['junco'+str(k)] if e['t']<C1]
    packet=p['centro_v10']['paquete'];state=complejo(packet['junco_fin_centro_z']);a=abs(state)**2;ph=np.angle(state);source=np.array(packet['junco_fin_centro_midi']);last=C1;parents=packet['ancestros_fin'];plans=[]
    total=float(a.sum())
    for n,old in enumerate(oldplans):
        start=old['t'];fin=old['fin'];ph=(ph+2*np.pi*hz(source)*(start-last))%(2*np.pi)
        retention=np.array(old['retencion']);received=a.copy();a=a*retention
        # Pérdidas de los cortes ocurridos desde la última llegada.
        previouscuts=[]
        for ca,cb in p['agujeros_pared']:
            if last<=ca<start:
                receiver=3 if ca<230 else 0;keep=.43 if receiver==3 else .87;a[receiver]*=keep;previouscuts.append([ca,cb,receiver,keep])
        b=.72*a+.28*np.roll(a,1);target=np.array(old['target']);target+=(packet['espera_aprendida_s']-.773579975233)*np.array([.4,-.2,.25,-.1])
        plan=plan_memoria(source,target,a,b,old['colores_origen'],old['colores_destino'],old['penalizacion'])
        edges=np.array(plan['pi']);arrivals=np.zeros(4,complex);destids=[[] for _ in range(4)]
        currentcuts=[]
        for ca,cb in p['agujeros_pared']:
            if start<=ca<fin:currentcuts.append([ca,cb,3 if ca<230 else 0,.43 if ca<230 else .87])
        for i in range(4):
            for j in range(4):
                mass=edges[i,j]
                if mass<1e-12:continue
                phase=float(ph[i]+2*np.pi*integral(source[i],target[j],fin-start))
                windows=[[start,fin]]
                for ca,cb,rec,keep in currentcuts:
                    windows=[w for u,v in windows for w in ([[u,min(v,ca)]] if v<=ca else [[max(u,cb),v]] if u>=cb else [[u,ca],[cb,v]]) if w[1]>w[0]]
                gains=[[cb,math.sqrt(keep)] for ca,cb,rec,keep in currentcuts if rec==j]
                amplitude=math.sqrt(mass)*math.prod(g for _,g in gains)
                arrivals[j]+=amplitude*np.exp(1j*phase)
                e=add(p,'junco'+str(j+1),start,source[i],fin-start,.41,'transporte que recibe el centro v10',parents[i],midi_fin=float(target[j]),
                      fase_inicial_rad=float(ph[i]),masa=float(mass),amplitud_relativa=math.sqrt(mass),salidas=windows,
                      ganancia_cortes=gains,plan=f'v10-plan-{n+1:02}',origen_fila=i,destino_columna=j)
                destids[j].append(e['id'])
        b_out=b.copy()
        for ca,cb,rec,keep in currentcuts:b_out[rec]*=keep
        destphase=np.where(abs(arrivals)>1e-12,np.angle(arrivals),ph)
        plan.update({'id':f'v10-plan-{n+1:02}','t':start,'fin':fin,'source':source.tolist(),'target':target.tolist(),
          'masa_recibida':received.tolist(),'a':a.tolist(),'b':b.tolist(),'b_salida':b_out.tolist(),'fases_origen':ph.tolist(),
          'fases_destino':destphase.tolist(),'ancestros':parents,'eventos_destino':destids,'cortes_anteriores':previouscuts,'cortes_internos':currentcuts})
        plans.append(plan);source=target;a=b_out;ph=destphase;parents=[es[0] if es else parents[j] for j,es in enumerate(destids)];last=fin
    p['transportes_v10']=plans
    # La reunión conserva el tipo de diálogo que gustó, recalculando sus fuentes.
    tau=packet['espera_aprendida_s'];center_ids=[e['id'] for k in range(1,5) for e in p['eventos']['junco'+str(k)] if C0<=e['t']<C1]
    center_pitch=np.array(packet['junco_fin_centro_midi']);delta=tau-.773579975233
    for part in ['terminal','androide']:
        solo=[e for e in p['eventos'][part] if 153.333<=e['t']<180]
        for i,e in enumerate(solo):
            source_voice=i%4;e['midi']+=float(center_pitch[source_voice]-[64,76,83.01955000865,91.86313713865][source_voice])+delta*(1 if i%2 else -1)
            e['hz']=float(hz(e['midi']));e['ancestro']=packet['ancestros_fin'][source_voice];e['revision']='v10'
            e['t']+=delta*.2*(i%3-1);e['dur']*=1+delta*.06
            e['salidas']=[[e['t'],min(180,e['t']+e['dur'])]];e['derivacion']='altura de llegada central y espera aprendida; contorno del solo previo conservado'
    p['controles']['terminal']['controles']['vector_y']=[[C1,.17],[160.133333333,norm_ratio(packet)],[180,.31]]
    # Sólo dos frases del solista en el regreso; las otras se vuelven articulación de cuerpos distintos.
    moved={}
    for e in list(p['eventos']['voz']):
        if 180<=e['t']<206.667 and any(s in e['frase'] for s in ['coro-noche','coro-otras']):
            p['eventos']['voz'].remove(e);part='corocuerda' if 'noche' in e['frase'] else 'corojunco';p['eventos'][part].append(e);moved[e['frase']]=part
    for l in p['letra']:
        if l['frase'] in moved:l['capa']=moved[l['frase']]
    # Sustituir sólo la espera añadida, no desplazar cada sílaba por rutina.
    for l in p['letra']:
        if l.get('espera_heredada_s',0)>0:
            ids=set(l['ids']);first=True
            for es in p['eventos'].values():
                for e in sorted([e for e in es if e['id'] in ids],key=lambda e:e['t']):
                    if first:first=False;continue
                    e['t']+=delta;e['salidas']=[[u+delta,v+delta] for u,v in e['salidas']]
            l['fin']+=delta;l['espera_heredada_s']=tau
    # La tercera ola recuerda el gesto de la exposición por omisión y remate.
    source_cadence=p['desarrollo_v10'][6]['ids'][-1]
    for e in p['eventos']['guitarra']:
        if 233.333<=e['t']<246.63:e['ancestro']=source_cadence;e['derivacion']='la última ola conserva la cesura del episodio G, con cuerpo continuo'
    # La coda hereda la masa efectiva después del último corte.
    phase_coda=ph[3]+2*np.pi*float(hz(source[3]))*(246.876666667-last)
    add(p,'junco4',246.876666667,source[3],4.3,.14,'residuo de la última recepción',parents[3],fase_inicial_rad=float(phase_coda%(2*np.pi)),
         masa=float(a[3]),amplitud_relativa=float(math.sqrt(a[3])),libre=True,amortiguacion_s_1=.12)
    p['analisis_datos']={'paquete':'centro_v10.paquete','encuentros':'encuentros_v10','planes':'transportes_v10',
       'espera_aprendida_s':tau,'masa_inicial_transporte':total,'masa_final':float(a.sum()),'telefono_apagado_s':236.3}
    p['interpretacion']={'datos_canonicos':'partitura-v10.json; todo estado, curva y ventana se guarda aquí',
       'nuevos':{'guitarra':'GuitarraMemoria; seis cuerdas, tres cajas, ocho modos; contacto lee carga persistente',
                 'junco':'centro_v10.segmentos y transportes_v10; fase integrada y recepción efectiva'},
       'limite':'Partitura corregida y resolución de controles sin audio nuevo; equilibrio perceptivo pendiente de interpretación.'}
    p['reglas']['centro']='cuatro ventanas diferentes, amortiguación y cruces; llegada usada como fuente del transporte'
    p['edicion_v10']={'tipo':'partitura proporcional completa y MusicXML de salidas; controles exactos en JSON',
       'no_aplicar_rama_v9':True,'no_utilizar_PCM_r2':True,'2_40':'referencia favorable que puede transformarse; solos conservan identidad y reciben otra llegada'}
    p['correcciones']=['Recomponer exposición y acompañamiento en nueve episodios','Restaurar raíz y tenis con prosodia completa',
       'Escribir centro con ventanas independientes y estado que llega al regreso','Recalcular 24 planes y la coda',
       'Actualizar partitura completa; no conservar metadatos v9 sin consumo']
    for es in p['eventos'].values():es.sort(key=lambda e:e['t'])
    for e in p['eventos']['guitarra']:
        states=[x for x in p['encuentros_v10'] if x['t']<=e['t']];cents=states[-1]['despues'] if states else [0,0,0]
        e['afinaciones_cajas_cents']=cents
        par=e['parametros_motor'];e['midi']=float(par['midi']+cents[par['caja']]/100+12*np.log2(par.get('parcial',1)));e['hz']=float(hz(e['midi']))
    p['letra'].sort(key=lambda e:e['t'])
    dump(out,'partitura-v10.json',p);stage(out,p,4,'Regreso recalculado / el centro cambia la continuación');print('v10 completa',sum(map(len,p['eventos'].values())),'eventos',flush=True)
def norm_ratio(packet):return float(packet['normas'][1]/packet['normas'][0])
if __name__=='__main__':{'iniciar':init,'exposicion':exposure,'centro':center,'regreso':return_score}[sys.argv[1]]()
