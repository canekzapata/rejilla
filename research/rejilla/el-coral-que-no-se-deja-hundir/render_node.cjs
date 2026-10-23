/* El coral que no se deja hundir — capas de node: las fragatas a lo Messiaen (pajaro.js de la copia fijada: siringe de van der Pol,
   gestos 'canto' en el modo 3) y las burbujas (motor/cueva.js de «Primero sueño en el cenote»: el volcán desgasifica al hundirse,
   burbujas de Minnaert en el flanco y en la laguna). 48 kHz.
     node render_node.cjs <carpeta> [capa…] */
const fs=require('fs'),path=require('path');
const dir=process.argv[2],solo=process.argv.slice(3),P=JSON.parse(fs.readFileSync(path.join(dir,'partitura.json'),'utf8')),SR=48000,D=P.duracion;
const C=path.join(__dirname,P.instrumentos,'codigo/rejilla/research/rejilla/');
const Cueva=require('./motor/cueva.js'),Pajaro=require(C+'objetos/motor/pajaro.js');
const quiero=n=>!solo.length||solo.includes(n);
const stats=(n,y,est)=>{let p=0,s=0;for(const v of y){p=Math.max(p,Math.abs(v));s+=v*v;}console.log(n.padEnd(12),est?'(estéreo)':'',(y.length/SR/(est?2:1)).toFixed(1)+' s','pico',p.toFixed(3),'rms',Math.sqrt(s/y.length).toFixed(4));};
const guardar=(n,y)=>{fs.writeFileSync(path.join(dir,n+'.f32'),Buffer.from(Float32Array.from(y).buffer));stats(n,y);};
const guardar2=(n,L,R)=>{const o=new Float32Array(L.length*2);for(let i=0;i<L.length;i++){o[2*i]=L[i];o[2*i+1]=R[i];}fs.writeFileSync(path.join(dir,n+'.f32'),Buffer.from(o.buffer));stats(n,o,1);};
if(quiero('aves'))for(const voz of [0,1])guardar('aves'+voz,Pajaro.render({dur:D,eventos:P.aves.filter(e=>(e.voz||0)===voz),semilla:P.semilla+voz},SR));
if(quiero('burbujas')){const y=Cueva.render({dur:D,camaras:P.camaras,gotas:P.gotas,semilla:P.semilla},SR);guardar2('burbujas',y.L,y.R);}
