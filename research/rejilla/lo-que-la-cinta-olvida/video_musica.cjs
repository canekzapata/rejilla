/* Lo que la cinta olvida — el video con el VISOR DE MÚSICA de Traspuesta (montanas-topograficas/musica.html) sobre la llanura de
   meandros 26: el terreno reacciona al audio, el actor de texto teclea la letra (los tiempos de la banda están en tiempo de cinta y
   se llevan a tiempo real con el mapa de la partitura) y Hydra encima, con los presets de las canciones de terreno (HYDRA.md).
   Reloj manual; Math.random sembrado (26).
     node video_musica.cjs <carpeta-de-entrega> [--fps 30] [--hasta segundos] */
const path = require('path'), fs = require('fs'), http = require('http'), { spawn, spawnSync } = require('child_process');
const { chromium } = require('playwright');
const MT = path.join(__dirname, '..', '..', 'montanas-topograficas');
const args = process.argv.slice(2), opc = {}, pos = [];
for (let i = 0; i < args.length; i++) args[i].startsWith('--') ? (opc[args[i].slice(2)] = args[++i]) : pos.push(args[i]);
const OUT = path.resolve(pos[0]), nombre = path.basename(OUT), P = JSON.parse(fs.readFileSync(path.join(OUT, 'partitura.json'), 'utf8'));
const fps = +(opc.fps || 30), W = 1920, H = 1080, DUR = Math.min(+(opc.hasta || P.duracion), P.duracion);
const wav = path.join(OUT, nombre + '.wav'), m4a = path.join(OUT, nombre + '.m4a');
const VU = P.vueltas, M = P.mapa;
const real = (x) => { const T = M.tau, R = M.t; if (x <= T[0]) return R[0]; for (let i = 1; i < T.length; i++) if (x <= T[i]) return R[i - 1] + (R[i] - R[i - 1]) * (x - T[i - 1]) / (T[i] - T[i - 1]); return R.at(-1); };
// ── la coreografía (presets: 0 eco, 1 rgb, 6 erosión, 10 diferencia, 5 curvas, 3 pixel) ──
const COREO = [
  { t: 0, hace: 'normal', mezcla: 0, por: 'el sonidero se presenta: la pluma traza la llanura de meandros' },
  { t: VU[0].t0, hace: 'mixto', preset: 1, auto: true, por: 'la cumbia: terreno + espectro, Hydra «rgb»' },
  { t: VU[4].t0, hace: 'mixto', preset: 6, mezcla: .6, por: 'lo más rebajado: «erosión», el eco se escurre' },
  { t: VU[7].t0, hace: 'mixto', preset: 10, mezcla: .5, por: 'lo vivo: «diferencia», sólo se ve lo que cambia sobre los lagos' },
  { t: P.fin_cinta, hace: 'normal', preset: 5, mezcla: .35, semilla: '26', por: 'la cinta se detiene: la pluma vuelve a trazar; «curvas»' },
];
for (const lg of P.lagos) COREO.push({ t: lg.t1 - .2, hace: 'cascada', preset: 3, mezcla: .8, por: 'el corte: cascada y «pixel»' }, { t: lg.t1 + 2.2, hace: 'mixto', preset: lg.vuelta < 5 ? 1 : 6, mezcla: .55, por: 'el lago se queda' });
if (opc.hydra) COREO.push({ t: 1, hace: 'mixto', preset: +opc.hydra, mezcla: .7, por: 'prueba' });
COREO.sort((a, b) => a.t - b.t);
const BONITA = { 'sa lu dos a la de mu chas vuel tas': 'saludos a la de muchas vueltas', 'a la que no lle va a na die': 'a la que no lleva a nadie',
  'des de la lla nu ra de los me an dros': 'desde la llanura de los meandros', 'pa ra to dos los que se que da ron': 'para todos los que se quedaron',
  'la de mu chas vuel tas': 'la de muchas vueltas', 'la que no lle va a na die': 'la que no lleva a nadie', 'zar pó con la bo de ga': 'zarpó con la bodega',
  'lle na de si len cio': 'llena de silencio', 'y u na so la or den': 'y una sola orden', 'en la cin ta': 'en la cinta', 're gre sa lo que ve as': 'regresa lo que veas',
  'u na vuel ta más': 'una vuelta más', 'la vuel ta nú me ro que ya na die cuen ta': 'la vuelta número que ya nadie cuenta', 'o tra vuel ta pa ra los que se que da ron': 'otra vuelta para los que se quedaron',
  'me que dé por que ol vi dar la mi sión': 'me quedé porque olvidar la misión', 'e ra lo más pa re ci do a lle gar': 'era lo más parecido a llegar',
  'lo que vuel ve es el re la to del re gre so': 'lo que vuelve es el relato del regreso', 'la voz que di ce re gre so mien tras se a le ja': 'la voz que dice regreso mientras se aleja',
  'se guir a pun tan do la an te na': 'seguir apuntando la antena', 'a don de ya no con tes ta na die': 'a donde ya no contesta nadie' };
const GUION = [[.2, 4, 'LO QUE LA CINTA OLVIDA']];
for (const vu of VU) GUION.push([vu.t0 + .1, vu.t0 + 3, 'VUELTA ' + vu.n + (vu.corte ? ' · CORTE' : '')]);
for (const lg of P.lagos) GUION.push([lg.t1, lg.t1 + 3, 'LAGO DE HERRADURA']);
function frases(evs, hueco) { evs = evs.slice().sort((a, b) => a.t - b.t); let g = []; const out = [];
  for (const e of evs) { if (g.length && e.t - (g.at(-1).t + g.at(-1).dur) > hueco) { out.push(g); g = []; } g.push(e); } if (g.length) out.push(g); return out; }
const enReal = (e) => ({ ...e, t: real(e.t), dur: real(e.t + e.dur) - real(e.t) });
for (const [evs, hueco] of [[P.sabina[0].eventos.map(enReal), .4], [P.sabina[1].eventos.map(enReal), .5], [P.coros.S.map(enReal), .5], [P.sabina[2].eventos, .6]])
  for (const g of frases(evs, hueco)) { const k = g.map((e) => e.texto).join(' '), fin = g.at(-1); GUION.push([g[0].t - .05, fin.t + Math.min(fin.dur, 2.5) + .5, (BONITA[k] || k).toUpperCase()]); }
GUION.sort((a, b) => a[0] - b[0]);
for (let i = 0; i + 1 < GUION.length; i++) if (GUION[i][1] > GUION[i + 1][0]) GUION[i][1] = GUION[i + 1][0];

const TIPOS = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.css': 'text/css' };
const srv = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  if (url === '/pista') { res.writeHead(200, { 'Content-Type': 'audio/wav' }); return fs.createReadStream(wav).pipe(res); }   // sólo la pista de esta entrega
  const f = path.join(MT, url);
  if (!f.startsWith(MT) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TIPOS[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(res);
});

(async () => {
  await new Promise((r) => srv.listen(0, '127.0.0.1', r));
  // el 2D en CPU: con SwiftShader Chromium también emulaba el lienzo 2D en GL por software (medido: 2 s por cuadro); Hydra sigue en WebGL
  const nav = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--disable-accelerated-2d-canvas'] });
  const pag = await nav.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  pag.on('pageerror', (e) => console.error('error en la página:', e.message));
  await pag.addInitScript(() => {                                     // Math.random sembrado (mulberry32): el banco de montañas es siempre el mismo
    let a = 26 >>> 0; Math.random = () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  });
  await pag.goto(`http://127.0.0.1:${srv.address().port}/musica.html?reloj=manual&w=${W}&h=${H}&semilla=26&oscuro=1&pista=x`);
  await pag.waitForFunction(() => window.musicaLista && window.musica && window.musica.A.modo === 'pista', null, { timeout: 120000 });
  await pag.evaluate((G) => { const m = window.musica; m.S.auto = false; m.X.guion = (t) => { for (const [a, z, s] of G) if (t >= a && t < z) return s; return null; }; }, GUION);
  // que el banco tenga montañas listas antes de empezar (el worker tarda 1–4 s por lámina)
  await pag.waitForFunction(() => window.musica.S.banco.length >= 3, null, { timeout: 120000 });
  const n = Math.ceil(DUR * fps), mudo = path.join(OUT, '..', 'render', nombre + '-visor-mudo.mp4');
  fs.mkdirSync(path.dirname(mudo), { recursive: true });
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'png', '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '17', '-preset', 'medium', mudo], { stdio: ['pipe', 'inherit', 'inherit'] });
  let ci = 0, cambios = 0; const t0 = Date.now();
  for (let f = 0; f < n; f++) {
    const t = f / fps, toca = [];
    while (ci < COREO.length && COREO[ci].t <= t + 1e-6) toca.push(COREO[ci++]);
    if (toca.length) {
      
      await pag.evaluate(async (L) => {
        const m = window.musica;
        for (const c of L) {
          if (c.semilla) await m.otra(c.semilla);
          if (c.hace === 'normal') { m.cascada(false); } else if (c.hace === 'mixto') m.mixto(true); else if (c.hace === 'cascada') m.cascada(true);
          if (c.preset != null) m.hydra.usaPreset(c.preset);
          if (c.auto != null) m.S.mezclaAuto = c.auto;
          if (c.mezcla != null) { m.S.mezclaAuto = false; m.hydra.mezcla(c.mezcla); }
          
        }
      }, toca);
    }
    await pag.evaluate((dt) => window.musica.paso(dt), f === 0 ? 0 : 1 / fps);
    const png = await pag.screenshot({ type: 'png' });
    if (!ff.stdin.write(png)) await new Promise((r) => ff.stdin.once('drain', r));
    if (f % fps === 0) process.stderr.write(`\rvisor · ${f}/${n} cuadros · ${((Date.now() - t0) / 1000).toFixed(0)} s`);
  }
  ff.stdin.end(); await new Promise((r) => ff.on('close', r));
  const estado = await pag.evaluate(() => ({ cambios: window.musica.S.cambios, hydra: window.musica.hydra.listo, error: window.musica.hydra.error }));
  await nav.close(); srv.close();
  process.stderr.write(`\rvisor · ${n} cuadros en ${((Date.now() - t0) / 1000).toFixed(0)} s · cambios de montaña ${estado.cambios.length} · Hydra ${estado.hydra ? 'sí' : 'NO'} ${estado.error || ''}\n`);
  if (opc.hasta) { console.log('prueba:', mudo); return; }
  const final = path.join(OUT, nombre + '-visor-1920x1080.mp4'), ligero = path.join(OUT, nombre + '-visor-1280x720.mp4');
  for (const [i, o, extra] of [[mudo, final, ['-i', m4a, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '30', '-preset', 'medium', '-c:a', 'copy', '-shortest']], [final, ligero, ['-vf', 'scale=1280:720', '-c:v', 'libx264', '-crf', '27', '-preset', 'slow', '-c:a', 'copy']]]) {
    const r = spawnSync('ffmpeg', ['-n', '-v', 'error', '-i', i, ...extra, '-movflags', '+faststart', o], { stdio: 'inherit' }); if (r.status) throw new Error('ffmpeg ' + o);
  }
  fs.writeFileSync(path.join(OUT, 'visor-coreografia.json'), JSON.stringify({ visor: 'montanas-topograficas/musica.html (reloj manual)', fps, coreografia: COREO, guion: GUION, cambios_de_montana: estado.cambios, hydra: estado.hydra }, null, 1), { flag: 'wx' });
  for (const p of [final, ligero]) console.log(p, (fs.statSync(p).size / 2 ** 20).toFixed(1), 'MB');
})().catch((e) => { console.error(e); process.exit(1); });
