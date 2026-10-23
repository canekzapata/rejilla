// node toponimia/medir.js desde hasta → cuántos nombres de lámina distintos
const path = require('path');
for (const f of ['nucleo', 'terreno']) require(path.join(__dirname, '..', f + '.js'));
for (const f of ['glosario', 'nombrar']) require(path.join(__dirname, f + '.js'));
const [a, b] = process.argv.slice(2).map(Number), out = [];
for (let s = a; s <= b; s++) { const N = MT.nombra(MT.terreno(String(s)), String(s)); out.push(N[0] ? N[0].nombre : '—'); }
process.stdout.write(JSON.stringify(out));
