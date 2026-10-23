/* «¿una más?» (yoshi es un vector, parte 15) — ~84 s de pop de videojuego a 124 bpm, Sol mayor. Una canción sobre jugar.
   Nadie nos obliga a jugar y aun así venimos cada tarde: cuatro controles, un sillón, el mundo se detiene. El juego es más viejo que la
   cultura (Huizinga, «Homo ludens»): los perros ya jugaban; tiene reglas que nadie escribió y un círculo donde todo vale. ¿Una más?
   Cuatro jugadores de una partida de verdad en Battlefield: Mario, Luigi, Peach y Bowser. Cada uno tiene su LEITMOTIV (Mario brinca
   hacia arriba, Luigi baja tímido, Peach flota, Bowser gruñe abajo) que aparece transformado (inversión, retrógrado, aumentación); en
   el puente suenan los cuatro a la vez. El coro de cuerdas y el de Peach y Luigi salen de una ARMONIZACIÓN A CUATRO VOCES CON REGLAS
   (armonia.py: sin quintas ni octavas paralelas, menor movimiento). Mario y Bowser no tienen voces afinables: gritan crudos.
   La banda: bajo de onda cuadrada, pitidos de menú del juego como instrumento (main.ssm, afinados por el censo), Rhodes, guitarra
   Karplus-Strong funky, cuerdas, y la batería de consola. Voces y motivos: voces.py → voces_*.wav + partitura.json. */
'use strict';
window.cancion=async function(opts={}){
const DIR='/meleeviewer/output/Arte/2026-10-03_yoshi_es_un_vector_15_una_mas/';
const SEED='yoshi-es-un-vector-15-una-mas',BPM=124,SPB=60/BPM,BAR=SPB*4,T0=.35,SR=44100,LEN=86,NBAR=42;
const tb=(bar,beat=0)=>T0+(bar*4+beat)*SPB,ts=(bar,step)=>tb(bar,step/4);
function hash(s){let h=1779033703^s.length;for(let i=0;i<s.length;i++){h=Math.imul(h^s.charCodeAt(i),3432918353);h=h<<13|h>>>19;}h=Math.imul(h^h>>>16,2246822507);h=Math.imul(h^h>>>13,3266489909);return (h^h>>>16)>>>0;}
function rng(tag){let a=hash(SEED+':'+tag);return ()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}
const hz=n=>440*2**((n-69)/12);

/* ---------- 1. El narrador ---------- */
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
async function sing(syl,note,D,{carrier='sierra',formant=1.03,vib=10}={}){
 const piece={...p0,seed:SEED,music:CM.normalize({...base,vozCarrier:carrier,voices:[{instrument:'none',octave:4,gain:.7,pan:0,entry:'none',words:false,gesture:false}]})};
 let v,ev;for(let n=1;n<=48;n++){v={i:0,key:'s',born:0,duration:D/.95,text:stretch(syl,n),effect:'fade',hold:0,speak:'vocoder',canto:note};ev=CM.speechEvents(piece,v)[0];if(ev.dur>=D*.97)break;}
 window.CANTA_FORMANT=formant;window.CANTA_VIB=vib;
 const buf=await CM.render(piece,[v],ev.dur+.6,SR),vt=(ev.steps.find(s=>s.v)||{t:0}).t;
 let pk=0;for(let c=0;c<2;c++){const d=buf.getChannelData(c);for(let k=0;k<d.length;k++)pk=Math.max(pk,Math.abs(d[k]));}
 return {buf,vt,norm:pk>0?1/pk:1};}

/* ---------- 2. La letra (sílaba:nota:tiempos; un compás por renglón; voces.py y video.html la leen de aquí) ---------- */
const NOTE={C:0,D:2,E:4,F:5,G:7,A:9,B:11};
const nm=s=>{const m=/^([A-G])(b|#)?(-?\d)$/.exec(s);if(!m)throw Error('nota: '+s);return 12*(+m[3]+1)+NOTE[m[1]]+(m[2]==='b'?-1:m[2]==='#'?1:0);};
function score(str,bar,tr=0,o={}){const out=[];let beat=0;for(const tok of str.trim().split(/\s+/)){const [a,b,c]=tok.split(':');if(a==='-'){beat+=+b;continue;}out.push({syl:a,note:nm(b)+tr,t:tb(bar,beat),D:+c*SPB-.03,...o});beat+=+c;}return out;}
const NL=String.fromCharCode(10);
function scoreBars(str,bar0,tr=0,o={}){return str.trim().split(NL).flatMap((l,k)=>score(l,bar0+k,tr,o));}
const INTRO=`pre:G4:.5 sio:B4:.5 na:D5:1 start:G5:2`;
const VERSO=`na:B4:.5 die:B4:.5 nos:D5:.5 o:D5:.5 bli:E5:.5 ga:D5:.5 a:B4:.5 ju:D5:.5
 gar:E5:2 -:2
 yaun:C5:.5 a:E5:.5 si:G5:.5 ve:G5:.5 ni:A5:.5 mos:G5:.5 ca:E5:.5 da:D5:.5
 tar:F#5:1 de:D5:1 -:2
 cua:B4:.5 tro:B4:.5 con:D5:.5 tro:D5:.5 les:G5:1 un:F#5:.5 si:E5:.5
 llon:E5:2 -:2
 el:E5:.5 mun:G5:.5 do:G5:.5 se:A5:.5 de:G5:.5 tie:E5:1 ne:D5:.5
 -:4`;
const PRE=`e:G4:.5 li:B4:.5 ge:D5:.5 tu:D5:.5 per:E5:.5 so:F#5:.5 na:G5:.5 je:A5:.5
 -:4`;
const CORO=`u:D5:.5 na:G5:.5 mas:B5:2 -:1
 u:D5:.5 na:F#5:.5 mas:A5:2 -:1
 el:G5:.5 que:G5:.5 pier:B5:.5 de:A5:.5 pa:G5:.5 sael:E5:.5 con:G5:.5 trol:B5:.5
 -:4
 u:D5:.5 na:G5:.5 mas:B5:2 -:1
 na:F#5:.5 die:A5:.5 ga:A5:.5 na:B5:.5 pa:A5:.5 ra:F#5:.5 siem:D5:.5 pre:E5:.5
 ge:E5:1 ge:G5:1 -:2
 u:F#5:.5 na:A5:.5 mas:D6:2 -:1`;
const VERSO2=`el:B4:.5 jue:B4:.5 goes:D5:.5 mas:D5:.5 vie:E5:.5 jo:D5:.5 que:B4:.5 la:D5:.5
 cul:E5:.5 tu:G5:.5 ra:E5:1 -:2
 los:C5:.5 pe:E5:.5 rros:G5:.5 ya:G5:.5 ju:A5:.5 ga:G5:.5 ban:E5:1
 an:F#5:.5 tes:D5:1.5 -:2
 tie:B4:.5 ne:B4:.5 re:D5:.5 glas:D5:.5 que:G5:.5 na:F#5:.5 dies:E5:.5 cri:D5:.5
 bio:E5:2 -:2
 yun:E5:.5 cir:G5:.5 cu:G5:.5 lo:A5:.5 don:G5:.5 de:E5:.5 to:D5:.5 do:C5:.5
 va:F#5:1 le:D5:1 -:2`;
const PUENTE=`bow:E5:.5 ser:E5:.5 ha:G5:.5 ce:G5:.5 tram:B5:1 pa:A5:1
 lui:C5:.5 gi:E5:.5 ga:G5:.5 na:G5:.5 sin:A5:.5 que:G5:.5 rer:E5:1
 peach:D5:1 flo:G5:.5 ta:G5:.5 ma:B5:.5 rio:A5:.5 di:G5:.5 ce:F#5:.5
 o:A5:1 tra:D6:2 -:1`;
const FINAL=`geim:G5:2 -:2
 u:D5:.5 na:G5:.5 mas:B5:3`;
const SECC=[['intro',0,2],['verso',2,10],['pre',10,12],['coro',12,20],['verso2',20,28],['puente',28,32],['coro2',32,40],['final',40,42]];
const lead=[...score(INTRO,1),...scoreBars(VERSO,2),...scoreBars(PRE,10),...scoreBars(CORO,12,0,{coro:1}),...scoreBars(VERSO2,20),...scoreBars(PUENTE,28),...scoreBars(CORO,32,0,{coro:1}),...scoreBars(FINAL,40,0,{coro:1})];

/* ---------- 3. La armonía (voces.py la armoniza a cuatro voces) ---------- */
const CH=['G','D', 'G','Em','C','D','G','Em','C','D', 'C','D', 'G','D','Em','C','G','D','C','D', 'G','Em','C','D','G','Em','C','D', 'Em','C','G','D', 'G','D','Em','C','G','D','C','D', 'G','G'];
const PC={C:0,D:2,E:4,F:5,G:7,A:9,B:11};
function chord(sym){const m=/^([A-G])(m?)$/.exec(sym),root=PC[m[1]],iv=m[2]?[0,3,7,10]:[0,4,7,11];let notes=iv.map(i=>57+root+i);while(notes[0]>62)notes=notes.map(n=>n-12);let b=36+root;if(b>42)b-=12;return {notes,bass:b};}
const sec=b=>(SECC.find(([,a,z])=>b>=a&&b<z)||['final'])[0];
const P=await (await fetch(DIR+'partitura.json')).json();

/* ---------- 4. La mezcla ---------- */
const ctx=new OfflineAudioContext(2,Math.ceil(LEN*SR),SR),H=rng('humano');
const master=ctx.createGain(),comp=ctx.createDynamicsCompressor();master.gain.value=.8;comp.threshold.value=-14;comp.ratio.value=2.8;comp.attack.value=.01;comp.release.value=.15;master.connect(comp);comp.connect(ctx.destination);
const mk=(v,to=master)=>{const g=ctx.createGain();g.gain.value=v;g.connect(to);return g;};
const inst=mk(opts.inst??.65),vocB=mk(opts.voc??2),vozB=mk(opts.voces??1.15),drumB=mk(opts.drums??.9),fxB=mk(opts.fx??.5),motB=mk(opts.motivos??.9);
/* que se entienda: la banda se agacha ~3 dB mientras canta el narrador */
[[inst,opts.inst??.65,.47]].forEach(([bus,alto,bajo])=>{bus.gain.setValueAtTime(alto,0);for(const x of lead){bus.gain.setTargetAtTime(bajo,x.t-.05,.03);bus.gain.setTargetAtTime(alto,x.t+x.D+.05,.12);}});
const verb=ctx.createConvolver(),vr=rng('reverb'),ir=ctx.createBuffer(2,SR*2.5,SR);for(let c=0;c<2;c++){const d=ir.getChannelData(c);for(let k=0;k<d.length;k++)d[k]=(vr()*2-1)*Math.exp(-k/SR*2.6)*(k<SR*.01?k/(SR*.01):1);}verb.buffer=ir;
const verbG=ctx.createGain();verbG.gain.value=.4;verb.connect(verbG);verbG.connect(master);
const send=(from,g)=>{const s=ctx.createGain();s.gain.value=g;from.connect(s);s.connect(verb);};send(inst,.15);send(vocB,.15);send(vozB,.3);send(motB,.25);send(fxB,.4);
const dl=ctx.createDelay(2),dfb=ctx.createGain(),dlp=ctx.createBiquadFilter();dl.delayTime.value=SPB*.75;dfb.gain.value=.3;dlp.type='lowpass';dlp.frequency.value=3500;dl.connect(dlp);dlp.connect(dfb);dfb.connect(dl);dlp.connect(master);
{const s=ctx.createGain();s.gain.value=.18;motB.connect(s);s.connect(dl);}
const pan=(p,to)=>{const s=ctx.createStereoPanner();s.pan.value=Math.max(-1,Math.min(1,p));s.connect(to);return s;};
const env=(g,t,a,peak,dec,sus=0.0001,tail=.05,end)=>{g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(peak,t+a);g.gain.setTargetAtTime(Math.max(sus,.0001),t+a,dec);if(end!=null)g.gain.setTargetAtTime(0,end,tail);};
function vibr(o,t,rate,cents,delay,dur){const l=ctx.createOscillator(),lg=ctx.createGain();l.frequency.value=rate;lg.gain.setValueAtTime(0,t);lg.gain.setValueAtTime(0,t+delay);lg.gain.linearRampToValueAtTime(cents,t+delay+.3);l.connect(lg);lg.connect(o.detune);l.start(t);l.stop(t+dur+.5);}
/* bajo de onda cuadrada, como de consola de 8 bits, con un filtro que lo calienta */
function bajo(t,n,dur,vel){const o=ctx.createOscillator(),lp=ctx.createBiquadFilter(),g=ctx.createGain();o.type='square';o.frequency.value=hz(n);lp.type='lowpass';lp.frequency.setValueAtTime(1400,t);lp.frequency.setTargetAtTime(500,t,.08);o.connect(lp);lp.connect(g);g.connect(inst);env(g,t,.004,.16*vel,.15,.1*vel,.03,t+dur);o.start(t);o.stop(t+dur+.2);
 const s=ctx.createOscillator(),sg=ctx.createGain();s.frequency.value=hz(n);s.connect(sg);sg.connect(inst);env(sg,t,.004,.25*vel,.3,.18*vel,.03,t+dur);s.start(t);s.stop(t+dur+.2);}
function ep(t,n,dur,vel,p=0){const f=hz(n),c=ctx.createOscillator(),mo=ctx.createOscillator(),mg=ctx.createGain(),g=ctx.createGain(),out=pan(p,inst);c.frequency.value=f;mo.frequency.value=f;mg.gain.setValueAtTime(f*1.5*vel,t);mg.gain.setTargetAtTime(f*.15,t,.18);mo.connect(mg);mg.connect(c.frequency);
 env(g,t,.005,.1*vel,.6,.04*vel,.08,t+dur);c.connect(g);g.connect(out);[c,mo].forEach(o=>{o.start(t);o.stop(t+dur+.7);});}
const ksr=rng('cuerda');
function cuerda(t,n,dur,vel,apagada,p=0){const f=hz(n),N=Math.max(2,Math.round(SR/f)),len=Math.ceil(SR*Math.min(dur+.3,2)),b=ctx.createBuffer(1,len,SR),d=b.getChannelData(0),buf=new Float32Array(N);
 for(let i=0;i<N;i++)buf[i]=ksr()*2-1;const damp=apagada?.94:.996;let k=0;for(let i=0;i<len;i++){const v=buf[k],nx=buf[(k+1)%N];buf[k]=damp*.5*(v+nx);d[i]=v*(apagada?Math.exp(-i/SR/.05):1);k=(k+1)%N;}
 const s=ctx.createBufferSource(),g=ctx.createGain(),lp=ctx.createBiquadFilter();lp.type='lowpass';lp.frequency.value=apagada?2000:4200;s.buffer=b;s.connect(lp);lp.connect(g);g.connect(pan(p,inst));g.gain.setValueAtTime(.15*vel,t);g.gain.setTargetAtTime(0,t+dur,.05);s.start(t);s.stop(t+len/SR);}
function cuerdas(t,notas,dur,vel){const lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.frequency.value=2400;lp.connect(g);g.connect(inst);
 notas.forEach((n,i)=>[-8,0,8].forEach(dt=>{const o=ctx.createOscillator();o.type='sawtooth';o.frequency.value=hz(n);o.detune.value=dt+(H()-.5)*6;vibr(o,t,4.8+i*.2,6,.4,dur);o.connect(pan((i-1.5)*.4,lp));o.start(t);o.stop(t+dur+1);}));env(g,t,.3,.014*vel,1.2,.012*vel,.3,t+dur);}
/* los pitidos de menú del juego: muestras de main.ssm afinadas por el censo, tocadas a cualquier nota cambiando la velocidad */
const PITIDOS=[];for(const p of P.pitidos){const ab=await (await fetch('/meleeviewer/output/Sonido/censo/muestras/'+p.id+'.wav')).arrayBuffer();PITIDOS.push({...p,buf:await ctx.decodeAudioData(ab)});}
function pitido(t,n,vel,p=0,dest=motB){const c=PITIDOS.reduce((a,b)=>Math.abs(b.midi-n)<Math.abs(a.midi-n)?b:a),s=ctx.createBufferSource(),g=ctx.createGain();s.buffer=c.buf;s.playbackRate.value=2**((n-c.midi)/12);g.gain.value=.4*vel;s.connect(g);g.connect(pan(p,dest));s.start(t);}
/* los timbres de los motivos */
function cuadrada(t,n,dur,vel,p=0){const o=ctx.createOscillator(),lp=ctx.createBiquadFilter(),g=ctx.createGain();o.type='square';o.frequency.value=hz(n);lp.type='lowpass';lp.frequency.value=2600;o.connect(lp);lp.connect(g);g.connect(pan(p,motB));env(g,t,.005,.05*vel,.15,.035*vel,.04,t+dur);o.start(t);o.stop(t+dur+.2);}
function campanita(t,n,dur,vel,p=0){const f=hz(n),c=ctx.createOscillator(),m=ctx.createOscillator(),mg=ctx.createGain(),g=ctx.createGain();c.frequency.value=f;m.frequency.value=f*4;mg.gain.setValueAtTime(f*.8,t);mg.gain.setTargetAtTime(0,t,.25);m.connect(mg);mg.connect(c.frequency);c.connect(g);g.connect(pan(p,motB));env(g,t,.003,.06*vel,.6);[c,m].forEach(x=>{x.start(t);x.stop(t+2.5);});}
function metal(t,n,dur,vel,p=0){const lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.Q.value=2;lp.frequency.setValueAtTime(400,t);lp.frequency.linearRampToValueAtTime(1800,t+.06);lp.frequency.setTargetAtTime(700,t+.1,.2);lp.connect(g);g.connect(pan(p,motB));
 [0,7,-5].forEach(d=>{const o=ctx.createOscillator();o.type='sawtooth';o.frequency.value=hz(n);o.detune.value=d;o.connect(lp);o.start(t);o.stop(t+dur+.3);});env(g,t,.02,.07*vel,.25,.05*vel,.06,t+dur);}
const TIMBRE={mario:(t,n,d,v)=>pitido(t,n,v,-.35),luigi:(t,n,d,v)=>cuadrada(t,n,d,v,.35),peach:(t,n,d,v)=>campanita(t,n,d,v,.15),bowser:(t,n,d,v)=>metal(t,n,d,v,-.15)};
P.eventos.filter(e=>e.tipo==='motivo').forEach(e=>e.notas.forEach(([t,n,d])=>TIMBRE[e.quien](t,n,d,e.vel||1)));
const nb=ctx.createBuffer(1,SR*2,SR),nr=rng('ruido');{const d=nb.getChannelData(0);for(let k=0;k<d.length;k++)d[k]=nr()*2-1;}
function riser(t,dur,vel=1){const s=ctx.createBufferSource(),bp=ctx.createBiquadFilter(),g=ctx.createGain();s.buffer=nb;s.loop=true;bp.type='bandpass';bp.Q.value=2;bp.frequency.setValueAtTime(400,t);bp.frequency.exponentialRampToValueAtTime(8000,t+dur);
 g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(.22*vel,t+dur);g.gain.setValueAtTime(0,t+dur);s.connect(bp);bp.connect(g);g.connect(fxB);s.start(t);s.stop(t+dur+.05);}

/* ---------- 5. Las voces del juego (voces.py) ---------- */
for(const [nombre,p,d] of [['voces_coro.wav',-.35,0],['voces_coro.wav',.35,.012],['voces_gritos.wav',0,0]]){const ab=await (await fetch(DIR+nombre)).arrayBuffer(),b=await ctx.decodeAudioData(ab),s=ctx.createBufferSource();s.buffer=b;s.connect(pan(p,vozB));s.start(d);}

/* ---------- 6. La batería de consola ---------- */
const LM=window.LecturaMusica;
async function bateria(bar0,bars,d,extra=0){const dr={gain:.6,kit:'tr909',...d};
 const q={...p0,clips:[],tempo:{...p0.tempo,bpm:BPM,meter:4},music:LM.normalize({...p0.music,on:true,gain:.75,reverb:.08,delay:0,pulse:'none',voices:[],drums:LM.drums(dr)})};
 const len=bars*BAR,buf=await LM.render(q,[],len+extra,SR),s=ctx.createBufferSource(),g=ctx.createGain();s.buffer=buf;s.connect(g);g.connect(drumB);
 const at=tb(bar0);g.gain.setValueAtTime(1,at);if(!extra){g.gain.setValueAtTime(1,at+len-.03);g.gain.linearRampToValueAtTime(0,at+len);}s.start(at);}
const q16=n=>'x'+'.'.repeat(n-1),rep=(s,n)=>s.repeat(n);
const FUNK={kick:'x.....x...x..x..',snare:'....x.......x...',hat:'x.xxx.xxx.xxx.xx',openhat:'......x.......x.'};
await bateria(1,1,{snare:'............x.xx',hat:'x.x.x.x.x.x.x.x.'});
await bateria(2,4,{kick:'x.......x.......',rim:'....x.......x...',hat:'x.x.x.x.x.x.x.x.',crash:q16(64)});
await bateria(6,4,{...FUNK,tomhi:rep('.',48)+'..........x.x.xx'});
await bateria(10,2,{...FUNK,snare:'....x.......x...'+'x.x.x.x.xxxxxxxx'});
await bateria(12,4,{...FUNK,clap:'....x.......x...',crash:q16(64)});
await bateria(16,4,{...FUNK,clap:'....x.......x...',tommid:rep('.',48)+'........x.x.xxxx'});
await bateria(20,4,{...FUNK,crash:q16(64)});
await bateria(24,4,{...FUNK,tomhi:rep('.',48)+'..........x.x.xx'});
await bateria(28,4,{kick:'x...x...x...x...',snare:'....x.......x...',hat:'xxxxxxxxxxxxxxxx',cowbell:'..x...x...x...x.',crash:q16(64)});
await bateria(32,4,{...FUNK,clap:'....x.......x...',crash:q16(64),spray:q16(64)});
await bateria(36,4,{...FUNK,clap:'....x.......x...',tomhi:rep('.',48)+'....x.x.x.xxxxxx'});
await bateria(40,2,{kick:'x...............',crash:'x...............'},3);

/* ---------- 7. El arreglo ---------- */
const hv=v=>v*(.9+H()*.2),ht=t=>t+(H()-.5)*.006;
for(let bar=0;bar<NBAR;bar++){const S=sec(bar),c=chord(CH[bar]),N=c.notes,T=s=>ts(bar,s),satb=P.satb[bar];
 const linea=(vel=.9)=>[[0,2,0],[3,1,12],[6,1,0],[8,2,7],[10,1,12],[12,2,0],[14,2,10]].forEach(([s,d,i])=>bajo(ht(T(s)),c.bass+i,d*SPB/4*.9,hv(vel)));
 const comp=(vel=.8)=>[[0,3],[3,2],[7,3],[10,4]].forEach(([s,d])=>N.forEach((n,k)=>ep(ht(T(s))+k*.01,n,d*SPB/4,hv(vel),(k-1.5)*.3)));
 const funk=(vel=.8)=>{for(let s=0;s<16;s++)if([2,5,6,10,13,14].includes(s))N.slice(0,3).forEach((n,k)=>cuerda(ht(T(s))+k*.006,n+12,.1,hv(vel)*(1-k*.1),true,.45));};
 const satbCuerdas=(vel=1)=>cuerdas(T(0),satb.slice(0,3),BAR*.98,vel);
 const menu=(vel=.7)=>[0,6,12].forEach((s,k)=>pitido(T(s),N[(k+bar)%4]+24,vel,k%2?.5:-.5,inst));
 if(S==='intro'){if(bar===0)[0,4,8,12].forEach((s,k)=>pitido(T(s),[67,71,74,79][k]+12,1,0,inst));else{linea(.6);riser(T(8),BAR/2,.7);}}
 if(S==='verso'){linea(bar<6?.7:.9);comp(.7);if(bar>=6)funk(.7);if(bar%2)menu(.5);}
 if(S==='pre'){linea(1);comp(.8);satbCuerdas(.9);if(bar===11)riser(T(0),BAR,1);}
 if(S==='coro'||S==='coro2'){linea(1);comp(.85);funk(.85);satbCuerdas(1.1);menu(.6);}
 if(S==='verso2'){linea(.9);comp(.75);funk(.75);satbCuerdas(.6);}
 if(S==='puente'){linea(.9);satbCuerdas(.8);}
 if(S==='final'){if(bar===40){N.forEach((n,k)=>ep(T(0),n,BAR,1,(k-1.5)*.3));satbCuerdas(1.2);bajo(T(0),c.bass,BAR,1);}else{[0,2,4,6,8,10].forEach((s,k)=>pitido(T(s),[79,83,86,91,86,91][k],.9,k%2?.4:-.4,inst));bajo(T(0),c.bass,BAR*.9,.8);}}}

/* ---------- 8. El narrador ---------- */
let sung=0;for(const x of lead){const r=await sing(x.syl,x.note,x.D);
 const s=ctx.createBufferSource(),g=ctx.createGain();s.buffer=r.buf;g.gain.value=.5*r.norm*(x.gain??1);s.connect(g);g.connect(pan(0,vocB));s.start(Math.max(0,x.t-r.vt));sung++;}

const out=await ctx.startRendering(),L=out.getChannelData(0),Rr=out.getChannelData(1);let pk=0;for(let k=0;k<L.length;k++)pk=Math.max(pk,Math.abs(L[k]),Math.abs(Rr[k]));const g=.92/pk;
const rms=[];for(let s=0;s<Math.floor(LEN);s+=5){let a=0;const i0=s*SR,i1=Math.min(L.length,(s+5)*SR);for(let k=i0;k<i1;k++)a+=L[k]*L[k];rms.push(+(Math.sqrt(a/(i1-i0))*g).toFixed(3));}
const pcm=new Int16Array(L.length*2);for(let k=0;k<L.length;k++){pcm[k*2]=Math.max(-1,Math.min(1,L[k]*g))*32767;pcm[k*2+1]=Math.max(-1,Math.min(1,Rr[k]*g))*32767;}
const u8=new Uint8Array(pcm.buffer);let b64='';for(let k=0;k<u8.length;k+=32768)b64+=String.fromCharCode(...u8.subarray(k,k+32768));
return {b64:btoa(b64),peak:pk,rms,sung,seconds:LEN};};
