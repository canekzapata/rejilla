// vida-experimento.mjs — busca reglas de vida (con linaje) que INTERVENGAN:
// que se coman parte de la trama, salgan de ella, se muevan, y no tapen todo.
// El olvido ya no se mide: con linaje es exacto por construcción (pruebas.mjs).
// node vida-experimento.mjs [n reglas] [semilla de la búsqueda]
import { crearMundo, ventana, genAhora, orilla, rngDe, FUERA } from './motor.js';
import { vidaVentana } from './vida.js';
import { TEXTO_FUNDADOR, SEMILLA } from './fundador.js';

const mundo = crearMundo({ semilla: SEMILLA, texto: TEXTO_FUNDADOR });
const ahora = Math.floor(genAhora());
const r = rngDe('vida-experimento|' + (process.argv[3] || ''));
const N = +(process.argv[2] || 60);
const W = 200, H = 100;

const rl = rngDe('lugares');
const lugares = Array.from({ length: 8 }, () => {
  const T = ahora - Math.floor(rl() * 60000);
  return [orilla(mundo, T)[1] - 150 - Math.floor(rl() * 4000), T];
});
const comidas = lugares.map(([X, T]) => {
  const d = ventana(mundo, X, T, W, H), m = new Uint8Array(W * H);
  mundo.capas.forEach((c, k) => { if (c.papel === 'tinta') for (let i = 0; i < m.length; i++) if (d[k][i] && d[k][i] !== FUERA) m[i] = 1; });
  return m;
});

function medir(regla) {
  let vivas = 0, comida = 0, come = 0, fuera = 0, cambio = 0, cambioN = 0, vacios = 0;
  for (const [k, [X, T]] of lugares.entries()) {
    const a = vidaVentana(mundo, regla, X, T, W, H), c = comidas[k];
    let v = 0;
    for (let i = 0; i < a.length; i++) {
      if (c[i]) { comida++; if (a[i]) come++; }
      if (a[i]) { v++; if (!c[i]) fuera++; }
      if (i >= W) { if (!a[i] !== !a[i - W]) cambio++; cambioN++; }
    }
    vivas += v; if (v < W * H * 0.02) vacios++;
  }
  return { come: come / comida, fuera: vivas ? fuera / vivas : 0, cob: vivas / (W * H * lugares.length), act: cambio / cambioN, vacios };
}

const sirven = [];
for (let i = 0; i < N; i++) {
  const regla = {
    chispa: Math.floor(r() * 5),
    nace: Math.floor(r() * 64) & ~1,
    naceSola: Math.floor(r() * 64) & ~1 & ~2, // sin comida no basta una sola vecina
    G: 6 + Math.floor(r() * 34),
    A: 1 + Math.floor(r() * 10),
  };
  const m = medir(regla);
  if (m.come > 0.25 && m.come < 0.75 && m.fuera > 0.25 && m.fuera < 0.7 && m.act > 0.05 && m.vacios <= 2) sirven.push({ regla, ...m });
}
const f = (v) => v.toFixed(3);
console.log(`${sirven.length} de ${N} reglas intervienen`);
for (const x of sirven.sort((a, b) => b.act - a.act).slice(0, 14))
  console.log(JSON.stringify(x.regla), 'come', f(x.come), 'fuera', f(x.fuera), 'cob', f(x.cob), 'act', f(x.act), 'vacíos', x.vacios);
