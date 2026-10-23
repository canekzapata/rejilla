# Telar de fase

21 de octubre de 2026. Instrumento para Rejilla, por Canek Zapata. Versión 1.0.0; semilla 20261021. Construido a partir de la [propuesta](../PROPUESTA-GRUPO-METAPLECTICO.md). El [Astrolabio](../astrolabio-metaplectico/README.md) se conserva como otro instrumento; sus archivos no se modificaron.

## Tocar

Abre **[abrir-telar.bat](abrir-telar.bat)** o el **[HTML portátil vigente](telar-portatil-s20261021-48d35d4afd7e/telar-de-fase-s20261021-48d35d4afd7e.html)** en un navegador moderno. El HTML contiene todo el motor y la interfaz: no necesita instalación, servidor ni conexión. La primera nota activa el audio.

- Teclas **A S D F G H J K**, o clic en el teclado: do, re, mi bemol, fa, sol, la, si bemol, do. Dos registros.
- **Cobre, vidrio y boca** son cuerpos sintetizados con siete paquetes de onda; boca distribuye parciales alrededor de dos resonancias y no pronuncia palabras.
- **Girar, inclinar, estirar y dispersar** transforman el cuerpo. Los cambios se aplican a la siguiente nota; no modifican una nota ya en reproducción.
- **Orden** permite comparar inclinar → girar y girar → inclinar. La dilatación va primero y la dispersión al final en ambos casos.
- **Una vuelta · silencio** prepara giro 2π y testigo al 100 %. La señal cancela su referencia. **Dos vueltas · regreso** recupera el signo original. Ambos presets ponen los demás gestos en identidad.
- **Tocar frase** reproduce ocho notas con los controles actuales; **Detener**, o espacio fuera de los controles, detiene las fuentes programadas.
- **Guardar WAV** guarda la nota que muestra la forma de onda, mono PCM16 a 32768 Hz. Cada descarga lleva un nonce nuevo, hash de ejecución y receta JSON dentro del bloque `LIST/INFO/ICMT` del WAV: controles, nota, versión, semilla y SHA-256 del PCM. No normaliza un silencio hasta volverlo audible.

En la vista, cobre es el testigo y turquesa la viajera. Las elipses muestran contornos de los paquetes individuales, no un espectrograma ni la distribución completa de Wigner de su suma. La forma de onda inferior sí corresponde a la salida, incluida la interferencia.

## Escuchar

Entrega exclusiva: **[telar-de-fase-s20261021-b17128d9b652](telar-de-fase-s20261021-b17128d9b652/)**.

| Audio | Qué escuchar |
|---|---|
| [La vuelta deja un hueco · máster](telar-de-fase-s20261021-b17128d9b652/la-vuelta-deja-un-hueco-master-s20261021-b17128d9b652.m4a) | 34 s. Frase original, deformación, alternancia del orden en vidrio, cancelación y regreso de la melodía sobre un grave. Todo se toca con el Telar. |
| [Siete gestos](telar-de-fase-s20261021-b17128d9b652/siete-gestos-s20261021-b17128d9b652.m4a) | 21 s: origen, inclinar, estirar, girar, dispersar y los dos órdenes, en bloques de 3 s. Misma fuente y ganancia. |
| [Una vuelta desaparece, dos regresa](telar-de-fase-s20261021-b17128d9b652/una-vuelta-desaparece-dos-regresa-s20261021-b17128d9b652.m4a) | 12 s. 0–4 s: origen con testigo; 4–8 s: cancelación; 8–12 s: retorno. |

Los WAV de trabajo se conservan localmente, fuera de git por su peso. Los M4A, las recetas, la partitura, las imágenes de magnitud/fase y las verificaciones sí se versionan.

## Motor y matemática

`motor.py` requiere numpy. `motor.mjs` realiza la misma operación en JavaScript sin dependencias. Una fuente es una suma de paquetes

```
ψ(x) = B exp[-π A (x-q)² + 2π i p (x-q/2)],   Re(A)>0.
```

Cada operador transforma **anchura compleja A, amplitud compleja B y centro (q,p)**. No asignamos la ley de los modos de Hermite a los armónicos de un timbre. Son paquetes desplazados, transformados por covariancia de Weyl.

- Chirp `C(c)`: `A → A-ic`, `p → p+cq`.
- Dilatación `D(a)`, `a>0`: `A → A/a²`, `B → B/√a`, `q → aq`, `p → p/a`.
- Giro `R(θ)`, matriz `[[cos θ, sin θ],[-sin θ, cos θ]]`: `A → (A cos θ+i sin θ)/(cos θ+i A sin θ)`, `B → B/√(cos θ+i A sin θ)`; el centro sigue la matriz. Se recorre θ por pasos de hasta π/4, sin reducirlo módulo 2π, para seguir la rama continua de la raíz. Así una vuelta da −ψ y dos dan ψ.
- Dispersión: `R(π/2) C(-b) R(-π/2)`, equivalente al multiplicador de Fourier `exp(-iπ b p²)`.

Convención `Fψ(p)=∫ψ(x)exp(-2πipx)dx`; `R(π/2)=exp(-iπ/4)F`. Se usa la notación Mp(2,ℝ) para la doble cubierta de Sp(2,ℝ) en una pareja de coordenadas.

**Escala y afinación:** `x=(t-centro)/τ`, `τ=0.018 s` y frecuencia relativa `p/τ`. Los paquetes se construyen en banda base compleja y después se aplica una portadora a la frecuencia MIDI. El núcleo metapléctico conserva la norma L² compleja continua. La portadora, tomar parte real, la ventana finita y la mezcla con el testigo son etapas de sonificación externas al grupo. Estirar comprime los intervalos espectrales relativos a la portadora; no transpone toda la nota como una cinta.

El testigo se mezcla como `(viajera+r·original)/(1+r)`. Los dos caminos comparten fuente, fase, alineación y ganancia. No hay compresor ni aleatoriedad nueva por nota en la interfaz. Los cambios de parámetros de una nota a otra son una partitura de estados, no una evolución hamiltoniana continua durante una nota.

Base: [de Gosson y Luef, 2014](https://doi.org/10.1016/j.jmaa.2014.03.013), para metaplécticos y Fourier fraccionaria; [de Gosson, Quantum Blobs](https://link.springer.com/article/10.1007/s10701-012-9636-x), para la acción sobre gaussianas y su doble signo. Los cuerpos, controles y música son decisiones de este instrumento.

## Usarlo en una canción de Rejilla

Desde Python, agrega esta carpeta a tus rutas de importación e importa `motor`:

```python
import numpy as np
from motor import render, coeficientes_rejilla

partitura = {'notas': [
    {'t': 1.0, 'midi': 57, 'vel': .8, 'cuerpo': 'cobre', 'inclinacion': .5},
    {'t': 2.0, 'midi': 60, 'vel': .8, 'giro': np.pi/2},
    {'t': 3.0, 'midi': 64, 'vel': .8, 'giro': 4*np.pi, 'referencia': 1},
]}
audio, recibos = render(partitura, duracion=5, sr=32768)
Z = coeficientes_rejilla(audio)  # canales × columnas de 1 segundo × filas
```

`t` indica el **centro** del gesto. La nota tiene una ventana de 1.5 s, cuyo centro está a 0.6 s: puede anticiparse. Reserva margen al principio y al final si necesitas conservar todas las colas. Los rangos musicales probados de la interfaz son giro 0–4π, inclinación ±0.8, estirar 0.5–2 y dispersión ±0.6; la API matemática admite otros recorridos.

El adaptador calcula la DFT del audio muestreado y conserva coeficientes complejos por columna. Es una entrada temporal a Rejilla; no afirma escribir estos paquetes por la fórmula modal cerrada de otros motores. `producir.py` demuestra la lectura de imágenes reales de 16 bits con `spectrumsynth` y la compara contra el motor.

## Verificación y límites

- Inversa de una cadena de cuatro gestos: error relativo `2.13e-15`.
- Conservación de norma compleja, incluyendo interferencia entre paquetes: error `5.55e-16` en la cuadratura probada.
- Fourier de π/2 contra integración numérica independiente: error `3.95e-16`.
- Una vuelta contra −ψ: `1.54e-15`; dos vueltas contra ψ: `1.86e-15`.
- Cancelación de una vuelta en audio seco: aproximadamente **−279 dB relativos**, piso numérico de esta prueba; no representa un rango audible ni el piso de un convertidor.
- Python frente a JavaScript Float32, cuatro estados: diferencia absoluta máxima **1.45e-8**. No se atribuye a escucha.
- DFT → imágenes de magnitud/fase de 16 bits → FFmpeg: **86.83 dB SNR**, original y chirp incluidos.
- Probado en el navegador local: carga, notas, frase, detener, presets de una/dos vueltas, vidrio, cambio de orden y descarga WAV. Verificación adicional del WAV con lector PCM y receta embebida.
- El HTML portátil tiene sintaxis comprobada y contiene los módulos completos, sin importaciones. La apertura directa `file:` no pudo probarse en el navegador automatizado porque su política permite sólo HTTP/HTTPS; se verificó la interfaz servida localmente. No se cambió esa política.

La ventana finita y su borde de 6 ms pueden recortar colas con gestos extremos. No procesa grabaciones arbitrarias ni implementa MIDI/VST. No hubo escucha humana propia: se entregan muestras para valorar el carácter musical, además de las comprobaciones matemáticas y de señal.

## Proceso, versiones y reproducción

[PNGs y explicación](telar-de-fase-s20261021-b17128d9b652/proceso/README.md) · [GIF del proceso](telar-de-fase-s20261021-b17128d9b652/telar-de-fase-proceso-s20261021-b17128d9b652.gif) · [PNG de resultado](telar-de-fase-s20261021-b17128d9b652/telar-de-fase-s20261021-b17128d9b652.png).

`python pruebas.py` comprueba el núcleo. `python producir.py` crea otra entrega exclusiva; necesita numpy, scipy, matplotlib, Pillow y FFmpeg. `python empaquetar.py` genera otro HTML autónomo con hash y nonce nuevos y comprueba su sintaxis con Node. `producir.py --cerrar CARPETA` agrega el GIF y el manifiesto final; rechaza volver a escribirlos.

La ejecución principal incluye el PNG original, versión, motor y un nonce en SHA-256. La receta registra el hash completo y la semilla; el manifiesto final registra huellas de contenido. Se aplicó el acuerdo de nombres del 13 de octubre de 2026. Los dos primeros empaquetados portátiles (`623736f46a69`, `a1e0e24c3ad6`) se conservan como borradores fallidos: tenían colisión de nombres al reunir módulos. **El vigente es `48d35d4afd7e`**, comprobado después de corregirla. Una comprobación por stdin también encontró la codificación CP1252 de Windows; ahora se envía UTF-8 explícito.

Los metadatos web dejan `https://canekzapata.net/telar-de-fase/` como **URL propuesta con TODO**. `og.png` es de 1200×630 y proviene de señales de la pieza, sin UI. Instrumento local, sin publicación ni push.
