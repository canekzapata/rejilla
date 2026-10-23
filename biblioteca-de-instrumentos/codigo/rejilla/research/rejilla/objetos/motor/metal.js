/* metal.js — trombón y trompeta con sordina (instrumento 11 de «objetos que cantan»), por modelado físico.
 *
 * Los labios son la lengüeta: una válvula que se abre hacia afuera, con su propia resonancia (la tensión de los labios),
 * acoplada al tubo. Como el Brass de la STK (Cook), una guía de onda:
 *     boca = 0.3 · presión;  tubo = 0.85 · regreso del tubo
 *     Δ = labio(boca − tubo)   (resonador de dos polos a la frecuencia de los labios, radio 0.997)
 *     área = min(1, Δ²)        (los labios abiertos dejan pasar la boca; cerrados, rebota el tubo)
 *     al tubo: área · boca + (1 − área) · tubo   →  línea de retardo de 2·sr/f (ida y vuelta)
 * La vara del trombón es el largo de esa línea: se desliza sin saltos (glisando). La trompeta es el mismo modelo más
 * arriba y más brillante.
 * Técnicas: 'normal' · 'lengua' (golpe de lengua: ataque duro y corto) · 'growl' (cantar mientras se toca: la voz
 * modula la presión, áspero) · 'aire' (soplar sin nota: el ruido del aire resuena en el tubo) · 'frulato' (la lengua
 * aletea la r: la presión late a 25 Hz).
 * Sordinas (filtros en la campana): 'abierta', 'straight' (aguda y metálica), 'cup' (redonda), 'harmon' (nasal, la de
 * Miles: una resonancia estrecha arriba y casi nada de graves), 'plunger' (el destapacaños de mano: un pasabajos
 * resonante que se abre y se cierra = wah).
 *
 *   Metal.render({dur, voz: 'trombon'|'trompeta', sordina, wah: [[t, abre 0-1]…], notas: [{t, dur, m, m2, tipo, v}]}, sr)
 */
(function (global) {
  'use strict';
  var hz = function (m) { return 440 * Math.pow(2, (m - 69) / 12); };
  function rngDe(s) { var h = s >>> 0 || 1; return function () { h ^= h << 13; h >>>= 0; h ^= h >> 17; h ^= h << 5; h >>>= 0; return h / 4294967296; }; }
  // filtro de estado variable (Chamberlin): lp, bp, hp de un solo golpe; f en Hz, q
  function SVF(sr) { this.sr = sr; this.l = 0; this.b = 0; }
  SVF.prototype.tick = function (x, f, q) {
    var F = 2 * Math.sin(Math.PI * Math.min(f, this.sr / 6) / this.sr), h = x - this.l - this.b / q;
    this.b += F * h; this.l += F * this.b; return { l: this.l, b: this.b, h: h };
  };
  // corrección de afinación (medida): los labios jalan la altura, de +41 cents en Mi2 a −101 en Do6, casi en línea recta
  // en los dos instrumentos: cents ≈ 167 − 3.2·m. Se pide la nota corregida al revés
  var CORR = function (m) { return Math.pow(2, (3.2 * m - 167) / 1200); };

  function render(c, sr) {
    sr = sr || 48000;
    var n = Math.ceil(c.dur * sr), y = new Float32Array(n), r = rngDe(c.semilla || 11), voz = c.voz || 'trombon', sord = c.sordina || 'abierta';
    var notas = c.notas.slice().sort(function (a, b) { return a.t - b.t; }), L = 1 << 14, linea = new Float32Array(L), w = 0;
    var l1 = 0, l2 = 0, x1 = 0, x2 = 0, o1 = 0, elp = 0, soplo = 0, dcx = 0, dcy = 0, ni = -1, fAct = 0, pres = 0, ruido = 0, gv = 0, s1 = new SVF(sr), s2 = new SVF(sr), s3 = new SVF(sr), hp = 0, cam = 0;
    var wah = c.wah || [[0, 1]], H0 = c._h0 == null ? .3 : c._h0, K = c._k == null ? -2 : c._k, LIP = c._lip || .92;
    var abre = function (t) {
      if (t <= wah[0][0]) return wah[0][1];
      for (var k = 1; k < wah.length; k++) if (t < wah[k][0]) return wah[k - 1][1] + (wah[k][1] - wah[k - 1][1]) * (t - wah[k - 1][0]) / (wah[k][0] - wah[k - 1][0]);
      return wah[wah.length - 1][1];
    };
    for (var i = 0; i < n; i++) {
      var t = i / sr;
      while (ni + 1 < notas.length && notas[ni + 1].t <= t) ni++;
      var nt = ni >= 0 ? notas[ni] : null, u = nt ? t - nt.t : 0, sonando = nt && u < nt.dur, tipo = nt ? nt.tipo || 'normal' : 'normal';
      // la frecuencia que pide la vara/los labios: glisando m → m2 a lo largo de la nota; entre notas ligadas, 50 ms de vara
      var fT = nt ? hz(nt.m2 == null ? nt.m : nt.m + (nt.m2 - nt.m) * Math.min(1, u / nt.dur)) : 100; if (nt) fT *= CORR(nt.m2 == null ? nt.m : nt.m + (nt.m2 - nt.m) * Math.min(1, u / nt.dur));
      fAct = fAct ? fAct + (fT - fAct) * (voz === 'trombon' ? .0006 : .002) : fT;
      // la presión: ataque (lengua 3 ms, normal 18 ms), sostiene, suelta en 30 ms
      var v = nt ? (nt.v == null ? .8 : nt.v) : 0, ataque = tipo === 'lengua' ? .003 : .018, objetivo = sonando ? v : 0;
      if (tipo === 'lengua' && sonando) objetivo = v * (1.25 * Math.exp(-u / .06) + .5);        // el golpe empuja y se retira
      pres += (objetivo - pres) * (objetivo > pres ? 1 / (ataque * sr) : 1 / (.03 * sr)) * 2.2;
      var p = pres * (1 + .025 * Math.sin(2 * Math.PI * 5.2 * t) * Math.min(1, u / .4));        // vibrato de labio, tarde
      if (tipo === 'growl') { gv += 2 * Math.PI * hz(nt.m - 19) / sr; ruido += .03 * ((r() * 2 - 1) - ruido); p *= 1 + .55 * Math.sin(gv) + .35 * ruido; }
      if (tipo === 'frulato') p *= .65 + .35 * Math.sign(Math.sin(2 * Math.PI * 25 * t));
      var aire = tipo === 'aire', boca = .3 * (aire ? 0 : .35 + .65 * p) * 3.2 * (p > .01 ? 1 : p * 100) * (1 + (.02 * Math.exp(-u / .05) + .002) * (r() * 2 - 1));   // un poco de turbulencia: sin ella los labios no arrancan (el resonador no deja pasar la presión constante)
      // el tubo: línea de retardo con lectura interpolada (la vara cambia su largo sin saltos)
      var D = Math.min(L - 4, 2 * sr / fAct + 3), rp = w - D; while (rp < 0) rp += L;
      var i0 = Math.floor(rp), fr = rp - i0, regreso = linea[i0 & (L - 1)] * (1 - fr) + linea[(i0 + 1) & (L - 1)] * fr;
      var tubo = .85 * regreso;
      // los labios: resonador de dos polos a fAct (radio .997, normalizado)
      var R = .997, a1 = -2 * R * Math.cos(2 * Math.PI * fAct * LIP / sr), a2 = R * R, b0 = .5 - .5 * R * R;
      var x = boca - tubo, lab = b0 * x - b0 * x2 - a1 * l1 - a2 * l2;
      x2 = x1; x1 = x; l2 = l1; l1 = lab;
      var area = Math.max(0, Math.min(1, H0 + K * lab)), sal = area * boca + (1 - area) * tubo;
      if (aire) { soplo += .12 * ((r() * 2 - 1) - soplo); sal = tubo + soplo * pres * 1.4; }   // ×1.4: con .25 el soplo quedaba 15 dB bajo los golpes (medido)   // soplar sin nota: el ruido (pasabajos ~1 kHz) entra al tubo y resuena
      dcy = sal - dcx + .995 * dcy; dcx = sal; linea[w] = dcy; w = (w + 1) & (L - 1);
      // la campana radía sobre todo los agudos (pasaaltos de un polo); la trompeta, más brillante
      var o = dcy - (voz === 'trompeta' ? .6 : .8) * hp; hp = dcy;
      // lo «cuivré»: tocado fuerte, la onda se empina al viajar por el tubo (propagación no lineal) y el metal se abre.
      // Aproximado con la pendiente de la onda, que pesa más con la presión (∝ v²): sin esto el modelo sonaba casi a seno
      // (centroide 260 Hz en un Mi3)
      var emp = (o - o1) * sr / (2 * Math.PI * 700); o1 = o; elp += .45 * (emp - elp); o = o + (aire ? 0 : .25 + 4 * Math.min(1, pres * pres)) * elp;   // (pasabajos ~5 kHz: que no se empine el ruido)
      // la sordina
      if (sord === 'straight') { var q = s1.tick(o, 1800, 1.6); o = q.b * 1.6 + q.h * .5; }
      else if (sord === 'cup') o = s1.tick(o, 1100, .9).l;
      else if (sord === 'harmon') { var q2 = s1.tick(o, voz === 'trompeta' ? 2100 : 1500, 5); o = q2.b * 2.2 + s2.tick(o, 3600, 3).b * .6; }
      else if (sord === 'plunger') { var ab = abre(t), fc = 300 * Math.pow(12, ab); o = s1.tick(o, fc, 2.4 - ab).l * (.55 + .45 * ab); }
      // niveles (medidos): la trompeta sonaba 9 dB arriba del trombón; la harmon, 4-5 dB arriba de abierta; la straight, 3 dB abajo
      y[i] = o * (voz === 'trompeta' ? .35 : 1) * (sord === 'harmon' ? .5 : sord === 'straight' ? 1.4 : 1);
    }
    return y;
  }
  var api = { render: render, CORR: CORR, hz: hz };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.Metal = api;
})(typeof window !== 'undefined' ? window : globalThis);
