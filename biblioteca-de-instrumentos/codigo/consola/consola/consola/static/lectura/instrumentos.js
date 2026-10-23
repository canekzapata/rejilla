/* Editor de instrumentos inventados: recetas de síntesis (datos con rangos, no código) que cualquier voz puede tocar. */
'use strict';
window.LecturaInstrumentos=(()=>{let current=null;
const el=(tag,text)=>{const n=document.createElement(tag);if(text)n.textContent=text;return n;};
const slug=s=>String(s).normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,34)||'instrumento';
function renderRecipes(box,api){const M=LecturaMusica,m=api.get(),list=m.instruments;box.replaceChildren();
 if(!list.some(r=>r.id===current))current=list[0]?.id??null;
 const head=el('div'),pick=el('select'),tpl=el('select'),add=el('button','＋ Inventar');head.className='inst-head';pick.id='inst-pick';pick.setAttribute('aria-label','Instrumento inventado');tpl.id='inst-template';tpl.setAttribute('aria-label','Partir de');add.id='inst-add';add.type='button';add.disabled=list.length>=8;
 list.forEach(r=>{const o=el('option',r.name);o.value=r.id;pick.append(o);});pick.value=current??'';pick.hidden=!list.length;pick.onchange=()=>{current=pick.value;renderRecipes(box,api);};
 for(const [k,t] of Object.entries(M.TEMPLATES)){const o=el('option','partir de: '+t.name);o.value=k;tpl.append(o);}{const o=el('option','partir de: en blanco');o.value='';tpl.append(o);}
 add.onclick=()=>{const base=tpl.value?M.TEMPLATES[tpl.value]:{name:'instrumento nuevo',partials:[{}]};let id=slug(base.name),k=2;while(list.some(r=>r.id===id)||Object.hasOwn(M.INSTR,id))id=slug(base.name)+'-'+k++;
  list.push(M.normalize({...m,instruments:[{...JSON.parse(JSON.stringify(base)),id}],voices:[]}).instruments[0]);current=id;api.changed();renderRecipes(box,api);};
 head.append(pick,tpl,add);box.append(head);
 const r=list.find(x=>x.id===current);if(!r){box.append(el('p','Inventa un instrumento: una receta de ondas, envolvente, filtro, vibrato, FM y aire. Luego elígelo en la música de cualquier voz.'));return;}
 const tools=el('div'),play=el('button','▶ Probar'),del=el('button','Quitar instrumento');tools.className='inst-tools';play.id='inst-play';play.type='button';del.id='inst-del';del.type='button';
 play.onclick=()=>api.audition(r.id);
 del.onclick=()=>{m.voices.forEach(v=>{if(v.instrument===r.id)v.instrument='kalimba';});list.splice(list.indexOf(r),1);current=null;api.changed();renderRecipes(box,api);};
 tools.append(play,del);box.append(tools);
 const fields=el('div');LecturaMateriales.inputs(fields,r,M.recipeSchema,'rec-',()=>{r.name=String(r.name).slice(0,40);if(pick.selectedOptions[0])pick.selectedOptions[0].textContent=r.name;api.changed();});box.append(fields);
 r.partials.forEach((p,i)=>{const d=el('details');d.className='material-group';d.append(el('summary','Parcial '+(i+1)));LecturaMateriales.inputs(d,p,M.partialSchema,'par'+i+'-',()=>api.changed());
  if(r.partials.length>1){const x=el('button','Quitar parcial');x.type='button';x.onclick=()=>{r.partials.splice(i,1);api.changed();renderRecipes(box,api);};d.append(x);}box.append(d);});
 if(r.partials.length<6){const more=el('button','＋ Parcial');more.type='button';more.id='inst-partial';more.onclick=()=>{r.partials.push({wave:'sine',ratio:r.partials.length+1,gain:+(.5/(r.partials.length+1)).toFixed(2),detune:0});api.changed();renderRecipes(box,api);};box.append(more);}}
/* MUESTRAS: tus sonidos. Se detecta su nota (para afinarlos a la escala) o, si no tienen tono claro, suenan como golpe. */
const NOTE=['do','do♯','re','re♯','mi','fa','fa♯','sol','sol♯','la','la♯','si'],noteName=m=>NOTE[((m%12)+12)%12]+(Math.floor(m/12)-1);
function renderSamples(box,api){const M=LecturaMusica,m=api.get(),list=m.samples||[];box.replaceChildren();
 const head=el('div'),file=el('input'),add=el('button','＋ Subir sonido'),msg=el('p');head.className='inst-head';file.type='file';file.accept='audio/*';file.hidden=true;file.id='smp-file';add.id='smp-add';add.type='button';add.disabled=list.length>=LecturaMuestras.LIMITS.count;msg.id='smp-msg';msg.className='hint';
 add.onclick=()=>file.click();
 file.onchange=async()=>{const f=file.files[0];file.value='';if(!f)return;msg.textContent='Leyendo '+f.name+'…';try{const meta=await LecturaMuestras.add(f);const taken=new Set([...Object.keys(M.INSTR),...(m.instruments||[]).map(r=>r.id),...list.map(s=>s.id)]);let id=slug(meta.name),k=2;while(taken.has(id))id=slug(meta.name)+'-'+k++;
   const s={id,sha:meta.sha,name:meta.name,root:meta.root,mode:meta.mode,gain:.8,attack:.005,release:.3};m.samples=[...list,s];api.changed();renderSamples(box,api);
   document.getElementById('smp-msg').textContent=meta.detected?`«${s.name}»: ${meta.seconds} s, suena en ${noteName(s.root)}. Elígelo en la música de una voz (♪).`:`«${s.name}»: ${meta.seconds} s, sin un tono claro: suena como golpe, tal cual.`;}catch(e){msg.textContent=e.message;}};
 head.append(add,file);const title=el('div','MUESTRAS · tus sonidos');title.className='section-title';box.append(title,head,msg);
 if(!list.length){msg.textContent='Sube un sonido corto (hasta 2 MB y 12 s): una nota, un golpe, una voz. Afinado, cada nota de la escala lo acelera o lo frena desde su nota; golpe, suena tal cual.';return;}
 list.forEach((s,i)=>{const d=el('details');d.className='material-group';d.open=i===list.length-1;const sum=el('summary','♪ '+s.name+' · '+(s.mode==='afinado'?noteName(s.root):'golpe'));d.append(sum);
  const fields=el('div');LecturaMateriales.inputs(fields,s,M.sampleSchema,'smp'+i+'-',()=>{s.name=String(s.name).slice(0,40);s.root=Math.round(s.root);sum.textContent='♪ '+s.name+' · '+(s.mode==='afinado'?noteName(s.root):'golpe');api.changed();});d.append(fields);
  const tools=el('div'),play=el('button','▶ Probar'),del=el('button','Quitar sonido');tools.className='inst-tools';play.type=del.type='button';play.id='smp-play-'+i;del.id='smp-del-'+i;play.onclick=()=>api.audition(s.id);
  del.onclick=()=>{m.voices.forEach(v=>{if(v.instrument===s.id)v.instrument='kalimba';});m.samples=list.filter(x=>x!==s);if(!m.samples.length)delete m.samples;api.changed();renderSamples(box,api);};
  tools.append(play,del);d.append(tools);if(!LecturaMuestras.has(s.sha))d.append(el('p','Este sonido todavía no llega (se busca en tu navegador y en la consola).'));box.append(d);});}
function render(box,api){box.replaceChildren();const a=el('div'),b=el('div');a.id='inst-recetas';b.id='inst-muestras';box.append(a,b);renderRecipes(a,api);renderSamples(b,api);}
return {render,noteName};})();
