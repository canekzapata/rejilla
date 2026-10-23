const fs=require('fs'),path=require('path');
const out=path.resolve(process.argv[2]),P=JSON.parse(fs.readFileSync(path.join(out,'partitura.json'),'utf8')),base=path.resolve(__dirname,'../objetos/motor'),SR=48000;
function save(name,y){let peak=0;for(const v of y){if(!Number.isFinite(v))throw Error(name+' no finito');peak=Math.max(peak,Math.abs(v));}fs.writeFileSync(path.join(out,'render',name+'.f32'),Buffer.from(y.buffer),{flag:'wx'});console.log(name,'pico',peak);}
for(const [name,engine,events] of [['pajaros','pajaro',P.pajaros],['agua','agua',P.agua]]){
 if(!fs.existsSync(path.join(out,'render',name+'.f32')))save(name,require(base+'/'+engine+'.js').render({dur:P.duracion,eventos:events,semilla:P.semilla},SR));
}
if(!fs.existsSync(path.join(out,'render','madera.f32'))){
 const O=require(base+'/objeto.js'),G=O.PURO.golpe,notes=P.madera;let k=0;
 const f=t=>{while(k+1<notes.length&&notes[k+1].t<=t)k++;return 440*2**((notes[k].m-69)/12);};
 save('madera',O.render({dur:P.duracion,f,w:()=>[0,0,1],soplo:()=>0,pos:()=>.23,disp:()=>1,perdida:()=>G.perdida,brillo:()=>G.brillo,ruido:()=>0,golpes:notes.map(e=>[e.t,e.v]),t60:()=>.65,semilla:P.semilla+3},SR));
}
