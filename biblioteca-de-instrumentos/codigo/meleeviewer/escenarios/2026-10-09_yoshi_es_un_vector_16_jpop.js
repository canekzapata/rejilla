/* Escenario de «yoshi es un vector 16_jpop» para la biblioteca de instrumentos: las declaraciones que usan sus instrumentos, tal cual,
   sacadas de meleeviewer/output/Arte/2026-10-09_yoshi_es_un_vector_16_jpop/cancion.js (sha256 5fd813de871d) por herramientas/escenarios_meleeviewer.cjs.
   Cambios: ctx → el que se dé; master → la salida que se dé (seco). Nombres que no se encontraron: r, ty. */
(function(){'use strict';return async function(__ctx,__salida,opts){opts=opts||{};
const DIR='/meleeviewer/output/Arte/2026-10-09_yoshi_es_un_vector_16_jpop/';
const P=await (await fetch(DIR+'partitura.json')).json();
const SEED='yoshi-es-un-vector-16-jpop';
const BPM=P.bpm;
const SPB=60/BPM;
const SR=44100;
const SOLO=opts.solo;
const suena=k=>!SOLO||SOLO===k;
function hash(s){let h=1779033703^s.length;for(let i=0;i<s.length;i++){h=Math.imul(h^s.charCodeAt(i),3432918353);h=h<<13|h>>>19;}h=Math.imul(h^h>>>16,2246822507);h=Math.imul(h^h>>>13,3266489909);return (h^h>>>16)>>>0;}
function rng(tag){let a=hash(SEED+':'+tag);return ()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}
const hz=n=>440*2**((n-69)/12);
const ctx=__ctx;
const H=rng('humano');
const master=__salida;
master.gain.value=.8;
const mk=(v,to=master)=>{const g=ctx.createGain();g.gain.value=v;g.connect(to);return g;};
const inst=mk(opts.inst??.6);
const fxB=mk(opts.fx??.5);
/* que se entienda: la banda se agacha bajo cada sílaba de la voz principal */
inst.gain.setValueAtTime(opts.inst??.6,0);
const pan=(p,to)=>{const s=ctx.createStereoPanner();s.pan.value=Math.max(-1,Math.min(1,p));s.connect(to);return s;};
const env=(g,t,a,peak,dec,sus=0.0001,tail=.05,end)=>{g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(peak,t+a);g.gain.setTargetAtTime(Math.max(sus,.0001),t+a,dec);if(end!=null)g.gain.setTargetAtTime(0,end,tail);};
function vibr(o,t,rate,cents,delay,dur){const l=ctx.createOscillator(),lg=ctx.createGain();l.frequency.value=rate;lg.gain.setValueAtTime(0,t);lg.gain.setValueAtTime(0,t+delay);lg.gain.linearRampToValueAtTime(cents,t+delay+.3);l.connect(lg);lg.connect(o.detune);l.start(t);l.stop(t+dur+.5);}
const nb=ctx.createBuffer(1,SR*2,SR);
const nr=rng('ruido');
{const d=nb.getChannelData(0);for(let k=0;k<d.length;k++)d[k]=nr()*2-1;};
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
return {piano,bajo,cuerda,rasgueo,cuerdas,sinte,glock,riser};
};})()