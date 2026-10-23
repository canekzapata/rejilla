/* biblioteca de instrumentos · motor «objeto» (loop 02): los objetos que cantan de rejilla (modelado físico muestra por muestra:
   saxofón, flauta, barra, clarinete, cuerdas frotadas, trombón y trompeta con sordina, gong, piano preparado, pájaro, tambor que
   habla, waterphone, agua) tocados con una nota. Usa la COPIA de su código en codigo/rejilla/…/objetos/motor/.
   Node:      const O=require('./objetos.js'); const y=O.nota(K,{midi:62,vel:.8,dur:1.2},48000);   (Float32Array)
   Navegador: cargar antes la copia del módulo (define window.Objeto, window.Cuerda…) y pasar cargar=(K)=>window[K.fisica.api]. */
(function(root){'use strict';
const COPIA='codigo/rejilla/research/rejilla/objetos/motor/';
function cargarNode(K){const path=require('path');return require(path.join(__dirname,'..',COPIA,K.fisica.modulo));}
function nota(K,n,sr=48000,cargar=cargarNode){const A=cargar(K),S=K.fisica,dur=n.dur??1,v=n.vel??.8,m=n.midi,cola=S.cola??1;
 if(S.forma==='objeto'){const p=A.PURO[S.puro],C=A.curva,hz=x=>440*Math.pow(2,(x-69)/12);   /* como herramientas/demo.js: nota sostenida, ataque, cuerpo, apagado */
  const sop=[[0,0],[.04,p.soplo*1.15],[.15,p.soplo],[dur-.15,p.soplo],[dur-.05,0],[dur,0]];
  return A.render({dur:dur+.6,f:C(hz(m)),w:C(p.w),pos:C(p.pos),perdida:C(p.perdida),brillo:C(p.brillo),disp:C(p.disp),soplo:C(sop),ruido:C(p.ruido),golpes:S.puro==='golpe'?[[.02,.9*v/.8]]:[],vibrato:S.puro==='golpe'?null:[5,.004]},sr);}
 const ev=Object.assign({t:.05,m,v,dur},S.evento||{});if(S.m2!=null)ev.m2=m+S.m2;
 if(S.forma==='metal')return A.render(Object.assign({dur:dur+cola,notas:[ev]},S.control||{}),sr);
 const c=Object.assign({dur:dur+cola,eventos:[ev]},S.control||{});if(S.prep)c.prepara=()=>A.PREP[S.prep];
 return A.render(c,sr);}
const api={nota,COPIA};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.InstrumentosObjeto=api;
})(typeof window!=='undefined'?window:globalThis);
