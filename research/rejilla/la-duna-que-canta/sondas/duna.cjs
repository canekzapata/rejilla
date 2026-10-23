/* sonda: la duna en tres situaciones — masa estadística (K=0), bramido (K=3), y Kontakte X al revés (f de 4.86 a 77.7 Hz con K=3).
   Mide la coherencia r, el nivel y el pico espectral (FFT de 1 s) para ver si el siseo se vuelve nota.  node sondas/duna.cjs */
const Duna=require('../motor/duna.js'),fs=require('fs'),SR=48000;
function pico(x,i0){const n=1<<15;let best=0,fb=0;for(let k=Math.round(30*n/SR);k<Math.round(400*n/SR);k++){let re=0,im=0;for(let j=0;j<n;j+=2){const w=2*Math.PI*k*j/n;re+=x[i0+j]*Math.cos(w);im-=x[i0+j]*Math.sin(w);}const m=re*re+im*im;if(m>best){best=m;fb=k*SR/n;}}return fb;}
const rms=(x,a,b)=>{let s=0;for(let i=a;i<b;i++)s+=x[i]*x[i];return 20*Math.log10(Math.sqrt(s/(b-a))+1e-12);};
for(const [nom,K,f] of [['estadistica',[[0,0]],[[0,77.7]]],['bramido',[[0,0],[1,3]],[[0,77.7]]],['kontakte',[[0,3]],[[0,4.86],[5,4.86],[9,77.7]]]]){
  const t0=Date.now(),y=Duna.render({dur:12,f,K,flujo:[[0,0],[.3,1],[11.5,1],[12,0]],semilla:675},SR);
  const out=[];for(const s of [2,5,8,10.5])out.push(`t${s}: r ${y.r[s*100].toFixed(2)} ${rms(y.L,s*SR,(s+.5)*SR).toFixed(1)} dB pico ${pico(y.L,Math.floor(s*SR)).toFixed(1)} Hz`);
  console.log(nom.padEnd(12),(Date.now()-t0)+' ms |',out.join(' | '));
  const o=new Float32Array(y.L.length*2);for(let i=0;i<y.L.length;i++){o[2*i]=y.L[i];o[2*i+1]=y.R[i];}fs.writeFileSync(__dirname+'/duna-'+nom+'.f32',Buffer.from(o.buffer));}
