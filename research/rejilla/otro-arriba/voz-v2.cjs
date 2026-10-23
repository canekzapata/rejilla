const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/HP-PC/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const out=path.resolve(process.argv[2]),P=JSON.parse(fs.readFileSync(path.join(out,'partitura.json'),'utf8')),vendor=path.resolve(__dirname,'../inferencia/vendor/difonos'),bankDir=path.join(vendor,'bancos/sabina-1-b44e7fab5cee');
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});try{
 const page=await browser.newPage();await page.setContent('<title>Otro arriba · fraseo v2</title>');
 for(const name of ['g2p.js','difonos.js'])await page.addScriptTag({content:fs.readFileSync(path.join(vendor,'runtime',name),'utf8')});
 const result=await page.evaluate(async({P,M,audio})=>{
  const sr=48000,ctx=new OfflineAudioContext(1,Math.ceil(P.duracion*sr),sr),bytes=Uint8Array.from(atob(audio),c=>c.charCodeAt(0));
  const bank=new Difonos.Banco(ctx,await ctx.decodeAudioData(bytes.buffer),M),queue=[],plans=[];
  let seed=P.semilla;const rng=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
  for(const f of P.frases){
   const g=ctx.createGain();g.connect(ctx.destination);const start=f.eventos[0].t-.05,end=f.eventos.at(-1).t+f.eventos.at(-1).dur;
   g.gain.setValueAtTime(f.nivel*.82,start);g.gain.linearRampToValueAtTime(f.nivel,start+.25);
   for(let i=0;i<f.eventos.length;i++){
    const e=f.eventos[i],strength=e.acento?1.09:e.fin_palabra?1.01:.94;
    const arc=.95+.08*Math.sin(Math.PI*(e.t-start)/(end-start));
    g.gain.linearRampToValueAtTime(f.nivel*strength*arc,e.t+Math.min(.07,e.dur*.2));
   }
   g.gain.linearRampToValueAtTime(f.nivel*.83,end);
   const plan=bank.plan(f.eventos,{modo:'psola'});let gap=0;for(let i=1;i<plan.length;i++)gap+=Math.max(0,plan[i].t-(plan[i-1].t+plan[i-1].dur));plans.push({id:f.id,piezas:plan.length,huecos_plan_s:gap});
   bank.cantar(g,f.eventos,{modo:'psola',vibrato:[4.7,.0014],rng,agendar:(t,fn)=>queue.push([t,fn])});
  }
  queue.sort((a,b)=>a[0]-b[0]);const until=t=>{while(queue.length&&queue[0][0]<t)queue.shift()[1]();};until(3);
  for(let t=2;t<P.duracion-.1;t+=2)ctx.suspend(t).then(()=>{until(t+3);ctx.resume();});
  const buf=await ctx.startRendering(),x=buf.getChannelData(0),ab=new ArrayBuffer(44+x.length*4),v=new DataView(ab);
  const str=(o,s)=>{for(let i=0;i<s.length;i++)v.setUint8(o+i,s.charCodeAt(i));};str(0,'RIFF');v.setUint32(4,36+x.length*4,true);str(8,'WAVE');str(12,'fmt ');v.setUint32(16,16,true);v.setUint16(20,3,true);v.setUint16(22,1,true);v.setUint32(24,sr,true);v.setUint32(28,sr*4,true);v.setUint16(32,4,true);v.setUint16(34,32,true);str(36,'data');v.setUint32(40,x.length*4,true);
  let peak=0;for(let i=0;i<x.length;i++){if(!Number.isFinite(x[i]))throw Error('Voz no finita');v.setFloat32(44+i*4,x[i],true);peak=Math.max(peak,Math.abs(x[i]));}
  const wav=await new Promise(resolve=>{const r=new FileReader();r.onload=()=>resolve(r.result.split(',')[1]);r.readAsDataURL(new Blob([ab]));});return {wav,peak,plans};
 },{P,M:JSON.parse(fs.readFileSync(path.join(bankDir,'manifiesto.json'),'utf8')),audio:fs.readFileSync(path.join(bankDir,'banco.flac')).toString('base64')});
 fs.writeFileSync(path.join(out,'render','voz-v2.wav'),Buffer.from(result.wav,'base64'),{flag:'wx'});delete result.wav;fs.writeFileSync(path.join(out,'voz-plan-v2.json'),JSON.stringify(result,null,2),{flag:'wx'});console.log('Voz ligada v2',result.peak);
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
