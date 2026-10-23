/* traductor.js — el traductor que se oxida: un instrumento imposible para «El androide en la estación».
 *
 * El chip de voz de los ochenta (LPC-10: el Speak & Spell, Kraftwerk) habla con una CELOSÍA: una cadena de coeficientes de
 * reflexión k₁…k_N que filtra un tren de pulsos (vocales) o ruido (consonantes). Esa celosía es, ecuación por ecuación, el tubo de
 * Kelly-Lochbaum de nuestra garganta de montaña: N secciones de un tubo acústico, con kᵢ = (Aᵢ − Aᵢ₊₁)/(Aᵢ + Aᵢ₊₁). El silicio y la
 * carne hablan con la misma fórmula; el androide deserta sin cambiar de ecuación: sólo cambian los números.
 *
 * Análisis: la voz guía (Sabina cantando la línea) se baja a 16 kHz y se analiza por LPC (autocorrelación + Levinson, orden 16,
 * ventana de 30 ms cada 10 ms): coeficientes de reflexión, ganancia y sonoridad (cruces por cero + energía grave) por cuadro.
 * Síntesis: la celosía toca con la ALTURA DE LA PARTITURA (la voz va abajo) y se desarma con `oxido` (0–1):
 *   0     LPC-10: los k cuantizados a 5 bits como razones de área logarítmicas, cuadros retenidos 22.5 ms, salida retenida a 8 kHz
 *         (el chip), tren de pulsos duro;
 *   ↑     la cuantización se vuelve ÓXIDO (ruido que salta en las uniones); los cuadros se arrastran (la interpolación pasa de 10 a
 *         150 ms: musgo); las uniones pierden (la onda que vuelve se moja); el pulso se vuelve aliento (pulso suave + ruido);
 *   >.75  el tubo toma la forma del PERFIL (un corte del archipiélago): estoy tierra.
 *
 *   Traductor.render({dur, guia: Float32Array (48 kHz), eventos: [{t, dur, nota}], oxido: [[t, 0–1]…], perfil: Float32Array,
 *                     semilla}, sr) → {y: Float32Array (48 kHz), k: [[t, k₁…k_N]…] (cada 50 ms, para el proceso)}
 */
(function (global) {
  'use strict';
  var hz = function (m) { return 440 * Math.pow(2, (m - 69) / 12); };
  function rngDe(s) { var h = s >>> 0 || 1; return function () { h ^= h << 13; h >>>= 0; h ^= h >> 17; h ^= h << 5; h >>>= 0; return h / 4294967296 * 2 - 1; }; }
  function curva(v, def) { return function (t) { if (!v || !v.length) return def; if (t <= v[0][0]) return v[0][1]; for (var i = 1; i < v.length; i++) if (t <= v[i][0]) { var u = (t - v[i - 1][0]) / (v[i][0] - v[i - 1][0]); return v[i - 1][1] + (v[i][1] - v[i - 1][1]) * u; } return v[v.length - 1][1]; }; }
  function bq(tipo, f, q, sr) {
    var w = 2 * Math.PI * f / sr, a = Math.sin(w) / (2 * q), c = Math.cos(w), b0, b1, b2;
    if (tipo === 'lp') { b0 = (1 - c) / 2; b1 = 1 - c; b2 = b0; } else if (tipo === 'hp') { b0 = (1 + c) / 2; b1 = -(1 + c); b2 = b0; } else { b0 = a; b1 = 0; b2 = -a; }
    var a0 = 1 + a; return { b0: b0 / a0, b1: b1 / a0, b2: b2 / a0, a1: -2 * c / a0, a2: (1 - a) / a0, x1: 0, x2: 0, y1: 0, y2: 0 };
  }
  function paso(F, x) { var y = F.b0 * x + F.b1 * F.x1 + F.b2 * F.x2 - F.a1 * F.y1 - F.a2 * F.y2; F.x2 = F.x1; F.x1 = x; F.y2 = F.y1; F.y1 = y; return y; }

  var SRI = 16000, ORDEN = 16;
  // Levinson-Durbin: autocorrelación r[0..p] → coeficientes de reflexión k[1..p] y error final
  function levinson(r, p) {
    var a = new Float64Array(p + 1), tmp = new Float64Array(p + 1), k = new Float64Array(p + 1), E = r[0] * 1.0001 + 1e-12; a[0] = 1;
    for (var i = 1; i <= p; i++) {
      var acc = r[i]; for (var j = 1; j < i; j++) acc += a[j] * r[i - j];
      var ki = -acc / E; k[i] = ki; for (j = 0; j <= i; j++) tmp[j] = a[j];
      for (j = 1; j < i; j++) a[j] = tmp[j] + ki * tmp[i - j]; a[i] = ki; E *= (1 - ki * ki);
    }
    return { k: k, E: E };
  }
  function analizar(x16) {
    var W = Math.round(.03 * SRI), H = Math.round(.01 * SRI), nF = Math.floor((x16.length - W) / H) + 1, win = new Float64Array(W), cuadros = [];
    for (var i = 0; i < W; i++) win[i] = .54 - .46 * Math.cos(2 * Math.PI * i / (W - 1));
    var seg = new Float64Array(W);
    for (var f = 0; f < nF; f++) {
      var o = f * H, en = 0, zc = 0, prev = 0;
      for (i = 0; i < W; i++) { var v = x16[o + i] - (i ? .94 * x16[o + i - 1] : 0); seg[i] = v * win[i]; en += x16[o + i] * x16[o + i]; if (i && (x16[o + i] >= 0) !== (prev >= 0)) zc++; prev = x16[o + i]; }
      var r = new Float64Array(ORDEN + 1);
      for (var l = 0; l <= ORDEN; l++) { var s = 0; for (i = l; i < W; i++) s += seg[i] * seg[i - l]; r[l] = s * (l ? Math.exp(-.5 * Math.pow(2 * Math.PI * 40 * l / SRI, 2)) : 1); }   // ensanchar ancho de banda (40 Hz): sin picos que silban
      var L = levinson(r, ORDEN), rms = Math.sqrt(en / W);
      cuadros.push({ k: Array.prototype.slice.call(L.k, 1), g: Math.sqrt(Math.max(L.E, 0) / W), rms: rms, sordo: zc / W > .22 });
    }
    return { cuadros: cuadros, hop: H / SRI };
  }
  // 5 bits sobre la razón de área logarítmica (como LPC-10 en los primeros coeficientes)
  function cuantiza(k, bits) { var lar = Math.log((1 + k) / (1 - k)), q = Math.pow(2, bits - 1) / 4; lar = Math.round(lar * q) / q; var e = Math.exp(lar); return (e - 1) / (e + 1); }

  function render(c, sr) {
    sr = sr || 48000;
    var D = c.dur, N16 = Math.ceil(D * SRI), r = rngDe((c.semilla || 2038) * 31 + 7), ox = curva(c.oxido, 0);
    // la guía a 16 kHz (promedio de 3 con un pasabajas antes)
    var lp = bq('lp', 6500, .7, sr), g16 = new Float64Array(N16), gu = c.guia;
    for (var i = 0, j = 0; i < gu.length && j < N16; i++) { var z = paso(lp, gu[i]); if (i % 3 === 2) g16[j++] = z; }
    var A = analizar(g16), CU = A.cuadros, nC = CU.length;
    // el tubo de tierra: áreas del perfil → coeficientes
    var kT = new Float64Array(ORDEN);
    if (c.perfil) { var P = c.perfil, area = function (q) { var x = q * (P.length - 1), a = Math.floor(x), b = Math.min(P.length - 1, a + 1); return .15 + 3 * (P[a] + (P[b] - P[a]) * (x - a)); };
      for (var s2 = 0; s2 < ORDEN; s2++) { var A1 = area(s2 / ORDEN), A2 = area((s2 + 1) / ORDEN); kT[s2] = (A1 - A2) / (A1 + A2) * .97; } }
    var ev = c.eventos.slice().sort(function (a, b) { return a.t - b.t; }), ei = 0;
    var kAct = new Float64Array(ORDEN), kRuido = new Float64Array(ORDEN), fwd = new Float64Array(ORDEN + 1), bck = new Float64Array(ORDEN + 1);
    var out16 = new Float64Array(N16), fase = 0, gAct = 0, sordoAct = 0, hold = 0, holdK = -1, kRegistro = [], suave = bq('lp', 900, .7, SRI), aliento = bq('bp', 1800, .6, SRI);
    for (var n = 0; n < N16; n++) {
      var t = n / SRI, o = ox(t);
      while (ei < ev.length - 1 && ev[ei + 1].t <= t) ei++;
      var e = ev[ei], vivo = e && t >= e.t - .01 && t < e.t + e.dur + .04;
      // el cuadro: con óxido 0 se retiene 22.5 ms (LPC-10); luego se interpola cada vez más lento (musgo)
      var fc = Math.min(nC - 1, Math.floor(t / A.hop)), cu = CU[fc];
      if (o < .25) { var fr = Math.floor(t / .0225); if (fr !== holdK) { holdK = fr; for (var q = 0; q < ORDEN; q++) kAct[q] = cuantiza(Math.max(-.995, Math.min(.995, cu.k[q])), q < 4 ? 5 : 4); gAct = cu.g; sordoAct = cu.sordo ? 1 : 0; } }
      else {
        var tau = .01 + .14 * Math.min(1, (o - .25) / .6), a = 1 - Math.exp(-1 / (tau * SRI));
        for (q = 0; q < ORDEN; q++) {
          if ((n & 31) === 0) kRuido[q] = r() * .25 * Math.max(0, Math.min(1, (o - .2) / .4)) * (1 - Math.max(0, (o - .8) / .2));   // el óxido salta en las uniones
          var w = Math.max(0, Math.min(1, (o - .75) / .25)) * .75, meta = (1 - w) * cu.k[q] + w * kT[q] + kRuido[q];
          kAct[q] += (Math.max(-.97, Math.min(.97, meta)) - kAct[q]) * a;
        }
        gAct += (cu.g - gAct) * a; sordoAct += ((cu.sordo ? 1 : 0) - sordoAct) * a;
      }
      // la fuente: pulsos con la altura de la partitura (abajo) o ruido; con el óxido el pulso se suaviza y entra aliento
      var f0 = e ? hz(e.nota) : 60, exc = 0;
      fase += f0 / SRI; var pulso = 0; if (fase >= 1) { fase -= 1; pulso = Math.sqrt(SRI / f0); }
      var blando = paso(suave, pulso) * 2.2, ruido = r() * .9;
      var voz = (1 - o) * pulso + o * (blando * .8 + paso(aliento, ruido) * .35 * o);
      exc = (sordoAct > .5 ? ruido * (1 - .5 * o) : voz) * gAct * (vivo ? 1 : 0);
      // la celosía (todo polos): f_{i-1} = f_i − k_i·b_{i-1}[n−1];  b_i = k_i·f_{i-1} + b_{i-1}[n−1]; las uniones se mojan (pérdida)
      var moja = 1 - .12 * Math.max(0, (o - .3) / .7), fN = exc;
      for (q = ORDEN; q >= 1; q--) { fN = fN - kAct[q - 1] * bck[q - 1]; fwd[q - 1] = fN; }
      var y = fN; for (q = ORDEN; q >= 1; q--) bck[q] = (kAct[q - 1] * fwd[q - 1] + bck[q - 1]) * moja; bck[0] = y;
      if (!isFinite(y)) { y = 0; for (q = 0; q <= ORDEN; q++) { fwd[q] = 0; bck[q] = 0; } }
      // el chip retiene la salida a 8 kHz mientras no hay óxido
      if (o < .25) { if (n % 2 === 0) hold = y; y = hold * (1 - o * 4) + y * o * 4; }
      out16[n] = y;
      if (n % 800 === 0) kRegistro.push([+t.toFixed(2)].concat(Array.prototype.map.call(kAct, function (v) { return +v.toFixed(3); })));
    }
    // a 48 kHz: lineal ×3 y pasabajas
    var N = Math.ceil(D * sr), y48 = new Float32Array(N), lp2 = bq('lp', 7000, .7, sr), lp3 = bq('lp', 7000, .7, sr), pk = 0;
    for (var m = 0; m < N; m++) { var x = m * SRI / sr, a0 = Math.floor(x), fr2 = x - a0, v0 = out16[a0] || 0, v1 = out16[a0 + 1] || 0; y48[m] = paso(lp3, paso(lp2, v0 + (v1 - v0) * fr2)); pk = Math.max(pk, Math.abs(y48[m])); }
    if (pk > 0) for (m = 0; m < N; m++) y48[m] /= pk;
    return { y: y48, k: kRegistro };
  }
  var api = { render: render, levinson: levinson };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.Traductor = api;
})(typeof window !== 'undefined' ? window : globalThis);
