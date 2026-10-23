# El Astrolabio Metapléctico

Llegó el 20 de octubre de 2026, hecho fuera de esta máquina por otra IA. Lo hizo en su propio sandbox, con la copia de rejilla compartida por Drive. Venía metido en `biblioteca/instrumentos-77a5750fe244/`, pero esa carpeta es una toma fijada por huella (`manifiesto.json`) y no debe cambiar. Por eso tiene su propia carpeta, como `instrumentos-de-tres-tiempos/`.

Es un instrumento de rejilla que gira acordes en el plano tiempo × frecuencia con los tres generadores de Mp₂(ℝ):
- **el giro fraccionario θ:** en θ = π/2 el acorde se acuesta y se vuelve ritmo;
- **la dilatación a;**
- **la cizalla de chirp c.**

Cada nota suena en dos hojas: una **testigo** quieta y una **viajera** que gira. Las dos se suman.

Es pariente de la [propuesta del grupo metapléctico](../PROPUESTA-GRUPO-METAPLECTICO.md) («Telar de fase»), que salió el mismo día.

## Archivos

| | |
|---|---|
| `astrolabio_metaplectico.py` | Motor, sonda, muestras, escena y láminas. Se corre con `python astrolabio_metaplectico.py`; tarda unos 30 s. |
| `APRENDIDO-ASTROLABIO-ORIGINAL.md` | El cuaderno que trajo, tal cual, salvo los enlaces: venían envueltos en búsquedas de Google hacia Drive y ahora apuntan a los archivos de aquí. Su teoría de la «Hoja −1» y del «Mp₄» la corrige este README. |
| `receta-astrolabio-original-s20261020.json` | La receta de la corrida original. Llegó a la toma un rato después. |
| `astrolabio-metaplectico-s20261020-e2c304abc1a9/` | La primera corrida aquí, con el código tal como llegó. |
| **`astrolabio-metaplectico-s20261020-fd6bc21e67a3/`** | **La vigente, ya arreglada.** Incluye: dos muestras (hermite e impares), la escena, 4 láminas, el GIF y la receta. Los m4a están en git y los wav fuera. |

## El arreglo (20 oct 2026, segunda corrida)

### 1. La perilla `reparto`

Decide cómo gira la fase de cada armónico de la viajera.

**El problema.** El código original daba fase −θ/2 a los armónicos 1, 3 y 5, y fase −θ a los 2, 4 y 6. Así sólo los impares cambiaban de signo en 2π: quedaba una octava hueca. Pero eso no lo obliga el grupo metapléctico. En la representación del oscilador, el modo m de Hermite gira con e^{−i(m+½)θ}, y en 2π **todos** los modos llevan −1.

**Los tres repartos:**

| `reparto` | ley | en 2π (fundamental / total) | en 4π |
|---|---|---|---|
| **`hermite`** (por omisión) | el armónico m gira como el modo m de Hermite: e^{−i(m+½)θ} | −211 / **−252 dB: se borra** | 0.00 dB |
| `global` | todos los armónicos con −θ/2: sólo el signo del recubrimiento | −211 / −252 dB | 0.00 dB |
| `impares` (el original) | impares −θ/2, pares −θ | −29 / −7.2 dB: **octava hueca** | 0.00 dB |

**Hermite contra global.** Medí que hermite y global suenan casi igual. En π/2 el centroide es 762 Hz con hermite y 764 Hz con global. La razón: a mitad de la vuelta la viajera está en otro lugar del plano y no se cruza con su testigo, así que la fase de cada armónico sólo cuenta donde coinciden (en los múltiplos de 2π). Lo que pasa de verdad es que la nota se borra en 2π y vuelve en 4π. Hermite queda por omisión porque es la ley del grupo.

**Impares** es la otra voz: un filtro de armónicos impares, como un tubo cerrado al revés. No es «el signo del recubrimiento», pero suena bien y la escena lo usa como halo para la voz.

Se elige en la partitura (`'reparto': 'hermite'`), por evento o como argumento de `escribir_acorde_astrolabio_en_pista(..., reparto=)`.

### 2. La rotación bajo↔boca usa de verdad los valores rotados

Antes se calculaban `q_rot` y `p_rot` sólo para medir la norma y se tiraban, y la boca se modulaba con un sidechain. Ahora el formante F2 de la boca sigue a `p_rot = sin φ · q_bajo + cos φ · p_vocal`, y el bajo recibe la vocal por la otra componente (los ataques se corren hasta 95 ms).

Medido: la correlación de F2 con la envolvente del bajo es **+0.09 en φ = 0** (la boca dice sus vocales) y **+1.00 en φ = π/2** (la boca canta el pulso del bajo).

Sigue sin ser un Mp₄. Para que la rotación fuera simpléctica en 4 dimensiones, al girar q_bajo hacia p_boca habría que girar también q_boca hacia p_bajo. Por eso se llama «rotación de controles».

### 3. Nombres honestos

- «Mp₄» ahora se llama rotación bajo↔boca.
- La «Boca de tres tiempos» ahora se llama boca de formantes: es propia del archivo y no la de Codex.
- La escena se llama `escena-astrolabio-bajo-boca`.

## Comprobado en la corrida vigente (fd6bc21e67a3)

- **spectrumsynth contra la suma en el tiempo:** SNR 69.69 dB, igual que antes.
- **La muestra `impares`** sale idéntica bit a bit a la del original: SHA del wav `337fc67966e9ae3e`. El arreglo no cambió el sonido viejo.
- **Volumen:**
  - la muestra hermite: −18.6 LUFS, y su sección IV (13.5–18.5 s) queda en silencio;
  - la escena: −16.7 LUFS, LRA 7.8.
- **Las 4 láminas** se revisaron a ojo y no tienen textos encimados. El GIF dura 7.2 s, son 4 cuadros y pesa 0.5 MB.
- **La primera corrida** (e2c304abc1a9) tenía un problema que quedó documentado: la escena salía con otro SHA que la original (`76859d06…` contra `3466124326…`) aunque medía igual. Pasa algo dependiente de la plataforma en la boca o en los filtros. No se buscó.

## Cómo tomarlo en una canción

- **Para escribirlo en la rejilla:** `escribir_acorde_astrolabio_en_pista(P, t_c, midi, semitonos, theta, comp_a, chirp_c, mezcla, reparto=)`. Escribe en la `PistaRejilla` del archivo, por serie geométrica cerrada, igual que `Pista.modo`/`Pista.seg`.
- **Para rendirlo en el tiempo:** `render_astrolabio_temporal(partitura, dur)`.
- **Una idea para canción:** que un coro vuelva en 2π con `hermite` y desaparezca, o con `impares` y quede hueco, para que la voz cante adentro.

**Sin escucha humana del arreglo.**

## La pieza 3D

[`3d-pista-de-moebius/`](3d-pista-de-moebius/index.html) es net art pop 3D.
- **Qué hace:** siete esferas cromadas recorren el recubrimiento doble sobre una pista de Möbius de 720°. A 360° el acorde se vuelve sombra hueca, y a 720° regresa.
- **Cómo está hecha:** three.js con Web Audio, autónoma. Llegó el 21 de octubre en `argon music3d/`.
- **Lo agregado:** los metadatos de AGENTS.md, `og.png` y `favicon.png`, sacados de la propia escena con `../og3d.cjs`. El canonical queda pendiente (TODO).
- **Ojo:** la pieza usa el reparto original de impares, el de la octava hueca, no el de hermite.
