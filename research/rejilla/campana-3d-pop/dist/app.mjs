import * as THREE from './vendor/three.module.js';
import {makeBody,poses,chamberCenter,PALETTE} from './forma.mjs';
import {INITIAL,readRoute,encodeRoute,audioParams} from './ruta.mjs';
import {AUDIO_SOURCE} from './audio/paquete.mjs';
import {postcard} from './postal.mjs';
import {SONGS,songById} from './canciones.mjs';
import {SpectralPetals} from './espectros.mjs';
import {SpatialListening} from './audio/espacio.mjs';
const $=s=>document.getElementById(s),canvas=$('world');
let cfg=readRoute(location.hash),actual={...cfg},rms=Array(64).fill(0),ctx,node,gain,analyser,audioPromise,muted=false,capturing=false,transport=null,lastUISync=0,space,lastSpaceUpdate=0,expectedScoreId=null;
let reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;$('reduced').checked=reduced;
const renderer=new THREE.WebGLRenderer({canvas,antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.setSize(innerWidth,innerHeight);renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=.85;
const scene=new THREE.Scene();scene.background=new THREE.Color('#fff0e6');scene.fog=new THREE.Fog('#fff0e6',17,45);
const camera=new THREE.PerspectiveCamera(39,innerWidth/innerHeight,.03,100);
scene.add(new THREE.HemisphereLight('#fff9ec','#a56bca',1.3));
const key=new THREE.DirectionalLight('#fff8e8',3.2);key.position.set(-4,7,6);key.castShadow=true;key.shadow.mapSize.set(1024,1024);key.shadow.camera.left=-5;key.shadow.camera.right=5;key.shadow.camera.top=5;key.shadow.camera.bottom=-5;key.shadow.bias=-.001;scene.add(key);
const fill=new THREE.DirectionalLight('#9ffeff',1.4);fill.position.set(4,1,-3);scene.add(fill);
const studio=new THREE.Scene();studio.background=new THREE.Color('#fff7ee');for(const [color,x,y,z,sx,sy,sz] of [['#ffffff',-4,5,4,4,4,.1],['#ff90c8',5,0,0,.1,7,7],['#a0f6ed',0,3,-5,8,3,.1]]){const panel=new THREE.Mesh(new THREE.BoxGeometry(sx,sy,sz),new THREE.MeshBasicMaterial({color}));panel.position.set(x,y,z);studio.add(panel);}const pmrem=new THREE.PMREMGenerator(renderer);const env=pmrem.fromScene(studio,.03);scene.environment=env.texture;scene.environmentIntensity=.65;pmrem.dispose();
const materials=PALETTE.map(color=>new THREE.MeshPhysicalMaterial({color,roughness:.22,metalness:.04,clearcoat:1,clearcoatRoughness:.13,side:THREE.DoubleSide}));
const body=makeBody(materials,new THREE.MeshStandardMaterial({color:'#ce7540',metalness:.92,roughness:.2}));scene.add(body.root);
const petals=new SpectralPetals(scene,camera);
const floor=new THREE.Mesh(new THREE.CircleGeometry(12,96),new THREE.MeshStandardMaterial({color:'#f4bed0',roughness:.8}));floor.rotation.x=-Math.PI/2;floor.position.y=-2.72;floor.receiveShadow=true;scene.add(floor);
const ring=new THREE.Mesh(new THREE.TorusGeometry(3.15,.017,8,100),new THREE.MeshStandardMaterial({color:'#f5298d',roughness:.35}));ring.rotation.x=Math.PI/2;ring.position.y=-2.7;scene.add(ring);
let theta=.53,phi=1.15,radius=10,target=new THREE.Vector3(0,.05,0),currentRadius=10,currentTarget=target.clone(),visualFold=cfg.fold;
function view(){if(cfg.inside){target=chamberCenter(cfg.pickup);theta=cfg.pickup&2?.08:Math.PI+.08;phi=1.28;radius=1.45;}else{target=new THREE.Vector3(0,.05,0);theta=.53;phi=1.15;radius=Math.max(12.8,8.5/(innerWidth/innerHeight));}}
function historySave(push=false){history[push?'pushState':'replaceState']({},'',encodeRoute(cfg));sync();}
function sync(){for(const k of ['fold','depth','tension','damping']){$(k).value=cfg[k];$(k+'Value').textContent=k==='fold'?Math.round(cfg[k]*100)+' %':Number(cfg[k]).toFixed(2);}const displayPitch=Math.round(cfg.midi);if(![...$('midi').options].some(o=>+o.value===displayPitch)){const o=new Option('MIDI '+displayPitch,displayPitch);$('midi').add(o);}$('midi').value=displayPitch;$('enter').innerHTML=cfg.inside?'OUTSIDE<br>↙':'INSIDE<br>↗';$('position').textContent='chamber '+String(cfg.pickup+1).padStart(2,'0')+' · '+(cfg.inside?'inside':'outside')+' · '+($('spatial').checked?'spatial':'original');for(const a of $('families').querySelectorAll('a')){const family=+a.dataset.family;a.setAttribute('aria-current',String(family===cfg.pickup));a.href=encodeRoute({...cfg,pickup:family,inside:true});}}
for(let k=0;k<8;k++){const a=document.createElement('a');a.style.background=PALETTE[k];a.dataset.family=k;a.setAttribute('aria-label','Enter family '+(k+1));a.addEventListener('click',e=>{e.preventDefault();cfg.pickup=k;cfg.inside=true;listenFamily();view();historySave(true);});$('families').lastElementChild.append(a);}
function sendParams(){const wasScore=expectedScoreId!==null;expectedScoreId=null;if(wasScore)$('status').textContent='Free play · the bell keeps ringing.';actual={...cfg};node?.port.postMessage({type:'params',params:audioParams(cfg),cancel:true});transport=null;updatePlayer();}
function listenFamily(){actual.pickup=cfg.pickup;node?.port.postMessage({type:'params',params:{pickup:cfg.pickup},cancel:false});}
function clock(t){return Math.floor(t/60)+':'+String(Math.floor(t%60)).padStart(2,'0');}
function updatePlayer(){
 $('nowPlaying').hidden=!transport;
 for(const button of $('songList').querySelectorAll('button'))button.setAttribute('aria-pressed',String(button.dataset.id===transport?.id));
 if(!transport)return;
 $('pieceTitle').textContent=songById(transport.id)?.title??'';
 $('pieceClock').textContent=clock(transport.elapsed)+' / '+clock(transport.duration)+(transport.ended?' · finished':transport.playing?'':' · paused');
 $('pieceProgress').max=transport.duration;$('pieceProgress').value=transport.elapsed;
 $('togglePlay').textContent=transport.ended?'↻':transport.playing?'Ⅱ':'▶';$('togglePlay').setAttribute('aria-label',transport.ended?'Replay piece':transport.playing?'Pause piece':'Resume piece');
}
async function audio(){
 if(!audioPromise)audioPromise=(async()=>{
  ctx=new AudioContext({latencyHint:'interactive'});const url=URL.createObjectURL(new Blob([AUDIO_SOURCE],{type:'text/javascript'}));
  try{await ctx.audioWorklet.addModule(url);}finally{URL.revokeObjectURL(url);}
  node=new AudioWorkletNode(ctx,'otra-distancia',{numberOfOutputs:9,outputChannelCount:[2,1,1,1,1,1,1,1,1]});gain=ctx.createGain();gain.gain.value=muted?0:.9;
  analyser=ctx.createAnalyser();analyser.fftSize=4096;analyser.smoothingTimeConstant=.08;analyser.minDecibels=-86;analyser.maxDecibels=-20;
  space=new SpatialListening(ctx);space.connect(node);space.setEnabled($('spatial').checked,true);updateAcoustics(true);space.output.connect(analyser);analyser.connect(gain);gain.connect(ctx.destination);
  node.port.onmessage=({data:s})=>{
   if(s.type==='strike'){petals.strike(s.region,performance.now()/1000);cfg.region=s.region;return;}
   if(s.type!=='state')return;rms=s.rms;actual=s.params;transport=s.transport?.id===expectedScoreId?s.transport:null;
   Object.assign(canvas.dataset,{frame:s.frame,hits:s.hits,limited:s.limitedFrames,energy:s.energy,piece:transport?.id??'',elapsed:transport?.elapsed??0,playing:transport?.playing??false});
   if(transport)Object.assign(cfg,s.params);
   if(performance.now()-lastUISync>120){lastUISync=performance.now();if(transport)sync();updatePlayer();}
  };
  node.onprocessorerror=()=>{$('status').textContent='Audio interrupted. Reload to play again.';};
  node.port.postMessage({type:'params',params:audioParams(cfg)});canvas.dataset.audio='active';
 })();
 await audioPromise;await ctx.resume();
}
async function playSong(id){
 try{await audio();const song=songById(id);expectedScoreId=id;node.port.postMessage({type:'play',id});transport={id,elapsed:0,duration:song.duration,playing:true,ended:false};updatePlayer();$('songsPanel').close();$('status').textContent=song.title+' · step inside or strike along.';}
 catch(e){$('status').textContent='Could not start audio: '+e.message;}
}
for(const [i,song] of SONGS.entries()){
 const button=document.createElement('button');button.dataset.id=song.id;button.innerHTML='<small>'+String(i+1).padStart(2,'0')+'</small><strong>'+song.title+'</strong><small>'+clock(song.duration)+'</small>';button.setAttribute('aria-pressed','false');button.onclick=()=>playSong(song.id);$('songList').append(button);
}
$('listen').onclick=()=>$('songsPanel').showModal();$('closeSongs').onclick=()=>$('songsPanel').close();
$('togglePlay').onclick=()=>{if(!transport)return;if(transport.ended)playSong(transport.id);else node?.port.postMessage({type:transport.playing?'pause':'resume'});};
$('stopPiece').onclick=()=>{expectedScoreId=null;node?.port.postMessage({type:'stop'});transport=null;updatePlayer();$('status').textContent='Free play · strike a plate.';};
async function hit(region=cfg.region){try{await audio();cfg.region=region;node.port.postMessage({type:'hit',region,velocity:.78});$('status').textContent='Plate '+String(region+1).padStart(2,'0')+' · drag to fold its resonance';historySave();}catch(e){$('status').textContent='Could not start audio: '+e.message;}}
for(const k of ['fold','depth','tension','damping'])$(k).addEventListener('input',()=>{cfg[k]=+$(k).value;sendParams();historySave();});$('midi').onchange=()=>{cfg.midi=+$('midi').value;sendParams();historySave();};$('reduced').onchange=()=>reduced=$('reduced').checked;
$('spatial').onchange=()=>{space?.setEnabled($('spatial').checked);sync();};
$('enter').onclick=()=>{cfg.inside=!cfg.inside;listenFamily();view();historySave(true);};$('help').onclick=()=>$('panel').showModal();$('close').onclick=()=>$('panel').close();
$('mute').onclick=()=>{muted=!muted;if(gain)gain.gain.setTargetAtTime(muted?0:.9,ctx.currentTime,.025);$('mute').textContent=muted?'sound ○':'sound ●';$('mute').setAttribute('aria-pressed',muted);};
$('reset').onclick=()=>{cfg={...INITIAL};sendParams();view();historySave(true);};$('copy').onclick=async()=>{historySave();try{await navigator.clipboard.writeText(location.href);$('captureStatus').textContent='Place copied. The link keeps its shape and family.';}catch{$('captureStatus').textContent='Copy this page address to return here.';}};
let postalURL;async function photograph(){capturing=true;const size=renderer.getSize(new THREE.Vector2()),ratio=renderer.getPixelRatio(),aspect=camera.aspect;try{renderer.setPixelRatio(1);renderer.setSize(1200,630,false);camera.aspect=1200/630;camera.updateProjectionMatrix();renderer.render(scene,camera);const png=await new Promise(resolve=>canvas.toBlob(resolve,'image/png'));const shot=await postcard(png,{...cfg,rms,transport,analysis:{fftSize:4096,rangeHz:[45,6000],mix:'post-spatial stereo to mono'},spatialListening:space?.state??null,camera:{position:camera.position.toArray(),target:currentTarget.toArray()}});if(postalURL)URL.revokeObjectURL(postalURL);postalURL=URL.createObjectURL(shot.blob);const a=$('postal');a.href=postalURL;a.download=shot.filename;a.hidden=false;a.click();$('captureStatus').textContent='1200 × 630 postcard, with its recipe inside the PNG.';}finally{renderer.setPixelRatio(ratio);renderer.setSize(size.x,size.y,false);camera.aspect=aspect;camera.updateProjectionMatrix();capturing=false;}}
$('photo').onclick=()=>photograph().catch(e=>{$('captureStatus').textContent='Could not save: '+e.message;});
function restore(){cfg=readRoute(location.hash);sendParams();view();sync();}addEventListener('popstate',restore);addEventListener('hashchange',restore);
const ray=new THREE.Raycaster(),pointer=new THREE.Vector2();function pick(e){const rect=canvas.getBoundingClientRect();pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);ray.setFromCamera(pointer,camera);return ray.intersectObjects(body.parts.map(p=>p.mesh))[0]?.object.userData.region;}
let drag;canvas.addEventListener('pointerdown',e=>{canvas.focus();drag={id:e.pointerId,x:e.clientX,y:e.clientY,fold:cfg.fold,theta,phi,region:e.shiftKey?undefined:pick(e),moved:false};canvas.setPointerCapture(e.pointerId);});
canvas.addEventListener('pointermove',e=>{if(!drag)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(Math.hypot(dx,dy)>6)drag.moved=true;if(!drag.moved)return;if(drag.region!==undefined){cfg.fold=THREE.MathUtils.clamp(drag.fold+dx/(innerWidth*.56),0,1);sendParams();sync();}else{theta=drag.theta-dx*.008;phi=THREE.MathUtils.clamp(drag.phi-dy*.006,.15,2.9);}});
canvas.addEventListener('pointerup',e=>{if(!drag)return;const d=drag;drag=undefined;if(!d.moved&&d.region!==undefined)hit(d.region);else if(d.region!==undefined)historySave();});canvas.addEventListener('pointercancel',()=>drag=undefined);
canvas.addEventListener('wheel',e=>{e.preventDefault();radius=THREE.MathUtils.clamp(radius*Math.exp(e.deltaY*.001),.55,24);},{passive:false});
addEventListener('keydown',e=>{if(e.repeat||$('panel').open||$('songsPanel').open||/^(INPUT|SELECT|BUTTON|A)$/.test(document.activeElement.tagName))return;const keys='asdfghjk',i=keys.indexOf(e.key.toLowerCase());if(i>=0){cfg.midi=[45,48,50,52,55,57,60,64][i];sendParams();hit(cfg.region);e.preventDefault();}else if(e.key===' '){expectedScoreId=null;transport=null;updatePlayer();node?.port.postMessage({type:'clear'});e.preventDefault();}else if(e.key==='e')$('enter').click();else if(e.key==='Escape'&&cfg.inside)$('enter').click();else if(e.key==='ArrowLeft'||e.key==='ArrowRight'){cfg.pickup=(cfg.pickup+(e.key==='ArrowRight'?1:7))%8;listenFamily();if(cfg.inside)view();historySave(true);e.preventDefault();}});
addEventListener('resize',()=>{if(capturing)return;renderer.setSize(innerWidth,innerHeight);camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();view();});
function updateAcoustics(immediate=false){
 if(!space||(!immediate&&performance.now()-lastSpaceUpdate<45))return;lastSpaceUpdate=performance.now();camera.updateMatrixWorld();
 const sources=Array.from({length:8},(_,k)=>{const c=new THREE.Vector3();for(let i=k;i<64;i+=8)c.add(body.parts[i].group.position);return c.multiplyScalar(1/8).toArray();});
 const pose={position:camera.position.toArray(),forward:camera.getWorldDirection(new THREE.Vector3()).toArray(),up:new THREE.Vector3(0,1,0).applyQuaternion(camera.quaternion).toArray()};
 const state=space.update(pose,sources,immediate);Object.assign(canvas.dataset,{spatial:space.enabled,acousticNearness:state.enclosure,roomWet:state.wet,nearestAperture:state.nearest,listenerX:pose.position[0],listenerY:pose.position[1],listenerZ:pose.position[2],panning:state.panningModel,spatialReduction:space.output.reduction});
}
view();sync();let last=performance.now();function draw(now){requestAnimationFrame(draw);if(capturing)return;const dt=Math.min((now-last)/1000,.1);last=now;const t=reduced?1:1-Math.exp(-dt*7);visualFold+=(actual.fold-visualFold)*t;if(cfg.inside){target=new THREE.Vector3();for(let i=cfg.pickup;i<64;i+=8)target.add(poses(i,visualFold).position);target.multiplyScalar(1/8);}currentTarget.lerp(target,t);currentRadius+=(radius-currentRadius)*t;camera.position.set(currentRadius*Math.sin(phi)*Math.sin(theta),currentRadius*Math.cos(phi),currentRadius*Math.sin(phi)*Math.cos(theta)).add(currentTarget);camera.lookAt(currentTarget);
 for(const part of body.parts){const p=poses(part.index,visualFold),energy=Math.min(1,rms[part.index]*100);part.group.position.copy(p.position);part.group.quaternion.copy(p.quaternion);part.group.scale.set(p.scale,p.scale,p.scale*(1+(reduced?0:energy*.38)));part.mesh.material.emissive.set(PALETTE[part.index%8]);part.mesh.material.emissiveIntensity=energy*.7;}
 updateAcoustics();
 petals.update(now/1000,analyser,visualFold,reduced,innerHeight,innerWidth);
 Object.assign(canvas.dataset,{spectra:petals.items.length,spectralTotal:petals.total,spectralPeak:petals.peak,spectralFrames:petals.frames,spectralColumns:Math.max(0,...petals.items.map(v=>v.columns)),fold:visualFold,region:cfg.region,family:cfg.pickup,view:cfg.inside?'inside':'outside',triangles:renderer.info.render.triangles});renderer.render(scene,camera);
}requestAnimationFrame(draw);
