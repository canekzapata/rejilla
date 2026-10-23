# El Solitón Subarmónico de Toda–KdV ($[L, P] = \dot{L}$): dispersión espectral inversa, potenciales de Bargmann sin reflexión y vórtices de Grisey para Rejilla

Propuesta de instrumento imposible y motor espectral para el sistema [Rejilla](../README.md), construida a partir del método de la transformada espectral inversa, los [pares de Lax](https://en.wikipedia.org/wiki/Lax_pair) ($[L, P] = \dot{L}$) de la [ecuación de Korteweg–de Vries (KdV)](https://en.wikipedia.org/wiki/Korteweg%E2%80%93De_Vries_equation) y la [red de Toda](https://en.wikipedia.org/wiki/Toda_lattice), la dualidad entre la [serie armónica](https://en.wikipedia.org/wiki/Harmonic_series_(music)) y la [serie subarmónica](https://en.wikipedia.org/wiki/Undertone_series), y la poética de los torbellinos temporales de [Vortex Temporum (1994–1996)](https://fr.wikipedia.org/wiki/Vortex_temporum) de [Gérard Grisey](https://en.wikipedia.org/wiki/G%C3%A9rard_Grisey).

Conecta directamente con los documentos del proyecto: [ESPECTRAL.md](../aurora/ESPECTRAL.md), [APRENDIDO.md](../APRENDIDO.md), [BASES-TEORICAS-INSTRUMENTOS-2026-10-19.md](../BASES-TEORICAS-INSTRUMENTOS-2026-10-19.md), [INSTRUMENTOS-POR-INVENTAR-2026-10-19.md](../INSTRUMENTOS-POR-INVENTAR-2026-10-19.md), [08-SONAR-LO-VIRTUAL.md](../la-fase-vuelve-distinta/la-fase-vuelve-distinta-s19102691-7fbc97cc5f1c/fuentes/08-SONAR-LO-VIRTUAL.md) y [TEXTURAS.md](../maquina/TEXTURAS.md).

---

## 1. El problema musical: ¿qué pasa cuando los parciales no se suman linealmente sino que chocan como vórtices?

En la síntesis aditiva tradicional —e incluso en la lectura estándar de una partitura espectral—, cuando un paquete armónico rápido se cruza en el tiempo con un pedal subarmónico lento, **las dos ondas simplemente se suman** ($y = y_1 + y_2$): se atraviesan como fantasmas sin enterarse la una de la otra, apilando energía en el punto de cruce y saturando el centro del compás.

En Vortex Temporum, [Gérard Grisey](https://en.wikipedia.org/wiki/G%C3%A9rard_Grisey) imaginó otra física para el tiempo musical:
1. **Tres arquetipos de onda:** un arpegio giratorio de [Maurice Ravel](https://fr.wikipedia.org/wiki/Vortex_temporum) (*Daphnis et Chloé*) se deforma continuamente entre una **onda sinusoidal pura** (invariante), una **ola espectral en diente de sierra** y un **vórtice esférico o helicoidal**.
2. **Tres escalas de tiempo que colisionan:** el **tiempo de las ballenas** (subarmónicos graves extremadamente dilatados), el **tiempo humano** (el pulso respiratorio del piano y las cuerdas) y el **tiempo de los pájaros o insectos** (paquetes armónicos agudos hiper-comprimidos y veloces).
3. **La ley que faltaba:** ¿qué ecuación de la física matemática hace que las alturas de un acorde sean **invariantes eternos** (no se desafinan jamás aunque choquen violentamente), pero que al cruzarse un paquete rápido («pájaro» armónico) con uno lento («ballena» subarmónica) **no se sumen linealmente**, sino que intercambien su cresta, abran un cráter de silencio en el centro del choque y salgan del otro lado con un **salto de tiempo y de fase no lineal**?

Esa ley existe y es uno de los descubrimientos más bellos del siglo XX: los **potenciales de Bargmann–Kay–Moses sin reflexión** y la dinámica de [solitones](https://en.wikipedia.org/wiki/Soliton) gobernada por un [par de Lax](https://en.wikipedia.org/wiki/Lax_pair) isoespectral.

---

## 2. La operación matemática oscura: Pares de Lax ($[L, P] = \dot{L}$), Función $\tau$ de Hirota y Potenciales de Schrödinger sin Reflexión

Consideremos el operador de Schrödinger unidimensional en el eje temporal de la rejilla:

$$L(\tau) = -\frac{\partial^2}{\partial t^2} + u(t, \tau)$$

donde $t$ es el tiempo dentro del compás (o la coordenada de la cuerda) y $\tau$ es el parámetro de evolución de vórtice (el avance macro-temporal de la pieza). Si el potencial $u(t, \tau)$ evoluciona según la [ecuación de Korteweg–de Vries (KdV)](https://en.wikipedia.org/wiki/Korteweg%E2%80%93De_Vries_equation) $u_\tau - 6 u u_t + u_{ttt} = 0$ (o su versión discreta exacta en la [red de Toda](https://en.wikipedia.org/wiki/Toda_lattice)), Peter Lax demostró en 1968 que la evolución equivale a la ecuación de conmutador ([par de Lax](https://en.wikipedia.org/wiki/Lax_pair)):

$$\frac{dL}{d\tau} = [P, L] = P L - L P, \qquad P = -4\frac{\partial^3}{\partial t^3} + 3\left(u\frac{\partial}{\partial t} + \frac{\partial}{\partial t}u\right)$$

### Qué significa esto para un instrumento de armónicos y subarmónicos

1. **Los armónicos y subarmónicos son autovalores ligados ($\lambda_j = -\kappa_j^2$) de un potencial sin reflexión:**
   La ecuación $\dot{L} = [P, L]$ garantiza que el flujo es **isoespectral**: los autovalores discretos $\lambda_1, \lambda_2, \dots, \lambda_N$ del operador $L(\tau)$ **permanecen constantes hasta la última cifra decimal ($\dot{\lambda}_j = 0$)** por más violenta que sea la colisión.
   En nuestro instrumento, dividimos los $N$ autovalores en dos familias:
   - **Solitones Subarmónicos («Ballenas», lentos y graves):** $\kappa_{\text{sub}, d} = \kappa_0 / d^\gamma$, asociados a la [serie subarmónica](https://en.wikipedia.org/wiki/Undertone_series) $f_0 / d$ ($d \in \{2, 3, 5, 7\}$). Como en KdV la velocidad de propagación de cada solitón es $v_j = 4\kappa_j^2$, los subarmónicos viajan despacio y tienen envolventes anchas ($\Delta t_j \propto 1/\kappa_j$).
   - **Solitones Armónicos («Pájaros», rápidos y agudos):** $\kappa_{\text{arm}, n} = \kappa_0 \cdot n^\gamma$, asociados a la [serie armónica](https://en.wikipedia.org/wiki/Harmonic_series_(music)) $n f_0$ ($n \in \{1, 2, 3, 5, 7, 11\}$). Al tener $\kappa_j$ grande, son pulsos estrechos, altos y veloces que alcanzan y atraviesan a los subarmónicos.

2. **Fórmula determinante de Kay–Moses / Hirota ($\tau = \det(I + M)$):**
   Cuando el coeficiente de reflexión continua es idénticamente cero ($R(k) \equiv 0$, *potencial transparente o sin reflexión*), el potencial exacto $q(t, \tau) = -u(t, \tau)$ se reconstruye mediante la función $\tau$ de Hirota:

   $$\tau(t, \tau) = \det\bigl(I + M(t, \tau)\bigr) = \sum_{\mu \in \{0,1\}^N} \exp\left(\sum_{i=1}^N -2\mu_i \theta_i(t, \tau) + \sum_{1 \le i < j \le N} \mu_i \mu_j \ln A_{ij}\right)$$

   donde $\theta_i(t, \tau) = \kappa_i (t - t_{i,0} - 4\kappa_i^2 \tau)$ es la fase cinemática del solitón $i$, y $A_{ij}$ es la **matriz de acoplamiento de colisión de KdV**:

   $$A_{ij} = \left(\frac{\kappa_i - \kappa_j}{\kappa_i + \kappa_j}\right)^2$$

   A partir de $\tau(t, \tau)$, el campo total de envolventes se obtiene por la segunda derivada logarítmica:

   $$q(t, \tau) = 2 \frac{\partial^2}{\partial t^2} \ln \tau(t, \tau) = 2 \frac{\tau \tau_{tt} - (\tau_t)^2}{\tau^2}$$

3. **Descomposición en Autofunciones Vestidas (identidad de traza de Deift–Trubowitz):**
   ¿Cómo separamos ese potencial no lineal $q(t, \tau)$ en las $N$ voces individuales (cada una con su propia frecuencia armónica o subarmónica $f_j$ en las filas de `spectrumsynth`)?
   Usando el teorema de traza para potenciales sin reflexión: si $\psi_j(t, \tau)$ son las autofunciones normalizadas que resuelven el sistema lineal algebraico de Kay–Moses:

   $$(I + M(t, \tau))\,\boldsymbol{\Psi}(t, \tau) = \mathbf{e}(t, \tau), \qquad M_{ij}(t, \tau) = \frac{2\sqrt{\kappa_i \kappa_j}}{\kappa_i + \kappa_j} e^{-(\theta_i + \theta_j)}$$

   entonces **la suma de los cuadrados de las autofunciones vestidas reconstruye exactamente el potencial multisolitón en todo instante**:

   $$q(t, \tau) = 4 \sum_{j=1}^N \kappa_j \,\psi_j^2(t, \tau)$$

---

## 3. Tres fenómenos acústicos imposibles que nacen de esta ecuación

| Fenómeno físico-matemático | Ecuación exacta en el motor | Qué se escucha en Rejilla (homenaje a *Vortex Temporum*) |
| :--- | :--- | :--- |
| **1. Salto temporal de colisión ($\Delta t_{ij}$)** | $\Delta t_i = \frac{1}{\kappa_i} \sum_{j \ne i} \operatorname{sgn}(\kappa_i - \kappa_j) \ln\left\lvert\frac{\kappa_i + \kappa_j}{\kappa_i - \kappa_j}\right\rvert$ | Cuando un arpegio armónico rápido ($\kappa_i$ grande) alcanza a un bordón subarmónico lento ($\kappa_j$ pequeño), **el armónico salta hacia adelante en el tiempo** ($\Delta t_i > 0$, se adelanta al metrónomo) y **el subarmónico retrocede** ($\Delta t_j < 0$, se recuesta hacia atrás). El ritmo se curva por gravedad espectral sin tocar el tempo global. |
| **2. Cráter de colisión (Costura no lineal automática)** | En el centro exacto del choque ($\theta_1 = \theta_2 = 0$): $q_{\text{col}}(0) = 2(\kappa_1^2 - \kappa_2^2) < 2\kappa_1^2 + 2\kappa_2^2$ | Al revés que la suma lineal (donde dos ondas que se cruzan suman sus picos y saturan), **dos solitones que chocan disminuyen su altura máxima durante el cruce**. El solitón grande se achata y le transfiere su cresta al pequeño: **en el instante exacto del choque se abre un cráter de amplitud** donde cabe la voz solista o el piano espectral sin compresión externa. |
| **3. Transparencia de Bargmann ($T(k) e^{i\Phi(k)}$)** | Coeficiente de transmisión $T(\omega) = \prod_{j=1}^N \frac{\omega + i\kappa_j}{\omega - i\kappa_j}$ con $\lvert T(\omega)\rvert \equiv 1$ | Si hacemos pasar otro instrumento (como la `Siringua` o un arpegio de piano) a través del potencial $u(t, \tau)$, el potencial es **100% libre de reflexión** ($\lvert T(\omega)\rvert = 1$, no ensucia ni filtra las magnitudes), pero enrolla la fase de cada frecuencia en $\Delta\Phi(\omega) = -2\sum_j \arctan(\kappa_j / \omega)$ (un filtro *all-pass* cuántico gobernado por los solitones). |

---

## 4. Cómo se toca: «El Solitón Subarmónico de Toda–KdV»

**Imagen acústica y poética:** Imagina un estanque estrecho de mercurio donde flotan dos clases de ondas solitarias que no se dispersan nunca:
- En el fondo se mueven lentamente **dos grandes ballenas subarmónicas** ($f_0/2 = 82.4\text{ Hz}$ y $f_0/3 = 54.9\text{ Hz}$ bajo el pivote Mi3 = $164.81\text{ Hz}$, llegando hasta el Mi0 = $41.2\text{ Hz}$).
- Desde la izquierda se lanzan ráfagas de **solitones armónicos veloces** ($2f_0, 3f_0, 5f_0, 7f_0, 11f_0$).
- Cada vez que una ráfaga armónica alcanza a una ballena subarmónica, no pasa por encima: **frena momentáneamente a la ballena, abre un remolino de fase (el vórtice de Grisey) y reaparece adelantada del otro lado**, dejando una estela de chirps instantáneos proporcionales a la derivada logarítmica $\partial_t \ln \psi_j(t, \tau)$.

### Los cuatro controles de interpretación en `soliton_toda_kdv.py`

| Control | Rango | Acción en el motor de Kay–Moses / Toda | Resultado musical (*Vortex Temporum* × Rejilla) |
| :--- | :--- | :--- | :--- |
| **`tiempo_vortice` ($\tau$)** | $-1.0 \to +1.0$ | Avanza el flujo isoespectral $e^{8\kappa_j^3 \tau}$ en el par de Lax $[L, P]$ | En $\tau < 0$: los solitones rápidos vienen detrás de los lentos (pre-colisión). En $\tau = 0$: **choque múltiple en el centro del compás** (máximo cráter no lineal y máxima transferencia de cresta). En $\tau > 0$: los armónicos ya adelantaron a los subarmónicos con su desfase asintótico $\Delta t_j$. |
| **`acoplamiento_kdv` ($\eta_{\text{nl}}$)** | $0.0 \to 1.0$ | Interpola la matriz de colisión entre $A_{ij} = 1$ (suma lineal sin interacción) y $A_{ij} = \bigl(\frac{\kappa_i - \kappa_j}{\kappa_i + \kappa_j}\bigr)^2$ (solitones KdV exactos) | En $0.0$: los parciales se cruzan linealmente sin desfasarse ni abrir hueco. En $1.0$: se activa la repulsión elástica de solitones, el salto temporal $\Delta t_{ij}$ y el cráter de costura en el cruce. |
| **`escala_temporal_grisey` ($\gamma_{\text{vortex}}$)** | $+1.0 \to -1.0$ | Ajusta la razón de autovalores $\kappa_j / \kappa_0$ entre las tres escalas de *Vortex Temporum* | En $+1.0$: Tiempo de Pájaros (solitones agudos muy estrechos y rápidos). En $0.0$: Tiempo Humano (vórtices de igual anchura que chocan con desfase gigante cuando $\kappa_i \to \kappa_j$). En $-1.0$: Tiempo de Ballenas (dominio de los solitones subarmónicos profundos). |
| **`chirp_de_fase_lax` ($\beta_{\text{lax}}$)** | $0.0 \to 1.0$ | Modula la frecuencia instantánea de cada parcial con el momento local del solitón $\delta f_j(t) \propto \partial_t \ln \psi_j^2(t, \tau)$ y la fase de transmisión de Bargmann | Durante el choque, las frecuencias se curvan brevemente siguiendo el flujo del operador $P$ antes de regresar intactas a su autovalor $\lambda_j = -\kappa_j^2$ (la altura asintótica nunca se desafina). |

---

## 5. Arquitectura en las 6 capas de [TEXTURAS.md](../maquina/TEXTURAS.md)

1. **Cuerpo:** $N = 6$ a $8$ autofunciones vestidas $\psi_j^2(t, \tau)$ del operador de Schrödinger sin reflexión $L = -\partial_t^2 + u(t, \tau)$, repartidas entre subarmónicos ($f_0/3, f_0/2$) y armónicos primos/naturales ($f_0, 2f_0, 3f_0, 5f_0, 7f_0, 11f_0$).
2. **Grano:** Durante el cruce de dos solitones, el término no lineal de advección de KdV ($-6 u u_t$) genera una pendiente abrupta que se traduce en un grano de **modulación de fase cruzada proporcional al determinante menor $M_{ij}$**, imitando el roce de arcos y llaves de viento de [Vortex Temporum](https://fr.wikipedia.org/wiki/Vortex_temporum).
3. **Movimiento:** El ritmo no viene de una cuadrícula rígida, sino de las **trayectorias de colisión en el plano $(t, \tau)$**: aunque lances los solitones a intervalos regulares, sus cruces producen aceleraciones y frenazos elásticos ($\Delta t_i = \frac{1}{\kappa_i}\ln\lvert\frac{\kappa_i+\kappa_j}{\kappa_i-\kappa_j}\rvert$) que vuelven orgánico cualquier ostinato.
4. **Espacio:** El paneo estéreo de cada solitón sigue el **centro de masa vestida** $x_j(\tau) = \int t\,\psi_j^2(t,\tau)\,dt / \int \psi_j^2(t,\tau)\,dt$. En una colisión, cuando el solitón rápido le pasa su cresta al lento (intercambio de identidad de KdV), **las dos voces intercambian su lugar en el campo estéreo sin cruzar bruscamente por el centro**.
5. **Edad:** Además del operador continuo de KdV, un registro paralelo integra la [red de Toda discreta](https://en.wikipedia.org/wiki/Toda_lattice) ($\ddot{q}_n = e^{-(q_n - q_{n-1})} - e^{-(q_{n+1} - q_n)}$) cuyas coordenadas de Flaschka $(a_n, b_n)$ modulan sutilmente el brillo de los armónicos superiores mientras conservan los autovalores de la matriz tridiagonal de Lax $L_{\text{Toda}}$.
6. **Costura:** El **cráter de colisión de KdV** ($q_{\text{col}}(0) = 2(\kappa_1^2 - \kappa_2^2)$) funciona como un *sidechain* físico-matemático sin compresores: justo en el instante en que todas las ondas convergen en el centro del compás, la energía del fondo se hunde por la no-linealidad de Hirota, abriendo una ventana limpia para que el **Piano Espectral de Vortex** y la **Siringua** articulen el centro del torbellino.
