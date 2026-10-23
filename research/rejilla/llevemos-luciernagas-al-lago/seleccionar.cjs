// Inspección real del visor local. Exporta datos sin modificar Traspuesta.
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {chromium}=require('playwright');
const ROOT=path.resolve(__dirname,'../../montanas-topograficas');
const nonce=crypto.randomUUID(),id=crypto.createHash('sha256').update(fs.readFileSync(__filename)).update(nonce).digest('hex').slice(0,12);
const OUT=path.join(__dirname,'exploracion-'+id);fs.mkdirSync(OUT);
function save(name,data){fs.writeFileSync(path.join(OUT,name),data,{flag:'wx'});}
(async()=>{
 const browser=await chromium.launch({headless:true,channel:'chrome'});
 const context=await browser.newContext({viewport:{width:1440,height:900},deviceScaleFactor:1});
 // Servir los archivos autorizados dentro del navegador evita depender del
 // acceso loopback de esta sesión. No se solicita ningún recurso externo.
 await context.route('**/*',async route=>{
  const u=new URL(route.request().url());
  if(u.hostname!=='127.0.0.1')return route.abort();
  let rel=decodeURIComponent(u.pathname);if(rel.endsWith('/'))rel+='index.html';
  const f=path.resolve(ROOT,'.'+rel);
  if(!f.startsWith(ROOT+path.sep)||!fs.existsSync(f))return route.fulfill({status:404,body:'no disponible'});
  const ext=path.extname(f);const ct={'.html':'text/html','.js':'application/javascript','.json':'application/json','.png':'image/png','.svg':'image/svg+xml','.woff2':'font/woff2'}[ext]||'application/octet-stream';
  return route.fulfill({body:fs.readFileSync(f),contentType:ct});
 });
 const page=await context.newPage();
 const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto('http://127.0.0.1:8766/',{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>document.querySelectorAll('#rejilla a').length>0,{timeout:60000});
 save('atlas-'+id+'.png',await page.screenshot());
 const catalog=JSON.parse(fs.readFileSync(path.join(ROOT,'edicion/edicion.json'),'utf8'));
 save('consulta-atlas.json',JSON.stringify({campos:catalog.campos,candidatas:catalog.filas.filter(r=>[1,27,43].includes(r[0]))},null,2));
 const meta=[];
 for(const s of [1,27,43]){
  await page.goto(`http://127.0.0.1:8766/ver.html?s=${s}&eras=0&pelicula=1&cuadro=1440x900&dur=3`,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>window.pelicula&&window.pelicula.listo,null,{timeout:60000});
  await page.evaluate(()=>window.pelicula.ir(window.pelicula.total));
  save(`traspuesta-s${s}-${id}.png`,await page.screenshot());
  const data=await page.evaluate(seed=>{
   const T=MT.terreno(String(seed)),L=MT.lamina(String(seed));
   const names=MT.nombra(T,String(seed),0).map(n=>({nombre:n.nombre||n.texto,clase:n.clase,u:n.u,v:n.v}));
   return {seed,G:T.G,arq:T.arq,nombre:T.nombre,anchoKm:T.anchoKm,relieve:T.relieve,base:T.base,mar:T.mar,nivelMar:T.nivelMar,
    hidro:T.hidro,rasgos:T.rasgos,nombres:names,h:Array.from(T.h),lamina:{meta:L.meta,papel:L.papel,plumas:L.plumas},svg:MT.svg(L)};
  },s);
  const svg=data.svg;delete data.svg;save(`lamina-s${s}-${id}.svg`,svg);
  save(`terreno-s${s}.json`,JSON.stringify(data));
  meta.push({seed:s,nombre:data.nombre,anchoKm:data.anchoKm,base:data.base,relieve:data.relieve,hidro:Object.keys(data.hidro||{}),nombres:data.nombres.slice(0,4)});
 }
 save('exploracion.json',JSON.stringify({nonce,id,meta,errors,metodo:'Chrome headless, aplicación real; capturas del atlas y visor; sin audio'},null,2));
 for(const name of ['nucleo.js','terreno.js','lamina.js','visor.js','ver.html','edicion/edicion.json']){
  const target=path.join(OUT,'fuentes',name);fs.mkdirSync(path.dirname(target),{recursive:true});fs.copyFileSync(path.join(ROOT,name),target,fs.constants.COPYFILE_EXCL);
 }
 await browser.close();console.log(OUT);console.log(JSON.stringify(meta));
})().catch(e=>{save('FALLO.txt',String(e.stack));console.error(e);process.exitCode=1;});
