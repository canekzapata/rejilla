// Mide candidatos de atolón: islotes (motus) sobre el anillo, en ángulo, y los pasos.   node terreno/inspeccionar.cjs s1 s2 …
const path = require('path'), M = path.join(__dirname, '../../../montanas-topograficas/');
for (const f of ['nucleo', 'terreno', 'idioma', 'letra', 'vistas', 'toponimia/glosario', 'toponimia/nombrar', 'lamina']) require(M + f + '.js');
for (const s of process.argv.slice(2)) {
  const T = MT.terreno(s, {}); const G = T.G; let cx = 0, cy = 0, n = 0;
  for (let i = 0; i < G * G; i++) if (T.h[i] > T.umbralMar) { cx += i % G; cy += Math.floor(i / G); n++; }
  cx /= n; cy /= n; const B = 720, arco = new Array(B).fill(0);
  for (let i = 0; i < G * G; i++) if (T.h[i] > T.umbralMar) { const a = Math.atan2(Math.floor(i / G) - cy, i % G - cx); arco[Math.floor((a + Math.PI) / (2 * Math.PI) * B) % B] = 1; }
  let seg = 0; for (let k = 0; k < B; k++) if (arco[k] && !arco[(k + B - 1) % B]) seg++;
  const tierra = arco.reduce((a, b) => a + b, 0) / B;
  console.log(s, T.arq, T.nombre || '', 'G', G, 'tierra', n, 'islotes(arco)', seg, 'cubre', tierra.toFixed(2), 'esp', JSON.stringify((T.especiales || []).map(e => e.term || e.tipo)).slice(0, 80));
}
