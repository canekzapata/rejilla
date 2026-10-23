// Cuenta las mesas separadas (componentes de h > umbral) de las láminas de tepuyes.   node terreno/contar.cjs [cuantas] [umbral]
const path = require('path'), M = path.join(__dirname, '../../../montanas-topograficas/');
for (const f of ['nucleo', 'terreno']) require(M + f + '.js');
const quiero = +(process.argv[2] || 60), U = +(process.argv[3] || .5), out = [];
for (let s = 1, k = 0; k < quiero && s < 40000; s++) {
  const rv = MT.rng(s + ':arq2')(); if (!(rv >= 0.915 && rv < 0.93)) continue; k++;
  const T = MT.terreno(String(s), { agua: false }), G = T.G, h = T.h, vis = new Uint8Array(G * G), comps = [];
  for (let i = 0; i < G * G; i++) if (!vis[i] && h[i] > U) {
    let n = 0, st = [i]; vis[i] = 1; let toca = false;
    while (st.length) { const j = st.pop(); n++; const x = j % G, y = (j / G) | 0; if (x === 0 || y === 0 || x === G - 1 || y === G - 1) toca = true;
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const a = x + dx, b = y + dy; if (a < 0 || b < 0 || a >= G || b >= G) continue; const q = b * G + a; if (!vis[q] && h[q] > U) { vis[q] = 1; st.push(q); } } }
    if (n > 600) comps.push([n, toca]);
  }
  const libres = comps.filter(c => !c[1]).length;
  if (comps.length >= 3) out.push([s, T.relieve, T.anchoKm, comps.length, libres, comps.map(c => c[0])]);
}
console.log(JSON.stringify(out));
