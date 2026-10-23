// node herramientas/waterphone_demo.js <etiqueta> — demos del waterphone a render/<et>-waterphone-*.wav (+ .json)
const W = require('../motor/waterphone.js'), SR = 48000, wav = require('./escribe_wav.js')(process.argv[2], 'waterphone', SR);
const fin = (ev) => Math.max(...ev.map((e) => e.t + (e.dur || 0))) + 3;
const hecho = (nombre, ev, meta) => wav(nombre, W.render({ dur: fin(ev), eventos: ev }, SR), meta, ev);
const t0 = Date.now();
// 1. arcos: tres varillas con arco, quietas, encimándose (sin agua)
hecho('arcos', [{ t: .1, tipo: 'arco', vara: 3, dur: 2.2 }, { t: 1.3, tipo: 'arco', vara: 11, dur: 2.2, v: .5 }, { t: 2.6, tipo: 'arco', vara: 17, dur: 2, v: .4 }], { gesto: 'arco' });
// 2. el gemido: las mismas varillas con el agua moviéndose (dobla hasta 2-3 semitonos y regresa)
hecho('gemido', [{ t: .1, tipo: 'arco', vara: 3, dur: 3.5, agua: 2.5, ola: .35 }, { t: 1.2, tipo: 'arco', vara: 8, dur: 3, v: .55, agua: 3, ola: .5 },
  { t: 2.6, tipo: 'arco', vara: 19, dur: 2.2, v: .35, agua: 1.5, ola: .8 }], { gesto: 'arco con agua' });
// 3. golpes: un arpegio de dedos sobre las varillas, el agua meciéndose despacio
{ const ev = []; [0, 4, 9, 13, 18, 22, 15, 7, 2, 10, 21, 5].forEach((k, i) => ev.push({ t: .1 + i * .19 + (i > 5 ? .4 : 0), tipo: 'golpe', vara: k, v: .5 + .3 * (i % 3 === 0), agua: 1, ola: .3 }));
  hecho('golpes', ev, { gesto: 'golpe' }); }
// 4. la superbola frotando la vasija
hecho('bola', [{ t: .1, tipo: 'bola', dur: 4, v: .8, agua: 1, ola: .25 }], { gesto: 'superbola' });
// 5. escena: la bola abajo, un arco con agua y dedos que caen encima
hecho('escena', [{ t: .1, tipo: 'bola', dur: 5, v: .6 }, { t: .8, tipo: 'arco', vara: 6, dur: 3.5, v: .6, agua: 2, ola: .3 },
  ...[20, 14, 23, 9].map((k, i) => ({ t: 2.2 + i * .45, tipo: 'golpe', vara: k, v: .45, agua: 2, ola: .3 })), { t: 3.5, tipo: 'arco', vara: 16, dur: 2.3, v: .4, agua: 3.5, ola: .6 }], { gesto: 'escena' });
console.log('render', ((Date.now() - t0) / 1000).toFixed(1), 's');
