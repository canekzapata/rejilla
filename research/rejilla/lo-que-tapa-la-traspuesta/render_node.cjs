/* Lo que tapa la traspuesta — las capas de node: los instrumentos imposibles (la garganta de montaña y el viento, motor/) y
   los objetos que cantan de la copia fijada (sax, clarinete, chelo, piano preparado, trombón, gong, pájaros, agua) más la voz
   de agua (vozagua.js original: la copia no trae su G2P). La garganta pronuncia con el lector de Difonos (es-MX, reglas).
   Mono 48 kHz a <carpeta>/<capa>.f32; el viento sale estéreo (L,R entrelazados).
     node render_node.cjs <carpeta> [capa…] */
const fs=require('fs'),path=require('path');
const dir=process.argv[2],solo=process.argv.slice(3),P=JSON.parse(fs.readFileSync(path.join(dir,'partitura.json'),'utf8')),SR=48000,D=P.duracion;
const OBJ=path.join(__dirname,P.instrumentos,'codigo/rejilla/research/rejilla/objetos/motor/');
const Objeto=require(OBJ+'objeto.js'),Pajaro=require(OBJ+'pajaro.js'),Agua=require(OBJ+'agua.js'),Gong=require(OBJ+'gong.js'),Metal=require(OBJ+'metal.js'),
      Clarinete=require(OBJ+'clarinete.js'),Cuerda=require(OBJ+'cuerda.js'),Piano=require(OBJ+'piano.js');
const VozAgua=require('../objetos/motor/vozagua.js'),Lector=require('../../../difonos/runtime/lector.js');
const Garganta=require('./motor/garganta.js'),Viento=require('./motor/viento.js');
const hz=m=>440*2**((m-69)/12),quiero=n=>!solo.length||solo.includes(n);
const H=new Float32Array(fs.readFileSync(path.join(__dirname,'terreno/h-420048.f32')).buffer.slice(0)),G=360;
const fila=j=>{const p=new Float32Array(G);let mx=0;for(let i=0;i<G;i++){p[i]=H[j*G+i];mx=Math.max(mx,p[i]);}for(let i=0;i<G;i++)p[i]/=mx||1;return p;};
const perfiles=P.perfiles.map(([t,j])=>[t,fila(j)]);
const guardar=(n,y)=>{fs.writeFileSync(path.join(dir,n+'.f32'),Buffer.from(Float32Array.from(y).buffer));let p=0,s=0;for(const v of y){p=Math.max(p,Math.abs(v));s+=v*v;}
  console.log(n.padEnd(16),(y.length/SR).toFixed(1)+' s','pico',p.toFixed(3),'rms',Math.sqrt(s/y.length).toFixed(4));};

function sax(notas){                                   // igual que en «Cuento en siete»: una caña que no se detiene entre notas ligadas
  notas=notas.slice().sort((a,b)=>a.t-b.t);             // los cambios del IV se agregan después del tema: sin ordenar, la búsqueda binaria dejaba la caña soplando
  const N=notas.length,ini=notas.map(n=>n.t);
  const idx=t=>{let lo=0,hi=N-1;if(t<ini[0])return -1;while(lo<hi){const m=(lo+hi+1)>>1;if(ini[m]<=t)lo=m;else hi=m-1;}return lo;};
  const f=t=>{const k=idx(t);if(k<0)return hz(notas[0].m+.18);const a=notas[k];
    if(k>0){const u=(t-a.t)/.012,b=notas[k-1];if(u<1&&a.t-(b.t+b.dur)<.05)return hz(b.m+(a.m-b.m)*Math.max(0,u)+.18);}return hz(a.m+.18);};
  const soplo=t=>{const k=idx(t);let v=0;for(const j of [k-1,k]){if(j<0)continue;const n=notas[j],u=t-n.t;if(u<-.004||u>n.dur+.035)continue;
    let e=n.v||.85;if(n.lengua&&u<.018)e*=.4+.6*Math.max(0,u)/.018;if(u>n.dur)e*=Math.max(0,1-(u-n.dur)/.035);v=Math.max(v,e);}return v;};
  const S=Objeto.PURO.saxofon;
  const y=Objeto.render({dur:D,f,w:()=>[1,0,0],soplo,pos:()=>S.pos,disp:()=>0,perdida:()=>S.perdida,brillo:()=>S.brillo,ruido:()=>S.ruido,vibrato:[5.4,.025],semilla:P.semilla%9973},SR);
  // sin soplo, el lazo de la caña se queda oscilando solo (medido: −28 dB constante en los silencios largos): compuerta que
  // sigue al soplo, abre en 2 ms y cierra en 80 ms
  let g=0;const sube=1-Math.exp(-1/(.002*SR)),baja=1-Math.exp(-1/(.08*SR));
  for(let i=0;i<y.length;i++){const m=soplo(i/SR)>0?1:0;g+=(m-g)*(m>g?sube:baja);y[i]*=g;}
  return y;
}
async function fonemas(evs){                           // cada sílaba de la garganta → sus fonemas (lector de Difonos, español, reglas)
  const cache={};
  for(const e of evs){if(e.fonemas)continue;const tx=(e.texto||'a').toLowerCase();
    if(!cache[tx]){const r=await Lector.readAsync(tx,{language:'es-MX',engine:'rules'});cache[tx]=r.words.flatMap(w=>w.phones);if(!cache[tx].length)cache[tx]=['a'];}
    e.fonemas=cache[tx];}
  return evs;
}
(async()=>{
 const sem=P.semilla%9973;
 if(quiero('garganta')){await fonemas(P.garganta);
   for(const voz of ['montana','coro','solo']){const evs=P.garganta.filter(e=>e.voz===voz);if(!evs.length)continue;
     const largo=voz==='montana'?2:voz==='coro'?1.25:1;           // la montaña del tamaño de un cerro; el tenor del coro, una garganta grande
     guardar('garganta-'+voz,Garganta.render({dur:D,perfiles,largo,eventos:evs,semilla:sem+(voz.length)},SR));}}
 if(quiero('viento')){const v=Viento.render({dur:D,perfiles,...P.viento,semilla:sem+3},SR),o=new Float32Array(v.L.length*2);
   for(let i=0;i<v.L.length;i++){o[2*i]=v.L[i];o[2*i+1]=v.R[i];}fs.writeFileSync(path.join(dir,'viento.f32'),Buffer.from(o.buffer));console.log('viento (estéreo)');}
 if(quiero('sax'))guardar('sax',sax(P.sax));
 if(quiero('clarinete'))guardar('clarinete',Clarinete.render({dur:D,eventos:P.clarinete,semilla:sem+4},SR));
 if(quiero('chelo'))guardar('chelo',Cuerda.render({dur:D,instrumento:'chelo',eventos:P.chelo,semilla:sem+5},SR));
 if(quiero('piano'))guardar('piano',Piano.render({dur:D,eventos:P.piano,prepara:()=>Piano.PREP.goma,semilla:sem+6},SR));
 if(quiero('trombon'))guardar('trombon',Metal.render({dur:D,voz:'trombon',sordina:'harmon',notas:P.trombon,semilla:sem+7},SR));
 if(quiero('gong'))guardar('gong',Gong.render({dur:D,eventos:P.gong,semilla:sem+8},SR));
 if(quiero('aves')){guardar('aves',Pajaro.render({dur:D,eventos:P.aves.filter(a=>!a.coro),semilla:sem+9},SR));
                    guardar('aves-coro',Pajaro.render({dur:D,eventos:P.aves.filter(a=>a.coro),semilla:sem+10},SR));
                    guardar('siringa',Pajaro.render({dur:D,eventos:P.siringa,semilla:sem+11},SR));}
 if(quiero('agua'))guardar('agua',Agua.render({dur:D,eventos:P.agua,semilla:sem+12},SR));
 if(quiero('vozagua'))guardar('vozagua',VozAgua.render({dur:D,eventos:P.vozagua,semilla:sem+13},SR));
})();
