// sonda: ¿el saxofón de objeto.js toca una línea de bebop en semicorcheas a 144? f(t) por tramos + soplo con lengua.
const fs=require('fs'),path=require('path');
const O=require('../instrumentos-dedf969a0fe6/codigo/rejilla/research/rejilla/objetos/motor/objeto.js');
const SR=48000,S=60/144/4,hz=m=>440*2**((m-69)/12);
const linea=JSON.parse(process.argv[2]);              // [[t, m, dur, lengua 0/1, vel]]
const out=process.argv[3],dur=linea.at(-1)[0]+linea.at(-1)[2]+.6;
const f=t=>{let k=0;while(k+1<linea.length&&linea[k+1][0]<=t)k++;const a=linea[k];
  if(k>0){const u=(t-a[0])/.012;if(u<1){return hz(linea[k-1][1]+(a[1]-linea[k-1][1])*Math.max(0,u));}}return hz(a[1]);};
const soplo=t=>{let v=0;for(const [t0,m,d,l,vel] of linea){if(t<t0-.01||t>t0+d+.03)continue;
  let e=vel; const u=t-t0; if(l&&u<.018)e*=.45+.55*u/.018; if(u>d)e*=Math.max(0,1-(u-d)/.03); v=Math.max(v,e);}return v;};
const P=O.PURO.saxofon;
const y=O.render({dur,f,w:()=>[1,0,0],soplo,pos:()=>P.pos,disp:()=>0,perdida:()=>P.perdida,brillo:()=>P.brillo,ruido:()=>P.ruido,vibrato:[5.2,.03],semilla:9},SR);
fs.writeFileSync(out,Buffer.from(y.buffer));console.log('ok',(y.length/SR).toFixed(2));
