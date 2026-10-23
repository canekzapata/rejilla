"""Medida del WAV entregado, veinte lecturas/s para Hydra."""
from comun import *
def main():
 out=ultimo();sr,y=wavfile.read(master());mono=y.mean(1);step=round(sr/20);r=np.array([np.sqrt(np.mean(mono[i:i+step]**2)) for i in range(0,len(y),step)]);scale=np.percentile(r,95);jsave(out/'audio-visual.json',{'hz':20,'rms':np.clip(r/(scale+1e-9),0,1).tolist(),'origen':master().name,'sha256':sha(master())})
if __name__=='__main__':main()
