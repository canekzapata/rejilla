/* Lo que el agua dibuja — la guitarra de cárcava (motor/carcava.js): el slide y el pulgar, cada uno a su capa estéreo 48 kHz,
   <carpeta>/<capa>.f32 (L,R entrelazados), más <carpeta>/zing.f32 (mono: el chirrido del vidrio solo, para medirlo).
     node render_node.cjs <carpeta> */
const fs = require('fs'), path = require('path'), C = require('./motor/carcava.js');
const dir = process.argv[2], P = JSON.parse(fs.readFileSync(path.join(dir, 'partitura.json'), 'utf8')), G = P.guitarra;
for (const cu of G.cuerdas) {
  const t0 = Date.now(), r = C.render({ dur: G.dur, fr: G.fr, semilla: G.semilla, cuerdas: [cu] }, 48000), N = r.L.length, x = new Float32Array(2 * N);
  let pk = 0; for (let i = 0; i < N; i++) { x[2 * i] = r.L[i]; x[2 * i + 1] = r.R[i]; pk = Math.max(pk, Math.abs(r.L[i]), Math.abs(r.R[i])); }
  if (pk > 0) for (let i = 0; i < 2 * N; i++) x[i] /= pk;
  const capa = cu.nombre === 'slide' ? 'guitarra' : cu.nombre;
  fs.writeFileSync(path.join(dir, capa + '.f32'), Buffer.from(x.buffer),{flag:'wx'});
  if (cu.entorchada) fs.writeFileSync(path.join(dir, 'zing.f32'), Buffer.from(r.zing.buffer),{flag:'wx'});
  console.log(capa.padEnd(10), (N / 48000).toFixed(1) + ' s', 'pico', pk.toFixed(3), (Date.now() - t0) + ' ms');
}
