"""Treinta funciones: medio tiempo pesado, pulgares y retorno con residuo."""
from comun import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
def figura(title,sub='',n=1):
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'text.color':'#e4e3ee','axes.labelcolor':'#e4e3ee','xtick.color':'#bab8ce','ytick.color':'#bab8ce','axes.facecolor':'#090b19','figure.facecolor':'#090b19','savefig.facecolor':'#090b19'})
 f,a=plt.subplots(1,n,figsize=(12,6.3),squeeze=False);f.subplots_adjust(top=.79,bottom=.13,left=.13,right=.96,wspace=.3);f.text(.06,.93,title,fontsize=23);f.text(.06,.86,sub,color='#b4a2ff');return f,a[0]
def salva(f,p):
 b=io.BytesIO();f.savefig(b,format='png',dpi=100);plt.close(f);guardar(p,b.getvalue())
def main():
 out=ultimo();tag=out.name.split('-')[-1];E=leer(out/'eco.json')
 f,ax=figura('El flujo intenta volver','Mismo estado inicial y reloj físico · inversión de velocidad · estados sin normalizar',2)
 for name,col in [('ideal','#c0b0ff'),('viscoso','#ff9769')]:
  trace=E[name]['traza'];ax[0].plot([e['t']+(8 if e['fase']=='vuelta' else 0) for e in trace],[e['energy'] for e in trace],color=col,label=name)
 ax[0].legend();ax[0].set_xlabel('segundos físicos');ax[0].set_ylabel('energía del modelo')
 a=np.array(E['ideal']['retornado']);b=np.array(E['viscoso']['retornado']);ax[1].plot(a,color='#c0b0ff',lw=.7);ax[1].plot(b-a,color='#ff9769',lw=.7);ax[1].set_xlabel('componente de Fourier');ax[1].set_title('Estado ideal y diferencia retornada')
 salva(f,out/'proceso'/f'02-eco-y-residuo-s{SEED}-{tag}.png')
 names=['sub','808-cuerpo','falcon','mandibula','residuo-grave','organo-roto','kick','caja','clap','hats','hats-tresillos','perc-frita','dundun','mbira','kalimba','arpa-boca','mbira-vocal','kalimba-vocal','solista-grave','doble-grave','voz-residual','chops-graves','coro-oscuro','boca-percusiva','flujo-ideal','flujo-viscoso','residuo','eco-captador','chelo','contrabajo']
 Q=60/140;B=4*Q;S=Q/4;D=128*B+4
 secs=[('I','Algo pesa bajo el agua',0,8),('II','Tu nombre por debajo',8,32),('III','Primer peso',32,48),('IV','Los dedos contestan',48,64),('V','Desandar la corriente',64,88),('VI','Lo que vuelve pesa más',88,120),('VII','El nombre que quedó',120,128)]
 P={'titulo':'La corriente devuelve tu nombre','semilla':SEED,'sr':SR,'bpm':140,'pulso_escuchado_bpm':70,'negra':Q,'compas':B,'duracion':D,'tonica':'F# menor','tonica_sub_Hz':float(hz(30)),'instrumentos':lib().name,'secciones':[{'id':i,'nombre':n,'t':a*B,'t1':b*B,'compases':[a,b]} for i,n,a,b in secs],'eventos':{n:[] for n in names},'sabina':[],'letra':[],'eco_musical':{'fin_ida':64*B,'fin_vuelta':88*B,'T_fisico_por_tramo':8,'nota':'ida musical más lenta; ambos flujos usan el mismo reloj físico; después del retorno se conserva el residuo y se cambia la captación'},'sujeto':{'semitonos':[0,0,3,2,-2,0],'semicorcheas':[3,1,2,3,1,6]},'solo_D':'comparación de estados efectivos viscoso menos ideal, sin igualar amplitudes antes de restar; la coda conserva ese material'}
 ev=P['eventos'];rng=np.random.default_rng(SEED)
 def add(c,t,m=54,d=.3,v=.7,p=0,**kw):ev[c].append({'t':round(float(t),6),'midi':float(m),'dur':float(d),'vel':float(v),'pan':float(p),**kw})
 active=list(range(8,48))+list(range(56,64))+list(range(88,120))
 for b in active:
  # Caja en el tercer pulso: 140 escrito / 70 percibido. El final cambia los huecos.
  kicks=[0,6,11] if b%2==0 else [0,3,14]
  if b>=88:kicks=[0,7,10,14] if b%4<2 else [0,5,11]
  for s in kicks:add('kick',(b*16+s)*S,d=.15,v=.95 if s==0 else .7,pieza='kick')
  add('caja',(b*16+8)*S,d=.15,v=.84,pieza='snare');add('clap',(b*16+8)*S+.011,d=.15,v=.55,pieza='clap')
  for s in range(0,16,2):add('hats',(b*16+s)*S,d=.06,v=.2+.12*(s%4==2),p=.25,pieza='hat')
  if b%4 in [1,3]:
   for j in range(6):add('hats-tresillos',(b*16+13+j/3)*S,d=.05,v=.2+.045*j,p=-.35+j*.12,pieza='hat',pitch=-4 if j%2 else 0)
  if b%4==3:
   for s in [6,15]:add('perc-frita',(b*16+s)*S,d=.1,v=.45,p=-.3,pieza='rim')
  # El sub articula notas largas y portamentos; los medios responden en sus huecos.
  bass=[30,30,33,32,28,30] if b<88 else [30,33,32,28,25,30]
  for j,s in enumerate([0,6,11]):
   m=bass[(j+b//2)%len(bass)];dur=[5.3,3.5,4.4][j]*S
   add('sub',(b*16+s)*S,m,dur,.9,prev=m+(-5 if j==2 else 2),glide=.065)
   add('808-cuerpo',(b*16+s)*S,m+12,dur,.65)
   if b%2==0:add('falcon',(b*16+s+1)*S,m+12,min(dur,.7),.5)
  if 32<=b<48 or b>=88:
   for j,s in enumerate([3,10,14]):add('mandibula',(b*16+s)*S,42+[0,3,-2][(j+b)%3],S*(2 if j==2 else 1.7),.8,prev=42,gesto=j+b%3)
 for b in [2,6,10,14,18,22,26,30,34,38,42,46,49,53,57,61,89,93,97,101,105,109,113,117,121,125]:
  subj=P['sujeto']['semitonos'][:];rit=P['sujeto']['semicorcheas'];start=b*B
  if b>=88:subj=[0,3,2,-2,-5,0] # el final conserva la inflexión del retorno
  if b in [22,42,53,101]:subj=list(reversed(subj))
  for j,(g,r) in enumerate(zip(subj,rit)):
   t=start+sum(rit[:j])*S;c='mbira' if j%2==0 else 'kalimba'
   add(c,t,54+g,r*S*.9,.65,p=-.28 if c=='mbira' else .3)
   if b>=10:add('arpa-boca',t+S,66+g,r*S,.52,p=.1)
   if 48<=b<64 or b>=88:
    add('mbira-vocal',t,54+g,r*S+Q,.72,p=-.2)
    if j%2:add('kalimba-vocal',t+S*.5,54+g,r*S+Q,.65,p=.2)
 # Solo de pulgares: desplazamiento de acentos, tres longitudes de frase y respuesta grave.
 for k,b in enumerate(range(48,64,2)):
  for j,g in enumerate([0,3,7,5,2,-2,0][:5+k%3]):
   t=b*B+j*Q*(.5 if k%2 else .75);m=54+g+(12 if k in [3,6] else 0)
   add('mbira-vocal',t,m,Q*(.4+j%3*.2),.8,p=float(np.sin(j)*.45));add('kalimba',t+Q*.25,m-12,Q*.5,.4,p=-.3)
  add('dundun',(b+1)*B,42+3*(k%2),.18,.7,texto=['tu nombre','por debajo','la corriente','devuelve'][k%4])
 for b in [4,12,20,28,36,44,60,70,78,86,92,100,108,116,124]:
  add('organo-roto',b*B,42+[0,3,-2,-5][b//4%4],B*2,.45)
  for c,m in [('chelo',54),('contrabajo',30)]:add(c,b*B,m+[0,3,2,-2][b//4%4],B*1.7,.5,p=-.3 if c=='chelo' else .15,tipo='tasto')
 for c in ['flujo-ideal','flujo-viscoso','residuo','eco-captador','residuo-grave']:
  for b in range(0,128,4):
   if c=='residuo-grave' and b<64:continue
   add(c,b*B,42 if c!='residuo-grave' else 30,B*4,.6)
 # El solo D escucha primero los dos campos; después sólo su diferencia, cambiando captador.
 P['gestos_captador']=[{'t':(64+k*3)*B,'angulo':float(k*np.pi/5),'nota':42+[0,3,2,7,5,2,-2,0][k]} for k in range(8)]
 phrases=[('tu nom bre vuel ve por de ba jo',[0,0,3,2,0,-2,0,-2,0],[1,1,2,1,1,2,1,1,4]),('lo que se pier de tam bién pe sa',[3,2,0,-2,-2,0,2,-2,-5],[1,1,1,2,1,1,2,1,4]),('di je tu nom bre con tra el a gua',[0,3,2,0,-2,0,2,3,2,0],[1,1,2,1,1,1,1,1,1,4]),('la co rrien te de vuel ve tu nom bre',[-2,0,3,2,0,-2,0,2,0,-5],[1,1,1,2,1,1,1,1,1,4]),('lo que re gre sa ya no es lo mis mo',[0,0,3,5,3,2,0,-2,0,-2,-5],[1,1,1,1,1,2,1,1,1,1,4])]
 voices={'solista':[],'doble':[],'chops':[],'coro':[]}
 for k,b in enumerate([10,14,18,22,26,30,34,40,50,58,66,74,82,90,94,98,102,106,110,114,120,124]):
  fi=(k%4 if b<88 else 4 if b%8==2 else 3);tx,notes,ds=phrases[fi];t=b*B+.18*Q;start=t
  for j,(sy,g,beats) in enumerate(zip(tx.split(),notes,ds)):
   dur=beats*Q*.88;m=42+g
   if b>=88 and j==len(notes)-2:m=37 # cambio que deja el solo
   voices['solista'].append({'t':t,'dur':dur,'texto':sy,'nota':m});add('solista-grave',t,m,dur,.8)
   if b in [26,34,40,90,98,106,114,124] and j%2==0:
    voices['doble'].append({'t':t+.025,'dur':dur*.97,'texto':sy,'nota':m-5});add('doble-grave',t+.025,m-5,dur,.5)
   if b>=66:add('voz-residual',t,m,dur,.65)
   if 48<=b<64 or b>=88:add('boca-percusiva',t,m,dur,.6)
   t+=beats*Q
  P['letra'].append({'t':start,'t1':t,'texto':tx,'frase':fi})
 for b in [31,39,47,63,87,95,103,111,119]:
  for j,sy in enumerate(['nom','nom','bre','vuel','ve','a']):
   t=b*B+j*Q*.5;voices['chops'].append({'t':t,'dur':Q*.35,'texto':sy,'nota':37+[0,0,5,3,0,-2][j]});add('chops-graves',t,37,Q*.35,.7)
 for b in [0,6,46,62,70,78,86,118,122,126]:
  voices['coro'].append({'t':b*B,'dur':B*1.6,'texto':['u','o','a'][b%3],'nota':49+[0,3,2,-2][b//2%4]});add('coro-oscuro',b*B,49,B*1.6,.5)
 P['sabina']=[{'capa':c,'eventos':v} for c,v in voices.items()]
 P['prueba_voz']=[{'t':.15+j*.45,'dur':.4 if j<8 else 1,'texto':s,'nota':42+[0,0,3,2,0,-2,0,-2,0][j]} for j,s in enumerate('tu nom bre vuel ve por de ba jo'.split())]
 for c in ev:ev[c].sort(key=lambda e:e['t'])
 assert len(ev)==30 and all(ev.values());jsave(out/'partitura.json',P)
 f,ax=figura('Treinta capas y una corriente','140 BPM escrito / 70 percibido · sub F#1 · solista grave · los solos dejan cambios')
 for i,(c,events) in enumerate(ev.items()):
  for e in events:ax[0].plot([e['t'],e['t']+min(e['dur'],3)],[i,i],lw=1,color=['#a292fa','#ff9966','#9bd9d1'][i//10])
 ax[0].set_yticks(range(30),names,fontsize=6);ax[0].set_xlim(0,D);ax[0].set_xlabel('segundos');salva(f,out/'proceso'/f'03-partitura-s{SEED}-{tag}.png')
 print('Partitura:',D,'s;',sum(map(len,ev.values())),'eventos')
if __name__=='__main__':main()
