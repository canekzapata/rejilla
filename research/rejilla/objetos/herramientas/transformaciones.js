// node herramientas/transformaciones.js <etiqueta> — los objetos puros (escala) y cuatro transformaciones, a render/
const fs = require('fs'), path = require('path');
const O = require('../motor/objeto.js'), P = O.PURO;
const SR = 48000, ET = process.argv[2], R = path.join(__dirname, '..', 'render');
const hz = (m) => 440 * Math.pow(2, (m - 69) / 12);
function wav(nombre, y, meta) {
  const f = path.join(R, `${ET}-${nombre}.wav`); if (fs.existsSync(f)) throw new Error('ya existe ' + f);
  let pico = 0; for (const v of y) pico = Math.max(pico, Math.abs(v)); const n = y.length, b = Buffer.alloc(44 + n * 2), k = .9 / (pico || 1);
  b.write('RIFF', 0); b.writeUInt32LE(36 + n * 2, 4); b.write('WAVEfmt ', 8); b.writeUInt32LE(16, 16); b.writeUInt16LE(1, 20); b.writeUInt16LE(1, 22);
  b.writeUInt32LE(SR, 24); b.writeUInt32LE(SR * 2, 28); b.writeUInt16LE(2, 32); b.writeUInt16LE(16, 34); b.write('data', 36); b.writeUInt32LE(n * 2, 40);
  for (let i = 0; i < n; i++) b.writeInt16LE(Math.round(Math.max(-1, Math.min(1, y[i] * k)) * 32767), 44 + i * 2);
  fs.writeFileSync(f, b, { flag: 'wx' }); fs.writeFileSync(f.replace('.wav', '.json'), JSON.stringify({ ...meta, pico }), { flag: 'wx' });
  console.log(nombre.padEnd(22), 'pico', pico.toFixed(3), (y.length / SR).toFixed(1) + ' s');
}
// mezcla de dos objetos puros con u en [0, 1]: cada parámetro físico se interpola
const entre = (a, b, u) => { const A = P[a], B = P[b], o = {}; for (const k of ['pos', 'perdida', 'brillo', 'disp', 'soplo', 'ruido']) o[k] = A[k] + (B[k] - A[k]) * u; o.w = A.w.map((x, i) => x + (B.w[i] - x) * u); return o; };
// control: tramos [t0, de, a, t1] (la transformación ocurre entre t0 y t1), notas [[t, midi]], soplo(t) (envolvente 0-1)
function control(dur, tramos, notas, soplo, golpes) {
  const em = (t) => { for (let i = tramos.length - 1; i >= 0; i--) if (t >= tramos[i][0]) { const [t0, a, b, t1] = tramos[i]; return entre(a, b, Math.min(1, Math.max(0, (t - t0) / (t1 - t0)))); } return entre(tramos[0][1], tramos[0][1], 0); };
  const nota = (t) => { let m = notas[0][1]; for (const [tn, mn] of notas) if (t >= tn) m = mn; return hz(m); };
  return { dur, f: nota, w: (t) => em(t).w, pos: (t) => em(t).pos, perdida: (t) => em(t).perdida, brillo: (t) => em(t).brillo, disp: (t) => em(t).disp,
           soplo: soplo, ruido: (t) => em(t).ruido, golpes: golpes || [], vibrato: [4.8, .03] };   // soplo = la respiración (0-1); el motor pone el soplo de cada lazo
}
fs.mkdirSync(R, { recursive: true });
const ESCALA = [45, 48, 50, 52, 55, 57, 60, 62, 64];
// 1-3. cada objeto puro: una escala (La menor pentatónica), notas de 0.55 s
for (const obj of ['saxofon', 'flauta', 'golpe']) {
  const notas = ESCALA.map((m, i) => [i * .55, m]), dur = ESCALA.length * .55 + .8;
  const sop = obj === 'golpe' ? () => 0 : (t) => { const k = t % .55; return t > ESCALA.length * .55 ? 0 : Math.min(1, k / .03) * (k < .48 ? 1 : 0); };
  const golpes = obj === 'golpe' ? ESCALA.map((m, i) => [i * .55 + .01, .9]) : [];
  wav(`puro-${obj}`, O.render(control(dur, [[0, obj, obj, 1]], notas, sop, golpes), SR), { tipo: 'puro', obj, notas });
}
// 4. saxofón → flauta en una nota larga (La3 sostenido 7 s; la transformación tarda 5 s)
wav('sax-a-flauta', O.render(control(7.6, [[0, 'saxofon', 'flauta', 1], [1, 'saxofon', 'flauta', 6]], [[0, 57]], (t) => Math.min(1, t / .05) * (t < 7 ? 1 : 0)), SR),
    { tipo: 'transformación', de: 'saxofon', a: 'flauta', notas: [[0, 57]] });
// 5-6. viento → percusión: notas repetidas; el soplo se acorta hasta volverse golpe y el tubo se vuelve barra
for (const [de, frase] of [['saxofon', [57, 60, 55, 57]], ['flauta', [52, 55, 57, 50]]]) {
  const notas = [], golpes = []; let t = 0, k = 0; const dur = 8;
  while (t < dur - .6) { notas.push([t, frase[k % 4]]); if (t > 2.5) golpes.push([t + .005, Math.min(.9, (t - 2.5) / 3)]); k++; t += .36; }
  const largo = (t) => Math.max(.02, .32 - .3 * Math.min(1, t / 6));          // cada soplo dura menos
  const sop = (t) => { const ph = t % .36; return t > dur - .6 ? 0 : (ph < largo(t) ? Math.min(1, ph / .02) : 0) * Math.max(0, 1 - Math.max(0, t - 5) / 1.5); };
  wav(`${de === 'saxofon' ? 'sax' : 'flauta'}-a-golpe`, O.render(control(dur, [[0, de, 'golpe', 1], [1, de, 'golpe', 6.5]], notas, sop, golpes), SR),
      { tipo: 'transformación', de, a: 'golpe', notas });
}
// 7. una frase que recorre los tres y regresa: sax (0-3) → flauta (3-6) → golpe (6-9) → sax (9-12)
{
  const frase = [57, 60, 62, 64, 62, 60, 57, 55, 57, 60, 64, 67, 64, 62, 60, 57, 55, 52, 55, 57, 60, 57, 55, 57];
  const notas = frase.map((m, i) => [i * .5, m]), dur = frase.length * .5 + .8, golpes = [];
  frase.forEach((m, i) => { const t = i * .5; if (t > 5 && t < 9.5) golpes.push([t + .005, .8]); });
  const sop = (t) => { const ph = t % .5, g = t > 6.2 && t < 9 ? .06 : .44; return t > frase.length * .5 ? 0 : (ph < g ? Math.min(1, ph / .025) : 0); };
  wav('frase-tres-objetos', O.render(control(dur, [[0, 'saxofon', 'saxofon', 1], [2.5, 'saxofon', 'flauta', 3.5], [5.5, 'flauta', 'golpe', 6.5], [8.5, 'golpe', 'saxofon', 9.8]], notas, sop, golpes), SR),
      { tipo: 'frase', notas });
}
