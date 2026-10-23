/* Motores originales: voz PSOLA, lengüetas/boca, kits, Falcon y cuerdas. */
const fs=require('fs'),path=require('path');const {chromium}=require('C:/Users/HP-PC/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const OUT=path.join(__dirname,fs.readFileSync(path.join(__dirname,'ULTIMA.txt'),'utf8').trim()),P=JSON.parse(fs.readFileSync(path.join(OUT,'partitura.json'),'utf8')),tag=path.basename(OUT).split('-').pop(),RUN=path.join(__dirname,'render',tag),SR=P.sr,lib=path.join(__dirname,P.instrumentos),modo=process.argv[2]||'prueba';
function save(n,x){const target=Math.round(P.duracion*SR);if(x.length===target+1)x=x.subarray(0,target);fs.writeFileSync(path.join(RUN,n+'.f32'),Buffer.from(x.buffer,x.byteOffset,x.byteLength),{flag:'wx'});console.log(n,x.length);}
function gate(y,ev){let g=new Float32Array(y.length);for(const e of ev){let i=Math.round(e.t*SR),n=Math.min(Math.round((e.dur+.23)*SR),y.length-i);for(let j=0;j<n;j++)g[i+j]=Math.max(g[i+j],Math.min(1,j/(.012*SR),(n-j)/(.08*SR)));}for(let i=0;i<y.length;i++)y[i]*=g[i];return y;}
async function objetos(){const folder=path.join(lib,'codigo/rejilla/research/rejilla/objetos/motor');
 for(const c of ['chelo','contrabajo']){const ev=P.eventos[c].map(e=>({t:e.t,m:e.midi,v:e.vel,dur:e.dur,tipo:e.tipo}));const y=require(path.join(folder,'cuerda.js')).render({dur:P.duracion,instrumento:c,eventos:ev,semilla:P.semilla},SR);save(c,gate(y,ev));}
 const ev=P.eventos.dundun.map(e=>({t:e.t,m:e.midi,v:e.vel,tipo:'habla',texto:e.texto,dur:e.dur,alto:4}));save('dundun',require(path.join(folder,'tambor.js')).render({dur:P.duracion,eventos:ev,semilla:P.semilla},SR));
}
async function navegador(){const br=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 try{const pg=await br.newPage();await pg.setContent('<title>Audio offline de La corriente</title>');await pg.exposeFunction('guardar',(n,b64,first)=>{let f=path.join(RUN,n+'.f32');if(first)fs.writeFileSync(f,Buffer.from(b64,'base64'),{flag:'wx'});else fs.appendFileSync(f,Buffer.from(b64,'base64'));});
 await pg.addScriptTag({content:`async function entrega(n,y){const STEP=1<<19;for(let i=0;i<y.length;i+=STEP){let z=y.slice(i,i+STEP),u=new Uint8Array(z.buffer),s='';for(let j=0;j<u.length;j+=32768)s+=String.fromCharCode(...u.subarray(j,j+32768));await guardar(n,btoa(s),i===0);}}`});
 if(modo==='prueba'||modo==='voz'){
  for(const f of ['g2p.js','difonos.js'])await pg.addScriptTag({content:fs.readFileSync(path.join(__dirname,'fuentes/difonos',f),'utf8')});
  const bank=path.join(__dirname,'../inferencia/vendor/difonos/bancos/sabina-1-b44e7fab5cee'),M=JSON.parse(fs.readFileSync(path.join(bank,'manifiesto.json'),'utf8')),audio=fs.readFileSync(path.join(bank,'banco.flac')).toString('base64');
  const frases=modo==='prueba'?[{capa:'prueba',eventos:P.prueba_voz}]:P.sabina;
  for(const fr of frases){const r=await pg.evaluate(async({fr,M,audio,SR,D,seed})=>{const ctx=new OfflineAudioContext(1,Math.round(D*SR),SR),bin=Uint8Array.from(atob(audio),c=>c.charCodeAt(0)),b=new Difonos.Banco(ctx,await ctx.decodeAudioData(bin.buffer),M);let s=seed,q=[];const rng=()=>{s=(Math.imul(s,1664525)+1013904223)>>>0;return s/4294967296;};b.cantar(ctx.destination,fr.eventos,{modo:'psola',vibrato:[4.3,.0015],rng,agendar:(t,f)=>q.push([t,f])});q.sort((a,b)=>a[0]-b[0]);let hasta=t=>{while(q.length&&q[0][0]<t)q.shift()[1]();};hasta(3);for(let k=2;k<D-.1;k+=2)ctx.suspend(k).then(()=>{hasta(k+3);ctx.resume();});let y=(await ctx.startRendering()).getChannelData(0);await entrega('sabina-'+fr.capa,y);return {capa:fr.capa,muestras:y.length};},{fr,M,audio,SR,D:modo==='prueba'?6:P.duracion,seed:P.semilla});console.log(r);}
 }
 if(modo==='web'||modo==='kits'){
  await pg.addScriptTag({content:fs.readFileSync(path.join(lib,'motores/web.js'),'utf8')});
  if(modo==='web'){
   await pg.addScriptTag({content:fs.readFileSync(path.join(lib,'motores/meleeviewer.js'),'utf8')});
   for(const [c,id] of [['mbira','mbira'],['kalimba','kalimbacaja'],['arpa-boca','arpaboca'],['organo-roto','receta-organo-roto'],['falcon','meleeviewer-8-basso']]){
    const K=JSON.parse(fs.readFileSync(path.join(lib,'fichas',id+'.json'),'utf8')),source=c==='falcon'?fs.readFileSync(path.join(lib,K.fisica.escenario),'utf8'):'';
    await pg.evaluate(async({c,K,source,events,SR,D})=>{const ctx=new OfflineAudioContext(1,Math.round(D*SR),SR);for(const e of events){const n={t:e.t,midi:e.midi,vel:e.vel,dur:e.dur};if(c==='falcon')await InstrumentosMelee.tocar(ctx,ctx.destination,K,n,{fuente:async()=>source});else Instrumentos.tocar(ctx,ctx.destination,K,n,{tonica:'F#',escala:[0,2,3,5,7,9,10]});}await entrega(c,(await ctx.startRendering()).getChannelData(0));},{c,K,source,events:P.eventos[c],SR,D:P.duracion});console.log(c);
   }
  }else for(const id of ['bateria-tr808','bateria-frito']){
   const K=JSON.parse(fs.readFileSync(path.join(lib,'fichas',id+'.json'),'utf8'));
   await pg.evaluate(async({K,SR})=>{for(const pieza of ['kick','snare','clap','hat','openhat','spray','rim'])for(let j=0;j<3;j++){const ctx=new OfflineAudioContext(1,SR*3,SR);Instrumentos.tocar(ctx,ctx.destination,K,{t:.04,midi:60,vel:[.3,.6,.9][j],dur:.2,pieza});await entrega(K.id+'-'+pieza+'-'+j,(await ctx.startRendering()).getChannelData(0).slice(Math.round(.04*SR)));}},{K,SR});console.log(id);
  }
 }
 }finally{await br.close();}}
(async()=>{if(modo==='objetos')await objetos();else await navegador();})().catch(e=>{console.error(e);process.exitCode=1;});
