// arbol-gif.mjs — cuadros del GIF de la genealogía: se toca una celda en la
// orilla y su árbol baja hasta ella (1.6 s) y luego lo recorre la onda.
// node arbol-gif.mjs carpeta [generación]
import { writeFileSync, mkdirSync } from 'node:fs';
import { crearMundo, ventana, genAhora, orilla, genealogia } from './motor.js';
import { crearPaleta, SEDIMENTO } from './color.js';
import { crearAchurado, pintar, mascaraArbol, pintarArbol } from './pintar.js';
import { vidaVentana, REGLA_VIDA } from './vida.js';
import { TEXTO_FUNDADOR, SEMILLA } from './fundador.js';

const dir = process.argv[2];
const g = process.argv[3] ? +process.argv[3] : Math.floor(genAhora());
mkdirSync(dir, { recursive: true });
const mundo = crearMundo({ semilla: SEMILLA, texto: TEXTO_FUNDADOR });
const pal = crearPaleta(mundo), ach = crearAchurado(mundo);
pal.rehacer(g);
const W = 300, H = 170, FPS = 15, N = 66;
const yAhora = Math.floor(H * 0.62), T0 = g - yAhora;
const X0 = orilla(mundo, g)[1] - Math.floor(W * 0.3) - Math.floor(W / 2);
// la celda: unas filas arriba del presente, la primera con letras en la trama
let sel = null;
for (let x = Math.floor(W * 0.55); x > 20 && !sel; x--) {
  const X = X0 + x, t = g - 6;
  if (genealogia(mundo, X, t).some((c) => c.papel === 'tinta' && c.letras.length && c.valor)) sel = { X, t };
}
const datos = ventana(mundo, X0, T0, W, H);
const vida = vidaVentana(mundo, REGLA_VIDA, X0, T0 - SEDIMENTO, W, H + SEDIMENTO);
const base = new Uint32Array(W * H);
pintar({ mundo, pal, ach, datos, X0, T0, W, H, px32: base, yAhora, cabeza: W, vida, A: REGLA_VIDA.A });
const arbol = mascaraArbol(mundo, sel.X, sel.t, X0, T0, W, H);
const px = new Uint32Array(W * H);
for (let k = 0; k < N; k++) {
  const s = k / FPS - 0.3; // un respiro antes del toque
  px.set(base);
  if (s >= 0) {
    pintarArbol(px, arbol, pal, W, H, sel.t - T0, Math.min(1, s / 1.6), s * 0.5);
    const cx = sel.X - X0, cy = sel.t - T0;
    for (const [dx, dy] of [[0, 0], [-2, 0], [2, 0], [0, -2], [0, 2]]) px[(cy + dy) * W + cx + dx] = pal.cabeza;
  }
  writeFileSync(`${dir}/${String(k).padStart(3, '0')}.rgba`, Buffer.from(px.buffer));
}
console.log(W, H, N, `x=${sel.X} t=${sel.t}`);
