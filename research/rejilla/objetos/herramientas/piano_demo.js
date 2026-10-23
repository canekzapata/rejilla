// node herramientas/piano_demo.js <etiqueta> — demos del piano preparado a render/<etiqueta>-piano-*.wav (+ .json)
const fs = require('fs'), path = require('path');
const P = require('../motor/piano.js');
const SR = 48000, ET = process.argv[2], R = path.join(__dirname, '..', 'render');
function wav(nombre, y, meta) {
  const f = path.join(R, `${ET}-piano-${nombre}.wav`); if (fs.existsSync(f)) throw new Error('ya existe ' + f);
  let pico = 0; for (const v of y) pico = Math.max(pico, Math.abs(v)); if (!isFinite(pico)) throw new Error('no finito en ' + nombre);
  const n = y.length, b = Buffer.alloc(44 + n * 2), k = .9 / (pico || 1);
  b.write('RIFF', 0); b.writeUInt32LE(36 + n * 2, 4); b.write('WAVEfmt ', 8); b.writeUInt32LE(16, 16); b.writeUInt16LE(1, 20); b.writeUInt16LE(1, 22);
  b.writeUInt32LE(SR, 24); b.writeUInt32LE(SR * 2, 28); b.writeUInt16LE(2, 32); b.writeUInt16LE(16, 34); b.write('data', 36); b.writeUInt32LE(n * 2, 40);
  for (let i = 0; i < n; i++) b.writeInt16LE(Math.round(Math.max(-1, Math.min(1, y[i] * k)) * 32767), 44 + i * 2);
  fs.writeFileSync(f, b, { flag: 'wx' }); fs.writeFileSync(f.replace('.wav', '.json'), JSON.stringify({ ...meta, pico }), { flag: 'wx' });
  console.log(nombre.padEnd(18), 'pico', pico.toFixed(3), (n / SR).toFixed(1) + ' s');
}
const t0 = Date.now(); fs.mkdirSync(R, { recursive: true });
const NOTAS = [33, 45, 52, 57, 64, 69, 76, 84];
// 1. sin preparar: notas sueltas a lo largo del teclado
wav('normal', P.render({ dur: NOTAS.length * 1.4 + 3, eventos: NOTAS.map((m, i) => ({ t: i * 1.4, m, v: .7, dur: 1.2 })) }, SR), { notas: NOTAS, cada: 1.4, prep: null });
// 2. las mismas notas con cada preparación
for (const tipo of Object.keys(P.PREP)) {
  wav(tipo, P.render({ dur: NOTAS.length * 1.4 + 3, eventos: NOTAS.map((m, i) => ({ t: i * 1.4, m, v: .7, dur: 1.2, prep: P.PREP[tipo] })) }, SR), { notas: NOTAS, cada: 1.4, prep: tipo });
}
// 3. una frase a lo Cage: cada tecla con su preparación fija (tabla sembrada), ritmos irregulares
{
  let h = 2026; const r = () => { h ^= h << 13; h >>>= 0; h ^= h >> 17; h ^= h << 5; h >>>= 0; return h / 4294967296; };
  const tipos = Object.keys(P.PREP), tabla = {};
  for (let m = 36; m <= 84; m++) tabla[m] = r() < .6 ? P.PREP[tipos[Math.floor(r() * tipos.length)]] : null;
  const frase = [52, 55, 57, 52, 64, 62, 57, 55, 52, 48, 50, 52, 57, 60, 64, 69, 67, 64, 57, 52], ritmo = [.4, .2, .6, .2, .8, .3, .3, .5, .25, .25, .9, .3, .2, .2, .4, .7, .3, .3, .6, 1.2];
  let t = .2; const ev = frase.map((m, i) => { const e = { t, m, v: .45 + .4 * r(), dur: ritmo[i] * .9 }; t += ritmo[i]; return e; });
  wav('cage', P.render({ dur: t + 3, eventos: ev, prepara: (m) => tabla[m] }, SR), { tabla: Object.fromEntries(Object.entries(tabla).map(([m, p]) => [m, p ? Object.keys(P.PREP).find((k) => P.PREP[k] === p) : null])) });
}
// 4. técnicas percutivas: golpes en la caja, pizz, cuerdas apagadas, clusters (con antebrazo)
{
  const ev = []; let t = .2;
  for (let k = 0; k < 6; k++) { ev.push({ t, tipo: 'caja', v: .5 + .1 * k }); t += k % 3 === 2 ? .45 : .22; }
  for (const m of [40, 47, 52, 59]) { ev.push({ t, m, v: .8, dur: .8, tipo: 'pizz' }); t += .3; }
  for (const m of [45, 45, 48, 45, 52, 45]) { ev.push({ t, m, v: .8, dur: .15, tipo: 'apagada' }); t += .16; }
  t += .3; for (let m = 36; m <= 47; m++) ev.push({ t, m, v: .85, dur: 1.6 }); t += 1.8;          // cluster grave
  for (let m = 60; m <= 70; m += 1) ev.push({ t, m, v: .5, dur: .25, tipo: 'apagada' }); t += .4;
  ev.push({ t, tipo: 'caja', v: 1 });
  wav('percusivo', P.render({ dur: t + 3, eventos: ev }, SR), { tecnicas: ['caja', 'pizz', 'apagada', 'cluster', 'cluster apagado'] });
}
// 5. un piano que se prepara mientras suena: la misma nota repetida, el tornillo entra poco a poco (ρ de 0 a .65)
{
  const ev = []; for (let k = 0; k < 14; k++) ev.push({ t: .2 + k * .55, m: 50, v: .7, dur: .5 });
  const prep = (t) => ({ pos: .13, rho: Math.min(.65, Math.max(0, (t - 1) / 6) * .65), amort: .02, zumbido: t > 5 ? .25 : 0, umbral: .015 });
  wav('se-prepara', P.render({ dur: 11, eventos: ev, prepara: () => prep }, SR), { nota: 50, rho: '0 → .65 entre 1 y 7 s; zumbido desde 5 s' });
}
console.log('render', ((Date.now() - t0) / 1000).toFixed(1), 's');
