# P-adic Bell — Canek Zapata, 2026

Versión 1.2.0. Nombre e interfaz en inglés; cinco piezas, pétalos espectrales y escucha espacial ligada a la cámara. La versión 1.1.0 se conserva en su entrega exclusiva. La versión anterior «Otra distancia» se conserva en git y en su entrega exclusiva.

Escultura musical 3D de porcelana pop y cobre. Un cuerpo de 64 láminas perforadas se abre como una campana y se pliega en ocho cámaras de color. Hecha por pedido de Canek el 21 de octubre de 2026, a partir de su campana p-ádica.

Abre **abrir-escultura.bat** en Windows con Python instalado. Sirve `dist/` por HTTP en tu propia computadora y abre el navegador; reutiliza su servidor si sigue disponible. Requiere WebGL 2 y AudioWorklet en un navegador moderno. No necesita descargar bibliotecas ni conectarse a un servicio. Para cerrar el servidor del lanzador, termina ese proceso de Python. El puerto se guarda únicamente en `puerto.local`, excluido de git. En otros sistemas: `python -m http.server 8000 --directory dist` y abre http://localhost:8000.

## Tocar y recorrer

- Pulsa una lámina para golpear esa región. Arrástrala horizontalmente para plegar el acoplamiento mientras suena; también puedes usar **FOLD**.
- Arrastra el fondo para girar; la rueda acerca la mirada. Mayúsculas al arrastrar permite girar incluso sobre una lámina.
- Los ocho círculos son enlaces a familias. **Inside** aproxima cámara y escucha a una familia; **Outside** vuelve al conjunto. Girar, acercarte y entrar modifican la proyección sonora. Volver/avanzar del navegador conserva el audio en curso.
- A S D F G H J K cambian la altura y golpean la última región. E entra/sale, flechas eligen familia y espacio apaga la resonancia. Todos los controles tienen recorrido de teclado.
- **Listen** abre cinco piezas compuestas para este cuerpo. **Sound** silencia la salida sin apagar la simulación. El audio empieza tras un gesto.
- **?** abre parentesco, tensión, caída y altura, movimiento reducido, enlace al lugar actual y postal PNG 1200×630 sin interfaz. La postal incluye receta iTXt, parámetros, cámara, energía RMS, nonce y SHA-256. No captura sonido ni incluye audio en el enlace.

## Qué relación guarda con la matemática

Se conserva byte por byte `../campana-padica/motor.mjs`: 64 osciladores reales con acoplamiento entre cuadrícula y vecindad 2-ádica, integración Verlet y amortiguamiento. Plegar cambia la rigidez y realiza trabajo; cambiar los parámetros conserva los desplazamientos y las velocidades existentes. Las familias corresponden a las clases módulo 8; al cerrar, cada par separado por 32 se aproxima antes que los parentescos de menor orden.

La geometría es una traducción espacial de esa jerarquía, no una incrustación euclidiana exacta del espacio 2-ádico. No se afirma representar literalmente 64 puntos con todas sus distancias matemáticas. La cámara sigue la posición de su familia durante el plegado. Cambiar familia modifica la captación. En la versión 1.2, la cámara también sitúa y orienta los oídos; la cercanía redistribuye ocho aperturas y abre una resonancia interior sintética.

El procesador informa RMS del desplazamiento de cada región en ventanas de 1024 muestras. Esa envolvente aumenta el brillo y, salvo movimiento reducido, el espesor visual. No se dibuja la oscilación de audio submuestreada a velocidad de pantalla. La escultura en reposo no finge estar resonando. Los PNGs del proceso muestran estados reales de trabajo y pruebas, sin pretender que documenten una escucha humana.

## Proceso y verificación

Entrega vigente: [p-adic-bell-spatial-s20261021-46a649a69ad4](p-adic-bell-spatial-s20261021-46a649a69ad4/proceso/README.md). Versión 1.1 conservada: [p-adic-bell-s20261021-0dd3b9a583a5](p-adic-bell-s20261021-0dd3b9a583a5/proceso/README.md). Entrega anterior conservada: [otra-distancia-s20261021-b9431c1221b7](otra-distancia-s20261021-b9431c1221b7/proceso/README.md). Semilla de identificación `20261021`; la geometría de esta versión es determinista y no usa azar. El identificador se obtuvo de imagen inicial + programa + versión + nonce nuevo. La receta conserva el SHA completo, nonce y hashes de contenido. Las postales individuales obtienen además su propio identificador.

`python preparar.py` comprueba la copia del motor y empaqueta el procesador. `node pruebas.mjs` verifica identidad de audio muestra por muestra, envolvente contra el motor original, huecos, espesor, parentesco espacial, rutas y continuidad de estado. Three.js r180, MIT, vendorizado desde una copia local y documentado en PROCEDENCIA.json. No se modificó la biblioteca.

En navegador se probaron audio por gesto y teclado, plegado, entrada/salida, historial sin reiniciar el motor, vista estrecha y exportación real PNG. La salida de prueba no activó el limitador. Las pruebas numéricas no sustituyen una valoración auditiva humana ni demuestran estabilidad para toda combinación posible de parámetros. El procesador original ya incluye protección de salida.

URL canónica propuesta: **https://canekzapata.net/p-adic-bell/**. Es un TODO en los metadatos: esta entrega es local, sin publicación ni repositorio remoto. `og.png` es un render de la propia escena sin interfaz; `favicon.png` se extrae de esa imagen.

## Estado del loop

Premisa: habitar el mismo cuerpo que se golpea. Operador: plegar su cercanía durante la resonancia. Resultado: campana abierta, ocho cámaras plegadas, vínculos a familias y postales con receta. El primer encuadre recortaba el cuerpo en una ventana estrecha y el material se veía demasiado lavado; las etapas 02 y 03 conservan ese ajuste real. La primera prueba de teclado detectó un selector que confundía CANVAS con A; se corrigió antes de la validación final.

El GIF reúne borradores sucesivos y pruebas de interacción; no es una grabación continua ni una vista de pasos internos del renderizador. No se cambió la campana anterior. No se ha hecho una prueba en teléfono físico ni una sesión de escucha humana por parte del agente.


## Cinco piezas para un solo cuerpo

| Pieza | Duración de la partitura | Carácter |
|---|---:|---|
| Porcelain Rain | 0:42 | Registro alto, gotas y arpegios espaciales |
| Folded Garden | 0:48 | Síncopas, parejas de parentesco y respuestas |
| Binary Tide | 0:54 | Registro grave y ondas lentas de plegado |
| Glass Orchard | 0:50 | Registro aéreo, cuatro notas y espacios amplios |
| Afterimage Waltz | 0:57 | Vals de tres pulsos, acentos y ecos suaves |

Las partituras viven en `dist/canciones.mjs`. Un único motor cambia de afinación: no son voces independientes con alturas retenidas ni archivos de audio reproducidos de fondo. Eventos programados por muestra dentro del AudioWorklet, sin temporizadores de pantalla. Puedes tocar encima y recorrer familias durante una pieza. Ajustar afinación, tensión, caída, parentesco o plegado cancela la partitura y conserva el cuerpo resonante para tocar libremente.

La pausa detiene el avance de la partitura; lo que ya sonaba sigue decayendo. Reanudar continúa desde el punto guardado. Stop hace un fundido de 25 ms y vacía el cuerpo. Al terminar la partitura no llegan más golpes y la cola puede seguir resonando. El menú permite volver a tocarla. Los M4A de la nueva entrega son renders a 48 kHz con la ganancia de la interfaz (.9), AAC 192 kb/s y un fundido final de 50 ms; la reproducción automática en el instrumento usa el motor en vivo.

## Adentro, afuera y lo que se escucha — 1.2.0

Ahora la escucha sigue la posición y orientación de la cámara. Ocho aperturas reciben las señales reales de las familias del motor, se ubican en sus centros visibles y pasan por HRTF, ganancias por cercanía, retardos de llegada y una cámara sintética breve. El modelo de recinto es una decisión de la obra, sin simulación acústica de las superficies. Afuera predomina el conjunto abierto; al acercarte a una familia ganan presencia sus aperturas próximas y la cola interior. Girar cambia la dirección percibida. La casilla **Spatial listening** de la ayuda permite comparar con el estéreo original sin reiniciar el cuerpo ni la partitura. Mute sigue apagando toda la salida.

La regla de cercanía es continua, de modo que el zoom también cambia la recepción. La cámara en modo Inside se aproxima a la familia elegida; no hay un cambio seco de preset por pulsar el botón. El estado vibratorio y las cinco partituras permanecen en el motor original. El analizador de los pétalos está después de la proyección y la receta de la postal guarda también la escucha espacial.

La versión 1.1 sólo movía la vista al entrar/salir con la misma familia. Canek pidió hacer audible esa diferencia el 21 de octubre de 2026; esta revisión implementa ese pedido.

Los tres documentos solicitados están en [Instrumentos teóricos en 3D](docs/README.md): [idea artística](docs/01-instrumentos-teoricos-como-espacios.md), [gramática de representación](docs/02-gramatica-de-representacion-3d.md) y [acústica y validación de P-adic Bell](docs/03-p-adic-bell-acustica-y-validacion.md).

`node pruebas_espaciales.mjs` verifica la descomposición del motor, ocho buses, campo de ganancias y respuesta determinista. `dist/prueba-espacial.html` renderiza la misma excitación con seis condiciones de escucha en OfflineAudioContext: fuera, dentro, referencia original en ambas vistas y un foco aislado con dos orientaciones. La prueba pasó las cinco condiciones: referencia original idéntica, diferencia interior más allá de una ganancia escalar (residuo relativo 0.8028), mayor cola, inversión del balance de oídos y picos menores a .98 (máximo medido .3486). Son medidas de esta prueba y no una evaluación perceptiva humana. Los audios exterior/interior de la entrega salen de esos renders reales.

## Pétalos de espectro real

Cada golpe efectivo del procesador, manual o de una pieza, abre una cinta pequeña junto a la lámina correspondiente. Muestra el espectro de la mezcla mono del cuerpo completo, no una frecuencia aislada de esa lámina. AnalyserNode de 4096 muestras; filas logarítmicas entre 45 y 6000 Hz (grave abajo, agudo arriba), muestreo visual cada 40 ms, intensidad derivada de dB reales y umbral visual para dejar desaparecer el silencio. Tiempo horizontal, a lo sumo tres cintas y vida de seis segundos; se encuadran dentro de la vista y liberan textura/material al terminar. Sin ruido ni notas inventadas para llenar el gráfico. Con movimiento reducido cambia a barras estáticas que sólo actualizan la amplitud.

La nueva entrega conserva siete PNGs de etapas más seis cuadros originales de una sola resonancia y sus tiempos de captura. Un GIF reúne los borradores reales; otro reúne el crecimiento real del espectro. La captura interrumpida antes de enviar una tecla no produjo cuadros: no se inventaron ni se sustituyeron por un proceso reconstruido.

`node verificar_canciones.mjs` comprueba las cinco partituras completas a 48 kHz, tiempos exactos de todos los golpes, fin, pausa/reanudación, continuidad al cambiar familia, cancelación manual, fundido de parada y mapa de 440 Hz/silencio del analizador. Con una ruta de salida nueva también exporta WAVs de trabajo; se quedan en `render/`, excluidos de git. Diferencia 0 en la prueba de audio manual contra el motor original; las cinco piezas completas no activaron su protección de salida. La valoración auditiva de Canek («las melodías son hermosas») es suya; no se atribuye al agente una escucha humana.
