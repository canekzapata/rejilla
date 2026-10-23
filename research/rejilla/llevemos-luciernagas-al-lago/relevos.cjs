/* Nuevas frases escritas para los mismos instrumentos de la biblioteca. */
const fs=require('fs'),path=require('path'),zlib=require('zlib');
const out=path.join(__dirname,fs.readFileSync(path.join(__dirname,'REVISION-ESCUCHA-ACTUAL.txt'),'utf8').trim());
const p=JSON.parse(fs.readFileSync(path.join(out,'partitura-v9.json'),'utf8'));
const bib=path.join(__dirname,'luciernagas-reescritura-s1-29d4afe5aad2/realizacion/biblioteca');
const O=require(path.join(bib,'motores/objetos.js')),SR=48000,y=new Float32Array(Math.round(153.33333333333334*SR)*2);
const fichas={clarinete:'objeto-clarinete',chelo:'objeto-chelo',piano:'objeto-piano-papel'};
for(const e of p.relevos_escucha){
 const K=JSON.parse(fs.readFileSync(path.join(bib,'fichas',fichas[e.parte]+'.json'),'utf8'));
 const a=O.nota(K,{midi:e.midi,vel:e.vel,dur:e.dur},SR),off=Math.round(.05*SR),at=Math.round(e.t*SR),pan=(e.pan+1)*Math.PI/4;
 for(let i=off;i<a.length&&at+i-off<y.length/2;i++){
  const t=e.t+(i-off)/SR;if(t>e.salidas[0][1])break;
  const end=Math.min(1,Math.max(0,(e.salidas[0][1]-t)/.025)),j=2*(at+i-off);
  y[j]+=a[i]*Math.cos(pan)*end;y[j+1]+=a[i]*Math.sin(pan)*end;
 }
}
fs.writeFileSync(path.join(out,'render/relevos.f32.gz'),zlib.gzipSync(Buffer.from(y.buffer),{level:3}),{flag:'wx'});
console.log(p.relevos_escucha.length,'notas realizadas con los motores originales');
