/** A finite 2-adic resonator. Real displacement + velocity, 64 regions.
 * u'' + 2 gamma u' + omega0^2 (I + kappa [(1-s)Lgrid+s L2])u = F.
 * Velocity Verlet with symmetric damping; controls update without resetting u,v.
 * No claim of exact energy conservation at finite numerical step.
 */
export const N=64, VERSION='1.0.0', SEED=20261021, SR=24000;
export const DEFAULT={fold:0,depth:.7,tension:7,damping:.55,midi:48,pickup:0};
export const hz=m=>440*2**((m-69)/12);
export function valuation2(n){if(!Number.isInteger(n)||n===0)throw Error('Diferencia entera no nula requerida');let k=0;while(n%2===0){n/=2;k++;}return k;}
export function distance2(i,j){return i===j?0:2**(-valuation2(i-j));}
export function weights(depth=.7){
 const w=new Float64Array(6);let norm=0;
 for(let k=0;k<6;k++){w[k]=2**((1+depth)*k);norm+=(32>>k)*w[k];}
 for(let k=0;k<6;k++)w[k]/=norm;return w;
}
export function matrix(depth=.7,fold=1){
 const w=weights(depth),m=Array.from({length:N},()=>new Float64Array(N));
 for(let i=0;i<N;i++)for(let j=0;j<N;j++)if(i!==j){
  const near=(Math.abs((i%8)-(j%8))+Math.abs((i>>3)-(j>>3))===1)?.25:0;
  const a=(1-fold)*near+fold*w[valuation2(i-j)];m[i][j]=-a;m[i][i]+=a;
 }return m;
}
const clamp=(v,lo,hi)=>Math.max(lo,Math.min(hi,v));
export function validate(p){
 const z={...DEFAULT,...p};
 for(const k of Object.keys(DEFAULT))if(!Number.isFinite(z[k]))throw Error('Parámetro no finito: '+k);
 z.fold=clamp(z.fold,0,1);z.depth=clamp(z.depth,0,2);z.tension=clamp(z.tension,.2,14);
 z.damping=clamp(z.damping,0,5);z.midi=clamp(z.midi,36,72);z.pickup=Math.round(clamp(z.pickup,0,7));return z;
}
export class Campana{
 constructor(sr=SR,p={}){
  if(!Number.isFinite(sr)||sr<16000||sr>192000)throw Error('Sample rate fuera de rango');
  this.sr=sr;this.dt=1/sr;this.q=new Float64Array(N);this.v=new Float64Array(N);this.a=new Float64Array(N);
  this.lp=new Float64Array(N);this.sums=Array.from({length:7},(_,k)=>new Float64Array(1<<k));
  this.left=new Float64Array(N);this.right=new Float64Array(N);
  this.output=new Float64Array(2);
  this.p=validate(p);this.target={...this.p};this.frame=0;this.work=0;this.maxPeak=0;this.clipped=0;
  this.refresh();this.force();
 }
 refresh(){
  this.w=weights(this.p.depth);this.omega=2*Math.PI*hz(this.p.midi);this.omega2=this.omega**2;
  this.decay=Math.exp(-this.p.damping/this.sr);
  // Fixed asymmetric stereo pickups; selected residue family moves the aperture.
  let ln=0,rn=0;
  for(let i=0;i<N;i++){
   const family=i%8===this.p.pickup?1:.12;
   this.left[i]=family*(.28+.6*Math.exp(-(((i-13)/11)**2))+.21*Math.sin(i*2.17+.4));
   this.right[i]=family*(.25+.55*Math.exp(-(((i-46)/13)**2))+.19*Math.cos(i*1.73+.7));
   ln+=this.left[i]**2;rn+=this.right[i]**2;
  }
  for(let i=0;i<N;i++){this.left[i]/=Math.sqrt(ln);this.right[i]/=Math.sqrt(rn);}
 }
 laplacian(q=this.q,out=this.lp){
  this.sums[6].set(q);
  for(let k=5;k>=0;k--)for(let r=0;r<(1<<k);r++)this.sums[k][r]=this.sums[k+1][r]+this.sums[k+1][r+(1<<k)];
  const f=this.p.fold,w=this.w;
  for(let i=0;i<N;i++){
   let neighbours=0;
   for(let k=0;k<6;k++)neighbours+=w[k]*this.sums[k+1][(i^(1<<k))&((1<<(k+1))-1)];
   let grid=0;
   if(i%8)grid+=q[i]-q[i-1];if(i%8<7)grid+=q[i]-q[i+1];
   if(i>=8)grid+=q[i]-q[i-8];if(i<56)grid+=q[i]-q[i+8];
   out[i]=(1-f)*grid*.25+f*(q[i]-neighbours);
  }return out;
 }
 force(){this.laplacian();for(let i=0;i<N;i++)this.a[i]=-this.omega2*(this.q[i]+this.p.tension*this.lp[i]);}
 energy(){
  this.laplacian();let e=0;
  for(let i=0;i<N;i++)e+=this.v[i]**2+this.omega2*(this.q[i]**2+this.p.tension*this.q[i]*this.lp[i]);
  return .5*e;
 }
 set(p,immediate=false){
  this.target=validate({...this.target,...p});
  if(immediate){const before=this.energy();this.p={...this.target};this.refresh();this.force();this.work+=this.energy()-before;}
 }
 advanceControls(){
  const blend=1-Math.exp(-64/(this.sr*.045));let changed=false;const next={...this.p};
  for(const k of ['fold','depth','tension','damping','midi']){
   const d=this.target[k]-this.p[k];if(Math.abs(d)>1e-8){next[k]+=d*blend;changed=true;}
  }
  if(this.p.pickup!==this.target.pickup){next.pickup=this.target.pickup;changed=true;}
  if(changed){const before=this.energy();this.p=next;this.refresh();this.force();this.work+=this.energy()-before;}
 }
 strike(zone=1,velocity=.7){
  if(!Number.isInteger(zone)||zone<0||zone>=N||!Number.isFinite(velocity))throw Error('Golpe inválido');
  this.v[zone]+=this.omega*clamp(velocity,0,1)*1.25;
 }
 clear(){this.q.fill(0);this.v.fill(0);this.a.fill(0);this.work=0;}
 sample(){
  if(this.frame%64===0)this.advanceControls();
  const h=.5*this.dt,d=this.decay;
  for(let i=0;i<N;i++){this.v[i]=this.v[i]*d+h*this.a[i];this.q[i]+=this.dt*this.v[i];}
  this.force();let l=0,r=0;
  for(let i=0;i<N;i++){this.v[i]=(this.v[i]+h*this.a[i])*d;l+=this.left[i]*this.q[i];r+=this.right[i]*this.q[i];}
  this.frame++;l*=.78;r*=.78;
  this.maxPeak=Math.max(this.maxPeak,Math.abs(l),Math.abs(r));
  if(Math.abs(l)>.98||Math.abs(r)>.98)this.clipped++;
  // Output-only protection for repeated heavy strikes; state remains linear.
  this.output[0]=clamp(l,-.98,.98);this.output[1]=clamp(r,-.98,.98);return this.output;
 }
 snapshot(){return {q:Array.from(this.q),v:Array.from(this.v),params:{...this.p},frame:this.frame};}
}
export function render(score={},duration=10,sr=SR){
 if(!Number.isFinite(duration)||duration<=0||duration>180)throw Error('Duración fuera de rango');
 const e=new Campana(sr,score.initial??{}),events=[...(score.events??[])].sort((a,b)=>a.t-b.t);
 const frames=Math.round(duration*sr),l=new Float32Array(frames),r=new Float32Array(frames),snapshots=[];
 let j=0;
 for(let i=0;i<frames;i++){
  while(j<events.length&&events[j].t*sr<=i){const ev=events[j++];if(ev.params)e.set(ev.params,ev.immediate??false);if(ev.hit!==undefined)e.strike(ev.hit,ev.vel??.7);if(ev.clear)e.clear();}
  const y=e.sample();l[i]=y[0];r[i]=y[1];
  if(i%(sr/20|0)===0)snapshots.push({t:i/sr,q:Array.from(e.q),params:{...e.p}});
 }
 return {left:l,right:r,snapshots,metrics:{peak:e.maxPeak,limitedFrames:e.clipped,work:e.work,energy:e.energy(),duration,sr,events:j}};
}
