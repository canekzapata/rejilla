/* «modo suspensión» (yoshi es un vector, parte 2) — canción de ~1 min: llega Jigglypuff, canta una canción de cuna en 8 bits y todo se suspende.
   Mismo motor que la parte 1; cambian semilla, tempo, tonalidad (Mi bemol → Fa), partitura, bossa en el verso y campanitas de sueño.
   La voz es el vocoder por formantes de consola (static/lectura/musica.js), cargado como copia parchada en memoria:
   canta la nota exacta de cada sílaba (v.canto), formantes un poco más arriba y vibrato en las notas largas.
   Todo lo demás (Rhodes FM, bajo, batería, glockenspiel, metales) es síntesis Web Audio sembrada: misma semilla, misma canción.
   Se corre dentro del visor de lectura (necesita Lectura, LecturaCinetica…): window.cancion(opciones) → WAV en base64. */
'use strict';
window.cancion=async function(opts={}){
const SEED='yoshi-es-un-vector-2-modo-suspension',BPM=118,SPB=60/BPM,T0=.35,SR=44100,LEN=70;
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
async function sing(syl,note,D,{carrier='sierra',formant=1.16,vib=24}={}){
 const piece={...p0,seed:SEED,music:CM.normalize({...base,vozCarrier:carrier,voices:[{instrument:'none',octave:4,gain:.7,pan:0,entry:'none',words:false,gesture:false}]})};
 let v,ev;for(let n=1;n<=48;n++){v={i:0,key:'s',born:0,duration:D/.95,text:stretch(syl,n),effect:'fade',hold:0,speak:'vocoder',canto:note};ev=CM.speechEvents(piece,v)[0];if(ev.dur>=D*.97)break;}
 window.CANTA_FORMANT=formant;window.CANTA_VIB=vib;
 const buf=await CM.render(piece,[v],ev.dur+.6,SR),vt=(ev.steps.find(s=>s.v)||{t:0}).t;
 let pk=0;for(let c=0;c<2;c++){const d=buf.getChannelData(c);for(let k=0;k<d.length;k++)pk=Math.max(pk,Math.abs(d[k]));}
 return {buf,vt,norm:pk>0?1/pk:1};}

/* ---------- 2. La letra y la melodía: sílaba:nota:tiempos (· = silencio) ---------- */
const NOTE={C:0,D:2,E:4,F:5,G:7,A:9,B:11};
const nm=s=>{const m=/^([A-G])(b|#)?(-?\d)$/.exec(s);if(!m)throw Error('nota: '+s);return 12*(+m[3]+1)+NOTE[m[1]]+(m[2]==='b'?-1:m[2]==='#'?1:0);};
function score(str,bar,tr=0,o={}){const out=[];let beat=0;for(const tok of str.trim().split(/\s+/)){const [a,b,c]=tok.split(':');if(a==='-'){beat+=+b;continue;}out.push({syl:a,note:nm(b)+tr,t:tb(bar,beat),D:+c*SPB-.035,...o});beat+=+c;}return out;}
const INTRO=`o:Bb4:.5 tra:C5:.5 vez:Eb5:1 -:2`;
const VERSO=`-:.5 yo:G4:.5 shi:Bb4:.5 si:C5:.5 gue:D5:.5 sien:Eb5:.5 do:D5:1
 un:C5:.5 vec:Bb4:.5 tor:G4:2 -:1
 -:.5 fox:Ab4:.5 si:C5:.5 gue:Eb5:.5 sin:G5:.5 ca:F5:.5 ber:Eb5:1
 -:1 ay:D5:.5 ay:F5:.5 -:2
 -:.5 pe:G4:.5 ro:Bb4:.5 lle:D5:.5 go:F5:1 jig:Eb5:.5 gly:Db5:.5
 puff:C5:1.5 -:.5 y:Ab4:.5 se:B4:.5 pu:C5:.5 so:Eb5:.5
 a:D5:.5 can:D5:.5 tar:Bb4:1 -:.5 la:C5:.5 la:E5:.5 la:G5:.5
 la:Ab5:1 la:G5:.5 la:F5:.5 -:2`;
const PRE=`u:C5:.5 na:C5:.5 can:C5:.5 cion:Bb4:.5 de:C5:.5 cu:D5:.5 na:Bb4:1
 en:C5:.5 o:Eb5:.5 cho:D5:.5 bits:C5:1 -:1.5
 y:Db5:.5 to:Db5:.5 do:Eb5:.5 el:F5:.5 mun:Gb5:1 do:F5:1
 se:F5:.5 duer:Eb5:.5 me:F5:2 -:1`;
const CORO_A=`mo:Eb5:.5 do:F5:.5 sus:G5:.5 pen:Ab5:.5 sion:Bb5:2
 -:.5 sus:Ab5:.5 pen:G5:.5 sion:F5:.5 de:Eb5:.5 a:D5:.5 mor:Eb5:1
 cie:C5:.5 rro:C5:.5 los:C5:.5 o:Bb4:.5 jos:C5:.5 guar:Eb5:.5 do:F5:.5 mi:G5:.5
 es:F5:.5 ta:Eb5:.5 do:Eb5:2 -:1`;
const CORO_B=`si:Eb5:.5 me:F5:.5 des:G5:.5 pier:Ab5:.5 tas:Bb5:.5 con:C6:.5 u:Bb5:.5 na:Ab5:.5
 te:G5:1 cla:E5:1 clic:G5:.5 -:1.5
 vuel:Ab5:.5 vo:G5:.5 a:F5:.5 qui:Eb5:.5 don:D5:.5 de:Eb5:.5 me:F5:.5 de:G5:.5
 jas:F5:.5 te:Eb5:1.5 -:2`;
const BREAK=`jig:Db5:.5 gly:Eb5:.5 jig:F5:.5 gly:Gb5:.5 jig:Ab5:.5 gly:Bb5:.5 puff:Ab5:1
 jig:C5:.5 gly:D5:.5 jig:E5:.5 gly:F5:.5 jig:G5:.5 gly:A5:.5 puff:Bb5:1`;
const ULTIMO_B=`gra:Eb5:.5 cias:F5:.5 por:G5:.5 can:Ab5:.5 tar:Bb5:.5 jig:C6:.5 gly:Bb5:.5 puff:Ab5:.5
 bue:G5:1 nas:E5:1 no:F5:.5 ches:G5:1.5`;
const FINAL=`o:A4:1 ya:C5:.5 su:D5:.5 mi:F5:2`;
const FIN=`se:F2:.5 sion:F2:.75 guar:F2:.5 da:F2:.25 da:F2:1.5`;
/* Las partituras de varios compases van un compás por renglón. */
const NL=String.fromCharCode(10);
function scoreBars(str,bar0,tr=0,o={}){return str.trim().split(NL).flatMap((l,k)=>score(l,bar0+k,tr,o));}
const lead=[...score(INTRO,1),...scoreBars(VERSO,2),...scoreBars(PRE,10),...scoreBars(CORO_A+NL+CORO_B,14,0,{coro:1}),
 ...scoreBars(BREAK,22,0,{carrier:'pulso'}),...scoreBars(CORO_A+NL+ULTIMO_B,24,2,{coro:1}),...score(FINAL,30),...score(FIN,32,0,{carrier:'coro',formant:.9,vib:0,gain:.8})];

/* ---------- 3. La armonía: un compás = uno o dos acordes ---------- */
const CH=[['Abmaj9'],['Bb13'],
 ['Ebmaj7'],['Cm9'],['Abmaj7'],['Bb7sus','Bb7'],['Ebmaj7','Eb7'],['Abmaj7','Db7'],['Gm7','C7'],['Fm7','Bb7'],
 ['Fm9','Gm7'],['Abmaj7','Adim7'],['Gbmaj7'],['Bb7sus','Bb7b9'],
 ['Abmaj7','Bb7'],['Gm7','Cm7'],['Fm7','Bb7'],['Ebmaj7','Eb7'],['Abmaj7','Bb/Ab'],['Gm7','C7'],['Fm7','Bb7'],['Eb6'],
 ['Gbmaj7','Ab7'],['C7sus','C7b9'],
 ['Bbmaj7','C7'],['Am7','Dm7'],['Gm7','C7'],['Fmaj7','F7'],['Bbmaj7','C/Bb'],['Am7','D7'],
 ['Gm7','C7'],['Fmaj9']];
const PC={C:0,'C#':1,Db:1,D:2,'D#':3,Eb:3,E:4,F:5,'F#':6,Gb:6,G:7,'G#':8,Ab:8,A:9,'A#':10,Bb:10,B:11};
const QUAL={maj7:[4,7,11,14],maj9:[4,11,14,19],6:[4,7,9,14],m7:[3,7,10,14],m9:[3,10,14,17],7:[4,9,10,14],13:[4,9,10,14],'7b9':[4,7,10,13],'7sus':[5,7,10,14],dim7:[3,6,9,12],'':[4,7,12,14]};
function chord(sym){const m=/^([A-G][b#]?)(.*?)(?:\/([A-G][b#]?))?$/.exec(sym),root=PC[m[1]],iv=QUAL[m[2]];if(!iv)throw Error('acorde: '+sym);
 let notes=iv.map(i=>48+root+i);while(notes[0]<53)notes=notes.map(n=>n+12);while(notes[0]>=64)notes=notes.map(n=>n-12);
 const bp=m[3]?PC[m[3]]:root;return {notes,bass:28+((bp-4+12)%12),fifth:28+((root-4+12)%12)+7};}
const sec=b=>b<2?'intro':b<10?'verso':b<14?'pre':b<22?'coro':b<24?'break':b<30?'coro':b<31?'coro':'final';

/* ---------- 4. La mezcla ---------- */
const ctx=new OfflineAudioContext(2,Math.ceil(LEN*SR),SR),H=rng('humano');
const master=ctx.createGain(),comp=ctx.createDynamicsCompressor();master.gain.value=.8;comp.threshold.value=-14;comp.ratio.value=3;comp.attack.value=.01;comp.release.value=.15;master.connect(comp);comp.connect(ctx.destination);
const instB=ctx.createGain(),vocB=ctx.createGain(),drumB=ctx.createGain();instB.gain.value=opts.inst??1;drumB.gain.value=opts.drums??1;vocB.gain.value=opts.voc??1.6;[instB,vocB,drumB].forEach(b=>b.connect(master));
const verb=ctx.createConvolver(),vr=rng('reverb'),ir=ctx.createBuffer(2,SR*2.4,SR);for(let c=0;c<2;c++){const d=ir.getChannelData(c);for(let k=0;k<d.length;k++)d[k]=(vr()*2-1)*Math.exp(-k/SR*2.6)*(k<SR*.01?k/(SR*.01):1);}verb.buffer=ir;
const verbG=ctx.createGain();verbG.gain.value=.5;verb.connect(verbG);verbG.connect(master);
const send=(from,g)=>{const s=ctx.createGain();s.gain.value=g;from.connect(s);s.connect(verb);};send(instB,.16);send(vocB,.28);send(drumB,.06);
const dl=ctx.createDelay(2),dfb=ctx.createGain(),dlp=ctx.createBiquadFilter(),dsend=ctx.createGain();dl.delayTime.value=SPB*.75;dfb.gain.value=.3;dlp.type='lowpass';dlp.frequency.value=3200;dsend.gain.value=.2;vocB.connect(dsend);dsend.connect(dl);dl.connect(dlp);dlp.connect(dfb);dfb.connect(dl);dlp.connect(master);
const nb=ctx.createBuffer(1,SR*2,SR),nr=rng('ruido');{const d=nb.getChannelData(0);for(let k=0;k<d.length;k++)d[k]=nr()*2-1;}
const pan=(p,to)=>{const s=ctx.createStereoPanner();s.pan.value=Math.max(-1,Math.min(1,p));s.connect(to);return s;};
const env=(g,t,a,peak,dec,sus=0.0001,tail=.05,end)=>{g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(peak,t+a);g.gain.setTargetAtTime(Math.max(sus,.0001),t+a,dec);if(end!=null)g.gain.setTargetAtTime(0,end,tail);};
function noise(t,dur,rate=1){const s=ctx.createBufferSource();s.buffer=nb;s.loop=true;s.playbackRate.value=rate;s.start(t,H()*1.5);s.stop(t+dur);return s;}

/* Rhodes FM: portadora + moduladora 1:1 con índice que cae, más la «púa» metálica del ataque. */
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
function kick(t,v){const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.setValueAtTime(165,t);o.frequency.exponentialRampToValueAtTime(46,t+.09);env(g,t,.002,.95*v,.11);o.connect(g);g.connect(drumB);o.start(t);o.stop(t+.5);
 const n=noise(t,.01,1),ng=ctx.createGain();ng.gain.value=.25*v;n.connect(ng);ng.connect(drumB);}
function snare(t,v,p=0){const out=pan(p,drumB),n=noise(t,.3),bp=ctx.createBiquadFilter(),g=ctx.createGain();bp.type='bandpass';bp.frequency.value=1900;bp.Q.value=.7;env(g,t,.001,.42*v,.06);n.connect(bp);bp.connect(g);g.connect(out);
 const o=ctx.createOscillator(),og=ctx.createGain();o.type='triangle';o.frequency.setValueAtTime(200,t);o.frequency.exponentialRampToValueAtTime(160,t+.06);env(og,t,.001,.35*v,.03);o.connect(og);og.connect(out);o.start(t);o.stop(t+.25);}
function rim(t,v){const n=noise(t,.05,1.4),bp=ctx.createBiquadFilter(),g=ctx.createGain(),out=pan(-.2,drumB);bp.type='bandpass';bp.frequency.value=3200;bp.Q.value=4;env(g,t,.001,.5*v,.012);n.connect(bp);bp.connect(g);g.connect(out);
 const o=ctx.createOscillator(),og=ctx.createGain();o.type='triangle';o.frequency.value=820;env(og,t,.001,.22*v,.012);o.connect(og);og.connect(out);o.start(t);o.stop(t+.1);}
function clap(t,v){const n=noise(t,.35),bp=ctx.createBiquadFilter(),g=ctx.createGain(),out=pan(.1,drumB);bp.type='bandpass';bp.frequency.value=1300;bp.Q.value=1.1;n.connect(bp);bp.connect(g);g.connect(out);
 g.gain.setValueAtTime(0,t);[0,.011,.023].forEach(d=>{g.gain.setValueAtTime(.35*v,t+d);g.gain.setTargetAtTime(.02,t+d+.001,.004);});g.gain.setValueAtTime(.3*v,t+.034);g.gain.setTargetAtTime(0,t+.035,.05);}
function hat(t,v,open=false){const n=noise(t,open?.5:.12,1.3),hp=ctx.createBiquadFilter(),g=ctx.createGain(),out=pan(-.25,drumB);hp.type='highpass';hp.frequency.value=7200;env(g,t,.001,.16*v,open?.1:.013);n.connect(hp);hp.connect(g);g.connect(out);}
function shaker(t,v){const n=noise(t,.12,.9),bp=ctx.createBiquadFilter(),g=ctx.createGain(),out=pan(.35,drumB);bp.type='bandpass';bp.frequency.value=6500;bp.Q.value=1.5;env(g,t,.012,.08*v,.018);n.connect(bp);bp.connect(g);g.connect(out);}
function crash(t,v){const n=noise(t,2.4,.8),hp=ctx.createBiquadFilter(),g=ctx.createGain();hp.type='highpass';hp.frequency.value=4200;env(g,t,.002,.2*v,.55);n.connect(hp);hp.connect(g);g.connect(drumB);}
function riser(t0,t1,v=.18){const n=noise(t0,t1-t0+.05),bp=ctx.createBiquadFilter(),g=ctx.createGain();bp.type='bandpass';bp.Q.value=3;bp.frequency.setValueAtTime(300,t0);bp.frequency.exponentialRampToValueAtTime(9000,t1);g.gain.setValueAtTime(0,t0);g.gain.linearRampToValueAtTime(v,t1);g.gain.setValueAtTime(0,t1+.01);n.connect(bp);bp.connect(g);g.connect(instB);}
/* La moneda: dos notas de onda cuadrada. */
function dormir(t,v=1,root=75){[0,-3,-5,-8,-12].forEach((d,k)=>glock(t+k*.11,root+12+d,.7*v,k%2?.5:-.5));}
function coin(t,v=1){const o=ctx.createOscillator(),g=ctx.createGain(),out=pan(.3,instB);o.type='square';o.frequency.setValueAtTime(hz(83),t);o.frequency.setValueAtTime(hz(88),t+.075);g.gain.setValueAtTime(.045*v,t);g.gain.setValueAtTime(.045*v,t+.075);g.gain.setTargetAtTime(0,t+.09,.12);o.connect(g);g.connect(out);o.start(t);o.stop(t+.8);}

/* ---------- 5. El arreglo, compás por compás ---------- */
const hv=v=>v*(.88+H()*.24),ht=t=>t+(H()-.5)*.008;
for(let bar=0;bar<CH.length;bar++){const S=sec(bar),cs=CH[bar].map(chord),nx=CH[bar+1]?chord(CH[bar+1][0]):cs[0],two=cs.length>1;
 const at=(step,push=8)=>two&&step>=push?cs[1]:cs[0],T=s=>ts(bar,s);
 const comp=(pat,push)=>pat.forEach(([s,d,v])=>{const c=at(s,push);c.notes.forEach((n,k)=>ep(ht(T(s))+k*.007,n,d*SPB/4,hv(v),(k-1.5)*.35));});
 if(S==='intro'){comp([[0,16,.6]]);const cuna=bar===0?[[0,79,4],[4,82,2],[6,80,2],[8,79,4],[12,75,4]]:[[0,77,4],[4,79,2],[6,77,2],[8,74,6],[14,70,2]];cuna.forEach(([s,n])=>glock(T(s),n,.9,.2));bass(T(0),cs[0].bass,SPB*4,.5);
  if(bar===1){[0,2,4,6,8,10,12,14].forEach(s=>hat(ht(T(s)),s%4?.35:.55));kick(T(0),.8);[12,14,15].forEach(s=>snare(T(s),.35+s*.02));}}
 if(S==='verso'){comp([[0,3,.8],[3,2,.45],[7,3,.7],[10,4,.6]],7);
  (two?[[0,3,'r'],[3,1,'o'],[6,1,'f'],[7,3,'R'],[10,1,'O'],[14,2,'a']]:[[0,3,'r'],[3,1,'o'],[6,2,'r'],[10,2,'f'],[14,2,'a']]).forEach(bs);
  [[0,.9],[6,.55],[8,.8],[14,.55]].forEach(([s,v])=>kick(ht(T(s)),v));[0,3,6,10,12].forEach(s=>rim(ht(T(s)),.8));for(let s=0;s<16;s++)shaker(ht(T(s)),s%2?.35:.7);
  if(bar===9)[13,14,15].forEach(s=>snare(T(s),.5));}
 if(S==='pre'){comp([[0,7,.7],[8,8,.7]]);[[0,4,'r'],[4,4,'f'],[8,4,'R'],[12,4,'a']].forEach(bs);[0,8].forEach(s=>kick(T(s),.85));[0,4,8,12].forEach(s=>hat(T(s),.45));
  if(bar<13)snare(T(12),.75);else for(let s=0;s<16;s++)snare(T(s),.18+s*.045,(s%2?.2:-.2));}
 if(S==='coro'){comp([[0,2,.8],[3,2,.55],[6,2,.7],[8,2,.8],[11,2,.55],[14,2,.7]],6);
  for(let s=0;s<16;s+=2)bs([s,1.6,s===14?'a':(s>=6&&two)?(s%4?'O':'R'):(s%4?'o':'r')]);
  [0,4,8,12].forEach(s=>kick(ht(T(s)),.95));[4,12].forEach(s=>{snare(ht(T(s)),.7);clap(ht(T(s)),.8);});[2,6,10,14].forEach(s=>hat(ht(T(s)),.5,true));for(let s=0;s<16;s++)shaker(ht(T(s)),s%2?.45:.8);
  if(bar%2)[12,13,14,15].forEach((s,k)=>glock(T(s),at(s,6).notes[k]+24,.7,.6));
  if([17,21,27].includes(bar))[12,14].forEach(s=>at(s,6).notes.slice(1).forEach(n=>brass(T(s),n+12,SPB*.4,1)));}
 if(S==='break'){if(bar===22){comp([[0,1,.8],[2,1,.8],[3,1,.8],[6,1,.8],[10,2,.8],[12,1,.8],[14,1,.8]]);for(let s=0;s<16;s++){bass(T(s),at(s).bass+(s%2?12:0),SPB/4*.8,.7);hat(T(s),s%2?.25:.5);}[0,3,6,10,12].forEach(s=>kick(T(s),.85));}
  else{comp([[0,6,.7],[8,8,.7]]);[[0,6,'r'],[8,6,'R'],[14,2,'a']].forEach(bs);[0,8].forEach(s=>kick(T(s),.9));for(let s=0;s<16;s++)snare(T(s),.15+s*.05,(s%2?.25:-.25));riser(T(0),ts(24,0));}}
 if(S==='final'){comp([[0,28,.85]]);bass(T(0),cs[0].bass,SPB*7,.8);kick(T(0),1);crash(T(0),1);
  for(let k=0;k<16;k++)glock(T(0)+.15+k*SPB/8,[65,67,69,72,74][k%5]+12*Math.floor(k/5)+12,.6+k*.02,(k%2?.6:-.6));}
 if([14,24,30].includes(bar)){crash(T(0),.9);for(let k=0;k<8;k++)glock(T(0)+k*.03,[70,72,75,77,79,82,84,87][k]+(bar>=24?2:0),.55,.5);}
 function bs([s,d,k]){const c=k===k.toUpperCase()&&k!=='a'?at(s,0):cs[0],n=k==='a'?nx.bass-1:k.toLowerCase()==='o'?c.bass+12:k==='f'?c.fifth:c.bass;bass(ht(T(s)),n,d*SPB/4*.92,hv(k==='a'?.7:.85));}}
riser(tb(10),tb(14),.14);dormir(tb(9,2.2));dormir(tb(13,2.5),.9,70);coin(tb(19,2),.8);coin(tb(22,0),.7);dormir(tb(33,.4),1.1,77);

/* ---------- 6. Las voces ---------- */
const lines=[...lead];
lead.filter(x=>x.coro).forEach(x=>lines.push({...x,note:x.note-12,carrier:'pulso',gain:.42,pan:.45,formant:1.05}));
lead.filter(x=>x.coro).forEach(x=>lines.push({...x,note:x.note-5,carrier:"sierra",gain:.2,pan:-.45,vib:30}));
let sung=0;for(const x of lines){const r=await sing(x.syl,x.note,x.D,{carrier:x.carrier||'sierra',formant:x.formant??1.16,vib:x.vib??24});
 const s=ctx.createBufferSource(),g=ctx.createGain();s.buffer=r.buf;g.gain.value=.5*r.norm*(x.gain??1);s.connect(g);g.connect(pan(x.pan||0,vocB));s.start(Math.max(0,x.t-r.vt));sung++;}

const out=await ctx.startRendering(),L=out.getChannelData(0),R=out.getChannelData(1);let pk=0;for(let k=0;k<L.length;k++)pk=Math.max(pk,Math.abs(L[k]),Math.abs(R[k]));const g=.93/pk;
const rms=[];for(let s=0;s<Math.floor(LEN);s+=5){let a=0;const i0=s*SR,i1=Math.min(L.length,(s+5)*SR);for(let k=i0;k<i1;k++)a+=L[k]*L[k];rms.push(+(Math.sqrt(a/(i1-i0))*g).toFixed(3));}
const pcm=new Int16Array(L.length*2);for(let k=0;k<L.length;k++){pcm[k*2]=Math.max(-1,Math.min(1,L[k]*g))*32767;pcm[k*2+1]=Math.max(-1,Math.min(1,R[k]*g))*32767;}
const u8=new Uint8Array(pcm.buffer);let b64='';for(let k=0;k<u8.length;k+=32768)b64+=String.fromCharCode(...u8.subarray(k,k+32768));
return {b64:btoa(b64),peak:pk,rms,sung,seconds:LEN};};
