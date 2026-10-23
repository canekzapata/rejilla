import assert from 'node:assert/strict';
import {Fluid,K,metrics,rhs,Voice,field} from './motor.mjs';
const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0),norm=a=>Math.sqrt(dot(a,a));
let f=new Fluid();f.kick(.7,1.5,.4,.7,.4);f.kick(2.8,.2,1,.3,1);const m=metrics(f.u),d=rhs(f.u,0),vis=rhs(f.u,.13);
const r={modes:K.length,conjugate_pairs:K.length/2,divergence:m.div,reality:m.reality,ideal_energy_derivative:dot(f.u,d),viscous_balance_error:Math.abs(dot(f.u,vis)+2*.13*m.enstrophy)};
assert(r.divergence<1e-12);assert(r.reality<1e-12);assert(Math.abs(r.ideal_energy_derivative)<1e-12);assert(r.viscous_balance_error<1e-12);
let s=new Fluid(),i=K.findIndex(k=>k[0]===1&&k[1]===0&&k[2]===0),j=K.findIndex(k=>k[0]===-1&&k[1]===0&&k[2]===0);s.u[i*6+2]=s.u[j*6+2]=.3;s.nu=.17;
for(let n=0;n<240;n++)s.step(1/240);r.shear_exact_decay_error=Math.abs(s.u[i*6+2]-.3*Math.exp(-.17));assert(r.shear_exact_decay_error<1e-11);
let initial=f.u.slice(),e0=m.energy;f.nu=0;for(let n=0;n<600;n++)f.step(1/240);r.inviscid_energy_drift=Math.abs(metrics(f.u).energy/e0-1);assert(r.inviscid_energy_drift<1e-7);
let linear=new Fluid();linear.u.set(initial);linear.nu=0;linear.nonlinear=0;for(let n=0;n<600;n++)linear.step(1/240);r.nonlinear_state_difference=norm(f.u.map((v,i)=>v-linear.u[i]))/norm(initial);assert(r.nonlinear_state_difference>.03);
let damp=new Fluid();damp.u.set(initial);damp.nu=.25;let last=metrics(damp.u).energy;for(let n=0;n<240;n++){damp.step(1/120);let e=metrics(damp.u).energy;assert(e<=last+1e-12);last=e;}r.damped_energy_ratio=last/e0;
// Independent energy inner product and real-field finite-difference divergence.
let eps=1e-5,pos=[.8,1.7,.2],dv=0;for(let c=0;c<3;c++){let a=pos.slice(),b=pos.slice();a[c]+=eps;b[c]-=eps;dv+=(field(initial,...a)[c]-field(initial,...b)[c])/(2*eps);}r.real_field_divergence=Math.abs(dv);assert(r.real_field_divergence<1e-8);
let v=new Voice(24000),w=new Voice(24000);for(let q of [v,w])q.event({kick:{force:.75}});let max=0,err=0;for(let n=0;n<24000;n++){let a=v.sample(),b=w.sample();for(let c=0;c<2;c++){assert(Number.isFinite(a[c]));max=Math.max(max,Math.abs(a[c]));err=Math.max(err,Math.abs(a[c]-b[c]));}}r.audio_peak=max;r.determinism_max_error=err;assert(err===0);assert(max>.01&&max<.98);
console.log(JSON.stringify(r,null,2));
