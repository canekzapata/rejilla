/* El río no tiene tronco — el video con el VISOR DE MÚSICA de Traspuesta (montanas-topograficas/musica.html, «Traspuesta suena»):
   las montañas reaccionan al audio de la canción, el actor de texto teclea la letra cuando el coro la canta, Hydra encima.
   El visor corre con su reloj manual (?reloj=manual): cada cuadro avanza 1/30 s con musica.paso(dt) y la pista se analiza en ese
   mismo reloj, así el video sale idéntico cada vez y sin cuadros perdidos. Math.random se siembra (412601) para que el banco de
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
const fps = +(opc.fps || 30), W = 1920, H = 1080, DUR = Math.min(+(opc.hasta || P.duracion), P.duracion);
const wav = path.join(OUT, nombre + '.wav'), m4a = path.join(OUT, nombre + '.m4a');
const SEC = P.secciones, TT = P.tiempos;

// ── la coreografía: lo que la música hace con el terreno, sección por sección ──
const COREO = [
  { t: 0, hace: 'normal', mezcla: 0, por: 'I las fuentes: la pluma traza el delta 412601; el relieve respira con la lluvia y los afluentes' },
  { t: SEC.II[0], hace: 'mixto', preset: 0, mezcla: .15, por: 'II el río: terreno + espectro (cada fila un instante); Hydra «eco» apenas; la letra del verso' },
  { t: TT.apice, hace: 'cascada', preset: 1, auto: true, por: 'III el delta: la cascada, la música dibuja la montaña; Hydra «rgb» sigue la actividad (hyperpop)' },
  { t: TT.apice + 8 * P.paso, hace: 'mixto', preset: 2, auto: true, por: 'III el delta: caleidoscopio — un río que se abre en cinco' },
  { t: TT.mar, hace: 'mixto', preset: 0, mezcla: .55, por: 'IV el mar (Scelsi): Hydra «eco» funde todo en una sola superficie' },
  { t: TT.mar + 18, hace: 'normal', mezcla: .3, por: 'IV el mar: se apaga Hydra, sólo el delta y su pluma' },
  { t: TT.fin - 6, hace: 'normal', mezcla: 0 },
];
if (opc.hydra) COREO.push({ t: 1, hace: 'mixto', preset: +opc.hydra, mezcla: .7, por: 'prueba' });
COREO.sort((a, b) => a.t - b.t);
// el guion del actor: cada renglón de la letra mientras el coro lo canta (en mayúsculas: la letra de un trazo); «mar»; el título
const GUION = [];
for (const [k, versos] of [['II', P.letra.verso], ['III', P.letra.estribillo]]) {
  const S = P.coros[k].S; let i = 0;
  for (const v of versos) { const n = v.split(' ').length, sil = S.slice(i, i + n); i += n; const fin = sil.at(-1);
    GUION.push([sil[0].t - .05, fin.t + Math.min(fin.dur, 2.5) + .6, v.replace(/ /g, '').length ? v : v]); }
}
const BONITA = { 'el a gua no re cuer da la mon ta ña': 'el agua no recuerda la montaña', 'ba ja con el nom bre de o tro rí o': 'baja con el nombre de otro río',
  'ca da a rro yo que me al can za': 'cada arroyo que me alcanza', 'se vuel ve mi voz y yo la su ya': 'se vuelve mi voz y yo la suya', 'no ten go tron co': 'no tengo tronco',
  'ten go de sem bo ca du ras': 'tengo desembocaduras', 'ca da bra zo di ce o tra vez lo que di je': 'cada brazo dice otra vez lo que dije', 'lle go al mar por to das par tes': 'llego al mar por todas partes' };
for (const g of GUION) g[2] = (BONITA[g[2]] || g[2]).toUpperCase();
GUION.push([TT.mar + 3, TT.mar + 26, 'MAR'], [TT.fin - 9, P.duracion, 'EL RÍO NO TIENE TRONCO']);

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
    let a = 412601 >>> 0; Math.random = () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  });
  await pag.goto(`http://127.0.0.1:${srv.address().port}/musica.html?reloj=manual&w=${W}&h=${H}&semilla=412601&oscuro=1&pista=x`);
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
  for (const [i, o, extra] of [[mudo, final, ['-i', m4a, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'copy', '-shortest']], [final, ligero, ['-vf', 'scale=1280:720', '-c:v', 'libx264', '-crf', '27', '-preset', 'slow', '-c:a', 'copy']]]) {
    const r = spawnSync('ffmpeg', ['-n', '-v', 'error', '-i', i, ...extra, '-movflags', '+faststart', o], { stdio: 'inherit' }); if (r.status) throw new Error('ffmpeg ' + o);
  }
  fs.writeFileSync(path.join(OUT, 'visor-coreografia.json'), JSON.stringify({ visor: 'montanas-topograficas/musica.html (reloj manual)', fps, coreografia: COREO, guion: GUION, cambios_de_montana: estado.cambios, hydra: estado.hydra }, null, 1), { flag: 'wx' });
  for (const p of [final, ligero]) console.log(p, (fs.statSync(p).size / 2 ** 20).toFixed(1), 'MB');
})().catch((e) => { console.error(e); process.exit(1); });
