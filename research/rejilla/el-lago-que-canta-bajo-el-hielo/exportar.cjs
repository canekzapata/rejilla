/* Exportación instrumentada, sin modificar Traspuesta. Misma función y mismas coordenadas deformadas. */
const fs=require('fs'),path=require('path'),vm=require('vm');
const out=path.resolve(process.argv[2]),src=path.join(__dirname,'fuentes/traspuesta');
vm.runInThisContext(fs.readFileSync(path.join(src,'nucleo.js'),'utf8'));
let s=fs.readFileSync(path.join(src,'terreno.js'),'utf8');
const marcador='const borde = (f2 - f1) * M;';
if(s.split(marcador).length!==2)throw Error('cambió el caso polígonos');
// Guardar etiqueta de la celda durante F.f: el motor la llama en las coordenadas wu,wv reales.
s=s.replace('let f1 = 9, f2 = 9;','let f1 = 9, f2 = 9, celdaLago = -1;');
s=s.replace('if (d < f1) { f2 = f1; f1 = d; }','if (d < f1) { f2 = f1; f1 = d; celdaLago = j * (M + 1) + i; }');
s=s.replace(marcador,'globalThis.__ultimaCeldaLago = celdaLago; '+marcador);
s=s.replace('const b = F.f(wu, wv);','const b = F.f(wu, wv); if(globalThis.__etiquetasLago) globalThis.__etiquetasLago[j*GN+i]=globalThis.__ultimaCeldaLago;');
vm.runInThisContext(s);globalThis.__etiquetasLago=new Int32Array(360*360);
const T=MT.terreno('227');if(T.arq!=='poligonos')throw Error('227 ya no es permafrost');
fs.mkdirSync(out,{recursive:true});
for(const [n,x] of [['h-227.f32',T.h],['regiones-227.i32',__etiquetasLago]])fs.writeFileSync(path.join(out,n),Buffer.from(x.buffer,x.byteOffset,x.byteLength),{flag:'wx'});
fs.writeFileSync(path.join(out,'terreno-227.json'),JSON.stringify({semilla:227,arq:T.arq,G:T.G,anchoKm:T.anchoKm,relieve:T.relieve,exportacion:'F.f en wu,wv; etiquetas del mismo mínimo que el borde',escala_acustica:1/32}),{flag:'wx'});
console.log('terreno 227 y regiones exportados');
