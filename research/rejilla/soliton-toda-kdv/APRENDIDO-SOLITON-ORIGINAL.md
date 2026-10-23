# rejilla · investigación y lo aprendido con El Solitón Subarmónico de Toda–KdV ($[L, P] = \dot{L}$, 21 de octubre de 2026)

Cuaderno de investigación, sonda y producción real de **El Solitón Subarmónico de Toda–KdV** (`soliton_toda_kdv.py`), construido para cruzar el motor espectral de [Rejilla](../README.md) (`spectrumsynth` de FFmpeg) con la transformada espectral inversa, los [pares de Lax](https://en.wikipedia.org/wiki/Lax_pair) ($[L, P] = \dot{L}$) de la [ecuación de Korteweg–de Vries (KdV)](https://en.wikipedia.org/wiki/Korteweg%E2%80%93De_Vries_equation) y la [red de Toda](https://en.wikipedia.org/wiki/Toda_lattice), y los torbellinos temporales de [Vortex Temporum](https://fr.wikipedia.org/wiki/Vortex_temporum) de [Gérard Grisey](https://en.wikipedia.org/wiki/G%C3%A9rard_Grisey).

Complementa [APRENDIDO.md](../APRENDIDO.md), [ESPECTRAL.md](../aurora/ESPECTRAL.md), [BASES-TEORICAS-INSTRUMENTOS-2026-10-19.md](../BASES-TEORICAS-INSTRUMENTOS-2026-10-19.md), [08-SONAR-LO-VIRTUAL.md](../la-fase-vuelve-distinta/la-fase-vuelve-distinta-s19102691-7fbc97cc5f1c/fuentes/08-SONAR-LO-VIRTUAL.md) y [TEXTURAS.md](../maquina/TEXTURAS.md).

---

## 1. De los potenciales de Bargmann sin reflexión a las filas de `spectrumsynth`

En un operador de Schrödinger unidimensional $L(\tau) = -\partial_t^2 + u(t, \tau)$ con coeficiente de reflexión idénticamente nulo ($R(k) \equiv 0$, *potenciales transparentes de Bargmann–Kay–Moses*), el potencial $q(t, \tau) = -u(t, \tau)$ queda determinado únicamente por sus $N$ autovalores discretos $\lambda_j = -\kappa_j^2$ y sus centros de fase $\theta_j(t, \tau) = \kappa_j(t - t_{j,0} - 4\kappa_j^2 \tau)$:

$$\tau(t, \tau) = \det\bigl(I + M(t, \tau)\bigr), \qquad M_{ij}(t, \tau) = \frac{2\sqrt{\kappa_i \kappa_j}}{\kappa_i + \kappa_j} e^{-(\theta_i + \theta_j)}, \qquad q(t, \tau) = 2\frac{\partial^2}{\partial t^2}\ln \tau(t, \tau)$$

Para convertir este potencial no lineal en un instrumento polifónico donde cada solitón $j$ porta un [armónico](https://en.wikipedia.org/wiki/Harmonic_series_(music)) ($n f_0$) o un [subarmónico](https://en.wikipedia.org/wiki/Undertone_series) ($f_0 / d$), utilizamos la **identidad de traza de Deift–Trubowitz** sobre las autofunciones vestidas $\boldsymbol{\Psi}(t, \tau) = (I + M)^{-1}\mathbf{e}$:

$$q(t, \tau) = \sum_{j=1}^N q_j(t, \tau) = \sum_{j=1}^N 4\kappa_j \,\psi_j^2(t, \tau)$$

---

## 2. Qué midió y qué descubrió la sonda (`ejecutar_sonda()`)

Siguiendo la disciplina de [APRENDIDO-CANCIONES-DE-TERRENO-2026-10-20.md](../APRENDIDO-CANCIONES-DE-TERRENO-2026-10-20.md), probamos el motor matemático y acústico antes de renderizar las piezas de 24 segundos:

| Prueba medida en `ejecutar_sonda()` | Valor medido | Significado físico y musical |
| :--- | :--- | :--- |
| **Isoespectralidad del Par de Lax $\dot{L} = [B, L]$ (Red de Toda, $N=7$)** | **Error máx. $6.06 \times 10^{-10}$** | Aunque los pulsos chocan de forma fuertemente no lineal en las variables de Flaschka $(a_n, b_n)$, los $7$ autovalores $\lambda_k$ permanecen inmóviles: **el choque curva el tiempo pero jamás desafina las alturas asintóticas**. |
| **Identidad de traza $\sum 4\kappa_j\psi_j^2(t) = 2\partial_t^2\ln\det(I+M)$** | **Error máx. $7.88 \times 10^{-13}$** | La descomposición del potencial multisolitón en las $N$ voces vestidas $q_j(t) = 4\kappa_j\psi_j^2(t)$ es algebraicamente exacta hasta precisión de máquina de 64 bits. |
| **Adelanto del solitón armónico rápido ($\kappa_2 = 3.0$)** | **$+0.3662\text{ s}$** (teórico: $+0.3662\text{ s}$) | Tras atravesar al solitón subarmónico lento ($\kappa_1 = 1.5$), el paquete armónico reaparece adelantado exactamente $\frac{1}{\kappa_2}\ln\frac{\kappa_2+\kappa_1}{\kappa_2-\kappa_1} = \frac{\ln 3}{3.0}\text{ s}$. |
| **Retraso del solitón subarmónico lento ($\kappa_1 = 1.5$)** | **$-0.7324\text{ s}$** (teórico: $-0.7324\text{ s}$) | Por conservación del centro de masa ($\kappa_1 \Delta t_1 + \kappa_2 \Delta t_2 = 0$), la «ballena» subarmónica retrocede exactamente el doble de tiempo que lo que avanza el «pájaro» armónico. |
| **Cráter de colisión de 2 solitones ($\kappa_1=1.5, \kappa_2=3.0$)** | **$-4.44\text{ dB}$** ($13.50$ vs $22.50$ lineal) | Si las dos ondas se sumaran linealmente, el pico central sería $2(\kappa_1^2+\kappa_2^2) = 22.50$. En KdV exacto, en el centro de simetría del choque ($\theta_i = \frac{1}{2}\ln\lvert\frac{\kappa_2-\kappa_1}{\kappa_2+\kappa_1}\rvert$), el pico cae a $2(\kappa_2^2-\kappa_1^2) = 13.50$. |
| **Hallazgo de la sonda: Cráter cuasi-resonante de Grisey ($\kappa_1=2.4, \kappa_2=2.6$)** | **$-21.95\text{ dB}$** ($2.00$ vs $25.04$ lineal) | Cuando dos solitones tienen autovalores cercanos (como dos parciales vecinos comprimidos en [Vortex Temporum](https://fr.wikipedia.org/wiki/Vortex_temporum)), la repulsión de autovalores les prohíbe encimarse: **el centro del choque se hunde casi $22\text{ dB}$** y forma un doble lóbulo que transfiere la cresta de una voz a la otra. |
| **SNR en `spectrumsynth` (`gray16le`, $S=32768, H=16384$)** | **$71.75\text{ dB}$** | Reconstrucción limpia de los paquetes solitónicos con fase de transmisión de Bargmann $-2\arctan(\kappa_j/\omega)$. |

---

## 3. Dos trampas que atrapó la sonda y cómo se corrigieron

1. **La ventana de observación del solitón rápido ($\kappa_2 = 3.0$):**
   En la primera corrida de la sonda, el retraso del solitón subarmónico lento dio $-0.7346\text{ s}$ (frente a $-0.7324\text{ s}$ teórico), pero el solitón armónico rápido reportó un valor absurdo ($-3.2985\text{ s}$). Al inspeccionar la traza vimos por qué: como la velocidad de un solitón crece con el cuadrado del autovalor ($v_j = 4\kappa_j^2 = 36.0$ para $\kappa_2 = 3.0$), en $\tau = \pm 0.18$ el solitón rápido ya había recorrido $\pm 6.48\text{ s}$ y se había salido de la ventana de prueba original $[-4, +6]\text{ s}$. Al ampliar la rejilla de medición a $[-12, +12]\text{ s}$, tanto el adelanto del rápido ($+0.3662\text{ s}$) como el retraso del lento ($-0.7324\text{ s}$) clavaron las cuatro cifras decimales de la fórmula de Hirota.
2. **El centro exacto de simetría del cráter ($\theta_i = \frac{1}{4}\ln A_{ij}$):**
   En la parametrización simétrica de Kay–Moses $M_{ij} = \frac{2\sqrt{\kappa_i\kappa_j}}{\kappa_i+\kappa_j}e^{-(\theta_i+\theta_j)}$, la diagonal es $M_{ii} = e^{-2\theta_i}$ y el determinante $2\times 2$ es $\tau = 1 + e^{-2\theta_1} + e^{-2\theta_2} + A_{12} e^{-2(\theta_1+\theta_2)}$. Eso significa que el punto donde los dos solitones están perfectamente superpuestos y el cráter alcanza su mínimo exacto $2(\kappa_2^2-\kappa_1^2)$ no ocurre en $\theta_1 = \theta_2 = 0$ (donde dio $14.05$), sino cuando $e^{2\theta_i} = \sqrt{A_{12}}$, es decir, en $\theta_i = \frac{1}{2}\ln\left\lvert\frac{\kappa_2-\kappa_1}{\kappa_2+\kappa_1}\right\rvert$. Al centrar ahí el choque, el pico medido bajó exactamente a **$13.50 = 2(3.0^2 - 1.5^2)$**.

---

## 4. El descubrimiento musical: Costura por Repulsión de Autovalores en *Vortex Temporum*

En `escena-vortex-toda-kdv-s20261021.wav` / `.m4a` ($-16.2\text{ LUFS}$, LRA $8.3$, pico $-3.3\text{ dBTP}$), pusimos a trabajar juntos los tres elementos del diseño:
- **Las tres escalas de tiempo de [Gérard Grisey](https://en.wikipedia.org/wiki/G%C3%A9rard_Grisey):** las *Ballenas* subarmónicas ($f_0/3 = 54.9\text{ Hz}$ y $f_0/2 = 82.4\text{ Hz}$ bajo Mi3 $= 164.81\text{ Hz}$), el *Tiempo Humano* del **Piano Espectral** (que toca el arpegio helicoidal de Vortex Temporum con inarmonicidad de cuerda real $f_m = m f_p \sqrt{1 + B m^2}$), y los *Pájaros* armónicos ($3f_0, 5f_0, 7f_0$).
- **Groove curvado por colisión de KdV:** cada vez que una nota del arpegio del piano cruza la trayectoria de la ballena subarmónica, su instante de ataque recibe el salto no lineal $\Delta t_i = \frac{1}{\kappa_i}\ln\left\lvert\frac{\kappa_i+\kappa_{\text{sub}}}{\kappa_i-\kappa_{\text{sub}}}\right\rvert$, haciendo que el arpegio se acelere y frene elásticamente como un remolino líquido.
- **Costura sin compresores (el Cráter de Hirota):** en las secciones II ($4.8\text{–}9.6\text{ s}$) y IV ($14.4\text{–}19.2\text{ s}$), todos los solitones convergen hacia $\tau = 0$. En lugar de producir un tutti ensordecedor en el centro del compás, la repulsión de autovalores de Kay–Moses achata las crestas del fondo (hasta $-21.95\text{ dB}$ entre modos vecinos) y abre un cráter transparente donde entra a cantar la **Siringua / Flauta espectral**.

---

## 5. Archivos producidos y verificados (Semilla `20261021`)

- `soliton_toda_kdv.py` — Motor completo (sistema lineal exacto de Kay–Moses $(I+M)\boldsymbol{\Psi}=\mathbf{e}$, suma bilineal de Hirota sobre $2^N$ subconjuntos, integrador RK4 del par de Lax $\dot{L}=[B,L]$ de la red de Toda, clase `PistaRejilla` para `spectrumsynth`, escena *Vortex Temporum* y láminas OKLCh).
- `muestra-soliton-toda-kdv-s20261021.wav` (y `.m4a`) — Muestra aislada de $24.0\text{ s}$ ($-19.2\text{ LUFS}$, LRA $5.4$, $-3.6\text{ dBTP}$, SHA-256 WAV `8529bbfe90e4ad37`). Recorre: (I) Cruce lineal sin interacción ($\eta = 0$), (II) Choque exacto de solitones en $\tau = 0$ con cráter de Hirota ($\eta = 1$), (III) Tiempo de Pájaros con desfases $\Delta t_{ij}$ desplegados, (IV) Tiempo de Ballenas dominado por los subarmónicos $f_0/2, f_0/3$, y (V) Doble vórtice final en la red de Toda–KdV.
- `escena-vortex-toda-kdv-s20261021.wav` (y `.m4a`) — Escena en contexto de $24.0\text{ s}$ ($-16.2\text{ LUFS}$, LRA $8.3$, $-3.3\text{ dBTP}$, SHA-256 WAV `ea589c4fe6a65aa2`) con Solitones de Toda–KdV, Piano Espectral helicoidal y Siringua/Flauta en los cráteres de colisión.
- `01-lax-hirota-y-sonda-s20261021.png` — Lámina 01: las tres etapas del choque ($\tau = -0.08, 0.00, +0.08$), resultados medidos por la sonda y el Mapa de Vórtice $(t, \tau)$ donde se ve el salto de fase de las 4 trayectorias.
- `02-vortice-kdv-y-espectrograma-s20261021.png` — Lámina 02: curvas de control ($\tau(t), \eta(t)$, envolventes de solitones subarmónicos y armónicos), onda estéreo y espectrograma ($35\text{ Hz–}10.5\text{ kHz}$) de la muestra aislada.
- `03-escena-vortex-temporum-costura-s20261021.png` — Lámina 03: trazas del Tiempo Vórtice $\tau(t)$, las Ballenas subarmónicas, el Piano Helicoidal, la Siringua en el cráter y espectrograma de la mezcla completa.
- `proceso-soliton-toda-kdv-s20261021.gif` — GIF en loop de $5.4\text{ s}$ ($3$ cuadros a $1200 \times 720$).
- `receta-soliton-toda-kdv-s20261021.json` — Receta completa con parámetros, partitura, mediciones de la sonda y huellas SHA-256.
