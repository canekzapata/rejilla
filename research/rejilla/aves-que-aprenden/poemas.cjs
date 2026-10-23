// Siringua: dos poemas completos, fonética inglesa escrita para este repertorio.
// No modifica los instrumentos históricos. Las ejecuciones y cada archivo son exclusivos.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),vm=require('vm');
const BASE=__dirname,ORIG=path.join(BASE,'../objetos'),SR=24000,SEED=181026;
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
function loadVariant(program){let s={module:{exports:{}},require:p=>require(path.resolve(ORIG,'motor',p))};vm.runInNewContext(program,s);return s.module.exports;}
const pSource=fs.readFileSync(path.join(ORIG,'motor/pajaro.js'),'utf8');
const P=require(path.join(ORIG,'motor/pajaro.js'));
const rawSource=pSource.replace('s += out * (k ? .8 : 1);','s += src * (k ? .8 : 1);');
if(rawSource===pSource)throw Error('Revisar cambio en el pájaro original');
const Raw=loadVariant(rawSource);
const vOriginal=fs.readFileSync(path.join(ORIG,'motor/vozagua.js'),'utf8');
// Valores de diseño para esta voz artificial; no mediciones de una persona o especie.
const englishFormants={AA:[730,1090,2440],AE:[660,1720,2410],AH:[520,1300,2500],AO:[570,840,2410],EH:[530,1840,2480],ER:[490,1350,1690],IH:[390,1990,2550],IY:[270,2290,3010],UH:[440,1020,2240],UW:[300,870,2240]};
let vSource=vOriginal.replace('var CLASE = function (f) {',`Object.assign(FORMANTES,${JSON.stringify(englishFormants)});\n  var CLASE = function (f) {`)
 .replace("if ('sfx'.indexOf(f) >= 0)","if (['s','f','x','SH','TH','DH','HH','v','z','ZH'].includes(f))")
 .replace("if ('mnN'.indexOf(f) >= 0)","if (['m','n','N','NG'].includes(f))")
 .replace("if (f === 'R') return 'trino';","if (['ENR','w','Y'].includes(f)) return 'liquida'; if (f === 'R') return 'trino';")
 .replace('var fon = G2P.frase(ev.texto).filter','var fon = (ev.fonemas || G2P.frase(ev.texto)).filter')
 .replace("if (CLASE(f) === 'vocal') nv++;","if (CLASE(f) === 'vocal') nv += (ev.pesos && ev.pesos[fon.indexOf(f)]) || 1;")
 .replace("cl === 'vocal' ? dv : DUR[cl]","cl === 'vocal' ? dv * ((ev.pesos && ev.pesos[i]) || 1) : DUR[cl]")
 .replace('var BANDA = {',"var BANDA = { SH: [2200, 6500], TH: [1800, 6200], DH: [1000, 4800], HH: [800, 5000], v: [1000, 4200], z: [3500, 7500], ZH: [1800, 5500],")
 .replace("s.clase === 'nasal' ? [280, 1200, 2400] : s.sig","s.clase === 'nasal' ? [280, 1200, 2400] : s.f === 'ENR' ? [350, 1100, 1650] : s.f === 'w' ? [300, 750, 2200] : s.f === 'Y' ? [300, 2200, 2900] : s.sig");
const V=loadVariant(vSource),G=require(path.join(ORIG,'vendor/difonos-g2p/g2p.js'));
// Léxico cerrado para el poema, transcripción compositiva aproximada. No lector de inglés general.
const EN={
 ee:'IY',eye:'AA IH',the:'DH AH',opens:'OW p AH n z',i:'AA IH',wire:'w AA IH ENR',asks:'AE s k s',for:'f AO ENR',a:'AH',name:'n EH IH m',
 all:'AO l',those:'DH OW z',in:'IH n',favour:'f EH IH v ER',aye:'AA IH',thousand:'TH AW z AH n d',little:'l IH t AH l',eyes:'AA IH z',
 approve:'AH p ENR UW v',morning:'m AO ENR n IH NG',click:'k l IH k',seed:'s IY d',enters:'EH n t ER z',circuit:'s ER k IH t',grows:'g ENR OW z',
 throat:'TH ENR OW t',whose:'HH UW z',words:'w ER d z',are:'AA ENR',these:'DH IY z',our:'AW ER',hour:'AW ER',air:'EH ENR',feather:'f EH DH ER',
 holds:'HH OW l d z',sentence:'s EH n t AH n s',open:'OW p AH n'};
const dip={OW:['AO','UW'],AW:['AA','UH']};
function enWord(w){if(!EN[w])throw Error('Palabra inglesa sin partitura: '+w);return EN[w].split(' ').flatMap(x=>dip[x]||[x]);}
const poems=[
 {slug:'la-republica-del-pico',title:'La república del pico',lang:'es-MX',lines:[
 'pi','pi pío','pío','pido','pido piso','piso de aire','aire de nadie',
 'trrránsito','trrranvía','trrráiganme una rama','para interrumpir la avenida',
 'ciu','dad','ciu','dad','se cayó la ciudad de mi boca','quedó','aquí','a quí','a quí','aquí cabe otro pájaro','pi']},
 {slug:'a-small-parliament-of-wires',title:'A small parliament of wires',lang:'en-US',lines:[
 'ee','ee eye','the eye opens','I','the wire asks for a name','I','I','I','all those in favour','aye aye aye',
 'a thousand little eyes','approve the morning','click','a seed enters the circuit','click','the circuit grows a throat',
 'whose words are these','our','hour','air','ee','a feather','holds the sentence','open']}
];
function wav(dest,y){let b=Buffer.alloc(44+y.length*4);b.write('RIFF');b.writeUInt32LE(b.length-8,4);b.write('WAVEfmt ',8);b.writeUInt32LE(16,16);b.writeUInt16LE(3,20);b.writeUInt16LE(1,22);b.writeUInt32LE(SR,24);b.writeUInt32LE(SR*4,28);b.writeUInt16LE(4,32);b.writeUInt16LE(32,34);b.write('data',36);b.writeUInt32LE(y.length*4,40);for(let i=0;i<y.length;i++){if(!Number.isFinite(y[i]))throw Error('Audio no finito');b.writeFloatLE(y[i],44+i*4);}fs.writeFileSync(dest,b,{flag:'wx'});}
const nonce=crypto.randomBytes(24).toString('hex'),version=fs.readFileSync(__filename),runHash=hash(Buffer.concat([version,Buffer.from(vSource),Buffer.from(rawSource),Buffer.from(nonce)])),id=runHash.slice(0,12),tag=`s${SEED}-${id}`;
const out=path.join(BASE,`siringua-dos-poemas-${tag}`);fs.mkdirSync(out);fs.mkdirSync(path.join(out,'fuentes'));fs.mkdirSync(path.join(out,'proceso'));
function write(name,data){fs.writeFileSync(path.join(out,name),data,{flag:'wx'});}
write('fuentes/poemas.cjs',version);write('fuentes/vozagua-bilingue.js',vSource);write('fuentes/pajaro-sin-pico.js',rawSource);write('fuentes/pajaro-original.js',pSource);
for(const p of ['motor/agua.js','motor/vozagua.js','vendor/difonos-g2p/g2p.js']){const dest=path.join(out,'fuentes/originales',p);fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,fs.readFileSync(path.join(ORIG,p)),{flag:'wx'});}
let recipe={version:'siringua-poemas-0.2',hash:runHash,id,nonce,semilla:SEED,sr:SR,tag,ingles:'léxico fonético cerrado, escrito para este poema; aproximaciones formánticas',englishFormants,lexico:EN,poemas:[]};
for(const [pi,poem] of poems.entries()){
 let t=.6,events=[],birdEvents=[],carrierEvents=[],score=[];
 const motif=pi===0?[57,60,62,59,64,60,57]:[59,62,60,65,63,59];
 for(let li=0;li<poem.lines.length;li++){
   const line=poem.lines[li],words=line.toLowerCase().split(/\s+/),start=t;
   for(let wi=0;wi<words.length;wi++){
    const texto=words[wi];let fon=poem.lang==='en-US'?enWord(texto):G.palabra(texto);
    let nV=fon.filter(f=>V.FORMANTES[f]).length,nC=fon.length-nV;
    let d=Math.max(.27,nV*(li<3?.19:.135)+nC*.075);
    // Claves sostenidas y fragmentación concreta: aquí/I/eye/aye no se recitan a la misma velocidad.
    if(['aquí','pío','eye','i','aye','our','hour','air','open'].includes(texto))d*=1.4;
    const note=motif[(li+wi)%motif.length]+(li>17?2:0),clarity=li<3?.1:li<7?.5:li<17?.8:.9;
    const e={t,dur:d,texto,fonemas:fon,nota:note,modo:li===0?'susurro':'canto',voz:1,v:.7,clarity,line:li};
    events.push(e);
    const high=note+27;
    // La segunda fuente responde después de cada palabra, no duplica todo el texto.
    birdEvents.push({t,dur:d*.82,m:high,m2:high+[3,-2,5,-4][(li+wi)%4],tipo:li%5===0?'gorjeo':'silbido',rate:16,prof:2.4,voz:0,v:.48});
    birdEvents.push({t:t+d*.62,dur:Math.min(.42,d*.6+.06),m:high+7.3,m2:high+2,tipo:'silbido',voz:1,v:.35});
    carrierEvents.push({t,dur:d,m:note,tipo:'ronco',voz:0,v:.74});
    carrierEvents.push({t,dur:d,m:note+[7,4,10.5][li%3],tipo:'ronco',voz:1,v:.52});
    t+=d+.075;
   }
   const pause=['click','quedó','aquí','open'].includes(line.toLowerCase())?.75:.32+(li%3)*.1;
   score.push({line:li,text:line,t:start,fin:t,pause});t+=pause;
 }
 const dur=t+.9,n=Math.ceil(dur*SR),water=new Float32Array(n),segments=[];
 // Render por palabra: evita que un poema largo multiplique memoria de las burbujas.
 for(const [ei,e] of events.entries()){
  const local={...e,t:0};const actual=V.segmentos(local),end=Math.max(e.dur,...actual.map(s=>s.t1));
  if(end>e.dur+.002)throw Error('Duración fonética excedida: '+e.texto);
  const y=V.render({dur:e.dur+.09,eventos:[local],semilla:SEED+ei+pi*1000},SR),at=Math.round(e.t*SR);
  for(let j=0;j<y.length&&at+j<n;j++)water[at+j]+=y[j];
  segments.push(...V.segmentos(e));
 }
 const bird=P.render({dur,eventos:birdEvents,semilla:SEED+pi},SR),carrier=Raw.render({dur,eventos:carrierEvents,semilla:SEED+pi},SR);
 wav(path.join(out,`${poem.slug}-agua-${tag}.wav`),water);wav(path.join(out,`${poem.slug}-aves-${tag}.wav`),bird);wav(path.join(out,`${poem.slug}-siringe-${tag}.wav`),carrier);
 const data={...poem,dur,eventos:events,aves:birdEvents,siringe:carrierEvents,segmentos:segments,score};recipe.poemas.push(data);
 write(`${poem.slug}-partitura-${tag}.json`,JSON.stringify(data,null,2));write(`${poem.slug}-${tag}.txt`,poem.title+'\n\n'+poem.lines.join('\n')+'\n');
 console.log(`${poem.slug}: ${dur.toFixed(2)} s, ${events.length} palabras`);
}
write(`receta-${tag}.json`,JSON.stringify(recipe,null,2));console.log(out);
