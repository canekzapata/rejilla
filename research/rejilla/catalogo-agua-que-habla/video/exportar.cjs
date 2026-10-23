/* Exporta el video cuadro por cuadro (sin reloj en vivo: no hay desfase) y lo une con el audio de la entrega.
   node exportar.cjs [--w 1920 --h 1080 --fps 30] → render/video-<w>x<h>.mp4 (luego se mueve a su carpeta con hash) */
const {chromium}=require('playwright');const fs=require('fs'),path=require('path'),{spawn}=require('child_process');
const a=process.argv.slice(2),op=(k,d)=>{const i=a.indexOf('--'+k);return i>=0?a[i+1]:d;};const W=+op('w',1920),H=+op('h',1080),FPS=+op('fps',30);
const D=JSON.parse(fs.readFileSync(path.join(__dirname,'datos.json'),'utf8')),audio=path.join(__dirname,'..',D.entrega,D.entrega+'.m4a');
const out=path.join(__dirname,'..','render',`video-${W}x${H}.mp4`);
(async()=>{const br=await chromium.launch({channel:'msedge',headless:true});const pg=await br.newPage({viewport:{width:Math.min(W,1920),height:Math.min(H,1080)}});
 await pg.goto(`http://127.0.0.1:8880/research/rejilla/catalogo-agua-que-habla/video/agua.html?w=${W}&h=${H}`);await pg.waitForFunction(()=>window.listo);
 const ff=spawn('ffmpeg',['-y','-v','error','-f','image2pipe','-c:v','mjpeg','-r',String(FPS),'-i','-','-i',audio,'-map','0:v','-map','1:a','-c:v','libx264','-preset','slow','-crf','17','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',out],{stdio:['pipe','inherit','inherit']});
 const N=Math.ceil(D.duracion*FPS),t0=Date.now();
 for(let i=0;i<N;i++){const b64=await pg.evaluate(t=>{cuadro(t);return document.getElementById('c').toDataURL('image/jpeg',.93).split(',')[1];},i/FPS);
  if(!ff.stdin.write(Buffer.from(b64,'base64')))await new Promise(r=>ff.stdin.once('drain',r));
  if(i%300===0)console.log(`cuadro ${i}/${N}`,((Date.now()-t0)/1000).toFixed(0)+' s');}
 ff.stdin.end();await new Promise(r=>ff.on('close',r));await br.close();console.log('listo',out,N,'cuadros');})();
