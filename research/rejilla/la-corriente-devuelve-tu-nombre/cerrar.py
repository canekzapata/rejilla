"""Reúne etapas efectivamente capturadas, postal y receta. No produce video."""
from comun import *
from PIL import Image,ImageOps,ImageDraw,ImageFont
out=ultimo();tag=out.name.split('-')[-1];P=leer(out/'partitura.json');V=leer(out/'validacion.json')
src=next((out/'proceso').glob('08-hydra-*.png'));im=ImageOps.fit(Image.open(src).convert('RGB'),(1200,630));b=io.BytesIO();im.save(b,format='PNG')
for p in [out/f'la-corriente-campo-s{SEED}-{tag}.png',out/'og.png',out/'proceso'/f'09-resultado-s{SEED}-{tag}.png',BASE/'og.png']:guardar(p,b.getvalue())
files=sorted((out/'proceso').glob('[0-9][0-9]-*.png'));frames=[]
for p in files:
 v=Image.open(p).convert('RGB');frame=Image.new('RGB',(840,441),'#090b19');small=ImageOps.contain(v,frame.size);frame.paste(small,((840-small.width)//2,(441-small.height)//2));frames.append(frame.quantize(colors=128))
gif=out/f'la-corriente-proceso-s{SEED}-{tag}.gif'
with gif.open('xb') as f:frames[0].save(f,format='GIF',save_all=True,append_images=frames[1:],duration=1000,loop=0,optimize=True)
g=Image.open(gif);duration=0;contact=Image.new('RGB',(1260,741),'#090b19');d=ImageDraw.Draw(contact);font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',11)
for i in range(g.n_frames):
 g.seek(i);duration+=g.info['duration'];v=g.convert('RGB');v.load();v.thumbnail((420,221));x=i%3*420;y=i//3*247;contact.paste(v,(x,y));d.text((x+5,y+225),files[i].name[:50],font=font,fill='white')
assert duration<=10000 and gif.stat().st_size<=15*1024*1024 and g.info.get('loop')==0
buf=io.BytesIO();contact.save(buf,format='PNG');guardar(out/'proceso'/f'contacto-s{SEED}-{tag}.png',buf.getvalue())
stages=['Impulso real inicial del campo, antes del eco.','Trayectorias energéticas y diferencia efectiva, antes de componer.','Partitura escrita de treinta funciones, antes de sintetizar.','Prueba de voz y mbira, antes de la interpretación completa.','Primera mezcla real y espectrograma, antes de corregir la cola y reforzar el subgrave.','Revisión efectiva del subgrave de la salida, después de medir la primera mezcla.','Campo instantáneo de la comprobación del visor, antes del tratamiento Hydra.','Cuadro fijo real con Hydra activo y controles del máster final.','Postal derivada del cuadro anterior, recorte 1200×630 sin interfaz.']
md='# Proceso real de La corriente devuelve tu nombre\n\nSemilla '+str(SEED)+', ejecución '+tag+'. El GIF reúne etapas capturadas durante el trabajo; no es el video de la canción ni una evolución continua.\n\n'
for i,p in enumerate(files):md+=f'{i+1}. [{p.name}]({p.name}) — {stages[i]}\n'
md+=f'\nGIF: {duration/1000:.2f} s, {gif.stat().st_size} bytes, {g.n_frames} cuadros, loop infinito. Todos sus cuadros se decodificaron; revisar en la lámina de contacto.\n\nLa captura del visor es fija, en un punto del regreso. El video completo lo renderiza Canek con hazvideo.py. El primer máster se conserva; MASTER-VIGENTE.txt apunta a la revisión de grave y cola.\n';guardar(out/'proceso/README.md',md.encode('utf-8'))
delivery=f'''# La corriente devuelve tu nombre

Canek Zapata · 2026 · semilla {SEED}. 3:43.429 y treinta capas.

[Escuchar el máster vigente]({master(out).with_suffix('.m4a').name}) · [Salida pesada](salida-pesada-final-s{SEED}-{tag}.m4a) · [Solo D](solo-eco-D-final-s{SEED}-{tag}.m4a) · [Pulgares vocales](pulgares-vocales-final-s{SEED}-{tag}.m4a).

[PNG final](la-corriente-campo-s{SEED}-{tag}.png) · [GIF del proceso]({gif.name}) · [Etapas](proceso/README.md) · [Instrumentos, forma, referencias y límites](../README.md).

Audio final en MASTER-VIGENTE.txt. Los archivos sin «-pesada» son las mezclas previas conservadas. No se renderizó video: ejecutar ../hazvideo.py o abrir ../hazvideo.bat para producirlo. Verificación de entradas y cuadros fijos; duración completa del video sin probar. Las verificaciones no sustituyen la escucha de Canek.
''';guardar(out/'README.md',delivery.encode('utf-8'))
recipe={'ejecucion':leer(out/'ejecucion.json'),'partitura':{'segundos':P['duracion'],'capas':30,'eventos':sum(map(len,P['eventos'].values()))},'modelo':{'protocolo':leer(out/'eco.json')['convencion'],'modelo_finito':True,'modos':56,'T_por_tramo':8,'nu':.045},'validacion':V,'audio_revision':leer(out/'master-pesada.json'),'GIF':{'segundos':duration/1000,'cuadros':g.n_frames,'bytes':gif.stat().st_size,'loop':0},'fuentes_fijadas':leer(BASE/'procedencia.json'),'biblioteca':lib().name,'codigo_sha256':{str(p.relative_to(BASE)).replace('\\','/'):sha(p) for p in BASE.iterdir() if p.suffix in ['.py','.mjs','.js','.cjs','.html','.bat']},'archivos_sha256':{str(p.relative_to(out)).replace('\\','/'):sha(p) for p in out.rglob('*') if p.is_file() and p.suffix not in ['.wav','.mp4']},'video_renderizado':False,'audicion_propia':False}
jsave(out/f'receta-corriente-s{SEED}-{tag}.json',recipe);print('Cierre',gif,recipe['GIF'])
