/* Escenario de «yoshi es un vector 9_coro_de_gritos» para la biblioteca de instrumentos: las declaraciones que usan sus instrumentos, tal cual,
   sacadas de meleeviewer/output/Arte/2026-09-29_yoshi_es_un_vector_9_coro_de_gritos/cancion.js (sha256 a9629f3e34b4) por herramientas/escenarios_meleeviewer.cjs.
   Cambios: ctx → el que se dé; master → la salida que se dé (seco). Nombres que no se encontraron: cut. */
(function(){'use strict';return async function(__ctx,__salida,opts){opts=opts||{};
const DIR='/biblioteca-de-instrumentos/codigo/meleeviewer/datos/2026-09-29_yoshi_es_un_vector_9_coro_de_gritos/';
const P=await (await fetch(DIR+'partitura.json')).json();
const SEED=P.seed;
const SR=44100;
function hash(s){let h=1779033703^s.length;for(let i=0;i<s.length;i++){h=Math.imul(h^s.charCodeAt(i),3432918353);h=h<<13|h>>>19;}h=Math.imul(h^h>>>16,2246822507);h=Math.imul(h^h>>>13,3266489909);return (h^h>>>16)>>>0;}
function rng(tag){let a=hash(SEED+':'+tag);return ()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}
const hz=n=>440*2**((n-69)/12);
const ctx=__ctx;
const H=rng('humano');
const master=__salida;
master.gain.value=.8;
const mk=(v,to=master)=>{const g=ctx.createGain();g.gain.value=v;g.connect(to);return g;};
const inst=mk(opts.inst??.6);
const synB=mk(1,inst);
const bassB=mk(1,inst);
const fxB=mk(opts.fx??.6);
const pan=(p,to)=>{const s=ctx.createStereoPanner();s.pan.value=Math.max(-1,Math.min(1,p));s.connect(to);return s;};
const env=(g,t,a,peak,dec,sus=0.0001,tail=.05,end)=>{g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(peak,t+a);g.gain.setTargetAtTime(Math.max(sus,.0001),t+a,dec);if(end!=null)g.gain.setTargetAtTime(0,end,tail);};
const DET=[-38,-24,-10,0,10,24,38];
function saw7(t,n,dur,vel,{cut=3200,cutEnd=null,cutT=null,a=.004,dec=.3,sus=.6,rel=.1,bus=synB,det=DET,w=.75,q=.8}={}){
 const g=ctx.createGain(),sides=[-w,w].map(p=>{const lp=ctx.createBiquadFilter();lp.type='lowpass';lp.Q.value=q;lp.frequency.setValueAtTime(cut,t);if(cutEnd!=null)lp.frequency.setTargetAtTime(cutEnd,t+.002,cutT??dur/3);lp.connect(pan(p,g));return lp;});
 det.forEach((d,i)=>{const o=ctx.createOscillator(),og=ctx.createGain();o.type='sawtooth';o.frequency.value=hz(n);o.detune.value=d+(H()-.5)*4;og.gain.value=1.4/det.length;o.connect(og);og.connect(sides[i%2]);o.start(t);o.stop(t+dur+rel*6);});
 const out=ctx.createGain();g.connect(out);out.connect(bus);env(out,t,a,vel,dec,vel*sus,rel,t+dur);}
function sub(t,n,dur,vel,glide=null){const o=ctx.createOscillator(),s=ctx.createOscillator(),g=ctx.createGain(),sg=ctx.createGain();o.frequency.setValueAtTime(hz(n),t);if(glide!=null)o.frequency.exponentialRampToValueAtTime(hz(glide),t+dur*.9);
 s.type='triangle';s.frequency.setValueAtTime(hz(n+12),t);if(glide!=null)s.frequency.exponentialRampToValueAtTime(hz(glide+12),t+dur*.9);sg.gain.value=.25;s.connect(sg);sg.connect(g);o.connect(g);g.connect(bassB);env(g,t,.008,.55*vel,.8,.45*vel,.06,t+dur);[o,s].forEach(x=>{x.start(t);x.stop(t+dur+.5);});}
function arp(t,n,vel,p=0){const o=ctx.createOscillator(),o2=ctx.createOscillator(),lp=ctx.createBiquadFilter(),g=ctx.createGain();o.type='triangle';o2.type='square';o.frequency.value=hz(n);o2.frequency.value=hz(n)*2.001;const g2=ctx.createGain();g2.gain.value=.15;o2.connect(g2);g2.connect(lp);
 lp.type='lowpass';lp.frequency.setValueAtTime(5000,t);lp.frequency.setTargetAtTime(1200,t,.06);o.connect(lp);lp.connect(g);g.connect(pan(p,synB));env(g,t,.002,.06*vel,.08);[o,o2].forEach(x=>{x.start(t);x.stop(t+.5);});}
function pad(t,notes,dur,vel,cut=1600){notes.forEach(n=>saw7(t,n+12,dur,vel*.035,{cut,a:.4,dec:1.5,sus:.85,rel:.5,w:.95}));}
const nb=ctx.createBuffer(1,SR*2,SR);
const nr=rng('ruido');
{const d=nb.getChannelData(0);for(let k=0;k<d.length;k++)d[k]=nr()*2-1;};
function noise(t,dur){const s=ctx.createBufferSource();s.buffer=nb;s.loop=true;s.start(t);s.stop(t+dur+.1);return s;}
function riser(t,dur,vel=1){const s=noise(t,dur),bp=ctx.createBiquadFilter(),g=ctx.createGain();bp.type='bandpass';bp.Q.value=2.5;bp.frequency.setValueAtTime(300,t);bp.frequency.exponentialRampToValueAtTime(10000,t+dur);
 g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(.3*vel,t+dur);g.gain.setValueAtTime(0,t+dur);s.connect(bp);bp.connect(g);g.connect(fxB);}
function impact(t,vel=1){const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.setValueAtTime(140,t);o.frequency.exponentialRampToValueAtTime(30,t+1);o.connect(g);g.connect(fxB);env(g,t,.003,.9*vel,.5);o.start(t);o.stop(t+2.5);
 const s=noise(t,1.5),lp=ctx.createBiquadFilter(),ng=ctx.createGain();lp.type='lowpass';lp.frequency.setValueAtTime(6000,t);lp.frequency.exponentialRampToValueAtTime(200,t+1.2);s.connect(lp);lp.connect(ng);ng.connect(fxB);env(ng,t,.002,.4*vel,.25);}
function reverso(t,dur){const s=noise(t-dur,dur),hp=ctx.createBiquadFilter(),g=ctx.createGain();hp.type='highpass';hp.frequency.value=2000;g.gain.setValueAtTime(.0001,t-dur);g.gain.exponentialRampToValueAtTime(.35,t-.01);g.gain.setValueAtTime(0,t);s.connect(hp);hp.connect(g);g.connect(fxB);}
return {saw7,sub,arp,pad,riser,impact,reverso};
};})()