/* El androide en la estación — capas de node: el traductor que se oxida (motor/traductor.js: LPC de la guía de Sabina en la
   celosía, con la altura de la partitura, abajo), el convoy que no sale (motor/convoy.js: Shepard–Risset) y el agua (agua.js de la
   copia fijada de la biblioteca). El traductor sale mono; el convoy estéreo (L,R entrelazados); el agua mono. 48 kHz, <carpeta>/<capa>.f32.
     node render_node.cjs <carpeta> [capa…] */
const fs=require('fs'),path=require('path');
const dir=process.argv[2],solo=process.argv.slice(3),P=JSON.parse(fs.readFileSync(path.join(dir,'partitura.json'),'utf8')),SR=48000,D=P.duracion;
const C=path.join(__dirname,P.instrumentos,'codigo/rejilla/research/rejilla/objetos/motor/');
const Agua=require(C+'agua.js'),Traductor=require('./motor/traductor.js'),Convoy=require('./motor/convoy.js');
const quiero=n=>!solo.length||solo.includes(n);
const stats=(n,y,est)=>{let p=0,s=0;for(const v of y){p=Math.max(p,Math.abs(v));s+=v*v;}console.log(n.padEnd(12),est?'(estéreo)':'',(y.length/SR/(est?2:1)).toFixed(1)+' s','pico',p.toFixed(3),'rms',Math.sqrt(s/y.length).toFixed(4));};
const guardar=(n,y)=>{fs.writeFileSync(path.join(dir,n+'.f32'),Buffer.from(Float32Array.from(y).buffer));stats(n,y);};
const guardar2=(n,L,R)=>{const o=new Float32Array(L.length*2);for(let i=0;i<L.length;i++){o[2*i]=L[i];o[2*i+1]=R[i];}fs.writeFileSync(path.join(dir,n+'.f32'),Buffer.from(o.buffer));stats(n,o,1);};
if(quiero('traductor')){const raw=new Float32Array(fs.readFileSync(path.join(dir,'sabina-guia.f32')).buffer.slice(0)),g=new Float32Array(raw.length/2);
  for(let i=0;i<g.length;i++)g[i]=(raw[2*i]+raw[2*i+1])/2;
  const t0=Date.now(),R=Traductor.render({dur:D,guia:g,eventos:P.traductor,oxido:P.oxido,perfil:Float32Array.from(P.perfil_isla),semilla:P.semilla},SR);
  guardar('traductor',R.y);fs.writeFileSync(path.join(dir,'traductor-k.json'),JSON.stringify(R.k));console.log('  traductor',(Date.now()-t0)+' ms');}
if(quiero('convoy')){const v=Convoy.render({dur:D,tonica:P.tonica_hz,tempo:1/P.negra,octava:P.periodo,...P.convoy,semilla:P.semilla+1},SR);guardar2('convoy',v.L,v.R);}
if(quiero('agua'))guardar('agua',Agua.render({dur:D,eventos:P.agua,semilla:P.semilla+2},SR));
