const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/HP-PC/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const D=path.resolve(process.argv[2]),P=JSON.parse(fs.readFileSync(path.join(D,'partitura.json'),'utf8'));
const vendor=path.join(__dirname,'../inferencia/vendor/difonos'),bankDir=path.join(vendor,'bancos/sabina-1-b44e7fab5cee');
(async()=>{let browser;try{
 browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 const page=await browser.newPage();await page.setContent('<title>Voz local — Lo que puede venir</title>');
 for(const f of ['g2p.js','difonos.js'])await page.addScriptTag({content:fs.readFileSync(path.join(vendor,'runtime',f),'utf8')});
 for(const kind of ['voz','respuesta']){
  const result=await page.evaluate(async({P,M,audio,kind})=>{
   let seed=P.semilla;const rng=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
   const sr=48000,ctx=new OfflineAudioContext(2,Math.ceil(P.duracion*sr),sr),bin=Uint8Array.from(atob(audio),c=>c.charCodeAt(0));
   const bank=new Difonos.Banco(ctx,await ctx.decodeAudioData(bin.buffer),M),queue=[];
   for(const f of P.frases){
    let events=f.eventos,level=f.nivel,pan=0;
    if(kind==='respuesta'){
     if(![16,18,20,22,48,50,52,54,56,58].includes(f.bar))continue;
     events=f.eventos.slice(-2).map(e=>({...e,t:e.t+.12,nota:e.nota+12,dur:e.dur*.78}));level=.38;pan=f.bar%4===0?-.55:.55;
    }
    const gain=ctx.createGain(),panner=ctx.createStereoPanner();panner.pan.value=pan;gain.connect(panner).connect(ctx.destination);
    const begin=events[0].t,end=events.at(-1).t+events.at(-1).dur;
    gain.gain.setValueAtTime(level*.8,begin);gain.gain.linearRampToValueAtTime(level,(begin+end)*.5);gain.gain.linearRampToValueAtTime(level*.72,end);
    bank.cantar(gain,events,{modo:kind==='voz'?'psola':'velocidad',vibrato:kind==='voz'?[4.9,.0015]:[0,0],rng,agendar:(t,fn)=>queue.push([t,fn])});
   }
   queue.sort((a,b)=>a[0]-b[0]);const until=t=>{while(queue.length&&queue[0][0]<t)queue.shift()[1]();};until(3);
   for(let k=2;k<P.duracion-.1;k+=2)ctx.suspend(k).then(()=>{until(k+3);ctx.resume();});
   const buf=await ctx.startRendering(),n=buf.length,ab=new ArrayBuffer(44+n*8),v=new DataView(ab);
   const str=(o,s)=>{for(let i=0;i<s.length;i++)v.setUint8(o+i,s.charCodeAt(i));};
   str(0,'RIFF');v.setUint32(4,36+n*8,true);str(8,'WAVE');str(12,'fmt ');v.setUint32(16,16,true);v.setUint16(20,3,true);v.setUint16(22,2,true);v.setUint32(24,sr,true);v.setUint32(28,sr*8,true);v.setUint16(32,8,true);v.setUint16(34,32,true);str(36,'data');v.setUint32(40,n*8,true);
   const L=buf.getChannelData(0),R=buf.getChannelData(1);let peak=0;
   for(let i=0;i<n;i++){if(!Number.isFinite(L[i]+R[i]))throw Error('voz no finita');v.setFloat32(44+i*8,L[i],true);v.setFloat32(48+i*8,R[i],true);peak=Math.max(peak,Math.abs(L[i]),Math.abs(R[i]));}
   const wav=await new Promise(resolve=>{const r=new FileReader();r.onload=()=>resolve(r.result.split(',')[1]);r.readAsDataURL(new Blob([ab]));});return {wav,peak,duration:buf.duration};
  },{P,M:JSON.parse(fs.readFileSync(path.join(bankDir,'manifiesto.json'),'utf8')),audio:fs.readFileSync(path.join(bankDir,'banco.flac')).toString('base64'),kind});
  fs.writeFileSync(path.join(D,'render',kind+'.wav'),Buffer.from(result.wav,'base64'),{flag:'wx'});delete result.wav;
  fs.writeFileSync(path.join(D,kind+'-render.json'),JSON.stringify(result,null,2),{flag:'wx'});console.log(kind,result);
 }
}finally{if(browser)await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
