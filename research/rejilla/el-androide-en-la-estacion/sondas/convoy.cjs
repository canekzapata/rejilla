/* sonda del convoy: (1) la ilusión: el espectro a t y a t+17 s (una vuelta) es el mismo, pero a t+1.42 s (1/12 de vuelta)
   todos los parciales subieron un semitono; el centroide no se escapa. (2) dir −1: baja. Escribe sondas/convoy.f32.
     node sondas/convoy.cjs */
const C=require('../motor/convoy.js'),fs=require('fs'),SR=48000,TON=1024/17;
const y=C.render({dur:40,tonica:TON,tempo:32/17,dir:[[0,1],[20,1],[20.01,-1],[40,-1]],cerca:[[0,.7]],octava:17,semilla:1},SR);
function esp(t,base){const n=1<<15,i0=Math.round(t*SR),X=new Float64Array(n/2);for(let k=0;k<n/2;k+=1){}  // (lo hacemos con picos)
  const picos=[];for(const f0 of (base||[60,120,240,480,960])){let best=0,bf=0;for(let f=f0*.97;f<f0*1.09;f+=.25){let re=0,im=0;for(let j=0;j<8192;j+=2){const w=2*Math.PI*f*j/SR;re+=y.L[i0+j]*Math.cos(w);im+=y.L[i0+j]*Math.sin(w);}const m=re*re+im*im;if(m>best){best=m;bf=f;}}picos.push(+bf.toFixed(1));}return picos;}
const st=(a,b)=>a.map((v,i)=>(12*Math.log2(b[i]/v)).toFixed(2));
const a=esp(1),b=esp(1+17/12,a);
console.log('picos a 1 s',a,'\n+1/12 vuelta',b,'semitonos',st(a,b),'\n(subiendo)');
const d=esp(22),e=esp(22+17/12);console.log('dir −1: semitonos en 1/12 de vuelta',st(d,e));
function cent(t){const n=8192,i0=Math.round(t*SR);let num=0,den=0;for(let f=40;f<4000;f+=20){let re=0,im=0;for(let j=0;j<n;j+=2){const w=2*Math.PI*f*j/SR;re+=y.L[i0+j]*Math.cos(w);im+=y.L[i0+j]*Math.sin(w);}const m=re*re+im*im;num+=f*m;den+=m;}return Math.round(num/den);}
console.log('centroide (Hz) a 1, 5, 10, 15, 18 s:',[1,5,10,15,18].map(cent));
const o=new Float32Array(y.L.length*2);for(let i=0;i<y.L.length;i++){o[2*i]=y.L[i];o[2*i+1]=y.R[i];}fs.writeFileSync(__dirname+'/convoy.f32',Buffer.from(o.buffer));
