// node herramientas/gong_demo.js <etiqueta> — demos del gong a render/<et>-gong-*.wav (+ .json)
const G = require('../motor/gong.js'), SR = 48000, wav = require('./escribe_wav.js')(process.argv[2], 'gong', SR);
const hecho = (nombre, dur, ev, meta) => wav(nombre, G.render({ dur, eventos: ev }, SR), meta, ev);
const t0 = Date.now(), TT = G.modosTamtam(9);
const lam = { titulo_lamina: 'la física: tam-tam (90 modos cada vez más densos; los agudos florecen tarde) · gong de ópera (un modo dominante)',
  modos_lamina: [['tam-tam', TT.filter((q) => q <= 40).map((q) => [q, Math.min(1, Math.pow(q, -.4))])], ['gong de ópera', G.OPERA], ['dos alturas', [[1, 1], [1.02, .85], [2.09, .25], [2.63, .1]]]] };
// 1. tam-tam: un golpe suave (casi sin florecer) y uno fuerte (el brillo crece tarde)
hecho('tam-tam', 11, [{ t: .1, tipo: 'tamtam', v: .35, dureza: .3 }, { t: 4, tipo: 'tamtam', v: 1, dureza: .6 }], { ...lam });
// 2. ópera de Pekín: el xiaoluo que sube y el daluo que baja, en un patrón de luogu
{ const ev = []; [[0, 'x'], [.5, 'x'], [.75, 'x'], [1.25, 'd'], [2.25, 'x'], [2.5, 'x'], [2.75, 'd'], [3.5, 'x'], [4, 'd']].forEach(([t, k]) =>
    ev.push(k === 'x' ? { t: .1 + t, tipo: 'opera', m: 79, v: .8, sube: 3 } : { t: .1 + t, tipo: 'opera', m: 62, v: .9, sube: -3.5 }));
  hecho('opera', 7.5, ev, { ...lam }); }
// 3. dos alturas que se cruzan: golpes sueltos en distintas notas y aperturas (la quinta golpea dos veces)
hecho('cruce', 12, [{ t: .1, tipo: 'cruce', m: 64, v: .8, abre: 4 }, { t: 2.7, tipo: 'cruce', m: 59, v: .8, abre: 7 }, { t: 5.3, tipo: 'cruce', m: 67, v: .7, abre: 2 },
  { t: 7.6, tipo: 'cruce', m: 55, v: .9, abre: 12 }, { t: 8.4, tipo: 'cruce', m: 62, v: .6, abre: 5 }], { ...lam });
// 4. el arco en el borde del tam-tam
hecho('arco', 10, [{ t: .1, tipo: 'arco', dur: 6, v: .8 }], { ...lam });
// 5. escena: roce grave, golpe de tam-tam, gongs que se cruzan encima
hecho('escena', 12, [{ t: .1, tipo: 'roce', dur: 5, v: .7 }, { t: 2.5, tipo: 'tamtam', v: .8 }, { t: 4, tipo: 'cruce', m: 66, v: .6, abre: 5 }, { t: 5.5, tipo: 'cruce', m: 61, v: .6, abre: -5 },
  { t: 6.5, tipo: 'opera', m: 79, v: .6, sube: 3 }, { t: 7, tipo: 'opera', m: 79, v: .6, sube: 3 }], { ...lam });
console.log('render', ((Date.now() - t0) / 1000).toFixed(1), 's');
