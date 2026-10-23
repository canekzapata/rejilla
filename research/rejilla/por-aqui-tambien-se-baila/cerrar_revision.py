"""Cierre de la revisión de escritura, no de la producción musical."""
from comun import *
from PIL import Image,ImageOps

def main():
    out=ultimo();tag=out.name.split('-')[-1];run=leer(out/'ejecucion.json');stages=sorted((out/'proceso').glob('0[1-4]-*.png'))
    assert len(stages)==4
    frames=[]
    for p in stages:
        im=Image.open(p).convert('RGB');im=ImageOps.contain(im,(1200,630));frame=Image.new('RGB',(1200,630),'#f7f0e7');frame.paste(im,((1200-im.width)//2,(630-im.height)//2));frames.append(frame.quantize(colors=160))
    gif=out/f'por-aqui-reescritura-s22-{tag}.gif';buf=io.BytesIO();frames[0].save(buf,format='GIF',save_all=True,append_images=frames[1:],duration=2000,loop=0,disposal=2);guardar(gif,buf.getvalue())
    im=Image.open(gif);secs=0
    for k in range(im.n_frames):im.seek(k);secs+=im.info.get('duration',0)/1000
    assert im.n_frames==4 and secs<=10 and gif.stat().st_size<=15_000_000
    final=out/f'por-aqui-partitura-general-s22-{tag}.png';guardar(final,stages[1].read_bytes());guardar(out/'og.png',stages[1].read_bytes())
    guardar(out/'proceso/README.md',f'''# Proceso real de la revisión 4

22 de octubre de 2026. Semilla 22. Identificador `{tag}`.

1. `{stages[0].name}`: perfil muestreado del viaje, guardado antes de generar
   los eventos. No representa una carretera medida; la ruta de transporte es compuesta.
2. `{stages[1].name}`: después de reescribir los eventos, actividad de treinta
   partes y la parada libre de 180 a 200 segundos.
3. `{stages[2].name}`: estado real del controlador de tres amplitudes durante
   el circuito del solo; se grafica después del plano de las treinta partes.
4. `{stages[3].name}`: raster de la página de avería del PDF efectivamente
   generado. Es una edición de dirección, no un render del audio o del visor.

El GIF reúne estas capturas en ese orden: **4 cuadros, {secs:.1f} segundos,
{gif.stat().st_size} bytes, loop infinito**. Muestra elaboración de la escritura;
no simula cómo dibuja un plotter ni un proceso interno de generación de imagen.
Su cuarto cuadro se ajusta con márgenes al lienzo 1200x630.

El PNG final y og.png son copias del plano de treinta partes, 1200x630.
No hay frames de visor: se dejó para después por instrucción de Canek.
Los borradores reales de esta sesión se conservan en las otras carpetas
`por-aqui-revision-s22-*`, con su ESTADO.md. No son entregas vigentes.
'''.encode('utf8'))
    jsave(out/'proceso/comprobacion-gif.json',{'cuadros':im.n_frames,'duracion_s':secs,'bytes':gif.stat().st_size,'loop':im.info.get('loop'),'semilla':22,'PNG_final':[1200,630],'verificacion_visual':'pendiente de inspección final del GIF y PNGs'})
    # Documentar borradores en vez de borrarlos o volverlos a etiquetar como fases
    # interiores de la última ejecución.
    for folder in BASE.glob('por-aqui-revision-s22-*'):
        if folder==out:continue
        if not (folder/'partitura-r4.json').exists():state='Ejecución detenida al serializar: una variable de ángulo fue reutilizada para un arreglo de aceleración. No produjo partitura ni PDF.'
        else:
            q=leer(folder/'partitura-r4.json');ct=len(leer(folder/'impactos-bolsa.json'))
            state=f'Borrador real: {sum(map(len,q["eventos"].values()))} eventos y {ct} impactos calculados. '
            state+=('La excitación no alcanzaba los topes: modelo corregido después. ' if ct==0 else 'Todavía no se presentaba un gesto de bolsa antes del aprendizaje de la mbira. ')
            if list(folder.glob('*.pdf')):state+='El primer PDF también tapaba el encabezado del solo y dejaba poco margen; corregido en la entrega vigente. '
        guardar(folder/'ESTADO.md',f'# Borrador conservado\n\n{state}\n\nEntrega vigente: `{out.name}`. No usar este borrador para interpretar la canción.\n'.encode('utf8'))
    old=BASE/'README-PRIMERA-ETAPA.md';guardar(old,(BASE/'README.md').read_bytes())
    (BASE/'README.md').write_text(f'''# Por aquí también se baila

**Revisión compositiva del 22 de octubre de 2026. Partitura e instrumentos para
revisar con Canek; detener antes de renderizar la canción. El visor va después.**

Entrega vigente: [{out.name}]({out.name}/REVISION-COMPOSITIVA.md), semilla 22,
versión {run['version']}. `ULTIMA.txt` selecciona la carpeta; `PARTITURA.txt`
selecciona partitura-r4.json. La primera entrega y los borradores permanecen intactos.

## Lo que cambió

- Bolsa concreta: trompo de lámina, cascabel y silbato de barro con un ala rota.
  Gesto escrito antes del aprendizaje de la mbira; 32 contactos adicionales
  calculados a partir del recorrido/tráfico. El silbato tiene consecuencia en la coda.
- Treinta partes, **2581 eventos**, tema compartido, respuestas por huecos,
  campos D/A, 6/5, 7/4 y residuo 11/8. La reducción de eventos no se usa como
  indicador de menor o mayor complejidad.
- Percusiones con subdivisiones 4/3/5, articulación y carga variable, remates y
  relevos; recursos carnáticos en una composición propia, sin fingir calibración tradicional.
- Solo D: circuito de transformaciones no conmutativas sobre tres amplitudes
  con signo. Cierra el circuito y conserva norma; cambia el reparto de la frase.
- Viaje cerrado de 4.022 km, ascenso y descenso acumulados de 155.64 m. Alturas
  del terreno; conexiones, clima y tiempo del transporte compuestos. La pendiente
  afecta la articulación y las voces conservan relojes integrados de tráfico.
- **Avería de 3:00 a 3:20**, sin capas métricas; corte y vaciado de efectos
  escritos. Radio, pitidos y arranques libres. Regresa la base con un ataque de
  membrana perdido. El corte acústico se verificará al producir, todavía no se ha oído.

## Qué revisar

[Crítica y respuestas a tus preguntas]({out.name}/REVISION-COMPOSITIVA.md).
[Compositor: preguntas reutilizables](../COMPOSITOR.md), con
[skill local](../.agents/skills/compositor/SKILL.md) para trabajar dentro de Rejilla.

La entrega tiene PDF de dirección de **17 páginas**, MusicXML con las 30 partes,
JSON y CSV completos. MusicXML conserva alteraciones fraccionarias y señala
senza misura durante la avería; JSON/CSV son el contrato de síntesis, incluyendo
signos de fase, carga de membrana y controles del recorrido. Los diagramas no
sustituyen las partes completas.

La [validación]({out.name}/validacion-r4.json) comprueba duración, silencio de
eventos métricos, retorno no conmutativo, caso identidad, recorrido cerrado,
presentación antes del aprendizaje y treinta partes de 96 posiciones en XML.
No acredita belleza o inteligibilidad. PDF revisado visualmente; falta escuchar
esta interpretación porque aún no se ha renderizado.

Motores nuevos de esta revisión: bolsa de impactos y motor fallido en
`instrumentos_revision.py`; controlador de tres voces en el mismo archivo.
Los instrumentos anteriores y sus sondas siguen disponibles: ver
[registro de primera etapa](README-PRIMERA-ETAPA.md) y [referencias](REFERENCIAS.md).
El vibráfono cede su parte a la bolsa: siguen siendo treinta, sin contar el
controlador como un timbre añadido.

## Proceso y reproducción

`reescribir.py` crea una carpeta exclusiva con imagen inicial + versión/código +
nonce; conserva su fuente en la ejecución. `edicion_revision.py` produce papel y
datos, `documentar_revision.py` escribe la crítica y `validar_revision.py` comprueba
la escritura. `cerrar_revision.py` reúne capturas y huellas. Cada etapa rechaza
destinos existentes. No relanzar sobre una carpeta ya entregada.

[GIF del proceso]({out.name}/{gif.name}), **8 segundos, cuatro capturas reales**;
[PNG de la partitura]({out.name}/{final.name}), og.png y
[explicación de etapas]({out.name}/proceso/README.md). No es una animación del
visor ni un video de la canción. Borradores previos conservados con ESTADO.md.

**Siguiente paso acordado: revisar la partitura contigo. Después, interpretar y
renderizar la canción. Visor y hazvideo.py después; el video completo lo hace Canek.**
No se produjo máster, MP4 o visor nuevo. Sin publicación ni push.
''',encoding='utf8')
    files={str(p.relative_to(out)).replace('\\','/'):sha(p) for p in out.rglob('*') if p.is_file()}
    code={n:sha(BASE/n) for n in ['reescribir.py','instrumentos_revision.py','edicion_revision.py','documentar_revision.py','validar_revision.py','cerrar_revision.py','README.md']}
    jsave(out/'receta-r4.json',{'ejecucion':run,'artefactos_sha256':files,'fuentes_sha256':code,'compositor_sha256':sha(BASE.parent/'COMPOSITOR.md'),'gif':{'nombre':gif.name,'segundos':secs,'bytes':gif.stat().st_size,'cuadros':4},'pendiente':'audición tras aprobación de escritura; visor después','commit_escritura':'3aa9668','nota':'la receta no incluye su propia huella; archivos posteriores de revisión se declaran aparte'})
    print(json.dumps({'gif':str(gif),'segundos':secs,'bytes':gif.stat().st_size,'artefactos_sellados':len(files)},ensure_ascii=False))

if __name__=='__main__':main()
