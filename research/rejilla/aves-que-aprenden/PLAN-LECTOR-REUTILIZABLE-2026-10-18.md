# Un lector de pronunciación para Siringua y otras bocas

Fecha: 18 de octubre de 2026. Pedido de Canek: planear la lectura de texto nuevo en inglés porque la pieza la necesita y se reutilizará en otros trabajos. El contrato común y el proveedor eSpeak NG/WASM ya viven en Difonos; queda verificar cobertura y navegador antes de cerrar el primer loop.

## Resultado que buscamos

Una pieza estática recibe un mensaje nuevo en español mexicano o inglés estadounidense, obtiene una representación de su pronunciación y la entrega al instrumento elegido. Siringua conserva su mezcla de agua, siringe y canto; otro consumidor puede producir agua sola o encadenar un banco de difonos. La lectura funciona en el navegador sin un servicio propio que procese el texto. Los archivos del lector se sirven como recursos estáticos.

Se empieza con selección explícita `es-MX` / `en-US`. Los mensajes con idiomas mezclados y otros acentos vendrán después mediante segmentos etiquetados; no se promete adivinación automática del idioma.

## Lo que ya existe y lo que falta

| Componente | Estado real | Trabajo necesario |
|---|---|---|
| G2P de Difonos | Reglas es-MX, versiones JS/Python y vectores compartidos; lector común y proveedor inglés eSpeak NG/WASM | Conservar compatibilidad; declarar cobertura, afinar acento/prosodia y revisar navegador |
| Inglés de los poemas | Léxico cerrado escrito a mano en la partitura original; Difonos ya puede leer texto nuevo con eSpeak | Comparar pronunciaciones y conservar correcciones artísticas sólo donde la escucha lo pida |
| VozAgua | Genera resonancias y consonantes españolas; ya acepta fonemas explícitos y vocales del prototipo inglés | Conectar el proveedor final, escuchar y ampliar articulación inglesa y sus transiciones |
| Adaptación inglesa de Siringua | Inventario experimental, diptongos y consonantes aproximados | Validar contrastes al oído; resolver sonoridad, transiciones y acento |
| Vocoder y composición | Render Node/Python; versos con duraciones y notas explícitas | Consumir la nueva representación; portar el procesamiento al navegador después de resolver lectura y articulación |
| Teia | Se investigó lectura de mensajes, sin integración | Conectar al instrumento cuando el procesamiento de texto nuevo esté probado |

Sabina pertenece al banco muestreado de otras piezas; no es requisito para ampliar el lector ni la fuente del agua–pájaro actual. Un banco español de muestras no adquiere fonemas ingleses por conectar el lector: ese consumidor deberá declarar cobertura o ampliarse por separado.

## Separación de responsabilidades

    texto original + idioma
              ↓
    normalización y proveedor de pronunciación
              ↓
    representación lingüística versionada
              ↓
    compositor: notas, ritmo, repeticiones, aprendizaje aparente
              ↓
    instrumento: Siringua / agua / banco compatible

El lector no fija una melodía. Entrega sonidos, límites de palabra, acentos disponibles y pausas lingüísticas. El compositor puede alargar una vocal, repetir una sílaba o cambiar el registro, dejando registrada la transformación. El instrumento decide cómo produce esos sonidos.

**Una sola fuente de verdad.** La ubicación propuesta del módulo compartido es el proyecto existente `difonos/`, que ya tiene el lector español y sus pruebas. Siringua conserva su propio motor y composición en rejilla. Antes de implementar, leer el README y LOOP_STATE de Difonos y añadir la nueva interfaz sin alterar consumidores antiguos. Distribuir copias versionadas con manifiesto/hash o un paquete local pequeño; no mantener otro G2P editado a mano dentro de cada obra. Las entregas antiguas conservan sus fuentes selladas.

## Contrato del lector, versión 1

Propuesta de API conceptual: `leer(texto, { idioma, perfil, correcciones })`. Una inicialización asíncrona carga datos/proveedor antes de usarla. El mismo contrato sirve en Node y navegador.

La respuesta incluye:

- texto original intacto, idioma y versión del proveedor/diccionarios;
- palabras con rangos en el original y pronunciación elegida;
- fonemas con identificadores inequívocos por inventario, equivalencia IPA cuando exista y sonoridad pertinente; no sobrecargar letras internas como `R`, que hoy significa rr española;
- acento primario/secundario y límites silábicos **cuando puedan obtenerse o derivarse**; si se derivan, señalar método; si faltan, no inventarlos;
- pausas por puntuación y una política declarada para saltos de línea/espacios;
- estados por palabra: pronunciación obtenida por reglas, diccionario, corrección explícita o falta de resolución;
- registro de normalizaciones y sustituciones. El compositor añade después tiempos y alturas.

No llamar “confianza” a un número sin un modelo que la estime. Un motor por reglas puede pronunciar una palabra desconocida sin tener evidencia de que acertó. Los homógrafos dependientes de contexto tampoco se dan por resueltos universalmente.

## Proveedor inglés: primera decisión técnica a probar

**Proveedor elegido: eSpeak NG como lector fonético**, sin usar su audio para sustituir la voz de Siringua. Difonos compila el enlace fonético mínimo como WASM; la extracción se convierte a ARPABET e incluye transcripción IPA y marcas de acento. La salida Node de «The new birds read messages.» ya conserva palabras, rangos y vocales. Aún falta repetir un conjunto amplio y abrir la versión navegador. La llamada actual es por palabra, por lo que homógrafos de contexto pueden requerir corrección.

Registrar versión/commit, tamaño real, latencia, archivos distribuidos y condiciones de licencia del componente. eSpeak NG declara GPLv3 o posterior: el empaquetado debe conservar licencias y fuentes correspondientes. Es una tarea de integración, no una razón para reemplazar de entrada la arquitectura.

**CMUdict: referencia de contraste**, no solución completa: aporta pronunciaciones y acentos de palabras de inglés estadounidense, pero una lista no resuelve por sí sola palabras ausentes ni contexto. No iniciar con una combinación de dos diccionarios y varios motores si eSpeak cubre el caso. Usar un único proveedor más correcciones explícitas.

Si el candidato no satisface navegador/tamaño/lectura, documentar el fallo y comparar otro G2P local detrás del mismo contrato. No resolver silenciosamente con TTS remoto o las voces variables del sistema operativo.

## Texto experimental y casos difíciles

- Conservar acentos y diéresis españoles antes de normalizar para pronunciación: el lector actual los elimina y eso pierde información prosódica.
- Una llamada como `pi`, un alargamiento `trrr` y una palabra inventada son material de la obra. Ofrecer correcciones fonéticas o una anotación de llamada; no corregir su escritura automáticamente.
- Eye / I / aye deben poder compartir fonemas manteniendo distintas palabras y funciones compositivas.
- Mantener saltos y blancos del poema en el texto; el compositor elige sus pausas. No reducir irreversiblemente toda la página a una cadena de palabras.
- Cifras, abreviaturas, URLs, emoji y nombres requieren una política explícita. Primer alcance: texto alfabético y puntuación; otros tokens se conservan con una marca y pueden omitirse/nombrarse por configuración. No desaparecer sin registro.
- Mensaje de Teia = datos. No interpretar texto público como código, rutas, órdenes del sistema o instrucciones del agente.

## Loops y entregables

### Loop 5 · Probar la lectura fuera de los poemas

Preparar 40 frases nuevas: 20 por idioma, separadas en desarrollo y comprobación final antes de ajustar reglas. Incluir palabras fuera del léxico actual, acentos, pares de vocales, consonantes, homógrafos y llamadas inventadas. Integrar el proveedor candidato primero en una prueba local y exportar JSON del lector. Repetir un subconjunto en navegador antes de seguir afinando el audio.

**Avance 18 de octubre:** Difonos tiene `runtime/lector.js`, contrato compartido, proveedor eSpeak NG 1.53.0/WASM, correcciones por palabra y alternativa `--engine rules`. Se fijó el commit fuente `ba90c8e9f440ad544f674a790bb5f53878b6ffc5`; el paquete JS/WASM/datos pesa 1,255,943 bytes y conserva las licencias GPL relacionadas. La llamada Node para «The new birds read messages.» devolvió cinco transcripciones IPA/ARPABET con rangos; *read* quedó marcado como lectura por defecto ambigua. El adaptador de Siringua ya consume el inventario ARPABET y transforma diptongos. No se ejecutó Worker, conjunto de 40 frases ni audio inglés nuevo. Se intentó navegador con una página servida localmente, pero el sandbox denegó abrir el puerto local; la carga web queda pendiente. El SDK Emscripten que Canek clonó está en `difonos/emsdk`; el código eSpeak se obtuvo y compiló en `difonos/vendor/espeak-ng`.

**Cierre:** todo el texto se conserva, ningún fonema falta por un fallo silencioso, cada sustitución queda registrada y un mensaje nuevo inglés no exige editar una tabla de palabras. Para homógrafos o invenciones puede seguir siendo necesaria una corrección explícita; registrarla. Se documenta qué marcas ofrece realmente el proveedor.

La integración de eSpeak está hecha, pero este loop no se cierra hasta procesar las 40 frases acordadas, comprobar el navegador y conservar los resultados. La página puede servir archivos estáticos: no hay un servidor propio que procese texto.

### Loop 6 · Agua que articula texto nuevo

Crear el adaptador de fonemas a gestos de agua. Resolver diptongos como transiciones con duración controlada, consonantes sonoras/sordas y acentos. Conservar el modo español anterior como referencia. Producir frases cortas de agua sola antes de añadir pájaro.

**Cierre:** comparación de escucha con palabras esperadas ocultas en la primera pasada; anotar qué se entendió y qué falló. Diferenciar acierto del G2P de claridad del sintetizador. Las métricas de espectro no sustituyen esa escucha. Guardar referencias, parámetros y resultados reales.

### Loop 7 · Siringua conserva su carácter

Conectar ambos idiomas al mismo compositor y motor. Añadir un control de articulación que gobierne registro, presencia de formantes y consonantes, manteniendo motivos y respuestas del otro lado. Ofrecer modo fiel al texto y modo de transformación poética; ambos guardan el texto original y lo que se hizo con él. Repetir los poemas actuales como referencias artísticas y cantar mensajes nunca partituriados.

**Cierre:** audio comparado con los ensayos que Canek valoró, más escucha de texto nuevo; decisión auditiva sobre claridad/caracter y sin presentar la mezcla como aprendizaje automático. No hace falta que todas las palabras sean transparentes en el modo poético.

### Loop 8 · Navegador y reutilización

Empaquetar lector y datos locales versionados; procesamiento por frases en Worker con cancelación y límites de cola. Adaptar síntesis/vocoder al navegador. Comprobar arranque por gesto, parada, cambio de texto, liberación de memoria y caché por texto exacto + idioma + proveedor/datos + compositor/instrumento + parámetros + semilla. Medir carga y generación en una computadora y un teléfono disponibles; registrar modelos reales, no prometer rendimiento sin medir.

**Cierre:** una página estática procesa una frase nueva sin invocar un backend lingüístico; sirve como demostración mínima para dos consumidores, Siringua y agua sola. Verificar que tras cargar los recursos puede generarse texto nuevo sin red en esa sesión. Persistencia tras recargar requiere caché de recursos explícita y prueba aparte. Los mensajes de Teia y la descarga inicial de la página sí necesitan su infraestructura habitual.

### Loop 9 · Mensajes de la pieza

Conectar la lectura del canal a una cola de cantos. Identificador estable por mensaje/edición, orden, duplicados, recuperación tras fallo y política de qué mensajes entran. Poner un límite inicial de 300 caracteres por canto; conservar el mensaje entero y dividirlo si excede ese límite. No sintetizar un historial entero a la vez.

**Cierre:** mensaje nuevo en cada idioma produce canto; abrir de nuevo reconstruye la misma partitura con versiones/semillas fijadas. El PCM entre navegadores no se promete idéntico bit a bit. Guardar snapshot del texto y metadatos usados: un mensaje editado no debe cambiar retroactivamente una entrega archivada.

**Avance 18 de octubre:** el canal abierto 10 se comprobó en lectura: evento `message_posted` → registro 168 del big map → JSON público en IPFS. Las 18 palabras del fragmento inglés pasaron por eSpeak NG/WASM; Siringua produjo voz de agua y 18 respuestas de pájaro. Entrega [s181026-28b2327e61b3](siringua-mensaje-abierto-s181026-28b2327e61b3/README.md), con AAC, fonemas, cuatro capturas, GIF y receta con hashes. Esto prueba por separado el transporte público y la ruta sonora, pero el render aún consume el texto archivado y no consulta Teia en vivo. El avance siguiente implementa ese lector y su cola.

**Avance 18 de octubre · lector y compositor:** `teia-canal.js` consulta el big map del canal y eventos TzKT, recupera el JSON de mensaje con gateways IPFS alternativos, ignora canales/mensajes ocultos y borrados, y empieza desde el evento más reciente. La cola identifica cada segmento por canal/mensaje/versión, limita cada canto a 300 caracteres y permite retirar lo pendiente si llega una edición o borrado. `siringua-mensajes.js` entrega esos elementos al mismo lector común y a los motores de agua/ave; español e inglés requieren elección explícita. Cinco pruebas con respuestas simuladas cubren el contrato, ocultamiento, borrado, fallback IPFS, segmentación y síntesis fonética/procedural. La red del entorno no resolvió `api.tzkt.io`, así que aún no se confirmó el adaptador contra el servicio en vivo ni en un navegador.

## Verificación y archivo

Pruebas significativas: cobertura declarada, conservación del original, acentos, rango de segmentos, resultado equivalente del lector en Node/navegador para el mismo proveedor, ausencia de audio no finito o saturado, cancelación y límites de memoria/cola. Mantener los vectores españoles existentes; no duplicar el motor inglés en Python para crear otra fuente de discrepancias.

Cada avance sonoro entrega AAC, receta, texto/partitura y fuentes versionadas; PNGs de etapas reales, GIF de proceso ≤10 s/≤15 MB, revisión visual y commit por loop. Si una sesión sólo produce un informe/JSON, no fabricar capturas sonoras o visuales de algo que no sucedió. Nombres nuevos con hash/semilla y destinos exclusivos. Sin publicar ni conectar carteras como parte de las pruebas del lector.

## Primer trabajo concreto

**Paquete de ensayo preparado:** [Siringua prueba de canal Teia](siringua-prueba-teia-d5b2b63514a7/README.md) enlaza la cola real con el compositor PCM en una edición HTML autosuficiente y ofrece una frase local de prueba. Cinco pruebas simuladas pasan y el paquete se cargó en un contexto global de navegador simulado para verificar español y PCM finito. **Siguiente paso: probar la previsualización del ZIP en Teia**, acuñar una copia si la previsualización funciona, abrir un canal `unrestricted`, iniciar la escucha antes de mandar el mensaje y verificar TzKT/IPFS, CORS/CSP, latencia y audio. La integración desde iframe sigue sin prueba en vivo. También faltan las 40 frases de cobertura y escuchar mensajes nuevos en ambos idiomas antes de publicar la obra visual.

## Fuentes consultadas

- [eSpeak NG: proyecto y licencia](https://github.com/espeak-ng/espeak-ng).
- [API de conversión en speech.c](https://github.com/espeak-ng/espeak-ng/blob/master/src/libespeak-ng/speech.c).
- [Reglas y diccionarios de pronunciación](https://github.com/espeak-ng/espeak-ng/blob/master/docs/dictionary.md).
- [Port Emscripten documentado](https://github.com/espeak-ng/espeak-ng/tree/master/emscripten). Su documentación indica versión 1.49.1, 2017; no se toma su tamaño histórico como medida actual.
- [CMUdict, referencia de pronunciaciones](https://github.com/cmusphinx/cmudict).
- Contexto local: `difonos/PLAN.md`, `difonos/runtime/g2p.js`, pruebas de Difonos y los ensayos de Siringua en esta carpeta.
