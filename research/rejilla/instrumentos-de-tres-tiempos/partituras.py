"""Partituras de prueba y una escena original: La boca abre una estación."""
from copy import deepcopy
from motores import NOMBRES

SEMILLA=19103419
def nota(t,m,d,v=.75,p=0,**kw):return dict(t=t,midi=m,dur=d,vel=v,pan=p,**kw)
def frase(start,pitches,durations,gap=.10,vel=.78,pan=0):
    out=[]; t=start
    for i,(m,d) in enumerate(zip(pitches,durations)):
        out.append(nota(round(t,5),m,d,vel*(.94 if i%3 else 1),pan)); t+=d+gap
    return out

def demo(k):
    d=24.; s={'notas':[],'controles':{}}
    if k=='boca':
        s['notas']=frase(.4,[57,60,62],[1.1,.65,1.7])+frase(4.6,[64,62,59],[2.9,.8,1.35],.18)
        s['notas']+=frase(10.8,[57,64,67,65,62],[1.6,.45,.7,1.2,2.1],.12)
        s['notas']+=frase(18.0,[60,59,57],[.65,1.1,2.6],.22)
        s['vocales']=[[0,'a'],[1.5,'i'],[3.4,'a'],[4.6,'a'],[10.5,'u'],[13.0,'e'],[17,'i'],[18,'a'],[20,'i'],[21.5,'u'],[24,'u']]
        s['consonantes']=[[.38,'m',.8],[1.6,'t',.6],[2.38,'k',.7],[5.5,'s',.8],[6.8,'t',.5],[8.3,'k',.7],[11.2,'t',.5],[11.85,'k',.65],[12.7,'s',.8],[14.6,'t',.55],[16.0,'k',.6],[18.0,'m',.8],[18.9,'t',.5],[20.2,'m',.7]]
        s['controles']={'vibrato':[[0,.12],[5,.4],[10,.25],[16,.7],[24,.18]]}
        s['secciones']=[[0,'Juntos'],[4.6,'La vocal tarda'],[10.8,'Tres recorridos'],[18,'Reunión']]
    elif k=='cuerda':
        s['base_midi']=50; s['notas']=[nota(.3,50,.4,.9),nota(8,57,.5,.65),nota(16,53,.4,.8),nota(20,50,.3,.6)]
        s['controles']={'presion':[[0,.05],[4,.25],[9,.9],[14,.45],[19,.8],[24,0]],'arco':[[0,0],[3,0],[6,.9],[12,.75],[15,0],[19,.45],[22,0]]}
    elif k=='arpa':
        s['cuerdas_midi']=[50,57,60,64,69]; s['notas']=[nota(.3,50,.3,.95,cuerda=0),nota(12,60,.3,.65,cuerda=2)]
        s['enlaces']=[[2,0,1,1.25],[4,1,2,1.35],[6,2,3,1.25],[8,3,4,1.2],[10,4,0,1.0],[14,2,4,1.4],[17,4,1,1.2],[19,1,0,1.3]]
    elif k=='organo':
        s['notas']=[nota(.3,86,22,.9,ataque=.25,soltar=.9)]
        s['controles']={'presion':[[0,0],[2,.1],[9,.98],[11,.5],[13,.5],[18,.08],[20,.50],[22,.50],[24,0]]}
    elif k=='sala':
        s['notas']=[nota(.5,57,.4,.8),nota(6,57,.4,.8),nota(11.5,57,.4,.8)]
        s['notas']+=frase(15,[57,64,60,69],[.45,.5,.7,.4],.55,.6)
        s['controles']={'pliegue_0':[[0,0],[5,0],[6,.7],[10,.7],[12,.15],[16,.9],[24,.2]],'pliegue_1':[[0,.2],[5,.2],[6,.9],[10,.9],[12,.1],[20,.8],[24,.1]]}
    else:
        pitches=[57,64,60,67,65,62,60,59,57]
        if k in ('piano','cristal','terminal'):pitches=[m+12 for m in pitches]
        if k=='androide':pitches=[m-12 for m in pitches]
        if k=='fotones':
            s['notas']=[nota(.35+j*.62,[43,55,67,79,48,72][j%6],.48,[.85,.5,.75,.55][j%4],[-.45,.3,0][j%3]) for j in range(12)]
            s['notas'] += [nota(11+j*.375,[43,62,55,74][j%4],.4,.8 if j%4==0 else .45,(-.4 if j%2 else .4)) for j in range(24)]
        elif k=='estacion':
            for t,chord in [(0,[50,57,60,64]),(7,[53,60,64,69]),(14,[55,62,65,69]),(19,[50,57,60,64])]:
                s['notas'] += [nota(t,m,6 if t<19 else 4,.55,-.65+i*.43) for i,m in enumerate(chord)]
        else:
            s['notas']=frase(.4,pitches[:4],[1.6,.8,1.15,2.2],.3,.65)+frase(9,pitches[4:],[.6,1.2,.7,1.8,2.7],.18,.88)
            s['notas']+=frase(19,pitches[1:4],[.4,.65,2.2],.18,.55)
        if k=='terminal':s['controles']={'vector_x':[[0,0],[6,1],[12,1],[18,0],[24,.5]],'vector_y':[[0,0],[6,0],[12,1],[18,1],[24,.4]]}
    if 'secciones' not in s:s['secciones']=[[0,'Gesto expuesto'],[10,'Desarrollo'],[19,'Salida']]
    return {'id':k,'nombre':NOMBRES[k],'duracion':d,'semilla':SEMILLA+list(NOMBRES).index(k),'partitura':s}

def escena():
    """84 s, cuatro escenas; voz con frases de tamaños y articulaciones distintos."""
    duration=84.; p={k:{'notas':[],'controles':{}} for k in NOMBRES}
    voice=p['boca']; voice['notas']=frase(1.2,[57,60,62,64],[1.25,.75,.55,2.4],.15,.82)
    voice['notas']+=frase(8.8,[65,64,60],[.6,1.4,2.1],.23,.76)
    voice['notas']+=frase(16.3,[59,60,57],[.45,.8,2.8],.12,.8)
    voice['notas']+=frase(45.7,[64,67,69,65,64,62],[.8,.45,1.4,.7,.5,1.9],.10,.8)
    voice['notas']+=frase(55.4,[60,64,62,59],[1.8,.65,1.1,2.5],.16,.82)
    voice['notas']+=frase(66,[57,60,65,64,62],[.7,.45,1.9,.6,1.5],.20,.8)
    voice['notas']+=frase(75,[60,59,57],[.8,1.4,3.2],.23,.7)
    voice['vocales']=[[0,'a'],[4,'a'],[6.3,'i'],[9,'e'],[13,'u'],[16,'o'],[20,'a'],[24,'u'],[45,'a'],[49,'i'],[52,'u'],[55,'e'],[60,'a'],[64,'o'],[66,'a'],[70,'u'],[74,'i'],[76,'a'],[79,'u'],[84,'u']]
    voice['consonantes']=[[t,ph,v] for t,ph,v in [(1.15,'m',.8),(3.6,'t',.6),(5.1,'s',.6),(8.8,'k',.65),(11,'s',.7),(16.3,'m',.8),(17.8,'t',.5),(45.6,'m',.8),(47.2,'t',.6),(49.8,'k',.5),(51.4,'s',.7),(55.3,'m',.7),(58.1,'t',.55),(60.2,'k',.5),(66,'m',.8),(68.8,'s',.6),(71,'t',.5),(75,'m',.7),(77.9,'m',.7)]]
    voice['controles']={'vibrato':[[0,.2],[20,.4],[40,.15],[58,.6],[70,.3],[84,.15]]}
    # Short answers inhabit the gaps, rather than copying the lead.
    for start,ms in [(6.8,[81,76,72]),(13.3,[77,76]),(20.5,[72,76,69]),(53,[79,76]),(63,[74,72,71]),(73,[76,72])]:
        p['cristal']['notas']+=frase(start,ms,[.24,.35,.85][:len(ms)],.14,.55,-.25)
    harmony=[(0,9,[50,57,60,64]),(9,7,[53,60,64,69]),(16,6,[55,59,62,65]),(46,8,[50,57,60,64]),(54,8,[53,60,64,69]),(66,8,[55,59,62,65]),(75,7,[50,57,60,64])]
    for t,d,ch in harmony:
        p['estacion']['notas'] += [nota(t,m,d,.42,-.75+i*.5) for i,m in enumerate(ch)]
    p['cuerda']={'base_midi':50,'notas':[nota(22,50,.3,.9),nota(27,57,.3,.8),nota(31,60,.3,.7),nota(36.5,53,.3,.85),nota(40,50,.3,.55)],'controles':{'arco':[[0,0],[23,0],[26,.9],[32,.7],[36,.3],[40,0],[84,0]],'presion':[[0,0],[22,.1],[28,.8],[35,.4],[40,.6],[45,0],[84,0]]}}
    p['arpa']={'cuerdas_midi':[50,57,60,64,69],'notas':[nota(23,50,.3,.9,cuerda=0),nota(32,60,.3,.7,cuerda=2),nota(72.5,50,.3,.7,cuerda=0)],'enlaces':[[25,0,1,1.25],[27,1,3,1.1],[29,3,4,1.3],[34,2,4,1.1],[37,4,1,1.25],[40,1,0,1.2],[74,0,2,1.2],[76,2,3,1.2],[79,3,0,1.0]],'controles':{}}
    p['piano']['notas']=frase(24,[69,72,76,74],[1,.5,1.3,2.1],.4,.7,.25)+frase(35,[72,71,69],[.8,1.3,2.4],.2,.65,.35)
    p['organo']['notas']=[nota(20.5,86,22.5,.7,ataque=.6,soltar=1.2),nota(63.5,86,17.5,.65,ataque=.6,soltar=1.2)]
    p['organo']['controles']={'presion':[[0,0],[20,0],[23,.15],[31,.9],[38,.5],[44,0],[63,0],[67,.8],[74,.45],[78,.5],[83,0]]}
    for t,m in [(21,50),(29,60),(34,57),(40,50),(64,62),(72,50),(79,50)]:p['sala']['notas'].append(nota(t,m,.35,.7))
    p['sala']['controles']={'pliegue_0':[[0,.1],[24,.1],[35,.8],[44,.2],[64,.8],[84,.1]],'pliegue_1':[[0,.8],[24,.8],[35,.1],[44,.7],[72,.1],[84,.6]]}
    p['terminal']['notas']=frase(41,[69,72,76],[.4,.6,1.8],.22,.75,-.2)+frase(61.8,[77,76,72],[.35,.5,1.4],.18,.65,.3)
    p['terminal']['controles']={'vector_x':[[0,0],[40,0],[45,1],[62,.3],[66,.9],[84,0]],'vector_y':[[0,.8],[40,.8],[45,.2],[62,.1],[66,.8],[84,.5]]}
    p['plasma']['notas']=frase(42.5,[69,72,76],[.3,.4,1.0],.1,.55,.25)+frase(52.8,[77,76,72],[.2,.25,.55],.1,.6,.3)
    p['plasma']['notas']+=frase(62.5,[74,76,79,77,76],[.2,.35,.4,.28,.8],.08,.6,.15)
    p['androide']['notas']=[]
    for bar in range(10):
        base=38 if bar<4 or bar>=8 else 41 if bar<6 else 43; t=44+bar*2.75
        p['androide']['notas'] += [nota(t,base,.72,.8),nota(t+1.45,base+7,.32,.55),nota(t+2.1,base+12,.36,.65)]
    for j in range(80):
        t=44+j*.34375
        if j%8 in (0,3,4,6):p['fotones']['notas'].append(nota(t,[43,74,55,67][(j%8)//2],.3,.7 if j%8==0 else .4,-.35 if j%2 else .35))
    p['fotones']['notas'] += [nota(72,43,.45,.9),nota(73,67,.3,.45),nota(74.2,55,.5,.5)]
    return {'titulo':'La boca abre una estación','duracion':duration,'semilla':SEMILLA,'pistas':p,
        'secciones':[[0,'I · boca y cristal'],[22,'II · cuerpos que se prestan'],[44,'III · estación eléctrica'],[72,'IV · volver a una boca']],
        'ganancias':{'boca':.92,'cuerda':.70,'piano':.45,'arpa':.8,'organo':.22,'sala':.6,'cristal':.55,'estacion':.33,'terminal':.55,'plasma':.40,'androide':.70,'fotones':.55}}
