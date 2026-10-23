/* Los objetos que cantan (y los imposibles) suenan desde la biblioteca: cada ficha objeto-* e imposible-* con una nota (62, .8, 1.2 s) da audio finito y no mudo,
   y es determinista (dos veces, la misma señal).    node pruebas/objetos_suenan.cjs */
const O=require('../motores/objetos.js'),fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const dir=path.join(__dirname,'..','fichas');let n=0;
for(const f of fs.readdirSync(dir).filter(x=>x.startsWith('objeto-')||x.startsWith('imposible-'))){const K=JSON.parse(fs.readFileSync(path.join(dir,f)));const t=Date.now();
 const y=O.nota(K,{midi:62,vel:.8,dur:1.2}),z=O.nota(K,{midi:62,vel:.8,dur:1.2});let p=0,e=0,d=0;
 for(let i=0;i<y.length;i++){p=Math.max(p,Math.abs(y[i]));e+=y[i]*y[i];d=Math.max(d,Math.abs(y[i]-z[i]));}
 const rms=Math.sqrt(e/y.length);console.log(K.id.padEnd(30),(y.length/48000).toFixed(2)+'s','pico',p.toFixed(3),'rms',rms.toFixed(4),(Date.now()-t)+'ms');
 assert.ok(Number.isFinite(p)&&rms>1e-5,K.id+' suena');assert.equal(d,0,K.id+' es determinista');n++;}
console.log('OK: '+n+' objetos suenan desde la biblioteca');
