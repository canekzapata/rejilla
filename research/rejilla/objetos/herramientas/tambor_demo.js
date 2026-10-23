// node herramientas/tambor_demo.js <etiqueta> — demos del tambor parlante a render/<et>-tambor-*.wav (+ .json)
const T = require('../motor/tambor.js'), SR = 48000, wav = require('./escribe_wav.js')(process.argv[2], 'tambor', SR);
const hecho = (nombre, dur, ev, meta) => wav(nombre, T.render({ dur, eventos: ev }, SR), meta, ev);
const t0 = Date.now();
const lam = { titulo_lamina: 'la física: el parche es una membrana circular (1 : 1.59 : 2.14 : 2.30 …, comprimida por el aire); apretar las cuerdas lo tensa: f ∝ √tensión',
  modos_lamina: [['centro', T.PARCHE.map((q, k) => [q, [1, .45, .3, .12, .1, .06, .05, .03][k]])], ['borde', T.PARCHE.map((q, k) => [q, [.25, .6, .55, .5, .4, .35, .3, .25][k]])]] };
// 1. los golpes: centro, borde, apagado, palo; un golpe suave y uno fuerte (el «boing»); y un golpe con apretón que sube 7 y regresa
hecho('golpes', 7, [{ t: .1, tipo: 'centro' }, { t: .7, tipo: 'borde' }, { t: 1.2, tipo: 'apagado' }, { t: 1.6, tipo: 'palo' },
  { t: 2.4, tipo: 'centro', v: .3 }, { t: 3, tipo: 'centro', v: 1 }, { t: 4, tipo: 'centro', v: .8, curva: [[0, 0], [.25, 7], [.6, 7], [.9, 0]] },
  { t: 5.2, tipo: 'palo', v: .8, curva: [[0, 0], [.4, -5]] }], { ...lam });
// 2. el tambor habla: tres frases (la del acento sube; la pregunta sube al final)
const frases = [{ t: .1, texto: 'el tambor habla' }, { t: 1.8, texto: 'canción del pájaro' }, { t: 3.8, texto: '¿me oyes?' }, { t: 5.2, texto: 'agua que corre, sombra blanca' }];
hecho('habla', 8.5, frases.map((f) => ({ ...f, tipo: 'habla', m: 45, dur: .2 })), { ...lam, silabas: frases.map((f) => T.silabas(f.texto).map((s) => (s.acento ? s.letras.toUpperCase() : s.letras)).join('-')) });
// 3. pregunta y respuesta: dos tambores (uno agudo y uno grave) contestándose
{ const ev = []; [['¿dónde está el agua?', 47, .1], ['bajo la piedra', 40, 1.6], ['¿quién la cuida?', 47, 3], ['la noche larga', 40, 4.3], ['la noche larga', 47, 5.8]].forEach(([texto, m, t]) => ev.push({ t, tipo: 'habla', texto, m, dur: .19, alto: m > 44 ? 5 : 3 }));
  hecho('cancion', 8, ev, { ...lam }); }
// 4. ritmo: un patrón de 12/8 con apretones (tres compases, el tercero con glisandos)
{ const ev = [], pat = [['centro', 0], ['apagado', 2], ['borde', 3], ['centro', 5], ['palo', 6], ['apagado', 8], ['borde', 9], ['centro', 10]], c = .17;
  for (let b = 0; b < 3; b++) pat.forEach(([tipo, k], i) => ev.push({ t: .1 + (b * 12 + k) * c, tipo, v: .6 + .3 * (k % 6 === 0), curva: b === 2 && i % 2 === 0 ? [[0, 0], [.18, i % 4 ? -3 : 6]] : [[0, b === 1 && i === 4 ? 4 : 0]] }));
  hecho('ritmo', 7.5, ev, { ...lam }); }
console.log('render', ((Date.now() - t0) / 1000).toFixed(1), 's');
