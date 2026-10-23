# Cobertura del taller restaurado

Revisión: 23 de octubre de 2026.

El catálogo de 330 entradas reúne distintas clases de material. No es un conteo
de instrumentos únicos: hay versiones, procesos y referencias de familias.

| Material | Entradas | Uso |
|---|---:|---|
| Fichas de la biblioteca | 231 | Motores modal, gemelo, Python, objetos y navegador |
| Código copiado de la edición anterior | 34 | Fuentes conservadas; sin adaptador común |
| Prototipos de tres tiempos y otros | 12 | Pedido JSON y productor Python |
| Motores y procesos propios | 38 | Pedido JSON y productor Python/Node |
| Familias recientes adicionales | 15 | Fuentes y documentación; API propia o adaptación pendiente |

Las doce referencias de tres tiempos del índice de biblioteca se corresponden
con los doce prototipos: no se añaden otra vez al catálogo.

## Fuentes conservadas

`INVENTARIO-INSTRUMENTOS.json` coteja **1494 archivos de código del Rejilla actual**
(**652 contenidos distintos**) y **877 filas de código del censo editorial anterior**
(871 de Rejilla y seis de otras dependencias de aquel taller). Todas las filas
apuntan a una copia con su SHA-256 original. Una ruta archivada representa una
versión conservada, no una promesa de que ese programa antiguo corra solo.

Los originales que requerían adaptación se conservan en `archivo/motores/`.
Las adaptaciones de uso están en las rutas activas. `PROCEDENCIA.json` distingue
huellas originales y actuales. Los scripts auxiliares, versiones y canciones no
se cuentan como instrumentos nuevos.

## Qué se puede producir

El laboratorio calcula muestras para las 231 fichas y los 50 ejemplos/prototipos.
La secuenciación de 16 pasos ofrece los 30 timbres Web Audio. Las 122 fichas
Meleeviewer usan sus escenarios originales; se incluyeron las dos partituras
necesarias para que no dependan de la carpeta de trabajo del autor.

Los cuatro paquetes externos (Fano, Navier–Stokes, Gross–Pitaevskii y Hofstadter)
y las familias recientes conservan su código. Algunas rutas de sus programas
originales todavía requieren adaptación antes de producir desde otra máquina.
Sus entradas permanecen identificadas y sin botón de muestra integrada. No se
reemplazan por otro sintetizador para aparentar compatibilidad.

La cadena completa del Agua incluye el banco de Sabina y las 23 capas de mezcla.
`herramientas/producir_agua.py` ejecuta sus motores y guarda resultados nuevos.
Las piezas históricas que usaban otras grabaciones o recursos externos pueden
necesitarlos: esta entrega conserva el código, no todas las sesiones de producción.

## Manual y resultados

El PDF conserva la edición editorial original. README.md y el manual HTML/Markdown
actualizan el arranque y las rutas de esta edición. Las muestras se calculan al
pedirlas y se guardan fuera de Git. Las ilustraciones antiguas de `imagenes/` están
identificadas como tales. Las capturas y gráficas nuevas están en `proceso/`.

Consulta `VERIFICACION.md` y los JSON de pruebas para distinguir conservación de
fuentes, producción de señal y comprobación de la cadena completa.
