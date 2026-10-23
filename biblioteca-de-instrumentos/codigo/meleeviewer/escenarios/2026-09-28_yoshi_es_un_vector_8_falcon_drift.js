/* Escenario de «yoshi es un vector 8_falcon_drift» para la biblioteca de instrumentos: las declaraciones que usan sus instrumentos, tal cual,
   sacadas de meleeviewer/output/Arte/2026-09-28_yoshi_es_un_vector_8_falcon_drift/cancion.js (sha256 4936e2fc358a) por herramientas/escenarios_meleeviewer.cjs.
   Cambios: ctx → el que se dé; master → la salida que se dé (seco). Nombres que no se encontraron: ty, cut. */
(function(){'use strict';return async function(__ctx,__salida,opts){opts=opts||{};
const SEED='yoshi-es-un-vector-8-falcon-drift';
const BPM=156;
const SPB=60/BPM;
const SR=44100;
function hash(s){let h=1779033703^s.length;for(let i=0;i<s.length;i++){h=Math.imul(h^s.charCodeAt(i),3432918353);h=h<<13|h>>>19;}h=Math.imul(h^h>>>16,2246822507);h=Math.imul(h^h>>>13,3266489909);return (h^h>>>16)>>>0;}
function rng(tag){let a=hash(SEED+':'+tag);return ()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}
const hz=n=>440*2**((n-69)/12);
const ctx=__ctx;
const H=rng('humano');
const master=__salida;
master.gain.value=.8;
const mk=v=>{const g=ctx.createGain();g.gain.value=v;g.connect(master);return g;};
const synB=mk(1);
const bassB=mk(1);
const fxB=mk(opts.fx??.7);
const dsyn=ctx.createGain();
dsyn.gain.value=0;
const pan=(p,to)=>{const s=ctx.createStereoPanner();s.pan.value=Math.max(-1,Math.min(1,p));s.connect(to);return s;};
const env=(g,t,a,peak,dec,sus=0.0001,tail=.05,end)=>{g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(peak,t+a);g.gain.setTargetAtTime(Math.max(sus,.0001),t+a,dec);if(end!=null)g.gain.setTargetAtTime(0,end,tail);};
const DET=[-36,-22,-9,0,9,22,36];
function saw7(t,n,dur,vel,{cut=3200,cutEnd=null,cutT=null,a=.004,dec=.3,sus=.6,rel=.1,bus=synB,det=DET,w=.7,q=.8,echo=0}={}){
 const g=ctx.createGain(),sides=[-w,w].map(p=>{const lp=ctx.createBiquadFilter();lp.type='lowpass';lp.Q.value=q;lp.frequency.setValueAtTime(cut,t);if(cutEnd!=null)lp.frequency.setTargetAtTime(cutEnd,t+.002,cutT??dur/3);lp.connect(pan(p,g));return lp;});
 det.forEach((d,i)=>{const o=ctx.createOscillator(),og=ctx.createGain();o.type='sawtooth';o.frequency.value=hz(n);o.detune.value=d+(H()-.5)*4;og.gain.value=1.4/det.length;o.connect(og);og.connect(sides[i%2]);o.start(t);o.stop(t+dur+rel*6);});
 const out=ctx.createGain();g.connect(out);out.connect(bus);if(echo){const e=ctx.createGain();e.gain.value=echo;out.connect(e);e.connect(dsyn);dsyn.gain.value=1;}env(out,t,a,vel,dec,vel*sus,rel,t+dur);}
function stab(t,notes,vel){notes.forEach(n=>saw7(t,n+12,SPB*.3,vel*.09,{cut:6500,cutEnd:700,cutT:.06,dec:.08,sus:.3,rel:.04,det:[-14,0,14],w:.5}));}
function bassO(t,n,dur,vel){const lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.Q.value=5;lp.frequency.setValueAtTime(380+1500*vel,t);lp.frequency.setTargetAtTime(300,t,.05);lp.connect(g);g.connect(bassB);
 [['sawtooth',0,.5],['sawtooth',7,.4],['square',-1200,.45]].forEach(([ty,d,a])=>{const o=ctx.createOscillator(),og=ctx.createGain();o.type=ty;o.frequency.value=hz(n);o.detune.value=d;og.gain.value=a;o.connect(og);og.connect(lp);o.start(t);o.stop(t+dur+.2);});
 env(g,t,.003,.34*vel,.12,.2*vel,.02,t+dur);}
function sub(t,n,dur,vel){const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.value=hz(n);o.connect(g);g.connect(bassB);env(g,t,.02,.45*vel,1,.4*vel,.1,t+dur);o.start(t);o.stop(t+dur+.6);}
function arp(t,n,vel,p=0){const o=ctx.createOscillator(),lp=ctx.createBiquadFilter(),g=ctx.createGain();o.type='square';o.frequency.value=hz(n);lp.type='lowpass';lp.frequency.setValueAtTime(4200,t);lp.frequency.setTargetAtTime(900,t,.05);o.connect(lp);lp.connect(g);g.connect(pan(p,synB));env(g,t,.002,.035*vel,.06);o.start(t);o.stop(t+.4);}
function pad(t,notes,dur,vel,cut=1800){notes.forEach(n=>saw7(t,n+12,dur,vel*.05,{cut,a:.25,dec:1.5,sus:.85,rel:.4,w:.9}));}
const nb=ctx.createBuffer(1,SR*2,SR);
const nr=rng('ruido');
{const d=nb.getChannelData(0);for(let k=0;k<d.length;k++)d[k]=nr()*2-1;};
function noise(t,dur){const s=ctx.createBufferSource();s.buffer=nb;s.loop=true;s.start(t);s.stop(t+dur+.1);return s;}
function riser(t,dur,vel=1){const s=noise(t,dur),bp=ctx.createBiquadFilter(),g=ctx.createGain();bp.type='bandpass';bp.Q.value=2.5;bp.frequency.setValueAtTime(300,t);bp.frequency.exponentialRampToValueAtTime(9000,t+dur);
 g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(.32*vel,t+dur);g.gain.setValueAtTime(0,t+dur);s.connect(bp);bp.connect(g);g.connect(pan(0,fxB));
 const o=ctx.createOscillator(),og=ctx.createGain();o.type='sawtooth';o.frequency.setValueAtTime(110,t);o.frequency.exponentialRampToValueAtTime(880,t+dur);og.gain.setValueAtTime(.0001,t);og.gain.exponentialRampToValueAtTime(.05*vel,t+dur);og.gain.setValueAtTime(0,t+dur);o.connect(og);og.connect(fxB);o.start(t);o.stop(t+dur+.05);}
function impact(t,vel=1){const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.setValueAtTime(160,t);o.frequency.exponentialRampToValueAtTime(32,t+.9);o.connect(g);g.connect(fxB);env(g,t,.003,.9*vel,.45);o.start(t);o.stop(t+2.5);
 const s=noise(t,1.5),lp=ctx.createBiquadFilter(),ng=ctx.createGain();lp.type='lowpass';lp.frequency.setValueAtTime(5000,t);lp.frequency.exponentialRampToValueAtTime(200,t+1.2);s.connect(lp);lp.connect(ng);ng.connect(fxB);env(ng,t,.002,.45*vel,.25);}
/* el derrapón: ruido en banda angosta que chilla y se tambalea */
function derrape(t,dur=1.1){const s=noise(t,dur),bp=ctx.createBiquadFilter(),g=ctx.createGain(),l=ctx.createOscillator(),lg=ctx.createGain();bp.type='bandpass';bp.Q.value=16;bp.frequency.setValueAtTime(3100,t);bp.frequency.linearRampToValueAtTime(2300,t+dur);
 l.frequency.value=9;lg.gain.value=260;l.connect(lg);lg.connect(bp.frequency);l.start(t);l.stop(t+dur);s.connect(bp);bp.connect(g);g.connect(pan(.3,fxB));g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(.55,t+.05);g.gain.setValueAtTime(.55,t+dur*.6);g.gain.linearRampToValueAtTime(0,t+dur);}
dsyn.connect(__salida);  /* bus sin salida en el escenario */
return {saw7,stab,bassO,sub,arp,pad,riser,impact,derrape};
};})()