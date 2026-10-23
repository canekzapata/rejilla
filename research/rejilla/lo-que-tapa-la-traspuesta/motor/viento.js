/* viento.js — el viento que lee el terreno («Lo que tapa la traspuesta»).
 *
 * El viento pasa sobre un perfil de Traspuesta (una fila del mapa de alturas) y el perfil decide cómo suena:
 *  - rumor: ruido grave cuyo filtro abre con la velocidad (v) del viento;
 *  - crestas: cada cumbre del perfil es un obstáculo que suelta remolinos (calle de von Kármán) y silba a su tono eólico,
 *    f = St·v/d (Strouhal 0.2), con d el grosor de la cresta: las agudas silban arriba, las romas abajo. Resonadores
 *    estrechos sobre ruido, con su aleteo;
 *  - collados: el hueco entre dos cumbres sopla como una botella (resonador ancho, más grave y con aire).
 * LISO o ESTRIADO (Mil mesetas, «Lo liso y lo estriado»): con `escala` (semitonos que se repiten cada `periodo`, que no
 * tiene que ser 12) los silbidos caen en la retícula — el viento canta en las curvas de nivel. `estria(t)` ∈ [0, 1]
 * pasa de uno al otro: 0 = la altura continua, 1 = la altura de la retícula.
 * Las ráfagas: v(t) = vel(t) · (1 + .35 r_lenta + .15 r_rápida), ruido suave sembrado.
 *
 *   Viento.render({dur, perfiles: [[t, Float32Array]…], vel: [[t, m/s]…], estria: [[t, 0–1]…], escala, periodo, base,
 *                  semilla}, sr) → {L: Float32Array, R: Float32Array}
 */
(function (global) {
  'use strict';
  function rngDe(s) { var h = s >>> 0 || 1; return function () { h ^= h << 13; h >>>= 0; h ^= h >> 17; h ^= h << 5; h >>>= 0; return h / 4294967296 * 2 - 1; }; }
  function curva(v) { return function (t) { if (t <= v[0][0]) return v[0][1]; for (var i = 1; i < v.length; i++) if (t <= v[i][0]) { var u = (t - v[i - 1][0]) / (v[i][0] - v[i - 1][0]); return v[i - 1][1] + (v[i][1] - v[i - 1][1]) * u; } return v[v.length - 1][1]; }; }
  function Reso() { this.y1 = 0; this.y2 = 0; }
  Reso.prototype.tick = function (x, f, q, sr) { var w = 2 * Math.PI * Math.min(f, sr * .45) / sr, R = Math.exp(-Math.PI * f / q / sr); var y = 2 * R * Math.cos(w) * this.y1 - R * R * this.y2 + (1 - R) * x; this.y2 = this.y1; this.y1 = y; return y; };
  function suave(r, hz, sr) { var a = 0, b = 0, k = 1 - Math.exp(-2 * Math.PI * hz / sr); return function () { a += k * (r() - a); b += k * (a - b); return b * 3; }; }

  /* las crestas de un perfil: máximos con prominencia, con su grosor (ancho a media prominencia) y su lugar (pan);
     los collados: mínimos entre dos crestas */
  function leer(perfil) {
    var n = perfil.length, cr = [], co = [];
    for (var i = 2; i < n - 2; i++) {
      var h = perfil[i];
      if (h > perfil[i - 1] && h >= perfil[i + 1] && h > perfil[i - 2] && h >= perfil[i + 2]) {
        var l = i, r = i; while (l > 0 && perfil[l - 1] < perfil[l]) l--; while (r < n - 1 && perfil[r + 1] < perfil[r]) r++;
        var prom = h - Math.max(perfil[l], perfil[r]); if (prom < .008) continue;
        var mitad = h - prom / 2, a = i, b = i; while (a > l && perfil[a] > mitad) a--; while (b < r && perfil[b] > mitad) b++;
        cr.push({ x: i / n, h: h, prom: prom, ancho: (b - a + 1) / n });
      }
    }
    cr.sort(function (a, b) { return b.prom - a.prom; }); cr = cr.slice(0, 6).sort(function (a, b) { return a.x - b.x; });
    for (var k = 0; k + 1 < cr.length; k++) {
      var i0 = Math.round(cr[k].x * n), i1 = Math.round(cr[k + 1].x * n), m = 1e9, mi = i0;
      for (var j = i0; j <= i1; j++) if (perfil[j] < m) { m = perfil[j]; mi = j; }
      co.push({ x: mi / n, h: m, hondo: Math.min(cr[k].h, cr[k + 1].h) - m });
    }
    return { crestas: cr, collados: co };
  }

  function render(c, sr) {
    sr = sr || 48000;
    var n = Math.ceil(c.dur * sr), L = new Float32Array(n), R = new Float32Array(n), r = rngDe(c.semilla || 31);
    var vel = curva(c.vel || [[0, 8]]), est = curva(c.estria || [[0, 0]]), lenta = suave(r, .15, sr), rapida = suave(r, 1.3, sr);
    var perf = c.perfiles.map(function (p) { return [p[0], leer(p[1])]; }), pi = 0;
    var escala = c.escala || [0, 2, 3, 5, 7, 8, 10], periodo = c.periodo || 12, base = c.base == null ? 40 : c.base;
    var resC = [], resK = [], alet = [], lp1 = 0, lp2 = 0;
    for (var k = 0; k < 8; k++) { resC.push([new Reso(), new Reso()]); resK.push(new Reso()); alet.push(suave(r, .8 + k * .37, sr)); }
    var cuant = function (m) {                                      // la retícula: escala que se repite cada `periodo` semitonos
      var o = Math.floor((m - base) / periodo), best = 1e9, bm = m;
      for (var d = -1; d <= 1; d++) for (var j = 0; j < escala.length; j++) { var x = base + (o + d) * periodo + escala[j]; if (Math.abs(x - m) < best) { best = Math.abs(x - m); bm = x; } }
      return bm;
    };
    var fC = new Float64Array(8), fK = new Float64Array(8);
    for (var i = 0; i < n; i++) {
      var t = i / sr;
      if (i % 64 === 0) {
        while (pi + 1 < perf.length && perf[pi + 1][0] <= t) pi++;
        var v = Math.max(0, vel(t)), e = est(t), P = perf[pi][1];
        for (var k1 = 0; k1 < P.crestas.length; k1++) {
          var cr = P.crestas[k1], d = .004 + .05 * cr.ancho;           // grosor del obstáculo (m): la cresta aguda es delgada
          var f = .2 * v / d, m = 69 + 12 * Math.log2(Math.max(20, f) / 440), mq = cuant(m);
          fC[k1] = 440 * Math.pow(2, ((1 - e) * m + e * mq - 69) / 12);
        }
        for (var k2 = 0; k2 < P.collados.length; k2++) {
          var co = P.collados[k2], fb = (60 + 260 * co.h) * (.6 + .05 * v), mb = 69 + 12 * Math.log2(fb / 440);
          fK[k2] = 440 * Math.pow(2, ((1 - e) * mb + e * cuant(mb) - 69) / 12);
        }
      }
      var vv = v * (1 + .35 * lenta() + .15 * rapida()), g = Math.max(0, vv / 12), x = r();
      // rumor: el filtro abre con el viento
      var fc = 70 + 45 * vv, a = 1 - Math.exp(-2 * Math.PI * fc / sr); lp1 += a * (x - lp1); lp2 += a * (lp1 - lp2);
      var sl = lp2 * g * 1.6, srr = lp2 * g * 1.6;
      for (var k3 = 0; k3 < P.crestas.length; k3++) {
        var c3 = P.crestas[k3], al = Math.max(0, .55 + .6 * alet[k3]()), q = 40 + 120 * c3.prom;
        var s = resC[k3][0].tick(x, fC[k3], q, sr) + .4 * resC[k3][1].tick(x, fC[k3] * 2.01, q * .8, sr);
        var amp = g * g * al * (.4 + c3.prom) * 9, pan = c3.x;
        sl += s * amp * (1 - pan); srr += s * amp * pan;
      }
      for (var k4 = 0; k4 < P.collados.length; k4++) {
        var c4 = P.collados[k4], sk = resK[k4].tick(x, fK[k4], 14, sr) * g * (.3 + c4.hondo) * 3;
        sl += sk * (1 - c4.x); srr += sk * c4.x;
      }
      L[i] = sl; R[i] = srr;
    }
    var pk = 0; for (var j2 = 0; j2 < n; j2++) pk = Math.max(pk, Math.abs(L[j2]), Math.abs(R[j2]));
    if (pk > 0) for (var j3 = 0; j3 < n; j3++) { L[j3] /= pk; R[j3] /= pk; }
    return { L: L, R: R };
  }
  var api = { render: render, leer: leer };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.Viento = api;
})(typeof window !== 'undefined' ? window : globalThis);
