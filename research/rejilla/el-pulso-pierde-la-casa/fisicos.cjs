const fs=require('fs'),path=require('path');
const out=process.argv[2],P=JSON.parse(fs.readFileSync(path.join(out,'partitura.json'),'utf8'));
const base=path.resolve(__dirname,'../objetos/motor');
const save=(name,y)=>{fs.writeFileSync(path.join(out,'render',name+'.f32'),Buffer.from(y.buffer),{flag:'wx'});console.log(name,y.length);};
const G=require('../lo-que-tapa-la-traspuesta/motor/garganta.js');
save('garganta',G.render({dur:P.duracion,perfil:Float32Array.from({length:96},(_,i)=>.5+.27*Math.sin(i*.12)+.17*Math.cos(i*.31)),largo:1,eventos:P.garganta.map(e=>({...e,nota:e.m,fonemas:[e.vocal||'a'],aprende:.85})),semilla:P.semilla},48000));
save('chelo',require(base+'/cuerda.js').render({dur:P.duracion,instrumento:'chelo',eventos:P.chelo,semilla:P.semilla},48000));
save('metal',require(base+'/metal.js').render({dur:P.duracion,voz:'trombon',sordina:'harmon',notas:P.metal,semilla:P.semilla},48000));
