/* «Popo está solo (desync)» (yoshi es un vector, parte 12) — ~74 s a 120 bpm, La menor (dórico). Música de fase.
   En Melee, Nana es una IA que copia lo que hace Popo unos cuadros después. Popo canta un loop de 12 semicorcheas; Nana lo canta igual y
   en los coros se adelanta poco a poco hasta volverse canon («desync»). Muere: Popo está solo y el loop sigue igual. En la siguiente vida
   ella se adelanta una vuelta completa, y el desfase total vuelve a ser unísono.
   Las voces del loop y la batería (golpes del juego medidos y elegidos) vienen de voces.py; aquí van el narrador (vocoder de consola),
   dos marimbas que siguen exactamente a Popo (izquierda) y a Nana (derecha) con su desfase, bajo, colchón frío y campanitas de hielo.
   Se corre dentro del visor de lectura: window.cancion(opciones) → WAV. */
'use strict';
window.cancion=async function(opts={}){
const DIR='/meleeviewer/output/Arte/2026-09-30_yoshi_es_un_vector_12_popo_esta_solo/';
const SEED='yoshi-es-un-vector-12-popo-esta-solo',BPM=120,SPB=60/BPM,BAR=SPB*4,T0=.35,SR=44100,LEN=78,NBAR=36;
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

/* ---------- 2. La letra (sílaba:nota:tiempos, un compás por renglón; video.html la lee de aquí) ---------- */
const NOTE={C:0,D:2,E:4,F:5,G:7,A:9,B:11};
const nm=s=>{const m=/^([A-G])(b|#)?(-?\d)$/.exec(s);if(!m)throw Error('nota: '+s);return 12*(+m[3]+1)+NOTE[m[1]]+(m[2]==='b'?-1:m[2]==='#'?1:0);};
function score(str,bar,tr=0,o={}){const out=[];let beat=0;for(const tok of str.trim().split(/\s+/)){const [a,b,c]=tok.split(':');if(a==='-'){beat+=+b;continue;}out.push({syl:a,note:nm(b)+tr,t:tb(bar,beat),D:+c*SPB-.03,...o});beat+=+c;}return out;}
const NL=String.fromCharCode(10);
function scoreBars(str,bar0,tr=0,o={}){return str.trim().split(NL).flatMap((l,k)=>score(l,bar0+k,tr,o));}
const VERSO=`na:A4:.5 na:C5:.5 co:E5:.5 pia:E5:.5 lo:D5:.5 que:C5:.5 ha:D5:.5 ce:E5:.5
 po:G5:1 po:E5:2 -:1
 con:C5:.5 u:C5:.5 nos:D5:.5 cua:E5:1 dros:D5:.5 des:C5:.5 pues:A4:.5
 -:4
 no:E5:.5 pien:G5:.5 sa:E5:1 re:D5:.5 pi:C5:.5 te:D5:1
 yes:E5:.5 pe:C5:.5 ra:A4:2 -:1
 pe:A4:.5 ro:C5:.5 jun:E5:.5 tos:G5:.5 su:A5:1 ben:G5:1
 la:E5:.5 mon:G5:.5 ta:A5:1 ña:E5:2`;
const FASE=`de:E5:.5 sinc:E5:.5 de:G5:.5 sinc:A5:1.5 -:1
 na:A5:.5 na:G5:.5 sea:E5:.5 de:D5:.5 lan:E5:1 to:C5:1
 ya:C5:.5 noes:D5:.5 tu:E5:.5 som:G5:1 bra:E5:1.5
 -:4
 es:E5:.5 tu:E5:.5 ca:G5:1 non:A5:2
 -:4
 dos:A5:1 vo:G5:.5 ces:E5:.5 u:D5:.5 na:E5:.5 can:G5:.5 cion:A5:.5
 -:4`;
const SOLO=`po:E5:1 po:D5:.5 es:C5:.5 ta:D5:1 so:C5:.5 lo:A4:.5
 -:4
 yel:C5:.5 lup:D5:.5 si:E5:.5 gue:D5:.5 i:C5:1 gual:A4:1`;
const FASE2=`si:A4:.5 guien:C5:.5 te:E5:.5 vi:G5:.5 da:A5:2
 -:4
 de:E5:.5 sinc:E5:.5 de:G5:.5 sinc:A5:1.5 -:1
 -:4
 vuel:A5:1 ta:G5:.5 com:E5:.5 ple:D5:.5 ta:E5:.5 -:1
 -:4
 y:E5:.5 o:G5:.5 tra:A5:.5 vez:C6:1.5 -:1
 en:A5:.5 sinc:A5:1.5 -:2`;
const OUTRO=`jun:E5:.5 tos:G5:1.5 -:2
 -:4
 su:A4:.5 bien:C5:.5 do:E5:2 -:1`;
const SECC=[['intro',0,4],['verso',4,12],['fase',12,20],['solo',20,24],['fase2',24,32],['outro',32,36]];
const lead=[...scoreBars(VERSO,4),...scoreBars(FASE,12),...scoreBars(SOLO,20),...scoreBars(FASE2,24),...scoreBars(OUTRO,32)];

/* ---------- 3. La armonía ---------- */
const CICLO=['Am7','Am7','Fmaj7','Fmaj7','G','G','Em7','Em7'];
const CH=[...Array(NBAR).keys()].map(b=>b>=20&&b<24?['Am7','Am7','Dm7','Dm7'][b-20]:b>=32?['Am7','Fmaj7','G','Am7'][b-32]:CICLO[b%8]);
const PC={C:0,'C#':1,D:2,'D#':3,E:4,F:5,'F#':6,G:7,'G#':8,A:9,'A#':10,Bb:10,B:11};
const QUAL={maj7:[0,4,7,11,14],m7:[0,3,7,10,14],'':[0,4,7,12,14]};
function chord(sym){const m=/^([A-G][b#]?)(.*)$/.exec(sym),root=PC[m[1]],iv=QUAL[m[2]];if(!iv)throw Error('acorde: '+sym);
 let notes=iv.slice(1).map(i=>53+root+i);while(notes[0]>60)notes=notes.map(n=>n-12);let b=36+root;if(b>42)b-=12;return {notes,bass:b};}
const sec=b=>(SECC.find(([,a,z])=>b>=a&&b<z)||['outro'])[0];

/* ---------- 4. La mezcla ---------- */
const ctx=new OfflineAudioContext(2,Math.ceil(LEN*SR),SR),H=rng('humano');
const master=ctx.createGain(),comp=ctx.createDynamicsCompressor();master.gain.value=.8;comp.threshold.value=-15;comp.ratio.value=2.5;comp.attack.value=.01;comp.release.value=.18;master.connect(comp);comp.connect(ctx.destination);
const mk=(v,to=master)=>{const g=ctx.createGain();g.gain.value=v;g.connect(to);return g;};
const inst=mk(opts.inst??.7),vocB=mk(opts.voc??2),loopB=mk(opts.loop??1.1),golB=mk(opts.golpes??1),fxB=mk(opts.fx??.5);
/* que se entienda: mientras canta el narrador, el loop y la banda bajan ~3 dB */
const verb=ctx.createConvolver(),vr=rng('reverb'),ir=ctx.createBuffer(2,SR*3,SR);for(let c=0;c<2;c++){const d=ir.getChannelData(c);for(let k=0;k<d.length;k++)d[k]=(vr()*2-1)*Math.exp(-k/SR*2.2)*(k<SR*.01?k/(SR*.01):1);}verb.buffer=ir;
const verbG=ctx.createGain();verbG.gain.value=.45;verb.connect(verbG);verbG.connect(master);
const send=(from,g)=>{const s=ctx.createGain();s.gain.value=g;from.connect(s);s.connect(verb);};send(inst,.2);send(vocB,.16);send(loopB,.25);send(golB,.1);send(fxB,.5);
const dl=ctx.createDelay(2),dfb=ctx.createGain(),dlp=ctx.createBiquadFilter();dl.delayTime.value=SPB*.75;dfb.gain.value=.3;dlp.type='lowpass';dlp.frequency.value=3200;dl.connect(dlp);dlp.connect(dfb);dfb.connect(dl);dlp.connect(master);
{const s=ctx.createGain();s.gain.value=.1;vocB.connect(s);s.connect(dl);}
const pan=(p,to)=>{const s=ctx.createStereoPanner();s.pan.value=Math.max(-1,Math.min(1,p));s.connect(to);return s;};
const env=(g,t,a,peak,dec,sus=0.0001,tail=.05,end)=>{g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(peak,t+a);g.gain.setTargetAtTime(Math.max(sus,.0001),t+a,dec);if(end!=null)g.gain.setTargetAtTime(0,end,tail);};
/* marimba: parciales de barra de madera (1 : 3.93 : 9.2), la fundamental dura más */
function marimba(t,n,vel,p=0){const out=pan(p,inst),f=hz(n);[[1,1,.45],[3.93,.22,.08],[9.2,.06,.025]].forEach(([r,a,d])=>{const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.value=f*r;env(g,t,.002,.07*vel*a,d);o.connect(g);g.connect(out);o.start(t);o.stop(t+d*6);});
 const nb=ctx.createOscillator(),ng=ctx.createGain();nb.type='square';nb.frequency.value=f*2;env(ng,t,.001,.006*vel,.006);nb.connect(ng);ng.connect(out);nb.start(t);nb.stop(t+.05);}
function bajo(t,n,dur,vel){const o=ctx.createOscillator(),tr=ctx.createOscillator(),g=ctx.createGain(),tg=ctx.createGain(),lp=ctx.createBiquadFilter();o.frequency.value=hz(n);tr.type='triangle';tr.frequency.value=hz(n);tg.gain.value=.5;lp.type='lowpass';lp.frequency.value=600;
 tr.connect(tg);tg.connect(lp);o.connect(lp);lp.connect(g);g.connect(inst);env(g,t,.015,.42*vel,.5,.28*vel,.08,t+dur);[o,tr].forEach(x=>{x.start(t);x.stop(t+dur+.5);});}
function colchon(t,notes,dur,vel){const lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.frequency.setValueAtTime(900,t);lp.frequency.linearRampToValueAtTime(2000,t+dur*.5);lp.frequency.linearRampToValueAtTime(1000,t+dur);lp.connect(g);g.connect(inst);
 notes.forEach((n,i)=>[-8,0,8].forEach(dt=>{const o=ctx.createOscillator();o.type='sawtooth';o.frequency.value=hz(n);o.detune.value=dt+(H()-.5)*5;o.connect(pan((i-1.5)*.45,lp));o.start(t);o.stop(t+dur+1.5);}));env(g,t,.8,.012*vel,1.8,.011*vel,.6,t+dur);}
function hielo(t,n,vel,p=0){const out=pan(p,inst);[[1,1,1.2],[2.76,.35,.35],[5.4,.15,.12]].forEach(([r,a,d])=>{const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.value=hz(n)*r;env(g,t,.001,.03*vel*a,d/3);o.connect(g);g.connect(out);o.start(t);o.stop(t+d*3);});}

/* ---------- 5. El loop cantado, los golpes, y las marimbas que siguen a Popo y a Nana ---------- */
const P=await (await fetch(DIR+'partitura.json')).json();
for(const [nombre,bus] of [['voces_loop.wav',loopB],['golpes.wav',golB]]){const ab=await (await fetch(DIR+nombre)).arrayBuffer(),b=await ctx.decodeAudioData(ab),s=ctx.createBufferSource();s.buffer=b;s.connect(bus);s.start(0);}
P.eventos.filter(e=>e.tipo==='loop').forEach(e=>marimba(e.t,e.nota-12,(e.paso===0?1:.75)*(e.quien==='nana'?.9:1),e.quien==='popo'?-.6:.6));
/* el loop se agacha cuando canta el narrador */
const cantando=lead.map(x=>[x.t,x.t+x.D]);[[loopB,opts.loop??1.1,.72],[inst,opts.inst??.7,.5]].forEach(([bus,alto,bajo])=>{bus.gain.setValueAtTime(alto,0);let prev=-9;for(const [a,z] of cantando){if(a-prev>.4){bus.gain.setValueAtTime(bus===loopB?alto:alto,Math.max(0,a-.12));bus.gain.linearRampToValueAtTime(bajo,a);}bus.gain.setValueAtTime(bajo,z);bus.gain.linearRampToValueAtTime(alto,z+.3);prev=z;}});

/* ---------- 6. El arreglo ---------- */
for(let bar=0;bar<NBAR;bar++){const S=sec(bar),c=chord(CH[bar]),N=c.notes,T=s=>ts(bar,s);
 if(S!=='intro'||bar>=2)bajo(T(0),c.bass,S==='solo'?BAR*.95:SPB*2.6,S==='solo'?.6:.8);if(S==='fase'||S==='fase2')bajo(T(10),c.bass+7,SPB*1.4,.6);
 if(bar%2===0)colchon(T(0),N.map(n=>n+12),BAR*2,S==='solo'?.6:S==='intro'?.5:.9);
 if(S==='fase'||S==='fase2'||S==='outro')[0,6,11].forEach((s,k)=>hielo(T(s),N[(k+bar)%4]+24,.8,k%2?.5:-.5));
 if(S==='solo')[0,8].forEach((s,k)=>hielo(T(s),N[k]+24,.6,k?.4:-.4));}

/* ---------- 7. El narrador ---------- */
let sung=0;for(const x of lead){const r=await sing(x.syl,x.note,x.D);
 const s=ctx.createBufferSource(),g=ctx.createGain();s.buffer=r.buf;g.gain.value=.5*r.norm*(x.gain??1);s.connect(g);g.connect(pan(0,vocB));s.start(Math.max(0,x.t-r.vt));sung++;}

const out=await ctx.startRendering(),L=out.getChannelData(0),Rr=out.getChannelData(1);let pk=0;for(let k=0;k<L.length;k++)pk=Math.max(pk,Math.abs(L[k]),Math.abs(Rr[k]));const g=.92/pk;
const rms=[];for(let s=0;s<Math.floor(LEN);s+=5){let a=0;const i0=s*SR,i1=Math.min(L.length,(s+5)*SR);for(let k=i0;k<i1;k++)a+=L[k]*L[k];rms.push(+(Math.sqrt(a/(i1-i0))*g).toFixed(3));}
const pcm=new Int16Array(L.length*2);for(let k=0;k<L.length;k++){pcm[k*2]=Math.max(-1,Math.min(1,L[k]*g))*32767;pcm[k*2+1]=Math.max(-1,Math.min(1,Rr[k]*g))*32767;}
const u8=new Uint8Array(pcm.buffer);let b64='';for(let k=0;k<u8.length;k+=32768)b64+=String.fromCharCode(...u8.subarray(k,k+32768));
return {b64:btoa(b64),peak:pk,rms,sung,seconds:LEN};};
