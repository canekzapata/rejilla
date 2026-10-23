# eSpeak NG para el lector de Difonos

El lector usa **eSpeak NG 1.53.0**, compilado con Emscripten 6.0.12 a un módulo de extracción fonética. Difonos llama `espeak_TextToPhonemesWithTerminator` y convierte su IPA al inventario ARPABET que ya consume VozAgua. No usa la síntesis de audio de eSpeak. No requiere un servidor de procesamiento: en navegador el texto y las tablas se procesan localmente en WASM; la página sólo debe servir los archivos estáticos.

La extracción incluye vocales reducidas, diptongos, consonantes y posición del acento primario/secundario. Para conservar el rango de cada palabra, esta primera versión procesa cada palabra por separado: un homógrafo cuya pronunciación dependa de la sintaxis puede requerir `corrections`. No se derivan límites silábicos. Los números se anotan como omitidos y no se envían al motor.

## Archivos entregables

- `runtime/espeak-wasm/difonos-espeak-en.js` — inicializador JavaScript, 67,052 bytes.
- `runtime/espeak-wasm/difonos-espeak-en.wasm` — motor, 316,805 bytes.
- `runtime/espeak-wasm/difonos-espeak-en.data` — fonemas, voz y diccionario inglés compilados, 872,086 bytes.
- Peso conjunto: 1,255,943 bytes (1.20 MiB). La cifra es de los tres archivos compilados en esta revisión.
- `wasm/phonemizer.c`, `wasm/CMakeLists.txt` y `herramientas/compilar-espeak-wasm.ps1` permiten reconstruir el módulo.

## Reconstruir en Windows

El código fuente de eSpeak NG vive en el clon local `vendor/espeak-ng/` y el SDK Emscripten en `emsdk/`. Si hace falta recuperar el clon, usar `git clone https://github.com/espeak-ng/espeak-ng vendor/espeak-ng` y fijarlo al commit `ba90c8e9f440ad544f674a790bb5f53878b6ffc5` antes de compilar. El script usa el SDK 6.0.12 y el CMake 4.2.0-rc3 instalados en el SDK:

```powershell
./herramientas/compilar-espeak-wasm.ps1
```

Las tablas de ejecución ya generadas y guardadas en `vendor/espeak-ng-wasm/data/` corresponden a `en-us`; se reconstruyen desde `dictsource/en_rules`, `dictsource/en_list`, `phsource` y las voces/configuraciones de `espeak-ng-data` del commit fijado.

## Licencia y procedencia

El motor se distribuye bajo GPL-3.0-or-later. La compilación enlaza eSpeak NG estáticamente; quien distribuya este lector debe cumplir la GPL y ofrecer el código fuente correspondiente. Se incluyen los avisos `COPYING`, `COPYING.APACHE`, `COPYING.BSD2` y `COPYING.UCD` del origen para las partes cubiertas. Revisar los avisos antes de integrar estos archivos a una distribución con otra licencia.

Commit de origen: `ba90c8e9f440ad544f674a790bb5f53878b6ffc5` (`1.53.0`). La API oficial de conversión está declarada en `src/include/espeak-ng/speak_lib.h`; la función que usa el puente se implementa en `src/libespeak-ng/speech.c`.

SHA-256 del paquete actual:

| Archivo | SHA-256 |
|---|---|
| `difonos-espeak-en.js` | `81aee7745a7c68d04ba06cdec1b24f01590ca4a4d8e35ac941b27217a64534c7` |
| `difonos-espeak-en.wasm` | `2e1e387046097f300ee14d425560b1fb2c5b7464f6b4503361bc9f7c889b928d` |
| `difonos-espeak-en.data` | `a32b5f50fa2d01415f42c91141b3e9e091dc3bcbeda6a9e0c7e6197fa4da35c0` |
