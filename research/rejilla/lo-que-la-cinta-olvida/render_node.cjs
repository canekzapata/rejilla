/* Lo que la cinta olvida — capas de node: el requinto (motor/cuerda.js, la guitarra de «La duna que canta»; en tiempo de cinta), y
   lo vivo, en tiempo real: el cello (cuerda frotada de la biblioteca), la garganta de río (motor/garganta_rio.js de «El río no
   tiene tronco», con el tubo en la forma de la curvatura del meandro), el agua y los pájaros de la llanura (biblioteca).
   Mono 48 kHz a <carpeta>/<capa>.f32; la garganta sale estéreo.   node render_node.cjs <carpeta> [capa…] */
const fs=require('fs'),path=require('path');
const dir=process.argv[2],solo=process.argv.slice(3),P=JSON.parse(fs.readFileSync(path.join(dir,'partitura.json'),'utf8')),SR=48000,D=P.duracion;
const C=path.join(__dirname,P.instrumentos,'codigo/rejilla/research/rejilla/objetos/motor/');
const Cuerda=require('./motor/cuerda.js'),Chelo=require(C+'cuerda.js'),Agua=require(C+'agua.js'),Pajaro=require(C+'pajaro.js'),GR=require('./motor/garganta_rio.js'),Lector=require('../../../difonos/runtime/lector.js');
const quiero=n=>!solo.length||solo.includes(n);
const stats=(n,y,est)=>{let p=0,s=0;for(const v of y){p=Math.max(p,Math.abs(v));s+=v*v;}console.log(n.padEnd(12),est?'(estéreo)':'',(y.length/SR/(est?2:1)).toFixed(1)+' s','pico',p.toFixed(3),'rms',Math.sqrt(s/y.length).toFixed(4));};
const guardar=(n,y)=>{fs.writeFileSync(path.join(dir,n+'.f32'),Buffer.from(Float32Array.from(y).buffer));stats(n,y);};
const guardar2=(n,L,R)=>{const o=new Float32Array(L.length*2);for(let i=0;i<L.length;i++){o[2*i]=L[i];o[2*i+1]=R[i];}fs.writeFileSync(path.join(dir,n+'.f32'),Buffer.from(o.buffer));stats(n,o,1);};
(async()=>{const sem=P.semilla;
 if(quiero('requinto'))guardar('requinto',Cuerda.render({dur:P.T_tau,tipo:'guitarra',notas:P.requinto,semilla:sem+1},SR));
 if(quiero('chelo'))guardar('chelo',Chelo.render({dur:D,instrumento:'chelo',eventos:P.chelo,semilla:sem+2},SR));
 if(quiero('garganta')){   /* el tubo con la forma del meandro: la curvatura a lo largo del cauce */
   const c=P.cauce,k=[];for(let i=1;i<c.length-1;i++){const a=Math.atan2(c[i][1]-c[i-1][1],c[i][0]-c[i-1][0]),b=Math.atan2(c[i+1][1]-c[i][1],c[i+1][0]-c[i][0]);let d=b-a;while(d>Math.PI)d-=2*Math.PI;while(d<-Math.PI)d+=2*Math.PI;k.push(Math.abs(d));}
   const n=40,perfil=new Float32Array(n);let mx=0;for(let i=0;i<n;i++){const j0=Math.floor(i*k.length/n),j1=Math.floor((i+1)*k.length/n);let s=0;for(let j=j0;j<j1;j++)s+=k[j];perfil[i]=s/(j1-j0);mx=Math.max(mx,perfil[i]);}
   for(let i=0;i<n;i++)perfil[i]=.15+.85*perfil[i]/mx;
   const R=GR.render({dur:D,perfil,largo:2.2,brazos:[],eventos:P.garganta,semilla:sem+3},SR);guardar2('garganta',R.L,R.R);}
 if(quiero('agua'))guardar('agua',Agua.render({dur:D,eventos:P.agua,semilla:sem+4},SR));
 if(quiero('aves'))guardar('aves',Pajaro.render({dur:D,eventos:P.aves,semilla:sem+5},SR));
})();
