"""El video lo renderiza Canek. --comprobar sólo guarda PNGs; --seco revisa entradas."""
from comun import *
import argparse,shutil
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('entrega',nargs='?');ap.add_argument('--ancho',type=int,choices=[1280,1920],default=1920);ap.add_argument('--fps',type=int,choices=[24,30],default=30);ap.add_argument('--comprobar',action='store_true');ap.add_argument('--seco',action='store_true');a=ap.parse_args();out=Path(a.entrega).resolve() if a.entrega else ultimo()
 for f in ['partitura.json','batidos.json','audio-visual.json',master(out).name]:
  if not (out/f).is_file():raise FileNotFoundError(out/f)
 for cmd in ['node','ffmpeg']:
  if not shutil.which(cmd):raise RuntimeError('falta '+cmd)
 for f in ['coma.js','render_video.cjs']:subprocess.run(['node','--check',str(BASE/f)],check=True)
 if a.seco:print('entradas y sintaxis correctas; no se abrió navegador ni se creó video');return
 subprocess.run(['node',str(BASE/'render_video.cjs'),str(out),'--ancho',str(a.ancho),'--fps',str(a.fps)]+(['--comprobar'] if a.comprobar else []),cwd=BASE,check=True)
if __name__=='__main__':main()
