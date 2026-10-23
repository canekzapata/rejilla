/* sonda de la cueva: (1) la gota de 3 mm debe empezar cerca de 3.26/0.003 = 1087 Hz y subir; (2) la misma gota en dos cámaras
   (fh 90 y 300 Hz) debe tener su energía extra cerca de su fh.   node sondas/cueva.cjs */
const C=require('../motor/cueva.js'),SR=48000;
function fpico(x,a,b,lo,hi){let best=0,bf=0;for(let f=lo;f<hi;f+=2){let s1=0,s2=0;const w=2*Math.cos(2*Math.PI*f/SR);for(let i=a;i<b;i++){const s=x[i]+w*s1-s2;s2=s1;s1=s;}const m=s1*s1+s2*s2-w*s1*s2;if(m>best){best=m;bf=f;}}return bf;}
function banda(x,f){let s1=0,s2=0;const w=2*Math.cos(2*Math.PI*f/SR);for(let i=0;i<x.length;i++){const s=x[i]+w*s1-s2;s2=s1;s1=s;}return 10*Math.log10(s1*s1+s2*s2-w*s1*s2+1e-12);}
const cam={a:{fh:90,fb:520,q:18,pan:0,eco:.6},b:{fh:300,fb:880,q:18,pan:0,eco:.6}};
const y=C.render({dur:1.5,camaras:cam,gotas:[{t:.1,id:'a',r:3,v:.8}]},SR).L;
console.log('gota 3 mm: primeros 4 ms',fpico(y,Math.round(.101*SR),Math.round(.105*SR),600,2500),'Hz · 15–20 ms',fpico(y,Math.round(.115*SR),Math.round(.12*SR),600,2500),'Hz (esperado 1087 y subiendo)');
const ya=y,yb=C.render({dur:1.5,camaras:cam,gotas:[{t:.1,id:'b',r:3,v:.8}]},SR).L;
console.log('cámara a (fh 90): 90 Hz',banda(ya,90).toFixed(1),'dB · 300 Hz',banda(ya,300).toFixed(1),'dB');
console.log('cámara b (fh 300): 90 Hz',banda(yb,90).toFixed(1),'dB · 300 Hz',banda(yb,300).toFixed(1),'dB');
