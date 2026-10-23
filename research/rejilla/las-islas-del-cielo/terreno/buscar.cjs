// Busca semillas de Traspuesta por su propio sorteo: tepuyes (franja 0.915–0.93) y mesas (clásico «mesa»), sin forzar el arquetipo.
//   node terreno/buscar.cjs [hasta]
const path = require('path'), M = path.join(__dirname, '../../../montanas-topograficas/');
for (const f of ['nucleo', 'terreno', 'idioma', 'letra', 'vistas', 'toponimia/glosario', 'toponimia/nombrar', 'lamina']) require(M + f + '.js');
const hasta = +(process.argv[2] || 4000), tep = [], mesa = [];
for (let s = 1; s <= hasta && (tep.length < 12 || mesa.length < 4); s++) {
  const rv = MT.rng(s + ':arq2')();
  if (rv >= 0.915 && rv < 0.93 && tep.length < 12) { const T = MT.terreno(String(s), {}); tep.push([s, T.arq, T.nombre, T.relieve, T.anchoKm]); }
  else if (mesa.length < 4 && !(rv >= 0.36 && rv < 0.69) && rv >= 0.36) { const T = MT.terreno(String(s), { agua: false }); if (T.arq === 'mesa') mesa.push([s, T.nombre, T.relieve]); }
}
console.log('tepuyes', JSON.stringify(tep)); console.log('mesas', JSON.stringify(mesa));
