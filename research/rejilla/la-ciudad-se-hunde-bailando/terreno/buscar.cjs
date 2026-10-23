// Busca semillas de Traspuesta que salen CAMPO DE CONOS por su propio sorteo (franja 0.14–0.18) y cuenta sus conos.
//   node terreno/buscar.cjs [cuantas]
const path = require('path'), M = path.join(__dirname, '../../../montanas-topograficas/');
for (const f of ['nucleo', 'terreno', 'idioma', 'letra', 'vistas', 'toponimia/glosario', 'toponimia/nombrar', 'lamina']) require(M + f + '.js');
const quiero = +(process.argv[2] || 25), out = [];
for (let s = 1, k = 0; k < quiero && s < 40000; s++) {
  const rv = MT.rng(s + ':arq2')(); if (!(rv >= 0.14 && rv < 0.18)) continue; k++;
  const T = MT.terreno(String(s), {}); let nom = [];
  try { nom = MT.nombra(T, String(s), 0).filter(n => n.clase === 'cumbre'); } catch (e) {}
  out.push([s, T.nombre, T.relieve, T.anchoKm, nom.length, nom.slice(0, 4).map(n => n.nombre || n.texto).join(' | ')]);
}
for (const o of out) console.log(JSON.stringify(o));
