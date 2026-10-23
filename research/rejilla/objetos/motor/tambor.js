/* tambor.js — el tambor parlante (instrumento 10 de «objetos que cantan»).
 *
 * El dùndún yoruba (y el kalangu hausa, el donno ashanti): un tambor de reloj de arena con dos parches unidos por
 * cuerdas. Bajo el brazo, apretar las cuerdas tensa el parche y la altura sube; como el yoruba es una lengua tonal,
 * el tambor «dice» frases imitando sus tonos. Aquí:
 *  - el parche es una membrana circular: modos 1 : 1.59 : 2.14 : 2.30 : 2.65 : 2.92 : 3.16 : 3.50, un poco
 *    comprimidos hacia lo armónico por el aire que carga el parche;
 *  - la altura es f(t) = f0 · √(tensión(t)): la tensión viene del apretón (curva de semitonos) más la no linealidad
 *    del golpe (un golpe fuerte estira el parche: la altura arranca arriba y cae en ~80 ms, el «boing»);
 *  - golpes: 'centro' (grave y redondo), 'borde' (agudo, poco fundamental), 'apagado' (la mano lo frena), 'palo'
 *    (el palo curvo: un chasquido brillante encima).
 * El español no es tonal, pero tiene acento: 'habla' parte una frase en sílabas (de la ortografía), le da a cada una un
 * golpe y a la sílaba con acento el parche más tenso; la frase cae al final (o sube, si es pregunta). La consonante
 * con que empieza la sílaba elige el golpe (p t k → palo; m n l → centro; s f j → borde; r → un redoble corto).
 *
 *   evento golpe: {t, tipo, m, v, curva: [[u, semitonos]…]}
 *   evento habla: {t, tipo: 'habla', texto, m, dur (por sílaba), v, alto (semitonos del acento)}
 *   Tambor.render({dur, eventos, semilla}, sr) → Float32Array;  Tambor.silabas(texto) → [{letras, acento, inicio}]
 */
(function (global) {
  'use strict';
  var M = typeof require !== 'undefined' ? require('./modos.js') : global.Modos;
  var PARCHE = [1, 1.59, 2.14, 2.30, 2.65, 2.92, 3.16, 3.50].map(function (q) { return 1 + (q - 1) * .9; });
  var GOLPE = {   // amplitud por modo, T60 del fundamental (s), chasquido
    centro: { a: [1, .45, .3, .12, .1, .06, .05, .03], T: 1.4, clic: .05 },
    borde: { a: [.25, .6, .55, .5, .4, .35, .3, .25], T: .9, clic: .15 },
    apagado: { a: [1, .4, .25, .1, .08, .05, .04, .02], T: .18, clic: .08 },
    palo: { a: [.8, .55, .45, .3, .25, .2, .18, .15], T: 1.1, clic: .5 }
  };
  var VOCAL = 'aeiouáéíóúü', FUERTE = 'aeoáéíóú';
  var ATONAS = ' el la los las lo le les de del que y a al en con por para me te se nos mi tu su sus un ';   // monosílabos sin acento

  // sílabas por núcleos vocálicos (i/u sin tilde junto a otra vocal = diptongo); acento: la tilde, si no la regla llana/aguda
  function silabas(texto) {
    var out = [];
    texto.toLowerCase().replace(/[^a-záéíóúüñ\s]/g, '').split(/\s+/).filter(Boolean).forEach(function (pal) {
      var nuc = [], i = 0, ini = 0;
      while (i < pal.length) {
        if (VOCAL.indexOf(pal[i]) >= 0) {
          var j = i + 1;
          while (j < pal.length && VOCAL.indexOf(pal[j]) >= 0 && !(FUERTE.indexOf(pal[j]) >= 0 && FUERTE.indexOf(pal[j - 1]) >= 0)) j++;
          // el ataque de la sílaba: la última consonante antes del núcleo (o las dos últimas si es bl, tr…); su primera letra elige el golpe
          var cons = pal.slice(ini, i), ata = cons.length > 1 && 'lr'.indexOf(cons[cons.length - 1]) >= 0 && 'lr'.indexOf(cons[cons.length - 2]) < 0 ? cons.slice(-2) : cons.slice(-1);
          if (nuc.length) nuc[nuc.length - 1].letras += cons.slice(0, cons.length - ata.length);
          nuc.push({ letras: pal.slice(i - ata.length, j), inicio: ata[0] || '', tilde: /[áéíóú]/.test(pal.slice(i, j)) }); ini = j; i = j;
        } else i++;
      }
      if (!nuc.length) return;
      nuc[nuc.length - 1].letras += pal.slice(ini);
      var t = nuc.findIndex(function (n) { return n.tilde; }), ult = pal[pal.length - 1];
      if (t < 0) t = nuc.length === 1 ? 0 : ('aeiouns'.indexOf(ult) >= 0 ? nuc.length - 2 : nuc.length - 1);
      if (nuc.length === 1 && ATONAS.indexOf(' ' + pal + ' ') >= 0) t = -1;
      nuc.forEach(function (n, k) { out.push({ letras: n.letras, inicio: n.inicio, acento: k === t, finPalabra: k === nuc.length - 1 }); });
    });
    return out;
  }

  function render(c, sr) {
    sr = sr || 48000;
    var y = new Float32Array(Math.ceil(c.dur * sr)), r = M.rngDe(c.semilla || 10), golpes = [];
    c.eventos.forEach(function (ev) {
      if (ev.tipo !== 'habla') { golpes.push(ev); return; }
      // la frase: cada sílaba un golpe; el acento arriba; la última sílaba cae (o sube con «?»)
      var sil = silabas(ev.texto), d = ev.dur || .22, alto = ev.alto == null ? 4 : ev.alto, pregunta = /\?\s*$/.test(ev.texto), t = ev.t, prev = 0;
      sil.forEach(function (s, k) {
        var nivel = s.acento ? alto : 0, ultima = k === sil.length - 1, ini = s.inicio;
        var tipo = 'ptkbdgcq'.indexOf(ini) >= 0 ? 'palo' : 'sfjzx'.indexOf(ini) >= 0 ? 'borde' : 'centro';
        // el apretón: la altura llega desde la sílaba anterior en 50 ms, y en la última se desliza (cae 3, o sube 5)
        var curva = [[0, prev], [.05, nivel]]; if (ultima) curva.push([d * 2.2, nivel + (pregunta ? 5 : -3)]);
        golpes.push({ t: t, tipo: tipo, m: ev.m, v: (ev.v || .75) * (s.acento ? 1 : .75), curva: curva, silaba: s.letras });
        if (ini === 'r' || s.letras.indexOf('rr') >= 0) golpes.push({ t: t + .045, tipo: 'apagado', m: ev.m, v: .35, curva: [[0, nivel]] });
        t += d * (s.finPalabra ? 1.35 : 1) * (s.acento ? 1.15 : 1); prev = nivel;
      });
    });
    golpes.forEach(function (ev) {
      var G = GOLPE[ev.tipo] || GOLPE.centro, v = ev.v == null ? .75 : ev.v, f0 = M.hz(ev.m == null ? 45 : ev.m), cv = ev.curva || [[0, 0]];
      var tension = function (u) {                                       // semitonos del apretón en u (interpolación lineal)
        if (u <= cv[0][0]) return cv[0][1];
        for (var k = 1; k < cv.length; k++) if (u < cv[k][0]) return cv[k - 1][1] + (cv[k][1] - cv[k - 1][1]) * (u - cv[k - 1][0]) / (cv[k][0] - cv[k - 1][0]);
        return cv[cv.length - 1][1];
      };
      PARCHE.forEach(function (q, k) {
        var T = G.T / Math.pow(q, 1.3), dk = M.T60(T), a0 = v * G.a[k] * .4;
        M.sumar(y, sr, { t0: ev.t, fin: ev.t + T, fase: r() * 6.28,
          f: function (u) { return f0 * q * Math.pow(2, (tension(u) + 1.2 * v * Math.exp(-u / .08)) / 12); },   // + el «boing» del golpe
          a: function (u) { return a0 * Math.min(1, u / .0015) * Math.exp(-dk * u); } });
      });
      // el chasquido de la mano o del palo: ruido corto y brillante (escrito directo al búfer)
      var i0 = Math.floor(ev.t * sr), n = Math.floor(.012 * sr), lp = 0;
      for (var i = 0; i < n && i0 + i < y.length; i++) { var x = r() * 2 - 1; lp += .35 * (x - lp); y[i0 + i] += (x - lp) * v * G.clic * .5 * Math.exp(-i / (n * .25)); }
    });
    return y;
  }
  var api = { render: render, silabas: silabas, PARCHE: PARCHE };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.Tambor = api;
})(typeof window !== 'undefined' ? window : globalThis);
