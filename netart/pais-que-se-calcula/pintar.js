// pintar.js — de los valores de las capas a píxeles. Lo usan la página, la
// hoja de contactos y el GIF, para que los tres vean exactamente lo mismo.
//
// Las capas de tinta se leen como color (paleta). Las capas de campo además se
// IMPRIMEN como achurado: cada valor tiene una dirección de recta y un
// espaciado, calculados en coordenadas del mundo (x, t), así que todos ven las
// mismas líneas. Donde la capa enorme cambia de valor, cambia el ángulo: esa
// costura es la figura del desierto.
import { FUERA, rngDe, coef } from './motor.js';
import { oklch, SEDIMENTO } from './color.js';

// direcciones enteras: la recta son las celdas con (a·x + b·t) ≡ 0 (mod s)
const DIRS = [[1, 0], [0, 1], [1, 1], [1, -1], [1, 2], [2, 1], [1, -2], [2, -1], [1, 3], [3, -1]];

export function crearAchurado(mundo) {
  const r = rngDe('achurado|' + mundo.semilla);
  return mundo.capas.map((c) => {
    if (c.papel !== 'campo') return null;
    const s = 3 + Math.floor(r() * 5);
    return Array.from({ length: c.p }, (_, v) => {
      const [a, b] = DIRS[Math.floor(r() * DIRS.length)];
      // a veces el cero no se raya: deja respirar
      return v === 0 && r() < 0.4 ? null : { a, b, s: s + Math.floor(r() * 3) };
    });
  });
}

const modp = (n, s) => ((n % s) + s) % s;

// vida (opcional): W×(H+SEDIMENTO), empieza SEDIMENTO filas arriba de T0; edad A
// para repartir los 8 tonos. Sólo se dibuja arriba del presente.
export function pintar({ mundo, pal, ach, datos, X0, T0, W, H, px32, yAhora = Infinity, cabeza = 0, vida = null, A = 1 }) {
  const capas = datos, nC = capas.length, mult = mundo.mult;
  const campos = [];
  let nTinta = 0;
  for (let c = 0; c < nC; c++) if (ach[c]) campos.push(c); else nTinta++;
  for (let y = 0, i = 0; y < H; y++) {
    const t = T0 + y;
    if (t < 0) { px32.fill(pal.antes, i, i + W); i += W; continue; }
    const futuro = y > yAhora;
    for (let x = 0; x < W; x++, i++) {
      let idx = 0, fuera = 0;
      for (let c = 0; c < nC; c++) { const v = capas[c][i]; if (v === FUERA) { if (!ach[c]) fuera++; } else idx += v * mult[c]; }
      // fuera del cono de toda la tinta: el país todavía no llega aquí
      if (fuera === nTinta) { px32[i] = pal.antes; continue; }
      let tabla;
      if (y < yAhora) tabla = pal.pasado;
      else if (futuro) tabla = pal.futuro;
      else tabla = x < cabeza ? pal.fresco : pal.futuro;
      // ¿cae sobre una recta de algún campo?
      let rectas = 0;
      const X = X0 + x;
      for (let k = 0; k < campos.length; k++) {
        const c = campos[k], v = capas[c][i];
        if (v === FUERA) continue;
        const d = ach[c][v];
        if (d && modp(d.a * X + d.b * t, d.s) === 0) rectas++;
      }
      if (vida && tabla !== pal.futuro) {
        const j = i + SEDIMENTO * W, a = vida[j];
        if (a) { px32[i] = pal.vida[Math.min(7, Math.floor((8 * (a - 1)) / A))]; continue; }
        // sedimento: viva hace k filas, ahora no; sólo donde no hay trama encima
        if (!idx || !rectas) {
          let k = 1;
          while (k <= SEDIMENTO && !vida[j - k * W]) k++;
          if (k <= SEDIMENTO) { px32[i] = pal.sedimento[k]; continue; }
        }
      }
      px32[i] = rectas ? (tabla === pal.futuro ? pal.rayaFutura : pal.raya)[Math.min(rectas, 2) * pal.estados + idx] : tabla[idx];
    }
  }
  if (yAhora >= 0 && yAhora < H && cabeza < W) px32[yAhora * W + cabeza] = pal.cabeza;
}

// El árbol de una celda (X, t): las celdas del pasado cuyo valor llega a ella.
// En una ley lineal eso es exacto: (x', t') llega si el coeficiente de f^(t-t')
// en x-x' no es cero. Por capa de tinta, a su escala: un Sierpinski invertido
// que converge en la celda. Devuelve por celda de la ventana la capa más fina
// que llega (1…), o 0.
export function mascaraArbol(mundo, X, t, X0, T0, W, H) {
  const m = new Uint8Array(W * H);
  mundo.capas.forEach((c, k) => {
    if (c.papel !== 'tinta') return;
    const e = c.escala, xn = Math.floor(X / e), tn = Math.floor(t / e);
    for (let y = 0; y < H; y++) {
      const tc = Math.floor((T0 + y) / e), dt = tn - tc;
      if (dt < 0 || T0 + y < 0) continue;
      for (let x = 0; x < W; x++) {
        const i = y * W + x;
        if (m[i]) continue;
        const dx = xn - Math.floor((X0 + x) / e);
        if (dx > dt || dx < -dt) continue;
        if (coef(c, dt, dx)) m[i] = k + 1;
      }
    }
  });
  return m;
}

// revelado 0…1: hasta dónde bajó (desde arriba de la ventana hasta la celda);
// fase: la onda que sigue bajando. cy = fila de la celda en la ventana.
export function pintarArbol(px32, m, pal, W, H, cy, revelado, fase) {
  const yMax = Math.min(H - 1, cy);
  const yRev = Math.floor(yMax * revelado);
  for (let y = 0; y <= yRev; y++) {
    const d = cy - y;                                 // distancia hacia arriba
    const onda = ((d / 36 + fase) % 1 + 1) % 1;       // la onda baja con la fase
    const borde = y > yRev - 3 && revelado < 1;       // el frente que va bajando
    const n = borde ? 4 : onda < 0.08 ? 4 : onda < 0.2 ? 2 : 1;
    for (let x = 0; x < W; x++) {
      const i = y * W + x, k = m[i];
      if (!k) continue;
      // translúcido: mitad árbol, mitad lo que había; la onda va a luz plena
      const c = pal.arbol[k - 1][n];
      px32[i] = n === 4 ? c : ((((px32[i] & 0xfefefe) >>> 1) + ((c & 0xfefefe) >>> 1)) | 0xff000000) >>> 0;
    }
  }
}
