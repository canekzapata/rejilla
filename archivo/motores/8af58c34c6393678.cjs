// Motores originales, notas con colas y escrituras exclusivas. No toca el banco.
const fs=require('fs'),path=require('path'),D=path.resolve(process.argv[2]);
const P=JSON.parse(fs.readFileSync(path.join(D,'partitura.json'),'utf8')),SR=48000;
const bank=path.join(__dirname,'../objetos/motor');
function write(name,y){
 let peak=0;for(const v of y){if(!Number.isFinite(v))throw Error(name+' no finito');peak=Math.max(peak,Math.abs(v));}
 const b=Buffer.alloc(44+y.length*4);b.write('RIFF');b.writeUInt32LE(36+y.length*4,4);b.write('WAVEfmt ',8);b.writeUInt32LE(16,16);b.writeUInt16LE(3,20);b.writeUInt16LE(1,22);b.writeUInt32LE(SR,24);b.writeUInt32LE(SR*4,28);b.writeUInt16LE(4,32);b.writeUInt16LE(32,34);b.write('data',36);b.writeUInt32LE(y.length*4,40);
 for(let i=0;i<y.length;i++)b.writeFloatLE(y[i],44+i*4);
 fs.writeFileSync(path.join(D,'render',name+'.wav'),b,{flag:'wx'});console.log(name,'pico',peak.toFixed(5));
}
if(process.argv[3]==='sondas'){
 const G=require(path.join(bank,'gong.js')),W=require(path.join(bank,'waterphone.js'));
 write('sonda-gong',G.render({dur:7,semilla:P.semilla,eventos:[{t:.1,tipo:'cruce',m:57,v:.7,abre:4}]},SR));
 write('sonda-waterphone',W.render({dur:7,semilla:P.semilla,eventos:[{t:.1,tipo:'arco',vara:3,dur:3.5,v:.7,agua:.3,ola:.25}]},SR));
}else{
 const mapping={piano:'piano',clarinete:'clarinete',chelo:'cuerda',metal:'metal',agua:'vozagua',bajo:'cuerda',campo:'cuerda',gong:'gong',waterphone:'waterphone'};
 const names=process.argv[3]?process.argv[3].split(','):Object.keys(mapping);
 for(const name of names){
  const motor=require(path.join(bank,mapping[name]+'.js')),y=new Float32Array(Math.ceil(P.duracion*SR));
  console.log('renderizando',name,P.instrumentos[name].length,'eventos');
  for(let k=0;k<P.instrumentos[name].length;k++){
   const e=P.instrumentos[name][k],ev={...e,t:0};
   let tail=['gong','waterphone'].includes(name)?4:name==='piano'?1.6:.45;
   let config={dur:e.dur+tail,semilla:P.semilla+k*97,eventos:[ev]};
   if(name==='piano'){if(e.prep){if(!motor.PREP[e.prep])throw Error('preparación '+e.prep);ev.prep=motor.PREP[e.prep];}}
   if(['chelo','campo','bajo'].includes(name))config.instrumento=name==='bajo'?'contrabajo':'chelo';
   if(name==='metal'){delete config.eventos;config.notas=[ev];config.voz='trombon';config.sordina=e.sordina||'harmon';config.wah=[[0,.1],[e.dur*.5,.95],[e.dur,.3]];}
   if(name==='agua'){
    ev.nota=e.m;ev.texto=e.texto||'a';ev.modo='canto';ev.voz=1;
   }
   const z=motor.render(config,SR),a=Math.round(e.t*SR);
   for(let i=0;i<z.length&&i+a<y.length;i++)y[a+i]+=z[i];
  }
  write(name,y);
 }
 const V=require(path.join(bank,'vozagua.js'));
 if(!process.argv[3])for(const vowel of ['a','i'])write('coda-'+vowel,V.render({dur:12,eventos:[{t:.04,dur:11,texto:vowel.repeat(3),nota:57,modo:'canto',voz:1,v:.7}],semilla:P.semilla},SR));
}
