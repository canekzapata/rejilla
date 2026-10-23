// Coral: todos los cuerpos proceden del banco original.
const fs=require('fs'),path=require('path'),D=path.resolve(process.argv[2]),SR=48000;
const P=JSON.parse(fs.readFileSync(path.join(D,'partitura.json'),'utf8')),bank=path.resolve(__dirname,'../objetos/motor');
const models={cuerda:require(path.join(bank,'cuerda.js')),clarinete:require(path.join(bank,'clarinete.js')),metal:require(path.join(bank,'metal.js')),gong:require(path.join(bank,'gong.js'))};
function wav(file,y){
 const b=Buffer.alloc(44+y.length*4);b.write('RIFF');b.writeUInt32LE(36+y.length*4,4);b.write('WAVEfmt ',8);b.writeUInt32LE(16,16);b.writeUInt16LE(3,20);b.writeUInt16LE(1,22);b.writeUInt32LE(SR,24);b.writeUInt32LE(SR*4,28);b.writeUInt16LE(4,32);b.writeUInt16LE(32,34);b.write('data',36);b.writeUInt32LE(y.length*4,40);
 for(let i=0;i<y.length;i++){if(!Number.isFinite(y[i]))throw Error(file+' no finito');b.writeFloatLE(y[i],44+i*4);}
 fs.writeFileSync(file,b,{flag:'wx'});
}
function note(name,e){
 const ev={...e,t:0},config={dur:e.dur+(name==='gong'?6:1.3),semilla:P.semilla,eventos:[ev]};
 if(name==='metal'){delete config.eventos;config.notas=[ev];config.voz='trombon';config.sordina=e.sordina||'cup';return models.metal.render(config,SR);}
 if(name==='gong')return models.gong.render(config,SR);
 if(name==='clarinete')return models.clarinete.render(config,SR);
 config.instrumento={violin:'violin',viola:'viola',chelo:'chelo',bajo:'contrabajo'}[name];return models.cuerda.render(config,SR);
}
if(process.argv[3]==='sondas'){
 for(const [name,m,tipo] of [['violin',69,'arco'],['viola',61,'tasto'],['chelo',45,'arco'],['bajo',45,'arco'],['metal',52,'normal'],['metal',57,'normal'],['clarinete',57,'normal']])wav(path.join(D,'render',`sonda-${name}-${m}.wav`),note(name,{m,tipo,dur:3,v:.6}));
 console.log('Siete sondas terminadas');
}else{
 for(const [name,events] of Object.entries(P.instrumentos)){
  console.log(name,events.length,'notas');for(const e of events)wav(path.join(D,'render',e.id+'.wav'),note(name,e));
 }
 console.log('Notas originales terminadas');
}
