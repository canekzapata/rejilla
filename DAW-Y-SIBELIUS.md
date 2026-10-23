# Llevar Rejilla a un DAW o a Sibelius

Esta información sirve para planear una ampliación, desarrollarla por tu cuenta o pedir ayuda a Canek. **Esta edición no implementa un plugin, un banco de muestras ni importación/exportación de MIDI o MusicXML.** Los motores y ejemplos existentes se conservan. Fecha de revisión: 20 de octubre de 2026.

## Qué puedes hacer hoy

Puedes producir un WAV con Rejilla e importarlo como audio en un DAW que admita ese formato. Allí puedes cortarlo, combinarlo con grabaciones, procesarlo y mezclarlo. Eso conserva el sonido producido, pero el WAV no contiene las notas editables del instrumento. Cambiar notas requiere volver a producirlas o trabajar con una futura versión del instrumento dentro del DAW.

Los WAV del productor espectral pueden usar una frecuencia de muestreo poco habitual. Al importarlos, deja que el DAW los convierta a la frecuencia de tu sesión. Para una futura exportación dedicada conviene ofrecer 44.1 o 48 kHz y documentar la conversión. Remuestrear implica calcular una nueva señal; cambiar sólo la etiqueta del sample rate altera duración y altura.

El productor actual guarda una mezcla. Todavía no ofrece una exportación general de cada pista por separado. El MIDI que aparece como números en las partituras JSON describe alturas; esos archivos JSON no son archivos MIDI `.mid`.

## Tres cosas que conviene distinguir

**Audio:** el resultado que ya suena. Un WAV conserva el timbre y la interpretación calculada, pero no ofrece los controles internos del instrumento.

**Partitura o eventos:** notas, tiempos, duraciones y parte de la expresión. MIDI resulta útil para secuenciadores; MusicXML está orientado al intercambio de notación. Sibelius admite ambos. Ninguno incorpora automáticamente el motor Python/JavaScript de Rejilla ni reproduce todos sus recorridos internos. [1]

**Instrumento reproducible:** el programa o banco que recibe notas y produce sonido. Para usarlo dentro de otra aplicación hay que preparar un formato que esa aplicación y su versión acepten. Los archivos `.py`, `.js` y las fichas `.json` de este paquete no se instalan directamente como instrumentos virtuales.

## ¿Puedo poner un instrumento propio en Sibelius?

Sí, mediante un dispositivo de reproducción compatible. Sibelius puede usar instrumentos virtuales VST/AU y dispositivos MIDI; el formato y la versión concretos deben comprobarse en el equipo de destino. No conviene suponer que cualquier VST3, AU o arquitectura funcionará por el solo nombre del formato. [2]

La ruta con muestras sería: producir notas aisladas del instrumento, organizarlas en un banco para un sampler, cargar ese sampler como instrumento virtual compatible y asignarlo a los pentagramas correspondientes. **No se trata de subir el Python a Sibelius.** El sampler es quien produce audio a partir de las muestras y las notas que recibe.

La otra ruta consiste en adaptar el propio motor a un instrumento virtual. Así puede responder a notas y controles durante la reproducción. Es una tarea de desarrollo de software: hay que resolver la interfaz del plugin, el procesamiento por bloques y su comunicación con el anfitrión, además de conservar el comportamiento musical.

Un **sound set** le describe a Sibelius los sonidos y capacidades de un dispositivo. No contiene las grabaciones ni el sintetizador. Cuando no existe uno específico, la configuración manual permite declarar sonidos por canal. Eso organiza la reproducción, pero no convierte por sí solo un motor de Rejilla a plugin. [2,3]

Crear o nombrar un instrumento en la partitura tampoco fabrica su sonido: la definición de notación y la fuente de reproducción deben conectarse.

## Ruta futura A: archivos para seguir trabajando

Una primera ampliación puede incorporar exportación de MIDI, MusicXML y pistas de audio separadas. Permitiría pedir: «haz esta pieza y déjame las notas para cambiarlas en mi DAW», o «dame una partitura para abrir en Sibelius».

Para que sea útil habría que guardar tempo y compás, nombrar pistas, definir unidades y documentar qué articulaciones y controles se traducen. Las pistas de audio deberían compartir el mismo inicio y duración de referencia, con colas conservadas, para alinearlas sin adivinar. Los instrumentos con altura decimal, cambios de afinación o recorridos continuos necesitan reglas específicas: redondear sus notas sin avisar perdería información.

La prueba mínima sería abrir los archivos en la aplicación real y comparar entradas, alturas, duraciones, tempo y asignaciones. Una validación de formato no sustituye esa importación. La maquetación de una partitura puede requerir revisión después de importar MusicXML.

## Ruta futura B: banco de muestras para un sampler

Puede ser un camino práctico para campanas, percusiones y otros sonidos con respuesta relativamente autónoma por nota. Hay que decidir registro, separación entre notas muestreadas, intensidades, duración de colas, comportamiento al soltar y posibles variaciones. Después se preparan los archivos y el mapa que entienda el sampler elegido.

Se debe comparar el banco con el motor original: notas intermedias, extremos del registro, distintas fuerzas, acordes y repeticiones. Transportar una sola grabación cambia también su tiempo y su espectro; por eso una muestra aislada no garantiza que todo el registro conserve el carácter original.

**Límite de los instrumentos inventados:** una muestra fija de Boca conserva una interpretación particular de vocales, consonantes y melodía, no sus tres recorridos editables. Muestrear el Órgano de divisores con memoria no conserva automáticamente su estado previo. El Piano de tres presentes consulta la nota futura: disparar muestras independientes no reproduce esa regla por sí solo. Se pueden diseñar aproximaciones, pero deben declararse como variantes.

## Ruta futura C: instrumento virtual con motor propio

Esta opción puede conservar más controles y comportamiento que un banco fijo, pero requiere una implementación específica. Hay que decidir cómo entran y terminan las notas, cómo se manejan voces simultáneas, cómo se guardan presets y cómo llegan las automatizaciones. También hay que comprobar latencia, uso de CPU, estabilidad y reinicio de estado.

Para los instrumentos que conocen la partitura completa, como Piano de tres presentes, hay una decisión adicional: recibir eventos con antelación, introducir latencia o rediseñar la regla para ejecución en vivo. Un plugin no puede conocer una nota futura que todavía no recibió.

La adaptación debe elegir plataforma, arquitectura y formato según el anfitrión y la versión reales. Por ejemplo, Ableton documenta sus formatos VST y Audio Units; eso no demuestra compatibilidad idéntica en Sibelius u otro DAW. Se necesitan pruebas independientes. [4]

No es obligatorio desarrollar un plugin para seguir usando Rejilla: se puede conservar el flujo conversacional, producir audio fuera del DAW y llevar los resultados a la sesión.

## Cómo pedir ayuda o encargar una ampliación

Puedes decirle a tu asistente: «Quiero llevar este instrumento a mi programa. Lee DAW-Y-SIBELIUS.md, revisa su motor y propón una ruta. Distingue qué existe de lo que falta desarrollar antes de prometer compatibilidad».

Para pedir ayuda a Canek, prepara un ejemplo pequeño y estos datos: aplicación y versión, Windows o Mac, arquitectura si la conoces, instrumento de la biblioteca, qué quieres editar o tocar y qué resultado necesitas. Añade si te basta el audio, si necesitas las notas o si buscas controlar el sintetizador dentro del programa. Si hubo un fallo, conserva el archivo y el mensaje exacto.

El desarrollo futuro debe conservar las mismas entregas del taller: explicación, audio comparativo, parámetros, imágenes del comportamiento y proceso, GIF corto y pruebas declaradas. No se debe presentar una ruta propuesta como integración ya construida o comprobada.

## Fuentes oficiales

[1] Avid, intercambio de partituras con Sibelius; importación MusicXML y revisión posterior. https://www.avid.com/resource-center/how-to-migrate-from-finale-to-sibelius

[2] Avid, dispositivos MIDI e instrumentos virtuales VST/AU; función del sound set. https://kb.avid.com/pkb/articles/en_US/faq/Can-I-use-my-external-MIDI-playback-device-with-Sibelius

[3] Avid, Sibelius Reference Guide 2022.10, Playback Devices y Manual Sound Sets. La referencia describe la configuración; para desarrollar una integración hay que contrastarla con la edición de destino. https://resources.avid.com/SupportFiles/Sibelius/2022.10/Sibelius_Reference.pdf

[4] Ableton, manual de Live 12, Using Plug-Ins. Referencia para ese anfitrión, no promesa de compatibilidad universal. https://www.ableton.com/en/live-manual/12/using-plug-ins/
