// Busca semillas de Traspuesta que salen ATOLÓN (no arrecife de barrera) por sorteo propio, sin forzar el arquetipo.
//   node terreno/buscar_atolon.cjs [hasta]
const path = require('path'), M = path.join(__dirname, '../../../montanas-topograficas/');
for (const f of ['nucleo', 'terreno']) require(M + f + '.js');
const hasta = +(process.argv[2] || 20000), out = [];
for (let s = 1; s <= hasta && out.length < 40; s++) {
  const rv = MT.rng(s + ':arq2')(); if (!(rv >= 0.85 && rv < 0.865)) continue;
  const rf = MT.rng(s + ':terreno:atolon'); const barrera = rf() < 0.4; if (barrera) continue;
  rf(); rf(); rf(); rf(); rf(); const npasos = rf.int ? null : null;
  out.push(s);
}
console.log(JSON.stringify(out));
