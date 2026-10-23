/* Escenario de «yoshi es un vector 3_kirby» para la biblioteca de instrumentos: las declaraciones que usan sus instrumentos, tal cual,
   sacadas de meleeviewer/output/Arte/2026-09-28_yoshi_es_un_vector_3_kirby/cancion.js (sha256 ae9c2a3a8da3) por herramientas/escenarios_meleeviewer.cjs.
   Cambios: ctx → el que se dé; master → la salida que se dé (seco). Nombres que no se encontraron: r. */
(function(){'use strict';return async function(__ctx,__salida,opts){opts=opts||{};
const SEED='yoshi-es-un-vector-3-kirby';
const SR=44100;
function hash(s){let h=1779033703^s.length;for(let i=0;i<s.length;i++){h=Math.imul(h^s.charCodeAt(i),3432918353);h=h<<13|h>>>19;}h=Math.imul(h^h>>>16,2246822507);h=Math.imul(h^h>>>13,3266489909);return (h^h>>>16)>>>0;}
function rng(tag){let a=hash(SEED+':'+tag);return ()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}
const hz=n=>440*2**((n-69)/12);
const ctx=__ctx;
const H=rng('humano');
const instB=ctx.createGain();
const vocB=ctx.createGain();
const drumB=ctx.createGain();
instB.gain.value=opts.inst??1;
drumB.gain.value=opts.drums??1;
vocB.gain.value=opts.voc??1.6;
const nb=ctx.createBuffer(1,SR*2,SR);
const nr=rng('ruido');
{const d=nb.getChannelData(0);for(let k=0;k<d.length;k++)d[k]=nr()*2-1;};
const pan=(p,to)=>{const s=ctx.createStereoPanner();s.pan.value=Math.max(-1,Math.min(1,p));s.connect(to);return s;};
const env=(g,t,a,peak,dec,sus=0.0001,tail=.05,end)=>{g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(peak,t+a);g.gain.setTargetAtTime(Math.max(sus,.0001),t+a,dec);if(end!=null)g.gain.setTargetAtTime(0,end,tail);};
function noise(t,dur,rate=1){const s=ctx.createBufferSource();s.buffer=nb;s.loop=true;s.playbackRate.value=rate;s.start(t,H()*1.5);s.stop(t+dur);return s;}
function vib(o,t,rate,cents,delay,dur){const l=ctx.createOscillator(),lg=ctx.createGain();l.frequency.value=rate;lg.gain.setValueAtTime(0,t);lg.gain.setValueAtTime(0,t+delay);lg.gain.linearRampToValueAtTime(cents,t+delay+.25);l.connect(lg);lg.connect(o.detune);l.start(t);l.stop(t+dur+.5);}
/* Rhodes FM, bajo, glockenspiel y metales (los de siempre). */
function ep(t,n,dur,vel,p=0){const f=hz(n),c=ctx.createOscillator(),mo=ctx.createOscillator(),mg=ctx.createGain(),g=ctx.createGain(),ti=ctx.createOscillator(),tg=ctx.createGain(),out=pan(p,instB);
 c.frequency.value=f;mo.frequency.value=f;mg.gain.setValueAtTime(f*1.8*vel,t);mg.gain.setTargetAtTime(f*.18,t,.18);mo.connect(mg);mg.connect(c.frequency);
 ti.frequency.value=f*14.2;tg.gain.setValueAtTime(.035*vel,t);tg.gain.setTargetAtTime(0,t,.012);ti.connect(tg);tg.connect(out);
 env(g,t,.004,.13*vel,.5,.05*vel,.07,t+dur);c.connect(g);g.connect(out);[c,mo,ti].forEach(o=>{o.start(t);o.stop(t+dur+.6);});}
function bass(t,n,dur,vel){const f=hz(n),o=ctx.createOscillator(),s=ctx.createOscillator(),lp=ctx.createBiquadFilter(),g=ctx.createGain(),sg=ctx.createGain();o.type='sawtooth';o.frequency.value=f;s.frequency.value=f;
 lp.type='lowpass';lp.Q.value=4;lp.frequency.setValueAtTime(300+1700*vel,t);lp.frequency.setTargetAtTime(260,t,.07);o.connect(lp);lp.connect(g);s.connect(sg);sg.gain.value=.9;sg.connect(g);
 env(g,t,.006,.3*vel,.25,.17*vel,.03,t+dur);g.connect(instB);[o,s].forEach(x=>{x.start(t);x.stop(t+dur+.3);});}
function glock(t,n,vel,p=0){const out=pan(p,instB);[[1,1,1.3],[2.76,.32,.45],[5.4,.12,.18],[8.93,.05,.08]].forEach(([r,a,d])=>{const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.value=hz(n)*r;env(g,t,.002,.075*vel*a,d/3);o.connect(g);g.connect(out);o.start(t);o.stop(t+d*3);});}
function brass(t,n,dur,vel,p=0){const out=pan(p,instB),lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.Q.value=2;lp.frequency.setValueAtTime(700,t);lp.frequency.linearRampToValueAtTime(3400,t+.03);lp.frequency.setTargetAtTime(1300,t+.05,.1);lp.connect(g);g.connect(out);
 [-9,9].forEach(dt=>{const o=ctx.createOscillator();o.type='sawtooth';o.frequency.value=hz(n);o.detune.value=dt;o.connect(lp);o.start(t);o.stop(t+dur+.2);});env(g,t,.015,.06*vel,.2,.03*vel,.03,t+dur);}
/* Krar (lira etíope): dos triángulos desafinados y un filtro que se cierra rápido, con el clic de la uña. */
function krar(t,n,dur,vel,p=0){const out=pan(p,instB),lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.Q.value=3;lp.frequency.setValueAtTime(5200,t);lp.frequency.setTargetAtTime(750,t,.06);lp.connect(g);g.connect(out);
 [-7,7].forEach(dt=>{const o=ctx.createOscillator();o.type='triangle';o.frequency.value=hz(n);o.detune.value=dt;o.connect(lp);o.start(t);o.stop(t+dur+.5);});
 const sq=ctx.createOscillator(),sg=ctx.createGain();sq.type='square';sq.frequency.value=hz(n);sg.gain.value=.25;sq.connect(sg);sg.connect(lp);sq.start(t);sq.stop(t+dur+.5);
 env(g,t,.002,.1*vel,.22,.0001);const c=noise(t,.02,1.6),cg=ctx.createGain();cg.gain.value=.05*vel;c.connect(cg);cg.connect(out);}
/* Washint (flauta de bambú): entra resbalando desde abajo, vibrato tardío y soplo. */
function washint(t,n,dur,vel,p=0){const out=pan(p,instB),g=ctx.createGain(),o=ctx.createOscillator(),o2=ctx.createOscillator(),g2=ctx.createGain();o.type='sine';o2.type='triangle';g2.gain.value=.3;
 [o,o2].forEach(x=>{x.frequency.setValueAtTime(hz(n-2),t);x.frequency.exponentialRampToValueAtTime(hz(n),t+.09);vib(x,t,5.8,28,.18,dur);x.start(t);x.stop(t+dur+.3);});o.connect(g);o2.connect(g2);g2.connect(g);g.connect(out);
 const b=noise(t,dur+.2,1),bp=ctx.createBiquadFilter(),bg=ctx.createGain();bp.type='bandpass';bp.frequency.value=hz(n);bp.Q.value=5;b.connect(bp);bp.connect(bg);bg.connect(out);
 env(g,t,.05,.09*vel,.4,.07*vel,.08,t+dur);env(bg,t,.03,.05*vel,.15,.02*vel,.08,t+dur);}
/* Masenqo (violín de una cuerda): sierra con cuerpo de caja, vibrato ancho y ornamento que baja. */
function masenqo(t,n,dur,vel,p=0){const out=pan(p,instB),o=ctx.createOscillator(),body=ctx.createBiquadFilter(),lp=ctx.createBiquadFilter(),g=ctx.createGain();o.type='sawtooth';
 o.frequency.setValueAtTime(hz(n+1),t);o.frequency.exponentialRampToValueAtTime(hz(n),t+.12);vib(o,t,6.4,45,.12,dur);body.type='peaking';body.frequency.value=1100;body.Q.value=1.2;body.gain.value=9;lp.type='lowpass';lp.frequency.value=3600;
 o.connect(body);body.connect(lp);lp.connect(g);g.connect(out);env(g,t,.06,.075*vel,.3,.06*vel,.08,t+dur);o.start(t);o.stop(t+dur+.4);}
/* Vibráfono ethio-jazz: parciales 1 y 4 con trémolo del motor. */
function vibes(t,n,vel,p=0,dur=1.6){const out=pan(p,instB),g=ctx.createGain(),trem=ctx.createGain(),l=ctx.createOscillator(),lg=ctx.createGain();trem.gain.value=.75;l.frequency.value=5.5;lg.gain.value=.25;l.connect(lg);lg.connect(trem.gain);l.start(t);l.stop(t+dur+.2);
 [[1,1,dur],[4,.22,.35],[10,.05,.08]].forEach(([r,a,d])=>{const o=ctx.createOscillator(),og=ctx.createGain();o.frequency.value=hz(n)*r;env(og,t,.002,a,d/2.5);o.connect(og);og.connect(g);o.start(t);o.stop(t+d*2.5);});g.gain.value=.07*vel;g.connect(trem);trem.connect(out);}
/* Cuerdas: tres sierras desafinadas, ataque lento. */
function pad(t,n,dur,vel,p=0){const out=pan(p,instB),lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.frequency.value=2200;lp.connect(g);g.connect(out);
 [-11,0,11].forEach(dt=>{const o=ctx.createOscillator();o.type='sawtooth';o.frequency.value=hz(n);o.detune.value=dt;o.connect(lp);o.start(t);o.stop(t+dur+.8);});env(g,t,.35,.022*vel,1.5,.02*vel,.25,t+dur);}
function kick(t,v){const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.setValueAtTime(165,t);o.frequency.exponentialRampToValueAtTime(46,t+.09);env(g,t,.002,.95*v,.11);o.connect(g);g.connect(drumB);o.start(t);o.stop(t+.5);
 const n=noise(t,.01,1),ng=ctx.createGain();ng.gain.value=.25*v;n.connect(ng);ng.connect(drumB);}
function snare(t,v,p=0){const out=pan(p,drumB),n=noise(t,.3),bp=ctx.createBiquadFilter(),g=ctx.createGain();bp.type='bandpass';bp.frequency.value=1900;bp.Q.value=.7;env(g,t,.001,.42*v,.06);n.connect(bp);bp.connect(g);g.connect(out);
 const o=ctx.createOscillator(),og=ctx.createGain();o.type='triangle';o.frequency.setValueAtTime(200,t);o.frequency.exponentialRampToValueAtTime(160,t+.06);env(og,t,.001,.35*v,.03);o.connect(og);og.connect(out);o.start(t);o.stop(t+.25);}
function clap(t,v){const n=noise(t,.35),bp=ctx.createBiquadFilter(),g=ctx.createGain(),out=pan(.1,drumB);bp.type='bandpass';bp.frequency.value=1300;bp.Q.value=1.1;n.connect(bp);bp.connect(g);g.connect(out);
 g.gain.setValueAtTime(0,t);[0,.011,.023].forEach(d=>{g.gain.setValueAtTime(.35*v,t+d);g.gain.setTargetAtTime(.02,t+d+.001,.004);});g.gain.setValueAtTime(.3*v,t+.034);g.gain.setTargetAtTime(0,t+.035,.05);}
function hat(t,v,open=false){const n=noise(t,open?.5:.12,1.3),hp=ctx.createBiquadFilter(),g=ctx.createGain(),out=pan(-.25,drumB);hp.type='highpass';hp.frequency.value=7200;env(g,t,.001,.16*v,open?.1:.013);n.connect(hp);hp.connect(g);g.connect(out);}
function shaker(t,v){const n=noise(t,.12,.9),bp=ctx.createBiquadFilter(),g=ctx.createGain(),out=pan(.35,drumB);bp.type='bandpass';bp.frequency.value=6500;bp.Q.value=1.5;env(g,t,.012,.08*v,.018);n.connect(bp);bp.connect(g);g.connect(out);}
function crash(t,v){const n=noise(t,2.4,.8),hp=ctx.createBiquadFilter(),g=ctx.createGain();hp.type='highpass';hp.frequency.value=4200;env(g,t,.002,.2*v,.55);n.connect(hp);hp.connect(g);g.connect(drumB);}
function riser(t0,t1,v=.18){const n=noise(t0,t1-t0+.05),bp=ctx.createBiquadFilter(),g=ctx.createGain();bp.type='bandpass';bp.Q.value=3;bp.frequency.setValueAtTime(300,t0);bp.frequency.exponentialRampToValueAtTime(9000,t1);g.gain.setValueAtTime(0,t0);g.gain.linearRampToValueAtTime(v,t1);g.gain.setValueAtTime(0,t1+.01);n.connect(bp);bp.connect(g);g.connect(instB);}
/* 808: seno que cae de tono, saturado. */
function boom(t,v=1,st=0){const o=ctx.createOscillator(),g=ctx.createGain(),ws=ctx.createWaveShaper(),cv=new Float32Array(1024);for(let k=0;k<1024;k++){const x=k/511.5-1;cv[k]=Math.tanh(x*2.6);}ws.curve=cv;
 o.frequency.setValueAtTime(hz(45+st)*2.2,t);o.frequency.exponentialRampToValueAtTime(hz(45+st),t+.06);env(g,t,.003,.55*v,.35);o.connect(ws);ws.connect(g);g.connect(drumB);o.start(t);o.stop(t+1.6);}
/* ñam: golpe grave + chasquido. */
function bite(t,v=1){const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.setValueAtTime(220,t);o.frequency.exponentialRampToValueAtTime(70,t+.08);env(g,t,.002,.5*v,.05);o.connect(g);g.connect(vocB);o.start(t);o.stop(t+.3);
 const n=noise(t,.08,1),bp=ctx.createBiquadFilter(),ng=ctx.createGain();bp.type='bandpass';bp.frequency.value=2400;bp.Q.value=2;env(ng,t,.001,.3*v,.015);n.connect(bp);bp.connect(ng);ng.connect(vocB);}
function coin(t,v=1){const o=ctx.createOscillator(),g=ctx.createGain(),out=pan(.3,instB);o.type='square';o.frequency.setValueAtTime(hz(83),t);o.frequency.setValueAtTime(hz(88),t+.075);g.gain.setValueAtTime(.045*v,t);g.gain.setValueAtTime(.045*v,t+.075);g.gain.setTargetAtTime(0,t+.09,.12);o.connect(g);g.connect(out);o.start(t);o.stop(t+.8);}
instB.connect(__salida);  /* bus sin salida en el escenario */
vocB.connect(__salida);  /* bus sin salida en el escenario */
drumB.connect(__salida);  /* bus sin salida en el escenario */
return {ep,bass,glock,brass,krar,washint,masenqo,vibes,pad,kick,snare,clap,hat,shaker,crash,riser,boom,bite,coin};
};})()