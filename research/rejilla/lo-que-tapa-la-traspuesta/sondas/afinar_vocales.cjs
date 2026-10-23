// busca la forma de cada vocal (constricción, área mínima, ancho, labios) cuyo tubo dé las formantes del español
const G=require('../motor/garganta.js');
const META={a:[700,1250],e:[450,1900],i:[300,2300],o:[500,950],u:[330,800]};
function respuesta(A){                 // respuesta en frecuencia del tubo por impulso (mismo KL que garganta.js)
  const N=A.length,sr=48000,L=2048,f=new Float64Array(N+1),b=new Float64Array(N+1),fn=new Float64Array(N+1),bn=new Float64Array(N+1),r=[],y=new Float64Array(L);
  for(let k=0;k<N-1;k++)r.push((A[k]-A[k+1])/(A[k]+A[k+1]));
  for(let i=0;i<L;i++){fn[0]=(i===0?1:0)+.75*b[0];for(let k=0;k<N-1;k++){fn[k+1]=(1+r[k])*f[k]-r[k]*b[k+1];bn[k]=r[k]*f[k]+(1-r[k])*b[k+1];}
    const s=f[N-1];bn[N-1]=-.85*s;for(let k=0;k<N;k++){f[k]=fn[k]*.9993;b[k]=bn[k]*.9993;}y[i]=s;}
  const pk=[];let prev=0,pp=0;for(let fq=150;fq<3200;fq+=25){let re=0,im=0;for(let i=0;i<L;i++){const w=2*Math.PI*fq*i/sr;re+=y[i]*Math.cos(w);im-=y[i]*Math.sin(w);}const m=re*re+im*im;if(prev>pp&&prev>m)pk.push(fq-25);pp=prev;prev=m;}
  return pk;}
const N=24,out={};
for(const v of 'aeiou'){let best=null;
  for(let xc=.15;xc<=.9;xc+=.05)for(const am of [.15,.3,.5,.8,1.2])for(const w of [.1,.15,.2])for(const lab of [.15,.4,.8,1.5,3,5]){
    G.VOCAL[v]=[xc,am,w,lab];const A=G.areaVocal(v,N,new Float64Array(N));const pk=respuesta(A);if(pk.length<2)continue;
    const e=Math.abs(Math.log(pk[0]/META[v][0]))+Math.abs(Math.log(pk[1]/META[v][1]));if(!best||e<best.e)best={e,p:[+xc.toFixed(2),am,w,lab],pk:pk.slice(0,3)};}
  out[v]=best;console.log(v,JSON.stringify(best));}
