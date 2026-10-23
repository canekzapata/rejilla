"""La fase vuelve distinta: una canción nueva de Rejilla, compuesta por familias y relevos."""
from pathlib import Path
import importlib.util,json,uuid,hashlib,io,subprocess
import numpy as np
from scipy.signal import butter,sosfilt,resample_poly
from scipy.io import wavfile
from PIL import Image,ImageDraw

R=Path(__file__).resolve().parent; REPO=R.parent
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
h=load('helpers',REPO/'la-garganta-sale-bailando/producir.py')
sy=load('sintes',REPO/'lo-que-tapa-la-traspuesta/sintes2.py')
SR=24000; DUR=188.; N=int(DUR*SR); SEED=19102691
SECTIONS=[(0,16,'semilla'),(16,46,'llamada'),(46,70,'coro'),(70,90,'espejo'),(90,120,'retorno'),(120,148,'diagonal'),(148,172,'danza'),(172,188,'coda')]
P=dict(titulo='La fase vuelve distinta',duracion=DUR,semilla=SEED,secciones=SECTIONS,garganta=[],metal=[],chelo=[],bajo=[],sinte=[],voces=[],bateria=[])

def note(v,t,m,d,vel=.8,**kw):
 if t+d<=DUR:P[v].append(dict(t=round(float(t),5),m=float(m),dur=float(d),v=vel,**kw))
def midi(hz):return 69+12*np.log2(hz/440.)
H=[220,247.5,275,302.5,330,357.5,385,412.5]
U=[220,6600/26,275,6600/22,330,6600/19,6600/17,330]
def phrase(v,t,vals,rhy,scale=1.,vel=.8,offset=0,vowels=True):
 for j,(m,r) in enumerate(zip(vals,rhy)):
  if m is not None:note(v,t,m+offset,r*scale,vel,vocal=('aeiou'[j%5] if vowels else 'a'))
  t+=r*scale
 return t
def family(fam,octv=0):
 return [midi(x*(2**octv)) for x in (H if fam=='H' else U)]

def score():
 # A short anchor, with an asymmetrical landing. The same contour is not copied as MIDI notes later.
 mh=family('H'); mu=family('U')
 phrase('garganta',16,mh,[.42,.25,.5,.34,.62,.23,.42,.9],.84,.82)
 phrase('metal',23.2,mh[::-1],[.25,.48,.33,.56,.22,.4,.55,.8],.74,.68,offset=-12)
 phrase('garganta',32.8,mh,[.42,.25,.5,.34,.62,.23,.42,1.25],.84,.78,offset=0)
 # Chorus: four lines enter at unequal offsets; the shared anchors remain audible.
 for j,off in enumerate([0,.38,.83,1.31]):
  vals=mh[::1] if j%2==0 else mh[::-1]
  phrase('voces',46+off,vals,[.42,.25,.5,.34,.62,.23,.42,.9],.7,.58,offset=(12 if j==2 else -12 if j==3 else 0))
 # The phase-conjugate section removes drums and reverses the arrival order in the low family.
 phrase('chelo',70,mu[::-1],[.8,.32,.6,.25,.48,.34,.7,1.1],.78,.6,offset=-12)
 phrase('garganta',72.8,mu,[.65,.22,.54,.29,.65,.2,.45,.95],.72,.72,offset=0)
 phrase('metal',80.5,mu[::-1],[.26,.4,.24,.63,.3,.46,.4,.72],.66,.55,offset=-24)
 # Return in 7/8: same hook rhythm is compressed and the last arrival is displaced.
 phrase('garganta',90,mu,[.42,.25,.5,.34,.62,.23,.42,.9],.68,.78,offset=12)
 phrase('metal',98.1,mu[2:]+mu[:2],[.34,.5,.24,.62,.3,.44,.55],.62,.62,offset=-12)
 phrase('voces',106.5,mu,[.42,.25,.5,.34,.62,.23,.42,.9],.61,.45,offset=0)
 # Diagonal: the bass gets the hook stretched; the upper voice cuts it into answers.
 phrase('bajo',120,[m-24 for m in mh],[.42,.25,.5,.34,.62,.23,.42,.9],1.18,.85)
 phrase('sinte',123.3,mh[::-1],[.22,.32,.18,.46,.24,.38,.27,.58],.83,.48,offset=12)
 phrase('metal',132.1,mh,[.42,.25,.5,.34,.62,.23,.42,.9],.53,.55,offset=-12)
 phrase('garganta',138.7,mu[::-1],[.31,.3,.42,.23,.5,.26,.6,.72],.7,.52,offset=0)
 # Dance: the family is mixed; each instrument owns a different fragment of the hook.
 phrase('voces',148,[mh[0],mh[2],mh[4],mh[7]],[.42,.5,.62,.9],.6,.52)
 phrase('metal',152.2,[mu[1],mu[3],mu[5],mu[6]],[.25,.34,.42,.54],.55,.52,offset=-12)
 phrase('garganta',157.1,[mh[7],mh[5],mh[3],mh[0]],[.23,.42,.34,.8],.55,.62,offset=12)
 # Coda is a memory with two unequal false endings and a final note that never lands on the first root.
 phrase('garganta',172,mh,[.42,.25,.5,.34,.62,.23,.42,.9],.58,.6,offset=-12)
 phrase('chelo',176.7,mu[:5],[.7,.3,.55,.25,.8],.55,.55,offset=-24)
 phrase('voces',180.3,[mh[7],mh[4],mu[2],mh[5]],[.42,.6,.34,1.1],.52,.5,offset=0)
 # Independent elastic bass, not a root loop.
 for a,z in [(16,46),(46,70),(90,120),(120,148),(148,172)]:
  step=2.0 if a<70 else 1.75 if a<120 else 1.45
  roots=[midi(110),midi(121),midi(137.5),midi(151.25),midi(165)]
  for j,t in enumerate(np.arange(a,z-.2,step)):
   note('bajo',float(t),roots[j%len(roots)]-24,.31 if j%3 else .48,.74,glis=(j%4==3),liso=(j%4==3))
 # Cello only answers in gaps and changes bow role at the mirror.
 for t,m,d,tipo,casa in [(4,57,2.8,'ponticello',0),(8.4,60,1.6,'arco',0),(12,55,2.4,'armonico',0),(70,52,.9,'tasto',0),(74.1,59,.55,'pizz',.2),(83.2,62,.7,'ponticello',0),(124,55,.7,'pizz',.7),(145,60,.8,'bartok',.8),(173.5,52,.9,'armonico',0),(184.2,58,1.1,'arco',0)]:note('chelo',t,m,d,.62,tipo=tipo,casa=casa)
 # Percussion has its own growing rule: 5/4, silence, 7/8, then a dembow that loses one hit before returning.
 for a,z,name in SECTIONS:
  if name=='semilla' or name=='espejo':continue
  q={ 'llamada':.6,'coro':.5,'retorno':60/168,'diagonal':60/112,'danza':60/188,'coda':.6}[name]
  bar=0;t=a
  while t<z-.1:
   for step in range(16):
    tt=t+step*q/4
    if tt>=z:continue
    if name=='llamada': kick=step in [0,7,10]; sn=step in [6,14]; hat=step%2==0
    elif name=='coro': kick=step in [0,5,8,12]; sn=step in [4,12]; hat=step%2==0
    elif name=='retorno': kick=step in ([0,4,9,13] if bar%3 else [0,5,10]); sn=step in [6,14]; hat=step%2==0
    elif name=='diagonal': kick=step in [0,8]; sn=step in [6,14]; hat=step in [3,7,11,15]
    elif name=='danza': kick=step in [0,6,8,11,14] if bar%4 else step in [0,8,12]; sn=step in [4,12]; hat=step%2==0
    else: kick=step in ([0,8] if bar%2 else [0,7,11]); sn=step in [6,14]; hat=step%2==0
    if kick:P['bateria'].append(dict(t=tt,pieza='kick',g=.85))
    if sn:P['bateria'].append(dict(t=tt,pieza='snare',g=.62))
    if hat:P['bateria'].append(dict(t=tt,pieza='hat',g=.13+.05*(step%4==0)))
    if step in [3,11] and name in ['llamada','coro','danza']:P['bateria'].append(dict(t=tt,pieza='rim',g=.28))
    if bar%3==2 and step in [13,15]:P['bateria'].append(dict(t=tt,pieza='tomlo',g=.3))
   if bar%4==0:P['bateria'].append(dict(t=t,pieza='spray',g=.15))
   t+=q*4;bar+=1
 # Explicit two silences are part of the score, not tails accidentally clipped.
 for t in [86.2,169.6,181.6,185.5]:P['bateria'].append(dict(t=t,pieza='clap',g=.4))
 for k in ['garganta','metal','chelo','bajo','sinte','voces','bateria']:P[k].sort(key=lambda e:e['t'])

def card(title):
 im=Image.new('RGB',(1200,630),'#101421');d=ImageDraw.Draw(im);d.text((32,20),'LA FASE VUELVE DISTINTA',font=h.font(41),fill='#fff1df');d.text((34,78),title,font=h.font(18),fill='#f0ae97')
 cols={'garganta':'#f2a3c0','metal':'#87ded0','chelo':'#e1d277','bajo':'#b09ff0','sinte':'#8eb9f1','voces':'#ed8d62'}
 for a,z,n in SECTIONS:
  x=40+a/DUR*1120;d.line((x,120,x,535),fill='#394052');d.text((x+2,545),n[:9],font=h.font(12),fill='#c9c7d0')
 for k,c in cols.items():
  for e in P[k]:
   x=40+e['t']/DUR*1120;y=488-(e['m']-32)*5.9;d.line((x,y,x+max(2,e['dur']/DUR*1120),y),fill=c,width=3)
 # Percussion is shown as a separate lower rail to keep its function visible.
 for e in P['bateria']:
  x=40+e['t']/DUR*1120;d.line((x,515,x,515-18*e['g']),fill='#fa875d',width=2)
 d.text((34,595),'Canek Zapata · 19 octubre 2026 · semilla 19102691',font=h.font(16),fill='#c8c6d2');return im

def add(stem,y,t,g=1,pan=0):
 a=int(t*SR);n=min(len(y),N-a)
 if a<0 or n<=0:return
 ang=(pan+1)*np.pi/4;stem[a:a+n,0]+=y[:n]*g*np.cos(ang);stem[a:a+n,1]+=y[:n]*g*np.sin(ang)

def main():
 score();im=card('01 · la misma melodía cambia de familia, fase y cuerpo')
 buf=io.BytesIO();im.save(buf,'PNG');nonce=uuid.uuid4().hex;full=hashlib.sha256(buf.getvalue()+Path(__file__).read_bytes()+nonce.encode()).hexdigest();tag=full[:12]
 out=R/f'la-fase-vuelve-distinta-s{SEED}-{tag}';out.mkdir()
 for k in ['render','proceso','fuentes']:(out/k).mkdir()
 h.js(out/'partitura.json',P);h.png(out/'proceso'/f'01-partitura-{tag}.png',im)
 sources=[Path(__file__),R/'fisicos.cjs',REPO/'lo-que-tapa-la-traspuesta/sintes2.py',REPO/'lo-que-tapa-la-traspuesta/motor/garganta.js',REPO/'objetos/motor/cuerda.js',REPO/'objetos/motor/metal.js',REPO/'otra-vez-hasta-romper/kit.cjs',REPO/'APRENDIDO.md',REPO/'SONAR-LO-VIRTUAL.md']
 hashes={str(p.relative_to(REPO)):h.sha(p) for p in sources}
 for j,p in enumerate(sources):(out/'fuentes'/f'{j:02d}-{p.name}').write_bytes(p.read_bytes())
 h.js(out/'receta-inicial.json',dict(hash=full,nonce=nonce,semilla=SEED,fuentes=hashes))
 subprocess.run(['node',str(R/'fisicos.cjs'),str(out)],check=True)
 subprocess.run(['node',str(REPO/'otra-vez-hasta-romper/kit.cjs'),str(out)],check=True)
 # Preserve a deliberately small three-voice sketch before the walls and drum field.
 sketch=np.zeros(N,np.float32)
 for k,g in [('garganta',.16),('metal',.12),('bajo',.14)]:
  for e in P[k]:
   n=int(e['dur']*SR);t=np.arange(n)/SR;y=np.sin(2*np.pi*h.hz(e['m'])*t)*h.env(n)*g;a=int(e['t']*SR);sketch[a:a+n]+=y
 h.wav(out/'render'/f'boceto-tres-voces-{tag}.wav',sketch)
 stems={k:np.zeros((N,2),np.float32) for k in ['solistas','chelo','bajo','paredes','vocoder','percusion']}
 for name,dest,g,pan in [('garganta','solistas',.33,-.15),('metal','solistas',.28,.22),('chelo','chelo',.28,-.32)]:
  y=resample_poly(np.fromfile(out/'render'/f'{name}.f32',dtype=np.float32),1,2);add(stems[dest],h.unit(y),0,g,pan)
 for name,timbre,g in [('bajo','fretless',.25),('sinte','zawinul',.18)]:
  y=resample_poly(sy.mono(P[name],int(DUR*48000),timbre,SEED),1,2);add(stems[name],y,0,g,0)
 # The wall is the audible Rejilla law: exact harmonic/subharmonic ratios with close beating copies.
 tt=np.arange(N)/SR;wall=np.zeros((N,2),np.float32)
 bands=[(0,70,'H'),(70,90,'M'),(90,120,'U'),(120,148,'M'),(148,172,'B'),(172,188,'U')]
 for a,b,fam in bands:
  i=int(a*SR);j=int(b*SR);t=tt[i:j]-a;freqs=(H if fam=='H' else U if fam=='U' else [(H[k]+U[k])*.5 for k in range(8)])
  for q,f in enumerate(freqs):
   env=np.minimum(1,t/.18)*np.minimum(1,np.maximum(0,b-a-t)/.4);amp=(.018/(1+q*.32))*env
   if fam=='B':amp*=1.3
   ph=2*np.pi*f*t
   wall[i:j,0]+=np.sin(ph)*amp
   wall[i:j,1]+=np.sin(ph+(.7+.03*q)*np.sin(t*(.8+q*.1)))*amp
 stems['paredes']+=wall
 # Vocoder vowels become the same hook in four different carriers.
 bank=REPO/'inferencia/vendor/difonos/bancos/sabina-1-b44e7fab5cee';M=json.loads((bank/'manifiesto.json').read_text('utf8'));raw=np.frombuffer(h.run(['ffmpeg','-v','error','-i',str(bank/'banco.flac'),'-f','f32le','-ac','1','pipe:1']).stdout,dtype='<f4');vowels={}
 for v in 'aeiou':
  u=M['unidades'][v*2];vowels[v]=resample_poly(raw[u['inicio']+u['izq']:u['inicio']+u['der']],160,147)
 edges=np.geomspace(100,10500,25);filters=[butter(2,[a,b],fs=SR,btype='band',output='sos') for a,b in zip(edges[:-1],edges[1:])];sm=butter(1,26,fs=SR,output='sos')
 for e in P['voces']:
  n=int(e['dur']*SR);t=np.arange(n)/SR;grain=vowels[e.get('vocal','a')];mod=np.zeros(n+len(grain))
  for q in range(0,n,max(1,len(grain)//3)):mod[q:q+len(grain)]+=grain*np.hanning(len(grain))
  ph=2*np.pi*h.hz(e['m'])*t;carrier=np.sin(ph+2.5*np.sin(ph*2.01)*np.exp(-t/1.8)) if int(e['m'])%2 else sum(np.sin(k*ph)/k for k in range(1,min(28,int(10500/h.hz(e['m'])))))
  y=sum(sosfilt(f,carrier)*sosfilt(sm,np.abs(sosfilt(f,mod[:n]))) for f in filters)
  add(stems['vocoder'],h.unit(y)*h.env(n,.025,.09),e['t'],.2,(-.5 if e['t']<70 else .35))
 # Real kit, with the front edge preserved and sustained fields ducked only at kicks.
 kit={k:h.unit(np.fromfile(out/'render'/f'kit-{k}.f32',dtype=np.float32)) for k in ['kick','snare','hat','rim','tomlo','spray','clap']}
 for e in P['bateria']:
  add(stems['percusion'],kit[e['pieza']],e['t'],e['g']*.7,0 if e['pieza'] in ['kick','snare'] else .32)
 duck=np.ones(N,np.float32)
 for e in P['bateria']:
  if e['pieza']=='kick':
   a=int(e['t']*SR);n=min(int(.16*SR),N-a);duck[a:a+n]=np.minimum(duck[a:a+n],1-.42*np.exp(-np.arange(n)/SR/.055))
 for k,y in stems.items():
  y*=duck[:,None]**(1.2 if k in ['bajo','paredes'] else .45)
  h.wav(out/'render'/f'{k}-{tag}.wav',y)
 # Make the phase mirror audible by giving the whole 70–90 bridge a narrower, quieter field.
 mix=sum(stems.values());mix[70*SR:90*SR]*=.78;mix[181*SR:186*SR]*=0
 # Unequal false endings: a short cut, a longer cut, then a final shared impact.
 for a,z in [(86.2,88.1),(169.6,172.0),(181.6,183.7),(185.5,187.0)]:
  i=int(a*SR);j=int(z*SR);r=min(int(.012*SR),j-i);mix[i:i+r]*=np.linspace(1,0,r)[:,None];mix[i+r:j]=0
 mix*=.78/(abs(mix).max()+1e-12);h.wav(out/f'mezcla-{tag}.wav',mix)
 master=out/f'la-fase-vuelve-distinta-{tag}.m4a';h.run(['ffmpeg','-v','error','-n','-i',str(out/f'mezcla-{tag}.wav'),'-af','volume=3dB,alimiter=limit=0.78:attack=3:release=55:level=false:latency=true','-c:a','aac','-b:a','256k',str(master)])
 # Render the final two stages and an actual process GIF.
 im2=card('02 · paredes armónicas/subarmónicas, vocoders y percusión frontal');h.png(out/'proceso'/f'02-orquestacion-{tag}.png',im2)
 im3=card('03 · el retorno conserva el gancho y cambia la fase');h.png(out/'proceso'/f'03-mezcla-{tag}.png',im3);h.png(out/f'la-fase-vuelve-distinta-{tag}.png',im3);h.png(out/'og.png',im3)
 frames=[Image.open(p).convert('RGB') for p in sorted((out/'proceso').glob('*.png')) if 'revision' not in p.name]
 with (out/f'proceso-la-fase-{tag}.gif').open('xb') as f:frames[0].save(f,format='GIF',save_all=True,append_images=frames[1:],duration=2400,loop=0)
 # Technical checks and final recipe.
 log=h.run(['ffmpeg','-hide_banner','-i',str(master),'-af','loudnorm=I=-14:TP=-1:LRA=9:print_format=json','-f','null','-']).stderr.decode('utf8','replace');m=json.JSONDecoder().raw_decode(log[log.rfind('{'):])[0]
 y=wavfile.read(out/f'mezcla-{tag}.wav')[1];assert np.isfinite(y).all() and abs(y).max()<1
 with (out/'verificacion.json').open('x') as f:json.dump(dict(duracion=len(y)/SR,pico=float(abs(y).max()),input_lufs=m['input_i'],input_tp=m['input_tp'],input_lra=m['input_lra'],finito=True,escucha_humana=False),f,indent=2)
 h.txt(out/'proceso/README.md','01: partitura y familias H/U/M; 02: orquestación con cuerpos, paredes y vocoders; 03: mezcla con sidechain y cortes escritos. El GIF reúne esas tres etapas reales, dura 7.2 s. Semilla 19102691.\n')
 h.txt(out/'ESCUCHA.md','# La fase vuelve distinta\n\nCanción instrumental con voces sin palabras, 3:08. Un mismo gancho pasa por armónicos, subarmónicos y una mezcla de ambos. La sección espejo quita la batería y altera el orden de llegada; el retorno lo comprime en 7/8; la danza reparte sus notas entre garganta, metal, bajo y vocoder. La coda tiene cortes desiguales y una llegada nueva.\n\nLa mezcla conserva la percusión al frente, pero los ataques abren hueco al bajo y a las paredes. Las medidas son técnicas; la escucha humana queda para Canek.\n')
 h.js(out/'receta-final.json',dict(hash=full,nonce=nonce,semilla=SEED,archivos={str(p.relative_to(out)):h.sha(p) for p in out.rglob('*') if p.is_file()}))
 print('TERMINADO',master,flush=True)
if __name__=='__main__':main()
