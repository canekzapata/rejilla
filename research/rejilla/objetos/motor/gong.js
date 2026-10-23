/* gong.js — gong y tam-tam no lineales (instrumento 9 de «objetos que cantan»).
 *
 * Una placa delgada que vibra fuerte es no lineal: su rigidez depende de la amplitud. Eso hace dos cosas que un modelo
 * lineal no tiene:
 *  - en el tam-tam la energía se pasa de los modos graves a los agudos después del golpe: el brillo «florece» medio
 *    segundo o más tarde (el crescendo del tam-tam). Aquí cada modo agudo crece con un retraso τ que sube con la
 *    frecuencia y con la fuerza del golpe (la transferencia va como v²);
 *  - en los gongs de ópera china (con el centro abombado) la altura depende de la amplitud: el xiaoluo empieza abajo
 *    y SUBE mientras se apaga, el daluo empieza arriba y BAJA. f(u) = f0 · 2^(−s·A(u)²/12), A = amplitud que cae.
 * Y el gong de dos alturas que se cruzan: dos modos del mismo gong con la dependencia de signo contrario (uno sube,
 * otro baja), arrancando a una distancia que se cierra hasta cruzarse; al cruzarse baten.
 *
 *   'tamtam'  {m (modo grave), v, dureza 0-1}            'opera'  {m, v, sube (semitonos; + sube, − baja)}
 *   'cruce'   {m (donde se cruzan), v, abre (semitonos de separación inicial)}
 *   'arco'    el arco en el borde del tam-tam: crece despacio, silba en modos agudos que cambian {m, dur, v}
 *   'roce'    la superbola en la cara del tam-tam: gemidos graves arrastrados {dur, v}
 *
 *   Gong.render({dur, eventos, semilla}, sr) → Float32Array;  Gong.modosTamtam(semilla) → razones
 */
(function (global) {
  'use strict';
  var M = typeof require !== 'undefined' ? require('./modos.js') : global.Modos;
  // modos de una placa circular grande: cada vez más densos hacia arriba (razón 1 a ~160), sembrados
  function modosTamtam(semilla) {
    var r = M.rngDe(semilla || 9), q = [];
    for (var k = 0; k < 90; k++) q.push(Math.exp(Math.log(160) * Math.pow(k / 89, .78)) * (1 + (r() - .5) * .05));
    return q.sort(function (a, b) { return a - b; });
  }
  var OPERA = [[1, 1], [1.52, .35], [2.09, .3], [2.63, .12], [3.41, .08]];   // [razón, amplitud]: el centro abombado da un modo dominante
  function render(c, sr) {
    sr = sr || 48000;
    var y = new Float32Array(Math.ceil(c.dur * sr)), r = M.rngDe(c.semilla || 9), TT = modosTamtam(c.semilla || 9);
    c.eventos.forEach(function (ev) {
      var v = ev.v == null ? .7 : ev.v, f0 = M.hz(ev.m == null ? 33 : ev.m);
      if (ev.tipo === 'tamtam') {
        var du = ev.dureza == null ? .5 : ev.dureza;
        TT.forEach(function (q, k) {
          var f = f0 * q; if (f > 15000) return;
          var T = 18 / Math.pow(q, .35), dk = M.T60(T);
          // golpe: los graves reciben la energía directa; los agudos la reciben después, por la no linealidad (∝ v²)
          var directo = v * Math.pow(q, -.9 + .5 * du) * (q > 4 ? .4 : 1), tau = .02 + .45 * v * Math.pow(Math.min(1, q / 60), .8), flor = v * v * .6 * Math.pow(q, -.25) * (q > 4 ? 1 : 0);
          var fin = Math.min(T, 12), a0 = r() * 6.28, tr = 3 + r() * 4;
          M.sumar(y, sr, { t0: ev.t, fin: ev.t + fin, fase: a0,
            f: function (u) { return f * (1 + .0015 * v * Math.exp(-u * 2) * Math.sin(u * tr)); },       // un temblor chico mientras es fuerte
            a: function (u) { return (directo * Math.min(1, u / (.001 + .006 * (1 - du))) + flor * (1 - Math.exp(-u / tau))) * Math.exp(-dk * u) * .3; } });
        });
      } else if (ev.tipo === 'opera' || ev.tipo === 'cruce') {
        var cruce = ev.tipo === 'cruce', s = ev.sube == null ? 2 : ev.sube, ab = ev.abre == null ? 4 : ev.abre;
        var T1 = cruce ? 6 : 3.5, d1 = M.T60(T1), A2 = function (u) { var a = Math.exp(-d1 * u * .9); return a * a; };   // A(u)²: la altura se mueve rápido al principio
        // en el cruce la altura se mueve más despacio que la amplitud (se cruzan a ~1.2 s): con A² se cruzaban a los 0.2 s y no se oía (medido)
        if (cruce) A2 = function (u) { return Math.exp(-u / 1.7); };
        var modos = cruce ? [[1, 1, +1], [1, .85, -1], [2.09, .25, 0], [2.63, .1, 0]] : OPERA.map(function (o) { return [o[0], o[1], 1]; });
        modos.forEach(function (o, k) {
          // en el cruce: el modo 0 arranca abre/2 abajo y sube; el modo 1 arranca abre/2 arriba y baja; se cruzan cuando A² = ½
          // en la ópera la desviación crece con la fuerza del golpe (v): un golpe suave casi no se mueve
          var T = T1 / Math.pow(o[0], .4), dk = M.T60(T);
          var ff = cruce && o[2] ? function (u) { return f0 * Math.pow(2, o[2] * ab / 2 * (1 - 2 * A2(u)) / 12); }   // de ∓abre/2 a ±abre/2, cruzando en f0
            : function (u) { return f0 * o[0] * Math.pow(2, (cruce ? 0 : -s * v) * A2(u) / 12); };
          M.sumar(y, sr, { t0: ev.t, fin: ev.t + T, fase: r() * 6.28, f: ff,
            a: function (u) { return v * o[1] * Math.min(1, u / .003) * Math.exp(-dk * u) * .5; } });
        });
        // el golpe de la baqueta en el gong: ruido corto filtrado alto
        M.sumar(y, sr, { t0: ev.t, fin: ev.t + .03, f: function () { return 3000 + 4000 * r(); }, a: function (u) { return v * .08 * Math.exp(-u * 160); } });
      } else if (ev.tipo === 'arco' || ev.tipo === 'roce') {
        // frotar: algunos modos se encienden y apagan por turnos (el arco silba en agudos; la bola gime en graves)
        var d = ev.dur || 4, n = ev.tipo === 'arco' ? 14 : 8;
        for (var k = 0; k < n; k++) (function (k) {
          var arco = ev.tipo === 'arco', q = arco ? TT[30 + Math.floor(r() * 50)] : TT[2 + Math.floor(r() * 14)], f = f0 * q, ini = r() * d * .6, len = .6 + r() * d * .6;
          var T = arco ? 5 : 3, dk = M.T60(T), sube = arco ? 0 : (r() - .5) * 4, g = (arco ? .24 : .35) * v * (.4 + .6 * r());
          M.sumar(y, sr, { t0: ev.t + ini, fin: ev.t + ini + len + T, fase: r() * 6.28,
            f: function (u) { return f * Math.pow(2, sube * Math.min(1, u / len) / 12); },
            a: function (u) { var e = u < len ? Math.pow(Math.sin(Math.PI / 2 * Math.min(1, u / (len * .7))), 2) : Math.exp(-dk * (u - len)); return g * e * (arco ? 1 : .7 + .3 * Math.sin(2 * Math.PI * 19 * u)); } });
        })(k);
        if (ev.tipo === 'arco') TT.slice(0, 6).forEach(function (q) {     // el arco también levanta un fondo grave
          M.sumar(y, sr, { t0: ev.t, fin: ev.t + d + 6, fase: r() * 6.28, f: function () { return f0 * q; },
            a: function (u) { return v * .2 * Math.min(1, u / (d * .8)) * (u < d ? 1 : Math.exp(-M.T60(6) * (u - d))); } });
        });
      }
    });
    return y;
  }
  var api = { render: render, modosTamtam: modosTamtam, OPERA: OPERA };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.Gong = api;
})(typeof window !== 'undefined' ? window : globalThis);
