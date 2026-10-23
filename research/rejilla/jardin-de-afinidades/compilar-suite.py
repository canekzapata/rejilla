"""Escucha seguida de I–V. Ensambla las entregas, sin reescribir sus mezclas."""
from pathlib import Path
import hashlib,json,os,subprocess
import numpy as np
from scipy.io import wavfile
import matplotlib.pyplot as plt
from PIL import Image
import preludio as util
ROOT=Path(__file__).resolve().parent;FF='C:/msys64/mingw64/bin/ffmpeg.exe';SR=48000
TRACKS=[
 ('I. Una puerta entreabierta','preludio-tiempo-vivo-s1610264-cea27f08b9a5','#e9cd95'),
 ('II. Aprender a irse','invencion-impulso-s1610265-0ca858b3c0a3','#b8a6db'),
 ('III. Raíces del mismo cielo','coral-respiracion-s1610266-ae4848ead9bd','#9fcba9'),
 ('IV. Lo que salta de una rama','scherzo-lo-que-salta-s1610267-49d415932ce1','#ec9e8b'),
 ('V. Cada quien guarda otra luz','postludio-cada-quien-guarda-s1610268-73596a5d8dc1','#9dc2e3')]
def run(args):
 r=subprocess.run(args,capture_output=True,text=True,encoding='utf8',errors='replace');assert r.returncode==0,r.stderr;return r
def title(fig,s):
 fig.suptitle('JARDÍN DE AFINIDADES / '+s,x=.06,ha='left',fontsize=17)
 fig.text(.06,.025,'Canek Zapata · suite en cinco movimientos · escucha seguida · 16 de octubre de 2026',fontsize=10)
 fig.tight_layout(rect=(.035,.06,.985,.91))
def main():
 tracks=[];cursor=0
 for i,(name,folder,color) in enumerate(TRACKS):
  p=ROOT/folder;audio=next(p.glob('*.m4a'));v=json.loads((p/'verificacion.json').read_text(encoding='utf8'));duration=v['duracion_decodificada']
  tracks.append({'titulo':name,'carpeta':folder,'audio':str(audio),'inicio_s':cursor,'duracion_s':duration,'color':color,'audio_sha256':util.sha(audio)})
  cursor+=duration+(1 if i<4 else 0)
 fig,ax=plt.subplots(figsize=(12,6.3),dpi=100)
 for i,t in enumerate(tracks):
  ax.barh(4-i,t['duracion_s'],left=t['inicio_s'],height=.5,color=t['color']);ax.text(t['inicio_s']+1,4-i+.32,t['titulo'],fontsize=10)
 ax.set(xlim=(0,cursor+3),ylim=(-.6,5),yticks=[],xlabel='segundos · un segundo adicional entre movimientos');title(fig,'01 / orden antes de ensamblar');fig.canvas.draw();nonce=os.urandom(24).hex()
 digest=hashlib.sha256(bytes(fig.canvas.buffer_rgba())+Path(__file__).read_bytes()+json.dumps(tracks).encode()+nonce.encode()).hexdigest();tag=digest[:12]
 out=ROOT/f'suite-jardin-de-afinidades-{tag}';out.mkdir(exist_ok=False);(out/'proceso').mkdir()
 util.png(out/'proceso'/f'01-orden-suite-{tag}.png',fig)
 util.dump(out/'receta-inicial.json',{'id':digest,'nonce':nonce,'fuente_sha256':util.sha(Path(__file__)),'movimientos':tracks,'pausa_extra_s':1})
 print(out,flush=True)
 inputs=[];filters=[]
 for i,t in enumerate(tracks):
  inputs+=['-i',t['audio']];filters.append(f'[{i}:a]aresample=48000'+(',apad=pad_dur=1' if i<4 else '')+f'[a{i}]')
 filters.append(''.join(f'[a{i}]' for i in range(5))+'concat=n=5:v=0:a=1[out]')
 base=f'jardin-de-afinidades-suite-{tag}';wp=out/(base+'.wav')
 run([FF,'-hide_banner','-nostdin','-n',*inputs,'-filter_complex',';'.join(filters),'-map','[out]','-c:a','pcm_f32le',str(wp)])
 sr,x=wavfile.read(wp,mmap=True);assert sr==SR and x.ndim==2
 w=12000;times=[];energy=[];peak=0
 for a in range(0,len(x),w):
  block=x[a:a+w].astype(float);assert np.isfinite(block).all();times.append(a/SR);energy.append(float(np.sqrt(np.mean(block*block))));peak=max(peak,float(np.max(np.abs(block))))
 assert peak<1 and abs(len(x)/SR-cursor)<.2
 fig,ax=plt.subplots(figsize=(12,6.3),dpi=100);ax.plot(times,energy,color='#e3dac5',lw=.8)
 for t in tracks:ax.axvspan(t['inicio_s'],t['inicio_s']+t['duracion_s'],color=t['color'],alpha=.12)
 ax.set(xlim=(0,cursor),xlabel='segundos',ylabel='RMS del WAV ensamblado · 250 ms');title(fig,'02 / ensamblaje real de las cinco entregas');util.png(out/'proceso'/f'02-ensamblaje-suite-{tag}.png',fig)
 metadata=';FFMETADATA1\ntitle=Jardín de afinidades\nartist=Canek Zapata\nalbum=Jardín de afinidades\ndate=2026\n'
 for t in tracks:metadata+=f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={round(t['inicio_s']*1000)}\nEND={round((t['inicio_s']+t['duracion_s'])*1000)}\ntitle={t['titulo']}\n"
 util.textfile(out/'capitulos.txt',metadata)
 run([FF,'-hide_banner','-nostdin','-n','-i',str(wp),'-i',str(out/'capitulos.txt'),'-map_metadata','1','-map_chapters','1','-c:a','aac','-b:a','256k','-movflags','+faststart',str(out/(base+'.m4a'))])
 r=run([FF,'-hide_banner','-nostdin','-i',str(out/(base+'.m4a')),'-af','loudnorm=I=-18:TP=-2:LRA=20:print_format=json','-f','null','-']);meter=json.JSONDecoder().raw_decode(r.stderr[r.stderr.rfind('{'):])[0]
 assert float(meter['input_tp'])<0
 fig,axes=plt.subplots(2,1,figsize=(12,6.3),dpi=100)
 for i,t in enumerate(tracks):
  axes[0].text(.02,.92-i*.18,f"{int(t['inicio_s']//60):02}:{int(t['inicio_s']%60):02}   {t['titulo']}",transform=axes[0].transAxes,color=t['color'],fontsize=14)
 axes[0].axis('off');axes[1].plot(times,energy,color='#e3dac5',lw=.8)
 for t in tracks:axes[1].axvspan(t['inicio_s'],t['inicio_s']+t['duracion_s'],color=t['color'],alpha=.13)
 axes[1].set(xlim=(0,cursor),xlabel='segundos · energía del ensamblaje',ylabel='RMS');title(fig,'03 / escucha completa, con capítulos')
 final=out/f'suite-jardin-resultado-{tag}.png';util.png(final,fig)
 with Image.open(final) as im:
  for p in [out/'og.png',out/'proceso'/f'03-escucha-suite-{tag}.png']:
   with p.open('xb') as f:im.save(f,'PNG')
 frames=[]
 for p in sorted((out/'proceso').glob('*.png')):
  with Image.open(p) as im:frames.append(im.convert('RGB').resize((900,472)).quantize(colors=128))
 gif=out/f'suite-jardin-proceso-{tag}.gif'
 with gif.open('xb') as f:frames[0].save(f,format='GIF',save_all=True,append_images=frames[1:],duration=2600,loop=0,optimize=False)
 with Image.open(gif) as im:
  canvas=Image.new('RGB',(1200,210));duration=0
  for i in range(im.n_frames):im.seek(i);duration+=im.info['duration'];canvas.paste(im.convert('RGB').resize((400,210)),(i*400,0))
  assert im.n_frames==3 and duration==7800 and gif.stat().st_size<15_000_000
  with (out/'proceso'/f'04-revision-suite-{tag}.png').open('xb') as f:canvas.save(f,'PNG')
 util.dump(out/'verificacion.json',{'duracion_WAV_s':len(x)/SR,'AAC':meter,'pico_muestra_WAV':peak,'metodo':'Fuentes AAC decodificadas, remuestreadas a48000 y concatenadas con1 s extra entre movimientos. Sin sumar señales ni igualar sonoridades. El medidor decodifica AAC para analizarlo; campos input son reales.','escucha':'Sin escucha humana durante el ensamblaje.'})
 util.textfile(out/'proceso'/'README.md','# Etapas reales del ensamblaje\n\n1. Orden y duraciones antes de unir audio.\n2. Energía del WAV ya concatenado, antes del AAC.\n3. Capítulos y la misma energía del WAV; el AAC final se midió aparte.\n4. Revisión de cuadros del GIF.\n\nGIF de7.8 s,tres etapas. No reconstruye la composición de los movimientos: cada uno conserva su proceso propio.\n')
 util.textfile(out/'README.md',f'# Jardín de afinidades — escucha seguida\n\nCanek Zapata,16 de octubre de2026. {int(cursor//60)}:{int(round(cursor%60)):02}. Cinco movimientos en orden, con capítulos y un segundo adicional entre cada uno. Se usan las revisiones actuales de I–III y las primeras entregas de IV–V. No se modifica su balance ni su dinámica; es una escucha de trabajo del conjunto.\n\nAudio {base}.m4a. WAV flotante local excluido de git. Fuentes y hashes en receta-inicial.json,capítulos en capitulos.txt. PNG,og.png1200×630 y GIF de ensamblaje7.8 s. Cada movimiento tiene su propio proceso y receta en la carpeta indicada. Sin publicación remota ni escucha humana durante el ensamblaje.\n')
 with (out/'compilar-suite-fuente.py').open('xb') as f:f.write(Path(__file__).read_bytes())
 util.dump(out/'receta.json',{'id':digest,'nonce':nonce,'contenido_sha256':{str(p.relative_to(out)):util.sha(p) for p in out.rglob('*') if p.is_file()}})
 print(json.dumps({'carpeta':str(out),'duracion_s':len(x)/SR,'AAC':meter,'gif_bytes':gif.stat().st_size},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
