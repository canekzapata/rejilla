'use strict';
/* =====================================================================
   EL CLAVE BIEN TEÑIDO — tiempo.js
   Tone.js 14.8.49, copia local, como DIRECTOR DE ORQUESTA y no como
   instrumento. se queda con lo que hace mejor que nadie —el tiempo— y no
   toca el timbre, no elige presets y no compone.

   la criba decide qué pulsos existen; el Transport sólo los cuenta.
   los cánones de tempo van en relojes independientes con intervalo en
   SEGUNDOS: la notación («4n») ata a un solo tempo y mata a Nancarrow.

   nada de `setInterval` ni `requestAnimationFrame` para decisiones
   musicales. lo visual se programa con `Tone.Draw`, nunca desde el
   callback de audio.
   ===================================================================== */
(function (raiz) {

  const T = {
    org: null, ctx: null, encendido: false,
    pulso: null, lazos: [], cuerpos: {}, canales: {},
    n: 0, aplicados: 0, base: '',
    alDibujar: null, peldano: 'sin-audio',
    /* dentro del callback del Transport no se puede construir ni destruir
       un `Tone.Loop`: crear un evento de repetición ahí obliga a Tone a
       resolver «ahora» por su cuenta, y avisa —con razón—. así que el
       montaje y el desmontaje se encolan y ocurren fuera del reloj, con
       instantes absolutos calculados aquí dentro: la precisión musical no
       se pierde porque el instante ya está decidido. */
    dentroDelReloj: false, cola: [],
    /* un residuo es una voz que ya no está: un solo parcial que sigue
       sonando para que la irreversibilidad se oiga como acumulación. */
    residuos: []
  };
  const MAX_RESIDUOS = 8;

  function COL() { return raiz.CLAVE.color; }

  /* ---- residuo: un solo parcial de una voz que ya no está ------------
     la voz muerta deja de evolucionar, pero conserva una nota que se
     desvanece lentamente. la memoria no es decoración: es otra capa del
     campo, acumulada e irreversible. */
  function crearResiduo(v, par, t0) {
    if (!T.encendido || !T.ctx || !v) return;
    const ctx = T.ctx;
    const t = Math.max(t0 || ctx.currentTime, ctx.currentTime);

    /* espectro audible en el instante de morir: elige la banda más viva */
    const a = par.a || [], b = par.b || a;
    const inter = par.interpolacion || 0;
    let mejor = -1, mejorAmp = 0;
    for (let j = 0; j < 8; j++) {
      const amp = (1 - inter) * (a[j] || 0) + inter * (b[j] || a[j] || 0);
      if (amp > mejorAmp) { mejorAmp = amp; mejor = j; }
    }
    if (mejor < 0 || mejorAmp < 1e-4) return;

    const M = 4;                                    // parciales por banda
    const k = mejor * M + 1;
    const cents = Math.pow(2, Math.max(-150, Math.min(150, par.desviacion || 0)) / 1200);
    const f = Math.max(20, Math.min(ctx.sampleRate / 2.2,
      (par.f0 || 110) * Math.pow(k, 1 + Math.max(-0.15, Math.min(0.15, par.estiramiento || 0))) * cents));

    /* mismo plano y panorama que la voz muerta: no se desplaza */
    const canal = raiz.CLAVE.red.canal(T.org.plano(v), v.rect.x + v.rect.w / 2);
    const osc = ctx.createOscillator();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(f, t);

    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);

    osc.connect(g);
    g.connect(canal.entrada);
    osc.start(t);

    /* la amplitud respeta la curva de la voz: el gris deja un susurro
       armónico, no un eco de fábrica. */
    const croma = Math.max(0, Math.min(1, par.croma || 0));
    const amp = Math.max(0.0001, Math.min(0.18, mejorAmp * 0.06 * croma / (1 + mejor * 0.35)));
    const durSubida = 0.8, durRes = 14, durBajada = 8;
    g.gain.linearRampToValueAtTime(amp, t + durSubida);
    g.gain.setTargetAtTime(amp * 0.4, t + durSubida + durRes, durBajada * 0.35);
    g.gain.setValueAtTime(amp * 0.4, t + durSubida + durRes + durBajada);
    g.gain.exponentialRampToValueAtTime(0.0001, t + durSubida + durRes + durBajada + 3);

    const r = {
      voz: v.id,
      osc: osc, ganancia: g, canal: canal,
      dispose: function () {
        if (!r.vivo) return;
        r.vivo = false;
        const ahora = ctx.currentTime;
        try { g.gain.cancelScheduledValues(ahora); } catch (e) {}
        try { g.gain.setValueAtTime(g.gain.value, ahora); } catch (e) {}
        try { g.gain.exponentialRampToValueAtTime(0.0001, ahora + 0.3); } catch (e) {}
        try { osc.stop(ahora + 0.35); } catch (e) {}
        setTimeout(function () {
          try { osc.disconnect(); } catch (e) {}
          try { g.disconnect(); } catch (e) {}
          try { canal.dispose(); } catch (e) {}
        }, 500);
      }
    };
    r.vivo = true;

    if (T.residuos.length >= MAX_RESIDUOS) {
      const viejo = T.residuos.shift();
      if (viejo) viejo.dispose();
    }
    T.residuos.push(r);

    /* se desvanece solo */
    setTimeout(function () {
      const i = T.residuos.indexOf(r);
      if (i >= 0) T.residuos.splice(i, 1);
      r.dispose();
    }, Math.ceil((durSubida + durRes + durBajada + 5) * 1000));
  }

  function encolar(tarea) {
    T.cola.push(tarea);
    if (T.cola.length === 1) setTimeout(vaciarCola, 0);
  }

  function vaciarCola() {
    const tareas = T.cola; T.cola = [];
    for (const x of tareas) {
      if (!T.encendido) { if (x.desmontar) x.desmontar(); continue; }
      if (x.tipo === 'crear') { const v = T.org.voz(x.id); if (v) construirVoz(v); }
      else if (x.tipo === 'retirar') desmontar(x);
    }
  }

  /* ---- encender: SIEMPRE dentro del gesto de consentimiento ---------- */
  async function encender(org, opciones) {
    if (T.encendido) return T.peldano;
    const o = opciones || {};
    T.org = org;
    T.base = o.base || '';
    if (typeof Tone === 'undefined') { T.peldano = 'sin-audio'; return T.peldano; }

    /* UN SOLO AudioContext, y nativo.
       Tone 14.8 envuelve su contexto con `standardized-audio-context`, y
       ese envoltorio no es un `BaseAudioContext`: construir un
       `AudioWorkletNode` con él lanza. así que el contexto lo creamos
       nosotros y se lo entregamos a Tone —que es la manera documentada de
       compartirlo—. sigue habiendo uno solo: Faust, el worklet, el
       analizador y el limitador cuelgan de éste. */
    const AC = window.AudioContext || window.webkitAudioContext;
    let ctx = Tone.getContext().rawContext;
    if (!(typeof AC === 'function' && ctx instanceof AC)) {
      ctx = new AC({ latencyHint: 'interactive' });
      Tone.setContext(new Tone.Context(ctx));
    }
    await Tone.start();                      // jamás antes del gesto
    T.ctx = ctx;
    raiz.CLAVE.red.arrancar(ctx);
    T.peldano = await raiz.CLAVE.cuerpo.preparar(ctx, T.base);
    T.encendido = true;

    for (const v of org.audibles()) construirVoz(v);

    /* la rejilla: el Transport cuenta pulsos base y la criba dice cuáles
       existen. las mutaciones del expediente se aplican en un pulso que
       existe, no en el instante del clic. */
    Tone.Transport.bpm.value = 60;            // irrelevante: todo va en segundos
    T.pulso = Tone.Transport.scheduleRepeat(function (t) {
      T.dentroDelReloj = true;
      T.n++;
      /* el modelo avanza contra el reloj del audio, no contra el del
         navegador: así la obra suena lo que ya se calculó. */
      const eventos = org.avanzar(Tone.Transport.seconds);
      const existe = org.existePulso(T.n);
      const acento = org.acento.patron[T.n % org.acento.patron.length];
      if (existe) {
        T.aplicados++;
        aplicarTodo(t, acento ? 0.06 : 0.35);
      }
      for (const e of eventos) reaccionar(e, t);
      if (T.alDibujar) Tone.Draw.schedule(function () { T.alDibujar(org, eventos); }, t);
      T.dentroDelReloj = false;
    }, org.pulso);

    Tone.Transport.start('+0.05');
    return T.peldano;
  }

  /* un reloj por voz. el intervalo es su período en segundos, derivado
     del área: ahí viven las razones incompatibles. */
  function construirVoz(v) {
    if (T.cuerpos[v.id]) return T.cuerpos[v.id];
    if (T.dentroDelReloj) { encolar({ tipo: 'crear', id: v.id }); return null; }
    const org = T.org, red = raiz.CLAVE.red;
    const canal = red.canal(org.plano(v), v.rect.x + v.rect.w / 2);
    const cuerpo = raiz.CLAVE.cuerpo.crear(T.ctx, red);
    cuerpo.salida.connect(canal.entrada);
    T.cuerpos[v.id] = cuerpo;
    T.canales[v.id] = canal;

    const per = Math.max(0.05, org.periodo(v));
    const lazo = new Tone.Loop(function (t) {
      /* el ciclo de una voz no dispara una nota: hace girar su gradiente
         un paso. el movimiento espectral ES la música de una voz sola, y
         por eso una voz sola sigue sin producir acontecimientos. */
      const vv = org.voz(v.id);
      if (!vv || vv.congelado) return;
      if (vv.estado !== 'audible') return;
      vv.eje = (vv.eje + 3) % 360;
      aplicarVoz(vv, t, per * 0.9);
    }, per);
    /* la fase se conserva módulo el período: así el punto de convergencia
       del canon sigue cayendo donde el modelo dice. el instante de
       arranque es ABSOLUTO en el transporte —una voz puede nacer dentro
       de un callback ya programado, y ahí un tiempo relativo encadena
       imprecisiones—. */
    const ahoraT = (typeof Tone !== 'undefined' && Tone.Transport.state === 'started') ? Tone.Transport.seconds : 0;
    const desfase = (((v.fase - ahoraT) % per) + per) % per;
    lazo.start(ahoraT + desfase);
    T.lazos.push({ id: v.id, lazo: lazo });

    canal.ganancia.setValueAtTime(0.0001, T.ctx.currentTime);
    canal.ganancia.linearRampToValueAtTime(0.5, T.ctx.currentTime + 1.6);
    aplicarVoz(v, T.ctx.currentTime, 0.4);
    return cuerpo;
  }

  function aplicarVoz(v, t, dur) {
    const c = T.cuerpos[v.id];
    if (!c) return;
    c.aplicar(raiz.CLAVE.cuerpo.parametros(T.org, v, COL()), t, dur);
  }

  function aplicarTodo(t, dur) {
    const org = T.org;
    for (const v of org.audibles()) {
      if (!T.cuerpos[v.id]) construirVoz(v);
      aplicarVoz(v, t, dur);
    }
    /* las voces que murieron dejan de sonar, y sus nodos se van */
    for (const id in T.cuerpos) {
      const v = org.voz(id);
      if (!v || (v.estado !== 'audible' && v.estado !== 'congelada')) retirarVoz(id, t);
    }
  }

  function retirarVoz(id, t) {
    const canal = T.canales[id], cuerpo = T.cuerpos[id];
    if (!canal || !cuerpo) return;
    const v = T.org.voz(id);
    const ahora = t === undefined ? T.ctx.currentTime : t;
    /* silenciar es inmediato y no pasa por Tone: es una rampa de un
       AudioParam nativo contra el reloj del audio. */
    canal.ganancia.cancelScheduledValues(ahora);
    canal.ganancia.setValueAtTime(canal.ganancia.value, ahora);
    canal.ganancia.linearRampToValueAtTime(0.0001, ahora + 0.5);
    const lazos = T.lazos.filter(l => l.id === id);
    T.lazos = T.lazos.filter(l => l.id !== id);
    delete T.cuerpos[id]; delete T.canales[id];
    /* capturar el espectro en el instante de morir: el residuo no evoluciona,
       así que necesita el parámetro ya calculado. */
    const par = v ? raiz.CLAVE.cuerpo.parametros(T.org, v, COL()) : null;
    const tarea = {
      tipo: 'retirar', id: id, lazos: lazos, cuerpo: cuerpo, canal: canal,
      v: v, par: par, t: ahora,
      desmontar: function () { cuerpo.dispose(); canal.dispose(); }
    };
    if (T.dentroDelReloj) encolar(tarea); else desmontar(tarea);
  }

  /* disposición de verdad: los lazos primero, los nodos medio segundo
      después de la rampa. una voz fundida que sigue sonando es una fuga, y
      una fuga se oye. */
  function desmontar(tarea) {
    const tT = (typeof Tone !== 'undefined' && Tone.Transport.state === 'started') ? Tone.Transport.seconds : 0;
    for (const l of tarea.lazos) { try { l.lazo.stop(tT); l.lazo.dispose(); } catch (e) {} }
    /* la voz muerta deja un residuo: un solo parcial, sin evolución, que
       se desvanece. esto es lo que convierte la poda en memoria. */
    if (T.encendido && tarea.v && tarea.par) {
      crearResiduo(tarea.v, tarea.par, Math.max(tarea.t || tT, T.ctx.currentTime));
    }
    if (typeof Tone !== 'undefined' && Tone.Transport.state === 'started') {
      Tone.Transport.scheduleOnce(tarea.desmontar, tT + 0.7);
    } else tarea.desmontar();
  }

  /* los acontecimientos del modelo se vuelven audibles aquí. ninguno
     inventa material: sólo cambian la evolución de un cuerpo que ya
     venía sonando. */
  function reaccionar(e, t) {
    const org = T.org;
    if (e.tipo === 'entrada') {
      const v = org.voz(e.voz);
      if (v) construirVoz(v);
    } else if (e.tipo === 'choque' || e.tipo === 'interpolacion-completa') {
      aplicarTodo(t, 0.25);
    } else if (e.tipo === 'paralelas' || e.tipo === 'expulsion') {
      retirarVoz(e.voz, t);
    } else if (e.tipo === 'convergencia') {
      /* la convergencia no se subraya con un efecto: se oye porque todas
         las voces coinciden una vez. lo único que se hace es dejar de
         suavizar, para que la coincidencia no se difumine. */
      aplicarTodo(t, 0.02);
    }
  }

  /* ---- apagar: no queda ni un nodo vivo ni un evento en cola --------- */
  function apagar() {
    if (!T.encendido) return;
    if (typeof Tone !== 'undefined') {
      Tone.Transport.stop();
      Tone.Transport.cancel(0);
      if (T.pulso !== null) { try { Tone.Transport.clear(T.pulso); } catch (e) {} }
    }
    T.dentroDelReloj = false;
    for (const x of T.cola) if (x.desmontar) x.desmontar();
    T.cola = [];
    for (const l of T.lazos) { try { l.lazo.stop(0); l.lazo.dispose(); } catch (e) {} }
    for (const id in T.cuerpos) { try { T.cuerpos[id].dispose(); } catch (e) {} }
    for (const id in T.canales) { try { T.canales[id].dispose(); } catch (e) {} }
    for (const r of T.residuos) { try { r.dispose(); } catch (e) {} }
    T.lazos = []; T.cuerpos = {}; T.canales = {}; T.pulso = null; T.n = 0; T.aplicados = 0;
    T.residuos = [];
    raiz.CLAVE.red.apagar();
    T.encendido = false;
    T.ctx = null;
  }

  /* ---- prueba sin oídos ----------------------------------------------
     `Tone.Offline` rinde un búfer determinista sin dispositivo de audio.
     no usa el worklet —el peldaño 2 es justo el que tiene que sonar igual
     de estructurado— y por eso vale como prueba de que la estructura no
     depende del timbre. */
  async function renderOffline(semilla, segundos, guion) {
    const CP = raiz.CLAVE.contrapunto;
    const buf = await Tone.Offline(function (ctx) {
      const org = CP.crear(semilla);
      const red = raiz.CLAVE.red;
      red.apagar();
      red.arrancar(ctx.rawContext ? ctx.rawContext : ctx);
      const c = ctx.rawContext ? ctx.rawContext : ctx;
      /* en el render offline el maestro no necesita rampa de entrada: la
         pieza ya está en ejecución; el silencio inicial contaría como
         muestras mudas en la prueba. */
      if (red.maestro) {
        red.maestro.gain.cancelScheduledValues(0);
        red.maestro.gain.setValueAtTime(0.85, 0);
      }
      const cuerpos = {};
      for (const v of org.audibles()) {
        const canal = red.canal(org.plano(v), v.rect.x + v.rect.w / 2);
        const cuerpo = raiz.CLAVE.cuerpo.crear(c, red);
        cuerpo.salida.connect(canal.entrada);
        canal.ganancia.setValueAtTime(0.5, 0);
        cuerpo.aplicar(raiz.CLAVE.cuerpo.parametros(org, v, COL()), 0, 0.05);
        cuerpos[v.id] = { cuerpo: cuerpo, canal: canal };
      }
      let n = 0;
      ctx.transport.scheduleRepeat(function (t) {
        n++;
        org.avanzar(ctx.transport.seconds);
        if (guion) guion(org, n, t);
        if (!org.existePulso(n)) return;
        for (const v of org.audibles()) {
          const e = cuerpos[v.id];
          if (e) e.cuerpo.aplicar(raiz.CLAVE.cuerpo.parametros(org, v, COL()), t, 0.2);
        }
      }, org.pulso);
      ctx.transport.start(0.02);
    }, segundos, 1, 44100);
    return buf;
  }

  const API = {
    encender, apagar, renderOffline, construirVoz, retirarVoz, aplicarTodo,
    get encendido() { return T.encendido; },
    get peldano() { return T.peldano; },
    get pulsos() { return { contados: T.n, existentes: T.aplicados }; },
    get voces() { return Object.keys(T.cuerpos).length; },
    get lazos() { return T.lazos.length; },
    set alDibujar(f) { T.alDibujar = f; },
    interno: T
  };

  raiz.CLAVE = raiz.CLAVE || {};
  raiz.CLAVE.tiempo = API;
  if (typeof module === 'object' && module.exports) module.exports = API;

})(typeof globalThis !== 'undefined' ? globalThis : this);
