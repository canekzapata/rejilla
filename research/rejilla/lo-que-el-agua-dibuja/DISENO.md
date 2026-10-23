# Lo que el agua dibuja · diseño

**El pedido.** Canek, 21 de octubre de 2026, eligió la tercera de las tres propuestas: blues del Delta con slide × drill × las nubes de glisandos de Xenakis (*Pithoprakta*), sobre unas tierras malas de Traspuesta. El video queda como partitura (`coreografia-video.json`) más `python hazvideo.py`, igual que en las anteriores.

## La lámina

**Tierras malas 67** de Traspuesta: 6 km por lado y 220 m de relieve. Entre las semillas de tierras malas que salen por su propio sorteo (`terreno/buscar.cjs`), es la de la cárcava más larga:
- **la cárcava:** Yucha Ka'nu («río grande» en mixteco, según el glosario de la lámina). Mide 7 699 m y baja de 1 432 a 1 306 m;
- **los afluentes:** le llegan siete;
- **los nombres:** La Cuchilla del Oriente, Yuku Iso, Yuku Kua'a, Yuku Ya'a, Yuku Lulu, El Boquerón, El Portichuelo y El Río Salado.

**La historia** que trae la lámina es la forma de la canción: **arcillas → lluvias raras y violentas → cárcavas → tierras malas**. Se le suma un final en la boca.

## Las ideas que lo organizan

- **El slide toca el terreno.** El perfil de la cárcava (altitud contra distancia) es la partitura de la guitarra:
  - un semitono cada 7 m, con la boca en la tónica;
  - en cada coro de 12 compases el vidrio baja la cárcava de la cabecera a la boca;
  - las notas son el perfil cuantizado a la escala de blues (o a los tonos del acorde en IV y V);
  - entre nota y nota el vidrio se desliza por el perfil mismo;
  - donde llega un afluente, la guitarra toca su riff: cae desde la altura del afluente hasta la de la junta (de 2.5 a 9.7 semitonos).
- **La lluvia es Xenakis.** Cada tormenta es una nube de glisandos, como en *Pithoprakta*:
  - las gotas llegan como proceso de Poisson;
  - cada una es una recta en altura–tiempo cuya velocidad sigue la distribución de Maxwell–Boltzmann;
  - la «temperatura» sube con la tormenta;
  - cada gota cae en un lugar del cuenco y suena a la altura del terreno donde cae, dos octavas arriba.
- **Cada gota erosiona.** La cárcava se ahonda con la ley de potencia de corriente, dz/dt = −K Q^½ S:
  - Q son las gotas que cayeron aguas arriba en ese cuarto de segundo;
  - se resuelve implícita desde la boca, que no se mueve;
  - el nudo (la garganta más empinada) retrocede aguas arriba;
  - el coro que sigue camina la cárcava nueva, así que el slide se hunde tormenta tras tormenta;
  - en cada tormenta la guitarra se queda trémolo donde más excava esa tormenta, y se oye hundirse.
  - **Está exagerado:** miles de años en tres tormentas. La forma es la de la ley.
- **El rayo y el trueno.**
  - Los rayos caen en los cerros con nombre, y quien escucha está en la boca.
  - El trueno llega a distancia/343 s del relámpago (el video lo avisa antes de que se oiga).
  - Su retumbo es la forma del rayo leída por distancias (Few).
- **La crecida.** Lo que llueve llega a la boca unos 5 s después: es el hidrograma, la lluvia convolucionada con una gamma. Con el caudal suben el rugido y los pedregones del arrastre de fondo, ∝ (Q − Q_c)^{3/2} (Meyer-Peter y Müller).
- **El drill.** Blues a 70 por negra = drill a 140: es el mismo pulso. Los hi-hats redoblan con los ceros de zeta (de *Los ceros que tocan a los primos*): los golpes son los picos de −2 Σ cos(γ u). El 808 se desliza de nota en nota.
- **La tónica.** La cárcava como tubo abierto, 343 / (2 · 7 699 m), subida 12 octavas: 91.24 Hz.

## Instrumentos

**Nuevos:**

| | |
|---|---|
| **guitarra de cárcava** (`motor/carcava.js`) | Karplus-Strong cuyo largo cambia en cada muestra siguiendo una curva de altura, porque el vidrio no tiene trastes. Lleva **el chirrido del entorchado**: el vidrio a x m del puente cruza espiras cada 0.4 mm, a |dx/dt| / 0.0004 por segundo, con x = Le (1 − f_abierta/f). Suena por un combo pequeño con slapback. |
| **lluvia de Xenakis** (`sintes11.lluvia_xenakis`) | pizz-glisando (la gota), arco-glisando (el chorro) y col legno (el golpe en la arcilla) |
| **trueno** (`sintes11.trueno`) | canal tortuoso de segmentos de 8 m con ramas; cada segmento es una onda N que llega a r/343 s, lateral y más oscura con la distancia |
| **crecida** (`sintes11.crecida`) | rugido que sigue al hidrograma, más los pedregones |
| **hats de la 808** (`sintes11.hats808`) | seis cuadradas metálicas por un pasabanda agudo |
| **808 que se desliza** (`sintes11.ocho_ocho`) | seno saturado con golpe de tono y portamento |
| **viento seco** (`sintes11.viento`) | ráfagas, más el silbido eólico de los pastos (Strouhal) |

**El resto:**
- **De la biblioteca** (`instrumentos-022eb82aec69`): bombo y tarola de la TR-808 y las palmas de la batería frita.
- **De otros:** los ceros de zeta (`ceros-que-tocan-primos`), y el vocoder y el coro sintético de *Cuento en siete*.
- **El pulgar:** el bajo monótono del Delta, las raíces al aire con la palma. Lo toca la misma guitarra de cárcava.
- **Voces (Sabina):**
  - el blues (lead y, en IV, su doble a la octava);
  - la respuesta en tres voces (unísono, una cuarta abajo y una octava abajo);
  - el rap del drill;
  - los chops («cár-ca-va», «hon-da»);
  - el río. Éste sólo modula el vocoder: **la crecida misma canta «lo que el agua dibuja»** en la boca.

## La forma

| | compases | qué pasa |
|---|---|---|
| I · Arcillas | 14 | El viento. La guitarra sube la cárcava (de la boca a la cabecera) y la baja virgen. «La tierra estaba lisa, nadie la había escrito». |
| tormenta 1 | 4 | Relámpago sobre Yuku Iso (el trueno tarda 14 s). Primera nube de Xenakis; la guitarra se hunde 1.1 semitonos. |
| II · Lluvias raras y violentas | 12 | Entra el drill. «Cada gota que cae se lleva un poco de cerro». Respuesta: «gota por gota». |
| tormenta 2 | 4 | La Cuchilla del Oriente y El Portichuelo. Entra el arco. |
| III · Cárcavas (rap) | 8 | El rap del drill: «de Yuku Iso hasta el Boquerón…». |
| III · Cárcavas | 12 | «Lo que el agua dibuja no lo borra nadie». Respuesta: «más honda». Chops. |
| tormenta 3 | 6 | La grande, *Pithoprakta* entero: tres rayos. La crecida mueve los pedregones; la guitarra se hunde 2 semitonos. |
| IV · Tierras malas | 12 | «Me dicen tierra mala porque aquí no crece nada / pero mírame las venas: cada una es una lluvia». El lead se dobla. |
| V · Yucha Ka'nu | 8 | La boca. El río (el vocoder) canta. «Yucha Ka'nu, río grande: todo lo que baja llega». La guitarra termina en la tónica, porque la boca nunca se mueve. |

## Hydra

Preset nuevo **«cárcava»** (índice 22):
- la lluvia cae como chispas en un búfer;
- el búfer se desliza cuesta abajo por el gradiente del mapa de alturas;
- lo que se junta en las hondonadas se queda, y el agua dibuja sus surcos.

El video también usa «estratos» (las arcillas), «relieve», «erosion», «rgb», «derrame», «marea» y «sombra».
