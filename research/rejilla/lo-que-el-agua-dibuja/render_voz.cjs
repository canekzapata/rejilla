/* Lo que el agua dibuja — Sabina (Difonos, PSOLA): la voz del blues, su doble, las respuestas (tres voces), el rap del drill, los chops y el río (que sólo modula el vocoder). Una capa por
   línea, estéreo 48 kHz, a <carpeta>/sabina-<capa>.f32. Banco y runtime
   locales (inferencia/vendor/difonos), sin cuentas ni navegador personal.
     node render_voz.cjs <carpeta> */
const fs=require('fs'),path=require('path');
const {lanzarChromium}=require('../../../herramientas/navegador.cjs');
const dir=path.resolve(process.argv[2]),P=JSON.parse(fs.readFileSync(path.join(dir,'partitura.json'),'utf8'));
const vendor=path.resolve(__dirname,'../../../difonos'),bankDir=path.join(vendor,'bancos/sabina-1-b44e7fab5cee');
(async()=>{let browser;
 try{browser=await lanzarChromium();
  const page=await browser.newPage();await page.setContent('<title>Render local de voz</title>');
  for(const f of ['g2p.js','difonos.js'])await page.addScriptTag({content:fs.readFileSync(path.join(vendor,'runtime',f),'utf8')});
  await page.exposeFunction('guardar',(nombre,b64,primero)=>{fs[primero?'writeFileSync':'appendFileSync'](path.join(dir,nombre+'.f32'),Buffer.from(b64,'base64'),primero?{flag:'wx'}:{});});
  const M=JSON.parse(fs.readFileSync(path.join(bankDir,'manifiesto.json'),'utf8')),audio=fs.readFileSync(path.join(bankDir,'banco.flac')).toString('base64');
  for(const capa of [...new Set(P.sabina.map(f=>f.capa))]){
   const r=await page.evaluate(async({P,M,audio,capa})=>{
    let seed=P.semilla+capa.length;const rng=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
    const sr=48000,ctx=new OfflineAudioContext(2,Math.ceil(P.duracion*sr),sr);
    const bin=Uint8Array.from(atob(audio),c=>c.charCodeAt(0)),bank=new Difonos.Banco(ctx,await ctx.decodeAudioData(bin.buffer),M);
    let q=[];const en=(t,f)=>{q.push([t,f]);};
    for(const fr of P.sabina.filter(f=>f.capa===capa)){const g=ctx.createGain(),p=ctx.createStereoPanner();g.gain.value=fr.nivel;p.pan.value=fr.pan;g.connect(p).connect(ctx.destination);
     bank.cantar(g,fr.eventos,{modo:'psola',vibrato:[4.8,.002],rng,agendar:en});}
    q.sort((a,b)=>a[0]-b[0]);const hasta=t=>{while(q.length&&q[0][0]<t)q.shift()[1]();};hasta(3);
    for(let k=2;k<P.duracion-.1;k+=2){ctx.suspend(k).then(()=>{hasta(k+3);ctx.resume();});}
    const b=await ctx.startRendering(),L=b.getChannelData(0),R=b.getChannelData(1),N=L.length,PASO=1<<20;let pico=0;
    for(let i=0;i<N;i+=PASO){const m=Math.min(PASO,N-i),x=new Float32Array(2*m);for(let k=0;k<m;k++){x[2*k]=L[i+k];x[2*k+1]=R[i+k];pico=Math.max(pico,Math.abs(L[i+k]));}
     const u=new Uint8Array(x.buffer);let s='';for(let j=0;j<u.length;j+=32768)s+=String.fromCharCode(...u.subarray(j,j+32768));await window.guardar('sabina-'+capa,btoa(s),i===0);}
    return {pico,segundos:N/sr};},{P,M,audio,capa});
   console.log('sabina-'+capa,r);}
 }finally{if(browser)await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
