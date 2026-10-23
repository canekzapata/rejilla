"""Preparación explícita del entorno local. Sólo descarga numpy/scipy/matplotlib/Pillow de PyPI."""
import pathlib, subprocess, sys, venv
base=pathlib.Path(__file__).resolve().parent
dest=base/'.venv'
print('Preparando el entorno dentro de esta carpeta. Hace falta internet para descargar dependencias.')
venv.EnvBuilder(with_pip=True).create(dest)
exe=dest/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
subprocess.run([str(exe),'-m','pip','install','-r',str(base/'requirements.txt')],check=True)
print('Listo. Abre Taller-Windows.bat o Taller-Mac.command. Si FFmpeg no está instalado, usa Directo.')
