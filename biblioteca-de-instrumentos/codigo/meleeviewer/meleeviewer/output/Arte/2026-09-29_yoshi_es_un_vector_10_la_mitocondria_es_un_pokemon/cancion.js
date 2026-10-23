/* «la mitocondria es un pokémon» (yoshi es un vector, parte 10) — ~95 s de city pop / nu-disco a 108 bpm, Fa mayor.
   Hace dos mil millones de años una célula se tragó a una bacteria y no la digirió: se quedó a vivir y hoy es tu mitocondria
   (Margulis; Hayles, «Bacteria to AI», 2025). Como un pokémon en su pokébola. Y la IA, dicen Bratton, Agüera y Arcas y Manyika
   («Artificial Symbiotic Intelligence», DeepMind), no será una sola mente sino un comité de agentes: modelos, personas, memorias,
   herramientas, que se arman y se desarman (muere la sesión); el espejo contesta. Mewtwo, el pokémon artificial, preside el comité.
   Más entendible que las anteriores: 108 bpm, sílabas de corchea o más, huecos entre frases, y los pokémon cantan la melodía
   del coro junto con el narrador. Más instrumentada: batería de consola, bajo funky, Rhodes FM, guitarra Karplus-Strong,
   cuerdas, metales, glockenspiel y arpegio. Las voces de los pokémon son las del juego afinadas (voces.py → voces_*.wav).
   Se corre dentro del visor de lectura: window.cancion(opciones) → WAV. */
'use strict';
window.cancion=async function(opts={}){
const DIR='/meleeviewer/output/Arte/2026-09-29_yoshi_es_un_vector_10_la_mitocondria_es_un_pokemon/';
const SEED='yoshi-es-un-vector-10-la-mitocondria-es-un-pokemon',BPM=108,SPB=60/BPM,BAR=SPB*4,T0=.35,SR=44100,LEN=99,NBAR=42;
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
async function sing(syl,note,D,{carrier='sierra',formant=1.04,vib=10}={}){
 const piece={...p0,seed:SEED,music:CM.normalize({...base,vozCarrier:carrier,voices:[{instrument:'none',octave:4,gain:.7,pan:0,entry:'none',words:false,gesture:false}]})};
 let v,ev;for(let n=1;n<=48;n++){v={i:0,key:'s',born:0,duration:D/.95,text:stretch(syl,n),effect:'fade',hold:0,speak:'vocoder',canto:note};ev=CM.speechEvents(piece,v)[0];if(ev.dur>=D*.97)break;}
 window.CANTA_FORMANT=formant;window.CANTA_VIB=vib;
 const buf=await CM.render(piece,[v],ev.dur+.6,SR),vt=(ev.steps.find(s=>s.v)||{t:0}).t;
 let pk=0;for(let c=0;c<2;c++){const d=buf.getChannelData(c);for(let k=0;k<d.length;k++)pk=Math.max(pk,Math.abs(d[k]));}
 return {buf,vt,norm:pk>0?1/pk:1};}

/* ---------- 2. La letra: sílaba:nota:tiempos (- = silencio), un compás por renglón. voces.py y video.html la leen de aquí ---------- */
const NOTE={C:0,D:2,E:4,F:5,G:7,A:9,B:11};
const nm=s=>{const m=/^([A-G])(b|#)?(-?\d)$/.exec(s);if(!m)throw Error('nota: '+s);return 12*(+m[3]+1)+NOTE[m[1]]+(m[2]==='b'?-1:m[2]==='#'?1:0);};
function score(str,bar,tr=0,o={}){const out=[];let beat=0;for(const tok of str.trim().split(/\s+/)){const [a,b,c]=tok.split(':');if(a==='-'){beat+=+b;continue;}out.push({syl:a,note:nm(b)+tr,t:tb(bar,beat),D:+c*SPB-.03,...o});beat+=+c;}return out;}
const NL=String.fromCharCode(10);
function scoreBars(str,bar0,tr=0,o={}){return str.trim().split(NL).flatMap((l,k)=>score(l,bar0+k,tr,o));}
const INTRO=`quien:C5:.5 pien:D5:.5 sa:E5:1 a:D5:.5 qui:C5:1.5`;
const VERSO=`ha:C5:.5 ce:C5:.5 dos:F5:1 mil:E5:.5 mi:D5:.5 llo:C5:.5 nes:D5:.5
 dea:E5:1 ños:C5:2 -:1
 se:D5:.5 tra:D5:.5 ga:F5:.5 ron:F5:.5 u:G5:1 na:F5:1
 bac:E5:.5 te:E5:.5 ria:G5:2 -:1
 no:C5:.5 la:C5:.5 di:F5:.5 gi:F5:.5 rie:A5:1 ron:G5:1
 se:F5:.5 que:E5:.5 do:D5:1 -:2
 hoy:D5:.5 es:D5:.5 tu:F5:.5 mi:G5:.5 to:A5:1 con:G5:1
 dria:E5:2 -:2`;
const CORO=`la:F5:.5 mi:F5:.5 to:A5:.5 con:A5:.5 dria:C6:1 es:A5:1
 un:G5:.5 po:G5:.5 ke:A5:.5 mon:G5:1.5 -:1
 vi:E5:.5 ve:E5:.5 en:G5:.5 su:G5:.5 po:A5:1 ke:G5:1
 bo:F5:.5 la:E5:.5 que:D5:.5 e:E5:.5 res:F5:.5 tu:D5:1.5
 na:D5:.5 die:F5:.5 pien:A5:1 sa:G5:.5 so:F5:.5 lo:G5:1
 -:4
 yo:A5:.5 shi:A5:.5 es:G5:.5 vec:F5:.5 tor:G5:1 tu:A5:1
 en:G5:.5 jam:F5:.5 bre:F5:2 -:1`;
const VERSO2=`la:C5:.5 i:C5:.5 a:F5:.5 noes:F5:.5 u:E5:.5 na:D5:.5 so:C5:.5 la:D5:.5
 men:E5:1 te:C5:2 -:1
 es:D5:.5 un:D5:.5 co:F5:.5 mi:F5:.5 te:G5:1 dea:F5:1
 gen:E5:.5 tes:G5:2.5 -:1
 se:C5:.5 cie:C5:.5 rra:F5:.5 la:F5:.5 se:A5:1 sion:G5:1
 y:F5:.5 se:E5:.5 mue:D5:1 re:C5:1 -:1
 yel:D5:.5 es:D5:.5 pe:F5:.5 jo:G5:.5 con:A5:1 tes:G5:1
 ta:E5:2 -:2`;
const PUENTE=`el:F5:.5 co:F5:.5 ne:Ab5:.5 jo:Ab5:.5 ve:C6:1 co:Ab5:.5 mo:F5:.5
 co:G5:.5 ne:Bb5:.5 jo:G5:2 -:1
 pi:A5:.5 ka:A5:.5 chu:C6:.5 ve:A5:.5 co:G5:.5 mo:F5:.5 pi:A5:.5 ka:C6:.5
 chu:Bb5:2 -:2
 pen:D5:.5 sar:F5:.5 es:A5:.5 dar:A5:.5 le:G5:.5 sen:F5:.5 ti:G5:.5 do:A5:.5
 aun:G5:.5 que:G5:.5 no:A5:.5 se:Bb5:.5 pas:A5:1 -:1`;
const OUTRO=`na:D5:.5 die:F5:.5 pien:A5:1 sa:G5:.5 so:F5:.5 lo:F5:1`;
const SECC=[['intro',0,2],['verso',2,10],['coro',10,18],['verso2',18,26],['puente',26,32],['coro2',32,40],['outro',40,42]];
const lead=[...score(INTRO,1),...scoreBars(VERSO,2),...scoreBars(CORO,10,0,{coro:1}),...scoreBars(VERSO2,18),...scoreBars(PUENTE,26),...scoreBars(CORO,32,0,{coro:1}),...score(OUTRO,40,0,{coro:1})];

/* ---------- 3. La armonía ---------- */
const CH=['Bbmaj7','Am7',
 'Fmaj7','Am7','Bbmaj7','C7','Fmaj7','Am7','Gm7','C7',
 'Bbmaj7','C7','Am7','Dm7','Gm7','C7','Fmaj7','F7',
 'Fmaj7','Am7','Bbmaj7','C7','Fmaj7','Am7','Gm7','C7',
 'Dbmaj7','Ebmaj7','Fmaj7','C7sus','Dm7','C7',
 'Bbmaj7','C7','Am7','Dm7','Gm7','C7','Fmaj7','F7',
 'Bbmaj7','Fmaj7'];
const PC={C:0,'C#':1,Db:1,D:2,'D#':3,Eb:3,E:4,F:5,'F#':6,Gb:6,G:7,'G#':8,Ab:8,A:9,'A#':10,Bb:10,B:11};
const QUAL={maj7:[0,4,7,11,14],m7:[0,3,7,10,14],7:[0,4,7,10,14],'7sus':[0,5,7,10,14]};
function chord(sym){const m=/^([A-G][b#]?)(.*)$/.exec(sym),root=PC[m[1]],iv=QUAL[m[2]];if(!iv)throw Error('acorde: '+sym);
 let notes=iv.slice(1).map(i=>53+root+i);while(notes[0]>60)notes=notes.map(n=>n-12);let b=36+root;if(b>41)b-=12;return {notes,bass:b,root};}
const sec=b=>(SECC.find(([,a,z])=>b>=a&&b<z)||['outro'])[0];

/* ---------- 4. La mezcla ---------- */
const ctx=new OfflineAudioContext(2,Math.ceil(LEN*SR),SR),H=rng('humano');
const master=ctx.createGain(),comp=ctx.createDynamicsCompressor();master.gain.value=.8;comp.threshold.value=-14;comp.ratio.value=2.5;comp.attack.value=.012;comp.release.value=.18;master.connect(comp);comp.connect(ctx.destination);
const mk=(v,to=master)=>{const g=ctx.createGain();g.gain.value=v;g.connect(to);return g;};
const inst=mk(opts.inst??.7),vocB=mk(opts.voc??2),pokeB=mk(opts.poke??1.3),drumB=mk(opts.drums??.95),fxB=mk(opts.fx??.5);
/* para que se entienda: en los coros y el final la banda baja ~3 dB y los pokémon ~1.5 dB (medido: ahí el narrador quedaba parejo con todo) */
[[inst,opts.inst??.7,.5],[pokeB,opts.poke??1.3,1.1]].forEach(([bus,alto,bajo])=>{bus.gain.setValueAtTime(alto,0);for(const [n,a,z] of [['coro',10,18],['coro2',32,40],['outro',40,42]]){bus.gain.setValueAtTime(alto,tb(a)-.08);bus.gain.linearRampToValueAtTime(bajo,tb(a)+.05);bus.gain.setValueAtTime(bajo,tb(z)-.08);bus.gain.linearRampToValueAtTime(z>=42?bajo:alto,tb(z)+.05);}});
const verb=ctx.createConvolver(),vr=rng('reverb'),ir=ctx.createBuffer(2,SR*3,SR);for(let c=0;c<2;c++){const d=ir.getChannelData(c);for(let k=0;k<d.length;k++)d[k]=(vr()*2-1)*Math.exp(-k/SR*2.4)*(k<SR*.01?k/(SR*.01):1);}verb.buffer=ir;
const verbG=ctx.createGain();verbG.gain.value=.45;verb.connect(verbG);verbG.connect(master);
const send=(from,g)=>{const s=ctx.createGain();s.gain.value=g;from.connect(s);s.connect(verb);};send(inst,.14);send(vocB,.16);send(pokeB,.3);send(fxB,.5);
const dl=ctx.createDelay(2),dfb=ctx.createGain(),dlp=ctx.createBiquadFilter();dl.delayTime.value=SPB*.75;dfb.gain.value=.3;dlp.type='lowpass';dlp.frequency.value=3500;dl.connect(dlp);dlp.connect(dfb);dfb.connect(dl);dlp.connect(master);
[[vocB,.1],[pokeB,.18]].forEach(([b,g])=>{const s=ctx.createGain();s.gain.value=g;b.connect(s);s.connect(dl);});
const pan=(p,to)=>{const s=ctx.createStereoPanner();s.pan.value=Math.max(-1,Math.min(1,p));s.connect(to);return s;};
const env=(g,t,a,peak,dec,sus=0.0001,tail=.05,end)=>{g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(peak,t+a);g.gain.setTargetAtTime(Math.max(sus,.0001),t+a,dec);if(end!=null)g.gain.setTargetAtTime(0,end,tail);};
function vibr(o,t,rate,cents,delay,dur){const l=ctx.createOscillator(),lg=ctx.createGain();l.frequency.value=rate;lg.gain.setValueAtTime(0,t);lg.gain.setValueAtTime(0,t+delay);lg.gain.linearRampToValueAtTime(cents,t+delay+.3);l.connect(lg);lg.connect(o.detune);l.start(t);l.stop(t+dur+.5);}
/* Rhodes FM */
function ep(t,n,dur,vel,p=0){const f=hz(n),c=ctx.createOscillator(),mo=ctx.createOscillator(),mg=ctx.createGain(),g=ctx.createGain(),ti=ctx.createOscillator(),tg=ctx.createGain(),out=pan(p,inst);
 c.frequency.value=f;mo.frequency.value=f;mg.gain.setValueAtTime(f*1.6*vel,t);mg.gain.setTargetAtTime(f*.15,t,.18);mo.connect(mg);mg.connect(c.frequency);
 ti.frequency.value=f*14.2;tg.gain.setValueAtTime(.022*vel,t);tg.gain.setTargetAtTime(0,t,.012);ti.connect(tg);tg.connect(out);
 env(g,t,.005,.11*vel,.6,.045*vel,.08,t+dur);c.connect(g);g.connect(out);[c,mo,ti].forEach(o=>{o.start(t);o.stop(t+dur+.7);});}
/* bajo funky: sierra + cuadrada con filtro que muerde */
function bajo(t,n,dur,vel){const lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.Q.value=6;lp.frequency.setValueAtTime(300+1800*vel,t);lp.frequency.setTargetAtTime(260,t,.06);lp.connect(g);g.connect(inst);
 [['sawtooth',0,.55],['square',-1200,.5]].forEach(([ty,d,a])=>{const o=ctx.createOscillator(),og=ctx.createGain();o.type=ty;o.frequency.value=hz(n);o.detune.value=d;og.gain.value=a;o.connect(og);og.connect(lp);o.start(t);o.stop(t+dur+.2);});
 env(g,t,.004,.36*vel,.14,.18*vel,.025,t+dur);}
/* guitarra: Karplus-Strong calculado aquí mismo (una cuerda por nota), apagada con la palma o abierta */
const ksr=rng('cuerda');
function cuerda(t,n,dur,vel,apagada=false,p=0){const f=hz(n),N=Math.max(2,Math.round(SR/f)),len=Math.ceil(SR*Math.min(dur+.3,2.5)),b=ctx.createBuffer(1,len,SR),d=b.getChannelData(0),buf=new Float32Array(N);
 for(let i=0;i<N;i++)buf[i]=(ksr()*2-1);const damp=apagada?.93:.996;let k=0,prev=0;
 for(let i=0;i<len;i++){const v=buf[k],nx=buf[(k+1)%N];const y=damp*.5*(v+nx);buf[k]=y;d[i]=v*(apagada?Math.exp(-i/SR/.045):1);k=(k+1)%N;}
 const s=ctx.createBufferSource(),g=ctx.createGain(),lp=ctx.createBiquadFilter();lp.type='lowpass';lp.frequency.value=apagada?1800:4200;s.buffer=b;s.connect(lp);lp.connect(g);g.connect(pan(p,inst));g.gain.setValueAtTime(.16*vel,t);g.gain.setTargetAtTime(0,t+dur,.05);s.start(t);s.stop(t+len/SR);}
function rasgueo(t,notes,vel,apagada,p){notes.forEach((n,i)=>cuerda(t+i*.007,n,apagada?.08:SPB*1.5,vel*(1-i*.08),apagada,p));}
function cuerdas(t,notes,dur,vel){const lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.frequency.value=2600;lp.connect(g);g.connect(inst);
 notes.forEach((n,i)=>[-8,0,8].forEach(dt=>{const o=ctx.createOscillator();o.type='sawtooth';o.frequency.value=hz(n);o.detune.value=dt+(H()-.5)*6;vibr(o,t,4.8+i*.2,7,.4,dur);o.connect(pan((i-1.5)*.35,lp));o.start(t);o.stop(t+dur+1.2);}));
 env(g,t,.45,.016*vel,1.5,.014*vel,.4,t+dur);}
function metal(t,notes,dur,vel){notes.forEach((n,i)=>{const lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.Q.value=2;lp.frequency.setValueAtTime(600,t);lp.frequency.linearRampToValueAtTime(3200*vel+800,t+.05);lp.frequency.setTargetAtTime(1200,t+.08,.15);lp.connect(g);g.connect(pan((i-1.5)*.3,inst));
 [['sawtooth',0],['sawtooth',6],['square',-4]].forEach(([ty,d])=>{const o=ctx.createOscillator();o.type=ty;o.frequency.value=hz(n);o.detune.value=d;o.connect(lp);o.start(t);o.stop(t+dur+.3);});env(g,t,.025,.03*vel,.25,.022*vel,.05,t+dur);});}
function glock(t,n,vel,p=0){const out=pan(p,inst);[[1,1,1.4],[2.76,.3,.4],[5.4,.12,.15]].forEach(([r,a,d])=>{const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.value=hz(n)*r;env(g,t,.001,.05*vel*a,d/3);o.connect(g);g.connect(out);o.start(t);o.stop(t+d*3);});}
function pluck(t,n,vel,p=0){const o=ctx.createOscillator(),lp=ctx.createBiquadFilter(),g=ctx.createGain();o.type='square';o.frequency.value=hz(n);lp.type='lowpass';lp.frequency.setValueAtTime(4000,t);lp.frequency.setTargetAtTime(700,t,.05);o.connect(lp);lp.connect(g);g.connect(pan(p,inst));env(g,t,.002,.04*vel,.07);o.start(t);o.stop(t+.4);}
const nb=ctx.createBuffer(1,SR*2,SR),nr=rng('ruido');{const d=nb.getChannelData(0);for(let k=0;k<d.length;k++)d[k]=nr()*2-1;}
function riser(t,dur,vel=1){const s=ctx.createBufferSource(),bp=ctx.createBiquadFilter(),g=ctx.createGain();s.buffer=nb;s.loop=true;bp.type='bandpass';bp.Q.value=2.5;bp.frequency.setValueAtTime(300,t);bp.frequency.exponentialRampToValueAtTime(9000,t+dur);
 g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(.25*vel,t+dur);g.gain.setValueAtTime(0,t+dur);s.connect(bp);bp.connect(g);g.connect(fxB);s.start(t);s.stop(t+dur+.05);}

/* ---------- 5. Las voces de los pokémon (pistas de voces.py) ---------- */
for(const [nombre,p] of [['voces_coro.wav',-.35],['voces_coro.wav',.35],['voces_chops.wav',0]]){const ab=await (await fetch(DIR+nombre)).arrayBuffer(),b=await ctx.decodeAudioData(ab),s=ctx.createBufferSource();s.buffer=b;s.connect(pan(p,pokeB));s.start(nombre==='voces_coro.wav'&&p>0?.012:0);}

/* ---------- 6. La batería de consola (kit acústico) ---------- */
const LM=window.LecturaMusica,R=LM.RITMOS;
async function bateria(bar0,bars,d,extra=0){const dr={gain:.6,kit:'acustico',...d};
 const q={...p0,clips:[],tempo:{...p0.tempo,bpm:BPM,meter:4},music:LM.normalize({...p0.music,on:true,gain:.75,reverb:.1,delay:0,pulse:'none',voices:[],drums:LM.drums(dr)})};
 const len=bars*BAR,buf=await LM.render(q,[],len+extra,SR),s=ctx.createBufferSource(),g=ctx.createGain();s.buffer=buf;s.connect(g);g.connect(drumB);
 const at=tb(bar0);g.gain.setValueAtTime(1,at);if(!extra){g.gain.setValueAtTime(1,at+len-.03);g.gain.linearRampToValueAtTime(0,at+len);}s.start(at);}
const q16=n=>'x'+'.'.repeat(n-1),rep=(s,n)=>s.repeat(n);
const CP={kick:'x......x..x.....',snare:'....x.......x...',hat:'x.xxx.xxx.xxx.xx',openhat:'......x.......x.'};
const DISCO={kick:'x...x...x...x...',snare:'....x.......x...',clap:'....o.......o...',hat:'o.x.o.x.o.x.o.x.',openhat:'..x...x...x...x.'};
await bateria(1,1,{hat:'o.o.o.o.o.o.oooo',snare:'............o.oo'});
await bateria(2,4,{...CP,snare:'',rim:'....x.......x...',crash:q16(64)});
await bateria(6,4,{...CP,tomhi:rep('.',48)+'..........x.x.xx'});
await bateria(10,4,{...DISCO,crash:q16(64)});
await bateria(14,4,{...DISCO,cowbell:'..x...x...x...x.',tommid:rep('.',48)+'........x.x.x.xx'});
await bateria(18,4,{...CP,crash:q16(64)});
await bateria(22,4,{...CP,snare:'....x.......x..o',tomhi:rep('.',48)+'..........x.x.xx'});
await bateria(26,4,{kick:'x.........x.....',rim:'....x.......x...',hat:'..x...x...x...x.',ride:'x.o.x.o.x.o.x.o.'});
await bateria(30,2,{...R.breakbeat,crash:q16(32),snare:rep('.',16)+'x.x.x.x.xxxxxxxx'});
await bateria(32,4,{...DISCO,crash:q16(64),spray:q16(64)});
await bateria(36,4,{...DISCO,cowbell:'..x...x...x...x.',tomhi:rep('.',48)+'....x.x.x.xxxxxx'});
await bateria(40,2,{kick:'x...............',crash:'x...............',hat:'o...o...o...o...'},3);

/* ---------- 7. El arreglo ---------- */
const hv=v=>v*(.92+H()*.16),ht=t=>t+(H()-.5)*.007;
for(let bar=0;bar<NBAR;bar++){const S=sec(bar),c=chord(CH[bar]),N=c.notes,T=s=>ts(bar,s),nx=CH[bar+1]?chord(CH[bar+1]):c;
 const comp=(pat,vel=1)=>pat.forEach(([s,d,v])=>N.forEach((n,k)=>ep(ht(T(s))+k*.01,n,d*SPB/4,hv(v*vel),(k-1.5)*.3)));
 const linea=(vel=.85)=>[[0,3,c.bass],[3,1,c.bass+12],[6,1,c.bass],[8,2,c.bass+7],[11,1,c.bass+12],[12,1,c.bass+10],[14,2,nx.bass-1]].forEach(([s,d,n])=>bajo(ht(T(s)),n,d*SPB/4*.9,hv(vel)));
 const scratch=(vel=.8)=>{for(let s=0;s<16;s++){if(s%4===2||s%8===7)rasgueo(ht(T(s)),N.map(n=>n+12),hv(vel),true,.45);}};
 const glockMel=(vel=.8)=>[0,3,6,8,11,14].forEach((s,k)=>glock(T(s),N[[3,2,1,3,2,0][k]]+24,vel,(k%2?.4:-.4)));
 if(S==='intro'){comp([[0,16,.6]]);glockMel(1);cuerdas(T(0),N.map(n=>n+12),BAR,.8);if(bar===1){riser(T(8),BAR/2,.6);metal(T(12),N.map(n=>n+12),SPB*.9,.8);}}
 if(S==='verso'||S==='verso2'){comp([[0,3,.75],[3,2,.45],[7,3,.65],[10,4,.55]]);linea(bar<6&&S==='verso'?.6:.85);scratch(bar>=6||S==='verso2'?.8:.5);
  if(S==='verso2')cuerdas(T(0),[N[0]],BAR,.6);}
 if(S==='coro'||S==='coro2'){comp([[0,2,.7],[3,2,.5],[6,2,.6],[8,2,.7],[11,2,.5],[14,2,.6]]);linea(.95);scratch(.9);cuerdas(T(0),N.map(n=>n+12),BAR*.98,1.1);
  if(bar%2===0)metal(T(0),N.map(n=>n+12),SPB*.4,1);metal(T(14),nx.notes.map(n=>n+12),SPB*.45,.9);
  if(S==='coro2')[0,4,8,12].forEach((s,k)=>glock(T(s),N[(k+bar)%4]+24,.6,k%2?.4:-.4));if(bar===17||bar===39)riser(T(8),BAR/2,.7);}
 if(S==='puente'){cuerdas(T(0),N.map(n=>n+12),BAR*.98,.9);for(let s=0;s<16;s++)pluck(T(s),N[[0,1,2,3,2,1,3,2][s%8]]+12,hv(.7)*(s%4?.7:1),s%2?.4:-.4);
  bajo(T(0),c.bass,SPB*1.8,.7);bajo(T(8),c.bass+7,SPB*1.8,.6);if(bar>=30){comp([[0,4,.6],[8,4,.6]]);glockMel(.7);}if(bar===31)riser(T(0),BAR,1);}
 if(S==='outro'){comp([[0,bar===41?24:16,.7]]);cuerdas(T(0),N.map(n=>n+12),bar===41?BAR*1.6:BAR,1);bajo(T(0),c.bass,bar===41?BAR*1.4:BAR*.9,.7);glockMel(.8);if(bar===41)rasgueo(T(0),N.map(n=>n+12),1,false,0);}}

/* ---------- 8. El narrador ---------- */
let sung=0;for(const x of lead){const r=await sing(x.syl,x.note,x.D);
 const s=ctx.createBufferSource(),g=ctx.createGain();s.buffer=r.buf;g.gain.value=.5*r.norm*(x.gain??1);s.connect(g);g.connect(pan(0,vocB));s.start(Math.max(0,x.t-r.vt));sung++;}

const out=await ctx.startRendering(),L=out.getChannelData(0),Rr=out.getChannelData(1);let pk=0;for(let k=0;k<L.length;k++)pk=Math.max(pk,Math.abs(L[k]),Math.abs(Rr[k]));const g=.92/pk;
const rms=[];for(let s=0;s<Math.floor(LEN);s+=5){let a=0;const i0=s*SR,i1=Math.min(L.length,(s+5)*SR);for(let k=i0;k<i1;k++)a+=L[k]*L[k];rms.push(+(Math.sqrt(a/(i1-i0))*g).toFixed(3));}
const pcm=new Int16Array(L.length*2);for(let k=0;k<L.length;k++){pcm[k*2]=Math.max(-1,Math.min(1,L[k]*g))*32767;pcm[k*2+1]=Math.max(-1,Math.min(1,Rr[k]*g))*32767;}
const u8=new Uint8Array(pcm.buffer);let b64='';for(let k=0;k<u8.length;k+=32768)b64+=String.fromCharCode(...u8.subarray(k,k+32768));
return {b64:btoa(b64),peak:pk,rms,sung,seconds:LEN};};
