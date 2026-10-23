/* sonda del traductor: (1) la celosía da la misma respuesta que el filtro directo 1/A(z) de Levinson; (2) con la voz de Sabina
   (la llamada de «La duna que canta») a óxido 0, .5 y 1: formantes por cuadro antes y después, nivel, y que nada explote.
     node sondas/traductor.cjs */
const T=require('../motor/traductor.js'),fs=require('fs'),SR=48000;
// (1) celosía contra forma directa con una autocorrelación de prueba
const p=8,r=new Float64Array(p+1);for(let l=0;l<=p;l++)r[l]=Math.cos(.3*l)*Math.exp(-.1*l)+.5*Math.cos(1.1*l)*Math.exp(-.05*l);
const L=T.levinson(r,p),k=Array.from(L.k).slice(1);
let a=[1];for(let i=0;i<p;i++){const ki=k[i],n=[...a,0];for(let j=1;j<=i+1;j++)n[j]=a[j]+ki*(a[i+1-j]??0);n[i+1]=ki;a=n.slice(0,i+2);}   // step-up
const M=64,dir=[],lat=[];const yd=new Float64Array(M);
for(let n=0;n<M;n++){let y=n===0?1:0;for(let j=1;j<=p;j++)y-=a[j]*(yd[n-j]||0);yd[n]=y;dir.push(y);}
const f=new Float64Array(p+1),b=new Float64Array(p+1);
for(let n=0;n<M;n++){let fN=n===0?1:0;for(let q=p;q>=1;q--){fN=fN-k[q-1]*b[q-1];f[q-1]=fN;}const y=fN;for(let q=p;q>=1;q--)b[q]=k[q-1]*f[q-1]+b[q-1];b[0]=y;lat.push(y);}
let err=0;for(let n=0;n<M;n++)err=Math.max(err,Math.abs(dir[n]-lat[n]));console.log('celosía vs directa: error máx',err.toExponential(2));
// (2) la voz
const raw=new Float32Array(fs.readFileSync('../la-duna-que-canta/render/r1/sabina-lead.f32').buffer);const D=14,g=new Float32Array(D*SR);
const t0=Math.round(34.5*SR);for(let i=0;i<g.length;i++)g[i]=(raw[2*(t0+i)]+raw[2*(t0+i)+1])/2;
const ev=[];for(let t=0;t<D;t+=.45)ev.push({t,dur:.43,nota:[46,49,51,46,44][ev.length%5]});
for(const o of [0,.5,1]){const tt=Date.now(),R=T.render({dur:D,guia:g,eventos:ev,oxido:[[0,o]],perfil:Float32Array.from({length:40},(_, i)=>Math.sin(i/7)**2),semilla:1},SR);
  let s=0,fin=true;for(const v of R.y){s+=v*v;if(!isFinite(v))fin=false;}console.log('óxido',o,'rms',(10*Math.log10(s/R.y.length)).toFixed(1),'dB',fin?'finito':'¡NaN!',(Date.now()-tt)+' ms','k1..3 a los 5 s',R.k[100].slice(1,4));
  fs.writeFileSync(__dirname+`/traductor-ox${o}.f32`,Buffer.from(R.y.buffer));}
fs.writeFileSync(__dirname+'/traductor-guia.f32',Buffer.from(g.buffer));
