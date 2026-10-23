// Sonido del front: consola juguetona sobre escalas etíopes computadas, y la voz (port del vocoder
// del visor de lectura, consola/static/lectura/musica.js). Web Audio puro, sin muestras.
// Acuerdos de SONIDO.md: se activa por voluntad, no suena cada letra, memoria de fatiga,
// se cede al abrir una obra, se suspende con la pestaña oculta.
(()=>{
'use strict';

// ── Escalas. Las cuatro qenet de la tradición amhara, con sus variantes mayores y menores.
const QENET={
  'tizita':[0,2,4,7,9],'tizita menor':[0,2,3,7,8],
  'bati':[0,4,5,7,11],'bati menor':[0,3,5,7,10],
  'ambassel':[0,1,5,7,8],'anchihoye':[0,1,5,6,9],
};
const NOMBRES=Object.keys(QENET);
const rnd=(R,a,b)=>a+(b-a)*R();
function hashStr(s){let h=2166136261>>>0;for(const ch of String(s)){h^=ch.codePointAt(0);h=Math.imul(h,16777619)>>>0}return h}
function mulberry32(a){return()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}}

// Escala computada: una qenet, desafinada grado por grado (la tizita no es temperada) y pasada
// por una operación: rotar a otro modo, injertar el tetracordio de otra qenet, estirar la octava
// o invertirla en espejo. Devuelve los grados en cents y el tamaño de su "octava".
function computa(R,nombre){
  const base=nombre||NOMBRES[Math.floor(R()*NOMBRES.length)];
  let c=QENET[base].map((st,i)=>st*100+(i?rnd(R,-35,35):0)),octava=1200,op='';
  const k=Math.floor(R()*4);
  if(k===0){const r=1+Math.floor(R()*4);c=c.slice(r).concat(c.slice(0,r).map(x=>x+1200)).map(x=>x-c[r]);op=`rotada ${r}`}
  else if(k===1){const otra=NOMBRES[Math.floor(R()*NOMBRES.length)];c=c.slice(0,3).concat(QENET[otra].slice(3).map(st=>st*100+rnd(R,-20,20)));op=`injerto de ${otra}`}
  else if(k===2){octava=Math.round(rnd(R,1180,1228));c=c.map(x=>x*octava/1200);op=`octava de ${octava}¢`}
  else{c=c.map(x=>(1200-x)%1200).sort((a,b)=>a-b);op='espejo'}
  return{nombre:base,op,cents:c,octava};
}

// La semilla de la visita: ?semilla= la fija (así se reabre una visita desde su postal); sin ella se
// sortea una nueva en cada carga y no se escribe en la URL, para que recargar siga dando otro mundo.
const semillaVisita=window.CanekSemilla||(window.CanekSemilla=(()=>{
  const dada=(new URLSearchParams(location.search).get('semilla')||'').toLowerCase().replace(/[^a-z0-9]/g,'').slice(0,12);
  return dada||Math.floor(Math.random()*36**5).toString(36).padStart(5,'0');
})());
const R0=mulberry32(hashStr('escala:'+semillaVisita));
let ESCALA=computa(R0);   // let: escribir el nombre de una qenet la cambia
const RAIZ=110*Math.pow(2,Math.floor(rnd(R0,0,7))/12);   // tónica de la visita: la2 a mi3
const freq=(deg,oct=1,esc=ESCALA)=>{const n=esc.cents.length,o=Math.floor(deg/n),d=((deg%n)+n)%n;
  return RAIZ*Math.pow(2,(oct*1200+o*esc.octava+esc.cents[d])/1200)};

// ── Motor
let ctx=null,master=null,verb=null,ruido=null,activo=false,cedido=false,voces=0;
const recientes=[];
const CLAVE='canek-front-sonido';
try{activo=sessionStorage.getItem(CLAVE)==='si'}catch{}

function arranca(){
  if(ctx)return;
  ctx=new (window.AudioContext||window.webkitAudioContext)();
  ({master,verb,ruido}=montaSalida(ctx));master.gain.value=0;
}
// la cadena de salida (compresor, recorte suave, ruido y reverb sembrados) sobre cualquier contexto
function montaSalida(ctx){
  const master=ctx.createGain();
  // salida: compresor fuerte y, al final, un recorte suave (tanh) para que nada pase de 1.0
  const lim=ctx.createDynamicsCompressor();lim.threshold.value=-14;lim.knee.value=2;lim.ratio.value=20;lim.attack.value=.001;lim.release.value=.18;
  const clip=ctx.createWaveShaper(),cc=new Float32Array(2048);for(let i=0;i<2048;i++){const x=i/1023.5-1;cc[i]=Math.tanh(1.4*x)/Math.tanh(1.4)*.92}clip.curve=cc;
  master.connect(lim);lim.connect(clip);clip.connect(ctx.destination);
  // ruido y reverberación sembrados: nada de muestras externas
  const Rn=mulberry32(hashStr('ruido-front'));
  const ruido=ctx.createBuffer(1,ctx.sampleRate,ctx.sampleRate);
  const d=ruido.getChannelData(0);for(let i=0;i<d.length;i++)d[i]=Rn()*2-1;
  const verb=ctx.createConvolver();
  const len=Math.floor(ctx.sampleRate*1.6),ir=ctx.createBuffer(2,len,ctx.sampleRate);
  for(let ch=0;ch<2;ch++){const x=ir.getChannelData(ch);for(let i=0;i<len;i++)x[i]=(Rn()*2-1)*Math.pow(1-i/len,3)}
  verb.buffer=ir;const vg=ctx.createGain();vg.gain.value=.28;verb.connect(vg);vg.connect(master);
  return{master,verb,ruido};
}
function sube(){if(reproductorCanto)reproductorCanto.muted=false;if(!ctx)return;master.gain.cancelScheduledValues(ctx.currentTime);master.gain.setTargetAtTime(.42,ctx.currentTime,.08)}
function baja(){if(reproductorCanto)reproductorCanto.muted=true;if(!ctx)return;master.gain.cancelScheduledValues(ctx.currentTime);master.gain.setTargetAtTime(0,ctx.currentTime,.06)}
let grabando=false;   // al renderizar una canción a archivo, el motor toca aunque el sonido esté apagado
const puede=()=>grabando||(activo&&!cedido&&ctx&&ctx.state==='running');

// fatiga: la actividad de los últimos 15 segundos baja la probabilidad y el volumen de lo decorativo
function fatiga(){const t=performance.now();while(recientes.length&&t-recientes[0]>15000)recientes.shift();return recientes.length}
function decorativo(p=1){if(!puede()||voces>4)return 0;const f=fatiga();if(Math.random()>p*Math.max(.15,1-f/24))return 0;recientes.push(performance.now());return 1/(1+f/14)}
// con dest, la reverb va a la reverb propia de ese canal (dest._verb), para que el fundido del canal también la calle
const salida=(g,rev=.35,dest=null)=>{g.connect(dest||master);if(rev){const s=ctx.createGain();s.gain.value=rev;g.connect(s);s.connect(dest?._verb||verb)}};
let capturandoCanto=false,fuentesCanto=new Set();
function registraVoz(nodos){
  if(grabando)return;
  voces++;
  nodos[0]?.addEventListener('ended',()=>{voces=Math.max(0,voces-1)},{once:true});
  if(capturandoCanto){const sources=fuentesCanto;for(const node of nodos){sources.add(node);node.addEventListener('ended',()=>sources.delete(node),{once:true})}}
}
const vive=(nodos,fin,inicio)=>{registraVoz(nodos);nodos.forEach(n=>{n.start?.(inicio);n.stop?.(fin)})};

// ── Instrumentos
// krar: lira pulsada; un filtro que se cierra y el zumbido bezez (una sierra saturada que se apaga rápido)
function krar(f,t,vel=.5){
  const a=ctx.createOscillator(),b=ctx.createOscillator(),lp=ctx.createBiquadFilter(),g=ctx.createGain();
  a.type='triangle';b.type='sawtooth';a.frequency.value=f;b.frequency.value=f;b.detune.value=7;
  lp.type='lowpass';lp.frequency.setValueAtTime(5200,t);lp.frequency.exponentialRampToValueAtTime(700,t+.35);
  g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(vel*.16,t+.004);g.gain.exponentialRampToValueAtTime(.0001,t+.9);
  const bz=ctx.createGain(),sh=ctx.createWaveShaper(),cur=new Float32Array(256);
  for(let i=0;i<256;i++){const x=i/127.5-1;cur[i]=Math.sign(x)*Math.min(1,Math.abs(x)*3)}
  sh.curve=cur;bz.gain.setValueAtTime(vel*.06,t);bz.gain.exponentialRampToValueAtTime(.0001,t+.25);
  a.connect(lp);b.connect(lp);lp.connect(g);b.connect(sh);sh.connect(bz);bz.connect(g);salida(g,.4);
  vive([a,b],t+1.2,t);
}
// masenqo: violín de una cuerda; entra deslizándose y vibra después de un instante
function masenqo(f,t,dur=.9,vel=.4){
  const o=ctx.createOscillator(),lfo=ctx.createOscillator(),ld=ctx.createGain(),lp=ctx.createBiquadFilter(),g=ctx.createGain();
  o.type='sawtooth';o.frequency.setValueAtTime(f*.965,t);o.frequency.setTargetAtTime(f,t,.06);
  lfo.frequency.value=5.6;ld.gain.setValueAtTime(0,t);ld.gain.linearRampToValueAtTime(f*.012,t+.25);lfo.connect(ld);ld.connect(o.frequency);
  lp.type='lowpass';lp.frequency.value=1700;lp.Q.value=4;
  g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(vel*.22,t+.08);g.gain.setTargetAtTime(0,t+dur,.12);
  o.connect(lp);lp.connect(g);salida(g,.45);vive([o,lfo],t+dur+.8,t);
}
// washint: flauta con aire; se desliza de una nota a otra
function washint(f1,f2,t,dur=.5,vel=.35){
  const o=ctx.createOscillator(),g=ctx.createGain(),n=ctx.createBufferSource(),bp=ctx.createBiquadFilter(),ng=ctx.createGain();
  o.type='sine';o.frequency.setValueAtTime(f1,t);o.frequency.exponentialRampToValueAtTime(f2,t+dur*.8);
  n.buffer=ruido;n.loop=true;bp.type='bandpass';bp.frequency.setValueAtTime(f1*2,t);bp.frequency.exponentialRampToValueAtTime(f2*2,t+dur*.8);bp.Q.value=14;ng.gain.value=vel*.5;
  g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(vel*.22,t+.06);g.gain.setTargetAtTime(0,t+dur,.08);
  o.connect(g);n.connect(bp);bp.connect(ng);ng.connect(g);salida(g,.5);vive([o,n],t+dur+.6,t);
}
// consola juguetona: el chasquido seco y el tono breve con una inflexión hacia abajo
function chasquido(t,vel=.5,brillo=2600){
  const n=ctx.createBufferSource(),hp=ctx.createBiquadFilter(),g=ctx.createGain();
  n.buffer=ruido;n.playbackRate.value=.7+Math.random()*.6;hp.type='bandpass';hp.frequency.value=brillo;hp.Q.value=1.2;
  g.gain.setValueAtTime(vel*.7,t);g.gain.exponentialRampToValueAtTime(.0001,t+.018);
  n.connect(hp);hp.connect(g);salida(g,0);vive([n],t+.05,t);
}
function tono(f,t,vel=.4){
  const o=ctx.createOscillator(),g=ctx.createGain();o.type='sine';
  o.frequency.setValueAtTime(f,t);o.frequency.exponentialRampToValueAtTime(f*.92,t+.07);
  g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(vel*.9,t+.004);g.gain.exponentialRampToValueAtTime(.0001,t+.09);
  o.connect(g);salida(g,.2);vive([o],t+.12,t);
}

// ── La voz: port del vocoder del visor. Letras → fonemas del español → formantes (el modulador,
// no se oye) → vocoder de 14 bandas cuyo portador es un acorde de la escala de la visita.
const FORMANT={a:[800,1200,2500],e:[450,1900,2550],i:[300,2200,2950],o:[500,900,2400],u:[320,750,2350],m:[280,1000,2200],n:[280,1600,2600],ñ:[280,2000,2800],l:[360,1300,2600],r:[420,1350,2500],b:[300,800,2200],d:[350,1600,2600],g:[300,1900,2400],y:[300,2100,2800]};
const NOISE={s:[6000,3,.55],f:[4000,.8,.3],x:[1800,2,.45],c:[3500,2.5,.6],p:[800,1.5,.7],t:[3500,2,.7],k:[1800,1.8,.7]};
function fonemas(text){const t=String(text).toLowerCase().normalize('NFC'),out=[];let w=0;const acc={á:'a',é:'e',í:'i',ó:'o',ú:'u',ü:'u'};
 for(let k=0;k<t.length;k++){const c=t[k],n=t[k+1]||'',n2=t[k+2]||'';
  if(/[,;:·]/.test(c)){out.push({p:'_',d:.18,w});continue;}if(/[.!?…\n/]/.test(c)){out.push({p:'_',d:.34,w,ask:c==='?'});continue;}
  if(/\s/.test(c)){if(out.length&&out.at(-1).p!=='_')out.push({p:' ',d:.04,w});w++;continue;}
  if(acc[c]){out.push({p:acc[c],v:1,stress:1,w});continue;}if('aeiou'.includes(c)){out.push({p:c,v:1,w});continue;}
  if(c==='c'&&n==='h'){out.push({p:'c',w});k++;continue;}if(c==='l'&&n==='l'){out.push({p:'y',w});k++;continue;}if(c==='r'&&n==='r'){out.push({p:'r',rr:1,w});k++;continue;}
  if(c==='q'&&n==='u'&&'eiéí'.includes(n2)){out.push({p:'k',w});k++;continue;}if(c==='g'&&n==='u'&&'eiéí'.includes(n2)){out.push({p:'g',w});k++;continue;}
  if(c==='c'){out.push({p:'eiéí'.includes(n)?'s':'k',w});continue;}if(c==='g'){out.push({p:'eiéí'.includes(n)?'x':'g',w});continue;}
  const map={j:'x',z:'s',h:null,v:'b',w:'u',k:'k',q:'k',ñ:'ñ',y:(!n||!/[a-záéíóú]/.test(n))?'i':'y'};if(c==='x'){out.push({p:'k',w},{p:'s',w});continue;}
  const p=Object.hasOwn(map,c)?map[c]:c;if(p===null)continue;if(p==='i'){out.push({p:'i',v:1,w});continue;}if(FORMANT[p]||NOISE[p])out.push({p,v:FORMANT[p]&&!NOISE[p]&&'aeiou'.includes(p)?1:0,rr:c==='r'&&(k===0||/\s/.test(t[k-1]))?1:0,w});}
 return out;}
const durOf=q=>q.p==='_'||q.p===' '?q.d:q.v?(q.stress?.17:.11):q.rr?.12:NOISE[q.p]&&'ptk'.includes(q.p)?.07:NOISE[q.p]?.09:.065;

// cada palabra canta en su grado de la escala (el mismo grado cada vez que se dice)
function pasos(texto,rate=1.15){
  const ph=fonemas(texto);if(!ph.length)return null;
  const ws=String(texto).toLowerCase().split(/\s+/),n=ESCALA.cents.length,lastW=ph.at(-1).w;
  let t=0;
  const steps=ph.map(q=>{const d=durOf(q)/rate,deg=hashStr(ws[q.w]||'')%n;
    const f=freq(deg,0)*Math.pow(2,((q.stress?2:0)-(q.w/Math.max(1,lastW))*1.2)/12);
    const s={t,d,p:q.p,v:q.v?1:0,rr:q.rr?1:0,f};t+=d;return s});
  return{steps,dur:t};
}
function speak(at,ev,env,nodos){
  const sum=ctx.createGain(),voiced=ctx.createGain(),hiss=ctx.createGain(),nf=ctx.createBiquadFilter(),ns=ctx.createBufferSource();
  sum.connect(env);voiced.connect(sum);hiss.connect(sum);voiced.gain.setValueAtTime(0,at);hiss.gain.setValueAtTime(0,at);
  ns.buffer=ruido;ns.loop=true;ns.connect(nf);nf.type='bandpass';nf.connect(hiss);nodos.push(ns);
  const bands=[1,.55,.3].map((g,k)=>{const f=ctx.createBiquadFilter(),gg=ctx.createGain();f.type='bandpass';f.Q.value=k?12:8;gg.gain.value=g*(k?2.2:1.6);f.connect(gg);gg.connect(voiced);return f});
  const o=ctx.createOscillator();o.type='sawtooth';bands.forEach(f=>o.connect(f));nodos.push(o);
  env.gain.setValueAtTime(.5,at);
  for(const s of ev.steps){const t0=at+s.t,F=FORMANT[s.p],N=NOISE[s.p];o.frequency.setTargetAtTime(s.f,t0,.02);
    if(F)bands.forEach((f,k)=>f.frequency.setTargetAtTime(F[k],t0,.012));
    const lv=s.p==='_'||s.p===' '?0:s.v?1:F&&!N?(s.p==='r'||s.p==='l'?.6:'bdg'.includes(s.p)?.45:'mnñ'.includes(s.p)?.5:.55):0;
    voiced.gain.setTargetAtTime(lv,t0,.012);if(s.rr)for(let j=1;j<4;j++)voiced.gain.setTargetAtTime(j%2?.15:.6,t0+s.d*j/4,.005);
    if(N){nf.frequency.setValueAtTime(N[0],t0);nf.Q.setValueAtTime(N[1],t0);
      if('ptk'.includes(s.p)){hiss.gain.setValueAtTime(0,t0);hiss.gain.setValueAtTime(N[2],t0+s.d*.45);hiss.gain.setTargetAtTime(0,t0+s.d*.5,.012)}
      else hiss.gain.setTargetAtTime(N[2],t0,.01)}
    else hiss.gain.setTargetAtTime(0,t0,.01)}
  voiced.gain.setTargetAtTime(0,at+ev.dur,.02);hiss.gain.setTargetAtTime(0,at+ev.dur,.02);
}
const BANDAS=Array.from({length:14},(_,k)=>170*Math.pow(6400/170,k/13));
function vocode(at,ev,vel=.8,dest=null){
  const nodos=[],mod=ctx.createGain(),carrier=ctx.createGain(),out=ctx.createGain(),env=ctx.createGain();out.gain.value=8.5;
  const lim=ctx.createDynamicsCompressor();lim.threshold.value=-22;lim.knee.value=6;lim.ratio.value=12;lim.attack.value=.002;lim.release.value=.12;
  out.connect(lim);lim.connect(env);salida(env,.3,dest);
  const mEnv=ctx.createGain();mEnv.connect(mod);speak(at,ev,mEnv,nodos);
  const rect=new Float32Array(1024);for(let k=0;k<1024;k++)rect[k]=Math.abs(k/511.5-1);
  for(const f of BANDAS){const mb=ctx.createBiquadFilter(),ws=ctx.createWaveShaper(),lp=ctx.createBiquadFilter(),cb=ctx.createBiquadFilter(),vca=ctx.createGain();
    mb.type=cb.type='bandpass';mb.frequency.value=cb.frequency.value=f;mb.Q.value=cb.Q.value=5;ws.curve=rect;lp.type='lowpass';lp.frequency.value=28;vca.gain.value=0;
    const pre=ctx.createGain(),sq=ctx.createGain();pre.gain.value=6;sq.gain.value=0;
    mod.connect(mb);mb.connect(ws);ws.connect(lp);lp.connect(pre);pre.connect(sq);pre.connect(sq.gain);sq.connect(vca.gain);carrier.connect(cb);cb.connect(vca);vca.connect(out)}
  const hp=ctx.createBiquadFilter(),sib=ctx.createGain();hp.type='highpass';hp.frequency.value=4200;sib.gain.value=.09;mod.connect(hp);hp.connect(sib);sib.connect(env);
  // portador: la voz canta sobre un acorde de la escala (tónica, quinta, octava y un sub)
  const bed=(ratio,gain,type='sawtooth')=>{const o=ctx.createOscillator(),g=ctx.createGain();o.type=type;g.gain.value=gain;o.connect(g);g.connect(carrier);nodos.push(o);
    for(const s of ev.steps)o.frequency.setTargetAtTime(s.f*ratio,at+s.t,.03)};
  bed(1,.5);bed(1.5,.35);bed(2,.25,'triangle');bed(.5,.3,'square');
  env.gain.setValueAtTime(0,at);env.gain.linearRampToValueAtTime(1.9*vel,at+.045);env.gain.setTargetAtTime(0,at+ev.dur+.15,.05);
  registraVoz(nodos);nodos.forEach(n=>{n.start(at);n.stop(at+ev.dur+.8)});
}

// ── Canto (palabra «canta»): el vocoder canta dos frases de código-poema sobre un acompañamiento
// medio Grisey (un espectro: parciales de una fundamental grave que respiran), medio Bach (arpegios de
// sinte analógico a semicorcheas, a lo Switched-On Bach, sobre cuatro acordes) y medio ochentero (pad de sierras con barrido de filtro,
// bombo y tarola con la reverb cortada). Todo sobre la escala de la visita. Va por su propio bus, que se
// calla con un fundido si el visitante escribe otra cosa.
let busCanto=null;
let reproductorCanto=null,urlCanto=null;
function callaCanto(){
  if(reproductorCanto){reproductorCanto.pause();reproductorCanto.removeAttribute('src');reproductorCanto.load();reproductorCanto.remove();reproductorCanto=null}
  if(urlCanto){URL.revokeObjectURL(urlCanto);urlCanto=null}
  if(!ctx)return;
  ultimaVoz=ctx.currentTime;
  const old=busCanto,sources=fuentesCanto;
  busCanto=null;busAcomp=null;busVoz=null;fuentesCanto=new Set();
  if(old){old.gain.cancelScheduledValues(ctx.currentTime);old.gain.setTargetAtTime(0,ctx.currentTime,.025)}
  for(const source of sources){try{source.stop(ctx.currentTime+.08)}catch{}}
  if(old)setTimeout(()=>old.disconnect(),180);
}
// los símbolos del código también se cantan
function cantable(linea){
  return String(linea)
    .replace(/==/g,' igual igual ').replace(/!=/g,' no igual ').replace(/=>/g,' flecha ').replace(/=/g,' igual ')
    .replace(/\//g,' entre ').replace(/&&/g,' y ').replace(/\|\|/g,' o ').replace(/\+\+/g,' más más ')
    .replace(/\b404\b/g,' cuatro cero cuatro ').replace(/\b0\b/g,' cero ').replace(/\b1\b/g,' uno ')
    .replace(/[{}()\[\]<>]/g,' ').replace(/;/g,'. ').replace(/:/g,', ').replace(/\./g,' punto ').replace(/\s+/g,' ').trim();
}
function clave(f,t,vel,dest){   // sinte analógico a lo Switched-On Bach: sierra + cuadrada una octava abajo, filtro resonante que se cierra
  const a=ctx.createOscillator(),b=ctx.createOscillator(),lp=ctx.createBiquadFilter(),g=ctx.createGain();
  a.type='sawtooth';b.type='square';a.frequency.value=f;b.frequency.value=f/2;b.detune.value=4;
  lp.type='lowpass';lp.Q.value=9;lp.frequency.setValueAtTime(Math.min(6000,f*9),t);lp.frequency.exponentialRampToValueAtTime(Math.max(180,f*1.2),t+.22);
  g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(vel*.06,t+.004);g.gain.exponentialRampToValueAtTime(.0001,t+.32);
  a.connect(lp);b.connect(lp);lp.connect(g);salida(g,.22,dest);vive([a,b],t+.4,t);
}
function pad80(f,t,dur,vel,dest){   // dos sierras desafinadas, filtro que se abre y se cierra
  const o=[0,1].map(i=>{const x=ctx.createOscillator();x.type='sawtooth';x.frequency.value=f;x.detune.value=i?11:-11;return x});
  const lp=ctx.createBiquadFilter(),g=ctx.createGain();lp.type='lowpass';lp.Q.value=6;
  lp.frequency.setValueAtTime(300,t);lp.frequency.linearRampToValueAtTime(2400,t+dur*.5);lp.frequency.linearRampToValueAtTime(500,t+dur);
  g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(vel*.05,t+.3);g.gain.setTargetAtTime(0,t+dur-.2,.15);
  o.forEach(x=>x.connect(lp));lp.connect(g);salida(g,.45,dest);vive(o,t+dur+.6,t);
}
function parcial(f,t,dur,vel,dest){   // un parcial del espectro: seno que entra y sale despacio
  const o=ctx.createOscillator(),g=ctx.createGain();o.type='sine';o.frequency.value=f;
  g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(vel,t+dur*.45);g.gain.linearRampToValueAtTime(0,t+dur);
  o.connect(g);salida(g,.5,dest);vive([o],t+dur+.1,t);
}
function bombo(t,dest){const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.setValueAtTime(120,t);o.frequency.exponentialRampToValueAtTime(42,t+.12);
  g.gain.setValueAtTime(.32,t);g.gain.exponentialRampToValueAtTime(.0001,t+.28);o.connect(g);salida(g,0,dest);vive([o],t+.3,t)}
function tarola(t,dest){   // reverb cortada: el ruido entra a la reverb, pero la compuerta lo corta en seco
  const n=ctx.createBufferSource(),bp=ctx.createBiquadFilter(),g=ctx.createGain();n.buffer=ruido;bp.type='bandpass';bp.frequency.value=1800;bp.Q.value=.7;
  g.gain.setValueAtTime(.2,t);g.gain.setValueAtTime(.2,t+.16);g.gain.linearRampToValueAtTime(0,t+.19);
  n.connect(bp);bp.connect(g);salida(g,.9,dest);vive([n],t+.25,t);
}
let busAcomp=null,busVoz=null;
function bajo80(f,t,dur,vel,dest){   // bajo de sinte: cuadrada + seno una octava abajo, filtro que muerde
  const a=ctx.createOscillator(),b=ctx.createOscillator(),lp=ctx.createBiquadFilter(),g=ctx.createGain();
  a.type='square';b.type='sine';a.frequency.value=f;b.frequency.value=f/2;
  lp.type='lowpass';lp.Q.value=5;lp.frequency.setValueAtTime(1400,t);lp.frequency.exponentialRampToValueAtTime(260,t+Math.min(.25,dur));
  g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(vel*.11,t+.006);g.gain.setTargetAtTime(0,t+dur*.85,.04);
  a.connect(lp);b.connect(lp);lp.connect(g);salida(g,.08,dest);vive([a,b],t+dur+.2,t);
}
function hihat(t,vel,dest){const n=ctx.createBufferSource(),hp=ctx.createBiquadFilter(),g=ctx.createGain();n.buffer=ruido;n.playbackRate.value=1.6;
  hp.type='highpass';hp.frequency.value=7500;g.gain.setValueAtTime(vel*.09,t);g.gain.exponentialRampToValueAtTime(.0001,t+.045);
  n.connect(hp);hp.connect(g);salida(g,.05,dest);vive([n],t+.06,t)}
// La voz canta a tempo: cada palabra empieza en una corchea y dura un número entero de corcheas; su nota
// sale de los tonos del acorde de ese compás, moviéndose por paso corto, en arco; la última palabra
// cadencia en la tónica del acorde y se alarga hasta el siguiente tiempo fuerte.
function melodia(texto,inicio,compas,acordeDe,tri,n){
  const ph=fonemas(texto);if(!ph.length)return null;
  const corchea=compas/8,palabras=[];
  for(const q of ph){if(!palabras[q.w])palabras[q.w]=[];palabras[q.w].push(q)}
  const ws=palabras.filter(Boolean),ultima=ws.length-1;
  let t=0,prev=null;const steps=[];
  ws.forEach((fon,wi)=>{
    const natural=fon.reduce((a,q)=>a+durOf(q),0)||corchea;
    let k=Math.max(1,Math.round(natural/corchea));
    if(wi===ultima){const hasta=Math.ceil((t+k*corchea)/(corchea*4))*corchea*4;k=Math.max(k+2,Math.round((hasta-t)/corchea))}
    const raiz=acordeDe(inicio+t),tonos=[...tri,tri[0]+n,tri[1]+n].map(x=>raiz+x);
    // en la primera mitad la melodía tiende a subir, en la segunda a bajar; nunca salta más de lo necesario
    const tendencia=wi<ws.length/2?1:-1;
    let nota;
    if(wi===ultima)nota=raiz+(prev!=null&&prev>raiz+n/2?n:0);
    else if(prev==null)nota=raiz+tri[1];
    else nota=tonos.reduce((m,x)=>{const c=Math.abs(x-prev)-(Math.sign(x-prev)===tendencia?.6:0)+(x===prev?1.6:0);return c<m.c?{x,c}:m},{x:tonos[0],c:1e9}).x;
    prev=nota;
    const escala=k*corchea/natural,f=freq(nota,0);
    for(const q of fon){const d=durOf(q)*escala;steps.push({t,d,p:q.p,v:q.v?1:0,rr:q.rr?1:0,f,w:wi});t+=d}
  });
  return{steps,dur:t};
}
function canta(lineas,{soloVoz=false,soloAcomp=false}={}){   // soloVoz / soloAcomp: para medir cada parte
  if(!puede())return 0;
  if(!grabando)callaCanto();
  capturandoCanto=true;
  try{
  if(!busCanto){
    busCanto=ctx.createGain();busCanto.connect(master);busAcomp=ctx.createGain();busVoz=ctx.createGain();
    // Reparto de energía 70/30, conservando el volumen total en ambos canales.
    const pan=1-4*Math.acos(Math.sqrt(.7))/Math.PI;
    for(const [bus,pos] of [[busAcomp,-pan],[busVoz,pan]]){const p=ctx.createStereoPanner();p.pan.value=pos;bus.connect(p);p.connect(busCanto)}
    // cada canal con su reverb (mismo espacio que la general), conectada después de su volumen
    for(const bus of[busCanto,busAcomp,busVoz]){const v=ctx.createConvolver();v.buffer=verb.buffer;const vg=ctx.createGain();vg.gain.value=.28;v.connect(vg);vg.connect(bus);bus._verb=v}
  }
  busCanto.gain.cancelScheduledValues(ctx.currentTime);busCanto.gain.setValueAtTime(1,ctx.currentTime);
  busAcomp.gain.cancelScheduledValues(ctx.currentTime);busAcomp.gain.setValueAtTime(soloVoz?0:.7,ctx.currentTime);
  const n=ESCALA.cents.length,tri=n>=7?[0,2,4]:[0,2,3];   // la tríada en pasos de la escala (en la pentatónica: 0,2,3)
  const pulso=60/92,compas=pulso*4,t0=ctx.currentTime+.1;
  // una progresión de ocho compases que va a algún lado y vuelve a casa (en grados de la escala)
  const PROGRESIONES=[[0,3,1,4,0,3,4,0],[0,2,3,4,0,1,4,0],[0,4,3,1,0,3,4,0],[0,1,3,4,2,3,4,0]];
  // misma semilla y misma letra, misma progresión
  const prog=PROGRESIONES[hashStr('canto:'+semillaVisita+':'+lineas.join('|'))%PROGRESIONES.length].map(g=>g%n);
  // la voz: cada frase empieza en un compás; entre frases, un compás de respiro
  const evs=[];let barra=1;
  for(const l of lineas){
    const inicio=barra*compas;
    const ev=melodia(cantable(l),inicio,compas,tt=>prog[Math.floor(tt/compas)%prog.length],tri,n);
    if(!ev)continue;evs.push({ev,at:t0+inicio});barra+=Math.ceil((ev.dur+.01)/compas)+1;
  }
  const compases=Math.max(barra+1,4),fin=compases*compas;
  ultimaVoz=t0+fin;
  for(const {ev,at} of evs){
    if(!soloAcomp)vocode(at,ev,1,busVoz);
    if(!soloVoz){busAcomp.gain.setTargetAtTime(.34,at-.12,.025);busAcomp.gain.setTargetAtTime(.7,at+ev.dur+.05,.25)}
  }
  // acordes por compás; el último se sostiene (fermata) y ahí no hay batería
  const acordeDe=c=>c>=compases-2?0:prog[c%prog.length];
  const patrones=[[0,1,2,3,2,1,0,1],[0,2,1,2,3,2,1,2]];   // índices en la tríada + octava (3)
  for(let c=0;c<compases;c++){
    const r=acordeDe(c),tc=t0+c*compas,final=c>=compases-2,tono=x=>r+(x===3?tri[0]+n:tri[x]);
    // pads: la tríada completa, con filtro que respira
    if(!final||c===compases-2){const largo=final?compas*2:compas;tri.forEach((x,i)=>pad80(freq(r+x,0),tc,largo,[.9,.6,.5][i],busAcomp))}
    // arpegio a semicorcheas (Switched-On Bach); se calla en la fermata
    if(!final){const pat=patrones[c%2];for(let i=0;i<16;i++)clave(freq(tono(pat[i%8]),1+(i>=8&&c%4===3?1:0)),tc+i*pulso/4,(i%4?.55:.85)*(c===0?.8:1),busAcomp)}
    else if(c===compases-2)tri.forEach((x,i)=>clave(freq(r+x,1),tc+i*.09,.7,busAcomp));   // el último acorde, arpegiado una vez
    // bajo: raíz, raíz, quinta, paso hacia el siguiente acorde (corcheas con acentos)
    const sig=acordeDe(c+1),bajoNotas=[r,r,r+tri[2],sig];
    if(c>0&&!final)bajoNotas.forEach((b,i)=>bajo80(freq(b,-1),tc+i*pulso,pulso*.9,i===0?1:.75,busAcomp));
    if(final&&c===compases-2)bajo80(freq(0,-1),tc,compas*2,1,busAcomp);
    // batería: entra con la voz (desde el segundo compás) y se va en la fermata
    if(c>0&&!final){bombo(tc,busAcomp);bombo(tc+pulso*1.5,busAcomp);bombo(tc+pulso*2,busAcomp);tarola(tc+pulso,busAcomp);tarola(tc+pulso*3,busAcomp);
      for(let h=0;h<8;h++)hihat(tc+h*pulso/2,h%2?.6:1,busAcomp)}
  }
  // Grisey: el espectro de la fundamental del acorde, que cambia cada dos compases y se abre en la fermata
  for(let c=0;c<compases;c+=2){
    const r=acordeDe(c),f0=freq(r,-2),tc=t0+c*compas,largo=Math.min(compases-c,c>=compases-2?2:2)*compas+(c>=compases-2?compas:0);
    const parciales=c>=compases-2?14:8;
    for(let k=1;k<=parciales;k++)parcial(f0*k*(1+.0015*k*k/13),tc+(k-1)*.18,largo,(c>=compases-2?.05:.03)/Math.sqrt(k),busAcomp);
  }
  recientes.push(performance.now());
  return t0+fin-ctx.currentTime;
  }finally{capturandoCanto=false}
}

// ── Lo que el front le pide al sonido
let ultimaVoz=0,ultimaChispa=0;
const S={
  get activo(){return activo},
  get cedido(){return cedido},
  descripcion:()=>`${ESCALA.nombre} · ${ESCALA.op}`,
  get suena(){return puede()},
  // escribir una qenet: la escala de la visita se vuelve esa (computada con la semilla) y suena
  qenet(nombre){
    if(!QENET[nombre])return null;
    ESCALA=computa(mulberry32(hashStr('qenet:'+nombre+':'+semillaVisita)),nombre);
    S.tocaEscala();return S.descripcion();
  },
  // la escala sube y baja en el krar, sobre un masenqo grave
  tocaEscala(){
    if(!puede())return 0;
    const n=ESCALA.cents.length,t=ctx.currentTime+.05,paso=.14,grados=[...Array(n+1).keys(),...[...Array(n).keys()].reverse()];
    grados.forEach((d,i)=>krar(freq(d,1),t+i*paso,.45));masenqo(freq(0,0),t,grados.length*paso+.3,.3);
    recientes.push(performance.now());return grados.length*paso+.6;
  },
  // the machine plays the blues: un bajo de masenqo por compás (grados 0, 3, 4 de la escala, a la manera
  // de los doce compases) y una melodía de krar que camina por la escala con swing. Devuelve su duración.
  blues(segundos=9){
    if(!puede())return 0;
    const t0=ctx.currentTime+.08,pulso=.36,compas=pulso*4,n=ESCALA.cents.length;
    const forma=[0,0,0,0,3,3,0,0,4,3,0,4];let g=Math.floor(Math.random()*n);
    for(let c=0;c*compas<segundos;c++){
      const raiz=forma[c%forma.length],tc=t0+c*compas;
      masenqo(freq(raiz,0),tc,compas*.92,.12);
      for(let b=0;b<8;b++){
        if(Math.random()<.32)continue;
        const tb=tc+Math.floor(b/2)*pulso+(b%2?pulso*.66:0);   // swing: la segunda corchea llega tarde
        g=Math.max(0,Math.min(n*2,g+[-2,-1,-1,1,1,2,0][Math.floor(Math.random()*7)]));
        krar(freq(raiz+g,1),tb,b%2?.11:.17);
      }
      if(c%2)chasquido(tc+pulso*2,.3,1600);
    }
    recientes.push(performance.now());return segundos;
  },
  etiqueta:tr=>activo?(cedido?tr('reanudar sonido','resume sound'):tr('silenciar','mute')):tr('activar sonido','sound on'),
  async alternar(){
    if(activo&&cedido){cedido=false;await ctx.resume();sube();
      if(ecoPendiente&&performance.now()<ecoPendiente.hasta)ecoPendiente.toca();ecoPendiente=null;return}
    activo=!activo;try{sessionStorage.setItem(CLAVE,activo?'si':'no')}catch{}
    if(activo){arranca();await ctx.resume();sube();const t=ctx.currentTime+.05;[0,2,4].forEach((d,i)=>krar(freq(d,1),t+i*.09,.5))}
    else baja();
  },
  // opción elegida: un año suena como escala; lo demás lo dice la voz
  opcion(label){
    if(!puede())return;
    const m=/^(\d{4})\s*·\s*(\d+)/.exec(label);
    if(m)return S.escala(+m[1],+m[2]);
    S.decir(label.replace(/^[›>]\s*/,''));
  },
  canta,
  enlazaCanto(audio,blob){callaCanto();reproductorCanto=audio;urlCanto=URL.createObjectURL(blob);audio.src=urlCanto;audio.muted=activo&&cedido;return urlCanto},
  // la misma canción (misma semilla, misma letra) renderizada fuera de tiempo real → WAV de 16 bits
  async grabaCancion(lineas,opciones={}){
    const sr=32000,g={ctx,master,verb,ruido,busCanto,busAcomp,busVoz,ultimaVoz};   // 32 kHz: alcanza para este sonido y rinde más rápido
    // dos pasadas: la primera sólo mide cuánto dura (en un contexto mínimo); la segunda reserva justo eso y la toca
    const tocaEn=off=>{try{ctx=off;({master,verb,ruido}=montaSalida(off));master.gain.value=.42;busCanto=null;busAcomp=null;busVoz=null;ultimaVoz=0;grabando=true;return canta(lineas,opciones)}
      finally{grabando=false;({ctx,master,verb,ruido,busCanto,busAcomp,busVoz,ultimaVoz}=g)}};
    const largo=tocaEn(new OfflineAudioContext(2,sr,sr))+2.5;
    const off=new OfflineAudioContext(2,Math.ceil(sr*largo),sr),fin=tocaEn(off);
    const buf=await off.startRendering(),n=Math.min(buf.length,Math.ceil((fin+2.5)*sr));
    const datos=new DataView(new ArrayBuffer(44+n*4)),texto=(o,t)=>[...t].forEach((c,i)=>datos.setUint8(o+i,c.charCodeAt(0)));
    texto(0,'RIFF');datos.setUint32(4,36+n*4,true);texto(8,'WAVE');texto(12,'fmt ');datos.setUint32(16,16,true);datos.setUint16(20,1,true);datos.setUint16(22,2,true);
    datos.setUint32(24,sr,true);datos.setUint32(28,sr*4,true);datos.setUint16(32,4,true);datos.setUint16(34,16,true);texto(36,'data');datos.setUint32(40,n*4,true);
    const L=buf.getChannelData(0),R=buf.getChannelData(1);
    for(let i=0;i<n;i++){datos.setInt16(44+i*4,Math.max(-1,Math.min(1,L[i]))*32767,true);datos.setInt16(46+i*4,Math.max(-1,Math.min(1,R[i]))*32767,true)}
    return new Blob([datos],{type:'audio/wav'});
  },
  // la partitura de una frase (para revisar la melodía sin oírla): palabra, grado, corchea de inicio, corcheas
  partitura(texto){
    const n=ESCALA.cents.length,tri=n>=7?[0,2,4]:[0,2,3],compas=60/92*4,corchea=compas/8,prog=[0,3,1,4,0,3,4,0];
    const ev=melodia(cantable(texto),compas,compas,tt=>prog[Math.floor(tt/compas)%8],tri,n);if(!ev)return[];
    const palabras=cantable(texto).split(/\s+/),out=[];
    for(const st of ev.steps){if(out[st.w])continue;out[st.w]={palabra:palabras[st.w]||'',nota:+(1200*Math.log2(st.f/freq(0,0))).toFixed(0)+'¢',corchea:+(st.t/corchea).toFixed(2)}}
    return{escala:S.descripcion(),notas:out.filter(Boolean),corcheas:+(ev.dur/corchea).toFixed(1)};
  },
  // escribir otra cosa desvanece la canción y detiene sus fuentes programadas
  callaCanto,
  decir(texto){
    if(!puede())return;
    const ev=pasos(texto);if(!ev)return;
    const at=Math.max(ctx.currentTime+.03,ultimaVoz);ultimaVoz=at+ev.dur+.1;   // una frase no pisa a otra
    vocode(at,ev);recientes.push(performance.now());
  },
  // cada año tiene su escala: la qenet y su operación salen del año, así que 2021 siempre suena a 2021;
  // tantas notas como piezas
  escala(año,cuantas){
    if(!puede())return;
    const esc=computa(mulberry32(hashStr('año:'+año)),NOMBRES[año%NOMBRES.length]);
    const n=Math.max(3,Math.min(13,cuantas)),t=ctx.currentTime+.04,paso=Math.max(.06,.5/n);
    for(let i=0;i<n;i++)krar(freq(i,1,esc),t+i*paso+(Math.random()-.5)*.012,(.5+.35*(i===n-1))*Math.min(1,6/n));
    masenqo(freq(0,0,esc),t,n*paso+.4,.35);recientes.push(performance.now());
  },
  tramo(){const v=decorativo(.5);if(v)chasquido(ctx.currentTime+.01,v)},
  chispa(){const now=performance.now();if(now-ultimaChispa<180)return;const v=decorativo(.4);if(!v)return;ultimaChispa=now;
    krar(freq(Math.floor(Math.random()*8),1),ctx.currentTime+.01,.35*v)},
  corrige(){const v=decorativo(.6);if(!v)return;const t=ctx.currentTime+.01;
    [0,1,2].forEach(i=>tono(freq(i*2,2),t+i*.045,.5*v));chasquido(t+.16,.6*v,1800)},
  pieza(i){const v=decorativo(.8);if(v)krar(freq(i%10,1),ctx.currentTime+.01,.4*v)},
  fila(r){if(r%4)return;const v=decorativo(.9);if(v)chasquido(ctx.currentTime+.005,.35*v,3400)},
  trazo(k){const v=decorativo(1);if(v)washint(freq(k,1),freq(k+1,1),ctx.currentTime+.02,.45,.5*v)},
  nodo(j,titulo){if(!puede())return;masenqo(freq(j,0),ctx.currentTime+.02,.9,.4);if(titulo)S.decir(titulo)},
  // abrir una obra: el sonido del front se aparta y espera a que lo reanuden
  cede(){if(!puede())return;cedido=true;baja()},

  // ── Rarezas (easter-eggs.js). No pasan por la fatiga: son raras de por sí, y si hay sonido suenan.
  // Nunca reactivan un sonido silenciado o cedido: el contagio llega justo al volver de una obra, cuando
  // el sonido está cedido; su eco queda esperando y suena si reanudan mientras la huella sigue viva.
  visitante(kind,familia,obra){
    const toca=()=>{const t=ctx.currentTime+.03;
      if(kind==='contagio'){const año=parseInt(obra?.year,10);
        const esc=computa(mulberry32(hashStr('año:'+(año||obra?.url||''))),NOMBRES[(año||hashStr(obra?.url||''))%NOMBRES.length]);
        gesto(familia,t+.25,esc,.55);[0,2,4,7].forEach((d,i)=>krar(freq(d,0,esc),t+i*.16,.28))}
      else gesto(familia,t,ESCALA,.8)};
    if(puede())return toca();
    if(kind==='contagio'&&activo&&cedido)ecoPendiente={toca,hasta:performance.now()+11000};
  },
  // al tocar o enfocar un visitante, la voz dice de dónde vino
  nombra(titulo){S.decir(titulo)},
  // error fértil: el glifo se escapa, cae y, al tocar el fondo, siembra
  cae(ms=780){if(!puede())return;const t=ctx.currentTime+.01;
    chasquido(t,.8,4200);
    const o=ctx.createOscillator(),g=ctx.createGain();o.type='triangle';
    o.frequency.setValueAtTime(freq(4,2),t);o.frequency.exponentialRampToValueAtTime(freq(0,0),t+ms/1000);
    g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(.12,t+.02);g.gain.setTargetAtTime(0,t+ms/1000-.05,.03);
    o.connect(g);salida(g,.3);vive([o],t+ms/1000+.3,t)},
  siembra(){if(!puede())return;const t=ctx.currentTime+.01;
    krar(freq(0,0),t,.9);chasquido(t,.9,900);[2,4,1].forEach((d,i)=>krar(freq(d,1),t+.09+i*.07,.3))},
  // la pelota extraviada: cada golpe contra el suelo, más bajo y más tenue que el anterior
  rebote(k,n){if(!puede())return;const t=ctx.currentTime+.005,v=1-k/(n+1);
    krar(freq(n-k+2,1),t,.6*v);chasquido(t,.5*v,1200)},
  // el eco: la voz dice la palabra y se repite, cada vez más lejos
  eco(palabra){if(!puede())return;const ev=pasos(palabra);if(!ev)return;
    const at=Math.max(ctx.currentTime+.03,ultimaVoz);[1,.45,.2].forEach((v,i)=>vocode(at+i*.3,ev,.8*v));ultimaVoz=at+.6+ev.dur},
  // se le escapa un dibujo: un tono que se encoge (sube y se apaga), como la figurita volviéndose punto
  dibujo(){if(!puede())return;const t=ctx.currentTime+.01;
    [0,2,4,6].forEach((d,i)=>tono(freq(d,2),t+.52+i*.17,.7-i*.12));krar(freq(1,1),t,.4)},
  // la consola se desvía y borra: la cinta rebobina (chasquidos cada vez más juntos y agudos)
  rebobina(ms=400){if(!puede())return;const t=ctx.currentTime+.01,n=9;
    for(let i=0;i<n;i++){const p=i/(n-1);chasquido(t+ms/1000*(1-Math.pow(1-p,1.8)),.55,1500+p*4200)}},
};
let ecoPendiente=null;

// Un gesto por familia de visitante: cada dibujo del archivo tiene su manera de sonar.
function gesto(familia,t,esc,v){
  const f=(d,o=1)=>freq(d,o,esc);
  switch(familia){
    case 'nube':      // aire que sube y baja por la flauta
      washint(f(0),f(3),t,.7,.5*v);washint(f(3),f(1),t+.62,.8,.4*v);break;
    case 'glifos':    // un puñado de teclas y tonos, como glifos que caen en su lugar
      for(let i=0;i<7;i++){const dt=t+i*.055+Math.random()*.03;chasquido(dt,.5*v,2000+Math.random()*3000);if(i%2)tono(f(Math.floor(Math.random()*6),2),dt,.5*v)}break;
    case 'pelota':    // rebota: cada golpe más cerca del anterior y más bajo
      {let dt=0,gap=.34;for(let i=0;i<7;i++){krar(f(6-i),t+dt,.55*v*(1-i*.1));chasquido(t+dt,.35*v,1400);dt+=gap;gap*=.72}}break;
    case 'montaña':   // masenqo grave con su quinta
      masenqo(f(0,0),t,1.6,.45*v);masenqo(f(2,0),t+.35,1.2,.3*v);break;
    case 'planta':    // crece: arpegio lento que sube y se ramifica
      [0,1,2,4,3,5,7].forEach((d,i)=>krar(f(d),t+i*.14+(i>3?.07:0),.4*v));break;
    case 'estrella':  // destellos agudos, dispersos
      for(let i=0;i<6;i++)tono(f(Math.floor(Math.random()*8),2),t+Math.random()*.9,.6*v);break;
    case 'linea':     // una línea larga que atraviesa la escala sin cortarse
      washint(f(0,0),f(9,0),t,2.2,.45*v);break;
    default:          // trama: dos notas que se alternan como un dither
      for(let i=0;i<10;i++)krar(f(i%2?4:2),t+i*.07,.2*v);
  }
}

// si ya estaba activo en esta sesión, arranca con el primer gesto (el navegador no deja antes)
if(activo){const uno=()=>{arranca();ctx.resume().then(()=>{if(!cedido)sube()});removeEventListener('pointerdown',uno);removeEventListener('keydown',uno)};
  addEventListener('pointerdown',uno);addEventListener('keydown',uno)}
let cantoOculto=false;
document.addEventListener('visibilitychange',()=>{
  if(document.hidden){cantoOculto=!!reproductorCanto&&!reproductorCanto.paused;reproductorCanto?.pause();ctx?.suspend()}
  else{if(activo)ctx?.resume();if(cantoOculto&&reproductorCanto&&!reproductorCanto.muted)reproductorCanto.play().catch(()=>{});cantoOculto=false}
});
// cualquier enlace que sale del front (obras, videos) cede el sonido
document.addEventListener('click',e=>{const a=e.target.closest?.('a[href]');if(a&&/^https?:/.test(a.getAttribute('href')))S.cede()},true);

window.CanekSonido=S;
})();
