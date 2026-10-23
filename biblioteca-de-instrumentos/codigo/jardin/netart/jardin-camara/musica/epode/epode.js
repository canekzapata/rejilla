/* epode.js — «Épode del jardín»: aves bitonales sentadas en los nudos de una planta 3D del
 * jardín; un autómata excitable sobre el grafo de la planta decide quién canta y pasa motivos
 * de ave en ave (ondas que viajan por las ramas: cánones); cada canto es fractal en tres niveles.
 *
 * Canek (16 oct 2026): «la Épode de Messiaen… ¿qué pasa con un autómata de Wolfram de 3
 * dimensiones?» y «jugar a hacer instrumentos como pájaros dutonales o tritonales, armónicos
 * extraños, que podamos fractalizar como un autómata».
 *
 * De Messiaen (Chronochromie, Épode): muchas aves a la vez, cada una con su carácter.
 * La lección: el autómata NO genera notas (eso da textura); decide QUIÉN canta y CUÁNDO, y
 * cada ave conserva su manera.
 *
 * Autómata: Greenberg–Hastings (medio excitable) sobre el grafo de la planta. Estados:
 *   0 callada · 1 canta · 2..R descansa. Una callada canta si 1 o 2 vecinas cantan (con 3 o
 *   más se inhibe: así no satura) o, rara vez, sola (una semilla nueva de motivo). En un árbol
 *   esto produce ondas que suben por el tallo, saltan a otra rama, chocan y se anulan.
 * Canon: el ave que se excita canta el MOTIVO de la que la excitó, transpuesto a su altura.
 * Fractal (el mismo contorno en tres escalas):
 *   macro  cada ave de la onda transpone el motivo según el contorno (paso k de la onda)
 *   medio  las notas del motivo siguen el contorno
 *   micro  cada nota entra con un adorno que repite el contorno en pequeño y rápido
 * Bitonal: el lado 0 de la siringe canta armónicos de F0 (F0·n); el lado 1, la gemela
 *   subarmónica (FU/m) más cercana: cada ave es un choque. Dos aves «imposibles» tienen un
 *   tercer lado (otra siringe) en la familia del 7.
 * Espacio: x del nudo → paneo; z (profundidad) → distancia; y (altura) → registro.
 *
 * Epode.componer(opciones) → {aves, pasos, eventosPorAve, registro}
 * Funciona en Node (require) y en el navegador (window.Epode). Determinista por semilla.
 */
(function (global) {
  'use strict';

  function pulse(x, y, g) { let h = (x * 374761393 ^ y * 668265263 ^ g * 2246822519) >>> 0; h = Math.imul(h ^ h >>> 13, 1274126177); return ((h ^ h >>> 16) >>> 0) / 4294967296; }  // = flores3d.js
  function rngDe(s) { let h = (s >>> 0) || 1; return function () { h ^= h << 13; h >>>= 0; h ^= h >> 17; h ^= h << 5; h >>>= 0; return h / 4294967296; }; }
  const midi = f => 69 + 12 * Math.log2(f / 440);

  // ---------------------------------------------------------------- la planta como grafo
  function vecinosDeAves(planta, idx) {
    // distancia en saltos por el árbol entre los nudos con ave
    const n = planta.nodes.length, ady = Array.from({ length: n }, () => []);
    planta.edges.forEach(e => { ady[e.parent].push(e.node); ady[e.node].push(e.parent); });
    const dist = idx.map(src => { const d = new Array(n).fill(Infinity), q = [src]; d[src] = 0;
      while (q.length) { const u = q.shift(); ady[u].forEach(v => { if (d[v] === Infinity) { d[v] = d[u] + 1; q.push(v); } }); } return d; });
    return idx.map((a, i) => {
      const orden = idx.map((b, j) => [dist[i][b], j]).filter(x => x[1] !== i).sort((p, q) => p[0] - q[0]);
      // las 2–4 más cercanas por las ramas
      const lim = orden[Math.min(2, orden.length - 1)][0];
      return orden.filter((x, k) => k < 4 && (x[0] <= lim || k < 2)).map(x => x[1]);
    });
  }

  function elegirNudos(planta, k, rnd) {
    // primero los nudos de las flores (puntas), luego nudos de rama al azar, sin repetir posición
    const flores = planta.edges.filter(e => !e.noHead).map(e => e.node);
    const ramas = planta.edges.filter(e => e.noHead).map(e => e.node).sort(() => rnd() - .5);
    const out = [];
    for (const id of flores.concat(ramas)) { if (out.length >= k) break;
      const p = planta.nodes[id].p; if (out.every(j => Math.hypot(...planta.nodes[j].p.map((v, i) => v - p[i])) > .12)) out.push(id); }
    return out;
  }

  // ---------------------------------------------------------------- material armónico
  function familias(F0, FU) {
    const arm = [], sub = [];
    for (let n = 8; n <= 40; n++) arm.push({ f: F0 * n, n });
    for (let m = 4; m <= 48; m++) sub.push({ f: FU / m, m });
    return { arm, sub, F0 };
  }
  function enRegistro(f, lo, hi) { while (f < lo) f *= 2; while (f > hi) f /= 2; return f; }
  function gemela(f, sub) {   // la subarmónica (cualquier octava) más cercana entre 15 y 110 cents; si no, la más cercana
    let mejor = null;
    sub.forEach(s => { const g = enRegistro(s.f, f / 1.45, f * 1.45), c = Math.abs(1200 * Math.log2(g / f));
      const costo = (c >= 15 && c <= 110) ? c : c + 400; if (!mejor || costo < mejor.costo) mejor = { f: g, m: s.m, c, costo }; });
    return mejor;
  }

  // ---------------------------------------------------------------- motivos
  function nuevoMotivo(rnd, id) {
    const largo = 3 + Math.floor(rnd() * 3);
    const contorno = [0]; for (let i = 1; i < largo; i++) contorno.push(contorno[i - 1] + [-3, -2, -1, 1, 2, 3, 4][Math.floor(rnd() * 7)]);
    const ritmo = contorno.map(() => [.08, .12, .16, .22][Math.floor(rnd() * 4)]);
    const gesto = ['canto', 'canto', 'silbido', 'trino'][Math.floor(rnd() * 4)];
    return { id, contorno, ritmo, gesto };
  }

  // Un canto: nivel medio (las notas del motivo) + micro (adorno con el mismo contorno, pequeño)
  function cantoDeAve(ave, motivo, pasoOnda, t0, rnd, fam) {
    // nivel macro: la distancia que la onda lleva recorrida por las ramas (en nudos, cada 3) elige
    // el grado del contorno: las aves lejanas cantan el motivo transpuesto más allá
    const macro = motivo.contorno[Math.floor(pasoOnda / 3) % motivo.contorno.length];
    const base = ave.n0 + macro;
    const ev = [], notas = [];
    let t = 0;
    motivo.contorno.forEach((c, i) => {
      let n = base + c;                                                      // sin tope: cualquier parcial, doblado al registro
      if (n < 6) n = 12 - n;                                                 // si baja de más, el contorno se refleja (no se recorta)
      const f = enRegistro(fam.F0 * n, ave.lo, ave.hi);
      notas.push({ t, f, d: motivo.ritmo[i] * ave.tempo });
      t += motivo.ritmo[i] * ave.tempo * (1.15 + .3 * rnd());
    });
    // micro: cada nota entra por un adorno que repite el contorno, en semitonos chicos y rápido
    const escalaMicro = .25;   // un cuarto del intervalo, un quinto del tiempo
    const cantoNotas = [];
    notas.forEach(nt => {
      if (nt.d > .1 && rnd() < .6) {
        motivo.contorno.slice(0, 3).forEach((c, k) => cantoNotas.push([nt.t + k * .022, midi(nt.f) + c * escalaMicro, .02]));
        cantoNotas.push([nt.t + .066, midi(nt.f), nt.d - .066]);
      } else cantoNotas.push([nt.t, midi(nt.f), nt.d]);
    });
    const dur = t + .15;
    const tipo = motivo.gesto;
    const lado = (voz, mapa) => {
      if (tipo === 'canto') return { t: t0, tipo: 'canto', voz, dur, v: ave.v, notas: cantoNotas.map(([a, m, d]) => [a, mapa(m), Math.max(.02, d)]) };
      const a = notas[0], b = notas[notas.length - 1];
      return { t: t0, tipo, voz, dur: Math.min(dur, .9), v: ave.v, m: mapa(midi(a.f)), m2: mapa(midi(b.f)), rate: 14 + 8 * rnd() };
    };
    // lado 0: armónico; lado 1: gemela subarmónica de cada nota (el choque dentro del ave)
    ev.push(lado(0, m => m));
    ev.push(lado(1, m => { const g = gemela(440 * Math.pow(2, (m - 69) / 12), fam.sub); return midi(g.f); }));
    const tercero = ave.imposible ? lado(0, m => midi(enRegistro(440 * Math.pow(2, (m - 69) / 12) * 7 / 4, ave.lo, ave.hi * 1.3))) : null;
    return { ev, tercero, notas, dur };
  }

  // ---------------------------------------------------------------- el coro
  function componer(o) {
    o = Object.assign({ semilla: 3, porte: 'candelabro', flores: 25, aves: 15, pasos: 120, paso: .7,
      F0: 27.5, FU: 3300, espontaneo: .02, descanso: 3, imposibles: 2 }, o || {});
    const rnd = rngDe(o.semilla * 7919 + 17);
    const planta = global.FloraPlant.build(o.semilla, o.flores, pulse, o.porte);
    const idx = elegirNudos(planta, o.aves, rnd);
    const vecinos = vecinosDeAves(planta, idx);
    const fam = familias(o.F0, o.FU);
    const ys = idx.map(i => planta.nodes[i].p[1]), ymin = Math.min(...ys), ymax = Math.max(...ys);
    const xs = idx.map(i => planta.nodes[i].p[0]), xabs = Math.max(...xs.map(Math.abs)) || 1;
    const zs = idx.map(i => planta.nodes[i].p[2]), zmin = Math.min(...zs), zmax = Math.max(...zs);
    const aves = idx.map((nodo, i) => {
      const alto = (ys[i] - ymin) / ((ymax - ymin) || 1);                 // las ramas altas cantan agudo
      const lo = 900 * Math.pow(2, alto * 1.1), hi = lo * 2.4;
      return { i, nodo, p: planta.nodes[nodo].p, pan: xs[i] / xabs * .9,
        lejos: (zs[i] - zmin) / ((zmax - zmin) || 1), lo, hi, n0: 16 + Math.floor(rnd() * 8),
        tempo: .8 + .6 * rnd(), v: .55 + .3 * rnd(), imposible: i < o.imposibles, vecinos: vecinos[i] };
    });
    // el autómata corre sobre TODOS los nudos de la planta (v2): el canto viaja por el tallo y
    // las ramas nudo por nudo, haya ave o no; un ave canta cuando la onda pasa por su nudo.
    // Así el tiempo entre dos aves es su distancia real por las ramas: cánones que se estiran.
    const N = planta.nodes.length, ady = Array.from({ length: N }, () => []);
    planta.edges.forEach(e => { ady[e.parent].push(e.node); ady[e.node].push(e.parent); });
    const aveEn = new Map(idx.map((nodo, i) => [nodo, i]));
    let estado = new Array(N).fill(0), motivoDe = new Array(N).fill(null), pasoOndaDe = new Array(N).fill(0);
    const pasos = [], pasosNudos = [], eventos = aves.map(() => []), terceros = aves.map(() => []), registro = [];
    let motivos = 0;
    for (let s = 0; s < o.pasos; s++) {
      const nuevo = estado.slice(), nm = motivoDe.slice(), np = pasoOndaDe.slice(), quien = new Array(N).fill(null);
      for (let u = 0; u < N; u++) {
        if (estado[u] === 0) {
          const cantan = ady[u].filter(v => estado[v] === 1);
          if (cantan.length === 1 || cantan.length === 2) {
            const v = cantan[Math.floor(rnd() * cantan.length)];
            nuevo[u] = 1; nm[u] = motivoDe[v]; np[u] = pasoOndaDe[v] + 1; quien[u] = v;   // nudos recorridos
          } else if (cantan.length === 0 && aveEn.has(u) && rnd() < o.espontaneo) {
            nuevo[u] = 1; nm[u] = nuevoMotivo(rnd, motivos++); np[u] = 0; quien[u] = 'semilla';
          }
        } else if (estado[u] === 1) nuevo[u] = 2;
        else nuevo[u] = estado[u] >= o.descanso + 1 ? 0 : estado[u] + 1;
      }
      if (s === 0 && !nuevo.some(x => x === 1)) { const u = idx[0]; nuevo[u] = 1; nm[u] = nuevoMotivo(rnd, motivos++); quien[u] = 'semilla'; }
      estado = nuevo; motivoDe = nm; pasoOndaDe = np;
      pasosNudos.push(estado.slice());
      pasos.push(idx.map(u => estado[u]));
      idx.forEach((u, i) => {
        if (estado[u] !== 1) return;
        const a = aves[i];
        const t0 = s * o.paso + .05 + rnd() * .3;                                  // rubato
        const c = cantoDeAve(a, motivoDe[u], pasoOndaDe[u], t0, rnd, fam);
        eventos[i].push(...c.ev); if (c.tercero) terceros[i].push(c.tercero);
        const de = quien[u] === 'semilla' ? 'semilla' : 'onda';
        registro.push({ paso: s, ave: i, motivo: motivoDe[u].id, onda: pasoOndaDe[u], de, t: +t0.toFixed(3),
          notas_hz: c.notas.map(n => +n.f.toFixed(2)) });
      });
    }
    return { opciones: o, planta: { porte: planta.porte, nodos: planta.nodes.length, tramos: planta.edges.length },
      aves: aves.map(a => ({ i: a.i, nodo: a.nodo, p: a.p, pan: +a.pan.toFixed(3), lejos: +a.lejos.toFixed(3), lo: +a.lo.toFixed(1),
        n0: a.n0, imposible: a.imposible, vecinos: a.vecinos })),
      pasos, pasosNudos, eventos, terceros, registro, motivos, duracion: o.pasos * o.paso + 2.5, nodos: planta.nodes.map(n => n.p),
      tramos: planta.edges.map(e => [e.parent, e.node]) };
  }

  const api = { componer, pulse };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else global.Epode = api;
})(typeof window !== 'undefined' ? window : globalThis);
