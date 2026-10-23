/* cancion.js — «epístrofe» (loop 08 de la rejilla). Partitura e instrumentos en Web Audio, por pistas.
 *
 * Tres caminantes recorren el mismo laberinto del Tonnetz (24 tríadas; cada paso mueve una sola voz) a distintas
 * velocidades: el bajo (¾ de paso por compás), el piano preparado (1½) y las voces (sobre la tríada del bajo).
 * El muro es la suma de los espectros de las tríadas del bajo y del piano: politonal hasta que coinciden.
 *
 *   Cancion.pista(n)(ctx, destino, banco, en)   en(t, f): crear los nodos de un evento justo antes de sonar
 *   Cancion.partitura()  Cancion.camino()  Cancion.DURACION …
 */
(function (global) {
  'use strict';
  var BPM = 108, T = 240 / BPM, S16 = T / 16, COMPASES = 64, COLA = 4;
  var DURACION = COMPASES * T + COLA, SWING = .62;
  var hz = function (m) { return 440 * Math.pow(2, (m - 69) / 12); };

  function rngDe(nombre) {
    var h = 2166136261; nombre = 'epistrofe·' + nombre;
    for (var i = 0; i < nombre.length; i++) { h ^= nombre.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
    return function () { h = (h + 0x6D2B79F5) >>> 0; var t = h; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }

  /* ── el laberinto: DFS sembrado sobre el Tonnetz desde La menor. El recorrido avanza, choca y regresa (47 pasos) ── */
  var vecinos = function (t) {                       // P, R, L: cada uno mueve una sola voz
    var r = t[0];
    return t[1] ? [[r, false], [(r + 9) % 12, false], [(r + 4) % 12, false]] : [[r, true], [(r + 3) % 12, true], [(r + 8) % 12, true]];
  };
  var CAMINO = (function () {
    var rng = rngDe('laberinto'), vis = {}, cam = [], clave = function (t) { return t[0] + (t[1] ? 'M' : 'm'); };
    (function visita(t) {
      vis[clave(t)] = 1; cam.push(t);
      var vs = vecinos(t).slice();
      for (var i = vs.length - 1; i > 0; i--) { var j = Math.floor(rng() * (i + 1)), x = vs[i]; vs[i] = vs[j]; vs[j] = x; }
      vs.forEach(function (v) { if (!vis[clave(v)]) { visita(v); cam.push(t); } });
    })([9, false]);
    return cam;
  })();
  var N = CAMINO.length - 1;                          // 46: el último paso es La menor otra vez (casa)
  // caminantes: índice en el recorrido según el tiempo (en compases)
  var pasoBajo = function (b) { return Math.min(N, Math.floor(b * N / 62)); };
  var pasoPiano = function (b) { var w = Math.floor(b * 1.5) % (2 * N); return Math.min(N, w <= N ? w : 2 * N - w); };
  var triada = function (i) { return CAMINO[i]; };
  var tonos = function (t) { return [t[0], (t[0] + (t[1] ? 4 : 3)) % 12, (t[0] + 7) % 12]; };
  var nombre = function (t) { return ['Do', 'Do♯', 'Re', 'Mi♭', 'Mi', 'Fa', 'Fa♯', 'Sol', 'La♭', 'La', 'Si♭', 'Si'][t[0]] + (t[1] ? '' : 'm'); };
  // grado del arpegio de la tríada a partir de una base: 0 = el primer tono ≥ base, 1 el siguiente…
  function notaDe(t, grado, base) {
    var pcs = tonos(t), arp = [];
    for (var m = base - 24; m <= base + 30; m++) if (pcs.indexOf(((m % 12) + 12) % 12) >= 0) arp.push(m);
    var i0 = 0; while (arp[i0] < base) i0++;
    return arp[Math.max(0, Math.min(arp.length - 1, i0 + grado))];
  }

  /* ── curvas por instrumento (tejer, no cortar) ── */
  var CURVAS = {
    muro:   [[0, .55], [7, 1], [8, .62], [23, .62], [24, .9], [31, .9], [32, 1], [39, 1], [40, .62], [47, .66], [48, .92], [55, .95], [56, .75], [63, .5], [64, 0]],
    fuzz:   [[0, .15], [8, .1], [24, .3], [31.5, .35], [32, .8], [39, .9], [40, .15], [48, .35], [56, .1], [64, 0]],
    delta:  [[0, 0], [31, 0], [32, .003], [38, .009], [40, 0], [64, 0]],
    bombeo: [[0, 0], [23.5, 0], [24, .7], [31.8, .7], [32, 0], [47.5, 0], [48, .75], [55.8, .75], [56, .2], [64, 0]],
    piano:  [[0, .35], [8, .5], [24, .6], [32, 1], [40, .7], [56, .5], [64, .2]],
    bajo:   [[0, 0], [7.9, 0], [8, 1], [31.9, 1], [32, 0], [39.9, 0], [40, 1], [60, 1], [63, .4], [64, 0]],
    kit:    [[0, 0], [7.9, 0], [8, 1], [31.9, 1], [32, 0], [39.9, 0], [40, 1], [56, .8], [62, .4], [64, 0]]
  };
  function curva(nombre, b) {
    var K = CURVAS[nombre];
    if (b <= K[0][0]) return K[0][1];
    for (var i = 1; i < K.length; i++) if (b <= K[i][0]) {
      var u = (b - K[i - 1][0]) / (K[i][0] - K[i - 1][0]); u = u * u * (3 - 2 * u);
      return K[i - 1][1] + (K[i][1] - K[i - 1][1]) * u;
    }
    return K[K.length - 1][1];
  }
  function U(ctx) {
    return {
      osc: function (tipo, f) { var o = ctx.createOscillator(); o.type = tipo; o.frequency.value = f; return o; },
      gain: function (v) { var g = ctx.createGain(); g.gain.value = v == null ? 1 : v; return g; },
      filtro: function (tipo, f, q) { var b = ctx.createBiquadFilter(); b.type = tipo; b.frequency.value = f; if (q != null) b.Q.value = q; return b; },
      paneo: function (p) { var x = ctx.createStereoPanner(); x.pan.value = p; return x; },
      ruido: function (seg, nombre) {
        var r = rngDe(nombre), n = Math.floor(seg * ctx.sampleRate), b = ctx.createBuffer(1, n, ctx.sampleRate), d = b.getChannelData(0);
        for (var i = 0; i < n; i++) d[i] = r() * 2 - 1; return b;
      },
      saturador: function (k) {
        var w = ctx.createWaveShaper(), c = new Float32Array(2048);
        for (var i = 0; i < 2048; i++) { var x = i / 1023.5 - 1; c[i] = Math.tanh(k * x) / Math.tanh(k); }
        w.curve = c; w.oversample = '2x'; return w;
      }
    };
  }
  var swing = function (paso) { return paso % 2 ? (SWING - .5) * 2 * S16 : 0; };

  /* ── 1. el muro: los espectros de dos tríadas (bajo + piano), estirados (Murail), con fuzz (Romitelli) y bombeo ── */
  function espectro(t, delta) {
    var raiz = 43 + ((t[0] - 43 % 12) + 24) % 12, fr = hz(raiz), parc = [];
    var M = t[1], f0 = M ? fr / 4 : fr / 10;
    var acorde = M ? [4, 5, 6, 8, 10, 12, 16, 20, 24] : [10, 12, 15, 20, 24, 30, 40];
    var entre = M ? [7, 9, 11, 13, 14, 15, 18, 22] : [11, 13, 17, 19, 21, 23, 27, 33];
    acorde.forEach(function (n) { parc.push([f0 * Math.pow(n, 1 + delta), .9 / Math.sqrt(n / acorde[0])]); });
    entre.forEach(function (n) { parc.push([f0 * Math.pow(n, 1 + delta), .32 / Math.sqrt(n / acorde[0])]); });
    return parc.filter(function (p) { return p[0] < 4600; });
  }
  function muro(ctx, dest, banco, en) {
    var u = U(ctx), sal = u.gain(1); sal.connect(dest);
    var limpio = u.gain(1), sucio = u.gain(0), suma = u.gain(.25), bomba = u.gain(1);   // .25: con .05 el muro quedaba a −48 dB y el fuzz no mordía (medido)
    var drive = u.gain(9), fz = u.saturador(3.5), hp = u.filtro('highpass', 110, .7), lp = u.filtro('lowpass', 3800, .8);
    suma.connect(limpio).connect(bomba); suma.connect(drive).connect(fz).connect(hp).connect(lp).connect(sucio).connect(bomba);
    bomba.connect(sal);
    for (var b = 0; b < COMPASES; b++) {                 // mezcla limpio/sucio y nivel por compás (suave)
      var fz_ = curva('fuzz', b), m = curva('muro', b), t = b * T;
      limpio.gain.setTargetAtTime(m * (1 - .6 * fz_), t, .4); sucio.gain.setTargetAtTime(m * fz_ * .45, t, .4);
      var bo = curva('bombeo', b + .5);
      if (bo > .01) for (var s = 0; s < 16; s++) {         // el muro bombea en dieciseisavos (funk)
        var abierto = [1, .25, .6, .3, .9, .25, .55, .35, 1, .25, .65, .3, .85, .3, .5, .4][s];
        bomba.gain.setTargetAtTime(1 - bo * (1 - abierto), t + s * S16, .012);
      } else bomba.gain.setTargetAtTime(1, t, .1);
    }
    bomba.gain.setTargetAtTime(0, COMPASES * T, 1.5);
    var prev = null;
    for (b = 0; b < COMPASES; b++) (function (b) {
      var tA = triada(pasoBajo(b + .01)), tB = triada(pasoPiano(b + .01)), d = curva('delta', b + .5), t0 = b * T;
      var iguales = tA[0] === tB[0] && tA[1] === tB[1];
      en(t0 - .3, function () {
        var capas = iguales ? [[tA, 1.25, -.3]] : [[tA, 1, -.45], [tB, .7, .45]];
        capas.forEach(function (c) {
          // el paneo de la capa se suelta cuando acaba su último parcial (con una hora fija, la limpieza caía dentro de
          // la ventana de anticipación del taller y cortaba el muro al medio segundo: medido)
          var pan = u.paneo(c[2]), parciales = espectro(c[0], d), vivos = parciales.length; pan.connect(suma);
          parciales.forEach(function (p, k) {
            var o = u.osc(p[0] < 380 ? 'triangle' : 'sine', p[0]), g = u.gain(0); o.connect(g).connect(pan);
            var entra = t0 - .12 + Math.min(.45, k * .035), a = p[1] * c[1];           // oleada: de grave a agudo
            g.gain.setValueAtTime(0, Math.max(0, entra)); g.gain.linearRampToValueAtTime(a, entra + .18);
            g.gain.setTargetAtTime(a * .55, entra + .3, T * .6);                         // respira dentro del compás
            g.gain.setTargetAtTime(0, t0 + T - .05, .12);                                // y se funde con el siguiente
            o.start(Math.max(0, entra)); o.stop(t0 + T + .8);
            o.onended = function () { g.disconnect(); if (--vivos === 0) pan.disconnect(); };
          });
        });
      });
    })(b);
  }

  /* ── 2. piano preparado: la célula de Monk (3 notas cada 3 dieciseisavos), notas chafadas y tonos enteros ── */
  function piano(ctx, dest, banco, en) {
    var u = U(ctx), rng = rngDe('piano'), bus = u.gain(.42), pan = u.paneo(.18); bus.connect(pan).connect(dest);
    var golpe = u.ruido(.06, 'piano-golpe');
    var nota = function (m, t, v) {
      en(t - .05, function () {
        var f = hz(m), car = u.osc('sine', f), mod = u.osc('sine', f * 3.47), idx = u.gain(0), amp = u.gain(0);
        var c2 = u.osc('triangle', f * 2.013), g2 = u.gain(v * .18), lp = u.filtro('lowpass', 2400 + v * 2400, .5);
        mod.connect(idx).connect(car.frequency); car.connect(amp); c2.connect(g2).connect(amp); amp.connect(lp).connect(bus);
        idx.gain.setValueAtTime(f * 2.2 * v, t); idx.gain.setTargetAtTime(f * .15, t + .004, .05);
        amp.gain.setValueAtTime(0, t); amp.gain.linearRampToValueAtTime(v, t + .003); amp.gain.setTargetAtTime(0, t + .01, .32);
        var n = ctx.createBufferSource(), nb = u.filtro('bandpass', 700 + m * 6, 1.4), ng = u.gain(v * .25); n.buffer = golpe;
        n.connect(nb).connect(ng).connect(bus);
        [car, mod, c2].forEach(function (o) { o.start(t); o.stop(t + 1.6); });
        n.start(t); n.stop(t + .06);
        car.onended = function () { idx.disconnect(); amp.disconnect(); g2.disconnect(); lp.disconnect(); };
        n.onended = function () { nb.disconnect(); ng.disconnect(); };
      });
    };
    for (var b = 0; b < COMPASES - 1; b += 2) {
      var dens = curva('piano', b + 1); if (rng() > .35 + .65 * dens) continue;
      var tr = triada(pasoPiano(b + .01)), pcs = tonos(tr);
      var celula = [notaDe(tr, 2, 62), notaDe(tr, 1, 62), notaDe(tr, 0, 62) + 11];      // 5ª, 3ª y la séptima mayor
      var largo = 6 + Math.floor(dens * 6), inicio = rng() < .5 ? 0 : 2;                   // a veces entra tarde
      for (var k = 0; k < largo; k++) {
        var paso = inicio + k * 3, t = b * T + paso * S16 + swing(paso), m = celula[k % 3] + (k >= 6 && k % 3 === 0 ? 12 : 0);
        var v = .55 + .35 * rng() * (k % 3 === 0 ? 1 : .7);
        if (rng() < .35) nota(m - 1, t - .025, v * .45);                                    // la nota chafada
        nota(m, t, v);
      }
      var fin = inicio + largo * 3 + 1, base = celula[0] + 12;                              // cierra con tonos enteros
      for (var j = 0; j < 5 && fin + j < 32; j++) { var pt = fin + j; nota(base - 2 * j, b * T + pt * S16 + swing(pt), .45 - j * .05); }
      if (dens > .8) nota(notaDe(tr, -3, 48), b * T + 16 * S16, .5);                         // un golpe grave, a lo Monk
    }
  }

  /* ── 3. bajo de slap FM (funk minimal): raíz y octava de la tríada del bajo, golpes en E(5,16), pops ── */
  function bajo(ctx, dest, banco, en) {
    var u = U(ctx), rng = rngDe('bajo'), bus = u.gain(.62); bus.connect(dest);
    var PAT = [[0, 0, 1], [3, 0, .7], [6, 12, .8], [8, 0, .55], [10, 0, .8], [11, 0, .3], [13, 12, .7], [14, 7, .5]];
    for (var b = 0; b < COMPASES; b++) {
      var d = curva('bajo', b + .5); if (d < .05) continue;
      var tr = triada(pasoBajo(b + .01)), raiz = 28 + ((tr[0] - 4 + 12) % 12);
      PAT.forEach(function (p) {
        if (p[2] < .6 && rng() > d * .8) return;
        var t = b * T + p[0] * S16, m = raiz + p[1], f = hz(m), v = p[2] * d, pop = p[1] === 12, corto = p[2] < .5;
        var desliza = !pop && rng() < .15;
        en(t - .05, function () {
          var car = u.osc('sine', f), mod = u.osc('sine', f), idx = u.gain(0), amp = u.gain(0), lp = u.filtro('lowpass', pop ? 2600 : 1100, 1.2);
          mod.connect(idx).connect(car.frequency); car.connect(amp).connect(lp).connect(bus);
          if (desliza) { car.frequency.setValueAtTime(f * .89, t); car.frequency.setTargetAtTime(f, t, .03); }
          idx.gain.setValueAtTime(f * (pop ? 4.5 : 2.6), t); idx.gain.setTargetAtTime(f * .3, t + .004, pop ? .03 : .06);
          amp.gain.setValueAtTime(0, t); amp.gain.linearRampToValueAtTime(v, t + .003);
          amp.gain.setTargetAtTime(0, t + S16 * (corto ? .4 : 1.3), .04);
          car.start(t); mod.start(t); car.stop(t + .8); mod.stop(t + .8);
          car.onended = function () { idx.disconnect(); amp.disconnect(); lp.disconnect(); };
        });
      });
    }
  }

  /* ── 4. batería cuadrada (MIDI): bombo, palmas tarde (4 y 13), aro fantasma, hats apagados ── */
  function bombo(ctx, dest, banco, en) {
    var u = U(ctx), bus = u.gain(.9); bus.connect(dest);
    for (var b = 0; b < COMPASES; b++) {
      var d = curva('kit', b + .5); if (d < .05) continue;
      [0, 3, 7, 10, b % 2 ? 14 : -1].forEach(function (p, i) {
        if (p < 0) return;
        var t = b * T + p * S16, v = (i === 0 ? 1 : .8) * d;
        en(t - .05, function () {
          var o = u.osc('sine', 140), g = u.gain(0); o.connect(g).connect(bus);
          o.frequency.setValueAtTime(140, t); o.frequency.exponentialRampToValueAtTime(45, t + .1);
          g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(v, t + .002); g.gain.setTargetAtTime(0, t + .02, .11);
          o.start(t); o.stop(t + .6); o.onended = function () { g.disconnect(); };
        });
      });
    }
  }
  function kit(ctx, dest, banco, en) {
    var u = U(ctx), rng = rngDe('kit'), bus = u.gain(.7); bus.connect(dest);
    var nz = u.ruido(1, 'kit');
    var golpe = function (t, v, f, q, tau, pan, desde) {
      en(t - .05, function () {
        var s = ctx.createBufferSource(), fl = u.filtro(f > 6000 ? 'highpass' : 'bandpass', f, q), g = u.gain(0), p = u.paneo(pan);
        s.buffer = nz; s.connect(fl).connect(g).connect(p).connect(bus);
        g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(v, t + .001); g.gain.setTargetAtTime(0, t + .002, tau);
        s.start(t, desde); s.stop(t + .3); s.onended = function () { fl.disconnect(); g.disconnect(); p.disconnect(); };
      });
    };
    for (var b = 0; b < COMPASES; b++) {
      var d = curva('kit', b + .5); if (d < .05) continue;
      [4, 13].forEach(function (p) {                    // palmas: tres manos a 0, 9 y 19 ms
        [0, .009, .019].forEach(function (dt, k) { golpe(b * T + p * S16 + dt, .55 * d * (1 - k * .2), 1300, 1.1, .05, (k - 1) * .2, rng()); });
      });
      [7, 10, 15].forEach(function (p) { if (rng() < .55 * d) golpe(b * T + p * S16, .22 * d, 1750, 6, .025, -.15, rng()); });   // aro fantasma
      for (var s = 0; s < 16; s++) {                     // hats apagados, cuadrados, con huecos
        if (s % 4 === 0 || rng() > .8 * d) continue;
        golpe(b * T + s * S16, (s % 2 ? .1 : .16) * d * (.7 + .3 * rng()), 8500, .7, s === 14 ? .09 : .018, .3, rng());
      }
    }
  }

  /* ── 5. las voces: sílaba por sílaba. [quién, compás, paso, base, [[sílaba, grado, 16avos]…]]
   * quién: A = ardilla (ardilla ligera, sin vibrato), G = grave (PSOLA, ligada). Las notas salen de la tríada del bajo. ── */
  var L = function (s) { return s.split(' ').map(function (x) { var p = x.split(':'); return [p[0], +p[1], +p[2]]; }); };
  var VERSO1 = [
    'te:2:2 de:2:1 jé:3:3 u:1:1 na:2:2 no:3:1 ta:4:3 en:2:1 la:2:1 es:3:2 qui:4:2 na:3:8',
    'se:3:2 vol:3:1 vió:4:3 o:2:1 tra:3:2 no:4:1 ta:5:3 en:3:1 la:3:1 es:4:2 qui:5:2 na:4:8',
    'di:2:1 la:2:1 vuel:3:2 ta:2:2 y:1:1 di:2:1 la:2:1 vuel:3:2 ta:2:2 en:1:1 la:1:1 es:2:2 qui:3:2 na:1:8',
    'y:1:1 me:2:1 es:3:2 ta:4:2 bas:3:1 es:4:1 pe:5:1 ran:4:2 do:3:2 en:2:1 la:2:1 es:3:2 qui:2:2 na:0:8'
  ];
  var ECO = 'en:0:2 la:0:2 es:1:3 qui:2:3 na:0:12';
  var MISTERIOSO = 'mis:5:2 te:4:2 rio:3:3 so:4:5 mis:5:2 te:4:2 rio:6:3 so:3:13';
  var CADAPASO = function (fin) { return 'ca:0:2 da:1:2 pa:2:2 so:1:2 cam:2:3 bia:3:3 u:2:2 na:1:2 voz:' + fin + ':14'; };
  var UNAVOZ = 'u:3:2 na:4:2 voz:5:8 u:3:2 na:4:2 voz:2:16';
  var LETRA = [];
  VERSO1.forEach(function (v, i) { LETRA.push(['A', 8 + 4 * i, 0, 57, L(v)]); LETRA.push(['G', 10 + 4 * i, 0, 45, L(ECO)]); });
  [24, 28, 48].forEach(function (b, i) {
    LETRA.push(['A', b, 0, 57, L(MISTERIOSO)]); LETRA.push(['G', b + 1, 0, 45, L(CADAPASO(0))]);
    LETRA.push(['A', b + 2, 0, 57, L(UNAVOZ)]); if (i < 2) LETRA.push(['G', b + 3, 0, 45, L(CADAPASO(i === 1 ? 0 : 1))]);
  });
  LETRA.push(['G', 34, 0, 45, L('no:0:3 hay:0:3 sa:1:2 li:0:2 da:-1:10')], ['G', 36, 0, 45, L('no:0:3 hay:0:3 sa:1:2 li:0:2 da:-1:10')],
             ['G', 38, 0, 45, L('en:0:2 ton:1:2 ces:2:2 la:1:2 sa:2:2 li:3:2 da:2:3 es:1:2 vol:1:3 ver:0:12')]);
  // verso 2: el espejo (la epístrofe se vuelve anáfora); la grave lleva
  LETRA.push(['G', 40, 0, 45, L('en:0:1 la:2:1 es:3:2 qui:2:2 na:3:3 me:4:1 es:5:1 ta:4:2 bas:3:1 es:4:2 pe:3:2 ran:2:2 do:1:8')],
             ['A', 42, 0, 57, L('en:1:1 la:3:1 es:2:2 qui:1:2 na:2:4 di:2:2 la:3:2 vuel:2:3 ta:2:11')],
             ['G', 44, 0, 45, L('en:4:1 la:5:1 es:4:2 qui:3:2 na:3:3 se:4:2 vol:3:1 vió:3:3 o:2:1 tra:1:2 no:2:2 ta:3:8')],
             ['A', 46, 0, 57, L('en:3:1 la:4:1 es:3:2 qui:2:2 na:2:3 te:4:2 de:3:1 jé:2:3 u:2:1 na:1:2 no:2:2 ta:2:8')]);
  var VUELVE = function (fin) { return L('y:2:1 vuel:3:2 ve:2:2 a:1:1 ca:1:3 sa:0:7 y:2:1 vuel:3:2 ve:4:2 a:3:1 ca:2:3 sa:0:' + fin); };
  [['A', 57], ['G', 45]].forEach(function (q) { LETRA.push([q[0], 52, 0, q[1], VUELVE(7)], [q[0], 54, 0, q[1], VUELVE(20)], [q[0], 58, 0, q[1], L('en:0:2 la:1:2 es:2:4 qui:1:4 na:0:20')]); });

  function partitura() {
    return LETRA.map(function (r) {
      var t = r[1] * T + r[2] * S16;
      return { quien: r[0], compas: r[1], eventos: r[4].map(function (w) {
        var tr = triada(pasoBajo(t / T + .01)), e = { t: t, dur: w[2] * S16, texto: w[0], nota: notaDe(tr, w[1], r[3]) }; t += e.dur; return e;
      }) };
    });
  }
  function voces(quien) {
    return function (ctx, dest, banco, en) {
      if (!banco) return;
      partitura().forEach(function (r, k) {
        if (r.quien !== quien) return;
        var op = quien === 'A' ? { porPalabra: true, rng: rngDe('a' + k), agendar: en }
                               : { modo: 'psola', vibrato: [4.6, .005], rng: rngDe('g' + k), agendar: en };   // vibrato a la mitad: en PSOLA grave cada armónico cruza los formantes y aleteaba (Canek: «los vibratos suenan raros»)
        banco.cantar(dest, r.eventos, op);
      });
    };
  }
  // el callejón: «es · qui · na» cada 4 dieciseisavos (3 contra 4), en ardilla, notas de la tríada del bajo
  function esquina(ctx, dest, banco, en) {
    if (!banco) return;
    var rng = rngDe('esquina'), sil = ['es', 'qui', 'na'];
    for (var b = 32; b < 40; b++) for (var p = 0; p < 16; p += 4) (function (b, p) {
      var k = ((b - 32) * 4 + p / 4), t = b * T + p * S16, tr = triada(pasoBajo(b + .01)), nota = notaDe(tr, [3, 4, 5][k % 3] + (b >= 36 ? 1 : 0), 64);
      var pp = (k % 3 - 1) * .5, nv = .6 + .4 * rng(), pan = null;
      en(t - .1, function () {
        pan = ctx.createStereoPanner(); pan.pan.value = pp; pan.connect(dest);
        banco.cantar(pan, [{ t: t, dur: S16 * (1.5 + (k % 3 === 2 ? 1 : 0)), texto: sil[k % 3], nota: nota }], { nivel: nv, porPalabra: true });
      });
      en(t + 2.5 * T, function () { if (pan) pan.disconnect(); });
    })(b, p);
  }

  var PISTAS = { muro: muro, piano: piano, bajo: bajo, bombo: bombo, kit: kit, ardilla: voces('A'), grave: voces('G'), esquina: esquina };
  global.Cancion = { PISTAS: Object.keys(PISTAS), pista: function (n) { return PISTAS[n]; }, partitura: partitura, curva: curva, CURVAS: CURVAS,
                     camino: function () { return CAMINO.map(nombre); }, caminantes: function (b) { return [nombre(triada(pasoBajo(b))), nombre(triada(pasoPiano(b)))]; },
                     DURACION: DURACION, T: T, S16: S16, COMPASES: COMPASES, BPM: BPM, hz: hz,
                     usaBanco: function (n) { return ['ardilla', 'grave', 'esquina'].indexOf(n) >= 0; } };
})(typeof window !== 'undefined' ? window : globalThis);
