/* biblioteca de instrumentos · motor «objeto» (loop 02): los objetos que cantan de rejilla (modelado físico muestra por muestra:
   saxofón, flauta, barra, clarinete, cuerdas frotadas, trombón y trompeta con sordina, gong, piano preparado, pájaro, tambor que
   habla, waterphone, agua) tocados con una nota. Usa la COPIA de su código en codigo/rejilla/…/objetos/motor/.
   Y los instrumentos imposibles de «Lo que tapa la traspuesta» (19 oct; su copia en codigo/rejilla/…/lo-que-tapa-la-traspuesta/motor/,
   dicha en fisica.carpeta): la GARGANTA DE MONTAÑA (forma 'garganta': siringe de pájaro dentro de un tubo con la forma de un perfil
   del terreno; nota.fonemas = ['k','a'] la hace hablar) y el VIENTO que lee el terreno (forma 'viento': cada cresta silba; con la
   retícula estriada los silbidos caen en la clase de altura de la nota; devuelve mono con .L y .R estéreo).
   Node:      const O=require('./objetos.js'); const y=O.nota(K,{midi:62,vel:.8,dur:1.2},48000);   (Float32Array)
   Navegador: cargar antes la copia del módulo (define window.Objeto, window.Cuerda…) y pasar cargar=(K)=>window[K.fisica.api]. */
(function(root){'use strict';
const COPIA='codigo/rejilla/research/rejilla/objetos/motor/',carpeta=(K)=>K.fisica.carpeta||COPIA;
function cargarNode(K){const path=require('path');return require(path.join(__dirname,'..',carpeta(K),K.fisica.modulo));}
function nota(K,n,sr=48000,cargar=cargarNode){const A=cargar(K),S=K.fisica,dur=n.dur??1,v=n.vel??.8,m=n.midi,cola=S.cola??1;
 if(S.forma==='objeto'){const p=A.PURO[S.puro],C=A.curva,hz=x=>440*Math.pow(2,(x-69)/12);   /* como herramientas/demo.js: nota sostenida, ataque, cuerpo, apagado */
  const sop=[[0,0],[.04,p.soplo*1.15],[.15,p.soplo],[dur-.15,p.soplo],[dur-.05,0],[dur,0]];
  return A.render({dur:dur+.6,f:C(hz(m)),w:C(p.w),pos:C(p.pos),perdida:C(p.perdida),brillo:C(p.brillo),disp:C(p.disp),soplo:C(sop),ruido:C(p.ruido),golpes:S.puro==='golpe'?[[.02,.9*v/.8]]:[],vibrato:S.puro==='golpe'?null:[5,.004]},sr);}
 if(S.forma==='garganta'){const ev={t:.05,dur,nota:m,fonemas:n.fonemas||S.fonemas||['a'],v,aprende:S.aprende??.9,ronco:S.ronco||0};
  if(S.intervalo!=null)ev.nota2=m+S.intervalo;                  /* bifonía: las dos caras de la siringe en el mismo tubo */
  return A.render({dur:dur+cola,perfil:Float32Array.from(n.perfil||S.perfil),largo:S.largo||1,eventos:[ev],semilla:S.semilla||23},sr);}
 if(S.forma==='viento'){const V=S.vel||12,w=A.render({dur:dur+cola,perfiles:[[0,Float32Array.from(n.perfil||S.perfil)]],
   vel:[[0,V*.35],[.3*dur,V*(.6+.6*v)],[dur,V*.5],[dur+cola,0]],estria:[[0,S.estria??1]],escala:S.escala||[0],periodo:S.periodo||12,base:m,semilla:S.semilla||31},sr);
  const y=new Float32Array(w.L.length);for(let i=0;i<y.length;i++)y[i]=.5*(w.L[i]+w.R[i]);y.L=w.L;y.R=w.R;return y;}
 const ev=Object.assign({t:.05,m,v,dur},S.evento||{});if(S.m2!=null)ev.m2=m+S.m2;
 if(S.forma==='metal')return A.render(Object.assign({dur:dur+cola,notas:[ev]},S.control||{}),sr);
 const c=Object.assign({dur:dur+cola,eventos:[ev]},S.control||{});if(S.prep)c.prepara=()=>A.PREP[S.prep];
 return A.render(c,sr);}
const api={nota,COPIA,carpeta};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.InstrumentosObjeto=api;
})(typeof window!=='undefined'?window:globalThis);
