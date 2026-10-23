"""Rinde capas originales y variantes; cada archivo existente se conserva."""
from comun import *
from instrumentos import *
import gc
def main():
 out=ultimo();P=leer(out/'partitura.json');N=round(P['duracion']*SR);Q=P['negra'];B=P['compas'];events=P['eventos'];eco=Eco(out,P)
 def mono(c):
  y=np.fromfile(run()/(c+'.f32'),np.float32);assert len(y)==N,(c,len(y),N);return y
 def done(c):return (run()/(c+'.f32')).exists()
 for c,kind in [('sub','sub'),('808-cuerpo','cuerpo'),('mandibula','growl')]:
  if done(c):continue
  y=np.zeros((N,2),np.float32)
  for e in events[c]:poner(y,bajo(e,kind),e['t'],p=0 if c=='sub' else e['pan'])
  raw(c,y);print(c,flush=True)
 for c in ['kick','caja','clap','hats','hats-tresillos','perc-frita']:
  if done(c):continue
  y=np.zeros((N,2),np.float32);cache={}
  for e in events[c]:
   key=('bateria-frito' if c in ['clap','perc-frita'] else 'bateria-tr808',e['pieza'],int(np.argmin(abs(np.array([.3,.6,.9])-e['vel']))),e.get('pitch',0))
   if key not in cache:
    x=np.fromfile(run()/f'{key[0]}-{key[1]}-{key[2]}.f32',np.float32)
    if key[3]:x=np.interp(np.arange(0,len(x),2**(key[3]/12)),np.arange(len(x)),x)
    cache[key]=x
   poner(y,cache[key],e['t'],e['vel']/[.3,.6,.9][key[2]],e['pan'])
  raw(c,y);print(c,flush=True)
 for c,kind,m,moving in [('flujo-ideal','ideal',42,False),('flujo-viscoso','viscoso',42,False),('residuo','residuo',42,False),('eco-captador','residuo',42,True),('residuo-grave','residuo',30,True)]:
  if done(c):continue
  y=eco.audio(kind,m,moving);raw(c,y);print(c,flush=True);del y;gc.collect()
 for c,source,fac in [('solista-grave','sabina-solista',.80),('doble-grave','sabina-doble',.84),('chops-graves','sabina-chops',.75),('coro-oscuro','sabina-coro',.86)]:
  if done(c):continue
  raw(c,pan(pecho(mono(source),fac),0 if c=='solista-grave' else -.18 if c=='doble-grave' else .18));print(c,flush=True)
 G=importar(lib()/'motores/gemelo.py','gemelo_corriente')
 for c,id in [('mbira-vocal','mbira'),('kalimba-vocal','kalimbacaja')]:
  if done(c):continue
  y=np.zeros((N,2),np.float32);K=leer(lib()/'fichas'/(id+'.json'));cache={}
  for e in events[c]:
   key=(e['midi'],round(e['vel'],1))
   if key not in cache:cache[key]=G.nota(K,key[0],key[1],segundos=2.4,sr=SR,tonica='F#')
   poner(y,cache[key],e['t'],p=e['pan'])
  z=boca_pulgar(y.mean(1),events[c]);raw(c,pan(z,-.23 if c=='mbira-vocal' else .23));print(c,flush=True);del y,z;gc.collect()
 if not done('voz-residual'):
  mod=mono('sabina-solista');car=np.fromfile(run()/'eco-captador.f32',np.float32).reshape(-1,2).mean(1);z=vocoder(mod,car);z[:round(64*B*SR)]=0;raw('voz-residual',pan(z));print('voz-residual',flush=True)
 if not done('boca-percusiva'):
  mod=mono('sabina-solista');car=mono('arpa-boca')+mono('dundun')*.35;z=vocoder(mod,np.tanh(car*4));gate=np.zeros(N)
  gate[round(48*B*SR):round(64*B*SR)]=1;gate[round(88*B*SR):round(120*B*SR)]=1
  raw('boca-percusiva',pan(z*gate,.2));print('boca-percusiva',flush=True)
if __name__=='__main__':main()
