import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
import {Voice,metrics} from './motor.mjs';
const path=process.argv[2];if(!path)throw Error('Indica el HTML portátil');
const html=fs.readFileSync(path,'utf8'),engine=JSON.parse(html.match(/const ENGINE_SOURCE=(.*);\n/)[1]),processor=html.match(/const processor=`([\s\S]*?)`;/)[1];
let Processor,messages=[];
vm.runInNewContext(engine.replace(/\bexport /g,'')+'\n'+processor,{sampleRate:48000,AudioWorkletProcessor:class{constructor(){this.port={postMessage:m=>messages.push(m)};}},registerProcessor:(name,c)=>Processor=c});
let p=new Processor(),v=new Voice(48000),error=0,peak=0;
const events=new Map([[0,{kick:{force:.7,fine:.3}}],[30,{params:{nu:.22,midi:52}}],[90,{kick:{x:3,y:2,force:.5,fine:1}}],[150,{params:{nonlinear:0,midi:45}}]]);
for(let b=0;b<240;b++){if(events.has(b)){let e=events.get(b);p.port.onmessage({data:e});v.event(e);}let out=[[new Float32Array(128),new Float32Array(128)]];p.process([],out);for(let n=0;n<128;n++){let a=v.sample();for(let c=0;c<2;c++){error=Math.max(error,Math.abs(out[0][c][n]-Math.fround(a[c])));peak=Math.max(peak,Math.abs(out[0][c][n]));}}}
assert(error===0);assert(messages.some(m=>m.state));assert(peak>.01);let r={worklet_vs_offline_float32_max_error:error,peak,frames:v.frame,state_messages:messages.filter(m=>m.state).length,final_metrics:metrics(v.fluid.u)};console.log(JSON.stringify(r,null,2));
