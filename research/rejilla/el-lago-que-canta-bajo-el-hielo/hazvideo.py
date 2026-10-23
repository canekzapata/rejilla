"""El lago que canta bajo el hielo: renderiza el video sólo cuando tú lo ejecutes.

    python hazvideo.py                  # 1920×1080, 30 fps, entrega de ULTIMA.txt
    python hazvideo.py --ancho 1280     # copia de 1280×720
    python hazvideo.py --comprobar      # sólo un PNG de prueba, ningún MP4
    python hazvideo.py --seco           # verifica archivos y sintaxis, sin navegador

No sobreescribe videos. Requiere Python, Node, Chrome y ffmpeg de esta máquina.
Conserva el máster WAV local junto al M4A. El visor está congelado en fuentes/traspuesta.
"""
import argparse,subprocess,shutil
from comun import *
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('entrega',nargs='?');ap.add_argument('--ancho',type=int,default=1920,choices=[1280,1920]);ap.add_argument('--fps',type=int,default=30);ap.add_argument('--comprobar',action='store_true');ap.add_argument('--cuadro',choices=['titulo','final']);ap.add_argument('--seco',action='store_true');a=ap.parse_args()
 out=Path(a.entrega).resolve() if a.entrega else ultimo()
 for p in [out/'partitura.json',out/'red.json',out/(out.name+'.wav'),BASE/'grieta.js',BASE/'fuentes/traspuesta/musica.html']:
  if not p.is_file():raise FileNotFoundError(p)
 for cmd in ['node','ffmpeg']:
  if not shutil.which(cmd):raise RuntimeError('falta '+cmd)
 for p in [BASE/'video_musica.cjs',BASE/'grieta.js']:subprocess.run(['node','--check',str(p)],check=True)
 if a.seco:print('entradas y sintaxis comprobadas; no se abrió navegador ni se creó video');return
 cmd=['node',str(BASE/'video_musica.cjs'),str(out),'--ancho',str(a.ancho),'--fps',str(a.fps)]+(['--comprobar'] if a.comprobar else [])+(['--cuadro',a.cuadro] if a.cuadro else [])
 subprocess.run(cmd,check=True,cwd=BASE)
if __name__=='__main__':main()
