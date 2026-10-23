/* «¡doki doki, presiona start!» (yoshi es un vector, parte 16) — ~73 s de J-pop a 132 bpm, Mi mayor → Fa mayor. La banda y la mezcla.
   Una vuelta de 180°: en vez del vocoder de consola canta una voz de texto a voz (Microsoft Sabina, es-MX) afinada sílaba por sílaba
   (cantante.py + voz.py), con la letra escrita para que las tónicas caigan en tiempo fuerte (prosodia medida: 100 %). Armonía del
   «camino real» del J-pop (IV△7–V7–iii7–vi) y el último coro medio tono arriba, como en los openings.
   Aquí: batería de consola (8-beat con rellenos), bajo de octavas en corcheas, piano brillante, guitarra Karplus-Strong (rasgueo
   apagado en los versos, abierta en los coros), cuerdas, gancho de sinte en la intro y el «na na na», y chispitas de glockenspiel en
   «kira kira». La banda se agacha ~2.5 dB bajo cada sílaba cantada. Se corre dentro del visor de lectura: window.cancion(opciones) → WAV. */
'use strict';
window.cancion=async function(opts={}){
const DIR='/meleeviewer/output/Arte/2026-10-09_yoshi_es_un_vector_16_jpop/';
const P=await (await fetch(DIR+'partitura.json')).json();
const SEED='yoshi-es-un-vector-16-jpop',BPM=P.bpm,SPB=60/BPM,BAR=SPB*4,T0=P.t0,SR=44100,LEN=opts.len??P.len,NBAR=opts.len?Math.min(P.compases,Math.ceil(opts.len/(60/P.bpm*4))):P.compases;
/* prueba: opts.solo = 'piano'|'bajo'|'cuerda'|'cuerdas'|'sinte'|'glock'|'bateria'|'voces' deja sonar sólo eso */
const SOLO=opts.solo,suena=k=>!SOLO||SOLO===k;
const tb=(bar,beat=0)=>T0+(bar*4+beat)*SPB,ts=(bar,step)=>tb(bar,step/4);
function hash(s){let h=1779033703^s.length;for(let i=0;i<s.length;i++){h=Math.imul(h^s.charCodeAt(i),3432918353);h=h<<13|h>>>19;}h=Math.imul(h^h>>>16,2246822507);h=Math.imul(h^h>>>13,3266489909);return (h^h>>>16)>>>0;}
function rng(tag){let a=hash(SEED+':'+tag);return ()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}
const hz=n=>440*2**((n-69)/12);
const p0=Lectura.snapshot().piece;
const sec=b=>(P.secciones.find(([,a,z])=>b>=a&&b<z)||['final'])[0];
const PC={C:0,'C#':1,Db:1,D:2,'D#':3,Eb:3,E:4,F:5,'F#':6,Gb:6,G:7,'G#':8,Ab:8,A:9,'A#':10,Bb:10,B:11};
const QUAL={'':[0,4,7,12],m:[0,3,7,12],7:[0,4,7,10],maj7:[0,4,7,11],m7:[0,3,7,10]};
function chord(sym){const m=/^([A-G][b#]?)(.*)$/.exec(sym),root=PC[m[1]],iv=QUAL[m[2]];let notes=iv.map(i=>57+root+i);while(notes[0]>62)notes=notes.map(n=>n-12);let b=36+root;if(b>42)b-=12;return {notes,bass:b,root};}

/* ---------- la mezcla ---------- */
const ctx=new OfflineAudioContext(2,Math.ceil(LEN*SR),SR),H=rng('humano');
const master=ctx.createGain(),comp=ctx.createDynamicsCompressor(),sinDC=ctx.createBiquadFilter();master.gain.value=.8;comp.threshold.value=-14;comp.ratio.value=3;comp.attack.value=.008;comp.release.value=.15;
/* medido: la mezcla traía corrimiento de DC (voces cortadas y la guitarra Karplus-Strong con distorsión: −0.077) que se comía el margen; un pasa-altos de 25 Hz lo quita */
sinDC.type='highpass';sinDC.frequency.value=25;sinDC.Q.value=.7;master.connect(sinDC);sinDC.connect(comp);comp.connect(ctx.destination);
const mk=(v,to=master)=>{const g=ctx.createGain();g.gain.value=v;g.connect(to);return g;};
const inst=mk(opts.inst??.6),vozB=mk(opts.voz??1.8),coroB=mk(opts.coro??.6),drumB=mk(opts.drums??.85),fxB=mk(opts.fx??.5);
/* las voces pasan por un pasa-altos de 90 Hz (sin DC ni retumbe); entran por vozIn/coroIn */
const pasaAltos=(to,f)=>{const h=ctx.createBiquadFilter();h.type='highpass';h.frequency.value=f;h.Q.value=.7;h.connect(to);return h;};const vozIn=pasaAltos(vozB,90),coroIn=pasaAltos(coroB,110);
/* que se entienda: medido, a la mezcla le faltaba 2–6 kHz (1–4 %); presencia en la voz (+4 dB en 3 kHz) y aire en la banda (+2.5 dB arriba de 6 kHz) */
{const pr=ctx.createBiquadFilter();pr.type='peaking';pr.frequency.value=3000;pr.Q.value=.9;pr.gain.value=4;vozB.disconnect();vozB.connect(pr);pr.connect(master);
 const aire=ctx.createBiquadFilter();aire.type='highshelf';aire.frequency.value=6000;aire.gain.value=2.5;inst.disconnect();inst.connect(aire);aire.connect(master);}
/* que se entienda: la banda se agacha bajo cada sílaba de la voz principal */
inst.gain.setValueAtTime(opts.inst??.6,0);for(const s of P.silabas){inst.gain.setTargetAtTime((opts.inst??.6)*.75,s.t-.03,.02);inst.gain.setTargetAtTime(opts.inst??.6,s.t+s.dur,.08);}
const verb=ctx.createConvolver(),vr=rng('reverb'),ir=ctx.createBuffer(2,SR*2.6,SR);for(let c=0;c<2;c++){const d=ir.getChannelData(c);for(let k=0;k<d.length;k++)d[k]=(vr()*2-1)*Math.exp(-k/SR*2.3)*(k<SR*.012?k/(SR*.012):1);}verb.buffer=ir;
const verbG=ctx.createGain();verbG.gain.value=.42;verb.connect(verbG);verbG.connect(master);
const send=(from,g)=>{const s=ctx.createGain();s.gain.value=g;from.connect(s);s.connect(verb);};send(inst,.16);send(vozB,.2);send(coroB,.3);send(fxB,.4);
/* eco de corchea con puntillo para la voz (el brillo del J-pop) */
const dl=ctx.createDelay(2),dfb=ctx.createGain(),dlp=ctx.createBiquadFilter(),dsend=ctx.createGain();dl.delayTime.value=SPB*.75;dfb.gain.value=.28;dlp.type='lowpass';dlp.frequency.value=4500;dsend.gain.value=.14;vozB.connect(dsend);dsend.connect(dl);dl.connect(dlp);dlp.connect(dfb);dfb.connect(dl);dlp.connect(master);
const pan=(p,to)=>{const s=ctx.createStereoPanner();s.pan.value=Math.max(-1,Math.min(1,p));s.connect(to);return s;};
const env=(g,t,a,peak,dec,sus=0.0001,tail=.05,end)=>{g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(peak,t+a);g.gain.setTargetAtTime(Math.max(sus,.0001),t+a,dec);if(end!=null)g.gain.setTargetAtTime(0,end,tail);};
function vibr(o,t,rate,cents,delay,dur){const l=ctx.createOscillator(),lg=ctx.createGain();l.frequency.value=rate;lg.gain.setValueAtTime(0,t);lg.gain.setValueAtTime(0,t+delay);lg.gain.linearRampToValueAtTime(cents,t+delay+.3);l.connect(lg);lg.connect(o.detune);l.start(t);l.stop(t+dur+.5);}
/* piano brillante: parciales con inarmonicidad y martillo */
const nb=ctx.createBuffer(1,SR*2,SR),nr=rng('ruido');{const d=nb.getChannelData(0);for(let k=0;k<d.length;k++)d[k]=nr()*2-1;}
function piano(t,n,dur,vel,p=0){if(!suena('piano'))return;const f=hz(n),out=pan(p,inst);for(let k=1;k<=7;k++){const fk=k*f*Math.sqrt(1+.0004*k*k);if(fk>10000)break;const o=ctx.createOscillator(),og=ctx.createGain();o.frequency.value=fk;const a=vel*.045/Math.pow(k,1.1)*(k===2?1.3:1),dec=Math.max(.2,2.2-(n-50)*.03)/Math.sqrt(k);
 og.gain.setValueAtTime(0,t);og.gain.linearRampToValueAtTime(a,t+.002);og.gain.setTargetAtTime(a*.35,t+.002,dec*.12);og.gain.setTargetAtTime(0,t+.04,dec);og.gain.setTargetAtTime(0,t+dur,.1);o.connect(og);og.connect(out);o.start(t);o.stop(t+dur+1);}
 const s=ctx.createBufferSource(),bp=ctx.createBiquadFilter(),hg=ctx.createGain();s.buffer=nb;bp.type='bandpass';bp.frequency.value=f*3;bp.Q.value=1;s.connect(bp);bp.connect(hg);hg.connect(out);env(hg,t,.001,.02*vel,.012);s.start(t,(n%7)*.1);s.stop(t+.08);}
function bajo(t,n,dur,vel){if(!suena('bajo'))return;const o=ctx.createOscillator(),s=ctx.createOscillator(),lp=ctx.createBiquadFilter(),g=ctx.createGain();o.type='sawtooth';o.frequency.value=hz(n);s.frequency.value=hz(n);lp.type='lowpass';lp.Q.value=3;lp.frequency.setValueAtTime(1500*vel+300,t);lp.frequency.setTargetAtTime(350,t,.07);
 const sg=ctx.createGain();sg.gain.value=.8;o.connect(lp);s.connect(sg);sg.connect(lp);lp.connect(g);g.connect(inst);env(g,t,.004,.3*vel,.15,.18*vel,.03,t+dur);[o,s].forEach(x=>{x.start(t);x.stop(t+dur+.2);});}
const ksr=rng('cuerda');
function cuerda(t,n,dur,vel,apagada,p=0){if(!suena('cuerda'))return;const f=hz(n),N=Math.max(2,Math.round(SR/f)),len=Math.ceil(SR*Math.min(dur+.3,2)),b=ctx.createBuffer(1,len,SR),d=b.getChannelData(0),buf=new Float32Array(N);
 for(let i=0;i<N;i++)buf[i]=ksr()*2-1;const damp=apagada?.95:.997;let k=0;for(let i=0;i<len;i++){const v=buf[k],nx=buf[(k+1)%N];buf[k]=damp*.5*(v+nx);d[i]=v*(apagada?Math.exp(-i/SR/.06):1);k=(k+1)%N;}
 const s=ctx.createBufferSource(),g=ctx.createGain(),lp=ctx.createBiquadFilter(),ws=ctx.createWaveShaper(),cur=new Float32Array(256);for(let i=0;i<256;i++){const x=i/128-1;cur[i]=Math.tanh(x*2.2);}ws.curve=cur;
 lp.type='lowpass';lp.frequency.value=apagada?2200:4500;s.buffer=b;s.connect(ws);ws.connect(lp);lp.connect(g);g.connect(pan(p,inst));g.gain.setValueAtTime(.09*vel,t);g.gain.setTargetAtTime(0,t+dur,.06);s.start(t);s.stop(t+len/SR);}
function rasgueo(t,notes,vel,apagada,p){notes.forEach((n,i)=>cuerda(t+i*.008,n,apagada?.09:SPB*1.8,vel*(1-i*.06),apagada,p));}
function cuerdas(t,notes,dur,vel){if(!suena('cuerdas'))return;const lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.frequency.value=2800;lp.connect(g);g.connect(inst);
 notes.forEach((n,i)=>[-8,0,8].forEach(dt=>{const o=ctx.createOscillator();o.type='sawtooth';o.frequency.value=hz(n);o.detune.value=dt+(H()-.5)*6;vibr(o,t,5,7,.4,dur);o.connect(pan((i-1.5)*.45,lp));o.start(t);o.stop(t+dur+1);}));env(g,t,.25,.013*vel,1.2,.011*vel,.3,t+dur);}
/* el gancho: sinte de dos osciladores con un poco de vibrato */
function sinte(t,n,dur,vel,p=0){if(!suena('sinte'))return;const lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.frequency.setValueAtTime(5000,t);lp.frequency.setTargetAtTime(2400,t,.1);lp.connect(g);g.connect(pan(p,inst));
 [['square',0,.6],['sawtooth',7,.5]].forEach(([ty,d,a])=>{const o=ctx.createOscillator(),og=ctx.createGain();o.type=ty;o.frequency.value=hz(n);o.detune.value=d;vibr(o,t,5.5,12,.12,dur);og.gain.value=a;o.connect(og);og.connect(lp);o.start(t);o.stop(t+dur+.2);});env(g,t,.006,.05*vel,.2,.04*vel,.05,t+dur);}
function glock(t,n,vel,p=0){if(!suena('glock'))return;const out=pan(p,inst);[[1,1,1.2],[2.76,.3,.35],[5.4,.12,.12]].forEach(([r,a,d])=>{const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.value=hz(n)*r;env(g,t,.001,.05*vel*a,d/3);o.connect(g);g.connect(out);o.start(t);o.stop(t+d*3);});}
function riser(t,dur,vel=1){const s=ctx.createBufferSource(),bp=ctx.createBiquadFilter(),g=ctx.createGain();s.buffer=nb;s.loop=true;bp.type='bandpass';bp.Q.value=2;bp.frequency.setValueAtTime(400,t);bp.frequency.exponentialRampToValueAtTime(9000,t+dur);
 g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(.2*vel,t+dur);g.gain.setValueAtTime(0,t+dur);s.connect(bp);bp.connect(g);g.connect(fxB);s.start(t);s.stop(t+dur+.05);}

/* ---------- las voces de Sabina (voz.py) ---------- */
for(const [nombre,bus,p,d] of suena('voces')?[['voz_lead.wav',vozIn,0,0],['voz_coro.wav',coroIn,-.3,0],['voz_coro.wav',coroIn,.3,.015]]:[]){const ab=await (await fetch(DIR+nombre)).arrayBuffer(),b=await ctx.decodeAudioData(ab),s=ctx.createBufferSource();s.buffer=b;s.connect(pan(p,bus));s.start(d);}

/* ---------- batería de consola: 8-beat de J-pop ---------- */
const LM=window.LecturaMusica;
async function bateria(bar0,bars,d,extra=0){if(!suena('bateria')||tb(bar0)>LEN)return;const dr={gain:.6,kit:'acustico',...d};
 const q={...p0,clips:[],tempo:{...p0.tempo,bpm:BPM,meter:4},music:LM.normalize({...p0.music,on:true,gain:.75,reverb:.1,delay:0,pulse:'none',voices:[],drums:LM.drums(dr)})};
 const len=bars*BAR,buf=await LM.render(q,[],len+extra,SR),s=ctx.createBufferSource(),g=ctx.createGain();s.buffer=buf;s.connect(g);g.connect(drumB);
 const at=tb(bar0);g.gain.setValueAtTime(1,at);if(!extra){g.gain.setValueAtTime(1,at+len-.03);g.gain.linearRampToValueAtTime(0,at+len);}s.start(at);}
const q16=n=>'x'+'.'.repeat(n-1),rep=(s,n)=>s.repeat(n);
const OCHO={kick:'x.....x.x.......',snare:'....x.......x...',hat:'x.x.x.x.x.x.x.x.'};
const CORO={kick:'x.....x.x.....x.',snare:'....x.......x...',hat:'x.xxx.xxx.xxx.xx',openhat:'..............x.'};
await bateria(0,4,{...OCHO,crash:q16(64),tomhi:rep('.',48)+'........x.x.xxxx'});
await bateria(4,4,{kick:'x.......x.......',rim:'....x.......x...',hat:'x.x.x.x.x.x.x.x.'});
await bateria(8,4,{...OCHO,tomlo:rep('.',48)+'............x.xx'});
await bateria(12,4,{...OCHO,snare:'....x.......x...'+'....x.......x...'+'....x.......x...'+'x.x.x.x.xxxxxxxx',ride:'x.x.x.x.x.x.x.x.'});
await bateria(16,4,{...CORO,crash:q16(64)});
await bateria(20,4,{...CORO,tomhi:rep('.',48)+'........x.x.xxxx'});
await bateria(24,4,{...CORO,crash:q16(64),cowbell:'..x...x...x...x.'});
await bateria(28,4,{...CORO,crash:q16(64),spray:q16(64)});
await bateria(32,4,{...CORO,tomhi:rep('.',48)+'....x.x.x.xxxxxx'});
await bateria(36,2,{kick:'x...............',crash:'x...............'},3);

/* ---------- el arreglo ---------- */
const hv=v=>v*(.9+H()*.2),ht=t=>t+(H()-.5)*.006;
/* el gancho de la intro y del «na na na» (corcheas; una frase por compás sobre el camino real) */
const GANCHO=[[73,71,68,71,73,76,73,71],[75,73,71,66,71,73,75,78],[71,68,63,68,71,75,73,71],[68,64,61,64,68,71,73,76]];
for(let bar=0;bar<NBAR;bar++){const S=sec(bar),c=chord(P.acordes[bar]),N=c.notes,T=s=>ts(bar,s),sube=bar>=28&&bar<36?1:0;
 const linea=(vel=.9)=>{for(let s=0;s<16;s+=2)bajo(ht(T(s)),c.bass+(s%4===2&&S!=='verso'?12:0),SPB*.45,hv(vel));};
 const arpegio=(vel=.7)=>{const ord=[0,1,2,3,2,1,2,3];for(let s=0;s<16;s++)piano(ht(T(s)),N[ord[s%8]]+12,SPB*.3,hv(vel)*(s%4?.7:1),s%2?.3:-.3);};
 const acordesPiano=(vel=.9)=>[0,3,6,8,11,14].forEach(s=>N.forEach((n,k)=>piano(ht(T(s))+k*.008,n+12,SPB*.6,hv(vel*.75),(k-1.5)*.3)));
 const apagado=(vel=.8)=>{for(let s=0;s<16;s+=2)rasgueo(ht(T(s)),N.slice(0,3).map(n=>n),hv(vel),true,.45);};
 const abierto=(vel=.9)=>[0,3,6,10,12,14].forEach(s=>rasgueo(ht(T(s)),[c.bass+12,...N.slice(0,3)],hv(vel),false,.4));
 const gancho=(vel=1)=>GANCHO[bar%4].forEach((n,k)=>sinte(T(k*2),n+sube,SPB*.45,vel,-.15));
 if(S==='intro'){gancho(1);linea(.8);acordesPiano(.7);if(bar===3)riser(T(8),BAR/2,.8);}
 if(S==='verso'){linea(bar<8?.7:.85);arpegio(.6);if(bar>=8)apagado(.6);}
 if(S==='pre'){linea(.9);acordesPiano(.8);cuerdas(T(0),N.map(n=>n+12),BAR*.98,.9);if(bar===15)riser(T(0),BAR,1);}
 if(S==='coro'||S==='coro2'){linea(1);acordesPiano(.9);abierto(.85);cuerdas(T(0),N.map(n=>n+12),BAR*.98,1.1);}
 if(S==='hook'){gancho(1.1);linea(1);acordesPiano(.8);apagado(.7);if(bar===27)riser(T(8),BAR/2,1);}
 if(S==='final'){N.forEach((n,k)=>piano(T(0),n+12,BAR*1.5,1,(k-1.5)*.3));if(bar===36){bajo(T(0),c.bass,BAR,1);[0,2,4,6,8,10,12,14].forEach((s,k)=>glock(T(s),N[k%4]+24+12*Math.floor(k/4),.8,k%2?.4:-.4));}}}
/* chispitas en «kira kira» (y en «doki doki», latidos de bombo) */
for(const s of P.silabas){if(s.txt==='ki'&&/kira/.test(s.renglon))for(let k=0;k<4;k++)glock(s.t+k*.05,s.nota+24+[0,4,7,12][k],.9,k%2?.5:-.5);}

const out=await ctx.startRendering(),L=out.getChannelData(0),Rr=out.getChannelData(1);let pk=0;for(let k=0;k<L.length;k++)pk=Math.max(pk,Math.abs(L[k]),Math.abs(Rr[k]));const g=.92/pk;
const rms=[];for(let s=0;s<Math.floor(LEN);s+=5){let a=0;const i0=s*SR,i1=Math.min(L.length,(s+5)*SR);for(let k=i0;k<i1;k++)a+=L[k]*L[k];rms.push(+(Math.sqrt(a/(i1-i0))*g).toFixed(3));}
const pcm=new Int16Array(L.length*2);for(let k=0;k<L.length;k++){pcm[k*2]=Math.max(-1,Math.min(1,L[k]*g))*32767;pcm[k*2+1]=Math.max(-1,Math.min(1,Rr[k]*g))*32767;}
const u8=new Uint8Array(pcm.buffer);let b64='';for(let k=0;k<u8.length;k+=32768)b64+=String.fromCharCode(...u8.subarray(k,k+32768));
return {b64:btoa(b64),peak:pk,rms,sung:P.silabas.length,seconds:LEN};};
