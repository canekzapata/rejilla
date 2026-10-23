/* partitura.js — «el tiempo es la altura»: canon de tempos de los objetos que cantan (loop B).
 *
 * Nancarrow (y antes Cowell, en «New Musical Resources»): el ritmo y la altura son la misma cosa a distinta escala.
 * Aquí cada voz toca el MISMO sujeto a un tempo r veces el de la voz de agua, y transpuesto por la misma razón r:
 * la voz que va a 3/2 suena una quinta justa arriba; la que va a 4/7, una séptima armónica abajo (−969 cents). Las razones
 * forman un acorde justo alrededor de la voz (7 y 5 dan los microtonos: −31 y −14 cents contra el temperado).
 * Las voces entran de lentas a rápidas y CONVERGEN: en Tc todas empiezan el sujeto juntas (el tam-tam). Después cada una
 * toca una vuelta más y se va, de rápidas a lentas. Cada objeto cambia de naturaleza en la convergencia.
 *
 * El sujeto sale de la letra: una nota por sílaba (sílabas y acentos del tambor parlante); las sílabas con acento duran
 * más y saltan; cada verso cae al final; el último cae a la tónica. Modo: Mi locrio (oscuro, con la quinta disminuida).
 *
 *   node pieza/partitura.js            → imprime el sujeto y el calendario
 *   require('./partitura.js')          → { SUJETO, VOCES, voz(nombre) → notas absolutas, TC, DUR, ... }
 */
const T = require('../motor/tambor.js');
const LETRA = ['el tiempo es la altura', 'cada cosa canta a su paso', 'cuando todas se tocan', 'suena una sola boca'];
const LOCRIO = [0, 1, 3, 5, 6, 8, 10], TONICA = 52, BEAT = .5;     // Mi3; el beat de la voz de agua (r = 1)
const rngDe = (s) => { let h = s >>> 0 || 1; return () => { h ^= h << 13; h >>>= 0; h ^= h >> 17; h ^= h << 5; h >>>= 0; return h / 4294967296; }; };
const grado = (g) => TONICA + LOCRIO[((g % 7) + 7) % 7] + 12 * Math.floor(g / 7);

// el sujeto: [{b (beat de inicio), d (beats), m (midi), silaba, acento, verso}]
function sujeto(semilla) {
  const r = rngDe(semilla || 1957); const S = []; let b = 0, g = 2;
  LETRA.forEach((verso, iv) => {
    const sil = T.silabas(verso);
    sil.forEach((s, k) => {
      const ultima = k === sil.length - 1;
      // el contorno: los acentos saltan (3-5 grados hacia arriba si estamos abajo, o hacia abajo si estamos arriba); lo átono camina
      if (s.acento) g += (g < 4 ? 1 : -1) * (3 + Math.floor(r() * 3)) * (r() < .25 ? -1 : 1);
      else g += g <= -2 ? 1 : g >= 8 ? -1 : r() < .5 ? -1 : 1;              // lo átono camina, rebotando en las orillas
      if (ultima) g = iv === LETRA.length - 1 ? 0 : [-2, 1, -1][iv];    // el verso cae; el último, a la tónica
      if (g < -2) g = -2 + (-2 - g); if (g > 9) g = 9 - (g - 9);           // (con un tope duro se quedaba pegado: Re, Re, Re, Re)
      const d = s.acento ? 1.5 : ultima ? 2 : .75;
      S.push({ b, d, m: grado(g), silaba: s.letras, acento: s.acento, inicio: s.inicio, verso: iv });
      b += d + (s.finPalabra ? .25 : 0);
    });
    b += 1.25;                                                          // respira entre versos
  });
  return { notas: S, beats: b };
}
const SUJETO = sujeto();
const P1 = SUJETO.beats * BEAT;                                         // segundos de una vuelta del sujeto a r = 1

// las voces: razón (tempo = altura), objeto, octavas de más, entrada (s), transformación en la convergencia
const TC = 118, DUR = 200;
const VOCES = [
  { nombre: 'contrabajo', r: 4 / 7, oct: 0, entra: 8, antes: 'arco', despues: 'pizz que se vuelve house' },
  { nombre: 'trombon', r: 2 / 3, oct: 0, entra: 22, antes: 'abierto con growl en los acentos', despues: 'plunger (wah)' },
  { nombre: 'tambor', r: 4 / 5, oct: 0, entra: 36, antes: 'centro y borde', despues: 'palo y apretones más hondos' },
  { nombre: 'vozagua', r: 1, oct: 0, entra: 48, antes: 'el agua aprende a hablar (voz 0 → 1)', despues: 'dos vocales a la vez en los acentos' },
  { nombre: 'sax', r: 5 / 4, oct: 0, entra: 62, antes: 'saxofón que se vuelve flauta', despues: 'flauta que se vuelve golpe' },
  { nombre: 'piano', r: 3 / 2, oct: 0, entra: 76, antes: 'sin preparar', despues: 'con tornillos (campanas)' },
  { nombre: 'pajaro', r: 7 / 4, oct: 2, entra: 90, antes: 'canto', despues: 'canto con la segunda voz de la siringe' },
];
// las notas absolutas de una voz: vueltas alineadas para que una empiece exactamente en TC; suena desde su entrada
// hasta terminar la vuelta que empieza en TC (sale después de una vuelta tras la convergencia)
function voz(nombre) {
  const V = VOCES.find((v) => v.nombre === nombre), per = P1 / V.r, sale = TC + per, out = [];
  const semi = 12 * Math.log2(V.r) + 12 * V.oct;
  for (let k = Math.floor((V.entra - TC) / per); TC + k * per < sale - 1e-6; k++) {
    const t0 = TC + k * per;
    SUJETO.notas.forEach((n, j) => {
      const t = t0 + n.b * BEAT / V.r; if (t < V.entra - 1e-6) return;
      out.push({ ...n, t, dur: n.d * BEAT / V.r, m: n.m + semi, vuelta: k, despues: t0 >= TC - 1e-6, j });
    });
  }
  return { ...V, semi, per, sale, notas: out };
}
module.exports = { LETRA, SUJETO, VOCES, voz, TC, DUR, BEAT, P1, TONICA };

if (require.main === module) {
  console.log('sujeto:', SUJETO.notas.length, 'sílabas,', SUJETO.beats, 'beats =', P1.toFixed(1), 's a r = 1');
  console.log(SUJETO.notas.map((n) => (n.acento ? n.silaba.toUpperCase() : n.silaba) + ':' + n.m).join(' '));
  VOCES.forEach((v) => { const V = voz(v.nombre); console.log(v.nombre.padEnd(10), 'r', v.r.toFixed(3), 'semitonos', V.semi.toFixed(2), 'vuelta', V.per.toFixed(1), 's  entra', v.entra, 'sale', V.sale.toFixed(1), 'notas', V.notas.length, 'rango', Math.min(...V.notas.map((n) => n.m)).toFixed(1), '-', Math.max(...V.notas.map((n) => n.m)).toFixed(1)); });
}
