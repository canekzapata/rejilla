/* «buenas noches, dulces sueños» (yoshi es un vector, parte 14) — ~98 s de canción de cuna en 3/4 a 84 bpm, Fa mayor.
   En Fountain of Dreams, de noche: Jigglypuff canta y todos se van durmiendo. Kirby con su gorrito, Yoshi en su huevito, Pikachu apaga
   su chispa, Pichu también. Cada uno bosteza (su voz del juego afinada, bajando) y se sale del coro. Jigglypuff se enoja porque nadie la
   oye y saca su plumón (el meme del anime). Al final hasta ella usa Descanso.
   El narrador es el vocoder de consola, bajito y claro; Jigglypuff y el coro son voces del juego afinadas con TD-PSOLA (voces.py →
   voces_*.wav). La banda: cajita de música, celesta, arpa Karplus-Strong, cuerdas suaves, colchón y bajo de vals (1 · 2 3).
   Se corre dentro del visor de lectura: window.cancion(opciones) → WAV. */
'use strict';
window.cancion=async function(opts={}){
const DIR='/meleeviewer/output/Arte/2026-10-03_yoshi_es_un_vector_14_buenas_noches/';
const SEED='yoshi-es-un-vector-14-buenas-noches',BPM=84,SPB=60/BPM,BEATS=3,BAR=SPB*BEATS,T0=.35,SR=44100,LEN=100,NBAR=44;
const tb=(bar,beat=0)=>T0+(bar*BEATS+beat)*SPB;
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
async function sing(syl,note,D,{carrier='sierra',formant=1.04,vib=16}={}){
 const piece={...p0,seed:SEED,music:CM.normalize({...base,vozCarrier:carrier,voices:[{instrument:'none',octave:4,gain:.7,pan:0,entry:'none',words:false,gesture:false}]})};
 let v,ev;for(let n=1;n<=48;n++){v={i:0,key:'s',born:0,duration:D/.95,text:stretch(syl,n),effect:'fade',hold:0,speak:'vocoder',canto:note};ev=CM.speechEvents(piece,v)[0];if(ev.dur>=D*.97)break;}
 window.CANTA_FORMANT=formant;window.CANTA_VIB=vib;
 const buf=await CM.render(piece,[v],ev.dur+.6,SR),vt=(ev.steps.find(s=>s.v)||{t:0}).t;
 let pk=0;for(let c=0;c<2;c++){const d=buf.getChannelData(c);for(let k=0;k<d.length;k++)pk=Math.max(pk,Math.abs(d[k]));}
 return {buf,vt,norm:pk>0?1/pk:1};}

/* ---------- 2. La letra (sílaba:nota:tiempos; compases de 3 tiempos, uno por renglón; voces.py y video.html la leen de aquí) ---------- */
const NOTE={C:0,D:2,E:4,F:5,G:7,A:9,B:11};
const nm=s=>{const m=/^([A-G])(b|#)?(-?\d)$/.exec(s);if(!m)throw Error('nota: '+s);return 12*(+m[3]+1)+NOTE[m[1]]+(m[2]==='b'?-1:m[2]==='#'?1:0);};
function score(str,bar,tr=0,o={}){const out=[];let beat=0;for(const tok of str.trim().split(/\s+/)){const [a,b,c]=tok.split(':');if(a==='-'){beat+=+b;continue;}out.push({syl:a,note:nm(b)+tr,t:tb(bar,beat),D:+c*SPB-.03,...o});beat+=+c;}return out;}
const NL=String.fromCharCode(10);
function scoreBars(str,bar0,tr=0,o={}){return str.trim().split(NL).flatMap((l,k)=>score(l,bar0+k,tr,o));}
const VERSO=`ya:A4:1 sea:C5:1 pa:F5:1
 go:E5:1 la:D5:.5 te:C5:.5 le:C5:1
 guar:D5:1 das:F5:1 te:A5:1
 la:G5:.5 par:F5:.5 ti:D5:1 da:F5:1
 el:C5:1 con:F5:1 trol:A5:1
 en:G5:.5 su:E5:.5 ca:C5:1 ji:D5:.5 ta:E5:.5
 yla:D5:1 lu:F5:1 na:Bb5:1
 en:A5:1 drim:G5:1 lan:E5:1`;
const CORO=`bue:F5:1 nas:G5:1 no:A5:1
 ches:G5:2 -:1
 dul:E5:1 ces:F5:1 sue:G5:1
 ños:A5:2 -:1
 kir:D5:1 by:F5:1 trae:Bb5:1
 su:A5:.5 go:G5:.5 rri:E5:1 to:C5:1
 yo:A5:1 shi:G5:1 duer:F5:1
 meen:E5:.5 su:D5:.5 hue:E5:1 vi:G5:.5 to:F5:.5`;
const VERSO2=`cuen:A4:.5 ta:A4:.5 o:C5:.5 ve:F5:.5 jas:F5:1
 no:E5:.5 po:E5:.5 ke:D5:.5 bo:C5:.5 las:C5:1
 que:D5:.5 ma:F5:.5 ña:A5:.5 na:A5:.5 hay:G5:1
 re:F5:.5 van:D5:.5 cha:F5:2
 pi:C5:.5 ka:C5:.5 chua:F5:.5 pa:F5:.5 ga:A5:1
 su:G5:.5 chis:E5:.5 pa:C5:2
 jig:D5:.5 gly:F5:.5 puff:G5:.5 can:Bb5:1 ta:A5:.5
 ba:G5:.5 ji:E5:.5 to:C5:2`;
const PUENTE=`oi:A5:1 gan:A5:2
 no:F5:.5 se:F5:.5 duer:Bb5:1 man:A5:1
 y:D5:.5 sa:F5:.5 ca:G5:1 su:G5:1
 plu:E5:1 mon:C5:2`;
const CORO2=`bue:F5:1 nas:G5:1 no:A5:1
 ches:G5:2 -:1
 dul:E5:1 ces:F5:1 sue:G5:1
 ños:A5:2 -:1
 has:D5:1 ta:F5:1 jig:Bb5:.5 gly:A5:.5
 puff:G5:1 des:E5:.5 can:D5:.5 sa:C5:1
 dul:A5:1 ces:G5:1 sue:F5:1
 ños:F5:3`;
const OUTRO=`bue:C5:1 nas:A4:1 no:G4:1
 ches:F4:3`;
const SECC=[['intro',0,4],['verso',4,12],['coro',12,20],['verso2',20,28],['puente',28,32],['coro2',32,40],['outro',40,44]];
const lead=[...scoreBars(VERSO,4),...scoreBars(CORO,12,0,{coro:1}),...scoreBars(VERSO2,20),...scoreBars(PUENTE,28,0,{formant:1.1,vib:6}),...scoreBars(CORO2,32,0,{coro:1}),...scoreBars(OUTRO,40,0,{formant:.98})];

/* ---------- 3. La armonía ---------- */
const CH=['F','C','Dm','Bb', 'F','C','Dm','Bb','F','C','Bb','C7', 'Bb','C','Am','Dm','Gm','C','F','C', 'F','C','Dm','Bb','F','C','Bb','C', 'Dm','Bb','Gm','C7', 'Bb','C','Am','Dm','Gm','C','F','F', 'Bb','F','Bb','F'];
const PC={C:0,D:2,E:4,F:5,G:7,A:9,Bb:10,B:11};
const QUAL={'':[0,4,7,12],m:[0,3,7,12],7:[0,4,7,10]};
function chord(sym){const m=/^([A-G]b?)(.*)$/.exec(sym),root=PC[m[1]],iv=QUAL[m[2]];if(!iv)throw Error('acorde: '+sym);
 let notes=iv.map(i=>57+root+i);while(notes[0]>62)notes=notes.map(n=>n-12);let b=36+root;if(b>41)b-=12;return {notes,bass:b};}
const sec=b=>(SECC.find(([,a,z])=>b>=a&&b<z)||['outro'])[0];

/* ---------- 4. La mezcla ---------- */
const ctx=new OfflineAudioContext(2,Math.ceil(LEN*SR),SR),H=rng('humano');
const master=ctx.createGain(),comp=ctx.createDynamicsCompressor();master.gain.value=.8;comp.threshold.value=-16;comp.ratio.value=2;comp.attack.value=.02;comp.release.value=.3;master.connect(comp);comp.connect(ctx.destination);
const mk=(v,to=master)=>{const g=ctx.createGain();g.gain.value=v;g.connect(to);return g;};
const inst=mk(opts.inst??.7),vocB=mk(opts.voc??1.9),vozB=mk(opts.voces??1.1),fxB=mk(opts.fx??.5);
/* que se entienda: la banda se agacha ~2.5 dB en los coros */
[[inst,opts.inst??.7,.52]].forEach(([bus,alto,bajo])=>{bus.gain.setValueAtTime(alto,0);for(const [a,z] of [[12,20],[32,40]]){bus.gain.setValueAtTime(alto,tb(a)-.1);bus.gain.linearRampToValueAtTime(bajo,tb(a)+.05);bus.gain.setValueAtTime(bajo,tb(z)-.1);bus.gain.linearRampToValueAtTime(alto,tb(z)+.05);}});
const verb=ctx.createConvolver(),vr=rng('reverb'),ir=ctx.createBuffer(2,SR*4.5,SR);for(let c=0;c<2;c++){const d=ir.getChannelData(c);for(let k=0;k<d.length;k++)d[k]=(vr()*2-1)*Math.exp(-k/SR*1.4)*(k<SR*.02?k/(SR*.02):1);}verb.buffer=ir;
const verbG=ctx.createGain();verbG.gain.value=.55;verb.connect(verbG);verbG.connect(master);
const send=(from,g)=>{const s=ctx.createGain();s.gain.value=g;from.connect(s);s.connect(verb);};send(inst,.3);send(vocB,.22);send(vozB,.4);send(fxB,.5);
const pan=(p,to)=>{const s=ctx.createStereoPanner();s.pan.value=Math.max(-1,Math.min(1,p));s.connect(to);return s;};
const env=(g,t,a,peak,dec,sus=0.0001,tail=.05,end)=>{g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(peak,t+a);g.gain.setTargetAtTime(Math.max(sus,.0001),t+a,dec);if(end!=null)g.gain.setTargetAtTime(0,end,tail);};
function vibr(o,t,rate,cents,delay,dur){const l=ctx.createOscillator(),lg=ctx.createGain();l.frequency.value=rate;lg.gain.setValueAtTime(0,t);lg.gain.setValueAtTime(0,t+delay);lg.gain.linearRampToValueAtTime(cents,t+delay+.3);l.connect(lg);lg.connect(o.detune);l.start(t);l.stop(t+dur+.5);}
/* cajita de música: lengüeta de metal (parciales 1 : 3.01 : 5.9) */
function cajita(t,n,vel,p=0){const out=pan(p,inst);[[1,1,1.3],[3.01,.25,.4],[5.9,.08,.14]].forEach(([r,a,d])=>{const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.value=hz(n)*r;env(g,t,.002,.065*vel*a,d/3);o.connect(g);g.connect(out);o.start(t);o.stop(t+d*3);});}
/* celesta: FM suave de razón 4 */
function celesta(t,n,vel,p=0){const f=hz(n),c=ctx.createOscillator(),m=ctx.createOscillator(),mg=ctx.createGain(),g=ctx.createGain();c.frequency.value=f;m.frequency.value=f*4;mg.gain.setValueAtTime(f*.9,t);mg.gain.setTargetAtTime(0,t,.25);m.connect(mg);mg.connect(c.frequency);c.connect(g);g.connect(pan(p,inst));env(g,t,.003,.05*vel,.7);[c,m].forEach(x=>{x.start(t);x.stop(t+3);});}
const ksr=rng('cuerda');
function arpa(t,n,vel,p=0){const f=hz(n),N=Math.max(2,Math.round(SR/f)),len=Math.ceil(SR*2.4),b=ctx.createBuffer(1,len,SR),d=b.getChannelData(0),buf=new Float32Array(N);
 for(let i=0;i<N;i++)buf[i]=(ksr()*2-1)*(i<N/2?1:.5);let k=0;for(let i=0;i<len;i++){const v=buf[k],nx=buf[(k+1)%N];buf[k]=.9975*.5*(v+nx);d[i]=v;k=(k+1)%N;}
 const s=ctx.createBufferSource(),g=ctx.createGain(),lp=ctx.createBiquadFilter();lp.type='lowpass';lp.frequency.value=3000;s.buffer=b;s.connect(lp);lp.connect(g);g.connect(pan(p,inst));g.gain.value=.09*vel;s.start(t);}
function cuerdas(t,notes,dur,vel){const lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.frequency.value=1900;lp.connect(g);g.connect(inst);
 notes.forEach((n,i)=>[-9,0,9].forEach(dt=>{const o=ctx.createOscillator();o.type='sawtooth';o.frequency.value=hz(n);o.detune.value=dt+(H()-.5)*6;vibr(o,t,4.6+i*.2,7,.6,dur);o.connect(pan((i-1.5)*.45,lp));o.start(t);o.stop(t+dur+2);}));
 env(g,t,1,.012*vel,2,.011*vel,.8,t+dur);}
function bajo(t,n,dur,vel){const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.value=hz(n);o.connect(g);g.connect(inst);env(g,t,.02,.32*vel,.8,.2*vel,.15,t+dur);o.start(t);o.stop(t+dur+.8);}
/* el plumón de Jigglypuff: rechinidos de ruido en banda alta */
const nb=ctx.createBuffer(1,SR*2,SR),nr=rng('ruido');{const d=nb.getChannelData(0);for(let k=0;k<d.length;k++)d[k]=nr()*2-1;}
function plumon(t,dur){const s=ctx.createBufferSource(),bp=ctx.createBiquadFilter(),g=ctx.createGain();s.buffer=nb;s.loop=true;bp.type='bandpass';bp.Q.value=9;bp.frequency.setValueAtTime(2600+H()*1500,t);bp.frequency.linearRampToValueAtTime(3200+H()*1500,t+dur);s.connect(bp);bp.connect(g);g.connect(pan((H()-.5)*.8,fxB));
 g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(.28,t+.02);g.gain.setValueAtTime(.28,t+dur*.8);g.gain.linearRampToValueAtTime(0,t+dur);s.start(t,H());s.stop(t+dur+.05);}

/* ---------- 5. Las voces del juego (voces.py) ---------- */
for(const [nombre,p,d] of [['voces_coro.wav',-.35,0],['voces_coro.wav',.35,.013],['voces_jiggly.wav',0,0]]){const ab=await (await fetch(DIR+nombre)).arrayBuffer(),b=await ctx.decodeAudioData(ab),s=ctx.createBufferSource();s.buffer=b;s.connect(pan(p,vozB));s.start(d);}

/* ---------- 6. El arreglo: vals (bajo en el 1, acorde en el 2 y el 3) ---------- */
const hv=v=>v*(.9+H()*.2),ht=t=>t+(H()-.5)*.01;
for(let bar=0;bar<NBAR;bar++){const S=sec(bar),c=chord(CH[bar]),N=c.notes,T=b=>tb(bar,b);
 const vals=(vel=1)=>{bajo(T(0),c.bass,SPB*.95,vel);[1,2].forEach(b=>N.slice(1).forEach((n,k)=>arpa(ht(T(b))+k*.012,n+12,hv(vel*.75),(k-1)*.35)));};
 const caja=(vel=1,oct=24)=>[0,.5,1,1.5,2,2.5].forEach((b,k)=>cajita(T(b),N[[0,1,2,3,2,1][k]]+oct,hv(vel)*(k%2?.75:1),k%2?.4:-.4));
 if(S==='intro'){caja(bar<2?.8:1);if(bar>=2)bajo(T(0),c.bass,BAR*.95,.6);}
 if(S==='verso'){vals(.85);if(bar%2===1)caja(.5);}
 if(S==='coro'){vals(1);cuerdas(T(0),N.map(n=>n+12),BAR*.98,1);[0,1,2].forEach(b=>celesta(T(b),N[(b+bar)%4]+24,.7,b%2?.4:-.4));}
 if(S==='verso2'){vals(.8);caja(.45);if(bar>=24)cuerdas(T(0),N.map(n=>n+12),BAR,.6);}
 if(S==='puente'){bajo(T(0),c.bass,BAR*.9,.7);N.forEach((n,k)=>arpa(T(k*.5),n+12,.9,(k-1.5)*.4));if(bar>=30)for(let k=0;k<5;k++)plumon(T(k*.55)+H()*.1,.18+H()*.25);}
 if(S==='coro2'){vals(bar<36?.9:.7);cuerdas(T(0),N.map(n=>n+12),BAR*.98,bar<36?1:.7);[0,1,2].forEach(b=>celesta(T(b),N[(b+bar)%4]+24,.6,b%2?.4:-.4));}
 if(S==='outro'){caja(.7-(bar-40)*.12);if(bar===43)N.forEach((n,k)=>celesta(T(k*.5),n+24,.6,(k-1.5)*.3));bajo(T(0),c.bass,BAR*.95,.5);}}

/* ---------- 7. El narrador ---------- */
let sung=0;for(const x of lead){const r=await sing(x.syl,x.note,x.D,{formant:x.formant??1.04,vib:x.vib??16});
 const s=ctx.createBufferSource(),g=ctx.createGain();s.buffer=r.buf;g.gain.value=.5*r.norm*(x.gain??1);s.connect(g);g.connect(pan(0,vocB));s.start(Math.max(0,x.t-r.vt));sung++;}

const out=await ctx.startRendering(),L=out.getChannelData(0),Rr=out.getChannelData(1);let pk=0;for(let k=0;k<L.length;k++)pk=Math.max(pk,Math.abs(L[k]),Math.abs(Rr[k]));const g=.92/pk;
const rms=[];for(let s=0;s<Math.floor(LEN);s+=5){let a=0;const i0=s*SR,i1=Math.min(L.length,(s+5)*SR);for(let k=i0;k<i1;k++)a+=L[k]*L[k];rms.push(+(Math.sqrt(a/(i1-i0))*g).toFixed(3));}
const pcm=new Int16Array(L.length*2);for(let k=0;k<L.length;k++){pcm[k*2]=Math.max(-1,Math.min(1,L[k]*g))*32767;pcm[k*2+1]=Math.max(-1,Math.min(1,Rr[k]*g))*32767;}
const u8=new Uint8Array(pcm.buffer);let b64='';for(let k=0;k<u8.length;k+=32768)b64+=String.fromCharCode(...u8.subarray(k,k+32768));
return {b64:btoa(b64),peak:pk,rms,sung,seconds:LEN};};
