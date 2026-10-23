/* Escenario de «yoshi es un vector 4_cuaternion» para la biblioteca de instrumentos: las declaraciones que usan sus instrumentos, tal cual,
   sacadas de meleeviewer/output/Arte/2026-09-28_yoshi_es_un_vector_4_cuaternion/cancion.js (sha256 b802d780c7c7) por herramientas/escenarios_meleeviewer.cjs.
   Cambios: ctx → el que se dé; master → la salida que se dé (seco). Nombres que no se encontraron: r. */
(function(){'use strict';return async function(__ctx,__salida,opts){opts=opts||{};
const hz=n=>440*2**((n-69)/12);
const ctx=__ctx;
const instB=ctx.createGain();
instB.gain.value=opts.inst??1;
const pan=(p,to)=>{const s=ctx.createStereoPanner();s.pan.value=Math.max(-1,Math.min(1,p));s.connect(to);return s;};
const env=(g,t,a,peak,dec,sus=0.0001,tail=.05,end)=>{g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(peak,t+a);g.gain.setTargetAtTime(Math.max(sus,.0001),t+a,dec);if(end!=null)g.gain.setTargetAtTime(0,end,tail);};
function vibr(o,t,rate,cents,delay,dur){const l=ctx.createOscillator(),lg=ctx.createGain();l.frequency.value=rate;lg.gain.setValueAtTime(0,t);lg.gain.setValueAtTime(0,t+delay);lg.gain.linearRampToValueAtTime(cents,t+delay+.3);l.connect(lg);lg.connect(o.detune);l.start(t);l.stop(t+dur+.5);}
function ep(t,n,dur,vel,p=0){const f=hz(n),c=ctx.createOscillator(),mo=ctx.createOscillator(),mg=ctx.createGain(),g=ctx.createGain(),ti=ctx.createOscillator(),tg=ctx.createGain(),out=pan(p,instB);
 c.frequency.value=f;mo.frequency.value=f;mg.gain.setValueAtTime(f*1.5*vel,t);mg.gain.setTargetAtTime(f*.15,t,.18);mo.connect(mg);mg.connect(c.frequency);
 ti.frequency.value=f*14.2;tg.gain.setValueAtTime(.025*vel,t);tg.gain.setTargetAtTime(0,t,.012);ti.connect(tg);tg.connect(out);
 env(g,t,.005,.12*vel,.6,.05*vel,.08,t+dur);c.connect(g);g.connect(out);[c,mo,ti].forEach(o=>{o.start(t);o.stop(t+dur+.7);});}
function bass(t,n,dur,vel){const f=hz(n),o=ctx.createOscillator(),s=ctx.createOscillator(),lp=ctx.createBiquadFilter(),g=ctx.createGain(),sg=ctx.createGain();o.type='triangle';o.frequency.value=f;s.frequency.value=f;
 lp.type='lowpass';lp.Q.value=2;lp.frequency.setValueAtTime(260+900*vel,t);lp.frequency.setTargetAtTime(240,t,.09);o.connect(lp);lp.connect(g);s.connect(sg);sg.gain.value=1;sg.connect(g);
 env(g,t,.008,.3*vel,.3,.18*vel,.04,t+dur);g.connect(instB);[o,s].forEach(x=>{x.start(t);x.stop(t+dur+.3);});}
/* cajita de música: parciales de lengüeta de metal, cortitos y brillantes */
function cajita(t,n,vel,p=0){const out=pan(p,instB);[[1,1,1.1],[3.01,.25,.35],[5.9,.08,.12]].forEach(([r,a,d])=>{const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.value=hz(n)*r;env(g,t,.002,.07*vel*a,d/3);o.connect(g);g.connect(out);o.start(t);o.stop(t+d*3);});}
function vibes(t,n,vel,p=0,dur=1.8){const out=pan(p,instB),g=ctx.createGain(),trem=ctx.createGain(),l=ctx.createOscillator(),lg=ctx.createGain();trem.gain.value=.78;l.frequency.value=5;lg.gain.value=.22;l.connect(lg);lg.connect(trem.gain);l.start(t);l.stop(t+dur+.2);
 [[1,1,dur],[4,.2,.35],[10,.04,.08]].forEach(([r,a,d])=>{const o=ctx.createOscillator(),og=ctx.createGain();o.frequency.value=hz(n)*r;env(og,t,.002,a,d/2.5);o.connect(og);og.connect(g);o.start(t);o.stop(t+d*2.5);});g.gain.value=.065*vel;g.connect(trem);trem.connect(out);}
function pad(t,n,dur,vel,p=0){const out=pan(p,instB),lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.frequency.value=1900;lp.connect(g);g.connect(out);
 [-9,0,9].forEach(dt=>{const o=ctx.createOscillator();o.type='sawtooth';o.frequency.value=hz(n);o.detune.value=dt;vibr(o,t,4.6,6,.5,dur);o.connect(lp);o.start(t);o.stop(t+dur+1);});env(g,t,.5,.02*vel,1.8,.018*vel,.35,t+dur);}
function flauta(t,n,dur,vel,p=0){const out=pan(p,instB),g=ctx.createGain(),o=ctx.createOscillator();o.frequency.setValueAtTime(hz(n),t);vibr(o,t,5.2,16,.25,dur);o.connect(g);g.connect(out);env(g,t,.06,.07*vel,.5,.055*vel,.1,t+dur);o.start(t);o.stop(t+dur+.4);}
instB.connect(__salida);  /* bus sin salida en el escenario */
return {ep,bass,cajita,vibes,pad,flauta};
};})()