import fs from 'node:fs';
import path from 'node:path';
import {render,VERSION,SEED} from './motor.mjs';
const [input,output]=process.argv.slice(2);
if(!input||!output)throw Error('Uso: node renderizar.mjs partitura.json prefijo-nuevo');
const score=JSON.parse(fs.readFileSync(input,'utf8'));
for(const ext of ['.raw','.json'])if(fs.existsSync(output+ext))throw Error('Destino existente: '+output+ext);
const result=render(score,score.duration??10,score.sr??24000),interleaved=new Float32Array(result.left.length*2);
for(let i=0;i<result.left.length;i++){interleaved[2*i]=result.left[i];interleaved[2*i+1]=result.right[i];}
fs.writeFileSync(output+'.raw',Buffer.from(interleaved.buffer),{flag:'wx'});
fs.writeFileSync(output+'.json',JSON.stringify({version:VERSION,seed:SEED,metrics:result.metrics,snapshots:result.snapshots}),{flag:'wx'});
console.log(JSON.stringify(result.metrics));
