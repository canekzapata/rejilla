/* cancion.js — «una sola línea» (loop 12 de la rejilla): Café internet, Berlín, 1997.
 *
 * En 1997 el edificio tenía UNA línea telefónica: estar en línea quería decir que nadie podía llamar. La red y la voz se
 * disputan el mismo cable, y la canción también:
 *  - la intro es el saludo del módem como partitura, en los cinco tiempos que pide la nota del libro: tono (el tono de
 *    marcar alemán, 425 Hz) / pregunta (los DTMF y el timbre) / respuesta (ANSam: 2100 Hz con inversiones de fase cada
 *    450 ms) / acuerdo (V.8 en FSK y el sondeo de línea: un peine de tonos cada 150 Hz) / arena (el entrenamiento:
 *    ruido de 600-3400 Hz, del que sale el breakbeat);
 *  - la velocidad de la conexión manda el tempo: 14 400 = trip-hop a 84; 28 800 = drum'n'bass a 168 (el doble);
 *    «la línea baja a la mitad» = vuelve a 84;
 *  - para llamar hay que colgar (+++ ATH0): sin módem no hay breakbeat; la llamada es voz de teléfono (Doina) contra la
 *    voz limpia de quien llama, con los pulsos de tarificación (3,40 el minuto) como reloj;
 *  - se reconecta (rebobinado de DJ, en la mezcla) y el final no tiene «línea de apagado»: se corta.
 * Sonido de los noventa: break sintetizado y pasado por un sampler de 12 bits (en la mezcla), bajo Reese, Rhodes con
 * trémolo, cuerdas de máquina, polvo de vinilo (en la mezcla).
 *
 *   Cancion.pista(n)(ctx, destino, banco, en)    Cancion.partitura()    Cancion.MAPA (qué pasa en cada compás)
 */
(function (global) {
  'use strict';
  var BPM = 84, T = 240 / BPM, S16 = T / 16, S32 = S16 / 2, COMPASES = 56, COLA = 0;   // sin cola: se corta
  var DURACION = COMPASES * T + COLA;
  var hz = function (m) { return 440 * Math.pow(2, (m - 69) / 12); };
  function rngDe(nombre) {
    var h = 2166136261; nombre = 'linea·' + nombre;
    for (var i = 0; i < nombre.length; i++) { h ^= nombre.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
    return function () { h = (h + 0x6D2B79F5) >>> 0; var t = h; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }

  /* ── el mapa: secciones, modo de la batería y acordes por compás ── */
  var SECC = [['handshake', 0, 8], ['verso', 8, 16], ['coro', 16, 24], ['atasco', 24, 26], ['mitad', 26, 28], ['llamada', 28, 40],
              ['coro2', 40, 52], ['coda', 52, 56]];
  var ACORDE = { Cm9: [36, [0, 3, 7, 10, 14]], Ab7M: [32, [0, 4, 7, 11, 14]], Fm9: [41, [0, 3, 7, 10, 14]], G7b9: [43, [0, 4, 10, 13]],
                 Bb6: [34, [0, 4, 7, 9, 14]], G7sus: [43, [0, 5, 7, 10]], Eb7M: [39, [0, 4, 7, 11, 14]], Dm7b5: [38, [0, 3, 6, 10]], Cmadd9: [36, [0, 7, 14, 15]] };
  var MAPA = (function () {
    var M = [], pon = function (a, b, kit, acordes) { for (var k = a; k < b; k++) M[k] = { kit: kit, acorde: acordes[(k - a) % acordes.length] }; };
    var VERSO = ['Cm9', 'Cm9', 'Ab7M', 'Ab7M', 'Fm9', 'Fm9', 'G7b9', 'G7b9'], CORO = ['Cm9', 'Bb6', 'Ab7M', 'G7sus'];
    pon(0, 6, 'nada', ['Cmadd9']); pon(6, 8, 'arena', ['Cmadd9']); pon(8, 16, 'trip', VERSO); pon(16, 24, 'dnb', CORO);
    pon(24, 26, 'atasco', ['G7sus']); pon(26, 28, 'trip', ['Fm9', 'G7b9']); pon(28, 32, 'nada', ['Cmadd9']);
    pon(32, 40, 'escobilla', ['Eb7M', 'Dm7b5', 'Cm9', 'Ab7M']); pon(40, 41, 'nada', ['G7sus']); pon(41, 51, 'dnb2', CORO); pon(51, 52, 'dnb2', ['Ab7M']);
    pon(52, 56, 'nada', ['Cmadd9']);
    return M;
  })();
  var en_ = function (b) { return MAPA[Math.max(0, Math.min(COMPASES - 1, Math.floor(b)))]; };
  var notasDe = function (nombre) { var a = ACORDE[nombre]; return a[1].map(function (i) { return a[0] + i; }); };
  var CURVAS = {   // niveles por compás (suaves)
    pad:    [[0, 0], [1.5, 0], [2.5, .7], [8, .5], [16, .9], [24, .6], [28, .7], [32, .8], [40, .5], [41, .9], [52, .7], [56, .6]],
    rhodes: [[0, 0], [7.9, 0], [8, .8], [16, .3], [24, .3], [26, .8], [28, 0], [31.9, 0], [32, 1], [40, 0], [52, 0], [56, 0]],
    bajo:   [[0, 0], [7.9, 0], [8, .9], [16, 1], [24, .6], [26, .9], [28, 0], [31.9, 0], [32, .6], [40, 0], [40.9, 0], [41, 1], [52, 0]],
    kitf:   [[0, 200], [6, 300], [7.9, 1800], [8, 18000], [56, 18000]]          // la arena se vuelve break: el filtro se abre
  };
  function curva(nombre, b) {
    var K = CURVAS[nombre];
    if (b <= K[0][0]) return K[0][1];
    for (var i = 1; i < K.length; i++) if (b <= K[i][0]) { var u = (b - K[i - 1][0]) / (K[i][0] - K[i - 1][0]); u = u * u * (3 - 2 * u); return K[i - 1][1] + (K[i][1] - K[i - 1][1]) * u; }
    return K[K.length - 1][1];
  }
  function U(ctx) {
    return {
      osc: function (tipo, f) { var o = ctx.createOscillator(); o.type = tipo; o.frequency.value = f; return o; },
      gain: function (v) { var g = ctx.createGain(); g.gain.value = v == null ? 1 : v; return g; },
      filtro: function (tipo, f, q) { var b = ctx.createBiquadFilter(); b.type = tipo; b.frequency.value = f; if (q != null) b.Q.value = q; return b; },
      paneo: function (p) { var x = ctx.createStereoPanner(); x.pan.value = p; return x; },
      ruido: function (seg, nombre) { var r = rngDe(nombre), n = Math.floor(seg * ctx.sampleRate), b = ctx.createBuffer(1, n, ctx.sampleRate), d = b.getChannelData(0); for (var i = 0; i < n; i++) d[i] = r() * 2 - 1; return b; }
    };
  }

  /* ── 1. el módem y el teléfono ── */
  var DTMF = { '1': [697, 1209], '2': [697, 1336], '3': [697, 1477], '4': [770, 1209], '5': [770, 1336], '6': [770, 1477], '7': [852, 1209], '8': [852, 1336], '9': [852, 1477], '0': [941, 1336] };
  function modem(ctx, dest, banco, en) {
    var u = U(ctx), rng = rngDe('modem'), bus = u.gain(.5); bus.connect(dest);
    var linea = u.filtro('bandpass', 1700, .45); linea.connect(bus);              // todo pasa por la línea (300-3400 Hz, más o menos)
    var tono = function (fs, t0, t1, v, tipo) {
      en(t0 - .1, function () {
        var g = u.gain(0); g.connect(linea);
        fs.forEach(function (f) { var o = u.osc(tipo || 'sine', f); o.connect(g); o.start(t0); o.stop(t1 + .02); o.onended = function () { g.disconnect(); }; });
        g.gain.setValueAtTime(0, t0); g.gain.linearRampToValueAtTime(v, t0 + .004); g.gain.setValueAtTime(v, t1 - .004); g.gain.linearRampToValueAtTime(0, t1);
      });
    };
    var marca = function (b, digitos) { digitos.split('').forEach(function (d, i) { var t = b * T + i * 2 * S16; tono(DTMF[d], t, t + S16 * 1.1, .35); }); };
    var arena = function (t0, t1, v, centro) {                                    // el entrenamiento / los datos: ruido de canal
      en(t0 - .1, function () {
        var s = ctx.createBufferSource(), bp = u.filtro('bandpass', centro || 1800, .7), g = u.gain(0); s.buffer = u.ruido(2, 'arena' + t0); s.loop = true;
        s.connect(bp).connect(g).connect(linea); g.gain.setValueAtTime(0, t0); g.gain.linearRampToValueAtTime(v, t0 + .05); g.gain.setValueAtTime(v, t1 - .05); g.gain.linearRampToValueAtTime(0, t1);
        s.start(t0); s.stop(t1 + .05); s.onended = function () { bp.disconnect(); g.disconnect(); };
      });
    };
    var fsk = function (t0, bits, f0, f1, v) {                                    // V.21 a 300 baudios: una sola osciladora, fase continua
      en(t0 - .1, function () {
        var o = u.osc('sine', f0), g = u.gain(0); o.connect(g).connect(linea);
        bits.forEach(function (b, i) { o.frequency.setValueAtTime(b ? f1 : f0, t0 + i / 300); });
        var t1 = t0 + bits.length / 300; g.gain.setValueAtTime(0, t0); g.gain.linearRampToValueAtTime(v, t0 + .005); g.gain.setValueAtTime(v, t1 - .005); g.gain.linearRampToValueAtTime(0, t1);
        o.start(t0); o.stop(t1 + .02); o.onended = function () { g.disconnect(); };
      });
    };
    var bitsDe = function (n, k) { var r = rngDe('bits' + k), b = []; for (var i = 0; i < n; i++) b.push(i % 10 === 0 ? 0 : i % 10 === 9 ? 1 : r() < .5 ? 1 : 0); return b; };
    var ansam = function (t0, t1, v) {                                            // 2100 Hz, AM a 15 Hz, inversión de fase cada 450 ms
      en(t0 - .1, function () {
        var o = u.osc('sine', 2100), am = u.osc('sine', 15), amg = u.gain(v * .2), g = u.gain(v), inv = u.gain(1);
        am.connect(amg).connect(g.gain); o.connect(inv).connect(g).connect(linea);
        for (var t = t0 + .45, s = -1; t < t1; t += .45, s = -s) inv.gain.setValueAtTime(s, t);
        g.gain.setValueAtTime(0, t0); g.gain.linearRampToValueAtTime(v, t0 + .01); g.gain.setValueAtTime(v, t1 - .01); g.gain.linearRampToValueAtTime(0, t1);
        [o, am].forEach(function (x) { x.start(t0); x.stop(t1 + .02); }); o.onended = function () { amg.disconnect(); g.disconnect(); inv.disconnect(); };
      });
    };
    var sondeo = function (t0, t1, v) {                                           // V.34: el peine de tonos de 150 a 3750 Hz (sin algunos)
      var fs = []; for (var k = 1; k <= 25; k++) if ([4, 6, 8, 10, 16].indexOf(k) < 0) fs.push(150 * k);
      tono(fs, t0, t1, v / Math.sqrt(fs.length));
    };
    // un saludo completo (comprimido con «x» < 1 para la reconexión)
    var saludo = function (b0, x, conMarcar) {
      var t = function (b) { return (b0 + b * x) * T; };
      if (conMarcar) {
        tono([425], t(0), t(1) - .05, .3);                                       // tono: el Freizeichen alemán
        marca(b0 + x, '0191011');                                                // pregunta: el número del proveedor
        tono([425], t(1.6), t(1.6) + 1, .28);                                    // un timbre (Rufton: 1 s)
      }
      var r0 = conMarcar ? 2 : 0;
      ansam(t(r0), t(r0 + 1.6), .35);                                            // respuesta
      fsk(t(r0 + 1.65), bitsDe(Math.round(.5 * x * T * 300), 1 + b0), 1650, 1850, .25);   // acuerdo: V.8 (la contestadora)
      fsk(t(r0 + 2), bitsDe(Math.round(.5 * x * T * 300), 2 + b0), 980, 1180, .25);       //          y quien llama
      tono([600, 1200], t(r0 + 2.5), t(r0 + 2.8), .2);                           // INFO (DPSK)
      sondeo(t(r0 + 2.85), t(r0 + 3.3), .6); sondeo(t(r0 + 3.45), t(r0 + 3.8), .6);
      arena(t(r0 + 3.9), t(r0 + 6), .4, 1700);                                   // arena: el entrenamiento
    };
    saludo(0, 1, true);
    arena(8 * T, 28 * T + 2 * S16, .04); arena(41 * T, 56 * T, .045);            // en línea: la arena se queda debajo, bajito
    // colgar: +++ (silencio de guarda), ATH0 y el clic del gancho; tono de marcar; marcar; el timbre al otro lado
    en(28.7 * T - .1, function () {
      var s = ctx.createBufferSource(), g = u.gain(0), hp = u.filtro('highpass', 900, .7); s.buffer = u.ruido(.05, 'clic'); s.connect(hp).connect(g).connect(bus);
      var t = 28.7 * T; g.gain.setValueAtTime(.8, t); g.gain.setTargetAtTime(0, t + .002, .006); s.start(t); s.stop(t + .05); s.onended = function () { hp.disconnect(); g.disconnect(); };
    });
    tono([425], 29 * T, 30 * T - .05, .3); marca(30, '00523847106');
    tono([425], 31 * T, 31 * T + 1, .28); tono([425], 31 * T + 2.5, 31 * T + 3.5, .22);
    for (var tt = 32 * T + .3; tt < 40 * T; tt += 2.12) tono([16000 / 4], tt, tt + .015, .08, 'square');   // pulsos de tarificación (0,12 por pulso a 3,40 el minuto)
    saludo(40, .2, false);                                                       // la reconexión: el saludo entero en un compás
  }

  /* ── 2. el break: bombo, caja crujiente, hats, ride; trip-hop a 84, drum'n'bass a 168; atasco; escobillas ── */
  function kit(ctx, dest, banco, en) {
    var u = U(ctx), rng = rngDe('kit'), lp = u.filtro('lowpass', 200, .9), bus = u.gain(.75); lp.connect(bus).connect(dest);
    for (var b = 0; b <= COMPASES; b += .25) lp.frequency.setTargetAtTime(curva('kitf', b), b * T, .2);
    var nz = u.ruido(1.2, 'kit');
    var bombo = function (t, v) {
      en(t - .05, function () {
        var o = u.osc('sine', 150), g = u.gain(0); o.connect(g).connect(lp);
        o.frequency.setValueAtTime(160, t); o.frequency.exponentialRampToValueAtTime(48, t + .09);
        g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(v, t + .002); g.gain.setTargetAtTime(0, t + .03, .14);
        o.start(t); o.stop(t + .7); o.onended = function () { g.disconnect(); };
      });
    };
    var ruido = function (t, v, tipo, f, q, tau, pan) {
      en(t - .05, function () {
        var s = ctx.createBufferSource(), fl = u.filtro(tipo, f, q), g = u.gain(0), p = u.paneo(pan || 0); s.buffer = nz;
        s.connect(fl).connect(g).connect(p).connect(lp);
        g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(v, t + .001); g.gain.setTargetAtTime(0, t + .003, tau);
        s.start(t, rng() * .9); s.stop(t + tau * 8 + .05); s.onended = function () { fl.disconnect(); g.disconnect(); p.disconnect(); };
      });
    };
    var caja = function (t, v) {
      ruido(t, v, 'bandpass', 2100, .8, .07, 0);
      en(t - .05, function () {
        var o = u.osc('triangle', 210), g = u.gain(0); o.connect(g).connect(lp);
        o.frequency.setValueAtTime(260, t); o.frequency.setTargetAtTime(190, t, .015);
        g.gain.setValueAtTime(v * .7, t); g.gain.setTargetAtTime(0, t + .005, .05); o.start(t); o.stop(t + .4); o.onended = function () { g.disconnect(); };
      });
    };
    var hat = function (t, v, abierto) { ruido(t, v, 'highpass', 7500, .7, abierto ? .14 : .025, .25); };
    var ride = function (t, v) { ruido(t, v, 'bandpass', 5200, 3, .35, -.3); };
    var sw = function (p) { return p % 2 ? .16 * S16 : 0; };                     // swing del trip-hop
    for (var b = 0; b < COMPASES; b++) {
      var k = MAPA[b].kit, t0 = b * T;
      if (k === 'trip') {
        [0, 7, 10].forEach(function (p) { bombo(t0 + p * S16 + sw(p), p ? .8 : 1); });
        [4, 12].forEach(function (p) { caja(t0 + p * S16 + .018, .9); });         // la caja, perezosa
        for (var p = 0; p < 16; p += 2) hat(t0 + p * S16 + sw(p / 2), p === 6 ? .3 : .18, p === 6);
        if (b % 2) caja(t0 + 15 * S16 + sw(15), .25);
      } else if (k === 'dnb' || k === 'dnb2' || k === 'arena') {
        // dos compases de 168 por cada compás de 84: el 2-step con fantasmas, y variación cada segundo medio compás
        for (var h = 0; h < 2; h++) {
          var th = t0 + h * 16 * S32, var_ = (b * 2 + h) % 4 === 3;
          (var_ ? [0, 2, 10] : [0, 10]).forEach(function (p) { bombo(th + p * S32, p ? .85 : 1); });
          (var_ ? [4, 12, 15] : [4, 12]).forEach(function (p) { caja(th + p * S32, p === 15 ? .5 : .95); });
          [7, 9, 14].forEach(function (p) { if (rng() < .7) caja(th + p * S32, .22); });   // fantasmas
          for (var q = 0; q < 16; q++) hat(th + q * S32, q % 4 === 2 ? .2 : .1, q === 14 && var_);
          if (k === 'dnb2') for (q = 0; q < 16; q += 4) ride(th + q * S32, .16);   // 33 600: el ride encima
        }
      } else if (k === 'atasco') {
        // 21:17:02 atasco ×3: el primer tiempo, tres veces idéntico, y un tiempo de silencio
        for (var r = 0; r < 3; r++) { var tr = t0 + r * 4 * S16; bombo(tr, 1); caja(tr + 2 * S16, .9); hat(tr + S16, .2); hat(tr + 3 * S16, .2); }
      } else if (k === 'escobilla') {
        // la llamada: escobillas (ruido largo y suave) y un bombo apagado en el uno
        bombo(t0, .5);
        for (p = 0; p < 16; p += 4) ruido(t0 + p * S16 + sw(p), .12, 'bandpass', 3800, .6, .16, -.2);
        caja(t0 + 12 * S16 + .02, .3);
      }
    }
  }

  /* ── 3. el bajo: sub de trip-hop (raíces largas con deslizamiento) y Reese de drum'n'bass (dos sierras desafinadas) ── */
  function bajo(ctx, dest, banco, en) {
    var u = U(ctx), bus = u.gain(.55); bus.connect(dest);
    for (var b = 0; b < COMPASES; b++) (function (b) {
      var d = curva('bajo', b + .5); if (d < .05) return;
      var M = MAPA[b], raiz = ACORDE[M.acorde][0], f = hz(raiz < 34 ? raiz + 12 : raiz) / 2, t0 = b * T, reese = M.kit === 'dnb' || M.kit === 'dnb2';
      if (b > 0 && MAPA[b - 1].acorde === M.acorde && !reese) return;            // en trip-hop la nota se queda dos compases
      var largo = reese ? T : (b + 1 < COMPASES && MAPA[b + 1].acorde === M.acorde ? 2 * T : T);
      en(t0 - .1, function () {
        var g = u.gain(0), lp = u.filtro('lowpass', reese ? 420 : 250, reese ? 3 : .7); lp.connect(g).connect(bus);
        var oscs = reese ? [u.osc('sawtooth', f * 1.006), u.osc('sawtooth', f * .994), u.osc('sine', f)] : [u.osc('sine', f), u.osc('triangle', f * 2)];
        var gains = reese ? [.25, .25, .8] : [1, .08];
        oscs.forEach(function (o, i) { var gg = u.gain(gains[i]); o.connect(gg).connect(lp); o.start(t0); o.stop(t0 + largo + .2); o.onended = function () { gg.disconnect(); }; });
        if (reese) { var lfo = u.osc('sine', .35), lg = u.gain(260); lfo.connect(lg).connect(lp.frequency); lfo.start(t0); lfo.stop(t0 + largo + .2); lfo.onended = function () { lg.disconnect(); }; }
        else { oscs[0].frequency.setValueAtTime(f * .94, t0); oscs[0].frequency.setTargetAtTime(f, t0, .04); }   // el deslizamiento del sub
        g.gain.setValueAtTime(0, t0); g.gain.linearRampToValueAtTime(d, t0 + .02); g.gain.setValueAtTime(d, t0 + largo - .06); g.gain.linearRampToValueAtTime(0, t0 + largo);
        oscs[0].onended = function () { lp.disconnect(); g.disconnect(); };
      });
    })(b);
  }

  /* ── 4. Rhodes con trémolo (trip-hop y la llamada) y 5. cuerdas de máquina ── */
  function rhodes(ctx, dest, banco, en) {
    var u = U(ctx), bus = u.gain(.3), trem = u.gain(1), lfo = u.osc('sine', 4.2), lg = u.gain(.35), pan = u.paneo(.15);
    lfo.connect(lg).connect(trem.gain); trem.connect(pan).connect(bus).connect(dest); lfo.start(0); lfo.stop(DURACION);
    var nota = function (m, t, v, largo) {
      en(t - .05, function () {
        var f = hz(m), car = u.osc('sine', f), mod = u.osc('sine', f), idx = u.gain(0), amp = u.gain(0), bell = u.osc('sine', f * 14), bg = u.gain(0);
        mod.connect(idx).connect(car.frequency); car.connect(amp); bell.connect(bg).connect(amp); amp.connect(trem);
        idx.gain.setValueAtTime(f * 1.9 * v, t); idx.gain.setTargetAtTime(f * .3, t + .005, .3);
        bg.gain.setValueAtTime(v * .07, t); bg.gain.setTargetAtTime(0, t + .002, .03);
        amp.gain.setValueAtTime(0, t); amp.gain.linearRampToValueAtTime(v, t + .004); amp.gain.setTargetAtTime(v * .45, t + .01, .5); amp.gain.setTargetAtTime(0, t + largo, .15);
        [car, mod, bell].forEach(function (o) { o.start(t); o.stop(t + largo + 1); }); car.onended = function () { idx.disconnect(); amp.disconnect(); bg.disconnect(); };
      });
    };
    for (var b = 0; b < COMPASES; b++) {
      var d = curva('rhodes', b + .5); if (d < .05) continue;
      var ns = notasDe(MAPA[b].acorde).slice(1).map(function (m) { while (m < 55) m += 12; while (m > 75) m -= 12; return m; }).sort(function (a, c) { return a - c; });
      var ns2 = b + 1 < COMPASES ? notasDe(MAPA[b + 1].acorde).slice(1).map(function (m) { while (m < 55) m += 12; while (m > 75) m -= 12; return m; }) : ns;
      ns.forEach(function (m, i) { nota(m, b * T + i * .012, .4 * d, 9 * S16); });
      if (MAPA[b + 1] && MAPA[b + 1].acorde !== MAPA[b].acorde) ns2.forEach(function (m, i) { nota(m, b * T + 14 * S16 + i * .012, .3 * d, 2 * S16); });   // anticipa
      else ns.slice(0, 3).forEach(function (m, i) { nota(m, b * T + 10 * S16 + .02 + i * .012, .22 * d, 4 * S16); });
    }
  }
  function cuerdas(ctx, dest, banco, en) {
    var u = U(ctx), bus = u.gain(.12); bus.connect(dest);
    for (var b = 0; b < COMPASES; b++) (function (b) {
      var d = curva('pad', b + .5); if (d < .05) return;
      if (b > 0 && MAPA[b - 1].acorde === MAPA[b].acorde) return;
      var b1 = b; while (b1 + 1 < COMPASES && MAPA[b1 + 1].acorde === MAPA[b].acorde) b1++;
      var t0 = b * T, t1 = (b1 + 1) * T, ns = notasDe(MAPA[b].acorde).map(function (m) { while (m < 48) m += 12; while (m > 70) m -= 12; return m; });
      en(t0 - .3, function () {
        var lp = u.filtro('lowpass', 1400, .6), g = u.gain(0); lp.connect(g).connect(bus);
        ns.forEach(function (m, i) { [-7, 7].forEach(function (c) { var o = u.osc('sawtooth', hz(m)); o.detune.value = c + (i % 2 ? 3 : -3); o.connect(lp); o.start(t0 - .2); o.stop(t1 + 1.2); }); });
        g.gain.setValueAtTime(0, t0 - .2); g.gain.linearRampToValueAtTime(d, t0 + .6); g.gain.setValueAtTime(d, t1 - .1); g.gain.linearRampToValueAtTime(0, t1 + 1);
        en(t1 + 2, function () { lp.disconnect(); g.disconnect(); });
      });
    })(b);
  }

  /* ── 6. las voces: [quién, compás, 'sílaba:grado:16avos …'] sobre Do eólico. A = ardilla ligera (coros, cortes),
   * G = grave (PSOLA: versos, quien llama), T = Doina al teléfono (se filtra a voz de teléfono en la mezcla) ── */
  var ESCALA = [0, 2, 3, 5, 7, 8, 10], BASE = { A: 60, G: 48, T: 60 };
  var grado = function (g, base) { return base + ESCALA[((g % 7) + 7) % 7] + 12 * Math.floor(g / 7); };
  var L = function (s) { return s.split(' ').map(function (x) { var p = x.split(':'); return [p[0].replace(/_/g, ' '), +p[1], +p[2]]; }); };
  var C1 = 'la:4:2 no:5:2 ti:6:2 cia:5:2 más:7:6 im:6:2 por:5:2 tan:4:2 te:3:12';
  var C2 = 'de_u:2:2 na:3:2 no:4:2 che:5:2 so:4:1 bre:3:1 co:4:1 mu:5:1 ni:6:1 ca:7:1 ción:6:2 pla:5:2 ne:4:2 ta:3:2 ria:2:10';
  var C3 = 'es:4:2 que_el:5:2 pe:7:4 rro:6:4 ce:5:4 nó:4:16';
  var C4 = 'el:7:1 pe:9:1 rro:8:2 ce:7:2 nó:7:2 el:7:1 pe:9:1 rro:8:2 ce:7:2 nó:4:10 ~:0:8';
  var ECO = 'es:2:2 que_el:3:2 pe:4:4 rro:3:4 ce:2:4 nó:0:16';
  var ATASCO = 'a:4:1 tas:4:1 co:4:2 a:4:1 tas:4:1 co:4:2 a:4:1 tas:4:1 co:4:2 ~:0:4';
  var LETRA = [
    ['G', 8, 'sie:4:2 te:4:2 do:4:2 ce:3:2 se:4:1 a:4:1 bre:5:2 la:4:2 puer:3:1 ta:2:1'],
    ['G', 9, 'sie:4:1 te:4:1 do:4:1 ce:3:1 cua:4:1 ren:5:1 ta:4:1 se:3:1 en:2:1 cien:3:2 de:2:1 la:1:1 pri:2:1 me:1:1 ra:0:1'],
    ['G', 10, 'nue:4:1 ve:4:1 ce:4:1 ro:4:1 tres:5:2 lle:4:1 gan:3:1 cua:4:2 tro:2:6'],
    ['G', 11, 'lle:2:2 gó:3:2 la:4:1 quin:5:3 ta:4:2 an:3:2 tes:2:4'],
    ['G', 12, 'on:4:2 ce:4:2 vein:5:2 ti:4:2 séis:3:8'],
    ['A', 13, 'jand:7:2 cheik:6:6 jand:7:2 cheik:6:6'],
    ['G', 14, 'tre:4:1 ce:4:1 cua:4:1 ren:5:1 ta:4:4 na:3:1 die:4:1 es:3:1 cri:2:1 be:3:4'],
    ['A', 15, 'jand:7:2 cheik:6:2 o:8:4 kei:7:8'], ['G', 15, 'al:2:1 guien:3:1 es:4:2 cri:3:2 be:2:2 man:3:2 cha:2:2 do:0:4'],
    ['A', 16, C1], ['A', 18, C2], ['A', 20, C3], ['G', 20, C3, -2], ['A', 22, C4], ['G', 22, ECO],
    ['G', 24, ATASCO], ['A', 25, ATASCO],
    ['T', 32, 'te:4:2 es:5:2 pe:6:2 ra:5:2 en:4:2 la:3:2 puer:4:2 ta:2:2'],
    ['T', 33, 'a:2:2 la:3:2 ho:4:2 ra_en:5:2 que:4:2 lle:3:2 ga:2:2 bas:1:2'],
    ['G', 34, 'le:4:2 di:5:2 go:4:2 que_en:3:2 diez:5:4 dí:4:2 as:2:2'],
    ['T', 35, 'me:5:2 di:6:2 ce:5:2 que:4:1 se:4:1 lo:3:2 di:4:2 ga_a:3:2 él:2:2'],
    ['G', 36, 'a:2:2 cer:3:2 ca_el:4:2 te:5:2 lé:6:2 fo:5:2 no_al:4:2 sue:3:1 lo:2:1'],
    ['G', 37, 'yo:4:2 di:5:2 go:4:2 su:3:2 nom:5:2 bre_a:4:2 u:3:1 na:2:1 sa:3:1 la:2:1'],
    ['G', 38, 'lle:2:1 na:3:1 de:4:1 gen:5:1 te:4:1 que:3:1 ha:4:1 bla:3:1 de_in:2:1 fra_es:3:1 truc:4:1 tu:5:1 ras:4:1 glo:3:1 ba:2:1 les:1:1'],
    ['G', 39, 'y_él:2:2 no:3:2 se:4:2 des:3:2 pier:2:4 ta:0:4'],
    ['A', 41, C1], ['A', 43, C2], ['G', 43, C2, -2], ['A', 45, C3], ['G', 45, C3, -2], ['A', 47, C4], ['G', 47, ECO],
    ['A', 49, C3], ['G', 49, C3, -2], ['A', 51, 'es:4:2 que_el:5:2 pe:7:4 rro:6:4 ce:5:4 nó:4:16'], ['G', 51, ECO]
  ];
  var DICHO = [['G', 26.15, 'la línea baja a la mitad', 41], ['A', 28.05, 'más más más', 67], ['G', 28.35, 'a te hache cero', 45],
               ['G', 53.05, 'llamar cuesta tres cuarenta el minuto', 45], ['G', 54.1, 'hablé nueve minutos', 45],
               ['G', 55.0, 'copia', 45], ['G', 55.25, 'copia', 45], ['G', 55.55, 'expulsar', 43]];
  function partitura() {
    return LETRA.map(function (r) {
      var t = r[1] * T;
      return { quien: r[0], compas: r[1], eventos: L(r[2]).map(function (w) { var e = { t: t, dur: w[2] * S16, texto: w[0], nota: grado(w[1] + (r[3] || 0), BASE[r[0]]) }; t += e.dur; return e; })
        .filter(function (e) { return e.texto !== '~'; }) };
    });
  }
  function voces(quien) {
    return function (ctx, dest, banco, en) {
      if (!banco) return;
      partitura().forEach(function (r, k) {
        if (r.quien !== quien) return;
        var op = quien === 'G' ? { modo: 'psola', vibrato: [4.6, .005], rng: rngDe('g' + k), agendar: en } : { porPalabra: true, rng: rngDe(quien + k), agendar: en };
        banco.cantar(dest, r.eventos, op);
      });
      DICHO.forEach(function (d) { if (d[0] === quien) banco.decir(dest, d[1] * T, d[2], d[0] === 'A' ? { nota: d[3], porPalabra: true, agendar: en } : { nota: d[3], modo: 'psola', agendar: en }); });
    };
  }

  var PISTAS = { modem: modem, kit: kit, bajo: bajo, rhodes: rhodes, cuerdas: cuerdas, ardilla: voces('A'), grave: voces('G'), telefono: voces('T') };
  global.Cancion = { PISTAS: Object.keys(PISTAS), pista: function (n) { return PISTAS[n]; }, partitura: partitura, MAPA: MAPA, SECC: SECC, curva: curva,
                     DURACION: DURACION, T: T, S16: S16, COMPASES: COMPASES, BPM: BPM, hz: hz,
                     usaBanco: function (n) { return n === 'ardilla' || n === 'grave' || n === 'telefono'; } };
})(typeof window !== 'undefined' ? window : globalThis);
