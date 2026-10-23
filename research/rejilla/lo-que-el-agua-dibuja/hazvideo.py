"""Lo que el agua dibuja — graba el video del visor de música de Traspuesta con la coreografía de coreografia-video.json.

    python hazvideo.py                 → toma la entrega más nueva (carpeta lo-que-el-agua-dibuja-s67-*) y graba el video
    python hazvideo.py <carpeta>       → esa entrega
    python hazvideo.py --prueba        → sólo unos cuadros sueltos (PNG en render/cuadros-prueba/), unos minutos

Tarda unas dos horas y media para 4:41 de canción (≈ 8 400 cuadros). Necesita node con playwright (el mismo de los otros videos de rejilla)
y ffmpeg. No pisa nada: si la entrega ya tiene video, se detiene. Al terminar anota los tamaños en el README y dice qué commitear
(los mp4 se quedan fuera de git; visor-coreografia.json y el README sí van).
"""
import glob, os, subprocess, sys, time
AQUI = os.path.dirname(os.path.abspath(__file__))


def entrega(arg=None):
    if arg: return os.path.abspath(arg)
    c = [d for d in glob.glob(os.path.join(AQUI, 'lo-que-el-agua-dibuja-s67-*')) if os.path.isdir(d)]
    if not c: sys.exit('no hay entrega todavía: corre primero la mezcla')
    return max(c, key=os.path.getmtime)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; prueba = '--prueba' in sys.argv
    E = entrega(args[0] if args else None); n = os.path.basename(E)
    if not os.path.exists(os.path.join(E, n + '.wav')): sys.exit(f'falta {n}.wav en la entrega')
    if not prueba and glob.glob(os.path.join(E, '*-visor-*.mp4')): sys.exit('esta entrega ya tiene video: no se pisa')
    cmd = ['node', os.path.join(AQUI, 'video_musica.cjs'), E] + (['--cuadros', '10,40,52,75,108,125,150,190,200,215,232,252,272', '--fps', '6'] if prueba else [])
    print('→', ' '.join(cmd), flush=True); t0 = time.time()
    r = subprocess.run(cmd, cwd=AQUI)
    if r.returncode: sys.exit(f'el video falló (código {r.returncode})')
    if prueba: print('listo en', round(time.time() - t0), 's: mira render/cuadros-prueba/'); return
    mp4 = sorted(glob.glob(os.path.join(E, '*-visor-*.mp4')))
    lineas = [f'- `{os.path.basename(p)}` ({os.path.getsize(p) / 2 ** 20:.0f} MB)' for p in mp4]
    readme = os.path.join(AQUI, 'README.md')
    with open(readme, 'a', encoding='utf-8') as f:
        f.write(f'\n**Video grabado** ({time.strftime("%Y-%m-%d")}, {round((time.time() - t0) / 60)} min), fuera de git:\n' + '\n'.join(lineas) + '\n')
    print('\n'.join(lineas)); print('\npara guardarlo en git:')
    print(f'  git add "{os.path.relpath(os.path.join(E, "visor-coreografia.json"), AQUI)}" README.md && git commit -m "lo que el agua dibuja: video con el visor de música"')


if __name__ == '__main__':
    main()
