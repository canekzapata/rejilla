/* La lluvia que hizo los cráteres — capas de node: los cráteres (motor/crater.js), una capa por familia de tamaño (los dos complejos,
   medianos, chicos, diminutos y el gran impacto); la garganta del kiai y el viento como shakuhachi (garganta.js y viento.js de la
   copia fijada de la biblioteca), los dos con la forma de un corte por el cráter más grande. Estéreo 48 kHz (L,R entrelazados).
     node render_node.cjs <carpeta> [capa…] */
const fs=require('fs'),path=require('path');
const dir=process.argv[2],solo=process.argv.slice(3),P=JSON.parse(fs.readFileSync(path.join(dir,'partitura.json'),'utf8')),SR=48000,D=P.duracion;
const C=path.join(__dirname,P.instrumentos,'codigo/rejilla/research/rejilla/lo-que-tapa-la-traspuesta/motor/');
const Crater=require('./motor/crater.js'),Garganta=require(C+'garganta.js'),Viento=require(C+'viento.js'),Lector=require('../../../difonos/runtime/lector.js');
const quiero=n=>!solo.length||solo.includes(n);
const stats=(n,y,est)=>{let p=0,s=0;for(const v of y){p=Math.max(p,Math.abs(v));s+=v*v;}console.log(n.padEnd(12),est?'(estéreo)':'',(y.length/SR/(est?2:1)).toFixed(1)+' s','pico',p.toFixed(3),'rms',Math.sqrt(s/y.length).toFixed(4));};
const guardar=(n,y)=>{fs.writeFileSync(path.join(dir,n+'.f32'),Buffer.from(Float32Array.from(y).buffer));stats(n,y);};
const guardar2=(n,L,R)=>{const o=new Float32Array(L.length*2);for(let i=0;i<L.length;i++){o[2*i]=L[i];o[2*i+1]=R[i];}fs.writeFileSync(path.join(dir,n+'.f32'),Buffer.from(o.buffer));stats(n,o,1);};
// un corte por el cráter más grande (el perfil del tazón con su pico central)
const H=new Float32Array(fs.readFileSync(path.join(__dirname,'terreno','h-18.f32')).buffer.slice(0)),G=360,big=P.tambores[P.familias.complejo[0]];
const perfil=new Float32Array(48);{const cy=Math.round(big.v*(G-1)),cx=Math.round(big.u*(G-1)),r=Math.round(big.D/(P.terreno.match(/[\d.]+ km/)?parseFloat(P.terreno.match(/([\d.]+) km/)[1])*1000:9000)*G*1.4);
 let mx=0,mn=9;for(let i=0;i<48;i++){const x=Math.max(0,Math.min(G-1,cx-r+Math.round(i*2*r/47)));perfil[i]=H[cy*G+x];mx=Math.max(mx,perfil[i]);mn=Math.min(mn,perfil[i]);}for(let i=0;i<48;i++)perfil[i]=(perfil[i]-mn)/(mx-mn+1e-9);}
async function fonemas(evs){const cache={};for(const e of evs){if(e.fonemas)continue;const tx=(e.texto||'a').toLowerCase();if(!cache[tx]){const r=await Lector.readAsync(tx,{language:'es-MX',engine:'rules'});cache[tx]=r.words.flatMap(w=>w.phones);if(!cache[tx].length)cache[tx]=['a'];}e.fonemas=cache[tx];}return evs;}
(async()=>{const sem=P.semilla;
 for(const fam of ['complejo','mediano','chico','diminuto','grande'])if(quiero(fam)){const t0=Date.now(),y=Crater.render({dur:D,tambores:P.tambores,golpes:P.golpes[fam],K:P.K,semilla:sem+fam.length},SR);guardar2('crater-'+fam,y.L,y.R);console.log('  ',fam,P.golpes[fam].length,'golpes',(Date.now()-t0)+' ms');}
 if(quiero('garganta')){await fonemas(P.garganta);guardar('garganta',Garganta.render({dur:D,perfil,largo:1.4,eventos:P.garganta,semilla:sem},SR));}
 if(quiero('viento')){const v=Viento.render({dur:D,perfiles:[[0,perfil]],...P.viento,semilla:sem+1},SR);guardar2('viento',v.L,v.R);}
})();
