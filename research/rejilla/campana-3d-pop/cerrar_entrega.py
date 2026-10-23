"""Empaquetar sólo capturas reales, sin pisar una entrega anterior."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json,hashlib,subprocess,zipfile
ROOT=Path(__file__).resolve().parent
TAG='s20261021-b9431c1221b7'
OUT=ROOT/('otra-distancia-'+TAG)
def save_exclusive(image,path,**kwargs):
    with path.open('xb') as f: image.save(f,**kwargs)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    result=OUT/('otra-distancia-resultado-'+TAG+'.png')
    image=Image.open(result);assert image.size==(1200,630)
    recipe=json.loads(image.text['Receta']);assert len(recipe['sha256'])==64
    with (ROOT/'dist/og.png').open('xb') as f: f.write(result.read_bytes())
    icon=image.crop((410,150,785,525)).resize((64,64),Image.Resampling.LANCZOS)
    save_exclusive(icon,ROOT/'dist/favicon.png',format='PNG')
    stages=sorted((OUT/'proceso').glob('[0-9][0-9]-*.png'));assert len(stages)==6
    captions=['Geometría: 64 láminas con hueco','Primer material y encuadre','Color y escala ajustados','Plegado: ocho familias','Entrar entre las láminas','Obra y gestos en vivo']
    frames=[]
    try: font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
    except OSError: font=ImageFont.load_default()
    for i,(path,caption) in enumerate(zip(stages,captions)):
        stage=Image.open(path).convert('RGB');frame=Image.new('RGB',(stage.width,stage.height+64),'#fff0e6');frame.paste(stage,(0,0));d=ImageDraw.Draw(frame);d.text((16,stage.height+10),f'{i+1}/6 · {caption}',font=font,fill='#321a43');d.text((16,stage.height+34),'Borradores sucesivos + pruebas reales',font=font,fill='#321a43');frames.append(frame)
    gif=OUT/('otra-distancia-proceso-'+TAG+'.gif')
    save_exclusive(frames[0],gif,format='GIF',save_all=True,append_images=frames[1:],duration=1200,loop=0,optimize=True)
    decoded=Image.open(gif);assert decoded.n_frames==6;duration=0;sheet=Image.new('RGB',(720,600),'#fff0e6')
    for i in range(decoded.n_frames):
        decoded.seek(i);duration+=decoded.info['duration'];tile=decoded.convert('RGB').resize((240,274));sheet.paste(tile,(i%3*240,i//3*300))
    assert duration<=10000 and gif.stat().st_size<=15*1024**2
    save_exclusive(sheet,OUT/('otra-distancia-revision-cuadros-'+TAG+'.png'),format='PNG')
    report=subprocess.run(['node','pruebas.mjs'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',check=True).stdout
    with (OUT/('pruebas-'+TAG+'.json')).open('x',encoding='utf-8') as f:f.write(report)
    with (OUT/'proceso/README.md').open('x',encoding='utf-8') as f:
        f.write('# Proceso real — Otra distancia\n\n21 de octubre de 2026. Versión 1.0.0. Semilla de identificación 20261021; geometría determinista sin azar.\n\n')
        for path,caption in zip(stages,captions):f.write(f'- [{caption}]({path.name}): captura original del navegador durante este loop.\n')
        f.write('\nEl GIF reúne estas seis etapas: 7.2 segundos, loop infinito. Muestra borradores sucesivos y pruebas de interacción, no una toma continua. La primera vista aún usa material gris; la segunda conserva un encuadre excesivamente cercano; la tercera ajusta color y escala; las siguientes prueban el plegado y el recorrido. No se reconstruyeron etapas que no se hubieran capturado.\n\nEl PNG de resultado es una exportación real del renderer a 1200×630 sin interfaz. Su receta iTXt individual conserva otro nonce/SHA; la identidad de esta entrega proviene de su primera captura y forma.mjs, versión y nonce, según identidad-*.json. Los nombres de etapas y entrega comparten el identificador de ejecución. No se sobrescribió una entrega previa.\n\nTodos los PNGs y los seis cuadros del GIF se decodificaron; se generó una hoja de revisión para comprobarlos visualmente. La variación de cámara o brillo no se presenta como cambio en la física original.\n')
    archive=OUT/('otra-distancia-local-'+TAG+'.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        files=list((ROOT/'dist').rglob('*'))+[ROOT/p for p in ['abrir.py','abrir-escultura.bat','README.md','PROCEDENCIA.json','audio_processor.mjs','preparar.py','pruebas.mjs','package.json']]
        for path in files:
            if path.is_file():z.write(path,Path('otra-distancia')/path.relative_to(ROOT))
        for path in OUT.rglob('*'):
            if path.is_file() and path!=archive:z.write(path,Path('otra-distancia/proceso-y-entrega')/path.relative_to(OUT))
    manifest={'version':'1.0.0','identidad':json.loads((OUT/('identidad-'+TAG+'.json')).read_text(encoding='utf-8')),'postal':recipe,'gif':{'frames':6,'duration_ms':duration,'bytes':gif.stat().st_size,'loop':0,'tipo':'Borradores sucesivos y pruebas reales'},'files':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and '.local' not in p.name and '__pycache__' not in p.parts}}
    with (OUT/('receta-final-'+TAG+'.json')).open('x',encoding='utf-8') as f:json.dump(manifest,f,ensure_ascii=False,indent=2)
    print(json.dumps({'gif_bytes':gif.stat().st_size,'duration_ms':duration,'png':image.size,'zip_bytes':archive.stat().st_size,'postal_metadata':'iTXt Receta válida'},ensure_ascii=False))
if __name__=='__main__':main()
