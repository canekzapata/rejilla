// muestras.mjs — hoja de contactos: el mundo en muchos lugares y tiempos.
// node muestras.mjs salida.rgba  → escribe crudo RGBA + ancho/alto en stdout
import { writeFileSync } from 'node:fs';
import { crearMundo, ventana, genAhora, genDeMs, orilla, FUERA, rngDe } from './motor.js';
import { crearPaleta } from './color.js';
import { crearAchurado, pintar } from './pintar.js';
import { TEXTO_FUNDADOR, SEMILLA } from './fundador.js';

const semilla = process.argv[3] || SEMILLA;
const mundo = crearMundo({ semilla, texto: TEXTO_FUNDADOR });
const pal = crearPaleta(mundo);
const ach = crearAchurado(mundo);
const ahora = Math.floor(genAhora());
pal.rehacer(ahora);
const W = 200, H = 120, COLS = 4, FILAS = 4, G = 4;
const r = rngDe('muestras|' + semilla);
// tiempos: primeros minutos, primer día, hoy, dentro de un año, 3026; lugares al azar dentro de la orilla
const tiempos = [600, 3000, 40000, ahora, ahora, ahora, ahora, ahora, Math.floor(genDeMs(Date.UTC(2027, 9, 2, 6))), Math.floor(genDeMs(Date.UTC(2027, 9, 2, 6))), Math.floor(genDeMs(Date.UTC(3026, 9, 2, 6))), Math.floor(genDeMs(Date.UTC(3026, 9, 2, 6)))];
const lugares = [];
for (const t of tiempos) { const [a, b] = orilla(mundo, t); lugares.push([Math.floor(a + r() * (b - a)), t]); }
lugares[3][0] = 0; // hoy, en la primera letra
lugares.push([orilla(mundo, ahora)[1] - W / 2, ahora]);  // hoy, en la orilla derecha
lugares.push([orilla(mundo, ahora)[0] - W / 2, ahora]);  // hoy, en la orilla izquierda
lugares.push([-W / 2, 1]);                                // el nacimiento
lugares.push([Math.floor(ahora * 0.37), ahora]);
const AW = COLS * W + (COLS + 1) * G, AH = FILAS * H + (FILAS + 1) * G;
const px = new Uint32Array(AW * AH);
lugares.slice(0, COLS * FILAS).forEach(([X0, T0], k) => {
  const v = ventana(mundo, X0, T0 - Math.floor(H * 0.62), W, H);
  const ox = G + (k % COLS) * (W + G), oy = G + Math.floor(k / COLS) * (H + G);
  const tile = new Uint32Array(W * H);
  pintar({ mundo, pal, ach, datos: v, X0, T0: T0 - Math.floor(H * 0.62), W, H, px32: tile, yAhora: Math.floor(H * 0.62), cabeza: W });
  for (let y = 0; y < H; y++) px.set(tile.subarray(y * W, y * W + W), (oy + y) * AW + ox);
});
writeFileSync(process.argv[2], Buffer.from(px.buffer));
console.log(AW, AH, mundo.capas.map(c => `p${c.p}(${c.cl}${c.cc}${c.cr})x${c.escala}`).join(' '));
