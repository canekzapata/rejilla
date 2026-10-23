// Prueba local: fragmento público de Teia -> eSpeak fonemas -> agua y respuesta de pájaro.
// La comprobación del mensaje y el CID están anotados en README; este script no hace peticiones de red.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { readAsync } = require('../../../difonos/runtime/lector.js');
const Agua = require('../objetos/motor/vozagua.js');
const Pajaro = require('../objetos/motor/pajaro.js');
const Adapter = require('./adaptador-siringua.js');

const text = 'Art is exclusive and egocentric by nature, no need to hide that behind a false sense of belonging.';
const SR = 24000;
const semilla = 181026;
function writeWav(file, samples) {
  const b = Buffer.alloc(44 + samples.length * 4);
  b.write('RIFF'); b.writeUInt32LE(b.length - 8, 4); b.write('WAVEfmt ', 8);
  b.writeUInt32LE(16, 16); b.writeUInt16LE(3, 20); b.writeUInt16LE(1, 22);
  b.writeUInt32LE(SR, 24); b.writeUInt32LE(SR * 4, 28); b.writeUInt16LE(4, 32);
  b.writeUInt16LE(32, 34); b.write('data', 36); b.writeUInt32LE(samples.length * 4, 40);
  for (let i = 0; i < samples.length; i++) b.writeFloatLE(Number.isFinite(samples[i]) ? samples[i] : 0, 44 + i * 4);
  fs.writeFileSync(file, b, { flag: 'wx' });
}
function mix(a, b) {
  const out = new Float32Array(Math.max(a.length, b.length));
  for (let i = 0; i < out.length; i++) out[i] = (a[i] || 0) * .78 + (b[i] || 0) * .72;
  let peak = 0; for (const x of out) peak = Math.max(peak, Math.abs(x));
  if (peak > .94) for (let i = 0; i < out.length; i++) out[i] *= .94 / peak;
  return out;
}
(async () => {
  const reading = await readAsync(text, { language: 'en-US' });
  const words = reading.words;
  if (words.length !== 18 || reading.unresolved.length) throw new Error('Lectura incompleta; no se crea entrega.');
  const waterEvents = [], birdEvents = [];
  let t = .35;
  words.forEach((word, i) => {
    const phones = Adapter.adaptar(word.phones);
    const vowels = phones.filter(p => Agua.FORMANTES[p]).length;
    const consonants = phones.length - vowels;
    const dur = Math.max(.28, vowels * .12 + consonants * .075);
    waterEvents.push({ t, dur, texto: word.text, fonemas: phones, nota: 55 + [0, 2, 4, 2][i % 4], modo: 'canto', voz: 1, v: .68 });
    const bt = t + dur + .07;
    const base = 65 + [0, 2, 5, 7][(phones.filter(p => Agua.FORMANTES[p]).length + i) % 4];
    birdEvents.push({ t: bt, dur: .19, tipo: 'canto', notas: [[0, base, .065], [.085, base + [3, 5, 2, 4][i % 4], .07]], voz: 1, v: .48 });
    t = bt + .25;
  });
  const duration = t + .35;
  const water = Agua.render({ dur: duration, eventos: waterEvents, semilla }, SR);
  const bird = Pajaro.render({ dur: duration, eventos: birdEvents, semilla: semilla + 1 }, SR);
  const final = mix(water, bird);
  const nonce = crypto.randomBytes(8).toString('hex');
  const sourceFiles = [__filename, path.join(__dirname, 'crear-proceso-teia.py'), path.join(__dirname, 'adaptador-siringua.js'), path.join(__dirname, '..', 'objetos/motor/vozagua.js'), path.join(__dirname, '..', 'objetos/motor/pajaro.js'), path.join(__dirname, '..', '..', '..', 'difonos/runtime/lector.js'), path.join(__dirname, '..', '..', '..', 'difonos/runtime/espeak-en-wasm.js')];
  const sourceHashes = Object.fromEntries(sourceFiles.map(f => [path.relative(path.join(__dirname, '..', '..'), f).replace(/\\/g, '/'), crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex')]));
  const imageBasisHash = crypto.createHash('sha256').update(Buffer.from(final.buffer, final.byteOffset, final.byteLength)).digest('hex');
  const runHash = crypto.createHash('sha256').update(text).update(JSON.stringify(sourceHashes)).update(imageBasisHash).update(nonce).digest('hex');
  const runId = runHash.slice(0, 12);
  const outDir = path.join(__dirname, `siringua-mensaje-abierto-s${semilla}-${runId}`);
  fs.mkdirSync(outDir, { recursive: false });
  writeWav(path.join(outDir, `agua-habla-s${semilla}-${runId}.wav`), water);
  writeWav(path.join(outDir, `respuesta-del-ave-s${semilla}-${runId}.wav`), bird);
  writeWav(path.join(outDir, `siringua-mensaje-de-teia-s${semilla}-${runId}.wav`), final);
  const metadata = { text, channel: 10, message: 168, cid: 'QmVxFZtC5QTQes1gZSAvX8chJrPFkNVJwoeLZ5mWmyipAN', semilla, nonce, runHash, runId, imageBasisHash, sourceHashes,
    provider: reading.provider, duration: Number(duration.toFixed(2)), wordCount: words.length,
    words: words.map(w => ({ text:w.text, phones:w.phones, ipa:w.transcription, status:w.status })),
    waterEventCount: waterEvents.length, birdEventCount: birdEvents.length };
  fs.writeFileSync(path.join(outDir, 'registro.json'), JSON.stringify(metadata, null, 2), { flag: 'wx' });
  console.log(JSON.stringify({ outDir, ...metadata, files: fs.readdirSync(outDir) }, null, 2));
})().catch(err => { console.error(err); process.exit(1); });
