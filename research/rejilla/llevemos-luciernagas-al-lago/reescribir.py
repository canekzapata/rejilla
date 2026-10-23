"""Segunda composición: frase, contacto, transferencia, regreso. Sólo partitura.

Carpeta exclusiva; cada etapa se conserva antes de producir la siguiente.
"""
from pathlib import Path
import copy, hashlib, io, json, math, uuid
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from modelos_memoria import (encuentro,contacto,complejo,pares,recibir,plan_memoria,
                            transferir_fases,comprobar)

ROOT=Path(__file__).resolve().parent
OLD=ROOT/'luciernagas-partitura-s1-054923e7c401'
P=copy.deepcopy(json.loads((OLD/'partitura-v4.json').read_text('utf8')))
Q=P['negra_s'];B=4*Q;C0,C1=P['centro'];P1=180.;P2=206.66666666666666;STOP=P['corte_banda'];D=P['duracion']
R=json.loads((OLD/'datos/recorrido.json').read_text('utf8'))
SEED=2026102201;VERSION='luciernagas-partitura-5.0'
nonce=uuid.uuid4().hex
initial=next((OLD/'proceso').glob('01-visor-elegido-*.png')).read_bytes()
program=Path(__file__).read_bytes()+(ROOT/'modelos_memoria.py').read_bytes()
full=hashlib.sha256(initial+VERSION.encode()+program+nonce.encode()).hexdigest();TAG=full[:12]
OUT=ROOT/f'luciernagas-reescritura-s1-{TAG}';OUT.mkdir(exist_ok=False)
for d in ['proceso','datos','fuentes']:(OUT/d).mkdir()

def put(name,data):
    with (OUT/name).open('xb') as f:f.write(data)
def js(name,data):put(name,json.dumps(data,ensure_ascii=False,indent=1).encode('utf8'))
def hz(m):return 440*2**((m-69)/12)
def midi(f):return 69+12*math.log2(f/440)
def font(n,b=False):return ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if b else 'arial.ttf'),n)
def stage(number,title,score):
    im=Image.new('RGB',(1600,1000),'#101c1b');d=ImageDraw.Draw(im)
    d.text((45,30),title,font=font(38,True),fill='#eee7c9')
    d.text((45,90),'Semilla 1 / revisión escrita / captura de una etapa real / sin audio',font=font(21),fill='#bad0b7')
    x0,x1,y0,row=300,1550,175,19
    for j,tr in enumerate(score['partes']):
        y=y0+j*row;d.text((35,y-7),f'{j+1:02} {tr["nombre"][:29]}',font=font(14),fill='#c9d9c5')
        for e in score['eventos'][tr['id']]:
            x=x0+(x1-x0)*e['t']/D;xx=x0+(x1-x0)*(e['t']+e['dur'])/D
            d.line((x,y,max(x+1,xx),y),width=2,fill='#e7aa75' if e.get('libre') else '#9bd8cb')
    for s in score['secciones']:
        x=x0+(x1-x0)*s['t']/D;d.line((x,y0-15,x,y0+36*row),fill='#647d70');d.text((x+2,y0-37),s['id'],font=font(17,True),fill='#eee7c9')
    d.text((45,920),f'{sum(map(len,score["eventos"].values()))} eventos / 36 partes / 4:18.667',font=font(24),fill='#eee7c9')
    bb=io.BytesIO();im.save(bb,format='PNG');put(f'proceso/{number:02}-{title.split(" / ")[0].lower().replace(" ","-")}-s1-{TAG}.png',bb.getvalue())

js('receta-inicial.json',{'id':TAG,'id_completo':full,'nonce':nonce,'version':VERSION,
   'semilla_terreno':1,'semilla_composicion':SEED,'imagen_sha256':hashlib.sha256(initial).hexdigest(),
   'programa_sha256':hashlib.sha256(program).hexdigest(),'origen':OLD.name,
   'partitura_anterior_sha256':hashlib.sha256((OLD/'partitura-v4.json').read_bytes()).hexdigest(),
   'etapa':'Reescritura y análisis; no audio ni másters.'})
for f in ['recorrido.json','terreno-s1.json']:put('datos/'+f,(OLD/'datos'/f).read_bytes())
stage(1,'Herencia / partitura anterior',P)

# Guardar el acompañamiento de exposición, identificando sus parentescos reales.
E={k:[] for k in P['eventos']}
true_q={'Q presentada','contracanto oblicuo','vocal del rasgueo','tensión / huecos'}
for k,events in P['eventos'].items():
    if k in ['voz','duo','corocuerda','corojunco']:continue
    for old in events:
        if old['t']>=C0:continue
        e=copy.deepcopy(old);e['dur']=min(e['dur'],C0-.035-e['t'])
        if e['dur']<=.01:continue
        if e['frase'] not in true_q:e['ancestro']=None
        e['procedencia']='exposición conservada de v4'
        if e['frase'] in true_q:e['operacion_herencia']='Q: transposición y escala temporal explicitadas por alturas/ataques'
        E[k].append(e)
P['eventos']=E;P['letra']=[];P['version']=VERSION;P['correcciones']=[]
P['interpretacion']['datos_canonicos']='partitura-v5.json; segundos, Hz y controles de esta revisión'
N=0
def ter(t):
    samples=R['muestras'];tt=[v['t'] for v in samples]
    return {a:float(np.interp(t,tt,[v[b] for v in samples])) for a,b in
            [('altura_m','z_m'),('pendiente','pendiente'),('deuda_cents','deuda_cents'),('u','u'),('v','v')]}
def section(t):return next(s['id'] for s in P['secciones'] if s['t']<=t<s['fin']+1e-8)
def note(k,t,m,d=.2,v=.5,art='ordinario',parent=None,phrase='',**kw):
    global N
    assert 0<=t<D and d>0,(k,t,d)
    N+=1;e=dict(id=f'r{N:05}',t=round(float(t),8),dur=round(min(float(d),D-t),8),midi=float(m),hz=hz(m),
       vel=float(v),pan=next(x['pan'] for x in P['partes'] if x['id']==k),articulacion=art,
       seccion=section(t),frase=phrase,ancestro=parent,terreno=ter(t),**kw)
    E[k].append(e);return e

# Frases completas: ritmos, acentos y respiración escogidos para cada texto.
vocal_specs=[
 ('lata','hay u na la ta en el a gua',8.25,[64,67,65,64,59,60,64,62,59],[1,.5,.5,1.5,.5,.75,.25,1,2],[0,3,7],'Hay una lata en el agua','nuevo'),
 ('raiz','u na ra íz sa le por la bo ca',12,[59,60,63,64,65,64,62,60,59,64],[.5,.5,.75,2,.5,.5,1,.5,1.5,2],[3,4,8],'una raíz sale por la boca','nuevo'),
 ('tenis','tra es lo do en los te nis',17.5,[67,65,64,60,59,62,64,60],[.75,.25,1.5,.5,.5,.5,1.5,.75],[0,2,6],'traes lodo en los tenis','nuevo'),
 ('mosco','y e se mos qui to nos a ta ca',21,[64,64,67,65,64,59,60,62,65,64],[.25,.5,.25,1,.5,1.25,.5,.5,1.5,.5],[1,4,8],'y ese mosquito nos ataca','adaptación del corpus'),
 ('cabezas','nues tras ca be zas cho can',25.25,[59,60,64,65,64,67,65],[.5,.5,.25,1.5,.25,.75,1.25],[0,3,5],'nuestras cabezas chocan','fragmento literal'),
 ('acuerdo','de ci mos sí al mis mo tiem po',28.5,[62,64,60,67,65,64,62,60,64],[.5,1,.5,2,.25,1,.5,2,1],[1,3,7],'decimos sí al mismo tiempo','fragmento literal'),
 ('coro-lago','lle ve mos u nas lu ciér na gas al la go',33,[64,59,60,64,67,65,64,67,65,62,64,64],[.5,1,.5,.5,.5,.25,1.75,.25,.5,.5,1,2],[1,3,6,10],'llevemos unas luciérnagas al lago','verso literal'),
 ('coro-noche','a es pe rar a que cai ga la no che',36.2,[67,65,64,62,64,65,67,64,60,59,64],[.25,.5,.5,1.75,.5,.5,1.25,.25,.5,2,.75],[3,6,9],'a esperar a que caiga la noche','verso literal'),
 ('coro-amor','es po si ble que el a mor e xis ta',40.1,[59,60,64,65,64,62,60,67,65,64,59],[.5,.5,1.5,.5,.25,.25,.5,2,.25,1.5,1],[2,7,9],'es posible que el amor exista','verso literal'),
 ('coro-otras','en o tras for mas de ex pe rien cia',44.7,[64,65,64,60,59,64,62,60,65,64],[.5,1.5,.5,1,.5,.5,.25,.5,2,2.5],[1,3,8],'en otras formas de experiencia','verso literal')]

def sing(spec,k='voz',start=None,scale=1.,returning=False,gap=0.,parent=None,shift=0):
    name,sy,bar,mel,rhythm,stress,plain,src=spec
    ss=sy.split();assert len(ss)==len(mel)==len(rhythm)
    t=bar*B if start is None else start;initial=t
    if returning:name+='-regreso'
    if k!='voz':name+='-'+k
    ids=[]
    for j,(syll,m,beats) in enumerate(zip(ss,mel,rhythm)):
        if returning and j==1:t+=gap
        length=beats*Q*scale
        e=note(k,t,m+shift,length*.91,.78 if j in stress else .56,'canto; acento escrito' if j in stress else 'canto ligado',
               parent if returning and j==1 else None,name,texto=syll,silaba=j+1,silabas_total=len(ss),
               acento=j in stress,respiracion_antes=returning and j==1,origen_texto=src,
               operacion_herencia='espera del relevo central' if returning and j==1 else 'frase vocal escrita, sin ancestro ficticio')
        ids.append(e['id']);t+=length
    P['letra'].append(dict(t=initial,fin=t,capa=k,texto=plain,silabas=sy,frase=name,procedencia=src,
       acentos_indices=stress,ritmo_negras=rhythm,escala=scale,espera_heredada_s=gap if returning else 0,ids=ids))
    return ids

for spec in vocal_specs:sing(spec)
sing(('respuesta-vi','ya lo vi',23,[55,59,52],[1,.5,2],[0,2],'ya lo vi','nuevo'),'duo')
sing(('respuesta-juntos','al mis mo tiem po',31.5,[59,60,62,60,59],[.5,1,.5,1.5,1],[1,3],'al mismo tiempo','adaptación'),'duo')
js('borrador-voz.json',P);stage(2,'Frases / voz y respiración',P)

# Tres promesas se presentan en dúos antes del centro. Después el orden importa.
MEET=[];x=np.zeros(3)
def meet(t,i,j,target,parent=None):
    global x
    before=x.copy();x=encuentro(x,i,j,target)
    MEET.append(dict(t=t,i=i,j=j,promesa_cents=target,antes=before.tolist(),despues=x.tolist(),ancestro=parent))
    return x.copy()
for t,i,j,target in [(22.,0,1,0),(56.4,1,2,0),(87.9,2,0,85)]:
    xx=meet(t,i,j,target)
    for box in [i,j]:note('guitarra',t+.017*box,64+xx[box]/100,.62,.32,'promesa entre dos cajas',phrase=f'promesa-{i}{j}',cuerda=4,caja=box)

# La lata toca agua; el contacto adquiere carga y un umbral más resistente.
dip=note('piano',29.1,76,.17,.31,'lata: papel y borde',phrase='objeto-en-el-agua',altura_asignable=False,
         accion_material={'pelicula_antes':.05,'pelicula_despues':.65,'causa':'acción compuesta; no humedad medida'})
attempt=contacto([[0,0],[.3,.30],[1.5,.30],[1.9,0]],.65)
failed=note('guitarra',C0-3.6,64,1.9,.18,'friccion sostenida: intento sin parcial',dip['id'],'contacto-anticipado',
     contacto=attempt,cuerda=4,caja=0,altura_asignable=False)
P['controles']['guitarra']={'version':'GuitarraMemoria','encuentros':'datos/encuentros.json',
    'afinacion':'interpolar estados de cada encuentro en 30 ms; no recalcular compromiso global',
    'pelicula':[[0,.05],[29.1,.65],[STOP,.65]],'contacto':'evaluar contacto a dt=.005; interpolar drive y ruido; no reatacar por muestra'}

# Centro: tiempos de transferencia derivados del estado que deja el contacto.
center_start=C0+.41
e1=note('guitarra',center_start,64,1.9,.17,'friccion: persiste el fallo',failed['id'],'centro-intento',
        libre=True,contacto=attempt,cuerda=4,caja=0,altura_asignable=False)
wood=note('guitarra',e1['t']+e1['dur']+1.31,64,.19,.21,'madera',e1['id'],'retirada',libre=True,cuerda=4,caja=0,altura_asignable=False)
success=contacto([[0,0],[.4,.91],[2.8,.91],[3.1,0]],.65)
t_contact=wood['t']+wood['dur']+3.49
rub=note('guitarra',t_contact,64,3.1,.24,'friccion: carga y deslizamiento',wood['id'],'contacto-conseguido',
         libre=True,contacto=success,cuerda=4,caja=1,altura_asignable=False)
slip=success['deslizamientos_s'][0];slip_event=note('guitarra',t_contact+slip,64+12*math.log2(5),.63,.23,'armonico',rub['id'],'parcial-que-escapa',
     libre=True,cuerda=4,caja=1,nodo=.2,parcial=5,operacion_herencia='primer deslizamiento del contacto; parcial 5')
z8=complejo(success['z_final']);indices=np.array([0,1,2,4]);zg=z8[indices]
wait1=2.3+6*float(abs(zg[-1])**2/np.sum(abs(zg)**2))
t_cuerda=t_contact+3.1+wait1
zc=recibir(zg,wait1,[.07,.12,.19,.37],.47)
retained=float(np.sum(abs(zc)**2)/np.sum(abs(zg)**2));learned=.42+1.1*(1-retained)
cuerda=note('cuerda',t_cuerda,64,4.17+retained,.28,'recibir envolventes; arco entra tras el relevo',slip_event['id'],'cuerda-recibe',
     libre=True,inyeccion_modal={'z':pares(zc),'fuente':pares(zg),'modos':[1,2,3,5],'espera_s':wait1,
     'retenciones':[.07,.12,.19,.37],'angulo':.47},operacion_herencia='recibir: amortiguación y rotación de cuatro envolventes complejas')
water=note('waterphone',t_cuerda+.63,64+12*math.log2([1,2,3,5][int(np.argmax(abs(zc)**2))]),.72,.16,
    'normal: captación parcial',cuerda['id'],'reflejo-del-modo-dominante',libre=True,operacion_herencia='altura del modo de máxima norma recibido')
meet(t_contact+slip,0,1,0,slip_event['id']);meet(t_cuerda,1,2,0,cuerda['id'])
t_junco=cuerda['t']+cuerda['dur']+5.13
zj=recibir(zc,learned,[.11,.17,.28,.83],-.61)
source=np.array([64+12*math.log2(h) for h in [1,2,3,5]])
center_j=[]
for j in range(4):
    ee=note('junco'+str(j+1),t_junco+.19*j,float(source[j]),[2.8,3.6,5.1,1.7][j],.18+.02*j,
       'recibe una envolvente; conserva fase',cuerda['id'],'junco-recibe',libre=True,
       estado_complejo=pares([zj[j]])[0],fase_inicial_rad=float(np.angle(zj[j])),
       masa=float(abs(zj[j])**2),operacion_herencia='rotación y amortiguación del paquete recibido por cuerda')
    center_j.append(ee)
meet(t_junco,2,0,85,center_j[0]['id'])
return_c=note('cuerda',t_junco+5.1+4.23,59.01955,2.31,.21,'recibe el hueco; arco y presión separados',center_j[2]['id'],
    'cuerda-recibe-la-perdida',libre=True,espera_heredada_s=learned,operacion_herencia='tercer parcial de Mi3; el hueco procede de la pérdida de norma')
bell=note('campana',return_c['t']+return_c['dur']+6.79,88,.81,.17,'captación 3',return_c['id'],'cambia-de-vecindad',libre=True)
last=note('junco4',bell['t']+bell['dur']+5.17,source[-1]-.41,1.93,.14,'resto; parcial retenido',center_j[3]['id'],'último-resto',libre=True,
     estado_complejo=pares([zj[-1]])[0],fase_inicial_rad=float(np.angle(zj[-1])),masa=float(abs(zj[-1])**2))
assert last['t']+last['dur']<C1-2
PACKET={'contacto_evento':rub['id'],'parcial_evento':slip_event['id'],'cuerda_evento':cuerda['id'],
 'junco_eventos':[e['id'] for e in center_j],'guitarra_z':pares(zg),'cuerda_z':pares(zc),'junco_z':pares(zj),
 'espera_hasta_cuerda_s':wait1,'retencion_norma':retained,'espera_aprendida_s':learned,
 'normas':[float(np.sum(abs(z)**2)) for z in [zg,zc,zj]],
 'limite':'Envolventes normalizadas; no extracción desde audio ni energía acústica.'}
center_events=[e for es in E.values() for e in es if C0<=e['t']<C1]
intervals=sorted((e['t'],e['t']+e['dur']) for e in center_events);union=[]
for a,b in intervals:
    if union and a<=union[-1][1]:union[-1][1]=max(b,union[-1][1])
    else:union.append([a,b])
P['oscuridades']=[];end=C0
for a,b in union+[[C1,C1]]:
    if a-end>=1.25:P['oscuridades'].append([end+.025,a-.025])
    end=max(end,b)
js('borrador-centro.json',P);js('datos/paquete-modal.json',PACKET)
stage(3,'Contacto / estados y transferencias',P)

# Reunión gradual. Cada familia recibe un intervalo o espera del relevo.
def snap(m,t,box=0):
    w=min(1,max(0,(t-C1)/(P2-C1)));target=midi(hz(40)*max(1,round(hz(m)/hz(40))))
    return (1-w)*m+w*target
for t,k,m,d in [(C1+.71,'arpa',64,1.3),(C1+3.12,'mbira',59.01955,.73),(C1+5.3,'organo',52,7.7),
                (C1+6.37,'cuerda',64,4.7),(C1+9.7,'chelo',40,3.1),(C1+12.3,'arpaboca',52,.8)]:
    note(k,t,m,d,.37,'respuesta al relevo',cuerda['id'],'reunión',espera_heredada_s=learned)

# Solos: tomar los intervalos y duraciones de la respuesta central, no otra lista.
solo_source=[center_j[0],water,return_c,last]
for n,(k,a,b,shift) in enumerate([('terminal',C1+6.8,C1+13.1,0),('androide',C1+13.1,P1-1,-24)]):
    t=a;i=0
    while t<b-.2:
        parent=solo_source[i%4];step=min((parent['dur']*.35+learned*.22)/(1+.12*(i//4)),b-t)
        mm=snap(parent['midi']+shift+([0,7,-5,0][i%4]),t)
        e=note(k,t,mm,step*.78,.61,'solo: contracción del relevo',parent['id'],f'solo-heredado-{k}',
               operacion_herencia='altura central + intervalo [0,7,-5,0]; duración central contraída')
        if i%3==2:note('fotones',t+step*.83,mm+12,.09,.3,'cierre de frase',e['id'],'fotones-contestan')
        if i%4==3:note('aro',t+step*.91,37,.06,.37,'réplica al hueco',e['id'],'aro-contesta',pieza='rim',altura_asignable=False)
        t+=step+(learned if i%7==6 else 0);i+=1

CH=[[40,47,52,59],[40,48,53,60],[43,50,55,62],[40,47,53,59]]
for bar in range(16,56):
    t0=C1+bar*B
    if t0>=STOP:break
    # Sólo VII conserva banda completa; VIII se escribe aparte.
    if t0>=P2:break
    chord=CH[((bar-16)//2)%4]
    hits=[0,1.5,2.75] if bar%2==0 else [.5,2,3.25]
    for j,beat in enumerate(hits):
        if bar==16 and j==0:continue
        for vi,m in enumerate(chord):note('guitarra',t0+beat*Q+vi*.003,snap(m,t0),.47,.41,'rasgueo con ataque perdido',phrase='riff-regresa',cuerda=vi,caja=vi%3)
    for j,beat in enumerate([0,1.5,2.75]):
        if bar%4==0 and j==0:continue
        note('bajo',t0+beat*Q,snap([40,47,43][j],t0),.31,.65,'dedo',phrase='bajo-aprende-hueco')
    for beat in ([0,2.5] if bar%2==0 else [.75,2.75]):note('bombo',t0+beat*Q,36,.12,.73,'pregunta',phrase='grave-VII',pieza='kick',altura_asignable=False)
    for beat in ([1,3] if bar%3 else [1.5,3.25]):note('caja',t0+beat*Q,38,.11,.66,'respuesta desplazada',phrase='caja-VII',pieza='snare',altura_asignable=False)
    for j in [0,1,3,4,6]:note('hat',t0+j*Q/2,42,.04,.29,'corto',phrase='hat-con-respiración',pieza='hat',altura_asignable=False)

for j in range(7):
    t=C1+14+j*1.71
    if t<P1:note('bombo' if j%2==0 else 'tom',t,36 if j%2==0 else 43,.12,.3+j*.04,'la banda aprende a entrar',
        center_j[j%4]['id'],'reunión-percutida',pieza='kick' if j%2==0 else 'tomlo',altura_asignable=False)

for i,spec in enumerate(vocal_specs[6:]):
    m=list(spec);m[0]+='-humano';m[3]=[snap(v,P1+i*4*B) for v in spec[3]]
    sing(tuple(m),start=P1+i*4*B,scale=.96,returning=True,gap=learned,parent=center_j[2]['id'])
    for j,eid in enumerate(P['letra'][-1]['ids']):
        ev=next(e for e in E['voz'] if e['id']==eid)
        if j in [len(spec[3])-2,len(spec[3])-1]:
            note('clarinete',ev['t']+learned*.25,ev['midi']+12,ev['dur']*.7,.27,'respuesta que ahora espera',eid,'clarinete-hereda',operacion_herencia='últimas dos alturas del regreso vocal, +12 y demora aprendida/4')

# Tres olas con conductas distintas, cortes y pérdidas persistentes.
HOLES=[[P2+6.3*B,P2+6.3*B+.53],[P2+12.9*B,P2+12.9*B+.83],[STOP-2.2,STOP-1.85]]
P['agujeros_pared']=HOLES
for j in range(8):
    t=P2+j*B
    if j%2==0:
        for k,shift in [('cuerda',0),('chelo',-24),('arpa',12)]:note(k,t+.11*(['cuerda','chelo','arpa'].index(k)),snap(64+shift,t),2.7,.33,
            'ola 1: resonancia compartida',center_j[j%4]['id'],'pared-resonancias')
    note('bombo',t+.5*Q,36,.13,.5,'paso aislado',phrase='pared-paso',pieza='kick',altura_asignable=False)
    for vi,m in enumerate(CH[(j//2)%4][:2]):note('guitarra',t+vi*.01,snap(m,t),1.2,.31,'rasgueo abierto, dejar caer',phrase='pared-primera',cuerda=vi,caja=vi)
for i,spec in enumerate(vocal_specs[6:8]):
    sing(spec,'corocuerda',start=P2+i*4*B+.3,scale=.89,returning=True,gap=learned,parent=cuerda['id'],shift=-12)

# Ola 2: ataques con una fuente y tres generaciones de réplicas.
contagios=[]
for j in range(8):
    t=220+j*B
    seed=note('mbira',t,snap([64,59,60,65,64][j%5],t),.19,.53,'llamada del contagio',center_j[j%4]['id'],'pared-llamada')
    parent=seed
    for depth,(k,delay,shift) in enumerate([('berimbau',.21,-12),('guitarra',.37,-24),('piano',.19,0)]):
        t=parent['t']+delay+learned*.11*(depth+1)
        child=note(k,t,parent['midi']+shift,.19+depth*.12,.43,'réplica por contacto',parent['id'],'pared-contagio',
            generacion=depth+1,operacion_herencia=f'altura anterior {shift:+} semitonos; demora {t-parent["t"]:.6f} s',cuerda=j%6,caja=depth%3)
        contagios.append([parent['id'],child['id']]);parent=child
        piece=['rim','snare','tomlo'][depth];pk=['aro','caja','tom'][depth]
        note(pk,t+.035,37,.09,.48,'la percusión recibe un ataque',child['id'],'percusión-contagio',pieza=piece,altura_asignable=False)
    if j%2:note('ride',t+.31,51,.74,.36,'borde del contagio',parent['id'],'ride-aprende',pieza='ride',altura_asignable=False)

# Ola 3: ocupación continua, ataques asimétricos y una frase humana legible.
for j in range(8):
    t=233.33333333333334+j*B
    for vi,m in enumerate(CH[(j//2)%4]):
        for h in range(5+(j%3)):
            note('guitarra',t+h*B/(5+j%3)+vi*.002,snap(m,t),.38,.35+.08*(h==0),
                 'ola 3: alambre continuo',phrase='pared-continuidad',cuerda=vi,caja=vi%3)
    for k,shift in [('cuerda',0),('organo',-12),('sala',12)]:note(k,t,snap(64+shift,t),B+.12,.39,'continuidad y batido',center_j[j%4]['id'],'pared-casi-cuerpo')
    beats=[0,1.5,2,4.25,5.5] if j%2==0 else [0,1,2.5,4,5.25,6]
    for z,beat in enumerate(beats):
        tt=t+beat*.5*Q
        pk='bombo' if z%2==0 else 'caja'
        note(pk,tt,36 if pk=='bombo' else 38,.12,.76,'Q/R comprimidas',phrase='percusión-temática',pieza='kick' if pk=='bombo' else 'snare',altura_asignable=False)
    for z in range([3,5,7][j%3]):note('hat',t+z*B/[3,5,7][j%3],42,.05,.34,'división que cambia con la frase',phrase='hat-357',pieza='hat',altura_asignable=False)
    if j%2:note('bajo',t+learned,snap(40,t),1.1,.71,'grave entra después de la espera',center_j[2]['id'],'bajo-último')
phone=('telefono','a pa ga el te lé fo no',0,[64,60,59,64,67,65,64,59],[.5,.5,.5,1,.5,1.5,.5,1],[1,5],'apaga el teléfono','nuevo')
sing(phone,'duo',start=233.8,scale=1.)
phone_end=P['letra'][-1]['fin']
sing(('juntos-final','sí al mis mo tiem po',0,[67,65,64,62,60,64],[2,.5,1,.5,2,3],[0,2,4],'sí al mismo tiempo','adaptación'),
     start=STOP-7.1,returning=True,gap=learned,parent=center_j[2]['id'])

# Planes encadenados: fuente y masa son la llegada anterior; pérdida explícita.
plans=[];src=source.copy();a=abs(zj)**2;a/=a.sum();phase=np.angle(zj);colors=np.arange(4);t=C1+.71;last_ids=[e['id'] for e in center_j];last_groups=[[v] for v in last_ids];k=0
while t<STOP-.9:
    next_t=min(STOP-.12,t+(3.2+.36*(k%3)+learned*.4))
    keep=np.array([.997,.996,.994,.991])
    passed=[h for h in HOLES if (plans[-1]['t'] if plans else C1)<h[1]<=t]
    if passed:keep[-1]*=.43;keep[0]*=.87
    origin_mass=a.copy();aa=a*keep;loss=origin_mass-aa
    mix=np.eye(4)*.72+np.roll(np.eye(4),1,axis=0)*.28
    bb=mix@aa
    goal=np.array([snap(m,t) for m in [64,71,76,83]])+x[np.arange(4)%3]/100
    # Recorridos intencionalmente distintos: memoria de familia y pérdida del quinto parcial.
    target_colors=np.roll(colors,1 if k%3 else -1);penalty=130. if k%3==1 else 0.
    plan=plan_memoria(src,goal,aa,bb,colors,target_colors,penalty)
    plain=plan_memoria(src,goal,aa,bb,colors,target_colors,0)
    duration=next_t-t;pi=np.array(plan['pi']);pid=f'memoria-{k+1:02}'
    plan.update(id=pid,t=t,fin=next_t,source=src.tolist(),target=goal.tolist(),a=aa.tolist(),b=bb.tolist(),
        masa_recibida=origin_mass.tolist(),perdida=loss.tolist(),penalizacion=penalty,
        colores_origen=colors.tolist(),colores_destino=target_colors.tolist(),
        cambio_pi_sin_familias=float(np.max(abs(pi-np.array(plain['pi'])))),
        anterior=plans[-1]['id'] if plans else 'paquete-modal',fases_origen=phase.tolist(),
        ancestros=last_ids,retencion=keep.tolist(),cortes_anteriores=[h[1] for h in passed])
    ids_by_dest=[[] for _ in range(4)]
    for i in range(4):
        for j in range(4):
            if pi[i,j]<1e-12:continue
            e=note('junco'+str(j+1),t,float(src[i]),duration,.20 if t<P2 else (.29 if t<233.333 else .41),
                'transporte heredado; fase por arista',last_ids[i],pid,midi_fin=float(goal[j]),masa=float(pi[i,j]),
                amplitud_relativa=float(np.sqrt(pi[i,j])),fase_inicial_rad=float(phase[i]),
                plan=pid,origen_fila=i,destino_columna=j,contribuyentes_estado=last_groups[i],operacion_herencia='fuente y masa recibidas del plan anterior')
            ids_by_dest[j].append(e['id'])
    # Cada receptor guarda la fase resultante tras integrar su trayectoria.
    from instrumentos import Junco
    osc=Junco();osc.phase[:]=phase[:,None]
    osc.avanzar(duration,src,goal,0,1,pi)
    zsum=np.sum(np.sqrt(pi)*np.exp(1j*osc.phase),axis=0)
    phase=np.where(abs(zsum)>1e-12,np.angle(zsum),phase)
    plan['fases_destino']=phase.tolist();plan['eventos_destino']=ids_by_dest
    plans.append(plan);src=goal;a=bb;colors=target_colors
    last_ids=[ids[0] if ids else last_ids[j] for j,ids in enumerate(ids_by_dest)]
    last_groups=ids_by_dest
    t=next_t;k+=1

# Relojes heredados: las emisiones toman la última respuesta disponible y esperan si está ocupada.
clock_stats=[]
for idx,cl in enumerate(P['relojes']):
    k=cl['capa'];candidates=[e for e in json.loads((OLD/'partitura-v4.json').read_text('utf8'))['eventos'][k] if C1<=e['t']<STOP]
    played=held=0
    for i,e in enumerate(candidates):
        parent=center_j[(i+idx)%4];tt=e['t'];delay=learned if i%5==idx else 0
        tt+=delay
        if tt>=STOP or (k=='boca' and tt>=phone_end):held+=1;continue
        if k=='fotones' and (i+idx)%3:held+=1;continue
        m=snap(parent['midi']-12*(idx%2),tt)
        note(k,tt,m,.13 if k=='fotones' else .39,.27,'reloj continúa; emisión recibe otra frase',parent['id'],
            f'reloj-heredado-{cl["periodo"]}',fase_acumulada=e.get('fase_acumulada',0),
            espera_heredada_s=delay,cuerda=(i+idx)%5)
        played+=1
    clock_stats.append(dict(**cl,emisiones_revision=played,emisiones_retenidas=held))
P['relojes']=clock_stats
P['controles']['boca']['silencio_desde']=phone_end
P['controles']['campana']['eventos']=[{'t':bell['t'],'hit':9,'vel':.17},{'t':bell['t']+.12,'params':{'pickup':3,'fold':1}}]
P['controles']['terminal']={'controles':{'vector_x':[[C1,0],[C1+13.1,1]],'vector_y':[[C1,.17],[C1+6.8,retained],[P1,.31]]}}
P['controles']['arpa']['enlaces']=[[pl['t']+.2,i%5,(i+2)%5,(-1 if i%2 else 1)*(.3+learned)] for i,pl in enumerate(plans)]
P['controles']['cuerda']['controles']={'presion':[[0,.1],[C0,.12],[t_cuerda,.19],[t_cuerda+1.7,.73],[C1,.31],[P2,.65],[STOP,0]],
                                    'arco':[[0,0],[t_cuerda,0],[t_cuerda+.47,.63],[t_cuerda+4.17+retained,0],[C1,.41],[STOP,0]]}

# Afinaciones leídas desde encuentros; parámetros consumibles por GuitarraMemoria.
def shifts(t):
    prev=np.zeros(3)
    for mm in MEET:
        if t<mm['t']:break
        if t<mm['t']+.03:return np.array(mm['antes'])+(np.array(mm['despues'])-mm['antes'])*(t-mm['t'])/.03
        prev=np.array(mm['despues'])
    return prev
for e in E['guitarra']:
    box=int(e.get('caja',0));shift=shifts(e['t']);h=e.get('parcial',1) if e['articulacion']=='armonico' else 1
    # Las promesas ya llevan su desviación escrita; los demás la reciben aquí.
    if not e['frase'].startswith('promesa-'):e['midi']+=shift[box]/100
    e['hz']=hz(e['midi']);e['afinaciones_cajas_cents']=shift.tolist()
    e['parametros_motor']={'cuerda':int(e.get('cuerda',0)),'caja':box,'midi':e['midi']-shift[box]/100-12*math.log2(h),
        'vel':e['vel'],'gesto':e['articulacion'] if e['articulacion'] in ['armonico','madera','apagar'] else 'pua',
        'nodo':e.get('nodo',.17),'parcial':h}

P['cortes_buses']=[dict(t=a,fin=b,accion='salida cero con rampa .012; el estado no se borra',destino='todos los buses',rampa_s=.012)
                   for a,b in P['oscuridades']+HOLES+[[C0-.035,C0+.15],[STOP-.035,STOP+.02]]]
cuts=[(c['t'],c['fin']) for c in P['cortes_buses']]
# Clipping sólo de salida. Mantener un único acontecimiento y enumerar segmentos visibles.
for k,events in E.items():
    result=[]
    for e in events:
        segments=[(e['t'],e['t']+e['dur'])]
        for a,b in cuts:
            rr=[]
            for u,v in segments:
                if v<=a or u>=b:rr.append((u,v))
                else:
                    if u<a:rr.append((u,a))
                    if v>b:rr.append((b,v))
            segments=rr
        e['salidas']=[[round(a,8),round(b,8)] for a,b in segments if b-a>.008]
        # Mantener eventos internos bajo mute permite heredar estados sin fingir reataques.
        result.append(e)
    E[k]=sorted(result,key=lambda e:(e['t'],e['id']))
note('junco4',STOP+.21,float(src[-1]),4.3,.13,'última llegada; sin restaurar la fuente',last_ids[-1],'coda',
     masa=float(plans[-1]['b'][-1]),fase_inicial_rad=float(phase[-1]),salidas=[[STOP+.21,STOP+4.51]])
note('waterphone',STOP+1.37,59.01955+24,6.1,.12,'residuo del tercer parcial',return_c['id'],'coda',salidas=[[STOP+1.37,STOP+7.47]])
for evs in E.values():evs.sort(key=lambda e:(e['t'],e['id']))
P['secciones'][4]['nombre']='Pantano / una respuesta cambia de cuerpo'
P['secciones'][4]['accion']='contacto, umbral, transferencia y esperas calculadas; sin pulso'
P['secciones'][5]['accion']='reunión gradual desde un solo relevo; solos derivados del centro'
P['secciones'][7]['accion']='resonancia compartida / contagio de ataques / casi continuidad'
P['reglas']['filiacion']='ancestro sólo para transformaciones declaradas; acompañamiento y frases originales pueden no tenerlo'
P['reglas']['fase']='fases de llegada heredadas; salidas lista ventanas audibles; los cortes no reexcitan'
P['reglas']['centro']='sin pulso; contacto y umbral determinan un relevo; oscuridades calculadas a partir de las pausas escritas'
P['interpretacion']['nuevos']['guitarra']='modelos_memoria.py / GuitarraMemoria; afinaciones de encuentros, contacto sostenido y parámetros por evento'
P['interpretacion']['nuevos']['junco']='modelos_memoria.py / plan_memoria + instrumentos.Junco; fases por arista, estados y masas heredados'
P['interpretacion']['inyeccion_cuerda']='variante motores-memoria.py; z complejo por modo sustituye excitación prefijada en cuerda-recibe'
P['interpretacion']['salida']='salidas enumera ventanas de cada evento; estado evoluciona también durante corte; rampas .012 s y buses cerrados'
P['interpretacion']['campos_de_partitura_que_exigen_adaptador']=['lectura de contacto continuo','captaciones de guitarra','aristas persistentes de junco','mutes después de efectos','guías vocales/vocoders']
P['analisis_datos']={'paquete':'datos/paquete-modal.json','encuentros':'datos/encuentros.json','planes':'datos/transportes-memoria.json',
                    'contagios':contagios,'telefono_apagado_s':phone_end,'espera_aprendida_s':learned}
js('datos/encuentros.json',MEET);js('datos/transportes-memoria.json',plans);js('partitura-v5.json',P)
js('datos/modelos-comprobados.json',comprobar());stage(4,'Reunión / partitura reescrita',P)

# Variante efectiva de la cuerda: inyección del paquete complejo en modos 1/2/3/5.
motor=(OLD/'fuentes/motores-arpa-afinable.py').read_text('utf8')
needle="state[v]+=amp/(np.arange(1,H+1)**1.3); done.add(j)"
assert motor.count(needle)==1
motor=motor.replace(needle,"""if 'inyeccion_modal' in e:
                    packet=e['inyeccion_modal']; vals=np.array([complex(re,im) for re,im in packet['z']])
                    for hmode,value in zip(packet['modos'],vals): state[v,hmode-1]+=value
                else: state[v]+=amp/(np.arange(1,H+1)**1.3)
                done.add(j)""")
compile(motor,'motores-memoria.py','exec');put('fuentes/motores-memoria.py',motor.encode('utf8'))
for f in ['reescribir.py','modelos_memoria.py','instrumentos.py']:put('fuentes/'+f,(ROOT/f).read_bytes())
for f in ['COMPOSITOR.md','LECTURA-POEMARIO-PANTANO-2026-10-22.md','MATEMATICAS-PARA-COMPONER-2026-10-22.md']:
    put('fuentes/'+f,(ROOT.parent/f).read_bytes())
put('fuentes/CRITICA-ANTERIOR.md',(ROOT/'CRITICA-COMPOSITIVA-2026-10-22.md').read_bytes())
with (ROOT/'REVISION-EN-CURSO.txt').open('x',encoding='utf8') as f:f.write(OUT.name+'\n')
print(json.dumps({'out':str(OUT),'eventos':sum(map(len,E.values())),'centro_eventos':len(center_events),
    'silencios':len(P['oscuridades']),'planes':len(plans),'espera_aprendida_s':learned,'normas':PACKET['normas'],
    'planes_con_costo_familia_efectivo':sum(p['cambio_pi_sin_familias']>1e-9 for p in plans)},ensure_ascii=False))
