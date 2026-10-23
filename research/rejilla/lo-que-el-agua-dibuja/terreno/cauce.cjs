// Perfil longitudinal de la cárcava mayor (el río más largo de la lámina): la partitura del slide.
//   node terreno/cauce.cjs <semilla>   → terreno/cauce-<semilla>.json: distancia (m) y altitud (m) de la cabecera a la boca,
//   más los afluentes que le llegan (dónde y cuánto bajan), que serán los riffs de la guitarra.
const path = require('path'), fs = require('fs'), M = path.join(__dirname, '../../../montanas-topograficas/');
for (const f of ['nucleo', 'terreno', 'idioma', 'letra', 'vistas', 'toponimia/glosario', 'toponimia/nombrar', 'lamina']) require(M + f + '.js');
const s = process.argv[2]; const T = MT.terreno(String(s), {}); const G = T.G;
const alt = (x, y) => { const i = Math.min(G - 1, Math.round(x * (G - 1))), j = Math.min(G - 1, Math.round(y * (G - 1))); return T.base + T.h[j * G + i] * T.relieve; };
const largo = r => { let d = 0; for (let k = 1; k < r.pts.length; k++) d += Math.hypot(r.pts[k][0] - r.pts[k - 1][0], r.pts[k][1] - r.pts[k - 1][1]); return d * T.anchoKm * 1000; };
const rios = T.hidro.rios.map(r => ({ ...r, L: largo(r) })).sort((a, b) => b.L - a.L);
let pts = rios[0].pts.slice(); if (alt(...pts[0]) < alt(...pts[pts.length - 1])) pts.reverse();
let d = 0; const perfil = pts.map((p, k) => { if (k) d += Math.hypot(p[0] - pts[k - 1][0], p[1] - pts[k - 1][1]) * T.anchoKm * 1000; return [+d.toFixed(1), +alt(...p).toFixed(2), +p[0].toFixed(5), +p[1].toFixed(5)]; });
// afluentes: ríos cuya boca (su punto más bajo) cae a menos de 30 m del cauce mayor
const cerca = (x, y) => { let mejor = 1e9, km = 0; for (let k = 0; k < pts.length; k += 2) { const e = Math.hypot(pts[k][0] - x, pts[k][1] - y) * T.anchoKm * 1000; if (e < mejor) { mejor = e; km = k; } } return [mejor, km]; };
const afl = [];
for (const r of rios.slice(1)) { if (r.L < 300) continue; let a = r.pts[0], b = r.pts[r.pts.length - 1]; if (alt(...a) < alt(...b)) [a, b] = [b, a]; const [e, k] = cerca(...b); if (e < 30) afl.push({ en: perfil[k][0], largo: +r.L.toFixed(0), baja: +(alt(...a) - alt(...b)).toFixed(1), clase: r.clase }); }
afl.sort((a, b) => a.en - b.en);
let nombres = []; try { nombres = MT.nombra(T, String(s), 0).map(n => ({ nombre: n.nombre || n.texto, u: n.u, v: n.v, tipo: n.tipo })); } catch (e) {}
const out = { semilla: s, nombre: T.nombre, relieve: T.relieve, base: T.base, anchoKm: T.anchoKm, metros: +d.toFixed(0), z_cabecera: perfil[0][1], z_boca: perfil[perfil.length - 1][1], n: perfil.length, afluentes: afl, nombres, perfil };
fs.writeFileSync(path.join(__dirname, 'cauce-' + s + '.json'), JSON.stringify(out));
console.log(JSON.stringify({ ...out, perfil: undefined, nombres: nombres.slice(0, 12).map(n => n.nombre) }));
