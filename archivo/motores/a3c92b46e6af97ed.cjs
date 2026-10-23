const fs = require('node:fs');
const path = require('node:path');
const Siringua = require('./lib/siringua/siringua-mensajes.js');

const runId = '5c60e41cb3dc';
const seed = 181026;
const output = __dirname;

function writeWavExclusive(file, samples, sampleRate) {
  const destination = path.join(output, file);
  const handle = fs.openSync(destination, 'wx');
  try {
    const pcm = Buffer.alloc(samples.length * 2);
    for (let i = 0; i < samples.length; i++) {
      const value = Math.max(-1, Math.min(1, Number.isFinite(samples[i]) ? samples[i] : 0));
      pcm.writeInt16LE(Math.round(value * 32767), i * 2);
    }
    const header = Buffer.alloc(44);
    header.write('RIFF', 0); header.writeUInt32LE(36 + pcm.length, 4); header.write('WAVE', 8);
    header.write('fmt ', 12); header.writeUInt32LE(16, 16); header.writeUInt16LE(1, 20);
    header.writeUInt16LE(1, 22); header.writeUInt32LE(sampleRate, 24);
    header.writeUInt32LE(sampleRate * 2, 28); header.writeUInt16LE(2, 32);
    header.writeUInt16LE(16, 34); header.write('data', 36); header.writeUInt32LE(pcm.length, 40);
    fs.writeSync(handle, header); fs.writeSync(handle, pcm);
  } finally { fs.closeSync(handle); }
  return destination;
}

(async () => {
  const text = 'hola bola de hola';
  const item = { id: `teia-comment/885842/80`, source: 'teia-token-comment',
    tokenId: '885842', commentId: '80', sender: 'tz1VHekC8LCYMXhkByM6p71RZQGdMweyUdaw',
    version: 1, text, originalText: text };
  const prepared = await Siringua.preparar(item, { language: 'es-MX', semilla: seed });
  const rendered = Siringua.render(prepared, 24000);
  const base = `siringua-comentario-80-s${seed}-${runId}`;
  const water = writeWavExclusive(`${base}-agua.wav`, rendered.water, rendered.sampleRate);
  const bird = writeWavExclusive(`${base}-ave.wav`, rendered.bird, rendered.sampleRate);
  const mix = writeWavExclusive(`${base}-mezcla.wav`, rendered.samples, rendered.sampleRate);
  const peak = Math.max(...Array.from(rendered.samples, Math.abs));
  const rms = Math.sqrt(rendered.samples.reduce((sum, value) => sum + value * value, 0) / rendered.samples.length);
  const result = { text, tokenId: item.tokenId, commentId: item.commentId,
    provider: prepared.provider, language: prepared.language, words: prepared.words,
    duration: Number(rendered.duration.toFixed(3)), sampleRate: rendered.sampleRate,
    sampleCount: rendered.samples.length, peak: Number(peak.toFixed(4)), rms: Number(rms.toFixed(4)),
    seed, files: [path.basename(water), path.basename(bird), path.basename(mix)] };
  const json = path.join(output, `audio-${runId}.json`);
  const jsonFd = fs.openSync(json, 'wx');
  try { fs.writeFileSync(jsonFd, JSON.stringify(result, null, 2), 'utf8'); }
  finally { fs.closeSync(jsonFd); }
  process.stdout.write(JSON.stringify(result, null, 2));
})().catch(error => { process.stderr.write(String(error.stack || error)); process.exitCode = 1; });
