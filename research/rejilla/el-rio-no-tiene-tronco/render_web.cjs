/* El río no tiene tronco — las capas que toca la biblioteca en el navegador (web.js de la copia fijada), una pista estéreo
   por capa, 48 kHz, a <carpeta>/<capa>.f32 (L,R entrelazados). Servidor estático en herramientas/agent, puerto 8880.
     node render_web.cjs <carpeta> */
const {chromium}=require('playwright');const fs=require('fs'),path=require('path');
const dir=process.argv[2],P=JSON.parse(fs.readFileSync(path.join(dir,'partitura.json'),'utf8'));
const BASE='/research/rejilla/el-rio-no-tiene-tronco/'+P.instrumentos+'/';
(async()=>{const br=await chromium.launch({channel:'msedge',headless:true});const pg=await br.newPage();
 await pg.exposeFunction('guardar',(nombre,b64,primero)=>{fs[primero?'writeFileSync':'appendFileSync'](path.join(dir,nombre+'.f32'),Buffer.from(b64,'base64'));});
 await pg.goto('http://127.0.0.1:8880'+BASE+'manifiesto.json');await pg.addScriptTag({url:BASE+'motores/web.js'});
 for(const [capa,evs] of Object.entries(P.web)){if(!evs.length)continue;const t0=Date.now();
  const n=await pg.evaluate(async([capa,evs,BASE,dur,ton,esc])=>{const SR=48000,ctx=new OfflineAudioContext(2,Math.ceil(dur*SR),SR),F={};
   for(const e of evs){F[e.ficha]=F[e.ficha]||await (await fetch(BASE+'fichas/'+e.ficha+'.json')).json();
    const p=ctx.createStereoPanner();p.pan.value=e.pan||0;p.connect(ctx.destination);
    Instrumentos.tocar(ctx,p,F[e.ficha],{t:e.t,midi:e.midi,vel:e.vel,dur:e.dur,pieza:e.pieza},{tonica:e.tonica??ton,escala:esc});}
   const b=await ctx.startRendering(),L=b.getChannelData(0),R=b.getChannelData(1),N=L.length,PASO=1<<20;
   for(let i=0;i<N;i+=PASO){const m=Math.min(PASO,N-i),x=new Float32Array(2*m);for(let k=0;k<m;k++){x[2*k]=L[i+k];x[2*k+1]=R[i+k];}
    const u=new Uint8Array(x.buffer);let s='';for(let j=0;j<u.length;j+=32768)s+=String.fromCharCode(...u.subarray(j,j+32768));await window.guardar(capa,btoa(s),i===0);}
   return N;},[capa,evs,BASE,P.duracion,P.tonica,P.escala]);
  console.log(capa.padEnd(14),evs.length,'notas',(n/48000).toFixed(1)+' s',(Date.now()-t0)+' ms');}
 await br.close();})();
