// Orquestación con los motores originales de objetos/. No modifica el banco ni normaliza las notas una por una.
const fs=require('fs'),path=require('path');
const out=path.resolve(process.argv[2]),P=JSON.parse(fs.readFileSync(path.join(out,'partitura.json'),'utf8'));
const M=path.join(__dirname,'../objetos/motor'),SR=48000,N=Math.ceil(P.duracion*SR);
const which=process.argv[3];
function write(name,y){
 let peak=0,sum=0;for(const v of y){if(!Number.isFinite(v))throw Error(name+' no finito');peak=Math.max(peak,Math.abs(v));sum+=v*v;}
 const b=Buffer.alloc(44+y.length*4);b.write('RIFF');b.writeUInt32LE(36+y.length*4,4);b.write('WAVEfmt ',8);b.writeUInt32LE(16,16);b.writeUInt16LE(3,20);b.writeUInt16LE(1,22);b.writeUInt32LE(SR,24);b.writeUInt32LE(SR*4,28);b.writeUInt16LE(4,32);b.writeUInt16LE(32,34);b.write('data',36);b.writeUInt32LE(y.length*4,40);
 for(let i=0;i<y.length;i++)b.writeFloatLE(y[i],44+i*4);
 fs.writeFileSync(path.join(out,'render',name+'.wav'),b,{flag:'wx'});
 fs.writeFileSync(path.join(out,'render',name+'-motor.json'),JSON.stringify({peak,rms:Math.sqrt(sum/y.length),sr:SR,frames:y.length}),{flag:'wx'});
 console.log(name,'pico',peak.toFixed(5));
}
function part(name,mod,extras={}){
 const motor=require(path.join(M,mod+'.js')),events=P.instrumentos[name];
 // Render por bloques de cuatro compases, con colas; cada nota se asigna una sola vez.
 const y=new Float32Array(N),step=P.compas*4;
 for(let t=0;t<P.duracion;t+=step){
  let ev=events.filter(e=>e.t>=t-1e-7&&e.t<t+step-1e-7).map(e=>({...e,t:e.t-t}));if(!ev.length)continue;
  if(name==='piano'){
   const prepAt=tt=>{
    const global=t+tt;let z=P.preparaciones[0];for(const q of P.preparaciones){if(global>=q.t)z=q;}
    let u=Math.max(0,Math.min(1,(global-z.t)/z.dur));u=u*u*(3-2*u);
    const normal={pos:.5,rho:0,amort:0,zumbido:0,umbral:.02};const A=motor.PREP[z.de]||normal,B=motor.PREP[z.a]||normal,r={};
    for(const key of Object.keys(normal))r[key]=A[key]+(B[key]-A[key])*u;return r;
   };
   ev=ev.map(e=>({...e,prep:prepAt}));
  }
  const length=Math.min(P.duracion-t,step+(mod==='piano'?4:mod==='gong'?6:3));
  let c={dur:length,eventos:ev,semilla:P.semilla+Math.round(t*100),...extras};
  if(name==='metal'){delete c.eventos;c.notas=ev;c.wah=[[0,.15],[step*.3,.95],[step*.6,.25],[step,1]];}
  const clip=motor.render(c,SR),start=Math.round(t*SR);
  for(let i=0;i<clip.length&&i+start<N;i++)y[i+start]+=clip[i];
 }
 write(name,y);
}
function viento(){
 const O=require(path.join(M,'objeto.js')),y=new Float32Array(N),events=P.instrumentos.viento;
 for(const e of events){
  const A=O.PURO[e.de],B=O.PURO[e.a],dur=e.dur+.65;
  const u=t=>{let q=Math.max(0,Math.min(1,t/e.dur));return q*q*(3-2*q);};
  const prop=(key,t)=>A[key]+(B[key]-A[key])*u(t);
  const c={dur,semilla:P.semilla+Math.round(e.t*100),f:()=>440*2**((e.m-69)/12),
   w:t=>A.w.map((v,i)=>v+(B.w[i]-v)*u(t)),pos:t=>prop('pos',t),disp:t=>prop('disp',t),
   perdida:t=>prop('perdida',t),brillo:t=>prop('brillo',t),ruido:t=>prop('ruido',t),
   soplo:t=>Math.min(1,t/.03)*Math.max(0,Math.min(1,(e.dur-t)/.10)),vibrato:[4.7,.012],
   golpes:e.a==='golpe'?[[e.dur*.55,.7],[e.dur*.8,.65]]:[],t60:()=>.8};
  const x=O.render(c,SR),start=Math.round(e.t*SR);for(let i=0;i<x.length&&start+i<N;i++)y[start+i]+=x[i]*e.v;
 }
 write('viento',y);
}
const jobs={piano:()=>part('piano','piano'),bajo:()=>part('bajo','cuerda',{instrumento:'contrabajo'}),
 cuerdas:()=>part('cuerdas','cuerda',{instrumento:'violin'}),clarinete:()=>part('clarinete','clarinete'),
 agua:()=>part('agua','agua'),vozagua:()=>part('vozagua','vozagua'),waterphone:()=>part('waterphone','waterphone'),
 tambor:()=>part('tambor','tambor'),metal:()=>part('metal','metal',{voz:'trombon',sordina:'plunger'}),
 pajaro:()=>part('pajaro','pajaro'),gong:()=>part('gong','gong'),viento};
for(const name of which?which.split(','):Object.keys(jobs)){console.log('renderizando',name);jobs[name]();}
