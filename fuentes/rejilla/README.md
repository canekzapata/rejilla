# rejilla · el país suena

Estudio a partir de RASTRUM (el studio 100 de *ffmpeg-music*): la imagen es la
partitura y `spectrumsynth` de ffmpeg la convierte en sonido con una FFT inversa.

**El truco:** con `sample_rate=65536` y 32768 filas, una columna dura exactamente
1 s y la fila k suena exactamente a k Hz. El país que se calcula
(`../../netart/pais-que-se-calcula`) avanza una generación por segundo, así que
una columna = una generación: el compás es el segundo del país.

**La ley (loop 01):** la celda h (1..24) es el armónico h de 110 Hz y se pulsa
h veces por segundo (el Rhythmicon de Theremin y Cowell). Su valor mod 3 es la
octava. Oído izquierdo: tinta ×1. Oído derecho: tinta ×7, la misma ley siete
veces más lenta.

```bash
python rejilla.py     # ventanas del país → partitura 16 bits → ffmpeg → prueba exacta → mezcla
python proceso.py     # PNGs de etapas + GIF
```

- `el-pais-suena-s20261002.m4a` — 98 s, AAC 192k. Medidas en `medidas-s20261002.json`.
- Prueba exacta: lo que sale de ffmpeg contra la irfft de numpy de la misma
  imagen: error relativo 1.7e-7. La rejilla se lee como creemos.
- Medido antes de escribir: en `spectrumsynth` abajo = 0 Hz; la mitad de abajo es
  el canal 0 (izquierdo); amplitud = 2·magnitud; fase = gris·2π − π.

## Loop 02 · una canción escrita en la rejilla

El loop 01 era una idea más que una música. El loop 02 es una canción: neo-soul en La,
96 bpm con swing, 52 compases (2:15) con intro, verso, coro, verso 2, coro, quiebre,
coro final y outro. Hay bajo, bombo, caja, hats, Rhodes, pad, voz y campanas.

- **Síntesis modal escrita en frecuencia.** Cada sonido es una suma de modos
  e^{(-a+2πif)t}. Para cada columna, los coeficientes del pedazo de modo que cae en
  ella tienen fórmula cerrada (serie geométrica) y se escriben directo en la imagen.
  Nunca se sintetiza en el tiempo: ffmpeg es el único que toca. Ninguna nota tiene que
  caer en una fila: la fórmula pinta la fuga exacta.
- **El quiebre es un gesto de la rejilla:** el coro 2 congelado (magnitud media, fase
  al azar fija por fila).
- **Mezcla:** cada pista sale de `spectrumsynth` por separado; sidechain del bombo sobre
  la armonía y el bajo, cuarto con `afir`, EQ de presencia, loudnorm a −14.

```bash
python musica.py            # ~25 min: partitura → ffmpeg por pista → prueba exacta → mezcla
python musica.py --mezcla   # rehacer sólo la mezcla (segundos)
python proceso_cancion.py   # PNGs + GIF
```

Prueba exacta: la fórmula coincide con la DFT directa hasta el redondeo. Lo que
atrapó: con ±2048 filas, cada nota que cruzaba una raya de compás daba un clic de
1 ms (las orillas de columna fugan a todas las filas). Ahora esos pedazos se escriben
en todas las filas y la nota entera decide junta. Residuo medido de punta a punta en el
bajo: 56 dB de SNR; en las rayas, ±4 ms al −40 dB (redondeo a 16 bits de las fugas
lejanas). Pendiente: probar `scale=log` de spectrumsynth para ganar rango ahí.

## Loop 03 · Esquinas

Monk (*Epistrophy*, *Evidence*, *Misterioso*, *Brilliant Corners*) pasado por PC Music,
J-pop, música contemporánea y el Weather Report de los ochenta. Dura 1:42 a 92 bpm.

- **El nudo:** leer la misma imagen al doble de `sample_rate` es el doble de tempo y una
  octava arriba. La duplicación de *Brilliant Corners* y el chipmunk de PC Music son la misma
  operación. La sección Doble es la imagen de la Esquina leída a 2×S, dos vueltas, con un piso
  nuevo a tempo normal.
- **Voces:** 17 sílabas de la TTS de Windows (Sabina es-MX, Zira en-US) afinadas por
  remuestreo y tartamudeadas, que entran a la rejilla con su DFT exacta por columna.
  «sí» y «no» se cantan a la vez a medio tono: un cluster hecho de una contradicción.
- **Acordes que dicen:** en la Pregunta, los armónicos de cada dominante pesan según la
  envolvente de la vocal de «sí» o de «no».
- **Al revés:** en el Misterioso, conjugar la fase de la columna invierte el compás, y la voz
  dice «otra vez» al revés.
- **Contradicciones:** el piano swinguea (62 %) y la batería MIDI va cuadrada; un supersaw
  dulce toca la tríada a un tritono de cada dominante cromático.
- **Weather Report:** metal tipo Prophet doblando el tema, fretless que canta en el
  Misterioso, leño en 3 contra 4 y cencerrito.

```bash
python esquinas.py            # ~15 min
python esquinas.py --mezcla   # sólo la mezcla
python proceso_esquinas.py    # PNGs + GIF
```

## Loop 10 · Lo que no sonó

Canción de 3:06 a 96 BPM: las alternativas descartadas de una melodía forman un coro espectral que pasa al frente. [Idea, letra, audio, PNGs, GIF y verificación](lo-que-no-sono/README.md).

## La mesa se mueve

Cuarteto de 3:05 a 96 BPM. Piano, bajo y percusión se desplazan con motivos de 15, 17 y 16 subdivisiones; sus encuentros producen el patrón del final. [Audio, letra, PNGs, GIF y receta](la-mesa-se-mueve/README.md).

## La salida cambia de lugar

Canción de 3:14 a 112 BPM con verso, pre, coro y puente. Usa los once motores físicos existentes de objetos/ en doce partes: instrumentos que cambian de cuerpo y un gancho pop que vuelve dentro del laberinto. [Audio, letra, PNGs, GIF y receta](la-salida-cambia/README.md).

## Mi boca termina en otra parte

Canción de 3:30 realizada el 16 de octubre: una frase pasa de Sabina a agua, clarinete, piano, trombón y chelo. Campos compuestos desde resonancias medidas de gong y waterphone, recuerdo house y retirada de la cantante. [Audio, boceto, letra, PNGs, GIF y receta](mi-boca-en-otra-parte/README.md).

## Cerquita de ti

Canción pop de 1:35 a 84 BPM: voz, piano, clarinete bajo y chelo al centro, con paredes armónicas y subarmónicas laterales. [Audio, letra, boceto, PNGs y GIF](cerquita-de-ti/README.md). Estudio autónomo para la idea del jardín musical, todavía sin cámara.

## Lo que puede venir

Canción de 2:23 sobre inferencia, hecha el 17 de octubre: voz sintética, respuestas kawaii, electrónica pop, piano y chelo físicos, paredes armónicas/subarmónicas y puente de 7/8. El último gancho adopta una nota de un pájaro anterior. [Audio, letra, voz aislada, PNGs, GIF y verificación](lo-que-puede-venir/README.md).

## La biblioteca de instrumentos (18 de octubre)

Los instrumentos de rejilla viven ahora también en `herramientas/agent/biblioteca-de-instrumentos`, junto con los de consola, meleeviewer, el jardín y los demás. Son 104 que suenan; 38 son de rejilla, capturados con una «pista espía» y comprobados contra el original a −99 dB o menos. Rejilla toma de la biblioteca con `tomar.py`, fijando una versión por huella. Primera pieza: arpa de boca, berimbau, saron, balafón y marimba [suenan juntos](biblioteca/suenan-juntos-7710e6008710/README.md). Qué se hizo, qué vía usar y qué se aprendió: [biblioteca/README.md](biblioteca/README.md).

## Catálogo de agua que habla (18 de octubre)

Pieza experimental de 1:42: percusiones que hablan, pájaros y agua, «Messiaen pero hyperpop». Usa los instrumentos nuevos de la biblioteca (marimba, mbira, saron, gendér, gyil, berimbau, teponaztli, arpa de boca, 808, dùndún, aves y agua), y a Siringua como la voz del agua. Lleva modo 2, ritmos no retrogradables, valores añadidos y canon por aumentación, con 808, sidechain, voz subida y cortada y glitch. [Audio, partitura, proceso y mediciones](catalogo-agua-que-habla/README.md).

## Los WAV están comprimidos sin pérdida (18 de octubre)

Rejilla pesaba 24 GB: 21.3 GB eran WAV de trabajo (stems, mezclas de prueba, renders de spectrumsynth), casi todos en float de 32 bits. Por pedido de Canek, después de que copió la carpeta a un disco externo, `comprimir_wav.py` los pasó a formatos sin pérdida:

- **enteros (16/24 bits) → FLAC:** 685 archivos, 1.46 → 0.50 GB;
- **float (32 bits) → WavPack `.wv`:** 1 711 archivos, 20.08 → 6.82 GB. FLAC no guarda float sin redondear; WavPack sí.

Antes de borrar cada WAV, el original y el comprimido se decodificaron al mismo formato crudo y su huella SHA-256 coincidió: **2 391 de 2 391 idénticos**. Se quedó un WAV vacío (46 bytes, un TTS fallido). La carpeta quedó en 9.1 GB. El registro, archivo por archivo, está en `compresion-wav.jsonl`.

**Los scripts viejos buscan `.wav`.** Para rehacer una mezcla, primero se regresa a WAV:

```bash
python comprimir_wav.py --restaurar render/aurora/x.wv      # vuelve el WAV idéntico (pcm_f32le, s16le o s24le según era)
ffmpeg -i x.wv -c:a pcm_f32le x.wav                          # o a mano
```

`.wv` y `.flac` están en `.gitignore`, como lo estaban los `.wav`.


## La garganta sale bailando

Instrumental de 2:56 del 18 de octubre: tres vocoders sin letra, desarrollo imitativo, gabber/breaks, chelo que se vuelve house, spray electrónico y coda contrapuntística sobre dembow. [Audio, prueba de bocas, PNGs, GIF y receta](la-garganta-sale-bailando/README.md).

## Otra vez hasta romper

Instrumental de 2:44 del 18 de octubre: dembow → gabber → arco melódico y breaks, ciclos de repetición que se deforman, encuentros que excitan los parciales de una nota y cierre en un golpe seco. [Audio vigente, partitura, referencias, PNGs y GIF](otra-vez-hasta-romper/README.md).

- 19 octubre 2026: [El pulso pierde la casa](el-pulso-pierde-la-casa/README.md), 3:22 de dembow, canto, retiradas, coro, gabber y dos falsos finales. Mezcla con percusión al frente.
- 19 octubre 2026: [La fase vuelve distinta](la-fase-vuelve-distinta/README.md), canción instrumental de 3:08: un gancho pasa por familias armónicas y subarmónicas, espejo sin batería, retorno en 7/8, danza y coda con cortes. GIF, PNGs, boceto y mezcla v2.
- 19 octubre 2026: [La boca enciende el cobre](la-boca-enciende-el-cobre/README.md), 3:24 con un lead de ocho compases en varias capas, dembow, coro vocalizado, cámara de cuerda y aire, solos de metal/sax/sinte y retorno que aprende del solo. Nuevos Rhodes modal y resonador vocal de cobre; instrumentos físicos existentes, escucha de lead, boceto, PNGs y GIF.
- 19 octubre 2026: [Otro arriba](otro-arriba/README.md), canción de 3:26 con letra aprobada a partir de poemas de Canek: voz PSOLA al frente, dembow, respuestas de metal, cuatro vocoders y una vocal del propio canto que produce la armonía del puente. Audio, voz aislada, boceto, letra sincronizada, PNGs y GIF.
- 19–20 octubre 2026: [Instrumentos de tres tiempos](instrumentos-de-tres-tiempos/README.md), doce prototipos offline: seis cuerpos imaginados y seis electrónicos sci-fi. Muestras individuales, atlas de 4:55 y escena La boca abre una estación de 1:24; motores reutilizables, controles, partitura/espectrograma, PNGs y GIF de 7.5 s.
