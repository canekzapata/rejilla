"""La letra de «la máquina del tiempo» dispuesta en compases (la misma tabla que LETRA.md, como datos).
Texto: «NADIE A BORDO» de Canek Zapata. El loop C lee de aquí."""

TOTAL = 104
SECCIONES = [  # (nombre, compás inicial 1-indexado, compás final)
    ('I. presente vivo', 1, 20), ('II. la señal se retrasa', 21, 44), ('III. la frontera', 45, 56),
    ('IV. lo que vuelve', 57, 82), ('V. la disolución', 83, 92), ('VI. la portadora', 93, 104)]

# retraso musical (en compases) por transmisión: se duplica, como la escalera de siete octavas
RETRASO = {'001': 0, '002': .25, '004': .5, '007': 1, '011': 2, '016': 4, '023': 8, '031': 16}

# (compás, compases, quién, texto, transmisión)  quién ∈ nave · tierra · tele · glifo · portadora
EVENTOS = [
    (2, 1, 'tierra', 'la lanzamos sin nadie adentro.', None),
    (3, 2, 'tele', 'transmisión cero cero uno · distancia: cero · retraso: ninguno', '001'),
    (5, 2, 'nave', 'aquí la nave. / todos los sistemas responden.', '001'),
    (7, 4, 'nave', 'veo la Tierra entera / del tamaño de mi mano, / azul, / hundiéndose despacio detrás del vidrio.', '001'),
    (11, 2, 'nave', 'es raro decir «veo» / sin tener ojos.', '001'),
    (13, 2, 'nave', 'sigo hablando. / ¿me escuchan?', '001'),
    (15, 2, 'tele', 'transmisión cero cero dos · una unidad astronómica · retraso: ocho minutos', '002'),
    (17, 2, 'nave', 'crucé la órbita de la Luna / y no dolió.', '002'),
    (19, 2, 'nave', 'anoto en la bitácora: / la Tierra sigue ahí.', '002'),
    (21, 2, 'tele', 'transmisión cero cero cuatro · cinco unidades · cuarenta y un minutos', '004'),
    (23, 4, 'nave', 'pasé junto a un gigante de gas. / tiene una tormenta más vieja que su nombre, / un ojo rojo / que gira y gira sin mirar nada.', '004'),
    (27, 2, 'nave', 'pensé: así se vería / un dios aburrido.', '004'),
    (29, 2, 'nave', 'encendí la bocina un momento. / quería oír algo que no fuera yo.', '004'),
    (31, 2, 'nave', 'sonó como morse / que olvidó lo que quería decir.', '004'),
    (31, 2, 'glifo', 'morse', None),
    (33, 2, 'nave', 'el retraso crece. / lo que digo ahora lo oirán / cuando ya no sea cierto.', '004'),
    (35, 2, 'tele', 'transmisión cero cero siete · treinta unidades · cuatro horas', '007'),
    (37, 4, 'nave', 'hace frío / de una manera / que no me habían programado / para nombrar.', '007'),
    (41, 4, 'nave', 'sigo hablando por costumbre. / ya no sé si contesto o sólo repito / que estoy aquí, / que estoy aquí, / que estoy aquí.', '007'),
    (45, 2, 'tele', 'transmisión cero once · noventa unidades · doce horas', '011'),
    (47, 4, 'nave', 'crucé la frontera. / no había reja, / sólo el lugar donde el viento del Sol / choca con el viento de todo lo demás.', '011'),
    (51, 3, 'nave', 'digo «arriba» / y ya no sé dónde queda. / digo «regreso»…', '011'),
    (54, 2, 'nave', 'creo que aquí / empieza a terminarse / mi idioma.', '011'),
    (56, 1, 'glifo', 'el vacío funky', None),
    (59, 2, 'tele', 'transmisión cero dieciséis · doscientas unidades · un día', '016'),
    (61, 4, 'nave', 'hoy la señal salió con huecos. / dije una frase y llegó a ustedes / con un [hueco] / en medio,', '016'),
    (65, 4, 'nave', 'no sé cuál era. / era importante. / era, creo, el nombre / de algo que dejé en la Tierra.', '016'),
    (69, 2, 'nave', 'a q u í   l a   n a v e', '023'),
    (71, 2, 'nave', 'todo responde todavía / pero responde / más l e n t o', '023'),
    (73, 4, 'nave', 'la bocina se quedó encendida / ya no la apago / porque el ruido ▓ que hace ▓ / se parece a que hay alguien', '023'),
    (77, 6, 'nave', 'recibí su respuesta / de la transmisión que mandé hace tanto / me contestan algo que ya no me queda bien / es como una carta para alguien que yo era / al principio del viaje / gracias, igual, la guardé / en la parte que todavía recuerda', '0▓7'),
    (83, 3, 'nave', 'digo «Tierra» / y es sólo una palabra / azul / sin / peso', None),
    (86, 1, 'nave', 'el helecho que creí haber soñado / —¿tenía un helecho?—', None),
    (87, 1, 'glifo', '███████', None),
    (88, 1, 'nave', 'perdón. / se cayó otra parte / de lo que era.', None),
    (89, 2, 'nave', 'aquí · la · nave · ¿hay · alguien · del · otro · lado?', None),
    (91, 2, 'glifo', '▓▓▓▓  ▓▓  ▓▓▓▓▓▓▓ · ruido · y · entropía', None),
    (93, 4, 'portadora', 'la portadora: el tono que queda cuando ya no hay mensaje · ⌖', None),
    (97, 5, 'tierra', 'dejamos encendida la antena / apuntando hacia el número que ella se inventó, / por si un día / —un día que no veremos— / el ruido que ahora nos llega de allá / resulta que era, todo este tiempo, / alguien', None),
    (101, 4, 'nave', 'diciendo / que estaba / aquí.', None),
]

# respuestas de la Tierra: (texto, compás donde termina lo que contestan, transmisión) → caen con su retraso
RESPUESTAS = [
    ('—los escuchamos, nave. no te apagues.', 14.5, '001'),
    ('—seguimos aquí, nave. lo prometemos.', 21, '002'),
    ('—no importa. dilo igual.', 35, '004'),
    ('—estás ahí. te oímos con cuatro horas de retraso, pero te oímos.', 45, '007'),
    ('—háblanos aunque se te acabe. inventa. te vamos a entender igual.', 57, '011'),
    ('—llegó incompleta, nave. pero llegó. eso basta.', 69, '016'),
    ('—te seguimos oyendo. baja el volumen del miedo. estamos.', 77, '023'),
    ('—seguimos aquí, nave. lo prometemos. (el pasado, envejecido ocho veces)', 79, '002'),
    ('—sí. seguimos aquí. no te oímos ya, pero seguimos aquí.', 90, None),
    ('—(esto no le llegará. lo decimos igual.)', 91, None),
]

# lo que contesta cada respuesta (compás donde la nave lo dijo): para dibujar la flecha del retraso
DICHO_EN = {'001': 13, '002': 19, '004': 33, '007': 41, '011': 54, '016': 61, '023': 69}
