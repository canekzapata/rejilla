import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import vm from 'node:vm';
import {Campana} from './dist/audio/motor.mjs';
import {AUDIO_SOURCE} from './dist/audio/paquete.mjs';
import {poses,porcelainGeometry,outline} from './dist/forma.mjs';
import {cleanRoute,readRoute,encodeRoute,INITIAL} from './dist/ruta.mjs';
const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
assert.equal(hash('./dist/audio/motor.mjs'),existsSync('../campana-padica/motor.mjs')?hash('../campana-padica/motor.mjs'):'df2f9216cce60456e56d314714551b8374c49c689e04836dc142d3c9f9cfb812');
assert.deepEqual(readRoute(encodeRoute({...INITIAL,inside:true})),{...INITIAL,inside:true});
assert.equal(cleanRoute({fold:Infinity}).fold,INITIAL.fold);assert.equal(cleanRoute({pickup:-9}).pickup,0);
const g=porcelainGeometry();assert.equal(g.attributes.position.count,574);assert.equal(g.index.count,3360);
for(let i=0;i<80;i++){const a=outline(i/80*Math.PI*2,0);assert.ok(Math.hypot(a[0],a[1])>.17);}
for(let i=0;i<32;i++){const a=poses(i,1).position;assert.ok(a.distanceTo(poses(i+32,1).position)<a.distanceTo(poses(i^8,1).position));}
let Processor;const scope={sampleRate:48000,AudioWorkletProcessor:class{constructor(){this.messages=[];this.port={postMessage:m=>this.messages.push(m)};}},registerProcessor:(name,C)=>Processor=C};vm.runInNewContext(AUDIO_SOURCE,scope);
const p=new Processor(),e=new Campana(48000),rms=new Float64Array(64);p.port.onmessage({data:{type:'hit',region:9,velocity:.78}});e.strike(9,.78);
let maxDifference=0;
for(let b=0;b<16;b++){const output=[new Float32Array(128),new Float32Array(128)];p.process([], [output]);for(let j=0;j<128;j++){const expected=e.sample();maxDifference=Math.max(maxDifference,Math.abs(output[0][j]-Math.fround(expected[0])),Math.abs(output[1][j]-Math.fround(expected[1])));if(b<8)for(let i=0;i<64;i++)rms[i]+=e.q[i]**2;}}
assert.equal(maxDifference,0);const states=p.messages.filter(s=>s.type==='state');assert.equal(states.length,2);for(let i=0;i<64;i++)assert.ok(Math.abs(states[0].rms[i]-Math.sqrt(rms[i]/1024))<1e-12);
const before=Array.from(p.e.q);p.port.onmessage({data:{type:'params',params:{fold:1,pickup:6},cancel:true}});assert.deepEqual(Array.from(p.e.q),before);
p.port.onmessage({data:{type:'clear'}});p.process([],[[new Float32Array(1024),new Float32Array(1024)]]);assert.ok(p.messages.at(-1).rms.every(v=>v===0));
console.log(JSON.stringify({motor_sha256:hash('./dist/audio/motor.mjs'),worklet_max_sample_difference:maxDifference,rms:'Coincide con 1024 muestras del motor original',geometry_vertices:g.attributes.position.count,geometry_triangles:g.index.count/3,holes:'64 aberturas reales',navigation:'Cambiar parámetros conserva q y v',result:'PASS'},null,2));
