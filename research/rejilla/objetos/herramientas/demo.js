// node herramientas/demo.js <etiqueta> — renderiza los objetos puros y las transformaciones a render/<etiqueta>-*.wav (+ .json)
// (nunca encima: si el archivo existe, se detiene)
const fs = require('fs'), path = require('path');
const O = require('../motor/objeto.js');
const SR = 48000, ET = process.argv[2] || 'a1', R = path.join(__dirname, '..', 'render');
const hz = (m) => 440 * Math.pow(2, (m - 69) / 12);
function wav(nombre, y, meta) {
  const f = path.join(R, `${ET}-${nombre}.wav`); if (fs.existsSync(f)) throw new Error('ya existe ' + f);
  let pico = 0; for (const v of y) pico = Math.max(pico, Math.abs(v));
  const n = y.length, b = Buffer.alloc(44 + n * 2), k = pico > .98 ? .98 / pico : 1;
  b.write('RIFF', 0); b.writeUInt32LE(36 + n * 2, 4); b.write('WAVEfmt ', 8); b.writeUInt32LE(16, 16); b.writeUInt16LE(1, 20); b.writeUInt16LE(1, 22);
  b.writeUInt32LE(SR, 24); b.writeUInt32LE(SR * 2, 28); b.writeUInt16LE(2, 32); b.writeUInt16LE(16, 34); b.write('data', 36); b.writeUInt32LE(n * 2, 40);
  for (let i = 0; i < n; i++) b.writeInt16LE(Math.round(Math.max(-1, Math.min(1, y[i] * k)) * 32767), 44 + i * 2);
  fs.writeFileSync(f, b, { flag: 'wx' }); fs.writeFileSync(f.replace('.wav', '.json'), JSON.stringify({ ...meta, pico, escala: k }), { flag: 'wx' });
  console.log(nombre, 'pico', pico.toFixed(3), isFinite(pico) ? '' : '¡NO FINITO!');
}
// una nota sostenida de un objeto puro: ataque, cuerpo, apagado
function nota(obj, m, dur, extra) {
  const p = O.PURO[obj], C = O.curva;
  const sop = [[0, 0], [.04, p.soplo * 1.15], [.15, p.soplo], [dur - .15, p.soplo], [dur - .05, 0], [dur, 0]];
  return Object.assign({ dur: dur + .6, f: C(hz(m)), w: C(p.w), pos: C(p.pos), perdida: C(p.perdida), brillo: C(p.brillo), disp: C(p.disp),
    soplo: C(sop), ruido: C(p.ruido), golpes: obj === 'golpe' ? [[.02, .9]] : [] }, extra || {});
}
fs.mkdirSync(R, { recursive: true });
for (const obj of ['saxofon', 'flauta', 'golpe']) for (const m of [50, 57, 64, 69]) {
  const t0 = Date.now(), y = O.render(nota(obj, m, 1.6, { vibrato: obj === 'golpe' ? null : [5, .004] }), SR);
  wav(`${obj}-${m}`, y, { obj, nota: m, ms: Date.now() - t0 });
}
