const fs=require('fs'),G=require('../motor/garganta.js');
const h=new Float32Array(fs.readFileSync(__dirname+'/../terreno/h-420048.f32').buffer.slice(0)),Gn=360;
const fila=j=>{const p=new Float32Array(Gn);let mx=0;for(let i=0;i<Gn;i++){p[i]=h[j*Gn+i];mx=Math.max(mx,p[i]);}for(let i=0;i<Gn;i++)p[i]/=mx||1;return p;};
const largo=+(process.argv[2]||1),ev=[];let t=.1;
for(const v of ['a','e','i','o','u']){ev.push({t,dur:1.9,nota:50,fonemas:[v],v:.6,aprende:1});t+=2;}
ev.push({t,dur:1.9,nota:50,fonemas:['a'],v:.6,aprende:0});t+=2;
const y=G.render({dur:t+.2,perfil:fila(180),largo,eventos:ev,fuente:'ruido'},48000);
fs.writeFileSync(__dirname+'/tubo-'+largo+'.f32',Buffer.from(y.buffer));
