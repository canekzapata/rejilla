/* clarinete.js — clarinete bajo por modelado físico (instrumento 3 de «objetos que cantan»).
 *
 * Tubo CILÍNDRICO cerrado en la caña (un retardo, reflexión invertida: sólo armónicos impares, el sonido hueco del
 * clarinete) + tabla de caña con pendiente negativa (STK Clarinet). El periodo es dos viajes del tubo: el retardo es
 * medio periodo (con el tubo entero sonaba una octava abajo: lo que pasó con el saxofón sin conicidad).
 * Además una campana (filtro de radiación) y el cuerpo de llaves.
 *
 * Técnicas, cantantes y percutivas:
 *   'normal'      legato con vibrato de aire
 *   'subtono'     poco soplo, mucho aire: sordo y cercano
 *   'slap'        golpe de lengua: la caña se pega y se suelta (un pulso de presión negativa y un tono cortísimo)
 *   'llaves'      golpes de llaves sin soplo: el tubo suena como percusión afinada a la nota que se digita
 *   'multifonico' sobresoplo con la tabla de caña llevada al caos: dos o más alturas a la vez, áspero
 *   'aire'        sólo aire por el tubo (ruido filtrado por sus resonancias)
 *
 *   Clarinete.render({dur, eventos: [{t, m, v, dur, tipo, gliss}]}, sr) → Float32Array
 */
(function (global) {
  'use strict';
  var hz = function (m) { return 440 * Math.pow(2, (m - 69) / 12); };
  function rngDe(s) { var h = s >>> 0 || 1; return function () { h ^= h << 13; h >>>= 0; h ^= h >> 17; h ^= h << 5; h >>>= 0; return h / 4294967296 * 2 - 1; }; }
  function Retardo(max) { this.b = new Float64Array(max); this.i = 0; this.d = 1; }
  Retardo.prototype.lee = function () { var n = this.b.length, r = this.i - this.d; while (r < 0) r += n; var i0 = Math.floor(r), f = r - i0; return this.b[i0 % n] * (1 - f) + this.b[(i0 + 1) % n] * f; };
  Retardo.prototype.escribe = function (x) { this.b[this.i] = x; this.i = (this.i + 1) % this.b.length; };

  function render(c, sr) {
    sr = sr || 48000;
    var n = Math.ceil(c.dur * sr), y = new Float32Array(n), r = rngDe(c.semilla || 31);
    var evs = c.eventos.slice().sort(function (a, b) { return a.t - b.t; });
    var tubo = new Retardo(Math.ceil(sr / 25)), lp = 0, campana = 0, dcx = 0, dcy = 0;
    var ei = -1, ev = null, sig = 0, f = hz(evs[0].m), slap = 0, llave = 0, T = 0;
    for (var i = 0; i < n; i++) {
      var t = i / sr;
      while (sig < evs.length && evs[sig].t <= t) {                    // la nota siguiente
        ev = evs[sig]; ei = sig; sig++; T = 0;
        if (ev.tipo === 'slap') slap = Math.round(.012 * sr);
        if (ev.tipo === 'llaves') llave = Math.round(.006 * sr);
      }
      if (!ev) { y[i] = 0; continue; }
      var dt = t - ev.t, tipo = ev.tipo || 'normal', v = ev.v == null ? .7 : ev.v, dur = ev.dur || .5;
      // altura (con glisando opcional hacia la nota siguiente) y el largo del tubo: medio periodo, menos la campana
      var m = ev.m + (ev.gliss && evs[ei + 1] ? (evs[ei + 1].m - ev.m) * Math.min(1, dt / dur) : 0);
      var ft = hz(m); f += (ft - f) * (ev.gliss ? 1 : .02);
      tubo.d = Math.max(2, (sr / f * .5 - 1.5) * 1.0115);   // ×1.0115: sin él iba ~20 cents agudo en todo el registro (medido)
      // la respiración de esta nota
      var on = dt < dur ? 1 : Math.max(0, 1 - (dt - dur) / .06), ataque = Math.min(1, dt / (tipo === 'subtono' ? .08 : .025));
      var soplo = 0, ruido = .03, tabla = -.3;                               // STK Clarinet: offset .7, pendiente −.3
      if (tipo === 'normal') soplo = (.55 + .25 * v) * (1 + .03 * Math.sin(2 * Math.PI * 4.6 * dt) * Math.min(1, dt / .5));
      else if (tipo === 'subtono') { soplo = .57 + .04 * v; ruido = .25; }   // con .48-.53 no oscilaba (sólo aire: medido)
      else if (tipo === 'multifonico') { soplo = .95 + .2 * v; tabla = -.22 - .1 * Math.sin(2 * Math.PI * 7.3 * dt); ruido = .1; }
      else if (tipo === 'aire') { soplo = .25; ruido = 1.2; }
      else if (tipo === 'slap') soplo = dt < .03 ? .6 : 0;
      soplo *= on * ataque;
      var P = soplo * (1 + ruido * r());
      if (slap > 0) { P -= v * 1.4 * (slap / (.012 * sr)); slap--; }              // la lengua arranca la caña
      var x = tubo.lee();
      lp = .5 * x + .5 * lp;                                                     // pérdida en el tubo
      var refl = -.95 * lp, pd = refl - P, rt = .7 + tabla * pd; rt = rt > 1 ? 1 : rt < -1 ? -1 : rt;
      var entra = P + pd * rt;
      if (llave > 0) { entra += v * .5 * r() * (llave / (.006 * sr)); llave--; }    // la llave golpea el tubo
      tubo.escribe(entra);
      // campana: radia los agudos (un paso-altos suave) y bloquea la continua
      campana = .6 * campana + .4 * x; var rad = x - .7 * campana;
      dcy = rad - dcx + .995 * dcy; dcx = rad; y[i] = dcy * .6;
      T++;
    }
    return y;
  }
  var api = { render: render, hz: hz };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.Clarinete = api;
})(typeof window !== 'undefined' ? window : globalThis);
