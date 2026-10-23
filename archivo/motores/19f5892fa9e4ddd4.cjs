const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/HP-PC/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const out=path.resolve(process.argv[2]),P=JSON.parse(fs.readFileSync(path.join(out,'partitura.json'),'utf8')),vendor=path.resolve(__dirname,'../inferencia/vendor/difonos'),bankDir=path.join(vendor,'bancos/sabina-1-b44e7fab5cee');
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});try{
 const page=await browser.newPage();await page.setContent('<title>Lo que tiembla adentro · moduladoras nuevas</title>');
 for(const name of ['g2p.js','difonos.js'])await page.addScriptTag({content:fs.readFileSync(path.join(vendor,'runtime',name),'utf8')});
 const result=await page.evaluate(async({P,M,audio})=>{
  const sr=48000,ctx=new OfflineAudioContext(3,Math.ceil(P.duracion*sr),sr),bytes=Uint8Array.from(atob(audio),c=>c.charCodeAt(0));
  const bank=new Difonos.Banco(ctx,await ctx.decodeAudioData(bytes.buffer),M),queue=[],merge=ctx.createChannelMerger(3);merge.connect(ctx.destination);
  for(const f of P.frases){
   const g=ctx.createGain(),channel={'aire':0,'cobre-luz':1,'palo':2}[f.voz];g.connect(merge,0,channel);
   const a=f.eventos[0].t,z=f.eventos.at(-1).t+f.eventos.at(-1).dur;g.gain.setValueAtTime(f.nivel*.82,Math.max(0,a-.1));g.gain.linearRampToValueAtTime(f.nivel,a+.2);g.gain.setValueAtTime(f.nivel,z-.15);g.gain.linearRampToValueAtTime(f.nivel*.78,z);
   bank.cantar(g,f.eventos,{modo:'psola',vibrato:[4.2,.0011],agendar:(t,fn)=>queue.push([t,fn])});
  }
  queue.sort((a,b)=>a[0]-b[0]);const until=t=>{while(queue.length&&queue[0][0]<t)queue.shift()[1]();};until(3);
  for(let t=2;t<P.duracion-.1;t+=2)ctx.suspend(t).then(()=>{until(t+3);ctx.resume();});
  const buf=await ctx.startRendering(),N=buf.length,ab=new ArrayBuffer(44+N*3*4),v=new DataView(ab),str=(o,s)=>{for(let i=0;i<s.length;i++)v.setUint8(o+i,s.charCodeAt(i));};
  str(0,'RIFF');v.setUint32(4,36+N*12,true);str(8,'WAVE');str(12,'fmt ');v.setUint32(16,16,true);v.setUint16(20,3,true);v.setUint16(22,3,true);v.setUint32(24,sr,true);v.setUint32(28,sr*12,true);v.setUint16(32,12,true);v.setUint16(34,32,true);str(36,'data');v.setUint32(40,N*12,true);
  const x=[0,1,2].map(c=>buf.getChannelData(c));let peak=0;for(let i=0;i<N;i++)for(let c=0;c<3;c++){const z=x[c][i];if(!Number.isFinite(z))throw Error('Voz no finita');peak=Math.max(peak,Math.abs(z));v.setFloat32(44+(i*3+c)*4,z,true);}
  const wav=await new Promise(resolve=>{const r=new FileReader();r.onload=()=>resolve(r.result.split(',')[1]);r.readAsDataURL(new Blob([ab]));});return {wav,peak};
 },{P,M:JSON.parse(fs.readFileSync(path.join(bankDir,'manifiesto.json'),'utf8')),audio:fs.readFileSync(path.join(bankDir,'banco.flac')).toString('base64')});
 fs.writeFileSync(path.join(out,'render','moduladoras.wav'),Buffer.from(result.wav,'base64'),{flag:'wx'});console.log('Tres moduladoras PSOLA',result.peak);
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
