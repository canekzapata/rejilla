// node herramientas/barrido.js — ¿en qué soplo toca cada objeto su nota (y no otro registro)? mapa nota × soplo
const O = require('../motor/objeto.js'), sr = 48000, C = O.curva, hz = (m) => 440 * Math.pow(2, (m - 69) / 12);
function f0de(y) {
  const s = y.subarray(Math.floor(.4 * sr), Math.floor(.9 * sr)); let best = 0, lag = 0;
  for (let L = 20; L < 1200; L++) { let c = 0, e1 = 0, e2 = 0; for (let i = 0; i < 6000; i += 2) { c += s[i] * s[i + L]; e1 += s[i] * s[i]; e2 += s[i + L] * s[i + L]; } const v = c / Math.sqrt(e1 * e2 + 1e-20); if (v > best + .02 || (v > best * .97 && lag && Math.abs(L - 2 * lag) < 3 === false && L < lag)) { best = v; lag = L; } }
  let rms = 0; for (const v of s) rms += v * v; return [sr / lag, best, Math.sqrt(rms / s.length)];
}
for (const obj of ['saxofon', 'flauta']) {
  console.log('\n' + obj + '   (cents respecto a la nota; · = no suena)');
  const soplos = obj === 'saxofon' ? [.7, .74, .78, .85] : [.7, .8, .9, 1, 1.1, 1.2, 1.35];
  console.log('nota  ' + soplos.map((s) => String(s).padStart(7)).join(''));
  for (const m of [45, 50, 55, 57, 60, 64, 67, 69, 72, 76]) {
    let fila = String(m).padEnd(6);
    for (const sop of soplos) {
      const p = O.PURO[obj]; const y = O.render({ dur: 1, f: C(hz(m)), w: C(p.w), pos: C(p.pos), perdida: C(p.perdida), brillo: C(p.brillo), disp: C(0),
        soplo: C([[0, 0], [.04, sop], [1, sop]]), ruido: C(p.ruido) }, sr);
      const [f, per, rms] = f0de(y);
      fila += (rms < .01 || per < .5 ? '·' : String(Math.round(1200 * Math.log2(f / hz(m))))).padStart(7);
    }
    console.log(fila);
  }
}
