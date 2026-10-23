'use strict';
// Iniciar antes: python herramientas/servidor.py --puerto 8482
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {lanzarChromium}=require('./navegador.cjs');
const root=path.resolve(__dirname,'..');
(async()=>{const browser=await lanzarChromium();try{
 const page=await browser.newPage({viewport:{width:1200,height:880}}),errores=[];
 page.on('pageerror',e=>errores.push(e.message));
 await page.goto(process.argv[2]||'http://127.0.0.1:8482/laboratorio.html');
 const nonce=crypto.randomBytes(16).toString('hex');
 const first=await page.screenshot();
 const full=crypto.createHash('sha256').update(first).update(fs.readFileSync(__filename)).update(nonce).digest('hex'),tag=full.slice(0,12);
 const dest=path.join(root,'proceso','restauracion-rejilla-'+tag);fs.mkdirSync(dest,{recursive:true});
 fs.writeFileSync(path.join(dest,'01-catalogo-'+tag+'.png'),first,{flag:'wx'});
 await page.locator('#secuencia').click();
 await page.waitForFunction(()=>document.getElementById('estado').textContent.startsWith('Audio calculado'));
 await page.locator('#onda').scrollIntoViewIfNeeded();
 await page.screenshot({path:path.join(dest,'02-secuencia-y-onda-'+tag+'.png')});
 await page.locator('#crear').click();
 await page.waitForFunction(()=>document.getElementById('estado').textContent.startsWith('Audio calculado'));
 await page.locator('#espectro').scrollIntoViewIfNeeded();
 await page.screenshot({path:path.join(dest,'03-diseno-y-espectro-'+tag+'.png')});
 const resultados=await page.evaluate(async()=>{
  const rows=CATALOGO.filter(r=>r.ficha&&(Instrumentos.motores.includes(r.ficha.motor)||r.ficha.motor==='meleeviewer')),out=[];
  for(const r of rows){try{const O=new OfflineAudioContext(2,32000*3,32000),g=O.createGain();g.gain.value=.5;g.connect(O.destination);const n={t:r.id.endsWith('-reverso')?1:.1,midi:62,vel:.7,dur:.5,pieza:'kick'};if(r.ficha.motor==='meleeviewer')await InstrumentosMelee.tocar(O,g,r.ficha,n,{fuente:p=>fetch('biblioteca-de-instrumentos/'+p).then(r=>{if(!r.ok)throw Error(p);return r.text()})});else Instrumentos.tocar(O,g,r.ficha,n);const b=await O.startRendering();let peak=0,finite=true;for(let c=0;c<2;c++)for(const x of b.getChannelData(c)){finite&&=Number.isFinite(x);peak=Math.max(peak,Math.abs(x))}out.push({id:r.id,ok:finite&&peak>1e-8,peak})}catch(e){out.push({id:r.id,ok:false,error:e.message})}}
  return out;
 });
 const resp=await page.request.get(new URL('/api/muestra?id=marimba',page.url()).href);if(!resp.ok())throw Error(await resp.text());
 const unknown=await page.request.get(new URL('/api/muestra?id=../../.env',page.url()).href);if(unknown.status()!==422)throw Error('Se aceptó un identificador no registrado');
 const downloadPromise=page.waitForEvent('download');await page.locator('#guardarDiseno').click();const download=await downloadPromise;await download.saveAs(path.join(root,'renders',download.suggestedFilename()));
 const receipt={ejecucion:full,nonce,version:crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex'),errores,resultados};
 fs.writeFileSync(path.join(dest,'verificacion.json'),JSON.stringify(receipt,null,2),{flag:'wx'});
 console.log(JSON.stringify({carpeta:dest,pruebas:resultados.length,ok:resultados.filter(x=>x.ok).length,fallos:resultados.filter(x=>!x.ok),errores}));
 if(errores.length||resultados.some(x=>!x.ok))process.exitCode=1;
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
