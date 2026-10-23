/* waterphone.js — el waterphone (instrumento 8 de «objetos que cantan»).
 *
 * Una vasija de acero con agua adentro y un anillo de varillas de bronce de largos distintos (Richard Waters, años 60).
 * Cada varilla es una barra empotrada de un lado y libre del otro: sus modos están en 1 : 6.267 : 17.55 : 34.39 (viga en
 * voladizo), así que suena casi a seno con un brillo metálico muy arriba. Las varillas no siguen ninguna escala.
 * El agua: al inclinar la vasija, el agua se mueve dentro del resonador y dobla la altura de todo hacia abajo y de
 * regreso (el gemido del waterphone). Aquí: f(t) × 2^(−agua·w(t)/12), con w que va y viene de 0 a 1 a «ola» Hz.
 * La vasija también suena: modos inarmónicos graves que se encienden por simpatía con cada varilla.
 *
 *   'arco'      el arco en una varilla: crece lento, sostiene con la aspereza del arco, se apaga en sus modos
 *   'golpe'     un dedo o una baqueta: ataque seco, cola larga
 *   'bola'      la superbola frotando la vasija: un gemido grave que se arrastra y cambia de modo (stick-slip)
 *   evento: {t, tipo, vara (índice 0-23) o m (nota midi), dur, v, agua (semitonos de doblez), ola (Hz del vaivén)}
 *
 *   Waterphone.render({dur, eventos, semilla}, sr) → Float32Array;  Waterphone.varas(semilla) → frecuencias
 */
(function (global) {
  'use strict';
  var M = typeof require !== 'undefined' ? require('./modos.js') : global.Modos;
  var VOLADIZO = [1, 6.267, 17.55, 34.39];
  var VASIJA = [[143, 9], [231, 7], [389, 6], [517, 5], [702, 4], [911, 3.5], [1288, 3], [1704, 2.4], [2210, 2]];   // [Hz, T60 s]
  // 24 varillas: largos sembrados, sin escala; la frecuencia va como 1/L² (de ~300 Hz a ~2 kHz)
  function varas(semilla) {
    var r = M.rngDe(semilla || 8), L = [];
    for (var k = 0; k < 24; k++) L.push(1 - .62 * (k + r() * .8) / 24);
    return L.map(function (l) { return 300 / (l * l); });
  }
  function render(c, sr) {
    sr = sr || 48000;
    var y = new Float32Array(Math.ceil(c.dur * sr)), r = M.rngDe(c.semilla || 8), V = varas(c.semilla || 8);
    c.eventos.forEach(function (ev) {
      var f0 = ev.m != null ? M.hz(ev.m) : V[ev.vara || 0], v = ev.v == null ? .7 : ev.v, d = ev.dur || 2, ag = ev.agua || 0, ola = ev.ola || .4;
      var dobla = function (u) { return ag ? Math.pow(2, -ag * (.5 - .5 * Math.cos(2 * Math.PI * ola * u)) / 12) : 1; };
      if (ev.tipo === 'arco' || ev.tipo === 'golpe') {
        var arco = ev.tipo === 'arco';
        VOLADIZO.forEach(function (q, k) {
          var T = (arco ? 5 : 7) / Math.pow(q, .55), a0 = v * (arco ? [1, .06, .02, .008] : [1, .35, .18, .1])[k], dk = M.T60(T);
          // el arco: crece en 0.3 s, sostiene con aspereza (el pelo engancha y suelta: ±12 % a ~31 Hz) y se apaga desde dur
          var grano = []; for (var g = 0; g < 4000; g++) grano.push(r());
          var env = arco ? function (u) {
            var s = Math.min(1, u / .3) * (u < d ? 1 : Math.exp(-dk * (u - d)));
            return a0 * s * (1 + .24 * (grano[Math.floor(u * 31) % 4000] - .5));
          } : function (u) { return a0 * Math.min(1, u / .0015) * Math.exp(-dk * u); };
          M.sumar(y, sr, { t0: ev.t, fin: ev.t + (arco ? d : 0) + T, f: function (u) { return f0 * q * dobla(u); }, a: env, fase: r() * 6.28 });
        });
        // la vasija suena por simpatía: más el modo cercano a la varilla
        VASIJA.forEach(function (b) {
          var a0 = v * .05 * Math.exp(-Math.abs(Math.log2(b[0] / f0)) * 2.5), dk = M.T60(b[1]), suelta = arco ? d : 0;
          if (a0 > .002) M.sumar(y, sr, { t0: ev.t, fin: ev.t + suelta + b[1], f: function (u) { return b[0] * dobla(u); },
            a: function (u) { return a0 * Math.min(1, u / (arco ? .5 : .01)) * Math.exp(-dk * Math.max(0, u - suelta)); } });
        });
      } else if (ev.tipo === 'bola') {
        // la superbola: la goma se pega y se suelta contra la vasija; cada tramo elige un modo grave y lo arrastra
        var tt = 0, ultimo = -1;
        while (tt < d) {
          var tramo = .25 + r() * .6, k = Math.floor(r() * 5); if (k === ultimo) k = (k + 1) % 5; ultimo = k;
          (function (b, t1, len, sube) {
            var dk = M.T60(b[1] * .5), a0 = v * 1.1;   // ×1.1: con .55 la bola quedaba 6 dB bajo los arcos (medido)
            M.sumar(y, sr, { t0: ev.t + t1, fin: ev.t + t1 + len + b[1] * .5, f: function (u) { return b[0] * Math.pow(2, sube * Math.min(1, u / len) / 12) * dobla(t1 + u); },
              a: function (u) { var s = Math.min(1, u / (len * .4)) * (u < len ? 1 : Math.exp(-dk * (u - len))); return a0 * s * (.6 + .4 * Math.sin(2 * Math.PI * 23 * u + Math.sin(u * 7))); } });
          })(VASIJA[k], tt, tramo, (r() - .5) * 3);
          tt += tramo * .7;
        }
      }
    });
    return y;
  }
  var api = { render: render, varas: varas, VOLADIZO: VOLADIZO, VASIJA: VASIJA };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.Waterphone = api;
})(typeof window !== 'undefined' ? window : globalThis);
