/* sonido.js — la música de «la portadora» (loop D: el compositor algorítmico).
 *
 * Loop B tenía un solo motor y por eso todas las tiradas sonaban igual (mismo tempo, mismo La, mismo groove,
 * misma forma). Ahora cada semilla genera el GENOMA de una canción:
 *   estilo     funk de una nota · ethio-groove · きくお · ambient espectral · electro raro 80s
 *   tempo, compás (pasos por compás: 16 = 4/4, 12 = 12/8, 14 = 7/8, 20 = 5/4), tónica de la portadora
 *   groove     ritmos euclidianos por banda (bajo, palmada, brillo), rotados; swing; coherencia
 *   forma      una sección por verso (A A B A, A B A C…), cada una con su transposición y su densidad
 *   orquesta   de una paleta: portadora · bajo elástico · bajo FM · batería de máquina · órgano · pared
 *              espectral (Grisey) · arpegios · stabs FM
 * Encima siguen las voces del poema (nave, eco, tierra, telemetría) y la tipografía como partitura.
 * Loop E: cada estilo trae su MEZCLA (graves, agudos, techo, saturación, compresión, sala, niveles por instrumento)
 * y su VOZ (registro, formante, onda, vibrato, portamento, aliento; el electro canta en escalones de robot).
 * Todo el azar sale de la semilla: misma semilla = misma canción. El audio sólo arranca con un gesto.
 */
(function (global) {
  'use strict';
  var QENET = { tizita: [0, 2, 3, 7, 8], bati: [0, 4, 5, 7, 11], ambassel: [0, 1, 5, 7, 8], anchihoye: [0, 1, 5, 6, 9] };
  var VOC = { a: [800, 1250, 2700], e: [480, 1950, 2750], i: [310, 2500, 3200], o: [500, 900, 2650], u: [340, 760, 2500] };
  var PARCIALES = { bajo: [[.5, .5], [1, 1], [2, .75], [3, .4]], medio: [[4, .45], [5, .26], [6, .28], [7, .38], [8, .2], [10, .18], [12, .16], [14, .18]],
                    alto: [[19, .12], [22, .07], [26, .05], [33, .035], [38, .035], [44, .025]] };
  var TAU = { bajo: .17, medio: .075, alto: .03 };
  var COMB = /[̀-ͯ]/g;
  var hz = function (midi) { return 440 * Math.pow(2, (midi - 69) / 12); };

  // ─────────── el genoma ───────────
  var ESTILOS = {
    'funk de una nota': { bpm: [96, 110], pasos: [16, 16, 14], tonica: [31, 36], forma: ['AABA', 'AAB', 'ABAB'], swing: [.06, .14], coh: [.75, 1],
                          orquesta: ['portadora', 'elastico', 'bateria'], extra: ['fm', 'stabs', 'pared'], portadora: 1, voz: 1 },
    'ethio-groove':     { bpm: [104, 124], pasos: [12, 12, 16], tonica: [33, 40], forma: ['AABB', 'ABAC', 'AAB'], swing: [0, .05], coh: [.8, 1],
                          orquesta: ['organo', 'fm', 'bateria'], extra: ['portadora', 'arpegio'], portadora: .45, voz: 1.05 },
    'きくお':            { bpm: [148, 176], pasos: [16, 14, 16], tonica: [35, 42], forma: ['ABAC', 'ABCB', 'AABC'], swing: [0, .03], coh: [.85, 1],
                          orquesta: ['arpegio', 'bateria', 'fm'], extra: ['stabs', 'portadora'], portadora: .35, voz: 1.18 },
    'ambient espectral':{ bpm: [60, 72], pasos: [20, 16, 20], tonica: [26, 33], forma: ['ABA', 'AAB', 'ABBA'], swing: [0, .02], coh: [.25, .6],
                          orquesta: ['portadora', 'pared'], extra: ['elastico'], portadora: 1.15, voz: .92 },
    'electro raro 80s': { bpm: [108, 122], pasos: [16, 14, 16], tonica: [31, 38], forma: ['AABA', 'ABAB', 'AABC'], swing: [.02, .08], coh: [.8, 1],
                          orquesta: ['bateria', 'fm', 'stabs'], extra: ['arpegio', 'portadora', 'organo'], portadora: .4, voz: 1 }
  };

  // la mezcla de cada estilo (loop E): no sólo otras notas, otro cuerpo. graves/agudos en dB (estantes),
  // techo = paso bajo final, drive = saturación, sala = [cola s, envío, afinado], niveles por instrumento,
  // voz = registro (semitonos), formante, onda, vibrato [Hz, profundidad], portamento (s), aliento (ruido), robot
  var MEZCLA = {
    'funk de una nota': { graves: 4, agudos: 0, techo: 12000, drive: 1.4, comp: 4, sala: [1.8, .4, .55],
                          niveles: { portadora: 1.1, elastico: 1.3, bateria: 1.1, fm: 1, stabs: .8, pared: .7, voz: .95 },
                          voz: { registro: -5, formante: .95, onda: 'sawtooth', vib: [5.2, 1], port: .03, aliento: .05 } },
    'ethio-groove':     { graves: 1, agudos: -2, techo: 9000, drive: 2.2, comp: 3, sala: [2.2, .5, .5],
                          niveles: { organo: 1.7, fm: 1.1, bateria: .9, portadora: .9, arpegio: .8, voz: 1 },
                          voz: { registro: 0, formante: 1.06, onda: 'sawtooth', vib: [6.2, 1.3], port: .04, aliento: .03, nasal: true } },
    'きくお':            { graves: -3, agudos: 7, techo: 16000, drive: 1.8, comp: 7, sala: [.9, .22, .3],
                          niveles: { arpegio: 2.2, bateria: 1.2, stabs: 1.4, fm: .9, portadora: .7, voz: 1.15 },
                          voz: { registro: 7, formante: 1.25, onda: 'square', vib: [7.2, .8], port: .012, aliento: 0 } },
    'ambient espectral':{ graves: 2, agudos: -6, techo: 5200, drive: 1, comp: 2, sala: [6, 1.2, .85],
                          niveles: { portadora: 1.25, pared: 1.6, elastico: .7, voz: 1.25 },
                          voz: { registro: -2, formante: .9, onda: 'triangle', vib: [3.8, 2.2], port: .09, aliento: .35,
                                  psola: true, registroDifonos: -12, nivelDifonos: 1.7 } },   // grave y humana: la ardilla aclaraba de más
    'electro raro 80s': { graves: 2, agudos: 6, techo: 15000, drive: 1.6, comp: 5, sala: [1.2, .45, .2], compuerta: true,
                          niveles: { bateria: 1.7, stabs: 1.9, fm: 1.1, arpegio: 1.1, organo: .9, portadora: .8, voz: 1 },
                          voz: { registro: 0, formante: 1.1, onda: 'square', vib: [0, 0], port: .0015, aliento: 0, robot: true } }
  };

  function euclides(k, n, rot) {                     // k golpes repartidos lo más parejo posible en n pasos, rotados
    var out = [];
    for (var j = 0; j < k; j++) out.push((Math.floor(j * n / k) + rot) % n);
    return out.sort(function (a, b) { return a - b; });
  }

  function genoma(P, rngDe) {
    var r = rngDe(P.semilla + '·cancion'), entre = function (a) { return a[0] + r() * (a[1] - a[0]); }, de = function (xs) { return xs[Math.floor(r() * xs.length)]; };
    var nombres = Object.keys(ESTILOS), estilo = de(nombres), E = ESTILOS[estilo];
    var pasos = de(E.pasos), bpm = Math.round(entre(E.bpm) * 4) / 4, tonica = Math.round(entre(E.tonica));
    var groove = {}, golpe = function (k, rot, fuerte) { var o = {}; euclides(k, pasos, rot).forEach(function (p, i) { o[p] = i === 0 ? 1 : fuerte ? .55 + .4 * r() : .3 + .4 * r(); }); return o; };
    groove.bajo = golpe(Math.max(2, Math.round(pasos * (.25 + .2 * r()))), Math.floor(r() * 3), true); groove.bajo[0] = 1;
    groove.medio = {}; groove.medio[Math.round(pasos / 4)] = .9; groove.medio[Math.round(pasos * 3 / 4)] = 1;      // la palmada: 2 y 4 (o donde caiga en el compás)
    if (r() < .5) groove.medio[pasos - 1 - Math.floor(r() * 2)] = .3;
    groove.alto = golpe(Math.round(pasos * (.4 + .45 * r())), Math.floor(r() * pasos), false);
    var forma = de(E.forma), lineas = P.lineas - 2, secciones = [];
    var transporte = { A: 0, B: de([5, -2, 7, 3]), C: de([-5, 2, 6, -3]) };
    if (estilo === 'きくお') transporte.B = 6;                 // el tritono: el color se rompe de golpe
    for (var i = 0; i < lineas; i++) {
      var letra = forma[Math.min(forma.length - 1, Math.floor(i * forma.length / Math.max(1, lineas)))];
      secciones.push({ letra: letra, transporte: transporte[letra], densidad: letra === 'A' ? .75 : letra === 'B' ? 1 : .55 });
    }
    var orquesta = E.orquesta.slice();
    E.extra.forEach(function (x) { if (r() < .45 && orquesta.indexOf(x) < 0) orquesta.push(x); });
    // la portadora suena SIEMPRE (es la pieza: el tono que queda). Sin ella, la intro del electro era silencio
    if (orquesta.indexOf('portadora') < 0) orquesta.push('portadora');
    var porVerso = bpm > 140 ? 4 : bpm < 75 ? 1 : 2;
    return { estilo: estilo, bpm: bpm, pasos: pasos, tonica: tonica, f0: hz(tonica), groove: groove, swing: entre(E.swing), coh: E.coh,
             forma: forma, secciones: secciones, orquesta: orquesta, porVerso: porVerso, intro: 1,   // un compás: con dos, la pieza tardaba en oírse (Canek: «no oigo nada hasta bien adentro»)
             pesoPortadora: E.portadora, voz: E.voz, escala: QENET[P.qenet] || QENET.tizita, mezcla: MEZCLA[estilo] };
  }

  // ─────────── la partitura: cuándo pasa cada cosa (la cabeza lectora visual usa los mismos tiempos) ───────────
  function partitura(P, rngDe) {
    var g = genoma(P, rngDe), rng = rngDe(P.semilla + '·partitura');
    var S16 = 60 / g.bpm / 4, T = g.pasos * S16, INTRO = g.intro, POR = g.porVerso, cupo = g.pasos * POR - 5;
    var pasos = [], ecos = [], tierra = [], maquina = [];
    P.voces.nave.forEach(function (l, i) {
      var t0 = (INTRO + i * POR) * T, partes = l.texto.split(/(\s+)/), pos = 0, w = 0;
      var largos = partes.map(function (x) { return /^\s+$/.test(x) ? Math.min(6, Math.floor(x.length / 3)) : Math.max(2, Math.min(5, (x.replace(COMB, '').match(/[aeiouáéíóúü]/gi) || []).length * 1.5 | 0)); });
      var total = largos.reduce(function (a, b) { return a + b; }, 0) || 1, cabe = cupo / total;
      partes.forEach(function (x, k) {
        if (!x) return;
        var d = Math.max(1, Math.round(largos[k] * Math.min(1.6, cabe)));
        if (/^\s+$/.test(x)) { if (x.length >= 3) pasos.push({ t: t0 + pos * S16, dur: d * S16, linea: i, hueco: true }); pos += d; return; }
        var adel = pos > 0 && rng() < .25 ? -.5 : 0;
        pasos.push({ t: t0 + (pos + adel) * S16, dur: d * S16, linea: i, palabra: w, texto: x, lejania: l.lejania,
                     eje: l.eje >= 0 && l.texto.indexOf(x) <= l.eje && l.eje < l.texto.indexOf(x) + x.length });
        pos += d; w++;
      });
    });
    P.voces.eco.forEach(function (e) { ecos.push({ t: (INTRO + e.llega * POR + POR / 2) * T, texto: e.texto, retraso: e.retraso, linea: e.llega }); });
    P.voces.tierra.forEach(function (x) { tierra.push({ t: (INTRO + x.linea * POR + POR * .62) * T, texto: x.texto, linea: x.linea }); });
    P.voces.maquina.forEach(function (x) { maquina.push({ t: (INTRO + x.linea * POR) * T, texto: x.texto, linea: x.linea }); });
    return { pasos: pasos, ecos: ecos, tierra: tierra, maquina: maquina, compases: INTRO + P.lineas * POR + 3, T: T, S16: S16, genoma: g, f0: g.f0 };
  }

  // ─────────── el motor ───────────
  // la voz de la nave y de la tierra: el banco de difonos (vendor/difonos, copia de herramientas/agent/difonos)
  var BANCO_DIFONOS = 'vendor/difonos/bancos/sabina-1-b44e7fab5cee/';

  function Sonido(ctx, P, rngDe, destino, banco) {
    this.banco = banco || null;                 // si no hay banco (o no cargó), la nave canta con la voz de formantes
    this.ctx = ctx; this.P = P; this.rngDe = rngDe; this.nodos = []; this.fuentes = [];
    this.Q = partitura(P, rngDe); this.G = this.Q.genoma; this.T = this.Q.T; this.S16 = this.Q.S16;
    this.escala = this.G.escala;
    this.salida = destino || ctx.destination;
    // en vivo, la voz no se arma toda al clic: se agenda y cada pieza nace ~2 s antes de sonar (ver S.agendar)
    this.vivo = !(typeof OfflineAudioContext !== 'undefined' && ctx instanceof OfflineAudioContext);
    this.cola = []; this.reloj = null;
  }
  var S = Sonido.prototype;

  // agendador de la voz: armar todos los granos de difonos al clic eran miles de nodos conectados y el hilo de audio
  // no alcanzaba (en vivo el reloj corría a 0.3-0.8× con 3861 cortes en 44 s: sólo se oía el final, medido)
  S.agendar = function (t, f) {
    if (!this.vivo) return this.adoptar(f());
    this.cola.push([t, f]); this.ordenada = false;
    if (this.reloj) return;
    var me = this;
    this.reloj = setInterval(function () {
      if (!me.ordenada) { me.cola.sort(function (a, b) { return a[0] - b[0]; }); me.ordenada = true; }
      var hasta = me.ctx.currentTime + 2;      // 2 s: aguanta la pestaña en segundo plano (timers a 1 s)
      while (me.cola.length && me.cola[0][0] < hasta) me.adoptar(me.cola.shift()[1]());
      if (!me.cola.length) { clearInterval(me.reloj); me.reloj = null; }
    }, 120);
  };

  S.n = function (nodo) { this.nodos.push(nodo); return nodo; };
  S.f = function (nodo) { this.fuentes.push(nodo); return this.n(nodo); };
  S.gain = function (v) { var g = this.n(this.ctx.createGain()); g.gain.value = v == null ? 1 : v; return g; };
  S.paneo = function (p) { var x = this.n(this.ctx.createStereoPanner()); x.pan.value = p; return x; };
  S.filtro = function (tipo, f, q) { var b = this.n(this.ctx.createBiquadFilter()); b.type = tipo; b.frequency.value = f; if (q != null) b.Q.value = q; return b; };
  S.osc = function (tipo, f) { var o = this.f(this.ctx.createOscillator()); o.type = tipo; o.frequency.value = f; return o; };
  S.ruido = function (seg, semilla) {
    var ctx = this.ctx, n = Math.ceil(seg * ctx.sampleRate), buf = ctx.createBuffer(1, n, ctx.sampleRate), d = buf.getChannelData(0), r = this.rngDe(semilla);
    for (var i = 0; i < n; i++) d[i] = r() * 2 - 1;
    return buf;
  };
  S.fin = function () { return this.t0 + this.Q.compases * this.T + 3; };
  // la sección (A/B/C) que suena en el compás b; intro y coda cuentan como A en reposo
  S.seccion = function (b) {
    var i = Math.floor((b - this.G.intro) / this.G.porVerso), sc = this.G.secciones;
    if (i < 0) return { letra: 'intro', transporte: 0, densidad: .4 };
    if (i >= sc.length) return { letra: 'coda', transporte: sc.length ? sc[sc.length - 1].transporte : 0, densidad: .3 };
    return sc[i];
  };
  S.lejaniaEn = function (b) {
    var i = Math.floor((b - this.G.intro) / this.G.porVerso), nv = this.P.voces.nave;
    return i < 0 ? 0 : i >= nv.length ? nv[nv.length - 1].lejania : nv[i].lejania;
  };
  S.tiene = function (x) { return this.G.orquesta.indexOf(x) >= 0; };

  // la sala afinada en la tónica de la canción (Lucier), normalizada por su respuesta en los armónicos
  // las muestras de la sala afinada: función pura (sin contexto de audio) y con caché, para calcularla antes del
  // clic (medido: 398 ms al clic, y el primer compás quedaba agendado en el pasado)
  var cacheSala = {};
  function datosSala(rngDe, F0, cola, afinado, compuerta, sr) {
    cola = cola || 2.6; afinado = afinado == null ? 1 : afinado;
    var clave = [F0.toFixed(3), cola, afinado, !!compuerta, sr].join('|');
    if (cacheSala[clave]) return cacheSala[clave];
    var n = Math.floor(cola * sr), r = rngDe('sala'), canales = [];
    for (var c = 0; c < 2; c++) {
      var d = new Float32Array(n);
      for (var k = 1; k <= 70; k++) {
        var f = F0 * k, a = .5 / Math.sqrt(k) * afinado, tau = .9 * cola / 2.6 / (1 + k / 25), ph = r() * 6.283;
        if (f > 9000) break;
        for (var i = 0; i < n; i++) { var t = i / sr; d[i] += a * Math.sin(6.283 * f * t + ph) * Math.exp(-t / tau); }
      }
      for (var j = 0; j < n; j++) { var tt = j / sr; d[j] += (r() * 2 - 1) * .35 * Math.exp(-tt * 3.2 * 2.6 / cola); d[j] *= Math.min(1, j / (sr * .012));
        if (compuerta && tt > .22) d[j] *= Math.max(0, 1 - (tt - .22) / .02); }
      var maxH = 0;
      for (var q = 1; q <= 24; q++) {
        var re = 0, im = 0, w = 6.283185 * F0 * q / sr;
        for (var z = 0; z < n; z += 2) { re += d[z] * Math.cos(w * z); im -= d[z] * Math.sin(w * z); }
        maxH = Math.max(maxH, 2 * Math.sqrt(re * re + im * im));
      }
      for (var m = 0; m < n; m++) d[m] /= maxH;
      canales.push(d);
    }
    return (cacheSala[clave] = canales);
  }
  function prepararSala(P, rngDe, sr) {
    var g = genoma(P, rngDe); datosSala(rngDe, g.f0, g.mezcla.sala[0], g.mezcla.sala[2], g.mezcla.compuerta, sr || 48000);
  }

  S.sala = function (cola, afinado) {
    var ctx = this.ctx, sr = ctx.sampleRate, d = datosSala(this.rngDe, this.G.f0, cola, afinado, this.G.mezcla.compuerta, sr);
    var buf = ctx.createBuffer(2, d[0].length, sr); buf.copyToChannel(d[0], 0); buf.copyToChannel(d[1], 1);
    var cv = this.n(ctx.createConvolver()); cv.normalize = false; cv.buffer = buf; return cv;
  };

  S.montar = function (t0) {
    var ctx = this.ctx, me = this, M = this.G.mezcla;
    this.t0 = t0;
    // la cadena de salida del estilo: saturación → estantes de graves y agudos → techo → compresor → limitador
    var sat = this.n(ctx.createWaveShaper()), cv = new Float32Array(2048);
    for (var i = 0; i < 2048; i++) { var x = i / 1023.5 - 1; cv[i] = Math.tanh(M.drive * x) / Math.tanh(M.drive); }
    sat.curve = cv;
    var gr = this.filtro('lowshelf', 110, null); gr.gain.value = M.graves;
    var ag = this.filtro('highshelf', 3800, null); ag.gain.value = M.agudos;
    var techo = this.filtro('lowpass', M.techo, .6);
    var comp = this.n(ctx.createDynamicsCompressor());
    comp.threshold.value = -18; comp.ratio.value = M.comp; comp.attack.value = .006; comp.release.value = .16;
    var lim = this.n(ctx.createDynamicsCompressor());
    lim.threshold.value = -4; lim.knee.value = 0; lim.ratio.value = 20; lim.attack.value = .002; lim.release.value = .08;
    this.master = this.gain(.5); this.master.connect(sat).connect(gr).connect(ag).connect(techo).connect(comp).connect(lim);
    lim.connect(this.gain(.89)).connect(this.salida);
    this.analizador = this.n(ctx.createAnalyser()); this.analizador.fftSize = 4096; lim.connect(this.analizador);
    this.envio = this.gain(M.sala[1]); this.envio.connect(this.sala(M.sala[0], M.sala[2])).connect(this.master);
    // cada instrumento escribe en su propio bus (su nivel en la mezcla del estilo): se cambia master un momento
    var real = this.master, conBus = function (nombre, f) {
      me.master = me.gain(M.niveles[nombre] == null ? 1 : M.niveles[nombre]); me.master.connect(real); f(); me.master = real;
    };
    var INST = { portadora: 'portadora', elastico: 'bajo', fm: 'bajoFM', bateria: 'bateria', organo: 'organo', pared: 'pared', arpegio: 'arpegio', stabs: 'stabs' };
    this.G.orquesta.forEach(function (x) { conBus(x, function () { me[INST[x]](); }); });
    conBus('voz', function () { me.nave(); me.ecos(); me.tierra(); });
    this.maquina();
    return this.Q.compases * this.T;
  };

  // ── la portadora: la tónica de la canción y su serie en tres bandas; el groove (euclidiano) son sus envolventes ──
  S.portadora = function () {
    var ctx = this.ctx, me = this, t0 = this.t0, C = this.Q.compases, T = this.T, S16 = this.S16, G = this.G, rng = this.rngDe(this.P.semilla + '·groove');
    Object.keys(PARCIALES).forEach(function (banda) {
      var bus = me.gain(0), pan = me.paneo(banda === 'alto' ? .25 : banda === 'medio' ? -.15 : 0);
      // en la intro la portadora suena a volumen de cuerpo (en los estilos donde pesa poco quedaba 13-20 dB abajo:
      // medido) y baja a su peso cuando entra el groove
      var peso = me.gain(G.pesoPortadora), arranque = Math.max(1, 1 / G.pesoPortadora) * 1.15;
      peso.gain.setValueAtTime(G.pesoPortadora * arranque, t0);
      peso.gain.setValueAtTime(G.pesoPortadora * arranque, t0 + G.intro * T * .75);
      peso.gain.linearRampToValueAtTime(G.pesoPortadora, t0 + (G.intro + 1) * T);
      bus.connect(peso).connect(pan).connect(me.master); pan.connect(me.envio);
      var oscs = [];
      PARCIALES[banda].forEach(function (pa, j) {
        [0, 1].forEach(function (k) {                                   // el halo: un gemelo que bate una vez por compás
          var o = me.osc('sine', G.f0 * pa[0] + k * (1 / T) * (j % 2 ? 1 : -1));
          var g = me.gain(pa[1] * (k ? .32 : 1) * .22); o.connect(g).connect(bus); o.start(t0); o.stop(me.fin()); oscs.push([o, pa[0], k, j]);
        });
      });
      // la forma: cada sección mueve la portadora (la transposición se desliza medio compás: no hay escalones)
      for (var b = 0; b < C; b++) {
        var sc = me.seccion(b), prev = me.seccion(b - 1);
        if (b === 0 || sc.transporte !== prev.transporte) oscs.forEach(function (x) {
          x[0].frequency.setTargetAtTime(G.f0 * Math.pow(2, sc.transporte / 12) * x[1] + x[2] * (1 / T) * (x[3] % 2 ? 1 : -1), Math.max(t0, t0 + b * T - T / 4), T / 6);
        });
      }
      if (banda === 'alto') {
        var ch = me.f(ctx.createBufferSource()); ch.buffer = me.ruido(1.3, me.P.semilla + 'chispa'); ch.loop = true;
        var hp = me.filtro('highpass', 4200, .7), gch = me.gain(.075);
        ch.connect(hp).connect(gch).connect(bus); ch.start(t0); ch.stop(me.fin());
      }
      var gr = bus.gain; gr.setValueAtTime(0, t0);
      for (var bb = 0; bb < C; bb++) {
        var u = me.lejaniaEn(bb), coh = Math.min(G.coh[1], G.coh[0] + (G.coh[1] - G.coh[0]) * (1 - u)), sw = G.swing * (.6 + .4 * Math.sin(bb / 1.3));
        var entra = Math.min(1, .5 + Math.max(0, bb / 1.5)), dens = me.seccion(bb).densidad;   // desde el compás 0 a media fuerza
        var piso = .18 + .5 * (1 - coh) + (1 - entra) * .6;
        if (bb >= C - 2) piso = Math.max(piso, .5);
        Object.keys(G.groove[banda]).forEach(function (paso) {
          paso = +paso;
          var gg = G.groove[banda][paso] * (.55 + .45 * dens), p = paso + (paso % 2 ? sw * 2 : 0);
          var t = t0 + bb * T + p * S16 + (1 - coh) * .03 * (rng() - .5);
          var ataque = .004 + (1 - coh) * .1, tau = TAU[banda] * (1 + (1 - coh) * 3.5) * (110 / G.bpm);
          gr.setTargetAtTime(Math.max(piso + (1 - piso) * gg * entra * (bb >= C - 2 ? .3 : 1), piso), t, ataque / 3);
          gr.setTargetAtTime(piso, t + ataque, tau);
        });
      }
      gr.setTargetAtTime(0, t0 + C * T, .8);
    });
  };

  // ── notas del modo: el grado g del qenet, en la octava o, con la transposición de la sección ──
  S.nota = function (base, grado, b) {
    var esc = this.escala, n = esc.length, oct = Math.floor(grado / n), k = ((grado % n) + n) % n;
    return base + esc[k] + 12 * oct + this.seccion(b).transporte;
  };

  // ── bajo elástico (ochentero): entre los golpes de la portadora, glissa desde abajo, abre su filtro ──
  S.bajo = function () {
    var me = this, t0 = this.t0, C = this.Q.compases, T = this.T, S16 = this.S16, G = this.G, rng = this.rngDe(this.P.semilla + '·bajo');
    var o1 = this.osc('sawtooth', 55), o2 = this.osc('square', 55), mezcla = this.gain(1), f = this.filtro('lowpass', 200, 11), amp = this.gain(0);
    var sat = this.n(this.ctx.createWaveShaper()), curva = new Float32Array(1024);
    for (var i = 0; i < 1024; i++) curva[i] = Math.tanh(2.2 * (i / 511.5 - 1));
    sat.curve = curva; o2.detune.value = -1200; var g2 = this.gain(.45);
    o1.connect(mezcla); o2.connect(g2).connect(mezcla); mezcla.connect(f).connect(sat).connect(amp).connect(this.gain(.25)).connect(this.master);
    o1.start(t0); o2.start(t0); o1.stop(this.fin()); o2.stop(this.fin());
    var golpes = Object.keys(G.groove.bajo).map(Number), POS = [];
    for (var p = 1; p < G.pasos; p++) if (golpes.indexOf(p) < 0 && rng() < .45) POS.push(p);
    for (var b = 3; b < C - 1; b++) {
      POS.forEach(function (p) {
        if (rng() < .22 + (1 - me.seccion(b).densidad) * .3) return;
        var m = me.nota(G.tonica, Math.floor(rng() * 5) + (rng() < .3 ? 5 : 0), b), t = t0 + b * T + p * S16, d = S16 * (1 + rng() * .8);
        [o1, o2].forEach(function (o) { o.frequency.setTargetAtTime(hz(m - 3), t - .002, .001); o.frequency.setTargetAtTime(hz(m), t, .03); });
        f.frequency.setTargetAtTime(1700, t, .006); f.frequency.setTargetAtTime(220, t + .02, .09);
        amp.gain.setTargetAtTime(.9, t, .004); amp.gain.setTargetAtTime(0, t + d, .03);
      });
    }
  };

  // ── bajo FM: un ostinato del modo, en los golpes del bajo del groove; el índice de modulación se cierra en cada nota ──
  S.bajoFM = function () {
    var me = this, t0 = this.t0, C = this.Q.compases, T = this.T, S16 = this.S16, G = this.G, rng = this.rngDe(this.P.semilla + '·fm');
    var car = this.osc('sine', 55), mod = this.osc('sine', 55), idx = this.gain(0), amp = this.gain(0), ratio = [1, 2, .5, 3][Math.floor(rng() * 4)];
    mod.connect(idx).connect(car.frequency); car.connect(amp).connect(this.gain(.42)).connect(this.master);
    car.start(t0); mod.start(t0); car.stop(this.fin()); mod.stop(this.fin());
    var golpes = Object.keys(G.groove.bajo).map(Number), ost = golpes.map(function () { return Math.floor(rng() * 7) - 1; });
    for (var b = 2; b < C - 1; b++) {
      var dens = this.seccion(b).densidad;
      golpes.forEach(function (p, i) {
        if (i > 0 && rng() > .55 + .45 * dens) return;
        var m = me.nota(G.tonica + 12, ost[i] + (b % 4 === 3 && i === golpes.length - 1 ? 2 : 0), b), t = t0 + b * T + p * S16, f = hz(m);
        car.frequency.setValueAtTime(f, t); mod.frequency.setValueAtTime(f * ratio, t);
        idx.gain.setValueAtTime(f * (2.5 + 2 * rng()), t); idx.gain.setTargetAtTime(f * .3, t + .005, .06);
        amp.gain.setTargetAtTime(.85, t, .003); amp.gain.setTargetAtTime(0, t + S16 * (1.2 + rng()), .04);
      });
    }
  };

  // ── batería de máquina: bombo (seno que cae), caja (ruido + tono), hat (ruido agudo); patrones del genoma ──
  S.bateria = function () {
    var me = this, ctx = this.ctx, t0 = this.t0, C = this.Q.compases, T = this.T, S16 = this.S16, G = this.G, rng = this.rngDe(this.P.semilla + '·bateria');
    var bus = this.gain(.8); bus.connect(this.master);
    var nz = this.ruido(1, this.P.semilla + 'bat');
    var bombo = Object.keys(G.groove.bajo).map(Number).filter(function (p, i) { return i === 0 || rng() < .55; });
    var caja = Object.keys(G.groove.medio).map(Number), hat = Object.keys(G.groove.alto).map(Number);
    // cada golpe se arma justo antes de sonar (S.agendar) y se suelta del grafo al acabar; el azar se saca ANTES,
    // en el mismo orden de siempre, para que la misma semilla dé la misma batería en vivo y fuera de línea
    var golpe = function (tipo, t, v, desde) {
      if (tipo === 'bombo') {
        var o = me.osc('sine', 150), g = me.gain(0); o.connect(g).connect(bus);
        o.frequency.setValueAtTime(160, t); o.frequency.exponentialRampToValueAtTime(42, t + .09);
        g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(v, t + .002); g.gain.setTargetAtTime(0, t + .01, .09); o.start(t); o.stop(t + .5);
        o.onended = function () { g.disconnect(); };
      } else {
        var s = me.f(ctx.createBufferSource()); s.buffer = nz;
        var fl = tipo === 'caja' ? me.filtro('bandpass', 1900, .9) : me.filtro('highpass', 7500, .7), gg = me.gain(0), pan = me.paneo(tipo === 'hat' ? .3 : 0);
        s.connect(fl).connect(gg).connect(pan).connect(bus); if (tipo === 'caja') pan.connect(me.envio);
        gg.gain.setValueAtTime(0, t); gg.gain.linearRampToValueAtTime(v, t + .001); gg.gain.setTargetAtTime(0, t + .003, tipo === 'caja' ? .07 : .022);
        s.start(t, desde); s.stop(t + .4);
        s.onended = function () { fl.disconnect(); gg.disconnect(); pan.disconnect(); };
        if (tipo === 'caja') { var o2 = me.osc('triangle', 190), g3 = me.gain(0); o2.connect(g3).connect(bus); g3.gain.setValueAtTime(v * .5, t); g3.gain.setTargetAtTime(0, t + .002, .05); o2.start(t); o2.stop(t + .3);
          o2.onended = function () { g3.disconnect(); }; }
      }
      return [];
    };
    var agenda = function (tipo, t, v) {
      var desde = tipo === 'bombo' ? 0 : rng() * .5;
      me.agendar(t - .05, function () { return golpe(tipo, t, v, desde); });
    };
    for (var b = G.intro; b < C - 2; b++) {
      var dens = this.seccion(b).densidad, sw = G.swing;
      bombo.forEach(function (p) { agenda('bombo', t0 + b * T + p * S16, .9); });
      caja.forEach(function (p) { if (dens > .5) agenda('caja', t0 + b * T + p * S16, .45); });
      hat.forEach(function (p) { if (rng() < .4 + .6 * dens) agenda('hat', t0 + b * T + (p + (p % 2 ? sw * 2 : 0)) * S16, .18 + .12 * rng()); });
    }
  };

  // ── órgano (ethio): dos cuadradas desafinadas, filtro y vibrato; acordes del modo a contratiempo ──
  S.organo = function () {
    var me = this, t0 = this.t0, C = this.Q.compases, T = this.T, S16 = this.S16, G = this.G, rng = this.rngDe(this.P.semilla + '·organo');
    var voces = [0, 1, 2].map(function (k) {
      var a = me.osc('square', 220), b2 = me.osc('square', 220); b2.detune.value = 9;
      var lp = me.filtro('lowpass', 2100, 1), amp = me.gain(0), pan = me.paneo(-.4 + .4 * k);
      a.connect(lp); b2.connect(lp); lp.connect(amp).connect(me.gain(.07)).connect(pan).connect(me.master); pan.connect(me.envio);
      var vib = me.osc('sine', 5.8 + k * .3), vg = me.gain(3); vib.connect(vg); vg.connect(a.detune); vg.connect(b2.detune);
      [a, b2, vib].forEach(function (o) { o.start(t0); o.stop(me.fin()); });
      return { a: a, b: b2, amp: amp };
    });
    var off = [], uno = G.pasos === 12 ? 3 : 4;
    for (var p = 0; p < G.pasos; p++) if (p % uno === Math.floor(uno / 2) || (rng() < .15 && p % 2)) off.push(p);
    for (var b = G.intro; b < C - 1; b++) {
      var grado = [0, 3, 1, 4][b % 4] + Math.floor(rng() * 2), dens = this.seccion(b).densidad;
      off.forEach(function (p) {
        if (rng() > .35 + .65 * dens) return;
        var t = t0 + b * T + p * S16;
        voces.forEach(function (v, k) {
          var f = hz(me.nota(G.tonica + 24, grado + k * 2, b)); v.a.frequency.setValueAtTime(f, t); v.b.frequency.setValueAtTime(f, t);
          v.amp.gain.setTargetAtTime(1, t, .004); v.amp.gain.setTargetAtTime(0, t + S16 * .8, .02);
        });
      });
    }
  };

  // ── pared espectral (Grisey): el acorde es el espectro de su fundamental virtual, estirado; crece y respira por sección ──
  S.pared = function () {
    var me = this, t0 = this.t0, C = this.Q.compases, T = this.T, G = this.G, rng = this.rngDe(this.P.semilla + '·pared');
    var delta = .004 + rng() * .012, parciales = [3, 4, 5, 6, 7, 9, 11, 13, 15, 17];
    var bus = this.gain(0), lp = this.filtro('lowpass', 3000, .4), pan = this.paneo(0); bus.connect(lp).connect(this.gain(.16)).connect(pan).connect(this.master); pan.connect(this.envio);
    var oscs = parciales.map(function (n, j) {
      var o = me.osc('sine', G.f0 * Math.pow(n, 1 + delta)), g = me.gain(.5 / Math.sqrt(n)); o.connect(g).connect(bus); o.start(t0); o.stop(me.fin());
      return [o, n];
    });
    for (var b = 0; b < C; b++) {
      var sc = this.seccion(b), t = t0 + b * T;
      if (b === 0 || sc.letra !== this.seccion(b - 1).letra) {
        oscs.forEach(function (x) { x[0].frequency.setTargetAtTime(G.f0 * Math.pow(2, sc.transporte / 12) * Math.pow(x[1], 1 + delta), t, T / 3); });
      }
      bus.gain.setTargetAtTime(.25 + .75 * sc.densidad * (.6 + .4 * Math.sin(b * 1.7)), t, T / 2.5);
    }
    bus.gain.setTargetAtTime(0, t0 + C * T, 1.2);
  };

  // ── arpegios (きくお): el modo en dieciseisavos (o fusas), brillantes y cortos, que saltan de octava ──
  S.arpegio = function () {
    var me = this, t0 = this.t0, C = this.Q.compases, T = this.T, S16 = this.S16, G = this.G, rng = this.rngDe(this.P.semilla + '·arpegio');
    var o = this.osc(rng() < .5 ? 'square' : 'sawtooth', 440), lp = this.filtro('lowpass', 3000, 6), amp = this.gain(0), pan = this.paneo(0);
    o.connect(lp).connect(amp).connect(this.gain(.09)).connect(pan).connect(this.master); pan.connect(this.envio);
    o.start(t0); o.stop(this.fin());
    var div = G.bpm > 140 ? 1 : 2, figura = [0, 2, 4, 1, 3, 5, 2, 4].map(function (x) { return x + Math.floor(rng() * 2); });
    for (var b = G.intro + 1; b < C - 1; b++) {
      var dens = this.seccion(b).densidad; if (dens < .6) continue;
      for (var s = 0; s < G.pasos * div; s++) {
        if (rng() < .12) continue;
        var t = t0 + b * T + s * S16 / div, gr = figura[s % figura.length] + (s % 7 === 0 ? 5 : 0);
        o.frequency.setValueAtTime(hz(me.nota(G.tonica + 36, gr, b)), t);
        lp.frequency.setValueAtTime(5200, t); lp.frequency.setTargetAtTime(900, t + .004, .04);
        amp.gain.setTargetAtTime(.9, t, .002); amp.gain.setTargetAtTime(0, t + S16 / div * .45, .015);
        pan.pan.setValueAtTime(s % 2 ? .45 : -.45, t);
      }
    }
  };

  // ── stabs FM (electro raro): acordes cortos y metálicos en los golpes de la palmada ──
  S.stabs = function () {
    var me = this, t0 = this.t0, C = this.Q.compases, T = this.T, S16 = this.S16, G = this.G, rng = this.rngDe(this.P.semilla + '·stabs');
    var pos = Object.keys(G.groove.medio).map(Number).concat([Math.floor(rng() * G.pasos)]);
    var voces = [0, 1, 2].map(function (k) {
      var c = me.osc('sine', 300), m = me.osc('sine', 300), ix = me.gain(0), a = me.gain(0), pan = me.paneo(-.3 + .3 * k);
      m.connect(ix).connect(c.frequency); c.connect(a).connect(me.gain(.11)).connect(pan).connect(me.master); pan.connect(me.envio);
      c.start(t0); m.start(t0); c.stop(me.fin()); m.stop(me.fin());
      return { c: c, m: m, ix: ix, a: a };
    });
    var ratio = 1.41 + rng() * .3;                                      // inarmónico: el metal raro
    for (var b = G.intro; b < C - 1; b++) {
      if (this.seccion(b).densidad < .7) continue;
      pos.forEach(function (p) {
        var t = t0 + b * T + p * S16;
        voces.forEach(function (v, k) {
          var f = hz(me.nota(G.tonica + 24, k * 2 + (b % 2), b));
          v.c.frequency.setValueAtTime(f, t); v.m.frequency.setValueAtTime(f * ratio, t);
          v.ix.gain.setValueAtTime(f * 3, t); v.ix.gain.setTargetAtTime(0, t + .01, .05);
          v.a.gain.setTargetAtTime(1, t, .002); v.a.gain.setTargetAtTime(0, t + .06, .05);
        });
      });
    }
  };

  // ── una voz de formantes: lee un trozo de texto con notas ──
  S.voz = function (eventos, opts) {
    var ctx = this.ctx, me = this;
    var V = this.G.mezcla.voz;
    var src = this.osc(opts.onda || V.onda || 'sawtooth', 220); if (opts.detune) src.detune.value = opts.detune;
    var nz = this.f(ctx.createBufferSource()); nz.buffer = this.ruido(.8, opts.semilla + 'n'); nz.loop = true;
    var gSrc = this.gain(1), gNz = this.gain(0); src.connect(gSrc); nz.connect(gNz);
    var suma = this.gain(1); gSrc.connect(suma); gNz.connect(suma);
    var F = [0, 1, 2].map(function (k) { return me.filtro('bandpass', VOC.a[k], (V.nasal ? [16, 18, 18] : [9, 12, 14])[k]); });
    var FG = [1, .55, .3].map(function (v) { return me.gain(v); });
    var amp = this.gain(0), out = opts.salida;
    F.forEach(function (fl, k) { suma.connect(fl).connect(FG[k]).connect(amp); });
    var brillo = this.filtro('lowpass', opts.brillo || 7000, .5); amp.connect(brillo).connect(out);
    var cons = this.gain(0), cf = this.filtro('bandpass', 3500, 1.2); nz.connect(cf).connect(cons).connect(out);
    var vib = this.osc('sine', V.vib[0] || 5.4), vibG = this.gain(0); vib.connect(vibG).connect(src.frequency);
    var t0 = eventos.length ? eventos[0].t : this.t0, tf = eventos.length ? eventos[eventos.length - 1].t + eventos[eventos.length - 1].dur : t0;
    [src, nz, vib].forEach(function (o) { o.start(Math.max(me.ctx.currentTime, t0 - .2)); o.stop(tf + 1.2); });
    src.frequency.setValueAtTime(hz(eventos[0] ? eventos[0].nota : 57), Math.max(0, t0 - .2));
    eventos.forEach(function (e, idx) {
      var limpio = e.texto.replace(COMB, ''), tachado = COMB.test(e.texto); COMB.lastIndex = 0;
      var vocales = (limpio.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').match(/[aeiou]/g) || ['e']);
      var ruidos = (limpio.match(/▓/g) || []).length, t = e.t, d = e.dur, f0 = hz(e.nota);
      if (V.robot) src.frequency.setValueAtTime(f0, Math.max(0, t)); else src.frequency.setTargetAtTime(f0, Math.max(0, t - .03), V.port);   // robot: escalones
      vibG.gain.setTargetAtTime(0, t, .02);
      if (d > .3 && V.vib[1]) vibG.gain.setTargetAtTime(f0 * .011 * V.vib[1] * (opts.vibrato == null ? 1 : opts.vibrato), t + .2, .12);
      vocales.forEach(function (v, k) {
        var tv = t + d * k / vocales.length;
        F.forEach(function (fl, j) { fl.frequency.setTargetAtTime(VOC[v][j] * (opts.formante || 1), tv, .025); });
      });
      var susurro = opts.susurro || tachado, ruido = ruidos / Math.max(1, limpio.length);
      gSrc.gain.setTargetAtTime(susurro ? 0 : 1 - Math.min(1, ruido * 2.5), Math.max(0, t - .01), .02);
      gNz.gain.setTargetAtTime(susurro ? .9 : Math.min(1.2, ruido * 3 + V.aliento), Math.max(0, t - .01), .02);   // el aliento del estilo
      var nivel = (e.acento ? 1 : .78) * (opts.nivel || 1), sola = limpio.replace(/[▓\s]/g, '').length <= 1 || opts.staccato;
      amp.gain.setTargetAtTime(nivel, t, sola ? .006 : .05);
      if (sola) amp.gain.setTargetAtTime(0, t + Math.min(d, .12), .03);
      var sig = eventos[idx + 1];
      if (!sig || sig.t - (t + d) > .12) amp.gain.setTargetAtTime(0, t + d, .09);
      if (/^[^aeiouáéíóú▓]/i.test(limpio)) { cons.gain.setTargetAtTime(.12, Math.max(0, t - .035), .005); cons.gain.setTargetAtTime(0, Math.max(0, t - .005), .015);
        cf.frequency.setValueAtTime(/^[sxzcf]/i.test(limpio) ? 6200 : 2600, Math.max(0, t - .04)); }
    });
    return amp;
  };

  // la melodía nómada en el qenet, alrededor de una base y con la transposición de la sección del compás b
  S.melodia = function (n, semilla, base, b) {
    var r = this.rngDe(semilla), esc = this.escala, gr = [], tr = b == null ? 0 : this.seccion(b).transporte;
    for (var o = -1; o <= 1; o++) esc.forEach(function (x) { gr.push(base + x + 12 * o); });
    gr.sort(function (a, c) { return a - c; });
    var i = gr.indexOf(base) >= 0 ? gr.indexOf(base) : 5, out = [];
    for (var k = 0; k < n; k++) { var paso = [-1, 1, 1, -1, 2, -2, 0][Math.floor(r() * 7)]; i = Math.max(2, Math.min(gr.length - 3, i + paso)); out.push(gr[i] + tr); }
    if (n > 2) out[n - 1] = out[n - 2] - [2, 3, 5][Math.floor(r() * 3)];
    return out;
  };
  S.compasDe = function (t) { return Math.floor(t / this.T); };

  S.telefono = function (u) {
    var ent = this.gain(1), seco = this.gain(1 - u), tel = this.gain(u * 1.4);
    var hp = this.filtro('highpass', 500, .7), lp = this.filtro('lowpass', 2300, .7);
    ent.connect(seco); ent.connect(hp).connect(lp).connect(tel);
    var sal = this.gain(1); seco.connect(sal); tel.connect(sal);
    return { entrada: ent, salida: sal };
  };

  // ¿esta palabra se canta con difonos? no si el ruido se la comió (▓) ni si está tachada (se susurra con formantes)
  var conDifonos = function (texto) {
    var limpio = texto.replace(/[\u0300-\u036f]/g, ''), tachado = /\u0336/.test(texto);
    var ruido = (limpio.match(/▓/g) || []).length / Math.max(1, limpio.replace(/\s/g, '').length);
    return !tachado && ruido < .3 && /[a-zA-ZáéíóúüñÁÉÍÓÚÑ]/.test(limpio);
  };

  S.nave = function () {
    var me = this, porLinea = {}, base = this.G.tonica + 24 + this.G.mezcla.voz.registro, V = this.G.mezcla.voz;
    this.Q.pasos.forEach(function (p) { if (!p.hueco) (porLinea[p.linea] = porLinea[p.linea] || []).push(p); });
    Object.keys(porLinea).forEach(function (k) {
      var ev = porLinea[k], u = ev[0].lejania || 0;
      var notas = me.melodia(ev.length, me.P.semilla + '·nave' + k, base, me.compasDe(ev[0].t));
      var tel = me.telefono(Math.min(1, u * 1.2)), pan = me.paneo(-.08);
      tel.salida.connect(me.gain(3)).connect(pan).connect(me.master); pan.connect(me.envio);
      var eventos = ev.map(function (p, j) { return { t: me.t0 + p.t, dur: p.dur, texto: p.texto, nota: notas[j], acento: p.eje }; });
      var dif = me.banco ? eventos.filter(function (e) { return conDifonos(e.texto); }) : [];
      var form = me.banco ? eventos.filter(function (e) { return !conDifonos(e.texto); }) : eventos;
      if (dif.length) {                                   // la nave canta con el banco: consonantes de verdad
        var brillo = me.filtro('lowpass', 7500 - 3500 * u, .5), g = me.gain((V.nivelDifonos || 2.4) * (V.psola ? 1 : 1.25));   // +2 dB: la ardilla ligera sale más baja (medido)
        brillo.connect(g).connect(tel.entrada);
        var r = me.banco.cantar(brillo, dif.map(function (e) {
          return { t: e.t, dur: e.dur, texto: e.texto.replace(/▓/g, ''), nota: e.nota + (V.registroDifonos || 0) };
        }), { vibrato: V.robot ? null : [V.vib[0] || 5.4, .011 * (V.vib[1] || 1)], rng: me.rngDe(me.P.semilla + '·difonos' + k), agendar: me.agendar.bind(me),
              modo: V.psola ? 'psola' : null,       // psola: la altura baja y el timbre se queda (difonos F4)
              porPalabra: true });                  // ardilla ligera: un buffer por palabra (con granos, きくお saturaba el audio)
        me.adoptar(r.nodos);
      }
      if (form.length) me.voz(form, { semilla: me.P.semilla + '·voz' + k, salida: tel.entrada, nivel: .9, brillo: 7000 - 3500 * u, formante: V.formante });
    });
  };

  // los nodos que crea el banco también se apagan y desconectan al detener
  S.adoptar = function (nodos) {
    var me = this;
    nodos.forEach(function (n) { me.nodos.push(n); if (n.stop) me.fuentes.push(n); });
  };

  S.ecos = function () {
    var me = this, S16 = this.S16;
    this.Q.ecos.forEach(function (e, k) {
      var pal = e.texto.split(/\s+/).filter(Boolean); if (!pal.length) return;
      var notas = me.melodia(pal.length, me.P.semilla + '·eco' + k, me.G.tonica + 36, me.compasDe(e.t));
      var edad = Math.log2(e.retraso) + 1;
      var bp = me.filtro('bandpass', 1300, .8 + edad * 1.2), cuant = me.n(me.ctx.createWaveShaper()), c = new Float32Array(2048), niveles = Math.max(4, 64 >> edad);
      for (var i = 0; i < 2048; i++) { var x = i / 1023.5 - 1; c[i] = Math.round(x * niveles) / niveles; }
      cuant.curve = c;
      var dl = me.n(me.ctx.createDelay(2)); dl.delayTime.value = Math.min(1.9, me.T / 4); var fb = me.gain(.38), lp = me.filtro('lowpass', 2200, .5);
      var pan = me.paneo(.55), g = me.gain(4.5 / edad);
      bp.connect(cuant).connect(g); g.connect(pan); g.connect(dl); dl.connect(lp).connect(fb).connect(dl); lp.connect(pan);
      pan.connect(me.master); pan.connect(me.envio);
      var dur = S16 * (e.texto.length > 20 ? 1 : 2.5);
      me.voz(pal.map(function (w, j) { return { t: me.t0 + e.t + j * dur * 1.1, dur: dur, texto: w, nota: notas[j] }; }),
             { semilla: me.P.semilla + '·ecovoz' + k, salida: bp, staccato: /\s{2}/.test(e.texto), formante: 1.08 * me.G.mezcla.voz.formante });
    });
  };

  S.tierra = function () {
    var me = this, S16 = this.S16;
    this.Q.tierra.forEach(function (x, k) {
      var pal = x.texto.replace(/[—()]/g, '').split(/\s+/).filter(Boolean); if (!pal.length) return;
      var notas = me.melodia(pal.length, me.P.semilla + '·tierra' + k, me.G.tonica + 12, me.compasDe(x.t));
      [[-.6, -12, 0], [0, 0, .025], [.6, 9, .05]].forEach(function (c, j) {
        var pan = me.paneo(c[0]), g = me.gain(1.4); g.connect(pan).connect(me.master);
        var sal = me.gain(1); sal.connect(g);
        var ev = pal.map(function (w, i) { return { t: me.t0 + x.t + c[2] + i * S16 * 1.5, dur: S16 * 1.4, texto: w, nota: notas[i] + c[1] / 100 }; });
        if (me.banco) {                                   // la tierra con el banco: una octava abajo de la nave, sin vibrato, en PSOLA (grave sin ogro)
          var lp = me.filtro('lowpass', 5200, .5), gd = me.gain(1.9); lp.connect(gd).connect(sal);
          me.adoptar(me.banco.cantar(lp, ev.map(function (e) { return { t: e.t, dur: e.dur, texto: e.texto, nota: e.nota + 12 }; }),
                                     { rng: me.rngDe(me.P.semilla + '·tierradif' + k + j), agendar: me.agendar.bind(me), modo: 'psola' }).nodos);
        } else {
          me.voz(ev.map(function (e) { return { t: e.t, dur: e.dur, texto: e.texto, nota: Math.round(e.nota) }; }),
                 { semilla: me.P.semilla + '·tierravoz' + k + j, salida: sal, detune: c[1], vibrato: 0, formante: .9, brillo: 5200, nivel: .8 });
        }
      });
    });
  };

  S.maquina = function () {
    var me = this, ctx = this.ctx, S16 = this.S16, golpes = Object.keys(this.G.groove.bajo).map(Number);
    this.Q.maquina.forEach(function (x, k) {
      x.texto.split(/[\s·]+/).filter(Boolean).forEach(function (w, i) {
        if (i >= golpes.length * 2) return;
        var h = 0; for (var j = 0; j < w.length; j++) h = (h * 31 + w.charCodeAt(j)) >>> 0;
        var parcial = 12 + (h % 40), t = me.t0 + x.t + (Math.floor(i / golpes.length) * me.G.pasos + golpes[i % golpes.length]) * S16;
        var src = me.f(ctx.createBufferSource()); src.buffer = me.ruido(.25, w + k);
        var bp = me.filtro('bandpass', me.G.f0 * parcial, 22), g = me.gain(0), pan = me.paneo(i % 2 ? .45 : -.45);
        src.connect(bp).connect(g).connect(pan).connect(me.master); pan.connect(me.envio);
        g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(2.2, t + .003); g.gain.setTargetAtTime(0, t + .004, .045);
        src.start(t); src.stop(t + .3);
      });
    });
  };

  S.detener = function () {
    var ahora = this.ctx.currentTime, me = this;
    if (this.reloj) { clearInterval(this.reloj); this.reloj = null; } this.cola = [];
    if (this.master) { this.master.gain.cancelScheduledValues(ahora); this.master.gain.setTargetAtTime(0, ahora, .05); }
    setTimeout(function () {
      me.fuentes.forEach(function (f) { try { f.stop(); } catch (e) {} });
      me.nodos.forEach(function (n) { try { n.disconnect(); } catch (e) {} });
      me.nodos = []; me.fuentes = [];
    }, 300);
  };

  function renderizar(P, rngDe, sr, ruta) {
    sr = sr || 48000;
    var Q = partitura(P, rngDe), seg = Q.compases * Q.T + 2.5;
    var off = new OfflineAudioContext(2, Math.ceil(seg * sr), sr);
    var D = global.Difonos, carga = D && ruta !== null ? D.cargar(off, ruta || BANCO_DIFONOS).catch(function () { return null; }) : Promise.resolve(null);
    return carga.then(function (banco) {
      var s = new Sonido(off, P, rngDe, null, banco); s.montar(.05);
      return off.startRendering().then(function (buf) { return { buffer: buf, nodos: s.nodos.length, segundos: seg, genoma: Q.genoma, difonos: !!banco }; });
    });
  }
  // cargar el banco una vez por contexto (index.html lo pide al primer gesto)
  var bancos = typeof WeakMap !== 'undefined' ? new WeakMap() : null;
  function bancoPara(ctx) {
    var D = global.Difonos; if (!D) return Promise.resolve(null);
    if (bancos && bancos.has(ctx)) return bancos.get(ctx);
    var pr = D.cargar(ctx, BANCO_DIFONOS).catch(function () { return null; });
    if (bancos) bancos.set(ctx, pr); return pr;
  }

  global.PortadoraSonido = { Sonido: Sonido, partitura: partitura, genoma: genoma, renderizar: renderizar, euclides: euclides, bancoPara: bancoPara, BANCO_DIFONOS: BANCO_DIFONOS, prepararSala: prepararSala,
                             QENET: QENET, VOC: VOC, ESTILOS: ESTILOS, MEZCLA: MEZCLA };
})(typeof window !== 'undefined' ? window : globalThis);
