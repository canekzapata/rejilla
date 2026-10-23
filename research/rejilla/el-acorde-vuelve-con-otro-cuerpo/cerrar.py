"""Entregar PNG, GIF de etapas efectivas y receta con huellas; jamás un video."""
from comun import *
from PIL import Image,ImageOps,ImageDraw
def main():
 out=ultimo();tag=out.name.split('-')[-1];stages=sorted((out/'proceso').glob('*.png'));assert len(stages)==9,len(stages)
 for p in stages:
  with Image.open(p) as im:im.verify()
 # Un cuadro propio de Hydra, sin controles, como resultado/OG. Recorte declarado.
 with Image.open(next((out/'proceso').glob('08-*.png'))) as im:
  final=ImageOps.fit(im.convert('RGB'),(1200,630),method=Image.Resampling.LANCZOS);b=io.BytesIO();final.save(b,format='PNG');data=b.getvalue();guardar(out/f'el-acorde-campo-s{SEED}-{tag}.png',data);guardar(out/'og.png',data);b=io.BytesIO();ImageOps.fit(final,(64,64)).save(b,format='PNG');guardar(out/'favicon.png',b.getvalue())
 frames=[]
 for p in stages:
  with Image.open(p) as im:
   frame=Image.new('RGB',(900,520),'#10191f');view=ImageOps.contain(im.convert('RGB'),(900,480),Image.Resampling.LANCZOS);frame.paste(view,((900-view.width)//2,(480-view.height)//2));ImageDraw.Draw(frame).text((16,494),p.name.split('-s21102681')[0].replace('-',' '),fill='#e9ded1');frames.append(frame.quantize(colors=128))
 b=io.BytesIO();frames[0].save(b,format='GIF',save_all=True,append_images=frames[1:],duration=1000,loop=0,optimize=True,disposal=2);gif=out/f'el-acorde-proceso-s{SEED}-{tag}.gif';guardar(gif,b.getvalue())
 with Image.open(gif) as im:
  duration=0
  for i in range(im.n_frames):im.seek(i);duration+=im.info.get('duration',0)
  assert duration<=10000 and im.info.get('loop')==0
 assert gif.stat().st_size<15*1024*1024
 # Lámina de contacto para comprobar también todos los estados del GIF.
 sheet=Image.new('RGB',(900,520*3),'#10191f')
 for i,fr in enumerate(frames):sheet.paste(fr.resize((300,173)),((i%3)*300,(i//3)*520))
 # Compactar la lámina: las tres filas conservan cada estado real, sin huecos.
 sheet=Image.new('RGB',(900,519),'#10191f')
 for i,fr in enumerate(frames):sheet.paste(fr.resize((300,173)),((i%3)*300,(i//3)*173))
 b=io.BytesIO();sheet.save(b,format='PNG');guardar(out/f'el-acorde-contacto-s{SEED}-{tag}.png',b.getvalue())
 text='''# Proceso real: El acorde vuelve con otro cuerpo

Semilla **21102681**, ejecución **765c608846ec**, versión acorde-1.0.0. Cada imagen se guardó después de la etapa correspondiente; no son borradores reconstruidos retrospectivamente.

1. **01, coma y batido:** cálculo y señal de referencia 110/111.375 Hz. Esta imagen, versión, código inicial y nonce originan el SHA de ejecución.
2. **02, partitura:** eventos escritos de las treinta capas y sus relevos, antes de sintetizar.
3. **03, pruebas de instrumentos:** medidas de notas largas de los dos pianos originales y prueba estacionaria del fuelle a dos presiones.
4. **04, fuentes reales:** capturas de las señales sintetizadas, antes de la mezcla: cruces y tres ventanas humanas.
5. **05, mezcla y Rejilla:** forma/espectro de la mezcla que pasó por magnitud/fase y spectrumsynth, con cierre de cola.
6. **06, campo antes de Hydra:** lienzo fuente en el cruce de registros, sin el tratamiento de Hydra.
7. **07, cruce de registros:** cuadro de Hydra de la misma escena.
8. **08, Hydra coma:** cuadro de otro instante del preset, durante el solo D.
9. **09, memoria de la coda:** cuadro fijo del relevo a los resonadores.

El GIF reúne esos nueve estados, un segundo cada uno: **9 s, loop infinito**. Los tres últimos cuadros comparan instantes distintos del mismo visor, no revisiones del programa. El PNG final/og.png recorta el cuadro 08 a 1200×630. La lámina de contacto permite revisar todos los estados.

Se comprobaron sólo cuadros fijos. Ningún video/MP4 fue renderizado; `hazvideo.py` queda para Canek. Los nombres existentes se rechazan al escribir. Las imágenes de magnitud/fase de Rejilla se guardan aparte de estos nueve PNGs.
'''
 guardar(out/'proceso/README.md',text.encode('utf8'))
 jsave(out/'proceso-medidas.json',{'etapas':len(stages),'GIF_ms':duration,'GIF_bytes':gif.stat().st_size,'loop':0,'cuadros_verificados':9,'video_renderizado':False})
 files={str(p.relative_to(out)).replace('\\','/'):sha(p) for p in sorted(out.rglob('*')) if p.is_file()};code={p.name:sha(p) for p in sorted(BASE.iterdir()) if p.is_file() and p.suffix in ['.py','.js','.cjs','.mjs','.html','.bat','.md']}
 jsave(out/'receta.json',{'ejecucion':leer(out/'ejecucion.json'),'artefactos_sha256':files,'codigo_sha256':code,'git_loop1':'0898a35','biblioteca':leer(lib()/'manifiesto.json')['huella'],'metodo_rejilla':leer(out/'mezcla-medidas.json')['rejilla'],'audio':leer(out/'validacion.json')['master'],'licencia_hydra':'fuentes/hydra/LICENCIA-HYDRA-LICENSE','video_renderizado':False,'limites':['sin audición propia','fuelle fenomenológico no calibrado','geometría visual interpretativa','URL propuesta sin publicación']})
 print(gif,duration,gif.stat().st_size,len(files))
if __name__=='__main__':main()
