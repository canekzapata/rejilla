# El tapete de Talbot

Instrumento de rejilla del 21 de octubre de 2026. Lo inventé a partir de la página del [grupo metapléctico](https://en.wikipedia.org/wiki/Metaplectic_group), después de ordenar y arreglar el [Astrolabio](../astrolabio-metaplectico/README.md).

**Entrega:** [`tapete-de-talbot-s20261021-50fbc9bb096b/`](tapete-de-talbot-s20261021-50fbc9bb096b/). Incluye cuatro muestras (los m4a están en git y los wav fuera), cuatro láminas, el GIF del proceso (9.4 s, 1.6 MB), la receta y una copia del código. Se corre con `python tapete.py` y tarda menos de dos minutos.

## La idea

**De dónde sale.** La página dice dos cosas que juntas dan un instrumento:
1. Uno de los generadores del grupo es la **fase cuadrática** 𝒯.
2. El grupo existe también sobre **grupos finitos**: la representación de Weil finita, la de las funciones theta de retícula.

Un loop de N muestras es una función sobre el grupo finito ℤ/N. Si a su armónico n le aplico la fase cuadrática:

```
Y[n] = X[n] · e^(−iπ n² τ)
```

**El efecto Talbot.** Así aparece el efecto Talbot (1836), que en óptica es la «alfombra cuántica», sólo que aquí ocurre en el tiempo:

| τ | qué le pasa al loop |
|---|---|
| 0 | nada |
| **p/q** | se vuelve **L copias de sí mismo**, corridas j·T/L, donde L = q si p·q es par y 2q si es impar. Cada copia tiene un peso que es una **suma de Gauss** |
| irracional | se deshace en una nube: el tapete es fractal |
| 1 | el loop se corre medio periodo |
| 2 | vuelve idéntico |

**Los pesos.** Un peso complejo sobre una copia real suena como mezcla de la copia y su transformada de Hilbert: es otro color del mismo golpe.

**La conexión con el grupo.** Las sumas de Gauss llevan raíces octavas de la unidad: G(p, q) = (p|q)·ε_q·√q, con ε_q = 1 o i. Esa es la raíz cuadrada ε(z)² = cz + d que define el recubrimiento, y la que hace de la función theta una forma modular de peso ½.

**Cómo se toca.** El loop es la urdimbre y τ es la trama. La partitura es un **camino por el tapete**, τ(t). El lector toma bloques de 43 ms: cada bloque usa su τ, transforma el loop entero y lee el pedazo que le toca.

### Los hilos

**El problema.** Con todos los armónicos, el tapete es tan sensible que no se puede deslizar. Si τ se mueve 0.0001, el loop ya es otro: su correlación con el original baja a −0.4. Entre racionales sólo hay nube.

**La solución:** `hilos = M` reduce los armónicos al grupo finito ℤ/M (ñ = n mod M, centrado). Es la misma fase cuadrática, pero en la representación de Weil de ℤ/M. Con eso:
- las copias caen en una retícula de T/M; con M = 16, en los dieciseisavos del compás;
- el tapete se puede deslizar: si τ se mueve 0.001, la correlación sigue en 0.996, y con 0.01 en 0.72.

Los deslizamientos se oyen como **cánones que se transforman**, ya no como ruido.

## Qué se oye

| muestra | loop | hilos | camino |
|---|---|---|---|
| `muestra-1-clave` (26 s) | una clave de madera cada 0.5 s | todos | se queda en 1/4, 1/3, 1/2, 2/3, 3/4, 1 y 2, y cruza la nube entre uno y otro |
| `muestra-2-bateria` (40 s) | un compás de 4/4 a 120 (bombo sincopado, tarola, hats, aro) | todos | 1/2, 1/3, 1/4, la nube áurea (0.618…), 2/3, 2/5, 1/6, 1, 2 |
| **`muestra-3-bateria-16`** (48 s) | el mismo compás | **16** | 1/4, se desliza despacio a 1/2, 1/8, 3/8, 1/16, se desliza a 1/3, 1, 2 |
| `muestra-4-canon` (48 s) | una frase de cuerda grave en re menor (4 s) | todos | 1/2, 1/3, 1/4, 2/5: cada uno es un canon de 2, 3, 4 o 5 voces |

**Lo que no me esperaba (medido):**
- **τ = 1/3 no cae en la cuadrícula.** Las tres copias quedan en 1/6, 3/6 y 5/6 del compás: es un tresillo corrido medio tresillo.
- **τ = 1/5 se comporta igual.** Da 5 copias en los décimos impares.
- **τ = 2/3 sí cae en la cuadrícula** (0, 1/3, 2/3), aunque tiene el mismo denominador que 1/3.

La aritmética, no el músico, decide si el tresillo se adelanta.

## La sonda (medido en la corrida 50fbc9bb096b)

- **Las copias son exactas.** A τ = p/q, la fase cuadrática coincide con la suma de L copias con pesos de Gauss, con un error ≤ 1.4e-15 en 11 racionales.
- **Cuántas copias suenan:**

  | τ | copias que suenan | de cuántas posibles |
  |---|---|---|
  | 1/2 | 2 | 2 |
  | 1/3 | 3 | 6 |
  | 2/3 | 3 | 3 |
  | 1/4 | 4 | 4 |
  | 1/5 | 5 | 10 |
  | 2/5 | 5 | 5 |
  | 1/6 | 6 | 6 |
  | 1/8 | 8 | 8 |

  Todas tienen |c| = 1/√q.
- **Es unitaria.** La energía cambia como máximo 4e-16 con cualquier τ.
- **τ = 1 y τ = 2.** τ = 1 coincide con el loop corrido medio periodo (7.8e-16). τ = 2 coincide con el loop original (7.8e-16).
- **Las sumas de Gauss** coinciden con (p|q)·ε_q·√q para todos los primos q ≤ 23 (error 9.4e-13). Es la raíz octava.
- **La nube tiene menos cresta.** El factor de cresta de la envolvente es 4.4 en τ = 0. En τ = 0.618 baja a 3.26, en τ = √2−1 a 3.13, y en 1/3 + 1e-6 a 3.32: con apenas una millonésima ya es nube.
- **Con 16 hilos**, el loop transformado es exactamente la suma de sus 16 corrimientos con los pesos w (error 7e-16). Cuántos hilos suenan:

  | τ | hilos que suenan | dónde caen |
  |---|---|---|
  | 1/2 | 2 | los tiempos 0 y 8 |
  | 1/4 | 4 | los negros |
  | 1/8 y 3/8 | 8 | los corcheas |
  | 1/16, 1/3 y 1/5 | 16 | todos |
- **El lector** con τ quieto es igual a repetir el loop transformado (error 7e-16).

## Las láminas

1. `01-tres-urdimbres`: el tapete con 16, 48 y 120 hilos. Las filas son τ de 0 a 2; la luz es el peso de cada hilo y el color, su fase. Con 16 hilos se ven arcos. Con 48 y 120 casi todo es nube, y los racionales sencillos aparecen como puntos brillantes.
2. `02-bateria-16-hilos`: el tapete del compás junto al camino de la muestra 3, con la misma escala de τ.
3. `03-quien-suena`: qué copias suenan en cada racional, dónde caen y con qué fase. Abajo, los errores de la sonda.
4. `04-espectrogramas`: las cuatro muestras con su τ(t). Los deslizamientos de la muestra 2 son ruido; los de la muestra 3, con 16 hilos, no.

**El GIF** muestra las tres urdimbres tejiéndose fila por fila, de τ = 0 a 2, y después las otras tres láminas.

## Cómo tomarlo en una canción

- **Funciones:**
  - `talbot(loop, τ, hilos)`: transforma un loop (un periodo exacto).
  - `leer(loop, camino, dur, hilos)`: lo recorre.
  - `camino_por_nudos([(t, τ), …])`: arma el camino. Con `Fraction` el tramo es exacto; dos nudos distintos se deslizan entre sí.
- **Qué loops sirven:** cualquiera cuya duración sea un periodo exacto, como un compás, una frase o un gesto. El número de muestras N debe ser divisible entre L para que las copias caigan en muestras enteras: con 96 000 sirven q = 1–6, 8, 10 y 12.
- **Ideas:**
  - un breakbeat que en el puente pasa por 1/3 y vuelve, para un tresillo que se adelanta solo;
  - un coro que se vuelve canon de 4 en 1/4;
  - el «medio periodo» de τ = 1 como síncopa global.

**Sin escucha humana todavía.**
