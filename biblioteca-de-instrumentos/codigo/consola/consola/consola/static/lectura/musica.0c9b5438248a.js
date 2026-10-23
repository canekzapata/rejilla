/* Música como código. Cada evento sale de la semilla de la pieza, la llave del bloque, su texto
   y el tiempo: misma semilla, misma música. Web Audio puro; ni Math.random ni muestras externas:
   el ruido y la reverberación también se generan con semilla. La IA puede componerla (son datos
   con rangos, como los materiales); al reproducir nunca se le pregunta nada. */
'use strict';
window.LecturaMusica=(()=>{
const NOTES=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'];
const SCALES={pentatonic:[0,2,4,7,9],minor_pentatonic:[0,3,5,7,10],major:[0,2,4,5,7,9,11],minor:[0,2,3,5,7,8,10],dorian:[0,2,3,5,7,9,10],phrygian:[0,1,3,5,7,8,10],lydian:[0,2,4,6,7,9,11],hirajoshi:[0,2,3,7,8],in:[0,1,5,7,8],yo:[0,2,5,7,9],whole:[0,2,4,6,8,10]};
const scaleLabels={pentatonic:'Pentatónica mayor',minor_pentatonic:'Pentatónica menor',major:'Mayor',minor:'Menor',dorian:'Dórica',phrygian:'Frigia',lydian:'Lidia',hirajoshi:'Hirajōshi',in:'In (miyako-bushi)',yo:'Yo',whole:'Tonos enteros'};
const INSTR={none:'Silencio',pluck:'Cuerda pulsada',kalimba:'Kalimba',bell:'Campana FM',glass:'Vidrio',pad:'Colchón',bass:'Bajo',drone:'Zumbido',xilofono:'Xilófono',xiloelec:'Xilófono eléctrico',marimba:'Marimba',balafon:'Balafón',gyil:'Gyil (con zumbido)',kalimbacaja:'Kalimba de caja',mbira:'Mbira (con chapitas)',vibrafono:'Vibráfono',saron:'Saron (gamelán)',gender:'Gendér (gamelán)',teponaztli:'Teponaztli (dos lenguas)',steelpan:'Steel pan',arpaboca:'Arpa de boca (birimbao)',berimbau:'Berimbau'};
/* Mismo formato que los materiales: [etiqueta, tipo, valor inicial, mínimo|opciones, máximo, paso]. */
const schema={on:['Música generativa','check',false],root:['Tónica','select','D',Object.fromEntries(NOTES.map(n=>[n,n]))],scale:['Escala','select','pentatonic',scaleLabels],gain:['Volumen general','range',.7,0,1,.05],reverb:['Reverberación','range',.35,0,1,.05],delay:['Eco','range',.2,0,.9,.05],delayTime:['Tiempo del eco (s)','range',.36,.05,1,.01],pulse:['Pulso sonoro (necesita ♩ > 0)','select','none',{none:'sin pulso sonoro',tick:'clic',drum:'bombo',shaker:'maraca'}],pattern:['Patrón: x fuerte, o suave, . silencio (4 pasos por pulso)','text','x...o...x...o...',64],density:['Densidad: más versos en escena, más música (0 = apagada)','range',0,0,1,.05]};
/* La voz que lee (vocoder propio): síntesis por formantes. El español se lee casi como se escribe: de las letras salen
   vocales (tres resonancias sobre una onda), consonantes de ruido (s, f, j, ch), golpes (p, t, k) y resonancias apagadas
   (m, n, l, r). Todo es código sembrado: suena igual en cualquier máquina y se renderiza como el resto de la música. */
Object.assign(schema,{vozOctave:['Voz que lee: octava','range',3,1,5,1],vozRate:['Voz que lee: velocidad','range',1,.5,2,.05],
 vozCarrier:['Voz que lee: timbre','select','sierra',{sierra:'vocoder de sierra',pulso:'vocoder de pulso',coro:'coro de tres voces',susurro:'susurro (solo ruido)',instrumento:'el instrumento de la voz habla',acorde:'colchón que habla',musica:'la música entera habla'}],
 vozMelody:['Voz que lee: entonación','select','palabras',{monotono:'monótona (robot)',palabras:'cada palabra en su nota',habla:'como se habla (sube y baja)'}],
 vozGain:['Voz que lee: volumen','range',.8,0,1,.05],vozLang:['Idioma de la voz que lee (la clara y el vocoder)','select','es-MX',{'es-MX':'español (México)','es-ES':'español (España)','en-US':'inglés','pt-BR':'portugués','fr-FR':'francés'}]});
const FORMANT={ae:[660,1720,2410],ah:[620,1220,2550],ih:[400,1920,2560],eh:[550,1770,2490],uh:[450,1030,2380],aw:[590,880,2540],er:[470,1380,1660],ax:[500,1450,2450],'ɹ':[350,1060,1600],w:[300,650,2200],v:[300,1150,2350],dh:[350,1500,2550],a:[800,1200,2500],e:[450,1900,2550],i:[300,2200,2950],o:[500,900,2400],u:[320,750,2350],m:[280,1000,2200],n:[280,1600,2600],ñ:[280,2000,2800],l:[360,1300,2600],r:[420,1350,2500],b:[300,800,2200],d:[350,1600,2600],g:[300,1900,2400],y:[300,2100,2800]};
const NOISE={h:[1500,.6,.22],sh:[2800,1.4,.6],th:[6000,.7,.22],s:[6000,3,.55],f:[4000,.8,.3],x:[1800,2,.45],c:[3500,2.5,.6],p:[800,1.5,.7],t:[3500,2,.7],k:[1800,1.8,.7]};
/* Letras → sonidos del español (ch→c, ll/y→y, qu/c/k→k, c/z ante e,i→s, g ante e,i y j→x, h muda, v→b, x→ks). */
function fonemas(text){const t=String(text).toLowerCase().normalize('NFC'),out=[];let w=0;const acc={á:'a',é:'e',í:'i',ó:'o',ú:'u',ü:'u'};
 for(let k=0;k<t.length;k++){const c=t[k],n=t[k+1]||'',n2=t[k+2]||'';
  if(/[,;:]/.test(c)){out.push({p:'_',d:.18,w});continue;}if(/[.!?…\n/]/.test(c)){out.push({p:'_',d:.34,w,ask:c==='?'});continue;}
  if(/\s/.test(c)){if(out.length&&out.at(-1).p!=='_')out.push({p:' ',d:.04,w});w++;continue;}
  if(acc[c]){out.push({p:acc[c],v:1,stress:1,w});continue;}if('aeiou'.includes(c)){out.push({p:c,v:1,w});continue;}
  if(c==='c'&&n==='h'){out.push({p:'c',w});k++;continue;}if(c==='l'&&n==='l'){out.push({p:'y',w});k++;continue;}if(c==='r'&&n==='r'){out.push({p:'r',rr:1,w});k++;continue;}
  if(c==='q'&&n==='u'&&'eiéí'.includes(n2)){out.push({p:'k',w});k++;continue;}if(c==='g'&&n==='u'&&'eiéí'.includes(n2)){out.push({p:'g',w});k++;continue;}
  if(c==='c'){out.push({p:'eiéí'.includes(n)?'s':'k',w});continue;}if(c==='g'){out.push({p:'eiéí'.includes(n)?'x':'g',w});continue;}
  const map={j:'x',z:'s',h:null,v:'b',w:'u',k:'k',q:'k',ñ:'ñ',y:(!n||!/[a-záéíóú]/.test(n))?'i':'y'};if(c==='x'){out.push({p:'k',w},{p:'s',w});continue;}
  const p=Object.hasOwn(map,c)?map[c]:c;if(p===null)continue;if(p==='i'){out.push({p:'i',v:1,w});continue;}if(FORMANT[p]||NOISE[p])out.push({p,v:FORMANT[p]&&!NOISE[p]&&'aeiou'.includes(p)?1:0,rr:c==='r'&&(k===0||/\s/.test(t[k-1]))?1:0,w});}
 return out;}
/* Melodía escrita (clip.sing): una nota por sílaba. «1 3 5:2 _ 8» son grados de la escala (1 = tónica; ' sube una octava, , la baja),
   «re fa# la» es solfeo y «D4 F#4» son notas con octava (sin número, la octava de la voz). «:2» dura dos tiempos del ♩ y «_» es un silencio.
   Sin «:» la nota cambia pero el ritmo es el del habla; con algún «:», el ritmo lo manda la melodía (un tiempo por nota si no dice).
   Si hay más sílabas que notas, la melodía vuelve a empezar. */
const SOLFEO={do:0,re:2,mi:4,fa:5,sol:7,la:9,si:11},LETTER={c:0,d:2,e:4,f:5,g:7,a:9,b:11};
function melodia(text){if(text==null||text==='')return null;if(typeof text!=='string'||text.length>400)throw Error('Melodía inválida (hasta 400 caracteres)');
 const toks=text.trim().split(/[\s|]+/).filter(Boolean);if(!toks.length)return null;if(toks.length>128)throw Error('Melodía demasiado larga (hasta 128 notas)');let rhythm=false;
 const out=toks.map(tok=>{const [p,b,...extra]=tok.split(':');if(extra.length)throw Error('Nota inválida: '+tok);let beats=null;if(b!==undefined){beats=Number(b);rhythm=true;if(!(beats>0&&beats<=16))throw Error('Duración inválida: '+tok);}
  if(p==='_')return {rest:true,beats};let m;const acc=s=>s==='#'?1:s==='b'?-1:0;
  if((m=/^([1-9]|1[0-5])([',]*)$/.exec(p)))return {deg:Number(m[1])-1,oct:(m[2].match(/'/g)||[]).length-(m[2].match(/,/g)||[]).length,beats};
  if((m=/^(do|re|mi|fa|sol|la|si)([#b]?)([0-7])?$/i.exec(p)))return {pc:SOLFEO[m[1].toLowerCase()]+acc(m[2]),octave:m[3]===undefined?null:Number(m[3]),beats};
  if((m=/^([a-g])([#b]?)([0-7])?$/i.exec(p)))return {pc:LETTER[m[1].toLowerCase()]+acc(m[2]),octave:m[3]===undefined?null:Number(m[3]),beats};
  throw Error('Nota inválida: «'+tok+'» (usa grados 1–15, do re mi…, C D E… con # o b y octava, «_» para silencio, «:2» para la duración)');});
 if(!out.some(n=>!n.rest))throw Error('La melodía necesita al menos una nota');return {rhythm,notes:out.map(n=>rhythm&&n.beats==null?{...n,beats:1}:n)};}
function melodyMidi(m,n){if(n.deg!==undefined)return midi(m,m.vozOctave,n.deg)+12*n.oct;return 12*((n.octave??m.vozOctave)+1)+n.pc;}
/* Sílabas: cada grupo de vocales de una palabra es un núcleo; entre dos núcleos de la misma palabra, la última consonante (o dos, si es pr, bl, tr…)
   abre la sílaba siguiente y las demás cierran la anterior. own[k] = sílaba del fonema k. */
const STRONG=new Set(['a','e','o']);/* dos vocales fuertes juntas (le-er, fe-o) son dos sílabas */
function silabas(ph){const L=[];ph.forEach((q,k)=>{if(!q.v)return;const last=L.at(-1);if(last&&last.e===k-1&&ph[last.s].w===q.w&&!(STRONG.has(ph[k-1].p)&&STRONG.has(q.p)))last.e=k;else L.push({s:k,e:k});});
 const own=new Array(ph.length).fill(-1);L.forEach((n,j)=>{for(let k=n.s;k<=n.e;k++)own[k]=j;});
 for(let j=0;j<=L.length;j++){const a=j?L[j-1].e+1:0,z=j<L.length?L[j].s:ph.length,cons=[];for(let k=a;k<z;k++)cons.push(k);
  if(j===L.length){cons.forEach(k=>own[k]=j-1);continue;}if(!j){cons.forEach(k=>own[k]=0);continue;}
  const bw=ph[L[j].s].w,inB=cons.filter(k=>ph[k].w===bw);cons.filter(k=>ph[k].w!==bw).forEach(k=>own[k]=j-1);
  if(ph[L[j-1].e].w!==bw){inB.forEach(k=>own[k]=j);continue;}
  const real=inB.filter(k=>ph[k].p!=='_'&&ph[k].p!==' ');let split=real.length?1:0;if(real.length>=2&&['l','r','ɹ'].includes(ph[real.at(-1)].p)&&['p','b','t','d','k','g','f'].includes(ph[real.at(-2)].p))split=2;
  const onset=new Set(real.slice(real.length-split));inB.forEach(k=>own[k]=onset.has(k)?j:j-1);}
 return {n:L.length,own};}
const isEn=(m,v)=>/^en/.test(v.lang||m.vozLang||'');
/* Tiempos, alturas y niveles de cada sonido: la frase entera cabe en el bloque (si no, se habla más rápido). Con melodía escrita, canta. */
function speechEvents(piece,v){const m=piece.music,vc=m.voices[v.i]||m.voices[0];if(v.speak!=='vocoder'||!String(v.text||'').trim())return [];const ph=(isEn(m,v)&&window.LecturaVozEn?window.LecturaVozEn.fonemas:fonemas)(v.text);if(!ph.length)return [];let mel=null;try{mel=melodia(v.sing);}catch(_){}
 const n=SCALES[m.scale].length,ws=words(v.text),base=(dur=>dur)(0),durOf=q=>q.p==='_'||q.p===' '?q.d:q.v?(q.stress?.17:.11):q.rr?.12:NOISE[q.p]&&'ptk'.includes(q.p)?.07:NOISE[q.p]?.09:.065;
 let total=ph.reduce((a,q)=>a+durOf(q),0)/m.vozRate;const fit=Math.max(1,total/(v.duration*.95));let t=0;const ask=ph.some(q=>q.ask),lastW=ph.at(-1).w,lastV=ph.map(q=>!!q.v).lastIndexOf(true);
 const steps=ph.map((q,k)=>{const d=durOf(q)/m.vozRate/fit,deg=m.vozMelody==='monotono'?0:m.vozMelody==='palabras'?wordDegree(piece.seed,ws[q.w]||'',n):Math.round(Math.sin(q.w*1.3+random(piece.seed+':habla:'+v.key,0)*6)*2),
  bend=(q.stress?2:0)-(m.vozMelody==='habla'?q.w/Math.max(1,lastW)*1.5:0)+(k>=lastV-1&&k>=0&&lastV>=0?(ask?3:-1):0),st={t,d,p:q.p,v:q.v?1:0,rr:q.rr?1:0,midi:midi(m,m.vozOctave,deg)+bend};t+=d;return st;});
 let steps2=steps,dur=t;const syl=mel&&silabas(ph);
 if(syl&&syl.n){const notes=[];for(let j=0,k=0;j<syl.n&&k<4096;k++){const n=mel.notes[k%mel.notes.length];if(n.rest){notes.push({rest:true,beats:n.beats});continue;}notes.push({syl:j++,midi:melodyMidi(m,n),beats:n.beats});}
  const noteOf=new Map(notes.filter(n=>!n.rest).map(n=>[n.syl,n.midi]));
  if(!mel.rhythm){/* La altura es la de la nota de su sílaba; el ritmo sigue siendo el del habla, sin inflexiones. */let last=noteOf.get(0);steps2=steps.map((s,k)=>{const j=syl.own[k];if(j>=0&&noteOf.has(j))last=noteOf.get(j);return {...s,midi:last};});}
  else{/* Canto medido: cada sílaba dura sus tiempos; las consonantes van al principio (y al final) y la vocal llena el resto. */
   const spb=60/(piece.tempo?.bpm||90),out=[];let tt=0,prev=notes.find(n=>!n.rest).midi;
   for(const n of notes){const D=n.beats*spb;if(n.rest){out.push({t:tt,d:D,p:'_',v:0,rr:0,midi:prev});tt+=D;continue;}prev=n.midi;
    const idx=[];syl.own.forEach((j,k)=>{if(j===n.syl&&ph[k].p!=='_'&&ph[k].p!==' ')idx.push(k);});const nuc=idx.filter(k=>ph[k].v),cons=idx.filter(k=>!ph[k].v);
    const cd=k=>Math.min(.12,durOf(ph[k])/m.vozRate),csum=cons.reduce((a,k)=>a+cd(k),0),cs=csum>D*.5?D*.5/csum:1,vd=(D-csum*cs)/Math.max(1,nuc.length);
    for(const k of idx){const q=ph[k],d=q.v?vd:cd(k)*cs;out.push({t:tt,d,p:q.p,v:q.v?1:0,rr:q.rr?1:0,midi:n.midi});tt+=d;}}
   steps2=out;dur=tt;}}
 const recipe=Object.hasOwn(INSTR,vc.instrument)?null:(m.instruments||[]).find(r=>r.id===vc.instrument),sample=Object.hasOwn(INSTR,vc.instrument)?null:(m.samples||[]).find(s=>s.id===vc.instrument);
 return [{t:v.born,kind:'speech',steps:steps2,dur,carrier:m.vozCarrier,vel:m.vozGain*(vc.gain??.7)/.7,pan:vc.pan||0,instr:vc.instrument,...(recipe?{recipe}:{}),...(sample?{sample}:{})}];}
/* Vocoder de canales: la voz sintética (modulador, no se oye) se parte en 14 bandas; la envolvente de cada una (al cuadrado: más contraste) abre la misma banda
   del portador, que es lo que suena: el instrumento de la voz (una nota por sílaba, con un hilo de sierra debajo para que las vocales largas
   no se apaguen) o un colchón de quinta y octava que sigue la entonación. Las consonantes sordas pasan aparte, para que se entiendan. */
const VOCODER_BANDS=Array.from({length:14},(_,k)=>170*Math.pow(6400/170,k/13));
function vocode(ctx,b,at,ev,env,nodes){const mod=ctx.createGain(),carrier=ctx.createGain(),out=ctx.createGain(),v=Math.max(.0002,ev.vel);out.gain.value=5.5;const lim=ctx.createDynamicsCompressor();lim.threshold.value=-22;lim.knee.value=6;lim.ratio.value=12;lim.attack.value=.002;lim.release.value=.12;out.connect(lim);lim.connect(env);
 const mEnv=ctx.createGain();mEnv.connect(mod);speak(ctx,b,at,{...ev,carrier:'sierra',vel:1},mEnv,nodes);
 const rect=new Float32Array(1024);for(let k=0;k<1024;k++)rect[k]=Math.abs(k/511.5-1);
 for(const f of VOCODER_BANDS){const mb=ctx.createBiquadFilter(),ws=ctx.createWaveShaper(),lp=ctx.createBiquadFilter(),cb=ctx.createBiquadFilter(),vca=ctx.createGain();
  mb.type=cb.type='bandpass';mb.frequency.value=cb.frequency.value=f;mb.Q.value=cb.Q.value=5;ws.curve=rect;lp.type='lowpass';lp.frequency.value=28;vca.gain.value=0;
  const pre=ctx.createGain(),sq=ctx.createGain();pre.gain.value=6;sq.gain.value=0;mod.connect(mb);mb.connect(ws);ws.connect(lp);lp.connect(pre);pre.connect(sq);pre.connect(sq.gain);sq.connect(vca.gain);carrier.connect(cb);cb.connect(vca);vca.connect(out);}
 const hp=ctx.createBiquadFilter(),sib=ctx.createGain();hp.type='highpass';hp.frequency.value=4200;sib.gain.value=.09;mod.connect(hp);hp.connect(sib);sib.connect(env);
 const bed=(ratio,gain,type='sawtooth')=>{const o=ctx.createOscillator(),g=ctx.createGain();o.type=type;g.gain.value=gain;o.connect(g);g.connect(carrier);nodes.push(o);for(const s of ev.steps)o.frequency.setTargetAtTime(hz(s.midi)*ratio,at+s.t,.03);return o;};
 /* La música entera habla: lo que tocan todas las voces entra al vocoder por una compuerta mientras dura la frase, y la mezcla normal se aparta. Un hilo de sierra, muy bajo, sostiene las palabras si la música calla. */
 if(ev.carrier==='musica'){out.gain.value=14;bed(1,.12);const gate=ctx.createGain();gate.gain.setValueAtTime(0,ctx.currentTime);gate.gain.setValueAtTime(1,at);gate.gain.setValueAtTime(0,at+ev.dur+.3);b.input.connect(gate);gate.connect(carrier);
  b.duck.setTargetAtTime(.25,at,.08);b.duck.setTargetAtTime(1,at+ev.dur+.1,.25);
  if(typeof OfflineAudioContext!=='undefined'&&!(ctx instanceof OfflineAudioContext))setTimeout(()=>{try{b.input.disconnect(gate);}catch(_){}},Math.max(0,(at+ev.dur+1.5-ctx.currentTime)*1000));}
 else if(ev.carrier==='acorde'||ev.instr==='none'||!ev.instr){out.gain.value=8.5;bed(1,.5);bed(1.5,.35);bed(2,.25,'triangle');bed(.5,.3,'square');}
 else{out.gain.value=4.3;bed(1,.18);/* Saturación suave: un instrumento casi senoidal (kalimba) gana armónicos para que las vocales lo puedan esculpir; conserva ataque y altura. */
  const drive=ctx.createGain(),sat=ctx.createWaveShaper(),curve=new Float32Array(1024);for(let k=0;k<1024;k++)curve[k]=Math.tanh(4*(k/511.5-1))/Math.tanh(4);sat.curve=curve;drive.gain.value=2.5;drive.connect(sat);sat.connect(carrier);
  const cb={...b,input:drive},live=new Set();let prev=false;ev.steps.forEach((s,k)=>{const vow=!!s.v;if(vow&&!prev){let next=ev.steps.findIndex((q,j)=>j>k&&q.v&&!ev.steps[j-1].v);const dur=Math.max(.25,(next<0?ev.dur:ev.steps[next].t)-s.t);play(ctx,cb,at+s.t,{kind:'note',instr:ev.instr,midi:s.midi,vel:1.6,dur,...(ev.recipe?{recipe:ev.recipe}:{}),...(ev.sample?{sample:ev.sample}:{})},live);}prev=vow;});}
 env.gain.setValueAtTime(.5*v,at);env.gain.setTargetAtTime(0,at+ev.dur+.15,.05);return ev.dur+.5;}
/* Síntesis: portadora (sierra, pulso, coro o ruido) → tres filtros de formante; ruido aparte para las consonantes sordas. */
function speak(ctx,b,at,ev,env,nodes){const v=Math.max(.0002,ev.vel),sum=ctx.createGain(),voiced=ctx.createGain(),hiss=ctx.createGain(),nf=ctx.createBiquadFilter(),ns=ctx.createBufferSource();
 sum.connect(env);voiced.connect(sum);hiss.connect(sum);voiced.gain.setValueAtTime(0,at);hiss.gain.setValueAtTime(0,at);ns.buffer=b.noise;ns.loop=true;ns.connect(nf);nf.type='bandpass';nf.connect(hiss);nodes.push(ns);
 const bands=[1,.55,.3].map((g,k)=>{const f=ctx.createBiquadFilter(),gg=ctx.createGain();f.type='bandpass';f.Q.value=k?12:8;gg.gain.value=g*(k?2.2:1.6);f.connect(gg);gg.connect(voiced);return f;});
 const oscs=[];if(ev.carrier==='susurro'){const s2=ctx.createBufferSource();s2.buffer=b.noise;s2.loop=true;s2.playbackRate.value=.73;bands.forEach(f=>s2.connect(f));nodes.push(s2);}
 else(ev.carrier==='coro'?[0,4,7]:[0]).forEach((iv,j)=>{const o=ctx.createOscillator(),g=ctx.createGain();o.type=ev.carrier==='pulso'?'square':'sawtooth';o.detune.value=iv*100+(j?(j%2?7:-7):0);g.gain.value=ev.carrier==='coro'?.45:1;o.connect(g);bands.forEach(f=>g.connect(f));nodes.push(o);oscs.push(o);});
 env.gain.setValueAtTime(.5*v,at);
 for(const s of ev.steps){const t0=at+s.t,F=FORMANT[s.p],N=NOISE[s.p];for(const o of oscs)o.frequency.setTargetAtTime(hz(s.midi),t0,.02);
  if(F)bands.forEach((f,k)=>f.frequency.setTargetAtTime(F[k],t0,.012));
  const lv=s.p==='_'||s.p===' '?0:s.v?1:F&&!N?(s.p==='r'||s.p==='l'?.6:'bdg'.includes(s.p)?.45:'mnñ'.includes(s.p)?.5:.55):0;
  voiced.gain.setTargetAtTime(lv,t0,.012);if(s.rr)for(let j=1;j<4;j++)voiced.gain.setTargetAtTime(j%2?.15:.6,t0+s.d*j/4,.005);
  if(N){nf.frequency.setValueAtTime(N[0],t0);nf.Q.setValueAtTime(N[1],t0);if('ptk'.includes(s.p)){hiss.gain.setValueAtTime(0,t0);hiss.gain.setValueAtTime(N[2],t0+s.d*.45);hiss.gain.setTargetAtTime(0,t0+s.d*.5,.012);}else hiss.gain.setTargetAtTime(N[2],t0,.01);}
  else hiss.gain.setTargetAtTime(ev.carrier==='susurro'&&lv?.12:0,t0,.01);}
 const end=ev.dur+.05;voiced.gain.setTargetAtTime(0,at+ev.dur,.02);hiss.gain.setTargetAtTime(0,at+ev.dur,.02);env.gain.setTargetAtTime(0,at+end,.03);return end+.2;}
const voiceSchema={instrument:['Instrumento','select','kalimba',INSTR],octave:['Octava','range',4,1,6,1],gain:['Volumen de la voz','range',.7,0,1,.05],pan:['Paneo (izquierda – derecha)','range',0,-1,1,.05],entry:['Al entrar un verso','select','note',{none:'nada',note:'una nota',chord:'acorde',arpeggio:'arpegio'}],words:['Una nota por palabra (la palabra tiene su nota)','check',false],gesture:['Sonido del comportamiento (estallar, caer, burbujas…)','check',true]};
function norm(raw,fields){if(raw==null)raw={};if(typeof raw!=='object'||Array.isArray(raw))throw Error('Música inválida');const out={};for(const [key,d]of Object.entries(fields)){let v=raw[key]??d[2];
 if(d[1]==='range'){if(!Number.isFinite(v))throw Error('Medida musical inválida: '+key);v=Math.min(d[4],Math.max(d[3],v));}
 else if(d[1]==='select'){if(!Object.hasOwn(d[3],v))throw Error('Opción musical desconocida: '+key);}
 else if(d[1]==='text'){if(typeof v!=='string'||v.length>d[3])throw Error('Texto demasiado largo: '+key);if((key==='pattern'||d[4]==='patron')&&!/^[xo.\-| ]*$/i.test(v))throw Error('Patrón inválido: usa x, o, punto, guion, espacio o |');}
 else v=!!v;out[key]=v;}return out;}
/* Instrumentos inventados: recetas de síntesis (datos con rangos). De 1 a 6 parciales, envolvente, filtro con barrido, vibrato, FM y aire. */
const WAVES={sine:'seno',triangle:'triángulo',square:'cuadrada',sawtooth:'sierra'};
const recipeSchema={name:['Nombre','text','instrumento nuevo',40],gain:['Volumen','range',.8,0,1.5,.05],attack:['Ataque (s)','range',.01,.001,4,.001],decay:['Caída (s)','range',.4,.01,8,.01],sustain:['Sostén','range',.4,0,1,.01],release:['Relajación (s)','range',.8,.01,8,.01],
 filterType:['Filtro','select','lowpass',{none:'sin filtro',lowpass:'pasa bajos',highpass:'pasa altos',bandpass:'pasa banda'}],filterFreq:['Frecuencia del filtro (Hz)','range',2400,40,16000,1],filterQ:['Resonancia del filtro','range',1,.1,30,.1],sweep:['Barrido del filtro (octavas desde arriba)','range',0,-6,6,.1],
 vibRate:['Vibrato: velocidad (Hz)','range',0,0,20,.1],vibDepth:['Vibrato: profundidad (cents)','range',0,0,100,1],vibDelay:['Vibrato: espera (s)','range',0,0,3,.05],
 fmRatio:['FM: razón del modulador (0 = sin FM)','range',0,0,16,.01],fmIndex:['FM: índice','range',0,0,20,.1],fmDecay:['FM: caída del índice (s)','range',1,.01,8,.01],noise:['Aire / ruido','range',0,0,1,.01]};
const partialSchema={wave:['Onda','select','sine',WAVES],ratio:['Razón de frecuencia','range',1,.25,16,.01],gain:['Nivel','range',1,0,1,.01],detune:['Desafinar (cents)','range',0,-50,50,1]};
const TEMPLATES={
 'violin-de-vidrio':{name:'violín de vidrio',gain:.8,attack:.35,decay:.4,sustain:.7,release:1.2,filterType:'bandpass',filterFreq:1800,filterQ:3,sweep:.5,vibRate:5.5,vibDepth:14,vibDelay:.25,noise:.06,partials:[{wave:'sawtooth',ratio:1,gain:1},{wave:'sine',ratio:2.01,gain:.3,detune:4}]},
 'gong-de-agua':{name:'gong de agua',gain:.9,attack:.005,decay:3,sustain:.1,release:3,filterType:'lowpass',filterFreq:3200,filterQ:.8,sweep:1.5,vibRate:.6,vibDepth:25,vibDelay:.4,fmRatio:1.41,fmIndex:3.5,fmDecay:2.5,partials:[{wave:'sine',ratio:1,gain:1},{wave:'sine',ratio:2.76,gain:.4},{wave:'sine',ratio:5.4,gain:.2}]},
 'soplo':{name:'soplo',gain:.9,attack:.25,decay:.3,sustain:.6,release:.9,filterType:'bandpass',filterFreq:900,filterQ:6,sweep:1,vibRate:4,vibDepth:8,vibDelay:.3,noise:.7,partials:[{wave:'sine',ratio:1,gain:.5}]},
 'organo-roto':{name:'órgano roto',gain:.7,attack:.05,decay:.2,sustain:.8,release:.4,filterType:'lowpass',filterFreq:2600,filterQ:1.5,vibRate:7,vibDepth:30,noise:.05,partials:[{wave:'square',ratio:1,gain:.8},{wave:'square',ratio:2,gain:.4,detune:-12},{wave:'sine',ratio:3,gain:.3,detune:9},{wave:'triangle',ratio:.5,gain:.5}]},
 'cuerda-frotada':{name:'cuerda frotada',gain:.8,attack:.18,decay:.6,sustain:.55,release:.7,filterType:'lowpass',filterFreq:1400,filterQ:2,sweep:1.2,vibRate:5,vibDepth:18,vibDelay:.35,fmRatio:1,fmIndex:.6,fmDecay:.8,noise:.12,partials:[{wave:'sawtooth',ratio:1,gain:1,detune:-6},{wave:'sawtooth',ratio:1,gain:.7,detune:7}]}};
/* Batería: pistas de golpes que suenan juntas, cada una con su patrón (x fuerte, o suave, . o - silencio; 4 pasos por pulso).
   Todo es síntesis: el kit decide cómo suena cada pieza. Suena con música encendida y ♩ > 0, igual que el pulso. */
const DRUMS={kick:'bombo',snare:'tarola',rim:'aro',clap:'palmas',hat:'hi-hat cerrado',openhat:'hi-hat abierto',crash:'platillo de choque',ride:'platillo ride',spray:'platillo spray ochentero',tomhi:'tom agudo',tommid:'tom medio',tomlo:'tom grave',cowbell:'cencerro'};
const KITS={acustico:'acústica',tr808:'808: sub que cae de tono, hats metálicos',tr909:'909: golpe seco y brillante',frito:'frita: 808 saturada'};
const DRUM_PAN={hat:-.25,openhat:-.25,rim:-.15,clap:.1,ride:.3,crash:.35,spray:-.35,tomhi:.35,tomlo:-.35,cowbell:.2};
const drumSchema={kit:['Kit','select','acustico',KITS],gain:['Volumen de la batería','range',.8,0,1.5,.05],tune:['Afinación (semitonos)','range',0,-12,12,1],decay:['Caída (× la del kit)','range',1,.3,3,.05],
 drive:['Saturación','range',0,0,1,.05],swing:['Swing (atrasa las semicorcheas pares)','range',0,0,.6,.01],
 ...Object.fromEntries(Object.entries(DRUMS).map(([k,l])=>[k,['Patrón: '+l,'text','',64,'patron']]))};
/* Ritmos de partida: se cargan y luego se editan paso por paso. */
const RITMOS={
 disco:{name:'disco',kit:'acustico',kick:'x...x...x...x...',snare:'....x.......x...',clap:'....o.......o...',hat:'x.x.x.x.x.x.x.x.',openhat:'..x...x...x...x.'},
 house:{name:'house',kit:'tr909',kick:'x...x...x...x...',clap:'....x.......x...',hat:'o.o.o.o.o.o.o.o.',openhat:'..x...x...x...x.',ride:'x.o.x.o.x.o.x.o.'},
 trap:{name:'trap',kit:'tr808',kick:'x......x..x.....',snare:'........x.......',hat:'x.x.x.x.xxx.x.xx',openhat:'..............x.'},
 bossa:{name:'bossa',kit:'acustico',swing:.08,kick:'x.....x.x.....x.',rim:'x..x..x...x..x..',hat:'o.o.o.o.o.o.o.o.'},
 breakbeat:{name:'breakbeat',kit:'acustico',kick:'x.x.......xx....',snare:'....x..o.o..x..o',hat:'x.x.x.x.x.x.x.x.',crash:'x...............'},
 citypop:{name:'city pop',kit:'acustico',kick:'x......x..x.....',snare:'....x.......x...',hat:'x.xxx.xxx.xxx.xx',openhat:'......x.......x.',tomhi:'..............ox',spray:'x...............'},
 ochentas:{name:'caja de ritmos ochentera',kit:'tr808',kick:'x.......x.x.....',snare:'....x.......x...',clap:'....x.......x...',hat:'x.x.x.x.x.x.x.x.',cowbell:'..x.....x.......',spray:'x.......x.......'},
 frito:{name:'frito',kit:'frito',drive:.4,kick:'x...x...x...x...',snare:'....x.......x...',hat:'xxxxxxxxxxxxxxxx',tomlo:'.............xxx'}};
function drums(raw){if(raw==null)return null;if(typeof raw!=='object'||Array.isArray(raw))throw Error('Batería inválida');for(const k of Object.keys(raw))if(k!=='name'&&!Object.hasOwn(drumSchema,k))throw Error('La batería no tiene «'+k+'»');const d=norm(raw,drumSchema);return d;}
function recipes(list){if(list==null)return [];if(!Array.isArray(list)||list.length>8)throw Error('Hasta 8 instrumentos inventados');const ids=new Set();
 return list.map(r=>{if(!r||typeof r!=='object'||Array.isArray(r))throw Error('Instrumento inválido');const id=String(r.id??'');if(!/^[a-z0-9-]{1,40}$/.test(id)||ids.has(id)||Object.hasOwn(INSTR,id))throw Error('Nombre interno de instrumento inválido: '+id);ids.add(id);
  const ps=r.partials??[{}];if(!Array.isArray(ps)||!ps.length||ps.length>6)throw Error('Un instrumento tiene de 1 a 6 parciales');return {id,...norm(r,recipeSchema),partials:ps.map(p=>norm(p,partialSchema))};});}
/* Muestras: sonidos propios. La pieza guarda la ficha y la huella; el audio vive aparte (muestras.js).
   afinado = cada nota de la escala cambia la velocidad del sonido desde su nota raíz; golpe = suena tal cual. */
const sampleSchema={name:['Nombre','text','muestra',40],root:['Nota raíz (MIDI; 60 = do central)','range',60,24,96,1],mode:['Cómo suena','select','afinado',{afinado:'afinado a la escala',golpe:'golpe, tal cual'}],gain:['Volumen','range',.8,0,1.5,.05],attack:['Ataque (s)','range',.005,0,2,.005],release:['Salida (s)','range',.3,.02,4,.01]};
function samples(list,taken){if(list==null)return [];if(!Array.isArray(list)||list.length>8)throw Error('Hasta 8 muestras');const ids=new Set();
 return list.map(s=>{if(!s||typeof s!=='object'||Array.isArray(s))throw Error('Muestra inválida');const id=String(s.id??'');if(!/^[a-z0-9-]{1,40}$/.test(id)||ids.has(id)||Object.hasOwn(INSTR,id)||taken.has(id))throw Error('Nombre interno de muestra inválido: '+id);ids.add(id);
  if(typeof s.sha!=='string'||!/^[0-9a-f]{64}$/.test(s.sha))throw Error('Huella de muestra inválida');const o={id,sha:s.sha,...norm(s,sampleSchema)};o.root=Math.round(o.root);return o;});}
/* Las voces pueden tocar los de fábrica, los inventados y las muestras de esta pieza. */
const voiceSchemaFor=m=>({...voiceSchema,instrument:[voiceSchema.instrument[0],'select','kalimba',{...INSTR,...Object.fromEntries((m?.instruments||[]).map(r=>[r.id,'✦ '+r.name])),...Object.fromEntries((m?.samples||[]).map(s=>[s.id,'♪ '+s.name]))}]});
function normalize(raw){const m=norm(raw,schema),voices=raw&&Array.isArray(raw.voices)?raw.voices:[];if(voices.length>3)throw Error('La música tiene tres voces');m.instruments=recipes(raw?.instruments);m.samples=samples(raw?.samples,new Set(m.instruments.map(r=>r.id)));if(!m.samples.length)delete m.samples;const dr=drums(raw?.drums);if(dr)m.drums=dr;const vs=voiceSchemaFor(m);m.voices=[0,1,2].map(i=>norm(voices[i],vs));return m;}
const random=(seed,k)=>LecturaCinetica.random(seed,k);
function midi(m,octave,deg){const s=SCALES[m.scale],n=s.length,o=Math.floor(deg/n);return 12*(octave+1)+NOTES.indexOf(m.root)+s[deg-o*n]+12*o;}
const hz=n=>440*2**((n-69)/12);
/* Cada palabra tiene su grado dentro de la escala (depende de la semilla, no de la voz): la misma palabra suena igual toda la tirada. */
function wordDegree(seed,word,n){return Math.floor(random(seed+':palabra:'+word,0)*n*2)-Math.floor(n/2);}
function words(text){return String(text).toLowerCase().match(/[\p{L}\p{N}]+/gu)||[];}
/* Los eventos de un bloque o disparo: v = {i, key, born, duration, text, effect}. Tiempos absolutos de la pieza. */
function events(piece,v){const m=piece.music,vc=m.voices[v.i],said=speechEvents(piece,v);if(!m.on)return said;const n=SCALES[m.scale].length,R=k=>random(piece.seed+':musica:'+v.key,k),beat=piece.tempo?.bpm?60/piece.tempo.bpm:0,step=beat?beat/2:.22,d=v.duration,out=[];
 const base=Math.floor(R('base')*n),note=(t,deg,vel,dur,instr=vc.instrument,octave=vc.octave)=>{if(instr!=='none'&&t>=0&&t<d){const recipe=Object.hasOwn(INSTR,instr)?null:(m.instruments||[]).find(r=>r.id===instr),sample=Object.hasOwn(INSTR,instr)?null:(m.samples||[]).find(s=>s.id===instr);if(!Object.hasOwn(INSTR,instr)&&!recipe&&!sample)return;out.push({t:v.born+t,kind:'note',instr,midi:midi(m,octave,deg),vel:vel*vc.gain,dur,pan:vc.pan,...(recipe?{recipe}:{}),...(sample?{sample}:{})});}},hit=(t,o)=>{if(t>=0&&t<d)out.push({t:v.born+t,pan:vc.pan,...o,vel:o.vel*vc.gain});};
 if(vc.entry==='note')note(0,base,.8,1.2);
 if(vc.entry==='chord')[0,2,4].forEach(k=>note(0,base+k,.5,1.8));
 if(vc.entry==='arpeggio')[0,2,4,7].forEach((k,j)=>note(j*step/2,base+k,.6,.9));
 const w0=out.length;if(vc.words)words(v.text).slice(0,24).forEach((w,k)=>note((k+(vc.entry==='none'?0:1))*step,wordDegree(piece.seed,w,n),.5,.7));const w1=out.length;
 /* El sonido del gesto también espera el tiempo de lectura. */
 const note0=note,hit0=hit;
 /* Gesto entre voces: suena al entrar, antes de cualquier espera. */
 if(v.cross&&vc.gesture){const c=v.cross;if(c==='interrupt')hit0(0,{kind:'noise',vel:.6,dur:.25,from:6000,to:800});if(c==='cover')hit0(0,{kind:'thud',vel:.7,dur:.4,midi:midi(m,2,base)});if(c==='correct'){note0(0,base+2,.4,.3,'pluck');note0(.12,base,.4,.5,'pluck');}if(c==='emphasis')note0(0,base+4,.35,1.2,'pad');if(c==='break'){hit0(0,{kind:'noise',vel:.9,dur:.6,from:8000,to:300});note0(0,base+n+2,.4,1.4,'glass');}if(c==='noise')hit0(0,{kind:'noise',vel:.3,dur:Math.min(6,v.duration*.8),from:5200,to:1800});if(c==='global')hit0(0,{kind:'drum',vel:.9,dur:.4});}
 if(vc.gesture){const H=LecturaCinetica.holdOf({effect:v.effect,hold:v.hold},v.duration),d=v.duration-H-LecturaCinetica.restOf({effect:v.effect,hold:v.hold,rest:v.rest},v.duration),note=(t,...r)=>note0(t+H,...r),hit=(t,o)=>hit0(t+H,o),e=v.effect,b=beat||.55;
  if(e==='shatter'){const te=d*.35;hit(te,{kind:'noise',vel:.9,dur:.6,from:7000,to:300});[0,1,2].forEach(k=>note(te+k*.03,base+n+Math.floor(R('s'+k)*n),.4,1.6,'glass'));}
  if(e==='fall')for(let k=0;k<6;k++)hit(.5+k*.28+R('f'+k)*.1,{kind:'thud',vel:.9-k*.12,dur:.35,midi:midi(m,2,base)});
  if(e==='bubbles')for(let k=0;k<5;k++)note(.3+k*.45+R('b'+k)*.1,base+k*2,.35,.5,'glass');
  if(e==='erode')for(let k=0;k<8;k++)hit(d*(.12+k*.07),{kind:'noise',vel:.22,dur:.08,from:2600,to:2600});
  if(e==='swarm'){note(d*.1,base,.35,d*.7,'pad');note(d*.1,base+2,.25,d*.7,'pad');}
  if(e==='burst')for(let k=0;k<4;k++)note(b*(1+k),base+n,.45,.25);
  if(e==='stutter')for(let k=0;k<4;k++)note(k*(beat?beat/4:.07),base,.5,.12);
  if(e==='exit')hit(d*.3,{kind:'noise',vel:.5,dur:1.2,from:300,to:6000});
  if(e==='collapse')for(let k=0;k<8;k++)note(d*(.1+k*.09),base+n-k,.4,.6);
  /* Cinética 3: cada transformación con su sonido, en golpes. */
  const beats=f=>{for(let k=0;k<Math.min(16,Math.floor(d/b));k++)f(k*b,k);};
  if(e==='caseflip')beats((t,k)=>note(t,base+(k%2?n:0),.3,.2,'pluck'));
  if(e==='weight')note(0,base-n,.35,d*.9,'drone',Math.max(1,vc.octave-1));
  if(e==='breathe'){note(0,base,.22,d*.9,'pad');note(0,base+2,.18,d*.9,'pad');}
  if(e==='monument')for(let k=0;k<Math.min(6,words(v.text).join('').length);k++)note((k+.5)*(beat?beat*2:d/6),base+k,.5,1,'bell');
  if(e==='texture')for(let k=0;k<4;k++)note(d*(.1+k*.15),base+n+k*2,.3,1.2,'glass');
  if(e==='flip')beats((t,k)=>note(t+b/2,base+n+(k%2),.25,.12,'pluck'));
  if(e==='hollow')beats((t,k)=>note(t,base+(k%2?2:0),.28,.3,k%2?'glass':'kalimba'));
  if(e==='invert')beats(t=>hit(t,{kind:'noise',vel:.3,dur:.05,from:5200,to:5200}));
  if(e==='cut')beats((t,k)=>{if(k){hit(t,{kind:'thud',vel:.6,dur:.2,midi:midi(m,2,base)});note(t,base+Math.floor(R('c'+k)*n),.4,.2);}});
  if(e==='interleave')for(let k=0;k<Math.min(24,words(v.text).join('').length);k++)note(k*(beat?beat/4:.12),k%2?base+n:base,.28,.25);
  /* Cinética 4 */
  const nw=Math.max(1,words(v.text).length),chars=words(v.text).join('').length;
  if(e==='lifespan')for(let k=0;k<Math.min(8,nw);k++)note(R('n'+k)*d*.5,base+k,.35,.6,'kalimba');
  if(e==='push')for(let k=0;k<Math.min(12,nw);k++)note(k*(beat||d*.8/nw),base+k,.35,.3,'pluck');
  if(e==='ghost'){note(0,base,.25,d*.8,'pad');note(d*.75,base+n,.3,1.5,'glass');}
  if(e==='drift')note(0,base-n,.2,d,'drone',Math.max(1,vc.octave-1));
  if(e==='orbit')for(let k=0;k<6;k++)note(k*d/6,base+[0,2,4,2][k%4],.3,1.2,'bell');
  if(e==='chase')for(let k=0;k<16;k++)note(k*(beat?beat/2:.2),base+k%5,.25,.15,'pluck');
  if(e==='gridhop')beats((t,k)=>{if(k){hit(t,{kind:'thud',vel:.4,dur:.15,midi:midi(m,2,base)});note(t,base+Math.floor(R('g'+k)*n),.3,.25,'kalimba');}});
  if(e==='ticker')beats(t=>hit(t,{kind:'shaker',vel:.3,dur:.07}));
  if(e==='rebuild'){hit(d*.3,{kind:'noise',vel:.45,dur:.4,from:6000,to:600});hit(d*.65,{kind:'noise',vel:.35,dur:.5,from:400,to:5000});}
  if(e==='morph')for(let k=0;k<Math.min(10,chars);k++)note(d*.1+k/Math.max(1,chars)*d*.6,base+k%n,.3,.5,'glass');
  if(e==='disorder')for(let k=0;k<12;k++)hit(d*Math.pow(k/12,.7),{kind:'noise',vel:.1+k*.03,dur:.06,from:3000,to:3000});
  if(e==='clash'){const tc=d*.35;hit(tc,{kind:'thud',vel:1,dur:.5,midi:midi(m,2,base)});hit(tc,{kind:'noise',vel:.7,dur:.4,from:5000,to:400});[0,1,3].forEach(k=>note(tc,base+k,.35,1.5,'bell'));}
  /* Cinética 5 */
  const lines=String(v.text).split(/\n/).length;
  if(e==='verses')for(let k=0;k<Math.max(1,nw>6?3:1);k++)note(k*(beat?beat*2:d*.8/3),base+k*2,.4,1,'kalimba');
  if(e==='mask')hit(0,{kind:'noise',vel:.35,dur:d*.35,from:200,to:4000});
  if(e==='fadeunits')for(let k=0;k<6;k++)note(d*(.2+k*.1),base+n-k,.25,.8,'glass');
  if(e==='leading')note(0,base,.2,d*.9,'pad');
  if(e==='layers')beats((t,k)=>{if(k%2===0)note(t,base+[0,4,2][k/2%3],.3,.6,'bell');});
  if(e==='bigthree')[0,1,2].forEach(k=>note(d*.15+k*.25,base-n+k*2,.6,1.8,'bass'));
  if(e==='frame')for(let k=0;k<8;k++)note(d*k/10,base+k%n,.25,.2,'pluck');
  if(e==='mass')for(let k=0;k<10;k++)note(d*k/10,base+(k%3),.12+k*.02,.8,'pad');
  if(e==='wall')beats(t=>hit(t,{kind:'drum',vel:.4,dur:.3}));
  if(e==='saturate'){for(let k=0;k<14;k++)hit(d*.7*k/14,{kind:'noise',vel:.1+k*.03,dur:.05,from:4000,to:4000});note(d*.7,base,.9,2,'bell');}
  if(e==='syllables')beats((t,k)=>note(t,base+(k%4===0?n:0),.4,.25,'kalimba'));
  if(e==='freeze'){hit(d*.55,{kind:'noise',vel:.8,dur:.5,from:8000,to:500});note(d*.55,base+n+1,.4,1.5,'glass');}
  /* Cinética 6 */
  if(e==='fontswap')beats((t,k)=>note(t,base+Math.floor(R('fs'+k)*n),.3,.2,['pluck','kalimba','bell','glass'][k%4]));
  if(e==='scales'){note(0,base,.3,.6,'bell');beats((t,k)=>{if(k&&k%4===0)note(t,base+Math.floor(R('sc'+k)*n),.45,.9,'bell');});}
  if(e==='stretch')beats((t,k)=>note(t,base+(k%3)*2,.3,.25,'pluck'));
  if(e==='architecture')for(let k=0;k<Math.min(8,nw);k++){const t=k*(beat?beat*2:d*.6/nw)+.3;hit(t,{kind:'thud',vel:.7,dur:.3,midi:midi(m,2,base)});note(t,base+k,.35,.8,'bass',2);}
  if(e==='figure')for(let k=0;k<12;k++)note(d*(.05+k*.04),base+[0,2,4,7,9][k%5],.25,.6,'kalimba');
  if(e==='void'){note(0,base-n,.3,d*.8,'drone',Math.max(1,vc.octave-1));hit(0,{kind:'noise',vel:.2,dur:d*.5,from:1200,to:200});}
  if(e==='crop'){hit(0,{kind:'thud',vel:.8,dur:.6,midi:midi(m,2,base)});note(0,base,.25,d*.8,'pad');}
  if(e==='microtext'){note(0,base-n,.5,1.5,'bell');for(let k=0;k<Math.min(20,chars);k++)note(.4+k*(beat?beat/4:.1),base+n+(k%3),.15,.1,'pluck');}
  if(e==='chroma'){note(0,base,.3,.6,'glass');beats((t,k)=>{if(k%2)[0,4,7].forEach((j,q)=>note(t+q*.02,base+j,.2,.4,'glass'));});}
  if(e==='warp'){note(0,base,.25,d*.9,'pad');note(0,base+1,.18,d*.9,'pad');}
  if(e==='pixel'){note(0,base+n,.3,.3,'pluck');beats((t,k)=>{if(k%4===0)for(let j=0;j<4;j++)hit(t+j*b/8,{kind:'noise',vel:.25-j*.05,dur:.04,from:2000+j*1500,to:2000+j*1500});});}
  if(e==='mirror')beats((t,k)=>{note(t,base+k%3*2,.3,.4,'kalimba');note(t+.01,base+n-(k%3)*2,.2,.4,'bell');});
  /* Cinética 7 */
  if(e==='fill')note(0,base-n,.4,d*.8,'pad');
  if(e==='relay')for(let k=0;k<Math.min(10,nw);k++)note(k*d*.6/Math.max(1,nw),base+k%n,.25,.4,'kalimba');
  if(e==='swiss')for(let k=0;k<Math.min(6,nw);k++)note(.2+k*.3,base+[0,4,2,5,1,3][k],.3,.5,'bell');
  if(e==='unfold'){note(0,base,.3,.6,'glass');note(d*.3,base+2,.3,.8,'glass');hit(d*.7,{kind:'noise',vel:.3,dur:.6,from:4000,to:400});}
  if(e==='relief')note(0,base-n,.25,d*.9,'drone',Math.max(1,vc.octave-1));
  if(e==='cloud'){note(0,base,.2,d*.8,'pad');note(0,base+4,.15,d*.8,'pad');}
  if(e==='slam')for(let k=0;k<Math.min(10,nw);k++){const t=k*(beat||d*.7/nw);hit(t,{kind:'thud',vel:.8,dur:.35,midi:midi(m,2,base)});hit(t,{kind:'noise',vel:.25,dur:.15,from:3000,to:300});}
  if(e==='anticipate')beats(t=>{hit(t-b*.3,{kind:'noise',vel:.12,dur:b*.3,from:300,to:3000});note(t,base,.4,.25,'pluck');});
  if(e==='lag')beats(t=>{for(let j=0;j<3;j++)note(t+j*b*.12,base+j*2,.3-j*.07,.2,'kalimba');});
  if(e==='whip')beats((t,k)=>{if(k%2===0)hit(t,{kind:'noise',vel:.35,dur:.3,from:500,to:7000});});
  if(e==='canon')for(let j=0;j<3;j++)note(j*(beat?beat*2:d*.18),base+j*2,.35-j*.06,1,'bell');
  if(e==='dialogue'){note(0,base+4,.35,.6,'kalimba');note(d*.5,base,.35,.8,'bell');}
  /* Cinética 8 */
  if(e==='vortex')for(let k=0;k<10;k++)note(d*(.1+k*.06),base+n-k,.3-k*.02,.4,'glass');
  if(e==='vowels'){note(0,base+4,.3,d*.8,'pad');note(0,base,.25,d*.8,'pad',Math.max(1,vc.octave-1));}
  if(e==='sort')for(let k=0;k<Math.min(12,chars);k++)note(d*.1+k*d*.035,base+k%n,.25,.2,'pluck');
  if(e==='rain')for(let k=0;k<Math.min(16,chars);k++)note(d*(.05+k/Math.max(1,chars)*.45)+R('ll'+k)*.2,base+n+Math.floor(R('lln'+k)*n),.18,.25,'kalimba');
  if(e==='tide')hit(0,{kind:'noise',vel:.2,dur:d*.9,from:300,to:900});
  if(e==='spotlight')note(0,base+2,.25,d*.9,'pad');
  if(e==='braid')beats((t,k)=>note(t,base+(k%2?2:0),.25,.3,'kalimba'));
  if(e==='pendulum')for(let k=0;k<8;k++)note(k*d/8,base+(k%4)*2,.25,.5,'bell');
  if(e==='domino')for(let k=0;k<Math.min(14,chars);k++)hit(d*(.15+k/Math.max(1,chars)*.55),{kind:'thud',vel:.35,dur:.12,midi:midi(m,3,base+k%n)});
  if(e==='magnify')note(0,base,.25,d*.9,'glass');
  if(e==='stamp')for(let k=0;k<Math.min(10,nw);k++){const t=k*(beat||d*.7/nw);hit(t,{kind:'thud',vel:.6,dur:.2,midi:midi(m,2,base)});hit(t,{kind:'noise',vel:.15,dur:.08,from:2500,to:2500});}
  if(e==='neon')for(let k=0;k<12;k++)hit(R('ne'+k)*d,{kind:'noise',vel:.08+R('nv'+k)*.1,dur:.05,from:6000,to:6000});
  /* Cinética 9 */
  if(e==='handwrite')for(let k=0;k<Math.min(16,chars);k++)hit(k/Math.max(1,chars)*d*.6+R('pl'+k)*.05,{kind:'noise',vel:.12,dur:.25,from:3000,to:1200});
  if(e==='melt')for(let k=0;k<6;k++)note(d*(.3+k*.1),base-k,.3,.9,'glass',Math.max(1,vc.octave-1));
  if(e==='fold')beats((t,k)=>hit(t,{kind:'noise',vel:.18,dur:.2,from:1500,to:600}));
  if(e==='crawl'){note(0,base,.3,d*.9,'pad');note(0,base+4,.2,d*.9,'pad');}
  if(e==='puzzle')for(let k=0;k<Math.min(10,chars);k++)hit(k/Math.max(1,chars)*d*.5+.7,{kind:'thud',vel:.3,dur:.08,midi:midi(m,4,base+k%n)});
  if(e==='typo')for(let k=0;k<Math.min(24,chars);k++)hit(k/Math.max(1,chars)*d*.75,{kind:'tick',vel:.5,dur:.03});
  if(e==='bloom')[0,2,4,6].forEach((j,q)=>note(d*.2+q*.15,base+j,.3,1.4,'bell'));
  if(e==='glitch')for(let k=0;k<10;k++)hit(R('gl'+k)*d,{kind:'noise',vel:.25,dur:.06,from:7000,to:200});
  if(e==='sundial')note(0,base-n,.25,d*.9,'drone',Math.max(1,vc.octave-1));
  if(e==='blot')hit(.05,{kind:'noise',vel:.3,dur:d*.5,from:400,to:2500});
  if(e==='stairs')for(let k=0;k<Math.min(10,nw);k++)note(k*(beat||d*.6/nw),base+nw-k,.35,.3,'pluck');
  if(e==='wind')hit(0,{kind:'noise',vel:.25,dur:d*.9,from:600,to:1400});
  /* Cinética 10: señales */
  if(e==='morse'){const u=.08,MC={a:'.-',b:'-...',c:'-.-.',d:'-..',e:'.',f:'..-.',g:'--.',h:'....',i:'..',j:'.---',k:'-.-',l:'.-..',m:'--',n:'-.',o:'---',p:'.--.',q:'--.-',r:'.-.',s:'...',t:'-',u:'..-',v:'...-',w:'.--',x:'-..-',y:'-.--',z:'--..'},letters=words(v.text).join('').normalize('NFD').replace(/[\u0300-\u036f]/g,'').slice(0,40);let q=0;[...letters].forEach((ch,k)=>{let t=k/Math.max(1,letters.length)*d*.55;if(t<q)t=q;for(const sym of MC[ch]||''){note(t,base+n,.22,(sym==='.'?1:3)*u,'pluck');t+=((sym==='.'?1:3)+1)*u;}q=t;});}
  if(e==='binary')for(let k=0;k<16;k++)hit(d*.25+k*d*.03,{kind:'tick',vel:k%3?.25:.5,dur:.02});
  if(e==='braille')for(let k=0;k<Math.min(10,chars);k++)note(d*.25+k*.12,base+[0,2,4][k%3]+n,.18,.3,'kalimba');
  if(e==='ekg')beats(t=>{hit(t,{kind:'thud',vel:.7,dur:.18,midi:midi(m,2,base)});hit(t+.18,{kind:'thud',vel:.45,dur:.15,midi:midi(m,2,base)});});
  if(e==='constellation')for(let k=0;k<10;k++)note(d*(.2+k*.055),base+n+Math.floor(R('est'+k)*n),.18,.9,'bell');
  if(e==='sew')for(let k=0;k<Math.min(20,chars);k++)note(k/Math.max(1,chars)*d*.7,base+(k%2?2:0),.2,.15,'pluck');
  if(e==='ripple')beats((t,k)=>{if(k%2===0){note(t,base+n,.35,1.4,'glass');note(t,base,.2,1.2,'glass',Math.max(1,vc.octave-1));}});
  if(e==='quake'){hit(d*.15,{kind:'noise',vel:.6,dur:d*.55,from:120,to:300});for(let k=0;k<5;k++)hit(d*(.25+k*.08),{kind:'thud',vel:.5,dur:.3,midi:midi(m,1,base)});}
  if(e==='helix'){note(0,base,.25,d*.9,'pad');for(let k=0;k<8;k++)note(k*d/8,base+[0,2,4,7][k%4],.2,.3,'kalimba');}
  if(e==='comet')for(let k=0;k<Math.min(10,chars);k++)hit(k/Math.max(1,chars)*d*.55+.3,{kind:'noise',vel:.2,dur:.5,from:6000,to:500});
  if(e==='balloon')for(let k=0;k<6;k++)note(d*(.3+k*.1),base+k*2,.25,.6,'glass');
  if(e==='phase'){const a=beat?beat/4:.12,b2=a*1.06;for(let k=0;k<32;k++){note(k*a,base+[0,2,4,7][k%4],.2,.12,'kalimba');note(k*b2,base+[0,2,4,7][k%4]+n,.16,.12,'kalimba');}}
  /* Cinética 11: la máquina que lee y escribe */
  if(e==='cuneiform')for(let k=0;k<Math.min(14,chars);k++)hit(k/Math.max(1,chars)*d*.6+.05,{kind:'thud',vel:.28,dur:.12,midi:midi(m,2,base+k%3)});
  if(e==='autocomplete'){for(let k=0;k<Math.min(20,chars);k++)hit(k/Math.max(1,chars)*d*.8,{kind:'tick',vel:.35,dur:.02});for(let k=0;k<4;k++)note(d*(.15+k*.18),base+n+k,.15,.5,'glass');}
  if(e==='topk')for(let k=0;k<Math.min(8,nw);k++){const t=(k/nw*.7+.12)*d;[0,1,2].forEach(j=>note(t-.75+j*.2,base+n+Math.floor(R('tk'+k+j)*n),.12,.25,'glass'));note(t,base+k%n,.35,.7,'kalimba');}
  if(e==='tokens')for(let k=0;k<Math.min(12,Math.ceil(chars/3));k++)note(d*.15+k*.12,base+(k%2?2:0),.22,.2,'pluck');
  if(e==='attention'){note(0,base-n,.22,d*.9,'pad');for(let k=0;k<6;k++)note(d*(.2+k*.1),base+n+Math.floor(R('at'+k)*n),.2,1.2,'bell');}
  if(e==='scan')hit(0,{kind:'noise',vel:.18,dur:d*.7,from:700,to:5200});
  if(e==='track'){for(let k=0;k<Math.min(10,nw);k++)hit(k/nw*d*.6,{kind:'tick',vel:.4,dur:.03});[0,4,7].forEach((j,q)=>note(d*.75+q*.05,base+j,.3,.9,'bell'));}
  if(e==='redact')for(let k=0;k<Math.min(8,nw);k++)hit((R('rd'+k)*.6+.12)*d,{kind:'noise',vel:.22,dur:.25,from:3000,to:900});
  if(e==='marginalia')for(let k=0;k<4;k++)hit(d*(.2+k*.15),{kind:'noise',vel:.14,dur:.5,from:2600,to:3400});
  if(e==='karaoke')for(let k=0;k<Math.min(12,nw);k++)note(.08*d+k/nw*d*.88,base+[0,2,4,2][k%4],.22,.4,'kalimba');
  if(e==='hesitate'){let t=0;for(let k=0;k<Math.min(24,chars);k++){hit(t,{kind:'tick',vel:.35,dur:.02});t+=d*.5/Math.max(1,chars)*(R('hs'+k)<.2?4:1);}}
  if(e==='palimpsest'){note(0,base-n,.2,d*.9,'drone',Math.max(1,vc.octave-1));for(let k=0;k<5;k++)note(d*(.1+k*.15),base+k,.18,.8,'glass');}
  /* Transiciones */
  if(e==='portal'){hit(d*.35,{kind:'noise',vel:.35,dur:d*.5,from:180,to:5200});note(d*.35,base-n,.3,d*.55,'pad',Math.max(1,vc.octave-1));hit(d*.85,{kind:'thud',vel:.9,dur:1.2,midi:midi(m,1,base)});note(d*.85,base,.35,2.5,'bell');}
  if(e==='respire'){note(0,base,.2,d*.9,'pad');note(0,base+2,.16,d*.9,'pad');hit(0,{kind:'noise',vel:.12,dur:d*.9,from:500,to:900});}
  if(e==='impact'&&beat)for(let k=0;k<Math.min(8,Math.floor(d/beat));k++)hit(k*beat,{kind:'thud',vel:.5,dur:.2,midi:midi(m,2,base)});}
 /* Densidad: cuántas otras voces había en escena al nacer (v.density). Sola, la voz se adelgaza (pierde notas de palabra);
    acompañada, sus notas suenan más fuerte y se doblan una octava arriba; desde dos, también abajo; desde tres, un colchón. */
 const a=m.density||0,D=Math.min(4,v.density||0);if(a>0){const add=[];out.forEach((ev,k)=>{if(ev.kind!=='note')return;const q=random(piece.seed+':densidad:'+v.key,k);if(D===0){if(k>=w0&&k<w1&&q<a*.5)ev.vel=0;return;}ev.vel*=1+.15*D*a;if(q<a*D/4)add.push({...ev,midi:ev.midi+12,vel:ev.vel*.45});if(D>=2&&q>1-a*(D-1)/3)add.push({...ev,midi:ev.midi-12,vel:ev.vel*.4});});
  if(D>=3)add.push({t:v.born,kind:'note',instr:'pad',midi:midi(m,Math.max(2,vc.octave-1),base),vel:.3*a*vc.gain,dur:Math.min(d,6),pan:vc.pan});for(let k=out.length-1;k>=0;k--)if(out[k].vel===0)out.splice(k,1);out.push(...add);}
 out.push(...said);return out.sort((a,b)=>a.t-b.t);}
/* Sostener: la nota de la voz (una octava abajo), grave y abierta. */
function sustainNote(piece,v){const m=piece.music,vc=m.voices[v.i]||m.voices[0],n=SCALES[m.scale].length,base=Math.floor(random(piece.seed+':musica:'+v.key,'base')*n);return {midi:midi(m,Math.max(2,vc.octave-1),base),vel:.9*vc.gain,pan:vc.pan};}
/* Colchón que se abre (filtro que sube) y gana una quinta y una octava mientras se sostiene; soltar lo apaga con un barrido que baja. */
function sustainVoice(ctx,b,at,ev,live){const env=ctx.createGain(),pan=ctx.createStereoPanner(),lp=ctx.createBiquadFilter(),f=hz(ev.midi),v=Math.max(.0002,ev.vel),nodes=[];pan.pan.value=ev.pan||0;lp.type='lowpass';lp.Q.value=3;lp.frequency.setValueAtTime(450,at);lp.frequency.setTargetAtTime(3600,at+.4,2.5);lp.connect(env);env.connect(pan);pan.connect(b.input);live.add(env);
 [[1,'sawtooth',-6,.33],[1,'sawtooth',6,.33],[1.5,'triangle',0,0],[2,'triangle',3,0]].forEach(([r,type,dt,g0],k)=>{const o=ctx.createOscillator(),g=ctx.createGain();o.type=type;o.frequency.value=f*r;o.detune.value=dt;g.gain.setValueAtTime(g0,at);if(!g0){g.gain.setValueAtTime(0,at+.5+k);g.gain.setTargetAtTime(.28,at+.5+k,1.5);}o.connect(g);g.connect(lp);o.start(at);nodes.push(o);});
 env.gain.setValueAtTime(0,at);env.gain.linearRampToValueAtTime(.09*v,at+.4);env.gain.setTargetAtTime(.2*v,at+.4,3);let done=false;
 return {release(r,E=1){if(done)return;done=true;const g=env.gain;if(g.cancelAndHoldAtTime)g.cancelAndHoldAtTime(r);else g.cancelScheduledValues(r);g.setTargetAtTime(0,r,Math.max(.1,E/4));lp.frequency.cancelScheduledValues(r);lp.frequency.setTargetAtTime(300,r,E/3);nodes.forEach(o=>o.stop(r+E+1));nodes[0].onended=()=>{live.delete(env);try{pan.disconnect();}catch(_){}};
  play(ctx,b,r,{kind:'noise',vel:.35*v,dur:E,from:5000,to:180,pan:ev.pan},live);}};}
/* El pulso sonoro es un patrón tipo Sonic Pi: cuatro pasos por pulso, en tiempo absoluto de la pieza. */
function pulseEvents(piece,from,to){const m=piece.music,bpm=piece.tempo?.bpm,out=[];if(!m.on||!bpm)return out;const step=60/bpm/4,p=m.pulse==='none'?'':String(m.pattern).replace(/[^xo.\-]/gi,'').toLowerCase();
 if(p.length)for(let s=Math.max(0,Math.ceil(from/step));s*step<to;s++){const c=p[s%p.length];if(c==='x'||c==='o')out.push({s,t:s*step,kind:m.pulse,vel:c==='x'?1:.5,pan:0});}
 return m.drums?out.concat(drumEvents(piece,from,to)):out;}
/* Una pista por pieza de la batería; el swing atrasa las semicorcheas pares (la «e» y la «a» de cada pulso). */
function drumEvents(piece,from,to){const m=piece.music,d=m.drums,bpm=piece.tempo?.bpm;if(!m.on||!d||!bpm)return [];const step=60/bpm/4,sw=d.swing*step,out=[];
 for(const k of Object.keys(DRUMS)){const p=String(d[k]||'').replace(/[^xo.\-]/gi,'').toLowerCase();if(!/[xo]/.test(p))continue;
  for(let s=Math.max(0,Math.floor((from-sw)/step));s*step<to;s++){const c=p[s%p.length],t=s*step+(s%2?sw:0);if((c!=='x'&&c!=='o')||t<from||t>=to)continue;
   out.push({s:k+':'+s,t,kind:'bateria',pieza:k,kit:d.kit,tune:d.tune,decay:d.decay,drive:d.drive,vel:(c==='x'?1:.55)*d.gain,pan:DRUM_PAN[k]||0});}}
 return out.sort((a,b)=>a.t-b.t);}
/* Ruido e impulso de reverberación con semilla: el sonido tampoco usa azar libre. */
function seeded(seed){let a=seed>>>0;return ()=>{a=a+0x6D2B79F5>>>0;let t=a;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return ((t^t>>>14)>>>0)/4294967296;};}
function buffers(ctx){const r=seeded(1729),noise=ctx.createBuffer(1,ctx.sampleRate*2,ctx.sampleRate),nd=noise.getChannelData(0);for(let i=0;i<nd.length;i++)nd[i]=r()*2-1;
 const len=Math.floor(ctx.sampleRate*2.4),imp=ctx.createBuffer(2,len,ctx.sampleRate);for(let c=0;c<2;c++){const d=imp.getChannelData(c);for(let i=0;i<len;i++)d[i]=(r()*2-1)*Math.pow(1-i/len,2.6);}return {noise,imp};}
function bus(ctx){const b=buffers(ctx),input=ctx.createGain(),master=ctx.createGain(),comp=ctx.createDynamicsCompressor(),verb=ctx.createConvolver(),verbGain=ctx.createGain(),delay=ctx.createDelay(1.5),fb=ctx.createGain(),tone=ctx.createBiquadFilter(),delayGain=ctx.createGain();
 verb.buffer=b.imp;tone.type='lowpass';tone.frequency.value=2600;
 /* input = lo que tocan los instrumentos; duck lo aparta mientras la música entera habla; post = la mezcla (ahí entra también esa voz, para que no vuelva a entrar como música). */
 const duck=ctx.createGain(),post=ctx.createGain();input.connect(duck);duck.connect(post);post.connect(master);post.connect(verb);verb.connect(verbGain);verbGain.connect(master);post.connect(delay);delay.connect(tone);tone.connect(fb);fb.connect(delay);tone.connect(delayGain);delayGain.connect(master);const hush=ctx.createGain();master.connect(hush);hush.connect(comp);comp.connect(ctx.destination);
 return {input,post,duck:duck.gain,noise:b.noise,hush:hush.gain,set(m){this.m=m;const at=ctx.currentTime;master.gain.setTargetAtTime(m.gain*2.2,at,.02);verbGain.gain.setTargetAtTime(m.reverb*.9,at,.02);delayGain.gain.setTargetAtTime(m.delay*.6,at,.02);fb.gain.setTargetAtTime(m.delay*.55,at,.02);delay.delayTime.setTargetAtTime(m.delayTime,at,.02);}};}
/* Síntesis por evento. Todo se conecta a una envolvente que se registra en `live` para poder callar. */
/* Una nota de muestra: el sonido acelerado o frenado desde su nota raíz (afinado) o tal cual (golpe), con ataque y salida. */
function sampleVoice(ctx,b,at,ev,env,nodes,buf){const s=ev.sample,src=ctx.createBufferSource(),v=Math.max(.0002,ev.vel),rate=s.mode==='afinado'?2**((ev.midi-s.root)/12):1;src.buffer=buf;src.playbackRate.setValueAtTime(rate,at);src.connect(env);nodes.push(src);
 const len=buf.duration/rate,level=.55*v*s.gain,a=Math.min(s.attack,len*.5),hold=s.mode==='afinado'?Math.max(.05,Math.min(len-a,ev.dur||.5)):Math.max(0,len-a-s.release),rel=Math.min(s.release,Math.max(.02,len-a-hold));
 if(a>0)env.gain.linearRampToValueAtTime(level,at+a);else env.gain.setValueAtTime(level,at);env.gain.setValueAtTime(level,at+a+hold);env.gain.linearRampToValueAtTime(0,at+a+hold+rel);return Math.min(len,a+hold+rel)+.02;}
function play(ctx,b,at,ev,live){const sbuf=ev.sample?window.LecturaMuestras?.buffer(ctx,ev.sample.sha):null;if(ev.sample&&!sbuf)return;const env=ctx.createGain(),pan=ctx.createStereoPanner();pan.pan.value=ev.pan||0;env.connect(pan);pan.connect(ev.kind==='speech'&&ev.carrier==='musica'?b.post:b.input);env.gain.setValueAtTime(0,at);live.add(env);
 const nodes=[],osc=(type,f,gain=1,detune=0)=>{const o=ctx.createOscillator(),g=ctx.createGain();o.type=type;o.frequency.setValueAtTime(f,at);o.detune.value=detune;g.gain.value=gain;o.connect(g);nodes.push(o);return {o,g};};
 const shape=(level,attack,decay,hold=0)=>{env.gain.linearRampToValueAtTime(level,at+attack);if(hold)env.gain.setValueAtTime(level,at+attack+hold);env.gain.exponentialRampToValueAtTime(.0001,at+attack+hold+decay);return attack+hold+decay;};
 let end=.5;const f=ev.midi?hz(ev.midi):0,v=Math.max(.0002,ev.vel);
 if(ev.kind==='speech')end=ev.carrier==='instrumento'||ev.carrier==='acorde'||ev.carrier==='musica'?vocode(ctx,b,at,ev,env,nodes):speak(ctx,b,at,ev,env,nodes);
 else if(ev.kind==='note'&&ev.sample)end=sampleVoice(ctx,b,at,ev,env,nodes,sbuf);
 else if(ev.kind==='note'&&ev.recipe)end=recipeVoice(ctx,b,at,ev,env,nodes,osc);
 else if(ev.kind==='note'){
  if(ev.instr==='pluck'){const {g}=osc('sawtooth',f),lp=ctx.createBiquadFilter();lp.type='lowpass';lp.frequency.setValueAtTime(4200,at);lp.frequency.exponentialRampToValueAtTime(Math.max(120,f*2),at+.3);g.connect(lp);lp.connect(env);end=shape(.22*v,.004,Math.max(.4,ev.dur));}
  else if(ev.instr==='kalimba'){osc('sine',f).g.connect(env);const t=osc('sine',f*5.4,.25);t.g.connect(env);t.g.gain.setValueAtTime(.25,at);t.g.gain.exponentialRampToValueAtTime(.001,at+.15);end=shape(.3*v,.002,1.1);}
  else if(ev.instr==='bell'){const c=osc('sine',f),mod=osc('sine',f*3.5,f*2.5);mod.g.gain.setValueAtTime(f*2.5,at);mod.g.gain.exponentialRampToValueAtTime(f*.1,at+1.6);mod.g.connect(c.o.frequency);c.g.connect(env);end=shape(.25*v,.003,2.4);}
  else if(ev.instr==='glass'){osc('sine',f*2).g.connect(env);osc('sine',f*2*2.76,.3).g.connect(env);end=shape(.18*v,.003,1.6);}
  else if(ev.instr==='pad'){const lp=ctx.createBiquadFilter();lp.type='lowpass';lp.frequency.value=1200;lp.connect(env);[-7,0,7].forEach(dt=>osc('sawtooth',f,.33,dt).g.connect(lp));end=shape(.12*v,.5,1.2,Math.max(0,ev.dur-.5));}
  else if(ev.instr==='bass'){osc('sine',f).g.connect(env);const lp=ctx.createBiquadFilter();lp.type='lowpass';lp.frequency.value=400;osc('square',f,.3).g.connect(lp);lp.connect(env);end=shape(.35*v,.005,.6);}
  else if(ev.instr==='drone'){osc('triangle',f).g.connect(env);osc('sine',f*1.5,.5).g.connect(env);end=shape(.14*v,1,1.5,Math.max(0,ev.dur-1));}
  else if(ev.instr==='arpaboca')end=arpaBoca(ctx,b,at,ev,env,nodes);
  else if(ev.instr==='berimbau')end=berimbau(ctx,b,at,ev,env,nodes,osc);
  else if(Object.hasOwn(MALLETS,ev.instr))end=malletVoice(ctx,b,at,ev,env,nodes,osc,MALLETS[ev.instr]);}
 else if(ev.kind==='bateria')end=drumVoice(ctx,b,at,ev,env,nodes,osc);
 else if(ev.kind==='thud'||ev.kind==='drum'){const base=ev.kind==='drum'?45:Math.max(35,f),o=osc('sine',base*3);o.o.frequency.exponentialRampToValueAtTime(base,at+.15);o.g.connect(env);end=shape((ev.kind==='drum'?.5:.45)*v,.003,ev.kind==='drum'?.35:(ev.dur||.35));}
 else{const src=ctx.createBufferSource(),flt=ctx.createBiquadFilter();src.buffer=b.noise;src.loop=true;nodes.push(src);src.connect(flt);flt.connect(env);
  if(ev.kind==='tick'){flt.type='highpass';flt.frequency.value=5000;end=shape(.3*v,.001,.03);}
  else if(ev.kind==='shaker'){flt.type='bandpass';flt.frequency.value=9000;flt.Q.value=2;end=shape(.35*v,.004,.07);}
  else{flt.type='bandpass';flt.Q.value=1.2;flt.frequency.setValueAtTime(ev.from,at);flt.frequency.exponentialRampToValueAtTime(ev.to,at+ev.dur);end=shape(.5*v,.005,ev.dur);}}
 const stop=at+end+.05;nodes.forEach(nd=>{nd.start(at);nd.stop(stop);});nodes[0].onended=()=>{live.delete(env);try{pan.disconnect();}catch(_){}};}
/* Un golpe de batería. Cada pieza es una suma de tonos que caen de altura, ruidos filtrados y (en la 808) bancos de ondas cuadradas;
   el kit cambia alturas, filtros y caídas. La saturación (y el kit frito) pasa todo por una curva tanh antes de la envolvente. */
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
/* Probar la batería: dos compases (o un pulso de 100 si la pieza no tiene tempo). */
function auditionDrums(ctx,piece,bars=2){const m=piece.music;if(!m.drums)return 0;const b=bus(ctx),live=new Set();b.set({...m,on:true});const tempo={...piece.tempo,bpm:piece.tempo?.bpm||100},meter=tempo.meter||4,len=bars*meter*60/tempo.bpm,at=ctx.currentTime+.05;
 drumEvents({...piece,tempo,music:{...m,on:true}},0,len).forEach(ev=>play(ctx,b,at+ev.t,ev,live));return len;}
/* Instrumentos de golpe (idiófonos): barras, lengüetas y lenguas que vibran con sus parciales propios, no con los de una cuerda.
   parts = [razón, nivel, caída (s), ataque (s)]: la barra libre de madera se afina a mano (xilófono 1:3:6, marimba 1:4:10), el bronce no
   (saron), la lengüeta empotrada da 1:6.27:17.5 (kalimba, mbira). dk: las notas agudas se apagan antes. click = la baqueta (ruido en banda);
   buzz = la membrana de la calabaza (balafón, gyil) o las chapitas (mbira): la onda recortada + ruido que sigue a la nota; pair = ombak,
   el gamelán afina cada instrumento en pareja con su gemelo un poco desafinado y el batido es parte del sonido; loose = cents de afinación
   a oído, distintos y fijos para cada nota; shift = la lengüeta arranca alta y baja; body = la caja o el bule que resuena. */
const MALLETS={
 xilofono:{gain:2.7,dk:.6,parts:[[1,1,.5],[3,.5,.16],[6,.18,.06],[9.8,.06,.03]],click:[4200,1.2,.35,.012]},
 xiloelec:{gain:.56,dk:.4,parts:[[1,1,1.5],[3,.55,.5],[6,.2,.15]],click:[3000,1,.18,.01],drive:.55,trem:[6.2,.35],lp:3800},
 marimba:{gain:1.3,dk:.7,parts:[[1,1,1.25],[4,.25,.25],[9.9,.06,.06]],click:[1100,.8,.14,.016]},
 balafon:{gain:2.2,dk:.6,loose:12,parts:[[1,1,.6],[2.9,.35,.16],[5.6,.12,.05]],click:[2500,1,.3,.01],buzz:[.35,1800]},
 gyil:{gain:2.2,dk:.6,loose:20,parts:[[1,1,.45],[3.2,.3,.12],[6.1,.1,.04]],click:[2000,1,.35,.01],buzz:[.75,1200]},
 kalimbacaja:{gain:.9,dk:.4,shift:22,parts:[[1,1,1.8],[6.27,.18,.12],[17.5,.05,.03]],click:[5200,2,.12,.006],body:[320,3,.45]},
 mbira:{gain:.88,dk:.35,shift:15,loose:8,parts:[[1,1,2.2],[5.8,.22,.15],[12,.06,.04]],click:[3800,1.5,.15,.007],buzz:[.5,2600],body:[180,2,.6]},
 vibrafono:{gain:1.05,dk:.5,parts:[[1,1,3.2],[4,.3,.9],[10,.05,.2]],click:[1500,.8,.07,.012],trem:[5.5,.45]},
 saron:{gain:1.04,dk:.3,pair:6,parts:[[1,1,2.6],[2.71,.3,.7],[5.1,.12,.25]],click:[3000,1,.25,.008]},
 gender:{gain:1.17,dk:.4,pair:5,parts:[[1,1,3.5],[3.9,.18,.8],[8.6,.05,.2]],click:[900,.7,.08,.015]},
 teponaztli:{gain:2.35,dk:.5,tongues:true,parts:[[1,1,.5],[.62,.4,.25],[2.3,.3,.12],[3.95,.12,.05]],click:[1800,1,.25,.012]},
 steelpan:{gain:.8,dk:.5,pair:1.2,parts:[[1,1,2.4,.002],[2,.6,1.4,.035],[3,.2,.6,.02],[4.02,.08,.3,.01]],click:[2200,.8,.1,.008]}};
/* Dos notas, como el teponaztli (dos lenguas) o el berimbau (al aire y con la piedra): la tónica y la nota de la escala más cercana a `cerca`
   semitonos arriba (una cuarta, un tono). Toda nota cae en la más cercana. */
function lenguas(m,mid,cerca=5){const s=SCALES[m.scale]||SCALES.pentatonic,iv=s.filter(x=>x>0).reduce((a,x)=>Math.abs(x-cerca)<Math.abs(a-cerca)?x:a,s[1]||cerca),low=midi(m,0,0),d=((Math.round(mid)-low)%12+12)%12;
 const cand=[0,iv,12].reduce((a,x)=>Math.abs(x-d)<Math.abs(a-d)?x:a,0);return Math.round(mid)-d+cand;}
/* Arpa de boca (birimbao, morsing, khomus): la lengüeta suena SIEMPRE la misma nota grave, rica en armónicos; la melodía la hace la boca,
   que es un filtro. Como en Stimmung de Stockhausen: sobre una fundamental fija, la vocal enciende un armónico. Cada nota pide un armónico
   (4–16) de la tónica en la octava 2; la boca toma la vocal (a e i o u) cuyo primer o segundo formante cae más cerca y lo pone exacto
   sobre ese armónico, con resonancia alta; los otros formantes de la vocal quedan suaves. La boca llega deslizándose (el «boing»). */
function arpaBoca(ctx,b,at,ev,env,nodes){const m=b.m||{root:'D',scale:'pentatonic'},v=Math.max(.0002,ev.vel);let dm=midi({...m,scale:m.scale||'pentatonic'},2,0);while(hz(dm)>130)dm-=12;while(hz(dm)<65)dm+=12;
 const f0=hz(dm);let h=Math.round(hz(ev.midi)/f0);while(h>16)h=Math.round(h/2);while(h<4)h*=2;const ft=h*f0;
 const N=64,re=new Float32Array(N),im=new Float32Array(N);for(let n=1;n<N;n++)im[n]=1/Math.pow(n,.55);const o=ctx.createOscillator();o.setPeriodicWave(ctx.createPeriodicWave(re,im));o.frequency.value=f0;nodes.push(o);
 const src=ctx.createGain(),hold=Math.max(.25,ev.dur||.5);o.connect(src);src.gain.setValueAtTime(0,at);src.gain.linearRampToValueAtTime(1,at+.003);src.gain.exponentialRampToValueAtTime(.35,at+.2);src.gain.setTargetAtTime(.0001,at+hold,.25);
 let best=null;for(const vw of 'aeiou')for(const k of [0,1]){const c=Math.abs(Math.log(FORMANT[vw][k]/ft));if(!best||c<best.c)best={c,vw,k};}
 const F=FORMANT[best.vw],from=ft*2**((h%2?.5:-.5));
 F.forEach((fq,k)=>{const bp=ctx.createBiquadFilter(),g=ctx.createGain();bp.type='bandpass';const on=k===best.k;bp.Q.value=on?30:5;g.gain.value=on?5:.35;
  if(on){bp.frequency.setValueAtTime(from,at);bp.frequency.setTargetAtTime(ft,at+.005,.035);}else bp.frequency.value=fq;src.connect(bp);bp.connect(g);g.connect(env);});
 const lp=ctx.createBiquadFilter(),dg=ctx.createGain();lp.type='lowpass';lp.frequency.value=f0*2.5;dg.gain.value=.35;src.connect(lp);lp.connect(dg);dg.connect(env);
 const L=.3*v*4.4,end=hold+1.1;env.gain.setValueAtTime(L,at);env.gain.setValueAtTime(L,at+end-.1);env.gain.exponentialRampToValueAtTime(.0001,at+end);return end;}
/* Berimbau: un alambre en un arco, golpeado con una varita. Dos notas: al aire y con la piedra (dobrão) apretada, que la sube a la nota de la
   escala más cercana a un tono; tocado suave (vel < .35) la piedra apenas roza: «chiado», un zumbido seco. La cabaça se abre contra el vientre
   (filtro que sube, el «uau») y el caxixi suena en cada golpe. El alambre es rígido: sus parciales se estiran (inarmonicidad). */
function berimbau(ctx,b,at,ev,env,nodes,osc){const m=b.m,mid=m?lenguas(m,ev.midi,2):ev.midi,f=hz(mid),v=Math.max(.0002,ev.vel),chiado=ev.vel<.35,ny=ctx.sampleRate*.45,sc=Math.min(1.6,Math.max(.5,Math.pow(130/f,.4)));
 const sum=ctx.createGain();let end=.1;
 for(let n=1;n<=14;n++){const fn=n*f*Math.sqrt(1+.00035*n*n);if(fn>ny)break;const lv=Math.abs(Math.sin(n*Math.PI*.13))/Math.pow(n,.55),d=(chiado?.09:1.7)/(1+.12*n)*sc,{g}=osc('sine',fn,0);
  g.gain.setValueAtTime(0,at);g.gain.linearRampToValueAtTime(lv,at+.002);g.gain.exponentialRampToValueAtTime(.0001,at+.002+d);g.connect(sum);end=Math.max(end,d+.002);}
 const dry=ctx.createGain(),bp=ctx.createBiquadFilter(),wg=ctx.createGain();dry.gain.value=.5;sum.connect(dry);dry.connect(env);
 bp.type='bandpass';bp.Q.value=4;bp.frequency.setValueAtTime(260,at);bp.frequency.exponentialRampToValueAtTime(820,at+.18);wg.gain.value=2.2;sum.connect(bp);bp.connect(wg);wg.connect(env);
 const noise=(fc,q,lv,d,t=0)=>{const s=ctx.createBufferSource(),f2=ctx.createBiquadFilter(),g=ctx.createGain();s.buffer=b.noise;s.loop=true;nodes.push(s);g.gain.value=0;/* sin esto, un golpe con retraso suena a ganancia 1 hasta que llega */f2.type='bandpass';f2.frequency.value=Math.min(ny,fc);f2.Q.value=q;
  s.connect(f2);f2.connect(g);g.connect(env);g.gain.setValueAtTime(0,at+t);g.gain.linearRampToValueAtTime(lv,at+t+.002);g.gain.exponentialRampToValueAtTime(.0001,at+t+.002+d);end=Math.max(end,t+d+.002);};
 noise(2500,1.5,.5,.012);if(chiado)noise(3400,2,.7,.07);noise(7000,1.2,.22,.045);noise(7600,1.2,.12,.035,.11);
 const L=.3*v*1.72;env.gain.setValueAtTime(L,at);env.gain.setValueAtTime(L,at+end);env.gain.exponentialRampToValueAtTime(.0001,at+end+.06);return end+.06;}
function malletVoice(ctx,b,at,ev,env,nodes,osc,S){const mid=S.tongues&&b.m?lenguas(b.m,ev.midi):ev.midi,f=hz(mid),v=Math.max(.0002,ev.vel),sc=Math.min(2.5,Math.max(.3,Math.pow(262/f,S.dk))),ny=ctx.sampleRate*.45;
 const sum=ctx.createGain();let out=sum,end=.05;
 if(S.trem){const tg=ctx.createGain(),lfo=osc('sine',S.trem[0],S.trem[1]/2);tg.gain.value=1-S.trem[1]/2;lfo.g.connect(tg.gain);out.connect(tg);out=tg;}
 if(S.lp){const lp=ctx.createBiquadFilter();lp.type='lowpass';lp.frequency.value=S.lp;out.connect(lp);out=lp;}
 if(S.drive){const ws=ctx.createWaveShaper(),cv=new Float32Array(1024),g=1+S.drive*6;for(let i=0;i<1024;i++){const x=i/511.5-1;cv[i]=Math.tanh(x*g)/Math.tanh(g);}ws.curve=cv;out.connect(ws);out=ws;}
 out.connect(env);
 const cents=S.loose?(Math.abs(Math.sin(mid*12.9898+7.233)*43758.5453)%1*2-1)*S.loose:0;
 S.parts.forEach(([r,g,d,a=.002],k)=>{const ff=f*r*2**((k?cents*1.6:cents)/1200),dd=d*sc;if(ff>ny)return;
  (S.pair?[-S.pair/2,S.pair/2]:[0]).forEach(dh=>{const {o,g:gg}=osc('sine',ff+dh,0);if(S.shift){o.frequency.setValueAtTime((ff+dh)*2**(S.shift/1200),at);o.frequency.exponentialRampToValueAtTime(ff+dh,at+.05);}
   const lv=g/(S.pair?1.6:1);gg.gain.setValueAtTime(0,at);gg.gain.linearRampToValueAtTime(lv,at+a);gg.gain.exponentialRampToValueAtTime(.0001,at+a+dd);gg.connect(sum);});end=Math.max(end,a+dd);});
 const noise=()=>{const s=ctx.createBufferSource();s.buffer=b.noise;s.loop=true;nodes.push(s);return s;};
 if(S.click){const [cf,q,cg,cd]=S.click,bp=ctx.createBiquadFilter(),g=ctx.createGain();bp.type='bandpass';bp.frequency.value=Math.min(ny,cf);bp.Q.value=q;noise().connect(bp);bp.connect(g);g.connect(sum);
  g.gain.setValueAtTime(0,at);g.gain.linearRampToValueAtTime(cg,at+.001);g.gain.exponentialRampToValueAtTime(.0001,at+.001+cd);}
 if(S.buzz){const [amt,hpf]=S.buzz,ws=ctx.createWaveShaper(),cv=new Float32Array(1024),hp=ctx.createBiquadFilter(),g=ctx.createGain(),rect=ctx.createWaveShaper(),rc=new Float32Array(1024),ng=ctx.createGain(),bp=ctx.createBiquadFilter();
  /* La membrana pega contra el borde: arriba de un umbral la onda se recorta a escalones (zumbido nasal); y suena ruido mientras la nota vibra. */
  for(let i=0;i<1024;i++){const x=i/511.5-1;cv[i]=x>.12?1:x<-.3?-.6:0;rc[i]=Math.max(0,Math.abs(x)-.05);}ws.curve=cv;rect.curve=rc;hp.type='highpass';hp.frequency.value=hpf;g.gain.value=amt*1.4;
  sum.connect(ws);ws.connect(hp);hp.connect(g);g.connect(env);
  bp.type='bandpass';bp.frequency.value=hpf*1.8;bp.Q.value=1.4;ng.gain.value=0;noise().connect(bp);bp.connect(ng);sum.connect(rect);rect.connect(ng.gain);const ng2=ctx.createGain();ng2.gain.value=amt*2.5;ng.connect(ng2);ng2.connect(env);}
 if(S.body){const [bf,q,bg]=S.body,bp=ctx.createBiquadFilter(),g=ctx.createGain();bp.type='bandpass';bp.frequency.value=bf;bp.Q.value=q;g.gain.value=bg;sum.connect(bp);bp.connect(g);g.connect(out===sum?env:out);}
 const L=.3*v*S.gain;env.gain.setValueAtTime(L,at);env.gain.setValueAtTime(L,at+end);env.gain.exponentialRampToValueAtTime(.0001,at+end+.08);return end+.08;}
/* Una nota de receta: parciales sumados → filtro (con barrido) → envolvente ADSR; FM y vibrato modulan todas las frecuencias; el aire es ruido filtrado en la nota. */
function recipeVoice(ctx,b,at,ev,env,nodes,osc){const r=ev.recipe,f=hz(ev.midi),v=Math.max(.0002,ev.vel),sum=ctx.createGain();let out=sum;
 if(r.filterType!=='none'){const fl=ctx.createBiquadFilter();fl.type=r.filterType;fl.Q.value=r.filterQ;fl.frequency.setValueAtTime(Math.min(18000,Math.max(30,r.filterFreq*2**r.sweep)),at);fl.frequency.exponentialRampToValueAtTime(r.filterFreq,at+r.attack+r.decay);sum.connect(fl);out=fl;}out.connect(env);
 const oscs=r.partials.map(p=>{const {o,g}=osc(p.wave,f*p.ratio,p.gain/Math.max(1,r.partials.length)*1.4,p.detune);g.connect(sum);return o;});
 if(r.fmIndex>0&&r.fmRatio>0){const mod=osc('sine',f*r.fmRatio,f*r.fmIndex);mod.g.gain.setValueAtTime(f*r.fmIndex,at);mod.g.gain.exponentialRampToValueAtTime(Math.max(.01,f*r.fmIndex*.05),at+r.fmDecay);oscs.forEach(o=>mod.g.connect(o.frequency));}
 if(r.vibDepth>0&&r.vibRate>0){const lfo=osc('sine',r.vibRate,0);lfo.g.gain.setValueAtTime(0,at+r.vibDelay);lfo.g.gain.linearRampToValueAtTime(f*(2**(r.vibDepth/1200)-1),at+r.vibDelay+.3);oscs.forEach(o=>lfo.g.connect(o.frequency));}
 if(r.noise>0){const src=ctx.createBufferSource(),bp=ctx.createBiquadFilter(),g=ctx.createGain();src.buffer=b.noise;src.loop=true;bp.type='bandpass';bp.frequency.value=Math.min(12000,f*2);bp.Q.value=1.2;g.gain.value=r.noise*.6;src.connect(bp);bp.connect(g);g.connect(sum);nodes.push(src);}
 const level=.34*v*r.gain,sus=Math.max(.0001,level*r.sustain),hold=Math.max(0,(ev.dur||.5)-r.attack-r.decay);env.gain.linearRampToValueAtTime(level,at+r.attack);env.gain.linearRampToValueAtTime(sus,at+r.attack+r.decay);env.gain.setValueAtTime(sus,at+r.attack+r.decay+hold);env.gain.exponentialRampToValueAtTime(.0001,at+r.attack+r.decay+hold+r.release);return r.attack+r.decay+hold+r.release;}
/* Probar un instrumento: arpegio de cuatro notas en la escala de la pieza, con su propio bus. */
async function audition(ctx,piece,id){const m=piece.music,b=bus(ctx);b.set({...m,on:true});const recipe=(m.instruments||[]).find(r=>r.id===id),sample=(m.samples||[]).find(s=>s.id===id),live=new Set();if(sample)await window.LecturaMuestras?.prepare(ctx,piece);
 const at=ctx.currentTime+.05;[0,2,4,7].forEach((d,k)=>play(ctx,b,at+k*.3,{kind:'note',instr:id,midi:sample?.mode==='golpe'?sample.root:midi(m,4,d),vel:.8,dur:.7,pan:0,...(recipe?{recipe}:{}),...(sample?{sample}:{})},live));}
/* Una sola nota fuera de línea, sin reverberación ni eco (pruebas y demos de instrumentos). */
async function renderNote(piece,id,mid,seconds=2,sampleRate=22050,vel=.8,seco=false,dur=.7,extra={}){const ctx=new OfflineAudioContext(1,Math.ceil(seconds*sampleRate),sampleRate),b=bus(ctx);b.set({...piece.music,on:true,reverb:0,delay:0});
 /* seco: la voz va directo a la salida, sin el bus (ni compresor): así se compara con la biblioteca de instrumentos muestra por muestra. */
 play(ctx,seco?{...b,input:ctx.destination,post:ctx.destination}:b,0,{kind:'note',instr:id,midi:mid,vel,dur,pan:0,...extra},new Set());return ctx.startRendering();}
/* Programador con anticipación: el reloj de la pieza manda; Web Audio recibe cada evento con su hora exacta. */
function create(ctx){const b=bus(ctx),done=new Set(),live=new Set(),cache=new Map(),held=new Map(),readying=new Set();let played=0;const S=window.LecturaSostener;
 const letGo=()=>{const at=ctx.currentTime;for(const hd of held.values())if(!hd.released)hd.h.release(at,.3);held.clear();};
 return {ctx,schedule(piece,voices,t,cycle,horizon=.25){b.set(piece.music.on?piece.music:{...piece.music,gain:piece.music.gain||.7});const now=ctx.currentTime;
  if(piece.music.samples?.length&&window.LecturaMuestras){const sig=piece.music.samples.map(s=>s.sha).join();if(!readying.has(sig)){readying.add(sig);LecturaMuestras.prepare(ctx,piece);}}
  const run=(id,ev)=>{if(done.has(id)||ev.t<t-.1||ev.t>=t+horizon)return;done.add(id);played++;play(ctx,b,now+Math.max(0,ev.t-t)+.03,ev,live);};
  /* Silencios: sin ataques dentro; «cortar» baja todo en seco al entrar y lo devuelve al salir. */
  const SL=window.LecturaSilencio,keepOf=s=>{let best=null;for(const v of voices)if(v.born<=s.start+1e-9&&(!best||v.born>best.born))best=v;return best?.i;},muted=(ev,i)=>SL&&ev.t>=t-.1&&SL.mutes(piece,ev.t,i,keepOf);
  if(SL)for(const s of SL.list(piece))if(s.release==='cortar'&&s.mode!=='texto'&&s.end>t&&s.start<t+horizon){const key=cycle+':sil:'+s.id;if(done.has(key))continue;done.add(key);b.hush.setTargetAtTime(0,now+Math.max(0,s.start-t),.012);b.hush.setTargetAtTime(1,now+(s.end-t),.04);}
  for(const v of voices){const id=cycle+':'+v.key+':'+v.born.toFixed(3),age=t-v.born;let list=cache.get(id);if(!list){list=events(piece,v);cache.set(id,list);}
   /* Sostenida: los gestos del efecto suenan hasta la mitad (o hasta soltar); luego suena el sostén y, al soltar, el borrado. */
   const cut=S&&S.sustained(v)&&age>=S.TAP?v.born+S.cutoff(v):Infinity;list.forEach((ev,k)=>{if((ev.t<=cut||ev.kind==='speech')&&!muted(ev,v.i))run(id+':'+k,ev);});
   if(S&&v.sus&&piece.music.on){let hd=held.get(id);const r=v.sus.release;if(!hd&&age>=S.TAP&&S.sustained(v)&&(r==null||age<r+.1)){hd={h:sustainVoice(ctx,b,now+.03,sustainNote(piece,v),live),released:false};held.set(id,hd);}
    if(hd&&!hd.released&&r!=null){hd.released=true;hd.h.release(now+Math.max(0,v.born+r-t)+.03,S.erase(v));}}}
  pulseEvents(piece,Math.max(0,t-.1),t+horizon).forEach(ev=>{if(!muted(ev,-9))run(cycle+':p:'+ev.s,ev);});},
 reset(){letGo();done.clear();cache.clear();readying.clear();const at=ctx.currentTime;b.hush.cancelScheduledValues(at);b.hush.setValueAtTime(1,at);},
 stop(){letGo();const at=ctx.currentTime;for(const env of live){try{env.gain.cancelScheduledValues(at);env.gain.setTargetAtTime(0,at,.015);}catch(_){}}live.clear();done.clear();cache.clear();},
 stats:()=>({played,live:live.size,held:[...held.values()].filter(x=>!x.released).length})};}
/* Render fuera de línea (pruebas y, más adelante, exportar audio): mismas funciones, sin reloj en vivo. */
async function render(piece,voices,seconds,sampleRate=22050){const ctx=new OfflineAudioContext(2,Math.ceil(seconds*sampleRate),sampleRate),b=bus(ctx),live=new Set();b.set(piece.music);if(piece.music.samples?.length&&window.LecturaMuestras)await LecturaMuestras.prepare(ctx,piece);
 const S=window.LecturaSostener,SL=window.LecturaSilencio,keepOf=s=>{let best=null;for(const v of voices)if(v.born<=s.start+1e-9&&(!best||v.born>best.born))best=v;return best?.i;},muted=(ev,i)=>SL&&SL.mutes(piece,ev.t,i,keepOf);
 const all=voices.flatMap(v=>{const cut=S&&S.sustained(v)?v.born+S.cutoff(v):Infinity;return events(piece,v).filter(ev=>(ev.t<=cut||ev.kind==='speech')&&!muted(ev,v.i));}).concat(pulseEvents(piece,0,seconds).filter(ev=>!muted(ev,-9)));
 if(SL)for(const s of SL.list(piece))if(s.release==='cortar'&&s.mode!=='texto'&&s.start<seconds){b.hush.setTargetAtTime(0,s.start,.012);b.hush.setTargetAtTime(1,s.end,.04);}for(const ev of all)if(ev.t<seconds)play(ctx,b,Math.max(0,ev.t),ev,live);
 if(S&&piece.music.on)for(const v of voices)if(S.sustained(v)&&v.sus.release!=null&&v.born+S.TAP<seconds){const h=sustainVoice(ctx,b,v.born+S.TAP,sustainNote(piece,v),live);h.release(v.born+v.sus.release,S.erase(v));}
 return ctx.startRendering();}
return {fonemas,speechEvents,melodia,silabas,schema,voiceSchema,voiceSchemaFor,recipeSchema,partialSchema,TEMPLATES,INSTR,SCALES,normalize,events,pulseEvents,midi,wordDegree,create,render,audition,sustainNote,sampleSchema,DRUMS,KITS,drumSchema,RITMOS,drums,drumEvents,auditionDrums,MALLETS,renderNote};
})();
