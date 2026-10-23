/* Escenario de «yoshi es un vector 10_la_mitocondria_es_un_pokemon» para la biblioteca de instrumentos: las declaraciones que usan sus instrumentos, tal cual,
   sacadas de meleeviewer/output/Arte/2026-09-29_yoshi_es_un_vector_10_la_mitocondria_es_un_pokemon/cancion.js (sha256 90e51b08aa81) por herramientas/escenarios_meleeviewer.cjs.
   Cambios: ctx → el que se dé; master → la salida que se dé (seco). Nombres que no se encontraron: r, ty. */
(function(){'use strict';return async function(__ctx,__salida,opts){opts=opts||{};
const SEED='yoshi-es-un-vector-10-la-mitocondria-es-un-pokemon';
const BPM=108;
const SPB=60/BPM;
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
/* Rhodes FM */
function ep(t,n,dur,vel,p=0){const f=hz(n),c=ctx.createOscillator(),mo=ctx.createOscillator(),mg=ctx.createGain(),g=ctx.createGain(),ti=ctx.createOscillator(),tg=ctx.createGain(),out=pan(p,inst);
 c.frequency.value=f;mo.frequency.value=f;mg.gain.setValueAtTime(f*1.6*vel,t);mg.gain.setTargetAtTime(f*.15,t,.18);mo.connect(mg);mg.connect(c.frequency);
 ti.frequency.value=f*14.2;tg.gain.setValueAtTime(.022*vel,t);tg.gain.setTargetAtTime(0,t,.012);ti.connect(tg);tg.connect(out);
 env(g,t,.005,.11*vel,.6,.045*vel,.08,t+dur);c.connect(g);g.connect(out);[c,mo,ti].forEach(o=>{o.start(t);o.stop(t+dur+.7);});}
/* bajo funky: sierra + cuadrada con filtro que muerde */
function bajo(t,n,dur,vel){const lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.Q.value=6;lp.frequency.setValueAtTime(300+1800*vel,t);lp.frequency.setTargetAtTime(260,t,.06);lp.connect(g);g.connect(inst);
 [['sawtooth',0,.55],['square',-1200,.5]].forEach(([ty,d,a])=>{const o=ctx.createOscillator(),og=ctx.createGain();o.type=ty;o.frequency.value=hz(n);o.detune.value=d;og.gain.value=a;o.connect(og);og.connect(lp);o.start(t);o.stop(t+dur+.2);});
 env(g,t,.004,.36*vel,.14,.18*vel,.025,t+dur);}
const ksr=rng('cuerda');
function cuerda(t,n,dur,vel,apagada=false,p=0){const f=hz(n),N=Math.max(2,Math.round(SR/f)),len=Math.ceil(SR*Math.min(dur+.3,2.5)),b=ctx.createBuffer(1,len,SR),d=b.getChannelData(0),buf=new Float32Array(N);
 for(let i=0;i<N;i++)buf[i]=(ksr()*2-1);const damp=apagada?.93:.996;let k=0,prev=0;
 for(let i=0;i<len;i++){const v=buf[k],nx=buf[(k+1)%N];const y=damp*.5*(v+nx);buf[k]=y;d[i]=v*(apagada?Math.exp(-i/SR/.045):1);k=(k+1)%N;}
 const s=ctx.createBufferSource(),g=ctx.createGain(),lp=ctx.createBiquadFilter();lp.type='lowpass';lp.frequency.value=apagada?1800:4200;s.buffer=b;s.connect(lp);lp.connect(g);g.connect(pan(p,inst));g.gain.setValueAtTime(.16*vel,t);g.gain.setTargetAtTime(0,t+dur,.05);s.start(t);s.stop(t+len/SR);}
function rasgueo(t,notes,vel,apagada,p){notes.forEach((n,i)=>cuerda(t+i*.007,n,apagada?.08:SPB*1.5,vel*(1-i*.08),apagada,p));}
function cuerdas(t,notes,dur,vel){const lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.frequency.value=2600;lp.connect(g);g.connect(inst);
 notes.forEach((n,i)=>[-8,0,8].forEach(dt=>{const o=ctx.createOscillator();o.type='sawtooth';o.frequency.value=hz(n);o.detune.value=dt+(H()-.5)*6;vibr(o,t,4.8+i*.2,7,.4,dur);o.connect(pan((i-1.5)*.35,lp));o.start(t);o.stop(t+dur+1.2);}));
 env(g,t,.45,.016*vel,1.5,.014*vel,.4,t+dur);}
function metal(t,notes,dur,vel){notes.forEach((n,i)=>{const lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.Q.value=2;lp.frequency.setValueAtTime(600,t);lp.frequency.linearRampToValueAtTime(3200*vel+800,t+.05);lp.frequency.setTargetAtTime(1200,t+.08,.15);lp.connect(g);g.connect(pan((i-1.5)*.3,inst));
 [['sawtooth',0],['sawtooth',6],['square',-4]].forEach(([ty,d])=>{const o=ctx.createOscillator();o.type=ty;o.frequency.value=hz(n);o.detune.value=d;o.connect(lp);o.start(t);o.stop(t+dur+.3);});env(g,t,.025,.03*vel,.25,.022*vel,.05,t+dur);});}
function glock(t,n,vel,p=0){const out=pan(p,inst);[[1,1,1.4],[2.76,.3,.4],[5.4,.12,.15]].forEach(([r,a,d])=>{const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.value=hz(n)*r;env(g,t,.001,.05*vel*a,d/3);o.connect(g);g.connect(out);o.start(t);o.stop(t+d*3);});}
function pluck(t,n,vel,p=0){const o=ctx.createOscillator(),lp=ctx.createBiquadFilter(),g=ctx.createGain();o.type='square';o.frequency.value=hz(n);lp.type='lowpass';lp.frequency.setValueAtTime(4000,t);lp.frequency.setTargetAtTime(700,t,.05);o.connect(lp);lp.connect(g);g.connect(pan(p,inst));env(g,t,.002,.04*vel,.07);o.start(t);o.stop(t+.4);}
const nb=ctx.createBuffer(1,SR*2,SR);
const nr=rng('ruido');
{const d=nb.getChannelData(0);for(let k=0;k<d.length;k++)d[k]=nr()*2-1;};
function riser(t,dur,vel=1){const s=ctx.createBufferSource(),bp=ctx.createBiquadFilter(),g=ctx.createGain();s.buffer=nb;s.loop=true;bp.type='bandpass';bp.Q.value=2.5;bp.frequency.setValueAtTime(300,t);bp.frequency.exponentialRampToValueAtTime(9000,t+dur);
 g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(.25*vel,t+dur);g.gain.setValueAtTime(0,t+dur);s.connect(bp);bp.connect(g);g.connect(fxB);s.start(t);s.stop(t+dur+.05);}
return {ep,bajo,cuerda,rasgueo,cuerdas,metal,glock,pluck,riser};
};})()