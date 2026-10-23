/* garganta_duna.js — copia de garganta.js (biblioteca, instrumentos-381572fc353a) para «La duna que canta»: igual, pero un evento
 * puede llevar `curva` y su altura se desliza (el contorno de una cresta cantado como glisando, Cage, Ryoan-ji).
 *
 * garganta.js — la garganta de montaña: un instrumento imposible para «Lo que tapa la traspuesta».
 *
 * Una siringe de pájaro (dos labios, osciladores de van der Pol, como pajaro.js: x'' = −ω²x + ω(p − x²)x') sopla dentro de
 * un tracto vocal de Kelly-Lochbaum: un tubo de N secciones cuyas áreas cambian en el tiempo. La forma del tubo es un PERFIL
 * DEL TERRENO (una fila del mapa de alturas de Traspuesta, remuestreada a N secciones): donde hay valle el tubo se cierra,
 * donde hay cumbre se abre. La montaña resuena como una garganta.
 * Para cantar, el tubo se deforma del perfil hacia la forma de cada vocal (modelo de una constricción de lengua más la
 * apertura de labios); `aprende` ∈ [0, 1] dice cuánto: 0 = la montaña sola, 1 = la vocal. Las oclusivas cierran el tubo en su
 * lugar (p labios, t dientes, k velo), las fricativas soplan ruido en la constricción, las nasales y líquidas estrechan.
 * El tubo puede ser más largo que una garganta (largo > 1): las formantes bajan, una criatura del tamaño de un cerro.
 * Las dos caras de la siringe pueden cantar dos alturas a la vez en el mismo tubo (bifonía): evento {nota2}.
 *
 *   Garganta.render({dur, perfil: Float32Array (0–1), perfiles: [[t, Float32Array]…] (opcional, cambia de fila en el
 *                    tiempo), largo, eventos: [{t, dur, nota, nota2, fonemas: ['k','a'], v, aprende, ronco}]}, sr)
 *   → Float32Array
 */
(function (global) {
  'use strict';
  var hz = function (m) { return 440 * Math.pow(2, (m - 69) / 12); };
  function rngDe(s) { var h = s >>> 0 || 1; return function () { h ^= h << 13; h >>>= 0; h ^= h >> 17; h ^= h << 5; h >>>= 0; return h / 4294967296 * 2 - 1; }; }

  // vocales: [posición de la constricción (0 glotis … 1 labios), área mínima cm², ancho, área de labios cm²]
  // halladas por búsqueda (sondas/afinar_vocales.cjs) contra las formantes del español: a 700/1250, e 450/1900, i 300/2300,
  // o 500/950, u 330/800. No son anatómicas; el tubo las dice (error ≤ 12 %, la i la que más se aleja: F2 2600)
  var VOCAL = { a: [.15, .3, .2, 5], e: [.15, .15, .15, .4], i: [.4, .15, .2, .15], o: [.25, .15, .1, 3], u: [.45, .15, .1, .4] };
  // consonantes: lugar (0–1), tipo; las sonoras cantan durante la oclusión, las sordas sólo soplan
  var CONS = { p: [1, 'ocl', 0], b: [1, 'ocl', 1], m: [1, 'nas', 1], f: [.97, 'fri', 0], t: [.88, 'ocl', 0], d: [.88, 'ocl', 1], n: [.88, 'nas', 1],
    s: [.9, 'fri', 0], l: [.86, 'liq', 1], r: [.86, 'vib', 1], R: [.86, 'vib', 1], 'rr': [.86, 'vib', 1], ch: [.82, 'fri', 0], y: [.78, 'liq', 1],
    k: [.62, 'ocl', 0], g: [.62, 'ocl', 1], x: [.6, 'fri', 0], j: [.6, 'fri', 0], 'ñ': [.8, 'nas', 1], N: [.8, 'nas', 1] };
  function areaVocal(v, n, out) {
    var p = VOCAL[v] || VOCAL.a;
    for (var k = 0; k < n; k++) {
      var x = k / (n - 1), d = (x - p[0]) / p[2];
      out[k] = 3.2 - (3.2 - p[1]) * Math.exp(-d * d);
      if (x > .9) out[k] = out[k] * (1 - (x - .9) * 10) + p[3] * (x - .9) * 10;     // los labios
    }
    return out;
  }
  function areaTerreno(perfil, n, out) {
    for (var k = 0; k < n; k++) {
      var u = k / (n - 1) * (perfil.length - 1), i = Math.floor(u), f = u - i, h = perfil[i] * (1 - f) + perfil[Math.min(perfil.length - 1, i + 1)] * f;
      out[k] = .25 + 5.5 * h * h;                                // valle = tubo cerrado, cumbre = tubo abierto
    }
    return out;
  }

  // la duna: un evento puede llevar `curva` [[u (0–1 de su duración), nota]…]: la altura se desliza por ella (glisando de Ryoan-ji)
  function notaEn(e, u) {
    var v = e.curva; if (!v) return e.nota; var x = Math.max(0, Math.min(1, u / e.dur));
    for (var i = 1; i < v.length; i++) if (x <= v[i][0]) { var w = (x - v[i - 1][0]) / ((v[i][0] - v[i - 1][0]) || 1); return v[i - 1][1] + (v[i][1] - v[i - 1][1]) * w; }
    return v[v.length - 1][1];
  }
  function render(c, sr) {
    sr = sr || 48000;
    // 24 secciones a 48 kHz = 17 cm, una garganta humana (medido: con 44 la F1 neutra caía a 270 Hz)
    var N = Math.round(24 * (c.largo || 1)), n = Math.ceil(c.dur * sr), y = new Float32Array(n), r = rngDe(c.semilla || 23);
    var A = new Float64Array(N), At = new Float64Array(N), Av = new Float64Array(N), Ap = new Float64Array(N), rr = new Float64Array(N);
    var f = new Float64Array(N + 1), b = new Float64Array(N + 1), fn = new Float64Array(N + 1), bn = new Float64Array(N + 1);
    var perfiles = c.perfiles || [[0, c.perfil]], pi = 0;
    areaTerreno(perfiles[0][1], N, At); for (var k = 0; k < N; k++) A[k] = At[k];
    var ev = c.eventos.slice().sort(function (a, b) { return a.t - b.t; }), ei = -1;
    // la siringe: dos lados (x1, x2) con su altura y presión
    var x1 = 0, v1 = 0, x2 = 0, v2 = 0, sub = 4, dt = 1 / (sr * sub), lpOut = 0, prevOut = 0, ruidoLP = 0;
    var BLOQ = 48, w1 = 0, w2 = 0, p1 = -1, p2 = -1, ruidoAmp = 0, ruidoPos = -1, cierre = -1, cierreAmt = 0, ganV = 0, nasal = 0, vib = 0;
    for (var i = 0; i < n; i++) {
      var t = i / sr;
      if (i % BLOQ === 0) {
        while (pi + 1 < perfiles.length && perfiles[pi + 1][0] <= t) { pi++; areaTerreno(perfiles[pi][1], N, At); }
        while (ei + 1 < ev.length && ev[ei + 1].t <= t) ei++;
        var e = ei >= 0 ? ev[ei] : null, u = e ? t - e.t : 1e9, viva = e && u < e.dur + .06;
        // ¿qué fonema suena ahora? se reparten en la sílaba: las consonantes 55 ms (o 90 las fricativas), la vocal el resto
        var fon = 'a', idx = 0, tipoC = null, lugar = 0, sonora = 1;
        if (viva) {
          var fs_ = e.fonemas || ['a'], durC = 0, nv = 0;
          fs_.forEach(function (q) { if (VOCAL[q]) nv++; else durC += (CONS[q] && CONS[q][1] === 'fri') ? .09 : .055; });
          var durV = Math.max(.04, (e.dur - durC) / Math.max(1, nv)), acc = 0;
          for (var j = 0; j < fs_.length; j++) {
            var q = fs_[j], dq = VOCAL[q] ? durV : ((CONS[q] && CONS[q][1] === 'fri') ? .09 : .055);
            if (u < acc + dq || j === fs_.length - 1) { fon = q; idx = j; break; }
            acc += dq;
          }
          if (!VOCAL[fon]) { var cc = CONS[fon] || [.8, 'liq', 1]; lugar = cc[0]; tipoC = cc[1]; sonora = cc[2]; }
          var vocal = VOCAL[fon] ? fon : (fs_.slice(idx).filter(function (q) { return VOCAL[q]; })[0] || fs_.filter(function (q) { return VOCAL[q]; }).slice(-1)[0] || 'a');
          areaVocal(vocal, N, Av);
        }
        var apr = viva ? (e.aprende == null ? .85 : e.aprende) : 0;
        for (var k2 = 0; k2 < N; k2++) Ap[k2] = At[k2] * (1 - apr) + Av[k2] * apr;
        cierre = -1; cierreAmt = 0; ruidoAmp = 0; nasal = 0;
        if (viva && tipoC) {
          cierre = Math.min(N - 1, Math.round(lugar * (N - 1)));
          if (tipoC === 'ocl') cierreAmt = .985; else if (tipoC === 'nas') { cierreAmt = .97; nasal = 1; }
          else if (tipoC === 'fri') { cierreAmt = .9; ruidoAmp = .5; } else if (tipoC === 'liq') cierreAmt = .7;
          else if (tipoC === 'vib') cierreAmt = .9 * (.5 + .5 * Math.sin(2 * Math.PI * 26 * u));   // la rr late a 26 Hz
          if (tipoC === 'ocl' && !sonora && u > 0) ruidoAmp = 0;
        }
        // las áreas se mueven con inercia (~25 ms): coarticulación
        var a = 1 - Math.exp(-BLOQ / (sr * .025));
        for (var k3 = 0; k3 < N; k3++) {
          var meta = Ap[k3];
          if (cierre >= 0) { var dd = Math.abs(k3 - cierre); if (dd <= 2) meta = meta * (1 - cierreAmt * (1 - dd * .3)) + .02; }
          A[k3] += (meta - A[k3]) * a;
        }
        for (var k4 = 0; k4 < N - 1; k4++) rr[k4] = (A[k4] - A[k4 + 1]) / (A[k4] + A[k4 + 1]);
        // la siringe
        if (viva) {
          var vibr = 1 + .006 * Math.sin(2 * Math.PI * 5.3 * t) * Math.min(1, u / .35);
          w1 = 2 * Math.PI * hz(notaEn(e, u)) * vibr; w2 = e.nota2 != null ? 2 * Math.PI * hz(e.nota2) * vibr : 0;
          var env = Math.min(1, u / .02) * Math.max(0, Math.min(1, (e.dur + .05 - u) / .05));
          var pr = (.08 + .5 * (e.v == null ? .7 : e.v) + .6 * (e.ronco || 0)) * env;
          var muda = tipoC && !sonora;
          p1 = muda ? -.4 : pr; p2 = w2 ? (muda ? -.4 : pr * .8) : -1; ganV = env;
          ruidoPos = cierre; if (muda) ruidoAmp = Math.max(ruidoAmp, tipoC === 'ocl' ? (u - acc < .02 ? 0 : .7) : .55);
        } else { p1 = -1; p2 = -1; ganV = 0; ruidoAmp = 0; }
      }
      // van der Pol, dos lados, 4× sobremuestreo semi-implícito
      var src = 0;
      if (p1 > 0) v1 += .02 * w1 * r(); if (p2 > 0) v2 += .02 * w2 * r();     // el aire nunca es liso: sin este empujón el oscilador se queda en cero
      for (var s = 0; s < sub; s++) {
        if (w1) { var acc1 = -w1 * w1 * x1 + w1 * (p1 - x1 * x1) * v1; v1 += acc1 * dt; x1 += v1 * dt; if (x1 > 4) x1 = 4; if (x1 < -4) x1 = -4; }
        if (w2) { var acc2 = -w2 * w2 * x2 + w2 * (p2 - x2 * x2) * v2; v2 += acc2 * dt; x2 += v2 * dt; if (x2 > 4) x2 = 4; if (x2 < -4) x2 = -4; }
      }
      src = (Math.max(0, x1) + (w2 ? Math.max(0, x2) * .8 : 0)) * .25;      // flujo: sólo cuando los labios se abren
      if (c.fuente === 'ruido') src = ganV * r() * .2;                        // para medir el tubo: ruido blanco en vez de siringe
      ruidoLP += .35 * (r() - ruidoLP);
      // Kelly-Lochbaum: glotis (refleja .75) → N secciones → labios (refleja −.85)
      fn[0] = src + .75 * b[0];
      for (var k5 = 0; k5 < N - 1; k5++) {
        var rk = rr[k5], fi = f[k5], bi = b[k5 + 1];
        fn[k5 + 1] = (1 + rk) * fi - rk * bi;
        bn[k5] = rk * fi + (1 - rk) * bi;
      }
      if (ruidoAmp > 0 && ruidoPos >= 0) fn[Math.min(N - 1, ruidoPos + 1)] += ruidoAmp * ruidoLP * .3;
      var salida = f[N - 1];
      bn[N - 1] = -.85 * salida;
      for (var k6 = 0; k6 < N; k6++) { f[k6] = fn[k6] * .9993; b[k6] = bn[k6] * .9993; }
      // radiación de los labios (derivada) y, si es nasal, el sonido sale por la nariz: pasabajos
      var o = (1 - .85) * salida, rad = o - prevOut; prevOut = o;
      lpOut += .08 * (o - lpOut);
      y[i] = nasal ? lpOut * 3 : rad * 4 + lpOut * .5;
    }
    var pk = 0; for (var q2 = 0; q2 < n; q2++) pk = Math.max(pk, Math.abs(y[q2]));
    if (pk > 0) for (var q3 = 0; q3 < n; q3++) y[q3] /= pk;
    return y;
  }
  var api = { render: render, VOCAL: VOCAL, CONS: CONS, areaVocal: areaVocal, areaTerreno: areaTerreno };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.Garganta = api;
})(typeof window !== 'undefined' ? window : globalThis);
