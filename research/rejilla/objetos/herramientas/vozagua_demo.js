// node herramientas/vozagua_demo.js <etiqueta> — demos del watervoicephone a render/<et>-vozagua-*.wav (+ .json)
const fs = require('fs'), path = require('path'), V = require('../motor/vozagua.js');
const SR = 48000, ET = process.argv[2], R = path.join(__dirname, '..', 'render');
function wav(nombre, y, meta, eventos) {
  const f = path.join(R, `${ET}-vozagua-${nombre}.wav`); if (fs.existsSync(f)) throw new Error('ya existe ' + f);
  let pico = 0; for (const v of y) pico = Math.max(pico, Math.abs(v)); if (!isFinite(pico)) throw new Error('no finito en ' + nombre);
  const n = y.length, b = Buffer.alloc(44 + n * 2), k = .9 / (pico || 1);
  b.write('RIFF', 0); b.writeUInt32LE(36 + n * 2, 4); b.write('WAVEfmt ', 8); b.writeUInt32LE(16, 16); b.writeUInt16LE(1, 20); b.writeUInt16LE(1, 22);
  b.writeUInt32LE(SR, 24); b.writeUInt32LE(SR * 2, 28); b.writeUInt16LE(2, 32); b.writeUInt16LE(16, 34); b.write('data', 36); b.writeUInt32LE(n * 2, 40);
  for (let i = 0; i < n; i++) b.writeInt16LE(Math.round(Math.max(-1, Math.min(1, y[i] * k)) * 32767), 44 + i * 2);
  fs.writeFileSync(f, b, { flag: 'wx' }); fs.writeFileSync(f.replace('.wav', '.json'), JSON.stringify({ ...meta, pico, eventos }), { flag: 'wx' });
  console.log(nombre.padEnd(14), 'pico', pico.toFixed(3), (n / SR).toFixed(1) + ' s');
}
// una frase: [[texto, nota, dur]…] seguidas desde t, con un respiro entre palabras
const frase = (t, pal, extra) => pal.map(([texto, nota, dur]) => { const e = { t, dur, texto, nota, ...extra }; t += dur + .06; return e; });
const fin = (ev) => Math.max(...ev.map((e) => e.t + e.dur)) + .6;
fs.mkdirSync(R, { recursive: true }); const t0 = Date.now();
// 1. susurro: el agua dice sin altura
{ const ev = frase(.1, [['el', 0, .3], ['agua', 0, .7], ['susurra', 0, 1.1], ['lo', 0, .3], ['que', 0, .35], ['sabe', 0, .9]], { modo: 'susurro', v: .8 }); wav('susurro', V.render({ dur: fin(ev), eventos: ev }, SR), { modo: 'susurro' }, ev); }
// 2. canto: una línea en La menor, oscura
{ const ev = frase(.1, [['el', 57, .35], ['agua', 60, .9], ['canta', 64, .8], ['con', 62, .35], ['la', 60, .35], ['boca', 59, .9], ['llena', 57, 1.3]], { modo: 'canto' }); wav('canto', V.render({ dur: fin(ev), eventos: ev }, SR), { modo: 'canto', texto: 'el agua canta con la boca llena' }, ev); }
// 3. gárgara
{ const ev = frase(.1, [['agua', 50, .9], ['en', 53, .4], ['la', 52, .4], ['garganta', 48, 1.6]], { modo: 'gargara' }); wav('gargara', V.render({ dur: fin(ev), eventos: ev }, SR), { modo: 'gargara' }, ev); }
// 4. el agua aprende a hablar: la misma frase con voz 0 → 1/3 → 2/3 → 1
{ let ev = [], t = .1; for (const voz of [0, .33, .66, 1]) { const f = frase(t, [['aprendo', 55, .9], ['a', 57, .3], ['hablar', 60, 1]], { modo: 'canto', voz }); ev = ev.concat(f); t = fin(f) - .2; }
  wav('aprende', V.render({ dur: fin(ev), eventos: ev }, SR), { voz: [0, .33, .66, 1] }, ev); }
// 5. dos voces de agua: contrapunto, una abajo y otra arriba que entra después
{ const a = frase(.1, [['dos', 52, .6], ['aguas', 55, 1], ['que', 53, .35], ['se', 52, .35], ['cruzan', 50, 1.4]], { modo: 'canto', v: .7 });
  const b = frase(.7, [['una', 64, .7], ['sube', 67, .9], ['otra', 65, .7], ['baja', 62, 1.2]], { modo: 'canto', v: .55, });
  const ev = a.concat(b); wav('dos-voces', V.render({ dur: fin(ev), eventos: ev, semilla: 9 }, SR), { voces: 2 }, ev); }
// 6. dos vocales a la vez: una sola agua dice «a» e «i» al mismo tiempo, luego «o»+«e», «u»+«a»
{ const ev = [['aaa', 'i', 57], ['ooo', 'e', 55], ['uuu', 'a', 52], ['iii', 'o', 60]].map(([texto, doble, nota], k) => ({ t: .1 + k * 1.3, dur: 1.15, texto, doble, nota, modo: 'canto' }));
  wav('dos-vocales', V.render({ dur: fin(ev), eventos: ev }, SR), { doble: ev.map((e) => e.texto[0] + '+' + e.doble) }, ev); }
console.log('render', ((Date.now() - t0) / 1000).toFixed(1), 's');
