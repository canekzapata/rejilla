// Exporta una lámina de Traspuesta: alturas (G×G float32), con y sin fondo, y su descripción.   node terreno/exportar.cjs <semilla>
const fs = require('fs'), path = require('path'), M = path.join(__dirname, '../../../montanas-topograficas/');
for (const f of ['nucleo', 'terreno', 'idioma', 'letra', 'vistas', 'toponimia/glosario', 'toponimia/nombrar', 'lamina']) require(M + f + '.js');
const s = process.argv[2], T = MT.terreno(s, {}), F = MT.terreno(s, { fondo: true });
fs.writeFileSync(path.join(__dirname, `h-${s}.f32`), Buffer.from(Float32Array.from(T.h).buffer));
fs.writeFileSync(path.join(__dirname, `fondo-${s}.f32`), Buffer.from(Float32Array.from(F.h).buffer));
let nombres = []; try { nombres = MT.nombra(T, String(s), (MT.VARIANTES && MT.VARIANTES[s]) || 0).slice(0, 30).map(n => ({ nombre: n.nombre || n.texto, clase: n.clase, u: n.u, v: n.v })); } catch (e) { nombres = ['(sin nombres: ' + e.message + ')']; }
const info = { semilla: s, arq: T.arq, nombre: T.nombre, G: T.G, relieve: T.relieve, anchoKm: T.anchoKm, umbralMar: T.umbralMar, nivelMar: T.nivelMar ?? null,
  umbralMarFondo: F.umbralMar, relieveFondo: F.relieve, historia: T.historia || null, especiales: T.especiales || [], nombres };
fs.writeFileSync(path.join(__dirname, `terreno-${s}.json`), JSON.stringify(info, null, 1));
console.log(s, T.nombre, 'relieve', T.relieve, 'km', T.anchoKm, 'umbral', T.umbralMar, 'fondo: relieve', F.relieve, 'umbral', F.umbralMar, 'historia', T.historia, 'nombres', nombres.length);
