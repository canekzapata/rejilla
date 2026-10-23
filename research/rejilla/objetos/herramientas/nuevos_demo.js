// node herramientas/nuevos_demo.js <etiqueta> — demos del clarinete bajo y de la cuerda frotada a render/<et>-<nombre>.wav
const fs = require('fs'), path = require('path');
const K = require('../motor/clarinete.js'), S = require('../motor/cuerda.js');
const SR = 48000, ET = process.argv[2], R = path.join(__dirname, '..', 'render');
function wav(nombre, y, meta) {
  const f = path.join(R, `${ET}-${nombre}.wav`); if (fs.existsSync(f)) throw new Error('ya existe ' + f);
  let pico = 0; for (const v of y) pico = Math.max(pico, Math.abs(v)); if (!isFinite(pico)) throw new Error('no finito en ' + nombre);
  const n = y.length, b = Buffer.alloc(44 + n * 2), k = .9 / (pico || 1);
  b.write('RIFF', 0); b.writeUInt32LE(36 + n * 2, 4); b.write('WAVEfmt ', 8); b.writeUInt32LE(16, 16); b.writeUInt16LE(1, 20); b.writeUInt16LE(1, 22);
  b.writeUInt32LE(SR, 24); b.writeUInt32LE(SR * 2, 28); b.writeUInt16LE(2, 32); b.writeUInt16LE(16, 34); b.write('data', 36); b.writeUInt32LE(n * 2, 40);
  for (let i = 0; i < n; i++) b.writeInt16LE(Math.round(Math.max(-1, Math.min(1, y[i] * k)) * 32767), 44 + i * 2);
  fs.writeFileSync(f, b, { flag: 'wx' }); fs.writeFileSync(f.replace('.wav', '.json'), JSON.stringify({ ...meta, pico }), { flag: 'wx' });
  console.log(nombre.padEnd(26), 'pico', pico.toFixed(3), (n / SR).toFixed(1) + ' s');
}
const seq = (notas, d, extra) => { let t = .1; return notas.map((m) => { const e = Object.assign({ t, m, v: .7, dur: d * .95 }, extra || {}); t += d; return e; }); };
const dur = (ev) => Math.max(...ev.map((e) => e.t + (e.dur || .5))) + 1.2;
fs.mkdirSync(R, { recursive: true }); const t0 = Date.now();

// ── clarinete bajo ──
{ const ev = seq([34, 38, 41, 43, 46, 50, 53, 55, 58, 62, 65], .55); wav('clarinete-escala', K.render({ dur: dur(ev), eventos: ev }, SR), { notas: ev.map((e) => [e.t, e.m]) }); }
{ const ev = seq([46, 45, 43, 41, 43, 38], .9, { tipo: 'subtono', v: .5 }); wav('clarinete-subtono', K.render({ dur: dur(ev), eventos: ev }, SR), { notas: ev.map((e) => [e.t, e.m]) }); }
{ // percutivo: slaps y llaves en un ritmo (3+3+2), y luego multifónico y aire
  const ev = []; let t = .1; const r = [.3, .3, .2, .3, .3, .2, .15, .15, .2, .3, .3, .2];
  r.forEach((d, i) => { ev.push({ t, m: [34, 41, 34, 46, 34, 41][i % 6], v: .8, dur: .1, tipo: i % 4 === 3 ? 'llaves' : 'slap' }); t += d; });
  ev.push({ t: t + .2, m: 41, v: .8, dur: 2.2, tipo: 'multifonico' }); ev.push({ t: t + 2.7, m: 38, v: .5, dur: 1.6, tipo: 'aire' });
  wav('clarinete-percusivo', K.render({ dur: dur(ev), eventos: ev }, SR), { tecnicas: ['slap', 'llaves', 'multifonico', 'aire'] });
}
{ const ev = [{ t: .1, m: 38, v: .7, dur: 1.6, gliss: true }, { t: 1.7, m: 50, v: .7, dur: 1.2 }, { t: 2.9, m: 43, v: .7, dur: 1.6, gliss: true }, { t: 4.5, m: 36, v: .7, dur: 1.5 }];
  wav('clarinete-glisando', K.render({ dur: dur(ev), eventos: ev }, SR), { notas: ev.map((e) => [e.t, e.m]) }); }

// ── cuerdas ──
{ const ev = seq([48, 50, 51, 55, 53, 51, 50, 48, 43, 48], .8, { tipo: 'arco' }); wav('chelo-arco', S.render({ dur: dur(ev), instrumento: 'chelo', eventos: ev }, SR), { notas: ev.map((e) => [e.t, e.m]) }); }
{ const ev = [];
  for (const [tipo, m] of [['arco', 69], ['ponticello', 69], ['tasto', 69], ['tremolo', 64], ['armonico', 69]]) ev.push(...seq([m, m + 3, m + 7], .6, { tipo }).map((e, i) => ({ ...e, t: e.t + ev.length * .6 + (i === 0 ? .2 : 0) })));
  wav('violin-colores', S.render({ dur: dur(ev), instrumento: 'violin', eventos: ev }, SR), { notas: ev.map((e) => [e.t, e.m + (e.tipo === 'armonico' ? 12 : 0)]), tecnicas: ['arco', 'ponticello', 'tasto', 'tremolo', 'armonico'] });
}
{ // percutivo: pizz, Bartók, col legno (chelo)
  const ev = []; let t = .1;
  [36, 43, 48, 43].forEach((m) => { ev.push({ t, m, v: .8, dur: .4, tipo: 'pizz' }); t += .35; });
  [36, 36, 43].forEach((m) => { ev.push({ t, m, v: .9, dur: .4, tipo: 'bartok' }); t += .45; });
  for (let k = 0; k < 10; k++) { ev.push({ t, m: [48, 55, 51, 55][k % 4], v: .6, dur: .1, tipo: 'legno' }); t += k % 3 === 2 ? .3 : .15; }
  wav('chelo-percusivo', S.render({ dur: t + 2, instrumento: 'chelo', eventos: ev }, SR), { tecnicas: ['pizz', 'bartok', 'legno'] });
}
{ // contrabajo pizz caminando
  const ev = seq([28, 31, 33, 35, 36, 35, 33, 31, 28, 26, 28, 33], .38, { tipo: 'pizz', v: .85 });
  wav('contrabajo-pizz', S.render({ dur: dur(ev) + 1, instrumento: 'contrabajo', eventos: ev }, SR), { notas: ev.map((e) => [e.t, e.m]) });
}
{ // el pizz que se vuelve house: corcheas a 122 bpm, casa de 0 a 1 en 8 s (acordes de Lam9 en dos voces)
  const ev = [], c = 60 / 122 / 2; let t = .1, k = 0;
  while (t < 9.5) { const casa = Math.min(1, Math.max(0, (t - 1) / 7)); const m = [45, 52, 57, 52, 48, 55, 59, 55][k % 8]; ev.push({ t, m, v: .8, dur: .3, tipo: 'pizz', casa }); if (k % 2 === 0) ev.push({ t, m: m + 7, v: .5, dur: .3, tipo: 'pizz', casa }); t += c; k++; }
  wav('chelo-a-house', S.render({ dur: t + 2, instrumento: 'chelo', eventos: ev }, SR), { casa: '0 → 1 entre 1 y 8 s', bpm: 122 });
}
console.log('render', ((Date.now() - t0) / 1000).toFixed(1), 's');
