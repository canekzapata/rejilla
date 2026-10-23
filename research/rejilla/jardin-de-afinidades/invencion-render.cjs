// Invención: banco físico original, archivos por nota y sondas independientes.
const fs=require('fs'),path=require('path'),D=path.resolve(process.argv[2]),SR=48000;
const P=JSON.parse(fs.readFileSync(path.join(D,'partitura.json'),'utf8')),bank=path.resolve(__dirname,'../objetos/motor');
const models={viola:require(path.join(bank,'cuerda.js')),clarinete:require(path.join(bank,'clarinete.js')),bajo:require(path.join(bank,'cuerda.js')),piano:require(path.join(bank,'piano.js'))};
function wav(file,y){
 const b=Buffer.alloc(44+y.length*4);b.write('RIFF');b.writeUInt32LE(36+y.length*4,4);b.write('WAVEfmt ',8);b.writeUInt32LE(16,16);b.writeUInt16LE(3,20);b.writeUInt16LE(1,22);b.writeUInt32LE(SR,24);b.writeUInt32LE(SR*4,28);b.writeUInt16LE(4,32);b.writeUInt16LE(32,34);b.write('data',36);b.writeUInt32LE(y.length*4,40);
 for(let i=0;i<y.length;i++){if(!Number.isFinite(y[i]))throw Error(file+' no finito');b.writeFloatLE(y[i],44+i*4);}
 fs.writeFileSync(file,b,{flag:'wx'});
}
function note(name,e){
 const ev={...e,t:0};if(name==='piano')ev.prep=models.piano.PREP.goma;
 return models[name].render({dur:e.dur+1.3,instrumento:name==='bajo'?'contrabajo':'viola',semilla:P.semilla,eventos:[ev]},SR);
}
if(process.argv[3]==='sondas'){
 for(const [name,m,tipo] of [['viola',57,'arco'],['viola',64,'arco'],['clarinete',57,'normal'],['clarinete',55,'normal'],['bajo',45,'pizz'],['bajo',41,'pizz']])wav(path.join(D,'render',`sonda-${name}-${m}.wav`),note(name,{m,tipo,dur:3,v:.6}));
 console.log('Seis sondas terminadas');
}else{
 for(const [name,events] of Object.entries(P.instrumentos)){
  console.log(name,events.length,'notas');
  for(const e of events)wav(path.join(D,'render',e.id+'.wav'),note(name,e));
 }
 console.log('Notas originales terminadas');
}
