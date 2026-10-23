/* Lo que tapa la traspuesta — el video con el VISOR DE MÚSICA de Traspuesta (montanas-topograficas/musica.html, «Traspuesta suena»):
   las montañas reaccionan al audio de la canción, el actor de texto teclea la letra cuando el coro la canta, Hydra encima.
   El visor corre con su reloj manual (?reloj=manual): cada cuadro avanza 1/30 s con musica.paso(dt) y la pista se analiza en ese
   mismo reloj, así el video sale idéntico cada vez y sin cuadros perdidos. Math.random se siembra (420048) para que el banco de
   montañas también sea siempre el mismo.
   La coreografía (qué vista y qué Hydra en cada sección, cambios de montaña en las tijeras de Nobuto) vive en COREO.
     node video_musica.cjs <carpeta-de-entrega> [--fps 30] [--hasta segundos]
   Escribe <entrega>/<nombre>-visor-1920x1080.mp4 y su corte de 1280×720 (fuera de git) y visor-coreografia.json. */
const path = require('path'), fs = require('fs'), http = require('http'), { spawn, spawnSync } = require('child_process');
const { chromium } = require('playwright');
const MT = path.join(__dirname, '..', '..', 'montanas-topograficas');
const args = process.argv.slice(2), opc = {}, pos = [];
for (let i = 0; i < args.length; i++) args[i].startsWith('--') ? (opc[args[i].slice(2)] = args[++i]) : pos.push(args[i]);
const OUT = path.resolve(pos[0]), nombre = path.basename(OUT), P = JSON.parse(fs.readFileSync(path.join(OUT, 'partitura.json'), 'utf8'));
const planos = JSON.parse(fs.readFileSync(path.join(OUT, 'video-planos.json'), 'utf8'));
const fps = +(opc.fps || 30), W = 1920, H = 1080, DUR = Math.min(+(opc.hasta || P.duracion), P.duracion);
const wav = path.join(OUT, nombre + '.wav'), m4a = path.join(OUT, nombre + '.m4a');
const SEC = P.secciones, S16 = P.semicorchea, BAR = 16 * S16;

// ── la coreografía: lo que la música hace con el terreno, sección por sección ──
const COREO = [
  { t: 0, hace: 'normal', mezcla: 0, por: 'I punto gris: la pluma traza 420048 y el relieve respira con el aire; el actor escribe lo que sabe del terreno' },
  { t: SEC.II[0], hace: 'mixto', preset: 0, mezcla: .18, por: 'II casa: terreno + espectro (cada fila un instante); Hydra «eco» apenas' },
  { t: SEC.III[0], hace: 'mixto', preset: 1, auto: true, por: 'III coro: Hydra «rgb» sigue la actividad; cada tijera de Nobuto cambia de montaña con barrido' },
  { t: SEC.IV[0], hace: 'cascada', semilla: '420048', preset: 3, mezcla: .12, por: 'IV abrir: la cascada pura, la música dibuja la montaña (improvisar); Hydra «pixel» apenas' },
  { t: SEC.IV[0] + 14 * BAR, hace: 'cascada', preset: 2, auto: true, por: 'IV cambios y recorte: caleidoscopio' },
  { t: SEC.V[0], hace: 'mixto', preset: 0, auto: true, por: 'V liso: terreno + espectro con Hydra «eco» que se funde (la retícula se disuelve)' },
  { t: SEC.VI[0], hace: 'normal', semilla: '420048', mezcla: .25, por: 'VI coda: otra vez 420048, la pluma lo vuelve a trazar; Hydra se apaga' },
  { t: SEC.VI[0] + 6, hace: 'normal', mezcla: 0 },
];
for (const tj of P.tijeras) COREO.push({ t: tj.t, cambia: true, por: 'tijera ' + tj.tipo });
if (opc.hydra) COREO.push({ t: 1, hace: 'mixto', preset: +opc.hydra, mezcla: .7, por: 'prueba' });   // --hydra N: prueba corta con Hydra encendido
COREO.sort((a, b) => a.t - b.t);
// el guion del actor: cada renglón de la letra mientras el coro lo canta (en mayúsculas: la letra de un trazo); el título al final
const GUION = planos.letra.map((l) => [l.desde, l.hasta + .6, l.texto.toUpperCase()]).concat([[SEC.VI[0] + 9, P.duracion, 'LO QUE TAPA LA TRASPUESTA']]);

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
    let a = 420048 >>> 0; Math.random = () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  });
  await pag.goto(`http://127.0.0.1:${srv.address().port}/musica.html?reloj=manual&w=${W}&h=${H}&semilla=420048&oscuro=1&pista=x`);
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
      cambios += toca.filter((c) => c.cambia).length;
      await pag.evaluate(async (L) => {
        const m = window.musica;
        for (const c of L) {
          if (c.semilla) await m.otra(c.semilla);
          if (c.hace === 'normal') { m.cascada(false); } else if (c.hace === 'mixto') m.mixto(true); else if (c.hace === 'cascada') m.cascada(true);
          if (c.preset != null) m.hydra.usaPreset(c.preset);
          if (c.auto != null) m.S.mezclaAuto = c.auto;
          if (c.mezcla != null) { m.S.mezclaAuto = false; m.hydra.mezcla(c.mezcla); }
          if (c.cambia) { if (!m.cambia('tijera')) m.rellena(); m.rellena(); }
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
  for (const [i, o, extra] of [[mudo, final, ['-i', m4a, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'copy', '-shortest']], [final, ligero, ['-vf', 'scale=1280:720', '-c:v', 'libx264', '-crf', '27', '-preset', 'slow', '-c:a', 'copy']]]) {
    const r = spawnSync('ffmpeg', ['-n', '-v', 'error', '-i', i, ...extra, '-movflags', '+faststart', o], { stdio: 'inherit' }); if (r.status) throw new Error('ffmpeg ' + o);
  }
  fs.writeFileSync(path.join(OUT, 'visor-coreografia.json'), JSON.stringify({ visor: 'montanas-topograficas/musica.html (reloj manual)', fps, coreografia: COREO, guion: GUION, cambios_de_montana: estado.cambios, hydra: estado.hydra }, null, 1), { flag: 'wx' });
  for (const p of [final, ligero]) console.log(p, (fs.statSync(p).size / 2 ** 20).toFixed(1), 'MB');
})().catch((e) => { console.error(e); process.exit(1); });
