"""La primera captura origina un identificador irrepetible de esta entrega."""
from comun import *
from laminas import *
import shutil
def main():
 scratch=BASE/'render'/('terreno-'+os.urandom(6).hex());scratch.parent.mkdir(exist_ok=True);subprocess.run(['node',str(BASE/'exportar.cjs'),str(scratch)],check=True)
 T=leer(scratch/'terreno-22.json');H=np.fromfile(scratch/'h-22.f32',np.float32).reshape(T['G'],T['G']);f,ax=figura('La mesa ya trae una salida','Traspuesta 22 · 7 km · relieve 340 m · abanico aluvial dentro de la hoja')
 ax[0].contour(H,levels=25,colors=T['plumas'][0],linewidths=.5,origin='upper');e=next(e for e in T['especiales'] if e['term']=='ABANICO');ax[0].plot(e['u']*(T['G']-1),e['v']*(T['G']-1),'o',color=T['plumas'][-1]);ax[0].set_aspect('equal');ax[0].set_axis_off();b=png(f);nonce=os.urandom(24).hex();full=hashlib.sha256(b+VERSION.encode()+nonce.encode()+Path(__file__).read_bytes()).hexdigest();tag=full[:12];out=BASE/f'por-aqui-partitura-s{SEED}-{tag}';out.mkdir(exist_ok=False);(out/'proceso').mkdir();(out/'datos').mkdir()
 guardar(out/'proceso'/f'01-lamina-y-abanico-s{SEED}-{tag}.png',b)
 for p in scratch.iterdir():guardar(out/'datos'/p.name,p.read_bytes())
 jsave(out/'ejecucion.json',{'hash':full,'nonce':nonce,'version':VERSION,'seed':SEED,'imagen_inicial_sha256':hashlib.sha256(b).hexdigest(),'etapa':'partitura e instrumentos para revisar','fecha_contexto_usuario':'2026-10-21'})
 guardar(BASE/'ULTIMA.txt',out.name.encode());print(out)
if __name__=='__main__':main()
