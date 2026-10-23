/* «sonidero de Final Destination (cumbiatón)» (yoshi es un vector, parte 13) — ~103 s de cumbiatón a 96 bpm, La menor; cierra «rebajada».
   Un baile sonidero en Final Destination: el narrador (vocoder de consola) grita como sonidero, con su eco de cinta, y manda saludos;
   el coro es el meme competitivo: «sin ítems, puro Fox, Final Destination… wavedash, wavedash, pa' la pista». Los personajes contestan
   con su voz del juego (cruda en los gritos y saludos, afinada en los coros: voces.py → voces_*.wav).
   El ritmo: dembow de la batería de consola (kit 808: bombo en cada tiempo, tarola en el 3·6·11·14 de cada compás), güiro sintetizado
   (largo-corto-corto), congas, bajo de cumbia (raíz y quinta), acordeón de lengüetas desafinadas (musette) y stabs a contratiempo.
   Al final, cumbia rebajada a la regiomontana: el tempo baja a 76 y todo baja tres semitonos (Fa# menor).
   Se corre dentro del visor de lectura: window.cancion(opciones) → WAV. */
'use strict';
window.cancion=async function(opts={}){
const DIR='/meleeviewer/output/Arte/2026-09-30_yoshi_es_un_vector_13_sonidero/';
const SEED='yoshi-es-un-vector-13-sonidero',BPM=96,BPM2=76,SPB=60/BPM,SPB2=60/BPM2,BAR=SPB*4,BAR2=SPB2*4,T0=.35,SR=44100,LEN=107,NBAR=40,REB=36;
/* mapa de tempo: del compás 36 en adelante, rebajada */
const tb=(bar,beat=0)=>bar<REB?T0+(bar*4+beat)*SPB:T0+REB*BAR+((bar-REB)*4+beat)*SPB2;
const spbDe=bar=>bar<REB?SPB:SPB2,ts=(bar,step)=>tb(bar,step/4);
function hash(s){let h=1779033703^s.length;for(let i=0;i<s.length;i++){h=Math.imul(h^s.charCodeAt(i),3432918353);h=h<<13|h>>>19;}h=Math.imul(h^h>>>16,2246822507);h=Math.imul(h^h>>>13,3266489909);return (h^h>>>16)>>>0;}
function rng(tag){let a=hash(SEED+':'+tag);return ()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}
const hz=n=>440*2**((n-69)/12);

/* ---------- 1. El sonidero: el vocoder de consola, parchado en una copia ---------- */
if(!window.CantaMusica){let src=await (await fetch('/consola/consola/static/lectura/musica.js')).text();
 const patch=(a,b)=>{if(!src.includes(a))throw Error('no encontré en musica.js: '+a);src=src.split(a).join(b);};
 patch('window.LecturaMusica=','window.CantaMusica=');
 patch('midi:midi(m,m.vozOctave,deg)+bend};','midi:(v.canto??(midi(m,m.vozOctave,deg)+bend))};');
 patch('f.frequency.setTargetAtTime(F[k],t0,.012)','f.frequency.setTargetAtTime(F[k]*(window.CANTA_FORMANT||1),t0,.012)');
 patch('nodes.push(o);oscs.push(o);});','nodes.push(o);oscs.push(o);if(window.CANTA_VIB&&ev.dur>.3){const l=ctx.createOscillator(),lg=ctx.createGain();l.frequency.value=5.4;lg.gain.setValueAtTime(0,at);lg.gain.setValueAtTime(0,at+.2);lg.gain.linearRampToValueAtTime(window.CANTA_VIB,at+.55);l.connect(lg);lg.connect(o.detune);l.start(at);l.stop(at+ev.dur+.6);}});');
 const s=document.createElement('script');s.textContent=src;document.head.append(s);}
const CM=window.CantaMusica,p0=Lectura.snapshot().piece;
const base={on:false,root:'C',scale:'major',gain:.8,reverb:.05,delay:0,delayTime:.3,pulse:'none',density:0,vozOctave:3,vozRate:1,vozCarrier:'sierra',vozMelody:'monotono',vozGain:1,instruments:[]};
function stretch(syl,n){const s=syl.toLowerCase(),idx=Math.max(...[...'aeiouáéíóú'].map(c=>s.lastIndexOf(c)));if(idx<0)return s.includes('y')?s.replace('y','i'.repeat(n)):s;return s.slice(0,idx+1)+s[idx].repeat(n-1)+s.slice(idx+1);}
async function sing(syl,note,D,{carrier='sierra',formant=1.02,vib=8}={}){
 const piece={...p0,seed:SEED,music:CM.normalize({...base,vozCarrier:carrier,voices:[{instrument:'none',octave:4,gain:.7,pan:0,entry:'none',words:false,gesture:false}]})};
 let v,ev;for(let n=1;n<=48;n++){v={i:0,key:'s',born:0,duration:D/.95,text:stretch(syl,n),effect:'fade',hold:0,speak:'vocoder',canto:note};ev=CM.speechEvents(piece,v)[0];if(ev.dur>=D*.97)break;}
 window.CANTA_FORMANT=formant;window.CANTA_VIB=vib;
 const buf=await CM.render(piece,[v],ev.dur+.6,SR),vt=(ev.steps.find(s=>s.v)||{t:0}).t;
 let pk=0;for(let c=0;c<2;c++){const d=buf.getChannelData(c);for(let k=0;k<d.length;k++)pk=Math.max(pk,Math.abs(d[k]));}
 return {buf,vt,norm:pk>0?1/pk:1};}

/* ---------- 2. La letra (sílaba:nota:tiempos; un compás por renglón; voces.py y video.html la leen de aquí) ---------- */
const NOTE={C:0,D:2,E:4,F:5,G:7,A:9,B:11};
const nm=s=>{const m=/^([A-G])(b|#)?(-?\d)$/.exec(s);if(!m)throw Error('nota: '+s);return 12*(+m[3]+1)+NOTE[m[1]]+(m[2]==='b'?-1:m[2]==='#'?1:0);};
function score(str,bar,tr=0,o={}){const out=[];let beat=0;const spb=spbDe(bar);for(const tok of str.trim().split(/\s+/)){const [a,b,c]=tok.split(':');if(a==='-'){beat+=+b;continue;}out.push({syl:a,note:nm(b)+tr,t:tb(bar,beat),D:+c*spb-.03,...o});beat+=+c;}return out;}
const NL=String.fromCharCode(10);
function scoreBars(str,bar0,tr=0,o={}){return str.trim().split(NL).flatMap((l,k)=>score(l,bar0+k,tr,o));}
const INTRO=`so:A4:.5 ni:C5:.5 do:E5:1 me:A5:.5 li:G5:1.5
 des:E5:.5 de:E5:.5 fi:G5:.5 nal:G5:.5 des:A5:.5 ti:G5:.5 nei:E5:.5 shon:C5:.5`;
const VERSO=`lle:A4:.5 go:C5:.5 la:E5:.5 ban:E5:.5 da:D5:.5 com:C5:.5 ple:D5:.5 ta:E5:.5
 al:F5:.5 es:F5:.5 ce:E5:.5 na:D5:.5 rio:E5:1 sin:D5:.5 fin:A4:.5
 sin:G4:.5 pla:B4:.5 ta:D5:.5 for:D5:.5 mas:D5:.5 sin:B4:.5 na:D5:.5 da:G5:.5
 pu:G5:.5 ro:E5:.5 pi:G5:.5 so:E5:.5 pa:C5:.5 bai:D5:.5 lar:E5:1
 kir:A4:.5 by:C5:.5 se:E5:.5 tra:E5:.5 go:D5:.5 la:C5:.5 bo:D5:.5 ci:E5:.5
 na:F5:1 y:E5:.5 a:D5:.5 ho:F5:.5 ra:E5:.5 -:1
 sue:B4:.5 na:D5:.5 con:E5:.5 to:E5:.5 doel:D5:.5 ba:B4:.5 jo:G#4:1
 -:4`;
const PRE=`yel:A4:.5 so:C5:.5 ni:F5:.5 de:F5:.5 ro:E5:.5 gri:F5:.5 ta:A5:1
 a:B4:.5 to:D5:.5 dos:E5:1 -:2`;
const CORO=`sin:A5:.5 i:A5:.5 tems:G5:1 pu:E5:.5 ro:E5:.5 fox:A5:1
 fi:F5:.5 nal:F5:.5 des:A5:.5 ti:G5:.5 nei:F5:.5 shon:D5:1.5
 weiv:G5:.5 dash:B5:1 weiv:G5:.5 dash:D6:1 -:1
 pa:E5:.5 la:E5:.5 pis:G5:.5 ta:C6:1.5 -:1
 sin:A5:.5 i:A5:.5 tems:G5:1 pu:E5:.5 ro:E5:.5 fox:A5:1
 fi:F5:.5 nal:F5:.5 des:A5:.5 ti:G5:.5 nei:F5:.5 shon:D5:1.5
 yel:E5:.5 que:G#5:.5 pier:B5:.5 da:B5:.5 pa:D6:.5 ga:B5:.5 las:G#5:.5 ca:B5:.5
 gua:C6:.5 mas:A5:2.5 -:1`;
const SALUDOS=`sa:A4:.5 lu:C5:.5 dos:E5:1 a:E5:.5 kir:A5:.5 by:G5:1
 y:E5:.5 su:E5:.5 fa:F5:.5 mi:E5:.5 lia:D5:2
 has:B4:.5 ta:D5:.5 yo:E5:.5 shis:E5:.5 ai:G#5:.5 land:B5:1.5
 pu:A5:.5 ra:A5:.5 cum:G5:.5 bia:E5:1.5 -:1`;
const VERSO2=`fal:A4:.5 con:C5:.5 no:E5:.5 tie:E5:.5 ne:D5:.5 pa:C5:.5 re:D5:.5 ja:E5:.5
 pe:F5:.5 roe:F5:.5 cho:E5:.5 su:D5:.5 fal:F5:.5 con:E5:.5 panch:D5:1
 yel:E5:.5 pi:E5:.5 so:G#5:.5 sea:B5:.5 lum:B5:.5 bro:G#5:.5 -:1
 -:4`;
const REBAJADA=`re:C#4:1 ba:B3:1 ja:A3:1 da:F#3:1
 -:4
 pu:F#3:1 ra:F#3:1 cum:E3:1 bia:C#3:1`;
const SECC=[['intro',0,2],['verso',2,10],['pre',10,12],['coro',12,20],['saludos',20,24],['verso2',24,28],['coro2',28,36],['rebajada',36,40]];
/* los gritos del sonidero llevan eco de cinta */
const lead=[...scoreBars(INTRO,0,0,{eco:1}),...scoreBars(VERSO,2),...scoreBars(PRE,10),...scoreBars(CORO,12,0,{coro:1}),...scoreBars(SALUDOS,20,0,{eco:1}),...scoreBars(VERSO2,24),...scoreBars(CORO,28,0,{coro:1}),...scoreBars(REBAJADA,36,0,{formant:.92,eco:1})];

/* ---------- 3. La armonía (la rebajada ya viene tres semitonos abajo) ---------- */
const CICLO=['Am','Dm','G','C','Am','Dm','E7','Am'];
const CH=[...Array(NBAR).keys()].map(b=>b<2?['Am','E7'][b]:b<10?CICLO[b-2]:b<12?['F','E7'][b-10]:b<20?CICLO[b-12]:b<24?['Am','Dm','E7','Am'][b-20]:b<28?['Am','Dm','E7','Am'][b-24]:b<36?CICLO[b-28]:['F#m','Bm','C#7','F#m'][b-36]);
const PC={C:0,'C#':1,D:2,'D#':3,E:4,F:5,'F#':6,G:7,'G#':8,A:9,'A#':10,Bb:10,B:11};
const QUAL={'':[0,4,7,12],m:[0,3,7,12],7:[0,4,7,10]};
function chord(sym){const m=/^([A-G][b#]?)(.*)$/.exec(sym),root=PC[m[1]],iv=QUAL[m[2]];if(!iv)throw Error('acorde: '+sym);
 let notes=iv.map(i=>57+root+i);while(notes[0]>62)notes=notes.map(n=>n-12);let b=36+root;if(b>42)b-=12;return {notes,bass:b,root};}
const sec=b=>(SECC.find(([,a,z])=>b>=a&&b<z)||['rebajada'])[0];

/* ---------- 4. La mezcla ---------- */
const ctx=new OfflineAudioContext(2,Math.ceil(LEN*SR),SR),H=rng('humano');
const master=ctx.createGain(),comp=ctx.createDynamicsCompressor();master.gain.value=.8;comp.threshold.value=-14;comp.ratio.value=3;comp.attack.value=.008;comp.release.value=.15;master.connect(comp);comp.connect(ctx.destination);
const mk=(v,to=master)=>{const g=ctx.createGain();g.gain.value=v;g.connect(to);return g;};
const inst=mk(opts.inst??.65),vocB=mk(opts.voc??2),vozB=mk(opts.voces??1.2),drumB=mk(opts.drums??.95),fxB=mk(opts.fx??.5);
const verb=ctx.createConvolver(),vr=rng('reverb'),ir=ctx.createBuffer(2,SR*2.5,SR);for(let c=0;c<2;c++){const d=ir.getChannelData(c);for(let k=0;k<d.length;k++)d[k]=(vr()*2-1)*Math.exp(-k/SR*2.8)*(k<SR*.01?k/(SR*.01):1);}verb.buffer=ir;
const verbG=ctx.createGain();verbG.gain.value=.4;verb.connect(verbG);verbG.connect(master);
const send=(from,g)=>{const s=ctx.createGain();s.gain.value=g;from.connect(s);s.connect(verb);};send(inst,.15);send(vocB,.14);send(vozB,.25);send(fxB,.5);
/* eco de sonidero: cinta con mucha realimentación, sin graves, que se va oscureciendo */
const ecoIn=ctx.createGain(),ecoD=ctx.createDelay(2),ecoFb=ctx.createGain(),ecoHp=ctx.createBiquadFilter(),ecoLp=ctx.createBiquadFilter(),ecoOut=ctx.createGain();
ecoD.delayTime.value=SPB*.75;ecoFb.gain.value=.58;ecoHp.type='highpass';ecoHp.frequency.value=500;ecoLp.type='lowpass';ecoLp.frequency.value=3000;ecoOut.gain.value=.7;
ecoIn.connect(ecoD);ecoD.connect(ecoHp);ecoHp.connect(ecoLp);ecoLp.connect(ecoFb);ecoFb.connect(ecoD);ecoLp.connect(ecoOut);ecoOut.connect(master);
const pan=(p,to)=>{const s=ctx.createStereoPanner();s.pan.value=Math.max(-1,Math.min(1,p));s.connect(to);return s;};
const env=(g,t,a,peak,dec,sus=0.0001,tail=.05,end)=>{g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(peak,t+a);g.gain.setTargetAtTime(Math.max(sus,.0001),t+a,dec);if(end!=null)g.gain.setTargetAtTime(0,end,tail);};
/* el bombo hunde un poquito al bajo y al acordeón (respira como reggaetón) */
const pumpB=mk(1,inst);pumpB.disconnect();pumpB.connect(inst);
/* acordeón: dos lengüetas por nota (una 12 cents arriba = musette), cuadrada + sierra filtradas, con su fuelle */
function acordeon(t,n,dur,vel,p=0,bus=pumpB){const out=pan(p,bus),lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.frequency.value=2800;lp.Q.value=.7;lp.connect(g);g.connect(out);
 [[0,'square',.5],[13,'sawtooth',.4],[-1200,'square',.25]].forEach(([d,ty,a])=>{const o=ctx.createOscillator(),og=ctx.createGain();o.type=ty;o.frequency.value=hz(n);o.detune.value=d;og.gain.value=a;o.connect(og);og.connect(lp);o.start(t);o.stop(t+dur+.15);});
 env(g,t,.012,.035*vel,.2,.028*vel,.04,t+dur);}
function bajo(t,n,dur,vel){const lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.frequency.setValueAtTime(900,t);lp.frequency.setTargetAtTime(300,t,.08);lp.connect(g);g.connect(pumpB);
 [['sine',0,1],['triangle',0,.5],['sawtooth',-1200,.12]].forEach(([ty,d,a])=>{const o=ctx.createOscillator(),og=ctx.createGain();o.type=ty;o.frequency.value=hz(n);o.detune.value=d;og.gain.value=a;o.connect(og);og.connect(lp);o.start(t);o.stop(t+dur+.2);});
 env(g,t,.006,.5*vel,.25,.32*vel,.04,t+dur);}
const nb=ctx.createBuffer(1,SR*2,SR),nr=rng('ruido');{const d=nb.getChannelData(0);for(let k=0;k<d.length;k++)d[k]=nr()*2-1;}
/* güiro: ruido en banda, raspado (modulado a ~70 Hz) */
function guiro(t,dur,vel,p=.3){const s=ctx.createBufferSource(),bp=ctx.createBiquadFilter(),g=ctx.createGain(),am=ctx.createGain(),l=ctx.createOscillator(),lg=ctx.createGain();s.buffer=nb;s.loop=true;bp.type='bandpass';bp.frequency.value=3800;bp.Q.value=1.6;
 l.type='sawtooth';l.frequency.value=70;lg.gain.value=.5;am.gain.value=.5;l.connect(lg);lg.connect(am.gain);s.connect(bp);bp.connect(am);am.connect(g);g.connect(pan(p,inst));env(g,t,.01,.22*vel,dur*.6,.0001,.02,t+dur);s.start(t,(t*7)%1.5);s.stop(t+dur+.05);l.start(t);l.stop(t+dur+.05);}
function conga(t,n,vel,p=-.3,slap=false){const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.setValueAtTime(hz(n)*1.5,t);o.frequency.exponentialRampToValueAtTime(hz(n),t+.03);o.connect(g);g.connect(pan(p,inst));env(g,t,.002,.32*vel,slap?.05:.13);o.start(t);o.stop(t+.5);
 if(slap){const s=ctx.createBufferSource(),hp=ctx.createBiquadFilter(),sg=ctx.createGain();s.buffer=nb;hp.type='highpass';hp.frequency.value=1800;s.connect(hp);hp.connect(sg);sg.connect(pan(p,inst));env(sg,t,.001,.18*vel,.025);s.start(t,.3);s.stop(t+.1);}}
function campana(t,vel,p=.4){[[587,1],[845,.6]].forEach(([f,a])=>{const o=ctx.createOscillator(),bp=ctx.createBiquadFilter(),g=ctx.createGain();o.type='square';o.frequency.value=f;bp.type='bandpass';bp.frequency.value=f*1.4;bp.Q.value=3;o.connect(bp);bp.connect(g);g.connect(pan(p,inst));env(g,t,.001,.05*vel*a,.07);o.start(t);o.stop(t+.4);});}
function riser(t,dur,vel=1){const s=ctx.createBufferSource(),bp=ctx.createBiquadFilter(),g=ctx.createGain();s.buffer=nb;s.loop=true;bp.type='bandpass';bp.Q.value=2;bp.frequency.setValueAtTime(400,t);bp.frequency.exponentialRampToValueAtTime(8000,t+dur);
 g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(.25*vel,t+dur);g.gain.setValueAtTime(0,t+dur);s.connect(bp);bp.connect(g);g.connect(fxB);s.start(t);s.stop(t+dur+.05);}
/* sirena de sonidero (la que suena en todos los bailes) */
function sirena(t,dur){const o=ctx.createOscillator(),l=ctx.createOscillator(),lg=ctx.createGain(),g=ctx.createGain();o.type='square';o.frequency.value=900;l.frequency.value=3;lg.gain.value=250;l.connect(lg);lg.connect(o.frequency);o.connect(g);g.connect(ecoIn);g.connect(pan(.2,fxB));env(g,t,.02,.035,dur,.03,.1,t+dur);[o,l].forEach(x=>{x.start(t);x.stop(t+dur+.3);});}
/* bombeo: cada bombo del dembow hunde 40 % y regresa */
pumpB.gain.setValueAtTime(1,0);for(let b=2;b<NBAR;b++){if(sec(b)==='saludos'&&b<23)continue;for(let k=0;k<4;k++){const t=tb(b,k);pumpB.gain.setValueAtTime(.6,t);pumpB.gain.linearRampToValueAtTime(1,t+spbDe(b)*.6);}}

/* ---------- 5. Las voces de Melee (voces.py): crudas en gritos y saludos, afinadas en el coro ---------- */
for(const [nombre,p,d] of [['voces_coro.wav',-.4,0],['voces_coro.wav',.4,.012],['voces_gritos.wav',0,0]]){const ab=await (await fetch(DIR+nombre)).arrayBuffer(),b=await ctx.decodeAudioData(ab),s=ctx.createBufferSource();s.buffer=b;s.connect(pan(p,vozB));if(nombre==='voces_gritos.wav'){const e=ctx.createGain();e.gain.value=.25;s.connect(e);e.connect(ecoIn);}s.start(d);}

/* ---------- 6. La batería de consola: dembow (kit 808); la rebajada con su propio tempo ---------- */
const LM=window.LecturaMusica;
async function bateria(bar0,bars,d,extra=0){const reb=bar0>=REB,dr={gain:.6,kit:'tr808',drive:.18,...d};
 const q={...p0,clips:[],tempo:{...p0.tempo,bpm:reb?BPM2:BPM,meter:4},music:LM.normalize({...p0.music,on:true,gain:.75,reverb:.06,delay:0,pulse:'none',voices:[],drums:LM.drums(dr)})};
 const len=bars*(reb?BAR2:BAR),buf=await LM.render(q,[],len+extra,SR),s=ctx.createBufferSource(),g=ctx.createGain();s.buffer=buf;if(reb)s.detune.value=0;s.connect(g);g.connect(drumB);
 const at=tb(bar0);g.gain.setValueAtTime(1,at);if(!extra){g.gain.setValueAtTime(1,at+len-.03);g.gain.linearRampToValueAtTime(0,at+len);}s.start(at);}
const q16=n=>'x'+'.'.repeat(n-1),rep=(s,n)=>s.repeat(n);
const DEMBOW={kick:'x...x...x...x...',snare:'...x..x....x..x.',hat:'x.x.x.x.x.x.x.x.'};
await bateria(1,1,{snare:'....x...x.x.xxxx',kick:'x.......x.......'});
await bateria(2,4,{kick:'x...x...x...x...',rim:'...x..x....x..x.',crash:q16(64)});
await bateria(6,4,{...DEMBOW,hat:'..x...x...x...x.'});
await bateria(10,2,{...DEMBOW,snare:rep('...x..x....x..x.',1)+'x.x.x.x.xxxxxxxx'});
await bateria(12,4,{...DEMBOW,clap:'...x..x....x..x.',crash:q16(64)});
await bateria(16,4,{...DEMBOW,clap:'...x..x....x..x.',tomhi:rep('.',48)+'........x.x.xxxx'});
await bateria(20,3,{rim:'...x..x....x..x.'});
await bateria(23,1,{snare:'x.x.x.x.xxxxxxxx',kick:'x...x...x...x...'});
await bateria(24,4,{...DEMBOW,crash:q16(64)});
await bateria(28,4,{...DEMBOW,clap:'...x..x....x..x.',crash:q16(64),drive:.3});
await bateria(32,4,{...DEMBOW,clap:'...x..x....x..x.',tomhi:rep('.',48)+'....x.x.x.xxxxxx',drive:.3});
await bateria(36,4,{kick:'x...x...x...x...',snare:'...x..x....x..x.',hat:'x...x...x...x...',decay:1.6,tune:-3},4);

/* ---------- 7. El arreglo ---------- */
const hv=v=>v*(.9+H()*.2);
/* el lick de acordeón: semicorcheas por las notas del acorde con su vecina de abajo */
const LICK=[[0,3],[1,2],[2,3],[3,2],[2,2],[1,2],[0,2]];
for(let bar=0;bar<NBAR;bar++){const S=sec(bar),c=chord(CH[bar]),N=c.notes,T=s=>ts(bar,s),sp=spbDe(bar),reb=S==='rebajada';
 const stabs=(vel=1)=>[2,6,10,14].forEach(s=>N.forEach((n,k)=>acordeon(T(s),n+12,sp*.22,hv(vel*.8),(k-1.5)*.3)));
 const cumbiaBajo=(vel=1)=>{bajo(T(0),c.bass,sp*1.4,vel);bajo(T(8),c.bass+7,sp*1.4,vel*.9);bajo(T(14),c.bass+12,sp*.4,vel*.7);};
 const guiros=(vel=1)=>[0,2,3,4,6,7,8,10,11,12,14,15].forEach(s=>guiro(T(s),s%2?sp*.18:sp*.38,hv(vel)*(s%4===0?1:.7)));
 const congas=(vel=1)=>{conga(T(2),62,vel,-.3,true);conga(T(7),55,vel*.8,-.2);conga(T(10),62,vel,-.3,true);conga(T(14),55,vel*.8,-.2);conga(T(15),55,vel*.6,-.2);};
 const lick=(vel=1,oct=12)=>{let s=0;for(const [k,d] of LICK){acordeon(T(s),N[k%4]+oct+(k===1&&s>6?-1:0),d*sp/4*.9,hv(vel),.25);s+=d;}};
 if(S==='intro'){lick(1);if(bar===0)sirena(T(0),sp*3);if(bar===1){riser(T(0),BAR,.8);guiros(.6);}}
 if(S==='verso'){cumbiaBajo(.9);guiros(bar<6?.6:.9);stabs(.8);if(bar>=6)congas(.8);if(bar===9)lick(1);}
 if(S==='pre'){cumbiaBajo(1);guiros(1);stabs(1);congas(1);if(bar===11)riser(T(0),BAR,1);}
 if(S==='coro'||S==='coro2'){cumbiaBajo(1.05);guiros(1);stabs(1);congas(1);[0,4,8,12].forEach(s=>campana(T(s+2),.9));if(bar%2)lick(1.1,24);if(bar===19||bar===35)riser(T(8),BAR/2,.8);if((bar-12)%8===0||(bar-28)%8===0)sirena(T(0),sp*2);}
 if(S==='saludos'){bajo(T(0),c.bass,sp*3.5,.8);N.forEach((n,k)=>acordeon(T(0),n+12,BAR*.95,.7,(k-1.5)*.3));guiros(.5);if(bar===20)sirena(T(0),sp*3);}
 if(S==='verso2'){cumbiaBajo(1);guiros(1);stabs(.9);congas(.9);if(bar===27)lick(1.1,24);}
 if(reb){cumbiaBajo(1);guiros(.7);stabs(.8);congas(.7);if(bar===39)N.forEach((n,k)=>acordeon(T(0),n+12,BAR*1.5,.8,(k-1.5)*.3));}}

/* ---------- 8. El sonidero ---------- */
let sung=0;for(const x of lead){const r=await sing(x.syl,x.note,x.D,{formant:x.formant??1.02});
 const s=ctx.createBufferSource(),g=ctx.createGain();s.buffer=r.buf;g.gain.value=.5*r.norm*(x.gain??1);s.connect(g);g.connect(pan(0,vocB));if(x.eco){const e=ctx.createGain();e.gain.value=.55*r.norm;s.connect(e);e.connect(ecoIn);}s.start(Math.max(0,x.t-r.vt));sung++;}

const out=await ctx.startRendering(),L=out.getChannelData(0),Rr=out.getChannelData(1);let pk=0;for(let k=0;k<L.length;k++)pk=Math.max(pk,Math.abs(L[k]),Math.abs(Rr[k]));const g=.92/pk;
const rms=[];for(let s=0;s<Math.floor(LEN);s+=5){let a=0;const i0=s*SR,i1=Math.min(L.length,(s+5)*SR);for(let k=i0;k<i1;k++)a+=L[k]*L[k];rms.push(+(Math.sqrt(a/(i1-i0))*g).toFixed(3));}
const pcm=new Int16Array(L.length*2);for(let k=0;k<L.length;k++){pcm[k*2]=Math.max(-1,Math.min(1,L[k]*g))*32767;pcm[k*2+1]=Math.max(-1,Math.min(1,Rr[k]*g))*32767;}
const u8=new Uint8Array(pcm.buffer);let b64='';for(let k=0;k<u8.length;k+=32768)b64+=String.fromCharCode(...u8.subarray(k,k+32768));
return {b64:btoa(b64),peak:pk,rms,sung,seconds:LEN};};
