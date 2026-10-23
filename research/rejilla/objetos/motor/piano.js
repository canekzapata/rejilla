/* piano.js — piano preparado por modelado físico (loop 10, instrumento 2 de «objetos que cantan»).
 *
 * Cada nota: 1-3 cuerdas al unísono (apenas desafinadas: baten), cada una una guía de onda de desplazamiento en dos
 * tramos (cejilla → punto de preparación → puente). En el puente: pérdida (un polo) y rigidez del acero (cadena de
 * alpasos: estira los armónicos como en un piano real). El martillo de fieltro es un pulso cuyo largo y brillo
 * dependen de la fuerza; su posición (1/8 de la cuerda) se imprime con un peine.
 *
 * LA PREPARACIÓN (Cage) es una unión en el punto donde se pone el objeto, entre los dos tramos:
 *   refleja ρ (un tornillo: la cuerda se parte en dos y aparecen los modos de cada tramo, inarmónicos → campana/gong),
 *   amortigua (goma: seco, de madera), zumba (tornillo suelto, papel, moneda: si el desplazamiento en ese punto
 *   pasa un umbral, el objeto choca contra la cuerda: ruido en el momento del choque).
 * Las cuerdas mueven una tapa armónica (modos de madera); la tapa también se puede golpear (técnica percutiva).
 *
 *   Piano.render({dur, eventos: [{t, m, v, dur, tipo, prep}], prepara(m) → prep|null}, sr) → Float32Array
 *     tipo: 'martillo' (por omisión) · 'pizz' (cuerda pulsada) · 'apagada' (mano sobre la cuerda) · 'caja' (golpe en la madera)
 *     prep: {tipo, pos (0-1 desde el puente), rho, amort, zumbido, umbral} — o una función prep(t) para preparar mientras suena
 */
(function (global) {
  'use strict';
  var hz = function (m) { return 440 * Math.pow(2, (m - 69) / 12); };
  function rngDe(s) { var h = s >>> 0 || 1; return function () { h ^= h << 13; h >>>= 0; h ^= h >> 17; h ^= h << 5; h >>>= 0; return h / 4294967296 * 2 - 1; }; }
  function Retardo(max) { this.b = new Float64Array(max); this.i = 0; this.d = 1; }
  Retardo.prototype.lee = function () {
    var n = this.b.length, r = this.i - this.d; while (r < 0) r += n;
    var i0 = Math.floor(r), f = r - i0; return this.b[i0 % n] * (1 - f) + this.b[(i0 + 1) % n] * f;
  };
  Retardo.prototype.escribe = function (x) { this.b[this.i] = x; this.i = (this.i + 1) % this.b.length; };

  // las preparaciones (valores de partida; la pieza las afina)
  var PREP = {
    tornillo:        { pos: .13, rho: .62, amort: .02, zumbido: 0, umbral: 1 },
    'tornillo-suelto': { pos: .11, rho: .45, amort: .04, zumbido: .35, umbral: .015 },
    goma:            { pos: .09, rho: .22, amort: .38, zumbido: 0, umbral: 1 },
    papel:           { pos: .2, rho: .06, amort: .09, zumbido: .12, umbral: .01 },
    moneda:          { pos: .16, rho: .32, amort: .03, zumbido: .18, umbral: .02 }
  };

  /* una cuerda */
  function Cuerda(sr, f, desafina, prep, semilla) {
    this.sr = sr; this.r = rngDe(semilla);
    var N = sr / (f * Math.pow(2, desafina / 1200));                     // ida y vuelta
    var B = f < 110 ? .0004 : f > 1000 ? .0003 : .00012;                  // rigidez: más en graves y agudos
    this.a = -Math.min(.8, 60 * B * Math.sqrt(f / 110));                  // coeficiente de los alpasos (4 etapas)
    var dAp = 4 * (1 - this.a) / (1 + this.a), pole = .2 + .35 * Math.min(1, f / 2000), dLp = pole / (1 - pole);
    this.pole = pole; this.g = Math.pow(.001, 1 / (Math.max(1.5, 14 - 3.2 * Math.log2(f / 55)) * f));   // T60 de 14 s (grave) a ~1.5 s
    // largo de un sentido: aR y bR se escriben y se leen en la misma muestra (una muestra menos cada uno), por eso +2
    // (con −2 la cuerda quedaba 4 muestras corta: +32 cents en La3, +64 en La4, medido)
    var H = Math.max(4, (N - dAp - dLp + 2) / 2);
    this.H = H; this.prep = prep; var x = prep ? prep.pos : .5;
    var max = Math.ceil(H) + 8;
    this.aR = new Retardo(max); this.aL = new Retardo(max); this.bR = new Retardo(max); this.bL = new Retardo(max);
    this.fija(x);
    this.lp = 0; this.ap = new Float64Array(4); this.apX = new Float64Array(4); this.jlp = 0; this.zum = 0;
    this.apagar = 1;                                                      // 1 = libre; < 1 = apagador
  }
  Cuerda.prototype.fija = function (x) {                                  // el punto de la preparación (desde el puente)
    var hb = Math.max(1, x * this.H), ha = Math.max(1, this.H - hb);
    this.aR.d = ha; this.aL.d = ha; this.bR.d = hb; this.bL.d = hb;
  };
  Cuerda.prototype.tick = function (exc, p) {
    // cejilla: refleja invertido (casi sin pérdida) e inyecta la excitación
    this.aR.escribe(-.999 * this.aL.lee() + exc);
    // la unión (la preparación)
    var ain = this.aR.lee(), bin = this.bL.lee(), oA, oB;
    if (p) {
      // unión sin pérdida (una rotación): refleja ρ y transmite √(1 − ρ²). Con (1 − ρ) se perdía casi la mitad de la
      // energía en cada pasada y el tornillo, en vez de sonar a gong, se apagaba en 0.65 s (medido)
      var k = p.rho, tr = Math.sqrt(1 - k * k);
      oA = -k * ain + tr * bin; oB = tr * ain + k * bin;
      if (p.amort > 0) { var s = 1 - p.amort; this.jlp = .5 * this.jlp + .5 * (oA + oB); oA = s * oA - p.amort * .5 * this.jlp; oB = s * oB - p.amort * .5 * this.jlp; }
      if (p.zumbido > 0) {                                                // el objeto choca contra la cuerda
        var d = Math.abs(ain + bin) - p.umbral;
        if (d > 0) this.zum = Math.min(1, this.zum + d * 40);
        var z = this.zum * p.zumbido * this.r() * .3; this.zum *= .995; oA += z; oB += z;
      }
    } else { oA = bin; oB = ain; }
    this.aL.escribe(oA); this.bR.escribe(oB);
    // puente: pérdida + rigidez, refleja invertido; ahí se escucha la cuerda
    var y = this.bR.lee();
    this.lp = (1 - this.pole) * y + this.pole * this.lp;
    var x = this.lp;
    for (var k2 = 0; k2 < 4; k2++) { var yk = this.a * x + this.apX[k2] - this.a * this.ap[k2]; this.apX[k2] = x; this.ap[k2] = yk; x = yk; }
    this.bL.escribe(-this.g * this.apagar * x);
    return y;
  };

  /* la tapa armónica: modos de madera (Hz, Q, ganancia) */
  var TAPA = [[96, 14, 1], [163, 16, .8], [241, 18, .7], [337, 20, .6], [488, 22, .5], [690, 24, .4], [960, 26, .3], [1420, 28, .22], [2100, 30, .15]];
  function Tapa(sr) {
    this.m = TAPA.map(function (q) {
      var w = 2 * Math.PI * q[0] / sr, R = Math.exp(-Math.PI * q[0] / q[1] / sr);
      return { c1: 2 * R * Math.cos(w), c2: -R * R, g: q[2] * (1 - R), y1: 0, y2: 0 };
    });
  }
  Tapa.prototype.tick = function (x) {
    var s = 0;
    for (var i = 0; i < this.m.length; i++) { var m = this.m[i], y = m.c1 * m.y1 + m.c2 * m.y2 + m.g * x; m.y2 = m.y1; m.y1 = y; s += y; }
    return s;
  };

  /* una voz: las cuerdas de una nota y su excitación */
  function Voz(sr, ev, prep, semilla) {
    var f = hz(ev.m), n = ev.m < 40 ? 1 : ev.m < 60 ? 2 : 3, r = rngDe(semilla);
    this.sr = sr; this.ev = ev; this.t0 = Math.round(ev.t * sr); this.prepF = typeof prep === 'function' ? prep : null;
    var p0 = this.prepF ? this.prepF(ev.t) : prep;
    this.cuerdas = [];
    for (var k = 0; k < n; k++) this.cuerdas.push(new Cuerda(sr, f, (k - (n - 1) / 2) * (.7 + .5 * Math.abs(r())), p0, semilla + k * 97));
    var v = ev.v == null ? .7 : ev.v, tipo = ev.tipo || 'martillo';
    // la excitación: martillo (pulso de coseno; más corto y brillante con más fuerza), pizz (triángulo), apagada (martillo + apagador)
    var largo = tipo === 'pizz' ? .0006 : .0045 - .0035 * v, L = Math.max(4, Math.round(largo * sr));
    var e = new Float64Array(L + Math.round(this.cuerdas[0].H * .25) + 2), peine = Math.round(this.cuerdas[0].H * .25);
    for (var i = 0; i < L; i++) { var u = i / L; e[i] += v * (tipo === 'pizz' ? 1 - Math.abs(2 * u - 1) : .5 - .5 * Math.cos(2 * Math.PI * u)); }
    if (tipo !== 'pizz') for (i = 0; i < L; i++) e[i + peine] -= .8 * v * (.5 - .5 * Math.cos(2 * Math.PI * i / L));   // el punto del martillo (1/8)
    this.e = e; this.tipo = tipo; this.fin = this.t0 + Math.round(((ev.dur || 1) + (tipo === 'apagada' ? 0 : 0)) * sr);
    if (tipo === 'apagada') this.cuerdas.forEach(function (c) { c.apagar = .985; c.pole = Math.min(.9, c.pole + .45); });
    this.vida = this.fin + Math.round(8 * sr); this.i = 0;
  }
  Voz.prototype.tick = function () {
    var exc = this.i < this.e.length ? this.e[this.i] : 0, n = this.t0 + this.i, s = 0;
    if (this.prepF && this.i % 64 === 0) {                                 // preparar mientras suena
      var p = this.prepF(n / this.sr); for (var k = 0; k < this.cuerdas.length; k++) { this.cuerdas[k].prep = p; if (p) this.cuerdas[k].fija(p.pos); }
    }
    if (n === this.fin && this.tipo !== 'pizz') for (k = 0; k < this.cuerdas.length; k++) { this.cuerdas[k].apagar = .9; this.cuerdas[k].pole = .8; }   // el apagador
    for (k = 0; k < this.cuerdas.length; k++) s += this.cuerdas[k].tick(exc, this.cuerdas[k].prep);
    this.i++; return s / this.cuerdas.length;
  };

  function render(c, sr) {
    sr = sr || 48000;
    var n = Math.ceil(c.dur * sr), y = new Float32Array(n), tapa = new Tapa(sr), r = rngDe(c.semilla || 11);
    var evs = c.eventos.slice().sort(function (a, b) { return a.t - b.t; }), ei = 0, voces = [], golpe = 0, gv = 0;
    for (var i = 0; i < n; i++) {
      while (ei < evs.length && Math.round(evs[ei].t * sr) <= i) {
        var ev = evs[ei++];
        if (ev.tipo === 'caja') { golpe = Math.round(.004 * sr); gv = ev.v == null ? .7 : ev.v; continue; }
        var prep = ev.prep !== undefined ? ev.prep : c.prepara ? c.prepara(ev.m) : null;
        voces.push(new Voz(sr, ev, prep, 1000 + ei * 13));
      }
      var s = 0;
      for (var k = voces.length - 1; k >= 0; k--) { s += voces[k].tick(); if (voces[k].t0 + voces[k].i > voces[k].vida) voces.splice(k, 1); }
      var nudillo = 0; if (golpe > 0) { nudillo = gv * (r() * .5 + (golpe > Math.round(.003 * sr) ? 1 : 0)) * 1.2; golpe--; }   // ×1.2: con ×3 tapaba todo; con ×.4 quedaba 8 dB bajo el pizz (medido)
      y[i] = .35 * s + tapa.tick(s * .6 + nudillo) * 2.2;
    }
    return y;
  }
  var api = { render: render, PREP: PREP, hz: hz };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.Piano = api;
})(typeof window !== 'undefined' ? window : globalThis);
