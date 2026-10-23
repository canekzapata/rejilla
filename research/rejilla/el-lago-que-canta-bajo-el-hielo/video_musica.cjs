/* Render delegado a Canek. --comprobar captura UN cuadro; no crea ningún video. */
const fs=require('fs'),path=require('path'),http=require('http'),{spawn}=require('child_process');
const {chromium}=require('C:/Users/HP-PC/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const args=process.argv.slice(2),OUT=path.resolve(args[0]),check=args.includes('--comprobar');
const get=(n,d)=>{const i=args.indexOf(n);return i<0?d:args[i+1];};
const cuadro=get('--cuadro','');
const W=+get('--ancho',1920),H=Math.round(W*9/16),fps=+get('--fps',30);
const P=JSON.parse(fs.readFileSync(path.join(OUT,'partitura.json'),'utf8')),R=JSON.parse(fs.readFileSync(path.join(OUT,'red.json'),'utf8'));
const name=path.basename(OUT),wav=path.join(OUT,name+'.wav'),src=path.join(__dirname,'fuentes/traspuesta'),tag=name.split('-').pop();
if(!fs.existsSync(wav))throw Error('falta el máster WAV de esta entrega');
const final=path.join(OUT,name+`-visor-${W}x${H}.mp4`);
if(!check&&fs.existsSync(final))throw Error('el video ya existe; se conserva');
const MIME={'.html':'text/html','.js':'text/javascript','.json':'application/json','.png':'image/png','.wav':'audio/wav'};
const srv=http.createServer((req,res)=>{
 const u=decodeURIComponent(req.url.split('?')[0]);if(u==='/pista'){res.writeHead(200,{'Content-Type':'audio/wav'});return fs.createReadStream(wav).pipe(res);}
 const f=path.resolve(src,'.'+u);if(!f.startsWith(src+path.sep)||!fs.existsSync(f)||!fs.statSync(f).isFile()){res.writeHead(404);return res.end();}
 res.writeHead(200,{'Content-Type':MIME[path.extname(f)]||'application/octet-stream'});
 if(u==='/musica.html'){
  const s=fs.readFileSync(f,'utf8').replace(/\r\n/g,'\n'),needle='dibuja();\n    hydraCuadro(dt);';if(!s.includes(needle))throw Error('cambió el gancho del reloj');
  return res.end(s.replace(needle,'dibuja();\n    if(window.grietaLago)window.grietaLago.paso(S.t);\n    hydraCuadro(dt);')
   .replace('const base = H * 0.019, max = H * 0.17','const base = H * 0.018, max = H * 0.032')
   .replace('function cartela() {',"function cartela() { escribe('EL LAGO QUE CANTA BAJO EL HIELO', W*.025, H*.94, Math.max(9, Math.round(H/62)), neon(S.hue+40), papel()); escribe('CANEK ZAPATA · 2026', W*.025, H*.98, Math.max(9, Math.round(H/62)), neon(S.hue+40), papel()); return;")
   .replace('const conGuion = !!(X.guion && X.gActual);',"if(X.color){X.color.fondo=null;X.color.tinta=neon(S.hue+50);X.color.sombras=[];} X.modo='cielo'; X.ax=0; const conGuion = !!(X.guion && X.gActual);"));
 }fs.createReadStream(f).pipe(res);
});
(async()=>{let br,ff;
 try{
 await new Promise(r=>srv.listen(0,'127.0.0.1',r));
 br=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-accelerated-2d-canvas']});
 const pg=await br.newPage({viewport:{width:W,height:H},deviceScaleFactor:1}),errors=[];pg.on('pageerror',e=>errors.push(e.message));
 await pg.addInitScript(()=>{let a=227;Math.random=()=>{a=(Math.imul(a,1664525)+1013904223)>>>0;return a/4294967296;};});
 await pg.goto(`http://127.0.0.1:${srv.address().port}/musica.html?reloj=manual&w=${W}&h=${H}&semilla=227&oscuro=1&pista=x`);
 await pg.waitForFunction(()=>window.musicaLista&&window.musica?.A.modo==='pista'&&window.musica.S.rows,null,{timeout:120000});
 await pg.addScriptTag({content:fs.readFileSync(path.join(__dirname,'grieta.js'),'utf8')});
 await pg.evaluate(({R,P,W,H})=>{const m=musica;m.S.auto=false;m.S.penDur=7;m.S.exag=.7;m.mixto(true);window.grietaLago=instalarGrieta(m,R,P,W,H);m.X.guion=t=>{const s=P.secciones.find(s=>t>=s.t&&t<s.t1);return s?s.nombre.toUpperCase():P.titulo.toUpperCase();};},{R,P,W,H});
 if(check){
  for(let i=0;i<80;i++)await pg.evaluate(()=>musica.paso(.1));
  const estado=await pg.evaluate(()=>({hydra:musica.hydra.listo,error:musica.hydra.error,t:musica.S.t,mascara:!!grietaLago.canvas,ancho:grietaLago.canvas.width}));
  const png=path.join(OUT,'proceso',cuadro==='final'?`09-visor-final-s227-${tag}.png`:cuadro?`08-visor-titulo-s227-${tag}.png`:`06-visor-grieta-s227-${tag}.png`);if(fs.existsSync(png))throw Error('el cuadro de prueba ya existe');
  await pg.screenshot({path:png});if(!estado.hydra||estado.error||errors.length)throw Error(JSON.stringify({estado,errors}));
  fs.writeFileSync(path.join(OUT,cuadro?`visor-comprobacion-${cuadro}.json`:'visor-comprobacion.json'),JSON.stringify({estado,errors,solo_un_cuadro:true,video_renderizado:false},null,1),{flag:'wx'});console.log('cuadro y preflight:',estado);return;
 }
 // El único camino que crea un MP4 es la invocación normal que ejecutará Canek.
 ff=spawn('ffmpeg',['-n','-v','error','-f','image2pipe','-framerate',String(fps),'-i','-','-i',wav,'-map','0:v','-map','1:a','-c:v','libx264','-preset','medium','-crf','27','-pix_fmt','yuv420p','-c:a','aac','-b:a','256k','-shortest','-movflags','+faststart',final],{stdio:['pipe','inherit','inherit']});
 let rejectFF;const finished=new Promise((res,rej)=>{rejectFF=rej;ff.on('error',rej);ff.on('close',c=>c===0?res():rej(Error('ffmpeg '+c)));});ff.stdin.on('error',e=>rejectFF(e));
 const n=Math.ceil(P.duracion*fps),start=Date.now();
 for(let f=0;f<n;f++){
  const t=f/fps;if(f%fps===0)process.stdout.write(`\r${t.toFixed(0)} / ${P.duracion.toFixed(0)} s · ${Math.round((Date.now()-start)/1000)} s de trabajo`);
  await pg.evaluate(({dt,t,P})=>{const m=musica,sec=P.secciones.find(s=>t>=s.t&&t<s.t1);if(sec){m.S.exag=sec.id==='VI'?.45:.7;m.hydra.mezcla(sec.id==='III'?.55:.8);}m.paso(dt);},{dt:f===0?0:1/fps,t,P});
  const b=await pg.screenshot({type:'png'});if(!ff.stdin.write(b))await new Promise(r=>ff.stdin.once('drain',r));
 }ff.stdin.end();await finished;
 fs.writeFileSync(path.join(OUT,`visor-recibo-${W}x${H}.json`),JSON.stringify({fps,cuadros:n,segundos:P.duracion,video:path.basename(final),grieta:'aristas de red.json, emisión y llegada en partitura.json',errors},null,1),{flag:'wx'});console.log('\n',final);
 }finally{if(br)await br.close();srv.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
