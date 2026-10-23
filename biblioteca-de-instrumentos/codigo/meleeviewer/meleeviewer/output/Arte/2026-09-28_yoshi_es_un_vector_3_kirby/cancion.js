/* «kirby se comió la memoria» (yoshi es un vector, parte 3) — ~1 min, girlypop dank en crescendo: kirby mide un píxel, se come todo y se vuelve inmenso.
   La instrumentación crece con kirby: de un krar solo detrás de un filtro de bocinita, a la banda entera con 808s; al final vuelve a ser un píxel.
   Escalas etíopes (qenet) dentro de la línea j-pop: verso en Bati mayor, pre y break en Ambassel, riffs de krar en Tezeta; vibráfono ethio-jazz.
   La voz es el vocoder por formantes de consola (static/lectura/musica.js), cargado como copia parchada en memoria (nota exacta por sílaba).
   Todo lo demás es síntesis Web Audio sembrada: misma semilla, misma canción. Se corre dentro del visor de lectura: window.cancion(opciones) → WAV en base64. */
'use strict';
window.cancion=async function(opts={}){
const SEED='yoshi-es-un-vector-3-kirby',BPM=150,SPB=60/BPM,T0=.35,SR=44100,LEN=56;
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
/* Alarga la sílaba repitiendo su última vocal: el vocoder la canta como una vocal sostenida. */
function stretch(syl,n){const s=syl.toLowerCase(),idx=Math.max(...[...'aeiou'].map(c=>s.lastIndexOf(c)));if(idx<0)return s.includes('y')?s.replace('y','i'.repeat(n)):s;return s.slice(0,idx+1)+s[idx].repeat(n-1)+s.slice(idx+1);}
async function sing(syl,note,D,{carrier='sierra',formant=1.24,vib=26}={}){
 const piece={...p0,seed:SEED,music:CM.normalize({...base,vozCarrier:carrier,voices:[{instrument:'none',octave:4,gain:.7,pan:0,entry:'none',words:false,gesture:false}]})};
 let v,ev;for(let n=1;n<=48;n++){v={i:0,key:'s',born:0,duration:D/.95,text:stretch(syl,n),effect:'fade',hold:0,speak:'vocoder',canto:note};ev=CM.speechEvents(piece,v)[0];if(ev.dur>=D*.97)break;}
 window.CANTA_FORMANT=formant;window.CANTA_VIB=vib;
 const buf=await CM.render(piece,[v],ev.dur+.6,SR),vt=(ev.steps.find(s=>s.v)||{t:0}).t;
 let pk=0;for(let c=0;c<2;c++){const d=buf.getChannelData(c);for(let k=0;k<d.length;k++)pk=Math.max(pk,Math.abs(d[k]));}
 return {buf,vt,norm:pk>0?1/pk:1};}

/* ---------- 2. La letra y la melodía: sílaba:nota:tiempos (- = silencio), un compás por renglón ---------- */
const NOTE={C:0,D:2,E:4,F:5,G:7,A:9,B:11};
const nm=s=>{const m=/^([A-G])(b|#)?(-?\d)$/.exec(s);if(!m)throw Error('nota: '+s);return 12*(+m[3]+1)+NOTE[m[1]]+(m[2]==='b'?-1:m[2]==='#'?1:0);};
function score(str,bar,tr=0,o={}){const out=[];let beat=0;for(const tok of str.trim().split(/\s+/)){const [a,b,c]=tok.split(':');if(a==='-'){beat+=+b;continue;}out.push({syl:a,note:nm(b)+tr,t:tb(bar,beat),D:+c*SPB-.03,...o});beat+=+c;}return out;}
const INTRO=`kir:E5:.5 by:A5:1.5 -:2`;
/* verso en Bati mayor (A C# D E G#) */
const VERSO=`kir:E5:.5 by:C#5:.5 mi:E5:.5 de:G#5:.5 un:E5:.5 pi:C#5:.5 xel:A4:1
 es:A4:.5 ta:C#5:.5 chi:D5:.5 qui:E5:.5 ti:G#5:.5 to:E5:1 -:.5
 no:G#5:.5 lo:G#5:.5 ve:E5:.5 la:C#5:.5 ca:E5:.5 ma:G#5:.5 ra:A5:1
 ni:A5:.5 con:G#5:.5 zum:E5:1 -:2
 pe:E5:.5 ro:C#5:.5 tie:E5:.5 ne:G#5:.5 ham:A5:1 bre:E5:1
 de:A5:.5 to:G#5:.5 dos:E5:.5 tus:D5:.5 da:C#5:1 tos:E5:1
 se:C#5:.5 co:E5:.5 mio:G#5:.5 a:E5:.5 yo:C#5:.5 shi:E5:.5 vec:C#5:.5 tor:A#4:.5
 y:D5:.5 a:D5:.5 fox:D5:.5 con:C#5:.5 ram:A4:1 -:1`;
/* pre en Ambassel (A Bb D E F) */
const PRE=`in:A4:.5 ha:D5:.5 la:E5:1 in:F5:.5 ha:E5:.5 la:D5:1
 cre:E5:.5 ce:E5:.5 ex:E5:.5 po:D5:.5 nen:F5:.5 cial:Bb5:1.5
 no:A5:.5 ca:F5:.5 be:A5:.5 en:Bb5:.5 el:A5:.5 mo:F5:.5 ni:E5:.5 tor:D5:.5
 o:E5:.5 ye:F5:.5 kir:G#5:1 by:A5:.5 no:B5:1.5`;
const CORO_A=`kir:F#5:.5 by:A5:.5 se:A5:.5 co:A5:.5 mio:B5:1 la:G#5:1
 me:E5:.5 mo:E5:.5 ria:C#5:1 nam:E5:.5 nam:F#5:1 -:.5
 se:D5:.5 co:D5:.5 mio:D5:.5 el:C#5:.5 vi:D5:.5 de:F#5:.5 o:G#5:.5 y:A5:.5
 la:B5:.5 his:A5:.5 to:G#5:.5 ria:A5:2.5`;
const CORO_B=`a:F#5:.5 ho:A5:.5 ra:A5:.5 es:A5:.5 in:B5:.5 men:C#6:.5 so:B5:.5 y:A5:.5
 yo:G#5:1 soy:E5:.5 un:C#5:.5 pi:E5:.5 xel:A#5:1.5
 a:D5:.5 bra:F#5:.5 za:A5:.5 me:B5:.5 fuer:B5:.5 te:A5:.5 po:G#5:.5 yo:E5:.5
 -:1 po:E5:.5 yo:A5:1 -:1.5`;
/* break en Ambassel sobre pedal de La, y sube a F#7b9 para caer en Si */
const BREAK=`po:A4:.5 yo:Bb4:.5 po:D5:.5 yo:E5:.5 po:F5:.5 yo:E5:.5 po:D5:.5 yo:Bb4:.5
 po:A5:.5 yo:Bb5:.5 po:D6:.5 yo:F6:.5 po:E6:.5 yo:C#6:.5 po:A#5:1`;
const ULTIMO_B=`gra:F#5:.5 cias:A5:.5 por:A5:.5 co:A5:.5 mer:B5:.5 te:C#6:.5 mi:B5:.5 can:A5:.5
 cion:G#5:1.5 -:.5 nam:E5:.5 nam:C#5:.5 nam:A#4:1`;
const FINAL=`po:C#6:1 yo:B5:3`;
const FIN=`me:B2:.5 mo:B2:.5 ria:B2:1 lle:B2:.5 na:B2:1.5`;
const NL=String.fromCharCode(10);
function scoreBars(str,bar0,tr=0,o={}){return str.trim().split(NL).flatMap((l,k)=>score(l,bar0+k,tr,o));}
const lead=[...score(INTRO,1),...scoreBars(VERSO,2),...scoreBars(PRE,10),...scoreBars(CORO_A+NL+CORO_B,14,0,{coro:1}),
 ...scoreBars(BREAK,22,0,{carrier:'pulso'}),...scoreBars(CORO_A+NL+ULTIMO_B,24,2,{coro:1}),...score(FINAL,30),...score(FIN,32,0,{carrier:'coro',formant:.85,vib:0,gain:.8})];

/* ---------- 3. La armonía ---------- */
const CH=[['Dmaj9'],['E13'],
 ['Amaj7'],['Dmaj7'],['C#m7'],['E7sus','E7'],['Amaj7','A7'],['Dmaj7'],['C#m7','F#7'],['Bm7','E7'],
 ['A7sus','Bb/A'],['A7sus','Bb/A'],['Bbmaj7'],['E7sus','E7b9'],
 ['Dmaj7','E7'],['C#m7','F#m7'],['Bm7','E7'],['Amaj7','A7'],['Dmaj7','E/D'],['C#m7','F#7'],['Bm7','E7'],['A6'],
 ['A5'],['Bb/A','F#7b9'],
 ['Emaj7','F#7'],['D#m7','G#m7'],['C#m7','F#7'],['Bmaj7','B7'],['Emaj7','F#/E'],['D#m7','G#7'],
 ['C#m7','F#7'],['Bmaj9']];
const PC={C:0,'C#':1,Db:1,D:2,'D#':3,Eb:3,E:4,F:5,'F#':6,Gb:6,G:7,'G#':8,Ab:8,A:9,'A#':10,Bb:10,B:11};
const QUAL={maj7:[4,7,11,14],maj9:[4,11,14,19],6:[4,7,9,14],m7:[3,7,10,14],m9:[3,10,14,17],7:[4,9,10,14],13:[4,9,10,14],'7b9':[4,7,10,13],'7sus':[5,7,10,14],dim7:[3,6,9,12],'':[4,7,12,14],5:[7,12,19,24]};
function chord(sym){const m=/^([A-G][b#]?)(.*?)(?:\/([A-G][b#]?))?$/.exec(sym),root=PC[m[1]],iv=QUAL[m[2]];if(!iv)throw Error('acorde: '+sym);
 let notes=iv.map(i=>48+root+i);while(notes[0]<53)notes=notes.map(n=>n+12);while(notes[0]>=64)notes=notes.map(n=>n-12);
 const bp=m[3]?PC[m[3]]:root;return {notes,bass:28+((bp-4+12)%12),fifth:28+((root-4+12)%12)+7};}
/* Los qenet (modos etíopes), como grados sobre la tónica. */
const QENET={tezeta:[0,2,4,7,9],bati:[0,4,5,7,11],ambassel:[0,1,5,7,8],anchihoye:[0,1,5,6,9]};
const qn=(q,root,i)=>{const s=QENET[q],o=Math.floor(i/s.length);return root+s[((i%s.length)+s.length)%s.length]+12*o;};
/* El tamaño de kirby manda qué tanto suena la banda. */
const sec=b=>b<2?'intro':b<10?'verso':b<14?'pre':b<22?'coro':b<24?'break':b<30?'coro':'final';
const tam=b=>b<6?'pixel':b<10?'crece':b<14?'expo':b<22?'inmenso':b<24?'frito':b<30?'todo':'vuelve';

/* ---------- 4. La mezcla: instrumentos y batería pasan por la «bocinita» (filtros que se abren con kirby) ---------- */
const ctx=new OfflineAudioContext(2,Math.ceil(LEN*SR),SR),H=rng('humano');
const master=ctx.createGain(),comp=ctx.createDynamicsCompressor();master.gain.value=.8;comp.threshold.value=-14;comp.ratio.value=3;comp.attack.value=.01;comp.release.value=.15;master.connect(comp);comp.connect(ctx.destination);
const instB=ctx.createGain(),vocB=ctx.createGain(),drumB=ctx.createGain(),banda=ctx.createGain();instB.gain.value=opts.inst??1;drumB.gain.value=opts.drums??1;vocB.gain.value=opts.voc??1.6;instB.connect(banda);drumB.connect(banda);vocB.connect(master);
const hpf=ctx.createBiquadFilter(),lpf=ctx.createBiquadFilter();hpf.type='highpass';lpf.type='lowpass';lpf.Q.value=.9;banda.connect(hpf);hpf.connect(lpf);lpf.connect(master);
lpf.frequency.setValueAtTime(1900,0);hpf.frequency.setValueAtTime(420,0);
lpf.frequency.setTargetAtTime(4500,tb(6),.15);hpf.frequency.setTargetAtTime(160,tb(6),.15);
lpf.frequency.setValueAtTime(4500,tb(10));lpf.frequency.exponentialRampToValueAtTime(20000,tb(14));hpf.frequency.setValueAtTime(160,tb(10));hpf.frequency.exponentialRampToValueAtTime(20,tb(14));
lpf.frequency.setValueAtTime(20000,tb(30,2));lpf.frequency.exponentialRampToValueAtTime(1500,tb(31,3));hpf.frequency.setValueAtTime(20,tb(30,2));hpf.frequency.exponentialRampToValueAtTime(450,tb(31,3));
/* Lo frito: saturación en paralelo que solo se abre en el break. */
const drive=ctx.createWaveShaper(),dcv=new Float32Array(2048),driveG=ctx.createGain();for(let k=0;k<2048;k++){const x=k/1023.5-1;dcv[k]=Math.tanh(x*7);}drive.curve=dcv;banda.connect(drive);drive.connect(driveG);driveG.connect(master);
driveG.gain.setValueAtTime(0,0);driveG.gain.setValueAtTime(.32,tb(22));driveG.gain.setValueAtTime(0,tb(24));
const verb=ctx.createConvolver(),vr=rng('reverb'),ir=ctx.createBuffer(2,SR*2.4,SR);for(let c=0;c<2;c++){const d=ir.getChannelData(c);for(let k=0;k<d.length;k++)d[k]=(vr()*2-1)*Math.exp(-k/SR*2.6)*(k<SR*.01?k/(SR*.01):1);}verb.buffer=ir;
const verbG=ctx.createGain();verbG.gain.value=.5;verb.connect(verbG);verbG.connect(master);
const send=(from,g)=>{const s=ctx.createGain();s.gain.value=g;from.connect(s);s.connect(verb);return s;};send(lpf,.14);send(vocB,.26);
const dl=ctx.createDelay(2),dfb=ctx.createGain(),dlp=ctx.createBiquadFilter(),dsend=ctx.createGain();dl.delayTime.value=SPB*.75;dfb.gain.value=.3;dlp.type='lowpass';dlp.frequency.value=3200;dsend.gain.value=.2;vocB.connect(dsend);dsend.connect(dl);dl.connect(dlp);dlp.connect(dfb);dfb.connect(dl);dlp.connect(master);
const nb=ctx.createBuffer(1,SR*2,SR),nr=rng('ruido');{const d=nb.getChannelData(0);for(let k=0;k<d.length;k++)d[k]=nr()*2-1;}
const pan=(p,to)=>{const s=ctx.createStereoPanner();s.pan.value=Math.max(-1,Math.min(1,p));s.connect(to);return s;};
const env=(g,t,a,peak,dec,sus=0.0001,tail=.05,end)=>{g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(peak,t+a);g.gain.setTargetAtTime(Math.max(sus,.0001),t+a,dec);if(end!=null)g.gain.setTargetAtTime(0,end,tail);};
function noise(t,dur,rate=1){const s=ctx.createBufferSource();s.buffer=nb;s.loop=true;s.playbackRate.value=rate;s.start(t,H()*1.5);s.stop(t+dur);return s;}
function vib(o,t,rate,cents,delay,dur){const l=ctx.createOscillator(),lg=ctx.createGain();l.frequency.value=rate;lg.gain.setValueAtTime(0,t);lg.gain.setValueAtTime(0,t+delay);lg.gain.linearRampToValueAtTime(cents,t+delay+.25);l.connect(lg);lg.connect(o.detune);l.start(t);l.stop(t+dur+.5);}

/* Rhodes FM, bajo, glockenspiel y metales (los de siempre). */
function ep(t,n,dur,vel,p=0){const f=hz(n),c=ctx.createOscillator(),mo=ctx.createOscillator(),mg=ctx.createGain(),g=ctx.createGain(),ti=ctx.createOscillator(),tg=ctx.createGain(),out=pan(p,instB);
 c.frequency.value=f;mo.frequency.value=f;mg.gain.setValueAtTime(f*1.8*vel,t);mg.gain.setTargetAtTime(f*.18,t,.18);mo.connect(mg);mg.connect(c.frequency);
 ti.frequency.value=f*14.2;tg.gain.setValueAtTime(.035*vel,t);tg.gain.setTargetAtTime(0,t,.012);ti.connect(tg);tg.connect(out);
 env(g,t,.004,.13*vel,.5,.05*vel,.07,t+dur);c.connect(g);g.connect(out);[c,mo,ti].forEach(o=>{o.start(t);o.stop(t+dur+.6);});}
function bass(t,n,dur,vel){const f=hz(n),o=ctx.createOscillator(),s=ctx.createOscillator(),lp=ctx.createBiquadFilter(),g=ctx.createGain(),sg=ctx.createGain();o.type='sawtooth';o.frequency.value=f;s.frequency.value=f;
 lp.type='lowpass';lp.Q.value=4;lp.frequency.setValueAtTime(300+1700*vel,t);lp.frequency.setTargetAtTime(260,t,.07);o.connect(lp);lp.connect(g);s.connect(sg);sg.gain.value=.9;sg.connect(g);
 env(g,t,.006,.3*vel,.25,.17*vel,.03,t+dur);g.connect(instB);[o,s].forEach(x=>{x.start(t);x.stop(t+dur+.3);});}
function glock(t,n,vel,p=0){const out=pan(p,instB);[[1,1,1.3],[2.76,.32,.45],[5.4,.12,.18],[8.93,.05,.08]].forEach(([r,a,d])=>{const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.value=hz(n)*r;env(g,t,.002,.075*vel*a,d/3);o.connect(g);g.connect(out);o.start(t);o.stop(t+d*3);});}
function brass(t,n,dur,vel,p=0){const out=pan(p,instB),lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.Q.value=2;lp.frequency.setValueAtTime(700,t);lp.frequency.linearRampToValueAtTime(3400,t+.03);lp.frequency.setTargetAtTime(1300,t+.05,.1);lp.connect(g);g.connect(out);
 [-9,9].forEach(dt=>{const o=ctx.createOscillator();o.type='sawtooth';o.frequency.value=hz(n);o.detune.value=dt;o.connect(lp);o.start(t);o.stop(t+dur+.2);});env(g,t,.015,.06*vel,.2,.03*vel,.03,t+dur);}
/* Krar (lira etíope): dos triángulos desafinados y un filtro que se cierra rápido, con el clic de la uña. */
function krar(t,n,dur,vel,p=0){const out=pan(p,instB),lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.Q.value=3;lp.frequency.setValueAtTime(5200,t);lp.frequency.setTargetAtTime(750,t,.06);lp.connect(g);g.connect(out);
 [-7,7].forEach(dt=>{const o=ctx.createOscillator();o.type='triangle';o.frequency.value=hz(n);o.detune.value=dt;o.connect(lp);o.start(t);o.stop(t+dur+.5);});
 const sq=ctx.createOscillator(),sg=ctx.createGain();sq.type='square';sq.frequency.value=hz(n);sg.gain.value=.25;sq.connect(sg);sg.connect(lp);sq.start(t);sq.stop(t+dur+.5);
 env(g,t,.002,.1*vel,.22,.0001);const c=noise(t,.02,1.6),cg=ctx.createGain();cg.gain.value=.05*vel;c.connect(cg);cg.connect(out);}
/* Washint (flauta de bambú): entra resbalando desde abajo, vibrato tardío y soplo. */
function washint(t,n,dur,vel,p=0){const out=pan(p,instB),g=ctx.createGain(),o=ctx.createOscillator(),o2=ctx.createOscillator(),g2=ctx.createGain();o.type='sine';o2.type='triangle';g2.gain.value=.3;
 [o,o2].forEach(x=>{x.frequency.setValueAtTime(hz(n-2),t);x.frequency.exponentialRampToValueAtTime(hz(n),t+.09);vib(x,t,5.8,28,.18,dur);x.start(t);x.stop(t+dur+.3);});o.connect(g);o2.connect(g2);g2.connect(g);g.connect(out);
 const b=noise(t,dur+.2,1),bp=ctx.createBiquadFilter(),bg=ctx.createGain();bp.type='bandpass';bp.frequency.value=hz(n);bp.Q.value=5;b.connect(bp);bp.connect(bg);bg.connect(out);
 env(g,t,.05,.09*vel,.4,.07*vel,.08,t+dur);env(bg,t,.03,.05*vel,.15,.02*vel,.08,t+dur);}
/* Masenqo (violín de una cuerda): sierra con cuerpo de caja, vibrato ancho y ornamento que baja. */
function masenqo(t,n,dur,vel,p=0){const out=pan(p,instB),o=ctx.createOscillator(),body=ctx.createBiquadFilter(),lp=ctx.createBiquadFilter(),g=ctx.createGain();o.type='sawtooth';
 o.frequency.setValueAtTime(hz(n+1),t);o.frequency.exponentialRampToValueAtTime(hz(n),t+.12);vib(o,t,6.4,45,.12,dur);body.type='peaking';body.frequency.value=1100;body.Q.value=1.2;body.gain.value=9;lp.type='lowpass';lp.frequency.value=3600;
 o.connect(body);body.connect(lp);lp.connect(g);g.connect(out);env(g,t,.06,.075*vel,.3,.06*vel,.08,t+dur);o.start(t);o.stop(t+dur+.4);}
/* Vibráfono ethio-jazz: parciales 1 y 4 con trémolo del motor. */
function vibes(t,n,vel,p=0,dur=1.6){const out=pan(p,instB),g=ctx.createGain(),trem=ctx.createGain(),l=ctx.createOscillator(),lg=ctx.createGain();trem.gain.value=.75;l.frequency.value=5.5;lg.gain.value=.25;l.connect(lg);lg.connect(trem.gain);l.start(t);l.stop(t+dur+.2);
 [[1,1,dur],[4,.22,.35],[10,.05,.08]].forEach(([r,a,d])=>{const o=ctx.createOscillator(),og=ctx.createGain();o.frequency.value=hz(n)*r;env(og,t,.002,a,d/2.5);o.connect(og);og.connect(g);o.start(t);o.stop(t+d*2.5);});g.gain.value=.07*vel;g.connect(trem);trem.connect(out);}
/* Cuerdas: tres sierras desafinadas, ataque lento. */
function pad(t,n,dur,vel,p=0){const out=pan(p,instB),lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.frequency.value=2200;lp.connect(g);g.connect(out);
 [-11,0,11].forEach(dt=>{const o=ctx.createOscillator();o.type='sawtooth';o.frequency.value=hz(n);o.detune.value=dt;o.connect(lp);o.start(t);o.stop(t+dur+.8);});env(g,t,.35,.022*vel,1.5,.02*vel,.25,t+dur);}
function kick(t,v){const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.setValueAtTime(165,t);o.frequency.exponentialRampToValueAtTime(46,t+.09);env(g,t,.002,.95*v,.11);o.connect(g);g.connect(drumB);o.start(t);o.stop(t+.5);
 const n=noise(t,.01,1),ng=ctx.createGain();ng.gain.value=.25*v;n.connect(ng);ng.connect(drumB);}
function snare(t,v,p=0){const out=pan(p,drumB),n=noise(t,.3),bp=ctx.createBiquadFilter(),g=ctx.createGain();bp.type='bandpass';bp.frequency.value=1900;bp.Q.value=.7;env(g,t,.001,.42*v,.06);n.connect(bp);bp.connect(g);g.connect(out);
 const o=ctx.createOscillator(),og=ctx.createGain();o.type='triangle';o.frequency.setValueAtTime(200,t);o.frequency.exponentialRampToValueAtTime(160,t+.06);env(og,t,.001,.35*v,.03);o.connect(og);og.connect(out);o.start(t);o.stop(t+.25);}
function clap(t,v){const n=noise(t,.35),bp=ctx.createBiquadFilter(),g=ctx.createGain(),out=pan(.1,drumB);bp.type='bandpass';bp.frequency.value=1300;bp.Q.value=1.1;n.connect(bp);bp.connect(g);g.connect(out);
 g.gain.setValueAtTime(0,t);[0,.011,.023].forEach(d=>{g.gain.setValueAtTime(.35*v,t+d);g.gain.setTargetAtTime(.02,t+d+.001,.004);});g.gain.setValueAtTime(.3*v,t+.034);g.gain.setTargetAtTime(0,t+.035,.05);}
function hat(t,v,open=false){const n=noise(t,open?.5:.12,1.3),hp=ctx.createBiquadFilter(),g=ctx.createGain(),out=pan(-.25,drumB);hp.type='highpass';hp.frequency.value=7200;env(g,t,.001,.16*v,open?.1:.013);n.connect(hp);hp.connect(g);g.connect(out);}
function shaker(t,v){const n=noise(t,.12,.9),bp=ctx.createBiquadFilter(),g=ctx.createGain(),out=pan(.35,drumB);bp.type='bandpass';bp.frequency.value=6500;bp.Q.value=1.5;env(g,t,.012,.08*v,.018);n.connect(bp);bp.connect(g);g.connect(out);}
function crash(t,v){const n=noise(t,2.4,.8),hp=ctx.createBiquadFilter(),g=ctx.createGain();hp.type='highpass';hp.frequency.value=4200;env(g,t,.002,.2*v,.55);n.connect(hp);hp.connect(g);g.connect(drumB);}
function riser(t0,t1,v=.18){const n=noise(t0,t1-t0+.05),bp=ctx.createBiquadFilter(),g=ctx.createGain();bp.type='bandpass';bp.Q.value=3;bp.frequency.setValueAtTime(300,t0);bp.frequency.exponentialRampToValueAtTime(9000,t1);g.gain.setValueAtTime(0,t0);g.gain.linearRampToValueAtTime(v,t1);g.gain.setValueAtTime(0,t1+.01);n.connect(bp);bp.connect(g);g.connect(instB);}
/* 808: seno que cae de tono, saturado. */
function boom(t,v=1,st=0){const o=ctx.createOscillator(),g=ctx.createGain(),ws=ctx.createWaveShaper(),cv=new Float32Array(1024);for(let k=0;k<1024;k++){const x=k/511.5-1;cv[k]=Math.tanh(x*2.6);}ws.curve=cv;
 o.frequency.setValueAtTime(hz(45+st)*2.2,t);o.frequency.exponentialRampToValueAtTime(hz(45+st),t+.06);env(g,t,.003,.55*v,.35);o.connect(ws);ws.connect(g);g.connect(drumB);o.start(t);o.stop(t+1.6);}
/* ñam: golpe grave + chasquido. */
function bite(t,v=1){const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.setValueAtTime(220,t);o.frequency.exponentialRampToValueAtTime(70,t+.08);env(g,t,.002,.5*v,.05);o.connect(g);g.connect(vocB);o.start(t);o.stop(t+.3);
 const n=noise(t,.08,1),bp=ctx.createBiquadFilter(),ng=ctx.createGain();bp.type='bandpass';bp.frequency.value=2400;bp.Q.value=2;env(ng,t,.001,.3*v,.015);n.connect(bp);bp.connect(ng);ng.connect(vocB);}
function coin(t,v=1){const o=ctx.createOscillator(),g=ctx.createGain(),out=pan(.3,instB);o.type='square';o.frequency.setValueAtTime(hz(83),t);o.frequency.setValueAtTime(hz(88),t+.075);g.gain.setValueAtTime(.045*v,t);g.gain.setValueAtTime(.045*v,t+.075);g.gain.setTargetAtTime(0,t+.09,.12);o.connect(g);g.connect(out);o.start(t);o.stop(t+.8);}

/* ---------- 5. El arreglo: crece con kirby ---------- */
const hv=v=>v*(.88+H()*.24),ht=t=>t+(H()-.5)*.008;
for(let bar=0;bar<CH.length;bar++){const S=sec(bar),Z=tam(bar),cs=CH[bar].map(chord),nx=CH[bar+1]?chord(CH[bar+1][0]):cs[0],two=cs.length>1;
 const at=(step,push=8)=>two&&step>=push?cs[1]:cs[0],T=s=>ts(bar,s);
 const comp=(pat,push)=>pat.forEach(([s,d,v])=>{const c=at(s,push);c.notes.forEach((n,k)=>ep(ht(T(s))+k*.007,n,d*SPB/4,hv(v),(k-1.5)*.35));});
 function bs([s,d,k]){const c=k===k.toUpperCase()&&k!=='a'?at(s,0):cs[0],n=k==='a'?nx.bass-1:k.toLowerCase()==='o'?c.bass+12:k==='f'?c.fifth:c.bass;bass(ht(T(s)),n,d*SPB/4*.92,hv(k==='a'?.7:.85));}
 /* píxel: krar en Bati, clics y un Rhodes apenas */
 if(Z==='pixel'){const idx=[0,1,2,3,4,3,2,1];idx.forEach((i,k)=>krar(ht(T(k*2)),qn('bati',69,i+(bar%2&&k>4?1:0)),SPB*.45,hv(.8),(k%2?.3:-.3)));
  for(let s=0;s<16;s+=2)hat(ht(T(s)),s%4?.18:.3);if(bar>=2){kick(T(0),.5);comp([[0,16,.35]]);}if(bar===1)[12,14].forEach(s=>glock(T(s),[81,88][s===12?0:1],.6,.4));}
 /* crece: entra la banda */
 if(Z==='crece'){comp([[0,3,.8],[3,2,.45],[7,3,.7],[10,4,.6]],7);
  (two?[[0,3,'r'],[3,1,'o'],[6,1,'f'],[7,3,'R'],[10,1,'O'],[14,2,'a']]:[[0,3,'r'],[3,1,'o'],[6,2,'r'],[10,2,'f'],[14,2,'a']]).forEach(bs);
  [[0,.95],[7,.7],[10,.8]].forEach(([s,v])=>kick(ht(T(s)),v));[4,12].forEach(s=>{snare(ht(T(s)),.7);clap(ht(T(s)),.55);});for(let s=0;s<16;s++){hat(ht(T(s)),s%2?.22:.5);if(bar%2&&s>=12)hat(T(s)+SPB/8,.3);}
  [0,2,4,6,8,10,12,14].forEach((s,k)=>krar(ht(T(s)),qn('bati',69,[0,2,4,3][k%4]+(k>3?1:0)),SPB*.4,hv(.55),-.5));
  at(12,7).notes.slice(1).forEach((n,k)=>vibes(T(12)+k*.05,n+12,.9,.45));if(bar===6)boom(T(0),.8);}
 /* exponencial: se abre el filtro, washint en Ambassel, cuerdas que se inflan, la batería se va apretando */
 if(Z==='expo'){const k0=bar-10;comp([[0,7,.7],[8,8,.7]]);[[0,4,'r'],[4,4,'f'],[8,4,'R'],[12,4,'a']].forEach(bs);
  at(0).notes.forEach(n=>pad(T(0),n+12,SPB*2,.5+k0*.2,.2));at(8).notes.forEach(n=>pad(T(8),n+12,SPB*2,.6+k0*.2,-.2));
  (k0<2?[0,8]:[0,4,8,12]).forEach(s=>kick(T(s),.85));const hs=k0===0?4:k0===1?2:1;for(let s=0;s<16;s+=hs)hat(T(s),.35+k0*.05);
  const wa=[[[0,5],[8,7]],[[0,8],[8,7]],[[0,5],[8,1]],[[0,7],[8,4]]][k0];wa.forEach(([s,i])=>washint(T(s),qn('ambassel',57,i),SPB*1.9,.9,-.35));
  if(bar<13)snare(T(12),.75);else for(let s=0;s<16;s++)snare(T(s),.18+s*.045,(s%2?.2:-.2));}
 /* inmenso y todo: la banda entera, 808 en cada compás, krar en Tezeta a semicorcheas, cuerdas, vibráfono y metales */
 if(Z==='inmenso'||Z==='todo'){const up=Z==='todo'?2:0;comp([[0,2,.8],[3,2,.55],[6,2,.7],[8,2,.8],[11,2,.55],[14,2,.7]],6);
  for(let s=0;s<16;s+=2)bs([s,1.6,s===14?'a':(s>=6&&two)?(s%4?'O':'R'):(s%4?'o':'r')]);
  [0,4,8,12].forEach(s=>kick(ht(T(s)),.95));[4,12].forEach(s=>{snare(ht(T(s)),.7);clap(ht(T(s)),.8);});[2,6,10,14].forEach(s=>hat(ht(T(s)),.5,true));for(let s=0;s<16;s++)shaker(ht(T(s)),s%2?.45:.8);boom(T(0),1,up);
  for(let s=0;s<16;s++)krar(ht(T(s)),qn('tezeta',69+up,[0,1,2,3,4,3,2,1,0,1,2,4,3,2,1,0][s]),SPB*.22,hv(s%4?.35:.55),-.55);
  at(0,6).notes.forEach(n=>pad(T(0),n+12,SPB*3.8,.7,.15));
  if(bar%2)[12,13,14,15].forEach((s,k)=>vibes(T(s),at(s,6).notes[k]+24,.8,.55,.8));
  if([17,21,27].includes(bar))[12,14].forEach(s=>at(s,6).notes.slice(1).forEach(n=>brass(T(s),n+12,SPB*.4,1)));
  if(Z==='todo'){[[0,0],[8,1]].forEach(([s,j])=>washint(T(s),qn('tezeta',59+up,[4,3,2,1,0,1,2,3,4,3,2,1][(bar-24)*2+j]),SPB*1.9,.85,-.4));if(bar%2===0)crash(T(0),.7);}}
 /* frito: masenqo en Ambassel sobre pedal, 808 en cada tiempo, redoble y subida */
 if(Z==='frito'){if(bar===22){[[0,0,2],[8,1,1],[12,2,1]].forEach(([s,i,d])=>masenqo(T(s),qn('ambassel',57,i),SPB*d*.95,1,.3));for(let s=0;s<16;s++){bass(T(s),33+(s%2?12:0),SPB/4*.8,.7);hat(T(s),s%2?.25:.5);}[0,3,6,10,12].forEach(s=>kick(T(s),.85));}
  else{[[0,3,2],[8,2,1],[12,-1,1]].forEach(([s,i,d])=>masenqo(T(s),qn('ambassel',57+12,i),SPB*d*.95,1,.3));[[0,6,'r'],[8,6,'R'],[14,2,'a']].forEach(bs);[0,8].forEach(s=>kick(T(s),.9));for(let s=0;s<16;s++)snare(T(s),.15+s*.05,(s%2?.25:-.25));riser(T(0),ts(24,0));}
  [0,4,8,12].forEach(s=>boom(T(s),.95,s/4));}
 /* vuelve a ser un píxel: se cierra el filtro, queda el krar y el vibráfono */
 if(Z==='vuelve'){if(bar===30){comp([[0,2,.7],[3,2,.5],[6,2,.6],[8,4,.6]],6);for(let s=0;s<16;s+=2)bs([s,1.6,(s>=6&&two)?'R':'r']);[0,4,8].forEach(s=>kick(T(s),.8));[4,12].forEach(s=>clap(T(s),.6));}
  else{comp([[0,24,.7]]);bass(T(0),cs[0].bass,SPB*5,.7);crash(T(0),.8);for(let k=0;k<12;k++)krar(T(0)+.1+k*SPB/2,qn('bati',71,[4,3,2,1,0,1,2,1,0,-1,-2,-3][k]),SPB*.45,.7-k*.03,(k%2?.4:-.4));
   for(let k=0;k<10;k++)vibes(T(0)+.3+k*SPB/4,[71,73,75,78,80][k%5]+12*Math.floor(k/5)+12,.6,(k%2?.5:-.5),1.2);}}
 if([14,24].includes(bar)){crash(T(0),1);for(let k=0;k<8;k++)glock(T(0)+k*.03,[69,71,73,76,78,81,83,85][k]+(bar>=24?2:0),.55,.5);}}
riser(tb(10),tb(14),.14);
[[15,2],[15,2.5],[29,2],[29,2.5],[29,3]].forEach(([b,x])=>bite(tb(b,x)));[[8,0],[8,1],[8,2]].forEach(([b,x])=>bite(tb(b,x),.6));
coin(tb(2,3.5));coin(tb(19,2),.8);boom(tb(32,0),1.1,-10);krar(tb(33,.2),47,1.2,.9);coin(tb(33,1.6),.6);

/* ---------- 6. Las voces ---------- */
const lines=[...lead];
lead.filter(x=>x.coro).forEach(x=>lines.push({...x,note:x.note-12,carrier:'pulso',gain:.42,pan:.45,formant:1.1}));
lead.filter(x=>x.coro).forEach(x=>lines.push({...x,note:x.note-5,carrier:'sierra',gain:.2,pan:-.45,vib:30}));
let sung=0;for(const x of lines){const r=await sing(x.syl,x.note,x.D,{carrier:x.carrier||'sierra',formant:x.formant??1.24,vib:x.vib??26});
 const s=ctx.createBufferSource(),g=ctx.createGain();s.buffer=r.buf;g.gain.value=.5*r.norm*(x.gain??1);s.connect(g);g.connect(pan(x.pan||0,vocB));s.start(Math.max(0,x.t-r.vt));sung++;}

const out=await ctx.startRendering(),L=out.getChannelData(0),R=out.getChannelData(1);let pk=0;for(let k=0;k<L.length;k++)pk=Math.max(pk,Math.abs(L[k]),Math.abs(R[k]));const g=.93/pk;
const rms=[];for(let s=0;s<Math.floor(LEN);s+=4){let a=0;const i0=s*SR,i1=Math.min(L.length,(s+4)*SR);for(let k=i0;k<i1;k++)a+=L[k]*L[k];rms.push(+(Math.sqrt(a/(i1-i0))*g).toFixed(3));}
const pcm=new Int16Array(L.length*2);for(let k=0;k<L.length;k++){pcm[k*2]=Math.max(-1,Math.min(1,L[k]*g))*32767;pcm[k*2+1]=Math.max(-1,Math.min(1,R[k]*g))*32767;}
const u8=new Uint8Array(pcm.buffer);let b64='';for(let k=0;k<u8.length;k+=32768)b64+=String.fromCharCode(...u8.subarray(k,k+32768));
return {b64:btoa(b64),peak:pk,rms,sung,seconds:LEN};};
