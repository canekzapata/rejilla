/* Escenario de «yoshi es un vector 11_que_dice_el_zorro» para la biblioteca de instrumentos: las declaraciones que usan sus instrumentos, tal cual,
   sacadas de meleeviewer/output/Arte/2026-09-29_yoshi_es_un_vector_11_que_dice_el_zorro/cancion.js (sha256 43581006d974) por herramientas/escenarios_meleeviewer.cjs.
   Cambios: ctx → el que se dé; master → la salida que se dé (seco). Nombres que no se encontraron: ninguno. */
(function(){'use strict';return async function(__ctx,__salida,opts){opts=opts||{};
const SEED='yoshi-es-un-vector-11-que-dice-el-zorro';
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
const nb=ctx.createBuffer(1,SR*2,SR);
const nr=rng('ruido');
{const d=nb.getChannelData(0);for(let k=0;k<d.length;k++)d[k]=nr()*2-1;};
function piano(t,n,dur,vel,p=0){const f=hz(n),Bi=.0004*(n<60?1:.6),out=pan(p,inst),g=ctx.createGain();g.connect(out);g.gain.value=1;
 for(let k=1;k<=8;k++){const fk=k*f*Math.sqrt(1+Bi*k*k);if(fk>9000)break;const o=ctx.createOscillator(),og=ctx.createGain();o.frequency.value=fk;const a=vel*.05/Math.pow(k,1.25)*(k===2?1.3:1),dec=Math.max(.25,2.6-(n-40)*.03)/Math.sqrt(k);
  og.gain.setValueAtTime(0,t);og.gain.linearRampToValueAtTime(a,t+.003);og.gain.setTargetAtTime(a*.4,t+.003,dec*.15);og.gain.setTargetAtTime(0,t+.05,dec);og.gain.setTargetAtTime(0,t+dur,.12);o.connect(og);og.connect(g);o.start(t);o.stop(t+dur+1.2);}
 const s=ctx.createBufferSource(),bp=ctx.createBiquadFilter(),hg=ctx.createGain();s.buffer=nb;bp.type='bandpass';bp.frequency.value=f*3;bp.Q.value=1.2;s.connect(bp);bp.connect(hg);hg.connect(out);env(hg,t,.001,.03*vel,.015);s.start(t,(n%7)*.1);s.stop(t+.1);}
const ksr=rng('cuerda');
function arpa(t,n,vel,p=0){const f=hz(n),N=Math.max(2,Math.round(SR/f)),len=Math.ceil(SR*2.2),b=ctx.createBuffer(1,len,SR),d=b.getChannelData(0),buf=new Float32Array(N);
 for(let i=0;i<N;i++)buf[i]=(ksr()*2-1)*(i<N/2?1:.6);let k=0;for(let i=0;i<len;i++){const v=buf[k],nx=buf[(k+1)%N];buf[k]=.997*.5*(v+nx);d[i]=v;k=(k+1)%N;}
 const s=ctx.createBufferSource(),g=ctx.createGain(),lp=ctx.createBiquadFilter();lp.type='lowpass';lp.frequency.value=3800;s.buffer=b;s.connect(lp);lp.connect(g);g.connect(pan(p,inst));g.gain.value=.1*vel;s.start(t);}
function cuerdas(t,notes,dur,vel){const lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.frequency.value=2300;lp.connect(g);g.connect(inst);
 notes.forEach((n,i)=>[-9,0,9].forEach(dt=>{const o=ctx.createOscillator();o.type='sawtooth';o.frequency.value=hz(n);o.detune.value=dt+(H()-.5)*6;vibr(o,t,4.7+i*.2,7,.5,dur);o.connect(pan((i-1.5)*.4,lp));o.start(t);o.stop(t+dur+1.5);}));
 env(g,t,.7,.015*vel,1.8,.013*vel,.6,t+dur);}
function colchon(t,notes,dur,vel){const lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.frequency.setValueAtTime(700,t);lp.frequency.linearRampToValueAtTime(1500,t+dur*.5);lp.frequency.linearRampToValueAtTime(800,t+dur);lp.connect(g);g.connect(inst);
 notes.forEach((n,i)=>['triangle','sawtooth'].forEach((ty,j)=>{const o=ctx.createOscillator();o.type=ty;o.frequency.value=hz(n);o.detune.value=(j?7:-7);const og=ctx.createGain();og.gain.value=j?.4:1;o.connect(og);og.connect(pan((i-1.5)*.5,lp));o.start(t);o.stop(t+dur+2);}));env(g,t,1.2,.018*vel,2,.016*vel,.9,t+dur);}
function bajo(t,n,dur,vel){const o=ctx.createOscillator(),tr=ctx.createOscillator(),g=ctx.createGain(),tg=ctx.createGain(),lp=ctx.createBiquadFilter();o.frequency.value=hz(n);tr.type='triangle';tr.frequency.value=hz(n);tg.gain.value=.5;lp.type='lowpass';lp.frequency.value=700;
 tr.connect(tg);tg.connect(lp);o.connect(lp);lp.connect(g);g.connect(inst);env(g,t,.02,.4*vel,.6,.26*vel,.1,t+dur);[o,tr].forEach(x=>{x.start(t);x.stop(t+dur+.6);});}
/* la campana del traductor: FM de razón no entera, dobla cada traducción muy bajito */
function campana(t,n,vel,p=0){const f=hz(n),c=ctx.createOscillator(),m=ctx.createOscillator(),mg=ctx.createGain(),g=ctx.createGain();c.frequency.value=f;m.frequency.value=f*3.5;mg.gain.setValueAtTime(f*2.2,t);mg.gain.setTargetAtTime(f*.3,t,.3);m.connect(mg);mg.connect(c.frequency);
 c.connect(g);g.connect(pan(p,inst));env(g,t,.002,.045*vel,1.1);[c,m].forEach(x=>{x.start(t);x.stop(t+4);});}
function soplo(t,dur,vel=1){const s=ctx.createBufferSource(),bp=ctx.createBiquadFilter(),g=ctx.createGain();s.buffer=nb;s.loop=true;bp.type='bandpass';bp.Q.value=3;bp.frequency.setValueAtTime(400,t);bp.frequency.exponentialRampToValueAtTime(6000,t+dur);
 g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(.2*vel,t+dur);g.gain.setValueAtTime(0,t+dur);s.connect(bp);bp.connect(g);g.connect(fxB);s.start(t);s.stop(t+dur+.05);}
return {piano,arpa,cuerdas,colchon,bajo,campana,soplo};
};})()