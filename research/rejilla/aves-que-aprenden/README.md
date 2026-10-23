# Aves que aprenden palabras

Estudio del 18 de octubre de 2026. Premisa de Canek: el mensaje de una persona aparece poco a poco en el canto de un ave; pensar el jardín como lugar de voces que permanecen. No se implementó Teia ni una obra interactiva en este estudio.

## Lo que averiguamos

### Dos fuentes, no necesariamente dos tonalidades

En aves canoras, cada lado de la siringe puede aportar una fuente de sonido con control parcialmente independiente. Pueden alternar, superponerse o presentar especializaciones por registro. Eso permite bifonía; **bitonalidad** designa otra cosa: organizar música en dos centros tonales. Tampoco todo sonido con dos frecuencias demuestra dos lados activos: se documentó bifonía desde un solo lado en cenzontles. Nuestro modelo simplificado usa dos osciladores independientes; no reproduce ese último mecanismo ni el acoplamiento completo de la anatomía.

Fuente primaria: Zollinger, Riede y Suthers (2008), [Two-voice complexity from a single side of the syrinx in northern mockingbird vocalizations](https://pmc.ncbi.nlm.nih.gov/articles/PMC2569999/), Journal of Experimental Biology 211, 1978–1991. [Síntesis del investigador R. Suthers](https://www.internationalornithology.org/PROCEEDINGS_Durban/Symposium/S09/S09.2.htm).

### Crear voz: fuente y articulación

La vibración de los pliegues vocales genera la fuente periódica; las cavidades del tracto vocal modifican el sonido. Para sintetizar habla hay que construir además consonantes, transiciones, duraciones, pausas y prosodia. Mover sólo la altura no pronuncia palabras. Fuente institucional: [NIDCD, What is voice?](https://www.nidcd.nih.gov/health/taking-care-your-voice).

Nuestro `pajaro.js` implementa dos osciladores de van der Pol, control de presión y filtros de pico/tráquea. No acepta texto. `vozagua.js` convierte texto mediante el G2P mexicano en segmentos; sus vocales usan resonancias de burbujas y sus consonantes, ruido, golpes y modulaciones. Esta es síntesis procedimental, no una grabación humana ni una garantía de comprensión. El G2P actual también elimina acentos al convertir fonemas: una prosodia sensible al acento escrito todavía requiere un analizador que conserve esa información antes de normalizar.

### Vocoder

En el vocoder de canales, se divide el modulador en bandas y se siguen sus envolventes. Esas envolventes gobiernan las bandas correspondientes de una portadora. El modulador aporta articulación espectral y temporal; la portadora aporta material sonoro. Un silbido estrecho deja muchas bandas sin energía. Nuestro experimento compara ese caso con una fuente más rica y grave, antes del filtro del pico. No se trata de un vocoder neuronal ni de conversión de identidad vocal.

Referencia técnica primaria consultada: [implementación de investigación de Etienne Gaudrain](https://github.com/egaudrain/vocoder/blob/master/vocode.m). Nuestro código es una implementación pequeña propia en SciPy; no copia esa implementación MATLAB.

## Experimento disponible

**Dos poemas cantados:** [Siringua en español e inglés](siringua-dos-poemas-s181026-732b2b5085ae/README.md), 18 de octubre de 2026. Inglés con léxico fonético escrito para el poema; no es todavía un lector general. Dos escuchas completas, referencias de agua, partituras y proceso.

[Entrega s18026-148344606fb4](el-pajaro-aprende-s18026-148344606fb4/README.md).

Frase de prueba: **«todavía estoy aquí»**, escrita para este ensayo. Hay referencias de agua y pájaro, dos vocoders, un híbrido y una secuencia de tres intentos. La secuencia introduce por mezcla la articulación: **no hay aprendizaje automático**. La medición muestra más cobertura espectral de la portadora rica, pero no mide comprensión ni calidad estética. No se realizó escucha humana por parte del agente.

## Qué conviene hacer después

La continuación acordada se desarrolla en [Un lector reutilizable de pronunciación](PLAN-LECTOR-REUTILIZABLE-2026-10-18.md). El lector común vive en `difonos/runtime/lector.js`; inglés ya tiene eSpeak NG/WASM para texto nuevo y el adaptador puede entregar sus fonemas ARPABET a VozAgua. La entrega poética guardada aquí conserva su léxico artístico y no fue regenerada con el nuevo lector. Falta escuchar una interpretación nueva y revisar el módulo en navegador.

1. Escuchar la referencia de agua sin leer la frase: si no se entiende, trabajar primero articulación y duración de sílabas; un vocoder no recupera información ausente.
2. Comparar vocoder estrecho, rico e híbrido con el mismo texto. Elegir por escucha, sin confundir más bandas activas con mejor voz.
3. Desarrollar un control continuo de «aprendizaje»: bajar gradualmente el registro que articula, abrir resonancias de vocales, introducir consonantes y mantener el segundo lado como canto independiente. La mezcla de este ensayo es una primera aproximación.
4. Usar la segunda fuente para recordar el motivo o responder a la primera; evitar dos frases simultáneas al principio porque dificultan la comprensión.
5. Si esa transición funciona, portar el banco de filtros al navegador, renderizar frases cortas en un Worker y guardar en caché por texto/versión/semilla. No se verificó rendimiento de navegador; el prototipo actual usa Node y Python.

La relación con Messiaen se toma como dirección compositiva: aves con frases y caracteres que conservan, alternancia y contrapunto. Este ensayo no transcribe ni reproduce una obra suya. La imagen de las cámaras puede pasar a la escena después; aquí se estudió el sonido.

### Mensaje abierto de Teia en Siringua

**Paquete de ensayo para acuñar:** [Siringua prueba de canal Teia](siringua-prueba-teia-d5b2b63514a7/README.md). Incluye [ZIP interactivo](siringua-prueba-teia-d5b2b63514a7/siringua-prueba-teia-d5b2b63514a7.zip) con lector de canal, prueba local de canto en español/inglés y dependencias WASM locales. El render local cantó «todavía estoy aquí» (2.97 s, 24 kHz). La consulta viva desde el iframe de Teia y CORS/CSP siguen sin verificarse; la previsualización debe probarse antes de aprobar el mint.

[Prueba s181026-28b2327e61b3](siringua-mensaje-abierto-s181026-28b2327e61b3/README.md): se siguió en lectura un mensaje público del canal 10 hasta su JSON en IPFS; sus 18 palabras inglesas pasaron por eSpeak NG/WASM y se convirtieron en agua articulada, con una llamada del ave después de cada palabra. La demostración sonora funciona, aunque la consulta de Teia y la síntesis aún son dos pasos separados: este primer render usa el fragmento verificado que quedó archivado en la receta.

El primer adaptador y la composición reutilizable ya están en `teia-canal.js` y `siringua-mensajes.js`. El lector acepta sólo canales `unrestricted`, arranca desde el último evento para no cantar el historial, observa mensajes nuevos/editados/borrados, comprueba el estado oculto actual y devuelve segmentos con IDs estables de canal/mensaje/versión. Cada segmento conserva su texto original y queda limitado a 300 caracteres. Los lotes traen `items` y `withdrawn`; el reproductor confirma lo que ya cantó con `acknowledge(id)`. Para Siringua se selecciona `en-US` o `es-MX` explícitamente y `preparar()` convierte cada elemento de cola a agua y respuesta de ave; `render()` produce el PCM. El lector aún requiere comprobación directa en navegador contra TzKT/IPFS antes de usarlo en una edición publicada.

El contrato se contrastó con el cliente de Teia fijado en [channels.ts](https://github.com/teia-community/teia-ui/blob/9c47e90cc31892b0206f0597bfc9a808546b4e9/src/data/messaging/channels.ts), [api.ts](https://github.com/teia-community/teia-ui/blob/9c47e90cc31892b0206f0597bfc9a808546b4e9/src/data/messaging/api.ts) e [ipfs.ts](https://github.com/teia-community/teia-ui/blob/9c47e90cc31892b0206f0597bfc9a808546b4e9/src/data/messaging/ipfs.ts). Pruebas locales con fetch simulado cubren acceso, ocultamientos, borrados, edición, fallback de gateways, segmentación y pronunciación/generación en ambos idiomas.

## Reproducir sin sobrescribir

Desde la raíz `research/rejilla`: ejecutar `node aves-que-aprenden/fuentes.cjs`; imprime una carpeta nueva exclusiva con hash y semilla. Ejecutar `python aves-que-aprenden/estudio.py RUTA_NUEVA fuentes` y después `python aves-que-aprenden/estudio.py RUTA_NUEVA vocoder`. Requiere NumPy, SciPy, Pillow, Matplotlib y FFmpeg. Los comandos rechazan salidas existentes. Los WAV locales se excluyen del repositorio por su regla general; las escuchas AAC y las pruebas gráficas sí se conservan en git.

## Loops

- Loop 1: fuentes de agua, dos silbidos y siringe cruda grave; captura 01 realizada antes del vocoder.
- Loop 2: vocoder de 28 bandas, híbrido de consonantes y aparición gradual; capturas 02 y 03 tras cada resultado. Evaluación técnica completada; escucha de Canek pendiente.
- Escucha de Canek del ensayo inicial: «super hermoso y experimental», con ritmo y acordes; pidió conservar esa dirección y explorar dos poemas.
- Loop 3: partituras completas de La república del pico y A small parliament of wires; adaptación de fonética inglesa de repertorio y fuentes. Commit 69fa4e3.
- Loop 4: interpretaciones completas, vocoder, consonantes, respuestas de canto y ecos; verificación de audio y proceso en la entrega 732b2b5085ae.
