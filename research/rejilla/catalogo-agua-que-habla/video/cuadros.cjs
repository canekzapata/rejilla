/* Saca cuadros sueltos (PNG) del video a resolución completa: node cuadros.cjs <carpeta> t1 t2 …  [--solo capa] [--w 1080 --h 1920] */
const {chromium}=require('playwright');const fs=require('fs'),path=require('path');
const a=process.argv.slice(2),dir=a[0],ts=a.slice(1).filter(x=>!x.startsWith('--')&&isFinite(+x)).map(Number),op=k=>{const i=a.indexOf('--'+k);return i>0?a[i+1]:null;};
(async()=>{fs.mkdirSync(dir,{recursive:true});const w=+op('w')||1920,h=+op('h')||1080,solo=op('solo');
 const br=await chromium.launch({channel:'msedge',headless:true});const pg=await br.newPage({viewport:{width:w,height:h}});
 await pg.goto(`http://127.0.0.1:8880/research/rejilla/catalogo-agua-que-habla/video/agua.html?w=${w}&h=${h}`+(solo?'&solo='+solo:''));await pg.waitForFunction(()=>window.listo);
 for(const t of ts){const b64=await pg.evaluate(t=>{cuadro(t);return document.getElementById('c').toDataURL('image/png').split(',')[1];},t);
  const f=path.join(dir,`t${t.toFixed(2).padStart(6,'0')}${solo?'-'+solo:''}.png`);fs.writeFileSync(f,Buffer.from(b64,'base64'));console.log(f);}
 await br.close();})();
