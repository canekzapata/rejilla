// node objetos.js <etiqueta> — los objetos físicos de «planeta 9» (motores de ../objetos/motor), afinados a los
// armónicos del planeta del momento, a render/<et>-<objeto>.wav (mono, 32 bits flotantes, sin normalizar: la mezcla mide)
const fs = require('fs'), path = require('path');
require('./motor/cancion.js'); const C = globalThis.Cancion;
const M = (n) => require('../objetos/motor/' + n + '.js');
const W = M('waterphone'), G = M('gong'), A = M('agua'), V = M('vozagua');
const SR = 48000, ET = process.argv[2], R = path.join(__dirname, 'render'), T = C.T, DUR = C.DURACION;
if (!ET || !/^[a-z0-9-]+$/.test(ET)) throw new Error('falta la etiqueta');
fs.mkdirSync(R, { recursive: true });
function wav(nombre, y, eventos) {
  const f = path.join(R, `${ET}-${nombre}.wav`); if (fs.existsSync(f)) throw new Error('ya existe ' + f);
  const n = y.length, b = Buffer.alloc(44 + n * 4);
  b.write('RIFF', 0); b.writeUInt32LE(36 + n * 4, 4); b.write('WAVEfmt ', 8); b.writeUInt32LE(16, 16); b.writeUInt16LE(3, 20); b.writeUInt16LE(1, 22);
  b.writeUInt32LE(SR, 24); b.writeUInt32LE(SR * 4, 28); b.writeUInt16LE(4, 32); b.writeUInt16LE(32, 34); b.write('data', 36); b.writeUInt32LE(n * 4, 40);
  for (let i = 0; i < n; i++) b.writeFloatLE(y[i], 44 + i * 4);
  fs.writeFileSync(f, b, { flag: 'wx' }); fs.writeFileSync(f.replace('.wav', '.json'), JSON.stringify({ eventos }), { flag: 'wx' });
  let pk = 0; for (const v of y) pk = Math.max(pk, Math.abs(v)); console.log(nombre.padEnd(12), 'pico', pk.toFixed(3));
}
// la nota midi del armónico n del planeta en el compás b, llevada por octavas a [lo, hi)
const armonico = (b, n, lo, hi) => { const Ak = C.acordes().filter((a) => a[0] <= b + 1e-9).pop(); let m = Ak[1] + 12 * Math.log2(n); while (m < lo) m += 12; while (m >= hi) m -= 12; return m; };

// waterphone: hielo quieto en la intro (arcos sin agua, en los armónicos 9, 15, 7, 11, 13 de Sol1) y el gemido del puente
{
  const ev = [];
  [[0, 9, 6], [1.5, 15, 5], [2.6, 7, 4.5], [3.4, 13, 3.5], [4.2, 11, 2.5]].forEach(([b, n, d]) => ev.push({ t: b * T, tipo: 'arco', m: armonico(b, n, 66, 90), dur: d * T, v: .5 }));
  for (let b = 46; b < 53; b++) ev.push({ t: b * T + .1, tipo: 'arco', m: armonico(b + .01, [7, 9, 11, 13, 15, 9, 7][b - 46], 64, 84), dur: T * 1.2, v: .45, agua: 2.5, ola: .3 });
  ev.push({ t: 46 * T, tipo: 'bola', dur: 7 * T, v: .35, agua: 1.5, ola: .15 });
  wav('waterphone', W.render({ dur: DUR, eventos: ev }, SR), ev);
}
// gong: dos alturas que se cruzan en el arranque de cada presoro (la gravedad), cruces en el puente y el tam-tam del último coro
{
  const ev = [{ t: 14 * T - .05, tipo: 'cruce', m: armonico(14.01, 7, 60, 72), v: .55, abre: 5 }, { t: 34 * T - .05, tipo: 'cruce', m: armonico(34.01, 7, 60, 72), v: .55, abre: -5 }];
  for (let b = 46; b < 53; b++) ev.push({ t: b * T, tipo: 'cruce', m: armonico(b + .01, 5, 58, 70), v: .35, abre: b % 2 ? 7 : -7 });
  ev.push({ t: 54 * T - .02, tipo: 'tamtam', v: .7, dureza: .5 });
  wav('gong', G.render({ dur: DUR, eventos: ev }, SR), ev);
}
// agua: en el puente, gotas afinadas a los armónicos del planeta que se suelta (la pecera del pez beta) y un burbujeo
{
  const ev = [{ t: 46 * T, tipo: 'burbujeo', dur: 7.5 * T, v: .4 }];
  for (let b = 46; b < 54; b++) [0, 3, 6, 10, 12].forEach((p, i) => { if ((b + i) % 3) ev.push({ t: b * T + p * C.S16, tipo: 'gota', m: armonico(b + p / 16, [9, 5, 13, 11, 7][i], 78, 92), v: .55 }); });   // sin el 15: la gota sube ~100 c al apagarse y cruzaba el 16
  wav('agua', A.render({ dur: DUR, eventos: ev }, SR), ev);
}
// la voz de agua: canta en el puente «y en su lugar un pez beta / como planeta nuevo» (dos vocales a la vez en «pez» y «be»)
{
  const ev = C.partituraAgua().map((e) => ({ ...e, dur: e.dur * .95, modo: 'canto', voz: 1, v: .75, doble: { pez: 'a', be: 'o', ne: 'u' }[e.texto] }));
  wav('vozagua', V.render({ dur: DUR, eventos: ev }, SR), ev);
}
