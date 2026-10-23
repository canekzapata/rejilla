// foto.mjs — una vista del país a PNG crudo, con el mismo pintor que la página.
// node foto.mjs salida.rgba <x|orilla> <t|ahora> <columnas> <filas> [cabeza 0..1]
// Escribe RGBA crudo; rgba2png.py lo convierte (y amplía por celda).
import { writeFileSync } from 'node:fs';
import { crearMundo, ventana, genAhora, orilla } from './motor.js';
import { crearPaleta, SEDIMENTO } from './color.js';
import { vidaVentana, REGLA_VIDA } from './vida.js';
import { crearAchurado, pintar } from './pintar.js';
import { TEXTO_FUNDADOR, SEMILLA } from './fundador.js';

const [, , salida, xs = 'orilla', ts = 'ahora', ws = '427', hs = '240', cs = '1'] = process.argv;
const mundo = crearMundo({ semilla: SEMILLA, texto: TEXTO_FUNDADOR });
const pal = crearPaleta(mundo), ach = crearAchurado(mundo);
const W = +ws, H = +hs;
const g = ts === 'ahora' ? genAhora() : +ts;
pal.rehacer(g);
const yAhora = Math.floor(H * 0.62);
const T0 = Math.floor(g) - yAhora;
const X = xs === 'orilla' ? orilla(mundo, g)[1] - Math.floor(W * 0.3) : +xs;
const X0 = X - Math.floor(W / 2);
const px32 = new Uint32Array(W * H);
pintar({ mundo, pal, ach, datos: ventana(mundo, X0, T0, W, H), X0, T0, W, H, px32, yAhora, vida: vidaVentana(mundo, REGLA_VIDA, X0, T0 - SEDIMENTO, W, H + SEDIMENTO), A: REGLA_VIDA.A, cabeza: Math.floor(+cs * W) });
writeFileSync(salida, Buffer.from(px32.buffer));
console.log(W, H, `x=${X} t=${Math.floor(g)}`);
