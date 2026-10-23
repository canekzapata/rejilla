/* carcava.js — la guitarra de cárcava (Lo que el agua dibuja, 21 oct 2026): una guitarra de slide cuya altura NO son notas sino
 * una curva continua (la partitura le da la altitud del cauce, ya convertida a semitonos, cada 5 ms).
 *
 * La cuerda: Karplus-Strong extendido como cuerda.js (línea de retardo de largo fraccionario sr/f con Lagrange de 3er orden,
 * pérdida de un cero, ganancia por periodo según el T60), pero el largo cambia en CADA muestra siguiendo la curva: el cuello de
 * botella no tiene trastes. Una pulsación sólo excita la cuerda (púa: triángulo + ruido); la altura la pone el vidrio.
 *
 * El chirrido del vidrio sobre el entorchado: con el slide a x metros del puente la cuerda suena a f = f_abierta · Le/(Le − x),
 * así que x = Le (1 − f_abierta/f) y la velocidad del vidrio es dx/dt = Le f_abierta f'/f². Las espiras del entorchado están cada
 * 0.4 mm: el vidrio las cruza a |dx/dt| / 0.0004 por segundo y eso suena como un tono de ruido en esa frecuencia (el «zing» de
 * cualquier slide), más fuerte mientras más rápido corre y mientras más vibra la cuerda.
 * El amplificador: tanh (un combo pequeño empujado), gabinete (pasabajas 4 kHz), y un slapback de cinta de 120 ms.
 *
 *   Carcava.render({dur, fr, semilla, cuerdas: [{curva: [midi…] a fr Hz, pulsos: [[t, v]…], t60, brillo, abierta, entorchada, pan,
 *                   apagar: [t…] (la palma)}]}, sr) → {L, R, zing}   (Float32Array)
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
  function rebq(F, tipo, f, q, sr) { var G = bq(tipo, f, q, sr); F.b0 = G.b0; F.b1 = G.b1; F.b2 = G.b2; F.a1 = G.a1; F.a2 = G.a2; }
  function paso(F, x) { var y = F.b0 * x + F.b1 * F.x1 + F.b2 * F.x2 - F.a1 * F.y1 - F.a2 * F.y2; F.x2 = F.x1; F.x1 = x; F.y2 = F.y1; F.y1 = y; return y; }
  var LE = 0.648, ESPIRA = 0.0004;

  function render(c, sr) {
    sr = sr || 48000;
    var N = Math.ceil(c.dur * sr), L = new Float32Array(N), R = new Float32Array(N), ZING = new Float32Array(N), MAX = 4096;
    c.cuerdas.forEach(function (cu, ci) {
      var r = rngDe((c.semilla || 1) * 31 + ci * 7 + 3), cur = cu.curva, fr = c.fr, buf = new Float64Array(MAX), w = 0, prev = 0;
      var pul = cu.pulsos.slice().sort(function (a, b) { return a[0] - b[0]; }), pi = 0, apag = (cu.apagar || []).slice().sort(function (a, b) { return a - b; }), ai = 0, apagaHasta = -1;
      var exc = null, ei = 0, pulsoF = bq('lp', 3800, .7, sr), zf = bq('bp', 1500, 7, sr), env = 0, b = cu.brillo, fab = hz(cu.abierta), out = new Float64Array(N);
      var mAnt = cur[0], zingG = 0;
      for (var i = 0; i < N; i++) {
        var t = i / sr, k = t * fr, k0 = Math.min(cur.length - 2, Math.floor(k)), u0 = k - k0, m = cur[k0] + (cur[k0 + 1] - cur[k0]) * u0;
        var f = hz(m);
        while (pi < pul.length && pul[pi][0] <= t) {                     // la púa
          var v = pul[pi++][1], Lx = Math.max(4, Math.round(sr / f)), pos = .12 + .08 * Math.abs(r()); exc = new Float64Array(Lx);
          for (var j = 0; j < Lx; j++) { var tri = j / Lx < pos ? j / (Lx * pos) : (Lx - j) / (Lx * (1 - pos)); exc[j] = v * (.6 * tri + .4 * paso(pulsoF, r())); }
          ei = 0; apagaHasta = -1;
        }
        while (ai < apag.length && apag[ai] <= t) { apagaHasta = apag[ai++] + .12; }
        var t60 = apagaHasta > t ? .08 : cu.t60;
        var D = sr / f - 1 - (1 - b) * .5, d = Math.floor(D), q = D - d;
        var i0 = (w - d + MAX) % MAX, im1 = (i0 + 1) % MAX, i1 = (i0 - 1 + MAX) % MAX, i2 = (i0 - 2 + MAX) % MAX;
        var x0 = buf[im1], x1 = buf[i0], x2 = buf[i1], x3 = buf[i2];
        var y = x0 * (-(q) * (q - 1) * (q - 2) / 6) + x1 * ((q + 1) * (q - 1) * (q - 2) / 2) + x2 * (-(q + 1) * q * (q - 2) / 2) + x3 * ((q + 1) * q * (q - 1) / 6);
        var g = Math.pow(10, -3 / (t60 * f)), nuevo = g * (b * y + (1 - b) * .5 * (y + prev)); prev = y;
        if (exc && ei < exc.length) nuevo += exc[ei++];
        w = (w + 1) % MAX; buf[w] = nuevo;
        env += (Math.abs(y) - env) * .001;
        // el zing: la velocidad del vidrio sobre las espiras
        var z = 0;
        if (cu.entorchada) {
          var dm = (m - mAnt) * sr; mAnt = m;                            // semitonos por segundo
          var fp = f * Math.LN2 / 12 * dm, vx = Math.abs(LE * fab * fp / (f * f)), fz = vx / ESPIRA;
          if ((i & 15) === 0) rebq(zf, 'bp', Math.min(7000, Math.max(150, fz)), 6, sr);
          zingG += (Math.min(1, vx / .35) - zingG) * .004;
          z = paso(zf, r()) * zingG * env * 2.2;
        }
        out[i] = y + z; ZING[i] += z;
      }
      // el amplificador
      var hp = bq('hp', 85, .7, sr), gab = bq('lp', 4000, .8, sr), gab2 = bq('lp', 5600, .7, sr), dr = cu.empuje || 2.6, dly = Math.round(.12 * sr);
      var s = new Float64Array(N);
      for (var i3 = 0; i3 < N; i3++) { var a = Math.tanh(dr * paso(hp, out[i3])) / Math.tanh(dr); s[i3] = paso(gab2, paso(gab, a)); }
      for (var i4 = N - 1; i4 >= dly; i4--) s[i4] += .22 * s[i4 - dly];
      var an = (cu.pan + 1) * Math.PI / 4, cl = Math.cos(an), cr = Math.sin(an);
      for (var i5 = 0; i5 < N; i5++) { L[i5] += s[i5] * cl; R[i5] += s[i5] * cr; }
    });
    return { L: L, R: R, zing: ZING };
  }
  var api = { render: render };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.Carcava = api;
})(typeof window !== 'undefined' ? window : globalThis);
