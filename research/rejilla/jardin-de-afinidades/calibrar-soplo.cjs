// Sondas auxiliares exclusivas; no modifica objeto.js.
const fs=require('fs'),path=require('path'),O=require('../objetos/motor/objeto.js'),D=path.resolve(process.argv[2]),SR=48000;
for(const breath of [.78,.86,.92,.96]){
 const dur=5,y=O.render({dur:6.4,semilla:1610267,f:()=>220,w:O.curva([[0,[1,0,0]],[.9,[1,0,0]],[3.9,[0,1,0]],[5,[0,1,0]]]),soplo:t=>breath*Math.max(0,Math.min(1,t/.08,(dur-t)/.12)),pos:()=>.3,disp:()=>0,perdida:()=>.95,brillo:()=>.8,ruido:()=>.08,golpes:[],vibrato:[4.7,.015]},SR);
 const b=Buffer.alloc(44+y.length*4);b.write('RIFF');b.writeUInt32LE(36+y.length*4,4);b.write('WAVEfmt ',8);b.writeUInt32LE(16,16);b.writeUInt16LE(3,20);b.writeUInt16LE(1,22);b.writeUInt32LE(SR,24);b.writeUInt32LE(SR*4,28);b.writeUInt16LE(4,32);b.writeUInt16LE(32,34);b.write('data',36);b.writeUInt32LE(y.length*4,40);for(let i=0;i<y.length;i++)b.writeFloatLE(y[i],44+i*4);
 fs.writeFileSync(path.join(D,'render',`sonda-soplo-${breath}.wav`),b,{flag:'wx'});
}
