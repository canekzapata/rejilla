// Loop 1: fuentes reales del experimento. No modifica los instrumentos originales.
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=__dirname, original=path.join(root,'../objetos'), sr=24000, seed=18026;
const names=['motor/pajaro.js','motor/vozagua.js','motor/agua.js','vendor/difonos-g2p/g2p.js'];
const sources=Object.fromEntries(names.map(p=>[p,fs.readFileSync(path.join(original,p))]));
const P=require(path.join(original,'motor/pajaro.js')),V=require(path.join(original,'motor/vozagua.js'));
// Variante aislada: conserva el oscilador del pájaro, toma la fuente antes del filtro del pico.
const vm=require('vm'),sandbox={module:{exports:{}}};
const needle='s += out * (k ? .8 : 1);';
if(!sources['motor/pajaro.js'].toString().includes(needle))throw Error('Cambió la fuente: revisar adaptación');
const rawProgram=sources['motor/pajaro.js'].toString().replace(needle,'s += src * (k ? .8 : 1);');
vm.runInNewContext(rawProgram,sandbox); const Raw=sandbox.module.exports;
const words=[['todavía',.95,57],['estoy',.7,60],['aquí',.9,59]];
let t=.2;const waterEvents=words.map(([texto,dur,nota])=>{let e={t,dur,texto,nota,modo:'canto',voz:1,v:.7};t+=dur+.12;return e;});
const dur=3.6;
const water=V.render({dur,eventos:waterEvents,semilla:seed},sr);
// Cada lado recorre su propia frecuencia, sin forzar una relación de armónicos.
const gestures=waterEvents.flatMap((e,i)=>[
 {t:e.t,dur:e.dur,m:84+[0,4,2][i],m2:91+[2,-2,0][i],tipo:'silbido',voz:0,v:.65},
 {t:e.t+.08,dur:e.dur-.1,m:91+[1,-3,2][i],m2:84+[0,1,-2][i],tipo:'silbido',voz:1,v:.48}
]);
const bird=P.render({dur,eventos:gestures,semilla:seed},sr);
// Registro experimental bajo: no se presenta como imitación biológica de una especie.
const lowEvents=waterEvents.flatMap((e,i)=>[
 {t:e.t,dur:e.dur,m:57+[0,3,2][i],tipo:'ronco',voz:0,v:.8},
 {t:e.t,dur:e.dur,m:62+[0,-2,1][i],tipo:'ronco',voz:1,v:.65}
]);
const carrier=Raw.render({dur,eventos:lowEvents,semilla:seed},sr);
const nonce=crypto.randomBytes(24).toString('hex');
const hash=crypto.createHash('sha256').update(Buffer.from(water.buffer)).update(fs.readFileSync(__filename)).update(rawProgram).update(nonce).digest('hex');
const id=hash.slice(0,12),tag=`s${seed}-${id}`,out=path.join(root,`el-pajaro-aprende-${tag}`);
fs.mkdirSync(out);fs.mkdirSync(path.join(out,'proceso'));fs.mkdirSync(path.join(out,'fuentes'));
function write(p,b){fs.writeFileSync(path.join(out,p),b,{flag:'wx'});}
function wav(name,y){
 for(const x of y)if(!Number.isFinite(x))throw Error('Audio no finito');
 const peak=Math.max(...Array.from(y).filter((_,i)=>i%100===0).map(Math.abs));
 // WAV float conserva amplitud original para el análisis posterior.
 let b=Buffer.alloc(44+y.length*4);b.write('RIFF');b.writeUInt32LE(b.length-8,4);b.write('WAVEfmt ',8);b.writeUInt32LE(16,16);b.writeUInt16LE(3,20);b.writeUInt16LE(1,22);b.writeUInt32LE(sr,24);b.writeUInt32LE(sr*4,28);b.writeUInt16LE(4,32);b.writeUInt16LE(32,34);b.write('data',36);b.writeUInt32LE(y.length*4,40);for(let i=0;i<y.length;i++)b.writeFloatLE(y[i],44+i*4);write(`${name}-${tag}.wav`,b);
}
for(const [p,b]of Object.entries(sources)){let target=path.join('fuentes',p);fs.mkdirSync(path.dirname(path.join(out,target)),{recursive:true});write(target,b);}
write('fuentes/pajaro-sin-filtro.js',rawProgram);
write('fuentes/fuentes.cjs',fs.readFileSync(__filename));
wav('01-agua-dice',water);wav('02-pajaro-doble',bird);wav('03-siringe-grave-cruda',carrier);
const receta={version:'aves-agua-0.1',id,hash,nonce,semilla:seed,sr,dur,texto:'todavía estoy aquí',waterEvents,gestures,lowEvents,
 identificador:'SHA-256 del audio de agua, programa, adaptación de siringe y nonce nuevo; sonido como medio primario',
 fuentes:Object.fromEntries(Object.entries(sources).map(([p,b])=>[p,crypto.createHash('sha256').update(b).digest('hex')]))};
write(`receta-${tag}.json`,JSON.stringify(receta,null,2));
console.log(out);
