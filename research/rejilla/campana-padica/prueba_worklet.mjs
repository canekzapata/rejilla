// Test the actual bundled processor, recording transport and WAV recipe.
import vm from 'node:vm';
import fs from 'node:fs';
import path from 'node:path';
import {WORKLET_SOURCE} from './paquete.mjs';
import {render} from './motor.mjs';
import {exportTake} from './archivo.mjs';
const out=process.argv[2];if(!out)throw Error('Se requiere una carpeta de entrega');
const messages=[];let Processor;
const sandbox={sampleRate:48000,AudioWorkletProcessor:class{constructor(){this.port={postMessage:m=>messages.push(m)};}},registerProcessor:(name,cls)=>{Processor=cls;}};
vm.runInNewContext(WORKLET_SOURCE,sandbox);
const p=new Processor();p.command({type:'record-start'});p.command({type:'hit',zone:9,velocity:.7});
for(let block=0;block<160;block++){
 if(block===75)p.command({type:'params',params:{fold:1}});
 p.process([],[[new Float32Array(128),new Float32Array(128)]]);
}
p.command({type:'record-stop'});const take=messages.find(m=>m.type==='recorded');
if(!take||take.left.length!==20480||take.events.length!==2)throw Error('Grabación incompleta');
const direct=render({events:[{t:0,hit:9,vel:.7},{t:.2,params:{fold:1}}]},20480/48000,48000);
let error=0;for(let i=0;i<take.left.length;i++)error=Math.max(error,Math.abs(take.left[i]-direct.left[i]),Math.abs(take.right[i]-direct.right[i]));
if(error!==0)throw Error('El procesador difiere del motor: '+error);
const img='data:image/png;base64,'+fs.readFileSync(new URL('./og.png',import.meta.url)).toString('base64');
const file=await exportTake(take,img);fs.writeFileSync(path.join(out,file.name),Buffer.from(file.buffer),{flag:'wx'});
const result={processorVsOfflineMaxError:error,frames:take.left.length,sr:take.sr,events:take.events,snapshots:messages.filter(m=>m.type==='state').length,
 exportedWav:file.name,recipe:file.recipe};
const dest=path.join(out,'verificacion-worklet-s20261021-9b5d27254a47.json');fs.writeFileSync(dest,JSON.stringify(result,null,2),{flag:'wx'});
console.log(JSON.stringify({error,frames:take.left.length,sr:take.sr,events:take.events.length,file:file.name}));
