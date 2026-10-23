/* «coro de gritos» (yoshi es un vector, parte 9) — ~72 s de future bass a 140 bpm (medio tiempo), Re mayor.
   Los personajes de Melee nunca dijeron una palabra, sólo gritaban, hasta que alguien los afinó. El coro son sus voces reales
   (muestras del juego, afinadas con TD-PSOLA en meleeviewer/tools/autotune_voces.py y renderizadas por voces.py en dos pistas:
   el coro sostenido y los chops). Aquí se les pone encima lo electrónico: acordes de supersierra que bombean, sub, arpegio, risers,
   la batería de consola (kit 808) y el vocoder de consola como narrador. El coro bombea con el bombo como los acordes.
   Se corre dentro del visor de lectura: window.cancion(opciones) → WAV. */
'use strict';
window.cancion=async function(opts={}){
const DIR='/meleeviewer/output/Arte/2026-09-29_yoshi_es_un_vector_9_coro_de_gritos/';
const P=await (await fetch(DIR+'partitura.json')).json();
const SEED=P.seed,BPM=P.bpm,SPB=60/BPM,BAR=SPB*4,T0=P.t0,SR=44100,LEN=P.len;
const tb=(bar,beat=0)=>T0+(bar*4+beat)*SPB,ts=(bar,step)=>tb(bar,step/4);
function hash(s){let h=1779033703^s.length;for(let i=0;i<s.length;i++){h=Math.imul(h^s.charCodeAt(i),3432918353);h=h<<13|h>>>19;}h=Math.imul(h^h>>>16,2246822507);h=Math.imul(h^h>>>13,3266489909);return (h^h>>>16)>>>0;}
function rng(tag){let a=hash(SEED+':'+tag);return ()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}
const hz=n=>440*2**((n-69)/12);

/* ---------- 1. El narrador: el vocoder de consola, parchado en una copia ---------- */
if(!window.CantaMusica){let src=await (await fetch('/consola/consola/static/lectura/musica.js')).text();
 const patch=(a,b)=>{if(!src.includes(a))throw Error('no encontré en musica.js: '+a);src=src.split(a).join(b);};
 patch('window.LecturaMusica=','window.CantaMusica=');
 patch('midi:midi(m,m.vozOctave,deg)+bend};','midi:(v.canto??(midi(m,m.vozOctave,deg)+bend))};');
 patch('f.frequency.setTargetAtTime(F[k],t0,.012)','f.frequency.setTargetAtTime(F[k]*(window.CANTA_FORMANT||1),t0,.012)');
 patch('nodes.push(o);oscs.push(o);});','nodes.push(o);oscs.push(o);if(window.CANTA_VIB&&ev.dur>.3){const l=ctx.createOscillator(),lg=ctx.createGain();l.frequency.value=5.4;lg.gain.setValueAtTime(0,at);lg.gain.setValueAtTime(0,at+.2);lg.gain.linearRampToValueAtTime(window.CANTA_VIB,at+.55);l.connect(lg);lg.connect(o.detune);l.start(at);l.stop(at+ev.dur+.6);}});');
 const s=document.createElement('script');s.textContent=src;document.head.append(s);}
const CM=window.CantaMusica,p0=Lectura.snapshot().piece;
const base={on:false,root:'C',scale:'major',gain:.8,reverb:.05,delay:0,delayTime:.3,pulse:'none',density:0,vozOctave:3,vozRate:1,vozCarrier:'sierra',vozMelody:'monotono',vozGain:1,instruments:[]};
function stretch(syl,n){const s=syl.toLowerCase(),idx=Math.max(...[...'aeiou'].map(c=>s.lastIndexOf(c)));if(idx<0)return s.includes('y')?s.replace('y','i'.repeat(n)):s;return s.slice(0,idx+1)+s[idx].repeat(n-1)+s.slice(idx+1);}
async function sing(syl,note,D,{carrier='sierra',formant=1.08,vib=14}={}){
 const piece={...p0,seed:SEED,music:CM.normalize({...base,vozCarrier:carrier,voices:[{instrument:'none',octave:4,gain:.7,pan:0,entry:'none',words:false,gesture:false}]})};
 let v,ev;for(let n=1;n<=48;n++){v={i:0,key:'s',born:0,duration:D/.95,text:stretch(syl,n),effect:'fade',hold:0,speak:'vocoder',canto:note};ev=CM.speechEvents(piece,v)[0];if(ev.dur>=D*.97)break;}
 window.CANTA_FORMANT=formant;window.CANTA_VIB=vib;
 const buf=await CM.render(piece,[v],ev.dur+.6,SR),vt=(ev.steps.find(s=>s.v)||{t:0}).t;
 let pk=0;for(let c=0;c<2;c++){const d=buf.getChannelData(c);for(let k=0;k<d.length;k++)pk=Math.max(pk,Math.abs(d[k]));}
 return {buf,vt,norm:pk>0?1/pk:1};}

/* ---------- 2. La letra del narrador: sílaba:nota:tiempos (- = silencio), un compás por renglón ---------- */
const NOTE={C:0,D:2,E:4,F:5,G:7,A:9,B:11};
const nm=s=>{const m=/^([A-G])(b|#)?(-?\d)$/.exec(s);if(!m)throw Error('nota: '+s);return 12*(+m[3]+1)+NOTE[m[1]]+(m[2]==='b'?-1:m[2]==='#'?1:0);};
function score(str,bar,tr=0,o={}){const out=[];let beat=0;for(const tok of str.trim().split(/\s+/)){const [a,b,c]=tok.split(':');if(a==='-'){beat+=+b;continue;}out.push({syl:a,note:nm(b)+tr,t:tb(bar,beat),D:+c*SPB-.03,...o});beat+=+c;}return out;}
const NL=String.fromCharCode(10);
function scoreBars(str,bar0,tr=0,o={}){return str.trim().split(NL).flatMap((l,k)=>score(l,bar0+k,tr,o));}
/* verso (compases 4-11): el compás 9 lo cantan ellos («po-yo», «pi-ka», «ja ja ja») */
const VERSO=`nun:D5:.5 ca:D5:.5 di:E5:.5 ji:F#5:.5 mos:G5:1 u:F#5:.5 na:E5:.5
 pa:E5:.5 la:C#5:.5 bra:A4:2 -:1
 so:C#5:.5 lo:C#5:.5 gri:E5:.5 tos:F#5:1 al:E5:.5 sal:C#5:.5 -:.5
 tar:D5:2 -:2
 po:B4:.5 yo:D5:.5 pi:G5:.5 ka:F#5:.5 ja:E5:.5 ja:D5:.5 ja:E5:1
 -:4
 has:A4:.5 ta:B4:.5 queal:D5:.5 guien:F#5:.5 nos:A5:1 a:G5:.5 fi:F#5:.5
 no:D5:2.5 -:1.5`;
const PRE=`a:E5:.5 ho:E5:.5 rael:G5:.5 gri:B5:.5 to:A5:1 es:G5:.5 u:F#5:.5
 na:E5:.5 no:F#5:.5 ta:C#5:2 -:1
 y:D5:.5 la:D5:.5 no:G5:.5 ta:B5:.5 es:A5:1 un:G5:.5 co:F#5:.5
 ro:E5:1.5 a:A5:.5 fi:A5:.5 na:A5:.5 dos:A5:1`;
const OUTRO=`a:F#5:.5 fi:E5:.5 na:D5:1 dos:D5:2`;
const lead=[...scoreBars(VERSO,4),...scoreBars(PRE,12),...score(OUTRO,38,0,{gain:.8})];

/* ---------- 3. La armonía (de partitura.json) ---------- */
const PC={C:0,'C#':1,D:2,'D#':3,E:4,F:5,'F#':6,G:7,'G#':8,A:9,'A#':10,Bb:10,B:11};
function chord(sym){const m=/^([A-G][b#]?)(m?)$/.exec(sym),root=PC[m[1]],iv=m[2]?[0,3,7,10,14]:[0,4,7,11,14];
 let notes=iv.map(i=>57+root+i);while(notes[0]>61)notes=notes.map(n=>n-12);let b=36+root;if(b>41)b-=12;return {notes,bass:b};}
const CH=P.acordes,sec=b=>P.secciones.find(([,a,z])=>b>=a&&b<z)[0];

/* ---------- 4. La mezcla ---------- */
const ctx=new OfflineAudioContext(2,Math.ceil(LEN*SR),SR),H=rng('humano');
const master=ctx.createGain(),comp=ctx.createDynamicsCompressor();master.gain.value=.8;comp.threshold.value=-14;comp.ratio.value=3;comp.attack.value=.01;comp.release.value=.15;master.connect(comp);comp.connect(ctx.destination);
const mk=(v,to=master)=>{const g=ctx.createGain();g.gain.value=v;g.connect(to);return g;};
const inst=mk(opts.inst??.6),synB=mk(1,inst),bassB=mk(1,inst),coroB=mk(opts.coro??1.25),chopB=mk(opts.chops??1.35),vocB=mk(opts.voc??1.6),drumB=mk(opts.drums??1),fxB=mk(opts.fx??.6);
const verb=ctx.createConvolver(),vr=rng('reverb'),ir=ctx.createBuffer(2,SR*3,SR);for(let c=0;c<2;c++){const d=ir.getChannelData(c);for(let k=0;k<d.length;k++)d[k]=(vr()*2-1)*Math.exp(-k/SR*2.2)*(k<SR*.01?k/(SR*.01):1);}verb.buffer=ir;
const verbG=ctx.createGain();verbG.gain.value=.5;verb.connect(verbG);verbG.connect(master);
const send=(from,g)=>{const s=ctx.createGain();s.gain.value=g;from.connect(s);s.connect(verb);};send(synB,.18);send(vocB,.22);send(coroB,.35);send(chopB,.25);send(fxB,.5);
const dl=ctx.createDelay(2),dfb=ctx.createGain(),dlp=ctx.createBiquadFilter();dl.delayTime.value=SPB*.75;dfb.gain.value=.34;dlp.type='lowpass';dlp.frequency.value=3800;dl.connect(dlp);dlp.connect(dfb);dfb.connect(dl);dlp.connect(master);
[[vocB,.15],[chopB,.22]].forEach(([b,g])=>{const s=ctx.createGain();s.gain.value=g;b.connect(s);s.connect(dl);});
const pan=(p,to)=>{const s=ctx.createStereoPanner();s.pan.value=Math.max(-1,Math.min(1,p));s.connect(to);return s;};
const env=(g,t,a,peak,dec,sus=0.0001,tail=.05,end)=>{g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(peak,t+a);g.gain.setTargetAtTime(Math.max(sus,.0001),t+a,dec);if(end!=null)g.gain.setTargetAtTime(0,end,tail);};
const DET=[-38,-24,-10,0,10,24,38];
function saw7(t,n,dur,vel,{cut=3200,cutEnd=null,cutT=null,a=.004,dec=.3,sus=.6,rel=.1,bus=synB,det=DET,w=.75,q=.8}={}){
 const g=ctx.createGain(),sides=[-w,w].map(p=>{const lp=ctx.createBiquadFilter();lp.type='lowpass';lp.Q.value=q;lp.frequency.setValueAtTime(cut,t);if(cutEnd!=null)lp.frequency.setTargetAtTime(cutEnd,t+.002,cutT??dur/3);lp.connect(pan(p,g));return lp;});
 det.forEach((d,i)=>{const o=ctx.createOscillator(),og=ctx.createGain();o.type='sawtooth';o.frequency.value=hz(n);o.detune.value=d+(H()-.5)*4;og.gain.value=1.4/det.length;o.connect(og);og.connect(sides[i%2]);o.start(t);o.stop(t+dur+rel*6);});
 const out=ctx.createGain();g.connect(out);out.connect(bus);env(out,t,a,vel,dec,vel*sus,rel,t+dur);}
/* acorde future bass: supersierra con el filtro que se abre y un temblor de tono al entrar */
function fbChord(t,notes,dur,vel,cut=5200){notes.forEach(n=>saw7(t,n+12,dur,vel*.05,{cut,cutEnd:cut*.45,cutT:dur*.6,a:.006,dec:.25,sus:.75,rel:.06,w:.9}));}
function sub(t,n,dur,vel,glide=null){const o=ctx.createOscillator(),s=ctx.createOscillator(),g=ctx.createGain(),sg=ctx.createGain();o.frequency.setValueAtTime(hz(n),t);if(glide!=null)o.frequency.exponentialRampToValueAtTime(hz(glide),t+dur*.9);
 s.type='triangle';s.frequency.setValueAtTime(hz(n+12),t);if(glide!=null)s.frequency.exponentialRampToValueAtTime(hz(glide+12),t+dur*.9);sg.gain.value=.25;s.connect(sg);sg.connect(g);o.connect(g);g.connect(bassB);env(g,t,.008,.55*vel,.8,.45*vel,.06,t+dur);[o,s].forEach(x=>{x.start(t);x.stop(t+dur+.5);});}
function arp(t,n,vel,p=0){const o=ctx.createOscillator(),o2=ctx.createOscillator(),lp=ctx.createBiquadFilter(),g=ctx.createGain();o.type='triangle';o2.type='square';o.frequency.value=hz(n);o2.frequency.value=hz(n)*2.001;const g2=ctx.createGain();g2.gain.value=.15;o2.connect(g2);g2.connect(lp);
 lp.type='lowpass';lp.frequency.setValueAtTime(5000,t);lp.frequency.setTargetAtTime(1200,t,.06);o.connect(lp);lp.connect(g);g.connect(pan(p,synB));env(g,t,.002,.06*vel,.08);[o,o2].forEach(x=>{x.start(t);x.stop(t+.5);});}
function pad(t,notes,dur,vel,cut=1600){notes.forEach(n=>saw7(t,n+12,dur,vel*.035,{cut,a:.4,dec:1.5,sus:.85,rel:.5,w:.95}));}
const nb=ctx.createBuffer(1,SR*2,SR),nr=rng('ruido');{const d=nb.getChannelData(0);for(let k=0;k<d.length;k++)d[k]=nr()*2-1;}
function noise(t,dur){const s=ctx.createBufferSource();s.buffer=nb;s.loop=true;s.start(t);s.stop(t+dur+.1);return s;}
function riser(t,dur,vel=1){const s=noise(t,dur),bp=ctx.createBiquadFilter(),g=ctx.createGain();bp.type='bandpass';bp.Q.value=2.5;bp.frequency.setValueAtTime(300,t);bp.frequency.exponentialRampToValueAtTime(10000,t+dur);
 g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(.3*vel,t+dur);g.gain.setValueAtTime(0,t+dur);s.connect(bp);bp.connect(g);g.connect(fxB);}
function impact(t,vel=1){const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.setValueAtTime(140,t);o.frequency.exponentialRampToValueAtTime(30,t+1);o.connect(g);g.connect(fxB);env(g,t,.003,.9*vel,.5);o.start(t);o.stop(t+2.5);
 const s=noise(t,1.5),lp=ctx.createBiquadFilter(),ng=ctx.createGain();lp.type='lowpass';lp.frequency.setValueAtTime(6000,t);lp.frequency.exponentialRampToValueAtTime(200,t+1.2);s.connect(lp);lp.connect(ng);ng.connect(fxB);env(ng,t,.002,.4*vel,.25);}
function reverso(t,dur){const s=noise(t-dur,dur),hp=ctx.createBiquadFilter(),g=ctx.createGain();hp.type='highpass';hp.frequency.value=2000;g.gain.setValueAtTime(.0001,t-dur);g.gain.exponentialRampToValueAtTime(.35,t-.01);g.gain.setValueAtTime(0,t);s.connect(hp);hp.connect(g);g.connect(fxB);}
/* sidechain de medio tiempo: el bombo cae en 1 y en el «y» del 3; el coro bombea igual que los acordes */
const KICKS=b=>['drop','drop2'].includes(sec(b))?[0,2.5]:['verso','pre'].includes(sec(b))?[0,2]:[];
[[synB,.8],[bassB,.5],[coroB,.55]].forEach(([bus,d])=>{bus.gain.setValueAtTime(1,0);for(let b=0;b<P.compases;b++)for(const k of KICKS(b)){const t=tb(b,k);bus.gain.setValueAtTime(1-d,t);bus.gain.linearRampToValueAtTime(1,t+SPB*.85);}});

/* ---------- 5. Las voces del coro (pistas de voces.py) ---------- */
async function pista(nombre,bus,p=0){const ab=await (await fetch(DIR+nombre)).arrayBuffer(),b=await ctx.decodeAudioData(ab),s=ctx.createBufferSource();s.buffer=b;s.connect(pan(p,bus));s.start(0);}
/* el coro, abierto en estéreo con un eco corto de un lado */
{const ab=await (await fetch(DIR+'voces_coro.wav')).arrayBuffer(),b=await ctx.decodeAudioData(ab);
 [[-.55,0],[.55,.013]].forEach(([p,d])=>{const s=ctx.createBufferSource();s.buffer=b;s.connect(pan(p,coroB));s.start(d);});}
await pista('voces_chops.wav',chopB,0);

/* ---------- 6. La batería de consola (kit 808) ---------- */
const LM=window.LecturaMusica;
async function bateria(bar0,bars,d,extra=0){const dr={gain:.62,kit:'tr808',drive:.15,...d};
 const q={...p0,clips:[],tempo:{...p0.tempo,bpm:BPM,meter:4},music:LM.normalize({...p0.music,on:true,gain:.75,reverb:.08,delay:0,pulse:'none',voices:[],drums:LM.drums(dr)})};
 const len=bars*BAR,buf=await LM.render(q,[],len+extra,SR),s=ctx.createBufferSource(),g=ctx.createGain();s.buffer=buf;s.connect(g);g.connect(drumB);
 const at=tb(bar0);g.gain.setValueAtTime(1,at);if(!extra){g.gain.setValueAtTime(1,at+len-.03);g.gain.linearRampToValueAtTime(0,at+len);}s.start(at);}
const q16=n=>'x'+'.'.repeat(n-1),rep=(s,n)=>s.repeat(n);
const MEDIO={kick:'x.........x.....',snare:'........x.......',clap:'........x.......',hat:'x.x.x.x.xxx.x.xx',openhat:'..............x.'};
await bateria(2,2,{hat:rep('.',16)+'o.o.o.o.o.o.oooo',kick:''});
await bateria(4,4,{kick:'x.......x.......',rim:'........x.......',hat:'x...x...x...x...',crash:q16(64)});
await bateria(8,4,{kick:'x.......x.......',clap:'........x.......',hat:'x.x.x.x.x.x.x.x.',openhat:rep('.',48)+'..x...x...x...x.'});
await bateria(12,4,{kick:'x...x...x...x...',snare:'x...x...x...x...'+'x.x.x.x.x.x.x.x.'+'x.x.x.x.x.x.x.x.'+'xxxxxxxxxxxxxxxx',hat:'o.o.o.o.o.o.o.o.'});
await bateria(16,4,{...MEDIO,crash:q16(64)});
await bateria(20,4,{...MEDIO,tomhi:rep('.',48)+'........x.x.xxxx'});
await bateria(24,3,{rim:'........x.......',hat:'..o...o...o...o.'});
await bateria(27,1,{snare:'x.x.x.x.xxxxxxxx',kick:'x.......x.......'});
await bateria(28,4,{...MEDIO,crash:q16(64),drive:.25});
await bateria(32,4,{...MEDIO,spray:q16(64),tomhi:rep('.',48)+'....x.x.x.xxxxxx',drive:.25});
await bateria(36,3,{kick:'x...............',hat:'x...x...x...x...',crash:q16(64)});
await bateria(39,1,{kick:'x...............'},3);

/* ---------- 7. El arreglo ---------- */
const hv=v=>v*(.92+H()*.16);
/* el ritmo de los acordes en el drop: stabs que respiran con el bombo (semicorcheas) */
const RITMO=[[0,3],[3,3],[6,2],[10,3],[13,3]];
for(let bar=0;bar<P.compases;bar++){const S=sec(bar),c=chord(CH[bar]),N=c.notes,T=s=>ts(bar,s);
 const arp16=(vel=.8,oct=24)=>{const ord=[0,2,1,3,4,3,2,1];for(let s=0;s<16;s+=1)arp(T(s),N[ord[s%8]]+oct-12,hv(vel)*(s%4?.7:1),s%2?.4:-.4);};
 if(S==='intro'){pad(T(0),N,BAR,.8+bar*.1,900+bar*400);if(bar===3)riser(T(0),BAR,.8);}
 if(S==='verso'){pad(T(0),N,BAR*.98,.6,1300);sub(T(0),c.bass,BAR*.9,.55);if(bar>=8)arp16(.45);}
 if(S==='pre'){pad(T(0),N,BAR*.98,.8,1600+(bar-12)*1000);for(let s=0;s<16;s+=4)sub(T(s),c.bass,SPB*.8,.6);arp16(.5+(bar-12)*.12);if(bar===14)riser(T(0),BAR*2,1.2);if(bar===15)reverso(tb(16),SPB*2);}
 if(S==='drop'||S==='drop2'){RITMO.forEach(([s,d])=>fbChord(T(s),N,d*SPB/4*.92,hv(1),S==='drop2'?6500:5200));
  sub(T(0),c.bass,SPB*2.4,1,CH[bar+1]?chord(CH[bar+1]).bass:null);sub(T(10),c.bass,SPB*1.4,.9);if(S==='drop2')arp16(.55,36);
  if(bar%4===3)riser(T(8),BAR/2,.6);}
 if(S==='break'){pad(T(0),N,BAR,1,1100+(bar-24)*500);sub(T(0),c.bass,BAR*.95,.7);if(bar===27){riser(T(0),BAR,1.2);reverso(tb(28),SPB);}}
 if(S==='outro'){pad(T(0),N,bar===39?BAR*2:BAR*.98,1,2200-(bar-36)*300);sub(T(0),c.bass,bar>=38?BAR*1.8:BAR*.95,.8);if(bar<38)arp16(.4-(bar-36)*.1,36);}}
[16,28].forEach(b=>impact(tb(b),1));impact(tb(36),.7);

/* ---------- 8. El narrador ---------- */
let sung=0;for(const x of lead){const r=await sing(x.syl,x.note,x.D,{carrier:x.carrier||'sierra',formant:x.formant??1.08,vib:x.vib??14});
 const s=ctx.createBufferSource(),g=ctx.createGain();s.buffer=r.buf;g.gain.value=.5*r.norm*(x.gain??1);s.connect(g);g.connect(pan(0,vocB));s.start(Math.max(0,x.t-r.vt));sung++;}

const out=await ctx.startRendering(),L=out.getChannelData(0),Rr=out.getChannelData(1);let pk=0;for(let k=0;k<L.length;k++)pk=Math.max(pk,Math.abs(L[k]),Math.abs(Rr[k]));const g=.92/pk;
const rms=[];for(let s=0;s<Math.floor(LEN);s+=5){let a=0;const i0=s*SR,i1=Math.min(L.length,(s+5)*SR);for(let k=i0;k<i1;k++)a+=L[k]*L[k];rms.push(+(Math.sqrt(a/(i1-i0))*g).toFixed(3));}
const pcm=new Int16Array(L.length*2);for(let k=0;k<L.length;k++){pcm[k*2]=Math.max(-1,Math.min(1,L[k]*g))*32767;pcm[k*2+1]=Math.max(-1,Math.min(1,Rr[k]*g))*32767;}
const u8=new Uint8Array(pcm.buffer);let b64='';for(let k=0;k<u8.length;k+=32768)b64+=String.fromCharCode(...u8.subarray(k,k+32768));
return {b64:btoa(b64),peak:pk,rms,sung,seconds:LEN};};
