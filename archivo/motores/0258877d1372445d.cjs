/* Original fixed library routes and Sabina PSOLA; no generic family substitutions. */
const fs=require('fs'),path=require('path');
const zlib=require('zlib');
const BASE=__dirname,OUT=process.env.LUCI_AUDIO_OUT||path.join(BASE,fs.readFileSync(path.join(BASE,'REALIZACION-ACTUAL.txt'),'utf8').trim());
const P=JSON.parse(fs.readFileSync(path.join(OUT,'partitura.json'),'utf8')),SR=48000;
const FIX=path.join(BASE,'luciernagas-reescritura-s1-29d4afe5aad2','realizacion'),BIB=path.join(FIX,'biblioteca');
const mode=process.argv[2],only=process.argv.slice(3);
const save=(name,y)=>{const file=path.join(OUT,'render',name+'.f32.gz');if(fs.existsSync(file))throw Error('No sobrescribir '+file);fs.writeFileSync(file,zlib.gzipSync(Buffer.from(y.buffer,y.byteOffset,y.byteLength),{level:3}));};
const {chromium}=require('C:/Users/HP-PC/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
async function browser(mode){
 const br=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 try{
 const pg=await br.newPage();await pg.setContent('<title>Luciérnagas · realización instrumental</title>');
 const begun=new Set();await pg.exposeFunction('guardar',(name,b64)=>{const f=path.join(OUT,'render',name+'.f32.gz'),data=zlib.gzipSync(Buffer.from(b64,'base64'),{level:3});
  if(!begun.has(name)){if(fs.existsSync(f))throw Error('No sobrescribir '+f);begun.add(name);fs.writeFileSync(f,data);}
  else fs.appendFileSync(f,data);});
 if(mode==='voz'){
  const vendor=path.resolve(BASE,'../inferencia/vendor/difonos'),bank=path.join(vendor,'bancos/sabina-1-b44e7fab5cee');
  let runtime=fs.readFileSync(path.join(vendor,'runtime/difonos.js'),'utf8');
  runtime=runtime.replace('fuente = function (tau) { return srcA + (tau - o0); };','fuente = function (tau) { return (u.inicio + u.izq) * k + (tau - p.t * srD) * (p.tasa_tiempo || 1); };');
  runtime+=`\n(function(){const original=Difonos.Banco.prototype.cantar_plan;Difonos.Banco.prototype.cantar_plan=function(es,op){
    const plan=original.call(this,es,{...op,adelanto:0}),groups=es.map(()=>[]);for(const p of plan)groups[p.palabra].push(p);
    for(let i=0;i<groups.length;i++){const g=groups[i];if(!g.length)continue;const a=Math.min(...g.map(p=>p.t)),b=Math.max(...g.map(p=>p.t+p.dur)),scale=es[i].dur/(b-a);
      for(const p of g){p.t=es[i].t+(p.t-a)*scale;p.dur*=scale;p.tasa_tiempo=1/scale;}}
    return plan;};})();`;
  fs.mkdirSync(path.join(OUT,'fuentes'),{recursive:true});fs.writeFileSync(path.join(OUT,'fuentes/difonos-prosodia.js'),runtime);
  await pg.addScriptTag({content:fs.readFileSync(path.join(vendor,'runtime/g2p.js'),'utf8')});await pg.addScriptTag({content:runtime});
  const M=JSON.parse(fs.readFileSync(path.join(bank,'manifiesto.json'),'utf8')),audio=fs.readFileSync(path.join(bank,'banco.flac')).toString('base64');
  for(const name of ['voz','duo','corocuerda','corojunco']){
   if(only.length&&!only.includes(name))continue;const start=Date.now();
   if(fs.existsSync(path.join(OUT,'render','prosodia-'+name+'.f32.gz')))continue;
   const result=await pg.evaluate(async({P,M,audio,name,SR})=>{
    const ctx=new OfflineAudioContext(2,Math.ceil(P.duracion*SR),SR);
    const data=Uint8Array.from(atob(audio),c=>c.charCodeAt(0));const bank=new Difonos.Banco(ctx,await ctx.decodeAudioData(data.buffer),M);
    const phrases={};for(const e of P.eventos[name]){(phrases[e.frase]??=[]).push(e);}
    const q=[];let seed=P.semilla;const rng=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
    for(const es of Object.values(phrases)){
     const g=ctx.createGain(),pan=ctx.createStereoPanner();pan.pan.value=es[0].pan??0;g.connect(pan).connect(ctx.destination);
     g.gain.value=.8;for(const e of es){g.gain.setValueAtTime(e.acento?1:.77,Math.max(0,e.t-.012));}
     bank.cantar(g,es.map(e=>({t:e.t,dur:e.dur,texto:e.texto,nota:e.midi,pausa:e.respiracion_antes})),
        {modo:'psola',vibrato:[4.8,.0017],rng,agendar:(t,f)=>q.push([t,f])});
    }
    q.sort((a,b)=>a[0]-b[0]);const until=t=>{while(q.length&&q[0][0]<t)q.shift()[1]();};until(3);
    for(let t=2;t<P.duracion-.1;t+=2)ctx.suspend(t).then(()=>{until(t+3);ctx.resume();});
    const b=await ctx.startRendering();let peak=0;
    for(let i=0;i<b.length;i+=1<<18){const n=Math.min(1<<18,b.length-i),o=new Float32Array(2*n),L=b.getChannelData(0),R=b.getChannelData(1);
     for(let k=0;k<n;k++){o[2*k]=L[i+k];o[2*k+1]=R[i+k];peak=Math.max(peak,Math.abs(o[2*k]),Math.abs(o[2*k+1]));}
     const u=new Uint8Array(o.buffer);let s='';for(let k=0;k<u.length;k+=32768)s+=String.fromCharCode(...u.subarray(k,k+32768));await window.guardar('prosodia-'+name,btoa(s));}
    return {peak,frames:b.length,frases:Object.keys(phrases).length};
   },{P,M,audio,name,SR});console.log(name,result,Date.now()-start,'ms');
  }
 }else{
  for(const file of ['web.js','meleeviewer.js'])await pg.addScriptTag({content:fs.readFileSync(path.join(BIB,'motores',file),'utf8')});
  let accumulated;await pg.exposeFunction('trozo',(at,b64)=>{const b=Buffer.from(b64,'base64'),x=new Float32Array(b.buffer,b.byteOffset,b.length/4),offset=Math.round(at*SR)*2;
   for(let k=0;k<x.length&&offset+k<accumulated.length;k++)accumulated[offset+k]+=x[k];});
  const routes={krar:'meleeviewer-3-krar',berimbau:'berimbau',mbira:'mbira',arpaboca:'arpaboca',
   bombo:'bateria-acustico',caja:'bateria-acustico',hat:'bateria-acustico',tom:'bateria-acustico',aro:'bateria-acustico',ride:'bateria-acustico'};
  for(const [name,ficha] of Object.entries(routes)){
   if(only.length&&!only.includes(name))continue;
   if(fs.existsSync(path.join(OUT,'render',name+'.f32.gz')))continue;
   const K=JSON.parse(fs.readFileSync(path.join(BIB,'fichas',ficha+'.json'),'utf8'));
   const scenario=K.motor==='meleeviewer'?fs.readFileSync(path.join(BIB,K.fisica.escenario),'utf8'):'';
   const start=Date.now();accumulated=new Float32Array(Math.ceil(P.duracion*SR)*2);
   // These fixed web engines make independent note nodes. Chunking changes allocation,
   // not their signal or onset: complete native tails overlap in the accumulation buffer.
   for(let at=0;at<P.duracion;at+=12){
    const es=P.eventos[name].filter(e=>e.t>=at&&e.t<at+12);if(!es.length)continue;
    const dur=Math.min(P.duracion-at,Math.max(...es.map(e=>e.t-at+e.dur))+4);
    const pan=P.partes.find(p=>p.id===name).pan;
    await pg.evaluate(async({es,K,scenario,SR,at,dur,panValue})=>{
    const ctx=new OfflineAudioContext(2,Math.ceil(dur*SR),SR);const pan=ctx.createStereoPanner();pan.pan.value=panValue;pan.connect(ctx.destination);
    for(const e of es){
     const n={...e,t:e.t-at,midi:e.midi,vel:e.vel,dur:e.dur};
     if(K.motor==='meleeviewer')await InstrumentosMelee.tocar(ctx,pan,K,n,{fuente:async()=>scenario});
     else Instrumentos.tocar(ctx,pan,K,n,{tonica:'E',escala:[0,1,3,5,7,8,10]});
    }
    const b=await ctx.startRendering();
    for(let i=0;i<b.length;i+=1<<18){const n=Math.min(1<<18,b.length-i),o=new Float32Array(2*n),L=b.getChannelData(0),R=b.getChannelData(1);
     for(let k=0;k<n;k++){o[2*k]=L[i+k];o[2*k+1]=R[i+k];}
     const u=new Uint8Array(o.buffer);let s='';for(let k=0;k<u.length;k+=32768)s+=String.fromCharCode(...u.subarray(k,k+32768));await window.trozo(at+i/SR,btoa(s));}
   },{es,K,scenario,SR,at,dur,panValue:pan});
   }
   save(name,accumulated);accumulated=null;if(global.gc)global.gc();console.log(name,P.eventos[name].length,'notas',Date.now()-start,'ms');
  }
 }
 }finally{await br.close();}
}
async function objetos(){
 const O=require(path.join(BIB,'motores/objetos.js'));const routes={clarinete:'objeto-clarinete',chelo:'objeto-chelo',contrabajo:'objeto-contrabajo',piano:'objeto-piano-papel',waterphone:'objeto-waterphone',gong:'objeto-gong-dos-alturas'};
 for(const [name,ficha] of Object.entries(routes)){
  if(only.length&&!only.includes(name))continue;
  const start=Date.now(),K=JSON.parse(fs.readFileSync(path.join(BIB,'fichas',ficha+'.json'),'utf8'));
  const y=new Float32Array(Math.ceil(P.duracion*SR)*2);
  for(const e of P.eventos[name]){
   // The wrapper's fixed .05-second instrument onset is compensated exactly.
   const a=O.nota(K,{midi:e.midi,vel:e.vel,dur:e.dur},SR);const off=Math.round(.05*SR),at=Math.round(e.t*SR);
   const pan=(e.pan+1)*Math.PI/4,l=Math.cos(pan),r=Math.sin(pan);
   for(let i=off;i<a.length&&at+i-off<y.length/2;i++){const j=2*(at+i-off);y[j]+=a[i]*l;y[j+1]+=a[i]*r;}
  }
  save(name,y);console.log(name,'motor original',P.eventos[name].length,'notas',Date.now()-start,'ms');
 }
}
(mode==='objetos'?objetos():browser(mode)).catch(e=>{console.error(e);process.exitCode=1;});
