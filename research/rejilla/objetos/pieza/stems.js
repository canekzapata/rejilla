// node pieza/stems.js <etiqueta> [stem …] — renderiza cada objeto de «el tiempo es la altura» a render/<et>-pieza-<stem>.wav
// (+ .json con el pico y los eventos). Sin lista: todos. Cada stem es un objeto que toca su voz del canon (partitura.js).
const P = require('./partitura.js'), SR = 48000, ET = process.argv[2], wav = require('../herramientas/escribe_wav.js')(ET, 'pieza', SR);
const Cuerda = require('../motor/cuerda.js'), Metal = require('../motor/metal.js'), Tambor = require('../motor/tambor.js'), VozAgua = require('../motor/vozagua.js');
const Objeto = require('../motor/objeto.js'), Piano = require('../motor/piano.js'), Pajaro = require('../motor/pajaro.js');
const Waterphone = require('../motor/waterphone.js'), Gong = require('../motor/gong.js'), Agua = require('../motor/agua.js');
const { TC, DUR } = P, hz = (m) => 440 * Math.pow(2, (m - 69) / 12);
const suma = (...ys) => { const o = new Float32Array(Math.ceil(DUR * SR)); ys.forEach((y) => { for (let i = 0; i < Math.min(o.length, y.length); i++) o[i] += y[i]; }); return o; };
const pide = process.argv.slice(3), quiere = (s) => !pide.length || pide.includes(s);
const lapso = (V) => (n) => (n.t - V.notas[0].t) / (V.sale - V.notas[0].t);   // 0 → 1 a lo largo de la voz
// iguala lo de después de la convergencia con lo de antes: cada transformación cambia el nivel (el pizz-house del contrabajo,
// la flauta que se vuelve golpe y el piano con goma quedaban 16-30 dB abajo de su propio antes: medido en p1)
const rmsActivo = (y, a, b) => { const c = []; for (let i = Math.floor(a * SR); i + 4800 <= Math.min(y.length, b * SR); i += 4800) { let e = 0; for (let j = i; j < i + 4800; j++) e += y[j] * y[j]; c.push(e / 4800); }
  const mx = Math.max(...c); const v = c.filter((q) => q > mx * 1e-4); return Math.sqrt(v.reduce((x, q) => x + q, 0) / Math.max(1, v.length)); };
function iguala(y, V) {
  const g = Math.min(8, Math.max(1, .9 * rmsActivo(y, V.entra, TC) / (rmsActivo(y, TC + .3, V.sale) + 1e-12)));
  for (let i = Math.floor((TC - .05) * SR); i < y.length; i++) y[i] *= 1 + (g - 1) * Math.min(1, (i / SR - TC + .05) / .35);
  console.log('  iguala', V.nombre, 'después ×' + g.toFixed(2)); return y;
}
const t0 = Date.now(), reloj = () => ((Date.now() - t0) / 1000).toFixed(0) + ' s';

// contrabajo: arco antes de la convergencia; después, pizz que se vuelve house (casa 0 → 1 en su última vuelta)
if (quiere('contrabajo')) {
  const V = P.voz('contrabajo'), ev = V.notas.map((n) => n.despues
    ? { t: n.t, m: n.m, dur: n.dur * .9, tipo: 'pizz', v: n.acento ? .9 : .7, casa: Math.min(1, n.j / 20) }
    : { t: n.t, m: n.m, dur: n.dur * .97, tipo: 'arco', v: n.acento ? .75 : .55 });
  wav('contrabajo', iguala(Cuerda.render({ dur: DUR, instrumento: 'contrabajo', eventos: ev }, SR), V), { voz: V.nombre, r: V.r }, ev); console.log(reloj());
}
// trombón: abierto con growl en los acentos; después, plunger que abre en cada nota
if (quiere('trombon')) {
  const V = P.voz('trombon'), antes = [], despues = [], wah = [[0, .1]];
  V.notas.forEach((n) => {
    const e = { t: n.t, m: n.m, dur: n.dur - .04, v: n.acento ? .85 : .65, tipo: n.acento && !n.despues ? 'growl' : n.inicio && 'ptkc'.includes(n.inicio) ? 'lengua' : 'normal' };
    (n.despues ? despues : antes).push(e);
    if (n.despues) wah.push([n.t, .05], [n.t + n.dur * .6, n.acento ? 1 : .6], [n.t + n.dur, .15]);
  });
  wav('trombon', iguala(suma(Metal.render({ dur: DUR, voz: 'trombon', notas: antes }, SR), Metal.render({ dur: DUR, voz: 'trombon', sordina: 'plunger', wah, notas: despues }, SR)), V),
    { voz: V.nombre, r: V.r }, antes.concat(despues)); console.log(reloj());
}
// tambor: cada sílaba un golpe (el ataque elige el golpe), el acento aprieta; después, palo y apretones más hondos
if (quiere('tambor')) {
  const V = P.voz('tambor'), ev = V.notas.map((n) => {
    const tipo = n.despues && n.acento ? 'palo' : 'ptkbdgcq'.includes(n.inicio) ? 'palo' : 'sfjzx'.includes(n.inicio) ? 'borde' : 'centro';
    const curva = n.despues ? [[0, 0], [.06, n.acento ? 4 : 0], [n.dur * 1.4, n.acento ? -3 : -1]] : [[0, 0], [.05, n.acento ? 2 : 0]];
    return { t: n.t, tipo, m: n.m, v: n.acento ? .9 : .65, curva };
  });
  wav('tambor', Tambor.render({ dur: DUR, eventos: ev }, SR), { voz: V.nombre, r: V.r }, ev); console.log(reloj());
}
// la voz de agua: canta la letra; aprende a hablar (voz 0 → 1) hasta la convergencia; después, dos vocales en los acentos.
// Coda: la voz sola dice el último verso a la mitad de tempo, una octava abajo (r = 1/2)
if (quiere('vozagua')) {
  const V = P.voz('vozagua'), PAREJA = { a: 'i', e: 'o', i: 'a', o: 'e', u: 'a' };
  const vocal = (s) => { const q = s.normalize('NFD').replace(/[̀-ͯ]/g, '').match(/[aeiou]/); return q ? q[0] : 'a'; };
  const ev = V.notas.map((n) => ({ t: n.t, dur: n.dur * .95, texto: n.silaba, nota: n.m, modo: 'canto', v: n.acento ? .8 : .65,
    voz: n.despues ? 1 : Math.max(0, Math.min(1, (n.t - V.entra) / (TC - V.entra))), doble: n.despues && n.acento ? PAREJA[vocal(n.silaba)] : undefined }));
  const coda = P.SUJETO.notas.filter((n) => n.verso === 3), b0 = coda[0].b, tc = 168;
  coda.forEach((n) => ev.push({ t: tc + (n.b - b0) * P.BEAT * 2, dur: n.d * P.BEAT * 2 * .95, texto: n.silaba, nota: n.m - 12, modo: n.acento ? 'canto' : 'gargara', v: .75, voz: 1, doble: n.acento ? PAREJA[vocal(n.silaba)] : undefined }));
  wav('vozagua', VozAgua.render({ dur: DUR, eventos: ev }, SR), { voz: V.nombre, r: V.r }, ev); console.log(reloj());
}
// el objeto que cambia: saxofón → flauta antes de la convergencia; flauta → golpe (barra) en su última vuelta
if (quiere('sax')) {
  const V = P.voz('sax'), PU = Objeto.PURO;
  const entre = (a, b, u) => { const A = PU[a], B = PU[b], o = {}; for (const k of ['pos', 'perdida', 'brillo', 'disp', 'soplo', 'ruido']) o[k] = A[k] + (B[k] - A[k]) * u; o.w = A.w.map((x, i) => x + (B.w[i] - x) * u); return o; };
  const tramos = [[0, 'saxofon', 'saxofon', 1], [TC - 30, 'saxofon', 'flauta', TC], [TC, 'flauta', 'golpe', V.sale - 4]];
  const em = (t) => { for (let i = tramos.length - 1; i >= 0; i--) if (t >= tramos[i][0]) { const [a0, a, b, a1] = tramos[i]; return entre(a, b, Math.min(1, Math.max(0, (t - a0) / (a1 - a0)))); } return entre('saxofon', 'saxofon', 0); };
  const N = V.notas, nota = (t) => { let m = N[0].m; for (const n of N) { if (n.t > t) break; m = n.m; } return hz(m); };
  // el soplo de cada nota; después de la convergencia cada soplo se acorta (de la nota entera a un golpe de 20 ms)
  const largo = (n) => n.despues ? Math.max(.02, n.dur * .92 * (1 - (n.t - TC) / (V.sale - TC))) : n.dur * .92;
  const soplo = (t) => { let k = -1; for (let i = 0; i < N.length && N[i].t <= t; i++) k = i; if (k < 0) return 0; const n = N[k], u = t - n.t; return u < largo(n) ? Math.min(1, u / .03) * (n.acento ? 1 : .8) : 0; };
  const golpes = N.filter((n) => n.despues).map((n) => [n.t + .004, Math.min(.9, .2 + (n.t - TC) / (V.sale - TC))]);
  const c = { dur: DUR, f: nota, w: (t) => em(t).w, pos: (t) => em(t).pos, perdida: (t) => em(t).perdida, brillo: (t) => em(t).brillo, disp: (t) => em(t).disp, soplo, ruido: (t) => em(t).ruido, golpes, vibrato: [4.8, .03] };
  wav('sax', iguala(Objeto.render(c, SR), V), { voz: V.nombre, r: V.r, tramos }, N.map((n) => ({ t: n.t, dur: n.dur, m: n.m }))); console.log(reloj());
}
// piano: sin preparar; después, los acentos con tornillo (campanas) y lo demás con goma
if (quiere('piano')) {
  const V = P.voz('piano'), ev = V.notas.map((n) => ({ t: n.t, m: n.m, v: n.acento ? .8 : .55, dur: n.dur * 1.2, prep: n.despues ? (n.acento ? Piano.PREP.tornillo : Piano.PREP.goma) : null }));
  wav('piano', iguala(Piano.render({ dur: DUR, eventos: ev }, SR), V), { voz: V.nombre, r: V.r }, ev); console.log(reloj());
}
// pájaro: canta su voz (cada nota con el ornamento de entrada); después, la segunda voz de la siringe silba la tónica en los acentos
if (quiere('pajaro')) {
  const V = P.voz('pajaro'), t1 = V.notas[0].t, ev = [{ t: t1, tipo: 'canto', v: .6, dur: V.sale - t1, notas: V.notas.map((n) => [n.t - t1, n.m, n.dur * .8]) }];
  V.notas.filter((n) => n.despues && n.acento).forEach((n) => ev.push({ t: n.t, tipo: 'silbido', voz: 1, m: P.TONICA + V.semi, m2: P.TONICA + V.semi - .5, dur: n.dur * 1.6, v: .4 }));
  wav('pajaro', Pajaro.render({ dur: DUR, eventos: ev }, SR), { voz: V.nombre, r: V.r }, ev); console.log(reloj());
}
// el ambiente: waterphone (niebla del principio y gemido del final), gongs (cada entrada, la convergencia, las salidas, el final)
// y agua (burbujeo al empezar; la ola al final)
if (quiere('waterphone')) {
  const ev = [{ t: 0, tipo: 'bola', dur: 14, v: .5, agua: 1, ola: .2 }, { t: 1, tipo: 'arco', vara: 2, dur: 9, v: .5, agua: 2, ola: .15 }, { t: 6, tipo: 'arco', vara: 13, dur: 8, v: .35, agua: 3, ola: .22 },
    { t: 112, tipo: 'arco', vara: 9, dur: 6, v: .35, agua: 1, ola: .4 }, { t: 160, tipo: 'arco', vara: 4, dur: 14, v: .5, agua: 3, ola: .12 }, { t: 166, tipo: 'arco', vara: 17, dur: 12, v: .35, agua: 2.5, ola: .18 },
    { t: 176, tipo: 'bola', dur: 16, v: .45, agua: 2, ola: .1 }];
  wav('waterphone', Waterphone.render({ dur: DUR, eventos: ev }, SR), {}, ev); console.log(reloj());
}
if (quiere('gong')) {
  const ev = [];
  P.VOCES.forEach((v, k) => { const m = P.TONICA + 12 * Math.log2(v.r) + 12 * (v.r < 1 ? 1 : 0); if (k) ev.push({ t: v.entra - .05, tipo: 'cruce', m, v: .45, abre: k % 2 ? 4 : -4 }); });
  ev.push({ t: TC - 9, tipo: 'roce', dur: 9, v: .6 }, { t: TC, tipo: 'tamtam', v: 1, dureza: .6 });
  P.VOCES.forEach((v) => ev.push({ t: P.voz(v.nombre).sale, tipo: 'opera', m: 79 + 12 * Math.log2(v.r), v: .35, sube: 2 }));
  ev.push({ t: 186, tipo: 'cruce', m: P.TONICA, v: .8, abre: 12 });
  wav('gong', Gong.render({ dur: DUR, eventos: ev }, SR), {}, ev); console.log(reloj());
}
if (quiere('agua')) {
  const ev = [{ t: 2, tipo: 'burbujeo', dur: 16, v: .5 }, { t: TC + .02, tipo: 'gota', m: P.TONICA + 36, v: .8 }, { t: 158, tipo: 'palo', dur: 6, m: 84, v: .6 }, { t: 163, tipo: 'ola', dur: 12, v: .8 }];
  wav('agua', Agua.render({ dur: DUR, eventos: ev }, SR), {}, ev); console.log(reloj());
}
