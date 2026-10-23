import vm from 'node:vm';
import fs from 'node:fs';
import path from 'node:path';
import {WORKLET_SOURCE} from './paquete.mjs';
import {render} from './motor.mjs';
let Processor;const box={sampleRate:48000,AudioWorkletProcessor:class{constructor(){this.port={postMessage:()=>{}};}},registerProcessor:(_,c)=>{Processor=c;}};
vm.runInNewContext(WORKLET_SOURCE,box);const p=new Processor();p.command({type:'demo'});
const got=new Float32Array(48000*8);
for(let b=0;b<3000;b++){const out=[new Float32Array(128),new Float32Array(128)];p.process([],[out]);got.set(out[0],b*128);}
const expected=render({initial:{fold:0,depth:.7,tension:7,damping:.2,midi:48,pickup:1},events:[{t:.12,hit:9,vel:.8},{t:1.4,params:{fold:1}},{t:3.7,params:{depth:1.8}},{t:5.8,params:{fold:0,depth:.7}}]},8,48000);
let difference=0;for(let i=0;i<got.length;i++)difference=Math.max(difference,Math.abs(got[i]-expected.left[i]));
if(difference!==0)throw Error('La secuencia de la interfaz difiere del render: '+difference);
const result={maxError:difference,frames:got.length,sr:48000,sequence:'Un solo golpe a .12 s; plegar 1.4 s, profundidad 3.7 s, regresar 5.8 s.'};
fs.writeFileSync(path.join(process.argv[2],'verificacion-demo-s20261021-9b5d27254a47.json'),JSON.stringify(result,null,2),{flag:'wx'});console.log(JSON.stringify(result));
