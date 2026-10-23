/* Las islas del cielo — capas de node: las arpas llaneras (la de la meseta y una por isla) y el cuatro (motor/cuerda.js, la cuerda de
   «La duna» con cuerpos de arpa y de cuatro) y las aves con dialecto (pajaro.js de la copia fijada). 48 kHz.
     node render_node.cjs <carpeta> [capa…] */
const fs=require('fs'),path=require('path');
const dir=process.argv[2],solo=process.argv.slice(3),P=JSON.parse(fs.readFileSync(path.join(dir,'partitura.json'),'utf8')),SR=48000,D=P.duracion;
const C=path.join(__dirname,P.instrumentos,'codigo/rejilla/research/rejilla/');
const Cuerda=require('./motor/cuerda.js'),Pajaro=require(C+'objetos/motor/pajaro.js');
const quiero=n=>!solo.length||solo.includes(n);
const guardar=(n,y)=>{fs.writeFileSync(path.join(dir,n+'.f32'),Buffer.from(Float32Array.from(y).buffer));let p=0,s=0;for(const v of y){p=Math.max(p,Math.abs(v));s+=v*v;}console.log(n.padEnd(12),(y.length/SR).toFixed(1)+' s','pico',p.toFixed(3),'rms',Math.sqrt(s/y.length).toFixed(4));};
for(const [k,ns] of Object.entries(P.arpas))if(ns.length&&quiero('arpa-'+k)){const t=Date.now();guardar('arpa-'+k,Cuerda.render({dur:D,tipo:'arpa',notas:ns,semilla:P.semilla+k.length},SR));console.log('   ',((Date.now()-t)/1000).toFixed(0),'s');}
if(quiero('cuatro'))guardar('cuatro',Cuerda.render({dur:D,tipo:'cuatro',notas:P.cuatro,semilla:P.semilla+9},SR));
if(quiero('aves'))for(const voz of [0,1])guardar('aves'+voz,Pajaro.render({dur:D,eventos:P.aves.filter(e=>(e.voz||0)===voz),semilla:P.semilla+voz},SR));
