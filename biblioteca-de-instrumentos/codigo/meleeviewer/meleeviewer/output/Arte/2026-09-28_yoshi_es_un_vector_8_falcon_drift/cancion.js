/* «FALCON DRIFT (tofu a domicilio)» (yoshi es un vector, parte 8) — ~78 s de eurobeat a 156 bpm, Re menor → Mi menor.
   Son las tres de la mañana en Mute City: Captain Falcon reparte tofu con un vaso de agua en la cabeza. Si se derrama, lo corren.
   Don Yoshi pidió cuatro kilos. En el break el tofu se tarda y Falcon lo entrega de un FALCON PUNCH; la propina es un huevo de Yoshi.
   Lo electrónico: supersierras de 7 osciladores, bajo de octavas a contratiempo, stabs, arpegio, risers de ruido, impactos, derrapón de llanta
   y todo lo que no es voz ni batería respira con el bombo (sidechain). La voz es el vocoder de consola (copia parchada en memoria) y la batería
   la de consola (music.drums, kit 909), renderizada en tramos por LecturaMusica. Se corre dentro del visor de lectura: window.cancion(opciones) → WAV. */
'use strict';
window.cancion=async function(opts={}){
const SEED='yoshi-es-un-vector-8-falcon-drift',BPM=156,SPB=60/BPM,BAR=SPB*4,T0=.35,SR=44100,LEN=80;
const tb=(bar,beat=0)=>T0+(bar*4+beat)*SPB,ts=(bar,step)=>tb(bar,step/4);
function hash(s){let h=1779033703^s.length;for(let i=0;i<s.length;i++){h=Math.imul(h^s.charCodeAt(i),3432918353);h=h<<13|h>>>19;}h=Math.imul(h^h>>>16,2246822507);h=Math.imul(h^h>>>13,3266489909);return (h^h>>>16)>>>0;}
function rng(tag){let a=hash(SEED+':'+tag);return ()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}
const hz=n=>440*2**((n-69)/12);

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
async function sing(syl,note,D,{carrier='sierra',formant=1.05,vib=10}={}){
 const piece={...p0,seed:SEED,music:CM.normalize({...base,vozCarrier:carrier,voices:[{instrument:'none',octave:4,gain:.7,pan:0,entry:'none',words:false,gesture:false}]})};
 let v,ev;for(let n=1;n<=48;n++){v={i:0,key:'s',born:0,duration:D/.95,text:stretch(syl,n),effect:'fade',hold:0,speak:'vocoder',canto:note};ev=CM.speechEvents(piece,v)[0];if(ev.dur>=D*.97)break;}
 window.CANTA_FORMANT=formant;window.CANTA_VIB=vib;
 const buf=await CM.render(piece,[v],ev.dur+.6,SR),vt=(ev.steps.find(s=>s.v)||{t:0}).t;
 let pk=0;for(let c=0;c<2;c++){const d=buf.getChannelData(c);for(let k=0;k<d.length;k++)pk=Math.max(pk,Math.abs(d[k]));}
 return {buf,vt,norm:pk>0?1/pk:1};}

/* ---------- 2. La letra: sílaba:nota:tiempos (- = silencio), un compás por renglón ---------- */
const NOTE={C:0,D:2,E:4,F:5,G:7,A:9,B:11};
const nm=s=>{const m=/^([A-G])(b|#)?(-?\d)$/.exec(s);if(!m)throw Error('nota: '+s);return 12*(+m[3]+1)+NOTE[m[1]]+(m[2]==='b'?-1:m[2]==='#'?1:0);};
function score(str,bar,tr=0,o={}){const out=[];let beat=0;for(const tok of str.trim().split(/\s+/)){const [a,b,c]=tok.split(':');if(a==='-'){beat+=+b;continue;}out.push({syl:a,note:nm(b)+tr,t:tb(bar,beat),D:+c*SPB-.03,...o});beat+=+c;}return out;}
const NL=String.fromCharCode(10);
function scoreBars(str,bar0,tr=0,o={}){return str.trim().split(NL).flatMap((l,k)=>score(l,bar0+k,tr,o));}
/* «show me your moves», dicho como suena en Mute City, por el robot grave */
const INTRO=`chou:A3:1 mi:A3:.5 yor:G3:.5 mus:A3:2
 fal:D4:1 con:F4:1 drift:A4:1.5 -:.5`;
const VERSO=`tres:A4:.5 de:A4:.5 la:D5:.5 ma:D5:.5 ña:E5:.5 na:F5:1.5
 miut:F5:1 si:E5:.5 ti:D5:1.5 -:1
 don:E5:.5 yo:E5:.5 shi:G5:.5 pi:G5:.5 dio:E5:1 cua:C5:.5 tro:D5:.5
 ki:E5:.5 los:E5:.5 de:D5:.5 to:C5:.5 fu:A4:1.5 -:.5
 un:A4:.5 va:A4:.5 so:D5:.5 dea:D5:.5 gua:F5:1 en:E5:.5 el:D5:.5
 ta:D5:.5 ble:F5:.5 ro:F5:2 -:1
 si:G5:.5 se:G5:.5 de:F5:.5 rra:G5:.5 ma:A5:1 me:G5:.5 co:F5:.5
 rren:E5:.5 del:E5:.5 tra:C#5:.5 ba:E5:.5 jo:A5:1.5 -:.5`;
const PRE=`cur:D5:.5 va:F5:.5 deor:F5:.5 qui:G5:.5 lla:A5:1 cien:G5:.5 too:F5:.5
 chen:E5:.5 ta:F5:.5 gra:G5:.5 dos:E5:1.5 -:1
 pren:C5:.5 do:E5:.5 las:E5:.5 lu:F5:.5 ces:A5:1 y:G5:.5 sue:A5:.5
 nael:Bb5:.5 eu:A5:.5 ro:G5:.5 bit:A5:1 -:1.5`;
const CORO=`fal:F5:.5 con:G5:.5 drift:A5:1.5 -:.5 de:A5:.5 rra:Bb5:.5
 pan:C6:.5 do:Bb5:.5 por:A5:.5 big:G5:.5 blu:E5:1.5 -:.5
 el:E5:.5 to:E5:.5 fu:A5:.5 no:A5:.5 se:G5:.5 rom:A5:.5 pe:C6:1
 yel:A5:.5 a:G5:.5 gua:F5:.5 no:F5:.5 se:E5:.5 ti:E5:.5 ra:D5:1
 fal:F5:.5 con:G5:.5 drift:A5:1.5 -:.5 mis:A5:.5 ro:Bb5:.5
 di:C6:.5 llas:Bb5:.5 en:A5:.5 cen:G5:.5 di:A5:.5 das:G5:1.5
 lle:E5:.5 goan:E5:.5 tes:G5:.5 de:A5:.5 que:C#6:.5 lo:D6:.5 pi:C#6:1
 das:D6:3 -:1`;
/* break: el robot pide movimientos, Yoshi pregunta por su tofu y llega el golpe */
const ROBOT=`chou:D4:1 mi:D4:.5 yor:C4:.5 mus:D4:2`;
const YOSHI=`y:A5:.5 mi:A5:.5 to:A5:.5 fu:D6:1.5 -:1`;
const PUNCH=`fal:F#3:1 con:A3:1 pansh:B3:1.5 -:.5`;
const FINAL=`pro:B4:.5 pi:D5:.5 na:E5:1 un:G5:.5 hue:F#5:.5 vo:E5:.5 de:D5:.5
 yo:E5:1 shi:E5:2 -:1`;
const FIN=`to:E3:.5 fu:E3:.5 en:E3:.5 tre:E3:.5 ga:E3:.5 do:E3:1.5`;
const robot={carrier:'coro',formant:.86,vib:0,gain:.9};
const lead=[...scoreBars(INTRO,0,0,robot),...scoreBars(VERSO,10),...scoreBars(PRE,18),...scoreBars(CORO,22,0,{coro:1}),
 ...score(ROBOT,34,0,robot),...score(YOSHI,35,0,{carrier:'pulso',formant:1.38,vib:30,gain:.8}),...score(ROBOT,36,0,robot),...score(PUNCH,37,0,{...robot,formant:.8,gain:1.1}),
 ...scoreBars(CORO,38,2,{coro:1}),...scoreBars(FINAL,46,0,{coro:1}),...score(FIN,48,0,robot)];

/* ---------- 3. La armonía (un acorde por compás; el último coro ya viene escrito un tono arriba) ---------- */
const CH=['Dm','C',
 'Dm','Bb','C','Am','Dm','Bb','C','A',
 'Dm','Bb','C','Am','Dm','Bb','Gm','A',
 'Bb','C','Am','A7',
 'Bb','C','Am','Dm','Bb','C','A','Dm',
 'Dm','Bb','C','A',
 'Bbmaj7','Dm','Bbmaj7','B7',
 'C','D','Bm','Em','C','D','B','Em',
 'Em','C','Em'];
const PC={C:0,'C#':1,Db:1,D:2,'D#':3,Eb:3,E:4,F:5,'F#':6,Gb:6,G:7,'G#':8,Ab:8,A:9,'A#':10,Bb:10,B:11};
const QUAL={m:[0,3,7,12],'':[0,4,7,12],7:[0,4,7,10],maj7:[0,4,7,11],m7:[0,3,7,10]};
function chord(sym){const m=/^([A-G][b#]?)(.*)$/.exec(sym),root=PC[m[1]],iv=QUAL[m[2]];if(!iv)throw Error('acorde: '+sym);
 let notes=iv.map(i=>57+root+i);while(notes[0]>62)notes=notes.map(n=>n-12);let b=36+root;if(b>43)b-=12;return {notes,bass:b};}
const sec=b=>b<2?'intro':b<10?'riff':b<18?'verso':b<22?'pre':b<30?'coro':b<34?'riff2':b<38?'break':b<46?'ultimo':b<48?'final':'fin';
/* el gancho: la frase de supersierra en semicorcheas (nota:pasos) */
const RIFF=[`D5:2 D5:1 A5:2 F5:2 D6:2 C6:2 A5:2 G5:1 A5:2`,`F5:2 F5:1 Bb5:2 A5:2 F5:2 D5:2 F5:2 G5:1 F5:2`,
 `E5:2 E5:1 G5:2 C6:2 E6:2 D6:2 C6:2 Bb5:1 C6:2`,`A5:3 E5:3 A5:2 C6:2 B5:2 A5:2 E5:2`];
const RIFF_A=`A5:2 C#6:2 E6:2 C#6:2 A5:2 G5:2 E5:2 C#5:2`;
function riff(str,bar,tr=0){let s=0;return str.trim().split(/\s+/).map(tok=>{const [n,d]=tok.split(':'),o={t:ts(bar,s),n:nm(n)+tr,d:+d*SPB/4};s+=+d;return o;});}

/* ---------- 4. La mezcla: todo lo sintético pasa por buses que respiran con el bombo ---------- */
const ctx=new OfflineAudioContext(2,Math.ceil(LEN*SR),SR),H=rng('humano');
const master=ctx.createGain(),comp=ctx.createDynamicsCompressor();master.gain.value=.8;comp.threshold.value=-14;comp.ratio.value=3;comp.attack.value=.01;comp.release.value=.15;master.connect(comp);comp.connect(ctx.destination);
const mk=v=>{const g=ctx.createGain();g.gain.value=v;g.connect(master);return g;};
const synB=mk(1),bassB=mk(1),inst=mk(opts.inst??.9),vocB=mk(opts.voc??2),drumB=mk(opts.drums??1),fxB=mk(opts.fx??.7);synB.disconnect();bassB.disconnect();synB.connect(inst);bassB.connect(inst);
const verb=ctx.createConvolver(),vr=rng('reverb'),ir=ctx.createBuffer(2,SR*3,SR);for(let c=0;c<2;c++){const d=ir.getChannelData(c);for(let k=0;k<d.length;k++)d[k]=(vr()*2-1)*Math.exp(-k/SR*2.6)*(k<SR*.01?k/(SR*.01):1);}verb.buffer=ir;
const verbG=ctx.createGain();verbG.gain.value=.5;verb.connect(verbG);verbG.connect(master);
const send=(from,g)=>{const s=ctx.createGain();s.gain.value=g;from.connect(s);s.connect(verb);};send(synB,.16);send(vocB,.22);send(fxB,.5);
/* eco a corchea con puntillo, para la voz y el gancho */
const dl=ctx.createDelay(2),dfb=ctx.createGain(),dlp=ctx.createBiquadFilter(),dsend=ctx.createGain(),dsyn=ctx.createGain();dl.delayTime.value=SPB*.75;dfb.gain.value=.32;dlp.type='lowpass';dlp.frequency.value=3500;dsend.gain.value=.16;dsyn.gain.value=0;
vocB.connect(dsend);dsend.connect(dl);dsyn.connect(dl);dl.connect(dlp);dlp.connect(dfb);dfb.connect(dl);dlp.connect(master);
const pan=(p,to)=>{const s=ctx.createStereoPanner();s.pan.value=Math.max(-1,Math.min(1,p));s.connect(to);return s;};
const env=(g,t,a,peak,dec,sus=0.0001,tail=.05,end)=>{g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(peak,t+a);g.gain.setTargetAtTime(Math.max(sus,.0001),t+a,dec);if(end!=null)g.gain.setTargetAtTime(0,end,tail);};
/* supersierra: 7 sierras desafinadas, la mitad a cada lado, con filtro que se cierra */
const DET=[-36,-22,-9,0,9,22,36];
function saw7(t,n,dur,vel,{cut=3200,cutEnd=null,cutT=null,a=.004,dec=.3,sus=.6,rel=.1,bus=synB,det=DET,w=.7,q=.8,echo=0}={}){
 const g=ctx.createGain(),sides=[-w,w].map(p=>{const lp=ctx.createBiquadFilter();lp.type='lowpass';lp.Q.value=q;lp.frequency.setValueAtTime(cut,t);if(cutEnd!=null)lp.frequency.setTargetAtTime(cutEnd,t+.002,cutT??dur/3);lp.connect(pan(p,g));return lp;});
 det.forEach((d,i)=>{const o=ctx.createOscillator(),og=ctx.createGain();o.type='sawtooth';o.frequency.value=hz(n);o.detune.value=d+(H()-.5)*4;og.gain.value=1.4/det.length;o.connect(og);og.connect(sides[i%2]);o.start(t);o.stop(t+dur+rel*6);});
 const out=ctx.createGain();g.connect(out);out.connect(bus);if(echo){const e=ctx.createGain();e.gain.value=echo;out.connect(e);e.connect(dsyn);dsyn.gain.value=1;}env(out,t,a,vel,dec,vel*sus,rel,t+dur);}
function stab(t,notes,vel){notes.forEach(n=>saw7(t,n+12,SPB*.3,vel*.09,{cut:6500,cutEnd:700,cutT:.06,dec:.08,sus:.3,rel:.04,det:[-14,0,14],w:.5}));}
function bassO(t,n,dur,vel){const lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.Q.value=5;lp.frequency.setValueAtTime(380+1500*vel,t);lp.frequency.setTargetAtTime(300,t,.05);lp.connect(g);g.connect(bassB);
 [['sawtooth',0,.5],['sawtooth',7,.4],['square',-1200,.45]].forEach(([ty,d,a])=>{const o=ctx.createOscillator(),og=ctx.createGain();o.type=ty;o.frequency.value=hz(n);o.detune.value=d;og.gain.value=a;o.connect(og);og.connect(lp);o.start(t);o.stop(t+dur+.2);});
 env(g,t,.003,.34*vel,.12,.2*vel,.02,t+dur);}
function sub(t,n,dur,vel){const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.value=hz(n);o.connect(g);g.connect(bassB);env(g,t,.02,.45*vel,1,.4*vel,.1,t+dur);o.start(t);o.stop(t+dur+.6);}
function arp(t,n,vel,p=0){const o=ctx.createOscillator(),lp=ctx.createBiquadFilter(),g=ctx.createGain();o.type='square';o.frequency.value=hz(n);lp.type='lowpass';lp.frequency.setValueAtTime(4200,t);lp.frequency.setTargetAtTime(900,t,.05);o.connect(lp);lp.connect(g);g.connect(pan(p,synB));env(g,t,.002,.035*vel,.06);o.start(t);o.stop(t+.4);}
function pad(t,notes,dur,vel,cut=1800){notes.forEach(n=>saw7(t,n+12,dur,vel*.05,{cut,a:.25,dec:1.5,sus:.85,rel:.4,w:.9}));}
/* efectos: ruido blanco sembrado */
const nb=ctx.createBuffer(1,SR*2,SR),nr=rng('ruido');{const d=nb.getChannelData(0);for(let k=0;k<d.length;k++)d[k]=nr()*2-1;}
function noise(t,dur){const s=ctx.createBufferSource();s.buffer=nb;s.loop=true;s.start(t);s.stop(t+dur+.1);return s;}
function riser(t,dur,vel=1){const s=noise(t,dur),bp=ctx.createBiquadFilter(),g=ctx.createGain();bp.type='bandpass';bp.Q.value=2.5;bp.frequency.setValueAtTime(300,t);bp.frequency.exponentialRampToValueAtTime(9000,t+dur);
 g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(.32*vel,t+dur);g.gain.setValueAtTime(0,t+dur);s.connect(bp);bp.connect(g);g.connect(pan(0,fxB));
 const o=ctx.createOscillator(),og=ctx.createGain();o.type='sawtooth';o.frequency.setValueAtTime(110,t);o.frequency.exponentialRampToValueAtTime(880,t+dur);og.gain.setValueAtTime(.0001,t);og.gain.exponentialRampToValueAtTime(.05*vel,t+dur);og.gain.setValueAtTime(0,t+dur);o.connect(og);og.connect(fxB);o.start(t);o.stop(t+dur+.05);}
function impact(t,vel=1){const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.setValueAtTime(160,t);o.frequency.exponentialRampToValueAtTime(32,t+.9);o.connect(g);g.connect(fxB);env(g,t,.003,.9*vel,.45);o.start(t);o.stop(t+2.5);
 const s=noise(t,1.5),lp=ctx.createBiquadFilter(),ng=ctx.createGain();lp.type='lowpass';lp.frequency.setValueAtTime(5000,t);lp.frequency.exponentialRampToValueAtTime(200,t+1.2);s.connect(lp);lp.connect(ng);ng.connect(fxB);env(ng,t,.002,.45*vel,.25);}
/* el derrapón: ruido en banda angosta que chilla y se tambalea */
function derrape(t,dur=1.1){const s=noise(t,dur),bp=ctx.createBiquadFilter(),g=ctx.createGain(),l=ctx.createOscillator(),lg=ctx.createGain();bp.type='bandpass';bp.Q.value=16;bp.frequency.setValueAtTime(3100,t);bp.frequency.linearRampToValueAtTime(2300,t+dur);
 l.frequency.value=9;lg.gain.value=260;l.connect(lg);lg.connect(bp.frequency);l.start(t);l.stop(t+dur);s.connect(bp);bp.connect(g);g.connect(pan(.3,fxB));g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(.55,t+.05);g.gain.setValueAtTime(.55,t+dur*.6);g.gain.linearRampToValueAtTime(0,t+dur);}
/* sidechain: cada bombo hunde los sintes y el bajo, y se recuperan antes del siguiente */
const PUMP=[...Array(49).keys()].filter(b=>!['intro','break','fin'].includes(sec(b)));
[[synB,.72],[bassB,.55]].forEach(([bus,d])=>{bus.gain.setValueAtTime(1,0);for(const b of PUMP)for(let k=0;k<4;k++){const t=tb(b,k);bus.gain.setValueAtTime(1-d,t);bus.gain.linearRampToValueAtTime(1,t+SPB*.6);}});

/* ---------- 5. La batería de consola: tramos de music.drums (kit 909) renderizados por LecturaMusica y puestos a tiempo ---------- */
const LM=window.LecturaMusica,R=LM.RITMOS;
async function bateria(bar0,bars,d,extra=0){const dr={gain:.62,kit:'tr909',drive:.22,...d};
 const q={...p0,clips:[],tempo:{...p0.tempo,bpm:BPM,meter:4},music:LM.normalize({...p0.music,on:true,gain:.75,reverb:.08,delay:0,pulse:'none',voices:[],drums:LM.drums(dr)})};
 const len=bars*BAR,buf=await LM.render(q,[],len+extra,SR),s=ctx.createBufferSource(),g=ctx.createGain();s.buffer=buf;s.connect(g);g.connect(drumB);
 const at=tb(bar0);g.gain.setValueAtTime(1,at);if(!extra){g.gain.setValueAtTime(1,at+len-.03);g.gain.linearRampToValueAtTime(0,at+len);}s.start(at);}
const q16=n=>'x'+'.'.repeat(n-1),rep=(s,n)=>s.repeat(n);
const EURO={kick:'x...x...x...x...',clap:'....x.......x...',snare:'....o.......o...',hat:'x.o.x.o.x.o.x.o.',openhat:'..x...x...x...x.'};
const ROLL16=rep('x...x...x...x...',1)+rep('x.x.x.x.x.x.x.x.',2)+'xxxxxxxxxxxxxxxx';
await bateria(1,1,{kick:'',snare:'o...o...o.o.oooo',crash:''});
await bateria(2,4,{...EURO,crash:q16(64)});
await bateria(6,4,{...EURO,crash:q16(64),tomlo:rep('.',48)+'........x.x.x.xx'});
await bateria(10,4,{kick:'x...x...x...x...',rim:'....o.......o...',hat:'..x...x...x...x.',crash:q16(64)});
await bateria(14,4,{...EURO,clap:'',hat:'..o...o...o...o.'});
await bateria(18,4,{kick:'x...x...x...x...',snare:ROLL16,hat:'o.o.o.o.o.o.o.o.',crash:q16(64)});
await bateria(22,4,{...EURO,crash:q16(64)});
await bateria(26,4,{...EURO,spray:q16(64),tomhi:rep('.',48)+'............x.xx'});
await bateria(30,4,{...EURO,crash:q16(64),cowbell:'..x...x...x...x.'});
await bateria(34,3,{hat:'....o.......o...',rim:'x..x..x.........'});
await bateria(37,1,{snare:'o.o.oooo........',kick:'x.......x.......',drive:.5});
await bateria(38,4,{...EURO,crash:q16(64),drive:.3});
await bateria(42,4,{...EURO,spray:q16(64),tomhi:rep('.',48)+'........x.x.xxxx',drive:.3});
await bateria(46,2,{...EURO,crash:q16(32)});
await bateria(48,1,{kick:'x...............',crash:'x...............'},3);

/* ---------- 6. El arreglo ---------- */
const hv=v=>v*(.92+H()*.16);
for(let bar=0;bar<CH.length;bar++){const S=sec(bar),c=chord(CH[bar]),T=s=>ts(bar,s),N=c.notes;
 const octBass=(vel=.8)=>{for(let s=0;s<16;s+=2)bassO(T(s),c.bass+(s%4===2?12:0),SPB*.45,hv(vel));};
 const stabs=(steps=[2,6,10,14],vel=1)=>steps.forEach(s=>stab(T(s),N,hv(vel)));
 const arp16=(vel=.8,oct=24)=>{const ord=[0,1,2,3,2,1,2,3];for(let s=0;s<16;s++)arp(T(s),N[ord[s%8]]+oct-12,hv(vel)*(s%4?.75:1),s%2?.35:-.35);};
 if(S==='intro'){pad(T(0),N,BAR,.8,bar?2600:900);sub(T(0),c.bass,BAR*.95,.6);if(bar===1){riser(T(0),BAR,1);}}
 if(S==='riff'||S==='riff2'){const k=(bar-(S==='riff'?2:30))%4,str=(k===3&&(bar===9||bar===33))?RIFF_A:RIFF[k];
  riff(str,bar).forEach(x=>saw7(x.t,x.n,x.d*.92,hv(.075),{cut:7000,cutEnd:2200,cutT:.12,dec:.15,sus:.55,rel:.06,echo:.35}));
  riff(str,bar).forEach(x=>saw7(x.t,x.n-12,x.d*.92,hv(.035),{cut:3000,cutEnd:900,cutT:.1,dec:.15,sus:.5,rel:.05,w:.3}));
  octBass(.85);stabs([2,6,10,14],.7);if(bar%4===3)riser(T(8),BAR/2,.5);}
 if(S==='verso'){octBass(bar<14?.6:.8);pad(T(0),N,BAR*.98,.55,1400);if(bar>=14)arp16(.7);else if(bar%2)arp16(.45);}
 if(S==='pre'){for(let s=0;s<16;s+=2)bassO(T(s),c.bass,SPB*.4,hv(.8));pad(T(0),N,BAR*.98,.9,1800+(bar-18)*900);stabs([0,6,12],.8);arp16(.6+(bar-18)*.15);if(bar===20)riser(T(0),BAR*2-SPB*.25,1.2);}
 if(S==='coro'||S==='ultimo'){octBass(.9);pad(T(0),N,BAR*.98,1,3400);stabs([2,6,10,14],.8);arp16(.8,36);
  if([22,26,38,42].includes(bar))derrape(tb(bar,.5));if(bar===29||bar===45)riser(T(8),BAR/2,.7);}
 if(S==='break'){pad(T(0),N,BAR,.9,bar===37?4000:1100);if(bar<37){sub(T(0),c.bass,BAR*.95,.8);for(let s=0;s<16;s+=4)arp(T(s),N[(s/4+bar)%4]+24,.8,(s/4)%2?.5:-.5);}
  if(bar===36)riser(T(0),BAR+SPB*2,1.3);}
 if(S==='final'){octBass(.85);pad(T(0),N,BAR*.98,1,3000);stabs([2,6,10,14],.7);arp16(.7,36);}
 if(S==='fin'){stab(T(0),N,1.6);pad(T(0),N,BAR*2,1.1,2400);sub(T(0),c.bass,BAR*1.5,1);}}
/* la voz también la dobla la supersierra en el coro, una octava abajo y bajito */
lead.filter(x=>x.coro).forEach(x=>saw7(x.t,x.note-12,x.D,.03,{cut:2600,cutEnd:1500,a:.01,dec:.3,sus:.7,rel:.06,w:.4}));
/* golpes: entradas de gancho, coros, y el FALCON PUNCH */
[2,22,30,48].forEach(b=>impact(tb(b),b===48?1.2:.8));impact(tb(37,2),1.6);impact(tb(38),.9);

/* ---------- 7. Las voces ---------- */
const lines=[...lead];
lead.filter(x=>x.coro).forEach(x=>lines.push({...x,note:x.note-12,carrier:'pulso',gain:.3,pan:.4,formant:1,vib:0}));
lead.filter(x=>x.coro).forEach(x=>lines.push({...x,note:x.note-5,carrier:'coro',gain:.2,pan:-.4,formant:1.02,vib:0}));
lead.filter(x=>x.carrier==='coro'&&x.formant<.9).forEach(x=>lines.push({...x,note:x.note-12,gain:.5,formant:.8}));
let sung=0;for(const x of lines){const r=await sing(x.syl,x.note,x.D,{carrier:x.carrier||'sierra',formant:x.formant??1.05,vib:x.vib??10});
 const s=ctx.createBufferSource(),g=ctx.createGain();s.buffer=r.buf;g.gain.value=.5*r.norm*(x.gain??1);s.connect(g);g.connect(pan(x.pan||0,vocB));s.start(Math.max(0,x.t-r.vt));sung++;}

const out=await ctx.startRendering(),L=out.getChannelData(0),Rr=out.getChannelData(1);let pk=0;for(let k=0;k<L.length;k++)pk=Math.max(pk,Math.abs(L[k]),Math.abs(Rr[k]));const g=.92/pk;
const rms=[];for(let s=0;s<Math.floor(LEN);s+=5){let a=0;const i0=s*SR,i1=Math.min(L.length,(s+5)*SR);for(let k=i0;k<i1;k++)a+=L[k]*L[k];rms.push(+(Math.sqrt(a/(i1-i0))*g).toFixed(3));}
const pcm=new Int16Array(L.length*2);for(let k=0;k<L.length;k++){pcm[k*2]=Math.max(-1,Math.min(1,L[k]*g))*32767;pcm[k*2+1]=Math.max(-1,Math.min(1,Rr[k]*g))*32767;}
const u8=new Uint8Array(pcm.buffer);let b64='';for(let k=0;k<u8.length;k+=32768)b64+=String.fromCharCode(...u8.subarray(k,k+32768));
return {b64:btoa(b64),peak:pk,rms,sung,seconds:LEN};};
