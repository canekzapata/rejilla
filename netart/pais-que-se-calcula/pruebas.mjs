// pruebas.mjs — node pruebas.mjs
// El motor calcula cada celda directo (Lucas/Frobenius); aquí se compara contra
// caminar paso a paso, que es lento pero no puede equivocarse.
import { capaDe, coef, celda, ventanaNativa, crearMundo, ventana, orilla, genealogia, densidadTramo, rngDe, genAhora, genDeMs, FUERA, MOTOR } from './motor.js';
import { TEXTO_FUNDADOR, SEMILLA } from './fundador.js';
import { vidaVentana, REGLA_VIDA } from './vida.js';

let ok = 0, mal = 0;
function prueba(nombre, fn) {
  try {
    const r = fn();
    if (r === true || r === undefined) { ok++; console.log('  ✓', nombre); }
    else { mal++; console.log('  ✗', nombre, r); }
  } catch (e) { mal++; console.log('  ✗', nombre, e.stack); }
}
const r = rngDe('pruebas');
const ent = (n) => Math.floor(r() * n);

function capaAzar(nSemillas = 1 + ent(12)) {
  const p = [2, 3, 5, 7][ent(4)];
  const semillas = [];
  for (let i = 0; i < nSemillas; i++) semillas.push({ x: ent(60) - 30, v: 1 + ent(p - 1), k: i });
  // dos semillas en el mismo lugar se suman, igual que en el motor
  return capaDe({ p, cl: 1 + ent(p - 1), cc: ent(p), cr: 1 + ent(p - 1), semillas });
}
// caminar: una tira que alcanza a cubrir el cono
function caminar(c, T) {
  const off = T + 40, n = 2 * off + 1;
  let a = new Uint8Array(n);
  for (let i = 0; i < c.sx.length; i++) a[c.sx[i] + off] = (a[c.sx[i] + off] + c.sv[i]) % c.p;
  const filas = [a];
  for (let t = 1; t <= T; t++) {
    const b = new Uint8Array(n);
    for (let x = 1; x < n - 1; x++) b[x] = (c.cl * a[x - 1] + c.cc * a[x] + c.cr * a[x + 1]) % c.p;
    filas.push(b); a = b;
  }
  return { filas, off };
}

console.log(MOTOR);

prueba('coeficiente de f^t = desarrollar el polinomio, t ≤ 400', () => {
  for (let k = 0; k < 30; k++) {
    const c = capaAzar(1);
    let poli = new Map([[0, 1]]);
    for (let t = 0; t <= 400; t++) {
      for (let m = -t - 2; m <= t + 2; m++) {
        const esperado = poli.get(m) || 0;
        if (coef(c, t, m) !== esperado) return `p=${c.p} (${c.cl},${c.cc},${c.cr}) t=${t} m=${m}: ${coef(c, t, m)} vs ${esperado}`;
      }
      const sig = new Map();
      for (const [e, v] of poli) {
        for (const [de, w] of [[-1, c.cr], [0, c.cc], [1, c.cl]]) sig.set(e + de, ((sig.get(e + de) || 0) + v * w) % c.p);
      }
      poli = sig;
    }
  }
});

prueba('celda directa = caminar, 40 capas al azar, todas las celdas hasta t=600', () => {
  for (let k = 0; k < 40; k++) {
    const c = capaAzar();
    const { filas, off } = caminar(c, 600);
    for (let t = 0; t <= 600; t += 1 + ent(7)) {
      for (let x = -t - 35; x <= t + 35; x++) {
        const v = celda(c, x, t);
        const esperado = x < c.xMin - t || x > c.xMax + t ? FUERA : filas[t][x + off];
        if (v !== esperado) return `capa ${k} p=${c.p} (x=${x}, t=${t}): ${v} vs ${esperado}`;
      }
    }
  }
});

prueba('t gigante: celda(t+j) = j pasos desde la fila t, t ~ 10^9 y 10^12', () => {
  for (let k = 0; k < 20; k++) {
    const c = capaAzar();
    const t = ent(2) ? 1e9 + ent(1e6) : 1e12 + ent(1e9);
    const X = ent(2 * t) - t, W = 120, J = 30;
    let fila = Array.from({ length: W + 2 * J }, (_, i) => { const v = celda(c, X - J + i, t); return v === FUERA ? 0 : v; });
    for (let j = 1; j <= J; j++) {
      fila = fila.slice(2).map((_, i) => (c.cl * fila[i] + c.cc * fila[i + 1] + c.cr * fila[i + 2]) % c.p);
      const real = Array.from({ length: fila.length }, (_, i) => celda(c, X - J + j + i, t + j));
      if (real.some((v, i) => (v === FUERA ? 0 : v) !== fila[i])) return `t=${t}+${j}`;
    }
  }
});

prueba('ventana = celdas una por una (con orilla y antes del origen)', () => {
  for (let k = 0; k < 40; k++) {
    const c = capaAzar();
    const W = 1 + ent(120), H = 1 + ent(120);
    const T0 = ent(3000) - 100, X0 = ent(2 * Math.max(T0, 50)) - Math.max(T0, 50) - W / 2 | 0;
    const v = ventanaNativa(c, X0, T0, W, H);
    for (let y = 0; y < H; y += 1 + ent(4))
      for (let x = 0; x < W; x++) {
        const e = celda(c, X0 + x, T0 + y);
        if (v[y * W + x] !== e) return `k=${k} (x=${X0 + x}, t=${T0 + y}) ${v[y * W + x]} vs ${e}`;
      }
  }
});

const mundo = crearMundo({ semilla: SEMILLA, texto: TEXTO_FUNDADOR });
const ahora = Math.floor(genAhora());

prueba('ventana del mundo con escalas = celda por celda', () => {
  for (let k = 0; k < 10; k++) {
    const T0 = ahora - ent(1e5), X0 = ent(2 * T0) - T0, W = 90, H = 70;
    const v = ventana(mundo, X0, T0, W, H);
    for (const [i, c] of mundo.capas.entries())
      for (let y = 0; y < H; y += 3) for (let x = 0; x < W; x += 2) {
        const e = celda(c, Math.floor((X0 + x) / c.escala), Math.floor((T0 + y) / c.escala));
        if (v[i][y * W + x] !== e) return `capa ${i}`;
      }
  }
});

prueba('dos ventanas que se enciman dicen lo mismo en lo compartido', () => {
  for (let k = 0; k < 10; k++) {
    const T = ahora - ent(1e5), X = ent(2 * T) - T;
    const a = ventana(mundo, X, T, 200, 150);
    const dx = ent(100), dt = ent(100);
    const b = ventana(mundo, X + dx, T + dt, 200, 150);
    for (let i = 0; i < a.length; i++)
      for (let y = 0; y < 150 - dt; y++) for (let x = 0; x < 200 - dx; x++)
        if (a[i][(y + dt) * 200 + x + dx] !== b[i][y * 200 + x]) return `capa ${i}`;
  }
});

// con mod 2 y 3 la letra sólo cuenta por paridad: lo que funda el mundo es la
// forma del texto (dónde caen letras, blancos y versos). Por eso se agrega una.
prueba('misma semilla = mismo mundo; una letra de más = otro mundo', () => {
  const igual = crearMundo({ semilla: SEMILLA, texto: TEXTO_FUNDADOR });
  const otro = crearMundo({ semilla: SEMILLA, texto: TEXTO_FUNDADOR.replace('sombra', 'sombras') });
  // cerca del origen, donde el cono de cada letra ya alcanzó la ventana
  const a = ventana(mundo, -2000, 400, 8000, 30), b = ventana(igual, -2000, 400, 8000, 30), c = ventana(otro, -2000, 400, 8000, 30);
  if (!a.every((v, i) => v.every((x, j) => x === b[i][j]))) return 'la misma semilla dio otro mundo';
  if (a.every((v, i) => v.every((x, j) => x === c[i][j]))) return 'agregar una letra no cambió nada';
});

// --- genealogía (loop 03) ---
prueba('genealogía: la suma de los aportes de las letras es el valor de la celda', () => {
  for (let k = 0; k < 300; k++) {
    const t = [ent(3000), ahora - ent(1e5), ent(1e9)][k % 3];
    const [a, b] = orilla(mundo, t);
    const X = a + ent(b - a);
    for (const g of genealogia(mundo, X, t)) {
      if (g.valor === FUERA) { if (g.letras.length) return 'fuera del cono y con letras'; continue; }
      const s = g.letras.reduce((acc, l) => acc + l.aporte, 0) % g.p;
      if (s !== g.valor) return `capa ${g.capa} (X=${X}, t=${t}): suma ${s} vs ${g.valor}`;
    }
  }
});

// el árbol que dibuja la página: cualquier renglón del pasado, pesado por los
// coeficientes, suma exactamente la celda (la ley es lineal)
prueba('árbol: Σ coef(t−t′, x−x′)·celda(x′, t′) sobre un renglón pasado = celda(x, t)', () => {
  for (let k = 0; k < 60; k++) {
    const c = mundo.capas[ent(3)];
    const t = 2000 + ent(Math.floor(ahora / c.escala)), x = ent(2 * t) - t;
    const dt = 1 + ent(300), t2 = t - dt;
    let s = 0;
    for (let x2 = x - dt; x2 <= x + dt; x2++) {
      const v = celda(c, x2, t2);
      if (v !== FUERA && v) s += coef(c, dt, x - x2) * v;
    }
    const e = celda(c, x, t);
    if (s % c.p !== (e === FUERA ? 0 : e)) return `x=${x} t=${t} dt=${dt}`;
  }
});

// --- la vida (loop 02) ---
prueba('vida: dos ventanas que se enciman coinciden (no depende de quién mira)', () => {
  for (let k = 0; k < 6; k++) {
    const T = ahora - 2000 - ent(50000), X = orilla(mundo, T)[1] - 300 - ent(2000);
    const a = vidaVentana(mundo, REGLA_VIDA, X, T, 180, 200);
    const dx = 1 + ent(90), dt = 1 + ent(150);
    const b = vidaVentana(mundo, REGLA_VIDA, X + dx, T + dt, 180, 200);
    for (let y = 0; y < 200 - dt; y++) for (let x = 0; x < 180 - dx; x++)
      if (a[(y + dt) * 180 + x + dx] !== b[y * 180 + x]) return `k=${k} (x=${x}, y=${y})`;
  }
});

prueba('vida: exacta — arrancar 200 generaciones antes y con 200 columnas más da lo mismo', () => {
  for (let k = 0; k < 8; k++) {
    const T = ahora - ent(80000), X = orilla(mundo, T)[1] - 200 - ent(4000);
    const a = vidaVentana(mundo, REGLA_VIDA, X, T, 160, 120);
    const b = vidaVentana(mundo, REGLA_VIDA, X, T, 160, 120, null, 200);
    for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return `k=${k} celda ${i}`;
  }
  // y en el nacimiento del mundo, donde no hay pasado
  const a = vidaVentana(mundo, REGLA_VIDA, -400, 0, 800, 60), b = vidaVentana(mundo, REGLA_VIDA, -400, 0, 800, 60, null, 200);
  if (a.some((v, i) => v !== b[i])) return 'en el origen';
});

console.log(`\n${ok} bien, ${mal} mal\n`);

// --- medidas (no son pruebas: son para leer) ---
console.log('mundo:', mundo.capas.map(c => `p=${c.p} (${c.cl},${c.cc},${c.cr}) ×${c.escala} ${c.sx.length} semillas`).join(' · '));
const [oa, ob] = orilla(mundo, ahora);
console.log(`orilla hoy (t=${ahora}): ${oa} … ${ob} → ${(ob - oa).toLocaleString('es-MX')} celdas de ancho`);
const t3026 = Math.floor(genDeMs(Date.UTC(3026, 9, 2, 6)));
const [pa, pb] = orilla(mundo, t3026);
console.log(`orilla en 3026: ${(pb - pa).toLocaleString('es-MX')} celdas de ancho`);
const medir = (nombre, fn, n = 3) => {
  const t0 = performance.now(); for (let i = 0; i < n; i++) fn();
  console.log(`  ${nombre}: ${((performance.now() - t0) / n).toFixed(1)} ms`);
};
console.log('tiempos:');
medir('ventana 640×360 hoy, en el centro', () => ventana(mundo, -320, ahora - 220, 640, 360));
medir('ventana 640×360 hoy, lejos del centro', () => ventana(mundo, 400000, ahora - 220, 640, 360));
medir('ventana 640×360 en 3026', () => ventana(mundo, 1e9, t3026, 640, 360));
medir('ventana 1280×720 hoy', () => ventana(mundo, -640, ahora - 440, 1280, 720));
console.log('densidad (fracción viva en 2000 celdas alrededor de x):');
for (const [t, x] of [[100, 0], [5000, 0], [ahora, 0], [ahora, ahora / 2 | 0], [ahora, ahora - 3000], [t3026, 0], [t3026, t3026 / 3 | 0]])
  console.log(`  t=${String(t).padStart(11)} x=${String(x).padStart(11)}  ` + mundo.capas.map(c => densidadTramo(c, Math.floor(x / c.escala), 2000, Math.floor(t / c.escala)).toFixed(3)).join('  '));
process.exit(mal ? 1 : 0);
