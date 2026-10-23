// node herramientas/agua_demo.js <etiqueta> — demos de la percusión de agua a render/<et>-agua-*.wav (+ .json)
const fs = require('fs'), path = require('path'), A = require('../motor/agua.js');
const SR = 48000, ET = process.argv[2], R = path.join(__dirname, '..', 'render');
function wav(nombre, y, meta) {
  const f = path.join(R, `${ET}-agua-${nombre}.wav`); if (fs.existsSync(f)) throw new Error('ya existe ' + f);
  let pico = 0; for (const v of y) pico = Math.max(pico, Math.abs(v)); if (!isFinite(pico)) throw new Error('no finito en ' + nombre);
  const n = y.length, b = Buffer.alloc(44 + n * 2), k = .9 / (pico || 1);
  b.write('RIFF', 0); b.writeUInt32LE(36 + n * 2, 4); b.write('WAVEfmt ', 8); b.writeUInt32LE(16, 16); b.writeUInt16LE(1, 20); b.writeUInt16LE(1, 22);
  b.writeUInt32LE(SR, 24); b.writeUInt32LE(SR * 2, 28); b.writeUInt16LE(2, 32); b.writeUInt16LE(16, 34); b.write('data', 36); b.writeUInt32LE(n * 2, 40);
  for (let i = 0; i < n; i++) b.writeInt16LE(Math.round(Math.max(-1, Math.min(1, y[i] * k)) * 32767), 44 + i * 2);
  fs.writeFileSync(f, b, { flag: 'wx' }); fs.writeFileSync(f.replace('.wav', '.json'), JSON.stringify({ ...meta, pico }), { flag: 'wx' });
  console.log(nombre.padEnd(14), 'pico', pico.toFixed(3), (n / SR).toFixed(1) + ' s');
}
fs.mkdirSync(R, { recursive: true }); const t0 = Date.now();
// una melodía de gotas (きくお: Do menor con la sexta bemol), ritmo irregular, registro agudo
const MEL = [72, 75, 79, 80, 79, 75, 72, 74, 75, 84, 80, 79, 72, 67, 72], RIT = [.3, .3, .45, .15, .3, .6, .3, .3, .45, .3, .15, .45, .6, .3, .9];
{ let t = .1; const ev = MEL.map((m, i) => { const e = { t, tipo: 'gota', m, v: .6 + .3 * (i % 3 === 0) }; t += RIT[i]; return e; });
  wav('gotas', A.render({ dur: t + 1, eventos: ev }, SR), { notas: ev.map((e) => [e.t, e.m]) }); }
wav('palo', A.render({ dur: 9, eventos: [{ t: .1, tipo: 'palo', dur: 2.6, m: 86 }, { t: 3, tipo: 'palo', dur: 2.6, m: 81 }, { t: 6, tipo: 'palo', dur: 2.6, m: 91 }] }, SR), { tipo: 'palo' });
{ const ev = []; let t = .1;                                     // güiro: largo-corto-corto, alternando hacia arriba y abajo
  for (let k = 0; k < 4; k++) for (const [d, n] of [[.42, 18], [.13, 6], [.13, 6]]) { ev.push({ t, tipo: 'guiro', dur: d, n, m: 79 + (k % 2) * 5, sube: k % 2 === 0, v: .75 }); t += d + .1; }
  wav('guiro', A.render({ dur: t + 1, eventos: ev }, SR), { tipo: 'guiro' }); }
wav('chorro', A.render({ dur: 5.5, eventos: [{ t: .1, tipo: 'chorro', dur: 4.5, desde: 300, hasta: 3000 }] }, SR), { tipo: 'chorro', desde: 300, hasta: 3000, dur: 4.5 });
wav('burbujeo', A.render({ dur: 5, eventos: [{ t: .1, tipo: 'burbujeo', dur: 4.5, v: .8 }] }, SR), { tipo: 'burbujeo' });
wav('ola', A.render({ dur: 8.5, eventos: [{ t: .1, tipo: 'ola', dur: 7, v: .8 }] }, SR), { tipo: 'ola', dur: 7, rompe: 2.9 });
// el agua que se vuelve ola: gotas cada vez más densas → palo de agua → chorro → la ola rompe → una sola gota
{
  const ev = []; let t = .1, k = 0;
  while (t < 6) { const sep = .5 * Math.pow(.07 / .5, t / 6); ev.push({ t, tipo: 'gota', m: MEL[k % MEL.length] + (k % 4 === 3 ? -12 : 0), v: .55 + .25 * (k % 3 === 0) }); t += sep; k++; }
  // el chorro y la ola se enciman (con el chorro hasta 10.5 s y la ola cuadrática quedaba un hoyo de −50 dB: medido)
  ev.push({ t: 4.5, tipo: 'palo', dur: 3.5, m: 84, v: .8 }, { t: 7, tipo: 'chorro', dur: 4.6, desde: 350, hasta: 2400, v: .8 }, { t: 9, tipo: 'ola', dur: 8, v: .9 });
  ev.push({ t: 17.6, tipo: 'gota', m: 72, v: .7 });
  wav('agua-a-ola', A.render({ dur: 19.2, eventos: ev }, SR), { etapas: [['gotas', 0, 6], ['palo', 4.5, 8], ['chorro', 7, 11.6], ['ola', 9, 17], ['gota', 17.6, 18]] });
}
console.log('render', ((Date.now() - t0) / 1000).toFixed(1), 's');
