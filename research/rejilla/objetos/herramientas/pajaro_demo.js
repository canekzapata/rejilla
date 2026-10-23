// node herramientas/pajaro_demo.js <etiqueta> — demos del pájaro a render/<et>-pajaro-*.wav (+ .json)
const fs = require('fs'), path = require('path'), P = require('../motor/pajaro.js');
const SR = 48000, ET = process.argv[2], R = path.join(__dirname, '..', 'render');
function wav(nombre, y, meta) {
  const f = path.join(R, `${ET}-pajaro-${nombre}.wav`); if (fs.existsSync(f)) throw new Error('ya existe ' + f);
  let pico = 0; for (const v of y) pico = Math.max(pico, Math.abs(v)); if (!isFinite(pico)) throw new Error('no finito en ' + nombre);
  const n = y.length, b = Buffer.alloc(44 + n * 2), k = .9 / (pico || 1);
  b.write('RIFF', 0); b.writeUInt32LE(36 + n * 2, 4); b.write('WAVEfmt ', 8); b.writeUInt32LE(16, 16); b.writeUInt16LE(1, 20); b.writeUInt16LE(1, 22);
  b.writeUInt32LE(SR, 24); b.writeUInt32LE(SR * 2, 28); b.writeUInt16LE(2, 32); b.writeUInt16LE(16, 34); b.write('data', 36); b.writeUInt32LE(n * 2, 40);
  for (let i = 0; i < n; i++) b.writeInt16LE(Math.round(Math.max(-1, Math.min(1, y[i] * k)) * 32767), 44 + i * 2);
  fs.writeFileSync(f, b, { flag: 'wx' }); fs.writeFileSync(f.replace('.wav', '.json'), JSON.stringify({ ...meta, pico }), { flag: 'wx' });
  console.log(nombre.padEnd(14), 'pico', pico.toFixed(3), (n / SR).toFixed(1) + ' s');
}
fs.mkdirSync(R, { recursive: true }); const t0 = Date.now();
// 1. silbidos: glisandos subiendo, bajando, y uno largo en curva
wav('silbidos', P.render({ dur: 4.6, eventos: [{ t: .1, tipo: 'silbido', m: 86, m2: 93, dur: .35 }, { t: .6, tipo: 'silbido', m: 96, m2: 88, dur: .3 }, { t: 1.1, tipo: 'silbido', m: 91, m2: 91, dur: .5 },
  { t: 1.8, tipo: 'silbido', m: 84, m2: 100, dur: 1.1, v: .8 }, { t: 3.1, tipo: 'silbido', m: 98, m2: 81, dur: 1.2, v: .6 }] }, SR), { gesto: 'silbido' });
// 2. trinos: rápido agudo, lento grave, y uno que se acelera (tres trinos encadenados)
wav('trinos', P.render({ dur: 4.4, eventos: [{ t: .1, tipo: 'trino', m: 93, m2: 98, dur: 1, rate: 24 }, { t: 1.3, tipo: 'trino', m: 84, m2: 81, dur: 1, rate: 11 },
  { t: 2.5, tipo: 'trino', m: 88, m2: 95, dur: .6, rate: 14 }, { t: 3.1, tipo: 'trino', m: 89, m2: 96, dur: .6, rate: 20 }, { t: 3.7, tipo: 'trino', m: 90, m2: 97, dur: .5, rate: 30 }] }, SR), { gesto: 'trino' });
// 3. gorjeo y chips
wav('gorjeo-chips', P.render({ dur: 4.4, eventos: [{ t: .1, tipo: 'gorjeo', m: 91, dur: 1.2, prof: 4, rate: 26 }, { t: 1.5, tipo: 'gorjeo', m: 86, dur: .9, prof: 7, rate: 40 },
  ...[0, 1, 2, 3, 4, 5].map((k) => ({ t: 2.7 + k * .22 - (k > 2 ? .06 : 0), tipo: 'chip', m: 100 - (k % 2) * 3, dur: .05 }))] }, SR), { gesto: 'gorjeo, chip' });
// 4. un canto a lo Messiaen: modo 2 (octatónico) desde Do, células repetidas y cambiadas, y la segunda voz de la siringe
{
  const M2 = [0, 1, 3, 4, 6, 7, 9, 10], nota = (g) => 84 + M2[((g % 8) + 8) % 8] + 12 * Math.floor(g / 8);
  const celula = (g0, ritmo) => ritmo.map((d, i) => [d, nota(g0 + [0, 2, 1, 4, 3, 7][i % 6])]);
  let u = 0; const notas = [];
  for (const [g0, rit] of [[0, [.09, .09, .18]], [0, [.09, .09, .18]], [2, [.06, .06, .06, .27]], [5, [.12, .06, .06, .06, .3]], [1, [.09, .09, .18]], [8, [.06, .06, .06, .06, .06, .36]]]) {
    for (const [d, m] of celula(g0, rit)) { notas.push([u, m, d * .8]); u += d; } u += .12;
  }
  const ev = [{ t: .1, tipo: 'canto', notas, dur: u + .1, v: .7 }];
  // la otra voz de la siringe: notas largas a una séptima mayor / tritono abajo, en los finales de célula
  ev.push({ t: .1 + .36 * 2 + .24, tipo: 'silbido', m: 77, m2: 78, dur: .5, voz: 1, v: .45 }, { t: .1 + u * .62, tipo: 'silbido', m: 79, m2: 77, dur: .7, voz: 1, v: .45 });
  wav('canto-messiaen', P.render({ dur: u + .8, eventos: ev }, SR), { gesto: 'canto (modo 2) + segunda voz', notas });
}
// 5. ronco (cuervo/perico) y 6. el carpintero con el chasquido del pico
wav('ronco', P.render({ dur: 3, eventos: [{ t: .1, tipo: 'ronco', m: 70, dur: .45, v: .7 }, { t: .8, tipo: 'ronco', m: 67, dur: .35, v: .9 }, { t: 1.4, tipo: 'ronco', m: 73, dur: .9, v: .8 }] }, SR), { gesto: 'ronco' });
wav('carpintero', P.render({ dur: 4.2, eventos: [{ t: .1, tipo: 'carpintero', dur: 1.3, v: .9 }, { t: 1.9, tipo: 'pico', v: .8 }, { t: 2.3, tipo: 'pico', v: .7 }, { t: 2.7, tipo: 'carpintero', dur: .9, v: .7 }, { t: 3.8, tipo: 'pico', v: .9 }] }, SR), { gesto: 'carpintero, pico' });
console.log('render', ((Date.now() - t0) / 1000).toFixed(1), 's');
