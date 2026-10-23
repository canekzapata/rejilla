/* modos.js — el motor aditivo de los objetos que vibran por modos (waterphone, gong, tambor parlante).
 *
 * Un objeto golpeado o frotado vibra en sus modos: senos a frecuencias propias, cada uno con su envolvente. Aquí cada
 * modo es una voz {t0, fin, f(u), a(u)} (u = segundos desde t0) que se integra por fase, así la frecuencia puede
 * moverse (el agua dobla las varillas, el gong sube con la amplitud, la cuerda del tambor tensa el parche) sin saltos.
 *
 *   Modos.sumar(y, sr, voz)   suma una voz al búfer y
 *   Modos.T60(t)              amortiguamiento (1/s) para que caiga 60 dB en t segundos
 */
(function (global) {
  'use strict';
  function sumar(y, sr, v) {
    var i0 = Math.max(0, Math.floor(v.t0 * sr)), i1 = Math.min(y.length, Math.ceil(v.fin * sr)), fase = v.fase || 0, dos = 2 * Math.PI / sr;
    for (var i = i0; i < i1; i++) {
      var u = i / sr - v.t0; if (u < 0) continue;
      var f = v.f(u); if (f < sr * .45) y[i] += v.a(u) * Math.sin(fase);
      fase += dos * f;
    }
  }
  var api = {
    sumar: sumar, T60: function (t) { return 6.9078 / t; }, hz: function (m) { return 440 * Math.pow(2, (m - 69) / 12); },
    rngDe: function (s) { var h = s >>> 0 || 1; return function () { h ^= h << 13; h >>>= 0; h ^= h >> 17; h ^= h << 5; h >>>= 0; return h / 4294967296; }; }
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.Modos = api;
})(typeof window !== 'undefined' ? window : globalThis);
