/* Extiende el motor original por protocolo, sin modificar su ecuación. */
import fs from 'node:fs';import path from 'node:path';
import {Fluid,K,metrics,field} from './fuentes/agua/motor.mjs';
function inicial(){let f=new Fluid();f.kick(.7,1.5,.4,.7,.7);f.kick(2.1,.35,1.3,.45,.45);return f;}
if(process.argv.includes('--inicial')){const f=inicial();console.log(JSON.stringify({K,u:Array.from(f.u),metricas:metrics(f.u)}));process.exit(0);}
const OUT=path.resolve(process.argv[2]),dt=1/240,T=8,N=Math.round(T/dt),init=inicial().u.slice();
function ciclo(nu,h,guardar=false){
 const f=new Fluid();f.nu=nu;f.u.set(init);const n=Math.round(T/h),ida=[],vuelta=[],traza=[];
 const cap=(list,t,s)=>{if(guardar)list.push(Float32Array.from(f.u));if(s%24===0||s===n)traza.push({fase:list===ida?'ida':'vuelta',t,...metrics(f.u)});};
 cap(ida,0,0);for(let j=1;j<=n;j++){f.step(h);cap(ida,j*h,j);}
 for(let i=0;i<f.u.length;i++)f.u[i]*=-1;
 cap(vuelta,0,0);for(let j=1;j<=n;j++){f.step(h);cap(vuelta,j*h,j);}
 const returned=Float64Array.from(f.u,x=>-x);let err=0,norm=0;for(let i=0;i<init.length;i++){err+=(returned[i]-init[i])**2;norm+=init[i]**2;}
 return {ida,vuelta,traza,retornado:Array.from(returned),error:Math.sqrt(err/norm)};
}
const ideal=ciclo(0,dt,true),viscoso=ciclo(.045,dt,true),coarse=ciclo(0,1/120);
const write=(name,x)=>fs.writeFileSync(path.join(OUT,name),x,{flag:'wx'});
for(const [n,c] of [['ideal',ideal],['viscoso',viscoso]])for(const fase of ['ida','vuelta']){
 const a=new Float32Array((N+1)*init.length);c[fase].forEach((x,i)=>a.set(x,i*init.length));write(`${n}-${fase}.f32`,Buffer.from(a.buffer));
}
const residuo=viscoso.retornado.map((v,i)=>v-ideal.retornado[i]);let e=0;for(let v of residuo)e+=v*v/2;
const info={modelo:'Fourier-Galerkin 56 modos del motor original; RK4; no simulación de turbulencia ilimitada',T_fisico:T,dt,N,dimension:init.length,K,nu:.045,inicial:Array.from(init),ideal:{error_retorno:ideal.error,error_dt_doble:coarse.error,traza:ideal.traza,retornado:ideal.retornado},viscoso:{error_retorno:viscoso.error,traza:viscoso.traza,retornado:viscoso.retornado},residuo,energia_residuo:e,convencion:'vuelta inicia con -u(T); al comparar el retorno se restituye el signo. Diferencia viscoso menos ideal sin normalizar sus estados.',video_renderizado:false};
if(!(ideal.error<1e-6&&ideal.error<coarse.error&&viscoso.error>.01&&e>0))throw Error('falló el eco '+JSON.stringify([ideal.error,coarse.error,viscoso.error]));
write('eco.json',JSON.stringify(info));console.log({ideal:ideal.error,coarse:coarse.error,viscoso:viscoso.error,energia_residuo:e});
