// escribe_wav.js — el escritor de demos compartido: render/<et>-<objeto>-<nombre>.wav (+ .json con el pico y los eventos)
const fs = require('fs'), path = require('path');
module.exports = function (ET, objeto, SR) {
  const R = path.join(__dirname, '..', 'render'); fs.mkdirSync(R, { recursive: true });
  return function wav(nombre, y, meta, eventos) {
    const f = path.join(R, `${ET}-${objeto}-${nombre}.wav`); if (fs.existsSync(f)) throw new Error('ya existe ' + f);
    let pico = 0; for (const v of y) pico = Math.max(pico, Math.abs(v)); if (!isFinite(pico)) throw new Error('no finito en ' + nombre);
    const n = y.length, b = Buffer.alloc(44 + n * 2), k = .9 / (pico || 1);
    b.write('RIFF', 0); b.writeUInt32LE(36 + n * 2, 4); b.write('WAVEfmt ', 8); b.writeUInt32LE(16, 16); b.writeUInt16LE(1, 20); b.writeUInt16LE(1, 22);
    b.writeUInt32LE(SR, 24); b.writeUInt32LE(SR * 2, 28); b.writeUInt16LE(2, 32); b.writeUInt16LE(16, 34); b.write('data', 36); b.writeUInt32LE(n * 2, 40);
    for (let i = 0; i < n; i++) b.writeInt16LE(Math.round(Math.max(-1, Math.min(1, y[i] * k)) * 32767), 44 + i * 2);
    fs.writeFileSync(f, b, { flag: 'wx' }); fs.writeFileSync(f.replace('.wav', '.json'), JSON.stringify({ ...meta, pico, eventos }), { flag: 'wx' });
    console.log(nombre.padEnd(16), 'pico', pico.toFixed(3), (n / SR).toFixed(1) + ' s');
  };
};
