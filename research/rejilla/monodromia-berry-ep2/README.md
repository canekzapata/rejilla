# El Monodromio No-Hermítico de Berry–EP2

Llegó el 21 de octubre de 2026 en `argon music3d/`, hecho fuera de esta máquina por otra IA. Es de la misma tanda que el [Astrolabio](../astrolabio-metaplectico/README.md), la [Criba de Möbius–Grisey](../criba-mobius-grisey/README.md) y el [Solitón de Toda–KdV](../soliton-toda-kdv/README.md).

**Qué es.** Un par de modos no hermítico, con frecuencias Ω±(z) = ω₀ − iγ₀ ± ½√(z² + 4κ²). Al dar una vuelta alrededor del punto excepcional (EP2), la raíz cuadrada cambia de hoja de Riemann y **los dos modos se intercambian**: el armónico n·f₀ llega a f₀/n, y vuelve en la segunda vuelta (4π), con signo −1 de la fase de Berry.

**Cómo se usa.**
- **El homenaje a Haas:** la escena es una escalera a lo *in vain* de Haas.
- **El colapso:** en el punto excepcional los modos se juntan en un bloque de Jordan, que crece de forma secular (t·e^(−at), con pico en 1/a).
- **El factor de Petermann:** se usa para abrir huecos.

## Archivos

| | |
|---|---|
| `monodromia_berry_ep2.py` | Motor, sonda, muestra, escena y láminas. Se corre con `python monodromia_berry_ep2.py`; tarda unos 26 s. |
| `APRENDIDO-MONODROMIA-ORIGINAL.md` | El cuaderno que trajo, tal cual, salvo los 7 enlaces a Drive, que ahora apuntan a los archivos de aquí. |
| `original-s20261021/` | Su receta (en git) y sus dos wav (en disco, fuera de git). |
| `monodromia-berry-ep2-s20261021-7722cbe8fb3d/` | La corrida aquí: muestra, escena, 3 láminas, GIF y receta. |
| **`3d-in-vain/`** | **La pieza de net art 3D:** la superficie de Riemann de √(z − z_EP), con 12 esferas. Al rodear el pilar de Jordan, n·f₀ y f₀/n se permutan. Es three.js con Web Audio, autónoma. Se le agregaron los metadatos de AGENTS.md, `og.png` y `favicon.png`, sacados de la propia escena con `../og3d.cjs`; el canonical queda pendiente (TODO). |

**Cambios al código:** dos, nada del sonido.
- Escribía en `/working_dir/...` (su sandbox). Ahora crea una carpeta exclusiva con hash.
- Se agregó Consolas como fuente.

## Lo que se probó aquí (21 oct 2026)

**Reproduce.**
- La muestra y la escena quedan a −240 y −230 dB de sus wav originales: es redondeo.
- La sonda da lo mismo, salvo 1.57e-14 → 1.58e-14.
- Mide lo mismo: −19.3 LUFS, LRA 7.6, −3.1 dBTP.
- Su sonda reporta: la permutación es exacta en 2π, la fase de Berry da −1 en 4π, spectrumsynth da 66.3 dB de SNR y el pico secular cae a 0.2485 s (teórico 0.25).

**Lo que falta.** No se ha medido **en el motor que suena**. En los tres instrumentos anteriores de argon, eso fue lo que encontró problemas. Queda pendiente.

**Sin escucha humana.**
