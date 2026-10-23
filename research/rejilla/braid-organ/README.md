# Braid Organ

Canek Zapata, 2026. Instrumento virtual y escultura de net art: tres cintas, un acorde y una memoria hecha de cruces.

Abrir `abrir-braid-organ.bat` en Windows, o ejecutar `python abrir.py`. Usa HTTP local porque AudioWorklet y módulos no funcionan al abrir el HTML como archivo. Three.js está incluido con su licencia; no necesita Internet ni instalar dependencias.

## Tocar

- **Listen** enciende un acorde mayor afinado en proporciones 1:5/4:3/2. **Rest** apaga la excitación con una caída suave; conserva la trenza.
- Arrastrar una perla hacia su vecina hace un cruce; Shift pasa la perla por debajo. Las teclas/botones **A**, **B**, **A⁻¹**, **B⁻¹** funcionan también. En teclado, Shift+A / Shift+B hacen los inversos.
- **Undo** deshace el último gesto; **Unweave** borra la partitura y devuelve el estado al inicio. Se conserva el tiempo de los osciladores y la cola de reverberación.
- **Play a weaving** interpreta *The Way Back*: `ABaBABAb` seguido por su inverso en orden contrario. Aproximadamente 34 s; termina en el estado tímbrico inicial con la historia dibujada. Minúsculas significan inversos. Un gesto manual, Rest o Escape cancela lo que falta de la partitura.
- Arrastrar el vacío gira la vista; rueda acerca/aleja. **Enter the braid** entra entre las cintas. Tres voces se localizan en las perlas mediante HRTF y el oyente sigue a la cámara. Audífonos permiten apreciar mejor la diferencia.
- **ROOT** transpone el acorde. **About** explica el instrumento y permite generar una postal limpia, sin interfaz.

La altura de la escultura representa el orden temporal de los cruces. Al crecer la palabra se comprime verticalmente su historia; no es un cuerpo mecánico de cinta elástica. Los colores siguen la identidad de cada hebra. Límite de 96 cruces por tejido; Undo y Unweave permiten continuar.

## Documentos y comprobación

- [Idea y traducción matemática](docs/instrumento-y-matematica.md).
- `node pruebas.mjs`: unitariedad, relación de trenza, no conmutación, norma, inversos, deriva de 1200 gestos e identidad de señales equivalentes con el mismo tiempo de osciladores.
- Las flores leen el espectro real de cada voz después de su proyección espacial. La expansión breve de un cruce es un acento gestual, multiplicado por la actividad sonora; no se presenta como medición física.
- `dist/` es la pieza autónoma. `vendor/` contiene únicamente Three.js y su licencia MIT.

Versión 1.0.0. Entrega local sin publicación. La URL canónica y las tarjetas sociales proponen `https://canekzapata.net/braid-organ/`; **TODO: confirmar la ruta al publicar**. Los metadatos y la interfaz están en inglés como en la campana, con autoría de Canek Zapata.

Las capturas y GIF de esta ejecución están en [braid-organ-970c1ab38e2a/proceso](braid-organ-970c1ab38e2a/proceso/README.md). El identificador SHA-256 se deriva de la primera captura real, el núcleo algebraico, versión y nonce nuevo; la receta conserva el identificador completo y las huellas de contenido. Se creó la carpeta exclusivamente y se rechazan destinos existentes. No reemplaza entregas anteriores.
