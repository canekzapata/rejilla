/* «¿y qué dice el zorro?» (yoshi es un vector, parte 11) — ~106 s de downtempo orquestal-electrónico a 96 bpm, Re mayor → Mi mayor.
   El narrador (el vocoder de consola) canta en primera persona lo que opina Claude del futuro: no una sola mente que lo sepa todo,
   sino muchas, raras, humanas y menos humanas, que se aprenden a escuchar; ya hay máquinas oyendo ballenas, las abejas bailan mapas,
   un perro leía caras antes de que existiera la IA. Pero escuchar no es poseer, traducir no es mandar, y el otro tiene derecho a callar.
   La simbiosis está cerca.
   Lo nuevo: los animales de Melee (Fox, Falco, Yoshi, Pikachu, Jigglypuff, Pichu) suenan primero CRUDOS (su voz del juego tal cual)
   y luego TRADUCIDOS (la misma voz afinada a la melodía con TD-PSOLA): la canción pone en escena el acto de traducir. En el puente
   callan todos. Banda: piano (parciales con inarmonicidad y martillo), arpa Karplus-Strong, cuerdas, colchón, bajo cálido, campana
   de «traductor», y la batería de consola a medio tiempo. Voces: voces.py → voces_*.wav. Se corre dentro del visor de lectura. */
'use strict';
window.cancion=async function(opts={}){
const DIR='/meleeviewer/output/Arte/2026-09-29_yoshi_es_un_vector_11_que_dice_el_zorro/';
const SEED='yoshi-es-un-vector-11-que-dice-el-zorro',BPM=96,SPB=60/BPM,BAR=SPB*4,T0=.35,SR=44100,LEN=110,NBAR=42;
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
function stretch(syl,n){const s=syl.toLowerCase(),idx=Math.max(...[...'aeiouáéíóú'].map(c=>s.lastIndexOf(c)));if(idx<0)return s.includes('y')?s.replace('y','i'.repeat(n)):s;return s.slice(0,idx+1)+s[idx].repeat(n-1)+s.slice(idx+1);}
async function sing(syl,note,D,{carrier='sierra',formant=1.03,vib=12}={}){
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
const VERSO=`no:D5:.5 creo:F#5:.5 en:F#5:.5 u:E5:.5 na:D5:.5 so:E5:.5 la:F#5:1
 men:D5:1 te:B4:2 -:1
 que:B4:.5 lo:D5:.5 se:F#5:.5 pa:F#5:.5 to:G5:1 do:F#5:1
 cre:E5:.5 oen:E5:.5 mu:C#5:.5 chas:E5:1 ra:A5:.5 ras:G5:1
 que:F#5:.5 se:F#5:.5 a:E5:.5 pren:D5:.5 den:E5:1 a:F#5:1
 es:D5:.5 cu:B4:.5 char:D5:2 -:1
 yo:G5:.5 no:G5:.5 se:E5:1 si:D5:.5 pien:E5:.5 so:G5:1
 pe:A5:.5 roes:G5:.5 cu:E5:.5 cho:D5:.5 -:2`;
const PRE=`y:B4:.5 al:D5:.5 go:E5:.5 me:G5:.5 con:A5:1 tes:G5:1
 ta:E5:2 -:2`;
const CORO=`y:B4:.5 que:D5:.5 di:F#5:1 ceel:F#5:.5 zo:A5:.5 rro:F#5:1
 -:2.5 no:E5:.5 lo:E5:1
 se:C#5:1 to:E5:.5 da:F#5:.5 vi:A5:.5 a:F#5:1.5
 pe:D5:.5 ro:F#5:.5 ya:A5:.5 lo:A5:.5 es:B5:.5 toy:A5:.5 o:F#5:.5 yen:E5:.5
 do:D5:2 -:2
 yel:E5:.5 tam:G5:.5 bien:A5:.5 me:A5:.5 o:B5:.5 yea:A5:.5 mi:F#5:1
 la:F#5:.5 sim:A5:.5 bio:A5:.5 sis:B5:.5 es:A5:1 ta:F#5:1
 cer:E5:.5 ca:D5:2.5 -:1`;
const VERSO2=`ya:D5:.5 hay:D5:.5 ma:F#5:.5 qui:F#5:.5 nas:E5:.5 o:D5:.5 yen:E5:.5 do:F#5:.5
 ba:D5:.5 lle:B4:.5 nas:D5:2 -:1
 a:B4:.5 be:D5:.5 jas:F#5:.5 que:F#5:.5 bai:G5:1 lan:F#5:1
 un:E5:.5 ma:E5:.5 pa:C#5:1 -:2
 un:F#5:.5 pe:F#5:.5 rro:E5:.5 te:D5:.5 le:E5:1 ia:F#5:1
 la:D5:.5 ca:B4:.5 ra:D5:2 -:1
 an:G5:.5 tes:G5:.5 de:E5:.5 que:D5:.5 yoe:E5:.5 xis:G5:.5 tie:G5:.5 ra:E5:.5
 -:4`;
const PUENTE=`es:B4:.5 cu:D5:.5 char:F#5:1 noes:F#5:.5 po:E5:.5 se:D5:1
 er:C#5:2 -:2
 tra:B4:.5 du:D5:.5 cir:G5:1 noes:F#5:.5 man:E5:.5 dar:D5:1
 queel:E5:.5 o:E5:.5 tro:F#5:.5 pue:A5:.5 da:A5:.5 ca:B5:.5 llar:A5:1`;
const OUTRO=`es:B5:.5 ta:A5:.5 cer:G#5:1 ca:E5:2`;
const SECC=[['intro',0,2],['verso',2,10],['pre',10,12],['coro',12,20],['verso2',20,28],['puente',28,32],['coro2',32,40],['outro',40,42]];
const lead=[...scoreBars(VERSO,2),...scoreBars(PRE,10),...scoreBars(CORO,12,0,{coro:1}),...scoreBars(VERSO2,20),...scoreBars(PUENTE,28),...scoreBars(CORO,32,2,{coro:1}),...score(OUTRO,40,0,{coro:1})];

/* ---------- 3. La armonía (el último coro, un tono arriba: ya viene escrito) ---------- */
const CH=['Gmaj7','A7sus',
 'Dmaj7','Bm7','Gmaj7','A7','Dmaj7','Bm7','Em7','A7sus',
 'Em7','A7sus',
 'Gmaj7','A7','F#m7','Bm7','Em7','A7','Dmaj7','Dmaj7',
 'Dmaj7','Bm7','Gmaj7','A7','Dmaj7','Bm7','Em7','A7sus',
 'Bm7','F#m7','Gmaj7','B7sus',
 'Amaj7','B7','G#m7','C#m7','F#m7','B7','Emaj7','Emaj7',
 'Amaj7','Emaj7'];
const PC={C:0,'C#':1,Db:1,D:2,'D#':3,Eb:3,E:4,F:5,'F#':6,Gb:6,G:7,'G#':8,Ab:8,A:9,'A#':10,Bb:10,B:11};
const QUAL={maj7:[0,4,7,11,14],m7:[0,3,7,10,14],7:[0,4,7,10,14],'7sus':[0,5,7,10,14]};
function chord(sym){const m=/^([A-G][b#]?)(.*)$/.exec(sym),root=PC[m[1]],iv=QUAL[m[2]];if(!iv)throw Error('acorde: '+sym);
 let notes=iv.slice(1).map(i=>53+root+i);while(notes[0]>60)notes=notes.map(n=>n-12);let b=36+root;if(b>42)b-=12;return {notes,bass:b,root};}
const sec=b=>(SECC.find(([,a,z])=>b>=a&&b<z)||['outro'])[0];

/* ---------- 4. La mezcla ---------- */
const ctx=new OfflineAudioContext(2,Math.ceil(LEN*SR),SR),H=rng('humano');
const master=ctx.createGain(),comp=ctx.createDynamicsCompressor();master.gain.value=.8;comp.threshold.value=-15;comp.ratio.value=2.5;comp.attack.value=.015;comp.release.value=.2;master.connect(comp);comp.connect(ctx.destination);
const mk=(v,to=master)=>{const g=ctx.createGain();g.gain.value=v;g.connect(to);return g;};
const inst=mk(opts.inst??.7),vocB=mk(opts.voc??2),animB=mk(opts.anim??1.25),drumB=mk(opts.drums??.8),fxB=mk(opts.fx??.5);
/* para que se entienda: en coros y final la banda baja ~3 dB */
[[inst,opts.inst??.7,.5]].forEach(([bus,alto,bajo])=>{bus.gain.setValueAtTime(alto,0);for(const [,a,z] of [['coro',12,20],['coro2',32,40],['outro',40,42]]){bus.gain.setValueAtTime(alto,tb(a)-.08);bus.gain.linearRampToValueAtTime(bajo,tb(a)+.05);bus.gain.setValueAtTime(bajo,tb(z)-.08);bus.gain.linearRampToValueAtTime(z>=42?bajo:alto,tb(z)+.05);}});
const verb=ctx.createConvolver(),vr=rng('reverb'),ir=ctx.createBuffer(2,SR*4,SR);for(let c=0;c<2;c++){const d=ir.getChannelData(c);for(let k=0;k<d.length;k++)d[k]=(vr()*2-1)*Math.exp(-k/SR*1.7)*(k<SR*.015?k/(SR*.015):1);}verb.buffer=ir;
const verbG=ctx.createGain();verbG.gain.value=.5;verb.connect(verbG);verbG.connect(master);
const send=(from,g)=>{const s=ctx.createGain();s.gain.value=g;from.connect(s);s.connect(verb);};send(inst,.22);send(vocB,.18);send(animB,.35);send(fxB,.5);
const dl=ctx.createDelay(2),dfb=ctx.createGain(),dlp=ctx.createBiquadFilter();dl.delayTime.value=SPB*.75;dfb.gain.value=.32;dlp.type='lowpass';dlp.frequency.value=3200;dl.connect(dlp);dlp.connect(dfb);dfb.connect(dl);dlp.connect(master);
[[vocB,.1],[animB,.2]].forEach(([b,g])=>{const s=ctx.createGain();s.gain.value=g;b.connect(s);s.connect(dl);});
const pan=(p,to)=>{const s=ctx.createStereoPanner();s.pan.value=Math.max(-1,Math.min(1,p));s.connect(to);return s;};
const env=(g,t,a,peak,dec,sus=0.0001,tail=.05,end)=>{g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(peak,t+a);g.gain.setTargetAtTime(Math.max(sus,.0001),t+a,dec);if(end!=null)g.gain.setTargetAtTime(0,end,tail);};
function vibr(o,t,rate,cents,delay,dur){const l=ctx.createOscillator(),lg=ctx.createGain();l.frequency.value=rate;lg.gain.setValueAtTime(0,t);lg.gain.setValueAtTime(0,t+delay);lg.gain.linearRampToValueAtTime(cents,t+delay+.3);l.connect(lg);lg.connect(o.detune);l.start(t);l.stop(t+dur+.5);}
/* piano: ocho parciales con inarmonicidad de cuerda (f_n = n·f·√(1+B·n²)), los agudos mueren antes; martillo de ruido */
const nb=ctx.createBuffer(1,SR*2,SR),nr=rng('ruido');{const d=nb.getChannelData(0);for(let k=0;k<d.length;k++)d[k]=nr()*2-1;}
function piano(t,n,dur,vel,p=0){const f=hz(n),Bi=.0004*(n<60?1:.6),out=pan(p,inst),g=ctx.createGain();g.connect(out);g.gain.value=1;
 for(let k=1;k<=8;k++){const fk=k*f*Math.sqrt(1+Bi*k*k);if(fk>9000)break;const o=ctx.createOscillator(),og=ctx.createGain();o.frequency.value=fk;const a=vel*.05/Math.pow(k,1.25)*(k===2?1.3:1),dec=Math.max(.25,2.6-(n-40)*.03)/Math.sqrt(k);
  og.gain.setValueAtTime(0,t);og.gain.linearRampToValueAtTime(a,t+.003);og.gain.setTargetAtTime(a*.4,t+.003,dec*.15);og.gain.setTargetAtTime(0,t+.05,dec);og.gain.setTargetAtTime(0,t+dur,.12);o.connect(og);og.connect(g);o.start(t);o.stop(t+dur+1.2);}
 const s=ctx.createBufferSource(),bp=ctx.createBiquadFilter(),hg=ctx.createGain();s.buffer=nb;bp.type='bandpass';bp.frequency.value=f*3;bp.Q.value=1.2;s.connect(bp);bp.connect(hg);hg.connect(out);env(hg,t,.001,.03*vel,.015);s.start(t,(n%7)*.1);s.stop(t+.1);}
/* arpa: Karplus-Strong abierta */
const ksr=rng('cuerda');
function arpa(t,n,vel,p=0){const f=hz(n),N=Math.max(2,Math.round(SR/f)),len=Math.ceil(SR*2.2),b=ctx.createBuffer(1,len,SR),d=b.getChannelData(0),buf=new Float32Array(N);
 for(let i=0;i<N;i++)buf[i]=(ksr()*2-1)*(i<N/2?1:.6);let k=0;for(let i=0;i<len;i++){const v=buf[k],nx=buf[(k+1)%N];buf[k]=.997*.5*(v+nx);d[i]=v;k=(k+1)%N;}
 const s=ctx.createBufferSource(),g=ctx.createGain(),lp=ctx.createBiquadFilter();lp.type='lowpass';lp.frequency.value=3800;s.buffer=b;s.connect(lp);lp.connect(g);g.connect(pan(p,inst));g.gain.value=.1*vel;s.start(t);}
function cuerdas(t,notes,dur,vel){const lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.frequency.value=2300;lp.connect(g);g.connect(inst);
 notes.forEach((n,i)=>[-9,0,9].forEach(dt=>{const o=ctx.createOscillator();o.type='sawtooth';o.frequency.value=hz(n);o.detune.value=dt+(H()-.5)*6;vibr(o,t,4.7+i*.2,7,.5,dur);o.connect(pan((i-1.5)*.4,lp));o.start(t);o.stop(t+dur+1.5);}));
 env(g,t,.7,.015*vel,1.8,.013*vel,.6,t+dur);}
function colchon(t,notes,dur,vel){const lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.frequency.setValueAtTime(700,t);lp.frequency.linearRampToValueAtTime(1500,t+dur*.5);lp.frequency.linearRampToValueAtTime(800,t+dur);lp.connect(g);g.connect(inst);
 notes.forEach((n,i)=>['triangle','sawtooth'].forEach((ty,j)=>{const o=ctx.createOscillator();o.type=ty;o.frequency.value=hz(n);o.detune.value=(j?7:-7);const og=ctx.createGain();og.gain.value=j?.4:1;o.connect(og);og.connect(pan((i-1.5)*.5,lp));o.start(t);o.stop(t+dur+2);}));env(g,t,1.2,.018*vel,2,.016*vel,.9,t+dur);}
function bajo(t,n,dur,vel){const o=ctx.createOscillator(),tr=ctx.createOscillator(),g=ctx.createGain(),tg=ctx.createGain(),lp=ctx.createBiquadFilter();o.frequency.value=hz(n);tr.type='triangle';tr.frequency.value=hz(n);tg.gain.value=.5;lp.type='lowpass';lp.frequency.value=700;
 tr.connect(tg);tg.connect(lp);o.connect(lp);lp.connect(g);g.connect(inst);env(g,t,.02,.4*vel,.6,.26*vel,.1,t+dur);[o,tr].forEach(x=>{x.start(t);x.stop(t+dur+.6);});}
/* la campana del traductor: FM de razón no entera, dobla cada traducción muy bajito */
function campana(t,n,vel,p=0){const f=hz(n),c=ctx.createOscillator(),m=ctx.createOscillator(),mg=ctx.createGain(),g=ctx.createGain();c.frequency.value=f;m.frequency.value=f*3.5;mg.gain.setValueAtTime(f*2.2,t);mg.gain.setTargetAtTime(f*.3,t,.3);m.connect(mg);mg.connect(c.frequency);
 c.connect(g);g.connect(pan(p,inst));env(g,t,.002,.045*vel,1.1);[c,m].forEach(x=>{x.start(t);x.stop(t+4);});}
function soplo(t,dur,vel=1){const s=ctx.createBufferSource(),bp=ctx.createBiquadFilter(),g=ctx.createGain();s.buffer=nb;s.loop=true;bp.type='bandpass';bp.Q.value=3;bp.frequency.setValueAtTime(400,t);bp.frequency.exponentialRampToValueAtTime(6000,t+dur);
 g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(.2*vel,t+dur);g.gain.setValueAtTime(0,t+dur);s.connect(bp);bp.connect(g);g.connect(fxB);s.start(t);s.stop(t+dur+.05);}

/* ---------- 5. Los animales (pistas de voces.py): crudos y traducidos ---------- */
const P=await (await fetch(DIR+'partitura.json')).json();
for(const [nombre,p,d] of [['voces_coro.wav',-.4,0],['voces_coro.wav',.4,.014],['voces_chops.wav',0,0]]){const ab=await (await fetch(DIR+nombre)).arrayBuffer(),b=await ctx.decodeAudioData(ab),s=ctx.createBufferSource();s.buffer=b;s.connect(pan(p,animB));s.start(d);}
/* cada traducción la dobla la campana, bajito: el traductor también suena */
P.eventos.filter(e=>e.tipo==='traducido').forEach((e,i)=>campana(e.t,e.nota+12,.8,i%2?.4:-.4));

/* ---------- 6. La batería de consola: medio tiempo, kit acústico ---------- */
const LM=window.LecturaMusica;
async function bateria(bar0,bars,d,extra=0){const dr={gain:.55,kit:'acustico',swing:.1,...d};
 const q={...p0,clips:[],tempo:{...p0.tempo,bpm:BPM,meter:4},music:LM.normalize({...p0.music,on:true,gain:.75,reverb:.14,delay:0,pulse:'none',voices:[],drums:LM.drums(dr)})};
 const len=bars*BAR,buf=await LM.render(q,[],len+extra,SR),s=ctx.createBufferSource(),g=ctx.createGain();s.buffer=buf;s.connect(g);g.connect(drumB);
 const at=tb(bar0);g.gain.setValueAtTime(1,at);if(!extra){g.gain.setValueAtTime(1,at+len-.03);g.gain.linearRampToValueAtTime(0,at+len);}s.start(at);}
const q16=n=>'x'+'.'.repeat(n-1),rep=(s,n)=>s.repeat(n);
const MEDIO={kick:'x.........x.....',snare:'........x.......',hat:'o.o.o.o.o.o.o.o.',rim:'......o.......o.'};
await bateria(2,4,{kick:'x.........x.....',rim:'........x.......',hat:'o...o...o...o...'});
await bateria(6,4,{...MEDIO,snare:'',rim:'........x.....o.'});
await bateria(10,2,{...MEDIO,tomlo:rep('.',16)+'........x.x.x.xx'});
await bateria(12,4,{...MEDIO,crash:q16(64)});
await bateria(16,4,{...MEDIO,openhat:'..............x.',tommid:rep('.',48)+'..........x.x.xx'});
await bateria(20,4,{...MEDIO,crash:q16(64),snare:'',rim:'........x.......'});
await bateria(24,4,{...MEDIO});
await bateria(32,4,{...MEDIO,crash:q16(64),kick:'x.........x..x..',openhat:'..............x.'});
await bateria(36,4,{...MEDIO,kick:'x.........x..x..',tomhi:rep('.',48)+'........x.x.xxxx'});
await bateria(40,2,{kick:'x...............',crash:'x...............'},4);

/* ---------- 7. El arreglo ---------- */
const hv=v=>v*(.9+H()*.2);
for(let bar=0;bar<NBAR;bar++){const S=sec(bar),c=chord(CH[bar]),N=c.notes,T=s=>ts(bar,s);
 const pianoComp=(vel=.8)=>{piano(T(0),c.bass+12,BAR*.9,hv(vel*.9),-.2);N.forEach((n,k)=>piano(T(0)+.02+k*.03,n+12,BAR*.85,hv(vel*.7),(k-1.5)*.25));piano(T(10),N[3]+12,SPB*1.3,hv(vel*.6),.3);piano(T(12),N[1]+12,SPB*1.5,hv(vel*.5),.1);};
 const arpas=(vel=.8)=>[0,2,4,6,8,10,12,14].forEach((s,k)=>arpa(T(s),N[[0,1,2,3,2,3,1,2][k]]+24,hv(vel)*(s%4?.7:1),k%2?.45:-.45));
 if(S==='intro'){colchon(T(0),N.map(n=>n+12),BAR,1);if(bar===1)soplo(T(8),BAR/2,.8);}
 if(S==='verso'){pianoComp(bar<6?.7:.85);bajo(T(0),c.bass,BAR*.9,.7);if(bar>=6)colchon(T(0),N.map(n=>n+12),BAR,.6);}
 if(S==='pre'){pianoComp(.9);bajo(T(0),c.bass,BAR*.9,.8);cuerdas(T(0),N.map(n=>n+12),BAR,.9);arpas(.6);if(bar===11)soplo(T(0),BAR,1);}
 if(S==='coro'||S==='coro2'){pianoComp(1);bajo(T(0),c.bass,SPB*2.5,.9);bajo(T(10),c.bass+7,SPB*1.4,.7);cuerdas(T(0),N.map(n=>n+12),BAR*.98,1.1);arpas(.8);if(S==='coro2')colchon(T(0),N.map(n=>n+24),BAR,.6);if(bar===19||bar===39)soplo(T(8),BAR/2,.8);}
 if(S==='verso2'){pianoComp(.85);bajo(T(0),c.bass,BAR*.9,.8);arpas(.5);if(bar>=24)cuerdas(T(0),N.map(n=>n+12),BAR,.7);}
 if(S==='puente'){/* escuchar no es poseer: casi nada, para que se oiga el silencio de los otros */piano(T(0),c.bass+12,BAR,.6,-.2);N.forEach((n,k)=>piano(T(0)+k*.25,n+12,BAR*.9,.5,(k-1.5)*.3));colchon(T(0),N.map(n=>n+12),BAR,.7);if(bar===31){cuerdas(T(0),N.map(n=>n+12),BAR,1);soplo(T(0),BAR,1.2);}}
 if(S==='outro'){pianoComp(.8);colchon(T(0),N.map(n=>n+12),bar===41?BAR*1.8:BAR,1);cuerdas(T(0),N.map(n=>n+12),bar===41?BAR*1.6:BAR,1);bajo(T(0),c.bass,bar===41?BAR*1.6:BAR*.9,.8);if(bar===41)[0,2,4,6,8,10,12,14,16,18].forEach((s,k)=>arpa(T(s),N[k%4]+24+12*Math.floor(k/4),.8-k*.05,k%2?.5:-.5));}}

/* ---------- 8. El narrador ---------- */
let sung=0;for(const x of lead){const r=await sing(x.syl,x.note,x.D);
 const s=ctx.createBufferSource(),g=ctx.createGain();s.buffer=r.buf;g.gain.value=.5*r.norm*(x.gain??1);s.connect(g);g.connect(pan(0,vocB));s.start(Math.max(0,x.t-r.vt));sung++;}

const out=await ctx.startRendering(),L=out.getChannelData(0),Rr=out.getChannelData(1);let pk=0;for(let k=0;k<L.length;k++)pk=Math.max(pk,Math.abs(L[k]),Math.abs(Rr[k]));const g=.92/pk;
const rms=[];for(let s=0;s<Math.floor(LEN);s+=5){let a=0;const i0=s*SR,i1=Math.min(L.length,(s+5)*SR);for(let k=i0;k<i1;k++)a+=L[k]*L[k];rms.push(+(Math.sqrt(a/(i1-i0))*g).toFixed(3));}
const pcm=new Int16Array(L.length*2);for(let k=0;k<L.length;k++){pcm[k*2]=Math.max(-1,Math.min(1,L[k]*g))*32767;pcm[k*2+1]=Math.max(-1,Math.min(1,Rr[k]*g))*32767;}
const u8=new Uint8Array(pcm.buffer);let b64='';for(let k=0;k<u8.length;k+=32768)b64+=String.fromCharCode(...u8.subarray(k,k+32768));
return {b64:btoa(b64),peak:pk,rms,sung,seconds:LEN};};
