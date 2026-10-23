/* Primero sueño en el cenote — capas de node: la cueva que gotea (motor/cueva.js: 56 cámaras con su gotero), el katajjaq (dos
   gargantas de la biblioteca que se tiran pulsos: una capa por garganta), el bordón gutural (la garganta larga, ronca) y las aves de
   noche (pajaro.js). La forma del tubo de las gargantas: un corte por la dolina más grande. 48 kHz; la cueva estéreo.
     node render_node.cjs <carpeta> [capa…] */
const fs=require('fs'),path=require('path');
const dir=process.argv[2],solo=process.argv.slice(3),P=JSON.parse(fs.readFileSync(path.join(dir,'partitura.json'),'utf8')),SR=48000,D=P.duracion;
const C=path.join(__dirname,P.instrumentos,'codigo/rejilla/research/rejilla/');
const Cueva=require('./motor/cueva.js'),Garganta=require(C+'lo-que-tapa-la-traspuesta/motor/garganta.js'),Pajaro=require(C+'objetos/motor/pajaro.js'),Lector=require('../../../difonos/runtime/lector.js');
const quiero=n=>!solo.length||solo.includes(n);
const stats=(n,y,est)=>{let p=0,s=0;for(const v of y){p=Math.max(p,Math.abs(v));s+=v*v;}console.log(n.padEnd(12),est?'(estéreo)':'',(y.length/SR/(est?2:1)).toFixed(1)+' s','pico',p.toFixed(3),'rms',Math.sqrt(s/y.length).toFixed(4));};
const guardar=(n,y)=>{fs.writeFileSync(path.join(dir,n+'.f32'),Buffer.from(Float32Array.from(y).buffer));stats(n,y);};
const guardar2=(n,L,R)=>{const o=new Float32Array(L.length*2);for(let i=0;i<L.length;i++){o[2*i]=L[i];o[2*i+1]=R[i];}fs.writeFileSync(path.join(dir,n+'.f32'),Buffer.from(o.buffer));stats(n,o,1);};
const H=new Float32Array(fs.readFileSync(path.join(__dirname,'terreno','h-43.f32')).buffer.slice(0)),G=360,c0=P.camaras_info[0];
const perfil=new Float32Array(40);{const cy=Math.round(c0.v*(G-1)),cx=Math.round(c0.u*(G-1)),r=Math.max(6,Math.round(c0.radio_m/(9500/359)*1.6));let mx=-9,mn=9;
 for(let i=0;i<40;i++){const x=Math.max(0,Math.min(G-1,cx-r+Math.round(i*2*r/39)));perfil[i]=H[cy*G+x];mx=Math.max(mx,perfil[i]);mn=Math.min(mn,perfil[i]);}for(let i=0;i<40;i++)perfil[i]=1-(perfil[i]-mn)/(mx-mn+1e-9);}   // hondo = abierto
async function fonemas(evs){const cache={};for(const e of evs){if(e.fonemas)continue;const tx=(e.texto||'a').toLowerCase();if(!cache[tx]){const r=await Lector.readAsync(tx,{language:'es-MX',engine:'rules'});cache[tx]=r.words.flatMap(w=>w.phones);if(!cache[tx].length)cache[tx]=['a'];}e.fonemas=cache[tx];}return evs;}
(async()=>{const sem=P.semilla;
 if(quiero('cueva')){const t0=Date.now(),y=Cueva.render({dur:D,camaras:P.camaras,gotas:P.gotas,semilla:sem},SR);guardar2('cueva',y.L,y.R);console.log('  ',P.gotas.length,'gotas',(Date.now()-t0)+' ms');}
 if(quiero('katajjaq'))for(const lado of [0,1])guardar('katajjaq'+lado,Garganta.render({dur:D,perfil,largo:1.1,eventos:P.garganta.filter(e=>e.lado===lado),semilla:sem+lado},SR));
 if(quiero('bordon'))guardar('bordon',Garganta.render({dur:D,perfil,largo:2.2,eventos:P.bordon,semilla:sem+5},SR));
 if(quiero('aves'))guardar('aves',Pajaro.render({dur:D,eventos:P.aves,semilla:sem+6},SR));
})();
