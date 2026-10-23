/* difonos.js — el runtime: texto → difonos del banco → Web Audio. Sin dependencias (usa runtime/g2p.js).
 *
 *   const banco = await Difonos.cargar(ctx, 'bancos/sabina-1-b44e7fab5cee/');
 *   banco.cadena('palabra')                       → ['#p','pa','al','la','ab','br','ra','a#']  (con respaldo X# + #Y)
 *   banco.decir(destino, t0, texto, {nota})       → habla: duración natural, a una altura
 *   banco.cantar(destino, eventos, opciones)      → canta: eventos [{t, dur, texto, nota}] (una palabra por evento)
 *   banco.plan(eventos, opciones)                 → lo mismo, pero sin audio: la lista de piezas con sus tiempos (para probar)
 *
 * Cómo canta (afinación por VELOCIDAD, la «ardilla»: altura y formantes suben juntos, muy Vocaloid):
 *   · cada palabra va en su nota: velocidad = frecuencia de la nota / La3 (la altura del banco)
 *   · la primera vocal de la palabra cae EN el tiempo de la nota; las consonantes de arranque se adelantan
 *   · si la nota dura más que la palabra, las vocales se sostienen con lazos de su unidad vocal→misma vocal
 *   · las piezas se encadenan con fundidos de 2 × margen en las mitades de vocal
 *
 * Ardilla ligera ({porPalabra: true}): el mismo modo por velocidad, pero cada palabra es un buffer (para en vivo).
 * Modo PSOLA (F4, opciones {modo: 'psola'}): la altura cambia y el timbre NO. Los ciclos de la voz se vuelven a
 * poner al periodo de la nota; los formantes se quedan donde están y las consonantes duran lo natural. Sirve para
 * lo grave y lo lento (el ambient), donde la ardilla se vuelve un ogro. Cada frase se calcula en JS a un solo
 * buffer: un nodo por frase.
 */
(function (global) {
  'use strict';
  var G2P = global.DifonosG2P || (typeof require !== 'undefined' ? require('./g2p.js') : null);
  var VOC = 'aeiou';
  var hz = function (m) { return 440 * Math.pow(2, (m - 69) / 12); };

  /* ── la parte pura: de eventos a piezas con tiempos (se prueba en node) ── */
  function Plan(manifiesto) {
    this.M = manifiesto; this.U = manifiesto.unidades; this.sr = manifiesto.sr;
    this.margen = manifiesto.margen_s; this.base = hz(manifiesto.nota_base_midi);
  }
  Plan.prototype.dur = function (d) { var u = this.U[d]; return (u.der - u.izq) / this.sr; };   // duración natural (s)

  // difonos de una lista de fonemas, con respaldo para lo que el banco no tiene
  Plan.prototype.difonos = function (f) {
    var out = [], U = this.U;
    G2P.difonos(f).forEach(function (d) {
      if (U[d]) out.push(d);
      else { if (U[d[0] + '#']) out.push(d[0] + '#'); if (U['#' + d[1]]) out.push('#' + d[1]); }
    });
    return out;
  };
  Plan.prototype.cadena = function (texto) { return this.difonos(G2P.frase(texto)); };

  /* eventos → piezas [{tipo:'unidad'|'lazo', d, t, rate, dur, nota}]; t = cuándo empieza a sonar (s), dur = cuánto suena (s) */
  Plan.prototype.cantar = function (eventos, op) {
    op = op || {};
    var me = this, piezas = [], cursor = -Infinity, adelanto = op.adelanto == null ? 1 : op.adelanto;
    var psola = op.modo === 'psola';
    // la velocidad a la que corre el tiempo de las piezas: la de la nota (ardilla) o 1 (psola: la altura va aparte)
    var vel = function (e) { return psola ? 1 : hz(e.nota) / me.base; };
    // la frase entera en fonemas, recordando de qué palabra viene cada uno (para que las palabras se liguen)
    var fon = ['#'], palabraDe = [-1];
    eventos.forEach(function (e, i) {
      var f = G2P.frase(e.texto).slice(1, -1);
      if (e.pausa && fon[fon.length - 1] !== '#') { fon.push('#'); palabraDe.push(i); }
      f.forEach(function (x) { fon.push(x); palabraDe.push(x === '#' ? -1 : i); });
    });
    fon.push('#'); palabraDe.push(eventos.length - 1);
    // agrupar los difonos por la palabra que los «canta»: un difono pertenece a la palabra de su SEGUNDO fonema
    // (la consonante que entra a una palabra ya suena con la nota nueva), salvo el silencio final
    var grupos = eventos.map(function () { return []; });
    for (var k = 0; k + 1 < fon.length; k++) {
      if (fon[k] === '#' && fon[k + 1] === '#') continue;
      var due = palabraDe[k + 1] >= 0 ? palabraDe[k + 1] : palabraDe[k];
      if (due < 0) due = 0;
      var ds = this.difonos([fon[k], fon[k + 1]]);
      ds.forEach(function (d) { grupos[due].push(d); });
    }
    // primero, el arranque de cada palabra (lo que suena antes de su primera vocal): la palabra anterior sólo se
    // sostiene hasta donde empieza ese arranque (si no, la vocal siguiente llegaba tarde: medido, 4/41 a tiempo)
    var arr = eventos.map(function (e, i) {
      var rate = vel(e), ds = grupos[i];
      var iv = ds.findIndex(function (d) { return VOC.indexOf(d[1]) >= 0; }); if (iv < 0) iv = 0;
      var a = 0; for (var j = 0; j <= iv && j < ds.length; j++) a += me.dur(ds[j]) / rate;
      return a * adelanto;
    });
    eventos.forEach(function (e, i) {
      var rate = vel(e), f = hz(e.nota), ds = grupos[i];
      if (!ds.length) return;
      var t = Math.max(cursor, e.t - arr[i]);
      var limite = e.t + e.dur;
      if (i + 1 < eventos.length) limite = Math.min(limite, eventos[i + 1].t - arr[i + 1]);
      // cuánto le falta a la palabra para llegar a su límite: se reparte en lazos sobre sus vocales
      var natural = ds.reduce(function (s, d) { return s + me.dur(d) / rate; }, 0);
      var hueco = Math.max(0, limite - (t + natural));
      var vocales = ds.filter(function (d) { return VOC.indexOf(d[1]) >= 0 && me.U[d[1] + d[1]]; }).length || 1;
      ds.forEach(function (d) {
        var dd = me.dur(d) / rate;
        piezas.push({ tipo: 'unidad', d: d, t: t, dur: dd, rate: rate, f: f, palabra: i });
        t += dd;
        if (VOC.indexOf(d[1]) >= 0 && me.U[d[1] + d[1]] && hueco > 0) {     // sostener la vocal en que termina este difono
          var lazo = hueco / vocales;
          piezas.push({ tipo: 'lazo', d: d[1] + d[1], t: t, dur: lazo, rate: rate, f: f, palabra: i });
          t += lazo;
        }
      });
      cursor = t;
    });
    return piezas;
  };

  /* ── PSOLA (F4): cambiar la altura sin mover los formantes. Funciones puras (se prueban en node) ──
   * El banco viene aplanado a La3 por la fábrica: lo sonoro es casi periódico a f0 = base, así que los pulsos se
   * encuentran sin estimar la altura (una marca por ciclo, en el pico del ciclo). */
  var PSOLA = {};
  // marcas de la tira x[a, b): {pos, son}. Sonoro = la tira se parece a sí misma un periodo después (r > .5)
  PSOLA.marcas = function (x, a, b, sr, f0) {
    var P = sr / f0, L = Math.round(P), pos = [], son = [], t = a + 1, ult = null;
    var lis = function (i) { return x[i - 1] + 2 * x[i] + x[i + 1]; };
    var sonoro = function (c) {
      var i0 = Math.max(a, Math.round(c - P)), i1 = Math.min(b - L, Math.round(c + P) - L), sxy = 0, sxx = 0, syy = 0;
      if (i1 - i0 < L / 2) return false;
      for (var i = i0; i < i1; i++) { sxy += x[i] * x[i + L]; sxx += x[i] * x[i]; syy += x[i + L] * x[i + L]; }
      return sxx / (i1 - i0) > 1e-6 && sxy / Math.sqrt(sxx * syy + 1e-20) > .5;
    };
    while (t < b - 1) {
      if (sonoro(t + P / 2)) {
        var conPrevio = ult !== null && son[son.length - 1];
        var lo = conPrevio ? Math.max(t, Math.round(ult + .8 * P)) : t, hi = Math.min(b - 1, conPrevio ? Math.round(ult + 1.2 * P) : Math.round(t + P));
        if (hi <= lo) break;
        var m = lo; for (var i = lo + 1; i < hi; i++) if (lis(i) > lis(m)) m = i;
        pos.push(m); son.push(true); ult = m; t = Math.round(m + .5 * P);
      } else { pos.push(t); son.push(false); ult = t; t += L; }
    }
    return { pos: pos, son: son };
  };
  var cerca = function (pos, s) {                     // índice de la marca más cercana a s (búsqueda binaria)
    var lo = 0, hi = pos.length - 1;
    while (hi - lo > 1) { var md = (lo + hi) >> 1; if (pos[md] < s) lo = md; else hi = md; }
    return Math.abs(pos[hi] - s) < Math.abs(pos[lo] - s) ? hi : lo;
  };
  /* tramos [{o0, o1, fade, fuente(τ)→s, marcas, f(τ)→Hz}] en muestras de salida → Float32Array de n muestras desde y0.
   * En cada marca de síntesis τ: lo sonoro pone el ciclo más cercano de la fuente (ventana Hann de 2 periodos) y
   * avanza un periodo de la NOTA; lo sordo se copia tal cual (avanza un periodo de la fuente: identidad). Los tramos
   * que se enciman se funden con sus pesos, y la altura se desliza ~30 ms entre notas (ligado, sin escalón). */
  PSOLA.sintetizar = function (x, tramos, y0, n, P0, sr) {
    var T = Math.round(P0), y = new Float32Array(n), han = new Float32Array(2 * T), ini = Infinity, fin = -Infinity;
    for (var i = 0; i < 2 * T; i++) han[i] = .5 - .5 * Math.cos(Math.PI * i / T);
    tramos.forEach(function (tr) { ini = Math.min(ini, tr.o0); fin = Math.max(fin, tr.o1); });
    var tau = ini, lf = null, enSonoro = false, alineado = false, hopPrev = T;
    while (tau < fin) {
      var cub = [], son = false, fv = 0, wv = -1, dv = 0;
      for (var j = 0; j < tramos.length; j++) {
        var tr = tramos[j]; if (tau < tr.o0 || tau >= tr.o1) continue;
        var w = Math.min(1, (tau - tr.o0) / tr.fade, (tr.o1 - tau) / tr.fade), s = tr.fuente(tau), k = cerca(tr.marcas.pos, s);
        var v = !!tr.marcas.son[k] && Math.abs(tr.marcas.pos[k] - s) < P0;
        if (v && w > wv) {
          wv = w; fv = tr.f(tau); son = true;
          var k2 = tr.marcas.pos[k] >= s ? k : k + 1;           // el pulso siguiente: alinear sólo hacia ADELANTE
          dv = k2 < tr.marcas.pos.length && tr.marcas.son[k2] ? tr.marcas.pos[k2] - s : 0;
        }
        cub.push([tr, w, s, k, v]);
      }
      // al entrar a lo sonoro, la marca de síntesis se alinea con el pulso de la fuente (si no, cada ciclo queda
      // corrido y alguno se repite o se salta: a La3 la identidad daba r = .75). Sólo hacia adelante: hacia atrás
      // podía salirse del tramo y volver a alinear sin fin (se colgó en node con una vocal sola)
      if (son && !enSonoro && !alineado && dv >= 1) { tau += dv; alineado = true; continue; }
      alineado = false; enSonoro = son;
      if (!cub.length) {
        var sig = Infinity; tramos.forEach(function (q) { if (q.o0 > tau && q.o0 < sig) sig = q.o0; });
        tau = sig; lf = null; enSonoro = false; continue;
      }
      var hop = T;
      // el ligado dura ~30 ms de tiempo real: el paso del deslizamiento es el hop anterior (por marca, en lo grave
      // se alargaba a ~100 ms y las palabras cortas no llegaban a su nota: medido, 4/16 a más de 50 cents)
      if (son) { var l = Math.log(fv); lf = lf === null ? l : lf + (l - lf) * Math.min(1, hopPrev / (.03 * sr)); hop = sr / Math.exp(lf); }
      var comp = Math.max(.5, Math.min(2, Math.sqrt(hop / P0))), c0 = Math.round(tau) - y0;
      cub.forEach(function (c) {
        var centro = c[4] ? c[0].marcas.pos[c[3]] : Math.round(c[2]), g = c[1] * (c[4] ? comp : hop / T);
        for (var i = -T; i < T; i++) {
          var xi = centro + i, yi = c0 + i;
          if (xi >= 0 && xi < x.length && yi >= 0 && yi < n) y[yi] += g * han[i + T] * x[xi];
        }
      });
      tau += hop; hopPrev = hop;
    }
    return y;
  };

  /* ── el banco con audio ── */
  function Banco(ctx, buffer, manifiesto) {
    Plan.call(this, manifiesto); this.ctx = ctx; this.buffer = buffer;
  }
  Banco.prototype = Object.create(Plan.prototype);

  // una pieza: un AudioBufferSourceNode del sprite, con fundidos en sus márgenes
  Banco.prototype.tocar = function (destino, p, op) {
    var u = this.U[p.d], sr = this.sr, m = this.margen, ctx = this.ctx;
    var ini = (u.inicio + u.izq) / sr - m, largo = (u.der - u.izq) / sr + 2 * m;           // en segundos del banco
    var cuando = p.t - m / p.rate, suena = largo / p.rate, fade = Math.min(2 * m / p.rate, suena / 3);
    var g = ctx.createGain(); g.connect(destino);
    var nodos = [];
    var una = function (t0, dur, offset, fadeIn, fadeOut) {
      var s = ctx.createBufferSource(), lfo = null, lg = null; s.buffer = this.buffer; s.playbackRate.value = p.rate;
      if (op.vibrato && p.tipo === 'lazo') {                                // vibrato tardío en lo sostenido
        lfo = ctx.createOscillator(); lg = ctx.createGain(); lfo.frequency.value = op.vibrato[0];
        lg.gain.setValueAtTime(0, t0); lg.gain.linearRampToValueAtTime(p.rate * op.vibrato[1], t0 + Math.min(.3, dur));
        lfo.connect(lg).connect(s.playbackRate); lfo.start(t0); lfo.stop(t0 + dur + .05); nodos.push(lfo, lg);
      }
      var e = ctx.createGain(); s.connect(e).connect(g);
      // al acabar se suelta del grafo: un nodo terminado pero conectado se sigue procesando (medido en la portadora)
      s.onended = function () { e.disconnect(); if (lfo) { lfo.disconnect(); lg.disconnect(); } };
      e.gain.setValueAtTime(0, Math.max(0, t0)); e.gain.linearRampToValueAtTime(1, Math.max(0, t0) + fadeIn);
      e.gain.setValueAtTime(1, Math.max(0, t0 + dur - fadeOut)); e.gain.linearRampToValueAtTime(0, t0 + dur);
      s.start(Math.max(0, t0), Math.max(0, offset), dur * p.rate); s.stop(t0 + dur + .02); nodos.push(s, e);
    }.bind(this);
    if (p.tipo === 'unidad') {
      una(cuando, suena, ini, fade, fade);
    } else {                                                                  // lazo: granos de la vocal pura, encimados
      var grano = Math.min(.09, (u.der - u.izq) / sr) / p.rate, paso = grano * .5, r = op.rng || Math.random;
      for (var t = p.t - m / p.rate; t < p.t + p.dur; t += paso) {
        var off = (u.inicio + u.izq) / sr + r() * Math.max(0, (u.der - u.izq) / sr - grano * p.rate);
        una(t, grano + paso * .5, off, grano * .45, grano * .45);
      }
    }
    nodos.push(g); return nodos;
  };

  // las marcas de pulso de una unidad, en muestras del buffer decodificado (se calculan una vez, al usarla)
  Banco.prototype.marcasDe = function (d) {
    this._marcas = this._marcas || {};
    if (this._marcas[d]) return this._marcas[d];
    var u = this.U[d], k = this.buffer.sampleRate / this.sr;
    return (this._marcas[d] = PSOLA.marcas(this.buffer.getChannelData(0), Math.round(u.inicio * k), Math.round((u.inicio + u.largo) * k),
                                           this.buffer.sampleRate, this.base));
  };

  // una tanda de piezas encadenadas → {t, buffer}: la frase calculada con PSOLA, lista para un solo nodo
  Banco.prototype.renderPSOLA = function (tanda, op) {
    var me = this, srD = this.buffer.sampleRate, k = srD / this.sr, m = this.margen, P0 = srD / this.base, T = Math.round(P0);
    var x = this.buffer.getChannelData(0);
    var tramos = tanda.map(function (p) {
      var u = me.U[p.d], o0 = Math.round((p.t - m) * srD), o1 = Math.round((p.t + p.dur + m) * srD), fuente;
      if (p.tipo === 'unidad') {
        var srcA = (u.inicio + u.izq) * k - m * srD;
        fuente = function (tau) { return (u.inicio + u.izq) * k + (tau - p.t * srD) * (p.tasa_tiempo || 1); };
      } else {
        // lazo: casi quieto en el centro de la vocal (va y viene a ×0.05 por el 30 % central: una vuelta tarda más de
        // un segundo). Antes caminaba y saltaba atrás al azar cada 40-80 ms y los formantes brincaban: se oía como un
        // vibrato raro (medido en «epístrofe»: el timbre se movía 7-13 %, la mitad entre 3 y 14 Hz). Ir y venir a ×0.3
        // fue peor: una vuelta cada ~280 ms es un temblor de 3.6 Hz (71-84 % de la modulación en esa banda)
        var a = (u.inicio + u.izq) * k + T, b = (u.inicio + u.der) * k - T, cen = (a + b) / 2;
        if (b - a < 2 * T) fuente = function () { return cen; };
        else {
          var ancho = (b - a) * .3, ini = cen - ancho / 2;
          fuente = function (tau) { var x = ((tau - o0) * .05) % (2 * ancho); return ini + (x < ancho ? x : 2 * ancho - x); };
        }
      }
      var vib = op.vibrato && p.tipo === 'lazo' ? op.vibrato : null;
      return { o0: o0, o1: o1, fade: Math.max(1, Math.round(Math.min(2 * m * srD, (o1 - o0) / 3))), fuente: fuente, marcas: me.marcasDe(p.d),
               f: function (tau) {
                 if (!vib) return p.f;
                 var tt = (tau - o0) / srD; return p.f * (1 + vib[1] * Math.min(1, tt / .3) * Math.sin(2 * Math.PI * vib[0] * tt));
               } };
    });
    var y0 = Math.max(0, tramos[0].o0 - T), n = tramos[tramos.length - 1].o1 + T - y0;
    var y = PSOLA.sintetizar(x, tramos, y0, n, P0, srD), buf = this.ctx.createBuffer(1, n, srD);
    buf.copyToChannel(y, 0);
    return { t: y0 / srD, buffer: buf };
  };

  Banco.prototype.cantarPSOLA = function (destino, eventos, op) {
    var me = this, ctx = this.ctx, nodos = [], piezas = this.cantar_plan(eventos, op), m = this.margen;
    var nivel = ctx.createGain(); nivel.gain.value = op.nivel == null ? 1 : op.nivel; nivel.connect(destino);
    var tandas = [];                                  // piezas que se tocan (con sus fundidos) van en la misma tanda
    piezas.forEach(function (p) {
      var ult = tandas[tandas.length - 1], fin = ult && ult[ult.length - 1];
      if (fin && p.t - m <= fin.t + fin.dur + m + 1e-6) ult.push(p); else tandas.push([p]);
    });
    tandas.forEach(function (tanda) {
      var f = function () {
        var r = me.renderPSOLA(tanda, op), s = ctx.createBufferSource(), tarde = Math.max(0, ctx.currentTime - r.t);
        s.buffer = r.buffer; s.connect(nivel); s.start(r.t + tarde, tarde);     // si llega tarde, entra a tiempo ya empezada
        s.onended = function () { s.disconnect(); };
        return [s];
      };
      if (op.agendar) op.agendar(tanda[0].t - m, f); else nodos = nodos.concat(f());
    });
    nodos.push(nivel); return { piezas: piezas, nodos: nodos };
  };

  /* ardilla ligera ({porPalabra: true}): cada palabra se calcula a un buffer con PSOLA a la altura del banco (sus
   * vocales sostenidas, sin granos) y se toca a la velocidad de su nota. El mismo carácter que la ardilla granular,
   * con 1-3 nodos por palabra en vez de decenas de granos por segundo (en vivo, la nave de きくお saturaba el hilo
   * de audio: medido en la portadora). El vibrato va en playbackRate. */
  Banco.prototype.cantarPorPalabra = function (destino, eventos, op) {
    var me = this, ctx = this.ctx, nodos = [], piezas = this.cantar_plan(eventos, op), m = this.margen;
    var srD = this.buffer.sampleRate, S = m + 2 * Math.round(srD / this.base) / srD;
    var nivel = ctx.createGain(); nivel.gain.value = op.nivel == null ? 1 : op.nivel; nivel.connect(destino);
    var palabras = {};
    piezas.forEach(function (p) { (palabras[p.palabra] = palabras[p.palabra] || []).push(p); });
    Object.keys(palabras).forEach(function (k) {
      var ps = palabras[k], rate = ps[0].rate, tw = ps[0].t;
      var f = function () {
        // las piezas en tiempo del buffer (natural): t' = (t − tw)·rate + S, dur' = dur·rate; f = la del banco (identidad)
        var tanda = ps.map(function (p) { return { tipo: p.tipo, d: p.d, t: (p.t - tw) * rate + S, dur: p.dur * rate, f: me.base }; });
        var r = me.renderPSOLA(tanda, { rng: op.rng }), src = ctx.createBufferSource(), sal = [src];
        var inicio = tw + (r.t - S) / rate, tarde = Math.max(0, ctx.currentTime - inicio);
        src.buffer = r.buffer; src.playbackRate.value = rate; src.connect(nivel);
        var largo = r.buffer.duration / rate;
        if (op.vibrato && largo > .45) {                                       // vibrato tardío, como en los lazos
          var lfo = ctx.createOscillator(), lg = ctx.createGain(); lfo.frequency.value = op.vibrato[0];
          lg.gain.setValueAtTime(0, inicio + .25); lg.gain.linearRampToValueAtTime(rate * op.vibrato[1], inicio + .55);
          lfo.connect(lg).connect(src.playbackRate); lfo.start(inicio); lfo.stop(inicio + largo + .05); sal.push(lfo, lg);
          src.onended = function () { lfo.disconnect(); lg.disconnect(); src.disconnect(); };
        } else src.onended = function () { src.disconnect(); };
        src.start(inicio + tarde, tarde * rate);
        return sal;
      };
      if (op.agendar) op.agendar(tw - S / rate, f); else nodos = nodos.concat(f());
    });
    nodos.push(nivel); return { piezas: piezas, nodos: nodos };
  };

  Banco.prototype.cantar = function (destino, eventos, op) {
    op = op || {};
    if (op.modo === 'psola') return this.cantarPSOLA(destino, eventos, op);
    if (op.porPalabra) return this.cantarPorPalabra(destino, eventos, op);
    var me = this, nodos = [], piezas = this.cantar_plan(eventos, op);
    var nivel = this.ctx.createGain(); nivel.gain.value = op.nivel == null ? 1 : op.nivel; nivel.connect(destino);
    // op.agendar(t, f): quien llama decide CUÁNDO se crean los nodos de cada pieza (en vivo, justo antes de sonar;
    // armar todo al clic eran miles de nodos y el hilo de audio no alcanzaba: 3861 cortes en 44 s, medido).
    // f() devuelve los nodos de la pieza. Sin agendar, se arma todo de una vez (fuera de línea).
    piezas.forEach(function (p) {
      var f = function () { return me.tocar(nivel, p, op); };
      if (op.agendar) op.agendar(p.t - me.margen / p.rate, f); else nodos = nodos.concat(f());
    });
    nodos.push(nivel); return { piezas: piezas, nodos: nodos };
  };
  Banco.prototype.cantar_plan = Plan.prototype.cantar;
  Banco.prototype.plan = Plan.prototype.cantar;
  Banco.prototype.decir = function (destino, t0, texto, op) {
    op = op || {}; var palabras = texto.split(/\s+/).filter(Boolean), nota = op.nota == null ? this.M.nota_base_midi : op.nota;
    var me = this, t = t0, ev = palabras.map(function (w) {           // habla: cada palabra con su duración natural
      var d = me.difonos(G2P.frase(w)).reduce(function (s, x) { return s + me.dur(x); }, 0) * .82 / (op.modo === 'psola' ? 1 : hz(nota) / me.base);
      var e = { t: t, dur: d, texto: w, nota: nota, pausa: /[.,;:!?]$/.test(w) }; t += d; return e;
    });
    return this.cantar(destino, ev, op);
  };

  function cargar(ctx, ruta) {
    ruta = ruta.replace(/\/?$/, '/');
    return fetch(ruta + 'manifiesto.json').then(function (r) { return r.json(); }).then(function (M) {
      return fetch(ruta + 'banco.flac').then(function (r) { return r.arrayBuffer(); })
        .then(function (ab) { return ctx.decodeAudioData(ab); })
        .then(function (buf) { return new Banco(ctx, buf, M); });
    });
  }

  var api = { cargar: cargar, Plan: Plan, Banco: Banco, PSOLA: PSOLA, hz: hz };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.Difonos = api;
})(typeof window !== 'undefined' ? window : globalThis);

(function(){const original=Difonos.Banco.prototype.cantar_plan;Difonos.Banco.prototype.cantar_plan=function(es,op){
    const plan=original.call(this,es,{...op,adelanto:0}),groups=es.map(()=>[]);for(const p of plan)groups[p.palabra].push(p);
    for(let i=0;i<groups.length;i++){const g=groups[i];if(!g.length)continue;const a=Math.min(...g.map(p=>p.t)),b=Math.max(...g.map(p=>p.t+p.dur)),scale=es[i].dur/(b-a);
      for(const p of g){p.t=es[i].t+(p.t-a)*scale;p.dur*=scale;p.tasa_tiempo=1/scale;}}
    return plan;};})();