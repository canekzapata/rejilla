"""Conservar el proceso real sin reemplazar entregas: PNGs, GIF, receta y paquete."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin
import hashlib
import json
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parent
TAG='970c1ab38e2a'
OUT=ROOT/f'braid-organ-{TAG}'

def exclusive(path, data):
    with path.open('xb') as stream:
        stream.write(data)

def main():
    identity=json.loads((OUT/f'identidad-{TAG}.json').read_text(encoding='utf-8'))
    report=json.loads(subprocess.check_output(['node','pruebas.mjs'],cwd=ROOT,text=True))
    exclusive(OUT/f'pruebas-{TAG}.json',json.dumps(report,ensure_ascii=False,indent=2).encode())
    source=OUT/f'braid-organ-cinco-cruces-{TAG}.png'
    image=Image.open(source).convert('RGB')
    assert image.size==(1200,630)
    meta=PngImagePlugin.PngInfo()
    meta.add_itxt('braid-organ',json.dumps({'author':'Canek Zapata','year':2026,'version':'1.0.0','word':'ABAbA','runSha256':identity['sha256'],'seedRoom':20261021,'source':'real Three.js renderer export; no UI'},ensure_ascii=False))
    result=OUT/f'braid-organ-final-{TAG}.png'
    with result.open('xb') as target:
        image.save(target,format='PNG',pnginfo=meta)
    # The two prior renderer exports remain in OUT; og.png is the current source asset.
    (ROOT/'dist/og.png').write_bytes(result.read_bytes())
    icon=image.crop((420,30,780,390)).resize((128,128),Image.Resampling.LANCZOS)
    with (ROOT/'dist/favicon.png').open('xb') as stream:
        icon.save(stream,format='PNG')
    stages=[
      ('01-primer-cuerpo','01 / Primer cuerpo: encuadre inicial'),
      ('02-primer-cruce','02 / Primer cruce: el acorde cambia'),
      ('05-tres-cruces-y-flores','03 / Tres cruces: la partitura toma cuerpo'),
      ('03-tejido-que-vuelve','04 / La ida y su inverso: 16 cruces, regreso timbrico'),
      ('07-dentro-de-la-trenza','05 / Entrar entre las cintas: escuchar desde dentro'),
      ('08-instrumento-terminado','06 / Cinco cruces: instrumento terminado'),
    ]
    frames=[]
    font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',14)
    for stem,title in stages:
        im=Image.open(OUT/'proceso'/f'{stem}-{TAG}.png').convert('RGB')
        im.thumbnail((960,540),Image.Resampling.LANCZOS)
        frame=Image.new('RGB',(960,570),'#0b24a7')
        frame.paste(im,((960-im.width)//2,(540-im.height)//2))
        ImageDraw.Draw(frame).text((15,547),title,font=font,fill='#f8f1df')
        frames.append(frame.quantize(colors=160))
    gif=OUT/f'braid-organ-proceso-{TAG}.gif'
    with gif.open('xb') as target:
        frames[0].save(target,format='GIF',save_all=True,append_images=frames[1:],duration=1100,loop=0,disposal=2,optimize=False)
    decoded=Image.open(gif)
    duration=0
    sheet=Image.new('RGB',(960,570),'#111')
    for i in range(decoded.n_frames):
        decoded.seek(i)
        duration+=decoded.info['duration']
        sheet.paste(decoded.convert('RGB').resize((320,285),Image.Resampling.LANCZOS),((i%3)*320,(i//3)*285))
    assert decoded.n_frames==6 and duration<=10000 and gif.stat().st_size<=15*1024*1024
    with (OUT/f'braid-organ-revision-gif-{TAG}.png').open('xb') as target:
        sheet.save(target,format='PNG')
    readme=f'''# Proceso real de Braid Organ · {TAG}

Capturas tomadas mientras se construyó y probó la pieza el 21 de octubre de 2026. Se conservan también ensayos que motivaron ajustes; no son reconstrucciones ni pasos internos inventados.

1. **01-primer-cuerpo**: cuerpo recto inicial y controles; el encuadre llegaba demasiado abajo.
2. **02-primer-cruce**: primer cruce A con el sintetizador encendido y encuadre corregido.
3. **03-tejido-que-vuelve**: partitura completa de 16 cruces. Recupera el estado algebraico inicial; la historia dibujada permanece.
4. **04-ensayo-movil-con-solapamiento**: título y cintas se solapaban en pantalla angosta. Se guarda el ensayo fallido.
5. **05-tres-cruces-y-flores**: frase ABA, cámara exterior y espectro de las tres voces.
6. **06-composicion-movil**: composición móvil corregida; el visor corta la parte inferior del iframe de 390×780.
7. **07-dentro-de-la-trenza**: cámara dentro del cuerpo, mismo estado ABA. Es una vista de proximidad, no una vista general de la escultura.
8. **08-instrumento-terminado**: ABAbA, flores más visibles según el espectro real y controles finales.
9. **09-movil-terminado**: vista móvil en funcionamiento, recortada por el área visible del navegador. No se presenta como captura del teléfono completo.

El GIF reúne **01 → 02 → 05 → 03 → 07 → 08**: etapas sucesivas de construcción y pruebas, con rótulos añadidos. No es una interpretación continua ni lleva audio. Duración {duration/1000:.1f} s, {gif.stat().st_size} bytes, seis cuadros en loop infinito. La hoja de revisión reúne los cuadros decodificados del propio GIF.

El PNG final de 1200×630 sale del renderer, sin interfaz. Se conservan las postales anteriores de tres y cinco cruces. `og.png` y `favicon.png` proceden de la pieza.

Identificación de ejecución: SHA-256 completo `{identity['sha256']}`; nonce nuevo registrado en identidad. Derivación: bytes de la primera captura + núcleo algebraico + versión + nonce. La semilla 20261021 pertenece sólo a la respuesta impulsiva del recinto, no a las matrices ni a los gestos. Huellas de archivos en la receta. Carpeta creada exclusivamente; archivos de entrega escritos con rechazo si ya existen.

Núcleo matemático y síntesis compartida verificados en `pruebas-{TAG}.json`. El navegador mostró AudioContext running, espectros distintos de cero, arrastre de una perla, teclado Shift+A y final de la partitura automática. No se afirma escucha humana por parte del agente.
'''
    exclusive(OUT/'proceso/README.md',readme.encode())
    files={str(p.relative_to(OUT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.rglob('*') if p.is_file()}
    sources={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'dist').rglob('*') if p.is_file()}
    recipe={**identity,'date':'2026-10-21','seedRoom':20261021,'gif':{'frames':6,'durationMs':duration,'bytes':gif.stat().st_size,'loop':0},'tests':report,'files':files,'dist':sources,'limitations':['GIF of successive real tests, not continuous playing','No human listening claimed','Mobile preview screenshots show the visible iframe area','Artistic HRTF/room, not geometry-based acoustics']}
    exclusive(OUT/f'receta-{TAG}.json',json.dumps(recipe,ensure_ascii=False,indent=2).encode())
    archive=OUT/f'braid-organ-local-{TAG}.zip'
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for directory in ['dist','docs']:
            for p in (ROOT/directory).rglob('*'):
                if p.is_file():z.write(p,str(p.relative_to(ROOT)))
        for name in ['README.md','abrir.py','abrir-braid-organ.bat','package.json','pruebas.mjs','cerrar_entrega.py']:
            z.write(ROOT/name,name)
        for p in OUT.rglob('*'):
            if p.is_file() and p!=archive:z.write(p,str(p.relative_to(ROOT)))
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    print(json.dumps({'gifBytes':gif.stat().st_size,'durationMs':duration,'zipBytes':archive.stat().st_size,'result':str(result),'review':str(OUT/f'braid-organ-revision-gif-{TAG}.png')},indent=2))

if __name__=='__main__':main()
