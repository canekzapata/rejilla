// Fibonacci representation of B3: A=R, B=FRF. Column states; gestures act on the left.
export const PHI=(1+Math.sqrt(5))/2;
const c=(r,i=0)=>[r,i], add=(a,b)=>[a[0]+b[0],a[1]+b[1]], mul=(a,b)=>[a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0]];
export const mm=(a,b)=>a.map(row=>b[0].map((_,j)=>row.reduce((s,v,k)=>add(s,mul(v,b[k][j])),c(0))));
export const mv=(a,v)=>a.map(row=>row.reduce((s,z,j)=>add(s,mul(z,v[j])),c(0)));
export const adj=a=>a[0].map((_,j)=>a.map(row=>[row[j][0],-row[j][1]]));
const phase=t=>[Math.cos(t),Math.sin(t)];
const F=[[c(1/PHI),c(1/Math.sqrt(PHI))],[c(1/Math.sqrt(PHI)),c(-1/PHI)]];
export const A=[[phase(-4*Math.PI/5),c(0)],[c(0),phase(3*Math.PI/5)]];
export const B=mm(mm(F,A),F);
export const matrices={A,B,a:adj(A),b:adj(B)};
export const inverse=g=>g===g.toUpperCase()?g.toLowerCase():g.toUpperCase();
export const identity=()=>[[c(1),c(0)],[c(0),c(1)]];
export const wordMatrix=word=>[...word].reduce((u,g)=>mm(matrices[g],u),identity());
// Six conjugate copies of the same representation, not six arbitrary effects.
export const bases=Array.from({length:6},(_,k)=>{
 const t=.21+k*.193,p=k*.73;return [[c(Math.cos(t)),mul(phase(p),c(-Math.sin(t)))],[mul(phase(-p),c(Math.sin(t))),c(Math.cos(t))]];
});
export function coefficients(u){return bases.flatMap((s,k)=>{
 const init=[c(Math.cos(.32+k*.18)),mul(phase(k*.57),c(Math.sin(.32+k*.18)))];
 return mv(s,mv(u,mv(adj(s),init))).flat();
});}
export const norm=v=>v.reduce((s,x)=>s+x*x,0);
export class BraidState{
 constructor(){this.u=identity();this.word='';this.steps=[];}
 cross(g){if(!matrices[g])throw Error('Unknown crossing');this.u=mm(matrices[g],this.u);this.word+=g;this.steps.push(g);return this.values;}
 undo(){const g=this.steps.pop();if(!g)return null;this.u=mm(matrices[inverse(g)],this.u);this.word=this.word.slice(0,-1);return this.values;}
 clear(){this.u=identity();this.word='';this.steps=[];return this.values;}
 get values(){return coefficients(this.u);}
}
