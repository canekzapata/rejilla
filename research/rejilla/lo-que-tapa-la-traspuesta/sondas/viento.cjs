const fs=require('fs'),V=require('../motor/viento.js');
const h=new Float32Array(fs.readFileSync(__dirname+'/../terreno/h-420048.f32').buffer.slice(0)),Gn=360;
const fila=j=>{const p=new Float32Array(Gn);let mx=0;for(let i=0;i<Gn;i++){p[i]=h[j*Gn+i];mx=Math.max(mx,p[i]);}for(let i=0;i<Gn;i++)p[i]/=mx||1;return p;};
const perfiles=[];for(let k=0;k<6;k++)perfiles.push([k*2,fila(60+k*45)]);
console.log(perfiles.map(p=>V.leer(p[1]).crestas.length+'c/'+V.leer(p[1]).collados.length+'k').join(' '));
const y=V.render({dur:12,perfiles,vel:[[0,4],[6,16],[12,10]],estria:[[0,0],[5.9,0],[6.1,1],[12,1]],escala:[0,3,5,8],periodo:11,base:40,semilla:5},48000);
const out=new Float32Array(y.L.length*2);for(let i=0;i<y.L.length;i++){out[2*i]=y.L[i];out[2*i+1]=y.R[i];}
fs.writeFileSync(__dirname+'/viento.f32',Buffer.from(out.buffer));console.log('ok');
