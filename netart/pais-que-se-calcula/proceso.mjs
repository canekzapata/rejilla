// proceso.mjs — cuadros del GIF: la orilla de hoy mientras el presente se
// escribe, acelerado (3 cuadros por generación en vez de un segundo).
// node proceso.mjs carpeta  → carpeta/000.rgba … y una línea "W H N"
import { writeFileSync, mkdirSync } from 'node:fs';
import { crearMundo, ventana, genAhora, orilla } from './motor.js';
import { crearPaleta, SEDIMENTO } from './color.js';
import { vidaVentana, REGLA_VIDA } from './vida.js';
import { crearAchurado, pintar } from './pintar.js';
import { TEXTO_FUNDADOR, SEMILLA } from './fundador.js';

const dir = process.argv[2];
const g0 = process.argv[3] ? +process.argv[3] : Math.floor(genAhora());
mkdirSync(dir, { recursive: true });
const mundo = crearMundo({ semilla: SEMILLA, texto: TEXTO_FUNDADOR });
const pal = crearPaleta(mundo), ach = crearAchurado(mundo);
const W = 300, H = 170, POR_GEN = 3, N = 120;
const yAhora = Math.floor(H * 0.62);
const px32 = new Uint32Array(W * H);
for (let k = 0; k < N; k++) {
  const g = g0 + k / POR_GEN;
  pal.rehacer(g);
  const T0 = Math.floor(g) - yAhora;
  const X0 = orilla(mundo, g)[1] - Math.floor(W * 0.3) - Math.floor(W / 2);
  pintar({ mundo, pal, ach, datos: ventana(mundo, X0, T0, W, H), X0, T0, W, H, px32, yAhora, vida: vidaVentana(mundo, REGLA_VIDA, X0, T0 - SEDIMENTO, W, H + SEDIMENTO), A: REGLA_VIDA.A, cabeza: Math.floor((g - Math.floor(g)) * W) });
  writeFileSync(`${dir}/${String(k).padStart(3, '0')}.rgba`, Buffer.from(px32.buffer));
}
console.log(W, H, N, g0);
