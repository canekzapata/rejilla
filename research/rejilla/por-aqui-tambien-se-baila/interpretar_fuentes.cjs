/* Motores fijados: instrumentos de biblioteca y voz Sabina. No visuales. */
const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/HP-PC/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const base=__dirname,out=path.join(base,fs.readFileSync(path.join(base,'RENDER-ACTUAL.txt'),'utf8').trim()),cfg=JSON.parse(fs.readFileSync(path.join(out,'interpretacion.json'),'utf8')),P=JSON.parse(fs.readFileSync(path.join(out,'partitura-aprobada.json'),'utf8')),R=path.join(cfg.scratch,'fuentes'),N=Math.round(cfg.duracion*cfg.sr),lib=cfg.biblioteca,mode=process.argv[2]||'todo';
function save(c,y){if(y.length===N+1)y=y.subarray(0,N);if(y.length!==N)throw Error(c+' longitud '+y.length);fs.writeFileSync(path.join(R,c+'.f32'),Buffer.from(y.buffer,y.byteOffset,y.byteLength),{flag:'wx'});console.log(c,flush=true);}
async function objetos(){
 const O=require(path.join(lib,'motores/objetos.js'));
 for(const [c,id] of [['clarinete','objeto-clarinete'],['chelo','objeto-chelo']]){
  if(fs.existsSync(path.join(R,c+'.f32')))continue;
  const K=JSON.parse(fs.readFileSync(path.join(lib,'fichas',id+'.json'),'utf8')),y=new Float32Array(N);
  for(const e of P.eventos[c]){const z=O.nota(K,{midi:e.midi,vel:e.vel,dur:e.dur},cfg.sr),a=Math.round(e.t*cfg.sr);for(let j=0;j<z.length&&a+j<N;j++)y[a+j]+=z[j];}save(c,y);
 }
 if(!fs.existsSync(path.join(R,'guembri-drone.f32'))){const C=require(path.join(base,'fuentes/guembri/cuerda.js'));save('guembri-drone',C.render({dur:cfg.duracion,tipo:'guembri',notas:P.eventos['guembri-drone'].map(e=>({t:e.t,dur:e.dur,m:e.midi,v:e.vel,c:0})),semilla:22},cfg.sr));}
}
async function navegador(){
 const br=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});try{
 const pg=await br.newPage();await pg.setContent('<title>Interpretación de Por aquí también se baila</title>');
 await pg.exposeFunction('guardar',(name,b64,first)=>{let f=path.join(R,name+'.f32');if(first)fs.writeFileSync(f,Buffer.from(b64,'base64'),{flag:'wx'});else fs.appendFileSync(f,Buffer.from(b64,'base64'));});
 await pg.addScriptTag({content:`async function entrega(n,y){for(let i=0;i<y.length;i+=1<<19){let z=y.slice(i,i+(1<<19)),u=new Uint8Array(z.buffer),s='';for(let j=0;j<u.length;j+=32768)s+=String.fromCharCode(...u.subarray(j,j+32768));await guardar(n,btoa(s),i===0);}}`});
 if(mode==='todo'||mode==='biblioteca'){
  for(const f of ['web.js','meleeviewer.js'])await pg.addScriptTag({content:fs.readFileSync(path.join(lib,'motores',f),'utf8')});
  const channels=[['acordeon-tema','meleeviewer-13-acordeon'],['acordeon-respuesta','meleeviewer-13-acordeon'],['bajo-cumbia','meleeviewer-13-bajo'],['guiro','meleeviewer-13-guiro'],['conga','meleeviewer-13-conga'],['campana','meleeviewer-13-campana'],['bombo','bateria-tr808'],['caja','bateria-acustico'],['timbal','bateria-acustico'],['mbira-boca','mbira']];
  for(const [c,id] of channels){
   if(fs.existsSync(path.join(R,c+'.f32')))continue;
   const K=JSON.parse(fs.readFileSync(path.join(lib,'fichas',id+'.json'),'utf8')),source=K.motor==='meleeviewer'?fs.readFileSync(path.join(lib,K.fisica.escenario),'utf8'):null,Kmouth=JSON.parse(fs.readFileSync(path.join(lib,'fichas/arpaboca.json'),'utf8'));
   await pg.evaluate(async({c,K,Kmouth,source,events,sr,D})=>{
    const ctx=new OfflineAudioContext(1,Math.round(D*sr),sr);
    for(const e of events){
     const n={t:e.t,midi:e.midi,vel:e.vel,dur:e.dur,pieza:c==='bombo'?'kick':c==='caja'?'snare':'tomhi',tune:c==='timbal'?e.midi-62:0};
     if(K.motor==='meleeviewer')await InstrumentosMelee.tocar(ctx,ctx.destination,K,n,{fuente:async()=>source});
     else Instrumentos.tocar(ctx,ctx.destination,K,n,{tonica:'D'});
     if(c==='mbira-boca')Instrumentos.tocar(ctx,ctx.destination,Kmouth,{...n,vel:n.vel*.13},{tonica:'D'});
    }
    await entrega(c,(await ctx.startRendering()).getChannelData(0));
   },{c,K,Kmouth,source,events:P.eventos[c],sr:cfg.sr,D:cfg.duracion});console.log(c);
  }
 }
 if(mode==='todo'||mode==='voz'){
  for(const f of ['g2p.js','difonos.js'])await pg.addScriptTag({content:fs.readFileSync(path.join(base,'fuentes/difonos',f),'utf8')});
  const banco=path.join(base,'../inferencia/vendor/difonos/bancos/sabina-1-b44e7fab5cee'),M=JSON.parse(fs.readFileSync(path.join(banco,'manifiesto.json'),'utf8')),audio=fs.readFileSync(path.join(banco,'banco.flac')).toString('base64');
  for(const c of ['voz-verso','voz-respuesta','radio-chofer','radio-pasajera']){
   if(fs.existsSync(path.join(R,c+'.f32')))continue;
   const rec=await pg.evaluate(async({c,events,M,audio,sr,D})=>{
    const ctx=new OfflineAudioContext(1,Math.round(D*sr),sr),bytes=Uint8Array.from(atob(audio),a=>a.charCodeAt(0)),bank=new Difonos.Banco(ctx,await ctx.decodeAudioData(bytes.buffer),M);let ev=[];
    if(c.startsWith('radio')){
     for(const e of events){const words=e.texto.split(/\s+/).filter(Boolean),weights=words.map(w=>Math.max(.1,bank.difonos(DifonosG2P.frase(w)).reduce((a,d)=>a+bank.dur(d),0))),sum=weights.reduce((a,b)=>a+b,0);let t=e.t;
      words.forEach((w,j)=>{const d=e.dur*weights[j]/sum;ev.push({t,dur:d*.95,texto:w,nota:e.midi+[0,.4,.1,-.5,-.7][j%5]});t+=d;});}
    }else ev=events.map(e=>({t:e.t,dur:e.dur,texto:e.texto,nota:e.midi}));
    let q=[];const plan=bank.cantar(ctx.destination,ev,{modo:'psola',vibrato:c.startsWith('radio')?[0,0]:[4.7,.0016],rng:()=>.5,agendar:(t,f)=>q.push([t,f])});q.sort((a,b)=>a[0]-b[0]);const until=t=>{while(q.length&&q[0][0]<t)q.shift()[1]();};until(3);for(let k=2;k<D-.1;k+=2)ctx.suspend(k).then(()=>{until(k+3);ctx.resume();});await entrega(c,(await ctx.startRendering()).getChannelData(0));return {canal:c,eventos:ev.length,piezas:plan.piezas.length,modo:'PSOLA; radio con duraciones naturales relativas ajustadas a la partitura'};
   },{c,events:P.eventos[c],M,audio,sr:cfg.sr,D:cfg.duracion});fs.writeFileSync(path.join(out,'voz-'+c+'.json'),JSON.stringify(rec,null,2),{flag:'wx'});console.log(c);
  }
 }
 }finally{await br.close();}
}
(async()=>{if(mode==='todo'||mode==='objetos')await objetos();if(mode!=='objetos')await navegador();})().catch(e=>{console.error(e);process.exitCode=1;});
