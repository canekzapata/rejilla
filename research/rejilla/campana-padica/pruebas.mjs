import {Campana,matrix,distance2,render,hz} from './motor.mjs';
const fail=(c,m)=>{if(!c)throw Error(m)};
const e=new Campana(48000,{fold:.73,depth:.9,damping:0,midi:45});
for(let i=0;i<64;i++)e.q[i]=.02*Math.sin(i*1.618);
const m=matrix(.9,.73),l=e.laplacian(),dense=m.map(row=>row.reduce((s,v,i)=>s+v*e.q[i],0));
const kernelError=Math.max(...l.map((v,i)=>Math.abs(v-dense[i])));
fail(kernelError<1e-13,'El kernel no coincide con la matriz');
e.clear();e.strike(1,.7);const E=e.energy();let drift=0;
for(let i=0;i<24000;i++){e.sample();if(i%97===0)drift=Math.max(drift,Math.abs(e.energy()/E-1));}
fail(drift<.002,'Deriva conservativa excesiva');
const before=e.snapshot(),old=e.energy();e.set({fold:1,depth:1.7},true);const after=e.snapshot();
const qcontinuity=Math.max(...after.q.map((v,i)=>Math.abs(v-before.q[i])));
const vcontinuity=Math.max(...after.v.map((v,i)=>Math.abs(v-before.v[i])));
fail(qcontinuity===0&&vcontinuity===0,'Se reinició la vibración al plegar');
const a=new Campana(48000,{fold:.7,damping:1.2,midi:45});a.strike(1,.7);const de=a.energy();
for(let i=0;i<24000;i++)a.sample();const decayRatio=a.energy()/de;
fail(Math.abs(decayRatio-Math.exp(-1.2))<.004,'Amortiguación incorrecta');
const analytic=new Campana(96000,{fold:.37,depth:.8,damping:0,midi:48});analytic.strike(9,.7);
for(let i=0;i<512;i++)analytic.sample();
const positions=[];
for(const zone of [1,2,9]){const x=render({initial:{fold:1,damping:.8},events:[{t:0,hit:zone}]},.5,24000);positions.push(Array.from(x.left.filter((_,i)=>i%16===0)));}
const diff=(x,y)=>Math.sqrt(x.reduce((s,v,i)=>s+(v-y[i])**2,0)/y.reduce((s,v)=>s+v*v,0));
const positionDifferences=[diff(positions[0],positions[1]),diff(positions[0],positions[2])];
fail(positionDifferences.every(v=>v>.05),'Las posiciones no se distinguen en la captación');
const extremes=[];
for(const fold of [0,1])for(const midi of [36,72]){
 const z=render({initial:{fold,midi,tension:14,depth:2,damping:.2},events:[{t:0,hit:1,vel:1}]},.15,24000);
 fail(z.left.every(Number.isFinite),'Audio no finito');extremes.push(z.metrics);
}
console.log(JSON.stringify({kernelError,conservativeEnergyDrift:drift,qcontinuity,vcontinuity,
 energyChangeOnFold:e.energy()-old,accountedWork:e.work,dampedEnergyRatio:decayRatio,expectedDecay:Math.exp(-1.2),
 distances:[distance2(1,2),distance2(1,3),distance2(1,9)],positionDifferences,extremes,
 analytic:{matrix:matrix(.8,.37).map(x=>Array.from(x)),q:Array.from(analytic.q),v:Array.from(analytic.v),
 t:512/96000,velocity:2*Math.PI*hz(48)*.7*1.25,midi:48,tension:7,zone:9},
 matrices:{local:matrix(.7,0).map(x=>Array.from(x)),padic:matrix(.7,1).map(x=>Array.from(x))}}));
