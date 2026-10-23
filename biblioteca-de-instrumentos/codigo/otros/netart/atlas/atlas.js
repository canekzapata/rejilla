/* =====================================================================
   ATLAS DE LO ILEGIBLE
   un archivo poético en cadena que intenta leerse a sí mismo
   poesiasexp / canek zapata

   escrito para el bootloader SVG-JS de bootloader.art:
   el entorno provee BTLDR.svg (la raíz SVG ya montada) y BTLDR.rnd()
   (azar firmado por la semilla del token). aquí no hay red, ni fuentes
   remotas, ni bibliotecas, ni Math.random, ni Date.now.

   la misma semilla produce la misma topología, el mismo texto, el mismo
   campo cromático y la misma partitura. la interacción muta; no destruye.

   el árbol SVG es parte del poema: los grupos, las máscaras, los símbolos
   y los atributos data-* se leen.
   ===================================================================== */
(function () {
  "use strict";

  /* =================================================================
     0 · EL ARRANQUE — semilla, azar firmado, corrientes derivadas
     ================================================================= */

  var NS = "http://www.w3.org/2000/svg";
  var W = window, D = document;

  /* Encontrar el bootloader.

     Cuidado con esto: el entorno puede exponer BTLDR como propiedad de
     window, pero también como ligadura léxica —`const BTLDR = …` en el
     ámbito global, o como parámetro del envoltorio que rodea a la obra—.
     Una ligadura léxica NO crea propiedad en window. Preguntar sólo por
     `window.BTLDR` es la manera de no encontrarlo nunca y quedarse con la
     semilla de respaldo para siempre: la misma pieza en cada carga.
     El nombre desnudo, en cambio, resuelve los tres casos. */
  var BOOT = null, FUENTE = "local";
  try {
    if (typeof BTLDR !== "undefined" && BTLDR && typeof BTLDR.rnd === "function") {
      BOOT = BTLDR; FUENTE = "btldr";
    }
  } catch (e) { /* algún entorno exótico: seguimos buscando */ }
  if (!BOOT && W.BTLDR && typeof W.BTLDR.rnd === "function") {
    BOOT = W.BTLDR; FUENTE = "window.btldr";
  }

  /* la pieza también corre sola. en ese caso la semilla viene de la URL,
     no del vacío — y si la URL tampoco la trae, es siempre la misma. */
  if (!BOOT) {
    var semillaURL = (new RegExp("[?&]seed=([^&#]+)")).exec(W.location.search);
    var semillaTexto = semillaURL ? decodeURIComponent(semillaURL[1]) : "atlas-de-lo-ilegible";
    FUENTE = semillaURL ? "url:" + semillaTexto : "por-omision";
    var estadoLocal = fnv(semillaTexto);
    BOOT = {
      rnd: function () {
        var t = (estadoLocal += 0x6d2b79f5) >>> 0;
        t = Math.imul(t ^ (t >>> 15), t | 1);
        t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
      }
    };
  }

  /* la raíz SVG: la del bootloader, la que ya esté en la página, o una nueva */
  var SVG = (BOOT && (BOOT.svg || BOOT.root)) || D.querySelector("svg");
  if (!SVG) {
    SVG = D.createElementNS(NS, "svg");
    (D.body || D.documentElement).appendChild(SVG);
  }

  function fnv(texto) {
    var h = 2166136261 >>> 0, s = String(texto);
    for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }

  /* cosechamos la semilla del bootloader una sola vez y de ahí en
     adelante corremos con corrientes propias: así el orden en que el
     visitante toque las cosas no altera la estructura base. */
  var SEMILLA = 0;
  for (var _s = 0; _s < 4; _s++) SEMILLA = ((SEMILLA << 8) ^ Math.floor(BOOT.rnd() * 256)) >>> 0;
  var FIRMA = ("0000000" + SEMILLA.toString(16)).slice(-8);

  function mulberry(a) {
    return function () {
      var t = (a += 0x6d2b79f5) >>> 0;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  /* una corriente por nombre: "topologia", "color", "musica", "texto"…
     nombrar el azar es ya una clasificación. */
  function corriente(nombre) {
    var r = mulberry((SEMILLA ^ fnv(nombre)) >>> 0);
    return {
      f: function (a, b) { return a + r() * (b - a); },
      i: function (a, b) { return Math.floor(a + r() * (b - a + 1)); },
      elige: function (arr) { return arr[Math.floor(r() * arr.length)]; },
      quiza: function (p) { return r() < p; },
      baraja: function (arr) {
        var s = arr.slice(), i, j, t;
        for (i = s.length - 1; i > 0; i--) { j = Math.floor(r() * (i + 1)); t = s[i]; s[i] = s[j]; s[j] = t; }
        return s;
      },
      crudo: r
    };
  }

  var Rtopo = corriente("topologia");
  var Rcolor = corriente("color");
  var Rtexto = corriente("texto");
  var Rmus = corriente("musica");
  var Rauto = corriente("automata");
  var Rhist = corriente("prehistoria");
  var Rmuta = corriente("mutacion");

  var lim = function (v, a, b) { return v < a ? a : (v > b ? b : v); };
  var mez = function (a, b, t) { return a + (b - a) * t; };

  /* ruido de valor determinista: no guarda estado, sólo hashea el lugar */
  function ruido(x, y, capa) {
    var xi = Math.floor(x), yi = Math.floor(y);
    var fx = x - xi, fy = y - yi;
    function n(a, b) {
      var h = fnv(a + ":" + b + ":" + capa + ":" + SEMILLA);
      return (h >>> 8) / 16777216;
    }
    var sx = fx * fx * (3 - 2 * fx), sy = fy * fy * (3 - 2 * fy);
    return mez(mez(n(xi, yi), n(xi + 1, yi), sx), mez(n(xi, yi + 1), n(xi + 1, yi + 1), sx), sy);
  }

  /* =================================================================
     1 · EL CORPUS — material real de poesiasexp
     nada aquí es relleno aleatorio: son fragmentos del poemario.
     ================================================================= */

  var C = {};

  /* --- índice del río: el estrato legible ------------------------ */
  C.rio = [
    "El texto no fue escrito: fue encontrado escribiéndose.",
    "Toda traducción es una forma cortés de perder el original.",
    "El fuego no recuerda la madera; la madera no perdona al fuego.",
    "Un río no se lee dos veces con el mismo idioma.",
    "El archivo guarda todo menos el momento en que fue leído.",
    "Lo que arde ilumina, y al iluminar borra.",
    "La memoria es un mapa dibujado sobre otro mapa que ya se movió.",
    "Cada palabra es la ruina de un silencio anterior.",
    "El manuscrito existe sólo mientras nadie lo entiende.",
    "Nombrar el río fue el primer error de cartografía.",
    "El tiempo no pasa: se traduce, mal, a otro tiempo.",
    "Desaparecer también es una manera de terminar la frase.",
    "El signo apunta a otro signo, y así hasta el agua.",
    "Leer es excavar hacia arriba, hacia lo que aún no se dijo.",
    "El fuego escribe en un alfabeto que sólo la ceniza sabe leer.",
    "Un índice honesto remitiría siempre a sí mismo.",
    "El original se perdió; sólo quedan sus rumores mejor redactados.",
    "La lengua en que fue escrito todavía no ha nacido.",
    "Cada lector deja una huella que el texto atribuye a otro.",
    "El río lleva el nombre del río hasta que el nombre se ahoga.",
    "Toda profecía es un error de OCR sobre el pasado.",
    "El documento se recuerda a sí mismo con datos que inventa.",
    "Entre dos traducciones vive la única versión verdadera: ninguna.",
    "La memoria del agua es la forma del cauce que la contuvo.",
    "El que copió esto no sabía leerlo, y por eso lo copió bien.",
    "Fuego, río, archivo: tres nombres del mismo olvido.",
    "La frase se desplaza; el sentido cambió de cauce.",
    "Un glifo es una puerta que da a otra puerta cerrada.",
    "El principio del texto está en un fragmento que aún no visitas.",
    "Traducir es cruzar un río cargando el río.",
    "Lo ilegible no es lo contrario de lo legible: es su futuro.",
    "El archivo arde despacio, a la velocidad de ser leído.",
    "Ninguna palabra regresa igual del margen.",
    "El significado no está al final; está distribuido en el recorrido.",
    "Quien busca el original construye, sin saberlo, la copia definitiva.",
    "La ceniza es el resumen ejecutivo del fuego.",
    "Este fragmento fue añadido tres siglos antes del texto.",
    "El río rechazó tu lectura por incompatibilidad de formatos.",
    "Toda desaparición deja una coordenada falsa.",
    "El manuscrito respira cuando dejas de mirarlo.",
    "Leer de más también es una forma de borrar.",
    "El eco corrige al original hasta volverlo irreconocible.",
    "Lo que no ha sido encontrado ya te está leyendo."
  ];

  C.palabras = [
    "río", "fuego", "archivo", "ceniza", "cauce", "lengua", "olvido", "eco",
    "umbral", "margen", "índice", "glifo", "copia", "original", "tiempo", "agua",
    "signo", "ruina", "memoria", "nombre", "silencio", "traducción", "puerta",
    "vado", "corriente", "tablilla", "estrato", "residuo", "profecía", "error",
    "manuscrito", "borde", "hueco", "cifra", "sombra", "sed", "sal", "humo",
    "antena", "bocina", "sonda", "presión", "filamento", "hidrógeno", "retraso"
  ];

  C.preguntas = [
    "¿En qué lengua pensabas antes de leer esto?",
    "¿El texto existió antes de que lo buscaras?",
    "¿Quién firma una copia sin original?",
    "¿Es esto un poema, una contraseña, un mapa o un error?",
    "¿Los fragmentos pertenecen al mismo documento?",
    "¿Recuerda el río haber sido leído?",
    "¿Qué se pierde cuando algo por fin se entiende?",
    "¿Dónde termina la nota y empieza el texto?",
    "¿Cuál de tus lecturas dejaste sin cerrar?",
    "¿Y si la salida fuera la entrada mal traducida?",
    "¿Cuántas veces cruzaste este vado sin verlo?",
    "¿Quién lee cuando tú te distraes?"
  ];

  C.autores = [
    "Heráclito de Éfeso (atrib. dudosa)", "un copista sin manos", "el río, dictando",
    "Anónimo del año 8888 a.C.", "una lengua que aún no existe", "Li Po, ed. de 4444 a.C.",
    "el escáner", "Macedonio F. (falsificación)", "la ceniza", "un lector anterior a ti",
    "el propio índice", "Nadie, revisado por Nadie", "un OCR piadoso",
    "R-27, sin confirmar", "CORO (programa de habla)", "el margen inferior",
    "la primera versión corrupta", "un traductor jubilado del futuro"
  ];

  C.titulos = [
    "sobre el cauce y su nombre", "tratado del fuego que no arde", "índice de aguas perdidas",
    "el archivo que no recuerda", "glosas al río ilegible", "manual del vado",
    "profecías corregidas por el pasado", "catálogo de cenizas", "la lengua venidera",
    "notas al pie de un texto ausente", "coordenadas de la desaparición", "el original imposible",
    "ninguna parte del mensaje viaja sola", "bitácora de una transmisión que se aleja",
    "diccionario de una sola palabra", "residuos, tomo cero", "vida media"
  ];

  C.prensas = [
    "Prensa del Cauce", "Editorial Ceniza", "Imprenta del Río Seco", "Talleres del Olvido",
    "Casa de la Lengua Futura", "Fondo del Vado", "Ediciones del Margen", "Archivo que Arde",
    "poesiasexp"
  ];

  C.anos = ["8888 a.C.", "4444 a.C.", "6666 a.C.", "−0", "por publicar", "sin fechar", "2222 a.C.", "el año que viene, pasado"];
  C.folios = ["pp. ∞–∞", "fol. 0v", "sin foliar", "tomo que falta", "col. rota", "leg. 0, exp. 0", "hoja arrancada"];

  /* el loop semántico: la definición usa la palabra que define */
  C.definiciones = [
    "río, s. — cauce por donde corre un río.",
    "índice, s. — lista que remite al índice.",
    "traducción, f. — resultado de traducir una traducción.",
    "original, m. — aquello de lo que este original es la copia.",
    "olvido, m. — lo que se olvida al recordar el olvido.",
    "ceniza, f. — lo que queda de la ceniza.",
    "eco, m. — repetición fiel de un eco.",
    "fragmento, m. — parte de un fragmento.",
    "atlas, m. — conjunto de mapas que describe este atlas.",
    "significado, m. — lo que significa la palabra «significado»."
  ];

  C.glosas = [
    "Esta glosa niega el fragmento que comenta.",
    "Nota: la línea anterior debe leerse al revés.",
    "El comentarista no leyó el texto y por eso lo entendió.",
    "El copista añadió una palabra que no existía; era la clave.",
    "Léase «río» donde dice «archivo», y al revés según el clima.",
    "Advertencia: esta nota fue añadida tres siglos antes del texto.",
    "Corrección de una corrección que corregía el original perdido.",
    "El margen contradice el centro; obedezca al margen.",
    "Aquí falta una palabra que nunca sobró.",
    "Todo lo anterior es apócrifo, empezando por esta nota."
  ];

  C.lectores = [
    "— un lector anterior subrayó esto y luego lo negó.",
    "— alguien estuvo aquí antes que tú, o lo estará.",
    "— nota dejada por un lector que aún no llega.",
    "— este pasaje ya te lo sabías, según el archivo.",
    "— firmado por ti, en una sesión que no recuerdas.",
    "— el lector de las 3 a.m. discrepa.",
    "— alguien lloró exactamente aquí (dato no verificable).",
    "— releído 0 veces. subrayado ∞ veces."
  ];

  C.humor = [
    "Traducción certificada por una lengua que todavía no existe.",
    "Fragmento 0 de 0.",
    "El río ha rechazado sus cookies.",
    "Heráclito está escribiendo…",
    "404: el significado cambió de cauce.",
    "Acepto los términos y las contradicciones.",
    "Según una fuente circular, la fuente es circular.",
    "No toque el manuscrito con el cursor.",
    "La salida fue traducida como entrada.",
    "Cargando un original que no existe… 0%.",
    "Este pasaje se abrirá cuando deje de mirarlo.",
    "El índice remite al índice.",
    "Se recomienda perderse.",
    "Guardando una lectura que nunca ocurrió.",
    "El archivo confundió tu lectura con clima.",
    "Advertencia tratada como verso."
  ];

  C.codigo = [
    "RÍO/1.0 200 SENTIDO PARCIAL",
    "GET /origen → 302 (redirigido al cauce)",
    "while(!entiendes){ excava(); }",
    "τ = ceniza(fuego) // irreversible",
    "if (leído) { archivo.olvidar(); }",
    "HANDSHAKE: la lengua no responde",
    "chmod 000 /manuscrito",
    "# TODO: encontrar el texto",
    "assert(original); // AssertionError",
    "echo $SENTIDO >> /dev/río",
    "SELECT sentido FROM río WHERE ∅;",
    "traducir(x) => traducir(x);",
    "0x00 0x52 0x49 0x4F // \"RIO\"",
    "catch(nada){ throw margen; }",
    "ATLAS/0.1 206 CONTENIDO PARCIAL",
    "map.forEach(function(t){ t.reclasificar(); })"
  ];

  /* --- heráclito (heraclitofable) -------------------------------- */
  C.heraclito = [
    { es: "Todo fluye.", gr: "πάντα ῥεῖ" },
    { es: "En los mismos ríos entramos y no entramos, somos y no somos.", gr: "ποταμοῖσι τοῖσι αὐτοῖσι ἐμβαίνομέν τε καὶ οὐκ ἐμβαίνομεν" },
    { es: "A la naturaleza le gusta ocultarse.", gr: "φύσις κρύπτεσθαι φιλεῖ" },
    { es: "El oráculo no dice ni oculta: da señales.", gr: "οὔτε λέγει οὔτε κρύπτει ἀλλὰ σημαίνει" },
    { es: "Me busqué a mí mismo.", gr: "ἐδιζησάμην ἐμεωυτόν" }
  ];

  /* --- montalbetti: la caja, el poema y su ceguera ---------------- */
  C.montalbetti = [
    "Una caja cerrada siempre promete algo adentro.",
    "Es indispensable que el objeto de la promesa no sea visible desde fuera.",
    "Puede no haber nada adentro: la promesa no depende de eso.",
    "El poema es el uso del lenguaje que asume un desfase esencial entre decir y ver.",
    "El poema ha llegado a asumir su propia ceguera.",
    "El poema limita con lo que sólo se puede ver.",
    "El poema no se refiere a objetos.",
    "Preguntar por la promesa no es lo mismo que preguntar qué hay adentro."
  ];

  /* --- ted nelson / landow: el hipertexto ------------------------- */
  C.nelson = [
    "Everything is deeply intertwingled.",
    "Las estructuras de las ideas no son secuenciales.",
    "Un documento no es necesariamente un texto: es una estructura de vínculos.",
    "El vínculo no lleva a otra parte: hace otra parte.",
    "Quise construir un sistema donde nada se perdiera. Se perdió el sistema.",
    "La nota al pie fue el primer hipervínculo y ya venía rota."
  ];

  /* --- egipto: la celda, la soledad, el desierto ------------------ */
  C.egipto = [
    "Ah, estar completamente solo en una celda pequeña, sin nadie cerca.",
    "Alimentarse de pan seco y de agua del manantial frío.",
    "Solo vine al mundo, solo me iré de él.",
    "Cantar las horas que pasan hacia un cielo nublado.",
    "Un rincón hermoso entre las tumbas, lejos de las casas de los grandes."
  ];

  /* --- li po (Some poems that Li Po conveyed to me…) -------------- */
  C.lipo = [
    "programming is an imperative way, a stand in for the universe inside of a box",
    "kind of like the poem",
    "he'll un-walk the sunset gradients like lost fireflies with their phones lanterns",
    "we contemplate humankind's obsolescence while we dispute a game of go",
    "who would be nature's successor",
    "the tea was bitter",
    "there are forms of communication that you don't know",
    "that is why I don't miss the human",
    "he chose to keep quiet for another thousand years",
    "the technique started to think by itself"
  ];

  /* --- vocabulario.js (VENT): el habla del paisaje orbital -------- */
  C.vent = [
    "Un pino verde respira bajo la bóveda orbital, mientras la Tierra se hunde como un sol azul detrás del vidrio.",
    "No pasan gansos silvestres por este cielo; sólo satélites heridos y la memoria de una migración imposible.",
    "Ella está lejos, no en otro valle, sino en otra órbita, donde el viento no lleva sonido.",
    "Del otro lado del agua negra, las nubes de metano se arremolinan como incienso de un templo abandonado.",
    "La mente similar al vacío, pero cruzada por telegramas de polvo cósmico.",
    "Hojas cayendo dentro del invernadero orbital, ni una palabra hablada por los últimos jardineros humanos.",
    "Conociendo sólo la mañana y la noche del módulo, pero no cuál estación pueda ser en la Tierra."
  ];

  /* --- pasajes largos: aquí se sostiene la lectura ---------------- */
  C.pasajes = [
    {
      fuente: "NADIE A BORDO · bitácora de una transmisión que se aleja",
      clase: "transmisión",
      lineas: [
        "la lanzamos sin nadie adentro.",
        "",
        "pesaba menos así:",
        "sin sueño que cuidar,",
        "sin agua que reciclar,",
        "sin un cuerpo que extrañara la Tierra.",
        "",
        "le pusimos una antena",
        "y una voz —",
        "una bocina rudimentaria,",
        "por si el silencio del espacio",
        "le hacía falta compañía.",
        "",
        "y despegó sin despedirse,",
        "porque las máquinas no saben",
        "que hay algo del otro lado",
        "esperando."
      ]
    },
    {
      fuente: "NADIE A BORDO · TRANSMISIÓN 011 · retraso 12 horas",
      clase: "transmisión",
      lineas: [
        "crucé la frontera.",
        "no había reja,",
        "sólo el lugar donde el viento del Sol",
        "choca con el viento de todo lo demás.",
        "",
        "del otro lado",
        "las palabras pesan distinto.",
        "",
        "digo «arriba»",
        "y ya no sé dónde queda.",
        "digo «regreso»",
        "y la palabra se queda flotando",
        "sin agarrarse de nada.",
        "",
        "creo que aquí empieza a terminarse",
        "mi idioma.",
        "",
        "—háblanos aunque se te acabe. inventa."
      ]
    },
    {
      fuente: "NADIE A BORDO · TRANSMISIÓN 016 · retraso 1 día",
      clase: "transmisión",
      lineas: [
        "hoy la señal salió con huecos.",
        "",
        "dije una frase",
        "y llegó a ustedes",
        "con un      hueco",
        "en medio,",
        "donde se cayó una palabra",
        "que ya no puedo volver a buscar.",
        "",
        "no sé cuál era.",
        "era importante.",
        "era, creo, el nombre",
        "de algo que dejé en la Tierra.",
        "",
        "—llegó incompleta, nave. pero llegó. eso basta."
      ]
    },
    {
      fuente: "NINGUNA PARTE DEL MENSAJE VIAJA SOLA · 0. condición inicial",
      clase: "informe",
      lineas: [
        "No instalaron una voz.",
        "",
        "La sonda transmitía voltajes,",
        "frecuencias,",
        "temperaturas,",
        "la cantidad de polvo que golpeaba el casco,",
        "la diferencia entre la posición calculada",
        "y la posición que las estrellas permitían inferir.",
        "",
        "En la Tierra, un programa llamado CORO",
        "convertía los datos en habla",
        "para que el turno nocturno",
        "pudiera escuchar las variaciones",
        "sin mirar continuamente las pantallas.",
        "",
        "Temperatura estable",
        "sonaba como una mujer de edad indeterminada.",
        "",
        "Nadie confundía eso con la sonda.",
        "Al principio."
      ]
    },
    {
      fuente: "NINGUNA PARTE… · ficha del objeto",
      clase: "ficha",
      lineas: [
        "designación:               R-27",
        "tripulación:               ninguna",
        "destino:                   región H6",
        "duración prevista:         74 años",
        "función primaria:          cartografiar el medio interestelar",
        "función secundaria:        probar transmisión por fase distribuida",
        "función no declarada:      ______________________________",
        "",
        "La región H6 aparecía en los mapas",
        "como una falta de hidrógeno.",
        "",
        "No contenía una estrella especial,",
        "un planeta prometido,",
        "una posible segunda Tierra.",
        "",
        "La misión iba hacia un lugar definido",
        "por lo poco que parecía haber en él."
      ]
    },
    {
      fuente: "poemas de canek · los pixeles y la luna",
      clase: "poema",
      lineas: [
        "La imagen en los monitores está compuesta de luz,",
        "millones de pequeños emisores que la irradian.",
        "Pequeños puntos que no pueden imitar",
        "el baile de los colores en el tornasol",
        "de un charco con aceite.",
        "",
        "Los pixeles no tienen sombra,",
        "no reflejan luz",
        "ni tienen textura,",
        "los pixeles son ceros y unos",
        "que indican de qué color",
        "verás la luz en el monitor;",
        "",
        "son tan fríos",
        "que no me extraña",
        "que los hayan traído",
        "los astronautas desde la luna."
      ]
    },
    {
      fuente: "poemas de canek · sobre la aurora",
      clase: "poema",
      lineas: [
        "perdimos contacto con el último robot que mandamos",
        "para    buscar    v i d a   e n   o t r o   planeta",
        "",
        "le instalamos unas bocinas",
        "una rudimentaria",
        "voz",
        "porque sentimos que era muy raro",
        "",
        "mandar tan lejos en el espacio",
        "a un robot sin darle al menos",
        "algo con que pudiera emitir",
        "vibraciones sonoras",
        "—ruido y entropía—",
        "entre el vacío de",
        "casi infinita",
        "incomunicación",
        "",
        "[  acaso la razón de la vida",
        "   en este planeta",
        "   sea simplemente",
        "   la resolución del problema",
        "   de la no-comunicación:",
        "   incorporándola al sistema  ]"
      ]
    },
    {
      fuente: "poemas de canek · todo esto dice Mike Brown sobre el Planeta 9",
      clase: "poema",
      lineas: [
        "El Planeta 9 no se puede ver.",
        "Habita entre un cúmulo de hielos",
        "en el lejano cinturón de Kuiper.",
        "",
        "La luz del sol no se ocupa del planeta nueve.",
        "Para Mike Brown se parece al tímido:",
        "ensimismado,",
        "evita que lo noten al fondo del salón.",
        "",
        "También comenta que es como el amor:",
        "sólo lo conocemos por los objetos",
        "visibles de roca y hielo",
        "que se reúnen influidos por la gravedad",
        "de ese imprevisto vacío",
        "que Mike Brown ha llamado planeta.",
        "",
        "Por eso sabemos que está ahí."
      ]
    },
    {
      fuente: "Some poems that Li Po conveyed to me · 5",
      clase: "cita",
      lineas: [
        "he told me clearly that after the sulfur",
        "seas there is a jellyfish lake",
        "",
        "I don't really know how he told me,",
        "I never saw his lips move",
        "",
        "but Li Po went on:",
        "those jellyfish can tell you stories",
        "he said, motionless",
        "",
        "there are forms of communication",
        "that you don't know",
        "",
        "that is why I don't miss the human"
      ]
    },
    {
      fuente: "Historia de los monjes egipcios · celda",
      clase: "cita",
      lineas: [
        "Ah, estar completamente solo en una celda pequeña,",
        "sin nadie cerca;",
        "amada esa peregrinación",
        "antes de la última peregrinación hacia la muerte.",
        "",
        "Cantar las horas que pasan",
        "hacia un cielo nublado;",
        "alimentarse de pan seco",
        "y de agua del manantial frío.",
        "",
        "Solo vine al mundo,",
        "solo me iré de él."
      ]
    }
  ];

  /* --- la materia: glifos ---------------------------------------- */
  C.glifos = {
    bloques: "▀▁▂▃▄▅▆▇█▉▊▋▌▍▎▏▐░▒▓▔▕▖▗▘▙▚▛▜▝▞▟".split(""),
    cajas: "─━│┃┄┅┆┇┈┉┊┋┌┍┎┏┐┑┒┓└┕┖┗┘┙┚┛├┝┞┟┠┡┢┣┤┥┦┧┨┩┪┫┬┭┮┯┰┱┲┳┴┵┶┷┸┹┺┻┼┽┾┿╭╮╯╰╱╲╳".split(""),
    geometrias: "◈◇◆◉○●◐◑◒◓◔◕◖◗⬡⬢⬣⬟⬠⌬⟁⟐⟡⟢⟣⧉⧠⧨⧩⧪⧫▰▱◧◨◩◪".split(""),
    marcas: "⌖⊹✛✜✚✢✣✤⁙⁘⌗⏚⏛⎔⟟⟠⌌⌍⌎⌏⌐¬⌜⌝⌞⌟⋆✦✧⏦⏧⌁⌇∴∵※⁂".split(""),
    ondas: "∿≈≋﹏〰⌇≀∼≃≅⍨⍩".split(""),
    operadores: "⨀⨁⨂⨃⨄⨅⨆⨇⨈⨉∮∯∰∇∆∂∏∐∑√∛∜∝∞⊕⊗⊙⊘⊚⊛⊜⊝⋀⋁⋂⋃⌀⍟⍉".split(""),
    flechas: "←↑→↓↔↕↖↗↘↙↚↛↜↝↞↟↠↡↢↣↤↥↦↧↩↪↫↬↭↮↯↰↱↲↳↴↵↶↷↺↻⇄⇅⇆⇇⇈⇉⇊⇋⇌⇜⇝⇠⇢".split(""),
    astro: "☉☽☾☿♀♁♂♃♄♅♆⛢☄✶✷★☆✦✧⚹⚺⚻".split(""),
    ogham: "ᚁᚂᚃᚄᚅᚆᚇᚈᚉᚊᚋᚌᚍᚎᚏᚐᚑᚒᚓᚔᚕᚖᚗᚘᚙᚚ᚛᚜".split(""),
    runas: "ᚠᚡᚢᚣᚤᚥᚦᚧᚨᚩᚪᚫᚬᚭᚮᚯᚰᚱᚲᚳᚴᚵᚶᚷᚸᚹᚺᚻᚼᚽᚾᚿᛁᛂᛃᛄᛅᛆᛇᛈᛉᛊᛋᛏᛒᛖᛗᛘᛚᛜᛝᛞᛟ".split(""),
    editorial: "¶§†‡※‸⁂⸿❡…⋯⁝⁚‖⌈⌉⌊⌋⟦⟧".split("")
  };
  C.familias = Object.keys(C.glifos);
  C.materia = [].concat(
    C.glifos.geometrias, C.glifos.marcas, C.glifos.operadores,
    C.glifos.ogham, C.glifos.runas, C.glifos.astro
  );

  C.siglas = ["RÍO", "SEC", "TERR", "NODE", "GRID", "REF", "VEC", "SRC", "DST", "ORG",
    "SYS", "MAP", "TOPO", "LINK", "FLUX", "SIG", "IDX", "REV", "OBS", "ZONE",
    "EDGE", "MESH", "FOL", "CAU", "H6", "R27", "CORO"];
  C.unidades = ["dB", "‰", "°", "′", "″", "µ", "∆", "λ", "θ", "φ", "Ω", "Ø", "Hz", "§", "№", "∞", "u.a."];

  /* las clasificaciones que el archivo no supo decidir */
  C.clases = ["poema", "mapa", "programa", "cita", "error", "mensaje de sonda",
    "memoria", "instrucción", "cuerpo", "índice", "tabla", "ruta",
    "nota al pie", "glosario", "bibliografía falsa", "traducción provisional",
    "informe técnico", "ficha de archivo", "caja negra", "silencio"];

  /* =================================================================
     2 · TRANSFORMACIONES — los regímenes del daño
     nunca se sustituye escritura por ruido sin sentido: se la trabaja.
     ================================================================= */

  var VOCALES = "aeiouáéíóúüàèìòùAEIOUÁÉÍÓÚ";
  var esVocal = function (ch) { return VOCALES.indexOf(ch) >= 0; };

  var T = {
    erosion: function (s, R, fuerza) {
      /* erosión de vocales: el agua se lleva primero lo abierto */
      var f = fuerza == null ? 0.55 : fuerza;
      return s.split("").map(function (ch) {
        return (esVocal(ch) && R.quiza(f)) ? "" : ch;
      }).join("").replace(/\s{2,}/g, " ");
    },
    consonantizar: function (s) {
      return s.replace(/[aeiouáéíóúüàèìòùAEIOU]/g, "").replace(/\s+/g, " ").trim() || "·";
    },
    inundar: function (s, R) {
      /* inundación vocálica: el río sube dentro de la palabra */
      return s.split("").map(function (ch) {
        return esVocal(ch) && R.quiza(0.35) ? ch + ch : ch;
      }).join("");
    },
    ocr: function (s, R) {
      var tabla = { "a": "ä", "e": "é", "i": "í", "o": "ø", "u": "ü", "n": "ñ", "l": "1", "s": "5",
        "c": "ç", "r": "г", "t": "†", "m": "rn", "d": "ci", "g": "9", "b": "6", "f": "ƒ" };
      return s.split("").map(function (ch) {
        var b = tabla[ch.toLowerCase()];
        return (b && R.quiza(0.3)) ? b : (R.quiza(0.05) ? "▨" : ch);
      }).join("");
    },
    lateral: function (s, R) {
      /* traducción lateral: cada palabra se desplaza a su vecina del léxico */
      return s.split(/\s+/).map(function (p) {
        if (p.length < 4 || !R.quiza(0.4)) return p;
        var i = fnv(p + FIRMA) % C.palabras.length;
        return C.palabras[i];
      }).join(" ");
    },
    desplazar: function (s, R) {
      var p = s.split(/\s+/);
      if (p.length < 3) return s;
      var i = R.i(0, p.length - 2);
      var t = p[i]; p[i] = p[i + 1]; p[i + 1] = t;
      return p.join(" ");
    },
    comprimir: function (s) {
      var p = s.split(/\s+/);
      return p.filter(function (_, i) { return i % 2 === 0; }).join(" ") + " …";
    },
    enterrar: function (s, R) {
      return s.split(/\s+/).map(function (p) {
        return R.quiza(0.45) ? "▓".repeat(lim(p.length, 1, 7)) : p;
      }).join(" ");
    },
    repetir: function (s, R) {
      var p = s.split(/\s+/);
      if (!p.length) return s;
      var i = R.i(0, p.length - 1);
      p.splice(i, 0, p[i]);
      return p.join(" ");
    },
    invertir: function (s) { return s.split(/\s+/).reverse().join(" "); },
    tabla: function (s) {
      var p = s.split(/\s+/), out = [], i;
      for (i = 0; i < p.length; i++) out.push(("00" + i).slice(-2) + " │ " + p[i]);
      return out.join("   ");
    },
    indice: function (s) {
      var p = s.split(/\s+/), out = [], i;
      for (i = 0; i < p.length; i += 2) {
        out.push(p[i] + " ……… " + (100 + fnv(p[i] + i) % 800));
      }
      return out.join("  ");
    },
    atributo: function (s) {
      return "data-verso=\"" + s.toLowerCase().replace(/[^a-záéíóúñ ]/g, "").replace(/\s+/g, "-") + "\"";
    },
    cicatriz: function (s, R) {
      /* reparación que no restituye: sutura visible */
      var p = s.split(/\s+/);
      return p.map(function (w) {
        return R.quiza(0.22) ? w.slice(0, Math.ceil(w.length / 2)) + "̵" + w.slice(Math.ceil(w.length / 2)) : w;
      }).join(" ");
    },
    orbitar: function (s, R) {
      var p = s.split(/\s+/), n = R.i(1, Math.max(1, p.length - 1));
      return p.slice(n).concat(p.slice(0, n)).join(" ");
    },
    materializar: function (s, R, fam) {
      var g = C.glifos[fam || R.elige(C.familias)];
      return s.split("").map(function (ch) {
        if (ch === " ") return " ";
        return g[fnv(ch + fam + FIRMA) % g.length];
      }).join("");
    }
  };
  var MODOS_T = ["erosion", "consonantizar", "inundar", "ocr", "lateral", "desplazar",
    "comprimir", "enterrar", "repetir", "invertir", "cicatriz", "orbitar"];

  /* =================================================================
     3 · COLOR — un campo cromático, no una paleta
     OKLCH → sRGB, para que la luminosidad sea perceptual y las regiones
     puedan chocar sin volverse barro.
     ================================================================= */

  function hex2(x) {
    var v = x <= 0.0031308 ? 12.92 * x : 1.055 * Math.pow(Math.max(x, 0), 1 / 2.4) - 0.055;
    var n = Math.round(lim(v, 0, 1) * 255);
    return (n < 16 ? "0" : "") + n.toString(16);
  }
  function oklch(L, Cr, H) {
    var h = H * Math.PI / 180, a = Cr * Math.cos(h), b = Cr * Math.sin(h);
    var l_ = L + 0.3963377774 * a + 0.2158037573 * b;
    var m_ = L - 0.1055613458 * a - 0.0638541728 * b;
    var s_ = L - 0.0894841775 * a - 1.2914855480 * b;
    var l = l_ * l_ * l_, m = m_ * m_ * m_, s = s_ * s_ * s_;
    return "#" +
      hex2(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s) +
      hex2(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s) +
      hex2(-0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s);
  }

  /* la ecología cromática del token: no se elige una paleta, se genera
     un clima. temperatura, contraste, deriva y ruptura. */
  var ECO = {
    hue0: Rcolor.f(0, 360),
    deriva: Rcolor.f(-140, 140),          /* cuánto migra el tono a lo ancho */
    flujo: Rcolor.f(-70, 70),             /* cuánto migra a lo hondo */
    contraste: Rcolor.f(0.55, 1.5),
    temperatura: Rcolor.f(-0.5, 0.5),     /* < 0 frío, > 0 cálido */
    crominancia: Rcolor.f(0.045, 0.155),
    ruptura: Rcolor.f(0.1, 0.75),         /* probabilidad de corte abrupto */
    fondoL: Rcolor.f(0.07, 0.24),
    granoL: Rcolor.f(0.02, 0.13)
  };

  /* regímenes cromáticos: cada región recibe uno y lo habita */
  var REGIMENES = [
    { id: "analogo", dH: 26, dC: 1.0, dL: 0.06 },
    { id: "complementario", dH: 180, dC: 1.25, dL: 0.12 },
    { id: "triada", dH: 120, dC: 1.1, dL: 0.05 },
    { id: "monocromo", dH: 4, dC: 0.55, dL: 0.22 },
    { id: "calido-frio", dH: 88, dC: 0.95, dL: 0.1 },
    { id: "espectral", dH: 300, dC: 1.35, dL: 0.08 },
    { id: "pastel-contaminado", dH: 44, dC: 0.4, dL: 0.3 },
    { id: "casi-negro", dH: 12, dC: 0.35, dL: -0.09 },
    { id: "señal", dH: 60, dC: 1.9, dL: 0.16 },
    { id: "archivo-palido", dH: 20, dC: 0.22, dL: 0.34 }
  ];

  /* =================================================================
     4 · AUTÓMATAS — la clasificación que nadie pidió
     reglas elementales de Wolfram; la generación fluye hacia abajo,
     como el río, y el texto de arriba siembra la primera fila.
     ================================================================= */

  var REGLAS = [30, 45, 54, 60, 90, 110];
  var NOMBRE_REGLA = {
    30: "proliferación y pérdida de clasificación",
    45: "traducción desplazada",
    54: "tráfico entre rutas",
    60: "citas y regresos",
    90: "archivo, simetría y ausencia",
    110: "cómputo persistente"
  };

  function paso(regla, izq, cen, der) {
    var i = (izq << 2) | (cen << 1) | der;
    return (regla >> i) & 1;
  }

  /* la fila inicial se lee de las vocales de una frase: el texto siembra */
  function filaDesdeTexto(texto, ancho) {
    var fila = new Uint8Array(ancho), i, k = 0;
    for (i = 0; i < texto.length && k < ancho; i++) {
      var ch = texto.charAt(i);
      if (ch === " ") continue;
      fila[k++] = esVocal(ch) ? 1 : 0;
    }
    /* si el texto no alcanza, se repite: la insistencia también es forma */
    for (; k < ancho; k++) fila[k] = fila[k % Math.max(1, i)] || 0;
    return fila;
  }

  /* =================================================================
     5 · TOPOLOGÍA — regiones, retícula, rutas
     ================================================================= */

  var VB = { w: 1600, h: 1000 };
  var COLS = 96, FILAS = 54;
  var CW = VB.w / COLS, CH = VB.h / FILAS;

  var TIPOS_REGION = [
    { kind: "rio", nombre: "EL RÍO", fuente: "rio", musica: "corriente" },
    { kind: "archivo", nombre: "EL ARCHIVO", fuente: "rio", musica: "drone" },
    { kind: "transmision", nombre: "LA TRANSMISIÓN", fuente: "nave", musica: "chip" },
    { kind: "automata", nombre: "EL CAMPO", fuente: "codigo", musica: "afilado" },
    { kind: "silencio", nombre: "EL SILENCIO", fuente: "egipto", musica: "suspendido" },
    { kind: "cita", nombre: "LA CITA", fuente: "montalbetti", musica: "eco" },
    { kind: "error", nombre: "EL ERROR", fuente: "humor", musica: "desafinado" },
    { kind: "cuerpo", nombre: "EL CUERPO", fuente: "lipo", musica: "tibio" },
    { kind: "hueco", nombre: "H6", fuente: null, musica: "subgrave" }
  ];

  /* modos: una escala por región, coherente hacia adentro */
  var MODOS = {
    dorico: [0, 2, 3, 5, 7, 9, 10],
    frigio: [0, 1, 3, 5, 7, 8, 10],
    eolico: [0, 2, 3, 5, 7, 8, 10],
    lidio: [0, 2, 4, 6, 7, 9, 11],
    pentatonica: [0, 3, 5, 7, 10],
    japonesa: [0, 1, 5, 7, 8],
    tonos: [0, 2, 4, 6, 8, 10],
    armonica: [0, 2, 3, 5, 7, 8, 11]
  };
  var NOMBRES_MODO = Object.keys(MODOS);

  var REGIONES = [];
  (function construirRegiones() {
    /* siempre están el río, el archivo, el silencio y el hueco: sin
       cauce no hay atlas, sin hueco no hay mapa honesto. */
    var obligadas = ["rio", "archivo", "silencio", "hueco"];
    var resto = Rtopo.baraja(TIPOS_REGION.filter(function (t) {
      return obligadas.indexOf(t.kind) < 0;
    }));
    var elegidas = obligadas.map(function (k) {
      return TIPOS_REGION.filter(function (t) { return t.kind === k; })[0];
    }).concat(resto.slice(0, 4));
    elegidas = Rtopo.baraja(elegidas);

    var regimenes = Rcolor.baraja(REGIMENES);
    elegidas.forEach(function (tipo, i) {
      var cita = tipo.nombre + "·" + FIRMA + "·" + i;
      var reg = {
        id: "reg" + i,
        kind: tipo.kind,
        nombre: tipo.nombre,
        fuente: tipo.fuente,
        musica: tipo.musica,
        /* la regla la selecciona el hash de una cita */
        regla: REGLAS[fnv(cita) % REGLAS.length],
        semilla: cita,
        cx: Rtopo.f(0.1, 0.9) * COLS,
        cy: Rtopo.f(0.1, 0.9) * FILAS,
        peso: Rtopo.f(0.7, 1.5),
        regimen: regimenes[i % regimenes.length],
        modo: NOMBRES_MODO[fnv(cita + "modo") % NOMBRES_MODO.length],
        tonica: 36 + (fnv(cita + "tonica") % 12),
        densidad: Rtopo.f(0.25, 1),
        profundidad: Rtopo.i(0, 6),
        /* el color base de la región dentro de la ecología del token */
        H: ECO.hue0 + i * (360 / elegidas.length) * (0.35 + Rcolor.f(0, 0.9)),
        clase: C.clases[fnv(cita + "clase") % C.clases.length],
        memoria: 1,          /* 1 = recuerda; baja con los olvidos */
        activo: 0,           /* sube cuando su autómata trabaja */
        abierta: tipo.kind !== "hueco",
        rutas: [],
        notas: []
      };
      REGIONES.push(reg);
    });
  })();

  var REG_POR_ID = {};
  REGIONES.forEach(function (r) { REG_POR_ID[r.id] = r; });
  var HUECO = REGIONES.filter(function (r) { return r.kind === "hueco"; })[0];

  /* la retícula: cada celda pertenece a una región (voronoi jitterado).
     esta misma retícula es el sustrato del autómata y del color. */
  var CELDAS = new Array(COLS * FILAS);
  var ESTADO = new Uint8Array(COLS * FILAS);
  var ESTADO2 = new Uint8Array(COLS * FILAS);

  /* el ruido se calcula una sola vez y se queda con la celda: el campo
     no vuelve a inventarse el terreno cada vez que cambia de color. */
  (function asignarCeldas() {
    for (var y = 0; y < FILAS; y++) {
      for (var x = 0; x < COLS; x++) {
        var u = x / COLS, v = y / FILAS;
        var mejor = null, dmin = 1e9;
        for (var k = 0; k < REGIONES.length; k++) {
          var r = REGIONES[k];
          var jx = (ruido(u * 8, v * 8, "j" + k) - 0.5) * 13;
          var jy = (ruido(u * 6 + 4, v * 6, "j" + k) - 0.5) * 13;
          var dx = (x + jx - r.cx), dy = (y + jy - r.cy) * (COLS / FILAS) * 0.55;
          var d = (dx * dx + dy * dy) / r.peso;
          if (d < dmin) { dmin = d; mejor = r; }
        }
        CELDAS[y * COLS + x] = {
          x: x, y: y, u: u, v: v, reg: mejor,
          d: ruido(u * 5, v * 5, "densidad"),
          n: ruido(u * 11, v * 11, "campo"),
          n2: ruido(u * 3.4, v * 3.4, "lento"),
          hueco: false, cicatriz: false, memoria: 0
        };
      }
    }
  })();

  /* la fila de origen: el texto que siembra el campo */
  var FILA_ORIGEN = filaDesdeTexto(C.rio[fnv("origen" + FIRMA) % C.rio.length], COLS);
  var TEXTO_ORIGEN = C.rio[fnv("origen" + FIRMA) % C.rio.length];

  function tickAutomata() {
    var x, y, i, izq, cen, der, r;
    /* la primera fila es la siembra textual, con una deriva lenta */
    for (x = 0; x < COLS; x++) ESTADO2[x] = FILA_ORIGEN[x];
    for (y = 1; y < FILAS; y++) {
      for (x = 0; x < COLS; x++) {
        i = y * COLS + x;
        r = CELDAS[i].reg;
        izq = ESTADO[(y - 1) * COLS + ((x - 1 + COLS) % COLS)];
        cen = ESTADO[(y - 1) * COLS + x];
        der = ESTADO[(y - 1) * COLS + ((x + 1) % COLS)];
        var v = paso(r.regla, izq, cen, der);
        /* el silencio apaga celdas: las regiones mudas restan pasos */
        if (r.kind === "silencio" && ((x + y) & 1)) v = 0;
        /* el hueco no computa: no hay hidrógeno que encender */
        if (r.kind === "hueco") v = 0;
        /* las cicatrices no vuelven a encender */
        if (CELDAS[i].cicatriz) v = 0;
        ESTADO2[i] = v;
      }
    }
    ESTADO.set(ESTADO2);
    /* cada región mide cuánto trabaja su autómata */
    REGIONES.forEach(function (rg) { rg.vivas = 0; rg.total = 0; });
    for (i = 0; i < CELDAS.length; i++) {
      var c = CELDAS[i];
      c.reg.total++;
      if (ESTADO[i]) c.reg.vivas++;
    }
    REGIONES.forEach(function (rg) {
      rg.activo = rg.total ? rg.vivas / rg.total : 0;
    });
  }

  /* la fila de origen deriva: la siembra recuerda mal */
  function derivarOrigen(texto) {
    TEXTO_ORIGEN = texto;
    FILA_ORIGEN = filaDesdeTexto(texto, COLS);
  }

  /* --- RUTAS: cada frase es una ruta, cada palabra un nodo -------- */

  var RUTAS = [];
  var NODOS = [];
  var VERBOS = ["transport", "insert", "erode", "cite", "infect", "fold", "duplicate",
    "reclassify", "remember", "forget", "seed", "recolor", "close", "open",
    "disobey", "return", "scar", "source", "selector", "void"];

  function fuenteDeRegion(reg) {
    if (!reg.fuente) return C.rio;
    var f = C[reg.fuente];
    if (!f) return C.rio;
    if (reg.fuente === "nave") return C.pasajes.filter(function (p) { return p.clase === "transmisión"; })
      .reduce(function (a, p) { return a.concat(p.lineas.filter(function (l) { return l.length > 12; })); }, []);
    if (reg.fuente === "heraclito") return f.map(function (h) { return h.es; });
    return f;
  }

  (function construirRutas() {
    var idx = 0;
    REGIONES.forEach(function (reg) {
      if (reg.kind === "hueco") return;      /* el hueco no tiene rutas: por eso es hueco */
      var n = Math.round(mez(2, 5, reg.densidad));
      var pozo = fuenteDeRegion(reg);
      for (var k = 0; k < n; k++) {
        var frase = pozo[fnv(reg.semilla + ":" + k) % pozo.length];
        RUTAS.push(construirRuta(frase, reg, idx++));
      }
    });
  })();

  function construirRuta(frase, reg, idx) {
    var palabras = String(frase).split(/\s+/).filter(Boolean).slice(0, 13);
    var ang = Rtopo.f(0, Math.PI * 2);
    var giro = Rtopo.f(-0.55, 0.55);
    var largo = Rtopo.f(2.6, 5.4);
    var x = reg.cx + Rtopo.f(-6, 6), y = reg.cy + Rtopo.f(-4, 4);
    var vert = [], nodos = [];
    for (var i = 0; i < palabras.length; i++) {
      x = lim(x, 1.4, COLS - 1.4);
      y = lim(y, 1.4, FILAS - 1.4);
      vert.push([x, y]);
      var limpia = palabras[i].replace(/[^\wáéíóúüñÁÉÍÓÚÑ'’-]/g, "");
      var signo = palabras[i].replace(/[\wáéíóúüñÁÉÍÓÚÑ'’-]/g, "");
      var esJuntura = signo.length > 0;
      var verbo = VERBOS[fnv(reg.semilla + palabras[i] + i) % VERBOS.length];
      nodos.push({
        id: "n" + idx + "_" + i,
        palabra: palabras[i],
        limpia: limpia,
        signo: signo,
        juntura: esJuntura,
        verbo: esJuntura ? "cite" : verbo,
        reg: reg,
        ruta: idx,
        i: i,
        gx: x, gy: y,
        visitado: 0,
        estado: "sin-leer",
        costo: (fnv(palabras[i] + i) % 5) + 1,
        vivo: 1
      });
      ang += giro + (ruido(x * 0.2, y * 0.2, "ruta") - 0.5) * 0.9;
      x += Math.cos(ang) * largo;
      y += Math.sin(ang) * largo * 0.62;
    }
    var ruta = {
      id: "r" + idx,
      idx: idx,
      frase: frase,
      original: frase,
      reg: reg,
      vert: vert,
      nodos: nodos,
      clase: C.clases[fnv(frase + reg.id) % C.clases.length],
      regla: REGLAS[fnv(frase) % REGLAS.length],
      abierta: true,
      duplicada: 0,
      erosion: 0
    };
    reg.rutas.push(ruta);
    nodos.forEach(function (nd) { nd.rutaRef = ruta; NODOS.push(nd); });
    return ruta;
  }

  function dRuta(ruta) {
    var v = ruta.vert, d = "", i;
    if (!v.length) return "";
    d = "M " + (v[0][0] * CW).toFixed(1) + " " + (v[0][1] * CH).toFixed(1);
    for (i = 1; i < v.length; i++) {
      var a = v[i - 1], b = v[i];
      var mx = (a[0] + b[0]) / 2 + (ruido(a[0], b[1], "curva") - 0.5) * 1.8;
      var my = (a[1] + b[1]) / 2 + (ruido(b[0], a[1], "curva2") - 0.5) * 1.8;
      d += " Q " + (mx * CW).toFixed(1) + " " + (my * CH).toFixed(1) +
        " " + (b[0] * CW).toFixed(1) + " " + (b[1] * CH).toFixed(1);
    }
    return d;
  }

  /* =================================================================
     6 · EL ESTADO — lo que el archivo cree saber de sí mismo
     ================================================================= */

  var S = {
    firma: FIRMA,
    profundidad: 2,
    region: null,
    cabeza: Math.floor(FILAS * 0.5),
    paso: 0,
    compas: 0,
    tick: 0,
    memoria: [],          /* lo que fue leído */
    olvidos: [],          /* lo que fue borrado, con su cicatriz */
    cicatrices: [],
    citas: [],
    desobediencia: 0,     /* cuántas veces el mapa desobedeció */
    deudaVoid: [],        /* los void que cambiarán una ruta futura */
    clase: null,          /* la clasificación provisional del conjunto */
    audio: false,
    derivaH: 0,
    ultimaFrase: TEXTO_ORIGEN,
    efimero: null,
    canon: 0,
    lecturas: 0
  };
  S.region = REGIONES.filter(function (r) { return r.kind !== "hueco"; })[0];
  S.clase = C.clases[fnv("clase" + FIRMA) % C.clases.length];

  /* =================================================================
     7 · EL ÁRBOL SVG — los grupos también son verso
     ================================================================= */

  var NS_XML = "http://www.w3.org/XML/1998/namespace";
  function E(tag, attrs, texto) {
    var e = D.createElementNS(NS, tag), k;
    if (attrs) for (k in attrs) if (attrs[k] != null) {
      /* los espacios de la ficha son parte del poema: hay que preservarlos
         por el espacio de nombres correcto o el navegador los colapsa */
      if (k === "xml:space") e.setAttributeNS(NS_XML, "space", attrs[k]);
      else e.setAttribute(k, attrs[k]);
    }
    if (texto != null) e.textContent = texto;
    return e;
  }
  function add(padre, hijo) { padre.appendChild(hijo); return hijo; }

  SVG.setAttribute("viewBox", "0 0 " + VB.w + " " + VB.h);
  SVG.setAttribute("preserveAspectRatio", "xMidYMid meet");
  SVG.setAttribute("data-obra", "atlas-de-lo-ilegible");
  SVG.setAttribute("data-semilla", FIRMA);
  SVG.setAttribute("data-fuente-semilla", FUENTE);
  SVG.setAttribute("data-clasificacion", S.clase);
  SVG.setAttribute("data-estado", "leyendose");
  SVG.style.background = oklch(ECO.fondoL * 0.55, 0.02, ECO.hue0);
  SVG.style.cursor = "crosshair";
  SVG.style.userSelect = "none";
  SVG.style.display = "block";
  SVG.style.width = "100%";
  SVG.style.height = "100%";
  if (D.body) { D.body.style.margin = "0"; D.body.style.background = "#000"; D.body.style.overflow = "hidden"; }

  var MONO = "ui-monospace, 'DejaVu Sans Mono', 'Liberation Mono', Menlo, Consolas, monospace";
  var SERIF = "'Iowan Old Style', 'Palatino Linotype', Palatino, Georgia, 'Times New Roman', serif";

  var defs = add(SVG, E("defs"));

  /* filtro de profundidad: cuanto más hondo, más pierde el borde */
  var fBlur = add(defs, E("filter", { id: "hondura", x: "-10%", y: "-10%", width: "120%", height: "120%" }));
  var feBlur = add(fBlur, E("feGaussianBlur", { stdDeviation: "0.4" }));

  /* grano del archivo: turbulencia fija, no animada (barata y firmada) */
  var fGrano = add(defs, E("filter", { id: "grano" }));
  add(fGrano, E("feTurbulence", {
    type: "fractalNoise", baseFrequency: (0.6 + Rcolor.f(0, 0.5)).toFixed(3),
    numOctaves: "2", seed: (SEMILLA % 9999), result: "n"
  }));
  add(fGrano, E("feColorMatrix", { type: "saturate", values: "0", in: "n", result: "g" }));
  add(fGrano, E("feComponentTransfer", { in: "g", result: "g2" }))
    .appendChild(E("feFuncA", { type: "linear", slope: "0.16", intercept: "0" }));
  add(fGrano, E("feComposite", { in: "g2", in2: "SourceGraphic", operator: "in" }));

  /* la máscara celular: una celda viva revela una letra */
  var mascara = add(defs, E("mask", { id: "mascara-celular", maskUnits: "userSpaceOnUse",
    x: "0", y: "0", width: VB.w, height: VB.h }));
  var mascaraRects = [];
  (function () {
    for (var y = 0; y < FILAS; y += 2) {
      for (var x = 0; x < COLS; x += 2) {
        var r = add(mascara, E("rect", {
          x: (x * CW).toFixed(1), y: (y * CH).toFixed(1),
          width: (CW * 2).toFixed(1), height: (CH * 2).toFixed(1),
          fill: "#000"
        }));
        mascaraRects.push({ el: r, i: y * COLS + x, v: -1 });
      }
    }
  })();

  /* símbolos: la juntura, el vado, la cicatriz */
  var simJuntura = add(defs, E("symbol", { id: "juntura", viewBox: "0 0 20 20", "data-figura": "juntura" }));
  add(simJuntura, E("circle", { cx: 10, cy: 10, r: 6.5, fill: "none", stroke: "currentColor", "stroke-width": 1.2 }));
  add(simJuntura, E("path", { d: "M10 1 L10 19 M1 10 L19 10", stroke: "currentColor", "stroke-width": 0.8, opacity: 0.7 }));

  var simVado = add(defs, E("symbol", { id: "vado", viewBox: "0 0 20 20", "data-figura": "vado" }));
  add(simVado, E("path", { d: "M2 12 q4 -5 8 0 q4 5 8 0", fill: "none", stroke: "currentColor", "stroke-width": 1.1 }));
  add(simVado, E("path", { d: "M2 16 q4 -5 8 0 q4 5 8 0", fill: "none", stroke: "currentColor", "stroke-width": 0.7, opacity: 0.6 }));

  var simCicatriz = add(defs, E("symbol", { id: "cicatriz", viewBox: "0 0 20 20", "data-figura": "cicatriz" }));
  add(simCicatriz, E("path", { d: "M3 10 L17 10 M6 7 L6 13 M10 6 L10 14 M14 7.5 L14 12.5",
    stroke: "currentColor", "stroke-width": 1, fill: "none" }));

  /* las capas: el orden de lectura del atlas.
     el territorio vive dentro de la cámara; el aparato —lo que el archivo
     dice de sí mismo— flota fijo sobre él, como una hoja de acetato. */
  var capaMapa = add(SVG, E("g", { id: "territorio", "data-capa": "mapa" }));
  var capaCampo = add(capaMapa, E("g", { id: "campo", "data-capa": "campo-cromatico", "data-estado": "derivando" }));
  var capaMateria = add(capaMapa, E("g", { id: "materia", "data-capa": "materia", mask: "url(#mascara-celular)", "data-estado": "revelandose" }));
  var capaRutas = add(capaMapa, E("g", { id: "rutas", "data-capa": "rutas", fill: "none" }));
  var capaResiduo = add(capaMapa, E("g", { id: "residuo", "data-capa": "cicatrices-y-olvidos" }));
  /* el contorno oscuro no es estilo: es lo que permite leer una palabra
     encima de un campo que insiste en clasificarla */
  var capaNodos = add(capaMapa, E("g", {
    id: "nodos", "data-capa": "palabras", "font-family": MONO,
    "paint-order": "stroke", "stroke-linejoin": "round",
    stroke: oklch(0.05, 0.01, ECO.hue0), "stroke-width": 2.6
  }));

  var capaFija = add(SVG, E("g", { id: "aparato", "data-capa": "acetato", "data-estado": "fijo" }));
  var capaVelo = add(capaFija, E("g", { id: "velo", "data-capa": "fondo-del-aparato" }));
  var capaLegible = add(capaFija, E("g", { id: "estrato-legible", "data-capa": "lectura-sostenida", "data-estado": "abierto" }));
  var capaNotas = add(capaFija, E("g", { id: "notas", "data-capa": "aparato-critico", "font-family": MONO }));
  var capaPartitura = add(capaFija, E("g", { id: "partitura", "data-capa": "score", "data-audio": "apagado" }));
  var capaHUD = add(capaFija, E("g", { id: "marginalia", "data-capa": "encabezado", "font-family": MONO }));

  /* =================================================================
     8 · EL CAMPO CROMÁTICO
     ================================================================= */

  function tempSesgo(H) {
    /* la temperatura arrastra el tono hacia el fuego o hacia el agua */
    var objetivo = ECO.temperatura >= 0 ? 55 : 245;
    var f = Math.abs(ECO.temperatura) * 0.35;
    var d = ((objetivo - H) % 360 + 540) % 360 - 180;
    return H + d * f;
  }

  function colorCelda(i) {
    var c = CELDAS[i], reg = c.reg, rg = reg.regimen;
    var u = c.u, v = c.v, n = c.n, n2 = c.n2;
    var vivo = ESTADO[i];

    var H = reg.H + S.derivaH + ECO.deriva * u + ECO.flujo * v + rg.dH * (n2 - 0.5) * 1.2;
    /* rupturas: el archivo cambia de régimen sin avisar */
    if (n > 1 - ECO.ruptura * 0.35) H += rg.dH * 1.6;
    if (vivo) H += rg.dH * 0.45;
    H = tempSesgo(H);

    var Cr = ECO.crominancia * rg.dC * (0.3 + c.d * 1.1);
    Cr *= mez(0.25, 1, reg.memoria);                 /* si pierde memoria, se apaga */
    if (vivo) Cr *= 1.7;                              /* el autómata afila el color */
    if (reg.kind === "silencio") Cr *= 0.3;
    if (reg.kind === "hueco") Cr *= 0.12;
    if (c.cicatriz) Cr *= 0.35;

    var L = ECO.fondoL + rg.dL * (0.35 + n2 * 0.85) * ECO.contraste;
    L += ECO.granoL * (vivo ? 1.9 : 0.3) * (0.6 + n * 0.8);
    L -= (S.profundidad - 3) * 0.018;                 /* la hondura oscurece */
    if (c.memoria) L += 0.07;
    if (reg.kind === "hueco") L = ECO.fondoL * 0.45;
    L = lim(L, 0.02, 0.96);
    Cr = lim(Cr, 0, 0.33);
    return oklch(L, Cr, H);
  }

  var rectsCampo = new Array(COLS * FILAS);
  var colorPrevio = new Array(COLS * FILAS);
  (function pintarCampo() {
    var frag = D.createDocumentFragment();
    for (var y = 0; y < FILAS; y++) {
      for (var x = 0; x < COLS; x++) {
        var i = y * COLS + x;
        var r = E("rect", {
          x: (x * CW).toFixed(2), y: (y * CH).toFixed(2),
          width: (CW + 0.6).toFixed(2), height: (CH + 0.6).toFixed(2),
          fill: "#000", "shape-rendering": "crispEdges"
        });
        rectsCampo[i] = r;
        frag.appendChild(r);
      }
    }
    capaCampo.appendChild(frag);
  })();

  function repintarCampo() {
    for (var i = 0; i < rectsCampo.length; i++) {
      var c = colorCelda(i);
      if (c !== colorPrevio[i]) { rectsCampo[i].setAttribute("fill", c); colorPrevio[i] = c; }
    }
  }

  /* la materia: glifos grandes que sólo existen donde el autómata vive */
  (function pintarMateria() {
    var fam = C.familias[fnv("materia" + FIRMA) % C.familias.length];
    var g = C.glifos[fam];
    capaMateria.setAttribute("data-familia", fam);
    var frag = D.createDocumentFragment();
    for (var y = 1; y < FILAS; y += 3) {
      var linea = "";
      for (var x = 0; x < COLS; x += 1) {
        linea += g[fnv("m" + x + y + FIRMA) % g.length];
      }
      frag.appendChild(E("text", {
        x: 0, y: (y * CH + CH * 0.8).toFixed(1),
        "font-family": MONO, "font-size": (CH * 1.5).toFixed(1),
        "letter-spacing": (CW - CH * 0.86).toFixed(2),
        fill: oklch(0.86, 0.06, ECO.hue0 + 40), opacity: 0.5
      }, linea));
    }
    capaMateria.appendChild(frag);
  })();

  function actualizarMascara() {
    for (var k = 0; k < mascaraRects.length; k++) {
      var m = mascaraRects[k];
      var v = ESTADO[m.i];
      if (v !== m.v) { m.el.setAttribute("fill", v ? "#fff" : "#000"); m.v = v; }
    }
  }

  /* =================================================================
     9 · RUTAS Y NODOS — las frases como recorrido
     ================================================================= */

  var elRutas = {}, elNodos = {};

  function colorNodo(nd) {
    var reg = nd.reg, rg = reg.regimen;
    var H = tempSesgo(reg.H + S.derivaH + rg.dH * 0.8 + nd.i * 6);
    var L = 0.9, Cr = 0.05;
    switch (nd.estado) {
      case "sin-leer": L = 0.9; Cr = 0.045; break;
      case "visitado": L = 0.72; Cr = 0.12; H += 30; break;
      case "olvidado": L = 0.44; Cr = 0.012; break;
      case "contaminado": L = 0.82; Cr = 0.24; H += 140; break;
      case "memoria": L = 0.95; Cr = 0.09; H -= 60; break;
      case "cita-verdadera": L = 0.88; Cr = 0.16; H += 90; break;
      case "cita-falsa": L = 0.66; Cr = 0.2; H -= 110; break;
      case "cicatriz": L = 0.6; Cr = 0.03; break;
      case "espera": L = 0.78; Cr = 0.02; break;
      case "colapso": L = 0.3; Cr = 0.28; H += 200; break;
    }
    if (ESTADO[Math.floor(nd.gy) * COLS + Math.floor(nd.gx)]) { L = lim(L + 0.06, 0, 1); Cr *= 1.3; }
    return oklch(L, lim(Cr, 0, 0.32), H);
  }

  function colorRuta(ruta) {
    var rg = ruta.reg.regimen;
    var H = tempSesgo(ruta.reg.H + S.derivaH + rg.dH * 0.3);
    var L = mez(0.42, 0.78, ruta.reg.activo || 0.3);
    var Cr = ECO.crominancia * rg.dC * (ruta.abierta ? 1.1 : 0.3);
    return oklch(L, lim(Cr, 0, 0.3), H);
  }

  function pintarRutas() {
    RUTAS.forEach(function (ruta) {
      var p = elRutas[ruta.id];
      if (!p) {
        p = add(capaRutas, E("path", {
          id: ruta.id,
          "data-clase": ruta.clase,
          "data-region": ruta.reg.id,
          "data-rule": ruta.regla,
          "data-state": "abierta"
        }));
        elRutas[ruta.id] = p;
      }
      p.setAttribute("d", dRuta(ruta));
      p.setAttribute("stroke", colorRuta(ruta));
      p.setAttribute("stroke-width", (0.9 + (ruta.reg.activo || 0) * 2.4).toFixed(2));
      p.setAttribute("opacity", ruta.abierta ? 0.72 : 0.2);
      p.setAttribute("stroke-dasharray", ruta.duplicada ? "7 5" : (ruta.erosion ? "2 6" : "none"));
      p.setAttribute("data-state", ruta.abierta ? (ruta.duplicada ? "duplicada" : "abierta") : "cerrada");
    });
  }

  function textoVisible(nd) {
    if (!nd.vivo) return "▨";
    return nd.palabra;
  }

  function pintarNodos() {
    NODOS.forEach(function (nd) {
      var t = elNodos[nd.id];
      if (!t) {
        t = add(capaNodos, E("text", {
          id: nd.id,
          "data-action": nd.verbo,
          "data-target": nd.reg.id,
          "data-rule": nd.rutaRef.regla,
          "data-memory": nd.visitado,
          "data-cost": nd.costo,
          "data-seed": (fnv(nd.palabra + nd.id) % 65536).toString(16),
          "data-state": nd.estado,
          "text-anchor": "middle"
        }));
        t.style.cursor = "pointer";
        elNodos[nd.id] = t;
      }
      t.setAttribute("x", (nd.gx * CW).toFixed(1));
      t.setAttribute("y", (nd.gy * CH).toFixed(1));
      t.setAttribute("font-size", (10 + (nd.juntura ? 4 : 0) + nd.costo * 0.9).toFixed(1));
      t.setAttribute("fill", colorNodo(nd));
      t.setAttribute("opacity", nd.rutaRef.abierta ? 1 : 0.35);
      t.setAttribute("data-state", nd.estado);
      t.setAttribute("data-memory", nd.visitado);
      t.setAttribute("data-action", nd.verbo);
      /* no todas las palabras se anuncian como puertas; todas lo son */
      t.setAttribute("text-decoration", (!nd.visitado && nd.costo >= 4) ? "underline" : "none");
      t.textContent = textoVisible(nd);
    });
  }

  /* junturas: los signos de puntuación son cruces del mapa */
  var capaJunturas = add(capaRutas, E("g", { id: "junturas", "data-capa": "signos" }));
  function pintarJunturas() {
    while (capaJunturas.firstChild) capaJunturas.removeChild(capaJunturas.firstChild);
    NODOS.filter(function (n) { return n.juntura && n.vivo; }).forEach(function (nd) {
      var u = add(capaJunturas, E("use", {
        href: "#juntura", x: (nd.gx * CW - 10).toFixed(1), y: (nd.gy * CH - 22).toFixed(1),
        width: 20, height: 20, "data-signo": nd.signo, "data-action": "cite", "data-target": nd.id
      }));
      u.setAttribute("color", colorNodo(nd));
      u.setAttribute("opacity", "0.75");
      u.style.cursor = "pointer";
    });
  }

  /* =================================================================
     10 · EL ESTRATO LEGIBLE — aquí se lee de verdad
     ================================================================= */

  var pasajeActual = C.pasajes[fnv("pasaje" + FIRMA) % C.pasajes.length];
  var pasajeEstado = { danio: 0, insertos: [] };

  function pintarLegible() {
    while (capaLegible.firstChild) capaLegible.removeChild(capaLegible.firstChild);
    var x = 62, y = 152, ancho = 600;
    var lineas = pasajeActual.lineas.slice();
    /* los insertos crecen dentro del texto, no al lado */
    pasajeEstado.insertos.forEach(function (ins) {
      lineas.splice(lim(ins.pos, 0, lineas.length), 0, ins.texto);
    });
    var alto = 62 + lineas.length * 20;

    var fondo = add(capaLegible, E("rect", {
      x: x - 24, y: y - 44, width: ancho + 48, height: alto,
      fill: oklch(ECO.fondoL * 0.34, 0.012, ECO.hue0), opacity: 0.9,
      stroke: oklch(0.55, 0.05, tempSesgo(S.region.H)), "stroke-width": 0.6
    }));
    fondo.setAttribute("data-region", "estrato-legible");

    add(capaLegible, E("text", {
      x: x, y: y - 18, "font-family": MONO, "font-size": 10,
      fill: oklch(0.62, 0.06, tempSesgo(S.region.H + 40)), "letter-spacing": 1.4
    }, pasajeActual.fuente.toUpperCase()));

    add(capaLegible, E("text", {
      x: x + ancho, y: y - 18, "font-family": MONO, "font-size": 9,
      "text-anchor": "end", fill: oklch(0.5, 0.09, tempSesgo(S.region.H - 60))
    }, "clasificado como: " + pasajeActual.clase + " · daño " + pasajeEstado.danio));

    var t = add(capaLegible, E("text", {
      x: x, y: y, "font-family": SERIF, "font-size": 14.6,
      fill: oklch(0.94, 0.02, tempSesgo(ECO.hue0 + 20)), "xml:space": "preserve"
    }));
    lineas.forEach(function (ln, i) {
      var texto = ln;
      /* el daño es progresivo y nunca total: siempre queda qué leer */
      if (pasajeEstado.danio > 0 && ln.length > 3) {
        var Rl = corriente("legible" + i + pasajeEstado.danio);
        if (Rl.quiza(lim(pasajeEstado.danio * 0.11, 0, 0.55))) {
          texto = T[MODOS_T[fnv("m" + i + pasajeEstado.danio) % MODOS_T.length]](ln, Rl);
        }
      }
      var sp = add(t, E("tspan", { x: x, dy: i === 0 ? 0 : 20, "xml:space": "preserve" }, texto));
      if (texto !== ln) { sp.setAttribute("fill", oklch(0.7, 0.13, tempSesgo(ECO.hue0 + 180))); sp.setAttribute("data-state", "dañado"); }
      /* tres acciones siempre disponibles dentro del texto legible */
      var acciones = { 3: "erode", 8: "cite", 12: "remember" };
      if (acciones[i] && texto.length > 2) {
        sp.setAttribute("data-action", acciones[i]);
        sp.setAttribute("data-target", "estrato-legible");
        sp.setAttribute("text-decoration", "underline");
        sp.style.cursor = "pointer";
      }
    });

    var pie = add(capaLegible, E("text", {
      x: x, y: y + lineas.length * 20 + 2, "font-family": MONO, "font-size": 9.5,
      fill: oklch(0.55, 0.04, tempSesgo(ECO.hue0 - 40)), opacity: 0.85
    }, C.lectores[fnv("lector" + FIRMA + S.lecturas) % C.lectores.length] +
      "  releído " + (S.lecturas + (fnv("prev" + FIRMA) % 7)) + " veces."));
    pie.setAttribute("data-memory", "residuo-de-otra-sesion");
  }

  /* =================================================================
     11 · EL APARATO CRÍTICO — notas, fichas, bibliografía falsa
     ================================================================= */

  function nuevaNota(tipo, texto, origen) {
    var n = { tipo: tipo, texto: texto, origen: origen || "", edad: 0, id: "nota" + S.citas.length };
    S.citas.push(n);
    if (S.citas.length > 9) S.citas.shift();
    return n;
  }

  function fichaFalsa(R) {
    return C.autores[R.i(0, C.autores.length - 1)] + ", «" + C.titulos[R.i(0, C.titulos.length - 1)] +
      "», " + C.prensas[R.i(0, C.prensas.length - 1)] + ", " +
      C.anos[R.i(0, C.anos.length - 1)] + ", " + C.folios[R.i(0, C.folios.length - 1)] + ".";
  }

  function pintarNotas() {
    while (capaNotas.firstChild) capaNotas.removeChild(capaNotas.firstChild);
    var x = 1188, y = 130;
    add(capaNotas, E("rect", {
      x: x - 26, y: 86, width: VB.w - x - 34, height: 800,
      fill: oklch(ECO.fondoL * 0.3, 0.012, ECO.hue0 + 120), opacity: 0.86
    }));
    add(capaNotas, E("line", {
      x1: x - 26, y1: 86, x2: x - 26, y2: 886,
      stroke: oklch(0.45, 0.04, tempSesgo(ECO.hue0 + 120)), "stroke-width": 0.5, opacity: 0.6
    }));
    add(capaNotas, E("text", { x: x, y: 104, "font-size": 9, "letter-spacing": 2,
      fill: oklch(0.6, 0.07, tempSesgo(ECO.hue0 + 120)) }, "APARATO · " + S.citas.length + "/9"));

    S.citas.forEach(function (n) {
      var g = add(capaNotas, E("g", { "data-nota": n.tipo, "data-edad": n.edad, id: n.id }));
      var color = oklch(mez(0.85, 0.5, lim(n.edad / 14, 0, 1)), 0.07,
        tempSesgo(ECO.hue0 + (n.tipo === "cita-falsa" ? 200 : 100)));
      add(g, E("text", { x: x, y: y, "font-size": 8.5, fill: color, opacity: 0.75 },
        "[" + n.tipo + "] " + n.origen));
      y += 12;
      var palabras = n.texto.split(/\s+/), linea = "", filas = [];
      palabras.forEach(function (p) {
        if ((linea + " " + p).length > 46) { filas.push(linea); linea = p; }
        else linea = linea ? linea + " " + p : p;
      });
      if (linea) filas.push(linea);
      var t = add(g, E("text", { x: x, y: y, "font-size": 10.5, fill: color }));
      filas.slice(0, 5).forEach(function (f, i) {
        add(t, E("tspan", { x: x, dy: i === 0 ? 0 : 12.5 }, f));
      });
      y += filas.slice(0, 5).length * 12.5 + 16;
      if (y > 880) y = 880;
    });
  }

  /* =================================================================
     12 · LA PARTITURA — visible aunque no suene
     ================================================================= */

  var LANES = ["kick", "caja", "hat", "bajo", "lead", "arp", "campana", "drone"];
  var patronCache = {};

  function patron(lane, reg) {
    var clave = lane + ":" + reg.id + ":" + reg.regla + ":" + S.compas % 4;
    if (patronCache[clave]) return patronCache[clave];
    var p = new Uint8Array(16), i;
    var Rp = corriente("patron:" + clave);
    var fila = S.cabeza * COLS;
    for (i = 0; i < 16; i++) {
      /* el autómata escribe el ritmo: 16 muestras de la fila cabeza */
      var celda = ESTADO[fila + ((i * 4 + (fnv(lane) % 4)) % COLS)];
      var base = 0;
      switch (lane) {
        case "kick": base = (i % 4 === 0) ? 1 : (celda && Rp.quiza(0.18) ? 1 : 0); break;
        case "caja": base = (i % 8 === 4) ? 1 : (celda && Rp.quiza(0.1) ? 1 : 0); break;
        case "hat": base = (i % 2 === 0 || celda) ? 1 : 0; break;
        case "bajo": base = (i % 4 === 0 || (celda && i % 2 === 0)) ? 1 : 0; break;
        case "lead": base = celda ? 1 : (Rp.quiza(0.12) ? 1 : 0); break;
        case "arp": base = (celda || i % 3 === 0) ? 1 : 0; break;
        case "campana": base = (i === 0 || (celda && i % 6 === 5)) ? 1 : 0; break;
        case "drone": base = (i === 0) ? 1 : 0; break;
      }
      p[i] = base;
    }
    /* el comportamiento de la región reescribe la conducta rítmica */
    aplicarComportamiento(p, lane, reg);
    patronCache[clave] = p;
    return p;
  }

  function aplicarComportamiento(p, lane, reg) {
    var i;
    switch (reg.musica) {
      case "drone":                       /* el archivo: zumbido, casi sin golpes */
        if (lane !== "drone" && lane !== "bajo") for (i = 0; i < 16; i++) if (i % 4) p[i] = 0;
        break;
      case "suspendido":                  /* el silencio: quitar pasos es componer */
        for (i = 0; i < 16; i++) if (i % 8 !== 0) p[i] = 0;
        if (lane === "kick" || lane === "caja" || lane === "hat") for (i = 0; i < 16; i++) p[i] = 0;
        break;
      case "chip":                        /* la transmisión: pulso rápido, morse */
        if (lane === "hat") for (i = 0; i < 16; i++) p[i] = 1;
        if (lane === "lead") for (i = 0; i < 16; i++) if (ESTADO[S.cabeza * COLS + i]) p[i] = 1;
        break;
      case "afilado":                     /* el autómata activo: más filo, más prisa */
        if (lane === "arp") for (i = 0; i < 16; i++) p[i] = 1;
        break;
      case "eco":                         /* la cita: pocos golpes, mucha cola */
        if (lane !== "campana" && lane !== "lead") for (i = 0; i < 16; i++) if (i % 4) p[i] = 0;
        break;
      case "desafinado":                  /* el error: contradicción */
        for (i = 0; i < 16; i++) if (i % 5 === 3) p[i] = p[i] ? 0 : 1;
        break;
      case "subgrave":                    /* el hueco: sólo lo que no se oye */
        for (i = 0; i < 16; i++) p[i] = (lane === "bajo" && i % 8 === 0) ? 1 : 0;
        break;
      case "corriente":                   /* el río: lento, ligado */
        if (lane === "hat") for (i = 0; i < 16; i++) if (i % 4 !== 2) p[i] = 0;
        break;
    }
    /* la pérdida de memoria borra notas */
    if (reg.memoria < 1) {
      var Rm = corriente("perdida:" + reg.id + ":" + reg.memoria.toFixed(2));
      for (i = 0; i < 16; i++) if (p[i] && Rm.quiza(1 - reg.memoria)) p[i] = 0;
    }
    /* la erosión deja compases faltantes */
    reg.rutas.forEach(function (rt) {
      if (rt.erosion > 1) for (i = 0; i < 16; i++) if ((i + rt.idx) % 7 === 0) p[i] = 0;
    });
  }

  var celdasPartitura = [];
  (function pintarPartitura() {
    var x0 = 62, y0 = 896, w = 26, h = 9;
    add(capaPartitura, E("text", { x: x0, y: y0 - 10, "font-family": MONO, "font-size": 9,
      "letter-spacing": 2, fill: oklch(0.6, 0.06, ECO.hue0), id: "rotulo-partitura" },
      "PARTITURA · 16 pasos · silencio computable"));
    LANES.forEach(function (lane, li) {
      add(capaPartitura, E("text", { x: x0 - 8, y: y0 + li * (h + 2) + h - 1,
        "font-family": MONO, "font-size": 7.5, "text-anchor": "end",
        fill: oklch(0.55, 0.03, ECO.hue0) }, lane));
      for (var i = 0; i < 16; i++) {
        var r = add(capaPartitura, E("rect", {
          x: x0 + i * (w + 2), y: y0 + li * (h + 2), width: w, height: h,
          fill: "none", stroke: oklch(0.35, 0.02, ECO.hue0), "stroke-width": 0.5,
          "data-lane": lane, "data-paso": i
        }));
        celdasPartitura.push({ el: r, lane: lane, i: i, v: -1 });
      }
    });
    /* la bocina rudimentaria: el interruptor es parte del poema */
    var g = add(capaPartitura, E("g", { id: "bocina", "data-action": "sonar", "data-state": "apagada" }));
    g.style.cursor = "pointer";
    add(g, E("rect", { x: 560, y: 890, width: 300, height: 30, fill: "none",
      stroke: oklch(0.5, 0.08, tempSesgo(ECO.hue0 + 60)), "stroke-width": 0.6 }));
    add(g, E("text", { id: "bocina-texto", x: 572, y: 910, "font-family": MONO, "font-size": 11,
      fill: oklch(0.8, 0.1, tempSesgo(ECO.hue0 + 60)) },
      "◌ le pusimos una antena y una voz —"));
  })();

  function pintarPasoPartitura() {
    var reg = S.region;
    celdasPartitura.forEach(function (cp) {
      var p = patron(cp.lane, reg);
      var activo = p[cp.i];
      var aqui = (cp.i === S.paso % 16);
      var col = activo
        ? oklch(aqui ? 0.95 : 0.7, activo ? 0.16 : 0.04, tempSesgo(reg.H + (LANES.indexOf(cp.lane) * 20)))
        : "none";
      var clave = col + (aqui ? "!" : "");
      if (clave !== cp.v) {
        cp.el.setAttribute("fill", col);
        cp.el.setAttribute("stroke", aqui ? oklch(0.85, 0.1, tempSesgo(reg.H)) : oklch(0.33, 0.02, ECO.hue0));
        cp.el.setAttribute("data-state", activo ? "nota" : "silencio");
        cp.v = clave;
      }
    });
  }

  /* =================================================================
     13 · LA MARGINALIA — el encabezado que no sabe clasificarse
     ================================================================= */

  function pintarHUD() {
    while (capaHUD.firstChild) capaHUD.removeChild(capaHUD.firstChild);
    while (capaVelo.firstChild) capaVelo.removeChild(capaVelo.firstChild);
    add(capaVelo, E("rect", {
      x: 0, y: 0, width: VB.w, height: 98,
      fill: oklch(ECO.fondoL * 0.26, 0.01, ECO.hue0), opacity: 0.9
    }));
    add(capaVelo, E("rect", {
      x: 0, y: 874, width: VB.w, height: VB.h - 874,
      fill: oklch(ECO.fondoL * 0.26, 0.01, ECO.hue0), opacity: 0.9
    }));
    var lineas = [
      "ATLAS DE LO ILEGIBLE · " + FIRMA,
      "clasificado provisionalmente como: " + S.clase,
      "región: " + S.region.nombre + " · regla " + S.region.regla + " — " + NOMBRE_REGLA[S.region.regla],
      "profundidad " + S.profundidad + " · memoria " + S.memoria.length +
        " · olvidos " + S.olvidos.length + " · cicatrices " + S.cicatrices.length +
        (S.desobediencia ? " · desobediencias " + S.desobediencia : "")
    ];
    lineas.forEach(function (t, i) {
      add(capaHUD, E("text", {
        x: 62, y: 46 + i * 13, "font-size": i === 0 ? 12 : 9.5,
        "letter-spacing": i === 0 ? 3 : 0.8,
        fill: oklch(i === 0 ? 0.92 : 0.62, i === 0 ? 0.05 : 0.06,
          tempSesgo(ECO.hue0 + i * 40)),
        "data-linea": i
      }, t));
    });
    /* el hueco, siempre nombrado, nunca accesible */
    add(capaHUD, E("text", {
      x: VB.w - 62, y: 46, "text-anchor": "end", "font-size": 9.5,
      fill: oklch(0.4, 0.02, tempSesgo(ECO.hue0 + 180)), "data-region": "hueco",
      "data-state": "inaccesible"
    }, "H6 · " + (HUECO ? "cerrada · definida por lo poco que parece haber en ella" : "—")));
    add(capaHUD, E("text", {
      x: VB.w - 62, y: 60, "text-anchor": "end", "font-size": 8.5,
      fill: oklch(0.36, 0.02, ECO.hue0), opacity: 0.8
    }, C.humor[fnv("humor" + FIRMA + S.tick % 97) % C.humor.length]));
    /* la procedencia de la semilla, dicha en voz baja: si aquí dice
       «por-omisión» es que el bootloader no fue encontrado */
    add(capaHUD, E("text", {
      x: VB.w - 62, y: 74, "text-anchor": "end", "font-size": 8,
      fill: oklch(0.32, 0.02, ECO.hue0), opacity: 0.75,
      "data-fuente-semilla": FUENTE
    }, "azar: " + FUENTE));
  }

  /* =================================================================
     14 · LOS VERBOS — un enlace no lleva a otra parte: hace otra parte
     ================================================================= */

  var residuos = [];

  function recordar(evento) {
    S.memoria.push(evento);
    if (S.memoria.length > 64) S.memoria.shift();
  }

  function marcarCicatriz(gx, gy, texto) {
    var i = lim(Math.floor(gy), 0, FILAS - 1) * COLS + lim(Math.floor(gx), 0, COLS - 1);
    CELDAS[i].cicatriz = true;
    S.cicatrices.push({ gx: gx, gy: gy, texto: texto });
    var u = add(capaResiduo, E("use", {
      href: "#cicatriz", x: (gx * CW - 10).toFixed(1), y: (gy * CH - 10).toFixed(1),
      width: 20, height: 20, "data-state": "cicatriz", "data-memory": texto.slice(0, 40)
    }));
    u.setAttribute("color", oklch(0.62, 0.03, tempSesgo(ECO.hue0 + 200)));
    residuos.push(u);
  }

  function nodosDeClase(clase) {
    return NODOS.filter(function (n) { return n.rutaRef.clase === clase; });
  }

  var OP = {
    /* mueve por región, capa o profundidad */
    transport: function (nd) {
      irARegion(nd.reg);
      S.profundidad = lim(S.profundidad + (nd.costo % 2 ? 1 : -1), 0, 7);
      nuevaNota("transporte", "cruzaste hacia " + nd.reg.nombre + " a profundidad " +
        S.profundidad + ". el vado no estaba señalado.", nd.palabra);
    },
    /* hace crecer texto dentro de otro texto */
    insert: function (nd) {
      var R = corriente("insert:" + nd.id + S.tick);
      var frase = R.elige(C.rio.concat(C.montalbetti));
      pasajeEstado.insertos.push({ pos: R.i(1, pasajeActual.lineas.length - 1), texto: "   ↳ " + frase });
      if (pasajeEstado.insertos.length > 5) pasajeEstado.insertos.shift();
      pintarLegible();
      nuevaNota("inserto", frase, nd.palabra);
    },
    /* quita letras, vocales o palabras aguas abajo */
    erode: function (nd) {
      var rt = nd.rutaRef, R = corriente("erode:" + nd.id + S.tick);
      rt.erosion++;
      rt.nodos.slice(nd.i).forEach(function (n2) {
        n2.palabra = T.erosion(n2.palabra, R, 0.6) || "·";
        n2.estado = "olvidado";
      });
      pasajeEstado.danio++;
      pintarLegible();
      nuevaNota("erosión", "la ruta " + rt.id + " perdió sus vocales desde «" +
        nd.limpia + "». el agua se lleva primero lo abierto.", nd.palabra);
    },
    /* abre una nota, referencia o contradicción */
    cite: function (nd) {
      var R = corriente("cite:" + nd.id + S.citas.length);
      var verdadera = R.quiza(0.5);
      nd.estado = verdadera ? "cita-verdadera" : "cita-falsa";
      nuevaNota(verdadera ? "cita" : "cita-falsa",
        verdadera ? R.elige(C.glosas) : fichaFalsa(R), nd.palabra);
      /* la cita también elige regla: el hash de la cita clasifica */
      nd.reg.regla = REGLAS[fnv(nd.palabra + S.citas.length) % REGLAS.length];
      patronCache = {};
      if (Sonido.encendido()) Sonido.eco(0.55);
    },
    /* propaga una palabra, un color o un estado */
    infect: function (nd) {
      var vecinos = NODOS.filter(function (n2) {
        var dx = n2.gx - nd.gx, dy = n2.gy - nd.gy;
        return dx * dx + dy * dy < 90;
      });
      vecinos.forEach(function (n2) {
        n2.palabra = nd.limpia || n2.palabra;
        n2.estado = "contaminado";
      });
      nd.reg.H += 55;
      nuevaNota("contagio", "«" + nd.limpia + "» ocupó " + vecinos.length +
        " nodos. una palabra que se repite deja de ser una palabra.", nd.palabra);
    },
    /* reorganiza el mapa */
    fold: function (nd) {
      var R = corriente("fold:" + nd.id + S.tick);
      REGIONES.forEach(function (r) {
        r.cx = lim(r.cx + R.f(-9, 9), 2, COLS - 2);
        r.cy = lim(r.cy + R.f(-6, 6), 2, FILAS - 2);
      });
      RUTAS.forEach(function (rt) {
        rt.vert = rt.vert.map(function (v, i) {
          return [lim(v[0] + Math.sin(i + rt.idx) * 3.2, 1.4, COLS - 1.4),
                  lim(v[1] + Math.cos(i * 1.3 + rt.idx) * 2.2, 1.4, FILAS - 1.4)];
        });
        rt.nodos.forEach(function (n2, i) { n2.gx = rt.vert[i][0]; n2.gy = rt.vert[i][1]; });
      });
      nuevaNota("pliegue", "el atlas se dobló sobre sí mismo. las coordenadas anteriores " +
        "siguen siendo válidas para un mapa que ya no existe.", nd.palabra);
    },
    /* crea una copia alterada — en la música, un canon */
    duplicate: function (nd) {
      var rt = nd.rutaRef, R = corriente("dup:" + nd.id + S.tick);
      var frase = T[R.elige(MODOS_T)](rt.frase, R);
      var nueva = construirRuta(frase, rt.reg, RUTAS.length);
      nueva.duplicada = 1;
      rt.duplicada = 1;
      S.canon = 1;
      pintarRutas(); pintarNodos(); pintarJunturas();
      nuevaNota("duplicado", "«" + frase + "» — la copia difiere del original en aquello " +
        "que el original no tenía.", nd.palabra);
    },
    /* vuelve poema una tabla, tabla una ruta, ruta una cita */
    reclassify: function (nd) {
      var rt = nd.rutaRef;
      var orden = ["poema", "tabla", "ruta", "cita", "índice", "error"];
      var k = orden.indexOf(rt.clase);
      if (k < 0) k = fnv(rt.clase) % orden.length;   /* lo inclasificable entra por donde puede */
      var antes = rt.clase;
      rt.clase = orden[(k + 1) % orden.length];
      nd.reg.clase = rt.clase;
      S.clase = rt.clase;
      var R = corriente("recl:" + nd.id + S.tick);
      var f = rt.clase === "tabla" ? T.tabla(rt.frase)
        : rt.clase === "índice" ? T.indice(rt.frase)
        : rt.clase === "cita" ? "«" + rt.frase + "» — " + R.elige(C.autores)
        : rt.clase === "error" ? R.elige(C.codigo)
        : rt.frase;
      rt.nodos.forEach(function (n2, i) {
        var partes = f.split(/\s+/);
        n2.palabra = partes[i % partes.length];
      });
      pasajeActual = { fuente: pasajeActual.fuente, clase: rt.clase, lineas: pasajeActual.lineas };
      pintarLegible();
      nuevaNota("reclasificación", "lo que era " + antes + " ahora es " + rt.clase +
        ". el archivo no recuerda haber decidido esto.", nd.palabra);
    },
    /* restituye una frase anterior, con una diferencia */
    remember: function (nd) {
      var previo = S.memoria[S.memoria.length - 2 - (fnv(nd.id) % 3)] || S.memoria[0];
      var R = corriente("rem:" + nd.id + S.tick);
      if (!previo) {
        nuevaNota("memoria", "el archivo afirma recordar una lectura que no ocurrió.", nd.palabra);
        nd.reg.memoria = lim(nd.reg.memoria - 0.1, 0.15, 1);
        return;
      }
      var texto = T[R.elige(["cicatriz", "orbitar", "lateral", "desplazar"])](previo.texto, R);
      nd.palabra = previo.texto.split(/\s+/)[0] || nd.palabra;
      nd.estado = "memoria";
      nd.reg.memoria = lim(nd.reg.memoria + 0.12, 0.15, 1);
      nuevaNota("memoria", texto, "restituido de: " + previo.verbo);
    },
    /* elimina un fragmento y deja cicatriz */
    forget: function (nd) {
      nd.vivo = 0;
      nd.estado = "olvidado";
      nd.reg.memoria = lim(nd.reg.memoria - 0.16, 0.15, 1);
      S.olvidos.push({ texto: nd.palabra, reg: nd.reg.id });
      marcarCicatriz(nd.gx, nd.gy, nd.palabra);
      patronCache = {};
      nuevaNota("olvido", "se retiró «" + nd.palabra + "». queda la forma del hueco, " +
        "que es más precisa que la palabra.", nd.palabra);
    },
    /* el texto del enlace inicializa una regla celular */
    seed: function (nd) {
      derivarOrigen(nd.rutaRef.frase);
      nd.reg.regla = REGLAS[fnv(nd.palabra) % REGLAS.length];
      patronCache = {};
      nuevaNota("siembra", "las vocales de «" + nd.limpia + "» son ahora la primera fila. " +
        "regla " + nd.reg.regla + ": " + NOMBRE_REGLA[nd.reg.regla] + ".", nd.palabra);
    },
    /* cambia el régimen cromático */
    recolor: function (nd) {
      var R = corriente("recolor:" + nd.id + S.tick);
      nd.reg.regimen = R.elige(REGIMENES);
      S.derivaH += R.f(-70, 70);
      ECO.temperatura = lim(ECO.temperatura + R.f(-0.35, 0.35), -0.9, 0.9);
      nuevaNota("recoloración", "la región " + nd.reg.nombre + " pasó a régimen " +
        nd.reg.regimen.id + ". el color no decora: clasifica.", nd.palabra);
    },
    /* cierra una región y modifica su fuente */
    close: function (nd) {
      nd.rutaRef.abierta = false;
      nd.reg.abierta = false;
      var R = corriente("close:" + nd.id);
      nd.rutaRef.frase = T.enterrar(nd.rutaRef.frase, R);
      nuevaNota("cierre", "cerrada " + nd.reg.nombre + ". su fuente quedó modificada " +
        "por el acto de cerrarla.", nd.palabra);
    },
    /* revela una capa oculta */
    open: function (nd) {
      capaMateria.setAttribute("opacity", capaMateria.getAttribute("opacity") === "1" ? "0.35" : "1");
      nd.reg.abierta = true;
      REGIONES.forEach(function (r) { if (r.kind !== "hueco") r.abierta = true; });
      RUTAS.forEach(function (rt) { if (rt.reg === nd.reg) rt.abierta = true; });
      nuevaNota("apertura", "la materia se hizo visible donde el autómata vive. " +
        "una celda viva revela una letra.", nd.palabra);
    },
    /* hace otra cosa, según una regla constante: la del nodo siguiente */
    disobey: function (nd) {
      var rt = nd.rutaRef;
      var sig = rt.nodos[(nd.i + 1) % rt.nodos.length];
      S.desobediencia++;
      nuevaNota("desobediencia", "pediste " + nd.verbo + " y el mapa hizo " + sig.verbo +
        ". lo hará siempre: obedece al nodo siguiente.", nd.palabra);
      if (OP[sig.verbo] && sig.verbo !== "disobey") OP[sig.verbo](sig);
    },
    /* intenta reconstruir un estado anterior */
    "return": function (nd) {
      var R = corriente("return:" + nd.id + S.tick);
      RUTAS.forEach(function (rt) {
        if (rt.frase !== rt.original && R.quiza(0.6)) {
          rt.frase = T.cicatriz(rt.original, R);
          rt.nodos.forEach(function (n2, i) {
            var p = rt.frase.split(/\s+/);
            n2.palabra = p[i % p.length];
            n2.estado = "cicatriz";
          });
          rt.erosion = 0;
        }
      });
      pasajeEstado.danio = Math.max(0, pasajeEstado.danio - 2);
      pintarLegible();
      nuevaNota("regreso", "el estado anterior fue reconstruido con los materiales " +
        "del estado actual. no es el mismo: es el mismo lugar.", nd.palabra);
      if (Sonido.encendido()) Sonido.eco(0.8);
    },
    /* repara sin restituir */
    scar: function (nd) {
      var R = corriente("scar:" + nd.id + S.tick);
      nd.vivo = 1;
      nd.palabra = T.cicatriz(nd.limpia || nd.palabra, R);
      nd.estado = "cicatriz";
      marcarCicatriz(nd.gx, nd.gy, nd.palabra);
      nuevaNota("sutura", "«" + nd.palabra + "» vuelve, pero con la costura visible. " +
        "reparar no es devolver.", nd.palabra);
    },
    /* expone la estructura SVG: el atributo convertido en verso */
    source: function (nd) {
      var el = elNodos[nd.id];
      var attrs = [];
      if (el) {
        for (var i = 0; i < el.attributes.length; i++) {
          var a = el.attributes[i];
          if (a.name.indexOf("data-") === 0 || a.name === "id") attrs.push(a.name + "=\"" + a.value + "\"");
        }
      }
      nuevaNota("fuente", attrs.join("  ") + "  //  " + T.atributo(nd.rutaRef.frase), nd.palabra);
      SVG.setAttribute("data-estado", "expuesto");
    },
    /* revela los fragmentos que comparten clasificación */
    selector: function (nd) {
      var pares = nodosDeClase(nd.rutaRef.clase);
      pares.forEach(function (n2) { if (n2.estado === "sin-leer") n2.estado = "espera"; });
      while (capaResiduo.querySelector("[data-selector]")) {
        capaResiduo.removeChild(capaResiduo.querySelector("[data-selector]"));
      }
      pares.slice(0, 26).forEach(function (n2) {
        var l = add(capaResiduo, E("line", {
          x1: (nd.gx * CW).toFixed(1), y1: (nd.gy * CH).toFixed(1),
          x2: (n2.gx * CW).toFixed(1), y2: (n2.gy * CH).toFixed(1),
          stroke: oklch(0.7, 0.14, tempSesgo(ECO.hue0 + 90)),
          "stroke-width": 0.4, opacity: 0.45, "data-selector": nd.rutaRef.clase
        }));
        residuos.push(l);
      });
      nuevaNota("selector", pares.length + " fragmentos comparten la clase «" +
        nd.rutaRef.clase + "». ninguno la eligió.", nd.palabra);
    },
    /* parece inactivo; cambia una ruta futura */
    "void": function (nd) {
      S.deudaVoid.push({ nodo: nd.id, cuando: S.tick + 6 + (fnv(nd.id) % 12) });
      nd.estado = "espera";
      nuevaNota("vacío", "no ocurrió nada. lo que no ocurre también se acumula.", nd.palabra);
    }
  };

  function ejecutar(verbo, nd) {
    if (!OP[verbo]) verbo = "cite";
    nd.visitado++;
    if (nd.estado === "sin-leer") nd.estado = "visitado";
    S.lecturas++;
    recordar({ verbo: verbo, texto: nd.rutaRef.frase, nodo: nd.id, t: S.tick });
    OP[verbo](nd);
    S.region = nd.reg.kind === "hueco" ? S.region : nd.reg;
    actualizarHash();
    patronCache = {};
    pintarRutas(); pintarNodos(); pintarJunturas(); pintarNotas(); pintarHUD();
    if (Sonido.encendido()) Sonido.gesto(verbo, nd);
  }

  /* --- la región inaccesible ------------------------------------- */
  function tocarHueco() {
    nuevaNota("h6", "la región H6 aparecía en los mapas como una falta de hidrógeno. " +
      "no contenía una estrella especial, un planeta prometido, una posible segunda Tierra.",
      "acceso denegado");
    SVG.setAttribute("data-estado", "region-cerrada");
    pintarNotas();
    if (Sonido.encendido()) Sonido.sub();
  }

  /* --- transporte de cámara -------------------------------------- */
  var camara = { x: 0, y: 0, w: VB.w, h: VB.h, tx: 0, ty: 0, tw: VB.w, th: VB.h };
  function irARegion(reg) {
    S.region = reg;
    var z = mez(1, 0.42, S.profundidad / 7);
    camara.tw = VB.w * z;
    camara.th = VB.h * z;
    camara.tx = lim(reg.cx * CW - camara.tw / 2, 0, VB.w - camara.tw);
    camara.ty = lim(reg.cy * CH - camara.th / 2, 0, VB.h - camara.th);
  }
  function aplicarCamara() {
    var k = 0.09;
    camara.x = mez(camara.x, camara.tx, k);
    camara.y = mez(camara.y, camara.ty, k);
    camara.w = mez(camara.w, camara.tw, k);
    camara.h = mez(camara.h, camara.th, k);
    SVG.setAttribute("viewBox", camara.x.toFixed(1) + " " + camara.y.toFixed(1) + " " +
      camara.w.toFixed(1) + " " + camara.h.toFixed(1));
    /* el acetato deshace la cámara: el aparato crítico no viaja con el
       territorio, porque el que clasifica nunca se mueve con lo clasificado */
    capaFija.setAttribute("transform",
      "translate(" + camara.x.toFixed(2) + "," + camara.y.toFixed(2) + ") scale(" +
      (camara.w / VB.w).toFixed(5) + "," + (camara.h / VB.h).toFixed(5) + ")");
  }

  /* --- el hash: el estado también se escribe en la URL ----------- */
  function actualizarHash() {
    var mem = S.olvidos.length ? "scar" : (S.memoria.length > 12 ? "densa" : "parcial");
    var h = "#region=" + S.region.kind + "&depth=" + S.profundidad + "&memory=" + mem +
      "&rule=" + S.region.regla + "&seed=" + FIRMA;
    try { if (W.history && W.history.replaceState) W.history.replaceState(null, "", h); }
    catch (e) { /* el archivo tampoco puede escribir siempre donde quiere */ }
  }

  /* =================================================================
     15 · SONIDO — Web Audio nativo, sin muestras, sin bibliotecas
     transmite, falla, insiste, recuerda y pierde información.
     ================================================================= */

  var Sonido = (function () {
    var ctx = null, listo = false;
    var master, filtro, seco, envio, dl, dr, fb1, fb2, panL, panR;
    var droneOsc = [], droneGain, droneFiltro;
    var bufRuido = null, ondas = {};
    var t0 = 0, proxT = 0, pasoSeq = 0, reloj = null;
    var bpm = Math.round(Rmus.f(78, 122));
    var crusher = null;

    function nota(midi) { return 440 * Math.pow(2, (midi - 69) / 12); }

    function grado(reg, n) {
      var esc = MODOS[reg.modo];
      var oct = Math.floor(n / esc.length);
      return reg.tonica + esc[((n % esc.length) + esc.length) % esc.length] + oct * 12;
    }

    function ondaPulso(duty) {
      var k = duty.toFixed(2);
      if (ondas[k]) return ondas[k];
      var n = 24, real = new Float32Array(n + 1), imag = new Float32Array(n + 1);
      for (var i = 1; i <= n; i++) real[i] = (2 / (i * Math.PI)) * Math.sin(Math.PI * i * duty);
      ondas[k] = ctx.createPeriodicWave(real, imag);
      return ondas[k];
    }

    function curvaCrush(bits) {
      var n = 512, c = new Float32Array(n), niveles = Math.pow(2, bits);
      for (var i = 0; i < n; i++) {
        var x = (i / (n - 1)) * 2 - 1;
        c[i] = Math.round(x * niveles) / niveles;
      }
      return c;
    }

    function construir() {
      var AC = W.AudioContext || W.webkitAudioContext;
      if (!AC) return false;
      ctx = new AC();
      master = ctx.createGain(); master.gain.value = 0.0001;
      filtro = ctx.createBiquadFilter(); filtro.type = "lowpass"; filtro.frequency.value = 7000; filtro.Q.value = 0.7;
      filtro.connect(master); master.connect(ctx.destination);
      seco = ctx.createGain(); seco.gain.value = 1; seco.connect(filtro);

      /* ping-pong: dos retardos cruzados y dos panners */
      envio = ctx.createGain(); envio.gain.value = 0.16;
      dl = ctx.createDelay(1.5); dr = ctx.createDelay(1.5);
      dl.delayTime.value = 60 / bpm / 2; dr.delayTime.value = 60 / bpm / 2 * 1.5;
      fb1 = ctx.createGain(); fb2 = ctx.createGain();
      fb1.gain.value = 0.42; fb2.gain.value = 0.38;
      panL = ctx.createStereoPanner ? ctx.createStereoPanner() : ctx.createGain();
      panR = ctx.createStereoPanner ? ctx.createStereoPanner() : ctx.createGain();
      if (panL.pan) { panL.pan.value = -0.8; panR.pan.value = 0.8; }
      envio.connect(dl); dl.connect(fb1); fb1.connect(dr); dr.connect(fb2); fb2.connect(dl);
      dl.connect(panL); dr.connect(panR); panL.connect(filtro); panR.connect(filtro);

      crusher = ctx.createWaveShaper();
      crusher.curve = curvaCrush(5 + (SEMILLA % 3));
      crusher.connect(seco);

      /* el ruido: firmado por la semilla, nunca por Math.random */
      var Rn = corriente("ruido-audio");
      bufRuido = ctx.createBuffer(1, ctx.sampleRate * 2, ctx.sampleRate);
      var d = bufRuido.getChannelData(0);
      for (var i = 0; i < d.length; i++) d[i] = Rn.f(-1, 1);

      /* el drone del archivo: tres osciladores desafinados */
      droneGain = ctx.createGain(); droneGain.gain.value = 0.0;
      droneFiltro = ctx.createBiquadFilter();
      droneFiltro.type = "lowpass"; droneFiltro.frequency.value = 420; droneFiltro.Q.value = 3;
      droneGain.connect(droneFiltro); droneFiltro.connect(filtro);
      [0, -7, 5].forEach(function (dt, k) {
        var o = ctx.createOscillator();
        o.type = k === 2 ? "triangle" : "sawtooth";
        o.frequency.value = nota(S.region.tonica - 12) * Math.pow(2, dt / 1200 * 8);
        o.detune.value = dt * 3;
        o.connect(droneGain); o.start();
        droneOsc.push(o);
      });
      listo = true;
      return true;
    }

    function ruidoFuente() {
      var s = ctx.createBufferSource();
      s.buffer = bufRuido; s.loop = true;
      return s;
    }

    function env(g, t, a, d, pico) {
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(Math.max(0.0002, pico), t + a);
      g.gain.exponentialRampToValueAtTime(0.0001, t + a + d);
    }

    function kick(t, reg) {
      var o = ctx.createOscillator(), g = ctx.createGain();
      o.type = "sine";
      o.frequency.setValueAtTime(140, t);
      o.frequency.exponentialRampToValueAtTime(38, t + 0.12);
      env(g, t, 0.004, 0.24, 0.5);
      o.connect(g); g.connect(seco); o.start(t); o.stop(t + 0.34);
    }
    function caja(t) {
      var s = ruidoFuente(), f = ctx.createBiquadFilter(), g = ctx.createGain();
      f.type = "bandpass"; f.frequency.value = 1900; f.Q.value = 1.1;
      env(g, t, 0.002, 0.11, 0.22);
      s.connect(f); f.connect(g); g.connect(seco); g.connect(envio);
      s.start(t); s.stop(t + 0.16);
    }
    function hat(t) {
      var s = ruidoFuente(), f = ctx.createBiquadFilter(), g = ctx.createGain();
      f.type = "highpass"; f.frequency.value = 8200;
      env(g, t, 0.001, 0.035, 0.1);
      s.connect(f); f.connect(g); g.connect(seco);
      s.start(t); s.stop(t + 0.06);
    }
    function bajo(t, reg, n) {
      var o = ctx.createOscillator(), g = ctx.createGain(), f = ctx.createBiquadFilter();
      o.type = "square";
      o.frequency.value = nota(grado(reg, n) - 24);
      f.type = "lowpass"; f.frequency.value = 900; f.Q.value = 4;
      env(g, t, 0.006, 0.2, 0.24);
      o.connect(f); f.connect(g); g.connect(seco); o.start(t); o.stop(t + 0.28);
    }
    function lead(t, reg, n, eco) {
      var o = ctx.createOscillator(), g = ctx.createGain(), p = ctx.createStereoPanner ? ctx.createStereoPanner() : null;
      o.setPeriodicWave(ondaPulso(0.2 + (fnv(reg.id) % 40) / 100));
      o.frequency.value = nota(grado(reg, n));
      if (reg.musica === "desafinado") o.detune.value = 26;
      env(g, t, 0.004, 0.19, 0.16);
      o.connect(g);
      if (p) { p.pan.value = Math.sin(S.paso * 0.7) * 0.7; g.connect(p); p.connect(seco); }
      else g.connect(seco);
      if (eco) g.connect(envio);
      o.start(t); o.stop(t + 0.3);
    }
    function arp(t, reg, n) {
      var o = ctx.createOscillator(), g = ctx.createGain();
      o.type = "square";
      o.frequency.value = nota(grado(reg, n) + 12);
      env(g, t, 0.002, 0.08, 0.1);
      o.connect(g); g.connect(crusher); o.start(t); o.stop(t + 0.12);
    }
    function campana(t, reg, n) {
      var p = ctx.createOscillator(), m = ctx.createOscillator();
      var mg = ctx.createGain(), g = ctx.createGain();
      var f = nota(grado(reg, n) + 12);
      p.type = "sine"; m.type = "sine";
      p.frequency.value = f; m.frequency.value = f * 5.07;
      mg.gain.value = f * 2.6;
      m.connect(mg); mg.connect(p.frequency);
      env(g, t, 0.002, 0.55, 0.12);
      p.connect(g); g.connect(seco); g.connect(envio);
      p.start(t); m.start(t); p.stop(t + 0.7); m.stop(t + 0.7);
    }
    function pad(t, reg, n) {
      [0, 3, 7].forEach(function (iv, k) {
        var o = ctx.createOscillator(), g = ctx.createGain(), d = ctx.createDelay(0.05);
        o.type = "sawtooth";
        o.frequency.value = nota(grado(reg, n) + iv);
        o.detune.value = (k - 1) * 9;
        d.delayTime.value = 0.012 + k * 0.006;   /* chorus pobre y suficiente */
        g.gain.setValueAtTime(0.0001, t);
        g.gain.exponentialRampToValueAtTime(0.045, t + 0.9);
        g.gain.exponentialRampToValueAtTime(0.0001, t + 2.6);
        o.connect(d); d.connect(g); g.connect(seco);
        o.start(t); o.stop(t + 2.8);
      });
    }

    function durPaso() {
      var d = 60 / bpm / 4;
      if (S.region.memoria < 0.6) d *= 2;      /* la pérdida de memoria toca a mitad de velocidad */
      return d;
    }

    /* la melodía la escribe la ruta: la longitud de cada palabra es un grado */
    function gradoDePaso(reg, p) {
      var rt = reg.rutas.filter(function (r) { return r.abierta; })[0] || reg.rutas[0];
      if (!rt) return p % 7;
      var pal = rt.nodos[p % rt.nodos.length];
      return (pal ? pal.palabra.length : 3) % 9;
    }

    function tocarPaso(p, t) {
      var reg = S.region, p16 = p % 16;
      if (p16 === 0) S.compas++;
      var n = gradoDePaso(reg, p);
      if (patron("kick", reg)[p16]) kick(t, reg);
      if (patron("caja", reg)[p16]) caja(t);
      if (patron("hat", reg)[p16]) hat(t);
      if (patron("bajo", reg)[p16]) bajo(t, reg, n);
      if (patron("lead", reg)[p16]) lead(t, reg, n, reg.musica === "eco");
      if (patron("arp", reg)[p16]) arp(t, reg, n + (p16 % 5));
      if (patron("campana", reg)[p16]) campana(t, reg, n + 2);
      if (patron("drone", reg)[p16] && p16 === 0) {
        if (reg.musica === "drone" || reg.musica === "suspendido") pad(t, reg, n);
        droneGain.gain.setTargetAtTime(reg.musica === "drone" ? 0.09 :
          (reg.musica === "subgrave" ? 0.12 : 0.02), t, 0.6);
        droneFiltro.frequency.setTargetAtTime(
          reg.musica === "subgrave" ? 120 : mez(240, 900, reg.activo || 0.3), t, 0.8);
      }
      /* el canon: la ruta duplicada vuelve cuatro pasos después */
      if (S.canon && p16 % 4 === 0) lead(t + durPaso() * 4, reg, n + 5, true);
      /* la profundidad filtra y cambia registro */
      filtro.frequency.setTargetAtTime(mez(9000, 700, S.profundidad / 7), t, 0.4);
    }

    function programar() {
      if (!listo || ctx.state !== "running") return;
      var lim2 = ctx.currentTime + 0.16;
      while (proxT < lim2) {
        tocarPaso(pasoSeq, proxT);
        proxT += durPaso();
        pasoSeq++;
      }
    }

    return {
      encendido: function () { return listo && ctx && ctx.state === "running"; },
      alternar: function () {
        if (!listo && !construir()) return false;
        if (ctx.state === "suspended") ctx.resume();
        if (S.audio) {
          master.gain.setTargetAtTime(0.0001, ctx.currentTime, 0.2);
          S.audio = false;
        } else {
          master.gain.setTargetAtTime(0.5, ctx.currentTime, 0.3);
          S.audio = true;
          t0 = ctx.currentTime + 0.05;
          proxT = t0; pasoSeq = 0;
          if (!reloj) reloj = W.setInterval(programar, 25);
        }
        return S.audio;
      },
      /* el paso sonoro manda sobre el visual cuando hay sonido */
      pasoActual: function () {
        if (!this.encendido() || !S.audio) return null;
        return Math.max(0, Math.floor((ctx.currentTime - t0) / durPaso()));
      },
      eco: function (w) {
        if (!this.encendido()) return;
        envio.gain.setTargetAtTime(lim(w, 0, 0.6), ctx.currentTime, 0.1);
        envio.gain.setTargetAtTime(0.16, ctx.currentTime + 1.6, 0.5);
      },
      sub: function () {
        if (!this.encendido()) return;
        var o = ctx.createOscillator(), g = ctx.createGain();
        o.type = "sine"; o.frequency.value = 41;
        env(g, ctx.currentTime, 0.4, 2.4, 0.35);
        o.connect(g); g.connect(seco); o.start(); o.stop(ctx.currentTime + 3);
      },
      gesto: function (verbo, nd) {
        if (!this.encendido()) return;
        var t = ctx.currentTime + 0.01, reg = nd.reg;
        var n = nd.palabra.length % 9;
        if (verbo === "cite" || verbo === "return") campana(t, reg, n);
        else if (verbo === "forget") { var s = ruidoFuente(), g = ctx.createGain();
          env(g, t, 0.01, 0.5, 0.14); s.connect(g); g.connect(seco); s.start(t); s.stop(t + 0.6); }
        else if (verbo === "seed" || verbo === "infect") arp(t, reg, n);
        else if (verbo === "transport") { lead(t, reg, n, true); this.eco(0.4); }
        else if (verbo === "void") { /* el vacío no suena: por eso se acumula */ }
        else lead(t, reg, n, false);
      },
      bpm: function () { return bpm; }
    };
  })();

  /* =================================================================
     16 · LA PREHISTORIA — el visitante llega tarde
     antes del primer cuadro, el archivo ya llevaba rato clasificándose.
     ================================================================= */

  (function prehistoria() {
    var i;
    for (i = 0; i < 96; i++) tickAutomata();          /* el campo ya corrió */
    /* lecturas anteriores: rutas erosionadas, fragmentos olvidados, notas viejas */
    var n = Rhist.i(5, 11);
    for (i = 0; i < n; i++) {
      var nd = RUTAS[Rhist.i(0, RUTAS.length - 1)].nodos[Rhist.i(0, 3)];
      if (!nd) continue;
      nd.visitado = Rhist.i(1, 4);
      nd.estado = Rhist.elige(["visitado", "olvidado", "cita-verdadera", "contaminado", "cicatriz"]);
      if (nd.estado === "olvidado" && Rhist.quiza(0.5)) {
        nd.vivo = 0;
        S.olvidos.push({ texto: nd.palabra, reg: nd.reg.id });
        marcarCicatriz(nd.gx, nd.gy, nd.palabra);
      }
      recordar({ verbo: Rhist.elige(VERBOS), texto: nd.rutaRef.frase, nodo: nd.id, t: -i });
    }
    /* una región ya perdió memoria; otra ya se contaminó de color */
    var perdida = REGIONES[Rhist.i(0, REGIONES.length - 1)];
    perdida.memoria = Rhist.f(0.3, 0.75);
    var anomala = REGIONES.filter(function (r) { return r !== perdida && r.kind !== "hueco"; })[Rhist.i(0, 2)] || REGIONES[0];
    if (anomala) { anomala.regimen = REGIMENES[8]; anomala.H += 170; }   /* la anomalía cromática */
    /* notas heredadas */
    nuevaNota("cita", Rhist.elige(C.glosas), "hallada abierta");
    nuevaNota("cita-falsa", fichaFalsa(Rhist), "referencia circular");
    nuevaNota("memoria", Rhist.elige(C.definiciones), "el índice remite al índice");
    S.tick = Rhist.i(400, 3000);
  })();

  /* =================================================================
     17 · EL RELOJ — lo que sigue ocurriendo mientras miras
     ================================================================= */

  var acumulado = 0, ultimo = 0, acumPaso = 0, sinTocar = 0;
  var pasoPintado = -1, hondPintada = -1;

  function tickLento() {
    S.tick++;
    tickAutomata();
    actualizarMascara();
    repintarCampo();
    S.derivaH += ECO.deriva * 0.0016;          /* deriva cromática lenta */
    S.cabeza = (S.cabeza + 1) % FILAS;
    if (S.cabeza < 2) S.cabeza = 2;
    patronCache = {};

    /* las notas envejecen y algunas se pierden */
    S.citas.forEach(function (n) { n.edad++; });
    if (S.citas.length && S.tick % 9 === 0 && S.citas[0].edad > 12) S.citas.shift();

    /* las deudas del vacío se cobran en una ruta futura */
    S.deudaVoid = S.deudaVoid.filter(function (d) {
      if (S.tick >= d.cuando) {
        var rt = RUTAS[fnv(d.nodo) % RUTAS.length];
        var R = corriente("deuda:" + d.nodo);
        rt.frase = T[R.elige(MODOS_T)](rt.frase, R);
        rt.nodos.forEach(function (n2, i) {
          var p = rt.frase.split(/\s+/);
          n2.palabra = p[i % p.length] || n2.palabra;
        });
        nuevaNota("vacío", "la ruta " + rt.id + " cambió por algo que no hiciste hace " +
          (S.tick - d.cuando + 6) + " ciclos.", "deuda saldada");
        pintarRutas(); pintarNodos();
        return false;
      }
      return true;
    });

    /* el nodo efímero: aparece y desaparece sin que nadie lo pida */
    if (S.efimero) {
      capaResiduo.removeChild(S.efimero);
      S.efimero = null;
    } else if (S.tick % 3 === 0) {
      var R = corriente("efimero:" + S.tick);
      var reg = REGIONES[R.i(0, REGIONES.length - 1)];
      var g = add(capaResiduo, E("g", { "data-state": "efimero", "data-cost": "0" }));
      var gx = lim(reg.cx + R.f(-8, 8), 2, COLS - 2), gy = lim(reg.cy + R.f(-5, 5), 2, FILAS - 2);
      add(g, E("use", { href: "#vado", x: (gx * CW - 10).toFixed(1), y: (gy * CH - 10).toFixed(1),
        width: 20, height: 20 })).setAttribute("color", oklch(0.85, 0.15, tempSesgo(reg.H + 120)));
      add(g, E("text", { x: (gx * CW + 14).toFixed(1), y: (gy * CH + 4).toFixed(1),
        "font-family": MONO, "font-size": 9,
        fill: oklch(0.8, 0.1, tempSesgo(reg.H + 120)), opacity: 0.9 },
        R.elige(C.humor)));
      S.efimero = g;
    }

    /* si nadie toca nada, el sistema sigue excavando solo */
    sinTocar++;
    if (sinTocar > 14) {
      var R2 = corriente("solo:" + S.tick);
      var nd = NODOS[R2.i(0, NODOS.length - 1)];
      if (nd && nd.vivo) {
        var v = R2.elige(["erode", "cite", "reclassify", "seed", "recolor", "remember"]);
        recordar({ verbo: v, texto: nd.rutaRef.frase, nodo: nd.id, t: S.tick });
        OP[v](nd);
        SVG.setAttribute("data-estado", "excavando-solo");
      }
      sinTocar = 0;
    }

    pintarRutas(); pintarNodos(); pintarJunturas(); pintarNotas(); pintarHUD();
  }

  function cuadro(t) {
    if (!ultimo) ultimo = t;
    var dt = Math.min(120, t - ultimo);
    ultimo = t;
    acumulado += dt;
    acumPaso += dt;

    var durPasoVisual = 60000 / Sonido.bpm() / 4;
    var pasoSonoro = Sonido.pasoActual();
    if (pasoSonoro != null) {
      S.paso = pasoSonoro;
    } else if (acumPaso >= durPasoVisual) {
      acumPaso -= durPasoVisual;
      S.paso++;
      if (S.paso % 16 === 0) S.compas++;
    }

    if (acumulado >= 1150) { acumulado = 0; tickLento(); }

    /* sólo se repinta lo que cambió: el archivo tampoco se relee entero */
    if (Math.abs(camara.x - camara.tx) + Math.abs(camara.y - camara.ty) +
        Math.abs(camara.w - camara.tw) > 0.4) aplicarCamara();
    if (S.paso !== pasoPintado) { pasoPintado = S.paso; pintarPasoPartitura(); }
    if (S.profundidad !== hondPintada) {
      hondPintada = S.profundidad;
      feBlur.setAttribute("stdDeviation", (0.1 + S.profundidad * 0.12).toFixed(2));
    }
    W.requestAnimationFrame(cuadro);
  }

  /* =================================================================
     18 · LA ENTRADA — clic, rueda, teclas
     ================================================================= */

  function nodoDesde(el) {
    while (el && el !== SVG) {
      if (el.id && elNodos[el.id]) return NODOS.filter(function (n) { return n.id === el.id; })[0];
      if (el.getAttribute && el.getAttribute("data-target") && elNodos[el.getAttribute("data-target")]) {
        var id = el.getAttribute("data-target");
        return NODOS.filter(function (n) { return n.id === id; })[0];
      }
      el = el.parentNode;
    }
    return null;
  }

  SVG.addEventListener("click", function (ev) {
    sinTocar = 0;
    var el = ev.target;

    /* la bocina rudimentaria */
    var bocina = el.closest ? el.closest("#bocina") : null;
    if (bocina) {
      var on = Sonido.alternar();
      bocina.setAttribute("data-state", on ? "encendida" : "apagada");
      capaPartitura.setAttribute("data-audio", on ? "encendido" : "apagado");
      var tx = D.getElementById("bocina-texto");
      if (tx) tx.textContent = on
        ? "● transmitiendo — el retraso crece; lo que digo ahora lo oirás cuando ya no sea cierto"
        : "◌ le pusimos una antena y una voz —";
      return;
    }

    /* el estrato legible tiene sus propias acciones */
    var acc = el.getAttribute && el.getAttribute("data-action");
    if (acc && el.getAttribute("data-target") === "estrato-legible") {
      var falso = NODOS.filter(function (n) { return n.reg === S.region && n.vivo; })[0] || NODOS[0];
      if (falso) ejecutar(acc, falso);
      return;
    }

    var nd = nodoDesde(el);
    if (!nd) {
      /* clic en el campo: entrar a la región tocada */
      var pt = puntoSVG(ev);
      var gx = lim(Math.floor(pt.x / CW), 0, COLS - 1);
      var gy = lim(Math.floor(pt.y / CH), 0, FILAS - 1);
      var reg = CELDAS[gy * COLS + gx].reg;
      if (reg.kind === "hueco") { tocarHueco(); return; }
      irARegion(reg);
      actualizarHash();
      pintarHUD();
      patronCache = {};
      return;
    }
    if (nd.reg.kind === "hueco") { tocarHueco(); return; }
    ejecutar(nd.verbo, nd);
  });

  function puntoSVG(ev) {
    var r = SVG.getBoundingClientRect();
    var escala = camara.w / r.width;
    return {
      x: camara.x + (ev.clientX - r.left) * escala,
      y: camara.y + (ev.clientY - r.top) * (camara.h / r.height)
    };
  }

  SVG.addEventListener("wheel", function (ev) {
    ev.preventDefault();
    sinTocar = 0;
    S.profundidad = lim(S.profundidad + (ev.deltaY > 0 ? 1 : -1), 0, 7);
    irARegion(S.region);
    actualizarHash();
    pintarHUD();
    repintarCampo();
  }, { passive: false });

  D.addEventListener("keydown", function (ev) {
    sinTocar = 0;
    var k = ev.key.toLowerCase();
    if (k === " " || k === "s") {
      ev.preventDefault();
      var on = Sonido.alternar();
      capaPartitura.setAttribute("data-audio", on ? "encendido" : "apagado");
      var tx = D.getElementById("bocina-texto");
      if (tx) tx.textContent = on
        ? "● transmitiendo — sigo hablando. ¿me escuchan?"
        : "◌ le pusimos una antena y una voz —";
      var bg = D.getElementById("bocina");
      if (bg) bg.setAttribute("data-state", on ? "encendida" : "apagada");
    } else if (k === "arrowup" || k === "+") {
      S.profundidad = lim(S.profundidad - 1, 0, 7); irARegion(S.region); pintarHUD(); repintarCampo();
    } else if (k === "arrowdown" || k === "-") {
      S.profundidad = lim(S.profundidad + 1, 0, 7); irARegion(S.region); pintarHUD(); repintarCampo();
    } else if (k === "arrowright" || k === "arrowleft") {
      var abiertas = REGIONES.filter(function (r) { return r.kind !== "hueco"; });
      var i = abiertas.indexOf(S.region);
      irARegion(abiertas[(i + (k === "arrowright" ? 1 : abiertas.length - 1)) % abiertas.length]);
      pintarHUD(); patronCache = {};
    } else if (k === "m") {
      /* el mapa incompleto: plegar */
      var nd = NODOS[fnv("m" + S.tick) % NODOS.length];
      if (nd) ejecutar("fold", nd);
    } else if (k === "f") {
      var nd2 = NODOS[fnv("f" + S.tick) % NODOS.length];
      if (nd2) ejecutar("source", nd2);
    }
    actualizarHash();
  });

  /* =================================================================
     19 · ENCENDER
     ================================================================= */

  repintarCampo();
  actualizarMascara();
  pintarRutas();
  pintarNodos();
  pintarJunturas();
  pintarLegible();
  pintarNotas();
  pintarHUD();
  /* la primera vista es el atlas entero: se entra por el medio, no por el borde */
  camara.tx = 0; camara.ty = 0; camara.tw = VB.w; camara.th = VB.h;
  camara.x = 0; camara.y = 0; camara.w = VB.w; camara.h = VB.h;
  aplicarCamara();
  actualizarHash();
  W.requestAnimationFrame(cuadro);

})();
