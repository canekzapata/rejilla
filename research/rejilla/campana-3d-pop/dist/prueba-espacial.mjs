import {Campana} from './audio/motor.mjs';
import {familySignals} from './audio/captacion.mjs';
import {SpatialListening} from './audio/espacio.mjs';
import {poses} from './forma.mjs';
const SR=48000,DURATION=4,INPUT_END=2.2;
const $=s=>document.getElementById(s);
const sourcePositions=Array.from({length:8},(_,k)=>{const v=[0,0,0];for(let i=k;i<64;i+=8)poses(i,.65).position.toArray().forEach((x,j)=>v[j]+=x/8);return v;});
function inputs(){
 const e=new Campana(SR,{fold:.65,depth:1.2,tension:7,damping:.55,midi:48,pickup:1}),channels=Array.from({length:10},()=>new Float32Array(SR*DURATION)),family=new Float64Array(8);
 for(let n=0;n<SR*INPUT_END;n++){
  if(n===Math.round(SR*.12))e.strike(9,.55);if(n===Math.round(SR*.86))e.strike(41,.3);
  const y=e.sample();familySignals(e.q,e.left,e.right,family);const fade=Math.min(1,(SR*INPUT_END-n)/(SR*.05));channels[0][n]=y[0]*fade;channels[1][n]=y[1]*fade;for(let k=0;k<8;k++)channels[k+2][n]=family[k]*fade;
 }return channels;
}
async function render(channels,pose,original=false,isolated=false){
 const ctx=new OfflineAudioContext(2,DURATION*SR,SR),space=new SpatialListening(ctx);
 space.setEnabled(!original,true);space.update(pose,sourcePositions,true);
 const stereo=ctx.createBufferSource(),buffer=ctx.createBuffer(2,DURATION*SR,SR);buffer.copyToChannel(channels[0],0);buffer.copyToChannel(channels[1],1);stereo.buffer=buffer;stereo.connect(space.original);stereo.start();
 for(let k=0;k<8;k++){const src=ctx.createBufferSource(),b=ctx.createBuffer(1,DURATION*SR,SR);if(!isolated||k===1)b.copyToChannel(channels[k+2],0);src.buffer=b;src.connect(space.apertures[k].input);src.start();}
 const master=ctx.createGain();master.gain.value=.9;space.output.connect(master);master.connect(ctx.destination);return ctx.startRendering();
}
function metrics(b){const a=b.getChannelData(0),c=b.getChannelData(1);let l=0,r=0,peak=0,tail=0;for(let i=0;i<a.length;i++){if(!Number.isFinite(a[i]+c[i]))throw Error('Non-finite output');l+=a[i]**2;r+=c[i]**2;peak=Math.max(peak,Math.abs(a[i]),Math.abs(c[i]));if(i>SR*2.5)tail+=a[i]**2+c[i]**2;}return {leftRms:Math.sqrt(l/a.length),rightRms:Math.sqrt(r/a.length),peak,tailEnergy:tail};}
function difference(a,b){let dot=0,bb=0,aa=0;for(let ch=0;ch<2;ch++){const x=a.getChannelData(ch),y=b.getChannelData(ch);for(let i=0;i<x.length;i++){dot+=x[i]*y[i];bb+=y[i]*y[i];aa+=x[i]*x[i];}}const gain=dot/bb;let residual=0,max=0;for(let ch=0;ch<2;ch++){const x=a.getChannelData(ch),y=b.getChannelData(ch);for(let i=0;i<x.length;i++){residual+=(x[i]-gain*y[i])**2;max=Math.max(max,Math.abs(x[i]-y[i]));}}return {bestGain:gain,relativeResidual:Math.sqrt(residual/aa),maxDifference:max};}
function wav(buffer){const bytes=new ArrayBuffer(44+buffer.length*4),v=new DataView(bytes),text=(at,s)=>{for(let i=0;i<s.length;i++)v.setUint8(at+i,s.charCodeAt(i));};text(0,'RIFF');v.setUint32(4,bytes.byteLength-8,true);text(8,'WAVEfmt ');v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,2,true);v.setUint32(24,SR,true);v.setUint32(28,SR*4,true);v.setUint16(32,4,true);v.setUint16(34,16,true);text(36,'data');v.setUint32(40,bytes.byteLength-44,true);for(let i=0;i<buffer.length;i++)for(let ch=0;ch<2;ch++)v.setInt16(44+i*4+ch*2,Math.round(Math.max(-1,Math.min(1,buffer.getChannelData(ch)[i]))*32767),true);return new Blob([bytes],{type:'audio/wav'});}
function draw(buffers){const canvas=$('comparison'),p=canvas.getContext('2d'),colors=['#ed2889','#5b4ad6','#28a6a6'];p.fillStyle='#fff0e6';p.fillRect(0,0,900,280);for(let k=0;k<3;k++){const a=buffers[k].getChannelData(0),base=45+k*85;p.fillStyle='#321a43';p.fillText(['Outside','Inside','Original stereo'][k],12,base-25);p.strokeStyle=colors[k];p.beginPath();for(let x=0;x<900;x++){let sum=0;const begin=Math.floor(x/900*a.length),end=Math.floor((x+1)/900*a.length);for(let j=begin;j<end;j++)sum+=a[j]*a[j];const y=base-Math.sqrt(sum/(end-begin))*650;p.lineTo(x,y);}p.stroke();p.strokeStyle='#bbb';p.beginPath();p.moveTo(0,base);p.lineTo(900,base);p.stroke();}}
$('render').onclick=async()=>{
 $('render').disabled=true;$('report').textContent='Rendering the same excitation at six listening conditions…';
 try{
  const channels=inputs(),outside={position:[0,0,12],forward:[0,0,-1],up:[0,1,0]},inside={position:sourcePositions[1].map((x,i)=>x+(i===2?1.45:0)),forward:[0,0,-1],up:[0,1,0]},left={...inside,forward:[-1,0,0]},right={...inside,forward:[1,0,0]};
  const a=await render(channels,outside),b=await render(channels,inside),c=await render(channels,outside,true),d=await render(channels,inside,true),l=await render(channels,left,false,true),r=await render(channels,right,false,true);
  const ma=metrics(a),mb=metrics(b),ml=metrics(l),mr=metrics(r),ab=difference(b,a),original=difference(c,d);
  const tests={sameOriginalAcrossViews:original.maxDifference===0,interiorChangesBeyondGain:ab.relativeResidual>.1,interiorHasLongerTail:mb.tailEnergy>ma.tailEnergy*1.5,directionReversesEarBalance:(ml.leftRms-ml.rightRms)*(mr.leftRms-mr.rightRms)<0,headroom:[a,b,c,l,r].every(buf=>metrics(buf).peak<.98)};
  const report={version:'1.2.0',result:Object.values(tests).every(Boolean)?'PASS':'FAIL',tests,outside:ma,inside:mb,lookLeft:ml,lookRight:mr,insideVsOutside:ab,originalStereoAcrossViews:original,sourcePositions,source:'Same two impulses, same q/v trajectory; only projection differs',tail:'Identical 50 ms input fade ends at 2.2 s; tail measured after 2.5 s'};
  draw([a,b,c]);const names=['outside','inside','original','original-inside','look-left','look-right'],all=[a,b,c,d,l,r];let run=new URLSearchParams(location.search).get('run');if(!/^s\d+-[a-f0-9]{12}$/.test(run??''))run='comparison';
  all.forEach((buf,i)=>{const item=document.createElement('div'),title=document.createElement('p'),audio=document.createElement('audio'),link=document.createElement('a');title.textContent=names[i];audio.controls=true;audio.src=URL.createObjectURL(wav(buf));link.href=audio.src;link.download='p-adic-bell-'+names[i]+'-'+run+'.wav';link.textContent='Download '+names[i];link.id='audio-'+names[i];item.append(title,audio,link);$('audio').append(item);});
  const json=document.createElement('a');json.id='reportFile';json.href=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'}));json.download='p-adic-bell-spatial-tests-'+run+'.json';json.textContent='Download report';$('audio').append(json);$('report').textContent=JSON.stringify(report,null,2);document.body.dataset.result=report.result;
 }catch(e){$('report').textContent=e.stack;document.body.dataset.result='ERROR';}
};
