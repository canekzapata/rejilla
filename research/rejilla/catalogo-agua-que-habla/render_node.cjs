/* Catálogo de agua que habla — capas de modelado físico (objetos que cantan, desde la copia fijada de la biblioteca) y Siringua
   (research/rejilla/aves-que-aprenden). Mono, 48 kHz, a <carpeta>/<capa>.f32.
     node render_node.cjs <carpeta> */
const fs=require('fs'),path=require('path');
const dir=process.argv[2],P=JSON.parse(fs.readFileSync(path.join(dir,'partitura.json'),'utf8')),SR=48000;
const OBJ=path.join(__dirname,P.instrumentos,'codigo/rejilla/research/rejilla/objetos/motor/');
const Pajaro=require(OBJ+'pajaro.js'),Agua=require(OBJ+'agua.js'),Tambor=require(OBJ+'tambor.js'),Waterphone=require(OBJ+'waterphone.js');
const VozAgua=require('../objetos/motor/vozagua.js'),Siringua=require('../aves-que-aprenden/siringua-mensajes.js'),Lector=require('../../../difonos/runtime/lector.js');
const guardar=(n,y)=>{fs.writeFileSync(path.join(dir,n+'.f32'),Buffer.from(Float32Array.from(y).buffer));let p=0;for(const v of y)p=Math.max(p,Math.abs(v));console.log(n.padEnd(22),(y.length/SR).toFixed(1)+' s','pico',p.toFixed(3));};
(async()=>{const D=P.duracion;
 guardar('aves-siringe',Pajaro.render({dur:D,eventos:P.aves_objeto,semilla:P.semilla},SR));
 guardar('agua',Agua.render({dur:D,eventos:P.agua,semilla:P.semilla+1},SR));
 guardar('waterphone',Waterphone.render({dur:D,eventos:P.waterphone,semilla:P.semilla+2},SR));
 guardar('tambor-que-habla',Tambor.render({dur:D,eventos:P.tambor_habla,semilla:P.semilla+3},SR));
 // Siringua: la frase entera (agua y ave por separado) y cada palabra sola, para cortarlas en la mezcla
 const lector=(x,o)=>Lector.readAsync(x,{...o,engine:'rules'});
 const c=await Siringua.preparar({id:'catalogo',text:P.frase},{language:'es-MX',semilla:P.semilla,lector});
 const s=Siringua.render(c,SR);guardar('siringua-agua',s.water);guardar('siringua-ave',s.bird);
 const palabras=[];
 for(const [i,w] of c.waterEvents.entries()){const e={...w,t:.02};const y=VozAgua.render({dur:w.dur+.25,eventos:[e],semilla:c.seed},SR)   /* la voz de agua de Siringua (vozagua.js) */;guardar('siringua-palabra-'+i,y);palabras.push({i,texto:w.texto,dur:w.dur,t:w.t});}
 fs.writeFileSync(path.join(dir,'siringua.json'),JSON.stringify({version:Siringua.version,palabras,duracion:c.duration,aves:c.birdEvents.length},null,1));})();
