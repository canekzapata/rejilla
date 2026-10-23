// vida.js — la vida olvida.
//
// Sobre la ley exacta corre un autómata NO lineal: una mancha que nace donde
// hay trama (comida), se extiende y se apaga. Sólo se muestra arriba del presente.
//
// Primer intento (descartado, ver LOOP_STATE): una vida con edad que arrancaba
// vacía cada tramo de 128 generaciones. En 4 lugares parecía olvidar al 100 %;
// en lugares al azar olvidaba al 89 % y ni con 512 de memoria llegaba al 99 %:
// quedaban costuras. Olvidar no se le puede pedir a una regla: hay que construirlo.
//
// Ahora la vida tiene LINAJE. Cada chispa (la comida con cierta forma) abre un
// linaje; la capa g de un linaje en t sólo depende de la capa g-1 en t-1:
//   E₀(x,t) = chispa(comida alrededor de x en t)
//   E_g(x,t) = regla(cuántas de E_{g-1} hay en x-2…x+2 en t-1, comida(x,t))
// y nada pasa de la capa G. Una celda está viva si algún linaje la tocó en las
// últimas A generaciones. Así la vida en (x,t) depende EXACTAMENTE de la comida
// en [t-G-A, t] y [x-2G-2, x+2G+2]: cualquier ventana la calcula igual, sin
// tramos ni costuras, como la ley.
import { ventana, FUERA } from './motor.js';

const R = 2; // radio: x-2…x+2

// regla: { chispa: cuánta comida vecina (0…4) enciende un linaje,
//          nace: máscara de n (0…5) con comida, naceSola: sin comida,
//          G: hasta qué capa llega un linaje, A: cuánto dura encendida una celda }
// La regla del mundo, elegida en el loop 02: de 3000 al azar, 8 intervenían
// (comen 25-75 % de la trama, 25-70 % de su vida cae fuera, se mueven); entre
// ésas, a ojo, la que tiende puentes sobre el desierto. Se come el 45 % de la
// trama, el 67 % de su vida está fuera de ella, cambio entre filas 0.24.
export const REGLA_VIDA = { chispa: 4, nace: 48, naceSola: 12, G: 19, A: 1 };

export function memoria(regla) { return regla.G + regla.A; }

// comida = alguna capa de tinta viva en la celda
function mascaraComida(mundo, datos, n) {
  const m = new Uint8Array(n);
  mundo.capas.forEach((c, k) => {
    if (c.papel !== 'tinta') return;
    const d = datos[k];
    for (let i = 0; i < n; i++) if (d[i] && d[i] !== FUERA) m[i] = 1;
  });
  return m;
}

// Vida de una ventana W×H desde (X0, T0). Valor: 0 = nada; 1…A = cuántas
// generaciones hace que un linaje tocó la celda (1 = ahora mismo).
// `extra` (sólo para pruebas): arrancar antes y con más margen; debe dar lo mismo.
export function vidaVentana(mundo, regla, X0, T0, W, H, out, extra = 0) {
  const { chispa, nace, naceSola, G, A } = regla;
  const o = out && out.length === W * H ? out : new Uint8Array(W * H);
  o.fill(0);
  const tFin = T0 + H - 1;
  if (tFin < 0) return o;
  const inicio = Math.max(0, T0 - G - A - extra);
  const margen = R * G + R + extra;
  const ancho = W + 2 * margen;
  const alto = tFin - inicio + 1;
  const comida = mascaraComida(mundo, ventana(mundo, X0 - margen, inicio, ancho, alto), ancho * alto);
  // capas de linaje: E[g] en el paso anterior, F[g] en el actual
  let E = Array.from({ length: G + 1 }, () => new Uint8Array(ancho));
  let F = Array.from({ length: G + 1 }, () => new Uint8Array(ancho));
  const ultimo = new Float64Array(ancho).fill(-1e12); // última vez que un linaje tocó la celda
  for (let t = inicio; t <= tFin; t++) {
    const c = comida.subarray((t - inicio) * ancho, (t - inicio + 1) * ancho);
    const F0 = F[0];
    for (let i = R; i < ancho - R; i++) {
      F0[i] = c[i] && c[i - 2] + c[i - 1] + c[i + 1] + c[i + 2] === chispa ? 1 : 0;
    }
    for (let g = 1; g <= G; g++) {
      const a = E[g - 1], b = F[g];
      for (let i = R; i < ancho - R; i++) {
        const n = a[i - 2] + a[i - 1] + a[i] + a[i + 1] + a[i + 2];
        b[i] = ((c[i] ? nace : naceSola) >> n) & 1;
      }
    }
    for (let g = 0; g <= G; g++) {
      const b = F[g];
      for (let i = R; i < ancho - R; i++) if (b[i]) ultimo[i] = t;
    }
    const tmp = E; E = F; F = tmp;
    if (t >= T0) {
      const base = (t - T0) * W;
      for (let x = 0; x < W; x++) {
        const d = t - ultimo[x + margen];
        if (d < A) o[base + x] = d + 1;
      }
    }
  }
  return o;
}
