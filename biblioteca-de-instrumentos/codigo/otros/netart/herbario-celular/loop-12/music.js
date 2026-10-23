(function(root){'use strict';
 const echo=typeof HerbEcho!=='undefined'?HerbEcho:require('./echo.js');
 const BPM=84,BEAT=60/BPM,BAR=BEAT*4;
 function score(seed,snapshot,bar){const r=HerbWorld.random(seed+'/music/'+bar),base=43+HerbWorld.hash(seed+'/tonic')%7,activity=snapshot.activity,boundary=snapshot.boundary;
  const chords=[[0,3,7,10],[0,5,7,12],[-2,2,5,9],[0,3,7,14]],c=chords[(Math.floor(bar/4)+Math.floor(boundary*8))%4],events=[];
  function note(instrument,n,beat,length,velocity){events.push({instrument,note:n,time:beat*BEAT,duration:length*BEAT,velocity});}
  note('bass',base+c[0],0,.85,.7);note('bass',base+c[2]-12,2,.7,.54);if(activity>.09)note('bass',base+(bar%2?2:5),3.45,.35,.42);
  for(let j=0;j<8;j++)if(j%2===0||r()<.3+activity){note('drums',42,j*.5+(j%2?.075:0),.1,j%2?.2:.3);}
  note('drums',36,0,.2,.6);if(activity>.035)note('drums',36,2.5,.15,.33);note('drums',38,1,.15,.27);note('drums',38,3,.14,.33);if(bar%4===3&&activity>.1)note('drums',38,3.65,.1,.2);
  if(bar%2===0||snapshot.stable<.6){for(const n of c.slice(1))note('keys',base+12+n,.6,1.6,.31);}
  if(bar%2===1&&activity>.06){for(const n of [c[0],c[2],c[3]])note('keys',base+12+n,2.65,.7,.23);}
  // Phrase recurrence changes on four-bar observations, with two bars of rest.
  const contact=snapshot.contacts.some(z=>z.strength>.09);
  if(bar%4===1||(bar%4===2&&contact)){const motif=[7,10,5,3],offset=HerbWorld.hash(seed+'/horn')%4;
   note('trombone',base+12+motif[(Math.floor(bar/4)+offset)%4],bar%4===1?.3:1.1,1.25,.39);
   if(activity>.1)note('trombone',base+12+c[1],2.2,.72,.32);
  }
  const weather=snapshot.climate||{intensity:.1,previousIntensity:.1,slow:0},heat=bar%4===0?weather.previousIntensity*.65+weather.intensity*.35:weather.intensity;
  if(heat>.4){
   for(const e of events){if(e.instrument==='keys'){e.time+=BEAT*(bar%2?.15:.25);e.note+=(bar%3===0?1:0);}if(e.instrument==='trombone'){e.note+=bar%2?5:-2;e.duration*=.75;}}
   for(let j=0;j<3;j++)note('drums',j===1?38:42,1.4+j*.23,.08,.18);
  }
  if(heat>.78){
   // Short departures retain the bass motif and end with a pocket of silence.
   for(let j=0;j<4;j++)note('trombone',base+12+[1,13,6,-1][(j+bar)%4],.35+j*.41,.2,.25);
   if(bar%2===0)for(const n of [0,1,6,10])note('keys',base+24+n,2.15,.38,.18);
   if(bar%4===3)for(let j=events.length-1;j>=0;j--)if(events[j].time>BEAT*2.65)events.splice(j,1);
  }else if(weather.slow>.14&&bar%8===7){note('keys',base+25,2.8,.75,.14);}
  for(const e of events)e.tension=heat;
  return echo.arrange(events.sort((a,b)=>a.time-b.time),snapshot.musicalMemory,bar,BEAT);
 }
 const noiseCache=new WeakMap();
 function noise(ctx){if(noiseCache.has(ctx))return noiseCache.get(ctx);const b=ctx.createBuffer(1,ctx.sampleRate,ctx.sampleRate),d=b.getChannelData(0),r=HerbWorld.random('herbario-drum-noise');for(let i=0;i<d.length;i++)d[i]=r()*2-1;noiseCache.set(ctx,b);return b;}
 function voice(ctx,bus,e,start,live){if(live&&live.size>=64)return;const t=start+e.time,d=Math.max(.05,e.duration),amp=ctx.createGain(),filter=ctx.createBiquadFilter(),nodes=[amp,filter],sources=[];filter.connect(amp);amp.connect(bus);let end=t+d+.3;
  const hz=440*Math.pow(2,(e.note-69)/12),vel=e.velocity;
  function osc(type,f,gain=1){const o=ctx.createOscillator(),g=ctx.createGain();o.type=type;o.frequency.setValueAtTime(f,t);g.gain.value=gain;o.connect(g);g.connect(filter);nodes.push(o,g);sources.push(o);return o;}
  function envelope(a,peak,sustain,release){amp.gain.setValueAtTime(0,t);amp.gain.linearRampToValueAtTime(peak,t+a);amp.gain.exponentialRampToValueAtTime(Math.max(.0001,sustain),t+Math.max(a+.01,d));amp.gain.exponentialRampToValueAtTime(.0001,t+d+release);end=t+d+release+.03;}
  if(e.instrument==='bass'){filter.type='lowpass';filter.frequency.value=700;filter.Q.value=.7;osc('triangle',hz,.7);osc('sine',hz,.6);envelope(.014,vel*.25,.014,.12);}
  else if(e.instrument==='keys'){filter.type='lowpass';filter.frequency.value=900+2600*(e.shade??1);osc('sine',hz,.7);osc('sine',hz*2,.2);osc('sine',hz*3,.07);envelope(.007,vel*.18,.012,.65);}
  else if(e.instrument==='trombone'){filter.type='lowpass';filter.Q.value=.9;filter.frequency.setValueAtTime(600,t);filter.frequency.linearRampToValueAtTime((1900+(e.tension||0)*650)*(e.shade??1),t+Math.min(.1,d*.3));filter.frequency.linearRampToValueAtTime(900,t+d);
   const o=osc('sawtooth',hz,.7);osc('triangle',hz,.35);const vibrato=ctx.createOscillator(),vg=ctx.createGain();vibrato.frequency.value=5.2;vg.gain.setValueAtTime(0,t);vg.gain.linearRampToValueAtTime(5,t+.3);vibrato.connect(vg);vg.connect(o.detune);nodes.push(vibrato,vg);sources.push(vibrato);envelope(.08,vel*.13,vel*.08,.15);
  }else if(e.note===36){filter.type='lowpass';filter.frequency.value=450;const o=osc('sine',115);o.frequency.exponentialRampToValueAtTime(45,t+.15);envelope(.005,vel*.32,.002,.08);}
  else{filter.type=e.note===42?'highpass':'bandpass';filter.frequency.value=e.note===42?7300:1600;filter.Q.value=.6;const n=ctx.createBufferSource();n.buffer=noise(ctx);n.connect(filter);nodes.push(n);sources.push(n);if(e.note===38)osc('triangle',180,.15);envelope(.004,vel*(e.note===42?.16:.24),.0005,.07);}
  let remaining=sources.length;const rec={sources,nodes};if(live)live.add(rec);
  for(const s of sources){s.onended=()=>{remaining--;if(!remaining){for(const n of nodes)try{n.disconnect();}catch{}if(live)live.delete(rec);}};s.start(t);s.stop(end);}
 }
 function output(ctx,volume){const master=ctx.createGain(),compressor=ctx.createDynamicsCompressor();master.gain.value=volume;compressor.threshold.value=-16;compressor.knee.value=12;compressor.ratio.value=5;compressor.attack.value=.006;compressor.release.value=.18;master.connect(compressor);compressor.connect(ctx.destination);return {master,compressor};}
 class Player{
  constructor(){this.ctx=null;this.live=new Set();this.volume=.45;this.timer=null;this.running=false;this.runId=0;}
  async start(seed,getSnapshot,position=0){this.stop();const runId=this.runId;if(!this.ctx){this.ctx=new (root.AudioContext||root.webkitAudioContext)();Object.assign(this,output(this.ctx,this.volume));}await this.ctx.resume();if(runId!==this.runId)return;getSnapshot(Math.floor(position/BAR));this.running=true;this.origin=this.ctx.currentTime+.09-position;this.bar=Math.floor(position/BAR);this.seed=seed;this.getSnapshot=getSnapshot;const startPosition=position;
   const tick=()=>{if(!this.running)return;while(this.origin+this.bar*BAR<this.ctx.currentTime+.18){const b=this.bar++,start=this.origin+b*BAR,snapshot=this.getSnapshot(b);for(const e of score(this.seed,snapshot,b))if(b*BAR+e.time>=startPosition-.001&&start+e.time>=this.ctx.currentTime+.008)voice(this.ctx,this.master,e,start,this.live);}};tick();this.timer=setInterval(tick,40);}
  position(){return this.running?Math.max(0,this.ctx.currentTime-this.origin):null;}
  stop(){this.runId++;this.running=false;if(this.timer)clearInterval(this.timer);this.timer=null;for(const rec of this.live){for(const s of rec.sources)try{s.stop();}catch{}for(const n of rec.nodes)try{n.disconnect();}catch{}}this.live.clear();}
  setVolume(v){this.volume=Math.max(0,Math.min(1,v));if(this.master)this.master.gain.setTargetAtTime(this.volume,this.ctx.currentTime,.035);}
 }
 function vlq(n){const b=[n&127];while((n>>>=7))b.unshift((n&127)|128);return b;}
 function midi(seed,snapshots,bars=16){const bytes=[],u32=n=>[(n>>>24)&255,(n>>>16)&255,(n>>>8)&255,n&255],ascii=s=>[...s].map(c=>c.charCodeAt(0));
  function chunk(name,data){bytes.push(...ascii(name),...u32(data.length),...data);}
  chunk('MThd',[0,1,0,5,1,224]);const tempo=Math.round(60000000/BPM);chunk('MTrk',[0,255,81,3,(tempo>>16)&255,(tempo>>8)&255,tempo&255,0,255,88,4,4,2,24,8,0,255,47,0]);
  for(const [name,ch,program] of [['bass',0,33],['keys',1,4],['trombone',2,57],['drums',9,null]]){const es=[];
   for(let b=0;b<bars;b++){const snap=snapshots[Math.min(snapshots.length-1,Math.floor(b/4))];for(const e of score(seed,snap,b).filter(e=>e.instrument===name)){const start=Math.round((b*BAR+e.time)/BEAT*480),end=start+Math.round(e.duration/BEAT*480);es.push({t:start,data:[0x90+ch,e.note,Math.round(e.velocity*110)],off:false},{t:end,data:[0x80+ch,e.note,0],off:true});}}
   es.sort((a,b)=>a.t-b.t||Number(b.off)-Number(a.off));const data=[0,255,3,name.length,...ascii(name)];if(program!==null)data.push(0,0xc0+ch,program);let last=0;for(const e of es){data.push(...vlq(e.t-last),...e.data);last=e.t;}data.push(0,255,47,0);chunk('MTrk',data);
  }return new Uint8Array(bytes);
 }
 async function renderPreview(seed,snapshots,bars=8,startBar=0){const ctx=new OfflineAudioContext(2,Math.ceil((bars*BAR+2)*22050),22050),{master}=output(ctx,.7);for(let b=0;b<bars;b++)for(const e of score(seed,snapshots[Math.min(snapshots.length-1,Math.floor((startBar+b)/4))],startBar+b))voice(ctx,master,e,b*BAR+.1);return await ctx.startRendering();}
 root.HerbMusic={BPM,BEAT,BAR,score,Player,midi,renderPreview};if(typeof module!=='undefined')module.exports=root.HerbMusic;
})(typeof window==='undefined'?globalThis:window);
