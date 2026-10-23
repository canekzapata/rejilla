/* duna.js — la duna que canta: un instrumento imposible para «La duna que canta».
 *
 * Las dunas que braman (Mar de Arena, Kelso, Badain Jaran) cantan una sola nota grave, de 70 a 110 Hz, cuando una avalancha baja
 * por su cara de sotavento. La nota no depende del tamaño de la duna sino del grano: f ≈ 0.4 · √(g / d) (Andreotti, Douady).
 * La explicación que usamos: en la capa que se desliza cada grano choca con los de abajo a su propio ritmo; mientras chocan cada
 * uno a su hora se oye un siseo (lluvia de granos), pero si la avalancha es lo bastante fuerte los choques se SINCRONIZAN y
 * todos pegan juntos: el siseo se vuelve una nota. Es un sistema de Kuramoto:
 *     dθᵢ/dt = ωᵢ + K · r · sin(ψ − θᵢ) + ruido      (r e^{iψ} = el promedio de e^{iθ}: la coherencia de la masa)
 * Cada vuelta de fase es un choque (un clic). Con K abajo del umbral (K_c ≈ 1.6 σ para una dispersión gaussiana σ) la masa es
 * estadística (Xenakis, Grisey: importa la media, no el grano); arriba del umbral los clics se juntan en un tren periódico y el
 * tren es altura (Stockhausen: más de 15–20 impulsos por segundo dejan de ser ritmo). Si además la frecuencia de los choques
 * sube de 5 a 80 Hz, la misma masa pasa del ritmo a la nota (Kontakte X, al revés).
 * El cuerpo: la capa seca de la superficie es una guía de ondas (Vriend) que resuena a la nota: un resonador en f y en sus dos
 * primeros armónicos, que pesa más cuanto más coherente es la masa. Encima, el grano: cada clic pasa por un filtro agudo y corto.
 * Scelsi: la nota no se queda quieta por dentro (la dispersión, el ruido y el flujo la mueven): tiene profundidad.
 *
 *   Duna.render({dur, f: [[t, Hz]…], K: [[t, múltiplo de K_c]…], flujo: [[t, 0–1]…], sigma (dispersión relativa, .06),
 *                M (granos, 96), ruido (rad/√s, .6), cuerpo (0–1, .7), semilla}, sr)
 *   → {L, R, r: Float32Array (la coherencia, a 100 Hz)}
 */
(function (global) {
  'use strict';
  function rngDe(s) { var h = s >>> 0 || 1; return function () { h ^= h << 13; h >>>= 0; h ^= h >> 17; h ^= h << 5; h >>>= 0; return h / 4294967296 * 2 - 1; }; }
  function curva(v, def) { return function (t) { if (!v || !v.length) return def; if (t <= v[0][0]) return v[0][1]; for (var i = 1; i < v.length; i++) if (t <= v[i][0]) { var u = (t - v[i - 1][0]) / (v[i][0] - v[i - 1][0]); return v[i - 1][1] + (v[i][1] - v[i - 1][1]) * u; } return v[v.length - 1][1]; }; }
  function gauss(r) { var s = 0; for (var k = 0; k < 6; k++) s += r(); return s / Math.sqrt(2); }   // 6 uniformes en [-1,1): varianza 2 → normal
  function bq(tipo, f, q, sr) {   // biquad RBJ
    var w = 2 * Math.PI * f / sr, a = Math.sin(w) / (2 * q), c = Math.cos(w), b0, b1, b2;
    if (tipo === 'bp') { b0 = a; b1 = 0; b2 = -a; } else if (tipo === 'lp') { b0 = (1 - c) / 2; b1 = 1 - c; b2 = b0; } else { b0 = (1 + c) / 2; b1 = -(1 + c); b2 = b0; }
    var a0 = 1 + a; return { b0: b0 / a0, b1: b1 / a0, b2: b2 / a0, a1: -2 * c / a0, a2: (1 - a) / a0, x1: 0, x2: 0, y1: 0, y2: 0 };
  }
  function paso(F, x) { var y = F.b0 * x + F.b1 * F.x1 + F.b2 * F.x2 - F.a1 * F.y1 - F.a2 * F.y2; F.x2 = F.x1; F.x1 = x; F.y2 = F.y1; F.y1 = y; return y; }
  function retune(F, f, q, sr) { var n = bq('bp', f, q, sr); F.b0 = n.b0; F.b1 = n.b1; F.b2 = n.b2; F.a1 = n.a1; F.a2 = n.a2; }

  function render(c, sr) {
    sr = sr || 48000;
    var N = Math.ceil(c.dur * sr), M = c.M || 96, sig = c.sigma == null ? .06 : c.sigma, D = c.ruido == null ? .6 : c.ruido, cuerpo = c.cuerpo == null ? .7 : c.cuerpo;
    var r = rngDe((c.semilla || 675) * 7 + 3), fC = curva(c.f, 80), kC = curva(c.K, 0), flC = curva(c.flujo, 0);
    var Kc = 1.6 * sig;                                        // umbral de Kuramoto (en unidades de la frecuencia media)
    var dev = new Float64Array(M), cs = new Float64Array(M), sn = new Float64Array(M), amp = new Float64Array(M), pan = new Float64Array(M);
    for (var i = 0; i < M; i++) { dev[i] = gauss(r) * sig; var th = Math.PI * (r() + 1); cs[i] = Math.cos(th); sn[i] = Math.sin(th); amp[i] = .6 + .4 * Math.abs(r()); pan[i] = r(); }
    var L = new Float32Array(N), R = new Float32Array(N), coh = new Float32Array(Math.ceil(c.dur * 100));
    // filtros: el grano (agudo, corto) y el cuerpo (la capa de la superficie: resonadores en f, 2f, 3f que se reafinan cada 64 muestras)
    var granoL = bq('bp', 3200, 1.2, sr), granoR = bq('bp', 3600, 1.2, sr), bajoL = bq('lp', 900, .7, sr), bajoR = bq('lp', 900, .7, sr);
    var cap = [bq('bp', 80, 6, sr), bq('bp', 160, 5, sr), bq('bp', 240, 4, sr)], capG = [1, .45, .2];
    var sqdt = Math.sqrt(1 / sr), rr = 0, psi = 0, f = 80, K = 0, fl = 0, cohS = 0;
    for (var n = 0; n < N; n++) {
      var t = n / sr;
      if ((n & 63) === 0) { f = fC(t); K = kC(t) * Kc; fl = flC(t); for (var j = 0; j < 3; j++) retune(cap[j], Math.min(f * (j + 1), sr * .45), [6, 5, 4][j], sr); }
      if (fl <= 1e-4) continue;
      // el campo medio
      var mc = 0, ms = 0; for (i = 0; i < M; i++) { mc += cs[i]; ms += sn[i]; } mc /= M; ms /= M;
      rr = Math.sqrt(mc * mc + ms * ms); var cps = rr > 1e-9 ? mc / rr : 1, sps = rr > 1e-9 ? ms / rr : 0;
      var w = 2 * Math.PI * f / sr, cl = 0, clL = 0, clR = 0;
      for (i = 0; i < M; i++) {
        var s0 = sn[i], c0 = cs[i];
        var acople = K * rr * (sps * c0 - cps * s0);              // sin(ψ − θ)
        var d = w * (1 + dev[i] + acople) + D * sqdt * r() * 1.7;  // (r uniforme en [-1,1): ×1.7 ≈ desviación 1)
        var s1 = s0 + d * c0, c1 = c0 - d * s0, nr = 1 / Math.sqrt(s1 * s1 + c1 * c1); s1 *= nr; c1 *= nr;
        if (s0 < 0 && s1 >= 0 && c1 > 0) {                         // una vuelta: un choque
          var a = amp[i] * (.7 + .3 * r()); cl += a; clL += a * (1 - pan[i]) * .5; clR += a * (1 + pan[i]) * .5;
        }
        sn[i] = s1; cs[i] = c1;
      }
      cohS += .001 * (rr - cohS);
      if (n % 480 === 0) coh[n / 480 | 0] = rr;
      // el grano: los clics, agudos y estéreo; el cuerpo: el tren grave por la capa (pesa con la coherencia)
      var gL = paso(granoL, clL), gR = paso(granoR, clR), b = 0;
      for (j = 0; j < 3; j++) b += capG[j] * paso(cap[j], cl);
      var bb = paso(bajoL, cl), bb2 = paso(bajoR, cl), wC = cuerpo * (.25 + .75 * cohS);
      L[n] = fl * (.35 * gL + wC * (b * 3 + .5 * bb));
      R[n] = fl * (.35 * gR + wC * (b * 3 + .5 * bb2));
    }
    return { L: L, R: R, r: coh };
  }
  var api = { render: render };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.Duna = api;
})(typeof window !== 'undefined' ? window : globalThis);
