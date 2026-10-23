# Úsalo como lo usa Canek: «oye, haz tal»

## Para ti

1. Extrae el ZIP completo.
2. Abre la carpeta extraída como proyecto en tu asistente de programación (por ejemplo, uno que trabaje con archivos y pueda ejecutar Python). Un chat sin acceso a la carpeta puede ayudarte a pensar, pero no producir aquí por sí solo.
3. Dile: **«Lee AGENTS.md, USAR-CON-TU-ASISTENTE.md e INSTRUCCIONES-PARA-CREAR.md. Prepara lo que necesites dentro de esta carpeta y úsala para hacer música conmigo. No sé terminal: encárgate tú de ejecutar y comprobar los programas.»**
4. Pide la música o instrumento como se lo pedirías a alguien que está colaborando contigo. Puedes compartir referencias, una imagen, un texto o un audio; no son requisitos para empezar. Una imagen de referencia no se convierte automáticamente en una partitura espectral: el asistente debe explicar la regla que propone.

No necesitas editar JSON ni aprender comandos para esta ruta. Los ejemplos y el manual ayudan al asistente a trabajar y a ti a entender o cuestionar lo que hizo. Usa el laboratorio para escuchar familias, comparar muestras y señalar sonidos que sí o no te interesan.

## Pedidos que puedes copiar y cambiar

**Primera canción:** «Haz una pieza de 40 segundos a 96 BPM, con bajo cálido, campanas y una melodía que primero pregunta y luego contesta. Que el final cambie la respuesta. Entrega audio, partitura, imágenes y GIF, y explícame por qué elegiste esos instrumentos.»

**Boca de tres tiempos:** «Haz que la Boca de tres tiempos sostenga una vocal mientras las notas se mueven y aparezcan consonantes separadas. Luego reúne los tres recorridos. Quiero oír primero el instrumento solo y después una escena con Cristal orbital y Bajo de androide. Incluye gráficas que permitan ver qué recorridos se separaron.»

**Instrumento inventado:** «Inventa una cuerda que empieza como madera y termina como metal. Justifica la idea con una técnica de síntesis concreta y referencias; distingue lo que inventaste de lo que viene de la teoría. Haz dos variantes, compara la misma frase y entrega un instrumento reutilizable con controles comprensibles.»

**Revisión musical:** «La melodía se repite demasiado y no se entiende el regreso. Conserva el motivo, cambia la respuesta y deja un tramo donde el bajo tome la voz principal. Guarda esta versión aparte y compárala con la anterior.»

**Desde una imagen:** «Mira esta imagen. Propón una relación musical concreta entre sus formas y las entradas, registro o timbres. Explica esa traducción, no digas que la imagen ya contiene la canción. Haz un boceto, escucha mi comentario y desarrolla la pieza.»

**Sólo explorar:** «Muéstrame cinco instrumentos de esta biblioteca que puedan responder a una voz. Usa las muestras que ya hay; explica sus diferencias y cuáles puedes producir aquí sin recursos externos.»

## Qué debe hacer el asistente

Leer las instrucciones y los archivos reales. Preparar un entorno con Python 3.13 y `requirements.txt` dentro de la carpeta si hace falta. Puede ejecutar `preparar.py`, que crea `.venv`; usar después su intérprete para que encuentre las dependencias. Para Rejilla debe localizar FFmpeg con spectrumsynth; si falta, explicar cómo conseguirlo desde la fuente oficial y continuar con síntesis temporal cuando esa ruta satisfaga el pedido. No presentar un render temporal como si hubiera pasado por spectrumsynth.

Para una primera pieza, duplicar y editar una partitura de `ejemplos/` y ejecutar `python/taller.py partitura.json --motor directo` o `--motor rejilla` con el intérprete del entorno. El programa guarda audio, partitura, receta, PNGs y GIF. Para un prototipo usar `ejemplos/doce/<id>.json`: el productor detecta la API temporal original. Las partituras generales usan pulsos; las de los doce usan segundos. No confundirlos.

Los cuatro ejemplos son material inicial, no fronteras artísticas. Para una pieza mayor, organizar secciones, ajustar controles o escribir un nuevo motor/ficha cuando haga falta. El productor didáctico limita las dimensiones; si el pedido las excede, producir y unir secciones con un arreglo continuo o ampliar la herramienta después de revisar memoria, tiempos y colas. Documentar cualquier adaptación sin tocar las fuentes originales. El registro de cambios debe acompañar la pieza, no trasladarse al usuario como tarea técnica.

Las fichas `modal`, `golpe`, `boca` y `arco` tienen traducción en `biblioteca/motores/rejilla.py`. Las otras familias pueden necesitar `web.js`, `objetos.js`, `gemelo.py`, `python.py` o `meleeviewer.js`; inspeccionar su API antes de usarlas. El productor didáctico no despacha todos esos motores automáticamente. El catálogo incluye 231 muestras conservadas para escuchar y comparar, más doce prototipos; eso no es una promesa de portabilidad universal. No inventar una implementación silenciosa como sustituto.

Al terminar debe entregar audio real y archivos locales, no sólo un bloque de código. Explicar intención, forma, cambios, técnicas, citas y límites. No decir «lo escuché» si sólo calculó medidas. Para nuevas invenciones, las gráficas y muestras comparativas son obligatorias. Debe conservar capturas reales, no reconstruir una historia falsa del proceso.

## Si después quieres usar un DAW o Sibelius

Lee `DAW-Y-SIBELIUS.md`: explica el uso actual de WAV y las ampliaciones posibles mediante archivos de notas, bancos de muestras o plugins. Puedes desarrollarlas con tu asistente o pedir ayuda a Canek. Esta edición sólo documenta esas rutas: no incluye un plugin, un banco de muestras ni conversión MIDI/MusicXML. Si sólo quieres hacer música, puedes continuar con el flujo actual sin desarrollar una integración.

## Qué cambia según el asistente y sus permisos

El ZIP no incluye una IA ni una cuenta. Necesitas un asistente que tenga acceso autorizado a estos archivos y herramientas de ejecución. Algunos leen `AGENTS.md` automáticamente y otros requieren que lo indiques al empezar. Sus permisos de ejecución, instalaciones y acceso a internet dependen de la aplicación que uses. No se promete que un chat ordinario pueda abrir archivos de tu equipo ni que todos los asistentes sigan instrucciones sin supervisión.

Si el asistente se queda en una explicación, dile: «Quiero que lo produzcas aquí: ejecuta los programas, comprueba los archivos y entrega el audio con sus imágenes. Usa las instrucciones del proyecto.»

## Instrumentos originales de todas las piezas

Consultar primero `MOTORES-PROPIOS.md`, `MOTORES-NUEVOS.json` y `COBERTURA-INSTRUMENTOS.md`. Hay 38 ejemplos ejecutables de motores, variantes y procesos originales. Para Siringua, cinta, convoy, traductor, gargantas, duna y cráteres usar sus motores reales mediante `ejemplos/motores-propios/<id>.json`; `python/taller.py` detecta `motor_propio`. No sustituirlos por un timbre modal genérico ni concluir que no existen por no figurar en el catálogo antiguo.

Los motores JS necesitan Node.js local; preparar Python y Node cuando corresponda. No necesitan npm ni FFmpeg estos 38 ejemplos. Tiempos en segundos. Se pueden editar las configuraciones conservando el original y usar el mismo productor. Revisar la API real para ampliar forma, notas o controles. Mantener el requisito de audio, gráficas, PNGs y GIF real.

El inventario `INVENTARIO-REJILLA.json` relaciona todos los archivos censados con su ruta y huella, incluidas variantes históricas que se archivaron en rutas cortas. El código principal está en `research/rejilla/`. Para una canción antigua completa, revisar recursos externos antes de prometer regenerarla: los bancos de voz humana y renders pesados no viajan. Los ejemplos nuevos identifican sus entradas sintéticas. Nunca presentar esos ejemplos como grabaciones originales de Sabina o perfiles medidos de terreno.

**Siringua:** «Haz que Siringua diga una frase nueva y que el ave vaya tomando la articulación. Compara agua/ave y vocoder. Incluye partitura fonética, espectrogramas y GIF».
