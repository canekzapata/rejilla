/* Audio offline de los motores originales fijados. No controla un navegador personal. */
const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/HP-PC/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const OUT=path.join(__dirname,fs.readFileSync(path.join(__dirname,'ULTIMA.txt'),'utf8').trim()),P=JSON.parse(fs.readFileSync(path.join(OUT,'partitura.json'),'utf8'));
const tag=path.basename(OUT).split('-').pop(),RUN=path.join(__dirname,'render',tag),SR=P.sr;
const lib=path.join(__dirname,'instrumentos-5620a744f682'),obj=path.join(lib,'codigo/rejilla/research/rejilla/objetos/motor');
const modo=process.argv[2]||'todo';
function save(n,x){fs.writeFileSync(path.join(RUN,n+'.f32'),Buffer.from(x.buffer,x.byteOffset,x.byteLength),{flag:'wx'});console.log(n,x.length);}
function gate(y,events){const g=new Float32Array(y.length);for(const e of events){const i0=Math.max(0,Math.round(e.t*SR)),n=Math.min(y.length-i0,Math.round((e.dur+.18)*SR));for(let j=0;j<n;j++)g[i0+j]=Math.max(g[i0+j],Math.min(1,j/(.008*SR),(n-j)/(.06*SR)));}for(let i=0;i<y.length;i++)y[i]*=g[i];return y;}
async function objetos(){
 const event=c=>P.eventos[c].map(e=>({t:e.t,m:e.midi,v:e.vel,dur:e.dur,tipo:e.tipo||'normal'}));
 for(const name of ['piano','chelo','clarinete','metal']){
  let y;const ev=event(name),dur=P.duracion;
  if(name==='piano'){const A=require(path.join(obj,'piano.js'));y=A.render({dur,eventos:ev.map(e=>({...e,tipo:'normal'})),prepara:()=>A.PREP.tornillo},SR);}
  if(name==='chelo')y=require(path.join(obj,'cuerda.js')).render({dur,instrumento:'chelo',eventos:ev,semilla:227},SR);
  if(name==='clarinete')y=require(path.join(obj,'clarinete.js')).render({dur,eventos:ev,semilla:227},SR);
  if(name==='metal')y=require(path.join(obj,'metal.js')).render({dur,voz:'trombon',sordina:'plunger',notas:ev,wah:[[0,.3],[P.duracion,.8]],semilla:227},SR);
  save(name,gate(y,ev));
 }
}
async function navegador(){
 const br=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 try{
 const pg=await br.newPage();await pg.setContent('<title>Audio offline del lago</title>');
 await pg.exposeFunction('guardar',(n,b64,primero)=>{const f=path.join(RUN,n+'.f32');if(primero)fs.writeFileSync(f,Buffer.from(b64,'base64'),{flag:'wx'});else fs.appendFileSync(f,Buffer.from(b64,'base64'));});
 if(modo==='kits'||modo==='todo'){
  await pg.addScriptTag({content:fs.readFileSync(path.join(lib,'motores/web.js'),'utf8')});
  const kits=['bateria-tr808','bateria-frito'].map(n=>JSON.parse(fs.readFileSync(path.join(lib,'fichas',n+'.json'),'utf8')));
  const info=await pg.evaluate(async({kits,SR})=>{
   const parts=['kick','snare','clap','hat','openhat','spray','rim'],vels=[.3,.6,.9],len=3*SR;
   for(const K of kits)for(const pieza of parts)for(let v=0;v<vels.length;v++){
    const ctx=new OfflineAudioContext(1,len,SR);Instrumentos.tocar(ctx,ctx.destination,K,{t:.04,midi:60,vel:vels[v],dur:.2,pieza});
    const y=(await ctx.startRendering()).getChannelData(0).slice(Math.round(.04*SR));let s='';const u=new Uint8Array(y.buffer);for(let j=0;j<u.length;j+=32768)s+=String.fromCharCode(...u.subarray(j,j+32768));await guardar(K.id+'-'+pieza+'-'+v,btoa(s),true);
   }return {kits:kits.length,piezas:parts.length,velocidades:vels};},{kits,SR});console.log(info);
 }
 if(modo==='voz'||modo==='todo'){
  const vendor=path.join(__dirname,'../inferencia/vendor/difonos'),bank=path.join(vendor,'bancos/sabina-1-b44e7fab5cee');
  for(const f of ['g2p.js','difonos.js'])await pg.addScriptTag({content:fs.readFileSync(path.join(vendor,'runtime',f),'utf8')});
  const M=JSON.parse(fs.readFileSync(path.join(bank,'manifiesto.json'),'utf8')),audio=fs.readFileSync(path.join(bank,'banco.flac')).toString('base64');
  for(const fr of P.sabina){
   const info=await pg.evaluate(async({fr,M,audio,SR,duracion})=>{
    let seed=227;const rng=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
    const ctx=new OfflineAudioContext(1,Math.ceil(duracion*SR),SR),bin=Uint8Array.from(atob(audio),c=>c.charCodeAt(0));
    const bank=new Difonos.Banco(ctx,await ctx.decodeAudioData(bin.buffer),M);let q=[];bank.cantar(ctx.destination,fr.eventos,{modo:'psola',vibrato:[4.8,.002],rng,agendar:(t,f)=>q.push([t,f])});q.sort((a,b)=>a[0]-b[0]);
    const hasta=t=>{while(q.length&&q[0][0]<t)q.shift()[1]();};hasta(3);
    for(let k=2;k<duracion-.1;k+=2)ctx.suspend(k).then(()=>{hasta(k+3);ctx.resume();});
    const y=(await ctx.startRendering()).getChannelData(0),STEP=1<<19;let peak=0;
    for(let a=0;a<y.length;a+=STEP){const z=y.slice(a,a+STEP);for(const v of z)peak=Math.max(peak,Math.abs(v));const u=new Uint8Array(z.buffer);let s='';for(let j=0;j<u.length;j+=32768)s+=String.fromCharCode(...u.subarray(j,j+32768));await guardar('sabina-'+fr.capa,btoa(s),a===0);}
    return {capa:fr.capa,pico:peak};},{fr,M,audio,SR,duracion:P.duracion});console.log(info);
  }
 }
 }finally{await br.close();}
}
(async()=>{if(modo==='objetos'||modo==='todo')await objetos();if(modo!=='objetos')await navegador();})().catch(e=>{console.error(e);process.exit(1);});
