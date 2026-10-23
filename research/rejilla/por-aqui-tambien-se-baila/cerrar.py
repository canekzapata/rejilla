"""Cerrar sólo partitura e instrumentos: GIF real, PNG, receta y parada de revisión."""
from comun import *
from PIL import Image,ImageOps,ImageDraw
def main():
 out=ultimo();tag=out.name.split('-')[-1];P=leer(score());T=leer(out/'datos/terreno-22.json');stages=list((out/'proceso').glob('*.png'))
 # Mantener el orden efectivo de captura, incluyendo las revisiones conservadas.
 stages.sort(key=lambda p:p.stat().st_mtime_ns);selected=[p for p in stages if not p.name.startswith(('04b-','05b-'))];frames=[]
 for p in selected:
  with Image.open(p) as im:
   im.verify()
  with Image.open(p) as im:
   fr=Image.new('RGB',(900,510),T['papel']);v=ImageOps.contain(im.convert('RGB'),(900,472),Image.Resampling.LANCZOS);fr.paste(v,((900-v.width)//2,(472-v.height)//2));ImageDraw.Draw(fr).text((18,486),p.name.split('-s22-')[0].replace('-',' '),fill=T['plumas'][0]);frames.append(fr.quantize(colors=128))
 b=io.BytesIO();ms=(9000//len(frames)//10)*10;frames[0].save(b,format='GIF',save_all=True,append_images=frames[1:],duration=ms,loop=0,optimize=True,disposal=2);gif=out/f'por-aqui-proceso-primera-etapa-s{SEED}-{tag}.gif';guardar(gif,b.getvalue());assert gif.stat().st_size<15*1024*1024
 with Image.open(gif) as im:
  total=0
  for k in range(im.n_frames):im.seek(k);total+=im.info['duration']
  assert total<=10000 and im.info.get('loop')==0
 with Image.open(next((out/'proceso').glob('07-*.png'))) as im:
  final=ImageOps.fit(im.convert('RGB'),(1200,630));b=io.BytesIO();final.save(b,format='PNG');guardar(out/f'por-aqui-lamina-s{SEED}-{tag}.png',b.getvalue());guardar(out/'og.png',b.getvalue())
 contact=Image.new('RGB',(1200,340*((len(frames)+3)//4)),T['papel'])
 for i,fr in enumerate(frames):contact.paste(fr.resize((300,170)),((i%4)*300,(i//4)*340))
 # Contacto compacto para verificar todos los cuadros del GIF.
 contact=Image.new('RGB',(1200,170*((len(frames)+3)//4)),T['papel'])
 for i,fr in enumerate(frames):contact.paste(fr.resize((300,170)),((i%4)*300,(i//4)*170))
 b=io.BytesIO();contact.save(b,format='PNG');guardar(out/f'por-aqui-contacto-s{SEED}-{tag}.png',b.getvalue())
 text='# Proceso real de la primera etapa\n\nSemilla 22; versión '+VERSION+'; ejecución '+tag+'. Capturas conservadas durante el trabajo; no se fabricaron borradores retrospectivos. El GIF sigue el orden efectivo de captura:\n\n'
 for i,p in enumerate(selected,1):text+=f'{i}. `{p.name}`\n'
 text+='''
01 y 02 son los primeros bocetos de lectura del raster; su superposición tenía orientación incorrecta. 02b corrige las coordenadas y reduce la magnificación del depósito de >400 a 29.12 m. El SVG de Traspuesta permanece intacto y su captura real es 07. 04, 04b y 04c conservan la evolución desde retrasos simples hasta fase local integrada y el modelo de depósito revisado; el GIF selecciona principio y versión vigente. 05/05b muestran la sonda de membrana (sin cambio del modelo); se selecciona la primera. 06 y 06b comparan el láser antes/después de revisar la geometría. 08 es una página realmente rasterizada del PDF.

El GIF reúne estados y revisiones, no reproduce la canción. La foto/PNG de entrega y og.png proceden de la propia lámina 22. No se implementó aún el preset final ni se renderizó un video musical. Los PDF/sondas están para revisión con Canek; la producción completa se detuvo en esta etapa por instrucción suya.
''';guardar(out/'proceso/README.md',text.encode('utf8'))
 # Guion de la siguiente etapa: datos escritos, sin implementar o renderizar el visor.
 jsave(out/'coreografia-borrador.json',{'estado':'guion para revisión; no implementado','visor':'research/montanas-topograficas/musica.html?reloj=manual','semilla':22,'preset_propuesto':'transbordo','fuentes':['traza de tráfico','estado de depósitos','reloj de partitura'],'escenas':[{'id':s['id'],'t':s['t'],'t1':s['t1'],'nombre':s['nombre'],'vista':'normal' if s['id'] in ['I','IX'] else 'cascada' if s['id'] in ['IV','VI','VIII'] else 'mixto','tratamiento':'transbordo' if s['id'] in ['IV','V','VI'] else 'curvas' if s['id']=='IX' else 'diferencia' if s['id']=='VII' else 'eco'} for s in P['secciones']],'video_completo':'Canek lo renderizará; hazvideo.py en la fase posterior'})
 jsave(out/'proceso-medidas.json',{'etapas_GIF':len(frames),'GIF_ms':total,'GIF_bytes':gif.stat().st_size,'loop':0,'orden':[p.name for p in selected],'master_producido':False,'video_renderizado':False})
 guardar(out/'PARADA-PARA-REVISION.md',b'# Parada acordada\n\nPartitura e instrumentos entregados para revisar con Canek. No continuar a producir el master completo ni el video antes de esa revision.\n')
 files={str(p.relative_to(out)).replace('\\','/'):sha(p) for p in sorted(out.rglob('*')) if p.is_file()};code={p.name:sha(p) for p in sorted(BASE.iterdir()) if p.is_file() and p.suffix in ['.py','.cjs','.md']};jsave(out/'receta.json',{'ejecucion':leer(out/'ejecucion.json'),'etapa':'partitura e instrumentos para revisar; parada antes del master','artefactos_sha256':files,'codigo_sha256':code,'fuentes_sha256':leer(BASE/'procedencia.json')['fuentes'],'biblioteca':leer(lib()/'manifiesto.json')['huella'],'partitura_vigente':score().name,'deposito_vigente':depo().name,'proceso':leer(out/'proceso-medidas.json'),'validacion':leer(out/'validacion-primera-etapa-r2.json'),'git_loop1':'578bf51','audicion_propia':False,'video_renderizado':False});print(gif.name,len(frames),total,gif.stat().st_size,len(files))
if __name__=='__main__':main()
