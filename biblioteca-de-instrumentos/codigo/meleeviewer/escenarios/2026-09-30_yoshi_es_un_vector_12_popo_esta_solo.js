/* Escenario de «yoshi es un vector 12_popo_esta_solo» para la biblioteca de instrumentos: las declaraciones que usan sus instrumentos, tal cual,
   sacadas de meleeviewer/output/Arte/2026-09-30_yoshi_es_un_vector_12_popo_esta_solo/cancion.js (sha256 73b51862aed3) por herramientas/escenarios_meleeviewer.cjs.
   Cambios: ctx → el que se dé; master → la salida que se dé (seco). Nombres que no se encontraron: r. */
(function(){'use strict';return async function(__ctx,__salida,opts){opts=opts||{};
const SEED='yoshi-es-un-vector-12-popo-esta-solo';
function hash(s){let h=1779033703^s.length;for(let i=0;i<s.length;i++){h=Math.imul(h^s.charCodeAt(i),3432918353);h=h<<13|h>>>19;}h=Math.imul(h^h>>>16,2246822507);h=Math.imul(h^h>>>13,3266489909);return (h^h>>>16)>>>0;}
function rng(tag){let a=hash(SEED+':'+tag);return ()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}
const hz=n=>440*2**((n-69)/12);
const ctx=__ctx;
const H=rng('humano');
const master=__salida;
master.gain.value=.8;
const mk=(v,to=master)=>{const g=ctx.createGain();g.gain.value=v;g.connect(to);return g;};
const inst=mk(opts.inst??.7);
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
return {marimba,bajo,colchon,hielo};
};})()