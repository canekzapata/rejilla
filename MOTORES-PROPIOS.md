# Los instrumentos que nacieron en las piezas

El taller conserva el catálogo anterior, los doce prototipos y el código de todos los proyectos de Rejilla censados en esta edición. Además trae **38 ejemplos ejecutables de motores, variantes y procesos** que antes faltaban: Siringua, cinta de meandro, lagos, convoy, traductor, gargantas, cuerdas de la duna, cráteres y otras voces. Son ejemplos de mecanismos diferentes; la cifra no significa 38 instrumentos independientes.

## Pedirlos como los pide Canek

Abre la carpeta con tu asistente y dile: «Lee AGENTS.md y MOTORES-PROPIOS.md. Haz una frase nueva con Siringua que diga “el agua recuerda mi nombre”. Primero entrégala sola, después haz una respuesta con cuerdas de la duna. Explica cómo se articuló el texto y entrega WAV, gráficas, PNGs y GIF del proceso». El asistente debe leer el registro, usar el motor original y producir archivos reales.

Puedes escuchar los ejemplos sin instalar nada en motores-propios.html o buscarlos por nombre en el catálogo del laboratorio. Escuchar una muestra funciona sin Python y sin Node.js. Para generar música nueva con estos motores se usa el productor local y sus dependencias.

Para trabajar manualmente, prepara Python como explica el manual y abre la ventana del taller. Selecciona uno de los JSON de `ejemplos/motores-propios/` y pulsa Producir. El pedido contiene `motor_propio`: el taller usa su motor temporal original aunque el selector general diga Directo o Rejilla. Los tiempos de estos ejemplos son **segundos**. Conserva el ejemplo y modifica una copia.

## Qué papel tienen Python, JavaScript y FFmpeg

Python organiza la producción, llama motores, guarda WAV y calcula gráficas. Los motores `.py` se ejecutan ahí. Los motores `.js` y `.cjs` de esta ampliación se ejecutan con Node.js, sin instalar paquetes npm. El laboratorio usa JavaScript del navegador y ofrece un conjunto menor de instrumentos para tocar directamente.

Si el motor necesita Node.js, instálalo desde https://nodejs.org/en/download para Windows o macOS, según tu equipo, y vuelve a abrir el taller. Tu asistente puede revisar si ya está disponible. El ZIP conserva el lector fonético y el runtime de eSpeak para Siringua; no necesita descargar una voz humana ni conectarse a Teia para estos ejemplos.

FFmpeg es un programa independiente: puede funcionar sin Python. En el taller, Python lo controla cuando eliges la producción espectral con `spectrumsynth`. FFmpeg no interpreta por sí solo los instrumentos escritos en Python o JavaScript. Los 38 ejemplos de esta ampliación producen audio temporal y no requieren FFmpeg.

## Siringua: un ave que se acerca a las palabras

La idea artística es que agua y canto de ave compartan articulación. El texto pasa a una sucesión de fonemas; una voz de agua los articula y una fuente de canto sintético responde. La variante `siringua-vocoder` toma la energía de la articulación del agua en 28 bandas y la aplica a una portadora de ave más rica. Las consonantes y la voz aparecen gradualmente. El vocoder describe una transformación espectral; no significa que todos los sonidos se hayan dibujado en la Rejilla ni que un modelo de aprendizaje automático aprenda a hablar.

Empieza con `siringua.json`: cambia `texto`, conserva `language: es-MX` y la semilla para comparar. Después prueba `siringua-vocoder.json` con la misma frase. Para inglés usa `language: en-US`. Pide una muestra aislada de cada variante, su partitura fonética y el espectrograma. En la onda ves entradas y pausas; en el espectrograma ves dónde persiste energía y cómo cambia la articulación. No confundas esas líneas con una transcripción de palabras ni con una medición de inteligibilidad.

La explicación fuente–filtro ayuda a separar lo que vibra de las resonancias que lo articulan. La invención es la relación musical entre agua, ave y aparición de la voz; la técnica de filtrado tiene una historia previa. Consulta Smith, Formant Synthesis Models, citado en el manual. Las fuentes y el límite de cada variante están en `MOTORES-NUEVOS.json`.

## Cinta y lagos: componer con el desgaste

La cinta de meandro hace que la velocidad de lectura cambie según una curva. Si lees más despacio, bajan juntas la altura y la velocidad del material; esto permite escribir una melodía cuya memoria se deforma. Se añaden variaciones lentas y rápidas de velocidad, saturación, filtrado y siseo. El lago de herradura recircula un fragmento y deteriora zonas acumulativamente: cada regreso conserva una herida de la vuelta anterior.

Compara dos copias de `cinta-meandro.json`: una con velocidad constante y otra con la curva del ejemplo. Conserva la entrada y la semilla. La gráfica de velocidad explica el gesto y el espectrograma permite revisar el descenso de las componentes. Para usar tu propio audio, el asistente puede poner una ruta WAV en `entrada_wav`; el ejemplo incluido genera su propia entrada sintética. En `lago-herradura.json`, revisa las vueltas registradas en la receta y pide una comparación de la primera y la última vuelta. Es una simulación de desgaste, no evidencia de cinta física envejecida.

## Convoy y traductor: dos maneras de cambiar sin llegar

El convoy distribuye parciales por octavas y superpone trenes de golpes para construir ascenso y aceleración aparentes. `dir` gobierna la dirección y `cerca` el acercamiento. Pide dos versiones con igual material y direcciones contrarias. Compara el movimiento de las bandas en el espectrograma y el tiempo entre golpes. Una muestra corta sólo muestra un tramo de la ilusión.

El traductor analiza una guía mediante predicción lineal (LPC). El control `oxido` transforma una articulación cuantizada hacia un tubo derivado de un perfil. La intención es que una máquina pierda el habla y adquiera otra cavidad. El ejemplo usa **VozAgua procedural**, no la voz humana Sabina de la obra original. Puedes aportar una guía WAV PCM16 mono o estéreo a 48 kHz mediante `guia_wav`; tu asistente debe comprobar su formato. Conserva notas y guía, compara `oxido` constante en 0 y en 1, y después dibuja una transición. La curva muestra la decisión; el espectrograma muestra su efecto, sin demostrar por sí solo que se entiendan las palabras.

## Gargantas, cuerdas y cráteres

Las gargantas de montaña, río y volcán usan fuentes oscilantes y tubos con áreas variables. La relación con un terreno es una regla de diseño: en estos ejemplos el perfil es sintético y está declarado en el JSON. Cambia el perfil manteniendo la nota para estudiar el timbre; cambia la nota manteniendo el perfil para separar ambos gestos. Las guías de onda digitales modelan propagación y reflexión mediante retardos y filtros; la exposición de Smith desarrolla ese fundamento: https://www.dsprelated.com/freebooks/pasp/Digital_Waveguide_Models.html

Las cuerdas de la duna usan realimentación de una línea de retardo, filtrado y excitación. Guembri y guitarra son variantes del mismo motor. Compara la misma frase y pide que el asistente muestre qué parámetros cambian. En los cráteres, varios modos de una membrana circular se excitan con golpes; diámetro, posición y envejecimiento modifican el resultado. Los ejemplos joven, viejo y complejo permiten conservar la secuencia y contrastar respuestas. El mapa entre cráter y tambor es una propuesta compositiva, no una grabación de la Luna.

El registro también incluye arpa, armonio, tambura, bajo dub, magma, estratos, avalancha, qraqeb, impresora, torniquete, campana, lluvia, pantalla, luciérnagas, cobre vocal y Halo de fase. Cada ficha explica la idea, la fuente concreta, los controles del ejemplo y su límite. Algunos son efectos o variantes de una familia.

## Cómo saber qué hay y qué se probó

`COBERTURA-INSTRUMENTOS.md` es el índice legible de la ampliación. `MOTORES-NUEVOS.json` relaciona los 38 ejemplos con su código original. `PRUEBAS-MOTORES.json` registra las ejecuciones y las muestras. Cada muestra conserva pedido, receta, semilla, huellas, WAV, tres gráficas y GIF de 5.1 segundos. El GIF recorre entradas/controles, onda y espectrograma calculados en esa ejecución; no pretende mostrar borradores históricos.

`INVENTARIO-REJILLA.json` enumera todos los archivos de código, recetas y documentos censados, con su origen y SHA-256. Conserva variantes históricas; un archivo o una función no equivale a un instrumento. Las rutas históricas muy largas se guardan por huella en `archivo/` y el inventario permite encontrarlas. Los motores principales mantienen su jerarquía en `research/rejilla/`.

Las canciones completas antiguas pueden necesitar sus datos de terreno, bancos de voz, grabaciones o herramientas externas. Sus fuentes se conservan, pero copiar un renderizador no demuestra que toda obra antigua pueda regenerarse sin esos recursos. Los ejemplos portables de esta ampliación usan entradas propias declaradas. No se incluyen indiscriminadamente los renders pesados ni los bancos humanos del equipo de Canek. Antes de prometer una regeneración íntegra, el asistente debe revisar sus dependencias y explicarlas.

Las comprobaciones de señal no son una escucha humana. La verificación del paquete distingue esas pruebas, las revisiones visuales y las plataformas donde realmente se ejecutó. Las nuevas invenciones deben conservar el mismo cuidado: mecanismo reutilizable, dos variantes comparables, audio real, gráficas con unidades, PNGs y GIF del proceso, explicación y citas verificadas.
