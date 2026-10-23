"""Lo que tapa la traspuesta — el video, con el motor de salida de Traspuesta (montanas-topograficas/herramientas/pelicula.js:
ver.html en modo película, reloj cuadro por cuadro, la pluma traza a velocidad constante). Un plano por sección, todos de la
cordillera 420048 en papel oscuro, cada uno dura lo que dura su sección; cortes secos en los cambios de sección (las tijeras de
Nobuto también son de imagen). La letra aparece, en minúsculas, mientras el coro la canta. El audio es la entrega.
    python video.py <carpeta-de-render> <carpeta-de-entrega>      (o --planos en vez de la entrega: sólo rinde los planos)
Escribe <entrega>/<nombre>-video-1920x1080.mp4 (fuera de git: pesa) y un corte ligero de 1280×720.
"""
import json, os, subprocess, sys
AQUI = os.path.dirname(os.path.abspath(__file__)); MT = os.path.normpath(os.path.join(AQUI, '..', '..', 'montanas-topograficas'))
RUN, OUT = sys.argv[1], sys.argv[2]; SOLO_PLANOS = OUT == '--planos'                 # --planos: sólo los planos (no dependen del audio)
P = json.load(open(os.path.join(RUN if SOLO_PLANOS else OUT, 'partitura.json'), encoding='utf-8')); SEC = P['secciones']
nombre = os.path.basename(OUT); audio = os.path.join(OUT, nombre + '.m4a'); tmp = os.path.join(RUN, 'video'); os.makedirs(tmp, exist_ok=True)
# por sección: la vista que le toca (lo que la música hace con el terreno) y cuánto tarda la pluma (el resto es cola quieta)
# la letra en pantalla, escrita (las sílabas de la partitura van separadas para el coro)
LETRA_BONITA = {'can to pa ra ha cer un ce rro': 'canto para hacer un cerro', 'ce rro pa ra que ha ya a trás': 'cerro para que haya atrás', 'lo que ta pa la tras pues ta': 'lo que tapa la traspuesta', 'un pá ja ro lo can ta rá': 'un pájaro lo cantará', 'ca da cur va es u na cer ca': 'cada curva es una cerca', 'ca da co ta un es ca lón': 'cada cota un escalón', 'el vien to no tie ne ca sa': 'el viento no tiene casa', 'pa sa y no de ja su nom bre': 'pasa y no deja su nombre', 'ma pa no te rri to rio': 'mapa no, territorio', 'te rri to rio que se va': 'territorio que se va', 'dos mil ce rros que no e xis ten': 'dos mil cerros que no existen', 'y un pá ja ro que los o ye': 'y un pájaro que los oye'}
PLANOS = {
    'I':   ('s=420048&oscuro=1', .92, 'la montaña se forma por eras y la pluma la pasa en limpio: el punto gris se vuelve forma'),
    'II':  ('s=420048&hoja=curvas&planta=curvas&tanaka=0&oscuro=1&eras=0', .9, 'curvas de nivel: lo estriado, la retícula de la casa'),
    'III': ('s=420048&hoja=crestas&malla=1&oscuro=1&eras=0', .92, 'la malla se teje: el estribillo'),
    'IV':  ('s=420048&hoja=corte&oscuro=1&eras=0&cam=0,0.5,0.4,1.15;0.7,0.5,0.4,1.15;0.76,0.5,0.5,0;0.8,0.5,0.5,0;0.86,0.5,0.8,1.1;1,0.5,0.8,1.1;1.15,0.5,0.5,0', .82, 'el corte A–A′: abrir el círculo, mirar adentro del cerro'),
    'V':   ('s=420048&hoja=crestas&malla=0&oscuro=1&eras=0', .95, 'los perfiles, de adelante hacia atrás: lo liso, la traspuesta'),
    'VI':  ('s=420048&hoja=curvas&planta=curvas&tanaka=1&oscuro=1&eras=0', .75, 'curvas iluminadas: la cancioncilla en el viento'),
}
partes = []
for k, (a, z) in SEC.items():
    largo = (P['duracion'] if k == 'VI' else z) - a; params, frac, _ = PLANOS[k]
    mp4 = os.path.abspath(os.path.join(tmp, f'{k}.mp4')); partes.append((mp4, largo))   # absoluta: pelicula.js corre desde la carpeta de Traspuesta
    if os.path.exists(mp4): continue
    subprocess.run(['node', os.path.join(MT, 'herramientas', 'pelicula.js'), f'{params}&dur={largo * frac:.2f}', mp4, '--cola', f'{largo * (1 - frac) + .2:.2f}'], cwd=MT, check=True)
if SOLO_PLANOS: sys.exit(0)
# unir con cortes secos, cada parte recortada exacta a su sección
lista = os.path.join(tmp, 'partes.txt')
with open(lista, 'w', encoding='utf-8') as f:
    for mp4, largo in partes: f.write(f"file '{os.path.abspath(mp4).replace(os.sep, '/')}'\noutpoint {largo:.3f}\n")
mudo = os.path.join(tmp, 'mudo.mp4')
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lista, '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', '30', mudo], check=True)
# la letra: cada renglón aparece cuando el coro lo empieza y se va cuando termina su última sílaba. Este ffmpeg no trae drawtext
# (sin freetype): cada renglón es un PNG transparente (PIL, Consolas) que se superpone con overlay mientras suena
from PIL import Image, ImageDraw, ImageFont
fuente = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 38); chica = ImageFont.truetype('C:/Windows/Fonts/consola.ttf', 20)
renglones = []
for (k, C), versos in zip(P['coros'].items(), (P['letra']['verso'], P['letra']['coro'], P['letra']['final'])):
    sop = C['S']; i = 0
    for linea in versos:
        n = len(linea.split()); sil = sop[i:i + n]; i += n
        renglones.append((LETRA_BONITA.get(linea, linea), sil[0]['t'] - .05, sil[-1]['t'] + min(sil[-1]['dur'], 2.5) + .2))
pngs = []
for j, (txt, a, z) in enumerate(renglones):
    im = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0)); d = ImageDraw.Draw(im); w = d.textlength(txt, font=fuente)
    d.text(((1920 - w) / 2 + 2, 972), txt, font=fuente, fill=(0, 0, 0, 200)); d.text(((1920 - w) / 2, 970), txt, font=fuente, fill=(237, 230, 214, 255))
    q = os.path.join(tmp, f'letra-{j:02d}.png'); im.save(q); pngs.append((q, a, z))
im = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0)); ImageDraw.Draw(im).text((1800, 1040), '420048', font=chica, fill=(138, 138, 153, 255)); q = os.path.join(tmp, 'semilla.png'); im.save(q)
args = ['ffmpeg', '-n', '-v', 'error', '-i', mudo, '-i', audio]
for q_, a, z in pngs: args += ['-i', q_]
args += ['-i', q]
grafo, prev = [], '0:v'
for j, (q_, a, z) in enumerate(pngs): grafo.append(f"[{prev}][{j + 2}:v]overlay=0:0:enable='between(t,{a:.2f},{z:.2f})'[v{j}]"); prev = f'v{j}'
grafo.append(f"[{prev}][{len(pngs) + 2}:v]overlay=0:0[vf]")
guion = os.path.join(tmp, 'grafo.txt'); open(guion, 'w', encoding='utf-8').write(';\n'.join(grafo))
final = os.path.join(OUT, f'{nombre}-video-1920x1080.mp4'); ligero = os.path.join(OUT, f'{nombre}-video-1280x720.mp4')
subprocess.run(args + ['-filter_complex_script', guion, '-map', '[vf]', '-map', '1:a', '-c:v', 'libx264', '-crf', '18', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', final], check=True)
subprocess.run(['ffmpeg', '-n', '-v', 'error', '-i', final, '-vf', 'scale=1280:720', '-c:v', 'libx264', '-crf', '27', '-preset', 'slow', '-c:a', 'copy', '-movflags', '+faststart', ligero], check=True)
json.dump(dict(planos={k: dict(params=PLANOS[k][0], pluma=PLANOS[k][1], por_que=PLANOS[k][2]) for k in PLANOS}, letra=[dict(texto=t_, desde=round(a, 2), hasta=round(z, 2)) for t_, a, z in renglones]),
          open(os.path.join(OUT, 'video-planos.json'), 'x', encoding='utf-8'), ensure_ascii=False, indent=1)
for p in (final, ligero): print(p, round(os.path.getsize(p) / 2 ** 20, 1), 'MB')
