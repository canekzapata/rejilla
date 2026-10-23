// Busca semillas de Traspuesta que salen TIERRAS MALAS por su propio sorteo (franja 0.99–1.01) y mide su cauce principal.
//   node terreno/buscar.cjs [cuantas]
const path = require('path'), M = path.join(__dirname, '../../../montanas-topograficas/');
for (const f of ['nucleo', 'terreno', 'idioma', 'letra', 'vistas', 'toponimia/glosario', 'toponimia/nombrar', 'lamina']) require(M + f + '.js');
const quiero = +(process.argv[2] || 12);
for (let s = 1, k = 0; k < quiero && s < 60000; s++) {
  const rv = MT.rng(s + ':arq2')(); if (!(rv >= 0.99 && rv < 1.01)) continue; k++;
  const T = MT.terreno(String(s), {}); const pr = T.hidro && T.hidro.principal; const rios = (T.hidro && T.hidro.rios) || [];
  let nom = []; try { nom = MT.nombra(T, String(s), 0).slice(0, 5).map(n => n.nombre || n.texto); } catch (e) {}
  console.log(JSON.stringify([s, T.nombre, T.relieve, T.anchoKm, pr ? pr.pts.length : 0, rios.length, nom.join(' | ')]));
}
