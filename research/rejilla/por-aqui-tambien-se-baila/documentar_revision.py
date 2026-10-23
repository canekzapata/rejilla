"""Notas de dirección r4 y crítica para la parada de revisión."""
from comun import *

def main():
    out=ultimo();P=leer(score());tag=out.name.split('-')[-1];n=sum(map(len,P['eventos'].values()));v=P['terreno_viaje']
    txt=f'''# Por aquí también se baila — revisión compositiva

22 de octubre de 2026. **Partitura para revisar con Canek. No producir todavía la
canción. El visor va después.** Entrega vigente: `{out.name}`.

## Qué estaba débil

La versión anterior no alcanzaba la complejidad relacional de «El río no tiene
tronco». Tenía treinta capas, pero repetía un tema D-F-A sobre ocho compases de
acordes; varias respuestas eran la misma figura, los relojes volvían a cuadrar
cada ocho pulsos y la supuesta memoria del terreno se quedaba parcialmente en
metadatos. No había una parada sin ritmo. Una bolsa llena de estaciones y un
puente no tenían suficiente contexto: rareza verbal sin acción que la sostuviera.

En «El río», el código relaciona alturas con armónicos, pendientes con tempos de
once afluentes, confluencias con sincronización y cinco longitudes con afinaciones
y llegadas distintas. También contiene patrones escogidos a mano: no todo emerge
del modelo. Se leyeron README y código; no se hizo una nueva audición. El criterio
útil es que cada desarrollo cambie algo que luego importe, no imitar su arpa.

## La bolsa: tu corrección

**Ahora contiene un trompo de lámina, un cascabel y un silbato de barro con un ala
rota.** Son juguetes que se pueden cargar. No contiene literalmente ritmos ni
tiempos: esos aparecen al moverse los objetos. Tampoco se obliga al clima a ser
una persona; la lluvia entra por una ventana y cambia lo que puede sonar.

Hay dos causas distintas, anotadas en la partitura:

- La pasajera acomoda la bolsa a 8.4 s y 28.4 s. Es un gesto escrito de tres
  contactos, separados por 3 y 2 unidades. La mbira lo aprende con aumentación
  al doble y completa sus huecos por episodios. Primero se oye la fuente.
- Los baches y las frenadas generan **32 contactos calculados** por tres
  osciladores con topes. La excitación es una combinación escalada de aceleración
  y curvatura del perfil; el factor es una elección compositiva, no una medición
  de una bolsa real. Estos accidentes no se cuantizan al compás.

Al final baja la pasajera y la radio recuerda el silbato; el clarinete lo recoge.
La duda sobre quién suena tiene un objeto presentado, una transformación y una
persistencia. Es una ambigüedad preparada; su eficacia queda pendiente de escucha.

## ¿La partitura es suficientemente compleja?

Ahora tiene **30 partes y {n} eventos**, menos eventos que los 3961 de r3. Se
eliminó densidad automática para escribir relevos, huecos y una avería de veinte
segundos. El número no acredita complejidad. Las relaciones nuevas sí pueden
señalarse: motivos entre objetos e instrumentos, campos armónicos con residuo,
relojes con historia y un retorno matemático que cambia la distribución de voces.

La edición contiene un PDF de dirección de 17 páginas, MusicXML con las treinta
partes, JSON íntegro y CSV con todos los parámetros. Los diagramas del PDF no
pretenden sustituir treinta pentagramas grabados. En 180–200 s las divisiones del
archivo son coordenadas de edición: MusicXML indica *senza misura*. No se debe
reintroducir un click audible para contar esos ocho segmentos.

## Tema, cambios, percusión y solo

| Material inicial | Operación | Consecuencia | Pasaje |
|---|---|---|---|
| Cabeza D-A-Ab, nota insistida y hueco | Relevos acordeón/láser/clarinete, respuestas que ocupan huecos | La frase conserva identidad sin duplicarse entera | 10–70 s; regreso 170 s; coda 220 s |
| Tres contactos de la bolsa | Aumentación x2, sustitución gradual de silencios | La mbira aprende algo que ya oímos; los accidentes no siguen ese aprendizaje | Bolsa 8.4 s; mbira desde 40 s |
| Campo D/A | Tercera 6/5; entrada de 7/4 con lluvia; residuo 11/8 tras avería | El regreso no reinicia el mismo bucle de acordes | 0–100; 100–180; 200–240 s |
| Din/ta/thom | Subdivisiones 4, 3 y 5; conversación con barro/pandero; remates triplicados | La percusión frasea; su carga cambia y un ataque queda pendiente | 20–180; 200–220 s |
| Motivo del solo | A, B, inversa de A, inversa de B sobre tres amplitudes firmadas | El sitio del circuito se cierra; la voz resultante cambia | 130–170 s |
| Recorrido del transporte | Ascenso, descenso corto, nueva subida, retroceso y parada | Mayor presión y notas más cortas al subir; aperturas al bajar | Perfil en `viaje.json` |
| Frase aprendida | Corte de todos los buses métricos y sus colas | Desaparece la posibilidad de continuar bailando en piloto automático | 180–200 s |
| Primer ataque esperado | Omisión en la membrana, con bajo/bombo de regreso | La deuda pertenece a una voz; hay que comprobar que no la tape la base | 200 s |

Cruce de prácticas: ancla y contratiempos de cumbia sonidera; organización de
subdivisiones, articulaciones y remates inspirada en recursos carnáticos; repetición
y bordones del jazz contemporáneo; construcción por huecos de Reich y contactos
de Lachenmann. No se llama mridangam real a una membrana sin calibrar ni se promete
una interpretación tradicional por usar esos recursos. Las referencias de la
primera etapa siguen en [REFERENCIAS](../REFERENCIAS.md).

### ¿El solo es A, B, C o D?

A: requinto virtuoso, descartado por Canek. B: láser haciendo pius sin transformar
la frase. C: aplicar Talbot como efecto a una frase terminada. **D: la misma célula
atraviesa un circuito que cambia quién puede emitirla y con qué signo.**

A rota las voces 1–2 por 0.73 rad; B rota 2–3 por 1.07 rad. Son ángulos elegidos
por el compositor, no derivados de una ley del terreno. El producto del circuito
es `C = B⁻¹ A⁻¹ B A`. Conserva norma, pero no es identidad. Error de ortogonalidad:
2.22e-16. Distancia de C a la identidad, norma de Frobenius: 1.01228. El estado
inicial `[1,0,0]` regresa aproximadamente `[.76880,.38911,.50748]`.

El circuito local del láser recorre los nodos radiales `(2,3), (2,5), (4,5), (4,3),
(2,3)`. El autobús sigue mientras tanto otro recorrido. No se afirma que haya
holonomía física medida en el mapa: se construyó una conexión para componer. La
conservación de norma del controlador tampoco es conservación de energía de la
mezcla, que incluye síntesis, interferencia y pérdidas en los retardos.

Lo extraño está en conservar la frase y cambiar su dueño al cerrar el circuito.
Es realizable con las tres versiones del láser y sus fases; no exige prometer
un sonido que el motor no pueda producir. Falta escuchar si el efecto se percibe
como desarrollo o sólo como un cambio de plano. Esa es una objeción real.

## Subida, bajada y clima

El viaje mide **{v['distancia_m']/1000:.3f} km**, con **{v['ascenso_m']:.2f} m** de
ascenso y **{v['descenso_m']:.2f} m** de descenso acumulados. Vuelve a la misma
cota: {v['origen_m']:.2f} m; llega a {v['cota_mayor_m']:.2f} m. Las alturas salen
de la lámina de Traspuesta; el autobús, las conexiones y el reloj son compuestos.

La pendiente cambia duración y presión, no sólo si una nota sube o baja. La lluvia
es un arco inventado entre 92 y 225 s; carga la membrana de 0.5 a 2.3 y oscurece
las articulaciones. No se presenta como pronóstico ni modelo de humedad real.
Las tres voces del tráfico conservan fase integrada desde el inicio: su retardo
acotado se calcula con esa historia, sin volver a cero cada dos compases.

## La avería a tres cuartos

**3:00–3:20**, inicio al 73.17% de los 4:06 previstos. Se eligió una avería por
calentamiento en la última subida. El tráfico no predice esa avería: es el
acontecimiento dramático compuesto. No hay batería, ostinato ni un drone pulsado
que conserve el baile debajo. A 179.960 s se ordena un corte de 35 ms y vaciado de
los retardos de láser, Talbot y reverberación.

| Segundo | Acontecimiento libre |
|---|---|
| 180.80 | Chofer: se calentó, esperen |
| 182.17 | Pitido distante |
| 184.63 | Primer arranque fallido |
| 187.30 | Pasajera recuerda que falta el primer golpe |
| 189.41 | Pitido doble, sin ciclo |
| 192.87 | Segundo intento fallido |
| 196.23 | Un solo golpe de dedo; no completa la célula |
| 197.61 | El motor prende sin fijar compás |
| 198.30 | «Ahora sí. Despacito.» |
| 200.00 | Regresa la base; falta el primer ataque de membrana |

No hay riser, redoble ni rampa de tempo. Al producir habrá que comprobar el corte
también en la señal: el silencio de eventos por sí solo no demuestra que se hayan
apagado los efectos.

## Instrumentos y límites de la etapa

Se conservan láser/red/Talbot, membrana cargada por FEM, raspador del depósito,
barro y pandero ya construidos. Se añaden **bolsa de impactos** y **motor que
falla**. El controlador de transbordos es una operación compositiva, no otro
instrumento contado para inflar la lista. El vibráfono cede su parte a la bolsa.
Acordeón, bajo, batería, güiro/conga/campana, mbira/boca, guembri/órgano, clarinete,
chelo y voces de la biblioteca conservan papeles diferenciados.

Código nuevo: `instrumentos_revision.py`. Genera timbres y controladores, pero no
se produjo audio completo ni una escucha nueva de esta revisión. Las sondas de
la primera etapa siguen disponibles y no representan este arreglo corregido.

Contrato de futura interpretación: JSON guarda `carga_central`, `fase_signo`,
`pendiente`, `corte_agudos_hz`, `objeto` y `fuerza_impacto`; `viaje.json` guarda el
clima y la velocidad globales. La radio deberá usar ese arco de clima, sin que
su habla se sincronice a la base. Aplicar signos antes de redes, cambiar realmente
los modos de membrana y vaciar los buses. Estos parámetros todavía no han sido
comprobados sobre una interpretación completa. MusicXML conserva alteraciones
fraccionarias y redondea tiempo a 960 ticks/pulso; no contiene todo el instrumento.

## Qué mirar antes de aprobar

1. Identidad de la frase: ¿se reconoce al pasar de objeto a mbira y láser, o la
   explicación escrita hace más trabajo que la música? Probar primero sin letra.
2. Percusión: ¿hay conversación y aire, como buscamos en las anteriores, o sólo
   subdivisiones correctas? No aprobar ese punto por una cuenta de golpes.
3. Silencio y regreso: ¿se pierde el compás durante la avería y se oye el ataque
   faltante al volver? La prueba requiere las colas reales al interpretar.
4. Texto: ¿los juguetes vuelven entendible la historia sin volverla demasiado
   literal? El ala rota podría resultar innecesaria; conservarla sólo si la voz
   le encuentra un lugar. La coda debe sostener su ambigüedad sin explicación extra.

[Compositor: preguntas reutilizables](../../COMPOSITOR.md). Skill local en
`../../.agents/skills/compositor/`. Esta revisión entrega escritura y motores;
**se detiene aquí para verla contigo antes de renderizar la canción.**
'''
    guardar(out/'REVISION-COMPOSITIVA.md',txt.encode('utf8'))
    guardar(out/'PARADA-PARA-REVISION.md',('Revisión compositiva lista. Ver REVISION-COMPOSITIVA.md, partitura PDF, MusicXML y JSON.\nNo renderizar la canción antes de revisarla con Canek. Visor después; video completo a cargo de Canek.\n').encode('utf8'))
    print(out/'REVISION-COMPOSITIVA.md')

if __name__=='__main__':main()
