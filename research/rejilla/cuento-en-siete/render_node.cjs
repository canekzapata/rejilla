/* Cuento en siete — capas de modelado físico (objetos que cantan, de la copia fijada de la biblioteca): el saxofón (objeto.js,
   caña), los pájaros de siringe, el agua, el waterphone, el gong, el trombón (metal.js), el tambor que habla, la barra (objeto.js,
   golpe) y la voz de agua (vozagua.js, que canta la contralto del coro). Mono, 48 kHz, a <carpeta>/<capa>.f32.
     node render_node.cjs <carpeta> [capa…] */
const fs=require('fs'),path=require('path');
const dir=process.argv[2],solo=process.argv.slice(3),P=JSON.parse(fs.readFileSync(path.join(dir,'partitura.json'),'utf8')),SR=48000,D=P.duracion;
const OBJ=path.join(__dirname,P.instrumentos,'codigo/rejilla/research/rejilla/objetos/motor/');
const Objeto=require(OBJ+'objeto.js'),Pajaro=require(OBJ+'pajaro.js'),Agua=require(OBJ+'agua.js'),Waterphone=require(OBJ+'waterphone.js'),
      Gong=require(OBJ+'gong.js'),Metal=require(OBJ+'metal.js'),Tambor=require(OBJ+'tambor.js');
const VozAgua=require('../objetos/motor/vozagua.js');        // la original: la copia no trae su G2P (vendor/difonos-g2p)
const hz=m=>440*2**((m-69)/12);
const guardar=(n,y)=>{fs.writeFileSync(path.join(dir,n+'.f32'),Buffer.from(Float32Array.from(y).buffer));let p=0,s=0;for(const v of y){p=Math.max(p,Math.abs(v));s+=v*v;}
  console.log(n.padEnd(14),(y.length/SR).toFixed(1)+' s','pico',p.toFixed(3),'rms',Math.sqrt(s/y.length).toFixed(4));};
const quiero=n=>!solo.length||solo.includes(n);

/* el saxofón: una sola caña que no se detiene entre notas ligadas. f(t) por tramos con 12 ms de portamento (el dedo cambia
   la llave, el aire sigue); la lengua es una caída del soplo de 18 ms al empezar la nota; la nota fantasma sopla menos.
   +18 cents: la sonda midió el modelo un poco bajo en este registro. */
function sax(notas){
  const N=notas.length,ini=notas.map(n=>n.t);
  const idx=t=>{let lo=0,hi=N-1;if(t<ini[0])return -1;while(lo<hi){const m=(lo+hi+1)>>1;if(ini[m]<=t)lo=m;else hi=m-1;}return lo;};
  const f=t=>{const k=idx(t);if(k<0)return hz(notas[0].m+.18);const a=notas[k];
    if(k>0){const u=(t-a.t)/.012,b=notas[k-1];if(u<1&&a.t-(b.t+b.dur)<.05)return hz(b.m+(a.m-b.m)*Math.max(0,u)+.18);}return hz(a.m+.18);};
  const soplo=t=>{const k=idx(t);let v=0;for(const j of [k-1,k]){if(j<0)continue;const n=notas[j],u=t-n.t;if(u<-.004||u>n.dur+.035)continue;
    let e=n.v;if(n.lengua&&u<.018)e*=.4+.6*Math.max(0,u)/.018;if(u>n.dur)e*=Math.max(0,1-(u-n.dur)/.035);v=Math.max(v,e);}return v;};
  const S=Objeto.PURO.saxofon;
  return Objeto.render({dur:D,f,w:()=>[1,0,0],soplo,pos:()=>S.pos,disp:()=>0,perdida:()=>S.perdida,brillo:()=>S.brillo,ruido:()=>S.ruido,vibrato:[5.4,.025],semilla:P.semilla},SR);
}
/* la barra: el mismo lazo, golpeado (w = golpe), afinado a la nota de cada golpe */
function barra(golpes){
  const g=golpes.slice().sort((a,b)=>a.t-b.t),G=Objeto.PURO.golpe;
  const f=t=>{let m=g[0].m;for(const x of g){if(x.t<=t+.001)m=x.m;else break;}return hz(m);};
  return Objeto.render({dur:D,f,w:()=>[0,0,1],soplo:()=>0,pos:()=>G.pos,disp:()=>G.disp,perdida:()=>G.perdida,brillo:()=>G.brillo,ruido:()=>0,golpes:g.map(x=>[x.t,x.v]),t60:()=>2.2,semilla:P.semilla+5},SR);
}
(async()=>{
 if(quiero('sax'))guardar('sax',sax(P.sax));
 if(quiero('aves')){guardar('aves',Pajaro.render({dur:D,eventos:P.aves.filter(a=>!a.coro),semilla:P.semilla},SR));
                    guardar('aves-coro',Pajaro.render({dur:D,eventos:P.aves.filter(a=>a.coro),semilla:P.semilla+9},SR));}
 if(quiero('agua'))guardar('agua',Agua.render({dur:D,eventos:P.agua,semilla:P.semilla+1},SR));
 if(quiero('waterphone'))guardar('waterphone',Waterphone.render({dur:D,eventos:P.waterphone,semilla:P.semilla+2},SR));
 if(quiero('gong'))guardar('gong',Gong.render({dur:D,eventos:P.gong,semilla:P.semilla+3},SR));
 if(quiero('trombon'))guardar('trombon',Metal.render({dur:D,voz:'trombon',sordina:'plunger',wah:P.wah,notas:P.trombon,semilla:P.semilla+4},SR));
 if(quiero('tambor'))guardar('tambor',Tambor.render({dur:D,eventos:P.tambor,semilla:P.semilla+6},SR));
 if(quiero('barra'))guardar('barra',barra(P.golpes_barra));
 if(quiero('vozagua'))guardar('vozagua',VozAgua.render({dur:D,eventos:P.vozagua,semilla:P.semilla+7},SR));
})();
