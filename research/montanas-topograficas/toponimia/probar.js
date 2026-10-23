// node toponimia/probar.js s1 s2 … → los nombres que el terreno se gana
const path = require('path');
for (const f of ['nucleo', 'terreno']) require(path.join(__dirname, '..', f + '.js'));
for (const f of ['glosario', 'nombrar']) require(path.join(__dirname, f + '.js'));
for (const s of process.argv.slice(2)) {
  const T = MT.terreno(s), N = MT.nombra(T, s);
  console.log(`\n${s} · ${T.nombre}`);
  for (const n of N) console.log(`  ${n.clase.padEnd(9)} ${n.nombre.padEnd(30)} · ${n.glosa}`);
}
