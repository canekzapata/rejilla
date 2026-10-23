/* «nadie canta la canción» (yoshi es un vector, parte 7) — el audio. Toca lo que decidió ecosistema.js: cada Pokémon con su
   instrumento y cantando sus sílabas con su propia voz (vocoder de consola, copia parchada: portador y formantes por Pokémon).
   El ambiente (Rhodes y cuerdas) crece con κ: en el azar casi no hay suelo común; en la simbiosis, sí. La batería es la de consola
   (music.drums) tocada por Electrode, que explota en el compás 22. Se corre dentro del visor de lectura: window.cancion() → WAV. */
'use strict';
window.cancion=async function(opts={}){
const E=Ecosistema.componer(opts.seed||'eof'),SR=44100,LEN=E.LEN,SPB=E.SPB;
const hz=n=>440*2**((n-69)/12);
function hash(s){let h=1779033703^s.length;for(let i=0;i<s.length;i++){h=Math.imul(h^s.charCodeAt(i),3432918353);h=h<<13|h>>>19;}h=Math.imul(h^h>>>16,2246822507);h=Math.imul(h^h>>>13,3266489909);return (h^h>>>16)>>>0;}
function rng(tag){let a=hash(E.seed+':'+tag);return ()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}

/* ---------- las voces: el vocoder de consola, parchado en una copia ---------- */
if(!window.CantaMusica){let src=await (await fetch('/consola/consola/static/lectura/musica.js')).text();
 const patch=(a,b)=>{if(!src.includes(a))throw Error('no encontré en musica.js: '+a);src=src.split(a).join(b);};
 patch('window.LecturaMusica=','window.CantaMusica=');
 patch('midi:midi(m,m.vozOctave,deg)+bend};','midi:(v.canto??(midi(m,m.vozOctave,deg)+bend))};');
 patch('f.frequency.setTargetAtTime(F[k],t0,.012)','f.frequency.setTargetAtTime(F[k]*(window.CANTA_FORMANT||1),t0,.012)');
 patch('nodes.push(o);oscs.push(o);});','nodes.push(o);oscs.push(o);if(window.CANTA_VIB&&ev.dur>.3){const l=ctx.createOscillator(),lg=ctx.createGain();l.frequency.value=5.4;lg.gain.setValueAtTime(0,at);lg.gain.setValueAtTime(0,at+.2);lg.gain.linearRampToValueAtTime(window.CANTA_VIB,at+.55);l.connect(lg);lg.connect(o.detune);l.start(at);l.stop(at+ev.dur+.6);}});');
 const s=document.createElement('script');s.textContent=src;document.head.append(s);}
const CM=window.CantaMusica,LM=window.LecturaMusica,p0=Lectura.snapshot().piece;
const base={on:false,root:'C',scale:'major',gain:.8,reverb:.05,delay:0,delayTime:.3,pulse:'none',density:0,vozOctave:3,vozRate:1,vozCarrier:'sierra',vozMelody:'monotono',vozGain:1,instruments:[]};
function stretch(syl,n){const s=syl.toLowerCase(),idx=Math.max(...[...'aeiou'].map(c=>s.lastIndexOf(c)));if(idx<0)return s.includes('y')?s.replace('y','i'.repeat(n)):s;return s.slice(0,idx+1)+s[idx].repeat(n-1)+s.slice(idx+1);}
async function sing(syl,note,D,carrier,formant,vib=20){
 const piece={...p0,seed:E.seed,music:CM.normalize({...base,vozCarrier:carrier,voices:[{instrument:'none',octave:4,gain:.7,pan:0,entry:'none',words:false,gesture:false}]})};
 let v,ev;for(let n=1;n<=48;n++){v={i:0,key:'s',born:0,duration:D/.95,text:stretch(syl,n),effect:'fade',hold:0,speak:'vocoder',canto:note};ev=CM.speechEvents(piece,v)[0];if(ev.dur>=D*.97)break;}
 window.CANTA_FORMANT=formant;window.CANTA_VIB=vib;const buf=await CM.render(piece,[v],ev.dur+.6,SR),vt=(ev.steps.find(s=>s.v)||{t:0}).t;
 let pk=0;for(let c=0;c<2;c++){const d=buf.getChannelData(c);for(let k=0;k<d.length;k++)pk=Math.max(pk,Math.abs(d[k]));}return {buf,vt,norm:pk>0?1/pk:1};}

/* ---------- la mezcla ---------- */
const ctx=new OfflineAudioContext(2,Math.ceil(LEN*SR),SR),H=rng('humano');
const master=ctx.createGain(),comp=ctx.createDynamicsCompressor();master.gain.value=.8;comp.threshold.value=-15;comp.ratio.value=2.5;comp.attack.value=.012;comp.release.value=.2;master.connect(comp);comp.connect(ctx.destination);
const instB=ctx.createGain(),vocB=ctx.createGain(),drumB=ctx.createGain();instB.gain.value=opts.inst??1;drumB.gain.value=opts.drums??1;vocB.gain.value=opts.voc??1.5;[instB,vocB,drumB].forEach(b=>b.connect(master));
const verb=ctx.createConvolver(),vr=rng('reverb'),ir=ctx.createBuffer(2,SR*2.8,SR);for(let c=0;c<2;c++){const d=ir.getChannelData(c);for(let k=0;k<d.length;k++)d[k]=(vr()*2-1)*Math.exp(-k/SR*2.2)*(k<SR*.01?k/(SR*.01):1);}verb.buffer=ir;
const verbG=ctx.createGain();verbG.gain.value=.5;verb.connect(verbG);verbG.connect(master);
/* la reverberación (el espacio común) crece con κ */
const sendI=ctx.createGain(),sendV=ctx.createGain();instB.connect(sendI);vocB.connect(sendV);sendI.connect(verb);sendV.connect(verb);
for(let b=0;b<31;b++){const k=E.KAPPA(b);sendI.gain.setValueAtTime(.06+.2*k,E.tb(b));sendV.gain.setValueAtTime(.08+.25*k,E.tb(b));}
const pan=(p,to)=>{const s=ctx.createStereoPanner();s.pan.value=Math.max(-1,Math.min(1,p));s.connect(to);return s;};
const env=(g,t,a,peak,dec,sus=0.0001,tail=.05,end)=>{g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(peak,t+a);g.gain.setTargetAtTime(Math.max(sus,.0001),t+a,dec);if(end!=null)g.gain.setTargetAtTime(0,end,tail);};
const nb=ctx.createBuffer(1,SR*2,SR),nr=rng('ruido');{const d=nb.getChannelData(0);for(let k=0;k<d.length;k++)d[k]=nr()*2-1;}
function noise(t,dur,rate=1){const s=ctx.createBufferSource();s.buffer=nb;s.loop=true;s.playbackRate.value=rate;s.start(t,H()*1.5);s.stop(t+dur);return s;}
function vibr(o,t,rate,cents,delay,dur){const l=ctx.createOscillator(),lg=ctx.createGain();l.frequency.value=rate;lg.gain.setValueAtTime(0,t);lg.gain.setValueAtTime(0,t+delay);lg.gain.linearRampToValueAtTime(cents,t+delay+.3);l.connect(lg);lg.connect(o.detune);l.start(t);l.stop(t+dur+.5);}
/* los instrumentos del equipo */
const INST={
 krar(t,n,dur,v,p){const out=pan(p,instB),lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.Q.value=3;lp.frequency.setValueAtTime(5000,t);lp.frequency.setTargetAtTime(800,t,.06);lp.connect(g);g.connect(out);[-7,7].forEach(dt=>{const o=ctx.createOscillator();o.type='triangle';o.frequency.value=hz(n);o.detune.value=dt;o.connect(lp);o.start(t);o.stop(t+dur+.5);});env(g,t,.002,.09*v,.25);},
 flauta(t,n,dur,v,p){const out=pan(p,instB),g=ctx.createGain(),o=ctx.createOscillator();o.frequency.setValueAtTime(hz(n-2),t);o.frequency.exponentialRampToValueAtTime(hz(n),t+.08);vibr(o,t,5.6,22,.2,dur);o.connect(g);g.connect(out);env(g,t,.05,.075*v,.4,.06*v,.08,t+dur);o.start(t);o.stop(t+dur+.4);
  const b=noise(t,dur+.2),bp=ctx.createBiquadFilter(),bg=ctx.createGain();bp.type='bandpass';bp.frequency.value=hz(n);bp.Q.value=5;b.connect(bp);bp.connect(bg);bg.connect(out);env(bg,t,.03,.04*v,.15,.015*v,.08,t+dur);},
 cajita(t,n,dur,v,p){const out=pan(p,instB);[[1,1,1],[3.01,.25,.3],[5.9,.08,.1]].forEach(([r,a,d])=>{const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.value=hz(n)*r;env(g,t,.002,.08*v*a,d/3);o.connect(g);g.connect(out);o.start(t);o.stop(t+d*3);});},
 vibes(t,n,dur,v,p){const out=pan(p,instB),g=ctx.createGain(),trem=ctx.createGain(),l=ctx.createOscillator(),lg=ctx.createGain();trem.gain.value=.78;l.frequency.value=5;lg.gain.value=.22;l.connect(lg);lg.connect(trem.gain);l.start(t);l.stop(t+1.8);
  [[1,1,1.4],[4,.2,.3]].forEach(([r,a,d])=>{const o=ctx.createOscillator(),og=ctx.createGain();o.frequency.value=hz(n)*r;env(og,t,.002,a,d/2.5);o.connect(og);og.connect(g);o.start(t);o.stop(t+d*2.5);});g.gain.value=.07*v;g.connect(trem);trem.connect(out);},
 campana(t,n,dur,v,p){const out=pan(p,instB);[[1,1,1.6],[2.76,.3,.5],[5.4,.1,.2]].forEach(([r,a,d])=>{const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.value=hz(n)*r;env(g,t,.002,.06*v*a,d/3);o.connect(g);g.connect(out);o.start(t);o.stop(t+d*3);});},
 bajo(t,n,dur,v,p){const o=ctx.createOscillator(),s=ctx.createOscillator(),lp=ctx.createBiquadFilter(),g=ctx.createGain();o.type='triangle';o.frequency.value=hz(n);s.frequency.value=hz(n);lp.type='lowpass';lp.frequency.value=700;o.connect(lp);lp.connect(g);s.connect(g);env(g,t,.01,.3*v,.35,.2*v,.05,t+dur);g.connect(pan(p,instB));[o,s].forEach(x=>{x.start(t);x.stop(t+dur+.3);});},
 ep(t,n,dur,v,p){const f=hz(n),c=ctx.createOscillator(),mo=ctx.createOscillator(),mg=ctx.createGain(),g=ctx.createGain();c.frequency.value=f;mo.frequency.value=f;mg.gain.setValueAtTime(f*1.4*v,t);mg.gain.setTargetAtTime(f*.12,t,.2);mo.connect(mg);mg.connect(c.frequency);env(g,t,.006,.1*v,.6,.04*v,.1,t+dur);c.connect(g);g.connect(pan(p,instB));[c,mo].forEach(o=>{o.start(t);o.stop(t+dur+.8);});},
 pad(t,n,dur,v,p){const lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.frequency.value=1800;lp.connect(g);g.connect(pan(p,instB));[-9,0,9].forEach(dt=>{const o=ctx.createOscillator();o.type='sawtooth';o.frequency.value=hz(n);o.detune.value=dt;o.connect(lp);o.start(t);o.stop(t+dur+1);});env(g,t,.4,.018*v,1.6,.016*v,.3,t+dur);}};
/* explosión (autodestrucción) y pokébola */
function explota(t){const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.setValueAtTime(90,t);o.frequency.exponentialRampToValueAtTime(28,t+.6);env(g,t,.003,.38,.35);o.connect(g);g.connect(drumB);o.start(t);o.stop(t+1.6);
 const n=noise(t,1.6,.6),lp=ctx.createBiquadFilter(),ng=ctx.createGain();lp.type='lowpass';lp.frequency.setValueAtTime(6000,t);lp.frequency.exponentialRampToValueAtTime(300,t+1.2);env(ng,t,.002,.28,.4);n.connect(lp);lp.connect(ng);ng.connect(drumB);}
function pokebola(t){[[88,0],[95,.09]].forEach(([m,d])=>{const o=ctx.createOscillator(),g=ctx.createGain();o.type='square';o.frequency.value=hz(m);env(g,t+d,.002,.05,.1);o.connect(g);g.connect(pan(.3,instB));o.start(t+d);o.stop(t+d+.4);});const n=noise(t+.2,.15,1.4),bp=ctx.createBiquadFilter(),g=ctx.createGain();bp.type='bandpass';bp.frequency.value=2500;env(g,t+.2,.002,.3,.03);n.connect(bp);bp.connect(g);g.connect(drumB);}
const P=Object.fromEntries(E.EQUIPO.map((q,i)=>[q.id,{...q,pan:Math.sin(i/E.EQUIPO.length*6.283)*.7}]));

/* ---------- el suelo común: crece con κ ---------- */
const PC={C:0,'C#':1,Db:1,D:2,'D#':3,Eb:3,E:4,F:5,'F#':6,Gb:6,G:7,'G#':8,Ab:8,A:9,'A#':10,Bb:10,B:11},QUAL={maj7:[4,7,11,14],maj9:[4,11,14,19],6:[4,7,9,14],m7:[3,7,10,14],m9:[3,10,14,17],7:[4,9,10,14],'7b9':[4,7,10,13],'7sus':[5,7,10,14],dim7:[3,6,9,12],'':[4,7,12,14]};
function acorde(sym){const m=/^([A-G][b#]?)(.*?)(?:\/([A-G][b#]?))?$/.exec(sym),root=PC[m[1]];let ns=QUAL[m[2]].map(i=>48+root+i);while(ns[0]<53)ns=ns.map(n=>n+12);while(ns[0]>=64)ns=ns.map(n=>n-12);return ns;}
for(let b=0;b<31;b++){const k=E.KAPPA(b),cs=E.CH[b].map(acorde);if(k>.05)cs.forEach((ns,j)=>{const t=E.tb(b,j*2),d=E.SPB*(cs.length>1?2:4);ns.forEach((n,q)=>INST.pad(t,n+12,d*.97,k*1.1,(q-1.5)*.3));if(k>.3)[0,1.5].forEach(o=>ns.forEach((n,q)=>INST.ep(t+o*E.SPB+q*.01,n,E.SPB*.9,.4+.4*k,(q-1.5)*.35)));});}

/* ---------- lo que tocó cada Pokémon ---------- */
for(const e of E.eventos){const q=P[e.poke],v=(e.vel??1)*(.9+H()*.2);
 if(e.tipo==='explosion'){explota(e.t);continue;}if(e.tipo==='pokebola'){pokebola(e.t);continue;}
 const inst=e.tipo==='metronomo'?e.inst:q.inst;if(inst==='bateria'||inst==='metronomo')continue;INST[inst](e.t,e.midi,e.dur,v*(e.tipo==='melodia'||e.tipo==='huevo'?.8:1),q.pan);}
/* la batería de Electrode (consola) */
for(const d of E.bateria){const qq={...p0,clips:[],tempo:{...p0.tempo,bpm:E.BPM,meter:4},music:LM.normalize({...p0.music,on:true,gain:.7,reverb:.1,delay:0,pulse:'none',voices:[],drums:LM.drums(d.drums)})};
 const buf=await LM.render(qq,[],E.BAR,SR),s=ctx.createBufferSource(),g=ctx.createGain();s.buffer=buf;s.connect(g);g.connect(pan(P.electrode.pan,drumB));const at=E.tb(d.bar);g.gain.setValueAtTime(1,at);g.gain.setValueAtTime(1,at+E.BAR-.03);g.gain.linearRampToValueAtTime(0,at+E.BAR);s.start(at);}

/* ---------- las voces: cada sílaba con la voz de quien la cantó ---------- */
let sung=0;for(const e of E.eventos){if(!e.syl)continue;const q=P[e.poke],[carrier,formant]=q.voz,note=e.tipo==='metronomo'?e.midi-12:e.midi;
 const r=await sing(e.syl,note,Math.max(.12,e.dur-.03),carrier,formant);const s=ctx.createBufferSource(),g=ctx.createGain();s.buffer=r.buf;g.gain.value=.5*r.norm*(e.tipo==='metronomo'?.55:e.tipo==='huevo'?.9:1);s.connect(g);g.connect(pan(q.pan*.8,vocB));s.start(Math.max(0,e.t-r.vt));sung++;}

const out=await ctx.startRendering(),L=out.getChannelData(0),Rr=out.getChannelData(1);
/* saturación suave: los picos sueltos (golpes que coinciden) ya no bajan todo lo demás al normalizar */
let pk0=0,sq=0;for(let k=0;k<L.length;k++){pk0=Math.max(pk0,Math.abs(L[k]),Math.abs(Rr[k]));sq+=L[k]*L[k];}const rms0=Math.sqrt(sq/L.length),pre=.3/Math.max(1e-6,rms0);
let pk=0;for(let k=0;k<L.length;k++){L[k]=Math.tanh(L[k]*pre);Rr[k]=Math.tanh(Rr[k]*pre);pk=Math.max(pk,Math.abs(L[k]),Math.abs(Rr[k]));}const g=.92/pk;
const rms=[];for(let s=0;s<Math.floor(LEN);s+=4){let a=0;const i0=s*SR,i1=Math.min(L.length,(s+4)*SR);for(let k=i0;k<i1;k++)a+=L[k]*L[k];rms.push(+(Math.sqrt(a/(i1-i0))*g).toFixed(3));}
const pcm=new Int16Array(L.length*2);for(let k=0;k<L.length;k++){pcm[k*2]=Math.max(-1,Math.min(1,L[k]*g))*32767;pcm[k*2+1]=Math.max(-1,Math.min(1,Rr[k]*g))*32767;}
const u8=new Uint8Array(pcm.buffer);let b64='';for(let k=0;k<u8.length;k+=32768)b64+=String.fromCharCode(...u8.subarray(k,k+32768));
return {b64:btoa(b64),peak:pk,rms,sung,seconds:LEN,medidas:E.medidas};};
