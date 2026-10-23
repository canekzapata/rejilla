import assert from 'node:assert/strict';
import vm from 'node:vm';
import {createHash} from 'node:crypto';
import {AUDIO_SOURCE} from './dist/audio/paquete.mjs';
import {Campana} from './dist/audio/motor.mjs';
import {familySignals} from './dist/audio/captacion.mjs';
import {spatialParameters,roomImpulse} from './dist/audio/espacio.mjs';
import {poses} from './dist/forma.mjs';
const sources=Array.from({length:8},(_,k)=>{const v=[0,0,0];for(let i=k;i<64;i+=8)poses(i,.65).position.toArray().forEach((x,j)=>v[j]+=x/8);return v;});
const outside=spatialParameters([0,0,12],sources),inside=spatialParameters(sources[1].map((x,i)=>x+(i===2?1.45:0)),sources);
assert.equal(outside.enclosure,0);assert.equal(inside.enclosure,1);assert.ok(inside.wet>outside.wet*10);assert.ok(inside.delays[1]<outside.delays[1]);assert.ok(inside.gains[1]>outside.gains[1]);
for(const p of [inside,outside]){assert.ok([...p.gains,...p.delays].every(Number.isFinite));assert.ok(Math.abs(p.gains.reduce((s,v)=>s+v*v,0)/8-(1.25*p.overall)**2)<1e-12);}
const ir=roomImpulse(48000),again=roomImpulse(48000);assert.deepEqual(ir,again);assert.notDeepEqual(ir[0],ir[1]);
for(const ear of ir){assert.ok(Math.abs(ear.reduce((s,v)=>s+v*v,0)-.64)<1e-6);assert.ok(ear.every(Number.isFinite));}
let C;vm.runInNewContext(AUDIO_SOURCE,{sampleRate:48000,AudioWorkletProcessor:class{constructor(){this.port={postMessage:()=>{}};}},registerProcessor:(name,cl)=>C=cl});
const p=new C(),e=new Campana(48000),family=new Float64Array(8);p.port.onmessage({data:{type:'hit',region:9,velocity:.55}});e.strike(9,.55);
let maxDifference=0,monoDifference=0;
for(let b=0;b<20;b++){
 const outputs=[[new Float32Array(128),new Float32Array(128)],...Array.from({length:8},()=>[new Float32Array(128)])];p.process([],outputs);
 for(let j=0;j<128;j++){
  const y=e.sample();familySignals(e.q,e.left,e.right,family);maxDifference=Math.max(maxDifference,Math.abs(outputs[0][0][j]-Math.fround(y[0])),Math.abs(outputs[0][1][j]-Math.fround(y[1])));
  for(let k=0;k<8;k++)assert.equal(outputs[k+1][0][j],Math.fround(family[k]));
  monoDifference=Math.max(monoDifference,Math.abs(family.reduce((s,v)=>s+v,0)-(y[0]+y[1])/2));
 }
}
assert.equal(maxDifference,0);assert.ok(monoDifference<1e-12);
console.log(JSON.stringify({version:'1.2.0',result:'PASS',worklet_original_max_difference:maxDifference,aperture_sum_max_difference:monoDifference,apertures:8,original_outputs:2,ir_sha256:createHash('sha256').update(Buffer.from(ir[0].buffer)).update(Buffer.from(ir[1].buffer)).digest('hex'),ir_seconds:ir[0].length/48000,inside:{wet:inside.wet,nearness:inside.enclosure},outside:{wet:outside.wet,nearness:outside.enclosure},core_state:'Spatial listener never changes q, v or score position'},null,2));
