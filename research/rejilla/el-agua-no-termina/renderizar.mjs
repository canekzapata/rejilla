import {Voice,VERSION,metrics} from './motor.mjs';
import fs from 'node:fs';
const [scorePath,prefix]=process.argv.slice(2);if(!scorePath||!prefix)throw Error('partitura.json prefijo-nuevo');
for(const ext of ['.raw','.json'])if(fs.existsSync(prefix+ext))throw Error('Destino existente');
let score=JSON.parse(fs.readFileSync(scorePath)),sr=score.sr??24000,n=Math.round(score.duration*sr),v=new Voice(sr),events=[...(score.events??[])].sort((a,b)=>a.t-b.t),i=0;
v.params(score.initial??{});const audio=new Float32Array(n*2),history=[];
for(let f=0;f<n;f++){while(i<events.length&&Math.round(events[i].t*sr)<=f)v.event(events[i++]);let a=v.sample();audio[f*2]=a[0];audio[f*2+1]=a[1];if(f%Math.round(sr/12)===0)history.push({t:f/sr,...metrics(v.fluid.u),u:Array.from(v.fluid.u)});}
fs.writeFileSync(prefix+'.raw',Buffer.from(audio.buffer),{flag:'wx'});fs.writeFileSync(prefix+'.json',JSON.stringify({version:VERSION,sr,score,history,output_saturator_samples:v.clipped}),{flag:'wx'});
