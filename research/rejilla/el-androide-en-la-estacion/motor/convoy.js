/* convoy.js — el convoy que no sale: un instrumento imposible para «El androide en la estación».
 *
 * El primer convoy de Sutura no salió. Aquí se acerca para siempre y nunca llega.
 *  - EL SILBIDO del maglev es una ilusión de Shepard–Risset: K parciales separados por octavas, todos sobre la tónica, que se
 *    deslizan juntos; cada uno pesa según una campana sobre el logaritmo de la frecuencia, así que los que suben se apagan arriba y
 *    entran nuevos abajo: la altura sube sin fin. Cada parcial lleva el zumbido de su bobina (dos copias que baten, un poco de 2º y
 *    3er armónico) y un trémolo de corriente.
 *  - LAS JUNTAS DEL RIEL: un accelerando de Risset. Cuatro trenes de golpes (cada golpe, un par de ruedas: clac-clac a 70 ms) con
 *    tempos a octavas que aceleran juntos; la campana sobre el log del tempo hace que siempre acelere y nunca llegue.
 *  - `dir` (−1…1): +1 se acerca (sube y acelera), −1 se hunde (baja y se frena para siempre: el descenso). `octava` = segundos que
 *    tarda una vuelta. `cerca` (0–1) abre el filtro, sube el nivel y estrecha el estéreo (lo lejano se abre: está en todas partes).
 *
 *   Convoy.render({dur, tonica (Hz), tempo (golpes/s base), dir: [[t, v]…], cerca: [[t, 0–1]…], octava (s), semilla}, sr) → {L, R}
 */
(function (global) {
  'use strict';
  function rngDe(s) { var h = s >>> 0 || 1; return function () { h ^= h << 13; h >>>= 0; h ^= h >> 17; h ^= h << 5; h >>>= 0; return h / 4294967296 * 2 - 1; }; }
  function curva(v, def) { return function (t) { if (!v || !v.length) return def; if (t <= v[0][0]) return v[0][1]; for (var i = 1; i < v.length; i++) if (t <= v[i][0]) { var u = (t - v[i - 1][0]) / (v[i][0] - v[i - 1][0]); return v[i - 1][1] + (v[i][1] - v[i - 1][1]) * u; } return v[v.length - 1][1]; }; }
  function bq(tipo, f, q, sr) {
    var w = 2 * Math.PI * f / sr, a = Math.sin(w) / (2 * q), c = Math.cos(w), b0, b1, b2;
    if (tipo === 'lp') { b0 = (1 - c) / 2; b1 = 1 - c; b2 = b0; } else if (tipo === 'hp') { b0 = (1 + c) / 2; b1 = -(1 + c); b2 = b0; } else { b0 = a; b1 = 0; b2 = -a; }
    var a0 = 1 + a; return { b0: b0 / a0, b1: b1 / a0, b2: b2 / a0, a1: -2 * c / a0, a2: (1 - a) / a0, x1: 0, x2: 0, y1: 0, y2: 0 };
  }
  function paso(F, x) { var y = F.b0 * x + F.b1 * F.x1 + F.b2 * F.x2 - F.a1 * F.y1 - F.a2 * F.y2; F.x2 = F.x1; F.x1 = x; F.y2 = F.y1; F.y1 = y; return y; }
  function retune(F, tipo, f, q, sr) { var n = bq(tipo, f, q, sr); F.b0 = n.b0; F.b1 = n.b1; F.b2 = n.b2; F.a1 = n.a1; F.a2 = n.a2; }

  function render(c, sr) {
    sr = sr || 48000;
    var N = Math.ceil(c.dur * sr), r = rngDe((c.semilla || 2038) * 17 + 3), dirC = curva(c.dir, 1), cerC = curva(c.cerca, .5);
    var K = 8, fmin = c.tonica / 2, OCT = c.octava || 17, KR = 4, tmin = (c.tempo || 1.882) / 2;
    var L = new Float32Array(N), R = new Float32Array(N), u = 0, v = 0, ph = new Float64Array(K * 2), phR = new Float64Array(KR), fl = bq('lp', 3000, .7, sr), flR = bq('lp', 3000, .7, sr);
    var golpe = [], gi = 0;                                   // golpes vivos: [muestra de inicio, amplitud, pan, tono]
    var trem = 0, cer = .5, d = 1;
    for (var n = 0; n < N; n++) {
      var t = n / sr;
      if ((n & 63) === 0) { d = dirC(t); cer = cerC(t); retune(fl, 'lp', 600 + 6000 * cer * cer, .7, sr); retune(flR, 'lp', 600 + 6000 * cer * cer, .7, sr); }
      u += d / (OCT * sr); v += d / (OCT * sr);
      // el silbido: K parciales a octavas con campana en log f
      var s = 0, sR = 0;
      for (var k = 0; k < K; k++) {
        var x = ((k + u) % K + K) % K, f = fmin * Math.pow(2, x), w = .5 - .5 * Math.cos(2 * Math.PI * x / K);
        for (var cp = 0; cp < 2; cp++) {
          var idx = 2 * k + cp; ph[idx] += f * (1 + (cp ? .0035 : -.0035)) / sr; if (ph[idx] > 1) ph[idx] -= 1;
          var a = 2 * Math.PI * ph[idx], tono = Math.sin(a) + .18 * Math.sin(2 * a) + .07 * Math.sin(3 * a);
          if (cp) sR += w * tono; else s += w * tono;
        }
      }
      trem = 1 + .12 * Math.sin(2 * Math.PI * 100 * t) * cer;     // la corriente de 100 Hz
      // las juntas: KR trenes a octavas de tempo, campana sobre el log del tempo
      for (var j = 0; j < KR; j++) {
        var y = ((j + v) % KR + KR) % KR, tj = tmin * Math.pow(2, y), wj = .5 - .5 * Math.cos(2 * Math.PI * y / KR);
        phR[j] += tj / sr; if (phR[j] >= 1) { phR[j] -= 1; golpe.push([n, wj, r() * .6, 1]); golpe.push([n + Math.round(.07 * sr), wj * .8, r() * .6, 1.3]); }
      }
      var gL = 0, gR = 0;
      for (var g = golpe.length - 1; g >= 0; g--) {
        var G = golpe[g], m = n - G[0]; if (m < 0) continue; if (m > .09 * sr) { golpe.splice(g, 1); continue; }
        var e = G[1] * Math.exp(-m / (.012 * sr)) * (Math.sin(2 * Math.PI * 180 * G[3] * m / sr) * .6 + r() * .5 * Math.exp(-m / (.002 * sr)));
        gL += e * (1 - G[2]) * .5; gR += e * (1 + G[2]) * .5;
      }
      var ancho = 1 - .7 * cer, mid = (s + sR) * .5, side = (s - sR) * .5 * (.3 + ancho);
      var nivel = .25 + .75 * cer;
      L[n] = paso(fl, (mid + side) * trem * .3) * nivel + gL * (.4 + .6 * cer);
      R[n] = paso(flR, (mid - side) * trem * .3) * nivel + gR * (.4 + .6 * cer);
    }
    var pk = 0; for (n = 0; n < N; n++) pk = Math.max(pk, Math.abs(L[n]), Math.abs(R[n])); if (pk > 0) for (n = 0; n < N; n++) { L[n] /= pk; R[n] /= pk; }
    return { L: L, R: R };
  }
  var api = { render: render };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.Convoy = api;
})(typeof window !== 'undefined' ? window : globalThis);
