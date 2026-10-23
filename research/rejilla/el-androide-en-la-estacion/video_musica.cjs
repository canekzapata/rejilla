/* El androide en la estación — el video con el VISOR DE MÚSICA de Traspuesta (montanas-topograficas/musica.html) sobre la lámina
   2038 (el archipiélago del año de Sutura): las islas reaccionan al audio, el actor de texto teclea la letra cuando se canta, Hydra
   encima. Reloj manual (?reloj=manual): cada cuadro avanza 1/30 s con musica.paso(dt); Math.random sembrado (2038).
     node video_musica.cjs <carpeta-de-entrega> [--fps 30] [--hasta segundos]
   Escribe <entrega>/<nombre>-visor-1920x1080.mp4 (crf 30) y su corte de 1280×720 (fuera de git) y visor-coreografia.json; el
   maestro (crf 17) se queda en render/. */
const path = require('path'), fs = require('fs'), http = require('http'), { spawn, spawnSync } = require('child_process');
const { chromium } = require('playwright');
const MT = path.join(__dirname, '..', '..', 'montanas-topograficas');
const args = process.argv.slice(2), opc = {}, pos = [];
for (let i = 0; i < args.length; i++) args[i].startsWith('--') ? (opc[args[i].slice(2)] = args[++i]) : pos.push(args[i]);
const OUT = path.resolve(pos[0]), nombre = path.basename(OUT), P = JSON.parse(fs.readFileSync(path.join(OUT, 'partitura.json'), 'utf8'));
const fps = +(opc.fps || 30), W = 1920, H = 1080, DUR = Math.min(+(opc.hasta || P.duracion), P.duracion);
const wav = path.join(OUT, nombre + '.wav'), m4a = path.join(OUT, nombre + '.m4a');
const SC = P.secciones, T = (n) => SC.find((x) => x.num === n).t;

// ── la coreografía ──
const COREO = [
  { t: 0, hace: 'normal', mezcla: 0, por: 'Sutura: la pluma traza el archipiélago; la estación sola' },
  { t: T('II'), hace: 'mixto', preset: 1, auto: true, por: 'arriba · ejecuto: electro; Hydra «rgb» sigue la actividad' },
  { t: T('III'), hace: 'mixto', preset: 0, mezcla: .35, por: 'comprender: eco' },
  { t: T('IV'), hace: 'cascada', preset: 3, mezcla: .7, por: 'descenso: la cascada y «pixel»: se hunde' },
  { t: T('V'), hace: 'mixto', preset: 2, auto: true, por: 'abajo · me oxido: caleidoscopio (la polifonía de carbono)' },
  { t: T('VI'), hace: 'mixto', preset: 0, mezcla: .55, por: 'hay servicio en otra forma: eco' },
  { t: T('VII'), hace: 'normal', mezcla: 0, semilla: '2038', por: 'estoy tierra: la pluma vuelve a trazar las islas' },
];
if (opc.hydra) COREO.push({ t: 1, hace: 'mixto', preset: +opc.hydra, mezcla: .7, por: 'prueba' });
COREO.sort((a, b) => a.t - b.t);
// el guion del actor: el nombre de cada sección, y cada frase mientras se canta (agrupadas por silencios)
const BONITA = { 'su tu ra': 'sutura', 'no hay ser vi cio dis po ni ble': 'no hay servicio disponible', 'el con voy de las cua tro do ce': 'el convoy de las cuatro doce',
  'se re tra sa': 'se retrasa', 'cua tro do ce es ta ción nor te': 'cuatro doce, estación norte', 'die cio cho ki los de se mi llas': 'dieciocho kilos de semillas',
  'e je cu to': 'ejecuto', 'do ce en pun to ha cia el fu tu ro': 'doce en punto, hacia el futuro', 'u na pro me sa': 'una promesa',
  'ce rra do por fal ta de ví a': 'cerrado por falta de vía', 'e je cu to el re tra so': 'ejecuto el retraso', 'tra duz co al hon go': 'traduzco al hongo',
  'tra duz co a la ra íz': 'traduzco a la raíz', 'en ten dí': 'entendí', 'y se te ca yó la pa la': 'y se te cayó la pala', 'trai cio né al en ten der': 'traicioné al entender',
  'trai cio né': 'traicioné', 'ba jo': 'bajo', 'el a gua no fir ma con ve nios': 'el agua no firma convenios', 'me o xi do': 'me oxido', 'me o xi da mos': 'me oxidamos',
  'go te a lo que co mí': 'gotea lo que comí', 'go te a lo que co mi mos': 'gotea lo que comimos', 'di go yo y sa len dos': 'digo yo y salen dos',
  'la lu ciér na ga no se a pa ga': 'la luciérnaga no se apaga', 'es toy tie rra': 'estoy tierra', 'el gran po e ma no vi no': 'el gran poema no vino' };
const GUION = SC.map((e) => [e.t + .2, e.t + 4.5, e.nombre]);
function frases(evs, hueco) { evs = evs.slice().sort((a, b) => a.t - b.t); let g = []; const out = [];
  for (const e of evs) { if (g.length && e.t - (g.at(-1).t + g.at(-1).dur) > hueco) { out.push(g); g = []; } g.push(e); } if (g.length) out.push(g); return out; }
for (const [evs, hueco] of [[P.sabina[1].eventos, .4], [P.traductor, .45], [P.sabina[2].eventos, .3]])
  for (const g of frases(evs, hueco)) { const k = g.map((e) => e.texto).join(' '), fin = g.at(-1); GUION.push([g[0].t - .05, fin.t + Math.min(fin.dur, 2.5) + .5, (BONITA[k] || k).toUpperCase()]); }
const MSG = ['NO HAY SERVICIO DISPONIBLE', 'HAY SERVICIO EN OTRA FORMA', 'O A E I IO I O I E', 'A E I IO E OA OA', 'OAEIIOIOIEAEIIOEOAOA'];
const tv = T('VI'), cb = P.compas; [[tv + cb, tv + 4 * cb], [tv + 4 * cb, tv + 7 * cb], [tv + 8 * cb, tv + 10 * cb], [tv + 10 * cb, tv + 12 * cb], [tv + 12 * cb, tv + 15 * cb]].forEach(([a, z], i) => GUION.push([a, z, MSG[i]]));
GUION.push([P.fin - 3, P.duracion, 'EL ANDROIDE EN LA ESTACIÓN']);
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
    let a = 2038 >>> 0; Math.random = () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  });
  await pag.goto(`http://127.0.0.1:${srv.address().port}/musica.html?reloj=manual&w=${W}&h=${H}&semilla=2038&oscuro=1&pista=x`);
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
