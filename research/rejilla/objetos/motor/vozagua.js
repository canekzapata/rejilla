/* vozagua.js — el watervoicephone: agua que habla y canta (instrumento 7 de «objetos que cantan»).
 *
 * Una vocal es un sonido con tres resonancias marcadas (formantes) y una nube de burbujas es un montón de resonancias:
 * si el tamaño de cada burbuja se elige para que su frecuencia caiga en un formante, el agua dice la vocal. Las palabras
 * pasan a fonemas con el G2P de difonos; cada fonema se vuelve agua:
 *   vocales (a e i o u, y semivocales)  burbujas en F1, F2, F3
 *   s f x (fricativas)                   burbujas diminutas, agudas y densas (sin altura)
 *   p t k b d g (oclusivas)              un salpicón: el golpe de una gota y una burbuja en el F2 de la vocal siguiente
 *   m n ñ (nasales) · l r rr             burbujas graves · un golpe de lengua · un trino (la rr late a 26 Hz)
 * Modos:
 *   'susurro'  las burbujas nacen al azar (Poisson): el agua susurra, sin altura
 *   'canto'    las burbujas sonoras nacen en los pulsos de la nota (f0): el tren de pulsos da la altura, las burbujas la vocal
 *   'gargara'  el canto con interrupciones al azar (12-25 Hz) y gorgoteo grave
 * voz ∈ [0, 1]: 0 = agua cualquiera (frecuencias al azar), 1 = agua que habla (frecuencias en los formantes): el agua aprende.
 * Dos voces: cada evento es una palabra con su nota; dos líneas de eventos suenan juntas (como los dos lados de la siringe).
 * Dos vocales a la vez: con doble: 'i' (por ejemplo) cada pulso suelta también las burbujas de esa otra vocal.
 *
 *   VozAgua.render({dur, eventos: [{t, dur, texto, nota, modo, voz, doble, v}]}, sr) → Float32Array
 */
(function (global) {
  'use strict';
  var A = typeof require !== 'undefined' ? require('./agua.js') : global.Agua;
  var G2P = typeof require !== 'undefined' ? require('../vendor/difonos-g2p/g2p.js') : global.DifonosG2P;
  var hz = function (m) { return 440 * Math.pow(2, (m - 69) / 12); };
  function rngDe(s) { var h = s >>> 0 || 1; return function () { h ^= h << 13; h >>>= 0; h ^= h >> 17; h ^= h << 5; h >>>= 0; return h / 4294967296; }; }

  var FORMANTES = { a: [800, 1200, 2500], e: [450, 1900, 2550], i: [300, 2300, 3000], o: [500, 880, 2400], u: [330, 780, 2300], y: [300, 2200, 2900],
    AA: [730,1090,2440], AE: [660,1720,2410], AH: [520,1300,2500], AO: [570,840,2410], EH: [530,1840,2480], ER: [490,1350,1690],
    IH: [390,1990,2550], IY: [270,2290,3010], UH: [440,1020,2240], UW: [300,870,2240] };
  var CLASE = function (f) {
    if (FORMANTES[f]) return 'vocal';
    if ('sfx'.indexOf(f) >= 0 || ['F','HH','S','SH','TH','DH','V','Z','ZH'].indexOf(f) >= 0) return 'fricativa';
    if ('ptkbdgC'.indexOf(f) >= 0 || ['B','D','G','JH','K','P','T','CH'].indexOf(f) >= 0) return 'oclusiva';
    if ('mnN'.indexOf(f) >= 0 || ['M','N','NG'].indexOf(f) >= 0) return 'nasal';
    if (f === 'R') return 'trino'; if (f === 'r') return 'golpe';
    if (f === 'l' || f === 'L' || f === 'R_EN' || f === 'W' || f === 'Y') return 'liquida';
    return 'fricativa';
  };
  var DUR = { fricativa: .085, oclusiva: .05, nasal: .07, trino: .12, golpe: .035, liquida: .06 };
  var BANDA = { s: [4500, 8000], f: [2500, 6000], x: [1200, 3200], C: [3000, 6500], S: [4500,8000], F: [2500,6000], SH: [2200,6500], TH: [1800,6200], DH: [1000,4800], HH: [800,5000], V: [1000,4200], Z: [3500,7500], ZH: [1800,5500], CH: [1800,6500] };

  // una palabra → segmentos [{t0, t1, f, clase, F (formantes), sig (formantes de la vocal siguiente)}]
  function segmentos(ev) {
    var fon = (ev.fonemas || G2P.frase(ev.texto)).filter(function (f) { return f !== '#'; }), cons = 0, nv = 0;
    fon.forEach(function (f) { if (CLASE(f) === 'vocal') nv++; else cons += DUR[CLASE(f)]; });
    var dv = Math.max(.06, (ev.dur - cons) / Math.max(1, nv)), t = ev.t, out = [];
    fon.forEach(function (f, i) {
      var cl = CLASE(f), d = cl === 'vocal' ? dv : DUR[cl], sig = null;
      for (var k = i + 1; k < fon.length; k++) if (FORMANTES[fon[k]]) { sig = FORMANTES[fon[k]]; break; }
    out.push({ t0: t, t1: t + d, f: f, clase: cl, F: FORMANTES[f] || null, sig: sig || FORMANTES.a }); t += d;
    });
    return out;
  }

  function render(c, sr) {
    sr = sr || 48000;
    var n = Math.ceil(c.dur * sr), y = new Float32Array(n), r = rngDe(c.semilla || 71), burbujas = [], golpes = [];
    var EPS = .1, CORR = Math.pow(2, -1000 * EPS / 1200);                  // las burbujas suben ~1000·ε cents: arrancan abajo
    var nace = function (t, f, a, eps) { burbujas.push(new A.Burbuja(t, f * CORR, a, eps == null ? EPS : eps)); };
    // la burbuja que habla: una burbuja de verdad apenas se amortigua (a 800 Hz suena con ~10 Hz de ancho) y en un tren
    // de pulsos sólo resuena si un armónico le cae justo encima: la vocal se perdía (medido: la «i» era puro 294 Hz).
    // La garganta se amortigua con el ancho de un formante (B Hz): d = π B; la amplitud × d/(π·100) iguala los picos
    var habla = function (t, f, a, B) { var q = new A.Burbuja(t, f * CORR, a * B / 100, EPS); q.d = Math.PI * B; q.sigma = EPS * q.d; q.fin = t + 7 / q.d; burbujas.push(q); };
    var ANCHO = [90, 110, 160];
    c.eventos.forEach(function (ev, ie) {
      var modo = ev.modo || 'canto', v = ev.v == null ? .7 : ev.v, voz = ev.voz == null ? 1 : ev.voz, f0 = hz(ev.nota || 57);
      var doble = ev.doble ? FORMANTES[ev.doble] : null, segs = segmentos(ev), ant = null;
      // la gárgara: una compuerta al azar (abierta/cerrada cada 40-80 ms)
      var compuerta = function (t) { var k = Math.floor((t - ev.t) * 18 + ie * 7.3); var h = Math.sin(k * 12.9898 + ie) * 43758.5453; return (h - Math.floor(h)) > .32; };
      // las frecuencias que «dice» el agua: con voz → en el formante (±3 %); sin voz → en cualquier parte del agua
      var elige = function (F) { return r() < voz ? F * (1 + (r() - .5) * .06) : 250 * Math.pow(16, r()); };
      segs.forEach(function (s) {
        var F = s.F;
        if (s.clase === 'vocal' && ant && ant.F) {}                        // (la transición la hace el muestreo de abajo)
        if (s.clase === 'vocal' || s.clase === 'nasal' || s.clase === 'liquida' || s.clase === 'trino' || s.clase === 'golpe') {
          var Fs = s.clase === 'vocal' ? F : s.clase === 'nasal' ? [280, 1200, 2400] : s.sig, pesos = s.clase === 'vocal' ? [1, .55, .3] : [.8, .25, .12];
          if (modo === 'susurro') {                                        // burbujas al azar, sin altura
            for (var t = s.t0; t < s.t1;) { t += -Math.log(1 - r() * .999) / 650; var k = r() < .5 ? 0 : r() < .6 ? 1 : 2; nace(t, elige(Fs[k]), v * pesos[k] * .11); }   // ×.11: con ×.5 el susurro sonaba 13 dB arriba del canto (medido)
          } else {                                                         // canto: una ráfaga de burbujas en cada pulso de la nota
            for (var tp = s.t0; tp < s.t1; tp += 1 / f0 * (1 + (r() - .5) * .02)) {
              if (s.clase === 'trino' && Math.sin(2 * Math.PI * 26 * (tp - s.t0)) < 0) continue;     // la rr late
              if (modo === 'gargara' && !compuerta(tp)) continue;
              var u = Math.min(1, (tp - s.t0) / .04), Fm = ant && ant.F && s.clase === 'vocal' ? Fs.map(function (q, j) { return ant.F[j] + (q - ant.F[j]) * u; }) : Fs;
              // cada pulso excita las MISMAS resonancias (como la glotis): si cada pulso elegía frecuencias un poco distintas
              // (±3 %), el tren no se repetía y no había altura (medido: la «a» daba 814 Hz y periodicidad .44)
              for (var j = 0; j < 3; j++) habla(tp, r() < voz ? Fm[j] : 250 * Math.pow(16, r()), v * pesos[j] * .32, ANCHO[j]);
              // y una burbuja grande en la fundamental (el zumbido de la glotis): en la «o» y la «u», con F1 bajo, la energía
              // caía toda en el armónico 2 o 3 y la altura se iba ahí (medido)
              if (s.clase === 'vocal' && r() < voz) habla(tp, f0, v * .1, 60);
              if (doble && s.clase === 'vocal') for (j = 0; j < 3; j++) habla(tp, r() < voz ? doble[j] : 250 * Math.pow(16, r()), v * [.6, .9, .5][j] * .3, ANCHO[j]);   // la otra vocal, a la vez: con su F2 al frente (el F2 es el que dice qué vocal es; con los pesos normales la «e» bajo la «o» no se veía)
            }
            if (modo === 'gargara') for (var tg = s.t0; tg < s.t1;) { tg += -Math.log(1 - r() * .999) / 22; nace(tg, 140 + 260 * r(), v * .25, .25); }
          }
          if (s.clase === 'golpe') golpes.push([s.t0, v * .25]);
        } else if (s.clase === 'fricativa') {                              // s f j: burbujas diminutas y densas
          var b = BANDA[s.f] || [2500, 6000];
          for (var tf = s.t0; tf < s.t1;) { tf += -Math.log(1 - r() * .999) / 1400; nace(tf, b[0] * Math.pow(b[1] / b[0], r()), v * .09, .05); }
        } else if (s.clase === 'oclusiva') {                               // salpicón: el golpe y una burbuja en el F2 que viene
          golpes.push([s.t0 + s.t1 * 0 + (s.t1 - s.t0) * .7, v * .45]); nace(s.t1 - .005, elige(s.sig[1]), v * .5, .15);
          if (s.f === 'C') for (var tc = s.t0; tc < s.t1; tc += .002) nace(tc, 3500 + 3000 * r(), v * .08, .05);
        }
        ant = s;
      });
    });
    burbujas.sort(function (a, b) { return a.t0 - b.t0; }); golpes.sort(function (a, b) { return a[0] - b[0]; });
    var vivas = [], bi = 0, gi = 0, chispa = 0, gv = 0, hp = 0;
    for (var i = 0; i < n; i++) {
      var t = i / sr, s = 0;
      while (bi < burbujas.length && burbujas[bi].t0 <= t) vivas.push(burbujas[bi++]);
      for (var k = vivas.length - 1; k >= 0; k--) { if (t > vivas[k].fin) { vivas.splice(k, 1); continue; } s += vivas[k].valor(t); }
      while (gi < golpes.length && golpes[gi][0] <= t) { chispa = Math.round(.002 * sr); gv = golpes[gi][1]; gi++; }
      var g = 0; if (chispa > 0) { g = (r() * 2 - 1) * gv * (chispa / (.002 * sr)); chispa--; }
      hp = .9 * hp + .1 * g; y[i] = s + (g - hp);                          // el golpe de la gota, sin graves
    }
    return y;
  }
  var api = { render: render, FORMANTES: FORMANTES, segmentos: segmentos };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.VozAgua = api;
})(typeof window !== 'undefined' ? window : globalThis);
