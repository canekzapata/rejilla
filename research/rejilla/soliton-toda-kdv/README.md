# El Solitón Subarmónico de Toda–KdV

Llegó el 21 de octubre de 2026 en `biblioteca-de-instrumentos/argon/`, hecho fuera de esta máquina por otra IA. Es el tercero de la misma tanda, después del [Astrolabio](../astrolabio-metaplectico/README.md) y del [Candelabro de Möbius–Grisey](../criba-mobius-grisey/README.md). Vive en rejilla porque escribe en la `PistaRejilla`. La carpeta `argon/` quedó vacía otra vez y se borró.

## Qué es

Siete voces, dos subarmónicas («ballenas»: f0/3 y f0/2) y cinco armónicas (f0, 2f0, 3f0, 5f0 y 7f0). Cada voz es un **solitón de KdV**. Su envolvente es la autofunción «vestida» q_j = 4κ_j·ψ_j² de un potencial sin reflexión (Kay–Moses), y su altura es fija porque el flujo es isoespectral.

**Cómo se mueven.** Los solitones viajan a 4κ²τ:
- los rápidos y estrechos son los pájaros, y los lentos y anchos son las ballenas;
- cuando chocan intercambian cresta y salen corridos en el tiempo.

**Los controles:**

| control | qué hace |
|---|---|
| **τ** | tiempo del vórtice |
| **η** | 0 = se suman sin tocarse; 1 = choque exacto de KdV |
| **γ** | escala de Grisey: pájaros, humano o ballenas |
| **β** | cuánto se curva la frecuencia durante el choque |

**La escena.** Es un homenaje a *Vortex Temporum*: un piano helicoidal cuyos ataques se corren con el desfase de colisión, y la Siringua cantando en los «cráteres».

## Archivos

| | |
|---|---|
| `soliton_toda_kdv.py` | Motor, sondas, muestras, escena y láminas. Se corre con `python soliton_toda_kdv.py`; tarda unos 30 s. |
| `PROPUESTA-SOLITON-ORIGINAL.md` | La propuesta que trajo. |
| `APRENDIDO-SOLITON-ORIGINAL.md` | Su cuaderno. Los enlaces venían envueltos en búsquedas de Google: 42 se pasaron a Wikipedia o a los archivos de aquí, y 2 a fuentes externas (el portal MaRDI y el Ensemble Intercontemporain) quedaron como texto. Lo que dicen de los pájaros y la fase de Bargmann lo corrige este README. |
| `original-s20261021/` | Su wav original, en disco y fuera de git. |
| **`soliton-toda-kdv-s20261021-2e356de3d07b/`** | **La corrida vigente:** muestra fiel, muestra original, escena, 4 láminas, GIF (7.2 s, 4 cuadros) y receta. |

## Lo que se probó aquí

**La reproducción.** Su sonda da aquí los mismos números:
- isoespectralidad de Toda: 6.06e-10;
- identidad de traza: 7.88e-13;
- desfases de colisión de +0.3662 y −0.7324 s, iguales al teórico;
- cráter de −4.44 dB y de −21.95 dB;
- SNR de 71.75 dB.

La muestra con `fiel=False` no sale idéntica bit a bit, pero la diferencia contra su wav es de **−170 dB**: redondeo del álgebra lineal entre plataformas.

**La matemática está bien.** Kay–Moses, la traza y los desfases son exactos. El problema estaba en cómo el motor que suena (`render_soliton_toda_kdv`) lee el campo.

**Lo que no cuadraba (medido en el motor que suena):**

1. **Las voces rápidas no sonaban.** Cada evento leía el campo en una ventana fija, t ∈ [−1.6, 1.6]. Pero con τ ≠ 0 los solitones rápidos viajan 4κ²τ y salen de ella. Cuántas de las siete voces tenían más de la mitad de su masa (∫q_j = 4κ_j) dentro:

   | evento | 0 (τ −0.14) | 1 (τ 0) | 2 «Pájaros» (τ 0.16) | 3 (τ 0) | 4 (τ −0.08) | 5 (τ 0.12) |
   |---|---|---|---|---|---|---|
   | original | 2 | 3 | **1** | 3 | 1 | 1 |
   | fiel | 7 | 7 | 7 | 7 | 7 | 7 |

   En la sección de los pájaros sólo sonaba f0: los armónicos de 2f0 a 7f0 tenían 0 % de su masa dentro.

2. **Los saltos de colisión no son una curvatura del groove.** Entre η = 1 y η = 0, los centros de las voces que sí sonaban se corrían de 0.3 a 1.1 s.

3. **La «transparencia de Bargmann» no es un all-pass.** En el motor es una fase constante por voz: cambia la onda, pero el espectro apenas cambia (−20 dB). No hay un camino para pasar otro instrumento por el potencial.

4. **La red de Toda sólo modula el brillo.** Se integra y su isoespectralidad se comprueba, pero en el sonido sólo mueve el brillo de los armónicos internos de cada voz, como un LFO.

5. **El «cráter cuasi-resonante» (−21.95 dB) no es un hueco de volumen.** Es el valor en el centro de simetría. Las dos crestas no se enciman (se repelen) y siguen casi a la misma altura.

**Lo que sí se oye del choque.** En los eventos con τ = 0, el pico de sonoridad de las voces baja de −11 a −11.5 dB con η = 1 contra la suma lineal.

## El arreglo: la perilla `fiel`

La perilla `fiel` va en la partitura o en cada evento. Con `fiel=True` (por omisión), la ventana de cada evento **sigue a los siete solitones**:
- abarca del 0.5 % al 99.5 % de la masa de cada uno, con un margen;
- si el campo es más ancho, el evento lo recorre más rápido, y los pájaros salen como pulsos cortos que se adelantan;
- el paneo por posición se normaliza con el ancho de la ventana.

`fiel=False` reproduce el original. La escena también usa la versión fiel.

## Qué escuchar

| archivo | qué es | LUFS / LRA / pico |
|---|---|---|
| `muestra-soliton-toda-kdv-s20261021.m4a` | fiel: las siete voces en cada evento | −18.9 / 7.0 / −1.8 dBTP |
| `muestra-soliton-toda-kdv-original-s20261021.m4a` | como llegó | −19.2 / 5.4 / −3.6 |
| `escena-vortex-toda-kdv-s20261021.m4a` | solitones, piano helicoidal y Siringua | −16.0 / 8.3 / −3.8 |

**Las láminas:**
- 01–03 son las suyas: la sonda, la muestra y la escena.
- La **04** es la nueva: qué voces suenan con la ventana fija y con la fiel.

**Sin escucha humana todavía.**

## La pieza 3D

[`3d-estanque/`](3d-estanque/index.html) es net art 3D: el estanque de Bargmann–Hirota.
- **Qué hace:** siete esferas solitónicas chocan, y al cruzar τ = 0 se abre el cráter.
- **Cómo está hecha:** three.js con Web Audio, autónoma. Llegó el 21 de octubre en `argon music3d/`.
- **Lo agregado:** los metadatos, `og.png` y `favicon.png`, con `../og3d.cjs`.

Con ella llegaron también la receta y la escena originales del Solitón, que ahora están en `original-s20261021/`; la escena es un wav, fuera de git.
