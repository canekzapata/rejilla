# rejilla · investigación y lo aprendido con El Candelabro de Möbius–Grisey ($\mu * \mathcal{M}_s$, 21 de octubre de 2026)

Cuaderno de investigación, sonda y producción real de **El Candelabro (Criba) de Möbius–Grisey** (`criba_mobius_grisey.py`), construido para cruzar el motor espectral de [Rejilla](../README.md) (`spectrumsynth` de FFmpeg) con la estética espectral de [Gérard Grisey](https://en.wikipedia.org/wiki/G%C3%A9rard_Grisey) ([Partiels](https://en.wikipedia.org/wiki/Partiels), [Les Espaces Acoustiques](https://fr.wikipedia.org/wiki/Les_Espaces_acoustiques)), la [fórmula de inversión de Möbius](https://en.wikipedia.org/wiki/M%C3%B6bius_inversion_formula) ($\mu(n)$), la [convolución de Dirichlet](https://en.wikipedia.org/wiki/Dirichlet_convolution), las [sumas de Ramanujan](https://en.wikipedia.org/wiki/Ramanujan%27s_sum) ($c_q(n)$) y la [transformada de Mellin](https://en.wikipedia.org/wiki/Mellin_transform).

Complementa [APRENDIDO.md](../APRENDIDO.md), [ESPECTRAL.md](../aurora/ESPECTRAL.md), [BASES-TEORICAS-INSTRUMENTOS-2026-10-19.md](../BASES-TEORICAS-INSTRUMENTOS-2026-10-19.md), [08-SONAR-LO-VIRTUAL.md](../la-fase-vuelve-distinta/la-fase-vuelve-distinta-s19102691-7fbc97cc5f1c/fuentes/08-SONAR-LO-VIRTUAL.md) y [TEXTURAS.md](../maquina/TEXTURAS.md).

---

## 1. Qué problema físico resuelve la Inversión de Chen–Möbius en la rejilla

Cuando un instrumento físico intenta tocar la [serie subarmónica](https://en.wikipedia.org/wiki/Undertone_series) ($f_0 / d$) o apilar generadores sobre los divisores de un espectro, cada generador $d$ emite inevitablemente su propia [serie armónica](https://en.wikipedia.org/wiki/Harmonic_series_(music)) $k = 1, 2, 3\dots$, de modo que en cada múltiplo compuesto $m = d \cdot k$ se amontonan todos los divisores $d \mid m$ (función divisor $\tau(m)$).

Al pesar cada rama $d$ con el coeficiente de la [función \$\\mu(d)\$ de Möbius](https://en.wikipedia.org/wiki/M%C3%B6bius_function) ($\mu(1)=+1$, $\mu(\text{primo})=-1$, $\mu(\text{biprimo})=+1$, $\mu(\text{con cuadrado})=0$), la amplitud resultante en cada múltiplo $m$ pasa a estar gobernada por la identidad fundamental de la [convolución de Dirichlet](https://en.wikipedia.org/wiki/Dirichlet_convolution):

$$\sum_{d \mid m} \mu(d) = \delta_{m, 1} = \begin{cases} 1 & \text{si } m = 1 \\ 0 & \text{si } m > 1 \end{cases}$$

---

## 2. Qué midió y qué descubrió la sonda (`ejecutar_sonda()`)

Probamos el motor en `spectrumsynth` (`S = 32768`, `H = 16384`, $1\text{ columna} = 1.0\text{ s}$, $1\text{ fila} = 1.0\text{ Hz}$). La sonda certificó cinco propiedades cuantitativas y descubrió un fenómeno acústico inesperado entre los [círculos de Ford](https://en.wikipedia.org/wiki/Ford_circle) y la cancelación de Dirichlet:

| Prueba medida en `ejecutar_sonda()` | Valor medido | Qué significa física y musicalmente |
| :--- | :--- | :--- |
| **SNR `spectrumsynth` vs suma temporal** | **$73.83\text{ dB}$** | Reconstrucción exacta de la criba aritmética desde los mapas `gray16le` de magnitud y fase. |
| **Conservación de la raíz ($m = 1$, $110\text{ Hz}$)** | **$+0.01\text{ dB}$** | El nodo fundamental ($d = 1$) atraviesa la criba sin perder un solo decibelio de cuerpo. |
| **Aniquilación de sobretonos compuestos ($m = 2..6$, ataque síncrono)** | **$-59.97\text{ dB}$** | Cuando los divisores entran al unísono, los primos ($\mu = -1$) y los biprimos ($\mu = +1$) **cancelan por interferencia destructiva casi $60\text{ dB}$** de todos los sobretonos compuestos parásitos. |
| **Hallazgo de la sonda: Desfase de Ford ($\Delta t = 140\text{ ms}$) vs Dirichlet** | **$-6.07\text{ dB}$** (promedio con transitorio) | Cuando los divisores entran escalonados según el radio de su [círculo de Ford](https://en.wikipedia.org/wiki/Ford_circle) $\Delta t_d \propto 1 - 1/d^2$, el primo $d=2$ y el primo $d=3$ entran *antes* que el biprimo $d=6$. Durante esos milisegundos en que el biprimo aún no llega, la suma $\sum_{d \mid 6} \mu(d)$ está incompleta y **suelta una «chispa aritmética de ataque»** que luego se apaga sola en el sostén cuando entra $d=6$. |
| **Huecos *square-free* ($\mu(4)=\mu(8)=\mu(9)=\mu(12)=0$)** | **$-68.67\text{ dB}$** | En las filas de las octavas cuadráticas ($4f_0, 8f_0$) y la novena/duodécima cuadrada ($9f_0, 12f_0$), la energía cae casi $69\text{ dB}$, dejando túneles limpios para que la voz solista cante sin enmascaramiento. |
| **Espejo de Mellin ($\gamma = +1 \leftrightarrow \gamma = -1$, pivote $330\text{ Hz}$)** | **$673.6\text{ Hz} \leftrightarrow 232.9\text{ Hz}$** ($+1.03\text{ oct} \leftrightarrow -0.50\text{ oct}$) | Al invertir el exponente de [Mellin](https://en.wikipedia.org/wiki/Mellin_transform) de $+1$ a $-1$, el centroide espectral cruza de estar una octava arriba del pivote a colgar media octava por debajo hacia el registro subgrave. |
| **Selectividad del Resonador de Ramanujan ($q = 7$)** | **$+6.77\text{ dB}$** | Multiplicar por la [suma de Ramanujan](https://en.wikipedia.org/wiki/Ramanujan%27s_sum) $c_7(n)$ realza casi $7\text{ dB}$ el 7º armónico/subarmónico frente a los parciales coprimos $(2, 3, 5)$ sin mover la nota fundamental. |

---

## 3. El descubrimiento musical: «La Chispa Aritmética de Ford» y la Costura *Square-Free*

1. **Por qué el desfase de Ford vuelve vivo al instrumento:**
   Si todos los divisores $d$ entran exactamente en el mismo milisegundo ($\Delta t_{\text{Ford}} = 0$), la cancelación $\sum_{d \mid m} \mu(d) = 0$ es de **$-59.97\text{ dB}$** desde el instante cero: perfecta en laboratorio, pero estática al oído. En cambio, al abrir `retardo_ford` entre $0.18\text{ s}$ y $0.38\text{ s}$ (como las entradas escalonadas de [Partiels](https://en.wikipedia.org/wiki/Partiels) de [Gérard Grisey](https://en.wikipedia.org/wiki/G%C3%A9rard_Grisey)), cada acorde tiene **tres fases audibles dentro de una misma nota**:
   - Primero abre el tronco fundamental ($d=1$, $\mu=+1$).
   - Luego entran los primos ($d=2, 3, 5, 7$, $\mu=-1$), que al estar todavía solos encienden un transitorio metálico en negativo.
   - Finalmente entran los biprimos ($d=6, 10, 14, 15$, $\mu=+1$) y **borran de golpe los sobretonos compuestos de los primos en la cola de resonancia**, dejando que el acorde se limpie por dentro mientras cae.
2. **Costura por ceros de Möbius ($\mu(p^2 k) = 0$) en la escena de 24 s:**
   En `escena-grisey-siringua-s20261021.wav` / `.m4a` ($-14.3\text{ LUFS}$, LRA $8.7$, pico $-3.8\text{ dBTP}$), pusimos a prueba la sexta capa de [TEXTURAS.md](../maquina/TEXTURAS.md) (*Costura*) sin usar un solo ecualizador ni *sidechain* tradicional:
   - El **Candelabro de Möbius–Grisey** construye su catedral sobre el pivote **Mi2 ($f_0 = 82.41\text{ Hz}$)**, mientras abajo ruge el **Trombón Fantasma de Mi0 ($41.20\text{ Hz}$)** con su crescendo de latón y raspado *sul ponticello* de [Partiels](https://en.wikipedia.org/wiki/Partiels).
   - Como $\mu(4) = \mu(8) = \mu(9) = \mu(12) = 0$, el Candelabro tiene **prohibido por aritmética** sonar en $4f_0 = 329.63\text{ Hz}$ (Mi4), $8f_0 = 659.26\text{ Hz}$ (Mi5), $9f_0 = 741.66\text{ Hz}$ (Fa#5 natural) y $12f_0 = 988.88\text{ Hz}$ (Si5).
   - La **Siringua / Voz formántica** ([BASES-TEORICAS-INSTRUMENTOS-2026-10-19.md](../BASES-TEORICAS-INSTRUMENTOS-2026-10-19.md)) canta su melodía **exclusivamente sobre esos números con factor cuadrado ($4f_0, 8f_0, 9f_0$)**, encajando como una llave en la cerradura dentro de los huecos de $-68.67\text{ dB}$ de la criba.

---

## 4. Archivos producidos y verificados (Semilla `20261021`)

- `criba_mobius_grisey.py` — Motor completo (aritmética de Möbius $\mu(n)$, sumas de Ramanujan $c_q(n)$, círculos de Ford, clase `PistaRejilla` para `spectrumsynth`, motor temporal `render_candelabro_temporal`, escena `render_escena_grisey_costura`, sonda `ejecutar_sonda` y láminas en OKLCh).
- `muestra-criba-mobius-grisey-s20261021.wav` (y `.m4a`) — Muestra aislada de $24.0\text{ s}$ ($-19.3\text{ LUFS}$, LRA $14.8$, $-5.2\text{ dBTP}$, SHA-256 WAV `eecfb01a7106fe79`). Recorre: (I) Serie armónica completa tipo *Partiels* ($\alpha_\mu = 0, \gamma = +1$), (II) Activación de la Criba de Möbius *square-free* ($\alpha_\mu = 1$), (III) Colapso en el Espejo de Mellin ($\gamma \to 0.12$) con batimientos diferenciales y sombra en Mi0, (IV) Abismo subarmónico descontaminado ($\gamma = -1$) colgado de Mi4 a Mi0, y (V) Iluminación de primos con sumas de Ramanujan ($q = 7 \to 11$).
- `escena-grisey-siringua-s20261021.wav` (y `.m4a`) — Escena en contexto de $24.0\text{ s}$ ($-14.3\text{ LUFS}$, LRA $8.7$, $-3.8\text{ dBTP}$, SHA-256 WAV `955500a4b841c992`) con el Candelabro de Möbius–Grisey, el Trombón Fantasma de Mi0 ($41.2\text{ Hz}$) y la Siringua cantando en los huecos $\mu(n)=0$ ($4f_0, 8f_0, 9f_0$).
- `01-criba-dirichlet-y-sonda-s20261021.png` — Lámina 01: barras de $\mu(d)$ para $d=1..16$, resultados medidos en la sonda y el Reloj de Arena de Grisey–Mellin ($\gamma: +1 \to 0 \to -1$).
- `02-espejo-mellin-y-espectrograma-s20261021.png` — Lámina 02: curvas de control ($\gamma(t), \alpha_\mu(t), q(t), \beta_{\text{diff}}(t)$), onda estéreo y espectrograma ($35\text{ Hz–}10.5\text{ kHz}$) de la muestra aislada.
- `03-escena-grisey-costura-squarefree-s20261021.png` — Lámina 03: trazas del Espejo de Mellin, las olas del Trombón Mi0 de *Partiels*, la melodía *square-free* de la Siringua y espectrograma de la mezcla.
- `proceso-criba-mobius-s20261021.gif` — GIF en loop de $5.4\text{ s}$ ($3$ cuadros a $1200 \times 720$).
- `receta-criba-mobius-s20261021.json` — Receta completa con parámetros, partitura, resultados de la sonda y huellas SHA-256.
