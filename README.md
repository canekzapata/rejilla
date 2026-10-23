# Rejilla

Partituras e instrumentos de Canek Zapata: síntesis espectral, modelos físicos
y música a partir del terreno de Traspuesta.

Esta edición reúne fuentes vigentes y una partitura. Los renders, grabaciones,
videos, ZIPs, cachés y versiones históricas del taller quedan fuera de Git.

## Qué hay

- `partituras/lo-que-el-agua-dibuja.json`: partitura completa, semilla 67.
- `biblioteca-de-instrumentos/`: fichas, motores y código conservado.
- `research/rejilla/`: núcleo espectral, generador del Agua y familias recientes:
  Tres tiempos, Telar, campanas, Braid, Astrolabio, Talbot, Möbius–Grisey,
  Toda–KdV, Berry y Siringua, entre otras.
- `research/montanas-topograficas/`: Traspuesta, atlas y visor vigente.
- `docs/MANUAL.md`: manual completo del taller. Conserva referencias a la
  edición pedagógica anterior; aquí no se distribuye aquel laboratorio completo.
- `PROCEDENCIA.json`: origen y huella de las fuentes copiadas y adaptaciones.
- `requirements.txt`, `.gitignore` y `LICENSE.md`.

Se conservan algunas rutas de carpetas del taller para mantener los imports
existentes. No es una copia completa de cada canción ni un instalador universal.
Las 231 fichas son versiones con motor, no instrumentos únicos; las 34 entradas
copiadas y 27 referencias documentales no se presentan como adaptadores listos.

## Empezar

Python 3.11 o posterior, Node.js 22 o posterior. FFmpeg con `spectrumsynth` para
la vía espectral; el render corto de prueba usa NumPy/SciPy y no necesita FFmpeg.

```powershell
python -m pip install -r requirements.txt
python biblioteca-de-instrumentos/tomar.py --lista
python herramientas/nota.py marimba --salida renders/marimba.wav
node biblioteca-de-instrumentos/pruebas/objetos_suenan.cjs
```

Para regenerar la partitura del Agua:

```powershell
python research/rejilla/lo-que-el-agua-dibuja/partitura.py renders/agua
```

Este repositorio no incluye la cadena completa de render y mezcla de sus 23
capas ni el audio terminado. Sí incluye sus eventos, el generador y los motores
de guitarra y lluvia. Los bancos de voz son opcionales: ver `difonos/README.md`.

Para recorrer Traspuesta:

```powershell
python -m http.server 8481 --bind 127.0.0.1
```

Abre `http://localhost:8481/research/montanas-topograficas/`.

## Trabajo y publicación

Guarda lo que generes en `renders/` o `salidas/`, que están ignorados por Git.
Los audios y videos para descargar se pueden distribuir aparte como Releases;
el historial del repositorio conserva el código y las partituras.

La licencia de publicación está pendiente; consulta `LICENSE.md` antes de
presentar este repositorio como software de código abierto.
