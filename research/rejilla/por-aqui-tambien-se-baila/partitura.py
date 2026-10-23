"""Partitura completa de eventos, todavía sin render de canción.
La unidad común es el pulso: dos compases 4/4 = ciclo de ocho pulsos 4+2+2.
El tráfico altera frases locales y silencios; no aplica varispeed global.
"""
from comun import *
from laminas import *
NOMBRES=['acordeon-tema','acordeon-respuesta','bajo-cumbia','guiro','conga','campana','timbal','bombo','caja','membrana-din','membrana-ta','membrana-thom','barro','pandero','boca-ritmica','laser-directo','laser-laberinto','laser-talbot','raspador','mbira-boca','guembri-drone','organo-drone','clarinete','chelo','vibrafono','voz-verso','voz-respuesta','radio-chofer','radio-pasajera','estatica-senal']
SECCIONES=[('I','La terminal todavía no existe',0,8),('II','Una bolsa llena de estaciones',8,20),('III','Por aquí también se baila',20,28),('IV','Tres puertas para el mismo pulso',28,40),('V','El semáforo cobra dos veces',40,52),('VI','Solo D: el láser hace transbordo',52,68),('VII','La salida se cambió de lado',68,80),('VIII','Contar para volver a encontrarse',80,88),('IX','Bajar en el otro reloj',88,96)]
THEME=[[(0,62,.5),(.75,65,.5),(1.5,69,.75),(3,67,.75)],[(.5,65,.5),(1.25,64,.5),(2,62,1.5)],[(0,62,.5),(1,65,.5),(2,69,.75),(3.25,72,.5)],[(.5,71,.5),(1.5,69,.75),(3,67,.75)],[(0,65,.5),(.75,69,.75),(2.25,67,.5),(3.25,64,.5)],[(.5,65,.5),(1.5,64,.5),(2.5,62,1.25)],[(0,60,.75),(1,62,.5),(2.25,64,.5),(3.25,65,.5)],[(0,64,.75),(1,61,.75),(2.5,62,1.25)]]
def mora(sub):
 M=2*sub;gap=sub;pat=[0,1,2,M//2,M-2,M-1];starts=[0,M+gap,2*(M+gap)];events=[s+x for s in starts for x in sorted(set(pat))];assert 3*M+2*gap==8*sub
 return {'subdivision':sub,'M':M,'silencio':gap,'total_unidades':8*sub,'inicios':starts,'golpes':events,'aterrizaje_pulsos':8,'nota':'remate triplicado propio, no transcripción de una korvai tradicional'}
def componer():
 out=ultimo();S=leer(depo());TR=leer(out/'trafico.json');VV=np.array(TR['v']);ev={c:[] for c in NOMBRES};trace=[];lyrics=[];cues=[]
 def add(c,b,off=0,m=62,d=.5,v=.6,**kw):
  beat=b*4+off;e={'pulso':round(float(beat),6),'t':round(float(beat*Q),6),'dur_pulsos':float(d),'dur':float(d*Q),'midi':float(m),'vel':float(v),**kw};ev[c].append(e);return e
 def estado(t):return min(19,int(t/(96*BAR)*20))
 def vehicle(t,k):return float(VV[min(len(VV)-1,max(0,round(t/TR['paso_guardado']))),k])
 clocks={}
 def local(c,b,off,m,d,v=.6,driver=0,**kw):
  nominal=b*4+off;t=nominal*Q;speed=vehicle(t,driver);st=estado(t);path=S['caminos'][min(len(S['caminos'])-1,st*16)];route=int(path[-1]);cycle=int(nominal//8)*8;key=(cycle,driver)
  if key not in clocks:
   ts=np.linspace(cycle*Q,(cycle+8)*Q,101);vs=np.array([vehicle(x,driver) for x in ts]);rate=np.where(vs<.8,0,vs);phase=np.r_[0,np.cumsum((rate[:-1]+rate[1:])*.5*np.diff(ts))];clocks[key]=(ts,phase,vs)
  ts,phase,vs=clocks[key]
  if phase[-1]<.3 or speed<.8 and (c in ['acordeon-tema','clarinete'] or c.startswith('laser')):
   trace.append({'capa':c,'pulso_nominal':b*4+off,'suprimido':True,'v':speed,'vehiculo':driver,'estado':st,'motivo':'detención local; el pulso y el drone continúan'});return
  target=(nominal-cycle)/8*phase[-1];eff=float(np.interp(target,phase,ts)/Q);end=float(np.interp(min(1,(nominal-cycle+d)/8)*phase[-1],phase,ts)/Q);duration=max(.12,min(2,end-eff));e=add(c,0,eff,m,duration,v,**kw,vehiculo=driver,velocidad_m_s=speed,estado_deposito=st,ramal=route,retardo_pulsos=eff-nominal);trace.append({'capa':c,'pulso_nominal':nominal,'pulso_efectivo':e['pulso'],'suprimido':False,'v':speed,'estado':st,'ramal':route,'regla':'fase integrada de velocidad; cierre musical común de ocho pulsos'})
 # Tema completo: cada retorno altera el final y distribuye la respuesta del mismo material.
 for start in [4,12,20,28,36,44,68,76,88]:
  for k,notes in enumerate(THEME):
   if start+k>=96:continue
   for j,(at,m,d) in enumerate(notes):
    if start>=68 and k>=6:m+=2 if j==0 else 0
    c='laser-directo' if start in [28,36] and j%2 else 'acordeon-tema'
    if start>=88:c='clarinete'
    local(c,start+k,at,m,d,.64,driver=(k%3)*11,frase='tema-regreso' if start>=68 else 'tema-A',articulacion='piu' if c.startswith('laser') else 'ligado-corto')
    if k%2 and start<88:local('acordeon-respuesta',start+k,at+.25,m-12,d*.65,.4,driver=22,frase='eco-del-tema')
 # Armonía: un pedal D/A, cambios de color en ocho compases; C# sólo en la cadencia.
 colors=[('Dm9',[50,57,60,64,65]),('Dm9',[50,57,60,64,65]),('G6/D',[50,55,59,64]),('G6/D',[50,55,59,64]),('Bbmaj7/D',[50,58,62,65,69]),('Bbmaj7/D',[50,58,62,65,69]),('A7sus',[45,55,62,64]),('A7',[45,55,61,64])]
 harmonic=[]
 for b in range(96):
  name,ch=colors[b%8];harmonic.append({'compas':b+1,'acorde':name,'notas':ch})
  if 8<=b<28 or 40<=b<52 or 68<=b<88:
   root=38 if b%8<6 else 33
   for at,step in [(0,0),(1.5,7),(2.5,12),(3.5,7)]:add('bajo-cumbia',b,at,root+step,.42,.72,funcion='ancla métrica; no varispeed')
   for at in [.5,1.5,2.5,3.5]:
    for m in ch[2:4]:add('acordeon-respuesta',b,at,m+12,.32,.28,frase='contratiempo')
   for at in np.arange(0,4,.5):add('guiro',b,float(at),60,.22,.35,gesto='raspado corto')
   for at in [0,1.5,2.5,3.5]:add('conga',b,at,60,.25,.5)
   for at in [0,2,3.25]:add('campana',b,at,76,.2,.3)
   for at in [0,2]:add('bombo',b,at,36,.22,.65)
   for at in [1,3]:add('caja',b,at,38,.16,.4)
   if b%4==3:
    for j,at in enumerate([2.5,2.75,3,3.5,3.75]):add('timbal',b,at,62+j,.12,.45)
  if b%8==0:
   for m in [38,45]:add('organo-drone',b,0,m,32,.32,funcion='bordón; conserva reloj durante detenciones')
  if b%2==0 and b<88:
   for at,step in [(0,0),(1.5,7),(3.25,0),(4.5,10),(6,7)]:add('guembri-drone',b,at,38+step,.65,.42,frase='ostinato de cinco ataques en ocho pulsos')
  if b in [0,8,20,40,68,88]:add('chelo',b,0,50 if b!=40 else 57,8,.35,articulacion='arco lento')
  if b%8==6 and b<88:
   for j,m in enumerate([69,65,64,62]):add('vibrafono',b,.5+j*.75,m,.5,.35)
 # Ciclos de ocho: agrupación 4+2+2 explícita, subdivisiones 4,3,5 por episodios.
 cycles=[]
 for b in range(8,88,2):
  sub=3 if 28<=b<40 else 5 if 52<=b<60 else 4;ending=b%8==6 or b in [50,66,86];R=mora(sub);cycles.append({'compas':b+1,'pulso':b*4,'t':b*BAR,'sub':sub,'angas':[4,2,2],'mora':ending})
  hits=R['golpes'] if ending else [i for i in range(8*sub) if i%sub in [0,sub-1] or (i//sub)%3==2 and i%sub==1]
  for k,tick in enumerate(hits):
   off=tick/sub;c=['membrana-din','membrana-ta','membrana-thom'][k%3];add(c,b,off,50 if c!='membrana-thom' else 38,.7 if c.endswith('din') else .2,.55,sub=sub,solkattu=['din','ta','thom'][k%3],ciclo_8=b//2,remate=ending)
   if ending and k%2==0:add('boca-ritmica',b,off,50,.18,.45,vocal='a' if k%4 else 'u',consonante='t' if k%4 else 'k',sub=sub)
   elif k%4==1:add('pandero',b,off,60,.1,.3,sub=sub)
   elif k%5==2:add('barro',b,off,67,.12,.32,sub=sub)
  if ending:add('membrana-din',b+2,0,50,.9,.82,sub=sub,llegada=True)
 # Distribución del depósito: la misma célula deriva a otras voces, con memoria de camino.
 routing=[]
 for b in range(16,88,2):
  st=estado(b*BAR);path=np.array(S['caminos'][st*16]);route=path[::3].tolist();onsets=[0,.75,1.5,3,4.5,5.5,6.75,7.5];ks=[62,65,69,67,65,64,60,62]
  for j,(at,m) in enumerate(zip(onsets,ks)):
   r=int(route[j%len(route)]);c=['barro','pandero','mbira-boca'][r%3];add(c,b,at,m,.2,.4,ramal=r,estado_deposito=st,funcion='célula del tema repartida por depósito')
  routing.append({'compas':b+1,'estado':st,'ramales':route})
 # Solo raro: A-D; D conserva alturas del tema y transforma red/espacio, no sólo un efecto.
 solo=[]
 for k,b in enumerate(range(52,68,2)):
  st=estado(b*BAR);seq=[(0,62,.5),(.75,65,.5),(1.5,69,1),(3,67,.75),(4.5,65,.5),(5.5,64,.5),(6.75,61 if k%2 else 60,.5),(7.5,62,.4)]
  for j,(at,m,d) in enumerate(seq):
   c='laser-directo' if k<2 else 'laser-laberinto' if k<5 else 'laser-talbot';local(c,b,at,m+12 if j in [2,3] and k>=4 else m,d,.68,driver=(k%3)*11,frase='solo-D',tau='0' if k<2 else '1/3' if k<5 else '2/5')
  add('raspador',b,1,62,6,.55,estado_deposito=st,lectura='perfil acumulado, entrada a salida')
  solo.append({'compas':b+1,'estado':st,'accion':['presentar cabeza','responder con pausa','abrir cruce','repetir con depósito','atascar y respirar','abrir Talbot 1/3','cruzar a 2/5','cadenciar en D'][k]})
 # Presencias respiradas: responden al contorno del tema sin duplicarlo todo el tiempo.
 for b in [2,10,18,30,34,42,46,70,74,82,90]:
  for j,m in enumerate([62,65,64,57]):local('clarinete',b,.5+j*1.5,m,.9,.4,driver=11,frase='contrasujeto-respirado')
 # Texto original. Ritmos y longitudes distintos por función, sin cuota de ausencia humana.
 texts=[(8,'subí con una bolsa llena de estaciones','su bí con u na bol sa lle na de es ta cio nes','verso'),(12,'la señora del fondo cargaba el último puente','la se ño ra del fon do car ga ba el úl ti mo puen te','verso'),(16,'el chofer cobró dos veces al mismo semáforo','el cho fer co bró dos ve ces al mis mo se má fo ro','verso'),(20,'por aquí también se baila','por a quí tam bién se bai la','coro'),(22,'por aquí también se baila','por a quí tam bién se bai la','coro'),(24,'si no pasa la salida que nos pase la voz','si no pa sa la sa li da que nos pa se la voz','respuesta'),(68,'ahora el puente viaja adentro de la bolsa','a ho ra el puen te via ja a den tro de la bol sa','verso'),(72,'por aquí también se baila','por a quí tam bién se bai la','coro'),(74,'aunque se movió el camino','aun que se mo vió el ca mi no','coro'),(76,'bajé del mismo lado pero del otro reloj','ba jé del mis mo la do pe ro del o tro re loj','respuesta'),(88,'guarda el cambio todavía falta un puente','guar da el cam bio to da ví a fal ta un puen te','coda')]
 for b,tx,sy,kind in texts:
  syll=sy.split();pattern=[.5,.5,.75,.25] if kind=='verso' else [.5,.5,1,.5,.5,1,.5,1.5];pos=.5;line=[]
  for j,s in enumerate(syll):
   d=pattern[j%len(pattern)] if j<len(syll)-1 else 1.5;m=[62,65,64,62,60,62,65,69][j%8] if kind=='verso' else [62,65,69,67,65,64,61,62][j%8];c='voz-respuesta' if kind=='respuesta' else 'voz-verso';e=add(c,b,pos,m,d*.85,.7,texto=s,frase=kind);line.append(e);pos+=d
  lyrics.append({'compas':b+1,'t':b*BAR,'texto':tx,'funcion':kind,'fin_pulsos':b*4+pos})
 radios=[(0,'chofer','Buenas noches. La ruta veintidós sale de la hoja. Guarde su cambio.'),(3,'pasajera','Traigo un puente en la bolsa. ¿Aquí lo puedo transbordar?'),(40,'chofer','Avance hasta el fondo. El fondo acaba de cambiar de calle.'),(46,'pasajera','Llevamos tres semáforos parados y la radio ya llegó.'),(80,'chofer','Cuatro puertas, dos vueltas, dos golpes. Nos vemos en el uno.'),(92,'pasajera','Próxima parada: el ruido que queda entre dos casas.')]
 for b,who,tx in radios:
  c='radio-'+who;words=tx.split();dur=min(12,len(words)*.45);add(c,b,0,50 if who=='chofer' else 57,dur/Q,.65,texto=tx,modo='hablado',ficcion='anuncios imaginarios, no información de transporte real');cues.append({'compas':b+1,'t':b*BAR,'voz':who,'texto':tx,'dur_estim_s':dur});add('estatica-senal',b,0,60,dur/Q+.5,.3,dial='buscar estación y aterrizar en la voz')
 for c in ev:ev[c].sort(key=lambda e:e['pulso'])
 assert all(ev.values()) and len(ev)==30
 return {'titulo':'Por aquí también se baila','subtitulo':'Laberinto de rutas, depósitos y detente-acelera','version':VERSION,'semilla':SEED,'BPM':BPM,'negra':Q,'compas':BAR,'duracion_prevista':96*BAR+6,'estado':'PARTITURA PARA REVISIÓN; no máster ni video','terreno':'Traspuesta 22, Mesa y Abanico del Alcor','secciones':[{'id':i,'nombre':n,'compas_inicio':a+1,'compas_fin':b,'t':a*BAR,'t1':b*BAR} for i,n,a,b in SECCIONES],'tema_A':THEME,'armonia':harmonic,'eventos':ev,'ciclos':cycles,'moras':[mora(s) for s in [4,3,5]],'traza_trafico':trace,'ruteo':routing,'solo_D':solo,'letra':lyrics,'radio':cues,'eleccion_solo':{'A':'requinto virtuoso: descartado por Canek','B':'pius sin desarrollo: insuficiente','C':'célula en Talbot: cambia patrón pero no escucha el laberinto','D':'láser de transbordos: tema, Talbot, red de cruces y tráfico, con regreso alterado'},'limites':['subdivisiones y remates propios inspirados en recursos carnáticos, no interpretación tradicional certificada','no se afirma caos determinista del tráfico','modelo aluvial reducido de masa conservada; rutas de transporte artísticas','timbres existentes no se renderizaron completos en esta etapa']}
def main():
 out=ultimo();P=componer();rev=(out/'partitura.json').exists();r=1
 while (out/('partitura.json' if r==1 else f'partitura-r{r}.json')).exists():r+=1
 file='partitura.json' if r==1 else f'partitura-r{r}.json';jsave(out/file,P)
 (out/'PARTITURA.txt').write_bytes(file.encode())
 tag=out.name.split('-')[-1];f,ax=figura('La canción conserva el pulso; las rutas no','96 compases previstos · treinta capas · solos sin requinto · parada antes del máster')
 for j,(c,events) in enumerate(P['eventos'].items()):
  for e in events:ax[0].plot([e['t'],e['t']+min(4,e['dur'])],[j,j],color=['#1d2869','#732605','#638179'][j//10],lw=1)
 ax[0].set_yticks(range(30),NOMBRES,fontsize=6);ax[0].set_xlim(0,P['duracion_prevista']);ax[0].set_xlabel('segundos de partitura');cap='04'+('' if r==1 else chr(96+r));salva(f,out/'proceso'/f'{cap}-partitura-y-relevos-s{SEED}-{tag}.png');print(len(P['eventos']),sum(map(len,P['eventos'].values())),len(P['traza_trafico']))
if __name__=='__main__':main()
