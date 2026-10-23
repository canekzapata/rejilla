/* garganta_volcan.js — la garganta de volcán: un instrumento imposible para «¿Por quién se toma la tierra?».
 *
 * Es la garganta de montaña (garganta.js, de la biblioteca de instrumentos: una siringe dentro de un tubo de Kelly-Lochbaum con la
 * forma de un perfil del terreno), pero el tubo ENVEJECE con el volcán: sus perfiles son el mismo corte del volcán 177 de Traspuesta
 * a seis edades (joven, disectado, colapso de flanco, caldera vieja, cuello), y la garganta pasa de uno a otro durante la canción.
 * Cuando el flanco colapsa, la caldera abierta se vuelve un RESONADOR DE HELMHOLTZ enorme: una cavidad con una boca (la brecha).
 * f_H = c/2π · √(A / (V·L)): con el volumen de la caldera y el ancho de la brecha cae en 20–40 Hz. El resonador lo excitan la
 * garganta misma y el magma (ruido grave que sube con `brama`): la tierra brama (Challenger, en «La geología de la moral»).
 *
 *   GargantaVolcan.render({dur, perfiles: [[t, Float32Array]…], largo, eventos (los de garganta.js), caldera: [[t, 0–1]…],
 *                          brama: [[t, 0–1]…], fH (Hz), semilla}, sr, Garganta) → {voz, caldera} (Float32Array, cada uno normalizado a su
 *                          pico: el bramido de la caldera es 70 dB más fuerte que la voz y se nivelan en la mezcla)
 */
(function (global) {
  'use strict';
  function curva(v) { return function (t) { if (!v || !v.length) return 0; if (t <= v[0][0]) return v[0][1]; for (var i = 1; i < v.length; i++) if (t <= v[i][0]) { var u = (t - v[i - 1][0]) / (v[i][0] - v[i - 1][0]); return v[i - 1][1] + (v[i][1] - v[i - 1][1]) * u; } return v[v.length - 1][1]; }; }
  function rngDe(s) { var h = s >>> 0 || 1; return function () { h ^= h << 13; h >>>= 0; h ^= h >> 17; h ^= h << 5; h >>>= 0; return h / 4294967296 * 2 - 1; }; }
  function render(c, sr, Garganta) {
    sr = sr || 48000;
    var y = Garganta.render({ dur: c.dur, perfiles: c.perfiles, largo: c.largo || 2, eventos: c.eventos, semilla: c.semilla }, sr);
    var cal = curva(c.caldera), bra = curva(c.brama), r = rngDe((c.semilla || 7) + 99), fH = c.fH || 28;
    // el resonador de Helmholtz: dos polos a fH, Q 9 (una cavidad grande con una boca ancha), excitado por la garganta y el magma
    var w = 2 * Math.PI * fH / sr, R = Math.exp(-Math.PI * fH / 9 / sr), a1 = 2 * R * Math.cos(w), a2 = -R * R, y1 = 0, y2 = 0, lp = 0, out = new Float32Array(y.length), pk = 0, pv = 0;
    for (var i = 0; i < y.length; i++) {
      var t = i / sr, k = cal(t), b = bra(t);
      lp += .002 * (r() - lp);                                               // el magma: ruido muy grave
      var x = (y[i] * .6 + lp * 40 * b) * k, z = a1 * y1 + a2 * y2 + (1 - R) * x; y2 = y1; y1 = z;
      out[i] = z * 6 * k; if (Math.abs(out[i]) > pk) pk = Math.abs(out[i]); if (Math.abs(y[i]) > pv) pv = Math.abs(y[i]);
    }
    if (pk > 0) for (var j = 0; j < out.length; j++) out[j] /= pk;
    return { voz: y, caldera: out };
  }
  var api = { render: render };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.GargantaVolcan = api;
})(typeof window !== 'undefined' ? window : globalThis);
