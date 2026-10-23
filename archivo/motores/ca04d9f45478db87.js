/* cuerda.js — cuerda frotada por modelado físico: violín, viola, chelo, contrabajo (instrumento 4 de «objetos que cantan»).
 *
 * El arco (STK Bowed): la cuerda es una guía de onda de velocidad partida en el punto del arco (cejilla ← arco → puente);
 * en ese punto la tabla de fricción decide si el arco agarra la cuerda o la suelta (stick-slip). La presión del arco
 * cambia la pendiente de la tabla y la posición (β) el color. La caja: modos de madera escalados por tamaño.
 *
 * Técnicas (cantantes y percutivas):
 *   'arco' · 'ponticello' (cerca del puente: vidrio) · 'tasto' (sobre el diapasón: flauta) · 'armonico' (flautando a
 *   la octava o la 12a: aproximado, sin dedo físico) · 'tremolo' (el arco va y viene a 12 Hz) ·
 *   'pizz' · 'bartok' (la cuerda rebota contra el diapasón) · 'legno' (col legno battuto: la madera del arco golpea)
 * El PIZZ QUE SE VUELVE HOUSE: con casa ∈ [0, 1] la cuerda pulsada pasa por un filtro resonante de 24 dB con barrido
 * (un pluck de Juno/house de los ochenta) y se le suma una capa de sierras: la madera se vuelve sintetizador.
 *
 *   Cuerda.render({dur, instrumento, eventos: [{t, m, v, dur, tipo, casa}]}, sr) → Float32Array
 */
(function (global) {
  'use strict';
  var hz = function (m) { return 440 * Math.pow(2, (m - 69) / 12); };
  function rngDe(s) { var h = s >>> 0 || 1; return function () { h ^= h << 13; h >>>= 0; h ^= h >> 17; h ^= h << 5; h >>>= 0; return h / 4294967296 * 2 - 1; }; }
  function Retardo(max) { this.b = new Float64Array(max); this.i = 0; this.d = 1; }
  Retardo.prototype.lee = function () { var n = this.b.length, r = this.i - this.d; while (r < 0) r += n; var i0 = Math.floor(r), f = r - i0; return this.b[i0 % n] * (1 - f) + this.b[(i0 + 1) % n] * f; };
  Retardo.prototype.escribe = function (x) { this.b[this.i] = x; this.i = (this.i + 1) % this.b.length; };

  // la caja de cada instrumento: modos de un violín (Hz, Q, ganancia) escalados por tamaño
  var VIOLIN = [[275, 12, 1], [460, 15, .8], [550, 18, .9], [700, 20, .6], [1000, 24, .5], [1500, 28, .4], [2300, 30, .3], [3200, 30, .2]];
  var ESCALA = { violin: 1, viola: .8, chelo: .44, contrabajo: .3 };
  function Caja(sr, inst) {
    var k = ESCALA[inst] || 1;
    this.m = VIOLIN.map(function (q) { var f = q[0] * k, w = 2 * Math.PI * f / sr, R = Math.exp(-Math.PI * f / q[1] / sr); return { c1: 2 * R * Math.cos(w), c2: -R * R, g: q[2] * (1 - R), y1: 0, y2: 0 }; });
  }
  Caja.prototype.tick = function (x) { var s = 0; for (var i = 0; i < this.m.length; i++) { var m = this.m[i], y = m.c1 * m.y1 + m.c2 * m.y2 + m.g * x; m.y2 = m.y1; m.y1 = y; s += y; } return s; };

  var tablaArco = function (x, pendiente) { var s = (x + .001) * pendiente, o = Math.pow(Math.abs(s) + .75, -4); return o > 1 ? 1 : o; };   // STK BowTable

  // filtro de estado variable (TPT, 2 polos); dos en cascada = 24 dB
  function SVF() { this.ic1 = 0; this.ic2 = 0; }
  SVF.prototype.lp = function (x, g, k) {
    var a1 = 1 / (1 + g * (g + k)), v3 = x - this.ic2, v1 = a1 * this.ic1 + g * a1 * v3, v2 = this.ic2 + g * v1;
    this.ic1 = 2 * v1 - this.ic1; this.ic2 = 2 * v2 - this.ic2; return v2;
  };

  function Voz(sr, ev, semilla) {
    this.sr = sr; this.ev = ev; this.r = rngDe(semilla); this.t0 = Math.round(ev.t * sr); this.i = 0;
    var f = hz(ev.m + (ev.tipo === 'armonico' ? 12 : 0)), tipo = ev.tipo || 'arco';
    this.tipo = tipo; this.v = ev.v == null ? .7 : ev.v; this.dur = ev.dur || .6; this.casa = ev.casa || 0; this.f = f;
    var beta = { ponticello: .045, tasto: .3, armonico: .25 }[tipo] || .127;
    // con − 4 (STK) iba de +9 a +118 cents agudo (le faltaban ~5 muestras); arriba de 450 Hz sobran hasta 2 (iba −48/−62)
    var base = sr / f + 1 - Math.min(2, Math.max(0, (f - 450) / 100));
    this.puente = new Retardo(Math.ceil(sr / hz(Math.min(ev.m, ev.m2 == null ? ev.m : ev.m2))) + 16); this.cejilla = new Retardo(Math.ceil(sr / hz(Math.min(ev.m, ev.m2 == null ? ev.m : ev.m2))) + 16);
    this.puente.d = Math.max(1, base * beta); this.cejilla.d = Math.max(1, base * (1 - beta));
    this.pole = { ponticello: .3, tasto: .75, armonico: .7 }[tipo] || .55; this.lp = 0;
    var punteado = tipo === 'pizz' || tipo === 'bartok' || tipo === 'legno';
    this.ganancia = punteado ? .997 : .95;                          // pulsada: la cuerda suena libre más tiempo
    // (los subarmónicos de Kimura no se lograron: con presión .75-.85 cerca del puente la cuerda sigue afinada; YIN)
    // presión por técnica (Schelleng: cerca del puente hace falta más fuerza); con .45 el arco saltaba a la octava en
    // 6 de 21 notas, con .75 ninguna (medido)
    this.presion = { ponticello: .8, tasto: .3, armonico: .15 }[tipo] || .75;
    this.pendiente = 5 - 4 * this.presion;
    this.vida = this.t0 + Math.round((this.dur + (punteado ? 3 : .6)) * sr);
    this.svf1 = new SVF(); this.svf2 = new SVF(); this.saw = [0, 0];
  }
  Voz.prototype.tick = function () {
    var sr = this.sr, t = this.i / sr, tipo = this.tipo, v = this.v, exc = 0, arco = 0;
    var suena = t < this.dur, sueltaT = t - this.dur;
    if (tipo === 'pizz' || tipo === 'bartok') {
      if (this.i < 24) exc = v * (1 - this.i / 24) * .9;                                  // el dedo suelta la cuerda
      if (tipo === 'bartok' && this.i > 40 && this.i < 300) exc += this.r() * v * .5 * Math.exp(-(this.i - 40) / 60);   // rebota contra el diapasón
    } else if (tipo === 'legno') {
      if (this.i < 6) exc = v * .8; if (this.i < 400) exc += this.r() * v * .12 * Math.exp(-this.i / 80);   // la madera del arco
    } else {
      var env = suena ? Math.min(1, t / .06) : Math.max(0, 1 - sueltaT / .08);
      arco = (.03 + .2 * v) * env;
      if (tipo === 'tremolo') arco *= Math.sin(2 * Math.PI * 12 * t) > 0 ? 1 : -1;
      arco *= 1 + .02 * this.r();
    }
    // STK Bowed
    if(this.ev.m2!=null){var uu=Math.min(1,t/this.dur);uu=uu*uu*(3-2*uu);var ff=hz(this.ev.m+(this.ev.m2-this.ev.m)*uu),bb=sr/ff+1-Math.min(2,Math.max(0,(ff-450)/100)),be=tipo==='tasto'?.3:tipo==='ponticello'?.045:tipo==='armonico'?.25:.127;this.puente.d=Math.max(1,bb*be);this.cejilla.d=Math.max(1,bb*(1-be));this.f=ff;} var reflPuente = -this.ganancia * (this.lp = (1 - this.pole) * this.puente.lee() + this.pole * this.lp);
    var reflCejilla = -this.cejilla.lee(), velCuerda = reflPuente + reflCejilla, nueva = 0;
    if (arco !== 0) { var dif = arco - velCuerda; nueva = dif * tablaArco(dif, this.pendiente); }
    this.cejilla.escribe(reflPuente + nueva + exc); this.puente.escribe(reflCejilla + nueva + exc);
    if (!suena && arco === 0 && tipo !== 'pizz' && tipo !== 'bartok') this.ganancia = .9;   // se apaga al soltar
    var y = this.puente.lee();
    // el pizz que se vuelve house: filtro resonante con barrido + sierras
    if (this.casa > 0 && (tipo === 'pizz' || tipo === 'bartok')) {
      var fc = Math.max(120, 1.5 * this.f) + 5200 * Math.exp(-t / .09) * (.6 + .4 * v), g = Math.tan(Math.PI * Math.min(fc, sr * .45) / sr), k = 2 - 1.75 * this.casa;   // más casa, más resonancia
      for (var j = 0; j < 2; j++) { this.saw[j] += this.f * (j ? 1.006 : .994) / sr; if (this.saw[j] > 1) this.saw[j] -= 2; }
      var amp = Math.exp(-t / .35) * v, fuente = y * 4 * (1 - .5 * this.casa) + this.casa * amp * .5 * (this.saw[0] + this.saw[1]);
      var syn = this.svf2.lp(this.svf1.lp(fuente, g, k), g, k);
      syn = Math.tanh(syn * 1.5);
      y = (1 - this.casa) * y + this.casa * syn * .5;
    }
    this.i++; return y;
  };

  function render(c, sr) {
    sr = sr || 48000;
    var n = Math.ceil(c.dur * sr), y = new Float32Array(n), caja = new Caja(sr, c.instrumento || 'chelo');
    var evs = c.eventos.slice().sort(function (a, b) { return a.t - b.t; }), ei = 0, voces = [];
    for (var i = 0; i < n; i++) {
      while (ei < evs.length && Math.round(evs[ei].t * sr) <= i) { voces.push(new Voz(sr, evs[ei], 500 + ei * 7)); ei++; }
      var s = 0, crudo = 0;
      for (var k = voces.length - 1; k >= 0; k--) {
        var vz = voces[k], o = vz.tick();
        if (vz.casa > 0 && (vz.tipo === 'pizz' || vz.tipo === 'bartok')) { s += o * (1 - vz.casa); crudo += o * vz.casa; } else s += o;   // el synth no pasa por la caja
        if (vz.t0 + vz.i > vz.vida) voces.splice(k, 1);
      }
      y[i] = caja.tick(s) * 1.2 + s * .15 + crudo;
    }
    return y;
  }
  var api = { render: render, hz: hz };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.Cuerda = api;
})(typeof window !== 'undefined' ? window : globalThis);
