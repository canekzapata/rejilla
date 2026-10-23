/* cancion.js — «la misma garganta» (loop 07 de la rejilla). La partitura y los instrumentos, en Web Audio.
 *
 * Se renderiza fuera de línea POR PISTAS (stems): cada pista es una función (ctx, destino, banco, en) que agenda
 * todo en un OfflineAudioContext. La mezcla, las salas y la edad se hacen después en Python (mezcla.py).
 * en(t, f): crea los nodos de un evento justo antes de que suene (el taller suspende el render cada compás).
 * Aun fuera de línea, cada nodo conectado se procesa en cada bloque de toda la pieza: la batería armada de
 * golpe tardaba 101 s en renderizar.
 *
 *   Cancion.PISTAS             → nombres de las pistas
 *   Cancion.pista(n)(ctx, d, banco)
 *   Cancion.partitura()        → la letra con tiempos y notas (para medir y dibujar)
 *   Cancion.DURACION           → segundos (60 compases + cola)
 *
 * La tónica es La en todo: portadora en La1, tierra en La2, encuentro en La3, nave en La4.
 * La escala es tizita menor sobre La (La Si Do Mi Fa); el grano oscuro es Si♭ (el armónico 17 de La1).
 */
(function (global) {
  'use strict';
  var BPM = 103.125, T = 240 / BPM, S16 = T / 16, COMPASES = 60, COLA = 4, F0 = 55;
  var DURACION = COMPASES * T + COLA;
  var hz = function (m) { return 440 * Math.pow(2, (m - 69) / 12); };

  // azar sembrado (FNV-1a + mulberry32): la misma canción siempre
  function rngDe(nombre) {
    var h = 2166136261; nombre = 'garganta·' + nombre;
    for (var i = 0; i < nombre.length; i++) { h ^= nombre.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
    return function () { h = (h + 0x6D2B79F5) >>> 0; var t = h; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }

  /* ── las curvas: cada instrumento cambia con su propia curva (tejer, no cortar). [compás, valor] ── */
  var CURVAS = {
    foco:        [[0, 0], [3, .1], [7.5, 1], [27.5, 1], [29.5, .3], [34, .35], [36, 1], [60, 1]],   // el groove entra en foco
    portadora:   [[0, .55], [6, .8], [8, .85], [28, .8], [36, .9], [56, 1], [60, 1]],
    pared:       [[0, .6], [7, 1], [9.5, .45], [19, .55], [20, .85], [28, 1], [36, .45], [47, .6], [48, .9], [56, .55], [60, .2]],
    bajo:        [[0, 0], [6.5, 0], [8, .55], [19, .65], [20, 1], [28, .35], [35, .55], [36, .8], [48, 1], [58, .9], [60, 0]],
    bombo:       [[0, 0], [5, 0], [8, .75], [19.5, .8], [20, 1], [28, .45], [35.5, .6], [36, .9], [48, 1], [59, .8], [60, 0]],
    caja:        [[0, 0], [16, 0], [20, 1], [28, .25], [35, .4], [36, .75], [48, 1], [57, .7], [60, 0]],
    consonantes: [[0, 0], [6, 0], [8, .3], [20, .55], [28, 1], [35, .9], [36, .45], [48, .65], [56, .3], [60, .1]],
    vidrio:      [[0, .25], [7.5, .5], [10, .1], [18, .1], [20, .6], [27, .5], [28, .1], [44, .1], [48, .8], [56, .5], [60, 0]]   // en la niebla: medios desde el arranque
  };
  function curva(nombre, b) {
    var K = CURVAS[nombre];
    if (b <= K[0][0]) return K[0][1];
    for (var i = 1; i < K.length; i++) if (b <= K[i][0]) {
      var u = (b - K[i - 1][0]) / (K[i][0] - K[i - 1][0]); u = u * u * (3 - 2 * u);   // suave en las uniones
      return K[i - 1][1] + (K[i][1] - K[i - 1][1]) * u;
    }
    return K[K.length - 1][1];
  }
  // una curva como automatización de un AudioParam (muestreada cada octavo de compás)
  function automatizar(param, nombre, escala, desde, hasta) {
    escala = escala == null ? 1 : escala; desde = desde || 0; hasta = hasta == null ? COMPASES : hasta;
    var n = Math.max(2, Math.round((hasta - desde) * 8)), v = new Float32Array(n);
    for (var i = 0; i < n; i++) v[i] = curva(nombre, desde + (hasta - desde) * i / (n - 1)) * escala;
    param.setValueCurveAtTime(v, desde * T, (hasta - desde) * T);
  }

  /* ── utilidades de nodos ── */
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
  function euclides(k, n, rot) { var out = []; for (var i = 0; i < n; i++) if (((i + (rot || 0)) * k) % n < k) out.push(i); return out; }

  /* ── 1. la portadora: La1 y su serie, en tres bandas; el groove son sus envolventes. Desenfocada = cada golpe
   *       se corre al azar y se alarga (ambient); enfocada = cae en la rejilla (funk de una nota) ── */
  var PARCIALES = { bajo: [[1, 1], [2, .7], [3, .5]], medio: [[4, .42], [5, .3], [6, .3], [8, .2]], alto: [[9, .13], [10, .11], [12, .08], [15, .05]] };
  var GROOVE = {
    bajo:  { 0: 1, 3: .55, 6: .8, 10: .7, 13: .45 },                 // el Uno pesado (P-Funk)
    medio: { 2: .45, 4: .9, 7: .4, 11: .55, 12: .85, 14: .35 },
    alto:  { 1: .3, 2: .5, 3: .25, 5: .45, 6: .3, 7: .6, 9: .3, 10: .5, 11: .3, 13: .45, 14: .3, 15: .65 }
  };
  var TAU = { bajo: .22, medio: .1, alto: .045 };
  function portadora(ctx, dest) {
    var u = U(ctx), rng = rngDe('portadora'), sal = u.gain(1); sal.connect(dest);
    automatizar(sal.gain, 'portadora');
    Object.keys(PARCIALES).forEach(function (banda) {
      var bus = u.gain(0), pan = u.paneo(banda === 'alto' ? .3 : banda === 'medio' ? -.2 : 0);
      bus.connect(pan).connect(sal);
      PARCIALES[banda].forEach(function (pa, j) {
        [0, 1].forEach(function (k) {                               // el halo: un gemelo que bate una vez por compás
          var o = u.osc('sine', F0 * pa[0] + k * (1 / T) * (j % 2 ? 1 : -1)), g = u.gain(pa[1] * (k ? .3 : 1) * .3);
          o.connect(g).connect(bus); o.start(0); o.stop(DURACION);
        });
      });
      var gr = bus.gain; gr.setValueAtTime(0, 0);
      for (var b = 0; b < COMPASES; b++) {
        var foco = curva('foco', b + .5), piso = .16 + .55 * (1 - foco);
        Object.keys(GROOVE[banda]).forEach(function (paso) {
          paso = +paso; var g = GROOVE[banda][paso];
          var corre = (1 - foco) * (rng() - .5) * T * .45, t = Math.max(0, b * T + paso * S16 + corre + (paso % 2 ? .012 : 0));
          var ataque = .004 + (1 - foco) * .12, tau = TAU[banda] * (1 + (1 - foco) * 4);
          gr.setTargetAtTime(piso + (1 - piso) * g * (.5 + .5 * foco), t, ataque / 3);
          gr.setTargetAtTime(piso, t + ataque, tau);
        });
      }
      gr.setTargetAtTime(0, COMPASES * T, 1.2);
    });
  }

  /* ── 2. bajo FM: ostinato de tizita en La1 con el grano Si♭; deslices (P-Funk) en algunos golpes ── */
  function bajo(ctx, dest) {
    var u = U(ctx), rng = rngDe('bajo'), car = u.osc('sine', 55), mod = u.osc('sine', 55), idx = u.gain(0), amp = u.gain(0);
    var nivel = u.gain(.5), lp = u.filtro('lowpass', 900, .7); mod.connect(idx).connect(car.frequency);
    car.connect(amp).connect(lp).connect(nivel).connect(dest); automatizar(nivel.gain, 'bajo', .5);
    car.start(0); mod.start(0); car.stop(DURACION); mod.stop(DURACION);
    var golpes = [0, 3, 6, 10, 13], ost = [[33, 33, 40, 36, 33], [33, 33, 40, 36, 29], [33, 33, 40, 43, 34], [33, 36, 40, 36, 33]];
    for (var b = 6; b < COMPASES - 1; b++) {
      var dens = curva('bajo', b + .5); if (dens < .05) continue;
      golpes.forEach(function (p, i) {
        if (i > 0 && rng() > .35 + .65 * dens) return;
        var m = ost[b % 4][i], t = b * T + p * S16 + (p % 2 ? .012 : 0), f = hz(m), desliza = rng() < .18;
        if (desliza) { car.frequency.setValueAtTime(hz(m - 5), t); car.frequency.setTargetAtTime(f, t, .04); }
        else car.frequency.setValueAtTime(f, t);
        mod.frequency.setValueAtTime(f * 2, t);
        idx.gain.setValueAtTime(f * (2.2 + 1.6 * rng()), t); idx.gain.setTargetAtTime(f * .25, t + .005, .07);
        amp.gain.setTargetAtTime(.9, t, .003); amp.gain.setTargetAtTime(0, t + S16 * (1.6 + rng() * 1.2), .05);
      });
    }
  }

  /* ── 3. bombo: sub que cae de 125 a 44 Hz, con un clic de madera apagado ── */
  function bombo(ctx, dest, banco, en) {
    var u = U(ctx), rng = rngDe('bombo'), bus = u.gain(.9); bus.connect(dest);
    var clic = u.ruido(.05, 'clic');
    for (var b = 0; b < COMPASES; b++) {
      var d = curva('bombo', b + .5); if (d < .05) continue;
      var pasos = d < .5 ? [0, 8] : [0, 6, 10].concat(b % 4 === 3 ? [14] : []);
      pasos.forEach(function (p, i) {
        var v = (i === 0 ? 1 : .75) * Math.min(1, d * 1.15) * (.9 + .1 * rng()), t = b * T + p * S16;
        en(t, function () {
        var o = u.osc('sine', 125), g = u.gain(0); o.connect(g).connect(bus);
        o.frequency.setValueAtTime(125, t); o.frequency.exponentialRampToValueAtTime(44, t + .11);
        g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(v, t + .003); g.gain.setTargetAtTime(0, t + .02, .12);
        o.start(t); o.stop(t + .7);
        var c = ctx.createBufferSource(), cf = u.filtro('bandpass', 1800, 1.5), cg = u.gain(0); c.buffer = clic;
        c.connect(cf).connect(cg).connect(bus); cg.gain.setValueAtTime(v * .12, t); cg.gain.setTargetAtTime(0, t + .002, .008); c.start(t); c.stop(t + .05);
        o.onended = function () { g.disconnect(); }; c.onended = function () { cf.disconnect(); cg.disconnect(); };
        });
      });
    }
  }

  /* ── 4. caja afinada: ruido por un peine de La (220, 440, 660, 880, 1320): un golpe que tiene altura ── */
  function caja(ctx, dest, banco, en) {
    var u = U(ctx), rng = rngDe('caja'), bus = u.gain(.7); bus.connect(dest);
    var nz = u.ruido(1.5, 'caja'), peine = [220, 440, 660, 880, 1320].map(function (f, k) {
      var bp = u.filtro('bandpass', f * (1 + .003 * k), 14), g = u.gain(1 / (k + 1.5)); bp.connect(g).connect(bus); return bp;
    });
    var cuerpo = u.filtro('bandpass', 2600, .8), cg = u.gain(.35); cuerpo.connect(cg).connect(bus);
    for (var b = 0; b < COMPASES; b++) {
      var d = curva('caja', b + .5); if (d < .05) continue;
      [[4, 1], [13, .9], [7, .25], [10, .3], [15, .2]].forEach(function (pv) {    // el segundo golpe llega tarde (13, no 12)
        if (pv[1] < .5 && rng() > d * .8) return;
        var t = b * T + pv[0] * S16 + (pv[0] % 2 ? .014 : 0), v = pv[1] * d * (.85 + .15 * rng()), desde = rng() * 1.2;
        en(t, function () {
          var s = ctx.createBufferSource(), g = u.gain(0); s.buffer = nz; s.connect(g);
          peine.forEach(function (bp) { g.connect(bp); }); g.connect(cuerpo);
          g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(v, t + .001); g.gain.setTargetAtTime(0, t + .004, .09);
          s.start(t, desde); s.stop(t + .45); s.onended = function () { g.disconnect(); };
        });
      });
    }
  }

  /* ── 5. pared espectral (Grisey): la serie de La1 estirada; el armónico 17 (≈ Si♭5) es el grano oscuro.
   *       Cada parcial respira a su propio ritmo (movimiento) y está doblado y apenas desafinado (cuerpo) ── */
  function pared(ctx, dest) {
    var u = U(ctx), rng = rngDe('pared'), delta = .005, sal = u.gain(.1), lp = u.filtro('lowpass', 3200, .5);
    lp.connect(sal).connect(dest); automatizar(sal.gain, 'pared', .1);
    [3, 4, 5, 6, 7, 9, 11, 13, 15, 17].forEach(function (n, j) {
      var f = F0 * Math.pow(n, 1 + delta), pan = u.paneo((j % 2 ? 1 : -1) * (.2 + .6 * rng())), g = u.gain(.6 / Math.sqrt(n)), resp = u.gain(.5);
      var lfo = u.osc('sine', .04 + .25 * rng()), lg = u.gain(.3);   // ±.3: con ±.45 el valle caía a −20 dB y dejaba un hoyo lfo.connect(lg).connect(resp.gain);
      [0, 1].forEach(function (k) { var o = u.osc(n > 9 ? 'sine' : 'triangle', f * (1 + (k ? .0011 : -.0007))); o.connect(g); o.start(0); o.stop(DURACION); });
      g.connect(resp).connect(pan).connect(lp); lfo.start(0); lfo.stop(DURACION);
    });
  }

  /* ── 6. vidrio frotado: la tercera aislada arriba (Do6) con su parcial inarmónico; nada de campanas ── */
  function vidrio(ctx, dest) {
    var u = U(ctx), sal = u.gain(.12); sal.connect(dest); automatizar(sal.gain, 'vidrio', .12);
    var nz = ctx.createBufferSource(); nz.buffer = u.ruido(4, 'vidrio'); nz.loop = true;
    [[hz(84), 90, 1], [hz(84) * 2.76, 120, .3], [hz(79), 90, .35]].forEach(function (p, k) {
      var bp = u.filtro('bandpass', p[0], p[1]), g = u.gain(p[2] * 9), pan = u.paneo(k === 1 ? .5 : -.35);
      var vib = u.osc('sine', .23 + k * .07), vg = u.gain(p[0] * .004); vib.connect(vg).connect(bp.frequency); vib.start(0); vib.stop(DURACION);
      nz.connect(bp).connect(g).connect(pan).connect(sal);
    });
    nz.start(0); nz.stop(DURACION);
  }

  /* ── 7. consonantes del banco como percusión fina (en vez de hats); en el puente, «garganta» deshecha ── */
  var SILABAS = ['ta', 'ka', 'cha', 'sa', 'ka', 'ti', 'ta', 'pu'];
  function consonantes(ctx, dest, banco, en) {
    if (!banco) return;
    var rng = rngDe('consonantes'), bus = ctx.createGain(); bus.gain.value = .55; bus.connect(dest);
    var hp = ctx.createBiquadFilter(); hp.type = 'highpass'; hp.frequency.value = 900; hp.connect(bus);
    for (var b = 6; b < COMPASES; b++) {
      var d = curva('consonantes', b + .5), puente = b >= 28 && b < 36;
      for (var p = 0; p < 16; p++) {
        if (rng() > d * (p % 4 === 2 ? 1 : p % 2 ? .75 : .45)) continue;
        var sil = puente && p % 4 === 0 ? ['gar', 'gan', 'ta', 'gan'][(p / 4) | 0] : SILABAS[(p + b) % SILABAS.length];
        var nota = puente ? 57 + [0, 3, -4, 7][(p / 4) | 0] : 69 + [0, 3, 7, 12][(rng() * 4) | 0];
        var pp = (rng() - .5) * 1.2, nv = .5 + .5 * rng(), t = b * T + p * S16 + (p % 2 ? .012 : 0), destino = puente ? bus : hp;
        (function (sil, nota, pp, nv, t, destino) {
          var pan = null;
          en(t - .1, function () {
            pan = ctx.createStereoPanner(); pan.pan.value = pp; pan.connect(destino);
            banco.cantar(pan, [{ t: t, dur: S16 * .8, texto: sil, nota: nota }], { nivel: nv });
          });
          // la sílaba ya sonó: fuera del grafo. A 2.5 compases, para que caiga en una suspensión POSTERIOR (con t + .8
          // se ejecutaba en la misma suspensión que la creación y desconectaba la sílaba antes de sonar: pista vacía)
          en(t + 2.5 * T, function () { if (pan) pan.disconnect(); });
        })(sil, nota, pp, nv, t, destino);
      }
    }
  }

  /* ── 8. las voces: la letra con su melodía. Cada renglón: [quién, compás, paso, base, [[palabra, grado, 16avos]…]] ──
   * quién: T = tierra (PSOLA, ligada, vibrato tardío), N = nave (ardilla, robótica), U = una sola voz al final.
   * grado = semitonos sobre la base (tizita menor en La: 0 2 3 7 8, y sus octavas) */
  var LETRA = [
    // verso 1: la tierra en La2, la nave contesta dos compases después en La4
    ['T', 8, 0, 45, [['aquí', 0, 3], ['abajo', 3, 4], ['el', 2, 1], ['aire', 0, 4], ['pesa', -4, 12]]],
    ['N', 10, 0, 69, [['allá', 7, 3], ['arriba', 8, 4], ['el', 7, 1], ['aire', 3, 3], ['es', 2, 1], ['poco', 0, 8]]],
    ['T', 12, 0, 45, [['te', 0, 2], ['canto', 3, 4], ['con', 2, 2], ['lo', 0, 2], ['que', -4, 2], ['queda', -5, 10]]],
    ['N', 14, 0, 69, [['te', 3, 2], ['oigo', 7, 4], ['chiquita', 8, 4], ['y', 7, 2], ['tarde', 3, 8]]],
    ['T', 16, 0, 45, [['lo', 0, 2], ['que', 2, 2], ['digo', 3, 4], ['ahora', 7, 12]]],
    ['N', 18, 0, 69, [['me', 3, 2], ['suena', 2, 4], ['todavía', 0, 14]]],
    // coro: las dos a dos octavas
    ['T', 20, 0, 45, [['una', 7, 4], ['garganta', 8, 24]]], ['N', 20, 0, 69, [['una', 7, 4], ['garganta', 8, 24]]],
    ['T', 22, 0, 45, [['dos', 3, 4], ['alturas', 2, 24]]], ['N', 22, 0, 69, [['dos', 3, 4], ['alturas', 2, 24]]],
    ['T', 24, 0, 45, [['el', 0, 2], ['mismo', 3, 4], ['aire', 2, 22]]], ['N', 24, 0, 69, [['el', 0, 2], ['mismo', 3, 4], ['aire', 2, 22]]],
    ['T', 26, 0, 45, [['partido', 0, 6], ['en', -4, 2], ['dos', 0, 20]]], ['N', 26, 0, 69, [['partido', 0, 6], ['en', -4, 2], ['dos', 0, 20]]],
    // puente: la tierra deshace la palabra; la nave, muy lejos
    ['T', 30, 0, 45, [['gar', 0, 8], ['gan', 3, 8], ['ta', -4, 16]]],
    ['N', 32, 8, 81, [['me', 0, 2], ['oyes', -4, 10]]], ['N', 34, 8, 81, [['me', 0, 2], ['oyes', -5, 12]]],
    // verso 2: se cruzan; el retraso se achica (dos compases → uno → nada)
    ['T', 36, 0, 45, [['si', 0, 2], ['bajo', -4, 4], ['la', 0, 2], ['voz', 3, 4], ['me', 2, 2], ['hago', 0, 4], ['ogro', -5, 10]]],
    ['N', 38, 0, 69, [['si', 7, 2], ['la', 8, 2], ['subo', 12, 4], ['me', 8, 2], ['hago', 7, 4], ['ardilla', 12, 10]]],
    ['T', 40, 0, 45, [['dime', 7, 4], ['en', 8, 2], ['qué', 7, 2], ['nota', 3, 8]]],
    ['N', 41, 0, 69, [['dime', -5, 4], ['en', -4, 2], ['qué', -5, 2], ['nota', -9, 8]]],
    ['T', 43, 0, 45, [['somos', 8, 4], ['la', 7, 2], ['misma', 3, 18]]], ['N', 43, 0, 69, [['somos', -4, 4], ['la', -5, 2], ['misma', -9, 18]]],
    // coro final: una octava (La2 / La3) → unísono en La3
    ['T', 48, 0, 45, [['una', 7, 4], ['garganta', 8, 24]]], ['N', 48, 0, 57, [['una', 7, 4], ['garganta', 8, 24]]],
    ['T', 50, 0, 45, [['dos', 3, 4], ['alturas', 2, 24]]], ['N', 50, 0, 57, [['dos', 3, 4], ['alturas', 2, 24]]],
    ['T', 52, 0, 57, [['el', 0, 2], ['mismo', 3, 4], ['aire', 2, 22]]], ['N', 52, 0, 57, [['el', 0, 2], ['mismo', 3, 4], ['aire', 2, 22]]],
    ['T', 54, 0, 57, [['partido', 0, 6], ['en', -4, 2], ['uno', 0, 20]]], ['N', 54, 0, 57, [['partido', 0, 6], ['en', -4, 2], ['uno', 0, 20]]],
    // la misma: una sola voz en La3 (a esta altura los dos modos dan el mismo sonido)
    ['U', 56, 0, 57, [['aquí', 0, 8]]], ['U', 57, 0, 57, [['la', 3, 4], ['misma', 2, 12]]], ['U', 58, 0, 57, [['garganta', 0, 28]]]
  ];
  function partitura() {
    return LETRA.map(function (r) {
      var t = r[1] * T + r[2] * S16;
      return { quien: r[0], compas: r[1], eventos: r[4].map(function (w) {
        var e = { t: t, dur: w[2] * S16, texto: w[0], nota: r[3] + w[1] }; t += e.dur; return e;
      }) };
    });
  }
  function voces(quien) {
    return function (ctx, dest, banco, en) {
      if (!banco) return;
      partitura().forEach(function (r, k) {
        if (r.quien !== quien) return;
        var op = quien === 'N' ? { rng: rngDe('nave' + k) }                                   // ardilla, robótica
               : { modo: 'psola', vibrato: [5.1, .013], rng: rngDe('tierra' + k) };          // PSOLA, ligada
        op.agendar = en;
        banco.cantar(dest, r.eventos, op);
      });
    };
  }

  var PISTAS = { portadora: portadora, bajo: bajo, bombo: bombo, caja: caja, pared: pared, vidrio: vidrio, consonantes: consonantes,
                 tierra: voces('T'), nave: voces('N'), una: voces('U') };
  global.Cancion = { PISTAS: Object.keys(PISTAS), pista: function (n) { return PISTAS[n]; }, partitura: partitura, curva: curva,
                     CURVAS: CURVAS, DURACION: DURACION, T: T, S16: S16, COMPASES: COMPASES, BPM: BPM, hz: hz,
                     usaBanco: function (n) { return ['consonantes', 'tierra', 'nave', 'una'].indexOf(n) >= 0; } };
})(typeof window !== 'undefined' ? window : globalThis);
