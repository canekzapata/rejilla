const fs=require('fs'),path=require('path'),D=path.resolve(process.argv[2]);
const p=JSON.parse(fs.readFileSync(path.join(D,'partitura.json'),'utf8')),sr=24000;
const motor=require('../objetos/motor/cuerda.js');
const y=motor.render({dur:p.duracion,instrumento:'chelo',eventos:p.chelo},sr);
const b=Buffer.alloc(44+4*y.length);b.write('RIFF');b.writeUInt32LE(36+4*y.length,4);b.write('WAVEfmt ',8);b.writeUInt32LE(16,16);b.writeUInt16LE(3,20);b.writeUInt16LE(1,22);b.writeUInt32LE(sr,24);b.writeUInt32LE(sr*4,28);b.writeUInt16LE(4,32);b.writeUInt16LE(32,34);b.write('data',36);b.writeUInt32LE(y.length*4,40);
let peak=0;for(let i=0;i<y.length;i++){if(!Number.isFinite(y[i]))throw Error('No finito');b.writeFloatLE(y[i],44+i*4);peak=Math.max(peak,Math.abs(y[i]));}
fs.writeFileSync(path.join(D,'render/chelo.wav'),b,{flag:'wx'});console.log({eventos:p.chelo.length,peak,segundos:y.length/sr});
