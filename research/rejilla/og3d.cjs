/* Saca og.png (1200×630) y favicon.png de una pieza 3D de rejilla: carga la página, espera a que la escena gire, esconde la
   interfaz (todo lo que no sea el lienzo o lo contenga) y toma la foto. No pisa: si ya existen, se detiene.
     node og3d.cjs <carpeta-de-la-pieza> [segundos] */
const path = require('path'), fs = require('fs'), { chromium } = require('playwright');
const dir = path.resolve(process.argv[2]), espera = +(process.argv[3] || 4) * 1000;
const og = path.join(dir, 'og.png'), fav = path.join(dir, 'favicon.png');
if (fs.existsSync(og) || fs.existsSync(fav)) { console.error('ya hay og.png o favicon.png: no se pisa'); process.exit(1); }
(async () => {
  const nav = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const pag = await nav.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
  const errores = []; pag.on('pageerror', (e) => errores.push(e.message));
  await pag.goto('file:///' + path.join(dir, 'index.html').replace(/\\/g, '/'));
  await pag.waitForTimeout(espera);
  await pag.evaluate(() => {                                         // sólo queda el lienzo más grande (la escena) y lo que lo contiene
    const cs = [...document.querySelectorAll('canvas')]; const g = cs.sort((x, y) => y.width * y.height - x.width * x.height)[0];
    for (const e of document.querySelectorAll('body *')) if (e !== g && !e.contains(g)) e.style.visibility = 'hidden';
  });
  await pag.waitForTimeout(300);
  await pag.screenshot({ path: og });
  await pag.setViewportSize({ width: 256, height: 256 }); await pag.waitForTimeout(500);
  await pag.screenshot({ path: fav });
  await nav.close();
  console.log(path.basename(dir), 'og.png y favicon.png', errores.length ? 'errores: ' + errores.join(' | ') : 'sin errores');
})();
