/* Lo que el agua dibuja — el drill (bombo y tarola de la TR-808, palmas de la frita) que toca la biblioteca en el navegador (web.js de la copia fijada), una pista estéreo
   por capa, 48 kHz, a <carpeta>/<capa>.f32 (L,R entrelazados). Servidor estático en herramientas/agent, puerto 8880.
     node render_web.cjs <carpeta> */
const {lanzarChromium}=require('../../../herramientas/navegador.cjs');const fs=require('fs'),path=require('path');
const dir=process.argv[2],P=JSON.parse(fs.readFileSync(path.join(dir,'partitura.json'),'utf8'));
const bib=path.resolve(__dirname,P.instrumentos||'../../../biblioteca-de-instrumentos');
(async()=>{const br=await lanzarChromium();const pg=await br.newPage();
 await pg.exposeFunction('guardar',(nombre,b64,primero)=>{fs[primero?'writeFileSync':'appendFileSync'](path.join(dir,nombre+'.f32'),Buffer.from(b64,'base64'),primero?{flag:'wx'}:{});});
 await pg.setContent('<title>Render local de batería</title>');for(const f of ['web.js','meleeviewer.js'])await pg.addScriptTag({content:fs.readFileSync(path.join(bib,'motores',f),'utf8')});const fichas={},fuentes={};for(const evs of Object.values(P.web))for(const e of evs){const k=fichas[e.ficha]||(fichas[e.ficha]=JSON.parse(fs.readFileSync(path.join(bib,'fichas',e.ficha+'.json'),'utf8')));if(k.motor==='meleeviewer')fuentes[k.fisica.escenario]=fs.readFileSync(path.join(bib,k.fisica.escenario),'utf8');}
 for(const [capa,evs] of Object.entries(P.web)){if(!evs.length)continue;const t0=Date.now();
  const n=await pg.evaluate(async([capa,evs,F,fuentes,dur,ton,esc])=>{const SR=48000,ctx=new OfflineAudioContext(2,Math.ceil(dur*SR),SR);
   for(const e of evs){
    const p=ctx.createStereoPanner();p.pan.value=e.pan||0;p.connect(ctx.destination);
    if(F[e.ficha].motor==='meleeviewer')await InstrumentosMelee.tocar(ctx,p,F[e.ficha],{t:e.t,midi:e.midi,vel:e.vel,dur:e.dur},{fuente:async r=>fuentes[r]});
    else Instrumentos.tocar(ctx,p,F[e.ficha],{t:e.t,midi:e.midi,vel:e.vel,dur:e.dur,pieza:e.pieza},{tonica:e.tonica??ton,escala:esc});}
   const b=await ctx.startRendering(),L=b.getChannelData(0),R=b.getChannelData(1),N=L.length,PASO=1<<20;
   for(let i=0;i<N;i+=PASO){const m=Math.min(PASO,N-i),x=new Float32Array(2*m);for(let k=0;k<m;k++){x[2*k]=L[i+k];x[2*k+1]=R[i+k];}
    const u=new Uint8Array(x.buffer);let s='';for(let j=0;j<u.length;j+=32768)s+=String.fromCharCode(...u.subarray(j,j+32768));await window.guardar(capa,btoa(s),i===0);}
   return N;},[capa,evs,fichas,fuentes,P.duracion,P.tonica,P.escala]);
  console.log(capa.padEnd(14),evs.length,'notas',(n/48000).toFixed(1)+' s',(Date.now()-t0)+' ms');}
 await br.close();})().catch(e=>{console.error(e);process.exitCode=1});
