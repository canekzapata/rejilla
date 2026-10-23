// Same Gaussian representation and metaplectic path as motor.py; no dependencies.
export const SR=32768, TAU=.018, SEED=20261021;
const add=(a,b)=>[a[0]+b[0],a[1]+b[1]], scale=(a,s)=>[a[0]*s,a[1]*s];
const mul=(a,b)=>[a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0]];
const div=(a,b)=>scale(mul(a,[b[0],-b[1]]),1/(b[0]*b[0]+b[1]*b[1]));
const root=a=>{const r=Math.sqrt(Math.hypot(...a)),t=Math.atan2(a[1],a[0])/2;return [r*Math.cos(t),r*Math.sin(t)]};
const ph=t=>[Math.cos(t),Math.sin(t)];
export const hz=m=>440*2**((m-69)/12);
export function source(midi=57,body='cobre',seed=SEED){
  if(!['cobre','vidrio','boca'].includes(body))throw Error('Cuerpo desconocido');
  return Array.from({length:7},(_,j)=>{
    const h=j+1,f=hz(midi),ratio=body==='vidrio'?h*(1+.014*(h-1)**2):h;
    let weight=h**-1.15;
    if(body==='boca')weight*=.25+1.7*Math.exp(-(((h*f-750)/260)**2))+Math.exp(-(((h*f-1250)/350)**2));
    const A=body==='vidrio'?[.16+.02*h,.01*h]:[.08+.012*h,.025*h];
    const q=-.2+.07*h,p=(ratio-1)*f*TAU,phase=.25*Math.sin((seed%65521)*.13+h*2.17);
    return {A,B:scale(ph(phase-Math.PI*p*q),.18*weight),q,p};
  });
}
export function rotate(packet,theta){
  if(!Number.isFinite(theta)||Math.abs(theta)>64*Math.PI)throw Error('Giro fuera de rango');
  let z={...packet}; const n=Math.max(1,Math.ceil(Math.abs(theta)/(Math.PI/4)));
  const c=Math.cos(theta/n),s=Math.sin(theta/n);
  for(let i=0;i<n;i++){
    const den=add([c,0],mul([0,s],z.A));
    z={A:div(add(scale(z.A,c),[0,s]),den),B:div(z.B,root(den)),q:c*z.q+s*z.p,p:-s*z.q+c*z.p};
  }return z;
}
export function apply(packets,ops){
  let z=packets.map(p=>({...p,A:[...p.A],B:[...p.B]}));
  for(const [op,v] of ops){
    if(!Number.isFinite(v))throw Error('Parámetro no finito');
    z=z.map(p=>{
      if(op==='girar')return rotate(p,v);
      if(op==='chirp')return {...p,A:add(p.A,[0,-v]),p:p.p+v*p.q};
      if(op==='dilatar'){
        if(v<=0)throw Error('Dilatación no positiva');
        return {A:scale(p.A,1/v**2),B:scale(p.B,1/Math.sqrt(v)),q:p.q*v,p:p.p/v};
      }
      if(op==='dispersar')return rotate(apply([rotate(p,-Math.PI/2)],[['chirp',-v]])[0],Math.PI/2);
      throw Error('Operación desconocida');
    });
  }return z;
}
export function operations(o={}){
  let mid=[['chirp',o.inclinacion??0],['girar',o.giro??0]];
  if(o.orden==='girar-inclinar')mid.reverse();
  return [['dilatar',o.estirar??1],...mid,['dispersar',o.dispersion??0]];
}
export function value(packets,x){
  let re=0,im=0;
  for(const p of packets){
    const d=x-p.q,env=Math.exp(-Math.PI*p.A[0]*d*d);
    const arg=-Math.PI*p.A[1]*d*d+2*Math.PI*p.p*(x-p.q/2),c=Math.cos(arg),s=Math.sin(arg);
    re+=env*(p.B[0]*c-p.B[1]*s);im+=env*(p.B[0]*s+p.B[1]*c);
  }return [re,im];
}
export function note(o={},sr=SR,duration=1.5){
  const midi=o.midi??57,reference=o.referencia??0;
  const original=source(midi,o.cuerpo??'cobre',o.semilla??SEED),traveller=apply(original,operations(o));
  const data=new Float32Array(Math.round(sr*duration)),fade=Math.max(1,Math.round(.006*sr));
  for(let i=0;i<data.length;i++){
    const t=i/sr-.6,x=t/TAU;
    let z=value(traveller,x);
    if(reference){const r=value(original,x);z=scale(add(z,scale(r,reference)),1/(1+reference));}
    let v=z[0]*Math.cos(2*Math.PI*hz(midi)*t)-z[1]*Math.sin(2*Math.PI*hz(midi)*t);
    if(i<fade)v*=i/(fade-1);
    if(i>=data.length-fade)v*=(data.length-i-1)/(fade-1);
    data[i]=v;
  }return data;
}
