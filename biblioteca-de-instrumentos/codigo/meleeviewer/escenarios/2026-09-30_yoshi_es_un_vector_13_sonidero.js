/* Escenario de «yoshi es un vector 13_sonidero» para la biblioteca de instrumentos: las declaraciones que usan sus instrumentos, tal cual,
   sacadas de meleeviewer/output/Arte/2026-09-30_yoshi_es_un_vector_13_sonidero/cancion.js (sha256 f8bdb1161d5c) por herramientas/escenarios_meleeviewer.cjs.
   Cambios: ctx → el que se dé; master → la salida que se dé (seco). Nombres que no se encontraron: f, ty, d. */
(function(){'use strict';return async function(__ctx,__salida,opts){opts=opts||{};
const SEED='yoshi-es-un-vector-13-sonidero';
const SR=44100;
function hash(s){let h=1779033703^s.length;for(let i=0;i<s.length;i++){h=Math.imul(h^s.charCodeAt(i),3432918353);h=h<<13|h>>>19;}h=Math.imul(h^h>>>16,2246822507);h=Math.imul(h^h>>>13,3266489909);return (h^h>>>16)>>>0;}
function rng(tag){let a=hash(SEED+':'+tag);return ()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}
const hz=n=>440*2**((n-69)/12);
const ctx=__ctx;
const master=__salida;
master.gain.value=.8;
const mk=(v,to=master)=>{const g=ctx.createGain();g.gain.value=v;g.connect(to);return g;};
const inst=mk(opts.inst??.65);
const fxB=mk(opts.fx??.5);
const ecoIn=ctx.createGain();
const pan=(p,to)=>{const s=ctx.createStereoPanner();s.pan.value=Math.max(-1,Math.min(1,p));s.connect(to);return s;};
const env=(g,t,a,peak,dec,sus=0.0001,tail=.05,end)=>{g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(peak,t+a);g.gain.setTargetAtTime(Math.max(sus,.0001),t+a,dec);if(end!=null)g.gain.setTargetAtTime(0,end,tail);};
const pumpB=mk(1,inst);
pumpB.connect(inst);
/* acordeón: dos lengüetas por nota (una 12 cents arriba = musette), cuadrada + sierra filtradas, con su fuelle */
function acordeon(t,n,dur,vel,p=0,bus=pumpB){const out=pan(p,bus),lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.frequency.value=2800;lp.Q.value=.7;lp.connect(g);g.connect(out);
 [[0,'square',.5],[13,'sawtooth',.4],[-1200,'square',.25]].forEach(([d,ty,a])=>{const o=ctx.createOscillator(),og=ctx.createGain();o.type=ty;o.frequency.value=hz(n);o.detune.value=d;og.gain.value=a;o.connect(og);og.connect(lp);o.start(t);o.stop(t+dur+.15);});
 env(g,t,.012,.035*vel,.2,.028*vel,.04,t+dur);}
function bajo(t,n,dur,vel){const lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.frequency.setValueAtTime(900,t);lp.frequency.setTargetAtTime(300,t,.08);lp.connect(g);g.connect(pumpB);
 [['sine',0,1],['triangle',0,.5],['sawtooth',-1200,.12]].forEach(([ty,d,a])=>{const o=ctx.createOscillator(),og=ctx.createGain();o.type=ty;o.frequency.value=hz(n);o.detune.value=d;og.gain.value=a;o.connect(og);og.connect(lp);o.start(t);o.stop(t+dur+.2);});
 env(g,t,.006,.5*vel,.25,.32*vel,.04,t+dur);}
const nb=ctx.createBuffer(1,SR*2,SR);
const nr=rng('ruido');
{const d=nb.getChannelData(0);for(let k=0;k<d.length;k++)d[k]=nr()*2-1;};
/* güiro: ruido en banda, raspado (modulado a ~70 Hz) */
function guiro(t,dur,vel,p=.3){const s=ctx.createBufferSource(),bp=ctx.createBiquadFilter(),g=ctx.createGain(),am=ctx.createGain(),l=ctx.createOscillator(),lg=ctx.createGain();s.buffer=nb;s.loop=true;bp.type='bandpass';bp.frequency.value=3800;bp.Q.value=1.6;
 l.type='sawtooth';l.frequency.value=70;lg.gain.value=.5;am.gain.value=.5;l.connect(lg);lg.connect(am.gain);s.connect(bp);bp.connect(am);am.connect(g);g.connect(pan(p,inst));env(g,t,.01,.22*vel,dur*.6,.0001,.02,t+dur);s.start(t,(t*7)%1.5);s.stop(t+dur+.05);l.start(t);l.stop(t+dur+.05);}
function conga(t,n,vel,p=-.3,slap=false){const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.setValueAtTime(hz(n)*1.5,t);o.frequency.exponentialRampToValueAtTime(hz(n),t+.03);o.connect(g);g.connect(pan(p,inst));env(g,t,.002,.32*vel,slap?.05:.13);o.start(t);o.stop(t+.5);
 if(slap){const s=ctx.createBufferSource(),hp=ctx.createBiquadFilter(),sg=ctx.createGain();s.buffer=nb;hp.type='highpass';hp.frequency.value=1800;s.connect(hp);hp.connect(sg);sg.connect(pan(p,inst));env(sg,t,.001,.18*vel,.025);s.start(t,.3);s.stop(t+.1);}}
function campana(t,vel,p=.4){[[587,1],[845,.6]].forEach(([f,a])=>{const o=ctx.createOscillator(),bp=ctx.createBiquadFilter(),g=ctx.createGain();o.type='square';o.frequency.value=f;bp.type='bandpass';bp.frequency.value=f*1.4;bp.Q.value=3;o.connect(bp);bp.connect(g);g.connect(pan(p,inst));env(g,t,.001,.05*vel*a,.07);o.start(t);o.stop(t+.4);});}
function riser(t,dur,vel=1){const s=ctx.createBufferSource(),bp=ctx.createBiquadFilter(),g=ctx.createGain();s.buffer=nb;s.loop=true;bp.type='bandpass';bp.Q.value=2;bp.frequency.setValueAtTime(400,t);bp.frequency.exponentialRampToValueAtTime(8000,t+dur);
 g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(.25*vel,t+dur);g.gain.setValueAtTime(0,t+dur);s.connect(bp);bp.connect(g);g.connect(fxB);s.start(t);s.stop(t+dur+.05);}
/* sirena de sonidero (la que suena en todos los bailes) */
function sirena(t,dur){const o=ctx.createOscillator(),l=ctx.createOscillator(),lg=ctx.createGain(),g=ctx.createGain();o.type='square';o.frequency.value=900;l.frequency.value=3;lg.gain.value=250;l.connect(lg);lg.connect(o.frequency);o.connect(g);g.connect(ecoIn);g.connect(pan(.2,fxB));env(g,t,.02,.035,dur,.03,.1,t+dur);[o,l].forEach(x=>{x.start(t);x.stop(t+dur+.3);});}
/* bombeo: cada bombo del dembow hunde 40 % y regresa */
pumpB.gain.setValueAtTime(1,0);
ecoIn.connect(__salida);  /* bus sin salida en el escenario */
return {acordeon,bajo,guiro,conga,campana,riser,sirena};
};})()