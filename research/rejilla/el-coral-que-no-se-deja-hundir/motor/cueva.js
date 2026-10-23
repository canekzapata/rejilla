/* cueva.js — la cueva que gotea: un instrumento para «Primero sueño en el cenote».
 *
 * Cada dolina del karst es una cámara y en cada una cuelga un gotero.
 *  - LA GOTA: al caer en el agua encierra una burbuja que suena (Minnaert): f₀ ≈ 3.26 / r (r en metros), se apaga con
 *    d = 0.13/r + 0.0072·r^(−3/2) y sube de tono mientras se cierra, f(t) = f₀ (1 + ξ·d·t) (van den Doel 2005). Antes, el golpecito
 *    de la gota contra el agua.
 *  - LA CÁMARA: la gota suena dentro de su dolina. Dos resonadores: el de Helmholtz de la cámara (con el volumen y la boca de la
 *    dolina, subido por octavas al registro audible: f_h) y un modo de la bóveda (f_b). La cámara colorea la cola; la misma gota
 *    suena distinta según la caverna.
 * La cámara está a su lugar del estéreo (la x de la dolina).
 *
 *   Cueva.render({dur, camaras: {id: {fh, fb, q, pan, eco}}, gotas: [{t, id, r (mm), v}], semilla}, sr) → {L, R}
 */
(function (global) {
  'use strict';
  function rngDe(s) { var h = s >>> 0 || 1; return function () { h ^= h << 13; h >>>= 0; h ^= h >> 17; h ^= h << 5; h >>>= 0; return h / 4294967296 * 2 - 1; }; }
  function reso(f, q, sr) { var w = 2 * Math.PI * f / sr, R = Math.exp(-Math.PI * f / q / sr); return { a1: 2 * R * Math.cos(w), a2: -R * R, g: (1 - R * R) * .5, y1: 0, y2: 0 }; }
  function paso(F, x) { var y = F.a1 * F.y1 + F.a2 * F.y2 + F.g * x; F.y2 = F.y1; F.y1 = y; return y; }

  function render(c, sr) {
    sr = sr || 48000;
    var N = Math.ceil(c.dur * sr), L = new Float32Array(N), R = new Float32Array(N), r = rngDe(c.semilla || 43);
    c.gotas.forEach(function (g) {
      var cm = c.camaras[g.id]; if (!cm) return;
      var rad = (g.r || 3) / 1000, f0 = 3.26 / rad, d = .13 / rad + .0072 * Math.pow(rad, -1.5), xi = .1, v = g.v == null ? .7 : g.v;
      var i0 = Math.round(g.t * sr), n = Math.min(N - i0, Math.round((.6 + 2.2 * (cm.eco || .5)) * sr));
      if (n <= 0) return;
      var Fh = reso(cm.fh, cm.q || 18, sr), Fb = reso(cm.fb, (cm.q || 18) * 1.6, sr), ph = 0, gl = Math.cos((cm.pan + 1) * Math.PI / 4), gr = Math.sin((cm.pan + 1) * Math.PI / 4);
      for (var k = 0; k < n; k++) {
        var t = k / sr, burbuja = 0;
        if (t < 8 / d) { ph += 2 * Math.PI * f0 * (1 + xi * d * t) / sr; burbuja = Math.sin(ph) * Math.exp(-d * t); }
        var golpe = k < 120 ? r() * Math.exp(-k / 18) * .6 : 0;
        var x = (burbuja + golpe) * v, cam = paso(Fh, x) * 2.4 + paso(Fb, x) * 1.6;
        var y = x * .55 + cam * (cm.eco || .5);
        L[i0 + k] += y * gl; R[i0 + k] += y * gr;
      }
    });
    var pk = 0; for (var i = 0; i < N; i++) pk = Math.max(pk, Math.abs(L[i]), Math.abs(R[i])); if (pk > 0) for (i = 0; i < N; i++) { L[i] /= pk; R[i] /= pk; }
    return { L: L, R: R };
  }
  var api = { render: render };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.Cueva = api;
})(typeof window !== 'undefined' ? window : globalThis);
