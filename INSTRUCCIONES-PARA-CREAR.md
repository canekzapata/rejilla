# Instrucciones para crear música e instrumentos con Rejilla

Autor de los proyectos: Canek Zapata. Esta guía viaja con el programa y aplica también si trabajas con un asistente.

## Antes de producir

1. Escribir intención musical y gesto de interpretación. Identificar el motor real que se usará: Web Audio, temporal Python o Rejilla/spectrumsynth.
2. Para un instrumento inventado, distinguir técnica conocida, decisiones originales e hipótesis perceptiva. Justificar cada relación entre controles y resultado. Citar fuentes primarias o documentación del autor cuando existan; declarar fuentes no consultadas por completo.
3. Fijar código, dependencias, partitura, parámetros y semilla. No presentar una analogía física como simulación medida.

## Entregables obligatorios

- Audio final y muestra aislada del instrumento o motivo.
- Partitura editable y receta con parámetros, semilla y huellas SHA-256.
- PNG final y PNGs numerados de etapas reales, con pies que expliquen qué se transformó.
- Gráficas que expliquen el motor: frecuencias y caídas para modos, recorridos de formantes y notas para fuente-filtro, controles de modulación para FM, conexiones y trazas para redes.
- GIF del proceso real, en loop, hasta 10 s y hasta 15 MB. Si reúne capas o análisis de una ejecución, decirlo. No fingir borradores o pasos internos que no se capturaron.
- `proceso/README.md` con orden, parámetros, origen de imágenes y límites.
- Explicación comprensible: qué tocar, qué escuchar, qué cambió, por qué se eligió y qué no se comprobó.

El programa debe generar audio, imágenes y receta juntos. No dar por terminada la entrega si faltan las imágenes exigidas. El laboratorio y los productores Python incluidos generan un conjunto básico; ampliarlo cuando la idea necesite una gráfica específica. Conservar las imágenes reales de etapas mientras se trabaja.

## Conservación y revisión

Crear cada carpeta de salida de forma exclusiva. Nombre descriptivo, semilla cuando exista e identificador de al menos 12 caracteres de SHA-256. El identificador completo incluye datos/imagen, versión de programa y nonce nuevo. Registrar hashes de contenido. Nunca sobrescribir avances ni entregas anteriores.

Comprobar señal finita, duración, niveles, comportamiento del control y reproducibilidad. Revisar visualmente PNGs y GIF y medir tamaño/duración. Distinguir pruebas técnicas de escucha humana. Guardar un repositorio git con un commit por avance significativo; no incluir credenciales ni subir a un remoto sin solicitud del autor.

Las imágenes anteriores del paquete son referencias explicadas y conservan su procedencia. No usarlas como evidencia de haber ejecutado un experimento nuevo.
