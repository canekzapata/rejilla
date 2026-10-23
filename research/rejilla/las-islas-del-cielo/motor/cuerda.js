/* cuerda.js — copia de la de «La duna que canta» (guembri, guitarra) con dos cuerpos nuevos para «Las islas del cielo»:
 *   arpa:   el arpa llanera: cuerda de nailon brillante, T60 3.2 s, cada cuerda sigue sonando (una cuerda por nota: c = la nota), tapa
 *           de madera (resonancias en 190 y 430 Hz), sin amplificador.
 *   cuatro: el cuatro venezolano: cuatro cuerdas cortas (T60 0.9 s) que se rasguean y se apagan con la palma (apagado 50 ms), caja chica
 *           (300 y 680 Hz).
 * Original:
 *
 * Karplus-Strong extendido: una línea de retardo de largo fraccionario (sr/f, interpolación de Lagrange de 3er orden) con una
 * pérdida de un cero (el brillo) y una ganancia por periodo que da el T60. Cada cuerda es independiente (`c`: 0, 1, 2…) y sigue
 * sonando entre notas: una nota con `liga` no pulsa, sólo cambia el largo (hammer-on, pull-off: la mano izquierda del tishoumaren),
 * y `desliz` (s) desliza la altura (el glisando de la cresta). Al soltar una nota sin liga, la cuerda se apaga (T60 corto).
 *   guembri: cuerda de tripa grave, pulso oscuro, T60 1.1 s; el pulgar golpea el cuero (un golpe sordo a 95 Hz) y la sersera, la
 *            lámina de hierro con argollas atada a la cabeza, chisporrotea con la cuerda (ruido agudo que sigue su envolvente, a
 *            golpes: las argollas rebotan a ~40 Hz). La caja de cuero resuena en 110 y 240 Hz.
 *   guitarra: eléctrica limpia que se ensucia: púa brillante, T60 2.6 s, un amplificador pequeño (tanh), un gabinete (pasabajas
 *            4.2 kHz) y un eco corto de cinta (slapback, 110 ms).
 *
 *   Cuerda.render({dur, tipo: 'guembri'|'guitarra'|'arpa'|'cuatro', notas: [{t, dur, m, v, c, liga, desliz}], semilla}, sr) → Float32Array
 */
(function (global) {
  'use strict';
  var hz = function (m) { return 440 * Math.pow(2, (m - 69) / 12); };
  function rngDe(s) { var h = s >>> 0 || 1; return function () { h ^= h << 13; h >>>= 0; h ^= h >> 17; h ^= h << 5; h >>>= 0; return h / 4294967296 * 2 - 1; }; }
  function bq(tipo, f, q, sr) {
    var w = 2 * Math.PI * f / sr, a = Math.sin(w) / (2 * q), c = Math.cos(w), b0, b1, b2;
    if (tipo === 'bp') { b0 = a; b1 = 0; b2 = -a; } else if (tipo === 'lp') { b0 = (1 - c) / 2; b1 = 1 - c; b2 = b0; } else { b0 = (1 + c) / 2; b1 = -(1 + c); b2 = b0; }
    var a0 = 1 + a; return { b0: b0 / a0, b1: b1 / a0, b2: b2 / a0, a1: -2 * c / a0, a2: (1 - a) / a0, x1: 0, x2: 0, y1: 0, y2: 0 };
  }
  function paso(F, x) { var y = F.b0 * x + F.b1 * F.x1 + F.b2 * F.x2 - F.a1 * F.y1 - F.a2 * F.y2; F.x2 = F.x1; F.x1 = x; F.y2 = F.y1; F.y1 = y; return y; }
  var TIPO = {
    guembri: { t60: 1.1, apaga: .07, brillo: .35, pulso: 600 },
    guitarra: { t60: 2.6, apaga: .09, brillo: .7, pulso: 3500 },
    arpa: { t60: 3.2, apaga: .6, brillo: .82, pulso: 5000 },
    cuatro: { t60: .9, apaga: .05, brillo: .6, pulso: 3000 }
  };

  function render(c, sr) {
    sr = sr || 48000;
    var T = TIPO[c.tipo], N = Math.ceil(c.dur * sr), r = rngDe((c.semilla || 1) * 13 + 5), out = new Float32Array(N);
    var porC = {};
    c.notas.slice().sort(function (a, b) { return a.t - b.t; }).forEach(function (n) { (porC[n.c || 0] = porC[n.c || 0] || []).push(n); });
    var MAX = Math.ceil(sr / 25) + 8;
    Object.keys(porC).forEach(function (k) {
      var ns = porC[k], buf = new Float64Array(MAX), w = 0, prev = 0, f = hz(ns[0].m), fMeta = f, dfs = 0, exc = null, ei = 0, vivo = 0, sueltaEn = -1;
      var pulsoF = bq('lp', T.pulso, .7, sr);
      for (var i = 0; i < N; i++) {
        var t = i / sr;
        while (ei < ns.length && ns[ei].t <= t) {               // empieza una nota
          var n = ns[ei++]; fMeta = hz(n.m);
          if (n.liga || n.desliz) dfs = n.desliz ? (fMeta - f) / (n.desliz * sr) : 0;
          if (!n.liga && !n.desliz) f = fMeta;
          if (!n.liga) {                                          // pulsar: un pulso de ruido (o triángulo) del largo de la cuerda
            var L = Math.max(4, Math.round(sr / fMeta)); exc = new Float64Array(L); var v = n.v == null ? .8 : n.v, pos = .13 + .1 * Math.abs(r());
            for (var j = 0; j < L; j++) { var tri = j / L < pos ? j / (L * pos) : (L - j) / (L * (1 - pos)); exc[j] = v * (.55 * tri + .45 * paso(pulsoF, r())); }
            exc.i = 0;
          }
          vivo = 1; sueltaEn = n.t + n.dur;
          if (ei < ns.length && ns[ei].t - sueltaEn < .03) sueltaEn = -1;   // la siguiente entra encima: no se suelta
        }
        if (dfs) { f += dfs; if ((dfs > 0 && f >= fMeta) || (dfs < 0 && f <= fMeta)) { f = fMeta; dfs = 0; } } else f += (fMeta - f) * .002;
        var t60 = (sueltaEn > 0 && t > sueltaEn) ? T.apaga : T.t60;
        var D = sr / f - 1 - (1 - T.brillo) * .5, d = Math.floor(D), fr = D - d;   // el lazo: la línea, la escritura (1) y el promedio ((1 − brillo)/2)
        // Lagrange de 3er orden sobre la línea
        var i0 = (w - d + MAX) % MAX, im1 = (i0 + 1) % MAX, i1 = (i0 - 1 + MAX) % MAX, i2 = (i0 - 2 + MAX) % MAX;
        var x0 = buf[im1], x1 = buf[i0], x2 = buf[i1], x3 = buf[i2], u = fr;
        var y = x0 * (-(u) * (u - 1) * (u - 2) / 6) + x1 * ((u + 1) * (u - 1) * (u - 2) / 2) + x2 * (-(u + 1) * u * (u - 2) / 2) + x3 * ((u + 1) * u * (u - 1) / 6);
        var g = Math.pow(10, -3 / (t60 * f)), b = T.brillo, nuevo = g * (b * y + (1 - b) * .5 * (y + prev)); prev = y;
        if (exc && exc.i < exc.length) nuevo += exc[exc.i++];
        w = (w + 1) % MAX; buf[w] = nuevo; out[i] += y;
      }
    });
    // el cuerpo
    var sal = new Float32Array(N), sem = rngDe((c.semilla || 1) * 7 + 1);
    if (c.tipo === 'guembri') {
      var cuero1 = bq('bp', 110, 3, sr), cuero2 = bq('bp', 240, 4, sr), lp = bq('lp', 2600, .7, sr), sers = bq('bp', 4800, 1.5, sr), envS = 0, golpeF = bq('bp', 95, 4, sr);
      var golpes = new Float32Array(N); c.notas.forEach(function (n) { if (n.liga) return; var i0 = Math.round(n.t * sr); for (var j = 0; j < 2400 && i0 + j < N; j++) golpes[i0 + j] += (n.v == null ? .8 : n.v) * Math.exp(-j / 300) * sem(); });
      for (var i = 0; i < N; i++) {
        var x = out[i]; envS += (Math.abs(x) - envS) * .002;
        var argollas = .5 + .5 * Math.sin(2 * Math.PI * 40 * i / sr + 3 * Math.sin(2 * Math.PI * 7 * i / sr));   // rebotan
        var z = paso(lp, x) + .9 * paso(cuero1, x) + .5 * paso(cuero2, x) + 2.2 * paso(golpeF, golpes[i]) + 1.4 * paso(sers, sem()) * envS * argollas;
        sal[i] = Math.tanh(1.5 * z);
      }
    } else if (c.tipo === 'arpa' || c.tipo === 'cuatro') {                  // madera: la tapa del arpa o la caja del cuatro, sin amplificador
      var A = c.tipo === 'arpa', m1 = bq('bp', A ? 190 : 300, 2.5, sr), m2 = bq('bp', A ? 430 : 680, 3, sr), hp2 = bq('hp', A ? 60 : 110, .7, sr), lp2 = bq('lp', A ? 7000 : 5200, .7, sr);
      for (var i4 = 0; i4 < N; i4++) { var x4 = paso(hp2, out[i4]); sal[i4] = paso(lp2, x4 + .6 * paso(m1, x4) + .35 * paso(m2, x4)); }
    } else {
      var hp = bq('hp', 90, .7, sr), gab = bq('lp', 4200, .8, sr), gab2 = bq('lp', 5200, .7, sr), dly = Math.round(.11 * sr);
      for (var i2 = 0; i2 < N; i2++) { var a = Math.tanh(2.4 * paso(hp, out[i2])) / Math.tanh(2.4); sal[i2] = paso(gab2, paso(gab, a)); }
      for (var i3 = N - 1; i3 >= dly; i3--) sal[i3] += .28 * sal[i3 - dly];
    }
    var pk = 0; for (var q = 0; q < N; q++) pk = Math.max(pk, Math.abs(sal[q])); if (pk > 0) for (q = 0; q < N; q++) sal[q] /= pk;
    return sal;
  }
  var api = { render: render };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.Cuerda = api;
})(typeof window !== 'undefined' ? window : globalThis);
