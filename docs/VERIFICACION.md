# Verificación del taller restaurado

23 de octubre de 2026. Actualiza el alcance de la primera edición mínima.

- Censo actual: 1494 archivos de código, 652 contenidos distintos. Censo editorial
  anterior: 877 filas de código. Todas las copias cotejadas por SHA-256.
- 38/38 pedidos de motores propios y 12/12 prototipos producidos con señal finita
  no muda. Cada productor escribió WAV, receta, PNGs y GIF. Resumen en
  `PRUEBAS-MOTORES.json`; los audios de prueba están ignorados.
- 152/152 fichas Web Audio/Meleeviewer produjeron señal finita no muda. Dos
  escenarios necesitaban sus partituras; se recuperaron y adaptaron las rutas.
  Las cuatro baterías requieren indicar la pieza (kick por defecto en el taller).
- 28/28 objetos/gargantas: prueba original de señal y determinismo aprobada.
- 65/65 fichas Python/modal/gemelo produjeron WAV finito no mudo. Junto con
  navegador y objetos se cubrieron las **231 fichas distintas**; hay motores
  con más de una vía. Detalle en `PRUEBAS-FICHAS.json`.
- Banco de Sabina presente: voz del jardín y ocho capas de voz del Agua calculadas.
- Cadena completa del Agua comprobada con una partitura técnica de 40 segundos:
  guitarra, Python, ocho voces, baterías del navegador, 23 capas activas, mezcla,
  WAV, M4A, receta, tres PNGs y GIF. Medidas en `PRUEBA-AGUA.json`.
  No se volvió a renderizar la obra completa de 281.286 segundos.
- La prueba corta detectó longitudes incompatibles en tres curvas interpoladas
  de crecida/viento. Se hizo coincidir el número de muestras aleatorias con sus
  nodos de interpolación. Las versiones originales permanecen archivadas.
  La automatización de mezcla usa convolución por bloques para evitar el costo
  cuadrático de una ventana larga; conserva el mismo filtro rectangular.
- Laboratorio: secuenciador, diseño modal, catálogo y exportación ZIP comprobados.
  ZIP íntegro con siete archivos, GIF válido de 3.6 s y huellas de sus contenidos.
- GIF del uso del laboratorio: 5.7 s, 176025 bytes; GIF de la prueba del Agua:
  5.7 s, 78488 bytes. PNGs y GIF revisados visualmente.

La primera prueba de descarga de dependencias falló por DNS del entorno aislado;
la instalación autorizada de npm terminó sin vulnerabilidades reportadas.
La comprobación del navegador requirió iniciar navegador y servidor fuera de ese
mismo aislamiento. No fue un error del taller. Las capturas de intentos previos
se conservan en `renders/capturas-intentos/`, sin duplicarlas en Git.

No se afirma haber escuchado críticamente cada resultado, reproducido cualquier
canción histórica ni ejecutado todas las aplicaciones visuales y paquetes externos.
La licencia propia sigue pendiente de elección. No se ha publicado esta actualización.
