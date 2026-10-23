import {SR,TAU,source,apply,operations,note} from './motor.mjs';
import {exportWav} from './archivo.mjs';
const $=id=>document.getElementById(id), intervals=[0,2,3,5,7,9,10,12], names=['Do','Re','Mi♭','Fa','Sol','La','Si♭','Do'], letters='ASDFGHJK';
let context,active=new Set(),timers=[],lastMidi=48,lastAudio=null,generation=0;
const status=s=>$('status').textContent=s;
function settings(){return {giro:+$('theta').value*Math.PI,inclinacion:+$('chirp').value,estirar:+$('stretch').value,dispersion:+$('dispersion').value,referencia:+$('reference').value,cuerpo:$('body').value,orden:$('order').value};}
function canvas(id){const c=$(id),r=c.getBoundingClientRect(),d=devicePixelRatio||1;c.width=Math.round(r.width*d);c.height=Math.round(r.height*d);const g=c.getContext('2d');g.scale(d,d);return [g,r.width,r.height];}
function draw(){
 const o=settings(),z=source(lastMidi,o.cuerpo),w=apply(z,operations(o));
 $('thetaValue').textContent=(o.giro/Math.PI).toFixed(2)+' π';$('chirpValue').textContent=o.inclinacion.toFixed(2);$('stretchValue').textContent=o.estirar.toFixed(2)+' ×';$('dispersionValue').textContent=o.dispersion.toFixed(2);$('referenceValue').textContent=Math.round(o.referencia*100)+' %';
 const [g,W,H]=canvas('field'),pad=30;
 // Fixed scales keep expansion and movement visible. Thin offscreen ellipses
 // are clipped to the plot; axes never rescale a cancellation into a signal.
 const X=q=>pad+(q+24)/48*(W-2*pad),Y=p=>H-pad-(p+20)/52*(H-2*pad);
 g.strokeStyle='#344346';g.lineWidth=1;
 for(let q=-24;q<=24;q+=6){g.beginPath();g.moveTo(X(q),12);g.lineTo(X(q),H-pad);g.stroke();}
 for(let p=-18;p<=30;p+=6){g.beginPath();g.moveTo(pad,Y(p));g.lineTo(W-pad,Y(p));g.stroke();}
 g.font='10px monospace';g.fillStyle='#a4b3b2';g.fillText('−0.43 s',pad,H-8);g.fillText('+0.43 s',W-77,H-8);g.fillText('Δf',7,18);
 g.save();g.beginPath();g.rect(pad,8,W-2*pad,H-pad-8);g.clip();
 for(const [packets,color] of [[z,'#eebd80'],[w,'#73d6c3']])for(const p of packets){
  g.strokeStyle=color;g.globalAlpha=.65;g.lineWidth=1.25;g.beginPath();
  for(let j=0;j<=100;j++){const t=j/100*2*Math.PI,dx=2*Math.cos(t)/Math.sqrt(4*Math.PI*p.A[0]),dp=-p.A[1]*dx+2*Math.sqrt(p.A[0]/(4*Math.PI))*Math.sin(t);const x=X(p.q+dx),y=Y(p.p+dp);j?g.lineTo(x,y):g.moveTo(x,y);}g.stroke();
  g.globalAlpha=1;g.fillStyle=color;g.beginPath();g.arc(X(p.q),Y(p.p),2.5,0,2*Math.PI);g.fill();
 }g.restore();
 lastAudio=note({...o,midi:lastMidi});
 const [a,V,Q]=canvas('wave');a.strokeStyle='#344346';a.beginPath();a.moveTo(0,Q/2);a.lineTo(V,Q/2);a.stroke();a.strokeStyle='#73d6c3';a.beginPath();
 let peak=0;for(const s of lastAudio)peak=Math.max(peak,Math.abs(s));
 for(let i=0;i<V;i++){const start=Math.floor(i/V*lastAudio.length),end=Math.floor((i+1)/V*lastAudio.length);let lo=0,hi=0;for(let j=start;j<end;j++){lo=Math.min(lo,lastAudio[j]);hi=Math.max(hi,lastAudio[j]);}a.moveTo(i,Q/2-lo*Q*1.2);a.lineTo(i,Q/2-hi*Q*1.2);}a.stroke();
 $('level').textContent=peak<1e-10?'CANCELACIÓN':(20*Math.log10(Math.max(peak,1e-16))).toFixed(1)+' dBFS';
}
async function audio(){context??=new AudioContext();if(context.state!=='running')await context.resume();return context;}
function stop(){generation++;for(const t of timers)clearTimeout(t);timers=[];for(const n of active){try{n.stop()}catch{}}active.clear();document.querySelectorAll('.key.active').forEach(k=>k.classList.remove('active'));status('Detenido. Puedes seguir tocando.');}
function queue(ctx,data,when){const b=ctx.createBuffer(1,data.length,SR);b.copyToChannel(data,0);const n=ctx.createBufferSource();n.buffer=b;const gain=ctx.createGain();gain.gain.value=.78;n.connect(gain).connect(ctx.destination);active.add(n);n.onended=()=>active.delete(n);n.start(when);return n;}
async function play(index){const token=generation,ctx=await audio();if(token!==generation)return;lastMidi=+$('octave').value+intervals[index];draw();queue(ctx,lastAudio,ctx.currentTime+.01);const k=$('keys').children[index];k.classList.add('active');timers.push(setTimeout(()=>k.classList.remove('active'),220));status('Tocando '+names[index]+'. '+(+$('theta').value===2&&+$('reference').value===1?'Una vuelta: el testigo y la viajera se cancelan.':''));}
for(let i=0;i<8;i++){const b=document.createElement('button');b.className='key';b.innerHTML='<span>'+names[i]+'</span><small>'+letters[i]+'</small>';b.setAttribute('aria-label','Tocar '+names[i]+', tecla '+letters[i]);b.onclick=()=>play(i).catch(e=>status(e.message));$('keys').append(b);}
document.addEventListener('keydown',e=>{if(e.repeat||e.ctrlKey||e.altKey||e.metaKey||['INPUT','SELECT','TEXTAREA'].includes(e.target.tagName))return;const i=letters.indexOf(e.key.toUpperCase());if(i>=0){e.preventDefault();play(i).catch(e=>status(e.message));}if(e.code==='Space'){e.preventDefault();stop();}});
let pending;document.querySelectorAll('input,select').forEach(el=>el.addEventListener('input',()=>{cancelAnimationFrame(pending);pending=requestAnimationFrame(draw);}));
function preset(name){const values={origen:[0,0,1,0,0],barrido:[0,.65,1.35,.15,0],giro:[.5,0,1,0,0],hueco:[2,0,1,0,1],regreso:[4,0,1,0,1]}[name];['theta','chirp','stretch','dispersion','reference'].forEach((id,i)=>$(id).value=values[i]);$('order').value='inclinar-girar';draw();status(name==='hueco'?'Una vuelta + testigo: el silencio al tocar es intencional.':'Recorrido preparado. Toca una tecla o la frase.');}
document.querySelectorAll('[data-preset]').forEach(b=>b.onclick=()=>preset(b.dataset.preset));
$('reset').onclick=()=>{stop();$('body').value='cobre';$('octave').value='48';lastMidi=48;preset('origen');};$('stop').onclick=stop;
$('phrase').onclick=async()=>{try{stop();const token=generation,ctx=await audio();if(token!==generation)return;const o=settings(),start=ctx.currentTime+.06;let n=0;for(const i of [0,2,4,6,7,4,3,0]){const d=note({...o,midi:+$('octave').value+intervals[i]});queue(ctx,d,start+n*.44);n++;}status('Frase de ocho notas · recorrido actual.');}catch(e){status(e.message);}};
$('download').onclick=async()=>{try{const file=await exportWav(lastAudio,settings(),lastMidi),url=URL.createObjectURL(new Blob([file.buffer],{type:'audio/wav'})),a=document.createElement('a');a.href=url;a.download=file.name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);status('WAV guardado con su receta y un identificador nuevo.');}catch(e){status('No se pudo guardar: '+e.message);}};
window.addEventListener('resize',()=>{clearTimeout(pending);pending=setTimeout(draw,150);});
draw();
