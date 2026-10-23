/* Motor gemelo del jardín musical: las mismas leyes que musica/temas (serie de día v1.9.1),
   en JS y en tiempo real. Sólo lógica: devuelve EVENTOS con tiempo (segundos de canción) que
   voces.js convierte en sonido con Web Audio. Corre igual en el navegador y en Node (pruebas).

   Gemelo, no copia: el azar es otro (mulberry32, no numpy), así que los caminos del laberinto
   no son los mismos que en los .m4a. Lo determinista sí es idéntico y se comprueba en
   pruebas/gemelo.cjs contra pruebas/referencia-python.json: FU, casa, tiempos, gemela,
   rugosidad y afinar.

   Lo que cambia en vivo (ver ../06-EL-JARDIN-SUENA-EN-VIVO.md):
   - el muro camina solo, por ciclos que salen de casa y regresan (un ciclo = una canción);
   - tocar una flor es una VISITA: su armónico n es la tónica de la escala del choque;
   - arrastrar entre flores mientras el principal canta: carreras de agua-arpa en la escala
     de cada flor, con sus sombras subarmónicas casi paralelas, vibrando;
   - si nadie toca, el jardín visita sus flores como en la serie (cada paso del caminante). */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.JardinMotor = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";
  const VERSION = "jardin-vivo-v0.1 (gemelo de serie-del-jardin-v1.9.1, día)";

  // ------------------------------------------------------------ azar sembrado
  function azar(semilla) {
    let s = (Math.imul((semilla | 0) ^ 0x5bd1e995, 0x9e3779b1) ^ 0x7f4a7c15) >>> 0;
    const r = {};
    r.random = () => {
      s = (s + 0x6d2b79f5) >>> 0;
      let t = s;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
    r.integers = (lo, hi) => (hi === undefined ? Math.floor(r.random() * lo) : lo + Math.floor(r.random() * (hi - lo)));
    r.uniform = (a, b) => a + (b - a) * r.random();
    r.choice = (arr, p) => {
      if (!p) return arr[Math.floor(r.random() * arr.length)];
      const tot = p.reduce((a, b) => a + b, 0);
      let x = r.random() * tot;
      for (let i = 0; i < arr.length; i++) { x -= p[i]; if (x < 0) return arr[i]; }
      return arr[arr.length - 1];
    };
    r.choiceN = (arr, k, p) => {            // sin reemplazo
      const a = arr.slice(), w = p ? p.slice() : arr.map(() => 1), out = [];
      for (let j = 0; j < k && a.length; j++) {
        const tot = w.reduce((x, y) => x + y, 0);
        let x = r.random() * tot, i = 0;
        for (; i < a.length - 1; i++) { x -= w[i]; if (x < 0) break; }
        out.push(a[i]); a.splice(i, 1); w.splice(i, 1);
      }
      return out;
    };
    let extra = null;
    r.normal = (mu = 0, sd = 1) => {
      if (extra !== null) { const z = extra; extra = null; return mu + sd * z; }
      const u = Math.max(1e-12, r.random()), v = r.random(), m = Math.sqrt(-2 * Math.log(u));
      extra = m * Math.sin(2 * Math.PI * v);
      return mu + sd * m * Math.cos(2 * Math.PI * v);
    };
    r.exponential = (escala) => -escala * Math.log(1 - r.random());
    return r;
  }

  const log2 = Math.log2, sum = (a) => a.reduce((x, y) => x + y, 0);
  const clip = (x, a, b) => (x < a ? a : x > b ? b : x);
  const pmod = (a, n) => ((a % n) + n) % n;

  // ------------------------------------------------------------ genomas (serie.py, día)
  const tensiones = {
    agua: (x) => 0.12 + 0.28 * Math.pow(Math.max(0, Math.sin(2 * Math.PI * 3 * x)), 3),
    florecer: (x) => 0.1 + 0.45 * Math.pow(Math.sin(Math.PI * Math.min(1, x / 0.8)), 2),
    subida: (x) => Math.min(1, x / 0.6),
  };
  const DIA = {
    voces: 3, bajo_de: "arriba", sub_arriba: true, batido: [0.3, 1.0], brillo: [3200, 2600],
    mezcla: { arriba: -1, abajo: -6, sombras: -4, bajo: -2, gotas: -11, pajaros: 19, resuena: 10 },
    agua: true, parlante: true, gotas: { n: [3, 8], octavas: [0, 1, 1, 2] }, cede: true,
    sala: { gotas: 0.85, pajaros: 0.55 }, tambor_libre: 0.5, principal: "aprende", agua_canta: true,
    principal_guarda: true, vericuetos: true, crecer: false, resonancia_aves: true, agua_arpa: true, bordon: false,
  };
  const SERIE_DIA = [
    Object.assign({}, DIA, { porte: "espiga", titulo: "tizita-mayor", semilla: 31, F0: 36.75, K: 180, rango: [8, 20], span: 11,
      pasos: [4, 6], bpm: 100, seg: 85, lente: "etiope-clara", instrumento: "farfisa", pulso: "agua_68", silencio: 0.25,
      tension: "agua", aves: { especies: ["primavera", "cenzontle"], alba: false, imitar: 0.5, presentir: 0.3, corte: 4000 } }),
    Object.assign({}, DIA, { porte: "arco", titulo: "amanecer", semilla: 265, F0: 30.9, K: 144, rango: [8, 20], span: 11,
      pasos: [6, 8], bpm: 60, seg: 95, lente: "indostani-clara", instrumento: "flauta", pulso: "ninguno", silencio: 0.2,
      bordon: true, tension: "agua", tambor_libre: 1.0,
      aves: { especies: ["colibri", "primavera", "clarin", "cenzontle", "clarin"], alba: true, imitar: 0.6, presentir: 0.5, corte: 4000 } }),
    Object.assign({}, DIA, { porte: "ikebana", titulo: "florecer", semilla: 3, F0: 34.65, K: 180, rango: [8, 20], span: 11,
      pasos: [5, 6], bpm: 64, seg: 95, lente: "jazz-clara", instrumento: "ondas", pulso: "florecer", crecer: true,
      aves: { especies: ["cenzontle"], alba: false, imitar: 0.8, presentir: 0.3, corte: 4000 }, silencio: 0.25, tension: "florecer" }),
    Object.assign({}, DIA, { porte: "corimbo", titulo: "sombrilla-de-sol", semilla: 7, F0: 43.65, K: 140, rango: [7, 20], span: 13,
      pasos: [5, 5], bpm: 92, seg: 85, lente: "hibrida-clara", instrumento: "theremin", pulso: "sol_54", silencio: 0.2,
      tension: "agua", aves: { especies: ["clarin", "colibri"], alba: false, imitar: 0.4, presentir: 0.4, corte: 4000 } }),
  ];
  // los portes que todavía no tienen gemela de día escuchan a su pariente más cercano
  const PORTE_A_CANCION = { espiga: "tizita-mayor", arco: "amanecer", ikebana: "florecer", corimbo: "sombrilla-de-sol",
    candelabro: "tizita-mayor", mata: "florecer", rosal: "sombrilla-de-sol" };

  // ------------------------------------------------------------ armonía (laberintos.py)
  function cancion(genoma) {
    const g = Object.assign({}, genoma);
    const c = { g, F0: g.F0, lo: g.rango[0], hi: g.rango[1], SPAN: g.span, N: g.voces,
      PASO_ARRIBA: g.pasos[0], PASO_ABAJO: g.pasos[1], BPM: g.bpm, BEAT: 60 / g.bpm, tension: tensiones[g.tension] };
    const medio = (c.lo + c.hi) / 2, medioArriba = g.F0 * medio, meta = g.sub_arriba ? 1.5 : 0.75;
    let FU = g.K * g.F0;
    while (FU / medio > meta * medioArriba) FU /= 2;
    while (FU / medio < (meta / 2) * medioArriba) FU *= 2;
    c.FU = FU;
    const mcm = lcm(g.pasos[0], g.pasos[1]);
    c.TIEMPOS = Math.round(g.seg / c.BEAT / mcm) * mcm;
    c.RED = red(c);
    const casa = buscarCasa(c);
    c.CASA = casa[1]; c.CASA_ABAJO = casa[2]; c.rugCasa = casa[0];
    c.CASA_HZ = c.CASA.map((n) => g.F0 * n);
    return c;
  }
  function gcd(a, b) { return b ? gcd(b, a % b) : a; }
  function lcm(a, b) { return (a * b) / gcd(a, b); }
  const clave = (ch) => ch.join(",");

  function valido(c, ch) {
    for (let i = 1; i < ch.length; i++) if (ch[i] - ch[i - 1] < 2) return false;
    return ch[ch.length - 1] - ch[0] <= c.SPAN && ch[0] >= c.lo && ch[0] <= c.hi && ch[ch.length - 1] >= c.lo && ch[ch.length - 1] <= c.hi;
  }
  function vecinos(c, ch) {
    const out = [];
    for (let i = 0; i < ch.length; i++) for (const d of [-2, -1, 1, 2]) {
      const n = ch.slice(); n[i] += d;
      if (valido(c, n)) out.push(n);
    }
    return out;
  }
  function combinaciones(lo, hi, k) {
    const out = [], cur = [];
    (function rec(s) {
      if (cur.length === k) { out.push(cur.slice()); return; }
      for (let x = s; x <= hi; x++) { cur.push(x); rec(x + 1); cur.pop(); }
    })(lo);
    return out;
  }
  function laberinto(c, rng, inicio) {
    const arbol = new Map([[clave(inicio), []]]), ch = new Map([[clave(inicio), inicio]]);
    let frontera = vecinos(c, inicio).map((v) => [inicio, v]);
    while (frontera.length) {
      const [a, b] = frontera.splice(rng.integers(frontera.length), 1)[0];
      const kb = clave(b);
      if (arbol.has(kb)) continue;
      arbol.get(clave(a)).push(b);
      arbol.set(kb, [a]); ch.set(kb, b);
      for (const v of vecinos(c, b)) if (!arbol.has(clave(v))) frontera.push([b, v]);
    }
    return arbol;
  }
  function parcialesDe(f, amp, kmax = 8, decl = 1.3) {
    const out = [];
    for (let k = 1; k <= kmax; k++) if (f * k < 5000) out.push([f * k, amp / Math.pow(k, decl)]);
    return out;
  }
  function rugosidad(p) {             // Sethares (1993)
    let r = 0;
    for (let i = 0; i < p.length; i++) for (let j = i + 1; j < p.length; j++) {
      const fmin = Math.min(p[i][0], p[j][0]), s = 0.24 / (0.021 * fmin + 19), d = Math.abs(p[i][0] - p[j][0]);
      r += p[i][1] * p[j][1] * (Math.exp(-3.5 * s * d) - Math.exp(-5.75 * s * d));
    }
    return r;
  }
  function rugAcordes(c, co, cu) {
    const p = [];
    for (const n of co) p.push(...parcialesDe(c.F0 * n, 1));
    for (const m of cu) p.push(...parcialesDe(c.FU / m, 1));
    return rugosidad(p);
  }
  function gemela(c, f) {             // la subarmónica más cercana que choca: 20–110 cents
    let mejor = null;
    for (let m = 5; m <= 40; m++) {
      let g = c.FU / m;
      while (g < f / 1.5) g *= 2;
      while (g > f * 1.5) g /= 2;
      const ct = Math.abs(1200 * log2(g / f));
      if (ct >= 20 && ct <= 110 && (mejor === null || ct < mejor[1])) mejor = [g, ct];
    }
    return mejor;
  }
  function potencia2(x) { const l = log2(x); return Math.abs(l - Math.round(l)) < 1e-9; }
  function buscarCasa(c) {
    const mejores = [];
    for (const ns of combinaciones(c.lo, c.hi, c.N)) {
      if (!valido(c, ns)) continue;
      const opciones = ns.map((n) => { const o = []; for (let m = c.lo; m <= c.hi; m++) if (potencia2((n * m) / c.g.K)) o.push(m); return o; });
      if (opciones.some((o) => !o.length)) continue;
      (function prod(i, ms) {
        if (i === ns.length) {
          if (new Set(ms).size === ms.length) {
            const mset = ms.slice().sort((a, b) => a - b);
            if (valido(c, mset)) mejores.push([rugAcordes(c, ns, mset), ns, mset]);
          }
          return;
        }
        for (const m of opciones[i]) prod(i + 1, ms.concat([m]));
      })(0, []);
    }
    mejores.sort((a, b) => a[0] - b[0] || cmpArr(a[1], b[1]) || cmpArr(a[2], b[2]));
    return mejores[0];
  }
  function cmpArr(a, b) { for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return a[i] - b[i]; return 0; }
  function estimarRango(c, rng, todos) {
    const r = [];
    for (let i = 0; i < 300; i++) r.push(rugAcordes(c, todos[rng.integers(todos.length)], todos[rng.integers(todos.length)]));
    r.sort((a, b) => a - b);
    const pct = (q) => { const x = (q / 100) * (r.length - 1), i = Math.floor(x); return r[i] + (r[Math.min(r.length - 1, i + 1)] - r[i]) * (x - i); };
    return [pct(5), pct(95)];
  }
  const RESERVA = { arriba: 2, abajo: 1 };
  function caminarJuntos(c, rng, labs, rmin, rmax) {
    const paso = { arriba: c.PASO_ARRIBA, abajo: c.PASO_ABAJO };
    const N = { arriba: Math.floor(c.TIEMPOS / paso.arriba), abajo: Math.floor(c.TIEMPOS / paso.abajo) };
    const casa = { arriba: c.CASA, abajo: c.CASA_ABAJO };
    const W = {};
    for (const k of ["arriba", "abajo"]) W[k] = { camino: [casa[k]], pila: [casa[k]], visto: new Set([clave(casa[k])]), regresando: false, callejones: [], vuelta: null };
    for (let beat = 1; beat < c.TIEMPOS; beat++) for (const k of ["arriba", "abajo"]) {
      if (beat % paso[k]) continue;
      const w = W[k], i = w.camino.length;
      if (i >= N[k]) continue;
      const quedan = N[k] - 1 - i - RESERVA[k], aqui = w.pila[w.pila.length - 1];
      const nuevos = labs[k].get(clave(aqui)).filter((v) => !w.visto.has(clave(v)));
      const puedeIr = w.pila.length <= quedan;
      const otroW = W[k === "arriba" ? "abajo" : "arriba"], otro = otroW.camino[otroW.camino.length - 1];
      let v;
      if (nuevos.length && puedeIr) {
        const meta = rmin + (rmax - rmin) * c.tension(beat / c.TIEMPOS);
        const r = nuevos.map((x) => Math.abs((k === "arriba" ? rugAcordes(c, x, otro) : rugAcordes(c, otro, x)) - meta));
        const orden = r.map((x, j) => j).sort((a, b) => r[a] - r[b]);
        v = nuevos[orden[orden.length === 1 || rng.random() < 0.7 ? 0 : 1]];
        w.visto.add(clave(v)); w.pila.push(v); w.regresando = false;
      } else if (w.pila.length > 1) {
        if (nuevos.length && !puedeIr && w.vuelta === null) w.vuelta = i;
        else if (!nuevos.length && !w.regresando && w.vuelta === null) w.callejones.push(i - 1);
        w.regresando = true; w.pila.pop(); v = w.pila[w.pila.length - 1];
      } else v = aqui;
      w.camino.push(v);
    }
    return W;
  }

  // ------------------------------------------------------------ escalas del choque
  const LENTES = {
    "etiope-clara": { "tizita mayor": [0, 200, 400, 700, 900], "bati mayor": [0, 400, 500, 700, 1100] },
    "jazz-clara": { "lidia": [0, 200, 400, 600, 700, 900, 1100], "lidia dominante": [0, 200, 400, 600, 700, 900, 1000],
      "tonos enteros": [0, 200, 400, 600, 800, 1000] },
    "indostani-clara": { "yaman": [0, 200, 400, 600, 700, 900, 1100], "bilawal": [0, 200, 400, 500, 700, 900, 1100],
      "hamsadhwani": [0, 200, 400, 700, 1100] },
  };
  function red(c) {
    const out = [];
    for (const [fam, gen] of [["O", (k) => c.F0 * k], ["U", (k) => c.FU / k]]) for (let k = 1; k <= 24; k++) {
      let f = gen(k);
      while (f < 300) f *= 2;
      while (f > 1300) f /= 2;
      while (f <= 1300) { out.push([f, fam + k]); f *= 2; }
    }
    return out;
  }
  function poza(c, arriba, abajo) {
    const out = [];
    for (const [fam, notas] of [["O", arriba.map((n) => [c.F0 * n, n])], ["U", abajo.map((m) => [c.FU / m, m])]]) for (let [f, k] of notas) {
      while (f < 300) f *= 2;
      while (f <= 1300) {
        out.push([f, fam + k]);
        const g = gemela(c, f);
        if (g) out.push([g[0], "gemela de " + fam + k]);
        f *= 2;
      }
    }
    return out;
  }
  function afinar(c, tonica, plantilla, pz) {
    const escala = [];
    for (const ct of plantilla) {
      const meta = tonica * Math.pow(2, (ct % 1200) / 1200);
      let mejor = null;
      for (const [fuente, tol, castigo] of [[pz, 70, 0], [c.RED, 45, 40]]) {
        for (const [f, nombre] of fuente) {
          const d = Math.abs(1200 * log2(f / meta));
          if (d <= tol && (mejor === null || d + castigo < mejor[2])) mejor = [f, nombre, d + castigo, 1200 * log2(f / meta)];
        }
        if (mejor) break;
      }
      if (mejor) escala.push({ grado_cents: ct % 1200, hz: mejor[0], fuente: mejor[1], error_cents: Math.round(mejor[3] * 10) / 10 });
    }
    escala.sort((a, b) => a.hz - b.hz);
    const limpia = [];
    for (const e of escala) if (!limpia.length || Math.abs(1200 * log2(e.hz / limpia[limpia.length - 1].hz)) > 15) limpia.push(e);
    return limpia;
  }
  function escogerLente(rng, version) {
    if (version === "hibrida-clara") {
      const [a, b] = rng.choiceN(["etiope-clara", "jazz-clara", "indostani-clara"], 2);
      const pa = rng.choice(Object.keys(LENTES[a])), pb = rng.choice(Object.keys(LENTES[b]));
      const pl = LENTES[a][pa].filter((x) => x % 1200 < 650).concat(LENTES[b][pb].filter((x) => x % 1200 >= 650)).sort((x, y) => x - y);
      return [a + ":" + pa + " abajo + " + b + ":" + pb + " arriba", pl, rng.choice([a, b]).replace("-clara", "")];
    }
    const p = rng.choice(Object.keys(LENTES[version]));
    return [version + ":" + p, LENTES[version][p], version.replace("-clara", "")];
  }

  // ------------------------------------------------------------ el principal hecho pájaro (principal.py)
  function gradoHz(esc, g) { const n = esc.length, o = Math.floor(g / n), i = g - o * n; return esc[i] * Math.pow(2, o); }
  function masCercano(esc, f) {
    let mejor = null, gm = 0;
    for (let o = -2; o <= 2; o++) for (let i = 0; i < esc.length; i++) {
      const d = Math.abs(log2((esc[i] * Math.pow(2, o)) / f));
      if (mejor === null || d < mejor) { mejor = d; gm = i + o * esc.length; }
    }
    return gm;
  }
  class Principal {
    constructor(rng, modo, guarda, vericuetos, crecer) {
      Object.assign(this, { modo, guarda, vericuetos, crecer, historial: [], ultima_funcion: null, herencia: null, ultima_hz: null, apariciones: 0 });
      let ritmo, contorno;
      for (let intento = 0; intento < 50; intento++) {
        const n = rng.integers(3, 5);
        ritmo = []; for (let k = 0; k < n; k++) ritmo.push(k % 2 === 0 ? rng.choice([4, 6, 8]) : rng.choice([2, 3]));
        const pasos = []; for (let k = 0; k < n - 2; k++) pasos.push(rng.choice([1, 2, 2, 3]));
        pasos.push(-rng.choice([1, 2]));
        contorno = [0]; for (const p of pasos) contorno.push(contorno[contorno.length - 1] + p);
        if (Math.max(...contorno) - Math.min(...contorno) >= 3 && contorno[contorno.length - 1] !== 0) break;
      }
      this.canto = { ritmo, contorno };
    }
    contornoVigente() {
      const c = this.canto.contorno.slice();
      if (this.herencia !== null) c[c.length - 1] = c[c.length - 2] + this.herencia;
      return c;
    }
    // guia (sólo en vivo, cuando toca alguien): {centro: Hz, dir: +1 | -1 | 0}. La frase vive en el
    // registro de la mano (abajo = grave) y va hacia donde va la mano (Canek: «no tiene sentido que el
    // lead se vaya a agudos si la mano va abajo»)
    frase(rng, esc, inicioHz, rasgo, progreso, gem, sinCallar, guia) {
      if (!esc.length) return [[], "calla"];
      this.apariciones++;
      let funcion;
      if (this.apariciones === 1) funcion = "expone";
      else {
        const opciones = ["insiste", "interrumpe", "amplia", "calla"], pesos = [0.45, 0.2, 0.15, 0.2];
        if (this.guarda && this.ultima_funcion === "calla") pesos[3] = 0;
        if (sinCallar) pesos[3] = 0;     // en vivo: si alguien toca una flor, el principal no calla
        if (this.vericuetos && this.historial.slice(-2).join() === "insiste,insiste") pesos[0] = 0;
        if (this.modo === "aprende" && rasgo) { opciones.push("contesta"); pesos.push(rasgo.tipo === "final" ? 1.2 : 0.35); }
        funcion = rng.choice(opciones, pesos);
      }
      if (this.modo === "aprende" && this.herencia !== null && rng.random() < 0.15) this.herencia = null;
      this.ultima_funcion = funcion; this.historial.push(funcion);
      if (funcion === "calla") return [[], funcion];
      const ref = inicioHz || this.ultima_hz, g0 = ref ? masCercano(esc, ref) : Math.floor(esc.length / 2);
      let contorno = this.contornoVigente(), ritmo = this.canto.ritmo.slice();
      if (funcion === "contesta" && rasgo) {
        if (rasgo.tipo === "final") {
          contorno[contorno.length - 1] = contorno[contorno.length - 2] + rasgo.paso;
          if (rng.random() < 0.8) { this.herencia = rasgo.paso; funcion = "aprende"; }
        } else if (rasgo.tipo === "intervalo") contorno = contorno.slice(0, -1).concat([contorno[contorno.length - 2] + rasgo.paso]);
      }
      if (funcion === "interrumpe") { contorno = contorno.slice(0, 2); ritmo = ritmo.slice(0, 2); }
      if (this.crecer && progreso > 0.25) for (let k = 0; k < Math.floor((progreso - 0.25) * 6); k++) {
        contorno = contorno.concat([contorno[contorno.length - 1] + [2, 1, 2, -1][k % 4]]);
        ritmo = ritmo.concat([[2, 4][k % 2]]);
      }
      const trucos = []; let desplaza = 0, silencioEn = null, corrida = null, arpa = null;
      if (this.vericuetos && funcion !== "expone" && rng.random() < 0.15 + 0.75 * progreso) {
        const n = 1 + (progreso > 0.5 && rng.random() < 0.5 ? 1 : 0);
        const nombres = ["desplaza", "ensancha", "secuencia", "invierte", "tonos", "silencio", "chafada", "arpa"];
        for (const tr of rng.choiceN(nombres, n, [1, 1, 1, 1, 1, 1, 1, 2.4])) {
          trucos.push(tr);
          if (tr === "desplaza") desplaza = rng.choice([1, 3]);
          else if (tr === "ensancha") contorno = contorno.map((x) => 2 * x);
          else if (tr === "secuencia") {
            const base = contorno.slice(0, 3), rb = ritmo.slice(0, 3), s = rng.choice([1, 2]);
            contorno = base.concat(base.map((x) => x + s), base.map((x) => x + 2 * s));
            const med = rb.map((d) => Math.max(1, Math.floor(d / 2)));
            ritmo = med.concat(med, rb);
          } else if (tr === "invierte") contorno = contorno.map((x) => -x);
          else if (tr === "silencio") silencioEn = 1;
          else if (tr === "arpa") arpa = rng.random() < 0.7 ? 1 : -1;
          else if (tr === "tonos") corrida = rng.random() < 0.6 ? 1 : -1;
        }
      }
      if (guia && guia.dir) {
        const va = Math.sign(contorno[contorno.length - 1] - contorno[0]);
        if (va && va !== guia.dir) contorno = contorno.map((x) => -x);
        if (arpa) arpa = guia.dir;
        if (corrida) corrida = guia.dir;
      }
      let fs = contorno.map((x) => gradoHz(esc, g0 + x));
      if (guia && guia.centro) {
        const gm = Math.exp(fs.reduce((s, f) => s + Math.log(f), 0) / fs.length);
        const k = Math.round(Math.log2(guia.centro / gm));
        fs = fs.map((f) => f * Math.pow(2, k));
        while (Math.max(...fs) > 1500) fs = fs.map((f) => f / 2);
        while (Math.min(...fs) < 160) fs = fs.map((f) => f * 2);
        fs = fs.map((f) => (f > guia.centro * 2.2 && f / 2 >= 160 ? f / 2 : f));   // con la mano abajo, nada se escapa a los agudos
      } else {
        const piso = 250 + (this.crecer ? 300 * progreso : 0);
        while (Math.max(...fs) > 1300) fs = fs.map((f) => f / 2);
        while (Math.min(...fs) < piso && Math.max(...fs) * 2 <= 1300) fs = fs.map((f) => f * 2);
      }
      const notas = []; let t = desplaza;
      const L = Math.min(fs.length, ritmo.length);
      for (let k = 0; k < L; k++) {
        const f = fs[k], d = ritmo[k];
        if (trucos.includes("chafada") && d >= 4 && gem) { const g = gem(f); if (g) notas.push([Math.max(0, t - 0.4), g[0], 0.4, 0.5, "chafada"]); }
        notas.push([t, f, d, k === 0 ? 0.9 : 0.8, k === L - 1 ? "llegada" : null]);
        t += d + (d >= 4 ? 1 : 0) + (silencioEn === k ? 3 : 0);
      }
      if (corrida) {
        let f = notas[notas.length - 1][1];
        for (const r of [9 / 8, 10 / 9, 9 / 8]) { f = corrida > 0 ? f * r : f / r; notas.push([t, f, 1, 0.65, "corrida"]); t += 1; }
      }
      if (arpa) {
        const g = masCercano(esc, notas[notas.length - 1][1]), k = rng.integers(6, 13);
        let fr = []; for (let j = 0; j < k; j++) fr.push(gradoHz(esc, g + arpa * (j + 1)));
        while (Math.max(...fr) > 1600) fr = fr.map((f) => f / 2);
        const pisoArpa = guia && guia.centro ? 160 : 250;          // con la mano abajo, la carrera también se queda abajo
        while (Math.min(...fr) < pisoArpa && Math.max(...fr) * 2 <= 1600) fr = fr.map((f) => f * 2);
        if (guia && guia.centro) while (Math.max(...fr) > guia.centro * 2.2 && Math.min(...fr) / 2 >= 160) fr = fr.map((f) => f / 2);
        fr.forEach((f, j) => { notas.push([t, f, 0.5, 0.6 + (0.25 * j) / k, "arpa"]); t += 0.5; });
      }
      if (funcion === "amplia") notas.push([t + 2, notas[notas.length - 1][1], 4, 0.55, "eco"]);
      this.ultima_hz = notas[notas.length - 1][1];
      if (trucos.length) funcion += "+" + trucos.join("+");
      return [notas, funcion];
    }
  }
  function regaloDelCenzontle(rng, cantoHz, esc) {
    if (cantoHz.length < 2 || !esc.length) return [null, null];
    const paso = rng.choice([-3, -2, 2, 3, 4]), g = masCercano(esc, cantoHz[1]);
    return [[cantoHz[0], cantoHz[1], gradoHz(esc, g + paso)], { tipo: "final", paso }];
  }

  // ------------------------------------------------------------ agua (agua.py)
  function salpicar(rng, escala, fuentes, t0, nr, octavas) {
    if (!escala.length) return [];
    const n = rng.integers(nr[0], nr[1]), gotas = [];
    let t = t0, dt = rng.uniform(0.03, 0.06);
    for (let k = 0; k < n; k++) {
      const i = rng.integers(escala.length);
      let f = escala[i] * Math.pow(2, rng.choice(octavas));
      if (rng.random() < 0.25) f = escala[i] * rng.choice([3, 5, 7]);
      while (f > 5000) f /= 2;
      const tam = rng.uniform(0, 1);
      gotas.push({ tipo: "gota", t, f, fuente: fuentes[i], tau: 0.012 + 0.05 * tam, chirp: rng.uniform(0.15, 0.6),
        amp: rng.uniform(0.45, 1.0) * (1 - (0.5 * k) / n), pan: rng.uniform(-1, 1), anillos: rng.integers(1, 4), eco: rng.uniform(0, 0.03) });
      t += dt; dt *= rng.uniform(1.1, 1.45);
    }
    return gotas;
  }
  function aguaArpa(rng, escala, fuentes, t0, sube, octavas = [1, 2]) {
    if (!escala.length) return [];
    const pares = escala.map((f, i) => [f, fuentes[i]]).sort((a, b) => a[0] - b[0]);
    let notas = [];
    for (const o of octavas) for (const [f, fu] of pares) notas.push([f * Math.pow(2, o), fu]);
    notas = notas.filter((x) => x[0] <= 4500);
    const k = rng.integers(8, 15);
    if (notas.length > k) { const i0 = rng.integers(0, notas.length - k + 1); notas = notas.slice(i0, i0 + k); }
    if (!sube) notas.reverse();
    const dt = rng.uniform(0.045, 0.07);
    return notas.map(([f, fu], j) => {
      const x = j / Math.max(1, notas.length - 1);
      return { tipo: "gota", t: t0 + j * dt * (1 + 0.08 * rng.normal()), f, fuente: fu, tau: rng.uniform(0.03, 0.05), chirp: 0.25,
        amp: 0.5 + 0.4 * Math.sin(Math.PI * x), pan: (2 * x - 1) * (sube ? 0.8 : -0.8), anillos: 1, eco: 0.015 };
    });
  }

  // ------------------------------------------------------------ aves (aves.py), como trazos que voces.js dibuja
  const ESPECIES = {
    clarin: { reg: [900, 2600], gestos: { silbido: 0.7, llamado: 0.2, trino: 0.1 }, largo: [2, 4], pausa: 5.0, repite: 1, dur: 1.6, vol: 1.0 },
    cenzontle: { reg: [1000, 3000], gestos: { silbido: 0.3, trino: 0.25, gorjeo: 0.25, llamado: 0.2 }, largo: [2, 3], pausa: 4.0, repite: 3, dur: 1.0, vol: 0.9 },
    primavera: { reg: [1200, 3000], gestos: { llamado: 0.5, silbido: 0.3, gorjeo: 0.2 }, largo: [3, 5], pausa: 6.0, repite: 1, dur: 0.8, vol: 0.85 },
    colibri: { reg: [1800, 3400], gestos: { gorjeo: 0.6, trino: 0.4 }, largo: [1, 3], pausa: 7.0, repite: 1, dur: 0.6, vol: 0.5 },
  };
  function registro(f, lo, hi) { while (f < lo) f *= 2; while (f > hi) f /= 2; return f; }
  class Ave {
    constructor(rng, especie, nombre) {
      Object.assign(this, { especie, nombre, e: ESPECIES[especie] });
      this.pan = rng.uniform(-0.95, 0.95);
      const tipos = Object.keys(this.e.gestos), pesos = tipos.map((t) => this.e.gestos[t]);
      this.motivo = [];
      const n = rng.integers(this.e.largo[0], this.e.largo[1] + 1);
      for (let k = 0; k < n; k++) this.motivo.push({ tipo: rng.choice(tipos, pesos), ga: rng.integers(0, 6), gb: rng.integers(0, 6),
        d: rng.uniform(0.6, 1.4) * 0.3 * this.e.dur, pausa: rng.uniform(0.05, 0.25) });
    }
    notas(escala) {
      const s = [...new Set(escala.map((f) => Math.round(registro(f, ...this.e.reg) * 1000) / 1000))].sort((a, b) => a - b);
      return s.length ? s : [this.e.reg[0]];
    }
    cantar(rng, escala) {            // → {trazos, dur, usadas}
      const ns = this.notas(escala), trazos = [], usadas = [];
      let t = 0;
      for (const g of this.motivo) {
        if (rng.random() < 0.15) continue;
        const salto = rng.random() < 0.2 ? rng.integers(-1, 2) : 0;
        const a = ns[pmod(g.ga + salto, ns.length)], b = ns[pmod(g.gb, ns.length)];
        const veces = this.e.repite > 1 ? rng.integers(2, this.e.repite + 1) : 1;
        usadas.push(a, b);
        for (let v = 0; v < veces; v++) {
          if (g.tipo === "silbido") { trazos.push({ tipo: "silbido", t, d: g.d, a, b: b !== a ? b : ns[(g.gb + 1) % ns.length], curva: rng.uniform(0.6, 1.6) }); t += g.d; }
          else if (g.tipo === "trino") { trazos.push({ tipo: "trino", t, d: g.d, a, b: ns[(ns.indexOf(a) + 1) % ns.length], vel: rng.uniform(12, 22) }); t += g.d; }
          else if (g.tipo === "gorjeo") {
            const k = rng.integers(3, 7);
            for (let j = 0; j < k; j++) { const d = rng.uniform(0.03, 0.07); trazos.push({ tipo: "pio", t, d, a: ns[(g.ga + j) % ns.length] }); t += d + rng.uniform(0.02, 0.06); }
          } else { trazos.push({ tipo: "llama1", t, d: 0.12, a }); trazos.push({ tipo: "llama2", t: t + 0.17, d: 0.28, a: b }); t += 0.45; }
          t += g.pausa;
        }
      }
      return { trazos, dur: Math.max(0.05, t), usadas };
    }
    imitar(rng, notasHz) {
      const ns = notasHz.map((f) => registro(f, ...this.e.reg)).slice(0, 6), trazos = [];
      if (ns.length < 2) return { trazos, dur: 0.05, usadas: [] };
      let t = 0;
      for (let i = 0; i + 1 < ns.length; i++) { const d = rng.uniform(0.09, 0.18); trazos.push({ tipo: "silbido", t, d, a: ns[i], b: ns[i + 1], curva: rng.uniform(0.5, 1.5) }); t += d + 0.03; }
      return { trazos, dur: t, usadas: ns };
    }
  }

  // ------------------------------------------------------------ tambor parlante (parlante.py)
  function regTambor(f) { while (f > 330) f /= 2; while (f < 110) f *= 2; return f; }
  function fraseParlante(rng, escala, t0, unidad) {
    if (!escala.length) return [];
    const alturas = escala.map(regTambor).sort((a, b) => a - b), k = rng.integers(2, 7), out = [];
    let t = t0, prev = alturas[rng.integers(alturas.length)], i = rng.integers(alturas.length);
    for (let j = 0; j < k; j++) {
      i = clip(i + rng.choice([-2, -1, 1, 1, 2]), 0, alturas.length - 1);
      const meta = alturas[i], apagado = rng.random() < 0.25, vel = 0.7 + 0.3 * rng.random() - (apagado ? 0.15 : 0);
      out.push({ tipo: "golpe", t, desde: prev, hasta: meta, vel, glide: rng.uniform(0.03, 0.12), largo: 0.45, apagado });
      prev = meta; t += rng.choice([0.5, 1, 1, 1.5, 2]) * unidad;
    }
    return out;
  }
  function fraseLibre(rng, alturasHz, t0, desde, unidad) {
    if (!alturasHz.length) return [[], desde];
    const alturas = [...new Set(alturasHz.map((f) => Math.round(regTambor(f) * 1000) / 1000))].sort((a, b) => a - b);
    const k = rng.integers(3, 10), out = [];
    let t = t0, prev = desde || alturas[rng.integers(alturas.length)];
    let i = 0; alturas.forEach((a, j) => { if (Math.abs(log2(a / prev)) < Math.abs(log2(alturas[i] / prev))) i = j; });
    const arco = rng.choice(["crece", "decrece", "monte"]);
    for (let j = 0; j < k; j++) {
      const x = j / Math.max(1, k - 1);
      const dinam = { crece: 0.55 + 0.45 * x, decrece: 1 - 0.45 * x, monte: 0.55 + 0.45 * Math.sin(Math.PI * x) }[arco];
      if (rng.random() > 0.3) i = clip(i + rng.choice([-2, -1, -1, 1, 1, 2]), 0, alturas.length - 1);
      const meta = alturas[i], apagado = rng.random() < 0.3, vel = dinam * (0.85 + 0.15 * rng.random()) - (apagado ? 0.12 : 0);
      if (rng.random() < 0.12) out.push({ tipo: "golpe", t: t - 0.025, desde: prev, hasta: prev, vel: vel * 0.45, glide: 0.02, largo: 0.15, apagado: true });
      out.push({ tipo: "golpe", t, desde: prev, hasta: meta, vel, glide: rng.uniform(0.03, 0.15), largo: 0.45, apagado });
      prev = meta; t += rng.choice([0.5, 1, 1, 1.5, 2, 3]) * unidad * (1 + rng.normal(0, 0.12));
    }
    return [out, prev];
  }

  // ------------------------------------------------------------ pulsos (serie.py), un compás a la vez
  const PULSOS = {
    ninguno: { tiempos: 4, compas() { return []; } },
    agua_68: { tiempos: 4, compas(j, t, B, rng, tambor) {   // 6/8 que flota
      const tres = B / 3, ev = [{ tipo: "bombo", t, vel: 0.4 }, tambor(t + 2 * B + 2 * tres, 0.45), tambor(t + 3 * B + tres, 0.3)];
      for (let k = 0; k < 12; k++) if (k % 3 === 0 || rng.random() < 0.35) ev.push({ tipo: "hat", t: t + k * tres + rng.normal(0, 0.003), vel: k % 6 === 0 ? 0.3 : 0.15 });
      return ev;
    } },
    sol_54: { tiempos: 5, compas(j, t, B, rng, tambor) {     // 5/4 sin bombo
      const ev = [tambor(t, 0.45), tambor(t + 3 * B, 0.4)];
      for (let k = 0; k < 10; k++) if (rng.random() < 0.6) ev.push({ tipo: "hat", t: t + (k * B) / 2 + rng.normal(0, 0.003), vel: 0.18 });
      return ev;
    } },
    florecer: { tiempos: 8, compas(j, t, B, rng, tambor) {   // casi nada
      return rng.random() < 0.7 ? [tambor(t + rng.choice([0, 1.5, 2.5]) * B, 0.35)] : [];
    } },
  };

  // ------------------------------------------------------------ el jardín: conductor en tiempo de canción
  class Jardin {
    constructor(genoma, opciones = {}) {
      this.c = cancion(genoma);
      const s = opciones.semilla ?? genoma.semilla;
      this.semilla = s;
      const g = this.c.g;
      this.r = { visita: azar(s + 1000), inst: azar(s + 2000), agua: azar(s + 4000), parl: azar(s + 5000), libre: azar(s + 7000),
        aves: azar(s + 8000), prin: azar(s + 9000), pulso: azar(s + 3500) };
      this.prin = new Principal(azar(s + 9100), g.principal, g.principal_guarda, g.vericuetos, g.crecer);
      this.aves = g.aves.especies.map((e, i) => new Ave(this.r.aves, e, e + "-" + i));
      this.imitadores = this.aves.filter((a) => a.especie === "cenzontle");
      if (!this.imitadores.length) this.imitadores = this.aves.slice(0, 1);
      this.ciclos = [];             // ciclos del muro ya caminados
      this.visitas = [];            // registro de lo que pasó
      this.ocupado = [];            // tramos [a, b] en que suena la línea del principal
      this.lente = null;
      this.aguaUltimo = null; this.rasgo = null;
      this.regalos = [];
      this.ultimoToque = -1e9;
      this.nVisitas = 0;
      this.memoriaFlor = new Map();   // flor → lo que cantó la última vez que alguien la tocó
      this.libre = { t: this.r.libre.uniform(1, 4), prev: null };
      this.avesT = this.aves.map((a, i) => (g.aves.alba ? (this.duracionCiclo() * 0.65 * i) / this.aves.length + this.r.aves.uniform(0, 3) : this.r.aves.uniform(1, 8)));
      this.pulsoJ = 0;
      this.eventos = [];            // cola que el sonido va consumiendo
    }
    duracionCiclo() { return this.c.TIEMPOS * this.c.BEAT; }
    ciclo(k) {                    // el muro del ciclo k: sale de casa y regresa
      while (this.ciclos.length <= k) {
        const j = this.ciclos.length, c = this.c, rng = azar(this.semilla + 101 * j);
        const todos = combinaciones(c.lo, c.hi, c.N).filter((x) => valido(c, x));
        const lab = { arriba: laberinto(c, rng, c.CASA), abajo: laberinto(c, rng, c.CASA_ABAJO) };
        const [rmin, rmax] = estimarRango(c, rng, todos);
        const W = caminarJuntos(c, rng, lab, rmin, rmax);
        this.ciclos.push({ k: j, t0: j * this.duracionCiclo(), arriba: W.arriba.camino, abajo: W.abajo.camino,
          callejones: W.arriba.callejones, vuelta: [W.arriba.vuelta, W.abajo.vuelta], rmin, rmax, rng });
      }
      return this.ciclos[k];
    }
    acordeEn(t) {
      const c = this.c, k = Math.max(0, Math.floor(t / this.duracionCiclo())), C = this.ciclo(k), u = t - C.t0;
      const co = C.arriba[Math.min(C.arriba.length - 1, Math.floor(u / (c.PASO_ARRIBA * c.BEAT)))];
      const cu = C.abajo[Math.min(C.abajo.length - 1, Math.floor(u / (c.PASO_ABAJO * c.BEAT)))];
      return { co, cu, ciclo: k, progreso: u / this.duracionCiclo() };
    }
    // el muro de un ciclo como tramos sostenidos (una voz se mueve por paso)
    muro(k) {
      const c = this.c, C = this.ciclo(k), g = c.g, ev = [];
      const segmentos = (camino, pasoT) => {
        const out = [];
        for (let v = 0; v < camino[0].length; v++) {
          let t0 = 0, val = camino[0][v];
          for (let i = 1; i < camino.length; i++) if (camino[i][v] !== val) { out.push([v, val, t0 * pasoT * c.BEAT, (i - t0) * pasoT * c.BEAT, t0 > 0]); t0 = i; val = camino[i][v]; }
          out.push([v, val, t0 * pasoT * c.BEAT, (camino.length - t0) * pasoT * c.BEAT, t0 > 0]);
        }
        return out;
      };
      for (const [v, n, t, d, movida] of segmentos(C.arriba, c.PASO_ARRIBA)) {
        ev.push({ tipo: "muro", fam: "arriba", t: C.t0 + t, d, f: c.F0 * n, ataque: movida ? 0.12 : 1.2, brillo: g.brillo[0], n });
        if (g.bajo_de === "arriba" && v === 0) { let fb = (c.F0 * n) / 2; while (fb > 120) fb /= 2; ev.push({ tipo: "bajo", t: C.t0 + t, d: Math.min(d, 4 * c.BEAT), f: fb }); }
      }
      for (const [v, m, t, d] of segmentos(C.abajo, c.PASO_ABAJO)) ev.push({ tipo: "pad", fam: "abajo", t: C.t0 + t, d, f: c.FU / m, brillo: g.brillo[1], m });
      if (g.bordon) {
        let raiz = Math.min(...c.CASA.map((n) => c.F0 * n)); while (raiz > 140) raiz /= 2;
        for (const [f, a] of [[raiz, 0.5], [raiz * 1.5, 0.3], [raiz * 2, 0.25]]) ev.push({ tipo: "muro", fam: "abajo", t: C.t0, d: this.duracionCiclo() + 1.5, f, ataque: 2.5, brillo: 1500, vel: a, bordon: true });
      }
      return ev;
    }
    // los pasos del caminante de arriba: donde el jardín visita una flor si nadie toca
    pasos(k) {
      const c = this.c, C = this.ciclo(k), out = [];
      for (let i = 1; i < C.arriba.length; i++) {
        const antes = C.arriba[i - 1], ahora = C.arriba[i];
        if (clave(antes) === clave(ahora)) continue;
        const v = ahora.findIndex((x, j) => x !== antes[j]);
        out.push({ t: C.t0 + i * c.PASO_ARRIBA * c.BEAT, n: ahora[v], ahora, callejon: C.callejones.includes(i - 1) });
      }
      return out;
    }
    principalOcupado(t) { return this.ocupado.some(([a, b]) => t >= a - 0.15 && t <= b + 0.25); }
    // ¿suena (o está por sonar) una frase que empezó alguien con la mano?
    tocadoPorAlguien(t) { return this.ocupado.some(([a, b, q]) => q === "toque" && t >= a - 0.15 && t <= b + 0.25); }
    // el jardín cede la voz: olvida sus visitas que todavía no empiezan; devuelve sus vid
    cederVoz(t) {
      const fuera = new Set(this.ocupado.filter(([a, , q]) => q !== "toque" && a > t).map((x) => x[3]));
      this.ocupado = this.ocupado.filter((x) => !fuera.has(x[3]));
      this.visitas = this.visitas.filter((v) => !fuera.has(v.vid));
      return fuera;
    }
    lineaSuenaHasta() { return this.ocupado.reduce((m, x) => Math.max(m, x[1]), -1); }
    // ----- una visita a una flor (laberintos.tema, el cuerpo de cada visita)
    visita(tPaso, opciones = {}) {
      const c = this.c, g = c.g, rc = this.r.visita, rpr = this.r.prin, ra = this.r.agua, paso16 = c.BEAT / 4;
      const { co, cu, progreso } = this.acordeEn(tPaso);
      if (!this.lente || rc.random() < 0.3) this.lente = escogerLente(rc, g.lente);
      const [nombre, plantilla] = this.lente;
      let ton;
      if (opciones.n) ton = c.F0 * opciones.n;                      // la flor tocada pone la tónica
      else if (this.sostenido) ton = c.F0 * this.sostenido.n;       // calderón: el jardín canta alrededor de la nota sostenida
      else {
        const comun = []; for (const n of co) for (const m of cu) if (Math.abs(c.F0 * n - c.FU / m) < 1e-6) comun.push(c.F0 * n);
        ton = comun.length ? comun[0] : c.F0 * (opciones.nPaso || co[0]);
      }
      while (ton < 300) ton *= 2;
      while (ton > 600) ton /= 2;
      const escala = afinar(c, ton, plantilla, poza(c, co, cu)), ehz = escala.map((e) => e.hz), efu = escala.map((e) => e.fuente);
      const ks = rc.choiceN([2, 3, 4, 5, 6], rc.choice([1, 2])).sort((a, b) => a - b);
      const batido = rc.uniform(...g.batido), signo = rc.choice([-1, 1]);
      const off = opciones.inmediato ? 0 : rc.choice([0, 1, 2, 3, 5, 6]);
      const gem = (f) => gemela(c, f);
      const guia = opciones.quien === "toque" && opciones.y != null ? { centro: 1100 * Math.pow(250 / 1100, clip(opciones.y, 0, 1)), dir: opciones.dir || 0 } : null;
      // si vuelves a una flor que sigue viva, recuerda lo que cantó y lo repite un poco raro (Canek:
      // «si vuelves a ella, tendría que tocar lo que acaba de tocar pero poquito raro»); más raro cada vuelta
      const mem = opciones.quien === "toque" && opciones.flor != null ? this.memoriaFlor.get(opciones.flor) : null;
      const [notas0, funcion] = mem && tPaso - mem.t < 60
        ? this.recordar(mem, rpr, ehz, gem, guia)
        : this.prin.frase(rpr, ehz, g.principal === "aprende" ? this.aguaUltimo : null, this.rasgo, progreso, gem, opciones.quien === "toque", guia);
      if (opciones.quien === "toque" && opciones.flor != null && notas0.length)
        this.memoriaFlor.set(opciones.flor, { t: tPaso, notas: notas0.map((x) => x.slice()), veces: mem && tPaso - mem.t < 60 ? mem.veces + 1 : 0, base: mem && tPaso - mem.t < 60 ? mem.base : notas0.map((x) => x.slice()) });
      const notas = notas0.map(([p, f, d, vel, a]) => [p, f, d, vel, a === "eco" ? "repetida" : a]);
      if (!(g.principal_guarda && funcion.split("+")[0] === "calla")) { this.aguaUltimo = null; this.rasgo = null; }
      const vid = ++this.nVisitas, quien = opciones.quien || "jardin";
      const ev = [{ tipo: "flor", t: tPaso, flor: opciones.flor, n: opciones.n || null, funcion, lente: nombre, ton }];
      const linea = [];
      for (const [p, f, d, vel, adorno] of notas) {
        const tt = tPaso + (off + p) * paso16 + rpr.normal(0, 0.004);
        linea.push({ t: tt, f, d: d * paso16, vel, adorno });
        if (adorno === "meend" || adorno === "aproximación") continue;
        for (const k of ks) ev.push({ tipo: "sombra", t: tt, d: d * paso16 + 0.5, f: f / k + (signo * batido) / k, vel: (0.8 * vel) / Math.pow(k, 0.3), k });
      }
      const fin = notas.length ? tPaso + (off + Math.max(...notas.map((n) => n[0] + n[2]))) * paso16 : tPaso + off * paso16;
      if (linea.length) {
        ev.push({ tipo: "linea", inst: g.instrumento, t: linea[0].t, notas: linea, casa: c.CASA_HZ, flor: opciones.flor });
        this.ocupado.push([linea[0].t, fin, quien, vid]);
        if (this.ocupado.length > 64) this.ocupado.shift();
      }
      // el agua
      if (g.agua) {
        const hizoArpa = notas.some((n) => n[4] === "arpa");
        let gotas;
        if (g.agua_arpa && (hizoArpa || ra.random() < 0.1 + 0.3 * progreso)) {
          const sube = !(hizoArpa && notas[notas.length - 1][1] > notas[0][1]);
          gotas = aguaArpa(ra, ehz, efu, hizoArpa ? fin + 0.25 : tPaso + off * paso16, sube);
        } else gotas = salpicar(ra, ehz, efu, tPaso + off * paso16, g.gotas.n, g.gotas.octavas);
        ev.push(...gotas);
      }
      // el tambor contesta al terminar la frase (casi siempre)
      if (g.parlante && notas.length && this.r.parl.random() < 0.75) ev.push(...fraseParlante(this.r.parl, ehz, fin + paso16, paso16 * 2));
      // el agua guarda la huella y la devuelve cantabile
      let devuelve = null;
      if (g.agua_canta && notas.length >= 2) {
        const dos = notas.slice().sort((a, b) => b[2] - a[2]).slice(0, 2).sort((a, b) => a[0] - b[0]);
        const sep = (dos[1][0] - dos[0][0]) * paso16, td = fin + rpr.uniform(1.0, 2.5);
        devuelve = { tipo: "aguaCanto", t: td, a: dos[0][1], b: dos[1][1], sep, pan: rpr.uniform(-0.6, 0.6), vel: 0.8, gotitas: [] };
        const nG = rpr.integers(2, 4);
        for (let k = 0; k < nG; k++) devuelve.gotitas.push({ f: dos[1][1] * rpr.choice([2, 3]), tau: rpr.uniform(0.01, 0.025), chirp: rpr.uniform(0.2, 0.5), amp: rpr.uniform(0.15, 0.3), dt: rpr.uniform(0.1, 0.8) });
        ev.push(devuelve);
        if (g.principal === "aprende") {
          this.aguaUltimo = dos[1][1];
          if (!this.rasgo) this.rasgo = { tipo: "intervalo", paso: masCercano(ehz, dos[1][1]) - masCercano(ehz, dos[0][1]) };
        }
      }
      // el cenzontle regala un final
      let regalo = null;
      if (g.principal === "aprende" && notas.length && rpr.random() < 0.45) {
        const [nh, rasgo] = regaloDelCenzontle(rpr, notas.map((n) => n[1]), ehz);
        if (nh) { regalo = { t: fin + rpr.uniform(0.5, 1.2), notas: nh, paso: rasgo.paso }; this.regalos.push(regalo); this.rasgo = rasgo; }
      }
      const v = { vid, t: tPaso, t_fin: fin, flor: opciones.flor, quien, funcion, lente: nombre, ton, escala: ehz,
        notas: linea.map((x) => x.f), regalo, devuelve: !!devuelve };
      this.visitas.push(v);
      if (this.visitas.length > 200) this.visitas.shift();
      // aves que reaccionan a esta visita
      const rav = this.r.aves, perfil = g.aves;
      if (linea.length && opciones.presentir && rav.random() < perfil.presentir) {
        const ave = this.aves[rav.integers(this.aves.length)], ns = ave.notas(ehz), d = rav.uniform(0.25, 0.5);
        ev.push(...this.ponerAve(tPaso - rav.uniform(0.8, 2.0), { trazos: [{ tipo: "silbido", t: 0, d, a: ns[0], b: ns[ns.length - 1], curva: 1 }], dur: d, usadas: [ns[0], ns[ns.length - 1]] }, ave, "presiente"));
      }
      if (linea.length && rav.random() < perfil.imitar) {
        const ave = this.imitadores[rav.integers(this.imitadores.length)];
        ev.push(...this.ponerAve(fin + rav.uniform(0.3, 1.2), ave.imitar(rav, linea.map((x) => x.f)), ave, "imita"));
      }
      if (regalo) ev.push(...this.ponerAve(regalo.t, this.imitadores[0].imitar(rav, regalo.notas), this.imitadores[0], "regala"));
      for (const e of ev) e.vid = vid;
      return ev;
    }
    // moverte entre flores mientras el principal canta: escala de la flor en gotas, con sombras que vibran
    arrastre(t, n, opciones = {}) {
      const c = this.c, g = c.g, rc = this.r.visita, ra = this.r.agua;
      const { co, cu } = this.acordeEn(t);
      if (!this.lente) this.lente = escogerLente(rc, g.lente);
      let ton = c.F0 * n; while (ton < 300) ton *= 2; while (ton > 600) ton /= 2;
      const escala = afinar(c, ton, this.lente[1], poza(c, co, cu)), ehz = escala.map((e) => e.hz);
      const fatiga = opciones.fatiga ?? 1;
      const octs = opciones.y == null ? [1, 2] : opciones.y > 0.66 ? [0, 1] : opciones.y > 0.33 ? [1] : [1, 2];   // abajo, gotas más graves
      const gotas = aguaArpa(ra, ehz, escala.map((e) => e.fuente), t, opciones.sube !== false, octs).slice(0, 6 + ra.integers(0, 4));
      gotas.forEach((x) => (x.amp *= 0.8 * fatiga));
      const f = ehz[masCercano(ehz, ton) % ehz.length] || ton;
      const ev = [{ tipo: "flor", t, flor: opciones.flor, n, funcion: "arrastre", ton }, ...gotas];
      const ks = rc.choiceN([2, 3, 4, 5, 6], 2).sort((a, b) => a - b), batido = rc.uniform(...g.batido), signo = rc.choice([-1, 1]);
      for (const k of ks) ev.push({ tipo: "sombra", t, d: 1.6, f: f / k + (signo * batido) / k, vel: (0.55 * fatiga) / Math.pow(k, 0.3), k });
      return ev;
    }
    // barrer (07-PLANTA-HUMANO-MUSICA.md): las flores que cruzó la palma, en un solo glissando
    // de agua, en el orden del gesto y a su velocidad; después limpia sombras y resonancia
    barrido(t, ns, opciones = {}) {
      const c = this.c, ra = this.r.agua, { co, cu } = this.acordeEn(t);
      if (!this.lente) this.lente = escogerLente(this.r.visita, c.g.lente);
      const dur = clip(opciones.dur ?? 0.5, 0.2, 1.2), fatiga = opciones.fatiga ?? 1, ev = [];
      // un glissando de arpa por la escala de la primera flor: a la derecha sube, a la izquierda baja;
      // cada flor cruzada es un acento (las de una misma fila tienen el mismo armónico)
      let ton = c.F0 * ns[0]; while (ton < 300) ton *= 2; while (ton > 600) ton /= 2;
      const esc = afinar(c, ton, this.lente[1], poza(c, co, cu)).map((e) => e.hz);
      const sube = opciones.sube !== false, k = clip(2 * ns.length + 2, 6, 14);
      let f0 = ton; while (f0 < (sube ? 700 : 1400)) f0 *= 2;
      const g0 = masCercano(esc, f0), notas = [];
      for (let j = 0; j < k; j++) { let x = gradoHz(esc, g0 + (sube ? j : -j)); while (x > 4000) x /= 2; while (x < 500) x *= 2; notas.push(x); }
      const acentos = new Set(ns.map((_, i) => Math.round((i / Math.max(1, ns.length - 1)) * (k - 1))));
      const dt = dur / Math.max(1, k - 1);
      notas.forEach((f, j) => {
        const x = j / Math.max(1, k - 1);
        ev.push({ tipo: "gota", t: t + j * dt * (1 + 0.06 * ra.normal()), f, tau: ra.uniform(0.025, 0.045) * (acentos.has(j) ? 1.6 : 1), chirp: 0.22,
          amp: (0.35 + 0.3 * Math.sin(Math.PI * x) + (acentos.has(j) ? 0.3 : 0)) * fatiga,
          pan: clip((opciones.pan0 ?? -0.7) + x * ((opciones.pan1 ?? 0.7) - (opciones.pan0 ?? -0.7)), -1, 1), anillos: acentos.has(j) ? 2 : 1, eco: 0.012 });
      });
      ns.forEach((n, i) => ev.push({ tipo: "flor", t: t + (i / Math.max(1, ns.length - 1)) * dur, flor: (opciones.flores || [])[i], n, funcion: "barrido", ton: c.F0 * n }));
      ev.push({ tipo: "limpia", t: t + dur + 0.05, seg: 0.5 });
      this.ultimoToque = t + dur + 3 - 7;          // el jardín calla 3 s (CALLA_TRAS_TOQUE es 7)
      return ev;
    }
    // la flor recuerda: su frase original (base) con 1, 2 o 3 vericuetos, según cuántas veces volviste
    recordar(mem, rng, esc, gem, guia) {
      let notas = mem.base.filter((x) => x[4] !== "arpa" && x[4] !== "corrida" && x[4] !== "eco").map((x) => x.slice());
      if (!notas.length) notas = mem.base.map((x) => x.slice());
      const n = Math.min(3, mem.veces + 1), trucos = rng.choiceN(["desplaza", "octava", "chafada", "final", "estira", "tonos"], n);
      // el registro se decide con la frase original, antes de torcerla (si no, una nota a la octava sube toda la frase)
      const kReg = guia && guia.centro ? Math.round(Math.log2(guia.centro / Math.exp(notas.reduce((s, x) => s + Math.log(x[1]), 0) / notas.length))) : 0;
      for (const tr of trucos) {
        if (tr === "desplaza") { const d = rng.choice([1, 3]); notas.forEach((x) => (x[0] += d)); }
        else if (tr === "octava" && notas.length > 2) { const i = 1 + rng.integers(notas.length - 2); notas[i][1] *= rng.random() < 0.5 ? 2 : 0.5; }
        else if (tr === "chafada") { const i = notas.reduce((b, x, j) => (x[2] > notas[b][2] ? j : b), 0), g = gem(notas[i][1]); if (g) notas.splice(i, 0, [Math.max(0, notas[i][0] - 0.4), g[0], 0.4, 0.5, "chafada"]); }
        else if (tr === "final" && notas.length > 1 && esc.length) {      // la llegada se refleja alrededor de la nota anterior
          const a = notas[notas.length - 2], b = notas[notas.length - 1], ga = masCercano(esc, a[1]), gb = masCercano(esc, b[1]);
          b[1] = gradoHz(esc, ga - (gb - ga || 1));
        }
        else if (tr === "estira") { const u = notas[notas.length - 1]; u[2] = Math.round(u[2] * 1.75); }
        else if (tr === "tonos") { let f = notas[notas.length - 1][1], t = Math.max(...notas.map((x) => x[0] + x[2])); const s = guia && guia.dir ? guia.dir : 1; for (const r of [9 / 8, 9 / 8]) { f = s > 0 ? f * r : f / r; notas.push([t, f, 1, 0.6, "corrida"]); t += 1; } }
      }
      notas.sort((a, b) => a[0] - b[0]);
      if (guia && guia.centro) {                    // en el registro de la mano de ahora
        notas.forEach((x) => (x[1] *= Math.pow(2, kReg)));
        while (Math.max(...notas.map((x) => x[1])) > 1500) notas.forEach((x) => (x[1] /= 2));
        while (Math.min(...notas.map((x) => x[1])) < 160) notas.forEach((x) => (x[1] *= 2));
      }
      this.prin.ultima_hz = notas[notas.length - 1][1];
      return [notas, "recuerda+" + trucos.join("+")];
    }
    // calderón (07-PLANTA-HUMANO-MUSICA.md): la mano quieta sobre una flor deja su nota en el muro,
    // con dos sombras que vibran contra ella, mientras la mano siga ahí
    calderon(t, n, opciones = {}) {
      const c = this.c, rc = this.r.visita;
      let f = c.F0 * n; while (f < 150) f *= 2; while (f > 500) f /= 2;
      const ks = rc.choiceN([2, 3, 4], 2).sort((a, b) => a - b), batido = rc.uniform(...c.g.batido), signo = rc.choice([-1, 1]);
      const id = "cal-" + (++this.nVisitas);
      this.sostenido = { n, t, id };
      return [{ tipo: "flor", t, flor: opciones.flor, n, funcion: "calderón", ton: f, id },
        { tipo: "calderon", t, id, f, sombras: ks.map((k) => ({ f: f / k + (signo * batido) / k, k })), brillo: c.g.brillo[0] }];
    }
    soltarCalderon(id) { if (this.sostenido && this.sostenido.id === id) this.sostenido = null; }
    // rozar con la cara: sólo las sombras subarmónicas de la flor, bajito, vibrando contra su nota
    roce(t, n, opciones = {}) {
      const c = this.c, rc = this.r.visita;
      let f = c.F0 * n; while (f < 250) f *= 2; while (f > 700) f /= 2;
      const ks = rc.choiceN([2, 3, 4, 5], 2).sort((a, b) => a - b), batido = rc.uniform(...c.g.batido), signo = rc.choice([-1, 1]);
      const ev = [{ tipo: "flor", t, flor: opciones.flor, n, funcion: "roce", ton: f }];
      for (const k of ks) ev.push({ tipo: "sombra", t, d: 1.2, f: f / k + (signo * batido) / k, vel: (0.35 * (opciones.fatiga ?? 1)) / Math.pow(k, 0.3), k });
      return ev;
    }
    // ----- aves con canto propio: nicho acústico (callan en la línea), resonancia del muro
    ponerAve(t, canto, ave, que) {
      let ok = false;
      for (let i = 0; i < 40; i++) {
        let libre = true;
        for (let k = 0; k <= Math.floor(canto.dur / 0.1); k++) if (this.principalOcupado(t + k * 0.1)) { libre = false; break; }
        if (libre) { ok = true; break; }
        t += 0.1;
      }
      if (!ok) return [];
      const ev = [{ tipo: "ave", t, trazos: canto.trazos, dur: canto.dur, pan: ave.pan, vol: ave.e.vol, corte: this.c.g.aves.corte, ave: ave.nombre, que }];
      if (this.c.g.resonancia_aves) {   // ±40 cents de un parcial del muro: ese parcial se enciende
        const { co, cu } = this.acordeEn(t), parciales = [];
        for (const n of co) for (let h = 1; h <= 12; h++) parciales.push(this.c.F0 * n * h);
        for (const m of cu) for (let h = 1; h <= 12; h++) parciales.push((this.c.FU / m) * h);
        for (const f of [...new Set(canto.usadas.map((x) => Math.round(x * 100) / 100))].sort((a, b) => a - b)) {
          let p = parciales[0];
          for (const q of parciales) if (Math.abs(log2(q / f)) < Math.abs(log2(p / f))) p = q;
          if (Math.abs(1200 * log2(p / f)) <= 40) ev.push({ tipo: "resuena", t: t + 0.08, f: p, ave_hz: f });
        }
      }
      return ev;
    }
    escalaEn(t) {
      const recientes = this.visitas.filter((v) => t - v.t >= 0 && t - v.t < 6);
      if (recientes.length) return recientes[recientes.length - 1].escala;
      const { co, cu } = this.acordeEn(t);
      return co.map((n) => this.c.F0 * n).concat(cu.map((m) => this.c.FU / m));
    }
    // ----- lo que pasa solo hasta el tiempo t (el sonido pide por adelantado)
    avesHasta(t) {
      const ev = [];
      this.aves.forEach((ave, i) => {
        while (this.avesT[i] <= t) {
          const t0 = this.avesT[i], canto = ave.cantar(this.r.aves, this.escalaEn(t0));
          ev.push(...this.ponerAve(t0, canto, ave, "canto"));
          this.avesT[i] = t0 + canto.dur + this.r.aves.exponential(ave.e.pausa) + 0.5;
        }
      });
      return ev;
    }
    tamborHasta(t) {
      const g = this.c.g, ev = [];
      if (!(g.tambor_libre > 0)) return ev;
      while (this.libre.t <= t) {
        const r = this.r.libre, t0 = this.libre.t;
        let notas = this.escalaEn(t0);
        const recientes = this.visitas.filter((v) => t0 - v.t >= 0 && t0 - v.t < 8);
        if (!(recientes.length && r.random() < 0.5)) { const { co, cu } = this.acordeEn(t0); notas = co.map((n) => this.c.F0 * n).concat(cu.map((m) => this.c.FU / m)); }
        const [golpes, prev] = fraseLibre(r, notas, t0, this.libre.prev, (this.c.BEAT / 4) * r.choice([1.5, 2, 3]));
        golpes.forEach((x) => (x.vel *= 0.85));
        ev.push(...golpes);
        this.libre.prev = prev;
        const dur = golpes.length ? golpes[golpes.length - 1].t - t0 : 1;
        this.libre.t = t0 + dur + r.exponential(5 / g.tambor_libre) + 0.8;
      }
      return ev;
    }
    pulsoHasta(t) {
      const c = this.c, P = PULSOS[c.g.pulso], ev = [], rng = this.r.pulso;
      const casa = c.CASA.map((n) => regTambor(c.F0 * n));
      const tambor = (tt, vel) => { const [a, b] = rng.choiceN(casa, 2); return { tipo: "golpe", t: tt, desde: a, hasta: b, vel, glide: rng.uniform(0.04, 0.1), largo: 0.45, apagado: rng.random() < 0.3 }; };
      while (this.pulsoJ * P.tiempos * c.BEAT <= t) { ev.push(...P.compas(this.pulsoJ, this.pulsoJ * P.tiempos * c.BEAT, c.BEAT, rng, tambor)); this.pulsoJ++; }
      return ev;
    }
  }

  function genoma(nombreOPorte) {
    const titulo = PORTE_A_CANCION[nombreOPorte] || nombreOPorte;
    return SERIE_DIA.find((g) => g.titulo === titulo) || SERIE_DIA[1];
  }

  return { VERSION, azar, SERIE_DIA, PORTE_A_CANCION, LENTES, ESPECIES, genoma, cancion, Jardin, gemela, rugosidad, rugAcordes, parcialesDe,
    afinar, poza, buscarCasa, masCercano, gradoHz, Principal, salpicar, aguaArpa, registro };
});
