/* La ciudad se hunde bailando — el video con el VISOR DE MÚSICA de Traspuesta (montanas-topograficas/musica.html). La coreografía
   NO vive aquí: es la partitura del video, coreografia-video.json (lámina inicial, pasos por sección, nombres, letra). Reloj manual;
   Math.random sembrado. Se lanza con «python hazvideo.py» (o directo):
     node video_musica.cjs <carpeta-de-entrega> [--fps 30] [--hasta segundos]
     node video_musica.cjs <carpeta-de-entrega> --cuadros 10,60,101,140,200 [--fps 6]   → PNGs de prueba en render/cuadros-prueba/, sin video */
const path = require('path'), fs = require('fs'), http = require('http'), { spawn, spawnSync } = require('child_process');
const { chromium } = require('playwright');
const MT = path.join(__dirname, '..', '..', 'montanas-topograficas');
const args = process.argv.slice(2), opc = {}, pos = [];
for (let i = 0; i < args.length; i++) args[i].startsWith('--') ? (opc[args[i].slice(2)] = args[++i]) : pos.push(args[i]);
const OUT = path.resolve(pos[0]), nombre = path.basename(OUT), P = JSON.parse(fs.readFileSync(path.join(OUT, 'partitura.json'), 'utf8'));
const CO = JSON.parse(fs.readFileSync(path.join(__dirname, 'coreografia-video.json'), 'utf8'));
const fps = +(opc.fps || 30), W = 1920, H = 1080, DUR = Math.min(+(opc.hasta || P.duracion), P.duracion);
const CUADROS = opc.cuadros ? opc.cuadros.split(',').map(Number) : null;
const wav = path.join(OUT, nombre + '.wav'), m4a = path.join(OUT, nombre + '.m4a');
const SC = P.secciones, T = (n) => SC.find((x) => x.num === n).t_real;          // tiempo real: el disco se rebaja
const VS = P.varispeed, real = (p) => { let i = 0; while (i + 1 < VS.length && VS[i + 1][0] < p) i++; const [p0, t0] = VS[i], [p1, t1] = VS[Math.min(i + 1, VS.length - 1)]; return p1 === p0 ? t0 : t0 + (t1 - t0) * (p - p0) / (p1 - p0); };
const COREO = CO.pasos.map((p) => ({ ...p, t: +(T(p.en) + (p.mas || 0)).toFixed(3) }));
COREO.sort((a, b) => a.t - b.t);
const BONITA = CO.letra_bonita, NOMBRE = CO.nombres_de_seccion;
const GUION = SC.map((e) => [e.t_real + .2, e.t_real + 4, NOMBRE[e.num]]);
function frases(evs, hueco) { evs = evs.slice().sort((a, b) => a.t - b.t); let g = []; const out = [];
  for (const e of evs) { if (g.length && e.t - (g.at(-1).t + g.at(-1).dur) > hueco) { out.push(g); g = []; } g.push(e); } if (g.length) out.push(g); return out; }
for (const [cap, hueco, disco] of [['lead', .5, true], ['coro', .4, true], ['mc', .3, false]])
  for (const g of frases(P.sabina.find((c) => c.capa === cap).eventos, hueco)) {
    const k = g.map((e) => e.texto).join(' '), fin = g.at(-1), ta = disco ? real(g[0].t) : g[0].t, tz = disco ? real(fin.t + Math.min(fin.dur, 2.5)) : fin.t + fin.dur;
    if (ta < P.inicio_disco) continue; GUION.push([ta - .05, tz + .5, (BONITA[k] || k).toUpperCase()]); }
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
    let a = 769 >>> 0; Math.random = () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  });
  await pag.goto(`http://127.0.0.1:${srv.address().port}/musica.html?reloj=manual&w=${W}&h=${H}&semilla=${CO.semilla_inicial}&oscuro=1&pista=x`);
  await pag.waitForFunction(() => window.musicaLista && window.musica && window.musica.A.modo === 'pista', null, { timeout: 120000 });
  await pag.evaluate((G) => { const m = window.musica; m.S.auto = false; m.X.guion = (t) => { for (const [a, z, s] of G) if (t >= a && t < z) return s; return null; }; }, GUION);
  // que el banco tenga montañas listas antes de empezar (el worker tarda 1–4 s por lámina)
  await pag.waitForFunction(() => window.musica.S.banco.length >= 3, null, { timeout: 120000 });
  const n = Math.ceil((CUADROS ? Math.max(...CUADROS) + .1 : DUR) * fps), mudo = path.join(OUT, '..', 'render', nombre + '-visor-mudo.mp4');
  fs.mkdirSync(path.dirname(mudo), { recursive: true });
  const dirP = path.join(OUT, '..', 'render', 'cuadros-prueba'); if (CUADROS) fs.mkdirSync(dirP, { recursive: true });
  const ff = CUADROS ? null : spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'png', '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '17', '-preset', 'medium', mudo], { stdio: ['pipe', 'inherit', 'inherit'] });
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
    if (CUADROS) { const k = CUADROS.findIndex((c) => Math.abs(c - t) < .5 / fps); if (k >= 0) await pag.screenshot({ path: path.join(dirP, `cuadro-${String(CUADROS[k]).padStart(5, '0')}s.png`) }); }
    else { const png = await pag.screenshot({ type: 'png' }); if (!ff.stdin.write(png)) await new Promise((r) => ff.stdin.once('drain', r)); }
    if (f % fps === 0) process.stderr.write(`\rvisor · ${f}/${n} cuadros · ${((Date.now() - t0) / 1000).toFixed(0)} s`);
  }
  if (ff) { ff.stdin.end(); await new Promise((r) => ff.on('close', r)); }
  const estado = await pag.evaluate(() => ({ cambios: window.musica.S.cambios, hydra: window.musica.hydra.listo, error: window.musica.hydra.error }));
  await nav.close(); srv.close();
  process.stderr.write(`\rvisor · ${n} cuadros en ${((Date.now() - t0) / 1000).toFixed(0)} s · cambios de montaña ${estado.cambios.length} · Hydra ${estado.hydra ? 'sí' : 'NO'} ${estado.error || ''}\n`);
  if (CUADROS) { console.log('cuadros de prueba:', dirP); return; }
  if (opc.hasta) { console.log('prueba:', mudo); return; }
  const final = path.join(OUT, nombre + '-visor-1920x1080.mp4'), ligero = path.join(OUT, nombre + '-visor-1280x720.mp4');
  for (const [i, o, extra] of [[mudo, final, ['-i', m4a, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '30', '-preset', 'medium', '-c:a', 'copy', '-shortest']], [final, ligero, ['-vf', 'scale=1280:720', '-c:v', 'libx264', '-crf', '27', '-preset', 'slow', '-c:a', 'copy']]]) {
    const r = spawnSync('ffmpeg', ['-n', '-v', 'error', '-i', i, ...extra, '-movflags', '+faststart', o], { stdio: 'inherit' }); if (r.status) throw new Error('ffmpeg ' + o);
  }
  fs.writeFileSync(path.join(OUT, 'visor-coreografia.json'), JSON.stringify({ visor: 'montanas-topograficas/musica.html (reloj manual)', fps, coreografia: COREO, partitura_del_video: 'coreografia-video.json', guion: GUION, cambios_de_montana: estado.cambios, hydra: estado.hydra }, null, 1), { flag: 'wx' });
  for (const p of [final, ligero]) console.log(p, (fs.statSync(p).size / 2 ** 20).toFixed(1), 'MB');
})().catch((e) => { console.error(e); process.exit(1); });
