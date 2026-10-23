const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
export const SPACE_VERSION='1.2.0',SPACE_SEED=20261021,METRES_PER_UNIT=.25;
export function spatialParameters(position,sources){
 const distances=sources.map(s=>Math.hypot(...s.map((v,i)=>v-position[i]))),raw=distances.map(d=>1/(1+(d/2.5)**2));
 const norm=Math.sqrt(raw.reduce((s,g)=>s+g*g,0)/sources.length)||1,nearest=Math.min(...distances);
 const t=clamp((5-nearest)/3.2,0,1),enclosure=t*t*(3-2*t),overall=clamp(1/(1+.045*Math.max(0,nearest-1.5)),.45,1);
 return {distances,gains:raw.map(g=>g/norm*overall*1.25),delays:distances.map(d=>Math.min(.1,d*METRES_PER_UNIT/343)),nearest,enclosure,wet:.025+.295*enclosure,cutoff:14500-6900*enclosure,overall};
}
export function roomImpulse(sampleRate,seed=SPACE_SEED){
 const length=Math.ceil(sampleRate*1.15),channels=[];
 for(let ch=0;ch<2;ch++){
  let state=(seed+ch*7919)>>>0,low=0;const data=new Float32Array(length);
  for(let i=0;i<length;i++){
   state^=state<<13;state^=state>>>17;state^=state<<5;
   const noise=(state>>>0)/4294967296*2-1;low=.62*low+.38*noise;
   const t=i/sampleRate;if(t>.018)data[i]=low*.045*Math.exp(-6.907755*(t-.018)/.82);
  }
  for(const [seconds,level] of [[.011,.4],[.019,.26],[.033,.18],[.052,.13],[.079,.09]])data[Math.round(sampleRate*(seconds+ch*.0017))]+=level;
  let energy=0;for(const x of data)energy+=x*x;const scale=.8/Math.sqrt(energy);for(let i=0;i<length;i++)data[i]*=scale;
  channels.push(data);
 }return channels;
}
export class SpatialListening{
 constructor(ctx){
  this.ctx=ctx;this.lastValues=new WeakMap();this.enabled=true;this.state=null;
  this.original=ctx.createGain();this.original.gain.value=0;
  this.sum=ctx.createGain();this.tone=ctx.createBiquadFilter();this.tone.type='lowpass';this.tone.frequency.value=14500;this.tone.Q.value=.5;
  this.direct=ctx.createGain();this.direct.gain.value=.96;this.wet=ctx.createGain();this.wet.gain.value=.025;this.spatial=ctx.createGain();this.spatial.gain.value=1;
  this.room=ctx.createConvolver();this.room.normalize=false;const channels=roomImpulse(ctx.sampleRate),impulse=ctx.createBuffer(2,channels[0].length,ctx.sampleRate);channels.forEach((data,ch)=>impulse.copyToChannel(data,ch));this.room.buffer=impulse;
  this.mix=ctx.createGain();this.output=ctx.createDynamicsCompressor();this.output.threshold.value=-6;this.output.knee.value=3;this.output.ratio.value=12;this.output.attack.value=.002;this.output.release.value=.12;
  this.original.connect(this.mix);this.sum.connect(this.tone);this.tone.connect(this.direct);this.direct.connect(this.spatial);this.tone.connect(this.room);this.room.connect(this.wet);this.wet.connect(this.spatial);this.spatial.connect(this.mix);this.mix.connect(this.output);
  this.apertures=Array.from({length:8},()=>{
   const input=ctx.createGain(),delay=ctx.createDelay(.1),panner=ctx.createPanner();
   panner.panningModel='HRTF';panner.distanceModel='inverse';panner.refDistance=1;panner.rolloffFactor=0;panner.coneInnerAngle=360;panner.coneOuterAngle=360;
   input.connect(delay);delay.connect(panner);panner.connect(this.sum);return {input,delay,panner};
  });
 }
 parameter(p,value,immediate=false){
  if(!Number.isFinite(value))throw Error('Non-finite spatial parameter');
  if(!immediate&&Math.abs((this.lastValues.get(p)??Infinity)-value)<1e-5)return;
  this.lastValues.set(p,value);const now=this.ctx.currentTime;p.cancelScheduledValues(now);
  if(immediate)p.setValueAtTime(value,now);else p.setTargetAtTime(value,now,.045);
 }
 vector(object,prefix,values,immediate){
  for(let i=0;i<3;i++)this.parameter(object[prefix+'XYZ'[i]],values[i],immediate);
 }
 connect(node){node.connect(this.original,0,0);this.apertures.forEach((a,k)=>node.connect(a.input,k+1,0));}
 setEnabled(enabled,immediate=false){this.enabled=enabled;this.parameter(this.original.gain,enabled?0:1,immediate);this.parameter(this.spatial.gain,enabled?1:0,immediate);}
 update(listener,sources,immediate=false){
  const p=spatialParameters(listener.position,sources),ears=this.ctx.listener;
  this.vector(ears,'position',listener.position.map(v=>v*METRES_PER_UNIT),immediate);this.vector(ears,'forward',listener.forward,immediate);this.vector(ears,'up',listener.up,immediate);
  this.apertures.forEach((a,k)=>{this.vector(a.panner,'position',sources[k].map(v=>v*METRES_PER_UNIT),immediate);this.parameter(a.input.gain,p.gains[k],immediate);this.parameter(a.delay.delayTime,p.delays[k],immediate);});
  this.parameter(this.wet.gain,p.wet,immediate);this.parameter(this.tone.frequency,Math.min(this.ctx.sampleRate*.45,p.cutoff),immediate);
  this.state={...p,enabled:this.enabled,listener,sourcePositions:sources,panningModel:'HRTF',version:SPACE_VERSION};return this.state;
 }
}
