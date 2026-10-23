/* La duna que canta — el video con el VISOR DE MÚSICA de Traspuesta (montanas-topograficas/musica.html, «Traspuesta suena»)
   sobre la duna 675 («TALI», barjanes): las dunas reaccionan al audio, el actor de texto teclea la letra cuando se canta, Hydra
   encima. Reloj manual (?reloj=manual): cada cuadro avanza 1/30 s con musica.paso(dt) y la pista se analiza en ese mismo reloj;
   Math.random sembrado (675). La coreografía (qué vista y qué Hydra en cada sección) vive en COREO.
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

// ── la coreografía: lo que la música hace con la duna, sección por sección ──
const COREO = [
  { t: 0, hace: 'normal', mezcla: 0, por: 'sonido absoluto: la pluma traza la duna 675; el relieve respira con el bramido pp' },
  { t: T('II'), hace: 'mixto', preset: 0, mezcla: .25, por: 'gnawa: terreno + espectro; Hydra «eco»' },
  { t: T('III'), hace: 'cascada', preset: 3, mezcla: .75, por: 'avalancha 1: la cascada y Hydra «pixel»: los granos' },
  { t: T('IV'), hace: 'mixto', preset: 1, auto: true, por: 'blues del desierto y Clapping Music: Hydra «rgb» sigue la actividad' },
  { t: P.solo[0].t0, hace: 'mixto', preset: 2, auto: true, por: 'el solo nómada: caleidoscopio (las crestas repetidas)' },
  { t: T('V'), hace: 'cascada', preset: 3, mezcla: .9, por: 'la duna brama: cascada y «pixel» al máximo' },
  { t: T('VI'), hace: 'mixto', preset: 0, mezcla: .5, por: 'correr al revés: eco' },
  { t: T('VII'), hace: 'normal', mezcla: 0, semilla: '675', por: 'una palabra: la pluma vuelve a trazar la duna' },
];
if (opc.hydra) COREO.push({ t: 1, hace: 'mixto', preset: +opc.hydra, mezcla: .7, por: 'prueba' });
COREO.sort((a, b) => a.t - b.t);
// el guion del actor: el nombre de cada sección al empezar, y cada renglón de la letra mientras se canta (la llamada y la respuesta)
const BONITA = { 'yo ya no es ta ré e xac ta men te a quí': 'yo ya no estaré exactamente aquí', 'con fir mo que no lle vo a na die': 'confirmo que no llevo a nadie',
  're gis tro u na lí ne a a zul': 'registro una línea azul', 'la luz ca yó so bre mis cá ma ras': 'la luz cayó sobre mis cámaras',
  'ya no es ta rá e xac ta men te a quí': 'ya no estará exactamente aquí', 'que no lle va a na die': 'que no lleva a nadie', 'u na lí ne a a zul': 'una línea azul',
  'las flo res del de sier to re na cen con la mí ni ma llu via': 'las flores del desierto renacen con la mínima lluvia', 'to da ví a lle ga al go': 'todavía llega algo',
  'co rrer al re vés': 'correr al revés', 'no los se pa ra': 'no los separa', 'lle ga al go': 'llega algo', 'al go': 'algo', 'al': 'al' };
const GUION = SC.map((e) => [e.t + .2, e.t + 4.5, e.nombre]);
function renglones(evs, versos) { let i = 0; for (const v of versos) { const n = v.split(' ').length, sil = evs.slice(i, i + n); i += n; if (!sil.length) continue; const fin = sil.at(-1);
  GUION.push([sil[0].t - .05, fin.t + Math.min(fin.dur, 2.5) + .5, (BONITA[v] || v).toUpperCase()]); } }
const L = P.letra, lead = P.sabina[0].eventos, sop = P.sabina[1].eventos;
renglones(lead, [...L.llamadas_1, ...L.llamadas_2, ...L.final]);
renglones(sop, [...Array(8).fill(L.respuesta), ...L.reves]);
GUION.push([P.fin - 3, P.duracion, 'LA DUNA QUE CANTA']);
GUION.sort((a, b) => a[0] - b[0]);
for (let i = 0; i + 1 < GUION.length; i++) if (GUION[i][1] > GUION[i + 1][0]) GUION[i][1] = GUION[i + 1][0];   // un renglón a la vez

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
    let a = 675 >>> 0; Math.random = () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  });
  await pag.goto(`http://127.0.0.1:${srv.address().port}/musica.html?reloj=manual&w=${W}&h=${H}&semilla=675&oscuro=1&pista=x`);
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
