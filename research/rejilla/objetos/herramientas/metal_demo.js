// node herramientas/metal_demo.js <etiqueta> — demos del trombón y la trompeta con sordina a render/<et>-metal-*.wav (+ .json)
const M = require('../motor/metal.js'), SR = 48000, wav = require('./escribe_wav.js')(process.argv[2], 'metal', SR);
const R = (c) => M.render(c, SR);
const suma = (...ys) => { const n = Math.max(...ys.map((y) => y.length)), o = new Float32Array(n); ys.forEach((y) => y.forEach((v, i) => { o[i] += v; })); return o; };
// una línea: [[m, dur, extra]…] seguidas (legato si ligado)
const linea = (t, l, sep = .02) => l.map(([m, d, x]) => { const e = { t, dur: d - sep, m, ...(x || {}) }; t += d; return e; });
const lam = { titulo_lamina: 'la física: los labios son una válvula con su resonancia; el tubo, una guía de onda (2·sr/f); la vara cambia su largo',
  modos_lamina: [['tubo (cónico-cilíndrico)', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((k) => [k, Math.pow(k, -.5)])]] };
const t0 = Date.now();
// 1. trombón abierto: una frase oscura en Re menor con vara (glisandos) y un gliss largo que cae al final
{ const n = linea(.1, [[50, .5], [53, .5], [57, .9, { m2: 55 }], [55, .4], [53, .4, { tipo: 'lengua' }], [52, .4, { tipo: 'lengua' }], [50, 1.6, { m2: 38, v: .95 }]], 0);
  wav('trombon', R({ dur: 6, voz: 'trombon', notas: n }), { ...lam }, n); }
// 2. plunger: doo-wah. En cada nota la mano empieza cerrada y abre (wah); la última se queda abriendo y cerrando
{ const n = linea(.1, [[58, .55], [58, .55], [61, .55], [58, 1.1], [56, .45], [53, 1.6]], .04), wah = [];
  n.forEach((e, k) => { wah.push([e.t, 0], [e.t + e.dur * .55, 1], [e.t + e.dur, k === n.length - 1 ? 1 : .2]); });
  const ult = n[n.length - 1]; for (let k = 0; k < 6; k++) wah.push([ult.t + .3 + k * .22, k % 2 ? 1 : .05]);
  wav('plunger', R({ dur: 6.5, voz: 'trombon', sordina: 'plunger', wah, notas: n }), { ...lam, wah }, n); }
// 3. growl: trombón que gruñe en notas largas, contestado por la trompeta con growl y frulato
{ const a = linea(.1, [[46, 1.2, { tipo: 'growl', v: .9 }], [49, .6, { tipo: 'growl' }], [46, 1.4, { tipo: 'growl', m2: 44, v: .95 }]]);
  const b = linea(3.4, [[70, .8, { tipo: 'growl' }], [72, .5, { tipo: 'frulato' }], [67, 1.2, { tipo: 'growl', m2: 65 }]]);
  wav('growl', suma(R({ dur: 6.8, voz: 'trombon', notas: a }), R({ dur: 6.8, voz: 'trompeta', notas: b })), { ...lam }, a.concat(b)); }
// 4. harmon: trompeta con harmon, despacio y grave para su registro (nasal, cerca del micrófono)
{ const n = linea(.1, [[62, .9], [65, .6], [64, 1.4, { m2: 63 }], [60, .5], [62, 1.8, { v: .6 }]], .05);
  wav('harmon', R({ dur: 6, voz: 'trompeta', sordina: 'harmon', notas: n }), { ...lam }, n); }
// 5. golpes de lengua y aire sin nota: staccatos secos, soplos que resuenan en el tubo, frulato
{ const a = [...[0, .18, .36, .72, .9].map((t) => ({ t: .1 + t, dur: .07, m: 46, tipo: 'lengua', v: .9 })), { t: 1.4, dur: 1.2, m: 46, tipo: 'aire', v: .9 },
    { t: 2.8, dur: .9, m: 41, tipo: 'aire', v: .8 }, { t: 4, dur: 1.2, m: 53, tipo: 'frulato', v: .8 }, ...[0, .14, .28].map((t) => ({ t: 5.4 + t, dur: .06, m: 58, tipo: 'lengua', v: 1 }))];
  wav('lengua-aire', R({ dur: 6.4, voz: 'trombon', notas: a }), { ...lam }, a); }
// 6. funk: riff de trompeta y trombón (una octava + quinta abajo) con golpes de lengua, el trombón con plunger abriendo en los acentos
{ const riff = [[0, .12, 'lengua'], [.25, .12, 'lengua'], [.5, .35, null], [1, .12, 'lengua'], [1.12, .12, 'lengua'], [1.5, .4, 'growl']], gr = [0, 0, 3, 5, 3, -2], b = .55, tp = [], tb = [], wah = [];
  for (let c = 0; c < 3; c++) riff.forEach(([t, d, tipo], k) => {
    const tt = .1 + c * 2 * b + t * b * 1.0, m = 65 + gr[k] + (c === 2 && k === 5 ? 3 : 0);
    tp.push({ t: tt, dur: d, m, tipo: tipo || 'normal', v: k === 2 ? .95 : .8 }); tb.push({ t: tt, dur: d, m: m - 19, tipo: tipo || 'normal', v: .85 });
    wah.push([tt, .1], [tt + d * .7, k === 2 || k === 5 ? 1 : .5], [tt + d, .1]);
  });
  wav('funk', suma(R({ dur: 4.6, voz: 'trompeta', sordina: 'straight', notas: tp }), R({ dur: 4.6, voz: 'trombon', sordina: 'plunger', wah, notas: tb })), { ...lam }, tp.concat(tb)); }
console.log('render', ((Date.now() - t0) / 1000).toFixed(1), 's');
