/* cancion.js — «planeta 9» (loop 11 de la rejilla): la nota que no está.
 *
 * El planeta 9 no se ve: sólo se conoce por cómo se reúnen los objetos que jala. Aquí cada acorde es un puñado de
 * armónicos n·f de una fundamental f que NADIE toca (el planeta). Los armónicos usados nunca son potencias de 2
 * (1, 2, 4, 8, 16): así ni f ni sus octavas suenan en ninguna parte. Y como cualquier n que no es potencia de 2 tiene
 * un factor impar ≥ 3, cualquier timbre armónico sobre n·f (sierra, triángulo, FM 1:1) tampoco produce la clase de f.
 * El oído la deduce igual (fundamental ausente, «residue pitch»): el bajo de la canción es un planeta.
 *
 * La progresión visible es J-pop (王道進行, IV–V–iii–vi y vuelta a I en Sol), pero sólo existe en las fundamentales
 * ausentes; lo que suena son sus armónicos: el bajo toca la quinta (n = 3), las teclas tocan 5, 6, 9, 10, 12, 15…
 * ENTROPÍA H(t) ∈ [0, 1]: los parciales se desafinan, se estiran (inarmónicos), respiran ruido y caen cristales de hielo.
 * BELLEZA = H 0: la serie armónica exacta. Los presoros (pre-coros) son la gravedad: los objetos se reúnen
 * (los parciales desafinados se deslizan hasta su lugar exacto) y el coro se oye entero.
 *
 *   Cancion.pista(n)(ctx, destino, banco, en)    Cancion.partitura()    Cancion.acordes()    Cancion.entropia(b)
 */
(function (global) {
  'use strict';
  var BPM = 84, T = 240 / BPM, S16 = T / 16, COMPASES = 70, COLA = 6;
  var DURACION = COMPASES * T + COLA;
  var hz = function (m) { return 440 * Math.pow(2, (m - 69) / 12); };
  var mi = function (f) { return 69 + 12 * Math.log2(f / 440); };
  function rngDe(nombre) {
    var h = 2166136261; nombre = 'planeta9·' + nombre;
    for (var i = 0; i < nombre.length; i++) { h ^= nombre.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
    return function () { h = (h + 0x6D2B79F5) >>> 0; var t = h; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }

  /* ── la forma y los planetas (fundamentales ausentes, en midi: Sol1 = 31) ── */
  var SECC = [['intro', 0, 6], ['verso1', 6, 14], ['pre1', 14, 18], ['coro1', 18, 26], ['verso2', 26, 34], ['pre2', 34, 38],
              ['coro2', 38, 46], ['puente', 46, 54], ['coro3', 54, 64], ['coda', 64, 70]];
  var SETS = {
    sombra: [3, 5, 7, 9, 11, 13, 15],                        // impares: hueco, con la séptima (−31 c), el 11 (+49 c) y el 13 (−59 c)
    reune: [3, 5, 6, 9, 10, 12, 15, 18, 20],                 // el coro, que llega desafinado y se reúne
    belleza: [3, 5, 6, 9, 10, 12, 15, 18, 20, 24, 30],       // maj9 sin raíz: Mi m7 sobre un Do que no está (el IV△9 del J-pop)
    residuo: [3, 5, 6, 7, 9],                                // la coda: sólo lo necesario para deducir el planeta
    sustituto: [4, 5, 6, 8, 10, 12, 16]                      // el pez beta: un planeta que SÍ se ve (con su raíz), de juguete
  };
  var ACORDES = (function () {
    var A = [], verso = function (b) { [[0, 24], [2, 26], [4, 23], [6, 28]].forEach(function (x) { A.push([b + x[0], x[1], 'sombra']); }); };
    var coro = function (b) { [[0, 24], [1, 26], [2, 23], [3, 28], [4, 24], [5, 26], [6, 31]].forEach(function (x) { A.push([b + x[0], x[1], 'belleza']); }); };
    A.push([0, 31, 'sombra']); verso(6); A.push([14, 21, 'reune'], [16, 26, 'reune']); coro(18);
    verso(26); A.push([34, 21, 'reune'], [36, 26, 'reune']); coro(38);
    // el puente: el planeta se suelta; en los compases 48-49 («un pez beta / como planeta nuevo») el sustituto se ve
    [27, 25.5, 22, 29.3, 24.7, 21.4, 26].forEach(function (m, i) { A.push([46 + i, m, i === 2 || i === 3 ? 'sustituto' : 'sombra']); });
    A.push([53, 26, 'reune']); coro(54); A.push([62, 31, 'belleza'], [64, 31, 'belleza'], [66, 31, 'residuo']);
    A.push([COMPASES, 31, 'residuo']);
    return A;
  })();
  var acordeEn = function (b) { var k = 0; while (k + 1 < ACORDES.length && ACORDES[k + 1][0] <= b + 1e-9) k++; return ACORDES[k]; };
  var seccionEn = function (b) { for (var i = 0; i < SECC.length; i++) if (b < SECC[i][2]) return SECC[i][0]; return 'coda'; };

  var CURVAS = {   // por compás; suave entre puntos
    H:      [[0, .9], [6, .55], [14, .5], [17.5, 0], [26, 0], [26.5, .5], [34, .5], [37.5, 0], [46, 0], [46.8, 1], [52.5, .8], [53.8, 0], [70, 0]],
    muro:   [[0, 0], [1, .8], [6, .7], [14, .75], [18, 1], [26, .8], [34, .8], [38, 1], [46, .9], [54, 1], [64, .9], [68, .8], [70, 0]],
    teclas: [[0, 0], [5.9, 0], [6, .5], [14, .6], [18, 1], [26, .6], [34, .6], [38, 1], [46, 0], [54, 1], [64, .5], [65, 0]],
    bajo:   [[0, 0], [5.9, 0], [6, .7], [14, .8], [18, 1], [26, .8], [38, 1], [46, 0], [53.9, 0], [54, 1], [64, 0]],
    kit:    [[0, 0], [5.9, 0], [6, .5], [14, .6], [18, 1], [26, .55], [34, .6], [38, 1], [46, 0], [53.9, 0], [54, 1], [63, 1], [64, 0]],
    hielo:  [[0, 1], [6, .4], [14, .3], [17, 0], [26, 0], [26.5, .3], [34, .3], [37, 0], [46, 0], [46.5, 1], [53, .8], [54, 0], [70, 0]]
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
      }
    };
  }
  // la desafinación de la entropía (cents) de un parcial n en el compás b: un desvío fijo por parcial, más grande en los
  // presoros (los objetos llegan lejos y la gravedad los jala) y estiramiento inarmónico en el puente
  var DESVIO = (function () { var r = rngDe('desvio'), d = {}; for (var n = 1; n <= 40; n++) d[n] = r() * 2 - 1; return d; })();
  function desafina(n, b) {
    var H = curva('H', b), s = seccionEn(b), ancho = s.indexOf('pre') === 0 ? 160 : s === 'puente' ? 90 : 45;
    var c = H * ancho * DESVIO[n] + (s === 'puente' ? H * 2400 * Math.log2(n) * .012 : 0);
    // ningún parcial cruza una potencia de 2 de f al desafinarse (15 está a 112 cents de 16): el planeta no se asoma ni de paso
    var arriba = 1200 * Math.log2(Math.pow(2, Math.ceil(Math.log2(n))) / n), abajo = 1200 * Math.log2(n / Math.pow(2, Math.floor(Math.log2(n))));
    return Math.max(-abajo + 45, Math.min(arriba - 45, c));       // 45 c de margen: la banda medida es ±26 c (±1.5 %) y con 15 c el 15 caía dentro
  }

  /* ── 1. el muro: los armónicos del planeta, uno por oscilador; respiran ruido de arco cuando hay entropía ── */
  function muro(ctx, dest, banco, en) {
    var u = U(ctx), bus = u.gain(.5); bus.connect(dest);
    var nz = u.ruido(4, 'arco');
    for (var k = 0; k + 1 < ACORDES.length; k++) (function (k) {
      var A = ACORDES[k], b0 = A[0], b1 = ACORDES[k + 1][0], f = hz(A[1]), t0 = b0 * T, t1 = b1 * T, set = SETS[A[2]];
      var lento = A[2] !== 'belleza';                                              // en la sombra todo entra y sale despacio
      en(t0 - .6, function () {
        set.forEach(function (n, j) {
          var fn = n * f; if (fn > 5000) return;
          var o = u.osc(fn < 330 ? 'triangle' : 'sine', fn), g = u.gain(0), p = u.paneo(((j * .618) % 1 - .5) * (fn > 300 ? 1.1 : .4));
          o.connect(g).connect(p).connect(bus);
          var a = .5 / Math.pow(n / 3, .62), entra = Math.max(0, t0 - (lento ? .35 : .04) + (b0 === 0 ? j * T * .55 : 0));   // intro: entran de uno en uno
          // la desafinación sigue a H compás a compás (y en los presoros se cierra hasta cero: los objetos se reúnen)
          for (var q = b0; q <= b1; q += .25) o.detune.setTargetAtTime(desafina(n, q), Math.max(0, q * T - .01), T * .2);
          g.gain.setValueAtTime(0, entra); g.gain.linearRampToValueAtTime(a, entra + (lento ? .6 : .08));
          for (q = b0; q < b1; q += .5) g.gain.setTargetAtTime(a * curva('muro', q + .25) * (1 - .35 * curva('H', q) * (.5 + .5 * Math.sin(q * 7.1 + n))), Math.max(entra + .1, q * T), T * .3);
          g.gain.setTargetAtTime(0, t1 + (lento ? .1 : -.02), lento ? .35 : .06);
          o.start(entra); o.stop(t1 + 2);
          o.onended = function () { g.disconnect(); p.disconnect(); };
          // el arco: ruido angosto alrededor del parcial, sólo con entropía
          var hmax = 0; for (q = b0; q < b1; q += .5) hmax = Math.max(hmax, curva('H', q));
          if (hmax > .15 && fn < 3000) {
            var s = ctx.createBufferSource(), bp = u.filtro('bandpass', fn, 30), gn = u.gain(0); s.buffer = nz; s.loop = true;
            s.connect(bp).connect(gn).connect(p);
            for (q = b0; q < b1; q += .5) gn.gain.setTargetAtTime(a * 6 * curva('H', q) * curva('muro', q), Math.max(entra, q * T), T * .3);
            gn.gain.setTargetAtTime(0, t1, .3);
            s.start(entra, (j * .37) % 3); s.stop(t1 + 2); s.onended = function () { bp.disconnect(); gn.disconnect(); };
          }
        });
      });
    })(k);
  }

  /* ── 2. hielo: cristales (senos cortos que suben un poco) en armónicos altos, densidad ∝ H ── */
  function hielo(ctx, dest, banco, en) {
    var u = U(ctx), rng = rngDe('hielo'), bus = u.gain(.16); bus.connect(dest);
    for (var t = 0; t < COMPASES * T; ) {
      var b = t / T, d = curva('hielo', b) * curva('H', b);
      t += d > .02 ? -Math.log(1 - rng() * .999) / (d * 9) : .25;
      if (d <= .02) continue;
      (function (t, b) {
        var A = acordeEn(b), set = SETS[A[2]], n = set[Math.floor(rng() * set.length)], f = n * hz(A[1]) * [4, 8, 8, 16][Math.floor(rng() * 4)];
        if (f > 9000) f /= 2;
        var v = .3 + .7 * rng(), pan = rng() * 1.6 - .8, dt = .04 + .25 * rng();
        en(t - .05, function () {
          var o = u.osc('sine', f), g = u.gain(0), p = u.paneo(pan); o.connect(g).connect(p).connect(bus);
          o.frequency.setValueAtTime(f, t); o.frequency.linearRampToValueAtTime(f * 1.012, t + dt);
          g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(v, t + .002); g.gain.setTargetAtTime(0, t + .004, dt * .35);
          o.start(t); o.stop(t + dt * 2 + .05); o.onended = function () { g.disconnect(); p.disconnect(); };
        });
      })(t, b);
    }
  }

  /* ── 3. teclas: piano eléctrico FM (1:1 y la campanita 14:1: armónicos de la nota, válidos) — J-pop: arpegio en los
   * versos, golpes sincopados con anticipación en los coros. Las notas: armónicos 5, 6, 9, 10, 12, 15 llevados a 300-900 Hz ── */
  function voicing(b) {
    var A = acordeEn(b), f = hz(A[1]), out = [];
    [5, 6, 9, 10, 12, 15].forEach(function (n) { if (A[2] === 'sombra' && (n === 6 || n === 12)) n = n === 6 ? 7 : 11; var x = n * f; while (x < 300) x *= 2; while (x > 900) x /= 2; out.push(x); });
    return out.sort(function (a, c) { return a - c; });
  }
  function teclas(ctx, dest, banco, en) {
    var u = U(ctx), rng = rngDe('teclas'), bus = u.gain(.28), pan = u.paneo(-.12); bus.connect(pan).connect(dest);
    var nota = function (f, t, v, largo) {
      en(t - .05, function () {
        var car = u.osc('sine', f), mod = u.osc('sine', f), idx = u.gain(0), amp = u.gain(0), bell = u.osc('sine', f * 14), bg = u.gain(0);
        mod.connect(idx).connect(car.frequency); car.connect(amp); bell.connect(bg).connect(amp); amp.connect(bus);
        idx.gain.setValueAtTime(f * 1.6 * v, t); idx.gain.setTargetAtTime(f * .25, t + .005, .25);
        bg.gain.setValueAtTime(v * .08, t); bg.gain.setTargetAtTime(0, t + .002, .03);
        amp.gain.setValueAtTime(0, t); amp.gain.linearRampToValueAtTime(v, t + .004); amp.gain.setTargetAtTime(v * .4, t + .01, .4); amp.gain.setTargetAtTime(0, t + largo, .12);
        [car, mod, bell].forEach(function (o) { o.start(t); o.stop(t + largo + .8); });
        car.onended = function () { idx.disconnect(); amp.disconnect(); bg.disconnect(); };
      });
    };
    for (var b = 0; b < COMPASES; b++) {
      var d = curva('teclas', b + .5); if (d < .05) continue;
      var s = seccionEn(b + .5);
      if (s.indexOf('coro') === 0) {
        // golpes: 0, 3, 6, 8, 11 y la anticipación en 14 (ya con el acorde del compás siguiente)
        [[0, 1, 3], [3, .7, 2], [6, .8, 2], [8, .9, 3], [11, .7, 2], [14, .85, 4]].forEach(function (p) {
          var t = b * T + p[0] * S16, vo = voicing(b + (p[0] + 2) / 16);
          vo.forEach(function (f, i) { if (i < 4 || p[0] === 0) nota(f, t + i * .004, (.35 + .15 * rng()) * p[1] * d, p[2] * S16); });
        });
      } else {
        // arpegio en corcheas, hacia arriba y abajo, con notas que se quedan (pedal)
        for (var k = 0; k < 8; k++) {
          var vo2 = voicing(b + k / 8), idx2 = [0, 2, 4, 5, 3, 1, 2, 4][k] % vo2.length;
          nota(vo2[idx2], b * T + k * 2 * S16 + (k % 2 ? .012 : 0), (.28 + .1 * rng()) * d, 6 * S16);
        }
      }
    }
  }

  /* ── 4. el bajo: toca la QUINTA del planeta (n = 3) y su octava (6); nunca la raíz. Sierra + seno, con anticipación ── */
  function bajo(ctx, dest, banco, en) {
    var u = U(ctx), bus = u.gain(.5); bus.connect(dest);
    var PAT = { coro: [[0, 3, 1, 3], [3, 3, .7, 2], [6, 6, .8, 2], [8, 3, .9, 3], [11, 3, .7, 2], [14, 3, .9, 3]],
                verso: [[0, 3, 1, 10], [10, 3, .7, 3], [13, 6, .6, 3]], pre: [[0, 3, 1, 4], [4, 3, .8, 4], [8, 3, .9, 4], [12, 6, .9, 4]] };
    for (var b = 0; b < COMPASES; b++) {
      var d = curva('bajo', b + .5); if (d < .05) continue;
      var s = seccionEn(b + .5), pat = s.indexOf('coro') === 0 ? PAT.coro : s.indexOf('pre') === 0 ? PAT.pre : PAT.verso;
      pat.forEach(function (p) {
        var t = b * T + p[0] * S16, A = acordeEn(b + (p[0] + 2) / 16), f = p[1] * hz(A[1]); while (f > 160) f /= 2; while (f < 70) f *= 2;
        var v = p[2] * d, largo = p[3] * S16;
        en(t - .05, function () {
          var sw = u.osc('sawtooth', f), si = u.osc('sine', f), lp = u.filtro('lowpass', 900, 2), amp = u.gain(0), gs = u.gain(.12), gi = u.gain(.9);
          sw.connect(gs).connect(lp); si.connect(gi).connect(lp); lp.connect(amp).connect(bus);
          lp.frequency.setValueAtTime(1600, t); lp.frequency.setTargetAtTime(380, t + .005, .08);
          amp.gain.setValueAtTime(0, t); amp.gain.linearRampToValueAtTime(v, t + .006); amp.gain.setTargetAtTime(v * .7, t + .02, .2); amp.gain.setTargetAtTime(0, t + largo * .92, .03);
          [sw, si].forEach(function (o) { o.start(t); o.stop(t + largo + .4); });
          sw.onended = function () { lp.disconnect(); amp.disconnect(); gs.disconnect(); gi.disconnect(); };
        });
      });
    }
  }

  /* ── 5. batería J-pop: el bombo afinado a la quinta del planeta (barre de 6f a 3f), caja con cuerpo en 5f,
   * hats en corcheas (coro), shaker en 16avos (verso), redoble al final de cada presoro ── */
  function bombo(ctx, dest, banco, en) {
    var u = U(ctx), bus = u.gain(.85); bus.connect(dest);
    for (var b = 0; b < COMPASES; b++) {
      var d = curva('kit', b + .5); if (d < .05) continue;
      var s = seccionEn(b + .5), pasos = s.indexOf('coro') === 0 ? [0, 6, 8, 14] : s.indexOf('pre') === 0 ? [0, 8] : [0, 10];
      pasos.forEach(function (p, i) {
        var t = b * T + p * S16, A = acordeEn(b + p / 16), f3 = 3 * hz(A[1]); while (f3 > 130) f3 /= 2; while (f3 < 65) f3 *= 2;
        var v = (i === 0 ? 1 : .8) * d;
        en(t - .05, function () {
          var o = u.osc('sine', f3), g = u.gain(0); o.connect(g).connect(bus);
          // barre de 3.9·(3f) a 3f: un barrido más largo cruzaba 4f y 8f (la clase del planeta) en cada golpe
          o.frequency.setValueAtTime(f3 * 1.3, t); o.frequency.exponentialRampToValueAtTime(f3, t + .05);
          g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(v, t + .002); g.gain.setTargetAtTime(0, t + .03, .12);
          o.start(t); o.stop(t + .7); o.onended = function () { g.disconnect(); };
        });
      });
    }
  }
  function kit(ctx, dest, banco, en) {
    var u = U(ctx), rng = rngDe('kit'), bus = u.gain(.6); bus.connect(dest);
    var nz = u.ruido(1, 'kit');
    var golpe = function (t, v, f, q, tau, pan, tono) {
      en(t - .05, function () {
        var s = ctx.createBufferSource(), fl = u.filtro(f > 6000 ? 'highpass' : 'bandpass', f, q), g = u.gain(0), p = u.paneo(pan);
        s.buffer = nz; s.connect(fl).connect(g).connect(p).connect(bus);
        g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(v, t + .001); g.gain.setTargetAtTime(0, t + .002, tau);
        s.start(t, rng() * .6); s.stop(t + .4); s.onended = function () { fl.disconnect(); g.disconnect(); p.disconnect(); };
        if (tono) {                                                                // el cuerpo de la caja: 5f, que cae un poco
          var o = u.osc('triangle', tono), go = u.gain(0); o.connect(go).connect(p);
          o.frequency.setValueAtTime(tono * 1.15, t); o.frequency.setTargetAtTime(tono, t, .01);
          go.gain.setValueAtTime(v * .6, t); go.gain.setTargetAtTime(0, t + .005, .045);
          o.start(t); o.stop(t + .3); o.onended = function () { go.disconnect(); };
        }
      });
    };
    for (var b = 0; b < COMPASES; b++) {
      var d = curva('kit', b + .5); if (d < .05) continue;
      var s = seccionEn(b + .5), A = acordeEn(b), f5 = 5 * hz(A[1]); while (f5 > 260) f5 /= 2; while (f5 < 150) f5 *= 2;
      if (s.indexOf('coro') === 0) {
        [4, 12].forEach(function (p) { golpe(b * T + p * S16, .8 * d, 1900, .9, .09, 0, f5); });
        for (var k = 0; k < 8; k++) golpe(b * T + k * 2 * S16, (k % 2 ? .22 : .14) * d, 9000, .7, k === 7 ? .12 : .025, .25, 0);
      } else if (s.indexOf('pre') === 0) {
        golpe(b * T + 8 * S16, .6 * d, 1900, .9, .08, 0, f5);
        if (b % 4 === 3 || b % 4 === 1 && b + 1 === 18) for (var r = 0; r < 16; r++) golpe(b * T + r * S16, (.15 + .55 * r / 15) * d, 1900, .9, .05, (r % 2 - .5) * .3, f5);   // redoble: crece
        for (k = 0; k < 8; k++) golpe(b * T + k * 2 * S16, .12 * d, 9000, .7, .025, .25, 0);
      } else {
        golpe(b * T + 8 * S16, .45 * d, 2600, 3, .03, -.1, 0);                     // aro en el tres (medio tiempo)
        for (var h = 0; h < 16; h++) golpe(b * T + h * S16 + (h % 2 ? .01 : 0), (h % 4 === 2 ? .11 : .06) * d * (.7 + .3 * rng()), 5200, 2.5, .03, .35, 0);   // shaker
      }
    }
  }

  /* ── 6. las voces: [quién, compás, paso, 'sílaba:grado:16avos …']. El grado es un índice en las notas permitidas en
   * ese instante (armónicos del planeta del momento, nunca su clase): la melodía se reacomoda sola si cambia el acorde ── */
  var VOZSET = { belleza: [3, 5, 9, 15, 27], reune: [3, 5, 9, 15, 27], sombra: [3, 5, 7, 9, 11, 13, 15], residuo: [3, 5, 7, 9], sustituto: [4, 5, 6, 9] };
  var RANGO = { A: [61, 80], G: [46, 64] };
  function permitidas(b, quien) {
    var A = acordeEn(b), R = RANGO[quien], out = [];
    VOZSET[A[2]].forEach(function (n) { var m = A[1] + 12 * Math.log2(n); while (m > R[0]) m -= 12; while (m < R[0]) m += 12; for (; m <= R[1]; m += 12) out.push(m); });
    out.sort(function (a, c) { return a - c; });
    return out.filter(function (m, i) { return i === 0 || m - out[i - 1] > .3; });
  }
  var L = function (s) { return s.split(' ').map(function (x) { var p = x.split(':'); return [p[0].replace(/_/g, ' '), +p[1], +p[2]]; }); };   // «de_e»: dos sílabas en una nota
  var VERSO1 = ['el:2:2 pla:3:2 ne:4:2 ta:4:2 nue:5:3 ve:4:3 no:3:2 se:2:2 pue:3:2 de:2:2 ver:1:8',
                'ha:1:2 bi:2:2 ta:3:2 en:3:2 tre:4:2 un:5:2 cú:6:3 mu:5:1 lo:4:2 de:3:2 hie:4:4 los:2:6',
                'en:2:2 el:2:2 le:3:2 ja:4:2 no:5:2 cin:4:2 tu:5:2 rón:6:4 de:5:2 kui:4:4 per:3:6',
                'un:3:2 pa:4:2 sa:5:2 je:4:2 ro:3:2 más:2:4 que:3:2 via:4:2 ja:5:2 con:6:2 no:5:2 so:4:2 tros:3:4'];
  var VERSO2 = ['se:2:2 pa:3:2 re:4:2 ce:5:4 al:4:2 tí:6:6 mi:5:2 do:3:10',
                'al:3:2 fon:4:2 do:5:4 del:4:2 sa:3:4 lón:2:16',
                'tam:2:2 bién:3:2 di:4:2 ce:5:2 que:4:2 es:3:2 co:4:2 mo_el:5:2 a:6:2 mor:5:4 ~:4:8',
                'flo:4:2 re:5:2 ce:6:2 su:5:2 piel:4:4 an:3:2 te_el:4:2 mí:5:2 ni:6:2 mo:7:2 ges:6:4 to:4:4'];
  var PRE = ['la:1:4 luz:2:4 del:3:4 sol:4:18', 'no:3:2 se_o:4:2 cu:5:2 pa:4:2 de:3:2 él:5:20'];
  var CORO = ['só:5:2 lo:4:2 lo:3:2 co:4:2 no:5:2 ce:6:2 mos:5:4 por:3:2 los:4:2 ob:5:2 je:4:2 tos:3:6',
              'que:3:2 se:4:2 re:5:2 ú:6:3 nen:5:3 in:4:2 flui:5:2 dos:6:2 por:7:2 la:6:2 gra:5:2 ve:4:2 dad:5:4',
              'de_e:4:2 se:5:2 im:6:2 pre:7:2 vis:6:2 to:5:2 va:6:2 cí:7:4 o:6:12',
              'que:6:2 lla:5:2 ma:4:2 mos:5:2 pla:4:4 ne:3:4 ta:2:14'];
  var TAG = 'por:3:2 e:4:2 so:5:2 sa:4:2 be:3:2 mos:2:4 que_es:3:2 tá:4:2 a:5:4 hí:4:8';
  var PUENTE_A = ['plu:3:2 tón:5:4 se_es:4:2 ca:3:2 pó:4:4 co:6:2 rrien:5:4 do:4:10', null, 'co:4:2 mo:5:2 pla:6:2 ne:5:2 ta:4:4 nue:3:4 vo:2:14'];
  var PUENTE_AGUA = [null, 'y_en:2:2 su:3:2 lu:4:2 gar:3:4 un:4:2 pez:3:4 be:5:4 ta:2:10', 'co:2:2 mo:3:2 pla:4:2 ne:3:2 ta:2:4 nue:1:4 vo:0:14'];
  var LETRA = [];
  var linea = function (q, b, s, desp) { LETRA.push([q, b, 2, L(s), desp || 0]); };
  VERSO1.forEach(function (s, i) { linea('G', 6 + 2 * i, s); });
  VERSO2.forEach(function (s, i) { linea('G', 26 + 2 * i, s); });
  [14, 34].forEach(function (b) { linea('A', b, PRE[0]); linea('A', b + 2, PRE[1]); });
  [18, 38, 54].forEach(function (b, k) {
    CORO.forEach(function (s, i) { linea('A', b + 2 * i, s); if (k > 0) linea('G', b + 2 * i, s, -1); });      // la grave dobla en el 2º y el 3º
  });
  linea('A', 62, TAG); linea('G', 62, TAG, -1);
  PUENTE_A.forEach(function (s, i) { if (s) linea('A', 46 + 2 * i, s); });
  var DICHO = [['G', .4, 'todo esto dice mike brown sobre el planeta nueve'], ['G', 52.2, 'es un padre que intenta suplantar el vacío']];

  function partitura() {
    return LETRA.map(function (r) {
      var t = r[1] * T + r[2] * S16;
      return { quien: r[0], compas: r[1], eventos: r[3].filter(function (w) { return true; }).map(function (w) {
        var P = permitidas(t / T + .01, r[0]), g = Math.max(0, Math.min(P.length - 1, w[1] + r[4]));
        var e = { t: t, dur: w[2] * S16, texto: w[0], nota: P[g] }; t += e.dur; return e;
      }).filter(function (e) { return e.texto !== '~'; }) };
    });
  }
  // el agua del puente canta en el registro grave (la renderiza node con vozagua.js: ver objetos.js)
  function partituraAgua() {
    var out = [];
    PUENTE_AGUA.forEach(function (s, i) {
      if (!s) return; var t = (46 + 2 * i) * T + 2 * S16;
      L(s).forEach(function (w) { var P = permitidas(t / T + .01, 'G'), e = { t: t, dur: w[2] * S16, texto: w[0], nota: P[Math.min(P.length - 1, w[1])] }; out.push(e); t += e.dur; });
    });
    return out;
  }
  function voces(quien) {
    return function (ctx, dest, banco, en) {
      if (!banco) return;
      partitura().forEach(function (r, k) {
        if (r.quien !== quien) return;
        var op = quien === 'A' ? { porPalabra: true, rng: rngDe('a' + k), agendar: en } : { modo: 'psola', vibrato: [4.6, .005], rng: rngDe('g' + k), agendar: en };
        banco.cantar(dest, r.eventos, op);
      });
      DICHO.forEach(function (d) { if (d[0] === quien) banco.decir(dest, d[1] * T, d[2], { nota: 45, modo: 'psola', agendar: en }); });
    };
  }

  var PISTAS = { muro: muro, hielo: hielo, teclas: teclas, bajo: bajo, bombo: bombo, kit: kit, ardilla: voces('A'), grave: voces('G') };
  global.Cancion = { PISTAS: Object.keys(PISTAS), pista: function (n) { return PISTAS[n]; }, partitura: partitura, partituraAgua: partituraAgua,
                     acordes: function () { return ACORDES; }, SETS: SETS, SECC: SECC, curva: curva, CURVAS: CURVAS, entropia: function (b) { return curva('H', b); },
                     permitidas: permitidas, desafina: desafina, DURACION: DURACION, T: T, S16: S16, COMPASES: COMPASES, BPM: BPM, hz: hz, mi: mi,
                     usaBanco: function (n) { return n === 'ardilla' || n === 'grave'; } };
})(typeof window !== 'undefined' ? window : globalThis);
