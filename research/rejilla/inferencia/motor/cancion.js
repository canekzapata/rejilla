/* cancion.js — «suma uno» (loop 09 de la rejilla): la pieza se infiere a sí misma.
 *
 * Un modelo bayesiano (Markov de primer orden sobre 12 clases de altura, conteos Dirichlet, temperatura) escucha cada
 * nota y predice la siguiente. construir() corre el modelo una vez (sembrado: siempre la misma pieza) y deja la
 * partitura: cada evento lleva su nota, su probabilidad, su sorpresa (−log2 p), la entropía y la distribución entera.
 * Los instrumentos leen esa partitura: la pared ES la distribución; la muestra es lo que el modelo eligió.
 *
 *   Cancion.pista(n)(ctx, destino, banco, en)   en(t, f): crear nodos justo antes de sonar
 *   Cancion.modelo()   → la partitura del modelo (para medir y dibujar)
 */
(function (global) {
  'use strict';
  var BPM = 104, P16 = 60 / BPM / 4, PULSOS = 1300, COLA = 5;
  var DURACION = PULSOS * P16 + COLA, T = 2, COMPASES = Math.ceil(DURACION / T);   // T: el trozo del taller, no un compás
  var hz = function (m) { return 440 * Math.pow(2, (m - 69) / 12); };
  var SECC = [{ n: 'prior', a: 0, b: 240, tau: 1.6, alfa: 1 }, { n: 'evidencia', a: 240, b: 540, tau: 1, alfa: .5 },
              { n: 'posterior', a: 540, b: 764, tau: .35, alfa: .05 }, { n: 'sorpresa', a: 764, b: 1084, tau: -1.2, alfa: .3 },
              { n: 'inferencia', a: 1084, b: 1300, tau: 1, alfa: .2 }];
  var seccion = function (p) { for (var i = 0; i < SECC.length; i++) if (p < SECC[i].b) return SECC[i]; return SECC[SECC.length - 1]; };
  var GANCHO = [[9, 2], [11, 2], [1, 2], [4, 4], [1, 2], [11, 2], [9, 4], [6, 2], [4, 2], [6, 2], [9, 4], [11, 4], [9, 2], [4, 6]];   // La mayor
  var POP = [[9, true], [4, true], [6, false], [2, true]];                                                                          // I–V–vi–IV

  function rngDe(nombre) {
    var h = 2166136261; nombre = 'sumauno·' + nombre;
    for (var i = 0; i < nombre.length; i++) { h ^= nombre.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
    return function () { h = (h + 0x6D2B79F5) >>> 0; var t = h; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }

  /* ── el modelo ── */
  var MODELO = (function construir() {
    var rng = rngDe('modelo'), C = [], ev = [], prev = 9, p = 0, gi = 0, turnoEv = false, improbable = false;
    for (var i = 0; i < 12; i++) { C.push([]); for (var j = 0; j < 12; j++) C[i].push(0); }
    var fila = []; for (i = 0; i < 31; i++) fila.push(i === 15 ? 1 : 0);            // regla 30, una celda prendida
    var paso30 = function () { var n = []; for (var i = 0; i < fila.length; i++) { var l = fila[(i + fila.length - 1) % fila.length], c = fila[i], r = fila[(i + 1) % fila.length]; n.push(l ^ (c | r)); } fila = n; };
    var predictiva = function (prev, alfa) {
      var s = 0, d = []; for (var j = 0; j < 12; j++) s += C[prev][j] + alfa;
      for (j = 0; j < 12; j++) d.push((C[prev][j] + alfa) / s); return d;
    };
    var entropia = function (d) { var h = 0; d.forEach(function (x) { if (x > 0) h -= x * Math.log2(x); }); return h; };
    var muestrea = function (q) { var s = q.reduce(function (a, b) { return a + b; }, 0), r = rng() * s; for (var j = 0; j < 12; j++) { r -= q[j]; if (r <= 0) return j; } return 11; };
    while (p < PULSOS) {
      var sec = seccion(p), dist = predictiva(prev, sec.alfa), pc, dur, tipo;
      paso30();
      if (sec.n === 'evidencia' && turnoEv) {                                    // los datos: el gancho pop
        pc = GANCHO[gi % GANCHO.length][0]; dur = GANCHO[gi % GANCHO.length][1]; gi++; tipo = 'evidencia';
        C[prev][pc] += 1;
      } else if (sec.n === 'sorpresa' && !improbable) {                          // LA nota improbable
        pc = dist.indexOf(Math.min.apply(null, dist)); dur = 16; tipo = 'improbable'; improbable = true;
      } else {
        var q = dist.map(function (x) { return Math.pow(x, 1 / sec.tau); });   // τ < 0: anti-inferencia (prefiere lo improbable)
        pc = muestrea(q); tipo = 'propia';
        var s = -Math.log2(dist[pc]);
        // la duración la decide la sorpresa: lo improbable se alarga (un calderón computacional)
        dur = s < 1.5 ? 1 : s < 2.6 ? 2 : s < 3.4 ? 3 : s < 4.4 ? 5 : 8;
        if (sec.n === 'posterior') dur = 2;                                      // el pop, cuantizado a corcheas
        if (sec.n === 'prior') dur = Math.max(dur, 3);
        var peso = { prior: .4, evidencia: 1, posterior: 2, sorpresa: .6, inferencia: 1.2 }[sec.n];
        C[prev][pc] += peso;                                                     // aprende también de lo que él mismo dice
      }
      if (sec.n === 'evidencia') turnoEv = !turnoEv;
      var oct = 4 + fila[15] - fila[14] * (sec.n === 'posterior' ? 0 : 1) + (fila[16] && sec.n === 'sorpresa' ? 1 : 0);
      ev.push({ p: p, dur: dur, pc: pc, oct: oct, tipo: tipo, sec: sec.n, prob: dist[pc], s: -Math.log2(dist[pc]), H: entropia(dist),
                dist: dist.slice(), fila: fila.slice() });
      prev = pc; p += dur;
    }
    return ev;
  })();
  var evEn = function (t) { var p = t / P16, k = 0; while (k + 1 < MODELO.length && MODELO[k + 1].p <= p) k++; return MODELO[k]; };
  var argmax = function (d) { return d.indexOf(Math.max.apply(null, d)); };

  var CURVAS = { reloj: [[0, .45], [240, .6], [540, .25], [764, 1], [1084, .5], [1300, 0]],
                 pared: [[0, 1], [240, .85], [540, .7], [764, 1], [1084, .9], [1300, .6]] };
  function curva(nombre, p) {
    var K = CURVAS[nombre]; if (p <= K[0][0]) return K[0][1];
    for (var i = 1; i < K.length; i++) if (p <= K[i][0]) { var u = (p - K[i - 1][0]) / (K[i][0] - K[i - 1][0]); return K[i - 1][1] + (K[i][1] - K[i - 1][1]) * u; }
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

  /* ── 1. la pared: 12 clases × 4 octavas; cada amplitud es la probabilidad (p^1.6), nota por nota.
   *       En la sorpresa se estira (f·(f/110)^δ, inarmónica); en el pop se adelgaza hasta la tríada. ── */
  function pared(ctx, dest) {
    var u = U(ctx), sal = u.gain(.11), lp = u.filtro('lowpass', 4200, .5); lp.connect(sal).connect(dest);
    var parciales = [];
    for (var o = 0; o < 4; o++) for (var pc = 0; pc < 12; pc++) {
      var m = 45 + o * 12 + ((pc - 9 + 12) % 12), f = hz(m), peso = [.55, 1, .8, .4][o];
      var osc = u.osc(o === 0 ? 'triangle' : 'sine', f), g = u.gain(0), pan = u.paneo(((pc * 5) % 12) / 11 * 1.4 - .7);
      osc.connect(g).connect(pan).connect(lp); osc.start(0); osc.stop(DURACION);
      parciales.push({ osc: osc, g: g, pc: pc, f: f, peso: peso });
    }
    MODELO.forEach(function (e) {
      var t = e.p * P16, tau = e.sec === 'posterior' ? .03 : .18, nivel = curva('pared', e.p);
      var tot = e.dist.reduce(function (a, x) { return a + Math.pow(x, 1.6); }, 0);
      parciales.forEach(function (q) { q.g.gain.setTargetAtTime(nivel * q.peso * Math.pow(e.dist[q.pc], 1.6) / tot * 3.2, t, tau); });
    });
    [[764, .012], [1084, 0]].forEach(function (x) {                              // estirar y enderezar la pared
      parciales.forEach(function (q) { q.osc.frequency.setTargetAtTime(q.f * Math.pow(q.f / 110, x[1]), x[0] * P16, x[1] ? .02 : 2.5); });
    });
    sal.gain.setTargetAtTime(0, PULSOS * P16, 1.5);
  }

  /* ── piano preparado (la muestra) y piano eléctrico (la evidencia) ── */
  function fm(ctx, bus, en, m, t, v, op) {
    var u = U(ctx);
    en(t - .05, function () {
      var f = hz(m), car = u.osc('sine', f), mod = u.osc('sine', f * op.ratio), idx = u.gain(0), amp = u.gain(0), lp = u.filtro('lowpass', op.brillo, .5);
      mod.connect(idx).connect(car.frequency); car.connect(amp).connect(lp).connect(bus);
      idx.gain.setValueAtTime(f * op.indice * v, t); idx.gain.setTargetAtTime(f * op.indice * .08, t + .004, op.cierra);
      amp.gain.setValueAtTime(0, t); amp.gain.linearRampToValueAtTime(v, t + .003); amp.gain.setTargetAtTime(0, t + .01, op.decae);
      car.start(t); mod.start(t); car.stop(t + op.decae * 6); mod.stop(t + op.decae * 6);
      car.onended = function () { idx.disconnect(); amp.disconnect(); lp.disconnect(); };
    });
  }
  function muestra(ctx, dest, banco, en) {
    var u = U(ctx), bus = u.gain(.4), pan = u.paneo(.15); bus.connect(pan).connect(dest);
    MODELO.forEach(function (e) {
      if (e.tipo === 'evidencia') return;
      var m = 12 * (e.oct + 1) + e.pc, t = e.p * P16, v = Math.min(1, .35 + e.s * .1);   // lo sorpresivo, más fuerte
      if (e.tipo === 'improbable') { fm(ctx, bus, en, m - 12, t, 1, { ratio: 3.47, indice: 3, cierra: .2, decae: 2.2, brillo: 5000 }); }
      fm(ctx, bus, en, m, t, v, { ratio: 3.47, indice: 2.2, cierra: .05, decae: .25 + e.dur * P16 * .6, brillo: 2400 + 2400 * v });
      if (e.s > 4 && e.tipo !== 'improbable') fm(ctx, bus, en, m - 1, t - .025, v * .4, { ratio: 3.47, indice: 2, cierra: .04, decae: .2, brillo: 2000 });
    });
  }
  function evidencia(ctx, dest, banco, en) {
    var u = U(ctx), bus = u.gain(.36), pan = u.paneo(-.25); bus.connect(pan).connect(dest);
    MODELO.forEach(function (e) {
      if (e.tipo !== 'evidencia') return;
      var m = 60 + ((e.pc - 0 + 12) % 12) + (e.pc < 4 ? 12 : 0), t = e.p * P16;
      fm(ctx, bus, en, m, t, .7, { ratio: 1, indice: 1.4, cierra: .25, decae: .9, brillo: 3000 });         // el cuerpo
      fm(ctx, bus, en, m, t, .15, { ratio: 14, indice: .6, cierra: .02, decae: .25, brillo: 7000 });       // la púa (DX)
    });
  }

  /* ── el pop (posterior): I–V–vi–IV en supersierras, bombo a negras, palmas, hats. Se corta en la nota improbable ── */
  function pop(ctx, dest, banco, en) {
    var u = U(ctx), bus = u.gain(.5); bus.connect(dest);
    var nz = u.ruido(1, 'pop');
    for (var c = 0; c * 16 + 540 < 764; c++) (function (c) {
      var p0 = 540 + c * 16, t = p0 * P16, d = 16 * P16, ch = POP[c % 4], raiz = 45 + ((ch[0] - 9 + 12) % 12);
      var notas = [raiz, raiz + (ch[1] ? 4 : 3), raiz + 7, raiz + 12, raiz + (ch[1] ? 16 : 15)];
      en(t - .1, function () {
        var lp = u.filtro('lowpass', 1800 + (c % 4) * 300, .8), g = u.gain(0); lp.connect(g).connect(bus);
        g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(.09, t + .03); g.gain.setTargetAtTime(0, t + d - .05, .03);
        var vivos = 0;
        notas.forEach(function (m, i) { [-11, -4, 0, 5, 12].forEach(function (dt) {
          var o = u.osc('sawtooth', hz(m)); o.detune.value = dt; o.connect(lp); o.start(t); o.stop(t + d + .1); vivos++;
          o.onended = function () { if (--vivos === 0) { lp.disconnect(); g.disconnect(); } };
        }); });
      });
      for (var b = 0; b < 4; b++) (function (tb) {                              // bombo a negras
        en(tb - .05, function () {
          var o = u.osc('sine', 150), g = u.gain(0); o.connect(g).connect(bus);
          o.frequency.setValueAtTime(150, tb); o.frequency.exponentialRampToValueAtTime(48, tb + .09);
          g.gain.setValueAtTime(0, tb); g.gain.linearRampToValueAtTime(1, tb + .002); g.gain.setTargetAtTime(0, tb + .02, .1);
          o.start(tb); o.stop(tb + .5); o.onended = function () { g.disconnect(); };
        });
      })(t + b * 4 * P16);
      [4, 12].forEach(function (pp) { [0, .008, .017].forEach(function (dt) { golpe(t + pp * P16 + dt, .5, 1400, 1, .05); }); });
      for (var s = 2; s < 16; s += 4) golpe(t + s * P16, .14, 9000, .7, .03);
    })(c);
    function golpe(t, v, f, q, tau) {
      en(t - .05, function () {
        var s = ctx.createBufferSource(), fl = u.filtro(f > 6000 ? 'highpass' : 'bandpass', f, q), g = u.gain(0); s.buffer = nz;
        s.connect(fl).connect(g).connect(bus); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(v, t + .001); g.gain.setTargetAtTime(0, t + .002, tau);
        s.start(t, (t * 7.3) % .6); s.stop(t + .3); s.onended = function () { fl.disconnect(); g.disconnect(); };
      });
    }
  }

  /* ── el reloj: la regla 30. Un chasquido donde la fila del autómata tiene 1 (16 celdas = 16 pulsos) ── */
  function reloj(ctx, dest, banco, en) {
    var u = U(ctx), bus = u.gain(.45); bus.connect(dest); var nz = u.ruido(.5, 'reloj'), k = 0;
    for (var b = 0; b * 16 < PULSOS; b++) {
      var e = evEn(b * 16 * P16), fila = e.fila;
      for (var i = 0; i < 16; i++) {
        var p = b * 16 + i; if (!fila[8 + i] || ((p * 2654435761) >>> 0) % 100 > curva('reloj', p) * 100) continue;
        (function (t, agudo, pan) {
          en(t - .05, function () {
            var s = ctx.createBufferSource(), fl = u.filtro('bandpass', agudo ? 6200 : 1250, agudo ? 4 : 9), g = u.gain(0), pn = u.paneo(pan); s.buffer = nz;
            s.connect(fl).connect(g).connect(pn).connect(bus); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(agudo ? .3 : .6, t + .0008); g.gain.setTargetAtTime(0, t + .001, agudo ? .006 : .018);
            s.start(t, (t * 3.1) % .4); s.stop(t + .12); s.onended = function () { fl.disconnect(); g.disconnect(); pn.disconnect(); };
          });
        })(p * P16, fila[7 + i] === 1, (i / 15) * 1.6 - .8);
        k++;
      }
    }
  }

  /* ── las voces ── */
  var DIG = ['cero', 'uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve'];
  var numero = function (p) { var c = Math.max(1, Math.round(p * 100)); return 'cero punto ' + DIG[Math.floor(c / 10)] + ' ' + DIG[c % 10]; };
  // renglones cantados: sílabas sobre la nota que el modelo CREE (argmax) en ese momento, o sobre la que ELIGIÓ (pop)
  var CANTO = [
    ['G', 280, 3, 'creencia', 'ca da no ta que lle ga cam bia lo que es pe ro'],
    ['G', 380, 3, 'creencia', 'cuen to di vi do vuel vo a con tar'],
    ['G', 470, 3, 'creencia', 'y la du da se a del ga za'],
    ['A', 572, 2, 'eleccion', 'lo más pro ba ble es que te quie ra'],
    ['A', 636, 2, 'eleccion', 'lo más pro ba ble es que te quie ra'],
    ['A', 700, 2, 'eleccion', 'lo más pro ba ble es que vuel vas'],
    ['A', 960, 3, 'eleccion', 'lo im pro ba ble tam bién su ma u no'],
    ['G', 1110, 3, 'creencia', 'in fe rir es es cu char ha cia a de lan te'],
    ['A', 1180, 3, 'creencia', 'la be lle za es el e rror que ca bí a'],
    ['A', 1256, 6, 'creencia', 'su ma u no'], ['G', 1256, 6, 'creencia', 'su ma u no']
  ];
  var DICHO = [['G', 40, 'antes de oír, todas las notas pesan lo mismo'], ['G', 150, 'doce puertas, ninguna abierta'],
               ['G', 668, 'con noventa y nueve por ciento'], ['G', 790, 'no lo vi venir']];
  function partitura() {
    var out = [];
    CANTO.forEach(function (r) {
      var sil = r[4].split(' '), base = r[0] === 'A' ? 66 : 50, t = r[1] * P16, evs = [];
      sil.forEach(function (s, i) {
        var e = evEn(t), pc = r[3] === 'creencia' ? argmax(e.dist) : e.pc, nota = base - 6 + ((pc - (base - 6)) % 12 + 12) % 12;
        var dur = (i === sil.length - 1 ? r[2] * 3 : r[2]) * P16; evs.push({ t: t, dur: dur, texto: s, nota: nota }); t += dur;
      });
      out.push({ quien: r[0], compas: r[1], eventos: evs });
    });
    return out;
  }
  // los números: la probabilidad de las notas más improbables de la sorpresa, leídas en voz alta (cada ≥ 40 pulsos)
  var NUMEROS = (function () {
    var out = [], ult = -999;
    MODELO.forEach(function (e) { if (e.sec === 'sorpresa' && e.prob < .06 && e.p - ult >= 40 && e.p < 1060) { out.push([e.p, numero(e.prob)]); ult = e.p; } });
    return out;
  })();
  function voces(quien) {
    return function (ctx, dest, banco, en) {
      if (!banco) return;
      partitura().forEach(function (r, k) {
        if (r.quien !== quien) return;
        var op = quien === 'A' ? { porPalabra: true, rng: rngDe('a' + k), agendar: en } : { modo: 'psola', vibrato: [4.6, .005], rng: rngDe('g' + k), agendar: en };
        banco.cantar(dest, r.eventos, op);
      });
      if (quien === 'G') DICHO.forEach(function (d) { banco.decir(dest, d[1] * P16, d[2], { nota: 47, modo: 'psola', agendar: en }); });
      NUMEROS.forEach(function (n, i) {                                         // alternan las dos voces
        if ((i % 2 === 0) !== (quien === 'A')) return;
        banco.decir(dest, n[0] * P16 + .05, n[1], quien === 'A' ? { nota: 69, porPalabra: true, agendar: en } : { nota: 47, modo: 'psola', agendar: en });
      });
    };
  }

  var PISTAS = { pared: pared, muestra: muestra, evidencia: evidencia, pop: pop, reloj: reloj, ardilla: voces('A'), grave: voces('G') };
  global.Cancion = { PISTAS: Object.keys(PISTAS), pista: function (n) { return PISTAS[n]; }, partitura: partitura, modelo: function () { return MODELO; },
                     numeros: function () { return NUMEROS; }, CURVAS: CURVAS, SECC: SECC, DURACION: DURACION, T: T, P16: P16, COMPASES: COMPASES, PULSOS: PULSOS, hz: hz,
                     usaBanco: function (n) { return n === 'ardilla' || n === 'grave'; } };
})(typeof window !== 'undefined' ? window : globalThis);
