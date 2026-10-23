/* La lluvia que hizo los cráteres — el video con el VISOR DE MÚSICA de Traspuesta (montanas-topograficas/musica.html) sobre el campo
   de impactos 18: el terreno reacciona al audio, el actor de texto teclea la letra, Hydra encima con los presets de las canciones de
   terreno (HYDRA.md: tectónica en la lluvia y en el gran impacto, luciérnagas en la aguja). Reloj manual; Math.random sembrado (18).
     node video_musica.cjs <carpeta-de-entrega> [--fps 30] [--hasta segundos] */
const path = require('path'), fs = require('fs'), http = require('http'), { spawn, spawnSync } = require('child_process');
const { chromium } = require('playwright');
const MT = path.join(__dirname, '..', '..', 'montanas-topograficas');
const args = process.argv.slice(2), opc = {}, pos = [];
for (let i = 0; i < args.length; i++) args[i].startsWith('--') ? (opc[args[i].slice(2)] = args[++i]) : pos.push(args[i]);
const OUT = path.resolve(pos[0]), nombre = path.basename(OUT), P = JSON.parse(fs.readFileSync(path.join(OUT, 'partitura.json'), 'utf8'));
const fps = +(opc.fps || 30), W = 1920, H = 1080, DUR = Math.min(+(opc.hasta || P.duracion), P.duracion);
const wav = path.join(OUT, nombre + '.wav'), m4a = path.join(OUT, nombre + '.m4a');
const SC = P.secciones, T = (n) => SC.find((x) => x.num === n).t, GR = P.gran;
// ── la coreografía (presets: 1 rgb, 3 pixel, 5 curvas, 9 tectónica, 10 diferencia, 13 luciérnagas) ──
const COREO = [
  { t: 0, hace: 'normal', mezcla: 0, por: 'la lluvia: la pluma traza el campo de impactos' },
  { t: 14, hace: 'mixto', preset: 9, mezcla: .45, por: 'la lluvia arrecia: «tectónica», cada impacto un sismo' },
  { t: T('II'), hace: 'mixto', preset: 1, auto: true, por: 'footwork: Hydra «rgb»' },
  { t: T('III'), hace: 'normal', preset: 5, mezcla: .3, semilla: '18', por: 'taiko: la pluma vuelve; «curvas»' },
  { t: T('IV'), hace: 'mixto', preset: 9, mezcla: .65, por: 'footwork otra vez: «tectónica»' },
  { t: GR.t - .15, hace: 'cascada', preset: 3, mezcla: .95, por: 'el gran impacto: cascada y «pixel» al máximo' },
  { t: GR.t + P.compas, hace: 'mixto', preset: 10, mezcla: .55, por: 'lo que queda: «diferencia»' },
  { t: T('V'), hace: 'normal', preset: 13, mezcla: .5, por: 'la aguja: «luciérnagas» sobre las líneas del campo' },
];
if (opc.hydra) COREO.push({ t: 1, hace: 'mixto', preset: +opc.hydra, mezcla: .7, por: 'prueba' });
COREO.sort((a, b) => a.t - b.t);
const BONITA = { 'el pla ne ta nue ve no se pue de ver': 'el planeta nueve no se puede ver', 'ha bi ta en tre un cú mu lo de hie los': 'habita entre un cúmulo de hielos',
  'só lo lo co no ce mos': 'sólo lo conocemos', 'por los ob je tos': 'por los objetos', 'de ro ca y hie lo': 'de roca y hielo', 'que se re ú nen al re de dor de un va cí o': 'que se reúnen alrededor de un vacío',
  'u na tris te ro ca': 'una triste roca', 'com pues ta de a gua con ge la da': 'compuesta de agua congelada', 'gol pe a rá la su per fi cie': 'golpeará la superficie',
  'nues tra úl ti ma': 'nuestra última', 'es pe ran za': 'esperanza' };
const NOMBRE = { I: 'LA LLUVIA', II: 'FOOTWORK', III: 'TAIKO', IV: 'EL GRAN IMPACTO', V: 'LA AGUJA' };
const GUION = SC.map((e) => [e.t + .2, e.t + 4, NOMBRE[e.num]]);
GUION.push([GR.t, GR.t + P.compas, 'IMPACTO · ' + (GR.D / 1000).toFixed(1) + ' KM']);
function frases(evs, hueco) { evs = evs.slice().sort((a, b) => a.t - b.t); let g = []; const out = [];
  for (const e of evs) { if (g.length && e.t - (g.at(-1).t + g.at(-1).dur) > hueco) { out.push(g); g = []; } g.push(e); } if (g.length) out.push(g); return out; }
for (const [cap, hueco] of [['susurro', .3], ['coro', .35], ['viva', .7]])
  for (const g of frases(P.sabina.find((c) => c.capa === cap).eventos, hueco)) { const k = g.map((e) => e.texto).join(' '), fin = g.at(-1); GUION.push([g[0].t - .05, fin.t + Math.min(fin.dur, 2.5) + .5, (BONITA[k] || k).toUpperCase()]); }
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
    let a = 18 >>> 0; Math.random = () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  });
  await pag.goto(`http://127.0.0.1:${srv.address().port}/musica.html?reloj=manual&w=${W}&h=${H}&semilla=18&oscuro=1&pista=x`);
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
