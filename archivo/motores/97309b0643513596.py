"""Partitura + espectrograma del AAC entregado + pistas y referencia, sin modificar audio."""
from pathlib import Path
import json,sys,io,uuid,hashlib,subprocess,csv
import numpy as np
from scipy.signal import resample_poly
from scipy.fft import rfft
from scipy.io import wavfile
from PIL import Image,ImageDraw,ImageFont

R=Path(__file__).resolve().parent;REPO=R.parent
SOURCE=R/'otro-arriba-v2-s19102819-60aa3aba1d3a'
REF=REPO/'cuento-en-siete/cuento-en-siete-s1910-052e69cc9507'
SR=32000;FFT=8192;HOP=2048;FREQ=np.geomspace(40,12000,480)
W=1800;X=100;PW=1650;BG=(11,11,16);FG=(238,232,218);MUTED=(166,165,185)
COLORS={'voz':'#f19abb','rhodes':'#a491e8','bajo':'#a4cf68','trompeta':'#edb16b','sax':'#6cd2b7','chelo':'#6b8de3'}

def font(n):return ImageFont.truetype('C:/Windows/Fonts/consola.ttf',n)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def js(path,obj):
 with path.open('x',encoding='utf8') as f:json.dump(obj,f,ensure_ascii=False,indent=2)
def png(path,im):
 with path.open('xb') as f:im.save(f,'PNG')
def text(path,s):
 with path.open('x',encoding='utf8') as f:f.write(s)
def read_audio(path):
 if path.suffix=='.wav':
  sr,y=wavfile.read(path)
  if np.issubdtype(y.dtype,np.integer):y=y.astype(np.float32)/(np.iinfo(y.dtype).max+1)
  y=y.astype(np.float32)
  if y.ndim==1:y=y[:,None]
  if sr!=SR:
   from math import gcd
   g=gcd(sr,SR);y=resample_poly(y,SR//g,sr//g,axis=0)
 else:
  raw=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','f32le','-ar',str(SR),'-ac','2','-'],check=True,capture_output=True).stdout
  y=np.frombuffer(raw,np.float32).reshape(-1,2)
 assert np.isfinite(y).all();return y

def analyze(y):
 """Stereo power average avoids cancellation. One-sided peak-equivalent spectral amplitude."""
 y=np.pad(y,((FFT//2,FFT//2),(0,0)));win=np.hanning(FFT).astype(np.float32)
 count=(len(y)-FFT)//HOP+1;t=np.arange(count)*HOP/SR;grid=np.fft.rfftfreq(FFT,1/SR)
 pos=np.interp(FREQ,grid,np.arange(len(grid)));lo=np.floor(pos).astype(int);w=(pos-lo).astype(np.float32)
 S=np.zeros((len(FREQ),count),np.float32);bands=np.zeros((5,count),np.float32)
 edges=[40,120,350,2000,8000,12000]
 for start in range(0,count,64):
  stop=min(count,start+64);idx=np.arange(start,stop)[:,None]*HOP+np.arange(FFT)[None,:]
  power=np.zeros((stop-start,len(grid)),np.float32)
  for c in range(y.shape[1]):
   z=rfft(y[idx,c]*win,axis=1);power+=abs(z)**2/y.shape[1]*(2/win.sum())**2
  S[:,start:stop]=(power[:,lo]*(1-w)+power[:,lo+1]*w).T
  for k,(a,b) in enumerate(zip(edges[:-1],edges[1:])):bands[k,start:stop]=power[:,(grid>=a)&(grid<b)].sum(axis=1)
 return dict(t=t,power=S,bands=bands,db=10*np.log10(np.maximum(S,1e-14)))

def spec_image(db,width,height):
 # Fixed scale for every view; no per-frame or per-stem normalization.
 a=np.clip((db[::-1]+85)/65,0,1)**1.15
 rgb=np.asarray(BG)[None,None,:]*(1-a[:,:,None])+np.array([239,231,212])[None,None,:]*a[:,:,None]
 return Image.fromarray(rgb.astype(np.uint8)).resize((width,height),Image.Resampling.BILINEAR)

def sections(d,secs,dur,y0,y1,width=PW,x=X):
 for a,z,name in secs:
  xx=x+a/dur*width;d.line((xx,y0,xx,y1),fill=(60,60,78));d.text((xx+4,y0+4),name,font=font(12),fill=MUTED)
def freq_axis(d,y,h):
 for f in [50,100,250,500,1000,2000,5000,10000]:
  yy=y+h*(1-np.log(f/40)/np.log(12000/40));d.text((12,yy-7),f'{f//1000}k' if f>=1000 else str(f),font=font(13),fill=MUTED)
def time_axis(d,dur,y):
 for t in range(0,int(dur)+1,20):
  xx=X+t/dur*PW;d.text((xx-12,y),f'{t//60}:{t%60:02}',font=font(13),fill=MUTED)
def line(d,t,v,dur,y,h,color,maxv=1):
 pts=[(X+tt/dur*PW,y+h*(1-min(max(float(vv)/maxv,0),1))) for tt,vv in zip(t,v) if tt<=dur]
 if len(pts)>1:d.line(pts,fill=color,width=2)
def master_canvas(P,A=None,density=False):
 dur=P['duracion'];secs=[(s['t'],s['fin'],s['nombre']) for s in P['secciones']]
 im=Image.new('RGB',(W,1150),BG);d=ImageDraw.Draw(im)
 d.text((30,20),'OTRO ARRIBA · PARTITURA Y SONIDO',font=font(32),fill=FG)
 d.text((30,67),'Revisión 2 · 3:26 · semilla 19102819 · audio AAC entregado, sin modificar',font=font(18),fill=MUTED)
 d.text((30,109),'01  Notas escritas (altura); percusión y portadoras del coro se ven en el audio inferior',font=font(16),fill=FG)
 for k,c in COLORS.items():
  notes=([dict(t=e['t'],dur=e['dur'],m=e['nota']) for f in P['frases'] for e in f['eventos']] if k=='voz' else P[k])
  for e in notes:
   xx=X+e['t']/dur*PW;yy=365-(e['m']-28)/64*200
   d.line((xx,yy,xx+max(1,e['dur']/dur*PW),yy),fill=c,width=2)
 for m in [36,48,60,72,84]:d.text((15,365-(m-28)/64*200-8),f'MIDI {m}',font=font(12),fill=MUTED)
 sections(d,secs,dur,145,380);time_axis(d,dur,386)
 xx=100
 for k,c in COLORS.items():d.text((xx,423),k,font=font(15),fill=c);xx+=170
 d.text((30,464),'02  Espectrograma · frecuencia logarítmica · mismo brillo = mismo nivel espectral',font=font(18),fill=FG)
 if A is not None:im.paste(spec_image(A['db'],PW,370),(X,505))
 else:d.text((X+20,655),'Etapa 1: partitura leída; audio pendiente de analizar.',font=font(21),fill=MUTED)
 sections(d,secs,dur,505,875);freq_axis(d,505,370);time_axis(d,dur,883)
 for i,val in enumerate([-85,-70,-55,-40,-20]):
  xx=1060+i*135;v=np.clip((val+85)/65,0,1)**1.15;c=tuple((np.array(BG)*(1-v)+np.array([239,231,212])*v).astype(int));d.rectangle((xx,925,xx+25,940),fill=c);d.text((xx+31,922),str(val),font=font(13),fill=MUTED)
 d.text((30,923),'Brillo: dBFS por bin, ventana Hann de 256 ms; paso de 64 ms.',font=font(15),fill=MUTED)
 d.text((30,963),'03  Ocupación espectral · proporción de filas logarítmicas por encima de −60 dBFS',font=font(17),fill=FG)
 if A is not None and density:line(d,A['t'],(A['db']>-60).mean(axis=0),dur,1010,75,'#f19abb')
 d.text((20,1004),'100 %',font=font(12),fill=MUTED);d.text((30,1071),'0 %',font=font(12),fill=MUTED)
 d.text((100,1111),'Más blanco puede ser más nivel, ruido o resonancia. La gráfica acompaña la escucha.',font=font(16),fill=MUTED)
 return im

def init():
 P=json.loads((SOURCE/'partitura.json').read_text('utf8'));im=master_canvas(P)
 buf=io.BytesIO();im.save(buf,'PNG');nonce=uuid.uuid4().hex;full=hashlib.sha256(buf.getvalue()+Path(__file__).read_bytes()+nonce.encode()).hexdigest();tag=full[:12]
 out=R/f'lectura-densidad-s{P["semilla"]}-{tag}';out.mkdir();(out/'proceso').mkdir();(out/'fuentes').mkdir()
 png(out/'proceso'/f'01-partitura-leida-s{P["semilla"]}-{tag}.png',im)
 with (out/'fuentes'/f'analizar-densidad-{tag}.py').open('xb') as f:f.write(Path(__file__).read_bytes())
 js(out/'receta-inicial.json',dict(hash_ejecucion=full,nonce=nonce,imagen_sha256=hashlib.sha256(buf.getvalue()).hexdigest(),programa_sha256=sha(Path(__file__)),semilla=P['semilla'],pieza=str(SOURCE.relative_to(REPO)),referencia=str(REF.relative_to(REPO)),fecha='2026-10-19'))
 print(out,flush=True)

def main(out):
 tag=out.name.split('-')[-1];P=json.loads((SOURCE/'partitura.json').read_text('utf8'));seed=P['semilla'];dur=P['duracion'];files={}
 def read(path):files[str(path.relative_to(REPO))]=sha(path);return read_audio(path)
 master=SOURCE/f'{SOURCE.name}.m4a';y=read(master);A=analyze(y)
 png(out/'proceso'/f'02-audio-transformado-s{seed}-{tag}.png',master_canvas(P,A))
 print('Espectrograma de la entrega calculado',flush=True)
 full=master_canvas(P,A,True);png(out/f'otro-arriba-partitura-espectrograma-s{seed}-{tag}.png',full);png(out/'proceso'/f'03-densidad-medida-s{seed}-{tag}.png',full)
 secs=[(s['t'],s['fin'],s['nombre']) for s in P['secciones']]
 gain=json.loads((SOURCE/'verificacion.json').read_text('utf8'))['ganancias']
 rows=[('voz-principal','Voz principal'),('coro','Coro / vocoders'),('rhodes','Rhodes'),('bajo','Bajo fretless'),('trompeta','Trompeta cup'),('sax','Sax'),('chelo','Chelo'),('piano','Piano preparado'),('sinte','Sinte'),('garganta','Garganta'),('vocal-hecha-armonia','Campo armónico'),('dembow','Percusión')]
 sheet=Image.new('RGB',(W,150+len(rows)*145),BG);d=ImageDraw.Draw(sheet)
 d.text((25,16),'OTRO ARRIBA · DENSIDAD POR INSTRUMENTO',font=font(29),fill=FG)
 d.text((25,62),'Pistas aisladas × ganancia nominal. Escala fija −85 a −20 dBFS; 40 Hz–12 kHz en cada fila.',font=font(17),fill=MUTED)
 d.text((25,91),'Antes del ducking, las reflexiones compartidas y el ajuste global del máster; no suman el AAC final.',font=font(15),fill=MUTED)
 stats={}
 for j,(k,label) in enumerate(rows):
  path=SOURCE/'render'/f'{k}-60aa3aba1d3a.wav';z=read(path)*gain[k];B=analyze(z);yy=145+j*145
  sheet.paste(spec_image(B['db'],PW,112),(X,yy));d.text((X+5,yy+5),label,font=font(15),fill='#cfc9f1');freq_axis(d,yy,112);sections(d,secs,dur,yy,yy+112)
  stats[k]=float((B['db']>-60).mean());print('Pista',k,flush=True)
 time_axis(d,dur,sheet.height-28);png(out/f'otro-arriba-espectrogramas-por-instrumento-s{seed}-{tag}.png',sheet)
 # Compare complete deliveries after ONE active-RMS gain per piece; preserve section dynamics.
 q=json.loads((REF/'partitura.json').read_text('utf8'));ref=read(REF/f'{REF.name}.m4a');B=analyze(ref)
 def active_rms(z):
  n=SR//5;a=z[:len(z)//n*n].reshape(-1,n,z.shape[1]);r=np.sqrt(np.mean(a*a,axis=(1,2)));return float(np.sqrt(np.mean(r[r>10**(-45/20)]**2)))
 comparison=Image.new('RGB',(W,1130),BG);d=ImageDraw.Draw(comparison)
 d.text((25,18),'DOS FORMAS DE OCUPAR EL SONIDO',font=font(34),fill=FG)
 d.text((25,67),'Misma escala de frecuencia y brillo. Un ajuste global de RMS activo por pieza; sin ajustar secciones.',font=font(16),fill=MUTED)
 report={};reference_sects={}
 for c in q['compases']:
  a,z=reference_sects.get(c[2],(c[0]*q['semicorchea'],0));reference_sects[c[2]]=(a,(c[0]+c[1])*q['semicorchea'])
 names=['I espectro','II invención','III coro','IV dúo','V coro','VI coda'];refsecs=[(a,z,names[j]) for j,(a,z) in enumerate(reference_sects.values())]
 for j,(name,z,aa,ss,dd) in enumerate([('Cuento en siete · 2:22',ref,B,refsecs,q['duracion']),('Otro arriba · revisión 2 · 3:26',y,A,secs,dur)]):
  g=10**(-18/20)/active_rms(z);db=aa['db']+20*np.log10(g);yy=145+j*470
  d.text((25,yy-34),name,font=font(23),fill=FG);comparison.paste(spec_image(db,PW,300),(X,yy));freq_axis(d,yy,300);sections(d,ss,dd,yy,yy+300)
  line(d,aa['t'],(db>-60).mean(axis=0),dd,yy+332,70,'#e8b888');d.text((X,yy+410),'0 %',font=font(13),fill=MUTED);d.text((X+PW-45,yy+410),'100 %',font=font(13),fill=MUTED)
  report[name]=dict(ganancia_analisis_db=float(20*np.log10(g)),rms_activo_fuente=active_rms(z),ocupacion_media=float((db>-60).mean()))
 d.text((25,1095),'Horizontal: proporción de cada pieza. Debajo: ocupación sobre −60 dBFS; no es una medida de complejidad musical.',font=font(15),fill=MUTED)
 png(out/f'cuento-y-otro-arriba-comparacion-s{seed}-{tag}.png',comparison)
 # Values remain available, with units and thresholds, rather than only a raster plot.
 csvpath=out/f'otro-arriba-densidad-y-bandas-s{seed}-{tag}.csv'
 with csvpath.open('x',newline='',encoding='utf8') as f:
  writer=csv.writer(f);writer.writerow(['tiempo_s','ocupacion_log_40_12000_sobre_menos60dBFS','energia_40_120','energia_120_350','energia_350_2000','energia_2000_8000','energia_8000_12000'])
  for i,t in enumerate(A['t']):
   if t<=dur:writer.writerow([round(float(t),4),float((A['db'][:,i]>-60).mean()),*map(float,A['bands'][:,i]/(A['bands'][:,i].sum()+1e-20))])
 summaries={}
 for s in P['secciones']:
  ix=(A['t']>=s['t'])&(A['t']<s['fin']);v=(A['db'][:,ix]>-60).mean(axis=0)
  summaries[s['nombre']]=dict(inicio=s['t'],fin=s['fin'],ocupacion_media=float(v.mean()),p10=float(np.quantile(v,.1)),p90=float(np.quantile(v,.9)))
 js(out/'medidas.json',dict(sr=SR,fft=FFT,ventana='Hann',hop=HOP,frecuencias_hz=[40,12000],filas_log=480,rango_brillo_dbfs=[-85,-20],umbral_ocupacion_dbfs=-60,metodo='Potencia estéreo media; FFT unilateral / suma de ventana × 2; interpolación lineal de potencia a filas logarítmicas. Bandas calculadas en bins lineales, no contando pixeles. No se promedian canales antes de elevar al cuadrado.',secciones=summaries,comparacion=report,pistas_ocupacion_nominal=stats,fuentes_sha256=files,sin_escucha_propia=True))
 assert all(sha(REPO/k)==v for k,v in files.items())
 # Genuine calculation stages, captured as they became available, not fabricated synthesis steps.
 frames=[Image.open(x).convert('RGB').resize((1200,767)) for x in sorted((out/'proceso').glob('0[123]-*.png'))]
 palette=frames[-1].quantize(colors=96);frames=[x.quantize(palette=palette) for x in frames]
 gif=out/f'proceso-lectura-densidad-s{seed}-{tag}.gif'
 with gif.open('xb') as f:frames[0].save(f,format='GIF',save_all=True,append_images=frames[1:],duration=2400,loop=0,optimize=False)
 contact=Image.new('RGB',(1200,768),BG);duration=0
 with Image.open(gif) as g:
  for i in range(g.n_frames):g.seek(i);duration+=g.info['duration'];contact.paste(g.convert('RGB').resize((600,384)),((i%2)*600,(i//2)*384))
 assert duration<=10000 and gif.stat().st_size<=15*1024**2;png(out/'proceso'/f'04-revision-gif-s{seed}-{tag}.png',contact)
 png(out/'og.png',full.crop((0,425,W,945)).resize((1200,630)))
 text(out/'proceso/README.md',f'# Etapas reales de análisis\n\n01: partitura cargada antes de decodificar el audio.\n02: AAC entregado convertido a espectrograma; curva todavía pendiente.\n03: ocupación calculada con umbral fijo y añadida al mismo eje temporal.\n04: hoja de cuadros decodificados del GIF para revisión; no forma parte de la animación.\n\nSemilla de la composición {seed}; análisis determinista, sin nueva aleatoriedad. GIF: {duration/1000} s, {gif.stat().st_size} bytes. No se presenta como proceso de composición ni de síntesis de una canción nueva.\n')
 text(out/'README.md',f'# Otro arriba · leer la densidad\n\nAnálisis del 19 de octubre de 2026, pedido por Canek al mostrar la gráfica de Cuento en siete y decir que esa composición le gusta mucho. Ejecución {tag}; semilla de la composición {seed}. No se cambió ningún audio.\n\n- [Partitura y audio](otro-arriba-partitura-espectrograma-s{seed}-{tag}.png). Notas escritas arriba, espectrograma del AAC entregado en medio y ocupación espectral debajo.\n- [Pistas por separado](otro-arriba-espectrogramas-por-instrumento-s{seed}-{tag}.png). Ganancia nominal de la mezcla, antes de ducking, reflexiones y ajuste global del máster. Misma escala fija en todas las pistas; no normalización individual.\n- [Comparar con Cuento en siete](cuento-y-otro-arriba-comparacion-s{seed}-{tag}.png). AAC reales, potencia estéreo, misma escala, frecuencia y duración relativa. Sólo para esta comparación se aplica un ajuste global por obra a RMS activo −18 dBFS (ventanas 200 ms sobre −45 dBFS). No altera dinámicas entre secciones ni produce un audio nuevo.\n- [Datos CSV](otro-arriba-densidad-y-bandas-s{seed}-{tag}.csv) y [método y medidas](medidas.json).\n- [GIF de cálculo](proceso-lectura-densidad-s{seed}-{tag}.gif) y [etapas](proceso/README.md).\n\n## Leer las gráficas\n\nEl tiempo avanza a la derecha; graves abajo y agudos arriba en escala logarítmica de 40 Hz a 12 kHz. Brillo fijo −85 a −20 dBFS por bin FFT, con amplitud equivalente de seno pico y sin corrección de scalloping. Líneas horizontales: componentes sostenidas; trazos verticales: ataques o transitorios; bandas difusas: contenido repartido. La ventana de 256 ms alisa ataques rápidos; paso de 64 ms.\n\nLa ocupación cuenta la proporción de 480 filas logarítmicas con nivel superior a −60 dBFS en cada instante. Depende del umbral, volumen y timbre: no equivale al número de voces, inteligibilidad, dificultad o calidad. Las bandas CSV son fracciones de energía espectral, calculadas sobre bins lineales entre 40 Hz y 12 kHz. Las frecuencias bajo 40 Hz y sobre 12 kHz quedan fuera de estas vistas.\n\nLa partitura superior omite percusión y portadoras del coro; aparecen en el espectrograma y en las pistas separadas. La comparación usa proporción de duración porque las obras duran distinto, no una alineación de sus compases. Originales intactos comprobados por SHA-256; fuentes, imagen inicial, versión del programa y nonce guardados. No se hizo escucha propia.\n')
 js(out/'receta-final.json',dict(hash_ejecucion=json.loads((out/'receta-inicial.json').read_text('utf8'))['hash_ejecucion'],archivos={str(x.relative_to(out)):sha(x) for x in out.rglob('*') if x.is_file()},gif_duracion_ms=duration,gif_bytes=gif.stat().st_size,fuentes_intactas=True))
 print('TERMINADO',out,flush=True)

if __name__=='__main__':
 if len(sys.argv)==1:init()
 else:main(Path(sys.argv[1]).resolve())
