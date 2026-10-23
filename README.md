# Rejilla

Partituras, instrumentos y taller de Canek Zapata: síntesis espectral,
modelos físicos y música a partir del terreno de Traspuesta.

## Qué incluye esta edición

- Partitura completa de **Lo que el agua dibuja**, su generador y la cadena de
  guitarra, lluvia, voz, batería, mezcla y master de sus 23 capas.
- Banco de voz de Sabina, motores Difonos y fonetizador inglés eSpeak/WASM.
- Laboratorio interactivo: catálogo, secuenciador de 16 pasos, diseño modal y
  exportación de WAV, partitura, PNGs, GIF y receta.
- 231 fichas, 34 entradas de código, 38 ejemplos de motores propios,
  12 prototipos y referencias de las familias recientes. El catálogo tiene
  330 entradas: son fichas, modelos, versiones y referencias; no 330 instrumentos únicos.
- Traspuesta: motor, atlas y visor vigente, sin los videos y renders de trabajo.
- Manual en `manual.pdf`, `manual.html`, `manual.md` y `docs/MANUAL.md`.
- `INVENTARIO-INSTRUMENTOS.json`: cotejo de fuentes actuales e históricas.
  `archivo/` conserva código original que tenía varias versiones o rutas largas.

Las familias recientes y los paquetes externos conservan sus fuentes; algunas
siguen sin adaptador común. El catálogo indica ese estado y desactiva la escucha
cuando no hay una vía integrada. Conservar fuentes no equivale a reproducir
cualquier pieza histórica: esas piezas pueden requerir sus grabaciones o datos.

## Abrir el taller

Python 3.11 o posterior y Node.js 22 o posterior. Instala las dependencias una vez:

```powershell
python -m pip install -r requirements.txt
npm ci
npx playwright install chromium
python herramientas/servidor.py --abrir
```

Abre `http://127.0.0.1:8481/laboratorio.html`. El servidor sólo escucha en tu equipo.
El secuenciador y diseño modal usan Web Audio; las demás muestras se calculan con
Python/Node al pedirlas y quedan en `renders/`, fuera de Git. Para producir desde
una partitura o usar la ventana Python:

```powershell
python python/taller.py ejemplos/02-patron.json
python python/ventana.py
```

Los botones `Taller-Windows.bat` y `Taller-Mac.command` abren la ventana de
producción Python después de preparar su entorno. Para el laboratorio usa el
servidor anterior. El manual original describe la edición pedagógica; esta guía
actualiza sus rutas y sustituye las muestras históricas por cálculo local.

## Producir el Agua

Instala también FFmpeg en el sistema. La vía espectral necesita una compilación
con `spectrumsynth`. La canción completa dura aproximadamente 4:41 y genera
varios GB de pistas temporales; guarda las salidas fuera del historial Git.

```powershell
python herramientas/producir_agua.py
```

Cada ejecución crea carpetas nuevas en `renders/` (pistas temporales) y
`salidas/` (WAV, M4A, partitura, receta y proceso con PNGs/GIF). No sobreescribe
una ejecución previa. Para una prueba técnica más corta que activa las 23 capas:

```powershell
python herramientas/verificar_agua.py
```

La partitura original sigue en `partituras/lo-que-el-agua-dibuja.json`. La prueba
de 40 segundos usa una partitura de integración distinta; no es la composición.

## Traspuesta

Con el servidor abierto, visita
`http://127.0.0.1:8481/research/montanas-topograficas/`.
La carpeta original completa ocupa 2.04 GB, incluidos videos y resultados. El
núcleo funcional incluido aquí ocupa aproximadamente 1.06 MB. Una selección
independiente de código, documentación y recursos básicos ocupa 4.07 MB.

## Publicación

No se guardan en Git audios terminados, videos, ZIPs, entornos ni cachés. La única
excepción de audio es el banco pequeño que el motor de voz necesita para funcionar.
Los materiales de terceros conservan sus avisos; consulta `LICENSE.md` y
`difonos/vendor/espeak-ng-wasm/README.md`. La licencia de las obras y el código
de Canek sigue pendiente de elección.

Las URLs de publicación del HTML son provisionales (`canekzapata.net/rejilla-taller/`)
y están señaladas con TODO. Las verificaciones y sus límites están en
`docs/VERIFICACION.md`. Esta actualización se prepara localmente; para subirla,
ejecuta `git push` después de revisar el commit.
