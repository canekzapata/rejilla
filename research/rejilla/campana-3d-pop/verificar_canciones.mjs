import assert from 'node:assert/strict';
import vm from 'node:vm';
import {writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {AUDIO_SOURCE} from './dist/audio/paquete.mjs';
import {SONGS} from './dist/canciones.mjs';
import {spectralRows} from './dist/espectros.mjs';
const sr=48000,block=128;
function processor(){let C;vm.runInNewContext(AUDIO_SOURCE,{sampleRate:sr,AudioWorkletProcessor:class{constructor(){this.messages=[];this.port={postMessage:m=>this.messages.push(m)};}},registerProcessor:(name,cl)=>C=cl});return new C();}
function run(p,blocks=1){const output=[new Float32Array(block),new Float32Array(block)];for(let b=0;b<blocks;b++)p.process([],[output]);return output;}
const timing=processor();timing.port.onmessage({data:{type:'play',id:SONGS[0].id}});run(timing,200);const position=timing.songFrame,frame=timing.e.frame;
timing.port.onmessage({data:{type:'pause'}});run(timing,40);assert.equal(timing.songFrame,position);assert.equal(timing.e.frame,frame+40*block);
timing.port.onmessage({data:{type:'resume'}});run(timing,4);assert.equal(timing.songFrame,position+4*block);
const q=Array.from(timing.e.q),v=Array.from(timing.e.v);timing.port.onmessage({data:{type:'params',params:{pickup:6},cancel:false}});assert.equal(timing.playing,true);assert.deepEqual(Array.from(timing.e.q),q);assert.deepEqual(Array.from(timing.e.v),v);
timing.port.onmessage({data:{type:'params',params:{fold:.6},cancel:true}});assert.equal(timing.song,null);assert.deepEqual(Array.from(timing.e.q),q);assert.deepEqual(Array.from(timing.e.v),v);
timing.port.onmessage({data:{type:'stop'}});run(timing,16);assert.ok(Array.from(timing.e.q).every(v=>v===0));assert.equal(timing.fade,null);
const silent=new Float32Array(2048).fill(-Infinity);assert.ok(spectralRows(silent,sr,4096).every(v=>v===0));
silent[Math.round(440/sr*4096)]=-24;const rows=spectralRows(silent,sr,4096);let y=rows.indexOf(Math.max(...rows));const frequency=6000*(45/6000)**((y+.5)/96);assert.ok(Math.abs(frequency-440)<60);
const destination=process.argv[2];if(destination)mkdirSync(destination,{recursive:false});
const reports=[];
for(const s of SONGS){
 const p=processor();p.port.onmessage({data:{type:'play',id:s.id}});let sum=0,peak=0,count=0;const hash=createHash('sha256');
 const blocks=Math.ceil((s.duration+.08)*sr/block),pcm=destination?Buffer.alloc(blocks*block*4):null;
 for(let b=0;b<blocks;b++){
  const out=run(p);for(let i=0;i<block;i++){for(let ch=0;ch<2;ch++){const value=out[ch][i]*.9;assert.ok(Number.isFinite(value));sum+=value*value;peak=Math.max(peak,Math.abs(value));count++;if(pcm)pcm.writeInt16LE(Math.max(-32768,Math.min(32767,Math.round(value*32767))),(b*block+i)*4+ch*2);}}hash.update(Buffer.from(out[0].buffer));hash.update(Buffer.from(out[1].buffer));
 }
 const hits=p.messages.filter(m=>m.type==='strike'),expected=s.events.filter(e=>e.hit!==undefined),intro=Math.round(sr*.025);
 assert.equal(hits.length,expected.length);for(let i=0;i<hits.length;i++){assert.equal(hits[i].region,expected[i].hit);assert.equal(hits[i].frame,intro+Math.round(expected[i].t*sr));}
 assert.equal(p.ended,true);assert.equal(p.playing,false);assert.equal(p.songFrame,Math.round(s.duration*sr));assert.equal(p.e.clipped,0);assert.ok(peak>.02&&peak<.98);
 if(pcm){const h=Buffer.alloc(44);h.write('RIFF',0);h.writeUInt32LE(36+pcm.length,4);h.write('WAVEfmt ',8);h.writeUInt32LE(16,16);h.writeUInt16LE(1,20);h.writeUInt16LE(2,22);h.writeUInt32LE(sr,24);h.writeUInt32LE(sr*4,28);h.writeUInt16LE(4,32);h.writeUInt16LE(16,34);h.write('data',36);h.writeUInt32LE(pcm.length,40);writeFileSync(destination+'/'+s.id+'.wav',Buffer.concat([h,pcm]),{flag:'wx'});}
 const report={id:s.id,title:s.title,duration:s.duration,sampleRate:sr,hits:hits.length,peak,rms:Math.sqrt(sum/count),limitedFrames:p.e.clipped,pcm_float32_sha256:hash.digest('hex'),sample_accurate_events:true,finished:true};reports.push(report);console.log(JSON.stringify(report));
}
assert.equal(new Set(reports.map(r=>r.pcm_float32_sha256)).size,5);
const summary={version:'1.1.0',result:'PASS',pause_resume:'Position freezes while resonator continues',navigation:'Family change keeps score, q and v',manual_fold:'Cancels score without resetting state',stop:'25 ms fade then silence',spectrum:'Silence zero; 440 Hz mapped within 60 Hz',songs:reports};
if(destination)writeFileSync(destination+'/verificacion.json',JSON.stringify(summary,null,2),{flag:'wx'});console.log('PASS: five complete scores, transport and real-frequency mapping.');
