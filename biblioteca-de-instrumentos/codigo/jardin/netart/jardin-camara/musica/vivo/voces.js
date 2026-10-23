/* Voces del jardín en vivo: convierte los eventos de motor.js en sonido con Web Audio.
   Cada voz es la gemela de su función en Python (instrumentos.py, agua.py, aves.py,
   parlante.py, laberintos.voz_sostenida, afinidades.voz_pad/voz_bajo/bombo/hat), con nodos
   nativos: osciladores con PeriodicWave (los parciales exactos), rampas en AudioParam para
   deslizar, filtros biquad y una sala por convolución. Sirve igual para AudioContext (en
   vivo) y OfflineAudioContext (render de escucha y calibración).

   Mezcla: en Python cada capa se normaliza por su energía en toda la canción (por pico las
   aves y la resonancia) y después recibe su ganancia G + MEZCLA_EXTRA. En vivo no existe «toda
   la canción», así que NORMA guarda, por canción, el factor que esa normalización daría,
   medido en un render de calibración (escucha.html → calibrar). */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.JardinVoces = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";
  // ganancias de laberintos.mezclar (dB) y paneo/sala; las capas estéreo de Python (gotas_i/d,
  // pajaros_i/d) aquí son una sola con paneo por evento
  const G = { arriba: -15, abajo: -14, bajo: -12, linea: -13, sombras: -17, bombo: -15, hats: -30, gotas: -15, tambor: -19, pajaros: -25, resuena: -16 };
  const PAN = { arriba: -0.25, abajo: 0.2, bajo: 0, linea: 0.1, sombras: -0.05, bombo: 0, hats: 0.35, gotas: 0, tambor: 0.15, pajaros: 0, resuena: 0 };
  const SALA = { arriba: 0.45, abajo: 0.5, bajo: 0.05, linea: 0.35, sombras: 0.55, bombo: 0.05, hats: 0.2, gotas: 0.5, tambor: 0.35, pajaros: 0.9, resuena: 0.6 };
  const PICO = new Set(["pajaros", "resuena"]);
  const CAPAS = Object.keys(G);
  // factor de normalización por canción (lineal), medido con escucha.html; 1 = sin medir
  const NORMA = {};

  const PERFIL = {
    farfisa: { glide: 0.0, ataque: 0.006, release: 0.05, vib: [6.2, 0.0045, 0.0] },
    flauta: { glide: 0.045, ataque: 0.05, release: 0.18, vib: [4.6, 0.003, 0.35] },
    theremin: { glide: 0.14, ataque: 0.09, release: 0.35, vib: [5.6, 0.008, 0.08] },
    ondas: { glide: 0.1, ataque: 0.06, release: 0.3, vib: [5.4, 0.005, 0.25] },
  };
  const lp = (fk, fc, orden = 2) => 1 / Math.sqrt(1 + Math.pow(fk / fc, 2 * orden));

  function crear(ctx, opciones = {}) {
    const V = { ctx, cancion: null, nodos: 0 };
    const salida = opciones.destino || ctx.destination;
    const SR = ctx.sampleRate;
    // --- maestro: sala, compresor suave y medidor
    const maestro = ctx.createGain(); maestro.gain.value = 1;
    const comp = ctx.createDynamicsCompressor();
    comp.threshold.value = -12; comp.knee.value = 10; comp.ratio.value = 3; comp.attack.value = 0.01; comp.release.value = 0.25;
    const final = ctx.createGain(); final.gain.value = opciones.volumen ?? 0.9;
    // como laberintos.mezclar: tanh(1.1·x)/1.1 al final, por si algún pico pasa el compresor
    // (la curva de un WaveShaper se lee sobre la entrada en [−1, 1]: se escribe para ±2 y se entra a la mitad)
    const sat = ctx.createWaveShaper(), satEnt = ctx.createGain(); satEnt.gain.value = 0.5;
    { const c = new Float32Array(2049); for (let i = 0; i < c.length; i++) { const x = (i / 1024 - 1) * 2; c[i] = Math.tanh(1.1 * x) / 1.1; } sat.curve = c; }
    maestro.connect(comp); comp.connect(satEnt); satEnt.connect(sat); sat.connect(final); final.connect(salida);
    const medidor = ctx.createAnalyser(); medidor.fftSize = 2048; final.connect(medidor);
    const sala = ctx.createConvolver(); sala.buffer = irSala(ctx, 3.0, 4500); sala.connect(maestro);
    V.maestro = maestro; V.final = final; V.medidor = medidor;
    // --- ruido compartido
    const ruido = ctx.createBuffer(1, SR * 2, SR);
    { const d = ruido.getChannelData(0); let s = 12345; for (let i = 0; i < d.length; i++) { s = (Math.imul(s, 1103515245) + 12345) >>> 0; d[i] = (s / 2147483648 - 1); } }
    function fuenteRuido(t, dur) {
      const n = ctx.createBufferSource(); n.buffer = ruido; n.loop = true;
      n.start(t, Math.random() * 1.5); n.stop(t + dur + 0.05); return n;
    }
    // --- capas
    const capa = {};
    for (const k of CAPAS) {
      const entrada = ctx.createGain(), cede = ctx.createGain(), nivel = ctx.createGain(), pan = ctx.createStereoPanner(), envio = ctx.createGain();
      pan.pan.value = PAN[k]; envio.gain.value = SALA[k];
      entrada.connect(cede); cede.connect(nivel); nivel.connect(pan); pan.connect(maestro); pan.connect(envio); envio.connect(sala);
      capa[k] = { entrada, cede, nivel, pan, envio };
    }
    // el bajo satura suave (tanh) como voz_bajo
    { const ws = ctx.createWaveShaper(), c = new Float32Array(1024); for (let i = 0; i < 1024; i++) { const x = (i / 511.5 - 1) * 2; c[i] = Math.tanh(1.6 * x) / Math.tanh(1.6); } ws.curve = c;
      const ent = ctx.createGain(); ent.gain.value = 0.5; ent.connect(ws); ws.connect(capa.bajo.entrada); capa.bajo.sat = ent; }   // curva en ±2, entrada a la mitad
    // anillos del agua: ecos más oscuros
    { const f = ctx.createBiquadFilter(); f.type = "lowpass"; f.frequency.value = 3300; f.Q.value = 0.5; f.connect(capa.gotas.entrada); capa.gotas.anillos = f; }
    // las aves lejanas: el aire se come los agudos
    { const f = ctx.createBiquadFilter(); f.type = "lowpass"; f.frequency.value = 4000; f.Q.value = 0.5; f.connect(capa.pajaros.entrada); capa.pajaros.lejos = f; }
    // palme de las ondas: cuerdas simpáticas afinadas a la casa (se afina en ponerCancion)
    const palme = { entrada: ctx.createGain(), filtros: [] };
    { const salidaP = ctx.createGain(); salidaP.gain.value = 0.45 * 6; palme.salida = salidaP; salidaP.connect(capa.linea.entrada); }
    V.capa = capa;

    V.ponerCancion = (c, extra = {}) => {          // c: motor.cancion(...)
      V.cancion = c;
      const mez = c.g.mezcla || {}, norma = NORMA[c.g.titulo] || {};
      for (const k of CAPAS) {
        const db = G[k] + (mez[k] || 0) + (extra[k] || 0);
        capa[k].nivel.gain.value = Math.pow(10, db / 20) * (norma[k] ?? 1);
      }
      for (const k of ["gotas", "pajaros"]) if (c.g.sala?.[k] !== undefined) capa[k].envio.gain.value = c.g.sala[k];
      palme.filtros.forEach((f) => f.disconnect()); palme.filtros = [];
      for (const f of c.CASA_HZ) for (const o of [0.5, 1, 2]) {
        const bp = ctx.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.value = f * o; bp.Q.value = Math.min(1000, f * o * Math.PI * 3.0 / 6.91);
        palme.entrada.connect(bp); bp.connect(palme.salida); palme.filtros.push(bp);
      }
      maestro.gain.value = norma.maestro ?? 1;
      V.normaActual = norma;
    };
    V.niveles = () => Object.fromEntries(CAPAS.map((k) => [k, capa[k].nivel.gain.value]));

    // ------------------------------------------------------------ utilidades
    const ondas = new Map();
    function onda(amps, clave) {
      if (clave && ondas.has(clave)) return ondas.get(clave);
      const re = new Float32Array(amps.length + 1), im = new Float32Array(amps.length + 1);
      for (let i = 0; i < amps.length; i++) im[i + 1] = amps[i];
      const w = ctx.createPeriodicWave(re, im, { disableNormalization: true });
      if (clave) { if (ondas.size > 600) ondas.clear(); ondas.set(clave, w); }
      return w;
    }
    const cuant = (f) => Math.round(Math.log2(f) * 48);   // 1/4 de semitono para la caché de timbres
    function osc(t, fin, f, wave) {
      const o = ctx.createOscillator();
      if (wave) o.setPeriodicWave(wave);
      o.frequency.setValueAtTime(f, t);
      o.start(t); o.stop(fin); V.nodos++;
      o.onended = () => { V.nodos--; };
      return o;
    }
    function adsr(p, t, n, a, d, s, r, pico = 1) {    // como afinidades.env_adsr sobre n segundos
      p.setValueAtTime(0, t);
      p.linearRampToValueAtTime(pico, t + a);
      p.setTargetAtTime(s * pico, t + a, Math.max(d, 1e-3));
      p.setTargetAtTime(0, t + Math.max(a, n - r), r / 3);
    }
    function respira(t, fin, hz, prof, destino) {        // respiración lenta de la amplitud
      const g = ctx.createGain(); g.gain.value = 1;
      const l = osc(t, fin, hz), lg = ctx.createGain(); lg.gain.value = prof;
      l.connect(lg); lg.connect(g.gain); g.connect(destino);
      return g;
    }
    function curva(param, t, dur, fn, puntos) {          // muestrea fn(u) y la pone como curva
      const n = Math.max(2, puntos | 0), c = new Float32Array(n);
      for (let i = 0; i < n; i++) c[i] = fn(i / (n - 1));
      param.setValueCurveAtTime(c, t, Math.max(dur, 1e-3));
    }

    // ------------------------------------------------------------ voces
    const VOZ = {};
    // muro: voz_sostenida (armónicos 1–8 sin desafinación propia: los batimientos son del choque)
    VOZ.muro = (e, t) => {
      const k = "s" + cuant(e.f) + "-" + e.brillo, amps = [];
      for (let h = 1; h <= 8; h++) amps.push(e.f * h < 5000 ? (1 / Math.pow(h, 1.3)) / Math.sqrt(1 + Math.pow((e.f * h) / e.brillo, 4)) : 0);
      const n = e.d + 0.6, fin = t + n + 0.1, o = osc(t, fin, e.f, onda(amps, k)), env = ctx.createGain();
      adsr(env.gain, t, n, e.ataque, 1.0, 0.85, 0.55, (e.vel ?? 1) * 0.5);
      o.connect(env); env.connect(respira(t, fin, 0.08 + 0.12 * Math.random(), 0.1, capa[e.fam === "abajo" ? "abajo" : "arriba"].entrada));
    };
    // pad del subarmónico: voz_pad, dos copias que baten
    VOZ.pad = (e, t) => {
      const k = "p" + cuant(e.f) + "-" + e.brillo, amps = [];
      for (let h = 1; h <= 60 && e.f * h < 16000; h++) amps.push((1 / Math.pow(h, 1.6)) * lp(e.f * h, e.brillo, 2));
      const n = e.d + 1.4, fin = t + n + 0.1, env = ctx.createGain(), w = onda(amps, k);
      adsr(env.gain, t, n, 0.9, 1.5, 0.8, 1.3, 0.35);
      for (const s of [-0.15, 0.15]) osc(t, fin, e.f + s, w).connect(env);
      env.connect(respira(t, fin, 0.07 + 0.09 * Math.random(), 0.18, capa.abajo.entrada));
    };
    // bajo: sierra con filtro que se cierra + sub senoidal, saturación suave
    VOZ.bajo = (e, t) => {
      const amps = []; for (let h = 1; h < 24 && e.f * h <= 6000; h++) amps.push(1 / h);
      const n = e.d + 0.12, fin = t + n + 0.1, f = ctx.createBiquadFilter(), env = ctx.createGain();
      f.type = "lowpass"; f.Q.value = 0.707; f.frequency.setValueAtTime(1160, t); f.frequency.setTargetAtTime(260, t, 0.09);
      osc(t, fin, e.f, onda(amps, "b" + cuant(e.f))).connect(f);
      const sub = ctx.createGain(); sub.gain.value = 0.8; osc(t, fin, e.f).connect(sub); sub.connect(env);
      f.connect(env); adsr(env.gain, t, n, 0.004, 0.35, 0.6, 0.08, 0.5); env.connect(capa.bajo.sat);
    };
    // sombras subarmónicas: f/k + δ, casi paralelas a la nota, vibran a k·δ contra ella
    VOZ.sombra = (e, t) => {
      const amps = []; for (let h = 1; h <= 8; h++) amps.push(e.f * h < 5000 ? (1 / Math.pow(h, 1.3)) / Math.sqrt(1 + Math.pow((e.f * h) / 1800, 4)) : 0);
      const n = e.d + 0.6, env = ctx.createGain();
      adsr(env.gain, t, n, 0.05, 1.0, 0.85, 0.55, e.vel * 0.5);
      osc(t, t + n + 0.1, e.f, onda(amps, "o" + cuant(e.f))).connect(env); env.connect(capa.sombras.entrada);
    };
    // la línea del principal: una sola voz que desliza (instrumentos.linea + el timbre)
    VOZ.linea = (e, t0) => {
      const P = PERFIL[e.inst] || PERFIL.theremin, notas = e.notas.slice().sort((a, b) => a.t - b.t);
      const t = (x) => t0 + (x - e.t);
      const fs = notas.map((x) => x.f).sort((a, b) => a - b), fm = fs[Math.floor(fs.length / 2)];
      const fin = t(Math.max(...notas.map((x) => x.t + x.d))) + P.release * 5 + 0.1;
      let base = 1, amps;
      if (e.inst === "farfisa") {                     // 16' + 8' + 4' sobre f/2
        base = 0.5; amps = new Array(80).fill(0); amps[0] = 0.45;
        for (let k = 1; k < 40; k += 2) { if (fm * k > 12000) break; amps[2 * k - 1] += (1 / k) * lp(fm * k, 3800, 2); }
        for (let k = 1; k < 30; k += 2) { if (2 * fm * k > 12000 || 4 * k > 80) break; amps[4 * k - 1] += 0.5 * (1 / k) * lp(2 * fm * k, 3800, 2); }
        amps = amps.map((a) => a / 2.2);
      } else if (e.inst === "flauta") amps = [1, 0.22, 0.1, 0.04, 0.02, 0.01].map((a) => a / 1.4);
      else if (e.inst === "ondas") { amps = []; for (let k = 1; k <= 40 && fm * k < 12000; k++) amps.push(((k % 2 ? 1 / (k * k) : 0.08 / k) * lp(fm * k, 4000, 2)) / 1.2); }
      else amps = [1, 0.12, 0.05, 0.015].map((a) => a / 1.1);
      const o = osc(t(notas[0].t), fin, notas[0].f * base, onda(amps, e.inst + cuant(fm)));
      const env = ctx.createGain(); env.gain.setValueAtTime(0, t(notas[0].t));
      o.connect(env);
      // vibrato tardío en cents
      const [vhz, vprof, vret] = P.vib, lfo = osc(t(notas[0].t), fin, vhz), prof = ctx.createGain();
      const D = 1200 * Math.log2(1 + vprof);
      prof.gain.setValueAtTime(vret > 0 ? 0 : D, t(notas[0].t)); lfo.connect(prof); prof.connect(o.detune);
      let prevFin = -1, previa = null;
      notas.forEach((x, i) => {
        const a = t(x.t), sig = notas[i + 1];
        let ligada = sig && sig.t <= x.t + x.d + 0.06;
        if (ligada && Math.abs(Math.log2(sig.f / x.f)) < 1e-3) ligada = false;    // repetida: corte y nuevo ataque
        let b = ligada ? t(sig.t) : a + x.d;
        if (!ligada && sig && sig.t <= x.t + x.d + 0.06) b = Math.max(a + 0.001, t(sig.t) - 0.045);
        if (i === 0 || P.glide === 0) o.frequency.setValueAtTime(x.f * base, a);
        else o.frequency.setTargetAtTime(x.f * base, a, P.glide / 3);
        env.gain.setTargetAtTime(x.vel * 0.5, a, previa !== null && x.vel < previa ? P.release : P.ataque);
        if (!ligada) env.gain.setTargetAtTime(0, b, P.release);
        if (vret > 0 && (previa === null || Math.abs(Math.log2(x.f / notas[i - 1].f)) > 1e-4)) {
          prof.gain.setValueAtTime(0, a); prof.gain.setValueAtTime(0, a + vret); prof.gain.linearRampToValueAtTime(D, a + vret + 0.3);
        }
        if (a > prevFin + 0.02) ataque(e.inst, a, x.vel, env);
        prevFin = b; previa = x.vel;
      });
      if (e.inst === "flauta") {                      // soplo filtrado, siempre bajo la envolvente
        const bp = ctx.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.value = 1300; bp.Q.value = 0.45;
        const g = ctx.createGain(); g.gain.value = 0.09 * 3;
        fuenteRuido(t(notas[0].t), fin - t(notas[0].t)).connect(bp); bp.connect(g); g.connect(env);
      }
      env.connect(capa.linea.entrada);
      if (e.inst === "ondas") env.connect(palme.entrada);
      // la línea manda: gotas y aves ceden hasta −8 dB mientras suena
      if (opciones.cede !== false && V.cancion?.g.cede) for (const k of ["gotas", "pajaros"]) {
        capa[k].cede.gain.setTargetAtTime(0.4, t(notas[0].t), 0.08);
        capa[k].cede.gain.setTargetAtTime(1, fin - P.release * 4, 0.3);
      }
    };
    function ataque(inst, a, vel, destino) {          // chiff de flauta, clic de tecla de la Farfisa
      if (inst !== "flauta" && inst !== "farfisa") return;
      const d = inst === "flauta" ? 0.035 : 0.004, g = ctx.createGain(), bp = ctx.createBiquadFilter();
      bp.type = "bandpass"; bp.frequency.value = inst === "flauta" ? 2400 : 3000; bp.Q.value = 0.7;
      g.gain.setValueAtTime((inst === "flauta" ? 0.5 : 0.3) * vel * 1.5, a); g.gain.linearRampToValueAtTime(0, a + d);
      fuenteRuido(a, d).connect(bp); bp.connect(g); g.connect(destino);
    }
    // gota-burbuja (Minnaert): casi seno que sube mientras se apaga, con anillos
    function burbuja(f, chirp, tau, amp, pan, t, destino) {
      const o = osc(t, t + tau * 7 + 0.05, f), g = ctx.createGain(), p = ctx.createStereoPanner();
      o.frequency.linearRampToValueAtTime(f * (1 + chirp), t + 4 * tau);
      g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(amp, t + 0.0025); g.gain.setTargetAtTime(0, t + 0.0025, tau);
      p.pan.value = Math.max(-1, Math.min(1, pan));
      o.connect(g); g.connect(p); p.connect(destino);
    }
    VOZ.gota = (e, t) => {
      burbuja(e.f, e.chirp, e.tau, e.amp * 0.5, e.pan, t, capa.gotas.entrada);
      for (let r = 0; r < e.anillos; r++) burbuja(e.f, e.chirp, e.tau, e.amp * 0.5 * Math.pow(0.5, r + 1), e.pan * 0.7, t + 0.09 + 0.07 * r + (e.eco || 0), capa.gotas.anillos);
    };
    // el agua canta: dos notas ligadas que se deslizan, con resonancia larga
    VOZ.aguaCanto = (e, t) => {
      let a = e.a, b = e.b; while (a < 500) a *= 2; while (b < 500) b *= 2;
      const sep = Math.min(1.6, Math.max(0.3, e.sep)), dur = sep + 1.4;
      const fr = (u) => { const tt = u * dur, tr = Math.min(1, Math.max(0, (tt - sep * 0.6) / (sep * 0.5))); return a * Math.pow(b / a, tr * tr * (3 - 2 * tr)) * (1 + 0.03 * Math.exp(-tt / 0.05)); };
      const am = (u) => { const tt = u * dur; return (1 - Math.exp(-tt / 0.02)) * Math.exp(-tt / (dur * 0.45)) * (1 + 0.4 * Math.exp(-Math.pow((tt - sep) / 0.08, 2))); };
      const p = ctx.createStereoPanner(); p.pan.value = e.pan; p.connect(capa.gotas.entrada);
      const n = Math.ceil(dur * 200);
      for (const [mult, prof, tau2] of [[1, 1, 0], [2, 0.18, 0.3]]) {
        const o = osc(t, t + dur + 0.05, a * mult), g = ctx.createGain();
        curva(o.frequency, t, dur, (u) => fr(u) * mult, n);
        curva(g.gain, t, dur, (u) => e.vel * 0.5 * prof * am(u) * (tau2 ? Math.exp(-(u * dur) / tau2) : 1), n);
        o.connect(g); g.connect(p);
      }
      for (const x of e.gotitas || []) burbuja(x.f, x.chirp, x.tau, x.amp * 0.5 * e.vel, e.pan, t + x.dt * dur, capa.gotas.entrada);
    };
    // aves: trazos de silbido, trino, pío y llamado en una sola voz con su 2.º armónico
    const ONDA_AVE = () => onda([1, 0.12], "ave");
    VOZ.ave = (e, t) => {
      const dur = e.dur + 0.05, n = Math.max(8, Math.ceil(dur * 1500)), fr = new Float32Array(n), am = new Float32Array(n);
      let fUlt = e.trazos.length ? e.trazos[0].a : 2000;
      const tr = e.trazos.slice().sort((x, y) => x.t - y.t);
      let j = 0;
      for (let i = 0; i < n; i++) {
        const tt = (i / (n - 1)) * dur;
        while (j < tr.length && tt > tr[j].t + tr[j].d) j++;
        const z = tr[j];
        if (z && tt >= z.t) {
          const u = (tt - z.t) / z.d, s = Math.sin(Math.PI * u);
          let f, a;
          if (z.tipo === "silbido") { f = z.a * Math.pow(z.b / z.a, Math.pow(u, z.curva)); a = Math.pow(s, 0.7); }
          else if (z.tipo === "trino") { const c = 0.5 + 0.5 * Math.tanh(4 * Math.sin(2 * Math.PI * z.vel * (tt - z.t))); f = z.a * Math.pow(z.b / z.a, c); a = Math.pow(s, 0.5) * (0.6 + 0.4 * c); }
          else if (z.tipo === "pio") { f = z.a * (0.8 + 0.3 * u); a = Math.pow(s, 0.6); }
          else if (z.tipo === "llama1") { f = z.a; a = s; }
          else { f = z.a * (1 - 0.12 * u * u); a = Math.pow(s, 0.6); }
          fr[i] = fUlt = f; am[i] = a;
        } else { fr[i] = fUlt; am[i] = 0; }
      }
      const o = osc(t, t + dur + 0.05, fr[0], ONDA_AVE()), g = ctx.createGain(), p = ctx.createStereoPanner();
      o.frequency.setValueCurveAtTime(fr, t, dur);
      for (let i = 0; i < n; i++) am[i] *= e.vol * 0.5;
      g.gain.setValueCurveAtTime(am, t, dur);
      p.pan.value = e.pan; o.connect(g); g.connect(p); p.connect(capa.pajaros.lejos);
    };
    // tambor parlante: membrana (modos de Bessel) cuyo tono se desliza mientras suena
    const MODOS = [[1.0, 1.0, 1.0], [1.594, 0.55, 0.6], [2.136, 0.38, 0.45], [2.296, 0.3, 0.4], [2.653, 0.18, 0.3], [2.918, 0.12, 0.25]];
    VOZ.golpe = (e, t) => {
      const tau = e.apagado ? 0.09 : 0.28, g = ctx.createGain(); g.gain.value = e.vel / 2 * 0.6; g.connect(capa.tambor.entrada);
      for (const [r, a, d] of MODOS) {
        const o = osc(t, t + e.largo + 0.05, r * e.desde), gm = ctx.createGain();
        o.frequency.setTargetAtTime(r * e.hasta, t, e.glide);
        gm.gain.setValueAtTime(a, t); gm.gain.setTargetAtTime(0, t, tau * d);
        o.connect(gm); gm.connect(g);
      }
      const bp = ctx.createBiquadFilter(), gp = ctx.createGain(); bp.type = "bandpass"; bp.frequency.value = 3400; bp.Q.value = 0.8;
      gp.gain.setValueAtTime(e.apagado ? 0.6 : 0.35, t); gp.gain.setTargetAtTime(0, t, 0.004);
      fuenteRuido(t, 0.05).connect(bp); bp.connect(gp); gp.connect(g);
    };
    VOZ.bombo = (e, t) => {
      const o = osc(t, t + 0.55, 141), g = ctx.createGain();
      o.frequency.setTargetAtTime(46, t, 0.035);
      g.gain.setValueAtTime(e.vel, t); g.gain.setTargetAtTime(0, t, 0.28);
      o.connect(g); g.connect(capa.bombo.entrada);
    };
    VOZ.hat = (e, t) => {
      const h1 = ctx.createBiquadFilter(), h2 = ctx.createBiquadFilter(), g = ctx.createGain();
      h1.type = h2.type = "highpass"; h1.frequency.value = h2.frequency.value = 7500;
      g.gain.setValueAtTime(e.vel, t); g.gain.setTargetAtTime(0, t, 0.022);
      fuenteRuido(t, 0.1).connect(h1); h1.connect(h2); h2.connect(g); g.connect(capa.hats.entrada);
    };
    // resonancia simpática: el parcial del muro que el ave enciende
    VOZ.resuena = (e, t) => {
      for (const [mult, a, ta, td] of [[1, 1, 0.12, 0.9], [0.5, 0.3, 0.3, 1.3]]) {
        const o = osc(t, t + 2.65, e.f * mult), g = ctx.createGain();
        curva(g.gain, t, 2.6, (u) => { const tt = u * 2.6; return 0.5 * a * (1 - Math.exp(-tt / ta)) * Math.exp(-tt / td); }, 160);
        o.connect(g); g.connect(capa.resuena.entrada);
      }
    };
    VOZ.flor = () => {};
    // limpiar: las capas que se quedan (sombras, resonancia) se apagan y vuelven despacio
    // calderón: la nota de la flor se queda en el muro hasta que la mano se va (V.soltar); entra lento
    // y, si nadie la suelta, se apaga sola a los 30 s
    const sostenidos = new Map();
    VOZ.calderon = (e, t) => {
      const voces = [];
      const una = (f, amp, capaK, brillo) => {
        const amps = []; for (let h = 1; h <= 8; h++) amps.push(f * h < 5000 ? (1 / Math.pow(h, 1.3)) / Math.sqrt(1 + Math.pow((f * h) / brillo, 4)) : 0);
        const o = osc(t, t + 34, f, onda(amps, "c" + cuant(f) + "-" + brillo)), g = ctx.createGain();
        g.gain.setValueAtTime(0, t); g.gain.setTargetAtTime(amp, t, 0.5); g.gain.setTargetAtTime(0, t + 30, 1.0);
        o.connect(g); g.connect(respira(t, t + 34, 0.1 + 0.1 * Math.random(), 0.12, capa[capaK].entrada));
        voces.push({ o, g });
      };
      una(e.f, 0.45, "arriba", e.brillo || 3000);
      for (const s of e.sombras) una(s.f, 0.3 / Math.pow(s.k, 0.3), "sombras", 1800);
      sostenidos.set(e.id, voces);
    };
    V.soltar = (id) => {
      const vs = sostenidos.get(id); if (!vs) return false;
      const t = ctx.currentTime;
      for (const { o, g } of vs) { g.gain.cancelScheduledValues(t); g.gain.setValueAtTime(g.gain.value, t); g.gain.setTargetAtTime(0, t, 0.8); try { o.stop(t + 5); } catch (e) {} }
      sostenidos.delete(id); return true;
    };
    VOZ.limpia = (e, t) => {
      for (const k of ["sombras", "resuena"]) {
        const g = capa[k].cede.gain;
        g.cancelScheduledValues(t); g.setTargetAtTime(0.08, t, e.seg / 4); g.setTargetAtTime(1, t + e.seg + 1.5, 1.0);
      }
    };

    // t0: tiempo de audio en que empieza la canción (evento.t = 0)
    V.tocar = (e, t0) => {
      const t = t0 + e.t;
      if (t < ctx.currentTime - 0.01 && !(e.tipo === "muro" || e.tipo === "pad")) return false;
      const f = VOZ[e.tipo];
      if (!f) return false;
      if (e.tipo === "linea") f(e, Math.max(t, ctx.currentTime + 0.005));
      else f(e, Math.max(t, ctx.currentTime + 0.005));
      return true;
    };
    V.nivelDb = () => {                             // RMS de lo que sale, en dBFS
      const b = new Float32Array(medidor.fftSize); medidor.getFloatTimeDomainData(b);
      let s = 0; for (const x of b) s += x * x; return 10 * Math.log10(s / b.length + 1e-12);
    };
    V.desvanecer = (seg = 1.2) => { final.gain.setTargetAtTime(0, ctx.currentTime, seg / 4); };
    V.capas = CAPAS;
    return V;
  }

  function irSala(ctx, seg, corte) {               // como afinidades.ir_sala: ruido que decae, oscuro
    const SR = ctx.sampleRate, n = Math.floor(seg * SR), b = ctx.createBuffer(2, n, SR);
    const a = Math.exp(-2 * Math.PI * corte / SR);
    for (let c = 0; c < 2; c++) {
      const d = b.getChannelData(c); let y = 0, s = 777 + c * 31337, e = 0;
      for (let i = 0; i < n; i++) {
        s = (Math.imul(s, 1664525) + 1013904223) >>> 0;
        const x = (s / 2147483648 - 1) * Math.exp((-6.91 * i) / n);
        y = (1 - a) * x + a * y; d[i] = i < SR * 0.012 ? 0 : y; e += y * y;
      }
      const k = 1 / Math.sqrt(e / 0.5 + 1e-12); for (let i = 0; i < n; i++) d[i] *= k;
    }
    return b;
  }

  return { crear, NORMA, G, PAN, SALA, PICO, CAPAS };
});
