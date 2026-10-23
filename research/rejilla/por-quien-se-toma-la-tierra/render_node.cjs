/* ¿Por quién se toma la tierra? — capas de node: la garganta de volcán (motor/, sobre la garganta de montaña de la copia fijada),
   los metales de Mulatu (sax de objeto.js; trompeta con sordina cup y trombón de metal.js, con growl en el colapso), el washint
   (la flauta de objeto.js), el tam-tam y las gotas de los lagos de la caldera. Mono 48 kHz a <carpeta>/<capa>.f32.
     node render_node.cjs <carpeta> [capa…] */
const fs=require('fs'),path=require('path');
const dir=process.argv[2],solo=process.argv.slice(3),P=JSON.parse(fs.readFileSync(path.join(dir,'partitura.json'),'utf8')),SR=48000,D=P.duracion;
const C=path.join(__dirname,P.instrumentos,'codigo/rejilla/research/rejilla/');
const Objeto=require(C+'objetos/motor/objeto.js'),Metal=require(C+'objetos/motor/metal.js'),Gong=require(C+'objetos/motor/gong.js'),Agua=require(C+'objetos/motor/agua.js');
const Garganta=require(C+'lo-que-tapa-la-traspuesta/motor/garganta.js'),GV=require('./motor/garganta_volcan.js'),Lector=require('../../../difonos/runtime/lector.js');
const hz=m=>440*2**((m-69)/12),quiero=n=>!solo.length||solo.includes(n);
const guardar=(n,y)=>{fs.writeFileSync(path.join(dir,n+'.f32'),Buffer.from(Float32Array.from(y).buffer));let p=0,s=0;for(const v of y){p=Math.max(p,Math.abs(v));s+=v*v;}
  console.log(n.padEnd(12),(y.length/SR).toFixed(1)+' s','pico',p.toFixed(3),'rms',Math.sqrt(s/y.length).toFixed(4));};
async function fonemas(evs){const cache={};for(const e of evs){if(e.fonemas)continue;const tx=(e.texto||'a').toLowerCase();
  if(!cache[tx]){const r=await Lector.readAsync(tx,{language:'es-MX',engine:'rules'});cache[tx]=r.words.flatMap(w=>w.phones);if(!cache[tx].length)cache[tx]=['a'];}e.fonemas=cache[tx];}return evs;}
/* un viento de objeto.js (sax o flauta) que toca una línea: f(t) por tramos con 12 ms de portamento, soplo con lengua y compuerta
   (sin soplo el lazo de la caña se queda oscilando: lo aprendimos en «Lo que tapa la traspuesta») */
function viento(notas,puro,corr){notas=notas.slice().sort((a,b)=>a.t-b.t);const N=notas.length,ini=notas.map(n=>n.t),S=Objeto.PURO[puro];
  const idx=t=>{let lo=0,hi=N-1;if(t<ini[0])return -1;while(lo<hi){const m=(lo+hi+1)>>1;if(ini[m]<=t)lo=m;else hi=m-1;}return lo;};
  const f=t=>{const k=idx(t);if(k<0)return hz(notas[0].m+corr);const a=notas[k];if(k>0){const u=(t-a.t)/.012,b=notas[k-1];if(u<1&&a.t-(b.t+b.dur)<.05)return hz(b.m+(a.m-b.m)*Math.max(0,u)+corr);}return hz(a.m+corr);};
  const soplo=t=>{const k=idx(t);let v=0;for(const j of [k-1,k]){if(j<0)continue;const n=notas[j],u=t-n.t;if(u<-.004||u>n.dur+.035)continue;let e=n.v||.85;if(u<.018)e*=.4+.6*Math.max(0,u)/.018;if(u>n.dur)e*=Math.max(0,1-(u-n.dur)/.035);v=Math.max(v,e);}return v;};
  const y=Objeto.render({dur:D,f,w:()=>S.w,soplo,pos:()=>S.pos,disp:()=>0,perdida:()=>S.perdida,brillo:()=>S.brillo,ruido:()=>S.ruido,vibrato:[5.2,.02],semilla:P.semilla},SR);
  let g=0;const sube=1-Math.exp(-1/(.002*SR)),baja=1-Math.exp(-1/(.08*SR));for(let i=0;i<y.length;i++){const m=soplo(i/SR)>0?1:0;g+=(m-g)*(m>g?sube:baja);y[i]*=g;}return y;}
(async()=>{const sem=P.semilla;
 if(quiero('garganta')){await fonemas(P.garganta);const perfiles=P.perfiles.map(([t,p])=>[t,Float32Array.from(p)]);
   const gv=GV.render({dur:D,perfiles,largo:2,eventos:P.garganta.filter(e=>!e.solo),caldera:P.caldera,brama:P.brama,fH:P.helmholtz.f_hz,semilla:sem},SR,Garganta);
   guardar('garganta',gv.voz);guardar('caldera',gv.caldera);
   guardar('garganta-cuello',Garganta.render({dur:D,perfiles,largo:1.2,eventos:P.garganta.filter(e=>e.solo),semilla:sem+1},SR));}   /* el cuello: sólo queda la garganta */
 if(quiero('metales')){const M=P.metales;
   guardar('sax',viento(M.filter(n=>n.ins==='sax'),'saxofon',.18));
   guardar('trompeta',Metal.render({dur:D,voz:'trompeta',sordina:'cup',notas:M.filter(n=>n.ins==='trompeta').map(n=>({t:n.t,dur:n.dur,m:n.m,v:n.v,tipo:'lengua'})),semilla:sem+2},SR));
   guardar('trombon',Metal.render({dur:D,voz:'trombon',sordina:'abierta',notas:M.filter(n=>n.ins==='trombon').map(n=>({t:n.t,dur:n.dur,m:n.m,v:n.v,tipo:n.growl?'growl':'lengua'})),semilla:sem+3},SR));}
 if(quiero('washint'))guardar('washint',viento(P.washint,'flauta',0));
 if(quiero('tamtam'))guardar('tamtam',Gong.render({dur:D,eventos:P.tamtam,semilla:sem+4},SR));
 if(quiero('lagos'))guardar('lagos',Agua.render({dur:D,eventos:P.lagos,semilla:sem+5},SR));
})();
