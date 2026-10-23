# El Candelabro (Criba) de Möbius–Grisey

Llegó el 21 de octubre de 2026 en `biblioteca-de-instrumentos/argon/`, hecho fuera de esta máquina por otra IA. Lo hizo en su sandbox, con la copia de rejilla compartida por Drive, igual que el [Astrolabio](../astrolabio-metaplectico/README.md). Escribe en la `PistaRejilla` de spectrumsynth, así que es un instrumento de rejilla: vive aquí, junto al Astrolabio y al [tapete de Talbot](../tapete-de-talbot/README.md). La carpeta `argon/` quedó vacía y se borró.

**Qué es.** Un acorde espectral a la Grisey (*Partiels*) sobre un pivote f0. Cada parcial d se pesa con la función de Möbius μ(d) y tiene cuatro controles:

| control | qué hace |
|---|---|
| **α** | mezcla entre la serie completa (α = 0) y la criba de μ (α = 1) |
| **γ** («espejo de Mellin») | pone el parcial d en f0·d^γ: γ = 1 da armónicos, γ = 0 los junta todos en el pivote y γ = −1 da subarmónicos |
| **q** (sumas de Ramanujan c_q) | realza los parciales múltiplos de q |
| **retardo de Ford** | escalona la entrada de cada parcial d según 1 − 1/d² |

**Modo Chen** (la inversión de Dirichlet): cada generador d emite su propia serie, y en m = d·k se suman los μ(d). Como Σ_{d|m} μ(d) = 0 para m > 1, todo se cancela menos la fundamental.

## Archivos

| | |
|---|---|
| `criba_mobius_grisey.py` | Motor, sondas, muestras, escena y láminas. Se corre con `python criba_mobius_grisey.py`; tarda unos 30 s. |
| `APRENDIDO-CRIBA-ORIGINAL.md` | El cuaderno que trajo, tal cual, salvo los 26 enlaces: venían envueltos en búsquedas de Google y ahora apuntan a Wikipedia o a los archivos de aquí. Lo que dice de los huecos y la chispa lo corrige este README. |
| `original-s20261021/` | La receta original (en git) y sus dos wav (en disco, fuera de git). |
| **`criba-mobius-grisey-s20261021-aaf076a2ad38/`** | **La corrida vigente:** muestra fiel, muestra original, escena, 4 láminas, GIF (7.2 s, 4 cuadros) y receta. |

## Lo que se probó aquí

**La reproducción.** Corre en esta máquina y su sonda da exactamente los mismos números que la original: −59.97, −6.07, −68.67 dB y SNR 73.83. La muestra con `fiel=False` sale **idéntica bit a bit** (SHA del wav `eecfb01a7106fe79`). La escena sale con otro SHA aunque mide igual, como pasó con el Astrolabio: es algo de la plataforma.

**Lo que no cuadraba.** Su sonda mide en un escritor espectral de laboratorio, donde las parejas (d, k) que caen en el mismo m tienen exactamente la misma amplitud. Pero las muestras se hacen con otro motor (`render_candelabro_temporal`), y ahí medí otra cosa (La2 = 110 Hz):

| promesa | lo que daba el motor que suena | por qué |
|---|---|---|
| la inversión de Dirichlet cancela los compuestos (−60 dB) | −14.7 dB sin retardo de Ford; **−2.3 dB** con el retardo de 0.32 s que usa la muestra | cada divisor tenía su propia amplitud, decaimiento, fase de arranque y paneo, y la serie de cada generador se cortaba en k = 5, así que Σ_{d|m} μ(d) quedaba incompleta |
| la «chispa de Ford» se apaga sola en el sostén | no se apagaba: el sostén quedaba igual de sucio | lo mismo |
| huecos libres de cuadrados en 4, 8, 9 y 12 (−68.7 dB), donde canta la Siringua | el 4 quedaba **+4.7 dB por encima** de sus vecinos; el 9 en −6.6 y el 12 en −9.4. Sólo el 8 era hueco | cada parcial trae armónicos internos 2 y 3: el 2·2 rellena el 4, el 3·3 el 9 y el 6·2 el 12 |

**Lo que no reportó y sí está ahí.** Con γ = 0 los 15 parciales caen en el pivote, y entonces el signo de μ pesa: −23.6 dB contra la misma nota con |μ|. Es la función de Mertens sonando (M(15) = −1).

## El arreglo: la perilla `fiel`

La perilla `fiel` va en la partitura o en cada evento. Con `fiel=True` (por omisión) el motor que suena hace lo que la sonda promete:

- **Modo Chen.** Cada generador d llega hasta m ≤ 15, así que la suma de μ está completa. Las parejas que caen en el mismo m comparten amplitud, decaimiento (contado desde t0), fase absoluta y paneo, y todas terminan juntas con un fundido común. El retardo de Ford sólo abre la entrada.
- **Modo Candelabro.** Los armónicos internos h de cada parcial d callan cuando μ(d·h) = 0.

`fiel=False` reproduce el original bit a bit.

**Medido después del arreglo:**

| | original | fiel |
|---|---|---|
| Chen, sostén, con Ford 0.32 s | −2.3 dB | **−136.1 dB** |
| Chen, ataque, con Ford 0.32 s | −0.0 dB | −0.6 dB: la chispa |
| hueco en 4·f0 | +4.7 dB | **−121.3 dB** |
| hueco en 8·f0 | −125.8 dB | −128.3 dB |
| hueco en 9·f0 | −6.6 dB | −139.3 dB |
| hueco en 12·f0 | −9.4 dB | −139.5 dB |

**Ojo con lo que esto implica.** El modo Chen con α = 1 y γ = 1 suena a una **senoide**: la inversión de Möbius de una serie de pesos iguales es la fundamental sola. Lo musical está en el camino: la chispa del ataque de Ford y el colapso hacia el seno. Con γ ≠ 1 los productos d·k ya no coinciden, así que no hay nada que cancelar (la sección IV de la muestra lo usa con γ = −1).

## Qué escuchar

| archivo | qué es | LUFS / LRA / pico |
|---|---|---|
| `muestra-criba-mobius-grisey-s20261021.m4a` | la muestra fiel: en II la chispa se limpia a una senoide | −19.2 / 17.0 / −4.5 dBTP |
| `muestra-criba-mobius-grisey-original-s20261021.m4a` | la misma partitura como llegó | −19.3 / 14.8 / −5.2 |
| `escena-grisey-siringua-s20261021.m4a` | el candelabro, el trombón fantasma en Mi0 y la Siringua, ahora sí en huecos | −14.3 / 8.8 / −3.8 |

**Las láminas:**
- 01–03 son las suyas: la sonda de laboratorio, la muestra y la escena.
- La **04** es la nueva: lo que suena, original contra fiel.

**Sin escucha humana todavía.**
