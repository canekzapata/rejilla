"""Cerrar la escucha espacial con capturas reales y audios del navegador."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
from array import array
import json,hashlib,subprocess,zipfile,wave,math
ROOT=Path(__file__).resolve().parent
TAG='s20261021-46a649a69ad4'
OUT=ROOT/('p-adic-bell-spatial-'+TAG)
DOWNLOADS=Path('C:/Users/HP-PC/Downloads')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(im,path,**kw):
    with path.open('xb') as f:im.save(f,**kw)
def font(size):
    try:return ImageFont.truetype('C:/Windows/Fonts/arial.ttf',size)
    except OSError:return ImageFont.load_default()
def main():
    result=OUT/('p-adic-bell-spatial-resultado-'+TAG+'.png');image=Image.open(result);assert image.size==(1200,630)
    postal=json.loads(image.text['Receta']);assert postal['version']=='1.2.0' and postal['state']['spatialListening']['enabled']
    (ROOT/'dist/og.png').write_bytes(result.read_bytes()) # Previous OG is preserved in prior exclusive outputs and git.
    report=json.loads((OUT/('comparacion-acustica-'+TAG+'.json')).read_text(encoding='utf-8'));assert report['result']=='PASS'
    chunks=[];audio=[]
    work=ROOT/'render'/TAG;work.mkdir(exist_ok=False)
    for mode in ['outside','inside']:
        source=DOWNLOADS/('p-adic-bell-'+mode+'-'+TAG+'.wav')
        with wave.open(str(source)) as wav:
            assert wav.getframerate()==48000 and wav.getnchannels()==2 and wav.getsampwidth()==2
            raw=wav.readframes(wav.getnframes());samples=array('h',raw);rms=[math.sqrt(sum((v/32767)**2 for v in samples[ch::2])/(len(samples)/2)) for ch in range(2)]
        assert abs(rms[0]-report[mode]['leftRms'])<1e-5 and abs(rms[1]-report[mode]['rightRms'])<1e-5
        chunks.append(raw);target=OUT/('p-adic-bell-'+mode+'-'+TAG+'.m4a')
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-n','-i',str(source),'-c:a','aac','-b:a','192k','-metadata','artist=Canek Zapata','-metadata','title=P-adic Bell: '+mode,'-metadata','comment=Spatial comparison 1.2.0; same excitation; '+TAG,str(target)],check=True)
        audio.append({'file':target.name,'source_wav_sha256':sha(source),'rms_pcm16':rms,'bytes':target.stat().st_size})
    combined=work/('p-adic-bell-outside-inside-'+TAG+'.wav')
    with wave.open(str(combined),'wb') as wav:
        wav.setparams((2,2,48000,0,'NONE','not compressed'));wav.writeframes(chunks[0]+bytes(round(.5*48000)*4)+chunks[1])
    ab=OUT/('p-adic-bell-outside-inside-'+TAG+'.m4a')
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-n','-i',str(combined),'-c:a','aac','-b:a','192k','-metadata','artist=Canek Zapata','-metadata','title=P-adic Bell: outside / inside','-metadata','comment=0-4s outside; 4.5-8.5s inside; same excitation; no loudness normalization; '+TAG,str(ab)],check=True)
    audio.append({'file':ab.name,'source_wav_sha256':sha(combined),'segments':{'outside':[0,4],'silence':[4,4.5],'inside':[4.5,8.5]},'bytes':ab.stat().st_size})
    for a in audio:
        p=OUT/a['file'];probe=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(p)],capture_output=True,text=True,check=True);a['duration']=float(json.loads(probe.stdout)['format']['duration'])
    assert abs(audio[2]['duration']-8.5)<.05
    stages=sorted((OUT/'proceso').glob('[0-9][0-9]-*.png'))
    captions=['Antes: vista sin acústica interior','Misma excitación, distinta proyección','Fuera: escuchar el conjunto','Dentro: dirección, cercanía y recinto','Comparación sin reiniciar la partitura','Volver a la escucha espacial','Instrumento espacial y control manual']
    assert len(stages)==len(captions)==7
    frames=[]
    for path,caption in zip(stages,captions):
        im=ImageOps.contain(Image.open(path).convert('RGB'),(800,450));f=Image.new('RGB',(800,510),'#fff0e6');f.paste(im,((800-im.width)//2,(450-im.height)//2));d=ImageDraw.Draw(f);d.text((16,463),caption,font=font(17),fill='#321a43');d.text((16,488),'Capturas reales del proceso · GIF sin audio · P-adic Bell 1.2.0',font=font(12),fill='#321a43');frames.append(f)
    gif=OUT/('p-adic-bell-escucha-espacial-proceso-'+TAG+'.gif')
    save(frames[0],gif,format='GIF',save_all=True,append_images=frames[1:],duration=1100,loop=0,optimize=True)
    check=Image.open(gif);total=0;sheet=Image.new('RGB',(1000,400),'#fff0e6')
    for i in range(check.n_frames):
        check.seek(i);total+=check.info['duration'];thumb=ImageOps.contain(check.convert('RGB'),(250,190));sheet.paste(thumb,(i%4*250,i//4*200))
    assert total<=10000 and gif.stat().st_size<=15*1024**2
    save(sheet,OUT/('p-adic-bell-escucha-espacial-revision-'+TAG+'.png'),format='PNG')
    with (OUT/'proceso/README.md').open('x',encoding='utf-8') as f:
        f.write('# P-adic Bell 1.2.0 — proceso de escucha espacial\n\n21 de octubre de 2026. Semilla 20261021. Ejecución exclusiva, nonce nuevo e identidad SHA-256 desde primera captura, programa anterior y versión 1.2.0. No se sobrescribieron las entregas 1.0/1.1.\n\n')
        for p,c in zip(stages,captions):f.write(f'- [{c}]({p.name}): captura real del navegador.\n')
        f.write('\nEl GIF reúne pruebas sucesivas, no una grabación continua. Es silencioso: las diferencias acústicas se comparan en los audios. El cuadro 05 conserva la vista capturada durante la comparación; el panel del control aparece claramente en el 06. Los siete cuadros del GIF se decodificaron y reunieron en una hoja de revisión. El PNG de resultado es una exportación real del renderer a 1200×630 sin interfaz y con receta iTXt. No se inventaron imágenes de una simulación acústica de la malla: esa simulación no forma parte de la pieza.\n\n')
        f.write('Se corrigió una carrera de actualizaciones de partitura frente al pliegue manual; el control quedó en 0.38 y la partitura se canceló sin vaciar el resonador. La prueba y los estados reales están en los JSON de esta entrega.\n\n## Escuchar la comparación\n\n')
        for a in audio:f.write(f"- [{a['file']}](../{a['file']})\n")
        f.write('\nEl archivo fuera/dentro dura 8.5 s: 0–4 s exterior, pausa de 0.5 s y 4.5–8.5 s interior. Mismos golpes, afinación, familia y trayectoria del resonador; sólo cambia la proyección. Sin normalización de volumen entre condiciones. AAC 192 kb/s de WAVs reales renderizados en OfflineAudioContext a 48 kHz. Los PCM16 se leyeron de forma independiente y coincidieron con los RMS del reporte (tolerancia 1e-5). La comparación tiene un fundido de entrada de señal a cero durante los últimos 50 ms anteriores a 2.2 s para medir el recinto después.\n\nLa versión espacial pasó referencia idéntica entre vistas, diferencia interior más allá de ganancia, mayor energía de cola, inversión del balance por orientación y margen de salida. Esto no sustituye la valoración auditiva de una persona. La documentación conceptual y técnica está en [docs](../../docs/README.md). URL canónica propuesta pendiente de publicación: https://canekzapata.net/p-adic-bell/.\n')
    archive=OUT/('p-adic-bell-spatial-local-'+TAG+'.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        files=list((ROOT/'dist').rglob('*'))+list((ROOT/'docs').rglob('*.md'))+[ROOT/p for p in ['README.md','abrir.py','abrir-escultura.bat','preparar.py','audio_processor.mjs','PROCEDENCIA.json','pruebas.mjs','pruebas_espaciales.mjs','verificar_canciones.mjs','package.json']]
        for p in files:
            if p.is_file():z.write(p,Path('p-adic-bell')/p.relative_to(ROOT))
        for p in OUT.rglob('*'):
            if p.is_file() and p!=archive:z.write(p,Path('p-adic-bell')/p.relative_to(ROOT))
    base=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    manifest={'version':'1.2.0','identity':json.loads((OUT/('identidad-'+TAG+'.json')).read_text(encoding='utf-8')),'source_base_commit':base,'postal':postal,'audio':audio,'tests':report,'gif':{'duration_ms':total,'frames':check.n_frames,'bytes':gif.stat().st_size,'loop':0},'files':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and ('dist' in p.relative_to(ROOT).parts or 'docs' in p.relative_to(ROOT).parts or OUT.name in p.parts or p.parent==ROOT) and not p.name.endswith('.local') and p.name!='.env'}}
    with (OUT/('receta-final-'+TAG+'.json')).open('x',encoding='utf-8') as f:json.dump(manifest,f,ensure_ascii=False,indent=2)
    print(json.dumps({'gif':manifest['gif'],'zip_bytes':archive.stat().st_size,'audios':audio,'tests':report['result']},ensure_ascii=False))
if __name__=='__main__':main()
