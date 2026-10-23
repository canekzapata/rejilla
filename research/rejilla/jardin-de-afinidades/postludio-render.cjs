// V: instrumentos físicos originales; el último piano se conserva sin espacio añadido.
const fs=require('fs'),path=require('path'),D=path.resolve(process.argv[2]),SR=48000;
const P=JSON.parse(fs.readFileSync(path.join(D,'partitura.json'),'utf8')),bank=path.resolve(__dirname,'../objetos/motor');
const Piano=require(path.join(bank,'piano.js')),Cuerda=require(path.join(bank,'cuerda.js')),Cl=require(path.join(bank,'clarinete.js')),Metal=require(path.join(bank,'metal.js'));
function wav(file,y){
 const b=Buffer.alloc(44+y.length*4);b.write('RIFF');b.writeUInt32LE(36+y.length*4,4);b.write('WAVEfmt ',8);b.writeUInt32LE(16,16);b.writeUInt16LE(3,20);b.writeUInt16LE(1,22);b.writeUInt32LE(SR,24);b.writeUInt32LE(SR*4,28);b.writeUInt16LE(4,32);b.writeUInt16LE(32,34);b.write('data',36);b.writeUInt32LE(y.length*4,40);
 for(let i=0;i<y.length;i++){if(!Number.isFinite(y[i]))throw Error(file+' no finito');b.writeFloatLE(y[i],44+i*4);}
 fs.writeFileSync(file,b,{flag:'wx'});
}
for(const [name,events] of Object.entries(P.instrumentos)){
 console.log(name,events.length,'eventos');
 for(const e of events){
  const ev={...e,t:0},c={dur:e.dur+1.4,semilla:P.semilla,eventos:[ev]};let y;
  if(name.startsWith('piano'))y=Piano.render(c,SR);
  else if(name==='clarinete')y=Cl.render(c,SR);
  else if(name==='metal'){delete c.eventos;c.notas=[ev];c.voz='trombon';c.sordina='cup';y=Metal.render(c,SR);}
  else {c.instrumento=name==='chelo'?'chelo':'viola';y=Cuerda.render(c,SR);}
  wav(path.join(D,'render',e.id+'.wav'),y);
 }
}
console.log('Notas originales terminadas');
