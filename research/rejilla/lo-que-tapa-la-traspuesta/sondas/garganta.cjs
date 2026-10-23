// sonda: cinco vocales sostenidas (aprende 1) y la montaña sola (aprende 0), nota 50; escribe f32 para medir formantes
const fs=require('fs'),G=require('../motor/garganta.js');
const h=new Float32Array(fs.readFileSync(__dirname+'/../terreno/h-420048.f32').buffer.slice(0)),Gn=360;
const fila=j=>{const p=new Float32Array(Gn);let mx=0;for(let i=0;i<Gn;i++){p[i]=h[j*Gn+i];mx=Math.max(mx,p[i]);}for(let i=0;i<Gn;i++)p[i]/=mx||1;return p;};
const largo=+(process.argv[2]||1),ev=[];let t=.1;
for(const v of ['a','e','i','o','u']){ev.push({t,dur:.9,nota:50,fonemas:[v],v:.6,aprende:1});t+=1.1;}
ev.push({t,dur:1.4,nota:50,fonemas:['a'],v:.6,aprende:0});t+=1.6;
ev.push({t,dur:1.2,nota:50,nota2:57.3,fonemas:['a'],v:.6,aprende:.6});t+=1.4;
for(const [k,s] of ['ka','sa','ta','pa','ma','la','rra'].entries()){ev.push({t,dur:.32,nota:52,fonemas:s==='rra'?['rr','a']:s.split(''),v:.7,aprende:1});t+=.4;}
const y=G.render({dur:t+.3,perfil:fila(180),largo,eventos:ev},48000);
fs.writeFileSync(__dirname+'/garganta-'+largo+'.f32',Buffer.from(y.buffer));console.log('ok',(y.length/48000).toFixed(1),'s');
