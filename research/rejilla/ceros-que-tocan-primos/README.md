# Los ceros que tocan a los primos

Instrumento de rejilla del 21 de octubre de 2026. Lo propuse yo después de limpiar los tres que llegaron por `argon/`, y Canek lo pidió («suena rarísimo y sensacional»).

**Entrega:** [`ceros-que-tocan-primos-s20261021-b646ea118e0a/`](ceros-que-tocan-primos-s20261021-b646ea118e0a/). Incluye la muestra de 41 s (el m4a está en git y el wav fuera), cuatro láminas, el GIF de 9 s, la receta y una copia del código.

## La idea

La fórmula explícita de Riemann–von Mangoldt, escrita en u = log x, es:

```
Σ_n Λ(n) n^(−1/2) δ(u − log n)  =  e^(u/2)  −  2 Σ_γ cos(γ u)  −  (ceros triviales)
```

Aquí ½ + iγ recorre los ceros no triviales de la zeta, y Λ(n) = log p si n = p^k (cero si no).

**Lo que dice.** Si sumas un coseno por cada cero, el resultado se cancela casi en todas partes. Sólo se refuerza en log 2, log 3, log 4, log 5, log 7, log 8, log 9, log 11… y cada golpe pesa log p/√n. Nadie escribe ese ritmo: lo deciden los ceros.

**Cómo se toca.** El instrumento suena esa suma con u(t) = ∫r dt:

| control | qué hace |
|---|---|
| **r grande** | cada cero es un parcial de γ·r/2π Hz: un acorde inarmónico, porque los ceros no guardan razón entre sí |
| **r chico** | los mismos cosenos son lentos, y su interferencia da golpes en los primos |
| **γ_max** (la nitidez) | cuántos ceros suenan. Con 12 los primos son oleajes; con 2000 son golpes secos. Ver la lámina 02 |

## La muestra: un palíndromo con espejo en el 2

| | qué pasa |
|---|---|
| **I · el acorde** (0–9 s) | u corre **hacia atrás** desde 346, a 32.6 por segundo. El primer cero suena en re2 (73.4 Hz) y se van sumando de 12 a 48 ceros. Pares a un lado e impares al otro. |
| **II · la escala baja** (9–16 s) | La rapidez cae exponencialmente: el acorde se hunde. Se suman ceros manteniendo la banda en 180 Hz o menos. Los primos llegan **al revés**, del rugido a 29, 23, 19, 17, 13, 11, 7, 5, 4, 3, 2. |
| **III · el espejo y el accelerando** (16–41 s) | En u = 0.45, justo antes de log 2, u da la vuelta y avanza a 0.45 por segundo con los 2000 ceros. Suenan 2, 3, 4, 5, 7, 8, 9, 11, 13… cada vez más juntos, hasta que se funden en un rugido. Una tarola o un aro caen en los picos **que se detectan en el audio**, no desde una lista de primos. |

**Volumen:** −16.0 LUFS, LRA 11.4, pico −3.8 dBTP. La suma se calcula a 2 kHz, porque su banda nunca pasa de unos 750 Hz, y se sube a 48 kHz con un poco de saturación para darle grano de órgano.

## Los ceros, calculados aquí

`ceros.py` calcula los 2000 primeros en unos 6 s, sin mpmath:
- **Riemann–Siegel** (rápido) para encerrar los cambios de signo de Z(t).
- **Euler–Maclaurin** (ζ(½+it) directa) para afinar cada cero por bisección.

**Comprobación** (`datos/ceros-zeta-2000.json`):
- los primeros diez coinciden con los publicados con un error de **3e-10**;
- la cuenta da 2000 contra 1999.4 de θ(T)/π + 1 (Riemann–von Mangoldt);
- la separación mínima entre ceros es 0.1;
- el último es γ = 2515.29.

Riemann–Siegel con un solo término se equivocaba 0.008 en los primeros: por eso se agregó Euler–Maclaurin.

## La sonda: medida en el audio

Es la lección de los instrumentos que llegaron por `argon/`: no medir sólo la fórmula.

**En u (la fórmula), de 0.5 a 7 (n hasta 1096).** Para cada potencia de primo, la altura del pico en log n contra el ruido de fondo:
- con 2000 ceros, **194 de 209** pasan 5 veces el ruido;
- están todas, sin faltar una, hasta n = 31; la primera que no es 32 (pesa log 2/√32 = 0.12);
- la altura sigue log p/√n con correlación **0.990**;
- con 100 ceros sólo pasan 2: la nitidez es el número de ceros.

**En el audio:**

| tramo | golpes detectados | caen en una potencia de primo | falsos | sin faltar una, hasta |
|---|---|---|---|---|
| III, la ida | 53 | 52 (±13 ms) | 1 | n = 13 (la primera que falta es 16) |
| II, la vuelta | 11 | 11 | 0 | n = 7 (la primera que falta es 8) |

En la ida, los golpes detectados son 2, 3, 4, 5, 7, 8, 9, 11, 13, 17, 19, 23, 25, 29, 31, 37…

**El acorde:** los 12 primeros ceros caen en γ·r/2π con un error de 0.07 Hz o menos.

**Hasta dónde llega.** Pasados u ≈ 4 (n ≈ 50), los primos están más juntos que el ancho de un golpe (π/γ_max en u) y la tarola deja de caer: queda el rugido. Ese límite no es un error: es la nitidez de 2000 ceros.

## Las láminas

1. `01-los-ceros`: los 40 primeros en la recta crítica, y N(T) contra θ(T)/π + 1.
2. `02-la-suma-encuentra-a-los-primos`: la suma con 10, 40, 200 y 2000 ceros sobre las rayas de log n.
3. `03-la-muestra`: el espectrograma, con u(t), la rapidez |r|, la nitidez γ_max y los golpes de la tarola.
4. `04-la-sonda-en-el-audio`: los números de arriba y la línea de los golpes detectados sobre las rayas de log n.

**El GIF** muestra la suma con 1, 2, 3, 5, 8, 13, 25, 50, 100, 200, 500, 1000 y 2000 ceros: los primos se van enfocando.

## Cómo tomarlo en una canción

- **Funciones:**
  - `suma(u, γ_max)`: la voz.
  - `camino()`: un ejemplo de recorrido de u(t).
  - `golpes()`: los disparadores que salen de la propia suma.
- **Ideas:**
  - un bombo que toca los primos con su propio accelerando;
  - quitar la contribución del 2 (restar sus golpes) para que el ritmo cojee;
  - u que va y viene como una mano sobre un cilindro: el palíndromo es sólo un camino.
- **Lo que falta:** escribirlo en la `Pista` de rejilla (spectrumsynth). Cada cero es un modo, así que cabe directo.

**Sin escucha humana todavía.**
