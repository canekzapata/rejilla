// color.js — el color se deriva de la semilla y de la hora; nunca hay hex.
// Una tabla por zona (pasado, presente recién escrito, futuro) indexada por
// el estado conjunto de las capas. Se rehace cada segundo: el tono deriva.
import { rngDe } from './motor.js';

export const SEDIMENTO = 12; // filas que tarda en borrarse lo que murió

function oklabALineal(L, a, b) {
  const l_ = L + 0.3963377774 * a + 0.2158037573 * b;
  const m_ = L - 0.1055613458 * a - 0.0638541728 * b;
  const s_ = L - 0.0894841775 * a - 1.291485548 * b;
  const l = l_ ** 3, m = m_ ** 3, s = s_ ** 3;
  return [
    4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
    -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
    -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s,
  ];
}
const gamma = (x) => (x <= 0.0031308 ? 12.92 * x : 1.055 * Math.pow(x, 1 / 2.4) - 0.055);
const dentro = (c) => c.every((v) => v >= -1e-4 && v <= 1 + 1e-4);

// OKLCh → sRGB; si se sale del gamut se baja el croma (bisección), no se recorta
export function oklch(L, C, hGrados) {
  const h = (hGrados * Math.PI) / 180;
  let lin = oklabALineal(L, C * Math.cos(h), C * Math.sin(h));
  if (!dentro(lin)) {
    let lo = 0, hi = C;
    for (let i = 0; i < 18; i++) {
      const m = (lo + hi) / 2;
      if (dentro(oklabALineal(L, m * Math.cos(h), m * Math.sin(h)))) lo = m; else hi = m;
    }
    lin = oklabALineal(L, lo * Math.cos(h), lo * Math.sin(h));
  }
  return lin.map((v) => Math.round(255 * Math.min(1, Math.max(0, gamma(Math.max(0, v))))));
}
const empaca = ([r, g, b]) => ((255 << 24) | (b << 16) | (g << 8) | r) >>> 0;

// Las capas finas son tintas: un tono propio que deriva con la hora; sus
// valores (1…p-1) mueven poco el tono y más la luz. Donde dos tramas se enciman
// las tintas se mezclan en OKLab y la luz sube, como serigrafía.
// Las capas enormes son el papel: tiñen el fondo por regiones, en oscuro.
export function crearPaleta(mundo) {
  const r = rngDe('color|' + mundo.semilla);
  const h0 = r() * 360;
  const tintas = mundo.capas.map((c, i) => ({
    h: h0 + 137.5 * i + (r() - 0.5) * 40,
    vuelta: (r() < 0.5 ? -1 : 1) * (8 + r() * 14),  // cuánto gira el tono por valor
    C: c.papel === 'campo' ? 0.04 + r() * 0.035 : 0.11 + r() * 0.07,
  }));
  const frio = h0 + 150 + r() * 60;           // el futuro vive del otro lado del círculo
  const ciclo = 86400 * (2 + r() * 3);        // una vuelta de tono cada 2-5 días
  const N = mundo.estados;
  const z = { pasado: new Uint32Array(N), fresco: new Uint32Array(N), futuro: new Uint32Array(N), antes: 0, cabeza: 0, estados: N,
    // rectas del achurado: [n·N + idx], n = cuántas rectas se cruzan (1 o 2)
    raya: new Uint32Array(3 * N), rayaFutura: new Uint32Array(3 * N),
    // vida: 8 tonos por edad (joven → vieja) y el sedimento que deja al morir
    vida: new Uint32Array(8), sedimento: new Uint32Array(SEDIMENTO + 1) };
  // la vida no es ninguna de las tintas: el tono más lejano de todas (de 5° en 5°)
  let hVida = 0, lejos = -1;
  for (let h = 0; h < 360; h += 5) {
    const d = Math.min(...tintas.filter((t, i) => mundo.capas[i].papel === 'tinta').map((t) => Math.abs((((h - t.h) % 360) + 540) % 360 - 180)));
    if (d > lejos) { lejos = d; hVida = h; }
  }

  function mezcla(idx, deriva) {
    let resto = idx, vivas = 0, sa = 0, sb = 0, sL = 0, pa = 0, pb = 0, campos = 0;
    mundo.capas.forEach((c, i) => {
      const v = resto % c.p; resto = Math.floor(resto / c.p);
      if (!v) return;
      const k = c.p > 2 ? (v - 1) / (c.p - 2) : 1;     // 0…1 dentro de la capa
      const t = tintas[i];
      const h = ((t.h + deriva + t.vuelta * (v - 1)) * Math.PI) / 180;
      const C = t.C * (0.75 + 0.35 * k);
      if (c.papel === 'campo') { pa += C * Math.cos(h); pb += C * Math.sin(h); campos++; return; }
      sa += C * Math.cos(h); sb += C * Math.sin(h); sL += 0.5 + 0.16 * k;
      vivas++;
    });
    const fondo = { L: 0.12 + 0.07 * campos, a: pa, b: pb };
    if (!vivas) return { L: fondo.L, a: fondo.a, b: fondo.b, vivas, campos };
    // la tinta se tiñe un poco del papel en el que cae
    const a = sa / vivas + 0.25 * pa, b = sb / vivas + 0.25 * pb;
    return { L: Math.min(0.95, sL / vivas + 0.11 * (vivas - 1) + 0.03 * campos), a, b, vivas, campos };
  }
  const lch = (L, a, b) => oklch(L, Math.hypot(a, b), (Math.atan2(b, a) * 180) / Math.PI);

  function rehacer(g) {
    const deriva = (360 * g) / ciclo;
    for (let idx = 0; idx < N; idx++) {
      const m = mezcla(idx, deriva);
      z.pasado[idx] = empaca(lch(m.L, m.a, m.b));
      z.fresco[idx] = empaca(lch(Math.min(0.97, m.L + 0.16), m.a * 1.25, m.b * 1.25));
      // el futuro: la misma ley, apagada y fría
      const hf = ((frio + deriva) * Math.PI) / 180;
      const Cf = 0.015 + 0.012 * m.vivas + 0.006 * m.campos;
      const Lf = 0.085 + 0.07 * m.vivas + 0.03 * m.campos, af = Cf * Math.cos(hf) + 0.1 * m.a, bf = Cf * Math.sin(hf) + 0.1 * m.b;
      z.futuro[idx] = empaca(lch(Lf, af, bf));
      // la recta es el papel con más luz y más croma; bajo la tinta no se ve
      for (let n = 1; n <= 2; n++) {
        z.raya[n * N + idx] = m.vivas ? z.pasado[idx] : empaca(lch(m.L + 0.17 * n, m.a * (1.8 + 0.6 * n), m.b * (1.8 + 0.6 * n)));
        z.rayaFutura[n * N + idx] = m.vivas ? z.futuro[idx] : empaca(lch(Lf + 0.05 * n, af * 1.3, bf * 1.3));
      }
    }
    for (let k = 0; k < 8; k++) z.vida[k] = empaca(oklch(0.9 - 0.055 * k, 0.17 - 0.008 * k, hVida + deriva * 1.7 - 9 * k));
    for (let k = 1; k <= SEDIMENTO; k++) z.sedimento[k] = empaca(oklch(0.34 - 0.017 * k, 0.07 - 0.004 * k, hVida + deriva * 1.7 + 40));
    // el color de cada capa para la página (la genealogía pinta las letras con él)
    z.colorCapa = mundo.capas.map((c, i) => {
      const t = tintas[i], campo = c.papel === 'campo';
      const [r, g, b] = oklch(campo ? 0.72 : 0.78, campo ? 0.09 : t.C * 1.2, t.h + deriva);
      return `rgb(${r} ${g} ${b})`;
    });
    // el árbol de una celda: por capa, 5 luces (0 = apenas, 4 = la onda que baja)
    z.arbol = mundo.capas.map((c, i) => Array.from({ length: 5 }, (_, n) =>
      empaca(oklch(0.42 + 0.13 * n, 0.07 + 0.025 * n, tintas[i].h + deriva))));
    z.colorVida = (([r, g, b]) => `rgb(${r} ${g} ${b})`)(oklch(0.88, 0.12, hVida + deriva * 1.7));
    z.antes = empaca(oklch(0.04, 0.006, frio + deriva));
    z.cabeza = empaca(oklch(0.97, 0.05, h0 + deriva + 90));
  }
  z.rehacer = rehacer;
  return z;
}
