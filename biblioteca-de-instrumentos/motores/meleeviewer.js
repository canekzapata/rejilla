/* biblioteca de instrumentos · motor «meleeviewer» (loop 03): toca una función de instrumento de una canción de «yoshi es un vector»
   dentro de su escenario (codigo/meleeviewer/escenarios/<canción>.js: las declaraciones que usa, tal cual; ctx y salida se dan).
   La nota se traduce a los parámetros de cada función por su nombre (t, n, notes, dur, vel/v, p…).

   await InstrumentosMelee.tocar(ctx, destino, ficha, {t, midi, vel, dur}, {fuente})      fuente(ruta) → texto del escenario
   En el navegador, fuente por omisión = fetch relativo a la biblioteca (BASE). En node no hay Web Audio: se usa en el navegador. */
(function(root){'use strict';
const ESC=new WeakMap();let BASE='';
async function escenario(ctx,destino,K,fuente){let porCtx=ESC.get(ctx);if(!porCtx){porCtx=new Map();ESC.set(ctx,porCtx);}
 const clave=K.fisica.escenario;let e=porCtx.get(clave);
 if(!e){const src=await (fuente||(r=>fetch(BASE+r).then(x=>{if(!x.ok)throw Error('no encontré '+r);return x.text();})))(clave);
  const salida=ctx.createGain();salida.connect(destino);const fab=(0,eval)(src);e={fns:await fab(ctx,salida,{}),salida};porCtx.set(clave,e);}
 return e;}
/* cada parámetro por su nombre: lo que la nota dice, o lo que la función trae por omisión (undefined) */
function argumentos(params,n){const m=n.midi,acorde=[m,m+3,m+7,m+10];const dur=n.dur??.8,vel=n.vel??.8;
 return params.map(p=>({t:n.t,t0:n.t,t1:n.t+dur,n:m,root:m,note:m,midi:m,notes:acorde,notas:acorde,dur,d:dur,vel,v:vel,p:0,open:false,apagada:false,slap:false})[p]);}
async function tocar(ctx,destino,K,n,op={}){const e=await escenario(ctx,destino,K,op.fuente),fn=e.fns[K.fisica.funcion];if(!fn)throw Error('el escenario no trae '+K.fisica.funcion);
 const nota={t:n.t??ctx.currentTime,midi:n.midi??60,vel:n.vel??.8,dur:n.dur??.8};return fn(...argumentos(K.fisica.params,nota));}
const api={tocar,argumentos,base:b=>{BASE=b;}};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.InstrumentosMelee=api;
})(typeof window!=='undefined'?window:globalThis);
