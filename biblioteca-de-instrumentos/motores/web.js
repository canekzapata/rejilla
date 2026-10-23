/* biblioteca de instrumentos · motor Web Audio (v2, loop 02: + voz, receta, bateria de consola).
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

/* ── Copiado tal cual de consola (static/lectura/musica.js, huella 724d5b2d5624) para tocar sus voces, recetas y batería desde una ficha.
      Sólo se cambia el envoltorio: `b.noise` es el ruido sembrado de la biblioteca (el mismo), y la nota llega como `ev`. ── */
const DRUM_KITS={acustico:{kick:[120,52,.07,.32,.3],snare:'acustico',hat:[7500,.035],open:.28,tom:[1.6,.05,.3,'sine'],drive:0},
 tr808:{kick:[110,45,.05,.9,.08],snare:'tr808',hat:'metal',open:.35,tom:[1.3,.08,.55,'sine'],drive:0},
 tr909:{kick:[190,50,.03,.45,.5],snare:'tr909',hat:[9000,.05],open:.3,tom:[1.5,.04,.35,'triangle'],drive:0},
 frito:{kick:[110,45,.05,.9,.15],snare:'tr808',hat:'metal',open:.35,tom:[1.3,.08,.55,'sine'],drive:.65}};
const METAL=[205.3,304.4,369.6,522.7,540,800];
function drumVoice(ctx,b,at,ev,env,nodes,osc){const K=DRUM_KITS[ev.kit]||DRUM_KITS.acustico,tn=2**((ev.tune||0)/12),dc=ev.decay||1,drive=Math.max(ev.drive||0,K.drive);let out=env,end=.05;
 if(drive>0){const ws=ctx.createWaveShaper(),cv=new Float32Array(1024),g=1+drive*9;for(let i=0;i<1024;i++){const x=i/511.5-1;cv[i]=Math.tanh(x*g)/Math.tanh(g);}ws.curve=cv;ws.connect(env);out=ws;}
 env.gain.setValueAtTime(Math.max(.0002,ev.vel),at);
 const amp=(node,level,a,d)=>{const g=ctx.createGain();g.gain.setValueAtTime(0,at);g.gain.linearRampToValueAtTime(level,at+a);g.gain.exponentialRampToValueAtTime(.0001,at+a+d);node.connect(g);g.connect(out);end=Math.max(end,a+d);return g;};
 const tone=(type,f0,f1,glide,level,a,d)=>{const {o,g}=osc(type,f0);if(f1&&f1!==f0)o.frequency.exponentialRampToValueAtTime(f1,at+glide);amp(g,level,a,d);};
 const noise=(rate=1)=>{const s=ctx.createBufferSource();s.buffer=b.noise;s.loop=true;s.playbackRate.value=rate;nodes.push(s);return s;};
 const hiss=(type,freq,q,level,a,d,rate=1)=>{const f=ctx.createBiquadFilter();f.type=type;f.frequency.value=freq;f.Q.value=q;noise(rate).connect(f);amp(f,level,a,d);};
 const metal=(freqs,freq,level,a,d)=>{const f=ctx.createBiquadFilter(),hp=ctx.createBiquadFilter();f.type='bandpass';f.frequency.value=freq;hp.type='highpass';hp.frequency.value=freq*.6;freqs.forEach(x=>osc('square',x*tn,.18).g.connect(f));f.connect(hp);amp(hp,level,a,d);};
 const P=ev.pieza;
 if(P==='kick'){const [f0,f1,gl,d,click]=K.kick;tone('sine',f0*tn,f1*tn,gl,1,.002,d*dc);hiss('highpass',3000,.7,click,.001,.012);}
 else if(P==='snare'){if(K.snare==='tr808'){tone('sine',238*tn,0,0,.45,.001,.09*dc);tone('sine',476*tn,0,0,.25,.001,.06*dc);hiss('highpass',1800,.7,.5,.001,.13*dc);}
  else if(K.snare==='tr909'){tone('triangle',185*tn,165*tn,.05,.55,.001,.07*dc);hiss('bandpass',3500,.6,.6,.001,.2*dc);}
  else{tone('triangle',200*tn,160*tn,.06,.5,.001,.08*dc);hiss('bandpass',1900,.7,.6,.001,.17*dc);}}
 else if(P==='rim'){tone('triangle',820*tn,0,0,.35,.001,.025*dc);hiss('bandpass',3200,4,.6,.001,.015);}
 else if(P==='clap'){const f=ctx.createBiquadFilter(),g=ctx.createGain();f.type='bandpass';f.frequency.value=1300*tn;f.Q.value=1.1;noise().connect(f);f.connect(g);g.connect(out);g.gain.setValueAtTime(0,at);
  [0,.011,.023].forEach(d=>{g.gain.setValueAtTime(.7,at+d);g.gain.setTargetAtTime(.04,at+d+.001,.004);});g.gain.setValueAtTime(.6,at+.034);g.gain.setTargetAtTime(0,at+.035,.05*dc);end=Math.max(end,.035+.3*dc);}
 else if(P==='hat'||P==='openhat'){const d=(P==='hat'?(K.hat==='metal'?.05:K.hat[1]):K.open)*dc;if(K.hat==='metal')metal(METAL,10000,.9,.001,d);else hiss('highpass',K.hat[0],.7,.4,.001,d,1.3);}
 else if(P==='crash'){hiss('highpass',4200,.7,.5,.002,1.6*dc,.8);if(K.hat==='metal')metal(METAL,8000,.35,.002,1.2*dc);}
 else if(P==='ride'){metal(METAL.map(x=>x*1.1),6500,.35,.001,.9*dc);tone('sine',3200*tn,0,0,.12,.001,.6*dc);hiss('highpass',6000,.7,.12,.001,.5*dc);}
 /* Spray: el platillo de las cajas de ritmos de los ochenta. Ruido reducido a pocos escalones (el grano de un sampler de 8 bits),
    sin graves, con un brillo en 9.5 kHz y una caída casi recta: «pssshhh». */
 else if(P==='spray'){const q=ctx.createWaveShaper(),cv=new Float32Array(1024),hp=ctx.createBiquadFilter(),pk=ctx.createBiquadFilter(),g=ctx.createGain();for(let i=0;i<1024;i++){const x=i/511.5-1;cv[i]=Math.round(x*7)/7;}q.curve=cv;
  hp.type='highpass';hp.frequency.value=5200*tn;pk.type='peaking';pk.frequency.value=9500;pk.Q.value=.8;pk.gain.value=7;noise(.71).connect(q);q.connect(hp);hp.connect(pk);pk.connect(g);g.connect(out);
  const d=1.3*dc;g.gain.setValueAtTime(0,at);g.gain.linearRampToValueAtTime(.5,at+.006);g.gain.linearRampToValueAtTime(.2,at+.006+d*.3);g.gain.exponentialRampToValueAtTime(.0001,at+.006+d);end=Math.max(end,.006+d);}
 else if(P==='tomhi'||P==='tommid'||P==='tomlo'){const f={tomhi:220,tommid:165,tomlo:110}[P]*tn,[up,gl,d,w]=K.tom;tone(w,f*up,f,gl,.8,.002,d*dc);hiss('bandpass',f*4,1,.12,.001,.03);}
 else if(P==='cowbell'){metal([540,800],800,.6,.001,.25*dc);}
 return end;}
function recipeVoice(ctx,b,at,ev,env,nodes,osc){const r=ev.recipe,f=hz(ev.midi),v=Math.max(.0002,ev.vel),sum=ctx.createGain();let out=sum;
 if(r.filterType!=='none'){const fl=ctx.createBiquadFilter();fl.type=r.filterType;fl.Q.value=r.filterQ;fl.frequency.setValueAtTime(Math.min(18000,Math.max(30,r.filterFreq*2**r.sweep)),at);fl.frequency.exponentialRampToValueAtTime(r.filterFreq,at+r.attack+r.decay);sum.connect(fl);out=fl;}out.connect(env);
 const oscs=r.partials.map(p=>{const {o,g}=osc(p.wave,f*p.ratio,p.gain/Math.max(1,r.partials.length)*1.4,p.detune);g.connect(sum);return o;});
 if(r.fmIndex>0&&r.fmRatio>0){const mod=osc('sine',f*r.fmRatio,f*r.fmIndex);mod.g.gain.setValueAtTime(f*r.fmIndex,at);mod.g.gain.exponentialRampToValueAtTime(Math.max(.01,f*r.fmIndex*.05),at+r.fmDecay);oscs.forEach(o=>mod.g.connect(o.frequency));}
 if(r.vibDepth>0&&r.vibRate>0){const lfo=osc('sine',r.vibRate,0);lfo.g.gain.setValueAtTime(0,at+r.vibDelay);lfo.g.gain.linearRampToValueAtTime(f*(2**(r.vibDepth/1200)-1),at+r.vibDelay+.3);oscs.forEach(o=>lfo.g.connect(o.frequency));}
 if(r.noise>0){const src=ctx.createBufferSource(),bp=ctx.createBiquadFilter(),g=ctx.createGain();src.buffer=b.noise;src.loop=true;bp.type='bandpass';bp.frequency.value=Math.min(12000,f*2);bp.Q.value=1.2;g.gain.value=r.noise*.6;src.connect(bp);bp.connect(g);g.connect(sum);nodes.push(src);}
 const level=.34*v*r.gain,sus=Math.max(.0001,level*r.sustain),hold=Math.max(0,(ev.dur||.5)-r.attack-r.decay);env.gain.linearRampToValueAtTime(level,at+r.attack);env.gain.linearRampToValueAtTime(sus,at+r.attack+r.decay);env.gain.setValueAtTime(sus,at+r.attack+r.decay+hold);env.gain.exponentialRampToValueAtTime(.0001,at+r.attack+r.decay+hold+r.release);return r.attack+r.decay+hold+r.release;}
/* voz: las siete voces de consola (kalimba, cuerda pulsada, campana FM, vidrio, colchón, bajo, zumbido). fisica.tipo = cuál. */
function voz(ctx,K,at,n,env,nodos,osc,o){const ev={instr:K.fisica.tipo,dur:n.dur??.7,vel:n.vel},f=hz(n.midi),v=Math.max(.0002,n.vel);
 const shape=(level,attack,decay,hold=0)=>{env.gain.linearRampToValueAtTime(level,at+attack);if(hold)env.gain.setValueAtTime(level,at+attack+hold);env.gain.exponentialRampToValueAtTime(.0001,at+attack+hold+decay);return attack+hold+decay;};
 let end=.5;
  if(ev.instr==='pluck'){const {g}=osc('sawtooth',f),lp=ctx.createBiquadFilter();lp.type='lowpass';lp.frequency.setValueAtTime(4200,at);lp.frequency.exponentialRampToValueAtTime(Math.max(120,f*2),at+.3);g.connect(lp);lp.connect(env);end=shape(.22*v,.004,Math.max(.4,ev.dur));}
  else if(ev.instr==='kalimba'){osc('sine',f).g.connect(env);const t=osc('sine',f*5.4,.25);t.g.connect(env);t.g.gain.setValueAtTime(.25,at);t.g.gain.exponentialRampToValueAtTime(.001,at+.15);end=shape(.3*v,.002,1.1);}
  else if(ev.instr==='bell'){const c=osc('sine',f),mod=osc('sine',f*3.5,f*2.5);mod.g.gain.setValueAtTime(f*2.5,at);mod.g.gain.exponentialRampToValueAtTime(f*.1,at+1.6);mod.g.connect(c.o.frequency);c.g.connect(env);end=shape(.25*v,.003,2.4);}
  else if(ev.instr==='glass'){osc('sine',f*2).g.connect(env);osc('sine',f*2*2.76,.3).g.connect(env);end=shape(.18*v,.003,1.6);}
  else if(ev.instr==='pad'){const lp=ctx.createBiquadFilter();lp.type='lowpass';lp.frequency.value=1200;lp.connect(env);[-7,0,7].forEach(dt=>osc('sawtooth',f,.33,dt).g.connect(lp));end=shape(.12*v,.5,1.2,Math.max(0,ev.dur-.5));}
  else if(ev.instr==='bass'){osc('sine',f).g.connect(env);const lp=ctx.createBiquadFilter();lp.type='lowpass';lp.frequency.value=400;osc('square',f,.3).g.connect(lp);lp.connect(env);end=shape(.35*v,.005,.6);}
  else if(ev.instr==='drone'){osc('triangle',f).g.connect(env);osc('sine',f*1.5,.5).g.connect(env);end=shape(.14*v,1,1.5,Math.max(0,ev.dur-1));}
 return end;}
/* receta: un instrumento inventado (parciales, filtro con barrido, vibrato, FM, aire). fisica = la receta. */
function receta(ctx,K,at,n,env,nodos,osc,o){return recipeVoice(ctx,{noise:o.ruido},at,{recipe:K.fisica,midi:n.midi,vel:n.vel,dur:n.dur??.7},env,nodos,osc);}
/* bateria: un kit; la nota dice qué pieza (nota.pieza) y con qué fuerza; tune, decay y drive vienen de la ficha (o de la nota). */
function bateria(ctx,K,at,n,env,nodos,osc,o){const F=K.fisica;return drumVoice(ctx,{noise:o.ruido},at,{kit:F.kit,pieza:n.pieza,vel:n.vel,tune:n.tune??F.tune,decay:n.decay??F.decay,drive:n.drive??F.drive},env,nodos,osc);}

const MOTORES={golpe,boca,arco,voz,receta,bateria};
function tocar(ctx,destino,ficha,nota,opciones={}){const fn=MOTORES[ficha.motor];if(!fn)throw Error('Este motor no sabe tocar «'+ficha.motor+'» ('+ficha.id+')');
 const at=nota.t??ctx.currentTime,env=ctx.createGain(),nodos=[];env.connect(destino);env.gain.setValueAtTime(0,at);
 const osc=(type,f,gain=1,detune=0)=>{const o=ctx.createOscillator(),g=ctx.createGain();o.type=type;o.frequency.setValueAtTime(f,at);o.detune.value=detune;g.gain.value=gain;o.connect(g);nodos.push(o);return {o,g};};
 const o={ruido:opciones.ruido||ruido(ctx),pc:pcDe(opciones.tonica??'C'),escala:opciones.escala||[0,2,4,7,9]};
 const end=fn(ctx,ficha,at,nota,env,nodos,osc,o),stop=at+end+.05;nodos.forEach(nd=>{nd.start(at);nd.stop(stop);});return end;}
const api={version:2,tocar,ruido,hz,lenguas,FORMANTES,motores:Object.keys(MOTORES)};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.Instrumentos=api;
})(typeof window!=='undefined'?window:globalThis);
