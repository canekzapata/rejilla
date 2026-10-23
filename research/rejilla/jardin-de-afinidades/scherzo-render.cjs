// IV: motores originales; el objeto transforma sus tres lazos físicos.
const fs=require('fs'),path=require('path'),D=path.resolve(process.argv[2]),SR=48000;
const P=JSON.parse(fs.readFileSync(path.join(D,'partitura.json'),'utf8')),bank=path.resolve(__dirname,'../objetos/motor');
const C=require(path.join(bank,'cuerda.js')),Piano=require(path.join(bank,'piano.js')),Cl=require(path.join(bank,'clarinete.js')),O=require(path.join(bank,'objeto.js')),Agua=require(path.join(bank,'agua.js'));
const hz=m=>440*Math.pow(2,(m-69)/12);
function wav(file,y){
 const b=Buffer.alloc(44+y.length*4);b.write('RIFF');b.writeUInt32LE(36+y.length*4,4);b.write('WAVEfmt ',8);b.writeUInt32LE(16,16);b.writeUInt16LE(3,20);b.writeUInt16LE(1,22);b.writeUInt32LE(SR,24);b.writeUInt32LE(SR*4,28);b.writeUInt16LE(4,32);b.writeUInt16LE(32,34);b.write('data',36);b.writeUInt32LE(y.length*4,40);
 for(let i=0;i<y.length;i++){if(!Number.isFinite(y[i]))throw Error(file+' no finito');b.writeFloatLE(y[i],44+i*4);}
 fs.writeFileSync(file,b,{flag:'wx'});
}
function note(name,e){
 const ev={...e,t:0},config={dur:e.dur+1.4,eventos:[ev],semilla:P.semilla};
 if(name==='piano'){ev.prep=Piano.PREP[e.prep];if(!ev.prep)throw Error(e.prep);return Piano.render(config,SR);}
 if(name==='clarinete')return Cl.render(config,SR);
 if(name==='agua')return Agua.render(config,SR);
 if(name==='objeto'){
  const bar=e.tipo==='barra',morph=e.tipo==='sax-flauta';
  return O.render({dur:e.dur+1.4,semilla:P.semilla,f:()=>hz(e.m),
   w:bar?()=>[0,0,1]:morph?O.curva([[0,[1,0,0]],[e.dur*.18,[1,0,0]],[e.dur*.78,[0,1,0]],[e.dur,[0,1,0]]]):()=>[0,1,0],
   soplo:bar?()=>0:t=>Math.max(0,Math.min(1,t/.08,(e.dur-t)/.12)),
   pos:()=>.3,disp:()=>bar?.8:0,perdida:()=>.95,brillo:()=>.8,ruido:()=>.08,
   golpes:bar?[[.005,e.v]]:[],t60:()=>bar?.7:1.4,vibrato:[4.7,.015]},SR);
 }
 config.instrumento=name==='bajo'?'contrabajo':'viola';return C.render(config,SR);
}
if(process.argv[3]==='sondas'){
 for(const [name,e,label] of [['objeto',{m:57,dur:5,v:.6,tipo:'sax-flauta'},'morfosis'],['objeto',{m:57,dur:.35,v:.6,tipo:'barra'},'barra'],['cuerda',{m:57,dur:.4,v:.6,tipo:'pizz'},'pizz'],['clarinete',{m:50,dur:3,v:.6,tipo:'normal'},'sostenido']])wav(path.join(D,'render','sonda-'+label+'.wav'),note(name,e));
 console.log('Cuatro sondas terminadas');
}else{
 for(const [name,events] of Object.entries(P.instrumentos)){
  console.log(name,events.length,'eventos');for(const e of events)wav(path.join(D,'render',e.id+'.wav'),note(name,e));
 }
 console.log('Notas originales terminadas');
}
