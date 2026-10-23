/* agua.js — percusión de agua por física de burbujas (instrumento 5 de «objetos que cantan»).
 *
 * El sonido del agua es el de sus burbujas (van den Doel 2005, «Physically based models for liquid sounds»): una burbuja
 * de radio r resuena a f0 ≈ 3/r Hz (Minnaert), se apaga con d = 0.13/r + 0.0072 r^(−3/2) y sube de tono mientras se
 * apaga (σ = ε·d): s(t) = a · sin(2π f0 (t + σ t²/2)) · e^(−d t). Todo lo demás son nubes de burbujas.
 *
 *   'gota'     una burbuja afinada a la nota m, con el golpecito de la gota (una melodía de gotas)
 *   'palo'     palo de lluvia de agua: una cascada de gotas que se va agotando, resonando en el tubo
 *   'guiro'    güiro de agua: cada estría del raspado suelta una burbuja (trazo de largo dur, estrías n)
 *   'chorro'   agua vertida en un vaso: nube de burbujas + la columna de aire que se acorta (el tono sube)
 *   'burbujeo' burbujas grandes y graves, espaciadas
 *   'ola'      una ola: crece (rumor grave cuyo filtro se abre), rompe (espuma: miles de burbujas de todos los tamaños
 *              y un golpe de ruido ancho) y se retira (siseo de burbujas chiquitas que se apagan)
 *
 *   Agua.render({dur, eventos: [{t, tipo, m, v, dur, n, ...}]}, sr) → Float32Array
 */
(function (global) {
  'use strict';
  var hz = function (m) { return 440 * Math.pow(2, (m - 69) / 12); };
  function rngDe(s) { var h = s >>> 0 || 1; return function () { h ^= h << 13; h >>>= 0; h ^= h >> 17; h ^= h << 5; h >>>= 0; return h / 4294967296; }; }

  // una burbuja a partir de su frecuencia (Hz): radio, amortiguamiento y subida de tono de van den Doel
  function Burbuja(t0, f0, a, eps) {
    var r = 3 / f0;                                                        // metros
    this.t0 = t0; this.f0 = f0; this.a = a;
    this.d = .13 / r + .0072 * Math.pow(r, -1.5); this.sigma = (eps == null ? .1 : eps) * this.d;
    this.fin = t0 + 7 / this.d;                                            // ~ −60 dB
  }
  Burbuja.prototype.valor = function (t) {
    var u = t - this.t0; if (u < 0) return 0;
    return this.a * Math.sin(2 * Math.PI * this.f0 * (u + this.sigma * u * u / 2)) * Math.exp(-this.d * u);
  };
  // resonador de dos polos (el tubo del palo, la columna de aire del vaso)
  function Reso(sr) { this.sr = sr; this.y1 = 0; this.y2 = 0; }
  Reso.prototype.tick = function (x, f, q) {
    var w = 2 * Math.PI * Math.min(f, this.sr * .45) / this.sr, R = Math.exp(-Math.PI * f / q / this.sr);
    var y = 2 * R * Math.cos(w) * this.y1 - R * R * this.y2 + (1 - R) * x; this.y2 = this.y1; this.y1 = y; return y;
  };

  function render(c, sr) {
    sr = sr || 48000;
    var n = Math.ceil(c.dur * sr), y = new Float32Array(n), r = rngDe(c.semilla || 41);
    var burbujas = [], ruidos = [], vasos = [], tubos = [], olas = [];
    // 1. cada evento se vuelve burbujas (y ruidos de impacto); los continuos (chorro, palo) dejan su resonador
    c.eventos.forEach(function (ev) {
      var v = ev.v == null ? .7 : ev.v, t = ev.t, d = ev.dur || 1, tipo = ev.tipo || 'gota';
      if (tipo === 'gota') {
        // la burbuja sube de tono al apagarse: su altura promedio (cruces por cero pesados por energía) queda ≈ 1000·ε
        // cents arriba de donde arranca, en todo el registro (calibrado: +120 c con ε = .12). Arranca abajo para que el
        // centro del «plop» caiga en la nota
        var eps = ev.eps == null ? .12 : ev.eps;
        burbujas.push(new Burbuja(t + .002, hz(ev.m) / Math.pow(2, 1000 * eps / 1200), v * 3.2, eps));
        ruidos.push([t, .0015, v * .5, 6000]);                               // el golpecito de la gota en la superficie
      } else if (tipo === 'palo') {
        // la cascada: la tasa sube rápido y se va agotando (las gotas que quedan arriba del palo son cada vez menos)
        var base = ev.m ? hz(ev.m) : 1800, tasa = ev.tasa || 260, tt = 0;
        while (tt < d) {
          var lam = tasa * Math.min(1, tt / .15) * Math.exp(-tt / (d * .45)) + 4;
          tt += -Math.log(1 - r() * .999) / lam;
          var f = base * Math.pow(2, (r() - .5) * 2.4);                      // gotas de tamaños variados (±1.2 octavas)
          burbujas.push(new Burbuja(t + tt, f, v * (.03 + .045 * r()) * Math.pow(base / f, .5), .08 + .1 * r()));
          if (r() < .3) ruidos.push([t + tt, .0006, v * .08, 4500]);         // las gotas chocan con las espinas del tubo
        }
        tubos.push({ t0: t, t1: t + d + .4, f: [380, 820, 1650], q: [5, 7, 9] });
      } else if (tipo === 'guiro') {
        // el raspado: n estrías repartidas en el trazo (un poco irregulares), cada una suelta una burbuja chiquita
        var est = ev.n || 18, base2 = ev.m ? hz(ev.m) : 1400;
        for (var k = 0; k < est; k++) {
          var tk = t + d * (k + .3 * (r() - .5)) / est, fk = base2 * (1 + .25 * (k / est) * (ev.sube ? 1 : -1)) * Math.pow(2, (r() - .5) * .3);
          burbujas.push(new Burbuja(tk, fk, v * .45, .2));
          ruidos.push([tk, .0012, v * .18, 3200]);                           // la estría
        }
      } else if (tipo === 'chorro') {
        // nube de burbujas (~300/s) y la columna de aire del vaso: de 300 Hz a 3 kHz mientras se llena
        var tt2 = 0, f0c = ev.desde || 300, f1c = ev.hasta || 3000;
        while (tt2 < d) {
          tt2 += -Math.log(1 - r() * .999) / (ev.tasa || 320);
          var fc = f0c * Math.pow(f1c / f0c, tt2 / d) * Math.pow(2, (r() - .5) * 1.6);
          burbujas.push(new Burbuja(t + tt2, fc * 1.3, v * (.12 + .2 * r()), .1));
        }
        vasos.push({ t0: t, t1: t + d, f0: f0c, f1: f1c, v: v });
      } else if (tipo === 'ola') {
        var rompe = t + d * .4, tt4 = 0;
        while (tt4 < d) {                                                    // la espuma: la tasa estalla al romper y se va
          var u4 = t + tt4 - rompe, lam4 = u4 < 0 ? 40 * Math.exp(u4 / (d * .12)) : 2600 * Math.exp(-u4 / (d * .22)) + 30;
          tt4 += -Math.log(1 - r() * .999) / lam4;
          var chica = u4 > d * .15 ? 1 : 0;                                  // al retirarse quedan las burbujas chiquitas (siseo)
          var f4 = (chica ? 2500 : 600) * Math.pow(2, (r() - .5) * (chica ? 2 : 3.5));
          burbujas.push(new Burbuja(t + tt4, f4, v * (.12 + .2 * r()) * (u4 < 0 ? .5 : 1), .15));
        }
        olas.push({ t0: t, t1: t + d, rompe: rompe, v: v, lp: 0, lp2: 0 });
      } else if (tipo === 'burbujeo') {
        var tt3 = 0;
        while (tt3 < d) { tt3 += -Math.log(1 - r() * .999) / (ev.tasa || 7); burbujas.push(new Burbuja(t + tt3, 160 + 420 * r(), v * (.5 + .5 * r()), .25)); }
      }
    });
    burbujas.sort(function (a, b) { return a.t0 - b.t0; });
    // 2. sumar en el tiempo (sólo las burbujas vivas)
    var vivas = [], bi = 0, reso = [new Reso(sr), new Reso(sr), new Reso(sr)], vasoR = new Reso(sr);
    for (var i = 0; i < n; i++) {
      var t = i / sr;
      while (bi < burbujas.length && burbujas[bi].t0 <= t) vivas.push(burbujas[bi++]);
      var s = 0;
      for (var k = vivas.length - 1; k >= 0; k--) { if (t > vivas[k].fin) { vivas.splice(k, 1); continue; } s += vivas[k].valor(t); }
      var ns = 0;
      for (k = 0; k < ruidos.length; k++) { var q = ruidos[k]; if (t >= q[0] && t < q[0] + q[1] * 4) ns += (r() * 2 - 1) * q[2] * Math.exp(-(t - q[0]) / q[1]); }
      var tubo = 0;
      for (k = 0; k < tubos.length; k++) if (t >= tubos[k].t0 && t < tubos[k].t1) for (var j = 0; j < 3; j++) tubo += reso[j].tick(s, tubos[k].f[j], tubos[k].q[j]) * .28;
      var vaso = 0;
      for (k = 0; k < vasos.length; k++) { var V = vasos[k]; if (t >= V.t0 && t < V.t1 + .3) { var u = Math.min(1, (t - V.t0) / (V.t1 - V.t0)); vaso += vasoR.tick(s + (r() * 2 - 1) * .02 * V.v, V.f0 * Math.pow(V.f1 / V.f0, u), 12) * 3.5; } }
      var mar = 0;
      for (k = 0; k < olas.length; k++) {                                   // el cuerpo de la ola: ruido filtrado
        var O = olas[k]; if (t < O.t0 || t > O.t1 + .5) continue;
        var u5 = t - O.rompe, crece = u5 < 0 ? Math.pow(Math.max(0, (t - O.t0) / (O.rompe - O.t0)), 1.3) : Math.exp(-u5 / ((O.t1 - O.rompe) * .35));
        var corte = u5 < 0 ? 150 + 750 * crece : 900 * Math.exp(-u5 / 1.2) + 250, a5 = 1 - Math.exp(-2 * Math.PI * corte / sr);
        O.lp += a5 * ((r() * 2 - 1) - O.lp); O.lp2 += a5 * (O.lp - O.lp2);
        var golpe = u5 >= 0 && u5 < .25 ? (r() * 2 - 1) * Math.exp(-u5 / .06) * .5 : 0;   // el golpe ancho al romper
        mar += (O.lp2 * 5 * crece + golpe * 2) * O.v;
      }
      y[i] = s + ns + tubo + vaso + mar;
    }
    return y;
  }
  var api = { render: render, hz: hz, Burbuja: Burbuja };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.Agua = api;
})(typeof window !== 'undefined' ? window : globalThis);
