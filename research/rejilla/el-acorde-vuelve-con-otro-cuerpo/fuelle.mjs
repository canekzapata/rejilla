/* Lengüetas autooscilantes bajo presión normalizada: modelo fenomenológico activo.
   No es una implementación del modelo aerodinámico de Ricot ni un bayan calibrado. */
import fs from 'node:fs';import path from 'node:path';
export function render(e,sr=32768,OS=2){const s=sr*OS,n=Math.round((e.dur+.5)*s),y=new Float32Array(Math.ceil(n/OS));let x=1e-4,v=0,prevQ=0;const f0=440*2**((e.midi-69)/12),f1=440*2**(((e.m2??e.midi)-69)/12),beta=.32;
function deriv(x,v,mu){return [v,(mu-beta*x*x)*v-x];}
for(let i=0;i<n;i++){
 const t=i/s,u=Math.min(1,t/e.dur),shape=u*u*(3-2*u),f=f0*(f1/f0)**shape,pressure=(e.presion??.7)*Math.min(1,t/.13)*Math.min(1,Math.max(0,(e.dur+.2-t)/.2)),mu=.1*pressure-.02,h=2*Math.PI*f/s;
 const a=deriv(x,v,mu),b=deriv(x+h*a[0]/2,v+h*a[1]/2,mu),c=deriv(x+h*b[0]/2,v+h*b[1]/2,mu),d=deriv(x+h*c[0],v+h*c[1],mu);x+=h*(a[0]+2*b[0]+2*c[0]+d[0])/6;v+=h*(a[1]+2*b[1]+2*c[1]+d[1])/6;
 const aperture=.5*(.22+x+Math.sqrt((.22+x)**2+.0025)),flow=aperture*Math.sqrt(Math.max(pressure,0));const sound=(flow-prevQ)*s/(2*Math.PI*f);prevQ=flow;
 y[Math.floor(i/OS)]+=sound*(e.aire===-1?-.8:1)*e.vel*.35/OS;
}return y;}
if(process.argv[2]&&process.argv[2]!=='--import'){
 const OUT=path.resolve(process.argv[2]),P=JSON.parse(fs.readFileSync(path.join(OUT,'partitura.json'),'utf8')),tag=path.basename(OUT).split('-').pop(),R=path.join(path.dirname(OUT),'render',tag),N=Math.round(P.duracion*P.sr);
 for(const c of ['fuelle-alto','fuelle-bajo','fuelle-portadora']){let y=new Float32Array(N*2);for(const e of P.eventos[c==='fuelle-portadora'?'voz-fuelle':c]){const ev=c==='fuelle-portadora'?{...e,dur:e.dur+.25,presion:.85}:e,z=render(ev,P.sr*2,1),i0=Math.round(e.t*P.sr*2);for(let j=0;j<z.length&&i0+j<y.length;j++)y[i0+j]+=z[j];}fs.writeFileSync(path.join(R,c+'-os2.f32'),Buffer.from(y.buffer),{flag:'wx'});console.log(c);}
}
