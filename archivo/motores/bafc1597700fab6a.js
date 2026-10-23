/* pajaro.js — un pájaro por modelado físico de la siringe (instrumento 6 de «objetos que cantan»).
 *
 * Mindlin y Laje (The Physics of Birdsong): los labios de la siringe son un oscilador no lineal (van der Pol):
 *     x'' = −ω(t)² x + ω(t) (p(t) − x²) x'
 * p = presión de los sacos aéreos (p < 0: silencio; p chica: casi un silbido puro; p grande: oscilación de relajación,
 * rica en armónicos y áspera); ω = 2π f, la tensión de los músculos siringeos (la altura). La tráquea y el pico filtran:
 * el pájaro abre el pico siguiendo la nota (un resonador que sigue a f), por eso su canto suena a silbido.
 * La siringe tiene DOS lados independientes: un pájaro puede cantar dos notas a la vez (voz 0 y voz 1).
 * Se integra con 4× sobremuestreo (semi-implícito) para que los agudos (hasta ~8 kHz) sean estables.
 *
 * Gestos (cada evento: {t, tipo, m, m2, dur, v, voz, ...}):
 *   'silbido'    glissando de m a m2                   'trino'   sílabas repetidas (rate Hz) entre m y m2
 *   'gorjeo'     frecuencia muy modulada (prof semitonos a rate Hz)   'chip'  caída rápida de una octava (30-60 ms)
 *   'canto'      notas [[dt, m, d]…] con ornamento (Messiaen): cada nota entra con un glissando de 15 ms desde abajo
 *   'ronco'      presión alta y tracto sin afinar: áspero (cuervo, perico)
 *   'carpintero' el pico golpea madera (redoble que acelera; rate de 12 a 26 Hz)     'pico'  el chasquido del pico
 *
 *   Pajaro.render({dur, eventos}, sr) → Float32Array
 */
(function (global) {
  'use strict';
  var hz = function (m) { return 440 * Math.pow(2, (m - 69) / 12); };
  function rngDe(s) { var h = s >>> 0 || 1; return function () { h ^= h << 13; h >>>= 0; h ^= h >> 17; h ^= h << 5; h >>>= 0; return h / 4294967296; }; }
  function Reso(sr) { this.sr = sr; this.y1 = 0; this.y2 = 0; }
  Reso.prototype.tick = function (x, f, q) {
    var w = 2 * Math.PI * Math.min(f, this.sr * .45) / this.sr, R = Math.exp(-Math.PI * f / q / this.sr);
    var y = 2 * R * Math.cos(w) * this.y1 - R * R * this.y2 + (1 - R) * x; this.y2 = this.y1; this.y1 = y; return y;
  };

  // el control de un gesto: [f (Hz), p (presión), ronco (0-1)] en el tiempo u ∈ [0, dur] desde su inicio
  function control(ev, u) {
    var d = ev.dur || .3, v = ev.v == null ? .7 : ev.v, f1 = hz(ev.m), f2 = hz(ev.m2 == null ? ev.m : ev.m2), x = u / d;
    var env = Math.min(1, u / .012) * Math.min(1, (d - u) / .02);        // los labios se abren y se cierran
    var p = .05 + .25 * v;
    switch (ev.tipo) {
      case 'silbido': return [f1 * Math.pow(f2 / f1, x), p * env, 0];
      case 'trino': {
        var rate = ev.rate || 18, fase = (u * rate) % 1;                  // cada sílaba: sube y la presión late
        return [f1 * Math.pow(f2 / f1, fase), p * env * (fase < .7 ? 1 : -1.5), 0];
      }
      case 'gorjeo': return [f1 * Math.pow(2, (ev.prof || 4) / 12 * Math.sin(2 * Math.PI * (ev.rate || 28) * u)), p * env, 0];
      case 'chip': return [f1 * Math.pow(.5, x), (p + .1) * env, 0];
      case 'ronco': return [f1 * (1 + .03 * Math.sin(2 * Math.PI * 9 * u)), (1.2 + .8 * v) * env, 1];
      case 'canto': {
        var notas = ev.notas, k = 0; while (k + 1 < notas.length && notas[k + 1][0] <= u) k++;
        var nk = notas[k], un = u - nk[0], fk = hz(nk[1]), orn = Math.min(1, un / .015);
        var ok = un < nk[2] ? 1 : -1.2;                                   // entre notas, la presión cae
        return [fk * Math.pow(2, -(1 - orn) * 3 / 12), p * env * ok * Math.min(1, un / .006), 0];
      }
    }
    return [f1, -.5, 0];
  }

  function render(c, sr) {
    sr = sr || 48000;
    var n = Math.ceil(c.dur * sr), y = new Float32Array(n), r = rngDe(c.semilla || 61), OS = 4, dt = 1 / (OS * sr);
    var cantos = [[], []], golpes = [];
    c.eventos.forEach(function (ev) {
      if (ev.tipo === 'carpintero') {                                     // redoble: la tasa sube (12 → 26 Hz) y se apaga
        var tt = 0, d = ev.dur || 1.5;
        while (tt < d) { var rate = 12 + 14 * (tt / d); golpes.push([ev.t + tt, (ev.v || .8) * (1 - .5 * tt / d), 'madera']); tt += 1 / rate; }
      } else if (ev.tipo === 'pico') { golpes.push([ev.t, ev.v || .7, 'pico'], [ev.t + .009, (ev.v || .7) * .6, 'pico']); }
      else cantos[ev.voz || 0].push(ev);
    });
    cantos.forEach(function (l) { l.sort(function (a, b) { return a.t - b.t; }); });
    golpes.sort(function (a, b) { return a[0] - b[0]; });
    var V = [0, 1].map(function () { return { x: .01, v: 0, ei: 0, pico: new Reso(sr), traq: new Reso(sr), amp: 0 }; });
    var madera = [[820, 25, 1], [1930, 30, .6], [3150, 35, .4], [4700, 40, .25]].map(function (m) { return { f: m[0], q: m[1], g: m[2], r: new Reso(sr) }; });
    var gi = 0, chispa = 0, cv = 0, ctipo = '';
    for (var i = 0; i < n; i++) {
      var t = i / sr, s = 0;
      for (var k = 0; k < 2; k++) {                                       // los dos lados de la siringe
        var Vk = V[k], l = cantos[k];
        while (Vk.ei + 1 < l.length && l[Vk.ei + 1].t <= t) Vk.ei++;
        var ev = l[Vk.ei], ctl = ev && t >= ev.t && t < ev.t + (ev.dur || .3) ? control(ev, t - ev.t) : [Vk.f || 2000, -.6, 0];
        var f = ctl[0], p = ctl[1], w = 2 * Math.PI * f; Vk.f = f;
        for (var o = 0; o < OS; o++) {                                   // van der Pol, semi-implícito, 4× sobremuestreo
          Vk.v += dt * (-w * w * Vk.x + w * (p - Vk.x * Vk.x) * Vk.v); Vk.x += dt * Vk.v;
        }
        if (Math.abs(Vk.x) < 1e-6 && p > 0) Vk.x = 1e-3 * (r() - .5);       // una semilla de movimiento para arrancar
        var src = Vk.v / w;                                               // la presión que sale de los labios
        // tráquea y pico: con canto, el pico sigue a la nota (silbido puro); con ronco, el tracto no se afina (áspero)
        // nivel: el resonador del pico pierde 13 dB de Mi5 a La7 (medido) → × (f/1000)^0.9; el ronco, ×0.25 (sonaba 8 veces más)
        var out = ctl[2] > 0 ? (Vk.traq.tick(src, 1450, 2.5) * 2 + Vk.pico.tick(src, 2900, 3)) * .25 : Vk.pico.tick(src, f, 5) * 2.2 * Math.pow(f / 1000, .9);
        s += src * (k ? .8 : 1);
      }
      // el pico contra la madera (carpintero) y el chasquido
      while (gi < golpes.length && golpes[gi][0] <= t) { chispa = Math.round(.0015 * sr); cv = golpes[gi][1]; ctipo = golpes[gi][2]; gi++; }
      var g = 0; if (chispa > 0) { g = (r() * 2 - 1) * cv; chispa--; }
      var mad = 0; for (k = 0; k < madera.length; k++) mad += madera[k].r.tick(ctipo === 'madera' ? g : 0, madera[k].f, madera[k].q) * madera[k].g;
      y[i] = s * .6 + mad * 30 + (ctipo === 'pico' ? g * 2.5 : 0);   // ×30 y ×2.5: con ×6 y ×.5 el carpintero quedaba 15 dB bajo los cantos (medido)
    }
    return y;
  }
  var api = { render: render, hz: hz };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.Pajaro = api;
})(typeof window !== 'undefined' ? window : globalThis);
