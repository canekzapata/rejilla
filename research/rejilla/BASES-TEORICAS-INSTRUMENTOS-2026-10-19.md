# De qué teoría salen estos instrumentos

19 de octubre de 2026. Respuesta a Canek sobre las [seis propuestas](INSTRUMENTOS-POR-INVENTAR-2026-10-19.md), especialmente **Boca de tres tiempos**, y su convivencia con electrónica de carácter ochentero/noventero y de ciencia ficción.

Distinguimos tres niveles: una técnica conocida de síntesis, una regla instrumental que proponemos y una expectativa musical que sólo podremos evaluar al escuchar el prototipo. Las fuentes sostienen las técnicas; no presentan estos seis diseños ni garantizan su resultado.

**Actualización, 20 de octubre:** Canek autorizó construirlos. [Doce prototipos, audio y revisión de comportamiento](instrumentos-de-tres-tiempos/README.md). Se conserva aquí la explicación del diseño inicial; las pruebas técnicas no sustituyen la valoración musical y las fichas delimitan la primera implementación.

## Boca de tres tiempos: fuente, articulación y contrapunto

La base acústica es el **modelo fuente–filtro**. En su aproximación a la voz sonora, una excitación periódica representa la fuente glótica y un filtro representa resonancias del tracto vocal, llamadas formantes. Esto permite controlar por separado aspectos de la excitación y de la resonancia. Es una aproximación, no una reproducción completa de la anatomía. Fuente: Julius O. Smith, [Formant Synthesis Models](https://dsprelated.com/freebooks/pasp/Formant_Synthesis_Models.html).

Nuestra extensión sería escribir tres recorridos temporales:

| Recorrido | Qué controlaría | Ejemplo de gesto propuesto |
| --- | --- | --- |
| Articulación | Entradas de consonantes, cierres, fricción y aire; no todas las consonantes se modelan igual. | Tres interrupciones pequeñas en una vocal larga. |
| Vocales | Movimiento de las resonancias entre configuraciones como «a», «u» e «i». | La boca tarda seis segundos en cerrarse hacia «u». |
| Melodía | Altura fundamental, duraciones y ataques de las notas cantadas. | Dos notas largas y una respuesta de tres notas breves. |

«Tres tiempos» no significa tres voces superpuestas. Sería una salida vocal cuyos procesos no empiezan y terminan siempre juntos. Tampoco significa bajar la frecuencia de vibración al tempo: la frecuencia fundamental determina la altura; el ritmo de las notas se escribe en otra escala temporal.

**Escena imaginada, todavía sin audio:** una «a» sostenida canta una nota larga; dentro aparecen tres ataques «t–k–s». Mientras la melodía responde con tres notas, la vocal sigue su viaje lento hacia «u». Al final consonante, vocal y nota coinciden en un «mi» breve. La sensación buscada es que una boca se desdobla y vuelve a enfocarse.

Musicalmente proponemos un **contrapunto entre parámetros**: vocal, articulación y melodía adquieren trayectorias relacionadas pero distintas. Es una estrategia de composición nuestra, no una nueva ley acústica. Podemos escribirla explícitamente, sin aprendizaje automático. Primero probaríamos vocales, fricción y cierres; cantar texto inteligible requeriría trabajo adicional de articulación y transiciones.

La decisión expresiva central sería cuándo separar esos procesos y cuándo reunirlos. Si siempre están desfasados, el instrumento también puede volverse monótono. El retorno a una sílaba clara tiene que estar compuesto.

## Cuerda de cuerpos incompatibles: modos y acoplamiento

Un modelo modal representa vibraciones mediante resonancias con frecuencia, amplitud y amortiguación. El acoplamiento hace que las partes se afecten: Smith describe cambios de envolvente e intercambio de señal entre componentes y cuerdas modeladas. Sumar sonidos desafinados no equivale por sí solo a simular ese intercambio. Fuente: [String Coupling Effects](https://www.dsprelated.com/freebooks/pasp/String_Coupling_Effects.html).

Nuestra hipótesis sería agrupar resonancias con comportamientos de cuerda, arco y placa bajo un gesto común. La identidad de «un cuerpo» sería una ficción instrumental que habría que conseguir con continuidad de ataque y respuesta. No afirmamos que exista una cuerda natural con esa constitución ni que el resultado vaya a ser más convincente que una buena instrumentación por capas.

## Piano de tres presentes: separar componentes y programar su tiempo

La síntesis espectral puede tratar por separado componentes sinusoidales, ruido y transitorios, transformando sus tiempos de formas distintas. Fuente: Smith, [Spectral Modeling Synthesis](https://dsprelated.com/freebooks/sasp/Spectral_Modeling_Synthesis.html).

Nuestra regla asignaría el ataque al próximo evento escrito, el cuerpo al actual y la caída al anterior. No es exactamente la descomposición de esa fuente: tomaríamos el principio de separar componentes para construir una partición propia por fases de nota. Se necesitarían transiciones sin cortes audibles.

La «anticipación» usa una partitura conocida. En vivo requeriría recibir las notas por adelantado o retrasar la salida; la ficción temporal no elimina esa condición causal. Su interés musical sería dejar oír el destino antes de que la melodía llegue.

## Arpa que presta su vibración: una red con intercambio

Comparte con la cuerda el principio de resonadores acoplados de [String Coupling Effects](https://www.dsprelated.com/freebooks/pasp/String_Coupling_Effects.html). Nuestra extensión convertiría los enlaces en controles de interpretación: qué cuerda cede, cuál recibe y cuánto se pierde.

El prototipo tendría que declarar cómo representa la energía y comprobar sus intercambios. Cambiar afinaciones o conexiones puede introducir trabajo: no bastaría con limitar la salida y afirmar conservación física. Podemos empezar por un modelo abstracto acotado y llamarlo así.

La propuesta musical es un relevo: el acompañamiento recibe fuerza del solista. Una red pasiva tampoco transfiere libremente energía entre cualesquiera alturas; si queremos esa libertad, habrá que diseñar una conversión activa y declarar su excitación adicional.

## Órgano de divisores con memoria: frecuencias y estado

La primera base es una definición matemática explícita: frecuencias `f/n` para enteros positivos `n`, frente a múltiplos `n·f`. Desde 440 Hz, los divisores 2, 3 y 5 dan 220, aproximadamente 146.67 y 88 Hz. Esos números no garantizan una armonía bella ni que se oiga 440 Hz como centro.

La segunda base sería una regla de **histéresis** programada: un componente se activa al superar un umbral y se desactiva al bajar de otro menor. Entre ambos conserva su estado. Ejemplo propuesto: entrada a presión 0.65, salida a 0.40. A presión 0.50 habría estados distintos según el recorrido previo.

No se atribuye esa regla a un órgano acústico real. El gesto musical sería decidir cuándo un acorde se engancha, persiste o se libera. No se ha demostrado todavía que esa memoria resulte perceptible en nuestro diseño.

## Sala plegada: redes de retardos y realimentación

Las redes de retardos con realimentación conectan caminos temporales mediante una matriz. Son una base establecida para reverberación artificial; Rocchesso y Smith estudian estructuras y condiciones sin pérdidas. Fuente primaria: [Circulant and Elliptic Feedback Delay Networks for Artificial Reverberation](https://www.di.univr.it/documenti/ArticoloRivista/allegato/allegato574545.pdf), 1997.

Nuestra extensión sería tocar sus conexiones y distribuir rutas distintas por registro. Una estructura estable con parámetros fijos no garantiza estabilidad al cambiarlos: hay que verificar las transiciones. La sala «imposible» es la imagen que guía esa arquitectura, no una afirmación sobre un recinto físico.

## Electrónica de ciencia ficción

La síntesis FM ofrece control de espectros móviles mediante relaciones de frecuencia y cantidad de modulación. Fuente: Chowning, [The Synthesis of Complex Audio Spectra by Means of Frequency Modulation](https://aes2.org/publications/elibrary-page/?id=1954), 1973. Se consultó su ficha y resumen públicos, no el artículo completo de pago.

Podría dar un cristal eléctrico para el Piano de tres presentes. Smith describe también síntesis vocal mediante FM en [FM Voice](https://www.dsprelated.com/freebooks/sasp/FM_Voice.html): sería una alternativa de motor para la boca, sin sustituir la escritura de su articulación.

«Ochentero», «noventero» y «sci-fi» describen aquí una dirección estética solicitada por Canek, no una reconstrucción histórica. Las propuestas de cristal, cuerdas sintéticas, bajo parlante y percusión láser se añaden al [documento de instrumentos](INSTRUMENTOS-POR-INVENTAR-2026-10-19.md). El fraseo, las relaciones entre capas y la forma siguen siendo decisiones de composición.
