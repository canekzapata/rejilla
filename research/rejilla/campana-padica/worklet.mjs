// Bundled after motor.mjs by empaquetar.py, so it also works without a server.
class CampanaProcessor extends AudioWorkletProcessor{
 constructor(){super();this.e=new Campana(sampleRate);this.events=[];this.recording=null;this.port.onmessage=({data:m})=>this.command(m);}
 log(m){if(this.recording)this.recording.events.push({frame:this.e.frame-this.recording.start,...m});}
 command(m){
  if(m.type==='params'){if(m.cancel)this.events=[];this.e.set(m.params);this.log({params:m.params});}
  if(m.type==='hit'){if(m.params)this.e.set(m.params);this.e.strike(m.zone,m.velocity??.7);this.log({hit:m.zone,vel:m.velocity??.7,params:m.params});}
  if(m.type==='clear'){this.events=[];this.e.clear();this.log({clear:true});}
  if(m.type==='demo'){
   this.e.clear();this.events=[];const p={fold:0,depth:.7,tension:7,damping:.2,midi:48,pickup:1};this.e.set(p,true);this.log({clear:true,params:p,immediate:true});
   const sequence=[{t:.12,hit:9,vel:.8},{t:1.4,params:{fold:1}},{t:3.7,params:{depth:1.8}},{t:5.8,params:{fold:0,depth:.7}}];
   this.events=sequence.map(ev=>({...ev,frame:this.e.frame+Math.round(ev.t*sampleRate)}));
  }
  if(m.type==='record-start'){
   if(this.recording)return;
   this.recording={left:new Float32Array(sampleRate*25),right:new Float32Array(sampleRate*25),n:0,start:this.e.frame,state:this.e.snapshot(),target:{...this.e.target},events:[]};
   this.port.postMessage({type:'recording',active:true});
  }
  if(m.type==='record-stop')this.finishRecording();
 }
 finishRecording(){
  const r=this.recording;if(!r)return;this.recording=null;
  const left=r.left.slice(0,r.n),right=r.right.slice(0,r.n);
  this.port.postMessage({type:'recorded',left,right,sr:sampleRate,initial:r.state,targets:r.target,events:r.events},[left.buffer,right.buffer]);
 }
 process(inputs,outputs){
  const out=outputs[0];if(!out?.length)return true;
  for(let i=0;i<out[0].length;i++){
   while(this.events.length&&this.events[0].frame<=this.e.frame){const ev=this.events.shift();if(ev.params)this.e.set(ev.params);if(ev.hit!==undefined)this.e.strike(ev.hit,ev.vel);this.log({params:ev.params,hit:ev.hit,vel:ev.vel});}
   const y=this.e.sample();out[0][i]=y[0];if(out[1])out[1][i]=y[1];
   if(this.recording){const r=this.recording;r.left[r.n]=y[0];r.right[r.n]=y[1];r.n++;if(r.n>=r.left.length)this.finishRecording();}
  }
  if(this.e.frame%1024<out[0].length)this.port.postMessage({type:'state',q:Array.from(this.e.q),params:{...this.e.p},energy:this.e.energy(),peak:this.e.maxPeak,frame:this.e.frame});
  return true;
 }
}
registerProcessor('campana-padica',CampanaProcessor);
