"""Entregar audio, receta y proceso; conservar tomas anteriores sin tocarlas."""
from audio_comun import *
from PIL import Image,ImageOps

def main():
    out,cfg,P,work=contexto();tag=out.name.split('-')[-1];E=leer(out/'audio-entrega.json');V=leer(out/'audio-verificado.json');M=leer(out/'mezcla-medidas.json');stages=sorted((out/'proceso').glob('0[1-4]-*.png'));assert len(stages)==4
    frames=[]
    for p in stages:
        im=ImageOps.contain(Image.open(p).convert('RGB'),(1200,630));frame=Image.new('RGB',(1200,630),'#f7f0e7');frame.paste(im,((1200-im.width)//2,(630-im.height)//2));frames.append(frame.quantize(colors=160))
    gif=out/f'por-aqui-proceso-de-audio-s22-{tag}.gif';b=io.BytesIO();frames[0].save(b,format='GIF',save_all=True,append_images=frames[1:],duration=2000,loop=0,disposal=2);guardar(gif,b.getvalue())
    g=Image.open(gif);secs=0
    for i in range(g.n_frames):g.seek(i);secs+=g.info.get('duration',0)/1000
    assert g.n_frames==4 and secs==8 and gif.stat().st_size<15_000_000
    final=out/f'por-aqui-master-en-senal-s22-{tag}.png';guardar(final,stages[-1].read_bytes());guardar(out/'og.png',stages[-1].read_bytes())
    # Fragmento específico para comprobar la llamada aprendida por la radio.
    clip=out/f'la-radio-aprende-el-silbato-s22-{tag}.m4a';subprocess.run(['ffmpeg','-n','-v','error','-ss','229','-i',str(out/E['master']),'-t','11','-c:a','aac','-b:a','224k',str(clip)],check=True)
    guardar(out/'proceso/README.md',f'''# Proceso real del render de audio

22 de octubre de 2026. Semilla 22. Hash de ejecución `{cfg['hash']}`.

1. `{stages[0].name}`: copia de la partitura revisada que Canek autorizó
   interpretar al decir «renderiza». Es una captura del plano anterior, no del visor.
2. `{stages[1].name}`: envolventes calculadas desde las treinta fuentes efectivamente
   renderizadas. Las fuentes se reutilizaron sin cambios de la primera toma;
   `fuentes-reutilizadas.json` identifica el origen y las huellas permiten comprobarlo.
3. `{stages[2].name}`: buses reales y avería en contexto. Las curvas de la izquierda
   están desplazadas verticalmente +0.05 por bus para leerlas; sus líneas de base no
   significan audio continuo. El bus métrico combinado tiene pico exactamente cero
   entre 180 y 200 s después de los efectos. Radio y gestos libres conservan sus silencios.
4. `{stages[3].name}`: mezcla completa y espectrograma después de la lectura Rejilla,
   antes de la ganancia final de exportación. El WAV entregado se midió por separado.

GIF de estas cuatro capturas: {secs:.0f} segundos, {gif.stat().st_size} bytes,
loop infinito. PNG final y og.png: 1200x630. No es un video musical ni una
implementación del visor. No representa la construcción interna del sintetizador.

Se conserva la primera mezcla en `../por-aqui-cancion-s22-56b7e385f96f/`.
En ella faltaba retransmitir el silbato efectivo por la radio; esta entrega lo
introduce a 231.72 s, antes del receptor y del clima. Las demás fuentes son idénticas.
Windows negó enlaces duros; se hicieron copias exclusivas, sin modificar las fuentes.
'''.encode('utf8'))
    guardar(out/'ESCUCHAR.md',f'''# Por aquí también se baila — audio completo

**4:06 · treinta partes · partitura r4 interpretada el 22 de octubre de 2026.**

- Escucha: [{E['escucha']}]({E['escucha']}).
- Máster WAV: [{E['master']}]({E['master']}), estéreo, 48 kHz, PCM de 24 bits.
- [Tema y juguetes](tema-y-juguetes-s22-{tag}.m4a), 0:18–0:50 del máster.
- [Solo del láser](solo-del-laser-s22-{tag}.m4a), 2:10–2:50.
- [Avería y regreso](averia-y-regreso-s22-{tag}.m4a), 2:52–3:38.
- [La radio aprende el silbato]({clip.name}), 3:49–4:00.

## Qué se realizó

La partitura aprobada se conserva byte por byte en `partitura-aprobada.json`.
Motor sonidero fijado para acordeón/bajo/conga/güiro/campana; batería acústica y
808; clarinete, chelo y guembri de los motores existentes. Mbira y arpa de boca
comparten parte; Boca de tres tiempos articula remates. El bordón de órgano se
interpreta con Cuerdas de estación, como en las pruebas de primera etapa.

Membrana cargada por FEM: 94 cargas distintas, control redondeado a 0.01
(error de carga máximo 0.005). El golpe cambia de modos, no sólo de volumen.
La bolsa contiene tres cuerpos modales y distingue los gestos escritos de los
32 contactos calculados. El raspador cambia perfil y dirección de lectura.

El láser aplica el signo antes de Talbot/redes. Sus tres salidas reciben una
calibración fija de transferencia y una ganancia de mezcla compartida; no se
normaliza cada célula ni se borran sus diferencias. Los ángulos y caminos siguen
siendo decisiones compositivas. No se afirma conservar energía acústica de la mezcla.

Sabina PSOLA canta verso y respuestas; parte de la respuesta adquiere color de
vocoder sobre lengüeta. Los anuncios son habla con duraciones naturales relativas
ajustadas a las ventanas de la partitura. La radio usa el receptor fijado de onda
corta, desintonía y clima. En la coda retransmite la muestra efectiva del silbato
de 177.37 s a 231.72 s: el recuerdo tiene la misma fuente sonora.

## La parada y Rejilla

**3:00–3:20: cero señal en el bus métrico**, comprobado después de añadir espacio
y cortar/vaciar sus colas. Se oyen radio, pitidos y arranques libres. Las cinco
ventanas de silencio previstas también son cero en el WAV. La base vuelve a
3:20; la membrana espera hasta 200.625 s para su primer ataque.

Magnitud y fase de la mezcla completa se escribieron en imágenes de Rejilla y
se leyeron de verdad con spectrumsynth: SNR de reconstrucción sin DC/Nyquist
{M['rejilla']['SNR_sin_DC_Nyquist_dB']:.2f} dB. Para mantener los silencios de la
avería sin el offset que puede introducir cada columna DFT, entre 180 y 200 s se
restituye el bus libre previo a Rejilla, con empalmes de 10 ms. Se declara esa
excepción; el resto usa la reconstrucción. No se cambió el tiempo del transporte.

## Comprobaciones y límites

AAC: **{V['AAC']['LUFS_I']:.2f} LUFS-I**, **{V['AAC']['true_peak_dBTP']:.2f} dBTP**;
WAV de 246.000 s, sin muestras saturadas y con silencio al final. Treinta fuentes
activas; signos del solo comprobados; compatibilidad mono medida. Ver
`audio-verificado.json`, `fuentes-verificadas.json` y `mezcla-medidas.json`.

No hubo audición propia: estos controles verifican señal, estructura y niveles;
la dicción, el balance perceptual y el resultado musical se revisan contigo al
escuchar. No se presenta la verificación numérica como juicio estético.

PNG y [GIF real del proceso]({gif.name}), cuatro cuadros en ocho segundos.
Las tomas anteriores, fuentes y partitura se conservaron sin sobrescribir.
**El visor y el video no se produjeron.** hazvideo.py corresponde a esa fase;
el video completo sigue a cargo de Canek. Sin publicación ni push.
'''.encode('utf8'))
    archive=BASE/'README-REVISION-PARTITURA.md';guardar(archive,(BASE/'README.md').read_bytes())
    (BASE/'README.md').write_text(f'''# Por aquí también se baila

**Audio completo renderizado por petición de Canek el 22 de octubre de 2026.**
4:06, treinta partes. La partitura r4 quedó aprobada para interpretación con
«renderiza». El visor y el video siguen para después.

## Escuchar

[Entrega, máster y fragmentos]({out.name}/ESCUCHAR.md).
[Canción completa]({out.name}/{E['escucha']}).
[WAV 48 kHz / 24 bits]({out.name}/{E['master']}).

`ULTIMO-AUDIO.txt` selecciona esta entrega de audio. `ULTIMA.txt` conserva la
selección de la partitura: no se reemplazan sus archivos ni su receta.

## Qué llega al audio

- Cumbia sonidera, recursos carnáticos, repetición/bordones de jazz contemporáneo,
  construcción por huecos y contactos instrumentales. Treinta partes y 2581 eventos.
- Bolsa concreta: trompo, cascabel y silbato de barro. La mbira aprende el gesto;
  los baches provocan contactos adicionales. La radio retransmite el silbato real en coda.
- Membranas FEM con 94 cargas; láser directo/red/Talbot con fase firmada y ganancia
  compartida, raspador del terreno, barro/pandero, Boca, mbira/arpaboca, guembri,
  órgano de función, clarinete, chelo y voces Sabina PSOLA con respuesta parcialmente vocalizada.
- Ruta de subida/bajada y relojes de tráfico de la r4; clima consume sus controles
  en articulación, modos y filtros. No se vende el recorrido compuesto como una carretera real.
- **Avería 3:00–3:20 sin bus métrico ni sus ecos.** Radio y gestos libres; primer
  golpe de membrana pospuesto a 200.625 s. El retorno conserva 11/8 y la memoria del solo.
- Lectura efectiva por Rejilla. La excepción de bus libre durante la avería se
  declara en las notas para preservar el silencio frente al DC de las columnas.

[Medidas del audio]({out.name}/audio-verificado.json): AAC {V['AAC']['LUFS_I']:.2f}
LUFS-I y {V['AAC']['true_peak_dBTP']:.2f} dBTP; máster sin clipping. No hubo audición
propia: falta tu valoración perceptual, especialmente de dicción, relevos y percusión.

## Escritura y proceso

[Revisión de partitura y crítica](README-REVISION-PARTITURA.md),
[primera etapa](README-PRIMERA-ETAPA.md), [referencias](REFERENCIAS.md) y
[Compositor](../COMPOSITOR.md), con su skill local.

[PNG del audio]({out.name}/{final.name}),
[GIF del proceso de ocho segundos]({out.name}/{gif.name}) y
[explicación de etapas]({out.name}/proceso/README.md). Son capturas del trabajo
sonoro, no un visor terminado. Se conservan las fuentes y las tomas previas.

Para reproducir una toma nueva: audio_comun.py crea carpeta exclusiva; los dos
intérpretes producen fuentes; verificar_fuentes.py las mide; mezclar_audio.py
realiza el arreglo/Rejilla/máster; verificar_audio.py comprueba el archivo y
cerrar_audio.py registra entrega y proceso. No relanzar contra destinos existentes.

**Siguiente fase separada: visor e instrumento visual, después hazvideo.py para
que Canek renderice el video completo.** No se produjo MP4 ni se hizo push.
''',encoding='utf8')
    (BASE/'ULTIMO-AUDIO.txt').write_text(out.name,encoding='utf8')
    for name in ['verificar_audio.py','cerrar_audio.py']:
        dst=out/'fuentes-fijadas'/name
        if not dst.exists():guardar(dst,(BASE/name).read_bytes())
    files={str(p.relative_to(out)).replace('\\','/'):sha(p) for p in out.rglob('*') if p.is_file()}
    jsave(out/'receta-audio.json',{'ejecucion':cfg,'artefactos_sha256':files,'fuentes_raiz_sha256':{n:sha(BASE/n) for n in ['audio_comun.py','interpretar_fuentes.cjs','interpretar_propios.py','verificar_fuentes.py','mezclar_audio.py','verificar_audio.py','cerrar_audio.py']},'gif':{'nombre':gif.name,'cuadros':4,'segundos':secs,'bytes':gif.stat().st_size,'loop':0},'primera_toma':'por-aqui-cancion-s22-56b7e385f96f','nota':'receta excluye su propia huella; revisión visual posterior se declara aparte','audicion_propia':False,'visor_video_producidos':False})
    print(json.dumps({'entrega':out.name,'gif_bytes':gif.stat().st_size,'gif_segundos':secs,'huellas':len(files)},ensure_ascii=False))

if __name__=='__main__':main()
