"""Cierra las capturas reales, GIF, receta y manifiesto. No renderiza video."""
import colorsys,io,os
from PIL import Image,ImageDraw,ImageFont,ImageOps
from comun import *
def main():
 out=ultimo();tag=out.name.split('-')[-1];P=jleer(out/'partitura.json');R=jleer(out/'red.json');mix=jleer(out/'mezcla-medidas.json');valid=jleer(out/'validacion-entrega.json')
 # Lámina final a partir de la red, eventos y la onda REAL del máster.
 im=Image.new('RGB',(1200,630),'#07151e');d=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',18);big=ImageFont.truetype('C:/Windows/Fonts/consolab.ttf',32)
 d.text((48,30),'EL LAGO QUE CANTA BAJO EL HIELO',font=big,fill='#e3f0f1');d.text((50,78),'227 / componer la llegada / Canek Zapata / 2026',font=font,fill='#7de9de')
 t=P['compas']*78;mem={a['id']:0 for a in R['aristas']}
 for e in P['grietas']:
  if e['t']<=t:mem[e['arista']]+=1
 for e in R['aristas']:
  pts=[(90+u*1000,140+(1-v)*370) for u,v in e['puntos']];h=(.5+(e['id']*.003+SEED*.001))%1;c=tuple(round(v*255) for v in colorsys.hsv_to_rgb(h,.4,.45+.4*min(1,mem[e['id']]/5)))
  if len(pts)>1:d.line(pts,fill=c,width=2)
 sr,y=wavfile.read(out/(out.name+'.wav'));mono=np.mean(y,axis=1);steps=np.linspace(0,len(mono)-1,1100).astype(int);wave=mono[steps];wave/=max(abs(wave).max(),1e-9)
 d.line([(50+i,550+v*25) for i,v in enumerate(wave)],fill='#7de9de',width=1);d.text((50,593),f'30 planos · {P["bpm"]:.2f} BPM · {P["duracion"]:.2f} s · magnitud / fase',font=font,fill='#bed0d7')
 buf=io.BytesIO();im.save(buf,format='PNG');guardar(out/f'el-lago-resultado-s227-{tag}.png',buf.getvalue());guardar(out/'og.png',buf.getvalue());guardar(out/'proceso'/f'07-campo-final-s227-{tag}.png',buf.getvalue())
 files=sorted((out/'proceso').glob('*.png'));frames=[]
 for p in files:
  img=Image.open(p).convert('RGB');frame=Image.new('RGB',(840,441),'#07151e');small=ImageOps.contain(img,(840,441));frame.paste(small,((840-small.width)//2,(441-small.height)//2));frames.append(frame.quantize(colors=128))
 gif=out/f'el-lago-proceso-s227-{tag}.gif'
 with gif.open('xb') as f:frames[0].save(f,format='GIF',save_all=True,append_images=frames[1:],duration=1100,loop=0,optimize=True)
 g=Image.open(gif);duration=0
 for i in range(g.n_frames):g.seek(i);duration+=g.info.get('duration',0);g.convert('RGB').load()
 assert duration<=10000 and gif.stat().st_size<=15*1024*1024
 stages=['Lámina original: alturas reales exportadas de Traspuesta.','Red y estados modales calculados antes de componer.','Ensayo de dispersión y compensación de fase, antes de la partitura.','Partitura efectiva de treinta planos.','Mezcla y espectrograma tras la lectura completa por Rejilla.','Un cuadro real de comprobación del visor y máscara de aristas.','Campo final de la red y onda del máster, sin interfaz.']
 md='# Proceso · El lago que canta bajo el hielo\n\nSemilla 227. Ejecución '+tag+'. Capturas guardadas durante etapas reales; el GIF reúne esas etapas, no es el video de la canción.\n\n'
 for i,p in enumerate(files):md+=f'{i+1}. [{p.name}]({p.name}) — {stages[min(i,len(stages)-1)]}\n'
 md+=f'\nGIF: {duration/1000:.2f} s, {gif.stat().st_size} bytes, {g.n_frames} cuadros, loop infinito.\n\nEl render del video completo queda a cargo de Canek mediante `hazvideo.py`.\n'
 guardar(out/'proceso/README.md',md.encode('utf-8'))
 code={str(p.relative_to(BASE)).replace('\\','/'):sha(p) for p in BASE.iterdir() if p.suffix in ['.py','.js','.cjs','.bat']};sources={str(p.relative_to(BASE)).replace('\\','/'):sha(p) for p in (BASE/'fuentes').rglob('*') if p.is_file() and '__pycache__' not in str(p)}
 recipe={'ejecucion':jleer(out/'ejecucion.json'),'codigo_sha256':code,'fuentes_fijadas':sources,'instrumentos':'instrumentos-5620a744f682','semilla':227,'estilos':['electro de Detroit','tintinnabuli a dos voces','desarrollo espectral','glitch'],'idea_D':'H_comp=exp(+i lambda r sqrt(w/alpha)); propagación H=exp(-i r sqrt(w/alpha)); lambda=1 cancela sólo dispersión de fase en banda limitada','modelo':{'placas':'Navier discreto, w=Delta w=0; eigenvalores de laplaciano al cuadrado','escala_espacial':1/32,'alpha':R['alpha'],'h':R['h'],'f0':P['f0'],'octavacion':P['f0']/R['placas'][0]['f0'],'acoplamiento':'resortes positivos entre modos fundamentales; parámetros artísticos','memoria':'umbrales e impulsos de control, no simulación termoelástica calibrada'},'audio':mix['aac'],'rejilla':mix['rejilla'],'validacion':valid,'GIF':{'segundos':duration/1000,'bytes':gif.stat().st_size,'cuadros':g.n_frames},'video_renderizado':False,'archivos':{str(p.relative_to(out)).replace('\\','/'):sha(p) for p in out.rglob('*') if p.is_file() and p.suffix not in ['.wav','.raw']}}
 jguardar(out/f'receta-el-lago-s227-{tag}.json',recipe)
 print('cerrado',out,'GIF',duration/1000,gif.stat().st_size)
if __name__=='__main__':main()
