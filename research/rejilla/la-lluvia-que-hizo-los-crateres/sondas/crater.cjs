/* sonda de la membrana de cráter: los picos del espectro contra los modos de Bessel; golpe al centro (sólo m = 0) contra golpe al
   borde; complejo contra simple; viejo contra joven (centroide).   node sondas/crater.cjs */
const C=require('../motor/crater.js'),SR=48000;
function picos(x,n=6){const N=1<<16,out=[];for(let f=20;f<600;f+=.25){let s1=0,s2=0;const w=2*Math.cos(2*Math.PI*f/SR);for(let i=0;i<N;i++){const s=x[i+2400]+w*s1-s2;s2=s1;s1=s;}out.push([f,s1*s1+s2*s2-w*s1*s2]);}
  return out.filter((p,i)=>i>0&&i<out.length-1&&p[1]>out[i-1][1]&&p[1]>out[i+1][1]).sort((a,b)=>b[1]-a[1]).slice(0,n).sort((a,b)=>a[0]-b[0]).map(p=>+p[0].toFixed(1));}
function cent(x){let a=0,b=0;const N=8192;for(let f=50;f<8000;f+=50){let s1=0,s2=0;const w=2*Math.cos(2*Math.PI*f/SR);for(let i=0;i<N;i++){const s=x[i]+w*s1-s2;s2=s1;s1=s;}const m=s1*s1+s2*s2-w*s1*s2;a+=f*m;b+=m;}return Math.round(a/b);}
const T={s:{D:1800,complejo:false,edad:0},c:{D:1800,complejo:true,edad:0},v:{D:600,complejo:false,edad:1},j:{D:600,complejo:false,edad:0}};
const R=(id,r,v=.9)=>C.render({dur:3,tambores:T,golpes:[{t:.05,id,v,r}],semilla:1},SR).L;
console.log('esperados (1.8 km):',[1,1.594,2.136,2.295,2.653,2.917].map(x=>+(45*x).toFixed(1)));
console.log('simple, golpe al borde (r .7):',picos(R('s',.7)));
console.log('simple, golpe al centro (r 0):',picos(R('s',0)),'(m = 0: 45, 103.3, 162.3)');
console.log('complejo, al borde:',picos(R('c',.7)),'(m = 0 sube x1.12; terrazas)');
console.log('centroide 600 m, joven',cent(R('j',.5)),'Hz · viejo',cent(R('v',.5)),'Hz');
const t0=Date.now();const g=[];for(let i=0;i<2000;i++)g.push({t:i*.1,id:['s','c','v','j'][i%4],v:.8,r:.5});C.render({dur:205,tambores:T,golpes:g,semilla:2},SR);console.log('2000 golpes en',Date.now()-t0,'ms');
