/* biblioteca de instrumentos · motor Web Audio (v1, loop 01).
   Lee una ficha (fichas/<id>.json) y toca una nota en un AudioContext u OfflineAudioContext. Sin dependencias.
   Sirve en el navegador (window.Instrumentos) y en node con un AudioContext compatible (module.exports).

   tocar(ctx, destino, ficha, nota, opciones) → segundos que dura
     nota     = {t: hora en el ctx, midi, vel: 0–1, dur: s (sostén del arpa de boca)}
     opciones = {ruido: AudioBuffer (si no, se crea el sembrado), tonica: 'D' o 0–11, escala: [semitonos]}
   La tónica y la escala sólo las usan los instrumentos con notas propias: teponaztli (dos lenguas), berimbau (al aire y con
   piedra) y arpa de boca (la tónica es su lengüeta). Todo es determinista: el ruido sale de una semilla fija (1729), igual que
   en consola, así que la misma ficha suena igual muestra por muestra. */
(function(root){'use strict';
const NOTAS=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'];
const hz=n=>440*2**((n-69)/12);
const pcDe=t=>typeof t==='number'?((t%12)+12)%12:Math.max(0,NOTAS.indexOf(t));
function sembrado(seed){let a=seed>>>0;return ()=>{a=a+0x6D2B79F5>>>0;let t=a;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return ((t^t>>>14)>>>0)/4294967296;};}
const RUIDOS=new WeakMap();
function ruido(ctx){if(RUIDOS.has(ctx))return RUIDOS.get(ctx);const r=sembrado(1729),b=ctx.createBuffer(1,ctx.sampleRate*2,ctx.sampleRate),d=b.getChannelData(0);for(let i=0;i<d.length;i++)d[i]=r()*2-1;RUIDOS.set(ctx,b);return b;}
/* Formantes de las vocales del español (F1, F2, F3), los mismos de la voz que lee de consola. */
const FORMANTES={a:[800,1200,2500],e:[450,1900,2550],i:[300,2200,2950],o:[500,900,2400],u:[320,750,2350]};
/* Dos notas: la tónica y la nota de la escala más cercana a `cerca` semitonos arriba; toda nota cae en la más cercana. */
function lenguas(pc,escala,mid,cerca){const iv=escala.filter(x=>x>0).reduce((a,x)=>Math.abs(x-cerca)<Math.abs(a-cerca)?x:a,escala[1]||cerca),low=12+pc,d=((Math.round(mid)-low)%12+12)%12;
 const c=[0,iv,12].reduce((a,x)=>Math.abs(x-d)<Math.abs(a-d)?x:a,0);return Math.round(mid)-d+c;}

/* golpe: barras, lengüetas y lenguas (idiófonos). Ver la ficha: parts = [razón, nivel, caída s, ataque s]. */
function golpe(ctx,K,at,n,env,nodos,osc,o){const S=K.fisica,mid=S.tongues?lenguas(o.pc,o.escala,n.midi,5):n.midi,f=hz(mid),v=Math.max(.0002,n.vel),sc=Math.min(2.5,Math.max(.3,Math.pow(262/f,S.dk))),ny=ctx.sampleRate*.45;
 const sum=ctx.createGain();let out=sum,end=.05;
 if(S.trem){const tg=ctx.createGain(),lfo=osc('sine',S.trem[0],S.trem[1]/2);tg.gain.value=1-S.trem[1]/2;lfo.g.connect(tg.gain);out.connect(tg);out=tg;}
 if(S.lp){const lp=ctx.createBiquadFilter();lp.type='lowpass';lp.frequency.value=S.lp;out.connect(lp);out=lp;}
 if(S.drive){const ws=ctx.createWaveShaper(),cv=new Float32Array(1024),g=1+S.drive*6;for(let i=0;i<1024;i++){const x=i/511.5-1;cv[i]=Math.tanh(x*g)/Math.tanh(g);}ws.curve=cv;out.connect(ws);out=ws;}
 out.connect(env);
 const cents=S.loose?(Math.abs(Math.sin(mid*12.9898+7.233)*43758.5453)%1*2-1)*S.loose:0;
 S.parts.forEach(([r,g,d,a=.002],k)=>{const ff=f*r*2**((k?cents*1.6:cents)/1200),dd=d*sc;if(ff>ny)return;
  (S.pair?[-S.pair/2,S.pair/2]:[0]).forEach(dh=>{const {o:os,g:gg}=osc('sine',ff+dh,0);if(S.shift){os.frequency.setValueAtTime((ff+dh)*2**(S.shift/1200),at);os.frequency.exponentialRampToValueAtTime(ff+dh,at+.05);}
   const lv=g/(S.pair?1.6:1);gg.gain.setValueAtTime(0,at);gg.gain.linearRampToValueAtTime(lv,at+a);gg.gain.exponentialRampToValueAtTime(.0001,at+a+dd);gg.connect(sum);});end=Math.max(end,a+dd);});
 const nz=()=>{const s=ctx.createBufferSource();s.buffer=o.ruido;s.loop=true;nodos.push(s);return s;};
 if(S.click){const [cf,q,cg,cd]=S.click,bp=ctx.createBiquadFilter(),g=ctx.createGain();bp.type='bandpass';bp.frequency.value=Math.min(ny,cf);bp.Q.value=q;nz().connect(bp);bp.connect(g);g.connect(sum);
  g.gain.setValueAtTime(0,at);g.gain.linearRampToValueAtTime(cg,at+.001);g.gain.exponentialRampToValueAtTime(.0001,at+.001+cd);}
 if(S.buzz){const [amt,hpf]=S.buzz,ws=ctx.createWaveShaper(),cv=new Float32Array(1024),hp=ctx.createBiquadFilter(),g=ctx.createGain(),rect=ctx.createWaveShaper(),rc=new Float32Array(1024),ng=ctx.createGain(),bp=ctx.createBiquadFilter();
  for(let i=0;i<1024;i++){const x=i/511.5-1;cv[i]=x>.12?1:x<-.3?-.6:0;rc[i]=Math.max(0,Math.abs(x)-.05);}ws.curve=cv;rect.curve=rc;hp.type='highpass';hp.frequency.value=hpf;g.gain.value=amt*1.4;
  sum.connect(ws);ws.connect(hp);hp.connect(g);g.connect(env);
  bp.type='bandpass';bp.frequency.value=hpf*1.8;bp.Q.value=1.4;ng.gain.value=0;nz().connect(bp);bp.connect(ng);sum.connect(rect);rect.connect(ng.gain);const ng2=ctx.createGain();ng2.gain.value=amt*2.5;ng.connect(ng2);ng2.connect(env);}
 if(S.body){const [bf,q,bg]=S.body,bp=ctx.createBiquadFilter(),g=ctx.createGain();bp.type='bandpass';bp.frequency.value=bf;bp.Q.value=q;g.gain.value=bg;sum.connect(bp);bp.connect(g);g.connect(out===sum?env:out);}
 const L=.3*v*S.gain;env.gain.setValueAtTime(L,at);env.gain.setValueAtTime(L,at+end);env.gain.exponentialRampToValueAtTime(.0001,at+end+.08);return end+.08;}

/* boca: arpa de boca. La lengüeta es la tónica grave; la boca pone el formante de una vocal sobre el armónico que pide la nota. */
function boca(ctx,K,at,n,env,nodos,osc,o){const S=K.fisica,v=Math.max(.0002,n.vel);let dm=12*(S.octava+1)+o.pc;while(hz(dm)>S.maxHz)dm-=12;while(hz(dm)<S.minHz)dm+=12;
 const f0=hz(dm);let h=Math.round(hz(n.midi)/f0);while(h>S.armonicos[1])h=Math.round(h/2);while(h<S.armonicos[0])h*=2;const ft=h*f0;
 const N=64,re=new Float32Array(N),im=new Float32Array(N);for(let k=1;k<N;k++)im[k]=1/Math.pow(k,S.brillo);const os=ctx.createOscillator();os.setPeriodicWave(ctx.createPeriodicWave(re,im));os.frequency.value=f0;nodos.push(os);
 const src=ctx.createGain(),hold=Math.max(.25,n.dur||.5);os.connect(src);src.gain.setValueAtTime(0,at);src.gain.linearRampToValueAtTime(1,at+.003);src.gain.exponentialRampToValueAtTime(.35,at+.2);src.gain.setTargetAtTime(.0001,at+hold,.25);
 let best=null;for(const vw of 'aeiou')for(const k of [0,1]){const c=Math.abs(Math.log(FORMANTES[vw][k]/ft));if(!best||c<best.c)best={c,vw,k};}
 const F=FORMANTES[best.vw],from=ft*2**((h%2?S.deslizar:-S.deslizar));
 F.forEach((fq,k)=>{const bp=ctx.createBiquadFilter(),g=ctx.createGain();bp.type='bandpass';const on=k===best.k;bp.Q.value=on?S.qBoca:S.qOtros;g.gain.value=on?S.nivelBoca:S.nivelOtros;
  if(on){bp.frequency.setValueAtTime(from,at);bp.frequency.setTargetAtTime(ft,at+.005,.035);}else bp.frequency.value=fq;src.connect(bp);bp.connect(g);g.connect(env);});
 const lp=ctx.createBiquadFilter(),dg=ctx.createGain();lp.type='lowpass';lp.frequency.value=f0*2.5;dg.gain.value=S.cuerpo;src.connect(lp);lp.connect(dg);dg.connect(env);
 const L=.3*v*S.gain,end=hold+1.1;env.gain.setValueAtTime(L,at);env.gain.setValueAtTime(L,at+end-.1);env.gain.exponentialRampToValueAtTime(.0001,at+end);return end;}

/* arco: berimbau. Alambre rígido golpeado; dos notas (al aire / con piedra); chiado si se toca suave; cabaça y caxixi. */
function arco(ctx,K,at,n,env,nodos,osc,o){const S=K.fisica,mid=lenguas(o.pc,o.escala,n.midi,S.cerca),f=hz(mid),v=Math.max(.0002,n.vel),chiado=n.vel<S.chiado,ny=ctx.sampleRate*.45,sc=Math.min(1.6,Math.max(.5,Math.pow(130/f,.4)));
 const sum=ctx.createGain();let end=.1;
 for(let k=1;k<=S.parciales;k++){const fn=k*f*Math.sqrt(1+S.inarmonia*k*k);if(fn>ny)break;const lv=Math.abs(Math.sin(k*Math.PI*S.golpe))/Math.pow(k,.55),d=(chiado?S.caidaChiado:S.caida)/(1+.12*k)*sc,{g}=osc('sine',fn,0);
  g.gain.setValueAtTime(0,at);g.gain.linearRampToValueAtTime(lv,at+.002);g.gain.exponentialRampToValueAtTime(.0001,at+.002+d);g.connect(sum);end=Math.max(end,d+.002);}
 const [c0,c1,ct,cq,cg]=S.cabaca,dry=ctx.createGain(),bp=ctx.createBiquadFilter(),wg=ctx.createGain();dry.gain.value=S.seco;sum.connect(dry);dry.connect(env);
 bp.type='bandpass';bp.Q.value=cq;bp.frequency.setValueAtTime(c0,at);bp.frequency.exponentialRampToValueAtTime(c1,at+ct);wg.gain.value=cg;sum.connect(bp);bp.connect(wg);wg.connect(env);
 const nz=(fc,q,lv,d,t=0)=>{const s=ctx.createBufferSource(),f2=ctx.createBiquadFilter(),g=ctx.createGain();s.buffer=o.ruido;s.loop=true;nodos.push(s);g.gain.value=0;/* sin esto, un golpe con retraso suena a ganancia 1 hasta que llega */f2.type='bandpass';f2.frequency.value=Math.min(ny,fc);f2.Q.value=q;
  s.connect(f2);f2.connect(g);g.connect(env);g.gain.setValueAtTime(0,at+t);g.gain.linearRampToValueAtTime(lv,at+t+.002);g.gain.exponentialRampToValueAtTime(.0001,at+t+.002+d);end=Math.max(end,t+d+.002);};
 nz(2500,1.5,.5,.012);if(chiado)nz(3400,2,.7,.07);nz(7000,1.2,.22,.045);nz(7600,1.2,.12,.035,.11);
 const L=.3*v*S.gain;env.gain.setValueAtTime(L,at);env.gain.setValueAtTime(L,at+end);env.gain.exponentialRampToValueAtTime(.0001,at+end+.06);return end+.06;}

const MOTORES={golpe,boca,arco};
function tocar(ctx,destino,ficha,nota,opciones={}){const fn=MOTORES[ficha.motor];if(!fn)throw Error('Este motor no sabe tocar «'+ficha.motor+'» ('+ficha.id+')');
 const at=nota.t??ctx.currentTime,env=ctx.createGain(),nodos=[];env.connect(destino);env.gain.setValueAtTime(0,at);
 const osc=(type,f,gain=1,detune=0)=>{const o=ctx.createOscillator(),g=ctx.createGain();o.type=type;o.frequency.setValueAtTime(f,at);o.detune.value=detune;g.gain.value=gain;o.connect(g);nodos.push(o);return {o,g};};
 const o={ruido:opciones.ruido||ruido(ctx),pc:pcDe(opciones.tonica??'C'),escala:opciones.escala||[0,2,4,7,9]};
 const end=fn(ctx,ficha,at,nota,env,nodos,osc,o),stop=at+end+.05;nodos.forEach(nd=>{nd.start(at);nd.stop(stop);});return end;}
const api={version:1,tocar,ruido,hz,lenguas,FORMANTES,motores:Object.keys(MOTORES)};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.Instrumentos=api;
})(typeof window!=='undefined'?window:globalThis);
