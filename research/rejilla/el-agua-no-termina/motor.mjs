export const VERSION='1.0.0';
export const SEED=20261021;
// Exact Fourier-Galerkin convolution on a symmetric ball in Z^3.
export const K=[];
for(let x=-2;x<=2;x++)for(let y=-2;y<=2;y++)for(let z=-2;z<=2;z++){
 const s=x*x+y*y+z*z;if(s>0&&s<=5)K.push([x,y,z,s]);
}
const lookup=new Map(K.map((k,i)=>[k.slice(0,3).join(','),i]));
export const PAIRS=K.map((k,i)=>({k,i})).filter(({k})=>k[0]>0||(k[0]===0&&(k[1]>0||(k[1]===0&&k[2]>0))));
const triads=K.map(k=>{let a=[];K.forEach((p,i)=>{let j=lookup.get([k[0]-p[0],k[1]-p[1],k[2]-p[2]].join(','));if(j!==undefined)a.push([i,j]);});return a;});
export function rhs(u,nu=0,nonlinear=1,out=new Float64Array(u.length)){
 out.fill(0);
 K.forEach((k,i)=>{
  let o=i*6;
  if(nonlinear)for(const [p,q] of triads[i]){
   let a=p*6,b=q*6,v=K[q],dr=0,di=0;
   for(let c=0;c<3;c++){dr+=u[a+2*c]*v[c];di+=u[a+2*c+1]*v[c];}
   for(let c=0;c<3;c++){let r=u[b+2*c],im=u[b+2*c+1];out[o+2*c]+=nonlinear*(dr*im+di*r);out[o+2*c+1]-=nonlinear*(dr*r-di*im);}
  }
  let dr=0,di=0;for(let c=0;c<3;c++){dr+=k[c]*out[o+2*c];di+=k[c]*out[o+2*c+1];}
  for(let c=0;c<3;c++){out[o+2*c]-=k[c]*dr/k[3]+nu*k[3]*u[o+2*c];out[o+2*c+1]-=k[c]*di/k[3]+nu*k[3]*u[o+2*c+1];}
 });return out;
}
export function metrics(u){
 let energy=0,enstrophy=0,div=0,reality=0,shells=Array(5).fill(0);
 K.forEach((k,i)=>{let e=0,dr=0,di=0,j=lookup.get(k.slice(0,3).map(x=>-x).join(','));
  for(let c=0;c<3;c++){let r=u[i*6+2*c],m=u[i*6+2*c+1];e+=(r*r+m*m)/2;dr+=k[c]*r;di+=k[c]*m;reality=Math.max(reality,Math.abs(r-u[j*6+2*c]),Math.abs(m+u[j*6+2*c+1]));}
  energy+=e;enstrophy+=k[3]*e;shells[k[3]-1]+=e;div=Math.max(div,Math.hypot(dr,di));
 });return {energy,enstrophy,div,reality,shells};
}
export class Fluid {
 constructor(){this.u=new Float64Array(K.length*6);this.nu=.035;this.nonlinear=1;this.time=0;this.work=0;this.tmp=new Float64Array(this.u.length);this.ks=Array.from({length:4},()=>new Float64Array(this.u.length));}
 kick(x=.7,y=1.5,z=.4,force=.65,fine=0){
  if(![x,y,z,force,fine].every(Number.isFinite)||force<0||force>1||fine<0||fine>1)throw Error('Impulso fuera de rango');
  const before=metrics(this.u).energy;
  K.forEach((k,i)=>{
   // Even polarization ensures conjugate symmetry, followed by Leray projection.
   let v=[.4,1,.3],dot=k[0]*v[0]+k[1]*v[1]+k[2]*v[2];
   let a=force*.19*Math.exp(-(.8-.55*fine)*(k[3]-1)),p=-(k[0]*x+k[1]*y+k[2]*z);
   for(let c=0;c<3;c++){let w=a*(v[c]-k[c]*dot/k[3]);this.u[i*6+2*c]+=w*Math.cos(p);this.u[i*6+2*c+1]+=w*Math.sin(p);}
  });this.work+=metrics(this.u).energy-before;
 }
 step(dt){
  let sub=Math.max(1,Math.ceil(dt*32*Math.sqrt(2*metrics(this.u).energy))),h=dt/sub;
  for(let n=0;n<sub;n++){
   let [a,b,c,d]=this.ks,u=this.u,t=this.tmp;rhs(u,this.nu,this.nonlinear,a);
   for(let i=0;i<u.length;i++)t[i]=u[i]+h*a[i]/2;rhs(t,this.nu,this.nonlinear,b);
   for(let i=0;i<u.length;i++)t[i]=u[i]+h*b[i]/2;rhs(t,this.nu,this.nonlinear,c);
   for(let i=0;i<u.length;i++)t[i]=u[i]+h*c[i];rhs(t,this.nu,this.nonlinear,d);
   for(let i=0;i<u.length;i++)u[i]+=h*(a[i]+2*b[i]+2*c[i]+d[i])/6;
  }this.time+=dt;
 }
 clear(){this.u.fill(0);this.time=0;this.work=0;}
}
export function field(u,x,y,z=.4){let v=[0,0,0];for(const {k,i} of PAIRS){let a=k[0]*x+k[1]*y+k[2]*z,c=Math.cos(a),s=Math.sin(a);for(let j=0;j<3;j++)v[j]+=2*(u[i*6+2*j]*c-u[i*6+2*j+1]*s);}return v;}

// Sonification: a moving probe x0 + (1,3,7)*phase samples the real field.
// The fluid clock is slow; the probe clock supplies musical pitch.
export class Voice {
 constructor(sr=48000){this.sr=sr;this.fluid=new Fluid();this.midi=45;this.speed=1;this.pickup=.4;this.gain=.32;this.frame=0;this.block=Math.round(sr/120);this.phase=0;this.coeff=new Float64Array(PAIRS.length*4);this.target=this.coeff.slice();this.clipped=0;}
 params(p){const ranges={midi:[24,84],speed:[.2,2],pickup:[0,2*Math.PI],nu:[0,1],nonlinear:[0,1]};for(const [k,v] of Object.entries(p)){if(!ranges[k]||!Number.isFinite(v)||v<ranges[k][0]||v>ranges[k][1])throw Error('Parámetro fuera de rango: '+k);}for(const k of ['midi','speed','pickup'])if(p[k]!==undefined)this[k]=p[k];if(p.nu!==undefined)this.fluid.nu=p.nu;if(p.nonlinear!==undefined)this.fluid.nonlinear=p.nonlinear;}
 event(e){if(e.clear)this.fluid.clear();if(e.params)this.params(e.params);if(e.kick){let p=e.kick;this.fluid.kick(p.x??.7,p.y??1.5,p.z??.4,p.force??.65,p.fine??0);}}
 update(){this.fluid.step(this.speed/120);let u=this.fluid.u;PAIRS.forEach(({k,i},j)=>{let p=k[2]*this.pickup,c=Math.cos(p),s=Math.sin(p);for(let ch=0;ch<2;ch++){let a=ch===0?[1,.22,.1]:[.22,1,.1],r=0,m=0;for(let n=0;n<3;n++){r+=a[n]*u[i*6+2*n];m+=a[n]*u[i*6+2*n+1];}this.target[j*4+ch*2]=2*(r*c-m*s);this.target[j*4+ch*2+1]=2*(r*s+m*c);}});}
 sample(){if(this.frame%this.block===0)this.update();let out=[0,0],f=440*2**((this.midi-69)/12),step=2*Math.PI*f/this.sr;
  PAIRS.forEach(({k},j)=>{let h=k[0]+3*k[1]+7*k[2];if(!h||Math.abs(h)*f>this.sr*.43)return;let c=Math.cos(h*this.phase),s=Math.sin(h*this.phase);for(let ch=0;ch<2;ch++){let a=j*4+ch*2,b=a+1;this.coeff[a]+=(this.target[a]-this.coeff[a])*.012;this.coeff[b]+=(this.target[b]-this.coeff[b])*.012;out[ch]+=this.coeff[a]*c-this.coeff[b]*s;}});
  this.phase=(this.phase+step)%(2*Math.PI);this.frame++;
  return out.map(v=>{let x=v*this.gain;if(Math.abs(x)>.98)this.clipped++;return .98*Math.tanh(x/.98);});
 }
}
