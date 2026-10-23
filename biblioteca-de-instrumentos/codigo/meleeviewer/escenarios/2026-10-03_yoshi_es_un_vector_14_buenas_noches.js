/* Escenario de «yoshi es un vector 14_buenas_noches» para la biblioteca de instrumentos: las declaraciones que usan sus instrumentos, tal cual,
   sacadas de meleeviewer/output/Arte/2026-10-03_yoshi_es_un_vector_14_buenas_noches/cancion.js (sha256 c3269f6c9b4d) por herramientas/escenarios_meleeviewer.cjs.
   Cambios: ctx → el que se dé; master → la salida que se dé (seco). Nombres que no se encontraron: r. */
(function(){'use strict';return async function(__ctx,__salida,opts){opts=opts||{};
const SEED='yoshi-es-un-vector-14-buenas-noches';
const SR=44100;
function hash(s){let h=1779033703^s.length;for(let i=0;i<s.length;i++){h=Math.imul(h^s.charCodeAt(i),3432918353);h=h<<13|h>>>19;}h=Math.imul(h^h>>>16,2246822507);h=Math.imul(h^h>>>13,3266489909);return (h^h>>>16)>>>0;}
function rng(tag){let a=hash(SEED+':'+tag);return ()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}
const hz=n=>440*2**((n-69)/12);
const ctx=__ctx;
const H=rng('humano');
const master=__salida;
master.gain.value=.8;
const mk=(v,to=master)=>{const g=ctx.createGain();g.gain.value=v;g.connect(to);return g;};
const inst=mk(opts.inst??.7);
const fxB=mk(opts.fx??.5);
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
const nb=ctx.createBuffer(1,SR*2,SR);
const nr=rng('ruido');
{const d=nb.getChannelData(0);for(let k=0;k<d.length;k++)d[k]=nr()*2-1;};
function plumon(t,dur){const s=ctx.createBufferSource(),bp=ctx.createBiquadFilter(),g=ctx.createGain();s.buffer=nb;s.loop=true;bp.type='bandpass';bp.Q.value=9;bp.frequency.setValueAtTime(2600+H()*1500,t);bp.frequency.linearRampToValueAtTime(3200+H()*1500,t+dur);s.connect(bp);bp.connect(g);g.connect(pan((H()-.5)*.8,fxB));
 g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(.28,t+.02);g.gain.setValueAtTime(.28,t+dur*.8);g.gain.linearRampToValueAtTime(0,t+dur);s.start(t,H());s.stop(t+dur+.05);}
return {cajita,celesta,arpa,cuerdas,bajo,plumon};
};})()