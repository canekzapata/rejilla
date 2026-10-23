export class OrganAudio{
 async init(values){if(this.pending){await this.pending;await this.ctx.resume();return;}this.pending=this.setup(values);try{await this.pending;}catch(e){await this.ctx?.close();this.ctx=null;this.pending=null;throw e;}}
 async setup(values){
  const ctx=this.ctx=new AudioContext();await ctx.audioWorklet.addModule('./worklet.mjs');
  this.node=new AudioWorkletNode(ctx,'braid-voice',{numberOfInputs:0,numberOfOutputs:3,outputChannelCount:[1,1,1]});
  this.mix=ctx.createGain();this.mix.gain.value=.72;
  const compressor=ctx.createDynamicsCompressor();compressor.threshold.value=-12;compressor.knee.value=8;compressor.ratio.value=5;compressor.attack.value=.006;compressor.release.value=.2;
  this.analyser=ctx.createAnalyser();this.analyser.fftSize=2048;this.analyser.smoothingTimeConstant=.72;
  this.mix.connect(compressor);compressor.connect(this.analyser);this.analyser.connect(ctx.destination);
  this.panners=[];this.stems=[];this.stemBins=[];for(let k=0;k<3;k++){let p=ctx.createPanner();p.panningModel='HRTF';p.distanceModel='inverse';p.refDistance=5;p.rolloffFactor=.32;this.node.connect(p,k);let a=ctx.createAnalyser();a.fftSize=2048;a.smoothingTimeConstant=.65;p.connect(a);a.connect(this.mix);this.stems.push(a);this.stemBins.push(new Uint8Array(a.frequencyBinCount));this.panners.push(p);}
  // Explicit artistic room: deterministic decaying reflections, not a geometry solver.
  const ir=ctx.createBuffer(2,Math.round(ctx.sampleRate*2.8),ctx.sampleRate);let s=20261021;
  for(let c=0;c<2;c++){const a=ir.getChannelData(c);for(let i=0;i<a.length;i++){s=(Math.imul(s,1664525)+1013904223)>>>0;a[i]=((s/4294967296)*2-1)*Math.exp(-i/(ctx.sampleRate*.63))*.09;}}
  const con=ctx.createConvolver();con.buffer=ir;this.wet=ctx.createGain();this.wet.gain.value=.24;this.mix.connect(con);con.connect(this.wet);this.wet.connect(compressor);
  this.bins=new Uint8Array(this.analyser.frequencyBinCount);this.node.port.postMessage({values});await ctx.resume();
 }
 set(values){this.node?.port.postMessage({values});}
 gate(on){this.node?.port.postMessage({gate:on?1:0});}
 note(midi){this.node?.port.postMessage({frequency:440*2**((midi-69)/12)});}
 spatial(camera,pearls,inside){if(!this.ctx)return;const t=this.ctx.currentTime,l=this.ctx.listener;
  const set=(p,v)=>p.setTargetAtTime(v,t,.045);
  ['X','Y','Z'].forEach((a,i)=>{set(l['position'+a],camera.position.getComponent(i));set(l['forward'+a],camera.forward.getComponent(i));set(l['up'+a],camera.up.getComponent(i));});
  this.panners.forEach((p,k)=>['X','Y','Z'].forEach((a,i)=>set(p['position'+a],pearls[k].getComponent(i))));set(this.wet.gain,inside?.36:.24);
 }
 spectrum(){if(!this.analyser)return null;this.analyser.getByteFrequencyData(this.bins);return this.bins;}
 spectra(){if(!this.stems)return null;this.stems.forEach((a,k)=>a.getByteFrequencyData(this.stemBins[k]));return this.stemBins;}
}
