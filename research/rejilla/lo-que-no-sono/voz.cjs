// Render fuera de línea con el banco y runtime locales de Difonos; ninguna cuenta ni navegador personal.
const fs=require('fs'), path=require('path'), cp=require('child_process');
const {chromium}=require('C:/Users/HP-PC/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const dir=path.resolve(process.argv[2]), plan=JSON.parse(fs.readFileSync(path.join(dir,'partitura.json'),'utf8'));
const vendor=path.join(__dirname,'../inferencia/vendor/difonos');
(async()=>{
 let browser;
 try{
  browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
  const page=await browser.newPage(); await page.setContent('<title>Render local de voz</title>');
  for(const f of ['g2p.js','difonos.js'])await page.addScriptTag({content:fs.readFileSync(path.join(vendor,'runtime',f),'utf8')});
  const bankDir=path.join(vendor,'bancos/sabina-1-b44e7fab5cee');
  const result=await page.evaluate(async ({P,M,audio})=>{
   let seed=P.semilla;const rng=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
   const sr=48000,ctx=new OfflineAudioContext(2,Math.ceil(P.duracion*sr),sr);
   const bin=Uint8Array.from(atob(audio),c=>c.charCodeAt(0));
   const bank=new Difonos.Banco(ctx,await ctx.decodeAudioData(bin.buffer),M);
   let queue=[];const en=(t,f)=>{queue.push([t,f]);};
   for(const frase of P.frases){
    const gain=ctx.createGain(),pan=ctx.createStereoPanner();gain.gain.value=frase.nivel;pan.pan.value=frase.pan;gain.connect(pan).connect(ctx.destination);
    bank.cantar(gain,frase.eventos,{modo:'psola',vibrato:[4.6,.002],rng,agendar:en});
   }
   queue.sort((a,b)=>a[0]-b[0]);const hasta=t=>{while(queue.length&&queue[0][0]<t)queue.shift()[1]();};hasta(3);
   for(let k=2;k<P.duracion-.1;k+=2){ctx.suspend(k).then(()=>{hasta(k+3);ctx.resume();});}
   const buf=await ctx.startRendering(),n=buf.length,ab=new ArrayBuffer(44+n*8),v=new DataView(ab);
   const str=(o,s)=>{for(let i=0;i<s.length;i++)v.setUint8(o+i,s.charCodeAt(i));};
   str(0,'RIFF');v.setUint32(4,36+n*8,true);str(8,'WAVE');str(12,'fmt ');v.setUint32(16,16,true);v.setUint16(20,3,true);v.setUint16(22,2,true);v.setUint32(24,sr,true);v.setUint32(28,sr*8,true);v.setUint16(32,8,true);v.setUint16(34,32,true);str(36,'data');v.setUint32(40,n*8,true);
   let L=buf.getChannelData(0),R=buf.getChannelData(1),peak=0;
   for(let i=0;i<n;i++){v.setFloat32(44+i*8,L[i],true);v.setFloat32(48+i*8,R[i],true);peak=Math.max(peak,Math.abs(L[i]),Math.abs(R[i]));}
   const encoded=await new Promise(resolve=>{let r=new FileReader();r.onload=()=>resolve(r.result.split(',')[1]);r.readAsDataURL(new Blob([ab]));});
   return {pico:peak,frases:P.frases.length,segundos:buf.duration,wav:encoded};
  },{P:plan,M:JSON.parse(fs.readFileSync(path.join(bankDir,'manifiesto.json'),'utf8')),audio:fs.readFileSync(path.join(bankDir,'banco.flac')).toString('base64')});
  fs.writeFileSync(path.join(dir,'render','voz.wav'),Buffer.from(result.wav,'base64'),{flag:'wx'});delete result.wav;
  fs.writeFileSync(path.join(dir,'voz-render.json'),JSON.stringify(result,null,2),{flag:'wx'});console.log(result);
 }finally{if(browser)await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
