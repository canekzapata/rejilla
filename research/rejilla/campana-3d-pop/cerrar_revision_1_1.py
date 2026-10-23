"""Entrega nueva y exclusiva; los PNGs provienen de capturas y exportación reales."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
import json, hashlib, subprocess, zipfile, wave
ROOT=Path(__file__).resolve().parent
TAG='s20261021-0dd3b9a583a5'
OUT=ROOT/('p-adic-bell-'+TAG)
WORK=ROOT/'render'/TAG
def save(image,path,**kwargs):
    with path.open('xb') as f:image.save(f,**kwargs)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def font(size):
    try:return ImageFont.truetype('C:/Windows/Fonts/arial.ttf',size)
    except OSError:return ImageFont.load_default()
def gif(frames,path,durations):
    save(frames[0],path,format='GIF',save_all=True,append_images=frames[1:],duration=durations,loop=0,optimize=True)
    im=Image.open(path);total=0;tiles=[]
    for i in range(im.n_frames):
        im.seek(i);total+=im.info['duration'];tiles.append(im.convert('RGB'))
    assert total<=10000 and path.stat().st_size<=15*1024**2
    return {'frames':im.n_frames,'duration_ms':total,'bytes':path.stat().st_size,'loop':0},tiles
def main():
    result=OUT/('p-adic-bell-resultado-'+TAG+'.png');image=Image.open(result)
    assert image.size==(1200,630);postal=json.loads(image.text['Receta']);assert postal['version']=='1.1.0'
    # Historical OG bytes remain in the previous exclusive delivery and git.
    (ROOT/'dist/og.png').write_bytes(result.read_bytes())
    report=json.loads((WORK/'verificacion.json').read_text(encoding='utf-8'));assert report['result']=='PASS' and len(report['songs'])==5
    with (OUT/('verificacion-cinco-piezas-'+TAG+'.json')).open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
    audio=[]
    for i,song in enumerate(report['songs'],1):
        source=WORK/(song['id']+'.wav');target=OUT/(str(i).zfill(2)+'-'+song['id']+'-'+TAG+'.m4a')
        with wave.open(str(source)) as w:duration=w.getnframes()/w.getframerate();assert w.getframerate()==48000
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-n','-i',str(source),'-af',f'afade=t=out:st={duration-.05:.6f}:d=0.05','-c:a','aac','-b:a','192k','-metadata','artist=Canek Zapata','-metadata','title='+song['title'],'-metadata','comment=P-adic Bell 1.1.0; '+TAG+'; live score rendered offline; gain 0.9; 50 ms final fade.',str(target)],check=True)
        probe=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(target)],capture_output=True,text=True,check=True)
        decoded=float(json.loads(probe.stdout)['format']['duration']);assert abs(decoded-duration)<.1
        audio.append({'file':target.name,'duration':decoded,'source_wav_sha256':sha(source),'bytes':target.stat().st_size})
    stages=sorted((OUT/'proceso').glob('[0-9][0-9]-*.png'))
    captions=['Estado anterior: Otra distancia','Nombre: P-adic Bell','Tres partituras iniciales','Primera animación espectral','Cinco piezas por pedido de Canek','Estelas junto a las láminas','Versión final y fin de partitura']
    assert len(stages)==len(captions)
    frames=[]
    for path,caption in zip(stages,captions):
        im=ImageOps.contain(Image.open(path).convert('RGB'),(800,450));f=Image.new('RGB',(800,510),'#fff0e6');f.paste(im,((800-im.width)//2,(450-im.height)//2));d=ImageDraw.Draw(f);d.text((18,464),caption,font=font(17),fill='#321a43');d.text((18,488),'Borradores sucesivos y pruebas reales · versión 1.1.0',font=font(12),fill='#321a43');frames.append(f)
    process_info,process_frames=gif(frames,OUT/('p-adic-bell-proceso-'+TAG+'.gif'),[1100]*len(frames))
    live_paths=sorted((OUT/'proceso/animacion').glob('*.png'));times=json.loads(next((OUT/'proceso/animacion').glob('tiempos-*.json')).read_text(encoding='utf-8'))
    durations=[max(50,round((times[i+1]['time']-times[i]['time'])/10)*10) for i in range(len(times)-1)]+[600]
    live=[ImageOps.contain(Image.open(p).convert('RGB'),(900,510)) for p in live_paths]
    animation_info,animation_frames=gif(live,OUT/('p-adic-bell-espectro-vivo-'+TAG+'.gif'),durations)
    all_frames=process_frames+animation_frames;sheet=Image.new('RGB',(1000,4*200),'#fff0e6')
    for i,im in enumerate(all_frames):
        tile=ImageOps.contain(im,(250,185));sheet.paste(tile,(i%4*250+(250-tile.width)//2,i//4*200))
    save(sheet,OUT/('p-adic-bell-revision-cuadros-'+TAG+'.png'),format='PNG')
    with (OUT/'proceso/README.md').open('x',encoding='utf-8') as f:
        f.write('# P-adic Bell — proceso de la versión 1.1.0\n\n21 de octubre de 2026. Semilla de identificación 20261021; partituras y geometría deterministas, sin azar. Identidad nueva: primera captura + app anterior + versión 1.1.0 + nonce nuevo. Se conservaron todas las entregas previas.\n\n')
        for p,c in zip(stages,captions):f.write(f'- [{c}]({p.name}): captura original en el navegador durante esta revisión.\n')
        f.write('\nEl primer GIF reúne estos borradores reales: no es una grabación continua. La petición pasó de tres a cinco piezas durante el trabajo; se conservaron ambas etapas. La primera colocación del espectro podía salir del encuadre y mostraba manchas demasiado amplias; se ajustaron posición, umbral y trazo, manteniendo datos reales. El selector de altura acumulaba opciones de afinación fraccionaria durante una pieza; se corrigió redondeando sólo la etiqueta, sin alterar el audio.\n\nEl segundo GIF reúne seis PNGs consecutivos de una sola resonancia, con tiempos originales en `animacion/tiempos-*.json`. Respeta esos intervalos redondeados a 10 ms y sostiene el último cuadro 600 ms. Es un muestreo de pantalla, no video continuo ni una reconstrucción de la señal. No contiene audio. Se conservan los PNGs originales en `animacion/`.\n\nLos cuadros de ambos GIFs se decodificaron y reunieron en una hoja de revisión visual. El resultado PNG es una exportación real a 1200×630 sin UI; incluye receta iTXt individual. Ninguna etapa interna del sintetizador o del renderizador se presenta como captura si no se registró.\n')
        f.write('\n## Cinco piezas en audio\n\nRenders del mismo procesador a 48 kHz, ganancia .9 y fundido final de 50 ms, AAC 192 kb/s. En la página se ejecutan como partituras en vivo, no como estos archivos. Las colas vivas pueden continuar más allá de la duración indicada.\n\n')
        for a,s in zip(audio,report['songs']):f.write(f"- [{s['title']}, {s['duration']} s](../{a['file']})\n")
    archive=OUT/('p-adic-bell-local-'+TAG+'.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        files=list((ROOT/'dist').rglob('*'))+[ROOT/p for p in ['abrir.py','abrir-escultura.bat','README.md','PROCEDENCIA.json','audio_processor.mjs','preparar.py','pruebas.mjs','verificar_canciones.mjs','package.json']]
        for p in files:
            if p.is_file():z.write(p,Path('p-adic-bell')/p.relative_to(ROOT))
        for p in OUT.rglob('*'):
            if p.is_file() and p!=archive:z.write(p,Path('p-adic-bell')/OUT.name/p.relative_to(OUT))
    manifest={'version':'1.1.0','identity':json.loads((OUT/('identidad-'+TAG+'.json')).read_text(encoding='utf-8')),'postal':postal,'process_gif':process_info,'live_spectrum_gif':animation_info,'audio':audio,'source_commit':'16e2e7b','canonical':'TODO https://canekzapata.net/p-adic-bell/','files':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and ('dist' in p.relative_to(ROOT).parts or OUT.name in p.parts or p.parent==ROOT) and not p.name.endswith('.local') and p.name!='puerto.local'}}
    with (OUT/('receta-final-'+TAG+'.json')).open('x',encoding='utf-8') as f:json.dump(manifest,f,ensure_ascii=False,indent=2)
    print(json.dumps({'process_gif':process_info,'live_spectrum_gif':animation_info,'zip_bytes':archive.stat().st_size,'audio':audio},ensure_ascii=False))
if __name__=='__main__':main()
