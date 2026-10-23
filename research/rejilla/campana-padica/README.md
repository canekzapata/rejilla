# Campana de distancias imposibles

21 de octubre de 2026. Instrumento para Rejilla, Canek Zapata. Versión 1.0.0. Realización de la [propuesta de campana p-ádica](../PROPUESTA-CAMPANA-PADICA-2026-10-21.md).

Golpea cualquiera de las 64 regiones y cambia su vecindad mientras sigue vibrando. Un resonador completo conserva desplazamientos y velocidades cuando cambia el acoplamiento. Afinar el cuerpo con otra tecla también transforma la resonancia que ya estaba dentro.

## Tocar

**[Abrir la campana](abrir-campana.bat)** · **[HTML portátil vigente](campana-portatil-s20261021-9b96e17a6f4f/campana-padica-s20261021-9b96e17a6f4f.html)**. El HTML incluye interfaz y procesador de audio, sin dependencias externas; se puede abrir en un navegador moderno. La interfaz servida localmente se probó en el navegador de Codex. La apertura directa de archivos no se volvió a intentar: la política de ese navegador permite HTTP/HTTPS, como se documentó al construir el Telar.

- Clic en una región: golpe en esa zona. Los números 0–63 son etiquetas del cuerpo, no frecuencias.
- **A S D F G H J K**: la, do, re, mi, sol, la, do, mi, en registros entre La 2 y Mi 4. Cada tecla afina **todo el mismo cuerpo**, con transición de 45 ms; no dispara ocho campanas independientes.
- **Plegar**: de una cuadrícula de vecinos a familias aritméticas. A mitad del recorrido hay una mezcla de acoplamientos, no una métrica p-ádica exacta.
- **Profundidad**: peso relativo de las escalas de parentesco. **Tensión**: rigidez que separa los modos. **Apagado**: amortiguación. Estos tres controles y el plegado actúan sobre la vibración en curso.
- **Familia que se escucha**: modifica una captación estéreo fija y asimétrica. Es una apertura hacia las regiones con el mismo residuo módulo 8, con una captación débil del resto.
- **Fuerza del golpe** se aplica a los golpes siguientes.
- **Escuchar el pliegue**: un solo golpe y una secuencia de 8 s: cerca, parentesco, profundidad y regreso. Un gesto manual cancela los cambios programados restantes.
- **Apagar**, o espacio fuera de los controles, vacía el movimiento. Reiniciar restablece también los controles.
- **Grabar toma**: captura la salida interna estéreo, sin micrófono, hasta 25 s. Vuelve a pulsar para guardar antes. WAV PCM16 a la frecuencia de muestreo del navegador, con receta JSON embebida en `LIST/INFO/ICMT`: estado inicial completo, objetivos, eventos con sus cuadros, versión y huellas. Cada exportación tiene nonce e identificador SHA-256 nuevos; incorpora una imagen del cuerpo a la identidad y registra su huella.

Cobre y violeta indican el signo del desplazamiento real de cada zona. La curva inferior muestra los 64 desplazamientos, no un espectrograma. Las líneas muestran las doce conexiones más fuertes desde la zona elegida. El borde verde identifica la familia de captación.

## Escuchar las muestras

Entrega vigente: [campana-distancias-s20261021-9b5d27254a47](campana-distancias-s20261021-9b5d27254a47/).

| Audio | Qué contiene |
|---|---|
| [La campana aprende otra distancia · máster](campana-distancias-s20261021-9b5d27254a47/la-campana-aprende-otra-distancia-master-s20261021-9b5d27254a47.m4a) | 34 s. Un solo cuerpo: golpes, familias, pliegue sostenido, cambio de afinación y frase de regreso. Máster a −18.08 LUFS y −4.15 dBTP. |
| [Un golpe cambia de mundo](campana-distancias-s20261021-9b5d27254a47/un-golpe-cambia-de-mundo-s20261021-9b5d27254a47.m4a) | 10 s. Un golpe a 0.12 s; cambia el pliegue a 1.4 s, la profundidad a 3.7 s y regresa a 5.8 s. |
| [El mismo golpe sin plegar](campana-distancias-s20261021-9b5d27254a47/referencia-un-golpe-sin-plegar-s20261021-9b5d27254a47.m4a) | Referencia con el mismo golpe y parámetros iniciales, manteniendo la geometría fija. |
| [Tres zonas, un parentesco](campana-distancias-s20261021-9b5d27254a47/tres-zonas-un-parentesco-s20261021-9b5d27254a47.m4a) | 10 s. Zonas 1, 2 y 9 con la misma fuerza, cuerpo y captación; se apaga entre golpes para comparar. |

Los WAV de trabajo se conservan localmente y se ignoran en git. M4A, partituras, estados, recetas, PNGs y GIF se versionan. Las comparaciones secas mantienen la ganancia original; sólo la muestra titulada máster tiene normalización para escucharla.

## Motor

`motor.mjs` realiza toda la física del instrumento en JavaScript, con arreglos Float64. Lo usan el renderizador de Node y el AudioWorklet del navegador. `campana.py` permite llamarlo desde Rejilla/Python sin duplicar ecuaciones; necesita numpy y Node.

Para regiones distintas, la distancia es `d₂(i,j)=2^(-v₂(i-j))`. En particular `d₂(1,2)=1`, `d₂(1,3)=1/2` y `d₂(1,9)=1/8`. Para cada escala k, el peso de conexión es proporcional a `2^((1+α)k)`, normalizado de modo que la suma de pesos desde cada región sea 1. El kernel calcula las mismas sumas que la matriz densa mediante familias de residuos.

La vecindad ordinaria es una cuadrícula 8×8 con bordes abiertos y peso 1/4 por arista. No es un anillo: un anillo y esta matriz p-ádica serían ambos circulantes y compartirían una base de Fourier. La cuadrícula abierta permite que cambien también las relaciones entre los modos; el conmutador de las matrices tiene norma 0.7784 en la prueba.

```
L(s) = (1-s) L_cuadrícula + s L_2
u'' + 2γ u' + ω₀² (I + κ L(s)) u = F(t)
```

Los dos Laplacianos son simétricos y positivos semidefinidos. El término `I` da una frecuencia central `ω₀=2π·Hz(MIDI)`. Un golpe incrementa la velocidad en la región elegida. No añade un oscilador independiente, eco o grabación.

Se integra con velocity Verlet y amortiguación simétrica; controles suavizados durante unos 45 ms, actualizados cada 64 muestras. El paso numérico introduce un error de energía pequeño y medido; no se afirma conservación exacta a paso finito. Con parámetros fijos y sin amortiguación, la ecuación continua conserva la energía cuadrática de un modelo con masas unitarias abstractas, no una medición de julios acústicos. Cambiar el acoplamiento o la afinación realiza trabajo, que se contabiliza. El cuerpo conserva u y v; su energía puede cambiar porque la rigidez cambió.

Captación lineal estéreo con protección de salida a ±0.98. Esa protección no modifica el estado del cuerpo; **no se activó en ninguna muestra entregada ni en los extremos probados**. La afinación central se mantiene como parámetro musical; los demás modos pueden ser inarmónicos.

Es un modelo jerárquico finito inspirado en análisis p-ádico. No implementa todo ℚ₂ ni pretende ser una discretización validada del operador de Vladimirov. [Kozyrev: análisis espectral p-ádico](https://arxiv.org/abs/math-ph/0012019) · [Operadores y wavelets p-ádicas](https://arxiv.org/abs/math-ph/0303045).

## Usarlo desde Rejilla

Agrega esta carpeta a las rutas de importación de tu pieza y usa:

```python
from campana import render, coeficientes_rejilla

partitura = {
    'initial': {'fold': 0, 'depth': .7, 'tension': 7,
                'damping': .2, 'midi': 48, 'pickup': 1},
    'events': [
        {'t': .12, 'hit': 9, 'vel': .8},
        {'t': 1.4, 'params': {'fold': 1}},
        {'t': 3.7, 'params': {'depth': 1.8}},
        {'t': 5.8, 'params': {'fold': 0}},
    ]
}
audio, recibo = render(partitura, duracion=10, sr=24000)
Z = coeficientes_rejilla(audio, sr=24000)
```

`audio` es estéreo; `Z` tiene canales × columnas de 1 s × filas, **incluidos DC y Nyquist**. La inversa rFFT recupera la señal. Es DFT de un motor temporal, no escritura modal cerrada. Una salida a `spectrumsynth` tiene que tratar explícitamente las filas extremas: aquí no se afirma haber hecho esa conversión.

También se puede renderizar con `node renderizar.mjs partitura.json prefijo-nuevo`; produce Float32 estéreo entrelazado `.raw` y un recibo `.json`. Rechaza destinos existentes. El motor es determinista; `20261021` identifica esta edición y sus entregas, sin ruido aleatorio en la física.

## Verificación

- Kernel jerárquico frente a matriz densa: error máximo `1.73e-17`; simetría, filas de suma cero y espectro no negativo dentro del redondeo.
- Energía con controles fijos y γ=0: deriva máxima **0.027 %** en la prueba de 0.5 s a 48 kHz, La 2. No se extiende esta cifra a cualquier frecuencia y paso.
- Plegar inmediatamente: desplazamientos y velocidades permanecen **idénticos**, diferencia 0. El cambio de energía coincide con el trabajo de cambiar la rigidez.
- Amortiguación: razón energética 0.301239 frente a 0.301194 esperada a 0.5 s con γ=1.2.
- Solución numérica frente a referencia independiente por diagonalización de la matriz: error relativo `3.06e-4` en desplazamiento, en la prueba a 96 kHz.
- Posiciones distintas y extremos de controles: señal finita, diferencias medibles y protección de salida sin activarse.
- Misma excitación con y sin plegado: señal idéntica antes de 1.4 s. Tras el gesto, el residuo después de ajustar la mejor ganancia escalar es **0.8414**; el cambio no se explica sólo por volumen. No prueba por sí mismo una percepción musical.
- Procesador AudioWorklet realmente empaquetado frente a render offline, a 48 kHz: **diferencia 0**, incluida una modificación durante la grabación. WAV estéreo y receta embebida comprobados con lector independiente.
- Ida y vuelta por DFT completa en Float64: error relativo `5.12e-16`.
- Navegador: carga, golpes, estados vibrantes, controles y grabación interna; guardado automático de una toma de 25 s observado. No se detectaron errores en la consola revisada. La versión portátil tiene sintaxis comprobada e incluye el procesador completo en un Blob local.

No hubo escucha humana propia. Se entregan las muestras para evaluar el timbre, el fraseo y la diferencia perceptiva del pliegue. La animación usa desplazamientos del motor, no niveles simulados a partir del control de volumen.

## Proceso y conservación

[PNGs y explicación](campana-distancias-s20261021-9b5d27254a47/proceso/README.md) · [GIF del proceso](campana-distancias-s20261021-9b5d27254a47/campana-padica-proceso-s20261021-9b5d27254a47.gif) · [PNG de resultado](campana-distancias-s20261021-9b5d27254a47/campana-distancias-s20261021-9b5d27254a47.png).

`python producir.py` calcula y conserva etapas reales: distancias, matrices, audio y espectrogramas; crea carpeta exclusiva y guarda inmediatamente la identidad SHA-256 completa. Necesita numpy, scipy, matplotlib, Pillow, Node y FFmpeg. `python producir.py --cerrar CARPETA` reúne los PNGs de etapas y capturas en un GIF y rechaza sobrescribirlo. `python empaquetar.py` genera otra versión portátil exclusiva y verifica su sintaxis con Node.

Las entregas siguen el acuerdo del 13 de octubre: nombre descriptivo, identificador de al menos 12 caracteres, nonce nuevo, identidad por imagen + versión + motor, semilla documental y huellas de contenido en receta. Las etapas no se reconstruyeron retrospectivamente.

Se conserva `74a0d08a3d72` como borrador interrumpido: su DFT Float32 excedió el umbral de precisión doble; se corrigió el adaptador a Float64. Esa primera corrida se detuvo antes de escribir nonce y hash completo: no se inventaron; ahora se guardan al crear la carpeta. El portátil `195559563c23` es una captura de construcción anterior a generar el OG; el vigente es `9b96e17a6f4f`. Los archivos anteriores conservan sus nombres.

`og.png` mide 1200×630 y proviene de las conexiones del cuerpo, sin UI. Metadatos con URL propuesta y TODO: `https://canekzapata.net/campana-padica/`. Instrumento local, sin publicación ni push.
