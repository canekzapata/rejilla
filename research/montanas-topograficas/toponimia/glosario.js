// toponimia/glosario.js — los nombres de lugar de Traspuesta.
// Fuentes: Moliner (Diccionario de uso del español, el de consola), catálogo de términos
// genéricos del INEGI (Diccionario de datos topográficos 1:50 000, 2020, anexo B) y las
// clases de rasgos del USGS/GNIS para el inglés. Cada genérico tiene su regla: sólo se usa
// si el terreno cumple lo que la palabra dice. Las definiciones van resumidas.
(function (G) {
  const MT = G.MT;
  // g: género (para concordar el complemento). r: regla, una función de las medidas del rasgo.
  // en: clase en inglés (lo que el lector de inglés ve como glosa).
  MT.GLOSARIO = {
    cumbre: [ // la cima principal de la lámina o de una montaña
      { w: 'cerro', g: 'm', en: 'hill', src: 'INEGI: elevación aislada, brusca, menor que el monte', r: (m) => m.aislado && m.altoRel < 0.7 },
      { w: 'cueto', g: 'm', en: 'conical hill', src: 'Moliner: cerro aislado de forma cónica', r: (m) => m.aislado && m.conico },
      { w: 'picacho', g: 'm', en: 'sharp peak', src: 'Moliner/INEGI: punta aguda de un monte', r: (m) => m.agudo },
      { w: 'pico', g: 'm', en: 'peak', src: 'INEGI: punta culminante de una montaña o sierra', r: (m) => m.principal && !m.romo },
      { w: 'mamelón', g: 'm', en: 'rounded knoll', src: 'Moliner: colina o cumbre redondeada', r: (m) => m.romo },
      { w: 'mogote', g: 'm', en: 'blunt cone', src: 'Moliner: montículo cónico de punta roma', r: (m) => m.conico && m.romo },
      { w: 'teso', g: 'm', en: 'summit', src: 'Moliner: cima de un monte', r: (m) => m.plano },
      { w: 'otero', g: 'm', en: 'lone hill', src: 'Moliner: montecillo aislado en un llano', r: (m) => m.aislado && m.llanoAlrededor },
      { w: 'cabezo', g: 'm', en: 'knob', src: 'Moliner: monte pequeño; roca redondeada que sobresale', r: (m) => m.chico && m.romo },
      { w: 'alcor', g: 'm', en: 'low hill', src: 'Moliner: monte pequeño', r: (m) => m.chico },
      { w: 'cerrajón', g: 'm', en: 'steep crag', src: 'Moliner: cerro alto y escarpado', r: (m) => m.escarpado && !m.chico },
      { w: 'cotera', g: 'f', en: 'steep hillock', src: 'Moliner: cerro pequeño de pendiente rápida', r: (m) => m.escarpado && m.chico },
      { w: 'peña', g: 'f', en: 'crag', src: 'INEGI: afloramiento rocoso escarpado', r: (m) => m.escarpado },
      { w: 'loma', g: 'f', en: 'ridge', src: 'Moliner/INEGI: elevación pequeña y alargada, de laderas suaves', r: (m) => m.alargado && !m.escarpado },
      { w: 'cuchilla', g: 'f', en: 'knife ridge', src: 'INEGI: elevación alargada y angosta', r: (m) => m.alargado && m.agudo },
      { w: 'monte', g: 'm', en: 'mountain', src: 'Moliner: elevación natural grande del terreno', r: (m) => m.principal && m.altoRel >= 0.7 },
      { w: 'mesa', g: 'f', en: 'mesa', src: 'INEGI: elevación de cima plana y laderas abruptas', r: (m) => m.plano && m.escarpado },
      { w: 'aguja', g: 'f', en: 'needle', src: 'Moliner: pico o peñasco muy agudo', r: (m) => m.agudo && m.escarpado },
      // paradójicos pero ciertos: LA ISLA, un cerro que el río rodea en la llanura
      { w: 'isla', g: 'f', en: 'the island: a hill the river wraps around', src: 'uso mexicano: cerro aislado por el río o la ciénega', r: (m) => m.arq === 'meandros' && m.cercaRio },
    ],
    paso: [ // collado: el punto más bajo entre dos cimas
      { w: 'collado', g: 'm', en: 'saddle', src: 'Moliner: depresión suave entre dos alturas', r: () => true },
      { w: 'portichuelo', g: 'm', en: 'foothill pass', src: 'Moliner: paso en las estribaciones', r: (m) => m.bajo },
      { w: 'gollizo', g: 'm', en: 'narrow gap', src: 'Moliner: paso estrecho entre montañas', r: (m) => m.estrecho },
      { w: 'puerto', g: 'm', en: 'pass', src: 'INEGI: la porción más baja para cruzar una cadena', r: (m) => m.enCadena },
      { w: 'boquerón', g: 'm', en: 'gap', src: 'INEGI: paso corto o abertura grande entre dos montañas', r: (m) => m.ancho },
      { w: 'abra', g: 'f', en: 'open gap', src: 'Moliner: abertura amplia entre dos montañas', r: (m) => m.ancho },
    ],
    hondonada: [ // cráter, dolina, sumidero, fondo cerrado
      { w: 'torca', g: 'f', en: 'sinkhole', src: 'Moliner: hondonada circular de bordes escarpados', r: (m) => m.circular && m.escarpado },
      { w: 'hoya', g: 'f', en: 'hollow', src: 'INEGI: concavidad generalmente circular', r: (m) => m.circular },
      { w: 'hoyada', g: 'f', en: 'hollow', src: 'Moliner: hondonada', r: () => true },
      // paradójico pero cierto: la laguna que casi nunca tiene agua (Laguna Seca, en todo el norte de México)
      { w: 'laguna seca', g: 'f', en: 'dry lake: a basin that fills only in the rains', src: 'uso mexicano: hondonada sin agua en tierra seca', r: (m) => ['dunas', 'badlands', 'testigos', 'inselbergs', 'canon', 'impactos'].includes(m.arq) },
      { w: 'rehoyo', g: 'm', en: 'deep hollow', src: 'Moliner: hoyo hondo', r: (m) => m.hondo },
    ],
    valle: [ // el río principal y su valle
      { w: 'vaguada', g: 'f', en: 'valley floor', src: 'Moliner: la parte más honda de un valle', r: () => true },
      { w: 'cañada', g: 'f', en: 'ravine', src: 'INEGI: espacio profundo entre dos alturas, valle en V', r: (m) => m.encajado },
      { w: 'barranca', g: 'f', en: 'gorge', src: 'INEGI: depresión estrecha de laderas abruptas con corriente', r: (m) => m.encajado && m.empinado },
      { w: 'hocino', g: 'm', en: 'river gorge', src: 'Moliner: paso de un río entre dos montañas', r: (m) => m.entreMontes },
      { w: 'quebrada', g: 'f', en: 'creek gorge', src: 'Moliner/INEGI: paso estrecho entre montañas con agua', r: (m) => m.encajado },
    ],
    llano: [ // lo bajo y plano de la lámina
      { w: 'nava', g: 'f', en: 'marshy hollow', src: 'Moliner: terreno bajo, a veces pantanoso, entre montañas', r: (m) => m.entreMontes && m.agua },
      { w: 'vega', g: 'f', en: 'river flat', src: 'Moliner: terreno bajo y llano atravesado por un río', r: (m) => m.rio },
      { w: 'llano', g: 'm', en: 'flat', src: 'INEGI: terreno igual y dilatado', r: () => true },
    ],
    lago: [
      { w: 'laguna', g: 'f', en: 'lake', src: 'INEGI', r: () => true },
      { w: 'balsa', g: 'f', en: 'pond', src: 'Moliner: agua detenida en una depresión del terreno', r: (m) => m.chico },
      { w: 'ojo de agua', g: 'm', en: 'spring pool', src: 'uso mexicano: donde brota el agua', r: (m) => m.nacimiento },
    ],
    aguja: [
      { w: 'tormo', g: 'm', en: 'rock pillar', src: 'Moliner: peñasco aislado en forma de mojón', r: () => true },
      { w: 'farallón', g: 'm', en: 'sea stack', src: 'Moliner: roca alta cortada a pico en el mar', r: (m) => m.enMar },
    ],
    colada: [
      { w: 'malpaís', g: 'm', en: 'lava flow', src: 'Moliner/INEGI: terreno invadido por lava solidificada', r: () => true },
    ],
  };

  // Nombres en náhuatl: sólo los que registra el Diccionario de geografía náhuatl de César
  // Macazaga Ordoño (1983, en consola/extras), con su sentido; nada se compone por cuenta
  // propia. Van como en los mapas mexicanos: el genérico en español + el nombre náhuatl
  // (LAGUNA TENEXAPAN), o solos cuando el nombre ya dice "cerro" (CENTZONTEPEC).
  MT.NAHUATL = {
    cumbre: [
      { w: 'Centzontepec', solo: true, es: 'lugar de innumerables cerros; serranía', en: 'place of countless hills', r: (m) => m.principal && m.nCimas >= 3 },
      { w: 'Iztactépetl', solo: true, es: 'sierra blanca', en: 'white mountain', r: (m) => m.principal && m.altM > 4700 }, // blanca de nieve (la caliza ya va en maya)
      { w: 'Atlixco', pre: 'cerro', es: 'sobre el agua', en: 'above the water', r: (m) => m.enIsla && !m.principal },
      // cosecha del Macazaga (loop 34): topónimos registrados con su sentido (Molina, Sahagún,
      // Vetancurt…); fuera los sagrados y míticos (Popocatépetl, Citlaltépetl, Coatépec,
      // Tláloc, Chicomóztoc, Aztlan, Tepeyácac) y las ciudades grandes
      { w: 'Cuauhtépetl', solo: true, es: 'cerro de árboles', en: 'hill of trees', r: (m) => !m.escarpado && m.altM < 3500 && !m.seco },
      { w: 'Yahualiuhcan', solo: true, es: 'donde el cerro redondo', en: 'where the round hill is', r: (m) => m.conico && !m.agudo },
      { w: 'Cuatlapanqui', solo: true, es: 'cabeza partida: cerro partido por arriba', en: 'split head', r: (m) => m.partido },
      { w: 'Tetzontépec', solo: true, es: 'cerro del tezontle', en: 'hill of scoria', r: (m) => m.roca === 'volcanica' },
      { w: 'Itztépec', solo: true, es: 'lugar de la obsidiana', en: 'place of obsidian', r: (m) => m.roca === 'volcanica' && m.agudo },
      { w: 'Yoaltépec', solo: true, es: 'en el cerro de la noche', en: 'hill of the night', r: (m) => m.roca === 'volcanica' && !m.chico },
      { w: 'Mixtitlan', solo: true, es: 'entre las nubes', en: 'among the clouds', r: (m) => m.altM > 4000 },
      { w: 'Quiahuitépec', solo: true, es: 'en el cerro de la lluvia', en: 'hill of the rain', r: (m) => m.altM > 2500 && !m.seco && m.nLagos >= 1 },
      { w: 'Oztotépec', solo: true, es: 'cerro de las cuevas', en: 'hill of the caves', r: (m) => m.escarpado },
      { w: 'Tehuitzco', solo: true, es: 'donde las piedras agudas', en: 'where the sharp stones are', r: (m) => m.agudo },
      { w: 'Tizatépec', solo: true, es: 'cerro de la tiza', en: 'hill of chalk', r: (m) => m.roca === 'arenisca' || m.roca === 'caliza' },
      { w: 'Tlamapan', solo: true, es: 'en las faldas de la sierra', en: 'on the skirts of the range', r: (m) => !m.principal && m.alargado },
      { w: 'Xalticpac', solo: true, es: 'en lo alto de la arena', en: 'atop the sand', r: (m) => m.arq === 'dunas' },
      // animales (Macazaga, por sus raíces): conejo, mapache, tecolote, iguana, serpiente
      { w: 'Tochtépec', solo: true, es: 'en el cerro del conejo (R. tochtli, tépetl)', en: 'hill of the rabbit', r: (m) => m.chico || m.romo },
      { w: 'Mapachtépec', solo: true, es: 'en el cerro del mapache (R. mapachtli, tépetl)', en: 'hill of the raccoon', r: (m) => !m.seco && m.altM < 2800 },
      { w: 'Tecolotlan', solo: true, es: 'lugar de tecolotes (R. tecólotl, tlan)', en: 'place of owls', r: (m) => m.romo && !m.chico && !m.principal },
      { w: 'Cuauhcuetzpaltitlan', solo: true, es: 'tierra de iguanas', en: 'land of iguanas', r: (m) => m.costa && m.altM < 600 },
      { w: 'Coaxalpan', solo: true, es: 'en el arenal de las serpientes', en: 'in the sands of the serpents', r: (m) => m.arq === 'dunas' },
    ],
    paso: [
      { w: 'Tepetózcatl', solo: true, es: 'collado o garganta de monte (Molina)', en: 'saddle, throat of the mountain', r: () => true },
      { w: 'Tepetl Itzónyoc', solo: true, es: 'puerto de monte y sierra (Molina)', en: 'mountain pass', r: (m) => m.enCadena },
    ],
    hondonada: [
      { w: 'Oztoyahualco', solo: true, es: 'en la cueva redonda', en: 'at the round cave', r: (m) => m.circular },
      { w: 'Oztotzinco', solo: true, es: 'el lugarcito de la cueva', en: 'little place of the cave', r: (m) => m.chico },
      { w: 'Oztopolco', solo: true, es: 'dentro de la gran cueva', en: 'inside the great cave', r: (m) => !m.chico && m.hondo },
      { w: 'Oztóyoc', solo: true, es: 'en el lugar lleno de cuevas', en: 'in the cavernous place', r: (m) => m.escarpado },
      { w: 'Atlacomulco', solo: true, es: 'en el pozo no muy profundo', en: 'at the shallow well', r: (m) => m.chico && !m.hondo },
      { w: 'Nextlalpan', solo: true, es: 'en el suelo de cenizas', en: 'on the ground of ashes', r: (m) => m.roca === 'volcanica' },
      { w: 'Nextícpac', solo: true, es: 'sobre las cenizas', en: 'upon the ashes', r: (m) => m.roca === 'volcanica' && m.chico },
    ],
    lago: [
      { w: 'Atezcapan', pre: 'laguna', es: 'en el agua del charco', en: 'at the pond water', r: (m) => m.chico },
      { w: 'Tenexapan', pre: 'laguna', es: 'en el agua de cal', en: 'at the lime water', r: (m) => m.arq === 'mesa' }, // la mesa de caliza fuera de Yucatán
      { w: 'Tequixquiapan', pre: 'laguna', es: 'salitral', en: 'saltpeter flat', r: (m) => m.arq === 'dunas' || m.arq === 'badlands' },
      { w: 'Xalatzinco', pre: 'laguna', es: 'donde el agua brota a través de la arena', en: 'where water springs through sand', r: (m) => ['dunas', 'costa', 'meandros'].includes(m.arq) },
      { w: 'Tepetitlan', pre: 'laguna', es: 'junto al monte', en: 'beside the mountain', r: (m) => m.juntoCumbre },
      { w: 'Atlxoxouhcan', pre: 'laguna', es: 'agua verde', en: 'green water', r: (m) => !m.chico },
      { w: 'Ayahualolco', solo: true, es: 'en derredor del agua', en: 'around the water', r: (m) => !m.chico },
      { w: 'Atotonilco', solo: true, es: 'agua que mana como a hervores', en: 'water that wells up boiling', r: (m) => m.roca === 'volcanica' },
      { w: 'Nexapan', solo: true, es: 'en el agua de ceniza: fuente que nace de un volcán', en: 'at the ash water', r: (m) => m.roca === 'volcanica' && m.chico },
      { w: 'Atézcac', solo: true, es: 'en el charco de agua', en: 'at the pool', r: (m) => m.chico },
      { w: 'Ayotzinco', solo: true, es: 'en el principio de los manantiales', en: 'where the springs begin', r: (m) => m.chico },
      { w: 'Tizapan', solo: true, es: 'lugar de las aguas blancas', en: 'place of white waters', r: (m) => m.roca === 'caliza' || m.roca === 'arenisca' },
      { w: 'Mazaapan', solo: true, es: 'agua de venados', en: 'water of the deer', r: () => true },
      { w: 'Pinahuizapan', solo: true, es: 'agua avergonzada: no se ve con tanto árbol', en: 'bashful water', r: (m) => !m.juntoCumbre },
      { w: 'Chiauhtla', solo: true, es: 'cenagoso: donde hay ciénegas', en: 'marshy place', r: (m) => ['meandros', 'costa'].includes(m.arq) },
      { w: 'Coyotépec', pre: 'laguna', es: 'laguna de aguas llovedizas (Vetancurt); R. cóyotl, tépetl: cerro del coyote', en: 'lake by the hill of the coyote', r: (m) => m.juntoCumbre },
      { w: 'Ayotlan', solo: true, es: 'junto a las tortugas (R. áyotl, tlan)', en: 'beside the turtles', r: (m) => ['meandros', 'costa'].includes(m.arq) },
    ],
    valle: [
      { w: 'Teloloapan', pre: 'río', es: 'en el río de los guijarros', en: 'at the river of pebbles', r: (m) => m.glaciar },
      { w: 'Xalatlauhco', pre: 'barranca', es: 'barranca de arena', en: 'sand ravine', r: (m) => m.encajado && m.roca === 'arenisca' },
      { w: 'Ameyalco', pre: 'río', es: 'manantial de agua', en: 'spring', r: (m) => m.nace },
      { w: 'Atoyac', solo: true, es: 'en el río grande', en: 'at the great river', r: (m) => !m.encajado },
      { w: 'Teapan', pre: 'río', es: 'río de piedra o pedregoso', en: 'stony river', r: (m) => m.encajado },
      { w: 'Michatóyatl', solo: true, es: 'río de pescado', en: 'river of fish', r: (m) => !m.encajado },
      { w: 'Totólatl', solo: true, es: 'río donde beben las gallinas silvestres', en: 'river where wild turkeys drink', r: () => true },
      { w: 'Quetzálatl', solo: true, es: 'agua como pluma verde rica: muy clara', en: 'water like a quetzal feather', r: (m) => !m.encajado && m.roca !== 'arenisca' },
      { w: 'Atlihuechía', solo: true, es: 'agua que se despeña', en: 'water that tumbles down', r: (m) => m.empinado },
      { w: 'Axictlan', solo: true, es: 'junto al remolino de agua que corre', en: 'by the whirlpool', r: (m) => m.encajado },
      { w: 'Atoyatenco', solo: true, es: 'en la ribera del río', en: 'on the riverbank', r: (m) => !m.encajado },
      { w: 'Tlalatlauhtli', solo: true, es: 'barranca alta (Molina)', en: 'high ravine', r: (m) => m.encajado && m.empinado },
      { w: 'Tepeític', solo: true, es: 'valle o quebrada de sierras (Molina)', en: 'valley between ranges', r: (m) => m.entreMontes },
      { w: 'Papaloapan', pre: 'río', es: 'río de mariposas (Vetancurt)', en: 'river of butterflies', r: (m) => ['meandros', 'costa'].includes(m.arq) },
    ],
  };

  // Nombres en maya yucateco: sólo los que registra el Diccionario Maya Cordemex (Barrera
  // Vásquez, dir., 1980; OCR en toponimia/fuentes/cordemex_norm.txt), con su sentido. Sólo en
  // terreno de caliza, que es donde hay cenotes: en lo volcánico o en la arenisca no tienen lugar.
  MT.MAYA = {
    hondonada: [
      { w: "Chan Ts'onot", solo: true, es: 'gran cenote (topónimo)', en: 'great cenote', r: (m) => m.roca === 'caliza' && !m.chico },
      { w: "Chik'in Ts'ono'ot", solo: true, es: 'cenote del oeste (topónimo)', en: 'cenote of the west', r: (m) => m.roca === 'caliza' && m.poniente },
      { w: "Chan K'om", solo: true, es: 'pequeña hondonada (topónimo)', en: 'little hollow', r: (m) => m.roca === 'caliza' && m.chico },
      { w: 'Aktun', solo: true, es: 'cueva, caverna', en: 'cave', r: (m) => m.roca === 'caliza' && m.escarpado },
      { w: "Ch'e'en", solo: true, es: 'pozo o cueva de agua', en: 'water well', r: (m) => m.roca === 'caliza' && m.hondo },
      { w: 'Homenhom', solo: true, es: 'simas hundidas, cavernas desplomadas', en: 'collapsed sinks', r: (m) => m.arq === 'karst' },
    ],
    cumbre: [
      { w: "U Ho'ol Wits", solo: true, es: 'cumbre de sierra', en: 'summit of the range', r: (m) => m.roca === 'caliza' && m.principal },
      { w: "Pu'uk", solo: true, es: 'sierra baja; falda de monte', en: 'low range', r: (m) => m.roca === 'caliza' && m.alargado },
    ],
    lago: [
      { w: "Ak'lil", solo: true, es: 'laguneta, aguada', en: 'water hole', r: (m) => m.roca === 'caliza' && m.chico },
      { w: "Tsa'ats", solo: true, es: 'aguada que nunca se seca', en: 'never-dry pond', r: (m) => m.roca === 'caliza' && !m.chico },
    ],
  };

  // Quechua del Cusco, del Simi Taqe (Academia Mayor de la Lengua Quechua, 2.ª ed., 2005).
  // Sólo formas que el diccionario da: "rit'i orqo, cerro nevado" y "orqo pata, encima del
  // cerro" vienen tal cual de la entrada orqo; lago = "qocha, hatun qocha"; laguna =
  // "qocha, huch'uy qocha". El color va antes del nombre, como en Yanaqocha o Pukaorqo.
  MT.QUECHUA = {
    cumbre: [
      { w: "Rit'i Orqo", solo: true, es: 'cerro nevado (Simi Taqe, s.v. orqo)', en: 'snow mountain', r: (m) => m.altM > 4700 },
      { w: 'Yuraq Orqo', solo: true, es: 'cerro blanco (yuraq: blanco)', en: 'white mountain', r: (m) => m.altM > 3800 && !m.chico },
      { w: 'Puka Orqo', solo: true, es: 'cerro colorado (puka: rojo)', en: 'red mountain', r: (m) => m.roca === 'volcanica' || m.roca === 'arenisca' },
      { w: 'Yana Orqo', solo: true, es: 'cerro negro (yana: negro)', en: 'black mountain', r: (m) => m.roca === 'volcanica' && m.conico },
      { w: 'Hatun Orqo', solo: true, es: 'cerro grande (hatun: grande)', en: 'great mountain', r: (m) => m.principal && !m.chico && m.altM > 3000 },
      { w: 'Orqo Pata', solo: true, es: 'encima del cerro (Simi Taqe, s.v. orqo)', en: 'on top of the mountain', r: (m) => m.plano },
      { w: "Huch'uy Orqo", solo: true, es: "cerro chico (huch'uy: pequeño)", en: 'little mountain', r: (m) => m.chico && !m.principal },
      // animales del Simi Taqe: kuntur (anka, huch'uy kuntur), taruka (venado andino), atoq (zorro), wisk'acha
      { w: 'Kuntur Orqo', solo: true, es: 'cerro del cóndor', en: 'hill of the condor', r: (m) => m.altM > 3800 && (m.agudo || m.escarpado) },
      { w: 'Anka Orqo', solo: true, es: 'cerro del águila (anka)', en: 'hill of the eagle', r: (m) => m.agudo },
      { w: 'Taruka Orqo', solo: true, es: 'cerro de la taruka, el venado andino', en: 'hill of the Andean deer', r: (m) => m.altM > 3000 && m.altM < 4600 },
      { w: 'Atoq Orqo', solo: true, es: 'cerro del zorro (atoq)', en: 'hill of the fox', r: (m) => m.chico || m.romo },
      { w: "Wisk'acha Orqo", solo: true, es: "cerro de la vizcacha (wisk'acha)", en: 'hill of the viscacha', r: (m) => m.escarpado && m.altM > 3000 },
      // más del Simi Taqe: rumi piedra, suni largo, muyu redondo, qhata ladera, puna, kiswar
      { w: 'Rumi Orqo', solo: true, es: 'el cerro de piedra (rumi)', en: 'stone hill', r: (m) => m.escarpado || m.agudo },
      { w: 'Suni Orqo', solo: true, es: 'el cerro largo (suni: largo, alargado)', en: 'long hill', r: (m) => m.alargado },
      { w: 'Muyu Orqo', solo: true, es: 'el cerro redondo (muyu: círculo, redondez)', en: 'round hill', r: (m) => m.conico && !m.agudo },
      { w: 'Qhata', solo: true, es: 'la ladera, la pendiente', en: 'slope', r: (m) => !m.principal && (m.solana || m.umbria) },
      { w: 'Puna', solo: true, es: 'la puna: el piso alto andino de 3 700 a 4 990 m', en: 'the high Andean plateau', r: (m) => m.altM > 3700 && m.altM < 4990 && (m.plano || m.romo) },
      { w: 'Kiswar Orqo', solo: true, es: 'el cerro del kiswar (un árbol andino)', en: 'hill of the kiswar tree', r: (m) => m.altM > 2500 && m.altM < 3800 && !m.seco },
    ],
    paso: [
      { w: "Q'asa", solo: true, es: "paso entre dos cerros (Simi Taqe, s.v. q'asa)", en: 'pass', r: () => true },
      { w: "Hatun Q'asa", solo: true, es: 'el paso grande', en: 'great pass', r: (m) => m.ancho },
    ],
    lago: [
      { w: "Huch'uy Qocha", solo: true, es: 'laguna (Simi Taqe: laguna = qocha, huch\'uy qocha)', en: 'little lake', r: (m) => m.chico },
      { w: 'Hatun Qocha', solo: true, es: 'lago (Simi Taqe: lago = qocha, hatun qocha)', en: 'great lake', r: (m) => !m.chico },
      { w: 'Yana Qocha', solo: true, es: 'laguna negra', en: 'black lake', r: (m) => m.roca === 'volcanica' || m.juntoCumbre },
      { w: 'Puma Qocha', solo: true, es: 'laguna del puma', en: 'lake of the puma', r: () => true },
      { w: 'Wallata Qocha', solo: true, es: 'laguna de la wallata, el ganso andino', en: 'lake of the Andean goose', r: (m) => !m.chico },
      { w: 'Muyu Qocha', solo: true, es: 'la laguna redonda', en: 'round lake', r: (m) => m.chico },
      { w: 'Suni Qocha', solo: true, es: 'la laguna larga', en: 'long lake', r: (m) => !m.chico },
    ],
    valle: [
      { w: "Wayq'o", solo: true, es: 'valle o quebrada (Simi Taqe)', en: 'ravine', r: (m) => m.encajado },
      { w: "Atoq Wayq'o", solo: true, es: 'quebrada del zorro', en: 'ravine of the fox', r: (m) => m.encajado },
      { w: 'Rumi Mayu', solo: true, es: 'el río de piedra', en: 'stony river', r: (m) => m.encajado || m.empinado },
      { w: 'Hatun Mayu', solo: true, es: 'río grande (mayu: río)', en: 'great river', r: (m) => !m.encajado },
    ],
  };

  // Zapoteco de la Sierra Juárez (Atepec), del Diccionario zapoteco de Juárez (Nellis y Goodner,
  // ILV, 1983). Sólo lugares que el diccionario registra con su sentido.
  const L = '̱'; // la línea abajo de las consonantes fuertes (zapoteco de Zoogocho)
  MT.ZAPOTECO = {
    valle: [
      { w: 'Bdin' + L + 'j', ref: 'Long y Cruz, Diccionario zapoteco de San Bartolomé Zoogocho', solo: true, es: 'la barranca (Zoogocho)', en: 'ravine', r: (m) => m.encajado },
    ],
    hondonada: [
      { w: 'Bloj', ref: 'Long y Cruz, Diccionario zapoteco de San Bartolomé Zoogocho', solo: true, es: 'la cueva (Zoogocho)', en: 'cave', r: (m) => m.escarpado || m.hondo },
    ],
    cumbre: [
      { w: "Í'yatò' Betsina'a", solo: true, es: 'cerro del Venado (arriba de Atepec)', en: 'hill of the deer', r: (m) => m.principal && (m.conico || m.agudo) },
      { w: "I'yayòtò'", solo: true, es: 'cerro del templo', en: 'hill of the temple', r: (m) => m.conico || m.romo },
      { w: "Ru'a Cuàdì", solo: true, es: 'cerro de Pastle: a la orilla de donde hay pastle', en: 'hill where the moss grows', r: (m) => !m.principal },
      { w: "Íyya Lídi'", solo: true, es: 'peña de la Liebre', en: 'crag of the hare', r: (m) => m.agudo && !m.principal },
      // compuestos con el mismo patrón (Í'yatò' cerro, Íyya peña) y animales que el diccionario registra
      { w: "Í'yatò' Bethiá'", solo: true, es: "cerro del águila (bethiá')", en: 'hill of the eagle', r: (m) => m.agudo },
      { w: "Í'yatò' Betití", solo: true, es: 'cerro del tecolote (betití)', en: 'hill of the owl', r: (m) => m.romo },
      { w: "Í'yatò' Be'rida", solo: true, es: "cerro de la ardilla (be'rida)", en: 'hill of the squirrel', r: (m) => m.chico || m.romo },
      { w: "Íyya Beda'", solo: true, es: "peña de la zorra (beda')", en: 'crag of the fox', r: (m) => m.escarpado },
      { w: 'Íyya Bèl·là', solo: true, es: 'peña de la culebra (bèl·là)', en: 'crag of the snake', r: (m) => m.escarpado && !m.principal },
      // zapoteco de San Bartolomé Zoogocho (Long y Cruz, ILV, 2000): Ya'absia es un pueblo cuyo
      // nombre dice "cerro del águila" (ya'a cerro + bsia águila); con el mismo patrón, los
      // animales y colores que registra el diccionario. Las consonantes fuertes van subrayadas.
      { w: "Ya'absia", ref: 'Long y Cruz, Diccionario zapoteco de San Bartolomé Zoogocho', solo: true, es: "cerro del águila (ya'a + bsia); nombre de pueblo, Apéndice F", en: 'hill of the eagle', r: (m) => m.agudo || m.principal },
      { w: "Ya'abeco'yo", ref: 'Long y Cruz, Diccionario zapoteco de San Bartolomé Zoogocho', solo: true, es: "cerro del coyote (beco'yo)", en: 'hill of the coyote', r: (m) => !m.agudo },
      { w: "Ya'abeza'", ref: 'Long y Cruz, Diccionario zapoteco de San Bartolomé Zoogocho', solo: true, es: "cerro de la zorra (beza')", en: 'hill of the fox', r: (m) => m.chico || m.romo },
      { w: "Ya'adam", ref: 'Long y Cruz, Diccionario zapoteco de San Bartolomé Zoogocho', solo: true, es: 'cerro del tecolote (dam)', en: 'hill of the owl', r: (m) => m.romo },
      { w: "Ya'abel" + L, ref: 'Long y Cruz, Diccionario zapoteco de San Bartolomé Zoogocho', solo: true, es: 'cerro de la culebra (bel' + L + ')', en: 'hill of the snake', r: (m) => m.escarpado },
      { w: "Ya'agasj", ref: 'Long y Cruz, Diccionario zapoteco de San Bartolomé Zoogocho', solo: true, es: 'cerro negro (gasj)', en: 'black hill', r: (m) => m.roca === 'volcanica' },
      { w: "Ya'axtil", ref: 'Long y Cruz, Diccionario zapoteco de San Bartolomé Zoogocho', solo: true, es: 'cerro blanco (xtil)', en: 'white hill', r: (m) => m.roca === 'caliza' || m.altM > 3500 },
      { w: "Ya'acha'o", ref: 'Long y Cruz, Diccionario zapoteco de San Bartolomé Zoogocho', solo: true, es: "cerro grande (cha'o)", en: 'big hill', r: (m) => m.principal && !m.chico },
    ],
    lago: [
      { w: "Rú'a Dina", solo: true, es: 'ojo de agua (lugar)', en: 'spring', r: (m) => m.chico },
      { w: "Yeldao'", ref: 'Long y Cruz, Diccionario zapoteco de San Bartolomé Zoogocho', solo: true, es: "laguna grande (yel + -dao'); nombre de pueblo, Zoogocho", en: 'big lake', r: (m) => !m.chico },
      { w: 'Yelgasj', ref: 'Long y Cruz, Diccionario zapoteco de San Bartolomé Zoogocho', solo: true, es: 'laguna negra (yel + gasj)', en: 'black lake', r: (m) => m.roca === 'volcanica' || m.juntoCumbre },
    ],
  };

  // Inuttut de Labrador, del English-Inuttut Dictionary del Labrador Virtual Museum.
  // La K mayúscula dentro de la palabra es la q uvular de la ortografía de Labrador.
  MT.INUTTUT = {
    cumbre: [
      { w: 'Natsak', solo: true, es: 'cerro alto', en: 'high hill', r: (m) => m.principal },
      { w: 'KakKak', solo: true, es: 'cerro', en: 'hill', r: () => true },
      { w: 'MajukKak', solo: true, es: 'cuesta empinada', en: 'steep slope', r: (m) => m.agudo || m.empinado },
      { w: 'Innak', solo: true, es: 'acantilado', en: 'cliff', r: (m) => m.escarpado || m.agudo },
      { w: 'Kikittak', solo: true, es: 'isla', en: 'island', r: (m) => m.enIsla },
    ],
    lago: [
      { w: 'Tasiujak', solo: true, es: 'laguna, "como lago"', en: 'pond', r: (m) => m.chico },
      { w: 'Tasik', solo: true, es: 'lago', en: 'lake', r: (m) => !m.chico },
    ],
    valle: [
      { w: 'Kok', solo: true, es: 'arroyo, río', en: 'brook', r: () => true },
    ],
  };

  // Kalaallisut (groenlandés occidental): topónimos reales de Groenlandia con su sentido.
  MT.KALAALLISUT = {
    // kalaallisut (groenlandés occidental), del Oqaasileriffik y Universidad de Chicago, Greenlandic–English Dictionary (2018, ordbog.gl). Sólo palabras y nombres que el
    // diccionario registra tal cual (uummannaq: "montaña en forma de corazón").
    cumbre: [
      { w: 'Qaqqaq', solo: true, ref: 'Oqaasileriffik y Universidad de Chicago, Greenlandic–English Dictionary (2018, ordbog.gl)', es: 'la montaña, el pico', en: 'mountain; peak', r: (m) => m.principal },
      { w: 'Inngik', solo: true, ref: 'Oqaasileriffik y Universidad de Chicago, Greenlandic–English Dictionary (2018, ordbog.gl)', es: 'la punta de la montaña', en: 'tip of the mountain', r: (m) => m.agudo },
      { w: 'Qingartaq', solo: true, ref: 'Oqaasileriffik y Universidad de Chicago, Greenlandic–English Dictionary (2018, ordbog.gl)', es: 'la cresta de la montaña', en: 'mountain ridge', r: (m) => m.alargado },
      { w: 'Qattuneq', solo: true, ref: 'Oqaasileriffik y Universidad de Chicago, Greenlandic–English Dictionary (2018, ordbog.gl)', es: 'la loma', en: 'hill', r: (m) => m.chico || m.romo },
      { w: 'Uummannaq', solo: true, ref: 'Oqaasileriffik y Universidad de Chicago, Greenlandic–English Dictionary (2018, ordbog.gl)', es: 'la montaña en forma de corazón', en: 'heart-shaped mountain', r: (m) => m.partido },
      { w: 'Qaqortoq', solo: true, ref: 'Oqaasileriffik y Universidad de Chicago, Greenlandic–English Dictionary (2018, ordbog.gl)', es: 'el blanco', en: 'the white one', r: (m) => m.altM > 2500 || m.roca === 'caliza' },
      { w: 'Qernertoq', solo: true, ref: 'Oqaasileriffik y Universidad de Chicago, Greenlandic–English Dictionary (2018, ordbog.gl)', es: 'el negro', en: 'the black one', r: (m) => m.roca === 'volcanica' || m.escarpado },
      { w: 'Nunataq', solo: true, ref: 'Oqaasileriffik y Universidad de Chicago, Greenlandic–English Dictionary (2018, ordbog.gl)', es: 'la cima que asoma sobre el glaciar', en: 'nunatak', r: (m) => m.altM > 1500 && !m.chico },
      { w: 'Ippik', solo: true, ref: 'Oqaasileriffik y Universidad de Chicago, Greenlandic–English Dictionary (2018, ordbog.gl)', es: 'el acantilado sobre el mar', en: 'sea cliff', r: (m) => m.costa && m.escarpado },
    ],
    paso: [
      { w: 'Kiggaq Ituittarfik', solo: true, ref: 'Oqaasileriffik y Universidad de Chicago, Greenlandic–English Dictionary (2018, ordbog.gl)', es: 'el paso de montaña', en: 'mountain pass', r: () => true },
    ],
    hondonada: [
      { w: 'Qaarusuk', solo: true, ref: 'Oqaasileriffik y Universidad de Chicago, Greenlandic–English Dictionary (2018, ordbog.gl)', es: 'la cueva en una pared de roca', en: 'cave in a rock wall', r: (m) => m.escarpado || m.hondo },
    ],
    lago: [
      { w: 'Taseq', solo: true, ref: 'Oqaasileriffik y Universidad de Chicago, Greenlandic–English Dictionary (2018, ordbog.gl)', es: 'el lago', en: 'lake', r: () => true },
      { w: 'Tasiilaq', solo: true, es: 'el lugar de los lagos (nombre de lugar)', en: 'place of the lakes', r: (m) => !m.chico },
    ],
    valle: [
      { w: 'Kuussuaq', solo: true, ref: 'Oqaasileriffik y Universidad de Chicago, Greenlandic–English Dictionary (2018, ordbog.gl)', es: 'el río grande', en: 'a big river', r: (m) => m.principal },
      { w: 'Kuuk', solo: true, ref: 'Oqaasileriffik y Universidad de Chicago, Greenlandic–English Dictionary (2018, ordbog.gl)', es: 'el río, el arroyo', en: 'river; creek', r: (m) => !m.principal },
      { w: 'Qooroq', solo: true, ref: 'Oqaasileriffik y Universidad de Chicago, Greenlandic–English Dictionary (2018, ordbog.gl)', es: 'el valle', en: 'valley', r: (m) => !m.encajado },
      { w: 'Qorlortoq', solo: true, ref: 'Oqaasileriffik y Universidad de Chicago, Greenlandic–English Dictionary (2018, ordbog.gl)', es: 'la cascada', en: 'waterfall', r: (m) => m.empinado },
      { w: 'Kangerlussuaq', solo: true, ref: 'Oqaasileriffik y Universidad de Chicago, Greenlandic–English Dictionary (2018, ordbog.gl)', es: 'el fiordo grande', en: 'a large fjord', r: (m) => m.glaciar || m.arq === 'costa' },
      { w: 'Sermilik', solo: true, es: 'el lugar con glaciares (nombre de lugar)', en: 'place with glaciers', r: (m) => m.glaciar },
    ],
  };

  // Suomi: la toponimia finlandesa se hace pegando un calificativo a un genérico registrado
  // (tunturi, vaara, harju, kumpu, kuru, järvi, lampi, joki), como en los miles de
  // Pitkäjärvi y Mustavaara del mapa del Maanmittauslaitos. Hiidenkirnu: marmita de gigante.
  MT.SUOMI = {
    cumbre: [
      { w: 'Isotunturi', solo: true, es: 'la gran loma pelada (tunturi: cerro sin árboles)', en: 'great fell', r: (m) => m.principal && m.romo }, // el tunturi es pelado y redondo
      { w: 'Pitkävaara', solo: true, es: 'el cerro largo (vaara: cerro boscoso)', en: 'long hill', r: (m) => m.alargado },
      { w: 'Kivivaara', solo: true, es: 'el cerro de piedra', en: 'stone hill', r: (m) => m.agudo },
      { w: 'Mustavaara', solo: true, es: 'el cerro negro', en: 'black hill', r: (m) => m.roca === 'volcanica' },
      { w: 'Kumpu', solo: true, es: 'el montículo', en: 'knoll', r: (m) => m.chico || m.romo },
      { w: 'Pitkäharju', solo: true, es: 'el esker largo (harju: cresta de grava glaciar)', en: 'long esker', r: (m) => m.alargado && m.arq === 'drumlins' },
    ],
    paso: [
      { w: 'Kuru', solo: true, es: 'la garganta', en: 'gorge', r: (m) => m.estrecho },
    ],
    hondonada: [
      { w: 'Hiidenkirnu', solo: true, es: 'marmita de gigante', en: "giant's kettle", r: (m) => m.circular && m.chico },
    ],
    lago: [
      { w: 'Pikkulampi', solo: true, es: 'la lagunita', en: 'little pond', r: (m) => m.chico },
      { w: 'Mustajärvi', solo: true, es: 'el lago negro', en: 'black lake', r: (m) => !m.chico },
      { w: 'Isojärvi', solo: true, es: 'el lago grande', en: 'great lake', r: (m) => !m.chico },
    ],
    valle: [
      { w: 'Isojoki', solo: true, es: 'el río grande', en: 'great river', r: (m) => !m.encajado },
      { w: 'Mustajoki', solo: true, es: 'el río negro', en: 'black river', r: (m) => m.encajado },
    ],
  };

  // Diné bizaad (navajo), de Wiktionary con sus referencias a Young y Morgan (The Navajo
  // Language, 1987; Analytical Lexicon, 1992). Sólo genéricos y descripciones (sustantivo +
  // color, como en la toponimia diné); nunca nombres de lugares reales, que pueden ser sagrados.
  MT.DINE = {
    cumbre: [
      { w: 'Bikoohdááʼ', solo: true, es: 'el borde del cañón', en: 'canyon rim', r: (m) => m.arq === 'canon' },
      { w: 'Dah Azką́', solo: true, es: 'mesa: está plano arriba', en: 'mesa, flat on top', r: (m) => m.plano },
      { w: 'Tsézhin', solo: true, es: 'roca de lava, malpaís (tsé roca + łizhin negro)', en: 'lava rock', r: (m) => m.roca === 'volcanica' },
      { w: 'Tsé Łichííʼ', solo: true, es: 'la roca roja', en: 'red rock', r: (m) => m.roca === 'arenisca' },
      { w: 'Tsé Łigai', solo: true, es: 'la roca blanca', en: 'white rock', r: (m) => m.roca === 'arenisca' && m.escarpado },
      { w: 'Dził Łichííʼ', solo: true, es: 'el cerro rojo', en: 'red mountain', r: (m) => m.roca === 'arenisca' && !m.chico && !m.plano && m.escarpado },
      { w: 'Dził Łizhin', solo: true, es: 'el cerro negro', en: 'black mountain', r: (m) => m.roca === 'volcanica' && !m.chico },
    ],
    hondonada: [
      { w: 'Tséʼáán', solo: true, es: 'cueva en la roca (tsé roca + aʼáán hoyo)', en: 'rock cave', r: (m) => m.escarpado },
      { w: 'Aʼáán', solo: true, es: 'el hoyo en la tierra', en: 'hole in the ground', r: (m) => m.chico },
    ],
    lago: [
      { w: 'Tónteel', solo: true, es: 'agua ancha: lago grande (tó agua + niteel es ancho)', en: 'wide water', r: (m) => !m.chico },
    ],
    valle: [
      { w: 'Bikooh', solo: true, es: 'la cañada, el arroyo seco', en: 'arroyo, gorge', r: (m) => m.encajado },
      { w: 'Tooh', solo: true, es: 'el río, el agua grande', en: 'river', r: (m) => !m.encajado },
    ],
  };

  // Pitjantjatjara, del glosario Kungka Kunpu (Art Gallery of South Australia), Wiktionary
  // (Goddard) y Glosbe. Sólo genéricos; fuera los nombres de sitios y relatos (Tjukurpa).
  MT.PITJANTJATJARA = {
    cumbre: [
      { w: 'Puḻi Puḻka', solo: true, es: 'el cerro de roca grande (puḻi roca, cerro + puḻka grande)', en: 'big rock hill', r: (m) => m.principal },
      { w: 'Puḻi', solo: true, es: 'roca, cerro', en: 'rock hill', r: () => true },
      { w: 'Apu', solo: true, es: 'piedra, cerro', en: 'stone, hill', r: (m) => m.chico || m.romo },
      { w: 'Puḻi Piṟanpa', solo: true, es: 'el cerro de roca blanca', en: 'white rock hill', r: (m) => m.escarpado },
      { w: 'Tali', solo: true, es: 'la duna, el médano', en: 'sand dune', r: (m) => m.arq === 'dunas' },
    ],
    hondonada: [
      { w: 'Tjukuḻa', solo: true, es: 'aguaje en la roca', en: 'rockhole', r: (m) => m.chico },
      { w: 'Piṯi', solo: true, es: 'el hoyo', en: 'hole', r: () => true },
    ],
    lago: [
      { w: 'Kapi Tjukuḻa', solo: true, es: 'el aguaje en la roca', en: 'rockhole', r: (m) => m.chico },
      { w: 'Kapi', solo: true, es: 'agua, lluvia, aguaje', en: 'water', r: () => true },
    ],
  };

  // Rarámuri (ralámuli) de Norogachi, del Diccionario Ralámuli (diccionarioralamuli.com.mx).
  // Casi todo el diccionario son verbos; de paisaje registra estos dos lugares con su sentido.
  MT.RARAMURI = {
    // del libro Tarahumara Medicine (Irigoyen-Rascón y Paredes, 2015), que cita el Diccionario
    // rarámuri-castellano de Brambila: con el sufijo -chi, "lugar de", como Wachóchi (lugar de
    // garzas). Fuera aborí (el táscate), que es de uso ritual.
    cumbre: [
      { w: 'Okóchi', ref: 'Irigoyen-Rascón y Paredes, Tarahumara Medicine (Brambila)', solo: true, es: 'lugar de pinos (okó)', en: 'place of pines', r: (m) => m.altM > 1800 && m.altM < 3200 },
      { w: 'Mateóchi', ref: 'Irigoyen-Rascón y Paredes, Tarahumara Medicine (Brambila)', solo: true, es: 'lugar de pinabetes (mateó)', en: 'place of firs', r: (m) => m.altM > 2400 },
      { w: 'Rojáchi', ref: 'Irigoyen-Rascón y Paredes, Tarahumara Medicine (Brambila)', solo: true, es: 'lugar de encinos (rojá)', en: 'place of oaks', r: (m) => m.altM > 1200 && m.altM < 2600 },
      { w: 'Bejokéchi', ref: 'Irigoyen-Rascón y Paredes, Tarahumara Medicine (Brambila)', solo: true, es: 'lugar de mezquites (bejoké)', en: 'place of mesquites', r: (m) => m.altM < 1500 },
      { w: 'Chumaríchi', ref: 'Irigoyen-Rascón y Paredes, Tarahumara Medicine (Brambila)', solo: true, es: 'lugar de venados (chumarí)', en: 'place of deer', r: () => true },
      { w: "Wa'wéchi", ref: 'Irigoyen-Rascón y Paredes, Tarahumara Medicine (Brambila)', solo: true, es: "lugar de águilas (wa'wé)", en: 'place of eagles', r: (m) => m.agudo || m.escarpado },
      { w: 'Wirúchi', ref: 'Irigoyen-Rascón y Paredes, Tarahumara Medicine (Brambila)', solo: true, es: 'lugar de zopilotes (wirú)', en: 'place of vultures', r: (m) => m.agudo },
      { w: 'Rowíchi', ref: 'Irigoyen-Rascón y Paredes, Tarahumara Medicine (Brambila)', solo: true, es: 'lugar de conejos (rowí)', en: 'place of rabbits', r: (m) => m.chico || m.romo },
      { w: 'Wasachíchi', ref: 'Irigoyen-Rascón y Paredes, Tarahumara Medicine (Brambila)', solo: true, es: 'lugar de coyotes (wasachí)', en: 'place of coyotes', r: (m) => !m.principal },
      { w: 'Sayawíchi', ref: 'Irigoyen-Rascón y Paredes, Tarahumara Medicine (Brambila)', solo: true, es: 'lugar de víboras de cascabel (sayawi)', en: 'place of rattlesnakes', r: (m) => m.escarpado && !m.principal },
    ],
    valle: [
      { w: 'Repogáchi', ref: 'Irigoyen-Rascón y Paredes, Tarahumara Medicine (Brambila)', solo: true, es: 'lugar de alisos (repogá)', en: 'place of sycamores', r: (m) => !m.encajado },
      { w: 'Watosíchi', ref: 'Irigoyen-Rascón y Paredes, Tarahumara Medicine (Brambila)', solo: true, es: 'lugar de sauces (watosí)', en: 'place of willows', r: (m) => !m.encajado },
      { w: 'Wisaróchi', ref: 'Irigoyen-Rascón y Paredes, Tarahumara Medicine (Brambila)', solo: true, es: 'lugar de álamos (wisaró)', en: 'place of aspens', r: () => true },
      { w: 'Nolóachi', solo: true, es: 'lugar donde da vuelta: el río envuelve un cerro', en: 'where the river wraps around a hill', r: (m) => m.encajado || m.arq === 'meandros' },
    ],
    lago: [
      { w: 'Wachóchi', solo: true, es: 'lugar de garzas', en: 'place of herons', r: () => true },
    ],
  };

  // Hawaiano (Wiktionary): sustantivo + calificativo, como Puʻu ʻUla. Fuera Mauna Kea,
  // Mauna Loa y todo lo de Pele: son lugares y una deidad vivos.
  MT.HAWAIANO = {
    cumbre: [
      { w: 'Mauna Nui', solo: true, es: 'la montaña grande', en: 'great mountain', r: (m) => m.principal && !m.chico },
      { w: 'Puʻu ʻUla', solo: true, es: 'el cerro rojo (puʻu: cerro, cono)', en: 'red hill', r: (m) => m.conico || m.chico },
      { w: 'Puʻu ʻEleʻele', solo: true, es: 'el cerro negro', en: 'black hill', r: (m) => m.roca === 'volcanica' },
      { w: 'Puʻu Kea', solo: true, es: 'el cerro blanco', en: 'white hill', r: (m) => m.altM > 3000 },
      { w: 'Pali', solo: true, es: 'el acantilado', en: 'cliff', r: (m) => m.escarpado },
    ],
    hondonada: [
      { w: 'Lua Nui', solo: true, es: 'el hoyo grande (lua: hoyo, cráter)', en: 'great pit', r: (m) => !m.chico },
      { w: 'Lua', solo: true, es: 'el hoyo', en: 'pit', r: (m) => m.chico },
    ],
    lago: [{ w: 'Loko', solo: true, es: 'el estanque', en: 'pond', r: () => true }],
    valle: [
      { w: 'Awāwa', solo: true, es: 'el valle', en: 'valley', r: (m) => !m.encajado },
      { w: 'Kahawai', solo: true, es: 'el arroyo ("lugar del agua")', en: 'stream', r: (m) => m.encajado },
    ],
  };

  // Islandés (Wiktionary): genéricos y nombres descriptivos que se repiten por toda la isla
  // (Hvítá, Svartá, Langavatn, Djúpavatn, Rauðhóll).
  MT.ISLANDES = {
    cumbre: [
      { w: 'Dyngja', solo: true, es: 'volcán escudo', en: 'shield volcano', r: (m) => m.arq === 'escudo' && m.principal },
      { w: 'Rauðhóll', solo: true, es: 'la loma roja: cono de escoria', en: 'red mound', r: (m) => m.roca === 'volcanica' && (m.chico || m.conico) },
      { w: 'Tindur', solo: true, es: 'el pico', en: 'peak', r: (m) => m.agudo },
      { w: 'Hamar', solo: true, es: 'el peñasco', en: 'crag', r: (m) => m.escarpado },
      { w: 'Hóll', solo: true, es: 'la loma', en: 'mound', r: (m) => m.romo },
    ],
    hondonada: [{ w: 'Gígur', solo: true, es: 'el cráter', en: 'crater', r: () => true }],
    paso: [{ w: 'Skarð', solo: true, es: 'el paso, la mella', en: 'notch, pass', r: () => true }],
    lago: [
      { w: 'Djúpavatn', solo: true, es: 'el lago hondo', en: 'deep lake', r: (m) => !m.chico },
      { w: 'Langavatn', solo: true, es: 'el lago largo', en: 'long lake', r: (m) => !m.chico },
    ],
    valle: [
      { w: 'Gljúfur', solo: true, es: 'el cañón', en: 'gorge', r: (m) => m.encajado },
      { w: 'Hvítá', solo: true, es: 'el río blanco (de glaciar)', en: 'white river', r: (m) => m.glaciar },
      { w: 'Svartá', solo: true, es: 'el río negro', en: 'black river', r: (m) => !m.glaciar },
    ],
  };

  // Purépecha (lista Swadesh de Wiktionary): juata cerro, tsakapu piedra, japunda lago,
  // iurhekua río, k'eri grande, sapi chico, charhapiti rojo, turhipiti negro.
  // Purépecha: Vocabulario del idioma purépecha (Lathrop, ILV, 2007) y el Abecedario de la
  // lengua purépecha (Pátzcuaro, 1980), que explica topónimos de Michoacán: Queréndaro "en el
  // peñasco", Yurécuaro "en el río", Acámbaro "en el maguey" (akamba, maguey en Lathrop). El
  // adjetivo va después del nombre, como en japonda sapichu "laguna chica" o ireta k'éri
  // "pueblo grande". Tsakapindu es "pedregal": el malpaís del campo de conos del Paricutín.
  MT.PUREPECHA = {
    cumbre: [
      { w: "Juáta K'éri", ref: 'Lathrop, Vocabulario del idioma purépecha', solo: true, es: "el cerro grande (juáta + k'éri)", en: 'big hill', r: (m) => m.principal },
      { w: 'Juáta Turhipiti', ref: 'Lathrop, Vocabulario del idioma purépecha', solo: true, es: 'el cerro negro', en: 'black hill', r: (m) => m.roca === 'volcanica' && m.conico },
      { w: 'Juáta Charhapiti', ref: 'Lathrop, Vocabulario del idioma purépecha', solo: true, es: 'el cerro colorado', en: 'red hill', r: (m) => m.roca === 'volcanica' && !m.conico },
      { w: 'Juáta Urapiti', ref: 'Lathrop, Vocabulario del idioma purépecha', solo: true, es: 'el cerro blanco', en: 'white hill', r: (m) => m.altM > 3500 || m.roca === 'caliza' },
      { w: 'Juáta Sapichu', ref: 'Lathrop, Vocabulario del idioma purépecha', solo: true, es: 'el cerro chico', en: 'little hill', r: (m) => m.chico },
      { w: "K'umsta", ref: 'Lathrop, Vocabulario del idioma purépecha', solo: true, es: 'loma chica (Lathrop)', en: 'small hill', r: (m) => m.chico && (m.romo || m.alargado) },
      { w: 'Juatarhu', ref: 'Lathrop, Vocabulario del idioma purépecha', solo: true, es: 'en el monte (juáta + -rhu, en)', en: 'in the hills', r: (m) => !m.principal && !m.chico },
      { w: 'Tsakapu', ref: 'Lathrop, Vocabulario del idioma purépecha', solo: true, es: 'la piedra', en: 'stone', r: (m) => m.agudo || m.escarpado },
      { w: 'Tsakapindu', ref: 'Lathrop, Vocabulario del idioma purépecha', solo: true, es: 'el pedregal (Lathrop): el malpaís', en: 'the lava field', r: (m) => m.cercaColada || (m.roca === 'volcanica' && m.escarpado) },
      { w: 'Queréndaro', ref: 'Abecedario de la lengua purépecha (Pátzcuaro, 1980)', solo: true, es: 'en el peñasco (topónimo de Michoacán, Abecedario 1980)', en: 'at the crag', r: (m) => m.escarpado && !m.principal },
      { w: 'Acámbaro', ref: 'Abecedario de la lengua purépecha (Pátzcuaro, 1980)', solo: true, es: 'en el maguey (topónimo, Abecedario 1980; akamba, maguey)', en: 'at the agave', r: (m) => m.seco || (m.altM > 1700 && m.altM < 2600) },
    ],
    lago: [
      { w: 'Japonda', ref: 'Lathrop, Vocabulario del idioma purépecha', solo: true, es: 'la laguna, el lago', en: 'lake', r: (m) => !m.chico },
      { w: 'Japonda Sapichu', ref: 'Lathrop, Vocabulario del idioma purépecha', solo: true, es: 'la laguna chica', en: 'little lake', r: (m) => m.chico },
      { w: 'Itsï Uérati', ref: 'Lathrop, Vocabulario del idioma purépecha', solo: true, es: 'fuente de agua, manantial (Lathrop)', en: 'spring', r: (m) => m.chico || m.nacimiento },
    ],
    valle: [
      { w: 'Iórhekua', ref: 'Lathrop, Vocabulario del idioma purépecha', solo: true, es: 'el río, la creciente', en: 'river', r: (m) => m.principal },
      { w: 'Iórhekua Sapichu', ref: 'Lathrop, Vocabulario del idioma purépecha', solo: true, es: 'el arroyo ("río chico")', en: 'creek', r: (m) => !m.principal },
      { w: 'Yurécuaro', ref: 'Abecedario de la lengua purépecha (Pátzcuaro, 1980)', solo: true, es: 'en el río (topónimo de Michoacán, Abecedario 1980)', en: 'at the river', r: (m) => !m.encajado },
      { w: 'Kauaru', ref: 'Lathrop, Vocabulario del idioma purépecha', solo: true, es: 'la barranca (Lathrop)', en: 'ravine', r: (m) => m.encajado },
    ],
  };

  // Mixteco de Teposcolula (Wiktionary, de Alvarado, Vocabulario en lengua misteca, 1593):
  // yucu cerro, yuu piedra, ita flor, ndute agua, yuta río. Yucu Ita es Yucuita, "cerro de
  // las flores".
  MT.MIXTECO = {
    // Mixteco de Santiago Yosondúa, Oaxaca (Beaty de Farris y otros, Diccionario básico del mixteco de Yosondúa (ILV, 2012)); el nombre va primero y lo que lo califica
    // después (yucha ka'nu, "río grande"; xini yuku, "cabeza del cerro": la cumbre). Yucu Ita
    // (Yucuita, "cerro de las flores") es de Teposcolula (Alvarado, 1593).
    cumbre: [
      { w: 'Xini Yuku', solo: true, ref: 'Beaty de Farris y otros, Diccionario básico del mixteco de Yosondúa (ILV, 2012)', es: 'la cumbre: "cabeza del cerro"', en: 'the summit, "head of the hill"', r: (m) => m.principal },
      { w: "Yuku Ka'nu", solo: true, ref: 'Beaty de Farris y otros, Diccionario básico del mixteco de Yosondúa (ILV, 2012)', es: "el cerro grande (ka'nu)", en: 'big hill', r: (m) => m.principal && !m.chico },
      { w: 'Yuku Lulu', solo: true, ref: 'Beaty de Farris y otros, Diccionario básico del mixteco de Yosondúa (ILV, 2012)', es: 'el cerro chico (lulu)', en: 'little hill', r: (m) => m.chico },
      { w: 'Yuku Kuijin', solo: true, ref: 'Beaty de Farris y otros, Diccionario básico del mixteco de Yosondúa (ILV, 2012)', es: 'el cerro blanco (kuijin)', en: 'white hill', r: (m) => m.roca === 'caliza' || m.altM > 3200 },
      { w: 'Yuku Jnuu', solo: true, ref: 'Beaty de Farris y otros, Diccionario básico del mixteco de Yosondúa (ILV, 2012)', es: 'el cerro negro (jnuu)', en: 'black hill', r: (m) => m.roca === 'volcanica' },
      { w: "Yuku Kua'a", solo: true, ref: 'Beaty de Farris y otros, Diccionario básico del mixteco de Yosondúa (ILV, 2012)', es: "el cerro colorado (kua'a)", en: 'red hill', r: (m) => m.roca === 'arenisca' },
      { w: 'Yuku Isu', solo: true, ref: 'Beaty de Farris y otros, Diccionario básico del mixteco de Yosondúa (ILV, 2012)', es: 'el cerro del venado (isu)', en: 'hill of the deer', r: (m) => !m.seco },
      { w: 'Yuku Iso', solo: true, ref: 'Beaty de Farris y otros, Diccionario básico del mixteco de Yosondúa (ILV, 2012)', es: 'el cerro del conejo (iso)', en: 'hill of the rabbit', r: (m) => m.chico || m.romo },
      { w: "Yuku Ya'a", solo: true, ref: 'Beaty de Farris y otros, Diccionario básico del mixteco de Yosondúa (ILV, 2012)', es: "el cerro del águila (ya'a)", en: 'hill of the eagle', r: (m) => m.agudo },
      { w: 'Yuku Tijii', solo: true, ref: 'Beaty de Farris y otros, Diccionario básico del mixteco de Yosondúa (ILV, 2012)', es: 'el cerro del zopilote (tijii)', en: 'hill of the vulture', r: (m) => m.escarpado },
      { w: 'Yuku Viko', solo: true, ref: 'Beaty de Farris y otros, Diccionario básico del mixteco de Yosondúa (ILV, 2012)', es: 'el cerro de la nube (viko)', en: 'hill of the cloud', r: (m) => m.altM > 2500 },
      { w: 'Yuku Sau', solo: true, ref: 'Beaty de Farris y otros, Diccionario básico del mixteco de Yosondúa (ILV, 2012)', es: 'el cerro de la lluvia (sau)', en: 'hill of the rain', r: (m) => !m.seco && m.nLagos >= 1 },
      { w: "Kava Ka'nu", solo: true, ref: 'Beaty de Farris y otros, Diccionario básico del mixteco de Yosondúa (ILV, 2012)', es: 'la peña grande (kava: roca, peña)', en: 'big crag', r: (m) => m.escarpado && !m.chico },
      { w: 'Kava', solo: true, ref: 'Beaty de Farris y otros, Diccionario básico del mixteco de Yosondúa (ILV, 2012)', es: 'la peña, la roca', en: 'crag', r: (m) => m.agudo || m.escarpado },
      { w: 'Yucu Ita', solo: true, ref: 'Alvarado, Vocabulario en lengua misteca, 1593 (vía Wiktionary)', es: 'el cerro de las flores (Yucuita)', en: 'hill of flowers', r: (m) => m.romo && !m.principal },
    ],
    hondonada: [
      { w: 'Yau', solo: true, ref: 'Beaty de Farris y otros, Diccionario básico del mixteco de Yosondúa (ILV, 2012)', es: 'la cueva', en: 'cave', r: (m) => m.escarpado || m.hondo },
    ],
    lago: [
      { w: 'Mini', solo: true, ref: 'Beaty de Farris y otros, Diccionario básico del mixteco de Yosondúa (ILV, 2012)', es: 'la laguna', en: 'lagoon', r: () => true },
      { w: 'Mini Lulu', solo: true, ref: 'Beaty de Farris y otros, Diccionario básico del mixteco de Yosondúa (ILV, 2012)', es: 'la laguna chica', en: 'little lagoon', r: (m) => m.chico },
      { w: 'Nducha', solo: true, ref: 'Beaty de Farris y otros, Diccionario básico del mixteco de Yosondúa (ILV, 2012)', es: 'el agua', en: 'water', r: (m) => m.chico },
    ],
    valle: [
      { w: "Yucha Ka'nu", solo: true, ref: 'Beaty de Farris y otros, Diccionario básico del mixteco de Yosondúa (ILV, 2012)', es: 'el río grande', en: 'great river', r: (m) => m.principal },
      { w: 'Yucha Lulu', solo: true, ref: 'Beaty de Farris y otros, Diccionario básico del mixteco de Yosondúa (ILV, 2012)', es: 'el río chico', en: 'little river', r: (m) => !m.principal },
      { w: "Xa'va", solo: true, ref: 'Beaty de Farris y otros, Diccionario básico del mixteco de Yosondúa (ILV, 2012)', es: 'la barranca', en: 'ravine', r: (m) => m.encajado },
    ],
  };

  // Hñähñu (otomí) del Valle del Mezquital, Hidalgo (Hernández Cruz y otros, Diccionario del hñähñu (otomí) del Valle del Mezquital (ILV)). El diccionario registra los
  // compuestos (boto̱ho̱ cerro prieto, nkamto̱ho̱ cerro ladeado, ndentho̱ cumbre del cerro,
  // dähñe barranca grande, xindo piedra ancha) y lugares con su sentido (Dähñe "Barranca
  // Grande", Mpathe "donde mana agua caliente", Momu "arenal").
  MT.OTOMI = {
    cumbre: [
      { w: 'Ndentho̱', solo: true, ref: 'Hernández Cruz y otros, Diccionario del hñähñu (otomí) del Valle del Mezquital (ILV)', es: 'la cumbre del cerro', en: 'summit of the hill', r: (m) => m.principal },
      { w: 'To̱ho̱', solo: true, ref: 'Hernández Cruz y otros, Diccionario del hñähñu (otomí) del Valle del Mezquital (ILV)', es: 'el cerro', en: 'hill', r: () => true },
      { w: 'Boto̱ho̱', solo: true, ref: 'Hernández Cruz y otros, Diccionario del hñähñu (otomí) del Valle del Mezquital (ILV)', es: 'el cerro prieto', en: 'dark hill', r: (m) => m.roca === 'volcanica' },
      { w: 'Nkamto̱ho̱', solo: true, ref: 'Hernández Cruz y otros, Diccionario del hñähñu (otomí) del Valle del Mezquital (ILV)', es: 'el cerro ladeado', en: 'leaning hill', r: (m) => m.solana || m.umbria || m.alargado },
      { w: 'Xindo', solo: true, ref: 'Hernández Cruz y otros, Diccionario del hñähñu (otomí) del Valle del Mezquital (ILV)', es: 'la piedra ancha', en: 'broad stone', r: (m) => m.plano },
      { w: 'Maye', solo: true, ref: 'Hernández Cruz y otros, Diccionario del hñähñu (otomí) del Valle del Mezquital (ILV)', es: 'la peña', en: 'crag', r: (m) => m.escarpado },
      { w: 'Momu', solo: true, ref: 'Hernández Cruz y otros, Diccionario del hñähñu (otomí) del Valle del Mezquital (ILV)', es: 'el arenal (nombre de pueblo: Arenal)', en: 'the sands', r: (m) => m.arq === 'dunas' },
    ],
    hondonada: [
      { w: 'Otsi', solo: true, ref: 'Hernández Cruz y otros, Diccionario del hñähñu (otomí) del Valle del Mezquital (ILV)', es: 'el hoyo', en: 'hole', r: () => true },
    ],
    lago: [
      { w: 'Po̱the', solo: true, ref: 'Hernández Cruz y otros, Diccionario del hñähñu (otomí) del Valle del Mezquital (ILV)', es: 'el manantial', en: 'spring', r: (m) => m.chico },
      { w: 'Mpathe', solo: true, ref: 'Hernández Cruz y otros, Diccionario del hñähñu (otomí) del Valle del Mezquital (ILV)', es: 'donde mana agua caliente (lugar, Tecozautla)', en: 'where hot water springs', r: (m) => m.roca === 'volcanica' },
    ],
    valle: [
      { w: 'Däthe', solo: true, ref: 'Hernández Cruz y otros, Diccionario del hñähñu (otomí) del Valle del Mezquital (ILV)', es: 'el río', en: 'river', r: (m) => m.principal },
      { w: 'Hñe', solo: true, ref: 'Hernández Cruz y otros, Diccionario del hñähñu (otomí) del Valle del Mezquital (ILV)', es: 'la barranca, el arroyo', en: 'ravine', r: (m) => m.encajado || !m.principal },
      { w: 'Dähñe', solo: true, ref: 'Hernández Cruz y otros, Diccionario del hñähñu (otomí) del Valle del Mezquital (ILV)', es: 'la barranca grande (lugar: Barranca Grande)', en: 'great ravine', r: (m) => m.encajado && m.empinado },
    ],
  };

  // Tének, del diccionario Tsakam lejkix káw Tének (Webonary): ts'en cerro, itse' arroyo,
  // chololól caída de agua; tsakam pequeño y pulik grande van antes del nombre.
  MT.TENEK = {
    // tének (huasteco): Larsen (Larsen, Vocabulario huasteco del estado de San Luis Potosí (ILV, 1955; leído con OCR)) y el diccionario de Webonary. El adjetivo va antes del
    // nombre: tsacam itse' "arroyo chico", pulic ja' "agua grande, el mar".
    cumbre: [
      { w: 'Putnib', solo: true, ref: 'Larsen, Vocabulario huasteco del estado de San Luis Potosí (ILV, 1955; leído con OCR)', es: 'la cumbre', en: 'the summit', r: (m) => m.principal },
      { w: "Pulik Ts'en", solo: true, ref: 'Tsakam lejkix káw Tének (Webonary)', es: 'el cerro grande', en: 'big hill', r: (m) => m.principal && !m.chico },
      { w: "Ts'en", solo: true, ref: 'Tsakam lejkix káw Tének (Webonary)', es: 'el cerro', en: 'hill', r: () => true },
      { w: "Tsakam Ts'en", solo: true, ref: 'Tsakam lejkix káw Tének (Webonary)', es: 'el cerro chico', en: 'little hill', r: (m) => m.chico },
      { w: 'Bolchal', solo: true, ref: 'Larsen, Vocabulario huasteco del estado de San Luis Potosí (ILV, 1955; leído con OCR)', es: 'la loma', en: 'ridge', r: (m) => m.alargado || m.romo },
      { w: "T'unu' Bolchal", solo: true, ref: 'Larsen, Vocabulario huasteco del estado de San Luis Potosí (ILV, 1955; leído con OCR)', es: "la loma negra (t'unu' negro)", en: 'black ridge', r: (m) => m.roca === 'volcanica' && (m.alargado || m.romo) },
      { w: "Tsacni' Bolchal", solo: true, ref: 'Larsen, Vocabulario huasteco del estado de San Luis Potosí (ILV, 1955; leído con OCR)', es: "la loma colorada (tsacni')", en: 'red ridge', r: (m) => m.roca === 'arenisca' && (m.alargado || m.romo) },
      { w: "Pactha' T'ujub", solo: true, ref: 'Larsen, Vocabulario huasteco del estado de San Luis Potosí (ILV, 1955; leído con OCR)', es: 'la peña', en: 'crag', r: (m) => m.escarpado },
      { w: 'Quithiblom', solo: true, ref: 'Larsen, Vocabulario huasteco del estado de San Luis Potosí (ILV, 1955; leído con OCR)', es: 'el arenal', en: 'the sands', r: (m) => m.arq === 'dunas' || m.costa },
    ],
    hondonada: [
      { w: 'Paxaljol', solo: true, ref: 'Larsen, Vocabulario huasteco del estado de San Luis Potosí (ILV, 1955; leído con OCR)', es: 'la cueva', en: 'cave', r: (m) => m.escarpado || m.hondo || m.roca === 'caliza' },
      { w: 'Jól', solo: true, ref: 'Larsen, Vocabulario huasteco del estado de San Luis Potosí (ILV, 1955; leído con OCR)', es: 'el hoyo', en: 'hole', r: (m) => m.chico },
    ],
    lago: [
      { w: 'Lejem', solo: true, ref: 'Larsen, Vocabulario huasteco del estado de San Luis Potosí (ILV, 1955; leído con OCR)', es: 'la laguna', en: 'lagoon', r: () => true },
      { w: "Elelja'", solo: true, ref: 'Larsen, Vocabulario huasteco del estado de San Luis Potosí (ILV, 1955; leído con OCR)', es: 'el manantial', en: 'spring', r: (m) => m.chico },
    ],
    valle: [
      { w: 'Cotob', solo: true, ref: 'Larsen, Vocabulario huasteco del estado de San Luis Potosí (ILV, 1955; leído con OCR)', es: 'la barranca', en: 'ravine', r: (m) => m.encajado },
      { w: 'Chololól', solo: true, ref: 'Tsakam lejkix káw Tének (Webonary)', es: 'la caída de agua', en: 'waterfall', r: (m) => m.empinado },
      { w: "Itse'", solo: true, ref: 'Tsakam lejkix káw Tének (Webonary)', es: 'el arroyo, el río chico', en: 'creek', r: (m) => m.principal },
      { w: "Tsacam Itse'", solo: true, ref: 'Larsen, Vocabulario huasteco del estado de San Luis Potosí (ILV, 1955; leído con OCR)', es: 'el arroyo chico', en: 'little creek', r: (m) => !m.principal },
    ],
  };

  // Complementos medidos. Cada uno dice algo cierto del rasgo; f/m: concordancia.
  MT.COMPLEMENTOS = [
    { c: (m) => m.romo && m.plano, m: 'pelón', f: 'pelona', en: 'bald' },
    { c: (m) => m.alargado, m: 'largo', f: 'larga', en: 'long' },
    { c: (m) => m.partido, m: 'partido', f: 'partida', en: 'split' },
    { c: (m) => m.conico && !m.agudo, m: 'redondo', f: 'redonda', en: 'round' },
    { c: (m) => m.agudo, m: 'agudo', f: 'aguda', en: 'sharp' },
    { c: (m) => m.plano, m: 'chato', f: 'chata', en: 'flat-topped' },
    { c: (m) => m.ancho && !m.alargado && m.romo, m: 'gordo', f: 'gorda', en: 'broad' },
    { c: (m) => m.solitario && m.aislado, m: 'solo', f: 'sola', en: 'lone' },
    { c: (m) => m.seco, m: 'seco', f: 'seca', en: 'dry' },
    { c: (m) => m.mayor, m: 'grande', f: 'grande', en: 'great' },
    { c: (m) => m.menor, m: 'chico', f: 'chica', en: 'little' },
    // la nieve: sólo arriba de 4 700 m (como el Nevado de Toluca)
    { c: (m) => m.altM > 4700, p: 0.45, m: 'nevado', f: 'nevada', en: 'snowy' },
    { c: (m) => m.altM > 4600, p: 0.4, m: 'de las nieves', f: 'de las nieves', en: 'of the snows' },
    { c: (m) => m.altM > 5000, p: 0.4, m: 'del hielo', f: 'del hielo', en: 'of the ice' },
    { c: (m) => m.altM > 4500, p: 0.5, m: 'de la nieve', f: 'de la nieve', en: 'of the snow' },
    // el color de la roca, según el tipo de terreno (prieto: basalto; colorado: arenisca y arcilla; blanco: caliza)
    { c: (m) => m.roca === 'volcanica', p: 0.5, m: 'prieto', f: 'prieta', en: 'dark' },
    { c: (m) => m.roca === 'arenisca', m: 'colorado', f: 'colorada', en: 'red' },
    { c: (m) => m.roca === 'caliza', m: 'blanco', f: 'blanca', en: 'white' },
    // lo expuesto: la más alta, aguda y por encima de 3 000 m
    { c: (m) => m.principal && m.agudo && m.altM > 3000, m: 'de los vientos', f: 'de los vientos', en: 'of the winds' },
    { c: (m) => m.nLagos >= 2, m: 'de los lagos', f: 'de los lagos', en: 'of the lakes' },
    { c: (m) => m.nCimas >= 3, m: 'de las tres cumbres', f: 'de las tres cumbres', en: 'of three summits' },
    // de + otro rasgo que de verdad está cerca
    { c: (m) => m.cercaLago, m: 'de la laguna', f: 'de la laguna', en: 'of the lake' },
    { c: (m) => m.cercaHoya, m: 'de la torca', f: 'de la torca', en: 'of the sinkhole' },
    { c: (m) => m.cercaColada, m: 'del malpaís', f: 'del malpaís', en: 'of the lava flow' },
    { c: (m) => m.cercaRio, m: 'del agua', f: 'del agua', en: 'of the water' },
    { c: (m) => m.rumbo, m: (m) => 'del ' + m.rumbo, f: (m) => 'del ' + m.rumbo, en: (m) => m.rumboEn },
    // las muy agudas, hasta arriba: donde se posan las aves de altura (Pico del Águila, Peña
    // del Cuervo, Cerro del Gavilán, comunes en la toponimia de México)
    { c: (m) => m.agudo && m.escarpado && m.altoRel > 0.6, m: 'del águila', f: 'del águila', en: 'of the eagle' },
    { c: (m) => m.agudo && m.escarpado && m.altoRel > 0.6, m: 'del gavilán', f: 'del gavilán', en: 'of the hawk' },
    { c: (m) => m.agudo && m.escarpado && m.altoRel > 0.6, m: 'del halcón', f: 'del halcón', en: 'of the falcon' },
    { c: (m) => m.agudo && m.escarpado, m: 'del cuervo', f: 'del cuervo', en: 'of the raven' },
    { c: (m) => m.agudo && m.escarpado && m.altoRel > 0.5, m: 'de los zopilotes', f: 'de los zopilotes', en: 'of the vultures' },
    // la vegetación según la altura, como en las montañas de México (nunca en lo polar)
    { c: (m) => !m.polar && m.altM > 3900 && m.altM < 4700, m: 'del zacatal', f: 'del zacatal', en: 'of the alpine grassland' },
    { c: (m) => !m.polar && !m.seco && m.altM > 2800 && m.altM < 3600, m: 'de los oyameles', f: 'de los oyameles', en: 'of the firs' },
    { c: (m) => !m.polar && !m.seco && m.altM > 2200 && m.altM < 3500, m: 'del pinar', f: 'del pinar', en: 'of the pinewood' },
    { c: (m) => !m.polar && m.altM > 1800 && m.altM < 3000, m: 'de los ocotes', f: 'de los ocotes', en: 'of the torch pines' },
    { c: (m) => !m.polar && !m.seco && m.altM > 1500 && m.altM < 2600, m: 'del encinal', f: 'del encinal', en: 'of the oak grove' },
    { c: (m) => !m.polar && m.altM < 1800 && (m.seco || ['dunas', 'badlands', 'testigos', 'inselbergs', 'canon'].includes(m.arq)), m: 'de los mezquites', f: 'de los mezquites', en: 'of the mesquites' },
    { c: (m) => !m.polar && m.altM < 600 && m.costa, m: 'de las palmas', f: 'de las palmas', en: 'of the palms' },
    // la fauna y la flora, donde viven (la toponimia de México está llena de ellas: Cerro del
    // Tecolote, Loma del Venado, Peña del Coyote, Llano del Maguey); al puma se le dice león
    { c: (m) => !m.polar && m.altM > 800 && m.altM < 3600, p: 0.35, m: 'del venado', f: 'del venado', en: 'of the deer' },
    { c: (m) => !m.polar && (m.seco || m.altM < 2600), p: 0.35, m: 'del coyote', f: 'del coyote', en: 'of the coyote' },
    { c: (m) => !m.polar && m.altM < 3200, p: 0.3, m: 'del tecolote', f: 'del tecolote', en: 'of the owl' },
    { c: (m) => !m.polar && m.chico && m.altM < 3000, p: 0.35, m: 'del conejo', f: 'del conejo', en: 'of the rabbit' },
    { c: (m) => !m.polar && m.llanoAlrededor, p: 0.35, m: 'de la liebre', f: 'de la liebre', en: 'of the hare' },
    { c: (m) => !m.polar && !m.seco && m.altM > 1500 && m.altM < 3800, p: 0.3, m: 'del león', f: 'del león', en: 'of the puma' },
    { c: (m) => !m.polar && !m.seco && m.altM < 1200 && (m.costa || m.roca === 'caliza'), p: 0.4, m: 'del tigre', f: 'del tigre', en: 'of the jaguar' },
    { c: (m) => !m.polar && !m.seco && m.altM > 2000 && m.altM < 3500, p: 0.3, m: 'del oso', f: 'del oso', en: 'of the bear' },
    { c: (m) => !m.polar && m.seco, p: 0.35, m: 'de las víboras', f: 'de las víboras', en: 'of the vipers' },
    { c: (m) => !m.polar && m.costa && m.altM < 400, p: 0.4, m: 'de las iguanas', f: 'de las iguanas', en: 'of the iguanas' },
    { c: (m) => m.polar && m.costa, p: 0.4, m: 'de las focas', f: 'de las focas', en: 'of the seals' },
    { c: (m) => m.polar, p: 0.3, m: 'del zorro', f: 'del zorro', en: 'of the fox' },
    { c: (m) => !m.polar && m.seco && m.altM > 1700 && m.altM < 2900, p: 0.35, m: 'del maguey', f: 'del maguey', en: 'of the agave' },
    { c: (m) => !m.polar && m.seco && m.altM < 2200, p: 0.35, m: 'de los órganos', f: 'de los órganos', en: 'of the organ cacti' },
    { c: (m) => !m.polar && m.seco && m.altM < 1600, p: 0.3, m: 'del palo blanco', f: 'del palo blanco', en: 'of the white-bark tree' },
    { c: (m) => !m.polar && m.cercaRio && m.altM < 2400, p: 0.35, m: 'de los sabinos', f: 'de los sabinos', en: 'of the cypresses' },
    // los tepuyes: la Gran Sabana (Roraima, Auyán), nombrados en castellano como allá
    { c: (m) => m.arq === 'tepuyes', p: 0.5, m: 'de la niebla', f: 'de la niebla', en: 'of the mist' },
    { c: (m) => m.arq === 'tepuyes' && m.escarpado, p: 0.5, m: 'de las cascadas', f: 'de las cascadas', en: 'of the waterfalls' },
    { c: (m) => m.arq === 'tepuyes' && m.escarpado, p: 0.4, m: 'del salto', f: 'del salto', en: 'of the falls' },
    { c: (m) => m.arq === 'tepuyes', p: 0.4, m: 'de los helechos', f: 'de los helechos', en: 'of the ferns' },
    { c: (m) => m.arq === 'tepuyes', p: 0.4, m: 'del musgo', f: 'del musgo', en: 'of the moss' },
    { c: (m) => m.arq === 'tepuyes', p: 0.35, m: 'de las orquídeas', f: 'de las orquídeas', en: 'of the orchids' },
    // la ladera: la que mira al sol y la que vive en sombra (Moliner)
    { c: (m) => m.solana, p: 0.55, m: 'de la solana', f: 'de la solana', en: 'of the sunny slope' },
    { c: (m) => m.umbria, p: 0.55, m: 'de la umbría', f: 'de la umbría', en: 'of the shady slope' },
    // ubicación: lo que hay alrededor
    { c: (m) => m.llanoAlrededor, m: 'del llano', f: 'del llano', en: 'of the plain' },
    { c: (m) => m.enmedio, m: 'de en medio', f: 'de en medio', en: 'in the middle' },
    { c: (m) => m.costa, m: 'de la costa', f: 'de la costa', en: 'of the coast' },
    { c: (m) => m.cercaRio, m: 'del río', f: 'del río', en: 'of the river' },
    { c: (m) => m.cercaRio && m.nRios >= 2, m: 'de las juntas', f: 'de las juntas', en: 'of the confluence' },
    { c: (m) => m.aislado && !m.solitario, m: 'apartado', f: 'apartada', en: 'set apart' },
  ];
})(typeof globalThis !== 'undefined' ? globalThis : window);
