/* Escenario de «yoshi es un vector 7_nadie_canta» para la biblioteca de instrumentos: las declaraciones que usan sus instrumentos, tal cual,
   sacadas de meleeviewer/output/Arte/2026-09-28_yoshi_es_un_vector_7_nadie_canta/cancion.js (sha256 36dd5aa950ac) por herramientas/escenarios_meleeviewer.cjs.
   Cambios: ctx → el que se dé; master → la salida que se dé (seco). Nombres que no se encontraron: m. */
(function(){'use strict';return async function(__ctx,__salida,opts){opts=opts||{};
/* «nadie canta la canción» (yoshi es un vector, parte 7): trabajar en equipo, entre el azar y la simbiosis.
   Hay una melodía con letra (la canción), pero ningún Pokémon la canta entera: se reparte nota por nota (hoquetus) y la frase sólo
   existe entre todos. κ (kappa) va de 0 = azar (cada quien por su lado: notas corridas de tiempo, de altura, sílabas revueltas,
   huecos) a 1 = simbiosis (se escuchan, se reparten los huecos, la frase se oye completa).
   Papeles: Snorlax el bajo · Chikorita, Venusaur, Cyndaquil cantan · Chansey cubre las notas que faltan (huevo) · Wobbuffet repite
   lo de los demás un tiempo después (contraataque) · Clefairy es el azar (metrónomo) · Electrode la batería, y a la mitad se
   autodestruye. Todo sale de la semilla (la cadena sigue: «eof», el final de la parte 6). Lo usan cancion.js y video.html. */
'use strict';
window.Ecosistema=(()=>{
const BPM=116,SPB=60/BPM,BAR=SPB*4,S16=SPB/4,T0=.35;
const tb=(bar,beat=0)=>T0+(bar*4+beat)*SPB;
function hash(s){let h=1779033703^s.length;for(let i=0;i<s.length;i++){h=Math.imul(h^s.charCodeAt(i),3432918353);h=h<<13|h>>>19;}h=Math.imul(h^h>>>16,2246822507);h=Math.imul(h^h>>>13,3266489909);return (h^h>>>16)>>>0;}
function rng(seed,tag){let a=hash(seed+':'+tag);return ()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}
/* el equipo: rango (MIDI), voz del vocoder (portador, formantes), instrumento y dónde se para en el círculo */
const EQUIPO=[
 {id:'snorlax',nombre:'Snorlax',kind:'Kabigon',papel:'bajo',rango:[28,52],voz:['coro',.8],inst:'bajo'},
 {id:'chikorita',nombre:'Chikorita',kind:'Chicorita',papel:'canta',rango:[59,76],voz:['sierra',1.18],inst:'krar'},
 {id:'venusaur',nombre:'Venusaur',kind:'Fushigibana',papel:'canta',rango:[55,72],voz:['sierra',1.02],inst:'flauta'},
 {id:'cyndaquil',nombre:'Cyndaquil',kind:'Hinoarashi',papel:'canta',rango:[66,86],voz:['pulso',1.34],inst:'cajita'},
 {id:'chansey',nombre:'Chansey',kind:'Lucky',papel:'huevo',rango:[60,84],voz:['sierra',1.26],inst:'vibes'},
 {id:'wobbuffet',nombre:'Wobbuffet',kind:'Sonans',papel:'eco',rango:[48,84],voz:['sierra',.95],inst:'campana'},
 {id:'clefairy',nombre:'Clefairy',kind:'Pippi',papel:'azar',rango:[60,88],voz:['coro',1.3],inst:'metronomo'},
 {id:'electrode',nombre:'Electrode',kind:'Marumine',papel:'bateria',rango:[0,0],voz:['pulso',1.1],inst:'bateria'}];
const CANTORES=['chikorita','venusaur','cyndaquil'];
/* la canción (una sílaba por nota; un compás por renglón; «-» = silencio) */
const PARTITURA=`so:B4:.5 lo:G#4:.5 soy:B4:.5 rui:C#5:.5 do:B4:1 -:1
so:B4:.5 lo:G#4:.5 soy:B4:.5 a:E5:.5 zar:D#5:1 -:1
u:C#5:.5 na:C#5:.5 si:E5:.5 la:C#5:.5 ba:B4:.5 suel:G#4:.5 ta:F#4:1
sin:F#4:.5 na:A4:.5 die:B4:.5 que:C#5:.5 la:D#5:.5 can:F#5:.5 te:E5:1
so:B4:.5 la:G#4:.5 no:B4:.5 se:C#5:.5 o:B4:.5 ye:G#4:.5 -:1
so:B4:.5 la:G#4:.5 no:B4:.5 es:E5:.5 can:D#5:.5 cion:B4:1.5
pe:C#5:.5 ro:C#5:.5 si:E5:.5 tes:C#5:.5 cu:B4:.5 cho:G#4:1.5
tu:F#4:.5 hue:A4:.5 coes:B4:.5 mi:C#5:.5 lu:D#5:.5 gar:E5:1.5
tu:C#5:.5 po:C#5:.5 nes:C#5:.5 lo:B4:.5 que:C#5:.5 me:E5:.5 fal:F#5:.5 ta:E5:.5
-:4
yo:B4:.5 pon:B4:.5 go:B4:.5 lo:A4:.5 que:B4:.5 te:D#5:.5 fal:E5:.5 ta:D#5:.5
-:4
yen:E5:.5 tre:G5:.5 los:G5:.5 dos:E5:2.5
u:D#5:.5 na:F#5:.5 fra:A5:1 se:G#5:2
na:E5:.5 die:E5:.5 can:F#5:.5 ta:G#5:.5 la:A5:.5 can:B5:.5 cion:A5:1
la:G#5:.5 can:F#5:.5 cion:E5:.5 nos:C#5:.5 can:E5:.5 taa:F#5:.5 to:G#5:.5 dos:E5:.5
en:C#5:.5 treel:E5:.5 a:F#5:.5 zar:A5:.5 y:G#5:.5 la:F#5:.5 sim:E5:.5 bio:F#5:.5
sis:G#5:2 -:2
cuan:E5:.5 do:F#5:.5 mees:G#5:.5 cu:A5:.5 chas:B5:1 -:1
sue:B5:.5 no:A5:.5 yo:G#5:3
na:E5:.5 die:F#5:.5 so:G#5:.5 lo:A5:.5 to:B5:.5 dos:C#6:.5 a:B5:.5 la:A5:.5
vez:G#5:3 -:1
si:G#4:.5 fal:B4:.5 tau:C#5:.5 no:B4:1 -:1.5
can:C#5:.5 ta:E5:.5 mos:C#5:.5 por:B4:.5 el:G#4:2
el:A4:.5 hue:B4:.5 co:C#5:.5 tam:E5:.5 bien:F#5:1 -:1
can:G#5:1 ta:E5:3
na:E5:.5 die:E5:.5 can:F#5:.5 ta:G#5:.5 la:A5:.5 can:B5:.5 cion:A5:1
la:G#5:.5 can:F#5:.5 cion:E5:.5 nos:C#5:.5 can:E5:.5 taa:F#5:.5 to:G#5:.5 dos:E5:.5
e:E5:1 qui:F#5:1 po:G#5:2
-:4`;
const MOSTRAR={cion:'ción',coes:'co es',tes:'te es',yen:'y en',treel:'tre el',mees:'me es',taa:'ta a',tau:'ta u',el:'él',rui:'rui',si:'sí',tu:'tú'};
const CH=[['Emaj7'],['C#m9'],['Amaj7'],['B7sus','B7'],['Emaj7'],['C#m9'],['Amaj7'],['B7sus','B7'],
 ['F#m9','G#m7'],['Amaj7','A#dim7'],['F#m9','G#m7'],['Amaj7','A#dim7'],['Cmaj7'],['B7sus','B7b9'],
 ['Amaj7','B7'],['G#m7','C#m7'],['F#m7','B7'],['Emaj7','E7'],['Amaj7','B/A'],['G#m7','C#7'],['F#m7','B7'],['E6'],
 ['C#m9'],['Amaj7'],['F#m7','B7'],['Emaj7'],['Amaj7','B7'],['G#m7','C#m7'],['F#m7','B7'],['Emaj9'],['Emaj9']];
/* κ por compás: azar, acoplamiento, simbiosis, autodestrucción (κ sigue en 1: falta Electrode), todos, y se disuelve */
const KAPPA=b=>b<6?0:b<14?(b-5)/8:b<30?1:.15;
const TRAMOS=[{id:'azar',de:0,a:6,jp:'偶然'},{id:'acoplamiento',de:6,a:14,jp:'結合'},{id:'simbiosis',de:14,a:22,jp:'共生'},{id:'autodestrucción',de:22,a:26,jp:'自爆'},{id:'equipo',de:26,a:30,jp:'仲間'},{id:'fin',de:30,a:31,jp:'解散'}];
const NOTE={C:0,D:2,E:4,F:5,G:7,A:9,B:11},nm=s=>{const m=/^([A-G])(b|#)?(-?\d)$/.exec(s);return 12*(+m[3]+1)+NOTE[m[1]]+(m[2]==='b'?-1:m[2]==='#'?1:0);};
const ESCALA=[4,6,8,9,11,1,3];/* mi mayor */
function componer(seed='eof'){
 const R=k=>rng(seed,k),r=R('azar'),rp=R('reparto'),re=R('eco'),rm=R('metronomo'),rb=R('bateria'),rj=R('bajo');
 /* la melodía objetivo */
 const objetivo=[];PARTITURA.trim().split('\n').forEach((line,bar)=>{let beat=0;for(const tok of line.trim().split(/\s+/)){const [s,n,d]=tok.split(':');if(s==='-'){beat+=+d;continue;}objetivo.push({bar,beat,t:tb(bar,beat),dur:+d*SPB,midi:nm(n),syl:s});beat+=+d;}});
 objetivo.forEach((n,i)=>n.i=i);
 const SYLS=objetivo.map(n=>n.syl),enRango=(p,m)=>{const P=EQUIPO.find(e=>e.id===p);return m>=P.rango[0]&&m<=P.rango[1];};
 const cuenta={},eventos=[],aristas=[],met=[];const push=e=>eventos.push({vel:1,...e});
 let prev=null;const EXPLOTA=22,REGRESA=24;
 /* el reparto: cada nota a quien no cantó la anterior y lleva menos notas (turnos justos); el azar la corre, la cambia o la pierde */
 for(const n of objetivo){const k=KAPPA(n.bar),cands=CANTORES.filter(p=>enRango(p,n.midi)&&p!==prev);const pool=cands.length?cands:CANTORES.filter(p=>p!==prev);
  pool.sort((a,b)=>(cuenta[a]||0)-(cuenta[b]||0)||(hash(seed+a+n.i)%7)-(hash(seed+b+n.i)%7));const quien=pool[0];
  const aturde=n.bar===EXPLOTA?.55:n.bar===EXPLOTA+1?.35:n.bar===EXPLOTA+2?.12:0,pierde=r()<(1-k)*.35+aturde,corre=(1-k),t=n.t+(r()-.5)*corre*SPB*2.5,alt=r()<(1-k)*.8,sylR=r()<(1-k)*.75;
  if(!pierde){cuenta[quien]=(cuenta[quien]||0)+1;const P=EQUIPO.find(e=>e.id===quien);let midi=n.midi;if(alt){const deg=Math.floor(r()*7),oct=Math.floor(P.rango[0]/12)+Math.floor(r()*2);midi=12*oct+ESCALA[deg];while(midi<P.rango[0])midi+=12;while(midi>P.rango[1])midi-=12;}
   const bien=Math.abs(t-n.t)<S16*.6&&midi===n.midi;push({tipo:'melodia',poke:quien,t,dur:n.dur*(alt?.8:1),midi,syl:sylR?SYLS[Math.floor(r()*SYLS.length)]:n.syl,bar:n.bar,i:n.i,bien});prev=quien;}
  else{/* Chansey pone el huevo: cubre la nota perdida, un dieciseisavo tarde, si el equipo ya se escucha */
   if(r()<k*.95+.05&&k>.2){push({tipo:'huevo',poke:'chansey',t:n.t+S16,dur:n.dur-S16*.5,midi:n.midi,syl:n.syl,bar:n.bar,i:n.i,bien:true,cubre:true});prev='chansey';}else prev=null;}}
 /* con Electrode fuera (22-23), sus golpes no suenan; los huecos de la melodía que caen en su turno los cubre Chansey */
 /* Wobbuffet: repite (sin letra) lo que tocaron otros, un tiempo después */
 for(const e of eventos.slice()){if(e.poke==='chansey'&&e.tipo==='huevo')continue;const k=KAPPA(e.bar);if(re()<.18+.3*k)push({tipo:'eco',poke:'wobbuffet',t:e.t+SPB,dur:Math.min(e.dur,SPB),midi:e.midi-(e.midi>80?12:0),de:e.poke,bar:e.bar,vel:.55});}
 /* Clefairy: metrónomo = azar. Más mientras menos se escuchan; nunca desaparece del todo */
 for(let b=0;b<31;b++){const k=KAPPA(b),n=Math.round((1-k)*6+.8+rm());for(let j=0;j<n;j++){const t=tb(b,Math.floor(rm()*16)/4),inst=EQUIPO[Math.floor(rm()*6)+1].inst,midi=60+Math.floor(rm()*26);
  push({tipo:'metronomo',poke:'clefairy',t,dur:SPB*(.25+rm()*.75),midi,inst,syl:rm()<.35?SYLS[Math.floor(rm()*SYLS.length)]:null,bar:b,vel:.6+(1-k)*.3});}}
 /* Snorlax: el bajo; en el azar despierta cuando quiere, en la simbiosis marca la fundamental y la quinta */
 const PC={C:0,'C#':1,Db:1,D:2,'D#':3,Eb:3,E:4,F:5,'F#':6,Gb:6,G:7,'G#':8,Ab:8,A:9,'A#':10,Bb:10,B:11};const raiz=s=>{const m=/^([A-G][b#]?)(?:.*?)(?:\/([A-G][b#]?))?$/.exec(s);return PC[m[2]||m[1]];};
 for(let b=0;b<31;b++){const k=KAPPA(b),cs=CH[b];for(let s=0;s<16;s+=2){const c=cs.length>1&&s>=8?cs[1]:cs[0],root=28+((raiz(c)-4+12)%12),tgt=s===0?root:s===8?root+(cs.length>1?0:7):s===14?root+12:null,azar=rj()<(1-k)*.25;
  if((tgt!=null&&rj()<.35+.65*k)||azar)push({tipo:'bajo',poke:'snorlax',t:tb(b,s/4),dur:SPB*(tgt!=null?1.6:.8),midi:azar?root+[0,7,12,3][Math.floor(rj()*4)]:tgt,bar:b,vel:.8});}}
 /* Electrode: la batería de consola; en el azar golpes sueltos, con κ se acomoda al groove; explota en el 22, regresa en el 24 */
 const GROOVE={kick:'x.....x...x.....',snare:'....x.......x...',hat:'x.x.x.x.x.x.x.x.',openhat:'..............x.',rim:'..........o.....'};const bateria=[];
 for(let b=0;b<31;b++){if(b>=EXPLOTA&&b<REGRESA)continue;const k=b>=REGRESA&&b<26?(b-REGRESA+1)/2*KAPPA(b):KAPPA(b),d={kit:'acustico',gain:.5+.2*k};
  for(const [p,g] of Object.entries(GROOVE))d[p]=g.split('').map(c=>rb()<k?c:(rb()<.12?(rb()<.5?'x':'o'):'.')).join('');if(b===14||b===26)d.spray='x...............';if(b===30)for(const p in GROOVE)d[p]='';bateria.push({bar:b,drums:d});}
 push({tipo:'explosion',poke:'electrode',t:tb(EXPLOTA),dur:1.2,bar:EXPLOTA,midi:28});push({tipo:'pokebola',poke:'electrode',t:tb(REGRESA)-SPB,dur:SPB,bar:REGRESA-1,midi:84});
 eventos.sort((a,b)=>a.t-b.t);
 /* medidas por compás: coherencia (notas de la canción que sí sonaron a tiempo y a su altura) y quién se pasó la frase con quién */
 for(let b=0;b<31;b++){const obj=objetivo.filter(n=>n.bar===b),ok=obj.filter(n=>eventos.some(e=>e.i===n.i&&e.bien));const ar={};
  const mel=eventos.filter(e=>e.bar===b&&(e.tipo==='melodia'||e.tipo==='huevo')).sort((x,y)=>x.i-y.i);for(let i=1;i<mel.length;i++)if(mel[i].i===mel[i-1].i+1&&mel[i].poke!==mel[i-1].poke){const key=[mel[i-1].poke,mel[i].poke].sort().join('|');ar[key]=(ar[key]||0)+1;}
  eventos.filter(e=>e.bar===b&&e.tipo==='eco').forEach(e=>{const key=[e.de,'wobbuffet'].sort().join('|');ar[key]=(ar[key]||0)+.3;});
  met.push({bar:b,kappa:KAPPA(b),coherencia:obj.length?ok.length/obj.length:null,aristas:ar});}
 const tramo=t=>{const b=Math.floor((t-T0)/BAR);return TRAMOS.find(x=>b>=x.de&&b<x.a)||(b<0?TRAMOS[0]:TRAMOS.at(-1));};
 const coh=met.filter(m=>m.coherencia!=null);
 return {seed,BPM,SPB,BAR,S16,T0,tb,EQUIPO,CH,TRAMOS,KAPPA,objetivo,eventos,bateria,met,tramo,MOSTRAR,EXPLOTA,REGRESA,LEN:tb(31)+2.5,
  medidas:{coherenciaAzar:+(coh.filter(m=>m.kappa===0).reduce((s,m)=>s+m.coherencia,0)/coh.filter(m=>m.kappa===0).length).toFixed(2),coherenciaSimbiosis:+(coh.filter(m=>m.kappa===1).reduce((s,m)=>s+m.coherencia,0)/coh.filter(m=>m.kappa===1).length).toFixed(2),
   porPokemon:Object.fromEntries(EQUIPO.map(p=>[p.id,eventos.filter(e=>e.poke===p.id).length])),huevos:eventos.filter(e=>e.tipo==='huevo').length,ecos:eventos.filter(e=>e.tipo==='eco').length}};}
return {componer,EQUIPO};})();

const E=Ecosistema.componer(opts.seed||'eof');
const SR=44100;
const hz=n=>440*2**((n-69)/12);
function hash(s){let h=1779033703^s.length;for(let i=0;i<s.length;i++){h=Math.imul(h^s.charCodeAt(i),3432918353);h=h<<13|h>>>19;}h=Math.imul(h^h>>>16,2246822507);h=Math.imul(h^h>>>13,3266489909);return (h^h>>>16)>>>0;}
function rng(tag){let a=hash(E.seed+':'+tag);return ()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}
const ctx=__ctx;
const H=rng('humano');
const instB=ctx.createGain();
const drumB=ctx.createGain();
instB.gain.value=opts.inst??1;
drumB.gain.value=opts.drums??1;
const pan=(p,to)=>{const s=ctx.createStereoPanner();s.pan.value=Math.max(-1,Math.min(1,p));s.connect(to);return s;};
const env=(g,t,a,peak,dec,sus=0.0001,tail=.05,end)=>{g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(peak,t+a);g.gain.setTargetAtTime(Math.max(sus,.0001),t+a,dec);if(end!=null)g.gain.setTargetAtTime(0,end,tail);};
const nb=ctx.createBuffer(1,SR*2,SR);
const nr=rng('ruido');
{const d=nb.getChannelData(0);for(let k=0;k<d.length;k++)d[k]=nr()*2-1;};
function noise(t,dur,rate=1){const s=ctx.createBufferSource();s.buffer=nb;s.loop=true;s.playbackRate.value=rate;s.start(t,H()*1.5);s.stop(t+dur);return s;}
/* explosión (autodestrucción) y pokébola */
function explota(t){const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.setValueAtTime(90,t);o.frequency.exponentialRampToValueAtTime(28,t+.6);env(g,t,.003,.38,.35);o.connect(g);g.connect(drumB);o.start(t);o.stop(t+1.6);
 const n=noise(t,1.6,.6),lp=ctx.createBiquadFilter(),ng=ctx.createGain();lp.type='lowpass';lp.frequency.setValueAtTime(6000,t);lp.frequency.exponentialRampToValueAtTime(300,t+1.2);env(ng,t,.002,.28,.4);n.connect(lp);lp.connect(ng);ng.connect(drumB);}
function pokebola(t){[[88,0],[95,.09]].forEach(([m,d])=>{const o=ctx.createOscillator(),g=ctx.createGain();o.type='square';o.frequency.value=hz(m);env(g,t+d,.002,.05,.1);o.connect(g);g.connect(pan(.3,instB));o.start(t+d);o.stop(t+d+.4);});const n=noise(t+.2,.15,1.4),bp=ctx.createBiquadFilter(),g=ctx.createGain();bp.type='bandpass';bp.frequency.value=2500;env(g,t+.2,.002,.3,.03);n.connect(bp);bp.connect(g);g.connect(drumB);}
instB.connect(__salida);  /* bus sin salida en el escenario */
drumB.connect(__salida);  /* bus sin salida en el escenario */
return {explota,pokebola};
};})()