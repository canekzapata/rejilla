// vida-hoja.mjs — las reglas candidatas lado a lado, en la orilla y tierra adentro.
// node vida-hoja.mjs salida.rgba '[regla, regla, …]'
import { writeFileSync } from 'node:fs';
import { crearMundo, ventana, genAhora, orilla } from './motor.js';
import { crearPaleta, SEDIMENTO } from './color.js';
import { crearAchurado, pintar } from './pintar.js';
import { vidaVentana } from './vida.js';
import { TEXTO_FUNDADOR, SEMILLA } from './fundador.js';

const reglas = JSON.parse(process.argv[3]);
const mundo = crearMundo({ semilla: SEMILLA, texto: TEXTO_FUNDADOR });
const pal = crearPaleta(mundo), ach = crearAchurado(mundo);
const g = Math.floor(genAhora());
pal.rehacer(g);
const W = 260, H = 150, G = 4;
const sitios = [orilla(mundo, g)[1] - 200, -300000, orilla(mundo, g)[1] - 1500];
const AW = sitios.length * (W + G) + G, AH = reglas.length * (H + G) + G;
const px = new Uint32Array(AW * AH);
reglas.forEach((regla, f) => sitios.forEach((X, c) => {
  const X0 = X - W / 2, yA = Math.floor(H * 0.75), T0 = g - yA;
  const tile = new Uint32Array(W * H);
  const vida = vidaVentana(mundo, regla, X0, T0 - SEDIMENTO, W, H + SEDIMENTO);
  pintar({ mundo, pal, ach, datos: ventana(mundo, X0, T0, W, H), X0, T0, W, H, px32: tile, yAhora: yA, cabeza: W, vida, A: regla.A });
  const ox = G + c * (W + G), oy = G + f * (H + G);
  for (let y = 0; y < H; y++) px.set(tile.subarray(y * W, y * W + W), (oy + y) * AW + ox);
}));
writeFileSync(process.argv[2], Buffer.from(px.buffer));
console.log(AW, AH);
