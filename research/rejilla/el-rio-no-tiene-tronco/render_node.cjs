/* El río no tiene tronco — capas de node: la garganta de río (motor/, nueva), la voz de agua (vozagua.js original) y los objetos
   que cantan de la copia fijada: agua, aves, el tambor que hace de tabla, el trombón con sordina del mar, el tam-tam frotado.
   La garganta pronuncia con el lector de Difonos (es-MX). Mono 48 kHz a <carpeta>/<capa>.f32; la garganta, estéreo (sus bocas).
     node render_node.cjs <carpeta> [capa…] */
const fs=require('fs'),path=require('path');
const dir=process.argv[2],solo=process.argv.slice(3),P=JSON.parse(fs.readFileSync(path.join(dir,'partitura.json'),'utf8')),SR=48000,D=P.duracion;
const OBJ=path.join(__dirname,P.instrumentos,'codigo/rejilla/research/rejilla/objetos/motor/');
const Pajaro=require(OBJ+'pajaro.js'),Agua=require(OBJ+'agua.js'),Gong=require(OBJ+'gong.js'),Metal=require(OBJ+'metal.js'),Tambor=require(OBJ+'tambor.js');
const VozAgua=require('../objetos/motor/vozagua.js'),Lector=require('../../../difonos/runtime/lector.js'),GR=require('./motor/garganta_rio.js');
const quiero=n=>!solo.length||solo.includes(n);
const guardar=(n,y)=>{fs.writeFileSync(path.join(dir,n+'.f32'),Buffer.from(Float32Array.from(y).buffer));let p=0,s=0;for(const v of y){p=Math.max(p,Math.abs(v));s+=v*v;}
  console.log(n.padEnd(14),(y.length/SR).toFixed(1)+' s','pico',p.toFixed(3),'rms',Math.sqrt(s/y.length).toFixed(4));};
const estereo=(n,o)=>{const x=new Float32Array(o.L.length*2);for(let i=0;i<o.L.length;i++){x[2*i]=o.L[i];x[2*i+1]=o.R[i];}fs.writeFileSync(path.join(dir,n+'.f32'),Buffer.from(x.buffer));console.log(n.padEnd(14),'(estéreo)');};
async function fonemas(evs){const cache={};for(const e of evs){if(e.fonemas)continue;const tx=(e.texto||'a').toLowerCase();
  if(!cache[tx]){const r=await Lector.readAsync(tx,{language:'es-MX',engine:'rules'});cache[tx]=r.words.flatMap(w=>w.phones);if(!cache[tx].length)cache[tx]=['a'];}e.fonemas=cache[tx];}return evs;}
(async()=>{const sem=P.semilla%9973,perfil=Float32Array.from(P.delta.perfil_rio),brazos=P.delta.brazos.map(b=>({secciones:b.secciones,area:2,pan:b.pan}));
 if(quiero('garganta')){await fonemas(P.garganta);
   estereo('garganta-coro',GR.render({dur:D,perfil,largo:1,brazos,eventos:P.garganta.filter(e=>e.voz==='coro'),semilla:sem},SR));
   estereo('garganta-mar',GR.render({dur:D,perfil,largo:1.6,brazos,eventos:P.garganta.filter(e=>e.voz==='mar'),semilla:sem+1},SR));}   /* el mar: un tubo más largo, más grave */
 if(quiero('vozagua'))guardar('vozagua',VozAgua.render({dur:D,eventos:P.vozagua,semilla:sem+2},SR));
 if(quiero('agua'))guardar('agua',Agua.render({dur:D,eventos:P.agua,semilla:sem+3},SR));
 if(quiero('aves'))guardar('aves',Pajaro.render({dur:D,eventos:P.aves,semilla:sem+4},SR));
 if(quiero('tabla'))guardar('tabla',Tambor.render({dur:D,eventos:P.tabla.map(e=>Object.assign({},e,e.curva?{}:{curva:undefined})),semilla:sem+5},SR));
 if(quiero('trombon'))guardar('trombon',Metal.render({dur:D,voz:'trombon',sordina:'harmon',notas:P.trombon,semilla:sem+6},SR));
 if(quiero('gong'))guardar('gong',Gong.render({dur:D,eventos:P.gong,semilla:sem+7},SR));
})();
