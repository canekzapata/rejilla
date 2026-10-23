const fs=require('fs'),path=require('path'),D=path.resolve(process.argv[2]),P=JSON.parse(fs.readFileSync(path.join(D,'partitura.json'),'utf8')),SR=48000;
const bank=path.join(__dirname,'../objetos/motor');
function write(name,y){const b=Buffer.alloc(44+y.length*4);b.write('RIFF');b.writeUInt32LE(36+y.length*4,4);b.write('WAVEfmt ',8);b.writeUInt32LE(16,16);b.writeUInt16LE(3,20);b.writeUInt16LE(1,22);b.writeUInt32LE(SR,24);b.writeUInt32LE(SR*4,28);b.writeUInt16LE(4,32);b.writeUInt16LE(32,34);b.write('data',36);b.writeUInt32LE(y.length*4,40);let peak=0;for(let i=0;i<y.length;i++){if(!Number.isFinite(y[i]))throw Error('no finito');b.writeFloatLE(y[i],44+i*4);peak=Math.max(peak,Math.abs(y[i]));}fs.writeFileSync(path.join(D,'render',name+'.wav'),b,{flag:'wx'});console.log(name,P.instrumentos[name].length,'eventos; pico',peak);}
for(const [name,module] of Object.entries({piano:'piano',chelo:'cuerda',pajaro:'pajaro',agua:'agua'})){
 const motor=require(path.join(bank,module+'.js')),y=new Float32Array(Math.ceil(P.duracion*SR));
 for(let k=0;k<P.instrumentos[name].length;k++){
  const e=P.instrumentos[name][k],ev={...e,t:0},cfg={dur:e.dur+(name==='piano'?1.8:.5),semilla:P.semilla+k*97,eventos:[ev]};
  if(name==='piano'){if(e.prep)ev.prep=motor.PREP[e.prep];else delete ev.prep;}
  if(name==='chelo')cfg.instrumento='chelo';
  const z=motor.render(cfg,SR),a=Math.round(e.t*SR);for(let i=0;i<z.length&&a+i<y.length;i++)y[a+i]+=z[i];
 }
 write(name,y);
}
