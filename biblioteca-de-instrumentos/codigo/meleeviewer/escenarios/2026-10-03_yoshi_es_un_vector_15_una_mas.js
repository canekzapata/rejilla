/* Escenario de «yoshi es un vector 15_una_mas» para la biblioteca de instrumentos: las declaraciones que usan sus instrumentos, tal cual,
   sacadas de meleeviewer/output/Arte/2026-10-03_yoshi_es_un_vector_15_una_mas/cancion.js (sha256 783425243cbb) por herramientas/escenarios_meleeviewer.cjs.
   Cambios: ctx → el que se dé; master → la salida que se dé (seco). Nombres que no se encontraron: ninguno. */
(function(){'use strict';return async function(__ctx,__salida,opts){opts=opts||{};
const SEED='yoshi-es-un-vector-15-una-mas';
const SR=44100;
function hash(s){let h=1779033703^s.length;for(let i=0;i<s.length;i++){h=Math.imul(h^s.charCodeAt(i),3432918353);h=h<<13|h>>>19;}h=Math.imul(h^h>>>16,2246822507);h=Math.imul(h^h>>>13,3266489909);return (h^h>>>16)>>>0;}
function rng(tag){let a=hash(SEED+':'+tag);return ()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}
const hz=n=>440*2**((n-69)/12);
const ctx=__ctx;
const H=rng('humano');
const master=__salida;
master.gain.value=.8;
const mk=(v,to=master)=>{const g=ctx.createGain();g.gain.value=v;g.connect(to);return g;};
const inst=mk(opts.inst??.65);
const fxB=mk(opts.fx??.5);
const motB=mk(opts.motivos??.9);
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
/* los timbres de los motivos */
function cuadrada(t,n,dur,vel,p=0){const o=ctx.createOscillator(),lp=ctx.createBiquadFilter(),g=ctx.createGain();o.type='square';o.frequency.value=hz(n);lp.type='lowpass';lp.frequency.value=2600;o.connect(lp);lp.connect(g);g.connect(pan(p,motB));env(g,t,.005,.05*vel,.15,.035*vel,.04,t+dur);o.start(t);o.stop(t+dur+.2);}
function campanita(t,n,dur,vel,p=0){const f=hz(n),c=ctx.createOscillator(),m=ctx.createOscillator(),mg=ctx.createGain(),g=ctx.createGain();c.frequency.value=f;m.frequency.value=f*4;mg.gain.setValueAtTime(f*.8,t);mg.gain.setTargetAtTime(0,t,.25);m.connect(mg);mg.connect(c.frequency);c.connect(g);g.connect(pan(p,motB));env(g,t,.003,.06*vel,.6);[c,m].forEach(x=>{x.start(t);x.stop(t+2.5);});}
function metal(t,n,dur,vel,p=0){const lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.Q.value=2;lp.frequency.setValueAtTime(400,t);lp.frequency.linearRampToValueAtTime(1800,t+.06);lp.frequency.setTargetAtTime(700,t+.1,.2);lp.connect(g);g.connect(pan(p,motB));
 [0,7,-5].forEach(d=>{const o=ctx.createOscillator();o.type='sawtooth';o.frequency.value=hz(n);o.detune.value=d;o.connect(lp);o.start(t);o.stop(t+dur+.3);});env(g,t,.02,.07*vel,.25,.05*vel,.06,t+dur);}
const nb=ctx.createBuffer(1,SR*2,SR);
const nr=rng('ruido');
{const d=nb.getChannelData(0);for(let k=0;k<d.length;k++)d[k]=nr()*2-1;};
function riser(t,dur,vel=1){const s=ctx.createBufferSource(),bp=ctx.createBiquadFilter(),g=ctx.createGain();s.buffer=nb;s.loop=true;bp.type='bandpass';bp.Q.value=2;bp.frequency.setValueAtTime(400,t);bp.frequency.exponentialRampToValueAtTime(8000,t+dur);
 g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(.22*vel,t+dur);g.gain.setValueAtTime(0,t+dur);s.connect(bp);bp.connect(g);g.connect(fxB);s.start(t);s.stop(t+dur+.05);}
return {bajo,ep,cuerda,cuerdas,cuadrada,campanita,metal,riser};
};})()