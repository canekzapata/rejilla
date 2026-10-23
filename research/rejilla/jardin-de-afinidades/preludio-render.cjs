// Renderizadores originales sin cambios. Cada nota queda disponible para medir y mezclar.
const fs=require('fs'),path=require('path'),D=path.resolve(process.argv[2]),SR=48000;
const P=JSON.parse(fs.readFileSync(path.join(D,'partitura.json'),'utf8'));
const bank=path.resolve(__dirname,'../objetos/motor');
function wav(file,y){
 const b=Buffer.alloc(44+y.length*4);b.write('RIFF');b.writeUInt32LE(36+y.length*4,4);b.write('WAVEfmt ',8);b.writeUInt32LE(16,16);b.writeUInt16LE(3,20);b.writeUInt16LE(1,22);b.writeUInt32LE(SR,24);b.writeUInt32LE(SR*4,28);b.writeUInt16LE(4,32);b.writeUInt16LE(32,34);b.write('data',36);b.writeUInt32LE(y.length*4,40);
 for(let i=0;i<y.length;i++){if(!Number.isFinite(y[i]))throw Error('no finito');b.writeFloatLE(y[i],44+i*4);}
 fs.writeFileSync(file,b,{flag:'wx'});
}
const instruments={piano:require(path.join(bank,'piano.js')),chelo:require(path.join(bank,'cuerda.js')),clarinete:require(path.join(bank,'clarinete.js'))};
if(process.argv[3]==='sondas'){
 for(const [name,m,tipo] of [['piano',57,'martillo'],['chelo',57,'tasto'],['chelo',47,'tasto'],['chelo',57,'arco'],['clarinete',57,'normal'],['clarinete',52,'normal']]){
  const y=instruments[name].render({dur:3.5,instrumento:'chelo',eventos:[{t:0,m,dur:3,v:.6,tipo}],semilla:P.semilla},SR);
  wav(path.join(D,'render',`sonda-${name}-${m}-${tipo}.wav`),y);
 }
 console.log('Seis sondas terminadas');
}else{
 for(const [name,events] of Object.entries(P.instrumentos)){
  console.log(name,events.length,'notas');
  for(const e of events){
   const ev={...e,t:0};
   wav(path.join(D,'render',e.id+'.wav'),instruments[name].render({dur:e.dur+1.1,instrumento:'chelo',semilla:P.semilla,eventos:[ev]},SR));
  }
 }
 console.log('Notas originales terminadas');
}
