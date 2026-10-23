from comun import *
from instrumentos import chirp
from scipy.signal import resample_poly
def main():
 out=ultimo();P=leer(score());V=np.fromfile(BASE/'render/guia-radio.f32',np.float32);R=importar(BASE/'fuentes/radio/sintes10.py','baila_radio');N=round(18*R.SR);voice=resample_poly(V,3,2);a=voice.copy();a[9*R.SR:]=0;b=voice.copy();b[:9*R.SR]=0;y,meta=R.radio([{'f':620,'audio':a,'nivel':.8,'fading':0},{'f':630,'audio':b,'nivel':.8,'fading':0}],[[0,615],[.5,620],[7,620],[8.5,625],[10,630],[17,630]],N,semilla=SEED);info={'radio':muestra(out,'sonda-radio-chofer-pasajera',pan(resample_poly(y,2,3))),'dial':meta};info['radio']['texto']='El fondo acaba de cambiar de calle / La radio ya llegó pero seguimos aquí';info['radio']['limite']='guía PSOLA, no interpretación hablada definitiva'
 # Reloj fijo a la izquierda; entradas efectivas de tres ciclos de la partitura a la derecha.
 clip=np.zeros((round(16*SR),2));proof=[]
 cycles=[28*4,52*4,64*4]
 for i,start in enumerate(cycles):
  for beat in range(8):
   n=round(.035*SR);tt=np.arange(n)/SR;z=.08*np.sin(2*np.pi*900*tt)*np.exp(-tt*150);poner(clip,z,i*5.3+beat*Q,p=-1)
  events=[e for c in ['laser-directo','laser-laberinto','laser-talbot','acordeon-tema'] for e in P['eventos'][c] if start<=e['pulso']<start+8]
  for e in events:poner(clip,chirp(e['midi'],min(.18,e['dur']),.4),i*5.3+(e['pulso']-start)*Q,p=1)
  tr=[e for e in P['traza_trafico'] if start<=e['pulso_nominal']<start+8];proof.append({'ciclo_pulso':start,'eventos':len(events),'traza':tr})
 info['trafico']={**muestra(out,'sonda-pulso-fijo-y-trafico',clip),'canales':'izquierda pulso fijo / derecha ataques de partitura; tres ciclos separados','pruebas':proof};jsave(out/'sondas-radio-trafico.json',info);print('radio y dos relojes: muestras cortas listas')
if __name__=='__main__':main()
