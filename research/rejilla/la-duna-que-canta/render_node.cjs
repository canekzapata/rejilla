/* La duna que canta — capas de node: la duna que canta (motor/duna.js: Kuramoto de granos; y una segunda duna más fina), el viento
   que lee las crestas (viento.js de la copia fijada de la biblioteca), la garganta de duna (motor/garganta_duna.js: los glisandos de
   Ryoan-ji y el tenor), el guembri y la guitarra del desierto (motor/cuerda.js). Mono 48 kHz a <carpeta>/<capa>.f32; la duna y el
   viento salen estéreo (L,R entrelazados).
     node render_node.cjs <carpeta> [capa…] */
const fs=require('fs'),path=require('path');
const dir=process.argv[2],solo=process.argv.slice(3),P=JSON.parse(fs.readFileSync(path.join(dir,'partitura.json'),'utf8')),SR=48000,D=P.duracion;
const C=path.join(__dirname,P.instrumentos,'codigo/rejilla/research/rejilla/lo-que-tapa-la-traspuesta/motor/');
const Viento=require(C+'viento.js'),Garganta=require('./motor/garganta_duna.js'),Duna=require('./motor/duna.js'),Cuerda=require('./motor/cuerda.js'),Lector=require('../../../difonos/runtime/lector.js');
const quiero=n=>!solo.length||solo.includes(n);
const stats=(n,y,est)=>{let p=0,s=0;for(const v of y){p=Math.max(p,Math.abs(v));s+=v*v;}console.log(n.padEnd(12),est?'(estéreo)':'',(y.length/SR/(est?2:1)).toFixed(1)+' s','pico',p.toFixed(3),'rms',Math.sqrt(s/y.length).toFixed(4));};
const guardar=(n,y)=>{fs.writeFileSync(path.join(dir,n+'.f32'),Buffer.from(Float32Array.from(y).buffer));stats(n,y);};
const guardar2=(n,L,R)=>{const o=new Float32Array(L.length*2);for(let i=0;i<L.length;i++){o[2*i]=L[i];o[2*i+1]=R[i];}fs.writeFileSync(path.join(dir,n+'.f32'),Buffer.from(o.buffer));stats(n,o,1);};
async function fonemas(evs){const cache={};for(const e of evs){if(e.fonemas)continue;const tx=(e.texto||'a').toLowerCase();
  if(!cache[tx]){const r=await Lector.readAsync(tx,{language:'es-MX',engine:'rules'});cache[tx]=r.words.flatMap(w=>w.phones);if(!cache[tx].length)cache[tx]=['a'];}e.fonemas=cache[tx];}return evs;}
(async()=>{const sem=P.semilla,perfiles=P.perfiles.map(([t,p])=>[t,Float32Array.from(p)]);
 if(quiero('duna')){const y=Duna.render({dur:D,...P.duna,M:96,semilla:sem},SR);guardar2('duna',y.L,y.R);
   fs.writeFileSync(path.join(dir,'duna-coherencia.json'),JSON.stringify(Array.from(y.r,v=>+v.toFixed(3))));}
 if(quiero('duna2')){const y=Duna.render({dur:D,...P.duna2,M:72,sigma:.05,semilla:sem+1},SR);guardar2('duna2',y.L,y.R);}
 if(quiero('duna-voz')){   /* la duna que dice la letra: sus choques siguen la melodía de la soprano (la portadora del vocoder de duna) */
   const E=P.sabina.find(c=>c.capa==='soprano').eventos.slice().sort((a,b)=>a.t-b.t),f=[],fl=[],hz=m=>440*2**((m-69)/12);
   for(const e of E){f.push([e.t-.03,hz(e.nota)],[e.t+e.dur,hz(e.nota)]);fl.push([e.t-.06,0],[e.t-.02,1],[e.t+e.dur+.05,1],[e.t+e.dur+.12,0]);}
   const y=Duna.render({dur:D,f,K:[[0,3.5]],flujo:fl,M:64,sigma:.04,cuerpo:.5,semilla:sem+2},SR);guardar2('duna-voz',y.L,y.R);}
 if(quiero('viento')){const v=Viento.render({dur:D,perfiles,...P.viento,semilla:sem+3},SR);guardar2('viento',v.L,v.R);}
 if(quiero('garganta')){await fonemas(P.garganta);
   guardar('garganta',Garganta.render({dur:D,perfiles,largo:1.6,eventos:P.garganta.filter(e=>!e.solo),semilla:sem},SR));
   guardar('garganta-final',Garganta.render({dur:D,perfiles,largo:1.3,eventos:P.garganta.filter(e=>e.solo),semilla:sem+1},SR));}
 if(quiero('guembri'))guardar('guembri',Cuerda.render({dur:D,tipo:'guembri',notas:P.guembri,semilla:sem+5},SR));
 if(quiero('guitarra')){guardar('guitarra',Cuerda.render({dur:D,tipo:'guitarra',notas:P.guitarra.filter(n=>!n.solo),semilla:sem+6},SR));
   guardar('guitarra-solo',Cuerda.render({dur:D,tipo:'guitarra',notas:P.guitarra.filter(n=>n.solo),semilla:sem+7},SR));}
})();
