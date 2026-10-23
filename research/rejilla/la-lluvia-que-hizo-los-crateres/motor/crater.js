/* crater.js — la membrana de cráter: un instrumento imposible para «La lluvia que hizo los cráteres».
 *
 * Cada cráter del campo de impactos es un tambor: una membrana circular de su diámetro. Una membrana ideal suena en los modos de
 * Bessel, f_mn = (j_mn / j_01) · f_01 (1, 1.594, 2.136, 2.296, 2.653, 2.918, 3.156, 3.501…), y la fundamental es inversa al
 * diámetro: f_01 = K / D (con K = 81 000 m·Hz, el cráter de 1.8 km da 45 Hz y el de 225 m, 360 Hz).
 *  - FORMA: el tazón simple es la membrana tal cual (taiko). El cráter complejo tiene fondo plano, terrazas y un PICO CENTRAL:
 *    la masa en el centro sube los modos simétricos (m = 0) y la cola dura más; las terrazas suman parciales inarmónicos.
 *  - EDAD: el motor de Traspuesta suaviza el terreno entre impacto e impacto; los viejos quedan romos. Aquí: el viejo pierde los
 *    modos altos y el clic del labio; el joven es filoso.
 *  - EL GOLPE: dónde cae (r: 0 centro … 1 borde) decide qué modos despierta, por la forma del modo, |J_m(j_mn · r)|; la fuerza
 *    sube un poco la altura al principio (la membrana se estira: la caída de tono del taiko) y abre el brillo.
 *  - LA ONDA DE CHOQUE (golpe con choque > 0): un barrido grave que llega antes que el golpe, en los cráteres grandes.
 * Síntesis modal con osciladores recursivos (rotación) que se cortan a −70 dB.
 *
 *   Crater.render({dur, tambores: {id: {D, complejo, edad}}, golpes: [{t, id, v, r, pan, choque}], K}, sr) → {L, R}
 */
(function (global) {
  'use strict';
  function rngDe(s) { var h = s >>> 0 || 1; return function () { h ^= h << 13; h >>>= 0; h ^= h >> 17; h ^= h << 5; h >>>= 0; return h / 4294967296 * 2 - 1; }; }
  // ceros de Bessel j_mn: [m, j]
  var MODOS = [[0, 2.4048], [1, 3.8317], [2, 5.1356], [0, 5.5201], [3, 6.3802], [1, 7.0156], [4, 7.5883], [2, 8.4172], [0, 8.6537], [5, 8.7715], [3, 9.7610], [6, 9.9361]];
  function besselJ(m, x) { var s = 0, N = 48; for (var i = 0; i < N; i++) { var tt = Math.PI * (i + .5) / N; s += Math.cos(m * tt - x * Math.sin(tt)); } return s / N; }

  function render(c, sr) {
    sr = sr || 48000;
    var N = Math.ceil(c.dur * sr), K = c.K || 81000, L = new Float32Array(N), R = new Float32Array(N), r = rngDe(c.semilla || 18);
    c.golpes.forEach(function (g, gi) {
      var tb = c.tambores[g.id]; if (!tb) return;
      var f01 = K / tb.D, v = g.v == null ? .8 : g.v, r0 = g.r == null ? .3 : g.r, edad = tb.edad || 0, cx = !!tb.complejo;
      var Tb = .5 + 3.2 * Math.pow(45 / f01, .8) * (cx ? 1.6 : 1);                 // los grandes suenan más
      var i0 = Math.round(g.t * sr), pan = g.pan || 0, gl = Math.cos((pan + 1) * Math.PI / 4), gr = Math.sin((pan + 1) * Math.PI / 4);
      var modos = MODOS.map(function (mo) {
        var rat = mo[1] / 2.4048; if (cx && mo[0] === 0 && rat > 1) rat *= 1.12;        // el pico central carga el centro
        var forma = Math.abs(besselJ(mo[0], mo[1] * Math.min(.95, r0 + .05)));
        var brillo = Math.exp(-(rat - 1) * (.35 + 1.2 * edad) / (.4 + v));              // el viejo y el golpe suave: menos modos altos
        return { f: f01 * rat, a: forma * brillo / Math.pow(rat, .4), T: Tb / Math.pow(rat, .75) };
      });
      if (cx) for (var q = 0; q < 3; q++) modos.push({ f: f01 * (1.31 + .87 * q + .1 * r()), a: .25, T: Tb * .4 });   // las terrazas
      var dur = Math.min(N - i0, Math.ceil(Math.max.apply(null, modos.map(function (m) { return m.T; })) * 1.1 * sr));
      if (dur <= 0) return;
      var buf = new Float32Array(dur);
      modos.forEach(function (m) {
        if (m.f > sr * .45 || m.a < 1e-3) return;
        var dec = Math.exp(-6.9 / (m.T * sr)), a = m.a * v, ph = r() * Math.PI, w0 = 2 * Math.PI * m.f / sr;
        var s = Math.sin(ph), co = Math.cos(ph);
        var nG = Math.round(.15 * sr), cw = Math.cos(w0), sw = Math.sin(w0);
        for (var n = 0; n < dur; n++) {
          if (n < nG) { var w = w0 * (1 + .06 * v * Math.exp(-n / (.03 * sr))); cw = Math.cos(w); sw = Math.sin(w); }   // la caída de tono del golpe (150 ms)
          else if (n === nG) { cw = Math.cos(w0); sw = Math.sin(w0); }
          var s2 = s * cw + co * sw; co = co * cw - s * sw; s = s2;
          buf[n] += a * s; a *= dec; if (a < 3e-4 * v) break;
        }
      });
      // el labio: un clic agudo (filoso si es joven)
      var clic = (1 - edad) * .5 * v, lp = 0;
      for (var n2 = 0; n2 < Math.min(dur, 400); n2++) { lp += (r() - lp) * .6; buf[n2] += clic * (r() - lp) * Math.exp(-n2 / 40); }
      // la onda de choque: un barrido grave antes del golpe
      if (g.choque) {
        var pre = Math.round(.35 * sr), j0 = Math.max(0, i0 - pre), ph2 = 0;
        for (var j = j0; j < i0 + Math.round(.2 * sr) && j < N; j++) {
          var u = (j - j0) / (i0 + .2 * sr - j0), f = 55 - 30 * u; ph2 += 2 * Math.PI * f / sr;
          var e = g.choque * Math.sin(Math.PI * u) * .6; L[j] += Math.sin(ph2) * e * gl; R[j] += Math.sin(ph2) * e * gr;
        }
      }
      for (var k = 0; k < dur; k++) { L[i0 + k] += buf[k] * gl; R[i0 + k] += buf[k] * gr; }
    });
    var pk = 0; for (var i = 0; i < N; i++) pk = Math.max(pk, Math.abs(L[i]), Math.abs(R[i])); if (pk > 0) for (i = 0; i < N; i++) { L[i] /= pk; R[i] /= pk; }
    return { L: L, R: R };
  }
  var api = { render: render, MODOS: MODOS, besselJ: besselJ };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.Crater = api;
})(typeof window !== 'undefined' ? window : globalThis);
