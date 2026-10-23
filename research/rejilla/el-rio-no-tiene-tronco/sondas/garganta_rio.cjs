// sonda: cinco vocales con siringe y con ruido; con brazos del delta y sin ellos (la garganta de montaña)
const fs=require('fs'),G=require('../motor/garganta_rio.js'),D=JSON.parse(fs.readFileSync(__dirname+'/../terreno/delta.json'));
const perfil=Float32Array.from(D.perfil_rio),brazos=D.brazos.map(b=>({secciones:b.secciones,area:2,pan:b.pan}));
for(const [nom,conBr,fuente] of [['delta',1,null],['solo',0,null],['delta-ruido',1,'ruido']]){const ev=[];let t=.1;
 for(const v of ['a','e','i','o','u']){ev.push({t,dur:1.4,nota:50,fonemas:[v],v:.6,aprende:1});t+=1.6;}
 const y=G.render({dur:t+.4,perfil,largo:1,brazos:conBr?brazos:[],eventos:ev,fuente},48000);
 const o=new Float32Array(y.L.length*2);for(let i=0;i<y.L.length;i++){o[2*i]=y.L[i];o[2*i+1]=y.R[i];}fs.writeFileSync(__dirname+'/gr-'+nom+'.f32',Buffer.from(o.buffer));
 let nan=0;for(const v of y.L)if(!Number.isFinite(v))nan++;console.log(nom,'ok',(y.L.length/48000).toFixed(1),'s nan',nan);}
