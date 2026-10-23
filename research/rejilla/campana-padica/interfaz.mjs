import {WORKLET_SOURCE} from './paquete.mjs';
import {exportTake} from './archivo.mjs';
const $=id=>document.getElementById(id),letterKeys='ASDFGHJK',notes=[45,48,50,52,55,57,60,64],names=['La 2','Do 3','Re 3','Mi 3','Sol 3','La 3','Do 4','Mi 4'];
let context,node,initializing,zone=1,q=new Float64Array(64),actual=null,recording=false,demoRunning=false,lastEnergy=0;
const state=s=>$('status').textContent=s;
function params(){return Object.fromEntries(['fold','depth','tension','damping','pickup','midi'].map(k=>[k,+$(k).value]));}
function labels(){for(const [k,v] of Object.entries(params())){if($(k+'Value'))$(k+'Value').textContent=k==='fold'?Math.round(v*100)+' %':v.toFixed(k==='tension'?1:2);}$('velocityValue').textContent=Math.round(+$('velocity').value*100)+' %';$('selected').textContent='Zona '+zone;}
function canvas(id){const c=$(id),r=c.getBoundingClientRect(),d=devicePixelRatio||1;c.width=Math.round(r.width*d);c.height=Math.round(r.height*d);const g=c.getContext('2d');g.scale(d,d);return [g,r.width,r.height];}
function draw(){
 labels();const p=actual??params(),buttons=Array.from($('cells').children),[g,W,H]=canvas('links'),bounds=$('links').getBoundingClientRect();
 const coords=buttons.map(b=>{const r=b.getBoundingClientRect();return [r.left-bounds.left+r.width/2,r.top-bounds.top+r.height/2];});
 const d2=(a,b)=>{let n=Math.abs(a-b),k=0;while(n&&n%2===0){n/=2;k++;}return 2**(-k);};
 let norm=0;for(let k=0;k<6;k++)norm+=(32>>k)*2**((1+p.depth)*k);
 const links=[];for(let j=0;j<64;j++)if(j!==zone){const local=Math.abs(zone%8-j%8)+Math.abs((zone>>3)-(j>>3))===1?.25:0,weight=(1-p.fold)*local+p.fold*d2(zone,j)**(-1-p.depth)/norm;links.push([j,weight]);}
 links.sort((a,b)=>b[1]-a[1]);const max=links[0]?.[1]||1;
 for(const [j,weight] of links.slice(0,12)){if(weight<1e-7)continue;g.beginPath();g.moveTo(...coords[zone]);g.lineTo(...coords[j]);g.strokeStyle=p.fold>.5?'#c4b0ff':'#edb976';g.lineWidth=.5+weight/max*2;g.globalAlpha=.15+.55*weight/max;g.stroke();}g.globalAlpha=1;
 for(let i=0;i<64;i++){const amp=Math.min(1,Math.abs(q[i])*8),b=buttons[i];b.style.backgroundColor=q[i]>=0?`rgba(${Math.round(33+180*amp)},${Math.round(30+105*amp)},${Math.round(42+22*amp)},.92)`:`rgba(${Math.round(33+72*amp)},${Math.round(30+44*amp)},${Math.round(42+151*amp)},.92)`;b.classList.toggle('selected',i===zone);b.classList.toggle('mic',i%8===Math.round(p.pickup));}
 const [a,V,Q]=canvas('vibration');a.strokeStyle='#4b435c';a.beginPath();a.moveTo(0,Q/2);a.lineTo(V,Q/2);a.stroke();a.strokeStyle='#c4b0ff';a.lineWidth=1.4;a.beginPath();for(let i=0;i<64;i++){const y=Q/2-Math.max(-1,Math.min(1,q[i]*6))*(Q*.45);i?a.lineTo(i/63*V,y):a.moveTo(0,y);}a.stroke();
 $('activity').textContent=lastEnergy>.01?'RESONANDO':'EN REPOSO';
}
function sync(p){for(const k of ['fold','depth','tension','damping'])if(p[k]!==undefined)$(k).value=p[k];if(p.pickup!==undefined)$('pickup').value=p.pickup;if(p.midi!==undefined){const v=String(Math.round(p.midi));if(Array.from($('midi').options).some(o=>o.value===v))$('midi').value=v;}}
async function init(){
 if(node){if(context.state!=='running')await context.resume();return node;}
 if(initializing)return initializing;
 initializing=(async()=>{context=new AudioContext({latencyHint:'interactive'});await context.resume();const url=URL.createObjectURL(new Blob([WORKLET_SOURCE],{type:'text/javascript'}));try{await context.audioWorklet.addModule(url);}finally{URL.revokeObjectURL(url);}node=new AudioWorkletNode(context,'campana-padica',{numberOfInputs:0,numberOfOutputs:1,outputChannelCount:[2]});node.connect(context.destination);node.onprocessorerror=()=>state('El motor se detuvo. Recarga la página para volver a tocar.');
 node.port.onmessage=async({data:m})=>{
  if(m.type==='state'){q=m.q;actual=m.params;lastEnergy=m.energy;if(demoRunning)sync(m.params);requestDraw();}
  if(m.type==='recording'){recording=true;$('record').textContent='■ Terminar y guardar';$('record').classList.add('recording');state('Grabando la salida interna. Toca y pliega; vuelve a pulsar para guardar.');}
  if(m.type==='recorded'){recording=false;$('record').textContent='● Grabar toma';$('record').classList.remove('recording');try{if(!m.left.length)throw Error('La toma está vacía');const file=await exportTake(m,$('links').toDataURL('image/png')),url=URL.createObjectURL(new Blob([file.buffer],{type:'audio/wav'})),a=document.createElement('a');a.href=url;a.download=file.name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1500);state('Toma guardada: '+(m.left.length/m.sr).toFixed(1)+' s, con estado inicial y receta.');}catch(e){state('No se pudo guardar: '+e.message);}}
 };node.port.postMessage({type:'params',params:params()});return node;})();
 try{return await initializing;}catch(e){initializing=null;throw e;}
}
let pending=false;
function requestDraw(){if(!pending){pending=true;requestAnimationFrame(()=>{pending=false;draw();});}}
function manual(){demoRunning=false;actual=null;if(node)node.port.postMessage({type:'params',params:params(),cancel:true});draw();}
async function hit(i,midi){zone=i;if(midi!==undefined)$('midi').value=midi;const n=await init();demoRunning=false;n.port.postMessage({type:'params',params:params(),cancel:true});n.port.postMessage({type:'hit',zone,velocity:+$('velocity').value});state('Zona '+zone+' · pliega sus conexiones mientras resuena.');draw();}
for(let i=0;i<64;i++){const b=document.createElement('button');b.className='cell';b.textContent=i;b.setAttribute('aria-label','Golpear zona '+i);b.onclick=()=>hit(i).catch(e=>state(e.message));$('cells').append(b);}
for(let i=0;i<8;i++){const b=document.createElement('button');b.className='key';b.innerHTML='<span>'+names[i]+'</span><small>'+letterKeys[i]+'</small>';b.setAttribute('aria-label','Tocar '+names[i]+', tecla '+letterKeys[i]);b.onclick=()=>hit(zone,notes[i]).catch(e=>state(e.message));$('keys').append(b);}
document.querySelectorAll('input,select').forEach(e=>e.addEventListener('input',manual));
$('silence').onclick=()=>{demoRunning=false;node?.port.postMessage({type:'clear'});q.fill(0);lastEnergy=0;state('Cuerpo apagado.');draw();};
$('demo').onclick=async()=>{try{const n=await init();demoRunning=true;zone=9;n.port.postMessage({type:'demo'});state('Un solo golpe: cerca → parentesco → profundidad → regreso. Dura unos 8 segundos.');}catch(e){state(e.message);}};
$('record').onclick=async()=>{try{const n=await init();n.port.postMessage({type:recording?'record-stop':'record-start'});}catch(e){state(e.message);}};
$('reset').onclick=()=>{node?.port.postMessage({type:'clear'});demoRunning=false;sync({fold:0,depth:.7,tension:7,damping:.55,midi:48,pickup:0});$('velocity').value=.7;zone=1;q.fill(0);lastEnergy=0;manual();state('Cuerpo listo para un nuevo golpe.');};
const presets={cerca:{fold:0,depth:.7,tension:7,damping:.55},parentesco:{fold:1,depth:.7,tension:7,damping:.3,pickup:1},profunda:{fold:1,depth:1.8,tension:11,damping:.16,pickup:1}};
document.querySelectorAll('[data-preset]').forEach(b=>b.onclick=()=>{sync(presets[b.dataset.preset]);manual();state('Vecindad preparada. Golpea una zona o escucha cómo cambia la resonancia actual.');});
document.addEventListener('keydown',e=>{if(e.repeat||e.ctrlKey||e.altKey||e.metaKey||['INPUT','SELECT','TEXTAREA'].includes(e.target.tagName))return;const i=letterKeys.indexOf(e.key.toUpperCase());if(i>=0){e.preventDefault();hit(zone,notes[i]).catch(e=>state(e.message));}if(e.code==='Space'){e.preventDefault();$('silence').click();}});
window.addEventListener('resize',requestDraw);draw();
