/* «la ley canta» (yoshi es un vector, parte 5) — la canción que se compone sola. No hay partitura: todo sale de compositor.js
   (un autómata celular de 31 células, una generación por corchea). Aquí solo se TOCA lo que el autómata decidió:
   - la voz (vocoder de consola, copia parchada) canta sus notas y sus sílabas;
   - Rhodes y cuerdas tocan su acorde del compás; el Rhodes ataca cuando nacen células en el registro medio;
   - el bajo toca la fundamental donde el autómata puso bombo; el vibráfono suena cuando nacen células arriba;
   - la batería es la de consola (music.drums) con los patrones que escribió el autómata, compás por compás.
   Al final, cuando la ley se apaga, una voz grave repite despacio la última palabra que eligió. Se corre dentro del visor de lectura. */
'use strict';
window.cancion=async function(opts={}){
const C=Compositor.componer(opts.seed||'la-ley-canta');
const BPM=120,SPB=60/BPM,E8=SPB/2,T0=.35,SR=44100,LEN=T0+C.G*E8+6;
const tg=g=>T0+g*E8,hz=n=>440*2**((n-69)/12);
function hash(s){let h=1779033703^s.length;for(let i=0;i<s.length;i++){h=Math.imul(h^s.charCodeAt(i),3432918353);h=h<<13|h>>>19;}h=Math.imul(h^h>>>16,2246822507);h=Math.imul(h^h>>>13,3266489909);return (h^h>>>16)>>>0;}
function rng(tag){let a=hash(C.seed+':'+tag);return ()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}

/* ---------- la voz: el vocoder de consola, parchado en una copia ---------- */
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
async function sing(syl,note,D,{carrier='sierra',formant=1.2,vib=22}={}){
 const piece={...p0,seed:C.seed,music:CM.normalize({...base,vozCarrier:carrier,voices:[{instrument:'none',octave:4,gain:.7,pan:0,entry:'none',words:false,gesture:false}]})};
 let v,ev;for(let n=1;n<=48;n++){v={i:0,key:'s',born:0,duration:D/.95,text:stretch(syl,n),effect:'fade',hold:0,speak:'vocoder',canto:note};ev=CM.speechEvents(piece,v)[0];if(ev.dur>=D*.97)break;}
 window.CANTA_FORMANT=formant;window.CANTA_VIB=vib;
 const buf=await CM.render(piece,[v],ev.dur+.6,SR),vt=(ev.steps.find(s=>s.v)||{t:0}).t;
 let pk=0;for(let c=0;c<2;c++){const d=buf.getChannelData(c);for(let k=0;k<d.length;k++)pk=Math.max(pk,Math.abs(d[k]));}
 return {buf,vt,norm:pk>0?1/pk:1};}

/* ---------- la mezcla ---------- */
const ctx=new OfflineAudioContext(2,Math.ceil(LEN*SR),SR),H=rng('humano');
const master=ctx.createGain(),comp=ctx.createDynamicsCompressor();master.gain.value=.8;comp.threshold.value=-15;comp.ratio.value=2.5;comp.attack.value=.012;comp.release.value=.18;master.connect(comp);comp.connect(ctx.destination);
const instB=ctx.createGain(),vocB=ctx.createGain(),drumB=ctx.createGain();instB.gain.value=opts.inst??1;drumB.gain.value=opts.drums??1;vocB.gain.value=opts.voc??1.6;[instB,vocB,drumB].forEach(b=>b.connect(master));
const verb=ctx.createConvolver(),vr=rng('reverb'),ir=ctx.createBuffer(2,SR*2.6,SR);for(let c=0;c<2;c++){const d=ir.getChannelData(c);for(let k=0;k<d.length;k++)d[k]=(vr()*2-1)*Math.exp(-k/SR*2.4)*(k<SR*.01?k/(SR*.01):1);}verb.buffer=ir;
const verbG=ctx.createGain();verbG.gain.value=.5;verb.connect(verbG);verbG.connect(master);
const send=(from,g)=>{const s=ctx.createGain();s.gain.value=g;from.connect(s);s.connect(verb);};send(instB,.2);send(vocB,.28);
const dl=ctx.createDelay(2),dfb=ctx.createGain(),dlp=ctx.createBiquadFilter(),dsend=ctx.createGain();dl.delayTime.value=SPB*.75;dfb.gain.value=.3;dlp.type='lowpass';dlp.frequency.value=3000;dsend.gain.value=.18;vocB.connect(dsend);dsend.connect(dl);dl.connect(dlp);dlp.connect(dfb);dfb.connect(dl);dlp.connect(master);
const pan=(p,to)=>{const s=ctx.createStereoPanner();s.pan.value=Math.max(-1,Math.min(1,p));s.connect(to);return s;};
const env=(g,t,a,peak,dec,sus=0.0001,tail=.05,end)=>{g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(peak,t+a);g.gain.setTargetAtTime(Math.max(sus,.0001),t+a,dec);if(end!=null)g.gain.setTargetAtTime(0,end,tail);};
function ep(t,n,dur,vel,p=0){const f=hz(n),c=ctx.createOscillator(),mo=ctx.createOscillator(),mg=ctx.createGain(),g=ctx.createGain(),ti=ctx.createOscillator(),tg2=ctx.createGain(),out=pan(p,instB);
 c.frequency.value=f;mo.frequency.value=f;mg.gain.setValueAtTime(f*1.6*vel,t);mg.gain.setTargetAtTime(f*.15,t,.18);mo.connect(mg);mg.connect(c.frequency);
 ti.frequency.value=f*14.2;tg2.gain.setValueAtTime(.028*vel,t);tg2.gain.setTargetAtTime(0,t,.012);ti.connect(tg2);tg2.connect(out);
 env(g,t,.005,.12*vel,.55,.05*vel,.08,t+dur);c.connect(g);g.connect(out);[c,mo,ti].forEach(o=>{o.start(t);o.stop(t+dur+.7);});}
function bass(t,n,dur,vel){const f=hz(n),o=ctx.createOscillator(),s=ctx.createOscillator(),lp=ctx.createBiquadFilter(),g=ctx.createGain(),sg=ctx.createGain();o.type='sawtooth';o.frequency.value=f;s.frequency.value=f;
 lp.type='lowpass';lp.Q.value=3;lp.frequency.setValueAtTime(280+1300*vel,t);lp.frequency.setTargetAtTime(240,t,.08);o.connect(lp);lp.connect(g);s.connect(sg);sg.gain.value=.9;sg.connect(g);
 env(g,t,.006,.28*vel,.25,.16*vel,.04,t+dur);g.connect(instB);[o,s].forEach(x=>{x.start(t);x.stop(t+dur+.3);});}
function vibes(t,n,vel,p=0,dur=1.4){const out=pan(p,instB),g=ctx.createGain(),trem=ctx.createGain(),l=ctx.createOscillator(),lg=ctx.createGain();trem.gain.value=.78;l.frequency.value=5.3;lg.gain.value=.22;l.connect(lg);lg.connect(trem.gain);l.start(t);l.stop(t+dur+.2);
 [[1,1,dur],[4,.2,.3],[10,.04,.08]].forEach(([r,a,d])=>{const o=ctx.createOscillator(),og=ctx.createGain();o.frequency.value=hz(n)*r;env(og,t,.002,a,d/2.5);o.connect(og);og.connect(g);o.start(t);o.stop(t+d*2.5);});g.gain.value=.06*vel;g.connect(trem);trem.connect(out);}
function pad(t,n,dur,vel,p=0){const out=pan(p,instB),lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.frequency.value=2000;lp.connect(g);g.connect(out);
 [-9,0,9].forEach(dt=>{const o=ctx.createOscillator();o.type='sawtooth';o.frequency.value=hz(n);o.detune.value=dt;o.connect(lp);o.start(t);o.stop(t+dur+1);});env(g,t,.35,.02*vel,1.6,.017*vel,.3,t+dur);}

/* ---------- lo que decidió el autómata ---------- */
const actoGain=[.7,.9,1,1];
const nac=(g,i,j)=>{let s=0;for(let q=i;q<=j;q++)s+=C.born[g][q];return s;};
for(const B of C.bars){const g0=B.b*C.GPB,A=actoGain[B.acto],bar=tg(g0),barLen=C.GPB*E8;
 /* cuerdas: el acorde entero, más fuerte mientras más viva está la fila */
 B.chord.forEach((n,k)=>pad(bar,n+12,barLen*.97,(.4+B.densidad*1.4)*A,(k-1.5)*.3));
 /* Rhodes: ataca en el primer tiempo y donde nacen células en el registro medio (6 a 11) */
 for(let e=0;e<C.GPB;e++){const g=g0+e,n=nac(g,6,11);if(e===0||n>=2){let d=1;while(e+d<C.GPB&&nac(g0+e+d,6,11)<2)d++;B.chord.forEach((m,k)=>ep(tg(g)+k*.01,m,d*E8*.95,(.45+.12*n)*A,(k-1.5)*.35));}}
 /* bajo: la fundamental donde el autómata puso bombo (y en el uno); octava si nacen las células de abajo */
 const ks=B.drums.kick||'';for(let e=0;e<C.GPB;e++){if(e===0||ks[2*e]==='x'){const oct=nac(g0+e,0,2)?12:0;bass(tg(g0+e),B.bass+oct,E8*1.8,.7*A);}}
 /* vibráfono: nacimientos arriba (26 a 30), a su altura */
 for(let e=0;e<C.GPB;e++){const g=g0+e;for(let i=26;i<=30;i++)if(C.born[g][i]&&(i+g)%3===0)vibes(tg(g),C.midiDe(i,g)-12,.8*A,(i-28)*.25);}}
/* batería de consola: los patrones del autómata, compás por compás */
for(const B of C.bars){const q={...p0,clips:[],tempo:{...p0.tempo,bpm:BPM,meter:4},music:LM.normalize({...p0.music,on:true,gain:.7,reverb:.1,delay:0,pulse:'none',voices:[],drums:LM.drums({gain:.6*actoGain[B.acto],...B.drums})})};
 const len=C.GPB*E8,last=B.b===C.BARS-1,buf=await LM.render(q,[],len+(last?3:0),SR),s=ctx.createBufferSource(),g=ctx.createGain();s.buffer=buf;s.connect(g);g.connect(drumB);
 const at=tg(B.b*C.GPB);g.gain.setValueAtTime(1,at);if(!last){g.gain.setValueAtTime(1,at+len-.03);g.gain.linearRampToValueAtTime(0,at+len);}s.start(at);}

/* ---------- la voz: lo que cantó el autómata ---------- */
const lines=C.notes.map(n=>{const a=Math.min(3,Math.floor(n.g/C.GPB/8));return {syl:n.syl,note:n.midi,t:tg(n.g),D:n.dur*E8-.03,carrier:['sierra','pulso','sierra','coro'][a],formant:[1.24,1.15,1.2,1.1][a],doble:a>=2};});
lines.filter(x=>x.doble).forEach(x=>lines.push({...x,note:x.note-12,carrier:'pulso',gain:.3,pan:.4,formant:1.05,doble:false}));
/* epílogo: la última palabra, despacio y grave, cuando ya no queda nadie */
const ultima=C.notes.at(-1),pal=Compositor.LEX.find(w=>w.join('')===ultima.word)||[ultima.syl];pal.forEach((s,k)=>lines.push({syl:s,note:ultima.midi-24,t:tg(C.G)+.6+k*SPB,D:SPB*.95,carrier:'coro',formant:.9,vib:0,gain:.75}));
let sung=0;for(const x of lines){const r=await sing(x.syl,x.note,x.D,{carrier:x.carrier,formant:x.formant,vib:x.vib??22});
 const s=ctx.createBufferSource(),g=ctx.createGain();s.buffer=r.buf;g.gain.value=.5*r.norm*(x.gain??1);s.connect(g);g.connect(pan(x.pan||0,vocB));s.start(Math.max(0,x.t-r.vt));sung++;}

const out=await ctx.startRendering(),L=out.getChannelData(0),Rr=out.getChannelData(1);let pk=0;for(let k=0;k<L.length;k++)pk=Math.max(pk,Math.abs(L[k]),Math.abs(Rr[k]));const g=.92/pk;
const rms=[];for(let s=0;s<Math.floor(LEN);s+=4){let a=0;const i0=s*SR,i1=Math.min(L.length,(s+4)*SR);for(let k=i0;k<i1;k++)a+=L[k]*L[k];rms.push(+(Math.sqrt(a/(i1-i0))*g).toFixed(3));}
const pcm=new Int16Array(L.length*2);for(let k=0;k<L.length;k++){pcm[k*2]=Math.max(-1,Math.min(1,L[k]*g))*32767;pcm[k*2+1]=Math.max(-1,Math.min(1,Rr[k]*g))*32767;}
const u8=new Uint8Array(pcm.buffer);let b64='';for(let k=0;k<u8.length;k+=32768)b64+=String.fromCharCode(...u8.subarray(k,k+32768));
return {b64:btoa(b64),peak:pk,rms,sung,seconds:LEN,medidas:C.medidas,reglas:C.actos.map(a=>a.rule)};};
