/* sonda: ¿la cuerda da la altura que se le pide? autocorrelación sobre 0.3–0.8 s; y una liga y un desliz.  node sondas/cuerda.cjs */
const C=require('../motor/cuerda.js'),fs=require('fs'),SR=48000,hz=m=>440*2**((m-69)/12);
function f0(x,a,b,lo,hi){let best=-1,bl=0;for(let L=Math.floor(SR/hi);L<SR/lo;L++){let s=0,e=0;for(let i=a;i<b;i++){s+=x[i]*x[i+L];e+=x[i]*x[i];}if(s/e>best){best=s/e;bl=L;}}
  let s=(L)=>{let q=0;for(let i=a;i<b;i++)q+=x[i]*x[i+L];return q;};const y0=s(bl-1),y1=s(bl),y2=s(bl+1),d=.5*(y0-y2)/(y0-2*y1+y2);return SR/(bl+d);}
for(const tipo of ['guembri','guitarra'])for(const m of (tipo==='guembri'?[39,46,51]:[51,63,75])){
  const y=C.render({dur:1,tipo,notas:[{t:0,dur:.9,m,v:.8}],semilla:1},SR);const f=f0(y,Math.round(.3*SR),Math.round(.5*SR),30,1200);
  const g=tipo==='guembri'?f0(y,Math.round(.3*SR),Math.round(.5*SR),60,400):0;console.log(tipo,m,'(60–400:',g.toFixed(1),')','pide',hz(m).toFixed(2),'da',f.toFixed(2),'cents',(1200*Math.log2(f/hz(m))).toFixed(1));}
const y=C.render({dur:3,tipo:'guitarra',notas:[{t:0,dur:.5,m:63,v:.8},{t:.5,dur:.5,m:66,liga:1},{t:1,dur:1.5,m:58,desliz:.4}],semilla:1},SR);
console.log('liga',f0(y,Math.round(.7*SR),Math.round(.85*SR),100,1200).toFixed(1),'pide',hz(66).toFixed(1),'· desliz',f0(y,Math.round(1.8*SR),Math.round(2*SR),100,1200).toFixed(1),'pide',hz(58).toFixed(1));
fs.writeFileSync(__dirname+'/cuerda-guitarra.f32',Buffer.from(y.buffer));
