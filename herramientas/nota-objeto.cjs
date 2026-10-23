'use strict';
const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..'),bib=path.join(root,'biblioteca-de-instrumentos');
const [id,destino]=process.argv.slice(2),ids=JSON.parse(fs.readFileSync(path.join(bib,'fichas/todas.json')));
if(!ids.includes(id)||!destino)throw Error('Uso: node herramientas/nota-objeto.cjs <ficha> <salida.wav>');
const K=JSON.parse(fs.readFileSync(path.join(bib,'fichas',id+'.json')));
if(K.motor!=='objeto')throw Error('Esta ficha no usa el motor objeto');
const y=require(path.join(bib,'motores/objetos.js')).nota(K,{midi:62,vel:.7,dur:1.2},48000);
let peak=0;for(const x of y){if(!Number.isFinite(x))throw Error('Señal no finita');peak=Math.max(peak,Math.abs(x))}
if(peak<1e-8)throw Error('Señal muda');
const out=Buffer.alloc(44+2*y.length),sr=48000;
out.write('RIFF');out.writeUInt32LE(out.length-8,4);out.write('WAVEfmt ',8);out.writeUInt32LE(16,16);out.writeUInt16LE(1,20);out.writeUInt16LE(1,22);out.writeUInt32LE(sr,24);out.writeUInt32LE(2*sr,28);out.writeUInt16LE(2,32);out.writeUInt16LE(16,34);out.write('data',36);out.writeUInt32LE(2*y.length,40);
for(let i=0;i<y.length;i++)out.writeInt16LE(Math.round(y[i]*Math.min(1,.8/peak)*32767),44+2*i);
fs.mkdirSync(path.dirname(path.resolve(destino)),{recursive:true});fs.writeFileSync(destino,out,{flag:'wx'});console.log(destino);
