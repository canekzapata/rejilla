/* BATERÍA: pistas de golpes que suenan juntas. Una fila de pasos por pieza (clic: . → x → o → .), kit y perillas, y ritmos de partida.
   Los datos viven en piece.music.drums (musica.js los valida y los toca); aquí solo se editan. */
'use strict';
window.LecturaBateria=(()=>{
const el=(tag,text)=>{const n=document.createElement(tag);if(text)n.textContent=text;return n;};
const LARGOS=[16,32,48,64],CICLO={'.':'x',x:'o',o:'.'},PERILLAS=['kit','gain','tune','decay','drive','swing'];
/* Nombres cortos para la columna de la cuadrícula (el completo queda de título). */
const CORTO={openhat:'hi-hat abierto',crash:'crash',ride:'ride',spray:'spray 80s'};
const limpio=p=>String(p||'').replace(/[^xo.\-]/gi,'').toLowerCase().replace(/-/g,'.');
/* Una pista más corta que la cuadrícula se muestra repetida, que es como suena; al editarla se guarda ya extendida. */
const estira=(p,n)=>/[xo]/.test(p)?p.repeat(Math.ceil(n/p.length)).slice(0,n):'.'.repeat(n);
let pasos=null;
function largoDe(d){const max=Math.max(0,...Object.keys(LecturaMusica.DRUMS).map(k=>limpio(d[k]).length));return LARGOS.find(n=>n>=max)||64;}
function render(box,api){const M=LecturaMusica,m=api.get();box.replaceChildren();
 const ritmos=()=>{const s=el('select');for(const [k,r] of Object.entries(M.RITMOS)){const o=el('option','partir de: '+r.name);o.value=k;s.append(o);}const o=el('option','partir de: en blanco');o.value='';s.append(o);return s;};
 const nueva=k=>M.drums(k?M.RITMOS[k]:{});
 if(!m.drums){const head=el('div'),pick=ritmos(),add=el('button','＋ Armar batería');head.className='inst-head';pick.id='bat-ritmo';pick.setAttribute('aria-label','Ritmo de partida');add.id='bat-add';add.type='button';
  add.onclick=()=>{m.drums=nueva(pick.value);pasos=null;api.changed();render(box,api);};head.append(pick,add);
  box.append(head,el('p','Bombo, tarola, aro, palmas, hi-hats, platillos (con el spray ochentero), toms y cencerro: cada uno con su patrón, todos a la vez. Suena con la música encendida y ♩ > 0.'));return;}
 const d=m.drums;if(!pasos||pasos<largoDe(d))pasos=largoDe(d);
 const tools=el('div'),play=el('button','▶ Probar'),largo=el('select'),pick=ritmos(),load=el('button','Cargar ritmo'),del=el('button','Quitar batería');tools.className='inst-head';
 play.id='bat-play';largo.id='bat-pasos';pick.id='bat-ritmo';load.id='bat-load';del.id='bat-del';[play,load,del].forEach(b=>b.type='button');largo.setAttribute('aria-label','Pasos');pick.setAttribute('aria-label','Ritmo');
 LARGOS.forEach(n=>{const o=el('option',n+' pasos');o.value=n;largo.append(o);});largo.value=pasos;
 play.onclick=()=>api.audition();
 largo.onchange=()=>{const n=+largo.value;for(const k of Object.keys(M.DRUMS)){const p=limpio(d[k]);d[k]=/[xo]/.test(p)?estira(p,n):'';}pasos=n;api.changed();render(box,api);};
 load.onclick=()=>{m.drums=nueva(pick.value);pasos=null;api.changed();render(box,api);};
 del.onclick=()=>{delete m.drums;pasos=null;api.changed();render(box,api);};
 tools.append(play,largo,pick,load,del);box.append(tools);
 const T=api.tempo?.();if(!m.on||!T?.bpm){const w=el('p',!T?.bpm?'Para que suene en la pieza, ponle pulso (♩ > 0) y enciende la música. ▶ Probar suena de todos modos.':'Para que suene en la pieza, enciende la música. ▶ Probar suena de todos modos.');w.className='hint';w.id='bat-aviso';box.append(w);}
 const grid=el('div'),wrap=el('div');wrap.className='bat-wrap';grid.className='bat-grid';grid.id='bat-grid';grid.style.setProperty('--n',pasos);wrap.append(grid);
 for(const [k,label] of Object.entries(M.DRUMS)){const name=el('span',CORTO[k]||label);name.className='bat-name';name.title=label;grid.append(name);
  const fila=estira(limpio(d[k]),pasos);
  for(let i=0;i<pasos;i++){const c=el('button');c.type='button';c.className='bat-cell'+(i%4===0?' bat-pulso':'');c.dataset.v=fila[i];c.dataset.pieza=k;c.dataset.i=i;c.setAttribute('aria-label',label+', paso '+(i+1));
   c.onclick=()=>{let row=estira(limpio(d[k]),pasos);const v=CICLO[row[i]]||'x';row=row.slice(0,i)+v+row.slice(i+1);d[k]=/[xo]/.test(row)?row:'';c.dataset.v=v;api.changed();};grid.append(c);}}
 box.append(wrap);
 const fields=el('div');LecturaMateriales.inputs(fields,d,Object.fromEntries(PERILLAS.map(k=>[k,M.drumSchema[k]])),'bat-',()=>api.changed());box.append(fields);}
return {render};})();
