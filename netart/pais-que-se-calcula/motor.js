// motor.js — la ley exacta del país.
//
// Cada capa es un autómata 1D LINEAL sobre GF(p) en una línea infinita:
//   b[x] = cl·a[x-1] + cc·a[x] + cr·a[x+1]   (mod p)
// La fila t es el renglón cero multiplicado por f(z)^t, f = cl·z + cc + cr·z⁻¹.
// En GF(p)[z] vale f(z)^(p^j) = f(z^(p^j)) (Frobenius), así que con t escrito
// en base p, f^t = Π_j f^(d_j)(z^(p^j)) y el coeficiente de z^m sale dígito por
// dígito (Lucas generalizado) en O(log t). Por eso cualquier celda de cualquier
// año se calcula directa, sin simular lo anterior, y todos ven lo mismo.
//
// El renglón cero es el texto fundador: una celda viva por letra. Nada existe
// fuera del cono de luz del texto: el país crece una celda por segundo de cada
// lado. Tiene orilla, y la orilla avanza.

export const MOTOR = 'pais-01.2';
// 2 de octubre de 2026, 00:00 en Ciudad de México (UTC-6). No se olvida.
export const ORIGEN_MS = Date.UTC(2026, 9, 2, 6, 0, 0);
export const GEN_POR_SEG = 1;
export const FUERA = 255; // fuera del cono de luz: el país todavía no llega ahí

export function genDeMs(ms) { return (ms - ORIGEN_MS) / 1000 * GEN_POR_SEG; }
export function msDeGen(g) { return ORIGEN_MS + g / GEN_POR_SEG * 1000; }
export function genAhora() { return genDeMs(Date.now()); }

// --- azar sembrado (sin Math.random en ningún lado) ---
function xmur3(s) {
  let h = 1779033703 ^ s.length;
  for (let i = 0; i < s.length; i++) {
    h = Math.imul(h ^ s.charCodeAt(i), 3432918353);
    h = (h << 13) | (h >>> 19);
  }
  return () => {
    h = Math.imul(h ^ (h >>> 16), 2246822507);
    h = Math.imul(h ^ (h >>> 13), 3266489909);
    return (h ^= h >>> 16) >>> 0;
  };
}
function mulberry32(a) {
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
export function rngDe(texto) { return mulberry32(xmur3(texto)()); }

// Una capa: la regla y sus semillas (posición, valor, letra que la puso).
// F[d][e+d] = coeficiente de z^e en f^d, para d < p.
export function capaDe({ p, cl, cc, cr, semillas, escala = 1 }) {
  const F = [[1]];
  for (let d = 1; d < p; d++) {
    const ant = F[d - 1], nuevo = new Array(2 * d + 1).fill(0);
    for (let i = 0; i < ant.length; i++) {
      const v = ant[i];
      if (!v) continue;
      nuevo[i] = (nuevo[i] + v * cr) % p;     // z^-1: lo que viene de la derecha
      nuevo[i + 1] = (nuevo[i + 1] + v * cc) % p;
      nuevo[i + 2] = (nuevo[i + 2] + v * cl) % p; // z: lo que viene de la izquierda
    }
    F.push(nuevo);
  }
  const ss = semillas.slice().sort((a, b) => a.x - b.x);
  return {
    p, cl, cc, cr, F, escala,
    sx: Int32Array.from(ss, (s) => s.x), sv: Uint8Array.from(ss, (s) => s.v),
    sk: Int32Array.from(ss, (s) => s.k ?? -1),
    xMin: ss.length ? ss[0].x : 0, xMax: ss.length ? ss[ss.length - 1].x : 0,
  };
}

// Coeficiente de z^m en f(z)^t (mod p). Se van comiendo los dígitos de t desde
// abajo; en cada uno, e_j ≡ m (mod p) y |e_j| ≤ d_j. Como e_j puede ser negativo
// quedan a lo más dos restos posibles por paso: se llevan los dos.
const restos = new Float64Array(4), pesos = new Int32Array(4), restos2 = new Float64Array(4), pesos2 = new Int32Array(4);
export function coef(capa, t, m) {
  if (m > t || m < -t) return 0;
  const { p, F } = capa;
  let n = 1; restos[0] = m; pesos[0] = 1;
  let tt = t;
  while (tt > 0) {
    const d = tt % p;
    tt = (tt - d) / p;
    const fila = F[d];
    let n2 = 0;
    for (let i = 0; i < n; i++) {
      const r = restos[i], w = pesos[i];
      let e = ((r % p) + p) % p;          // e ≡ r, primero el no negativo…
      for (let k = 0; k < 2; k++, e -= p) { // …y luego e - p
        if (e > d || e < -d) continue;
        const c = fila[e + d];
        if (!c) continue;
        const r2 = (r - e) / p, w2 = (w * c) % p;
        let j = 0;
        while (j < n2 && restos2[j] !== r2) j++;
        if (j === n2) { restos2[n2] = r2; pesos2[n2] = w2; n2++; }
        else pesos2[j] = (pesos2[j] + w2) % p;
      }
    }
    if (!n2) return 0;
    n = 0;
    for (let i = 0; i < n2; i++) if (pesos2[i]) { restos[n] = restos2[i]; pesos[n] = pesos2[i]; n++; }
    if (!n) return 0;
  }
  for (let i = 0; i < n; i++) if (restos[i] === 0) return pesos[i];
  return 0;
}

// Valor exacto de una celda (x, t) de la capa, en sus propias coordenadas.
export function celda(capa, x, t) {
  if (t < 0 || x < capa.xMin - t || x > capa.xMax + t) return FUERA;
  const { p, sx, sv } = capa;
  let s = 0;
  for (let i = 0; i < sx.length; i++) {
    const m = x - sx[i];
    if (m > t || m < -t) continue;
    const c = coef(capa, t, m);
    if (c) s += c * sv[i];
  }
  return s % p;
}

// Cinco capas a escalas que van de la celda a miles de celdas: las finas son
// tinta (trama), las enormes son campo (el color de fondo de una región que
// cambia cada tantas horas). Una capa a escala e vive en (x/e, t/e): es más
// joven y por eso sigue densa cuando las finas ya se volvieron desierto.
export const ESCALA_CAMPO = 100;
export function crearMundo({ semilla, texto }) {
  const r = rngDe('pais|' + semilla);
  const letras = [...texto];
  const escalas = [1, 3 + Math.floor(r() * 5), 24 + Math.floor(r() * 40), 200 + Math.floor(r() * 300), 2000 + Math.floor(r() * 3000)];
  const capas = escalas.map((escala) => {
    const campo = escala >= ESCALA_CAMPO;
    // tinta sólo mod 2 y mod 3: con mod 5 y 7 las letras encimadas dan estática (medido)
    const p = campo ? [2, 3, 3, 5][Math.floor(r() * 4)] : [2, 3, 3][Math.floor(r() * 3)];
    // los vecinos nunca son cero: si no, la capa no se propaga hacia un lado.
    // Centro cero casi siempre: con centro las tramas se vuelven estática (medido)
    const cl = 1 + Math.floor(r() * (p - 1));
    const cr = 1 + Math.floor(r() * (p - 1));
    const cc = r() < 0.7 ? 0 : Math.floor(r() * p);
    // letras separadas en la tinta: sus triángulos se cruzan como moaré y no como ruido
    const paso = campo ? [1, 2, 3, 4, 6][Math.floor(r() * 5)] : [5, 8, 13, 21, 34][Math.floor(r() * 5)];
    const desfase = Math.floor((r() - 0.5) * 400);
    const semillas = [];
    let x = desfase;
    letras.forEach((ch, k) => {
      if (ch === '\n') { x += paso * 5; return; }
      if (/\s/.test(ch)) { x += paso * 2; return; }
      semillas.push({ x, v: 1 + (ch.codePointAt(0) % (p - 1)), k });
      x += paso;
    });
    const c = capaDe({ p, cl, cc, cr, semillas, escala });
    c.papel = campo ? 'campo' : 'tinta';
    return c;
  });
  const mult = [];
  let m = 1;
  for (const c of capas) { mult.push(m); m *= c.p; }
  return { semilla, texto, letras, capas, mult, estados: m };
}

// La orilla del país en la generación t (columnas del mundo). El país es el
// cono de luz de las capas de tinta; los campos sólo se ven adentro.
export function orilla(mundo, t) {
  let a = Infinity, b = -Infinity;
  for (const c of mundo.capas) {
    if (c.papel === 'campo') continue;
    const tc = Math.floor(t / c.escala);
    a = Math.min(a, (c.xMin - tc) * c.escala);
    b = Math.max(b, (c.xMax + tc + 1) * c.escala - 1);
  }
  return [a, b];
}

// Ventana de W×H en las coordenadas propias de la capa: el renglón T0 se
// calcula directo en el ancho del cono de la ventana y luego se camina hacia
// abajo. Lo de fuera del cono de luz vale FUERA.
export function ventanaNativa(capa, X0, T0, W, H, out) {
  const { p, cl, cc, cr } = capa;
  const o = out || new Uint8Array(W * H);
  o.fill(FUERA);
  const tFin = T0 + H - 1;
  const tIni = Math.max(T0, 0);
  if (tIni > tFin) return o;
  const margen = tFin - tIni;
  let len = W + 2 * margen;
  let fila = new Uint8Array(len), sig = new Uint8Array(len);
  const L = X0 - margen;
  for (let i = 0; i < len; i++) {
    const v = celda(capa, L + i, tIni);
    fila[i] = v === FUERA ? 0 : v;
  }
  let izq = margen;
  for (let t = tIni; ; t++) {
    const a = capa.xMin - t, b = capa.xMax + t; // el cono en esta generación
    const base = (t - T0) * W;
    const x0 = Math.max(0, a - X0), x1 = Math.min(W - 1, b - X0);
    for (let x = x0; x <= x1; x++) o[base + x] = fila[izq + x];
    if (t === tFin) break;
    const n = len - 2;
    for (let i = 0; i < n; i++) sig[i] = (cl * fila[i] + cc * fila[i + 1] + cr * fila[i + 2]) % p;
    const tmp = fila; fila = sig; sig = tmp;
    len = n; izq -= 1;
  }
  return o;
}

const fdiv = (a, b) => Math.floor(a / b);

// Ventana del mundo: cada capa se calcula a su escala y se amplía.
export function ventana(mundo, X0, T0, W, H, outs) {
  return mundo.capas.map((c, i) => {
    const o = (outs && outs[i] && outs[i].length === W * H) ? outs[i] : new Uint8Array(W * H);
    const e = c.escala;
    if (e === 1) return ventanaNativa(c, X0, T0, W, H, o);
    const nx0 = fdiv(X0, e), nt0 = fdiv(T0, e);
    const nW = fdiv(X0 + W - 1, e) - nx0 + 1, nH = fdiv(T0 + H - 1, e) - nt0 + 1;
    const n = ventanaNativa(c, nx0, nt0, nW, nH);
    for (let y = 0; y < H; y++) {
      const ny = fdiv(T0 + y, e) - nt0;
      for (let x = 0; x < W; x++) o[y * W + x] = n[ny * nW + fdiv(X0 + x, e) - nx0];
    }
    return o;
  });
}

// Fracción viva de un tramo de una capa en la generación t (para leer).
export function densidadTramo(capa, x0, ancho, t) {
  let vivas = 0, dentro = 0;
  for (let x = x0; x < x0 + ancho; x++) {
    const v = celda(capa, x, t);
    if (v === FUERA) continue;
    dentro++; if (v) vivas++;
  }
  return dentro ? vivas / dentro : 0;
}

// Genealogía de una celda del mundo: por capa, qué letras del texto fundador
// llegan a (X, t) y con cuánto. La ley es lineal: el valor de la celda es
// exactamente la suma de esos aportes (mod p). Puede que lleguen letras y se
// anulen entre sí: entonces la celda está vacía aunque la hayan tocado.
export function genealogia(mundo, X, t) {
  return mundo.capas.map((c, i) => {
    const x = Math.floor(X / c.escala), tc = Math.floor(t / c.escala);
    const letras = [];
    if (tc >= 0) {
      for (let j = 0; j < c.sx.length; j++) {
        const m = x - c.sx[j];
        if (m > tc || m < -tc) continue;
        const k = coef(c, tc, m);
        if (k) letras.push({ k: c.sk[j], aporte: (k * c.sv[j]) % c.p });
      }
    }
    return { capa: i, papel: c.papel, p: c.p, escala: c.escala, valor: celda(c, x, tc), letras };
  });
}
