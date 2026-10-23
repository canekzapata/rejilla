// node herramientas/contrabajo_house.js <etiqueta> — una línea de bajo de house (122 bpm, dieciseisavos) que empieza
// como contrabajo pizz y en 8 s se vuelve bajo de synth house ochentero (casa 0 → 1), y luego se queda ahí 4 s
const fs = require('fs'), path = require('path'), S = require('../motor/cuerda.js');
const SR = 48000, ET = process.argv[2], R = path.join(__dirname, '..', 'render');
const s16 = 60 / 122 / 4, PATRON = [33, 0, 45, 33, 0, 33, 45, 0, 36, 0, 48, 36, 31, 0, 43, 33];     // La1 con octavas; 0 = silencio
const ev = []; let k = 0;
for (let t = .1; t < 12.2; t += s16, k++) {
  const m = PATRON[k % 16]; if (!m) continue;
  const casa = Math.min(1, Math.max(0, (t - 1) / 7)), acento = k % 4 === 0 ? 1 : .75;
  ev.push({ t, m, v: .85 * acento, dur: s16 * (k % 16 === 2 || k % 16 === 6 ? .6 : 1.4), tipo: 'pizz', casa });
}
const y = S.render({ dur: 13.5, instrumento: 'contrabajo', eventos: ev }, SR);
let pico = 0; for (const v of y) pico = Math.max(pico, Math.abs(v)); if (!isFinite(pico)) throw new Error('no finito');
const f = path.join(R, `${ET}-contrabajo-a-house.wav`), n = y.length, b = Buffer.alloc(44 + n * 2), kk = .9 / pico;
b.write('RIFF', 0); b.writeUInt32LE(36 + n * 2, 4); b.write('WAVEfmt ', 8); b.writeUInt32LE(16, 16); b.writeUInt16LE(1, 20); b.writeUInt16LE(1, 22);
b.writeUInt32LE(SR, 24); b.writeUInt32LE(SR * 2, 28); b.writeUInt16LE(2, 32); b.writeUInt16LE(16, 34); b.write('data', 36); b.writeUInt32LE(n * 2, 40);
for (let i = 0; i < n; i++) b.writeInt16LE(Math.round(Math.max(-1, Math.min(1, y[i] * kk)) * 32767), 44 + i * 2);
fs.writeFileSync(f, b, { flag: 'wx' }); fs.writeFileSync(f.replace('.wav', '.json'), JSON.stringify({ casa: '0 → 1 entre 1 y 8 s', bpm: 122, pico }), { flag: 'wx' });
console.log('contrabajo-a-house pico', pico.toFixed(3), (n / SR).toFixed(1), 's');
