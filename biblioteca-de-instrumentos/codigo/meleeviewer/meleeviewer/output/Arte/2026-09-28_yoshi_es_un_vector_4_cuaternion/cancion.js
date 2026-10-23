/* «dos vueltas para volver a ti» (yoshi es un vector, parte 4) — ~1 min, girlypop jazzy, sutil y cursi: la amistad como cuaternión.
   La emoción es un cuaternión unitario q = w + xi + yj + zk (calma, alegría, nostalgia, asombro) que viaja por la esfera de cuatro
   dimensiones (EMOCION, abajo) y mueve la mezcla: la alegría sube el vibráfono y la cajita, la nostalgia las cuerdas y el swing, el asombro la
   batería. Una vuelta (360°) lleva q a −1: misma orientación, otra emoción; hacen falta dos vueltas para volver (doble cubierta, truco del plato).
   La voz es el vocoder de consola (copia parchada en memoria). La batería es la de consola: music.drums, renderizada por LecturaMusica.render
   en tramos y puesta a tiempo. Lo demás es síntesis Web Audio sembrada. Se corre dentro del visor de lectura: window.cancion(opciones) → WAV. */
'use strict';
window.cancion=async function(opts={}){
const SEED='yoshi-es-un-vector-4-cuaternion',BPM=110,SPB=60/BPM,BAR=SPB*4,T0=.35,SR=44100,LEN=74;
const tb=(bar,beat=0)=>T0+(bar*4+beat)*SPB,ts=(bar,step)=>tb(bar,step/4);
function hash(s){let h=1779033703^s.length;for(let i=0;i<s.length;i++){h=Math.imul(h^s.charCodeAt(i),3432918353);h=h<<13|h>>>19;}h=Math.imul(h^h>>>16,2246822507);h=Math.imul(h^h>>>13,3266489909);return (h^h>>>16)>>>0;}
function rng(tag){let a=hash(SEED+':'+tag);return ()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}
const hz=n=>440*2**((n-69)/12);

/* ---------- 0. La emoción: cuaternión unitario por compás, interpolado por slerp SIN escoger el camino corto
   (así se ve la doble cubierta: q cruza −1 en el break y regresa a +1 hasta el final). [compás, w, x(i), y(j), z(k)] ---------- */
const EMOCION=`[[0,1,0,0,0],[2,0.8,0.6,0,0],[6,0.62,0.5,0.6,0],[8,0.5,0.35,0.3,0.73],[10,0.2,0.15,0.85,0.45],[14,0.3,0.62,0.2,0.7],[18,-0.2,0.7,0.1,0.68],[22,-1,0,0,0],[24,-0.35,0.62,0.2,0.67],[28,0.4,0.6,0.35,0.6],[31,1,0,0,0]]`;
const KF=JSON.parse(EMOCION).map(([b,...q])=>{const n=Math.hypot(...q);return {b,q:q.map(v=>v/n)};});
function slerp(a,b,t){let d=a[0]*b[0]+a[1]*b[1]+a[2]*b[2]+a[3]*b[3];d=Math.max(-1,Math.min(1,d));const th=Math.acos(d);if(th<1e-6)return a.slice();const s=Math.sin(th);return a.map((v,i)=>(Math.sin((1-t)*th)*v+Math.sin(t*th)*b[i])/s);}
function emocion(bar){if(bar<=KF[0].b)return KF[0].q;for(let i=1;i<KF.length;i++)if(bar<=KF[i].b){const a=KF[i-1],b=KF[i],u=(bar-a.b)/(b.b-a.b),e=u*u*(3-2*u);return slerp(a.q,b.q,e);}return KF.at(-1).q;}
const EM=b=>{const [w,x,y,z]=emocion(b+.5);return {calma:Math.abs(w),alegria:Math.abs(x),nostalgia:Math.abs(y),asombro:Math.abs(z)};};

/* ---------- 1. La voz: el vocoder de consola, parchado en una copia ---------- */
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
async function sing(syl,note,D,{carrier='sierra',formant=1.18,vib=22}={}){
 const piece={...p0,seed:SEED,music:CM.normalize({...base,vozCarrier:carrier,voices:[{instrument:'none',octave:4,gain:.7,pan:0,entry:'none',words:false,gesture:false}]})};
 let v,ev;for(let n=1;n<=48;n++){v={i:0,key:'s',born:0,duration:D/.95,text:stretch(syl,n),effect:'fade',hold:0,speak:'vocoder',canto:note};ev=CM.speechEvents(piece,v)[0];if(ev.dur>=D*.97)break;}
 window.CANTA_FORMANT=formant;window.CANTA_VIB=vib;
 const buf=await CM.render(piece,[v],ev.dur+.6,SR),vt=(ev.steps.find(s=>s.v)||{t:0}).t;
 let pk=0;for(let c=0;c<2;c++){const d=buf.getChannelData(c);for(let k=0;k<d.length;k++)pk=Math.max(pk,Math.abs(d[k]));}
 return {buf,vt,norm:pk>0?1/pk:1};}

/* ---------- 2. La letra: sílaba:nota:tiempos (- = silencio), un compás por renglón ---------- */
const NOTE={C:0,D:2,E:4,F:5,G:7,A:9,B:11};
const nm=s=>{const m=/^([A-G])(b|#)?(-?\d)$/.exec(s);if(!m)throw Error('nota: '+s);return 12*(+m[3]+1)+NOTE[m[1]]+(m[2]==='b'?-1:m[2]==='#'?1:0);};
function score(str,bar,tr=0,o={}){const out=[];let beat=0;for(const tok of str.trim().split(/\s+/)){const [a,b,c]=tok.split(':');if(a==='-'){beat+=+b;continue;}out.push({syl:a,note:nm(b)+tr,t:tb(bar,beat),D:+c*SPB-.035,...o});beat+=+c;}return out;}
const INTRO=`i:E5:.5 jo:F#5:.5 ta:A5:.5 ka:B5:1.5 -:1`;
const VERSO=`con:F#5:.5 an:A5:.5 gu:F#5:.5 los:E5:.5 de:D5:.5 oi:E5:.5 ler:F#5:1
 me:D5:.5 tra:C#5:.5 be:D5:.5 en:F#5:.5 yim:E5:.5 bal:D5:.5 lok:B4:1
 pe:B4:.5 ro:D5:.5 tu:F#5:.5 lle:F#5:.5 gas:F#5:.5 ten:E5:.5 cua:F#5:.5 ter:A5:.5
 nio:G5:1 nes:E5:1 -:2
 tu:F#5:.5 ri:A5:.5 sa:F#5:.5 es:E5:.5 i:A5:1.5 -:.5
 mi:B4:.5 llan:D5:.5 to:F#5:.5 es:E5:.5 jo:E5:1 ta:D5:1
 yel:C#5:.5 a:E5:.5 som:A5:.5 bro:G#5:.5 es:F#5:.5 la:D#5:.5 ka:F#5:1
 i:G5:.5 por:F#5:.5 jo:E5:.5 ta:D5:.5 es:C#5:.5 ka:E5:1.5`;
const PRE=`pe:B4:.5 ro:D5:.5 jo:F#5:.5 ta:E5:.5 por:F#5:.5 i:A5:1.5
 es:G5:.5 me:F#5:.5 nos:E5:.5 ka:D5:1.5 -:1
 el:D5:.5 or:F5:.5 den:A5:.5 im:A5:.5 por:Bb5:.5 ta:A5:1.5
 no:G5:.5 con:A5:.5 mu:G5:.5 ta:E5:.5 mos:C#5:2`;
const CORO_A=`so:B4:.5 mos:D5:.5 u:F#5:.5 na:A5:.5 ro:A5:.5 ta:B5:.5 cion:A5:1
 que:F#5:.5 no:E5:.5 se:F#5:.5 tra:A5:.5 ba:F#5:.5 nun:D5:.5 ca:E5:1
 flu:G5:.5 tu:F#5:.5 a:E5:.5 mi:D5:.5 e:E5:.5 mo:F#5:.5 cion:G5:1
 en:A5:.5 la:F#5:.5 es:E5:.5 fe:D5:.5 ra:E5:.5 de:F#5:.5 cua:A5:.5 tro:C6:.5`;
const CORO_B=`si:B4:.5 me:D5:.5 gi:F#5:.5 ro:A5:.5 u:B5:.5 na:C#6:.5 vuel:B5:.5 ta:A5:.5
 to:F#5:.5 da:E5:.5 vi:F#5:.5 a:A5:.5 no:A5:.5 soy:F#5:.5 yo:D#5:1
 dos:G5:1 vuel:F#5:.5 tas:E5:.5 pa:C#5:.5 ra:E5:.5 vol:G5:.5 ver:A5:.5
 a:B5:1 ti:A5:3`;
/* break: la fórmula del puente de Brougham, sobre acordes que giran por terceras mayores (D → F → Bb → C#: rumbo a Fa#) */
const BREAK=`i:F#5:.5 jo:A5:.5 ta:A5:.5 ka:F#5:.5 me:F5:.5 nos:A5:.5 u:C6:.5 no:A5:.5
 i:D5:.5 jo:F5:.5 ta:A5:.5 ka:Bb5:.5 me:G#5:.5 nos:F5:.5 u:C#5:.5 no:G#5:.5`;
const ULTIMO_B=`gra:B4:.5 cias:D5:.5 por:F#5:.5 gi:A5:.5 rar:B5:.5 con:C#6:.5 mi:B5:.5 go:A5:.5
 dos:A5:.5 vuel:F#5:.5 tas:E5:.5 ya:F#5:.5 qui:A5:.5 es:A5:.5 toy:D#5:1`;
const FINAL=`a:A#4:1 mi:C#5:.5 go:F#5:2.5`;
const FIN=`i:F#2:.5 jo:F#2:.5 ta:F#2:.5 ka:F#2:.5 me:F#2:.5 nos:F#2:.5 u:F#2:.5 no:F#2:1`;
const NL=String.fromCharCode(10);
function scoreBars(str,bar0,tr=0,o={}){return str.trim().split(NL).flatMap((l,k)=>score(l,bar0+k,tr,o));}
/* último coro en Fa# (una tercera mayor arriba: el giro llegó) */
const lead=[...score(INTRO,1),...scoreBars(VERSO,2),...scoreBars(PRE,10),...scoreBars(CORO_A+NL+CORO_B,14,0,{coro:1}),
 ...scoreBars(BREAK,22,0,{carrier:'coro',formant:1.1,gain:.8}),...scoreBars(CORO_A+NL+ULTIMO_B,24,4,{coro:1}),...score(FINAL,30),...score(FIN,32,0,{carrier:'coro',formant:.9,vib:0,gain:.7})];

/* ---------- 3. La armonía ---------- */
const CH=[['Gmaj9'],['A13'],
 ['Dmaj7'],['Bm9'],['Gmaj7'],['A7sus','A7'],['Dmaj7','D7'],['Gmaj7','Gm6'],['F#m7','B7'],['Em7','A7'],
 ['Em9','F#m7'],['Gmaj7','G#dim7'],['Bbmaj7'],['A7sus','A7b9'],
 ['Gmaj7','A7'],['F#m7','Bm7'],['Em7','A7'],['Dmaj7','D7'],['Gmaj7','A/G'],['F#m7','B7'],['Em7','A7'],['D6'],
 ['Dmaj7','F7'],['Bbmaj7','C#7'],
 ['Bmaj7','C#7'],['A#m7','D#m7'],['G#m7','C#7'],['F#maj7','F#7'],['Bmaj7','C#/B'],['A#m7','D#7'],
 ['G#m7','C#7'],['F#maj9']];
const PC={C:0,'C#':1,Db:1,D:2,'D#':3,Eb:3,E:4,F:5,'F#':6,Gb:6,G:7,'G#':8,Ab:8,A:9,'A#':10,Bb:10,B:11};
const QUAL={maj7:[4,7,11,14],maj9:[4,11,14,19],6:[4,7,9,14],m6:[3,7,9,14],m7:[3,7,10,14],m9:[3,10,14,17],7:[4,9,10,14],13:[4,9,10,14],'7b9':[4,7,10,13],'7sus':[5,7,10,14],dim7:[3,6,9,12],'':[4,7,12,14]};
function chord(sym){const m=/^([A-G][b#]?)(.*?)(?:\/([A-G][b#]?))?$/.exec(sym),root=PC[m[1]],iv=QUAL[m[2]];if(!iv)throw Error('acorde: '+sym);
 let notes=iv.map(i=>48+root+i);while(notes[0]<53)notes=notes.map(n=>n+12);while(notes[0]>=64)notes=notes.map(n=>n-12);
 const bp=m[3]?PC[m[3]]:root;return {notes,bass:28+((bp-4+12)%12),fifth:28+((root-4+12)%12)+7};}
const sec=b=>b<2?'intro':b<10?'verso':b<14?'pre':b<22?'coro':b<24?'break':b<30?'ultimo':'final';

/* ---------- 4. La mezcla ---------- */
const ctx=new OfflineAudioContext(2,Math.ceil(LEN*SR),SR),H=rng('humano');
const master=ctx.createGain(),comp=ctx.createDynamicsCompressor();master.gain.value=.8;comp.threshold.value=-15;comp.ratio.value=2.5;comp.attack.value=.015;comp.release.value=.2;master.connect(comp);comp.connect(ctx.destination);
const instB=ctx.createGain(),vocB=ctx.createGain(),drumB=ctx.createGain();instB.gain.value=opts.inst??1;drumB.gain.value=opts.drums??1;vocB.gain.value=opts.voc??1.6;[instB,vocB,drumB].forEach(b=>b.connect(master));
const verb=ctx.createConvolver(),vr=rng('reverb'),ir=ctx.createBuffer(2,SR*3,SR);for(let c=0;c<2;c++){const d=ir.getChannelData(c);for(let k=0;k<d.length;k++)d[k]=(vr()*2-1)*Math.exp(-k/SR*2.1)*(k<SR*.012?k/(SR*.012):1);}verb.buffer=ir;
const verbG=ctx.createGain();verbG.gain.value=.55;verb.connect(verbG);verbG.connect(master);
const send=(from,g)=>{const s=ctx.createGain();s.gain.value=g;from.connect(s);s.connect(verb);};send(instB,.24);send(vocB,.32);
const dl=ctx.createDelay(2),dfb=ctx.createGain(),dlp=ctx.createBiquadFilter(),dsend=ctx.createGain();dl.delayTime.value=SPB*.75;dfb.gain.value=.3;dlp.type='lowpass';dlp.frequency.value=3000;dsend.gain.value=.2;vocB.connect(dsend);dsend.connect(dl);dl.connect(dlp);dlp.connect(dfb);dfb.connect(dl);dlp.connect(master);
const pan=(p,to)=>{const s=ctx.createStereoPanner();s.pan.value=Math.max(-1,Math.min(1,p));s.connect(to);return s;};
const env=(g,t,a,peak,dec,sus=0.0001,tail=.05,end)=>{g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(peak,t+a);g.gain.setTargetAtTime(Math.max(sus,.0001),t+a,dec);if(end!=null)g.gain.setTargetAtTime(0,end,tail);};
function vibr(o,t,rate,cents,delay,dur){const l=ctx.createOscillator(),lg=ctx.createGain();l.frequency.value=rate;lg.gain.setValueAtTime(0,t);lg.gain.setValueAtTime(0,t+delay);lg.gain.linearRampToValueAtTime(cents,t+delay+.3);l.connect(lg);lg.connect(o.detune);l.start(t);l.stop(t+dur+.5);}
function ep(t,n,dur,vel,p=0){const f=hz(n),c=ctx.createOscillator(),mo=ctx.createOscillator(),mg=ctx.createGain(),g=ctx.createGain(),ti=ctx.createOscillator(),tg=ctx.createGain(),out=pan(p,instB);
 c.frequency.value=f;mo.frequency.value=f;mg.gain.setValueAtTime(f*1.5*vel,t);mg.gain.setTargetAtTime(f*.15,t,.18);mo.connect(mg);mg.connect(c.frequency);
 ti.frequency.value=f*14.2;tg.gain.setValueAtTime(.025*vel,t);tg.gain.setTargetAtTime(0,t,.012);ti.connect(tg);tg.connect(out);
 env(g,t,.005,.12*vel,.6,.05*vel,.08,t+dur);c.connect(g);g.connect(out);[c,mo,ti].forEach(o=>{o.start(t);o.stop(t+dur+.7);});}
function bass(t,n,dur,vel){const f=hz(n),o=ctx.createOscillator(),s=ctx.createOscillator(),lp=ctx.createBiquadFilter(),g=ctx.createGain(),sg=ctx.createGain();o.type='triangle';o.frequency.value=f;s.frequency.value=f;
 lp.type='lowpass';lp.Q.value=2;lp.frequency.setValueAtTime(260+900*vel,t);lp.frequency.setTargetAtTime(240,t,.09);o.connect(lp);lp.connect(g);s.connect(sg);sg.gain.value=1;sg.connect(g);
 env(g,t,.008,.3*vel,.3,.18*vel,.04,t+dur);g.connect(instB);[o,s].forEach(x=>{x.start(t);x.stop(t+dur+.3);});}
/* cajita de música: parciales de lengüeta de metal, cortitos y brillantes */
function cajita(t,n,vel,p=0){const out=pan(p,instB);[[1,1,1.1],[3.01,.25,.35],[5.9,.08,.12]].forEach(([r,a,d])=>{const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.value=hz(n)*r;env(g,t,.002,.07*vel*a,d/3);o.connect(g);g.connect(out);o.start(t);o.stop(t+d*3);});}
function vibes(t,n,vel,p=0,dur=1.8){const out=pan(p,instB),g=ctx.createGain(),trem=ctx.createGain(),l=ctx.createOscillator(),lg=ctx.createGain();trem.gain.value=.78;l.frequency.value=5;lg.gain.value=.22;l.connect(lg);lg.connect(trem.gain);l.start(t);l.stop(t+dur+.2);
 [[1,1,dur],[4,.2,.35],[10,.04,.08]].forEach(([r,a,d])=>{const o=ctx.createOscillator(),og=ctx.createGain();o.frequency.value=hz(n)*r;env(og,t,.002,a,d/2.5);o.connect(og);og.connect(g);o.start(t);o.stop(t+d*2.5);});g.gain.value=.065*vel;g.connect(trem);trem.connect(out);}
function pad(t,n,dur,vel,p=0){const out=pan(p,instB),lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.frequency.value=1900;lp.connect(g);g.connect(out);
 [-9,0,9].forEach(dt=>{const o=ctx.createOscillator();o.type='sawtooth';o.frequency.value=hz(n);o.detune.value=dt;vibr(o,t,4.6,6,.5,dur);o.connect(lp);o.start(t);o.stop(t+dur+1);});env(g,t,.5,.02*vel,1.8,.018*vel,.35,t+dur);}
function flauta(t,n,dur,vel,p=0){const out=pan(p,instB),g=ctx.createGain(),o=ctx.createOscillator();o.frequency.setValueAtTime(hz(n),t);vibr(o,t,5.2,16,.25,dur);o.connect(g);g.connect(out);env(g,t,.06,.07*vel,.5,.055*vel,.1,t+dur);o.start(t);o.stop(t+dur+.4);}

/* ---------- 5. La batería de consola: tramos de music.drums renderizados por LecturaMusica y puestos a tiempo ---------- */
const LM=window.LecturaMusica,R=LM.RITMOS;
async function bateria(bar0,bars,d,extra=0){const em=EM(bar0+bars/2),dr={gain:.55,...d,drive:Math.min(.3,(d.drive||0)+em.asombro*.18),swing:Math.min(.35,(d.swing||0)+em.nostalgia*.1)};
 const q={...p0,clips:[],tempo:{...p0.tempo,bpm:BPM,meter:4},music:LM.normalize({...p0.music,on:true,gain:.7,reverb:.12,delay:0,pulse:'none',voices:[],drums:LM.drums(dr)})};
 const len=bars*BAR,buf=await LM.render(q,[],len+extra,SR),s=ctx.createBufferSource(),g=ctx.createGain();s.buffer=buf;s.connect(g);g.connect(drumB);
 const at=tb(bar0);g.gain.setValueAtTime(1,at);if(!extra){g.gain.setValueAtTime(1,at+len-.03);g.gain.linearRampToValueAtTime(0,at+len);}s.start(at);}
const suave={kit:'acustico',hat:'o.o.o.o.o.o.o.o.',rim:'....o.......o...'},q16=n=>'x'+'.'.repeat(n-1);
await bateria(1,1,{kit:'acustico',ride:'o...o...o...o...',rim:'..........o.o.o.'});
await bateria(2,4,{...suave,kick:'x.........x.....',spray:q16(64)});
await bateria(6,4,{...R.citypop,snare:'....o.......o...',hat:'o.oxo.oxo.oxo.ox',spray:q16(64),tomhi:''});
await bateria(10,3,{kit:'acustico',kick:'x.......x.......',rim:'....x.......x...',ride:'x.o.x.o.x.o.x.o.'});
await bateria(13,1,{kit:'acustico',kick:'x.......x.......',snare:'....o...o.o.oooo',tomhi:'........o.......',tommid:'..........o.....',tomlo:'............o...'});
await bateria(14,8,{...R.disco,clap:'....o.......o...',snare:'....o.......o...',spray:q16(64),crash:''});
await bateria(22,2,{...R.ochentas,gain:.5,snare:'',clap:'....o.......o...',spray:q16(32)});
await bateria(24,6,{...R.disco,clap:'....o.......o...',snare:'....o.......o...',spray:q16(32)});
await bateria(30,1,{kit:'acustico',kick:'x.......x.......',rim:'....o.......o...',hat:'o.o.o.o.o.o.o...'});
await bateria(31,1,{kit:'acustico',spray:q16(64),kick:q16(64)},3);

/* ---------- 6. El arreglo: la emoción del compás decide cuánto suena cada cosa ---------- */
const hv=v=>v*(.9+H()*.2),ht=t=>t+(H()-.5)*.008;
for(let bar=0;bar<CH.length;bar++){const S=sec(bar),E=EM(bar),cs=CH[bar].map(chord),nx=CH[bar+1]?chord(CH[bar+1][0]):cs[0],two=cs.length>1;
 const at=(step,push=8)=>two&&step>=push?cs[1]:cs[0],T=s=>ts(bar,s);
 const comp=(pat,push)=>pat.forEach(([s,d,v])=>{const c=at(s,push);c.notes.forEach((n,k)=>ep(ht(T(s))+k*.012,n,d*SPB/4,hv(v*(.75+.35*E.calma)),(k-1.5)*.3));});
 function bs([s,d,k]){const c=k===k.toUpperCase()&&k!=='a'?at(s,0):cs[0],n=k==='a'?nx.bass-1:k.toLowerCase()==='o'?c.bass+12:k==='f'?c.fifth:c.bass;bass(ht(T(s)),n,d*SPB/4*.9,hv(k==='a'?.6:.75));}
 /* alegría: la cajita y el vibráfono; nostalgia: cuerdas; asombro: glissando y metales suaves */
 const brillo=E.alegria,cuerdas=.25+E.nostalgia*.9;
 if(S==='intro'){comp([[0,16,.6]]);[[0,78,2],[2,81,2],[4,83,2],[6,81,2],[8,86,4],[12,83,4]].forEach(([s,n])=>cajita(T(s)+(bar?0:0),n-(bar?2:0),.9,.2));if(bar===1)bass(T(0),cs[0].bass,BAR,.5);}
 if(S==='verso'){comp([[0,3,.75],[3,2,.4],[7,3,.65],[10,4,.55]],7);
  if(bar>=4)(two?[[0,3,'r'],[3,1,'o'],[6,1,'f'],[7,3,'R'],[10,1,'O'],[14,2,'a']]:[[0,3,'r'],[3,1,'o'],[6,2,'r'],[10,2,'f'],[14,2,'a']]).forEach(bs);else bass(T(0),cs[0].bass,BAR*.9,.55);
  if(brillo>.3)[12,13,14,15].forEach((s,k)=>cajita(T(s),at(s,7).notes[k]+24,brillo,.5));if(E.nostalgia>.4)at(0,7).notes.forEach(n=>pad(T(0),n+12,BAR*.95,cuerdas,-.2));}
 if(S==='pre'){comp([[0,7,.7],[8,8,.7]]);[[0,4,'r'],[4,4,'f'],[8,4,'R'],[12,4,'a']].forEach(bs);at(0).notes.forEach(n=>pad(T(0),n+12,SPB*2,cuerdas,.15));at(8).notes.forEach(n=>pad(T(8),n+12,SPB*2,cuerdas,-.15));
  [[0,4],[8,4]].forEach(([s,d])=>flauta(T(s),at(s).notes[3]+12,SPB*d/4*1.9,.8,-.35));}
 if(S==='coro'||S==='ultimo'){comp([[0,2,.75],[3,2,.5],[6,2,.65],[8,2,.75],[11,2,.5],[14,2,.65]],6);
  for(let s=0;s<16;s+=2)bs([s,1.6,s===14?'a':(s>=6&&two)?(s%4?'O':'R'):(s%4?'o':'r')]);
  at(0,6).notes.forEach(n=>pad(T(0),n+12,BAR*.95,cuerdas*1.1,.15));
  [0,4,8,12].forEach((s,k)=>vibes(T(s),at(s,6).notes[(k+bar)%4]+12,.5+brillo*.6,(k%2?.45:-.45)));
  if(bar%2)[12,13,14,15].forEach((s,k)=>cajita(T(s),at(s,6).notes[k]+24,.6+brillo*.4,.55));
  if(E.asombro>.55&&(bar===17||bar===21||bar===27))at(12,6).notes.slice(1).forEach(n=>{const o=hz(n+12);flauta(T(12),n+12,SPB*.9,.7,.3);});}
 if(S==='break'){comp([[0,4,.6],[8,4,.6]]);[[0,6,'r'],[8,6,'R'],[14,2,'a']].forEach(bs);at(0).notes.forEach(n=>pad(T(0),n+12,SPB*2,1,.1));at(8).notes.forEach(n=>pad(T(8),n+12,SPB*2,1,-.1));
  for(let k=0;k<8;k++)vibes(T(k*2),at(k*2).notes[k%4]+24,.7,(k%2?.5:-.5),1);}
 if(S==='final'){if(bar===30){comp([[0,4,.6],[8,4,.6]]);bass(T(0),cs[0].bass,SPB*2,.6);bass(T(8),at(8).bass,SPB*2,.6);}
  else{comp([[0,28,.7]]);bass(T(0),cs[0].bass,SPB*6,.6);for(let k=0;k<14;k++)cajita(T(0)+.2+k*SPB/4,[78,80,82,85,87][k%5]+12*Math.floor(k/5),.8-k*.03,(k%2?.5:-.5));}}
 if([14,24].includes(bar))for(let k=0;k<8;k++)cajita(T(0)+k*.045,[74,76,78,81,83,86,88,90][k]+(bar>=24?4:0),.6,.4);}

/* ---------- 7. Las voces ---------- */
const lines=[...lead];
lead.filter(x=>x.coro).forEach(x=>lines.push({...x,note:x.note-12,carrier:'pulso',gain:.34,pan:.45,formant:1.05}));
lead.filter(x=>x.coro).forEach(x=>lines.push({...x,note:x.note-5,carrier:'sierra',gain:.18,pan:-.45,vib:28}));
let sung=0;for(const x of lines){const r=await sing(x.syl,x.note,x.D,{carrier:x.carrier||'sierra',formant:x.formant??1.18,vib:x.vib??22});
 const s=ctx.createBufferSource(),g=ctx.createGain();s.buffer=r.buf;g.gain.value=.5*r.norm*(x.gain??1);s.connect(g);g.connect(pan(x.pan||0,vocB));s.start(Math.max(0,x.t-r.vt));sung++;}

const out=await ctx.startRendering(),L=out.getChannelData(0),Rr=out.getChannelData(1);let pk=0;for(let k=0;k<L.length;k++)pk=Math.max(pk,Math.abs(L[k]),Math.abs(Rr[k]));const g=.92/pk;
const rms=[];for(let s=0;s<Math.floor(LEN);s+=5){let a=0;const i0=s*SR,i1=Math.min(L.length,(s+5)*SR);for(let k=i0;k<i1;k++)a+=L[k]*L[k];rms.push(+(Math.sqrt(a/(i1-i0))*g).toFixed(3));}
const pcm=new Int16Array(L.length*2);for(let k=0;k<L.length;k++){pcm[k*2]=Math.max(-1,Math.min(1,L[k]*g))*32767;pcm[k*2+1]=Math.max(-1,Math.min(1,Rr[k]*g))*32767;}
const u8=new Uint8Array(pcm.buffer);let b64='';for(let k=0;k<u8.length;k+=32768)b64+=String.fromCharCode(...u8.subarray(k,k+32768));
return {b64:btoa(b64),peak:pk,rms,sung,seconds:LEN};};
