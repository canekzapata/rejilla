// Concatenated after the byte-frozen engine and deterministic score definitions.
class SculptureProcessor extends AudioWorkletProcessor{
 constructor(){
  super();this.e=new Campana(sampleRate);this.queue=[];this.squares=new Float64Array(64);this.count=0;this.hits=0;this.song=null;this.songFrame=0;this.playing=false;this.ended=false;this.fade=null;this.apertureSamples=new Float64Array(8);
  this.port.onmessage=({data:m})=>{
   if(m.type==='params'){if(m.cancel)this.cancelScore();this.e.set(m.params);}
   if(m.type==='hit')this.strike(m.region,m.velocity??.72);
   if(m.type==='clear'){this.cancelScore();this.e.clear();this.squares.fill(0);this.count=0;this.fade=null;}
   if(m.type==='play'){const s=songById(m.id);if(s){this.playing=false;this.fade={left:Math.round(sampleRate*.025),total:Math.round(sampleRate*.025),next:s};}}
   if(m.type==='pause'&&this.song&&!this.ended)this.playing=false;
   if(m.type==='resume'&&this.song&&!this.ended)this.playing=true;
   if(m.type==='stop'){this.cancelScore();this.fade={left:Math.round(sampleRate*.025),total:Math.round(sampleRate*.025),next:null};}
  };
 }
 cancelScore(){this.song=null;this.playing=false;this.ended=false;this.queue=[];this.fade=null;}
 strike(region,velocity){this.e.strike(region,velocity);this.hits++;this.port.postMessage({type:'strike',region,frame:this.e.frame,velocity});}
 start(s){
  this.e.clear();this.squares.fill(0);this.count=0;this.e.set(s.initial,true);this.song=s;this.songFrame=0;this.playing=true;this.ended=false;
  this.queue=s.events.map(ev=>({...ev,frame:Math.round(ev.t*sampleRate)}));
 }
 process(input,outputs){
  const out=outputs[0];if(!out?.[0])return true;
  for(let j=0;j<out[0].length;j++){
   if(this.playing&&this.song){
    while(this.queue.length&&this.queue[0].frame<=this.songFrame){const ev=this.queue.shift();if(ev.params)this.e.set(ev.params);if(ev.hit!==undefined)this.strike(ev.hit,ev.vel??.5);}
    this.songFrame++;if(this.songFrame>=Math.round(this.song.duration*sampleRate)){this.playing=false;this.ended=true;}
   }
   const y=this.e.sample();let level=1;
   if(this.fade){level=this.fade.left/this.fade.total;this.fade.left--;if(this.fade.left<=0){const next=this.fade.next;this.fade=null;if(next)this.start(next);else{this.e.clear();this.squares.fill(0);this.count=0;}level=0;}}
   out[0][j]=y[0]*level;if(out[1])out[1][j]=y[1]*level;
   if(outputs.length>1){familySignals(this.e.q,this.e.left,this.e.right,this.apertureSamples);for(let k=0;k<8;k++)if(outputs[k+1]?.[0])outputs[k+1][0][j]=this.apertureSamples[k]*level;}
   for(let k=0;k<64;k++)this.squares[k]+=this.e.q[k]**2;this.count++;
  }
  if(this.count>=1024){
   const rms=Array.from(this.squares,v=>Math.sqrt(v/this.count));
   this.port.postMessage({type:'state',rms,params:{...this.e.p},energy:this.e.energy(),frame:this.e.frame,hits:this.hits,peak:this.e.maxPeak,limitedFrames:this.e.clipped,transport:this.song?{id:this.song.id,elapsed:this.songFrame/sampleRate,duration:this.song.duration,playing:this.playing,ended:this.ended}:null});this.squares.fill(0);this.count=0;
  }
  return true;
 }
}
registerProcessor('otra-distancia',SculptureProcessor);
