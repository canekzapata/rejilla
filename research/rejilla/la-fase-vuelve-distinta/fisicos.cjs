const fs=require('fs'),path=require('path');
const out=process.argv[2],P=JSON.parse(fs.readFileSync(path.join(out,'partitura.json'),'utf8'));
const G=require('../lo-que-tapa-la-traspuesta/motor/garganta.js');
const C=require('../objetos/motor/cuerda.js');
const M=require('../objetos/motor/metal.js');
function save(name,y){fs.writeFileSync(path.join(out,'render',name+'.f32'),Buffer.from(y.buffer),{flag:'wx'});console.log(name,y.length);}
save('garganta',G.render({dur:P.duracion,perfil:Float32Array.from({length:96},(_,i)=>.48+.22*Math.sin(i*.17)+.14*Math.cos(i*.29)),largo:1,eventos:P.garganta.map(e=>({...e,nota:e.m,fonemas:[e.vocal||'a'],aprende:.9})),semilla:P.semilla},48000));
save('chelo',C.render({dur:P.duracion,instrumento:'chelo',eventos:P.chelo,semilla:P.semilla},48000));
save('metal',M.render({dur:P.duracion,voz:'trombon',sordina:'harmon',notas:P.metal,semilla:P.semilla},48000));
