'use strict';
/* =====================================================================
   EL CLAVE BIEN TEÑIDO — cuerpo.js
   el puente entre el modelo y la materia. decide en qué peldaño de
   degradación está la pieza y construye el cuerpo de cada voz.

     peldaño 1 · completo    Tone + Web Audio + el `.wasm` de Faust en un
                             AudioWorklet: 32 parciales por voz
     peldaño 2 · sin Faust   ocho osciladores y una banda de ruido de Web
                             Audio: menos cuerpo, MISMA estructura, mismas
                             causas, mismos invariantes
     peldaño 3 · sin audio   no se construye nada; el modelo sigue igual
     peldaño 4 · sin matiz   no es asunto de este archivo (§12)

   los dos cuerpos aceptan exactamente el mismo estado. si la cadena no
   funciona sin Faust, tampoco funciona con él: significaría que el
   sistema depende del timbre y no de las relaciones.
   ===================================================================== */
(function (raiz) {

  const cargados = new WeakSet();     // contextos que ya registraron el worklet
  let WASM = null, META = null, peldano = 'sin-audio';
  /* el cuerpo nunca se disuelve del todo en ruido: el gris es un estado
     del modelo, no una orden de callarse. este piso mantiene la altura
     cuando el croma se agota. */
  const MIN_CUERPO_CROMA = 0.5;

  /* ---- preparación: una sola vez por contexto ------------------------ */
  async function preparar(ctx, base) {
    const raiz_ = base || '';
    if (!WASM) {
      try {
        const [w, m] = await Promise.all([
          fetch(raiz_ + 'dsp/cuerpo.wasm').then(r => { if (!r.ok) throw new Error(r.status); return r.arrayBuffer(); }),
          fetch(raiz_ + 'dsp/cuerpo.meta.json').then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
        ]);
        WASM = w; META = m;
      } catch (e) {
        WASM = null; META = null;
      }
    }
    if (WASM && !cargados.has(ctx)) {
      try {
        /* addModule una sola vez por procesador y por contexto: registrar
           dos veces el mismo nombre lanza y deja el grafo a medias. */
        await ctx.audioWorklet.addModule(raiz_ + 'worklets/cuerpo.js');
        cargados.add(ctx);
      } catch (e) {
        WASM = null; META = null;
      }
    }
    peldano = (WASM && META && cargados.has(ctx)) ? 'completo' : 'sin-faust';
    return peldano;
  }

  function estado() { return peldano; }

  /* ---- el cuerpo de Faust -------------------------------------------- */
  function cuerpoFaust(ctx, red) {
    const nodo = new AudioWorkletNode(ctx, 'cuerpo', {
      numberOfInputs: 0,
      numberOfOutputs: 1,
      outputChannelCount: [1],
      processorOptions: { wasm: WASM, meta: META }
    });
    let vivo = true;
    red.cuentas.faust++;
    red.cuentas.nodos++;
    const p = (n) => nodo.parameters.get(n);

    return {
      tipo: 'faust',
      salida: nodo,
      aplicar: function (par, cuando, dur) {
        if (!vivo) return;
        const t = cuando === undefined ? ctx.currentTime : cuando;
        const d = dur === undefined ? 0.08 : dur;
        const set = (n, v) => {
          const a = p(n);
          if (!a) return;
          const val = Math.max(a.minValue, Math.min(a.maxValue, v));
          /* rampas programadas contra el reloj de audio: una transición
             de veinte minutos se programa, no se anima cuadro a cuadro */
          a.cancelScheduledValues(t);
          a.setValueAtTime(a.value, t);
          a.linearRampToValueAtTime(val, t + Math.max(0.01, d));
        };
        set('f0', par.f0); set('estiramiento', par.estiramiento);
        set('desviacion', par.desviacion); set('croma', par.croma);
        set('rugosidad', par.rugosidad); set('interpolacion', par.interpolacion);
        set('ganancia', par.ganancia);
        const c = p('congelado');
        if (c) { c.cancelScheduledValues(t); c.setValueAtTime(par.congelado ? 1 : 0, t); }
        for (let j = 0; j < 8; j++) { set('a' + j, par.a[j] || 0); set('b' + j, par.b ? (par.b[j] || 0) : (par.a[j] || 0)); }
      },
      dispose: function () {
        if (!vivo) return;
        vivo = false;
        try { nodo.port.postMessage({ tipo: 'apagar' }); } catch (e) {}
        try { nodo.disconnect(); } catch (e) {}
        red.cuentas.faust--; red.cuentas.nodos--;
      }
    };
  }

  /* una sola fuente de ruido por contexto, creada la primera vez que
     alguna voz la necesita y desmontada con la red. */
  const fuentes = new WeakMap();
  function fuenteDeRuido(ctx, red) {
    if (fuentes.has(ctx)) return fuentes.get(ctx);
    const n = Math.floor(ctx.sampleRate * 1.5);
    const bufr = ctx.createBuffer(1, n, ctx.sampleRate);
    const d = bufr.getChannelData(0);
    /* ruido blanco por congruencia lineal: determinista, y sin
       `Math.random()` en ninguna parte de la pieza */
    let x = 22695477;
    for (let i = 0; i < n; i++) { x = (Math.imul(x, 1103515245) + 12345) >>> 0; d[i] = (x / 2147483648) - 1; }
    const src = ctx.createBufferSource();
    src.buffer = bufr; src.loop = true; src.start();
    fuentes.set(ctx, src);
    red.cuentas.ruidos += 1;
    red.cuentas.nodos += 1;
    red.ruidoCompartido = function () {
      try { src.stop(); src.disconnect(); } catch (e) {}
      fuentes.delete(ctx);
      red.cuentas.ruidos = Math.max(0, red.cuentas.ruidos - 1);
      red.cuentas.nodos = Math.max(0, red.cuentas.nodos - 1);
      red.ruidoCompartido = null;
    };
    return src;
  }

  /* ---- el cuerpo sin Faust -------------------------------------------
     una parada del gradiente = un oscilador. mismo contrato, misma
     estructura, menos parciales. */
  function cuerpoSimple(ctx, red) {
    const M = 4;                        // parciales por banda en el modelo
    const salida = ctx.createGain(); salida.gain.value = 1;
    const busTono = ctx.createGain(); busTono.gain.value = 1;
    const busRuido = ctx.createGain(); busRuido.gain.value = 0;
    busTono.connect(salida); busRuido.connect(salida);

    const oscs = [], gs = [], gemelos = [];
    for (let j = 0; j < 8; j++) {
      const o = ctx.createOscillator();
      o.type = j % 3 === 0 ? 'triangle' : 'sine';
      const g = ctx.createGain(); g.gain.value = 0.0001;
      o.connect(g); g.connect(busTono); o.start();
      oscs.push(o); gs.push(g);
      /* sólo las tres primeras bandas llevan gemelo: el batimiento se
         oye abajo, y arriba sólo ensuciaría */
      if (j < 3) {
        const o2 = ctx.createOscillator(); o2.type = 'sine';
        const g2 = ctx.createGain(); g2.gain.value = 0.0001;
        o2.connect(g2); g2.connect(busTono); o2.start();
        gemelos.push({ o: o2, g: g2, j: j });
      }
    }

    /* la banda de ruido: no es degradación sin estructura, es la voz
       cuando su croma se fue. la FUENTE es una sola para toda la pieza
       —el tope son tres— y cada voz la filtra en su propia banda: así el
       ruido de cada voz sigue centrado en su fundamental sin que haya
       dieciséis generadores corriendo a la vez. */
    const filtro = ctx.createBiquadFilter();
    filtro.type = 'bandpass'; filtro.frequency.value = 300;
    filtro.Q.value = 0.9;                                  // sin pico peligroso
    filtro.connect(busRuido);
    fuenteDeRuido(ctx, red).connect(filtro);

    red.cuentas.osciladores += oscs.length + gemelos.length;
    red.cuentas.nodos += oscs.length * 2 + gemelos.length * 2 + 5;

    let vivo = true;
    return {
      tipo: 'simple',
      salida: salida,
      aplicar: function (par, cuando, dur) {
        if (!vivo) return;
        const t = cuando === undefined ? ctx.currentTime : cuando;
        const dd = Math.max(0.02, dur === undefined ? 0.08 : dur);
        const cents = Math.pow(2, par.desviacion / 1200);
        for (let j = 0; j < 8; j++) {
          const k = j * M + 1;
          const f = Math.max(20, Math.min(ctx.sampleRate / 2.2, par.f0 * Math.pow(k, 1 + par.estiramiento) * cents));
          oscs[j].frequency.cancelScheduledValues(t);
          oscs[j].frequency.setValueAtTime(oscs[j].frequency.value, t);
          oscs[j].frequency.linearRampToValueAtTime(f, t + dd);
          /* la interpolación entre dos espectros existe también aquí: es
             la rampa de las ocho ganancias hacia el gradiente destino */
          const a = par.a[j] || 0, b = par.b ? (par.b[j] || 0) : a;
          const v = ((1 - par.interpolacion) * a + par.interpolacion * b) * par.ganancia * 0.22 / (1 + j * 0.35);
          gs[j].gain.cancelScheduledValues(t);
          gs[j].gain.setValueAtTime(gs[j].gain.value, t);
          gs[j].gain.linearRampToValueAtTime(Math.max(0.0001, v), t + dd);
        }
        for (const g of gemelos) {
          const k = g.j * M + 1;
          const f = Math.max(20, par.f0 * Math.pow(k, 1 + par.estiramiento) * cents * (1 + par.rugosidad * 0.006 * k));
          g.o.frequency.cancelScheduledValues(t);
          g.o.frequency.setValueAtTime(g.o.frequency.value, t);
          g.o.frequency.linearRampToValueAtTime(Math.min(ctx.sampleRate / 2.2, f), t + dd);
          const v = (par.a[g.j] || 0) * par.rugosidad * 0.7 * par.ganancia * 0.22;
          g.g.gain.cancelScheduledValues(t);
          g.g.gain.setValueAtTime(g.g.gain.value, t);
          g.g.gain.linearRampToValueAtTime(Math.max(0.0001, v), t + dd);
        }
        busTono.gain.cancelScheduledValues(t);
        busTono.gain.setValueAtTime(busTono.gain.value, t);
        busTono.gain.linearRampToValueAtTime(Math.max(0.0001, par.croma), t + dd);
        busRuido.gain.cancelScheduledValues(t);
        busRuido.gain.setValueAtTime(busRuido.gain.value, t);
        busRuido.gain.linearRampToValueAtTime(Math.max(0.0001, (1 - par.croma) * par.ganancia * 0.5), t + dd);
        filtro.frequency.setTargetAtTime(Math.max(40, Math.min(9000, par.f0 * 3)), t, 0.2);
        filtro.Q.setTargetAtTime(0.6 + par.rugosidad * 1.2, t, 0.3);
      },
      dispose: function () {
        if (!vivo) return;
        vivo = false;
        const ahora = ctx.currentTime;
        for (const o of oscs) { try { o.stop(ahora + 0.06); o.disconnect(); } catch (e) {} }
        for (const g of gemelos) { try { g.o.stop(ahora + 0.06); g.o.disconnect(); g.g.disconnect(); } catch (e) {} }
        for (const g of gs) { try { g.disconnect(); } catch (e) {} }
        try { filtro.disconnect(); busTono.disconnect(); busRuido.disconnect(); salida.disconnect(); } catch (e) {}
        red.cuentas.osciladores -= oscs.length + gemelos.length;
        red.cuentas.nodos -= oscs.length * 2 + gemelos.length * 2 + 5;
      }
    };
  }

  function crear(ctx, red) {
    const R = red.interno || red;
    const topes = red.TOPE || { faust: 8 };
    /* con el tope de nodos Faust alcanzado, las voces siguientes usan el
       cuerpo simple. no se calla ninguna voz por falta de cuerpo. */
    if (peldano === 'completo' && R.cuentas.faust < topes.faust) {
      try { return cuerpoFaust(ctx, R); } catch (e) { API.ultimoError = String(e && e.message || e); }
    }
    return cuerpoSimple(ctx, R);
  }

  /* ---- del modelo al cuerpo -----------------------------------------
     esta función es la frontera. de un lado hay colores, áreas y causas;
     del otro hay Hz y amplitudes. NO decide nada: traduce. */
  function parametros(org, v, COL) {
    const alt = COL.altura(v.color, org.temperamento, org.f0);
    const bandas = org.bandasDe(v);
    /* la erosión se lleva las bandas de arriba: cada regreso pierde
       parciales, y eso se oye como pérdida de brillo */
    for (let j = 8 - v.erosion; j < 8; j++) bandas[j] = 0;
    const inter = v.interpolacion
      ? Math.max(0, Math.min(1, (org.t - v.interpolacion.t0) / v.interpolacion.dur))
      : 0;

    const periodo = org.periodo(v);
    const enCanto = org.plano(v) === 'canto';
    const bandasVivas = bandas.slice();
    let desviacionExtra = 0;
    let factorCroma = 1;

    if (!v.congelado) {
      /* ---- A. articulación espectral: cada banda pico en un instante
         distinto del ciclo. la voz no sostiene un espectro plano: lo
         recorre como un arpegio de parciales. ---- */
      const fase = (((org.t - v.fase) % periodo) + periodo) % periodo / periodo;
      const piso = enCanto ? 0.15 : 0.35;
      for (let j = 0; j < 8; j++) {
        if (bandasVivas[j] <= 0) continue;
        let d = Math.abs(fase - j / 7);
        if (d > 0.5) d = 1 - d;
        bandasVivas[j] *= piso + (1 - piso) * Math.max(0, 1 - d * 2.5);
      }

      /* ---- C. entrada con crescendo espectral: las bandas graves
         entran antes que las agudas, como un cantante que construye
         su registro desde abajo. ---- */
      const tEntrada = v.entraEn !== undefined ? v.entraEn : v.nacida;
      const edad = org.t - tEntrada;
      if (v.estado === 'audible' && edad < periodo && edad > 0) {
        for (let j = 0; j < 8; j++) {
          const retardoBanda = (j / 7) * periodo * 0.55;
          const fb = Math.max(0, Math.min(1, (edad - retardoBanda) / (periodo * 0.7)));
          bandasVivas[j] *= fb;
        }
      }

      /* ---- B. el plano canto como registro expresivo: vibrato y
         respiración del croma. mover una pantalla arriba la vuelve
         cantante; abajo es masa sostenida. ---- */
      if (enCanto) {
        desviacionExtra = v.rugosidad * 24 * Math.sin(org.t * 5.5 * 2 * Math.PI);
        factorCroma = 1 + Math.sin(org.t / (periodo * 8) * 2 * Math.PI) * 0.1;
      }
    }

    /* el gris es un estado del color: cuando C se desvanece, la voz
       pierde brillo y color, pero conserva un piso de altura para que la
       pieza siga cantando en lugar de convertirse en ruido blanco. */
    const cuerpoCroma = Math.min(1,
      (v.color.C / COL.C_MAX * 3.2) * factorCroma + MIN_CUERPO_CROMA);

    return {
      f0: Math.max(20, Math.min(4000, alt.hz)),
      /* el eje del gradiente estira o comprime el banco de parciales */
      estiramiento: Math.max(-0.15, Math.min(0.15, Math.sin(v.eje * Math.PI / 180) * 0.06)),
      desviacion: Math.max(-150, Math.min(150, alt.cents + desviacionExtra)),
      croma: cuerpoCroma,
      rugosidad: Math.max(0, Math.min(1, v.rugosidad)),
      congelado: v.congelado ? 1 : 0,
      interpolacion: inter,
      ganancia: v.estado === 'audible' || v.estado === 'congelada' ? 1 : 0,
      a: v.interpolacion ? v.interpolacion.desde : bandasVivas,
      b: v.interpolacion ? v.interpolacion.hacia : bandasVivas
    };
  }

  const API = { preparar, crear, estado, parametros, get peldano() { return peldano; } };

  raiz.CLAVE = raiz.CLAVE || {};
  raiz.CLAVE.cuerpo = API;
  if (typeof module === 'object' && module.exports) module.exports = API;

})(typeof globalThis !== 'undefined' ? globalThis : this);
